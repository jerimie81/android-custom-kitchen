from __future__ import annotations

import pytest

import ackitchen.runner as runner_mod
from ackitchen.runner import CommandRunner, CommandSpec


class FakeSignal:
    def __init__(self):
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def emit(self, *args, **kwargs):
        for cb in list(self._callbacks):
            cb(*args, **kwargs)


class FakeQProcess:
    NotRunning = 0
    Running = 1

    def __init__(self, _parent=None):
        self.readyReadStandardOutput = FakeSignal()
        self.readyReadStandardError = FakeSignal()
        self.finished = FakeSignal()
        self._state = self.NotRunning
        self._cwd = None
        self.start_calls: list[tuple[str, list[str]]] = []
        self.killed = False

    def state(self):
        return self._state

    def setWorkingDirectory(self, cwd):
        self._cwd = cwd

    def start(self, program, args):
        self.start_calls.append((program, list(args)))
        self._state = self.Running

    def kill(self):
        self.killed = True
        self._state = self.NotRunning

    def finish(self, exit_code, exit_status=0):
        self._state = self.NotRunning
        self.finished.emit(exit_code, exit_status)


@pytest.fixture
def fake_qprocess(monkeypatch):
    monkeypatch.setattr(runner_mod, "QProcess", FakeQProcess)


@pytest.fixture
def capture_signals():
    class Bag:
        def __init__(self):
            self.lines = []
            self.started_count = 0
            self.finished = []

    return Bag()


def test_run_many_sequences_commands_in_order(fake_qprocess, capture_signals):
    runner = CommandRunner()
    runner.line_out.connect(lambda line, kind: capture_signals.lines.append((line, kind)))
    runner.started.connect(lambda: setattr(capture_signals, "started_count", capture_signals.started_count + 1))
    runner.finished.connect(lambda ok: capture_signals.finished.append(ok))

    runner.run_many(
        [
            CommandSpec("cmd1", ["a"]),
            CommandSpec("cmd2", ["b", "c"]),
        ]
    )

    assert runner._proc.start_calls == [("cmd1", ["a"])]
    assert capture_signals.started_count == 1

    runner._proc.finish(0)
    assert runner._proc.start_calls == [("cmd1", ["a"]), ("cmd2", ["b", "c"])]

    runner._proc.finish(0)
    assert capture_signals.finished == [True]
    assert any(line == "✔  Done  (exit 0)" and kind == "ok" for line, kind in capture_signals.lines)


def test_nonzero_exit_stops_queue_and_propagates_failure(fake_qprocess, capture_signals):
    runner = CommandRunner()
    runner.line_out.connect(lambda line, kind: capture_signals.lines.append((line, kind)))
    runner.finished.connect(lambda ok: capture_signals.finished.append(ok))

    runner.run_many([CommandSpec("cmd1", []), CommandSpec("cmd2", [])])
    assert runner._proc.start_calls == [("cmd1", [])]

    runner._proc.finish(3)

    assert runner._proc.start_calls == [("cmd1", [])]
    assert capture_signals.finished == [False]
    assert runner._failed is True
    assert any(line == "✖  Failed  (exit 3)" and kind == "fail" for line, kind in capture_signals.lines)


def test_stop_kills_process_and_marks_failed(fake_qprocess, capture_signals):
    runner = CommandRunner()
    runner.line_out.connect(lambda line, kind: capture_signals.lines.append((line, kind)))
    runner.finished.connect(lambda ok: capture_signals.finished.append(ok))

    runner.run_many([CommandSpec("cmd1", []), CommandSpec("cmd2", [])])
    runner.stop()

    assert runner._proc.killed is True
    assert runner._failed is True
    assert runner._queue == []
    assert any(line == "■  Process killed by user." and kind == "fail" for line, kind in capture_signals.lines)

    runner._proc.finish(9)
    assert capture_signals.finished == [False]
