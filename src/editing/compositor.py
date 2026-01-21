from pathlib import Path
from typing import Any, List

import numpy as np
from loguru import logger
from moviepy import AudioFileClip, CompositeVideoClip, VideoFileClip, concatenate_videoclips, vfx

from src.config_manager import ConfigManager
from src.editing.effects import create_blurred_background
from src.editing.models import RenderPlan


class VideoCompositor:
    def __init__(self, config_manager: ConfigManager):
        self.cfg = config_manager.editing
        self.paths = config_manager.paths

    def _get_crop_at_time(self, t: float, crop_frames: List[Any], fps: float) -> Any:
        """Finds the nearest crop data for time t."""
        # Simple index calculation
        idx = int(t * fps)
        # Clamp
        idx = max(0, min(idx, len(crop_frames) - 1))
        # Verify timestamp match? 
        # frames[idx] should match t closely if fps matches.
        return crop_frames[idx]

    def render(self, plan: RenderPlan):
        """
        Composites and renders the final video.
        """
        logger.info(f"Starting composition for {len(plan.clip_crop_data)} clips...")
        
        final_clips = []
        
        # Load source globally? No, load per subclip to avoid locking issues, or load once.
        # MoviePy VideoFileClip holds file open.
        
        for crop_data in plan.clip_crop_data:
            # We assume clip_crop_data corresponds to sequential viral clips
            # We need start/end time of this clip relative to original video.
            # ClipCropData frames have timestamps relative to VIDEO start? Yes, from Part 4.
            if not crop_data.frames:
                continue
                
            start_t = crop_data.frames[0].timestamp
            end_t = crop_data.frames[-1].timestamp
            duration = end_t - start_t
            
            logger.info(f"Compositing clip: {start_t:.1f}s - {end_t:.1f}s")
            
            # 1. Source Subclip
            # Use context manager or close manually
            src_clip = VideoFileClip(plan.source_video_path).subclipped(start_t, end_t)
            fps = src_clip.fps
            
            # 2. Dynamic Crop (Layer 1)
            # We need to capture crop_data.frames in closure
            frames_data = crop_data.frames
            
            def crop_filter(
                get_frame: Any, t: float, fps: float = fps, frames_data: List[Any] = frames_data
            ) -> np.ndarray:
                frame = get_frame(t)
                
                # Optimize:
                idx = int(t * fps)
                if idx < len(frames_data):
                    cd = frames_data[idx]
                else:
                    cd = frames_data[-1]
                
                x, y, w, h = cd.crop_x, cd.crop_y, cd.crop_w, cd.crop_h
                
                # Slice
                # Ensure bounds
                H, W, _ = frame.shape
                x = max(0, min(x, W - w))
                y = max(0, min(y, H - h))
                
                return frame[y:y+h, x:x+w]

            cropped_clip = src_clip.fl(crop_filter, apply_to=['mask'])
            
            # 3. Background (Layer 0)
            # Blurred version. 
            # We need to resize cropped_clip to target resolution?
            # Target is 1080x1920.
            # cropped_clip size is ~607x1080.
            # We center it.
            
            # Create Background
            # It should be the FULL frame (uncropped) blurred.
            # src_clip is full frame.
            
            def blur_filter(get_frame: Any, t: float) -> np.ndarray:
                frame = get_frame(t)
                return create_blurred_background(frame, self.cfg.blur_radius, self.cfg.output_resolution)
            
            bg_clip = src_clip.fl(blur_filter, apply_to=[]) # No mask for BG
            
            # 4. B-Roll (Layer 2)
            # Check overlap with B-Roll segments
            b_roll_clips = []
            for br in plan.b_roll_segments:
                # br.start/end are absolute timestamps
                # We are in subclip (start_t, end_t).
                # Intersection?
                overlap_start = max(start_t, br.start)
                overlap_end = min(end_t, br.end)
                
                if overlap_start < overlap_end:
                    # There is B-Roll here.
                    br_path = br.video_path
                    if Path(br_path).exists():
                        br_src = VideoFileClip(br_path)
                        # Loop if too short? Assume matched length for now.
                        # Cut relevant part (or start from 0 if generic)
                        # Usually B-Roll is generic, we take first (overlap_end - overlap_start) seconds
                        br_dur = overlap_end - overlap_start
                        
                        # Clip B-Roll
                        if br_src.duration < br_dur:
                            br_src = vfx.loop(br_src, duration=br_dur)
                        else:
                            br_src = br_src.subclipped(0, br_dur)
                            
                        # Resize to fill 9:16
                        # moviepy resized logic
                        # br_src = br_src.resized(height=1920) # Simple resize, maybe crop?
                        # Let's just resize to fill
                        br_src = br_src.with_effects([vfx.Resize(self.cfg.output_resolution)]) # v2 syntax
                        
                        # Set start time relative to composite
                        rel_start = overlap_start - start_t
                        br_src = br_src.with_start(rel_start)
                        
                        b_roll_clips.append(br_src)
            
            # Composite layers
            # Order: BG, Cropped (Centered), B-Rolls
            
            # Center the cropped clip on canvas
            cropped_clip = cropped_clip.with_position("center")
            
            layers = [bg_clip, cropped_clip] + b_roll_clips
            comp = CompositeVideoClip(layers, size=self.cfg.output_resolution)
            comp = comp.with_duration(duration) # Force duration
            
            final_clips.append(comp)

        # Concatenate all viral clips
        if not final_clips:
            logger.warning("No clips to render.")
            return

        final_video = concatenate_videoclips(final_clips, method="compose") # compose handles different sizes if any
        
        # Add Music (Placeholder)
        # music = AudioFileClip("assets/music/track.mp3").with_volume(0.1)
        # final_video = final_video.with_audio(CompositeAudioClip([final_video.audio, music]))
        
        # Write
        logger.info(f"Rendering to {plan.output_path}...")
        final_video.write_videofile(
            plan.output_path, 
            fps=30, 
            codec="libx264", 
            audio_codec="aac",
            preset="ultrafast",
            threads=4,
            logger=None # Reduce noise
        )
        logger.success("Render Complete.")
        
        # Cleanup
        final_video.close()
        for c in final_clips:
            c.close()