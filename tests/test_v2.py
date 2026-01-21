import pytest
from unittest.mock import MagicMock
from src.audio.separator import AudioSeparator
from src.editing.ffmpeg_compositor import FFmpegCompositor
from src.editing.models import RenderPlan
from src.vision.models import ClipCropData, FrameCrop

@pytest.fixture
def mock_config_manager(mocker):
    mock = mocker.Mock()
    mock.paths.workspace_dir = "workspace"
    mock.editing.output_resolution = (1080, 1920)
    mock.editing.blur_radius = 21
    return mock

def test_audio_separation_mock(mocker, mock_config_manager):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("subprocess.run")
    mocker.patch("shutil.copy")
    mocker.patch("pathlib.Path.mkdir")
    
    separator = AudioSeparator(mock_config_manager)
    res = separator.separate_vocals("test.wav")
    assert "vocals.wav" in res

def test_ffmpeg_compositor_render(mocker, mock_config_manager):
    mocker.patch("cv2.VideoCapture")
    mocker.patch("cv2.VideoWriter")
    mock_run = mocker.patch("subprocess.run")
    mocker.patch("os.remove")
    mocker.patch("builtins.open", mocker.mock_open())
    
    compositor = FFmpegCompositor(mock_config_manager)
    
    plan = RenderPlan(
        source_video_path="v.mp4",
        source_audio_path="a.wav",
        clip_crop_data=[
            ClipCropData(
                clip_id="c1", video_id="v1",
                frames=[FrameCrop(timestamp=0, frame_index=0, crop_x=0, crop_y=0, crop_w=100, crop_h=100)]
            )
        ],
        b_roll_segments=[],
        output_path="out.mp4"
    )
    
    # Simulate crop generation success
    mocker.patch.object(compositor, "_generate_cropped_video", return_value=True)
    
    compositor.render(plan)
    # Check if subprocess called (ffmpeg)
    assert mock_run.called
