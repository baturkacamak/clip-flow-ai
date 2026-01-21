import pytest
from unittest.mock import MagicMock
from pathlib import Path
from src.modes.story_builder import StoryBuilder
from src.config_manager import ConfigManager
from src.transcription.models import TranscriptionResult, Segment
from src.editing.models import RenderPlan, BRollSegment
from src.pipeline import PipelineManager

@pytest.fixture
def mock_config_manager(tmp_path):
    class MockPaths:
        workspace_dir = str(tmp_path / "workspace")
        output_dir = str(tmp_path / "outputs")
        log_dir = str(tmp_path / "logs")
        cookies_file = None
        history_file = str(tmp_path / "history.json")

    class MockRetrievalConfig:
        deduplication_window = 5

    class MockConfigManager:
        paths = MockPaths()
        retrieval = MockRetrievalConfig()
        editing = MagicMock()
        intelligence = MagicMock()
        
        # Transcription config mocks must be strings/valid types for AudioTranscriber init
        transcription = MagicMock()
        transcription.model_size = "tiny"
        transcription.device = "cpu"
        transcription.compute_type = "int8"
        
        downloader = MagicMock()

    return MockConfigManager()

@pytest.fixture
def mock_transcriber(mocker):
    mock = mocker.patch("src.modes.story_builder.AudioTranscriber")
    instance = mock.return_value
    
    # Setup default response
    transcript = TranscriptionResult(
        video_id="test_story",
        language="en",
        segments=[
            Segment(start=0.0, end=5.0, text="This is the first sentence."),
            Segment(start=5.0, end=10.0, text="This is the second sentence.")
        ]
    )
    instance.transcribe.return_value = transcript
    return instance

@pytest.fixture
def mock_matcher(mocker):
    mock = mocker.patch("src.modes.story_builder.VisualMatcher")
    instance = mock.return_value
    # Return a dummy path when find_match is called
    instance.find_match.return_value = "assets/b_roll/dummy.mp4"
    return instance

def test_story_builder_flow(mock_config_manager, mock_transcriber, mock_matcher, tmp_path):
    """Test that StoryBuilder creates a valid RenderPlan from audio."""
    # Setup
    audio_path = tmp_path / "voiceover.mp3"
    audio_path.touch()
    
    builder = StoryBuilder(mock_config_manager)
    builder.set_matcher(mock_matcher)
    
    # Execution
    output_path = str(tmp_path / "output.mp4")
    plan, transcript = builder.build_plan(str(audio_path), output_path)
    
    # Verification
    assert plan is not None
    assert transcript is not None
    assert plan.source_audio_path == str(audio_path)
    assert len(plan.b_roll_segments) > 0
    # We expect 2 segments based on the transcript (0-5, 5-10)
    # The builder logic merges short clips (<3s), these are 5s, so should be 2.
    assert len(plan.b_roll_segments) == 2
    assert plan.b_roll_segments[0].video_path == "assets/b_roll/dummy.mp4"

def test_story_builder_no_audio(mock_config_manager, mocker):
    """Test failure when audio file is missing."""
    mocker.patch("src.modes.story_builder.AudioTranscriber")
    builder = StoryBuilder(mock_config_manager)
    plan, _ = builder.build_plan("non_existent.mp3", "out.mp4")
    assert plan is None

def test_pipeline_story_branch(mocker, mock_config_manager, tmp_path):
    """Test that PipelineManager routes to _run_story_mode correctly."""
    # Mock internal methods/classes
    mock_run_story = mocker.patch.object(PipelineManager, "_run_story_mode")
    mock_run_viral = mocker.patch.object(PipelineManager, "_run_viral_mode")
    
    pipeline = PipelineManager(mock_config_manager, keep_temp=True)
    
    # Test Viral Mode (Default)
    pipeline.run(url="http://test.com", mode="viral")
    mock_run_viral.assert_called_once()
    mock_run_story.assert_not_called()
    
    mock_run_viral.reset_mock()
    
    # Test Story Mode
    audio_path = str(tmp_path / "test.mp3")
    pipeline.run(audio_path=audio_path, mode="story")
    mock_run_story.assert_called_once_with(audio_path, False, None)
    mock_run_viral.assert_not_called()

def test_pipeline_story_mode_execution(mocker, mock_config_manager, tmp_path):
    """Test the internal execution of _run_story_mode."""
    # Mock dependencies initialized inside _run_story_mode
    mocker.patch("src.pipeline.LibraryIndexer")
    mocker.patch("src.pipeline.VisualMatcher")
    
    mock_builder_cls = mocker.patch("src.pipeline.StoryBuilder")
    mock_builder = mock_builder_cls.return_value
    mock_builder.build_plan.return_value = (MagicMock(), MagicMock()) # plan, transcript
    
    mock_compositor_cls = mocker.patch("src.pipeline.VideoCompositor")
    mock_overlay_cls = mocker.patch("src.pipeline.SubtitleOverlay")
    
    pipeline = PipelineManager(mock_config_manager)
    audio_path = str(tmp_path / "voice.mp3")
    
    # Execute
    pipeline._run_story_mode(audio_path, False, None)
    
    # Verify calls
    mock_builder.build_plan.assert_called_once()
    mock_compositor_cls.return_value.render_story_mode.assert_called_once()
    mock_overlay_cls.return_value.overlay_subtitles.assert_called_once()
