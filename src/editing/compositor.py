from pathlib import Path
from typing import Any, List, cast

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
        idx = int(t * fps)
        idx = max(0, min(idx, len(crop_frames) - 1))
        return crop_frames[idx]

    def render_story_mode(self, plan: RenderPlan) -> None:
        """
        Renders "Story Mode" (Audio + B-Rolls).
        """
        logger.info("Starting Story Mode Composition...")
        
        if not plan.source_audio_path or not Path(plan.source_audio_path).exists():
            logger.error("Source audio missing for Story Mode.")
            return

        audio = AudioFileClip(plan.source_audio_path)
        clips = []
        
        # Iterate B-Rolls and create clips
        for br in plan.b_roll_segments:
            duration = br.end - br.start
            if duration <= 0:
                continue
            
            try:
                clip = VideoFileClip(br.video_path)
                
                # Loop if needed
                if clip.duration < duration:
                    clip = vfx.loop(clip, duration=duration)
                else:
                    clip = clip.subclipped(0, duration)
                
                # Resize to target
                # Aspect Ratio fill?
                # We want 9:16 (1080x1920) usually for shorts.
                # Use vfx.Resize to fill or fit?
                # For shorts, we usually crop center 9:16.
                # Helper: resize to height, then crop width? Or max dimension.
                # Let's resize to cover target.
                w, h = self.cfg.output_resolution
                
                # Resize keeping aspect ratio so it covers the area
                # Calculate scale
                scale_w = w / clip.w
                scale_h = h / clip.h
                scale = max(scale_w, scale_h)
                
                clip = clip.resized(scale=scale)
                
                # Center crop
                clip = clip.cropped(width=w, height=h, x_center=clip.w/2, y_center=clip.h/2)
                
                # Ken Burns Effect (Slow Zoom)
                # Zoom from 1.0 to 1.1 over duration
                # We can use vfx.Resize with lambda? expensive.
                # Or just simple resize.
                # clip = clip.with_effects([vfx.Resize(lambda t: 1 + 0.05 * (t/duration))]) # Simulates zoom
                # Note: vfx.Resize on each frame is slow.
                # We'll skip Ken Burns for speed/stability in MVP, but it's requested "Optional but cool".
                # I'll leave it commented or simple.
                
                clips.append(clip)
                
            except Exception as e:
                logger.warning(f"Failed to load clip {br.video_path}: {e}")
                # Use placeholder (black)
                # color_clip = ColorClip(size=(w,h), color=(0,0,0), duration=duration)
                # clips.append(color_clip)
                pass

        if not clips:
            logger.error("No valid clips for story.")
            return

        # Concatenate
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Sync Audio duration
        # If visual is longer/shorter than audio?
        # Usually we want visual to match audio exactly.
        final_video = final_video.with_audio(audio)
        
        # Trim visual to match audio end
        final_video = final_video.with_duration(audio.duration)

        logger.info(f"Rendering Story to {plan.output_path}...")
        final_video.write_videofile(
            plan.output_path,
            fps=30,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=4,
            logger=None
        )
        logger.success("Story Render Complete.")
        
        # Cleanup
        final_video.close()
        for c in clips:
            c.close()
        audio.close()

    def render(self, plan: RenderPlan) -> None:
        """
        Composites and renders the final video (Viral Mode).
        """
        logger.info(f"Starting composition for {len(plan.clip_crop_data)} clips...")
        
        final_clips = []
        
        for crop_data in plan.clip_crop_data:
            if not crop_data.frames:
                continue
                
            start_t = crop_data.frames[0].timestamp
            end_t = crop_data.frames[-1].timestamp
            duration = end_t - start_t
            
            logger.info(f"Compositing clip: {start_t:.1f}s - {end_t:.1f}s")
            
            src_clip = VideoFileClip(plan.source_video_path).subclipped(start_t, end_t)
            fps = src_clip.fps
            
            frames_data = crop_data.frames
            
            def crop_filter(
                get_frame: Any, t: float, fps: float = fps, frames_data: List[Any] = frames_data
            ) -> np.ndarray[Any, Any]:
                frame = get_frame(t)
                idx = int(t * fps)
                if idx < len(frames_data):
                    cd = frames_data[idx]
                else:
                    cd = frames_data[-1]
                
                x, y, w, h = cd.crop_x, cd.crop_y, cd.crop_w, cd.crop_h
                
                H, W, _ = frame.shape
                x = max(0, min(x, W - w))
                y = max(0, min(y, H - h))
                
                return cast(np.ndarray[Any, Any], frame[y:y+h, x:x+w])

            cropped_clip = src_clip.fl(crop_filter, apply_to=['mask'])
            
            def blur_filter(get_frame: Any, t: float) -> np.ndarray[Any, Any]:
                frame = get_frame(t)
                return create_blurred_background(frame, self.cfg.blur_radius, self.cfg.output_resolution)
            
            bg_clip = src_clip.fl(blur_filter, apply_to=[])
            
            b_roll_clips = []
            for br in plan.b_roll_segments:
                overlap_start = max(start_t, br.start)
                overlap_end = min(end_t, br.end)
                
                if overlap_start < overlap_end:
                    br_path = br.video_path
                    if Path(br_path).exists():
                        br_src = VideoFileClip(br_path)
                        br_dur = overlap_end - overlap_start
                        
                        if br_src.duration < br_dur:
                            br_src = vfx.loop(br_src, duration=br_dur)
                        else:
                            br_src = br_src.subclipped(0, br_dur)
                            
                        br_src = br_src.with_effects([vfx.Resize(self.cfg.output_resolution)])
                        
                        rel_start = overlap_start - start_t
                        br_src = br_src.with_start(rel_start)
                        
                        b_roll_clips.append(br_src)
            
            cropped_clip = cropped_clip.with_position("center")
            
            layers = [bg_clip, cropped_clip] + b_roll_clips
            comp = CompositeVideoClip(layers, size=self.cfg.output_resolution)
            comp = comp.with_duration(duration)
            
            final_clips.append(comp)

        if not final_clips:
            logger.warning("No clips to render.")
            return

        final_video = concatenate_videoclips(final_clips, method="compose")
        
        logger.info(f"Rendering to {plan.output_path}...")
        final_video.write_videofile(
            plan.output_path, 
            fps=30, 
            codec="libx264", 
            audio_codec="aac",
            preset="ultrafast",
            threads=4,
            logger=None
        )
        logger.success("Render Complete.")
        
        final_video.close()
        for c in final_clips:
            c.close()
