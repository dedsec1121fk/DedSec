#!/data/data/com.termux/files/usr/bin/bash
set -u
# install.sh performs dependency setup, the one-time internal-Downloads save,
# and only then starts the DedSec menu.
ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
exec bash "$ROOT_DIR/Needs/install.sh" --run "$@"
