from __future__ import annotations

from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from .adb import list_adb_devices
from .pages import APKPage, AboutPage, DashboardPage, FirmwarePage, SetupPage
from .runner import CommandRunner
from .settings_store import SettingsStore
from .styles import BG0, BG1, BORDER, GREEN, MUTED
from .widgets import LogPanel

_NAV = [
    ("🏠", " Dashboard"),
    ("📦", " APK Tools"),
    ("💾", " Firmware"),
    ("⚙️", " Setup"),
    ("ℹ️", " About"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        """
        Create and configure the main application window, its UI, and core runtime components.
        
        Initializes the window and its widgets, instantiates CommandRunner, SettingsStore, and LogPanel, and constructs navigation and status-bar elements (including the ADB device combo). Registers this instance as the ADB serial provider for the runner and connects the runner's finished signal to the window's finish handler.
        
        Attributes:
            runner (CommandRunner): Command runner used to execute and monitor external operations.
            settings (SettingsStore): Application settings store and tool resolver.
            log (LogPanel): Log panel bound to the command runner.
            _nav_btns (List[QPushButton]): Sidebar navigation buttons.
            _adb_combo (QComboBox): Status-bar combo box for selecting an ADB device.
        """
        super().__init__()
        self.setWindowTitle("Android Custom Kitchen  v2.1")
        self.setMinimumSize(1080, 680)
        self.resize(1340, 840)

        self.runner = CommandRunner(self)
        self.settings = SettingsStore()
        self.log = LogPanel(self.runner)
        self._nav_btns: List[QPushButton] = []
        self._adb_combo = QComboBox()
        self.runner.set_adb_serial_provider(self._selected_adb_serial)
        self.runner.finished.connect(self._on_finish)
        self._build_ui()

    def _build_ui(self):
        """
        Builds the main window user interface: a fixed-width left navigation sidebar, a central stacked pages area with a log panel, and a status bar with ADB controls.
        
        The sidebar is populated from _NAV and provides navigation buttons. The central area is a vertical splitter containing a QStackedWidget with the Dashboard, APK, Firmware, Setup, and About pages and the log panel; the Dashboard page's `navigate` signal is connected to the window navigation handler. The status bar includes an ADB device selection combo box and a refresh button. After constructing the UI, initial splitter sizes are set, the ADB device list is refreshed, and the first navigation page is shown.
        """
        root = QWidget()
        self.setCentralWidget(root)
        rl = QHBoxLayout(root)
        rl.setContentsMargins(0, 0, 0, 0)

        sidebar = QWidget()
        sidebar.setFixedWidth(206)
        sidebar.setStyleSheet(f"QWidget {{ background:{BG1}; border-right:1px solid {BORDER}; }}")
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)

        logo_w = QWidget()
        logo_w.setFixedHeight(62)
        logo_w.setStyleSheet(f"background:{BG0}; border-bottom:1px solid {BORDER};")
        ll = QHBoxLayout(logo_w)
        ll.setContentsMargins(16, 0, 16, 0)
        ll.addWidget(QLabel("🍳"))
        name = QLabel(" ACKitchen")
        name.setStyleSheet(f"font-size:15px; font-weight:bold; color:{GREEN};")
        ll.addWidget(name)
        ll.addStretch()
        sl.addWidget(logo_w)

        for i, (emoji, txt) in enumerate(_NAV):
            btn = QPushButton(f"{emoji}{txt}")
            btn.setObjectName("nav")
            btn.clicked.connect(lambda _, idx=i: self._navigate(idx))
            sl.addWidget(btn)
            self._nav_btns.append(btn)
        sl.addStretch()

        ws = QLabel("  Workspace\n  ~/android-custom-kitchen")
        ws.setStyleSheet(f"color:{MUTED}; font-size:11px; padding:10px 14px 4px;")
        sl.addWidget(ws)
        rl.addWidget(sidebar)

        vsplit = QSplitter(Qt.Vertical)
        self.stack = QStackedWidget()
        dash = DashboardPage(self.runner, self.log, self.settings)
        dash.navigate.connect(self._navigate)
        for page in (dash, APKPage(self.runner, self.log, self.settings), FirmwarePage(self.runner, self.log, self.settings), SetupPage(self.runner, self.log, self.settings), AboutPage(self.runner, self.log, self.settings)):
            self.stack.addWidget(page)
        vsplit.addWidget(self.stack)
        vsplit.addWidget(self.log)
        vsplit.setSizes([580, 220])
        rl.addWidget(vsplit, 1)

        self.sb = QStatusBar()
        self.setStatusBar(self.sb)
        self._adb_combo.setMinimumWidth(220)
        self._adb_combo.setToolTip("ADB target device serial")
        self._adb_refresh_btn = QPushButton("⟳")
        self._adb_refresh_btn.setFixedWidth(32)
        self._adb_refresh_btn.setToolTip("Refresh connected ADB devices")
        self._adb_refresh_btn.clicked.connect(self._refresh_adb_devices)
        self.sb.addPermanentWidget(QLabel("ADB Device:"))
        self.sb.addPermanentWidget(self._adb_combo)
        self.sb.addPermanentWidget(self._adb_refresh_btn)
        self.sb.showMessage("Ready — select a workflow from the sidebar to begin.")
        self._refresh_adb_devices()
        self._navigate(0)

    def _navigate(self, idx: int):
        """
        Switches the stacked widget to the specified page and updates sidebar buttons so the button for that page is visually active.
        
        Parameters:
            idx (int): Index of the page in the stacked widget to activate; the navigation button at this index will be assigned the active style.
        """
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_btns):
            name = "nav_on" if i == idx else "nav"
            if btn.objectName() != name:
                btn.setObjectName(name)
                btn.style().unpolish(btn)
                btn.style().polish(btn)
                btn.update()

    def _on_finish(self, ok: bool):
        """
        Show a transient status-bar message indicating the outcome of an operation.
        
        If ok is True, displays "✔  Operation completed successfully." otherwise displays "✖  Operation failed — check Terminal Output." The message is shown for 6000 milliseconds.
        """
        self.sb.showMessage("✔  Operation completed successfully." if ok else "✖  Operation failed — check Terminal Output.", 6000)

    def _refresh_adb_devices(self):
        """
        Update the ADB device selector with currently connected devices.
        
        Rebuilds the combo box to include an "Auto-select" entry (data = "") plus one entry per connected device whose state is "device", labeled "<serial> (device)" with the combo data set to the device serial. If the previously selected serial is still present it is restored. The combo is enabled only when it contains at least one device entry besides "Auto-select".
        """
        current = self._adb_combo.currentData()
        self._adb_combo.clear()
        self._adb_combo.addItem("Auto-select", "")
        for device in list_adb_devices(self.settings.resolve_tool("adb")):
            if device.state == "device":
                label = f"{device.serial} ({device.state})"
                self._adb_combo.addItem(label, device.serial)
        if current:
            idx = self._adb_combo.findData(current)
            if idx >= 0:
                self._adb_combo.setCurrentIndex(idx)
        self._adb_combo.setEnabled(self._adb_combo.count() > 1)

    def _selected_adb_serial(self) -> str:
        """
        Get the currently selected ADB device serial or indicate auto-selection.
        
        Returns:
            The selected ADB serial as a string; an empty string indicates "Auto-select" or no device is selected.
        """
        return str(self._adb_combo.currentData() or "")