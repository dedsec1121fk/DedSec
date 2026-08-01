#!/data/data/com.termux/files/usr/bin/bash
set -u
ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
exec bash "$ROOT_DIR/Needs/install.sh" "$@"
