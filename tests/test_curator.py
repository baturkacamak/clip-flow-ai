import pytest

from python_core.intelligence.curator import ContentCurator
from python_core.intelligence.models import ViralClip
from python_core.transcription.models import Segment, TranscriptionResult


@pytest.fixture
def mock_config_manager(tmp_path):
    class MockIntelligenceConfig:
        llm_provider = "openai"
        openai_api_key = "sk-fake-key"
        anthropic_api_key = None
        model_name = "gpt-4-test"
        virality_threshold = 70
        focus_topic = None

    class MockConfigManager:
        intelligence = MockIntelligenceConfig()
        paths = None  # Not used

    return MockConfigManager()


def test_format_transcript(mock_config_manager):
    curator = ContentCurator(mock_config_manager)
    transcript = TranscriptionResult(
        video_id="test",
        language="en",
        segments=[
            Segment(start=0.0, end=5.0, text="Hello world."),
            Segment(start=5.0, end=10.0, text="This is a test."),
        ],
    )
    formatted = curator._format_transcript(transcript)
    assert "[00:00] SPEAKER_00: Hello world." in formatted
    assert "[00:05] SPEAKER_00: This is a test." in formatted


def test_curation_mock(mocker, mock_config_manager):
    # Mock the client
    mock_client = mocker.patch("python_core.intelligence.curator.instructor.from_openai")
    mock_create = mock_client.return_value.chat.completions.create

    # Mock response
    mock_clip = ViralClip(
        start_time=10.0, end_time=20.0, title="Viral Moment", virality_score=85, reasoning="Funny", category="Humor"
    )

    class MockResponse:
        clips = [mock_clip]

    mock_create.return_value = MockResponse()

    curator = ContentCurator(mock_config_manager)

    transcript = TranscriptionResult(video_id="test", language="en", segments=[])
    result = curator.curate(transcript)

    assert len(result.clips) == 1
    assert result.clips[0].title == "Viral Moment"
    assert result.clips[0].virality_score == 85


def test_curator_no_key(mock_config_manager):
    # Unset key
    mock_config_manager.intelligence.openai_api_key = None
    mock_config_manager.intelligence.anthropic_api_key = None

    curator = ContentCurator(mock_config_manager)

    # Should handle it gracefully or return empty
    transcript = TranscriptionResult(video_id="test", language="en", segments=[])
    result = curator.curate(transcript)

    assert len(result.clips) == 0


def test_curator_api_error(mocker, mock_config_manager):
    mock_client = mocker.patch("python_core.intelligence.curator.instructor.from_openai")
    mock_client.return_value.chat.completions.create.side_effect = Exception("API Error")

    curator = ContentCurator(mock_config_manager)
    transcript = TranscriptionResult(video_id="test", language="en", segments=[])

    # Should catch and return empty list
    result = curator.curate(transcript)
    assert len(result.clips) == 0
