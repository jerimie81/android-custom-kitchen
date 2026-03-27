from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

from PyQt5.QtCore import QObject, QProcess, pyqtSignal

from .adb import list_adb_devices

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
        """
        Initialize the CommandRunner, create its internal QProcess, connect I/O and finish signals, and set up the command queue state.
        
        Parameters:
            parent (Optional[QObject]): Optional Qt parent for ownership; passed to QObject.__init__ and used as the parent of the internal QProcess.
        """
        super().__init__(parent)
        self._proc = QProcess(self)
        self._proc.readyReadStandardOutput.connect(self._on_stdout)
        self._proc.readyReadStandardError.connect(self._on_stderr)
        self._proc.finished.connect(self._on_finish)
        self._queue: list[CommandSpec] = []
        self._failed = False
        self._adb_serial_provider: Optional[Callable[[], str]] = None

    def set_adb_serial_provider(self, provider: Callable[[], str]):
        self._adb_serial_provider = provider

    @property
    def running(self) -> bool:
        """
        Indicates whether the internal QProcess is currently running.
        
        Returns:
            `True` if the internal process is running, `False` otherwise.
        """
        return self._proc.state() != QProcess.NotRunning

    def run_one(self, program: str, args: list[str], cwd: Optional[str] = None):
        """
        Run a single command with the runner using the provided program, arguments, and optional working directory.
        
        Parameters:
        	program (str): Executable name or path to run.
        	args (list[str]): Argument list passed to the process (argv-style; not joined into a shell command).
        	cwd (Optional[str]): Working directory for the command; if None the runner's default (typically the user's home) is used.
        """
        self.run_many([CommandSpec(program, args, cwd=cwd)])

    def run_many(self, commands: Iterable[CommandSpec]):
        """
        Enqueue multiple commands and begin executing them sequentially.
        
        If the runner is already active, emits a failure line and returns without changing the queue. Otherwise the given commands are stored (preserving order), the internal failure flag is reset, and processing begins: if the queue is empty `finished(True)` is emitted; otherwise `started()` is emitted and execution of the first command is started.
        
        Parameters:
            commands (Iterable[CommandSpec]): An iterable of CommandSpec instances to run in FIFO order.
        """
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
        """
        Stop any currently running command and mark the run as failed.
        
        If a process is running, clear the pending command queue, kill the subprocess, set the internal failure flag, and emit a user-facing failure line indicating the process was killed.
        """
        if self.running:
            self._queue.clear()
            self._proc.kill()
            self._failed = True
            self.line_out.emit("■  Process killed by user.", "fail")

    def _start_next(self):
        """
        Advance the queue by starting the next command or finish the run if none remain.
        
        If the internal command queue is empty, emits `finished(<success>)` where `<success>` reflects whether any prior command failed. Otherwise, removes the next CommandSpec from the queue, sets the process working directory (using the command's `cwd` or the user's home), emits a formatted informational line showing the command, and starts the `QProcess` with the command's program and arguments.
        """
        if not self._queue:
            self.finished.emit(not self._failed)
            return
        cmd = self._queue.pop(0)
        prepared = self._prepare_command(cmd)
        if prepared is None:
            self._failed = True
            self._queue.clear()
            self.line_out.emit("✖  Failed  (preflight)", "fail")
            self.finished.emit(False)
            return
        cmd = prepared
        self._proc.setWorkingDirectory(cmd.cwd or str(Path.home()))
        pretty = " ".join([cmd.program, *[self._quote(arg) for arg in cmd.args]])
        self.line_out.emit(f"$ {pretty}", "info")
        self._proc.start(cmd.program, cmd.args)

    def _prepare_command(self, cmd: CommandSpec) -> Optional[CommandSpec]:
        if Path(cmd.program).name != "adb":
            return cmd
        devices = [d for d in list_adb_devices(cmd.program) if d.state == "device"]
        if not devices:
            self.line_out.emit("✖  No ADB devices connected. Connect a device and refresh the selector.", "fail")
            return None
        connected = ", ".join(d.serial for d in devices)
        self.line_out.emit(f"ℹ  Connected ADB devices: {connected}", "info")
        selected = self._adb_serial_provider().strip() if self._adb_serial_provider else ""
        if not selected:
            if len(devices) == 1:
                selected = devices[0].serial
            else:
                self.line_out.emit("✖  Multiple ADB devices detected. Select a device from the combo box.", "fail")
                return None
        if selected not in {d.serial for d in devices}:
            self.line_out.emit(f"✖  Selected ADB device '{selected}' is not connected.", "fail")
            return None
        if "-s" in cmd.args:
            return cmd
        return CommandSpec(program=cmd.program, args=["-s", selected, *cmd.args], cwd=cmd.cwd)

    @staticmethod
    def _quote(v: str) -> str:
        """
        Render a string for safe display by quoting it only when necessary.
        
        Parameters:
            v (str): Input string to format for display.
        
        Returns:
            The original string if it contains no whitespace or quote characters and is not empty; otherwise the Python `repr` of the string (quoted and escaped).
        """
        if not v or any(ch in v for ch in " \t\n\"'"):
            return repr(v)
        return v

    def _on_stdout(self):
        """
        Read available standard output from the internal process, decode it as UTF-8 (replacing invalid bytes), split into lines, and emit each non-empty line via the `line_out` signal with category `"out"`.
        """
        raw = bytes(self._proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        for line in raw.splitlines():
            if line.strip():
                self.line_out.emit(line, "out")

    def _on_stderr(self):
        """
        Handle available standard-error data from the process and emit each non-empty decoded line with the "err" category.
        
        Reads any pending standard-error output from the internal QProcess, decodes it to text, splits into lines, and emits each non-blank line via the `line_out` signal with category `"err"`.
        """
        raw = bytes(self._proc.readAllStandardError()).decode("utf-8", errors="replace")
        for line in raw.splitlines():
            if line.strip():
                self.line_out.emit(line, "err")

    def _on_finish(self, code: int, _status):
        """
        Handle the QProcess finished event, update internal state, and either start the next queued command or emit final result signals.
        
        If `code` is non-zero the runner is marked as failed and pending commands are cleared. If `code` is zero and commands remain, the next command is started. When no more commands remain (or a failure occurred), emits a final status line and the `finished` signal indicating overall success.
        
        Parameters:
            code (int): The process exit code.
            _status: The QProcess exit status (unused).
        """
        ok = code == 0
        if not ok:
            self._failed = True
            self._queue.clear()
        if self._queue and ok:
            self._start_next()
            return
        self.line_out.emit("✔  Done  (exit 0)" if ok and not self._failed else f"✖  Failed  (exit {code})", "ok" if ok and not self._failed else "fail")
        self.finished.emit(ok and not self._failed)
