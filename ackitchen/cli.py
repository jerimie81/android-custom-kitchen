from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PyQt5.QtCore import QCoreApplication

from .runner import CommandRunner
from .settings_store import SettingsStore
from .workflows import (
    WorkflowError,
    apk_decompile_commands,
    apk_rebuild_commands,
    apk_sign_commands,
    firmware_extract_payload_commands,
    firmware_pack_super_commands,
    setup_commands,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="android-custom-kitchen", description="Headless Android Custom Kitchen workflows")
    sub = parser.add_subparsers(dest="workflow", required=True)

    d = sub.add_parser("apk-decompile", help="Decompile APK with apktool (optionally jadx)")
    d.add_argument("--apk", required=True)
    d.add_argument("--out", required=True)
    d.add_argument("--jadx", action="store_true")

    r = sub.add_parser("apk-rebuild", help="Rebuild APK from decompiled directory")
    r.add_argument("--dir", required=True, dest="decompiled_dir")
    r.add_argument("--out", required=True)

    s = sub.add_parser("apk-sign", help="Sign APK with apksigner")
    s.add_argument("--in", required=True, dest="input_apk")
    s.add_argument("--out", required=True, dest="output_apk")
    s.add_argument("--keystore", required=True)
    s.add_argument("--alias", required=True)
    s.add_argument("--keystore-pass", required=True)
    s.add_argument("--key-pass", default="")

    p = sub.add_parser("firmware-extract", help="Extract OTA payload.bin")
    p.add_argument("--payload", required=True)
    p.add_argument("--out", required=True)

    sp = sub.add_parser("firmware-pack-super", help="Build super.img from partition images")
    sp.add_argument("--partitions", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--super-size", default="3221225472")
    sp.add_argument("--group-size", default="3221225472")
    sp.add_argument("--metadata-size", default="65536")

    sub.add_parser("setup", help="Install prerequisite tools")
    return parser


def _run_commands(commands) -> int:
    app = QCoreApplication.instance() or QCoreApplication(sys.argv)
    runner = CommandRunner()
    result = {"ok": True}

    def on_line(line: str, _kind: str):
        print(line, flush=True)

    def on_finish(ok: bool):
        result["ok"] = ok
        app.quit()

    runner.line_out.connect(on_line)
    runner.finished.connect(on_finish)
    runner.run_many(commands)
    app.exec_()
    return 0 if result["ok"] else 1


def run_cli(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = SettingsStore()
    tools = {
        "apktool": settings.resolve_tool("apktool"),
        "jadx": settings.resolve_tool("jadx"),
        "apksigner": settings.resolve_tool("apksigner"),
        "payload-dumper-go": settings.resolve_tool("payload-dumper-go"),
        "lpmake": settings.resolve_tool("lpmake"),
    }

    try:
        if args.workflow == "apk-decompile":
            commands = apk_decompile_commands(args.apk, args.out, args.jadx, tools)
        elif args.workflow == "apk-rebuild":
            commands = apk_rebuild_commands(args.decompiled_dir, args.out, tools)
        elif args.workflow == "apk-sign":
            commands = apk_sign_commands(
                args.input_apk,
                args.output_apk,
                args.keystore,
                args.alias,
                args.keystore_pass,
                args.key_pass,
                tools,
            )
        elif args.workflow == "firmware-extract":
            commands = firmware_extract_payload_commands(args.payload, args.out, tools)
        elif args.workflow == "firmware-pack-super":
            commands = firmware_pack_super_commands(
                partition_dir=args.partitions,
                output_super=args.out,
                super_size=args.super_size,
                group_size=args.group_size,
                metadata_size=args.metadata_size,
                tools=tools,
            )
        elif args.workflow == "setup":
            installer_script = str(Path(__file__).with_name("installers.py"))
            commands = setup_commands(installer_script)
        else:
            parser.error(f"Unknown workflow: {args.workflow}")
            return 2
    except WorkflowError as exc:
        print(f"✖  {exc}", file=sys.stderr)
        return 2

    return _run_commands(commands)
