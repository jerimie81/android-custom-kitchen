from __future__ import annotations

import ackitchen.settings_store as settings_mod


def test_tool_available_falls_back_to_path_when_override_is_invalid(monkeypatch):
    store = settings_mod.SettingsStore.__new__(settings_mod.SettingsStore)
    monkeypatch.setattr(store, "resolve_tool", lambda _tool: "/does/not/exist/apktool")
    monkeypatch.setattr(settings_mod.os.path, "isfile", lambda _path: False)
    monkeypatch.setattr(settings_mod.os, "access", lambda _path, _mode: False)
    monkeypatch.setattr(settings_mod.shutil, "which", lambda tool: f"/usr/bin/{tool}" if tool == "apktool" else None)

    assert store.tool_available("apktool") is True
