import os
from pathlib import Path
import yaml
from pydantic import BaseModel, Field
from typing import Optional

class PathsConfig(BaseModel):
    base_dir: str = Field(default=".")
    workspace_dir: str = Field(default="assets/workspace")
    output_dir: str = Field(default="outputs")
    log_dir: str = Field(default="logs")
    cookies_file: Optional[str] = Field(default="config/cookies.txt")
    history_file: str = Field(default="assets/workspace/download_history.json")

class DownloaderConfig(BaseModel):
    resolution: str = Field(default="1080")
    min_resolution: str = Field(default="720")
    video_format: str = Field(default="mp4")
    separate_audio: bool = Field(default=True)
    audio_format: str = Field(default="wav")
    check_duplicates: bool = Field(default=True)
    retries: int = Field(default=3)

class TranscriptionConfig(BaseModel):
    model_size: str = Field(default="large-v2")
    compute_type: str = Field(default="float16")
    device: str = Field(default="auto")
    language: str = Field(default="auto")
    beam_size: int = Field(default=5)
    vad_filter: bool = Field(default=True)
    min_silence_duration_ms: int = Field(default=500)
    enable_diarization: bool = Field(default=False)

class IntelligenceConfig(BaseModel):
    llm_provider: str = Field(default="openai")
    model_name: str = Field(default="gpt-4-0125-preview")
    virality_threshold: int = Field(default=75)
    chunk_duration_minutes: int = Field(default=10)
    focus_topic: Optional[str] = Field(default=None)
    openai_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    anthropic_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))

class PipelineConfig(BaseModel):
    target_aspect_ratio: str = Field(default="9:16")

class AppConfig(BaseModel):
    paths: PathsConfig
    downloader: DownloaderConfig
    transcription: TranscriptionConfig
    intelligence: IntelligenceConfig
    pipeline: PipelineConfig

class ConfigManager:
    """
    Manages loading and validation of application configuration.
    """
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = Path(config_path)
        self.config: AppConfig = self._load_config()

    def _load_config(self) -> AppConfig:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at {self.config_path}")

        with open(self.config_path, "r") as f:
            raw_config = yaml.safe_load(f)

        return AppConfig(**raw_config)

    @property
    def paths(self) -> PathsConfig:
        return self.config.paths

    @property
    def downloader(self) -> DownloaderConfig:
        return self.config.downloader

    @property
    def transcription(self) -> TranscriptionConfig:
        return self.config.transcription

    @property
    def intelligence(self) -> IntelligenceConfig:
        return self.config.intelligence

    @property
    def pipeline(self) -> PipelineConfig:
        return self.config.pipeline