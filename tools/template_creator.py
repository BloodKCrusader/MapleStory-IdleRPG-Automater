#!/usr/bin/env python3
"""
Template Creator Tool - Capture UI elements for template matching.

Controls:
  LEFT CLICK + DRAG  = Select region for template
  RIGHT CLICK        = Tap in game at that position (to navigate)
  C                  = Capture new screenshot (after navigating)
  S                  = Save selected region as template
  F                  = Save full screenshot
  Q                  = Quit
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
import numpy as np

from core.adb_controller import ADBController
from core.logger import setup_logger


class TemplateCreator:
    """Interactive tool for creating template images."""
    
    def __init__(self, adb: ADBController, output_dir: str = "templates/maple_story_idle"):
        self.adb = adb
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_image = None
        self.display_image = None
        self.selection_start = None
        self.selection_end = None
        self.selecting = False
        self.last_tap = None
        
        self.window_name = "Template Creator"
    
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events."""
        
        # LEFT BUTTON - Selection for template
        if event == cv2.EVENT_LBUTTONDOWN:
            self.selection_start = (x, y)
            self.selection_end = None
            self.selecting = True
        
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.selecting:
                self.selection_end = (x, y)
        
        elif event == cv2.EVENT_LBUTTONUP:
            if self.selecting:
                self.selection_end = (x, y)
                self.selecting = False
        
        # RIGHT BUTTON - Tap in game
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.last_tap = (x, y)
            print(f"\n>>> TAPPING game at ({x}, {y})...")
            if self.adb.tap(x, y):
                print(f"    [OK] Tap sent! Press 'c' to refresh screenshot.")
            else:
                print(f"    [FAIL] Tap failed!")
    
    def capture_screen(self) -> bool:
        """Capture current screen from emulator."""
        print("Capturing screenshot...")
        img_data = self.adb.screencap()
        if img_data is not None:
            # Convert bytes to numpy array
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None:
                self.current_image = img
                print(f"[OK] Screenshot captured: {img.shape[1]}x{img.shape[0]}")
                return True
        print("[FAIL] Failed to capture screenshot")
        return False
    
    def save_selection(self, name: str) -> bool:
        """Save the selected region as a template."""
        if self.current_image is None:
            print("No image captured!")
            return False
        
        if self.selection_start is None or self.selection_end is None:
            print("No region selected! Click and drag to select.")
            return False
        
        # Get selection bounds
        x1 = min(self.selection_start[0], self.selection_end[0])
        y1 = min(self.selection_start[1], self.selection_end[1])
        x2 = max(self.selection_start[0], self.selection_end[0])
        y2 = max(self.selection_start[1], self.selection_end[1])
        
        if x2 - x1 < 10 or y2 - y1 < 10:
            print("Selection too small! Make it at least 10x10 pixels.")
            return False
        
        # Extract region
        region = self.current_image[y1:y2, x1:x2]
        
        # Save template
        filepath = self.output_dir / f"{name}.png"
        cv2.imwrite(str(filepath), region)
        
        print(f"\n[OK] SAVED: {filepath}")
        print(f"     Size: {x2-x1}x{y2-y1} pixels")
        print(f"     Position: ({x1}, {y1}) to ({x2}, {y2})")
        
        # Clear selection
        self.selection_start = None
        self.selection_end = None
        
        return True
    
    def run_interactive(self):
        """Run interactive template creation mode."""
        print("\n" + "=" * 60)
        print("  TEMPLATE CREATOR - Interactive Mode")
        print("=" * 60)
        print()
        print("  CONTROLS:")
        print("  -----------------------------------------")
        print("  LEFT CLICK + DRAG  = Select region")
        print("  RIGHT CLICK        = TAP in game (navigate)")
        print("  C                  = Capture new screenshot")
        print("  S                  = Save selected region")
        print("  F                  = Save full screenshot")
        print("  Q                  = Quit")
        print("  -----------------------------------------")
        print()
        print("  TIP: RIGHT-CLICK to tap buttons in the game,")
        print("       then press C to refresh the screenshot!")
        print()
        print("=" * 60)
        
        # Initial capture
        if not self.capture_screen():
            print("Failed to capture initial screen!")
            return
        
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        while True:
            # Create display image
            if self.current_image is not None:
                display = self.current_image.copy()
                
                # Draw selection rectangle
                if self.selection_start and self.selection_end:
                    cv2.rectangle(
                        display,
                        self.selection_start,
                        self.selection_end,
                        (0, 255, 0),  # Green
                        2
                    )
                    # Show size
                    w = abs(self.selection_end[0] - self.selection_start[0])
                    h = abs(self.selection_end[1] - self.selection_start[1])
                    cv2.putText(
                        display,
                        f"{w}x{h}",
                        (min(self.selection_start[0], self.selection_end[0]), 
                         min(self.selection_start[1], self.selection_end[1]) - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        1
                    )
                
                # Draw last tap position
                if self.last_tap:
                    cv2.circle(display, self.last_tap, 15, (0, 0, 255), 2)
                    cv2.circle(display, self.last_tap, 3, (0, 0, 255), -1)
                
                # Draw instructions at top
                cv2.rectangle(display, (0, 0), (display.shape[1], 25), (0, 0, 0), -1)
                cv2.putText(
                    display,
                    "LEFT-drag: Select | RIGHT-click: Tap game | C: Refresh | S: Save | Q: Quit",
                    (10, 17),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (255, 255, 255),
                    1
                )
                
                cv2.imshow(self.window_name, display)
            
            key = cv2.waitKey(50) & 0xFF
            
            if key == ord('q') or key == 27:  # Q or ESC
                break
            
            elif key == ord('c'):
                print("\nRefreshing screenshot...")
                self.capture_screen()
                self.last_tap = None
            
            elif key == ord('s'):
                if self.selection_start and self.selection_end:
                    print("\n" + "-" * 40)
                    name = input("Enter template name (e.g., pq_button): ").strip()
                    if name:
                        self.save_selection(name)
                    print("-" * 40)
                else:
                    print("\nNo region selected! Left-click and drag first.")
            
            elif key == ord('f'):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name = f"fullscreen_{timestamp}"
                filepath = self.output_dir / f"{name}.png"
                cv2.imwrite(str(filepath), self.current_image)
                print(f"\n[OK] Saved full screenshot: {filepath}")
        
        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(
        description="Template Creator - Capture game UI elements",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Controls:
  LEFT CLICK + DRAG  = Select region for template
  RIGHT CLICK        = Tap in game (to navigate menus)
  C                  = Capture new screenshot
  S                  = Save selected region
  Q                  = Quit
        """
    )
    parser.add_argument("--port", "-p", type=int, default=5555, help="ADB port (default: 5555)")
    parser.add_argument("--output", "-o", default="templates/maple_story_idle", help="Output directory")
    args = parser.parse_args()
    
    logger = setup_logger("template_creator", "info", log_to_file=False)
    
    print(f"\nConnecting to BlueStacks on port {args.port}...")
    adb = ADBController(port=args.port, logger=logger)
    
    if not adb.connect():
        print("\n[FAIL] Failed to connect!")
        print("Make sure:")
        print("  1. BlueStacks is running")
        print("  2. ADB is enabled (Settings > Advanced)")
        print("  3. Try port 5555, 5565, or 5575")
        sys.exit(1)
    
    print("[OK] Connected!")
    
    creator = TemplateCreator(adb, args.output)
    
    try:
        creator.run_interactive()
    except KeyboardInterrupt:
        pass
    finally:
        adb.disconnect()
        print("\nDone!")


if __name__ == "__main__":
    main()
