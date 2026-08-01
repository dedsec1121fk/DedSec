#!/data/data/com.termux/files/usr/bin/bash
set -uo pipefail

# DedSec Project single setup entry point.
# This file contains the former Needs/install.sh and Needs/update.sh behavior.

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
MODULES_DIR="$ROOT_DIR/Needs/Modules"
PACKAGES_DIR="$ROOT_DIR/Needs/Packages"
LOG_DIR="$ROOT_DIR/Needs/Logs"
RUN_SETTINGS=1
REQUIRED_ONLY=0
SKIP_REPOSITORY_REFRESH=0

show_help() {
  cat <<'HELP'
Usage: bash Setup.sh [options]

Default behavior:
  1. Check the vendored packages and Python modules already stored in Needs/.
  2. Install missing or newer local dependencies first.
  3. Refresh repositories and update/download anything still missing.
  4. Verify the environment.
  5. Create the one-time Downloads save when needed.
  6. Start the DedSec menu.

Options:
  --run                         Start the DedSec menu after dependency setup.
  --no-run, --update-only       Update dependencies without opening the menu.
  --required-only               Skip optional Termux packages.
  --skip-system-update          Do not refresh package repository metadata.
  --skip-repository-refresh     Same as --skip-system-update.
  -h, --help                    Show this help message.

Examples:
  bash Setup.sh
  bash Setup.sh --update-only
  bash Setup.sh --required-only
HELP
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

mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/setup-$(date +%Y%m%d-%H%M%S).log"
if command -v tee >/dev/null 2>&1; then
  exec > >(tee -a "$LOG_FILE") 2>&1
fi

printf '[DedSec Setup] Project: %s\n' "$ROOT_DIR"
printf '[DedSec Setup] Log: %s\n' "$LOG_FILE"

read_manifest() {
  [ -f "$1" ] || return 0
  sed -e 's/[[:space:]]*#.*$//' -e '/^[[:space:]]*$/d' "$1"
}

warn() { printf '[warning] %s\n' "$*"; }
info() { printf '[info] %s\n' "$*"; }

PYTHON_BIN=""
resolve_python() {
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    PYTHON_BIN=""
  fi
}

pip_flags=()
resolve_pip_flags() {
  pip_flags=()
  [ -n "$PYTHON_BIN" ] || return 0
  if "$PYTHON_BIN" -m pip help install 2>/dev/null | grep -q -- '--break-system-packages'; then
    pip_flags+=(--break-system-packages)
  fi
}

termux_architecture() {
  if command -v dpkg >/dev/null 2>&1; then
    dpkg --print-architecture 2>/dev/null && return
  fi
  case "$(uname -m 2>/dev/null || true)" in
    aarch64|arm64) echo aarch64 ;;
    armv7l|armv8l) echo arm ;;
    x86_64|amd64) echo x86_64 ;;
    i?86) echo i686 ;;
    *) uname -m ;;
  esac
}

prepare_local_debs() {
  cache_dir="$1"
  output_dir="$2"
  mkdir -p "$output_dir"
  LOCAL_DEBS=()
  [ -d "$cache_dir" ] || return 0

  while IFS= read -r -d '' deb; do
    LOCAL_DEBS+=("$deb")
  done < <(find "$cache_dir" -maxdepth 1 -type f -name '*.deb' -print0 2>/dev/null)

  while IFS= read -r -d '' first_part; do
    base="${first_part%.part001}"
    output="$output_dir/$(basename "$base")"
    parts=("$base".part*)
    if [ "${#parts[@]}" -gt 0 ]; then
      cat "${parts[@]}" > "$output"
      LOCAL_DEBS+=("$output")
    fi
  done < <(find "$cache_dir" -maxdepth 1 -type f -name '*.deb.part001' -print0 2>/dev/null)
}

install_local_termux_packages() {
  arch="$(termux_architecture)"
  cache="$PACKAGES_DIR/Cache/$arch"
  temp_dir="$(mktemp -d "${TMPDIR:-/tmp}/dedsec-local-debs.XXXXXX")"
  prepare_local_debs "$cache" "$temp_dir"

  if [ "${#LOCAL_DEBS[@]}" -eq 0 ]; then
    warn "No vendored Termux .deb files were found for architecture $arch."
    rm -rf "$temp_dir"
    return 0
  fi

  info "Checking ${#LOCAL_DEBS[@]} vendored Termux packages for $arch."
  local_targets=()
  for deb in "${LOCAL_DEBS[@]}"; do
    package="$(dpkg-deb -f "$deb" Package 2>/dev/null || true)"
    cached_version="$(dpkg-deb -f "$deb" Version 2>/dev/null || true)"
    if [ -z "$package" ] || [ -z "$cached_version" ]; then
      warn "Ignoring invalid package file: $deb"
      continue
    fi

    installed_version="$(dpkg-query -W -f='${Version}' "$package" 2>/dev/null || true)"
    if [ -z "$installed_version" ]; then
      info "Local package will install missing $package ($cached_version)."
      local_targets+=("$deb")
    elif dpkg --compare-versions "$installed_version" lt "$cached_version"; then
      info "Local package will update $package: $installed_version -> $cached_version."
      local_targets+=("$deb")
    else
      info "$package is already at $installed_version; cached version is $cached_version."
    fi
  done

  if [ "${#local_targets[@]}" -gt 0 ]; then
    if ! apt install -y --no-install-recommends "${local_targets[@]}"; then
      warn "Some vendored packages could not be installed locally. The repository pass will retry them."
    fi
  fi
  rm -rf "$temp_dir"
}

ensure_termux_manifest() {
  manifest="$1"
  optional="${2:-0}"
  [ -f "$manifest" ] || return 0

  while IFS= read -r package; do
    [ -n "$package" ] || continue
    info "Checking repository package: $package"
    if ! pkg install -y "$package"; then
      if [ "$optional" -eq 1 ]; then
        warn "Optional Termux package unavailable: $package"
      else
        warn "Required Termux package could not be updated or downloaded: $package"
      fi
    fi
  done < <(read_manifest "$manifest")
}

install_python_dependencies() {
  resolve_python
  if [ -z "$PYTHON_BIN" ]; then
    warn "Python is unavailable after package installation."
    return 1
  fi
  if ! "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
    warn "pip is unavailable after package installation."
    return 1
  fi
  resolve_pip_flags

  cache="$MODULES_DIR/Cache"
  requirements="$MODULES_DIR/requirements.txt"
  [ -f "$requirements" ] || {
    warn "Missing $requirements"
    return 1
  }

  info "Checking vendored Python artifacts first."
  if find "$cache" -maxdepth 1 -type f \( -name '*.whl' -o -name '*.tar.gz' -o -name '*.zip' \) -print -quit 2>/dev/null | grep -q .; then
    while IFS= read -r requirement; do
      [ -n "$requirement" ] || continue
      if ! "$PYTHON_BIN" -m pip install --upgrade --no-index --no-deps \
          --find-links "$cache" "$requirement" "${pip_flags[@]}"; then
        info "No usable local artifact for $requirement; the online pass will retry it."
      fi
    done < <(read_manifest "$requirements")
  else
    warn "No vendored Python archives were found in $cache."
  fi

  info "Updating dependencies and downloading anything still missing."
  if "$PYTHON_BIN" -m pip install --upgrade --find-links "$cache" \
      --requirement "$requirements" "${pip_flags[@]}"; then
    return 0
  fi

  warn "Bulk Python dependency update failed; retrying each requirement independently."
  failures=0
  while IFS= read -r requirement; do
    [ -n "$requirement" ] || continue
    if ! "$PYTHON_BIN" -m pip install --upgrade --find-links "$cache" \
        "$requirement" "${pip_flags[@]}"; then
      warn "Python dependency unavailable: $requirement"
      failures=$((failures + 1))
    fi
  done < <(read_manifest "$requirements")
  return "$failures"
}

ensure_termux_storage_for_first_save() {
  marker="$ROOT_DIR/Needs/State/.first-run-download-save-complete.json"
  downloads="$HOME/storage/downloads"

  [ -f "$marker" ] && return 0
  if [ -d "$downloads" ] && [ -r "$downloads" ] && [ -w "$downloads" ]; then
    return 0
  fi
  if ! command -v termux-setup-storage >/dev/null 2>&1; then
    warn "termux-setup-storage is unavailable; the first-run Downloads save will be retried later."
    return 1
  fi

  echo
  echo "[storage permission] DedSec needs access to Android internal Downloads"
  echo "to create the one-time first-run project save."
  echo "Approve the Android permission request. If Termux asks for y/n or Enter,"
  echo "answer the visible prompt to continue."
  echo

  if ! termux-setup-storage; then
    warn "Storage access was not granted. The next Setup.sh run will ask again."
    return 1
  fi

  if [ ! -d "$downloads" ] || [ ! -w "$downloads" ]; then
    warn "Android Downloads is still unavailable. The first-run save will be retried later."
    return 1
  fi
  return 0
}

if command -v pkg >/dev/null 2>&1; then
  info "Termux environment detected."

  # Local packages are always checked before repository/network operations.
  install_local_termux_packages

  if [ "$SKIP_REPOSITORY_REFRESH" -eq 0 ]; then
    pkg update -y || warn "Repository metadata could not be refreshed; local caches were still checked first."
  fi

  ensure_termux_manifest "$PACKAGES_DIR/termux-required.txt" 0
  if [ "$REQUIRED_ONLY" -eq 0 ]; then
    ensure_termux_manifest "$PACKAGES_DIR/termux-optional.txt" 1
  fi
elif command -v apt-get >/dev/null 2>&1; then
  info "Debian/Ubuntu environment detected."
  if [ "$(id -u)" -eq 0 ]; then
    SUDO=""
  elif command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
  else
    SUDO=""
    warn "sudo is unavailable; system package installation may fail."
  fi

  if [ "$SKIP_REPOSITORY_REFRESH" -eq 0 ]; then
    $SUDO apt-get update || warn "Debian repository metadata could not be refreshed."
  fi

  while IFS= read -r package; do
    [ -n "$package" ] || continue
    $SUDO apt-get install -y "$package" || warn "Debian package unavailable: $package"
  done < <(read_manifest "$PACKAGES_DIR/debian-required.txt")
else
  echo "[error] No supported package manager was found." >&2
  exit 1
fi

python_failures=0
install_python_dependencies || python_failures=$?
resolve_python
if [ -n "$PYTHON_BIN" ]; then
  "$PYTHON_BIN" "$ROOT_DIR/Needs/verify_needs.py" --installed --cache || true
fi

echo
if [ "$python_failures" -eq 0 ]; then
  echo "[complete] Dependencies were checked, locally restored where possible, updated, and missing items were downloaded."
else
  echo "[complete with warnings] $python_failures Python dependency operation(s) failed. Review $LOG_FILE"
fi

echo "[note] Termux:API commands also require the separate Termux:API Android application."

if [ "$RUN_SETTINGS" -eq 0 ]; then
  echo "[complete] Dependency-only mode finished; the DedSec menu was not opened."
  exit 0
fi

resolve_python
if [ -z "$PYTHON_BIN" ]; then
  echo "[error] Cannot start the menu because Python is unavailable." >&2
  exit 1
fi

if [ ! -f "$ROOT_DIR/Scripts/Settings.py" ]; then
  echo "[error] Cannot start the menu because Scripts/Settings.py is missing." >&2
  exit 1
fi

# The save is attempted only before the first menu launch. Its marker is
# created only after a complete, validated archive reaches Android Downloads.
ensure_termux_storage_for_first_save || true
if ! "$PYTHON_BIN" "$ROOT_DIR/Needs/first_run_save.py"; then
  warn "The first-run Downloads save could not be created. Setup will retry it on the next run."
fi

# Preserve the original DedSec launch behavior: run Settings.py from the
# project root through its relative path, then retry once after repairing the
# requests dependency if the first execution fails.
cd "$ROOT_DIR" || exit 1
SCRIPT_PATH="./Scripts/Settings.py"

echo "[launch] Starting the DedSec menu with: python $SCRIPT_PATH"
if [ -f "$SCRIPT_PATH" ]; then
  "$PYTHON_BIN" "$SCRIPT_PATH"
  EXEC_STATUS=$?
else
  echo "[error] Script file not found at $SCRIPT_PATH. Cannot execute." >&2
  EXEC_STATUS=1
fi

if [ "$EXEC_STATUS" -ne 0 ]; then
  warn "Settings.py exited with code $EXEC_STATUS. Repairing requests and retrying once."
  resolve_pip_flags
  if ! "$PYTHON_BIN" -m pip install --upgrade requests "${pip_flags[@]}"; then
    warn "The requests repair command failed; retrying Settings.py anyway."
  fi

  echo "[launch] Retrying the DedSec menu..."
  if [ -f "$SCRIPT_PATH" ]; then
    "$PYTHON_BIN" "$SCRIPT_PATH"
    FINAL_STATUS=$?
    if [ "$FINAL_STATUS" -eq 0 ]; then
      echo "[success] Settings.py completed successfully after the retry."
    else
      echo "[error] Settings.py failed again (exit code: $FINAL_STATUS)." >&2
    fi
    exit "$FINAL_STATUS"
  fi

  echo "[error] Script file is still missing at $SCRIPT_PATH." >&2
  exit 1
fi

echo "[success] Settings.py completed successfully."
exit 0
