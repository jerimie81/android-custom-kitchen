from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from PyQt5.QtCore import QObject, QProcess, pyqtSignal


@dataclass
class CommandSpec:
    program: str
    args: list[str]
    cwd: Optional[str] = None


class CommandRunner(QObject):
    """QProcess runner using argv (no shell) to avoid command injection."""

    line_out = pyqtSignal(str, str)
    started = pyqtSignal()
    finished = pyqtSignal(bool)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._proc = QProcess(self)
        self._proc.readyReadStandardOutput.connect(self._on_stdout)
        self._proc.readyReadStandardError.connect(self._on_stderr)
        self._proc.finished.connect(self._on_finish)
        self._queue: list[CommandSpec] = []
        self._failed = False

    @property
    def running(self) -> bool:
        return self._proc.state() != QProcess.NotRunning

    def run_one(self, program: str, args: list[str], cwd: Optional[str] = None):
        self.run_many([CommandSpec(program, args, cwd=cwd)])

    def run_many(self, commands: Iterable[CommandSpec]):
        if self.running:
            self.line_out.emit("⚠  Another operation is already running.", "fail")
            return
        self._queue = list(commands)
        self._failed = False
        if not self._queue:
            self.finished.emit(True)
            return
        self.started.emit()
        self._start_next()

    def stop(self):
        if self.running:
            self._queue.clear()
            self._proc.kill()
            self._failed = True
            self.line_out.emit("■  Process killed by user.", "fail")

    def _start_next(self):
        if not self._queue:
            self.finished.emit(not self._failed)
            return
        cmd = self._queue.pop(0)
        self._proc.setWorkingDirectory(cmd.cwd or str(Path.home()))
        pretty = " ".join([cmd.program, *[self._quote(arg) for arg in cmd.args]])
        self.line_out.emit(f"$ {pretty}", "info")
        self._proc.start(cmd.program, cmd.args)

    @staticmethod
    def _quote(v: str) -> str:
        if not v or any(ch in v for ch in " \t\n\"'"):
            return repr(v)
        return v

    def _on_stdout(self):
        raw = bytes(self._proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        for line in raw.splitlines():
            if line.strip():
                self.line_out.emit(line, "out")

    def _on_stderr(self):
        raw = bytes(self._proc.readAllStandardError()).decode("utf-8", errors="replace")
        for line in raw.splitlines():
            if line.strip():
                self.line_out.emit(line, "err")

    def _on_finish(self, code: int, _status):
        ok = code == 0
        if not ok:
            self._failed = True
            self._queue.clear()
        if self._queue and ok:
            self._start_next()
            return
        self.line_out.emit("✔  Done  (exit 0)" if ok and not self._failed else f"✖  Failed  (exit {code})", "ok" if ok and not self._failed else "fail")
        self.finished.emit(ok and not self._failed)
