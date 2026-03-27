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
        super().__init__()
        self.setWindowTitle("Android Custom Kitchen  v2.1")
        self.setMinimumSize(1080, 680)
        self.resize(1340, 840)

        self.runner = CommandRunner(self)
        self.log = LogPanel(self.runner)
        self._nav_btns: List[QPushButton] = []
        self.runner.finished.connect(self._on_finish)
        self._build_ui()

    def _build_ui(self):
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
        dash = DashboardPage(self.runner, self.log)
        dash.navigate.connect(self._navigate)
        for page in (dash, APKPage(self.runner, self.log), FirmwarePage(self.runner, self.log), SetupPage(self.runner, self.log), AboutPage(self.runner, self.log)):
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
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_btns):
            name = "nav_on" if i == idx else "nav"
            if btn.objectName() != name:
                btn.setObjectName(name)
                btn.style().unpolish(btn)
                btn.style().polish(btn)
                btn.update()

    def _on_finish(self, ok: bool):
        self.sb.showMessage("✔  Operation completed successfully." if ok else "✖  Operation failed — check Terminal Output.", 6000)
