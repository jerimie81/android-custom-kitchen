from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class AdbDevice:
    serial: str
    state: str


def list_adb_devices(adb_program: str = "adb") -> list[AdbDevice]:
    """
    Return devices reported by `adb devices`, excluding header/blank lines.
    """
    proc = subprocess.run(
        [adb_program, "devices"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    devices: list[AdbDevice] = []
    for raw in proc.stdout.splitlines():
        line = raw.strip()
        if not line or line.startswith("List of devices attached"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            devices.append(AdbDevice(serial=parts[0], state=parts[1]))
    return devices
