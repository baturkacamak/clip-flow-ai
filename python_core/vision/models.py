from typing import List

from pydantic import BaseModel


class FrameCrop(BaseModel):
    timestamp: float
    frame_index: int
    crop_x: int
    crop_y: int
    crop_h: int 
    crop_w: int 

class ClipCropData(BaseModel):
    clip_id: str
    video_id: str
    frames: List[FrameCrop]
