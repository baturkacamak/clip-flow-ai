from unittest.mock import MagicMock

import numpy as np
import pytest

from python_core.intelligence.models import ViralClip
from python_core.vision.cropper import SmartCropper
from python_core.vision.stabilizer import Stabilizer


def test_stabilizer_ema():
    # Alpha 0.5 for simple math
    stabilizer = Stabilizer(alpha=0.5)

    # First update
    x, y = stabilizer.update(100, 100)
    assert x == 100
    assert y == 100

    # Second update: target 200. Smooth = 0.5*200 + 0.5*100 = 150
    x, y = stabilizer.update(200, 200)
    assert x == 150
    assert y == 150

    stabilizer.reset()
    assert stabilizer.prev_x is None


@pytest.fixture
def mock_config_manager(mocker):
    mock = mocker.Mock()
    mock.vision.face_detection_confidence = 0.5
    mock.vision.stabilization_factor = 0.1
    mock.vision.vertical_crop_ratio = 9 / 16
    mock.vision.debug_preview = False
    mock.paths.workspace_dir = "."
    return mock


def test_cropper_process_clips_no_video(mocker, mock_config_manager):
    mocker.patch("python_core.vision.cropper.mp")
    cropper = SmartCropper(mock_config_manager)
    results = cropper.process_clips("non_existent.mp4", [], "vid1")
    assert results == []


def test_cropper_single_clip(mocker, mock_config_manager):
    # Mock cv2
    mock_cv2 = mocker.patch("python_core.vision.cropper.cv2")
    mock_cap = MagicMock()
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cap.isOpened.return_value = True
    mock_cap.get.side_effect = lambda prop: {
        mock_cv2.CAP_PROP_FPS: 30.0,
        mock_cv2.CAP_PROP_FRAME_COUNT: 100,
        mock_cv2.CAP_PROP_FRAME_WIDTH: 1920,
        mock_cv2.CAP_PROP_FRAME_HEIGHT: 1080,
    }.get(prop, 0)

    # Mock frame reading (return one frame then None)
    mock_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    mock_cap.read.side_effect = [(True, mock_frame), (False, None)]

    # Mock MediaPipe
    mock_mp = mocker.patch("python_core.vision.cropper.mp")
    mock_detector = mock_mp.solutions.face_detection.FaceDetection.return_value

    # Mock detection result
    mock_detection = MagicMock()
    mock_detection.location_data.relative_bounding_box.xmin = 0.4
    mock_detection.location_data.relative_bounding_box.ymin = 0.2
    mock_detection.location_data.relative_bounding_box.width = 0.2
    mock_detection.location_data.relative_bounding_box.height = 0.2

    mock_results = MagicMock()
    mock_results.detections = [mock_detection]
    mock_detector.process.return_value = mock_results

    # Mock Path exists to pass check
    mocker.patch("pathlib.Path.exists", return_value=True)
    # Mock file writing
    mocker.patch("builtins.open", mocker.mock_open())

    cropper = SmartCropper(mock_config_manager)
    clip = ViralClip(start_time=0.0, end_time=1.0, title="Test", virality_score=10, reasoning="", category="")

    results = cropper.process_clips("dummy.mp4", [clip], "vid1")

    assert len(results) == 1
    assert len(results[0].frames) > 0
    # Check crop dimensions (9:16 of 1080h is 607w)
    assert results[0].frames[0].crop_w == int(1080 * (9 / 16))
    assert results[0].frames[0].crop_h == 1080
