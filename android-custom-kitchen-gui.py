#!/usr/bin/env python3
"""
Android Custom Kitchen v2.0
Professional GUI — Debian/Ubuntu — PyQt5

Install deps:  sudo apt-get install python3-pyqt5
Run:           python3 android_custom_kitchen_gui.py
"""

import sys
import shutil
from pathlib import Path
from typing import List, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QTextEdit, QLineEdit,
    QFileDialog, QCheckBox, QFrame, QScrollArea, QGridLayout,
    QSplitter, QTabWidget, QGroupBox, QSizePolicy, QStatusBar,
    QProgressBar, QSpacerItem,
)
from PyQt5.QtCore import Qt, QProcess, pyqtSignal, QTimer, QObject
from PyQt5.QtGui import QFont, QTextCursor, QFontDatabase, QColor


# ══════════════════════════════════════════════════════════════════════════════
#  PALETTE
# ══════════════════════════════════════════════════════════════════════════════
BG0    = "#090F17"      # Deepest — window base
BG1    = "#0E1620"      # Panels, sidebar
BG2    = "#141D2B"      # Cards, inputs
BG3    = "#1C2736"      # Hover states
BG4    = "#243044"      # Active / selected

GREEN  = "#3DDC84"      # Android signature green
GDIM   = "#1A5C3A"      # Dark green for button bg
GFADE  = "#0D3020"      # Very dim green bg

CYAN   = "#4FC3F7"      # Secondary accent
BLUE   = "#5B8AF5"

TEXT   = "#DDE6F0"      # Primary text
DIM    = "#7A94AA"      # Secondary text
MUTED  = "#3A5068"      # Disabled / placeholder

RED    = "#FF4757"
ORANGE = "#FFB74D"
OK     = "#43E97B"

BORDER = "#1E2D3D"
SHADOW = "#060C12"


# ══════════════════════════════════════════════════════════════════════════════
#  GLOBAL STYLESHEET
# ══════════════════════════════════════════════════════════════════════════════
def _ss() -> str:
    return f"""
/* ── Base ─────────────────────────────────────────────────────────────── */
* {{
    font-family: 'Ubuntu', 'Noto Sans', 'DejaVu Sans', sans-serif;
    font-size: 13px;
    outline: none;
}}
QWidget {{
    background: {BG0};
    color: {TEXT};
    border: none;
}}
QLabel {{ background: transparent; }}

/* ── Inputs ────────────────────────────────────────────────────────────── */
QLineEdit {{
    background: {BG2};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 8px 11px;
    selection-background-color: {GDIM};
}}
QLineEdit:focus {{ border-color: {GREEN}; background: {BG3}; }}
QLineEdit:disabled {{ color: {MUTED}; }}

QTextEdit {{
    background: {BG1};
    color: #9FB8CC;
    border: 1px solid {BORDER};
    border-radius: 6px;
    font-family: 'JetBrains Mono', 'Cascadia Mono', 'Fira Code', 'Courier New', monospace;
    font-size: 12px;
    selection-background-color: {GDIM};
}}

QCheckBox {{ spacing: 9px; color: {TEXT}; }}
QCheckBox::indicator {{
    width: 17px; height: 17px;
    border: 1px solid {BORDER};
    border-radius: 4px;
    background: {BG2};
}}
QCheckBox::indicator:hover {{ border-color: {GREEN}; }}
QCheckBox::indicator:checked {{
    background: {GDIM};
    border-color: {GREEN};
    image: none;
}}
QCheckBox::indicator:checked:hover {{ background: {GREEN}; }}

/* ── Buttons ────────────────────────────────────────────────────────────── */
QPushButton {{
    background: {BG3};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 8px 16px;
    min-height: 32px;
}}
QPushButton:hover  {{ background: {BG4}; border-color: {GREEN}; color: {TEXT}; }}
QPushButton:pressed {{ background: {BG1}; }}
QPushButton:disabled {{ color: {MUTED}; border-color: {MUTED}; background: {BG2}; }}

/* Primary RUN button */
QPushButton#run {{
    background: {GDIM};
    color: #FFFFFF;
    border: 1px solid {GREEN};
    font-weight: bold;
    font-size: 14px;
    min-height: 42px;
    border-radius: 8px;
    letter-spacing: 0.5px;
}}
QPushButton#run:hover {{ background: {GREEN}; color: {BG0}; }}
QPushButton#run:disabled {{
    background: {BG2}; color: {MUTED}; border-color: {MUTED};
}}

/* STOP button */
QPushButton#stop {{
    background: #2A1015;
    color: {RED};
    border: 1px solid {RED};
    font-weight: bold;
    font-size: 14px;
    min-height: 42px;
    border-radius: 8px;
}}
QPushButton#stop:hover {{ background: {RED}; color: #fff; }}
QPushButton#stop:disabled {{ color: {MUTED}; border-color: {MUTED}; background: {BG2}; }}

/* Browse button */
QPushButton#browse {{
    background: {BG2};
    color: {DIM};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 7px 14px;
    min-height: 0;
}}
QPushButton#browse:hover {{ color: {GREEN}; border-color: {GREEN}; background: {GFADE}; }}

/* Sidebar NAV buttons */
QPushButton#nav {{
    background: transparent;
    color: {DIM};
    text-align: left;
    border: none;
    border-radius: 0;
    padding: 11px 20px 11px 18px;
    font-size: 14px;
    min-height: 44px;
}}
QPushButton#nav:hover {{
    background: {BG3};
    color: {TEXT};
}}
QPushButton#nav_on {{
    background: {GFADE};
    color: {GREEN};
    text-align: left;
    border: none;
    border-left: 3px solid {GREEN};
    padding: 11px 20px 11px 15px;
    font-size: 14px;
    min-height: 44px;
    font-weight: bold;
}}

/* Quick action cards */
QPushButton#qcard {{
    background: {BG2};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 18px 16px;
    min-height: 80px;
    text-align: left;
    font-size: 13px;
    color: {TEXT};
}}
QPushButton#qcard:hover {{
    border-color: {GREEN};
    background: {BG3};
}}

/* ── Scrollbars ─────────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent; width: 7px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER}; border-radius: 3px; min-height: 22px;
}}
QScrollBar::handle:vertical:hover {{ background: {MUTED}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent; height: 7px; margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER}; border-radius: 3px; min-width: 22px;
}}
QScrollBar::handle:horizontal:hover {{ background: {MUTED}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── GroupBox ────────────────────────────────────────────────────────────── */
QGroupBox {{
    background: {BG1};
    border: 1px solid {BORDER};
    border-radius: 9px;
    margin-top: 18px;
    padding: 14px 12px 12px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 2px 9px;
    color: {GREEN};
    font-weight: bold;
    font-size: 12px;
    background: {BG1};
    border-radius: 4px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 0 9px 9px 9px;
    background: {BG1};
    top: -1px;
}}
QTabBar::tab {{
    background: {BG0};
    color: {DIM};
    padding: 9px 20px;
    border: 1px solid {BORDER};
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    margin-right: 3px;
    font-size: 13px;
}}
QTabBar::tab:selected {{
    background: {BG1};
    color: {TEXT};
    border-bottom: 2px solid {GREEN};
}}
QTabBar::tab:!selected:hover {{ background: {BG2}; color: {TEXT}; }}

/* ── Splitter ────────────────────────────────────────────────────────────── */
QSplitter::handle:vertical   {{ background: {BORDER}; height: 1px; }}
QSplitter::handle:horizontal {{ background: {BORDER}; width: 1px;  }}

/* ── Status bar ──────────────────────────────────────────────────────────── */
QStatusBar {{
    background: {BG1};
    color: {DIM};
    border-top: 1px solid {BORDER};
    font-size: 12px;
    padding-left: 4px;
}}

/* ── Progress bar ────────────────────────────────────────────────────────── */
QProgressBar {{
    background: {BG3};
    border: none;
    border-radius: 3px;
    height: 5px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{ background: {GREEN}; border-radius: 3px; }}
"""


# ══════════════════════════════════════════════════════════════════════════════
#  COMMAND RUNNER — wraps QProcess for real-time streaming output
# ══════════════════════════════════════════════════════════════════════════════
class CommandRunner(QObject):
    """Single shared QProcess wrapper. Emits real-time output lines."""
    line_out = pyqtSignal(str, str)   # (text, kind)  kind ∈ {out, err, info, ok, fail}
    started  = pyqtSignal()
    finished = pyqtSignal(bool)       # True = success

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._proc = QProcess(self)
        self._proc.readyReadStandardOutput.connect(self._on_stdout)
        self._proc.readyReadStandardError.connect(self._on_stderr)
        self._proc.finished.connect(self._on_finish)

    @property
    def running(self) -> bool:
        return self._proc.state() != QProcess.NotRunning

    def run(self, cmd: str, cwd: Optional[str] = None):
        if self.running:
            self.line_out.emit("⚠  Another operation is already running.", "fail")
            return
        self._proc.setWorkingDirectory(cwd or str(Path.home()))
        self.line_out.emit(f"$ {cmd}", "info")
        self.started.emit()
        self._proc.start("bash", ["-c", cmd])

    def stop(self):
        if self.running:
            self._proc.kill()
            self.line_out.emit("■  Process killed by user.", "fail")

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
        ok = (code == 0)
        if ok:
            self.line_out.emit(f"✔  Done  (exit 0)", "ok")
        else:
            self.line_out.emit(f"✖  Failed  (exit {code})", "fail")
        self.finished.emit(ok)


# ══════════════════════════════════════════════════════════════════════════════
#  REUSABLE HELPER WIDGETS
# ══════════════════════════════════════════════════════════════════════════════
class FilePicker(QWidget):
    """Labelled QLineEdit + Browse button combo."""
    changed = pyqtSignal(str)

    def __init__(self, label: str, placeholder: str = "",
                 mode: str = "file",
                 ffilter: str = "All Files (*)",
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._mode    = mode
        self._filter  = ffilter
        self._is_save = False

        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(5)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color:{DIM}; font-size:12px; letter-spacing:0.3px;")
        v.addWidget(lbl)

        row = QHBoxLayout()
        row.setSpacing(6)
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

    def set_value(self, v: str):
        self.edit.setText(v)


class SavePicker(FilePicker):
    """FilePicker variant that uses getSaveFileName."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_save = True


def _hline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setStyleSheet(f"background:{BORDER}; max-height:1px;")
    return f


def _lbl(text: str, size: int = 13, color: str = TEXT, bold: bool = False) -> QLabel:
    w = QLabel(text)
    style = f"color:{color}; font-size:{size}px;"
    if bold:
        style += " font-weight:bold;"
    w.setStyleSheet(style)
    return w


def _warn_box(text: str) -> QLabel:
    w = QLabel(text)
    w.setWordWrap(True)
    w.setStyleSheet(
        f"color:{ORANGE}; font-size:12px; padding:10px 12px; "
        f"background:#1C1400; border:1px solid #4A3800; border-radius:7px;"
    )
    return w


def _info_box(text: str) -> QLabel:
    w = QLabel(text)
    w.setWordWrap(True)
    w.setStyleSheet(
        f"color:{CYAN}; font-size:12px; padding:10px 12px; "
        f"background:#071622; border:1px solid #1A3A55; border-radius:7px;"
    )
    return w


# ══════════════════════════════════════════════════════════════════════════════
#  LOG PANEL — terminal-style streaming output
# ══════════════════════════════════════════════════════════════════════════════
_LOG_COLORS = {
    "out":  "#9FB8CC",
    "err":  ORANGE,
    "info": CYAN,
    "ok":   GREEN,
    "fail": RED,
}


class LogPanel(QWidget):
    def __init__(self, runner: "CommandRunner", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._runner = runner
        self._build()
        runner.line_out.connect(self.append)
        runner.started.connect(self._on_start)
        runner.finished.connect(self._on_finish)

    def _build(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # Header bar
        hdr = QWidget()
        hdr.setFixedHeight(36)
        hdr.setStyleSheet(
            f"background:{BG1}; border-top:1px solid {BORDER}; border-bottom:1px solid {BORDER};"
        )
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(14, 0, 10, 0)

        dot = QLabel("●")
        dot.setObjectName("log_dot")
        dot.setStyleSheet(f"color:{MUTED}; font-size:11px;")
        hl.addWidget(dot)
        hl.addSpacing(6)

        hl.addWidget(_lbl("Terminal Output", 12, DIM))
        hl.addStretch()

        self._prog = QProgressBar()
        self._prog.setRange(0, 0)
        self._prog.setFixedSize(80, 5)
        self._prog.setVisible(False)
        hl.addWidget(self._prog)
        hl.addSpacing(8)

        self._stop_btn = QPushButton("■  Stop")
        self._stop_btn.setObjectName("stop")
        self._stop_btn.setFixedSize(80, 26)
        self._stop_btn.setStyleSheet(
            f"font-size:11px; min-height:0; padding:3px 8px;"
            f"background:#2A1015; color:{RED}; border:1px solid {RED}; border-radius:5px;"
        )
        self._stop_btn.setEnabled(False)
        # Use the instance runner so the signal is bound correctly
        self._stop_btn.clicked.connect(self._runner.stop)
        hl.addWidget(self._stop_btn)
        hl.addSpacing(4)

        clr = QPushButton("Clear")
        clr.setFixedSize(54, 26)
        clr.setStyleSheet(
            f"font-size:11px; min-height:0; padding:3px 8px;"
        )
        clr.clicked.connect(self.clear)
        hl.addWidget(clr)

        main.addWidget(hdr)

        # Terminal text area
        self._te = QTextEdit()
        self._te.setReadOnly(True)
        self._te.document().setMaximumBlockCount(6000)
        self._te.setStyleSheet(
            f"background:{BG0}; border:none; border-radius:0; font-size:12px; padding:6px 4px;"
        )
        main.addWidget(self._te, 1)

        # Green "ready" prompt on startup
        self.append("Android Custom Kitchen v2.0 ready.", "ok")
        self.append(f"Workspace: {Path.home() / 'android-custom-kitchen'}", "info")

    def append(self, text: str, kind: str = "out"):
        col  = _LOG_COLORS.get(kind, _LOG_COLORS["out"])
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self._te.append(f'<span style="color:{col}; white-space:pre;">{safe}</span>')
        self._te.moveCursor(QTextCursor.End)

    def clear(self):
        self._te.clear()

    def _on_start(self):
        self._prog.setVisible(True)
        self._stop_btn.setEnabled(True)
        self._update_dot(active=True)

    def _on_finish(self, ok: bool):
        self._prog.setVisible(False)
        self._stop_btn.setEnabled(False)
        self._update_dot(active=False)

    def _update_dot(self, active: bool):
        dot = self.findChild(QLabel, "log_dot")
        if dot:
            dot.setStyleSheet(
                f"color:{GREEN}; font-size:11px;" if active
                else f"color:{MUTED}; font-size:11px;"
            )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE BASE — common page skeleton with scrollable body
# ══════════════════════════════════════════════════════════════════════════════
class PageBase(QWidget):
    def __init__(self, title: str, subtitle: str,
                 runner: CommandRunner, log: LogPanel,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.runner = runner
        self.log    = log

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Page title bar
        hdr = QWidget()
        hdr.setFixedHeight(62)
        hdr.setStyleSheet(
            f"background:{BG1}; border-bottom:1px solid {BORDER};"
        )
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(26, 0, 26, 0)
        tl = QLabel(title)
        tl.setStyleSheet(f"font-size:19px; font-weight:bold; color:{TEXT};")
        hl.addWidget(tl)
        hl.addSpacing(14)
        sl = QLabel(subtitle)
        sl.setStyleSheet(f"color:{MUTED}; font-size:12px;")
        hl.addWidget(sl, 1)
        outer.addWidget(hdr)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.body = QWidget()
        self.bl   = QVBoxLayout(self.body)
        self.bl.setContentsMargins(26, 22, 26, 26)
        self.bl.setSpacing(16)
        scroll.setWidget(self.body)
        outer.addWidget(scroll, 1)

    def _register_run(self, btn: QPushButton):
        """Disable/re-enable a run button while any operation is active."""
        self.runner.started.connect(lambda: btn.setEnabled(False))
        self.runner.finished.connect(lambda ok: btn.setEnabled(True))

    def _exec(self, cmd: str):
        self.runner.run(cmd)


# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD PAGE
# ══════════════════════════════════════════════════════════════════════════════
TOOL_REGISTRY = [
    ("apktool",           "APK Decompile",   "Smali + resources"),
    ("jadx",              "Java Decompile",  "Java / Kotlin source"),
    ("apksigner",         "APK Signing",     "v2 + v3 signing"),
    ("adb",               "ADB",             "Android Debug Bridge"),
    ("fastboot",          "Fastboot",        "Bootloader flash"),
    ("payload-dumper-go", "OTA Extractor",   "payload.bin → images"),
    ("lpunpack",          "Super Unpack",    "Dynamic partitions"),
    ("lpmake",            "Super Repack",    "lpmake packer"),
    ("mkbootimg",         "Boot Repack",     "AOSP mkbootimg"),
    ("unpack_bootimg",    "Boot Unpack",     "AOSP unpack_bootimg"),
    ("fsck.erofs",        "EROFS Extract",   "Android 12+ FS"),
    ("avbtool",           "AVB Signing",     "Verified Boot 2.0"),
]


class DashboardPage(PageBase):
    navigate = pyqtSignal(int)

    def __init__(self, runner: CommandRunner, log: LogPanel,
                 parent: Optional[QWidget] = None):
        super().__init__(
            "Dashboard",
            "Tool status and quick-access workflows",
            runner, log, parent,
        )
        self._cards: dict = {}
        self._build()

    def _build(self):
        # ── Welcome banner ────────────────────────────────────────────────────
        banner = QWidget()
        banner.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {GFADE}, stop:1 {BG1});"
            f"border:1px solid {GDIM}; border-radius:10px; padding:4px;"
        )
        bl = QHBoxLayout(banner)
        bl.setContentsMargins(20, 16, 20, 16)
        txt = QVBoxLayout()
        txt.setSpacing(4)
        t1 = QLabel("Android Custom Kitchen")
        t1.setStyleSheet(f"font-size:18px; font-weight:bold; color:{GREEN};")
        t2 = QLabel("Firmware & APK Engineering Suite  ·  All tools in one place")
        t2.setStyleSheet(f"font-size:13px; color:{DIM};")
        txt.addWidget(t1)
        txt.addWidget(t2)
        bl.addLayout(txt)
        bl.addStretch()
        icon = QLabel("🍳")
        icon.setStyleSheet("font-size:36px;")
        bl.addWidget(icon)
        self.bl.addWidget(banner)

        # ── Tool Status grid ──────────────────────────────────────────────────
        status_box = QGroupBox("Installed Tools")
        grid = QGridLayout(status_box)
        grid.setSpacing(8)
        grid.setContentsMargins(12, 16, 12, 12)

        for i, (cmd, name, desc) in enumerate(TOOL_REGISTRY):
            card = self._make_card(cmd, name, desc)
            self._cards[cmd] = card
            grid.addWidget(card, i // 3, i % 3)

        self.bl.addWidget(status_box)

        ref_btn = QPushButton("⟳  Refresh Status")
        ref_btn.setFixedWidth(160)
        ref_btn.setStyleSheet(f"font-size:12px; padding:5px 12px; min-height:0;")
        ref_btn.clicked.connect(self._refresh)
        self.bl.addWidget(ref_btn, alignment=Qt.AlignLeft)

        # ── Quick Actions ─────────────────────────────────────────────────────
        qa_box = QGroupBox("Quick Actions")
        qa_lay = QHBoxLayout(qa_box)
        qa_lay.setSpacing(10)

        actions = [
            ("📦", "Decompile APK",    "apktool + optional JADX", 1),
            ("💾", "Extract OTA",      "payload.bin → images",    2),
            ("🥾", "Unpack Boot",      "kernel + ramdisk + DTB",  2),
            ("⚙️", "Setup / Install",  "Install all prerequisites", 3),
        ]
        for emoji, title, sub, page in actions:
            btn = QPushButton()
            btn.setObjectName("qcard")
            btn.setText(f"{emoji}  {title}\n      {sub}")
            btn.clicked.connect(lambda _, p=page: self.navigate.emit(p))
            qa_lay.addWidget(btn)

        self.bl.addWidget(qa_box)
        self.bl.addStretch()
        self._refresh()

    def _make_card(self, cmd: str, name: str, desc: str) -> QWidget:
        card = QWidget()
        card.setObjectName(f"card_{cmd}")
        card.setStyleSheet(
            f"QWidget {{ background:{BG2}; border:1px solid {BORDER}; border-radius:8px; }}"
        )
        lay = QHBoxLayout(card)
        lay.setContentsMargins(10, 9, 10, 9)
        lay.setSpacing(10)

        dot = QLabel("●")
        dot.setObjectName(f"dot_{cmd}")
        dot.setStyleSheet(f"color:{MUTED}; font-size:14px;")
        lay.addWidget(dot)

        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(_lbl(name, 12, TEXT, bold=True))
        col.addWidget(_lbl(desc, 11, MUTED))
        lay.addLayout(col, 1)

        return card

    def _refresh(self):
        for cmd, _, _ in TOOL_REGISTRY:
            found = bool(shutil.which(cmd))
            card  = self._cards.get(cmd)
            if not card:
                continue
            dot = card.findChild(QLabel, f"dot_{cmd}")
            if dot:
                dot.setStyleSheet(
                    f"color:{GREEN}; font-size:14px;" if found
                    else f"color:{RED}; font-size:14px;"
                )
            border_color = GDIM if found else "#3D1010"
            card.setStyleSheet(
                f"QWidget {{ background:{BG2}; border:1px solid {border_color}; border-radius:8px; }}"
            )


# ══════════════════════════════════════════════════════════════════════════════
#  APK PAGE
# ══════════════════════════════════════════════════════════════════════════════
class APKPage(PageBase):
    def __init__(self, runner: CommandRunner, log: LogPanel,
                 parent: Optional[QWidget] = None):
        super().__init__("APK Tools", "Decompile · Rebuild · Sign", runner, log, parent)
        tabs = QTabWidget()
        tabs.addTab(self._decompile_tab(), "  Decompile  ")
        tabs.addTab(self._rebuild_tab(),   "  Rebuild    ")
        tabs.addTab(self._sign_tab(),      "  Sign       ")
        self.bl.addWidget(tabs)
        self.bl.addStretch()

    # ── Decompile ─────────────────────────────────────────────────────────────
    def _decompile_tab(self) -> QWidget:
        w, v = _tab_widget()

        v.addWidget(_lbl("Decompile APK", 15, TEXT, bold=True))
        v.addWidget(_lbl(
            "Extract Smali bytecode, resources, AndroidManifest.xml and layouts via apktool.\n"
            "Optionally run JADX to produce readable Java / Kotlin source alongside.",
            12, DIM))
        v.addWidget(_hline())

        self.dc_apk  = FilePicker("APK File", "/path/to/app.apk",
                                   ffilter="APK Files (*.apk);;All Files (*)")
        self.dc_out  = FilePicker("Output Directory", "/path/to/output", mode="dir")
        self.dc_jadx = QCheckBox("  Also decompile Java/Kotlin source with JADX  (slower)")

        v.addWidget(self.dc_apk)
        v.addWidget(self.dc_out)
        v.addSpacing(4)
        v.addWidget(self.dc_jadx)
        v.addSpacing(8)

        v.addWidget(_info_box(
            "apktool d  flags used:  --force (overwrite)   --no-res is skipped so resources decode."
        ))

        row, run, stop = _run_row("▶  Run Decompile")
        run.clicked.connect(self._do_decompile)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        v.addLayout(row)
        v.addStretch()
        return w

    def _do_decompile(self):
        apk = self.dc_apk.value()
        out = self.dc_out.value()
        if not apk or not out:
            self.log.append("✖  APK path and output directory are required.", "fail")
            return
        cmd = f"apktool d '{apk}' -o '{out}' --force"
        if self.dc_jadx.isChecked():
            jadx_out = f"{out}/jadx_sources"
            cmd += f" && jadx -d '{jadx_out}' --deobf '{apk}'"
        self._exec(cmd)

    # ── Rebuild ───────────────────────────────────────────────────────────────
    def _rebuild_tab(self) -> QWidget:
        w, v = _tab_widget()

        v.addWidget(_lbl("Rebuild APK", 15, TEXT, bold=True))
        v.addWidget(_lbl(
            "Recompile modified Smali, resources and manifest back into a signed-ready .apk.",
            12, DIM))
        v.addWidget(_hline())

        self.rb_dir = FilePicker("Decompiled Directory", "/path/to/decompiled", mode="dir")
        self.rb_out = SavePicker("Output APK Path", "app-modified.apk",
                                  ffilter="APK Files (*.apk);;All Files (*)")
        v.addWidget(self.rb_dir)
        v.addWidget(self.rb_out)

        row, run, stop = _run_row("▶  Run Rebuild")
        run.clicked.connect(self._do_rebuild)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        v.addLayout(row)
        v.addStretch()
        return w

    def _do_rebuild(self):
        d = self.rb_dir.value()
        o = self.rb_out.value()
        if not d or not o:
            self.log.append("✖  Both fields are required.", "fail")
            return
        self._exec(f"apktool b '{d}' -o '{o}' --force")

    # ── Sign ──────────────────────────────────────────────────────────────────
    def _sign_tab(self) -> QWidget:
        w, v = _tab_widget()

        v.addWidget(_lbl("Sign APK", 15, TEXT, bold=True))
        v.addWidget(_lbl(
            "Sign a rebuilt APK with apksigner using the Android debug keystore.\n"
            "If the keystore is absent it will be generated automatically (debug only).",
            12, DIM))
        v.addWidget(_hline())

        self.sg_apk = FilePicker("Unsigned APK", "/path/to/unsigned.apk",
                                  ffilter="APK Files (*.apk);;All Files (*)")
        self.sg_out = SavePicker("Signed APK Output  (blank = *-signed.apk)",
                                  "app-signed.apk",
                                  ffilter="APK Files (*.apk);;All Files (*)")
        v.addWidget(self.sg_apk)
        v.addWidget(self.sg_out)

        v.addWidget(_warn_box(
            "Debug keystore only — suitable for sideloading & testing.\n"
            "Production releases require your own release keystore."
        ))

        row, run, stop = _run_row("▶  Sign APK")
        run.clicked.connect(self._do_sign)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        v.addLayout(row)
        v.addStretch()
        return w

    def _do_sign(self):
        apk = self.sg_apk.value()
        if not apk:
            self.log.append("✖  APK path is required.", "fail")
            return
        out = self.sg_out.value() or str(
            Path(apk).with_name(Path(apk).stem + "-signed.apk")
        )
        ks = Path.home() / ".android" / "debug.keystore"
        if ks.exists():
            cmd = f"apksigner sign --ks '{ks}' --ks-pass pass:android --out '{out}' '{apk}'"
        else:
            gen = (
                "keytool -genkey -v -keystore /tmp/ack_debug.keystore "
                "-alias androiddebugkey -keyalg RSA -keysize 2048 -validity 10000 "
                "-storepass android -keypass android "
                "-dname 'CN=Android Debug,O=Android,C=US' 2>&1"
            )
            sign = (
                f"apksigner sign --ks /tmp/ack_debug.keystore "
                f"--ks-pass pass:android --out '{out}' '{apk}'"
            )
            cmd = f"({gen}) && {sign}"
        self._exec(cmd)


# ══════════════════════════════════════════════════════════════════════════════
#  FIRMWARE PAGE
# ══════════════════════════════════════════════════════════════════════════════
class FirmwarePage(PageBase):
    def __init__(self, runner: CommandRunner, log: LogPanel,
                 parent: Optional[QWidget] = None):
        super().__init__(
            "Firmware Tools",
            "Extract Payload · Super · Boot · EROFS",
            runner, log, parent,
        )
        tabs = QTabWidget()
        tabs.addTab(self._payload_tab(),  "  Extract Payload  ")
        tabs.addTab(self._super_up_tab(), "  Unpack Super  ")
        tabs.addTab(self._super_pk_tab(), "  Pack Super  ")
        tabs.addTab(self._boot_up_tab(),  "  Unpack Boot  ")
        tabs.addTab(self._boot_rp_tab(),  "  Repack Boot  ")
        tabs.addTab(self._erofs_tab(),    "  EROFS  ")
        self.bl.addWidget(tabs)
        self.bl.addStretch()

    # ── Extract Payload ───────────────────────────────────────────────────────
    def _payload_tab(self) -> QWidget:
        w, v = _tab_widget()
        v.addWidget(_lbl("Extract OTA Payload", 15, TEXT, bold=True))
        v.addWidget(_lbl(
            "Parallel-extract all partition images from an OTA payload.bin "
            "using payload-dumper-go.", 12, DIM))
        v.addWidget(_hline())

        self.pl_bin = FilePicker("payload.bin", "/path/to/payload.bin",
                                  ffilter="Payload Files (*.bin);;All Files (*)")
        self.pl_out = FilePicker("Output Directory", "/path/to/extracted", mode="dir")
        v.addWidget(self.pl_bin)
        v.addWidget(self.pl_out)

        row, run, stop = _run_row("▶  Extract Payload")
        run.clicked.connect(self._do_payload)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        v.addLayout(row)
        v.addStretch()
        return w

    def _do_payload(self):
        p = self.pl_bin.value()
        o = self.pl_out.value()
        if not p or not o:
            self.log.append("✖  Both fields are required.", "fail")
            return
        self._exec(f"payload-dumper-go -o '{o}' '{p}'")

    # ── Unpack Super ──────────────────────────────────────────────────────────
    def _super_up_tab(self) -> QWidget:
        w, v = _tab_widget()
        v.addWidget(_lbl("Unpack super.img", 15, TEXT, bold=True))
        v.addWidget(_lbl(
            "Extract logical partitions (system, vendor, product, odm…) "
            "from a dynamic super.img using lpunpack.", 12, DIM))
        v.addWidget(_hline())

        self.su_img = FilePicker("super.img", "/path/to/super.img",
                                  ffilter="Image Files (*.img);;All Files (*)")
        self.su_out = FilePicker("Output Directory", "/path/to/super_out", mode="dir")
        v.addWidget(self.su_img)
        v.addWidget(self.su_out)

        row, run, stop = _run_row("▶  Unpack Super")
        run.clicked.connect(lambda: self._exec(
            f"lpunpack '{self.su_img.value()}' '{self.su_out.value()}'"
        ) if self.su_img.value() and self.su_out.value()
          else self.log.append("✖  Both fields are required.", "fail"))
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        v.addLayout(row)
        v.addStretch()
        return w

    # ── Pack Super ────────────────────────────────────────────────────────────
    def _super_pk_tab(self) -> QWidget:
        w, v = _tab_widget()
        v.addWidget(_lbl("Pack super.img  (lpmake)", 15, TEXT, bold=True))
        v.addWidget(_lbl(
            "Repack extracted partition images into a new super.img.", 12, DIM))
        v.addWidget(_hline())

        self.pk_dir = FilePicker("Partitions Directory", "/path/to/partitions", mode="dir")
        self.pk_out = SavePicker("Output super.img", "super_new.img",
                                  ffilter="Image Files (*.img);;All Files (*)")
        v.addWidget(self.pk_dir)
        v.addWidget(self.pk_out)

        v.addWidget(_warn_box(
            "⚠  lpmake requires exact --metadata-size, partition sizes and group sizes "
            "that match your device.\nRun  lpdump super.img  first and update the "
            "values in the generated command. Wrong sizes will produce a non-bootable image."
        ))

        row, run, stop = _run_row("▶  Pack Super  (verify sizes first!)")
        run.clicked.connect(self._do_pack_super)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        v.addLayout(row)
        v.addStretch()
        return w

    def _do_pack_super(self):
        d = self.pk_dir.value()
        o = self.pk_out.value()
        if not d or not o:
            self.log.append("✖  Both fields are required.", "fail")
            return
        cmd = (
            f"lpmake --metadata-size 65536 --super-name super --metadata-slots 2 "
            f"--device super:3221225472 --group main:3221225472 "
            f"--partition system:readonly:2147483648 --image system='{d}/system.img' "
            f"--partition vendor:readonly:1073741824 --image vendor='{d}/vendor.img' "
            f"-o '{o}'"
        )
        self._exec(cmd)

    # ── Unpack Boot ───────────────────────────────────────────────────────────
    def _boot_up_tab(self) -> QWidget:
        w, v = _tab_widget()
        v.addWidget(_lbl("Unpack boot.img", 15, TEXT, bold=True))
        v.addWidget(_lbl(
            "Extract kernel, ramdisk.cpio, DTB, and boot parameters.\n"
            "Uses  unpack_bootimg  (AOSP) or Android Image Kitchen if present.",
            12, DIM))
        v.addWidget(_hline())

        self.bu_img = FilePicker("boot.img / init_boot.img", "/path/to/boot.img",
                                  ffilter="Image Files (*.img);;All Files (*)")
        self.bu_out = FilePicker("Output Directory", "/path/to/boot_unpacked", mode="dir")
        v.addWidget(self.bu_img)
        v.addWidget(self.bu_out)

        row, run, stop = _run_row("▶  Unpack Boot")
        run.clicked.connect(self._do_unpack_boot)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        v.addLayout(row)
        v.addStretch()
        return w

    def _do_unpack_boot(self):
        img = self.bu_img.value()
        out = self.bu_out.value()
        if not img or not out:
            self.log.append("✖  Both fields are required.", "fail")
            return
        if shutil.which("unpack_bootimg"):
            self._exec(f"unpack_bootimg --boot_img '{img}' --out '{out}'")
        elif Path("/usr/local/bin/unpackimg.sh").exists():
            self._exec(f"unpackimg.sh '{img}' --out '{out}'")
        else:
            self.log.append(
                "✖  unpack_bootimg not found. Run Setup to install AOSP tools "
                "or install Android Image Kitchen manually.", "fail"
            )

    # ── Repack Boot ───────────────────────────────────────────────────────────
    def _boot_rp_tab(self) -> QWidget:
        w, v = _tab_widget()
        v.addWidget(_lbl("Repack boot.img", 15, TEXT, bold=True))
        v.addWidget(_lbl(
            "Reconstruct boot.img from an unpacked directory using mkbootimg.\n"
            "Adjust cmdline / base / pagesize to match your device.",
            12, DIM))
        v.addWidget(_hline())

        self.br_dir = FilePicker("Unpacked Boot Directory", "/path/to/boot_unpacked", mode="dir")
        self.br_out = SavePicker("Output boot.img", "boot_new.img",
                                  ffilter="Image Files (*.img);;All Files (*)")
        v.addWidget(self.br_dir)
        v.addWidget(self.br_out)

        params = QGroupBox("Boot Parameters")
        pg = QGridLayout(params)
        pg.setSpacing(10)

        def _row(label_text: str, default: str, col: int):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"color:{DIM}; font-size:12px;")
            edit = QLineEdit(default)
            pg.addWidget(lbl,  col, 0)
            pg.addWidget(edit, col, 1)
            return edit

        self.br_cmdline  = _row("Cmdline",    "console=ttyS0,115200n8 androidboot.hardware=mt6765", 0)
        self.br_base     = _row("Base",       "0x40078000", 1)
        self.br_pagesize = _row("Page Size",  "2048",       2)
        self.br_osver    = _row("OS Version", "14.0.0",     3)
        self.br_ospatch  = _row("OS Patch",   "2025-01",    4)
        pg.setColumnStretch(1, 1)
        v.addWidget(params)

        row, run, stop = _run_row("▶  Repack Boot")
        run.clicked.connect(self._do_repack_boot)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        v.addLayout(row)
        v.addStretch()
        return w

    def _do_repack_boot(self):
        d = self.br_dir.value()
        o = self.br_out.value()
        if not d or not o:
            self.log.append("✖  Both fields are required.", "fail")
            return
        if shutil.which("mkbootimg"):
            cmd = (
                f"mkbootimg "
                f"--kernel '{d}/kernel' "
                f"--ramdisk '{d}/ramdisk.cpio' "
                f"--cmdline '{self.br_cmdline.text()}' "
                f"--base {self.br_base.text()} "
                f"--pagesize {self.br_pagesize.text()} "
                f"--os_version {self.br_osver.text()} "
                f"--os_patch_level {self.br_ospatch.text()} "
                f"-o '{o}'"
            )
            self._exec(cmd)
        elif Path("/usr/local/bin/repackimg.sh").exists():
            self._exec(f"repackimg.sh '{d}' --out '{o}'")
        else:
            self.log.append(
                "✖  mkbootimg not found. Run Setup to install AOSP tools.", "fail"
            )

    # ── EROFS ─────────────────────────────────────────────────────────────────
    def _erofs_tab(self) -> QWidget:
        w, v = _tab_widget()
        v.addWidget(_lbl("Extract EROFS Image", 15, TEXT, bold=True))
        v.addWidget(_lbl(
            "Extract an EROFS-formatted partition image (Android 12+)\n"
            "using  fsck.erofs  from the erofs-utils package.",
            12, DIM))
        v.addWidget(_hline())

        self.er_img = FilePicker("EROFS Image (.img / .erofs)", "/path/to/system.img",
                                  ffilter="Image Files (*.img *.erofs);;All Files (*)")
        self.er_out = FilePicker("Output Directory", "/path/to/erofs_out", mode="dir")
        v.addWidget(self.er_img)
        v.addWidget(self.er_out)

        row, run, stop = _run_row("▶  Extract EROFS")
        run.clicked.connect(lambda: self._exec(
            f"fsck.erofs --extract='{self.er_out.value()}' '{self.er_img.value()}'"
        ) if self.er_img.value() and self.er_out.value()
          else self.log.append("✖  Both fields are required.", "fail"))
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        v.addLayout(row)
        v.addStretch()
        return w


# ══════════════════════════════════════════════════════════════════════════════
#  SETUP PAGE
# ══════════════════════════════════════════════════════════════════════════════
class SetupPage(PageBase):
    def __init__(self, runner: CommandRunner, log: LogPanel,
                 parent: Optional[QWidget] = None):
        super().__init__("Setup & Prerequisites",
                         "Install all required tools",
                         runner, log, parent)
        self._build()

    def _build(self):
        self.bl.addWidget(_lbl(
            "Installs all dependencies for Android Custom Kitchen on Debian / Ubuntu.\n"
            "Requires sudo. Review the Terminal Output panel while running.",
            13, DIM))
        self.bl.addWidget(_hline())

        pkg_box = QGroupBox("Packages & Binaries to Install")
        pg = QGridLayout(pkg_box)
        pg.setSpacing(8)
        pg.setContentsMargins(12, 16, 12, 12)

        items = [
            ("APK Tools",        "apktool, apksigner, JADX (binary download)"),
            ("Android Bridge",   "adb, fastboot, android-tools packages"),
            ("Filesystem Tools", "e2fsprogs, erofs-utils, fsck.erofs"),
            ("Build Essentials", "openjdk-17-jdk, clang, cmake, ninja-build"),
            ("Firmware Tools",   "lpunpack, lpmake (android-sdk-libsparse-utils)"),
            ("OTA Extractor",    "payload-dumper-go (binary download from GitHub)"),
            ("Dev Libraries",    "libssl-dev, libelf-dev, libxml2-utils, zlib1g-dev"),
            ("Utilities",        "git, curl, unzip, jq, xz-utils, file"),
        ]
        for i, (cat, desc) in enumerate(items):
            c1 = QLabel(f"  ●  {cat}")
            c1.setStyleSheet(f"color:{GREEN}; font-size:12px; font-weight:bold;")
            c2 = QLabel(desc)
            c2.setStyleSheet(f"color:{DIM}; font-size:12px;")
            pg.addWidget(c1, i, 0)
            pg.addWidget(c2, i, 1)
        pg.setColumnStretch(1, 1)
        self.bl.addWidget(pkg_box)

        self.bl.addWidget(_warn_box(
            "⚠  This will run  sudo apt-get  and download binaries from GitHub.\n"
            "Ensure you are on a Debian-based distribution and have internet access."
        ))

        row, run, stop = _run_row("▶  Run Setup  (requires sudo)", stop_label="■  Stop")
        run.clicked.connect(self._do_setup)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        self.bl.addLayout(row)
        self.bl.addStretch()

    def _do_setup(self):
        workspace = Path.home() / "android-custom-kitchen"
        tools_dir = workspace / "tools"
        pkgs = (
            "git curl unzip zip xz-utils file jq python3-pip openjdk-17-jdk "
            "build-essential clang lld make cmake ninja-build bc bison flex gawk "
            "libc6-dev-i386 lib32stdc++6 lib32z1 zlib1g-dev libssl-dev libelf-dev "
            "libxml2-utils xsltproc e2fsprogs erofs-utils device-tree-compiler "
            "android-tools-adb android-tools-fastboot android-sdk-platform-tools-common "
            "apktool android-sdk-libsparse-utils"
        )
        payload_url = (
            "https://github.com/ssut/payload-dumper-go/releases/latest/download/payload-dumper-go"
        )
        jadx_url = (
            "https://github.com/skylot/jadx/releases/latest/download/jadx-1.5.0.zip"
        )
        cmd = (
            f"set -e && "
            f"sudo apt-get update -qq 2>&1 && "
            f"sudo apt-get install -y -qq {pkgs} 2>&1 && "
            f"mkdir -p '{tools_dir}' && "
            # payload-dumper-go
            f"(command -v payload-dumper-go && echo 'payload-dumper-go: already installed' || ("
            f"echo 'Downloading payload-dumper-go...' && "
            f"curl -fL -o '{tools_dir}/payload-dumper-go' '{payload_url}' && "
            f"chmod +x '{tools_dir}/payload-dumper-go' && "
            f"sudo ln -sf '{tools_dir}/payload-dumper-go' /usr/local/bin/payload-dumper-go && "
            f"echo 'payload-dumper-go installed.')) && "
            # JADX
            f"(command -v jadx && echo 'jadx: already installed' || ("
            f"echo 'Downloading JADX...' && "
            f"curl -fL -o '{tools_dir}/jadx.zip' '{jadx_url}' && "
            f"unzip -q -o '{tools_dir}/jadx.zip' -d '{tools_dir}/jadx' && "
            f"chmod +x '{tools_dir}/jadx/bin/jadx' && "
            f"sudo ln -sf '{tools_dir}/jadx/bin/jadx' /usr/local/bin/jadx && "
            f"sudo ln -sf '{tools_dir}/jadx/bin/jadx-gui' /usr/local/bin/jadx-gui && "
            f"echo 'JADX installed.')) && "
            f"echo '' && echo '✔  Setup complete. Restart ACKitchen to refresh tool status.'"
        )
        self._exec(cmd)


# ══════════════════════════════════════════════════════════════════════════════
#  ABOUT PAGE
# ══════════════════════════════════════════════════════════════════════════════
class AboutPage(PageBase):
    def __init__(self, runner: CommandRunner, log: LogPanel,
                 parent: Optional[QWidget] = None):
        super().__init__("About", "Android Custom Kitchen", runner, log, parent)
        self._build()

    def _build(self):
        # Hero
        hero = QWidget()
        hero.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f"stop:0 {GFADE}, stop:0.6 {BG1}, stop:1 {BG0});"
            f"border:1px solid {GDIM}; border-radius:12px;"
        )
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(28, 24, 28, 24)
        txt = QVBoxLayout()
        txt.setSpacing(6)
        t1 = QLabel("Android Custom Kitchen")
        t1.setStyleSheet(f"font-size:26px; font-weight:bold; color:{GREEN};")
        t2 = QLabel("Professional Firmware & APK Engineering Suite")
        t2.setStyleSheet(f"font-size:14px; color:{DIM};")
        t3 = QLabel("Version 2.0  ·  Debian/Ubuntu  ·  PyQt5")
        t3.setStyleSheet(f"font-size:12px; color:{MUTED};")
        txt.addWidget(t1)
        txt.addWidget(t2)
        txt.addWidget(t3)
        hl.addLayout(txt)
        hl.addStretch()
        ico = QLabel("🍳")
        ico.setStyleSheet("font-size:48px;")
        hl.addWidget(ico)
        self.bl.addWidget(hero)

        # Description
        desc = QLabel(
            "ACKitchen provides a unified professional graphical interface for the full Android "
            "reverse-engineering and firmware modification workflow — from APK decompilation to "
            "OTA payload extraction, super.img partition manipulation, boot image modification, "
            "and EROFS filesystem extraction.\n\n"
            "All operations delegate to battle-tested open-source CLI tools; ACKitchen simply "
            "provides a consistent, ergonomic GUI layer with real-time streamed output."
        )
        desc.setStyleSheet(f"color:{DIM}; font-size:13px; line-height:1.7;")
        desc.setWordWrap(True)
        self.bl.addWidget(desc)

        # Tool references
        refs = QGroupBox("Underlying Tools & References")
        rl = QGridLayout(refs)
        rl.setSpacing(8)
        links = [
            ("apktool",              "ibotpeaches.github.io/Apktool"),
            ("JADX",                 "github.com/skylot/jadx"),
            ("apksigner",            "developer.android.com/tools/apksigner"),
            ("payload-dumper-go",    "github.com/ssut/payload-dumper-go"),
            ("Android Image Kitchen","github.com/osm0sis/Android-Image-Kitchen"),
            ("AOSP Build Tools",     "source.android.com/setup/build/building"),
            ("erofs-utils",          "github.com/erofs/erofs-utils"),
            ("lpunpack / lpmake",    "android.googlesource.com (system/extras)"),
        ]
        for i, (name, url) in enumerate(links):
            rl.addWidget(_lbl(f"● {name}", 12, GREEN, bold=True), i, 0)
            rl.addWidget(_lbl(url, 12, MUTED), i, 1)
        rl.setColumnStretch(1, 1)
        self.bl.addWidget(refs)
        self.bl.addStretch()


# ══════════════════════════════════════════════════════════════════════════════
#  SHARED TAB HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _tab_widget():
    """Returns (QWidget, QVBoxLayout) for tab content with standard padding."""
    w   = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(22, 20, 22, 20)
    lay.setSpacing(14)
    return w, lay


def _run_row(run_label: str = "▶  Run", stop_label: str = "■  Stop"):
    """Returns (QHBoxLayout, run_btn, stop_btn) pre-styled."""
    row  = QHBoxLayout()
    row.setSpacing(10)

    run  = QPushButton(run_label)
    run.setObjectName("run")

    stop = QPushButton(stop_label)
    stop.setObjectName("stop")
    stop.setEnabled(False)

    row.addWidget(run, 3)
    row.addWidget(stop, 1)

    def _on_start():  stop.setEnabled(True)
    def _on_finish(): stop.setEnabled(False)

    # These will be connected to the real runner by the caller via _register_run
    return row, run, stop


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ══════════════════════════════════════════════════════════════════════════════
_NAV = [
    ("🏠", " Dashboard"),
    ("📦", " APK Tools"),
    ("💾", " Firmware"),
    ("⚙️", " Setup"),
    ("ℹ️", " About"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Android Custom Kitchen  v2.0")
        self.setMinimumSize(1080, 680)
        self.resize(1340, 840)

        self.runner = CommandRunner(self)
        self.log    = LogPanel(self.runner)
        self._nav_btns: List[QPushButton] = []

        # Status bar feedback
        self.runner.finished.connect(self._on_finish)

        self._build_ui()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        rl = QHBoxLayout(root)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setFixedWidth(206)
        sidebar.setStyleSheet(
            f"QWidget {{ background:{BG1}; border-right:1px solid {BORDER}; }}"
        )
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)

        # Logo strip
        logo_w = QWidget()
        logo_w.setFixedHeight(62)
        logo_w.setStyleSheet(
            f"background:{BG0}; border-bottom:1px solid {BORDER};"
        )
        ll = QHBoxLayout(logo_w)
        ll.setContentsMargins(16, 0, 16, 0)
        ico = QLabel("🍳")
        ico.setStyleSheet("font-size:20px;")
        name = QLabel(" ACKitchen")
        name.setStyleSheet(f"font-size:15px; font-weight:bold; color:{GREEN};")
        ll.addWidget(ico)
        ll.addWidget(name)
        ll.addStretch()
        sl.addWidget(logo_w)
        sl.addSpacing(6)

        # Nav buttons
        for i, (emoji, label_text) in enumerate(_NAV):
            btn = QPushButton(f"{emoji}{label_text}")
            btn.setObjectName("nav")
            btn.clicked.connect(lambda _, idx=i: self._navigate(idx))
            sl.addWidget(btn)
            self._nav_btns.append(btn)

        sl.addStretch()

        # Bottom workspace info
        ws = QLabel(f"  Workspace\n  ~/android-custom-kitchen")
        ws.setStyleSheet(f"color:{MUTED}; font-size:11px; padding:10px 14px 4px;")
        ws.setWordWrap(True)
        sl.addWidget(ws)

        ver = QLabel("  Debian/Ubuntu  ·  PyQt5")
        ver.setStyleSheet(f"color:{MUTED}; font-size:10px; padding:2px 14px 14px;")
        sl.addWidget(ver)

        rl.addWidget(sidebar)

        # ── Right: pages + log (vertical splitter) ────────────────────────────
        vsplit = QSplitter(Qt.Vertical)
        vsplit.setHandleWidth(1)

        self.stack = QStackedWidget()
        dash  = DashboardPage(self.runner, self.log)
        dash.navigate.connect(self._navigate)
        apk   = APKPage(self.runner, self.log)
        fw    = FirmwarePage(self.runner, self.log)
        setup = SetupPage(self.runner, self.log)
        about = AboutPage(self.runner, self.log)

        for page in (dash, apk, fw, setup, about):
            self.stack.addWidget(page)

        vsplit.addWidget(self.stack)
        vsplit.addWidget(self.log)
        vsplit.setSizes([580, 220])
        vsplit.setCollapsible(0, False)
        vsplit.setCollapsible(1, True)

        rl.addWidget(vsplit, 1)

        # ── Status bar ────────────────────────────────────────────────────────
        self.sb = QStatusBar()
        self.setStatusBar(self.sb)
        self.sb.showMessage("Ready — select a workflow from the sidebar to begin.")

        self._navigate(0)

    def _navigate(self, idx: int):
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_btns):
            new_name = "nav_on" if i == idx else "nav"
            if btn.objectName() != new_name:
                btn.setObjectName(new_name)
                btn.style().unpolish(btn)
                btn.style().polish(btn)
                btn.update()

    def _on_finish(self, ok: bool):
        self.sb.showMessage(
            "✔  Operation completed successfully." if ok else "✖  Operation failed — check Terminal Output.",
            6000,
        )


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Android Custom Kitchen")
    app.setApplicationVersion("2.0")
    app.setStyleSheet(_ss())

    # Prefer Ubuntu font if installed (standard on Ubuntu/Mint)
    try:
        fdb = QFontDatabase()
        if "Ubuntu" in fdb.families():
            app.setFont(QFont("Ubuntu", 13))
        elif "Noto Sans" in fdb.families():
            app.setFont(QFont("Noto Sans", 13))
    except Exception:
        pass

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
