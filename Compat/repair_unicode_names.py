#!/usr/bin/env python3
"""Repair #Uhhhh-style filenames produced by some old unzip/locale combinations.

The source ZIP stores Greek paths as UTF-8. Some older Info-ZIP builds running under
an ASCII/POSIX locale extract non-ASCII filename characters as literal tokens such
as ``#U0395``. This helper reverses that escaping in-place before DedSec starts.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

TOKEN_RE = re.compile(r"#U([0-9A-Fa-f]{4,6})")


def decode_component(name: str) -> str:
    def replace(match: re.Match[str]) -> str:
        codepoint = int(match.group(1), 16)
        if codepoint > 0x10FFFF:
            return match.group(0)
        return chr(codepoint)

    return TOKEN_RE.sub(replace, name)


def repair_tree(root: Path) -> tuple[int, int]:
    repaired = 0
    skipped = 0

    # Rename deepest paths first so children remain reachable while parents move.
    candidates = [p for p in root.rglob("*") if TOKEN_RE.search(p.name)]
    candidates.sort(key=lambda p: len(p.parts), reverse=True)

    for path in candidates:
        if not path.exists():
            continue
        decoded = decode_component(path.name)
        if decoded == path.name:
            continue
        target = path.with_name(decoded)
        if target.exists():
            print(
                f"[unicode-repair] Skipped collision: {path} -> {target}",
                file=sys.stderr,
            )
            skipped += 1
            continue
        path.rename(target)
        repaired += 1

    return repaired, skipped


def main() -> int:
    root = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    root = root.resolve()
    if not root.is_dir():
        print(f"[unicode-repair] Project directory not found: {root}", file=sys.stderr)
        return 1

    repaired, skipped = repair_tree(root)
    if repaired:
        print(f"[unicode-repair] Restored {repaired} UTF-8 filename(s).")
    if skipped:
        print(f"[unicode-repair] {skipped} collision(s) were left unchanged.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
