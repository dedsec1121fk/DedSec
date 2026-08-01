#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / "Needs" / "Modules"
PACKAGES = ROOT / "Needs" / "Packages"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def read_manifest(path: Path) -> list[str]:
    if not path.is_file():
        return []
    result: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            result.append(line)
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_module_cache() -> tuple[int, int]:
    cache = MODULES / "Cache"
    manifest_path = cache / "cache-manifest.json"
    if not manifest_path.is_file():
        print("[cache warning] Python cache manifest is absent")
        return 0, 1
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = 0
    files = data.get("files", [])
    for entry in files:
        path = cache / entry["name"]
        if not path.is_file():
            print(f"[cache error] Missing Python artifact: {path.name}")
            errors += 1
        elif sha256(path) != entry["sha256"]:
            print(f"[cache error] Python checksum mismatch: {path.name}")
            errors += 1
    print(f"[cache] {len(files)} vendored Python artifacts checked")
    return len(files), errors


def verify_package_cache() -> tuple[int, int]:
    cache = PACKAGES / "Cache"
    manifest_path = cache / "cache-manifest.json"
    if not manifest_path.is_file():
        print("[cache warning] Termux cache manifest is absent; the workflow will create it")
        return 0, 1
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = 0
    entries = data.get("entries", [])
    for entry in entries:
        arch = entry.get("cache_architecture", entry.get("architecture", ""))
        directory = cache / arch
        stored = entry.get("stored_sha256", {})
        if entry.get("parts"):
            ordered_paths = [directory / name for name in entry["parts"]]
        else:
            ordered_paths = [directory / entry["file"]]
        logical = hashlib.sha256()
        for path in ordered_paths:
            if not path.is_file():
                print(f"[cache error] Missing Termux artifact: {path}")
                errors += 1
                continue
            expected = stored.get(path.name)
            if expected and sha256(path) != expected:
                print(f"[cache error] Stored-file checksum mismatch: {path}")
                errors += 1
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    logical.update(chunk)
        if all(path.is_file() for path in ordered_paths) and logical.hexdigest() != entry["sha256"]:
            print(f"[cache error] Reconstructed package checksum mismatch: {entry['package']}")
            errors += 1
    if entries:
        print(f"[cache] {len(entries)} vendored Termux package records checked")
    else:
        print("[cache warning] Termux cache has no packages yet; push or manually run the update workflow")
        errors += 1
    return len(entries), errors


def verify_package_locks() -> tuple[int, int]:
    errors = 0
    total_records = 0
    lock_paths = sorted(PACKAGES.glob("package-lock-*.json"))
    if not lock_paths:
        print("[lock error] No Termux package lock is present")
        return 0, 1

    required_roots = set(read_manifest(PACKAGES / "termux-required.txt"))
    for lock_path in lock_paths:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
        records = data.get("packages", data.get("entries", []))
        if not isinstance(records, list) or not records:
            print(f"[lock error] No package records in {lock_path.name}")
            errors += 1
            continue

        names: set[str] = set()
        calculated_size = 0
        for record in records:
            name = str(record.get("package", "")).strip()
            checksum = str(record.get("sha256", "")).lower()
            filename = str(record.get("filename", record.get("file", ""))).strip()
            if not name or name in names:
                print(f"[lock error] Missing or duplicate package in {lock_path.name}: {name!r}")
                errors += 1
            names.add(name)
            if not filename.endswith(".deb"):
                print(f"[lock error] Invalid package filename for {name}: {filename}")
                errors += 1
            if not SHA256_RE.fullmatch(checksum):
                print(f"[lock error] Invalid SHA-256 for {name}")
                errors += 1
            try:
                size = int(record.get("size", 0))
            except (TypeError, ValueError):
                size = 0
            if size <= 0:
                print(f"[lock error] Invalid package size for {name}")
                errors += 1
            calculated_size += max(size, 0)

        missing_roots = sorted(required_roots - names)
        if missing_roots:
            print(f"[lock error] Required roots absent from {lock_path.name}: {', '.join(missing_roots)}")
            errors += 1

        declared_count = data.get("package_count", data.get("count"))
        if declared_count is not None and int(declared_count) != len(records):
            print(f"[lock error] Record count mismatch in {lock_path.name}")
            errors += 1
        declared_size = data.get("total_size", data.get("total_size_bytes"))
        if declared_size is not None and int(declared_size) != calculated_size:
            print(f"[lock error] Total size mismatch in {lock_path.name}")
            errors += 1

        total_records += len(records)
        print(
            f"[lock] {lock_path.name}: {len(records)} package records, "
            f"{calculated_size / (1024 * 1024):.2f} MiB"
        )
    return total_records, errors


def verify_index_snapshots() -> tuple[int, int]:
    errors = 0
    checked = 0
    for manifest_path in sorted((PACKAGES / "Indexes").glob("*/index-manifest.json")):
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in data.get("files", []):
            path = manifest_path.parent / entry["name"]
            if not path.is_file():
                print(f"[index error] Missing snapshot: {path}")
                errors += 1
                continue
            if sha256(path) != entry["sha256"]:
                print(f"[index error] Snapshot checksum mismatch: {path.name}")
                errors += 1
                continue
            try:
                with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
                    prefix = handle.read(4096)
                if "Package:" not in prefix:
                    print(f"[index error] Snapshot is not a package index: {path.name}")
                    errors += 1
                    continue
            except OSError:
                print(f"[index error] Invalid gzip snapshot: {path.name}")
                errors += 1
                continue
            checked += 1
    if checked:
        print(f"[index] {checked} compressed repository snapshots checked")
    else:
        print("[index warning] No repository index snapshots were found")
        errors += 1
    return checked, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--installed", action="store_true", help="test the current device environment")
    parser.add_argument("--cache", action="store_true", help="validate vendored dependency artifacts")
    parser.add_argument("--lock", action="store_true", help="validate package locks and index snapshots")
    args = parser.parse_args()

    requirements = set(read_manifest(MODULES / "requirements.txt"))
    mapping = json.loads((MODULES / "import-map.json").read_text(encoding="utf-8"))
    missing_manifest = sorted({distribution for distribution in mapping.values() if distribution not in requirements})
    print(f"[manifest] {len(requirements)} Python distributions listed")
    print(f"[manifest] {len(read_manifest(PACKAGES / 'termux-required.txt'))} required Termux packages listed")
    if missing_manifest:
        print("[manifest error] Import-map distributions absent from requirements:", ", ".join(missing_manifest))
        return 2
    print("[manifest] Import map is fully covered")

    errors = 0
    if args.cache:
        _, module_errors = verify_module_cache()
        _, package_errors = verify_package_cache()
        errors += module_errors + package_errors
    if args.lock or args.cache:
        _, lock_errors = verify_package_locks()
        _, index_errors = verify_index_snapshots()
        errors += lock_errors + index_errors

    if args.installed:
        missing_imports: list[str] = []
        for module in sorted(mapping):
            try:
                if importlib.util.find_spec(module) is None:
                    missing_imports.append(module)
            except Exception:
                missing_imports.append(module)
        if missing_imports:
            print("[installed warning] Missing Python imports:", ", ".join(missing_imports))
            errors += 1
        else:
            print("[installed] All audited Python imports are available")

        commands = ["cloudflared", "ffmpeg", "git", "nmap", "ssh", "tor", "unrar", "whois"]
        missing_commands = [command for command in commands if shutil.which(command) is None]
        if missing_commands:
            print("[installed warning] Missing external commands:", ", ".join(missing_commands))
            errors += 1
        else:
            print("[installed] Core external commands are available")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
