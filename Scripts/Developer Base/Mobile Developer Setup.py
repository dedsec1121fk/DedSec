#!/usr/bin/env python3

import argparse
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

# -----------------------------------------------------------------------------
# Mobile Developer Setup for Termux
#
# Design goals:
# - Safe to re-run (idempotent where practical)
# - Core tools fail loudly; optional tools fail independently
# - Never assume this standalone .py file lives inside a Git repository
# - Preserve user configuration with backups before destructive changes
# - Track paths created by this script so uninstall does not delete user files
# - Use current package releases instead of hard-pinning stale npm versions
# -----------------------------------------------------------------------------

HOME = Path.home()
APP_DIR = HOME / ".mobile-dev-setup"
BACKUPS_DIR = APP_DIR / "backups"
NVI_BACKUPS_DIR = APP_DIR / "nvim-backups"
STATE_FILE = APP_DIR / "state.json"
LOG_FILE = APP_DIR / "last-run.log"
TOOLS_DIR = HOME / ".mobile-dev-setup-tools"
TERMUX_DIR = HOME / ".termux"
ZSH_PLUGINS_DIR = HOME / ".zsh-plugins"
OH_MY_ZSH_DIR = HOME / ".oh-my-zsh"
NVIM_CONFIG_DIR = HOME / ".config" / "nvim"
NVIM_DATA_DIR = HOME / ".local" / "share" / "nvim"
NVIM_STATE_DIR = HOME / ".local" / "state" / "nvim"


# Termux global shell configuration. DedSec Settings.py writes its shell
# integration here, while this setup uses Zsh as the authoritative shell.
PREFIX = Path(os.environ.get("PREFIX") or "/data/data/com.termux/files/usr")
GLOBAL_BASHRC = PREFIX / "etc" / "bash.bashrc"
GLOBAL_PROFILE = PREFIX / "etc" / "profile"

DEDSEC_MENU_START = "# --- DedSec Menu Startup (Set by Settings.py) ---"
DEDSEC_MENU_END = "# --------------------------------------------------"
DEDSEC_NETWORK_START = "# --- DedSec VPN and Tor Utilities (Set by Settings.py) ---"
DEDSEC_NETWORK_END = "# --- End DedSec VPN and Tor Utilities ---"

ZSH_HANDOFF_START = "# >>> MOBILE DEV SETUP ZSH HANDOFF >>>"
ZSH_HANDOFF_END = "# <<< MOBILE DEV SETUP ZSH HANDOFF <<<"

MARK_BEGIN = "# >>> MOBILE DEV SETUP (managed) >>>"
MARK_END = "# <<< MOBILE DEV SETUP (managed) <<<"

DEFAULT_FONT_ARCHIVE_URLS = (
    "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/Meslo.tar.xz",
    "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/Meslo.zip",
)

OH_MY_ZSH_REPO = "https://github.com/ohmyzsh/ohmyzsh.git"
NVCHAD_STARTER_REPO = "https://github.com/NvChad/starter.git"


@dataclass(frozen=True)
class TermuxPackage:
    name: str
    required: bool = False
    note: str = ""


@dataclass(frozen=True)
class NpmTool:
    package: str
    command: str
    required: bool = False


CORE_PACKAGES = [
    TermuxPackage("git", True),
    TermuxPackage("zsh", True),
    TermuxPackage("neovim", True),
    TermuxPackage("nodejs", True),
    TermuxPackage("npm", True),
    TermuxPackage("python", True),
    TermuxPackage("python-pip", True),
    TermuxPackage("curl", True),
    TermuxPackage("wget", True),
    TermuxPackage("jq", True),
    TermuxPackage("ripgrep", True),
    TermuxPackage("fzf", True),
    TermuxPackage("bat", True),
    TermuxPackage("clang", True),
    TermuxPackage("make", True),
    TermuxPackage("unzip", True),
    TermuxPackage("zip", True),
]

DEVELOPER_PACKAGES = [
    # Languages and runtimes
    TermuxPackage("gh", True),
    TermuxPackage("perl", True),
    TermuxPackage("php", True),
    TermuxPackage("ruby", True),
    TermuxPackage("rust", True),
    TermuxPackage("rust-analyzer", True),
    TermuxPackage("golang", True),
    TermuxPackage("openjdk-21", True),
    TermuxPackage("lua54", True),
    TermuxPackage("lua-language-server", True),
    TermuxPackage("stylua", True),

    # Build systems, compilers and debugging
    TermuxPackage("cmake", True),
    TermuxPackage("ninja", True),
    TermuxPackage("xmake", True),
    TermuxPackage("pkg-config", True),
    TermuxPackage("autoconf", True),
    TermuxPackage("automake", True),
    TermuxPackage("libtool", True),
    TermuxPackage("bison", True),
    TermuxPackage("flex", True),
    TermuxPackage("m4", True),
    TermuxPackage("patch", True),
    TermuxPackage("ccache", True),
    TermuxPackage("binutils", True),
    TermuxPackage("gdb", True),
    TermuxPackage("protobuf", True),
    TermuxPackage("gradle", True),
    TermuxPackage("maven", True),

    # Editors, code navigation and quality tools
    TermuxPackage("vim", True),
    TermuxPackage("nano", True),
    TermuxPackage("shellcheck", True),
    TermuxPackage("shfmt", True),
    TermuxPackage("tree-sitter", True),
    TermuxPackage("fd", True),
    TermuxPackage("lsd", True),

    # Version control, remote development and terminal workflow
    TermuxPackage("git-lfs", True),
    TermuxPackage("subversion", True),
    TermuxPackage("openssh", True),
    TermuxPackage("rsync", True),
    TermuxPackage("tmux", True),
    TermuxPackage("tmate", True),
    TermuxPackage("cloudflared", True),

    # Databases and data tooling
    TermuxPackage("postgresql", True),
    TermuxPackage("mariadb", True),
    TermuxPackage("sqlite", True),
    TermuxPackage("redis", True),

    # General developer utilities
    TermuxPackage("proot", True),
    TermuxPackage("ncurses-utils", True),
    TermuxPackage("translate-shell", True),
    TermuxPackage("html2text", True),
    TermuxPackage("bc", True),
    TermuxPackage("tree", True),
    TermuxPackage("imagemagick", True),
    TermuxPackage("tur-repo", True, note="Repository package required for TUR developer packages such as mongodb."),
]

# Developer tools whose upstream-supported installation path on Termux is Python/pip.
# Keep these out of the pkg phase so missing Termux repository packages do not
# incorrectly make the whole Termux package installation fail.
PYTHON_DEVELOPER_TOOLS = [
    ("meson", "meson"),
    ("mercurial", "hg"),
]

TUR_PACKAGES = [
    TermuxPackage("mongodb", True, note="Termux User Repository database package."),
]

NPM_TOOLS = [
    NpmTool("@devcorex/dev.x", "dev.x"),
    NpmTool("typescript", "tsc"),
    NpmTool("@nestjs/cli", "nest"),
    NpmTool("prettier", "prettier"),
    NpmTool("live-server", "live-server"),
    NpmTool("localtunnel", "lt"),
    NpmTool("vercel", "vercel"),
    NpmTool("markserv", "markserv"),
    NpmTool("psqlformat", "psqlformat"),
    NpmTool("@google/gemini-cli", "gemini"),
    NpmTool("@qwen-code/qwen-code", "qwen"),
    NpmTool("npm-check-updates", "ncu"),
    NpmTool("ngrok", "ngrok"),
    NpmTool("eslint", "eslint"),
    NpmTool("yarn", "yarn"),
    NpmTool("pnpm", "pnpm"),
    NpmTool("vite", "vite"),
    NpmTool("nodemon", "nodemon"),
    NpmTool("http-server", "http-server"),
    NpmTool("serve", "serve"),
    NpmTool("typescript-language-server", "typescript-language-server"),
]

# name, repository, zsh source/fpath line
ZSH_PLUGIN_REPOS = [
    (
        "zsh-defer",
        "https://github.com/romkatv/zsh-defer.git",
        "source ~/.zsh-plugins/zsh-defer/zsh-defer.plugin.zsh",
    ),
    (
        "powerlevel10k",
        "https://github.com/romkatv/powerlevel10k.git",
        "source ~/.zsh-plugins/powerlevel10k/powerlevel10k.zsh-theme",
    ),
    (
        "zsh-autosuggestions",
        "https://github.com/zsh-users/zsh-autosuggestions.git",
        "source ~/.zsh-plugins/zsh-autosuggestions/zsh-autosuggestions.zsh",
    ),
    (
        "zsh-syntax-highlighting",
        "https://github.com/zsh-users/zsh-syntax-highlighting.git",
        "source ~/.zsh-plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh",
    ),
    (
        "zsh-history-substring-search",
        "https://github.com/zsh-users/zsh-history-substring-search.git",
        "source ~/.zsh-plugins/zsh-history-substring-search/zsh-history-substring-search.zsh",
    ),
    (
        "zsh-completions",
        "https://github.com/zsh-users/zsh-completions.git",
        "fpath+=(~/.zsh-plugins/zsh-completions/src)",
    ),
    (
        "fzf-tab",
        "https://github.com/Aloxaf/fzf-tab.git",
        "source ~/.zsh-plugins/fzf-tab/fzf-tab.plugin.zsh",
    ),
    (
        "zsh-you-should-use",
        "https://github.com/MichaelAquilina/zsh-you-should-use.git",
        "source ~/.zsh-plugins/zsh-you-should-use/you-should-use.plugin.zsh",
    ),
    (
        "zsh-autopair",
        "https://github.com/hlissner/zsh-autopair.git",
        "source ~/.zsh-plugins/zsh-autopair/autopair.zsh",
    ),
    (
        "zsh-better-npm-completion",
        "https://github.com/lukechilds/zsh-better-npm-completion.git",
        "source ~/.zsh-plugins/zsh-better-npm-completion/zsh-better-npm-completion.plugin.zsh",
    ),
    (
        "zsh-autocomplete",
        "https://github.com/marlonrichert/zsh-autocomplete.git",
        "source ~/.zsh-plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh",
    ),
]

BACKUP_TARGETS = [
    TERMUX_DIR / "termux.properties",
    TERMUX_DIR / "colors.properties",
    TERMUX_DIR / "font.ttf",
    HOME / ".zshrc",
    HOME / ".bashrc",
    HOME / ".profile",
    GLOBAL_BASHRC,
    GLOBAL_PROFILE,
]


class C:
    OK = "\033[92m"
    INFO = "\033[96m"
    WARN = "\033[93m"
    ERR = "\033[91m"
    DIM = "\033[2m"
    END = "\033[0m"


class RunSummary:
    def __init__(self) -> None:
        self.ok: list[str] = []
        self.warn: list[str] = []
        self.failed: list[str] = []

    def clear(self) -> None:
        self.ok.clear()
        self.warn.clear()
        self.failed.clear()

    def success(self, message: str) -> None:
        self.ok.append(message)
        print(c(f"✓ {message}", C.OK))

    def warning(self, message: str) -> None:
        self.warn.append(message)
        print(c(f"! {message}", C.WARN))

    def failure(self, message: str) -> None:
        self.failed.append(message)
        print(c(f"✗ {message}", C.ERR))

    def show(self) -> None:
        header("Run summary")
        print(f"Successful: {len(self.ok)}")
        print(f"Warnings:   {len(self.warn)}")
        print(f"Failed:     {len(self.failed)}")
        if self.warn:
            print(c("\nWarnings:", C.WARN))
            for item in self.warn:
                print(f"  - {item}")
        if self.failed:
            print(c("\nFailures:", C.ERR))
            for item in self.failed:
                print(f"  - {item}")


SUMMARY = RunSummary()
ASSUME_YES = False
NON_INTERACTIVE = False


def supports_color() -> bool:
    return sys.stdout.isatty() and os.environ.get("TERM", "") not in ("", "dumb")


def c(text: str, color: str) -> str:
    return f"{color}{text}{C.END}" if supports_color() else text


def header(title: str) -> None:
    print("\n" + c("═" * 62, C.DIM))
    print(c(f"  {title}", C.INFO))
    print(c("═" * 62, C.DIM))


def ensure_dirs() -> None:
    for p in (APP_DIR, BACKUPS_DIR, NVI_BACKUPS_DIR, TOOLS_DIR):
        p.mkdir(parents=True, exist_ok=True)


def is_termux() -> bool:
    prefix = os.environ.get("PREFIX", "")
    return shutil.which("pkg") is not None and bool(prefix)


def require_termux() -> bool:
    if is_termux():
        return True
    print(c("This script must be run inside Termux.", C.ERR))
    print("Run it with: python 'Mobile Developer Setup.py'")
    return False


def quote_cmd(args: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(x)) for x in args)


def log_line(text: str) -> None:
    ensure_dirs()
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")


def run_cmd(
    args: list[str],
    *,
    check: bool = False,
    capture: bool = False,
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
) -> subprocess.CompletedProcess:
    command_text = quote_cmd(args)
    log_line(f"$ {command_text}")
    kwargs = {
        "cwd": str(cwd) if cwd else None,
        "env": env,
        "text": True,
    }
    if capture:
        kwargs.update({"stdout": subprocess.PIPE, "stderr": subprocess.PIPE})
    result = subprocess.run(args, **kwargs)
    if capture:
        if result.stdout:
            log_line(result.stdout)
        if result.stderr:
            log_line(result.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {command_text}")
    return result


def run_shell(command: str, *, check: bool = False, capture: bool = False) -> subprocess.CompletedProcess:
    return run_cmd(["bash", "-lc", command], check=check, capture=capture)


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    if ASSUME_YES:
        return True
    if NON_INTERACTIVE:
        return default
    suffix = " [Y/n] " if default else " [y/N] "
    while True:
        answer = input(c(prompt + suffix, C.INFO)).strip().lower()
        if not answer:
            return default
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print(c("Please answer y or n.", C.WARN))


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def atomic_write_text(path: Path, content: str, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(temp_path, mode)
        temp_path.replace(path)
    finally:
        temp_path.unlink(missing_ok=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def now_stamp() -> str:
    # Include sub-second precision so multiple backups in one second cannot collide.
    return time.strftime("%Y%m%d-%H%M%S") + f"-{time.time_ns() % 1_000_000:06d}"


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict) -> None:
    ensure_dirs()
    atomic_write_text(STATE_FILE, json.dumps(state, indent=2, sort_keys=True) + "\n")


def mark_managed_path(path: Path) -> None:
    state = load_state()
    managed = set(state.get("managed_paths", []))
    managed.add(str(path))
    state["managed_paths"] = sorted(managed)
    save_state(state)


def is_managed_path(path: Path) -> bool:
    return str(path) in set(load_state().get("managed_paths", []))


def safe_notify(message: str) -> None:
    if shutil.which("termux-toast"):
        run_cmd(["termux-toast", message], check=False, capture=True)


# -----------------------------------------------------------------------------
# Backup / restore
# -----------------------------------------------------------------------------


def _backup_archive_name(target: Path) -> str:
    """Build a safe archive path for files below Termux HOME or PREFIX."""
    for root, label in ((HOME, "home"), (PREFIX, "prefix")):
        try:
            rel = target.relative_to(root)
            return f"{label}/{rel.as_posix()}"
        except ValueError:
            continue
    raise ValueError(f"Unsupported backup target: {target}")


def _safe_restore_target(target: Path) -> bool:
    """Allow restores only inside Termux HOME or PREFIX."""
    candidate = target.resolve(strict=False)
    for root in (HOME.resolve(strict=False), PREFIX.resolve(strict=False)):
        if candidate == root or root in candidate.parents:
            return True
    return False


def make_backup() -> Path:
    ensure_dirs()
    stamp = now_stamp()
    out = BACKUPS_DIR / f"termux-settings-backup-{stamp}.tar.gz"
    manifest = {
        "created": stamp,
        "home": str(HOME),
        "prefix": str(PREFIX),
        "targets": [],
        "note": "Termux settings/config backup created before Mobile Developer Setup changes.",
    }

    with tarfile.open(out, "w:gz") as tf:
        for target in BACKUP_TARGETS:
            existed = target.exists() and target.is_file()
            item = {"path": str(target), "existed": existed}
            if existed:
                item["mode"] = target.stat().st_mode & 0o777
                item["archive_name"] = _backup_archive_name(target)
                item["sha256"] = sha256_file(target)
                tf.add(str(target), arcname=item["archive_name"], recursive=False)
            manifest["targets"].append(item)

        payload = json.dumps(manifest, indent=2).encode("utf-8")
        info = tarfile.TarInfo("manifest.json")
        info.size = len(payload)
        info.mtime = int(time.time())
        tf.addfile(info, io.BytesIO(payload))

    state = load_state()
    state["last_backup"] = str(out)
    backups = set(state.get("backups", []))
    backups.add(str(out))
    state["backups"] = sorted(backups)
    save_state(state)
    SUMMARY.success(f"Backup saved: {out}")
    return out


def list_backups() -> list[Path]:
    ensure_dirs()
    return sorted(BACKUPS_DIR.glob("termux-settings-backup-*.tar.gz"), reverse=True)


def _load_backup_manifest(tf: tarfile.TarFile) -> dict:
    member = tf.getmember("manifest.json")
    fileobj = tf.extractfile(member)
    if fileobj is None:
        raise RuntimeError("Backup manifest is unreadable.")
    data = json.loads(fileobj.read().decode("utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("targets"), list):
        raise RuntimeError("Backup manifest is invalid.")
    return data


def restore_backup(backup_path: Path) -> None:
    if not backup_path.exists():
        raise FileNotFoundError(str(backup_path))

    header("Restoring Termux settings")
    with tarfile.open(backup_path, "r:gz") as tf:
        manifest = _load_backup_manifest(tf)
        for item in manifest["targets"]:
            target_raw = item.get("path")
            if not isinstance(target_raw, str):
                continue
            target = Path(target_raw)

            if not _safe_restore_target(target):
                SUMMARY.warning(f"Skipped unsafe backup path: {target}")
                continue

            if not item.get("existed", False):
                if target.exists() and target.is_file():
                    target.unlink()
                    SUMMARY.success(f"Removed file that did not exist at backup time: {target}")
                continue

            archive_name = item.get("archive_name")
            if not isinstance(archive_name, str) or not archive_name.startswith(("home/", "prefix/", "files/")):
                SUMMARY.warning(f"Missing archive entry for {target}")
                continue

            try:
                member = tf.getmember(archive_name)
                source = tf.extractfile(member)
            except KeyError:
                source = None
            if source is None:
                SUMMARY.warning(f"Backup data missing for {target}")
                continue

            data = source.read()
            expected = item.get("sha256")
            if expected:
                actual = hashlib.sha256(data).hexdigest()
                if actual != expected:
                    raise RuntimeError(f"Backup integrity check failed for {target}")

            target.parent.mkdir(parents=True, exist_ok=True)
            fd, temp_name = tempfile.mkstemp(prefix=target.name + ".", dir=str(target.parent))
            temp = Path(temp_name)
            try:
                with os.fdopen(fd, "wb") as f:
                    f.write(data)
                    f.flush()
                    os.fsync(f.fileno())
                temp.replace(target)
                mode = item.get("mode")
                if isinstance(mode, int):
                    os.chmod(target, mode)
            finally:
                temp.unlink(missing_ok=True)
            SUMMARY.success(f"Restored {target}")

    reload_termux_settings()

def choose_backup_interactive() -> Optional[Path]:
    backups = list_backups()
    if not backups:
        print(c(f"No backups found in {BACKUPS_DIR}", C.WARN))
        return None
    if NON_INTERACTIVE:
        return backups[0]

    print(c("\nAvailable backups:", C.INFO))
    for idx, backup in enumerate(backups, 1):
        print(f"  {idx}) {backup.name}")
    while True:
        answer = input(c("Pick a backup number (0 to cancel): ", C.INFO)).strip()
        if answer == "0":
            return None
        if answer.isdigit() and 1 <= int(answer) <= len(backups):
            return backups[int(answer) - 1]
        print(c("Invalid choice.", C.WARN))


# -----------------------------------------------------------------------------
# Termux package management
# -----------------------------------------------------------------------------


def dpkg_installed(package: str) -> bool:
    if not shutil.which("dpkg-query"):
        return False
    result = run_cmd(
        ["dpkg-query", "-W", "-f=${Status}", package],
        capture=True,
        check=False,
    )
    return result.returncode == 0 and "install ok installed" in (result.stdout or "")


def pkg_refresh(upgrade: bool = True) -> bool:
    header("Refreshing Termux repositories")
    update = run_cmd(["pkg", "update", "-y"], check=False)
    if update.returncode != 0:
        SUMMARY.failure("pkg update failed. Check your Termux mirror/network, then retry.")
        return False
    SUMMARY.success("Termux package lists refreshed")

    if upgrade:
        result = run_cmd(["pkg", "upgrade", "-y"], check=False)
        if result.returncode == 0:
            SUMMARY.success("Installed Termux packages upgraded")
        else:
            SUMMARY.warning("pkg upgrade reported an error; setup will continue with individual installs")
    return True


def install_one_pkg(package: TermuxPackage, *, force: bool = False) -> bool:
    if not force and dpkg_installed(package.name):
        SUMMARY.success(f"{package.name} already installed")
        return True

    result = run_cmd(["pkg", "install", "-y", package.name], check=False)
    ok = result.returncode == 0 and dpkg_installed(package.name)
    if ok:
        SUMMARY.success(f"Installed {package.name}")
    elif package.required:
        SUMMARY.failure(f"Required Termux package failed: {package.name}")
    else:
        suffix = f" ({package.note})" if package.note else ""
        SUMMARY.warning(f"Optional Termux package skipped/failed: {package.name}{suffix}")
    return ok


def install_packages(*, force: bool = False) -> bool:
    header("Installing complete Termux developer package set")
    all_ok = True

    for package in CORE_PACKAGES:
        all_ok = install_one_pkg(package, force=force) and all_ok

    header("Installing additional required developer tools")
    for package in DEVELOPER_PACKAGES:
        all_ok = install_one_pkg(package, force=force) and all_ok

    # mongodb lives in TUR, so enable tur-repo first and refresh package indexes
    # before attempting its installation.
    if dpkg_installed("tur-repo"):
        header("Installing required Termux User Repository packages")
        refresh = run_cmd(["pkg", "update", "-y"], check=False)
        if refresh.returncode != 0:
            SUMMARY.failure("TUR repository refresh failed")
            all_ok = False
        for package in TUR_PACKAGES:
            all_ok = install_one_pkg(package, force=force) and all_ok
    else:
        SUMMARY.failure("tur-repo was not installed, so mongodb cannot be installed")
        all_ok = False

    return all_ok



# -----------------------------------------------------------------------------
# Python developer tools
# -----------------------------------------------------------------------------


def python_pip_available() -> bool:
    python_bin = shutil.which("python") or shutil.which("python3")
    if not python_bin:
        return False
    result = run_cmd([python_bin, "-m", "pip", "--version"], capture=True, check=False)
    return result.returncode == 0


def install_python_developer_tools(*, update: bool = False) -> bool:
    """Install required developer tools whose supported distribution path is PyPI."""
    header("Installing required Python developer tools")
    python_bin = shutil.which("python") or shutil.which("python3")
    if not python_bin:
        SUMMARY.failure("Python is unavailable, so Python developer tools cannot be installed")
        return False
    if not python_pip_available():
        SUMMARY.failure("python-pip is unavailable. Run Repair after python-pip is installed")
        return False

    all_ok = True
    for package, command in PYTHON_DEVELOPER_TOOLS:
        if not update and shutil.which(command):
            SUMMARY.success(f"{package} already installed")
            continue

        args = [
            python_bin, "-m", "pip", "install",
            "--disable-pip-version-check", "--no-input",
        ]
        if update:
            args.append("--upgrade")
        args.append(package)

        result = run_cmd(args, check=False)
        if result.returncode == 0 and shutil.which(command):
            action = "Updated" if update else "Installed"
            SUMMARY.success(f"{action} Python developer tool {package}")
        else:
            SUMMARY.failure(f"Required Python developer tool failed: {package}")
            all_ok = False
    return all_ok

# -----------------------------------------------------------------------------
# Legacy DedSec Bash environment cleanup
# -----------------------------------------------------------------------------


def _looks_like_dedsec_ps1(line: str) -> bool:
    stripped = line.lstrip()
    return (
        stripped.startswith("PS1=")
        and r"\D{%d/%m/%Y}" in line
        and r"\A" in line
        and r"\W" in line
    )



def extract_dedsec_prompt_name(text: str) -> str:
    """Extract the visible username from the DedSec Settings.py PS1, if present."""
    for line in text.splitlines():
        if not _looks_like_dedsec_ps1(line):
            continue
        match = re.search(r"1;34m\\\]([^\\'\n]+?)\\\[\\e\[0m", line)
        if match:
            return sanitize_prompt_name(match.group(1))
    return ""


def clean_dedsec_bash_environment() -> bool:
    """Remove only shell hooks created by DedSec Settings.py.

    Settings.py itself is not modified, and unrelated Bash configuration is kept.
    The global bash.bashrc is included in the safety backup before this runs.
    """
    header("Removing legacy DedSec Bash environment")
    if not GLOBAL_BASHRC.exists():
        SUMMARY.success("No global bash.bashrc exists to clean")
        return True

    original = read_text(GLOBAL_BASHRC)

    # Preserve the user's existing DedSec prompt identity before removing Bash PS1.
    if not get_prompt_name():
        migrated_prompt = extract_dedsec_prompt_name(original)
        if migrated_prompt:
            state = load_state()
            state["prompt_name"] = migrated_prompt
            save_state(state)
            SUMMARY.success(f"Migrated DedSec prompt name to Zsh: {migrated_prompt}")

    output: list[str] = []
    mode: Optional[str] = None

    for line in original.splitlines(keepends=True):
        if mode == "menu":
            if DEDSEC_MENU_END in line:
                mode = None
            continue
        if mode == "network":
            if DEDSEC_NETWORK_END in line:
                mode = None
            continue
        if mode == "background":
            if line.startswith("# --- End DedSec ") and "Background Checker" in line:
                mode = None
            continue

        if DEDSEC_MENU_START in line:
            mode = "menu"
            continue
        if DEDSEC_NETWORK_START in line:
            mode = "network"
            continue
        if line.startswith("# --- DedSec ") and "Background Checker" in line:
            mode = "background"
            continue

        stripped = line.strip()
        dedsec_settings_line = "DedSec/Scripts" in line and "Settings.py" in line
        dedsec_alias = bool(re.search(r"^\s*alias\s+(?:m|e|g)=", line)) and dedsec_settings_line
        dedsec_startup = dedsec_settings_line and "--menu" in line
        dedsec_scan = "Settings.py" in line and "--pipboy-scan" in line

        if dedsec_alias or dedsec_startup or dedsec_scan or _looks_like_dedsec_ps1(line):
            continue
        if stripped in {"dedsec_network_session_guard", "dedsec_network_session_guard;"}:
            continue
        output.append(line)

    cleaned = "".join(output)
    if cleaned == original:
        SUMMARY.success("No active DedSec shell overrides found in bash.bashrc")
        return True

    temp = APP_DIR / "bash.bashrc.cleaned.tmp"
    mode_bits = GLOBAL_BASHRC.stat().st_mode & 0o777
    atomic_write_text(temp, cleaned, mode=mode_bits)
    if shutil.which("bash"):
        check = run_cmd(["bash", "-n", str(temp)], capture=True, check=False)
        if check.returncode != 0:
            temp.unlink(missing_ok=True)
            SUMMARY.failure("DedSec cleanup produced invalid bash.bashrc syntax; original file was kept")
            if check.stderr:
                print(check.stderr.rstrip())
            return False

    atomic_write_text(GLOBAL_BASHRC, cleaned, mode=mode_bits)
    temp.unlink(missing_ok=True)
    state = load_state()
    state["dedsec_bash_environment_overridden"] = True
    save_state(state)
    SUMMARY.success("Removed DedSec PS1, menu autostart, aliases and network hooks from global bash.bashrc")
    return True


# -----------------------------------------------------------------------------
# npm tools
# -----------------------------------------------------------------------------


def npm_package_installed(package: str) -> bool:
    if not shutil.which("npm"):
        return False
    result = run_cmd(["npm", "list", "-g", "--depth=0", "--json", package], capture=True, check=False)
    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return False
    dependencies = payload.get("dependencies", {})
    return isinstance(dependencies, dict) and package in dependencies


def ensure_npm_available() -> bool:
    """Ensure npm exists on current Termux, where npm is a separate package."""
    if shutil.which("npm"):
        return True
    if not is_termux():
        SUMMARY.failure("npm is unavailable")
        return False

    # npm is now an official standalone Termux package. Refresh first and install
    # npm by itself so apt can select a compatible nodejs/nodejs-lts dependency.
    run_cmd(["pkg", "update", "-y"], check=False)
    attempts = [
        ["pkg", "install", "-y", "npm"],
        ["apt", "install", "-y", "npm"],
    ]
    for command in attempts:
        if not shutil.which(command[0]):
            continue
        result = run_cmd(command, check=False)
        if result.returncode == 0 and shutil.which("npm"):
            SUMMARY.success("npm installed and available")
            return True

    # Final recovery: upgrade the installed Node.js package, then retry npm.
    node_package = "nodejs-lts" if dpkg_installed("nodejs-lts") else "nodejs"
    run_cmd(["pkg", "upgrade", "-y", node_package], check=False)
    result = run_cmd(["pkg", "install", "-y", "npm"], check=False)
    if result.returncode == 0 and shutil.which("npm"):
        SUMMARY.success("npm installed after updating Node.js")
        return True

    SUMMARY.failure("npm could not be installed from the active Termux repositories")
    return False


def install_npm_tools(*, update: bool = False) -> None:
    header("Installing global npm developer tools")
    if not ensure_npm_available():
        return
    env = os.environ.copy()
    env["npm_config_audit"] = "false"
    env["npm_config_fund"] = "false"
    env["npm_config_update_notifier"] = "false"
    for tool in NPM_TOOLS:
        if not update and npm_package_installed(tool.package):
            SUMMARY.success(f"npm: {tool.package} already installed")
            continue
        spec = f"{tool.package}@latest"
        result = run_cmd(["npm", "install", "-g", spec], env=env, check=False)
        if result.returncode == 0:
            SUMMARY.success(f"npm: installed {spec}")
        elif tool.required:
            SUMMARY.failure(f"Required npm tool failed: {tool.package}")
        else:
            SUMMARY.warning(f"Optional npm tool failed: {tool.package}")

def patch_localtunnel_android_openurl() -> None:
    """Make localtunnel --open launch URLs correctly on Android/Termux."""
    candidates: list[Path] = []

    if shutil.which("npm"):
        root_result = run_cmd(["npm", "root", "-g"], capture=True, check=False)
        root = (root_result.stdout or "").strip()
        if root_result.returncode == 0 and root:
            candidates.append(Path(root) / "localtunnel" / "bin" / "lt.js")

    lt_bin = shutil.which("lt")
    if lt_bin:
        try:
            candidates.append(Path(lt_bin).resolve())
        except OSError:
            candidates.append(Path(lt_bin))

    target = next((p for p in candidates if p.exists() and p.is_file()), None)
    if target is None:
        return

    text = read_text(target)
    marker = "MOBILE DEV SETUP ANDROID OPEN"
    if marker in text or ("termux-open-url" in text and "process.platform" in text):
        SUMMARY.success("localtunnel Android browser integration already configured")
        return

    needle = "openurl.open(tunnel.url);"
    if needle not in text:
        # localtunnel is optional. If upstream changes again, do not report a false
        # setup warning for a browser convenience feature that does not block setup.
        return

    replacement = (
        "// MOBILE DEV SETUP ANDROID OPEN\n"
        "    if (process.platform === 'android') {\n"
        "      const child = require('child_process').spawn('termux-open-url', [tunnel.url], {\n"
        "        detached: true,\n"
        "        stdio: 'ignore',\n"
        "      });\n"
        "      child.on('error', () => {});\n"
        "      child.unref();\n"
        "    } else {\n"
        "      openurl.open(tunnel.url);\n"
        "    }"
    )
    patched = text.replace(needle, replacement, 1)
    atomic_write_text(target, patched, mode=0o755)
    SUMMARY.success("Configured localtunnel --open for Android/Termux")


# -----------------------------------------------------------------------------
# Zsh / Oh My Zsh
# -----------------------------------------------------------------------------


def git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def clone_or_update_repo(name: str, repo: str, dest: Path, *, update: bool = False) -> bool:
    if dest.exists():
        if git_repo(dest):
            if update and is_managed_path(dest):
                result = run_cmd(["git", "-C", str(dest), "pull", "--ff-only"], check=False)
                if result.returncode == 0:
                    SUMMARY.success(f"Updated {name}")
                    return True
                SUMMARY.warning(f"Could not update {name}; existing checkout kept")
                return True
            SUMMARY.success(f"{name} already present")
            return True
        SUMMARY.warning(f"{name} path already exists but is not a Git checkout; left untouched: {dest}")
        return False

    result = run_cmd(["git", "clone", "--depth=1", repo, str(dest)], check=False)
    if result.returncode == 0:
        mark_managed_path(dest)
        SUMMARY.success(f"Installed {name}")
        return True
    shutil.rmtree(dest, ignore_errors=True)
    SUMMARY.warning(f"Could not install {name}")
    return False


def install_oh_my_zsh(*, update: bool = False) -> None:
    header("Oh My Zsh")
    if not shutil.which("zsh") or not shutil.which("git"):
        SUMMARY.warning("Oh My Zsh skipped because zsh or git is unavailable")
        return
    clone_or_update_repo("Oh My Zsh", OH_MY_ZSH_REPO, OH_MY_ZSH_DIR, update=update)


def install_zsh_plugins(*, update: bool = False) -> None:
    header("Zsh plugins")
    if not shutil.which("git"):
        SUMMARY.warning("Zsh plugins skipped because git is unavailable")
        return
    ZSH_PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    for name, repo, _ in ZSH_PLUGIN_REPOS:
        clone_or_update_repo(name, repo, ZSH_PLUGINS_DIR / name, update=update)


def _zsh_plugin_lines() -> tuple[list[str], list[str]]:
    fpath_lines: list[str] = []
    source_lines: list[str] = []
    for name, _, line in ZSH_PLUGIN_REPOS:
        # Powerlevel10k is installed but deliberately not started automatically.
        # Its wizard and prompt are opt-in through the dedicated menu action.
        if name == "powerlevel10k":
            continue
        dest = ZSH_PLUGINS_DIR / name
        if not dest.exists():
            continue
        if line.startswith("fpath"):
            if (dest / "src").is_dir():
                fpath_lines.append(line)
            else:
                SUMMARY.warning(f"Skipped incomplete Zsh plugin: {name}")
            continue

        match = re.match(r"source\s+(.+)$", line)
        if not match:
            continue
        source_path = Path(os.path.expanduser(match.group(1)))
        if source_path.is_file():
            source_lines.append(line)
        else:
            SUMMARY.warning(f"Skipped incomplete Zsh plugin: {name}")
    return fpath_lines, source_lines


def sanitize_prompt_name(name: str) -> str:
    """Sanitize a persistent Zsh prompt name using DedSec-compatible characters."""
    name = (name or "").strip()
    name = re.sub(r"[^A-Za-z0-9_.@-]", "_", name)
    return name[:48]


def get_prompt_name() -> str:
    value = load_state().get("prompt_name", "")
    return sanitize_prompt_name(value) if isinstance(value, str) else ""


def powerlevel10k_config_path() -> Path:
    return HOME / ".p10k.zsh"


def powerlevel10k_config_exists() -> bool:
    path = powerlevel10k_config_path()
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def powerlevel10k_enabled() -> bool:
    return bool(load_state().get("powerlevel10k_enabled", False))


def _save_powerlevel10k_state(enabled: bool, *, personalization_complete: Optional[bool] = None) -> None:
    state = load_state()
    state["powerlevel10k_enabled"] = bool(enabled)
    if personalization_complete is not None:
        state["shell_personalization_complete"] = bool(personalization_complete)
    save_state(state)


def adopt_existing_powerlevel10k_config(*, announce: bool = True) -> bool:
    """Use an existing ~/.p10k.zsh instead of asking the user to configure it again."""
    if not powerlevel10k_config_exists():
        return False
    _save_powerlevel10k_state(True, personalization_complete=bool(get_prompt_name()))
    if announce:
        SUMMARY.success("Existing Powerlevel10k configuration detected and reused")
    return True


def _powerlevel10k_zsh_lines() -> list[str]:
    """Source Powerlevel10k only when it has been configured or explicitly enabled."""
    if not powerlevel10k_enabled():
        return []
    theme = ZSH_PLUGINS_DIR / "powerlevel10k" / "powerlevel10k.zsh-theme"
    if not theme.is_file():
        SUMMARY.warning("Powerlevel10k is enabled but its theme file is missing")
        return []
    return [
        # The automatic upstream wizard is always disabled. Setup launches it explicitly
        # only when first-run configuration is actually required.
        "typeset -g POWERLEVEL9K_DISABLE_CONFIGURATION_WIZARD=true",
        "source ~/.zsh-plugins/powerlevel10k/powerlevel10k.zsh-theme",
        "[[ -f ~/.p10k.zsh ]] && source ~/.p10k.zsh",
    ]


def _powerlevel10k_prompt_name_lines() -> list[str]:
    """Add the saved prompt name as a Powerlevel10k custom segment."""
    if not powerlevel10k_enabled():
        return []
    name = get_prompt_name()
    if not name:
        return []
    quoted = shlex.quote(name)
    return [
        f"export MOBILE_DEV_PROMPT_NAME={quoted}",
        "function prompt_mobile_dev_name() {",
        "  p10k segment -f 12 -t \"$MOBILE_DEV_PROMPT_NAME\"",
        "}",
        "typeset -ga POWERLEVEL9K_LEFT_PROMPT_ELEMENTS",
        "if [[ \" ${POWERLEVEL9K_LEFT_PROMPT_ELEMENTS[*]} \" != *\" mobile_dev_name \"* ]]; then",
        "  POWERLEVEL9K_LEFT_PROMPT_ELEMENTS=(mobile_dev_name ${POWERLEVEL9K_LEFT_PROMPT_ELEMENTS[@]})",
        "fi",
    ]


def zsh_prompt_lines() -> list[str]:
    """Return the fallback DedSec-style Zsh prompt when Powerlevel10k is not active."""
    if powerlevel10k_enabled():
        return []
    name = get_prompt_name()
    if not name:
        return ["PROMPT='%F{green}%n@%m%f %F{blue}%~%f %# '"]
    quoted = shlex.quote(name)
    return [
        "setopt PROMPT_SUBST",
        f"export MOBILE_DEV_PROMPT_NAME={quoted}",
        "PROMPT='%F{cyan}%D{%d/%m/%Y}%f-%F{cyan}[%D{%H:%M}]%f-(%F{blue}${MOBILE_DEV_PROMPT_NAME}%f)-(%F{yellow}%~%f) : '",
        "RPROMPT=''",
    ]


def configure_zshrc() -> None:
    """Fully replace ~/.zshrc with the environment owned by this setup."""
    header("Fully configuring ~/.zshrc")
    zshrc = HOME / ".zshrc"
    fpath_lines, source_lines = _zsh_plugin_lines()

    lines = [
        MARK_BEGIN,
        "# Mobile Developer Setup exclusively manages this ~/.zshrc while installed.",
        "# Bash startup files are intentionally not sourced from Zsh.",
        'export SHELL="$(command -v zsh)"',
        'unset PROMPT_COMMAND 2>/dev/null || true',
        # Never let Powerlevel10k launch its wizard on ordinary terminal startup.
        "typeset -g POWERLEVEL9K_DISABLE_CONFIGURATION_WIZARD=true",
        'HISTFILE="$HOME/.zsh_history"',
        "HISTSIZE=10000",
        "SAVEHIST=10000",
        "setopt HIST_IGNORE_DUPS SHARE_HISTORY AUTO_CD INTERACTIVE_COMMENTS",
        "autoload -Uz colors && colors",
        "",
    ]
    lines.extend(fpath_lines)
    if fpath_lines:
        lines.append("")

    if (OH_MY_ZSH_DIR / "oh-my-zsh.sh").is_file():
        lines.extend([
            'export ZSH="$HOME/.oh-my-zsh"',
            'ZSH_THEME=""',
            '[[ -f "$ZSH/oh-my-zsh.sh" ]] && source "$ZSH/oh-my-zsh.sh"',
            "",
        ])
    else:
        lines.extend(["autoload -Uz compinit", "compinit -d ~/.zcompdump", ""])

    lines.extend(source_lines)
    if source_lines:
        lines.append("")

    p10k_lines = _powerlevel10k_zsh_lines()
    lines.extend(p10k_lines)
    if p10k_lines:
        lines.append("")
        # Keep the saved prompt identity even when Powerlevel10k owns the prompt.
        lines.extend(_powerlevel10k_prompt_name_lines())
        if get_prompt_name():
            lines.append("")

    lines.extend([
        "if (( $+functions[history-substring-search-up] )); then",
        "  bindkey '^[[A' history-substring-search-up",
        "  bindkey '^[[B' history-substring-search-down",
        "fi",
        "zstyle ':completion:*' menu-select yes",
        "zstyle ':fzf-tab:*' switch-word yes",
        "command -v lsd >/dev/null 2>&1 && alias ls='lsd'",
        "command -v bat >/dev/null 2>&1 && alias cat='bat --theme=Dracula --style=plain --paging=never'",
        "",
    ])

    lines.extend(zsh_prompt_lines())
    lines.extend([MARK_END, ""])

    atomic_write_text(zshrc, "\n".join(lines))
    state = load_state()
    state["zshrc_owned_by_setup"] = True
    save_state(state)

    result = run_cmd(["zsh", "-n", str(zshrc)], capture=True, check=False)
    if result.returncode == 0:
        SUMMARY.success("~/.zshrc fully replaced and syntax-checked")
    else:
        SUMMARY.failure("New ~/.zshrc failed zsh syntax validation; use the safety backup to restore")
        if result.stderr:
            print(result.stderr.rstrip())


def set_prompt_name(name: str, *, activate: bool = False) -> bool:
    """Persist the prompt name without disabling an existing Powerlevel10k setup."""
    clean = sanitize_prompt_name(name)
    state = load_state()
    state["prompt_name"] = clean
    state["shell_personalization_complete"] = bool(clean and powerlevel10k_config_exists())
    save_state(state)

    if not shutil.which("zsh"):
        SUMMARY.warning("Prompt name was saved, but Zsh is not installed yet")
        return False

    configure_zshrc()
    if clean:
        SUMMARY.success(f"Prompt name set to: {clean}")
        if powerlevel10k_enabled():
            SUMMARY.success("Prompt name integrated into the active Powerlevel10k prompt")
    else:
        SUMMARY.success("Custom prompt name removed")

    if activate:
        activate_zsh_now()
    return True


def _default_prompt_name() -> str:
    for candidate in (os.environ.get("USER"), os.environ.get("LOGNAME"), "developer"):
        clean = sanitize_prompt_name(candidate or "")
        if clean:
            return clean
    return "developer"


def ensure_first_run_prompt_name() -> bool:
    """Require a prompt identity once, while reusing any migrated/saved value."""
    current = get_prompt_name()
    if current:
        SUMMARY.success(f"Existing Zsh prompt name reused: {current}")
        return True

    default = _default_prompt_name()
    if NON_INTERACTIVE:
        state = load_state()
        state["prompt_name"] = default
        save_state(state)
        SUMMARY.warning(f"Non-interactive setup used default prompt name: {default}")
        return True

    header("First-time Zsh prompt setup")
    while True:
        entered = input(c(f"Prompt name [{default}]: ", C.INFO)).strip()
        clean = sanitize_prompt_name(entered or default)
        if clean:
            state = load_state()
            state["prompt_name"] = clean
            save_state(state)
            SUMMARY.success(f"Zsh prompt name configured: {clean}")
            return True
        print(c("Enter a valid prompt name.", C.WARN))


def run_powerlevel10k_wizard(
    *,
    required: bool = False,
    activate: bool = False,
    make_safety_backup: bool = True,
) -> bool:
    """Configure Powerlevel10k explicitly; never from ordinary shell startup."""
    if not require_termux():
        return False

    existing_before = powerlevel10k_config_exists()
    header("Powerlevel10k configuration" + (" — required first setup" if required else ""))

    if existing_before:
        adopt_existing_powerlevel10k_config(announce=True)
        configure_zshrc()
        if activate:
            activate_zsh_now()
        return True

    if NON_INTERACTIVE:
        _save_powerlevel10k_state(False, personalization_complete=False)
        configure_zshrc()
        SUMMARY.warning("Powerlevel10k first-time configuration is pending because this run is non-interactive")
        return False

    if not required:
        if not ask_yes_no("Run the Powerlevel10k configuration wizard now?", default=True):
            return False

    if make_safety_backup:
        make_backup()

    theme = ZSH_PLUGINS_DIR / "powerlevel10k" / "powerlevel10k.zsh-theme"
    if not theme.is_file():
        clone_or_update_repo(
            "powerlevel10k",
            "https://github.com/romkatv/powerlevel10k.git",
            ZSH_PLUGINS_DIR / "powerlevel10k",
            update=False,
        )
    if not theme.is_file():
        SUMMARY.failure("Powerlevel10k could not be installed")
        return False

    # Allow at most two attempts during required first-time setup. If the user cancels,
    # the setup is marked incomplete but the wizard will NOT reappear on every terminal start.
    attempts = 2 if required else 1
    for attempt in range(attempts):
        _save_powerlevel10k_state(True, personalization_complete=False)
        configure_zshrc()
        zsh_path = shutil.which("zsh")
        if not zsh_path:
            SUMMARY.failure("Zsh is unavailable")
            return False

        wizard = run_cmd([zsh_path, "-ic", 'source "$HOME/.zshrc"; p10k configure'], check=False)
        if wizard.returncode == 0 and powerlevel10k_config_exists():
            _save_powerlevel10k_state(True, personalization_complete=bool(get_prompt_name()))
            configure_zshrc()
            SUMMARY.success("Powerlevel10k configuration completed and saved")
            if activate:
                activate_zsh_now()
            return True

        if attempt + 1 < attempts:
            if not ask_yes_no("Powerlevel10k setup was not completed. Run the wizard again?", default=True):
                break

    _save_powerlevel10k_state(False, personalization_complete=False)
    configure_zshrc()
    SUMMARY.warning("Powerlevel10k setup remains incomplete. It will not open automatically on terminal startup; use menu option 9 to finish it.")
    if activate:
        activate_zsh_now()
    return False


def ensure_first_run_shell_personalization() -> bool:
    """Complete one-time prompt + Powerlevel10k setup, reusing existing configuration."""
    prompt_ok = ensure_first_run_prompt_name()

    if powerlevel10k_config_exists():
        adopt_existing_powerlevel10k_config(announce=True)
        configure_zshrc()
        state = load_state()
        state["shell_personalization_complete"] = bool(prompt_ok)
        save_state(state)
        return prompt_ok

    state = load_state()
    if state.get("shell_personalization_complete") and powerlevel10k_enabled():
        # State claims completion but the actual config is gone; repair it now.
        state["shell_personalization_complete"] = False
        state["powerlevel10k_enabled"] = False
        save_state(state)

    p10k_ok = run_powerlevel10k_wizard(required=True, activate=False, make_safety_backup=False)
    return bool(prompt_ok and p10k_ok)


def change_prompt_name_interactive() -> None:
    SUMMARY.clear()
    if not require_termux():
        return
    current = get_prompt_name()
    header("Zsh Prompt Name")
    print("Current name:", current or "(default prompt)")
    print("The name is also shown inside Powerlevel10k when Powerlevel10k is configured.")
    print("Leave it empty to remove the custom prompt name.")
    name = input(c("New prompt name: ", C.INFO)).strip()
    make_backup()
    set_prompt_name(name, activate=False)
    SUMMARY.show()
    if shutil.which("zsh"):
        activate_zsh_now()


def configure_powerlevel10k_interactive() -> None:
    """Configure or reconfigure Powerlevel10k only when selected from the menu."""
    SUMMARY.clear()
    if not require_termux():
        return
    make_backup()
    ok = run_powerlevel10k_wizard(required=False, activate=False, make_safety_backup=False)
    if ok:
        state = load_state()
        state["shell_personalization_complete"] = bool(get_prompt_name() and powerlevel10k_config_exists())
        save_state(state)
    SUMMARY.show()
    if shutil.which("zsh"):
        activate_zsh_now()


def set_default_zsh() -> bool:
    """Force Zsh as Termux's default shell instead of leaving Bash active."""
    zsh_path = shutil.which("zsh")
    if not zsh_path:
        SUMMARY.failure("Zsh is unavailable, so it cannot be set as the default shell")
        return False
    chsh_path = shutil.which("chsh")
    if not chsh_path:
        SUMMARY.warning("chsh is unavailable; persistent Bash-to-Zsh handoff will be used")
        return False

    result = run_cmd([chsh_path, "-s", zsh_path], capture=True, check=False)
    if result.returncode != 0:
        SUMMARY.warning("chsh failed; persistent Bash-to-Zsh handoff will still force Zsh on interactive starts")
        if result.stderr:
            print(result.stderr.rstrip())
        return False

    os.environ["SHELL"] = zsh_path
    state = load_state()
    state["default_shell"] = zsh_path
    save_state(state)
    SUMMARY.success(f"Zsh set as the default Termux shell: {zsh_path}")
    return True


def _remove_zsh_handoff_block(text: str) -> str:
    pattern = re.compile(
        re.escape(ZSH_HANDOFF_START) + r"[\s\S]*?" + re.escape(ZSH_HANDOFF_END) + r"\n?"
    )
    return pattern.sub("", text).lstrip("\n")


def _install_zsh_handoff_in_file(path: Path, zsh_path: str) -> bool:
    """Install an idempotent Bash/login-shell handoff without deleting unrelated content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    original = read_text(path)
    remainder = _remove_zsh_handoff_block(original)
    zsh_q = shlex.quote(zsh_path)
    block = "\n".join(
        [
            ZSH_HANDOFF_START,
            "# Force every interactive Bash-backed Termux terminal into Zsh.",
            "# POSIX-compatible guard so this is safe even when placed in /etc/profile.",
            'if [ -n "${BASH_VERSION:-}" ] && [ -t 0 ] && [ -t 1 ] && [ -z "${ZSH_VERSION:-}" ] && [ -z "${MOBILE_DEV_ZSH_HANDOFF:-}" ]; then',
            "  export MOBILE_DEV_ZSH_HANDOFF=1",
            f"  if [ -x {zsh_q} ]; then",
            f"    exec {zsh_q} -il",
            "  fi",
            "fi",
            ZSH_HANDOFF_END,
            "",
        ]
    )
    new_text = block + remainder
    mode_bits = path.stat().st_mode & 0o777 if path.exists() else 0o644

    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".handoff.", dir=str(path.parent))
    os.close(fd)
    temp = Path(temp_name)
    try:
        atomic_write_text(temp, new_text, mode=mode_bits)
        if shutil.which("bash"):
            check = run_cmd(["bash", "-n", str(temp)], capture=True, check=False)
            if check.returncode != 0:
                SUMMARY.failure(f"Zsh startup handoff failed Bash syntax validation for {path}")
                if check.stderr:
                    print(check.stderr.rstrip())
                return False
        atomic_write_text(path, new_text, mode=mode_bits)
        return True
    finally:
        temp.unlink(missing_ok=True)


def install_zsh_startup_handoff() -> bool:
    """Force Zsh on current and future Termux terminals even if chsh is ignored."""
    zsh_path = shutil.which("zsh")
    if not zsh_path:
        SUMMARY.failure("Persistent Zsh startup handoff could not be installed because zsh is unavailable")
        return False

    targets = (GLOBAL_BASHRC, GLOBAL_PROFILE, HOME / ".bashrc")
    ok = True
    for target in targets:
        ok = _install_zsh_handoff_in_file(target, zsh_path) and ok

    if ok:
        state = load_state()
        state["zsh_startup_handoff"] = True
        save_state(state)
        SUMMARY.success("Persistent Bash/login → Zsh handoff installed for every Termux terminal start")
    return ok


def remove_zsh_startup_handoff() -> None:
    removed = False
    for path in (GLOBAL_BASHRC, GLOBAL_PROFILE, HOME / ".bashrc"):
        if not path.exists():
            continue
        original = read_text(path)
        cleaned = _remove_zsh_handoff_block(original)
        if cleaned == original:
            continue
        mode_bits = path.stat().st_mode & 0o777
        atomic_write_text(path, cleaned, mode=mode_bits)
        removed = True
    if removed:
        SUMMARY.success("Removed persistent Bash/login → Zsh startup handoff")

def activate_zsh_now() -> bool:
    """Force the current setup process to become an interactive login Zsh."""
    zsh_path = shutil.which("zsh")
    if not zsh_path:
        SUMMARY.warning("Zsh could not be activated in the current session because it is unavailable")
        return False

    zshrc = HOME / ".zshrc"
    if not zshrc.is_file():
        SUMMARY.warning("Zsh could not be activated because ~/.zshrc is missing")
        return False

    syntax = run_cmd([zsh_path, "-n", str(zshrc)], capture=True, check=False)
    if syntax.returncode != 0:
        SUMMARY.failure("Current-session Zsh activation was blocked because ~/.zshrc failed validation")
        if syntax.stderr:
            print(syntax.stderr.rstrip())
        return False

    if NON_INTERACTIVE:
        SUMMARY.success("Zsh is ready and will be used for the next interactive Termux session")
        return False

    print(c("\nSwitching this Termux session to Zsh now...", C.INFO), flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    env = os.environ.copy()
    env["SHELL"] = zsh_path
    env["MOBILE_DEV_ZSH_HANDOFF"] = "1"
    try:
        # -i guarantees an interactive prompt; -l makes this a login Zsh.
        os.execve(zsh_path, [zsh_path, "-il"], env)
    except OSError as exc:
        SUMMARY.failure(f"Could not switch the current session to Zsh: {exc}")
        print(c("Run this manually: exec zsh", C.WARN))
        return False


# -----------------------------------------------------------------------------
# Termux UI
# -----------------------------------------------------------------------------


def replace_or_add_property(text: str, key: str, value: str) -> str:
    lines = text.splitlines()
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    replaced = False
    output = []
    for line in lines:
        if pattern.match(line):
            if not replaced:
                output.append(value)
                replaced = True
            continue
        output.append(line)
    if not replaced:
        output.append(value)
    return "\n".join(output).rstrip() + "\n"


def valid_font_file(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            data = f.read(4)
    except OSError:
        return False
    return data in {b"\x00\x01\x00\x00", b"OTTO", b"true", b"ttcf"}


def download_font(urls: Iterable[str] = DEFAULT_FONT_ARCHIVE_URLS) -> bool:
    """Download Meslo Nerd Font from official release assets with an archive fallback."""
    TERMUX_DIR.mkdir(parents=True, exist_ok=True)
    ensure_dirs()
    target = TERMUX_DIR / "font.ttf"
    temp_font = target.with_suffix(".ttf.download")
    temp_font.unlink(missing_ok=True)

    preferred_names = (
        "MesloLGSNerdFont-Regular.ttf",
        "MesloLGSNerdFontMono-Regular.ttf",
        "MesloLGSNerdFontPropo-Regular.ttf",
    )

    for index, url in enumerate(urls):
        suffix = ".zip" if url.lower().endswith(".zip") else ".tar.xz"
        archive = APP_DIR / f"Meslo-Nerd-Font-{index}{suffix}.download"
        archive.unlink(missing_ok=True)
        result = run_cmd([
            "curl", "-fL", "--retry", "3", "--retry-all-errors", "--retry-delay", "2",
            "--connect-timeout", "20", url, "-o", str(archive)
        ], check=False)
        if result.returncode != 0 or not archive.exists() or archive.stat().st_size < 10_000:
            archive.unlink(missing_ok=True)
            continue

        try:
            if url.lower().endswith(".zip"):
                with zipfile.ZipFile(archive, "r") as zf:
                    names = [n for n in zf.namelist() if n.lower().endswith(".ttf") and not n.endswith("/")]
                    if not names:
                        raise RuntimeError("Meslo archive contains no TTF files")
                    chosen = None
                    for preferred in preferred_names:
                        chosen = next((n for n in names if Path(n).name == preferred), None)
                        if chosen:
                            break
                    if chosen is None:
                        chosen = next((n for n in names if "regular" in Path(n).stem.lower()), names[0])
                    with zf.open(chosen, "r") as source, temp_font.open("wb") as out:
                        shutil.copyfileobj(source, out)
            else:
                with tarfile.open(archive, "r:*") as tf:
                    members = [m for m in tf.getmembers() if m.isfile() and m.name.lower().endswith(".ttf")]
                    if not members:
                        raise RuntimeError("Meslo archive contains no TTF files")
                    chosen = None
                    for preferred in preferred_names:
                        chosen = next((m for m in members if Path(m.name).name == preferred), None)
                        if chosen is not None:
                            break
                    if chosen is None:
                        chosen = next((m for m in members if "regular" in Path(m.name).stem.lower()), members[0])
                    source = tf.extractfile(chosen)
                    if source is None:
                        raise RuntimeError("Could not read selected font")
                    with source, temp_font.open("wb") as out:
                        shutil.copyfileobj(source, out)
        except (OSError, tarfile.TarError, zipfile.BadZipFile, RuntimeError):
            temp_font.unlink(missing_ok=True)
            archive.unlink(missing_ok=True)
            continue
        finally:
            archive.unlink(missing_ok=True)

        if temp_font.exists() and temp_font.stat().st_size >= 10_000 and valid_font_file(temp_font):
            temp_font.replace(target)
            SUMMARY.success("Meslo Nerd Font installed for Termux")
            return True
        temp_font.unlink(missing_ok=True)

    SUMMARY.warning("Nerd Font could not be downloaded from the official release assets; existing Termux font was kept")
    return False


def reload_termux_settings() -> None:
    if shutil.which("termux-reload-settings"):
        run_cmd(["termux-reload-settings"], capture=True, check=False)


def configure_termux_ui() -> None:
    header("Termux UI settings")
    TERMUX_DIR.mkdir(parents=True, exist_ok=True)

    props_path = TERMUX_DIR / "termux.properties"
    props = read_text(props_path)
    props = replace_or_add_property(props, "terminal-cursor-blink-rate", "terminal-cursor-blink-rate=500")
    extra_keys = (
        "extra-keys = [['ESC','</>','-','HOME',{key: 'UP', display: '▲'},'END','PGUP'], "
        "['TAB','CTRL','ALT',{key: 'LEFT', display: '◀'},{key: 'DOWN', display: '▼'},"
        "{key: 'RIGHT', display: '▶'},'PGDN']]"
    )
    props = replace_or_add_property(props, "extra-keys", extra_keys)
    atomic_write_text(props_path, props)
    SUMMARY.success("Termux extra keys and cursor blink configured")

    colors_path = TERMUX_DIR / "colors.properties"
    colors = replace_or_add_property(read_text(colors_path), "cursor", "cursor=#00FF00")
    atomic_write_text(colors_path, colors)
    SUMMARY.success("Termux cursor color configured")

    if shutil.which("curl"):
        download_font()
    else:
        SUMMARY.warning("Font installation skipped because curl is unavailable")

    reload_termux_settings()
    safe_notify("Mobile Developer Setup: Termux UI updated")


# -----------------------------------------------------------------------------
# NvChad
# -----------------------------------------------------------------------------


def backup_existing_nvim() -> Optional[Path]:
    existing = [p for p in (NVIM_CONFIG_DIR, NVIM_DATA_DIR, NVIM_STATE_DIR) if p.exists()]
    if not existing:
        return None

    out = NVI_BACKUPS_DIR / now_stamp()
    out.mkdir(parents=True, exist_ok=False)
    for src in existing:
        rel = src.relative_to(HOME)
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dest, symlinks=True)
        else:
            shutil.copy2(src, dest)
    SUMMARY.success(f"Existing Neovim files backed up to {out}")
    return out


def install_nvchad() -> None:
    header("NvChad")
    if not shutil.which("git") or not shutil.which("nvim"):
        SUMMARY.warning("NvChad skipped because git or neovim is unavailable")
        return

    if NVIM_CONFIG_DIR.exists() and git_repo(NVIM_CONFIG_DIR):
        remote = run_cmd(
            ["git", "-C", str(NVIM_CONFIG_DIR), "remote", "get-url", "origin"],
            capture=True,
            check=False,
        )
        if remote.returncode == 0 and "NvChad/starter" in (remote.stdout or ""):
            SUMMARY.success("NvChad starter configuration already present")
            return

    existing_nvim = any(p.exists() for p in (NVIM_CONFIG_DIR, NVIM_DATA_DIR, NVIM_STATE_DIR))
    if existing_nvim:
        if not ask_yes_no("Existing Neovim files found. Back them up and replace them with NvChad?", default=False):
            SUMMARY.warning("NvChad installation skipped to preserve existing Neovim files")
            return

    backup_existing_nvim()
    for p in (NVIM_CONFIG_DIR, NVIM_DATA_DIR, NVIM_STATE_DIR):
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()

    NVIM_CONFIG_DIR.parent.mkdir(parents=True, exist_ok=True)
    result = run_cmd(["git", "clone", "--depth=1", NVCHAD_STARTER_REPO, str(NVIM_CONFIG_DIR)], check=False)
    if result.returncode == 0:
        mark_managed_path(NVIM_CONFIG_DIR)
        SUMMARY.success("Installed official NvChad starter configuration")
        print(c("Open nvim once to let lazy.nvim fetch plugins, then run :MasonInstallAll if desired.", C.INFO))
    else:
        shutil.rmtree(NVIM_CONFIG_DIR, ignore_errors=True)
        SUMMARY.warning("NvChad starter clone failed; your backup remains available under ~/.mobile-dev-setup/nvim-backups")


def update_nvchad() -> None:
    if not NVIM_CONFIG_DIR.exists() or not git_repo(NVIM_CONFIG_DIR):
        SUMMARY.warning("NvChad configuration is not a Git checkout; update skipped")
        return
    remote = run_cmd(["git", "-C", str(NVIM_CONFIG_DIR), "remote", "get-url", "origin"], capture=True, check=False)
    if remote.returncode != 0 or "NvChad/starter" not in (remote.stdout or ""):
        SUMMARY.warning("Existing Neovim config is not NvChad/starter; update skipped")
        return
    result = run_cmd(["git", "-C", str(NVIM_CONFIG_DIR), "pull", "--ff-only"], check=False)
    if result.returncode == 0:
        SUMMARY.success("NvChad starter updated")
    else:
        SUMMARY.warning("NvChad starter could not be fast-forward updated")


# -----------------------------------------------------------------------------
# High-level workflows
# -----------------------------------------------------------------------------


def reset_log() -> None:
    ensure_dirs()
    atomic_write_text(LOG_FILE, f"Mobile Developer Setup run: {time.ctime()}\n")


def install_setup(
    *,
    upgrade: bool = True,
    configure_zsh: bool = True,
    configure_ui: bool = True,
    install_nvim: bool = True,
) -> None:
    SUMMARY.clear()
    if not require_termux():
        return
    reset_log()
    header("Mobile Developer Setup — Install")
    backup_path = make_backup()
    state = load_state()
    state["install_backup"] = str(backup_path)
    save_state(state)

    if not pkg_refresh(upgrade=upgrade):
        SUMMARY.show()
        return

    termux_ok = install_packages()
    python_tools_ok = install_python_developer_tools(update=False)
    if not (termux_ok and python_tools_ok):
        SUMMARY.failure("Full developer environment installation is incomplete. Fix the errors above and run Repair.")

    install_npm_tools(update=False)
    patch_localtunnel_android_openurl()

    if configure_zsh:
        clean_dedsec_bash_environment()
        install_oh_my_zsh(update=False)
        install_zsh_plugins(update=False)
        if shutil.which("zsh"):
            personalization_ok = ensure_first_run_shell_personalization()
            configure_zshrc()
            set_default_zsh()
            install_zsh_startup_handoff()
            if not personalization_ok:
                SUMMARY.warning("First-time Zsh personalization is still incomplete; finish Powerlevel10k setup with menu option 9.")

    if configure_ui:
        configure_termux_ui()

    if install_nvim:
        install_nvchad()

    state = load_state()
    state["last_install"] = now_stamp()
    save_state(state)
    safe_notify("Mobile Developer Setup completed")
    SUMMARY.show()
    if configure_zsh and shutil.which("zsh"):
        activate_zsh_now()

def run_update(
    *,
    upgrade: bool = True,
    configure_zsh: bool = True,
    configure_ui: bool = True,
    update_nvim: bool = True,
) -> None:
    SUMMARY.clear()
    if not require_termux():
        return
    reset_log()
    header("Mobile Developer Setup — Update")
    make_backup()
    pkg_refresh(upgrade=upgrade)
    install_packages(force=False)
    install_python_developer_tools(update=True)
    install_npm_tools(update=True)
    patch_localtunnel_android_openurl()
    if configure_zsh:
        clean_dedsec_bash_environment()
        install_oh_my_zsh(update=True)
        install_zsh_plugins(update=True)
        if shutil.which("zsh"):
            adopt_existing_powerlevel10k_config(announce=False)
            configure_zshrc()
            set_default_zsh()
            install_zsh_startup_handoff()
    if update_nvim:
        update_nvchad()
    if configure_ui:
        configure_termux_ui()
    state = load_state()
    state["last_update"] = now_stamp()
    save_state(state)
    SUMMARY.show()
    if configure_zsh and shutil.which("zsh"):
        activate_zsh_now()

def repair_setup(
    *,
    configure_zsh: bool = True,
    configure_ui: bool = True,
    install_nvim: bool = True,
) -> None:
    SUMMARY.clear()
    if not require_termux():
        return
    reset_log()
    header("Mobile Developer Setup — Repair")
    make_backup()
    run_cmd(["pkg", "update", "-y"], check=False)
    install_packages(force=False)
    install_python_developer_tools(update=False)
    install_npm_tools(update=False)
    patch_localtunnel_android_openurl()
    if configure_zsh:
        clean_dedsec_bash_environment()
        install_oh_my_zsh(update=False)
        install_zsh_plugins(update=False)
        if shutil.which("zsh"):
            personalization_ok = ensure_first_run_shell_personalization()
            configure_zshrc()
            set_default_zsh()
            install_zsh_startup_handoff()
            if not personalization_ok:
                SUMMARY.warning("Zsh personalization is still incomplete; use menu option 9 to finish Powerlevel10k setup.")
    if configure_ui:
        configure_termux_ui()
    if install_nvim:
        install_nvchad()
    SUMMARY.show()
    if configure_zsh and shutil.which("zsh"):
        activate_zsh_now()

def remove_managed_zsh_block() -> None:
    zshrc = HOME / ".zshrc"
    if not zshrc.exists():
        return
    text = read_text(zshrc)
    if MARK_BEGIN not in text or MARK_END not in text:
        return
    pattern = re.compile(re.escape(MARK_BEGIN) + r"[\s\S]*?" + re.escape(MARK_END) + r"\n?")
    new_text = pattern.sub("", text, count=1).rstrip() + "\n"
    atomic_write_text(zshrc, new_text)
    SUMMARY.success("Removed managed section from ~/.zshrc")


def uninstall_files_only(*, reset_summary: bool = True) -> None:
    if reset_summary:
        SUMMARY.clear()
    if not require_termux():
        return
    header("Removing setup-managed files")
    state = load_state()
    managed = [Path(p) for p in state.get("managed_paths", []) if isinstance(p, str)]

    # Remove the managed zsh block regardless of who owns ~/.zshrc.
    remove_managed_zsh_block()
    remove_zsh_startup_handoff()

    # Delete only paths explicitly recorded as created by this script.
    for path in sorted(managed, key=lambda p: len(str(p)), reverse=True):
        try:
            path.relative_to(HOME)
        except ValueError:
            SUMMARY.warning(f"Skipped unsafe managed path outside HOME: {path}")
            continue
        if not path.exists():
            continue
        try:
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
            SUMMARY.success(f"Removed {path}")
        except OSError as exc:
            SUMMARY.warning(f"Could not remove {path}: {exc}")

    # TOOLS_DIR currently only contains setup-owned material.
    if TOOLS_DIR.exists():
        shutil.rmtree(TOOLS_DIR, ignore_errors=True)
        SUMMARY.success(f"Removed {TOOLS_DIR}")

    state["managed_paths"] = []
    save_state(state)
    SUMMARY.show()
    print(c("Installed apt/npm packages were intentionally kept.", C.INFO))


def restore_and_remove() -> None:
    SUMMARY.clear()
    if not require_termux():
        return
    backup = choose_backup_interactive()
    if backup is None:
        return
    if not ask_yes_no(f"Restore {backup.name} and remove setup-managed files?", default=True):
        return
    restore_backup(backup)
    uninstall_files_only(reset_summary=False)
    print(c("Restart Termux to complete the restore.", C.INFO))


def backup_only() -> None:
    SUMMARY.clear()
    if not require_termux():
        return
    header("Backup Termux settings")
    make_backup()


def restore_latest() -> None:
    SUMMARY.clear()
    if not require_termux():
        return
    backups = list_backups()
    if not backups:
        print(c(f"No backups found in {BACKUPS_DIR}", C.WARN))
        return
    restore_backup(backups[0])
    SUMMARY.show()


def show_info() -> None:
    header("Mobile Developer Setup information")
    state = load_state()
    print("App directory:      ", APP_DIR)
    print("Backups:            ", BACKUPS_DIR)
    print("Run log:            ", LOG_FILE)
    print("Zsh plugins:        ", ZSH_PLUGINS_DIR)
    print("Oh My Zsh:          ", OH_MY_ZSH_DIR)
    print("Neovim config:      ", NVIM_CONFIG_DIR)
    print("NvChad backups:     ", NVI_BACKUPS_DIR)
    print("Termux detected:    ", "yes" if is_termux() else "no")
    print("Zsh prompt name:    ", get_prompt_name() or "(default)")
    print("Powerlevel10k:      ", "configured" if powerlevel10k_enabled() and powerlevel10k_config_exists() else "setup pending")
    print("Global bash.bashrc: ", GLOBAL_BASHRC)
    print("Managed paths:      ", len(state.get("managed_paths", [])))
    if state.get("install_backup"):
        print("Install backup:     ", state["install_backup"])
    if state.get("last_backup"):
        print("Last backup:        ", state["last_backup"])
    if state.get("last_install"):
        print("Last install stamp: ", state["last_install"])
    if state.get("last_update"):
        print("Last update stamp:  ", state["last_update"])


def menu() -> None:
    ensure_dirs()
    while True:
        header("Mobile Developer Setup")
        print("1) Install / Setup")
        print("2) Update installed tools")
        print("3) Repair missing/broken setup components")
        print("4) Backup Termux settings")
        print("5) Restore settings + remove setup-managed files")
        print("6) Remove setup-managed files only")
        print("7) Info")
        print("8) Set / change Zsh prompt name")
        print("9) Configure / reconfigure Powerlevel10k")
        print("0) Exit")
        choice = input(c("\nChoose a number: ", C.INFO)).strip()

        try:
            if choice == "1":
                install_setup()
            elif choice == "2":
                run_update()
            elif choice == "3":
                repair_setup()
            elif choice == "4":
                backup_only()
            elif choice == "5":
                restore_and_remove()
            elif choice == "6":
                uninstall_files_only()
            elif choice == "7":
                show_info()
            elif choice == "8":
                change_prompt_name_interactive()
            elif choice == "9":
                configure_powerlevel10k_interactive()
            elif choice == "0":
                print(c("Bye!", C.OK))
                return
            else:
                print(c("Invalid choice.", C.WARN))
                continue
        except KeyboardInterrupt:
            print("\n" + c("Cancelled.", C.WARN))
        except Exception as exc:
            SUMMARY.failure(str(exc))
            print(c(f"See the log at {LOG_FILE}", C.INFO))

        if not NON_INTERACTIVE:
            input(c("\nPress Enter to return to the menu…", C.DIM))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reliable Termux mobile developer environment setup.")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--install", action="store_true", help="Run full installation")
    action.add_argument("--update", action="store_true", help="Update packages, npm tools and managed Git checkouts")
    action.add_argument("--repair", action="store_true", help="Repair missing setup components")
    action.add_argument("--backup", action="store_true", help="Create a settings backup")
    action.add_argument("--restore-latest", action="store_true", help="Restore the newest settings backup")
    action.add_argument("--uninstall-files", action="store_true", help="Remove only files created/managed by this setup")
    action.add_argument("--info", action="store_true", help="Show setup paths and state")
    action.add_argument("--prompt-name", metavar="NAME", help="Set or change the persistent Zsh prompt name")
    action.add_argument("--powerlevel10k", action="store_true", help="Configure or reconfigure Powerlevel10k")

    parser.add_argument("-y", "--yes", action="store_true", help="Assume yes for confirmation prompts")
    parser.add_argument("--non-interactive", action="store_true", help="Do not prompt for input")
    parser.add_argument("--no-upgrade", action="store_true", help="Do not run pkg upgrade")
    parser.add_argument("--skip-zsh", action="store_true", help="Do not replace the shell environment or install/configure Zsh")
    parser.add_argument("--skip-ui", action="store_true", help="Do not change Termux keys/colors/font")
    parser.add_argument("--skip-nvchad", action="store_true", help="Do not install NvChad")
    return parser


def main() -> None:
    global ASSUME_YES, NON_INTERACTIVE
    parser = build_parser()
    args = parser.parse_args()
    ASSUME_YES = args.yes
    NON_INTERACTIVE = args.non_interactive

    if args.install:
        install_setup(
            upgrade=not args.no_upgrade,
            configure_zsh=not args.skip_zsh,
            configure_ui=not args.skip_ui,
            install_nvim=not args.skip_nvchad,
        )
    elif args.update:
        run_update(upgrade=not args.no_upgrade, configure_zsh=not args.skip_zsh, configure_ui=not args.skip_ui, update_nvim=not args.skip_nvchad)
    elif args.repair:
        repair_setup(configure_zsh=not args.skip_zsh, configure_ui=not args.skip_ui, install_nvim=not args.skip_nvchad)
    elif args.backup:
        backup_only()
    elif args.restore_latest:
        restore_latest()
    elif args.uninstall_files:
        uninstall_files_only()
    elif args.info:
        show_info()
    elif args.prompt_name is not None:
        SUMMARY.clear()
        if require_termux():
            make_backup()
            set_prompt_name(args.prompt_name, activate=True)
    elif args.powerlevel10k:
        configure_powerlevel10k_interactive()
    else:
        menu()


if __name__ == "__main__":
    main()
