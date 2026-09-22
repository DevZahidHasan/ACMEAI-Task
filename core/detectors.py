import cv2
import numpy as np
from shapely.geometry import Polygon
from typing import Optional
from core.config import FieldDetectorConfig

class SamMaskV1Detector:
    def __init__(self, config: FieldDetectorConfig):
        self.config = config

    def extract_mask(self, frame: np.ndarray) -> np.ndarray:
        # Dummy mask generation based on green color thresholding
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        return cv2.inRange(hsv, lower_green, upper_green)

    def derive_polygon(self, mask: np.ndarray) -> Optional[Polygon]:
        try:
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest) > self.config.min_area:
                    pts = largest.reshape(-1, 2)
                    if len(pts) >= 3:
                        return Polygon(pts)
        except Exception:
            pass
        return None
