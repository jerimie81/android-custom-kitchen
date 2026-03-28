from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QObject, QThread, Qt, pyqtSignal
from PyQt5.QtWidgets import QGridLayout, QGroupBox, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from ..preflight import CheckResult, run_preflight
from ..runner import CommandRunner
from ..settings_store import SettingsStore
from ..styles import BG2, GDIM, GREEN, MUTED, RED
from ..widgets import label
from .base import PageBase

TOOL_REGISTRY = [
    ("apktool", "APK Decompile", "Smali + resources"),
    ("jadx", "Java Decompile", "Java / Kotlin source"),
    ("apksigner", "APK Signing", "v2 + v3 signing"),
    ("adb", "ADB", "Android Debug Bridge"),
    ("fastboot", "Fastboot", "Bootloader flash"),
    ("payload-dumper-go", "OTA Extractor", "payload.bin -> images"),
    ("lpunpack", "Super Unpack", "Dynamic partitions"),
    ("lpmake", "Super Repack", "lpmake packer"),
    ("mkbootimg", "Boot Repack", "AOSP mkbootimg"),
    ("unpack_bootimg", "Boot Unpack", "AOSP unpack_bootimg"),
    ("fsck.erofs", "EROFS Extract", "Android 12+ FS"),
]


class PreflightWorker(QObject):
    finished = pyqtSignal(object)

    def __init__(self, settings: SettingsStore):
        super().__init__()
        self.settings = settings

    def run(self):
        self.finished.emit(run_preflight(self.settings))


class DashboardPage(PageBase):
    navigate = pyqtSignal(int)

    def __init__(self, runner: CommandRunner, log, settings: SettingsStore, parent: Optional[QWidget] = None):
        super().__init__("Dashboard", "Tool status and quick-access workflows", runner, log, settings, parent)
        self._cards: dict[str, QWidget] = {}
        self._preflight_thread: Optional[QThread] = None
        self._preflight_worker: Optional[PreflightWorker] = None
        self._preflight_layout: Optional[QVBoxLayout] = None
        self._preflight_spinner: Optional[QProgressBar] = None
        self.destroyed.connect(self._stop_preflight_thread)
        self._build()

    def _build(self):
        status_box = QGroupBox("Installed Tools")
        grid = QGridLayout(status_box)
        for i, (cmd, name, desc) in enumerate(TOOL_REGISTRY):
            card = self._make_card(cmd, name, desc)
            self._cards[cmd] = card
            grid.addWidget(card, i // 3, i % 3)
        self.bl.addWidget(status_box)

        preflight = QGroupBox("Startup Preflight")
        pl = QVBoxLayout(preflight)
        self._preflight_layout = pl
        self._preflight_spinner = QProgressBar()
        self._preflight_spinner.setRange(0, 0)
        self._preflight_spinner.setTextVisible(False)
        self._preflight_spinner.setFixedHeight(10)
        pl.addWidget(QLabel("Running startup preflight checks..."))
        pl.addWidget(self._preflight_spinner)
        self.bl.addWidget(preflight)

        ref_btn = QPushButton("⟳  Refresh Status")
        ref_btn.clicked.connect(self._refresh)
        self.bl.addWidget(ref_btn, alignment=Qt.AlignLeft)
        self.bl.addStretch()
        self._refresh()
        self._run_preflight_async()

    def _run_preflight_async(self):
        if self._preflight_thread is not None:
            return
        self._preflight_thread = QThread(self)
        self._preflight_worker = PreflightWorker(self.settings)
        self._preflight_worker.moveToThread(self._preflight_thread)
        self._preflight_thread.started.connect(self._preflight_worker.run)
        self._preflight_worker.finished.connect(self._on_preflight_ready)
        self._preflight_worker.finished.connect(self._preflight_thread.quit)
        self._preflight_thread.finished.connect(self._preflight_worker.deleteLater)
        self._preflight_thread.finished.connect(self._preflight_thread.deleteLater)
        self._preflight_thread.finished.connect(self._on_preflight_thread_finished)
        self._preflight_thread.start()

    def _on_preflight_ready(self, results: object):
        if self._preflight_layout is None:
            return
        self._clear_preflight_rows()
        for result in results:
            self._add_preflight_row(result)

    def _on_preflight_thread_finished(self):
        self._preflight_thread = None
        self._preflight_worker = None

    def _stop_preflight_thread(self):
        if self._preflight_thread is not None and self._preflight_thread.isRunning():
            self._preflight_thread.quit()
            self._preflight_thread.wait(2000)

    def _clear_preflight_rows(self):
        if self._preflight_layout is None:
            return
        while self._preflight_layout.count():
            item = self._preflight_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _add_preflight_row(self, result: CheckResult):
        if self._preflight_layout is None:
            return
        prefix = "✔" if result.ok else "✖"
        color = GREEN if result.ok else RED
        row = QLabel(f"{prefix}  {result.message}\n    Remediation: {result.remediation}")
        row.setStyleSheet(f"color:{color if result.ok else '#FF9AA5'}; font-size:12px;")
        self._preflight_layout.addWidget(row)

    def _make_card(self, cmd: str, name: str, desc: str) -> QWidget:
        card = QWidget()
        card.setStyleSheet(f"QWidget {{ background:{BG2}; border:1px solid #223244; border-radius:8px; }}")
        lay = QHBoxLayout(card)
        dot = QLabel("●")
        dot.setObjectName(f"dot_{cmd}")
        dot.setStyleSheet(f"color:{MUTED};")
        lay.addWidget(dot)
        col = QVBoxLayout()
        col.addWidget(label(name, 12, "#DFE8EF", bold=True))
        col.addWidget(label(desc, 11, MUTED))
        lay.addLayout(col, 1)
        return card

    def _refresh(self):
        for cmd, _, _ in TOOL_REGISTRY:
            found = self.settings.tool_available(cmd)
            card = self._cards.get(cmd)
            if not card:
                continue
            dot = card.findChild(QLabel, f"dot_{cmd}")
            if dot:
                dot.setStyleSheet(f"color:{GREEN};" if found else f"color:{RED};")
            border = GDIM if found else "#3D1010"
            card.setStyleSheet(f"QWidget {{ background:{BG2}; border:1px solid {border}; border-radius:8px; }}")
