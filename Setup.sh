#!/data/data/com.termux/files/usr/bin/bash
set -uo pipefail

# DedSec Project setup entry point.
# This file is the canonical dependency source for the project.
# This file is the canonical dependency source for the project setup.
# Other dependency/update entry points should be synchronized with it.

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
RUN_SETTINGS=1
REQUIRED_ONLY=0
SKIP_REPOSITORY_REFRESH=0
WARNINGS=0
PYTHON_FAILURES=0
OPTIONAL_TERMUX_FAILURES=0

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
  2. Install core Termux/build dependencies.
  3. Install tool-specific Termux dependencies.
  4. Install the Python dependencies used by active DedSec scripts.
  5. Verify core and tool Python imports.
  6. Start the DedSec menu.

Options:
  --run                         Start the DedSec menu after dependency setup.
  --no-run, --update-only       Update dependencies without opening the menu.
  --required-only               Install/verify only the core runtime.
  --skip-system-update          Do not refresh/upgrade Termux repositories.
  --skip-repository-refresh     Same as --skip-system-update.
  -h, --help                    Show this help message.

Large feature-specific environments such as Mobile Desktop/Termux:X11,
full proot desktop software, and Mobile Developer Setup language toolchains
remain on-demand and are installed by their own tools.
HELP
}

warn() {
  WARNINGS=$((WARNINGS + 1))
  printf '[warning] %s\n' "$*"
}

info() {
  printf '[info] %s\n' "$*"
}

fatal() {
  printf '[error] %s\n' "$*" >&2
  exit 1
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

command -v pkg >/dev/null 2>&1 || \
  fatal 'This setup is designed for Termux and requires the pkg command.'

# Core runtime + native build libraries needed by Python packages used across
# the project. Python modules with reliable Termux-native packages are kept
# under pkg to avoid unnecessary source builds on Android.
TERMUX_REQUIRED=(
  binutils
  ca-certificates
  clang
  curl
  git
  freetype
  libcairo
  libffi
  libjpeg-turbo
  libpng
  libxml2
  libxslt
  make
  ncurses
  openssl
  openssl-tool
  pkg-config
  python
  python-cryptography
  python-lxml
  python-pillow
  python-pip
  rust
  unzip
  wget
  zip
)

# Active-tool dependencies. Failures here are reported clearly but do not
# prevent the main menu from starting. Tools that need a missing item can
# still retry installation when opened.
TERMUX_TOOL_PACKAGES=(
  aapt
  cloudflared
  espeak
  ffmpeg
  file
  fzf
  gh
  iproute2
  ncurses-utils
  net-tools
  nmap
  nodejs
  npm
  openssh
  termux-api
  termux-tools
  tor
  unrar
  whois
)

# These are intentionally NOT installed globally by Setup.sh:
#   avahi net-snmp samba                 -> Devices Finder deep scan only
#   proot-distro pulseaudio x11-repo termux-x11 -> Mobile Desktop only
#   large language/editor toolchains     -> Mobile Developer Setup only
#   nano/jq                              -> convenience tools, not runtime deps

# Minimal Python runtime needed by common DedSec networking/update paths.
PYTHON_CORE_PACKAGES=(
  requests
  urllib3
)

# PyPI distributions directly used by active scripts. cryptography, lxml and
# Pillow are installed above from Termux-native packages.
PYTHON_TOOL_PACKAGES=(
  beautifulsoup4
  CairoSVG
  cloudscraper
  colorama
  python-dateutil
  dnspython
  python-docx
  python-dotenv
  EbookLib
  ExifRead
  flask
  flask-socketio
  geopy
  httpx
  Jinja2
  Markdown
  MarkupSafe
  odfpy
  paramiko
  phonenumbers
  python-nmap
  python-pptx
  psd-tools
  psutil
  py7zr
  pycountry
  PySocks
  pytz
  qrcode
  rarfile
  reportlab
  rich
  speedtest-cli
  striprtf
  tldextract
  validators
  websocket-client
  werkzeug
  python-whois
  zxcvbn
)

install_termux_package() {
  local package="$1"
  local optional="${2:-0}"

  if dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q 'install ok installed'; then
    info "Termux package already installed: $package"
    return 0
  fi

  info "Installing Termux package: $package"
  if pkg install -y "$package"; then
    return 0
  fi

  if [ "$optional" -eq 1 ]; then
    OPTIONAL_TERMUX_FAILURES=$((OPTIONAL_TERMUX_FAILURES + 1))
    warn "Tool-specific Termux package could not be installed: $package"
    return 1
  fi

  fatal "Required Termux package could not be installed: $package"
}

if [ "$SKIP_REPOSITORY_REFRESH" -eq 0 ]; then
  info 'Refreshing Termux package metadata.'
  pkg update -y || warn 'Termux package metadata could not be refreshed.'

  info 'Upgrading installed Termux packages.'
  pkg upgrade -y || warn 'Some installed Termux packages could not be upgraded.'
fi

for package in "${TERMUX_REQUIRED[@]}"; do
  install_termux_package "$package" 0
done

if [ "$REQUIRED_ONLY" -eq 0 ]; then
  for package in "${TERMUX_TOOL_PACKAGES[@]}"; do
    install_termux_package "$package" 1 || true
  done
fi

PYTHON_BIN=""
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
fi

[ -n "$PYTHON_BIN" ] || fatal 'Python is unavailable after package installation.'
"$PYTHON_BIN" -m pip --version >/dev/null 2>&1 || \
  fatal 'pip is unavailable after installing python/python-pip.'

PIP_FLAGS=()
if "$PYTHON_BIN" -m pip help install 2>/dev/null | grep -q -- '--break-system-packages'; then
  PIP_FLAGS+=(--break-system-packages)
fi

# Termux owns pip through python-pip. Never use pip to replace or upgrade pip itself.
info 'Updating Python build helpers.'
if ! "$PYTHON_BIN" -m pip install "${PIP_FLAGS[@]}" --upgrade setuptools wheel; then
  warn 'setuptools/wheel could not be updated.'
fi

install_python_package() {
  local package="$1"
  local optional="${2:-0}"
  info "Installing/updating Python package: $package"
  if "$PYTHON_BIN" -m pip install "${PIP_FLAGS[@]}" --upgrade "$package"; then
    return 0
  fi

  PYTHON_FAILURES=$((PYTHON_FAILURES + 1))
  if [ "$optional" -eq 1 ]; then
    warn "Tool-specific Python package could not be installed or updated: $package"
    return 1
  fi
  fatal "Required Python package could not be installed or updated: $package"
}

for package in "${PYTHON_CORE_PACKAGES[@]}"; do
  install_python_package "$package" 0
done

if [ "$REQUIRED_ONLY" -eq 0 ]; then
  for package in "${PYTHON_TOOL_PACKAGES[@]}"; do
    install_python_package "$package" 1 || true
  done
fi

# Verify imports by module name (distribution names and import names differ for
# several packages: beautifulsoup4->bs4, Pillow->PIL, python-whois->whois,
# websocket-client->websocket, PySocks->socks, etc.).
VERIFY_MODE="core"
[ "$REQUIRED_ONLY" -eq 0 ] && VERIFY_MODE="full"

VERIFY_OUTPUT="$($PYTHON_BIN - "$VERIFY_MODE" <<'PY'
import importlib
import sys

mode = sys.argv[1]
core = [
    "requests",
    "urllib3",
]

tools = [
    "PIL",
    "bs4",
    "cairosvg",
    "cloudscraper",
    "colorama",
    "cryptography",
    "dateutil",
    "dns",
    "docx",
    "dotenv",
    "ebooklib",
    "exifread",
    "flask",
    "flask_socketio",
    "geopy",
    "httpx",
    "jinja2",
    "lxml",
    "markdown",
    "markupsafe",
    "nmap",
    "odf",
    "paramiko",
    "phonenumbers",
    "pptx",
    "psd_tools",
    "psutil",
    "py7zr",
    "pycountry",
    "pytz",
    "qrcode",
    "rarfile",
    "reportlab",
    "rich",
    "socks",
    "speedtest",
    "striprtf",
    "tldextract",
    "validators",
    "websocket",
    "werkzeug",
    "whois",
    "zxcvbn",
]

names = core if mode == "core" else core + tools
missing = []
for name in names:
    try:
        importlib.import_module(name)
    except Exception as exc:
        missing.append((name, f"{type(exc).__name__}: {exc}"))

if missing:
    for name, reason in missing:
        print(f"MISSING\t{name}\t{reason}")
    raise SystemExit(3)

print(f"OK\t{len(names)}")
PY
)"
VERIFY_STATUS=$?

if [ "$VERIFY_STATUS" -eq 0 ]; then
  VERIFIED_COUNT="${VERIFY_OUTPUT#OK$'\t'}"
  echo "[verify] Python imports ready: ${VERIFIED_COUNT}."
else
  echo '[warning] One or more Python imports are still unavailable:'
  printf '%s\n' "$VERIFY_OUTPUT" | while IFS=$'\t' read -r kind module reason; do
    [ "$kind" = 'MISSING' ] && printf '  - %s (%s)\n' "$module" "$reason"
  done
  if [ "$REQUIRED_ONLY" -eq 1 ]; then
    fatal 'Core Python verification failed.'
  fi
  warn 'Full tool dependency verification is incomplete. See the missing modules above.'
fi

# Verify the commands needed by the core setup itself.
CORE_COMMANDS=(python git curl wget unzip zip openssl)
for command_name in "${CORE_COMMANDS[@]}"; do
  command -v "$command_name" >/dev/null 2>&1 || \
    fatal "Required command is unavailable after setup: $command_name"
done

if [ "$REQUIRED_ONLY" -eq 0 ]; then
  # Optional command checks provide an accurate final status instead of a false
  # "everything verified" message when a tool package was unavailable.
  OPTIONAL_COMMANDS=(aapt cloudflared espeak ffmpeg file fzf gh ip nmap node npm ssh tor unrar whois)
  for command_name in "${OPTIONAL_COMMANDS[@]}"; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
      warn "Tool command is unavailable: $command_name"
    fi
  done
fi

[ -f "$ROOT_DIR/Scripts/Settings.py" ] || fatal 'Scripts/Settings.py is missing.'

if [ ! -d "$ROOT_DIR/Scripts/Ελληνική Έκδοση" ] && [ ! -d "$ROOT_DIR/Scripts/.Ελληνική Έκδοση" ]; then
  warn 'The Greek edition directory is missing.'
fi

echo
if [ "$WARNINGS" -eq 0 ] && [ "$PYTHON_FAILURES" -eq 0 ] && [ "$OPTIONAL_TERMUX_FAILURES" -eq 0 ]; then
  echo '[complete] DedSec dependencies were installed and verified successfully.'
else
  echo "[complete with warnings] Setup finished with $WARNINGS warning(s). Review: $LOG_FILE"
fi

echo '[note] Termux:API commands also require the separate Termux:API Android application.'
echo '[note] Mobile Desktop/X11 and deep-scan extras remain on-demand to avoid a very large default installation.'
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
  warn "Settings.py exited with code $EXEC_STATUS. Repairing requests/urllib3 and retrying once."
  "$PYTHON_BIN" -m pip install "${PIP_FLAGS[@]}" --upgrade requests urllib3 || \
    warn 'The requests/urllib3 repair command failed.'
  echo '[launch] Retrying the DedSec menu...'
  run_settings_on_terminal
  exit $?
fi

exit 0
