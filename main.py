#!/usr/bin/env python3
"""
main.py – Entry point for Resume Optimizer Pro.

Usage:
    python main.py
"""

import sys


def main() -> None:
    # Verify Python version
    if sys.version_info < (3, 9):
        print(
            "Resume Optimizer Pro requires Python 3.9 or later.\n"
            f"You are running Python {sys.version}.\n"
            "Please upgrade Python and try again.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        import tkinter as tk
    except ImportError:
        print(
            "tkinter is not available on this Python installation.\n\n"
            "macOS:   brew install python-tk  (or reinstall Python from python.org)\n"
            "Ubuntu:  sudo apt install python3-tk\n"
            "Windows: tkinter is included with standard Python installers.",
            file=sys.stderr,
        )
        sys.exit(1)

    from app.gui import ResumeOptimizerApp

    root = tk.Tk()
    app = ResumeOptimizerApp(root)  # noqa: F841
    root.mainloop()


if __name__ == "__main__":
    main()
