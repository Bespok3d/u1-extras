import sys
from pathlib import Path

MOONRAKER = Path(__file__).resolve().parent.parent / "files" / "moonraker"
sys.path.insert(0, str(MOONRAKER))
