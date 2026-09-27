#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
RUN_SETTINGS=1
REQUIRED_ONLY=0
SKIP_SYSTEM_UPDATE=0

show_help() {
  cat <<'HELP'
Usage: bash Setup.sh [options]

Supported platforms:
  - Termux (Android)
  - Ubuntu
  - Kali Linux
  - Linux Mint
  - Other Debian/Ubuntu-family systems with apt-get (best effort)

Options:
  --run                         Start the DedSec menu after setup (default).
  --no-run, --update-only       Install/update dependencies without opening the menu.
  --required-only               Install only the core runtime.
  --skip-system-update          Skip apt/pkg repository refresh and OS package upgrade.
  --skip-repository-refresh     Same as --skip-system-update.
  -h, --help                    Show this help message.

Notes:
  Desktop Linux uses a project-local .venv so distro-managed Python is not modified.
  Termux keeps the project's original Termux-native dependency installer.
HELP
}

for arg in "$@"; do
  case "$arg" in
    --run) RUN_SETTINGS=1 ;;
    --no-run|--update-only) RUN_SETTINGS=0 ;;
    --required-only) REQUIRED_ONLY=1 ;;
    --skip-system-update|--skip-repository-refresh) SKIP_SYSTEM_UPDATE=1 ;;
    -h|--help) show_help; exit 0 ;;
    *) printf '[error] Unknown option: %s\n\n' "$arg" >&2; show_help >&2; exit 2 ;;
  esac
done

is_termux() {
  [ -n "${TERMUX_VERSION:-}" ] || [ -x /data/data/com.termux/files/usr/bin/pkg ] || [[ "${PREFIX:-}" == *com.termux* ]]
}

# Preserve the mature Termux setup path unchanged.
if is_termux; then
  args=()
  [ "$RUN_SETTINGS" -eq 0 ] && args+=(--no-run)
  [ "$REQUIRED_ONLY" -eq 1 ] && args+=(--required-only)
  [ "$SKIP_SYSTEM_UPDATE" -eq 1 ] && args+=(--skip-system-update)
  exec bash "$ROOT_DIR/Setup-Termux.sh" "${args[@]}"
fi

if ! command -v apt-get >/dev/null 2>&1; then
  echo '[error] Desktop setup currently requires an apt-get based Linux distribution.' >&2
  echo '[error] Supported desktop targets are Ubuntu, Kali Linux, and Linux Mint.' >&2
  exit 1
fi

OS_ID='linux'
OS_NAME='Linux'
OS_LIKE=''
if [ -r /etc/os-release ]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  OS_ID="${ID:-linux}"
  OS_NAME="${PRETTY_NAME:-${NAME:-Linux}}"
  OS_LIKE="${ID_LIKE:-}"
fi

case " $OS_ID $OS_LIKE " in
  *' ubuntu '*|*' debian '*|*' kali '*|*' linuxmint '*|*' mint '*) ;;
  *) echo "[warning] $OS_NAME is not one of the primary tested targets; continuing because apt-get is available." ;;
esac

echo "[DedSec Setup] Platform: $OS_NAME"
echo "[DedSec Setup] Project:  $ROOT_DIR"

APT=(apt-get)
if [ "$(id -u)" -ne 0 ]; then
  if command -v sudo >/dev/null 2>&1; then
    APT=(sudo apt-get)
  else
    echo '[error] sudo is required for OS package installation when not running as root.' >&2
    exit 1
  fi
fi

apt_install_best_effort() {
  local packages=("$@")
  [ "${#packages[@]}" -eq 0 ] && return 0
  DEBIAN_FRONTEND=noninteractive "${APT[@]}" install -y --no-install-recommends "${packages[@]}" || return 1
}

if [ "$SKIP_SYSTEM_UPDATE" -eq 0 ]; then
  echo '[info] Refreshing apt package metadata...'
  "${APT[@]}" update || echo '[warning] apt update reported an error; setup will continue.'
  echo '[info] Upgrading installed packages...'
  DEBIAN_FRONTEND=noninteractive "${APT[@]}" upgrade -y || echo '[warning] apt upgrade reported an error; setup will continue.'
fi

CORE_APT=(
  bash ca-certificates curl git wget unzip zip openssl file
  python3 python3-venv python3-pip
  build-essential pkg-config libffi-dev libssl-dev
  libjpeg-dev libpng-dev libxml2-dev libxslt1-dev libfreetype6-dev libcairo2-dev
  libncurses-dev
)

OPTIONAL_APT=(
  ffmpeg fzf iproute2 net-tools nmap nodejs npm openssh-client tor whois
  espeak-ng xdg-utils xclip wl-clipboard libnotify-bin at procps psmisc
  dnsutils iputils-ping traceroute avahi-utils snmp samba-common-bin
  zsh neovim mpv sox sqlite3 jq ripgrep rsync
)

# Install core in one pass; retry individually so a distro-specific missing package
# does not hide which dependency failed.
echo '[info] Installing core desktop packages...'
if ! apt_install_best_effort "${CORE_APT[@]}"; then
  echo '[warning] Bulk core install failed; retrying packages individually.'
  for p in "${CORE_APT[@]}"; do
    apt_install_best_effort "$p" || { echo "[error] Required package could not be installed: $p" >&2; exit 1; }
  done
fi

if [ "$REQUIRED_ONLY" -eq 0 ]; then
  echo '[info] Installing optional tool packages (best effort)...'
  for p in "${OPTIONAL_APT[@]}"; do
    apt_install_best_effort "$p" || echo "[warning] Optional package unavailable: $p"
  done
fi

VENV_DIR="$ROOT_DIR/.venv"
if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo '[info] Creating project Python virtual environment...'
  python3 -m venv "$VENV_DIR"
fi
PYTHON_BIN="$VENV_DIR/bin/python"

# Repair Unicode filenames if an older unzip extracted Greek names as #Uhhhh tokens.
REPAIR_UNICODE="$ROOT_DIR/Compat/repair_unicode_names.py"
if [ -f "$REPAIR_UNICODE" ]; then
  "$PYTHON_BIN" "$REPAIR_UNICODE" "$ROOT_DIR" || echo '[warning] Unicode filename repair reported an error; setup will continue.'
fi

"$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel

CORE_PY=(requests urllib3)
TOOL_PY=(
  beautifulsoup4 CairoSVG cloudscraper colorama python-dateutil dnspython
  python-docx python-dotenv EbookLib ExifRead flask flask-socketio geopy httpx
  Jinja2 Markdown MarkupSafe odfpy paramiko phonenumbers python-nmap python-pptx
  psd-tools psutil py7zr pycountry PySocks pytz qrcode rarfile reportlab rich
  pypdf
  speedtest-cli striprtf tldextract validators websocket-client werkzeug python-whois zxcvbn
  cryptography lxml numpy pillow scipy
)

echo '[info] Installing core Python packages into .venv...'
"$PYTHON_BIN" -m pip install --upgrade "${CORE_PY[@]}"

if [ "$REQUIRED_ONLY" -eq 0 ]; then
  echo '[info] Installing tool Python packages into .venv...'
  for p in "${TOOL_PY[@]}"; do
    "$PYTHON_BIN" -m pip install --upgrade "$p" || echo "[warning] Optional Python package unavailable: $p"
  done
fi

# Make desktop compatibility shims visible only for launches through Setup.sh/Run.sh.
export PATH="$ROOT_DIR/Compat/bin:$VENV_DIR/bin:$PATH"
export DEDSEC_ROOT="$ROOT_DIR"
export DEDSEC_PLATFORM="desktop-linux"
export DEDSEC_SAFE_CROSS_PLATFORM=1

chmod +x "$ROOT_DIR/Run.sh" "$ROOT_DIR/Compat/bin/"* 2>/dev/null || true

# Basic validation.
"$PYTHON_BIN" - <<'PY'
import importlib
required = ['requests', 'urllib3']
missing=[]
for name in required:
    try: importlib.import_module(name)
    except Exception as exc: missing.append((name, str(exc)))
if missing:
    for name, err in missing: print(f'[verify] MISSING {name}: {err}')
    raise SystemExit(1)
print('[verify] Core Python imports are ready.')
PY

for cmd in bash git curl wget unzip zip openssl; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "[error] Required command unavailable: $cmd" >&2; exit 1; }
done

echo '[complete] Desktop Linux dependencies are ready.'
echo "[note] Python environment: $VENV_DIR"
echo '[note] Android/Termux-only tools are detected and reported as unavailable on desktop rather than crashing.'
echo '[note] Sensitive credential/card/camera/location capture and Trojan tooling are not enabled by the desktop compatibility launcher.'

if [ "$RUN_SETTINGS" -eq 0 ]; then
  exit 0
fi

cd "$ROOT_DIR" || exit 1
exec "$PYTHON_BIN" "$ROOT_DIR/Scripts/Settings.py"
