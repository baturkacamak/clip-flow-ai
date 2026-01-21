from typing import List
from pydantic import BaseModel, Field

class VideoPackage(BaseModel):
    """Final package for a generated video."""
    video_path: str
    thumbnail_path: str
    title: str
    description: str
    tags: List[str]
    captions: str # Text for auto-captions input
    platforms: List[str] = Field(default_factory=lambda: ["youtube", "tiktok"])
