from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .styles import BG0, BG1, BORDER, CYAN, DIM, GREEN, MUTED, ORANGE, RED, TEXT


class FilePicker(QWidget):
    changed = pyqtSignal(str)

    def __init__(self, label: str, placeholder: str = "", mode: str = "file", ffilter: str = "All Files (*)", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._mode = mode
        self._filter = ffilter
        self._is_save = False
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(5)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color:{DIM}; font-size:12px;")
        v.addWidget(lbl)
        row = QHBoxLayout()
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.textChanged.connect(self.changed)
        row.addWidget(self.edit, 1)
        btn = QPushButton("Browse…")
        btn.setObjectName("browse")
        btn.setFixedWidth(84)
        btn.clicked.connect(self._browse)
        row.addWidget(btn)
        v.addLayout(row)

    def _browse(self):
        if self._is_save:
            path, _ = QFileDialog.getSaveFileName(self, "Save As…", filter=self._filter)
        elif self._mode == "dir":
            path = QFileDialog.getExistingDirectory(self, "Select Directory")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Open File", filter=self._filter)
        if path:
            self.edit.setText(path)

    def value(self) -> str:
        return self.edit.text().strip()


class SavePicker(FilePicker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_save = True


def hline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setStyleSheet(f"background:{BORDER}; max-height:1px;")
    return f


def label(text: str, size: int = 13, color: str = TEXT, bold: bool = False) -> QLabel:
    w = QLabel(text)
    style = f"color:{color}; font-size:{size}px;"
    if bold:
        style += " font-weight:bold;"
    w.setStyleSheet(style)
    return w


def warn_box(text: str) -> QLabel:
    w = QLabel(text)
    w.setWordWrap(True)
    w.setStyleSheet(f"color:{ORANGE}; font-size:12px; padding:10px 12px; background:#1C1400; border:1px solid #4A3800; border-radius:7px;")
    return w


def info_box(text: str) -> QLabel:
    w = QLabel(text)
    w.setWordWrap(True)
    w.setStyleSheet(f"color:{CYAN}; font-size:12px; padding:10px 12px; background:#071622; border:1px solid #1A3A55; border-radius:7px;")
    return w


_LOG_COLORS = {"out": "#9FB8CC", "err": ORANGE, "info": CYAN, "ok": GREEN, "fail": RED}


class LogPanel(QWidget):
    def __init__(self, runner, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._runner = runner
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)

        hdr = QWidget()
        hdr.setFixedHeight(36)
        hdr.setStyleSheet(f"background:{BG1}; border-top:1px solid {BORDER}; border-bottom:1px solid {BORDER};")
        hl = QHBoxLayout(hdr)
        dot = QLabel("●")
        dot.setObjectName("log_dot")
        dot.setStyleSheet(f"color:{MUTED};")
        hl.addWidget(dot)
        hl.addWidget(label("Terminal Output", 12, DIM))
        hl.addStretch()
        self._prog = QProgressBar()
        self._prog.setRange(0, 0)
        self._prog.setFixedSize(80, 5)
        self._prog.setVisible(False)
        hl.addWidget(self._prog)
        self._stop_btn = QPushButton("■  Stop")
        self._stop_btn.setObjectName("stop")
        self._stop_btn.setFixedSize(80, 26)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._runner.stop)
        hl.addWidget(self._stop_btn)
        clr = QPushButton("Clear")
        clr.setFixedSize(54, 26)
        clr.clicked.connect(self.clear)
        hl.addWidget(clr)
        main.addWidget(hdr)

        self._te = QTextEdit()
        self._te.setReadOnly(True)
        self._te.document().setMaximumBlockCount(6000)
        self._te.setStyleSheet(f"background:{BG0}; border:none;")
        main.addWidget(self._te, 1)

        self.append("Android Custom Kitchen v2.1 ready.", "ok")
        self.append(f"Workspace: {Path.home() / 'android-custom-kitchen'}", "info")

        runner.line_out.connect(self.append)
        runner.started.connect(self._on_start)
        runner.finished.connect(self._on_finish)

    def append(self, text: str, kind: str = "out"):
        col = _LOG_COLORS.get(kind, _LOG_COLORS["out"])
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self._te.append(f'<span style="color:{col}; white-space:pre;">{safe}</span>')
        self._te.moveCursor(QTextCursor.End)

    def clear(self):
        self._te.clear()

    def _on_start(self):
        self._prog.setVisible(True)
        self._stop_btn.setEnabled(True)

    def _on_finish(self, _ok: bool):
        self._prog.setVisible(False)
        self._stop_btn.setEnabled(False)


def tab_widget():
    from PyQt5.QtWidgets import QWidget, QVBoxLayout

    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(22, 20, 22, 20)
    lay.setSpacing(14)
    return w, lay


def run_row(run_label: str = "▶  Run", stop_label: str = "■  Stop"):
    row = QHBoxLayout()
    run = QPushButton(run_label)
    run.setObjectName("run")
    stop = QPushButton(stop_label)
    stop.setObjectName("stop")
    stop.setEnabled(False)
    row.addWidget(run, 3)
    row.addWidget(stop, 1)
    return row, run, stop
