from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..preflight import run_preflight
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


class DashboardPage(PageBase):
    navigate = pyqtSignal(int)

    def __init__(self, runner: CommandRunner, log, settings: SettingsStore, parent: Optional[QWidget] = None):
        super().__init__("Dashboard", "Tool status and quick-access workflows", runner, log, settings, parent)
        self._cards: dict[str, QWidget] = {}
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
        for result in run_preflight(self.settings):
            prefix = "✔" if result.ok else "✖"
            color = GREEN if result.ok else RED
            row = QLabel(f"{prefix}  {result.message}\n    Remediation: {result.remediation}")
            row.setStyleSheet(f"color:{color if result.ok else '#FF9AA5'}; font-size:12px;")
            pl.addWidget(row)
        self.bl.addWidget(preflight)

        ref_btn = QPushButton("⟳  Refresh Status")
        ref_btn.clicked.connect(self._refresh)
        self.bl.addWidget(ref_btn, alignment=Qt.AlignLeft)
        self.bl.addStretch()
        self._refresh()

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
