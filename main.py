import sys
from pathlib import Path

from src.config_manager import ConfigManager
from src.ingestion.downloader import VideoDownloader
from src.transcription.engine import AudioTranscriber
from src.utils.logger import setup_logger


def main():
    # 1. Initialize Configuration
    try:
        config_manager = ConfigManager()
    except Exception as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)

    # 2. Setup Logging
    logger = setup_logger(log_dir=config_manager.paths.log_dir, level="DEBUG")

    logger.info("Starting AutoReelAI - Part 2: Audio Intelligence")

    # 3. Ingestion Phase
    downloader = VideoDownloader(config_manager)

    # Using "Big Buck Bunny" (High Res)
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
    logger.info(f"Ingestion: Checking {test_url}")

    download_result = downloader.download(test_url)

    audio_path = None
    video_id = "aqz-KE-bpKQ"  # Known ID for the test URL

    if download_result:
        audio_path = download_result.get("audio_path")
        video_id = download_result.get("id")
    else:
        # Fallback for testing if already downloaded (Part 1 artifact)
        # We construct the expected path based on what we saw in Part 1
        workspace = Path(config_manager.paths.workspace_dir)
        # Search for the audio file with the known ID
        potential_files = list(workspace.glob(f"*{video_id}*.wav"))
        if potential_files:
            audio_path = str(potential_files[0])
            logger.info(f"Found existing audio file: {audio_path}")
        else:
            logger.warning(
                "Download skipped and no local audio file found. Cannot proceed to transcription."
            )
            sys.exit(0)

    # 4. Transcription Phase
    if audio_path:
        transcriber = AudioTranscriber(config_manager)
        transcript = transcriber.transcribe(audio_path, video_id)

        if transcript:
            # Print Snippet
            logger.success("Transcription Result Snippet:")
            print(f"Language: {transcript.language}")
            print(f"Processing Time: {transcript.processing_time:.2f}s")

            # Print first 3 segments
            for i, seg in enumerate(transcript.segments[:3]):
                print(f"[{seg.start:.2f} - {seg.end:.2f}] {seg.speaker}: {seg.text}")
                # Print words for the first segment only
                if i == 0:
                    print(
                        f"   > Words: {', '.join([f'{w.word}({w.start:.1f})' for w in seg.words])}"
                    )
        else:
            logger.error("Transcription returned no result.")


if __name__ == "__main__":
    main()
