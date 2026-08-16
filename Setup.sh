#!/data/data/com.termux/files/usr/bin/bash
set -uo pipefail

# DedSec Project setup entry point.
# Dependencies are installed directly from the configured Termux/PyPI repositories.
# No vendored dependency cache is required.

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
RUN_SETTINGS=1
REQUIRED_ONLY=0
SKIP_REPOSITORY_REFRESH=0
WARNINGS=0

LOG_DIR="${HOME:-$ROOT_DIR}/.dedsec/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/setup-$(date +%Y%m%d-%H%M%S).log"
if command -v tee >/dev/null 2>&1; then
  exec > >(tee -a "$LOG_FILE") 2>&1
fi

show_help() {
  cat <<'HELP'
Usage: bash Setup.sh [options]

Default behavior:
  1. Refresh Termux package metadata and installed packages.
  2. Install the DedSec Termux dependencies directly from Termux repositories.
  3. Install the DedSec Python dependencies directly from PyPI.
  4. Verify the core runtime.
  5. Start the DedSec menu.

Options:
  --run                         Start the DedSec menu after dependency setup.
  --no-run, --update-only       Update dependencies without opening the menu.
  --required-only               Skip optional Termux packages.
  --skip-system-update          Do not refresh/upgrade Termux repositories.
  --skip-repository-refresh     Same as --skip-system-update.
  -h, --help                    Show this help message.

Examples:
  bash Setup.sh
  bash Setup.sh --update-only
  bash Setup.sh --required-only
HELP
}

warn() {
  WARNINGS=$((WARNINGS + 1))
  printf '[warning] %s\n' "$*"
}

info() {
  printf '[info] %s\n' "$*"
}

for arg in "$@"; do
  case "$arg" in
    --run) RUN_SETTINGS=1 ;;
    --no-run|--update-only) RUN_SETTINGS=0 ;;
    --required-only) REQUIRED_ONLY=1 ;;
    --skip-system-update|--skip-repository-refresh) SKIP_REPOSITORY_REFRESH=1 ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      printf '[error] Unknown option: %s\n\n' "$arg" >&2
      show_help >&2
      exit 2
      ;;
  esac
done

printf '[DedSec Setup] Project: %s\n' "$ROOT_DIR"
printf '[DedSec Setup] Log: %s\n' "$LOG_FILE"

if ! command -v pkg >/dev/null 2>&1; then
  echo '[error] This setup is designed for Termux and requires the pkg command.' >&2
  exit 1
fi

# Packages required by the main menu and common project tools.
TERMUX_REQUIRED=(
  clang curl git jq libffi libxml2 libxslt nano ncurses
  openssl openssl-tool proot python python-pip rust unzip wget zip
)

# Tool-specific packages. The default setup installs these too; --required-only skips them.
TERMUX_OPTIONAL=(
  aapt cloudflared ffmpeg fzf nodejs openssh termux-api tor
)

PYTHON_PACKAGES=(
  blessed
  bs4
  cryptography
  flask
  flask-socketio
  geopy
  mutagen
  phonenumbers
  pycountry
  pydub
  pycryptodome
  requests
  werkzeug
  psutil
  pillow
  pysocks
)

install_termux_package() {
  local package="$1"
  local optional="${2:-0}"

  if dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q 'install ok installed'; then
    info "Termux package already installed: $package"
    return 0
  fi

  info "Installing Termux package: $package"
  if ! pkg install -y "$package"; then
    if [ "$optional" -eq 1 ]; then
      warn "Optional Termux package could not be installed: $package"
    else
      warn "Required Termux package could not be installed: $package"
    fi
    return 1
  fi
}

if [ "$SKIP_REPOSITORY_REFRESH" -eq 0 ]; then
  info 'Refreshing Termux package metadata.'
  pkg update -y || warn 'Termux package metadata could not be refreshed.'

  info 'Upgrading installed Termux packages.'
  pkg upgrade -y || warn 'Some installed Termux packages could not be upgraded.'
fi

for package in "${TERMUX_REQUIRED[@]}"; do
  install_termux_package "$package" 0 || true
done

if [ "$REQUIRED_ONLY" -eq 0 ]; then
  for package in "${TERMUX_OPTIONAL[@]}"; do
    install_termux_package "$package" 1 || true
  done
fi

PYTHON_BIN=""
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
fi

if [ -z "$PYTHON_BIN" ]; then
  echo '[error] Python is unavailable after package installation.' >&2
  exit 1
fi

if ! "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
  echo '[error] pip is unavailable after installing python/python-pip.' >&2
  exit 1
fi

PIP_FLAGS=()
if "$PYTHON_BIN" -m pip help install 2>/dev/null | grep -q -- '--break-system-packages'; then
  PIP_FLAGS+=(--break-system-packages)
fi

# Termux manages pip through the python-pip package. Do not self-upgrade pip with pip.
info 'Updating Python build helpers.'
if ! "$PYTHON_BIN" -m pip install --upgrade setuptools wheel "${PIP_FLAGS[@]}"; then
  warn 'setuptools/wheel could not be updated.'
fi

PYTHON_FAILURES=0
for package in "${PYTHON_PACKAGES[@]}"; do
  info "Installing/updating Python package: $package"
  if ! "$PYTHON_BIN" -m pip install --upgrade "$package" "${PIP_FLAGS[@]}"; then
    warn "Python package could not be installed or updated: $package"
    PYTHON_FAILURES=$((PYTHON_FAILURES + 1))
  fi
done

# Verify the dependencies needed to start the main menu.
if ! "$PYTHON_BIN" - <<'PY'
import importlib
import sys

required = ("requests",)
missing = []
for name in required:
    try:
        importlib.import_module(name)
    except Exception:
        missing.append(name)

if missing:
    print("[error] Missing core Python module(s): " + ", ".join(missing), file=sys.stderr)
    raise SystemExit(1)
print("[verify] Core Python runtime is ready.")
PY
then
  exit 1
fi

if [ ! -f "$ROOT_DIR/Scripts/Settings.py" ]; then
  echo '[error] Scripts/Settings.py is missing.' >&2
  exit 1
fi

if [ ! -d "$ROOT_DIR/Scripts/Ελληνική Έκδοση" ] && [ ! -d "$ROOT_DIR/Scripts/.Ελληνική Έκδοση" ]; then
  warn 'The Greek edition directory is missing.'
fi

echo
if [ "$WARNINGS" -eq 0 ] && [ "$PYTHON_FAILURES" -eq 0 ]; then
  echo '[complete] DedSec dependencies were installed and verified successfully.'
else
  echo "[complete with warnings] Setup finished with $WARNINGS warning(s). Review: $LOG_FILE"
fi

echo '[note] Termux:API commands also require the separate Termux:API Android application.'
echo '[note] Use Settings -> Save DedSec Project when you want to create or refresh a backup.'

if [ "$RUN_SETTINGS" -eq 0 ]; then
  echo '[complete] Dependency-only mode finished; the DedSec menu was not opened.'
  exit 0
fi

cd "$ROOT_DIR" || exit 1
SCRIPT_PATH='./Scripts/Settings.py'

run_settings_on_terminal() {
  if [ -r /dev/tty ] && [ -w /dev/tty ]; then
    "$PYTHON_BIN" "$SCRIPT_PATH" </dev/tty >/dev/tty 2>/dev/tty
  else
    "$PYTHON_BIN" "$SCRIPT_PATH"
  fi
}

echo "[launch] Starting the DedSec menu with: $PYTHON_BIN $SCRIPT_PATH"
run_settings_on_terminal
EXEC_STATUS=$?

if [ "$EXEC_STATUS" -ne 0 ]; then
  warn "Settings.py exited with code $EXEC_STATUS. Repairing requests and retrying once."
  "$PYTHON_BIN" -m pip install --upgrade requests "${PIP_FLAGS[@]}" || warn 'The requests repair command failed.'
  echo '[launch] Retrying the DedSec menu...'
  run_settings_on_terminal
  exit $?
fi

exit 0
