from pathlib import Path
from typing import Any, List, Optional

import cv2
import mediapipe as mp
from loguru import logger

from src.config_manager import ConfigManager
from src.intelligence.models import ViralClip
from src.vision.models import ClipCropData, FrameCrop
from src.vision.stabilizer import Stabilizer


class SmartCropper:
    def __init__(self, config_manager: ConfigManager):
        self.cfg = config_manager.vision
        self.paths = config_manager.paths
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1, # 1 for full range/further faces
            min_detection_confidence=self.cfg.face_detection_confidence
        )
        self.stabilizer = Stabilizer(alpha=self.cfg.stabilization_factor)

    def process_clips(self, video_path: str, clips: List[ViralClip], video_id: str) -> List[ClipCropData]:
        """
        Generates crop coordinates for a list of viral clips.
        """
        results = []
        
        if not Path(video_path).exists():
            logger.error(f"Video not found: {video_path}")
            return []

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error("Failed to open video.")
            return []

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        logger.info(f"Video Info: {width}x{height} @ {fps}fps, {total_frames} frames.")

        for clip in clips:
            logger.info(f"Processing clip: {clip.title} ({clip.start_time:.1f}s - {clip.end_time:.1f}s)")
            self.stabilizer.reset() # Reset stabilizer for each new clip
            
            crop_data = self._process_single_clip(cap, clip, width, height, fps, video_id)
            if crop_data:
                results.append(crop_data)
                
                # Save individual crop data
                output_path = Path(self.paths.workspace_dir) / f"crops_{crop_data.clip_id}.json"
                with open(output_path, "w") as f:
                    f.write(crop_data.model_dump_json(indent=2))

        cap.release()
        return results

    def _process_single_clip(self, cap: cv2.VideoCapture, clip: ViralClip, 
                             video_w: int, video_h: int, fps: float, video_id: str) -> Optional[ClipCropData]:
        
        start_frame = int(clip.start_time * fps)
        end_frame = int(clip.end_time * fps)
        
        # Seek
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        frames_data: List[FrameCrop] = []
        clip_id = f"{video_id}_{int(clip.start_time)}_{int(clip.end_time)}"
        
        # Debug Video Writer
        debug_writer = None
        if self.cfg.debug_preview:
            debug_path = Path(self.paths.workspace_dir) / f"debug_{clip_id}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v') # type: ignore
            # Preview is vertical 9:16? Or Just raw with box?
            # Let's write the cropped result for visualization
            target_w = int(video_h * self.cfg.vertical_crop_ratio)
            target_h = video_h
            debug_writer = cv2.VideoWriter(str(debug_writer), fourcc, fps, (target_w, target_h)) # Error here? str(Path)
            # Re-init correctly below
            debug_writer = cv2.VideoWriter(str(debug_path), fourcc, fps, (target_w, target_h))

        current_frame_idx = start_frame
        
        while current_frame_idx < end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            
            # RGB conversion for MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(frame_rgb)
            
            face_center_x = video_w // 2
            face_center_y = video_h // 3 # Rule of thirds (upper) default
            
            if results.detections:
                # Find dominant face
                def get_face_area(d: Any) -> float:
                    rel_box = d.location_data.relative_bounding_box
                    return float(rel_box.width * rel_box.height)

                best_detection = max(results.detections, key=get_face_area)
                bbox = best_detection.location_data.relative_bounding_box
                
                # Calculate center
                raw_x = int((bbox.xmin + bbox.width / 2) * video_w)
                _raw_y = int((bbox.ymin + bbox.height / 2) * video_h)
                
                # We mainly care about X for 9:16 crop from 16:9. Y is usually full height.
                face_center_x = raw_x
                # face_center_y = raw_y # We might want to keep Y stable or track it too.
            
            # Stabilize
            smooth_x, smooth_y = self.stabilizer.update(face_center_x, face_center_y)
            
            # Calculate Crop Rect (9:16) centered on smooth_x
            target_h = video_h
            target_w = int(target_h * self.cfg.vertical_crop_ratio)
            
            crop_x = smooth_x - (target_w // 2)
            crop_y = 0 # Vertical is full height usually
            
            # Boundary checks
            crop_x = max(0, min(crop_x, video_w - target_w))
            
            # Save Data
            timestamp = current_frame_idx / fps
            frames_data.append(FrameCrop(
                timestamp=timestamp,
                frame_index=current_frame_idx,
                crop_x=crop_x,
                crop_y=crop_y,
                crop_w=target_w,
                crop_h=target_h
            ))
            
            # Debug Preview
            if debug_writer:
                # Crop the frame
                cropped_frame = frame[crop_y:crop_y+target_h, crop_x:crop_x+target_w]
                
                # Draw green box on face relative to crop? 
                # Or just save the cropped result.
                # If we want to see the face detection, we'd need to draw on original then crop.
                # Let's just save the cropped frame to see stability.
                if cropped_frame.shape[0] == target_h and cropped_frame.shape[1] == target_w:
                     debug_writer.write(cropped_frame)
            
            current_frame_idx += 1

        if debug_writer:
            debug_writer.release()
            logger.info(f"Debug preview saved to {debug_path}")

        return ClipCropData(
            clip_id=clip_id,
            video_id=video_id,
            frames=frames_data
        )
