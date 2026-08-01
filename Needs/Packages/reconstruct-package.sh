#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: bash reconstruct-package.sh OUTPUT.deb PART1 [PART2 ...]" >&2
  exit 2
fi

output="$1"
shift
cat "$@" > "$output"
