from pathlib import Path
from typing import Any

import cv2
from loguru import logger
from PIL import Image, ImageDraw, ImageFont

from python_core.config_manager import ConfigManager
from python_core.intelligence.models import ViralClip


class ThumbnailMaker:
    def __init__(self, config_manager: ConfigManager):
        self.cfg = config_manager.packaging
        self.font: Any = None
        try:
            # Using a larger font size for thumbnails usually
            self.font = ImageFont.truetype(self.cfg.thumbnail_font_path, 100)
        except OSError:
            logger.warning("Thumbnail font not found. Using default.")
            self.font = ImageFont.load_default()

    def generate_thumbnail(self, video_path: str, clip: ViralClip, output_path: str) -> str:
        """Generates a high-CTR thumbnail."""
        if not Path(video_path).exists():
            logger.error(f"Video not found: {video_path}")
            return ""

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return ""

        # Smart Frame Selection (First 3 seconds)
        fps = cap.get(cv2.CAP_PROP_FPS)
        num_frames = int(fps * 3)
        
        best_frame = None
        max_variance = -1.0
        
        for _ in range(num_frames):
            ret, frame = cap.read()
            if not ret:
                break
            
            # Laplacian Variance
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            variance = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            if variance > max_variance:
                max_variance = variance
                best_frame = frame
        
        cap.release()
        
        if best_frame is None:
            logger.warning("Could not extract frame for thumbnail.")
            return ""

        # Convert to PIL
        img = cv2.cvtColor(best_frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img)
        draw = ImageDraw.Draw(pil_img)
        
        # Draw Text
        text = clip.title.upper()
        # Word wrap? Simple approach: split if too long?
        # Let's just draw centered.
        
        W, H = pil_img.size
        
        # Calculate size
        bbox = draw.textbbox((0, 0), text, font=self.font, stroke_width=6)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        x = (W - text_w) // 2
        y = (H - text_h) // 3 # Upper third
        
        # Draw with stroke
        draw.text((x, y), text, font=self.font, fill="white", stroke_width=6, stroke_fill="black")
        
        # Save
        pil_img.save(output_path, quality=95)
        logger.success(f"Thumbnail saved to {output_path}")
        
        return output_path