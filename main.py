"""Launch the Car Wash PyQt5 application."""

import sys

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from gui import run_app

if __name__ == "__main__":
    run_app()
