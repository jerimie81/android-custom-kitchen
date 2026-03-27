from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import QGridLayout, QGroupBox, QLabel, QLineEdit, QTabWidget, QWidget

from ..runner import CommandRunner
from ..settings_store import SettingsStore
from ..widgets import FilePicker, SavePicker, run_row, tab_widget, warn_box
from ..workflows import WorkflowError, firmware_extract_payload_commands, firmware_pack_super_commands
from .base import PageBase


class FirmwarePage(PageBase):
    def __init__(self, runner: CommandRunner, log, settings: SettingsStore, parent: Optional[QWidget] = None):
        super().__init__("Firmware Tools", "Extract Payload · Super · Boot", runner, log, settings, parent)
        tabs = QTabWidget()
        tabs.addTab(self._payload_tab(), "Extract Payload")
        tabs.addTab(self._super_pack_tab(), "Pack Super")
        self.bl.addWidget(tabs)

    def _payload_tab(self) -> QWidget:
        w, v = tab_widget()
        self.pl_bin = FilePicker("payload.bin", "/path/to/payload.bin")
        self.pl_out = FilePicker("Output Directory", "/path/to/extracted", mode="dir")
        self.settings.bind_line_edit(self.pl_bin.edit, "firmware/payload/input")
        self.settings.bind_line_edit(self.pl_out.edit, "firmware/payload/output")
        v.addWidget(self.pl_bin)
        v.addWidget(self.pl_out)
        row, run, stop = run_row("▶  Extract Payload")
        run.clicked.connect(self._do_payload)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        v.addLayout(row)
        return w

    def _do_payload(self):
        try:
            cmds = firmware_extract_payload_commands(
                payload_bin=self.pl_bin.value(),
                output_dir=self.pl_out.value(),
                tools={"payload-dumper-go": self.settings.resolve_tool("payload-dumper-go")},
            )
        except WorkflowError as exc:
            self.log.append(f"✖  {exc}", "fail")
            return
        self.runner.run_many(cmds)

    def _super_pack_tab(self) -> QWidget:
        w, v = tab_widget()
        self.pk_dir = FilePicker("Partitions Directory", "/path/to/partitions", mode="dir")
        self.pk_out = SavePicker("Output super.img", "super_new.img")
        self.pk_super_size = QLineEdit("3221225472")
        self.pk_group_size = QLineEdit("3221225472")
        self.pk_meta_size = QLineEdit("65536")
        self.settings.bind_line_edit(self.pk_dir.edit, "firmware/super/input_dir")
        self.settings.bind_line_edit(self.pk_out.edit, "firmware/super/output", "super_new.img")
        self.settings.bind_line_edit(self.pk_super_size, "firmware/super/super_size", "3221225472")
        self.settings.bind_line_edit(self.pk_group_size, "firmware/super/group_size", "3221225472")
        self.settings.bind_line_edit(self.pk_meta_size, "firmware/super/metadata_size", "65536")
        v.addWidget(self.pk_dir)
        v.addWidget(self.pk_out)
        g = QGroupBox("Device Layout")
        gl = QGridLayout(g)
        gl.addWidget(QLabel("Super size bytes"), 0, 0)
        gl.addWidget(self.pk_super_size, 0, 1)
        gl.addWidget(QLabel("Group max size bytes"), 1, 0)
        gl.addWidget(self.pk_group_size, 1, 1)
        gl.addWidget(QLabel("Metadata size bytes"), 2, 0)
        gl.addWidget(self.pk_meta_size, 2, 1)
        v.addWidget(g)
        v.addWidget(warn_box("Device-aware repack: partitions are discovered from *.img files in the chosen directory. Verify sizes against lpdump output for your target device."))
        row, run, stop = run_row("▶  Pack Super (device-aware)")
        run.clicked.connect(self._do_pack_super)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        v.addLayout(row)
        return w

    def _do_pack_super(self):
        try:
            cmds = firmware_pack_super_commands(
                partition_dir=str(Path(self.pk_dir.value())),
                output_super=self.pk_out.value(),
                super_size=self.pk_super_size.text().strip(),
                group_size=self.pk_group_size.text().strip(),
                metadata_size=self.pk_meta_size.text().strip(),
                tools={"lpmake": self.settings.resolve_tool("lpmake")},
            )
        except WorkflowError as exc:
            self.log.append(f"✖  {exc}", "fail")
            return
        self.runner.run_many(cmds)
