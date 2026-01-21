import sys
from pathlib import Path

from src.config_manager import ConfigManager
from src.ingestion.downloader import VideoDownloader
from src.intelligence.curator import ContentCurator
from src.intelligence.models import ViralClip
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
    
    logger.info("Starting AutoReelAI - Part 5: Semantic Retrieval")

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

    # 6. Retrieval Phase (Indexing & Matching)
    logger.info("Starting B-Roll Retrieval Engine...")
    indexer = LibraryIndexer(config_manager)
    indexer.index_library() # Scan assets/b_roll
    
    matcher = VisualMatcher(config_manager, indexer)
    
    # 7. Vision Phase & Integration
    if clips and video_path:
        logger.info("Starting Visual Processing...")
        cropper = SmartCropper(config_manager)
        crop_results = cropper.process_clips(video_path, clips, video_id)
        
        for i, _ in enumerate(crop_results):
            # Check for B-Roll for this clip
            clip = clips[i]
            
            # Get text context
            clip_text = get_text_for_range(transcript, clip.start_time, clip.end_time) if transcript else clip.reasoning
            
            # Find B-Roll
            b_roll_path = matcher.find_match(clip_text)
            
            if b_roll_path:
                logger.success(f"Clip {i}: Found B-Roll -> {b_roll_path}")
            else:
                logger.info(f"Clip {i}: No B-Roll match. Using Face Track.")

if __name__ == "__main__":
    main()