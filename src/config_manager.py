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


class PipelineConfig(BaseModel):
    target_aspect_ratio: str = Field(default="9:16")
    llm_model: str = Field(default="gpt-4")


class AppConfig(BaseModel):
    paths: PathsConfig
    downloader: DownloaderConfig
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
            raise FileNotFoundError(
                f"Configuration file not found at {self.config_path}"
            )

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
    def pipeline(self) -> PipelineConfig:
        return self.config.pipeline
