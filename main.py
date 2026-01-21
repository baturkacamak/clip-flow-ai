import sys
from src.config_manager import ConfigManager
from src.utils.logger import setup_logger
from src.ingestion.downloader import VideoDownloader


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
        level="DEBUG",  # Set to DEBUG for initial testing
    )

    logger.info("Starting AutoReelAI - Part 1: Ingestion Module")

    # 3. Initialize Downloader
    downloader = VideoDownloader(config_manager)

    # 4. Test Download
    # Using "Big Buck Bunny" (High Res) to pass quality checks
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
    logger.info(f"Testing download with URL: {test_url}")

    result = downloader.download(test_url)

    if result:
        logger.success("Test Download Successful!")
        logger.info(f"Video: {result['video_path']}")
        logger.info(f"Audio: {result['audio_path']}")
        logger.info(f"Metadata: {result['metadata_path']}")
    else:
        logger.error("Test Download Failed.")


if __name__ == "__main__":
    main()
