"""
Screen Capture - Handles capturing and processing screenshots from the emulator.
"""
import io
import sys
import time
from typing import Optional, Tuple
import logging
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

# Add parent directory to path for imports
_parent_dir = str(Path(__file__).parent.parent)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from core.adb_controller import ADBController


class ScreenCapture:
    """
    Handles screen capture from BlueStacks emulator.
    Provides methods for capturing, caching, and preprocessing screenshots.
    """
    
    def __init__(self, adb: ADBController, logger: Optional[logging.Logger] = None):
        """
        Initialize screen capture.
        
        Args:
            adb: ADB controller instance
            logger: Optional logger instance
        """
        self.adb = adb
        self.logger = logger or logging.getLogger(__name__)
        
        # Cache for reducing screenshot frequency
        self._last_capture: Optional[np.ndarray] = None
        self._last_capture_time: float = 0
        self._cache_duration: float = 0.1  # Cache for 100ms
        
        # Expected resolution
        self.expected_width = 960
        self.expected_height = 540
    
    def capture(self, use_cache: bool = True) -> Optional[np.ndarray]:
        """
        Capture the current screen.
        
        Args:
            use_cache: Whether to use cached screenshot if available
        
        Returns:
            Screenshot as numpy array (BGR format for OpenCV), or None if failed
        """
        # Check cache
        current_time = time.time()
        if use_cache and self._last_capture is not None:
            if current_time - self._last_capture_time < self._cache_duration:
                return self._last_capture.copy()
        
        # Capture new screenshot
        img_data = self.adb.screencap()
        if img_data is None:
            self.logger.warning("Failed to capture screenshot")
            return None
        
        try:
            # Convert bytes to PIL Image, then to numpy array
            img = Image.open(io.BytesIO(img_data))
            img_array = np.array(img)
            
            # Convert RGB to BGR for OpenCV
            if len(img_array.shape) == 3:
                if img_array.shape[2] == 4:  # RGBA
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
                elif img_array.shape[2] == 3:  # RGB
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Update cache
            self._last_capture = img_array
            self._last_capture_time = current_time
            
            return img_array.copy()
            
        except Exception as e:
            self.logger.error(f"Failed to process screenshot: {e}")
            return None
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> Optional[np.ndarray]:
        """
        Capture a specific region of the screen.
        
        Args:
            x: Top-left X coordinate
            y: Top-left Y coordinate
            width: Region width
            height: Region height
        
        Returns:
            Region as numpy array, or None if failed
        """
        full_screen = self.capture()
        if full_screen is None:
            return None
        
        # Bounds checking
        h, w = full_screen.shape[:2]
        x = max(0, min(x, w - 1))
        y = max(0, min(y, h - 1))
        x2 = min(x + width, w)
        y2 = min(y + height, h)
        
        return full_screen[y:y2, x:x2].copy()
    
    def get_resolution(self) -> Tuple[int, int]:
        """
        Get the current screen resolution.
        
        Returns:
            Tuple of (width, height)
        """
        screen = self.capture()
        if screen is not None:
            h, w = screen.shape[:2]
            return w, h
        return self.expected_width, self.expected_height
    
    def check_resolution(self) -> bool:
        """
        Check if screen resolution matches expected (960x540).
        
        Returns:
            True if resolution is correct
        """
        w, h = self.get_resolution()
        if w == self.expected_width and h == self.expected_height:
            return True
        self.logger.warning(
            f"Resolution mismatch! Expected {self.expected_width}x{self.expected_height}, "
            f"got {w}x{h}. Please configure BlueStacks correctly."
        )
        return False
    
    def save_screenshot(self, path: str) -> bool:
        """
        Save current screenshot to file.
        
        Args:
            path: File path to save to
        
        Returns:
            True if successful
        """
        screen = self.capture()
        if screen is not None:
            cv2.imwrite(path, screen)
            self.logger.debug(f"Screenshot saved to {path}")
            return True
        return False
    
    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert image to grayscale."""
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image
    
    def to_hsv(self, image: np.ndarray) -> np.ndarray:
        """Convert image to HSV color space."""
        return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    def get_pixel_color(self, x: int, y: int) -> Optional[Tuple[int, int, int]]:
        """
        Get the color of a specific pixel.
        
        Args:
            x: X coordinate
            y: Y coordinate
        
        Returns:
            Tuple of (B, G, R) values, or None if failed
        """
        screen = self.capture()
        if screen is not None:
            h, w = screen.shape[:2]
            if 0 <= x < w and 0 <= y < h:
                return tuple(screen[y, x])
        return None
    
    def invalidate_cache(self):
        """Force next capture to get a fresh screenshot."""
        self._last_capture = None
        self._last_capture_time = 0


# Quick test
if __name__ == "__main__":
    from adb_controller import ADBController
    from logger import setup_logger
    
    log = setup_logger("capture_test", "debug")
    adb = ADBController(port=5555, logger=log)
    
    if adb.connect():
        capture = ScreenCapture(adb, log)
        
        print("Resolution:", capture.get_resolution())
        print("Resolution OK:", capture.check_resolution())
        
        if capture.save_screenshot("test_capture.png"):
            print("Screenshot saved!")
        
        adb.disconnect()

