from __future__ import annotations

from pathlib import Path

import pytest

from ackitchen.runner import CommandSpec
from ackitchen.workflows import (
    WorkflowError,
    apk_decompile_commands,
    apk_rebuild_commands,
    apk_sign_commands,
    firmware_extract_payload_commands,
    firmware_pack_super_commands,
    setup_commands,
)


@pytest.fixture
def tools() -> dict[str, str]:
    return {
        "apktool": "/opt/tools/apktool",
        "jadx": "/opt/tools/jadx",
        "apksigner": "/opt/tools/apksigner",
        "payload-dumper-go": "/opt/tools/payload-dumper-go",
        "lpmake": "/opt/tools/lpmake",
    }


@pytest.mark.parametrize(
    ("apk", "out_dir"),
    [
        ("", "out"),
        ("in.apk", ""),
    ],
)
def test_apk_decompile_commands_rejects_missing_required_fields(apk, out_dir, tools):
    with pytest.raises(
        WorkflowError, match="APK path and output directory are required"
    ):
        apk_decompile_commands(apk, out_dir, use_jadx=False, tools=tools)


@pytest.mark.parametrize("use_jadx", [False, True])
def test_apk_decompile_commands_builds_expected_commands(use_jadx, tools):
    commands = apk_decompile_commands(
        "app.apk", "decoded", use_jadx=use_jadx, tools=tools
    )

    expected = [
        CommandSpec(tools["apktool"], ["d", "app.apk", "-o", "decoded", "--force"])
    ]
    if use_jadx:
        expected.append(
            CommandSpec(
                tools["jadx"],
                ["-d", str(Path("decoded") / "jadx_sources"), "--deobf", "app.apk"],
            )
        )
    assert commands == expected


@pytest.mark.parametrize(
    ("decompiled_dir", "output_apk"),
    [
        ("", "out.apk"),
        ("decoded", ""),
    ],
)
def test_apk_rebuild_commands_rejects_missing_required_fields(
    decompiled_dir, output_apk, tools
):
    with pytest.raises(WorkflowError, match="Both fields are required"):
        apk_rebuild_commands(decompiled_dir, output_apk, tools)


def test_apk_rebuild_commands_returns_single_apktool_command(tools):
    commands = apk_rebuild_commands("decoded", "rebuilt.apk", tools)

    assert commands == [
        CommandSpec(tools["apktool"], ["b", "decoded", "-o", "rebuilt.apk", "--force"]),
    ]


@pytest.mark.parametrize(
    ("input_apk", "output_apk", "keystore", "alias", "keystore_password"),
    [
        ("", "signed.apk", "k.jks", "release", "pw"),
        ("unsigned.apk", "", "k.jks", "release", "pw"),
        ("unsigned.apk", "signed.apk", "", "release", "pw"),
        ("unsigned.apk", "signed.apk", "k.jks", "", "pw"),
        ("unsigned.apk", "signed.apk", "k.jks", "release", ""),
    ],
)
def test_apk_sign_commands_rejects_missing_required_fields(
    input_apk,
    output_apk,
    keystore,
    alias,
    keystore_password,
    tools,
):
    with pytest.raises(
        WorkflowError,
        match="Unsigned APK, output path, keystore, alias, and keystore password are required",
    ):
        apk_sign_commands(
            input_apk,
            output_apk,
            keystore,
            alias,
            keystore_password,
            key_password="keypw",
            tools=tools,
        )


@pytest.mark.parametrize("key_password", ["", "keypw"])
def test_apk_sign_commands_adds_optional_key_pass_conditionally(key_password, tools):
    commands = apk_sign_commands(
        input_apk="unsigned.apk",
        output_apk="signed.apk",
        keystore="release.jks",
        alias="release",
        keystore_password="storepw",
        key_password=key_password,
        tools=tools,
    )

    assert len(commands) == 2
    sign_cmd, verify_cmd = commands
    assert sign_cmd.program == tools["apksigner"]
    assert verify_cmd == CommandSpec(
        tools["apksigner"], ["verify", "--verbose", "signed.apk"]
    )

    assert "--ks" in sign_cmd.args
    assert "--ks-key-alias" in sign_cmd.args
    assert "--ks-pass" in sign_cmd.args
    assert sign_cmd.args[-1] == "unsigned.apk"

    if key_password:
        assert "--key-pass" in sign_cmd.args
        assert f"pass:{key_password}" in sign_cmd.args
    else:
        assert "--key-pass" not in sign_cmd.args


@pytest.mark.parametrize(
    ("payload_bin", "output_dir"),
    [
        ("", "out"),
        ("payload.bin", ""),
    ],
)
def test_firmware_extract_payload_commands_rejects_missing_required_fields(
    payload_bin, output_dir, tools
):
    with pytest.raises(WorkflowError, match="Both fields are required"):
        firmware_extract_payload_commands(payload_bin, output_dir, tools)


def test_firmware_extract_payload_commands_returns_expected_command(tools):
    commands = firmware_extract_payload_commands("payload.bin", "out", tools)

    assert commands == [
        CommandSpec(tools["payload-dumper-go"], ["-o", "out", "payload.bin"])
    ]


def test_firmware_pack_super_commands_rejects_nonexistent_partition_dir(
    tmp_path, tools
):
    missing = tmp_path / "does-not-exist"

    with pytest.raises(
        WorkflowError, match="Valid partition directory and output file are required"
    ):
        firmware_pack_super_commands(
            str(missing), "super.img", "1024", "512", "4096", tools
        )


@pytest.mark.parametrize("output_super", ["", None])
def test_firmware_pack_super_commands_rejects_missing_output_super(
    tmp_path, output_super, tools
):
    part_dir = tmp_path / "parts"
    part_dir.mkdir()
    (part_dir / "system.img").write_bytes(b"1234")

    with pytest.raises(
        WorkflowError, match="Valid partition directory and output file are required"
    ):
        firmware_pack_super_commands(
            str(part_dir), output_super, "1024", "512", "4096", tools
        )


def test_firmware_pack_super_commands_rejects_directory_without_images(tmp_path, tools):
    part_dir = tmp_path / "parts"
    part_dir.mkdir()
    (part_dir / "README.txt").write_text("no images")

    with pytest.raises(
        WorkflowError, match=r"No \*\.img partitions found in directory"
    ):
        firmware_pack_super_commands(
            str(part_dir), "super.img", "1024", "512", "4096", tools
        )


def test_firmware_pack_super_commands_group_too_small_currently_maps_to_integer_error(
    tmp_path, tools
):
    part_dir = tmp_path / "parts"
    part_dir.mkdir()
    (part_dir / "system.img").write_bytes(b"1234")
    (part_dir / "vendor.img").write_bytes(b"1234")

    with pytest.raises(
        WorkflowError, match="Super/group/metadata sizes must be integer byte values"
    ):
        firmware_pack_super_commands(
            str(part_dir), "super.img", "999", "7", "4096", tools
        )


@pytest.mark.parametrize(
    ("super_size", "group_size", "metadata_size"),
    [
        ("not-int", "8", "4096"),
        ("1024", "not-int", "4096"),
        ("1024", "8", "not-int"),
    ],
)
def test_firmware_pack_super_commands_rejects_non_integer_sizes(
    tmp_path, super_size, group_size, metadata_size, tools
):
    part_dir = tmp_path / "parts"
    part_dir.mkdir()
    (part_dir / "system.img").write_bytes(b"1234")

    with pytest.raises(
        WorkflowError, match="Super/group/metadata sizes must be integer byte values"
    ):
        firmware_pack_super_commands(
            str(part_dir), "super.img", super_size, group_size, metadata_size, tools
        )


def test_firmware_pack_super_commands_returns_lpmake_command_with_sorted_partitions(
    tmp_path, tools
):
    part_dir = tmp_path / "parts"
    part_dir.mkdir()
    (part_dir / "vendor.img").write_bytes(b"12")
    (part_dir / "system.img").write_bytes(b"1234")

    commands = firmware_pack_super_commands(
        str(part_dir), "super.img", "8192", "4096", "65536", tools
    )

    assert len(commands) == 1
    command = commands[0]
    assert command.program == tools["lpmake"]
    assert command.args[:12] == [
        "--metadata-size",
        "65536",
        "--super-name",
        "super",
        "--metadata-slots",
        "2",
        "--device",
        "super:8192",
        "--group",
        "main:4096",
        "--partition",
        "system:readonly:4",
    ]
    assert "--partition" in command.args
    system_image_arg = next(arg for arg in command.args if arg.startswith("system="))
    vendor_image_arg = next(arg for arg in command.args if arg.startswith("vendor="))
    assert "system=" in system_image_arg
    assert "vendor=" in vendor_image_arg
    assert command.args[-2:] == ["-o", "super.img"]
    assert system_image_arg.endswith("system.img")


def test_setup_commands_returns_expected_install_sequence():
    commands = setup_commands("/tmp/installers.py")

    assert commands == [
        CommandSpec("sudo", ["apt-get", "update", "-qq"]),
        CommandSpec(
            "sudo",
            [
                "apt-get",
                "install",
                "-y",
                "-qq",
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
            ],
        ),
        CommandSpec("sudo", ["python3", "/tmp/installers.py", "ensure-tools"]),
    ]
