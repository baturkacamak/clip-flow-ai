import argparse
import sys

from src.config_manager import ConfigManager
from src.pipeline import PipelineManager
from src.utils.logger import setup_logger


def main():
    parser = argparse.ArgumentParser(description="AutoReelAI CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Process Command
    process_parser = subparsers.add_parser("process", help="Process a video URL or Audio file")
    
    # Inputs
    process_parser.add_argument("url", nargs="?", help="YouTube URL (Required for viral mode)")
    process_parser.add_argument("--mode", choices=["viral", "story"], default="viral", help="Processing mode")
    process_parser.add_argument("--audio", help="Path to input audio (Required for story mode)")
    
    # Options
    process_parser.add_argument("--topic", help="Focus topic for curation")
    process_parser.add_argument("--upload", action="store_true", help="Upload to platforms")
    process_parser.add_argument("--dry-run", action="store_true", help="Skip actual upload")
    process_parser.add_argument("--keep-temp", action="store_true", help="Keep temporary files")
    process_parser.add_argument("--platform", action="append", help="Specific platform(s)")
    process_parser.add_argument("--async-mode", action="store_true", help="Dispatch to Celery worker")
    
    args = parser.parse_args()
    
    # Setup
    try:
        config = ConfigManager()
    except Exception as e:
        print(f"Config Error: {e}")
        sys.exit(1)
        
    setup_logger(log_dir=config.paths.log_dir)
    
    if args.command == "process":
        should_upload = args.upload and not args.dry_run
        
        # Validation
        if args.mode == "viral" and not args.url:
            print("Error: URL is required for viral mode.")
            sys.exit(1)
        if args.mode == "story" and not args.audio:
            print("Error: --audio path is required for story mode.")
            sys.exit(1)
        
        if args.async_mode:
            # We assume worker handles mode/audio logic update too, but for now just viral supported in async?
            # Or we update task signature. 
            # Given constraints, let's assume async supports basic viral for now or we update it.
            # I will pass kwargs to task if possible, or just log not supported.
            from src.worker import process_video_task
            if args.mode != "viral":
                print("Async mode currently only supports viral mode.")
                sys.exit(1)
            task = process_video_task.delay(args.url, topic=args.topic, upload=should_upload)
            print(f"Task dispatched: {task.id}")
        else:
            pipeline = PipelineManager(config, keep_temp=args.keep_temp)
            pipeline.run(
                url=args.url,
                topic=args.topic,
                upload=should_upload,
                platforms=args.platform,
                mode=args.mode,
                audio_path=args.audio
            )
        
        if args.dry_run and args.upload:
            print("[DRY RUN] Skipping actual upload.")

if __name__ == "__main__":
    main()