"""
ADB Controller - Manages connection to BlueStacks via Android Debug Bridge.
"""
import subprocess
import time
from typing import Optional, Tuple
from pathlib import Path
import logging


class ADBController:
    """
    Controls ADB connection to BlueStacks emulator.
    Handles connection, screenshot capture, and input commands.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 5555, logger: Optional[logging.Logger] = None):
        """
        Initialize ADB controller.
        
        Args:
            host: ADB host address (default: 127.0.0.1)
            port: ADB port (BlueStacks typically uses 5555, 5565, 5575, or 5675)
            logger: Optional logger instance
        """
        self.host = host
        self.port = port
        self.address = f"{host}:{port}"
        self.logger = logger or logging.getLogger(__name__)
        self.connected = False
        self._adb_path = self._find_adb()
        
    def _find_adb(self) -> str:
        """Find ADB executable path."""
        # Common ADB locations
        common_paths = [
            r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe",
            r"C:\Program Files (x86)\BlueStacks_nxt\HD-Adb.exe",
            r"C:\Program Files\BlueStacks\HD-Adb.exe",
            r"C:\Program Files (x86)\BlueStacks\HD-Adb.exe",
            "adb",  # System PATH
        ]
        
        for path in common_paths:
            if path == "adb":
                try:
                    result = subprocess.run(
                        ["adb", "version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        return "adb"
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            elif Path(path).exists():
                return path
        
        self.logger.warning("ADB not found in common locations, using 'adb' from PATH")
        return "adb"
    
    def _run_adb(self, *args, timeout: int = 30) -> Tuple[bool, str]:
        """
        Run an ADB command.
        
        Returns:
            Tuple of (success, output/error message)
        """
        cmd = [self._adb_path] + list(args)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except FileNotFoundError:
            return False, f"ADB not found at {self._adb_path}"
        except Exception as e:
            return False, str(e)
    
    def connect(self) -> bool:
        """
        Connect to BlueStacks via ADB.
        
        Returns:
            True if connection successful
        """
        self.logger.info(f"Connecting to BlueStacks at {self.address}...")
        
        # First, ensure ADB server is running
        self._run_adb("start-server")
        
        # Try to connect
        success, output = self._run_adb("connect", self.address)
        
        if success and ("connected" in output.lower() or "already connected" in output.lower()):
            self.connected = True
            self.logger.info(f"[OK] Connected to {self.address}")
            return True
        else:
            self.logger.error(f"[FAIL] Failed to connect: {output}")
            self.connected = False
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from the device."""
        success, _ = self._run_adb("disconnect", self.address)
        self.connected = False
        self.logger.info("Disconnected from device")
        return success
    
    def is_connected(self) -> bool:
        """Check if still connected to device."""
        success, output = self._run_adb("devices")
        if success and self.address in output:
            return True
        self.connected = False
        return False
    
    def get_screen_resolution(self) -> Optional[Tuple[int, int]]:
        """Get the screen resolution of the connected device."""
        success, output = self._run_adb("-s", self.address, "shell", "wm", "size")
        if success:
            # Output format: "Physical size: 960x540"
            try:
                size_str = output.split(":")[-1].strip()
                width, height = map(int, size_str.split("x"))
                return width, height
            except (ValueError, IndexError):
                pass
        return None
    
    def screencap(self) -> Optional[bytes]:
        """
        Capture screenshot from device.
        
        Returns:
            PNG image data as bytes, or None if failed
        """
        try:
            cmd = [self._adb_path, "-s", self.address, "exec-out", "screencap", "-p"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0 and len(result.stdout) > 0:
                return result.stdout
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
        return None
    
    def tap(self, x: int, y: int) -> bool:
        """
        Tap at coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
        
        Returns:
            True if successful
        """
        success, _ = self._run_adb("-s", self.address, "shell", "input", "tap", str(x), str(y))
        if success:
            self.logger.debug(f"Tap at ({x}, {y})")
        return success
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> bool:
        """
        Swipe from one point to another.
        
        Args:
            x1, y1: Starting coordinates
            x2, y2: Ending coordinates
            duration_ms: Swipe duration in milliseconds
        
        Returns:
            True if successful
        """
        success, _ = self._run_adb(
            "-s", self.address, "shell", "input", "swipe",
            str(x1), str(y1), str(x2), str(y2), str(duration_ms)
        )
        if success:
            self.logger.debug(f"Swipe from ({x1}, {y1}) to ({x2}, {y2})")
        return success
    
    def long_press(self, x: int, y: int, duration_ms: int = 1000) -> bool:
        """
        Long press at coordinates (implemented as swipe to same location).
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration_ms: Press duration in milliseconds
        
        Returns:
            True if successful
        """
        return self.swipe(x, y, x, y, duration_ms)
    
    def key_event(self, keycode: int) -> bool:
        """
        Send a key event.
        
        Common keycodes:
            - 4: BACK
            - 3: HOME
            - 82: MENU
            - 26: POWER
        
        Args:
            keycode: Android keycode
        
        Returns:
            True if successful
        """
        success, _ = self._run_adb("-s", self.address, "shell", "input", "keyevent", str(keycode))
        return success
    
    def press_back(self) -> bool:
        """Press the back button."""
        return self.key_event(4)
    
    def press_home(self) -> bool:
        """Press the home button."""
        return self.key_event(3)
    
    def shell(self, command: str, timeout: int = 30) -> Tuple[bool, str]:
        """
        Run a shell command on the device.
        
        Args:
            command: Shell command to execute
            timeout: Command timeout in seconds
        
        Returns:
            Tuple of (success, output/error message)
        """
        success, output = self._run_adb("-s", self.address, "shell", command, timeout=timeout)
        return success, output
    
    def input_text(self, text: str) -> bool:
        """
        Input text (for text fields).
        
        Args:
            text: Text to input (spaces replaced with %s)
        
        Returns:
            True if successful
        """
        # Escape special characters
        text = text.replace(" ", "%s").replace("&", "\\&").replace("<", "\\<").replace(">", "\\>")
        success, _ = self._run_adb("-s", self.address, "shell", "input", "text", text)
        return success
    
    def list_devices(self) -> list:
        """List all connected ADB devices."""
        success, output = self._run_adb("devices")
        devices = []
        if success:
            lines = output.strip().split("\n")[1:]  # Skip header
            for line in lines:
                if line.strip():
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        devices.append({"address": parts[0], "status": parts[1]})
        return devices


# Quick test
if __name__ == "__main__":
    from logger import setup_logger
    log = setup_logger("adb_test", "debug")
    
    adb = ADBController(port=5555, logger=log)
    print("Available devices:", adb.list_devices())
    
    if adb.connect():
        print("Resolution:", adb.get_screen_resolution())
        print("Taking screenshot...")
        img_data = adb.screencap()
        if img_data:
            with open("test_screenshot.png", "wb") as f:
                f.write(img_data)
            print("Screenshot saved!")
        adb.disconnect()

