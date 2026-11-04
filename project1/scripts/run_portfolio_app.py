"""Launch the Streamlit portfolio application."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def main() -> None:
    app = Path(__file__).resolve().parents[2] / "streamlit_app.py"
    raise SystemExit(subprocess.call([sys.executable, "-m", "streamlit", "run", str(app), *sys.argv[1:]]))


if __name__ == "__main__":
    main()
