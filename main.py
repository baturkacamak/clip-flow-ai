import sys
from pathlib import Path

from src.config_manager import ConfigManager
from src.ingestion.downloader import VideoDownloader
from src.intelligence.curator import ContentCurator
from src.intelligence.models import ViralClip
from src.transcription.engine import AudioTranscriber
from src.utils.logger import setup_logger
from src.vision.cropper import SmartCropper


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
    
    logger.info("Starting AutoReelAI - Part 4: Visual Intelligence")

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
        # Search for files
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
            logger.warning("No clips found via LLM. Using MOCK clip for Part 4 testing.")
            # Mock clip for Big Buck Bunny (approx 10s to 25s)
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

    # 6. Vision Phase (Smart Cropping)
    if clips and video_path:
        logger.info("Starting Smart Cropping...")
        cropper = SmartCropper(config_manager)
        crop_results = cropper.process_clips(video_path, clips, video_id)
        
        logger.success(f"Generated crop data for {len(crop_results)} clips.")
        for res in crop_results:
            logger.info(f"Clip {res.clip_id}: {len(res.frames)} frames processed.")

if __name__ == "__main__":
    main()
