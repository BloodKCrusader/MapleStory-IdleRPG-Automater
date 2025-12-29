"""
Input Handler - Human-like input simulation for the bot.
"""
import random
import sys
import time
from typing import Optional, Tuple, List
import logging
from pathlib import Path

# Add parent directory to path for imports
_parent_dir = str(Path(__file__).parent.parent)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from core.adb_controller import ADBController


class InputHandler:
    """
    Handles input simulation with human-like randomization.
    Provides methods for tapping, swiping, and complex gestures.
    """
    
    def __init__(self, adb: ADBController, logger: Optional[logging.Logger] = None):
        """
        Initialize input handler.
        
        Args:
            adb: ADB controller instance
            logger: Optional logger instance
        """
        self.adb = adb
        self.logger = logger or logging.getLogger(__name__)
        
        # Humanization settings
        self.humanize = True
        self.tap_offset_range = 5  # Random pixel offset for taps
        self.tap_delay_range = (0.05, 0.15)  # Random delay before tap
        self.between_action_delay = (0.1, 0.3)  # Delay between actions
        
        # Screen dimensions (for bounds checking)
        self.screen_width = 960
        self.screen_height = 540
    
    def _humanize_point(self, x: int, y: int) -> Tuple[int, int]:
        """Add small random offset to coordinates for human-like behavior."""
        if self.humanize:
            x += random.randint(-self.tap_offset_range, self.tap_offset_range)
            y += random.randint(-self.tap_offset_range, self.tap_offset_range)
        
        # Bounds checking
        x = max(0, min(x, self.screen_width - 1))
        y = max(0, min(y, self.screen_height - 1))
        
        return x, y
    
    def _random_delay(self, delay_range: Tuple[float, float]):
        """Wait for a random amount of time."""
        if self.humanize:
            delay = random.uniform(*delay_range)
            time.sleep(delay)
    
    def tap(self, x: int, y: int, humanize: bool = True) -> bool:
        """
        Tap at coordinates with optional humanization.
        
        Args:
            x: X coordinate
            y: Y coordinate
            humanize: Whether to add random offset
        
        Returns:
            True if successful
        """
        if humanize and self.humanize:
            self._random_delay(self.tap_delay_range)
            x, y = self._humanize_point(x, y)
        
        success = self.adb.tap(x, y)
        
        if success:
            self.logger.debug(f"Tapped at ({x}, {y})")
        else:
            self.logger.warning(f"Failed to tap at ({x}, {y})")
        
        return success
    
    def tap_center(self, match_result) -> bool:
        """
        Tap at the center of a template match result.
        
        Args:
            match_result: MatchResult object with center coordinates
        
        Returns:
            True if successful
        """
        return self.tap(match_result.center_x, match_result.center_y)
    
    def double_tap(self, x: int, y: int, interval: float = 0.1) -> bool:
        """
        Double tap at coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            interval: Time between taps
        
        Returns:
            True if both taps successful
        """
        result1 = self.tap(x, y)
        time.sleep(interval)
        result2 = self.tap(x, y)
        return result1 and result2
    
    def long_press(self, x: int, y: int, duration: float = 1.0) -> bool:
        """
        Long press at coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Press duration in seconds
        
        Returns:
            True if successful
        """
        if self.humanize:
            self._random_delay(self.tap_delay_range)
            x, y = self._humanize_point(x, y)
        
        duration_ms = int(duration * 1000)
        success = self.adb.long_press(x, y, duration_ms)
        
        if success:
            self.logger.debug(f"Long press at ({x}, {y}) for {duration}s")
        
        return success
    
    def swipe(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration: float = 0.3
    ) -> bool:
        """
        Swipe from one point to another.
        
        Args:
            x1, y1: Starting coordinates
            x2, y2: Ending coordinates
            duration: Swipe duration in seconds
        
        Returns:
            True if successful
        """
        if self.humanize:
            self._random_delay(self.tap_delay_range)
            x1, y1 = self._humanize_point(x1, y1)
            x2, y2 = self._humanize_point(x2, y2)
            # Slightly randomize duration
            duration *= random.uniform(0.9, 1.1)
        
        duration_ms = int(duration * 1000)
        success = self.adb.swipe(x1, y1, x2, y2, duration_ms)
        
        if success:
            self.logger.debug(f"Swipe from ({x1}, {y1}) to ({x2}, {y2})")
        
        return success
    
    def swipe_up(self, distance: int = 200, start_y: Optional[int] = None) -> bool:
        """Swipe upward from center or specified position."""
        center_x = self.screen_width // 2
        start_y = start_y or (self.screen_height * 2 // 3)
        return self.swipe(center_x, start_y, center_x, start_y - distance)
    
    def swipe_down(self, distance: int = 200, start_y: Optional[int] = None) -> bool:
        """Swipe downward from center or specified position."""
        center_x = self.screen_width // 2
        start_y = start_y or (self.screen_height // 3)
        return self.swipe(center_x, start_y, center_x, start_y + distance)
    
    def swipe_left(self, distance: int = 200, start_x: Optional[int] = None) -> bool:
        """Swipe left from center or specified position."""
        center_y = self.screen_height // 2
        start_x = start_x or (self.screen_width * 2 // 3)
        return self.swipe(start_x, center_y, start_x - distance, center_y)
    
    def swipe_right(self, distance: int = 200, start_x: Optional[int] = None) -> bool:
        """Swipe right from center or specified position."""
        center_y = self.screen_height // 2
        start_x = start_x or (self.screen_width // 3)
        return self.swipe(start_x, center_y, start_x + distance, center_y)
    
    def tap_sequence(self, points: List[Tuple[int, int]], interval: float = 0.5) -> bool:
        """
        Tap a sequence of points with delays.
        
        Args:
            points: List of (x, y) coordinates
            interval: Delay between taps
        
        Returns:
            True if all taps successful
        """
        all_success = True
        for x, y in points:
            if not self.tap(x, y):
                all_success = False
            time.sleep(interval)
        return all_success
    
    def random_tap_in_region(self, x: int, y: int, width: int, height: int) -> bool:
        """
        Tap at a random point within a region.
        
        Args:
            x, y: Top-left corner of region
            width, height: Region dimensions
        
        Returns:
            True if successful
        """
        tap_x = x + random.randint(0, width)
        tap_y = y + random.randint(0, height)
        return self.tap(tap_x, tap_y, humanize=False)  # Already randomized
    
    def wait(self, duration: float):
        """Wait for specified duration with optional humanization."""
        if self.humanize:
            duration *= random.uniform(0.9, 1.1)
        time.sleep(duration)
    
    def wait_random(self, min_duration: float, max_duration: float):
        """Wait for a random duration."""
        duration = random.uniform(min_duration, max_duration)
        time.sleep(duration)
    
    def press_back(self) -> bool:
        """Press the back button."""
        self._random_delay(self.tap_delay_range)
        return self.adb.press_back()
    
    def press_home(self) -> bool:
        """Press the home button."""
        self._random_delay(self.tap_delay_range)
        return self.adb.press_home()
    
    # Pre-defined actions for common game interactions
    def jump(self) -> bool:
        """
        Perform a jump action.
        For MapleStory Idle, this is typically a tap in the upper area.
        """
        jump_x = self.screen_width // 2
        jump_y = self.screen_height // 4
        return self.tap(jump_x, jump_y)
    
    def random_movement(self) -> bool:
        """
        Perform a random movement (for anti-detection).
        """
        actions = [
            lambda: self.swipe_left(random.randint(50, 150)),
            lambda: self.swipe_right(random.randint(50, 150)),
            lambda: self.tap(random.randint(100, self.screen_width - 100), 
                           random.randint(100, self.screen_height - 100)),
        ]
        action = random.choice(actions)
        return action()


# Quick test
if __name__ == "__main__":
    from adb_controller import ADBController
    from logger import setup_logger
    
    log = setup_logger("input_test", "debug")
    adb = ADBController(port=5555, logger=log)
    
    if adb.connect():
        input_handler = InputHandler(adb, log)
        
        print("Testing tap at center...")
        input_handler.tap(480, 270)
        
        print("Testing swipe up...")
        input_handler.swipe_up()
        
        adb.disconnect()

