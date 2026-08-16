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

MARK_BEGIN = "# >>> MOBILE DEV SETUP (managed) >>>"
MARK_END = "# <<< MOBILE DEV SETUP (managed) <<<"

DEFAULT_FONT_URL = (
    "https://raw.githubusercontent.com/ryanoasis/nerd-fonts/master/"
    "patched-fonts/Meslo/L/Regular/MesloLGSNerdFont-Regular.ttf"
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
    TermuxPackage("python", True),
    TermuxPackage("curl", True),
    TermuxPackage("wget", True),
    TermuxPackage("jq", True),
    TermuxPackage("ripgrep", True),
    TermuxPackage("fzf", True),
    TermuxPackage("bat", True),
    TermuxPackage("clang", True),
    TermuxPackage("make", True),
    TermuxPackage("unzip", True),
]

OPTIONAL_PACKAGES = [
    TermuxPackage("gh"),
    TermuxPackage("perl"),
    TermuxPackage("php"),
    TermuxPackage("lua-language-server"),
    TermuxPackage("lsd"),
    TermuxPackage("proot"),
    TermuxPackage("ncurses-utils"),
    TermuxPackage("stylua"),
    TermuxPackage("tmate"),
    TermuxPackage("cloudflared"),
    TermuxPackage("translate-shell"),
    TermuxPackage("html2text"),
    TermuxPackage("postgresql"),
    TermuxPackage("mariadb"),
    TermuxPackage("sqlite"),
    TermuxPackage("bc"),
    TermuxPackage("tree"),
    TermuxPackage("imagemagick"),
    TermuxPackage("shfmt"),
    TermuxPackage("cmake"),
    TermuxPackage("pkg-config"),
    TermuxPackage("openssh"),
    TermuxPackage("rsync"),
    TermuxPackage("tur-repo", note="Repository package used for TUR packages such as mongodb."),
]

TUR_PACKAGES = [
    TermuxPackage("mongodb", note="Optional Termux User Repository package."),
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


def make_backup() -> Path:
    ensure_dirs()
    stamp = now_stamp()
    out = BACKUPS_DIR / f"termux-settings-backup-{stamp}.tar.gz"
    manifest = {
        "created": stamp,
        "home": str(HOME),
        "targets": [],
        "note": "Termux settings/config backup created before Mobile Developer Setup changes.",
    }

    with tarfile.open(out, "w:gz") as tf:
        for target in BACKUP_TARGETS:
            existed = target.exists() and target.is_file()
            item = {"path": str(target), "existed": existed}
            if existed:
                item["mode"] = target.stat().st_mode & 0o777
                rel = target.relative_to(HOME)
                arcname = f"files/{rel.as_posix()}"
                item["archive_name"] = arcname
                item["sha256"] = sha256_file(target)
                tf.add(str(target), arcname=arcname, recursive=False)
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

            # Only restore files under the current HOME to avoid arbitrary writes.
            try:
                target.relative_to(HOME)
            except ValueError:
                SUMMARY.warning(f"Skipped unsafe backup path: {target}")
                continue

            if not item.get("existed", False):
                if target.exists() and target.is_file():
                    target.unlink()
                    SUMMARY.success(f"Removed file that did not exist at backup time: {target}")
                continue

            archive_name = item.get("archive_name")
            if not isinstance(archive_name, str) or not archive_name.startswith("files/"):
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


def install_packages(*, include_optional: bool = True, force: bool = False) -> bool:
    header("Installing core Termux packages")
    core_ok = True
    for package in CORE_PACKAGES:
        core_ok = install_one_pkg(package, force=force) and core_ok

    if include_optional:
        header("Installing optional Termux packages")
        for package in OPTIONAL_PACKAGES:
            install_one_pkg(package, force=force)

        # TUR packages must be attempted only after tur-repo has been installed.
        if dpkg_installed("tur-repo"):
            header("Installing optional Termux User Repository packages")
            # Refresh once because installing tur-repo adds a repository.
            run_cmd(["pkg", "update", "-y"], check=False)
            for package in TUR_PACKAGES:
                install_one_pkg(package, force=force)
        else:
            SUMMARY.warning("tur-repo is unavailable, so mongodb was skipped")

    return core_ok


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


def install_npm_tools(*, update: bool = False) -> None:
    header("Installing global npm developer tools")
    if not shutil.which("npm"):
        SUMMARY.warning("npm is unavailable; npm developer tools were skipped")
        return

    # Avoid npm audit/fund network chatter for global utility installs.
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
    prefix = os.environ.get("PREFIX", "")
    if not prefix:
        return
    target = Path(prefix) / "lib" / "node_modules" / "localtunnel" / "node_modules" / "openurl" / "openurl.js"
    if not target.exists():
        SUMMARY.warning("localtunnel Android open-url patch skipped (openurl.js layout not found)")
        return

    text = read_text(target)
    if "case 'android':" in text or 'case "android":' in text:
        SUMMARY.success("localtunnel Android open-url patch already present")
        return

    # Patch only when a known switch layout exists. Never blindly inject with sed.
    pattern = re.compile(r"(case ['\"]win32['\"]:[\s\S]*?\bbreak;)")
    match = pattern.search(text)
    if not match:
        SUMMARY.warning("localtunnel openurl.js changed upstream; safe Android patch was not applied")
        return

    insertion = (
        match.group(1)
        + "\n    case 'android':\n"
        + "        command = 'termux-open-url';\n"
        + "        break;"
    )
    patched = text[: match.start()] + insertion + text[match.end() :]
    atomic_write_text(target, patched)
    SUMMARY.success("Patched localtunnel to use termux-open-url on Android")


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


def configure_zshrc() -> None:
    header("Configuring ~/.zshrc")
    zshrc = HOME / ".zshrc"
    existing = read_text(zshrc)
    fpath_lines, source_lines = _zsh_plugin_lines()

    lines = [
        MARK_BEGIN,
        "# Managed by Mobile Developer Setup.py. Edit outside this block for custom settings.",
        "",
    ]
    lines.extend(fpath_lines)
    if fpath_lines:
        lines.append("")

    if (OH_MY_ZSH_DIR / "oh-my-zsh.sh").is_file():
        lines.extend(
            [
                'export ZSH="$HOME/.oh-my-zsh"',
                '[[ -z "${ZSH_THEME:-}" ]] && ZSH_THEME="robbyrussell"',
                '[[ -f "$ZSH/oh-my-zsh.sh" ]] && source "$ZSH/oh-my-zsh.sh"',
                "",
            ]
        )
    else:
        lines.extend(["autoload -Uz compinit", "compinit -d ~/.zcompdump", ""])

    lines.extend(source_lines)
    lines.extend(
        [
            "",
            "if (( $+functions[history-substring-search-up] )); then",
            "  bindkey '^[[A' history-substring-search-up",
            "  bindkey '^[[B' history-substring-search-down",
            "fi",
            "zstyle ':completion:*' menu-select yes",
            "zstyle ':fzf-tab:*' switch-word yes",
            "command -v lsd >/dev/null 2>&1 && alias ls='lsd'",
            "command -v bat >/dev/null 2>&1 && alias cat='bat --theme=Dracula --style=plain --paging=never'",
            MARK_END,
            "",
        ]
    )
    managed_block = "\n".join(lines)

    if MARK_BEGIN in existing and MARK_END in existing:
        pattern = re.compile(re.escape(MARK_BEGIN) + r"[\s\S]*?" + re.escape(MARK_END))
        new_text = pattern.sub(managed_block.strip(), existing, count=1).rstrip() + "\n"
    else:
        prefix = existing.rstrip()
        new_text = (prefix + "\n\n" if prefix else "") + managed_block

    atomic_write_text(zshrc, new_text)
    result = run_cmd(["zsh", "-n", str(zshrc)], capture=True, check=False)
    if result.returncode == 0:
        SUMMARY.success("~/.zshrc configured and syntax-checked")
    else:
        SUMMARY.failure("~/.zshrc failed zsh syntax validation; restore your backup if needed")
        if result.stderr:
            print(result.stderr.rstrip())


def maybe_set_default_zsh() -> None:
    if not shutil.which("zsh") or not shutil.which("chsh"):
        return
    current = os.environ.get("SHELL", "")
    zsh_path = shutil.which("zsh") or "zsh"
    if current.endswith("/zsh"):
        SUMMARY.success("Zsh is already the current login shell")
        return
    if ask_yes_no("Set Zsh as the default Termux login shell?", default=True):
        result = run_cmd(["chsh", "-s", zsh_path], check=False)
        if result.returncode == 0:
            SUMMARY.success("Zsh set as the default shell")
        else:
            SUMMARY.warning("Could not set Zsh as the default shell; you can still run: exec zsh")


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


def download_font(url: str = DEFAULT_FONT_URL) -> bool:
    TERMUX_DIR.mkdir(parents=True, exist_ok=True)
    target = TERMUX_DIR / "font.ttf"
    temp = target.with_suffix(".ttf.download")
    temp.unlink(missing_ok=True)
    result = run_cmd(
        ["curl", "-fL", "--retry", "3", "--retry-delay", "2", "--connect-timeout", "20", url, "-o", str(temp)],
        check=False,
    )
    if result.returncode != 0 or not temp.exists() or temp.stat().st_size < 10_000 or not valid_font_file(temp):
        temp.unlink(missing_ok=True)
        SUMMARY.warning("Nerd Font download failed or did not look like a valid font; existing font was kept")
        return False
    temp.replace(target)
    SUMMARY.success("Meslo Nerd Font installed for Termux")
    return True


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
    include_optional: bool = True,
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

    core_ok = install_packages(include_optional=include_optional)
    if not core_ok:
        SUMMARY.failure("Core package installation is incomplete. Fix the package errors above and run Repair.")

    install_npm_tools(update=False)
    patch_localtunnel_android_openurl()

    if configure_zsh:
        install_oh_my_zsh(update=False)
        install_zsh_plugins(update=False)
        if shutil.which("zsh"):
            configure_zshrc()
            maybe_set_default_zsh()

    if configure_ui:
        configure_termux_ui()

    if install_nvim:
        install_nvchad()

    state = load_state()
    state["last_install"] = now_stamp()
    save_state(state)
    safe_notify("Mobile Developer Setup completed")
    SUMMARY.show()
    print(c("\nRestart Termux, or run 'exec zsh' if you enabled Zsh.", C.INFO))


def run_update(*, include_optional: bool = True, upgrade: bool = True) -> None:
    SUMMARY.clear()
    if not require_termux():
        return
    reset_log()
    header("Mobile Developer Setup — Update")
    pkg_refresh(upgrade=upgrade)
    install_packages(include_optional=include_optional, force=False)
    install_npm_tools(update=True)
    patch_localtunnel_android_openurl()
    install_oh_my_zsh(update=True)
    install_zsh_plugins(update=True)
    if shutil.which("zsh"):
        configure_zshrc()
    update_nvchad()
    configure_termux_ui()
    state = load_state()
    state["last_update"] = now_stamp()
    save_state(state)
    SUMMARY.show()


def repair_setup(*, include_optional: bool = True) -> None:
    SUMMARY.clear()
    if not require_termux():
        return
    reset_log()
    header("Mobile Developer Setup — Repair")
    run_cmd(["pkg", "update", "-y"], check=False)
    install_packages(include_optional=include_optional, force=False)
    install_npm_tools(update=False)
    patch_localtunnel_android_openurl()
    install_oh_my_zsh(update=False)
    install_zsh_plugins(update=False)
    if shutil.which("zsh"):
        configure_zshrc()
    configure_termux_ui()
    SUMMARY.show()


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

    parser.add_argument("-y", "--yes", action="store_true", help="Assume yes for confirmation prompts")
    parser.add_argument("--non-interactive", action="store_true", help="Do not prompt for input")
    parser.add_argument("--skip-optional", action="store_true", help="Skip optional Termux packages")
    parser.add_argument("--no-upgrade", action="store_true", help="Do not run pkg upgrade")
    parser.add_argument("--skip-zsh", action="store_true", help="Do not install/configure Oh My Zsh or plugins")
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
            include_optional=not args.skip_optional,
            upgrade=not args.no_upgrade,
            configure_zsh=not args.skip_zsh,
            configure_ui=not args.skip_ui,
            install_nvim=not args.skip_nvchad,
        )
    elif args.update:
        run_update(include_optional=not args.skip_optional, upgrade=not args.no_upgrade)
    elif args.repair:
        repair_setup(include_optional=not args.skip_optional)
    elif args.backup:
        backup_only()
    elif args.restore_latest:
        restore_latest()
    elif args.uninstall_files:
        uninstall_files_only()
    elif args.info:
        show_info()
    else:
        menu()


if __name__ == "__main__":
    main()
