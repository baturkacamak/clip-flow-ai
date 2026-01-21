import os
import pickle
from datetime import datetime
from typing import Any, Optional

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from loguru import logger

from python_core.config_manager import ConfigManager
from python_core.distribution.base import BaseUploader
from python_core.packaging.models import VideoPackage

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubeUploader(BaseUploader):
    def __init__(self, config_manager: ConfigManager):
        super().__init__(config_manager)
        self.service: Optional[Any] = None

    def authenticate(self) -> None:
        creds = None
        # Token file
        token_path = "token.pickle"

        if os.path.exists(token_path):
            with open(token_path, "rb") as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                secrets_path = self.cfg.youtube_client_secrets_path
                if not os.path.exists(secrets_path):
                    logger.error(f"Client secrets not found at {secrets_path}")
                    return

                flow = InstalledAppFlow.from_client_secrets_file(secrets_path, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(token_path, "wb") as token:
                pickle.dump(creds, token)

        self.service = build("youtube", "v3", credentials=creds)

    def upload(self, video_package: VideoPackage, schedule_time: Optional[datetime] = None) -> bool:
        if not self.service:
            try:
                self.authenticate()
            except Exception as e:
                logger.error(f"Authentication failed: {e}")
                return False

        if not self.service:
            return False

        logger.info(f"Uploading to YouTube: {video_package.title}")

        body = {
            "snippet": {
                "title": video_package.title[:100],  # Max 100
                "description": video_package.description,
                "tags": video_package.tags,
                "categoryId": "22",  # People & Blogs
            },
            "status": {
                "privacyStatus": "private",  # Default to private for safety
                "selfDeclaredMadeForKids": False,
            },
        }

        try:
            # chunk_size needs to be multiple of 256 * 1024
            media = MediaFileUpload(video_package.video_path, chunksize=-1, resumable=True)
            request = self.service.videos().insert(part=",".join(body.keys()), body=body, media_body=media)

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Uploaded {int(status.progress() * 100)}%")

            logger.success(f"YouTube Upload Complete! Video ID: {response.get('id')}")
            return True

        except Exception as e:
            logger.error(f"YouTube upload failed: {e}")
            return False

    def verify_upload(self) -> bool:
        return True
