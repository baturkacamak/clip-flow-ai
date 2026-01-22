import argparse
import sys
from pathlib import Path

# Add current directory to path so python_core is importable
sys.path.append(str(Path(__file__).parent))

try:
    from python_core.config_manager import ConfigManager
    from python_core.pipeline import PipelineManager
    from python_core.utils.logger import setup_logger
except ImportError as e:
    print(f"Critical Configuration Error: {e}")
    print("Did you run 'python refactor.py' to restructure the project?")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="ClipFlowAI CLI")
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
            try:
                from python_core.worker import process_video_task

                if args.mode != "viral":
                    print("Async mode currently only supports viral mode.")
                    sys.exit(1)
                task = process_video_task.delay(args.url, topic=args.topic, upload=should_upload)
                print(f"Task dispatched: {task.id}")
            except ImportError:
                print("Worker module not found in python_core.")
        else:
            pipeline = PipelineManager(config, keep_temp=args.keep_temp)
            pipeline.run(
                url=args.url,
                topic=args.topic,
                upload=should_upload,
                platforms=args.platform,
                mode=args.mode,
                audio_path=args.audio,
            )

        if args.dry_run and args.upload:
            print("[DRY RUN] Skipping actual upload.")


if __name__ == "__main__":
    main()
