# ClipFlowAI

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/baturkacamak/clip-flow-ai)
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
- **Async Workflow:** Supports dispatching tasks to a Celery worker for background processing.

## Getting Started

### Prerequisites

- Python 3.9+
- [FFmpeg](https://ffmpeg.org/download.html) installed and available in your system's PATH.
- (Optional but Recommended) An NVIDIA GPU for significantly faster processing.
- Access keys for services you intend to use (OpenAI, Google API for YouTube, etc.).

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/baturkacamak/clip-flow-ai.git
    cd clip-flow-ai
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up configuration:**
    - Rename `config/settings.yaml.example` to `config/settings.yaml` (if an example is provided) and review the settings.
    - Create a `.env` file in the root directory and add your API keys:
      ```env
      OPENAI_API_KEY="sk-..."
      ANTHROPIC_API_KEY="sk-..."
      # Add other keys as needed
      ```
    - Place your B-roll footage in the `assets/b_roll` directory.
    - For YouTube uploads, place your `client_secrets.json` in the `config/` directory.
    - For TikTok uploads, place your `tiktok_cookies.json` in the `assets/auth/` directory.

## Desktop GUI

ClipFlowAI also includes a desktop GUI for a more interactive experience.

### GUI Installation
To use the GUI, you need to install the Node.js dependencies:

```bash
# From the project root
npm install
```

### Running the GUI
To run the GUI in development mode:

```bash
npm run dev
```

This command will concurrently start the Vite development server for the React frontend, compile the Electron-specific TypeScript code, and launch the Electron application.

## Usage

ClipFlowAI is controlled via `cli.py`. The main command is `process`, which has two primary modes: `viral` and `story`.

### Viral Mode

This mode takes a video URL and creates multiple short, viral-style clips from it.

**Basic Example:**
```bash
python cli.py process "https://www.youtube.com/watch?v=your_video_id"
```

**Example with Uploading:**
```bash
python cli.py process "https://www.youtube.com/watch?v=your_video_id" --upload
```

### Story Mode

This mode takes an audio file and generates a single video by matching it with B-roll from your library.

**Basic Example:**
```bash
python cli.py process --mode story --audio "path/to/your/voiceover.wav"
```

### Command-Line Options

| Command             | Argument            | Description                                                                                             |
| ------------------- | ------------------- | ------------------------------------------------------------------------------------------------------- |
| **`process`**       | `url`               | (Required for `viral` mode) The source YouTube URL.                                                     |
|                     | `--mode`            | The processing mode. Choices: `viral`, `story`. Default: `viral`.                                       |
|                     | `--audio`           | (Required for `story` mode) The path to the input audio file.                                           |
|                     | `--topic`           | A specific topic to guide the LLM's content curation in `viral` mode.                                   |
|                     | `--upload`          | If set, uploads the final videos to the configured platforms.                                           |
|                     | `--dry-run`         | Simulates the full process, including uploads, without actually uploading.                              |
|                     | `--keep-temp`       | Prevents the cleanup of temporary files (like downloaded videos) in the workspace after a run.          |
|                     | `--platform`        | Specify a platform to upload to (e.g., `--platform youtube`). Can be used multiple times.                |
|                     | `--async-mode`      | Dispatches the task to a Celery worker for background processing (currently only supports `viral` mode). |


## Configuration

All pipeline behavior can be fine-tuned in `config/settings.yaml`.

| Section         | Key                             | Description                                                                   |
| --------------- | ------------------------------- | ----------------------------------------------------------------------------- |
| **`paths`**     | `workspace_dir`                 | Directory for temporary files.                                                |
|                 | `output_dir`                    | Directory for final video outputs.                                            |
|                 | `b_roll_library_path`           | Path to your B-roll video library.                                            |
| **`downloader`**| `resolution`                    | Preferred download resolution (e.g., "1080").                                 |
| **`transcription`**| `model_size`                 | `faster-whisper` model size (e.g., "large-v2", "base").                     |
|                 | `device`                        | "auto", "cuda", or "cpu".                                                     |
| **`intelligence`**|`llm_provider`                 | "openai" or "anthropic".                                                      |
|                 | `model_name`                    | The specific LLM to use (e.g., "gpt-4-0125-preview").                       |
|                 | `virality_threshold`            | Minimum score (0-100) for a clip to be considered viral.                        |
| **`retrieval`** | `similarity_threshold`          | Threshold for matching B-roll (lower is stricter).                            |
| **`editing`**   | `output_resolution`             | Final video resolution (e.g., [1080, 1920]).                                  |
| **`overlay`**   | `font_path`                     | Path to the font file for subtitles.                                          |
|                 | `highlight_color`               | Color for the currently spoken word.                                          |

...and many more. See `config/settings.yaml` for all available options.

## Docker (Recommended)

To run the application in a containerized environment with GPU acceleration (NVIDIA):

1.  **Build the image:**
    ```bash
    docker build -t clip-flow-ai .
    ```

2.  **Run the container:**
    This example runs `viral` mode on a YouTube video.
    ```bash
    docker run --gpus all \
      -v $(pwd)/outputs:/app/outputs \
      -v $(pwd)/assets:/app/assets \
      -v $(pwd)/config:/app/config \
      --env-file .env \
      clip-flow-ai process "https://www.youtube.com/watch?v=your_video_id" --upload
    ```
