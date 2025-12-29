# GUI modules
import sys
from pathlib import Path

# Add parent directory to path for imports
_parent_dir = str(Path(__file__).parent.parent)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from gui.launcher import BotLauncher

__all__ = ['BotLauncher']

