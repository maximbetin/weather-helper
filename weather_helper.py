"""
Entry point for running the Weather Helper GUI application.
"""

from src.gui.app import main
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
  sys.path.append(project_root)


if __name__ == "__main__":
  main()
