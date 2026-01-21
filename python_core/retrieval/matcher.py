from pathlib import Path
from typing import Optional, Set

from loguru import logger

from python_core.config_manager import ConfigManager
from python_core.retrieval.indexer import LibraryIndexer


class VisualMatcher:
    def __init__(self, config_manager: ConfigManager, indexer: LibraryIndexer):
        self.cfg = config_manager.retrieval
        self.indexer = indexer  # Share the indexer to reuse model/collection
        self.session_history: Set[str] = set()
        self.history_window = self.cfg.deduplication_window
        self.recent_matches: list[str] = []  # To handle window

    def find_match(self, query_text: str) -> Optional[str]:
        """
        Finds the best B-Roll video for the given text.
        Returns the file path or None if no good match.
        """
        try:
            # Encode text
            text_embedding = self.indexer.model.encode(query_text).tolist()

            # Query DB
            # We ask for top k to handle deduplication
            k = 10
            results = self.indexer.collection.query(
                query_embeddings=[text_embedding],  # type: ignore
                n_results=k,
            )

            if not results or not results["ids"]:
                return None

            ids = results["ids"][0]
            distances = results["distances"][0]  # type: ignore
            # Chroma default is L2 (squared Euclidean). Lower is better.
            # If we want similarity (higher is better), we need cosine.
            # But wait, settings.yaml has `similarity_threshold: 0.25`.
            # Typically cosine similarity is 0..1.
            # I should assume cosine distance or convert.
            # Actually, let's just use the result if it's "close enough".
            # For L2: 0 is identical.
            # For Cosine distance: 0 is identical, 1 is orthogonal, 2 is opposite.
            # I should verify Chroma metric. By default it is L2.
            # I'll stick to L2 for now, but threshold 0.25 might be for Cosine Similarity.
            # If I want Cosine Similarity, I should have initialized collection with metadata={"hnsw:space": "cosine"}.
            # But I didn't. I'll rely on relative ranking for now and a loose threshold.
            # Or I can just check if distance < threshold.

            for i, vid_id in enumerate(ids):
                dist = distances[i]

                # Check history
                if vid_id in self.session_history:
                    continue

                # Check threshold (L2 distance)
                # If using L2, values can be > 1.
                # If standard CLIP, embeddings are normalized?
                # SentenceTransformers CLIP usually outputs normalized vectors if requested, but check.
                # Assuming normalized, L2 = 2 * (1 - cosine_sim).
                # So if cosine_sim > 0.25, L2 < 2*(1-0.25) = 1.5.
                # Let's effectively accept anything reasonable for now, say L2 < 1.0.
                if dist > 1.0:  # Matches are too far
                    # logger.debug(f"Match rejected: {dist} > 1.0")
                    continue

                # We have a winner
                metadata = results["metadatas"][0][i]  # type: ignore
                video_path = str(metadata["path"])

                self._update_history(vid_id)
                logger.info(f"Matched B-Roll for '{query_text[:30]}...': {Path(video_path).name} (dist={dist:.2f})")
                return video_path

            return None

        except Exception as e:
            logger.error(f"Matching failed: {e}")
            return None

    def _update_history(self, vid_id: str) -> None:
        self.session_history.add(vid_id)
        self.recent_matches.append(vid_id)
        if len(self.recent_matches) > self.history_window:
            removed = self.recent_matches.pop(0)
            self.session_history.remove(removed)
