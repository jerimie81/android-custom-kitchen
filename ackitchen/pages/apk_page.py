from __future__ import annotations

from typing import Optional

from PyQt5.QtWidgets import QCheckBox, QLineEdit, QTabWidget, QWidget

from ..runner import CommandRunner
from ..settings_store import SettingsStore
from ..widgets import FilePicker, SavePicker, label, run_row, tab_widget
from ..workflows import WorkflowError, apk_decompile_commands, apk_rebuild_commands, apk_sign_commands
from .base import PageBase


class APKPage(PageBase):
    def __init__(self, runner: CommandRunner, log, settings: SettingsStore, parent: Optional[QWidget] = None):
        super().__init__("APK Tools", "Decompile · Rebuild · Sign", runner, log, settings, parent)
        tabs = QTabWidget()
        tabs.addTab(self._decompile_tab(), "Decompile")
        tabs.addTab(self._rebuild_tab(), "Rebuild")
        tabs.addTab(self._sign_tab(), "Sign")
        self.bl.addWidget(tabs)

    def _decompile_tab(self) -> QWidget:
        w, v = tab_widget()
        self.dc_apk = FilePicker("APK File", "/path/to/app.apk", ffilter="APK Files (*.apk)")
        self.dc_out = FilePicker("Output Directory", "/path/to/output", mode="dir")
        self.dc_jadx = QCheckBox("Also decompile Java/Kotlin source with JADX")
        self.settings.bind_line_edit(self.dc_apk.edit, "apk/decompile/input")
        self.settings.bind_line_edit(self.dc_out.edit, "apk/decompile/output")
        self.settings.bind_checkbox(self.dc_jadx, "apk/decompile/use_jadx", default=True)
        v.addWidget(self.dc_apk)
        v.addWidget(self.dc_out)
        v.addWidget(self.dc_jadx)
        row, run, stop = run_row("▶  Run Decompile")
        run.clicked.connect(self._do_decompile)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        v.addLayout(row)
        return w

    def _do_decompile(self):
        try:
            cmds = apk_decompile_commands(
                apk=self.dc_apk.value(),
                out_dir=self.dc_out.value(),
                use_jadx=self.dc_jadx.isChecked(),
                tools={"apktool": self.settings.resolve_tool("apktool"), "jadx": self.settings.resolve_tool("jadx")},
            )
        except WorkflowError as exc:
            self.log.append(f"✖  {exc}", "fail")
            return
        self.runner.run_many(cmds)

    def _rebuild_tab(self) -> QWidget:
        w, v = tab_widget()
        self.rb_dir = FilePicker("Decompiled Directory", "/path/to/decompiled", mode="dir")
        self.rb_out = SavePicker("Output APK Path", "app-modified.apk", ffilter="APK Files (*.apk)")
        self.settings.bind_line_edit(self.rb_dir.edit, "apk/rebuild/input")
        self.settings.bind_line_edit(self.rb_out.edit, "apk/rebuild/output", "app-modified.apk")
        v.addWidget(self.rb_dir)
        v.addWidget(self.rb_out)
        row, run, stop = run_row("▶  Run Rebuild")
        run.clicked.connect(self._do_rebuild)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        v.addLayout(row)
        return w

    def _do_rebuild(self):
        try:
            cmds = apk_rebuild_commands(
                decompiled_dir=self.rb_dir.value(),
                output_apk=self.rb_out.value(),
                tools={"apktool": self.settings.resolve_tool("apktool")},
            )
        except WorkflowError as exc:
            self.log.append(f"✖  {exc}", "fail")
            return
        self.runner.run_many(cmds)

    def _sign_tab(self) -> QWidget:
        w, v = tab_widget()
        self.sg_in = FilePicker("Unsigned APK", "/path/to/app-unsigned.apk", ffilter="APK Files (*.apk)")
        self.sg_out = SavePicker("Signed APK Output", "app-signed.apk", ffilter="APK Files (*.apk)")
        self.sg_ks = FilePicker("Keystore (.jks/.keystore)", "/path/to/release.keystore")
        self.sg_alias = QLineEdit()
        self.sg_alias.setPlaceholderText("release_alias")
        self.sg_kspass = QLineEdit()
        self.sg_kspass.setPlaceholderText("Keystore password")
        self.sg_kspass.setEchoMode(QLineEdit.Password)
        self.sg_keypass = QLineEdit()
        self.sg_keypass.setPlaceholderText("Key password (optional)")
        self.sg_keypass.setEchoMode(QLineEdit.Password)
        self.settings.bind_line_edit(self.sg_in.edit, "apk/sign/input")
        self.settings.bind_line_edit(self.sg_out.edit, "apk/sign/output", "app-signed.apk")
        self.settings.bind_line_edit(self.sg_ks.edit, "apk/sign/keystore")
        self.settings.bind_line_edit(self.sg_alias, "apk/sign/alias")
        self.settings.bind_line_edit(self.sg_kspass, "apk/sign/keystore_password")
        self.settings.bind_line_edit(self.sg_keypass, "apk/sign/key_password")
        v.addWidget(self.sg_in)
        v.addWidget(self.sg_out)
        v.addWidget(self.sg_ks)
        v.addWidget(label("Key Alias", 12, "#7D90A6"))
        v.addWidget(self.sg_alias)
        v.addWidget(label("Keystore Password", 12, "#7D90A6"))
        v.addWidget(self.sg_kspass)
        v.addWidget(label("Key Password (optional)", 12, "#7D90A6"))
        v.addWidget(self.sg_keypass)
        row, run, stop = run_row("▶  Sign APK")
        run.clicked.connect(self._do_sign)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        v.addLayout(row)
        return w

    def _do_sign(self):
        try:
            cmds = apk_sign_commands(
                input_apk=self.sg_in.value(),
                output_apk=self.sg_out.value(),
                keystore=self.sg_ks.value(),
                alias=self.sg_alias.text().strip(),
                keystore_password=self.sg_kspass.text(),
                key_password=self.sg_keypass.text(),
                tools={"apksigner": self.settings.resolve_tool("apksigner")},
            )
        except WorkflowError as exc:
            self.log.append(f"✖  {exc}", "fail")
            return
        self.runner.run_many(cmds)
