from typing import List

from pydantic import BaseModel

from python_core.transcription.models import Word


class CaptionGroup(BaseModel):
    """A group of words displayed together as a subtitle line."""

    words: List[Word]
    start: float
    end: float
    text: str
