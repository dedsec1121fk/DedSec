#!/usr/bin/env python3
"""Refresh vendored Python archives and Termux packages safely.

The new dependency set is fully downloaded into a staging directory and
validated before the current cache is replaced. If any required download or
validation fails, the existing cache is left untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
NEEDS = ROOT / "Needs"
MODULES = NEEDS / "Modules"
PACKAGES = NEEDS / "Packages"
USER_AGENT = "DedSec-Dependency-Maintainer/1.0"
MAX_GITHUB_FILE = 45 * 1024 * 1024
SOURCE_REPOSITORY_OVERRIDES = {
    "psd-tools": "https://github.com/psd-tools/psd-tools",
}

REPOSITORIES = (
    (
        "main",
        "stable",
        (
            "https://packages.termux.dev/apt/termux-main",
            "https://packages-cf.termux.dev/apt/termux-main",
            "https://termux.librehat.com/apt/termux-main",
            "https://mirror.fcix.net/termux/termux-main",
            "https://mirrors.sdu.edu.cn/termux/termux-main",
        ),
    ),
    (
        "x11",
        "x11",
        (
            "https://packages.termux.dev/apt/termux-x11",
            "https://packages-cf.termux.dev/apt/termux-x11",
            "https://termux.librehat.com/apt/termux-x11",
            "https://mirror.fcix.net/termux/termux-x11",
            "https://mirrors.sdu.edu.cn/termux/termux-x11",
        ),
    ),
)


def read_manifest(path: Path) -> list[str]:
    values: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            values.append(line)
    return values


def run(command: list[str], *, cwd: Path | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path, *, attempts: int = 3) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".download")
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        temporary.unlink(missing_ok=True)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=240) as response, temporary.open("wb") as output:
                shutil.copyfileobj(response, output, length=1024 * 1024)
            temporary.replace(destination)
            return
        except Exception as exc:
            last_error = exc
            temporary.unlink(missing_ok=True)
            if attempt < attempts:
                delay = min(2 ** (attempt - 1), 8)
                print(f"Download attempt {attempt}/{attempts} failed for {url}: {exc}; retrying in {delay}s")
                time.sleep(delay)
    raise RuntimeError(f"Could not download {url} after {attempts} attempts: {last_error}")



def canonical_distribution_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).strip("-").lower()


def github_repository_url(distribution: str, payload: dict[str, object]) -> str | None:
    canonical = canonical_distribution_name(distribution)
    override = SOURCE_REPOSITORY_OVERRIDES.get(canonical)
    if override:
        return override.rstrip("/")

    info = payload.get("info", {})
    if not isinstance(info, dict):
        return None
    candidates: list[str] = []
    project_urls = info.get("project_urls", {})
    if isinstance(project_urls, dict):
        preferred_keys = ("source", "source code", "repository", "code", "homepage")
        ordered = sorted(
            project_urls.items(),
            key=lambda item: (
                preferred_keys.index(str(item[0]).strip().lower())
                if str(item[0]).strip().lower() in preferred_keys
                else len(preferred_keys)
            ),
        )
        candidates.extend(str(value) for _key, value in ordered if value)
    home_page = info.get("home_page")
    if home_page:
        candidates.append(str(home_page))

    for candidate in candidates:
        match = re.match(r"https?://github\.com/([^/]+)/([^/#?]+)", candidate.strip())
        if not match:
            continue
        owner, repository = match.groups()
        repository = repository.removesuffix(".git")
        if owner and repository:
            return f"https://github.com/{owner}/{repository}"
    return None


def validate_python_source_archive(path: Path) -> None:
    try:
        with tarfile.open(path, mode="r:*") as archive:
            members = archive.getmembers()
    except (tarfile.TarError, OSError) as exc:
        raise RuntimeError(f"Invalid source archive {path.name}: {exc}") from exc

    metadata_names = {"pyproject.toml", "setup.py", "setup.cfg"}
    if not any(Path(member.name).name in metadata_names for member in members if member.isfile()):
        raise RuntimeError(f"Source archive lacks Python build metadata: {path.name}")


def download_github_source_archive(
    distribution: str,
    version: str,
    payload: dict[str, object],
    destination: Path,
) -> Path:
    repository_url = github_repository_url(distribution, payload)
    if not repository_url:
        raise RuntimeError(
            f"PyPI provides no source distribution and no GitHub source repository "
            f"was found for {distribution}=={version}"
        )

    filename = f"{canonical_distribution_name(distribution)}-{version}.tar.gz"
    target = destination / filename
    errors: list[str] = []
    for tag in (f"v{version}", version):
        encoded_tag = urllib.parse.quote(tag, safe="")
        url = f"{repository_url}/archive/refs/tags/{encoded_tag}.tar.gz"
        try:
            download(url, target)
            validate_python_source_archive(target)
            print(f"Saved verified GitHub source archive: {target} ({tag})", flush=True)
            return target
        except Exception as exc:
            target.unlink(missing_ok=True)
            errors.append(f"{url}: {exc}")

    raise RuntimeError(
        f"Could not obtain a usable source archive for {distribution}=={version}: "
        + " | ".join(errors)
    )

def download_pypi_sdist(
    distribution: str,
    destination: Path,
    *,
    version: str | None = None,
) -> Path:
    """Download a source distribution without invoking a package build backend.

    ``pip download --no-binary`` may execute PEP 517 metadata hooks. Some
    projects, including lxml, then require native development headers even
    though we only want to archive their untouched source distribution. PyPI's
    JSON API exposes the exact source file and checksum, so the maintenance job
    can download and verify it directly. If a release publishes only platform
    wheels, its immutable GitHub tag archive is validated and stored instead.
    """
    quoted_name = urllib.parse.quote(distribution, safe="")
    if version is None:
        metadata_url = f"https://pypi.org/pypi/{quoted_name}/json"
    else:
        quoted_version = urllib.parse.quote(version, safe="")
        metadata_url = f"https://pypi.org/pypi/{quoted_name}/{quoted_version}/json"

    request = urllib.request.Request(metadata_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=180) as response:
        payload = json.load(response)

    resolved_version = version or str(payload.get("info", {}).get("version", "")).strip()
    candidates = [
        item for item in payload.get("urls", []) if item.get("packagetype") == "sdist"
    ]
    if not candidates:
        if not resolved_version:
            raise RuntimeError(f"PyPI did not report a version for {distribution}")
        return download_github_source_archive(
            distribution,
            resolved_version,
            payload,
            destination,
        )

    # Prefer the conventional tar.gz source archive when more than one format
    # is published, while remaining compatible with ZIP-only projects.
    candidates.sort(
        key=lambda item: (
            0 if str(item.get("filename", "")).endswith(".tar.gz") else 1,
            str(item.get("filename", "")),
        )
    )
    selected = candidates[0]
    filename = str(selected.get("filename", "")).strip()
    url = str(selected.get("url", "")).strip()
    expected_sha256 = str(selected.get("digests", {}).get("sha256", "")).strip().lower()
    if not filename or not url or not expected_sha256:
        raise RuntimeError(f"Incomplete PyPI source metadata for {distribution}")

    target = destination / filename
    download(url, target)
    actual_sha256 = sha256(target).lower()
    if actual_sha256 != expected_sha256:
        target.unlink(missing_ok=True)
        raise RuntimeError(
            f"Checksum mismatch for {filename}: expected {expected_sha256}, got {actual_sha256}"
        )
    print(f"Saved verified PyPI source archive: {target}", flush=True)
    return target


def parse_control(text: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for block in re.split(r"\n\s*\n", text.strip()):
        record: dict[str, str] = {}
        current = ""
        for line in block.splitlines():
            if line.startswith((" ", "\t")) and current:
                record[current] += "\n" + line.strip()
                continue
            if ":" not in line:
                continue
            current, value = line.split(":", 1)
            record[current] = value.strip()
        if record.get("Package"):
            records.append(record)
    return records


def split_large_file(path: Path) -> list[Path]:
    if path.stat().st_size <= MAX_GITHUB_FILE:
        return [path]
    parts: list[Path] = []
    with path.open("rb") as source:
        index = 1
        while True:
            chunk = source.read(MAX_GITHUB_FILE)
            if not chunk:
                break
            part = path.with_name(f"{path.name}.part{index:03d}")
            part.write_bytes(chunk)
            parts.append(part)
            index += 1
    path.unlink()
    return parts


def refresh_python(stage: Path) -> dict[str, object]:
    stage.mkdir(parents=True, exist_ok=True)
    requirements = MODULES / "requirements.txt"

    # Resolve the complete runtime dependency closure using the runner. Universal
    # wheels are portable to Termux. Runner-specific wheels are replaced with
    # the exact matching source distribution.
    try:
        run(
            [
                sys.executable,
                "-m",
                "pip",
                "download",
                "--disable-pip-version-check",
                "--dest",
                str(stage),
                "--requirement",
                str(requirements),
            ]
        )
        platform_wheels: list[tuple[str, str, Path]] = []
        try:
            from packaging.utils import parse_wheel_filename
        except ImportError as exc:
            raise RuntimeError("The maintenance runner requires the packaging module") from exc

        for wheel_path in sorted(stage.glob("*.whl")):
            if wheel_path.name.endswith("-none-any.whl"):
                continue
            distribution, version, _build, _tags = parse_wheel_filename(wheel_path.name)
            platform_wheels.append((str(distribution), str(version), wheel_path))

        for distribution, version, wheel_path in platform_wheels:
            # Fetch the untouched sdist from PyPI instead of asking pip to
            # prepare metadata. Metadata preparation can execute native build
            # checks (for example lxml requiring libxml2/libxslt headers).
            download_pypi_sdist(distribution, stage, version=version)
            wheel_path.unlink()

        # Common PEP 517 build backends are cached as well. This makes source
        # builds much more reliable when Setup is run with limited connectivity.
        build_helpers = [
            "setuptools",
            "wheel",
            "packaging",
            "pyproject-hooks",
            "flit-core",
            "hatchling",
            "hatch-vcs",
            "setuptools-scm",
            "meson-python",
            "Cython",
            "maturin",
        ]
        for helper in build_helpers:
            try:
                run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "download",
                        "--disable-pip-version-check",
                        "--no-deps",
                        "--only-binary=:all:",
                        "--platform=any",
                        "--implementation=py",
                        "--abi=none",
                        "--dest",
                        str(stage),
                        helper,
                    ]
                )
            except subprocess.CalledProcessError:
                download_pypi_sdist(helper, stage)
        resolution = "full-portable-runtime-closure"
    except (subprocess.CalledProcessError, RuntimeError) as exc:
        raise RuntimeError(
            "A complete portable Python dependency closure could not be built; "
            "the existing module cache has not been changed."
        ) from exc


    files = sorted(path for path in stage.iterdir() if path.is_file())
    if not files:
        raise RuntimeError("Python cache is empty")
    manifest = {
        "generated_by": "Needs/Maintenance/update_vendored_dependencies.py",
        "resolution": resolution,
        "files": [
            {"name": path.name, "size": path.stat().st_size, "sha256": sha256(path)}
            for path in files
        ],
    }
    (stage / "cache-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


@dataclass(frozen=True)
class PackageRecord:
    repository: str
    base_url: str
    package: str
    version: str
    architecture: str
    filename: str
    size: int
    sha256: str
    depends: str
    pre_depends: str
    provides: str


def load_termux_index(repository: str, suite: str, base_url: str, architecture: str) -> dict[str, PackageRecord]:
    index_url = f"{base_url}/dists/{suite}/main/binary-{architecture}/Packages"
    request = urllib.request.Request(index_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=180) as response:
        text = response.read().decode("utf-8", errors="replace")
    result: dict[str, PackageRecord] = {}
    for item in parse_control(text):
        package = item.get("Package", "")
        filename = item.get("Filename", "")
        checksum = item.get("SHA256", "")
        if not package or not filename or not checksum:
            continue
        result[package] = PackageRecord(
            repository=repository,
            base_url=base_url,
            package=package,
            version=item.get("Version", "unknown"),
            architecture=item.get("Architecture", architecture),
            filename=filename,
            size=int(item.get("Size", "0") or 0),
            sha256=checksum,
            depends=item.get("Depends", ""),
            pre_depends=item.get("Pre-Depends", ""),
            provides=item.get("Provides", ""),
        )
    return result


def dependency_names(value: str) -> list[list[str]]:
    groups: list[list[str]] = []
    for group in value.split(","):
        alternatives: list[str] = []
        for alternative in group.split("|"):
            name = re.sub(r"\s*\([^)]*\)", "", alternative).strip()
            name = name.split(":", 1)[0].strip()
            if name:
                alternatives.append(name)
        if alternatives:
            groups.append(alternatives)
    return groups


def resolve_package_closure(
    roots: Iterable[str], indexes: list[dict[str, PackageRecord]]
) -> tuple[dict[str, PackageRecord], list[str]]:
    combined: dict[str, PackageRecord] = {}
    providers: dict[str, str] = {}
    for index in indexes:
        for name, record in index.items():
            combined.setdefault(name, record)
            for provided_group in dependency_names(record.provides):
                for provided in provided_group:
                    providers.setdefault(provided, name)

    resolved: dict[str, PackageRecord] = {}
    missing: list[str] = []
    queue = list(roots)
    while queue:
        requested = queue.pop(0)
        actual = requested if requested in combined else providers.get(requested, requested)
        if actual in resolved:
            continue
        record = combined.get(actual)
        if record is None:
            missing.append(requested)
            continue
        resolved[actual] = record
        for alternatives in dependency_names(",".join(filter(None, [record.pre_depends, record.depends]))):
            selected = next(
                (name for name in alternatives if name in combined or name in providers),
                alternatives[0],
            )
            queue.append(selected)
    return resolved, sorted(set(missing))


def refresh_termux(stage: Path) -> dict[str, object]:
    required = read_manifest(PACKAGES / "termux-required.txt")
    optional = read_manifest(PACKAGES / "termux-optional.txt")
    architectures = read_manifest(PACKAGES / "architectures.txt")
    if not architectures:
        raise RuntimeError("No Termux cache architecture is configured")

    all_entries: list[dict[str, object]] = []
    for architecture in architectures:
        architecture_dir = stage / architecture
        architecture_dir.mkdir(parents=True, exist_ok=True)
        indexes: list[dict[str, PackageRecord]] = []
        for repository, suite, base_urls in REPOSITORIES:
            loaded: dict[str, PackageRecord] | None = None
            last_error: Exception | None = None
            for base_url in base_urls:
                try:
                    loaded = load_termux_index(repository, suite, base_url, architecture)
                    if loaded:
                        break
                except Exception as exc:
                    last_error = exc
            if loaded:
                indexes.append(loaded)
            else:
                print(f"Warning: could not read {repository} index for {architecture}: {last_error}")
                indexes.append({})

        required_closure, missing_required = resolve_package_closure(required, indexes)
        if missing_required:
            raise RuntimeError(
                f"Required Termux packages absent for {architecture}: " + ", ".join(missing_required)
            )
        optional_closure: dict[str, PackageRecord] = {}
        for optional_root in optional:
            closure, missing_optional = resolve_package_closure([optional_root], indexes)
            if missing_optional:
                print(f"Optional Termux package not found: {optional_root} ({architecture})")
                continue
            optional_closure.update(closure)

        package_records = dict(optional_closure)
        package_records.update(required_closure)
        repository_mirrors = {name: urls for name, _suite, urls in REPOSITORIES}
        for package in sorted(package_records):
            record = package_records[package]
            optional_item = package not in required_closure
            encoded_filename = "/".join(urllib.parse.quote(part, safe="+") for part in record.filename.split("/"))
            destination = architecture_dir / Path(record.filename).name
            candidate_bases = list(dict.fromkeys((record.base_url, *repository_mirrors[record.repository])))
            selected_url = ""
            failures: list[str] = []
            for base_url in candidate_bases:
                url = f"{base_url}/{encoded_filename}"
                print(f"Downloading {package} {record.version} for {architecture} from {base_url}")
                try:
                    download(url, destination)
                    actual_hash = sha256(destination)
                    if actual_hash.lower() != record.sha256.lower():
                        raise RuntimeError(f"checksum {actual_hash} != {record.sha256}")
                    selected_url = url
                    break
                except Exception as exc:
                    destination.unlink(missing_ok=True)
                    failures.append(f"{url}: {exc}")
                    print(f"Mirror failed for {package}: {exc}")
            if not selected_url:
                raise RuntimeError(
                    f"Every configured mirror failed for {package} {record.version}: " + " | ".join(failures)
                )
            parts = split_large_file(destination)
            all_entries.append(
                {
                    "package": package,
                    "optional": optional_item,
                    "version": record.version,
                    "architecture": record.architecture,
                    "cache_architecture": architecture,
                    "repository": record.repository,
                    "source_url": selected_url,
                    "mirror_urls": [f"{base}/{encoded_filename}" for base in candidate_bases],
                    "sha256": record.sha256,
                    "size": record.size,
                    "filename": record.filename,
                    "depends": record.depends,
                    "pre_depends": record.pre_depends,
                    "provides": record.provides,
                    "file": destination.name,
                    "parts": [part.name for part in parts] if len(parts) > 1 else [],
                    "stored_sha256": {part.name: sha256(part) for part in parts},
                }
            )

    manifest = {
        "generated_by": "Needs/Maintenance/update_vendored_dependencies.py",
        "github_file_limit_bytes": MAX_GITHUB_FILE,
        "entries": all_entries,
    }
    (stage / "cache-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def validate_cache(path: Path) -> None:
    manifest_path = path / "cache-manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"Missing cache manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if "files" in manifest:
        for entry in manifest["files"]:
            artifact = path / entry["name"]
            if not artifact.is_file() or sha256(artifact) != entry["sha256"]:
                raise RuntimeError(f"Invalid Python cache artifact: {artifact}")
    if "entries" in manifest:
        for entry in manifest["entries"]:
            architecture_dir = path / entry.get("cache_architecture", entry["architecture"])
            stored = entry.get("stored_sha256", {})
            for name, expected in stored.items():
                artifact = architecture_dir / name
                if not artifact.is_file() or sha256(artifact) != expected:
                    raise RuntimeError(f"Invalid Termux cache artifact: {artifact}")


def replace_after_staging(new_cache: Path, current_cache: Path) -> None:
    """Keep current_cache until new_cache is complete, then swap with rollback."""
    incoming = current_cache.with_name(current_cache.name + ".new")
    backup = current_cache.with_name(current_cache.name + ".old")
    # Recover a previous interrupted swap before starting a new one.
    if not current_cache.exists() and backup.exists():
        backup.replace(current_cache)
    elif current_cache.exists() and backup.exists():
        shutil.rmtree(backup, ignore_errors=True)
    shutil.rmtree(incoming, ignore_errors=True)
    shutil.copytree(new_cache, incoming)
    validate_cache(incoming)
    try:
        if current_cache.exists():
            current_cache.replace(backup)
        incoming.replace(current_cache)
    except Exception:
        if current_cache.exists():
            shutil.rmtree(current_cache, ignore_errors=True)
        if backup.exists():
            backup.replace(current_cache)
        raise
    shutil.rmtree(backup, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--modules-only", action="store_true")
    parser.add_argument("--packages-only", action="store_true")
    args = parser.parse_args()
    if args.modules_only and args.packages_only:
        parser.error("Choose at most one of --modules-only and --packages-only")

    with tempfile.TemporaryDirectory(prefix="dedsec-needs-") as temporary:
        staging = Path(temporary)
        if not args.packages_only:
            module_stage = staging / "Modules"
            refresh_python(module_stage)
            validate_cache(module_stage)
        if not args.modules_only:
            package_stage = staging / "Packages"
            refresh_termux(package_stage)
            validate_cache(package_stage)

        # No existing cache is changed before every requested staging operation succeeds.
        if not args.packages_only:
            replace_after_staging(staging / "Modules", MODULES / "Cache")
        if not args.modules_only:
            replace_after_staging(staging / "Packages", PACKAGES / "Cache")

    print("Vendored dependency caches updated successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
