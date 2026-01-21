import json
from pathlib import Path
from typing import Any, Dict, Optional

import yt_dlp
from loguru import logger

from src.config_manager import ConfigManager, DownloaderConfig, PathsConfig


class VideoDownloader:
    """
    Production-grade video downloader wrapper around yt-dlp.
    Handles metadata extraction, quality control, and audio separation.
    """

    def __init__(self, config_manager: ConfigManager):
        self.cfg: DownloaderConfig = config_manager.downloader
        self.paths: PathsConfig = config_manager.paths
        self.workspace = Path(self.paths.workspace_dir)
        self.history_file = Path(self.paths.history_file)

        self.workspace.mkdir(parents=True, exist_ok=True)
        self._ensure_history_file()

    def _ensure_history_file(self) -> None:
        """Creates the history file if it doesn't exist."""
        if not self.history_file.exists():
            with open(self.history_file, "w") as f:
                json.dump([], f)

    def _is_duplicate(self, video_id: str) -> bool:
        """Checks if video_id has already been processed."""
        if not self.cfg.check_duplicates:
            return False

        try:
            with open(self.history_file, "r") as f:
                history = json.load(f)
            return video_id in history
        except Exception as e:
            logger.error(f"Failed to read history file: {e}")
            return False

    def _add_to_history(self, video_id: str) -> None:
        """Adds video_id to the processed history."""
        if not self.cfg.check_duplicates:
            return

        try:
            with open(self.history_file, "r") as f:
                history = json.load(f)

            if video_id not in history:
                history.append(video_id)
                with open(self.history_file, "w") as f:
                    json.dump(history, f)
        except Exception as e:
            logger.error(f"Failed to update history file: {e}")

    def progress_hook(self, d: Dict[str, Any]) -> None:
        """Callback for yt-dlp progress."""
        if d["status"] == "downloading":
            p = d.get("_percent_str", "0%").replace("%", "")
            logger.debug(
                f"Downloading: {p}% | Speed: {d.get('_speed_str', 'N/A')} | ETA: {d.get('_eta_str', 'N/A')}"
            )
        elif d["status"] == "finished":
            logger.info("Download completed processing post-download hooks...")

    def download(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Downloads a video and optionally extracts audio and metadata.

        Args:
            url: The URL of the video to download.

        Returns:
            Dict containing paths to video, audio, and metadata, or None if failed.
        """
        logger.info(f"Initiating download for: {url}")

        # 1. Extract Info first (Dry Run) to check metadata/duplicates
        try:
            with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                info = ydl.extract_info(url, download=False)
                video_id = info.get("id")
                title = info.get("title")
                # duration = info.get('duration') # Unused

                # Check Duplicates
                if self._is_duplicate(video_id):
                    logger.warning(
                        f"Video '{title}' ({video_id}) already exists in history. Skipping."
                    )
                    return None

                # Quality Control (Simple Check based on available formats is complex in dry run,
                # but we can check if generic height is acceptable if available in info)
                # Note: 'height' might be None for some extractors or adaptive streams
                height = info.get("height")
                if height and height < int(self.cfg.min_resolution):
                    logger.warning(
                        f"Video resolution ({height}p) is below minimum ({self.cfg.min_resolution}p). Skipping."
                    )
                    return None

        except Exception as e:
            logger.error(f"Failed to extract info for {url}: {e}")
            return None

        # 2. Configure yt-dlp options
        # We construct a filename template that includes the ID to avoid collisions
        out_tmpl = str(self.workspace / "%(title)s [%(id)s].%(ext)s")

        ydl_opts = {
            "format": f"bestvideo[height>={self.cfg.min_resolution}]+bestaudio/best[height>={self.cfg.min_resolution}]",
            "outtmpl": out_tmpl,
            "writethumbnail": True,
            "writeinfojson": True,  # Metadata sidecar
            "progress_hooks": [self.progress_hook],
            "merge_output_format": self.cfg.video_format,
            "retries": self.cfg.retries,
        }

        # Cookie support
        if self.paths.cookies_file and Path(self.paths.cookies_file).exists():
            ydl_opts["cookiefile"] = self.paths.cookies_file

        # Post-processors
        postprocessors = []

        # Audio Separation
        if self.cfg.separate_audio:
            # Extract audio as a separate file
            postprocessors.append(
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": self.cfg.audio_format,
                    "preferredquality": "192",
                }
            )
            # Important: Keep the original video file
            ydl_opts["keepvideo"] = True

        if postprocessors:
            ydl_opts["postprocessors"] = postprocessors

        # 3. Execute Download
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)

                # Retrieve final file paths
                # Note: filename logic in yt-dlp can be tricky with post-processors
                # We can prepare the return object based on the requested template

                base_filename = ydl.prepare_filename(info_dict)
                # If merged, the extension might change to .mp4 from .webm etc.
                # But since we forced merge_output_format, it should be predictable.

                video_path = Path(base_filename).with_suffix(
                    f".{self.cfg.video_format}"
                )

                # Metadata path
                metadata_path = Path(base_filename).with_suffix(".info.json")

                # Audio path (if separated)
                audio_path = None
                if self.cfg.separate_audio:
                    audio_path = Path(base_filename).with_suffix(
                        f".{self.cfg.audio_format}"
                    )

                result = {
                    "id": video_id,
                    "title": title,
                    "video_path": str(video_path),
                    "metadata_path": str(metadata_path),
                    "audio_path": str(audio_path) if audio_path else None,
                }

                # Update History
                self._add_to_history(video_id)

                logger.success(f"Successfully processed: {title}")
                return result

        except Exception as e:
            logger.error(f"Download failed for {url}: {e}")
            return None
