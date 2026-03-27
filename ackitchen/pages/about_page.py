from __future__ import annotations

from typing import Optional

from PyQt5.QtWidgets import QWidget

from ..runner import CommandRunner
from ..settings_store import SettingsStore
from ..styles import DIM, GREEN, MUTED
from ..widgets import label
from .base import PageBase


class AboutPage(PageBase):
    def __init__(self, runner: CommandRunner, log, settings: SettingsStore, parent: Optional[QWidget] = None):
        super().__init__("About", "Android Custom Kitchen", runner, log, settings, parent)
        self.bl.addWidget(label("Android Custom Kitchen", 26, GREEN, bold=True))
        self.bl.addWidget(label("Version 2.1  ·  Debian/Ubuntu  ·  PyQt5", 12, MUTED))
        self.bl.addWidget(label("This build modularizes pages, runner, widgets and styling while hardening command execution.", 13, DIM))
        self.bl.addStretch()
