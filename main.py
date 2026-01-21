import sys
import json
from pathlib import Path
from loguru import logger
from src.config_manager import ConfigManager
from src.utils.logger import setup_logger
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

def get_text_for_range(transcript, start: float, end: float) -> str:
    text = []
    for seg in transcript.segments:
        seg_start = seg.start
        seg_end = seg.end
        if max(start, seg_start) < min(end, seg_end):
            text.append(seg.text)
    return " ".join(text)

def main():
    try:
        config_manager = ConfigManager()
    except Exception as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)

    logger = setup_logger(
        log_dir=config_manager.paths.log_dir,
        level="DEBUG"
    )
    
    logger.info("Starting AutoReelAI - Part 8: Packaging")

    # 1. Ingestion
    downloader = VideoDownloader(config_manager)
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
    logger.info(f"Ingestion: Checking {test_url}")

    download_result = downloader.download(test_url)
    
    video_path = None
    audio_path = None
    video_id = "aqz-KE-bpKQ"

    if download_result:
        video_path = download_result.get('video_path')
        audio_path = download_result.get('audio_path')
        video_id = download_result.get('id')
    else:
        workspace = Path(config_manager.paths.workspace_dir)
        vid_files = list(workspace.glob(f"*{video_id}*.mp4"))
        aud_files = list(workspace.glob(f"*{video_id}*.wav"))
        
        if vid_files:
            video_path = str(vid_files[0])
        if aud_files:
            audio_path = str(aud_files[0])
            
        if not video_path:
            logger.error("Video file not found.")
            sys.exit(1)

    # 2. Transcription
    transcript = None
    if audio_path:
        transcriber = AudioTranscriber(config_manager)
        transcript = transcriber.transcribe(audio_path, video_id)

    # 3. Curation
    clips = []
    if transcript:
        curator = ContentCurator(config_manager)
        curation_result = curator.curate(transcript)
        clips = curation_result.clips
        
        if not clips:
            logger.warning("No clips found via LLM. Using MOCK clip.")
            clips = [
                ViralClip(
                    start_time=10.0,
                    end_time=25.0,
                    title="Big Buck Bunny Viral",
                    virality_score=99,
                    reasoning="Manual Test",
                    category="Animation"
                )
            ]

    # 4. Retrieval & Vision
    indexer = LibraryIndexer(config_manager)
    indexer.index_library()
    matcher = VisualMatcher(config_manager, indexer)
    cropper = SmartCropper(config_manager)
    
    crop_results = []
    b_roll_segments = []
    
    if clips and video_path:
        crop_results = cropper.process_clips(video_path, clips, video_id)
        
        for i, _ in enumerate(crop_results):
            clip = clips[i]
            clip_text = get_text_for_range(transcript, clip.start_time, clip.end_time) if transcript else clip.reasoning
            b_roll_path = matcher.find_match(clip_text)
            
            if b_roll_path:
                b_roll_segments.append(BRollSegment(
                    start=clip.start_time,
                    end=clip.end_time,
                    video_path=b_roll_path
                ))

    # 5. Editing & Overlay & Packaging
    # Output Directory
    output_dir = Path(config_manager.paths.output_dir) / video_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    clean_output_path = str(output_dir / "clean_output.mp4")
    final_output_path = str(output_dir / "final_with_subs.mp4")
    thumbnail_path = str(output_dir / "thumbnail.jpg")
    metadata_path = str(output_dir / "metadata.json")
    
    if crop_results and video_path:
        logger.info("Compositing...")
        compositor = VideoCompositor(config_manager)
        plan = RenderPlan(
            source_video_path=video_path,
            source_audio_path=audio_path,
            clip_crop_data=crop_results,
            b_roll_segments=b_roll_segments,
            output_path=clean_output_path
        )
        compositor.render(plan)

        if Path(clean_output_path).exists() and transcript:
            logger.info("Overlays...")
            overlay = SubtitleOverlay(config_manager)
            overlay.overlay_subtitles(clean_output_path, transcript, final_output_path)
            
            # Packaging
            logger.info("Packaging...")
            # Use the first clip for metadata context (or aggregate?)
            # Assuming one clip per render for now based on loop structure
            target_clip = clips[0] 
            
            meta_gen = MetadataGenerator(config_manager)
            pkg = meta_gen.generate_metadata(target_clip, final_output_path, thumbnail_path)
            
            thumb_maker = ThumbnailMaker(config_manager)
            thumb_maker.generate_thumbnail(final_output_path, target_clip, thumbnail_path)
            
            # Save Metadata
            with open(metadata_path, "w") as f:
                f.write(pkg.model_dump_json(indent=2))
                
            logger.success(f"Package created at {output_dir}")

if __name__ == "__main__":
    main()
