# Greek visible-language version generated from the uploaded Dead Man's Switch.py. Logic/commands/repo names are preserved.
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
        log(f"[!] Το όνομα repo διορθώθηκε στο runtime από {REPO_NAME!r} to {FINAL_REPO_NAME!r}") if 'log' in globals() else None
        REPO_NAME = FINAL_REPO_NAME
    return FINAL_REPO_NAME


def resolve_downloads_dir() -> Path:
    home = Path.home()
    candidates = [
        home / "storage" / "downloads",
        Path("/storage/emulated/0/Λήψη"),
        Path("/sdcard/Λήψη"),
    ]
    for c in candidates:
        if c.exists():
            return c
    return Path("/storage/emulated/0/Λήψη")

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
PERSONAL_DETAILS_JSON_NAME = "Άτομοal_Details.json"
PERSONAL_DETAILS_TXT_NAME = "Άτομοal_Details.txt"
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
    append_log("START", f"Το Dead Man's Switch ξεκίνησε | script={Path(__file__).resolve()} | python={sys.version.split()[0]} | cwd={Path.cwd()}")
    sys.stdout = TeeStream(_ORIGINAL_STDOUT, "stdout")
    sys.stderr = TeeStream(_ORIGINAL_STDERR, "stderr")
    print(f"[*] Αρχείο log: {RUN_LOG_FILE}")

def get_log_file_path() -> Path:
    ensure_logs_dir()
    return RUN_LOG_FILE

README_TEXT = """# Dead Man's Switch (Νεκροδιακόπτης)

Ένας *dead man's switch* είναι μηχανισμός ασφαλείας που ενεργοποιεί μια ενέργεια όταν ο χειριστής δεν μπορεί πλέον να συνεχίσει — για παράδειγμα όταν σταματήσει να κάνει check-in.

Με απλά λόγια: αν ένα άτομο δεν μπορεί να επιβεβαιώσει ότι είναι καλά, το σύστημα μπορεί να αποκαλύψει οδηγίες, να μεταφέρει πρόσβαση, να στείλει ειδοποιήσεις ή να δημοσιεύσει πληροφορίες.

Αυτό το repository μπορεί να χρησιμοποιηθεί ως backup concept για dead man's switch:
- Κράτα εδώ σημαντικά έγγραφα, οδηγίες ή αρχεία.
- Ενημέρωνέ το όποτε χρειάζεται.
- Μπορείς να αυτοματοποιήσεις check-ins και ενέργειες ξεχωριστά, έξω από αυτό το script.

> Αυτό το script **δεν** υλοποιεί μόνο του την αυτόματη ενεργοποίηση.
> Συγχρονίζει τον τοπικό φάκελό σου στο GitHub και προαιρετικά μπορεί να κάνει wipe/delete το repo.
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
        print("[!] Μη έγκυρη ορατότητα. Χρησιμοποίησε public/private.")
        return
    settings = load_settings()
    settings["visibility"] = vis
    save_settings(settings)
    print(f"[✓] Αποθηκεύτηκε η προτίμηση ορατότητας repo: {vis.upper()}")

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
        print("[!] Το storage του Termux δεν έχει ρυθμιστεί ακόμα (δεν υπάρχει πρόσβαση στον κοινόχρηστο χώρο).")
        print("    Εκτέλεση: termux-setup-storage")
        run(["termux-setup-storage"], check=False)
        print("\n    Allow the permission prompt, then re-run the script.")
        sys.exit(1)

def ensure_folder():
    ensure_termux_storage()
    if not LOCAL_DIR.exists():
        print(f"[*] Δημιουργία φακέλου: {LOCAL_DIR}")
        LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    else:
        print(f"[*] Ο φάκελος υπάρχει ήδη: {LOCAL_DIR}")

def ensure_pkg(bin_name, pkg_name=None):
    """Install a Termux package only when the required command is missing."""
    global PKG_UPDATED_ONCE
    if which(bin_name):
        return True
    if not which("pkg"):
        print(f"[!] Λείπει η εντολή: {bin_name}")
        print("    Η αυτόματη εγκατάσταση χρειάζεται την εντολή pkg του Termux.")
        return False
    pkg_name = pkg_name or bin_name
    print(f"[*] {bin_name} λείπει. Εγκατάσταση πακέτου: {pkg_name}")
    if not PKG_UPDATED_ONCE:
        run(["pkg", "update", "-y"], check=False)
        PKG_UPDATED_ONCE = True
    run(["pkg", "install", "-y", pkg_name], check=False)
    if which(bin_name):
        print(f"[✓] Εγκατεστημένο/διαθέσιμο: {bin_name}")
        return True
    print(f"[!] {bin_name} λείπει ακόμα μετά την προσπάθεια εγκατάστασης του {pkg_name}.")
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
    print("[*] Λείπουν εντολές Termux:API: " + ", ".join(missing))
    ensure_pkg("termux-notification", "termux-api")
    still_missing = [cmd for cmd in needed_commands if not which(cmd)]
    if still_missing:
        print("[!] Κάποιες εντολές Termux:API λείπουν ακόμα: " + ", ".join(still_missing))
        print("    Εγκατέστησε και την εφαρμογή Termux:API και δώσε άδειες όταν τις ζητήσει το Android.")
        print("    Εντολή πακέτου: pkg install termux-api")
        return False
    print("[✓] Οι εντολές Termux:API είναι διαθέσιμες.")
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
    print("\nΚατάσταση:")
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
    print("[*] Έλεγχος κατάστασης σύνδεσης GitHub...")
    ok = subprocess.run(["gh", "auth", "status"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if ok:
        print("[*] GitHub: είσαι ήδη συνδεδεμένος (αποθηκευμένο στο HOME του Termux).")
        return
    print("\n[!] You are not logged in to GitHub CLI (gh).")
    print("    Εκκίνηση σύνδεσης μέσω συσκευής/web (μοντέρνο, χωρίς κωδικό).")
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
    print(f"[*] Λείπουν δικαιώματα GitHub token: {', '.join(missing)}")
    print("[*] Ζήτηση επιπλέον δικαιωμάτων (μία φορά)...")
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

    Σημαντικό: GitHub keeps redirects after a repository rename. When asking for
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

    print(f"[*] Μετονομασία repository: {owner}/{old_name} -> {owner}/{new_name}")
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
                print(f"[!] Η προσπάθεια μετονομασίας απέτυχε: {short}")

    # GitHub can take a moment to update names/redirects.
    for _ in range(12):
        time.sleep(0.8)
        actual_new = repo_actual_name(owner, new_name)
        if actual_new.lower() == new_name.lower():
            # If querying the old name now redirects to new_name, that is success.
            actual_old = repo_actual_name(owner, old_name)
            if not actual_old or actual_old.lower() != old_name.lower():
                print(f"[✓] Το repository μετονομάστηκε: {owner}/{old_name} -> {owner}/{new_name}")
                return True
            # If both exist with exact names, rename did not happen.
        
    print(f"[!] Η επαλήθευση μετονομασίας repository απέτυχε: {owner}/{old_name} -> {owner}/{new_name}")
    print("    Άνοιξε το αρχείο log για το ακριβές σφάλμα GitHub CLI/API.")
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

    print(f"[*] Δημιουργία αντιγράφου των παλιών αρχείων repository πριν τη διαγραφή: {owner}/{old_name}")
    attempts = [
        ["gh", "repo", "clone", f"{owner}/{old_name}", str(clone_dir), "--", "--depth", "1"],
        ["git", "clone", "--depth", "1", f"https://github.com/{owner}/{old_name}.git", str(clone_dir)],
    ]
    for cmd in attempts:
        rc, out = run_rc(cmd, capture=True)
        append_log("LEGACY_CLONE_ATTEMPT", f"rc={rc} | {command_to_text(cmd)}\n{out}")
        if rc == 0 and clone_dir.exists():
            print(f"[✓] Το παλιό repository έγινε clone τοπικά για μεταφορά: {clone_dir}")
            return clone_dir
    print("[!] Δεν μπόρεσα να κάνω clone το παλιό repository. Συνέχεια μόνο με τα τοπικά αρχεία φακέλου.")
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
        with zipfile.ZipΑρχείο(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
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
                zf.writestr("EMPTY_OLD_REPOSITORY.txt", f"Δεν βρέθηκαν αρχεία στο {old_name} before deletion.\n")
            zf.writestr("MIGRATION_INFO.txt", f"Old repository: {old_name}\nΝέο repository: {REPO_NAME}\nCreated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(f"[✓] Αποθηκεύτηκε backup παλιού repository: {zip_path.relative_to(LOCAL_DIR).as_posix()}")
        return zip_path.relative_to(LOCAL_DIR).as_posix()
    except Exception:
        log_exception("zip_legacy_clone_to_history")
        print("[!] Δεν μπόρεσα να δημιουργήσω zip backup παλιού repository. Συνέχεια.")
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
        print(f"[✓] Αντιγράφηκαν {copied} αρχείο/α που έλειπαν από το παλιό repository στον τοπικό φάκελο.")
    return copied

def wipe_legacy_repo_files_before_delete(clone_dir: Path, old_name: str) -> None:
    """Best-effort cleanup commit on the old repo before deleting it."""
    if not clone_dir or not clone_dir.exists() or not (clone_dir / ".git").exists():
        return
    print(f"[*] Καθαρισμός αρχείων από το παλιό repository πριν τη διαγραφή: {old_name}")
    try:
        run(["git", "config", "user.name", "dead-mans-switch-termux"], cwd=str(clone_dir), check=False)
        run(["git", "config", "user.email", "dead-mans-switch@localhost"], cwd=str(clone_dir), check=False)
        run(["git", "rm", "-r", "--ignore-unmatch", "."], cwd=str(clone_dir), check=False)
        (clone_dir / ".gitkeep").write_text(f"Το παλιό repository καθαρίστηκε πριν τη μεταφορά στο {REPO_NAME}.\n", encoding="utf-8")
        run(["git", "add", "-A"], cwd=str(clone_dir), check=False)
        rc, out = run_rc(["git", "commit", "-m", f"Καθαρισμός παλιού repository πριν τη μεταφορά στο {REPO_NAME}"], cwd=str(clone_dir), capture=True)
        append_log("LEGACY_WIPE_COMMIT", f"rc={rc}\n{out}")
        # Push even if commit said nothing changed; it is harmless and verifies access.
        rc, out = run_rc(["git", "push", "origin", "HEAD", "--force-with-lease"], cwd=str(clone_dir), capture=True)
        append_log("LEGACY_WIPE_PUSH", f"rc={rc}\n{out}")
        if rc == 0:
            print("[✓] Τα αρχεία του παλιού repository καθαρίστηκαν πριν τη διαγραφή.")
        else:
            print("[!] Δεν μπόρεσα να κάνω push το cleanup commit του παλιού repo. Συνέχεια στη διαγραφή του παλιού repo.")
    except Exception:
        log_exception("wipe_legacy_repo_files_before_delete")
        print("[!] Ο καθαρισμός παλιού repo απέτυχε. Συνέχεια στη διαγραφή του παλιού repo.")

def delete_legacy_repo_named(owner: str, old_name: str) -> bool:
    """Delete a specific old repo name without touching REPO_NAME."""
    if not owner or not old_name:
        return False
    print(f"[*] Διαγραφή παλιού repository: {owner}/{old_name}")
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
            print(f"[✓] Το παλιό repository διαγράφηκε: {owner}/{old_name}")
            return True
    print(f"[!] Δεν μπόρεσα να διαγράψω το παλιό repository: {owner}/{old_name}")
    print("    Έλεγξε τα δικαιώματα GitHub και το αρχείο log για το ακριβές σφάλμα.")
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

    print(f"[*] Εντοπίστηκε παλιό repository: {owner}/{old_name}")
    print(f"[*] Λειτουργία μεταφοράς: διαγραφή παλιού repo και χρήση/δημιουργία {owner}/{REPO_NAME}")

    clone_dir = clone_legacy_repo_for_migration(owner, old_name)
    if clone_dir and clone_dir.exists():
        zip_legacy_clone_to_history(clone_dir, old_name)
        copy_missing_legacy_files_to_local(clone_dir)
        wipe_legacy_repo_files_before_delete(clone_dir, old_name)

    if not delete_legacy_repo_named(owner, old_name):
        print("[!] Η μεταφορά σταμάτησε επειδή το παλιό repository δεν μπόρεσε να διαγραφεί.")
        print("    Δεν θα δημιουργηθεί διπλό repo όσο υπάρχει ακόμα το παλιό.")
        return False

    try:
        if clone_dir and clone_dir.exists():
            shutil.rmtree(clone_dir.parent, ignore_errors=True)
    except Exception:
        pass

    if repo_exists_named(owner, REPO_NAME, exact=True):
        print(f"[✓] Το επίσημο repository υπάρχει ήδη: {owner}/{REPO_NAME}")
        return True

    print(f"[*] Το παλιό repo αφαιρέθηκε. Τώρα θα δημιουργηθεί το επίσημο repo: {owner}/{REPO_NAME}")
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
        raise RuntimeError("Εντοπίστηκε παλιό repository, αλλά δεν μπόρεσε να μετονομαστεί. Η δημιουργία νέου repository σταμάτησε για να αποφευχθούν διπλότυπα.")
    if repo_state is None:
        print(f"[*] Δημιουργία {visibility.upper()} repo: {owner}/{REPO_NAME}")
        private_flag = "true" if visibility == "private" else "false"
        run(["gh", "api", "-X", "POST", "user/repos",
             "-f", f"name={REPO_NAME}",
             "-f", f"private={private_flag}",
             "-f", "auto_init=false"], check=True)
        print("[*] Το repo δημιουργήθηκε.")
    else:
        print(f"[*] Το repo υπάρχει: {owner}/{REPO_NAME}")
    private_flag = "true" if visibility == "private" else "false"
    run(["gh", "api", "-X", "PATCH", f"repos/{owner}/{REPO_NAME}", "-f", f"private={private_flag}"], check=False, capture=True)
    edit_args = ["gh", "repo", "edit", f"{owner}/{REPO_NAME}", "--visibility", visibility, "--accept-visibility-change-consequences"]
    run(edit_args, check=False, capture=True)

def init_or_use_git_repo():
    ensure_git_safe_directory()
    ensure_git_identity()
    if not (LOCAL_DIR / ".git").exists():
        print("[*] Αρχικοποίηση τοπικού git repo...")
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
        alt1 = Path("/storage/emulated/0/Λήψη") / APP_NAME
        alt2 = Path("/sdcard/Λήψη") / APP_NAME
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
        print(f"[*] Συγχρονισμός τοπικού repo με remote branch: {branch_to_track}")
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
    print("\n=== GitHub Pages setup before Χρειάζομαι Βοήθεια starts ===")
    print("Το GitHub μπορεί να απαιτεί χειροκίνητη ενεργοποίηση των Pages από το website/app.")
    print("Κάνε αυτό μία φορά πριν ξεκινήσει η καταγραφή έκτακτης ανάγκης:")
    print("  1) Άνοιξε τις ρυθμίσεις του repository:")
    print(f"     {settings_url}")
    print("  2) Πήγαινε: Settings > Pages")
    print("  3) Source: Deploy from a branch")
    print("  4) Branch: main")
    print("  5) Folder: / (root)")
    print("  6) Πάτα Save")
    print("  7) Ενεργοποίησε το Enforce HTTPS αν το εμφανίζει το GitHub")
    print("  8) Περίμενε μέχρι το GitHub να πει ότι το site δημοσιεύτηκε")
    print(f"\nExpected website link: {pages_url}")
    if repo_url:
        print(f"Link repository: {repo_url}")
    if which("termux-open-url") and settings_url.startswith("http"):
        open_now = input("\nΆνοιγμα GitHub Pages settings in browser now? (y/N): ").strip().lower()
        if open_now == "y":
            run(["termux-open-url", settings_url], check=False)
    print("\nOnly continue after Pages is enabled or if you accept that the website may show 404 until you enable it.")

def build_readme_text(owner: str = "", pages_url: str = "") -> str:
    owner = (owner or "").strip()
    repo_url = repo_url_for(owner)
    pages_url = (pages_url or expected_pages_url(owner) or "Δεν έχει δημοσιευτεί ακόμα").strip()
    generated_at = time.strftime("%Y-%m-%d %H:%M:%S")
    link_section = f"""# Dead Man's Switch

**Ιστοσελίδα GitHub Pages:** {pages_url}
**Repository:** {repo_url or 'Άγνωστο μέχρι να εντοπιστεί σύνδεση GitHub'}
**Τελευταία ενημέρωση README:** {generated_at}

Αυτό το repository δημιουργείται και συντηρείται από το `Dead Man's Switch.py`. Η ιστοσελίδα GitHub Pages είναι η βασική φιλική προς έκτακτη ανάγκη προβολή: οργανώνει στοιχεία προφίλ, φωτογραφίες, ήχο, τοποθεσίες, εγγραφές timeline, έγγραφα και όλα τα ανεβασμένα αρχεία σε απλές στατικές σελίδες.

Αν το link της ιστοσελίδας GitHub Pages δείχνει 404, ενεργοποίησε χειροκίνητα τα GitHub Pages στις ρυθμίσεις του repository: Settings → Pages → Source: Deploy from a branch → Branch: main → Folder: / (root) → Save → Enforce HTTPS.

## Τι να ανοίξεις πρώτο

1. Άνοιξε την ιστοσελίδα GitHub Pages από πάνω.
2. Ξεκίνα από το `Προφίλ Ατόμου` για να ταυτοποιήσεις το άτομο και να διαβάσεις στοιχεία έκτακτης ανάγκης.
3. Έλεγξε το `Τοποθεσίες` για αποθηκευμένα αρχεία τοποθεσίας GPS/network και map links.
4. Έλεγξε το `Συλλογή Φωτογραφιών` και το `Ήχος` για emergency captures.
5. Έλεγξε το `Χρονολόγιο` για να καταλάβεις τι έγινε ανά ημερομηνία και ώρα.
6. Έλεγξε το `Όλα τα Αρχεία` για κάθε ανεβασμένο αρχείο που δεν είναι μέρος του ίδιου του website.
7. Διάβασε το `Πληροφορίες Έκτακτης Ανάγκης` για οδηγίες και προειδοποιήσεις.

## Σημαντικές σημειώσεις ασφαλείας

- Η λειτουργία έκτακτης ανάγκης μπορεί να κάνει αυτό το repository **public** ώστε να έχουν πρόσβαση οι έμπιστες επαφές.
- Μην αποθηκεύεις **ποτέ** εδώ κωδικούς, στοιχεία τράπεζας/κάρτας, crypto seed phrases, private keys ή account secrets.
- Αυτό το project δεν αντικαθιστά τις υπηρεσίες έκτακτης ανάγκης. Αν κάποιος μπορεί να κινδυνεύει, επικοινώνησε αμέσως με τις τοπικές υπηρεσίες έκτακτης ανάγκης.
- Το website είναι στατικό. Κάνε refresh αργότερα αν η λειτουργία έκτακτης ανάγκης ανεβάζει ακόμα νέα δεδομένα.

## Τοπικός φάκελος που χρησιμοποιεί το script

`{LOCAL_DIR}`

## Δημιουργημένες σελίδες website

- `index.html` — dashboard
- `Pages/profile.html` — προσωπική ταυτοποίηση/προφίλ
- `Pages/gallery.html` — φωτογραφίες ομαδοποιημένες από τα ανεβασμένα αρχεία
- `Pages/videos.html` — βίντεο ομαδοποιημένα από τα ανεβασμένα αρχεία
- `Pages/audio.html` — ηχογραφήσεις
- `Pages/locations.html` — αρχεία τοποθεσίας και map links όταν υπάρχουν συντεταγμένες
- `Pages/timeline.html` — αρχεία οργανωμένα ανά ημερομηνία/ώρα
- `Pages/files.html` — πλήρες αρχείο αρχείων
- `Pages/emergency.html` — οδηγίες έκτακτης ανάγκης

## Προηγούμενο Ιστορικό

Πριν από κανονικές δημοσιεύσεις στο repository, το προηγούμενο repository/τοπικό snapshot πακετάρεται σε zip με ημερομηνία μέσα στο `History/`. Μετά το script καθαρίζει το Git tracking και ανεβάζει το νέο τρέχον snapshot, κρατώντας τα history zips. Τα τοπικά αρχεία του τηλεφώνου **δεν** διαγράφονται από αυτόν τον καθαρισμό· ανανεώνεται μόνο το index του Git repository.

## Δομή repository

- `index.html`, `style.css`, `scripts.js`, `README.md` μένουν στο root του repository.
- `Pages/` περιέχει κάθε σελίδα του website εκτός από το κύριο `index.html`.
- `Assets/Φωτογραφίαs/`, `Assets/Βίντεο/`, `Assets/Recordings/`, `Assets/Τοποθεσίες/`, `Assets/Profile/`, `Assets/Sessions/`, and `Assets/Other/` κρατούν τα ανεβασμένα δεδομένα.
- `History/` περιέχει zip snapshots προηγούμενων εκδόσεων.

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
        if commit_staged("Ενημέρωση README με link GitHub Pages"):
            push_current()
    except Exception as e:
        print(f"[!] Δεν μπόρεσα να ενημερώσω το README με το τελικό Pages link: {e}")

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
        print("[!] Το git commit απέτυχε.")
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
    print("[*] Γίνεται push στο GitHub...")
    rc, out = run_rc(["git", "push", "-u", "origin", head], cwd=str(LOCAL_DIR), capture=True)
    if rc == 0:
        return True

    out = out or ""
    non_fast_forward = ("non-fast-forward" in out.lower() or "fetch first" in out.lower() or "rejected" in out.lower())
    if non_fast_forward:
        print("[!] Το remote branch είναι πιο μπροστά. Γίνεται fetch και ασφαλής επανάληψη με --force-with-lease...")
        run(["git", "fetch", "origin", "--prune"], cwd=str(LOCAL_DIR), check=False)
        rc2, out2 = run_rc(["git", "push", "--force-with-lease", "-u", "origin", head], cwd=str(LOCAL_DIR), capture=True)
        if rc2 == 0:
            print("[✓] Το push πέτυχε μετά από ασφαλή επανάληψη.")
            return True
        print("[!] Η επανάληψη git push απέτυχε.")
        if out2:
            print(out2)
        return False

    print("[!] Το git push απέτυχε.")
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
    f"{SITE_ASSETS_DIR_NAME}/Φωτογραφίαs",
    f"{SITE_ASSETS_DIR_NAME}/Βίντεο",
    f"{SITE_ASSETS_DIR_NAME}/Recordings",
    f"{SITE_ASSETS_DIR_NAME}/Τοποθεσίες",
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
    if kind == "Φωτογραφία":
        return f"{SITE_ASSETS_DIR_NAME}/Φωτογραφίαs"
    if kind == "Βίντεο":
        return f"{SITE_ASSETS_DIR_NAME}/Βίντεο"
    if kind == "Ήχος":
        return f"{SITE_ASSETS_DIR_NAME}/Recordings"
    if kind == "Τοποθεσία":
        return f"{SITE_ASSETS_DIR_NAME}/Τοποθεσίες"
    if kind == "Emergency session":
        return f"{SITE_ASSETS_DIR_NAME}/Sessions"
    if kind == "Προσωπικό προφίλ":
        return f"{SITE_ASSETS_DIR_NAME}/Profile"
    return f"{SITE_ASSETS_DIR_NAME}/Other"

def organize_local_repository_structure() -> None:
    """Move script-managed files into a clear repo structure.

    Root: index.html, style.css, scripts.js, README.md
    Assets/: Φωτογραφίαs, Βίντεο, Recordings, Τοποθεσίες, Sessions, Profile, Other
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

    with zipfile.ZipΑρχείο(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
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
        print(f"[✓] Η προηγούμενη έκδοση έγινε zip: {rel_zip} ({human_size(size)})")
        if size > MAX_FILE_BYTES:
            print(f"[!] Το zip ιστορικού είναι μεγαλύτερο από {MAX_FILE_BYTES/(1024*1024):.0f}MB και μπορεί να παραλειφθεί από τα upload batches.")
    except Exception:
        print(f"[✓] Η προηγούμενη έκδοση έγινε zip: {rel_zip}")
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
                print(f"[!] Παράλειψη υπερβολικά μεγάλου zip ιστορικού: {rel} ({human_size(path.stat().st_size)})")
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
        if commit_staged(f"Αρχείο previous version before {reason}"):
            push_current()
        else:
            print("[*] Δεν χρειάστηκε commit καθαρισμού/ιστορικού repository.")
    return rel_zip

def build_current_repository_snapshot(owner: str, pages_url: str, reason: str) -> List[Tuple[str, int]]:
    """Generate README/site, clean Git index, and return current upload candidates."""
    organize_local_repository_structure()
    ensure_readme(owner, pages_url)
    generate_static_website(owner, pages_url)
    run(["git", "reset"], cwd=str(LOCAL_DIR), check=False)
    run(["git", "rm", "-r", "--cached", "--ignore-unmatch", "."], cwd=str(LOCAL_DIR), check=False)
    local_items = list_local_files()
    print(f"[*] Εντοπίστηκαν αρχεία στο τρέχον τοπικό snapshot: {len(local_items)}")
    skipped_large = [(rel, size) for rel, size in local_items if size > MAX_FILE_BYTES]
    report_skips(skipped_large)
    candidates = [(rel, size) for rel, size in local_items if size <= MAX_FILE_BYTES]
    if not candidates:
        print("[!] Δεν βρέθηκαν αρχεία κάτω από το όριο upload.")
    else:
        print(f"[*] Ετοιμάστηκε καθαρό repository snapshot για: {reason}")
    return candidates

def create_switch_only_new():
    print("\n=== Create / Update Switch Repository ===")
    ensure_folder()
    ensure_core_dependencies(include_termux_api=False)
    ensure_logged_in()
    ensure_repo_scope()
    owner = gh_user()
    if not owner:
        print("[!] Δεν μπόρεσα να εντοπίσω το GitHub username.")
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
    print(f"[*] Upload καθαρού snapshot: {len(candidates)} αρχείο/α σε {len(batches)} batch(es).")
    uploaded = 0
    for i, batch in enumerate(batches, start=1):
        batch_paths = [rel for rel, _ in batch]
        batch_bytes = sum(size for _, size in batch)
        print(f"\n[*] Batch {i}/{len(batches)}: {len(batch_paths)} file(s), {batch_bytes/(1024*1024):.2f} MB")
        stage_paths(batch_paths, force=True)
        if not commit_staged(f"Publish current Dead Man's Switch snapshot batch {i}/{len(batches)}"):
            print("[*] Δεν άλλαξε κάτι σε αυτό το batch.")
            continue
        if not push_current():
            print("[!] Διακοπή επειδή το push απέτυχε. Διόρθωσε το πρόβλημα και ξανατρέξε το script.")
            return
        uploaded += len(batch_paths)
    pages_url = ensure_github_pages(owner, current_branch())
    print(f"\n[✓] Done. Published {uploaded} αρχείο/α. Repo: https://github.com/{owner}/{REPO_NAME}")
    print(f"[✓] Ιστοσελίδα: {pages_url}")

def overwrite_repository_batched():
    print("\n=== Force Full Repository Refresh ===")
    ensure_folder()
    ensure_core_dependencies(include_termux_api=False)
    ensure_logged_in()
    ensure_repo_scope()
    owner = gh_user()
    if not owner:
        print("[!] Δεν μπόρεσα να εντοπίσω το GitHub username.")
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
    print(f"[*] Upload ανανεωμένου snapshot: {len(candidates)} αρχείο/α σε {len(batches)} batch(es).")
    committed_any = False
    for i, batch in enumerate(batches, start=1):
        batch_paths = [rel for rel, _ in batch]
        batch_bytes = sum(size for _, size in batch)
        print(f"\n[*] Batch {i}/{len(batches)}: {len(batch_paths)} file(s), {batch_bytes/(1024*1024):.2f} MB")
        stage_paths(batch_paths, force=True)
        if commit_staged(f"Refresh current Dead Man's Switch snapshot batch {i}/{len(batches)}"):
            committed_any = True
            if not push_current():
                print("[!] Διακοπή επειδή το push απέτυχε. Διόρθωσε το πρόβλημα και ξανατρέξε το script.")
                return
        else:
            print("[*] Δεν άλλαξε κάτι σε αυτό το batch.")
    pages_url = ensure_github_pages(owner, current_branch())
    if committed_any:
        print(f"\n[✓] Done. Repo: https://github.com/{owner}/{REPO_NAME}")
    else:
        print("\n[*] No changes detected to upload after refresh.")
    print(f"[✓] Ιστοσελίδα: {pages_url}")

def wipe_repo_files(owner):
    print("[*] Wipe αρχείων repository (empty commit)...")
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
    print("[*] Τα περιεχόμενα του repo έγιναν wipe (best effort).")

def ensure_delete_scope():
    print("[*] Έλεγχος δικαιωμάτων διαγραφής (delete_repo)...")
    ensure_scopes(["delete_repo", "repo"])

def delete_repo(owner):
    print(f"[*] Διαγραφή repo: {owner}/{REPO_NAME}")
    ensure_delete_scope()
    rc = subprocess.run(["gh", "repo", "delete", f"{owner}/{REPO_NAME}", "--yes"],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).returncode
    if rc != 0:
        run(["gh", "api", "-X", "DELETE", f"repos/{owner}/{REPO_NAME}"], check=False)
    if repo_exists(owner):
        print("[!] Το repo υπάρχει ακόμα.")
        print("    Δοκίμασε χειροκίνητα:")
        print("    gh auth refresh -h github.com -s delete_repo -s repo")
        print(f"    gh repo delete {owner}/{REPO_NAME} --yes")
    else:
        print("[✓] Το repo διαγράφηκε.")

def kill_switch():
    print("\n=== Kill Switch (Wipe + Delete Repo) ===")
    ensure_folder()
    ensure_core_dependencies(include_termux_api=False)
    ensure_logged_in()
    ensure_repo_scope()
    owner = gh_user()
    if not owner:
        print("[!] Δεν μπόρεσα να εντοπίσω το GitHub username.")
        return
    if not repo_exists(owner):
        print(f"[*] Το repo δεν υπάρχει: {owner}/{REPO_NAME}")
        return
    try:
        wipe_repo_files(owner)
    except Exception:
        print("[!] Δεν μπόρεσα να κάνω πλήρες wipe αρχείων (συνέχεια με διαγραφή repo έτσι κι αλλιώς).")
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
        "--content", f"Διάλεξε ενέργεια (repo {get_visibility().upper()}):",
        "--button1", "Δημιουργία/Ενημέρωση",
        "--button1-action", create_cmd,
        "--button2", "Χρειάζομαι Βοήθεια",
        "--button2-action", help_cmd,
        "--ongoing"
    ], check=False)
    print("[✓] Δημιουργήθηκε ειδοποίηση με κουμπιά Δημιουργία/Ενημέρωση και Χρειάζομαι Βοήθεια.")
    print("    Η λειτουργία Χρειάζομαι Βοήθεια απαιτεί ακόμα δύο ορατές επιβεβαιώσεις Enter πριν ενεργοποιηθεί.")

def ensure_termux_camera():
    if not which("termux-camera-photo"):
        ensure_termux_api()
        if not which("termux-camera-photo"):
            print("[!] Δεν βρέθηκε το termux-camera-photo. Εγκατέστησε την εφαρμογή Termux:API και το πακέτο termux-api.")
            return False
    return True

def ensure_termux_microphone():
    if not which("termux-microphone-record"):
        ensure_termux_api()
        if not which("termux-microphone-record"):
            print("[!] Δεν βρέθηκε το termux-microphone-record. Εγκατέστησε την εφαρμογή Termux:API και το πακέτο termux-api.")
            return False
    return True

def ensure_termux_location():
    if not which("termux-location"):
        ensure_termux_api()
        if not which("termux-location"):
            print("[!] Δεν βρέθηκε το termux-location. Εγκατέστησε την εφαρμογή Termux:API και το πακέτο termux-api.")
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
    print("[!] Δεν βρέθηκε εντολή καταγραφής βίντεο σε αυτή τη ρύθμιση Termux.")
    print("    Οι φωτογραφίες, ο ήχος και η τοποθεσία θα συνεχίσουν. Το βίντεο θα παραλειφθεί εκτός αν υπάρχει συμβατή εντολή.")
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
        print("[!] Δεν έχουν ρυθμιστεί επαφές. Δεν στάλθηκε SMS.")
        return 0
    if not which("termux-sms-send"):
        ensure_termux_api()
        if not which("termux-sms-send"):
            print("[!] Το termux-sms-send δεν είναι διαθέσιμο. Δεν θα σταλεί SMS.")
            return 0
    message = f"Έκτακτη ανάγκη: Το Dead Man's Switch ενεργοποιήθηκε. Ιστοσελίδα/repository: {repo_url}"
    sent = 0
    for contact in contacts:
        raw_phone = str(contact.get("phone", "")).strip()
        phone = normalize_phone(raw_phone)
        if not phone_looks_valid(phone):
            print(f"[!] Παράλειψη μη έγκυρου τηλεφώνου για {contact.get('name', 'άγνωστο')}: {raw_phone}")
            continue
        print(f"[*] Αποστολή SMS σε {contact.get('name', phone)} ({phone})")
        run(["termux-sms-send", "-n", phone, message], check=False)
        sent += 1
    return sent


PERSONAL_DETAIL_FIELDS = [
    ("first_name", "Όνομα"),
    ("last_name", "Επώνυμο"),
    ("aliases", "Ψευδώνυμα / aliases"),
    ("phone", "Αριθμός τηλεφώνου"),
    ("email", "Email"),
    ("age", "Ηλικία"),
    ("birthday", "Ημερομηνία γέννησης"),
    ("blood_type", "Ομάδα αίματος"),
    ("height", "Ύψος"),
    ("weight", "Βάρος"),
    ("sex_or_gender", "Φύλο / gender (προαιρετικό)"),
    ("nationality", "Εθνικότητα"),
    ("languages", "Γλώσσες που μιλάς"),
    ("country_living", "Χώρα διαμονής"),
    ("city_living", "Πόλη διαμονής"),
    ("area_or_neighborhood", "Περιοχή / γειτονιά"),
    ("home_area_or_address", "Περιοχή/διεύθυνση σπιτιού ή τελευταίο γνωστό ασφαλές μέρος"),
    ("eye_color", "Χρώμα ματιών"),
    ("hair_color", "Χρώμα μαλλιών"),
    ("body_build", "Σωματότυπος"),
    ("skin_complexion", "Περιγραφή δέρματος/εμφάνισης"),
    ("scars", "Ουλές / σημάδια γέννησης"),
    ("tattoos", "Τατουάζ"),
    ("piercings", "Piercings"),
    ("medical_conditions", "Ιατρικές καταστάσεις που πρέπει να γνωρίζουν οι διασώστες"),
    ("allergies", "Αλλεργίες"),
    ("medications", "Σημαντικά φάρμακα"),
    ("emergency_instructions", "Οδηγίες έκτακτης ανάγκης"),
    ("trusted_people", "Έμπιστα άτομα / ποιοι πρέπει να ειδοποιηθούν"),
    ("social_usernames", "Social usernames που μπορούν να βοηθήσουν στην ταυτοποίησή σου"),
    ("photo_description", "Περιγραφή φωτογραφίας/εμφάνισης"),
    ("usual_clothing", "Συνηθισμένα ρούχα / αξεσουάρ"),
    ("additional_notes", "Επιπλέον σημειώσεις"),
]

PERSONAL_DETAILS_WARNING = """\
[!] Τα Προσωπικά Στοιχεία μπορούν να ανέβουν στο GitHub dead-mans-switch repository σου.
[!] In Χρειάζομαι Βοήθεια mode, the repository is made PUBLIC so emergency contacts can access it.
[!] ΜΗΝ αποθηκεύεις κωδικούς, στοιχεία τράπεζας/κάρτας, private keys, seed phrases, αριθμούς ταυτότητας ή οτιδήποτε μπορεί να χρησιμοποιηθεί για κλοπή.
[!] Χρησιμοποίησέ το μόνο για ταυτοποίηση και πληροφορίες βοήθειας έκτακτης ανάγκης.
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
    """Επιστρέφει έτοιμα στοιχεία εμφάνισης. Τα κενά πεδία γίνονται απλά placeholder μόνο για το website."""
    out = default_personal_details()
    if isinstance(data, dict):
        for key in out:
            out[key] = data.get(key, out.get(key, ""))
    placeholders = {
        "first_name": "Άγνωστο",
        "last_name": "Άτομο",
        "aliases": "Δεν έχει δοθεί ακόμα",
        "phone": "Δεν έχει δοθεί ακόμα",
        "email": "Δεν έχει δοθεί ακόμα",
        "age": "Δεν έχει δοθεί ακόμα",
        "birthday": "Δεν έχει δοθεί ακόμα",
        "blood_type": "Δεν έχει δοθεί ακόμα",
        "height": "Δεν έχει δοθεί ακόμα",
        "weight": "Δεν έχει δοθεί ακόμα",
        "sex_or_gender": "Δεν έχει δοθεί ακόμα",
        "nationality": "Δεν έχει δοθεί ακόμα",
        "languages": "Δεν έχει δοθεί ακόμα",
        "country_living": "Δεν έχει δοθεί ακόμα",
        "city_living": "Δεν έχει δοθεί ακόμα",
        "area_or_neighborhood": "Δεν έχει δοθεί ακόμα",
        "home_area_or_address": "Δεν έχει δοθεί ακόμα",
        "eye_color": "Δεν έχει δοθεί ακόμα",
        "hair_color": "Δεν έχει δοθεί ακόμα",
        "body_build": "Δεν έχει δοθεί ακόμα",
        "skin_complexion": "Δεν έχει δοθεί ακόμα",
        "scars": "Δεν έχει δοθεί ακόμα",
        "tattoos": "Δεν έχει δοθεί ακόμα",
        "piercings": "Δεν έχει δοθεί ακόμα",
        "medical_conditions": "Δεν έχει δοθεί ακόμα",
        "allergies": "Δεν έχει δοθεί ακόμα",
        "medications": "Δεν έχει δοθεί ακόμα",
        "emergency_instructions": "Δεν έχουν δοθεί ειδικές οδηγίες έκτακτης ανάγκης ακόμα.",
        "trusted_people": "Χρησιμοποίησε τις ρυθμισμένες επαφές SMS αν υπάρχουν.",
        "social_usernames": "Δεν έχει δοθεί ακόμα",
        "photo_description": "Δεν έχει δοθεί περιγραφή ακόμα.",
        "usual_clothing": "Δεν έχει δοθεί ακόμα",
        "additional_notes": "Δεν έχουν δοθεί επιπλέον σημειώσεις ακόμα.",
    }
    for key, placeholder in placeholders.items():
        if not str(out.get(key, "")).strip():
            out[key] = placeholder
    if not str(out.get("last_updated", "")).strip():
        out["last_updated"] = "Δεν έχει δοθεί ακόμα"
    return out

def personal_details_to_text(data: Dict[str, Any]) -> str:
    lines = [
        "Dead Man's Switch - Προσωπικά Στοιχεία",
        "================================",
        "",
        "Σκοπός: ταυτοποίηση και πληροφορίες βοήθειας έκτακτης ανάγκης.",
        "Μην αποθηκεύεις εδώ κωδικούς, στοιχεία τράπεζας/κάρτας, private keys, seed phrases ή αριθμούς ταυτότητας.",
        "",
        f"Τελευταία ενημέρωση: {data.get('last_updated', '')}",
        "",
    ]
    for key, label in PERSONAL_DETAIL_FIELDS:
        value = str(data.get(key, "")).strip()
        if value:
            lines.append(f"{label}: {value}")
    if not personal_details_has_content(data):
        lines.append("Δεν έχουν προστεθεί προσωπικά στοιχεία ακόμα.")
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
    print("\n=== Άτομοal Details ===")
    print(PERSONAL_DETAILS_WARNING)
    print(personal_details_to_text(data))
    print(f"Αποθηκευμένο JSON: {personal_details_json_path()}")
    print(f"Αποθηκευμένο TXT : {personal_details_txt_path()}")

def edit_all_personal_details(data: Dict[str, Any]) -> Dict[str, Any]:
    print("\n=== Add/Edit All Άτομοal Details ===")
    print("Άφησε κενό για να κρατήσεις την τρέχουσα τιμή. Γράψε '-' για να καθαρίσεις ένα πεδίο.")
    for key, label in PERSONAL_DETAIL_FIELDS:
        current = str(data.get(key, "")).strip()
        shown = f" [{current}]" if current else ""
        value = input(f"{label}{shown}: ").strip()
        if value == "-":
            data[key] = ""
        elif value:
            data[key] = value
    save_personal_details(data)
    print("[✓] Τα προσωπικά στοιχεία αποθηκεύτηκαν.")
    return data

def edit_one_personal_detail(data: Dict[str, Any]) -> Dict[str, Any]:
    print("\n=== Edit One Άτομοal Detail ===")
    for i, (key, label) in enumerate(PERSONAL_DETAIL_FIELDS, 1):
        value = str(data.get(key, "")).strip()
        preview = value[:40] + ("..." if len(value) > 40 else "")
        print(f"{i}) {label}" + (f" - {preview}" if preview else ""))
    print("0) Πίσω")
    choice = input("Επιλογή πεδίου: ").strip()
    if choice == "0":
        return data
    try:
        idx = int(choice) - 1
        if not 0 <= idx < len(PERSONAL_DETAIL_FIELDS):
            print("[!] Μη έγκυρο πεδίο.")
            return data
        key, label = PERSONAL_DETAIL_FIELDS[idx]
        current = str(data.get(key, "")).strip()
        print(f"Τρέχον {label}{current or '(κενό)'}")
        value = input("Νέα τιμή (κενό = καθαρισμός): ").strip()
        data[key] = value
        save_personal_details(data)
        print("[✓] Ενημερώθηκε.")
    except Exception:
        print("[!] Μη έγκυρη επιλογή.")
    return data

def clear_one_personal_detail(data: Dict[str, Any]) -> Dict[str, Any]:
    print("\n=== Clear One Άτομοal Detail ===")
    for i, (key, label) in enumerate(PERSONAL_DETAIL_FIELDS, 1):
        value = str(data.get(key, "")).strip()
        if value:
            print(f"{i}) {label} - {value[:40]}" + ("..." if len(value) > 40 else ""))
        else:
            print(f"{i}) {label} - κενό")
    print("0) Πίσω")
    choice = input("Επιλογή πεδίου για καθαρισμό: ").strip()
    if choice == "0":
        return data
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(PERSONAL_DETAIL_FIELDS):
            key, label = PERSONAL_DETAIL_FIELDS[idx]
            data[key] = ""
            save_personal_details(data)
            print(f"[✓] Καθαρίστηκε: {label}")
        else:
            print("[!] Μη έγκυρο πεδίο.")
    except Exception:
        print("[!] Μη έγκυρη επιλογή.")
    return data

def delete_personal_details_files():
    for path in [personal_details_json_path(), personal_details_txt_path()]:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass
    print("[✓] Τα αρχεία προσωπικών στοιχείων διαγράφηκαν τοπικά.")

def configure_personal_details():
    ensure_folder()
    data = load_personal_details()
    while True:
        print("\n=== Άτομοal Details ===")
        print("Αυτά τα στοιχεία βοηθούν στην ταυτοποίησή σου σε έκτακτη ανάγκη και μπορούν να ανέβουν μαζί με το Dead Man's Switch repo.")
        print("1) Προβολή προσωπικών στοιχείων")
        print("2) Προσθήκη/Επεξεργασία όλων των στοιχείων")
        print("3) Επεξεργασία ενός πεδίου")
        print("4) Καθαρισμός ενός πεδίου")
        print("5) Αναδημιουργία/export αρχείων JSON + TXT")
        print("6) Διαγραφή όλων των προσωπικών στοιχείων τοπικά")
        print("0) Πίσω")
        choice = input("Select: ").strip()
        if choice == "1":
            print_personal_details(data)
            input("Πάτα Enter για συνέχεια...")
        elif choice == "2":
            print(PERSONAL_DETAILS_WARNING)
            data = edit_all_personal_details(data)
            input("Πάτα Enter για συνέχεια...")
        elif choice == "3":
            data = edit_one_personal_detail(data)
            input("Πάτα Enter για συνέχεια...")
        elif choice == "4":
            data = clear_one_personal_detail(data)
            input("Πάτα Enter για συνέχεια...")
        elif choice == "5":
            paths = write_personal_details_files(data)
            print("[✓] Αναδημιουργήθηκαν τα αρχεία προσωπικών στοιχείων:")
            for path in paths:
                print(f"    {path}")
            input("Πάτα Enter για συνέχεια...")
        elif choice == "6":
            confirm = input("Γράψε DELETE DETAILS για να διαγράψεις τα τοπικά προσωπικά στοιχεία: ").strip()
            if confirm == "DELETE DETAILS":
                data = default_personal_details()
                delete_personal_details_files()
            else:
                print("[*] Ακυρώθηκε.")
            input("Πάτα Enter για συνέχεια...")
        elif choice == "0":
            return
        else:
            print("[!] Μη έγκυρη επιλογή.")
            input("Πάτα Enter για συνέχεια...")


def prompt_int_with_default(label: str, current: int, minimum: int) -> int:
    raw = input(f"{label} δευτερόλεπτα [{current}]: ").strip()
    if not raw:
        return current
    try:
        value = int(raw)
        if value >= minimum:
            return value
        print(f"[!] Πολύ χαμηλό. Κρατάω {current}.")
    except Exception:
        print(f"[!] Μη έγκυρος αριθμός. Κρατάω {current}.")
    return current

def first_time_i_need_help_setup(force: bool = False) -> None:
    settings = load_settings()
    if settings.get("help_first_setup_done") and not force:
        return
    ensure_folder()
    print("\n=== First Time Setup for Χρειάζομαι Βοήθεια ===")
    print("Αυτή η ρύθμιση εμφανίζεται πριν την πρώτη ενεργοποίηση έκτακτης ανάγκης.")
    print("Ρυθμίζει τα διαστήματα καταγραφής, τις επαφές SMS και τα Προσωπικά Στοιχεία.")
    print(PERSONAL_DETAILS_WARNING)

    use_defaults = input("Χρήση προεπιλεγμένων διαστημάτων καταγραφής; (Y/n): ").strip().lower()
    if use_defaults == "n":
        settings["help_photo_interval"] = prompt_int_with_default("Διάστημα φωτογραφίας", int(settings.get("help_photo_interval", 5)), 1)
        settings["help_video_interval"] = prompt_int_with_default("Διάστημα βίντεο", int(settings.get("help_video_interval", 5)), 1)
        settings["help_video_duration"] = prompt_int_with_default("Διάρκεια βίντεο", int(settings.get("help_video_duration", 5)), 1)
        settings["help_mic_interval"] = prompt_int_with_default("Τμήμα/διάστημα μικροφώνου", int(settings.get("help_mic_interval", 10)), 1)
        settings["help_location_interval"] = prompt_int_with_default("Διάστημα τοποθεσίας", int(settings.get("help_location_interval", 180)), 1)

    print("\nEmergency SMS contacts")
    contacts = settings.get("help_contacts", [])
    if contacts:
        print("Υπάρχουσες επαφές:")
        for i, c in enumerate(contacts, 1):
            print(f"  {i}) {c.get('name')} - {c.get('phone')}")
    while True:
        add = input("Να προσθέσω τώρα επαφή SMS έκτακτης ανάγκης; (y/N): ").strip().lower()
        if add != "y":
            break
        name = input("Όνομα: ").strip()
        phone = input("Τηλέφωνο με κωδικό χώρας, π.χ. +306912345678: ").strip()
        if name and phone and phone_looks_valid(phone):
            contacts.append({"name": name, "phone": phone})
            print("[✓] Η επαφή προστέθηκε.")
        else:
            print("[!] Μη έγκυρη επαφή. Προτείνεται όνομα και τηλέφωνο με κωδικό χώρας.")
    settings["help_contacts"] = contacts

    data = load_personal_details()
    if not personal_details_has_content(data):
        print("\nΆτομοal Details")
        fill = input("Να προσθέσω Προσωπικά Στοιχεία τώρα; (προτείνεται) (Y/n): ").strip().lower()
        if fill != "n":
            data = edit_all_personal_details(data)
        else:
            write_personal_details_files(data)
    else:
        print("[*] Τα Προσωπικά Στοιχεία υπάρχουν ήδη. Μπορείς να τα αλλάξεις αργότερα από τις Ρυθμίσεις.")
        write_personal_details_files(data)

    settings["help_first_setup_done"] = True
    save_settings(settings)
    print("[✓] First time Χρειάζομαι Βοήθεια setup saved.")

def repository_visibility_menu():
    print("\nChoose visibility:")
    print("1) Δημόσιο")
    print("2) Ιδιωτικό")
    print("0) Πίσω")
    v = input("\nSelect: ").strip()
    if v == "1":
        set_visibility("public")
    elif v == "2":
        set_visibility("private")
    else:
        print("[*] Ακυρώθηκε.")


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
        "# Δημιουργήθηκε by Dead Man's Switch.py\n"
        "# Άνοιγμα the main Dead Man's Switch menu from Termux:Widget.\n"
        f"cd \"{script_path.parent}\"\n"
        f"exec \"{python_bin}\" \"{script_path}\"\n"
    )
    try:
        widget_path.write_text(content, encoding="utf-8")
        widget_path.chmod(0o755)
        print(f"[✓] Το Termux Widget δημιουργήθηκε/ενημερώθηκε: {widget_path}")
        print("\nHow to use it:")
        print("  1) Εγκατέστησε την Android εφαρμογή Termux:Widget αν δεν την έχεις ήδη.")
        print("  2) Κράτα πατημένη την αρχική οθόνη.")
        print("  3) Πρόσθεσε ένα Termux:Widget widget.")
        print("  4) Διάλεξε: Dead Man's Switch")
    except Exception:
        log_exception("Αποτυχία δημιουργίας Termux Widget")
        print(f"[!] Αποτυχία δημιουργίας widget. Έλεγξε το log: {get_log_file_path()}")

def delete_termux_widget():
    print("\n=== Delete Termux Widget ===")
    widget_path = termux_widget_path()
    try:
        if widget_path.exists():
            widget_path.unlink()
            print(f"[✓] Διαγράφηκε το Termux Widget: {widget_path}")
        else:
            print("[*] Δεν υπάρχει ακόμα αρχείο widget Dead Man's Switch.")
    except Exception:
        log_exception("Αποτυχία διαγραφής Termux Widget")
        print(f"[!] Αποτυχία διαγραφής widget. Έλεγξε το log: {get_log_file_path()}")

def termux_widget_menu():
    while True:
        print("\n=== Termux Widget ===")
        print("1) Δημιουργία / Ενημέρωση Termux Widget")
        print("2) Διαγραφή Termux Widget")
        print("0) Πίσω")
        choice = input("Select: ").strip()
        if choice == "1":
            create_termux_widget()
            input("Πάτα Enter για συνέχεια...")
        elif choice == "2":
            confirm = input("Γράψε DELETE για να αφαιρέσεις το αρχείο widget: ").strip()
            if confirm == "DELETE":
                delete_termux_widget()
            else:
                print("[*] Ακυρώθηκε.")
            input("Πάτα Enter για συνέχεια...")
        elif choice == "0":
            return
        else:
            print("[!] Μη έγκυρη επιλογή.")
            input("Πάτα Enter για συνέχεια...")

def settings_menu():
    while True:
        print("\n=== Settings ===")
        print("1) Ορατότητα Repository (Δημόσιο / Ιδιωτικό)")
        print("2) Χρειάζομαι Βοήθεια settings (intervals, contacts)")
        print("3) Προσωπικά Στοιχεία")
        print("4) Run Χρειάζομαι Βοήθεια first-time setup again")
        print("5) Termux Widget (δημιουργία/διαγραφή)")
        print("0) Πίσω")
        choice = input("Select: ").strip()
        if choice == "1":
            repository_visibility_menu()
            input("Πάτα Enter για συνέχεια...")
        elif choice == "2":
            configure_help_settings()
        elif choice == "3":
            configure_personal_details()
        elif choice == "4":
            first_time_i_need_help_setup(force=True)
            input("Πάτα Enter για συνέχεια...")
        elif choice == "5":
            termux_widget_menu()
        elif choice == "0":
            return
        else:
            print("[!] Μη έγκυρη επιλογή.")
            input("Πάτα Enter για συνέχεια...")

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
        print("\n=== Configure Χρειάζομαι Βοήθεια ===")
        print("Τρέχουσες ρυθμίσεις:")
        print(f"  Διάστημα φωτογραφιών: {settings['help_photo_interval']} seconds")
        print(f"  Διάστημα βίντεο: {settings.get('help_video_interval', 5)} seconds")
        print(f"  Διάρκεια βίντεο: {settings.get('help_video_duration', 5)} seconds")
        print(f"  Διάστημα μικροφώνου: {settings['help_mic_interval']} seconds")
        print(f"  Διάστημα τοποθεσίας: {settings['help_location_interval']} seconds")
        print("  Διάστημα push: σταθερό 300 δευτερόλεπτα / 5 λεπτά")
        print("  Επαφές:")
        if settings.get("help_contacts"):
            for i, c in enumerate(settings.get("help_contacts", []), 1):
                print(f"    {i}) {c.get('name')} : {c.get('phone')}")
        else:
            print("    Δεν έχουν ρυθμιστεί επαφές.")
        print("\n1) Set photo interval")
        print("2) Ορισμός διαστήματος βίντεο")
        print("3) Ορισμός διάρκειας βίντεο")
        print("4) Ορισμός διαστήματος/διάρκειας εγγραφής μικροφώνου")
        print("5) Ορισμός διαστήματος τοποθεσίας")
        print("6) Προσθήκη επαφής")
        print("7) Επεξεργασία επαφής")
        print("8) Διαγραφή επαφής")
        print("9) Πίσω")
        choice = input("Select: ").strip()

        def set_interval(key: str, label: str, minimum: int):
            try:
                val = int(input(f"Νέο {label} διάστημα (δευτερόλεπτα, >= {minimum}): ").strip())
                if val >= minimum:
                    settings[key] = val
                    save_settings(settings)
                    print("[✓] Ενημερώθηκε.")
                else:
                    print(f"[!] Πρέπει να είναι >= {minimum} seconds.")
            except Exception:
                print("[!] Μη έγκυρος αριθμός.")

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
            name = input("Όνομα: ").strip()
            phone = input("Τηλέφωνο (με κωδικό χώρας, π.χ. +306912345678): ").strip()
            if not name or not phone:
                print("[!] Απαιτούνται όνομα και τηλέφωνο.")
            elif not phone_looks_valid(phone):
                print("[!] Η μορφή τηλεφώνου φαίνεται μη έγκυρη. Χρησιμοποίησε κωδικό χώρας αν γίνεται, π.χ. +306912345678.")
            else:
                settings.setdefault("help_contacts", []).append({"name": name, "phone": phone})
                save_settings(settings)
                print("[✓] Η επαφή προστέθηκε.")
        elif choice == "7":
            contacts = settings.get("help_contacts", [])
            if not contacts:
                print("[!] Δεν υπάρχουν επαφές για επεξεργασία.")
            else:
                try:
                    idx = int(input("Αριθμός επαφής για επεξεργασία: ").strip()) - 1
                    if 0 <= idx < len(contacts):
                        old = contacts[idx]
                        name = input(f"Name [{old.get('name', '')}]: ").strip() or old.get("name", "")
                        phone = input(f"Τηλέφωνο [{old.get('phone', '')}]: ").strip() or old.get("phone", "")
                        if name and phone and phone_looks_valid(phone):
                            contacts[idx] = {"name": name, "phone": phone}
                            save_settings(settings)
                            print("[✓] Η επαφή ενημερώθηκε.")
                        else:
                            print("[!] Μη έγκυρο όνομα ή τηλέφωνο.")
                    else:
                        print("[!] Μη έγκυρος αριθμός επαφής.")
                except Exception:
                    print("[!] Μη έγκυρη επιλογή.")
        elif choice == "8":
            contacts = settings.get("help_contacts", [])
            if not contacts:
                print("[!] Δεν υπάρχουν επαφές για διαγραφή.")
            else:
                try:
                    idx = int(input("Αριθμός επαφής για διαγραφή: ").strip()) - 1
                    if 0 <= idx < len(contacts):
                        deleted = contacts.pop(idx)
                        save_settings(settings)
                        print(f"[✓] Διαγράφηκε: {deleted.get('name')}")
                    else:
                        print("[!] Μη έγκυρος αριθμός επαφής.")
                except Exception:
                    print("[!] Μη έγκυρη επιλογή.")
        elif choice == "9":
            return
        else:
            print("[!] Μη έγκυρη επιλογή.")
        input("Πάτα Enter για συνέχεια...")
        settings = load_settings()

def help_mode():
    print("\n=== I NEED HELP MODE ===")
    first_time_i_need_help_setup(force=False)

    print("\n=== I NEED HELP MODE ===")
    print("[!] Αυτό θα ενεργοποιήσει ορατά την καταγραφή έκτακτης ανάγκης ΜΟΝΟ σε αυτό το τηλέφωνο.")
    print("[!] Θα κάνει το GitHub repository σου PUBLIC.")
    print("[!] Θα καταγράφει διαθέσιμες κάμερες, τμήματα μικροφώνου και τοποθεσία με άδειες Termux:API.")
    print("[!] Θα στείλει SMS alerts μόνο στις επαφές που ρύθμισες στις Ρυθμίσεις.")
    print("[!] Αυτή η ενέργεια είναι ορατή και χειροκίνητη. Δεν τρέχει κρυφά στο background.")
    print("[!] Τρόπος διακοπής: πάτα Ctrl+C. Το script τότε θα κάνει push τα υπόλοιπα αρχεία πριν κλείσει.")

    ensure_folder()
    ensure_core_dependencies(include_termux_api=True)
    ensure_logged_in()
    ensure_repo_scope()
    owner = gh_user()
    if not owner:
        print("[!] Δεν μπόρεσα να εντοπίσω το GitHub username.")
        return

    print("[*] Έλεγχος ότι το repository υπάρχει και είναι PUBLIC...")
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
    input("Πάτα Enter για επιβεβαίωση ότι το GitHub Pages είναι ενεργό ή ότι καταλαβαίνεις πως μπορεί να δείχνει 404 μέχρι να ενεργοποιηθεί...")
    input("Press Enter one more time to START Χρειάζομαι Βοήθεια now...")

    camera_ok = ensure_termux_camera()
    video_ok = ensure_termux_video()
    mic_ok = ensure_termux_microphone()
    location_ok = ensure_termux_location()

    archive_previous_version_and_clean_repo(owner, "Χρειάζομαι Βοήθεια activation")
    organize_local_repository_structure()
    ensure_readme(owner, pages_url)
    generate_static_website(owner, pages_url)

    session_id = time.strftime("session_%Y%m%d_%H%M%S")
    photos_dir = LOCAL_DIR / SITE_ASSETS_DIR_NAME / "Φωτογραφίαs" / session_id
    videos_dir = LOCAL_DIR / SITE_ASSETS_DIR_NAME / "Βίντεο" / session_id
    recordings_dir = LOCAL_DIR / SITE_ASSETS_DIR_NAME / "Recordings" / session_id
    locations_dir = LOCAL_DIR / SITE_ASSETS_DIR_NAME / "Τοποθεσίες" / session_id
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
        f"Διάστημα φωτογραφίας: {photo_interval}s\n"
        f"Διάστημα βίντεο: {video_interval}s\n"
        f"Διάρκεια βίντεο: {video_duration}s\n"
        f"Μικρόφωνο interval/segment: {mic_interval}s\n"
        f"Διάστημα τοποθεσίας: {loc_interval}s\n"
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
        print("[!] Δεν εντοπίστηκε λειτουργική κάμερα ή λείπει άδεια κάμερας. Οι φωτογραφίες θα παραλειφθούν.")
    print(f"[*] Εντοπισμένες κάμερες: {cameras}")
    if not video_ok:
        print("[!] Η καταγραφή βίντεο δεν είναι διαθέσιμη. Τα βίντεο θα παραλειφθούν.")
    if not mic_ok:
        print("[!] Η καταγραφή μικροφώνου δεν είναι διαθέσιμη. Ο ήχος θα παραλειφθεί.")
    if not location_ok:
        print("[!] Η τοποθεσία δεν είναι διαθέσιμη. Τα αρχεία τοποθεσίας θα παραλειφθούν.")

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
                print(f"[!] {label} αρχείο λείπει ή είναι κενό: {filepath.name}")
                return False
            size = filepath.stat().st_size
            if size > MAX_FILE_BYTES:
                print(f"[!] {label} πολύ μεγάλο ({size/(1024*1024):.2f} MB), παράλειψη: {filepath.name}")
                return False
            rel = filepath.relative_to(LOCAL_DIR).as_posix()
            with lock:
                if rel not in staged_files:
                    staged_files.append(rel)
                    staged_size += size
            print(f"[*] {label} αποθηκεύτηκε: {filepath.name} ({size/(1024*1024):.2f} MB)")
            return True
        except Exception as e:
            print(f"[!] Δεν μπόρεσα να βάλω στην ουρά {label}: {e}")
            return False

    def queue_existing_local_files_for_emergency():
        """Queue existing files already in the Dead Man's Switch local folder for the first emergency upload."""
        print("[*] Προσθήκη των υπαρχόντων τοπικών αρχείων φακέλου Dead Man's Switch στο emergency upload...")
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
                print(f"[!] Υπάρχον τοπικό αρχείο πολύ μεγάλο, παράλειψη: {rel} ({human_size(size)})")
                continue
            path = LOCAL_DIR / rel
            if queue_file(path, "Existing local file"):
                added += 1
        print(f"[✓] Υπάρχοντα τοπικά αρχεία μπήκαν στην ουρά: {added}" + (f" | παραλείφθηκαν ως πολύ μεγάλα: {skipped}" if skipped else ""))

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
            print("[!] Δεν έχουν ρυθμιστεί επαφές. Δεν στάλθηκε SMS.")
            sms_sent = True
            return
        print(f"[*] Αποστολή emergency SMS alert ({reason})...")
        send_sms_alert(contacts, repo_url)
        sms_sent = True

    def record_audio_async(output_path: Path, duration_sec: int):
        nonlocal audio_in_progress
        try:
            if record_audio_segment(duration_sec, output_path):
                queue_file(output_path, "Ήχος")
            else:
                print("[!] Αποτυχία εγγραφής ήχου")
        finally:
            audio_in_progress = False

    queue_file(session_info, "Session info")
    personal_files = existing_personal_detail_files()
    if personal_files:
        for personal_file in personal_files:
            queue_file(personal_file, "Άτομοal details")
    else:
        print("[!] Δεν βρέθηκε αρχείο Προσωπικών Στοιχείων. Μπορείς να το προσθέσεις από τις Ρυθμίσεις.")

    queue_existing_local_files_for_emergency()

    print("\n[*] Capturing first emergency set now...")
    first_set_time = time.time()

    if cameras:
        for cam_id in cameras:
            ts = time.strftime("%Y%m%d_%H%M%S")
            filepath = photos_dir / f"photo_cam{cam_id}_{ts}.jpg"
            if capture_photo_cam(cam_id, filepath):
                queue_file(filepath, f"Φωτογραφία cam{cam_id}")
            else:
                print(f"[!] Αποτυχία λήψης φωτογραφίας από κάμερα {cam_id}")
    else:
        print("[*] Το πρώτο βήμα φωτογραφίας παραλείφθηκε: δεν υπάρχουν διαθέσιμες κάμερες.")

    if video_ok and cameras:
        print(f"[*] Καταγραφή πρώτου video set ({video_duration}s το καθένα) μετά τις φωτογραφίες...")
        for cam_id in cameras:
            ts = time.strftime("%Y%m%d_%H%M%S")
            filepath = videos_dir / f"video_cam{cam_id}_{ts}.mp4"
            if capture_video_cam(cam_id, video_duration, filepath):
                queue_file(filepath, f"Βίντεο cam{cam_id}")
            else:
                print(f"[!] Αποτυχία καταγραφής βίντεο από κάμερα {cam_id}")
    else:
        print("[*] Το πρώτο βήμα βίντεο παραλείφθηκε: δεν υπάρχει εντολή βίντεο ή δεν υπάρχουν κάμερες.")

    if location_ok:
        ts = time.strftime("%Y%m%d_%H%M%S")
        filepath = locations_dir / f"location_{ts}.json"
        if get_location(filepath):
            queue_file(filepath, "Τοποθεσία")
        else:
            print("[!] Αποτυχία λήψης πρώτης τοποθεσίας")
    else:
        print("[*] Το πρώτο βήμα τοποθεσίας παραλείφθηκε: η τοποθεσία δεν είναι διαθέσιμη.")

    if mic_ok:
        ts = time.strftime("%Y%m%d_%H%M%S")
        filepath = recordings_dir / f"audio_{ts}.aac"
        print(f"[*] Εγγραφή πρώτου τμήματος ήχου ({mic_interval}s) πριν το πρώτο push...")
        if record_audio_segment(mic_interval, filepath):
            queue_file(filepath, "Ήχος")
        else:
            print("[!] Αποτυχία εγγραφής πρώτου ήχου")
    else:
        print("[*] Το πρώτο βήμα ήχου παραλείφθηκε: το μικρόφωνο δεν είναι διαθέσιμο.")

    last_photo_time = first_set_time
    last_video_time = time.time()
    last_mic_time = time.time()
    last_location_time = first_set_time

    print("[*] Το πρώτο emergency capture set ολοκληρώθηκε. Γίνεται άμεσο push...")
    first_push_ok = do_push("Initial emergency data after first capture set")
    if first_push_ok:
        print("[✓] Το πρώτο emergency upload ολοκληρώθηκε.")
    else:
        print("[!] Το πρώτο emergency upload δεν ολοκληρώθηκε. Θα ξαναδοκιμάζει κάθε 5 λεπτά και στο Ctrl+C.")
        last_push_time = time.time()

    send_sms_once("first capture finished")

    print("\n[!] Emergency capture is active. Keep this Termux session open.")
    print("[!] Πάτα Ctrl+C για διακοπή. Τα υπόλοιπα αρχεία στην ουρά θα γίνουν push πριν την έξοδο.")
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
                        queue_file(filepath, f"Φωτογραφία cam{cam_id}")
                    else:
                        print(f"[!] Αποτυχία λήψης φωτογραφίας από κάμερα {cam_id}")

            if video_ok and cameras and (now - last_video_time) >= video_interval:
                last_video_time = now
                print(f"[*] Καταγραφή video set ({video_duration}s each)...")
                for cam_id in cameras:
                    ts = time.strftime("%Y%m%d_%H%M%S")
                    filepath = videos_dir / f"video_cam{cam_id}_{ts}.mp4"
                    if capture_video_cam(cam_id, video_duration, filepath):
                        queue_file(filepath, f"Βίντεο cam{cam_id}")
                    else:
                        print(f"[!] Αποτυχία καταγραφής βίντεο από κάμερα {cam_id}")

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
                    queue_file(filepath, "Τοποθεσία")
                else:
                    print("[!] Αποτυχία λήψης τοποθεσίας")

            with lock:
                has_files = bool(staged_files)
                queued_size = staged_size

            if has_files and ((time.time() - last_push_time) >= push_interval or queued_size >= MAX_BATCH_BYTES):
                do_push()

            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Emergency mode stopped by Ctrl+C.")
        if audio_in_progress:
            print("[*] Αναμονή λίγων δευτερολέπτων για να τελειώσει το τρέχον τμήμα ήχου...")
            wait_until = time.time() + max(3, min(mic_interval + 2, 20))
            while audio_in_progress and time.time() < wait_until:
                time.sleep(1)
        with lock:
            has_files = bool(staged_files)
        if has_files:
            print("[*] Γίνεται push των υπόλοιπων δεδομένων...")
            do_push("Final emergency data before Ctrl+C stop")
        print("[✓] Η λειτουργία βοήθειας ολοκληρώθηκε. Το repository παραμένει public.")
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
  const savedΘέμα = localStorage.getItem('dead-switch-theme');
  if(savedΘέμα === 'light') document.body.classList.add('light-theme');
  const themeBtn = document.querySelector('[data-theme-toggle]');
  function updateΘέμαText(){ if(themeBtn) themeBtn.textContent = document.body.classList.contains('light-theme') ? 'Σκούρο θέμα' : 'Ανοιχτό θέμα'; }
  if(themeBtn){themeBtn.addEventListener('click',()=>{document.body.classList.toggle('light-theme');localStorage.setItem('dead-switch-theme',document.body.classList.contains('light-theme')?'light':'dark');updateΘέμαText();});updateΘέμαText();}
  const menu = document.querySelector('[data-menu-panel]');
  const backdrop = document.querySelector('[data-menu-backdrop]');
  const openBtn = document.querySelector('[data-menu-open]');
  const closeBtn = document.querySelector('[data-menu-close]');
  function setΜενού(open){ if(menu) menu.classList.toggle('open', open); if(backdrop) backdrop.classList.toggle('open', open); if(openBtn) openBtn.setAttribute('aria-expanded', open ? 'true' : 'false'); }
  if(openBtn) openBtn.addEventListener('click',()=>setΜενού(true));
  if(closeBtn) closeBtn.addEventListener('click',()=>setΜενού(false));
  if(backdrop) backdrop.addEventListener('click',()=>setΜενού(false));
  document.addEventListener('keydown',e=>{ if(e.key === 'Escape') setΜενού(false); });
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
        return "Άγνωστο"

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
    return "Άγνωστο", "Άγνωστο", fallback_mtime

def file_kind(rel: str) -> str:
    lower = rel.lower()
    suffix = Path(lower).suffix
    if Path(rel).name in {PERSONAL_DETAILS_JSON_NAME, PERSONAL_DETAILS_TXT_NAME}:
        return "Προσωπικό προφίλ"
    if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return "Φωτογραφία"
    if suffix in {".mp4", ".3gp", ".webm", ".mkv", ".mov"}:
        return "Βίντεο"
    if suffix in {".aac", ".mp3", ".wav", ".m4a", ".ogg", ".flac"}:
        return "Ήχος"
    if "location" in lower and suffix in {".json", ".txt"}:
        return "Τοποθεσία"
    if "session_info" in lower:
        return "Emergency session"
    if suffix in {".pdf", ".doc", ".docx", ".txt", ".md", ".json", ".csv"}:
        return "Έγγραφο"
    return "Αρχείο"

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
        ("index.html", "Πίνακας Ελέγχου", "dashboard"),
        (f"{PAGES_DIR_NAME}/profile.html", "Προφίλ Ατόμου", "profile"),
        (f"{PAGES_DIR_NAME}/gallery.html", "Συλλογή Φωτογραφιών", "gallery"),
        (f"{PAGES_DIR_NAME}/videos.html", "Βίντεο", "videos"),
        (f"{PAGES_DIR_NAME}/audio.html", "Ήχος", "audio"),
        (f"{PAGES_DIR_NAME}/locations.html", "Τοποθεσίες", "locations"),
        (f"{PAGES_DIR_NAME}/timeline.html", "Χρονολόγιο", "timeline"),
        (f"{PAGES_DIR_NAME}/files.html", "Όλα τα Αρχεία", "files"),
        (f"{PAGES_DIR_NAME}/emergency.html", "Πληροφορίες Έκτακτης Ανάγκης", "emergency"),
    ]
    link_html = "\n".join(f'<a class="{ "active" if key == active else "" }" href="{href}">{label}</a>' for href, label, key in links)
    return f"""
<header class="topbar">
  <nav class="nav">
    <div class="brand">Dead Man's Switch<small>Emergency backup GitHub Pages</small></div>
    <button class="burger-btn" type="button" data-menu-open aria-label="Άνοιγμα μενού" aria-expanded="false"><span class="burger-lines"><span></span><span></span><span></span></span> Μενού</button>
  </nav>
</header>
<div class="menu-backdrop" data-menu-backdrop></div>
<aside class="menu-panel" data-menu-panel>
  <div class="menu-header"><span>Μενού</span><button class="close-menu" type="button" data-menu-close>Κλείσιμο</button></div>
  {link_html}
  <button type="button" data-theme-toggle>Θέμα</button>
</aside>
"""

def site_layout(title: str, active: str, body: str, generated_at: str, in_pages: bool = False) -> str:
    base_tag = '<base href="../">' if in_pages else ''
    return f"""<!doctype html>
<html lang="el">
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
  <p>Δημιουργήθηκε από το Dead Man's Switch.py στις {h(generated_at)}. Αυτό το στατικό website έχει σκοπό να βοηθήσει έμπιστα άτομα να καταλάβουν και να ελέγξουν γρήγορα emergency files.</p>
  <p>Σημείωση ιδιωτικότητας: η λειτουργία έκτακτης ανάγκης μπορεί να κάνει αυτό το repository public. Μην βάζεις εδώ κωδικούς, αριθμούς καρτών, seed phrases, private keys ή ευαίσθητα account secrets.</p>
</footer>
</main>
<script src="{SITE_JS_NAME}"></script>
</body>
</html>
"""

def stat_cards(items: List[Dict[str, Any]]) -> str:
    photos = sum(1 for i in items if i["kind"] == "Φωτογραφία")
    videos = sum(1 for i in items if i["kind"] == "Βίντεο")
    audio = sum(1 for i in items if i["kind"] == "Ήχος")
    locations = sum(1 for i in items if i["kind"] == "Τοποθεσία")
    sessions = sum(1 for i in items if i["kind"] == "Emergency session")
    docs = sum(1 for i in items if i["kind"] in {"Έγγραφο", "Προσωπικό προφίλ"})
    return f"""
<section class="grid small">
  <div class="card"><div class="stat">{len(items)}</div><div class="muted">Σύνολο καταχωρημένων αρχείων</div></div>
  <div class="card"><div class="stat">{photos}</div><div class="muted">Φωτογραφίαs</div></div>
  <div class="card"><div class="stat">{videos}</div><div class="muted">Βίντεο</div></div>
  <div class="card"><div class="stat">{audio}</div><div class="muted">Ηχητικά clips</div></div>
  <div class="card"><div class="stat">{locations}</div><div class="muted">Αρχεία τοποθεσίας</div></div>
  <div class="card"><div class="stat">{sessions}</div><div class="muted">Emergency sessions</div></div>
  <div class="card"><div class="stat">{docs}</div><div class="muted">Προφίλ / έγγραφα</div></div>
</section>
"""

def dashboard_page(items: List[Dict[str, Any]], personal: Dict[str, Any], generated_at: str, owner: str = "", pages_url: str = "") -> str:
    latest = items[:8]
    name = " ".join(str(personal.get(k, "")).strip() for k in ["first_name", "last_name"]).strip() or "Άγνωστο άτομο"
    city = str(personal.get("city_living", "")).strip() or str(personal.get("area_or_neighborhood", "")).strip() or "Άγνωστη τοποθεσία"
    cards = "".join(f"""
      <div class="card" data-filter-card>
        <span class="pill">{h(item['kind'])}</span><span class="pill">{h(item['date'])} {h(item['time'])}</span>
        <h3>{h(item['name'])}</h3>
        <p class="muted">{h(item['folder'])} · {h(item['size_h'])}</p>
        <a class="btn" href="{h(item['url'])}">Άνοιγμα αρχείου</a>
      </div>
    """ for item in latest)
    if not cards:
        cards = '<div class="empty">Δεν έχουν καταχωρηθεί αρχεία ακόμα.</div>'
    repo_url = repo_url_for(owner)
    pages_url = pages_url or expected_pages_url(owner)
    link_cards = ""
    if pages_url or repo_url:
        link_cards = f"""
<section class="grid">
  <div class="card success"><h2>Link GitHub Pages</h2><p class="muted">Αυτό είναι το link της ιστοσελίδας που γράφεται και στο README.md.</p><a class="btn primary" href="{h(pages_url)}">Άνοιγμα Ιστοσελίδας</a></div>
  <div class="card"><h2>Link Repository</h2><p class="muted">Raw GitHub repository με κάθε ανεβασμένο αρχείο.</p><a class="btn" href="{h(repo_url)}">Άνοιγμα Repository</a></div>
</section>
"""
    body = f"""
<section class="hero">
  <span class="badge">Ιστοσελίδα emergency backup</span>
  <h1>Πίνακας Ελέγχου Dead Man's Switch</h1>
  <p>Αυτή η σελίδα οργανώνει το ανεβασμένο υλικό του Dead Man's Switch σε προφίλ ατόμου, συλλογή φωτογραφιών, ηχητικά clips, αρχεία τοποθεσίας, χρονολόγιο και αρχείο αρχείων.</p>
  <div class="buttons">
    <a class="btn primary" href="Pages/profile.html">Άνοιγμα Προφίλ Ατόμου</a>
    <a class="btn" href="Pages/gallery.html">Άνοιγμα Συλλογής Φωτογραφιών</a>
    <a class="btn" href="Pages/videos.html">Άνοιγμα Βίντεο</a>
    <a class="btn" href="Pages/locations.html">Άνοιγμα Τοποθεσιών</a>
    <a class="btn danger" href="Pages/emergency.html">Οδηγίες Έκτακτης Ανάγκης</a>
  </div>
</section>
{link_cards}
<section class="grid">
  <div class="card success"><h2>Άτομο</h2><p class="stat" style="font-size:1.25rem">{h(name)}</p><p class="muted">Πόλη / περιοχή: {h(city)}</p></div>
  <div class="card"><h2>Δημιουργήθηκε</h2><p class="stat" style="font-size:1.25rem">{h(generated_at)}</p><p class="muted">Αναδημιουργείται κάθε φορά που το Dead Man's Switch δημοσιεύει το στατικό site.</p></div>
</section>
{stat_cards(items)}
<section class="card">
  <h2>Τελευταία καταχωρημένα αρχεία</h2>
  <input class="searchbar" data-search placeholder="Αναζήτηση τελευταίων αρχείων...">
  <div class="grid">{cards}</div>
</section>
"""
    return site_layout("Πίνακας Ελέγχου", "dashboard", body, generated_at)

def profile_page(personal: Dict[str, Any], generated_at: str) -> str:
    rows = []
    for key, label in PERSONAL_DETAIL_FIELDS:
        value = str(personal.get(key, "")).strip()
        if value:
            rows.append(f"<tr><th>{h(label)}</th><td>{h(value).replace(chr(10), '<br>')}</td></tr>")
    if not rows:
        rows.append('<tr><th>Κατάσταση</th><td>Δεν έχουν προστεθεί προσωπικά στοιχεία ακόμα.</td></tr>')
    body = f"""
<section class="hero"><span class="badge">Ταυτοποίηση</span><h1>Προφίλ Ατόμου</h1><p>Πληροφορίες που προστέθηκαν από το μενού Προσωπικών Στοιχείων. Μπορούν να βοηθήσουν έμπιστα άτομα να ταυτοποιήσουν τον χρήστη και να καταλάβουν το emergency context.</p></section>
<section class="card warning"><h2>Προειδοποίηση Ιδιωτικότητας</h2><p>This profile may become public during Χρειάζομαι Βοήθεια mode. It should contain emergency identification details only, not account secrets or financial information.</p></section>
<section class="card"><div class="table-wrap"><table class="profile-table"><tbody>{''.join(rows)}</tbody></table></div></section>
"""
    return site_layout("Προφίλ Ατόμου", "profile", body, generated_at, in_pages=True)

def gallery_page(items: List[Dict[str, Any]], generated_at: str) -> str:
    photos = [i for i in items if i["kind"] == "Φωτογραφία"]
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for item in photos:
        grouped.setdefault(item["date"], []).append(item)
    parts = []
    for date, group in grouped.items():
        imgs = "".join(f"""
        <article class="photo-card card" data-filter-card>
          <a href="{h(item['url'])}"><img src="{h(item['url'])}" alt="{h(item['name'])}" loading="lazy"></a>
          <div class="media-meta"><strong>{h(item['name'])}</strong><br>{h(item['date'])} {h(item['time'])}<br>{h(item['folder'])}</div>
          <div class="buttons"><a class="btn primary" href="{h(item['url'])}" download>Λήψη φωτογραφίας</a><a class="btn" href="{h(item['url'])}">Άνοιγμα φωτογραφίας</a></div>
        </article>
        """ for item in group)
        parts.append(f"<h2>{h(date)}</h2><div class=\"gallery\">{imgs}</div>")
    content = "".join(parts) if parts else '<div class="empty">Δεν βρέθηκαν φωτογραφίες ακόμα.</div>'
    body = f"""
<section class="hero"><span class="badge">Φωτογραφίαs</span><h1>Συλλογή Φωτογραφιών</h1><p>Οι φωτογραφίες ομαδοποιούνται βάσει εντοπισμένης ημερομηνίας/ώρας από emergency filenames ή χρόνο τροποποίησης αρχείου.</p></section>
<input class="searchbar" data-search placeholder="Αναζήτηση φωτογραφιών ανά όνομα αρχείου, φάκελο, ημερομηνία...">
{content}
"""
    return site_layout("Συλλογή Φωτογραφιών", "gallery", body, generated_at, in_pages=True)

def videos_page(items: List[Dict[str, Any]], generated_at: str) -> str:
    videos = [i for i in items if i["kind"] == "Βίντεο"]
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for item in videos:
        grouped.setdefault(item["date"], []).append(item)
    parts = []
    for date, group in grouped.items():
        cards = "".join(f"""
        <article class="video-card card" data-filter-card>
          <video controls preload="metadata" src="{h(item['url'])}"></video>
          <div class="media-meta"><strong>{h(item['name'])}</strong><br>{h(item['date'])} {h(item['time'])}<br>{h(item['folder'])}</div>
          <div class="buttons"><a class="btn primary" href="{h(item['url'])}" download>Λήψη βίντεο</a><a class="btn" href="{h(item['url'])}">Άνοιγμα βίντεο</a></div>
        </article>
        """ for item in group)
        parts.append(f"<h2>{h(date)}</h2><div class=\"gallery\">{cards}</div>")
    content = "".join(parts) if parts else '<div class="empty">Δεν βρέθηκαν βίντεο ακόμα. Η καταγραφή βίντεο είναι προαιρετική και εξαρτάται από το αν το Termux setup σου παρέχει συμβατή εντολή βίντεο.</div>'
    body = f"""
<section class="hero"><span class="badge">Βίντεο</span><h1>Συλλογή Βίντεο</h1><p>Τα βίντεο ομαδοποιούνται βάσει εντοπισμένης ημερομηνίας/ώρας από emergency filenames ή χρόνο τροποποίησης αρχείου.</p></section>
<input class="searchbar" data-search placeholder="Αναζήτηση βίντεο ανά όνομα αρχείου, φάκελο, ημερομηνία...">
{content}
"""
    return site_layout("Βίντεο", "videos", body, generated_at, in_pages=True)

def audio_page(items: List[Dict[str, Any]], generated_at: str) -> str:
    audio_items = [i for i in items if i["kind"] == "Ήχος"]
    rows = []
    for item in audio_items:
        rows.append(f"""
        <article class="card" data-filter-card>
          <span class="pill">{h(item['date'])} {h(item['time'])}</span><span class="pill">{h(item['size_h'])}</span>
          <h3>{h(item['name'])}</h3>
          <audio controls src="{h(item['url'])}"></audio>
          <p class="media-meta">{h(item['folder'])}</p>
          <div class="buttons"><a class="btn primary" href="{h(item['url'])}" download>Λήψη ήχου</a><a class="btn" href="{h(item['url'])}">Άνοιγμα ήχου</a></div>
        </article>
        """)
    content = "".join(rows) if rows else '<div class="empty">Δεν βρέθηκαν ηχητικά clips ακόμα.</div>'
    body = f"""
<section class="hero"><span class="badge">Μικρόφωνο</span><h1>Ηχητικά Clips</h1><p>Αρχεία ήχου που καταγράφηκαν ή ανέβηκαν στον φάκελο Dead Man's Switch.</p></section>
<input class="searchbar" data-search placeholder="Αναζήτηση ήχου ανά όνομα αρχείου, φάκελο, ημερομηνία...">
<div class="audio-list">{content}</div>
"""
    return site_layout("Ηχητικά Clips", "audio", body, generated_at, in_pages=True)

def locations_page(items: List[Dict[str, Any]], generated_at: str) -> str:
    loc_items = [i for i in items if i["kind"] == "Τοποθεσία"]
    cards = []
    for item in loc_items:
        lat, lon, maps = read_location_info(LOCAL_DIR / item["rel"])
        map_btn = f'<a class="btn primary" href="{h(maps)}" target="_blank" rel="noopener">Άνοιγμα στους Χάρτες</a>' if maps else ''
        coords = f"Γεωγραφικό πλάτος: {h(lat)}<br>Γεωγραφικό μήκος: {h(lon)}" if lat and lon else "Οι συντεταγμένες δεν μπόρεσαν να διαβαστούν αυτόματα. Άνοιξε το raw αρχείο."
        cards.append(f"""
        <article class="card" data-filter-card>
          <span class="pill">{h(item['date'])} {h(item['time'])}</span>
          <h3>{h(item['name'])}</h3>
          <p class="muted">{coords}</p>
          <div class="buttons">{map_btn}<a class="btn primary" href="{h(item['url'])}" download>Λήψη αρχείου τοποθεσίας</a><a class="btn" href="{h(item['url'])}">Άνοιγμα raw αρχείου τοποθεσίας</a></div>
          <p class="media-meta">{h(item['folder'])}</p>
        </article>
        """)
    content = "".join(cards) if cards else '<div class="empty">Δεν βρέθηκαν αρχεία τοποθεσίας ακόμα.</div>'
    body = f"""
<section class="hero"><span class="badge">GPS / Network</span><h1>Τοποθεσίες</h1><p>Τα αρχεία τοποθεσίας εμφανίζονται βάσει εντοπισμένης ημερομηνίας/ώρας. Όταν το γεωγραφικό πλάτος και μήκος διαβάζονται, δημιουργείται κουμπί χάρτη.</p></section>
<input class="searchbar" data-search placeholder="Αναζήτηση τοποθεσιών ανά όνομα αρχείου, φάκελο, ημερομηνία...">
<div class="grid">{content}</div>
"""
    return site_layout("Τοποθεσίες", "locations", body, generated_at, in_pages=True)

def timeline_page(items: List[Dict[str, Any]], generated_at: str) -> str:
    events = []
    for item in items:
        events.append(f"""
        <article class="event card" data-filter-card>
          <span class="pill">{h(item['kind'])}</span><span class="pill">{h(item['size_h'])}</span>
          <h3>{h(item['date'])} {h(item['time'])}</h3>
          <p><a href="{h(item['url'])}">{h(item['name'])}</a></p>
          <p class="media-meta">{h(item['folder'])}</p>
          <div class="buttons"><a class="btn primary" href="{h(item['url'])}" download>Λήψη</a><a class="btn" href="{h(item['url'])}">Άνοιγμα</a></div>
        </article>
        """)
    content = "".join(events) if events else '<div class="empty">Δεν βρέθηκαν γεγονότα χρονολογίου ακόμα.</div>'
    body = f"""
<section class="hero"><span class="badge">Χρονολογία</span><h1>Χρονολόγιο</h1><p>Όλα τα καταχωρημένα αρχεία ταξινομημένα ανά εντοπισμένο timestamp, πρώτα τα νεότερα.</p></section>
<input class="searchbar" data-search placeholder="Αναζήτηση στο χρονολόγιο...">
<section class="timeline">{content}</section>
"""
    return site_layout("Χρονολόγιο", "timeline", body, generated_at, in_pages=True)

def files_page(items: List[Dict[str, Any]], generated_at: str) -> str:
    rows = []
    for item in items:
        rows.append(f"""
        <tr data-filter-card>
          <td><span class="pill">{h(item['kind'])}</span></td>
          <td><a href="{h(item['url'])}">{h(item['rel'])}</a></td>
          <td>{h(item['date'])} {h(item['time'])}</td>
          <td>{h(item['size_h'])}</td>
          <td><a class="btn primary" href="{h(item['url'])}" download>Λήψη</a></td>
        </tr>
        """)
    if not rows:
        rows.append('<tr><td colspan="5">Δεν έχουν καταχωρηθεί αρχεία ακόμα.</td></tr>')
    body = f"""
<section class="hero"><span class="badge">Αρχείο</span><h1>Όλα τα Αρχεία</h1><p>Κάθε μη δημιουργημένο αρχείο που βρέθηκε στον φάκελο Dead Man's Switch, εκτός από τα ίδια τα αρχεία του website.</p></section>
<input class="searchbar" data-search placeholder="Αναζήτηση σε όλα τα αρχεία...">
<section class="card table-wrap"><table class="file-table"><thead><tr><th>Τύπος</th><th>Αρχείο</th><th>Ημερομηνία / ώρα</th><th>Μέγεθος</th><th>Λήψη</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>
"""
    return site_layout("Όλα τα Αρχεία", "files", body, generated_at, in_pages=True)

def emergency_page(items: List[Dict[str, Any]], personal: Dict[str, Any], generated_at: str) -> str:
    name = " ".join(str(personal.get(k, "")).strip() for k in ["first_name", "last_name"]).strip() or "ο χρήστης του Dead Man's Switch"
    body = f"""
<section class="hero"><span class="badge">Διάβασε πρώτα</span><h1>Οδηγίες Έκτακτης Ανάγκης</h1><p>Αυτό το site είναι φτιαγμένο για να βοηθήσει έμπιστα άτομα να ελέγξουν γρήγορα emergency data αν κάτι συνέβη στον/στην {h(name)}.</p></section>
<section class="grid">
  <div class="card warning"><h2>1. Έλεγξε το προφίλ</h2><p>Άνοιξε πρώτα το προφίλ ατόμου. Μπορεί να περιέχει στοιχεία ταυτοποίησης, ιατρικές σημειώσεις, αλλεργίες, έμπιστα άτομα και οδηγίες έκτακτης ανάγκης.</p><a class="btn primary" href="Pages/profile.html">Άνοιγμα Προφίλ</a></div>
  <div class="card"><h2>2. Έλεγξε τις τοποθεσίες</h2><p>Άνοιξε τη σελίδα τοποθεσιών και τις νεότερες εγγραφές χρονολογίου. Αν υπάρχουν συντεταγμένες, χρησιμοποίησε το κουμπί χαρτών.</p><a class="btn primary" href="Pages/locations.html">Άνοιγμα Τοποθεσιών</a></div>
  <div class="card"><h2>3. Έλεγξε το υλικό</h2><p>Έλεγξε τις νεότερες φωτογραφίες και τα ηχητικά clips. Μπορεί να δείχνουν περιβάλλον, ώρα, άτομα ή ήχους.</p><a class="btn primary" href="Pages/timeline.html">Άνοιγμα Χρονολογίου</a></div>
</section>
<section class="card success"><h2>Σημαντικό</h2><p>Αυτό το website είναι στατικό. Δείχνει μόνο αρχεία που ανέβηκαν σε αυτό το GitHub repository. Αν η λειτουργία έκτακτης ανάγκης τρέχει ακόμα, κάνε refresh αργότερα για να δεις νεότερα uploads.</p></section>
<section class="card warning"><h2>Ιδιωτικότητα και ασφάλεια</h2><p>Μην κοινοποιείς δημόσια αυτό το repository εκτός αν είναι απαραίτητο για την ασφάλεια του ατόμου. Αν υπάρχει άμεσος κίνδυνος, επικοινώνησε απευθείας με τις τοπικές υπηρεσίες έκτακτης ανάγκης και τις έμπιστες επαφές.</p></section>
"""
    return site_layout("Οδηγίες Έκτακτης Ανάγκης", "emergency", body, generated_at, in_pages=True)

def generate_static_website(owner: str = "", pages_url: str = "") -> List[str]:
    """Build/update the static Ιστοσελίδα GitHub Pages files inside LOCAL_DIR. Returns generated rel paths."""
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
            "photos": sum(1 for i in items if i["kind"] == "Φωτογραφία"),
            "videos": sum(1 for i in items if i["kind"] == "Βίντεο"),
            "audio": sum(1 for i in items if i["kind"] == "Ήχος"),
            "locations": sum(1 for i in items if i["kind"] == "Τοποθεσία"),
            "documents": sum(1 for i in items if i["kind"] in {"Έγγραφο", "Προσωπικό προφίλ"}),
        },
        "files": [{k: item[k] for k in ["rel", "kind", "size_h", "date", "time", "updated"]} for item in items],
    }
    (LOCAL_DIR / SITE_ASSETS_DIR_NAME / SITE_MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    generated = sorted(GENERATED_SITE_REL_PATHS)
    print(f"[✓] Δημιουργήθηκε το στατικό emergency website ({len(generated)} αρχείο/α).")
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
        print("[!] Το GitHub Pages δεν είναι ενεργό ακόμα ή το GitHub δεν το έχει δημοσιεύσει ακόμα.")
        print("    Ενεργοποίησέ το χειροκίνητα από Repository Settings > Pages.")
        print(f"    Αναμενόμενο website link μετά τη ρύθμιση: {pages_url}")

    commit_readme_with_pages_url(owner, pages_url)
    print("    Μπορεί να χρειαστεί λίγος χρόνος μέχρι το GitHub Pages να ολοκληρώσει τη δημοσίευση μετά από push.")
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
        print("[!] Δεν μπόρεσα να εντοπίσω το GitHub username.")
        return ""
    ensure_repo_created(owner, get_visibility())
    init_or_use_git_repo()
    set_remote(owner)
    ensure_gitignore()
    sync_local_repo_with_remote(owner)
    pages_url = get_known_or_expected_pages_url(owner)
    readme_path = ensure_readme(owner, pages_url)
    print(f"[*] Το README δημιουργήθηκε/ενημερώθηκε με website link: {readme_path}")
    generated = generate_static_website(owner, pages_url)
    generated = sorted(set(generated) | {"README.md"})
    run(["git", "reset"], cwd=str(LOCAL_DIR), check=False)
    stage_paths(generated, force=True)
    if commit_staged("Δημιουργία emergency website Dead Man's Switch"):
        if push_current():
            if enable_pages:
                return ensure_github_pages(owner, current_branch())
    else:
        print("[*] Τα αρχεία website είναι ήδη ενημερωμένα.")
        if enable_pages:
            return ensure_github_pages(owner, current_branch())
    return ""


def clean_repository_menu():
    print("\n=== Clean Repository ===")
    print("[!] Αυτό διαγράφει ΟΛΑ τα αρχεία από το τελευταίο σημείο του history branch στο GitHub repository.")
    print("[!] ΔΕΝ διαγράφει τον τοπικό φάκελο Dead Man's Switch από το τηλέφωνό σου.")
    confirm = input("Γράψε DELETE για καθαρισμό των αρχείων repository: ").strip()
    if confirm != "DELETE":
        print("[*] Ακυρώθηκε.")
        return
    ensure_folder()
    ensure_core_dependencies(include_termux_api=False)
    ensure_logged_in()
    ensure_repo_scope()
    owner = gh_user()
    if not owner:
        print("[!] Δεν μπόρεσα να εντοπίσω το GitHub username.")
        return
    if not repo_exists(owner):
        print(f"[*] Το repository δεν υπάρχει ακόμα: {owner}/{REPO_NAME}")
        return
    init_or_use_git_repo()
    set_remote(owner)
    sync_local_repo_with_remote(owner)
    run(["git", "reset"], cwd=str(LOCAL_DIR), check=False)
    # Remove from Git tracking only. Local phone files stay untouched.
    run(["git", "rm", "-r", "--cached", "--ignore-unmatch", "."], cwd=str(LOCAL_DIR), check=False)
    if commit_staged("Καθαρισμός αρχείων repository Dead Man's Switch"):
        if push_current():
            print(f"[✓] Τα αρχεία repository καθαρίστηκαν: https://github.com/{owner}/{REPO_NAME}")
        else:
            print("[!] Δημιουργήθηκε clean commit, αλλά το push απέτυχε. Ξανατρέξε το μετά τη διόρθωση του GitHub sync.")
    else:
        print("[*] Δεν υπήρχαν tracked αρχεία repository που χρειάζονταν καθαρισμό.")

def print_header():
    enforce_final_repo_name_runtime()
    if os.environ.get("TERM"):
        os.system("clear")
    print("===================================")
    print(f" {APP_NAME} (Termux, no root)")
    print("===================================")
    print(f"Τοπικός φάκελος: {LOCAL_DIR} (resolved: {LOCAL_DIR.resolve()})  (downloads: {DOWNLOADS_DIR})")
    print(f"Αρχείο log  : {get_log_file_path()}")
    print(f"GitHub repo : {FINAL_REPO_NAME} (προτίμηση: {get_visibility().upper()})")
    print(f"Έκδοση      : {APP_VERSION}")
    print(f"Αρχείο script: {Path(__file__).resolve()}")
    print("Κανόνες upload:")
    print(" - Τα πακέτα Termux που λείπουν εγκαθίστανται αυτόματα μόνο όταν χρειάζονται.")
    print(" - Κάθε batch push <= 40MB συνολικά· κάθε αρχείο > 40MB παραλείπεται.")
    print(" - Πριν από κανονικές δημοσιεύσεις repository, το προηγούμενο snapshot γίνεται zip στο History/.")
    print(" - Ο καθαρισμός repository αφαιρεί παλιά Git-tracked αρχεία από το repo, όχι από το storage του τηλεφώνου σου.")
    print("Λειτουργίες:")
    print(" - Δημιουργία/Ενημέρωση: archives previous snapshot, rebuilds README + GitHub Pages, uploads current files.")
    print(" - Χρειάζομαι Βοήθεια: first-time setup, queues existing local files, emergency capture, auto-upload, SMS alert, public website.")
    print("Η σύνδεση παραμένει μέσω GitHub CLI στο Termux HOME (~/.config/gh).")
    print("")

def menu():
    while True:
        print_header()
        print("1) Repository Dead Man's Switch")
        print("2) Χρειάζομαι Βοήθεια")
        print("3) Ρυθμίσεις")
        print("4) Καθαρισμός Repository")
        print("5) Έξοδος")
        choice = input("\nSelect: ").strip()

        if choice == "1":
            create_switch_only_new()
            input("\nΠάτα Enter για συνέχεια...")
        elif choice == "2":
            help_mode()
            input("\nΠάτα Enter για συνέχεια...")
        elif choice == "3":
            settings_menu()
        elif choice == "4":
            clean_repository_menu()
            input("\nΠάτα Enter για συνέχεια...")
        elif choice == "5":
            print("Αντίο.")
            return
        else:
            print("[!] Μη έγκυρη επιλογή.")
            input("\nΠάτα Enter για συνέχεια...")

def show_cli_help():
    print(f"{APP_NAME} - βοηθός Termux GitHub Dead Man's Switch")
    print("")
    print("Χρήση:")
    print("  python \"Dead Man's Switch.py\"               Άνοιγμα μενού")
    print("  python \"Dead Man's Switch.py\" --create        Create/update repository, website, README, history")
    print("  python \"Dead Man's Switch.py\" --i-need-help   Run first-time setup if needed, show Pages guide, then start emergency mode")
    print("  python \"Dead Man's Switch.py\" --settings      Άνοιγμα Settings")
    print("  python \"Dead Man's Switch.py\" --personal      Άνοιγμα Άτομοal Details menu")
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
            print("[!] Χρήση: --visibility public Ή --visibility private")
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
        append_log("STOP", "Λήφθηκε KeyboardInterrupt / Ctrl+C")
        print("\nΑντίο.")
    except Exception:
        log_exception("Fatal unhandled error")
        print(f"\n[!] Fatal error saved in log file: {get_log_file_path()}")
        raise
