import pytest
import yaml

from src.config_manager import AppConfig, ConfigManager


@pytest.fixture
def mock_config_file(tmp_path):
    """Creates a temporary config file."""
    config_data = {
        "paths": {
            "base_dir": str(tmp_path),
            "workspace_dir": str(tmp_path / "workspace"),
            "output_dir": str(tmp_path / "outputs"),
            "log_dir": str(tmp_path / "logs"),
            "cookies_file": None,
            "history_file": str(tmp_path / "history.json"),
        },
        "downloader": {
            "resolution": "1080",
            "min_resolution": "720",
            "check_duplicates": False
        },
        "transcription": {
            "model_size": "large-v2"
        },
        "intelligence": {
            "llm_provider": "openai"
        },
        "vision": {},
        "retrieval": {},
        "editing": {},
        "overlay": {},
        "pipeline": {
            "target_aspect_ratio": "9:16"
        }
    }

    config_path = tmp_path / "test_settings.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)

    return str(config_path)


def test_config_load_valid(mock_config_file):
    """Test loading a valid configuration file."""
    manager = ConfigManager(config_path=mock_config_file)
    assert isinstance(manager.config, AppConfig)
    assert manager.downloader.resolution == "1080"
    assert manager.pipeline.target_aspect_ratio == "9:16"


def test_config_file_not_found():
    """Test that missing config file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        ConfigManager(config_path="non_existent.yaml")


def test_default_values(tmp_path):
    """Test that default values are used when optional fields are missing (if applicable)."""
    # Create minimal config
    config_data = {
        "paths": {}, 
        "downloader": {}, 
        "transcription": {}, 
        "intelligence": {}, 
        "vision": {},
        "retrieval": {},
        "editing": {},
        "overlay": {},
        "pipeline": {}
    }
    config_path = tmp_path / "minimal.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)

    manager = ConfigManager(config_path=str(config_path))
    assert manager.downloader.resolution == "1080"  # Default
    assert manager.paths.base_dir == "."  # Default
