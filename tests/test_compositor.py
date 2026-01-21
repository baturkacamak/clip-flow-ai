
import numpy as np
import pytest

from python_core.editing import effects
from python_core.editing.compositor import VideoCompositor
from python_core.editing.models import RenderPlan
from python_core.vision.models import ClipCropData, FrameCrop


@pytest.fixture
def mock_config_manager(mocker):
    mock = mocker.Mock()
    mock.editing.output_resolution = (1080, 1920)
    mock.editing.blur_radius = 21
    mock.editing.music_volume = 0.1
    mock.editing.fade_in_duration = 0.5
    mock.editing.transition_duration = 0.2
    return mock

def test_effects_blur(mocker):
    # Mock scikit-image gaussian
    mocker.patch("src.editing.effects.gaussian", return_value=np.zeros((100, 100, 3)))
    mocker.patch("src.editing.effects.resize", return_value=np.zeros((1920, 1080, 3)))
    
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    res = effects.create_blurred_background(frame, 21, (1080, 1920))
    assert res is not None

def test_compositor_init(mock_config_manager):
    compositor = VideoCompositor(mock_config_manager)
    assert compositor.cfg.blur_radius == 21

def test_render_plan_validation():
    # Test valid plan creation
    plan = RenderPlan(
        source_video_path="vid.mp4",
        source_audio_path="aud.wav",
        clip_crop_data=[],
        b_roll_segments=[],
        output_path="out.mp4"
    )
    assert plan.source_video_path == "vid.mp4"

def test_compositor_render_call(mocker, mock_config_manager):
    # Mock MoviePy
    mocker.patch("src.editing.compositor.VideoFileClip")
    mocker.patch("src.editing.compositor.AudioFileClip")
    mocker.patch("src.editing.compositor.CompositeVideoClip")
    mocker.patch("src.editing.compositor.concatenate_videoclips")
    
    compositor = VideoCompositor(mock_config_manager)
    
    plan = RenderPlan(
        source_video_path="vid.mp4",
        source_audio_path="aud.wav",
        clip_crop_data=[
            ClipCropData(
                clip_id="c1", video_id="v1",
                frames=[FrameCrop(timestamp=0.0, frame_index=0, crop_x=0, crop_y=0, crop_w=100, crop_h=100)]
            )
        ],
        b_roll_segments=[],
        output_path="out.mp4"
    )
    
    # Expect success (no error raised) - heavily mocked
    compositor.render(plan)
