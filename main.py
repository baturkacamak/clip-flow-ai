import sys
from pathlib import Path
from typing import List

from src.config_manager import ConfigManager
from src.editing.compositor import VideoCompositor
from src.editing.models import BRollSegment, RenderPlan
from src.ingestion.downloader import VideoDownloader
from src.intelligence.curator import ContentCurator
from src.intelligence.models import ViralClip
from src.overlay.subtitle import SubtitleOverlay
from src.retrieval.indexer import LibraryIndexer
from src.retrieval.matcher import VisualMatcher
from src.transcription.engine import AudioTranscriber
from src.utils.logger import setup_logger
from src.vision.cropper import SmartCropper


def get_text_for_range(transcript, start: float, end: float) -> str:
    """Extracts text from transcript for a given time range."""
    text = []
    for seg in transcript.segments:
        # Check overlap
        seg_start = seg.start
        seg_end = seg.end
        if max(start, seg_start) < min(end, seg_end):
            text.append(seg.text)
    return " ".join(text)

def main():
    # 1. Initialize Configuration
    try:
        config_manager = ConfigManager()
    except Exception as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)

    # 2. Setup Logging
    logger = setup_logger(
        log_dir=config_manager.paths.log_dir,
        level="DEBUG"
    )
    
    logger.info("Starting AutoReelAI - Part 7: Subtitle Overlay")

    # 3. Ingestion Phase
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
            logger.info(f"Found existing video file: {video_path}")
        if aud_files:
            audio_path = str(aud_files[0])
            logger.info(f"Found existing audio file: {audio_path}")
            
        if not video_path:
            logger.error("Video file not found. Cannot proceed.")
            sys.exit(1)

    # 4. Transcription Phase
    transcript = None
    if audio_path:
        transcriber = AudioTranscriber(config_manager)
        transcript = transcriber.transcribe(audio_path, video_id)

    # 5. Curation Phase
    clips = []
    if transcript:
        logger.info("Starting Curation...")
        curator = ContentCurator(config_manager)
        curation_result = curator.curate(transcript)
        clips = curation_result.clips
        
        if not clips:
            logger.warning("No clips found via LLM. Using MOCK clip for testing.")
            clips = [
                ViralClip(
                    start_time=10.0,
                    end_time=25.0,
                    title="Mock Viral Clip",
                    virality_score=99,
                    reasoning="Manual Test",
                    category="Test"
                )
            ]

    # 6. Retrieval & Vision Phases
    logger.info("Starting Visual Intelligence & Retrieval...")
    indexer = LibraryIndexer(config_manager)
    indexer.index_library()
    matcher = VisualMatcher(config_manager, indexer)
    cropper = SmartCropper(config_manager)
    
    crop_results = []
    b_roll_segments: List[BRollSegment] = []
    
    if clips and video_path:
        crop_results = cropper.process_clips(video_path, clips, video_id)
        
        for i, _ in enumerate(crop_results):
            clip = clips[i]
            
            # Get text context
            clip_text = get_text_for_range(transcript, clip.start_time, clip.end_time) if transcript else clip.reasoning
            
            # Find B-Roll
            b_roll_path = matcher.find_match(clip_text)
            
            if b_roll_path:
                logger.success(f"Clip {i}: Found B-Roll -> {b_roll_path}")
                b_roll_segments.append(BRollSegment(
                    start=clip.start_time,
                    end=clip.end_time,
                    video_path=b_roll_path
                ))
            else:
                logger.info(f"Clip {i}: No B-Roll match. Using Face Track.")

    # 7. Compositing Phase
    clean_output_path = str(Path(config_manager.paths.output_dir) / "clean_output.mp4")
    
    if crop_results and video_path:
        logger.info("Starting Compositing...")
        compositor = VideoCompositor(config_manager)
        
        plan = RenderPlan(
            source_video_path=video_path,
            source_audio_path=audio_path,
            clip_crop_data=crop_results,
            b_roll_segments=b_roll_segments,
            output_path=clean_output_path
        )
        
        compositor.render(plan)

    # 8. Subtitle Overlay Phase
    final_output_path = str(Path(config_manager.paths.output_dir) / "final_with_subs.mp4")
    
    if Path(clean_output_path).exists() and transcript:
        logger.info("Starting Subtitle Overlay...")
        overlay = SubtitleOverlay(config_manager)
        overlay.overlay_subtitles(clean_output_path, transcript, final_output_path)
    else:
        logger.warning("Clean output not found or transcript missing. Skipping subtitles.")

if __name__ == "__main__":
    main()