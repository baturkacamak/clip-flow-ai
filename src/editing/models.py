from typing import List, Optional

from pydantic import BaseModel

from src.vision.models import ClipCropData


class BRollSegment(BaseModel):
    start: float
    end: float
    video_path: str

class RenderPlan(BaseModel):
    source_video_path: str
    source_audio_path: Optional[str]
    clip_crop_data: List[ClipCropData]
    b_roll_segments: List[BRollSegment]
    output_path: str
