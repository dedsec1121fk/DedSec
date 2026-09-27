#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

if [ -n "${TERMUX_VERSION:-}" ] || [ -x /data/data/com.termux/files/usr/bin/pkg ] || [[ "${PREFIX:-}" == *com.termux* ]]; then
  PYTHON_BIN="$(command -v python || command -v python3)"
  export DEDSEC_PLATFORM=termux
else
  if [ ! -x "$ROOT_DIR/.venv/bin/python" ]; then
    echo '[error] Desktop environment is not set up yet. Run: bash Setup.sh' >&2
    exit 1
  fi
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
  export PATH="$ROOT_DIR/Compat/bin:$ROOT_DIR/.venv/bin:$PATH"
  export DEDSEC_PLATFORM=desktop-linux
  export DEDSEC_SAFE_CROSS_PLATFORM=1
fi

REPAIR_UNICODE="$ROOT_DIR/Compat/repair_unicode_names.py"
if [ -f "$REPAIR_UNICODE" ]; then
  if ! "$PYTHON_BIN" "$REPAIR_UNICODE" "$ROOT_DIR"; then
    echo '[warning] Unicode filename repair reported an error; continuing with existing paths.' >&2
  fi
fi

export DEDSEC_ROOT="$ROOT_DIR"
cd "$ROOT_DIR"
exec "$PYTHON_BIN" "$ROOT_DIR/Scripts/Settings.py" "$@"
