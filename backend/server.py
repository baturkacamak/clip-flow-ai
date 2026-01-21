import sys
import os
import asyncio
import logging
import threading
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Architecture Fix: Add Root to sys.path ---
# Current file: /backend/server.py
# Root dir: /
# Python Core: /python_core
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Import the actual pipeline logic from python_core
try:
    from python_core.pipeline import PipelineManager
    from python_core.config_manager import ConfigManager
except ImportError as e:
    print(f"WARNING: Could not import python_core modules. Error: {e}")
    # Mock implementation for UI testing if core is missing
    class PipelineManager:
        def __init__(self, config, keep_temp=False): pass
        def run(self, **kwargs): 
            logging.info(f"Mock Pipeline Running: {kwargs}")
            import time
            time.sleep(2)

# --- App Configuration ---
app = FastAPI(title="AutoReelAI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

log_handler = LogQueueHandler()
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S')
log_handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(log_handler)

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
    logging.info(f"--- Starting Job: Mode={config.get('mode')} ---")
    try:
        # Load ConfigManager (usually loads from settings.yaml)
        # We might want to override settings here based on UI input if ConfigManager supports it
        try:
            cm = ConfigManager()
        except:
            cm = None 

        pipeline = PipelineManager(cm, keep_temp=True)
        pipeline.run(
            url=config.get('url'),
            topic=config.get('topic'),
            upload=not config.get('dry_run'),
            mode=config.get('mode'),
            audio_path=config.get('audio_path')
        )
    except Exception as e:
        logging.error(f"PIPELINE ERROR: {e}")
        import traceback
        logging.error(traceback.format_exc())

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