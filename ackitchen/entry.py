from __future__ import annotations

import sys


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] == "--cli":
        from .cli import run_cli

        return run_cli(argv[1:])

    try:
        from .app import main as run_gui
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("PyQt5"):
            print(
                "PyQt5 is required for GUI mode but is not installed.\n"
                "Install it with one of:\n"
                "  pip install PyQt5\n"
                "  sudo apt-get install python3-pyqt5",
                file=sys.stderr,
            )
            return 1
        raise

    return run_gui()
