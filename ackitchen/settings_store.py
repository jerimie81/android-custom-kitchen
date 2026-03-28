from __future__ import annotations

import os
import shutil
from typing import Optional

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QCheckBox, QLineEdit


class SettingsStore:
    def __init__(self):
        self._settings = QSettings("ackitchen", "android-custom-kitchen")

    def get_str(self, key: str, default: str = "") -> str:
        value = self._settings.value(key, default, type=str)
        return (value or "").strip()

    def set_str(self, key: str, value: str):
        self._settings.setValue(key, value.strip())

    def get_bool(self, key: str, default: bool = False) -> bool:
        return bool(self._settings.value(key, default, type=bool))

    def set_bool(self, key: str, value: bool):
        self._settings.setValue(key, bool(value))

    def bind_line_edit(self, widget: QLineEdit, key: str, default: str = ""):
        widget.setText(self.get_str(key, default))
        widget.textChanged.connect(lambda text: self.set_str(key, text))

    def bind_checkbox(self, widget: QCheckBox, key: str, default: bool = False):
        widget.setChecked(self.get_bool(key, default))
        widget.toggled.connect(lambda checked: self.set_bool(key, checked))

    def tool_path(self, tool_name: str) -> str:
        return self.get_str(f"tools/{tool_name}/path")

    def set_tool_path(self, tool_name: str, path: str):
        self.set_str(f"tools/{tool_name}/path", path)

    def resolve_tool(self, tool_name: str) -> str:
        return self.tool_path(tool_name) or tool_name

    def tool_available(self, tool_name: str) -> bool:
        candidate = self.resolve_tool(tool_name)
        if os.path.sep in candidate:
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return True
            # Fallback to PATH lookup when a stale/invalid override is configured.
            return shutil.which(tool_name) is not None
        return shutil.which(candidate) is not None
