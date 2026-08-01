#!/usr/bin/env python3
"""Export the verified package cache manifest as a readable lock and TSV plan."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

PACKAGES = Path(__file__).resolve().parent
CACHE_MANIFEST = PACKAGES / "Cache" / "cache-manifest.json"


def read_manifest(path: Path) -> list[str]:
    result: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            result.append(line)
    return result


def main() -> int:
    data = json.loads(CACHE_MANIFEST.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    if not entries:
        raise RuntimeError("The Termux cache is empty; refusing to replace package lock files")

    grouped: dict[str, list[dict[str, object]]] = {}
    for original in entries:
        item = dict(original)
        arch = str(item.get("cache_architecture", item.get("architecture", "unknown")))
        source_url = str(item.get("source_url", ""))
        item.setdefault("filename", urlsplit(source_url).path.lstrip("/"))
        grouped.setdefault(arch, []).append(item)

    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    required_roots = read_manifest(PACKAGES / "termux-required.txt")
    optional_roots = read_manifest(PACKAGES / "termux-optional.txt")

    for architecture, architecture_entries in grouped.items():
        architecture_entries.sort(key=lambda entry: str(entry["package"]))
        previous_path = PACKAGES / f"package-lock-{architecture}.json"
        previous = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.is_file() else {}
        previous_by_package = {entry["package"]: entry for entry in previous.get("entries", [])}
        merged_entries: list[dict[str, object]] = []
        for entry in architecture_entries:
            old = previous_by_package.get(entry["package"], {})
            for key in ("depends", "pre_depends", "provides"):
                if key in old and key not in entry:
                    entry[key] = old[key]
            merged_entries.append(entry)

        lock = {
            "generated_at_utc": generated,
            "generated_from": "verified Needs/Packages/Cache/cache-manifest.json",
            "architecture": architecture,
            "required_roots": required_roots,
            "optional_roots": optional_roots,
            "missing_optional_roots": previous.get("missing_optional_roots", []),
            "package_count": len(merged_entries),
            "total_size_bytes": sum(int(entry.get("size", 0)) for entry in merged_entries),
            "entries": merged_entries,
        }
        previous_path.write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        tsv_path = PACKAGES / f"download-plan-{architecture}.tsv"
        with tsv_path.open("w", encoding="utf-8", newline="") as output:
            output.write("package\tversion\trepository\toptional\tsize\tsha256\turl\n")
            for entry in merged_entries:
                output.write(
                    f"{entry['package']}\t{entry.get('version', '')}\t{entry.get('repository', '')}\t"
                    f"{str(bool(entry.get('optional', False))).lower()}\t{entry.get('size', 0)}\t"
                    f"{entry.get('sha256', '')}\t{entry.get('source_url', '')}\n"
                )
        print(f"Exported {len(merged_entries)} package records for {architecture}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
