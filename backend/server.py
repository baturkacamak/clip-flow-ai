import asyncio
import logging
import sys
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel

# --- Architecture Fix: Add Root to sys.path ---
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Import the actual pipeline logic from python_core
try:
    from python_core.config_manager import ConfigManager
    from python_core.pipeline import PipelineManager
except ImportError as e:
    print(f"WARNING: Could not import python_core modules. Error: {e}")

    # Mock implementation for UI testing if core is missing
    class PipelineManager:  # type: ignore
        def __init__(self, config, keep_temp=False):
            pass

        def run(self, **kwargs):
            logging.info(f"Mock Pipeline Running: {kwargs}")
            import time

            time.sleep(2)


# --- Log Streaming ---
class LogQueueHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.queue = asyncio.Queue()

    def emit(self, record):
        try:
            msg = self.format(record)
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.call_soon_threadsafe(self.queue.put_nowait, msg)
        except (RuntimeError, asyncio.CancelledError):
            pass


# Bridge loguru to standard logging
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


log_handler = LogQueueHandler()
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", datefmt="%H:%M:%S")
log_handler.setFormatter(formatter)

# Redirect loguru to our LogQueueHandler
logger.add(log_handler, format="{time:HH:mm:ss} | {level: <8} | {message}", level="INFO")

# Also intercept standard logging
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
logging.getLogger("uvicorn").handlers = [InterceptHandler()]
logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]

# --- App Configuration ---
app = FastAPI(title="ClipFlowAI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Data Models ---
class JobConfig(BaseModel):
    mode: str
    url: Optional[str] = None
    audio_path: Optional[str] = None
    script: Optional[str] = None
    llm_provider: str = "openai"
    topic: Optional[str] = None
    background_blur: int = 20
    face_tracking: bool = True
    music_volume: float = 0.1
    subtitle_color: str = "#FFFF00"
    dry_run: bool = False
    platform: str = "youtube"


# --- Logic ---
def run_pipeline_thread(config: dict):
    logger.info(f"--- Starting Job: Mode={config.get('mode')} ---")
    try:
        # Load ConfigManager (usually loads from settings.yaml)
        try:
            cm = ConfigManager()
        except Exception:
            cm = None

        pipeline = PipelineManager(cm, keep_temp=True)
        pipeline.run(
            url=config.get("url"),
            topic=config.get("topic"),
            upload=not config.get("dry_run"),
            mode=config.get("mode"),
            audio_path=config.get("audio_path"),
        )
    except Exception as e:
        logger.error(f"PIPELINE ERROR: {e}")
        import traceback

        logger.error(traceback.format_exc())


@app.post("/start-job")
async def start_job(config: JobConfig):
    if config.mode == "viral" and not config.url:
        raise HTTPException(status_code=400, detail="URL is required for Viral Mode.")
    if config.mode == "story" and not config.audio_path:
        raise HTTPException(status_code=400, detail="Audio file path is required for Story Mode.")

    thread = threading.Thread(target=run_pipeline_thread, args=(config.dict(),), daemon=True)
    thread.start()
    return {"status": "started", "config": config.dict()}


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            log_msg = await log_handler.queue.get()
            await websocket.send_text(log_msg)
    except WebSocketDisconnect:
        pass


@app.get("/library")
async def get_library():
    library_path = Path("./library")
    if not library_path.exists():
        return {"files": []}
    files = [f.name for f in library_path.iterdir() if f.is_file()]
    return {"files": files}


if __name__ == "__main__":
    import uvicorn

    # 0.0.0.0 allows access from other containers/machines if needed
    uvicorn.run(app, host="127.0.0.1", port=8000)
