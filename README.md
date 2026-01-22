# ClipFlowAI

[![CI](https://github.com/baturkacamak/clip-flow-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/baturkacamak/clip-flow-ai/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue)](https://github.com/baturkacamak/clip-flow-ai/blob/main/LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-orange)](https://github.com/baturkacamak/clip-flow-ai)

ClipFlowAI is a powerful, fully automated video production pipeline designed to transform long-form content into engaging short-form videos for platforms like TikTok and YouTube Shorts, or to create narrative-driven videos from audio.

## Core Features

- **Dual Processing Modes:**
    - **Viral Mode:** Automatically identifies and extracts viral moments from a video URL (e.g., YouTube), creating multiple short clips from a single source.
    - **Story Mode:** Generates a compelling visual narrative by combining a primary audio track (e.g., a voiceover) with relevant B-roll footage from your library.
- **Intelligent Content Curation:** Uses Large Language Models (OpenAI, Anthropic) to find the most engaging segments for `viral` mode.
- **Semantic B-Roll Matching:** Employs CLIP and a vector index to find the most relevant B-roll clips from your library to match the source content.
- **AI-Powered Visuals:**
    - **Smart Cropping:** Automatically tracks faces and objects to create a dynamic 9:16 vertical crop.
    - **Dynamic Subtitles:** Generates karaoke-style, word-by-word subtitles with highlighting.
- **Automated Production:** Handles everything from downloading and transcription to editing, overlays, and packaging (metadata, thumbnails).
- **Multi-Platform Distribution:** Directly uploads the final videos to YouTube and TikTok.
- **Desktop GUI:** An Electron-based interface for managing configurations and monitoring pipeline logs.
- **Async Workflow:** Supports dispatching tasks to a Celery worker for background processing.

## Getting Started

### Prerequisites

- **Python 3.10+** (managed with [Poetry](https://python-poetry.org/))
- **Node.js 18+** (for the Desktop GUI)
- **FFmpeg** installed and available in your system's PATH.
- (Optional but Recommended) An NVIDIA GPU for significantly faster processing.
- Access keys for services you intend to use (OpenAI, Anthropic, etc.).

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/baturkacamak/clip-flow-ai.git
    cd clip-flow-ai
    ```

2.  **Install Python dependencies:**
    ```bash
    poetry install
    ```

3.  **Install GUI dependencies:**
    ```bash
    npm install
    ```

4.  **Set up configuration:**
    - Review `config/settings.yaml` for pipeline parameters.
    - Create a `.env` file in the root directory and add your API keys:
      ```env
      OPENAI_API_KEY="sk-..."
      ANTHROPIC_API_KEY="sk-..."
      ```
    - Place your B-roll footage in `assets/b_roll`.
    - (Optional) Configure YouTube/TikTok credentials in `config/` and `assets/auth/`.

## Running the Application

### 1. Full Desktop Application (Recommended)
You can start both the Python backend API and the Electron GUI with a single command:

**Using NPM:**
```bash
npm run dev-all
```

**Using [Just](https://github.com/casey/just) (Task Runner):**
```bash
just dev
```

### 2. Command-Line Interface (CLI)
You can run the pipeline directly from the terminal without the GUI:

```bash
# Viral Mode
poetry run python cli.py process "https://www.youtube.com/watch?v=your_video_id"

# Story Mode
poetry run python cli.py process --mode story --audio "path/to/voiceover.wav"
```

### 3. Manual Component Startup
If you prefer to run components in separate terminals:

- **Backend API:** `just server` or `poetry run python backend/server.py`
- **Frontend GUI:** `just gui` or `npm run dev`

## Usage & CLI Options

| Command             | Argument            | Description                                                                                             |
| ------------------- | ------------------- | ------------------------------------------------------------------------------------------------------- |
| **`process`**       | `url`               | (Required for `viral` mode) The source YouTube URL.                                                     |
|                     | `--mode`            | The processing mode. Choices: `viral`, `story`. Default: `viral`.                                       |
|                     | `--audio`           | (Required for `story` mode) The path to the input audio file.                                           |
|                     | `--topic`           | A specific topic to guide the LLM's content curation in `viral` mode.                                   |
|                     | `--upload`          | If set, uploads the final videos to the configured platforms.                                           |
|                     | `--dry-run`         | Simulates the full process, including uploads, without actually uploading.                              |
|                     | `--async-mode`      | Dispatches the task to a Celery worker for background processing.                                       |

## Development Standards

This project follows the standards defined in `GEMINI.md`.

- **Linting & Formatting:** `just lint` or `npm run lint`
- **Tests:** `just test` or `npm run test` (for UI)
- **Pre-commit Hooks:** Automatically installed on `npm install`. Ensures all checks pass before commits.

## Docker

To run with GPU acceleration:
```bash
docker build -t clip-flow-ai .
docker run --gpus all -v $(pwd)/outputs:/app/outputs --env-file .env clip-flow-ai process "URL"
```
