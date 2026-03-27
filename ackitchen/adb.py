from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class AdbDevice:
    serial: str
    state: str


def list_adb_devices(adb_program: str = "adb") -> list[AdbDevice]:
    """
    Parse the output of `adb devices` and produce a list of detected devices.
    
    Parameters:
        adb_program (str): Command or path to the `adb` executable to invoke (default: "adb").
    
    Returns:
        list[AdbDevice]: A list of AdbDevice instances parsed from the command output. If the `adb` command exits with a non-zero status, an empty list is returned.
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
