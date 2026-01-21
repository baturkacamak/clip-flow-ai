import hashlib
from pathlib import Path
from typing import Any, List, Optional

import chromadb
import cv2
import numpy as np
from loguru import logger
from PIL import Image
from sentence_transformers import SentenceTransformer

from python_core.config_manager import ConfigManager


class LibraryIndexer:
    def __init__(self, config_manager: ConfigManager):
        self.cfg = config_manager.retrieval
        self.paths = config_manager.paths
        self.db_path = Path(self.paths.workspace_dir) / "chroma_db"
        self.model_name = self.cfg.clip_model_name

        # Lazy load model
        self._model: Optional[SentenceTransformer] = None
        self._client: Optional[Any] = None
        self._collection: Optional[Any] = None

    @property
    def model(self) -> SentenceTransformer:
        if not self._model:
            logger.info(f"Loading CLIP model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    @property
    def collection(self) -> chromadb.Collection:
        if not self._client:
            self._client = chromadb.PersistentClient(path=str(self.db_path))
        if not self._collection:
            self._collection = self._client.get_or_create_collection(name="b_roll_library")
        return self._collection

    def _get_file_hash(self, file_path: str) -> str:
        """Returns SHA256 hash of the file path (to track indexing status)."""
        return hashlib.sha256(file_path.encode()).hexdigest()

    def _extract_frames(self, video_path: str, num_frames: int = 3) -> List[Image.Image]:
        """Extracts n frames (start, middle, end) from video."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames < num_frames:
            # If video is too short, just take what we have
            indices = list(range(total_frames))
        else:
            indices = [0, total_frames // 2, total_frames - 1]

        frames = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(Image.fromarray(frame_rgb))

        cap.release()
        return frames

    def index_library(self) -> None:
        """Scans b_roll_library_path and indexes new videos."""
        lib_path = Path(self.cfg.b_roll_library_path)
        if not lib_path.exists():
            logger.warning(f"B-Roll library path not found: {lib_path}")
            return

        # Get existing IDs
        existing_ids = set()
        try:
            # ChromaDB get returns dict with ids list
            existing_data = self.collection.get()
            if existing_data and existing_data["ids"]:
                existing_ids = set(existing_data["ids"])
        except Exception as e:
            logger.warning(f"Failed to fetch existing IDs: {e}")

        video_files = list(lib_path.glob("**/*.mp4")) + list(lib_path.glob("**/*.mov"))
        logger.info(f"Found {len(video_files)} videos in {lib_path}")

        new_videos = []
        for vid in video_files:
            file_id = self._get_file_hash(str(vid))
            if file_id not in existing_ids:
                new_videos.append((vid, file_id))

        if not new_videos:
            logger.info("Library is up to date.")
            return

        logger.info(f"Indexing {len(new_videos)} new videos...")

        for vid_path, file_id in new_videos:
            try:
                frames = self._extract_frames(str(vid_path))
                if not frames:
                    logger.warning(f"Could not extract frames from {vid_path}")
                    continue

                # Encode frames
                embeddings = self.model.encode(frames)  # type: ignore

                # Mean pooling
                mean_embedding = np.mean(embeddings, axis=0)

                # Add to DB
                self.collection.add(
                    documents=[str(vid_path)],  # We store path in document for now, or metadata
                    metadatas=[{"path": str(vid_path), "filename": vid_path.name}],
                    ids=[file_id],
                    embeddings=[mean_embedding.tolist()],
                )
                logger.debug(f"Indexed: {vid_path.name}")

            except Exception as e:
                logger.error(f"Failed to index {vid_path}: {e}")

        logger.success("Indexing complete.")
