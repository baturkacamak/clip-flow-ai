import json
import time
from pathlib import Path
from typing import Optional

import torch
from faster_whisper import WhisperModel
from loguru import logger

from python_core.config_manager import ConfigManager, TranscriptionConfig
from python_core.transcription.models import Segment, TranscriptionResult, Word


class AudioTranscriber:
    def __init__(self, config_manager: ConfigManager):
        self.cfg: TranscriptionConfig = config_manager.transcription
        self.paths = config_manager.paths
        self.device = self._get_device()
        self.compute_type = self._get_compute_type()

        logger.info(f"Initializing Whisper Model: {self.cfg.model_size} on {self.device} ({self.compute_type})")

        self.model = WhisperModel(self.cfg.model_size, device=self.device, compute_type=self.compute_type)

    def _get_device(self) -> str:
        if self.cfg.device != "auto":
            return self.cfg.device

        if torch.cuda.is_available():
            return "cuda"
        # MPS support in CTranslate2 is limited/experimental, defaulting to CPU for stability on Mac for now
        # unless specifically requested.
        return "cpu"

    def _get_compute_type(self) -> str:
        if self.cfg.compute_type != "auto":
            if self.device == "cpu" and self.cfg.compute_type == "float16":
                logger.warning("Float16 requested on CPU, falling back to int8 for compatibility.")
                return "int8"
            return self.cfg.compute_type

        if self.device == "cuda":
            return "float16"
        return "int8"

    def _get_cache_path(self, video_id: str) -> Path:
        return Path(self.paths.workspace_dir) / f"transcript_{video_id}.json"

    def transcribe(self, audio_path: str, video_id: str) -> Optional[TranscriptionResult]:
        """
        Transcribes audio file and returns structured result.
        Checks cache first.
        """
        cache_path = self._get_cache_path(video_id)
        if cache_path.exists():
            logger.info(f"Loading cached transcript for {video_id}")
            try:
                with open(cache_path, "r") as f:
                    data = json.load(f)
                return TranscriptionResult(**data)
            except Exception as e:
                logger.error(f"Failed to load cache: {e}. Reprocessing.")

        if not Path(audio_path).exists():
            logger.error(f"Audio file not found: {audio_path}")
            return None

        logger.info(f"Starting transcription for {audio_path}...")
        start_time = time.time()

        try:
            segments_generator, info = self.model.transcribe(
                audio_path,
                beam_size=self.cfg.beam_size,
                language=self.cfg.language if self.cfg.language != "auto" else None,
                vad_filter=self.cfg.vad_filter,
                vad_parameters=dict(min_silence_duration_ms=self.cfg.min_silence_duration_ms),
                word_timestamps=True,
            )

            # Iterate generator
            segments_list = []
            for seg in segments_generator:
                words_list = []
                if seg.words:
                    for w in seg.words:
                        words_list.append(
                            Word(
                                word=w.word,
                                start=w.start,
                                end=w.end,
                                score=w.probability,
                            )
                        )

                # Confidence Filtering Log
                if seg.avg_logprob < -1.0:  # Threshold can be tuned
                    logger.debug(f"Low confidence segment ({seg.avg_logprob:.2f}): {seg.text}")

                segments_list.append(
                    Segment(
                        start=seg.start,
                        end=seg.end,
                        text=seg.text.strip(),
                        speaker="SPEAKER_00",  # Placeholder for diarization
                        words=words_list,
                        avg_logprob=seg.avg_logprob,
                        no_speech_prob=seg.no_speech_prob,
                    )
                )

            processing_time = time.time() - start_time

            result = TranscriptionResult(
                video_id=video_id,
                language=info.language,
                segments=segments_list,
                processing_time=processing_time,
                device=self.device,
            )

            # Save Cache
            with open(cache_path, "w") as f:
                f.write(result.model_dump_json(indent=2))

            logger.success(f"Transcription complete in {processing_time:.2f}s. Saved to {cache_path}")
            return result

        except Exception as e:
            logger.exception(f"Transcription failed: {e}")
            return None
