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
        """
        Create a FilePicker widget: a labeled input with a placeholder and a "Browse…" button for selecting files or directories.
        
        Parameters:
            label (str): Text for the top label describing the picker.
            placeholder (str): Placeholder text shown in the input field.
            mode (str): Selection mode, either "file" (default) for file selection or "dir" for directory selection.
            ffilter (str): File dialog filter string (e.g. "All Files (*)") used when selecting files.
            parent (Optional[QWidget]): Optional parent widget.
        
        Behavior:
            - The line edit's textChanged signal is forwarded to this widget's `changed` signal.
            - The "Browse…" button opens an appropriate file/directory/save dialog when clicked and updates the line edit with the chosen path.
        """
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
        """
        Open an appropriate file dialog (save, directory, or open) based on the widget configuration and update the line edit with the selected path.
        
        If the user selects a path, sets that path into the widget's line edit; otherwise leaves the current value unchanged.
        """
        if self._is_save:
            path, _ = QFileDialog.getSaveFileName(self, "Save As…", filter=self._filter)
        elif self._mode == "dir":
            path = QFileDialog.getExistingDirectory(self, "Select Directory")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Open File", filter=self._filter)
        if path:
            self.edit.setText(path)

    def value(self) -> str:
        """
        Get the current text from the picker's input, trimmed of leading and trailing whitespace.
        
        Returns:
            str: The input text with leading and trailing whitespace removed.
        """
        return self.edit.text().strip()


class SavePicker(FilePicker):
    def __init__(self, *args, **kwargs):
        """
        Initialize a FilePicker configured for saving files.
        
        Forwards all arguments to the base class initializer and sets an internal flag so the picker opens a save-file dialog instead of an open-file or directory dialog.
        """
        super().__init__(*args, **kwargs)
        self._is_save = True


def hline() -> QFrame:
    """
    Create a styled horizontal separator line.
    
    Returns:
        QFrame: A QFrame configured as a horizontal rule with the module's BORDER color and a maximum height of 1px.
    """
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setStyleSheet(f"background:{BORDER}; max-height:1px;")
    return f


def label(text: str, size: int = 13, color: str = TEXT, bold: bool = False) -> QLabel:
    """
    Create a QLabel with inline CSS for text color, font size, and optional bold weight.
    
    Parameters:
        text (str): The label text.
        size (int): Font size in pixels.
        color (str): CSS color value (e.g., '#rrggbb', 'red', or a Qt color constant).
        bold (bool): If True, applies bold font weight.
    
    Returns:
        QLabel: A QLabel instance styled with the specified color, font size, and weight.
    """
    w = QLabel(text)
    style = f"color:{color}; font-size:{size}px;"
    if bold:
        style += " font-weight:bold;"
    w.setStyleSheet(style)
    return w


def warn_box(text: str) -> QLabel:
    """
    Create a word-wrapping warning QLabel styled with orange text, padded background, and rounded border.
    
    Returns:
        QLabel: A configured warning label containing the provided text.
    """
    w = QLabel(text)
    w.setWordWrap(True)
    w.setStyleSheet(f"color:{ORANGE}; font-size:12px; padding:10px 12px; background:#1C1400; border:1px solid #4A3800; border-radius:7px;")
    return w


def info_box(text: str) -> QLabel:
    """
    Create a word-wrapping informational QLabel styled with a cyan color scheme.
    
    Parameters:
        text (str): The text to display inside the label.
    
    Returns:
        QLabel: A QLabel configured with word wrap and pre-applied cyan-themed styling.
    """
    w = QLabel(text)
    w.setWordWrap(True)
    w.setStyleSheet(f"color:{CYAN}; font-size:12px; padding:10px 12px; background:#071622; border:1px solid #1A3A55; border-radius:7px;")
    return w


_LOG_COLORS = {"out": "#9FB8CC", "err": ORANGE, "info": CYAN, "ok": GREEN, "fail": RED}


class LogPanel(QWidget):
    def __init__(self, runner, parent: Optional[QWidget] = None):
        """
        Create a LogPanel widget bound to a runner that displays color-coded output and provides start/stop/clear controls.
        
        Parameters:
            runner: An object that emits `line_out(str, str)` for lines (text, kind), `started` and `finished` signals, and exposes a `stop()` method; emitted lines are appended to the panel.
            parent (Optional[QWidget]): Optional Qt parent widget.
        """
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
        """
        Append a line of colored, HTML-escaped text to the panel's output area.
        
        The text is escaped for HTML, wrapped in a styled <span> that preserves spacing, appended to the internal text widget, and the cursor is moved to the end.
        
        Parameters:
            text (str): The message text to append.
            kind (str): Log kind determining display color; typically one of "out", "err", "info", "ok", "fail". Defaults to "out".
        """
        col = _LOG_COLORS.get(kind, _LOG_COLORS["out"])
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self._te.append(f'<span style="color:{col}; white-space:pre;">{safe}</span>')
        self._te.moveCursor(QTextCursor.End)

    def clear(self):
        """
        Clear the log display.
        
        Removes all text from the panel's internal read-only text area.
        """
        self._te.clear()

    def _on_start(self):
        """
        Show the indeterminate progress bar and enable the Stop button.
        
        This is invoked when the runner starts to indicate ongoing activity and allow the user to stop it.
        """
        self._prog.setVisible(True)
        self._stop_btn.setEnabled(True)

    def _on_finish(self, _ok: bool):
        """
        Handle runner finish by hiding the progress bar and disabling the Stop button.
        
        Parameters:
            _ok (bool): Indicates whether the runner finished successfully; this value is ignored.
        """
        self._prog.setVisible(False)
        self._stop_btn.setEnabled(False)


def tab_widget():
    """
    Create a container widget preconfigured for tab content with a vertical layout.
    
    Returns:
        w (QWidget), lay (QVBoxLayout): the container widget and its associated vertical layout. The layout has margins (left=22, top=20, right=22, bottom=20) and spacing 14.
    """
    from PyQt5.QtWidgets import QWidget, QVBoxLayout

    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(22, 20, 22, 20)
    lay.setSpacing(14)
    return w, lay


def run_row(run_label: str = "▶  Run", stop_label: str = "■  Stop"):
    """
    Create a horizontal row containing a primary "Run" button and a secondary "Stop" button.
    
    Parameters:
        run_label (str): Text for the primary run button.
        stop_label (str): Text for the secondary stop button (initially disabled).
    
    Returns:
        tuple: (row, run_button, stop_button) where `row` is a QHBoxLayout, `run_button` is the primary QPushButton, and `stop_button` is the secondary QPushButton.
    """
    row = QHBoxLayout()
    run = QPushButton(run_label)
    run.setObjectName("run")
    stop = QPushButton(stop_label)
    stop.setObjectName("stop")
    stop.setEnabled(False)
    row.addWidget(run, 3)
    row.addWidget(stop, 1)
    return row, run, stop
