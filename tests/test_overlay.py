
import pytest

from python_core.overlay.subtitle import SubtitleOverlay
from python_core.transcription.models import Segment, TranscriptionResult, Word
from python_core.utils.text_utils import chunk_words


@pytest.fixture
def sample_words():
    return [
        Word(word="Hello", start=0.0, end=0.5, score=1.0),
        Word(word="world", start=0.5, end=1.0, score=1.0),
        Word(word="this", start=1.0, end=1.5, score=1.0),
        Word(word="is", start=1.5, end=2.0, score=1.0),
        Word(word="test", start=2.0, end=2.5, score=1.0),
    ]

def test_chunk_words(sample_words):
    groups = chunk_words(sample_words, max_words=2)
    assert len(groups) == 3
    assert groups[0].text == "Hello world"
    assert groups[0].start == 0.0
    assert groups[0].end == 1.0
    assert groups[2].text == "test"

@pytest.fixture
def mock_config_manager(mocker):
    mock = mocker.Mock()
    mock.overlay.font_path = "arial.ttf"
    mock.overlay.font_size = 50
    mock.overlay.highlight_color = "#FFFF00"
    mock.overlay.text_color = "#FFFFFF"
    mock.overlay.stroke_width = 2
    mock.overlay.max_words_per_line = 3
    mock.overlay.vertical_position = 0.7
    mock.editing.output_resolution = (1080, 1920)
    mock.paths.workspace_dir = "."
    return mock

def test_subtitle_overlay_init(mock_config_manager):
    overlay = SubtitleOverlay(mock_config_manager)
    assert overlay is not None

def test_overlay_process(mocker, mock_config_manager):
    mocker.patch("src.overlay.subtitle.VideoFileClip")
    mocker.patch("src.overlay.subtitle.CompositeVideoClip")
    mocker.patch("src.overlay.subtitle.ImageFont.truetype")
    
    overlay = SubtitleOverlay(mock_config_manager)
    transcript = TranscriptionResult(
        video_id="test", language="en", 
        segments=[Segment(start=0, end=1, text="Hi", words=[Word(word="Hi", start=0, end=1, score=1)])]
    )
    
    overlay.overlay_subtitles("in.mp4", transcript, "out.mp4")
