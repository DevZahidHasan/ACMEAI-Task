from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional
import json

class FieldDetectorConfig(BaseModel):
    type: str = Field(..., description="The type of the detector (e.g., sam_mask_v1)")
    sport: str = Field(default="football")
    min_area: int = Field(default=1000, ge=1)

class CropSearchConfig(BaseModel):
    aspect_ratio: str = Field(default="16:9")
    padding_px: int = Field(default=20, ge=0)

class AppConfig(BaseModel):
    video_path: str = Field(..., description="Path to the video file")
    target_fps: int = Field(default=30, gt=0)
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    field_detector: FieldDetectorConfig
    crop_search: CropSearchConfig
    debug_mode: bool = Field(default=False)
    api_url: str = Field(default="http://mock_api:5000")
    start_frame: int = Field(default=0, ge=0)
    end_frame: Optional[int] = Field(default=None)

    @field_validator('end_frame')
    def validate_end_frame(cls, v, info):
        if v is not None and v <= info.data.get('start_frame', 0):
            raise ValueError('end_frame must be greater than start_frame')
        return v

def load_config(config_path: str) -> AppConfig:
    with open(config_path, 'r') as f:
        data = json.load(f)
    return AppConfig(**data)
