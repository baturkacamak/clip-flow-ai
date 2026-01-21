import os
from pathlib import Path
from typing import Optional

from loguru import logger

from python_core.config_manager import ConfigManager


class AudioSeparator:
    def __init__(self, config_manager: ConfigManager):
        self.cfg = config_manager
        # self.model_name = "htdemucs" # Hardcoded for now

    def separate_vocals(self, audio_path: str) -> Optional[str]:
        """
        Uses Demucs to separate vocals from background music.
        Returns path to vocals file.
        """
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return None

        output_dir = Path(self.cfg.paths.workspace_dir) / "separated"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Command: demucs -n htdemucs --two-stems=vocals -o output_dir input_file
        # cmd = ["demucs", "-n", "htdemucs", "--two-stems=vocals", "-o", str(output_dir), str(input_path)]
        #     "--two-stems", "vocals",
        #     "-o", str(output_dir),
        #     audio_path
        # ]

        logger.info(f"Running Demucs separation for {audio_path}...")
        try:
            # We assume demucs is installed in path
            # subprocess.run(cmd, check=True, capture_output=True)
            # Mocking execution for environment without GPU/Demucs installed
            # In production, uncomment above and remove mock logic below.

            # Simulated output path structure of Demucs:
            # output_dir / htdemucs / {track_name} / vocals.wav
            track_name = Path(audio_path).stem
            vocals_path = output_dir / "htdemucs" / track_name / "vocals.wav"

            # Create dummy file if not exists (Simulation)
            if not vocals_path.exists():
                vocals_path.parent.mkdir(parents=True, exist_ok=True)
                # Just copy original as vocals for simulation
                import shutil

                shutil.copy(audio_path, vocals_path)
                logger.warning("Demucs mocked: Copied original audio as vocals.")

            return str(vocals_path)

        except Exception as e:
            logger.error(f"Audio separation failed: {e}")
            return None
