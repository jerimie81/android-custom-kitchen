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
        Initialize the CommandRunner and its internal process, signals, and queue state.
        
        Creates an internal QProcess as this object's child, connects its stdout, stderr, and finished signals to the runner's handlers, and initializes the command queue, failure flag, and optional ADB-serial provider callback.
        
        Parameters:
            parent (Optional[QObject]): Optional Qt parent used for ownership; passed to QObject.__init__ and set as the parent of the internal QProcess.
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
        """
        Register a callback that supplies the ADB device serial for `adb` commands.
        
        Parameters:
            provider (Callable[[], str]): A no-argument callable that returns the ADB device serial string to inject with `-s` when preparing `adb` invocations.
        """
        self._adb_serial_provider = provider

    @property
    def running(self) -> bool:
        """
        Report whether the runner's internal process is currently active.
        
        Returns:
            True if the internal QProcess is running, False otherwise.
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
        Begin execution of the next queued CommandSpec or complete the run when the queue is empty.
        
        If the queue is empty, emits `finished(True)` when no prior command has failed or `finished(False)` otherwise. If a queued command fails preflight (i.e., `_prepare_command` returns `None`), marks the run as failed, clears the queue, emits a failure line, and emits `finished(False)`. For a prepared command, sets the process working directory to the command's `cwd` or the user's home directory, emits an informational line displaying the command, and starts the internal `QProcess` with the command's program and arguments.
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
        """
        Prepare an adb CommandSpec by ensuring a target device is selected and inserting the "-s <serial>" argument when needed.
        
        If the program is not an adb executable (by Path(cmd.program).stem) or the args already contain "-s", returns cmd unchanged. For adb without "-s", selects a single connected device: it uses the registered adb-serial provider if present (trimmed), or auto-selects when exactly one device is connected. Emits informational or failure messages via `line_out` when listing devices or when selection fails. On success returns a new CommandSpec whose args are ["-s", selected_serial, *original_args]; returns None if no device is connected, if multiple devices exist with no selection, or if the selected serial is not currently connected.
        
        Parameters:
            cmd (CommandSpec): The command to prepare.
        
        Returns:
            Optional[CommandSpec]: A new CommandSpec with "-s <serial>" injected on success, or `None` if preparation failed.
        """
        if Path(cmd.program).stem.lower() != "adb":
            return cmd
        if "-s" in cmd.args:
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
        return CommandSpec(program=cmd.program, args=["-s", selected, *cmd.args], cwd=cmd.cwd)

    @staticmethod
    def _quote(v: str) -> str:
        """
        Return a display-friendly string, quoting only when necessary.
        
        Parameters:
            v (str): Input string to format for display.
        
        Returns:
            str: The original string when it is non-empty and contains no whitespace or quote characters; otherwise the string's Python `repr` (quoted and escaped).
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