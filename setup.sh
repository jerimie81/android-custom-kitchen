#!/usr/bin/env bash
set -euo pipefail

DEFAULT_WORKSPACE_ROOT="${HOME}/android-custom-kitchen"
WORKSPACE_ROOT="$DEFAULT_WORKSPACE_ROOT"

echo "== Android Custom Kitchen setup =="
echo

if [[ ! -d "$DEFAULT_WORKSPACE_ROOT/original" || ! -d "$DEFAULT_WORKSPACE_ROOT/work" || ! -d "$DEFAULT_WORKSPACE_ROOT/modified" ]]; then
  echo "First-run workspace setup"
  read -r -p "Workspace root [${DEFAULT_WORKSPACE_ROOT}]: " input_root
  if [[ -n "${input_root}" ]]; then
    WORKSPACE_ROOT="$input_root"
  fi

  ORIGINAL_DIR="${WORKSPACE_ROOT}/original"
  WORK_DIR="${WORKSPACE_ROOT}/work"
  MODIFIED_DIR="${WORKSPACE_ROOT}/modified"

  read -r -p "Create workspace directories (original/work/modified) in '${WORKSPACE_ROOT}'? [Y/n]: " create_ws
  if [[ ! "$create_ws" =~ ^[Nn]$ ]]; then
    mkdir -p "$ORIGINAL_DIR" "$WORK_DIR" "$MODIFIED_DIR"
    echo "Workspace ready:"
    echo "  - ${ORIGINAL_DIR}"
    echo "  - ${WORK_DIR}"
    echo "  - ${MODIFIED_DIR}"
  else
    echo "Workspace creation skipped."
  fi
fi

TOOLS_DIR="${WORKSPACE_ROOT}/tools"
LINK_DIR="${HOME}/.local/bin"
mkdir -p "$TOOLS_DIR" "$LINK_DIR"

# dependency key => executable name => apt package (if available)
DEPS=(
  "apktool:apktool:apktool"
  "adb:adb:adb"
  "fastboot:fastboot:fastboot"
  "apksigner:apksigner:apksigner"
  "java:java:openjdk-17-jre"
  "lpunpack:lpunpack:android-sdk-libsparse-utils"
  "lpmake:lpmake:android-sdk-libsparse-utils"
  "unpack_bootimg:unpack_bootimg:android-sdk-libsparse-utils"
  "mkbootimg:mkbootimg:android-sdk-libsparse-utils"
  "fsck.erofs:fsck.erofs:erofs-utils"
  "jadx:jadx:"
  "payload-dumper-go:payload-dumper-go:"
)

COMMON_PATHS=(
  "/usr/local/bin"
  "/usr/bin"
  "${HOME}/bin"
  "${HOME}/.local/bin"
  "${TOOLS_DIR}"
)

declare -A RESOLVED

detect_dep() {
  local exe="$1"

  if command -v "$exe" >/dev/null 2>&1; then
    command -v "$exe"
    return 0
  fi

  local p
  for base in "${COMMON_PATHS[@]}"; do
    p="${base}/${exe}"
    if [[ -x "$p" ]]; then
      echo "$p"
      return 0
    fi
  done

  return 1
}

link_dep() {
  local exe="$1"
  local path="$2"
  ln -sf "$path" "${LINK_DIR}/${exe}"
}

echo "Step 1/3: Scanning this PC for dependencies..."

for dep in "${DEPS[@]}"; do
  IFS=":" read -r name exe apt_pkg <<<"$dep"
  if found_path="$(detect_dep "$exe")"; then
    RESOLVED["$exe"]="$found_path"
    printf "  [FOUND] %-20s -> %s\n" "$exe" "$found_path"
    link_dep "$exe" "$found_path"
  else
    printf "  [MISSING] %s\n" "$exe"
  fi
done

echo
echo "Step 2/3: Ask for manual locations for anything missing."
for dep in "${DEPS[@]}"; do
  IFS=":" read -r name exe apt_pkg <<<"$dep"
  if [[ -n "${RESOLVED[$exe]:-}" ]]; then
    continue
  fi

  read -r -p "Path for '${exe}' (press Enter to skip): " user_path
  if [[ -z "$user_path" ]]; then
    continue
  fi

  if [[ -x "$user_path" ]]; then
    RESOLVED["$exe"]="$user_path"
    link_dep "$exe" "$user_path"
    printf "  [SET] %-22s -> %s\n" "$exe" "$user_path"
  else
    printf "  [WARN] '%s' is not executable; ignored.\n" "$user_path"
  fi
done

MISSING=()
for dep in "${DEPS[@]}"; do
  IFS=":" read -r name exe apt_pkg <<<"$dep"
  if [[ -z "${RESOLVED[$exe]:-}" ]]; then
    MISSING+=("$dep")
  fi
done

if [[ ${#MISSING[@]} -eq 0 ]]; then
  echo
  echo "All dependencies resolved via scan/manual path. Nothing to install."
  exit 0
fi

echo
echo "Step 3/3: Last resort install for remaining dependencies."
for dep in "${MISSING[@]}"; do
  IFS=":" read -r name exe apt_pkg <<<"$dep"
  if [[ -n "$apt_pkg" ]]; then
    read -r -p "Install '${exe}' via apt package '${apt_pkg}'? [y/N]: " yn
    if [[ "$yn" =~ ^[Yy]$ ]]; then
      sudo apt-get update
      sudo apt-get install -y "$apt_pkg"
      if found_path="$(detect_dep "$exe")"; then
        RESOLVED["$exe"]="$found_path"
        link_dep "$exe" "$found_path"
      fi
    fi
    continue
  fi

  case "$exe" in
    jadx)
      read -r -p "Download latest JADX release to ${TOOLS_DIR}? [y/N]: " yn
      if [[ "$yn" =~ ^[Yy]$ ]]; then
        tmp_zip="$(mktemp /tmp/jadx.XXXXXX.zip)"
        curl -fL "https://github.com/skylot/jadx/releases/latest/download/jadx.zip" -o "$tmp_zip"
        rm -rf "${TOOLS_DIR}/jadx"
        unzip -qo "$tmp_zip" -d "${TOOLS_DIR}/jadx"
        chmod +x "${TOOLS_DIR}/jadx/bin/jadx"
        RESOLVED["$exe"]="${TOOLS_DIR}/jadx/bin/jadx"
        link_dep "$exe" "${TOOLS_DIR}/jadx/bin/jadx"
      fi
      ;;
    payload-dumper-go)
      read -r -p "Download payload-dumper-go (Linux x86_64) to ${TOOLS_DIR}? [y/N]: " yn
      if [[ "$yn" =~ ^[Yy]$ ]]; then
        url="$(curl -fsSL https://api.github.com/repos/ssut/payload-dumper-go/releases/latest | sed -n 's/.*\"browser_download_url\": \"\([^\"]*linux_amd64[^\"]*\.tar\.gz\)\".*/\1/p' | head -n1)"
        if [[ -z "$url" ]]; then
          echo "  [WARN] Could not find a linux_amd64 payload-dumper-go release asset."
          continue
        fi
        tmp_tgz="$(mktemp /tmp/payload-dumper-go.XXXXXX.tar.gz)"
        curl -fL "$url" -o "$tmp_tgz"
        tar -xzf "$tmp_tgz" -C "$TOOLS_DIR"
        chmod +x "${TOOLS_DIR}/payload-dumper-go"
        RESOLVED["$exe"]="${TOOLS_DIR}/payload-dumper-go"
        link_dep "$exe" "${TOOLS_DIR}/payload-dumper-go"
      fi
      ;;
  esac
done

echo
echo "Resolved tools:"
for dep in "${DEPS[@]}"; do
  IFS=":" read -r name exe apt_pkg <<<"$dep"
  printf "  %-20s : %s\n" "$exe" "${RESOLVED[$exe]:-NOT SET}"
done

echo
echo "Done. Ensure '${LINK_DIR}' is in PATH to prioritize resolved binaries."
