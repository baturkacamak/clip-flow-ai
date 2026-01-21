from typing import List

from pydantic import BaseModel, Field


class ViralClip(BaseModel):
    """A selected video clip with high viral potential."""

    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    title: str = Field(..., description="A catchy, clickbait-style title for this clip")
    virality_score: int = Field(..., description="Score from 0-100 based on hook, value, and completeness")
    reasoning: str = Field(..., description="Why this clip was selected")
    category: str = Field(..., description="Category like 'Humor', 'Motivation', 'Tech'")


class CurationResult(BaseModel):
    """Result of the content curation process."""

    video_id: str
    clips: List[ViralClip]
