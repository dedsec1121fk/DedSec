#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import contextlib
import datetime as dt
import hashlib
import hmac
import html
import ipaddress
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import zipfile
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _ensure_flask() -> None:
    try:
        import flask  # noqa: F401
        return
    except Exception:
        pass
    print("Flask is required. Installing it now…", flush=True)
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "flask>=3.0", "werkzeug>=3.0"],
        check=False,
    )
    try:
        import flask  # noqa: F401
    except Exception as exc:
        raise SystemExit(f"Could not install Flask: {exc}") from exc


_ensure_flask()

from flask import (  # noqa: E402
    Flask,
    Response,
    abort,
    flash,
    g,
    jsonify,
    make_response,
    redirect,
    render_template_string,
    request,
    send_file,
    session,
    url_for,
    has_request_context,
)
from markupsafe import Markup  # noqa: E402
from werkzeug.middleware.proxy_fix import ProxyFix  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402


APP_NAME = "DedSec's Server"
EDITION_LANGUAGE = "en"
EDITION_LABEL = "English"
DEFAULT_MANAGER_PASSWORD = "12345678"
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "password"
MAX_UPLOAD_BYTES = 30 * 1024 * 1024 * 1024
UPLOAD_CHUNK_BYTES = 16 * 1024 * 1024
UPLOAD_REQUEST_OVERHEAD_BYTES = 4 * 1024 * 1024
SESSION_SECONDS = 12 * 60 * 60
HOME = Path.home()
APP_HOME = HOME / "DedSec's Server"
EDITION_HOME = APP_HOME / "English"
CONFIG_DIR = EDITION_HOME / "Config"
CONFIG_FILE = CONFIG_DIR / "config.json"
RUNTIME_BASE = EDITION_HOME / "Runtime"
COMMENTS_DIR = EDITION_HOME / "Comments"
SERVERS_ROOT = EDITION_HOME / "Servers"
PREVIOUS_CONFIG_DIR = HOME / ".config" / "dedsecs-server-english"
PREVIOUS_SERVERS_ROOT = HOME / "DedSec-Servers-English"
LEGACY_CONFIG_DIR = Path(os.environ.get("FFUAD_CONFIG_DIR", HOME / ".config" / "ffuad")).expanduser()

# Keep both language editions under the same Termux home folder.
ALL_EDITION_HOMES = (APP_HOME / "English", APP_HOME / "Greek")
ALL_STORAGE_DIRS = [APP_HOME]
for _edition_root in ALL_EDITION_HOMES:
    ALL_STORAGE_DIRS.extend(
        _edition_root / _name
        for _name in ("Config", "Servers", "Runtime", "Comments")
    )
for _directory in ALL_STORAGE_DIRS:
    _directory.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(Exception):
        _directory.chmod(0o700)


# ---------------------------------------------------------------------------
# Text / translations
# ---------------------------------------------------------------------------

TEXT: Dict[str, Dict[str, str]] = {'en': {'management': 'Management',
        'start_server': 'Start server',
        'create_server': 'Create server',
        'edit_server': 'Edit server',
        'delete_server': 'Delete server',
        'list_servers': 'List servers',
        'change_language': 'Change language',
        'show_password': 'Show manager password',
        'install_dependencies': 'Install dependencies',
        'exit': 'Exit',
        'choose_option': 'Choose an option',
        'choose_server': 'Choose the server you want to open',
        'no_servers': 'No servers exist. Create one first.',
        'invalid': 'Invalid option or value.',
        'manager_password': 'Manager password',
        'wrong_manager_password': 'Incorrect manager password.',
        'server_name': 'Server name',
        'server_description': 'Description (optional)',
        'server_password': 'Main administrator password (blank = password)',
        'storage_folder': "Storage folder under ~/DedSec's Server",
        'default_language': 'Default website language',
        'confirm_create': 'Create this server?',
        'confirm_edit': 'Save these changes?',
        'confirm_delete': 'Delete this server profile?',
        'confirm_delete_files': 'Also permanently delete its files folder?',
        'created_ok': 'Server created.',
        'updated_ok': 'Server updated.',
        'deleted_ok': 'Server deleted.',
        'cancelled': 'Action cancelled.',
        'selected_server': 'Selected server',
        'starting_links': 'Starting local, Cloudflare, and Tor links…',
        'local_network': 'LOCAL NETWORK',
        'localhost': 'LOCALHOST',
        'cloudflare': 'CLOUDFLARE',
        'tor': 'TOR',
        'unavailable': 'UNAVAILABLE',
        'stop_hint': 'Press Ctrl+C to stop only this server session.',
        'passwordless_warning_cli': 'OPEN SERVER: Guests can browse and download files with read-only access.',
        'installing': 'Installing dependencies…',
        'install_complete': 'Dependency installation finished.',
        'name_exists': 'A server with that name already exists.',
        'keep_current': 'leave blank to keep the current value',
        'password_mode': 'Password: [k]eep, [c]hange, c[l]ear',
        'language_choice': 'Language [en/el]',
        'yes_no': 'y/N',
        'files': 'Files',
        'search': 'Search',
        'all': 'All',
        'folders': 'Folders',
        'documents': 'Documents',
        'images': 'Images',
        'videos': 'Videos',
        'audio': 'Audio',
        'archives': 'Archives',
        'code': 'Code',
        'apps': 'Applications',
        'other': 'Other',
        'upload': 'Upload',
        'new_folder': 'New folder',
        'folder_name': 'Folder name',
        'create': 'Create',
        'name': 'Name',
        'type': 'Type',
        'size': 'Size',
        'modified': 'Modified',
        'actions': 'Actions',
        'open': 'Open',
        'download': 'Download',
        'details': 'Details',
        'move': 'Move',
        'delete': 'Delete',
        'selected_delete': 'Delete selected',
        'empty': 'No matching entries were found.',
        'root': 'Root',
        'current_folder': 'Current folder',
        'password': 'Server password',
        'login': 'Administrator login',
        'login_help': 'Enter an administrator username and password for full management access.',
        'wrong_password': 'Incorrect password.',
        'access_title': 'Choose access',
        'access_help': 'Choose how you want to open this server.',
        'admin_login': 'Log in as administrator',
        'admin_login_help': 'Administrators can upload, create, move, rename, and delete files and folders.',
        'guest_continue': 'Continue as guest',
        'guest_help': 'Guests can browse, search, view details, and download, but cannot change anything.',
        'guest_mode': 'Guest · Read-only',
        'admin_mode': 'Administrator',
        'permission_denied': 'This operation is available only to the administrator.',
        'logout': 'Exit',
        'light': 'Light',
        'dark': 'Dark',
        'theme': 'Theme',
        'language': 'Language',
        'protected': 'Protected',
        'public': 'Open to guests',
        'confirm_upload': 'Upload the selected files?',
        'confirm_folder': 'Create this folder?',
        'confirm_move': 'Move this entry to the selected folder?',
        'confirm_delete_web': 'Permanently delete this entry? This cannot be undone.',
        'confirm_bulk': 'Permanently delete every selected entry? This cannot be undone.',
        'confirm_theme': 'Change the display theme?',
        'confirm_language': 'Change the display language?',
        'confirm_logout': 'Log out of this session?',
        'upload_done': 'Upload completed.',
        'folder_done': 'Folder created.',
        'move_done': 'Entry moved.',
        'delete_done': 'Entry deleted.',
        'bulk_done': 'Selected entries deleted.',
        'action_failed': 'The action failed.',
        'invalid_path': 'Invalid or unsafe path.',
        'already_exists': 'An entry with that name already exists.',
        'too_large': 'The file exceeds the 30 GB limit.',
        'storage_too_full': 'The upload was stopped because device storage would reach 85% usage.',
        'destination': 'Destination folder (relative path)',
        'new_name': 'New name',
        'save': 'Save',
        'back': 'Back',
        'location': 'Location',
        'created': 'Created',
        'mime': 'MIME type',
        'category': 'Category',
        'checksum': 'SHA-256',
        'calculate': 'Calculate',
        'entry': 'Entry',
        'upload_hint': 'Select multiple files. Files up to 30 GB upload in 16 MB chunks with live progress.',
        'no_password_warning': 'Open server: guest read-only access is enabled.',
        'search_placeholder': 'Search file or folder names…',
        'choose_files': 'Choose files',
        'upload_progress': 'Uploading',
        'file_label': 'File',
        'folder_label': 'Folder',
        'items': 'items',
        'path': 'Path',
        'browse_files': 'Browse files',
        'access_badge': 'Access',
        'server_badge': 'Server',
        'clear_search': 'Clear search',
        'select_all': 'Select all',
        'selected_count': 'selected',
        'nothing_selected': 'Select at least one entry.',
        'home': 'Home',
        'security_check_failed': 'Security check failed. Refresh the page and try again.',
        'rate_limited': 'Too many failed attempts. Try again later.',
        'not_found': 'The requested entry was not found.',
        'open_menu': 'Open categories',
        'close_menu': 'Close categories',
        'upload_failed': 'Upload failed',
        'folder_download': 'Folder download',
        'refresh': 'Refresh',
        'settings': 'Settings',
        'settings_help': 'Management and security settings',
        'change_manager_password': 'Change management password',
        'current_manager_password': 'Current management password',
        'new_manager_password': 'New management password',
        'confirm_manager_password': 'Confirm new management password',
        'manager_password_changed': 'Management password changed successfully.',
        'passwords_do_not_match': 'The passwords do not match.',
        'password_minimum': 'The management password must contain at least 8 characters.',
        'back_to_menu': 'Back to main menu',
        'password_action': 'Main administrator password: [1] keep, [2] change, [3] reset to password',
        'profile_language_fixed': 'Interface language',
        'categories_label': 'Categories',
        'breadcrumb_label': 'Folder path',
        'filters': 'Filters',
        'apply_filters': 'Apply filters',
        'reset_filters': 'Reset filters',
        'size_filter': 'File size',
        'date_filter': 'Modified date',
        'minimum_size': 'Minimum',
        'maximum_size': 'Maximum',
        'from_date': 'From',
        'to_date': 'To',
        'megabytes': 'MB',
        'date_range_help': 'Choose dates from 14/08/2004 onward.',
        'sort_by': 'Sort by',
        'sort_order': 'Order',
        'any_size': 'Any size',
        'size_under_1mb': 'Under 1 MB',
        'size_1_10mb': '1–10 MB',
        'size_10_100mb': '10–100 MB',
        'size_over_100mb': '100 MB or more',
        'any_date': 'Any date',
        'date_today': 'Today',
        'date_7_days': 'Last 7 days',
        'date_30_days': 'Last 30 days',
        'date_year': 'Last 12 months',
        'sort_name': 'Name',
        'sort_size': 'Size',
        'sort_date': 'Modified date',
        'sort_type': 'Type',
        'ascending': 'Ascending',
        'descending': 'Descending',
        'rename': 'Rename',
        'confirm_rename': 'Rename this entry?',
        'rename_done': 'Entry renamed.',
        'destination_folder': 'Destination folder (relative path)',
        'administrators': 'Administrators',
        'manage_admins': 'Manage administrators',
        'admin_username': 'Administrator username',
        'current_admin': 'Current administrator',
        'add_admin': 'Add administrator',
        'change_admin_password': 'Change password',
        'delete_admin': 'Delete administrator',
        'new_admin_password': 'New administrator password',
        'confirm_admin_password': 'Confirm administrator password',
        'admin_added': 'Administrator added.',
        'admin_password_changed': 'Administrator password changed.',
        'admin_deleted': 'Administrator deleted.',
        'admin_exists': 'An administrator with that username already exists.',
        'invalid_username': 'Use 1–64 letters, numbers, dots, underscores, or hyphens.',
        'cannot_delete_last_admin': 'The final administrator cannot be deleted.',
        'cannot_delete_current_admin': 'You cannot delete the administrator account currently in use.',
        'confirm_delete_admin': 'Delete this administrator account?',
        'admin_password_minimum': 'Administrator passwords must contain at least 8 characters.',
        'comments': 'Comments',
        'add_comment': 'Add comment',
        'comment': 'Comment',
        'comment_placeholder': 'Write a comment about this file…',
        'comment_added': 'Comment added.',
        'comment_deleted': 'Comment deleted.',
        'no_comments': 'No comments have been added to this file.',
        'confirm_delete_comment': 'Delete this comment?',
        'comment_too_long': 'Comments can contain up to 2,000 characters.',
        'written_by': 'By',
        'server_access_mode': 'Server access: [1] open to guests, [2] protected for administrators only',
        'access_mode_action': 'Server access: [1] open, [2] protected',
        'open_server_guest_notice': 'Open server: guests can browse and download files with read-only access.',
        'protected_admin_only': 'This server is protected. Only administrators can sign in.',
        'guest_not_allowed': 'Guest access is disabled on protected servers.',
        'default_admin_credentials': 'Default main administrator: admin / password',
        'manage_server_admins_cli': 'Manage server administrator profiles',
        'admin_profiles_cli': 'Administrator profiles',
        'choose_admin_action': 'Choose an administrator action',
        'reset_admin_password': 'Reset password to password',
        'users': 'Users',
        'logs': 'Logs',
        'users_help': 'Administrator accounts and access sessions recorded for this server.',
        'logs_help': 'Complete activity and security event history for this server.',
        'sessions': 'Sessions',
        'role_label': 'Role',
        'ip_address': 'IP address',
        'user_agent': 'Device / browser',
        'signed_in': 'Signed in',
        'last_seen': 'Last seen',
        'status': 'Status',
        'active': 'Active',
        'ended': 'Ended',
        'event': 'Event',
        'result': 'Result',
        'success': 'Success',
        'failed': 'Failed',
        'log_details': 'Details',
        'no_logs': 'No log entries exist yet.',
        'no_sessions': 'No access sessions have been recorded yet.',
        'log_file_location': 'Log file',
        'main_admin_cannot_delete': 'The main administrator cannot be deleted from the Termux menu.',
        'no_admins': 'No administrator accounts exist yet.',
        'main_administrator': 'Main administrator',
        'your_account': 'Your administrator account',
        'change_own_password_help': 'You can change only the password for your own account.',
        'main_admin_manage_help': 'As the main administrator, you can add, delete, and change passwords for all administrators.',
        'main_admin_only': 'Only the main administrator can manage other administrator accounts.',
        'account_type': 'Account type',
        'download_logs_zip': 'Download logs as ZIP',
        'log_export_help': 'Choose a date range to view and download all matching daily logs as TXT files inside one ZIP. Exporting never deletes logs.',
        'no_logs_in_range': 'No log records exist in the selected date range.',
        'current_log_file': 'Current-day detailed log',
        'daily_log_files': 'Daily consolidated TXT logs',
        'request_label': 'Request',
        'status_code': 'Status code',
        'duration': 'Duration'}}


def tr(key: str, lang: Optional[str] = None) -> str:
    return TEXT[EDITION_LANGUAGE].get(key, key)


AUDIT_EVENT_LABELS = {
    "server_started": "Server started",
    "server_stopped": "Server stopped",
    "guest_login": "Guest login",
    "guest_login_blocked": "Blocked guest login",
    "admin_login": "Administrator login",
    "admin_login_failed": "Failed administrator login",
    "logout": "Logout",
    "administrator_added": "Administrator added",
    "administrator_password_changed": "Administrator password changed",
    "administrator_deleted": "Administrator deleted",
    "folder_created": "Folder created",
    "file_uploaded": "File uploaded",
    "upload_rejected": "Upload rejected",
    "entry_moved": "Entry moved",
    "entry_renamed": "Entry renamed",
    "entry_deleted": "Entry deleted",
    "bulk_delete": "Bulk delete",
    "comment_added": "Comment added",
    "comment_deleted": "Comment deleted",
    "file_downloaded": "File downloaded",
    "folder_downloaded": "Folder downloaded",
    "http_request": "Web request",
    "logs_exported": "Logs exported",
}


def audit_event_label(event: str) -> str:
    return AUDIT_EVENT_LABELS.get(str(event), str(event).replace("_", " ").capitalize())


# ---------------------------------------------------------------------------
# Persistent configuration / profiles
# ---------------------------------------------------------------------------

CONFIG_LOCK = threading.RLock()


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _atomic_json_write(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + f".tmp-{os.getpid()}-{secrets.token_hex(3)}")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    with contextlib.suppress(Exception):
        temp.chmod(0o600)
    os.replace(temp, path)


def _path_is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except (OSError, ValueError):
        return False


def _import_previous_layout() -> None:
    # Migrate configuration and maintenance data from older storage locations.
    previous_config = PREVIOUS_CONFIG_DIR / "config.json"
    if not CONFIG_FILE.exists() and previous_config.is_file():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(previous_config, CONFIG_FILE)
    previous_comments = PREVIOUS_CONFIG_DIR / "comments"
    if previous_comments.is_dir() and not any(COMMENTS_DIR.iterdir()):
        shutil.copytree(previous_comments, COMMENTS_DIR, dirs_exist_ok=True)
    previous_runtime = PREVIOUS_CONFIG_DIR / "runtime"
    migrated_runtime = RUNTIME_BASE / "Previous-Runtime"
    if previous_runtime.is_dir() and not migrated_runtime.exists():
        with contextlib.suppress(Exception):
            shutil.move(str(previous_runtime), str(migrated_runtime))


def _next_profile_root(profile: Dict[str, Any], occupied: set[str]) -> Path:
    base = slugify(str(profile.get("id") or profile.get("name") or "server"))
    candidate = SERVERS_ROOT / base
    index = 2
    while str(candidate.resolve(strict=False)) in occupied or candidate.exists():
        candidate = SERVERS_ROOT / f"{base}-{index}"
        index += 1
    return candidate


def _move_profiles_into_app_home(cfg: Dict[str, Any]) -> bool:
    # Keep every server and generated data under ~/DedSec's Server.
    changed = False
    occupied = {
        str(Path(profile.get("root", "")).expanduser().resolve(strict=False))
        for profile in cfg.get("servers", {}).values()
        if profile.get("root")
        and _path_is_inside(Path(profile.get("root", "")).expanduser(), SERVERS_ROOT)
    }
    for profile in cfg.get("servers", {}).values():
        source = Path(profile.get("root", "")).expanduser() if profile.get("root") else Path()
        if profile.get("root") and _path_is_inside(source, SERVERS_ROOT):
            source.mkdir(parents=True, exist_ok=True)
            continue
        destination = _next_profile_root(profile, occupied)
        destination.parent.mkdir(parents=True, exist_ok=True)
        moved = False
        if profile.get("root") and source.exists():
            try:
                shutil.move(str(source), str(destination))
                moved = True
            except Exception as exc:
                print(f"Could not move server storage into {APP_HOME}: {exc}")
        else:
            destination.mkdir(parents=True, exist_ok=True)
            moved = True
        if moved:
            profile["root"] = str(destination.resolve(strict=False))
            occupied.add(str(destination.resolve(strict=False)))
            changed = True
    if changed:
        cfg["storage_home"] = str(APP_HOME.resolve(strict=False))
    return changed


def _default_config() -> Dict[str, Any]:
    return {
        "version": 3,
        "language": EDITION_LANGUAGE,
        "manager_password": DEFAULT_MANAGER_PASSWORD,
        "secret_key": secrets.token_urlsafe(48),
        "servers": {},
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
    }


def _read_legacy_value(path: Path, key: str) -> str:
    if not path.is_file():
        return ""
    prefix = key + "="
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith(prefix):
                return line[len(prefix) :]
    except Exception:
        return ""
    return ""


def _legacy_b64(value: str) -> str:
    try:
        return base64.b64decode(value).decode("utf-8", errors="replace")
    except Exception:
        return ""


def _migrate_legacy_config() -> Optional[Dict[str, Any]]:
    global_file = LEGACY_CONFIG_DIR / "bash-global.conf"
    profiles_dir = LEGACY_CONFIG_DIR / "bash-profiles"
    if not global_file.is_file() or not profiles_dir.is_dir():
        return None
    cfg = _default_config()
    old_lang = _read_legacy_value(global_file, "language")
    if old_lang in ("en", "el"):
        cfg["language"] = old_lang
    old_manager = _read_legacy_value(global_file, "admin_secret")
    if old_manager:
        cfg["manager_password"] = old_manager
    for profile_path in sorted(profiles_dir.glob("*.profile")):
        profile_id = _read_legacy_value(profile_path, "id") or profile_path.stem
        name = _legacy_b64(_read_legacy_value(profile_path, "name")) or profile_id
        root = _legacy_b64(_read_legacy_value(profile_path, "root")) or str(SERVERS_ROOT / profile_id)
        description = _legacy_b64(_read_legacy_value(profile_path, "description"))
        language = _read_legacy_value(profile_path, "language")
        if language not in ("en", "el"):
            language = cfg["language"]
        old_hash = _read_legacy_value(profile_path, "password_hash")
        old_salt = _read_legacy_value(profile_path, "password_salt")
        cfg["servers"][profile_id] = {
            "id": profile_id,
            "name": name,
            "description": description,
            "root": root,
            "language": language,
            "password_hash": old_hash,
            "password_salt": old_salt,
            "password_scheme": "legacy-sha256" if old_hash else "none",
            "access_mode": "protected" if old_hash else "open",
            "secret": _read_legacy_value(profile_path, "secret") or secrets.token_urlsafe(32),
            "created_at": _read_legacy_value(profile_path, "created_at") or _utc_now(),
            "updated_at": _read_legacy_value(profile_path, "updated_at") or _utc_now(),
        }
    cfg["migrated_from_ffuad"] = True
    return cfg


def load_config() -> Dict[str, Any]:
    with CONFIG_LOCK:
        _import_previous_layout()
        if not CONFIG_FILE.exists():
            migrated = _migrate_legacy_config()
            cfg = migrated or _default_config()
            cfg["language"] = EDITION_LANGUAGE
            cfg["manager_password"] = DEFAULT_MANAGER_PASSWORD
            for profile in cfg.get("servers", {}).values():
                profile["language"] = EDITION_LANGUAGE
                _normalize_profile_admins(profile)
            _move_profiles_into_app_home(cfg)
            cfg["storage_home"] = str(APP_HOME.resolve(strict=False))
            _atomic_json_write(CONFIG_FILE, cfg)
            if migrated:
                print("Migrated existing FFUAD profiles to DedSec's Server.")
            else:
                first_run_setup(cfg)
            return cfg
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception as exc:
            backup = CONFIG_FILE.with_name(f"config-broken-{int(time.time())}.json")
            with contextlib.suppress(Exception):
                shutil.copy2(CONFIG_FILE, backup)
            raise SystemExit(f"Configuration is invalid. Backup: {backup}\n{exc}") from exc
        cfg.setdefault("servers", {})
        cfg["language"] = EDITION_LANGUAGE
        cfg.setdefault("manager_password", DEFAULT_MANAGER_PASSWORD)
        cfg.setdefault("secret_key", secrets.token_urlsafe(48))
        changed = False
        for profile in cfg["servers"].values():
            profile["language"] = EDITION_LANGUAGE
            changed = _normalize_profile_admins(profile) or changed
        changed = _move_profiles_into_app_home(cfg) or changed
        expected_storage_home = str(APP_HOME.resolve(strict=False))
        if cfg.get("storage_home") != expected_storage_home:
            cfg["storage_home"] = expected_storage_home
            changed = True
        if changed:
            _atomic_json_write(CONFIG_FILE, cfg)
        return cfg


def save_config(cfg: Dict[str, Any]) -> None:
    with CONFIG_LOCK:
        cfg["updated_at"] = _utc_now()
        _atomic_json_write(CONFIG_FILE, cfg)


def first_run_setup(cfg: Dict[str, Any]) -> None:
    cfg["language"] = EDITION_LANGUAGE
    cfg["manager_password"] = DEFAULT_MANAGER_PASSWORD
    save_config(cfg)
    if sys.stdin.isatty():
        print(f"\n{tr('manager_password')}: {cfg['manager_password']}\n")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^\w-]+", "-", value, flags=re.UNICODE)
    value = re.sub(r"-+", "-", value).strip("-_")
    return value or "server"


def valid_name(value: str) -> bool:
    return bool(value and value not in (".", "..") and not any(ch in value for ch in ("/", "\\", "\0", "\n", "\r")))


def unique_profile_id(cfg: Dict[str, Any], name: str) -> str:
    base = slugify(name)
    candidate = base
    index = 2
    while candidate in cfg["servers"]:
        candidate = f"{base}-{index}"
        index += 1
    return candidate


def unique_storage_root(cfg: Dict[str, Any], name: str) -> Path:
    used = {str(Path(p.get("root", "")).expanduser().resolve(strict=False)) for p in cfg["servers"].values()}
    base = slugify(name)
    candidate = SERVERS_ROOT / base
    index = 2
    while str(candidate.expanduser().resolve(strict=False)) in used or candidate.exists():
        candidate = SERVERS_ROOT / f"{base}-{index}"
        index += 1
    return candidate


def make_password(password: str) -> Tuple[str, str, str]:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 310_000).hex()
    return digest, salt, "pbkdf2-sha256"



def _normalize_profile_admins(profile: Dict[str, Any]) -> bool:
    # Keep old server profiles compatible while separating admin credentials from guest access.
    changed = False
    legacy_protected = bool(profile.get("password_hash"))
    access_mode = str(profile.get("access_mode", "")).strip().lower()
    if access_mode not in ("open", "protected"):
        profile["access_mode"] = "protected" if legacy_protected else "open"
        changed = True

    raw_admins = profile.get("admins")
    admins: List[Dict[str, str]] = []
    if isinstance(raw_admins, list):
        seen = set()
        for raw in raw_admins:
            if not isinstance(raw, dict):
                changed = True
                continue
            username = str(raw.get("username", "")).strip()
            key = username.casefold()
            if not valid_admin_username(username) or key in seen:
                changed = True
                continue
            password_hash = str(raw.get("password_hash", ""))
            password_salt = str(raw.get("password_salt", ""))
            password_scheme = str(raw.get("password_scheme", "pbkdf2-sha256"))
            if not password_hash or not password_salt:
                changed = True
                continue
            visible_password = str(raw.get("termux_password", ""))
            if not visible_password and username.casefold() == DEFAULT_ADMIN_USERNAME.casefold():
                candidate = DEFAULT_ADMIN_PASSWORD
                probe = {
                    "password_hash": password_hash,
                    "password_salt": password_salt,
                    "password_scheme": password_scheme,
                }
                if _verify_account_password(probe, candidate):
                    visible_password = candidate
                    changed = True
            admins.append({
                "username": username,
                "password_hash": password_hash,
                "password_salt": password_salt,
                "password_scheme": password_scheme,
                "termux_password": visible_password,
                "created_at": str(raw.get("created_at") or _utc_now()),
            })
            seen.add(key)
    else:
        changed = True

    if not admins and legacy_protected:
        legacy_account = {
            "username": DEFAULT_ADMIN_USERNAME,
            "password_hash": str(profile.get("password_hash", "")),
            "password_salt": str(profile.get("password_salt", "")),
            "password_scheme": str(profile.get("password_scheme", "legacy-sha256")),
            "termux_password": "",
            "created_at": str(profile.get("created_at") or _utc_now()),
        }
        if _verify_account_password(legacy_account, DEFAULT_ADMIN_PASSWORD):
            legacy_account["termux_password"] = DEFAULT_ADMIN_PASSWORD
        admins.append(legacy_account)
        changed = True

    if not admins:
        admins.append(make_admin_account(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD))
        changed = True

    if raw_admins != admins:
        profile["admins"] = admins
        changed = True
    return changed

def valid_admin_username(username: str) -> bool:
    username = (username or "").strip()
    return bool(1 <= len(username) <= 64 and all(ch.isalnum() or ch in "._-" for ch in username))


def make_admin_account(username: str, password: str) -> Dict[str, str]:
    digest, salt, scheme = make_password(password)
    return {
        "username": username.strip(),
        "password_hash": digest,
        "password_salt": salt,
        "password_scheme": scheme,
        "termux_password": password,
        "created_at": _utc_now(),
    }


def visible_password_input(prompt: str) -> str:
    return input(prompt)


def termux_password(account: Dict[str, Any]) -> str:
    value = str(account.get("termux_password", ""))
    if value:
        return value
    return "[reset required]" if EDITION_LANGUAGE == "en" else "[απαιτείται επαναφορά]"


def print_termux_credentials(cfg: Dict[str, Any]) -> None:
    title = "TERMUX OWNER CREDENTIALS" if EDITION_LANGUAGE == "en" else "ΣΤΟΙΧΕΙΑ ΙΔΙΟΚΤΗΤΗ TERMUX"
    manager_label = "Management password" if EDITION_LANGUAGE == "en" else "Κωδικός διαχείρισης"
    server_label = "Server" if EDITION_LANGUAGE == "en" else "Διακομιστής"
    admin_label = "Main admin" if EDITION_LANGUAGE == "en" else "Κύριος διαχειριστής"
    password_label = "Password" if EDITION_LANGUAGE == "en" else "Κωδικός"
    print(f"\n=== {title} ===")
    print(f"{manager_label}: {cfg.get('manager_password', DEFAULT_MANAGER_PASSWORD)}")
    servers = sorted(cfg.get("servers", {}).values(), key=lambda item: str(item.get("name", "")).casefold())
    if not servers:
        print(f"{admin_label}: {DEFAULT_ADMIN_USERNAME}")
        print(f"{password_label}: {DEFAULT_ADMIN_PASSWORD}")
        return
    for profile in servers:
        _normalize_profile_admins(profile)
        accounts = list(profile.get("admins", []))
        primary = accounts[0] if accounts else make_admin_account(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)
        print(f"{server_label}: {profile.get('name', profile.get('id', ''))}")
        print(f"  {admin_label}: {primary.get('username', DEFAULT_ADMIN_USERNAME)}")
        print(f"  {password_label}: {termux_password(primary)}")


def _verify_account_password(account: Dict[str, Any], password: str) -> bool:
    expected = str(account.get("password_hash", ""))
    salt = str(account.get("password_salt", ""))
    scheme = str(account.get("password_scheme", "legacy-sha256"))
    if not expected or not salt:
        return False
    try:
        if scheme == "pbkdf2-sha256":
            actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 310_000).hex()
        else:
            actual = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def verify_admin_credentials(profile: Dict[str, Any], username: str, password: str) -> Optional[str]:
    _normalize_profile_admins(profile)
    requested = (username or "").strip().casefold()
    for account in profile.get("admins", []):
        if str(account.get("username", "")).casefold() == requested and _verify_account_password(account, password):
            return str(account.get("username", ""))
    return None


def profile_is_protected(profile: Dict[str, Any]) -> bool:
    _normalize_profile_admins(profile)
    return str(profile.get("access_mode", "open")).lower() == "protected"


def profile_has_password(profile: Dict[str, Any]) -> bool:
    # Compatibility name used by older UI code.
    return profile_is_protected(profile)



def confirm_cli(prompt: str, lang: str) -> bool:
    answer = input(f"{prompt} ({tr('yes_no')}): ").strip().lower()
    return answer in ("y", "yes")


def require_manager(cfg: Dict[str, Any], lang: str) -> bool:
    expected = str(cfg.get("manager_password", ""))
    if not expected:
        return True
    entered = visible_password_input(f"{tr('manager_password', lang)}: ")
    if not hmac.compare_digest(entered, expected):
        print(tr("wrong_manager_password", lang))
        return False
    return True


def select_profile(cfg: Dict[str, Any], lang: str) -> Optional[str]:
    servers = list(cfg["servers"].values())
    if not servers:
        print(tr("no_servers", lang))
        return None
    servers.sort(key=lambda item: item.get("name", "").casefold())
    print(tr("choose_server", lang) + ":")
    for index, profile in enumerate(servers, 1):
        lock = tr("protected", lang) if profile_has_password(profile) else tr("public", lang)
        print(f"{index}) {profile['name']}  [{lock}]  {profile['root']}")
    try:
        selected = int(input("> ").strip())
        if 1 <= selected <= len(servers):
            return servers[selected - 1]["id"]
    except (ValueError, EOFError):
        pass
    print(tr("invalid", lang))
    return None


def create_profile(cfg: Dict[str, Any], lang: str) -> None:
    lang = EDITION_LANGUAGE
    if not require_manager(cfg, lang):
        return
    name = input(f"{tr('server_name')}: ").strip()
    if not valid_name(name):
        print(tr("invalid"))
        return
    if any(p.get("name", "").casefold() == name.casefold() for p in cfg["servers"].values()):
        print(tr("name_exists"))
        return
    description = input(f"{tr('server_description')}: ").strip()
    access_choice = input(f"{tr('server_access_mode')} [1]: ").strip() or "1"
    if access_choice not in ("1", "2"):
        print(tr("invalid"))
        return
    access_mode = "open" if access_choice == "1" else "protected"
    password = visible_password_input(f"{tr('server_password')}: ") or DEFAULT_ADMIN_PASSWORD
    root = unique_storage_root(cfg, name)
    access_label = tr("public") if access_mode == "open" else tr("protected")
    print(f"\n{tr('server_name')}: {name}\n{tr('storage_folder')}: {root}\n{tr('access_badge')}: {access_label}\n{tr('profile_language_fixed')}: {EDITION_LABEL}")
    print(tr("default_admin_credentials") if password == DEFAULT_ADMIN_PASSWORD else f"{tr('admin_username')}: {DEFAULT_ADMIN_USERNAME}")
    if not confirm_cli(tr("confirm_create"), lang):
        print(tr("cancelled"))
        return
    profile_id = unique_profile_id(cfg, name)
    admin = make_admin_account(DEFAULT_ADMIN_USERNAME, password)
    root.mkdir(parents=True, exist_ok=True)
    cfg["servers"][profile_id] = {
        "id": profile_id,
        "name": name,
        "description": description,
        "root": str(root.resolve(strict=False)),
        "language": EDITION_LANGUAGE,
        "access_mode": access_mode,
        "password_hash": admin["password_hash"],
        "password_salt": admin["password_salt"],
        "password_scheme": admin["password_scheme"],
        "termux_password": admin.get("termux_password", password),
        "admins": [admin],
        "secret": secrets.token_urlsafe(32),
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
    }
    save_config(cfg)
    print(tr("created_ok"))

def edit_profile(cfg: Dict[str, Any], lang: str) -> None:
    lang = EDITION_LANGUAGE
    if not require_manager(cfg, lang):
        return
    profile_id = select_profile(cfg, lang)
    if not profile_id:
        return
    profile = cfg["servers"][profile_id]
    _normalize_profile_admins(profile)
    name = input(f"{tr('server_name')} [{profile['name']}]: ").strip() or profile["name"]
    if not valid_name(name):
        print(tr("invalid"))
        return
    if any(pid != profile_id and p.get("name", "").casefold() == name.casefold() for pid, p in cfg["servers"].items()):
        print(tr("name_exists"))
        return
    description = input(f"{tr('server_description')} [{profile.get('description', '')}]: ").strip()
    if not description:
        description = profile.get("description", "")
    root = Path(profile["root"]).expanduser()

    current_access = "2" if profile_is_protected(profile) else "1"
    access_choice = input(f"{tr('access_mode_action')} [{current_access}]: ").strip() or current_access
    if access_choice not in ("1", "2"):
        print(tr("invalid"))
        return
    access_mode = "open" if access_choice == "1" else "protected"

    password_mode = input(f"{tr('password_action')} [1]: ").strip() or "1"
    admins = list(profile.get("admins", []))
    if not admins:
        admins = [make_admin_account(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)]
    if password_mode == "2":
        password = visible_password_input(f"{tr('server_password')}: ") or DEFAULT_ADMIN_PASSWORD
        replacement = make_admin_account(str(admins[0].get("username") or DEFAULT_ADMIN_USERNAME), password)
        admins[0].update(replacement)
    elif password_mode == "3":
        replacement = make_admin_account(str(admins[0].get("username") or DEFAULT_ADMIN_USERNAME), DEFAULT_ADMIN_PASSWORD)
        admins[0].update(replacement)
    elif password_mode != "1":
        print(tr("invalid"))
        return

    if not confirm_cli(tr("confirm_edit"), lang):
        print(tr("cancelled"))
        return
    root.mkdir(parents=True, exist_ok=True)
    primary = admins[0]
    profile.update({
        "name": name,
        "description": description,
        "root": str(root.resolve(strict=False)),
        "language": EDITION_LANGUAGE,
        "access_mode": access_mode,
        "password_hash": primary["password_hash"],
        "password_salt": primary["password_salt"],
        "password_scheme": primary["password_scheme"],
        "termux_password": primary.get("termux_password", ""),
        "admins": admins,
        "updated_at": _utc_now(),
    })
    save_config(cfg)
    print(tr("updated_ok"))

def delete_profile(cfg: Dict[str, Any], lang: str) -> None:
    if not require_manager(cfg, lang):
        return
    profile_id = select_profile(cfg, lang)
    if not profile_id:
        return
    profile = cfg["servers"][profile_id]
    if not confirm_cli(f"{tr('confirm_delete', lang)} [{profile['name']}]", lang):
        print(tr("cancelled", lang))
        return
    delete_files = confirm_cli(tr("confirm_delete_files", lang), lang)
    root = Path(profile["root"]).expanduser()
    del cfg["servers"][profile_id]
    save_config(cfg)
    if delete_files and root.exists():
        with contextlib.suppress(Exception):
            shutil.rmtree(root)
    print(tr("deleted_ok", lang))


def list_profiles(cfg: Dict[str, Any], lang: str) -> None:
    if not cfg["servers"]:
        print(tr("no_servers", lang))
        return
    for profile in sorted(cfg["servers"].values(), key=lambda p: p.get("name", "").casefold()):
        state = tr("protected", lang) if profile_has_password(profile) else tr("public", lang)
        print(f"- {profile['id']}: {profile['name']} [{state}]\n  {profile['root']}\n  {profile.get('description', '')}")

# ---------------------------------------------------------------------------
# Active web application state
# ---------------------------------------------------------------------------

ACTIVE_CONFIG: Dict[str, Any] = {}
ACTIVE_PROFILE: Dict[str, Any] = {}
ACTIVE_ROOT = Path("/")
LOGIN_ATTEMPTS: Dict[str, List[float]] = {}
LOGIN_LOCK = threading.Lock()


class LoopbackProxyFix:
    """Trust forwarded headers only from a local reverse proxy."""

    def __init__(self, app):
        self.app = app
        self.proxy = ProxyFix(app, x_for=1, x_proto=1, x_host=1)

    def __call__(self, environ, start_response):
        remote = (environ.get("REMOTE_ADDR") or "").strip()
        if remote in ("127.0.0.1", "::1"):
            return self.proxy(environ, start_response)
        for key in (
            "HTTP_X_FORWARDED_FOR",
            "HTTP_X_FORWARDED_PROTO",
            "HTTP_X_FORWARDED_HOST",
            "HTTP_X_FORWARDED_PORT",
        ):
            environ.pop(key, None)
        return self.app(environ, start_response)


app = Flask(__name__)
app.wsgi_app = LoopbackProxyFix(app.wsgi_app)
app.config.update(
    MAX_CONTENT_LENGTH=UPLOAD_CHUNK_BYTES + UPLOAD_REQUEST_OVERHEAD_BYTES,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=dt.timedelta(seconds=SESSION_SECONDS),
)


def current_language() -> str:
    return EDITION_LANGUAGE


def current_theme() -> str:
    query_theme = request.args.get("theme", "")
    if query_theme in ("dark", "light"):
        return query_theme
    cookie_theme = request.cookies.get("DEDSEC_THEME", "")
    return cookie_theme if cookie_theme in ("dark", "light") else "dark"


def role() -> str:
    if session.get("profile_id") != ACTIVE_PROFILE.get("id"):
        return ""
    value = session.get("role", "")
    return value if value in ("admin", "guest") else ""


def is_admin() -> bool:
    return role() == "admin"


def current_admin() -> str:
    if not is_admin():
        return ""
    return str(session.get("admin_username") or "admin")


def main_admin_username() -> str:
    _normalize_profile_admins(ACTIVE_PROFILE)
    accounts = ACTIVE_PROFILE.get("admins", [])
    if not accounts:
        return DEFAULT_ADMIN_USERNAME
    return str(accounts[0].get("username") or DEFAULT_ADMIN_USERNAME)


def is_main_admin() -> bool:
    return is_admin() and current_admin().casefold() == main_admin_username().casefold()


def require_main_admin() -> None:
    require_role(admin=True)
    if not is_main_admin():
        abort(403, description=tr("main_admin_only"))


def csrf_token() -> str:
    token = session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf"] = token
    return token


def verify_csrf() -> bool:
    supplied = request.form.get("csrf") or request.headers.get("X-CSRF-Token") or request.args.get("csrf")
    expected = session.get("csrf", "")
    if not supplied or not expected or not hmac.compare_digest(str(supplied), str(expected)):
        return False
    origin = request.headers.get("Origin")
    referer = request.headers.get("Referer")
    expected_host = request.host.lower()
    for candidate in (origin, referer):
        if not candidate:
            continue
        try:
            if urllib.parse.urlsplit(candidate).netloc.lower() != expected_host:
                return False
        except Exception:
            return False
    return True


def require_role(admin: bool = False) -> None:
    if not role():
        abort(401)
    if admin and not is_admin():
        abort(403)


INTERNAL_DIR_NAME = ".dedsec-server"
AUDIT_LOCK = threading.RLock()
SESSION_REGISTRY_LOCK = threading.RLock()


def server_internal_dir() -> Path:
    directory = ACTIVE_ROOT / INTERNAL_DIR_NAME
    directory.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(Exception):
        directory.chmod(0o700)
    return directory



def audit_log_path() -> Path:
    directory = server_internal_dir() / "logs"
    directory.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(Exception):
        directory.chmod(0o700)
    return directory / "audit.jsonl"


def audit_history_path() -> Path:
    return audit_log_path().parent / ".history.jsonl"


def audit_daily_path(day: dt.date) -> Path:
    return audit_log_path().parent / day.strftime("%d-%m-%Y.txt")


def _atomic_text_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".tmp-{os.getpid()}-{secrets.token_hex(3)}")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    with contextlib.suppress(Exception):
        temporary.chmod(0o600)
    os.replace(temporary, path)


def _audit_datetime(record: Dict[str, Any]) -> dt.datetime:
    raw = str(record.get("timestamp") or "").strip()
    try:
        parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone()
    except (ValueError, TypeError):
        return dt.datetime.now().astimezone()


def _audit_day(record: Dict[str, Any]) -> dt.date:
    return _audit_datetime(record).date()


def _audit_record_id(record: Dict[str, Any]) -> str:
    existing = str(record.get("id") or "").strip()
    if existing:
        return existing
    material = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8", errors="replace")).hexdigest()[:32]


def _detail_as_text(value: Any) -> str:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    text = str(value or "").strip()
    return text or "—"


def _audit_txt_labels() -> Dict[str, str]:
    if EDITION_LANGUAGE == "el":
        return {
            "record_id": "Αναγνωριστικό εγγραφής", "local_time": "Τοπική ημερομηνία/ώρα", "utc_time": "Ημερομηνία/ώρα UTC",
            "event": "Συμβάν", "result": "Αποτέλεσμα", "success": "ΕΠΙΤΥΧΙΑ", "failed": "ΑΠΟΤΥΧΙΑ",
            "actor": "Χρήστης", "role": "Ρόλος", "session_id": "Αναγνωριστικό συνεδρίας", "request_id": "Αναγνωριστικό αιτήματος",
            "ip": "Διεύθυνση IP", "method": "Μέθοδος", "endpoint": "Σημείο λειτουργίας", "path": "Διαδρομή", "query": "Παράμετροι αιτήματος",
            "host": "Κεντρικός υπολογιστής", "scheme": "Πρωτόκολλο", "status_code": "Κωδικός κατάστασης", "duration": "Διάρκεια",
            "request_type": "Τύπος περιεχομένου αιτήματος", "request_length": "Μέγεθος περιεχομένου αιτήματος",
            "response_type": "Τύπος περιεχομένου απόκρισης", "response_length": "Μέγεθος περιεχομένου απόκρισης",
            "range": "Κεφαλίδα Range", "referer": "Σελίδα προέλευσης", "user_agent": "Συσκευή / πρόγραμμα περιήγησης",
            "server_profile": "Προφίλ διακομιστή", "server_root": "Ριζικός φάκελος διακομιστή", "details": "Λεπτομέρειες",
            "daily_log": "Ημερήσια καταγραφή ελέγχου", "records": "Εγγραφές", "log_export": "Εξαγωγή καταγραφών",
            "server": "Διακομιστής", "requested_range": "Επιλεγμένο εύρος", "daily_files": "Ημερήσια αρχεία",
            "total_records": "Συνολικές εγγραφές", "not_deleted": "Η εξαγωγή δεν διέγραψε ούτε τροποποίησε τις αρχικές καταγραφές του διακομιστή.",
        }
    return {
        "record_id": "Record ID", "local_time": "Local date/time", "utc_time": "UTC date/time", "event": "Event",
        "result": "Result", "success": "SUCCESS", "failed": "FAILED", "actor": "Actor", "role": "Role",
        "session_id": "Session ID", "request_id": "Request ID", "ip": "IP address", "method": "Method", "endpoint": "Endpoint",
        "path": "Path", "query": "Query", "host": "Host", "scheme": "Scheme", "status_code": "Status code", "duration": "Duration",
        "request_type": "Request content type", "request_length": "Request content length", "response_type": "Response content type",
        "response_length": "Response content length", "range": "Range header", "referer": "Referer", "user_agent": "User agent",
        "server_profile": "Server profile", "server_root": "Server root", "details": "Details", "daily_log": "Daily audit log",
        "records": "Records", "log_export": "Log export", "server": "Server", "requested_range": "Requested range",
        "daily_files": "Daily files", "total_records": "Total records",
        "not_deleted": "The original server logs were not deleted or changed by this export.",
    }


def format_audit_record_text(record: Dict[str, Any]) -> str:
    labels = _audit_txt_labels()
    local_time = _audit_datetime(record)
    lines = [
        "=" * 78,
        f"{labels['record_id']}: {_audit_record_id(record)}",
        f"{labels['local_time']}: {local_time.strftime('%d/%m/%Y %H:%M:%S %Z')}",
        f"{labels['utc_time']}: {record.get('timestamp', '—')}",
        f"{labels['event']}: {audit_event_label(str(record.get('event', '')))} ({record.get('event', '—')})",
        f"{labels['result']}: {labels['success'] if bool(record.get('success', False)) else labels['failed']}",
        f"{labels['actor']}: {record.get('actor', '—')}",
        f"{labels['role']}: {record.get('role', '—')}",
        f"{labels['session_id']}: {record.get('session_id', '—')}",
        f"{labels['request_id']}: {record.get('request_id', '—')}",
        f"{labels['ip']}: {record.get('ip', '—')}",
        f"{labels['method']}: {record.get('method', '—')}",
        f"{labels['endpoint']}: {record.get('endpoint', '—')}",
        f"{labels['path']}: {record.get('path', '—')}",
        f"{labels['query']}: {record.get('query', '—')}",
        f"{labels['host']}: {record.get('host', '—')}",
        f"{labels['scheme']}: {record.get('scheme', '—')}",
        f"{labels['status_code']}: {record.get('status_code', '—')}",
        f"{labels['duration']}: {record.get('duration_ms', '—')} ms",
        f"{labels['request_type']}: {record.get('content_type', '—')}",
        f"{labels['request_length']}: {record.get('content_length', '—')}",
        f"{labels['response_type']}: {record.get('response_content_type', '—')}",
        f"{labels['response_length']}: {record.get('response_content_length', '—')}",
        f"{labels['range']}: {record.get('range', '—')}",
        f"{labels['referer']}: {record.get('referer', '—')}",
        f"{labels['user_agent']}: {record.get('user_agent', '—')}",
        f"{labels['server_profile']}: {record.get('server_profile', '—')}",
        f"{labels['server_root']}: {record.get('server_root', '—')}",
        f"{labels['details']}:",
        _detail_as_text(record.get("detail")),
        "",
    ]
    return "\n".join(lines)


def _read_jsonl_records(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    output: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    item = json.loads(line)
                except Exception:
                    continue
                if isinstance(item, dict):
                    item["id"] = _audit_record_id(item)
                    output.append(item)
    except OSError:
        return []
    return output


def _write_jsonl_records(path: Path, records: List[Dict[str, Any]]) -> None:
    content = "".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in records)
    _atomic_text_write(path, content)


def consolidate_previous_audit_logs() -> None:
    with AUDIT_LOCK:
        live_path = audit_log_path()
        live_records = _read_jsonl_records(live_path)
        if not live_records:
            return
        today = dt.datetime.now().astimezone().date()
        previous = [item for item in live_records if _audit_day(item) < today]
        if not previous:
            return
        current = [item for item in live_records if _audit_day(item) >= today]
        history = _read_jsonl_records(audit_history_path())
        merged: Dict[str, Dict[str, Any]] = {_audit_record_id(item): item for item in history}
        for item in previous:
            merged[_audit_record_id(item)] = item
        history_records = sorted(merged.values(), key=lambda item: str(item.get("timestamp", "")))
        _write_jsonl_records(audit_history_path(), history_records)
        affected_days = sorted({_audit_day(item) for item in previous})
        for day in affected_days:
            day_records = [item for item in history_records if _audit_day(item) == day]
            labels = _audit_txt_labels()
            heading = (
                f"{APP_NAME} — {ACTIVE_PROFILE.get('name', ACTIVE_PROFILE.get('id', labels['server']))}\n"
                f"{labels['daily_log']}: {day.strftime('%d/%m/%Y')}\n"
                f"{labels['records']}: {len(day_records)}\n\n"
            )
            body = heading + "".join(format_audit_record_text(item) for item in day_records)
            _atomic_text_write(audit_daily_path(day), body)
        _write_jsonl_records(live_path, current)


def upload_work_dir() -> Path:
    directory = server_internal_dir() / "uploads"
    directory.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(Exception):
        directory.chmod(0o700)
    return directory


def cleanup_stale_uploads(max_age_seconds: int = 24 * 60 * 60) -> None:
    cutoff = time.time() - max_age_seconds
    directory = upload_work_dir()
    for item in directory.iterdir():
        try:
            if item.stat().st_mtime < cutoff:
                item.unlink(missing_ok=True)
        except OSError:
            continue


def disk_allows_upload(target: Path, expected_total: int, already_written: int = 0) -> bool:
    try:
        usage = shutil.disk_usage(target)
        remaining = max(0, int(expected_total) - max(0, int(already_written)))
        predicted_used = int(usage.used) + remaining
        return usage.total > 0 and (predicted_used / usage.total) < 0.85
    except (OSError, ValueError, TypeError):
        return False


def session_registry_path() -> Path:
    return server_internal_dir() / "sessions.json"


def _load_session_registry() -> Dict[str, Dict[str, Any]]:
    path = session_registry_path()
    with SESSION_REGISTRY_LOCK:
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}


def _save_session_registry(data: Dict[str, Dict[str, Any]]) -> None:
    with SESSION_REGISTRY_LOCK:
        _atomic_json_write(session_registry_path(), data)



def _sanitized_mapping(values: Any) -> Dict[str, Any]:
    protected_fragments = ("password", "passwd", "secret", "token", "csrf", "key")
    result: Dict[str, Any] = {}
    try:
        keys = list(values.keys())
    except Exception:
        return result
    for key in keys[:80]:
        lowered = str(key).casefold()
        if any(fragment in lowered for fragment in protected_fragments):
            result[str(key)] = "[REDACTED]"
            continue
        try:
            items = values.getlist(key)
        except Exception:
            items = [values.get(key)]
        cleaned = [str(item)[:500] for item in items]
        result[str(key)] = cleaned if len(cleaned) > 1 else (cleaned[0] if cleaned else "")
    return result


def _request_files_summary() -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    try:
        items = request.files.items(multi=True)
    except Exception:
        return output
    for field, storage in items:
        output.append({
            "field": str(field),
            "filename": str(getattr(storage, "filename", ""))[:500],
            "content_type": str(getattr(storage, "content_type", ""))[:200],
            "content_length": getattr(storage, "content_length", None),
        })
    return output[:100]


def audit_event(event: str, detail: Any = "", *, success: bool = True, actor: str = "", extra: Optional[Dict[str, Any]] = None) -> None:
    try:
        consolidate_previous_audit_logs()
        in_request = has_request_context()
        current_role = role() if in_request else "system"
        current_actor = current_admin() if in_request and current_role == "admin" else current_role
        request_id = str(getattr(g, "audit_request_id", "")) if in_request else secrets.token_hex(8)
        record: Dict[str, Any] = {
            "id": secrets.token_hex(16),
            "timestamp": _utc_now(),
            "event": str(event)[:120],
            "success": bool(success),
            "actor": actor or current_actor or "system",
            "role": current_role or "system",
            "session_id": str(session.get("access_session_id") or "") if in_request else "",
            "request_id": request_id,
            "ip": request.remote_addr if in_request else "local",
            "method": request.method if in_request else "CLI",
            "endpoint": str(request.endpoint or "") if in_request else "",
            "path": request.path if in_request else "",
            "query": request.query_string.decode("utf-8", errors="replace")[:4000] if in_request else "",
            "host": request.host if in_request else "local",
            "scheme": request.scheme if in_request else "",
            "content_type": request.content_type or "" if in_request else "",
            "content_length": request.content_length if in_request else None,
            "range": request.headers.get("Range", "") if in_request else "",
            "referer": request.headers.get("Referer", "")[:1000] if in_request else "",
            "user_agent": str(request.user_agent)[:1000] if in_request else "",
            "server_profile": str(ACTIVE_PROFILE.get("name") or ACTIVE_PROFILE.get("id") or ""),
            "server_root": str(ACTIVE_ROOT),
            "detail": detail,
        }
        if extra:
            for key, value in extra.items():
                record[str(key)[:80]] = value
        with AUDIT_LOCK:
            path = audit_log_path()
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    except Exception:
        pass


def read_audit_events(limit: int = 0) -> List[Dict[str, Any]]:
    consolidate_previous_audit_logs()
    records = _read_jsonl_records(audit_history_path()) + _read_jsonl_records(audit_log_path())
    unique: Dict[str, Dict[str, Any]] = {}
    for item in records:
        unique[_audit_record_id(item)] = item
    events = sorted(unique.values(), key=lambda item: str(item.get("timestamp", "")), reverse=True)
    return events if limit <= 0 else events[:max(1, limit)]


def audit_events_in_range(start: dt.date, end: dt.date) -> List[Dict[str, Any]]:
    return [item for item in read_audit_events() if start <= _audit_day(item) <= end]


def create_logs_export(start: dt.date, end: dt.date) -> Optional[Path]:
    events = audit_events_in_range(start, end)
    if not events:
        return None
    export_dir = server_internal_dir() / "log-exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    cleanup_stale_uploads()
    filename = f"DedSec-Server-Logs_{start.strftime('%d-%m-%Y')}_to_{end.strftime('%d-%m-%Y')}.zip"
    destination = export_dir / filename
    grouped: Dict[dt.date, List[Dict[str, Any]]] = {}
    for item in events:
        grouped.setdefault(_audit_day(item), []).append(item)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        for day in sorted(grouped):
            records = sorted(grouped[day], key=lambda item: str(item.get("timestamp", "")))
            labels = _audit_txt_labels()
            header = (
                f"{APP_NAME} — {ACTIVE_PROFILE.get('name', ACTIVE_PROFILE.get('id', labels['server']))}\n"
                f"{labels['daily_log']}: {day.strftime('%d/%m/%Y')}\n"
                f"{labels['records']}: {len(records)}\n\n"
            )
            archive.writestr(day.strftime("%d-%m-%Y.txt"), header + "".join(format_audit_record_text(item) for item in records))
        labels = _audit_txt_labels()
        summary = (
            f"{APP_NAME} — {labels['log_export']}\n"
            f"{labels['server']}: {ACTIVE_PROFILE.get('name', ACTIVE_PROFILE.get('id', labels['server']))}\n"
            f"{labels['requested_range']}: {start.strftime('%d/%m/%Y')} - {end.strftime('%d/%m/%Y')}\n"
            f"{labels['daily_files']}: {len(grouped)}\n"
            f"{labels['total_records']}: {len(events)}\n"
            f"{labels['not_deleted']}\n"
        )
        archive.writestr("README.txt", summary)
    return destination


def register_access_session(role_name: str, username: str) -> None:
    session_id = secrets.token_urlsafe(18)
    session["access_session_id"] = session_id
    session["registry_touch"] = int(time.time())
    now = _utc_now()
    registry = _load_session_registry()
    registry[session_id] = {
        "id": session_id,
        "role": role_name,
        "username": username or ("guest" if role_name == "guest" else DEFAULT_ADMIN_USERNAME),
        "ip": request.remote_addr or "unknown",
        "user_agent": str(request.user_agent)[:500],
        "signed_in": now,
        "last_seen": now,
        "ended_at": "",
    }
    _save_session_registry(registry)


def touch_access_session() -> None:
    if not role():
        return
    session_id = str(session.get("access_session_id") or "")
    if not session_id:
        register_access_session(role(), current_admin() if is_admin() else "guest")
        return
    now_epoch = int(time.time())
    if now_epoch - int(session.get("registry_touch") or 0) < 60:
        return
    session["registry_touch"] = now_epoch
    registry = _load_session_registry()
    item = registry.get(session_id)
    if item:
        item["last_seen"] = _utc_now()
        item["ip"] = request.remote_addr or item.get("ip", "unknown")
        registry[session_id] = item
        _save_session_registry(registry)


def end_access_session() -> None:
    session_id = str(session.get("access_session_id") or "")
    if not session_id:
        return
    registry = _load_session_registry()
    item = registry.get(session_id)
    if item:
        item["last_seen"] = _utc_now()
        item["ended_at"] = _utc_now()
        registry[session_id] = item
        _save_session_registry(registry)

@app.before_request
def _security_context():
    session.permanent = True
    csrf_token()
    touch_access_session()
    g.audit_request_id = secrets.token_hex(10)
    g.audit_started = time.monotonic()


@app.after_request
def _security_headers(response: Response):
    try:
        duration_ms = round((time.monotonic() - float(getattr(g, "audit_started", time.monotonic()))) * 1000, 2)
        detail = {
            "arguments": _sanitized_mapping(request.args),
            "form": _sanitized_mapping(request.form),
            "files": _request_files_summary(),
            "remote_port": request.environ.get("REMOTE_PORT"),
            "forwarded_for": request.headers.get("X-Forwarded-For", ""),
            "accept": request.headers.get("Accept", "")[:1000],
            "accept_language": request.headers.get("Accept-Language", "")[:500],
        }
        audit_event(
            "http_request",
            detail,
            success=response.status_code < 400,
            extra={
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "response_content_type": response.content_type or "",
                "response_content_length": response.calculate_content_length(),
            },
        )
    except Exception:
        pass
    response.headers.setdefault("Cache-Control", "no-store")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'",
    )
    query_theme = request.args.get("theme", "")
    if query_theme in ("dark", "light"):
        response.set_cookie("DEDSEC_THEME", query_theme, max_age=365 * 86400, samesite="Lax", secure=request.is_secure)
    return response


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------

CATEGORY_EXTENSIONS = {
    "documents": {".pdf", ".txt", ".md", ".rtf", ".doc", ".docx", ".odt", ".xls", ".xlsx", ".ods", ".ppt", ".pptx", ".odp", ".csv", ".epub"},
    "images": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".ico", ".heic", ".avif"},
    "videos": {".mp4", ".mkv", ".webm", ".avi", ".mov", ".m4v", ".3gp", ".mpeg", ".mpg"},
    "audio": {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus", ".wma"},
    "archives": {".zip", ".7z", ".rar", ".tar", ".gz", ".bz2", ".xz", ".tgz", ".apk", ".deb", ".rpm"},
    "code": {".py", ".sh", ".bash", ".js", ".ts", ".html", ".htm", ".css", ".json", ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".c", ".h", ".cpp", ".hpp", ".java", ".kt", ".go", ".rs", ".php", ".rb", ".sql"},
    "apps": {".exe", ".msi", ".appimage", ".dmg", ".pkg", ".jar"},
}
VALID_CATEGORIES = {"all", "folders", *CATEGORY_EXTENSIONS.keys(), "other"}


def entry_category(path: Path) -> str:
    if path.is_dir():
        return "folders"
    suffix = path.suffix.lower()
    for category, extensions in CATEGORY_EXTENSIONS.items():
        if suffix in extensions:
            return category
    return "other"


def safe_path(relative: str = "", *, must_exist: bool = True) -> Path:
    relative = urllib.parse.unquote(relative or "").replace("\\", "/").lstrip("/")
    parts = Path(relative).parts
    if parts and parts[0] == INTERNAL_DIR_NAME:
        raise ValueError(tr("invalid_path"))
    candidate = (ACTIVE_ROOT / relative).resolve(strict=must_exist)
    root = ACTIVE_ROOT.resolve(strict=True)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(tr("invalid_path")) from exc
    return candidate


def relative_path(path: Path) -> str:
    return path.resolve(strict=False).relative_to(ACTIVE_ROOT.resolve(strict=True)).as_posix()


def _path_is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def validate_entry_name(name: str) -> str:
    name = name.strip()
    if not valid_name(name):
        raise ValueError(tr("invalid_path"))
    return name


def unique_destination(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    index = 2
    while True:
        candidate = directory / f"{stem} ({index}){suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def human_size(size: int) -> str:
    value = float(max(size, 0))
    units = ("B", "KB", "MB", "GB", "TB")
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{int(value)} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def format_time(timestamp: float) -> str:
    if not timestamp:
        return "—"
    try:
        return dt.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "—"


def folder_size(path: Path) -> int:
    total = 0
    for root, _, files in os.walk(path, followlinks=False):
        for filename in files:
            with contextlib.suppress(OSError):
                total += (Path(root) / filename).stat().st_size
    return total


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(4 * 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _clamp_int(value: Any, minimum: int, maximum: int, default: int) -> int:
    try:
        return max(minimum, min(maximum, int(str(value).strip())))
    except (TypeError, ValueError):
        return default


SIZE_RANGE_MAX_MB = 10_000
DATE_RANGE_MIN = dt.date(2004, 8, 14)


def parse_size_range(value: str) -> Tuple[int, int]:
    minimum, maximum = 0, SIZE_RANGE_MAX_MB
    try:
        left, right = str(value or "").split(":", 1)
        minimum = _clamp_int(left, 0, SIZE_RANGE_MAX_MB, 0)
        maximum = _clamp_int(right, 0, SIZE_RANGE_MAX_MB, SIZE_RANGE_MAX_MB)
    except ValueError:
        pass
    if minimum > maximum:
        minimum, maximum = maximum, minimum
    return minimum, maximum


def parse_date_range(value: str) -> Tuple[dt.date, dt.date]:
    today = dt.datetime.now().astimezone().date()
    start, end = DATE_RANGE_MIN, today
    try:
        raw_start, raw_end = str(value or "").split("|", 1)
        if raw_start:
            start = dt.date.fromisoformat(raw_start)
        if raw_end:
            end = dt.date.fromisoformat(raw_end)
    except (ValueError, TypeError):
        start, end = DATE_RANGE_MIN, today
    start = max(DATE_RANGE_MIN, min(today, start))
    end = max(DATE_RANGE_MIN, min(today, end))
    if start > end:
        start, end = end, start
    return start, end


def format_iso_datetime(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "—"
    try:
        parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone()
        return parsed.strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return raw


def iter_entries(
    current: Path,
    query: str,
    category: str,
    size_filter: str = "",
    date_filter: str = "",
    sort_by: str = "name",
    order: str = "asc",
    limit: int = 2000,
) -> List[Dict[str, Any]]:
    query_fold = query.casefold().strip()
    candidates: Iterable[Path]
    if query_fold:
        candidates = ACTIVE_ROOT.rglob("*")
    else:
        candidates = current.iterdir()

    minimum_mb, maximum_mb = parse_size_range(size_filter)
    minimum_bytes = minimum_mb * 1024 * 1024
    maximum_bytes = maximum_mb * 1024 * 1024
    size_range_active = minimum_mb > 0 or maximum_mb < SIZE_RANGE_MAX_MB
    start_date, end_date = parse_date_range(date_filter)
    start_timestamp = dt.datetime.combine(start_date, dt.time.min).timestamp()
    end_timestamp = dt.datetime.combine(end_date + dt.timedelta(days=1), dt.time.min).timestamp()

    entries: List[Dict[str, Any]] = []
    for path in candidates:
        if len(entries) >= limit:
            break
        try:
            resolved = path.resolve(strict=True)
            relative_parts = resolved.relative_to(ACTIVE_ROOT.resolve(strict=True)).parts
            if relative_parts and relative_parts[0] == INTERNAL_DIR_NAME:
                continue
            if query_fold and query_fold not in path.name.casefold():
                continue
            cat = entry_category(resolved)
            if category != "all" and cat != category:
                continue
            stat = resolved.stat()
            is_dir = resolved.is_dir()
            item_size = 0 if is_dir else stat.st_size

            if is_dir:
                if size_range_active:
                    continue
            else:
                if item_size < minimum_bytes:
                    continue
                if maximum_mb < SIZE_RANGE_MAX_MB and item_size > maximum_bytes:
                    continue

            if stat.st_mtime < start_timestamp or stat.st_mtime >= end_timestamp:
                continue

            entries.append(
                {
                    "name": path.name,
                    "rel": relative_path(resolved),
                    "is_dir": is_dir,
                    "category": cat,
                    "size": item_size,
                    "size_text": "—" if is_dir else human_size(item_size),
                    "modified": stat.st_mtime,
                    "modified_text": format_time(stat.st_mtime),
                }
            )
        except (OSError, ValueError):
            continue

    sort_keys = {
        "name": lambda item: item["name"].casefold(),
        "size": lambda item: item["size"],
        "date": lambda item: item["modified"],
        "type": lambda item: (item["category"], item["name"].casefold()),
    }
    key_function = sort_keys.get(sort_by, sort_keys["name"])
    entries.sort(key=key_function, reverse=(order == "desc"))
    entries.sort(key=lambda item: not item["is_dir"])
    return entries


def safe_next_url(value: str) -> str:
    if not value:
        return url_for("browse") if role() else url_for("access")
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme or parsed.netloc or not value.startswith("/"):
        return url_for("browse") if role() else url_for("access")
    return value


COMMENTS_LOCK = threading.RLock()


def _comments_file() -> Path:
    profile_id = slugify(str(ACTIVE_PROFILE.get("id", "server")))
    return COMMENTS_DIR / f"{profile_id}.json"


def load_comments() -> Dict[str, List[Dict[str, str]]]:
    path = _comments_file()
    with COMMENTS_LOCK:
        if not path.exists():
            return {}
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        if not isinstance(raw, dict):
            return {}
        clean: Dict[str, List[Dict[str, str]]] = {}
        for entry, values in raw.items():
            if not isinstance(entry, str) or not isinstance(values, list):
                continue
            items = []
            for value in values:
                if not isinstance(value, dict):
                    continue
                text = str(value.get("text", "")).strip()
                if not text:
                    continue
                items.append({
                    "id": str(value.get("id") or secrets.token_urlsafe(8)),
                    "author": str(value.get("author") or "admin"),
                    "text": text[:2000],
                    "created_at": str(value.get("created_at") or _utc_now()),
                })
            if items:
                clean[entry.strip("/")] = items
        return clean


def save_comments(comments: Dict[str, List[Dict[str, str]]]) -> None:
    with COMMENTS_LOCK:
        _atomic_json_write(_comments_file(), comments)


def move_comment_tree(old_relative: str, new_relative: str) -> None:
    old_key = old_relative.strip("/")
    new_key = new_relative.strip("/")
    if not old_key or old_key == new_key:
        return
    comments = load_comments()
    changed = False
    for key in list(comments):
        if key == old_key or key.startswith(old_key + "/"):
            suffix = key[len(old_key):]
            comments[new_key + suffix] = comments.pop(key)
            changed = True
    if changed:
        save_comments(comments)


def delete_comment_tree(relative: str) -> None:
    key_prefix = relative.strip("/")
    if not key_prefix:
        return
    comments = load_comments()
    changed = False
    for key in list(comments):
        if key == key_prefix or key.startswith(key_prefix + "/"):
            comments.pop(key, None)
            changed = True
    if changed:
        save_comments(comments)


# ---------------------------------------------------------------------------
# Responsive ButSystem-palette UI
# ---------------------------------------------------------------------------

BASE_TEMPLATE = r"""
<!doctype html>
<html lang="{{ lang }}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="{{ '#ffffff' if theme == 'light' else '#000000' }}">
  <title>{{ title }}</title>
  <style>
    :root{
      --bg:#000000;
      --panel:#0e0d18;
      --panel2:rgba(18,18,30,.52);
      --nav:#0b0a12;
      --border:rgba(205,147,255,.50);
      --text:rgba(255,255,255,.92);
      --muted:rgba(255,255,255,.74);
      --accent:#cd93ff;
      --accent-hover:#e2c1ff;
      --danger:#ff6b6b;
      --success:#51cf66;
      --warning:#ffd43b;
      --text-on-accent:#0b0a12;
      --shadow:0 18px 50px rgba(0,0,0,.42);
      --radius:22px;
      --radius-sm:15px;
      --app-font:system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans","Helvetica Neue",Arial,sans-serif;
    }
    body.light-theme{
      --bg:#ffffff;
      --panel:#ffffff;
      --panel2:rgba(255,255,255,.62);
      --nav:#ffffff;
      --border:rgba(123,31,162,.35);
      --text:rgba(10,10,18,.92);
      --muted:rgba(10,10,18,.70);
      --accent:#7b1fa2;
      --accent-hover:#9c27b0;
      --danger:#d6336c;
      --success:#2f9e44;
      --warning:#f59f00;
      --text-on-accent:rgba(255,255,255,.96);
      --shadow:0 18px 50px rgba(0,0,0,.16);
    }
    *{box-sizing:border-box}
    html{height:100%;overflow-x:hidden;-webkit-text-size-adjust:100%;text-size-adjust:100%}
    body{margin:0;min-height:100dvh;overflow-x:hidden;background:var(--bg);color:var(--text);font-family:var(--app-font);padding-bottom:env(safe-area-inset-bottom);caret-color:var(--accent)}
    body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:-1;background:radial-gradient(circle at 12% -10%,rgba(205,147,255,.16),transparent 36rem),radial-gradient(circle at 100% 10%,rgba(123,31,162,.10),transparent 34rem)}
    body.light-theme::before{background:radial-gradient(circle at 10% -10%,rgba(123,31,162,.10),transparent 34rem),radial-gradient(circle at 100% 15%,rgba(205,147,255,.10),transparent 30rem)}
    a{color:var(--accent);text-decoration:none}a:hover{color:var(--accent-hover)}
    button,input,select,textarea{font:inherit}button{touch-action:manipulation}
    ::selection{background:rgba(205,147,255,.35);color:var(--text)}
    :focus-visible{outline:3px solid color-mix(in srgb,var(--accent) 74%,transparent);outline-offset:3px}
    .topbar{position:sticky;top:0;z-index:50;background:color-mix(in srgb,var(--nav) 91%,transparent);backdrop-filter:blur(18px);border-bottom:1px solid var(--border);padding-top:env(safe-area-inset-top)}
    .topbar-inner{width:min(100%,1600px);margin:auto;padding:10px max(12px,env(safe-area-inset-right)) 10px max(12px,env(safe-area-inset-left));display:flex;align-items:center;gap:12px;justify-content:space-between}
    .brand{min-width:0;display:flex;align-items:center;gap:10px;color:var(--text);font-weight:900;letter-spacing:.045em}
    .brand:hover{color:var(--text)}
    .brand-copy{min-width:0}.brand-title{display:block;font-size:clamp(1.22rem,2.15vw,1.68rem);line-height:1.05;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.brand-server{display:block;color:var(--muted);font-size:clamp(.9rem,1.35vw,1.12rem);line-height:1.2;font-weight:720;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:min(48vw,620px);letter-spacing:0;margin-top:3px}
    .toolbar{display:flex;align-items:center;justify-content:flex-end;gap:7px;flex-wrap:wrap}
    .container{width:min(100%,1600px);margin:auto;padding:clamp(12px,2.2vw,28px) max(12px,env(safe-area-inset-right)) clamp(24px,4vw,48px) max(12px,env(safe-area-inset-left))}
    .card{background:color-mix(in srgb,var(--panel) 94%,transparent);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow)}
    .btn{min-height:44px;display:inline-flex;align-items:center;justify-content:center;gap:8px;border:1px solid var(--border);border-radius:15px;background:var(--panel2);color:var(--text);padding:9px 14px;font-weight:760;line-height:1.15;cursor:pointer;transition:transform .15s ease,border-color .15s ease,background .15s ease;color .15s ease;max-width:100%;overflow-wrap:anywhere}
    .btn:hover{color:var(--text);border-color:var(--accent);background:color-mix(in srgb,var(--panel2) 70%,var(--accent) 8%);transform:translateY(-1px)}
    .btn.primary{background:var(--accent);border-color:var(--accent);color:var(--text-on-accent)}
    .btn.primary:hover{background:var(--accent-hover);border-color:var(--accent-hover);color:var(--text-on-accent)}
    .btn.danger{color:var(--danger);border-color:color-mix(in srgb,var(--danger) 58%,var(--border))}
    .btn.ghost{background:transparent}.btn.small{min-height:38px;padding:7px 10px;border-radius:13px;font-size:.86rem}.btn.theme-toggle{min-height:52px;padding:12px 19px;border-radius:18px;font-size:1.02rem;font-weight:850}.btn.theme-toggle span:first-child{font-size:1.28rem}.btn[disabled]{opacity:.55;cursor:not-allowed;transform:none}
    .badge{min-height:40px;display:inline-flex;align-items:center;justify-content:center;padding:8px 12px;border:1px solid var(--border);border-radius:999px;background:var(--panel2);color:var(--muted);font-size:.82rem;font-weight:780;white-space:nowrap}
    .badge.admin{color:var(--accent-hover)}.badge.guest{color:var(--muted)}
    .hero{padding:clamp(18px,3vw,32px);margin-bottom:16px;display:grid;gap:14px}
    .hero-row{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;flex-wrap:wrap}
    h1,h2,h3,p{overflow-wrap:anywhere}h1{font-size:clamp(1.55rem,4vw,2.45rem);line-height:1.11;margin:0}h2{font-size:clamp(1.1rem,2.6vw,1.45rem);margin:0}p{line-height:1.58}.muted{color:var(--muted)}.hero h1{font-size:clamp(2rem,5.4vw,3.35rem)}.hero-subtitle{font-size:clamp(1.02rem,2vw,1.28rem);font-weight:620;margin:.45rem 0 0}
    .notice{padding:13px 15px;border:1px solid var(--border);border-left:4px solid var(--success);border-radius:15px;background:var(--panel2);margin-bottom:14px;line-height:1.45}.notice.warning{border-left-color:var(--warning)}.notice.error{border-left-color:var(--danger)}
    .actions{display:flex;align-items:center;gap:9px;flex-wrap:wrap}.actions.stretch>.btn{flex:1 1 180px}
    .layout{display:grid;grid-template-columns:minmax(190px,235px) minmax(0,1fr);gap:16px;align-items:start}
    .sidebar{position:sticky;top:78px;padding:11px;display:grid;gap:4px;max-height:calc(100dvh - 100px);overflow:auto}
    .category-link{min-height:43px;display:flex;align-items:center;gap:9px;padding:9px 11px;border-radius:14px;color:var(--muted);font-weight:720;border:1px solid transparent;white-space:nowrap}
    .category-link:hover,.category-link.active{color:var(--text);background:var(--panel2);border-color:var(--border)}
    .main{min-width:0;display:grid;gap:16px}.browser-card{overflow:hidden}
    .browser-tools{padding:14px;border-bottom:1px solid var(--border);display:flex;gap:10px;align-items:center;flex-wrap:wrap;background:color-mix(in srgb,var(--panel2) 42%,transparent)}
    .search-form{display:grid;grid-template-columns:minmax(220px,1.35fr) minmax(310px,1.2fr) minmax(300px,1.05fr) repeat(2,minmax(135px,.58fr));gap:10px;flex:1 1 100%;min-width:0;align-items:end}.search-form .input{min-width:0}.search-form .btn{white-space:nowrap}.filter-field{display:grid;gap:7px;min-width:0}.filter-field>label{font-size:.78rem;font-weight:800;color:var(--muted);padding-left:3px}.filter-actions{display:flex;gap:8px;align-items:end;grid-column:1 / -1}.range-values{display:flex;justify-content:space-between;gap:10px;color:var(--muted);font-size:.8rem;font-weight:760}.range-values strong{color:var(--text);font-size:.9rem}.dual-range{position:relative;height:38px;display:flex;align-items:center;--range-start:0%;--range-end:100%}.range-track,.range-fill{position:absolute;left:0;right:0;height:8px;border-radius:999px;pointer-events:none}.range-track{background:color-mix(in srgb,var(--panel2) 76%,var(--border))}.range-fill{left:var(--range-start);right:calc(100% - var(--range-end));background:var(--accent);box-shadow:0 0 0 1px color-mix(in srgb,var(--accent) 72%,transparent)}.range-input{position:absolute;left:0;width:100%;height:38px;margin:0;appearance:none;-webkit-appearance:none;background:transparent;pointer-events:none}.range-input::-webkit-slider-runnable-track{height:8px;background:transparent}.range-input::-moz-range-track{height:8px;background:transparent}.range-input::-webkit-slider-thumb{appearance:none;-webkit-appearance:none;width:24px;height:24px;margin-top:-8px;border-radius:50%;border:3px solid var(--panel);background:var(--accent);box-shadow:0 0 0 2px var(--accent),0 5px 14px rgba(0,0,0,.28);pointer-events:auto;cursor:grab}.range-input::-moz-range-thumb{width:20px;height:20px;border-radius:50%;border:3px solid var(--panel);background:var(--accent);box-shadow:0 0 0 2px var(--accent),0 5px 14px rgba(0,0,0,.28);pointer-events:auto;cursor:grab}.range-input:active::-webkit-slider-thumb{cursor:grabbing;transform:scale(1.08)}.date-range-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.date-control{display:grid;gap:5px;color:var(--muted);font-size:.76rem;font-weight:780}.date-control .input{min-height:46px;color-scheme:dark}body.light-theme .date-control .input{color-scheme:light}.filter-help{font-size:.72rem;color:var(--muted);margin:0 3px}
    .input,.select,.textarea{width:100%;min-height:46px;border:1px solid var(--border);border-radius:14px;background:var(--panel2);color:var(--text);padding:10px 12px}.textarea{min-height:110px;resize:vertical}.input::placeholder{color:color-mix(in srgb,var(--muted) 78%,transparent)}
    .breadcrumbs{display:flex;gap:6px;align-items:center;flex-wrap:wrap;padding:12px 15px;border-bottom:1px solid var(--border);color:var(--muted);font-size:.9rem}.breadcrumbs a{color:var(--muted)}.breadcrumbs a:hover{color:var(--accent-hover)}
    .entries-head,.entry-row{display:grid;grid-template-columns:42px minmax(210px,1.8fr) minmax(110px,.65fr) minmax(90px,.55fr) minmax(135px,.7fr) minmax(250px,1.25fr);align-items:center}
    .entries-head{background:color-mix(in srgb,var(--panel2) 48%,transparent);border-bottom:1px solid var(--border);color:var(--muted);font-size:.76rem;font-weight:840;text-transform:uppercase;letter-spacing:.055em}
    .entries-head>div,.entry-row>div{padding:12px 13px;min-width:0}
    .entry-row{border-bottom:1px solid var(--border);transition:background .15s ease}.entry-row:last-child{border-bottom:0}.entry-row:hover{background:color-mix(in srgb,var(--panel2) 48%,transparent)}
    .entry-name{display:flex;align-items:flex-start;gap:10px;font-weight:780;min-width:0}.entry-icon{flex:0 0 auto;width:34px;height:34px;border-radius:12px;display:grid;place-items:center;background:var(--panel2);border:1px solid var(--border);font-size:1rem}.entry-text{min-width:0}.entry-title{display:block;color:var(--text);overflow-wrap:anywhere}.entry-path{display:block;color:var(--muted);font-size:.76rem;margin-top:3px;overflow-wrap:anywhere}
    .row-actions{display:flex;gap:6px;align-items:center;flex-wrap:wrap}.row-actions form{display:inline-flex;margin:0}.check{width:19px;height:19px;accent-color:var(--accent)}
    .empty{padding:clamp(34px,8vw,76px) 18px;text-align:center;color:var(--muted)}
    .login-wrap{width:min(100%,960px);margin:clamp(22px,7vh,80px) auto}.login-panel{padding:clamp(20px,4vw,38px)}
    .access-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:20px}.access-option{padding:clamp(18px,3vw,27px);display:flex;flex-direction:column;align-items:flex-start;gap:12px}.access-option .btn{margin-top:auto;width:100%}.access-option form{width:100%;margin-top:auto}.access-option form .btn{width:100%}
    .form-card{width:min(100%,760px);margin:clamp(14px,5vh,58px) auto;padding:clamp(18px,4vw,32px)}.form-grid{display:grid;gap:15px}.field{display:grid;gap:7px}.field label{color:var(--muted);font-weight:720;font-size:.92rem}
    .details-grid{display:grid;grid-template-columns:minmax(125px,190px) minmax(0,1fr);border:1px solid var(--border);border-radius:17px;overflow:hidden;margin-top:16px}.detail-key,.detail-value{padding:12px 14px;border-bottom:1px solid var(--border)}.detail-key{background:var(--panel2);color:var(--muted);font-weight:740}.detail-value{overflow-wrap:anywhere}.details-grid>*:nth-last-child(-n+2){border-bottom:0}
    .progress-shell{height:14px;border:1px solid var(--border);border-radius:999px;overflow:hidden;background:var(--panel2);margin-top:12px}.progress-bar{height:100%;width:0;background:var(--accent);transition:width .12s linear}.upload-list{display:grid;gap:8px;margin-top:14px}.upload-item{padding:10px 12px;border:1px solid var(--border);border-radius:13px;background:var(--panel2);display:flex;justify-content:space-between;gap:10px;align-items:center}
    .bulkbar{display:none;padding:10px 14px;border-bottom:1px solid var(--border);background:color-mix(in srgb,var(--accent) 8%,var(--panel2));align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}.bulkbar.visible{display:flex}
    .admin-nav{display:flex;gap:9px;flex-wrap:wrap;margin:14px 0 4px}.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.84rem}.status-ok{color:var(--success)}.status-bad{color:var(--danger)}
    .admin-section{margin-top:24px}.admin-section-title{margin-bottom:12px}.record-grid{display:grid;gap:12px;margin-top:12px}.accounts-grid{grid-template-columns:repeat(auto-fit,minmax(min(100%,250px),1fr))}.sessions-grid,.logs-grid{grid-template-columns:1fr}.record-card{min-width:0;padding:15px;border:1px solid var(--border);border-radius:18px;background:color-mix(in srgb,var(--panel2) 76%,transparent)}.record-card-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap;padding-bottom:12px;border-bottom:1px solid color-mix(in srgb,var(--border) 76%,transparent)}.record-title{font-size:1.03rem;line-height:1.3;overflow-wrap:break-word}.record-subtitle{display:block;margin-top:4px;color:var(--muted);font-size:.82rem;line-height:1.45}.record-fields{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px 16px;margin-top:14px}.record-field{min-width:0;display:grid;gap:4px;align-content:start}.record-field.full{grid-column:1 / -1}.record-label{color:var(--muted);font-size:.72rem;line-height:1.25;font-weight:850;text-transform:uppercase;letter-spacing:.055em}.record-value{min-width:0;font-size:.92rem;line-height:1.48;overflow-wrap:break-word;word-break:normal}.record-value.mono{overflow-wrap:anywhere;word-break:break-word}.device-value{font-size:.84rem;line-height:1.5;overflow-wrap:anywhere;word-break:break-word}.log-detail{margin:0;white-space:pre-wrap;max-height:360px;overflow:auto;padding:10px;border:1px solid var(--border);border-radius:12px;background:var(--panel2)}.status-pill{display:inline-flex;align-items:center;justify-content:center;min-height:32px;padding:6px 10px;border:1px solid var(--border);border-radius:999px;font-size:.78rem;font-weight:850;white-space:nowrap}.status-pill.ok{color:var(--success);border-color:color-mix(in srgb,var(--success) 60%,var(--border))}.status-pill.bad{color:var(--danger);border-color:color-mix(in srgb,var(--danger) 60%,var(--border))}.status-pill.neutral{color:var(--muted)}.path-box{margin-top:10px;padding:10px 12px;border:1px solid var(--border);border-radius:13px;background:var(--panel2);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.78rem;line-height:1.45;overflow-wrap:anywhere}.permission-note{margin:15px 0 0}.self-admin-card{border-color:color-mix(in srgb,var(--accent) 62%,var(--border))}
    .admin-page{width:min(100%,1180px)}.add-admin-form{margin:20px 0;padding:18px;border:1px solid var(--border);border-radius:18px;background:var(--panel2)}.admin-list{display:grid;gap:12px}.admin-card{padding:16px;border:1px solid var(--border);border-radius:18px;background:var(--panel2)}.admin-card-head,.comment-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap}.compact-form{margin-top:14px}.comments-section{margin-top:24px;padding-top:20px;border-top:1px solid var(--border)}.comments-list{display:grid;gap:10px;margin:14px 0}.comment-card{padding:14px;border:1px solid var(--border);border-radius:16px;background:var(--panel2)}.comment-card p{white-space:pre-wrap;margin:10px 0}.comment-card form{display:flex;justify-content:flex-end}.comments-empty{padding:24px}.comment-form{margin-top:15px}
    .mobile-category-toggle{display:none;width:100%}
    @media(max-width:1250px){.search-form{grid-template-columns:repeat(2,minmax(0,1fr))}.search-main{grid-column:1 / -1}.range-filter,.date-range-filter{grid-column:span 1}.filter-actions{grid-column:1 / -1}.filter-actions .btn{flex:1 1 180px}}
    @media(max-width:1100px){.entries-head,.entry-row{grid-template-columns:42px minmax(200px,1.65fr) minmax(95px,.55fr) minmax(125px,.7fr) minmax(230px,1.25fr)}.col-size{display:none}}
    @media(max-width:850px){
      .topbar-inner{align-items:flex-start}.brand-server{max-width:44vw}.toolbar{gap:6px}.toolbar .btn{padding:9px 11px}.toolbar .btn.theme-toggle{min-height:50px;min-width:50px;padding:10px 13px}.toolbar .badge{display:none}
      .layout{grid-template-columns:1fr}.mobile-category-toggle{display:flex}.sidebar{display:none;position:static;max-height:none;grid-template-columns:repeat(2,minmax(0,1fr))}.sidebar.open{display:grid}
      .entries-head{display:none}.entry-row{margin:11px;border:1px solid var(--border);border-radius:18px;display:grid;grid-template-columns:42px minmax(0,1fr);padding:12px;background:color-mix(in srgb,var(--panel) 95%,transparent);box-shadow:0 8px 28px rgba(0,0,0,.12)}.entry-row:hover{background:var(--panel)}
      .entry-row>div{padding:5px 7px}.entry-row .cell-check{grid-row:1 / span 4;align-self:start;padding-top:11px}.entry-row .cell-name{grid-column:2}.entry-row .cell-category,.entry-row .cell-size,.entry-row .cell-modified{grid-column:2;display:inline-flex;gap:7px;align-items:baseline}.entry-row .cell-actions{grid-column:2;margin-top:5px}.entry-row .cell-category::before{content:attr(data-label) ":";color:var(--muted);font-size:.75rem;font-weight:700}.entry-row .cell-size::before{content:attr(data-label) ":";color:var(--muted);font-size:.75rem;font-weight:700}.entry-row .cell-modified::before{content:attr(data-label) ":";color:var(--muted);font-size:.75rem;font-weight:700}.row-actions{width:100%}.row-actions .btn,.row-actions form{flex:1 1 125px}.row-actions form .btn{width:100%}
      .access-grid{grid-template-columns:1fr}.details-grid{grid-template-columns:1fr}.detail-key{padding-bottom:4px;border-bottom:0}.detail-value{padding-top:4px}.details-grid>*:nth-last-child(-n+2){border-bottom:initial}.details-grid>*:last-child{border-bottom:0}
    }
    @media(max-width:560px){
      .topbar-inner{gap:8px}.brand-title{font-size:1.08rem;max-width:46vw}.brand-server{font-size:.82rem;max-width:46vw}.toolbar .control-text{display:none}.toolbar .btn{min-width:46px;min-height:46px;padding:8px 10px}.toolbar .btn.theme-toggle{min-width:52px;min-height:52px}.toolbar .btn.danger{display:none}
      .container{padding-top:11px}.hero{border-radius:18px}.browser-tools{align-items:stretch}.search-form{grid-template-columns:1fr}.search-main,.range-filter,.date-range-filter,.filter-actions{grid-column:1}.date-range-grid{grid-template-columns:1fr 1fr}.search-form .btn{padding-left:11px;padding-right:11px}.actions>.btn{flex:1 1 145px}.sidebar{grid-template-columns:1fr 1fr}.entry-row{margin:9px;padding:9px}.entry-row .cell-check{grid-row:1 / span 5}.row-actions .btn,.row-actions form{flex-basis:100%}
      .access-option,.login-panel,.form-card{border-radius:18px}.upload-item{align-items:flex-start;flex-direction:column}.bulkbar .btn{width:100%}
      .record-fields{grid-template-columns:1fr}.record-field.full{grid-column:1}.record-card{padding:14px}.record-card-head{gap:8px}.admin-nav .btn{flex:1 1 130px}.admin-page{padding:16px}.path-box{font-size:.73rem}
    }
    @media(max-width:370px){.brand-title{font-size:.96rem;max-width:45vw}.brand-server{display:block;font-size:.73rem;max-width:45vw}.sidebar{grid-template-columns:1fr}.search-form{grid-template-columns:1fr}.search-main,.range-filter,.date-range-filter,.filter-actions{grid-column:1}.date-range-grid{grid-template-columns:1fr}.filter-actions{display:grid;grid-template-columns:1fr}.search-form .input{grid-column:1}.toolbar{flex-wrap:nowrap}.toolbar .btn{min-width:44px;padding:7px}}
    @media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;transition:none!important;animation:none!important}}
  </style>
</head>
<body class="{{ 'light-theme' if theme == 'light' else '' }}">
<header class="topbar">
  <div class="topbar-inner">
    <a class="brand" href="{{ home_url }}">
      <span class="brand-copy"><span class="brand-title">DedSec's Server</span><span class="brand-server">{{ server_name }}</span></span>
    </a>
    <nav class="toolbar" aria-label="{{ t('actions') }}">
      <a class="btn theme-toggle confirm-link" data-confirm="{{ t('confirm_theme') }}" href="{{ theme_url }}" aria-label="{{ t('theme') }}: {{ theme_label }}"><span aria-hidden="true">◐</span><span class="control-text">{{ theme_label }}</span></a>
      {% if role_name == 'admin' %}<a class="btn" href="{{ url_for('users') }}"><span aria-hidden="true">♙</span><span class="control-text">{{ t('users') }}</span></a><a class="btn" href="{{ url_for('logs') }}"><span aria-hidden="true">▤</span><span class="control-text">{{ t('logs') }}</span></a><a class="btn" href="{{ url_for('administrators') }}"><span aria-hidden="true">⚙</span><span class="control-text">{{ t('administrators') }}</span></a>{% endif %}
      {% if role_name %}<span class="badge {{ role_name }}">{{ (t('admin_mode') ~ ' · ' ~ admin_name) if role_name == 'admin' else t('guest_mode') }}</span>{% endif %}
      {% if role_name %}<a class="btn danger confirm-link" data-confirm="{{ t('confirm_logout') }}" href="{{ url_for('logout') }}"><span aria-hidden="true">↪</span><span class="control-text">{{ t('logout') }}</span></a>{% endif %}
    </nav>
  </div>
</header>
<main class="container {{ page_class }}">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for category, message in messages %}<div class="notice {{ category }}" role="status">{{ message }}</div>{% endfor %}
  {% endwith %}
  {{ content }}
</main>
<script>
  document.querySelectorAll('.confirm-link').forEach(function(link){link.addEventListener('click',function(event){if(!confirm(link.dataset.confirm||'Confirm?'))event.preventDefault();});});
  document.querySelectorAll('form[data-confirm]').forEach(function(form){form.addEventListener('submit',function(event){if(!confirm(form.dataset.confirm||'Confirm?'))event.preventDefault();});});
  document.querySelectorAll('[data-category-toggle]').forEach(function(button){button.addEventListener('click',function(){var nav=document.getElementById('categoryNav');if(!nav)return;var open=nav.classList.toggle('open');button.setAttribute('aria-expanded',open?'true':'false');button.querySelector('.toggle-copy').textContent=open?button.dataset.close:button.dataset.open;});});
  (function(){
    const shell=document.getElementById('sizeRange'), minimum=document.getElementById('sizeMinimum'), maximum=document.getElementById('sizeMaximum'), minimumValue=document.getElementById('sizeMinValue'), maximumValue=document.getElementById('sizeMaxValue');
    if(shell&&minimum&&maximum){
      const limit=Number(maximum.max||10000);
      function syncRange(changed){
        let low=Number(minimum.value), high=Number(maximum.value);
        if(low>high){if(changed===minimum){high=low;maximum.value=high;}else{low=high;minimum.value=low;}}
        minimumValue.textContent=String(low);
        maximumValue.textContent=high>=limit?String(limit)+'+':String(high);
        shell.style.setProperty('--range-start',(low/limit*100)+'%');
        shell.style.setProperty('--range-end',(high/limit*100)+'%');
        minimum.style.zIndex=low>limit-25?'5':'3';
        maximum.style.zIndex='4';
      }
      minimum.addEventListener('input',()=>syncRange(minimum));maximum.addEventListener('input',()=>syncRange(maximum));syncRange();
    }
    document.querySelectorAll('input[type="date"]').forEach(function(input){input.addEventListener('click',function(){if(typeof input.showPicker==='function'){try{input.showPicker();}catch(_){}}});});
  })();
  {{ extra_script }}
</script>
</body>
</html>
"""


def render_page(title: str, content: Markup, *, page_class: str = "", extra_script: str = "") -> str:
    lang = EDITION_LANGUAGE
    theme = current_theme()
    next_path = request.full_path.rstrip("?")
    target_theme = "light" if theme == "dark" else "dark"
    return render_template_string(
        BASE_TEMPLATE,
        title=f"{title} · {APP_NAME}",
        content=content,
        page_class=page_class,
        extra_script=Markup(extra_script),
        lang=lang,
        theme=theme,
        server_name=ACTIVE_PROFILE.get("name", APP_NAME),
        role_name=role(),
        admin_name=current_admin(),
        home_url=url_for("browse") if role() else url_for("access"),
        theme_url=url_for("preference", theme=target_theme, next=next_path),
        theme_label=tr(target_theme),
        t=tr,
    )


def h(value: Any) -> str:
    return html.escape(str(value), quote=True)


def icon_for(category: str, is_dir: bool) -> str:
    if is_dir:
        return "▰"
    return {"documents": "▤", "images": "▧", "videos": "▶", "audio": "♪", "archives": "▦", "code": "</>", "apps": "◆", "other": "•"}.get(category, "•")


def breadcrumbs(
    relative: str,
    category: str,
    query: str,
    size_filter: str,
    date_filter: str,
    sort_by: str,
    order: str,
) -> str:
    parts = [part for part in Path(relative).parts if part not in (".", "")]
    common = {
        "category": category,
        "q": query,
        "size": size_filter,
        "date": date_filter,
        "sort": sort_by,
        "order": order,
    }
    links = [f'<a href="{h(url_for("browse", path="", **common))}">{h(tr("root"))}</a>']
    accumulated: List[str] = []
    for part in parts:
        accumulated.append(part)
        links.append('<span aria-hidden="true">/</span>')
        links.append(f'<a href="{h(url_for("browse", path="/".join(accumulated), **common))}">{h(part)}</a>')
    return f'<nav class="breadcrumbs" aria-label="{h(tr("breadcrumb_label"))}">' + "".join(links) + "</nav>"


def category_sidebar(
    current_path: str,
    category: str,
    query: str,
    size_filter: str,
    date_filter: str,
    sort_by: str,
    order: str,
) -> str:
    keys = ("all", "folders", "documents", "images", "videos", "audio", "archives", "code", "apps", "other")
    links = []
    for key in keys:
        active = " active" if key == category else ""
        href = url_for(
            "browse",
            path=current_path,
            category=key,
            q=query,
            size=size_filter,
            date=date_filter,
            sort=sort_by,
            order=order,
        )
        links.append(f'<a class="category-link{active}" href="{h(href)}"><span aria-hidden="true">{h(icon_for(key, key == "folders"))}</span>{h(tr(key))}</a>')
    return (
        f'<button class="btn mobile-category-toggle" type="button" data-category-toggle aria-expanded="false" data-open="{h(tr("open_menu"))}" data-close="{h(tr("close_menu"))}"><span aria-hidden="true">☰</span><span class="toggle-copy">{h(tr("open_menu"))}</span></button>'
        + f'<aside id="categoryNav" class="card sidebar" aria-label="{h(tr("categories_label"))}">'
        + "".join(links)
        + "</aside>"
    )

# ---------------------------------------------------------------------------
# Web routes
# ---------------------------------------------------------------------------


@app.route("/preference")
def preference():
    response = make_response(redirect(safe_next_url(request.args.get("next", ""))))
    lang = request.args.get("lang", "")
    theme = request.args.get("theme", "")
    if theme in ("dark", "light"):
        response.set_cookie("DEDSEC_THEME", theme, max_age=365 * 86400, samesite="Lax", secure=request.is_secure)
    return response


@app.route("/")
def index():
    return redirect(url_for("browse") if role() else url_for("access"))


@app.route("/access")
def access():
    if role():
        return redirect(url_for("browse"))
    protected = profile_is_protected(ACTIVE_PROFILE)
    notice = f'<div class="notice warning">{h(tr("protected_admin_only"))}</div>' if protected else f'<div class="notice">{h(tr("open_server_guest_notice"))}</div>'
    description = ACTIVE_PROFILE.get("description", "")
    description_html = f'<p class="muted">{h(description)}</p>' if description else ""
    guest_card = ""
    if not protected:
        guest_card = f'''<article class="card access-option"><span class="entry-icon" aria-hidden="true">◇</span><h2>{h(tr('guest_continue'))}</h2><p class="muted">{h(tr('guest_help'))}</p><form method="post" action="{h(url_for('guest_login'))}"><input type="hidden" name="csrf" value="{h(csrf_token())}"><button class="btn" type="submit">{h(tr('guest_continue'))}</button></form></article>'''
    content = Markup(
        f'''
        <section class="login-wrap">
          <div class="card login-panel">
            <div class="hero-row"><div><h1>{h(ACTIVE_PROFILE['name'])}</h1>{description_html}<p class="muted">{h(tr('access_help'))}</p></div><span class="badge">{h(tr('protected') if protected else tr('public'))}</span></div>
            {notice}
            <div class="access-grid">
              <article class="card access-option"><span class="entry-icon" aria-hidden="true">◆</span><h2>{h(tr('admin_login'))}</h2><p class="muted">{h(tr('admin_login_help'))}</p><a class="btn primary" href="{h(url_for('admin_login'))}">{h(tr('admin_login'))}</a></article>
              {guest_card}
            </div>
          </div>
        </section>
        '''
    )
    return render_page(tr("access_title"), content)

@app.post("/guest")
def guest_login():
    if not verify_csrf():
        abort(400)
    if profile_is_protected(ACTIVE_PROFILE):
        audit_event("guest_login_blocked", tr("guest_not_allowed"), success=False, actor="guest")
        abort(403)
    session.clear()
    session.permanent = True
    session["profile_id"] = ACTIVE_PROFILE["id"]
    session["role"] = "guest"
    session["csrf"] = secrets.token_urlsafe(32)
    register_access_session("guest", "guest")
    audit_event("guest_login", "Guest read-only access", actor="guest")
    return redirect(url_for("browse"))

def _login_blocked(ip: str) -> bool:
    now = time.time()
    with LOGIN_LOCK:
        attempts = [stamp for stamp in LOGIN_ATTEMPTS.get(ip, []) if now - stamp < 600]
        LOGIN_ATTEMPTS[ip] = attempts
        return len(attempts) >= 8


def _record_login_failure(ip: str) -> None:
    with LOGIN_LOCK:
        LOGIN_ATTEMPTS.setdefault(ip, []).append(time.time())


def _clear_login_failures(ip: str) -> None:
    with LOGIN_LOCK:
        LOGIN_ATTEMPTS.pop(ip, None)


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if role() == "admin":
        return redirect(url_for("browse"))
    error = ""
    ip = request.remote_addr or "unknown"
    if request.method == "POST":
        if not verify_csrf():
            abort(400)
        if _login_blocked(ip):
            error = tr("rate_limited")
        else:
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            authenticated_username = verify_admin_credentials(ACTIVE_PROFILE, username, password)
            if authenticated_username:
                _clear_login_failures(ip)
                session.clear()
                session.permanent = True
                session["profile_id"] = ACTIVE_PROFILE["id"]
                session["role"] = "admin"
                session["admin_username"] = authenticated_username
                session["csrf"] = secrets.token_urlsafe(32)
                register_access_session("admin", authenticated_username)
                audit_event("admin_login", f"Administrator {authenticated_username} signed in", actor=authenticated_username)
                return redirect(url_for("browse"))
            _record_login_failure(ip)
            audit_event("admin_login_failed", f"Username={username}", success=False, actor=username or "unknown")
            error = tr("wrong_password")
    error_html = f'<div class="notice error">{h(error)}</div>' if error else ""
    content = Markup(
        f"""
        <section class="card form-card">
          <h1>{h(tr('admin_login'))}</h1><p class="muted">{h(tr('login_help'))}</p>{error_html}
          <form class="form-grid" method="post" action="{h(url_for('admin_login'))}">
            <input type="hidden" name="csrf" value="{h(csrf_token())}">
            <div class="field"><label for="username">{h(tr('admin_username'))}</label><input class="input" id="username" name="username" autocomplete="username" required autofocus></div>
            <div class="field"><label for="password">{h(tr('password'))}</label><input class="input" id="password" name="password" type="password" autocomplete="current-password" required></div>
            <div class="actions stretch"><button class="btn primary" type="submit">{h(tr('admin_login'))}</button><a class="btn" href="{h(url_for('access'))}">{h(tr('back'))}</a></div>
          </form>
        </section>
        """
    )
    return render_page(tr("login"), content)


@app.route("/logout")
def logout():
    audit_event("logout", "Access session ended")
    end_access_session()
    session.clear()
    return redirect(url_for("access"))



@app.route("/users")
def users():
    require_role(admin=True)
    _normalize_profile_admins(ACTIVE_PROFILE)
    primary_username = main_admin_username()
    account_cards = []
    for account in ACTIVE_PROFILE.get("admins", []):
        username = str(account.get("username", ""))
        account_type = tr("main_administrator") if username.casefold() == primary_username.casefold() else tr("admin_mode")
        account_cards.append(f'''<article class="record-card">
          <div class="record-card-head"><strong class="record-title">{h(username)}</strong><span class="status-pill neutral">{h(account_type)}</span></div>
          <div class="record-fields"><div class="record-field full"><span class="record-label">{h(tr("created"))}</span><span class="record-value">{h(format_iso_datetime(account.get("created_at", "")))}</span></div></div>
        </article>''')
    accounts_html = "".join(account_cards) or f'<div class="empty">{h(tr("no_admins"))}</div>'

    registry = _load_session_registry()
    session_cards = []
    for item in sorted(registry.values(), key=lambda value: str(value.get("last_seen", "")), reverse=True):
        active = not bool(item.get("ended_at"))
        status_text = tr("active") if active else tr("ended")
        status_class = "ok" if active else "neutral"
        role_text = tr("admin_mode") if item.get("role") == "admin" else tr("guest_mode")
        session_cards.append(f'''<article class="record-card">
          <div class="record-card-head"><div><strong class="record-title">{h(item.get("username", ""))}</strong><span class="record-subtitle">{h(role_text)}</span></div><span class="status-pill {status_class}">{h(status_text)}</span></div>
          <div class="record-fields">
            <div class="record-field"><span class="record-label">{h(tr("ip_address"))}</span><span class="record-value mono">{h(item.get("ip", ""))}</span></div>
            <div class="record-field"><span class="record-label">{h(tr("signed_in"))}</span><span class="record-value">{h(format_iso_datetime(item.get("signed_in", "")))}</span></div>
            <div class="record-field"><span class="record-label">{h(tr("last_seen"))}</span><span class="record-value">{h(format_iso_datetime(item.get("last_seen", "")))}</span></div>
            <div class="record-field full"><span class="record-label">{h(tr("user_agent"))}</span><span class="record-value device-value">{h(item.get("user_agent", ""))}</span></div>
          </div>
        </article>''')
    sessions_html = "".join(session_cards) or f'<div class="empty">{h(tr("no_sessions"))}</div>'
    content = Markup(f'''
      <section class="card form-card admin-page">
        <div class="hero-row"><div><h1>{h(tr('users'))}</h1><p class="muted">{h(tr('users_help'))}</p></div><a class="btn" href="{h(url_for('browse'))}">{h(tr('back'))}</a></div>
        <div class="admin-nav"><a class="btn primary" href="{h(url_for('administrators'))}">{h(tr('administrators'))}</a><a class="btn" href="{h(url_for('logs'))}">{h(tr('logs'))}</a></div>
        <section class="admin-section"><h2 class="admin-section-title">{h(tr('administrators'))}</h2><div class="record-grid accounts-grid">{accounts_html}</div></section>
        <section class="admin-section"><h2 class="admin-section-title">{h(tr('sessions'))}</h2><div class="record-grid sessions-grid">{sessions_html}</div></section>
      </section>
    ''')
    return render_page(tr("users"), content)


@app.route("/logs")
def logs():
    require_role(admin=True)
    today = dt.datetime.now().astimezone().date()
    raw_range = f"{request.args.get('date_from', '')}|{request.args.get('date_to', '')}"
    if request.args.get("date_from") or request.args.get("date_to"):
        date_from, date_to = parse_date_range(raw_range)
    else:
        date_from, date_to = DATE_RANGE_MIN, today
    events = audit_events_in_range(date_from, date_to)
    cards = []
    for item in events:
        ok = bool(item.get("success", False))
        result_class = "ok" if ok else "bad"
        result_text = tr("success") if ok else tr("failed")
        role_text = tr("admin_mode") if item.get("role") == "admin" else (tr("guest_mode") if item.get("role") == "guest" else item.get("role", ""))
        detail_text = _detail_as_text(item.get("detail"))
        request_line = " ".join(part for part in (str(item.get("method", "")), str(item.get("path", ""))) if part).strip() or "—"
        cards.append(f'''<article class="record-card">
          <div class="record-card-head"><div><strong class="record-title">{h(audit_event_label(item.get("event", "")))}</strong><span class="record-subtitle">{h(format_iso_datetime(item.get("timestamp", "")))}</span></div><span class="status-pill {result_class}">{h(result_text)}</span></div>
          <div class="record-fields">
            <div class="record-field"><span class="record-label">{h(tr("admin_username"))}</span><span class="record-value">{h(item.get("actor", ""))}</span></div>
            <div class="record-field"><span class="record-label">{h(tr("role_label"))}</span><span class="record-value">{h(role_text)}</span></div>
            <div class="record-field"><span class="record-label">{h(tr("ip_address"))}</span><span class="record-value mono">{h(item.get("ip", ""))}</span></div>
            <div class="record-field"><span class="record-label">{h(tr("request_label"))}</span><span class="record-value mono">{h(request_line)}</span></div>
            <div class="record-field"><span class="record-label">{h(tr("status_code"))}</span><span class="record-value">{h(item.get("status_code", "—"))}</span></div>
            <div class="record-field"><span class="record-label">{h(tr("duration"))}</span><span class="record-value">{h(item.get("duration_ms", "—"))} ms</span></div>
            <div class="record-field full"><span class="record-label">{h(tr("user_agent"))}</span><span class="record-value device-value">{h(item.get("user_agent", "")) or "—"}</span></div>
            <div class="record-field full"><span class="record-label">{h(tr("log_details"))}</span><pre class="record-value mono log-detail">{h(detail_text)}</pre></div>
          </div>
        </article>''')
    cards_html = "".join(cards) or f'<div class="empty">{h(tr("no_logs"))}</div>'
    content = Markup(f'''
      <section class="card form-card admin-page">
        <div class="hero-row"><div><h1>{h(tr('logs'))}</h1><p class="muted">{h(tr('logs_help'))}</p><div class="path-box"><strong>{h(tr('current_log_file'))}:</strong><br>{h(audit_log_path())}<br><br><strong>{h(tr('daily_log_files'))}:</strong><br>{h(audit_log_path().parent)}</div></div><a class="btn" href="{h(url_for('browse'))}">{h(tr('back'))}</a></div>
        <div class="admin-nav"><a class="btn" href="{h(url_for('users'))}">{h(tr('users'))}</a><a class="btn" href="{h(url_for('administrators'))}">{h(tr('administrators'))}</a></div>
        <form class="card filter-panel" method="get" action="{h(url_for('logs'))}">
          <input type="hidden" name="csrf" value="{h(csrf_token())}">
          <div class="filter-grid">
            <label class="date-control"><span>{h(tr('from_date'))}</span><input class="input" type="date" name="date_from" min="2004-08-14" max="{today.isoformat()}" value="{date_from.isoformat()}"></label>
            <label class="date-control"><span>{h(tr('to_date'))}</span><input class="input" type="date" name="date_to" min="2004-08-14" max="{today.isoformat()}" value="{date_to.isoformat()}"></label>
          </div>
          <p class="muted">{h(tr('log_export_help'))}</p>
          <div class="actions"><button class="btn" type="submit">{h(tr('apply_filters'))}</button><button class="btn primary" type="submit" formmethod="post" formaction="{h(url_for('download_logs'))}">{h(tr('download_logs_zip'))}</button></div>
        </form>
        <div class="record-grid logs-grid">{cards_html}</div>
      </section>
    ''')
    return render_page(tr("logs"), content)


@app.route("/logs/download", methods=["POST"])
def download_logs():
    require_role(admin=True)
    if not verify_csrf():
        abort(400)
    start, end = parse_date_range(f"{request.form.get('date_from', '')}|{request.form.get('date_to', '')}")
    audit_event("logs_exported", {"date_from": start.isoformat(), "date_to": end.isoformat()})
    archive = create_logs_export(start, end)
    if archive is None:
        flash(tr("no_logs_in_range"), "error")
        return redirect(url_for("logs", date_from=start.isoformat(), date_to=end.isoformat()))
    response = send_file(archive, as_attachment=True, download_name=archive.name, conditional=True)
    response.call_on_close(lambda: archive.unlink(missing_ok=True))
    return response


@app.route("/administrators")
def administrators():
    require_role(admin=True)
    _normalize_profile_admins(ACTIVE_PROFILE)
    accounts = list(ACTIVE_PROFILE.get("admins", []))
    current = current_admin()
    main_access = is_main_admin()
    visible_accounts = accounts if main_access else [item for item in accounts if str(item.get("username", "")).casefold() == current.casefold()]
    cards: List[str] = []
    for account in visible_accounts:
        username = str(account.get("username", ""))
        is_primary = username.casefold() == main_admin_username().casefold()
        current_badge = f'<span class="badge admin">{h(tr("current_admin"))}</span>' if username.casefold() == current.casefold() else ""
        account_badge = f'<span class="status-pill neutral">{h(tr("main_administrator") if is_primary else tr("admin_mode"))}</span>'
        delete_form = ""
        if main_access and len(accounts) > 1 and username.casefold() != current.casefold():
            delete_form = f'''
              <form method="post" action="{h(url_for('delete_administrator'))}" data-confirm="{h(tr('confirm_delete_admin'))}">
                <input type="hidden" name="csrf" value="{h(csrf_token())}"><input type="hidden" name="username" value="{h(username)}">
                <button class="btn danger" type="submit">{h(tr('delete_admin'))}</button>
              </form>
            '''
        card_class = "admin-card self-admin-card" if username.casefold() == current.casefold() else "admin-card"
        cards.append(f'''
          <article class="{card_class}">
            <div class="admin-card-head"><div><h2>{h(username)}</h2><p class="muted">{h(tr('created'))}: {h(format_iso_datetime(account.get('created_at', '')))}</p></div><div class="actions">{account_badge}{current_badge}</div></div>
            <form class="form-grid compact-form" method="post" action="{h(url_for('change_administrator_password'))}">
              <input type="hidden" name="csrf" value="{h(csrf_token())}"><input type="hidden" name="username" value="{h(username)}">
              <div class="field"><label>{h(tr('new_admin_password'))}</label><input class="input" name="password" type="password" minlength="8" autocomplete="new-password" required></div>
              <div class="field"><label>{h(tr('confirm_admin_password'))}</label><input class="input" name="confirmation" type="password" minlength="8" autocomplete="new-password" required></div>
              <div class="actions"><button class="btn" type="submit">{h(tr('change_admin_password'))}</button></div>
            </form>
            {delete_form}
          </article>
        ''')
    accounts_html = "".join(cards) if cards else f'<div class="empty">{h(tr("no_admins"))}</div>'
    help_text = tr("main_admin_manage_help") if main_access else tr("change_own_password_help")
    add_form = ""
    if main_access:
        add_form = f'''
        <form class="form-grid add-admin-form" method="post" action="{h(url_for('add_administrator'))}">
          <h2>{h(tr('add_admin'))}</h2><input type="hidden" name="csrf" value="{h(csrf_token())}">
          <div class="field"><label>{h(tr('admin_username'))}</label><input class="input" name="username" maxlength="64" autocomplete="username" required></div>
          <div class="field"><label>{h(tr('new_admin_password'))}</label><input class="input" name="password" type="password" minlength="8" autocomplete="new-password" required></div>
          <div class="field"><label>{h(tr('confirm_admin_password'))}</label><input class="input" name="confirmation" type="password" minlength="8" autocomplete="new-password" required></div>
          <div class="actions"><button class="btn primary" type="submit">{h(tr('add_admin'))}</button></div>
        </form>
        '''
    content = Markup(f'''
      <section class="card form-card admin-page">
        <div class="hero-row"><div><h1>{h(tr('administrators'))}</h1><p class="muted">{h(help_text)}</p></div><a class="btn" href="{h(url_for('browse'))}">{h(tr('back'))}</a></div>
        <div class="admin-nav"><a class="btn" href="{h(url_for('users'))}">{h(tr('users'))}</a><a class="btn" href="{h(url_for('logs'))}">{h(tr('logs'))}</a></div>
        {add_form}
        <div class="admin-list">{accounts_html}</div>
      </section>
    ''')
    return render_page(tr("administrators"), content)


@app.post("/administrators/add")
def add_administrator():
    require_main_admin()
    if not verify_csrf():
        abort(400)
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    confirmation = request.form.get("confirmation", "")
    _normalize_profile_admins(ACTIVE_PROFILE)
    if not valid_admin_username(username):
        flash(tr("invalid_username"), "error")
    elif any(str(item.get("username", "")).casefold() == username.casefold() for item in ACTIVE_PROFILE.get("admins", [])):
        flash(tr("admin_exists"), "error")
    elif len(password) < 8:
        flash(tr("admin_password_minimum"), "error")
    elif not hmac.compare_digest(password, confirmation):
        flash(tr("passwords_do_not_match"), "error")
    else:
        ACTIVE_PROFILE.setdefault("admins", []).append(make_admin_account(username, password))
        ACTIVE_PROFILE["updated_at"] = _utc_now()
        save_config(ACTIVE_CONFIG)
        audit_event("administrator_added", username)
        flash(tr("admin_added"), "")
    return redirect(url_for("administrators"))


@app.post("/administrators/password")
def change_administrator_password():
    require_role(admin=True)
    if not verify_csrf():
        abort(400)
    username = request.form.get("username", "").strip() or current_admin()
    if not is_main_admin() and username.casefold() != current_admin().casefold():
        abort(403, description=tr("main_admin_only"))
    password = request.form.get("password", "")
    confirmation = request.form.get("confirmation", "")
    if len(password) < 8:
        flash(tr("admin_password_minimum"), "error")
        return redirect(url_for("administrators"))
    if not hmac.compare_digest(password, confirmation):
        flash(tr("passwords_do_not_match"), "error")
        return redirect(url_for("administrators"))
    account = next((item for item in ACTIVE_PROFILE.get("admins", []) if str(item.get("username", "")).casefold() == username.casefold()), None)
    if account is None:
        flash(tr("action_failed"), "error")
    else:
        replacement = make_admin_account(str(account.get("username", username)), password)
        account.update(replacement)
        ACTIVE_PROFILE["updated_at"] = _utc_now()
        save_config(ACTIVE_CONFIG)
        audit_event("administrator_password_changed", username)
        flash(tr("admin_password_changed"), "")
    return redirect(url_for("administrators"))


@app.post("/administrators/delete")
def delete_administrator():
    require_main_admin()
    if not verify_csrf():
        abort(400)
    username = request.form.get("username", "").strip()
    accounts = ACTIVE_PROFILE.get("admins", [])
    if len(accounts) <= 1:
        flash(tr("cannot_delete_last_admin"), "error")
    elif username.casefold() == current_admin().casefold():
        flash(tr("cannot_delete_current_admin"), "error")
    else:
        remaining = [item for item in accounts if str(item.get("username", "")).casefold() != username.casefold()]
        if len(remaining) == len(accounts):
            flash(tr("action_failed"), "error")
        else:
            ACTIVE_PROFILE["admins"] = remaining
            ACTIVE_PROFILE["updated_at"] = _utc_now()
            save_config(ACTIVE_CONFIG)
            audit_event("administrator_deleted", username)
            flash(tr("admin_deleted"), "")
    return redirect(url_for("administrators"))


@app.route("/files")
def browse():
    require_role()
    requested_path = request.args.get("path", "")
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "all")
    if category not in VALID_CATEGORIES:
        category = "all"
    raw_size_filter = request.args.get("size", "")
    if "size_min" in request.args or "size_max" in request.args:
        size_min_mb = _clamp_int(request.args.get("size_min"), 0, SIZE_RANGE_MAX_MB, 0)
        size_max_mb = _clamp_int(request.args.get("size_max"), 0, SIZE_RANGE_MAX_MB, SIZE_RANGE_MAX_MB)
        if size_min_mb > size_max_mb:
            size_min_mb, size_max_mb = size_max_mb, size_min_mb
    else:
        size_min_mb, size_max_mb = parse_size_range(raw_size_filter)
    size_filter = f"{size_min_mb}:{size_max_mb}"

    raw_date_filter = request.args.get("date", "")
    if "date_from" in request.args or "date_to" in request.args:
        raw_date_filter = f"{request.args.get('date_from', '')}|{request.args.get('date_to', '')}"
    date_from, date_to = parse_date_range(raw_date_filter)
    date_from_value, date_to_value = date_from.isoformat(), date_to.isoformat()
    date_filter = f"{date_from_value}|{date_to_value}"
    today_value = dt.datetime.now().astimezone().date().isoformat()
    sort_by = request.args.get("sort", "name")
    order = request.args.get("order", "asc")
    if sort_by not in {"name", "size", "date", "type"}:
        sort_by = "name"
    if order not in {"asc", "desc"}:
        order = "asc"
    try:
        current = safe_path(requested_path)
        if not current.is_dir():
            raise ValueError
    except (ValueError, OSError):
        abort(400)
    entries = iter_entries(current, query, category, size_filter, date_filter, sort_by, order)
    current_rel = relative_path(current)
    search_url = url_for("browse")
    toolbar_actions = ""
    if is_admin():
        toolbar_actions = (
            f'<a class="btn primary" href="{h(url_for("upload_page", path=current_rel))}"><span aria-hidden="true">↑</span>{h(tr("upload"))}</a>'
            f'<a class="btn" href="{h(url_for("new_folder", path=current_rel))}"><span aria-hidden="true">＋</span>{h(tr("new_folder"))}</a>'
        )
    description = ACTIVE_PROFILE.get("description", "")
    hero = f"""
      <section class="card hero">
        <div class="hero-row"><div><h1>{h(ACTIVE_PROFILE['name'])}</h1><p class="muted hero-subtitle">{h(description or tr('browse_files'))}</p></div><div class="actions">{toolbar_actions}<a class="btn ghost" href="{h(url_for('browse', path=current_rel, category=category, q=query, size=size_filter, date=date_filter, sort=sort_by, order=order))}">↻ {h(tr('refresh'))}</a></div></div>
      </section>
    """
    rows: List[str] = []
    for item in entries:
        rel = item["rel"]
        name = item["name"]
        open_button = ""
        if item["is_dir"]:
            open_button = f'<a class="btn small primary" href="{h(url_for("browse", path=rel, category="all", size=size_filter, date=date_filter, sort=sort_by, order=order))}">{h(tr("open"))}</a>'
        actions = (
            open_button
            + f'<a class="btn small" href="{h(url_for("download_entry", entry=rel))}">{h(tr("download"))}</a>'
            + f'<a class="btn small" href="{h(url_for("details", entry=rel))}">{h(tr("details"))}</a>'
        )
        check_cell = '<div class="cell-check"></div>'
        if is_admin():
            check_cell = f'<div class="cell-check"><input class="check entry-check" type="checkbox" value="{h(rel)}" aria-label="{h(tr("select_all"))}: {h(name)}"></div>'
            actions += (
                f'<a class="btn small" href="{h(url_for("move_entry", entry=rel))}">{h(tr("move"))}</a>'
                f'<a class="btn small" href="{h(url_for("rename_entry", entry=rel))}">{h(tr("rename"))}</a>'
                f'<form method="post" action="{h(url_for("delete_entry"))}" data-confirm="{h(tr("confirm_delete_web"))}"><input type="hidden" name="csrf" value="{h(csrf_token())}"><input type="hidden" name="entry" value="{h(rel)}"><input type="hidden" name="return_path" value="{h(current_rel)}"><button class="btn small danger" type="submit">{h(tr("delete"))}</button></form>'
            )
        path_hint = f'<span class="entry-path">{h(rel)}</span>' if query else ""
        rows.append(
            f"""
            <article class="entry-row">
              {check_cell}
              <div class="cell-name"><div class="entry-name"><span class="entry-icon" aria-hidden="true">{h(icon_for(item['category'], item['is_dir']))}</span><span class="entry-text"><span class="entry-title">{h(name)}</span>{path_hint}</span></div></div>
              <div class="cell-category" data-label="{h(tr('type'))}">{h(tr(item['category']))}</div>
              <div class="cell-size col-size" data-label="{h(tr('size'))}">{h(item['size_text'])}</div>
              <div class="cell-modified" data-label="{h(tr('modified'))}">{h(item['modified_text'])}</div>
              <div class="cell-actions"><div class="row-actions">{actions}</div></div>
            </article>
            """
        )
    entries_html = "".join(rows) if rows else f'<div class="empty">{h(tr("empty"))}</div>'
    clear_search = f'<a class="btn small" href="{h(url_for("browse", path=current_rel, category=category, size=size_filter, date=date_filter, sort=sort_by, order=order))}">{h(tr("clear_search"))}</a>' if query else ""
    bulk_html = ""
    select_header = "<div></div>"
    if is_admin():
        select_header = f'<div><input id="selectAll" class="check" type="checkbox" aria-label="{h(tr("select_all"))}"></div>'
        bulk_html = f"""
          <div id="bulkBar" class="bulkbar"><strong><span id="selectedNumber">0</span> {h(tr('selected_count'))}</strong><form id="bulkForm" method="post" action="{h(url_for('bulk_delete'))}" data-confirm="{h(tr('confirm_bulk'))}"><input type="hidden" name="csrf" value="{h(csrf_token())}"><input type="hidden" name="return_path" value="{h(current_rel)}"><button class="btn danger" type="submit">{h(tr('selected_delete'))}</button></form></div>
        """
    browser = f"""
      <div class="layout">
        <div>{category_sidebar(current_rel, category, query, size_filter, date_filter, sort_by, order)}</div>
        <section class="main">
          <div class="card browser-card">
            <div class="browser-tools">
              <form class="search-form" method="get" action="{h(search_url)}">
                <input type="hidden" name="path" value="{h(current_rel)}">
                <input type="hidden" name="category" value="{h(category)}">
                <div class="filter-field search-main"><label for="fileSearch">{h(tr('search'))}</label><input id="fileSearch" class="input" name="q" value="{h(query)}" placeholder="{h(tr('search_placeholder'))}"></div>
                <div class="filter-field range-filter">
                  <label>{h(tr('size_filter'))}</label>
                  <div class="range-values"><span>{h(tr('minimum_size'))}: <strong id="sizeMinValue">{size_min_mb}</strong> {h(tr('megabytes'))}</span><span>{h(tr('maximum_size'))}: <strong id="sizeMaxValue">{str(size_max_mb) + ('+' if size_max_mb >= SIZE_RANGE_MAX_MB else '')}</strong> {h(tr('megabytes'))}</span></div>
                  <div id="sizeRange" class="dual-range">
                    <div class="range-track"></div><div class="range-fill"></div>
                    <input id="sizeMinimum" class="range-input" type="range" name="size_min" min="0" max="{SIZE_RANGE_MAX_MB}" step="1" value="{size_min_mb}" aria-label="{h(tr('minimum_size'))}">
                    <input id="sizeMaximum" class="range-input" type="range" name="size_max" min="0" max="{SIZE_RANGE_MAX_MB}" step="1" value="{size_max_mb}" aria-label="{h(tr('maximum_size'))}">
                  </div>
                </div>
                <div class="filter-field date-range-filter">
                  <label>{h(tr('date_filter'))}</label>
                  <div class="date-range-grid">
                    <label class="date-control"><span>{h(tr('from_date'))}</span><input class="input" type="date" name="date_from" min="2004-08-14" max="{today_value}" value="{date_from_value}"></label>
                    <label class="date-control"><span>{h(tr('to_date'))}</span><input class="input" type="date" name="date_to" min="2004-08-14" max="{today_value}" value="{date_to_value}"></label>
                  </div>
                  <p class="filter-help">{h(tr('date_range_help'))}</p>
                </div>
                <div class="filter-field"><label for="sortFilter">{h(tr('sort_by'))}</label><select id="sortFilter" class="select" name="sort"><option value="name"{' selected' if sort_by == 'name' else ''}>{h(tr('sort_name'))}</option><option value="size"{' selected' if sort_by == 'size' else ''}>{h(tr('sort_size'))}</option><option value="date"{' selected' if sort_by == 'date' else ''}>{h(tr('sort_date'))}</option><option value="type"{' selected' if sort_by == 'type' else ''}>{h(tr('sort_type'))}</option></select></div>
                <div class="filter-field"><label for="orderFilter">{h(tr('sort_order'))}</label><select id="orderFilter" class="select" name="order"><option value="asc"{' selected' if order == 'asc' else ''}>{h(tr('ascending'))}</option><option value="desc"{' selected' if order == 'desc' else ''}>{h(tr('descending'))}</option></select></div>
                <div class="filter-actions"><button class="btn primary" type="submit">{h(tr('apply_filters'))}</button><a class="btn" href="{h(url_for('browse', path=current_rel))}">{h(tr('reset_filters'))}</a>{clear_search}</div>
              </form>
            </div>
            {breadcrumbs(current_rel, category, query, size_filter, date_filter, sort_by, order)}
            {bulk_html}
            <div class="entries-head">{select_header}<div>{h(tr('name'))}</div><div>{h(tr('type'))}</div><div class="col-size">{h(tr('size'))}</div><div>{h(tr('modified'))}</div><div>{h(tr('actions'))}</div></div>
            <div class="entries-body">{entries_html}</div>
          </div>
        </section>
      </div>
    """
    extra_script = ""
    if is_admin():
        extra_script = f"""
        (function(){{
          const boxes=[...document.querySelectorAll('.entry-check')], all=document.getElementById('selectAll'), bar=document.getElementById('bulkBar'), number=document.getElementById('selectedNumber'), form=document.getElementById('bulkForm');
          function sync(){{const selected=boxes.filter(b=>b.checked);number.textContent=selected.length;bar.classList.toggle('visible',selected.length>0);if(all){{all.checked=selected.length===boxes.length&&boxes.length>0;all.indeterminate=selected.length>0&&selected.length<boxes.length;}}}}
          boxes.forEach(b=>b.addEventListener('change',sync));if(all)all.addEventListener('change',()=>{{boxes.forEach(b=>b.checked=all.checked);sync();}});
          if(form)form.addEventListener('submit',function(event){{form.querySelectorAll('input[name="entry"]').forEach(x=>x.remove());const selected=boxes.filter(b=>b.checked);if(!selected.length){{event.preventDefault();alert({json.dumps(tr('nothing_selected'))});return;}}selected.forEach(b=>{{const i=document.createElement('input');i.type='hidden';i.name='entry';i.value=b.value;form.appendChild(i);}});}});
        }})();
        """
    return render_page(tr("files"), Markup(hero + browser), extra_script=extra_script)


@app.route("/new-folder", methods=["GET", "POST"])
def new_folder():
    require_role(admin=True)
    path_value = request.values.get("path", "")
    try:
        directory = safe_path(path_value)
        if not directory.is_dir():
            raise ValueError
    except (ValueError, OSError):
        abort(400)
    current_rel = relative_path(directory)
    if request.method == "POST":
        if not verify_csrf():
            abort(400)
        try:
            name = validate_entry_name(request.form.get("name", ""))
            destination = safe_path((Path(current_rel) / name).as_posix(), must_exist=False)
            if destination.exists():
                flash(tr("already_exists"), "error")
            else:
                destination.mkdir(parents=False)
                audit_event("folder_created", relative_path(destination))
                flash(tr("folder_done"), "")
                return redirect(url_for("browse", path=current_rel))
        except (ValueError, OSError):
            flash(tr("action_failed"), "error")
    content = Markup(
        f"""
        <section class="card form-card">
          <h1>{h(tr('new_folder'))}</h1><p class="muted">{h(tr('current_folder'))}: /{h(current_rel)}</p>
          <form class="form-grid" method="post" action="{h(url_for('new_folder'))}" data-confirm="{h(tr('confirm_folder'))}">
            <input type="hidden" name="csrf" value="{h(csrf_token())}"><input type="hidden" name="path" value="{h(current_rel)}">
            <div class="field"><label for="folder-name">{h(tr('folder_name'))}</label><input class="input" id="folder-name" name="name" required autofocus></div>
            <div class="actions stretch"><button class="btn primary" type="submit">{h(tr('create'))}</button><a class="btn" href="{h(url_for('browse', path=current_rel))}">{h(tr('back'))}</a></div>
          </form>
        </section>
        """
    )
    return render_page(tr("new_folder"), content)


@app.route("/upload")
def upload_page():
    require_role(admin=True)
    path_value = request.args.get("path", "")
    try:
        directory = safe_path(path_value)
        if not directory.is_dir():
            raise ValueError
    except (ValueError, OSError):
        abort(400)
    current_rel = relative_path(directory)
    content = Markup(
        f"""
        <section class="card form-card">
          <h1>{h(tr('upload'))}</h1><p class="muted">{h(tr('upload_hint'))}</p><p class="muted">{h(tr('current_folder'))}: /{h(current_rel)}</p>
          <div class="field"><label for="filePicker">{h(tr('choose_files'))}</label><input class="input" id="filePicker" type="file" multiple></div>
          <div class="actions stretch"><button class="btn primary" id="uploadButton" type="button">{h(tr('upload'))}</button><a class="btn" href="{h(url_for('browse', path=current_rel))}">{h(tr('back'))}</a></div>
          <div id="uploadStatus" class="muted" style="margin-top:14px" aria-live="polite"></div>
          <div class="progress-shell"><div id="uploadBar" class="progress-bar"></div></div>
          <div id="uploadList" class="upload-list"></div>
        </section>
        """
    )
    script = f"""
      (function(){{
        const picker=document.getElementById('filePicker'),button=document.getElementById('uploadButton'),bar=document.getElementById('uploadBar'),status=document.getElementById('uploadStatus'),list=document.getElementById('uploadList');
        const endpoint={json.dumps(url_for('upload_file'))},csrf={json.dumps(csrf_token())},path={json.dumps(current_rel)},returnUrl={json.dumps(url_for('browse', path=current_rel))};
        const maxBytes={MAX_UPLOAD_BYTES},chunkBytes={UPLOAD_CHUNK_BYTES},tooLarge={json.dumps(tr('too_large'))},uploadFailed={json.dumps(tr('upload_failed'))};
        function uploadId(){{
          if(window.crypto&&typeof window.crypto.randomUUID==='function')return window.crypto.randomUUID().replace(/-/g,'');
          return Date.now().toString(36)+Math.random().toString(36).slice(2)+Math.random().toString(36).slice(2);
        }}
        async function sendFile(file,fileIndex,fileCount,row){{
          if(file.size>maxBytes)throw new Error(file.name+': '+tooLarge);
          const id=uploadId(),totalChunks=Math.max(1,Math.ceil(file.size/chunkBytes));
          for(let index=0;index<totalChunks;index++){{
            await new Promise((resolve,reject)=>{{
              const start=index*chunkBytes,end=Math.min(file.size,start+chunkBytes),blob=file.slice(start,end),xhr=new XMLHttpRequest(),data=new FormData();
              data.append('csrf',csrf);data.append('path',path);data.append('upload_id',id);data.append('file_name',file.name);data.append('chunk_index',String(index));data.append('total_chunks',String(totalChunks));data.append('total_size',String(file.size));data.append('file',blob,file.name+'.part');
              xhr.open('POST',endpoint);
              xhr.upload.onprogress=e=>{{if(e.lengthComputable){{const fileProgress=(index+(e.loaded/e.total))/totalChunks;const overall=((fileIndex+fileProgress)/fileCount)*100;bar.style.width=overall.toFixed(1)+'%';row.children[1].textContent=Math.floor(fileProgress*100)+'%';}}}};
              xhr.onload=()=>{{if(xhr.status>=200&&xhr.status<300)resolve();else reject(xhr.responseText||uploadFailed);}};xhr.onerror=()=>reject(uploadFailed);xhr.send(data);
            }});
          }}
        }}
        button.addEventListener('click',async()=>{{const files=[...picker.files];if(!files.length)return;if(!confirm({json.dumps(tr('confirm_upload'))}))return;button.disabled=true;list.innerHTML='';
          try{{for(let i=0;i<files.length;i++){{const file=files[i];status.textContent={json.dumps(tr('upload_progress'))}+' '+(i+1)+'/'+files.length+': '+file.name;const row=document.createElement('div');row.className='upload-item';row.innerHTML='<span></span><strong>0%</strong>';row.children[0].textContent=file.name;list.appendChild(row);await sendFile(file,i,files.length,row);row.children[1].textContent='100%';}}window.location.href=returnUrl;}}
          catch(error){{alert(String(error));button.disabled=false;}}
        }});
      }})();
    """
    return render_page(tr("upload"), content, extra_script=script)


@app.post("/api/upload")
def upload_file():
    require_role(admin=True)
    if not verify_csrf():
        abort(400)
    cleanup_stale_uploads()
    uploaded = request.files.get("file")
    if uploaded is None:
        abort(400)
    upload_id = str(request.form.get("upload_id", "")).strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{12,96}", upload_id):
        abort(400)
    try:
        chunk_index = int(request.form.get("chunk_index", "-1"))
        total_chunks = int(request.form.get("total_chunks", "0"))
        total_size = int(request.form.get("total_size", "-1"))
    except (TypeError, ValueError):
        abort(400)
    if total_size < 0 or total_size > MAX_UPLOAD_BYTES:
        audit_event("upload_rejected", request.form.get("file_name", ""), success=False)
        return tr("too_large"), 413
    expected_chunks = max(1, (total_size + UPLOAD_CHUNK_BYTES - 1) // UPLOAD_CHUNK_BYTES)
    if total_chunks != expected_chunks or chunk_index < 0 or chunk_index >= total_chunks:
        abort(400)

    work = upload_work_dir()
    state_path = work / f"{upload_id}.json"
    part_path = work / f"{upload_id}.part"
    try:
        directory = safe_path(request.form.get("path", ""))
        if not directory.is_dir():
            raise ValueError
        file_name = validate_entry_name(Path(request.form.get("file_name", "")).name)
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
        else:
            if chunk_index != 0:
                return tr("upload_failed"), 409
            destination = unique_destination(directory, file_name)
            if not disk_allows_upload(directory, total_size, 0):
                audit_event("upload_rejected", f"{file_name}: storage threshold", success=False)
                return tr("storage_too_full"), 507
            state = {
                "destination": relative_path(destination),
                "file_name": file_name,
                "total_size": total_size,
                "total_chunks": total_chunks,
                "next_index": 0,
                "owner": current_admin(),
                "created_at": _utc_now(),
            }
            _atomic_json_write(state_path, state)

        if state.get("owner") != current_admin() or int(state.get("total_size", -1)) != total_size or int(state.get("total_chunks", 0)) != total_chunks or int(state.get("next_index", -1)) != chunk_index:
            return tr("upload_failed"), 409
        already_written = part_path.stat().st_size if part_path.exists() else 0
        if not disk_allows_upload(directory, total_size, already_written):
            part_path.unlink(missing_ok=True)
            state_path.unlink(missing_ok=True)
            audit_event("upload_rejected", f"{file_name}: storage threshold", success=False)
            return tr("storage_too_full"), 507

        with part_path.open("ab") as output:
            while True:
                data = uploaded.stream.read(1024 * 1024)
                if not data:
                    break
                output.write(data)
        written = part_path.stat().st_size
        if written > total_size or written > MAX_UPLOAD_BYTES:
            part_path.unlink(missing_ok=True)
            state_path.unlink(missing_ok=True)
            audit_event("upload_rejected", file_name, success=False)
            return tr("too_large"), 413

        state["next_index"] = chunk_index + 1
        _atomic_json_write(state_path, state)
        complete = state["next_index"] == total_chunks
        if complete:
            if written != total_size:
                part_path.unlink(missing_ok=True)
                state_path.unlink(missing_ok=True)
                return tr("upload_failed"), 400
            destination = safe_path(str(state["destination"]), must_exist=False)
            os.replace(part_path, destination)
            state_path.unlink(missing_ok=True)
            audit_event("file_uploaded", f"{relative_path(destination)} ({written} bytes)")
            return jsonify(ok=True, complete=True, name=destination.name)
        return jsonify(ok=True, complete=False, next_index=state["next_index"])
    except (ValueError, OSError, json.JSONDecodeError, KeyError):
        return tr("action_failed"), 400



@app.route("/move", methods=["GET", "POST"])
def move_entry():
    require_role(admin=True)
    entry = request.values.get("entry", "")
    try:
        source = safe_path(entry)
        if source == ACTIVE_ROOT:
            raise ValueError
    except (ValueError, OSError):
        abort(400)
    parent_rel = relative_path(source.parent)
    if request.method == "POST":
        if not verify_csrf():
            abort(400)
        try:
            destination_rel = request.form.get("destination", "").strip().strip("/")
            destination_dir = safe_path(destination_rel)
            if not destination_dir.is_dir():
                raise ValueError
            destination = safe_path((Path(destination_rel) / source.name).as_posix(), must_exist=False)
            if destination.exists():
                flash(tr("already_exists"), "error")
            elif source.is_dir() and _path_is_within(destination, source):
                flash(tr("invalid_path"), "error")
            else:
                old_rel = relative_path(source)
                shutil.move(str(source), str(destination))
                new_rel = relative_path(destination)
                move_comment_tree(old_rel, new_rel)
                audit_event("entry_moved", f"{old_rel} -> {new_rel}")
                flash(tr("move_done"), "")
                return redirect(url_for("browse", path=destination_rel))
        except (ValueError, OSError):
            flash(tr("action_failed"), "error")
    folder_paths = [""]
    for candidate in ACTIVE_ROOT.rglob("*"):
        try:
            if not candidate.is_dir():
                continue
            candidate_parts = candidate.relative_to(ACTIVE_ROOT).parts
            if candidate_parts and candidate_parts[0] == INTERNAL_DIR_NAME:
                continue
            if source.is_dir() and _path_is_within(candidate, source):
                continue
            folder_paths.append(relative_path(candidate))
        except (OSError, ValueError):
            continue
    folder_paths = sorted(set(folder_paths), key=lambda value: (value.count("/"), value.casefold()))
    folder_options = "".join(
        f'<option value="{h(value)}"{" selected" if value == parent_rel else ""}>{h("/" + value if value else tr("root"))}</option>'
        for value in folder_paths
    )
    content = Markup(
        f'''
        <section class="card form-card">
          <h1>{h(tr('move'))}</h1><p class="muted">{h(tr('entry'))}: /{h(entry)}</p>
          <form class="form-grid" method="post" action="{h(url_for('move_entry'))}" data-confirm="{h(tr('confirm_move'))}">
            <input type="hidden" name="csrf" value="{h(csrf_token())}"><input type="hidden" name="entry" value="{h(entry)}">
            <div class="field"><label for="destination">{h(tr('destination_folder'))}</label><select class="select" id="destination" name="destination">{folder_options}</select></div>
            <div class="actions stretch"><button class="btn primary" type="submit">{h(tr('move'))}</button><a class="btn" href="{h(url_for('browse', path=parent_rel))}">{h(tr('back'))}</a></div>
          </form>
        </section>
        '''
    )
    return render_page(tr("move"), content)


@app.route("/rename", methods=["GET", "POST"])
def rename_entry():
    require_role(admin=True)
    entry = request.values.get("entry", "")
    try:
        source = safe_path(entry)
        if source == ACTIVE_ROOT:
            raise ValueError
    except (ValueError, OSError):
        abort(400)
    parent_rel = relative_path(source.parent)
    if request.method == "POST":
        if not verify_csrf():
            abort(400)
        try:
            new_name = validate_entry_name(request.form.get("new_name", ""))
            destination = safe_path((Path(parent_rel) / new_name).as_posix(), must_exist=False)
            if destination.exists():
                flash(tr("already_exists"), "error")
            else:
                old_rel = relative_path(source)
                source.rename(destination)
                new_rel = relative_path(destination)
                move_comment_tree(old_rel, new_rel)
                audit_event("entry_renamed", f"{old_rel} -> {new_rel}")
                flash(tr("rename_done"), "")
                return redirect(url_for("browse", path=parent_rel))
        except (ValueError, OSError):
            flash(tr("action_failed"), "error")
    content = Markup(
        f'''
        <section class="card form-card">
          <h1>{h(tr('rename'))}</h1><p class="muted">{h(tr('entry'))}: /{h(entry)}</p>
          <form class="form-grid" method="post" action="{h(url_for('rename_entry'))}" data-confirm="{h(tr('confirm_rename'))}">
            <input type="hidden" name="csrf" value="{h(csrf_token())}"><input type="hidden" name="entry" value="{h(entry)}">
            <div class="field"><label for="new-name">{h(tr('new_name'))}</label><input class="input" id="new-name" name="new_name" value="{h(source.name)}" required></div>
            <div class="actions stretch"><button class="btn primary" type="submit">{h(tr('rename'))}</button><a class="btn" href="{h(url_for('browse', path=parent_rel))}">{h(tr('back'))}</a></div>
          </form>
        </section>
        '''
    )
    return render_page(tr("rename"), content)


@app.post("/delete")
def delete_entry():
    require_role(admin=True)
    if not verify_csrf():
        abort(400)
    return_path = request.form.get("return_path", "")
    try:
        target = safe_path(request.form.get("entry", ""))
        if target == ACTIVE_ROOT:
            raise ValueError
        target_rel = relative_path(target)
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        delete_comment_tree(target_rel)
        audit_event("entry_deleted", target_rel)
        flash(tr("delete_done"), "")
    except (ValueError, OSError):
        flash(tr("action_failed"), "error")
    return redirect(url_for("browse", path=return_path))


@app.post("/bulk-delete")
def bulk_delete():
    require_role(admin=True)
    if not verify_csrf():
        abort(400)
    return_path = request.form.get("return_path", "")
    deleted = 0
    for entry in request.form.getlist("entry"):
        try:
            target = safe_path(entry)
            if target == ACTIVE_ROOT:
                continue
            target_rel = relative_path(target)
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            delete_comment_tree(target_rel)
            deleted += 1
        except (ValueError, OSError):
            continue
    audit_event("bulk_delete", f"Deleted {deleted} entries", success=bool(deleted))
    flash(tr("bulk_done") if deleted else tr("action_failed"), "" if deleted else "error")
    return redirect(url_for("browse", path=return_path))



@app.route("/details")
def details():
    require_role()
    entry = request.args.get("entry", "")
    try:
        target = safe_path(entry)
        stat = target.stat()
    except (ValueError, OSError):
        abort(404)
    is_directory = target.is_dir()
    size = folder_size(target) if is_directory else stat.st_size
    mime = "inode/directory" if is_directory else (mimetypes.guess_type(target.name)[0] or "application/octet-stream")
    checksum = ""
    if request.args.get("checksum") == "1" and target.is_file():
        checksum = sha256_file(target)
    parent_rel = relative_path(target.parent)
    rows = [
        (tr("location"), "/" + relative_path(target)),
        (tr("type"), tr("folder_label") if is_directory else tr("file_label")),
        (tr("category"), tr(entry_category(target))),
        (tr("size"), human_size(size)),
        (tr("mime"), mime),
        (tr("modified"), format_time(stat.st_mtime)),
        (tr("created"), format_time(getattr(stat, "st_birthtime", stat.st_ctime))),
    ]
    if checksum:
        rows.append((tr("checksum"), checksum))
    detail_html = "".join(f'<div class="detail-key">{h(key)}</div><div class="detail-value">{h(value)}</div>' for key, value in rows)
    checksum_button = ""
    if target.is_file() and not checksum:
        checksum_button = f'<a class="btn" href="{h(url_for("details", entry=entry, checksum=1))}">{h(tr("calculate"))} {h(tr("checksum"))}</a>'
    admin_buttons = ""
    if is_admin():
        admin_buttons = (
            f'<a class="btn" href="{h(url_for("move_entry", entry=entry))}">{h(tr("move"))}</a>'
            f'<a class="btn" href="{h(url_for("rename_entry", entry=entry))}">{h(tr("rename"))}</a>'
        )

    comments_section = ""
    if target.is_file():
        comments = load_comments().get(entry.strip("/"), [])
        comment_cards: List[str] = []
        for item in comments:
            delete_button = ""
            if is_admin():
                delete_button = f'''
                  <form method="post" action="{h(url_for('delete_comment'))}" data-confirm="{h(tr('confirm_delete_comment'))}">
                    <input type="hidden" name="csrf" value="{h(csrf_token())}"><input type="hidden" name="entry" value="{h(entry)}"><input type="hidden" name="comment_id" value="{h(item.get('id', ''))}">
                    <button class="btn small danger" type="submit">{h(tr('delete'))}</button>
                  </form>
                '''
            comment_cards.append(f'''
              <article class="comment-card"><div class="comment-head"><strong>{h(tr('written_by'))} {h(item.get('author', 'admin'))}</strong><span class="muted">{h(item.get('created_at', ''))}</span></div><p>{h(item.get('text', ''))}</p>{delete_button}</article>
            ''')
        comments_html = "".join(comment_cards) if comment_cards else f'<div class="empty comments-empty">{h(tr("no_comments"))}</div>'
        add_form = ""
        if is_admin():
            add_form = f'''
              <form class="form-grid comment-form" method="post" action="{h(url_for('add_comment'))}">
                <input type="hidden" name="csrf" value="{h(csrf_token())}"><input type="hidden" name="entry" value="{h(entry)}">
                <div class="field"><label for="comment-text">{h(tr('add_comment'))}</label><textarea class="textarea" id="comment-text" name="text" maxlength="2000" placeholder="{h(tr('comment_placeholder'))}" required></textarea></div>
                <div class="actions"><button class="btn primary" type="submit">{h(tr('add_comment'))}</button></div>
              </form>
            '''
        comments_section = f'''<section class="comments-section"><h2>{h(tr('comments'))}</h2><div class="comments-list">{comments_html}</div>{add_form}</section>'''

    content = Markup(
        f'''
        <section class="card form-card">
          <div class="hero-row"><div><h1>{h(target.name)}</h1><p class="muted">/{h(relative_path(target))}</p></div><span class="entry-icon" aria-hidden="true">{h(icon_for(entry_category(target), is_directory))}</span></div>
          <div class="details-grid">{detail_html}</div>
          <div class="actions" style="margin-top:16px"><a class="btn primary" href="{h(url_for('download_entry', entry=entry))}">{h(tr('download'))}</a>{checksum_button}{admin_buttons}<a class="btn" href="{h(url_for('browse', path=parent_rel))}">{h(tr('back'))}</a></div>
          {comments_section}
        </section>
        '''
    )
    return render_page(tr("details"), content)


@app.post("/comments/add")
def add_comment():
    require_role(admin=True)
    if not verify_csrf():
        abort(400)
    entry = request.form.get("entry", "").strip().strip("/")
    text = request.form.get("text", "").strip()
    try:
        target = safe_path(entry)
        if not target.is_file():
            raise ValueError
    except (ValueError, OSError):
        abort(400)
    if not text:
        flash(tr("action_failed"), "error")
    elif len(text) > 2000:
        flash(tr("comment_too_long"), "error")
    else:
        comments = load_comments()
        comments.setdefault(entry, []).append({
            "id": secrets.token_urlsafe(10),
            "author": current_admin(),
            "text": text,
            "created_at": _utc_now(),
        })
        save_comments(comments)
        audit_event("comment_added", entry)
        flash(tr("comment_added"), "")
    return redirect(url_for("details", entry=entry))


@app.post("/comments/delete")
def delete_comment():
    require_role(admin=True)
    if not verify_csrf():
        abort(400)
    entry = request.form.get("entry", "").strip().strip("/")
    comment_id = request.form.get("comment_id", "")
    try:
        target = safe_path(entry)
        if not target.is_file():
            raise ValueError
    except (ValueError, OSError):
        abort(400)
    comments = load_comments()
    old = comments.get(entry, [])
    new = [item for item in old if str(item.get("id", "")) != comment_id]
    if len(new) == len(old):
        flash(tr("action_failed"), "error")
    else:
        if new:
            comments[entry] = new
        else:
            comments.pop(entry, None)
        save_comments(comments)
        audit_event("comment_deleted", entry)
        flash(tr("comment_deleted"), "")
    return redirect(url_for("details", entry=entry))


@app.route("/download")
def download_entry():
    require_role()
    entry = request.args.get("entry", "")
    try:
        target = safe_path(entry)
        if target == ACTIVE_ROOT:
            raise ValueError
    except (ValueError, OSError):
        abort(404)
    if target.is_file():
        stat = target.stat()
        audit_event("file_downloaded", {
            "entry": entry,
            "relative_path": relative_path(target),
            "file_name": target.name,
            "size_bytes": stat.st_size,
            "size_human": human_size(stat.st_size),
            "modified": dt.datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(),
            "mime_type": mimetypes.guess_type(target.name)[0] or "application/octet-stream",
            "range_request": request.headers.get("Range", ""),
            "download_type": "file",
        })
        return send_file(target, as_attachment=True, download_name=target.name, conditional=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="dedsec-download-", dir=RUNTIME_BASE))
    archive = temp_dir / f"{target.name}.zip"
    try:
        file_count = 0
        total_bytes = 0
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zip_handle:
            for path in target.rglob("*"):
                if path.is_file():
                    relative_parts = path.relative_to(ACTIVE_ROOT).parts
                    if relative_parts and relative_parts[0] == INTERNAL_DIR_NAME:
                        continue
                    stat = path.stat()
                    file_count += 1
                    total_bytes += stat.st_size
                    zip_handle.write(path, arcname=(Path(target.name) / path.relative_to(target)).as_posix())
        archive_size = archive.stat().st_size
        audit_event("folder_downloaded", {
            "entry": entry,
            "relative_path": relative_path(target),
            "folder_name": target.name,
            "file_count": file_count,
            "source_size_bytes": total_bytes,
            "source_size_human": human_size(total_bytes),
            "archive_size_bytes": archive_size,
            "archive_size_human": human_size(archive_size),
            "download_type": "folder_zip",
        })
        response = send_file(archive, as_attachment=True, download_name=archive.name, conditional=True)
        response.call_on_close(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        return response
    except Exception as exc:
        audit_event("folder_downloaded", {"entry": entry, "error": str(exc)}, success=False)
        shutil.rmtree(temp_dir, ignore_errors=True)
        abort(500)


@app.errorhandler(400)
def bad_request(_error):
    return _error_page(400, tr("security_check_failed"))


@app.errorhandler(401)
def unauthorized(_error):
    return redirect(url_for("access"))


@app.errorhandler(403)
def forbidden(_error):
    return _error_page(403, tr("permission_denied"))


@app.errorhandler(404)
def not_found(_error):
    return _error_page(404, tr("not_found"))


@app.errorhandler(413)
def too_large(_error):
    return _error_page(413, tr("too_large"))


@app.errorhandler(500)
def internal_error(_error):
    return _error_page(500, tr("action_failed"))


def _error_page(status: int, message: str):
    content = Markup(
        f'<section class="card form-card"><h1>{status}</h1><div class="notice error">{h(message)}</div><div class="actions"><a class="btn primary" href="{h(url_for("browse") if role() else url_for("access"))}">{h(tr("back"))}</a></div></section>'
    )
    return render_page(str(status), content), status

# ---------------------------------------------------------------------------
# Cloudflare / Tor / server runtime
# ---------------------------------------------------------------------------


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def is_termux() -> bool:
    prefix = os.environ.get("PREFIX", "")
    return "com.termux" in prefix or Path("/data/data/com.termux/files/usr/bin/pkg").exists()


def run_command(command: List[str], *, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=check, text=True)


def install_cloudflared_linux() -> bool:
    machine = os.uname().machine.lower()
    architecture = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64", "armv7l": "arm"}.get(machine)
    if not architecture:
        return False
    url = f"https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-{architecture}"
    target_dir = Path.home() / ".local" / "bin"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "cloudflared"
    try:
        print(f"Downloading cloudflared for {architecture}…")
        urllib.request.urlretrieve(url, target)
        target.chmod(0o755)
        os.environ["PATH"] = str(target_dir) + os.pathsep + os.environ.get("PATH", "")
        return command_exists("cloudflared")
    except Exception as exc:
        print(f"Cloudflared installation failed: {exc}")
        return False


def install_dependencies(lang: str) -> None:
    print(tr("installing", lang))
    if is_termux() and command_exists("pkg"):
        run_command(["pkg", "update", "-y"])
        run_command(["pkg", "install", "-y", "python", "cloudflared", "tor"])
    elif command_exists("apt-get"):
        prefix = [] if os.geteuid() == 0 else (["sudo"] if command_exists("sudo") else [])
        if prefix or os.geteuid() == 0:
            run_command(prefix + ["apt-get", "update"])
            run_command(prefix + ["apt-get", "install", "-y", "python3", "python3-pip", "tor"])
        if not command_exists("cloudflared"):
            install_cloudflared_linux()
    elif command_exists("dnf"):
        prefix = [] if os.geteuid() == 0 else (["sudo"] if command_exists("sudo") else [])
        if prefix or os.geteuid() == 0:
            run_command(prefix + ["dnf", "install", "-y", "python3", "python3-pip", "tor"])
        if not command_exists("cloudflared"):
            install_cloudflared_linux()
    else:
        print("Install Python 3, Flask, cloudflared, and Tor manually.")
    _ensure_flask()
    print(tr("install_complete", lang))


def ensure_link_dependencies(lang: str) -> None:
    missing = [name for name in ("cloudflared", "tor") if not command_exists(name)]
    if not missing:
        return
    if is_termux() and command_exists("pkg"):
        print(f"Installing missing link tools: {', '.join(missing)}")
        run_command(["pkg", "install", "-y", *missing])
    elif "cloudflared" in missing:
        install_cloudflared_linux()
    still_missing = [name for name in ("cloudflared", "tor") if not command_exists(name)]
    if still_missing:
        print(f"{tr('unavailable', lang)}: {', '.join(still_missing)}")


def find_free_port(start: int = 8080, end: int = 9999) -> int:
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free TCP port was found.")


def local_ip() -> str:
    with contextlib.suppress(Exception):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("1.1.1.1", 80))
            address = sock.getsockname()[0]
            if ipaddress.ip_address(address).is_private:
                return address
    with contextlib.suppress(Exception):
        return socket.gethostbyname(socket.gethostname())
    return "127.0.0.1"


def start_cloudflared(port: int, runtime: Path) -> Tuple[Optional[subprocess.Popen], Path]:
    log_path = runtime / "cloudflared.log"
    if not command_exists("cloudflared"):
        return None, log_path
    log_handle = log_path.open("w", encoding="utf-8")
    try:
        process = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate"],
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True,
        )
        process._dedsec_log_handle = log_handle  # type: ignore[attr-defined]
        return process, log_path
    except Exception:
        log_handle.close()
        return None, log_path


def start_tor(port: int, runtime: Path) -> Tuple[Optional[subprocess.Popen], Path]:
    tor_base = runtime / "tor"
    data_dir = tor_base / "data"
    hidden_dir = tor_base / "hidden-service"
    torrc = tor_base / "torrc"
    log_path = tor_base / "tor.log"
    hostname_path = hidden_dir / "hostname"
    if not command_exists("tor"):
        return None, hostname_path
    data_dir.mkdir(parents=True, exist_ok=True)
    hidden_dir.mkdir(parents=True, exist_ok=True)
    for directory in (tor_base, data_dir, hidden_dir):
        with contextlib.suppress(Exception):
            directory.chmod(0o700)
    torrc.write_text(
        f"DataDirectory {data_dir}\nSocksPort 0\nControlPort 0\nLog notice stdout\nHiddenServiceDir {hidden_dir}\nHiddenServicePort 80 127.0.0.1:{port}\n",
        encoding="utf-8",
    )
    log_handle = log_path.open("w", encoding="utf-8")
    try:
        process = subprocess.Popen(["tor", "-f", str(torrc)], stdout=log_handle, stderr=subprocess.STDOUT, text=True)
        process._dedsec_log_handle = log_handle  # type: ignore[attr-defined]
        return process, hostname_path
    except Exception:
        log_handle.close()
        return None, hostname_path


def stop_process(process: Optional[subprocess.Popen]) -> None:
    if not process:
        return
    with contextlib.suppress(Exception):
        process.terminate()
        process.wait(timeout=4)
    if process.poll() is None:
        with contextlib.suppress(Exception):
            process.kill()
    handle = getattr(process, "_dedsec_log_handle", None)
    if handle:
        with contextlib.suppress(Exception):
            handle.close()


def wait_for_public_links(
    cloudflared: Optional[subprocess.Popen],
    cloudflared_log: Path,
    tor: Optional[subprocess.Popen],
    tor_hostname: Path,
    timeout: float = 60.0,
) -> Tuple[str, str]:
    cloudflare_url = ""
    onion_url = ""
    deadline = time.time() + timeout
    pattern = re.compile(r"https://[A-Za-z0-9-]+\.trycloudflare\.com")
    while time.time() < deadline:
        if not cloudflare_url and cloudflared_log.exists():
            with contextlib.suppress(Exception):
                match = pattern.search(cloudflared_log.read_text(encoding="utf-8", errors="replace"))
                if match:
                    cloudflare_url = match.group(0)
        if not onion_url and tor_hostname.exists():
            with contextlib.suppress(Exception):
                hostname = tor_hostname.read_text(encoding="utf-8", errors="replace").strip()
                if hostname.endswith(".onion"):
                    onion_url = "http://" + hostname
        cloudflare_done = cloudflare_url or cloudflared is None or cloudflared.poll() is not None
        tor_done = onion_url or tor is None or tor.poll() is not None
        if cloudflare_done and tor_done:
            break
        time.sleep(0.25)
    return cloudflare_url, onion_url


def open_browser(url: str) -> None:
    command = None
    if command_exists("termux-open-url"):
        command = ["termux-open-url", url]
    elif command_exists("xdg-open"):
        command = ["xdg-open", url]
    if command:
        with contextlib.suppress(Exception):
            subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def start_server_session(cfg: Dict[str, Any], profile_id: str) -> None:
    global ACTIVE_CONFIG, ACTIVE_PROFILE, ACTIVE_ROOT
    profile = cfg.get("servers", {}).get(profile_id)
    if not profile:
        raise SystemExit(f"Unknown server profile: {profile_id}")
    lang = EDITION_LANGUAGE
    root = Path(profile["root"]).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    ACTIVE_CONFIG = cfg
    ACTIVE_PROFILE = profile
    ACTIVE_ROOT = root.resolve(strict=True)
    server_internal_dir()
    audit_event("server_started", f"Profile={profile_id}", actor="termux-manager")
    app.secret_key = hashlib.sha256(f"{cfg['secret_key']}:{profile['secret']}:{profile_id}".encode("utf-8")).digest()
    app.config["SESSION_COOKIE_NAME"] = f"dedsec_server_{slugify(profile_id)}"

    ensure_link_dependencies(lang)
    port = find_free_port()
    session_id = f"{profile_id}-{int(time.time())}-{os.getpid()}-{secrets.token_hex(3)}"
    runtime = RUNTIME_BASE / session_id
    runtime.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(Exception):
        runtime.chmod(0o700)

    http_server = make_server("0.0.0.0", port, app, threaded=True)
    http_thread = threading.Thread(target=http_server.serve_forever, name="dedsec-http", daemon=True)
    cloudflared: Optional[subprocess.Popen] = None
    tor: Optional[subprocess.Popen] = None
    old_int = signal.getsignal(signal.SIGINT)
    old_term = signal.getsignal(signal.SIGTERM)

    def _interrupt(_signum, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, _interrupt)
    signal.signal(signal.SIGTERM, _interrupt)
    http_thread.start()

    try:
        print(f"\n{tr('selected_server', lang)}: {profile['name']}")
        print(tr("starting_links", lang))
        if not profile_has_password(profile):
            print(tr("passwordless_warning_cli", lang))

        lan_url = f"http://{local_ip()}:{port}"
        localhost_url = f"http://127.0.0.1:{port}"
        print(f"\n{APP_NAME} [{profile['name']}]")
        print(f"{tr('local_network', lang):<18} {lan_url}")
        print(f"{tr('localhost', lang):<18} {localhost_url}")

        cloudflared, cloudflared_log = start_cloudflared(port, runtime)
        tor, tor_hostname = start_tor(port, runtime)
        cloudflare_url, onion_url = wait_for_public_links(cloudflared, cloudflared_log, tor, tor_hostname)
        print(f"{tr('cloudflare', lang):<18} {cloudflare_url or tr('unavailable', lang)}")
        print(f"{tr('tor', lang):<18} {onion_url or tr('unavailable', lang)}")
        print(f"\n{tr('stop_hint', lang)}")
        print(f"Session: {session_id}\nLogs: {runtime}")
        open_browser(localhost_url)

        while http_thread.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print()
    finally:
        signal.signal(signal.SIGINT, old_int)
        signal.signal(signal.SIGTERM, old_term)
        http_server.shutdown()
        http_server.server_close()
        stop_process(cloudflared)
        stop_process(tor)
        audit_event("server_stopped", f"Profile={profile_id}", actor="termux-manager")
        shutil.rmtree(runtime, ignore_errors=True)


# ---------------------------------------------------------------------------
# CLI manager
# ---------------------------------------------------------------------------


def manage_server_admins_cli(cfg: Dict[str, Any], lang: str) -> None:
    lang = EDITION_LANGUAGE
    if not require_manager(cfg, lang):
        return
    profile_id = select_profile(cfg, lang)
    if not profile_id:
        return
    profile = cfg["servers"][profile_id]
    _normalize_profile_admins(profile)
    while True:
        accounts = list(profile.get("admins", []))
        print(f"\n=== {APP_NAME} — {tr('admin_profiles_cli')} — {profile['name']} ===")
        for index, account in enumerate(accounts, 1):
            suffix = (" [ΚΥΡΙΟΣ]" if EDITION_LANGUAGE == "el" else " [MAIN]") if index == 1 else ""
            password_label = "Password" if EDITION_LANGUAGE == "en" else "Κωδικός"
            print(f"{index}) {account.get('username', '')}{suffix} | {password_label}: {termux_password(account)}")
        print(f"\n1) {tr('add_admin')}\n2) {tr('change_admin_password')}\n3) {tr('delete_admin')}\n0) {tr('back_to_menu')}")
        try:
            choice = input(f"{tr('choose_admin_action')}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if choice == "0":
            return
        if choice == "1":
            username = input(f"{tr('admin_username')}: ").strip()
            if not valid_admin_username(username):
                print(tr("invalid_username"))
                continue
            if any(str(item.get("username", "")).casefold() == username.casefold() for item in accounts):
                print(tr("admin_exists"))
                continue
            password = visible_password_input(f"{tr('new_admin_password')}: ")
            confirmation = visible_password_input(f"{tr('confirm_admin_password')}: ")
            if len(password) < 8:
                print(tr("admin_password_minimum"))
                continue
            if not hmac.compare_digest(password, confirmation):
                print(tr("passwords_do_not_match"))
                continue
            profile.setdefault("admins", []).append(make_admin_account(username, password))
            save_config(cfg)
            print(tr("admin_added"))
        elif choice == "2":
            username = input(f"{tr('admin_username')}: ").strip()
            account = next((item for item in accounts if str(item.get("username", "")).casefold() == username.casefold()), None)
            if account is None:
                print(tr("invalid"))
                continue
            password = visible_password_input(f"{tr('new_admin_password')}: ")
            confirmation = visible_password_input(f"{tr('confirm_admin_password')}: ")
            if len(password) < 8:
                print(tr("admin_password_minimum"))
                continue
            if not hmac.compare_digest(password, confirmation):
                print(tr("passwords_do_not_match"))
                continue
            account.update(make_admin_account(str(account.get("username", username)), password))
            if account is accounts[0]:
                profile["password_hash"] = account["password_hash"]
                profile["password_salt"] = account["password_salt"]
                profile["password_scheme"] = account["password_scheme"]
                profile["termux_password"] = account.get("termux_password", "")
            save_config(cfg)
            print(tr("admin_password_changed"))
        elif choice == "3":
            username = input(f"{tr('admin_username')}: ").strip()
            if accounts and str(accounts[0].get("username", "")).casefold() == username.casefold():
                print(tr("main_admin_cannot_delete"))
                continue
            remaining = [item for item in accounts if str(item.get("username", "")).casefold() != username.casefold()]
            if len(remaining) == len(accounts):
                print(tr("invalid"))
                continue
            profile["admins"] = remaining
            save_config(cfg)
            print(tr("admin_deleted"))
        else:
            print(tr("invalid"))

def change_manager_password(cfg: Dict[str, Any], lang: str) -> None:
    new_password = visible_password_input(f"{tr('new_manager_password')}: ")
    if len(new_password) < 8:
        print(tr("password_minimum"))
        return
    confirmation = visible_password_input(f"{tr('confirm_manager_password')}: ")
    if not hmac.compare_digest(new_password, confirmation):
        print(tr("passwords_do_not_match"))
        return
    cfg["manager_password"] = new_password
    save_config(cfg)
    print(tr("manager_password_changed"))


def settings_menu(cfg: Dict[str, Any], lang: str) -> None:
    lang = EDITION_LANGUAGE
    if not require_manager(cfg, lang):
        return
    while True:
        print(f"\n=== {APP_NAME} — {tr('settings')} ===")
        print(f"1) {tr('change_manager_password')}")
        print(f"2) {tr('show_password')}")
        print(f"0) {tr('back_to_menu')}")
        try:
            choice = input(f"{tr('choose_option')}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if choice == "1":
            change_manager_password(cfg, lang)
        elif choice == "2":
            print(f"{tr('current_manager_password')}: {cfg['manager_password']}")
        elif choice == "0":
            return
        else:
            print(tr("invalid"))


def manager_menu(cfg: Dict[str, Any]) -> None:
    cfg["language"] = EDITION_LANGUAGE
    while True:
        lang = EDITION_LANGUAGE
        print_termux_credentials(cfg)
        print(f"\n=== {APP_NAME} — {tr('management')} ===")
        options = (
            ("1", "start_server"),
            ("2", "create_server"),
            ("3", "edit_server"),
            ("4", "delete_server"),
            ("5", "list_servers"),
            ("6", "manage_server_admins_cli"),
            ("7", "settings"),
            ("0", "exit"),
        )
        for number, key in options:
            print(f"{number}) {tr(key)}")
        try:
            choice = input(f"{tr('choose_option')}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if choice == "1":
            profile_id = select_profile(cfg, lang)
            if profile_id:
                start_server_session(cfg, profile_id)
        elif choice == "2":
            create_profile(cfg, lang)
        elif choice == "3":
            edit_profile(cfg, lang)
        elif choice == "4":
            delete_profile(cfg, lang)
        elif choice == "5":
            list_profiles(cfg, lang)
        elif choice == "6":
            manage_server_admins_cli(cfg, lang)
        elif choice == "7":
            settings_menu(cfg, lang)
        elif choice == "0":
            return
        else:
            print(tr("invalid"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"{APP_NAME} — multi-profile file server")
    parser.add_argument("--start", nargs="?", const="", metavar="SERVER_ID", help="start a server profile")
    parser.add_argument("--create", action="store_true", help="create a server profile")
    parser.add_argument("--edit", action="store_true", help="edit a server profile")
    parser.add_argument("--delete", action="store_true", help="delete a server profile")
    parser.add_argument("--list-servers", action="store_true", help="list server profiles")
    parser.add_argument("--show-password", action="store_true", help="show the local management password")
    return parser


def main() -> None:
    cfg = load_config()
    lang = EDITION_LANGUAGE
    args = build_parser().parse_args()
    if args.create:
        create_profile(cfg, lang)
    elif args.edit:
        edit_profile(cfg, lang)
    elif args.delete:
        delete_profile(cfg, lang)
    elif args.list_servers:
        list_profiles(cfg, lang)
    elif args.show_password:
        print(cfg["manager_password"])
    elif args.start is not None:
        profile_id = args.start or select_profile(cfg, lang)
        if profile_id:
            start_server_session(cfg, profile_id)
    else:
        manager_menu(cfg)


if __name__ == "__main__":
    main()
