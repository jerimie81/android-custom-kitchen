from __future__ import annotations

import ackitchen.preflight as preflight


def test_run_preflight_uses_shutil_which_for_tool_checks(monkeypatch):
    monkeypatch.setattr(preflight.platform, "system", lambda: "Linux")

    present = {"adb", "apksigner"}
    monkeypatch.setattr(preflight.shutil, "which", lambda tool: f"/usr/bin/{tool}" if tool in present else None)

    results = preflight.run_preflight()

    assert results[0].ok is True
    by_msg = {r.message.split(":")[0]: r for r in results[1:]}
    assert by_msg["adb"].ok is True
    assert by_msg["apksigner"].ok is True
    assert by_msg["apktool"].ok is False
    assert by_msg["fastboot"].ok is False


def test_run_preflight_flags_non_linux_runtime(monkeypatch):
    monkeypatch.setattr(preflight.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(preflight.shutil, "which", lambda _tool: None)

    results = preflight.run_preflight()

    assert results[0].ok is False
    assert results[0].message == "Non-Linux runtime detected."
    assert all(result.ok is False for result in results[1:])
