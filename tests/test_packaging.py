import pytest

from python_core.intelligence.models import ViralClip
from python_core.packaging.generator import MetadataGenerator
from python_core.packaging.models import VideoPackage
from python_core.packaging.thumbnail import ThumbnailMaker


@pytest.fixture
def mock_config_manager(mocker):
    mock = mocker.Mock()
    mock.packaging.thumbnail_font_path = "arial.ttf"
    mock.packaging.max_title_length = 50
    mock.packaging.hashtags_count = 5
    mock.intelligence.llm_provider = "openai"
    mock.intelligence.openai_api_key = "sk-fake"
    mock.intelligence.anthropic_api_key = None
    mock.intelligence.model_name = "gpt-4"
    return mock


@pytest.fixture
def sample_clip():
    return ViralClip(start_time=0, end_time=10, title="Test Clip", virality_score=90, reasoning="Good", category="Tech")


def test_metadata_generator_mock(mocker, mock_config_manager, sample_clip):
    mocker.patch("python_core.packaging.generator.instructor.from_openai")

    gen = MetadataGenerator(mock_config_manager)
    # We test that it returns a VideoPackage (implementation will fail or return default until implemented)
    pkg = gen.generate_metadata(sample_clip, "vid.mp4", "thumb.jpg")
    assert isinstance(pkg, VideoPackage)


def test_thumbnail_maker_logic(mocker, mock_config_manager, sample_clip):
    # Mock cv2 and PIL
    mock_cv2 = mocker.patch("python_core.packaging.thumbnail.cv2")
    # Mock Image
    mock_image = mocker.patch("python_core.packaging.thumbnail.Image")
    mock_pil_img = mocker.Mock()
    mock_pil_img.size = (1920, 1080)
    mock_image.fromarray.return_value = mock_pil_img

    mocker.patch("python_core.packaging.thumbnail.ImageDraw")
    mocker.patch("python_core.packaging.thumbnail.ImageFont")
    mocker.patch("pathlib.Path.exists", return_value=True)
    # Setup mock cap via cv2 mock
    mock_cap = mocker.Mock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.return_value = 30.0  # fps
    mock_cap.read.return_value = (True, mocker.Mock())  # ret, frame
    mock_cv2.VideoCapture.return_value = mock_cap

    # Mock Laplacian via cv2 mock
    mock_cv2.cvtColor.return_value = mocker.Mock()
    mock_cv2.Laplacian.return_value.var.return_value = 100.0

    maker = ThumbnailMaker(mock_config_manager)
    path = maker.generate_thumbnail("vid.mp4", sample_clip, "out.jpg")
    assert path == "out.jpg"
