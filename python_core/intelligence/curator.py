from typing import Any, List, Optional

import instructor
from anthropic import Anthropic
from loguru import logger
from openai import OpenAI
from pydantic import BaseModel

from python_core.config_manager import ConfigManager
from python_core.intelligence.models import CurationResult, ViralClip
from python_core.intelligence.prompts import USER_PROMPT_TEMPLATE, VIDEO_EDITOR_SYSTEM_PROMPT
from python_core.transcription.models import TranscriptionResult


class ContentCurator:
    def __init__(self, config_manager: ConfigManager):
        self.cfg = config_manager.intelligence
        self.client: Optional[Any] = self._init_client()

    def _init_client(self) -> Optional[Any]:
        """Initialize the LLM client wrapped with Instructor."""
        if self.cfg.llm_provider == "openai":
            api_key = self.cfg.openai_api_key
            if not api_key:
                logger.warning("OpenAI API Key not found. Curation will be mocked/skipped.")
                return None
            return instructor.from_openai(OpenAI(api_key=api_key))
        
        elif self.cfg.llm_provider == "anthropic":
            api_key = self.cfg.anthropic_api_key
            if not api_key:
                logger.warning("Anthropic API Key not found. Curation will be mocked/skipped.")
                return None
            return instructor.from_anthropic(Anthropic(api_key=api_key))
        
        else:
            raise ValueError(f"Unsupported LLM provider: {self.cfg.llm_provider}")

    def _format_transcript(self, transcript: TranscriptionResult) -> str:
        """Formats transcript into a readable string with timestamps."""
        formatted = []
        for seg in transcript.segments:
            # Format timestamp as [MM:SS]
            start_m = int(seg.start // 60)
            start_s = int(seg.start % 60)
            timestamp = f"[{start_m:02d}:{start_s:02d}]"
            formatted.append(f"{timestamp} {seg.speaker}: {seg.text}")
        return "\n".join(formatted)

    def curate(self, transcript: TranscriptionResult) -> CurationResult:
        """
        Analyzes the transcript and returns a list of viral clips.
        Handles chunking for long videos.
        """
        if not self.client:
            logger.error("LLM Client not available. Returning empty curation.")
            return CurationResult(video_id=transcript.video_id, clips=[])

        # Simple logic: For now, we process the whole transcript if it fits.
        # Ideally, we implement sliding window.
        # Let's verify length.
        full_text = self._format_transcript(transcript)
        
        # Token estimation (rough char count / 4)
        est_tokens = len(full_text) / 4
        logger.info(f"Transcript length: {len(full_text)} chars (~{int(est_tokens)} tokens)")

        # TODO: Implement robust chunking if > 100k tokens
        # For Part 3 demo, we process as one block or first X minutes.
        
        clips = self._process_chunk(full_text, self.cfg.focus_topic)
        
        return CurationResult(video_id=transcript.video_id, clips=clips)

    def _process_chunk(self, transcript_text: str, focus_topic: Optional[str]) -> List[ViralClip]:
        """Sends a transcript chunk to the LLM."""
        if not self.client:
            return []

        try:
            # We ask for a wrapper object to get a list
            class Response(BaseModel):
                clips: List[ViralClip]

            user_prompt = USER_PROMPT_TEMPLATE.format(
                focus_topic=focus_topic if focus_topic else "General Virality",
                transcript_text=transcript_text
            )

            resp = self.client.chat.completions.create(
                model=self.cfg.model_name,
                response_model=Response,
                messages=[
                    {"role": "system", "content": VIDEO_EDITOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                max_retries=2,
            )
            
            # Filter by score
            filtered_clips = [
                c for c in resp.clips 
                if c.virality_score >= self.cfg.virality_threshold
            ]
            
            logger.success(f"Identified {len(filtered_clips)} viral candidates (from {len(resp.clips)} raw).")
            return filtered_clips

        except Exception as e:
            logger.error(f"LLM Curation failed: {e}")
            return []
