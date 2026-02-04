#!/usr/bin/env python3
# Dead Switch.py — Termux (no root)
#
# Syncs /storage/emulated/0/Download/Dead Switch to a GitHub repo (PUBLIC).
# Upload batching:
# - Each push/commit batch uploads at most 20MB total.
# - Files > 20MB are skipped (GitHub/file-limit safety).
# - If you have more than 20MB total to upload, it will upload in multiple batches automatically.
#
# Λειτουργίες:
# 1) Create Switch      -> uploads ONLY NEW files (won't overwrite existing repo paths)
# 2) Overwrite Repo     -> uploads/overwrites files (still batched)
# 3) Kill Switch        -> wipes repo then deletes it
# 4) Notification       -> creates a Termux notification with two actions:
#                          "Create Switch" and "Kill Switch"
#
# Authentication:
# - Uses GitHub CLI (gh) device/web login (modern).
# - gh saves login in Termux HOME (~/.config/gh), so login persists even if you delete this script.

import os
import sys
import json
import re
import subprocess
import shutil
from pathlib import Path
from typing import List, Tuple, Set

APP_NAME = "Νεκροδιακόπτης"
REPO_NAME = "Dead-Switch"   # GitHub repo name (no spaces)
def resolve_downloads_dir() -> Path:
    """
    Prefer Termux's storage symlink if available: ~/storage/downloads
    Fallback to Android public Download locations.
    """
    home = Path.home()
    candidates = [
        home / "storage" / "downloads",          # Termux standard (after termux-setup-storage)
        Path("/storage/emulated/0/Download"),    # common Android path
        Path("/sdcard/Download"),                # alternative
    ]
    for c in candidates:
        if c.exists():
            return c
    # Last-resort default
    return Path("/storage/emulated/0/Download")

DOWNLOADS_DIR = resolve_downloads_dir()
LOCAL_DIR = DOWNLOADS_DIR / APP_NAME

MAX_BATCH_BYTES = 40 * 1024 * 1024  # 40MB per upload batch (commit+push)
MAX_FILE_BYTES = 40 * 1024 * 1024   # also skip any single file > 40MB

CONFIG_PATH = Path.home() / ".dead_switch_settings.json"

README_TEXT = """# Νεκροδιακόπτης (Dead Man\'s Switch)

Ένας *νεκροδιακόπτης* (dead man’s switch) είναι ένας μηχανισμός ασφαλείας που ενεργοποιεί μια ενέργεια αν ο χειριστής πάψει να μπορεί να συνεχίσει—για παράδειγμα, αν σταματήσει να κάνει check‑in.

Με απλά λόγια: αν κάποιος δεν μπορεί να επιβεβαιώσει ότι είναι καλά, το σύστημα μπορεί να αποκαλύψει οδηγίες, να μεταφέρει πρόσβαση, να στείλει ειδοποιήσεις ή να δημοσιεύσει πληροφορίες.

Αυτό το αποθετήριο μπορεί να χρησιμοποιηθεί ως “backup concept” νεκροδιακόπτη:
- Κράτα σημαντικά έγγραφα ή οδηγίες μέσα στο repo.
- Ενημέρωνέ το όποτε χρειάζεται.
- Μπορείς να αυτοματοποιήσεις check‑ins και ενέργειες ξεχωριστά (εκτός αυτού του script).

> Αυτό το script **δεν** υλοποιεί από μόνο του την αυτόματη ενεργοποίηση.
> Απλά συγχρονίζει το περιεχόμενο του τοπικού φακέλου σου στο GitHub και προαιρετικά μπορεί να αδειάσει/διαγράψει το repo.
"""

def load_settings() -> dict:
    """
    Settings persisted in Termux HOME so they survive deleting/recreating the script.
    """
    defaults = {"visibility": "public"}  # public/private
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                defaults.update(data)
    except Exception:
        pass
    vis = str(defaults.get("visibility", "public")).lower().strip()
    if vis not in ("public", "private"):
        vis = "public"
    defaults["visibility"] = vis
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
    """Run a command and return (returncode, output)."""
    p = subprocess.run(cmd, cwd=cwd, text=True,
                       stdout=subprocess.PIPE if capture else None,
                       stderr=subprocess.STDOUT if capture else None)
    out = (p.stdout or "").strip() if capture else ""
    return p.returncode, out

def run(cmd, cwd=None, check=True, capture=False):
    try:
        if capture:
            p = subprocess.run(cmd, cwd=cwd, check=check, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            return p.stdout.strip()
        subprocess.run(cmd, cwd=cwd, check=check)
        return ""
    except subprocess.CalledProcessError as e:
        msg = ""
        if getattr(e, "stdout", None):
            msg = "\n" + e.stdout
        print(f"\n[!] Command failed: {' '.join(cmd)}{msg}")
        if check:
            raise
        return msg.strip()

def which(bin_name):
    return shutil.which(bin_name) is not None

def ensure_termux_storage():
    # Try to ensure Termux has storage permission and the ~/storage links exist.
    # We check both the resolved downloads dir and the Termux storage link path.
    termux_dl = Path.home() / "storage" / "downloads"
    if not DOWNLOADS_DIR.exists() or (str(DOWNLOADS_DIR).startswith(str(Path.home())) and not termux_dl.exists()):
        print("[!] Δεν έχει ρυθμιστεί το Termux storage (δεν υπάρχει πρόσβαση στον κοινόχρηστο χώρο ακόμα).")
        print("    Εκτέλεση: termux-setup-storage")
        run(["termux-setup-storage"], check=False)
        print("\n    Δώσε την άδεια στο παράθυρο που θα εμφανιστεί και μετά ξανατρέξε το script.")
        sys.exit(1)

def ensure_folder():
    ensure_termux_storage()
    if not LOCAL_DIR.exists():
        print(f"[*] Δημιουργία φακέλου: {LOCAL_DIR}")
        LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    else:
        print(f"[*] Ο φάκελος υπάρχει: {LOCAL_DIR}")

def ensure_pkg(bin_name, pkg_name=None):
    if which(bin_name):
        return
    pkg_name = pkg_name or bin_name
    print(f"[*] Γίνεται εγκατάσταση {pkg_name} ...")
    run(["pkg", "update", "-y"], check=False)
    run(["pkg", "install", "-y", pkg_name])

def ensure_git():
    ensure_pkg("git", "git")

def ensure_gh():
    ensure_pkg("gh", "gh")

def ensure_termux_api():
    # termux-notification binary comes from termux-api package
    if which("termux-notification"):
        return
    print("[*] Γίνεται εγκατάσταση termux-api (for notifications)...")
    ensure_pkg("termux-notification", "termux-api")
    if not which("termux-notification"):
        print("[!] Το termux-notification δεν βρέθηκε ακόμη.")
        print("    Εγκατέστησε την εφαρμογή Termux:API από F-Droid/Play Store και τρέξε:")
        print("    pkg install termux-api")
        return

def ensure_logged_in():
    print("[*] Έλεγχος κατάστασης σύνδεσης στο GitHub...")
    ok = subprocess.run(["gh", "auth", "status"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if ok:
        print("[*] GitHub: ήδη συνδεδεμένος (αποθηκευμένο στο HOME του Termux).")
        return

    print("\n[!] Δεν είσαι συνδεδεμένος στο GitHub CLI (gh).")
    print("    Εκκίνηση σύνδεσης device/web (σύγχρονο, χωρίς κωδικό).")
    print("    Ακολούθησε τις οδηγίες στο Termux.\n")
    run(["gh", "auth", "login", "--hostname", "github.com", "--git-protocol", "https", "--web"], check=False)

    ok = subprocess.run(["gh", "auth", "status"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if not ok:
        print("\n[!] Η σύνδεση δεν ολοκληρώθηκε. Τρέξε χειροκίνητα:")
        print("    gh auth login --hostname github.com --git-protocol https --web")
        sys.exit(1)


def get_token_scopes() -> set:
    """
    Returns a set of OAuth scopes for the currently-authenticated gh token (best effort).
    """
    out = run(["gh", "auth", "status", "-h", "github.com"], capture=True, check=False)
    scopes = set()
    if out:
        for line in out.splitlines():
            if "Token scopes:" in line:
                # Example: "Token scopes: 'repo', 'read:org', ..."
                part = line.split("Token scopes:", 1)[1]
                # Extract words like repo, delete_repo, read:org etc
                found = re.findall(r"[A-Za-z0-9:_-]+", part)
                scopes.update(found)
                break
    return scopes

def ensure_scopes(required_scopes):
    """
    Only refresh gh auth if required scopes are missing.
    This avoids asking you for a new device code every time you run the script.
    """
    scopes = get_token_scopes()
    missing = [sc for sc in required_scopes if sc not in scopes]
    if not missing:
        return
    print(f"[*] Λείπουν δικαιώματα (scopes) token GitHub: {', '.join(missing)}")
    print("[*] Ζητούνται επιπλέον δικαιώματα (μία φορά)...")
    args = ["gh", "auth", "refresh", "-h", "github.com"]
    for sc in missing:
        args += ["-s", sc]
    run(args, check=False)

def ensure_repo_scope():
    # Needed for creating repos and toggling visibility
    ensure_scopes(["repo"])
def gh_user():
    out = run(["gh", "api", "user", "--jq", ".login"], capture=True, check=False)
    return (out or "").strip()

def repo_exists(owner):
    rc = subprocess.run(["gh", "repo", "view", f"{owner}/{REPO_NAME}"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
    return rc == 0

def get_default_branch(owner):
    out = run(["gh", "api", f"repos/{owner}/{REPO_NAME}", "--jq", ".default_branch"], capture=True, check=False)
    return (out or "main").strip() or "main"

def ensure_repo_created(owner, visibility: str):
    """
    Ensure repo exists and matches the selected visibility ("public" or "private").
    """
    visibility = (visibility or "public").lower().strip()
    if visibility not in ("public", "private"):
        visibility = "public"

    # Ensure we have scope to create/edit repo without prompting every run
    ensure_repo_scope()

    if not repo_exists(owner):
        print(f"[*] Δημιουργία {visibility.upper()} repo: {owner}/{REPO_NAME}")
        private_flag = "true" if visibility == "private" else "false"
        run(["gh", "api", "-X", "POST", "user/repos",
             "-f", f"name={REPO_NAME}",
             "-f", f"private={private_flag}",
             "-f", "auto_init=false"], check=True)
        print("[*] Το repo δημιουργήθηκε.")
    else:
        print(f"[*] Το repo υπάρχει: {owner}/{REPO_NAME}")

    # Apply desired visibility (best effort) and verify
    print(f"[*] Εφαρμογή ορατότητας αποθετηρίου: {visibility.upper()}...")
    private_flag = "true" if visibility == "private" else "false"
    run(["gh", "api", "-X", "PATCH", f"repos/{owner}/{REPO_NAME}", "-f", f"private={private_flag}"], check=False)

    # gh repo edit expects: --visibility public|private
    edit_args = ["gh", "repo", "edit", f"{owner}/{REPO_NAME}", "--visibility", visibility, "--accept-visibility-change-consequences"]
    run(edit_args, check=False)

    # Verify state
    priv = run(["gh", "api", f"repos/{owner}/{REPO_NAME}", "--jq", ".private"], capture=True, check=False).strip().lower()
    want_priv = "true" if visibility == "private" else "false"
    if priv and priv != want_priv:
        print("[!] Η ορατότητα δεν εφαρμόστηκε με την πρώτη. Επαναπροσπάθεια μία φορά...")
        ensure_repo_scope()
        run(["gh", "api", "-X", "PATCH", f"repos/{owner}/{REPO_NAME}", "-f", f"private={private_flag}"], check=False)
        run(edit_args, check=False)

def init_or_use_git_repo():
    # Always ensure Git trusts this directory on Android
    ensure_git_safe_directory()
    ensure_git_identity()
    if not (LOCAL_DIR / ".git").exists():
        print("[*] Αρχικοποίηση τοπικού git repo...")
        run(["git", "init"], cwd=str(LOCAL_DIR))
        run(["git", "config", "user.name", "dead-switch-termux"], cwd=str(LOCAL_DIR), check=False)
        run(["git", "config", "user.email", "dead-switch@localhost"], cwd=str(LOCAL_DIR), check=False)


def set_remote(owner):
    remote_url = f"https://github.com/{owner}/{REPO_NAME}.git"
    remotes = run(["git", "remote"], cwd=str(LOCAL_DIR), capture=True, check=False)
    if "origin" in remotes.split():
        run(["git", "remote", "set-url", "origin", remote_url], cwd=str(LOCAL_DIR), check=False)
    else:
        run(["git", "remote", "add", "origin", remote_url], cwd=str(LOCAL_DIR), check=False)


def ensure_git_safe_directory():
    """
    Fix Git's 'detected dubious ownership' error (safe.directory).
    This can happen on Android shared storage paths.
    """
    try:
        # Add both raw and resolved paths
        paths = {str(LOCAL_DIR), str(LOCAL_DIR.resolve())}

        # Also add common equivalent Android paths if they point to the same folder
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

def ensure_gitignore():
    gi = LOCAL_DIR / ".gitignore"
    if not gi.exists():
        gi.write_text(".DS_Store\nThumbs.db\n*.log\n__pycache__/\n*.pyc\n", encoding="utf-8")

def ensure_readme():
    """Create/refresh README.md inside your local Dead Switch folder (Downloads)."""
    rm = LOCAL_DIR / "README.md"
    rm.write_text(README_TEXT, encoding="utf-8")
    return rm

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
        print("[*] Nothing staged to commit.")
        return False
    # Commit and detect success
    rc, out = run_rc(["git", "commit", "-m", message], cwd=str(LOCAL_DIR), capture=True)
    if rc != 0:
        print("[!] Αποτυχία commit.")
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
    if rc != 0:
        print("[!] Αποτυχία push.")
        if out:
            print(out)
        return False
    return True

def list_local_files() -> List[Tuple[str, int]]:
    """
    Returns list of (relative_posix_path, size_bytes) excluding .git.
    """
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
    # Stable ordering helps predictability
    items.sort(key=lambda x: x[0])
    return items

def fetch_remote_paths(owner) -> Set[str]:
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
    """
    Greedy batching by sorted order: packs files until max_bytes reached, then starts new batch.
    Skips any file > MAX_FILE_BYTES.
    """
    batches: List[List[Tuple[str, int]]] = []
    current: List[Tuple[str, int]] = []
    total = 0

    for rel, size in candidates:
        if size > MAX_FILE_BYTES:
            # caller may also handle/report; keep skip here for safety
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
    print("\n[!] Παραλείφθηκαν αρχεία (πολύ μεγάλα):")
    for rel, size in skipped:
        mb = size / (1024 * 1024)
        print(f"    - {rel} ({mb:.2f} MB)")
    print("")

def stage_paths(paths: List[str]):
    for rel in paths:
        run(["git", "add", "--", rel], cwd=str(LOCAL_DIR), check=False)

def create_switch_only_new():
    """
    Upload only NEW paths not present in repo.
    Παρτίδαed so each push <= 20MB.
    """
    print("\n=== Δημιουργία (Μόνο νέα αρχεία) ===")
    ensure_folder()
    ensure_git()
    ensure_gh()
    ensure_logged_in()
    ensure_repo_scope()

    owner = gh_user()
    if not owner:
        print("[!] Δεν μπόρεσα να εντοπίσω το username στο GitHub.")
        return

    ensure_repo_created(owner, get_visibility())
    init_or_use_git_repo()
    set_remote(owner)
    ensure_gitignore()
    readme_path = ensure_readme()
    print(f"[*] Το README δημιουργήθηκε/ενημερώθηκε στο: {readme_path}")

    run(["git", "fetch", "origin"], cwd=str(LOCAL_DIR), check=False)

    remote_paths = fetch_remote_paths(owner)

    local_items = list_local_files()
    print(f"[*] Εντοπίστηκαν τοπικά αρχεία: {len(local_items)}")
    if len(local_items) == 0:
        print("[!] Ο φάκελος Νεκροδιακόπτης είναι άδειος. Βάλε αρχεία μέσα και ξαναδοκίμασε.")
        return
    # Always ensure README/.gitignore exist and are considered
    # (they are in local_items already because ensure_* wrote them)
    skipped_large = [(rel, size) for rel, size in local_items if size > MAX_FILE_BYTES]
    report_skips(skipped_large)

    # In "only new files" mode we still ALWAYS upload/update README.md
    candidates = []
    for rel, size in local_items:
        if size > MAX_FILE_BYTES:
            continue
        if rel == "README.md":
            candidates.append((rel, size))
            continue
        if rel not in remote_paths:
            candidates.append((rel, size))

    if not candidates:
        print("[*] Δεν υπάρχουν νέα αρχεία για ανέβασμα (το repo έχει ήδη αυτά τα ονόματα/διαδρομές).")
        print(f"[✓] Repo: https://github.com/{owner}/{REPO_NAME}")
        return

    batches = make_batches(candidates, MAX_BATCH_BYTES)
    print(f"[*] Χρειάζεται να ανέβουν {len(candidates)} new file(s) in {len(batches)} παρτίδα(ες).")

    uploaded = 0
    for i, batch in enumerate(batches, start=1):
        # Clear staging area (best effort)
        run(["git", "reset"], cwd=str(LOCAL_DIR), check=False)

        batch_paths = [rel for rel, _ in batch]
        batch_bytes = sum(size for _, size in batch)

        print(f"\n[*] Παρτίδα {i}/{len(batches)}: {len(batch_paths)} αρχείο(α), {batch_bytes/(1024*1024):.2f} MB")
        stage_paths(batch_paths)

        if not commit_staged(f"Add new files batch {i}/{len(batches)} (<=40MB)"):
            # If commit failed, stop to avoid misleading "done"
            print("[!] Διακοπή επειδή απέτυχε το commit. Διόρθωσε το πρόβλημα και ξανατρέξε το script.")
            return

        if not push_current():
            print("[!] Διακοπή επειδή απέτυχε το push. Διόρθωσε το πρόβλημα και ξανατρέξε το script.")
            return

        uploaded += len(batch_paths)

        # Update remote paths locally so next batches don't duplicate if rerun quickly
        for rel in batch_paths:
            remote_paths.add(rel)

    print(f"\n[✓] Τέλος. Ανέβηκαν {uploaded} file(s). Repo: https://github.com/{owner}/{REPO_NAME}")

def overwrite_repository_batched():
    """
    Full overwrite/sync in <=40MB batches (adds/updates).
    - Stages files from the folder in batches.
    - Does NOT automatically delete remote files you removed locally.
    """
    print("\n=== Overwrite Repository (Full Sync, Παρτίδαed) ===")
    ensure_folder()
    ensure_git()
    ensure_gh()
    ensure_logged_in()
    ensure_repo_scope()

    owner = gh_user()
    if not owner:
        print("[!] Δεν μπόρεσα να εντοπίσω το username στο GitHub.")
        return

    ensure_repo_created(owner, get_visibility())
    init_or_use_git_repo()
    set_remote(owner)
    ensure_gitignore()
    readme_path = ensure_readme()
    print(f"[*] Το README δημιουργήθηκε/ενημερώθηκε στο: {readme_path}")

    run(["git", "fetch", "origin"], cwd=str(LOCAL_DIR), check=False)

    local_items = list_local_files()
    print(f"[*] Εντοπίστηκαν τοπικά αρχεία: {len(local_items)}")
    if len(local_items) == 0:
        print("[!] Ο φάκελος Νεκροδιακόπτης είναι άδειος. Βάλε αρχεία μέσα και ξαναδοκίμασε.")
        return
    skipped_large = [(rel, size) for rel, size in local_items if size > MAX_FILE_BYTES]
    report_skips(skipped_large)

    candidates = [(rel, size) for rel, size in local_items if size <= MAX_FILE_BYTES]
    if not candidates:
        print("[*] Τίποτα για ανέβασμα (δεν υπάρχουν αρχεία κάτω από το όριο).")
        return

    batches = make_batches(candidates, MAX_BATCH_BYTES)
    print(f"[*] Θα συγχρονιστούν {len(candidates)} file(s) in {len(batches)} παρτίδα(ες).")

    committed_any = False
    for i, batch in enumerate(batches, start=1):
        run(["git", "reset"], cwd=str(LOCAL_DIR), check=False)
        batch_paths = [rel for rel, _ in batch]
        batch_bytes = sum(size for _, size in batch)

        print(f"\n[*] Παρτίδα {i}/{len(batches)}: {len(batch_paths)} αρχείο(α), {batch_bytes/(1024*1024):.2f} MB")
        stage_paths(batch_paths)

        if commit_staged(f"Overwrite/sync batch {i}/{len(batches)} (<=40MB)"):
            committed_any = True
            if not push_current():
                print("[!] Διακοπή επειδή απέτυχε το push. Διόρθωσε το πρόβλημα και ξανατρέξε το script.")
                return
        else:
            print("[*] Δεν άλλαξε κάτι σε αυτή την παρτίδα.")

    if committed_any:
        print(f"\n[✓] Done. Repo: https://github.com/{owner}/{REPO_NAME}")
    else:
        print("\n[*] Δεν εντοπίστηκαν αλλαγές για ανέβασμα.")

def wipe_repo_files(owner):
    print("[*] Άδειασμα αρχείων αποθετηρίου (empty commit)...")
    ensure_git()
    init_or_use_git_repo()
    set_remote(owner)

    run(["git", "fetch", "origin"], cwd=str(LOCAL_DIR), check=False)

    for branch in ("main", "master"):
        rc = subprocess.run(["git", "checkout", branch], cwd=str(LOCAL_DIR),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        if rc == 0:
            break
    else:
        run(["git", "checkout", "-B", "main"], cwd=str(LOCAL_DIR), check=False)

    run(["git", "rm", "-r", "--ignore-unmatch", "."], cwd=str(LOCAL_DIR), check=False)

    (LOCAL_DIR / "README.md").write_text(README_TEXT, encoding="utf-8")
    (LOCAL_DIR / ".gitkeep").write_text("Το repo αδειάστηκε από το Dead Switch.py\n", encoding="utf-8")

    run(["git", "add", "-A"], cwd=str(LOCAL_DIR), check=False)
    commit_staged("Wipe repository contents")
    run(["git", "push", "origin", "HEAD", "--force"], cwd=str(LOCAL_DIR), check=False)
    print("[*] Το περιεχόμενο του repo άδειασε (best effort).")

def ensure_delete_scope():
    print("[*] Έλεγχος δικαιωμάτων διαγραφής (delete_repo)...")
    ensure_scopes(["delete_repo", "repo"])

def delete_repo(owner):
    print(f"[*] Γίνεται διαγραφή repo: {owner}/{REPO_NAME}")
    ensure_delete_scope()

    rc = subprocess.run(["gh", "repo", "delete", f"{owner}/{REPO_NAME}", "--yes"],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).returncode
    if rc != 0:
        run(["gh", "api", "-X", "DELETE", f"repos/{owner}/{REPO_NAME}"], check=False)

    if repo_exists(owner):
        print("[!] Το repo εξακολουθεί να υπάρχει.")
        print("    Δοκίμασε χειροκίνητα:")
        print("    gh auth refresh -h github.com -s delete_repo -s repo")
        print(f"    gh repo delete {owner}/{REPO_NAME} --yes")
    else:
        print("[✓] Το repo διαγράφηκε.")

def kill_switch():
    print("\n=== Ακύρωση (Άδειασμα + Διαγραφή Repo) ===")
    ensure_folder()
    ensure_git()
    ensure_gh()
    ensure_logged_in()
    ensure_repo_scope()

    owner = gh_user()
    if not owner:
        print("[!] Δεν μπόρεσα να εντοπίσω το username στο GitHub.")
        return

    if not repo_exists(owner):
        print(f"[*] Το repo δεν υπάρχει: {owner}/{REPO_NAME}")
        return

    try:
        wipe_repo_files(owner)
    except Exception:
        print("[!] Δεν μπόρεσα να αδειάσω πλήρως τα αρχεία (συνεχίζω στη διαγραφή του repo).")

    delete_repo(owner)

def create_notification():
    """
    Creates a Termux notification with 2 action buttons:
    - Create Switch
    - Kill Switch
    Buttons run this same script with CLI args.
    """
    ensure_termux_api()
    if not which("termux-notification"):
        return

    script_path = os.path.abspath(__file__)
    python_bin = sys.executable or "python"

    create_cmd = f'{python_bin} "{script_path}" --create'
    kill_cmd = f'{python_bin} "{script_path}" --kill'

    run([
        "termux-notification",
        "--id", "dead_switch",
        "--title", "Νεκροδιακόπτης",
        "--content", f"Διάλεξε ενέργεια (repo {get_visibility().upper()}):",
        "--button1", "Δημιουργία",
        "--button1-action", create_cmd,
        "--button2", "Ακύρωση",
        "--button2-action", kill_cmd,
        "--ongoing"
    ], check=False)

    print("[✓] Η ειδοποίηση δημιουργήθηκε. (Απαιτεί εγκατεστημένη την εφαρμογή Termux:API.)")

def print_header():
    os.system("clear")
    print("===================================")
    print(f" {APP_NAME} (Termux, no root)")
    print("===================================")
    print(f"Τοπικός φάκελος: {LOCAL_DIR} (resolved: {LOCAL_DIR.resolve()})  (downloads: {DOWNLOADS_DIR})")
    print(f"Αποθετήριο GitHub : {REPO_NAME} (preference: {get_visibility().upper()})")
    print("Κανόνες μεταφόρτωσης:")
    print(" - Κάθε παρτίδα (batch) push <= 40MB συνολικά.")
    print(" - Κάθε μεμονωμένο αρχείο > 40MB παραλείπεται.")
    print("Λειτουργίες:")
    print(" - Δημιουργία: ανεβάζει μόνο ΝΕΑ αρχεία/διαδρομές (χωρίς αντικατάσταση).")
    print(" - Αντικατάσταση: ενημερώνει/αντικαθιστά σε παρτίδες.")
    print(" - Ακύρωση: άδειασμα + διαγραφή αποθετηρίου.")
    print("Η σύνδεση παραμένει μέσω GitHub CLI στο HOME του Termux (~/.config/gh).")
    print("")

def menu():
    while True:
        print_header()
        print("1) Δημιουργία (ΜΟΝΟ νέα αρχεία, σε παρτίδες <=40MB)")
        print("2) Αντικατάσταση/Συγχρονισμός αποθετηρίου (παρτίδες <=40MB)")
        print("3) Ακύρωση (άδειασμα repo και μετά διαγραφή)")
        print("4) Ορατότητα αποθετηρίου (Δημόσιο / Ιδιωτικό)")
        print("5) Ειδοποίηση Termux (Δημιουργία / Ακύρωση)")
        print("6) Άνοιγμα φακέλου Νεκροδιακόπτης (termux-open)")
        print("0) Έξοδος")
        choice = input("\nΕπιλογή: ").strip()

        if choice == "1":
            create_switch_only_new()
            input("\nΠάτα Enter για συνέχεια...")
        elif choice == "2":
            print("\n[!] ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Αυτό θα ΑΝΤΙΚΑΤΑΣΤΗΣΕΙ/ΕΝΗΜΕΡΩΣΕΙ αρχεία στο repo (σε παρτίδες).")
            confirm = input("Πληκτρολόγησε OVERWRITE για συνέχεια: ").strip()
            if confirm == "OVERWRITE":
                overwrite_repository_batched()
            else:
                print("[*] Ακυρώθηκε.")
            input("\nΠάτα Enter για συνέχεια...")
            input("\nΠάτα Enter για συνέχεια...")
        elif choice == "3":
            print("\n[!] ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Αυτό θα ΑΔΕΙΑΣΕΙ και θα ΔΙΑΓΡΑΨΕΙ το GitHub repo σου.")
            confirm = input("Πληκτρολόγησε KILL για συνέχεια: ").strip()
            if confirm == "KILL":
                kill_switch()
            else:
                print("[*] Ακυρώθηκε.")
            input("\nΠάτα Enter για συνέχεια...")
            input("\nΠάτα Enter για συνέχεια...")
        elif choice == "4":
            print("\nΔιάλεξε ορατότητα:")
            print("1) Δημόσιο")
            print("2) Ιδιωτικό")
            v = input("\nΕπιλογή: ").strip()
            if v == "1":
                set_visibility("public")
            elif v == "2":
                set_visibility("private")
            else:
                print("[*] Ακυρώθηκε.")
            input("\nΠάτα Enter για συνέχεια...")
            input("\nΠάτα Enter για συνέχεια...")
        elif choice == "5":
            create_notification()
            input("\nΠάτα Enter για συνέχεια...")
        elif choice == "6":
            ensure_folder()
            run(["termux-open", str(LOCAL_DIR)], check=False)
        elif choice == "0":
            print("Γεια.")
            return
        else:
            print("[!] Μη έγκυρη επιλογή.")
            input("\nΠάτα Enter για συνέχεια...")

def cli_entry():
    # Non-interactive flags for notification buttons
    if "--create" in sys.argv:
        create_switch_only_new()
        return True
    if "--overwrite" in sys.argv:
        overwrite_repository_batched()
        return True
    if "--kill" in sys.argv:
        kill_switch()
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
        return True
    return False

if __name__ == "__main__":
    try:
        if not cli_entry():
            menu()
    except KeyboardInterrupt:
        print("\nΓεια.")
