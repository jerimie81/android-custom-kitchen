from __future__ import annotations

from typing import Optional

from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from ..runner import CommandRunner
from ..settings_store import SettingsStore
from ..styles import BG1, BORDER, MUTED, TEXT


class PageBase(QWidget):
    def __init__(self, title: str, subtitle: str, runner: CommandRunner, log, settings: SettingsStore, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.runner = runner
        self.log = log
        self.settings = settings
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        hdr = QWidget()
        hdr.setFixedHeight(62)
        hdr.setStyleSheet(f"background:{BG1}; border-bottom:1px solid {BORDER};")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(26, 0, 26, 0)
        tl = QLabel(title)
        tl.setStyleSheet(f"font-size:19px; font-weight:bold; color:{TEXT};")
        hl.addWidget(tl)
        sl = QLabel(subtitle)
        sl.setStyleSheet(f"color:{MUTED}; font-size:12px;")
        hl.addWidget(sl, 1)
        outer.addWidget(hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.body = QWidget()
        self.bl = QVBoxLayout(self.body)
        self.bl.setContentsMargins(26, 22, 26, 26)
        self.bl.setSpacing(16)
        scroll.setWidget(self.body)
        outer.addWidget(scroll, 1)

    def _register_run(self, btn: QPushButton):
        self.runner.started.connect(lambda: btn.setEnabled(False))
        self.runner.finished.connect(lambda _ok: btn.setEnabled(True))
