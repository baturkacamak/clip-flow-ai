import os

from celery import Celery

from python_core.config_manager import ConfigManager
from python_core.pipeline import PipelineManager

# Config
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery("autoreel", broker=REDIS_URL, backend=REDIS_URL)


@app.task(bind=True)
def process_video_task(self, url: str, topic: str = None, upload: bool = False):
    """
    Background task to process video.
    """
    try:
        # Re-init config per task to get fresh env/settings
        config = ConfigManager()
        pipeline = PipelineManager(config)
        pipeline.run(url, topic=topic, upload=upload)
        return {"status": "success", "url": url}
    except Exception as e:
        # Sentry capture here would be ideal
        return {"status": "failed", "error": str(e)}
