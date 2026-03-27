from __future__ import annotations

from pathlib import Path

from .runner import CommandSpec


class WorkflowError(ValueError):
    """Raised when workflow inputs are invalid."""


def apk_decompile_commands(apk: str, out_dir: str, use_jadx: bool, tools: dict[str, str]) -> list[CommandSpec]:
    if not apk or not out_dir:
        raise WorkflowError("APK path and output directory are required.")
    commands = [CommandSpec(tools["apktool"], ["d", apk, "-o", out_dir, "--force"])]
    if use_jadx:
        commands.append(CommandSpec(tools["jadx"], ["-d", str(Path(out_dir) / "jadx_sources"), "--deobf", apk]))
    return commands


def apk_rebuild_commands(decompiled_dir: str, output_apk: str, tools: dict[str, str]) -> list[CommandSpec]:
    if not decompiled_dir or not output_apk:
        raise WorkflowError("Both fields are required.")
    return [CommandSpec(tools["apktool"], ["b", decompiled_dir, "-o", output_apk, "--force"])]


def apk_sign_commands(
    input_apk: str,
    output_apk: str,
    keystore: str,
    alias: str,
    keystore_password: str,
    key_password: str,
    tools: dict[str, str],
) -> list[CommandSpec]:
    if not input_apk or not output_apk or not keystore or not alias or not keystore_password:
        raise WorkflowError("Unsigned APK, output path, keystore, alias, and keystore password are required.")
    signer = tools["apksigner"]
    args = [
        "sign",
        "--ks",
        keystore,
        "--ks-key-alias",
        alias,
        "--ks-pass",
        f"pass:{keystore_password}",
        "--out",
        output_apk,
    ]
    if key_password:
        args.extend(["--key-pass", f"pass:{key_password}"])
    args.append(input_apk)
    return [CommandSpec(signer, args), CommandSpec(signer, ["verify", "--verbose", output_apk])]


def firmware_extract_payload_commands(payload_bin: str, output_dir: str, tools: dict[str, str]) -> list[CommandSpec]:
    if not payload_bin or not output_dir:
        raise WorkflowError("Both fields are required.")
    return [CommandSpec(tools["payload-dumper-go"], ["-o", output_dir, payload_bin])]


def firmware_pack_super_commands(
    partition_dir: str,
    output_super: str,
    super_size: str,
    group_size: str,
    metadata_size: str,
    tools: dict[str, str],
) -> list[CommandSpec]:
    d = Path(partition_dir)
    if not d.exists() or not output_super:
        raise WorkflowError("Valid partition directory and output file are required.")

    images = sorted(p for p in d.glob("*.img") if p.is_file())
    if not images:
        raise WorkflowError("No *.img partitions found in directory.")

    try:
        total = sum(p.stat().st_size for p in images)
        if int(group_size) < total:
            raise WorkflowError(f"Group max size ({group_size}) must be >= total partition bytes ({total}).")
        int(super_size)
        int(metadata_size)
    except OSError as exc:
        raise WorkflowError(f"Failed to read image size: {exc}") from exc
    except ValueError as exc:
        raise WorkflowError("Super/group/metadata sizes must be integer byte values.") from exc

    args = [
        "--metadata-size",
        metadata_size,
        "--super-name",
        "super",
        "--metadata-slots",
        "2",
        "--device",
        f"super:{super_size}",
        "--group",
        f"main:{group_size}",
    ]
    for img in images:
        part = img.stem
        size = str(img.stat().st_size)
        args.extend(["--partition", f"{part}:readonly:{size}", "--image", f"{part}={str(img)}"])
    args.extend(["-o", output_super])
    return [CommandSpec(tools["lpmake"], args)]


def setup_commands(installer_script: str) -> list[CommandSpec]:
    pkgs = [
        "git",
        "curl",
        "unzip",
        "xz-utils",
        "file",
        "jq",
        "python3-pip",
        "openjdk-17-jdk",
        "build-essential",
        "clang",
        "cmake",
        "ninja-build",
        "e2fsprogs",
        "erofs-utils",
        "android-tools-adb",
        "android-tools-fastboot",
        "apktool",
        "android-sdk-libsparse-utils",
        "jadx",
    ]
    return [
        CommandSpec("sudo", ["apt-get", "update", "-qq"]),
        CommandSpec("sudo", ["apt-get", "install", "-y", "-qq", *pkgs]),
        CommandSpec("sudo", ["python3", installer_script, "ensure-tools"]),
    ]
