# 🍳 Android Custom Kitchen (ACKitchen)

> A professional desktop GUI for Android ROM modding, APK analysis, and firmware engineering — built with PyQt5 on Debian/Ubuntu.

![Version](https://img.shields.io/badge/version-2.1-3DDC84?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Debian%20%7C%20Ubuntu-0E1620?style=flat-square)
![Python](https://img.shields.io/badge/python-3.9%2B-4FC3F7?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-3DDC84?style=flat-square)

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
- [Usage](#usage)
  - [Dashboard](#dashboard)
  - [APK Tools](#apk-tools)
  - [Firmware Tools](#firmware-tools)
  - [Setup & Prerequisites](#setup--prerequisites)
- [Tool Reference](#tool-reference)
- [Security Model](#security-model)
- [Project Structure](#project-structure)
- [Development](#development)
  - [Running from Source](#running-from-source)
  - [Running Tests](#running-tests)
  - [Code Style](#code-style)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**Android Custom Kitchen** is an open-source desktop application that wraps the most common Android firmware and APK engineering workflows into a clean, dark-themed GUI. Instead of memorising long `apktool`, `jadx`, `lpmake`, and `payload-dumper-go` command lines, ACKitchen validates your inputs, constructs commands safely using argv arrays (no shell interpolation), streams output in real time to a colour-coded terminal panel, and chains multi-step operations with automatic failure propagation.

The application is specifically designed and tested on **Debian 12/13 and Ubuntu 22.04+**, the dominant host platforms for Android ROM development.

---

## Features

### APK Workflows
- **Decompile** — One-click `apktool d` to extract Smali bytecode and resources.
- **JADX Integration** — Optional side-by-side Java/Kotlin source decompilation with deobfuscation (`--deobf`), output to `jadx_sources/` alongside Smali.
- **Rebuild** — Repack a modified Smali directory back into an unsigned APK using `apktool b`.

### Firmware Workflows
- **OTA Payload Extraction** — Extract all partition images from an OTA `payload.bin` using `payload-dumper-go`.
- **Device-Aware Super Image Packing** — Automatically discovers `*.img` files in a directory, computes per-partition sizes, and constructs the full `lpmake` argument chain for a `super.img` with configurable super size and metadata slot count.

### Platform
- **Startup Preflight Checks** — Verifies Linux runtime and presence of 8 required tools on launch. Each check reports a targeted remediation hint on failure.
- **Live Tool Status Dashboard** — Colour-coded cards for 11 tool executables, refreshable on demand.
- **Sequential Command Queue** — Multi-step operations run in FIFO order; a failure in any step cancels remaining steps and surfaces an error.
- **Real-Time Terminal Output** — Colour-coded log panel (stdout=blue-grey, stderr=orange, info=cyan, ok=green, fail=red) with 6,000-line rolling buffer and manual clear.
- **Process Control** — Stop any running operation instantly; the runner kills the subprocess, clears the queue, and re-enables all controls.
- **Guided Setup** — One-click `apt-get` installation of all Debian/Ubuntu dependencies.

---

## Architecture

ACKitchen is a deliberately small, modular Python package. Every concern is isolated to a single file:

```
ackitchen/
├── app.py          — QApplication bootstrap, font selection, stylesheet injection
├── main_window.py  — Top-level window, sidebar navigation, splitter layout
├── pages.py        — All page classes (Dashboard, APK, Firmware, Setup, About)
├── runner.py       — QProcess-based command runner with argv safety and queue logic
├── preflight.py    — OS/tool checks run at startup
├── styles.py       — Color constants and global Qt stylesheet
└── widgets.py      — Reusable widgets: FilePicker, SavePicker, LogPanel, helpers
```

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
| Python | 3.9 or newer |
| PyQt5 | 5.15+ |

### External Tools

ACKitchen is a GUI front-end — the tools below must be separately installed. The **Dashboard** page shows which are present on `PATH` and the **Setup** page installs the `apt`-available subset automatically.

| Tool | Source | Purpose |
|---|---|---|
| `apktool` | `apt` / [apktool.org](https://apktool.org) | APK decompile / rebuild |
| `jadx` | [GitHub Releases](https://github.com/skylot/jadx/releases) | Java/Kotlin decompilation |
| `apksigner` | Android Build Tools | APK signing (v2/v3) |
| `zipalign` | Android Build Tools | APK alignment before signing |
| `adb` | `apt` (`android-tools-adb`) | Android Debug Bridge |
| `fastboot` | `apt` (`android-tools-fastboot`) | Bootloader/partition flashing |
| `payload-dumper-go` | [GitHub Releases](https://github.com/ssut/payload-dumper-go/releases) | OTA payload.bin extraction |
| `lpunpack` | `apt` (`android-sdk-libsparse-utils`) | Dynamic partition (super) unpack |
| `lpmake` | `apt` (`android-sdk-libsparse-utils`) | Dynamic partition (super) repack |
| `mkbootimg` | AOSP build tools | Boot image repack |
| `unpack_bootimg` | AOSP build tools | Boot image unpack |
| `fsck.erofs` | `apt` (`erofs-utils`) | EROFS filesystem extraction (Android 12+) |

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

# 4. Launch
python3 android-custom-kitchen-gui.py
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
# Download the latest release from GitHub
JADX_VER=$(curl -s https://api.github.com/repos/skylot/jadx/releases/latest | grep tag_name | cut -d'"' -f4)
wget "https://github.com/skylot/jadx/releases/download/${JADX_VER}/jadx-${JADX_VER}.zip" -O /tmp/jadx.zip
sudo unzip /tmp/jadx.zip -d /opt/jadx
sudo ln -sf /opt/jadx/bin/jadx /usr/local/bin/jadx
```

#### payload-dumper-go (OTA Extractor)

```bash
# Download the Linux amd64 binary from GitHub
PD_VER=$(curl -s https://api.github.com/repos/ssut/payload-dumper-go/releases/latest | grep tag_name | cut -d'"' -f4)
wget "https://github.com/ssut/payload-dumper-go/releases/download/${PD_VER}/payload-dumper-go_${PD_VER}_linux_amd64.tar.gz" -O /tmp/pdg.tar.gz
tar -xzf /tmp/pdg.tar.gz -C /tmp
sudo mv /tmp/payload-dumper-go /usr/local/bin/
sudo chmod +x /usr/local/bin/payload-dumper-go
```

#### Android SDK Build Tools (apksigner, zipalign)

```bash
# Install via sdkmanager (requires Android SDK commandline tools)
sdkmanager "build-tools;34.0.0"
# Then add to PATH:
export PATH="$ANDROID_HOME/build-tools/34.0.0:$PATH"
```

Or download the standalone APK signing tools from [Android Studio](https://developer.android.com/studio) and add the `build-tools/` directory to your `PATH`.

---

## Usage

### Dashboard

The Dashboard loads automatically on startup and shows two panels:

**Installed Tools** — A grid of 11 tool cards. Each card has a coloured status dot:
- 🟢 Green dot + green border — tool found on `PATH`
- 🔴 Red dot + red border — tool not found

Click **⟳ Refresh Status** after installing tools to update the display without restarting the app.

**Startup Preflight** — A checklist run once on launch. Each item reports:
- ✔ Linux runtime detected (required for firmware tools)
- ✔ / ✖ for each critical tool, with a specific remediation hint on failure.

---

### APK Tools

Navigate to **📦 APK Tools** in the sidebar.

#### Decompile Tab

| Field | Description |
|---|---|
| APK File | Path to the `.apk` you want to analyse |
| Output Directory | Where Smali + resources will be written |
| Also decompile with JADX | If checked, also produces deobfuscated Java/Kotlin sources in `<output>/jadx_sources/` |

Click **▶ Run Decompile**. The Terminal Output panel streams `apktool` (and optionally `jadx`) output in real time. Both commands run sequentially; if `apktool` fails, `jadx` is skipped.

#### Rebuild Tab

| Field | Description |
|---|---|
| Decompiled Directory | The folder previously created by decompile (contains `AndroidManifest.xml`, `smali/`, `res/`) |
| Output APK Path | Where the unsigned rebuilt APK will be saved |

Click **▶ Run Rebuild**. The output is an unsigned APK — sign it with `apksigner` before installing.

> **Tip:** After rebuilding, always `zipalign -v 4 app-unsigned.apk app-aligned.apk` before signing. Misaligned APKs are rejected by Android 9+ installers.

---

### Firmware Tools

Navigate to **💾 Firmware** in the sidebar.

#### Extract Payload Tab

Extracts all partition images from a factory OTA `payload.bin` (e.g. from a Google or Samsung OTA zip).

| Field | Description |
|---|---|
| payload.bin | Path to the `payload.bin` file |
| Output Directory | Directory where extracted `.img` files will be written |

Requires `payload-dumper-go` on `PATH`. See [Installation](#installing-external-tools) for setup instructions.

#### Pack Super Tab

Assembles a new `super.img` from individual partition `.img` files using `lpmake`.

| Field | Description |
|---|---|
| Partitions Directory | Directory containing `*.img` files (e.g. `system.img`, `vendor.img`, `product.img`) |
| Output super.img | Path for the output image |
| Super size bytes | Total super partition size in bytes — **verify with `lpdump /dev/block/by-name/super` on the target device** |
| Metadata size bytes | Metadata partition size in bytes (default: 65536) |

> ⚠️ **Device-specific sizes are critical.** Writing a `super.img` larger than the target device's super partition will corrupt the partition table. Always verify sizes from a live device before flashing.

The tool auto-discovers all `*.img` files in the chosen directory and includes them all as read-only partitions in the `main` group.

---

### Setup & Prerequisites

Navigate to **⚙️ Setup** in the sidebar.

Click **▶ Run Setup (requires sudo)** to run:
1. `sudo apt-get update -qq`
2. `sudo apt-get install -y -qq <packages>` for the full toolchain

This installs: `git`, `curl`, `unzip`, `jq`, `openjdk-17-jdk`, `build-essential`, `clang`, `cmake`, `ninja-build`, `e2fsprogs`, `erofs-utils`, `android-tools-adb`, `android-tools-fastboot`, `apktool`, `android-sdk-libsparse-utils`.

For tools not available via `apt` (`jadx`, `payload-dumper-go`, Android Build Tools), see [Installing External Tools](#installing-external-tools).

---

## Tool Reference

### lpmake Device Layout Parameters

To find the correct `super size` and `metadata size` for your device:

```bash
# On a rooted device with ADB root access:
adb root
adb shell lpdump /dev/block/by-name/super | grep -E "Metadata|Device size"
```

### apktool Common Options

ACKitchen calls `apktool d <apk> -o <out> --force`. Additional options you may want to run manually:

```bash
# Decompile without resources (faster, Smali only)
apktool d app.apk -o out --no-res

# Decompile specific API framework
apktool d app.apk -o out --api 33
```

### JADX Deobfuscation

ACKitchen passes `--deobf` automatically when JADX is selected. To fine-tune:

```bash
# Adjust minimum deobfuscation name length (default: 3)
jadx -d output --deobf --deobf-min-len 2 app.apk

# Generate Gradle project structure
jadx -d output --export-gradle app.apk
```

---

## Security Model

ACKitchen was designed with command-injection safety as a first-class constraint:

1. **No shell execution.** All commands use `QProcess.start(program, List[str])`. Arguments are never joined into a shell string. A path like `/tmp/evil; rm -rf /` is passed as a single literal argument to the target program, not interpreted by a shell.

2. **No `subprocess.run(shell=True)`.** No Python subprocess calls exist anywhere in the codebase.

3. **HTML-escaped log output.** All text written to the `LogPanel` is escaped (`&`, `<`, `>` → HTML entities) before being inserted as rich text. A program that emits `<script>` tags to stdout cannot inject into the log display.

4. **No API keys, no network access.** ACKitchen makes no outbound network connections. All operations are local filesystem and process invocations only.

5. **File dialogs only.** Path inputs use native OS file pickers or manual text entry — no URL loading, no arbitrary path construction from untrusted sources.

---

## Project Structure

```
android-custom-kitchen/
├── android-custom-kitchen-gui.py   # Entry point launcher
├── ackitchen/
│   ├── __init__.py                 # Package exports
│   ├── app.py                      # QApplication bootstrap
│   ├── main_window.py              # Main window, sidebar, splitter
│   ├── pages.py                    # Dashboard, APK, Firmware, Setup, About pages
│   ├── preflight.py                # Startup check definitions and runner
│   ├── runner.py                   # QProcess command queue engine
│   ├── styles.py                   # Color constants + Qt stylesheet builder
│   └── widgets.py                  # FilePicker, SavePicker, LogPanel, helpers
├── tests/                          # (planned) pytest-qt test suite
│   ├── test_runner.py
│   └── test_preflight.py
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

```bash
pip install pytest pytest-qt
pytest tests/ -v
```

> Tests require a display. On headless CI, prefix with `xvfb-run -a pytest tests/ -v`.

### Code Style

The project targets **Python 3.9+** syntax. Code style follows:
- `ruff` for linting (`ruff check ackitchen/`)
- `black` for formatting (`black ackitchen/`)
- `mypy --strict` for type checking (`mypy ackitchen/`)

Install dev tools:
```bash
pip install ruff black mypy
```

### Adding a New Page

1. Create a class inheriting from `PageBase` in `pages.py` (or a new file).
2. Call `super().__init__("Title", "Subtitle", runner, log, parent)`.
3. Use `self.bl` (the body `QVBoxLayout`) to add your widgets.
4. Use `self.runner.run_one()` / `self.runner.run_many()` for command execution.
5. Register your run button with `self._register_run(btn)` to auto-disable it during execution.
6. Add the page to `_NAV` in `main_window.py` and instantiate it in `_build_ui()`.

```python
class MyPage(PageBase):
    def __init__(self, runner, log, parent=None):
        super().__init__("My Tool", "Description here", runner, log, parent)
        self.my_input = FilePicker("Input File", "/path/to/file.bin")
        self.bl.addWidget(self.my_input)
        row, run, stop = run_row("▶  Run My Tool")
        run.clicked.connect(self._do_run)
        stop.clicked.connect(self.runner.stop)
        self._register_run(run)
        self.bl.addLayout(row)

    def _do_run(self):
        path = self.my_input.value()
        if not path:
            self.log.append("✖  Input file is required.", "fail")
            return
        self.runner.run_one("my-tool", ["--input", path])
```

---

## Troubleshooting

### App won't launch: `ModuleNotFoundError: No module named 'PyQt5'`
```bash
pip install PyQt5
# or on Debian/Ubuntu system Python:
sudo apt-get install python3-pyqt5
```

### Dashboard shows all tools as missing after installing them
Click **⟳ Refresh Status** or restart the app. The dashboard checks `PATH` at runtime — newly installed tools in the current session's `PATH` are detected on refresh.

### `apktool` fails with `brut.androlib.AndrolibException`
This usually means the APK uses a newer resource format than your `apktool` version supports. Update apktool:
```bash
sudo apt-get install --only-upgrade apktool
# or install the latest jar manually from https://apktool.org
```

### `payload-dumper-go` not found after installation
Ensure `/usr/local/bin` is on your `PATH`:
```bash
echo $PATH | grep -q '/usr/local/bin' || echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### `lpmake` fails: `error: partition ... is too large`
The total size of your partition images exceeds the `Super size bytes` value. Either increase the super size to match your device's actual super partition size (check with `lpdump`), or the source images are from a different device.

### JADX decompilation produces empty output
Some heavily obfuscated APKs produce minimal output. Try without `--deobf` by running `jadx` manually:
```bash
jadx -d output/ app.apk
```

### Qt font warnings (`Could not load the Qt platform plugin "xcb"`)
```bash
sudo apt-get install libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0
```

---

## Roadmap

The following improvements are planned for future versions:

### v2.2 — Stability & Completeness
- [ ] **APK Signing tab** — `zipalign` + `apksigner` workflow with password-masked keystore fields
- [ ] **Session persistence** — Save and restore all file picker paths between sessions using `QSettings`
- [ ] **Async preflight** — Move dashboard tool checks to a `QThread` worker for non-blocking startup
- [ ] **Input validation** — `QIntValidator` on all numeric fields; path existence checks before launching
- [ ] **JADX & payload-dumper-go setup** — Binary download/install logic in the Setup page

### v2.3 — Device Integration
- [ ] **ADB Device Panel** — Live connected device list with auto-refresh, device selection for all ADB operations
- [ ] **Boot Image Unpack/Repack** — GUI around `unpack_bootimg` + `mkbootimg` + kernel/ramdisk pickers
- [ ] **Project Files** — `.ackit` project format (TOML) saving all workflow paths and device parameters

### v3.0 — Platform
- [ ] **Plugin Architecture** — Auto-discovered page plugins from `~/.config/ACKitchen/plugins/`
- [ ] **CLI Mode** — Headless `--cli` flag for scripting and CI integration
- [ ] **Magisk/KernelSU Patch** — One-click boot image patching workflow
- [ ] **Smali Syntax Highlighting** — `QSyntaxHighlighter` for Smali with opcode and register coloring
- [ ] **Debian Package** — `.deb` installer via `dpkg-buildpackage`

---

## Contributing

Contributions are welcome. Please follow these steps:

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feature/my-improvement
   ```

2. **Code standards**: run `ruff check`, `black`, and `mypy --strict` before committing. All three must pass clean.

3. **Tests**: add `pytest-qt` tests for any new `CommandRunner` logic or pure utility functions.

4. **Command safety**: never use `shell=True`, `os.system()`, or f-string command construction. All subprocess arguments must be separate list elements passed to `QProcess.start(program, args)`.

5. **PR description**: explain what workflow the change supports and include a screenshot if it modifies the UI.

### Reporting Bugs

Open a GitHub issue and include:
- ACKitchen version (`About` page)
- OS and version (`uname -a`)
- Terminal Output panel content (copy via right-click or the Clear/copy workflow)
- Steps to reproduce

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built for Android ROM developers on Debian/Ubuntu.  
**ACKitchen** — because modding Android shouldn't require memorising 40-flag command lines.

</div>
