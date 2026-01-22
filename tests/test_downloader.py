from pathlib import Path

import pytest
from yt_dlp.utils import DownloadError

from python_core.ingestion.downloader import VideoDownloader


@pytest.fixture
def mock_config_manager(tmp_path):
    """Creates a ConfigManager with temporary paths."""
    # We mock the ConfigManager object directly or point it to a temp config
    # Here we'll patch the config attribute of a real instance or just create a struct

    class MockPaths:
        workspace_dir = str(tmp_path / "workspace")
        history_file = str(tmp_path / "history.json")
        cookies_file = None

    class MockDownloaderConfig:
        min_resolution = "720"
        video_format = "mp4"
        audio_format = "wav"
        separate_audio = True
        check_duplicates = True
        retries = 1

    class MockConfigManager:
        paths = MockPaths()
        downloader = MockDownloaderConfig()

    return MockConfigManager()


def test_downloader_initialization(mock_config_manager, tmp_path):
    """Test that workspace and history file are created."""
    VideoDownloader(mock_config_manager)
    assert Path(mock_config_manager.paths.workspace_dir).exists()
    assert Path(mock_config_manager.paths.history_file).exists()


def test_duplicate_check(mock_config_manager):
    """Test duplicate detection logic."""
    downloader = VideoDownloader(mock_config_manager)
    video_id = "test_123"

    # First check should be False
    assert downloader._is_duplicate(video_id) is False

    # Add to history
    downloader._add_to_history(video_id)

    # Second check should be True
    assert downloader._is_duplicate(video_id) is True


def test_download_mocked(mocker, mock_config_manager):
    """Test the download flow with mocked yt-dlp."""
    mock_ydl = mocker.patch("python_core.ingestion.downloader.yt_dlp.YoutubeDL")

    # Setup mock context manager
    mock_instance = mock_ydl.return_value.__enter__.return_value

    # Mock extract_info return values
    mock_instance.extract_info.side_effect = [
        {
            "id": "vid123",
            "title": "Test Video",
            "duration": 100,
            "height": 1080,
        },  # Dry run
        {"id": "vid123", "title": "Test Video", "ext": "mp4"},  # Actual download
    ]

    # Mock prepare_filename
    mock_instance.prepare_filename.return_value = str(
        Path(mock_config_manager.paths.workspace_dir) / "Test Video [vid123].mp4"
    )

    downloader = VideoDownloader(mock_config_manager)
    result = downloader.download("http://test.com/video")

    assert result is not None
    assert result["id"] == "vid123"
    assert "video_path" in result
    assert "metadata_path" in result

    # Verify yt-dlp was called
    assert mock_instance.extract_info.call_count == 2


def test_download_quality_skip(mocker, mock_config_manager):
    """Test that low resolution videos are skipped."""
    mock_ydl = mocker.patch("python_core.ingestion.downloader.yt_dlp.YoutubeDL")
    mock_instance = mock_ydl.return_value.__enter__.return_value

    # Return low resolution info
    mock_instance.extract_info.return_value = {
        "id": "lowres",
        "title": "Bad Video",
        "height": 480,
    }

    downloader = VideoDownloader(mock_config_manager)
    result = downloader.download("http://test.com/lowres")

    assert result is None


def test_download_retry_on_429(mocker, mock_config_manager):
    """Test that downloader retries without subtitles on HTTP 429."""
    mock_ydl = mocker.patch("python_core.ingestion.downloader.yt_dlp.YoutubeDL")
    mock_instance = mock_ydl.return_value.__enter__.return_value

    # Mock prepare_filename
    mock_instance.prepare_filename.return_value = str(
        Path(mock_config_manager.paths.workspace_dir) / "Test Video [vid429].mp4"
    )

    # Side effect:
    # 1. extract_info (dry run) -> Success
    # 2. extract_info (download) -> Error 429
    # 3. extract_info (retry) -> Success
    mock_instance.extract_info.side_effect = [
        {"id": "vid429", "title": "Retry Video", "height": 1080},  # Dry run
        DownloadError("HTTP Error 429: Too Many Requests"),  # First attempt fails
        {"id": "vid429", "title": "Retry Video", "ext": "mp4"},  # Retry succeeds
        {"id": "vid429", "title": "Retry Video", "ext": "mp4"},  # Post-process call
    ]

    downloader = VideoDownloader(mock_config_manager)
    result = downloader.download("http://test.com/retry")

    assert result is not None
    assert result["id"] == "vid429"

    # Check calls
    # Call 1: Dry run
    # Call 2: Failed download
    # Call 3: Retry download
    # Call 4: Post-processing (prepare_filename helper block)
    assert mock_instance.extract_info.call_count >= 3

    # Verify that the retry call (3rd initialization of YoutubeDL) disabled subtitles
    # We inspect the calls to YoutubeDL constructor
    calls = mock_ydl.call_args_list

    # Call 0: Dry run options
    # Call 1: Initial download options (writesubtitles=True)
    initial_opts = calls[1][0][0]
    assert initial_opts.get("writesubtitles") is True

    # Call 2: Retry options (writesubtitles=False)
    retry_opts = calls[2][0][0]
    assert retry_opts.get("writesubtitles") is False


def test_download_duplicate_logic(mocker, mock_config_manager):
    """Test duplicate handling with and without existing files."""
    mock_ydl = mocker.patch("python_core.ingestion.downloader.yt_dlp.YoutubeDL")
    mock_instance = mock_ydl.return_value.__enter__.return_value

    downloader = VideoDownloader(mock_config_manager)
    video_id = "dup123"
    title = "Existing Video"

    # 1. Simulate duplicate in history
    downloader._add_to_history(video_id)

    # Setup mock for dry run to return info
    mock_instance.extract_info.return_value = {"id": video_id, "title": title, "height": 1080}

    # Case A: File Missing -> Should Download
    # We ensure no files exist in workspace
    # (tmp_path is clean by default for this test run)

    # We need to mock prepare_filename to avoid crash in download path
    mock_instance.prepare_filename.return_value = str(
        Path(mock_config_manager.paths.workspace_dir) / f"{title} [{video_id}].mp4"
    )

    downloader.download("http://test.com/dup1")

    # Should have called download=True
    # Calls: 1. dry run (download=False) 2. download (download=True)
    assert mock_instance.extract_info.call_count == 2
    assert mock_instance.extract_info.call_args_list[1][1]["download"] is True

    # Case B: File Exists -> Should Skip
    mock_instance.extract_info.reset_mock()

    # Create the file
    vid_file = Path(mock_config_manager.paths.workspace_dir) / f"{title} [{video_id}].mp4"
    vid_file.touch()

    result = downloader.download("http://test.com/dup1")

    # Should have returned result pointing to existing file
    assert result is not None
    assert result["video_path"] == str(vid_file)

    # Should NOT have called download=True, only dry run (download=False)
    assert mock_instance.extract_info.call_count == 1
    assert mock_instance.extract_info.call_args_list[0][1]["download"] is False
