import sys
from pathlib import Path

import pytest

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))


def test_server_module_import():
    """
    Test that backend.server can be imported successfully.
    This validates that all dependencies and type definitions (like AppConfig) are correctly defined.
    """
    import importlib

    try:
        importlib.import_module("backend.server")
    except ImportError as e:
        pytest.fail(f"Failed to import backend.server: {e}")
    except NameError as e:
        pytest.fail(f"NameError in backend.server: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error importing backend.server: {e}")
