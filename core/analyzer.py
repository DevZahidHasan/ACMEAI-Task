import time
import cv2
import logging
from shapely.geometry import Polygon
from core.config import AppConfig
from core.interfaces import FieldDetectorProtocol
from core.api_client import ApiClient, ProgressReport, EventReport

logger = logging.getLogger(__name__)

class FieldBoundaryAnalyzer:
    def __init__(self, config: AppConfig, detector: FieldDetectorProtocol, api_client: ApiClient):
        self.config = config
        self.detector = detector
        self.api_client = api_client
        # Pre-compute outer boundary once
        self.outer_boundary = Polygon([(0, 0), (1280, 0), (1280, 720), (0, 720)])

    def process_video(self):
        logger.info(f"Starting processing for video: {self.config.video_path}")
        
        self.api_client.report_event(EventReport(
            event_type="JOB_STARTED",
            message=f"Starting analysis on {self.config.video_path}"
        ))
        
        cap = cv2.VideoCapture(self.config.video_path)
        
        if not cap.isOpened():
            msg = "Error: Could not open video stream."
            logger.error(msg)
            self.api_client.report_event(EventReport(event_type="JOB_FAILED", message=msg))
            raise RuntimeError(msg)

        video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate frame skip step
        step = max(1, int(video_fps / self.config.target_fps)) if self.config.target_fps > 0 else 1
        
        start_frame = self.config.start_frame
        end_frame = self.config.end_frame if self.config.end_frame is not None else total_frames
        
        # Seek to start_frame if not 0
        if start_frame > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
        current_frame = start_frame
        processed_count = 0
        valid_polygons = []

        try:
            while True:
                if current_frame >= end_frame:
                    break
                    
                ret = cap.grab()
                if not ret:
                    break
                    
                if (current_frame - start_frame) % step != 0:
                    current_frame += 1
                    continue
                    
                ret, frame = cap.retrieve()
                if not ret:
                    break

                try:
                    mask = self.detector.extract_mask(frame)
                    poly = self.detector.derive_polygon(mask)

                    if poly and poly.is_valid:
                        intersection_area = poly.intersection(self.outer_boundary).area
                        valid_polygons.append((current_frame, poly, intersection_area))
                    else:
                        logger.debug(f"Frame {current_frame}: Invalid or missing polygon.")
                        
                except Exception as e:
                    logger.warning(f"Error processing frame {current_frame}: {e}")
                    # Skip bad frame and continue
                    
                processed_count += 1
                current_frame += 1

                # Simulate heavy per-frame processing latency
                time.sleep(0.005)

                if processed_count % 100 == 0:
                    logger.info(f"Processed {processed_count} frames. Found {len(valid_polygons)} boundaries.")
                    self.api_client.report_progress(ProgressReport(
                        video_path=self.config.video_path,
                        status="IN_PROGRESS",
                        frames_processed=processed_count,
                        polygons_found=len(valid_polygons)
                    ))
        finally:
            cap.release()

        logger.info(f"Finished. Processed {processed_count} frames. Found {len(valid_polygons)} boundaries.")
        self.api_client.report_progress(ProgressReport(
            video_path=self.config.video_path,
            status="COMPLETED",
            frames_processed=processed_count,
            polygons_found=len(valid_polygons)
        ))
        self.api_client.report_event(EventReport(
            event_type="JOB_COMPLETED",
            message=f"Finished analysis on {self.config.video_path}"
        ))
        
        return valid_polygons
