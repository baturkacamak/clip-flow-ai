import os
import subprocess
from pathlib import Path
from typing import List

import cv2
from loguru import logger

from src.config_manager import ConfigManager
from src.editing.models import RenderPlan


class FFmpegCompositor:
    def __init__(self, config_manager: ConfigManager):
        self.cfg = config_manager.editing
        self.paths = config_manager.paths

    def render(self, plan: RenderPlan):
        """
        Renders video using Hybrid CV2 (Crop) + FFmpeg (Composite) approach.
        """
        logger.info("Starting FFmpeg Hybrid Render...")
        
        # 1. Fast Crop Generation (Python/CV2)
        # We generate a video of just the centered face
        # We process frame by frame but efficiently.
        
        # We need to handle multiple clips? plan.clip_crop_data is a list.
        # We should render them sequentially or concat.
        # For simplicity, let's assume we render one monolithic "face_track.mp4" for the whole timeline?
        # No, the timeline jumps.
        
        # Let's iterate clips and render chunks.
        segment_files = []
        
        for _i, crop_data in enumerate(plan.clip_crop_data):
            clip_id = crop_data.clip_id
            temp_face_path = Path(self.paths.workspace_dir) / f"face_{clip_id}.mp4"
            
            if not self._generate_cropped_video(plan.source_video_path, crop_data, str(temp_face_path)):
                logger.error(f"Failed to generate crop for {clip_id}")
                continue
            
            # Now we have the cropped face video.
            # We need the background.
            # Generate BG using FFmpeg (crop 9:16 area from center? No, blur full video resized)
            # Actually, standard effect is: Background = Full Video (blurred, zoomed).
            
            # Complex FFmpeg Filter:
            # Inputs:
            # 0: Source Video (trimmed to clip time)
            # 1: Cropped Face Video (temp_face_path)
            # 2+: B-Rolls
            
            # We need to extract the source segment first to sync with face video.
            start_t = crop_data.frames[0].timestamp
            end_t = crop_data.frames[-1].timestamp
            duration = end_t - start_t
            
            segment_final = Path(self.paths.workspace_dir) / f"segment_{clip_id}.mp4"
            
            # Build Filter Complex
            # [0:v] (Source) -> scale=-2:1920, boxblur=20 [bg]
            # [1:v] (Face) -> [bg] overlay=(W-w)/2:(H-h)/2 [base]
            # B-Rolls overlay on top
            
            # Note: We need to trim source to match exact frames of face video.
            
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(start_t), "-t", str(duration), "-i", plan.source_video_path, # Input 0: Source Segment
                "-i", str(temp_face_path), # Input 1: Face
            ]
            
            # Add B-Roll inputs
            # Map b_rolls to this clip
            clip_b_rolls = []
            for br in plan.b_roll_segments:
                # Check overlap (logic from compositor.py)
                if max(start_t, br.start) < min(end_t, br.end):
                    clip_b_rolls.append(br)
            
            for br in clip_b_rolls:
                cmd.extend(["-i", br.video_path]) # Inputs 2, 3...
            
            # Filter Complex
            filter_str = ""
            
            # 1. Prepare Background
            # Scale to height 1920 (maintaining aspect), crop to 1080x1920 centered, blur
            target_w, target_h = self.cfg.output_resolution
            filter_str += f"[0:v]scale=-2:{target_h},crop={target_w}:{target_h},boxblur={self.cfg.blur_radius}:5[bg]"
            
            # 2. Overlay Face
            # Face video is already cropped size (e.g. 608x1080).
            # Center it.
            filter_str += "[bg][1:v]overlay=(W-w)/2:(H-h)/2[v1]"
            
            last_stream = "v1"
            
            # 3. Overlay B-Rolls
            # Need to trim B-Roll and set start time
            # ffmpeg -itsoffset? Or enable input at specific time.
            # overlay=enable='between(t,start,end)'
            
            for idx, br in enumerate(clip_b_rolls):
                input_idx = idx + 2
                rel_start = max(0, br.start - start_t)
                rel_end = min(duration, br.end - start_t)
                
                # Complex filter
                filter_str += (
                    f"[{input_idx}:v]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
                    f"crop={target_w}:{target_h}[br{idx}];"
                )
                
                filter_str += f"[{last_stream}][br{idx}]overlay=enable='between(t,{rel_start},{rel_end})'[v{idx+2}];"
                last_stream = f"v{idx+2}"
            
            # Map final video
            cmd.extend([
                "-filter_complex", filter_str,
                "-map", f"[{last_stream}]",
                "-map", "0:a", # Use source audio
                "-c:v", "libx264", "-preset", "fast",
                str(segment_final)
            ])
            
            logger.info(f"Rendering segment {clip_id} via FFmpeg...")
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            segment_files.append(str(segment_final))
            
            # Cleanup temp face
            try:
                os.remove(temp_face_path)
            except Exception:
                pass

        # Concat segments
        if segment_files:
            self._concat_segments(segment_files, plan.output_path)
            logger.success("FFmpeg Render Complete.")

    def _generate_cropped_video(self, source_path, crop_data, output_path):
        """Uses CV2 to write the cropped face video very fast."""
        cap = cv2.VideoCapture(source_path)
        if not cap.isOpened():
            return False
        
        frames = crop_data.frames
        if not frames:
            return False
        
        # Setup Writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = cap.get(cv2.CAP_PROP_FPS)
        w, h = frames[0].crop_w, frames[0].crop_h
        writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
        
        # Optimize: Seek to first frame
        start_frame = frames[0].frame_index
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        current_idx = start_frame
        
        # Frame map for O(1) lookup or just iterate logic
        # frames list is sequential.
        frame_iter = iter(frames)
        next_crop = next(frame_iter, None)
        
        while next_crop:
            ret, frame = cap.read()
            if not ret:
                break
            
            if current_idx == next_crop.frame_index:
                # Crop
                x, y = next_crop.crop_x, next_crop.crop_y
                cw, ch = next_crop.crop_w, next_crop.crop_h
                
                # Check bounds
                H, W, _ = frame.shape
                x = max(0, min(x, W - cw))
                y = max(0, min(y, H - ch))
                
                cropped = frame[y:y+ch, x:x+cw]
                writer.write(cropped)
                
                next_crop = next(frame_iter, None)
            
            current_idx += 1
            if next_crop and current_idx > next_crop.frame_index:
                # We missed a frame? Or seeking drift?
                # Just continue reading until catch up?
                # Or if video skipped.
                pass
                
        cap.release()
        writer.release()
        return True

    def _concat_segments(self, files: List[str], output: str):
        # Create concat file
        list_path = "concat_list.txt"
        with open(list_path, "w") as f:
            for path in files:
                f.write(f"file '{path}'\n")
        
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", list_path, "-c", "copy", output
        ]
        subprocess.run(cmd, check=True)
        os.remove(list_path)
        # Cleanup segments
        for f in files:
            try:
                os.remove(f)
            except Exception:
                pass
