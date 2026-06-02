import os
import sys
import json
import re
import subprocess
import shutil
import zipfile
import time
import threading
import traceback
import html as html_lib
import mimetypes
from urllib.parse import quote
from pathlib import Path
from typing import List, Tuple, Set, Dict, Any

APP_NAME = "Dead Man's Switch"
LEGACY_APP_NAMES = ["Dead Switch"]
SCRIPT_FILE_NAME = "Dead Man's Switch.py"
REPO_NAME = "dead-mans-switch"
FINAL_REPO_NAME = "dead-mans-switch"
APP_VERSION = "2026-06-02 force-new-repo-visible-v3"
LEGACY_REPO_NAMES = ["Dead-Switch", "DeadSwitch", "Dead_Switch", "Dead-Switch.py", "Dead Switch", "dead-switch"]


# Hard-coded repository target. Do not read this from settings.
# This prevents the script from ever creating the old Dead-Switch repo again.
assert REPO_NAME == "dead-mans-switch"
assert FINAL_REPO_NAME == "dead-mans-switch"

def enforce_final_repo_name_runtime():
    """Hard safety: this script must never create/use the old Dead-Switch repo name."""
    global REPO_NAME
    if REPO_NAME != FINAL_REPO_NAME:
        log(f"[!] Runtime repo name corrected from {REPO_NAME!r} to {FINAL_REPO_NAME!r}") if 'log' in globals() else None
        REPO_NAME = FINAL_REPO_NAME
    return FINAL_REPO_NAME


def resolve_downloads_dir() -> Path:
    home = Path.home()
    candidates = [
        home / "storage" / "downloads",
        Path("/storage/emulated/0/Download"),
        Path("/sdcard/Download"),
    ]
    for c in candidates:
        if c.exists():
            return c
    return Path("/storage/emulated/0/Download")

DOWNLOADS_DIR = resolve_downloads_dir()

def resolve_local_dir() -> Path:
    preferred = DOWNLOADS_DIR / APP_NAME
    if preferred.exists():
        return preferred
    for legacy_name in LEGACY_APP_NAMES:
        legacy_path = DOWNLOADS_DIR / legacy_name
        if legacy_path.exists():
            try:
                legacy_path.rename(preferred)
                return preferred
            except Exception:
                # Fall back to the existing legacy folder instead of losing access to user files.
                return legacy_path
    return preferred

LOCAL_DIR = resolve_local_dir()

MAX_BATCH_BYTES = 40 * 1024 * 1024
MAX_FILE_BYTES = 40 * 1024 * 1024

CONFIG_PATH = Path.home() / ".dead_switch_settings.json"
PERSONAL_DETAILS_JSON_NAME = "Personal_Details.json"
PERSONAL_DETAILS_TXT_NAME = "Personal_Details.txt"
SITE_ASSETS_DIR_NAME = "Assets"
SITE_CSS_NAME = "style.css"
SITE_JS_NAME = "scripts.js"
SITE_MANIFEST_NAME = "dead_switch_site_manifest.json"
PAGES_DIR_NAME = "Pages"
PREVIOUS_HISTORY_DIR_NAME = "History"
LEGACY_PREVIOUS_HISTORY_DIR_NAME = "Previous History"
PKG_UPDATED_ONCE = False
LOGS_DIR_NAME = "Logs"
RUN_LOG_FILE = LOCAL_DIR / LOGS_DIR_NAME / f"Dead_Mans_Switch_Log_{time.strftime('%Y-%m-%d_%H-%M-%S')}.txt"
_ORIGINAL_STDOUT = sys.stdout
_ORIGINAL_STDERR = sys.stderr
_LOGGING_READY = False

def safe_text(value) -> str:
    try:
        return str(value)
    except Exception:
        return repr(value)

def command_to_text(cmd) -> str:
    try:
        if isinstance(cmd, (list, tuple)):
            return " ".join(safe_text(x) for x in cmd)
        return safe_text(cmd)
    except Exception:
        return repr(cmd)

def ensure_logs_dir() -> Path:
    try:
        (LOCAL_DIR / LOGS_DIR_NAME).mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return LOCAL_DIR / LOGS_DIR_NAME

def append_log(level: str, message: str):
    try:
        ensure_logs_dir()
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with RUN_LOG_FILE.open("a", encoding="utf-8", errors="replace") as f:
            f.write(f"[{stamp}] [{level}] {message}\n")
    except Exception:
        pass

def log_exception(context: str):
    try:
        append_log("EXCEPTION", f"{context}\n{traceback.format_exc()}")
    except Exception:
        pass

class TeeStream:
    def __init__(self, original_stream, stream_name: str):
        self.original_stream = original_stream
        self.stream_name = stream_name

    def write(self, data):
        try:
            self.original_stream.write(data)
        except Exception:
            pass
        try:
            ensure_logs_dir()
            with RUN_LOG_FILE.open("a", encoding="utf-8", errors="replace") as f:
                f.write(data)
        except Exception:
            pass

    def flush(self):
        try:
            self.original_stream.flush()
        except Exception:
            pass

    def isatty(self):
        try:
            return self.original_stream.isatty()
        except Exception:
            return False


def setup_runtime_logging():
    global _LOGGING_READY
    if _LOGGING_READY:
        return
    _LOGGING_READY = True
    ensure_logs_dir()
    append_log("START", f"Dead Man's Switch started | script={Path(__file__).resolve()} | python={sys.version.split()[0]} | cwd={Path.cwd()}")
    sys.stdout = TeeStream(_ORIGINAL_STDOUT, "stdout")
    sys.stderr = TeeStream(_ORIGINAL_STDERR, "stderr")
    print(f"[*] Log file: {RUN_LOG_FILE}")

def get_log_file_path() -> Path:
    ensure_logs_dir()
    return RUN_LOG_FILE

README_TEXT = """# Dead Man's Switch (Dead Man's Switch)

A *dead man's switch* is a safety mechanism that triggers an action if the operator becomes unable to continue—
for example, if they stop checking in.

In simple terms: if a person can’t confirm they’re okay, the system can reveal instructions, transfer access,
send alerts, or publish information.

This repository can be used as a “dead man’s switch” *backup concept*:
- Keep important documents or instructions in this repo.
- Update it whenever you need.
- You can automate check-ins and actions separately (outside of this script).

> This script does **not** implement automatic triggering logic by itself.
> It only syncs the contents of your local folder to GitHub, and can optionally wipe/delete the repo.

---

# Dead Man's Switch (Νεκροδιακόπτης / Dead Man's Switch)

Ο *dead man’s switch* είναι ένας μηχανισμός ασφαλείας που ενεργοποιεί μια ενέργεια αν ο χειριστής δεν μπορεί
να συνεχίσει—π.χ. αν σταματήσει να “κάνει check‑in”.

Με απλά λόγια: αν κάποιος δεν μπορεί να επιβεβαιώσει ότι είναι καλά, το σύστημα μπορεί να αποκαλύψει οδηγίες,
να μεταφέρει πρόσβαση, να στείλει ειδοποιήσεις ή να δημοσιεύσει πληροφορίες.

Αυτό το αποθετήριο μπορεί να χρησιμοποιηθεί ως ένα “backup concept” dead man’s switch:
- Κράτα σημαντικά αρχεία ή οδηγίες εδώ.
- Ενημέρωνέ το όποτε χρειάζεται.
- Μπορείς να αυτοματοποιήσεις check‑ins και ενέργειες ξεχωριστά (εκτός αυτού του script).

> Αυτό το script **δεν** υλοποιεί από μόνο του την αυτόματη ενεργοποίηση.
> Απλά συγχρονίζει τον φάκελό σου στο GitHub και προαιρετικά μπορεί να κάνει wipe/delete το repo.
"""

def load_settings() -> dict:
    defaults = {
        "visibility": "public",
        "help_photo_interval": 5,
        "help_video_interval": 5,
        "help_video_duration": 5,
        "help_mic_interval": 10,
        "help_location_interval": 180,
        "help_push_interval": 300,
        "help_contacts": [],
        "help_first_setup_done": False
    }
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for k, v in data.items():
                    if k in defaults:
                        defaults[k] = v
    except Exception:
        pass

    vis = str(defaults.get("visibility", "public")).lower().strip()
    if vis not in ("public", "private"):
        vis = "public"
    defaults["visibility"] = vis

    interval_defaults = {
        "help_photo_interval": 5,
        "help_video_interval": 5,
        "help_video_duration": 5,
        "help_mic_interval": 10,
        "help_location_interval": 180,
        "help_push_interval": 300,
    }
    for k, default_value in interval_defaults.items():
        try:
            defaults[k] = int(defaults.get(k, default_value))
        except Exception:
            defaults[k] = default_value
        if defaults[k] < 1:
            defaults[k] = default_value
    if defaults["help_push_interval"] < 30:
        defaults["help_push_interval"] = 30

    clean_contacts = []
    if isinstance(defaults.get("help_contacts"), list):
        for c in defaults["help_contacts"]:
            if not isinstance(c, dict):
                continue
            name = str(c.get("name", "")).strip()
            phone = str(c.get("phone", "")).strip()
            if name and phone:
                clean_contacts.append({"name": name, "phone": phone})
    defaults["help_contacts"] = clean_contacts
    defaults["help_first_setup_done"] = bool(defaults.get("help_first_setup_done", False))
    return defaults

def save_settings(settings: dict):
    try:
        CONFIG_PATH.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

def get_visibility() -> str:
    return load_settings().get("visibility", "public")

def set_visibility(vis: str):
    vis = (vis or "").lower().strip()
    if vis not in ("public", "private"):
        print("[!] Invalid visibility. Use public/private.")
        return
    settings = load_settings()
    settings["visibility"] = vis
    save_settings(settings)
    print(f"[✓] Saved repository visibility preference: {vis.upper()}")

def run_rc(cmd, cwd=None, capture=False):
    cmd_text = command_to_text(cmd)
    append_log("CMD", f"cwd={cwd or Path.cwd()} | {cmd_text}")
    try:
        p = subprocess.run(cmd, cwd=cwd, text=True,
                           stdout=subprocess.PIPE if capture else None,
                           stderr=subprocess.STDOUT if capture else None)
        out = (p.stdout or "").strip() if capture else ""
        if p.returncode != 0:
            append_log("CMD_FAIL", f"rc={p.returncode} | {cmd_text}" + (f"\n{out}" if out else ""))
        return p.returncode, out
    except Exception:
        log_exception(f"Command crashed before return: {cmd_text}")
        raise

def run(cmd, cwd=None, check=True, capture=False):
    cmd_text = command_to_text(cmd)
    append_log("CMD", f"cwd={cwd or Path.cwd()} | {cmd_text}")
    try:
        if capture:
            p = subprocess.run(cmd, cwd=cwd, check=check, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out = (p.stdout or "").strip()
            if p.returncode != 0:
                append_log("CMD_FAIL", f"rc={p.returncode} | {cmd_text}" + (f"\n{out}" if out else ""))
            return out
        p = subprocess.run(cmd, cwd=cwd, check=check)
        if p.returncode != 0:
            append_log("CMD_FAIL", f"rc={p.returncode} | {cmd_text}")
        return ""
    except subprocess.CalledProcessError as e:
        msg = ""
        if getattr(e, "stdout", None):
            msg = "\n" + e.stdout
        append_log("CMD_EXCEPTION", f"{cmd_text}{msg}")
        print(f"\n[!] Command failed: {' '.join(map(str, cmd))}{msg}")
        if check:
            raise
        return msg.strip()
    except Exception:
        log_exception(f"Command crashed: {cmd_text}")
        if check:
            raise
        return ""

def which(bin_name):
    return shutil.which(bin_name) is not None

def ensure_termux_storage():
    termux_dl = Path.home() / "storage" / "downloads"
    if not DOWNLOADS_DIR.exists() or (str(DOWNLOADS_DIR).startswith(str(Path.home())) and not termux_dl.exists()):
        print("[!] Termux storage not set up (can't access shared storage yet).")
        print("    Running: termux-setup-storage")
        run(["termux-setup-storage"], check=False)
        print("\n    Allow the permission prompt, then re-run the script.")
        sys.exit(1)

def ensure_folder():
    ensure_termux_storage()
    if not LOCAL_DIR.exists():
        print(f"[*] Creating folder: {LOCAL_DIR}")
        LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    else:
        print(f"[*] Folder exists: {LOCAL_DIR}")

def ensure_pkg(bin_name, pkg_name=None):
    """Install a Termux package only when the required command is missing."""
    global PKG_UPDATED_ONCE
    if which(bin_name):
        return True
    if not which("pkg"):
        print(f"[!] Missing command: {bin_name}")
        print("    Automatic installation needs Termux's pkg command.")
        return False
    pkg_name = pkg_name or bin_name
    print(f"[*] {bin_name} is missing. Installing package: {pkg_name}")
    if not PKG_UPDATED_ONCE:
        run(["pkg", "update", "-y"], check=False)
        PKG_UPDATED_ONCE = True
    run(["pkg", "install", "-y", pkg_name], check=False)
    if which(bin_name):
        print(f"[✓] Installed/available: {bin_name}")
        return True
    print(f"[!] {bin_name} is still missing after trying to install {pkg_name}.")
    return False

def ensure_git():
    return ensure_pkg("git", "git")

def ensure_gh():
    return ensure_pkg("gh", "gh")

def ensure_termux_open():
    return ensure_pkg("termux-open", "termux-tools")

def ensure_termux_api():
    needed_commands = [
        "termux-notification",
        "termux-camera-photo",
        "termux-camera-info",
        "termux-microphone-record",
        "termux-location",
        "termux-sms-send",
    ]
    missing = [cmd for cmd in needed_commands if not which(cmd)]
    if not missing:
        return True
    print("[*] Termux:API command(s) missing: " + ", ".join(missing))
    ensure_pkg("termux-notification", "termux-api")
    still_missing = [cmd for cmd in needed_commands if not which(cmd)]
    if still_missing:
        print("[!] Some Termux:API commands are still missing: " + ", ".join(still_missing))
        print("    Install the Termux:API app too, then allow permissions when Android asks.")
        print("    Package command: pkg install termux-api")
        return False
    print("[✓] Termux:API commands are available.")
    return True

def ensure_core_dependencies(include_termux_api: bool = False):
    """Install/check the common requirements. Everything is installed only if missing."""
    ensure_git()
    ensure_gh()
    ensure_termux_open()
    if include_termux_api:
        ensure_termux_api()

def check_install_requirements():
    print("\n=== Check / Install Requirements ===")
    ensure_folder()
    ensure_core_dependencies(include_termux_api=True)
    print("\nStatus:")
    checks = {
        "git": "git",
        "GitHub CLI": "gh",
        "termux-open": "termux-open",
        "Termux notification": "termux-notification",
        "Termux camera photo": "termux-camera-photo",
        "Termux camera info": "termux-camera-info",
        "Termux microphone": "termux-microphone-record",
        "Termux location": "termux-location",
        "Termux SMS": "termux-sms-send",
    }
    for label, cmd in checks.items():
        print(f"  {'[✓]' if which(cmd) else '[!]'} {label}: {cmd}")
    print("\nNote: Termux:API also needs the separate Android app and Android permissions.")

def ensure_logged_in():
    print("[*] Checking GitHub login status...")
    ok = subprocess.run(["gh", "auth", "status"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if ok:
        print("[*] GitHub: already logged in (saved in Termux HOME).")
        return
    print("\n[!] You are not logged in to GitHub CLI (gh).")
    print("    Starting device/web login (modern, no password).")
    print("    Follow the instructions in Termux.\n")
    run(["gh", "auth", "login", "--hostname", "github.com", "--git-protocol", "https", "--web"], check=False)
    ok = subprocess.run(["gh", "auth", "status"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if not ok:
        print("\n[!] Login still not completed. Run manually:")
        print("    gh auth login --hostname github.com --git-protocol https --web")
        sys.exit(1)

def get_token_scopes() -> set:
    out = run(["gh", "auth", "status", "-h", "github.com"], capture=True, check=False)
    scopes = set()
    if out:
        for line in out.splitlines():
            if "Token scopes:" in line:
                part = line.split("Token scopes:", 1)[1]
                found = re.findall(r"[A-Za-z0-9:_-]+", part)
                scopes.update(found)
                break
    return scopes

def ensure_scopes(required_scopes):
    scopes = get_token_scopes()
    missing = [sc for sc in required_scopes if sc not in scopes]
    if not missing:
        return
    print(f"[*] Missing GitHub token scopes: {', '.join(missing)}")
    print("[*] Requesting additional permissions (one-time)...")
    args = ["gh", "auth", "refresh", "-h", "github.com"]
    for sc in missing:
        args += ["-s", sc]
    run(args, check=False)

def ensure_repo_scope():
    ensure_scopes(["repo"])

def gh_user():
    out = run(["gh", "api", "user", "--jq", ".login"], capture=True, check=False)
    return (out or "").strip()

def repo_actual_name(owner: str, repo_name: str) -> str:
    """Return the real repository name from GitHub.

    Important: GitHub keeps redirects after a repository rename. When asking for
    an old name, the API can answer with the new repo. That is why callers must
    compare the returned .name with the requested name to know if the old repo
    still really exists.
    """
    if not owner or not repo_name:
        return ""
    # Use capture=True so GitHub's large JSON output never floods the terminal.
    rc, out = run_rc(["gh", "api", f"repos/{owner}/{repo_name}", "--jq", ".name"], capture=True)
    if rc == 0 and (out or "").strip():
        return (out or "").strip()
    rc, out = run_rc(["gh", "repo", "view", f"{owner}/{repo_name}", "--json", "name", "--jq", ".name"], capture=True)
    if rc == 0 and (out or "").strip():
        return (out or "").strip()
    return ""

def repo_html_url(owner: str, repo_name: str) -> str:
    rc, out = run_rc(["gh", "api", f"repos/{owner}/{repo_name}", "--jq", ".html_url"], capture=True)
    return (out or "").strip() if rc == 0 else ""

def repo_exists_named(owner: str, repo_name: str, exact: bool = True) -> bool:
    actual = repo_actual_name(owner, repo_name)
    if not actual:
        return False
    if exact:
        return actual.lower() == repo_name.lower()
    return True

def rename_repository(owner: str, old_name: str, new_name: str) -> bool:
    """Rename a GitHub repo and verify the result.

    The code tries multiple gh methods because Termux installations can have
    different gh versions. It also suppresses raw JSON output and logs it instead.
    """
    if not owner or not old_name or not new_name:
        return False
    if old_name.lower() == new_name.lower():
        return True

    print(f"[*] Renaming repository: {owner}/{old_name} -> {owner}/{new_name}")
    append_log("REPO_RENAME", f"Attempting {owner}/{old_name} -> {owner}/{new_name}")

    attempts = [
        ["gh", "api", "-X", "PATCH", f"repos/{owner}/{old_name}", "-F", f"name={new_name}"],
        ["gh", "api", "--method", "PATCH", f"repos/{owner}/{old_name}", "-F", f"name={new_name}"],
        ["gh", "repo", "rename", new_name, "--repo", f"{owner}/{old_name}"],
    ]

    for cmd in attempts:
        rc, out = run_rc(cmd, capture=True)
        append_log("REPO_RENAME_ATTEMPT", f"rc={rc} | {command_to_text(cmd)}\n{out}")
        if rc == 0:
            break
        if out:
            # Only show short errors, not giant repository JSON.
            short = out.strip().splitlines()[-1][:250]
            if short:
                print(f"[!] Rename attempt failed: {short}")

    # GitHub can take a moment to update names/redirects.
    for _ in range(12):
        time.sleep(0.8)
        actual_new = repo_actual_name(owner, new_name)
        if actual_new.lower() == new_name.lower():
            # If querying the old name now redirects to new_name, that is success.
            actual_old = repo_actual_name(owner, old_name)
            if not actual_old or actual_old.lower() != old_name.lower():
                print(f"[✓] Repository renamed: {owner}/{old_name} -> {owner}/{new_name}")
                return True
            # If both exist with exact names, rename did not happen.
        
    print(f"[!] Repository rename verification failed: {owner}/{old_name} -> {owner}/{new_name}")
    print("    Open the log file for the exact GitHub CLI/API error.")
    return False

def legacy_repo_to_migrate(owner: str) -> str:
    """Find a true legacy repo. Redirects to the official name are ignored."""
    for old_name in LEGACY_REPO_NAMES:
        if not old_name or old_name.lower() == REPO_NAME.lower():
            continue
        actual = repo_actual_name(owner, old_name)
        if actual and actual.lower() == old_name.lower():
            return old_name
    return ""

def safe_repo_fragment(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(name or "repo")).strip("_") or "repo"

def clone_legacy_repo_for_migration(owner: str, old_name: str) -> Path:
    """Clone the old repo into Termux HOME so its files can be preserved before deletion."""
    base = Path.home() / ".dead_mans_switch_repo_migration"
    try:
        shutil.rmtree(base, ignore_errors=True)
    except Exception:
        pass
    base.mkdir(parents=True, exist_ok=True)
    clone_dir = base / f"{safe_repo_fragment(old_name)}_{time.strftime('%Y%m%d_%H%M%S')}"

    print(f"[*] Backing up old repository files before deletion: {owner}/{old_name}")
    attempts = [
        ["gh", "repo", "clone", f"{owner}/{old_name}", str(clone_dir), "--", "--depth", "1"],
        ["git", "clone", "--depth", "1", f"https://github.com/{owner}/{old_name}.git", str(clone_dir)],
    ]
    for cmd in attempts:
        rc, out = run_rc(cmd, capture=True)
        append_log("LEGACY_CLONE_ATTEMPT", f"rc={rc} | {command_to_text(cmd)}\n{out}")
        if rc == 0 and clone_dir.exists():
            print(f"[✓] Old repository cloned locally for migration: {clone_dir}")
            return clone_dir
    print("[!] Could not clone old repository. Continuing with local folder files only.")
    return Path("")

def zip_legacy_clone_to_history(clone_dir: Path, old_name: str) -> str:
    """Save a zip backup of the old repository inside History/."""
    if not clone_dir or not clone_dir.exists():
        return ""
    try:
        ensure_folder()
        hist_dir = previous_history_dir()
        hist_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        zip_path = hist_dir / f"Legacy_{safe_repo_fragment(old_name)}_Before_Delete_{stamp}.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            wrote = False
            for p in clone_dir.rglob("*"):
                if p.is_dir():
                    continue
                try:
                    rel = p.relative_to(clone_dir).as_posix()
                except Exception:
                    continue
                if rel.startswith(".git/") or "/.git/" in rel:
                    continue
                try:
                    zf.write(p, rel)
                    wrote = True
                except Exception:
                    pass
            if not wrote:
                zf.writestr("EMPTY_OLD_REPOSITORY.txt", f"No files were found in {old_name} before deletion.\n")
            zf.writestr("MIGRATION_INFO.txt", f"Old repository: {old_name}\nNew repository: {REPO_NAME}\nCreated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(f"[✓] Old repository backup saved: {zip_path.relative_to(LOCAL_DIR).as_posix()}")
        return zip_path.relative_to(LOCAL_DIR).as_posix()
    except Exception:
        log_exception("zip_legacy_clone_to_history")
        print("[!] Could not create old repository backup zip. Continuing.")
        return ""

def copy_missing_legacy_files_to_local(clone_dir: Path) -> int:
    """Copy files that exist only in the old repo into the local folder before new upload."""
    if not clone_dir or not clone_dir.exists():
        return 0
    copied = 0
    for src in clone_dir.rglob("*"):
        if src.is_dir():
            continue
        try:
            rel = src.relative_to(clone_dir).as_posix()
        except Exception:
            continue
        if rel.startswith(".git/") or "/.git/" in rel:
            continue
        # Never overwrite the current script or current local files. This preserves phone-side changes.
        dest = LOCAL_DIR / rel
        if dest.exists():
            continue
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            copied += 1
        except Exception:
            pass
    if copied:
        print(f"[✓] Copied {copied} missing file(s) from old repository into the local folder.")
    return copied

def wipe_legacy_repo_files_before_delete(clone_dir: Path, old_name: str) -> None:
    """Best-effort cleanup commit on the old repo before deleting it."""
    if not clone_dir or not clone_dir.exists() or not (clone_dir / ".git").exists():
        return
    print(f"[*] Cleaning files from old repository before deletion: {old_name}")
    try:
        run(["git", "config", "user.name", "dead-mans-switch-termux"], cwd=str(clone_dir), check=False)
        run(["git", "config", "user.email", "dead-mans-switch@localhost"], cwd=str(clone_dir), check=False)
        run(["git", "rm", "-r", "--ignore-unmatch", "."], cwd=str(clone_dir), check=False)
        (clone_dir / ".gitkeep").write_text(f"Old repository cleaned before migration to {REPO_NAME}.\n", encoding="utf-8")
        run(["git", "add", "-A"], cwd=str(clone_dir), check=False)
        rc, out = run_rc(["git", "commit", "-m", f"Clean old repository before migration to {REPO_NAME}"], cwd=str(clone_dir), capture=True)
        append_log("LEGACY_WIPE_COMMIT", f"rc={rc}\n{out}")
        # Push even if commit said nothing changed; it is harmless and verifies access.
        rc, out = run_rc(["git", "push", "origin", "HEAD", "--force-with-lease"], cwd=str(clone_dir), capture=True)
        append_log("LEGACY_WIPE_PUSH", f"rc={rc}\n{out}")
        if rc == 0:
            print("[✓] Old repository files cleaned before deletion.")
        else:
            print("[!] Could not push old-repo cleanup commit. Continuing to delete old repo.")
    except Exception:
        log_exception("wipe_legacy_repo_files_before_delete")
        print("[!] Old-repo cleanup failed. Continuing to delete old repo.")

def delete_legacy_repo_named(owner: str, old_name: str) -> bool:
    """Delete a specific old repo name without touching REPO_NAME."""
    if not owner or not old_name:
        return False
    print(f"[*] Deleting old repository: {owner}/{old_name}")
    ensure_scopes(["delete_repo", "repo"])
    attempts = [
        ["gh", "repo", "delete", f"{owner}/{old_name}", "--yes"],
        ["gh", "api", "-X", "DELETE", f"repos/{owner}/{old_name}"],
    ]
    for cmd in attempts:
        rc, out = run_rc(cmd, capture=True)
        append_log("LEGACY_DELETE_ATTEMPT", f"rc={rc} | {command_to_text(cmd)}\n{out}")
        time.sleep(1)
        if not repo_exists_named(owner, old_name, exact=True):
            print(f"[✓] Old repository deleted: {owner}/{old_name}")
            return True
    print(f"[!] Could not delete old repository: {owner}/{old_name}")
    print("    Check GitHub permissions and the log file for the exact error.")
    return False

def rename_legacy_repo_if_needed(owner: str):
    """
    Migrate legacy repo names by deletion/recreation instead of GitHub rename.

    The user requested this flow because GitHub rename was unreliable on Termux:
      1) detect old repository name on GitHub
      2) back up/copy old repo files
      3) delete files from the old repo as best effort
      4) delete the old repo
      5) allow/create/use the official repo name: REPO_NAME

    Returns:
      True  -> official repo exists after migration/check
      None  -> no official repo exists yet; caller can create it
      False -> old repo existed but deletion failed, so caller should stop
    """
    if not owner:
        return None

    old_name = legacy_repo_to_migrate(owner)
    target_exists = repo_exists_named(owner, REPO_NAME, exact=True)

    if not old_name:
        return True if target_exists else None

    print(f"[*] Old repository detected: {owner}/{old_name}")
    print(f"[*] Migration mode: delete old repo and use/create {owner}/{REPO_NAME}")

    clone_dir = clone_legacy_repo_for_migration(owner, old_name)
    if clone_dir and clone_dir.exists():
        zip_legacy_clone_to_history(clone_dir, old_name)
        copy_missing_legacy_files_to_local(clone_dir)
        wipe_legacy_repo_files_before_delete(clone_dir, old_name)

    if not delete_legacy_repo_named(owner, old_name):
        print("[!] Migration stopped because the old repository could not be deleted.")
        print("    I will not create a duplicate repo while the old one still exists.")
        return False

    try:
        if clone_dir and clone_dir.exists():
            shutil.rmtree(clone_dir.parent, ignore_errors=True)
    except Exception:
        pass

    if repo_exists_named(owner, REPO_NAME, exact=True):
        print(f"[✓] Official repository already exists: {owner}/{REPO_NAME}")
        return True

    print(f"[*] Old repo removed. The official repo will now be created: {owner}/{REPO_NAME}")
    return None

def repo_exists(owner):
    enforce_final_repo_name_runtime()
    state = rename_legacy_repo_if_needed(owner)
    return state is True

def get_default_branch(owner):
    enforce_final_repo_name_runtime()
    rename_legacy_repo_if_needed(owner)
    out = run(["gh", "api", f"repos/{owner}/{REPO_NAME}", "--jq", ".default_branch"], capture=True, check=False)
    return (out or "main").strip() or "main"

def ensure_repo_created(owner, visibility: str):
    enforce_final_repo_name_runtime()
    visibility = (visibility or "public").lower().strip()
    if visibility not in ("public", "private"):
        visibility = "public"
    ensure_repo_scope()
    repo_state = rename_legacy_repo_if_needed(owner)
    if repo_state is False:
        raise RuntimeError("Old repository was detected, but it could not be renamed. New repository creation was stopped to avoid duplicates.")
    if repo_state is None:
        print(f"[*] Creating {visibility.upper()} repo: {owner}/{REPO_NAME}")
        private_flag = "true" if visibility == "private" else "false"
        run(["gh", "api", "-X", "POST", "user/repos",
             "-f", f"name={REPO_NAME}",
             "-f", f"private={private_flag}",
             "-f", "auto_init=false"], check=True)
        print("[*] Repo created.")
    else:
        print(f"[*] Repo exists: {owner}/{REPO_NAME}")
    private_flag = "true" if visibility == "private" else "false"
    run(["gh", "api", "-X", "PATCH", f"repos/{owner}/{REPO_NAME}", "-f", f"private={private_flag}"], check=False, capture=True)
    edit_args = ["gh", "repo", "edit", f"{owner}/{REPO_NAME}", "--visibility", visibility, "--accept-visibility-change-consequences"]
    run(edit_args, check=False, capture=True)

def init_or_use_git_repo():
    ensure_git_safe_directory()
    ensure_git_identity()
    if not (LOCAL_DIR / ".git").exists():
        print("[*] Initializing local git repo...")
        run(["git", "init"], cwd=str(LOCAL_DIR))
        run(["git", "config", "user.name", "dead-mans-switch-termux"], cwd=str(LOCAL_DIR), check=False)
        run(["git", "config", "user.email", "dead-mans-switch@localhost"], cwd=str(LOCAL_DIR), check=False)

def set_remote(owner):
    enforce_final_repo_name_runtime()
    remote_url = f"https://github.com/{owner}/{REPO_NAME}.git"
    remotes = run(["git", "remote"], cwd=str(LOCAL_DIR), capture=True, check=False)
    if "origin" in remotes.split():
        run(["git", "remote", "set-url", "origin", remote_url], cwd=str(LOCAL_DIR), check=False)
    else:
        run(["git", "remote", "add", "origin", remote_url], cwd=str(LOCAL_DIR), check=False)

def ensure_git_safe_directory():
    try:
        paths = {str(LOCAL_DIR), str(LOCAL_DIR.resolve())}
        alt1 = Path("/storage/emulated/0/Download") / APP_NAME
        alt2 = Path("/sdcard/Download") / APP_NAME
        for p in (alt1, alt2):
            if p.exists():
                paths.add(str(p))
                try:
                    paths.add(str(p.resolve()))
                except Exception:
                    pass
        for p in sorted(paths):
            run(["git", "config", "--global", "--add", "safe.directory", p], check=False)
    except Exception:
        pass

def ensure_git_identity():
    try:
        name = run(["git", "config", "--global", "user.name"], capture=True, check=False).strip()
        email = run(["git", "config", "--global", "user.email"], capture=True, check=False).strip()
        if not name:
            run(["git", "config", "--global", "user.name", "dead-mans-switch-termux"], check=False)
        if not email:
            run(["git", "config", "--global", "user.email", "dead-mans-switch@localhost"], check=False)
        if (LOCAL_DIR / ".git").exists():
            run(["git", "config", "user.name", "dead-mans-switch-termux"], cwd=str(LOCAL_DIR), check=False)
            run(["git", "config", "user.email", "dead-mans-switch@localhost"], cwd=str(LOCAL_DIR), check=False)
    except Exception:
        pass

def remote_branch_exists(branch: str) -> bool:
    if not branch:
        return False
    rc, out = run_rc(["git", "ls-remote", "--heads", "origin", branch], cwd=str(LOCAL_DIR), capture=True)
    return rc == 0 and bool((out or "").strip())

def sync_local_repo_with_remote(owner):
    default_branch = get_default_branch(owner) or "main"
    run(["git", "fetch", "origin", "--prune"], cwd=str(LOCAL_DIR), check=False)
    branch_to_track = None
    if remote_branch_exists(default_branch):
        branch_to_track = default_branch
    elif default_branch != "main" and remote_branch_exists("main"):
        branch_to_track = "main"
    elif default_branch != "master" and remote_branch_exists("master"):
        branch_to_track = "master"
    if branch_to_track:
        print(f"[*] Syncing local repo to remote branch: {branch_to_track}")
        run(["git", "checkout", "-B", branch_to_track, f"origin/{branch_to_track}"], cwd=str(LOCAL_DIR), check=False)
        if branch_to_track != default_branch:
            run(["git", "branch", "-M", default_branch], cwd=str(LOCAL_DIR), check=False)
    else:
        run(["git", "checkout", "-B", default_branch], cwd=str(LOCAL_DIR), check=False)

def ensure_gitignore():
    """Create/update .gitignore without blocking emergency help_data uploads."""
    gi = LOCAL_DIR / ".gitignore"
    default_lines = [".DS_Store", "Thumbs.db", "*.log", "__pycache__/", "*.pyc"]
    existing_lines = []
    if gi.exists():
        try:
            existing_lines = gi.read_text(encoding="utf-8").splitlines()
        except Exception:
            existing_lines = []

    cleaned = []
    for line in existing_lines:
        stripped = line.strip()
        # Old versions ignored help_data/, which broke the emergency upload feature.
        if stripped in {"help_data/", "/help_data/", "help_data", "/help_data"}:
            continue
        if line not in cleaned:
            cleaned.append(line)

    for line in default_lines:
        if line not in cleaned:
            cleaned.append(line)

    gi.write_text("\n".join(cleaned).rstrip() + "\n", encoding="utf-8")

def repo_url_for(owner: str) -> str:
    owner = (owner or "").strip()
    if not owner:
        return ""
    return f"https://github.com/{owner}/{REPO_NAME}"

def expected_pages_url(owner: str) -> str:
    owner = (owner or "").strip()
    if not owner:
        return ""
    return f"https://{owner}.github.io/{REPO_NAME}/"

def get_known_or_expected_pages_url(owner: str) -> str:
    """Return the configured GitHub Pages URL if it exists, otherwise the standard expected URL.
    This never returns raw GitHub API error JSON such as {"message":"Not Found"}.
    """
    owner = (owner or "").strip()
    if not owner:
        return ""
    rc, out = run_rc(["gh", "api", f"repos/{owner}/{REPO_NAME}/pages", "--jq", ".html_url"], capture=True)
    known = (out or "").strip() if rc == 0 else ""
    if known.startswith("http"):
        return known
    return expected_pages_url(owner)

def print_github_pages_manual_setup_guide(owner: str):
    """Show the user exactly how to enable GitHub Pages before emergency capture starts."""
    owner = (owner or "").strip()
    repo_url = repo_url_for(owner)
    pages_url = expected_pages_url(owner)
    settings_url = f"https://github.com/{owner}/{REPO_NAME}/settings/pages" if owner else "GitHub repository Settings > Pages"
    print("\n=== GitHub Pages setup before I Need Help starts ===")
    print("GitHub may require Pages to be enabled manually from the website/app.")
    print("Do this once before starting emergency capture:")
    print("  1) Open the repository settings:")
    print(f"     {settings_url}")
    print("  2) Go to: Settings > Pages")
    print("  3) Source: Deploy from a branch")
    print("  4) Branch: main")
    print("  5) Folder: / (root)")
    print("  6) Tap Save")
    print("  7) Turn ON Enforce HTTPS if GitHub shows that option")
    print("  8) Wait until GitHub says the site is published")
    print(f"\nExpected website link: {pages_url}")
    if repo_url:
        print(f"Repository link: {repo_url}")
    if which("termux-open-url") and settings_url.startswith("http"):
        open_now = input("\nOpen GitHub Pages settings in browser now? (y/N): ").strip().lower()
        if open_now == "y":
            run(["termux-open-url", settings_url], check=False)
    print("\nOnly continue after Pages is enabled or if you accept that the website may show 404 until you enable it.")

def build_readme_text(owner: str = "", pages_url: str = "") -> str:
    owner = (owner or "").strip()
    repo_url = repo_url_for(owner)
    pages_url = (pages_url or expected_pages_url(owner) or "Not published yet").strip()
    generated_at = time.strftime("%Y-%m-%d %H:%M:%S")
    link_section = f"""# Dead Man's Switch

**GitHub Pages website:** {pages_url}
**Repository:** {repo_url or 'Unknown until GitHub login is detected'}
**Last README update:** {generated_at}

This repository is generated and maintained by `Dead Man's Switch.py`. The GitHub Pages website is the main emergency-friendly view: it organizes profile details, photos, audio, locations, timeline entries, documents, and all uploaded files into simple static pages.

If the GitHub Pages website link shows a 404, enable GitHub Pages manually in the repository settings: Settings → Pages → Source: Deploy from a branch → Branch: main → Folder: / (root) → Save → Enforce HTTPS.

## What to open first

1. Open the GitHub Pages website above.
2. Start with `Person Profile` to identify the person and read emergency details.
3. Check `Locations` for saved GPS/network location files and map links.
4. Check `Photo Gallery` and `Audio` for emergency captures.
5. Check `Timeline` to understand what happened by date and time.
6. Check `All Files` for every uploaded file that is not part of the website itself.
7. Read `Emergency Info` for guidance and warnings.

## Important safety notes

- Emergency mode can make this repository **public** so trusted contacts can access it.
- Do **not** store passwords, bank/card data, crypto seed phrases, private keys, or account secrets here.
- This project is not a replacement for emergency services. If someone may be in danger, contact local emergency services immediately.
- The website is static. Refresh it later if emergency mode is still uploading new data.

## Local folder used by the script

`{LOCAL_DIR}`

## Generated website pages

- `index.html` — dashboard
- `Pages/profile.html` — personal identification/profile
- `Pages/gallery.html` — photos grouped from uploaded files
- `Pages/videos.html` — videos grouped from uploaded files
- `Pages/audio.html` — audio recordings
- `Pages/locations.html` — location files and map links when coordinates exist
- `Pages/timeline.html` — files organized by date/time
- `Pages/files.html` — full file archive
- `Pages/emergency.html` — emergency guidance

## Previous History

Before normal repository publishes, the previous repository/local snapshot is packed into a timestamped zip inside `History/`. The script then cleans Git tracking and uploads the new current snapshot, while keeping those history zips. Local phone files are **not** deleted by this cleanup; only the Git repository index is refreshed.

## Repository structure

- `index.html`, `style.css`, `scripts.js`, `README.md` stay in the repository root.
- `Pages/` contains every website page except the main `index.html`.
- `Assets/Photos/`, `Assets/Videos/`, `Assets/Recordings/`, `Assets/Locations/`, `Assets/Profile/`, `Assets/Sessions/`, and `Assets/Other/` hold the uploaded data.
- `History/` contains previous-version zip snapshots.

---

"""
    return link_section + README_TEXT

def ensure_readme(owner: str = "", pages_url: str = ""):
    rm = LOCAL_DIR / "README.md"
    rm.write_text(build_readme_text(owner, pages_url), encoding="utf-8")
    return rm

def commit_readme_with_pages_url(owner: str, pages_url: str) -> None:
    """Best-effort: make README.md contain the final GitHub Pages URL and push that small update."""
    try:
        if not (LOCAL_DIR / ".git").exists():
            return
        ensure_readme(owner, pages_url)
        run(["git", "reset"], cwd=str(LOCAL_DIR), check=False)
        stage_paths(["README.md"], force=True)
        if commit_staged("Update README with GitHub Pages link"):
            push_current()
    except Exception as e:
        print(f"[!] Could not update README with final Pages link: {e}")

def current_branch():
    b = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(LOCAL_DIR), capture=True, check=False)
    return "main" if not b or b == "HEAD" else b

def ensure_main_branch():
    b = current_branch()
    if b == "master":
        run(["git", "branch", "-M", "main"], cwd=str(LOCAL_DIR), check=False)

def staged_has_changes() -> bool:
    out = run(["git", "diff", "--cached", "--name-only"], cwd=str(LOCAL_DIR), capture=True, check=False)
    return bool((out or "").strip())

def commit_staged(message: str) -> bool:
    if not staged_has_changes():
        return False
    rc, out = run_rc(["git", "commit", "-m", message], cwd=str(LOCAL_DIR), capture=True)
    if rc != 0:
        print("[!] Git commit failed.")
        if out:
            print(out)
        return False
    return True

def push_current() -> bool:
    ensure_main_branch()
    head = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(LOCAL_DIR), capture=True, check=False)
    if not head or head == "HEAD":
        run(["git", "checkout", "-B", "main"], cwd=str(LOCAL_DIR), check=False)
        head = "main"
    print("[*] Pushing to GitHub...")
    rc, out = run_rc(["git", "push", "-u", "origin", head], cwd=str(LOCAL_DIR), capture=True)
    if rc == 0:
        return True

    out = out or ""
    non_fast_forward = ("non-fast-forward" in out.lower() or "fetch first" in out.lower() or "rejected" in out.lower())
    if non_fast_forward:
        print("[!] Remote branch is ahead. Fetching remote state and retrying safely with --force-with-lease...")
        run(["git", "fetch", "origin", "--prune"], cwd=str(LOCAL_DIR), check=False)
        rc2, out2 = run_rc(["git", "push", "--force-with-lease", "-u", "origin", head], cwd=str(LOCAL_DIR), capture=True)
        if rc2 == 0:
            print("[✓] Push succeeded after safe retry.")
            return True
        print("[!] Git push retry failed.")
        if out2:
            print(out2)
        return False

    print("[!] Git push failed.")
    if out:
        print(out)
    return False

def list_local_files() -> List[Tuple[str, int]]:
    items: List[Tuple[str, int]] = []
    for p in LOCAL_DIR.rglob("*"):
        if p.is_dir():
            continue
        if ".git" in p.parts:
            continue
        try:
            size = p.stat().st_size
        except OSError:
            continue
        rel = p.relative_to(LOCAL_DIR).as_posix()
        items.append((rel, size))
    items.sort(key=lambda x: x[0])
    return items

def fetch_remote_paths(owner) -> Set[str]:
    enforce_final_repo_name_runtime()
    if not repo_exists(owner):
        return set()
    default_branch = get_default_branch(owner)
    out = run(["gh", "api", f"repos/{owner}/{REPO_NAME}/git/trees/{default_branch}", "-f", "recursive=1"],
              capture=True, check=False)
    if not out:
        return set()
    try:
        data = json.loads(out)
        paths = set()
        for item in data.get("tree", []):
            if item.get("type") == "blob" and "path" in item:
                paths.add(item["path"])
        return paths
    except Exception:
        return set()

def make_batches(candidates: List[Tuple[str, int]], max_bytes: int) -> List[List[Tuple[str, int]]]:
    batches: List[List[Tuple[str, int]]] = []
    current: List[Tuple[str, int]] = []
    total = 0
    for rel, size in candidates:
        if size > MAX_FILE_BYTES:
            continue
        if not current:
            current = [(rel, size)]
            total = size
            continue
        if total + size <= max_bytes:
            current.append((rel, size))
            total += size
        else:
            batches.append(current)
            current = [(rel, size)]
            total = size
    if current:
        batches.append(current)
    return batches

def report_skips(skipped: List[Tuple[str, int]]):
    if not skipped:
        return
    print("\n[!] Skipped files (too large):")
    for rel, size in skipped:
        mb = size / (1024 * 1024)
        print(f"    - {rel} ({mb:.2f} MB)")
    print("")

def stage_paths(paths: List[str], force: bool = False):
    for rel in paths:
        cmd = ["git", "add"]
        if force:
            cmd.append("-f")
        cmd.extend(["--", rel])
        run(cmd, cwd=str(LOCAL_DIR), check=False)


def previous_history_dir() -> Path:
    return LOCAL_DIR / PREVIOUS_HISTORY_DIR_NAME

def is_previous_history_file(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    return (
        rel == PREVIOUS_HISTORY_DIR_NAME or rel.startswith(PREVIOUS_HISTORY_DIR_NAME + "/")
        or rel == LEGACY_PREVIOUS_HISTORY_DIR_NAME or rel.startswith(LEGACY_PREVIOUS_HISTORY_DIR_NAME + "/")
    )


STRUCTURE_DIRS = [
    f"{SITE_ASSETS_DIR_NAME}/Photos",
    f"{SITE_ASSETS_DIR_NAME}/Videos",
    f"{SITE_ASSETS_DIR_NAME}/Recordings",
    f"{SITE_ASSETS_DIR_NAME}/Locations",
    f"{SITE_ASSETS_DIR_NAME}/Sessions",
    f"{SITE_ASSETS_DIR_NAME}/Profile",
    f"{SITE_ASSETS_DIR_NAME}/Other",
    PREVIOUS_HISTORY_DIR_NAME,
    PAGES_DIR_NAME,
]

ROOT_ALLOWED_FILES = {"index.html", SITE_CSS_NAME, SITE_JS_NAME, "README.md"}

OLD_GENERATED_ROOT_PAGES = {
    "profile.html", "gallery.html", "videos.html", "audio.html", "locations.html",
    "timeline.html", "files.html", "emergency.html", SITE_MANIFEST_NAME,
}

def ensure_repository_structure() -> None:
    """Create the clean repository layout requested by the user."""
    ensure_folder()
    for rel in STRUCTURE_DIRS:
        d = LOCAL_DIR / rel
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.write_text("Keeps this repository folder visible.\n", encoding="utf-8")

def unique_dest_path(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    i = 2
    while True:
        candidate = dest.with_name(f"{stem}_{i}{suffix}")
        if not candidate.exists():
            return candidate
        i += 1

def structured_folder_for_rel(rel: str) -> str:
    kind = file_kind(rel)
    if kind == "Photo":
        return f"{SITE_ASSETS_DIR_NAME}/Photos"
    if kind == "Video":
        return f"{SITE_ASSETS_DIR_NAME}/Videos"
    if kind == "Audio":
        return f"{SITE_ASSETS_DIR_NAME}/Recordings"
    if kind == "Location":
        return f"{SITE_ASSETS_DIR_NAME}/Locations"
    if kind == "Emergency session":
        return f"{SITE_ASSETS_DIR_NAME}/Sessions"
    if kind == "Personal profile":
        return f"{SITE_ASSETS_DIR_NAME}/Profile"
    return f"{SITE_ASSETS_DIR_NAME}/Other"

def organize_local_repository_structure() -> None:
    """Move script-managed files into a clear repo structure.

    Root: index.html, style.css, scripts.js, README.md
    Assets/: Photos, Videos, Recordings, Locations, Sessions, Profile, Other
    History/: previous snapshot zips
    Pages/: all pages except index.html
    """
    ensure_repository_structure()

    # Move old history folder zips into the new History/ folder.
    legacy_hist = LOCAL_DIR / LEGACY_PREVIOUS_HISTORY_DIR_NAME
    if legacy_hist.exists() and legacy_hist.is_dir():
        for path in legacy_hist.rglob("*"):
            if path.is_file():
                try:
                    dest = unique_dest_path(previous_history_dir() / path.name)
                    shutil.move(str(path), str(dest))
                except Exception:
                    pass

    # Remove old generated root pages/assets from earlier versions. They are rebuilt in the new structure.
    for old in OLD_GENERATED_ROOT_PAGES:
        path = LOCAL_DIR / old
        if path.exists() and path.is_file():
            try:
                path.unlink()
            except Exception:
                pass
    legacy_assets = LOCAL_DIR / "assets"
    if legacy_assets.exists() and legacy_assets.is_dir():
        for old in [legacy_assets / "site.css", legacy_assets / "site.js"]:
            if old.exists() and old.is_file():
                try:
                    old.unlink()
                except Exception:
                    pass

    # Move old personal details from root into Assets/Profile.
    for legacy, current in [
        (legacy_personal_details_json_path(), personal_details_json_path()),
        (legacy_personal_details_txt_path(), personal_details_txt_path()),
    ]:
        if legacy.exists() and legacy.is_file():
            try:
                current.parent.mkdir(parents=True, exist_ok=True)
                if not current.exists():
                    shutil.copy2(str(legacy), str(current))
                legacy.unlink()
            except Exception:
                pass

    # Organize any files that are outside the requested structure into Assets/*.
    protected_prefixes = (f"{SITE_ASSETS_DIR_NAME}/", f"{PAGES_DIR_NAME}/", f"{PREVIOUS_HISTORY_DIR_NAME}/", ".git/")
    for path in list(LOCAL_DIR.rglob("*")):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(LOCAL_DIR).as_posix()
        except Exception:
            continue
        if rel in ROOT_ALLOWED_FILES or rel == ".gitignore":
            continue
        if rel.startswith(protected_prefixes):
            continue
        if rel.startswith(f"{LEGACY_PREVIOUS_HISTORY_DIR_NAME}/"):
            continue
        if "/.git/" in rel or rel.startswith(".git/"):
            continue
        # Keep this script out of the public snapshot if somebody placed it in the folder.
        if Path(rel).name.lower() in {"dead switch.py", "dead_switch.py"}:
            dest_folder = f"{SITE_ASSETS_DIR_NAME}/Other"
        else:
            dest_folder = structured_folder_for_rel(rel)
        safe_name = rel.replace("/", "__")
        dest = unique_dest_path(LOCAL_DIR / dest_folder / safe_name)
        try:
            shutil.move(str(path), str(dest))
        except Exception:
            pass

def make_previous_history_zip(reason: str = "repository update") -> str:
    """Create a timestamped zip of the current local snapshot without nesting old history zips."""
    ensure_folder()
    organize_local_repository_structure()
    hist_dir = previous_history_dir()
    hist_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    safe_reason = re.sub(r"[^A-Za-z0-9_-]+", "_", reason.strip().lower()).strip("_") or "update"
    zip_path = hist_dir / f"Dead_Mans_Switch_Previous_{stamp}_{safe_reason}.zip"
    counter = 2
    while zip_path.exists():
        zip_path = hist_dir / f"Dead_Mans_Switch_Previous_{stamp}_{safe_reason}_{counter}.zip"
        counter += 1

    files_to_zip: List[Path] = []
    for path in LOCAL_DIR.rglob("*"):
        if path.is_dir():
            continue
        try:
            rel = path.relative_to(LOCAL_DIR).as_posix()
        except Exception:
            continue
        if rel.startswith(".git/") or "/.git/" in rel:
            continue
        if is_previous_history_file(rel):
            continue
        if path == zip_path:
            continue
        files_to_zip.append(path)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        if files_to_zip:
            for path in sorted(files_to_zip, key=lambda x: x.relative_to(LOCAL_DIR).as_posix()):
                rel = path.relative_to(LOCAL_DIR).as_posix()
                try:
                    zf.write(path, rel)
                except Exception:
                    pass
        else:
            zf.writestr("EMPTY_SNAPSHOT.txt", "No local files existed before this update.\n")
        zf.writestr("SNAPSHOT_INFO.txt", f"Dead Man's Switch previous snapshot\nCreated: {time.strftime('%Y-%m-%d %H:%M:%S')}\nReason: {reason}\n")

    rel_zip = zip_path.relative_to(LOCAL_DIR).as_posix()
    try:
        size = zip_path.stat().st_size
        print(f"[✓] Previous version zipped: {rel_zip} ({human_size(size)})")
        if size > MAX_FILE_BYTES:
            print(f"[!] History zip is larger than {MAX_FILE_BYTES/(1024*1024):.0f}MB and may be skipped by upload batching.")
    except Exception:
        print(f"[✓] Previous version zipped: {rel_zip}")
    return rel_zip

def history_zip_rels_under_limit() -> List[str]:
    rels: List[str] = []
    hist_dir = previous_history_dir()
    if not hist_dir.exists():
        return rels
    for path in sorted(hist_dir.rglob("*.zip")):
        try:
            rel = path.relative_to(LOCAL_DIR).as_posix()
            if path.stat().st_size <= MAX_FILE_BYTES:
                rels.append(rel)
            else:
                print(f"[!] Skipping oversized history zip: {rel} ({human_size(path.stat().st_size)})")
        except Exception:
            pass
    return rels

def archive_previous_version_and_clean_repo(owner: str, reason: str = "repository update") -> str:
    """Push a history-only cleanup commit, preserving local files while clearing old remote contents."""
    if not owner:
        return ""
    remote_paths = fetch_remote_paths(owner)
    rel_zip = make_previous_history_zip(reason)
    run(["git", "reset"], cwd=str(LOCAL_DIR), check=False)
    # Remove every tracked file from the Git index, but keep local phone files untouched.
    run(["git", "rm", "-r", "--cached", "--ignore-unmatch", "."], cwd=str(LOCAL_DIR), check=False)
    history_rels = history_zip_rels_under_limit()
    if history_rels:
        stage_paths(history_rels, force=True)
    if remote_paths or staged_has_changes():
        if commit_staged(f"Archive previous version before {reason}"):
            push_current()
        else:
            print("[*] No repository cleanup/history commit was needed.")
    return rel_zip

def build_current_repository_snapshot(owner: str, pages_url: str, reason: str) -> List[Tuple[str, int]]:
    """Generate README/site, clean Git index, and return current upload candidates."""
    organize_local_repository_structure()
    ensure_readme(owner, pages_url)
    generate_static_website(owner, pages_url)
    run(["git", "reset"], cwd=str(LOCAL_DIR), check=False)
    run(["git", "rm", "-r", "--cached", "--ignore-unmatch", "."], cwd=str(LOCAL_DIR), check=False)
    local_items = list_local_files()
    print(f"[*] Current local snapshot files detected: {len(local_items)}")
    skipped_large = [(rel, size) for rel, size in local_items if size > MAX_FILE_BYTES]
    report_skips(skipped_large)
    candidates = [(rel, size) for rel, size in local_items if size <= MAX_FILE_BYTES]
    if not candidates:
        print("[!] No files under the upload limit were found.")
    else:
        print(f"[*] Prepared clean repository snapshot for: {reason}")
    return candidates

def create_switch_only_new():
    print("\n=== Create / Update Switch Repository ===")
    ensure_folder()
    ensure_core_dependencies(include_termux_api=False)
    ensure_logged_in()
    ensure_repo_scope()
    owner = gh_user()
    if not owner:
        print("[!] Could not detect GitHub username.")
        return
    ensure_repo_created(owner, get_visibility())
    init_or_use_git_repo()
    set_remote(owner)
    ensure_gitignore()
    sync_local_repo_with_remote(owner)

    # Preserve the previous repository/local snapshot before publishing the new one.
    archive_previous_version_and_clean_repo(owner, "normal update")

    pages_url = get_known_or_expected_pages_url(owner)
    candidates = build_current_repository_snapshot(owner, pages_url, "normal update")
    if not candidates:
        return
    batches = make_batches(candidates, MAX_BATCH_BYTES)
    print(f"[*] Uploading clean snapshot: {len(candidates)} file(s) in {len(batches)} batch(es).")
    uploaded = 0
    for i, batch in enumerate(batches, start=1):
        batch_paths = [rel for rel, _ in batch]
        batch_bytes = sum(size for _, size in batch)
        print(f"\n[*] Batch {i}/{len(batches)}: {len(batch_paths)} file(s), {batch_bytes/(1024*1024):.2f} MB")
        stage_paths(batch_paths, force=True)
        if not commit_staged(f"Publish current Dead Man's Switch snapshot batch {i}/{len(batches)}"):
            print("[*] Nothing changed in this batch.")
            continue
        if not push_current():
            print("[!] Stopping because push failed. Fix the issue and re-run.")
            return
        uploaded += len(batch_paths)
    pages_url = ensure_github_pages(owner, current_branch())
    print(f"\n[✓] Done. Published {uploaded} file(s). Repo: https://github.com/{owner}/{REPO_NAME}")
    print(f"[✓] Website: {pages_url}")

def overwrite_repository_batched():
    print("\n=== Force Full Repository Refresh ===")
    ensure_folder()
    ensure_core_dependencies(include_termux_api=False)
    ensure_logged_in()
    ensure_repo_scope()
    owner = gh_user()
    if not owner:
        print("[!] Could not detect GitHub username.")
        return
    ensure_repo_created(owner, get_visibility())
    init_or_use_git_repo()
    set_remote(owner)
    ensure_gitignore()
    sync_local_repo_with_remote(owner)

    archive_previous_version_and_clean_repo(owner, "full refresh")

    pages_url = get_known_or_expected_pages_url(owner)
    candidates = build_current_repository_snapshot(owner, pages_url, "full refresh")
    if not candidates:
        return
    batches = make_batches(candidates, MAX_BATCH_BYTES)
    print(f"[*] Uploading refreshed snapshot: {len(candidates)} file(s) in {len(batches)} batch(es).")
    committed_any = False
    for i, batch in enumerate(batches, start=1):
        batch_paths = [rel for rel, _ in batch]
        batch_bytes = sum(size for _, size in batch)
        print(f"\n[*] Batch {i}/{len(batches)}: {len(batch_paths)} file(s), {batch_bytes/(1024*1024):.2f} MB")
        stage_paths(batch_paths, force=True)
        if commit_staged(f"Refresh current Dead Man's Switch snapshot batch {i}/{len(batches)}"):
            committed_any = True
            if not push_current():
                print("[!] Stopping because push failed. Fix the issue and re-run.")
                return
        else:
            print("[*] Nothing changed in this batch.")
    pages_url = ensure_github_pages(owner, current_branch())
    if committed_any:
        print(f"\n[✓] Done. Repo: https://github.com/{owner}/{REPO_NAME}")
    else:
        print("\n[*] No changes detected to upload after refresh.")
    print(f"[✓] Website: {pages_url}")

def wipe_repo_files(owner):
    print("[*] Wiping repository files (empty commit)...")
    ensure_git()
    init_or_use_git_repo()
    set_remote(owner)
    sync_local_repo_with_remote(owner)
    run(["git", "rm", "-r", "--ignore-unmatch", "."], cwd=str(LOCAL_DIR), check=False)
    ensure_readme(owner, expected_pages_url(owner))
    (LOCAL_DIR / ".gitkeep").write_text("Repo wiped by Dead Man's Switch.py\n", encoding="utf-8")
    run(["git", "add", "-A"], cwd=str(LOCAL_DIR), check=False)
    commit_staged("Wipe repository contents")
    run(["git", "push", "origin", "HEAD", "--force"], cwd=str(LOCAL_DIR), check=False)
    print("[*] Repo contents wiped (best effort).")

def ensure_delete_scope():
    print("[*] Ensuring delete permissions (delete_repo)...")
    ensure_scopes(["delete_repo", "repo"])

def delete_repo(owner):
    print(f"[*] Deleting repo: {owner}/{REPO_NAME}")
    ensure_delete_scope()
    rc = subprocess.run(["gh", "repo", "delete", f"{owner}/{REPO_NAME}", "--yes"],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).returncode
    if rc != 0:
        run(["gh", "api", "-X", "DELETE", f"repos/{owner}/{REPO_NAME}"], check=False)
    if repo_exists(owner):
        print("[!] Repo still exists.")
        print("    Try manually:")
        print("    gh auth refresh -h github.com -s delete_repo -s repo")
        print(f"    gh repo delete {owner}/{REPO_NAME} --yes")
    else:
        print("[✓] Repo deleted.")

def kill_switch():
    print("\n=== Kill Switch (Wipe + Delete Repo) ===")
    ensure_folder()
    ensure_core_dependencies(include_termux_api=False)
    ensure_logged_in()
    ensure_repo_scope()
    owner = gh_user()
    if not owner:
        print("[!] Could not detect GitHub username.")
        return
    if not repo_exists(owner):
        print(f"[*] Repo does not exist: {owner}/{REPO_NAME}")
        return
    try:
        wipe_repo_files(owner)
    except Exception:
        print("[!] Could not fully wipe files (continuing to delete repo anyway).")
    delete_repo(owner)

def create_notification():
    ensure_termux_api()
    if not which("termux-notification"):
        return
    script_path = os.path.abspath(__file__)
    python_bin = sys.executable or "python"
    create_cmd = f'{python_bin} "{script_path}" --create'
    help_cmd = f'{python_bin} "{script_path}" --i-need-help'
    run([
        "termux-notification",
        "--id", "dead_switch",
        "--title", "Dead Man's Switch",
        "--content", f"Choose an action (repo {get_visibility().upper()}):",
        "--button1", "Create/Update",
        "--button1-action", create_cmd,
        "--button2", "I Need Help",
        "--button2-action", help_cmd,
        "--ongoing"
    ], check=False)
    print("[✓] Notification created with Create/Update and I Need Help buttons.")
    print("    I Need Help still requires two visible Enter confirmations before activation.")

def ensure_termux_camera():
    if not which("termux-camera-photo"):
        ensure_termux_api()
        if not which("termux-camera-photo"):
            print("[!] termux-camera-photo not found. Please install Termux:API app and termux-api package.")
            return False
    return True

def ensure_termux_microphone():
    if not which("termux-microphone-record"):
        ensure_termux_api()
        if not which("termux-microphone-record"):
            print("[!] termux-microphone-record not found. Please install Termux:API app and termux-api package.")
            return False
    return True

def ensure_termux_location():
    if not which("termux-location"):
        ensure_termux_api()
        if not which("termux-location"):
            print("[!] termux-location not found. Please install Termux:API app and termux-api package.")
            return False
    return True

def capture_photo_cam(cam_id: int, output_path: Path) -> bool:
    try:
        cmd = ["termux-camera-photo"]
        if cam_id is not None:
            cmd.extend(["-c", str(cam_id)])
        cmd.append(str(output_path))
        rc, _ = run_rc(cmd, capture=True)
        return rc == 0 and output_path.exists() and output_path.stat().st_size > 0
    except Exception:
        return False


def video_capture_command() -> str:
    """Return an available Termux-compatible video capture command, if the device provides one.

    Standard Termux:API reliably provides termux-camera-photo, but video commands are not
    present on every setup. This is intentionally optional: if no command exists, emergency
    mode continues with photos, audio, and location instead of failing.
    """
    for cmd in ("termux-camera-video", "termux-camera-record", "termux-video-record"):
        if which(cmd):
            return cmd
    return ""

def ensure_termux_video() -> bool:
    cmd = video_capture_command()
    if cmd:
        return True
    # Best effort: install termux-api, then check again. Many Termux:API builds still will not
    # provide a video command, so absence is treated as unsupported rather than fatal.
    ensure_termux_api()
    if video_capture_command():
        return True
    print("[!] Video capture command not found on this Termux setup.")
    print("    Photos, audio, and location will continue. Video will be skipped unless a compatible command exists.")
    return False

def capture_video_cam(cam_id: int, duration_sec: int, output_path: Path) -> bool:
    """Best-effort short video capture for devices that expose a Termux video command.

    Termux camera video support is not universal, so this function tries a small set of
    common CLI shapes and returns False cleanly when unsupported.
    """
    cmd = video_capture_command()
    if not cmd:
        return False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    attempts = [
        [cmd, "-c", str(cam_id), "-l", str(duration_sec), str(output_path)],
        [cmd, "-c", str(cam_id), "-d", str(duration_sec), str(output_path)],
        [cmd, "-c", str(cam_id), "-o", str(output_path), "-l", str(duration_sec)],
        [cmd, "--camera", str(cam_id), "--duration", str(duration_sec), "--output", str(output_path)],
    ]
    timeout = max(15, int(duration_sec) + 20)
    for attempt in attempts:
        try:
            p = subprocess.run(attempt, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
            if p.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
                return True
        except subprocess.TimeoutExpired:
            try:
                if output_path.exists() and output_path.stat().st_size > 0:
                    return True
            except Exception:
                pass
        except Exception:
            pass
    return output_path.exists() and output_path.stat().st_size > 0

def record_audio_segment(duration_sec: int, output_path: Path) -> bool:
    try:
        run(["termux-microphone-record", "-q"], check=False)
        time.sleep(0.5)
        run(["termux-microphone-record", "-f", str(output_path), "-l", str(duration_sec), "-e", "aac"], check=False)
        time.sleep(duration_sec + 1)
        run(["termux-microphone-record", "-q"], check=False)
        return output_path.exists() and output_path.stat().st_size > 0
    except Exception:
        return False

def get_location(output_path: Path) -> bool:
    try:
        out = run(["termux-location", "-p", "gps", "-r", "last"], capture=True, check=False)
        if not out:
            out = run(["termux-location", "-p", "network"], capture=True, check=False)
        if out:
            output_path.write_text(out, encoding="utf-8")
            return True
    except Exception:
        pass
    return False

def detect_available_cameras(help_dir: Path) -> List[int]:
    """Detect usable Termux camera IDs. Falls back to testing 0 and 1."""
    camera_ids: List[int] = []
    if which("termux-camera-info"):
        out = run(["termux-camera-info"], capture=True, check=False)
        try:
            data = json.loads(out)
            if isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    raw_id = item.get("id", item.get("cameraId", item.get("camera_id")))
                    try:
                        cam_id = int(raw_id)
                    except Exception:
                        continue
                    if cam_id not in camera_ids:
                        camera_ids.append(cam_id)
        except Exception:
            pass

    for fallback in [0, 1]:
        if fallback not in camera_ids:
            camera_ids.append(fallback)

    working: List[int] = []
    test_photo = help_dir / "camera_test.jpg"
    for cam_id in camera_ids:
        if capture_photo_cam(cam_id, test_photo):
            working.append(cam_id)
            try:
                test_photo.unlink(missing_ok=True)
            except Exception:
                pass
    return working

def normalize_phone(phone: str) -> str:
    phone = str(phone).strip()
    has_plus = phone.startswith("+")
    digits = re.sub(r"\D", "", phone)
    return ("+" if has_plus else "") + digits

def phone_looks_valid(phone: str) -> bool:
    normalized = normalize_phone(phone)
    return bool(re.fullmatch(r"\+?[0-9]{6,25}", normalized))

def send_sms_alert(contacts: List[Dict[str, str]], repo_url: str) -> int:
    if not contacts:
        print("[!] No contacts configured. SMS not sent.")
        return 0
    if not which("termux-sms-send"):
        ensure_termux_api()
        if not which("termux-sms-send"):
            print("[!] termux-sms-send not available. SMS will not be sent.")
            return 0
    message = f"Emergency: Dead Man's Switch activated. Website/repository: {repo_url}"
    sent = 0
    for contact in contacts:
        raw_phone = str(contact.get("phone", "")).strip()
        phone = normalize_phone(raw_phone)
        if not phone_looks_valid(phone):
            print(f"[!] Skipping invalid phone number for {contact.get('name', 'unknown')}: {raw_phone}")
            continue
        print(f"[*] Sending SMS to {contact.get('name', phone)} ({phone})")
        run(["termux-sms-send", "-n", phone, message], check=False)
        sent += 1
    return sent


PERSONAL_DETAIL_FIELDS = [
    ("first_name", "First name"),
    ("last_name", "Last name"),
    ("aliases", "Nicknames / aliases"),
    ("phone", "Phone number"),
    ("email", "Email"),
    ("age", "Age"),
    ("birthday", "Birthday"),
    ("blood_type", "Blood type"),
    ("height", "Height"),
    ("weight", "Weight"),
    ("sex_or_gender", "Sex / gender (optional)"),
    ("nationality", "Nationality"),
    ("languages", "Languages spoken"),
    ("country_living", "Country living in"),
    ("city_living", "City living in"),
    ("area_or_neighborhood", "Area / neighborhood"),
    ("home_area_or_address", "Home area/address or last known safe place"),
    ("eye_color", "Eye color"),
    ("hair_color", "Hair color"),
    ("body_build", "Body build"),
    ("skin_complexion", "Skin/complexion description"),
    ("scars", "Scars / birthmarks"),
    ("tattoos", "Tattoos"),
    ("piercings", "Piercings"),
    ("medical_conditions", "Medical conditions that emergency helpers should know"),
    ("allergies", "Allergies"),
    ("medications", "Important medications"),
    ("emergency_instructions", "Emergency instructions"),
    ("trusted_people", "Trusted people / who should be contacted"),
    ("social_usernames", "Social usernames that can help identify you"),
    ("photo_description", "Photo/appearance description"),
    ("usual_clothing", "Usual clothing / accessories"),
    ("additional_notes", "Additional notes"),
]

PERSONAL_DETAILS_WARNING = """\
[!] Personal Details can be uploaded to your GitHub dead-mans-switch repository.
[!] In I Need Help mode, the repository is made PUBLIC so emergency contacts can access it.
[!] Do NOT store passwords, bank/card details, private keys, seed phrases, ID numbers, or anything that could be used to steal from you.
[!] Use this for identification and emergency-help information only.
"""

def personal_details_json_path() -> Path:
    return LOCAL_DIR / SITE_ASSETS_DIR_NAME / "Profile" / PERSONAL_DETAILS_JSON_NAME

def personal_details_txt_path() -> Path:
    return LOCAL_DIR / SITE_ASSETS_DIR_NAME / "Profile" / PERSONAL_DETAILS_TXT_NAME

def legacy_personal_details_json_path() -> Path:
    return LOCAL_DIR / PERSONAL_DETAILS_JSON_NAME

def legacy_personal_details_txt_path() -> Path:
    return LOCAL_DIR / PERSONAL_DETAILS_TXT_NAME

def default_personal_details() -> Dict[str, Any]:
    data = {key: "" for key, _ in PERSONAL_DETAIL_FIELDS}
    data["last_updated"] = ""
    return data

def load_personal_details() -> Dict[str, Any]:
    ensure_folder()
    path = personal_details_json_path()
    legacy_path = legacy_personal_details_json_path()
    data = default_personal_details()
    read_path = path if path.exists() else legacy_path
    if read_path.exists():
        try:
            loaded = json.loads(read_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                for key in data:
                    if key in loaded:
                        data[key] = loaded.get(key, "")
        except Exception:
            pass
    return data

def personal_details_has_content(data: Dict[str, Any]) -> bool:
    for key, _ in PERSONAL_DETAIL_FIELDS:
        if str(data.get(key, "")).strip():
            return True
    return False


def personal_details_for_site(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return display-ready details. Empty fields become simple placeholder text for the website only."""
    out = default_personal_details()
    if isinstance(data, dict):
        for key in out:
            out[key] = data.get(key, out.get(key, ""))
    placeholders = {
        "first_name": "Unknown",
        "last_name": "Person",
        "aliases": "Not provided yet",
        "phone": "Not provided yet",
        "email": "Not provided yet",
        "age": "Not provided yet",
        "birthday": "Not provided yet",
        "blood_type": "Not provided yet",
        "height": "Not provided yet",
        "weight": "Not provided yet",
        "sex_or_gender": "Not provided yet",
        "nationality": "Not provided yet",
        "languages": "Not provided yet",
        "country_living": "Not provided yet",
        "city_living": "Not provided yet",
        "area_or_neighborhood": "Not provided yet",
        "home_area_or_address": "Not provided yet",
        "eye_color": "Not provided yet",
        "hair_color": "Not provided yet",
        "body_build": "Not provided yet",
        "skin_complexion": "Not provided yet",
        "scars": "Not provided yet",
        "tattoos": "Not provided yet",
        "piercings": "Not provided yet",
        "medical_conditions": "Not provided yet",
        "allergies": "Not provided yet",
        "medications": "Not provided yet",
        "emergency_instructions": "No custom emergency instructions provided yet.",
        "trusted_people": "Use the configured SMS contacts if available.",
        "social_usernames": "Not provided yet",
        "photo_description": "No description provided yet.",
        "usual_clothing": "Not provided yet",
        "additional_notes": "No extra notes provided yet.",
    }
    for key, placeholder in placeholders.items():
        if not str(out.get(key, "")).strip():
            out[key] = placeholder
    if not str(out.get("last_updated", "")).strip():
        out["last_updated"] = "Not provided yet"
    return out

def personal_details_to_text(data: Dict[str, Any]) -> str:
    lines = [
        "Dead Man's Switch - Personal Details",
        "================================",
        "",
        "Purpose: identification and emergency-help information.",
        "Do not store passwords, bank/card details, private keys, seed phrases, or ID numbers here.",
        "",
        f"Last updated: {data.get('last_updated', '')}",
        "",
    ]
    for key, label in PERSONAL_DETAIL_FIELDS:
        value = str(data.get(key, "")).strip()
        if value:
            lines.append(f"{label}: {value}")
    if not personal_details_has_content(data):
        lines.append("No personal details have been added yet.")
    lines.append("")
    return "\n".join(lines)

def write_personal_details_files(data: Dict[str, Any]) -> List[Path]:
    ensure_folder()
    data = dict(data)
    if not data.get("last_updated"):
        data["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    personal_details_json_path().parent.mkdir(parents=True, exist_ok=True)
    personal_details_json_path().write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    personal_details_txt_path().write_text(personal_details_to_text(data), encoding="utf-8")
    return [personal_details_json_path(), personal_details_txt_path()]

def save_personal_details(data: Dict[str, Any]) -> None:
    data = dict(data)
    data["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    write_personal_details_files(data)

def print_personal_details(data: Dict[str, Any]) -> None:
    print("\n=== Personal Details ===")
    print(PERSONAL_DETAILS_WARNING)
    print(personal_details_to_text(data))
    print(f"Saved JSON: {personal_details_json_path()}")
    print(f"Saved TXT : {personal_details_txt_path()}")

def edit_all_personal_details(data: Dict[str, Any]) -> Dict[str, Any]:
    print("\n=== Add/Edit All Personal Details ===")
    print("Leave blank to keep the current value. Type '-' to clear a field.")
    for key, label in PERSONAL_DETAIL_FIELDS:
        current = str(data.get(key, "")).strip()
        shown = f" [{current}]" if current else ""
        value = input(f"{label}{shown}: ").strip()
        if value == "-":
            data[key] = ""
        elif value:
            data[key] = value
    save_personal_details(data)
    print("[✓] Personal details saved.")
    return data

def edit_one_personal_detail(data: Dict[str, Any]) -> Dict[str, Any]:
    print("\n=== Edit One Personal Detail ===")
    for i, (key, label) in enumerate(PERSONAL_DETAIL_FIELDS, 1):
        value = str(data.get(key, "")).strip()
        preview = value[:40] + ("..." if len(value) > 40 else "")
        print(f"{i}) {label}" + (f" - {preview}" if preview else ""))
    print("0) Back")
    choice = input("Select field: ").strip()
    if choice == "0":
        return data
    try:
        idx = int(choice) - 1
        if not 0 <= idx < len(PERSONAL_DETAIL_FIELDS):
            print("[!] Invalid field.")
            return data
        key, label = PERSONAL_DETAIL_FIELDS[idx]
        current = str(data.get(key, "")).strip()
        print(f"Current {label}: {current or '(empty)'}")
        value = input("New value (blank = clear): ").strip()
        data[key] = value
        save_personal_details(data)
        print("[✓] Updated.")
    except Exception:
        print("[!] Invalid selection.")
    return data

def clear_one_personal_detail(data: Dict[str, Any]) -> Dict[str, Any]:
    print("\n=== Clear One Personal Detail ===")
    for i, (key, label) in enumerate(PERSONAL_DETAIL_FIELDS, 1):
        value = str(data.get(key, "")).strip()
        if value:
            print(f"{i}) {label} - {value[:40]}" + ("..." if len(value) > 40 else ""))
        else:
            print(f"{i}) {label} - empty")
    print("0) Back")
    choice = input("Select field to clear: ").strip()
    if choice == "0":
        return data
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(PERSONAL_DETAIL_FIELDS):
            key, label = PERSONAL_DETAIL_FIELDS[idx]
            data[key] = ""
            save_personal_details(data)
            print(f"[✓] Cleared: {label}")
        else:
            print("[!] Invalid field.")
    except Exception:
        print("[!] Invalid selection.")
    return data

def delete_personal_details_files():
    for path in [personal_details_json_path(), personal_details_txt_path()]:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass
    print("[✓] Personal details files deleted locally.")

def configure_personal_details():
    ensure_folder()
    data = load_personal_details()
    while True:
        print("\n=== Personal Details ===")
        print("These details help identify you in an emergency and can be uploaded with the Dead Man's Switch repo.")
        print("1) View personal details")
        print("2) Add/Edit all details")
        print("3) Edit one field")
        print("4) Clear one field")
        print("5) Rebuild/export JSON + TXT files")
        print("6) Delete all personal details locally")
        print("0) Back")
        choice = input("Select: ").strip()
        if choice == "1":
            print_personal_details(data)
            input("Press Enter to continue...")
        elif choice == "2":
            print(PERSONAL_DETAILS_WARNING)
            data = edit_all_personal_details(data)
            input("Press Enter to continue...")
        elif choice == "3":
            data = edit_one_personal_detail(data)
            input("Press Enter to continue...")
        elif choice == "4":
            data = clear_one_personal_detail(data)
            input("Press Enter to continue...")
        elif choice == "5":
            paths = write_personal_details_files(data)
            print("[✓] Rebuilt personal detail files:")
            for path in paths:
                print(f"    {path}")
            input("Press Enter to continue...")
        elif choice == "6":
            confirm = input("Type DELETE DETAILS to delete local personal details: ").strip()
            if confirm == "DELETE DETAILS":
                data = default_personal_details()
                delete_personal_details_files()
            else:
                print("[*] Cancelled.")
            input("Press Enter to continue...")
        elif choice == "0":
            return
        else:
            print("[!] Invalid choice.")
            input("Press Enter to continue...")


def prompt_int_with_default(label: str, current: int, minimum: int) -> int:
    raw = input(f"{label} seconds [{current}]: ").strip()
    if not raw:
        return current
    try:
        value = int(raw)
        if value >= minimum:
            return value
        print(f"[!] Too low. Keeping {current}.")
    except Exception:
        print(f"[!] Invalid number. Keeping {current}.")
    return current

def first_time_i_need_help_setup(force: bool = False) -> None:
    settings = load_settings()
    if settings.get("help_first_setup_done") and not force:
        return
    ensure_folder()
    print("\n=== First Time Setup for I Need Help ===")
    print("This setup is shown before the first emergency activation.")
    print("It configures capture intervals, SMS contacts, and Personal Details.")
    print(PERSONAL_DETAILS_WARNING)

    use_defaults = input("Use default capture intervals? (Y/n): ").strip().lower()
    if use_defaults == "n":
        settings["help_photo_interval"] = prompt_int_with_default("Photo interval", int(settings.get("help_photo_interval", 5)), 1)
        settings["help_video_interval"] = prompt_int_with_default("Video interval", int(settings.get("help_video_interval", 5)), 1)
        settings["help_video_duration"] = prompt_int_with_default("Video duration", int(settings.get("help_video_duration", 5)), 1)
        settings["help_mic_interval"] = prompt_int_with_default("Microphone segment/interval", int(settings.get("help_mic_interval", 10)), 1)
        settings["help_location_interval"] = prompt_int_with_default("Location interval", int(settings.get("help_location_interval", 180)), 1)

    print("\nEmergency SMS contacts")
    contacts = settings.get("help_contacts", [])
    if contacts:
        print("Existing contacts:")
        for i, c in enumerate(contacts, 1):
            print(f"  {i}) {c.get('name')} - {c.get('phone')}")
    while True:
        add = input("Add an emergency SMS contact now? (y/N): ").strip().lower()
        if add != "y":
            break
        name = input("Name: ").strip()
        phone = input("Phone with country code, e.g. +306912345678: ").strip()
        if name and phone and phone_looks_valid(phone):
            contacts.append({"name": name, "phone": phone})
            print("[✓] Contact added.")
        else:
            print("[!] Invalid contact. Name and phone with country code are recommended.")
    settings["help_contacts"] = contacts

    data = load_personal_details()
    if not personal_details_has_content(data):
        print("\nPersonal Details")
        fill = input("Add Personal Details now? (recommended) (Y/n): ").strip().lower()
        if fill != "n":
            data = edit_all_personal_details(data)
        else:
            write_personal_details_files(data)
    else:
        print("[*] Personal Details already exist. You can change them later from Settings.")
        write_personal_details_files(data)

    settings["help_first_setup_done"] = True
    save_settings(settings)
    print("[✓] First time I Need Help setup saved.")

def repository_visibility_menu():
    print("\nChoose visibility:")
    print("1) Public")
    print("2) Private")
    print("0) Back")
    v = input("\nSelect: ").strip()
    if v == "1":
        set_visibility("public")
    elif v == "2":
        set_visibility("private")
    else:
        print("[*] Cancelled.")


def termux_widget_dir() -> Path:
    return Path.home() / ".shortcuts"

def termux_widget_path() -> Path:
    return termux_widget_dir() / "Dead Man's Switch"

def create_termux_widget():
    print("\n=== Create / Update Termux Widget ===")
    ensure_folder()
    widget_dir = termux_widget_dir()
    widget_dir.mkdir(parents=True, exist_ok=True)
    script_path = Path(__file__).resolve()
    python_bin = sys.executable or "python"
    widget_path = termux_widget_path()
    content = (
        "#!/data/data/com.termux/files/usr/bin/sh\n"
        "# Generated by Dead Man's Switch.py\n"
        "# Open the main Dead Man's Switch menu from Termux:Widget.\n"
        f"cd \"{script_path.parent}\"\n"
        f"exec \"{python_bin}\" \"{script_path}\"\n"
    )
    try:
        widget_path.write_text(content, encoding="utf-8")
        widget_path.chmod(0o755)
        print(f"[✓] Termux Widget created/updated: {widget_path}")
        print("\nHow to use it:")
        print("  1) Install the Termux:Widget Android app if you do not already have it.")
        print("  2) Long press your home screen.")
        print("  3) Add a Termux:Widget widget.")
        print("  4) Choose: Dead Man's Switch")
    except Exception:
        log_exception("Failed to create Termux Widget")
        print(f"[!] Failed to create widget. Check log: {get_log_file_path()}")

def delete_termux_widget():
    print("\n=== Delete Termux Widget ===")
    widget_path = termux_widget_path()
    try:
        if widget_path.exists():
            widget_path.unlink()
            print(f"[✓] Deleted Termux Widget: {widget_path}")
        else:
            print("[*] No Dead Man's Switch widget file exists yet.")
    except Exception:
        log_exception("Failed to delete Termux Widget")
        print(f"[!] Failed to delete widget. Check log: {get_log_file_path()}")

def termux_widget_menu():
    while True:
        print("\n=== Termux Widget ===")
        print("1) Create / Update Termux Widget")
        print("2) Delete Termux Widget")
        print("0) Back")
        choice = input("Select: ").strip()
        if choice == "1":
            create_termux_widget()
            input("Press Enter to continue...")
        elif choice == "2":
            confirm = input("Type DELETE to remove the widget file: ").strip()
            if confirm == "DELETE":
                delete_termux_widget()
            else:
                print("[*] Cancelled.")
            input("Press Enter to continue...")
        elif choice == "0":
            return
        else:
            print("[!] Invalid choice.")
            input("Press Enter to continue...")

def settings_menu():
    while True:
        print("\n=== Settings ===")
        print("1) Repository Visibility (Public / Private)")
        print("2) I Need Help settings (intervals, contacts)")
        print("3) Personal Details")
        print("4) Run I Need Help first-time setup again")
        print("5) Termux Widget (create/delete)")
        print("0) Back")
        choice = input("Select: ").strip()
        if choice == "1":
            repository_visibility_menu()
            input("Press Enter to continue...")
        elif choice == "2":
            configure_help_settings()
        elif choice == "3":
            configure_personal_details()
        elif choice == "4":
            first_time_i_need_help_setup(force=True)
            input("Press Enter to continue...")
        elif choice == "5":
            termux_widget_menu()
        elif choice == "0":
            return
        else:
            print("[!] Invalid choice.")
            input("Press Enter to continue...")

def existing_personal_detail_files() -> List[Path]:
    files = []
    for path in [personal_details_json_path(), personal_details_txt_path()]:
        if path.exists() and path.stat().st_size > 0:
            files.append(path)
    if files:
        return files
    # Backward compatibility with older script versions that saved these in the root.
    for path in [legacy_personal_details_json_path(), legacy_personal_details_txt_path()]:
        if path.exists() and path.stat().st_size > 0:
            files.append(path)
    return files

def configure_help_settings():
    settings = load_settings()
    while True:
        print("\n=== Configure I Need Help ===")
        print("Current settings:")
        print(f"  Photo interval: {settings['help_photo_interval']} seconds")
        print(f"  Video interval: {settings.get('help_video_interval', 5)} seconds")
        print(f"  Video duration: {settings.get('help_video_duration', 5)} seconds")
        print(f"  Microphone interval: {settings['help_mic_interval']} seconds")
        print(f"  Location interval: {settings['help_location_interval']} seconds")
        print("  Push interval: fixed 300 seconds / 5 minutes")
        print("  Contacts:")
        if settings.get("help_contacts"):
            for i, c in enumerate(settings.get("help_contacts", []), 1):
                print(f"    {i}) {c.get('name')} : {c.get('phone')}")
        else:
            print("    No contacts configured.")
        print("\n1) Set photo interval")
        print("2) Set video interval")
        print("3) Set video duration")
        print("4) Set microphone recording interval / segment length")
        print("5) Set location interval")
        print("6) Add contact")
        print("7) Edit contact")
        print("8) Delete contact")
        print("9) Back")
        choice = input("Select: ").strip()

        def set_interval(key: str, label: str, minimum: int):
            try:
                val = int(input(f"New {label} interval (seconds, >= {minimum}): ").strip())
                if val >= minimum:
                    settings[key] = val
                    save_settings(settings)
                    print("[✓] Updated.")
                else:
                    print(f"[!] Must be >= {minimum} seconds.")
            except Exception:
                print("[!] Invalid number.")

        if choice == "1":
            set_interval("help_photo_interval", "photo", 1)
        elif choice == "2":
            set_interval("help_video_interval", "video", 1)
        elif choice == "3":
            set_interval("help_video_duration", "video duration", 1)
        elif choice == "4":
            set_interval("help_mic_interval", "microphone", 1)
        elif choice == "5":
            set_interval("help_location_interval", "location", 1)
        elif choice == "6":
            name = input("Name: ").strip()
            phone = input("Phone (with country code, e.g., +306912345678): ").strip()
            if not name or not phone:
                print("[!] Name and phone are required.")
            elif not phone_looks_valid(phone):
                print("[!] Phone number format looks invalid. Use country code if possible, e.g., +306912345678.")
            else:
                settings.setdefault("help_contacts", []).append({"name": name, "phone": phone})
                save_settings(settings)
                print("[✓] Contact added.")
        elif choice == "7":
            contacts = settings.get("help_contacts", [])
            if not contacts:
                print("[!] No contacts to edit.")
            else:
                try:
                    idx = int(input("Contact number to edit: ").strip()) - 1
                    if 0 <= idx < len(contacts):
                        old = contacts[idx]
                        name = input(f"Name [{old.get('name', '')}]: ").strip() or old.get("name", "")
                        phone = input(f"Phone [{old.get('phone', '')}]: ").strip() or old.get("phone", "")
                        if name and phone and phone_looks_valid(phone):
                            contacts[idx] = {"name": name, "phone": phone}
                            save_settings(settings)
                            print("[✓] Contact updated.")
                        else:
                            print("[!] Invalid name or phone.")
                    else:
                        print("[!] Invalid contact number.")
                except Exception:
                    print("[!] Invalid selection.")
        elif choice == "8":
            contacts = settings.get("help_contacts", [])
            if not contacts:
                print("[!] No contacts to delete.")
            else:
                try:
                    idx = int(input("Contact number to delete: ").strip()) - 1
                    if 0 <= idx < len(contacts):
                        deleted = contacts.pop(idx)
                        save_settings(settings)
                        print(f"[✓] Deleted: {deleted.get('name')}")
                    else:
                        print("[!] Invalid contact number.")
                except Exception:
                    print("[!] Invalid selection.")
        elif choice == "9":
            return
        else:
            print("[!] Invalid choice.")
        input("Press Enter to continue...")
        settings = load_settings()

def help_mode():
    print("\n=== I NEED HELP MODE ===")
    first_time_i_need_help_setup(force=False)

    print("\n=== I NEED HELP MODE ===")
    print("[!] This will visibly activate emergency capture on THIS phone only.")
    print("[!] It will make your GitHub repository PUBLIC.")
    print("[!] It will capture available cameras, microphone segments, and location using Termux:API permissions.")
    print("[!] It will send SMS alerts only to contacts you configured in Settings.")
    print("[!] This action is visible and manual. It does not run secretly in the background.")
    print("[!] Stop method: press Ctrl+C. The script will then push remaining files before exiting.")

    ensure_folder()
    ensure_core_dependencies(include_termux_api=True)
    ensure_logged_in()
    ensure_repo_scope()
    owner = gh_user()
    if not owner:
        print("[!] Could not detect GitHub username.")
        return

    print("[*] Ensuring repository exists and is PUBLIC...")
    ensure_repo_created(owner, "public")
    set_visibility("public")
    run(["gh", "repo", "edit", f"{owner}/{REPO_NAME}", "--visibility", "public", "--accept-visibility-change-consequences"], check=False)

    init_or_use_git_repo()
    set_remote(owner)
    ensure_gitignore()
    sync_local_repo_with_remote(owner)

    pages_url = expected_pages_url(owner)
    raw_repo_url = f"https://github.com/{owner}/{REPO_NAME}"
    print_github_pages_manual_setup_guide(owner)
    input("Press Enter to confirm GitHub Pages is enabled or you understand it may show 404 until enabled...")
    input("Press Enter one more time to START I Need Help now...")

    camera_ok = ensure_termux_camera()
    video_ok = ensure_termux_video()
    mic_ok = ensure_termux_microphone()
    location_ok = ensure_termux_location()

    archive_previous_version_and_clean_repo(owner, "I Need Help activation")
    organize_local_repository_structure()
    ensure_readme(owner, pages_url)
    generate_static_website(owner, pages_url)

    session_id = time.strftime("session_%Y%m%d_%H%M%S")
    photos_dir = LOCAL_DIR / SITE_ASSETS_DIR_NAME / "Photos" / session_id
    videos_dir = LOCAL_DIR / SITE_ASSETS_DIR_NAME / "Videos" / session_id
    recordings_dir = LOCAL_DIR / SITE_ASSETS_DIR_NAME / "Recordings" / session_id
    locations_dir = LOCAL_DIR / SITE_ASSETS_DIR_NAME / "Locations" / session_id
    session_dir = LOCAL_DIR / SITE_ASSETS_DIR_NAME / "Sessions" / session_id
    for d in [photos_dir, videos_dir, recordings_dir, locations_dir, session_dir]:
        d.mkdir(parents=True, exist_ok=True)

    settings = load_settings()
    photo_interval = settings.get("help_photo_interval", 5)
    video_interval = settings.get("help_video_interval", 5)
    video_duration = settings.get("help_video_duration", 5)
    mic_interval = settings.get("help_mic_interval", 10)
    loc_interval = settings.get("help_location_interval", 180)
    push_interval = 300  # Fixed emergency behavior requested by the user: push every 5 minutes.
    contacts = settings.get("help_contacts", [])

    repo_url = pages_url or raw_repo_url
    session_info = session_dir / "SESSION_INFO.txt"
    session_info.write_text(
        "Dead Man's Switch emergency session\n"
        f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Website: {repo_url}\n"
        f"Repo: {raw_repo_url}\n"
        f"Photo interval: {photo_interval}s\n"
        f"Video interval: {video_interval}s\n"
        f"Video duration: {video_duration}s\n"
        f"Microphone interval/segment: {mic_interval}s\n"
        f"Location interval: {loc_interval}s\n"
        "Push interval: 300s / 5 minutes\n"
        "Activation required two visible Enter confirmations from the device owner.\n"
        "Stop method: Ctrl+C.\n",
        encoding="utf-8"
    )

    if camera_ok:
        cameras = detect_available_cameras(session_dir)
    else:
        cameras = []
    if not cameras:
        print("[!] No working camera detected or camera permission missing. Photos will be skipped.")
    print(f"[*] Detected cameras: {cameras}")
    if not video_ok:
        print("[!] Video capture unavailable. Videos will be skipped.")
    if not mic_ok:
        print("[!] Microphone capture unavailable. Audio will be skipped.")
    if not location_ok:
        print("[!] Location unavailable. Location files will be skipped.")

    lock = threading.Lock()
    staged_files: List[str] = []
    staged_size = 0
    sms_sent = False
    audio_in_progress = False
    last_photo_time = 0.0
    last_video_time = 0.0
    last_mic_time = 0.0
    last_location_time = 0.0
    last_push_time = 0.0

    def queue_file(filepath: Path, label: str) -> bool:
        nonlocal staged_size
        try:
            if not filepath.exists() or filepath.stat().st_size <= 0:
                print(f"[!] {label} file missing or empty: {filepath.name}")
                return False
            size = filepath.stat().st_size
            if size > MAX_FILE_BYTES:
                print(f"[!] {label} too large ({size/(1024*1024):.2f} MB), skipping: {filepath.name}")
                return False
            rel = filepath.relative_to(LOCAL_DIR).as_posix()
            with lock:
                if rel not in staged_files:
                    staged_files.append(rel)
                    staged_size += size
            print(f"[*] {label} saved: {filepath.name} ({size/(1024*1024):.2f} MB)")
            return True
        except Exception as e:
            print(f"[!] Could not queue {label}: {e}")
            return False

    def queue_existing_local_files_for_emergency():
        """Queue existing files already in the Dead Man's Switch local folder for the first emergency upload."""
        print("[*] Adding existing local Dead Man's Switch folder files to the emergency upload...")
        added = 0
        skipped = 0
        for rel, size in list_local_files():
            rel = rel.replace("\\", "/")
            if rel.startswith(".git/") or "/.git/" in rel:
                continue
            if rel == "README.md" or is_generated_site_file(rel):
                continue
            if size <= 0:
                continue
            if size > MAX_FILE_BYTES:
                skipped += 1
                print(f"[!] Existing local file too large, skipping: {rel} ({human_size(size)})")
                continue
            path = LOCAL_DIR / rel
            if queue_file(path, "Existing local file"):
                added += 1
        print(f"[✓] Existing local files queued: {added}" + (f" | skipped too large: {skipped}" if skipped else ""))

    def do_push(force_commit_msg=None) -> bool:
        nonlocal last_push_time, staged_size, staged_files
        with lock:
            ensure_readme(owner, pages_url)
            generated_site_paths = generate_static_website(owner, pages_url)
            to_stage = []
            for rel in ["README.md"] + list(staged_files) + list(generated_site_paths):
                if rel not in to_stage:
                    to_stage.append(rel)
            if not to_stage:
                return False
            to_stage_size = staged_size
            run(["git", "reset"], cwd=str(LOCAL_DIR), check=False)
            stage_paths(to_stage, force=True)
            msg = force_commit_msg or f"Emergency batch push ({len(to_stage)} items, {to_stage_size/(1024*1024):.2f} MB plus website)"
            if commit_staged(msg) and push_current():
                staged_files = []
                staged_size = 0
                last_push_time = time.time()
                return True
        return False

    def send_sms_once(reason: str):
        nonlocal sms_sent
        if sms_sent:
            return
        if not contacts:
            print("[!] No contacts configured. SMS not sent.")
            sms_sent = True
            return
        print(f"[*] Sending emergency SMS alert ({reason})...")
        send_sms_alert(contacts, repo_url)
        sms_sent = True

    def record_audio_async(output_path: Path, duration_sec: int):
        nonlocal audio_in_progress
        try:
            if record_audio_segment(duration_sec, output_path):
                queue_file(output_path, "Audio")
            else:
                print("[!] Failed to record audio")
        finally:
            audio_in_progress = False

    queue_file(session_info, "Session info")
    personal_files = existing_personal_detail_files()
    if personal_files:
        for personal_file in personal_files:
            queue_file(personal_file, "Personal details")
    else:
        print("[!] No Personal Details file found. You can add it from Settings.")

    queue_existing_local_files_for_emergency()

    print("\n[*] Capturing first emergency set now...")
    first_set_time = time.time()

    if cameras:
        for cam_id in cameras:
            ts = time.strftime("%Y%m%d_%H%M%S")
            filepath = photos_dir / f"photo_cam{cam_id}_{ts}.jpg"
            if capture_photo_cam(cam_id, filepath):
                queue_file(filepath, f"Photo cam{cam_id}")
            else:
                print(f"[!] Failed to capture photo from camera {cam_id}")
    else:
        print("[*] First photo step skipped: no available cameras.")

    if video_ok and cameras:
        print(f"[*] Capturing first video set ({video_duration}s each) after photos...")
        for cam_id in cameras:
            ts = time.strftime("%Y%m%d_%H%M%S")
            filepath = videos_dir / f"video_cam{cam_id}_{ts}.mp4"
            if capture_video_cam(cam_id, video_duration, filepath):
                queue_file(filepath, f"Video cam{cam_id}")
            else:
                print(f"[!] Failed to capture video from camera {cam_id}")
    else:
        print("[*] First video step skipped: video command unavailable or no cameras.")

    if location_ok:
        ts = time.strftime("%Y%m%d_%H%M%S")
        filepath = locations_dir / f"location_{ts}.json"
        if get_location(filepath):
            queue_file(filepath, "Location")
        else:
            print("[!] Failed to get first location")
    else:
        print("[*] First location step skipped: location unavailable.")

    if mic_ok:
        ts = time.strftime("%Y%m%d_%H%M%S")
        filepath = recordings_dir / f"audio_{ts}.aac"
        print(f"[*] Recording first audio segment ({mic_interval}s) before first push...")
        if record_audio_segment(mic_interval, filepath):
            queue_file(filepath, "Audio")
        else:
            print("[!] Failed to record first audio")
    else:
        print("[*] First audio step skipped: microphone unavailable.")

    last_photo_time = first_set_time
    last_video_time = time.time()
    last_mic_time = time.time()
    last_location_time = first_set_time

    print("[*] First emergency capture set finished. Pushing immediately...")
    first_push_ok = do_push("Initial emergency data after first capture set")
    if first_push_ok:
        print("[✓] First emergency upload completed.")
    else:
        print("[!] First emergency upload did not complete. It will retry every 5 minutes and on Ctrl+C.")
        last_push_time = time.time()

    send_sms_once("first capture finished")

    print("\n[!] Emergency capture is active. Keep this Termux session open.")
    print("[!] Press Ctrl+C to stop. Remaining queued files will be pushed before exit.")
    print("[!] Automatic push interval: every 5 minutes.\n")
    try:
        while True:
            now = time.time()

            if cameras and (now - last_photo_time) >= photo_interval:
                last_photo_time = now
                for cam_id in cameras:
                    ts = time.strftime("%Y%m%d_%H%M%S")
                    filepath = photos_dir / f"photo_cam{cam_id}_{ts}.jpg"
                    if capture_photo_cam(cam_id, filepath):
                        queue_file(filepath, f"Photo cam{cam_id}")
                    else:
                        print(f"[!] Failed to capture photo from camera {cam_id}")

            if video_ok and cameras and (now - last_video_time) >= video_interval:
                last_video_time = now
                print(f"[*] Capturing video set ({video_duration}s each)...")
                for cam_id in cameras:
                    ts = time.strftime("%Y%m%d_%H%M%S")
                    filepath = videos_dir / f"video_cam{cam_id}_{ts}.mp4"
                    if capture_video_cam(cam_id, video_duration, filepath):
                        queue_file(filepath, f"Video cam{cam_id}")
                    else:
                        print(f"[!] Failed to capture video from camera {cam_id}")

            if mic_ok and not audio_in_progress and (now - last_mic_time) >= mic_interval:
                last_mic_time = now
                audio_in_progress = True
                ts = time.strftime("%Y%m%d_%H%M%S")
                filepath = recordings_dir / f"audio_{ts}.aac"
                t = threading.Thread(target=record_audio_async, args=(filepath, mic_interval), daemon=True)
                t.start()

            if location_ok and (now - last_location_time) >= loc_interval:
                last_location_time = now
                ts = time.strftime("%Y%m%d_%H%M%S")
                filepath = locations_dir / f"location_{ts}.json"
                if get_location(filepath):
                    queue_file(filepath, "Location")
                else:
                    print("[!] Failed to get location")

            with lock:
                has_files = bool(staged_files)
                queued_size = staged_size

            if has_files and ((time.time() - last_push_time) >= push_interval or queued_size >= MAX_BATCH_BYTES):
                do_push()

            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Emergency mode stopped by Ctrl+C.")
        if audio_in_progress:
            print("[*] Waiting a few seconds for the current audio segment to finish...")
            wait_until = time.time() + max(3, min(mic_interval + 2, 20))
            while audio_in_progress and time.time() < wait_until:
                time.sleep(1)
        with lock:
            has_files = bool(staged_files)
        if has_files:
            print("[*] Pushing remaining data...")
            do_push("Final emergency data before Ctrl+C stop")
        print("[✓] Help mode finished. Repository remains public.")
        return


# ========== GitHub Pages / Static emergency website functionality ==========

GENERATED_SITE_REL_PATHS = {
    "index.html",
    SITE_CSS_NAME,
    SITE_JS_NAME,
    f"{PAGES_DIR_NAME}/profile.html",
    f"{PAGES_DIR_NAME}/gallery.html",
    f"{PAGES_DIR_NAME}/videos.html",
    f"{PAGES_DIR_NAME}/audio.html",
    f"{PAGES_DIR_NAME}/locations.html",
    f"{PAGES_DIR_NAME}/timeline.html",
    f"{PAGES_DIR_NAME}/files.html",
    f"{PAGES_DIR_NAME}/emergency.html",
    f"{SITE_ASSETS_DIR_NAME}/{SITE_MANIFEST_NAME}",
}

SITE_CSS = """/* Dead Man's Switch emergency website theme
   Colors based on the DedSec Project CSS variables provided by the user. */
:root{
  --nm-abyss-blue:#000000;--nm-darkest:rgba(10,10,18,.72);--nm-nav-solid:#0b0a12;--nm-menu-solid:#0e0d18;--nm-dark:rgba(14,14,24,.58);--nm-container:rgba(18,18,30,.52);
  --nm-border:rgba(205,147,255,.50);--nm-accent:#cd93ff;--nm-accent-hover:#e2c1ff;--nm-text:rgba(255,255,255,.92);--nm-text-muted:rgba(255,255,255,.74);--nm-text-accent:rgba(255,255,255,.96);
  --nm-danger:#ff6b6b;--nm-success:#51cf66;--nm-warning:#ffd43b;--nm-text-on-accent:#0b0a12;--glow-rgb:205,147,255;--shadow-elev-1:0 10px 30px rgba(0,0,0,.35);--shadow-elev-2:0 18px 50px rgba(0,0,0,.42);
  --radius-sm:0;--radius-md:0;--radius-lg:0;--radius-pill:0;
  --font-primary:Inter,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;--font-secondary:Orbitron,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;--font-mono:'Roboto Mono',ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,'Courier New',monospace;
}
body.light-theme{--nm-abyss-blue:#ffffff;--nm-darkest:rgba(255,255,255,.82);--nm-nav-solid:#ffffff;--nm-menu-solid:#ffffff;--nm-dark:rgba(255,255,255,.70);--nm-container:rgba(255,255,255,.62);--nm-border:rgba(123,31,162,.35);--nm-accent:#7b1fa2;--nm-accent-hover:#9c27b0;--nm-text:rgba(10,10,18,.92);--nm-text-muted:rgba(10,10,18,.70);--nm-text-accent:rgba(10,10,18,.96);--nm-danger:#d6336c;--nm-success:#2f9e44;--nm-warning:#f59f00;--nm-text-on-accent:rgba(255,255,255,.96);--glow-rgb:123,31,162;--shadow-elev-1:0 10px 30px rgba(0,0,0,.12);--shadow-elev-2:0 18px 50px rgba(0,0,0,.16)}
*,*::before,*::after{box-sizing:border-box}html{scroll-behavior:smooth;-webkit-tap-highlight-color:transparent}body{margin:0;background:var(--nm-abyss-blue);color:var(--nm-text);font-family:var(--font-primary);font-size:15px;line-height:1.45;overflow-x:hidden;-webkit-font-smoothing:antialiased}body::before{content:"";position:fixed;inset:0;z-index:-2;pointer-events:none;background:radial-gradient(900px 380px at 10% -5%,rgba(var(--glow-rgb),.24),transparent 60%),radial-gradient(700px 320px at 95% 0%,rgba(255,198,122,.10),transparent 55%),linear-gradient(180deg,var(--nm-abyss-blue),var(--nm-menu-solid))}a{color:var(--nm-accent);text-decoration:none}a:hover{text-decoration:underline}img,video,audio{max-width:100%}
.topbar{position:sticky;top:0;z-index:80;background:var(--nm-nav-solid);border-bottom:1px solid var(--nm-border);box-shadow:var(--shadow-elev-1)}.nav{max-width:1180px;margin:0 auto;display:flex;align-items:center;gap:12px;padding:12px 16px}.brand{font-family:var(--font-secondary);font-weight:800;letter-spacing:.04em;color:var(--nm-text-accent);margin-right:auto}.brand small{display:block;font-family:var(--font-mono);font-size:.68rem;color:var(--nm-text-muted);letter-spacing:0}.burger-btn{border:1px solid var(--nm-border);background:var(--nm-container);color:var(--nm-text);border-radius:0;padding:10px 12px;font-family:var(--font-mono);font-size:.86rem;cursor:pointer;display:inline-flex;align-items:center;gap:8px}.burger-lines{display:inline-flex;flex-direction:column;gap:4px}.burger-lines span{display:block;width:22px;height:2px;background:var(--nm-text)}.burger-btn:hover{background:var(--nm-accent);color:var(--nm-text-on-accent);border-color:var(--nm-accent)}.burger-btn:hover .burger-lines span{background:var(--nm-text-on-accent)}.menu-panel{position:fixed;top:0;right:0;width:min(360px,92vw);height:100vh;background:var(--nm-menu-solid);border-left:1px solid var(--nm-border);box-shadow:var(--shadow-elev-2);transform:translateX(110%);transition:transform .25s ease;z-index:100;padding:16px;display:flex;flex-direction:column;gap:10px;overflow:auto}.menu-panel.open{transform:translateX(0)}.menu-header{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--nm-border);padding-bottom:10px;margin-bottom:8px;font-family:var(--font-secondary);color:var(--nm-text-accent)}.menu-panel a,.menu-panel button,.btn{border:1px solid var(--nm-border);background:var(--nm-container);color:var(--nm-text);border-radius:0;padding:10px 12px;font-family:var(--font-mono);font-size:.84rem;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:7px;text-decoration:none;width:100%}.menu-panel a.active,.menu-panel a:hover,.menu-panel button:hover,.btn:hover{background:var(--nm-accent);color:var(--nm-text-on-accent);border-color:var(--nm-accent);text-decoration:none;transform:translateY(-1px)}.menu-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:90;opacity:0;pointer-events:none;transition:opacity .25s ease}.menu-backdrop.open{opacity:1;pointer-events:auto}.close-menu{max-width:80px;margin-left:auto}.wrap{max-width:1180px;margin:0 auto;padding:24px 16px 50px}.hero{position:relative;overflow:hidden;border:1px solid var(--nm-border);border-radius:0;background:linear-gradient(180deg,rgba(var(--glow-rgb),.16),rgba(14,13,24,.92));padding:30px;margin-bottom:22px;box-shadow:var(--shadow-elev-1)}.hero::before{content:"";position:absolute;inset:-2px;background:conic-gradient(from 180deg,rgba(198,155,255,.55),rgba(255,170,210,.20),rgba(255,164,98,.18),rgba(198,155,255,.55));filter:blur(22px);opacity:.28;z-index:0}.hero>*{position:relative;z-index:1}.badge{display:inline-flex;align-items:center;gap:8px;background:var(--nm-accent);color:var(--nm-text-on-accent);border-radius:0;padding:8px 13px;font-weight:800;font-family:var(--font-mono);font-size:.8rem}.hero h1{font-family:var(--font-secondary);font-size:clamp(1.7rem,5vw,3rem);margin:15px 0 8px;color:var(--nm-text-accent)}.hero p{max-width:76ch;color:var(--nm-text-muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px}.grid.small{grid-template-columns:repeat(auto-fit,minmax(170px,1fr))}.card{background:var(--nm-dark);border:1px solid var(--nm-border);border-radius:0;padding:17px;box-shadow:var(--shadow-elev-1);overflow:hidden}.card:hover{border-color:var(--nm-accent)}.card h2,.card h3{font-family:var(--font-secondary);color:var(--nm-text-accent);margin:.2rem 0 .65rem}.muted{color:var(--nm-text-muted)}.stat{font-family:var(--font-secondary);font-size:1.8rem;color:var(--nm-accent);font-weight:800}.warning{border-left:5px solid var(--nm-danger);background:rgba(255,107,107,.08)}.success{border-left:5px solid var(--nm-success);background:rgba(81,207,102,.08)}.buttons{display:flex;gap:10px;flex-wrap:wrap;margin-top:15px}.buttons .btn{width:auto}.btn.primary{background:var(--nm-accent);color:var(--nm-text-on-accent);border-color:var(--nm-accent);font-weight:800}.btn.danger{border-color:var(--nm-danger);color:var(--nm-danger)}.btn.danger:hover{background:var(--nm-danger);color:white}.profile-table,.file-table{width:100%;border-collapse:collapse;overflow:hidden}.profile-table th,.profile-table td,.file-table th,.file-table td{border-bottom:1px solid var(--nm-border);padding:10px;text-align:left;vertical-align:top}.profile-table th,.file-table th{font-family:var(--font-mono);color:var(--nm-text-accent);width:210px}.table-wrap{overflow:auto;border:1px solid var(--nm-border);border-radius:0}
.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}.photo-card img,.video-card video{width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:0;border:1px solid var(--nm-border);background:var(--nm-menu-solid)}.media-meta{font-family:var(--font-mono);font-size:.76rem;color:var(--nm-text-muted);word-break:break-word;margin-top:8px}.audio-list{display:grid;gap:12px}.searchbar{width:100%;border:1px solid var(--nm-border);background:var(--nm-menu-solid);color:var(--nm-text);border-radius:0;padding:12px 14px;margin:12px 0 18px;font-family:var(--font-mono)}.timeline{position:relative;margin-left:10px}.timeline::before{content:"";position:absolute;left:8px;top:0;bottom:0;border-left:2px solid var(--nm-border)}.event{position:relative;margin:0 0 14px 30px}.event::before{content:"";position:absolute;left:-28px;top:9px;width:12px;height:12px;border-radius:0;background:var(--nm-accent);box-shadow:0 0 0 4px rgba(var(--glow-rgb),.14)}.pill{display:inline-flex;border:1px solid var(--nm-border);border-radius:0;padding:4px 8px;font-family:var(--font-mono);font-size:.73rem;color:var(--nm-text-muted);margin:2px}.empty{text-align:center;color:var(--nm-text-muted);padding:35px;border:1px dashed var(--nm-border);border-radius:0}footer{border-top:1px solid var(--nm-border);color:var(--nm-text-muted);font-size:.82rem;margin-top:35px;padding-top:18px}.hide{display:none!important}
@media(max-width:640px){.brand{min-width:0}.hero{padding:20px}.profile-table th,.profile-table td,.file-table th,.file-table td{display:block;width:100%}.file-table thead{display:none}.file-table tr{display:block;border-bottom:1px solid var(--nm-border);padding:8px}.file-table td{border:0;padding:5px 8px}.gallery{grid-template-columns:repeat(auto-fit,minmax(140px,1fr))}.buttons .btn{width:100%}}
"""

SITE_JS = """(function(){
  const savedTheme = localStorage.getItem('dead-switch-theme');
  if(savedTheme === 'light') document.body.classList.add('light-theme');
  const themeBtn = document.querySelector('[data-theme-toggle]');
  function updateThemeText(){ if(themeBtn) themeBtn.textContent = document.body.classList.contains('light-theme') ? 'Dark Theme' : 'Light Theme'; }
  if(themeBtn){themeBtn.addEventListener('click',()=>{document.body.classList.toggle('light-theme');localStorage.setItem('dead-switch-theme',document.body.classList.contains('light-theme')?'light':'dark');updateThemeText();});updateThemeText();}
  const menu = document.querySelector('[data-menu-panel]');
  const backdrop = document.querySelector('[data-menu-backdrop]');
  const openBtn = document.querySelector('[data-menu-open]');
  const closeBtn = document.querySelector('[data-menu-close]');
  function setMenu(open){ if(menu) menu.classList.toggle('open', open); if(backdrop) backdrop.classList.toggle('open', open); if(openBtn) openBtn.setAttribute('aria-expanded', open ? 'true' : 'false'); }
  if(openBtn) openBtn.addEventListener('click',()=>setMenu(true));
  if(closeBtn) closeBtn.addEventListener('click',()=>setMenu(false));
  if(backdrop) backdrop.addEventListener('click',()=>setMenu(false));
  document.addEventListener('keydown',e=>{ if(e.key === 'Escape') setMenu(false); });
  const search = document.querySelector('[data-search]');
  if(search){search.addEventListener('input',()=>{const q=search.value.toLowerCase().trim();document.querySelectorAll('[data-filter-card]').forEach(card=>{card.classList.toggle('hide', q && !card.textContent.toLowerCase().includes(q));});});}
})();
"""

def site_assets_dir() -> Path:
    return LOCAL_DIR / SITE_ASSETS_DIR_NAME

def is_generated_site_file(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    # Only generated website files are excluded. User/emergency media inside Assets/ must stay indexed.
    return rel in GENERATED_SITE_REL_PATHS or rel.startswith(f"{PAGES_DIR_NAME}/")

def h(value: Any) -> str:
    return html_lib.escape(str(value or ""), quote=True)

def link_for_rel(rel: str) -> str:
    return "/".join(quote(part) for part in rel.split("/"))

def human_size(size: int) -> str:
    try:
        size = int(size)
    except Exception:
        return "0 B"
    units = ["B", "KB", "MB", "GB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"

def format_local_time(ts: float) -> str:
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(ts)))
    except Exception:
        return "Unknown"

def timestamp_from_name(rel: str, fallback_mtime: float) -> Tuple[str, str, float]:
    name = Path(rel).name
    match = re.search(r"(20\d{6})[_-](\d{6})", rel)
    if match:
        raw_date, raw_time = match.group(1), match.group(2)
        try:
            parsed = time.mktime(time.strptime(raw_date + raw_time, "%Y%m%d%H%M%S"))
            return raw_date[:4] + "-" + raw_date[4:6] + "-" + raw_date[6:8], raw_time[:2] + ":" + raw_time[2:4] + ":" + raw_time[4:6], parsed
        except Exception:
            pass
    formatted = format_local_time(fallback_mtime)
    if " " in formatted:
        d, t = formatted.split(" ", 1)
        return d, t, fallback_mtime
    return "Unknown", "Unknown", fallback_mtime

def file_kind(rel: str) -> str:
    lower = rel.lower()
    suffix = Path(lower).suffix
    if Path(rel).name in {PERSONAL_DETAILS_JSON_NAME, PERSONAL_DETAILS_TXT_NAME}:
        return "Personal profile"
    if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return "Photo"
    if suffix in {".mp4", ".3gp", ".webm", ".mkv", ".mov"}:
        return "Video"
    if suffix in {".aac", ".mp3", ".wav", ".m4a", ".ogg", ".flac"}:
        return "Audio"
    if "location" in lower and suffix in {".json", ".txt"}:
        return "Location"
    if "session_info" in lower:
        return "Emergency session"
    if suffix in {".pdf", ".doc", ".docx", ".txt", ".md", ".json", ".csv"}:
        return "Document"
    return "File"

def scan_site_items(include_generated: bool = False) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    ensure_folder()
    for rel, size in list_local_files():
        if rel.startswith(".git/") or "/.git/" in rel:
            continue
        if Path(rel).name == ".gitkeep":
            continue
        if not include_generated and is_generated_site_file(rel):
            continue
        path = LOCAL_DIR / rel
        try:
            mtime = path.stat().st_mtime
        except Exception:
            mtime = time.time()
        date, clock, sort_ts = timestamp_from_name(rel, mtime)
        mime, _ = mimetypes.guess_type(str(path))
        items.append({
            "rel": rel,
            "url": link_for_rel(rel),
            "name": Path(rel).name,
            "folder": str(Path(rel).parent).replace(".", "") or "Root",
            "size": size,
            "size_h": human_size(size),
            "mtime": mtime,
            "updated": format_local_time(mtime),
            "date": date,
            "time": clock,
            "sort_ts": sort_ts,
            "kind": file_kind(rel),
            "mime": mime or "",
        })
    items.sort(key=lambda x: (x.get("sort_ts") or 0), reverse=True)
    return items

def read_location_info(path: Path) -> Tuple[str, str, str]:
    """Return latitude, longitude, map_link from a Termux location JSON file when possible."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        lat = data.get("latitude", data.get("lat", ""))
        lon = data.get("longitude", data.get("lon", data.get("lng", "")))
        if lat != "" and lon != "":
            return str(lat), str(lon), f"https://www.google.com/maps?q={quote(str(lat))},{quote(str(lon))}"
    except Exception:
        pass
    return "", "", ""

def site_nav(active: str) -> str:
    links = [
        ("index.html", "Dashboard", "dashboard"),
        (f"{PAGES_DIR_NAME}/profile.html", "Person Profile", "profile"),
        (f"{PAGES_DIR_NAME}/gallery.html", "Photo Gallery", "gallery"),
        (f"{PAGES_DIR_NAME}/videos.html", "Videos", "videos"),
        (f"{PAGES_DIR_NAME}/audio.html", "Audio", "audio"),
        (f"{PAGES_DIR_NAME}/locations.html", "Locations", "locations"),
        (f"{PAGES_DIR_NAME}/timeline.html", "Timeline", "timeline"),
        (f"{PAGES_DIR_NAME}/files.html", "All Files", "files"),
        (f"{PAGES_DIR_NAME}/emergency.html", "Emergency Info", "emergency"),
    ]
    link_html = "\n".join(f'<a class="{ "active" if key == active else "" }" href="{href}">{label}</a>' for href, label, key in links)
    return f"""
<header class="topbar">
  <nav class="nav">
    <div class="brand">Dead Man's Switch<small>Emergency GitHub Pages backup</small></div>
    <button class="burger-btn" type="button" data-menu-open aria-label="Open menu" aria-expanded="false"><span class="burger-lines"><span></span><span></span><span></span></span> Menu</button>
  </nav>
</header>
<div class="menu-backdrop" data-menu-backdrop></div>
<aside class="menu-panel" data-menu-panel>
  <div class="menu-header"><span>Menu</span><button class="close-menu" type="button" data-menu-close>Close</button></div>
  {link_html}
  <button type="button" data-theme-toggle>Theme</button>
</aside>
"""

def site_layout(title: str, active: str, body: str, generated_at: str, in_pages: bool = False) -> str:
    base_tag = '<base href="../">' if in_pages else ''
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{h(title)} - Dead Man's Switch</title>
{base_tag}
<link rel="stylesheet" href="{SITE_CSS_NAME}">
</head>
<body>
{site_nav(active)}
<main class="wrap">
{body}
<footer>
  <p>Generated by Dead Man's Switch.py on {h(generated_at)}. This static website is meant to help trusted people quickly understand and review emergency files.</p>
  <p>Privacy note: emergency mode can make this repository public. Do not place passwords, card numbers, seed phrases, private keys, or sensitive account secrets here.</p>
</footer>
</main>
<script src="{SITE_JS_NAME}"></script>
</body>
</html>
"""

def stat_cards(items: List[Dict[str, Any]]) -> str:
    photos = sum(1 for i in items if i["kind"] == "Photo")
    videos = sum(1 for i in items if i["kind"] == "Video")
    audio = sum(1 for i in items if i["kind"] == "Audio")
    locations = sum(1 for i in items if i["kind"] == "Location")
    sessions = sum(1 for i in items if i["kind"] == "Emergency session")
    docs = sum(1 for i in items if i["kind"] in {"Document", "Personal profile"})
    return f"""
<section class="grid small">
  <div class="card"><div class="stat">{len(items)}</div><div class="muted">Total files indexed</div></div>
  <div class="card"><div class="stat">{photos}</div><div class="muted">Photos</div></div>
  <div class="card"><div class="stat">{videos}</div><div class="muted">Videos</div></div>
  <div class="card"><div class="stat">{audio}</div><div class="muted">Audio clips</div></div>
  <div class="card"><div class="stat">{locations}</div><div class="muted">Location files</div></div>
  <div class="card"><div class="stat">{sessions}</div><div class="muted">Emergency sessions</div></div>
  <div class="card"><div class="stat">{docs}</div><div class="muted">Profile / documents</div></div>
</section>
"""

def dashboard_page(items: List[Dict[str, Any]], personal: Dict[str, Any], generated_at: str, owner: str = "", pages_url: str = "") -> str:
    latest = items[:8]
    name = " ".join(str(personal.get(k, "")).strip() for k in ["first_name", "last_name"]).strip() or "Unknown person"
    city = str(personal.get("city_living", "")).strip() or str(personal.get("area_or_neighborhood", "")).strip() or "Unknown location"
    cards = "".join(f"""
      <div class="card" data-filter-card>
        <span class="pill">{h(item['kind'])}</span><span class="pill">{h(item['date'])} {h(item['time'])}</span>
        <h3>{h(item['name'])}</h3>
        <p class="muted">{h(item['folder'])} · {h(item['size_h'])}</p>
        <a class="btn" href="{h(item['url'])}">Open file</a>
      </div>
    """ for item in latest)
    if not cards:
        cards = '<div class="empty">No files indexed yet.</div>'
    repo_url = repo_url_for(owner)
    pages_url = pages_url or expected_pages_url(owner)
    link_cards = ""
    if pages_url or repo_url:
        link_cards = f"""
<section class="grid">
  <div class="card success"><h2>GitHub Pages Link</h2><p class="muted">This is the website link also written into README.md.</p><a class="btn primary" href="{h(pages_url)}">Open Website</a></div>
  <div class="card"><h2>Repository Link</h2><p class="muted">Raw GitHub repository with every uploaded file.</p><a class="btn" href="{h(repo_url)}">Open Repository</a></div>
</section>
"""
    body = f"""
<section class="hero">
  <span class="badge">Emergency backup website</span>
  <h1>Dead Man's Switch Dashboard</h1>
  <p>This page organizes the uploaded Dead Man's Switch material into a person profile, photo gallery, audio clips, location files, timeline, and file archive.</p>
  <div class="buttons">
    <a class="btn primary" href="Pages/profile.html">Open Person Profile</a>
    <a class="btn" href="Pages/gallery.html">Open Photo Gallery</a>
    <a class="btn" href="Pages/videos.html">Open Videos</a>
    <a class="btn" href="Pages/locations.html">Open Locations</a>
    <a class="btn danger" href="Pages/emergency.html">Emergency Instructions</a>
  </div>
</section>
{link_cards}
<section class="grid">
  <div class="card success"><h2>Person</h2><p class="stat" style="font-size:1.25rem">{h(name)}</p><p class="muted">City / area: {h(city)}</p></div>
  <div class="card"><h2>Generated</h2><p class="stat" style="font-size:1.25rem">{h(generated_at)}</p><p class="muted">Rebuilt whenever Dead Man's Switch publishes the static site.</p></div>
</section>
{stat_cards(items)}
<section class="card">
  <h2>Latest indexed files</h2>
  <input class="searchbar" data-search placeholder="Search latest files...">
  <div class="grid">{cards}</div>
</section>
"""
    return site_layout("Dashboard", "dashboard", body, generated_at)

def profile_page(personal: Dict[str, Any], generated_at: str) -> str:
    rows = []
    for key, label in PERSONAL_DETAIL_FIELDS:
        value = str(personal.get(key, "")).strip()
        if value:
            rows.append(f"<tr><th>{h(label)}</th><td>{h(value).replace(chr(10), '<br>')}</td></tr>")
    if not rows:
        rows.append('<tr><th>Status</th><td>No personal details have been added yet.</td></tr>')
    body = f"""
<section class="hero"><span class="badge">Identification</span><h1>Person Profile</h1><p>Information added from the Personal Details menu. This can help trusted people identify the user and understand emergency context.</p></section>
<section class="card warning"><h2>Privacy Warning</h2><p>This profile may become public during I Need Help mode. It should contain emergency identification details only, not account secrets or financial information.</p></section>
<section class="card"><div class="table-wrap"><table class="profile-table"><tbody>{''.join(rows)}</tbody></table></div></section>
"""
    return site_layout("Person Profile", "profile", body, generated_at, in_pages=True)

def gallery_page(items: List[Dict[str, Any]], generated_at: str) -> str:
    photos = [i for i in items if i["kind"] == "Photo"]
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for item in photos:
        grouped.setdefault(item["date"], []).append(item)
    parts = []
    for date, group in grouped.items():
        imgs = "".join(f"""
        <article class="photo-card card" data-filter-card>
          <a href="{h(item['url'])}"><img src="{h(item['url'])}" alt="{h(item['name'])}" loading="lazy"></a>
          <div class="media-meta"><strong>{h(item['name'])}</strong><br>{h(item['date'])} {h(item['time'])}<br>{h(item['folder'])}</div>
          <div class="buttons"><a class="btn primary" href="{h(item['url'])}" download>Download photo</a><a class="btn" href="{h(item['url'])}">Open photo</a></div>
        </article>
        """ for item in group)
        parts.append(f"<h2>{h(date)}</h2><div class=\"gallery\">{imgs}</div>")
    content = "".join(parts) if parts else '<div class="empty">No photos found yet.</div>'
    body = f"""
<section class="hero"><span class="badge">Photos</span><h1>Photo Gallery</h1><p>Photos are grouped by detected date/time from emergency filenames or file modification time.</p></section>
<input class="searchbar" data-search placeholder="Search photos by file name, folder, date...">
{content}
"""
    return site_layout("Photo Gallery", "gallery", body, generated_at, in_pages=True)

def videos_page(items: List[Dict[str, Any]], generated_at: str) -> str:
    videos = [i for i in items if i["kind"] == "Video"]
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for item in videos:
        grouped.setdefault(item["date"], []).append(item)
    parts = []
    for date, group in grouped.items():
        cards = "".join(f"""
        <article class="video-card card" data-filter-card>
          <video controls preload="metadata" src="{h(item['url'])}"></video>
          <div class="media-meta"><strong>{h(item['name'])}</strong><br>{h(item['date'])} {h(item['time'])}<br>{h(item['folder'])}</div>
          <div class="buttons"><a class="btn primary" href="{h(item['url'])}" download>Download video</a><a class="btn" href="{h(item['url'])}">Open video</a></div>
        </article>
        """ for item in group)
        parts.append(f"<h2>{h(date)}</h2><div class=\"gallery\">{cards}</div>")
    content = "".join(parts) if parts else '<div class="empty">No videos found yet. Video capture is optional and depends on whether your Termux setup provides a compatible video command.</div>'
    body = f"""
<section class="hero"><span class="badge">Videos</span><h1>Video Gallery</h1><p>Videos are grouped by detected date/time from emergency filenames or file modification time.</p></section>
<input class="searchbar" data-search placeholder="Search videos by file name, folder, date...">
{content}
"""
    return site_layout("Videos", "videos", body, generated_at, in_pages=True)

def audio_page(items: List[Dict[str, Any]], generated_at: str) -> str:
    audio_items = [i for i in items if i["kind"] == "Audio"]
    rows = []
    for item in audio_items:
        rows.append(f"""
        <article class="card" data-filter-card>
          <span class="pill">{h(item['date'])} {h(item['time'])}</span><span class="pill">{h(item['size_h'])}</span>
          <h3>{h(item['name'])}</h3>
          <audio controls src="{h(item['url'])}"></audio>
          <p class="media-meta">{h(item['folder'])}</p>
          <div class="buttons"><a class="btn primary" href="{h(item['url'])}" download>Download audio</a><a class="btn" href="{h(item['url'])}">Open audio</a></div>
        </article>
        """)
    content = "".join(rows) if rows else '<div class="empty">No audio clips found yet.</div>'
    body = f"""
<section class="hero"><span class="badge">Microphone</span><h1>Audio Clips</h1><p>Audio files captured or uploaded into the Dead Man's Switch folder.</p></section>
<input class="searchbar" data-search placeholder="Search audio by file name, folder, date...">
<div class="audio-list">{content}</div>
"""
    return site_layout("Audio Clips", "audio", body, generated_at, in_pages=True)

def locations_page(items: List[Dict[str, Any]], generated_at: str) -> str:
    loc_items = [i for i in items if i["kind"] == "Location"]
    cards = []
    for item in loc_items:
        lat, lon, maps = read_location_info(LOCAL_DIR / item["rel"])
        map_btn = f'<a class="btn primary" href="{h(maps)}" target="_blank" rel="noopener">Open in Maps</a>' if maps else ''
        coords = f"Latitude: {h(lat)}<br>Longitude: {h(lon)}" if lat and lon else "Coordinates could not be parsed automatically. Open the raw file."
        cards.append(f"""
        <article class="card" data-filter-card>
          <span class="pill">{h(item['date'])} {h(item['time'])}</span>
          <h3>{h(item['name'])}</h3>
          <p class="muted">{coords}</p>
          <div class="buttons">{map_btn}<a class="btn primary" href="{h(item['url'])}" download>Download location file</a><a class="btn" href="{h(item['url'])}">Open raw location file</a></div>
          <p class="media-meta">{h(item['folder'])}</p>
        </article>
        """)
    content = "".join(cards) if cards else '<div class="empty">No location files found yet.</div>'
    body = f"""
<section class="hero"><span class="badge">GPS / Network</span><h1>Locations</h1><p>Location files are listed by detected date/time. When latitude and longitude are readable, a maps button is created.</p></section>
<input class="searchbar" data-search placeholder="Search locations by file name, folder, date...">
<div class="grid">{content}</div>
"""
    return site_layout("Locations", "locations", body, generated_at, in_pages=True)

def timeline_page(items: List[Dict[str, Any]], generated_at: str) -> str:
    events = []
    for item in items:
        events.append(f"""
        <article class="event card" data-filter-card>
          <span class="pill">{h(item['kind'])}</span><span class="pill">{h(item['size_h'])}</span>
          <h3>{h(item['date'])} {h(item['time'])}</h3>
          <p><a href="{h(item['url'])}">{h(item['name'])}</a></p>
          <p class="media-meta">{h(item['folder'])}</p>
          <div class="buttons"><a class="btn primary" href="{h(item['url'])}" download>Download</a><a class="btn" href="{h(item['url'])}">Open</a></div>
        </article>
        """)
    content = "".join(events) if events else '<div class="empty">No timeline events found yet.</div>'
    body = f"""
<section class="hero"><span class="badge">Chronology</span><h1>Timeline</h1><p>All indexed files ordered by detected timestamp, newest first.</p></section>
<input class="searchbar" data-search placeholder="Search timeline...">
<section class="timeline">{content}</section>
"""
    return site_layout("Timeline", "timeline", body, generated_at, in_pages=True)

def files_page(items: List[Dict[str, Any]], generated_at: str) -> str:
    rows = []
    for item in items:
        rows.append(f"""
        <tr data-filter-card>
          <td><span class="pill">{h(item['kind'])}</span></td>
          <td><a href="{h(item['url'])}">{h(item['rel'])}</a></td>
          <td>{h(item['date'])} {h(item['time'])}</td>
          <td>{h(item['size_h'])}</td>
          <td><a class="btn primary" href="{h(item['url'])}" download>Download</a></td>
        </tr>
        """)
    if not rows:
        rows.append('<tr><td colspan="5">No files indexed yet.</td></tr>')
    body = f"""
<section class="hero"><span class="badge">Archive</span><h1>All Files</h1><p>Every non-generated file found in the Dead Man's Switch folder, excluding the website files themselves.</p></section>
<input class="searchbar" data-search placeholder="Search all files...">
<section class="card table-wrap"><table class="file-table"><thead><tr><th>Type</th><th>File</th><th>Date / time</th><th>Size</th><th>Download</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>
"""
    return site_layout("All Files", "files", body, generated_at, in_pages=True)

def emergency_page(items: List[Dict[str, Any]], personal: Dict[str, Any], generated_at: str) -> str:
    name = " ".join(str(personal.get(k, "")).strip() for k in ["first_name", "last_name"]).strip() or "the Dead Man's Switch user"
    body = f"""
<section class="hero"><span class="badge">Read first</span><h1>Emergency Instructions</h1><p>This site is designed to help trusted people quickly review emergency data if something happened to {h(name)}.</p></section>
<section class="grid">
  <div class="card warning"><h2>1. Check the profile</h2><p>Open the person profile first. It may contain identification details, medical notes, allergies, trusted people, and emergency instructions.</p><a class="btn primary" href="Pages/profile.html">Open Profile</a></div>
  <div class="card"><h2>2. Check locations</h2><p>Open the location page and newest timeline entries. If coordinates exist, use the maps button.</p><a class="btn primary" href="Pages/locations.html">Open Locations</a></div>
  <div class="card"><h2>3. Check media</h2><p>Review the newest photos and audio clips. They may show surroundings, time, people, or sounds.</p><a class="btn primary" href="Pages/timeline.html">Open Timeline</a></div>
</section>
<section class="card success"><h2>Important</h2><p>This website is static. It only shows files that were uploaded to this GitHub repository. If emergency mode is still running, refresh the page later to see newer uploads.</p></section>
<section class="card warning"><h2>Privacy and safety</h2><p>Do not share this repository publicly unless it is necessary for the person’s safety. If there is immediate danger, contact local emergency services and trusted contacts directly.</p></section>
"""
    return site_layout("Emergency Instructions", "emergency", body, generated_at, in_pages=True)

def generate_static_website(owner: str = "", pages_url: str = "") -> List[str]:
    """Build/update the static GitHub Pages website files inside LOCAL_DIR. Returns generated rel paths."""
    ensure_folder()
    organize_local_repository_structure()
    assets_dir = site_assets_dir()
    assets_dir.mkdir(parents=True, exist_ok=True)
    generated_at = time.strftime("%Y-%m-%d %H:%M:%S")
    items = scan_site_items(include_generated=False)
    personal = personal_details_for_site(load_personal_details())
    pages_url = pages_url or expected_pages_url(owner)

    pages = {
        "index.html": dashboard_page(items, personal, generated_at, owner, pages_url),
        f"{PAGES_DIR_NAME}/profile.html": profile_page(personal, generated_at),
        f"{PAGES_DIR_NAME}/gallery.html": gallery_page(items, generated_at),
        f"{PAGES_DIR_NAME}/videos.html": videos_page(items, generated_at),
        f"{PAGES_DIR_NAME}/audio.html": audio_page(items, generated_at),
        f"{PAGES_DIR_NAME}/locations.html": locations_page(items, generated_at),
        f"{PAGES_DIR_NAME}/timeline.html": timeline_page(items, generated_at),
        f"{PAGES_DIR_NAME}/files.html": files_page(items, generated_at),
        f"{PAGES_DIR_NAME}/emergency.html": emergency_page(items, personal, generated_at),
        SITE_CSS_NAME: SITE_CSS,
        SITE_JS_NAME: SITE_JS,
    }
    for rel, content in pages.items():
        path = LOCAL_DIR / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    manifest = {
        "app": APP_NAME,
        "repo": REPO_NAME,
        "owner": owner,
        "repository_url": repo_url_for(owner),
        "github_pages_url": pages_url,
        "generated_at": generated_at,
        "total_files_indexed": len(items),
        "counts": {
            "photos": sum(1 for i in items if i["kind"] == "Photo"),
            "videos": sum(1 for i in items if i["kind"] == "Video"),
            "audio": sum(1 for i in items if i["kind"] == "Audio"),
            "locations": sum(1 for i in items if i["kind"] == "Location"),
            "documents": sum(1 for i in items if i["kind"] in {"Document", "Personal profile"}),
        },
        "files": [{k: item[k] for k in ["rel", "kind", "size_h", "date", "time", "updated"]} for item in items],
    }
    (LOCAL_DIR / SITE_ASSETS_DIR_NAME / SITE_MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    generated = sorted(GENERATED_SITE_REL_PATHS)
    print(f"[✓] Static emergency website generated ({len(generated)} file(s)).")
    return generated

def ensure_github_pages(owner: str, branch: str = "") -> str:
    """Return the expected GitHub Pages URL and update README.
    GitHub often requires Pages to be enabled manually from repository Settings > Pages.
    If Pages already exists, this function best-effort updates it/enforces HTTPS without printing raw API errors.
    """
    ensure_repo_scope()
    branch = branch or current_branch() or get_default_branch(owner) or "main"
    pages_url = expected_pages_url(owner)

    rc, out = run_rc(["gh", "api", f"repos/{owner}/{REPO_NAME}/pages", "--jq", ".html_url"], capture=True)
    known = (out or "").strip() if rc == 0 else ""
    if known.startswith("http"):
        pages_url = known
        # Best-effort update existing Pages settings and enforce HTTPS. Ignore failures.
        run_rc([
            "gh", "api", "-X", "PUT", f"repos/{owner}/{REPO_NAME}/pages",
            "-f", f"source[branch]={branch}",
            "-f", "source[path]=/",
            "-F", "https_enforced=true"
        ], capture=True)
        print(f"[✓] GitHub Pages URL: {pages_url}")
    else:
        print("[!] GitHub Pages is not enabled yet or GitHub has not published it yet.")
        print("    Enable it manually in repository Settings > Pages.")
        print(f"    Expected website link after setup: {pages_url}")

    commit_readme_with_pages_url(owner, pages_url)
    print("    It can take a little time for GitHub Pages to finish publishing after a push.")
    return pages_url

def publish_static_website(enable_pages: bool = True) -> str:
    print("\n=== Build / Publish Emergency Website ===")
    ensure_folder()
    ensure_git()
    ensure_gh()
    ensure_logged_in()
    ensure_repo_scope()
    owner = gh_user()
    if not owner:
        print("[!] Could not detect GitHub username.")
        return ""
    ensure_repo_created(owner, get_visibility())
    init_or_use_git_repo()
    set_remote(owner)
    ensure_gitignore()
    sync_local_repo_with_remote(owner)
    pages_url = get_known_or_expected_pages_url(owner)
    readme_path = ensure_readme(owner, pages_url)
    print(f"[*] README created/updated with website link: {readme_path}")
    generated = generate_static_website(owner, pages_url)
    generated = sorted(set(generated) | {"README.md"})
    run(["git", "reset"], cwd=str(LOCAL_DIR), check=False)
    stage_paths(generated, force=True)
    if commit_staged("Build Dead Man's Switch emergency website"):
        if push_current():
            if enable_pages:
                return ensure_github_pages(owner, current_branch())
    else:
        print("[*] Website files already up to date.")
        if enable_pages:
            return ensure_github_pages(owner, current_branch())
    return ""


def clean_repository_menu():
    print("\n=== Clean Repository ===")
    print("[!] This deletes ALL files from the GitHub repository history branch tip.")
    print("[!] It does NOT delete your local Dead Man's Switch folder from your phone.")
    confirm = input("Type DELETE to clean the repository files: ").strip()
    if confirm != "DELETE":
        print("[*] Cancelled.")
        return
    ensure_folder()
    ensure_core_dependencies(include_termux_api=False)
    ensure_logged_in()
    ensure_repo_scope()
    owner = gh_user()
    if not owner:
        print("[!] Could not detect GitHub username.")
        return
    if not repo_exists(owner):
        print(f"[*] Repository does not exist yet: {owner}/{REPO_NAME}")
        return
    init_or_use_git_repo()
    set_remote(owner)
    sync_local_repo_with_remote(owner)
    run(["git", "reset"], cwd=str(LOCAL_DIR), check=False)
    # Remove from Git tracking only. Local phone files stay untouched.
    run(["git", "rm", "-r", "--cached", "--ignore-unmatch", "."], cwd=str(LOCAL_DIR), check=False)
    if commit_staged("Clean Dead Man's Switch repository files"):
        if push_current():
            print(f"[✓] Repository files cleaned: https://github.com/{owner}/{REPO_NAME}")
        else:
            print("[!] Clean commit was created, but push failed. Re-run after fixing GitHub sync.")
    else:
        print("[*] No tracked repository files needed cleaning.")

def print_header():
    enforce_final_repo_name_runtime()
    if os.environ.get("TERM"):
        os.system("clear")
    print("===================================")
    print(f" {APP_NAME} (Termux, no root)")
    print("===================================")
    print(f"Local folder: {LOCAL_DIR} (resolved: {LOCAL_DIR.resolve()})  (downloads: {DOWNLOADS_DIR})")
    print(f"Log file    : {get_log_file_path()}")
    print(f"GitHub repo : {FINAL_REPO_NAME} (preference: {get_visibility().upper()})")
    print(f"Version     : {APP_VERSION}")
    print(f"Script file : {Path(__file__).resolve()}")
    print("Upload rules:")
    print(" - Missing Termux packages install automatically only when needed.")
    print(" - Each batch push <= 40MB total; any single file > 40MB is skipped.")
    print(" - Before normal repository publishes, the previous snapshot is zipped in History/.")
    print(" - Repository cleanup removes old Git-tracked files from the repo, not from your phone storage.")
    print("Modes:")
    print(" - Create/Update: archives previous snapshot, rebuilds README + GitHub Pages, uploads current files.")
    print(" - I Need Help: first-time setup, queues existing local files, emergency capture, auto-upload, SMS alert, public website.")
    print("Login persists via GitHub CLI in Termux HOME (~/.config/gh).")
    print("")

def menu():
    while True:
        print_header()
        print("1) Dead Man's Switch Repository")
        print("2) I Need Help")
        print("3) Settings")
        print("4) Clean Repository")
        print("5) Exit")
        choice = input("\nSelect: ").strip()

        if choice == "1":
            create_switch_only_new()
            input("\nPress Enter to continue...")
        elif choice == "2":
            help_mode()
            input("\nPress Enter to continue...")
        elif choice == "3":
            settings_menu()
        elif choice == "4":
            clean_repository_menu()
            input("\nPress Enter to continue...")
        elif choice == "5":
            print("Bye.")
            return
        else:
            print("[!] Invalid choice.")
            input("\nPress Enter to continue...")

def show_cli_help():
    print(f"{APP_NAME} - Termux GitHub Dead Man's Switch helper")
    print("")
    print("Usage:")
    print("  python \"Dead Man's Switch.py\"               Open menu")
    print("  python \"Dead Man's Switch.py\" --create        Create/update repository, website, README, history")
    print("  python \"Dead Man's Switch.py\" --i-need-help   Run first-time setup if needed, show Pages guide, then start emergency mode")
    print("  python \"Dead Man's Switch.py\" --settings      Open Settings")
    print("  python \"Dead Man's Switch.py\" --personal      Open Personal Details menu")
    print("  python \"Dead Man's Switch.py\" --visibility public|private")
    print("  python \"Dead Man's Switch.py\" --widget        Create/update Termux Widget")
    print("  python \"Dead Man's Switch.py\" --delete-widget Delete Termux Widget")
    print(f"\nLogs are saved in: {get_log_file_path()}")

def cli_entry():
    if "--create" in sys.argv:
        create_switch_only_new()
        return True
    if "--notify" in sys.argv:
        create_notification()
        return True
    if "--visibility" in sys.argv:
        try:
            idx = sys.argv.index("--visibility")
            val = sys.argv[idx+1] if idx+1 < len(sys.argv) else ""
        except Exception:
            val = ""
        if val:
            set_visibility(val)
        else:
            print("[!] Usage: --visibility public OR --visibility private")
        return True
    if "--i-need-help" in sys.argv or "--help-mode" in sys.argv:
        help_mode()
        return True
    if "--settings" in sys.argv:
        settings_menu()
        return True
    if "--clean" in sys.argv or "--clean-repo" in sys.argv:
        clean_repository_menu()
        return True
    if "--personal" in sys.argv or "--personal-details" in sys.argv:
        configure_personal_details()
        return True
    if "--create-widget" in sys.argv or "--widget" in sys.argv:
        create_termux_widget()
        return True
    if "--delete-widget" in sys.argv:
        delete_termux_widget()
        return True
    if "--help" in sys.argv or "-h" in sys.argv:
        show_cli_help()
        return True
    return False


if __name__ == "__main__":
    setup_runtime_logging()
    try:
        if not cli_entry():
            menu()
    except KeyboardInterrupt:
        append_log("STOP", "KeyboardInterrupt / Ctrl+C received")
        print("\nBye.")
    except Exception:
        log_exception("Fatal unhandled error")
        print(f"\n[!] Fatal error saved in log file: {get_log_file_path()}")
        raise
