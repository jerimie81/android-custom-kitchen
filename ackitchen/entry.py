from __future__ import annotations

import sys


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] == "--cli":
        from .cli import run_cli

        return run_cli(argv[1:])

    from .app import main as run_gui

    return run_gui()
