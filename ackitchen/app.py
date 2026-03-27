import sys

from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import QApplication

from .main_window import MainWindow
from .styles import build_stylesheet


def main() -> int:
    """
    Create and run the Qt application for Android Custom Kitchen.
    
    Initializes a QApplication, applies application name, version, and stylesheet, selects a default UI font when available, constructs and shows the main window, and starts the Qt event loop.
    
    Returns:
        int: Exit status code returned by the Qt event loop.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("Android Custom Kitchen")
    app.setApplicationVersion("2.1")
    app.setStyleSheet(build_stylesheet())
    fdb = QFontDatabase()
    if "Ubuntu" in fdb.families():
        app.setFont(QFont("Ubuntu", 13))
    elif "Noto Sans" in fdb.families():
        app.setFont(QFont("Noto Sans", 13))
    win = MainWindow()
    win.show()
    return app.exec_()
