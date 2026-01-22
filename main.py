import argparse
import sys
from pathlib import Path

from python_core.config_manager import ConfigManager
from python_core.distribution.tiktok_browser import TikTokUploader
from python_core.distribution.youtube import YouTubeUploader
from python_core.editing.compositor import VideoCompositor
from python_core.editing.models import BRollSegment, RenderPlan
from python_core.ingestion.downloader import VideoDownloader
from python_core.intelligence.curator import ContentCurator
from python_core.intelligence.models import ViralClip
from python_core.overlay.subtitle import SubtitleOverlay
from python_core.packaging.generator import MetadataGenerator
from python_core.packaging.thumbnail import ThumbnailMaker
from python_core.retrieval.indexer import LibraryIndexer
from python_core.retrieval.matcher import VisualMatcher
from python_core.transcription.engine import AudioTranscriber
from python_core.utils.logger import setup_logger
from python_core.vision.cropper import SmartCropper


def get_text_for_range(transcript, start: float, end: float) -> str:
    text = []
    for seg in transcript.segments:
        seg_start = seg.start
        seg_end = seg.end
        if max(start, seg_start) < min(end, seg_end):
            text.append(seg.text)
    return " ".join(text)


def main():
    parser = argparse.ArgumentParser(description="ClipFlowAI Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Simulate uploads without sending data")
    args = parser.parse_args()

    try:
        config_manager = ConfigManager()
    except Exception as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)

    logger = setup_logger(log_dir=config_manager.paths.log_dir, level="DEBUG")

    logger.info("Starting ClipFlowAI - Part 9: Distribution")
    if args.dry_run:
        logger.info("DRY RUN MODE ACTIVE")

    # 1. Ingestion
    downloader = VideoDownloader(config_manager)
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
    logger.info(f"Ingestion: Checking {test_url}")

    download_result = downloader.download(test_url)

    video_path = None
    audio_path = None
    video_id = "aqz-KE-bpKQ"

    if download_result:
        video_path = download_result.get("video_path")
        audio_path = download_result.get("audio_path")
        video_id = download_result.get("id")
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
                    category="Animation",
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
                b_roll_segments.append(BRollSegment(start=clip.start_time, end=clip.end_time, video_path=b_roll_path))

    # 5. Editing & Overlay & Packaging
    output_dir = Path(config_manager.paths.output_dir) / video_id
    output_dir.mkdir(parents=True, exist_ok=True)

    clean_output_path = str(output_dir / "clean_output.mp4")
    final_output_path = str(output_dir / "final_with_subs.mp4")
    thumbnail_path = str(output_dir / "thumbnail.jpg")
    metadata_path = str(output_dir / "metadata.json")

    pkg = None

    if crop_results and video_path:
        logger.info("Compositing...")
        compositor = VideoCompositor(config_manager)
        plan = RenderPlan(
            source_video_path=video_path,
            source_audio_path=audio_path,
            clip_crop_data=crop_results,
            b_roll_segments=b_roll_segments,
            output_path=clean_output_path,
        )
        compositor.render(plan)

        if Path(clean_output_path).exists() and transcript:
            logger.info("Overlays...")
            overlay = SubtitleOverlay(config_manager)
            overlay.overlay_subtitles(clean_output_path, transcript, final_output_path)

            logger.info("Packaging...")
            target_clip = clips[0]

            meta_gen = MetadataGenerator(config_manager)
            pkg = meta_gen.generate_metadata(target_clip, final_output_path, thumbnail_path)

            thumb_maker = ThumbnailMaker(config_manager)
            thumb_maker.generate_thumbnail(final_output_path, target_clip, thumbnail_path)

            with open(metadata_path, "w") as f:
                f.write(pkg.model_dump_json(indent=2))

            logger.success(f"Package created at {output_dir}")

    # 6. Distribution
    if pkg and Path(final_output_path).exists():
        logger.info("Starting Distribution...")

        if args.dry_run:
            logger.info(f"[DRY RUN] Would upload to YouTube: {pkg.title}")
            logger.info(f"[DRY RUN] Would upload to TikTok: {pkg.title}")
        else:
            # YouTube
            if "youtube" in pkg.platforms:
                yt_uploader = YouTubeUploader(config_manager)
                yt_uploader.upload(pkg)

            # TikTok
            if "tiktok" in pkg.platforms:
                tt_uploader = TikTokUploader(config_manager)
                tt_uploader.upload(pkg)


if __name__ == "__main__":
    main()
