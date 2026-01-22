# ClipFlowAI

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Version](https://img.shields.io/badge/version-1.0.0-orange)

ClipFlowAI is a highly advanced, fully automated video production pipeline designed to create viral-ready content for platforms like TikTok, YouTube Shorts, and standard YouTube.

## Features
- **Ingestion:** High-res video/audio downloading via `yt-dlp`.
- **Audio Intelligence:** Transcription with `faster-whisper` (GPU optimized).
- **Semantic Search:** B-Roll matching using `CLIP` and `ChromaDB`.
- **Creative Intelligence:** LLM-based clip selection (`OpenAI` / `Anthropic`).
- **Visual Intelligence:** Face tracking and dynamic 9:16 cropping with `MediaPipe`.
- **Post-Production:** Automated editing, blurring, and layering with `MoviePy`.
- **Overlay:** Karaoke-style dynamic subtitles.
- **Packaging:** Viral title/thumbnail generation.
- **Distribution:** Auto-uploading to YouTube and TikTok.

## Installation

### Local
```bash
# Install dependencies
pip install -r requirements.txt

# Run CLI
python cli.py process "https://www.youtube.com/watch?v=..." --upload
```

### Docker (Recommended)
To run with GPU acceleration (NVIDIA):

1. **Build:**
   ```bash
   docker build -t clip-flow-ai .
   ```

2. **Run:**
   ```bash
   docker run --gpus all \
     -v $(pwd)/outputs:/app/outputs \
     -v $(pwd)/assets:/app/assets \
     -v $(pwd)/config:/app/config \
     --env-file .env \
     clipflowai process "https://www.youtube.com/watch?v=..."
   ```

## Configuration
Edit `config/settings.yaml` to tune parameters.
Set API keys in `.env` or environment variables:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `TIKTOK_COOKIES_PATH`
