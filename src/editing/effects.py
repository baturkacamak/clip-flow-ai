import numpy as np
from skimage.filters import gaussian
from skimage.transform import resize
from typing import Tuple, Any, cast

def create_blurred_background(frame: np.ndarray[Any, Any], radius: float, target_size: Tuple[int, int]) -> np.ndarray[Any, Any]:
    """
    Creates a blurred background from the source frame.
    Optimization: Downscale -> Blur -> Upscale.
    """
    target_w, target_h = target_size
    h, w, _ = frame.shape
    
    # 1. Calculate scale to cover target (Zoom fill)
    scale_w = target_w / w
    scale_h = target_h / h
    scale = max(scale_w, scale_h)
    
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    # 2. Resize to small for fast blur (e.g., 1/10th of target or fixed small size)
    # Actually, we can resize directly to target size then blur, but blurring is kernel size dependent.
    # Let's resize to target size first (or slightly larger)
    
    resized = resize(frame, (new_h, new_w), preserve_range=True).astype(np.uint8) # type: ignore
    
    # 3. Center crop to exact target size
    start_x = (new_w - target_w) // 2
    start_y = (new_h - target_h) // 2
    
    cropped = resized[start_y:start_y+target_h, start_x:start_x+target_w]
    
    # 4. Blur
    # Sigma for gaussian. Radius 21 is huge.
    # Normalize 0-1 for float, then back to uint8
    blurred = gaussian(cropped, sigma=radius, channel_axis=-1, preserve_range=True).astype(np.uint8) # type: ignore
    
    return cast(np.ndarray[Any, Any], blurred)