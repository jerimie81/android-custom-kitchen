# 🍳 Android Custom Kitchen (ACKitchen)

> A professional desktop GUI and headless CLI for Android ROM modding, APK analysis, and firmware engineering — built with PyQt5 on Debian/Ubuntu.

![Version](https://img.shields.io/badge/version-2.1-3DDC84?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Debian%20%7C%20Ubuntu-0E1620?style=flat-square)
![Python](https://img.shields.io/badge/python-3.10%2B-4FC3F7?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-3DDC84?style=flat-square)
![Tests](https://img.shields.io/badge/tests-pytest--qt-3DDC84?style=flat-square)

---

## Table of Contents

- [Overview](#overview)
- [Screenshots](#screenshots)
- [Features](#features)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Manual Setup](#manual-setup)
  - [Installing External Tools](#installing-external-tools)
  - [Debian Package](#debian-package)
- [Usage](#usage)
  - [GUI Mode](#gui-mode)
  - [CLI Mode](#cli-mode)
  - [Dashboard](#dashboard)
  - [APK Tools](#apk-tools)
  - [Firmware Tools](#firmware-tools)
  - [Setup & Prerequisites](#setup--prerequisites)
- [Configuration & Persistence](#configuration--persistence)
- [Tool Reference](#tool-reference)
- [Security Model](#security-model)
- [Project Structure](#project-structure)
- [Development](#development)
  - [Running from Source](#running-from-source)
  - [Running Tests](#running-tests)
  - [Code Style](#code-style)
  - [Adding a New Page](#adding-a-new-page)
  - [Adding a New CLI Workflow](#adding-a-new-cli-workflow)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**Android Custom Kitchen** is an open-source desktop application that wraps the most common Android firmware and APK engineering workflows into a clean, dark-themed GUI — with a fully headless `--cli` mode for scripting and CI integration. Instead of memorising long `apktool`, `jadx`, `lpmake`, and `payload-dumper-go` command lines, ACKitchen validates your inputs, constructs commands safely using argv arrays (no shell interpolation), streams output in real time to a colour-coded terminal panel, and chains multi-step operations with automatic failure propagation.

ACKitchen is specifically designed and tested on **Debian 12/13 and Ubuntu 22.04+**, the dominant host platforms for Android ROM development.

### Design Principles

- **No shell injection, ever.** All commands run via `QProcess.start(program, args)` — never joined into a shell string.
- **Settings persistence.** Every path picker and option is saved automatically via `QSettings`; your workspace is restored on the next launch.
- **Fail fast, fail cleanly.** A non-zero exit from any queued command cancels all remaining steps and surfaces an unambiguous error.
- **Dual-mode.** The same workflow logic powers both the GUI and the `--cli` flag — no code duplication between modes.

---

## Features

### APK Workflows
- **Decompile** — One-click `apktool d` to extract Smali bytecode and resources.
- **JADX Integration** — Optional side-by-side Java/Kotlin source decompilation with deobfuscation (`--deobf`), output to `jadx_sources/` alongside Smali.
- **Rebuild** — Repack a modified Smali directory back into an unsigned APK using `apktool b`.
- **Sign** — Full `zipalign` + `apksigner` workflow with password-masked keystore and key fields, followed by automatic `apksigner verify` confirmation.

### Firmware Workflows
- **OTA Payload Extraction** — Extract all partition images from an OTA `payload.bin` using `payload-dumper-go`.
- **Device-Aware Super Image Packing** — Automatically discovers `*.img` files in a directory, validates that total image size fits within the group maximum, computes per-partition sizes, and constructs the full `lpmake` argument chain for a `super.img` with configurable super size, group size, and metadata slot count.

### Platform
- **Startup Preflight Checks** — Verifies Linux runtime and presence of 8 required tools on launch. Each check reports a targeted remediation hint on failure.
- **Live Tool Status Dashboard** — Colour-coded cards for 11 tool executables, refreshable on demand.
- **Persistent Tool Path Overrides** — Point ACKitchen at non-`PATH` binaries (e.g. a locally-built `apksigner`) via the Setup page; overrides survive restarts.
- **Sequential Command Queue** — Multi-step operations run in FIFO order; a failure in any step cancels remaining steps and surfaces an error.
- **Real-Time Terminal Output** — Colour-coded log panel (stdout=blue-grey, stderr=orange, info=cyan, ok=green, fail=red) with 6,000-line rolling buffer and manual clear.
- **Process Control** — Stop any running operation instantly; the runner kills the subprocess, clears the queue, and re-enables all controls.
- **CLI Mode** — Full headless workflow execution via `android-custom-kitchen --cli <workflow>` for scripting and CI.
- **Guided Setup** — One-click `apt-get` installation of all Debian/Ubuntu dependencies, plus automated binary download of `payload-dumper-go` and `jadx` via `installers.py`.

---

## Architecture

ACKitchen is a deliberately small, modular Python package. Every concern is isolated:

```
ackitchen/
├── entry.py           — Dispatch: GUI vs --cli mode
├── app.py             — QApplication bootstrap, font selection, stylesheet injection
├── cli.py             — argparse CLI frontend; mirrors all GUI workflows
├── main_window.py     — Top-level window, sidebar navigation, splitter layout
├── pages/
│   ├── __init__.py
│   ├── base.py        — PageBase: shared header, scroll area, _register_run helper
│   ├── dashboard_page.py  — Tool status cards + preflight results
│   ├── apk_page.py    — Decompile / Rebuild / Sign tabs
│   ├── firmware_page.py   — Extract Payload / Pack Super tabs
│   ├── setup_page.py  — Apt install + tool path overrides
│   └── about_page.py
├── runner.py          — QProcess command queue (argv-safe, no shell)
├── workflows.py       — Pure functions: input validation → List[CommandSpec]
├── preflight.py       — OS/tool checks run at startup
├── settings_store.py  — QSettings wrapper; bind_line_edit / bind_checkbox
├── installers.py      — Binary downloader for jadx + payload-dumper-go
├── styles.py          — Color constants + global Qt stylesheet
└── widgets.py         — FilePicker, SavePicker, LogPanel, helpers
```

### Workflow Layering

```
┌─────────────────────────────────────────────┐
│  GUI Pages / CLI argparse                   │  ← user interaction
├─────────────────────────────────────────────┤
│  workflows.py  (pure, testable)             │  ← input validation → CommandSpec list
├─────────────────────────────────────────────┤
│  CommandRunner (QProcess, argv-safe queue)  │  ← execution engine
├─────────────────────────────────────────────┤
│  External tools: apktool, jadx, lpmake …   │  ← actual work
└─────────────────────────────────────────────┘
```

`workflows.py` functions are **pure**: they accept strings, validate, and return `List[CommandSpec]`. They never spawn processes. This makes them trivially unit-testable without Qt or the filesystem.

### Command Execution Model

All commands are executed by `CommandRunner` using `QProcess.start(program, args)` — never `QProcess.startDetached(shell_string)` or Python's `subprocess` with `shell=True`. This means:

- No shell metacharacter injection is possible regardless of what paths users enter.
- Arguments with spaces or quotes are displayed safely (repr-quoted in the log) but passed verbatim to the OS.
- Stdout and stderr are read asynchronously via Qt signals and streamed line-by-line to the log panel without blocking the UI thread.

---

## Requirements

### System
| Requirement | Version |
|---|---|
| OS | Debian 11+ / Ubuntu 20.04+ (Linux required for firmware tools) |
| Python | 3.10 or newer |
| PyQt5 | 5.15+ |

### External Tools

ACKitchen is a GUI/CLI front-end — the tools below must be separately installed. The **Dashboard** page shows which are present on `PATH` and the **Setup** page installs the `apt`-available subset automatically.

| Tool | Source | Purpose | Auto-installed |
|---|---|---|---|
| `apktool` | `apt` / [apktool.org](https://apktool.org) | APK decompile / rebuild | ✅ apt |
| `jadx` | [GitHub Releases](https://github.com/skylot/jadx/releases) | Java/Kotlin decompilation | ✅ binary |
| `apksigner` | Android Build Tools | APK signing (v2/v3) | ❌ manual |
| `zipalign` | Android Build Tools | APK alignment before signing | ❌ manual |
| `adb` | `apt` (`android-tools-adb`) | Android Debug Bridge | ✅ apt |
| `fastboot` | `apt` (`android-tools-fastboot`) | Bootloader/partition flashing | ✅ apt |
| `payload-dumper-go` | [GitHub Releases](https://github.com/ssut/payload-dumper-go/releases) | OTA payload.bin extraction | ✅ binary |
| `lpunpack` | `apt` (`android-sdk-libsparse-utils`) | Dynamic partition unpack | ✅ apt |
| `lpmake` | `apt` (`android-sdk-libsparse-utils`) | Dynamic partition repack | ✅ apt |
| `mkbootimg` | AOSP build tools | Boot image repack | ❌ manual |
| `unpack_bootimg` | AOSP build tools | Boot image unpack | ❌ manual |
| `fsck.erofs` | `apt` (`erofs-utils`) | EROFS filesystem (Android 12+) | ✅ apt |

---

## Installation

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourname/android-custom-kitchen.git
cd android-custom-kitchen

# 2. Create and activate a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install PyQt5

# 4. Launch GUI
python3 android-custom-kitchen-gui.py

# Or launch CLI
python3 android-custom-kitchen-gui.py --cli --help
```

Then use the **Setup** page inside the app to install all `apt`-available tools with a single click.

---

### Manual Setup

If you prefer to install dependencies before launching:

```bash
sudo apt-get update
sudo apt-get install -y \
    git curl unzip xz-utils file jq python3-pip openjdk-17-jdk \
    build-essential clang cmake ninja-build \
    e2fsprogs erofs-utils \
    android-tools-adb android-tools-fastboot \
    apktool android-sdk-libsparse-utils
```

---

### Installing External Tools

#### JADX (Java/Kotlin Decompiler)

```bash
JADX_VER=$(curl -s https://api.github.com/repos/skylot/jadx/releases/latest | grep tag_name | cut -d'"' -f4)
wget "https://github.com/skylot/jadx/releases/download/${JADX_VER}/jadx-${JADX_VER}.zip" -O /tmp/jadx.zip
sudo unzip /tmp/jadx.zip -d /opt/jadx
sudo ln -sf /opt/jadx/bin/jadx /usr/local/bin/jadx
```

Or use the **Setup** page — ACKitchen's built-in `installers.py` handles this automatically.

#### payload-dumper-go (OTA Extractor)

```bash
PD_VER=$(curl -s https://api.github.com/repos/ssut/payload-dumper-go/releases/latest | grep tag_name | cut -d'"' -f4)
wget "https://github.com/ssut/payload-dumper-go/releases/download/${PD_VER}/payload-dumper-go_${PD_VER}_linux_amd64.tar.gz" -O /tmp/pdg.tar.gz
tar -xzf /tmp/pdg.tar.gz -C /tmp
sudo mv /tmp/payload-dumper-go /usr/local/bin/
sudo chmod +x /usr/local/bin/payload-dumper-go
```

Or use the **Setup** page — handled automatically.

#### Android SDK Build Tools (apksigner, zipalign)

```bash
# Install via sdkmanager (requires Android SDK commandline tools)
sdkmanager "build-tools;34.0.0"
export PATH="$ANDROID_HOME/build-tools/34.0.0:$PATH"
```

Or download the standalone APK signing tools from [Android Studio](https://developer.android.com/studio) and add the `build-tools/` directory to your `PATH`. Once installed, point ACKitchen at the binary via **Setup → Tool Path Overrides**.

---

### Debian Package

To build and install a `.deb`:

```bash
sudo apt-get install devscripts debhelper dh-python pybuild-plugin-pyproject
dpkg-buildpackage -us -uc -b
sudo dpkg -i ../android-custom-kitchen_2.1.0-1_all.deb
# Then launch with:
android-custom-kitchen
```

---

## Usage

### GUI Mode

```bash
python3 android-custom-kitchen-gui.py
# or if installed via pip / .deb:
android-custom-kitchen
```

### CLI Mode

```bash
android-custom-kitchen --cli <workflow> [options]

# Available workflows:
android-custom-kitchen --cli apk-decompile --apk app.apk --out ./decompiled [--jadx]
android-custom-kitchen --cli apk-rebuild   --dir ./decompiled --out app-modified.apk
android-custom-kitchen --cli apk-sign      --in app-unsigned.apk --out app-signed.apk \
                                            --keystore release.jks --alias key0 \
                                            --keystore-pass hunter2 [--key-pass hunter2]
android-custom-kitchen --cli firmware-extract --payload payload.bin --out ./images
android-custom-kitchen --cli firmware-pack-super \
                                            --partitions ./images --out super_new.img \
                                            --super-size 3221225472 \
                                            --group-size 3221225472 \
                                            --metadata-size 65536
android-custom-kitchen --cli setup
```

All CLI workflows exit `0` on success, `1` on command failure, and `2` on invalid arguments. They are safe to use in shell scripts and CI pipelines.

---

### Dashboard

The Dashboard loads automatically on startup and shows two panels:

**Installed Tools** — A grid of 11 tool cards. Each card has a coloured status dot:
- 🟢 Green dot + green border — tool found on `PATH` (or overridden path)
- 🔴 Red dot + red border — tool not found

Click **⟳ Refresh Status** after installing tools to update the display without restarting.

**Startup Preflight** — A checklist run once on launch:
- ✔ Linux runtime detected
- ✔/✖ for each critical tool, with a specific remediation hint on failure

---

### APK Tools

Navigate to **📦 APK Tools** in the sidebar.

#### Decompile Tab

| Field | Description |
|---|---|
| APK File | Path to the `.apk` you want to analyse |
| Output Directory | Where Smali + resources will be written |
| Also decompile with JADX | Produces deobfuscated Java/Kotlin sources in `<output>/jadx_sources/` |

Click **▶ Run Decompile**. If `apktool` fails, `jadx` is skipped automatically.

#### Rebuild Tab

| Field | Description |
|---|---|
| Decompiled Directory | Folder previously created by decompile (contains `AndroidManifest.xml`, `smali/`, `res/`) |
| Output APK Path | Where the unsigned rebuilt APK will be saved |

Output is an **unsigned APK** — proceed to the Sign tab before installing.

#### Sign Tab

| Field | Description |
|---|---|
| Unsigned APK | Path to the APK to sign (e.g. output of Rebuild) |
| Signed APK Output | Destination for the signed APK |
| Keystore (.jks/.keystore) | Path to your signing keystore |
| Key Alias | Alias for the signing key within the keystore |
| Keystore Password | Password protecting the keystore (masked) |
| Key Password | Per-key password if different from keystore (masked, optional) |

The Sign workflow runs `apksigner sign` followed automatically by `apksigner verify --verbose` to confirm the signature is valid before finishing.

> **Note:** Always sign with a key that matches the installed app on the target device, or uninstall first. Android enforces signature consistency across updates.

---

### Firmware Tools

Navigate to **💾 Firmware** in the sidebar.

#### Extract Payload Tab

| Field | Description |
|---|---|
| payload.bin | Path to the `payload.bin` file from an OTA zip |
| Output Directory | Where extracted `.img` files will be written |

Requires `payload-dumper-go` on `PATH`. See [Installation](#installing-external-tools).

#### Pack Super Tab

| Field | Description |
|---|---|
| Partitions Directory | Directory containing `*.img` files (`system.img`, `vendor.img`, `product.img`, etc.) |
| Output super.img | Path for the output image |
| Super size bytes | Total super partition size in bytes |
| Group max size bytes | Maximum bytes for the main partition group (usually equals super size) |
| Metadata size bytes | Metadata partition size in bytes (default: 65536) |

ACKitchen auto-discovers all `*.img` files in the chosen directory and validates that their combined size fits within the group maximum before invoking `lpmake`. It **rejects the operation** if the images are too large, rather than letting `lpmake` fail with a cryptic error.

> ⚠️ **Device-specific sizes are critical.** Writing a `super.img` larger than the target device's super partition will corrupt the partition table. Always verify sizes from a live device:
> ```bash
> adb root
> adb shell lpdump /dev/block/by-name/super | grep -E "Metadata|Device size"
> ```

---

### Setup & Prerequisites

Navigate to **⚙️ Setup** in the sidebar.

**Tool Path Overrides** — If a tool isn't on your `PATH` (e.g. `apksigner` from a custom Android SDK location), enter its absolute path here. These paths are persisted and take precedence over `PATH` lookup everywhere in the app.

**Run Setup** — Click **▶ Run Setup (requires sudo)** to:
1. `sudo apt-get update -qq`
2. `sudo apt-get install -y -qq <packages>` for the full toolchain
3. `sudo python3 installers.py ensure-tools` to download `payload-dumper-go` and `jadx` binaries from GitHub if not already present

---

## Configuration & Persistence

ACKitchen uses Qt's `QSettings` (platform-native: `~/.config/ackitchen/android-custom-kitchen.conf` on Linux) to persist all user state automatically. You never need to manually save a project.

**Persisted values include:**
- All file picker paths (APK input/output, payload, keystore, etc.)
- Checkbox states (e.g. "use JADX")
- Numeric fields (super size, group size, metadata size)
- Tool path overrides from the Setup page

To reset all settings to defaults:
```bash
rm ~/.config/ackitchen/android-custom-kitchen.conf
```

---

## Tool Reference

### lpmake Device Layout Parameters

```bash
# On a rooted device with ADB root access:
adb root
adb shell lpdump /dev/block/by-name/super | grep -E "Metadata|Device size|Group"
```

### apktool Common Options

ACKitchen calls `apktool d <apk> -o <out> --force`. For manual use:

```bash
# Smali only (faster, no resource decoding)
apktool d app.apk -o out --no-res

# Target specific API level for resource decoding
apktool d app.apk -o out --api 33
```

### JADX Deobfuscation

ACKitchen passes `--deobf` automatically. To fine-tune manually:

```bash
# Adjust minimum name length for deobfuscation (default: 3)
jadx -d output --deobf --deobf-min-len 2 app.apk

# Generate Gradle project structure for import into Android Studio
jadx -d output --export-gradle app.apk
```

### apksigner Verification

After signing, ACKitchen automatically runs:

```bash
apksigner verify --verbose app-signed.apk
```

To check which signing schemes are active:
```bash
apksigner verify --print-certs app-signed.apk
```

---

## Security Model

ACKitchen was designed with command-injection safety as a first-class constraint:

1. **No shell execution.** All commands use `QProcess.start(program, List[str])`. Arguments are never joined into a shell string. A path like `/tmp/evil; rm -rf /` is passed as a single literal argument to the target program.

2. **No `subprocess.run(shell=True)`.** No Python subprocess calls exist anywhere in the codebase.

3. **HTML-escaped log output.** All text written to the `LogPanel` is escaped (`&`, `<`, `>` → HTML entities) before being inserted as rich text. A program that emits `<script>` tags to stdout cannot inject into the log.

4. **No API keys, no network access (at runtime).** ACKitchen makes no outbound network connections during normal operation. The `installers.py` downloader is only invoked explicitly from the Setup page or the `setup` CLI workflow.

5. **File dialogs only.** Path inputs use native OS file pickers or manual text entry — no URL loading, no arbitrary path construction from untrusted sources.

6. **Password masking.** Keystore and key passwords in the Sign tab use `QLineEdit.Password` echo mode and are never written to disk by ACKitchen.

---

## Project Structure

```
android-custom-kitchen/
├── android-custom-kitchen-gui.py   # Entry point launcher
├── pyproject.toml                  # Hatch build config; defines `android-custom-kitchen` script
├── ackitchen/
│   ├── __init__.py                 # Exports main()
│   ├── entry.py                    # GUI / --cli dispatch
│   ├── app.py                      # QApplication bootstrap
│   ├── cli.py                      # argparse CLI, mirrors GUI workflows
│   ├── main_window.py              # Main window, sidebar, splitter
│   ├── installers.py               # Binary downloader: jadx, payload-dumper-go
│   ├── preflight.py                # Startup check definitions and runner
│   ├── runner.py                   # QProcess command queue engine
│   ├── settings_store.py           # QSettings wrapper with widget binding helpers
│   ├── styles.py                   # Color constants + Qt stylesheet builder
│   ├── widgets.py                  # FilePicker, SavePicker, LogPanel, helpers
│   ├── workflows.py                # Pure input validation → CommandSpec lists
│   └── pages/
│       ├── __init__.py
│       ├── base.py                 # PageBase: scroll area, header, _register_run
│       ├── about_page.py
│       ├── apk_page.py             # Decompile / Rebuild / Sign tabs
│       ├── dashboard_page.py       # Tool grid + preflight display
│       ├── firmware_page.py        # Payload extract / Pack super tabs
│       └── setup_page.py           # Apt install + path overrides
├── tests/
│   ├── conftest.py                 # PyQt5 stub for headless test environments
│   ├── test_runner.py              # CommandRunner unit tests (FakeQProcess)
│   └── test_preflight.py           # Preflight check unit tests
├── debian/
│   ├── changelog
│   ├── control
│   ├── rules
│   └── source/format
├── README.md
└── LICENSE
```

---

## Development

### Running from Source

```bash
git clone https://github.com/yourname/android-custom-kitchen.git
cd android-custom-kitchen
python3 -m venv .venv
source .venv/bin/activate
pip install PyQt5
python3 android-custom-kitchen-gui.py
```

### Running Tests

Tests use a `conftest.py` that stubs out PyQt5, so they run on headless CI without a display:

```bash
pip install pytest
pytest tests/ -v
```

For full widget tests (requires a display):
```bash
pip install pytest pytest-qt
pytest tests/ -v
# On headless CI:
xvfb-run -a pytest tests/ -v
```

**Test layout:**

| File | What it covers |
|---|---|
| `test_runner.py` | `CommandRunner` queue sequencing, failure propagation, stop/kill |
| `test_preflight.py` | Preflight checks with monkeypatched `shutil.which` and `platform.system` |

When adding a new workflow, add a corresponding `tests/test_workflows_<name>.py` that exercises the pure `workflows.py` functions with valid and invalid inputs.

### Code Style

The project targets **Python 3.10+**. Code style:

```bash
pip install ruff black mypy

ruff check ackitchen/          # lint
black ackitchen/               # format
mypy --strict ackitchen/       # type-check
```

All three must pass clean before a PR is mergeable.

### Adding a New Page

1. Create a class inheriting from `PageBase` in `ackitchen/pages/`.
2. Call `super().__init__("Title", "Subtitle", runner, log, settings, parent)`.
3. Use `self.bl` (the body `QVBoxLayout`) to add your widgets.
4. Define workflow inputs using `FilePicker`, `SavePicker`, or `QLineEdit`, and bind them with `self.settings.bind_line_edit(widget, "your/key")` so they persist.
5. Use `self.runner.run_many(cmds)` for command execution; validate first via a `workflows.py` function.
6. Register your run button with `self._register_run(btn)` to auto-disable it during execution.
7. Export from `ackitchen/pages/__init__.py` and instantiate in `main_window.py`.

```python
# ackitchen/pages/my_page.py
class MyPage(PageBase):
    def __init__(self, runner, log, settings, parent=None):
        super().__init__("My Tool", "Description here", runner, log, settings, parent)
        self.my_input = FilePicker("Input File", "/path/to/file.bin")
        self.settings.bind_line_edit(self.my_input.edit, "mytool/input")
        self.bl.addWidget(self.my_input)
        row, run, stop = run_row("▶  Run My Tool")
        run.clicked.connect(self._do_run)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        self.bl.addLayout(row)

    def _do_run(self):
        try:
            cmds = my_workflow_commands(self.my_input.value(), tools={...})
        except WorkflowError as exc:
            self.log.append(f"✖  {exc}", "fail")
            return
        self.runner.run_many(cmds)
```

### Adding a New CLI Workflow

1. Add the pure command builder to `workflows.py`.
2. Add a subparser in `cli.py`'s `build_parser()`.
3. Handle the new `args.workflow` branch in `run_cli()`.
4. The same `WorkflowError` handling pattern applies — the CLI will print the error and exit `2`.

---

## Troubleshooting

### App won't launch: `ModuleNotFoundError: No module named 'PyQt5'`
```bash
pip install PyQt5
# or system-wide on Debian/Ubuntu:
sudo apt-get install python3-pyqt5
```

### Dashboard shows all tools as missing after installing them
Click **⟳ Refresh Status** or restart the app. PATH is evaluated at runtime; newly installed tools are detected on refresh.

### `apktool` fails with `brut.androlib.AndrolibException`
Your `apktool` version doesn't support the APK's resource format. Update it:
```bash
sudo apt-get install --only-upgrade apktool
# or install the latest jar from https://apktool.org
```

### `payload-dumper-go` not found after Setup installed it
Ensure `/usr/local/bin` is on your `PATH`:
```bash
echo $PATH | grep -q '/usr/local/bin' || echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### `lpmake` fails: `error: partition ... is too large`
The total size of your partition images exceeds the `Super size bytes` value. Either increase the super size to match your device's actual super partition (check with `lpdump`), or the source images are from a different device.

### Sign workflow fails: `DOES_NOT_VERIFY` or `Failed to verify`
- Ensure the unsigned APK was built with `apktool b` without errors.
- Check that the keystore alias and passwords are correct.
- Try manually: `apksigner verify --verbose app-signed.apk`

### JADX decompilation produces empty or minimal output
Some heavily obfuscated APKs produce minimal output. Try without `--deobf`:
```bash
jadx -d output/ app.apk
```

### Qt plugin error: `Could not load the Qt platform plugin "xcb"`
```bash
sudo apt-get install libxcb-xinerama0 libxcb-icccm4 libxcb-image0 \
    libxcb-keysyms1 libxcb-randr0 libxcb-render-util0
```

### CLI exits immediately with no output
Ensure the workflow name is spelled correctly (`apk-decompile`, not `apk_decompile`). Run `--help` for the full usage:
```bash
android-custom-kitchen --cli --help
android-custom-kitchen --cli apk-decompile --help
```

---

## Roadmap

### v2.2 — Stability & Input Hardening
- [ ] **QIntValidator on numeric fields** — Reject non-integer input in the Super Pack tab at the widget level before any command runs
- [ ] **Async preflight** — Move dashboard tool checks to a `QThread` worker for non-blocking startup
- [ ] **Zipalign in Sign workflow** — Add automatic `zipalign -v 4` step before `apksigner` in the Sign tab
- [ ] **Session restore** — Restore last-used paths from `QSettings` into all pickers on startup (already half-implemented via `bind_line_edit`)
- [ ] **Expanded test coverage** — `pytest-qt` tests for `workflows.py` (parametrized valid/invalid inputs) and `settings_store.py`

### v2.3 — Device Integration
- [ ] **ADB Device Panel** — Live connected device list with auto-refresh via `adb devices`, device selector for ADB operations
- [ ] **Boot Image Unpack/Repack** — GUI around `unpack_bootimg` + `mkbootimg` with kernel/ramdisk pickers
- [ ] **Direct Device Pull** — Pull APKs from connected device via `adb shell pm path` + `adb pull`
- [ ] **Project Files** — `.ackit` project format (TOML) saving all workflow paths and device parameters for reproducible sessions

### v3.0 — Platform
- [ ] **Plugin Architecture** — Auto-discovered page plugins from `~/.config/ACKitchen/plugins/`
- [ ] **Magisk / KernelSU Patch** — One-click boot image patching workflow
- [ ] **Smali Syntax Highlighting** — `QSyntaxHighlighter` for Smali with opcode, register, and label colouring
- [ ] **ROM Diff View** — Compare two decompiled APK trees side-by-side to identify changes between versions
- [ ] **Script Recorder** — Capture a GUI session as a reproducible shell script or CLI command sequence
- [ ] **AppImage packaging** — Self-contained Linux AppImage alongside the `.deb`

---

## Contributing

Contributions are welcome. Please follow these steps:

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feature/my-improvement
   ```

2. **Code standards**: run `ruff check`, `black`, and `mypy --strict` before committing. All three must pass clean.

3. **Tests**: add `pytest` or `pytest-qt` tests for:
   - Any new `workflows.py` function (minimum: valid inputs, missing-field error, tool-not-found path)
   - Any new `CommandRunner` logic

4. **Command safety**: never use `shell=True`, `os.system()`, or f-string command construction. All subprocess arguments must be separate list elements passed to `QProcess.start(program, args)` or `CommandSpec`.

5. **Settings binding**: any new user-facing field must be bound with `self.settings.bind_line_edit()` or `self.settings.bind_checkbox()` so its value persists across sessions.

6. **PR description**: explain what workflow the change supports and include a screenshot if it modifies the UI.

### Reporting Bugs

Open a GitHub issue and include:
- ACKitchen version (`About` page or `android-custom-kitchen --cli --help`)
- OS and version (`uname -a`)
- Terminal Output panel content (copy via right-click)
- Steps to reproduce
- Whether the issue reproduces in `--cli` mode (helps isolate GUI vs logic bugs)

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built for Android ROM developers on Debian/Ubuntu.<br>
<strong>ACKitchen</strong> — because modding Android shouldn't require memorising 40-flag command lines.

</div>
