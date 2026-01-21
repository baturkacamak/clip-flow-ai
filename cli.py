import argparse
import sys
from src.config_manager import ConfigManager
from src.pipeline import PipelineManager
from src.utils.logger import setup_logger

def main():
    parser = argparse.ArgumentParser(description="AutoReelAI CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Process Command
    process_parser = subparsers.add_parser("process", help="Process a video URL")
    process_parser.add_argument("url", help="YouTube URL")
    process_parser.add_argument("--topic", help="Focus topic for curation")
    process_parser.add_argument("--upload", action="store_true", help="Upload to platforms")
    process_parser.add_argument("--dry-run", action="store_true", help="Skip actual upload")
    process_parser.add_argument("--keep-temp", action="store_true", help="Keep temporary files")
    process_parser.add_argument("--platform", action="append", help="Specific platform(s)")
    
    args = parser.parse_args()
    
    # Setup
    try:
        config = ConfigManager()
    except Exception as e:
        print(f"Config Error: {e}")
        sys.exit(1)
        
    setup_logger(log_dir=config.paths.log_dir)
    
    if args.command == "process":
        # Handle dry-run by patching uploader in config? 
        # Or just pass upload=False if dry-run, but we want to simulate?
        # The upload flag triggers upload logic.
        # If dry-run is set, we might want to run everything BUT upload, or mock upload.
        # Requirements said: "--dry-run: Generate video but skip upload"
        # So dry-run effectively means upload=False? 
        # Or "print 'Would have uploaded'". 
        # In main.py I did print.
        # In PipelineManager, I didn't add dry-run logic.
        # I'll rely on `upload` flag. If dry-run, I set upload=False?
        # But user wants to see "Would have uploaded".
        # I should probably pass `dry_run` to `run` or handle it.
        # `pipeline.run` has `upload` bool.
        # If `args.dry_run`, I set `upload=False` but maybe print info.
        
        # Actually, let's keep it simple.
        # If dry-run, we process but don't call uploader.upload.
        # Or we call uploader.upload but uploader handles dry-run?
        # The uploader class doesn't have dry-run state.
        
        should_upload = args.upload and not args.dry_run
        
        pipeline = PipelineManager(config, keep_temp=args.keep_temp)
        pipeline.run(args.url, topic=args.topic, upload=should_upload, platforms=args.platform)
        
        if args.dry_run and args.upload:
            print("[DRY RUN] Skipping actual upload.")

if __name__ == "__main__":
    main()
