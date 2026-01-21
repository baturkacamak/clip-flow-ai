from typing import List

from pydantic import BaseModel, Field


class Word(BaseModel):
    """Represents a single word with timestamps."""

    word: str
    start: float
    end: float
    score: float = Field(..., description="Confidence score 0-1")


class Segment(BaseModel):
    """Represents a segment of speech (subtitle block)."""

    start: float
    end: float
    text: str
    speaker: str = Field(default="SPEAKER_00")
    words: List[Word] = Field(default_factory=list)
    avg_logprob: float = Field(
        default=0.0, description="Average log probability of the segment"
    )
    no_speech_prob: float = Field(
        default=0.0, description="Probability that this segment is silence"
    )


class TranscriptionResult(BaseModel):
    """Final structured output for transcription."""

    video_id: str
    language: str
    segments: List[Segment]
    processing_time: float = Field(default=0.0)
    device: str = Field(default="unknown")
