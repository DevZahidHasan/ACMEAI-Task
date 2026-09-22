import requests
import logging
from pydantic import BaseModel, Field
from typing import Optional

logger = logging.getLogger(__name__)

class ProgressReport(BaseModel):
    video_path: str
    status: str
    frames_processed: int
    polygons_found: int
    error: Optional[str] = None

class EventReport(BaseModel):
    event_type: str
    message: str
    details: Optional[dict] = None

class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        
    def report_progress(self, report: ProgressReport) -> bool:
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/jobs/progress",
                json=report.model_dump(),
                timeout=5.0
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.warning(f"Failed to report progress to platform: {e}")
            return False

    def report_event(self, report: EventReport) -> bool:
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/jobs/events",
                json=report.model_dump(),
                timeout=5.0
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.warning(f"Failed to report event to platform: {e}")
            return False
