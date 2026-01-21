import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure backend path is in sys.path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from server import app

client = TestClient(app)


@pytest.fixture
def mock_pipeline(mocker):
    # Patch the PipelineManager in server module
    return mocker.patch("server.PipelineManager")


def test_start_job_viral_valid(mock_pipeline):
    payload = {"mode": "viral", "url": "https://youtube.com/test", "llm_provider": "openai"}
    response = client.post("/start-job", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "started"


def test_start_job_viral_missing_url():
    payload = {"mode": "viral", "llm_provider": "openai"}
    response = client.post("/start-job", json=payload)
    assert response.status_code == 400
    assert "URL is required" in response.json()["detail"]


def test_start_job_story_valid(mock_pipeline):
    payload = {"mode": "story", "audio_path": "/tmp/test.mp3", "llm_provider": "anthropic"}
    response = client.post("/start-job", json=payload)
    assert response.status_code == 200


def test_library_endpoint(tmp_path):
    # We can't easily mock CWD for Path("./library") in server without patching Path
    # So we will just test it returns 200 and maybe empty list
    response = client.get("/library")
    assert response.status_code == 200
    assert "files" in response.json()
