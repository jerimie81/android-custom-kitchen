from __future__ import annotations

import json
import os
import shutil
import stat
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path


def _download_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "ackitchen-setup"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _download_file(url: str, out_path: Path):
    req = urllib.request.Request(url, headers={"User-Agent": "ackitchen-setup"})
    with urllib.request.urlopen(req, timeout=60) as resp, out_path.open("wb") as fh:
        fh.write(resp.read())


def _pick_asset(assets: list[dict], include: list[str], exclude: list[str]) -> dict | None:
    for asset in assets:
        name = (asset.get("name") or "").lower()
        if all(token in name for token in include) and not any(token in name for token in exclude):
            return asset
    return None


def install_payload_dumper_go() -> int:
    data = _download_json("https://api.github.com/repos/ssut/payload-dumper-go/releases/latest")
    asset = _pick_asset(data.get("assets", []), include=["linux", "amd64"], exclude=["sha", "sig"])
    if not asset:
        raise RuntimeError("Unable to find a Linux amd64 payload-dumper-go release asset.")
    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        archive = tdir / asset["name"]
        _download_file(asset["browser_download_url"], archive)
        bin_target = Path("/usr/local/bin/payload-dumper-go")
        if archive.suffix == ".gz" or archive.suffix == ".tgz" or archive.name.endswith(".tar.gz"):
            with tarfile.open(archive) as tf:
                tf.extractall(tdir)
            binary = next((p for p in tdir.rglob("*") if p.name == "payload-dumper-go"), None)
            if not binary:
                raise RuntimeError("payload-dumper-go binary not found in archive.")
            shutil.copy2(binary, bin_target)
        else:
            shutil.copy2(archive, bin_target)
        bin_target.chmod(bin_target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"Installed payload-dumper-go -> {bin_target}")
    return 0


def install_jadx() -> int:
    data = _download_json("https://api.github.com/repos/skylot/jadx/releases/latest")
    asset = _pick_asset(data.get("assets", []), include=["jadx", ".zip"], exclude=["with-jre", "arm", "sha"])
    if not asset:
        raise RuntimeError("Unable to find a jadx zip release asset.")
    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        archive = tdir / "jadx.zip"
        _download_file(asset["browser_download_url"], archive)
        opt_root = Path("/opt/jadx")
        if opt_root.exists():
            shutil.rmtree(opt_root)
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(opt_root)
        jadx_sh = next((p for p in opt_root.rglob("jadx") if p.is_file()), None)
        if not jadx_sh:
            raise RuntimeError("jadx executable was not found in extracted package.")
        link = Path("/usr/local/bin/jadx")
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(jadx_sh)
    print(f"Installed jadx -> {link}")
    return 0


def ensure_tools() -> int:
    if shutil.which("payload-dumper-go") is None:
        install_payload_dumper_go()
    else:
        print("payload-dumper-go already present on PATH.")

    if shutil.which("jadx") is None:
        install_jadx()
    else:
        print("jadx already present on PATH.")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: installers.py [payload-dumper-go|jadx|ensure-tools]")
        return 2
    cmd = argv[1]
    if cmd == "payload-dumper-go":
        return install_payload_dumper_go()
    if cmd == "jadx":
        return install_jadx()
    if cmd == "ensure-tools":
        return ensure_tools()
    print(f"Unknown installer target: {cmd}")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except Exception as exc:
        print(f"Install failed: {exc}", file=sys.stderr)
        raise
