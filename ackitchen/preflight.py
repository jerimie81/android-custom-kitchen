from __future__ import annotations

import platform
import shutil
from dataclasses import dataclass


@dataclass
class CheckResult:
    ok: bool
    message: str
    remediation: str


def run_preflight() -> list[CheckResult]:
    out: list[CheckResult] = []
    is_linux = platform.system().lower() == "linux"
    out.append(CheckResult(is_linux, "Linux runtime detected." if is_linux else "Non-Linux runtime detected.", "Use Debian/Ubuntu for full firmware tool compatibility."))

    required = {
        "apktool": "Install with: sudo apt-get install apktool",
        "adb": "Install with: sudo apt-get install android-tools-adb",
        "fastboot": "Install with: sudo apt-get install android-tools-fastboot",
        "lpmake": "Install with: sudo apt-get install android-sdk-libsparse-utils",
        "lpunpack": "Install with: sudo apt-get install android-sdk-libsparse-utils",
        "payload-dumper-go": "Open Setup page to install payload-dumper-go binary.",
        "fsck.erofs": "Install with: sudo apt-get install erofs-utils",
        "apksigner": "Install Android build-tools and ensure apksigner is on PATH.",
    }
    for tool, fix in required.items():
        found = shutil.which(tool) is not None
        out.append(CheckResult(found, f"{tool}: {'found' if found else 'missing'}", fix))

    return out
