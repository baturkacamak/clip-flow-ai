from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.config_manager import ConfigManager
from src.packaging.models import VideoPackage


class BaseUploader(ABC):
    def __init__(self, config_manager: ConfigManager):
        self.cfg = config_manager.distribution
        self.paths = config_manager.paths

    @abstractmethod
    def authenticate(self) -> None:
        """Handles authentication (OAuth, Cookies, etc)."""
        pass

    @abstractmethod
    def upload(self, video_package: VideoPackage, schedule_time: Optional[datetime] = None) -> bool:
        """Uploads the video package."""
        pass

    @abstractmethod
    def verify_upload(self) -> bool:
        """Checks if upload was successful."""
        pass
