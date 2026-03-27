from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .preflight import run_preflight
from .runner import CommandRunner, CommandSpec
from .styles import BG1, BG2, BORDER, DIM, GDIM, GFADE, GREEN, MUTED, RED, TEXT
from .widgets import FilePicker, SavePicker, hline, info_box, label, run_row, tab_widget, warn_box

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


class PageBase(QWidget):
    def __init__(self, title: str, subtitle: str, runner: CommandRunner, log, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.runner = runner
        self.log = log
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


class DashboardPage(PageBase):
    navigate = pyqtSignal(int)

    def __init__(self, runner: CommandRunner, log, parent: Optional[QWidget] = None):
        super().__init__("Dashboard", "Tool status and quick-access workflows", runner, log, parent)
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
        for result in run_preflight():
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
        card.setStyleSheet(f"QWidget {{ background:{BG2}; border:1px solid {BORDER}; border-radius:8px; }}")
        lay = QHBoxLayout(card)
        dot = QLabel("●")
        dot.setObjectName(f"dot_{cmd}")
        dot.setStyleSheet(f"color:{MUTED};")
        lay.addWidget(dot)
        col = QVBoxLayout()
        col.addWidget(label(name, 12, TEXT, bold=True))
        col.addWidget(label(desc, 11, MUTED))
        lay.addLayout(col, 1)
        return card

    def _refresh(self):
        for cmd, _, _ in TOOL_REGISTRY:
            found = bool(shutil.which(cmd))
            card = self._cards.get(cmd)
            if not card:
                continue
            dot = card.findChild(QLabel, f"dot_{cmd}")
            if dot:
                dot.setStyleSheet(f"color:{GREEN};" if found else f"color:{RED};")
            border = GDIM if found else "#3D1010"
            card.setStyleSheet(f"QWidget {{ background:{BG2}; border:1px solid {border}; border-radius:8px; }}")


class APKPage(PageBase):
    def __init__(self, runner: CommandRunner, log, parent: Optional[QWidget] = None):
        super().__init__("APK Tools", "Decompile · Rebuild · Sign", runner, log, parent)
        tabs = QTabWidget()
        tabs.addTab(self._decompile_tab(), "Decompile")
        tabs.addTab(self._rebuild_tab(), "Rebuild")
        self.bl.addWidget(tabs)

    def _decompile_tab(self) -> QWidget:
        w, v = tab_widget()
        self.dc_apk = FilePicker("APK File", "/path/to/app.apk", ffilter="APK Files (*.apk)")
        self.dc_out = FilePicker("Output Directory", "/path/to/output", mode="dir")
        self.dc_jadx = QCheckBox("Also decompile Java/Kotlin source with JADX")
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
        apk, out = self.dc_apk.value(), self.dc_out.value()
        if not apk or not out:
            self.log.append("✖  APK path and output directory are required.", "fail")
            return
        cmds = [CommandSpec("apktool", ["d", apk, "-o", out, "--force"])]
        if self.dc_jadx.isChecked():
            cmds.append(CommandSpec("jadx", ["-d", str(Path(out) / "jadx_sources"), "--deobf", apk]))
        self.runner.run_many(cmds)

    def _rebuild_tab(self) -> QWidget:
        w, v = tab_widget()
        self.rb_dir = FilePicker("Decompiled Directory", "/path/to/decompiled", mode="dir")
        self.rb_out = SavePicker("Output APK Path", "app-modified.apk", ffilter="APK Files (*.apk)")
        v.addWidget(self.rb_dir)
        v.addWidget(self.rb_out)
        row, run, stop = run_row("▶  Run Rebuild")
        run.clicked.connect(self._do_rebuild)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        v.addLayout(row)
        return w

    def _do_rebuild(self):
        d, o = self.rb_dir.value(), self.rb_out.value()
        if not d or not o:
            self.log.append("✖  Both fields are required.", "fail")
            return
        self.runner.run_one("apktool", ["b", d, "-o", o, "--force"])


class FirmwarePage(PageBase):
    def __init__(self, runner: CommandRunner, log, parent: Optional[QWidget] = None):
        super().__init__("Firmware Tools", "Extract Payload · Super · Boot", runner, log, parent)
        tabs = QTabWidget()
        tabs.addTab(self._payload_tab(), "Extract Payload")
        tabs.addTab(self._super_pack_tab(), "Pack Super")
        self.bl.addWidget(tabs)

    def _payload_tab(self) -> QWidget:
        w, v = tab_widget()
        self.pl_bin = FilePicker("payload.bin", "/path/to/payload.bin")
        self.pl_out = FilePicker("Output Directory", "/path/to/extracted", mode="dir")
        v.addWidget(self.pl_bin)
        v.addWidget(self.pl_out)
        row, run, stop = run_row("▶  Extract Payload")
        run.clicked.connect(self._do_payload)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        v.addLayout(row)
        return w

    def _do_payload(self):
        p, o = self.pl_bin.value(), self.pl_out.value()
        if not p or not o:
            self.log.append("✖  Both fields are required.", "fail")
            return
        self.runner.run_one("payload-dumper-go", ["-o", o, p])

    def _super_pack_tab(self) -> QWidget:
        w, v = tab_widget()
        self.pk_dir = FilePicker("Partitions Directory", "/path/to/partitions", mode="dir")
        self.pk_out = SavePicker("Output super.img", "super_new.img")
        self.pk_super_size = QLineEdit("3221225472")
        self.pk_meta_size = QLineEdit("65536")
        v.addWidget(self.pk_dir)
        v.addWidget(self.pk_out)
        g = QGroupBox("Device Layout")
        gl = QGridLayout(g)
        gl.addWidget(QLabel("Super size bytes"), 0, 0)
        gl.addWidget(self.pk_super_size, 0, 1)
        gl.addWidget(QLabel("Metadata size bytes"), 1, 0)
        gl.addWidget(self.pk_meta_size, 1, 1)
        v.addWidget(g)
        v.addWidget(warn_box("Device-aware repack: partitions are discovered from *.img files in the chosen directory. Verify sizes against lpdump output for your target device."))
        row, run, stop = run_row("▶  Pack Super (device-aware)")
        run.clicked.connect(self._do_pack_super)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        v.addLayout(row)
        return w

    def _do_pack_super(self):
        d, o = Path(self.pk_dir.value()), self.pk_out.value()
        if not d.exists() or not o:
            self.log.append("✖  Valid partition directory and output file are required.", "fail")
            return
        images = sorted(p for p in d.glob("*.img") if p.is_file())
        if not images:
            self.log.append("✖  No *.img partitions found in directory.", "fail")
            return
        super_size = self.pk_super_size.text().strip()
        metadata = self.pk_meta_size.text().strip()
        try:
            total = sum(p.stat().st_size for p in images)
        except OSError as exc:
            self.log.append(f"✖  Failed to read image size: {exc}", "fail")
            return

        args = [
            "--metadata-size", metadata,
            "--super-name", "super",
            "--metadata-slots", "2",
            "--device", f"super:{super_size}",
            "--group", f"main:{total}",
        ]
        for img in images:
            part = img.stem
            size = str(img.stat().st_size)
            args.extend(["--partition", f"{part}:readonly:{size}", "--image", f"{part}={str(img)}"])
        args.extend(["-o", o])
        self.runner.run_one("lpmake", args)


class SetupPage(PageBase):
    def __init__(self, runner: CommandRunner, log, parent: Optional[QWidget] = None):
        super().__init__("Setup & Prerequisites", "Install all required tools", runner, log, parent)
        self.bl.addWidget(info_box("Setup is split into safe argv-based calls to avoid shell injection and path-escaping issues."))
        self.bl.addWidget(hline())
        row, run, stop = run_row("▶  Run Setup (requires sudo)")
        run.clicked.connect(self._do_setup)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        self.bl.addLayout(row)

    def _do_setup(self):
        pkgs = [
            "git", "curl", "unzip", "xz-utils", "file", "jq", "python3-pip", "openjdk-17-jdk",
            "build-essential", "clang", "cmake", "ninja-build", "e2fsprogs", "erofs-utils",
            "android-tools-adb", "android-tools-fastboot", "apktool", "android-sdk-libsparse-utils",
        ]
        self.runner.run_many([
            CommandSpec("sudo", ["apt-get", "update", "-qq"]),
            CommandSpec("sudo", ["apt-get", "install", "-y", "-qq", *pkgs]),
        ])


class AboutPage(PageBase):
    def __init__(self, runner: CommandRunner, log, parent: Optional[QWidget] = None):
        super().__init__("About", "Android Custom Kitchen", runner, log, parent)
        self.bl.addWidget(label("Android Custom Kitchen", 26, GREEN, bold=True))
        self.bl.addWidget(label("Version 2.1  ·  Debian/Ubuntu  ·  PyQt5", 12, MUTED))
        self.bl.addWidget(label("This build modularizes pages, runner, widgets and styling while hardening command execution.", 13, DIM))
        self.bl.addStretch()
