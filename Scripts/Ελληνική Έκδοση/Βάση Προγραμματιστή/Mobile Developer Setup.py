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
# Mobile Developer Setup για Termux
#
# Στόχοι σχεδιασμού:
# - Ασφαλής επανεκτέλεση (idempotent όπου είναι πρακτικά εφικτό)
# - Τα βασικά εργαλεία αποτυγχάνουν εμφανώς, ενώ τα προαιρετικά ανεξάρτητα
# - Δεν θεωρούμε ποτέ ότι αυτό το αυτόνομο .py αρχείο βρίσκεται μέσα σε Git repository
# - Διατηρούμε τις ρυθμίσεις του χρήστη με αντίγραφα ασφαλείας πριν από καταστροφικές αλλαγές
# - Καταγράφουμε τις διαδρομές που δημιουργεί το script ώστε η απεγκατάσταση να μη διαγράφει αρχεία του χρήστη
# - Χρησιμοποιούμε τρέχουσες εκδόσεις πακέτων αντί για παλιές σταθερά δεσμευμένες εκδόσεις npm
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


# Global ρύθμιση shell του Termux. Το DedSec Settings.py γράφει εδώ το δικό του
# περιβάλλον shell, ενώ αυτό το setup ορίζει το Zsh ως το κύριο περιβάλλον.
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
    TermuxPackage("tur-repo", True, note="Πακέτο repository που απαιτείται για πακέτα ανάπτυξης TUR όπως το mongodb."),
]

# Developer εργαλεία των οποίων η υποστηριζόμενη εγκατάσταση στο Termux γίνεται μέσω Python/pip.
# Παραμένουν έξω από τη φάση pkg ώστε η απουσία πακέτου από το Termux repository
# να μη χαρακτηρίζει λανθασμένα ολόκληρη την εγκατάσταση πακέτων ως αποτυχημένη.
PYTHON_DEVELOPER_TOOLS = [
    ("meson", "meson"),
    ("mercurial", "hg"),
]

TUR_PACKAGES = [
    TermuxPackage("mongodb", True, note="Πακέτο βάσης δεδομένων από το Termux User Repository."),
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

# όνομα, repository, γραμμή source/fpath του zsh
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


class GreekArgumentParser(argparse.ArgumentParser):
    """ArgumentParser με ελληνικές βασικές επικεφαλίδες/μηνύματα."""

    def format_usage(self) -> str:
        return super().format_usage().replace("usage:", "χρήση:", 1)

    def format_help(self) -> str:
        text = super().format_help()
        text = text.replace("usage:", "χρήση:", 1)
        text = text.replace("options:\n", "επιλογές:\n", 1)
        return text


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
        header("Σύνοψη εκτέλεσης")
        print(f"Επιτυχίες:    {len(self.ok)}")
        print(f"Προειδοποιήσεις: {len(self.warn)}")
        print(f"Αποτυχίες:     {len(self.failed)}")
        if self.warn:
            print(c("\nΠροειδοποιήσεις:", C.WARN))
            for item in self.warn:
                print(f"  - {item}")
        if self.failed:
            print(c("\nΑποτυχίες:", C.ERR))
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
    print(c("Αυτό το script πρέπει να εκτελεστεί μέσα στο Termux.", C.ERR))
    print("Εκτέλεσέ το με: python 'Mobile Developer Setup Fixed Greek.py'")
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
        raise RuntimeError(f"Η εντολή απέτυχε ({result.returncode}): {command_text}")
    return result


def run_shell(command: str, *, check: bool = False, capture: bool = False) -> subprocess.CompletedProcess:
    return run_cmd(["bash", "-lc", command], check=check, capture=capture)


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    if ASSUME_YES:
        return True
    if NON_INTERACTIVE:
        return default
    suffix = " [Ν/y] " if default else " [ν/Ο] "
    while True:
        answer = input(c(prompt + suffix, C.INFO)).strip().lower()
        if not answer:
            return default
        if answer in {"y", "yes", "ν", "ναι", "nai"}:
            return True
        if answer in {"n", "no", "ο", "όχι", "οχι", "oxi"}:
            return False
        print(c("Απάντησε y/n ή ν/ο.", C.WARN))


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
    # Περιλαμβάνουμε ακρίβεια μικρότερη του δευτερολέπτου ώστε πολλαπλά backups στο ίδιο δευτερόλεπτο να μη συγκρούονται.
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
# Αντίγραφα ασφαλείας / επαναφορά
# -----------------------------------------------------------------------------


def _backup_archive_name(target: Path) -> str:
    """Δημιουργεί ασφαλές path μέσα στο backup για αρχεία κάτω από HOME ή PREFIX."""
    for root, label in ((HOME, "home"), (PREFIX, "prefix")):
        try:
            rel = target.relative_to(root)
            return f"{label}/{rel.as_posix()}"
        except ValueError:
            continue
    raise ValueError(f"Μη υποστηριζόμενος στόχος backup: {target}")


def _safe_restore_target(target: Path) -> bool:
    """Επιτρέπει επαναφορά μόνο μέσα στα Termux HOME ή PREFIX."""
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
        "note": "Backup ρυθμίσεων/config του Termux πριν από αλλαγές του Mobile Developer Setup.",
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
    SUMMARY.success(f"Το backup αποθηκεύτηκε: {out}")
    return out


def list_backups() -> list[Path]:
    ensure_dirs()
    return sorted(BACKUPS_DIR.glob("termux-settings-backup-*.tar.gz"), reverse=True)


def _load_backup_manifest(tf: tarfile.TarFile) -> dict:
    member = tf.getmember("manifest.json")
    fileobj = tf.extractfile(member)
    if fileobj is None:
        raise RuntimeError("Το manifest του αντιγράφου ασφαλείας δεν μπορεί να διαβαστεί.")
    data = json.loads(fileobj.read().decode("utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("targets"), list):
        raise RuntimeError("Το manifest του αντιγράφου ασφαλείας δεν είναι έγκυρο.")
    return data


def restore_backup(backup_path: Path) -> None:
    if not backup_path.exists():
        raise FileNotFoundError(str(backup_path))

    header("Επαναφορά ρυθμίσεων Termux")
    with tarfile.open(backup_path, "r:gz") as tf:
        manifest = _load_backup_manifest(tf)
        for item in manifest["targets"]:
            target_raw = item.get("path")
            if not isinstance(target_raw, str):
                continue
            target = Path(target_raw)

            if not _safe_restore_target(target):
                SUMMARY.warning(f"Παραλείφθηκε μη ασφαλές path backup: {target}")
                continue

            if not item.get("existed", False):
                if target.exists() and target.is_file():
                    target.unlink()
                    SUMMARY.success(f"Αφαιρέθηκε αρχείο που δεν υπήρχε τη στιγμή του backup: {target}")
                continue

            archive_name = item.get("archive_name")
            if not isinstance(archive_name, str) or not archive_name.startswith(("home/", "prefix/", "files/")):
                SUMMARY.warning(f"Λείπει εγγραφή archive για {target}")
                continue

            try:
                member = tf.getmember(archive_name)
                source = tf.extractfile(member)
            except KeyError:
                source = None
            if source is None:
                SUMMARY.warning(f"Λείπουν δεδομένα backup για {target}")
                continue

            data = source.read()
            expected = item.get("sha256")
            if expected:
                actual = hashlib.sha256(data).hexdigest()
                if actual != expected:
                    raise RuntimeError(f"Απέτυχε ο έλεγχος ακεραιότητας backup για {target}")

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
            SUMMARY.success(f"Επαναφέρθηκε {target}")

    reload_termux_settings()

def choose_backup_interactive() -> Optional[Path]:
    backups = list_backups()
    if not backups:
        print(c(f"Δεν βρέθηκαν αντίγραφα ασφαλείας στο {BACKUPS_DIR}", C.WARN))
        return None
    if NON_INTERACTIVE:
        return backups[0]

    print(c("\nΔιαθέσιμα αντίγραφα ασφαλείας:", C.INFO))
    for idx, backup in enumerate(backups, 1):
        print(f"  {idx}) {backup.name}")
    while True:
        answer = input(c("Επίλεξε αριθμό αντιγράφου ασφαλείας (0 για ακύρωση): ", C.INFO)).strip()
        if answer == "0":
            return None
        if answer.isdigit() and 1 <= int(answer) <= len(backups):
            return backups[int(answer) - 1]
        print(c("Μη έγκυρη επιλογή.", C.WARN))


# -----------------------------------------------------------------------------
# Διαχείριση πακέτων Termux
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
    header("Ανανέωση repositories του Termux")
    update = run_cmd(["pkg", "update", "-y"], check=False)
    if update.returncode != 0:
        SUMMARY.failure("Το pkg update απέτυχε. Έλεγξε το mirror/δίκτυο του Termux και δοκίμασε ξανά.")
        return False
    SUMMARY.success("Οι λίστες πακέτων του Termux ανανεώθηκαν")

    if upgrade:
        result = run_cmd(["pkg", "upgrade", "-y"], check=False)
        if result.returncode == 0:
            SUMMARY.success("Τα εγκατεστημένα πακέτα του Termux αναβαθμίστηκαν")
        else:
            SUMMARY.warning("Το pkg upgrade ανέφερε σφάλμα· η εγκατάσταση θα συνεχίσει με ξεχωριστά πακέτα")
    return True


def install_one_pkg(package: TermuxPackage, *, force: bool = False) -> bool:
    if not force and dpkg_installed(package.name):
        SUMMARY.success(f"Το {package.name} είναι ήδη εγκατεστημένο")
        return True

    result = run_cmd(["pkg", "install", "-y", package.name], check=False)
    ok = result.returncode == 0 and dpkg_installed(package.name)
    if ok:
        SUMMARY.success(f"Εγκαταστάθηκε το {package.name}")
    elif package.required:
        SUMMARY.failure(f"Απέτυχε απαιτούμενο πακέτο Termux: {package.name}")
    else:
        suffix = f" ({package.note})" if package.note else ""
        SUMMARY.warning(f"Προαιρετικό πακέτο Termux παραλείφθηκε/απέτυχε: {package.name}{suffix}")
    return ok


def install_packages(*, force: bool = False) -> bool:
    header("Εγκατάσταση πλήρους πακέτου ανάπτυξης Termux")
    all_ok = True

    for package in CORE_PACKAGES:
        all_ok = install_one_pkg(package, force=force) and all_ok

    header("Εγκατάσταση πρόσθετων απαιτούμενων εργαλείων ανάπτυξης")
    for package in DEVELOPER_PACKAGES:
        all_ok = install_one_pkg(package, force=force) and all_ok

    # Το mongodb βρίσκεται στο TUR, οπότε ενεργοποιούμε πρώτα το tur-repo και
    # ανανεώνουμε τους καταλόγους πακέτων πριν από την εγκατάστασή του.
    if dpkg_installed("tur-repo"):
        header("Εγκατάσταση απαιτούμενων πακέτων Termux User Repository")
        refresh = run_cmd(["pkg", "update", "-y"], check=False)
        if refresh.returncode != 0:
            SUMMARY.failure("Απέτυχε η ανανέωση του TUR repository")
            all_ok = False
        for package in TUR_PACKAGES:
            all_ok = install_one_pkg(package, force=force) and all_ok
    else:
        SUMMARY.failure("Το tur-repo δεν εγκαταστάθηκε, επομένως το mongodb δεν μπορεί να εγκατασταθεί")
        all_ok = False

    return all_ok



# -----------------------------------------------------------------------------
# Python developer εργαλεία
# -----------------------------------------------------------------------------


def python_pip_available() -> bool:
    python_bin = shutil.which("python") or shutil.which("python3")
    if not python_bin:
        return False
    result = run_cmd([python_bin, "-m", "pip", "--version"], capture=True, check=False)
    return result.returncode == 0


def install_python_developer_tools(*, update: bool = False) -> bool:
    """Εγκαθιστά απαιτούμενα developer εργαλεία που διανέμονται σωστά μέσω PyPI."""
    header("Εγκατάσταση απαιτούμενων Python developer εργαλείων")
    python_bin = shutil.which("python") or shutil.which("python3")
    if not python_bin:
        SUMMARY.failure("Η Python δεν είναι διαθέσιμη, οπότε τα Python developer εργαλεία δεν μπορούν να εγκατασταθούν")
        return False
    if not python_pip_available():
        SUMMARY.failure("Το python-pip δεν είναι διαθέσιμο. Εκτελέστε Επιδιόρθωση αφού εγκατασταθεί το python-pip")
        return False

    all_ok = True
    for package, command in PYTHON_DEVELOPER_TOOLS:
        if not update and shutil.which(command):
            SUMMARY.success(f"Το {package} είναι ήδη εγκατεστημένο")
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
            action = "Ενημερώθηκε" if update else "Εγκαταστάθηκε"
            SUMMARY.success(f"{action} το Python developer εργαλείο {package}")
        else:
            SUMMARY.failure(f"Απέτυχε το απαιτούμενο Python developer εργαλείο: {package}")
            all_ok = False
    return all_ok

# -----------------------------------------------------------------------------
# Καθαρισμός παλιού περιβάλλοντος Bash του DedSec
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
    """Εντοπίζει το ορατό όνομα χρήστη από το PS1 του DedSec Settings.py, αν υπάρχει."""
    for line in text.splitlines():
        if not _looks_like_dedsec_ps1(line):
            continue
        match = re.search(r"1;34m\\\]([^\\'\n]+?)\\\[\\e\[0m", line)
        if match:
            return sanitize_prompt_name(match.group(1))
    return ""


def clean_dedsec_bash_environment() -> bool:
    """Αφαιρεί μόνο shell hooks που δημιουργεί το DedSec Settings.py.

    Το Settings.py δεν τροποποιείται και διατηρείται άσχετη ρύθμιση Bash.
    Το global bash.bashrc περιλαμβάνεται στο safety backup πριν εκτελεστεί.
    """
    header("Αφαίρεση παλιού περιβάλλοντος Bash του DedSec")
    if not GLOBAL_BASHRC.exists():
        SUMMARY.success("Δεν υπάρχει global bash.bashrc για καθαρισμό")
        return True

    original = read_text(GLOBAL_BASHRC)

    # Διατηρεί το υπάρχον όνομα prompt του DedSec πριν αφαιρεθεί το Bash PS1.
    if not get_prompt_name():
        migrated_prompt = extract_dedsec_prompt_name(original)
        if migrated_prompt:
            state = load_state()
            state["prompt_name"] = migrated_prompt
            save_state(state)
            SUMMARY.success(f"Μεταφέρθηκε το όνομα prompt του DedSec στο Zsh: {migrated_prompt}")

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
        SUMMARY.success("Δεν βρέθηκαν ενεργά shell overrides του DedSec στο bash.bashrc")
        return True

    temp = APP_DIR / "bash.bashrc.cleaned.tmp"
    mode_bits = GLOBAL_BASHRC.stat().st_mode & 0o777
    atomic_write_text(temp, cleaned, mode=mode_bits)
    if shutil.which("bash"):
        check = run_cmd(["bash", "-n", str(temp)], capture=True, check=False)
        if check.returncode != 0:
            temp.unlink(missing_ok=True)
            SUMMARY.failure("Ο καθαρισμός DedSec παρήγαγε μη έγκυρο bash.bashrc· το αρχικό αρχείο διατηρήθηκε")
            if check.stderr:
                print(check.stderr.rstrip())
            return False

    atomic_write_text(GLOBAL_BASHRC, cleaned, mode=mode_bits)
    temp.unlink(missing_ok=True)
    state = load_state()
    state["dedsec_bash_environment_overridden"] = True
    save_state(state)
    SUMMARY.success("Αφαιρέθηκαν το DedSec PS1, menu autostart, aliases και network hooks από το global bash.bashrc")
    return True


# -----------------------------------------------------------------------------
# Εργαλεία npm
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
    """Διασφαλίζει ότι το npm υπάρχει σε τρέχον Termux, όπου πλέον είναι ξεχωριστό πακέτο."""
    if shutil.which("npm"):
        return True
    if not is_termux():
        SUMMARY.failure("Το npm δεν είναι διαθέσιμο")
        return False

    # Το npm είναι πλέον ξεχωριστό επίσημο πακέτο Termux. Κάνουμε πρώτα refresh
    # και το εγκαθιστούμε μόνο του ώστε το apt να επιλέξει συμβατό nodejs/nodejs-lts.
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
            SUMMARY.success("Το npm εγκαταστάθηκε και είναι διαθέσιμο")
            return True

    # Τελευταία προσπάθεια: αναβάθμιση του εγκατεστημένου Node.js και νέα εγκατάσταση npm.
    node_package = "nodejs-lts" if dpkg_installed("nodejs-lts") else "nodejs"
    run_cmd(["pkg", "upgrade", "-y", node_package], check=False)
    result = run_cmd(["pkg", "install", "-y", "npm"], check=False)
    if result.returncode == 0 and shutil.which("npm"):
        SUMMARY.success("Το npm εγκαταστάθηκε μετά την αναβάθμιση του Node.js")
        return True

    SUMMARY.failure("Δεν ήταν δυνατή η εγκατάσταση του npm από τα ενεργά repositories του Termux")
    return False


def install_npm_tools(*, update: bool = False) -> None:
    header("Εγκατάσταση καθολικών εργαλείων ανάπτυξης npm")
    if not ensure_npm_available():
        return
    env = os.environ.copy()
    env["npm_config_audit"] = "false"
    env["npm_config_fund"] = "false"
    env["npm_config_update_notifier"] = "false"
    for tool in NPM_TOOLS:
        if not update and npm_package_installed(tool.package):
            SUMMARY.success(f"npm: το {tool.package} είναι ήδη εγκατεστημένο")
            continue
        spec = f"{tool.package}@latest"
        result = run_cmd(["npm", "install", "-g", spec], env=env, check=False)
        if result.returncode == 0:
            SUMMARY.success(f"npm: εγκαταστάθηκε το {spec}")
        elif tool.required:
            SUMMARY.failure(f"Απέτυχε απαιτούμενο εργαλείο npm: {tool.package}")
        else:
            SUMMARY.warning(f"Απέτυχε προαιρετικό εργαλείο npm: {tool.package}")

def patch_localtunnel_android_openurl() -> None:
    """Ρυθμίζει το localtunnel --open ώστε να ανοίγει URL σωστά στο Android/Termux."""
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
        SUMMARY.success("Η ενσωμάτωση browser του localtunnel για Android είναι ήδη ρυθμισμένη")
        return

    needle = "openurl.open(tunnel.url);"
    if needle not in text:
        # Το localtunnel είναι προαιρετικό. Αν αλλάξει ξανά upstream, δεν εμφανίζουμε
        # ψευδή προειδοποίηση για κάτι που δεν εμποδίζει το βασικό setup.
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
    SUMMARY.success("Το localtunnel --open ρυθμίστηκε για Android/Termux")


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
                    SUMMARY.success(f"Ενημερώθηκε: {name}")
                    return True
                SUMMARY.warning(f"Δεν ήταν δυνατή η ενημέρωση του {name}· διατηρήθηκε το υπάρχον checkout")
                return True
            SUMMARY.success(f"Το {name} υπάρχει ήδη")
            return True
        SUMMARY.warning(f"Η διαδρομή του {name} υπάρχει αλλά δεν είναι Git checkout· έμεινε ανέπαφη: {dest}")
        return False

    result = run_cmd(["git", "clone", "--depth=1", repo, str(dest)], check=False)
    if result.returncode == 0:
        mark_managed_path(dest)
        SUMMARY.success(f"Εγκαταστάθηκε: {name}")
        return True
    shutil.rmtree(dest, ignore_errors=True)
    SUMMARY.warning(f"Δεν ήταν δυνατή η εγκατάσταση του {name}")
    return False


def install_oh_my_zsh(*, update: bool = False) -> None:
    header("Oh My Zsh")
    if not shutil.which("zsh") or not shutil.which("git"):
        SUMMARY.warning("Το Oh My Zsh παραλείφθηκε επειδή το zsh ή το git δεν είναι διαθέσιμο")
        return
    clone_or_update_repo("Oh My Zsh", OH_MY_ZSH_REPO, OH_MY_ZSH_DIR, update=update)


def install_zsh_plugins(*, update: bool = False) -> None:
    header("Zsh plugins")
    if not shutil.which("git"):
        SUMMARY.warning("Τα plugins του Zsh παραλείφθηκαν επειδή το git δεν είναι διαθέσιμο")
        return
    ZSH_PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    for name, repo, _ in ZSH_PLUGIN_REPOS:
        clone_or_update_repo(name, repo, ZSH_PLUGINS_DIR / name, update=update)


def _zsh_plugin_lines() -> tuple[list[str], list[str]]:
    fpath_lines: list[str] = []
    source_lines: list[str] = []
    for name, _, line in ZSH_PLUGIN_REPOS:
        # Το Powerlevel10k εγκαθίσταται αλλά δεν ξεκινά αυτόματα.
        # Το wizard και το prompt του ενεργοποιούνται μόνο από τη σχετική επιλογή μενού.
        if name == "powerlevel10k":
            continue
        dest = ZSH_PLUGINS_DIR / name
        if not dest.exists():
            continue
        if line.startswith("fpath"):
            if (dest / "src").is_dir():
                fpath_lines.append(line)
            else:
                SUMMARY.warning(f"Παραλείφθηκε ελλιπές plugin του Zsh: {name}")
            continue

        match = re.match(r"source\s+(.+)$", line)
        if not match:
            continue
        source_path = Path(os.path.expanduser(match.group(1)))
        if source_path.is_file():
            source_lines.append(line)
        else:
            SUMMARY.warning(f"Παραλείφθηκε ελλιπές plugin του Zsh: {name}")
    return fpath_lines, source_lines


def sanitize_prompt_name(name: str) -> str:
    """Καθαρίζει το μόνιμο όνομα prompt ώστε να είναι ασφαλές για το Zsh."""
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
    """Χρησιμοποιεί υπάρχον ~/.p10k.zsh χωρίς να ζητά ξανά ρύθμιση από τον χρήστη."""
    if not powerlevel10k_config_exists():
        return False
    _save_powerlevel10k_state(True, personalization_complete=bool(get_prompt_name()))
    if announce:
        SUMMARY.success("Βρέθηκε υπάρχουσα ρύθμιση Powerlevel10k και χρησιμοποιήθηκε ξανά")
    return True


def _powerlevel10k_zsh_lines() -> list[str]:
    """Κάνει source το Powerlevel10k μόνο όταν έχει ρυθμιστεί ή ενεργοποιηθεί ρητά."""
    if not powerlevel10k_enabled():
        return []
    theme = ZSH_PLUGINS_DIR / "powerlevel10k" / "powerlevel10k.zsh-theme"
    if not theme.is_file():
        SUMMARY.warning("Το Powerlevel10k είναι ενεργό αλλά λείπει το αρχείο theme")
        return []
    return [
        "typeset -g POWERLEVEL9K_DISABLE_CONFIGURATION_WIZARD=true",
        "source ~/.zsh-plugins/powerlevel10k/powerlevel10k.zsh-theme",
        "[[ -f ~/.p10k.zsh ]] && source ~/.p10k.zsh",
    ]


def _powerlevel10k_prompt_name_lines() -> list[str]:
    """Προσθέτει το αποθηκευμένο όνομα prompt ως custom segment του Powerlevel10k."""
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
    """Επιστρέφει το fallback DedSec-style prompt όταν το Powerlevel10k δεν είναι ενεργό."""
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
    """Αντικαθιστά πλήρως το ~/.zshrc με το περιβάλλον που διαχειρίζεται αυτό το setup."""
    header("Πλήρης ρύθμιση ~/.zshrc")
    zshrc = HOME / ".zshrc"
    fpath_lines, source_lines = _zsh_plugin_lines()

    lines = [
        MARK_BEGIN,
        "# Το Mobile Developer Setup διαχειρίζεται αποκλειστικά αυτό το ~/.zshrc όσο είναι εγκατεστημένο.",
        "# Τα Bash startup files δεν γίνονται source από το Zsh.",
        'export SHELL="$(command -v zsh)"',
        'unset PROMPT_COMMAND 2>/dev/null || true',
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
        SUMMARY.success("Το ~/.zshrc αντικαταστάθηκε πλήρως και πέρασε έλεγχο σύνταξης")
    else:
        SUMMARY.failure("Το νέο ~/.zshrc απέτυχε στον έλεγχο σύνταξης zsh· χρησιμοποιήστε το safety backup για επαναφορά")
        if result.stderr:
            print(result.stderr.rstrip())


def set_prompt_name(name: str, *, activate: bool = False) -> bool:
    """Αποθηκεύει το όνομα prompt χωρίς να απενεργοποιεί υπάρχουσα ρύθμιση Powerlevel10k."""
    clean = sanitize_prompt_name(name)
    state = load_state()
    state["prompt_name"] = clean
    state["shell_personalization_complete"] = bool(clean and powerlevel10k_config_exists())
    save_state(state)

    if not shutil.which("zsh"):
        SUMMARY.warning("Το όνομα prompt αποθηκεύτηκε, αλλά το Zsh δεν είναι ακόμη εγκατεστημένο")
        return False

    configure_zshrc()
    if clean:
        SUMMARY.success(f"Το όνομα prompt ορίστηκε σε: {clean}")
        if powerlevel10k_enabled():
            SUMMARY.success("Το όνομα prompt ενσωματώθηκε στο ενεργό Powerlevel10k prompt")
    else:
        SUMMARY.success("Το custom όνομα prompt αφαιρέθηκε")

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
    """Ζητά μία φορά ταυτότητα prompt, χρησιμοποιώντας ξανά υπάρχουσα/μεταφερμένη τιμή."""
    current = get_prompt_name()
    if current:
        SUMMARY.success(f"Χρησιμοποιήθηκε ξανά το υπάρχον όνομα Zsh prompt: {current}")
        return True

    default = _default_prompt_name()
    if NON_INTERACTIVE:
        state = load_state()
        state["prompt_name"] = default
        save_state(state)
        SUMMARY.warning(f"Το non-interactive setup χρησιμοποίησε προεπιλεγμένο όνομα prompt: {default}")
        return True

    header("Αρχική ρύθμιση Zsh prompt")
    while True:
        entered = input(c(f"Όνομα prompt [{default}]: ", C.INFO)).strip()
        clean = sanitize_prompt_name(entered or default)
        if clean:
            state = load_state()
            state["prompt_name"] = clean
            save_state(state)
            SUMMARY.success(f"Ρυθμίστηκε το όνομα Zsh prompt: {clean}")
            return True
        print(c("Εισαγάγετε έγκυρο όνομα prompt.", C.WARN))


def run_powerlevel10k_wizard(
    *,
    required: bool = False,
    activate: bool = False,
    make_safety_backup: bool = True,
) -> bool:
    """Ρυθμίζει ρητά το Powerlevel10k· ποτέ από απλή εκκίνηση terminal."""
    if not require_termux():
        return False

    existing_before = powerlevel10k_config_exists()
    header("Ρύθμιση Powerlevel10k" + (" — απαιτείται στην πρώτη εγκατάσταση" if required else ""))

    if existing_before:
        adopt_existing_powerlevel10k_config(announce=True)
        configure_zshrc()
        if activate:
            activate_zsh_now()
        return True

    if NON_INTERACTIVE:
        _save_powerlevel10k_state(False, personalization_complete=False)
        configure_zshrc()
        SUMMARY.warning("Η πρώτη ρύθμιση Powerlevel10k εκκρεμεί επειδή αυτή η εκτέλεση είναι non-interactive")
        return False

    if not required:
        if not ask_yes_no("Εκτέλεση του Powerlevel10k configuration wizard τώρα;", default=True):
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
        SUMMARY.failure("Το Powerlevel10k δεν μπόρεσε να εγκατασταθεί")
        return False

    attempts = 2 if required else 1
    for attempt in range(attempts):
        _save_powerlevel10k_state(True, personalization_complete=False)
        configure_zshrc()
        zsh_path = shutil.which("zsh")
        if not zsh_path:
            SUMMARY.failure("Το Zsh δεν είναι διαθέσιμο")
            return False

        wizard = run_cmd([zsh_path, "-ic", 'source "$HOME/.zshrc"; p10k configure'], check=False)
        if wizard.returncode == 0 and powerlevel10k_config_exists():
            _save_powerlevel10k_state(True, personalization_complete=bool(get_prompt_name()))
            configure_zshrc()
            SUMMARY.success("Η ρύθμιση Powerlevel10k ολοκληρώθηκε και αποθηκεύτηκε")
            if activate:
                activate_zsh_now()
            return True

        if attempt + 1 < attempts:
            if not ask_yes_no("Η ρύθμιση Powerlevel10k δεν ολοκληρώθηκε. Εκτέλεση wizard ξανά;", default=True):
                break

    _save_powerlevel10k_state(False, personalization_complete=False)
    configure_zshrc()
    SUMMARY.warning("Η ρύθμιση Powerlevel10k παραμένει ελλιπής. Δεν θα ανοίγει αυτόματα στην εκκίνηση· χρησιμοποιήστε την επιλογή 9 για να την ολοκληρώσετε.")
    if activate:
        activate_zsh_now()
    return False


def ensure_first_run_shell_personalization() -> bool:
    """Ολοκληρώνει μία φορά prompt + Powerlevel10k, χρησιμοποιώντας υπάρχουσες ρυθμίσεις."""
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
    header("Όνομα Zsh Prompt")
    print("Τρέχον όνομα:", current or "(προεπιλεγμένο prompt)")
    print("Το όνομα εμφανίζεται επίσης μέσα στο Powerlevel10k όταν είναι ρυθμισμένο.")
    print("Αφήστε το κενό για να αφαιρεθεί το custom όνομα prompt.")
    name = input(c("Νέο όνομα prompt: ", C.INFO)).strip()
    make_backup()
    set_prompt_name(name, activate=False)
    SUMMARY.show()
    if shutil.which("zsh"):
        activate_zsh_now()


def configure_powerlevel10k_interactive() -> None:
    """Ρυθμίζει ή ξαναρυθμίζει το Powerlevel10k μόνο από τη σχετική επιλογή μενού."""
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
    """Ορίζει το Zsh ως προεπιλεγμένο Termux shell αντί να αφήνει ενεργό το Bash."""
    zsh_path = shutil.which("zsh")
    if not zsh_path:
        SUMMARY.failure("Το Zsh δεν είναι διαθέσιμο, οπότε δεν μπορεί να οριστεί ως προεπιλεγμένο shell")
        return False
    chsh_path = shutil.which("chsh")
    if not chsh_path:
        SUMMARY.warning("Το chsh δεν είναι διαθέσιμο· θα χρησιμοποιηθεί η μόνιμη μετάβαση Bash → Zsh")
        return False

    result = run_cmd([chsh_path, "-s", zsh_path], capture=True, check=False)
    if result.returncode != 0:
        SUMMARY.warning("Το chsh απέτυχε· η μόνιμη μετάβαση Bash → Zsh θα εξακολουθεί να επιβάλλει Zsh στις διαδραστικές εκκινήσεις")
        if result.stderr:
            print(result.stderr.rstrip())
        return False

    os.environ["SHELL"] = zsh_path
    state = load_state()
    state["default_shell"] = zsh_path
    save_state(state)
    SUMMARY.success(f"Το Zsh ορίστηκε ως προεπιλεγμένο Termux shell: {zsh_path}")
    return True


def _remove_zsh_handoff_block(text: str) -> str:
    pattern = re.compile(
        re.escape(ZSH_HANDOFF_START) + r"[\s\S]*?" + re.escape(ZSH_HANDOFF_END) + r"\n?"
    )
    return pattern.sub("", text).lstrip("\n")


def _install_zsh_handoff_in_file(path: Path, zsh_path: str) -> bool:
    """Εγκαθιστά idempotent handoff Bash/login χωρίς να διαγράφει άσχετο περιεχόμενο."""
    path.parent.mkdir(parents=True, exist_ok=True)
    original = read_text(path)
    remainder = _remove_zsh_handoff_block(original)
    zsh_q = shlex.quote(zsh_path)
    block = "\n".join(
        [
            ZSH_HANDOFF_START,
            "# Επιβάλλει Zsh σε κάθε διαδραστικό Termux terminal που ξεκινά μέσω Bash.",
            "# POSIX-compatible guard ώστε να είναι ασφαλές ακόμη και μέσα στο /etc/profile.",
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
                SUMMARY.failure(f"Το Zsh startup handoff απέτυχε στον έλεγχο σύνταξης Bash για {path}")
                if check.stderr:
                    print(check.stderr.rstrip())
                return False
        atomic_write_text(path, new_text, mode=mode_bits)
        return True
    finally:
        temp.unlink(missing_ok=True)


def install_zsh_startup_handoff() -> bool:
    """Επιβάλλει Zsh τώρα και σε μελλοντικά Termux terminals ακόμη κι αν αγνοηθεί το chsh."""
    zsh_path = shutil.which("zsh")
    if not zsh_path:
        SUMMARY.failure("Δεν ήταν δυνατή η εγκατάσταση μόνιμης μετάβασης σε Zsh επειδή το zsh δεν είναι διαθέσιμο")
        return False

    targets = (GLOBAL_BASHRC, GLOBAL_PROFILE, HOME / ".bashrc")
    ok = True
    for target in targets:
        ok = _install_zsh_handoff_in_file(target, zsh_path) and ok

    if ok:
        state = load_state()
        state["zsh_startup_handoff"] = True
        save_state(state)
        SUMMARY.success("Εγκαταστάθηκε μόνιμη μετάβαση Bash/login → Zsh για κάθε εκκίνηση Termux terminal")
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
        SUMMARY.success("Αφαιρέθηκε η μόνιμη μετάβαση Bash/login → Zsh")

def activate_zsh_now() -> bool:
    """Επιβάλλει η τρέχουσα διεργασία setup να γίνει διαδραστικό login Zsh."""
    zsh_path = shutil.which("zsh")
    if not zsh_path:
        SUMMARY.warning("Το Zsh δεν μπόρεσε να ενεργοποιηθεί στην τρέχουσα συνεδρία επειδή δεν είναι διαθέσιμο")
        return False

    zshrc = HOME / ".zshrc"
    if not zshrc.is_file():
        SUMMARY.warning("Το Zsh δεν μπόρεσε να ενεργοποιηθεί επειδή λείπει το ~/.zshrc")
        return False

    syntax = run_cmd([zsh_path, "-n", str(zshrc)], capture=True, check=False)
    if syntax.returncode != 0:
        SUMMARY.failure("Η άμεση ενεργοποίηση Zsh ακυρώθηκε επειδή το ~/.zshrc απέτυχε στον έλεγχο σύνταξης")
        if syntax.stderr:
            print(syntax.stderr.rstrip())
        return False

    if NON_INTERACTIVE:
        SUMMARY.success("Το Zsh είναι έτοιμο και θα χρησιμοποιηθεί στην επόμενη διαδραστική συνεδρία Termux")
        return False

    print(c("\nΜετάβαση της τρέχουσας συνεδρίας Termux σε Zsh τώρα...", C.INFO), flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    env = os.environ.copy()
    env["SHELL"] = zsh_path
    env["MOBILE_DEV_ZSH_HANDOFF"] = "1"
    try:
        # Το -i εγγυάται interactive prompt και το -l login Zsh.
        os.execve(zsh_path, [zsh_path, "-il"], env)
    except OSError as exc:
        SUMMARY.failure(f"Δεν ήταν δυνατή η μετάβαση της τρέχουσας συνεδρίας σε Zsh: {exc}")
        print(c("Εκτελέστε χειροκίνητα: exec zsh", C.WARN))
        return False


# -----------------------------------------------------------------------------
# Περιβάλλον χρήστη Termux
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
    """Κατεβάζει Meslo Nerd Font από τα επίσημα release assets με εναλλακτικό archive."""
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
                        raise RuntimeError("Το archive της Meslo δεν περιέχει TTF")
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
                        raise RuntimeError("Το archive της Meslo δεν περιέχει TTF")
                    chosen = None
                    for preferred in preferred_names:
                        chosen = next((m for m in members if Path(m.name).name == preferred), None)
                        if chosen is not None:
                            break
                    if chosen is None:
                        chosen = next((m for m in members if "regular" in Path(m.name).stem.lower()), members[0])
                    source = tf.extractfile(chosen)
                    if source is None:
                        raise RuntimeError("Δεν ήταν δυνατή η ανάγνωση της γραμματοσειράς")
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
            SUMMARY.success("Εγκαταστάθηκε η Meslo Nerd Font για το Termux")
            return True
        temp_font.unlink(missing_ok=True)

    SUMMARY.warning("Δεν ήταν δυνατή η λήψη της Nerd Font από τα επίσημα release assets· διατηρήθηκε η υπάρχουσα γραμματοσειρά")
    return False


def reload_termux_settings() -> None:
    if shutil.which("termux-reload-settings"):
        run_cmd(["termux-reload-settings"], capture=True, check=False)


def configure_termux_ui() -> None:
    header("Ρυθμίσεις εμφάνισης Termux")
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
    SUMMARY.success("Ρυθμίστηκαν τα πρόσθετα πλήκτρα και το αναβόσβημα του κέρσορα στο Termux")

    colors_path = TERMUX_DIR / "colors.properties"
    colors = replace_or_add_property(read_text(colors_path), "cursor", "cursor=#00FF00")
    atomic_write_text(colors_path, colors)
    SUMMARY.success("Ρυθμίστηκε το χρώμα του κέρσορα στο Termux")

    if shutil.which("curl"):
        download_font()
    else:
        SUMMARY.warning("Η εγκατάσταση γραμματοσειράς παραλείφθηκε επειδή το curl δεν είναι διαθέσιμο")

    reload_termux_settings()
    safe_notify("Mobile Developer Setup: ενημερώθηκε η εμφάνιση του Termux")


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
    SUMMARY.success(f"Τα υπάρχοντα αρχεία Neovim αποθηκεύτηκαν σε backup: {out}")
    return out


def install_nvchad() -> None:
    header("NvChad")
    if not shutil.which("git") or not shutil.which("nvim"):
        SUMMARY.warning("Το NvChad παραλείφθηκε επειδή το git ή το neovim δεν είναι διαθέσιμο")
        return

    if NVIM_CONFIG_DIR.exists() and git_repo(NVIM_CONFIG_DIR):
        remote = run_cmd(
            ["git", "-C", str(NVIM_CONFIG_DIR), "remote", "get-url", "origin"],
            capture=True,
            check=False,
        )
        if remote.returncode == 0 and "NvChad/starter" in (remote.stdout or ""):
            SUMMARY.success("Η αρχική ρύθμιση NvChad υπάρχει ήδη")
            return

    existing_nvim = any(p.exists() for p in (NVIM_CONFIG_DIR, NVIM_DATA_DIR, NVIM_STATE_DIR))
    if existing_nvim:
        if not ask_yes_no("Βρέθηκαν υπάρχοντα αρχεία Neovim. Να δημιουργηθεί backup και να αντικατασταθούν με NvChad;", default=False):
            SUMMARY.warning("Η εγκατάσταση NvChad παραλείφθηκε για να διατηρηθούν τα υπάρχοντα αρχεία Neovim")
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
        SUMMARY.success("Εγκαταστάθηκε η επίσημη αρχική ρύθμιση NvChad")
        print(c("Άνοιξε το nvim μία φορά ώστε το lazy.nvim να κατεβάσει τα plugins και μετά, αν θέλεις, εκτέλεσε :MasonInstallAll.", C.INFO))
    else:
        shutil.rmtree(NVIM_CONFIG_DIR, ignore_errors=True)
        SUMMARY.warning("Το clone του NvChad starter απέτυχε· το backup σου παραμένει διαθέσιμο στο ~/.mobile-dev-setup/nvim-backups")


def update_nvchad() -> None:
    if not NVIM_CONFIG_DIR.exists() or not git_repo(NVIM_CONFIG_DIR):
        SUMMARY.warning("Η ρύθμιση NvChad δεν είναι Git checkout· η ενημέρωση παραλείφθηκε")
        return
    remote = run_cmd(["git", "-C", str(NVIM_CONFIG_DIR), "remote", "get-url", "origin"], capture=True, check=False)
    if remote.returncode != 0 or "NvChad/starter" not in (remote.stdout or ""):
        SUMMARY.warning("Η υπάρχουσα ρύθμιση Neovim δεν είναι NvChad/starter· η ενημέρωση παραλείφθηκε")
        return
    result = run_cmd(["git", "-C", str(NVIM_CONFIG_DIR), "pull", "--ff-only"], check=False)
    if result.returncode == 0:
        SUMMARY.success("Το NvChad starter ενημερώθηκε")
    else:
        SUMMARY.warning("Το NvChad starter δεν μπόρεσε να ενημερωθεί με fast-forward")


# -----------------------------------------------------------------------------
# Κύριες ροές εργασίας
# -----------------------------------------------------------------------------


def reset_log() -> None:
    ensure_dirs()
    atomic_write_text(LOG_FILE, f"Εκτέλεση Mobile Developer Setup: {time.ctime()}\n")


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
    header("Mobile Developer Setup — Εγκατάσταση")
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
        SUMMARY.failure("Η πλήρης εγκατάσταση του developer περιβάλλοντος δεν ολοκληρώθηκε. Διορθώστε τα παραπάνω σφάλματα και εκτελέστε Επιδιόρθωση.")

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
                SUMMARY.warning("Η αρχική προσωποποίηση του Zsh παραμένει ελλιπής· ολοκληρώστε τη ρύθμιση Powerlevel10k από την επιλογή 9.")

    if configure_ui:
        configure_termux_ui()

    if install_nvim:
        install_nvchad()

    state = load_state()
    state["last_install"] = now_stamp()
    save_state(state)
    safe_notify("Το Mobile Developer Setup ολοκληρώθηκε")
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
    header("Mobile Developer Setup — Ενημέρωση")
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
    header("Mobile Developer Setup — Επιδιόρθωση")
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
                SUMMARY.warning("Η προσωποποίηση Zsh παραμένει ελλιπής· χρησιμοποιήστε την επιλογή 9 για να ολοκληρώσετε το Powerlevel10k.")
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
    SUMMARY.success("Αφαιρέθηκε το διαχειριζόμενο τμήμα από το ~/.zshrc")


def uninstall_files_only(*, reset_summary: bool = True) -> None:
    if reset_summary:
        SUMMARY.clear()
    if not require_termux():
        return
    header("Αφαίρεση αρχείων που διαχειρίζεται το setup")
    state = load_state()
    managed = [Path(p) for p in state.get("managed_paths", []) if isinstance(p, str)]

    # Αφαιρούμε το διαχειριζόμενο block του zsh ανεξάρτητα από το ποιος έχει το ~/.zshrc.
    remove_managed_zsh_block()
    remove_zsh_startup_handoff()

    # Διαγράφουμε μόνο διαδρομές που έχουν καταγραφεί ρητά ως δημιουργημένες από αυτό το script.
    for path in sorted(managed, key=lambda p: len(str(p)), reverse=True):
        try:
            path.relative_to(HOME)
        except ValueError:
            SUMMARY.warning(f"Παραλείφθηκε μη ασφαλής διαχειριζόμενη διαδρομή εκτός HOME: {path}")
            continue
        if not path.exists():
            continue
        try:
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
            SUMMARY.success(f"Αφαιρέθηκε: {path}")
        except OSError as exc:
            SUMMARY.warning(f"Δεν ήταν δυνατή η αφαίρεση του {path}: {exc}")

    # Το TOOLS_DIR περιέχει αυτή τη στιγμή μόνο υλικό που ανήκει στο setup.
    if TOOLS_DIR.exists():
        shutil.rmtree(TOOLS_DIR, ignore_errors=True)
        SUMMARY.success(f"Removed {TOOLS_DIR}")

    state["managed_paths"] = []
    save_state(state)
    SUMMARY.show()
    print(c("Τα εγκατεστημένα πακέτα apt/npm διατηρήθηκαν σκόπιμα.", C.INFO))


def restore_and_remove() -> None:
    SUMMARY.clear()
    if not require_termux():
        return
    backup = choose_backup_interactive()
    if backup is None:
        return
    if not ask_yes_no(f"Να επαναφερθεί το {backup.name} και να αφαιρεθούν τα αρχεία που διαχειρίζεται η ρύθμιση;", default=True):
        return
    restore_backup(backup)
    uninstall_files_only(reset_summary=False)
    print(c("Κάνε επανεκκίνηση του Termux για να ολοκληρωθεί η επαναφορά.", C.INFO))


def backup_only() -> None:
    SUMMARY.clear()
    if not require_termux():
        return
    header("Αντίγραφο ασφαλείας ρυθμίσεων Termux")
    make_backup()


def restore_latest() -> None:
    SUMMARY.clear()
    if not require_termux():
        return
    backups = list_backups()
    if not backups:
        print(c(f"Δεν βρέθηκαν αντίγραφα ασφαλείας στο {BACKUPS_DIR}", C.WARN))
        return
    restore_backup(backups[0])
    SUMMARY.show()


def show_info() -> None:
    header("Πληροφορίες Mobile Developer Setup")
    state = load_state()
    print("Φάκελος εφαρμογής:       ", APP_DIR)
    print("Αντίγραφα ασφαλείας:     ", BACKUPS_DIR)
    print("Αρχείο καταγραφής:       ", LOG_FILE)
    print("Plugins Zsh:              ", ZSH_PLUGINS_DIR)
    print("Oh My Zsh:                ", OH_MY_ZSH_DIR)
    print("Ρύθμιση Neovim:           ", NVIM_CONFIG_DIR)
    print("Backups NvChad:           ", NVI_BACKUPS_DIR)
    print("Εντοπίστηκε Termux:       ", "ναι" if is_termux() else "όχι")
    print("Όνομα Zsh prompt:         ", get_prompt_name() or "(προεπιλεγμένο)")
    print("Powerlevel10k:             ", "ρυθμισμένο" if powerlevel10k_enabled() and powerlevel10k_config_exists() else "εκκρεμεί ρύθμιση")
    print("Global bash.bashrc:       ", GLOBAL_BASHRC)
    print("Διαχειριζόμενες διαδρομές:", len(state.get("managed_paths", [])))
    if state.get("install_backup"):
        print("Backup εγκατάστασης:      ", state["install_backup"])
    if state.get("last_backup"):
        print("Τελευταίο backup:         ", state["last_backup"])
    if state.get("last_install"):
        print("Τελευταία εγκατάσταση:    ", state["last_install"])
    if state.get("last_update"):
        print("Τελευταία ενημέρωση:      ", state["last_update"])


def menu() -> None:
    ensure_dirs()
    while True:
        header("Mobile Developer Setup")
        print("1) Εγκατάσταση / Ρύθμιση")
        print("2) Ενημέρωση εγκατεστημένων εργαλείων")
        print("3) Επιδιόρθωση ελλιπών/χαλασμένων στοιχείων")
        print("4) Αντίγραφο ασφαλείας ρυθμίσεων Termux")
        print("5) Επαναφορά ρυθμίσεων + αφαίρεση αρχείων της ρύθμισης")
        print("6) Αφαίρεση μόνο των αρχείων που διαχειρίζεται η ρύθμιση")
        print("7) Πληροφορίες")
        print("8) Ορισμός / αλλαγή ονόματος Zsh prompt")
        print("9) Ρύθμιση / επαναρύθμιση Powerlevel10k")
        print("0) Έξοδος")
        choice = input(c("\nΕπίλεξε αριθμό: ", C.INFO)).strip()

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
                print(c("Έξοδος ολοκληρώθηκε.", C.OK))
                return
            else:
                print(c("Μη έγκυρη επιλογή.", C.WARN))
                continue
        except KeyboardInterrupt:
            print("\n" + c("Ακυρώθηκε.", C.WARN))
        except Exception as exc:
            SUMMARY.failure(str(exc))
            print(c(f"Δες το αρχείο καταγραφής στο {LOG_FILE}", C.INFO))

        if not NON_INTERACTIVE:
            input(c("\nΠάτησε Enter για επιστροφή στο μενού…", C.DIM))


def build_parser() -> argparse.ArgumentParser:
    parser = GreekArgumentParser(description="Αξιόπιστη ρύθμιση περιβάλλοντος ανάπτυξης για Termux σε κινητό.", add_help=False)
    parser.add_argument("-h", "--help", action="help", help="Εμφάνιση αυτού του μηνύματος βοήθειας και έξοδος")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--install", action="store_true", help="Εκτέλεση πλήρους εγκατάστασης")
    action.add_argument("--update", action="store_true", help="Ενημέρωση πακέτων, εργαλείων npm και διαχειριζόμενων Git checkouts")
    action.add_argument("--repair", action="store_true", help="Επιδιόρθωση στοιχείων ρύθμισης που λείπουν")
    action.add_argument("--backup", action="store_true", help="Δημιουργία αντιγράφου ασφαλείας ρυθμίσεων")
    action.add_argument("--restore-latest", action="store_true", help="Επαναφορά του νεότερου αντιγράφου ασφαλείας ρυθμίσεων")
    action.add_argument("--uninstall-files", action="store_true", help="Αφαίρεση μόνο αρχείων που δημιουργήθηκαν/διαχειρίζονται από αυτή τη ρύθμιση")
    action.add_argument("--info", action="store_true", help="Εμφάνιση διαδρομών και κατάστασης της ρύθμισης")
    action.add_argument("--prompt-name", metavar="ΟΝΟΜΑ", help="Ορισμός ή αλλαγή του μόνιμου ονόματος του Zsh prompt")
    action.add_argument("--powerlevel10k", action="store_true", help="Ρητή ενεργοποίηση και ρύθμιση του Powerlevel10k")

    parser.add_argument("-y", "--yes", action="store_true", help="Θεώρηση απάντησης ναι στα αιτήματα επιβεβαίωσης")
    parser.add_argument("--non-interactive", action="store_true", help="Χωρίς αιτήματα εισαγωγής από τον χρήστη")
    parser.add_argument("--no-upgrade", action="store_true", help="Να μην εκτελεστεί pkg upgrade")
    parser.add_argument("--skip-zsh", action="store_true", help="Να μην αντικατασταθεί το shell περιβάλλον και να μην εγκατασταθεί/ρυθμιστεί το Zsh")
    parser.add_argument("--skip-ui", action="store_true", help="Να μην αλλάξουν πλήκτρα/χρώματα/γραμματοσειρά του Termux")
    parser.add_argument("--skip-nvchad", action="store_true", help="Να μην εγκατασταθεί το NvChad")
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

