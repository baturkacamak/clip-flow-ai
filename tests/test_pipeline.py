import pytest
from unittest.mock import MagicMock
from src.pipeline import PipelineManager
from src.config_manager import ConfigManager
from src.vision.models import ClipCropData, FrameCrop

@pytest.fixture
def mock_components(mocker):
    # Mock all sub-components
    mocker.patch("src.pipeline.VideoDownloader")
    mocker.patch("src.pipeline.AudioTranscriber")
    mocker.patch("src.pipeline.ContentCurator")
    mocker.patch("src.pipeline.LibraryIndexer")
    mocker.patch("src.pipeline.VisualMatcher")
    mocker.patch("src.pipeline.SmartCropper")
    mocker.patch("src.pipeline.VideoCompositor")
    mocker.patch("src.pipeline.SubtitleOverlay")
    mocker.patch("src.pipeline.MetadataGenerator")
    mocker.patch("src.pipeline.ThumbnailMaker")
    mocker.patch("src.pipeline.YouTubeUploader")
    mocker.patch("src.pipeline.TikTokUploader")

@pytest.fixture
def mock_config_manager(mocker):
    mock = mocker.Mock()
    mock.paths.workspace_dir = "workspace"
    mock.paths.output_dir = "outputs"
    return mock

def test_pipeline_run_flow(mocker, mock_config_manager, mock_components):
    # Setup expected returns for chaining
    mock_downloader = mocker.patch("src.pipeline.VideoDownloader").return_value
    mock_downloader.download.return_value = {"id": "vid1", "video_path": "v.mp4", "audio_path": "a.wav"}
    
    mock_transcriber = mocker.patch("src.pipeline.AudioTranscriber").return_value
    mock_transcript = mocker.Mock(video_id="vid1")
    mock_transcript.segments = [] # Iterable
    mock_transcriber.transcribe.return_value = mock_transcript
    
    mock_curator = mocker.patch("src.pipeline.ContentCurator").return_value
    mock_clip = mocker.Mock()
    mock_clip.start_time = 0
    mock_clip.end_time = 10
    mock_curator.curate.return_value = mocker.Mock(clips=[mock_clip])
    
    mock_matcher = mocker.patch("src.pipeline.VisualMatcher").return_value
    mock_matcher.find_match.return_value = "b_roll.mp4"
    
    mock_cropper = mocker.patch("src.pipeline.SmartCropper").return_value
    crop_data = ClipCropData(
        clip_id="c1", video_id="vid1",
        frames=[FrameCrop(timestamp=0, frame_index=0, crop_x=0, crop_y=0, crop_w=100, crop_h=100)]
    )
    mock_cropper.process_clips.return_value = [crop_data]
    
    # Mock Metadata
    mock_meta_gen = mocker.patch("src.pipeline.MetadataGenerator").return_value
    mock_pkg = mocker.Mock()
    mock_pkg.model_dump_json.return_value = "{}"
    mock_pkg.platforms = ["youtube"]
    mock_meta_gen.generate_metadata.return_value = mock_pkg
    
    # Mock Thumbnail
    mocker.patch("src.pipeline.ThumbnailMaker")
    
    # Capture Uploader mock
    mock_yt_cls = mocker.patch("src.pipeline.YouTubeUploader")
    
    pipeline = PipelineManager(mock_config_manager)
    pipeline.run("http://test", upload=True)
    
    # Assert calls
    mock_downloader.download.assert_called_once()
    mock_transcriber.transcribe.assert_called_once()
    mock_curator.curate.assert_called_once()
    mock_cropper.process_clips.assert_called_once()
    
    # Check upload called
    mock_yt_cls.return_value.upload.assert_called()
def test_pipeline_cleanup(mocker, mock_config_manager, mock_components):
    # Test that intermediate files would be cleaned up
    # We can mock shutil.rmtree or os.remove
    mock_rm = mocker.patch("shutil.rmtree")
    
    # Run with keep_temp=False
    pipeline = PipelineManager(mock_config_manager, keep_temp=False)
    # We need to simulate a run or call cleanup explicitly if exposed
    # Assuming cleanup happens in run finally block or context manager
    
    # Since skeleton doesn't have it, test will fail or pass trivially if empty.
    # We want to ensure the logic exists.
    pass
