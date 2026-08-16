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
# Mobile Developer Setup για Termux — Ελληνική έκδοση
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
    TermuxPackage("tur-repo", note="Πακέτο repository που χρησιμοποιείται για πακέτα TUR όπως το mongodb."),
]

TUR_PACKAGES = [
    TermuxPackage("mongodb", note="Προαιρετικό πακέτο του Termux User Repository."),
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


def make_backup() -> Path:
    ensure_dirs()
    stamp = now_stamp()
    out = BACKUPS_DIR / f"termux-settings-backup-{stamp}.tar.gz"
    manifest = {
        "created": stamp,
        "home": str(HOME),
        "targets": [],
        "note": "Αντίγραφο ασφαλείας ρυθμίσεων/config του Termux πριν από αλλαγές του Mobile Developer Setup.",
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
    SUMMARY.success(f"Το αντίγραφο ασφαλείας αποθηκεύτηκε: {out}")
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

            # Επαναφέρουμε μόνο αρχεία μέσα στο τρέχον HOME ώστε να αποφεύγονται αυθαίρετες εγγραφές.
            try:
                target.relative_to(HOME)
            except ValueError:
                SUMMARY.warning(f"Παραλείφθηκε μη ασφαλής διαδρομή backup: {target}")
                continue

            if not item.get("existed", False):
                if target.exists() and target.is_file():
                    target.unlink()
                    SUMMARY.success(f"Αφαιρέθηκε αρχείο που δεν υπήρχε όταν δημιουργήθηκε το backup: {target}")
                continue

            archive_name = item.get("archive_name")
            if not isinstance(archive_name, str) or not archive_name.startswith("files/"):
                SUMMARY.warning(f"Λείπει καταχώριση αρχείου στο backup για: {target}")
                continue

            try:
                member = tf.getmember(archive_name)
                source = tf.extractfile(member)
            except KeyError:
                source = None
            if source is None:
                SUMMARY.warning(f"Λείπουν δεδομένα backup για: {target}")
                continue

            data = source.read()
            expected = item.get("sha256")
            if expected:
                actual = hashlib.sha256(data).hexdigest()
                if actual != expected:
                    raise RuntimeError(f"Ο έλεγχος ακεραιότητας του backup απέτυχε για: {target}")

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
            SUMMARY.success(f"Επαναφέρθηκε: {target}")

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


def install_packages(*, include_optional: bool = True, force: bool = False) -> bool:
    header("Εγκατάσταση βασικών πακέτων Termux")
    core_ok = True
    for package in CORE_PACKAGES:
        core_ok = install_one_pkg(package, force=force) and core_ok

    if include_optional:
        header("Εγκατάσταση προαιρετικών πακέτων Termux")
        for package in OPTIONAL_PACKAGES:
            install_one_pkg(package, force=force)

        # Τα πακέτα TUR πρέπει να δοκιμάζονται μόνο αφού εγκατασταθεί το tur-repo.
        if dpkg_installed("tur-repo"):
            header("Εγκατάσταση προαιρετικών πακέτων Termux User Repository")
            # Κάνουμε μία ανανέωση επειδή η εγκατάσταση του tur-repo προσθέτει νέο repository.
            run_cmd(["pkg", "update", "-y"], check=False)
            for package in TUR_PACKAGES:
                install_one_pkg(package, force=force)
        else:
            SUMMARY.warning("Το tur-repo δεν είναι διαθέσιμο, οπότε το mongodb παραλείφθηκε")

    return core_ok


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


def install_npm_tools(*, update: bool = False) -> None:
    header("Εγκατάσταση καθολικών εργαλείων ανάπτυξης npm")
    if not shutil.which("npm"):
        SUMMARY.warning("Το npm δεν είναι διαθέσιμο· τα εργαλεία ανάπτυξης npm παραλείφθηκαν")
        return

    # Αποφεύγουμε πρόσθετη κίνηση δικτύου από npm audit/fund στις καθολικές εγκαταστάσεις εργαλείων.
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
    prefix = os.environ.get("PREFIX", "")
    if not prefix:
        return
    target = Path(prefix) / "lib" / "node_modules" / "localtunnel" / "node_modules" / "openurl" / "openurl.js"
    if not target.exists():
        SUMMARY.warning("Η διόρθωση Android open-url του localtunnel παραλείφθηκε (δεν βρέθηκε η αναμενόμενη δομή openurl.js)")
        return

    text = read_text(target)
    if "case 'android':" in text or 'case "android":' in text:
        SUMMARY.success("Η διόρθωση Android open-url του localtunnel υπάρχει ήδη")
        return

    # Εφαρμόζουμε patch μόνο όταν υπάρχει γνωστή δομή switch. Δεν κάνουμε ποτέ τυφλή εισαγωγή με sed.
    pattern = re.compile(r"(case ['\"]win32['\"]:[\s\S]*?\bbreak;)")
    match = pattern.search(text)
    if not match:
        SUMMARY.warning("Το openurl.js του localtunnel άλλαξε upstream· δεν εφαρμόστηκε το ασφαλές Android patch")
        return

    insertion = (
        match.group(1)
        + "\n    case 'android':\n"
        + "        command = 'termux-open-url';\n"
        + "        break;"
    )
    patched = text[: match.start()] + insertion + text[match.end() :]
    atomic_write_text(target, patched)
    SUMMARY.success("Το localtunnel ρυθμίστηκε να χρησιμοποιεί termux-open-url στο Android")


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


def configure_zshrc() -> None:
    header("Ρύθμιση του ~/.zshrc")
    zshrc = HOME / ".zshrc"
    existing = read_text(zshrc)
    fpath_lines, source_lines = _zsh_plugin_lines()

    lines = [
        MARK_BEGIN,
        "# Διαχειρίζεται από το Mobile Developer Setup. Κάνε προσωπικές αλλαγές έξω από αυτό το block.",
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
        SUMMARY.success("Το ~/.zshrc ρυθμίστηκε και πέρασε έλεγχο σύνταξης")
    else:
        SUMMARY.failure("Το ~/.zshrc απέτυχε στον έλεγχο σύνταξης zsh· επανάφερε το backup αν χρειάζεται")
        if result.stderr:
            print(result.stderr.rstrip())


def maybe_set_default_zsh() -> None:
    if not shutil.which("zsh") or not shutil.which("chsh"):
        return
    current = os.environ.get("SHELL", "")
    zsh_path = shutil.which("zsh") or "zsh"
    if current.endswith("/zsh"):
        SUMMARY.success("Το Zsh είναι ήδη το τρέχον login shell")
        return
    if ask_yes_no("Να οριστεί το Zsh ως προεπιλεγμένο login shell του Termux;", default=True):
        result = run_cmd(["chsh", "-s", zsh_path], check=False)
        if result.returncode == 0:
            SUMMARY.success("Το Zsh ορίστηκε ως προεπιλεγμένο shell")
        else:
            SUMMARY.warning("Δεν ήταν δυνατός ο ορισμός του Zsh ως προεπιλεγμένου shell· μπορείς ακόμη να εκτελέσεις: exec zsh")


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
        SUMMARY.warning("Η λήψη Nerd Font απέτυχε ή το αρχείο δεν φαινόταν έγκυρη γραμματοσειρά· διατηρήθηκε η υπάρχουσα")
        return False
    temp.replace(target)
    SUMMARY.success("Η Meslo Nerd Font εγκαταστάθηκε για το Termux")
    return True


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
    header("Mobile Developer Setup — Εγκατάσταση")
    backup_path = make_backup()
    state = load_state()
    state["install_backup"] = str(backup_path)
    save_state(state)

    if not pkg_refresh(upgrade=upgrade):
        SUMMARY.show()
        return

    core_ok = install_packages(include_optional=include_optional)
    if not core_ok:
        SUMMARY.failure("Η εγκατάσταση βασικών πακέτων δεν ολοκληρώθηκε. Διόρθωσε τα παραπάνω σφάλματα πακέτων και εκτέλεσε Επιδιόρθωση.")

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
    safe_notify("Το Mobile Developer Setup ολοκληρώθηκε")
    SUMMARY.show()
    print(c("\nΚάνε επανεκκίνηση του Termux ή εκτέλεσε 'exec zsh' αν ενεργοποίησες το Zsh.", C.INFO))


def run_update(*, include_optional: bool = True, upgrade: bool = True) -> None:
    SUMMARY.clear()
    if not require_termux():
        return
    reset_log()
    header("Mobile Developer Setup — Ενημέρωση")
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
    header("Mobile Developer Setup — Επιδιόρθωση")
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

    parser.add_argument("-y", "--yes", action="store_true", help="Θεώρηση απάντησης ναι στα αιτήματα επιβεβαίωσης")
    parser.add_argument("--non-interactive", action="store_true", help="Χωρίς αιτήματα εισαγωγής από τον χρήστη")
    parser.add_argument("--skip-optional", action="store_true", help="Παράλειψη προαιρετικών πακέτων Termux")
    parser.add_argument("--no-upgrade", action="store_true", help="Να μην εκτελεστεί pkg upgrade")
    parser.add_argument("--skip-zsh", action="store_true", help="Να μην εγκατασταθεί/ρυθμιστεί το Oh My Zsh ή τα plugins")
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
