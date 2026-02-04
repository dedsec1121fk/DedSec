import os
import sys
import json
import re
import subprocess
import shutil
from pathlib import Path
from typing import List, Tuple, Set

APP_NAME = "Dead Switch"
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

README_TEXT = """# Dead Switch (Dead Man's Switch)

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

# Dead Switch (Νεκροδιακόπτης / Dead Man's Switch)

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
    if which(bin_name):
        return
    pkg_name = pkg_name or bin_name
    print(f"[*] Installing {pkg_name} ...")
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
    print("[*] Installing termux-api (for notifications)...")
    ensure_pkg("termux-notification", "termux-api")
    if not which("termux-notification"):
        print("[!] termux-notification still not found.")
        print("    Install Termux:API app from F-Droid/Play Store and run:")
        print("    pkg install termux-api")
        return

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
    print(f"[*] Missing GitHub token scopes: {', '.join(missing)}")
    print("[*] Requesting additional permissions (one-time)...")
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
        print(f"[*] Creating {visibility.upper()} repo: {owner}/{REPO_NAME}")
        private_flag = "true" if visibility == "private" else "false"
        run(["gh", "api", "-X", "POST", "user/repos",
             "-f", f"name={REPO_NAME}",
             "-f", f"private={private_flag}",
             "-f", "auto_init=false"], check=True)
        print("[*] Repo created.")
    else:
        print(f"[*] Repo exists: {owner}/{REPO_NAME}")

    # Apply desired visibility (best effort) and verify
    print(f"[*] Ensuring repository visibility is {visibility.upper()}...")
    private_flag = "true" if visibility == "private" else "false"
    run(["gh", "api", "-X", "PATCH", f"repos/{owner}/{REPO_NAME}", "-f", f"private={private_flag}"], check=False)

    # gh repo edit expects: --visibility public|private
    edit_args = ["gh", "repo", "edit", f"{owner}/{REPO_NAME}", "--visibility", visibility, "--accept-visibility-change-consequences"]
    run(edit_args, check=False)

    # Verify state
    priv = run(["gh", "api", f"repos/{owner}/{REPO_NAME}", "--jq", ".private"], capture=True, check=False).strip().lower()
    want_priv = "true" if visibility == "private" else "false"
    if priv and priv != want_priv:
        print("[!] Visibility did not apply on first try. Retrying once...")
        ensure_repo_scope()
        run(["gh", "api", "-X", "PATCH", f"repos/{owner}/{REPO_NAME}", "-f", f"private={private_flag}"], check=False)
        run(edit_args, check=False)

def init_or_use_git_repo():
    # Always ensure Git trusts this directory on Android
    ensure_git_safe_directory()
    ensure_git_identity()
    if not (LOCAL_DIR / ".git").exists():
        print("[*] Initializing local git repo...")
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
        print("[!] Commit failed.")
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
    if rc != 0:
        print("[!] Push failed.")
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
    print("\n[!] Skipped files (too large):")
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
    Batched so each push <= 20MB.
    """
    print("\n=== Create Switch (Only New Files) ===")
    ensure_folder()
    ensure_git()
    ensure_gh()
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
    readme_path = ensure_readme()
    print(f"[*] README created/updated at: {readme_path}")

    run(["git", "fetch", "origin"], cwd=str(LOCAL_DIR), check=False)

    remote_paths = fetch_remote_paths(owner)

    local_items = list_local_files()
    print(f"[*] Local files detected: {len(local_items)}")
    if len(local_items) == 0:
        print("[!] Your Dead Switch folder is empty. Put files in it and try again.")
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
        print("[*] No new files to upload (repo already has these names/paths).")
        print(f"[✓] Repo: https://github.com/{owner}/{REPO_NAME}")
        return

    batches = make_batches(candidates, MAX_BATCH_BYTES)
    print(f"[*] Need to upload {len(candidates)} new file(s) in {len(batches)} batch(es).")

    uploaded = 0
    for i, batch in enumerate(batches, start=1):
        # Clear staging area (best effort)
        run(["git", "reset"], cwd=str(LOCAL_DIR), check=False)

        batch_paths = [rel for rel, _ in batch]
        batch_bytes = sum(size for _, size in batch)

        print(f"\n[*] Batch {i}/{len(batches)}: {len(batch_paths)} file(s), {batch_bytes/(1024*1024):.2f} MB")
        stage_paths(batch_paths)

        if not commit_staged(f"Add new files batch {i}/{len(batches)} (<=40MB)"):
            # If commit failed, stop to avoid misleading "done"
            print("[!] Stopping because commit failed. Fix the issue and re-run.")
            return

        if not push_current():
            print("[!] Stopping because push failed. Fix the issue and re-run.")
            return

        uploaded += len(batch_paths)

        # Update remote paths locally so next batches don't duplicate if rerun quickly
        for rel in batch_paths:
            remote_paths.add(rel)

    print(f"\n[✓] Done. Uploaded {uploaded} file(s). Repo: https://github.com/{owner}/{REPO_NAME}")

def overwrite_repository_batched():
    """
    Full overwrite/sync in <=40MB batches (adds/updates).
    - Stages files from the folder in batches.
    - Does NOT automatically delete remote files you removed locally.
    """
    print("\n=== Overwrite Repository (Full Sync, Batched) ===")
    ensure_folder()
    ensure_git()
    ensure_gh()
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
    readme_path = ensure_readme()
    print(f"[*] README created/updated at: {readme_path}")

    run(["git", "fetch", "origin"], cwd=str(LOCAL_DIR), check=False)

    local_items = list_local_files()
    print(f"[*] Local files detected: {len(local_items)}")
    if len(local_items) == 0:
        print("[!] Your Dead Switch folder is empty. Put files in it and try again.")
        return
    skipped_large = [(rel, size) for rel, size in local_items if size > MAX_FILE_BYTES]
    report_skips(skipped_large)

    candidates = [(rel, size) for rel, size in local_items if size <= MAX_FILE_BYTES]
    if not candidates:
        print("[*] Nothing to upload (no files under limit).")
        return

    batches = make_batches(candidates, MAX_BATCH_BYTES)
    print(f"[*] Will sync {len(candidates)} file(s) in {len(batches)} batch(es).")

    committed_any = False
    for i, batch in enumerate(batches, start=1):
        run(["git", "reset"], cwd=str(LOCAL_DIR), check=False)
        batch_paths = [rel for rel, _ in batch]
        batch_bytes = sum(size for _, size in batch)

        print(f"\n[*] Batch {i}/{len(batches)}: {len(batch_paths)} file(s), {batch_bytes/(1024*1024):.2f} MB")
        stage_paths(batch_paths)

        if commit_staged(f"Overwrite/sync batch {i}/{len(batches)} (<=40MB)"):
            committed_any = True
            if not push_current():
                print("[!] Stopping because push failed. Fix the issue and re-run.")
                return
        else:
            print("[*] Nothing changed in this batch.")

    if committed_any:
        print(f"\n[✓] Done. Repo: https://github.com/{owner}/{REPO_NAME}")
    else:
        print("\n[*] No changes detected to upload.")

def wipe_repo_files(owner):
    print("[*] Wiping repository files (empty commit)...")
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
    (LOCAL_DIR / ".gitkeep").write_text("Repo wiped by Dead Switch.py\n", encoding="utf-8")

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
    ensure_git()
    ensure_gh()
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
        "--title", "Dead Switch",
        "--content", f"Choose an action (repo {get_visibility().upper()}):",
        "--button1", "Create Switch",
        "--button1-action", create_cmd,
        "--button2", "Kill Switch",
        "--button2-action", kill_cmd,
        "--ongoing"
    ], check=False)

    print("[✓] Notification created. (Needs Termux:API app installed.)")

def print_header():
    os.system("clear")
    print("===================================")
    print(f" {APP_NAME} (Termux, no root)")
    print("===================================")
    print(f"Local folder: {LOCAL_DIR} (resolved: {LOCAL_DIR.resolve()})  (downloads: {DOWNLOADS_DIR})")
    print(f"GitHub repo : {REPO_NAME} (preference: {get_visibility().upper()})")
    print("Upload rules:")
    print(" - Each batch push <= 40MB total.")
    print(" - Any single file > 40MB is skipped.")
    print("Modes:")
    print(" - Create Switch: uploads only NEW paths (no overwrite).")
    print(" - Overwrite Repo: updates/overwrites in batches.")
    print(" - Kill Switch: wipe + delete repo.")
    print("Login persists via GitHub CLI in Termux HOME (~/.config/gh).")
    print("")

def menu():
    while True:
        print_header()
        print("1) Create Switch (ONLY new files, batched <=40MB)")
        print("2) Overwrite Repository (sync/overwrite, batched <=40MB)")
        print("3) Kill Switch (wipe repo then delete it)")
        print("4) Set Repository Visibility (Public / Private)")
        print("5) Create Termux Notification (Create Switch / Kill Switch)")
        print("6) Open Dead Switch folder (termux-open)")
        print("0) Exit")
        choice = input("\nSelect: ").strip()

        if choice == "1":
            create_switch_only_new()
            input("\nPress Enter to continue...")
        elif choice == "2":
            print("\n[!] WARNING: This will OVERWRITE/UPDATE files in the repo (batched).")
            confirm = input("Type OVERWRITE to continue: ").strip()
            if confirm == "OVERWRITE":
                overwrite_repository_batched()
            else:
                print("[*] Cancelled.")
            input("\nPress Enter to continue...")
            input("\nPress Enter to continue...")
        elif choice == "3":
            print("\n[!] WARNING: This will WIPE and DELETE your GitHub repo.")
            confirm = input("Type KILL to continue: ").strip()
            if confirm == "KILL":
                kill_switch()
            else:
                print("[*] Cancelled.")
            input("\nPress Enter to continue...")
            input("\nPress Enter to continue...")
        elif choice == "4":
            print("\nChoose visibility:")
            print("1) Public")
            print("2) Private")
            v = input("\nSelect: ").strip()
            if v == "1":
                set_visibility("public")
            elif v == "2":
                set_visibility("private")
            else:
                print("[*] Cancelled.")
            input("\nPress Enter to continue...")
            input("\nPress Enter to continue...")
        elif choice == "5":
            create_notification()
            input("\nPress Enter to continue...")
        elif choice == "6":
            ensure_folder()
            run(["termux-open", str(LOCAL_DIR)], check=False)
        elif choice == "0":
            print("Bye.")
            return
        else:
            print("[!] Invalid choice.")
            input("\nPress Enter to continue...")

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
        print("\nBye.")
