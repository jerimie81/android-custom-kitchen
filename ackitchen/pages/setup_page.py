from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import QGridLayout, QGroupBox

from ..runner import CommandRunner
from ..settings_store import SettingsStore
from ..widgets import FilePicker, hline, info_box, run_row
from ..workflows import setup_commands
from .base import PageBase


class SetupPage(PageBase):
    def __init__(self, runner: CommandRunner, log, settings: SettingsStore, parent: Optional[QWidget] = None):
        super().__init__("Setup & Prerequisites", "Install all required tools", runner, log, settings, parent)
        self.bl.addWidget(info_box("Setup is split into safe argv-based calls to avoid shell injection and path-escaping issues."))
        overrides = QGroupBox("Tool Path Overrides (optional)")
        ovl = QGridLayout(overrides)
        self.path_apksigner = FilePicker("apksigner path", "/usr/local/bin/apksigner")
        self.path_jadx = FilePicker("jadx path", "/usr/local/bin/jadx")
        self.path_payload = FilePicker("payload-dumper-go path", "/usr/local/bin/payload-dumper-go")
        self.settings.bind_line_edit(self.path_apksigner.edit, "tools/apksigner/path")
        self.settings.bind_line_edit(self.path_jadx.edit, "tools/jadx/path")
        self.settings.bind_line_edit(self.path_payload.edit, "tools/payload-dumper-go/path")
        ovl.addWidget(self.path_apksigner, 0, 0)
        ovl.addWidget(self.path_jadx, 1, 0)
        ovl.addWidget(self.path_payload, 2, 0)
        self.bl.addWidget(overrides)
        self.bl.addWidget(hline())
        row, run, stop = run_row("▶  Run Setup (requires sudo)")
        run.clicked.connect(self._do_setup)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        self.bl.addLayout(row)

    def _do_setup(self):
        installer_script = str(Path(__file__).resolve().parent.parent / "installers.py")
        self.runner.run_many(setup_commands(installer_script))
