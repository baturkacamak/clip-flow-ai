import pytest

from python_core.distribution.tiktok_browser import TikTokUploader
from python_core.distribution.youtube import YouTubeUploader
from python_core.packaging.models import VideoPackage


@pytest.fixture
def mock_config_manager(mocker):
    mock = mocker.Mock()
    mock.distribution.youtube_client_secrets_path = "secrets.json"
    mock.distribution.tiktok_cookies_path = "cookies.json"
    mock.distribution.schedule_offset_hours = 2
    mock.paths.workspace_dir = "."
    return mock


@pytest.fixture
def sample_package():
    return VideoPackage(
        video_path="vid.mp4",
        thumbnail_path="thumb.jpg",
        title="Title",
        description="Desc",
        tags=["tag"],
        captions="Cap",
        platforms=["youtube", "tiktok"],
    )


def test_youtube_upload_flow(mocker, mock_config_manager, sample_package):
    # Mock googleapiclient
    mocker.patch("python_core.distribution.youtube.build")
    mocker.patch("python_core.distribution.youtube.InstalledAppFlow")
    mocker.patch("python_core.distribution.youtube.MediaFileUpload")
    mocker.patch("os.path.exists", return_value=True)  # for secrets check

    uploader = YouTubeUploader(mock_config_manager)
    # Assume auth passes or is mocked out
    uploader.service = mocker.Mock()
    mocker.patch.object(uploader, "authenticate")  # Disable auth call if service is somehow None

    # But wait, I set uploader.service = Mock(). So logic `if not self.service` is false.
    # It proceeds to `media = MediaFileUpload(...)`.
    # I mocked MediaFileUpload.
    # It calls `self.service.videos().insert(...)`.
    # request.next_chunk() loop.
    # request is return value of insert().
    # I need to configure the request mock.

    mock_request = mocker.Mock()
    mock_request.next_chunk.return_value = (None, {"id": "123"})  # Finish immediately
    uploader.service.videos.return_value.insert.return_value = mock_request

    res = uploader.upload(sample_package)
    # Should be False because implementation is empty/returns False
    assert res is True

    def test_tiktok_upload_flow(mocker, mock_config_manager, sample_package):
        # Mock playwright
        mocker.patch("python_core.distribution.tiktok_browser.sync_playwright")
        mocker.patch("os.path.exists", return_value=True)

        TikTokUploader(mock_config_manager)

    res = uploader.upload(sample_package)
    assert res is True
