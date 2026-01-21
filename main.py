import sys
from pathlib import Path
from src.config_manager import ConfigManager
from src.utils.logger import setup_logger
from src.ingestion.downloader import VideoDownloader
from src.transcription.engine import AudioTranscriber
from src.intelligence.curator import ContentCurator

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
    
    logger.info("Starting AutoReelAI - Part 3: Semantic Intelligence")

    # 3. Ingestion Phase
    downloader = VideoDownloader(config_manager)
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
    logger.info(f"Ingestion: Checking {test_url}")

    download_result = downloader.download(test_url)
    
    audio_path = None
    video_id = "aqz-KE-bpKQ"

    if download_result:
        audio_path = download_result.get('audio_path')
        video_id = download_result.get('id')
    else:
        workspace = Path(config_manager.paths.workspace_dir)
        potential_files = list(workspace.glob(f"*{video_id}*.wav"))
        if potential_files:
            audio_path = str(potential_files[0])
            logger.info(f"Found existing audio file: {audio_path}")
        else:
            logger.warning("Download skipped and no local audio file found. Cannot proceed.")
            sys.exit(0)

    # 4. Transcription Phase
    transcript = None
    if audio_path:
        transcriber = AudioTranscriber(config_manager)
        transcript = transcriber.transcribe(audio_path, video_id)

    # 5. Curation Phase
    if transcript:
        logger.info("Starting Curation...")
        curator = ContentCurator(config_manager)
        curation_result = curator.curate(transcript)
        
        if curation_result.clips:
            logger.success(f"Found {len(curation_result.clips)} viral clips!")
            for clip in curation_result.clips:
                print("\n" + "="*40)
                print(f"Title: {clip.title}")
                print(f"Score: {clip.virality_score}/100 | Category: {clip.category}")
                print(f"Time: {clip.start_time:.1f}s - {clip.end_time:.1f}s")
                print(f"Reason: {clip.reasoning}")
                print("="*40)
        else:
            logger.warning("No clips found (or LLM unavailable).")
    else:
        logger.error("Transcription failed, cannot curate.")

if __name__ == "__main__":
    main()