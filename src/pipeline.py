import shutil
from pathlib import Path
from typing import Optional, List
from loguru import logger
from src.config_manager import ConfigManager
from src.ingestion.downloader import VideoDownloader
from src.transcription.engine import AudioTranscriber
from src.intelligence.curator import ContentCurator
from src.intelligence.models import ViralClip
from src.vision.cropper import SmartCropper
from src.retrieval.indexer import LibraryIndexer
from src.retrieval.matcher import VisualMatcher
from src.editing.compositor import VideoCompositor
from src.editing.models import RenderPlan, BRollSegment
from src.overlay.subtitle import SubtitleOverlay
from src.packaging.generator import MetadataGenerator
from src.packaging.thumbnail import ThumbnailMaker
from src.distribution.youtube import YouTubeUploader
from src.distribution.tiktok_browser import TikTokUploader

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

    def run(self, url: str, topic: Optional[str] = None, upload: bool = False, platforms: Optional[List[str]] = None) -> None:
        logger.info(f"Starting Pipeline for {url}")
        
        # Override topic if provided
        if topic:
            self.cfg.intelligence.focus_topic = topic

        try:
            # 1. Ingestion
            downloader = VideoDownloader(self.cfg)
            dl_res = downloader.download(url)
            if not dl_res:
                logger.error("Download failed.")
                return
            
            video_path = dl_res['video_path']
            audio_path = dl_res.get('audio_path')
            video_id = dl_res['id']
            
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
                    output_path=clean_path
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

        finally:
            if not self.keep_temp:
                self.cleanup()

    def cleanup(self):
        """Removes workspace files."""
        logger.info("Cleaning up workspace...")
        # Be careful not to delete chrome_db or history
        # Delete only mp4/wav in workspace? 
        # Or just specific files we created.
        # Implementation: Find all media files in workspace and delete?
        # User requirement: "delete ... intermediate frames ... keeping only final result"
        # Final result is in output_dir. Workspace is temp.
        # But workspace has chroma_db which is persistent.
        # So we should NOT delete workspace root.
        # We delete *files* in workspace, not directories (except maybe frames dir if any).
        
        for f in self.workspace.glob("*"):
            if f.is_file() and f.suffix in ['.mp4', '.wav', '.jpg', '.png', '.json']:
                # Keep history
                if f.name == "download_history.json":
                    continue
                try:
                    f.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete {f}: {e}")