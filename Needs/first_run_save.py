#!/usr/bin/env python3
"""Create the one-time DedSec Project save in Android internal Downloads."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import zipfile
from pathlib import Path

ARCHIVE_NAME = "DedSec Project.zip"
ARCHIVE_ROOT = "DedSec Project"
MARKER_NAME = ".first-run-download-save-complete.json"


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def downloads_directory() -> Path | None:
    """Return only Android's internal-storage Downloads directory."""
    termux_downloads = Path.home() / "storage" / "downloads"
    if termux_downloads.is_dir():
        return termux_downloads

    android_downloads = Path("/storage/emulated/0/Download")
    if android_downloads.is_dir() and os.access(android_downloads, os.W_OK):
        return android_downloads
    return None


def should_exclude(relative: Path) -> bool:
    parts = relative.parts
    if not parts:
        return False
    if parts[0] in {".git", "__pycache__"}:
        return True
    if "__pycache__" in parts:
        return True
    if relative.suffix == ".pyc":
        return True
    if parts[:2] == ("Needs", "Logs"):
        return True
    if parts[:2] == ("Needs", "State"):
        return True
    return False


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_archive(root: Path, target: Path) -> tuple[int, str]:
    temporary = target.with_name(f".{target.name}.new-{os.getpid()}")
    temporary.unlink(missing_ok=True)
    file_count = 0

    try:
        with zipfile.ZipFile(
            temporary,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
            allowZip64=True,
        ) as archive:
            for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
                relative = path.relative_to(root)
                if should_exclude(relative):
                    continue
                archive_name = (Path(ARCHIVE_ROOT) / relative).as_posix()
                if path.is_dir():
                    info = zipfile.ZipInfo(archive_name.rstrip("/") + "/")
                    info.external_attr = (0o40755 & 0xFFFF) << 16
                    archive.writestr(info, b"")
                elif path.is_file():
                    archive.write(path, archive_name)
                    file_count += 1

        with zipfile.ZipFile(temporary, "r") as archive:
            corrupt = archive.testzip()
            if corrupt is not None:
                raise RuntimeError(f"ZIP validation failed at {corrupt}")

        checksum = sha256(temporary)
        # os.replace keeps the old archive until the complete new archive exists.
        os.replace(temporary, target)
        return file_count, checksum
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    root = project_root()
    state_dir = root / "Needs" / "State"
    marker = state_dir / MARKER_NAME

    if marker.is_file():
        print("[first-run save] Already completed; no additional save was created.")
        return 0

    downloads = downloads_directory()
    if downloads is None:
        print(
            "[first-run save] Android internal Downloads is unavailable. "
            "Approve storage access; the next Setup.sh run will retry.",
            file=sys.stderr,
        )
        return 1

    downloads.mkdir(parents=True, exist_ok=True)
    target = downloads / ARCHIVE_NAME
    print(f"[first-run save] Creating {target}")
    count, checksum = build_archive(root, target)

    state_dir.mkdir(parents=True, exist_ok=True)
    marker_data = {
        "schema": 1,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "archive": str(target),
        "files": count,
        "sha256": checksum,
    }
    temporary_marker = marker.with_suffix(marker.suffix + ".tmp")
    temporary_marker.write_text(
        json.dumps(marker_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary_marker, marker)
    print(f"[first-run save] Complete: {count} files saved only to Android Downloads.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
