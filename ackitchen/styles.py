"""Shared color constants + global stylesheet."""

BG0    = "#090F17"
BG1    = "#0E1620"
BG2    = "#141D2B"
BG3    = "#1C2736"
BG4    = "#243044"

GREEN  = "#3DDC84"
GDIM   = "#1A5C3A"
GFADE  = "#0D3020"

CYAN   = "#4FC3F7"
TEXT   = "#DDE6F0"
DIM    = "#7A94AA"
MUTED  = "#3A5068"

RED    = "#FF4757"
ORANGE = "#FFB74D"
BORDER = "#1E2D3D"


def build_stylesheet() -> str:
    """
    Builds the application's global Qt stylesheet from the module's color and style constants.
    
    Returns:
        stylesheet (str): A Qt stylesheet string defining base font and outline rules and styling for QWidget, QLabel, QLineEdit (focus state), QTextEdit, QCheckBox (including checked state), QPushButton (and object-name variants `#run`, `#stop`, `#browse`, `#nav`, `#nav_on`), QGroupBox (and its title), QStatusBar, and QProgressBar.
    """
    return f"""
* {{ font-family: 'Ubuntu', 'Noto Sans', 'DejaVu Sans', sans-serif; font-size: 13px; outline: none; }}
QWidget {{ background: {BG0}; color: {TEXT}; border: none; }}
QLabel {{ background: transparent; }}
QLineEdit {{ background: {BG2}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 6px; padding: 8px 11px; }}
QLineEdit:focus {{ border-color: {GREEN}; background: {BG3}; }}
QTextEdit {{ background: {BG1}; color: #9FB8CC; border: 1px solid {BORDER}; border-radius: 6px; font-family: 'JetBrains Mono', 'Courier New', monospace; font-size: 12px; }}
QCheckBox::indicator {{ width: 17px; height: 17px; border: 1px solid {BORDER}; border-radius: 4px; background: {BG2}; }}
QCheckBox::indicator:checked {{ background: {GDIM}; border-color: {GREEN}; }}
QPushButton {{ background: {BG3}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 7px; padding: 8px 16px; min-height: 32px; }}
QPushButton:hover {{ background: {BG4}; border-color: {GREEN}; }}
QPushButton#run {{ background: {GDIM}; color: #fff; border: 1px solid {GREEN}; font-weight: bold; min-height: 42px; }}
QPushButton#stop {{ background: #2A1015; color: {RED}; border: 1px solid {RED}; font-weight: bold; min-height: 42px; }}
QPushButton#browse {{ background: {BG2}; color: {DIM}; border: 1px solid {BORDER}; min-height: 0; }}
QPushButton#nav {{ background: transparent; color: {DIM}; text-align: left; border: none; border-radius: 0; padding: 11px 20px 11px 18px; font-size: 14px; min-height: 44px; }}
QPushButton#nav_on {{ background: {GFADE}; color: {GREEN}; text-align: left; border: none; border-left: 3px solid {GREEN}; padding: 11px 20px 11px 15px; font-size: 14px; min-height: 44px; font-weight: bold; }}
QGroupBox {{ background: {BG1}; border: 1px solid {BORDER}; border-radius: 9px; margin-top: 18px; padding: 14px 12px 12px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 14px; padding: 2px 9px; color: {GREEN}; font-weight: bold; font-size: 12px; background: {BG1}; }}
QStatusBar {{ background: {BG1}; color: {DIM}; border-top: 1px solid {BORDER}; font-size: 12px; }}
QProgressBar {{ background: {BG3}; border: none; border-radius: 3px; height: 5px; color: transparent; }}
QProgressBar::chunk {{ background: {GREEN}; border-radius: 3px; }}
"""
