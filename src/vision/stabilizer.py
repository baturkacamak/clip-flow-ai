from typing import Optional, Tuple


class Stabilizer:
    """
    Implements Exponential Moving Average (EMA) to smooth coordinates.
    """
    def __init__(self, alpha: float = 0.1):
        """
        Args:
            alpha: Smoothing factor (0 < alpha <= 1). 
                   Lower = smoother (less responsive).
                   Higher = more responsive (jittery).
        """
        self.alpha = alpha
        self.prev_x: Optional[float] = None
        self.prev_y: Optional[float] = None

    def update(self, x: float, y: float) -> Tuple[int, int]:
        """
        Update the stabilizer with new raw coordinates and return smoothed values.
        """
        if self.prev_x is None or self.prev_y is None:
            self.prev_x = x
            self.prev_y = y
            return int(x), int(y)

        # EMA Formula: S_t = alpha * Y_t + (1 - alpha) * S_{t-1}
        smooth_x = self.alpha * x + (1 - self.alpha) * self.prev_x
        smooth_y = self.alpha * y + (1 - self.alpha) * self.prev_y

        self.prev_x = smooth_x
        self.prev_y = smooth_y

        return int(smooth_x), int(smooth_y)

    def reset(self) -> None:
        """Resets the stabilizer state."""
        self.prev_x = None
        self.prev_y = None
