from __future__ import annotations

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
from .settings_store import SettingsStore
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
    def __init__(self, title: str, subtitle: str, runner: CommandRunner, log, settings: SettingsStore, parent: Optional[QWidget] = None):
        """
        Initialize the page scaffold with a fixed header (title and subtitle) and a scrollable content area.
        
        Sets self.runner and self.log, creates a styled header showing title and subtitle, and prepares a scrollable body widget with a top-level vertical layout available as self.body and self.bl for subclasses to populate.
        
        Parameters:
            title (str): Header title text.
            subtitle (str): Header subtitle text.
            runner (CommandRunner): Command runner used by the page to execute operations.
            log: Log widget or logger where the page should append status/error messages.
            parent (Optional[QWidget]): Optional Qt parent widget.
        """
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
        """
        Attach the given run button to the page's CommandRunner so the button is disabled while a run is active and re-enabled when the run finishes.
        
        Parameters:
            btn (QPushButton): The run button to disable during execution and re-enable when finished.
        """
        self.runner.started.connect(lambda: btn.setEnabled(False))
        self.runner.finished.connect(lambda _ok: btn.setEnabled(True))


class DashboardPage(PageBase):
    navigate = pyqtSignal(int)

    def __init__(self, runner: CommandRunner, log, settings: SettingsStore, parent: Optional[QWidget] = None):
        """
        Initialize the Dashboard page that displays installed-tool status cards and startup preflight results.
        
        Parameters:
            runner (CommandRunner): Command runner used to execute external tool checks and workflows.
            log: UI log widget or logger used to append status/error messages.
            parent (Optional[QWidget]): Optional Qt parent widget.
        """
        super().__init__("Dashboard", "Tool status and quick-access workflows", runner, log, settings, parent)
        self._cards: dict[str, QWidget] = {}
        self._build()

    def _build(self):
        """
        Builds the dashboard content: an "Installed Tools" grid, a "Startup Preflight" list, and a refresh control.
        
        Creates a card for each tool in TOOL_REGISTRY and stores it in self._cards, renders preflight results with a success/failure icon and colored text, adds a "Refresh Status" button wired to self._refresh, and calls self._refresh() to initialize the displayed statuses.
        """
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
        """
        Create a small status card widget for a tool.
        
        Parameters:
        	cmd (str): Tool executable/command name; used to identify the status dot widget (object name `dot_{cmd}`).
        	name (str): Display title shown on the card.
        	desc (str): Short, muted description shown below the title.
        
        Returns:
        	card (QWidget): A styled QWidget containing a status dot and the tool's title and description.
        """
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
        """
        Update installed-tool cards to reflect whether each tool is available on PATH.
        
        For each entry in TOOL_REGISTRY, checks whether the tool executable is found on PATH and updates the corresponding card widget (if present) by setting the status dot color to green or red and adjusting the card border color. Tools without a registered card are skipped silently.
        """
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


class APKPage(PageBase):
    def __init__(self, runner: CommandRunner, log, settings: SettingsStore, parent: Optional[QWidget] = None):
        """
        Create the APK Tools page containing "Decompile" and "Rebuild" tabs.
        
        Initializes the page title and subtitle via the base class and adds a QTabWidget with a Decompile tab and a Rebuild tab.
        
        Parameters:
        	parent (Optional[QWidget]): Optional Qt parent widget for this page.
        """
        super().__init__("APK Tools", "Decompile · Rebuild · Sign", runner, log, settings, parent)
        tabs = QTabWidget()
        tabs.addTab(self._decompile_tab(), "Decompile")
        tabs.addTab(self._rebuild_tab(), "Rebuild")
        tabs.addTab(self._sign_tab(), "Sign")
        self.bl.addWidget(tabs)

    def _decompile_tab(self) -> QWidget:
        """
        Create the "Decompile" tab containing input widgets and run/stop controls.
        
        Sets self.dc_apk, self.dc_out, and self.dc_jadx to the created FilePicker and QCheckBox widgets, connects the run button to self._do_decompile and the stop button to self.runner.stop, and registers the run button with the command runner.
        
        Returns:
            QWidget: The tab widget ready to be inserted into a QTabWidget.
        """
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
        """
        Run an APK decompilation: validates inputs, schedules apktool and optional JADX tasks.
        
        If the APK path or output directory is missing, appends a failure message to the UI log and aborts. Otherwise enqueues an `apktool d` command to decompile the APK into the output directory and, if the "decompile with JADX" option is checked, also enqueues a `jadx` command to produce deobfuscated Java/Kotlin sources under `<out>/jadx_sources`.
        """
        apk, out = self.dc_apk.value(), self.dc_out.value()
        if not apk or not out:
            self.log.append("✖  APK path and output directory are required.", "fail")
            return
        cmds = [CommandSpec(self.settings.resolve_tool("apktool"), ["d", apk, "-o", out, "--force"])]
        if self.dc_jadx.isChecked():
            cmds.append(CommandSpec(self.settings.resolve_tool("jadx"), ["-d", str(Path(out) / "jadx_sources"), "--deobf", apk]))
        self.runner.run_many(cmds)

    def _rebuild_tab(self) -> QWidget:
        """
        Create and return the "Rebuild" tab UI for the APK rebuild workflow.
        
        This builds UI controls for selecting a decompiled directory and the output APK path, assigns them to
        self.rb_dir and self.rb_out, and adds a run/stop row where the run button is connected to
        self._do_rebuild and the stop button calls self.runner.stop. The run button is registered with the
        page runner to toggle its enabled state during execution.
        
        Returns:
            QWidget: The constructed tab widget.
        """
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
        """
        Builds an APK from the selected decompiled directory and writes it to the chosen output path.
        
        If either the decompiled directory or output path is empty, appends "✖  Both fields are required." to the log with level "fail" and aborts. Otherwise invokes apktool to rebuild the APK into the specified output file.
        """
        d, o = self.rb_dir.value(), self.rb_out.value()
        if not d or not o:
            self.log.append("✖  Both fields are required.", "fail")
            return
        self.runner.run_one(self.settings.resolve_tool("apktool"), ["b", d, "-o", o, "--force"])

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
        v.addWidget(label("Key Alias", 12, DIM))
        v.addWidget(self.sg_alias)
        v.addWidget(label("Keystore Password", 12, DIM))
        v.addWidget(self.sg_kspass)
        v.addWidget(label("Key Password (optional)", 12, DIM))
        v.addWidget(self.sg_keypass)
        row, run, stop = run_row("▶  Sign APK")
        run.clicked.connect(self._do_sign)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        v.addLayout(row)
        return w

    def _do_sign(self):
        in_apk, out_apk = self.sg_in.value(), self.sg_out.value()
        ks, alias = self.sg_ks.value(), self.sg_alias.text().strip()
        ks_pass = self.sg_kspass.text()
        key_pass = self.sg_keypass.text()
        if not in_apk or not out_apk or not ks or not alias or not ks_pass:
            self.log.append("✖  Unsigned APK, output path, keystore, alias, and keystore password are required.", "fail")
            return
        signer = self.settings.resolve_tool("apksigner")
        args = ["sign", "--ks", ks, "--ks-key-alias", alias, "--ks-pass", f"pass:{ks_pass}", "--out", out_apk]
        if key_pass:
            args.extend(["--key-pass", f"pass:{key_pass}"])
        args.append(in_apk)
        self.runner.run_many([
            CommandSpec(signer, args),
            CommandSpec(signer, ["verify", "--verbose", out_apk]),
        ])


class FirmwarePage(PageBase):
    def __init__(self, runner: CommandRunner, log, settings: SettingsStore, parent: Optional[QWidget] = None):
        """
        Initialize the FirmwarePage UI with tabs for OTA payload extraction and super image packing.
        
        Creates a tab widget containing:
        - "Extract Payload" — tools for extracting an OTA payload.bin.
        - "Pack Super" — tools for building a `super.img` from partition images.
        
        Parameters:
            parent (Optional[QWidget]): Optional parent widget for ownership in the Qt hierarchy.
        """
        super().__init__("Firmware Tools", "Extract Payload · Super · Boot", runner, log, settings, parent)
        tabs = QTabWidget()
        tabs.addTab(self._payload_tab(), "Extract Payload")
        tabs.addTab(self._super_pack_tab(), "Pack Super")
        self.bl.addWidget(tabs)

    def _payload_tab(self) -> QWidget:
        """
        Create and return the "Extract Payload" tab widget used for OTA payload extraction.
        
        This builds a tab containing file pickers for the input `payload.bin` and an output directory, adds Run and Stop controls wired to `_do_payload` and the runner's `stop`, and registers the Run button with the page's runner so its enabled state is managed.
        
        Returns:
            QWidget: The constructed tab widget.
        """
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
        """
        Extract the given OTA payload.bin into the specified output directory using payload-dumper-go.
        
        Validates that both the payload file path and output directory are provided; if either is missing, a failure message is appended to the log and the operation is aborted.
        
        Parameters:
            p (str): Path to the payload.bin file to extract.
            o (str): Path to the directory where extracted files will be written.
        """
        p, o = self.pl_bin.value(), self.pl_out.value()
        if not p or not o:
            self.log.append("✖  Both fields are required.", "fail")
            return
        self.runner.run_one(self.settings.resolve_tool("payload-dumper-go"), ["-o", o, p])

    def _super_pack_tab(self) -> QWidget:
        """
        Create and return the "Pack Super" tab widget for assembling a device-aware super.img from partition images.
        
        The tab provides UI controls to select a partitions directory, choose an output super.img path, and enter super and metadata sizes; it also shows a warning about verifying sizes and includes Run/Stop controls that trigger the pack action and stop the runner.
        
        Returns:
            QWidget: The constructed tab widget containing the directory/file pickers, size inputs, warning box, and run/stop controls.
        """
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
        """
        Pack partition `.img` files into an Android super image using lpmake.
        
        Validates the selected partition directory and output path, parses `super`, `group`, and `metadata` sizes from the UI as integers, and ensures the group size is at least the sum of the partition file sizes. If validation or filesystem checks fail, appends a failure message to the page log and returns without running any commands. On success, invokes the resolved `lpmake` tool via the page's command runner to produce the specified output super image.
        """
        d, o = Path(self.pk_dir.value()), self.pk_out.value()
        if not d.exists() or not o:
            self.log.append("✖  Valid partition directory and output file are required.", "fail")
            return
        images = sorted(p for p in d.glob("*.img") if p.is_file())
        if not images:
            self.log.append("✖  No *.img partitions found in directory.", "fail")
            return
        super_size_raw = self.pk_super_size.text().strip()
        group_size_raw = self.pk_group_size.text().strip()
        metadata_raw = self.pk_meta_size.text().strip()
        try:
            super_size = int(super_size_raw)
            group_size = int(group_size_raw)
            metadata = int(metadata_raw)
        except ValueError:
            self.log.append("✖  Super/group/metadata sizes must be integer byte values.", "fail")
            return
        try:
            total = sum(p.stat().st_size for p in images)
            if group_size < total:
                self.log.append(f"✖  Group max size ({group_size}) must be >= total partition bytes ({total}).", "fail")
                return
        except OSError as exc:
            self.log.append(f"✖  Failed to read image size: {exc}", "fail")
            return

        args = [
            "--metadata-size", str(metadata),
            "--super-name", "super",
            "--metadata-slots", "2",
            "--device", f"super:{super_size}",
            "--group", f"main:{group_size}",
        ]
        for img in images:
            part = img.stem
            size = str(img.stat().st_size)
            args.extend(["--partition", f"{part}:readonly:{size}", "--image", f"{part}={str(img)}"])
        args.extend(["-o", o])
        self.runner.run_one(self.settings.resolve_tool("lpmake"), args)


class SetupPage(PageBase):
    def __init__(self, runner: CommandRunner, log, settings: SettingsStore, parent: Optional[QWidget] = None):
        """
        Initialize the Setup page UI and wire the run/stop controls for installing prerequisite packages.
        
        Parameters:
            runner (CommandRunner): Executor used to run installation commands.
            log: Log widget or logger where action output and errors are appended.
            parent (Optional[QWidget]): Optional parent widget for this page.
        """
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
        """
        Install the prerequisite development and Android tooling packages using apt (requires sudo).
        
        Executes an `apt-get update` followed by `apt-get install -y` for a predefined set of packages (development toolchain, filesystem utilities, Android platform tools, apktool, OpenJDK, and related dependencies).
        """
        pkgs = [
            "git", "curl", "unzip", "xz-utils", "file", "jq", "python3-pip", "openjdk-17-jdk",
            "build-essential", "clang", "cmake", "ninja-build", "e2fsprogs", "erofs-utils",
            "android-tools-adb", "android-tools-fastboot", "apktool", "android-sdk-libsparse-utils", "jadx",
        ]
        installer_script = str(Path(__file__).with_name("installers.py"))
        self.runner.run_many([
            CommandSpec("sudo", ["apt-get", "update", "-qq"]),
            CommandSpec("sudo", ["apt-get", "install", "-y", "-qq", *pkgs]),
            CommandSpec("sudo", ["python3", installer_script, "ensure-tools"]),
        ])


class AboutPage(PageBase):
    def __init__(self, runner: CommandRunner, log, settings: SettingsStore, parent: Optional[QWidget] = None):
        """
        Constructs the About page UI displaying the application title, version/platform, and a brief build description.
        
        Adds styled labels for the app title, a version/platform line, and a short build summary, then inserts a stretch to consume remaining vertical space.
        """
        super().__init__("About", "Android Custom Kitchen", runner, log, settings, parent)
        self.bl.addWidget(label("Android Custom Kitchen", 26, GREEN, bold=True))
        self.bl.addWidget(label("Version 2.1  ·  Debian/Ubuntu  ·  PyQt5", 12, MUTED))
        self.bl.addWidget(label("This build modularizes pages, runner, widgets and styling while hardening command execution.", 13, DIM))
        self.bl.addStretch()