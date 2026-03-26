# 🍳 Android Custom Kitchen

> **A professional GUI for Android firmware engineering and APK reverse engineering — built for Debian/Ubuntu.**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/UI-PyQt5-41CD52?style=flat-square)](https://pypi.org/project/PyQt5/)
[![Platform](https://img.shields.io/badge/Platform-Debian%20%7C%20Ubuntu-E95420?style=flat-square&logo=ubuntu)](https://ubuntu.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

Android Custom Kitchen (ACKitchen) puts the entire Android reverse-engineering and firmware modification workflow behind a single, cohesive desktop interface. Instead of memorising flags for a dozen CLI tools, you get a dark-themed PyQt5 GUI with real-time streamed terminal output, file pickers, guided parameter fields, and live tool-status detection — all without hiding what's actually being executed.

Every operation delegates to the battle-tested open-source tools the community already trusts. ACKitchen is purely a GUI layer.

---

## ✨ Features

### APK Workflows
| Feature | Tool | Notes |
|---|---|---|
| Decompile APK | `apktool` | Smali bytecode + XML resources + AndroidManifest |
| Java / Kotlin source | `jadx` | Optional, run alongside apktool in one click |
| Rebuild APK | `apktool b` | Recompile modified Smali and resources |
| Sign APK | `apksigner` | Uses debug keystore; auto-generates if absent |

### Firmware Workflows
| Feature | Tool | Notes |
|---|---|---|
| Extract OTA payload | `payload-dumper-go` | Parallel extraction of all partition images from `payload.bin` |
| Unpack `super.img` | `lpunpack` | Extracts logical partitions (system, vendor, product, odm…) |
| Repack `super.img` | `lpmake` | Guided template with size/group fields |
| Unpack `boot.img` | `unpack_bootimg` / Android Image Kitchen | Kernel, ramdisk.cpio, DTB |
| Repack `boot.img` | `mkbootimg` / Android Image Kitchen | Editable cmdline, base, pagesize, OS version |
| Extract EROFS | `fsck.erofs` | Android 12+ system/vendor partition images |

### General
- **Live tool status dashboard** — all 12 tools detected via `shutil.which`, green/red at a glance
- **Real-time terminal output** — `QProcess`-backed streaming, color-coded by stream type
- **One-click Setup** — installs all apt packages and downloads GitHub binaries automatically
- **Resizable terminal panel** — drag the splitter; collapse when not needed
- **Stop button** — kill any running process instantly
- **No hidden commands** — every `$` line is echoed before execution

---

## 📸 Interface

```
┌──────────────────────────────────────────────────────────────────┐
│ 🍳 ACKitchen    │  Dashboard                                     │
│─────────────────│  ────────────────────────────────────────────  │
│ 🏠  Dashboard   │  [ Tool Status Grid — 12 tools, ●green/●red ]  │
│ 📦  APK Tools   │                                                │
│ 💾  Firmware    │  Quick Actions                                 │
│ ⚙️   Setup       │  [ Decompile APK ]  [ Extract OTA ]           │
│ ℹ️   About       │  [ Unpack Boot  ]  [ Setup / Install ]        │
│                 │                                                │
│─────────────────│────────────────────────────────────────────────│
│ Workspace:      │ ● Terminal Output                    [Stop][X] │
│ ~/android-      │ $ apktool d app.apk -o ./out --force           │
│   custom-       │ I: Using Apktool 2.9.3                         │
│   kitchen       │ I: Decoding resources...                       │
│                 │ ✔  Done  (exit 0)                              │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Install the only runtime dependency

```bash
sudo apt-get install python3-pyqt5
```

### 2. Clone and run

```bash
git clone https://github.com/YOUR_USERNAME/android-custom-kitchen.git
cd android-custom-kitchen
python3 android_custom_kitchen_gui.py
```

### 3. Install the toolchain (first time)

Run the setup script (or use the GUI **Run Setup** action, which mirrors this behavior):

```bash
./setup.sh
```

The setup flow now works in this order:

1. **Scan your PC first** for required tools on `PATH` and common directories.
2. **Ask you for manual locations** for any missing dependency.
3. **As a last resort, install/download** what is still missing (apt or GitHub releases).

All resolved executables are linked into `~/.local/bin` and downloaded tools go into `~/android-custom-kitchen/tools/`.

---

## 📋 Requirements

| Requirement | Version |
|---|---|
| OS | Debian 11+ / Ubuntu 20.04+ / Linux Mint 20+ |
| Python | 3.8 or newer |
| PyQt5 | Any recent version via `apt` or `pip` |

All other dependencies (apktool, jadx, adb, lpunpack, etc.) are installed by the built-in Setup page.

For `boot.img` unpack/repack, either AOSP `unpack_bootimg` / `mkbootimg` **or** [Android Image Kitchen](https://github.com/osm0sis/Android-Image-Kitchen) must be on `PATH`.

---

## 🗂 Project Structure

```
android-custom-kitchen/
├── android_custom_kitchen_gui.py   # Single-file application (PyQt5)
├── README.md
└── ~/android-custom-kitchen/       # Runtime workspace (auto-created)
    └── tools/                      # Downloaded binaries (payload-dumper-go, jadx)
```

---

## 🛠 Underlying Tools

ACKitchen is a GUI wrapper. All credit for the heavy lifting goes to these projects:

| Tool | Purpose | Source |
|---|---|---|
| [apktool](https://ibotpeaches.github.io/Apktool/) | APK decompile / rebuild | iBotPeaches |
| [JADX](https://github.com/skylot/jadx) | Java / Kotlin decompilation | skylot |
| [apksigner](https://developer.android.com/tools/apksigner) | APK signing | Android SDK |
| [payload-dumper-go](https://github.com/ssut/payload-dumper-go) | OTA payload extraction | ssut |
| [Android Image Kitchen](https://github.com/osm0sis/Android-Image-Kitchen) | Boot image pack/unpack | osm0sis |
| [lpunpack / lpmake](https://source.android.com) | Dynamic partition tools | AOSP |
| [erofs-utils](https://github.com/erofs/erofs-utils) | EROFS filesystem extraction | erofs project |
| [avbtool](https://android.googlesource.com/platform/external/avb/) | Verified Boot 2.0 signing | AOSP |

---

## ⚠️ Disclaimer

This tool is intended for **legitimate use only**: modding your own devices, security research, ROM development, and educational purposes. Ensure you have the right to modify any firmware or APK you work with. The authors take no responsibility for misuse.

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first to discuss what you'd like to change.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/erofs-repack`)
3. Commit your changes
4. Push and open a Pull Request

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.
