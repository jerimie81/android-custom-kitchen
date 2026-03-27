from __future__ import annotations

from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
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
        Initialize the main window and its core components.
        
        Creates the window title and size, instantiates the CommandRunner (self.runner) and LogPanel (self.log), initializes the navigation button list (self._nav_btns), connects the runner's finished signal to self._on_finish, and constructs the UI by calling self._build_ui().
        """
        super().__init__()
        self.setWindowTitle("Android Custom Kitchen  v2.1")
        self.setMinimumSize(1080, 680)
        self.resize(1340, 840)

        self.runner = CommandRunner(self)
        self.settings = SettingsStore()
        self.log = LogPanel(self.runner)
        self._nav_btns: List[QPushButton] = []
        self.runner.finished.connect(self._on_finish)
        self._build_ui()

    def _build_ui(self):
        """
        Constructs and lays out the main application user interface for the window.
        
        Builds a fixed-width left sidebar with logo, navigation buttons (populated from _NAV), and workspace label; creates a vertical splitter containing the central QStackedWidget (with Dashboard, APK, Firmware, Setup, and About pages) and the log panel; sets initial splitter sizes, initializes the status bar with a ready message, and selects the first navigation page. The Dashboard page's `navigate` signal is connected to the window navigation handler.
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
        self.sb.showMessage("Ready — select a workflow from the sidebar to begin.")
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
        Update the status bar with a success or failure message based on the operation result.
        
        Parameters:
            ok (bool): True if the operation succeeded; False if it failed. Shows a corresponding message ("✔  Operation completed successfully." or "✖  Operation failed — check Terminal Output.") for 6000 milliseconds.
        """
        self.sb.showMessage("✔  Operation completed successfully." if ok else "✖  Operation failed — check Terminal Output.", 6000)
