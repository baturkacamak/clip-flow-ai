from pathlib import Path
from typing import List, Optional, Tuple

from loguru import logger

from python_core.config_manager import ConfigManager
from python_core.editing.models import BRollSegment, RenderPlan
from python_core.retrieval.matcher import VisualMatcher
from python_core.transcription.engine import AudioTranscriber
from python_core.transcription.models import TranscriptionResult


class StoryBuilder:
    def __init__(self, config_manager: ConfigManager):
        self.cfg = config_manager
        self.transcriber = AudioTranscriber(config_manager)
        self.matcher: Optional[VisualMatcher] = None

    def set_matcher(self, matcher: VisualMatcher) -> None:
        self.matcher = matcher

    def build_plan(
        self, audio_path: str, output_path: str
    ) -> Tuple[Optional[RenderPlan], Optional[TranscriptionResult]]:
        """
        Orchestrates the Story Mode generation.
        Returns (RenderPlan, TranscriptionResult).
        """
        if not Path(audio_path).exists():
            logger.error(f"Audio file not found: {audio_path}")
            return None, None

        # 1. Transcribe
        video_id = f"story_{Path(audio_path).stem}"
        transcript = self.transcriber.transcribe(audio_path, video_id)
        if not transcript:
            return None, None

        # 2. Visual Matching
        if not self.matcher:
            logger.error("VisualMatcher not set in StoryBuilder.")
            return None, transcript

        b_rolls: List[BRollSegment] = []

        MIN_SCENE_DURATION = 3.0
        current_text = ""
        current_start = 0.0

        segments = transcript.segments

        if not segments:
            logger.error("No segments in transcript.")
            return None, transcript

        current_start = segments[0].start

        for i, seg in enumerate(segments):
            current_text += " " + seg.text
            duration = seg.end - current_start

            is_last = i == len(segments) - 1
            is_long_enough = duration >= MIN_SCENE_DURATION
            is_sentence_end = seg.text.strip().endswith((".", "?", "!"))

            if is_last or (is_long_enough and is_sentence_end):
                query = current_text.strip()
                match_path = self.matcher.find_match(query)

                if match_path:
                    b_rolls.append(BRollSegment(start=current_start, end=seg.end, video_path=match_path))
                else:
                    logger.warning(f"No visual match for: '{query}'. reusing previous.")
                    if b_rolls:
                        prev = b_rolls[-1]
                        b_rolls.append(BRollSegment(start=current_start, end=seg.end, video_path=prev.video_path))
                    else:
                        pass

                current_start = seg.end
                current_text = ""

        plan = RenderPlan(
            source_video_path="",
            source_audio_path=audio_path,
            clip_crop_data=[],
            b_roll_segments=b_rolls,
            output_path=output_path,
        )
        return plan, transcript
