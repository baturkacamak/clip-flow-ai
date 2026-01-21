from pathlib import Path
from typing import Any, List, Optional, Tuple

import numpy as np
from loguru import logger
from moviepy import CompositeVideoClip, VideoFileClip
from PIL import Image, ImageDraw, ImageFont

from python_core.config_manager import ConfigManager
from python_core.transcription.models import TranscriptionResult, Word
from python_core.utils.text_utils import chunk_words


class SubtitleOverlay:
    def __init__(self, config_manager: ConfigManager):
        self.cfg = config_manager.overlay
        self.paths = config_manager.paths
        
        # Load font
        self.font: Any = None
        try:
            self.font = ImageFont.truetype(self.cfg.font_path, self.cfg.font_size)
        except OSError:
            logger.warning(f"Font not found at {self.cfg.font_path}. Using default.")
            self.font = ImageFont.load_default() # Fallback

    def overlay_subtitles(self, video_path: str, transcript: TranscriptionResult, output_path: str) -> None:
        """
        Adds dynamic karaoke subtitles to the video.
        """
        if not Path(video_path).exists():
            logger.error(f"Video not found: {video_path}")
            return

        logger.info(f"Adding subtitles to {video_path}...")
        
        # Collect all words from transcript segments
        all_words: List[Word] = []
        for seg in transcript.segments:
            all_words.extend(seg.words)
            
        if not all_words:
            logger.warning("No words in transcript. Skipping subtitles.")
            return

        # Chunk words
        caption_groups = chunk_words(all_words, max_words=self.cfg.max_words_per_line)
        
        # Load Video
        video = VideoFileClip(video_path)
        W, H = video.size
        
        # Memoization cache
        last_state: Tuple[int, int] = (-1, -1)
        last_frame: Optional[np.ndarray[Any, Any]] = None
        
        def make_text_frame(t: float) -> np.ndarray[Any, Any]:
            nonlocal last_state, last_frame
            
            # 1. Find active group
            active_group_idx = -1
            active_group = None
            
            # Simple linear search (optimize with bisect later if needed)
            for i, group in enumerate(caption_groups):
                if group.start <= t <= group.end:
                    active_group = group
                    active_group_idx = i
                    break
            
            if not active_group:
                # Return transparent frame
                return np.zeros((H, W, 4), dtype=np.uint8) # RGBA
                # If using CompositeVideoClip, we want RGBA or mask. 
                # Let's return transparent RGBA.
            
            # 2. Find active word
            active_word_idx = -1
            for i, word in enumerate(active_group.words):
                if word.start <= t <= word.end:
                    active_word_idx = i
                    break
            
            # 3. Check cache
            current_state = (active_group_idx, active_word_idx)
            if current_state == last_state and last_frame is not None:
                return last_frame
            
            # 4. Draw Frame
            # Create transparent image
            img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Calculate text size and position
            text = active_group.text
            # We assume text is single line for now (chunking ensures small groups)
            # Center horizontally
            
            # Get text bounding box
            # PIL 10+ uses textbbox
            left, top, right, bottom = draw.textbbox((0, 0), text, font=self.font, stroke_width=self.cfg.stroke_width)
            text_w = right - left
            # text_h = bottom - top
            
            x = (W - text_w) // 2
            y = int(H * self.cfg.vertical_position)
            
            # Draw words individually to handle colors
            # We need to calculate x position for each word.
            # Usually we draw the full sentence with spacing.
            # Getting exact x for each word is tricky with variable width font.
            # Strategy: Draw the full text in white first.
            # Then redraw the active word in yellow on top?
            # Issue: "kerning" might shift if drawn separately.
            # Better Strategy: Measure width of words before active word.
            
            # Let's rebuild the line word by word.
            cursor_x = x
            
            for i, word in enumerate(active_group.words):
                word_text = word.word
                
                # Color
                color = self.cfg.highlight_color if i == active_word_idx else self.cfg.text_color
                
                # Draw
                draw.text((cursor_x, y), word_text, font=self.font, fill=color, 
                          stroke_width=self.cfg.stroke_width, stroke_fill="black")
                
                # Advance cursor
                w_left, w_top, w_right, w_bottom = draw.textbbox(
                    (0, 0), word_text, font=self.font, stroke_width=self.cfg.stroke_width
                )
                w_width = w_right - w_left
                
                # Add space width
                space_bbox = draw.textbbox((0, 0), " ", font=self.font)
                space_width = space_bbox[2] - space_bbox[0]
                
                cursor_x += w_width + space_width

            # Convert to numpy
            result_array = np.array(img)
            
            # Update cache
            last_state = current_state
            last_frame = result_array
            
            return result_array

        # Create Clip
        # We make a clip of same duration as video
        # We assume ImageClip accepts a function via make_frame?
        # No, VideoClip(make_frame=...)
        from moviepy import VideoClip
        
        subtitle_clip = VideoClip(make_frame=make_text_frame, duration=video.duration)
        
        # Composite
        final = CompositeVideoClip([video, subtitle_clip])
        
        # Render
        logger.info(f"Rendering subtitles to {output_path}...")
        final.write_videofile(
            output_path,
            fps=video.fps,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=4,
            logger=None
        )
        logger.success("Subtitle render complete.")
        
        video.close()
        final.close()