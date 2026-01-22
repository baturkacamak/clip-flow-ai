from pathlib import Path
from typing import List, Optional

from loguru import logger

from python_core.config_manager import ConfigManager
from python_core.distribution.tiktok_browser import TikTokUploader
from python_core.distribution.youtube import YouTubeUploader
from python_core.editing.compositor import VideoCompositor
from python_core.editing.models import BRollSegment, RenderPlan
from python_core.ingestion.downloader import VideoDownloader
from python_core.intelligence.curator import ContentCurator
from python_core.modes.story_builder import StoryBuilder
from python_core.overlay.subtitle import SubtitleOverlay
from python_core.packaging.generator import MetadataGenerator
from python_core.packaging.thumbnail import ThumbnailMaker
from python_core.retrieval.indexer import LibraryIndexer
from python_core.retrieval.matcher import VisualMatcher
from python_core.transcription.engine import AudioTranscriber
from python_core.vision.cropper import SmartCropper


def get_text_for_range(transcript, start: float, end: float) -> str:
    text = []
    for seg in transcript.segments:
        seg_start = seg.start
        seg_end = seg.end
        if max(start, seg_start) < min(end, seg_end):
            text.append(seg.text)
    return " ".join(text)


class PipelineManager:
    def __init__(self, config_manager: ConfigManager, keep_temp: bool = False):
        self.cfg = config_manager
        self.keep_temp = keep_temp
        self.workspace = Path(self.cfg.paths.workspace_dir)
        self.output_dir = Path(self.cfg.paths.output_dir)

    def run(
        self,
        url: Optional[str] = None,
        topic: Optional[str] = None,
        upload: bool = False,
        platforms: Optional[List[str]] = None,
        mode: str = "viral",
        audio_path: Optional[str] = None,
    ) -> None:
        logger.info(f"Starting Pipeline (Mode: {mode})")

        if topic:
            self.cfg.intelligence.focus_topic = topic

        try:
            if mode == "story":
                self._run_story_mode(audio_path, upload, platforms)
            else:
                if not url:
                    logger.error("URL is required for viral mode.")
                    return
                self._run_viral_mode(url, upload, platforms)
        except Exception as e:
            logger.exception(f"Pipeline failed: {e}")
            raise e
        finally:
            if not self.keep_temp:
                self.cleanup()

    def _run_story_mode(self, audio_path: Optional[str], upload: bool, platforms: Optional[List[str]]):
        if not audio_path:
            logger.error("Audio path required for story mode.")
            return

        # Init Retrieval
        indexer = LibraryIndexer(self.cfg)
        indexer.index_library()
        matcher = VisualMatcher(self.cfg, indexer)

        builder = StoryBuilder(self.cfg)
        builder.set_matcher(matcher)

        # Build Plan
        # Output directory based on audio name
        vid_id = Path(audio_path).stem
        out_dir = self.output_dir / f"story_{vid_id}"
        out_dir.mkdir(parents=True, exist_ok=True)

        clean_path = str(out_dir / "clean.mp4")
        final_path = str(out_dir / "final.mp4")

        plan, transcript = builder.build_plan(audio_path, clean_path)

        if not plan or not transcript:
            logger.error("Failed to build story plan.")
            return

        # Render
        compositor = VideoCompositor(self.cfg)
        compositor.render_story_mode(plan)

        # Overlay
        overlay = SubtitleOverlay(self.cfg)
        overlay.overlay_subtitles(clean_path, transcript, final_path)

        logger.success(f"Story Mode finished: {final_path}")
        # Metadata/Upload logic if needed (Optional for story mode for now unless requested)
        # Using dummy clip data for metadata gen? Or skip.
        # Story Mode implies we have one output.
        pass

    def _run_viral_mode(self, url: str, upload: bool, platforms: Optional[List[str]]):
        # 1. Ingestion
        downloader = VideoDownloader(self.cfg)
        dl_res = downloader.download(url)
        if not dl_res:
            logger.error("Download failed.")
            return

        video_path = dl_res["video_path"]
        audio_path = dl_res.get("audio_path")
        video_id = dl_res["id"]

        # 2. Transcription
        transcriber = AudioTranscriber(self.cfg)
        transcript = transcriber.transcribe(audio_path, video_id)
        if not transcript:
            logger.error("Transcription failed.")
            return

        # 3. Curation
        curator = ContentCurator(self.cfg)
        curation_res = curator.curate(transcript)
        clips = curation_res.clips

        if not clips:
            logger.warning("No clips found.")
            return

        # 4. Retrieval (Init)
        indexer = LibraryIndexer(self.cfg)
        indexer.index_library()
        matcher = VisualMatcher(self.cfg, indexer)

        # 5. Vision
        cropper = SmartCropper(self.cfg)
        crop_results = cropper.process_clips(video_path, clips, video_id)

        # 6. Editing Loop per Clip
        compositor = VideoCompositor(self.cfg)
        overlay = SubtitleOverlay(self.cfg)
        meta_gen = MetadataGenerator(self.cfg)
        thumb_maker = ThumbnailMaker(self.cfg)

        for i, res in enumerate(crop_results):
            clip = clips[i]
            logger.info(f"Processing Clip {i+1}/{len(clips)}: {clip.title}")

            # B-Roll
            b_rolls = []
            clip_text = get_text_for_range(transcript, clip.start_time, clip.end_time)
            b_roll_path = matcher.find_match(clip_text)
            if b_roll_path:
                b_rolls.append(BRollSegment(start=clip.start_time, end=clip.end_time, video_path=b_roll_path))

            # Prepare Output paths
            clip_dir = self.output_dir / video_id / f"clip_{i}"
            clip_dir.mkdir(parents=True, exist_ok=True)

            clean_path = str(clip_dir / "clean.mp4")
            final_path = str(clip_dir / "final.mp4")
            thumb_path = str(clip_dir / "thumbnail.jpg")
            meta_path = str(clip_dir / "metadata.json")

            # Composite
            plan = RenderPlan(
                source_video_path=video_path,
                source_audio_path=audio_path,
                clip_crop_data=[res],
                b_roll_segments=b_rolls,
                output_path=clean_path,
            )
            compositor.render(plan)

            # Overlay
            overlay.overlay_subtitles(clean_path, transcript, final_path)

            # Package
            pkg = meta_gen.generate_metadata(clip, final_path, thumb_path)
            thumb_maker.generate_thumbnail(final_path, clip, thumb_path)

            with open(meta_path, "w") as f:
                f.write(pkg.model_dump_json(indent=2))

            # Upload
            if upload:
                target_platforms = platforms or pkg.platforms
                if "youtube" in target_platforms:
                    YouTubeUploader(self.cfg).upload(pkg)
                if "tiktok" in target_platforms:
                    TikTokUploader(self.cfg).upload(pkg)

    def cleanup(self):
        """Removes workspace files."""
        logger.info("Cleaning up workspace...")
        for f in self.workspace.glob("*"):
            if f.is_file() and f.suffix in [".mp4", ".wav", ".jpg", ".png", ".json"]:
                if f.name == "download_history.json":
                    continue
                try:
                    f.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete {f}: {e}")
