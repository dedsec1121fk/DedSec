#!/usr/bin/env python3 

import os
import re
import sys
import time
import json
import urllib.request
import urllib.parse
import urllib.error
import zipfile
import glob
import base64
import queue
import shutil
import socket
import ipaddress
import sqlite3
import logging
import mimetypes
import pathlib
import threading
import subprocess
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Tuple, Any
import hashlib
import hmac
import ssl


# ---------------------------
# Minimal dependency bootstrap (Termux-aware)
# ---------------------------

def _run(cmd, *, check=False, capture=False, text=True, env=None):
    """_run.

Internal helper function.

This docstring was expanded to make future maintenance easier.

Args:
    cmd: Parameter.
    check: Parameter.
    capture: Parameter.
    text: Parameter.
    env: Parameter.

Returns:
    Varies.
"""
    try:
        if capture:
            return subprocess.run(cmd, check=check, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=text, env=env)
        return subprocess.run(cmd, check=check, env=env)
    except FileNotFoundError:
        return None

def _bash(cmd: str, capture: bool=False):
    """_bash.

Internal helper function.

This docstring was expanded to make future maintenance easier.

Args:
    cmd: Parameter.
    capture: Parameter.

Returns:
    Varies.
"""
    return _run(["bash", "-lc", cmd], check=False, capture=capture)

def _is_termux() -> bool:
    """_is_termux.

Internal helper function.

This docstring was added automatically to improve maintainability.

Returns:
    Varies.
"""
    prefix = os.environ.get("PREFIX", "")
    return ("com.termux" in prefix) or os.path.exists("/data/data/com.termux/files/usr/bin/pkg")

def _termux_pkg_install(pkgs):
    """_termux_pkg_install.

Internal helper function.

This docstring was expanded to make future maintenance easier.

Args:
    pkgs: Parameter.

Returns:
    Varies.
"""
    if isinstance(pkgs, str):
        pkgs = [pkgs]
    _bash("pkg update -y", capture=False)
    _bash("pkg install -y " + " ".join(pkgs), capture=False)

def ensure_dependencies():
    # flask + werkzeug included with flask
    """ensure_dependencies.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    # flask + werkzeug included with flask
    try:
        import flask  # noqa
    except Exception:
        _run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=False)
        _run([sys.executable, "-m", "pip", "install", "flask>=2.3"], check=False)

    # cryptography (prefer termux package)
    try:
        import cryptography  # noqa
    except Exception:
        if _is_termux():
            _termux_pkg_install(["python-cryptography", "openssl"])
        try:
            import cryptography  # noqa
        except Exception:
            env = os.environ.copy()
            if _is_termux() and "ANDROID_API_LEVEL" not in env:
                try:
                    sdk = subprocess.check_output(["getprop", "ro.build.version.sdk"], text=True).strip()
                    if sdk.isdigit():
                        env["ANDROID_API_LEVEL"] = sdk
                except Exception:
                    pass
            _run([sys.executable, "-m", "pip", "install", "cryptography>=41.0"], check=False, env=env)

ensure_dependencies()

from flask import (
    Flask, request, redirect, url_for, session, abort,
    Response, flash, render_template, render_template_string, jsonify, g, send_file
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from jinja2 import DictLoader
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa, padding as asym_padding
from cryptography import x509
from cryptography.x509.oid import NameOID

# ---------------------------
# Paths / logging
# ---------------------------

WATERMARK = ""

# ---------------------------
# Appearance presets (saved per user)
# ---------------------------
ACCENT_PRESETS = {
    "purple": {"label": "Purple", "accent": "#cd93ff", "hover": "#e2c1ff"},
    "blue":   {"label": "Blue",   "accent": "#74c0fc", "hover": "#a5d8ff"},
    "green":  {"label": "Green",  "accent": "#69db7c", "hover": "#b2f2bb"},
    "red":    {"label": "Red",    "accent": "#ff6b6b", "hover": "#ffa8a8"},
    "orange": {"label": "Orange", "accent": "#ffa94d", "hover": "#ffd8a8"},
    "pink":   {"label": "Pink",   "accent": "#f783ac", "hover": "#ffb3c6"},
}

FONT_PRESETS = {
    "system": {"label": "System", "stack": 'system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", "Helvetica Neue", Arial, "Apple Color Emoji","Segoe UI Emoji"'},
    "clean_sans": {"label": "Clean Sans", "stack": '"Noto Sans", "Segoe UI", Roboto, Arial, sans-serif'},
    "readable_sans": {"label": "Readable Sans", "stack": 'Verdana, "Noto Sans", "Segoe UI", Arial, sans-serif'},
    "compact_sans": {"label": "Compact Sans", "stack": 'Tahoma, "Noto Sans", "Segoe UI", Arial, sans-serif'},
    "humanist": {"label": "Humanist Sans", "stack": '"Trebuchet MS", "Noto Sans", "Segoe UI", Arial, sans-serif'},
    "modern_ui": {"label": "Modern UI", "stack": '"Inter", "Noto Sans", "Segoe UI", Roboto, Arial, sans-serif'},
    "rounded_ui": {"label": "Rounded UI", "stack": '"Nunito", "Noto Sans", "Segoe UI", Arial, sans-serif'},
    "wide_sans": {"label": "Wide Sans", "stack": '"Lucida Sans Unicode", "Lucida Grande", "Noto Sans", "Segoe UI", Arial, sans-serif'},
    "news": {"label": "News Serif", "stack": 'Georgia, "Noto Serif", "Times New Roman", Times, serif'},
    "classic_serif": {"label": "Classic Serif", "stack": 'Cambria, "Noto Serif", Georgia, serif'},
    "mono": {"label": "Monospace", "stack": 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "DejaVu Sans Mono", "Courier New", monospace'},
    "terminal": {"label": "Terminal Mono", "stack": '"DejaVu Sans Mono", "Noto Sans Mono", Consolas, "Liberation Mono", monospace'},
}

UI_THEME_PRESETS = {
    "default": {"label": "Default"},
    "matrix": {"label": "Matrix"},
    "ocean": {"label": "Ocean"},
    "amber": {"label": "Amber"},
    "crimson": {"label": "Crimson"},
    "silver": {"label": "Silver"},
    "rose": {"label": "Rose"},
    "forest": {"label": "Forest"},
    "midnight": {"label": "Midnight"},
    "neon": {"label": "Neon"},
    "lavender": {"label": "Lavender"},
    "cyber": {"label": "Cyber"},
    "emerald": {"label": "Emerald"},
    "sunset": {"label": "Sunset"},
    "ice": {"label": "Ice"},
    "coffee": {"label": "Coffee"},
    "obsidian": {"label": "Obsidian"},
    "royal": {"label": "Royal"},
    "peach": {"label": "Peach"},
    "terminal": {"label": "Terminal"},
    "storm": {"label": "Storm"},
    "mint": {"label": "Mint"},
    "plum": {"label": "Plum"},
    "gold": {"label": "Gold"},
    "volcano": {"label": "Volcano"},
    "glacier": {"label": "Glacier"},
    "nightshade": {"label": "Nightshade"},
    "sand": {"label": "Sand"},
    "aqua": {"label": "Aqua"},
    "orchid": {"label": "Orchid"},
}

ACCENT_CHOICES = [{"key": k, "label": v["label"]} for k, v in ACCENT_PRESETS.items()]
FONT_CHOICES = [{"key": k, "label": v["label"]} for k, v in FONT_PRESETS.items()]
UI_THEME_CHOICES = [{"key": k, "label": v["label"]} for k, v in UI_THEME_PRESETS.items()]

DEFAULT_PREFS = {"accent_key": "purple", "font_key": "system", "ui_theme_key": "default"}


LOGO_DARK_URL = "https://raw.githubusercontent.com/dedsec1121fk/dedsec1121fk.github.io/c0d1f698cc38dbd0535a94f8865ac9ba9fb45086/Assets/Images/Logos/Black%20Purple%20Butterfly%20Logo.jpeg"
LOGO_LIGHT_URL = "https://raw.githubusercontent.com/dedsec1121fk/dedsec1121fk.github.io/c0d1f698cc38dbd0535a94f8865ac9ba9fb45086/Assets/Images/Logos/White%20Purple%20Butterfly%20Logo.jpeg"

HOME = os.path.expanduser("~")
LEGACY_BASE_DIR = os.path.join(HOME, "ButSystem")  # old internal (non-persistent) location

def _termux_shared_root() -> Optional[str]:
    """Return Termux shared storage root if termux-setup-storage was run."""
    try:
        shared = os.path.join(HOME, "storage", "shared")
        if os.path.isdir(shared):
            ap = os.path.abspath(shared)
            # Usually resolves to /storage/emulated/0
            if ap.startswith("/storage/") or os.path.islink(shared):
                return ap
    except Exception:
        pass
    return None

def _choose_homework_root() -> str:
    """Prefer phone storage so data survives Termux uninstall."""
    candidates = []
    ext = os.environ.get("EXTERNAL_STORAGE")
    if ext:
        candidates.append(os.path.join(ext, "Homework"))
    shared = _termux_shared_root()
    if shared:
        candidates.append(os.path.join(shared, "Homework"))
    candidates.append("/storage/emulated/0/Homework")

    seen = set()
    for root in candidates:
        if not root or root in seen:
            continue
        seen.add(root)
        try:
            os.makedirs(root, exist_ok=True)
            if os.path.isdir(root) and os.access(root, os.W_OK):
                return root
        except Exception:
            continue

    # Fallback (non-persistent): still run, but data may be lost on uninstall
    fallback = os.path.join(HOME, "Homework")
    try:
        os.makedirs(fallback, exist_ok=True)
    except Exception:
        pass
    return fallback

def _choose_face_detector_output_dir() -> str:
    """Prefer phone Downloads for saved face detector captures."""
    candidates = []
    shared = _termux_shared_root()
    if shared:
        candidates.append(os.path.join(shared, "Download", "ButSystem", "Face Detector"))
        candidates.append(os.path.join(shared, "Downloads", "ButSystem", "Face Detector"))
    candidates.append(os.path.join(HOME, "storage", "downloads", "ButSystem", "Face Detector"))
    candidates.append(os.path.join(HOME, "Downloads", "ButSystem", "Face Detector"))
    candidates.append(os.path.join(HOME, "ButSystem", "Face Detector"))

    seen = set()
    for root in candidates:
        if not root or root in seen:
            continue
        seen.add(root)
        try:
            os.makedirs(root, exist_ok=True)
            if os.path.isdir(root) and os.access(root, os.W_OK):
                return root
        except Exception:
            continue
    fallback = os.path.join(HOME, "ButSystem", "Face Detector")
    try:
        os.makedirs(fallback, exist_ok=True)
    except Exception:
        pass
    return fallback

HOMEWORK_ROOT = _choose_homework_root()
BASE_DIR = os.path.join(HOMEWORK_ROOT, "ButSystem")

DATA_DIR = os.path.join(BASE_DIR, "data")
STORAGE_DIR = os.path.join(BASE_DIR, "storage")          # user vault files (plaintext)
KEYS_DIR = os.path.join(BASE_DIR, "keys")
LOG_DIR = os.path.join(BASE_DIR, "logs")
TOR_DIR = os.path.join(HOME, ".ButSystem_tor")  # internal (Tor requires strict perms)

ATT_DIR = os.path.join(DATA_DIR, "attachments_enc")      # chat voice + profiler attachments (plaintext)
TMP_UPLOAD_DIR = os.path.join(DATA_DIR, "tmp_uploads")    # temporary plain uploads before background encryption
PFP_DIR = os.path.join(DATA_DIR, "profile_pics_enc")     # user profile pictures (plaintext)
DM_FILES_DIR = os.path.join(DATA_DIR, "dm_files_enc")    # DM file exchange (plaintext)
DISC_FILES_DIR = os.path.join(DATA_DIR, "discussion_files_enc")  # Discussion attachments (plaintext)
FACE_DETECTOR_DIR = _choose_face_detector_output_dir()

DB_PATH = os.path.join(DATA_DIR, "butsystem.db")
MASTER_KEY_PATH = os.path.join(KEYS_DIR, "master.key")
SESSION_KEY_PATH = os.path.join(KEYS_DIR, "session.key")
LOG_PATH = os.path.join(LOG_DIR, "butsystem.log")

def _migrate_legacy_data():
    """Best-effort: move ~/ButSystem -> Homework/ButSystem on upgrade."""
    try:
        if not os.path.isdir(LEGACY_BASE_DIR):
            return
        legacy_db = os.path.join(LEGACY_BASE_DIR, "data", "butsystem.db")
        new_db = os.path.join(BASE_DIR, "data", "butsystem.db")
        if os.path.exists(new_db):
            return
        if not os.path.exists(legacy_db):
            return
        os.makedirs(BASE_DIR, exist_ok=True)
        # Copy only if destination doesn't already have the item
        for name in os.listdir(LEGACY_BASE_DIR):
            src = os.path.join(LEGACY_BASE_DIR, name)
            dst = os.path.join(BASE_DIR, name)
            if os.path.exists(dst):
                continue
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
    except Exception as e:
        try:
            print(f"[ButSystem] Legacy migration skipped: {e}")
        except Exception:
            pass

_migrate_legacy_data()

for d in (BASE_DIR, DATA_DIR, STORAGE_DIR, KEYS_DIR, LOG_DIR, TOR_DIR, ATT_DIR, PFP_DIR, DM_FILES_DIR, DISC_FILES_DIR, FACE_DETECTOR_DIR):
    os.makedirs(d, exist_ok=True)

# ---------------------------
# Device binding (protect admin from remote/conflicts)
# ---------------------------

DEVICE_ID_PATH = os.path.join(KEYS_DIR, "device.id")

def load_or_create_device_id() -> str:
    """Stable per-device id stored in persistent Homework folder."""
    try:
        if os.path.exists(DEVICE_ID_PATH):
            raw = open(DEVICE_ID_PATH, "r", encoding="utf-8").read().strip()
            if raw:
                return raw
    except Exception:
        pass
    did = base64.urlsafe_b64encode(os.urandom(18)).decode("ascii").rstrip("=")
    try:
        with open(DEVICE_ID_PATH, "w", encoding="utf-8") as f:
            f.write(did)
        try:
            os.chmod(DEVICE_ID_PATH, 0o600)
        except Exception:
            pass
    except Exception:
        # fallback (non-persistent)
        return did
    return did

DEVICE_ID = load_or_create_device_id()


logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("butsystem")

# ---------------------------
# Crypto helpers (TEXT encryption only; binary files stored plaintext)
# ---------------------------

MAGIC = b"BUTSYS1"
NONCE_LEN = 12
TAG_LEN = 16
HDR_LEN = len(MAGIC) + NONCE_LEN + TAG_LEN
CHUNK = 4 * 1024 * 1024  # 4 MiB chunks for fast encrypted streaming (low RAM + good throughput)

def load_or_create_master_key() -> bytes:
    """load_or_create_master_key.

Internal helper function.

This docstring was added automatically to improve maintainability.

Returns:
    Varies.
"""
    if os.path.exists(MASTER_KEY_PATH):
        raw = open(MASTER_KEY_PATH, "rb").read().strip()
        key = base64.urlsafe_b64decode(raw)
        if len(key) != 32:
            raise RuntimeError("Invalid master key length.")
        return key
    key = os.urandom(32)
    with open(MASTER_KEY_PATH, "wb") as f:
        f.write(base64.urlsafe_b64encode(key))
    try:
        os.chmod(MASTER_KEY_PATH, 0o600)
    except Exception:
        pass
    return key

MASTER_KEY = load_or_create_master_key()

def aesgcm_encrypt_stream(src_fp, dst_path: str):
    """File format: MAGIC || NONCE || TAG || CIPHERTEXT"""
    nonce = os.urandom(NONCE_LEN)
    cipher = Cipher(algorithms.AES(MASTER_KEY), modes.GCM(nonce))
    encryptor = cipher.encryptor()

    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    with open(dst_path, "wb") as out:
        out.write(MAGIC)
        out.write(nonce)
        out.write(b"\x00" * TAG_LEN)  # tag placeholder

        while True:
            chunk = src_fp.read(CHUNK)
            if not chunk:
                break
            out.write(encryptor.update(chunk))
        encryptor.finalize()
        tag = encryptor.tag

        out.seek(len(MAGIC) + NONCE_LEN)
        out.write(tag)

def _filestorage_size(file_storage) -> Optional[int]:
    """Return the size (bytes) of an uploaded FileStorage if possible.

    We prefer stream seeking because Content-Length is not always available for
    multipart parts on all clients.
    """
    if file_storage is None:
        return None
    try:
        cl = getattr(file_storage, "content_length", None)
        if cl is not None:
            cl = int(cl)
            if cl >= 0:
                return cl
    except Exception:
        pass
    try:
        s = getattr(file_storage, "stream", None)
        if s is None:
            return None
        pos = None
        try:
            pos = s.tell()
        except Exception:
            pos = None
        try:
            s.seek(0, os.SEEK_END)
            size = int(s.tell())
        finally:
            try:
                if pos is None:
                    s.seek(0)
                else:
                    s.seek(pos)
            except Exception:
                pass
        return size
    except Exception:
        return None

def _save_plain_upload(file_storage, tmp_path: str) -> int:
    """Save uploaded file to disk quickly (plain) and return size.

    Speed notes:
      - Prefer Werkzeug's built-in `save()` which streams efficiently to disk.
      - Fallback to a large-buffer copy for environments where `save()` misbehaves.
    """
    os.makedirs(os.path.dirname(tmp_path), exist_ok=True)

    # Fast path: Werkzeug's streaming save (usually the quickest).
    try:
        file_storage.save(tmp_path)
        return int(os.path.getsize(tmp_path))
    except Exception:
        pass

    # Fallback: manual copy with a large buffer (minimize Python overhead).
    size = 0
    try:
        try:
            file_storage.stream.seek(0)
        except Exception:
            pass
        with open(tmp_path, "wb") as out:
            shutil.copyfileobj(file_storage.stream, out, length=8 * 1024 * 1024)  # 8 MiB buffer
        size = int(os.path.getsize(tmp_path))
    except Exception:
        # Last resort: try save again (some backends reset stream after failure)
        file_storage.save(tmp_path)
        size = int(os.path.getsize(tmp_path))
    return int(size)

def _bg_encrypt_file(tmp_plain: str, out_enc: str, finalize_fn):
    """Encrypt tmp_plain -> out_enc in a background thread, then call finalize_fn(success:bool, err:str|None)."""
    def worker():
        """worker.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
        err = None
        ok = False
        try:
            with open(tmp_plain, "rb") as fp:
                aesgcm_encrypt_stream(fp, out_enc)
            ok = True
        except Exception as e:
            err = str(e)
        finally:
            try:
                if os.path.exists(tmp_plain):
                    os.remove(tmp_plain)
            except Exception:
                pass
            try:
                finalize_fn(ok, err)
            except Exception:
                pass
    threading.Thread(target=worker, daemon=True).start()



def aesgcm_decrypt_generator(src_path: str):
    """aesgcm_decrypt_generator.

Cryptography helper for encrypting/decrypting application data.

This docstring was expanded to make future maintenance easier.

Args:
    src_path: Parameter.

Returns:
    Varies.
"""
    with open(src_path, "rb") as f:
        hdr = f.read(HDR_LEN)
        if len(hdr) != HDR_LEN or hdr[:len(MAGIC)] != MAGIC:
            raise ValueError("Not an encrypted ButSystem blob.")
        nonce = hdr[len(MAGIC):len(MAGIC)+NONCE_LEN]
        tag = hdr[len(MAGIC)+NONCE_LEN:HDR_LEN]

        cipher = Cipher(algorithms.AES(MASTER_KEY), modes.GCM(nonce, tag))
        decryptor = cipher.decryptor()

        while True:
            chunk = f.read(CHUNK)
            if not chunk:
                break
            out = decryptor.update(chunk)
            if out:
                yield out
        out = decryptor.finalize()
        if out:
            yield out

def aesgcm_encrypt_text(plaintext: str) -> str:
    """aesgcm_encrypt_text.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    plaintext: Parameter.

Returns:
    Varies.
"""
    nonce = os.urandom(NONCE_LEN)
    cipher = Cipher(algorithms.AES(MASTER_KEY), modes.GCM(nonce))
    enc = cipher.encryptor()
    ct = enc.update(plaintext.encode("utf-8")) + enc.finalize()
    blob = nonce + enc.tag + ct
    return base64.urlsafe_b64encode(blob).decode("ascii")

def aesgcm_decrypt_text(blob_b64: str) -> str:
    """aesgcm_decrypt_text.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    blob_b64: Parameter.

Returns:
    Varies.
"""
    blob = base64.urlsafe_b64decode(blob_b64.encode("ascii"))
    nonce = blob[:NONCE_LEN]
    tag = blob[NONCE_LEN:NONCE_LEN+TAG_LEN]
    ct = blob[NONCE_LEN+TAG_LEN:]
    cipher = Cipher(algorithms.AES(MASTER_KEY), modes.GCM(nonce, tag))
    dec = cipher.decryptor()
    pt = dec.update(ct) + dec.finalize()
    return pt.decode("utf-8", errors="replace")

# ---------------------------
# Database
# ---------------------------

def db_connect():
    """db_connect.

Database helper for connecting to or initializing the SQLite database.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def now_z() -> str:
    """now_z.

Internal helper function.

This docstring was added automatically to improve maintainability.

Returns:
    Varies.
"""
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def db_init():
    """db_init.

Database helper for connecting to or initializing the SQLite database.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    conn = db_connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        pw_hash TEXT NOT NULL,
        is_admin INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """)

    # lightweight schema migration
    cols = [r[1] for r in cur.execute("PRAGMA table_info(users)").fetchall()]
    if "logout_at" not in cols:
        try:
            cur.execute("ALTER TABLE users ADD COLUMN logout_at TEXT")
        except Exception:
            pass

    if "admin_device_id" not in cols:
        try:
            cur.execute("ALTER TABLE users ADD COLUMN admin_device_id TEXT")
        except Exception:
            pass

    # Bind any existing admin(s) to this device so admin cannot be reused across devices.
    try:
        cur.execute(
            "UPDATE users SET admin_device_id=? WHERE is_admin=1 AND (admin_device_id IS NULL OR admin_device_id='')",
            (DEVICE_ID,)
        )
    except Exception:
        pass

    
    # Security questions / 2FA (best-effort; answers are hashed)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_security (
        username TEXT PRIMARY KEY,
        q1 TEXT,
        q2 TEXT,
        q3 TEXT,
        a1_hash TEXT,
        a2_hash TEXT,
        a3_hash TEXT,
        enabled INTEGER NOT NULL DEFAULT 0,
        updated_at TEXT
    )
    """)
    def _ensure_col(table: str, col: str, ddl: str):
        """_ensure_col.

Internal helper function.

This docstring was expanded to make future maintenance easier.

Args:
    table: Parameter.
    col: Parameter.
    ddl: Parameter.

Returns:
    Varies.
"""
        try:
            cols = [r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]
            if col not in cols:
                cur.execute(ddl)
        except Exception:
            pass

    # dm_messages new columns (backward compatible)
    _ensure_col("dm_messages", "has_file", "ALTER TABLE dm_messages ADD COLUMN has_file INTEGER NOT NULL DEFAULT 0")
    _ensure_col("dm_messages", "delivered_at", "ALTER TABLE dm_messages ADD COLUMN delivered_at TEXT")
    _ensure_col("dm_messages", "edited_at", "ALTER TABLE dm_messages ADD COLUMN edited_at TEXT")
    _ensure_col("dm_messages", "deleted_at", "ALTER TABLE dm_messages ADD COLUMN deleted_at TEXT")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pending_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        pw_hash TEXT NOT NULL,
        requested_ip TEXT,
        requested_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending'
    )
    """)


    # Trusted devices (auto-login) + device access approval workflow
    cur.execute("""
    CREATE TABLE IF NOT EXISTS trusted_devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        device_fp TEXT NOT NULL,
        token_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        last_used TEXT,
        approved_by TEXT,
        status TEXT NOT NULL DEFAULT 'approved',
        UNIQUE(username, device_fp)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS device_access_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        device_fp TEXT NOT NULL,
        requested_ip TEXT,
        user_agent TEXT,
        requested_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',  -- pending | approved | denied
        approved_by TEXT,
        approved_at TEXT
    )
    """)

    # User visible profile (NOT the Profiler feature): 
    cur.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        username TEXT PRIMARY KEY,
        nickname_enc TEXT,
        bio_enc TEXT,
        links_enc TEXT,
        email_enc TEXT,
        phone_enc TEXT,
        id_number_enc TEXT,
        tax_number_enc TEXT,
        license_plate_enc TEXT,
        car_model_enc TEXT,
        job_enc TEXT,
        town_enc TEXT,
        address_enc TEXT,
        family_members_enc TEXT,
        close_friends_enc TEXT,
        height_enc TEXT,
        weight_enc TEXT,
        hair_color_enc TEXT,
        eye_color_enc TEXT,
        city_enc TEXT,
        country_enc TEXT,
        state_enc TEXT,
        pic_path TEXT,
        pic_mime TEXT,
        updated_at TEXT
    )
    """)
    # profiles new columns (backward compatible)
    _ensure_col("profiles", "email_enc", "ALTER TABLE profiles ADD COLUMN email_enc TEXT")
    _ensure_col("profiles", "phone_enc", "ALTER TABLE profiles ADD COLUMN phone_enc TEXT")
    _ensure_col("profiles", "id_number_enc", "ALTER TABLE profiles ADD COLUMN id_number_enc TEXT")
    _ensure_col("profiles", "tax_number_enc", "ALTER TABLE profiles ADD COLUMN tax_number_enc TEXT")
    _ensure_col("profiles", "license_plate_enc", "ALTER TABLE profiles ADD COLUMN license_plate_enc TEXT")
    _ensure_col("profiles", "car_model_enc", "ALTER TABLE profiles ADD COLUMN car_model_enc TEXT")
    _ensure_col("profiles", "job_enc", "ALTER TABLE profiles ADD COLUMN job_enc TEXT")
    _ensure_col("profiles", "town_enc", "ALTER TABLE profiles ADD COLUMN town_enc TEXT")
    _ensure_col("profiles", "address_enc", "ALTER TABLE profiles ADD COLUMN address_enc TEXT")
    _ensure_col("profiles", "family_members_enc", "ALTER TABLE profiles ADD COLUMN family_members_enc TEXT")
    _ensure_col("profiles", "close_friends_enc", "ALTER TABLE profiles ADD COLUMN close_friends_enc TEXT")
    _ensure_col("profiles", "height_enc", "ALTER TABLE profiles ADD COLUMN height_enc TEXT")
    _ensure_col("profiles", "weight_enc", "ALTER TABLE profiles ADD COLUMN weight_enc TEXT")
    _ensure_col("profiles", "hair_color_enc", "ALTER TABLE profiles ADD COLUMN hair_color_enc TEXT")
    _ensure_col("profiles", "eye_color_enc", "ALTER TABLE profiles ADD COLUMN eye_color_enc TEXT")
    _ensure_col("profiles", "city_enc", "ALTER TABLE profiles ADD COLUMN city_enc TEXT")
    _ensure_col("profiles", "country_enc", "ALTER TABLE profiles ADD COLUMN country_enc TEXT")
    _ensure_col("profiles", "state_enc", "ALTER TABLE profiles ADD COLUMN state_enc TEXT")

    # Per-user appearance preferences (accent + font)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_prefs (
        username TEXT PRIMARY KEY,
        accent_key TEXT,
        font_key TEXT,
        updated_at TEXT
    )
    """)
    _ensure_col("user_prefs", "accent_key", "ALTER TABLE user_prefs ADD COLUMN accent_key TEXT")
    _ensure_col("user_prefs", "font_key", "ALTER TABLE user_prefs ADD COLUMN font_key TEXT")
    _ensure_col("user_prefs", "ui_theme_key", "ALTER TABLE user_prefs ADD COLUMN ui_theme_key TEXT")
    _ensure_col("user_prefs", "updated_at", "ALTER TABLE user_prefs ADD COLUMN updated_at TEXT")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_pin_locks (
        owner TEXT NOT NULL,
        scope TEXT NOT NULL,      -- 'dm' | 'group'
        target TEXT NOT NULL,     -- username for dm, group id string for group
        pin_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        PRIMARY KEY(owner, scope, target)
    )
    """)

    # Direct chat messages (encrypted text)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS dm_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        recipient TEXT NOT NULL,
        body_enc TEXT NOT NULL,
        created_at TEXT NOT NULL,
        delivered_at TEXT,
        read_at TEXT,
        has_voice INTEGER NOT NULL DEFAULT 0,
        has_file INTEGER NOT NULL DEFAULT 0,
        edited_at TEXT,
        deleted_at TEXT
    )
    """)

    # Direct chat files (NOT encrypted)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS dm_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dm_id INTEGER NOT NULL,
        filename TEXT,
        mime TEXT,
        stored_path TEXT,
        size INTEGER,
        created_at TEXT
    )
    """)

    # Direct chat voice attachments (encrypted)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS dm_voice (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dm_id INTEGER NOT NULL,
        mime TEXT,
        stored_path TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(dm_id) REFERENCES dm_messages(id) ON DELETE CASCADE
    )
    """)

    # WebRTC call signaling (simple polling; requires HTTPS for camera/mic in browsers)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS dm_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        a TEXT NOT NULL,
        b TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TEXT NOT NULL,
        ended_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS dm_call_signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        call_id INTEGER NOT NULL,
        sender TEXT NOT NULL,
        kind TEXT NOT NULL,   -- 'ring' | 'offer' | 'answer' | 'ice' | 'hangup'
        payload TEXT,         -- JSON string
        created_at TEXT NOT NULL
    )
    """)
    # Groups + memberships
    cur.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        owner TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    # role: owner/admin/member
    cur.execute("""
    CREATE TABLE IF NOT EXISTS group_members (
        group_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'member',
        added_at TEXT NOT NULL,
        PRIMARY KEY(group_id, username),
        FOREIGN KEY(group_id) REFERENCES groups(id) ON DELETE CASCADE
    )
    """)

    # Group chat messages (encrypted text)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS group_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        sender TEXT NOT NULL,
        body_enc TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(group_id) REFERENCES groups(id) ON DELETE CASCADE
    )
    """)
    # Group voice attachments (encrypted)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS group_voice (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gm_id INTEGER NOT NULL,
        mime TEXT,
        stored_path TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(gm_id) REFERENCES group_messages(id) ON DELETE CASCADE
    )
    """)

    
    # Live location sharing (opt-in)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_locations (
        username TEXT PRIMARY KEY,
        lat REAL,
        lon REAL,
        accuracy REAL,
        sharing INTEGER NOT NULL DEFAULT 0,
        updated_at TEXT
    )
    """)


    # ---------------- Profiler feature (FULLY encrypted) ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS profiler_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner TEXT NOT NULL,
        first_enc TEXT NOT NULL,
        last_enc TEXT NOT NULL,
        info_enc TEXT NOT NULL,
        optional_enc TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    # profiler_entries schema migration (optional fields stored encrypted as JSON)
    pcols = [r[1] for r in cur.execute("PRAGMA table_info(profiler_entries)").fetchall()]
    if "optional_enc" not in pcols:
        try:
            cur.execute("ALTER TABLE profiler_entries ADD COLUMN optional_enc TEXT")
        except Exception:
            pass
    if "bounty_price" not in pcols:
        try:
            cur.execute("ALTER TABLE profiler_entries ADD COLUMN bounty_price REAL")
        except Exception:
            pass
    if "bounty_set_by" not in pcols:
        try:
            cur.execute("ALTER TABLE profiler_entries ADD COLUMN bounty_set_by TEXT")
        except Exception:
            pass
    if "bounty_updated_at" not in pcols:
        try:
            cur.execute("ALTER TABLE profiler_entries ADD COLUMN bounty_updated_at TEXT")
        except Exception:
            pass
    if "bounty_reason" not in pcols:
        try:
            cur.execute("ALTER TABLE profiler_entries ADD COLUMN bounty_reason TEXT")
        except Exception:
            pass
    cur.execute("""
    CREATE TABLE IF NOT EXISTS profiler_attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_id INTEGER NOT NULL,
        filename_enc TEXT NOT NULL,
        mime_enc TEXT NOT NULL,
        stored_path TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(entry_id) REFERENCES profiler_entries(id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()

db_init()


# ---------------------------
# Appearance preference helpers
# ---------------------------

def get_user_prefs(username: Optional[str]) -> Dict[str, str]:
    """Return saved UI preferences for a user (accent + font).

    Falls back to DEFAULT_PREFS if nothing is saved yet.
    """
    prefs = dict(DEFAULT_PREFS)
    if not username:
        return prefs
    try:
        conn = db_connect()
        row = conn.execute(
            "SELECT accent_key, font_key, ui_theme_key FROM user_prefs WHERE username=?",
            (username,),
        ).fetchone()
        conn.close()
        if row:
            ak = (row["accent_key"] or "").strip()
            fk = (row["font_key"] or "").strip()
            tk = (row["ui_theme_key"] or "").strip() if "ui_theme_key" in row.keys() else ""
            if ak in ACCENT_PRESETS:
                prefs["accent_key"] = ak
            if fk in FONT_PRESETS:
                prefs["font_key"] = fk
            if tk in UI_THEME_PRESETS:
                prefs["ui_theme_key"] = tk
    except Exception:
        pass
    return prefs


def set_user_prefs(username: str, accent_key: str, font_key: str, ui_theme_key: Optional[str]=None) -> None:
    """Persist UI preferences for a user."""
    if not username:
        return
    ak = accent_key if accent_key in ACCENT_PRESETS else DEFAULT_PREFS["accent_key"]
    fk = font_key if font_key in FONT_PRESETS else DEFAULT_PREFS["font_key"]
    tk = ui_theme_key if ui_theme_key in UI_THEME_PRESETS else DEFAULT_PREFS["ui_theme_key"]
    try:
        conn = db_connect()
        conn.execute(
            "INSERT OR REPLACE INTO user_prefs(username, accent_key, font_key, ui_theme_key, updated_at) VALUES (?,?,?,?,?)",
            (username, ak, fk, tk, now_z()),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def prefs_css(prefs: Dict[str, str]) -> str:
    """Build a small CSS override block for the active user's preferences."""
    ak = (prefs or {}).get("accent_key") or DEFAULT_PREFS["accent_key"]
    fk = (prefs or {}).get("font_key") or DEFAULT_PREFS["font_key"]
    a = ACCENT_PRESETS.get(ak, ACCENT_PRESETS[DEFAULT_PREFS["accent_key"]])
    f = FONT_PRESETS.get(fk, FONT_PRESETS[DEFAULT_PREFS["font_key"]])
    # Later :root overrides earlier ones in BUT_CSS
    return f"\n:root{{--accent:{a['accent']};--accent-hover:{a['hover']};--app-font:{f['stack']};}}\n"


# ---------------------------
# Notifications helpers
# ---------------------------

def dm_unread_counts(me: str) -> Tuple[int, Dict[str, int]]:
    """Return (total_unread, {sender: count})."""
    if not me:
        return 0, {}
    conn = db_connect()
    rows = conn.execute("""
        SELECT sender, COUNT(*) AS c
        FROM dm_messages
        WHERE recipient=? AND read_at IS NULL AND (deleted_at IS NULL OR deleted_at='')
        GROUP BY sender
    """, (me,)).fetchall()
    conn.close()
    by = {r["sender"]: int(r["c"]) for r in rows} if rows else {}
    return sum(by.values()), by

# ---------------------------
# Session key
# ---------------------------

def load_or_create_session_key() -> str:
    """load_or_create_session_key.

Internal helper function.

This docstring was added automatically to improve maintainability.

Returns:
    Varies.
"""
    if os.path.exists(SESSION_KEY_PATH):
        raw = open(SESSION_KEY_PATH, "rb").read().strip().decode("utf-8", errors="ignore")
        return raw or base64.urlsafe_b64encode(os.urandom(32)).decode()
    key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    with open(SESSION_KEY_PATH, "wb") as f:
        f.write(key.encode("utf-8"))
    try:
        os.chmod(SESSION_KEY_PATH, 0o600)
    except Exception:
        pass
    return key

# ---------------------------
# Presence (online/offline) — heartbeat
# ---------------------------

PRESENCE = {}  # scope -> {username: last_seen_ts}
PRESENCE_LOCK = threading.Lock()
ONLINE_WINDOW = 45  # seconds

def current_scope() -> str:
    """Return a presence scope based on the host used to reach the app.

    This keeps 'online' accurate per generated link (local vs cloudflared vs tor),
    so users are only shown online if they're actually active on the same link.
    """
    try:
        h = request.headers.get("X-Forwarded-Host") or request.host or "unknown"
    except Exception:
        h = "unknown"
    return (h or "unknown").lower()

def mark_online(username: str, scope: str):
    """mark_online.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    username: Parameter.
    scope: Parameter.

Returns:
    Varies.
"""
    now = time.time()
    with PRESENCE_LOCK:
        bucket = PRESENCE.setdefault(scope, {})
        bucket[username] = now

def is_online(username: str, scope: str) -> bool:
    """is_online.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    username: Parameter.
    scope: Parameter.

Returns:
    Varies.
"""
    now = time.time()
    with PRESENCE_LOCK:
        bucket = PRESENCE.get(scope, {})
        t = bucket.get(username)
    return bool(t and (now - t) <= ONLINE_WINDOW)


def online_usernames(scope: str) -> set:
    """Return a set of usernames considered online in the given scope."""
    now = time.time()
    out = set()
    with PRESENCE_LOCK:
        bucket = dict(PRESENCE.get(scope, {}))
    for u, t in bucket.items():
        try:
            if t and (now - float(t)) <= ONLINE_WINDOW:
                out.add(u)
        except Exception:
            continue
    return out

def scope_capacity_ok(username: str, is_admin_flag: bool, scope: str) -> bool:
    """Enforce a maximum of 20 users per scope (plus 1 admin = 21)."""
    if not scope:
        return True
    online = online_usernames(scope)
    # Refreshing the page / re-login shouldn't count as taking an extra slot.
    if username in online:
        return True
    limit = 21 if is_admin_flag else 20
    return len(online) < limit

def user_cards(scope: str, exclude: Optional[str]=None) -> Tuple[List[Dict[str, object]], int, int]:
    """Return users with profile info, sorted online-first, plus counts."""
    conn = db_connect()
    rows = conn.execute(
        """SELECT u.username, p.nickname_enc, p.pic_path, p.pic_mime
             FROM users u
             LEFT JOIN profiles p ON p.username=u.username
             ORDER BY u.username COLLATE NOCASE ASC"""
    ).fetchall()
    conn.close()

    cards: List[Dict[str, object]] = []
    for r in rows:
        u = r["username"]
        if exclude and u == exclude:
            continue
        nick = u
        try:
            if r["nickname_enc"]:
                nick = aesgcm_decrypt_text(r["nickname_enc"]) or u
        except Exception:
            nick = u
        pic_path = r["pic_path"]
        has_pic = bool(pic_path and os.path.exists(pic_path))
        on = is_online(u, scope)
        cards.append({"username": u, "nickname": nick, "has_pic": has_pic, "online": on})

    # Sort: online first, then nickname/username
    cards.sort(key=lambda c: (0 if c["online"] else 1, str(c["nickname"]).lower(), c["username"].lower()))

    online_count = sum(1 for c in cards if c["online"])
    offline_count = len(cards) - online_count
    return cards, online_count, offline_count

def online_sorted_users(exclude: Optional[str]=None, scope: Optional[str]=None) -> List[Tuple[str, bool]]:
    """online_sorted_users.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    exclude: Parameter.
    scope: Parameter.

Returns:
    Varies.
"""
    sc = scope or "unknown"
    cards, _, _ = user_cards(sc, exclude=exclude)
    return [(c["username"], bool(c["online"])) for c in cards]

# ---------------------------
# App / helpers
# ---------------------------

app = Flask(__name__)
# Respect X-Forwarded-* headers when running behind Cloudflared / reverse proxies.
# This helps correct URL generation (scheme/host) and client IP for security logs.
# Only trust X-Forwarded-* when the direct peer is loopback (cloudflared/tor connect locally).
class _LoopbackProxyFix:
    def __init__(self, wsgi_app):
        self.app = wsgi_app
        self._pf = ProxyFix(wsgi_app, x_for=1, x_proto=1, x_host=1)

    def __call__(self, environ, start_response):
        ra = (environ.get("REMOTE_ADDR") or "").strip()
        if ra in ("127.0.0.1", "::1"):
            return self._pf(environ, start_response)
        # Strip forwarded headers to prevent spoofing when accessed directly on LAN.
        for k in ("HTTP_X_FORWARDED_FOR", "HTTP_X_FORWARDED_PROTO", "HTTP_X_FORWARDED_HOST", "HTTP_X_FORWARDED_PORT"):
            environ.pop(k, None)
        return self.app(environ, start_response)

app.wsgi_app = _LoopbackProxyFix(app.wsgi_app)
app.secret_key = load_or_create_session_key()
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_REFRESH_EACH_REQUEST=False,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    # Global hard cap (needed for Flask/Werkzeug to accept large multipart bodies).
    # We enforce tighter per-feature limits below.
    MAX_CONTENT_LENGTH=(333 * 1024 * 1024) + (8 * 1024 * 1024),  # 333MB file cap (+overhead)
)

# ---------------------------
# Upload size limits (requested)
# ---------------------------
# Chat attachments (DM + Groups): 33MB max per attached file/voice.
CHAT_MAX_BYTES = 33 * 1024 * 1024

# Calls (audio/video) are disabled (Discuss is text/voice/file only)
ENABLE_CALLS = True
# Profile pictures: keep small to reduce risk/CPU (10MB).
PFP_MAX_BYTES = 10 * 1024 * 1024
# Vault Files uploads: 333MB max (applies to both classic and chunked uploads).
FILES_MAX_BYTES = 333 * 1024 * 1024

# ---------------------------
# Security helpers (CSRF + per-request nonce + security headers)
# ---------------------------
# Dependency-free CSRF protection:
#   - A random token stored in the signed session cookie
#   - Automatically injected into POST forms (client-side)
#   - Automatically attached to same-origin POST/PUT/PATCH/DELETE fetch() calls
#
# This keeps the app Termux-friendly (no extra dependencies) while stopping
# cross-site form posts and most CSRF attacks.

# ---------------------------
# Trusted device auto-login (cookie-based)
# ---------------------------

DEVICE_FP_COOKIE = "bs_device_fp"
DEVICE_TOKEN_COOKIE = "bs_device_token"

def _sha256_hex(s: str) -> str:
    try:
        import hashlib
        return hashlib.sha256(s.encode("utf-8")).hexdigest()
    except Exception:
        return ""

def _ensure_device_fp_cookie(resp=None) -> Optional[str]:
    """Ensure a stable per-device fingerprint id (random) stored in a cookie.
    This is *not* hardware fingerprinting; it's a per-browser random id.
    """
    fp = (request.cookies.get(DEVICE_FP_COOKIE) or "").strip()
    if not fp or len(fp) < 16:
        fp = secrets.token_urlsafe(24)
        if resp is not None:
            # 180 days
            resp.set_cookie(DEVICE_FP_COOKIE, fp, max_age=180*24*3600, httponly=True, samesite="Lax", secure=request.is_secure)
    return fp

def _set_device_token_cookie(resp, token: str):
    # 180 days
    resp.set_cookie(DEVICE_TOKEN_COOKIE, token, max_age=180*24*3600, httponly=True, samesite="Lax", secure=request.is_secure)

def _clear_device_token_cookie(resp):
    resp.delete_cookie(DEVICE_TOKEN_COOKIE)
    # Do not delete fp cookie so device approval flow can work.

def _trusted_device_lookup(fp: str, token: str) -> Optional[str]:
    """Return username if token matches a trusted device and is approved."""
    if not fp or not token:
        return None
    th = _sha256_hex(token)
    if not th:
        return None
    conn = db_connect()
    row = conn.execute(
        "SELECT username FROM trusted_devices WHERE device_fp=? AND token_hash=? AND status='approved' LIMIT 1",
        (fp, th)
    ).fetchone()
    conn.close()
    return (row["username"] if row else None)

def _trusted_device_touch(username: str, fp: str):
    try:
        conn = db_connect()
        conn.execute("UPDATE trusted_devices SET last_used=? WHERE username=? AND device_fp=?", (now_z(), username, fp))
        conn.commit()
        conn.close()
    except Exception:
        pass

def _issue_trusted_device(username: str, fp: str, approved_by: Optional[str]=None) -> str:
    """Create or rotate a trusted-device token for (username, fp). Returns raw token."""
    token = secrets.token_urlsafe(32)
    th = _sha256_hex(token)
    conn = db_connect()
    # Upsert (best-effort)
    row = conn.execute("SELECT id FROM trusted_devices WHERE username=? AND device_fp=?", (username, fp)).fetchone()
    if row:
        conn.execute(
            "UPDATE trusted_devices SET token_hash=?, status='approved', approved_by=COALESCE(?, approved_by), created_at=COALESCE(created_at, ?) WHERE id=?",
            (th, approved_by, now_z(), row["id"])
        )
    else:
        conn.execute(
            "INSERT INTO trusted_devices(username, device_fp, token_hash, created_at, last_used, approved_by, status) VALUES(?,?,?,?,?,?, 'approved')",
            (username, fp, th, now_z(), now_z(), approved_by)
        )
    conn.commit()
    conn.close()
    return token

def _admins_list() -> List[str]:
    try:
        conn = db_connect()
        rows = conn.execute("SELECT username FROM users WHERE is_admin=1 ORDER BY username ASC").fetchall()
        conn.close()
        return [r["username"] for r in rows]
    except Exception:
        return []

def csrf_token() -> str:
    """csrf_token.

Internal helper function.

This docstring was added automatically to improve maintainability.

Returns:
    Varies.
"""
    tok = session.get("_csrf")
    if not tok:
        tok = secrets.token_urlsafe(32)
        session["_csrf"] = tok
    return tok

def _same_origin_ok() -> bool:
    """Best-effort same-origin check using Origin / Referer headers.

    Notes:
    - We compare only the host:port (netloc) to avoid false failures behind TLS
      terminators (e.g., Cloudflared) where the app server may see HTTP.
    - If headers are missing, we allow the request.
    - If headers are present but malformed/unparseable, we fail closed.
    """
    from urllib.parse import urlparse

    expected = (request.host or "").lower().strip()
    if not expected:
        return False

    origin = (request.headers.get("Origin") or "").strip()
    ref = (request.headers.get("Referer") or "").strip()

    # If neither header is present, don't block legitimate requests.
    if not origin and not ref:
        return True

    def _netloc(h: str) -> Optional[str]:
        try:
            p = urlparse(h)
            return (p.netloc or "").lower()
        except Exception:
            return None

    if origin:
        n = _netloc(origin)
        if not n:
            return False
        if n != expected:
            return False

    if ref:
        n = _netloc(ref)
        if not n:
            return False
        if n != expected:
            return False

    return True
    return True

@app.before_request
def _set_security_context():
    # Nonce is useful if you later decide to tighten CSP (remove unsafe-inline).
    """_set_security_context.

Internal helper function.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    # Nonce is useful if you later decide to tighten CSP (remove unsafe-inline).
    g.csp_nonce = secrets.token_urlsafe(16)
    # Ensure token exists early so templates can reference it.
    g.csrf_token = csrf_token()

@app.before_request
def _validate_host_header():
    try:
        host = (request.host or "").split(":", 1)[0].strip().strip("[]")
    except Exception:
        host = ""
    if not _host_is_allowed(host):
        log_security_event("blocked_host_header", detail=f"host={host or '?'}", level="warning")
        abort(400)
    return None

@app.before_request
def _csrf_protect():
    """_csrf_protect.

Internal helper function.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return None
    sent = (
        request.headers.get("X-CSRF-Token")
        or request.headers.get("X-CSRFToken")
        or request.form.get("csrf_token")
    )
    tok = csrf_token()
    if (not sent) or (not secrets.compare_digest(str(sent), str(tok))) or (not _same_origin_ok()):
        wants_json = bool(
            request.path.startswith("/api/")
            or request.is_json
            or ("application/json" in (request.headers.get("Accept", "")))
        )
        if wants_json:
            return jsonify({"ok": False, "error": "csrf"}), 400
        flash("Security check failed (CSRF). Please refresh and try again.")
        return redirect(request.referrer or (url_for("profiler") if is_logged_in() else url_for("index")))
    return None



@app.before_request
def _auto_login_from_trusted_device():
    """If the user is not logged in, attempt auto-login using a trusted-device token cookie.
    Skips auto-login when 2FA is enabled for that account.
    """
    try:
        # Always ensure we have a stable device fp cookie on GET pages.
        if request.method in ("GET", "HEAD"):
            # cookie is set in after_request if needed
            pass
        if is_logged_in():
            return None
        fp = (request.cookies.get(DEVICE_FP_COOKIE) or "").strip()
        tok = (request.cookies.get(DEVICE_TOKEN_COOKIE) or "").strip()
        if not fp or not tok:
            return None
        u = _trusted_device_lookup(fp, tok)
        if not u:
            return None
        # Do not auto-login when 2FA is enabled.
        if user_2fa_enabled(u):
            return None
        # Scope capacity check (match normal login)
        try:
            is_admin_u = bool(is_admin(u))
            sc = current_scope()
            if not scope_capacity_ok(u, is_admin_u, sc):
                return None
        except Exception:
            pass

        session["u"] = u
        session.permanent = True
        session["login_at"] = now_z()
        ensure_profile_row(u)
        _trusted_device_touch(u, fp)
        return None
    except Exception:
        return None

@app.after_request
def _security_headers(resp):
    # Keep headers compatible with Termux-local HTTP, while improving safety on HTTPS.
    """_security_headers.

Internal helper function.

This docstring was expanded to make future maintenance easier.

Args:
    resp: Parameter.

Returns:
    Varies.
"""
    # Keep headers compatible with Termux-local HTTP, while improving safety on HTTPS.
    try:
        _ensure_device_fp_cookie(resp)
    except Exception:
        pass
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "same-origin")
    resp.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    resp.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
    resp.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
    resp.headers.setdefault("Origin-Agent-Cluster", "?1")

    # Permissions-Policy helps reduce unexpected browser permission prompts/leaks.
    resp.headers.setdefault(
        "Permissions-Policy",
        "geolocation=(self), microphone=(self), camera=(self), fullscreen=(self), payment=(), display-capture=()"
    )

    # CSP: tuned to keep everything working across iOS/Android/Desktop.
    # (We allow inline scripts for now because templates include a few inline handlers.)
    # If you later remove inline handlers, you can tighten script-src by removing 'unsafe-inline'.
    csp_value = (
        "default-src 'self'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "object-src 'none'; "
        "img-src 'self' data: blob: https:; "
        "media-src 'self' blob: data:; "
        "font-src 'self' data: https:; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "connect-src 'self' https: wss:; "
    )
    try:
        if request.endpoint == 'face_detector_page':
            csp_value = (
                "default-src 'self'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none'; "
                "object-src 'none'; "
                "img-src 'self' data: blob: https:; "
                "media-src 'self' blob: data: https:; "
                "font-src 'self' data: https:; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob: https://cdn.jsdelivr.net; "
                "worker-src 'self' blob: https://cdn.jsdelivr.net; "
                "child-src 'self' blob: https://cdn.jsdelivr.net; "
                "connect-src 'self' https: blob: data: wss:; "
            )
    except Exception:
        pass
    resp.headers.setdefault("Content-Security-Policy", csp_value)

    # Only set HSTS when actually served over HTTPS (safe for Cloudflared/Tor HTTPS frontends).
    try:
        if request.is_secure:
            resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    except Exception:
        pass

    # Avoid caching authenticated or sensitive pages in browsers / shared devices.
    try:
        sensitive_endpoints = {
            "chat_with", "group_chat", "discussion", "profile", "settings_security",
            "settings_appearance_page", "admin_panel", "admin_logs", "profiler", "news",
            "face_detector", "reports", "files", "locations_page"
        }
        if is_logged_in() or (request.endpoint in sensitive_endpoints):
            resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private, max-age=0"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
    except Exception:
        pass

    # Mark cookies Secure when served over HTTPS (keeps local HTTP working).
    try:
        if request.is_secure:
            cookies = resp.headers.getlist("Set-Cookie")
            if cookies:
                resp.headers.pop("Set-Cookie", None)
                for c in cookies:
                    if "; Secure" not in c and "; secure" not in c:
                        c = c + "; Secure"
                    resp.headers.add("Set-Cookie", c)
    except Exception:
        pass

    return resp

def current_user() -> Optional[str]:
    """current_user.

Internal helper function.

This docstring was added automatically to improve maintainability.

Returns:
    Varies.
"""
    return session.get("u")

def is_logged_in() -> bool:
    """is_logged_in.

Internal helper function.

This docstring was added automatically to improve maintainability.

Returns:
    Varies.
"""
    return bool(current_user())


def _normalize_chat_pin(pin: str) -> str:
    pin = re.sub(r"\s+", "", str(pin or ""))
    if not re.fullmatch(r"\d{4,12}", pin):
        raise ValueError("invalid_pin")
    return pin


def _lock_target(scope: str, target) -> str:
    if scope == "dm":
        return str(target or "").strip()
    if scope == "group":
        return str(int(target))
    raise ValueError("invalid_scope")


def _lock_session_key(owner: str, scope: str, target) -> str:
    return f"{owner}|{scope}|{_lock_target(scope, target)}"


def _session_unlocks() -> set:
    raw = session.get("chat_pin_unlocks") or []
    if isinstance(raw, list):
        return set(str(x) for x in raw if x)
    return set()


def _save_session_unlocks(items: set):
    session["chat_pin_unlocks"] = sorted(set(str(x) for x in items if x))
    session.modified = True


def _chat_lock_exists(owner: str, scope: str, target) -> bool:
    if not owner:
        return False
    conn = db_connect()
    try:
        row = conn.execute(
            "SELECT 1 FROM chat_pin_locks WHERE owner=? AND scope=? AND target=? LIMIT 1",
            (owner, scope, _lock_target(scope, target)),
        ).fetchone()
        return bool(row)
    finally:
        conn.close()


def _chat_lock_is_unlocked(owner: str, scope: str, target) -> bool:
    if not _chat_lock_exists(owner, scope, target):
        return True
    return _lock_session_key(owner, scope, target) in _session_unlocks()


def _chat_lock_set(owner: str, scope: str, target, pin: str):
    pin = _normalize_chat_pin(pin)
    t = _lock_target(scope, target)
    conn = db_connect()
    try:
        conn.execute(
            """
            INSERT INTO chat_pin_locks(owner, scope, target, pin_hash, created_at, updated_at)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(owner, scope, target)
            DO UPDATE SET pin_hash=excluded.pin_hash, updated_at=excluded.updated_at
            """,
            (owner, scope, t, generate_password_hash(pin), now_z(), now_z()),
        )
        conn.commit()
    finally:
        conn.close()
    items = _session_unlocks()
    items.add(_lock_session_key(owner, scope, t))
    _save_session_unlocks(items)


def _chat_lock_verify_and_unlock(owner: str, scope: str, target, pin: str) -> bool:
    try:
        pin = _normalize_chat_pin(pin)
    except Exception:
        return False
    conn = db_connect()
    try:
        row = conn.execute(
            "SELECT pin_hash FROM chat_pin_locks WHERE owner=? AND scope=? AND target=?",
            (owner, scope, _lock_target(scope, target)),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return True
    try:
        ok = check_password_hash(row["pin_hash"], pin)
    except Exception:
        ok = False
    if ok:
        items = _session_unlocks()
        items.add(_lock_session_key(owner, scope, target))
        _save_session_unlocks(items)
    return ok


def _chat_lock_remove(owner: str, scope: str, target):
    conn = db_connect()
    try:
        conn.execute(
            "DELETE FROM chat_pin_locks WHERE owner=? AND scope=? AND target=?",
            (owner, scope, _lock_target(scope, target)),
        )
        conn.commit()
    finally:
        conn.close()
    _chat_lock_clear_session(owner, scope, target)


def _chat_lock_clear_session(owner: str, scope: str, target):
    items = _session_unlocks()
    items.discard(_lock_session_key(owner, scope, target))
    _save_session_unlocks(items)


def _locked_json_or_redirect(scope: str, target):
    wants_json = (
        request.path.startswith("/api/")
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in (request.headers.get("Accept", ""))
    )
    if wants_json:
        return jsonify(ok=False, locked=True, error="PIN required"), 423
    if scope == "dm":
        return redirect(url_for("chat_with", username=_lock_target(scope, target)))
    return redirect(url_for("group_chat", gid=int(_lock_target(scope, target))))


# -----------------------------
# Language toggle (EN / EL)
# -----------------------------
# Default language: English ("en"). Toggle route switches between English and Greek ("el").
from flask import g

TRANSLATIONS_EL = {
    # Loading / welcome
    "Welcome": "Καλώς ήρθες",
    "Loading": "Φόρτωση",

    # Navigation / common
    "Files": "Αρχεία",
    "Chats": "Συνομιλίες",
    "Groups": "Ομάδες",
    "News": "Νέα",

    "Live Locations": "Ζωντανές τοποθεσίες",
    "Live location": "Ζωντανή τοποθεσία",
    "Share live location": "Κοινή χρήση ζωντανής τοποθεσίας",
    "Stop sharing": "Διακοπή κοινής χρήσης",
    "Start sharing": "Έναρξη κοινής χρήσης",
    "Refreshing…": "Ανανέωση…",
    "Open in Google Maps": "Άνοιγμα στο Google Maps",
    "Updated": "Ενημερώθηκε",
    "No one is sharing location right now.": "Κανείς δεν μοιράζεται τοποθεσία αυτή τη στιγμή.",
    "Tip: Keep this page open while sharing. Your position updates automatically.": "Συμβουλή: Κράτα αυτή τη σελίδα ανοιχτή όσο μοιράζεσαι. Η θέση σου ενημερώνεται αυτόματα.",
    "Sharing": "Κοινή χρήση",
    "Not sharing": "Χωρίς κοινή χρήση",
    "Requesting permission…": "Ζητείται άδεια…",
    "Geolocation not supported.": "Η γεωτοποθέτηση δεν υποστηρίζεται.",
    "Location unavailable.": "Η τοποθεσία δεν είναι διαθέσιμη.",
    "Geolocation requires HTTPS to request permission.": "Η γεωτοποθέτηση απαιτεί HTTPS για να ζητηθεί άδεια.",
    "Geolocation not supported.": "Η γεωτοποθέτηση δεν υποστηρίζεται.",
    "GIF": "GIF",

    "Admin": "Διαχείριση",
    "? Help": "Βοήθεια",
    "My Profile": "Το προφίλ μου",
    "Logout": "Αποσύνδεση",
    "Login": "Σύνδεση",
    "Request Access": "Αίτηση πρόσβασης",
    "Toggle theme": "Εναλλαγή θέματος",
    "Search": "Αναζήτηση",
    "Save": "Αποθήκευση",
    "Cancel": "Ακύρωση",
    "Delete": "Διαγραφή",
    "Edit": "Επεξεργασία",
    "Upload": "Μεταφόρτωση",
    "Download": "Λήψη",
    "Send": "Αποστολή",
    "Back": "Πίσω",
    "Home": "Αρχική",
    "Settings": "Ρυθμίσεις",
    "Username": "Όνομα χρήστη",
    "Password": "Κωδικός",
    "Confirm password": "Επιβεβαίωση κωδικού",
    "Email": "Ηλ. ταχυδρομείο",
    "Submit": "Υποβολή",
    "Create": "Δημιουργία",
    "Update": "Ενημέρωση",
    "New": "Νέο",
    "Yes": "Ναι",
    "No": "Όχι",

    # Pages / headings (best-effort)
    "ButSystem Helper": "Βοηθός ButSystem",
    "Dashboard": "Πίνακας",
    "Profile": "Προφίλ",
    "Messages": "Μηνύματα",
    "Members": "Μέλη",
    "Online": "Σε σύνδεση",
    "Offline": "Εκτός σύνδεσης",
    "File Vault": "Θησαυροφυλάκιο αρχείων",
    "Title": "Τίτλος",
    "Message": "Μήνυμα",
    "Description": "Περιγραφή",
    "Status": "Κατάσταση",
    "Open": "Ανοιχτό",
    "Closed": "Κλειστό",
    "Resolved": "Επιλύθηκε",

    # Auth
    "Sign up": "Εγγραφή",
    "Create account": "Δημιουργία λογαριασμού",
    "Remember me": "Να με θυμάσαι",
    "Forgot password?": "Ξέχασες τον κωδικό;",
    "Open chat": "Άνοιγμα συνομιλίας",
    "Type a message": "Γράψε μήνυμα",
    "Record": "Εγγραφή",
    "Stop": "Σταμάτημα",
    "Play": "Αναπαραγωγή",
    "Pause": "Παύση",
    "Copy": "Αντιγραφή",
    "Copied": "Αντιγράφηκε",
    "View": "Προβολή",
    "Reply": "Απάντηση",
    "Close": "Κλείσιμο",
    "Friends": "Φίλοι",
    "Pending": "Σε αναμονή",
    "Approved": "Εγκρίθηκε",
    "Denied": "Απορρίφθηκε",
    "Priority": "Προτεραιότητα",
    "Low": "Χαμηλή",
    "Medium": "Μεσαία",
    "High": "Υψηλή",
    "All fields required.": "Απαιτούνται όλα τα πεδία.",
    "Invalid credentials.": "Λάθος στοιχεία σύνδεσης.",
    "Passwords do not match.": "Οι κωδικοί δεν ταιριάζουν.",
    "Logged out.": "Έγινε αποσύνδεση.",
    "Profile updated.": "Το προφίλ ενημερώθηκε.",
    "Password changed.": "Ο κωδικός άλλαξε.",
    "Wrong current password.": "Λάθος τρέχων κωδικός.",
    "No file selected.": "Δεν επιλέχθηκε αρχείο.",
    "Upload failed.": "Η μεταφόρτωση απέτυχε.",
    "Uploaded.": "Μεταφορτώθηκε.",
    "Folder created.": "Ο φάκελος δημιουργήθηκε.",
    "Folder deleted.": "Ο φάκελος διαγράφηκε.",
    "Folder already exists.": "Ο φάκελος υπάρχει ήδη.",
    "Could not create folder.": "Δεν ήταν δυνατή η δημιουργία φακέλου.",
    "File deleted.": "Το αρχείο διαγράφηκε.",
    "Download failed.": "Η λήψη απέτυχε.",
    "Delete failed.": "Η διαγραφή απέτυχε.",
    "Saved.": "Αποθηκεύτηκε.",
    "Updated.": "Ενημερώθηκε.",
    "Created.": "Δημιουργήθηκε.",
    "Ticket created.": "Το αίτημα δημιουργήθηκε.",
    "Ticket closed.": "Το αίτημα έκλεισε.",
    "Reply sent.": "Η απάντηση στάλθηκε.",
    "Member added.": "Το μέλος προστέθηκε.",
    "Member removed.": "Το μέλος αφαιρέθηκε.",
    "Group created.": "Η ομάδα δημιουργήθηκε.",
    "Group deleted.": "Η ομάδα διαγράφηκε.",
    "Group name required.": "Απαιτείται όνομα ομάδας.",
    "Left group.": "Αποχώρησες από την ομάδα.",
    "You were signed out by admin.": "Έγινες αποσυνδεδεμένος/η από τον διαχειριστή.",
    "Not found.": "Δεν βρέθηκε.",
    "Invalid path.": "Μη έγκυρη διαδρομή.",
    "Invalid action.": "Μη έγκυρη ενέργεια.",
    "Cannot delete the last admin.": "Δεν μπορείς να διαγράψεις τον τελευταίο διαχειριστή.",
    "Cannot remove owner.": "Δεν μπορείς να αφαιρέσεις τον ιδιοκτήτη.",
    "Admin removed.": "Ο διαχειριστής αφαιρέθηκε.",
    "User already exists.": "Το όνομα χρήστη υπάρχει ήδη.",
    "Request submitted. Waiting for admin approval.": "Η αίτηση υποβλήθηκε. Αναμονή για έγκριση διαχειριστή.",
    "User approved.": "Ο χρήστης εγκρίθηκε.",
    "User denied.": "Ο χρήστης απορρίφθηκε.",
    "Deleted.": "Διαγράφηκε.",

    # Settings / security
    "Profiler": "Profiler",
    "People": "Άτομα",
    "Online now": "Σε σύνδεση τώρα",
    "Offline now": "Εκτός σύνδεσης τώρα",
    "Account security": "Ασφάλεια λογαριασμού",
    "Change password": "Αλλαγή κωδικού",
    "Current password": "Τρέχων κωδικός",
    "New password": "Νέος κωδικός",
    "Confirm new password": "Επιβεβαίωση νέου κωδικού",
    "2-factor authentication (security questions)": "Έλεγχος ταυτότητας 2 παραγόντων (ερωτήσεις ασφαλείας)",
    "Not as strong as an authenticator app, but it adds an extra step after your password.": "Δεν είναι τόσο ισχυρό όσο μια εφαρμογή ελέγχου ταυτότητας, αλλά προσθέτει ένα επιπλέον βήμα μετά τον κωδικό σας.",
    "Question 1": "Ερώτηση 1",
    "Answer 1": "Απάντηση 1",
    "Question 2": "Ερώτηση 2",
    "Answer 2": "Απάντηση 2",
    "Question 3": "Ερώτηση 3",
    "Answer 3": "Απάντηση 3",
    "e.g. What was your first pet's name?": "π.χ. Πώς λεγόταν το πρώτο σας κατοικίδιο;",
    "e.g. City you were born in?": "π.χ. Σε ποια πόλη γεννηθήκατε;",
    "e.g. Favorite teacher's last name?": "π.χ. Το επίθετο του αγαπημένου σας δασκάλου;",
    "Leave blank to keep existing answer": "Άφησε κενό για να κρατήσεις την υπάρχουσα απάντηση",
    "Enable 2FA on login": "Ενεργοποίηση 2FA κατά τη σύνδεση",
    "Password recovery uses these same questions at": "Η ανάκτηση κωδικού χρησιμοποιεί τις ίδιες ερωτήσεις στο",

    # Calls
    "Ready": "Έτοιμο",
    "Collapse/Expand": "Σύμπτυξη/Επέκταση",
    "Join Call": "Σύνδεση στην κλήση",
    "Join": "Σύνδεση",
    "Mute": "Σίγαση",
    "Mute / Unmute": "Σίγαση / Άρση σίγασης",
    "Camera": "Κάμερα",
    "Camera On / Off": "Κάμερα ενεργή / ανενεργή",
    "Switch Camera": "Εναλλαγή κάμερας",
    "Overlay": "Επικάλυψη",
    "Overlay call": "Επικάλυψη κλήσης",
    "Cam": "Κάμερα",
    "Flip": "Αλλαγή",
    "All": "Όλα",
    "Hide": "Απόκρυψη",
    "Hide cameras": "Απόκρυψη καμερών",
    "Hide cameras (keep audio)": "Απόκρυψη καμερών (με ήχο)",
    "Leave Call": "Τερματισμός κλήσης",
    "Leave": "Έξοδος",

    # Profile / Profiler
    "Actions": "Ενέργειες",
    "Add attachment": "Προσθήκη συνημμένου",
    "Add attachment (optional)": "Προσθήκη συνημμένου (προαιρετικό)",
    "Address": "Διεύθυνση",
    "Address (optional)": "Διεύθυνση (προαιρετικό)",
    "Attachments": "Συνημμένα",
    "Attachments (optional)": "Συνημμένα (προαιρετικό)",
    "Attachments are stored (not encrypted).": "Τα συνημμένα αποθηκεύονται (όχι κρυπτογραφημένα).",
    "Attachments stored inside Profiler.": "Τα συνημμένα αποθηκεύονται μέσα στο Profiler.",
    "Bio": "Βιογραφικό",
    "Car Model": "Μοντέλο αυτοκινήτου",
    "Car Model (optional)": "Μοντέλο αυτοκινήτου (προαιρετικό)",
    "City": "Πόλη",
    "Close Friends (up to 10) (optional)": "Κοντινοί φίλοι (έως 10) (προαιρετικό)",
    "Close Friends (up to 10, one per line)": "Κοντινοί φίλοι (έως 10, ένας ανά γραμμή)",
    "Close Friends:": "Κοντινοί φίλοι:",
    "Combine Profiles": "Συγχώνευση προφίλ",
    "Country": "Χώρα",
    "Country (optional)": "Χώρα (προαιρετικό)",
    "Create profile": "Δημιουργία προφίλ",
    "Create/search encrypted profiles (first/last/info + encrypted attachments).": "Δημιουργία/αναζήτηση κρυπτογραφημένων προφίλ (όνομα/επώνυμο/πληροφορίες + κρυπτογραφημένα συνημμένα).",
    "Delete attachment?": "Να διαγραφεί το συνημμένο;",
    "Edit Profile": "Επεξεργασία προφίλ",
    "Email (optional)": "Ηλ. ταχυδρομείο (προαιρετικό)",
    "English": "Αγγλικά",
    "Greek": "Ελληνικά",
    "Export Profiles": "Εξαγωγή προφίλ",
    "Eye Color": "Χρώμα ματιών",
    "Eye Color (optional)": "Χρώμα ματιών (προαιρετικό)",
    "Family Members (up to 10) (optional)": "Μέλη οικογένειας (έως 10) (προαιρετικό)",
    "Family Members (up to 10, one per line)": "Μέλη οικογένειας (έως 10, ένας ανά γραμμή)",
    "Family Members:": "Μέλη οικογένειας:",
    "First Name": "Όνομα",
    "Go": "Μετάβαση",
    "Hair Color": "Χρώμα μαλλιών",
    "Hair Color (optional)": "Χρώμα μαλλιών (προαιρετικό)",
    "Height": "Ύψος",
    "Height (cm) (optional)": "Ύψος (εκ.) (προαιρετικό)",
    "ID": "Αναγνωριστικό",
    "ID Number": "Αριθμός ταυτότητας",
    "ID Number (optional)": "Αριθμός ταυτότητας (προαιρετικό)",
    "Information": "Πληροφορίες",
    "Job": "Επάγγελμα",
    "Job (optional)": "Επάγγελμα (προαιρετικό)",
    "Last Name": "Επώνυμο",
    "License Plate": "Πινακίδα",
    "License Plate (optional)": "Πινακίδα (προαιρετικό)",
    "Links": "Σύνδεσμοι",
    "Links (one per line, must start with http:// or https:// or mailto:)": "Σύνδεσμοι (ένας ανά γραμμή, πρέπει να ξεκινά με http:// ή https:// ή mailto:)",
    "Name": "Όνομα",
    "Nickname": "Ψευδώνυμο",
    "Nickname is what others will see. Username stays the same.": "Το ψευδώνυμο είναι αυτό που θα βλέπουν οι άλλοι. Το όνομα χρήστη παραμένει ίδιο.",
    "No attachments.": "Δεν υπάρχουν συνημμένα.",
    "No entries yet.": "Δεν υπάρχουν εγγραφές ακόμη.",
    "No pic": "Χωρίς φωτογραφία",
    "No picture set yet.": "Δεν έχει οριστεί φωτογραφία ακόμη.",
    "One per line": "Ένα ανά γραμμή",
    "Optional details": "Προαιρετικές λεπτομέρειες",
    "Phone Number": "Τηλέφωνο",
    "Phone Number (optional)": "Τηλέφωνο (προαιρετικό)",
    "Profile Picture": "Φωτογραφία προφίλ",
    "Profile picture": "Φωτογραφία προφίλ",
    "Profiler • View": "Profiler • Προβολή",
    "Remove picture": "Αφαίρεση εικόνας",
    "Remove profile picture?": "Να αφαιρεθεί η φωτογραφία προφίλ;",
    "Save (encrypted)": "Αποθήκευση (κρυπτογραφημένα)",
    "Save changes": "Αποθήκευση αλλαγών",
    "Save profile changes": "Αποθήκευση αλλαγών προφίλ",
    "Search (decrypts your entries to match)": "Αναζήτηση (αποκρυπτογραφεί τις εγγραφές για αντιστοίχιση)",
    "Search is done locally in the app by decrypting your entries (still stored encrypted).": "Η αναζήτηση γίνεται τοπικά στην εφαρμογή με αποκρυπτογράφηση των εγγραφών (παραμένουν αποθηκευμένες κρυπτογραφημένες).",
    "State": "Περιφέρεια",
    "State (optional)": "Περιφέρεια (προαιρετικό)",
    "Tax Number": "ΑΦΜ",
    "Tip: one name per line (only first 10 saved).": "Συμβουλή: ένα όνομα ανά γραμμή (αποθηκεύονται μόνο τα πρώτα 10).",
    "Town": "Κωμόπολη",
    "Town (optional)": "Κωμόπολη (προαιρετικό)",
    "Upload picture (jpg/png/webp)": "Μεταφόρτωση εικόνας (jpg/png/webp)",
    "Visible to logged-in users.": "Ορατό σε συνδεδεμένους χρήστες.",
    "Weight": "Βάρος",
    "Weight (kg) (optional)": "Βάρος (κιλά) (προαιρετικό)",
    "Your profile data is stored locally in ButSystem.": "Τα δεδομένα του προφίλ σου αποθηκεύονται τοπικά στο ButSystem.",
    "e.g. 180 cm": "π.χ. 180 εκ.",
    "e.g. 75 kg": "π.χ. 75 κιλά",
    "Ελληνικά": "Ελληνικά",
    "⬆️ Optional": "⬆️ Προαιρετικό",
    "⬇️ Optional": "⬇️ Προαιρετικό",

    # Helper / Privacy
    ": Create groups, add members, and chat with multiple people.": ": Δημιούργησε ομάδες, πρόσθεσε μέλη και συζήτησε με πολλούς χρήστες.",
    ": Send text, voice, GIFs, and files. The chat updates live without reloading.": ": Στείλε κείμενο, φωνή, GIF και αρχεία. Η συνομιλία ενημερώνεται ζωντανά χωρίς ανανέωση.",
    ": Set a nickname, bio, links, and a profile picture. Optional fields are hidden until you expand them.": ": Όρισε ψευδώνυμο, βιογραφικό, συνδέσμους και φωτογραφία προφίλ. Τα προαιρετικά πεδία κρύβονται μέχρι να τα ανοίξεις.",
    ": Share your live location (opt-in). You can stop sharing anytime.": ": Μοιράσου τη ζωντανή τοποθεσία σου (προαιρετικό). Μπορείς να σταματήσεις οποιαδήποτε στιγμή.",
    ": Tap a user to open a DM. Online users appear first; use search to find anyone fast.": ": Πάτησε έναν χρήστη για να ανοίξεις DM. Οι online χρήστες εμφανίζονται πρώτοι· χρησιμοποίησε αναζήτηση για να βρεις γρήγορα όποιον θέλεις.",
    ": The call button shows only when chatting with someone else (not with yourself).": ": Το κουμπί κλήσης εμφανίζεται μόνο όταν μιλάς με άλλον χρήστη (όχι με τον εαυτό σου).",
    ": Upload and organize your private files/folders.": ": Ανέβασε και οργάνωσε τα ιδιωτικά σου αρχεία/φακέλους.",
    ": Use": ": Χρησιμοποίησε",
    "Calls": "Κλήσεις",
    "Files/voice": "Αρχεία/φωνή",
    "How to use ButSystem": "Πώς να χρησιμοποιήσεις το ButSystem",
    "Logs:": "Καταγραφές:",
    "Privacy notes": "Σημειώσεις απορρήτου",
    "Search & Notifications": "Αναζήτηση & Ειδοποιήσεις",
    "Text messages": "Μηνύματα κειμένου",
    "are encrypted at rest.": "είναι κρυπτογραφημένα κατά την αποθήκευση.",
    "are stored on your device (not encrypted) for speed and compatibility.": "αποθηκεύονται στη συσκευή σου (χωρίς κρυπτογράφηση) για ταχύτητα και συμβατότητα.",
    "logo": "λογότυπο",
    "pfp": "φωτογραφία προφίλ",
    "to create an account, then an admin approves it.": "για να δημιουργήσεις λογαριασμό και μετά ένας διαχειριστής τον εγκρίνει.",

    # More helper/profile strings
    ": Change password, manage security questions (2FA), and customize accent color + font.": ": Άλλαξε κωδικό, διαχειρίσου ερωτήσεις ασφαλείας (2FA) και προσαρμόσε χρώμα έμφασης + γραμματοσειρά.",
    "ButSystem runs on your device. Everything you do stays in your local ButSystem folder (unless you share a link).": "Το ButSystem τρέχει στη συσκευή σου. Ό,τι κάνεις μένει στον τοπικό φάκελο ButSystem (εκτός αν μοιραστείς έναν σύνδεσμο).",
    "Delete this profile entry?": "Να διαγραφεί αυτή η εγγραφή προφίλ;",
    "Login / Request Access": "Σύνδεση / Αίτημα πρόσβασης",

    "Message...": "Μήνυμα...",
    "Send file": "Αποστολή αρχείου",
    "GIFs": "GIF",
    "Send voice message": "Αποστολή φωνητικού",
    "Search GIFs...": "Αναζήτηση GIF...",
    "No results.": "Κανένα αποτέλεσμα.",
    "GIF search failed.": "Αποτυχία αναζήτησης GIF.",
    "Voice upload failed.": "Αποτυχία αποστολής φωνής.",
    "Recorded ✓ uploading…": "Ηχογραφήθηκε ✓ αποστολή…",
    "Recording… tap again to stop": "Ηχογράφηση… πάτα ξανά για διακοπή",
    "Recording not supported here. Choose an audio file.": "Η ηχογράφηση δεν υποστηρίζεται εδώ. Διάλεξε αρχείο ήχου.",
    "Mic blocked / not available.": "Μικρόφωνο μπλοκαρισμένο / μη διαθέσιμο.",
}

# Build reverse (Greek -> English) map for best-effort translation back to English.
# If duplicates exist, we keep the first encountered English key.
TRANSLATIONS_EN = {}
for _en, _el in TRANSLATIONS_EL.items():
    TRANSLATIONS_EN.setdefault(_el, _en)


# Extra UI strings found in templates (best-effort) to improve coverage.
TRANSLATIONS_EL.update({
    ": create encrypted entries with optional encrypted attachments.": ": \u03b4\u03b7\u03bc\u03b9\u03bf\u03cd\u03c1\u03b3\u03b7\u03c3\u03b5 \u03ba\u03c1\u03c5\u03c0\u03c4\u03bf\u03b3\u03c1\u03b1\u03c6\u03b7\u03bc\u03ad\u03bd\u03b5\u03c2 \u03ba\u03b1\u03c4\u03b1\u03c7\u03c9\u03c1\u03ae\u03c3\u03b5\u03b9\u03c2 \u03bc\u03b5 \u03c0\u03c1\u03bf\u03b1\u03b9\u03c1\u03b5\u03c4\u03b9\u03ba\u03ac \u03ba\u03c1\u03c5\u03c0\u03c4\u03bf\u03b3\u03c1\u03b1\u03c6\u03b7\u03bc\u03ad\u03bd\u03b1 \u03c3\u03c5\u03bd\u03b7\u03bc\u03bc\u03ad\u03bd\u03b1.",
    ": online users appear first. Search usernames as you type.": ": \u03bf\u03b9 \u03c7\u03c1\u03ae\u03c3\u03c4\u03b5\u03c2 \u03c3\u03b5 \u03c3\u03cd\u03bd\u03b4\u03b5\u03c3\u03b7 \u03b5\u03bc\u03c6\u03b1\u03bd\u03af\u03b6\u03bf\u03bd\u03c4\u03b1\u03b9 \u03c0\u03c1\u03ce\u03c4\u03bf\u03b9. \u0391\u03bd\u03b1\u03b6\u03ae\u03c4\u03b7\u03c3\u03b5 \u03bf\u03bd\u03cc\u03bc\u03b1\u03c4\u03b1 \u03c7\u03c1\u03b7\u03c3\u03c4\u03ce\u03bd \u03ba\u03b1\u03b8\u03ce\u03c2 \u03c0\u03bb\u03b7\u03ba\u03c4\u03c1\u03bf\u03bb\u03bf\u03b3\u03b5\u03af\u03c2.",
    ": opening a chat marks received messages as read.": ": \u03b1\u03bd\u03bf\u03af\u03b3\u03bf\u03bd\u03c4\u03b1\u03c2 \u03bc\u03b9\u03b1 \u03c3\u03c5\u03bd\u03bf\u03bc\u03b9\u03bb\u03af\u03b1 \u03c3\u03b7\u03bc\u03b5\u03b9\u03ce\u03bd\u03b5\u03b9\u03c2 \u03c4\u03b1 \u03bb\u03b7\u03c6\u03b8\u03ad\u03bd\u03c4\u03b1 \u03bc\u03b7\u03bd\u03cd\u03bc\u03b1\u03c4\u03b1 \u03c9\u03c2 \u03b1\u03bd\u03b1\u03b3\u03bd\u03c9\u03c3\u03bc\u03ad\u03bd\u03b1.",
    ": record inside the chat composer.": ": \u03ba\u03ac\u03bd\u03b5 \u03b5\u03b3\u03b3\u03c1\u03b1\u03c6\u03ae \u03bc\u03ad\u03c3\u03b1 \u03b1\u03c0\u03cc \u03c4\u03bf \u03c0\u03bb\u03b1\u03af\u03c3\u03b9\u03bf \u03c3\u03cd\u03bd\u03c4\u03b1\u03be\u03b7\u03c2 \u03c4\u03b7\u03c2 \u03c3\u03c5\u03bd\u03bf\u03bc\u03b9\u03bb\u03af\u03b1\u03c2.",
    "Actions": "\u0395\u03bd\u03ad\u03c1\u03b3\u03b5\u03b9\u03b5\u03c2",
    "Add": "\u03a0\u03c1\u03bf\u03c3\u03b8\u03ae\u03ba\u03b7",
    "Add attachment (optional)": "\u03a0\u03c1\u03bf\u03c3\u03b8\u03ae\u03ba\u03b7 \u03c3\u03c5\u03bd\u03b7\u03bc\u03bc\u03ad\u03bd\u03bf\u03c5 (\u03c0\u03c1\u03bf\u03b1\u03b9\u03c1\u03b5\u03c4\u03b9\u03ba\u03ac)",
    "Add member": "\u03a0\u03c1\u03bf\u03c3\u03b8\u03ae\u03ba\u03b7 \u03bc\u03ad\u03bb\u03bf\u03c5\u03c2",
    "Admin-only actions. Use carefully.": "\u0395\u03bd\u03ad\u03c1\u03b3\u03b5\u03b9\u03b5\u03c2 \u03bc\u03cc\u03bd\u03bf \u03b3\u03b9\u03b1 \u03b4\u03b9\u03b1\u03c7\u03b5\u03b9\u03c1\u03b9\u03c3\u03c4\u03ad\u03c2. \u03a7\u03c1\u03b7\u03c3\u03b9\u03bc\u03bf\u03c0\u03bf\u03af\u03b7\u03c3\u03b5 \u03bc\u03b5 \u03c0\u03c1\u03bf\u03c3\u03bf\u03c7\u03ae.",
    "Admins": "\u0394\u03b9\u03b1\u03c7\u03b5\u03b9\u03c1\u03b9\u03c3\u03c4\u03ad\u03c2",
    "Apply": "\u0395\u03c6\u03b1\u03c1\u03bc\u03bf\u03b3\u03ae",
    "Asc": "\u0391\u03cd\u03be.",
    "Attachments": "\u03a3\u03c5\u03bd\u03b7\u03bc\u03bc\u03ad\u03bd\u03b1",
    "Attachments (optional)": "\u03a3\u03c5\u03bd\u03b7\u03bc\u03bc\u03ad\u03bd\u03b1 (\u03c0\u03c1\u03bf\u03b1\u03b9\u03c1\u03b5\u03c4\u03b9\u03ba\u03ac)",
    "Attachments are stored (not encrypted).": "\u03a4\u03b1 \u03c3\u03c5\u03bd\u03b7\u03bc\u03bc\u03ad\u03bd\u03b1 \u03b5\u03af\u03bd\u03b1\u03b9 .",
    "Back to Admin": "\u03a0\u03af\u03c3\u03c9 \u03c3\u03c4\u03b7 \u03b4\u03b9\u03b1\u03c7\u03b5\u03af\u03c1\u03b9\u03c3\u03b7",
    "Bio": "\u0392\u03b9\u03bf\u03b3\u03c1\u03b1\u03c6\u03b9\u03ba\u03cc",
    "ButSystem": "ButSystem",
    "Chat groups with admins.": "\u039f\u03bc\u03b1\u03b4\u03b9\u03ba\u03ad\u03c2 \u03c3\u03c5\u03bd\u03bf\u03bc\u03b9\u03bb\u03af\u03b5\u03c2 \u03bc\u03b5 \u03b4\u03b9\u03b1\u03c7\u03b5\u03b9\u03c1\u03b9\u03c3\u03c4\u03ad\u03c2.",
    "Choose file": "\u0395\u03c0\u03b9\u03bb\u03bf\u03b3\u03ae \u03b1\u03c1\u03c7\u03b5\u03af\u03bf\u03c5",
    "Choose how you want to enter.": "\u0394\u03b9\u03ac\u03bb\u03b5\u03be\u03b5 \u03c0\u03ce\u03c2 \u03b8\u03ad\u03bb\u03b5\u03b9\u03c2 \u03bd\u03b1 \u03bc\u03c0\u03b5\u03b9\u03c2.",
    "City": "\u03a0\u03cc\u03bb\u03b7",
    "Combine Profiles": "\u03a3\u03c5\u03bd\u03b4\u03c5\u03b1\u03c3\u03bc\u03cc\u03c2 \u03c0\u03c1\u03bf\u03c6\u03af\u03bb",
    "Confirm username": "\u0395\u03c0\u03b9\u03b2\u03b5\u03b2\u03b1\u03af\u03c9\u03c3\u03b7 \u03bf\u03bd\u03cc\u03bc\u03b1\u03c4\u03bf\u03c2 \u03c7\u03c1\u03ae\u03c3\u03c4\u03b7",
    "Confirm username and password twice.": "\u0395\u03c0\u03b9\u03b2\u03b5\u03b2\u03b1\u03af\u03c9\u03c3\u03b5 \u03cc\u03bd\u03bf\u03bc\u03b1 \u03c7\u03c1\u03ae\u03c3\u03c4\u03b7 \u03ba\u03b1\u03b9 \u03ba\u03c9\u03b4\u03b9\u03ba\u03cc \u03b4\u03cd\u03bf \u03c6\u03bf\u03c1\u03ad\u03c2.",
    "Copy Link": "\u0391\u03bd\u03c4\u03b9\u03b3\u03c1\u03b1\u03c6\u03ae \u03c3\u03c5\u03bd\u03b4\u03ad\u03c3\u03bc\u03bf\u03c5",
    "Country": "\u03a7\u03ce\u03c1\u03b1",
    "Create group": "\u0394\u03b7\u03bc\u03b9\u03bf\u03c5\u03c1\u03b3\u03af\u03b1 \u03bf\u03bc\u03ac\u03b4\u03b1\u03c2",
    "Create profile": "\u0394\u03b7\u03bc\u03b9\u03bf\u03c5\u03c1\u03b3\u03af\u03b1 \u03c0\u03c1\u03bf\u03c6\u03af\u03bb",
    "Create/search encrypted profiles (first/last/info + encrypted attachments).": "\u0394\u03b7\u03bc\u03b9\u03bf\u03c5\u03c1\u03b3\u03af\u03b1/\u03b1\u03bd\u03b1\u03b6\u03ae\u03c4\u03b7\u03c3\u03b7 \u03ba\u03c1\u03c5\u03c0\u03c4\u03bf\u03b3\u03c1\u03b1\u03c6\u03b7\u03bc\u03ad\u03bd\u03c9\u03bd \u03c0\u03c1\u03bf\u03c6\u03af\u03bb (\u03cc\u03bd\u03bf\u03bc\u03b1/\u03b5\u03c0\u03ce\u03bd\u03c5\u03bc\u03bf/\u03c0\u03bb\u03b7\u03c1\u03bf\u03c6\u03bf\u03c1\u03af\u03b5\u03c2 + \u03ba\u03c1\u03c5\u03c0\u03c4\u03bf\u03b3\u03c1\u03b1\u03c6\u03b7\u03bc\u03ad\u03bd\u03b1 \u03c3\u03c5\u03bd\u03b7\u03bc\u03bc\u03ad\u03bd\u03b1).",
    "Created": "\u0394\u03b7\u03bc\u03b9\u03bf\u03c5\u03c1\u03b3\u03ae\u03b8\u03b7\u03ba\u03b5",
    "Danger zone": "\u0396\u03ce\u03bd\u03b7 \u03ba\u03b9\u03bd\u03b4\u03cd\u03bd\u03bf\u03c5",
    "Delete ButSystem (self\u2011destruct)": "\u0394\u03b9\u03b1\u03b3\u03c1\u03b1\u03c6\u03ae ButSystem (\u03b1\u03c5\u03c4\u03bf\u03ba\u03b1\u03c4\u03b1\u03c3\u03c4\u03c1\u03bf\u03c6\u03ae)",
    "Delete my account": "\u0394\u03b9\u03b1\u03b3\u03c1\u03b1\u03c6\u03ae \u03c4\u03bf\u03c5 \u03bb\u03bf\u03b3\u03b1\u03c1\u03b9\u03b1\u03c3\u03bc\u03bf\u03cd \u03bc\u03bf\u03c5",
    "Delete my admin account": "\u0394\u03b9\u03b1\u03b3\u03c1\u03b1\u03c6\u03ae \u03c4\u03bf\u03c5 \u03bb\u03bf\u03b3\u03b1\u03c1\u03b9\u03b1\u03c3\u03bc\u03bf\u03cd \u03b4\u03b9\u03b1\u03c7\u03b5\u03b9\u03c1\u03b9\u03c3\u03c4\u03ae \u03bc\u03bf\u03c5",
    "Demote": "\u03a5\u03c0\u03bf\u03b2\u03b9\u03b2\u03b1\u03c3\u03bc\u03cc\u03c2",
    "Desc": "\u03a6\u03b8\u03af\u03bd.",
    "Duration (seconds, for video/audio)": "\u0394\u03b9\u03ac\u03c1\u03ba\u03b5\u03b9\u03b1 (\u03b4\u03b5\u03c5\u03c4\u03b5\u03c1\u03cc\u03bb\u03b5\u03c0\u03c4\u03b1, \u03b3\u03b9\u03b1 \u03b2\u03af\u03bd\u03c4\u03b5\u03bf/\u03ae\u03c7\u03bf)",
    "Empty folder.": "\u039a\u03b5\u03bd\u03cc\u03c2 \u03c6\u03ac\u03ba\u03b5\u03bb\u03bf\u03c2.",
    "Encrypted": "\u039a\u03c1\u03c5\u03c0\u03c4\u03bf\u03b3\u03c1\u03b1\u03c6\u03b7\u03bc\u03ad\u03bd\u03bf",
    "Enter": "\u0395\u03af\u03c3\u03bf\u03b4\u03bf\u03c2",
    "Existing users only.": "\u039c\u03cc\u03bd\u03bf \u03b3\u03b9\u03b1 \u03c5\u03c0\u03ac\u03c1\u03c7\u03bf\u03bd\u03c4\u03b5\u03c2 \u03c7\u03c1\u03ae\u03c3\u03c4\u03b5\u03c2.",
    "Export Profiles": "\u0395\u03be\u03b1\u03b3\u03c9\u03b3\u03ae \u03c0\u03c1\u03bf\u03c6\u03af\u03bb",
    "Eye Color": "\u03a7\u03c1\u03ce\u03bc\u03b1 \u03bc\u03b1\u03c4\u03b9\u03ce\u03bd",
    "First Name": "\u038c\u03bd\u03bf\u03bc\u03b1",
    "Folder name": "\u038c\u03bd\u03bf\u03bc\u03b1 \u03c6\u03b1\u03ba\u03ad\u03bb\u03bf\u03c5",
    "For existing users.": "\u0393\u03b9\u03b1 \u03c5\u03c0\u03ac\u03c1\u03c7\u03bf\u03bd\u03c4\u03b5\u03c2 \u03c7\u03c1\u03ae\u03c3\u03c4\u03b5\u03c2.",
    "Generate Link": "\u0394\u03b7\u03bc\u03b9\u03bf\u03c5\u03c1\u03b3\u03af\u03b1 \u03c3\u03c5\u03bd\u03b4\u03ad\u03c3\u03bc\u03bf\u03c5",
    "Go": "\u039c\u03b5\u03c4\u03ac\u03b2\u03b1\u03c3\u03b7",
    "Group name": "\u038c\u03bd\u03bf\u03bc\u03b1 \u03bf\u03bc\u03ac\u03b4\u03b1\u03c2",
    "Group text + voice are .": "\u03a4\u03bf \u03ba\u03b5\u03af\u03bc\u03b5\u03bd\u03bf \u03ba\u03b1\u03b9 \u03b7 \u03c6\u03c9\u03bd\u03ae \u03c4\u03b7\u03c2 \u03bf\u03bc\u03ac\u03b4\u03b1\u03c2 \u03b5\u03af\u03bd\u03b1\u03b9 .",
    "Hair Color": "\u03a7\u03c1\u03ce\u03bc\u03b1 \u03bc\u03b1\u03bb\u03bb\u03b9\u03ce\u03bd",
    "Height": "\u038e\u03c8\u03bf\u03c2",
    "ID": "\u03a4\u03b1\u03c5\u03c4\u03cc\u03c4\u03b7\u03c4\u03b1",
    "ID Number": "\u0391\u03c1\u03b9\u03b8\u03bc\u03cc\u03c2 \u03c4\u03b1\u03c5\u03c4\u03cc\u03c4\u03b7\u03c4\u03b1\u03c2",
    "Info": "\u03a0\u03bb\u03b7\u03c1\u03bf\u03c6\u03bf\u03c1\u03af\u03b5\u03c2",
    "Information": "\u03a0\u03bb\u03b7\u03c1\u03bf\u03c6\u03bf\u03c1\u03af\u03b5\u03c2",
    "Kick": "\u0391\u03c0\u03bf\u03b2\u03bf\u03bb\u03ae",
    "Last Name": "\u0395\u03c0\u03ce\u03bd\u03c5\u03bc\u03bf",
    "Leave": "\u0391\u03c0\u03bf\u03c7\u03ce\u03c1\u03b7\u03c3\u03b7",
    "License Plate": "\u03a0\u03b9\u03bd\u03b1\u03ba\u03af\u03b4\u03b1 \u03ba\u03c5\u03ba\u03bb\u03bf\u03c6\u03bf\u03c1\u03af\u03b1\u03c2",
    "Links (one per line, must start with http:// or https:// or mailto:)": "\u03a3\u03cd\u03bd\u03b4\u03b5\u03c3\u03bc\u03bf\u03b9 (\u03ad\u03bd\u03b1\u03c2 \u03b1\u03bd\u03ac \u03b3\u03c1\u03b1\u03bc\u03bc\u03ae, \u03c0\u03c1\u03ad\u03c0\u03b5\u03b9 \u03bd\u03b1 \u03be\u03b5\u03ba\u03b9\u03bd\u03ac \u03bc\u03b5 http:// \u03ae https:// \u03ae mailto:)",
    "Logs:": "\u039a\u03b1\u03c4\u03b1\u03b3\u03c1\u03b1\u03c6\u03ad\u03c2:",
    "Make admin": "\u039a\u03ac\u03bd\u03b5 \u03b4\u03b9\u03b1\u03c7\u03b5\u03b9\u03c1\u03b9\u03c3\u03c4\u03ae",
    "Members (comma separated usernames)": "\u039c\u03ad\u03bb\u03b7 (\u03bf\u03bd\u03cc\u03bc\u03b1\u03c4\u03b1 \u03c7\u03c1\u03b7\u03c3\u03c4\u03ce\u03bd, \u03c7\u03c9\u03c1\u03b9\u03c3\u03bc\u03ad\u03bd\u03b1 \u03bc\u03b5 \u03ba\u03cc\u03bc\u03bc\u03b1)",
    "Members/Admins": "\u039c\u03ad\u03bb\u03b7/\u0394\u03b9\u03b1\u03c7\u03b5\u03b9\u03c1\u03b9\u03c3\u03c4\u03ad\u03c2",
    "Modified": "\u03a4\u03c1\u03bf\u03c0\u03bf\u03c0\u03bf\u03b9\u03ae\u03b8\u03b7\u03ba\u03b5",
    "Name": "\u038c\u03bd\u03bf\u03bc\u03b1",
    "Need access? Use": "\u03a7\u03c1\u03b5\u03b9\u03ac\u03b6\u03b5\u03c3\u03b1\u03b9 \u03c0\u03c1\u03cc\u03c3\u03b2\u03b1\u03c3\u03b7; \u03a7\u03c1\u03b7\u03c3\u03b9\u03bc\u03bf\u03c0\u03bf\u03af\u03b7\u03c3\u03b5",
    "New account requests require admin approval.": "\u03a4\u03b1 \u03b1\u03b9\u03c4\u03ae\u03bc\u03b1\u03c4\u03b1 \u03bd\u03ad\u03bf\u03c5 \u03bb\u03bf\u03b3\u03b1\u03c1\u03b9\u03b1\u03c3\u03bc\u03bf\u03cd \u03b1\u03c0\u03b1\u03b9\u03c4\u03bf\u03cd\u03bd \u03ad\u03b3\u03ba\u03c1\u03b9\u03c3\u03b7 \u03b4\u03b9\u03b1\u03c7\u03b5\u03b9\u03c1\u03b9\u03c3\u03c4\u03ae.",
    "New folder": "\u039d\u03ad\u03bf\u03c2 \u03c6\u03ac\u03ba\u03b5\u03bb\u03bf\u03c2",
    "Nickname": "\u03a0\u03b1\u03c1\u03b1\u03c4\u03c3\u03bf\u03cd\u03ba\u03bb\u03b9",
    "Nickname is what others will see. Username stays the same.": "\u03a4\u03bf \u03c0\u03b1\u03c1\u03b1\u03c4\u03c3\u03bf\u03cd\u03ba\u03bb\u03b9 \u03b5\u03af\u03bd\u03b1\u03b9 \u03b1\u03c5\u03c4\u03cc \u03c0\u03bf\u03c5 \u03b8\u03b1 \u03b2\u03bb\u03ad\u03c0\u03bf\u03c5\u03bd \u03bf\u03b9 \u03ac\u03bb\u03bb\u03bf\u03b9. \u03a4\u03bf \u03cc\u03bd\u03bf\u03bc\u03b1 \u03c7\u03c1\u03ae\u03c3\u03c4\u03b7 \u03bc\u03ad\u03bd\u03b5\u03b9 \u03af\u03b4\u03b9\u03bf.",
    "No attachments.": "\u0394\u03b5\u03bd \u03c5\u03c0\u03ac\u03c1\u03c7\u03bf\u03c5\u03bd \u03c3\u03c5\u03bd\u03b7\u03bc\u03bc\u03ad\u03bd\u03b1.",
    "No entries yet.": "\u0394\u03b5\u03bd \u03c5\u03c0\u03ac\u03c1\u03c7\u03bf\u03c5\u03bd \u03ba\u03b1\u03c4\u03b1\u03c7\u03c9\u03c1\u03ae\u03c3\u03b5\u03b9\u03c2 \u03b1\u03ba\u03cc\u03bc\u03b1.",
    "No picture set yet.": "\u0394\u03b5\u03bd \u03ad\u03c7\u03b5\u03b9 \u03bf\u03c1\u03b9\u03c3\u03c4\u03b5\u03af \u03b5\u03b9\u03ba\u03cc\u03bd\u03b1 \u03b1\u03ba\u03cc\u03bc\u03b1.",
    "One-time use \u2022 Expires in 30 minutes": "\u039c\u03af\u03b1\u03c2 \u03c7\u03c1\u03ae\u03c3\u03b7\u03c2 \u2022 \u039b\u03ae\u03b3\u03b5\u03b9 \u03c3\u03b5 30 \u03bb\u03b5\u03c0\u03c4\u03ac",
    "Only the owner can change admin roles.": "\u039c\u03cc\u03bd\u03bf \u03bf \u03b9\u03b4\u03b9\u03bf\u03ba\u03c4\u03ae\u03c4\u03b7\u03c2 \u03bc\u03c0\u03bf\u03c1\u03b5\u03af \u03bd\u03b1 \u03b1\u03bb\u03bb\u03ac\u03be\u03b5\u03b9 \u03c1\u03cc\u03bb\u03bf\u03c5\u03c2 \u03b4\u03b9\u03b1\u03c7\u03b5\u03b9\u03c1\u03b9\u03c3\u03c4\u03ae.",
    "Optional details": "\u03a0\u03c1\u03bf\u03b1\u03b9\u03c1\u03b5\u03c4\u03b9\u03ba\u03ad\u03c2 \u03bb\u03b5\u03c0\u03c4\u03bf\u03bc\u03ad\u03c1\u03b5\u03b9\u03b5\u03c2",
    "Path: /": "\u0394\u03b9\u03b1\u03b4\u03c1\u03bf\u03bc\u03ae: /",
    "Phone Number": "\u03a4\u03b7\u03bb\u03ad\u03c6\u03c9\u03bd\u03bf",
    "Preview": "\u03a0\u03c1\u03bf\u03b5\u03c0\u03b9\u03c3\u03ba\u03cc\u03c0\u03b7\u03c3\u03b7",
    "Profile Picture": "\u0395\u03b9\u03ba\u03cc\u03bd\u03b1 \u03c0\u03c1\u03bf\u03c6\u03af\u03bb",
    "Profiler Entry #": "\u039a\u03b1\u03c4\u03b1\u03c7\u03ce\u03c1\u03b7\u03c3\u03b7 \u03a0\u03c1\u03bf\u03c6\u03af\u03bb #",
    "Promote": "\u03a0\u03c1\u03bf\u03b1\u03b3\u03c9\u03b3\u03ae",
    "Quick tips": "\u0393\u03c1\u03ae\u03b3\u03bf\u03c1\u03b5\u03c2 \u03c3\u03c5\u03bc\u03b2\u03bf\u03c5\u03bb\u03ad\u03c2",
    "Remove": "\u0391\u03c6\u03b1\u03af\u03c1\u03b5\u03c3\u03b7",
    "Remove admin": "\u0391\u03c6\u03b1\u03af\u03c1\u03b5\u03c3\u03b7 \u03b4\u03b9\u03b1\u03c7\u03b5\u03b9\u03c1\u03b9\u03c3\u03c4\u03ae",
    "Remove member": "\u0391\u03c6\u03b1\u03af\u03c1\u03b5\u03c3\u03b7 \u03bc\u03ad\u03bb\u03bf\u03c5\u03c2",
    "Remove picture": "\u0391\u03c6\u03b1\u03af\u03c1\u03b5\u03c3\u03b7 \u03b5\u03b9\u03ba\u03cc\u03bd\u03b1\u03c2",
    "Request access": "\u0391\u03af\u03c4\u03b7\u03c3\u03b7 \u03c0\u03c1\u03cc\u03c3\u03b2\u03b1\u03c3\u03b7\u03c2",
    "Role": "\u03a1\u03cc\u03bb\u03bf\u03c2",
    "Role:": "\u03a1\u03cc\u03bb\u03bf\u03c2:",
    "Save (encrypted)": "\u0391\u03c0\u03bf\u03b8\u03ae\u03ba\u03b5\u03c5\u03c3\u03b7 (\u03ba\u03c1\u03c5\u03c0\u03c4\u03bf\u03b3\u03c1\u03b1\u03c6\u03b7\u03bc\u03ad\u03bd\u03bf)",
    "Save changes": "\u0391\u03c0\u03bf\u03b8\u03ae\u03ba\u03b5\u03c5\u03c3\u03b7 \u03b1\u03bb\u03bb\u03b1\u03b3\u03ce\u03bd",
    "Save profile": "\u0391\u03c0\u03bf\u03b8\u03ae\u03ba\u03b5\u03c5\u03c3\u03b7 \u03c0\u03c1\u03bf\u03c6\u03af\u03bb",
    "Seen": "\u0395\u03b8\u03b5\u03ac\u03b8\u03b7",
    "Self\u2011destruct": "\u0391\u03c5\u03c4\u03bf\u03ba\u03b1\u03c4\u03b1\u03c3\u03c4\u03c1\u03bf\u03c6\u03ae",
    "Send Request": "\u0391\u03c0\u03bf\u03c3\u03c4\u03bf\u03bb\u03ae \u03b1\u03b9\u03c4\u03ae\u03bc\u03b1\u03c4\u03bf\u03c2",
    "Sign In": "\u03a3\u03cd\u03bd\u03b4\u03b5\u03c3\u03b7",
    "Sign in": "\u03a3\u03cd\u03bd\u03b4\u03b5\u03c3\u03b7",
    "Size": "\u039c\u03ad\u03b3\u03b5\u03b8\u03bf\u03c2",
    "Sort: modified": "\u03a4\u03b1\u03be\u03b9\u03bd\u03cc\u03bc\u03b7\u03c3\u03b7: \u03c4\u03c1\u03bf\u03c0\u03bf\u03c0\u03bf\u03af\u03b7\u03c3\u03b7",
    "Sort: name": "\u03a4\u03b1\u03be\u03b9\u03bd\u03cc\u03bc\u03b7\u03c3\u03b7: \u03cc\u03bd\u03bf\u03bc\u03b1",
    "Sort: size": "\u03a4\u03b1\u03be\u03b9\u03bd\u03cc\u03bc\u03b7\u03c3\u03b7: \u03bc\u03ad\u03b3\u03b5\u03b8\u03bf\u03c2",
    "Sort: type": "\u03a4\u03b1\u03be\u03b9\u03bd\u03cc\u03bc\u03b7\u03c3\u03b7: \u03c4\u03cd\u03c0\u03bf\u03c2",
    "State": "\u03a0\u03b5\u03c1\u03b9\u03c6\u03ad\u03c1\u03b5\u03b9\u03b1",
    "Target": "\u03a3\u03c4\u03cc\u03c7\u03bf\u03c2",
    "Tax Number": "\u0391\u03a6\u039c",
    "This removes your login + public profile but does": "\u0391\u03c5\u03c4\u03cc \u03b1\u03c6\u03b1\u03b9\u03c1\u03b5\u03af \u03c4\u03b7 \u03c3\u03cd\u03bd\u03b4\u03b5\u03c3\u03ae \u03c3\u03bf\u03c5 \u03ba\u03b1\u03b9 \u03c4\u03bf \u03b4\u03b7\u03bc\u03cc\u03c3\u03b9\u03bf \u03c0\u03c1\u03bf\u03c6\u03af\u03bb \u03c3\u03bf\u03c5 \u03b1\u03bb\u03bb\u03ac \u03b4\u03b5\u03bd",
    "Timestamp": "\u03a7\u03c1\u03bf\u03bd\u03b9\u03ba\u03ae \u03c3\u03ae\u03bc\u03b1\u03bd\u03c3\u03b7",
    "Type": "\u03a4\u03cd\u03c0\u03bf\u03c2",
    "Up": "\u03a0\u03ac\u03bd\u03c9",
    "Updated": "\u0395\u03bd\u03b7\u03bc\u03b5\u03c1\u03ce\u03b8\u03b7\u03ba\u03b5",
    "Upload": "\u039c\u03b5\u03c4\u03b1\u03c6\u03cc\u03c1\u03c4\u03c9\u03c3\u03b7 (\u03ba\u03c1\u03c5\u03c0\u03c4\u03bf\u03b3\u03c1\u03b1\u03c6\u03b7\u03bc\u03ad\u03bd\u03bf)",
    "Upload picture (jpg/png/webp)": "\u039c\u03b5\u03c4\u03b1\u03c6\u03cc\u03c1\u03c4\u03c9\u03c3\u03b7 \u03b5\u03b9\u03ba\u03cc\u03bd\u03b1\u03c2 (jpg/png/webp)",
    "User": "\u03a7\u03c1\u03ae\u03c3\u03c4\u03b7\u03c2",
    "User Files \u2013 @": "\u0391\u03c1\u03c7\u03b5\u03af\u03b1 \u03c7\u03c1\u03ae\u03c3\u03c4\u03b7 \u2013 @",
    "Vault files are stored after upload.": "\u03a4\u03b1 \u03b1\u03c1\u03c7\u03b5\u03af\u03b1 \u03b8\u03b7\u03c3\u03b1\u03c5\u03c1\u03bf\u03c6\u03c5\u03bb\u03b1\u03ba\u03af\u03bf\u03c5 \u03b5\u03af\u03bd\u03b1\u03b9  \u03bc\u03b5\u03c4\u03ac \u03c4\u03b7 \u03bc\u03b5\u03c4\u03b1\u03c6\u03cc\u03c1\u03c4\u03c9\u03c3\u03b7.",
    "Visible to logged-in users.": "\u039f\u03c1\u03b1\u03c4\u03cc \u03c3\u03b5 \u03c3\u03c5\u03bd\u03b4\u03b5\u03b4\u03b5\u03bc\u03ad\u03bd\u03bf\u03c5\u03c2 \u03c7\u03c1\u03ae\u03c3\u03c4\u03b5\u03c2.",
    "Voice": "\u03a6\u03c9\u03bd\u03ae",
    "Voice (optional)": "\u03a6\u03c9\u03bd\u03ae (\u03c0\u03c1\u03bf\u03b1\u03b9\u03c1\u03b5\u03c4\u03b9\u03ba\u03ac)",
    "Weight": "\u0392\u03ac\u03c1\u03bf\u03c2",
    "You are not in any groups yet.": "\u0394\u03b5\u03bd \u03b5\u03af\u03c3\u03b1\u03b9 \u03c3\u03b5 \u03ba\u03b1\u03bc\u03af\u03b1 \u03bf\u03bc\u03ac\u03b4\u03b1 \u03b1\u03ba\u03cc\u03bc\u03b1.",
    "You become owner. You can promote admins in the group page.": "\u0393\u03af\u03bd\u03b5\u03c3\u03b1\u03b9 \u03b9\u03b4\u03b9\u03bf\u03ba\u03c4\u03ae\u03c4\u03b7\u03c2. \u039c\u03c0\u03bf\u03c1\u03b5\u03af\u03c2 \u03bd\u03b1 \u03c0\u03c1\u03bf\u03ac\u03b3\u03b5\u03b9\u03c2 \u03b4\u03b9\u03b1\u03c7\u03b5\u03b9\u03c1\u03b9\u03c3\u03c4\u03ad\u03c2 \u03c3\u03c4\u03b7 \u03c3\u03b5\u03bb\u03af\u03b4\u03b1 \u03bf\u03bc\u03ac\u03b4\u03b1\u03c2.",
    "Your profile content is .": "\u03a4\u03bf \u03c0\u03b5\u03c1\u03b9\u03b5\u03c7\u03cc\u03bc\u03b5\u03bd\u03bf \u03c4\u03bf\u03c5 \u03c0\u03c1\u03bf\u03c6\u03af\u03bb \u03c3\u03bf\u03c5 \u03b5\u03af\u03bd\u03b1\u03b9 .",
    "Your request is held until the admin approves it in the terminal.": "\u03a4\u03bf \u03b1\u03af\u03c4\u03b7\u03bc\u03ac \u03c3\u03bf\u03c5 \u03c0\u03b1\u03c1\u03b1\u03bc\u03ad\u03bd\u03b5\u03b9 \u03c3\u03b5 \u03b1\u03bd\u03b1\u03bc\u03bf\u03bd\u03ae \u03bc\u03ad\u03c7\u03c1\u03b9 \u03bd\u03b1 \u03c4\u03bf \u03b5\u03b3\u03ba\u03c1\u03af\u03bd\u03b5\u03b9 \u03bf \u03b4\u03b9\u03b1\u03c7\u03b5\u03b9\u03c1\u03b9\u03c3\u03c4\u03ae\u03c2 \u03c3\u03c4\u03bf \u03c4\u03b5\u03c1\u03bc\u03b1\u03c4\u03b9\u03ba\u03cc.",
    "Your role": "\u039f \u03c1\u03cc\u03bb\u03bf\u03c2 \u03c3\u03bf\u03c5",
    "admin": "\u03b4\u03b9\u03b1\u03c7\u03b5\u03b9\u03c1\u03b9\u03c3\u03c4\u03ae\u03c2",
    "and wait for approval.": "\u03ba\u03b1\u03b9 \u03c0\u03b5\u03c1\u03af\u03bc\u03b5\u03bd\u03b5 \u03ad\u03b3\u03ba\u03c1\u03b9\u03c3\u03b7.",
    "delete stored files.": "\u03b4\u03b9\u03b1\u03b3\u03c1\u03ac\u03c6\u03b5\u03b9 \u03c4\u03b1 \u03b1\u03c0\u03bf\u03b8\u03b7\u03ba\u03b5\u03c5\u03bc\u03ad\u03bd\u03b1 \u03b1\u03c1\u03c7\u03b5\u03af\u03b1.",
    "lat:  , lon:": "\u03b3\u03b5\u03c9\u03c0\u03bb.:  , \u03b3\u03b5\u03c9\u03bc\u03ba.:",
    "not": "\u03cc\u03c7\u03b9",
    "stored": "\u03b1\u03c0\u03bf\u03b8\u03b7\u03ba\u03b5\u03c5\u03bc\u03ad\u03bd\u03bf",
    "user": "\u03c7\u03c1\u03ae\u03c3\u03c4\u03b7\u03c2",
    "\u2022 Owner:": "\u2022 \u0399\u03b4\u03b9\u03bf\u03ba\u03c4\u03ae\u03c4\u03b7\u03c2:",
    "\u2022 Voice": "\u2022 \u03a6\u03c9\u03bd\u03ae",
    "\ud83c\udfa4 Audio (10s)": "\ud83c\udfa4 \u0389\u03c7\u03bf\u03c2 (10\u03b4)",
    "\ud83c\udfa5 Video (10s)": "\ud83c\udfa5 \u0392\u03af\u03bd\u03c4\u03b5\u03bf (10\u03b4)",
    "\ud83d\udccd Location": "\ud83d\udccd \u03a4\u03bf\u03c0\u03bf\u03b8\u03b5\u03c3\u03af\u03b1",
    "\ud83d\udcf8 Photo": "\ud83d\udcf8 \u03a6\u03c9\u03c4\u03bf\u03b3\u03c1\u03b1\u03c6\u03af\u03b1",
})

# Profiler optional-field phrases (ensure full, non-mixed Greek in UI)
TRANSLATIONS_EL.update({
    "Optional details": "Προαιρετικές λεπτομέρειες",
    "Optional Details": "Προαιρετικές λεπτομέρειες",
    "Fill anything you want — all optional.": "Συμπληρώστε ό,τι θέλετε — όλα είναι Προαιρετικό.",
    "Family Members (up to 10) (optional)": "Μέλη Οικογένειας (έως 10) (Προαιρετικό)",
    "Close Friends (up to 10) (optional)": "Κοντινοί φίλοι (έως 10) (Προαιρετικό)",
    "One per line": "Ένα ανά γραμμή",
    "Tip: one name per line (only first 10 saved).": "Συμβουλή: ένα όνομα ανά γραμμή (αποθηκεύονται μόνο τα πρώτα 10).",
    "Car Model (optional)": "Μοντέλο Αυτοκινήτου (Προαιρετικό)",
    "Car Model": "Μοντέλο Αυτοκινήτου",
    "(optional)": "(Προαιρετικό)",
    "optional": "Προαιρετικό",
    "Optional": "Προαιρετικό",
})


# Extra coverage for delivery ticks, chat controls, placeholders, and tooltips.
TRANSLATIONS_EL.update({
    "Call": "Κλήση",
    "Sent": "Εστάλη",
    "Delivered": "Παραδόθηκε",
    "Seen": "Διαβάστηκε",
    "Saved messages": "Αποθηκευμένα μηνύματα",
    "Message...": "Μήνυμα...",
    "Search user...": "Αναζήτηση χρήστη...",
    "Search GIFs…": "Αναζήτηση GIF…",
    "Search GIFs...": "Αναζήτηση GIF...",
    "Send file": "Αποστολή αρχείου",
    "Send voice message": "Αποστολή φωνητικού μηνύματος",
    "Message actions": "Ενέργειες μηνύματος",
    "Attach voice": "Επισύναψη φωνής",
    "Connecting…": "Σύνδεση…",
    "Connecting...": "Σύνδεση...",
    "Ended": "Τερματίστηκε",
})


# Extra coverage + fixes (no mixed EN/EL, avoid substring misspellings)
TRANSLATIONS_EL.update({
    # Navbar / core controls
    "Menu": "Μενού",
    "Theme": "Θέμα",
    "Language": "Γλώσσα",
    "Help": "Βοήθεια",

    # Appearance settings
    "Appearance": "Εμφάνιση",
    "Accent color": "Χρώμα έμφασης",
    "Font": "Γραμματοσειρά",
    "Customize accent color and font (saved per account).": "Προσαρμόστε το χρώμα έμφασης και τη γραμματοσειρά (αποθηκεύεται ανά λογαριασμό).",

    # Common screens
    "Entering…": "Είσοδος…",
    "Entering...": "Είσοδος...",

    # Help canvas (base.html)
    "How to use ButSystem": "Πώς να χρησιμοποιείς το ButSystem",
    "ButSystem is preparing your session.": "Το ButSystem προετοιμάζει τη συνεδρία σου.",
    "Please wait — this may take 20–40 seconds.": "Παρακαλώ περίμενε — αυτό μπορεί να πάρει 20–40 δευτερόλεπτα.",
    "Please wait — this may take 10–20 seconds.": "Παρακαλώ περίμενε — αυτό μπορεί να πάρει 10–20 δευτερόλεπτα.",
    "Important notice": "Σημαντική ειδοποίηση",
    "This system is NOT affiliated with police, military, or any government agency.": "Αυτό το σύστημα ΔΕΝ σχετίζεται με αστυνομία, στρατό ή οποιαδήποτε κρατική υπηρεσία.",
    "It is for personal use only.": "Προορίζεται μόνο για προσωπική χρήση.",
    "Only create profiles for people who have given you explicit consent.": "Δημιούργησε προφίλ μόνο για άτομα που σου έχουν δώσει ρητή συγκατάθεση.",
    "Do not use this system for harassment, stalking, or any illegal activity.": "Μην χρησιμοποιείς αυτό το σύστημα για παρενόχληση, παρακολούθηση ή οποιαδήποτε παράνομη δραστηριότητα.",
    "The creators and maintainers are not responsible for misuse.": "Οι δημιουργοί και οι συντηρητές δεν φέρουν ευθύνη για κακή χρήση.",
    "ButSystem runs on your device. Everything you do stays in your local ButSystem folder (unless you share a link).":
        "Το ButSystem τρέχει στη συσκευή σου. Ό,τι κάνεις μένει στον τοπικό φάκελο ButSystem (εκτός αν μοιραστείς έναν σύνδεσμο).",
    "Login / Request Access": "Σύνδεση / Αίτηση πρόσβασης",
    ": Use": ": Χρησιμοποίησε",
    "to create an account, then an admin approves it.": "για να δημιουργήσεις λογαριασμό, και μετά ένας διαχειριστής τον εγκρίνει.",
    ": Tap a user to open a DM. Online users appear first; use search to find anyone fast.":
        ": Πάτα έναν χρήστη για να ανοίξεις ιδιωτική συνομιλία. Οι online χρήστες εμφανίζονται πρώτοι· χρησιμοποίησε την αναζήτηση για να βρεις γρήγορα οποιονδήποτε.",
    ": Send text, voice, GIFs, and files. The chat updates live without reloading.":
        ": Στείλε κείμενο, φωνή, GIF και αρχεία. Η συνομιλία ενημερώνεται ζωντανά χωρίς ανανέωση.",
    ": The call button shows only when chatting with someone else (not with yourself).":
        ": Το κουμπί κλήσης εμφανίζεται μόνο όταν συνομιλείς με κάποιον άλλον (όχι με τον εαυτό σου).",
    ": Create groups, add members, and chat with multiple people.":
        ": Δημιούργησε ομάδες, πρόσθεσε μέλη και μίλα με πολλούς.",
    ": Upload and organize your private files/folders.":
        ": Μεταφόρτωσε και οργάνωσε τα ιδιωτικά σου αρχεία/φακέλους.",
    ": Share your live location (opt-in). You can stop sharing anytime.":
        ": Μοιράσου τη ζωντανή τοποθεσία σου (προαιρετικά). Μπορείς να σταματήσεις την κοινή χρήση οποιαδήποτε στιγμή.",
    ": Set a nickname, bio, links, and a profile picture. Optional fields are hidden until you expand them.":
        ": Όρισε ψευδώνυμο, βιογραφικό, συνδέσμους και φωτογραφία προφίλ. Τα προαιρετικά πεδία κρύβονται μέχρι να τα ανοίξεις.",
    ": Change password, manage security questions (2FA), and customize accent color + font.":
        ": Άλλαξε κωδικό, διαχειρίσου τις ερωτήσεις ασφαλείας (2FA) και προσαρμόσε το χρώμα έμφασης + γραμματοσειρά.",
    ": Use search boxes to jump to users quickly; unread badges show new messages.":
        ": Χρησιμοποίησε τα πεδία αναζήτησης για γρήγορη μετάβαση σε χρήστες· τα σήματα μη αναγνωσμένων δείχνουν νέα μηνύματα.",
    "Privacy notes": "Σημειώσεις απορρήτου",
    "Text messages": "Μηνύματα κειμένου",
    "Files/voice": "Αρχεία/φωνή",
    "are encrypted at rest.": "είναι κρυπτογραφημένα σε κατάσταση αποθήκευσης.",
    "are stored on your device (not encrypted) for speed and compatibility.":
        "αποθηκεύονται στη συσκευή σου (χωρίς κρυπτογράφηση) για ταχύτητα και συμβατότητα.",
    "entries are stored encrypted; optional data can be expanded/collapsed.":
        "οι καταχωρήσεις αποθηκεύονται κρυπτογραφημένες· τα προαιρετικά δεδομένα μπορούν να εμφανιστούν/κρυφτούν.",
    "Logs:": "Αρχεία καταγραφής:",

    # Security / auth
    "2FA check": "Έλεγχος 2 παραγόντων",
    "Password recovery": "Ανάκτηση κωδικού",
    "Reset password": "Επαναφορά κωδικού",
    "Recover your account using your security questions.": "Ανάκτησε τον λογαριασμό σου χρησιμοποιώντας τις ερωτήσεις ασφαλείας.",

    # File + upload UI messages
    "Upload failed. Please retry.": "Η μεταφόρτωση απέτυχε. Παρακαλώ δοκιμάστε ξανά.",
    "Done. Refreshing…": "Ολοκληρώθηκε. Ανανέωση…",
    "Upload failed. Please choose an audio file.": "Η μεταφόρτωση απέτυχε. Παρακαλώ επιλέξτε ένα αρχείο ήχου.",
    "Recording… tap again to stop": "Εγγραφή… πατήστε ξανά για διακοπή",
    "Recording not supported here. Choose an audio file.": "Η εγγραφή δεν υποστηρίζεται εδώ. Επιλέξτε ένα αρχείο ήχου.",
    "Uploading…": "Μεταφόρτωση…",
    "Verify": "Επαλήθευση",
    "Refresh failed.": "Η ανανέωση απέτυχε.",

    # Message action labels
    "✏️ Edit message": "✏️ Επεξεργασία μηνύματος",
    "🗑️ Delete": "🗑️ Διαγραφή",
    "⬇️ Optional": "⬇️ Προαιρετικό",
    "(edited)": "(επεξεργασμένο)",

    # Fixes for previously incomplete/mixed translations
    "Attachments are stored (not encrypted).": "Τα συνημμένα αποθηκεύονται (δεν είναι κρυπτογραφημένα).",
    "Vault files are stored after upload.": "Τα αρχεία του θησαυροφυλακίου αποθηκεύονται μετά τη μεταφόρτωση.",
    "Your profile content is .": "Το περιεχόμενο του προφίλ σου είναι κρυπτογραφημένο.",
    "Group text + voice are .": "Το κείμενο και η φωνή της ομάδας είναι κρυπτογραφημένα.",
    "Group text + voice are encrypted at rest.": "Το κείμενο και η φωνή της ομάδας είναι κρυπτογραφημένα σε κατάσταση αποθήκευσης.",

    # Avoid English-only labels in Greek UI
    "Email": "Ηλ. ταχυδρομείο",
    "Profiler": "Profiler",
        
    # Chats page
    "Type to search users (username or nickname)": "Πληκτρολόγησε για αναζήτηση χρηστών (όνομα χρήστη ή ψευδώνυμο)",

    # Landing / welcome tip
    "Tip: Camera/mic features (if used) may require HTTPS — use the Cloudflared link.": "Συμβουλή: Οι λειτουργίες κάμερας/μικροφώνου (αν χρησιμοποιηθούν) μπορεί να απαιτούν HTTPS — χρησιμοποίησε τον σύνδεσμο Cloudflared.",

    # Profiler (feature) - make sure everything is fully translated
    "Create/search encrypted profiles (first/last/info + encrypted attachments).": "Δημιούργησε/αναζήτησε κρυπτογραφημένα προφίλ (όνομα/επώνυμο/πληροφορίες + κρυπτογραφημένα συνημμένα).",
    "Search (decrypts your entries to match)": "Αναζήτηση (αποκρυπτογραφεί τις καταχωρήσεις σου για αντιστοίχιση)",
    "Search is done locally in the app by decrypting your entries (still stored encrypted).": "Η αναζήτηση γίνεται τοπικά στην εφαρμογή, αποκρυπτογραφώντας τις καταχωρήσεις σου (παραμένουν αποθηκευμένες κρυπτογραφημένες).",
    "Go": "Μετάβαση",
    "Profiler Entry #": "Καταχώρηση Profiler #",
    " • Owner: ": " • Ιδιοκτήτης: ",
    "Profiler • View": "Profiler • Προβολή",
    "Entry #": "Καταχώρηση #",
    "Updated ": "Ενημερώθηκε ",
    "Address (optional)": "Διεύθυνση (προαιρετικό)",
    "Phone Number (optional)": "Αριθμός τηλεφώνου (προαιρετικό)",
    "Email (optional)": "Ηλ. ταχυδρομείο (προαιρετικό)",
    "ID Number (optional)": "Αριθμός ταυτότητας (προαιρετικό)",
    "License Plate (optional)": "Πινακίδα κυκλοφορίας (προαιρετικό)",
    "Car Model (optional)": "Μοντέλο αυτοκινήτου (προαιρετικό)",
    "Job (optional)": "Επάγγελμα (προαιρετικό)",
    "Town (optional)": "Πόλη/Χωριό (προαιρετικό)",
    "State (optional)": "Πολιτεία/Νομός (προαιρετικό)",
    "Country (optional)": "Χώρα (προαιρετικό)",
    "Height (cm) (optional)": "Ύψος (εκ.) (προαιρετικό)",
    "Weight (kg) (optional)": "Βάρος (κιλά) (προαιρετικό)",
    "Hair Color (optional)": "Χρώμα μαλλιών (προαιρετικό)",
    "Eye Color (optional)": "Χρώμα ματιών (προαιρετικό)",
    "Family Members (up to 10) (optional)": "Μέλη οικογένειας (έως 10) (προαιρετικό)",
    "Close Friends (up to 10) (optional)": "Κοντινοί φίλοι (έως 10) (προαιρετικό)",
    "Tip: one name per line (only first 10 saved).": "Συμβουλή: ένα όνομα ανά γραμμή (αποθηκεύονται μόνο τα πρώτα 10).",
    "Attachments stored inside Profiler.": "Τα συνημμένα αποθηκεύονται μέσα στο Profiler.",
    "Family Members:": "Μέλη οικογένειας:",
    "Close Friends:": "Κοντινοί φίλοι:",
"Open in Google Maps": "Άνοιγμα στους Χάρτες Google",
})



# Expanded Helper content
TRANSLATIONS_EL.update({
    "Close": "Κλείσιμο",
    "This guide explains every button and icon you see in the app.": "Αυτός ο οδηγός εξηγεί κάθε κουμπί και εικονίδιο που βλέπεις στην εφαρμογή.",
    "Top bar": "Επάνω μπάρα",
    "Switch between dark and light.": "Εναλλαγή μεταξύ σκοτεινού και φωτεινού.",
    "Switch the interface language.": "Αλλαγή γλώσσας διεπαφής.",
    "Open the menu to navigate to all pages.": "Άνοιξε το μενού για να μεταβείς σε όλες τις σελίδες.",
    "Chats list": "Λίστα συνομιλιών",
    "Your private notes to yourself.": "Οι ιδιωτικές σημειώσεις σου προς τον εαυτό σου.",
    "User status.": "Κατάσταση χρήστη.",
    "Type a username or nickname to filter the list.": "Πληκτρολόγησε όνομα χρήστη ή ψευδώνυμο για φιλτράρισμα της λίστας.",
    "Tap a user to open a DM.": "Πάτησε έναν χρήστη για να ανοίξεις ιδιωτική συνομιλία.",
    "Chat screen": "Οθόνη συνομιλίας",
    "Start an audio call.": "Ξεκίνα κλήση ήχου.",
    "Start a video call.": "Ξεκίνα βιντεοκλήση.",
    "Send the message.": "Στείλε το μήνυμα.",
    "Attach file": "Επισύναψη αρχείου",
    "Send a file in chat.": "Στείλε ένα αρχείο στη συνομιλία.",
    "Send an animated GIF.": "Στείλε ένα κινούμενο GIF.",
    "Voice message": "Φωνητικό μήνυμα",
    "Record a voice message (tap again to stop).": "Κατέγραψε φωνητικό μήνυμα (πάτησε ξανά για να σταματήσει).",
    "Edit message": "Επεξεργασία μηνύματος",
    "Edit your own message when available.": "Επεξεργάσου το δικό σου μήνυμα όταν είναι διαθέσιμο.",
    "Delete your own message.": "Διέγραψε το δικό σου μήνυμα.",
    "Sent / Delivered / Seen": "Απεστάλη / Παραδόθηκε / Διαβάστηκε",
    "Delivery status.": "Κατάσταση παράδοσης.",
    "Call controls": "Χειριστήρια κλήσης",
    "Join the call.": "Συνδέσου στην κλήση.",
    "Mute/unmute your microphone.": "Σίγαση/ενεργοποίηση μικροφώνου.",
    "Turn camera on/off.": "Άνοιγμα/κλείσιμο κάμερας.",
    "Switch front/back camera.": "Εναλλαγή μπροστινής/πίσω κάμερας.",
    "Overlay call view.": "Επικάλυψη προβολής κλήσης.",
    "Hide/show cameras (keep audio).": "Απόκρυψη/εμφάνιση καμερών (ο ήχος συνεχίζει).",
    "Leave the call.": "Αποχώρηση από την κλήση.",
    "Create group chats and manage members.": "Δημιούργησε ομαδικές συνομιλίες και διαχειρίσου μέλη.",
    "Folder": "Φάκελος",
    "File": "Αρχείο",
    "Open a folder.": "Άνοιξε έναν φάκελο.",
    "Download or open a file.": "Κατέβασε ή άνοιξε ένα αρχείο.",
    "Share your location with others. You can stop anytime.": "Μοιράσου την τοποθεσία σου με άλλους. Μπορείς να σταματήσεις οποιαδήποτε στιγμή.",
    "Update the list of people who are sharing.": "Ενημέρωσε τη λίστα των ατόμων που μοιράζονται τοποθεσία.",
    "Optional fields": "Προαιρετικά πεδία",
    "Show or hide optional fields.": "Εμφάνισε ή κρύψε τα προαιρετικά πεδία.",
    "Update your nickname, bio, links, and picture.": "Ενημέρωσε ψευδώνυμο, βιογραφικό, συνδέσμους και φωτογραφία.",
    "Create an encrypted Profiler entry.": "Δημιούργησε μια κρυπτογραφημένη καταχώρηση Profiler.",
    "Download all Profiler entries as an export file.": "Κατέβασε όλες τις καταχωρήσεις Profiler ως αρχείο εξαγωγής.",
    "Merge imported Profiler data into your local Profiler.": "Συγχώνευσε τα εισαγόμενα δεδομένα Profiler στο τοπικό σου Profiler.",
    "Search is done locally by decrypting entries in memory (still stored encrypted).": "Η αναζήτηση γίνεται τοπικά, αποκρυπτογραφώντας τις καταχωρήσεις στη μνήμη (παραμένουν αποθηκευμένες κρυπτογραφημένες).",
    "Settings & Security": "Ρυθμίσεις & Ασφάλεια",
    "Change password, security questions (2FA), accent color, and font.": "Άλλαξε κωδικό, ερωτήσεις ασφαλείας (2FA), χρώμα έμφασης και γραμματοσειρά.",
    "Approve accounts and manage users.": "Έγκρινε λογαριασμούς και διαχειρίσου χρήστες.",
    "Admin options are visible only to admins.": "Οι επιλογές διαχείρισης είναι ορατές μόνο στους διαχειριστές.",
})

TRANSLATIONS_EL.update({
    "Reports": "Αναφορές",
    "Discussion": "Συζήτηση",
    "Public room (text).": "Δημόσια αίθουσα (κείμενο).",
    "Report title, subject and text are required.": "Απαιτούνται τίτλος αναφοράς, θέμα και κείμενο.",
    "All report fields are required.": "Όλα τα πεδία αναφοράς είναι υποχρεωτικά.",
    "Message required.": "Απαιτείται μήνυμα.",
    "Please wait 5 seconds before sending another discussion message.": "Περίμενε 5 δευτερόλεπτα πριν στείλεις άλλο μήνυμα συζήτησης.",
    "Report created.": "Η αναφορά δημιουργήθηκε.",
    "Report updated.": "Η αναφορά ενημερώθηκε.",
    "Report deleted.": "Η αναφορά διαγράφηκε.",
    "Not allowed.": "Δεν επιτρέπεται.",
    "Title, subject and text are required.": "Απαιτούνται τίτλος, θέμα και κείμενο.",
    "Create report": "Δημιουργία αναφοράς",
    "Search reports...": "Αναζήτηση αναφορών...",
    "Search discussion...": "Αναζήτηση συζήτησης...",
    "Write to everyone...": "Γράψε σε όλους...",
    "Cooldown: 5 seconds per user (text only, no call features).": "Χρονικό όριο: 5 δευτερόλεπτα ανά χρήστη (μόνο κείμενο, χωρίς κλήσεις).",
    "No messages yet.": "Δεν υπάρχουν μηνύματα ακόμη.",
    "Attachment": "Συνημμένο",
    "Edit report": "Επεξεργασία αναφοράς",
    "Save edit": "Αποθήκευση αλλαγών",
    "Delete report": "Διαγραφή αναφοράς",
    "Delete report?": "Διαγραφή αναφοράς;",
    "No reports found.": "Δεν βρέθηκαν αναφορές.",
    "By": "Από",
    "Text": "Κείμενο",
    "Search groups...": "Αναζήτηση ομάδων..."
})

# Keep reverse map in sync for EL -> EN toggling
for _en, _el in TRANSLATIONS_EL.items():
    TRANSLATIONS_EN.setdefault(_el, _en)

# --- Fallback word-level translation (best-effort) ----------------------------
# This helps cover stray UI strings that weren't explicitly listed in TRANSLATIONS_EL.
# We keep it conservative and only apply it to plain text nodes (between > and <),
# not inside scripts/styles/attributes.

_WORD_MAP_EL = {
    "Theme": "Θέμα",
    "Language": "Γλώσσα",
    "Back": "Πίσω",
    "Home": "Αρχική",
    "Settings": "Ρυθμίσεις",
    "Search": "Αναζήτηση",
    "Save": "Αποθήκευση",
    "Cancel": "Ακύρωση",
    "Delete": "Διαγραφή",
    "Edit": "Επεξεργασία",
    "Upload": "Μεταφόρτωση",
    "Download": "Λήψη",
    "Send": "Αποστολή",
    "Open": "Άνοιγμα",
    "Close": "Κλείσιμο",
    "Friends": "Φίλοι",
    "Yes": "Ναι",
    "No": "Όχι",
    "Name": "Όνομα",
    "Type": "Τύπος",
    "Created": "Δημιουργήθηκε",
    "Status": "Κατάσταση",
    "Message": "Μήνυμα",
    "Subject": "Θέμα",
    "People": "Άτομα",
    "Online": "Σε σύνδεση",
    "Offline": "Εκτός σύνδεσης",
    "Now": "Τώρα",
    "Confirm": "Επιβεβαίωση",
    "Username": "Όνομα χρήστη",
    "Password": "Κωδικός",
    "Sign": "Σύνδεση",
    "In": "Είσοδος",
    "Request": "Αίτηση",
    "Access": "Πρόσβαση",
    "Profile": "Προφίλ",
    "Picture": "Εικόνα",
    "Remove": "Αφαίρεση",
    "Optional": "Προαιρετικό",
    "optional": "Προαιρετικό",
    "Details": "Λεπτομέρειες",
    "First": "Όνομα",
    "Last": "Επώνυμο",
    "Phone": "Τηλέφωνο",
    "Number": "Αριθμός",
    "City": "Πόλη",
    "State": "Νομός",
    "Country": "Χώρα",
    "Bio": "Βιογραφικό",
    "Nickname": "Ψευδώνυμο",
    "Open chats": "Ανοιχτές συνομιλίες",
    "Saved messages": "Αποθηκευμένα μηνύματα",
    "Pinned": "Καρφιτσωμένο",
    "Quick tips": "Γρήγορες συμβουλές",
    "Choose how you want to enter.": "Επιλέξτε πώς θέλετε να μπείτε.",
    "For existing users.": "Για υπάρχοντες χρήστες.",
    "Existing users only.": "Μόνο για υπάρχοντες χρήστες.",
    "New account requests require admin approval.": "Οι νέες αιτήσεις λογαριασμού απαιτούν έγκριση διαχειριστή.",
    "Confirm username": "Επιβεβαίωση ονόματος χρήστη",
    "Confirm username and password twice.": "Επιβεβαιώστε όνομα χρήστη και κωδικό δύο φορές.",
    "Send Request": "Αποστολή αίτησης",
    "Save profile": "Αποθήκευση προφίλ",
    "Profile Picture": "Φωτογραφία προφίλ",
    "Visible to logged-in users.": "Ορατό σε συνδεδεμένους χρήστες.",
    "Thank you. You may close this page.": "Ευχαριστούμε. Μπορείτε να κλείσετε αυτή τη σελίδα.",
    # --- Profiler / optional fields (full Greek translations) ---
    "Fill anything you want — all optional.": "Συμπληρώστε ό,τι θέλετε — όλα είναι προαιρετικά.",
    "Phone Number (optional)": "Τηλέφωνο (Προαιρετικό)",
    "Email (optional)": "Ηλ. ταχυδρομείο (Προαιρετικό)",
    "Car Model (optional)": "Μοντέλο Αυτοκινήτου (Προαιρετικό)",
    "License Plate (optional)": "Πινακίδα κυκλοφορίας (Προαιρετικό)",
    "ID Number (optional)": "Αριθμός ταυτότητας (Προαιρετικό)",
    "Height (cm) (optional)": "Ύψος (cm) (Προαιρετικό)",
    "Weight (kg) (optional)": "Βάρος (kg) (Προαιρετικό)",
    "Eye Color (optional)": "Χρώμα ματιών (Προαιρετικό)",
    "Hair Color (optional)": "Χρώμα μαλλιών (Προαιρετικό)",
    "Job (optional)": "Επάγγελμα (Προαιρετικό)",
    "Country (optional)": "Χώρα (Προαιρετικό)",
    "State (optional)": "Περιφέρεια (Προαιρετικό)",
    "Town (optional)": "Κωμόπολη/Πόλη (Προαιρετικό)",
    "Address (optional)": "Διεύθυνση (Προαιρετικό)",
    "Address": "Διεύθυνση",
    "Family Members (up to 10) (optional)": "Μέλη Οικογένειας (έως 10) (Προαιρετικό)",
    "Family Members": "Μέλη Οικογένειας",
    "Close Friends (up to 10) (optional)": "Κοντινοί φίλοι (έως 10) (Προαιρετικό)",
    "Close Friends": "Κοντινοί φίλοι",
    "Tip: one name per line (only first 10 saved).": "Συμβουλή: ένα όνομα ανά γραμμή (αποθηκεύονται μόνο τα πρώτα 10).",
    "One per line": "Ένα ανά γραμμή",
    "Delete this entry?": "Διαγραφή αυτής της καταχώρησης;",
    "Delete attachment?": "Διαγραφή συνημμένου;",
    "Car Model": "Μοντέλο Αυτοκινήτου",
    "Job": "Επάγγελμα",
    "Town": "Κωμόπολη/Πόλη",
    "Family Members (up to 10, one per line)": "Μέλη Οικογένειας (έως 10, ένα ανά γραμμή)",
    "Close Friends (up to 10, one per line)": "Κοντινοί φίλοι (έως 10, ένα ανά γραμμή)",

}

# Reverse map for the fallback translator (Greek -> English)
_WORD_MAP_EN = {v: k for k, v in _WORD_MAP_EL.items()}

_WORD_RE = re.compile(r"\b([A-Za-z][A-Za-z0-9']*)\b")

def _word_translate(s: str, mapping: dict) -> str:
    """_word_translate.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    s: Parameter.
    mapping: Parameter.

Returns:
    Varies.
"""
    def repl(m):
        """repl.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    m: Parameter.

Returns:
    Varies.
"""
        w = m.group(1)
        return mapping.get(w, w)
    return _WORD_RE.sub(repl, s)


_SIMPLE_WORD_EN_RE = re.compile(r"^[A-Za-z0-9]+$")
_SIMPLE_WORD_UNI_RE = re.compile(r"^[\w]+$", re.UNICODE)

_EL_PHRASE_KEYS: List[str] = []
_EN_PHRASE_KEYS: List[str] = []
_EL_WORD_RE = None
_EN_WORD_RE = None

def _compile_safe_phrase_maps():
    """Compile safe replacement helpers to avoid substring misspellings (e.g., Add -> Address)."""
    global _EL_PHRASE_KEYS, _EN_PHRASE_KEYS, _EL_WORD_RE, _EN_WORD_RE

    # English -> Greek
    el_word_keys = [k for k in TRANSLATIONS_EL.keys() if _SIMPLE_WORD_EN_RE.fullmatch(k or "")]
    el_phrase_keys = [k for k in TRANSLATIONS_EL.keys() if k not in el_word_keys]
    _EL_PHRASE_KEYS = sorted(el_phrase_keys, key=len, reverse=True)
    if el_word_keys:
        _EL_WORD_RE = re.compile(r"\b(" + "|".join(sorted(map(re.escape, el_word_keys), key=len, reverse=True)) + r")\b")
    else:
        _EL_WORD_RE = None

    # Greek -> English (reverse)
    en_word_keys = [k for k in TRANSLATIONS_EN.keys() if _SIMPLE_WORD_UNI_RE.fullmatch(k or "")]
    en_phrase_keys = [k for k in TRANSLATIONS_EN.keys() if k not in en_word_keys]
    _EN_PHRASE_KEYS = sorted(en_phrase_keys, key=len, reverse=True)
    if en_word_keys:
        _EN_WORD_RE = re.compile(r"\b(" + "|".join(sorted(map(re.escape, en_word_keys), key=len, reverse=True)) + r")\b", re.UNICODE)
    else:
        _EN_WORD_RE = None

def _apply_phrase_map(out: str, lang: str) -> str:
    """Apply phrase + word-key replacements safely, then the fallback word-map."""
    if lang == "el":
        for k in _EL_PHRASE_KEYS:
            out = out.replace(k, TRANSLATIONS_EL[k])
        if _EL_WORD_RE:
            out = _EL_WORD_RE.sub(lambda m: TRANSLATIONS_EL.get(m.group(1), m.group(1)), out)
        out = _word_translate(out, _WORD_MAP_EL)
        return out

    for k in _EN_PHRASE_KEYS:
        out = out.replace(k, TRANSLATIONS_EN[k])
    if _EN_WORD_RE:
        out = _EN_WORD_RE.sub(lambda m: TRANSLATIONS_EN.get(m.group(1), m.group(1)), out)
    out = _word_translate(out, _WORD_MAP_EN)
    return out

TRANSLATIONS_EL.update({
    "Subject": "Θέμα",
    "Report title, subject and text are required.": "Απαιτούνται τίτλος αναφοράς, θέμα και κείμενο.",
    "All report fields are required.": "Όλα τα πεδία αναφοράς είναι υποχρεωτικά."
})
TRANSLATIONS_EN.setdefault("Θέμα", "Subject")

# Compile once after all TRANSLATIONS_EL updates are done.
_compile_safe_phrase_maps()

_TEXT_NODE_RE = re.compile(r">([^<>]+)<")

def _translate_text_nodes(body: str, lang: str) -> str:
    """Translate only visible text nodes between > and < (best-effort).

    Strategy per text node:
      1) Apply explicit phrase replacements (TRANSLATIONS_EL / TRANSLATIONS_EN) sorted by length.
      2) Apply fallback word-level mapping (_WORD_MAP_EL / _WORD_MAP_EN).
    """
    def repl(m):
        """repl.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    m: Parameter.

Returns:
    Varies.
"""
        txt = m.group(1)

        # Skip Jinja placeholders / code-like segments
        if "{{" in txt or "{%" in txt:
            return ">" + txt + "<"
        if any(x in txt for x in ["document.", "function", "=>", "var ", "const "]):
            return ">" + txt + "<"

        out = txt

        if lang == "el":
            # Only bother if it looks like English text
            if any("a" <= ch.lower() <= "z" for ch in out):
                out = _apply_phrase_map(out, "el")
        else:
            # lang == "en"
            if any("\u0370" <= ch <= "\u03FF" for ch in out):
                out = _apply_phrase_map(out, "en")

        return ">" + out + "<"

    return _TEXT_NODE_RE.sub(repl, body)

# --- Attribute translation (title/placeholder/aria-label) ---------------------
# The HTML text-node translator does not touch attributes. That caused mixed EN/EL
# tooltips/placeholders (e.g., delivery ticks) in Greek mode.
_ATTR_RE = re.compile(r'\b(title|aria-label|placeholder|data-bs-original-title|data-bs-title|data-open|data-closed|alt)="([^"]*)"')

def _translate_common_attributes(body: str, lang: str) -> str:
    """Translate common UI attributes in rendered HTML (best-effort).

    We only touch a small, safe set of attributes:
      - title
      - aria-label
      - placeholder

    We intentionally skip values that contain 'ButSystem' to keep
    the brand label unchanged.
    """
    def _attr_repl(m):
        attr = m.group(1)
        val = m.group(2)

        # Skip empty / template-like
        if not val or "{{" in val or "{%" in val:
            return m.group(0)

        # Keep brand label
        if "ButSystem" in val:
            return m.group(0)

        out = val
        if lang == "el":
            if any("a" <= ch.lower() <= "z" for ch in out):
                out = _apply_phrase_map(out, "el")
        else:
            if any("\u0370" <= ch <= "\u03FF" for ch in out):
                out = _apply_phrase_map(out, "en")

        return f'{attr}="{out}"'

    return _ATTR_RE.sub(_attr_repl, body)

# -----------------------------------------------------------------------------

def get_lang() -> str:
    """get_lang.

Internal helper function.

This docstring was added automatically to improve maintainability.

Returns:
    Varies.
"""
    lang = session.get("lang", "en")
    return "el" if lang == "el" else "en"

@app.before_request
def _set_lang_on_g():
    """_set_lang_on_g.

Internal helper function.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    g.lang = get_lang()

@app.context_processor
def _inject_lang():
    """_inject_lang.

Internal helper function.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    return {
        "lang": getattr(g, "lang", "en"),
        "logo_light": LOGO_LIGHT_URL,
        "logo_dark": LOGO_DARK_URL,
        "csrf_token": getattr(g, "csrf_token", csrf_token()),
        "csp_nonce": getattr(g, "csp_nonce", ""),
        "credit_line": CREDIT_LINE if "CREDIT_LINE" in globals() else WATERMARK,
        "ENABLE_CALLS": ENABLE_CALLS,
    }

@app.route("/lang/toggle")
def toggle_language():
    """toggle_language.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    session["lang"] = "el" if get_lang() == "en" else "en"
    return redirect(request.referrer or (url_for("profiler") if is_logged_in() else url_for("index")))

def _(s: str) -> str:
    """Translate a short UI string based on session language."""
    if get_lang() == "el":
        return TRANSLATIONS_EL.get(s, s)
    return s

# Make _() available in all templates (optional direct use).
try:
    app.jinja_env.globals["_"] = _
except Exception:
    pass

@app.after_request
def _translate_html_response(resp):
    """Best-effort UI translation (EN ⇄ EL) applied only to visible text nodes.

    Goals:
      - Avoid breaking attributes/URLs (e.g., logo src) by never doing whole-document replaces.
      - Keep specific labels as requested:
          * Theme button text must stay exactly: 'Theme'
          * Language toggle button shows the target language:
              - English UI -> 'Ελληνικά'
              - Greek UI -> 'English'
    """
    try:
        lang = get_lang()
        if not resp.mimetype or "text/html" not in resp.mimetype:
            return resp

        body = resp.get_data(as_text=True)

        # Protect user-generated message bodies (DM + Group) from translation.
        _msg_store = []
        def _msg_hold(m):
            """_msg_hold.

Internal helper function.

This docstring was expanded to make future maintenance easier.

Args:
    m: Parameter.

Returns:
    Varies.
"""
            _msg_store.append(m.group(2))
            return m.group(1) + f"__MSG_{len(_msg_store)-1}__" + m.group(3)
        body = re.sub(r'(<span\s+class="msg-text"[^>]*>)([\s\S]*?)(</span>)', _msg_hold, body)


        # Protect brand/title/logo + special buttons from translation.
        # We protect by placeholdering the exact rendered text nodes.
        body = body.replace(">Theme<", ">__THEME_BTN__<")
        # Language toggle shows the *target* language:
        #   English UI -> 'Ελληνικά'
        #   Greek UI   -> 'English'
        body = body.replace(">English<", ">__LANG_TARGET_EN__<")
        body = body.replace(">Ελληνικά<", ">__LANG_TARGET_EL__<")
        body = body.replace(">ButSystem<", ">__BRAND__<")

        # Translate only visible text nodes.
        body = _translate_text_nodes(body, lang)
        body = _translate_common_attributes(body, lang)

        # Ensure html lang attribute matches.
        body = re.sub(r'<html\s+lang="[^"]*"', f'<html lang="{lang}"', body, flags=re.I)

        # Restore protected elements.
        body = body.replace(">__THEME_BTN__<", ">Theme<")
        body = body.replace(">__LANG_TARGET_EN__<", ">English<")
        body = body.replace(">__LANG_TARGET_EL__<", ">Ελληνικά<")
        body = body.replace(">__BRAND__<", ">ButSystem<")

        # Restore protected user message bodies (DM + Group) so placeholders never leak to UI.
        try:
            for i, _txt in enumerate(_msg_store):
                body = body.replace(f"__MSG_{i}__", _txt)
        except Exception:
            pass


        resp.set_data(body)
        return resp
    except Exception:
        return resp

def login_required(fn):
    """login_required.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    fn: Parameter.

Returns:
    Varies.
"""
    def wrapper(*args, **kwargs):
        """wrapper.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    *args: Parameter.
    **kwargs: Parameter.

Returns:
    Varies.
"""
        if not is_logged_in():
            return redirect(url_for("login", next=request.path))

        # Kick support: admin can invalidate sessions by setting users.logout_at
        try:
            u = current_user()
            login_at = session.get("login_at")
            if u and login_at:
                conn = db_connect()
                row = conn.execute("SELECT logout_at FROM users WHERE username=?", (u,)).fetchone()
                conn.close()
                if row and row["logout_at"] and row["logout_at"] > login_at:
                    session.pop("u", None)
                    session.pop("login_at", None)
                    flash("You were signed out by admin.")
                    return redirect(url_for("login"))
        except Exception:
            pass

        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper



def privacy_panic_active() -> bool:
    try:
        return float(session.get("privacy_panic_until") or 0) > time.time()
    except Exception:
        return False


@app.route("/privacy/panic", methods=["POST"])
@login_required
def privacy_panic():
    session.pop("privacy_panic_until", None)
    session.modified = True
    try:
        log_user_action("privacy_panic", detail="blur_sensitive_content", username=current_user())
    except Exception:
        pass
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify({"ok": True, "reload": True})
    return redirect(request.referrer or url_for("chats"))


@app.route("/privacy/resume", methods=["POST"])
@login_required
def privacy_resume():
    session.pop("privacy_panic_until", None)
    session.modified = True
    try:
        log_user_action("privacy_resume", detail="show_sensitive_content", username=current_user())
    except Exception:
        pass
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify({"ok": True, "reload": True})
    return redirect(request.referrer or url_for("chats"))

def guess_mime(filename: str) -> str:
    """guess_mime.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    filename: Parameter.

Returns:
    Varies.
"""
    mt, _ = mimetypes.guess_type(filename)
    return mt or "application/octet-stream"

# MIME / inline-preview safety helpers
_DANGEROUS_INLINE_MIMES = {
    "text/html",
    "application/xhtml+xml",
    "text/xml",
    "application/xml",
    "image/svg+xml",
}

_DANGEROUS_INLINE_EXTS = {".html", ".htm", ".xhtml", ".xml", ".svg"}

def is_inline_safe(mime: str, filename: str = "") -> bool:
    """Return True if we should allow inline rendering for this file.

    Rationale: inline-rendering active content (HTML/SVG/XML) on the main app
    origin enables stored XSS via user uploads. We therefore force download for
    risky types while preserving inline previews for common media.
    """
    mime = (mime or "application/octet-stream").lower().strip()
    ext = pathlib.Path(filename or "").suffix.lower()

    if mime in _DANGEROUS_INLINE_MIMES or ext in _DANGEROUS_INLINE_EXTS:
        return False

    if mime.startswith("image/"):
        # SVG handled above
        return True
    if mime.startswith("audio/") or mime.startswith("video/"):
        return True
    if mime in ("application/pdf", "text/plain"):
        return True

    return False

def ensure_profile_row(username: str):
    """ensure_profile_row.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    username: Parameter.

Returns:
    Varies.
"""
    conn = db_connect()
    row = conn.execute("SELECT username FROM profiles WHERE username=?", (username,)).fetchone()
    if not row:
        conn.execute("INSERT INTO profiles(username, updated_at) VALUES(?,?)", (username, now_z()))
        conn.commit()
    conn.close()


PROFILE_EXTRA_MAP = {
    "email": "email_enc",
    "phone": "phone_enc",
    "id_number": "id_number_enc",
    "tax_number": "tax_number_enc",
    "license_plate": "license_plate_enc",
    "car_model": "car_model_enc",
    "job": "job_enc",
    "town": "town_enc",
    "address": "address_enc",
    "family_members": "family_members_enc",
    "close_friends": "close_friends_enc",
    "height": "height_enc",
    "weight": "weight_enc",
    "hair_color": "hair_color_enc",
    "eye_color": "eye_color_enc",
    "city": "city_enc",
    "country": "country_enc",
    "state": "state_enc",
}


def get_profile(username: str) -> Dict[str, object]:
    """get_profile.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    username: Parameter.

Returns:
    Varies.
"""
    ensure_profile_row(username)
    conn = db_connect()
    row = conn.execute("SELECT * FROM profiles WHERE username=?", (username,)).fetchone()
    conn.close()

    prof = {
        "username": username,
        "nickname": username,
        "bio": "",
        "links": [],
        "has_pic": False,
        "pic_mime": None,
        # Optional (encrypted) fields
        "email": "",
        "phone": "",
        "id_number": "",
        "tax_number": "",
        "license_plate": "",
        "car_model": "",
        "job": "",
        "town": "",
        "address": "",
        "family_members": "",
        "close_friends": "",
        "height": "",
        "weight": "",
        "hair_color": "",
        "eye_color": "",
        "city": "",
        "country": "",
        "state": "",
    }
    if not row:
        return prof

    try:
        if row["nickname_enc"]:
            prof["nickname"] = aesgcm_decrypt_text(row["nickname_enc"])
    except Exception:
        pass
    try:
        if row["bio_enc"]:
            prof["bio"] = aesgcm_decrypt_text(row["bio_enc"])
    except Exception:
        pass
    try:
        if row["links_enc"]:
            prof["links"] = json.loads(aesgcm_decrypt_text(row["links_enc"]) or "[]")
    except Exception:
        pass

    # Optional fields (only if columns exist)
    try:
        keys = set(row.keys())
        for k, col in PROFILE_EXTRA_MAP.items():
            if col in keys and row[col]:
                try:
                    prof[k] = aesgcm_decrypt_text(row[col])
                except Exception:
                    pass
    except Exception:
        pass

    try:
        prof["has_pic"] = bool(row["pic_path"] and os.path.exists(row["pic_path"]))
    except Exception:
        prof["has_pic"] = False
    try:
        prof["pic_mime"] = row["pic_mime"]
    except Exception:
        prof["pic_mime"] = None
    return prof


def set_profile(username: str, nickname: str, bio: str, links: List[str], extras: Optional[Dict[str, str]] = None):
    """set_profile.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    username: Parameter.
    nickname: Parameter.
    bio: Parameter.
    links: Parameter.
    extras: Parameter.

Returns:
    Varies.
"""
    ensure_profile_row(username)
    conn = db_connect()

    # Build a safe UPDATE that only touches columns that exist (older DBs)
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(profiles)").fetchall()]
    except Exception:
        cols = []

    set_parts = ["nickname_enc=?", "bio_enc=?", "links_enc=?"]
    params: List[object] = [
        aesgcm_encrypt_text(nickname),
        aesgcm_encrypt_text(bio),
        aesgcm_encrypt_text(json.dumps(links, ensure_ascii=False)),
    ]

    if extras:
        for k, v in extras.items():
            if v is None:
                v = ""
            col = PROFILE_EXTRA_MAP.get(k)
            if col and col in cols:
                set_parts.append(f"{col}=?")
                params.append(aesgcm_encrypt_text(str(v)))

    set_parts.append("updated_at=?")
    params.append(now_z())
    params.append(username)

    sql = f"UPDATE profiles SET {', '.join(set_parts)} WHERE username=?"
    conn.execute(sql, tuple(params))
    conn.commit()
    
    # Keep a Profiler entry automatically mirrored from "My Profile".
    try:
        profiler_sync_from_user_profile(username)
    except Exception:
        pass

    conn.close()

def set_profile_pic(username: str, file_stream, mime: str):
    """Store a user's profile picture on disk (plaintext).

    We keep profile pictures capped (PFP_MAX_BYTES) to avoid slow uploads and
    reduce risk/abuse.
    """
    ensure_profile_row(username)
    dst = os.path.join(PFP_DIR, f"{username}.bin")
    os.makedirs(os.path.dirname(dst), exist_ok=True)

    total = 0
    try:
        try:
            file_stream.seek(0)
        except Exception:
            pass
        with open(dst, "wb") as out:
            while True:
                chunk = file_stream.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > PFP_MAX_BYTES:
                    raise ValueError("pfp_too_large")
                out.write(chunk)
    except Exception:
        # Cleanup partial file on failure.
        try:
            os.remove(dst)
        except Exception:
            pass
        raise

    conn = db_connect()
    conn.execute(
        "UPDATE profiles SET pic_path=?, pic_mime=?, updated_at=? WHERE username=?",
        (dst, mime, now_z(), username),
    )
    conn.commit()
    conn.close()


def remove_profile_pic(username: str):
    """remove_profile_pic.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    username: Parameter.

Returns:
    Varies.
"""
    ensure_profile_row(username)
    conn = db_connect()
    row = conn.execute("SELECT pic_path FROM profiles WHERE username=?", (username,)).fetchone()
    if row and row["pic_path"] and os.path.exists(row["pic_path"]):
        try:
            os.remove(row["pic_path"])
        except Exception:
            pass
    conn.execute("UPDATE profiles SET pic_path=NULL, pic_mime=NULL, updated_at=? WHERE username=?",
                 (now_z(), username))
    conn.commit()
    conn.close()

def user_root(username: str) -> str:
    """user_root.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    username: Parameter.

Returns:
    Varies.
"""
    p = os.path.join(STORAGE_DIR, username)
    os.makedirs(p, exist_ok=True)
    return p

def safe_relpath(p: str) -> str:
    """safe_relpath.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    p: Parameter.

Returns:
    Varies.
"""
    p = (p or "").replace("\\", "/").strip()
    if p in ("", ".", "/"):
        return ""
    p = p.lstrip("/")
    parts = []
    for part in p.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise ValueError("Path traversal")
        parts.append(part)
    return "/".join(parts)

def abs_user_path(username: str, rel: str) -> str:
    """abs_user_path.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    username: Parameter.
    rel: Parameter.

Returns:
    Varies.
"""
    rel = safe_relpath(rel)
    root = user_root(username)
    ap = os.path.abspath(os.path.join(root, rel))
    root_abs = os.path.abspath(root)
    if not (ap == root_abs or ap.startswith(root_abs + os.sep)):
        raise ValueError("Bad path")
    return ap



def fast_save(file_storage, dest_path: str, bufsize: int = 64 * 1024 * 1024):
    # Fast chunked saving for large uploads.
    # Bigger buffer + buffered writer improves throughput on many devices.
    """fast_save.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    file_storage: Parameter.
    dest_path: Parameter.
    bufsize: Parameter.

Returns:
    Varies.
"""
    # Fast chunked saving for large uploads.
    # Bigger buffer + buffered writer improves throughput on many devices.
    try:
        file_storage.stream.seek(0)
    except Exception:
        pass
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb", buffering=bufsize) as out:
        shutil.copyfileobj(file_storage.stream, out, length=bufsize)

def human_size(n: int) -> str:
    """human_size.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    n: Parameter.

Returns:
    Varies.
"""
    units = ["B", "KB", "MB", "GB", "TB"]
    x = float(n)
    for u in units:
        if x < 1024.0 or u == units[-1]:
            return f"{x:.1f} {u}" if u != "B" else f"{int(x)} {u}"
        x /= 1024.0
    return f"{n} B"



# ---------------------------
# Admin helpers / kick support
# ---------------------------


def _client_ip() -> str:
    """Real client IP with anti-spoofing.

    We only trust forwarded headers when the request comes from loopback
    (i.e., a local reverse-proxy like cloudflared/tor on the SAME device).
    """
    ra = (request.remote_addr or "?").strip()
    try:
        if not _is_loopback(ra):
            return ra

        # If loopback, allow reverse-proxy headers (cloudflared commonly sets one of these)
        for h in ("CF-Connecting-IP", "X-Real-IP"):
            v = (request.headers.get(h) or "").strip()
            if v:
                return v.split(",")[0].strip()
        xff = (request.headers.get("X-Forwarded-For") or "").strip()
        if xff:
            return xff.split(",")[0].strip()
    except Exception:
        pass
    return ra

def _is_loopback(ip: str) -> bool:
    """_is_loopback.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    ip: Parameter.

Returns:
    Varies.
"""
    ip = (ip or "").strip()
    return ip == "::1" or ip == "0:0:0:0:0:0:0:1" or ip.startswith("127.")

def _is_local_admin_request() -> bool:
    """Allow admin ONLY from the host device.

    Rules:
    - Host header must be local (localhost / loopback / this device LAN IP)
    - Client IP must also be local (loopback / this device LAN IP)

    This blocks remote admin usage through LAN peers, cloudflared, Tor, etc.
    """
    try:
        host = (request.host or "").strip()
        host_only = host.split(",")[0].strip()
        host_only = host_only.split(":")[0].strip().strip("[]").lower()

        # Collect IPs that belong to THIS device (best-effort).
        server_ips = {"127.0.0.1", "::1", "0:0:0:0:0:0:0:1"}
        try:
            lip = local_ip()
            if lip:
                server_ips.add(lip.strip())
        except Exception:
            pass

        client = _client_ip()
        # Host must be local-ish, and client must be one of our own IPs.
        host_ok = (host_only in {"localhost"} or host_only in {ip.strip("[]").lower() for ip in server_ips})
        return host_ok and (client in server_ips or _is_loopback(client))
    except Exception:
        return False

def user_is_admin(username: Optional[str]) -> bool:
    """user_is_admin.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    username: Parameter.

Returns:
    Varies.
"""
    if not username:
        return False
    try:
        conn = db_connect()
        row = conn.execute("SELECT is_admin, admin_device_id FROM users WHERE username=?", (username,)).fetchone()
        conn.close()
        if not row or int(row["is_admin"]) != 1:
            return False
        # Admin is bound to device id. If DB is copied elsewhere, admin won't work.
        bound = (row["admin_device_id"] or "").strip()
        if bound and bound != DEVICE_ID:
            return False
        return True
    except Exception:
        return False

def require_admin():
    # Admin only (device-bound via admin_device_id). Admin can use Local/LAN/Cloudflared/Tor links.
    """require_admin.

Admin-only route handler.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    # Admin only (device-bound via admin_device_id). Admin can use Local/LAN/Cloudflared/Tor links.
    if not user_is_admin(current_user()):
        abort(403)


def downloads_dir() -> str:
    '''
    Best-effort Android/Termux downloads directory.
    - Termux: ~/storage/downloads (requires termux-setup-storage)
    - Android common: /storage/emulated/0/Download
    - Fallback: Homework/ButSystem/ (or internal if storage permission missing)
    '''
    cand = os.path.join(HOME, "storage", "downloads")
    if os.path.isdir(cand):
        return cand
    cand = "/storage/emulated/0/Download"
    if os.path.isdir(cand):
        return cand
    return BASE_DIR

def is_encrypted_file(path: str) -> bool:
    """is_encrypted_file.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    path: Parameter.

Returns:
    Varies.
"""
    try:
        with open(path, "rb") as f:
            return f.read(len(MAGIC)) == MAGIC
    except Exception:
        return False

# ---------------------------
# UI (lavender/purple/blue/black + light theme)
# ---------------------------

BUT_CSS = r"""
:root{
  /* Palette synced (approx) from style.css */
  --bg:#000000;                               /* --nm-abyss-blue */
  --panel:#0e0d18;                            /* --nm-menu-solid */
  --panel2:rgba(18, 18, 30, 0.52);            /* --nm-container */
  --nav: #0b0a12;                             /* --nm-nav-solid */
  --border:rgba(205, 147, 255, 0.50);         /* --nm-border */
  --text:rgba(255, 255, 255, 0.92);           /* --nm-text */
  --muted:rgba(255, 255, 255, 0.74);          /* --nm-text-muted */
  --accent:#cd93ff;                           /* --nm-accent */
  --accent-hover:#e2c1ff;                     /* --nm-accent-hover */
  --danger:#ff6b6b;                           /* --nm-danger */
  --success:#51cf66;                          /* --nm-success */
  --warning:#ffd43b;                          /* --nm-warning */
  --text-on-accent:#0b0a12;                   /* --nm-text-on-accent */
  --shadow: 0 18px 50px rgba(0,0,0,0.42);     /* --shadow-elev-2 */
  --radius: 22px;                             /* --radius-lg */

  /* App font */
  --app-font: system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", "Helvetica Neue", Arial, "Apple Color Emoji","Segoe UI Emoji";

  /* Chat bubbles */
  --bubble-me: var(--accent);
  --bubble-them: rgba(14, 14, 24, 0.58);      /* --nm-dark */
  --bubble-me-text: var(--text-on-accent);
  --bubble-them-text: var(--text);

  /* Burger icon */
  --burger:#ffffff;
  --burger-bg:#000000;
  --toggler-icon: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 30 30'%3e%3cpath stroke='%23ffffff' stroke-linecap='round' stroke-miterlimit='10' stroke-width='2' d='M4 7h22M4 15h22M4 23h22'/%3e%3c/svg%3e");
}

.light-theme{
  /* Light theme values from style.css */
  --bg:#ffffff;                               /* --nm-abyss-blue */
  --panel:#ffffff;                            /* --nm-menu-solid */
  --panel2:rgba(255, 255, 255, 0.62);         /* --nm-container */
  --nav:#ffffff;                              /* --nm-nav-solid */
  --border:rgba(123, 31, 162, 0.35);          /* --nm-border */
  --text:rgba(10, 10, 18, 0.92);              /* --nm-text */
  --muted:rgba(10, 10, 18, 0.70);             /* --nm-text-muted */
  --accent:#7b1fa2;                           /* --nm-accent */
  --accent-hover:#9c27b0;                     /* --nm-accent-hover */
  --danger:#d6336c;                           /* --nm-danger */
  --success:#2f9e44;                          /* --nm-success */
  --warning:#f59f00;                          /* --nm-warning */
  --text-on-accent:rgba(255, 255, 255, 0.96); /* --nm-text-on-accent */
  --shadow: 0 18px 50px rgba(0,0,0,0.16);     /* --shadow-elev-2 */
  --radius: 22px;

  --bubble-me: var(--accent);
  --bubble-them: rgba(255, 255, 255, 0.70);   /* --nm-dark */
  --bubble-me-text: var(--text-on-accent);
  --bubble-them-text: var(--text);

  --burger:#111111;
  --burger-bg:#ffffff;
  --toggler-icon: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 30 30'%3e%3cpath stroke='%23111111' stroke-linecap='round' stroke-miterlimit='10' stroke-width='2' d='M4 7h22M4 15h22M4 23h22'/%3e%3c/svg%3e");
}

html,body{height:100%;min-height:100%;overflow-x:hidden;}
html{-webkit-text-size-adjust:100%; text-size-adjust:100%;}
body{
  margin:0;
  min-height: var(--app-height, 100vh);
  background: var(--bg);
  color: var(--text);
  font-family: var(--app-font);
  padding-bottom: env(safe-area-inset-bottom);
  caret-color: var(--accent);
}
@supports (-webkit-touch-callout: none){
  html, body{ min-height: -webkit-fill-available; }
  body{ min-height: var(--app-height, -webkit-fill-available); }
}

/* Chat mode: prevent whole page scrolling; only messages scroll */
body.chat-mode{ height: var(--app-height, 100dvh); min-height: var(--app-height, 100dvh); overflow:hidden; display:flex; flex-direction:column; }
main.chat-main{ flex:1 1 auto; overflow:hidden; padding:0; }
.chat-page{ height:100%; display:flex; flex-direction:column; }
.chat-top{ flex:0 0 auto; padding: 12px 12px 0 12px; }
.chat-messages{ flex:1 1 auto; overflow:auto; padding: 12px; }
.chat-composer{ flex:0 0 auto; padding: 10px; border-top:1px solid var(--border); background: var(--bg); padding-bottom: calc(10px + env(safe-area-inset-bottom)); }
.composer-actions{
  display:flex;
  align-items:center;
  gap: .45rem;
  flex-wrap: nowrap;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 2px;
}
.composer-actions::-webkit-scrollbar{ display:none; }
.composer-status{ min-height: 1em; }

.composer-row{
  display:flex;
  align-items:flex-end;
  gap:.45rem;
  flex-wrap:nowrap;
}
.composer-row .msg-input{
  flex:1 1 auto;
  min-width:0;
}
.gif-text-btn{
  padding: .25rem .55rem;
  font-weight:800;
  letter-spacing:.02em;
}
.dm-ticks{
  margin-left:.35rem;
  font-size:.85em;
  opacity:.85;
  user-select:none;
}
.dm-ticks.delivered{ opacity:.9; }
.dm-ticks.seen{ color: var(--accent); opacity:1; }

/* Composer controls */
.file-hidden{
  position:absolute !important;
  width:1px !important;
  height:1px !important;
  padding:0 !important;
  margin:-1px !important;
  overflow:hidden !important;
  clip:rect(0,0,0,0) !important;
  white-space:nowrap !important;
  border:0 !important;
  opacity:0 !important;
}
.icon-only{
  padding: .29rem .48rem !important;
  line-height: 1 !important;
  display:inline-flex !important;
  align-items:center !important;
  justify-content:center !important;
  gap:0 !important;
}
.msg-input{
  resize:none !important;
  overflow:hidden !important;
  min-height: 34px;
  max-height: 160px;
}
.btn-send{
  padding: .36rem .59rem !important;
  line-height: 1 !important;
  display:inline-flex !important;
  align-items:center !important;
  justify-content:center !important;
  border-radius: 16px !important;
}
.btn-chat-top{
  padding: .3rem .6rem !important;
  font-size: .8rem !important;
  line-height: 1.1 !important;
}
a{color:var(--accent); text-decoration:none;}
a:visited{color:var(--accent);}
a:hover{color:var(--accent-hover);}
::selection{ background: rgba(205,147,255,0.35); color: var(--text); }

.navbar{
  background: var(--nav) !important;
  border-bottom:1px solid var(--border);
  /* 10% smaller top nav everywhere */
  --bs-navbar-padding-y: .45rem;
  --bs-navbar-padding-x: 1rem;
  font-size: 0.9rem;
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}
.navbar .navbar-brand, .navbar .nav-link{ color: var(--text) !important; }
.navbar .nav-link:hover{ color: var(--accent-hover) !important; }
/* Fix: burger menu dropdown should never be transparent */
.navbar .navbar-collapse{
  background: var(--nav) !important;
}
@media (max-width: 991.98px){
  .navbar .navbar-collapse{
    margin-top: .6rem;
    padding: .75rem;
    border: 1px solid var(--border);
    border-radius: 18px;
    box-shadow: var(--shadow);
  }
}
.brand{letter-spacing:.12em; font-weight:900; text-transform:uppercase;}

.brand-logo{height:25px;width:25px;border-radius:10px;object-fit:cover;box-shadow:0 8px 22px rgba(0,0,0,.25);}

/* --- Top bar: keep Theme + Language outside burger menu and fit on one line --- */
.navbar .container-fluid{
  padding-left: .55rem !important;
  padding-right: .55rem !important;
}
.nav-top-controls .btn{
  padding: .28rem .55rem !important;
  border-radius: 14px;
  line-height: 1.05;
}
.nav-top-controls{
  flex: 0 0 auto;
}

/* Keep brand + controls on one line; prevent wrap/overflow on small screens */
.navbar .navbar-brand{ min-width: 0; }
.navbar .navbar-brand span{ white-space: nowrap; }
.nav-top-controls{ white-space: nowrap; }
.lang-toggle{ white-space: nowrap; }
.lang-toggle.lang-long{ font-size: .82rem; padding: .24rem .45rem !important; }
@media (max-width: 420px){
  .lang-toggle.lang-long{ font-size: .78rem; padding: .22rem .38rem !important; }
}

@media (max-width: 520px){
  .navbar .navbar-brand span{
    max-width: 46vw;
    overflow: hidden;
    text-overflow: ellipsis;
    display: inline-block;
    vertical-align: bottom;
  }
}
@media (max-width: 380px){
  .nav-top-controls .btn{
    padding: .22rem .42rem !important;
    font-size: .85rem;
  }
  .navbar-toggler{
    padding: .26rem .44rem !important;
  }
}



@media (max-width: 480px){
  .navbar{
    --bs-navbar-padding-y: .26rem;
    font-size: .86rem;
  }
  .brand-logo{height:22px;width:22px;border-radius:8px;}
  .navbar .navbar-brand{ padding-top:.1rem; padding-bottom:.1rem; }
  .nav-top-controls .btn{
    padding: .20rem .42rem !important;
    font-size: .84rem;
  }
  .navbar-toggler{ padding: .22rem .40rem !important; }
}
@media (max-width: 360px){
  .navbar .navbar-brand span{ display:none; }
}
.card-soft{
  background: var(--panel);
  border:1px solid var(--border);
  box-shadow: var(--shadow);
  border-radius: var(--radius);
}



/* Palette-friendly notice (replaces Bootstrap's bright yellow warning in our app UI) */
.alert-notice{
  background: rgba(205, 147, 255, 0.12) !important;
  border: 1px solid rgba(205, 147, 255, 0.38) !important;
  color: var(--text) !important;
  border-radius: 16px !important;
  box-shadow: none !important;
}
.light-theme .alert-notice{
  background: rgba(123, 31, 162, 0.10) !important;
  border-color: rgba(123, 31, 162, 0.28) !important;
  color: var(--text) !important;
}
.alert-notice a{ color: var(--accent) !important; }
.alert-notice ul{ margin-bottom:0; }
.small-muted{color:var(--muted);}
.badge-soft{
  background: var(--panel2);
  border:1px solid var(--border);
  color: var(--accent);
  font-weight:800;
}

.btn{border-radius: 14px;}
.btn-ghost{
  background: var(--panel2);
  border: 2px solid var(--border);
  color: var(--text);
  font-weight:800;
}
.btn-ghost:hover{background: var(--panel); border-color: var(--accent-hover); color: var(--accent-hover);}
.btn-ghost.active{background: var(--accent); border-color: var(--accent); color: var(--text-on-accent);}

.btn-accent{
  background: var(--accent);
  border: 2px solid var(--accent);
  color: var(--text-on-accent);
  font-weight:900;
}
.btn-accent:hover{
  background: var(--accent-hover);
  border-color: var(--accent-hover);
  color: var(--text-on-accent);
}
.btn-accent:active{filter: brightness(0.95);}

.form-control, .form-select{
  background: var(--panel2);
  border:1px solid var(--border);
  color: var(--text);
  border-radius: 14px;
}
.form-control:focus, .form-select:focus{ border-color: var(--accent); box-shadow: none; }
.form-label{color: var(--muted);}
hr{border-color: var(--border);}

/* Mobile: prevent iOS zoom-on-focus by keeping inputs >=16px */
@media (max-width: 991.98px){
  input.form-control, textarea.form-control, select.form-select{ font-size: 16px; }
}
/* Better tap behavior across Android/iOS/desktop */
.btn, .nav-link, summary, .pfp-clickable{ touch-action: manipulation; -webkit-tap-highlight-color: transparent; }

/* Flash messages */
.flash{
  background: var(--panel2);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 10px 12px;
}

/* Bootstrap close button (theme-aware) */
.btn-close{ filter: invert(1); opacity: .9; }
.light-theme .btn-close{ filter: invert(0); }

/* iOS/Safari autofill can override dark colors */
input:-webkit-autofill,
textarea:-webkit-autofill,
select:-webkit-autofill{
  -webkit-text-fill-color: var(--text) !important;
  box-shadow: 0 0 0px 1000px var(--panel2) inset !important;
  transition: background-color 9999s ease-in-out 0s;
}


.avatar{ width:32px;height:32px;border-radius:10px;border:1px solid var(--border); object-fit:cover; }
.kbd{
  border:1px solid var(--border);
  background: var(--panel2);
  padding:2px 6px;
  border-radius:8px;
  font-size:.78rem;
  color:var(--muted);
}

/* --- Chat layout --- */
.chat-shell{display:flex; gap: 16px; align-items:stretch;}
.chat-list{width: 320px; max-width: 100%;}
@media (max-width: 991px){
  .chat-shell{flex-direction:column;}
  .chat-list{width:100%;}
}
.chat-thread{flex:1; min-height: 56vh;}

.msg-row{display:flex; flex-direction:column; gap: 2px; margin-bottom: 10px;}
.msg-row.me{align-items:flex-end;}
.msg-row.them{align-items:flex-start;}

.bubble{
  display:inline-block;
  width:auto;
  max-width: 86%;
  padding: .28rem .62rem;
  border-radius: 18px;
  white-space: normal;
  word-break: break-word;
  line-height: 1.35;
}
.bubble.me{
  background: var(--bubble-me);
  color: var(--bubble-me-text);
  border: 1px solid var(--border);
  border-bottom-right-radius: 6px;
}
.bubble.them{
  background: var(--bubble-them);
  color: var(--bubble-them-text);
  border: 1px solid var(--border);
  border-bottom-left-radius: 6px;
}
.msg-meta{font-size:.78rem; color: var(--muted);}

.msg-text{ white-space: pre-wrap; }

/* --- Typeahead suggestions --- */
.suggest-wrap{position:relative;}
.suggest-list{
  position:absolute;
  top: calc(100% + 6px);
  left:0; right:0;
  background: var(--panel);
  border:1px solid var(--border);
  border-radius: 14px;
  box-shadow: var(--shadow);
  z-index: 2000;
  overflow:hidden;
  display:none;
}
.suggest-item{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap: 10px;
  padding: 10px 12px;
  color: var(--text);
  border-bottom:1px solid var(--border);
}
.suggest-item:last-child{border-bottom:none;}
.suggest-item:hover{ background: var(--panel2); color: var(--accent-hover); }
.suggest-left{display:flex; align-items:center; gap:8px; min-width:0;}
.suggest-name{font-weight:900; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}

/* --- Tables --- */
.table{
  color: var(--text);
  --bs-table-bg: var(--panel);
  --bs-table-striped-bg: var(--panel2);
  --bs-table-border-color: var(--border);
}
.table thead th{color: var(--muted); border-color: var(--border);}
.table td, .table th{border-color: var(--border);}

/* Offcanvas */
.offcanvas{
  background: var(--panel);
  color: var(--text);
  border-left: 1px solid var(--border);
}

.user-item{
  display:flex;
  align-items:center;
  gap:12px;
  padding:10px 12px;
  border:1px solid var(--border);
  border-radius: 16px;
  background: var(--panel);
}
.user-item + .user-item{ margin-top: 10px; }

.avatar-wrap{ width:42px; height:42px; flex:0 0 42px; }
.avatar-img{
  width:42px; height:42px; border-radius: 14px;
  object-fit: cover;
  border: 1px solid var(--border);
  background: var(--panel2);
}
.avatar-fallback{
  width:42px; height:42px; border-radius: 14px;
  display:flex; align-items:center; justify-content:center;
  background: var(--panel2);
  border: 1px solid var(--border);
  color: var(--text);
  font-size: 18px;
}

.pill{
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--panel2);
  font-size: 12px;
  color: var(--text);
  white-space: nowrap;
}
.pill.online{ border-color: var(--success); }
.pill.offline{ border-color: var(--border); color: var(--muted); }

.read-box{
  background: var(--panel2);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: .75rem .85rem;
  color: var(--text);
  white-space: pre-wrap;
}

.user-item.active{border-color: var(--accent); background: var(--panel2);}

/* Burger icon */
.navbar-toggler{
  border:1px solid var(--border);
  background: var(--burger-bg) !important;
  border-radius: 14px;
}
.navbar-toggler:focus{ box-shadow: 0 0 0 .2rem rgba(120,120,255,0.18); }

.navbar-toggler-icon{
  background-image: var(--toggler-icon) !important;
  background-size: 1.45em 1.45em;
}


/* Chat bubble media sizing */
.bubble audio{ width: 220px; max-width: 100%; height: 34px; }
.bubble video, .bubble img{ max-width: 100%; border-radius: 14px; display:block; }
/* Keep media bubbles from becoming huge on mobile */
.bubble img{ max-width: 260px; max-height: 340px; object-fit: cover; }
.bubble video{ max-width: 260px; max-height: 420px; }

/* GIF picker */
.gif-grid{ display:grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
@media (min-width: 768px){ .gif-grid{ grid-template-columns: repeat(4, 1fr); } }
.gif-item{ border:0; padding:0; background:transparent; border-radius: 14px; overflow:hidden; }
.gif-item img{ width:100%; height: 120px; object-fit: cover; display:block; }
.bubble .file-chip{
  display:inline-flex; align-items:center; gap:8px;
  padding:6px 10px; border-radius:999px;
  border:1px solid var(--border); background: rgba(255,255,255,0.08);
  text-decoration:none; color: inherit; font-weight: 600;
}
.light-theme .bubble .file-chip{ background: rgba(0,0,0,0.06); }

/* Long-press actions */
#actionSheet{
  position:fixed; inset:0; display:none;
  background: rgba(0,0,0,0.55);
  z-index: 5000;
  align-items:flex-end; justify-content:center;
  padding: 14px;
  padding-bottom: calc(14px + env(safe-area-inset-bottom));
}
.light-theme #actionSheet{ background: rgba(255,255,255,0.60); }
#actionSheet .sheet{
  width: min(520px, 100%);
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 10px;
  box-shadow: var(--shadow);
}
#actionSheet .sheet button{
  width:100%;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--panel2);
  color: var(--text);
  font-weight: 700;
}
#actionSheet .sheet button + button{ margin-top: 8px; }
#actionSheet .sheet .danger{ border-color: rgba(255,107,107,0.6); }
#actionSheet .sheet .closex{ background: transparent; border:none; color: var(--muted); font-weight: 600; padding: 8px; }

/* Bootstrap component visibility fixes */
.navbar-toggler{ border-color: var(--border) !important; }
.navbar-toggler:focus{ box-shadow:none !important; }
.form-control::placeholder{ color: var(--muted); opacity: .85; }
.form-control:disabled, .form-select:disabled{ opacity:.85; }

.dropdown-menu{
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  box-shadow: var(--shadow);
}
.dropdown-item{ color: var(--text) !important; }
.dropdown-item:hover, .dropdown-item:focus{ background: var(--panel2) !important; color: var(--text) !important; }

.modal-content{
  background: var(--panel) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}
.modal-header, .modal-footer{ border-color: var(--border) !important; }

.list-group-item{
  background: var(--panel2) !important;
  border-color: var(--border) !important;
  color: var(--text) !important;
}
.card{
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
}
.card-header{ border-color: var(--border) !important; }

.btn-outline-secondary{
  border-color: var(--border) !important;
  color: var(--text) !important;
}
.btn-outline-secondary:hover{ background: var(--panel2) !important; color: var(--text) !important; }

/* --- Fix: burger/toggler visibility across themes --- */
.navbar{
  --bs-navbar-toggler-icon-bg: var(--toggler-icon);
}
.navbar-toggler{
  background: var(--burger-bg) !important;
  border-color: var(--border) !important;
  color: var(--text) !important;
}
.navbar-toggler:hover{
  background: var(--burger-bg) !important;
  border-color: var(--accent-hover) !important;
}
.navbar-toggler-icon{
  background-image: var(--toggler-icon) !important;
  filter: none !important;
}

/* --- Fix: ensure Bootstrap table-dark respects theme vars --- */
.table-dark{
  --bs-table-bg: var(--panel) !important;
  --bs-table-striped-bg: var(--panel2) !important;
  --bs-table-border-color: var(--border) !important;
  --bs-table-color: var(--text) !important;
  color: var(--text) !important;
}
.table-dark th, .table-dark td{
  color: var(--text) !important;
  border-color: var(--border) !important;
}

/* --- Fix: text utility classes --- */
.text-muted{ color: var(--muted) !important; }
.text-dark{ color: var(--text) !important; }
.text-secondary{ color: var(--muted) !important; }

/* --- Back button --- */
.btn-back{
  width: 42px;
  height: 38px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  font-weight: 900;
  line-height: 1;
}

/* --- Theme toggle button visibility (top-right square) --- */
#themeToggle, .theme-toggle, [data-theme-toggle]{
  background: var(--panel2) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
}
#themeToggle:hover, .theme-toggle:hover, [data-theme-toggle]:hover{
  border-color: var(--accent-hover) !important;
}

/* --- Global text enforcement (dark=white, light=black via --text) --- */
body, h1,h2,h3,h4,h5,h6, p, span, div, small, strong, em, li, label, td, th, input, textarea, select, button{
  color: var(--text);
}
.light-theme body, .light-theme h1,.light-theme h2,.light-theme h3,.light-theme h4,.light-theme h5,.light-theme h6,
.light-theme p, .light-theme span, .light-theme div, .light-theme small, .light-theme strong, .light-theme em,
.light-theme li, .light-theme label, .light-theme td, .light-theme th,
.light-theme input, .light-theme textarea, .light-theme select, .light-theme button{
  color: var(--text);
}

/* --- Burger icon: force 3-line icon visibility and sizing --- */
.navbar-toggler{
  padding: .315rem .495rem !important;
}
.navbar-toggler-icon{
  width: 1.44em !important;
  height: 1.44em !important;
  background-image: var(--toggler-icon) !important;
  background-size: 100% 100% !important;
  background-repeat: no-repeat !important;
  background-position: center !important;
  opacity: 1 !important;
}


/* --- Fix: burger button colors + icon visibility (mobile navbar) --- */
.navbar-toggler{
  background: var(--panel2) !important;
  border: 2px solid var(--border) !important;
  border-radius: 14px;
}
.navbar-toggler:hover{
  background: var(--panel) !important;
  border-color: var(--accent-hover) !important;
}
.navbar-toggler:focus{ box-shadow:none !important; }

/* --- Fix: Bootstrap .table text colors in dark theme (Admin table etc.) --- */
.table{
  --bs-table-color: var(--text) !important;
  --bs-table-striped-color: var(--text) !important;
  --bs-table-hover-color: var(--text) !important;
  --bs-table-active-color: var(--text) !important;
}
.table>:not(caption)>*>*{
  color: var(--bs-table-color) !important;
}
.table thead th{
  color: var(--muted) !important;
}
.table .small-muted, .table td.small-muted, .table th.small-muted{
  color: var(--muted) !important;
}


.notif-badge{display:inline-flex;align-items:center;justify-content:center;min-width:1.4rem;height:1.4rem;padding:0 .35rem;border-radius:999px;background:var(--accent);color:var(--accentText);font-size:.75rem;line-height:1;font-weight:800;}


/* Optional section toggle (bullet button) */
details.opt-details > summary{ list-style:none; cursor:pointer; user-select:none; display:inline-flex; align-items:center;
  padding:.4rem .8rem; border:1px solid var(--border); border-radius:16px; background:rgba(255,255,255,0.03);
}
details.opt-details > summary::-webkit-details-marker{ display:none; }
details.opt-details[open] > summary{ background:rgba(255,255,255,0.06); }

/* Click-to-expand images */
.pfp-clickable{ cursor:pointer; }
.img-modal{ position:fixed; inset:0; display:none; align-items:center; justify-content:center;
  background:rgba(0,0,0,0.78); z-index: 2500; padding:18px;
}
.img-modal.open{ display:flex; }
.img-modal img{ max-width:92vw; max-height:90vh; border-radius:18px; border:1px solid var(--border); background:var(--panel); box-shadow: var(--shadow); }

/* Burger menu: 3 items per row on mobile */
@media (max-width: 991.98px){
  .navbar-nav.nav-grid{
    display:grid !important;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap:10px;
    margin-top:12px;
  }
  .navbar-nav.nav-grid .nav-item{ margin:0 !important; }
  .navbar-nav.nav-grid .nav-link{
    padding:.55rem .6rem;
    border:1px solid var(--border);
    border-radius:16px;
    text-align:center;
    background:rgba(255,255,255,0.03);
  }
}

/* --- Global responsive auto-resize (small screens) --- */
:root{ --navH: 72px; }
.navbar{ min-height: var(--navH); }
.nav-top-controls .btn{ min-width:44px; }
.lang-toggle{ width: 92px; text-align:center; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
  font-size: clamp(.72rem, 2.8vw, .92rem);
}
.navbar-nav .nav-link{
  font-size: clamp(.72rem, 2.6vw, .95rem);
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}
@media (max-width: 420px){
  :root{ --navH: 60px; }
  .navbar{ padding-top: 6px; padding-bottom: 6px; }
  .navbar .brand span{ font-size: 1.05rem; letter-spacing:.02em; }
  .brand-logo{ width:32px !important; height:32px !important; border-radius:12px !important; }
  .nav-top-controls{ gap:.4rem !important; }
}
@media (max-width: 576px){
  main.container{ padding-left: 12px !important; padding-right: 12px !important; }
  .card-soft{ border-radius: 22px; }
}
/* Panic privacy mode: hide sensitive details but keep navigation usable */
body.privacy-panic .panic-blurable{
  filter: blur(18px) saturate(.7) brightness(.28);
  transition: filter .2s ease, opacity .2s ease;
}
body.privacy-panic .panic-banner{ display:flex !important; }
.panic-banner{
  display:none;
  position:fixed;
  right:12px;
  bottom:calc(12px + env(safe-area-inset-bottom));
  z-index:2500;
  gap:.55rem;
  align-items:center;
  padding:.75rem .9rem;
  border:1px solid var(--border);
  border-radius:16px;
  background:rgba(8,11,16,.92);
  box-shadow:var(--shadow);
  max-width:min(92vw, 420px);
}
body.light-theme .panic-banner{ background:rgba(255,255,255,.94); }
.panic-banner .panic-text{ font-size:.92rem; color:var(--text); }


"""

TEMPLATES = {}

TEMPLATES["base.html"] = r"""
<!doctype html>
<html lang="{{ lang }}">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"/>
  <meta name="format-detection" content="telephone=no,date=no,address=no,email=no"/>
  <meta name="apple-mobile-web-app-capable" content="yes"/>
  <meta name="mobile-web-app-capable" content="yes"/>
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"/>
  <meta name="theme-color" content="#0b0f14"/>
  <meta name="csrf-token" content="{{ csrf_token }}"/>
  <title>{{ title or "ButSystem" }}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>{{ but_css|safe }}</style>
</head>
<body data-ui-theme="{{ (user_prefs.ui_theme_key if user_prefs and user_prefs.ui_theme_key else 'default') }}" class="{% if request.endpoint in ['chat_with','group_chat','discussion'] %}chat-mode{% endif %}">
<nav class="navbar navbar-expand-lg sticky-top">
  <div class="container-fluid">
    <a class="navbar-brand brand d-flex align-items-center gap-2" href="https://ded-sec.space">
      <img id="brandLogo" data-logo class="brand-logo" src="{{ logo_dark }}" alt="logo"/>
      <span>ButSystem</span>
    </a>

    {% set hide_burger = request.endpoint in ['index','loading','login','signup'] %}

    <!-- Always-visible controls (outside the burger menu): Language + Burger -->
    <div class="d-flex align-items-center gap-2 ms-auto nav-top-controls">
      <a class="btn btn-ghost btn-sm lang-toggle {% if lang=='en' %}lang-long{% endif %}" href="{{ url_for('toggle_language') }}" title="{{ _('Language') }}" aria-label="{{ _('Language') }}">
        {{- "Ελληνικά" if lang=="en" else "English" -}}
      </a>
      {% if not hide_burger %}
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navBut" aria-controls="navBut" aria-expanded="false" aria-label="{{ _('Menu') }}">
        <span class="navbar-toggler-icon"></span>
      </button>
      {% endif %}
    </div>

    {% if not hide_burger %}
    <div class="collapse navbar-collapse" id="navBut">
      <ul class="navbar-nav nav-grid me-auto mb-2 mb-lg-0">
        {% if user %}
          <li class="nav-item"><a class="nav-link" href="{{ url_for('profiler') }}">{{ _('Profiler') }}</a></li>
          {% if is_admin %}<li class="nav-item"><a class="nav-link" href="{{ url_for('bounty') }}">{{ _('Bounty') }}</a></li>{% endif %}
          <li class="nav-item"><a class="nav-link" href="{{ url_for('reports') }}">{{ _('Reports') }}</a></li>
          <li class="nav-item"><a class="nav-link" href="{{ url_for('news') }}">{{ _("News") }}</a></li>
          <li class="nav-item"><a class="nav-link" href="{{ url_for('groups') }}">{{ _("Groups") }}</a></li>
          <li class="nav-item"><a class="nav-link" href="{{ url_for('discussion') }}">{{ _('Discussion') }}</a></li>
          <li class="nav-item"><a class="nav-link" href="{{ url_for('chats') }}">{{ _("Chats") }} {% if notifications and notifications.dm_total>0 %}<span class="notif-badge">{{ notifications.dm_total }}</span>{% endif %}</a></li>
          <li class="nav-item"><a class="nav-link" href="{{ url_for('stories') }}">{{ _('Stories') }}</a></li>
          <li class="nav-item"><a class="nav-link" href="{{ url_for('live_locations') }}"><span>{{ _("Live Locations") }}</span></a></li>
          <li class="nav-item"><a class="nav-link" href="{{ url_for('face_detector_page') }}">{{ _("Face Detector") }}</a></li>
          <li class="nav-item"><a class="nav-link" href="{{ url_for('profile') }}">{{ _("My Profile") }}</a></li>
          {% if is_admin %}<li class="nav-item"><a class="nav-link" href="{{ url_for('admin_panel') }}">{{ _("Admin") }}</a></li>{% endif %}
          <li class="nav-item"><a class="nav-link" href="{{ url_for('settings_security') }}">{{ _("Settings") }}</a></li>
          <li class="nav-item"><a class="nav-link" href="#" data-bs-toggle="offcanvas" data-bs-target="#helpCanvas">{{ _("Help") }}</a></li>
          <li class="nav-item"><a class="nav-link" href="{{ url_for('logout') }}">{{ _("Logout") }}</a></li>
        {% endif %}
      </ul>

      <div class="d-flex align-items-center gap-2 flex-wrap justify-content-end">
        {% if not user %}
          <a class="btn btn-ghost" href="{{ url_for('login') }}">{{ _("Login") }}</a>
          <a class="btn btn-accent" href="{{ url_for('signup') }}">{{ _("Request Access") }}</a>
        {% endif %}
      </div>
    </div>
    {% endif %}
  </div>
</nav>

{% if request.endpoint in ['chat_with','group_chat','discussion'] %}
<main class="chat-main">
{% else %}
<main class="container py-4">
{% endif %}
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <div class="flash mb-3">
        {% for m in messages %}<div>• {{ m }}</div>{% endfor %}
      </div>
    {% endif %}
  {% endwith %}

  {% block content %}{% endblock %}
  {% if request.endpoint not in ['chat_with','group_chat','discussion'] %}
  <hr class="mt-5"/>
  {% endif %}
</main>

<div class="panic-banner">
  <div class="panic-text">{{ _("Panic mode is active. Sensitive content is blurred until you resume.") }}</div>
  {% if user %}<button class="btn btn-sm btn-accent" type="button" id="resumePrivacyBtnInline">{{ _("Resume") }}</button>{% endif %}
</div>

<div class="offcanvas offcanvas-end" tabindex="-1" id="helpCanvas">
  <div class="offcanvas-header">
    <h5 class="offcanvas-title">{{ _("ButSystem Helper") }}</h5>
    <button type="button" class="btn-close" data-bs-dismiss="offcanvas" aria-label="{{ _('Close') }}"></button>
  </div>
  <div class="offcanvas-body">
    <div class="card-soft p-3">
      <div class="small-muted mb-2">{{ _("How to use ButSystem") }}</div>
      <div class="small-muted mb-3">{{ _("This guide explains every button and icon you see in the app.") }}</div>

      <div class="alert alert-notice small-muted" style="font-size:.92rem;">
        <div class="fw-bold mb-2">{{ _("Important notice") }}</div>
        <ul class="mb-0 ps-3">
          <li>{{ _("This system is NOT affiliated with police, military, or any government agency.") }}</li>
          <li>{{ _("It is for personal use only.") }}</li>
          <li>{{ _("Only create profiles for people who have given you explicit consent.") }}</li>
          <li>{{ _("Do not use this system for harassment, stalking, or any illegal activity.") }}</li>
          <li>{{ _("The creators and maintainers are not responsible for misuse.") }}</li>
        </ul>
      </div>

      <div class="fw-bold mb-2">{{ _("Top bar") }}</div>
      <ul class="small-muted">
        <li><span class="kbd">Settings → Appearance</span> <b>{{ _("Theme") }}</b> — {{ _("Choose dark/light mode and color style.") }}</li>
        <li><span class="kbd">English / Ελληνικά</span> <b>{{ _("Language") }}</b> — {{ _("Switch the interface language.") }}</li>
        <li><span class="kbd">☰</span> <b>{{ _("Menu") }}</b> — {{ _("Open the menu to navigate to all pages.") }}</li>
      </ul>

      <hr class="my-3"/>

      <div class="fw-bold mb-2">{{ _("Chats list") }}</div>
      <ul class="small-muted">
        <li><span class="kbd">📌</span> <b>{{ _("Saved messages") }}</b> — {{ _("Your private notes to yourself.") }}</li>
        <li><span class="kbd">🟢</span> {{ _("Online") }} / <span class="kbd">⚫</span> {{ _("Offline") }} — {{ _("User status.") }}</li>
        <li><b>{{ _("Search") }}</b> — {{ _("Type a username or nickname to filter the list.") }}</li>
        <li><b>{{ _("Open chat") }}</b> — {{ _("Tap a user to open a DM.") }}</li>
      </ul>

      <hr class="my-3"/>

      <div class="fw-bold mb-2">{{ _("Chat screen") }}</div>
      <ul class="small-muted">
<li><span class="kbd">➡️</span> <b>{{ _("Send") }}</b> — {{ _("Send the message.") }}</li>
        <li><span class="kbd">📎</span> <b>{{ _("Attach file") }}</b> — {{ _("Send a file in chat.") }}</li>
        <li><span class="kbd">🖼️ / GIF</span> <b>{{ _("GIFs") }}</b> — {{ _("Send an animated GIF.") }}</li>
        <li><span class="kbd">🎙️ → ⏹️</span> <b>{{ _("Voice message") }}</b> — {{ _("Record a voice message (tap again to stop).") }}</li>
        <li><span class="kbd">✏️</span> <b>{{ _("Edit message") }}</b> — {{ _("Edit your own message when available.") }}</li>
        <li><span class="kbd">🗑️</span> <b>{{ _("Delete") }}</b> — {{ _("Delete your own message.") }}</li>
        <li><span class="kbd">✔ / ✔✔</span> <b>{{ _("Sent / Delivered / Seen") }}</b> — {{ _("Delivery status.") }}</li>
      </ul>

      <hr class="my-3"/>
      <hr class="my-3"/>

<div class="fw-bold mb-2">{{ _("Groups") }}</div>
      <ul class="small-muted">
        <li><span class="kbd">👥</span> {{ _("Create group chats and manage members.") }}</li>
      </ul>

      <div class="fw-bold mb-2">{{ _("File Vault") }}</div>
      <ul class="small-muted">
        <li><span class="kbd">📁</span> <b>{{ _("Folder") }}</b> — {{ _("Open a folder.") }}</li>
        <li><span class="kbd">📄</span> <b>{{ _("File") }}</b> — {{ _("Download or open a file.") }}</li>
      </ul>

      <div class="fw-bold mb-2">{{ _("Live Locations") }}</div>
      <ul class="small-muted">
        <li><b>{{ _("Start sharing") }}</b> / <b>{{ _("Stop sharing") }}</b> — {{ _("Share your location with others. You can stop anytime.") }}</li>
        <li><b>{{ _("Refresh") }}</b> — {{ _("Update the list of people who are sharing.") }}</li>
      </ul>

      <div class="fw-bold mb-2">{{ _("My Profile") }}</div>
      <ul class="small-muted">
        <li><b>{{ _("Edit") }}</b> — {{ _("Update your nickname, bio, links, and picture.") }}</li>
        <li><span class="kbd">⬇️ / ⬆️</span> <b>{{ _("Optional fields") }}</b> — {{ _("Show or hide optional fields.") }}</li>
      </ul>

      <div class="fw-bold mb-2">Profiler</div>
      <ul class="small-muted">
        <li><b>{{ _("Create profile") }}</b> — {{ _("Create an encrypted Profiler entry.") }}</li>
        <li><b>{{ _("Export Profiles") }}</b> — {{ _("Download all Profiler entries as an export file.") }}</li>
        <li><b>{{ _("Combine Profiles") }}</b> — {{ _("Merge imported Profiler data into your local Profiler.") }}</li>
        <li><b>{{ _("Search") }}</b> + <b>{{ _("Go") }}</b> — {{ _("Search is done locally by decrypting entries in memory (still stored encrypted).") }}</li>
      </ul>

      <div class="fw-bold mb-2">{{ _("Settings & Security") }}</div>
      <ul class="small-muted">
        <li>{{ _("Change password, security questions (2FA), accent color, and font.") }}</li>
      </ul>

      {% if is_admin %}
      <div class="fw-bold mb-2">{{ _("Admin") }}</div>
      <ul class="small-muted mb-0">
        <li>{{ _("Approve accounts and manage users.") }} {{ _("Admins can also manage Profiler bounties from the Bounty page.") }}</li>
      </ul>
      {% else %}
      <div class="small-muted mb-0">{{ _("Admin options are visible only to admins.") }}</div>
      {% endif %}


<div class="fw-bold mb-2">{{ _("Stories") }}</div>
<ul class="small-muted">
  <li>{{ _("Upload up to 5 stories per day. Stories are visible for 24 hours.") }}</li>
  <li>{{ _("Users with stories show a purple ring on their profile picture.") }}</li>
  <li>{{ _("You can react with emoji/text — the reaction is sent in chat together with the story.") }}</li>
</ul>

<div class="fw-bold mb-2">{{ _("Device auto‑login") }}</div>
<ul class="small-muted">
  <li>{{ _("After you login once, the app can remember this device so you don’t need credentials next time.") }}</li>
  <li>{{ _("On a new server/device, you can request approval from an admin (admins are shown by name).") }}</li>
  <li>{{ _("If 2FA is enabled on your account, auto‑login is disabled and you must sign in normally.") }}</li>
</ul>


      <hr class="my-3"/>

      <div class="fw-bold mb-2">{{ _("Face Detector") }}</div>
      <ul class="small-muted">
        <li><b>{{ _("Face Detector") }}</b> — {{ _("Open the built-in camera or upload a photo/video to detect faces.") }}</li>
        <li>{{ _("Use the save button to store a captured result in your Downloads/ButSystem/Face Detector folder when available.") }}</li>
        <li>{{ _("The top bar theme button still switches only between dark and light. Extra style presets are available in Settings.") }}</li>
      </ul>

      <hr class="my-3"/>

      <div class="small-muted mb-2">{{ _("Privacy notes") }}</div>
      <ul class="small-muted mb-0">
        <li><b>{{ _("Text messages") }}</b> {{ _("are encrypted at rest.") }}</li>
        <li><b>{{ _("Profiler") }}</b> {{ _("entries are stored encrypted; optional data can be expanded/collapsed.") }}</li>
        <li><b>{{ _("Files/voice") }}</b> {{ _("are stored on your device (not encrypted) for speed and compatibility.") }}</li>
      </ul>
    </div>
  </div>
</div>

<div id="imgModal" class="img-modal" aria-hidden="true"><img id="imgModalImg" src="" alt=""/></div>
<script nonce="{{ csp_nonce }}"  src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script nonce="{{ csp_nonce }}">
(function(){
  window.__butLogoDark = {{ logo_dark|tojson }};
  window.__butLogoLight = {{ logo_light|tojson }};
  const key = "but_theme_mode";
  function getSavedMode(){
    const raw = (localStorage.getItem(key) || "dark").toLowerCase();
    return (raw === "light" || raw === "dark" || raw === "system") ? raw : "dark";
  }
  function effectiveMode(mode){
    if(mode === "system"){
      try{
        return (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) ? "light" : "dark";
      }catch(e){ return "dark"; }
    }
    return mode === "light" ? "light" : "dark";
  }
  function apply(mode){
    const eff = effectiveMode(mode || getSavedMode());
    document.body.classList.toggle("light-theme", eff === "light");
    document.querySelectorAll('img[data-logo]').forEach(el => { el.src = (eff === 'light') ? window.__butLogoLight : window.__butLogoDark; });
  }
  function setMode(mode){
    const next = (mode === "light" || mode === "dark" || mode === "system") ? mode : "dark";
    localStorage.setItem(key, next);
    apply(next);
  }
  apply(getSavedMode());
  try{
    const mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: light)') : null;
    if(mq){
      const onChange = ()=>{ if(getSavedMode() === 'system') apply('system'); };
      if(mq.addEventListener) mq.addEventListener('change', onChange);
      else if(mq.addListener) mq.addListener(onChange);
    }
  }catch(e){}
  window.butSetThemeMode = setMode;
  window.butGetThemeMode = getSavedMode;
  window.butApplyTheme = apply;
})();
</script>

<script nonce="{{ csp_nonce }}">
(function(){
  // Convert UTC timestamps (data-utc) into the viewer's local time.
  // Works for server-rendered messages and newly appended AJAX messages.
  function fmt(utc){
    if(!utc) return "";
    try{
      const d = new Date(utc);
      if(isNaN(d.getTime())) return "";
      const now = new Date();
      const sameDay = (d.getFullYear()===now.getFullYear() && d.getMonth()===now.getMonth() && d.getDate()===now.getDate());
      return sameDay ? d.toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"}) : d.toLocaleString([], {year:"numeric", month:"2-digit", day:"2-digit", hour:"2-digit", minute:"2-digit"});
    }catch(e){ return ""; }
  }
  window.butFormatTimes = function(root){
    const scope = root || document;
    scope.querySelectorAll('[data-utc]').forEach(el=>{
      const utc = el.getAttribute('data-utc');
      const out = fmt(utc);
      if(out) el.textContent = out;
    });
  };
  document.addEventListener("DOMContentLoaded", ()=>{ try{ window.butFormatTimes(document); }catch(e){} });
})();
</script>

<script nonce="{{ csp_nonce }}">
(function(){
  // Optional section toggle label: ⬇️ when closed, ⬆️ when opened.
  function sync(d){
    const s = d.querySelector("summary.opt-summary");
    if(!s) return;
    const closed = s.getAttribute("data-closed") || "⬇️ Optional";
    const opened = s.getAttribute("data-open") || "⬆️ Optional";
    s.textContent = d.open ? opened : closed;
  }
  document.addEventListener("DOMContentLoaded", ()=>{
    document.querySelectorAll("details.opt-details").forEach(d=>{
      sync(d);
      d.addEventListener("toggle", ()=>sync(d));
    });
  });
})();
</script>

<script nonce="{{ csp_nonce }}">
(function(){
  // Click-to-expand images: tap to open full view, tap again / background / ESC to close.
  const modal = document.getElementById("imgModal");
  const img = document.getElementById("imgModalImg");
  function close(){
    try{
      if(!modal) return;
      modal.classList.remove("open");
      modal.setAttribute("aria-hidden","true");
      if(img) img.src = "";
    }catch(e){}
  }
  window.toggleImageModal = function(src){
    try{
      if(!modal || !img) return;
      if(modal.classList.contains("open")){ close(); return; }
      img.src = src || "";
      modal.classList.add("open");
      modal.setAttribute("aria-hidden","false");
    }catch(e){}
  };
  if(modal){
    modal.addEventListener("click", (e)=>{ if(e.target === modal) close(); });
  }
  document.addEventListener("keydown", (e)=>{ if(e.key === "Escape") close(); });
})();
</script>

<script nonce="{{ csp_nonce }}">
// Profiler delete safety: require typing the profile's first + last name.
window.butConfirmProfilerDelete = function(form){
  try{
    const first = (form && form.dataset && form.dataset.first) ? String(form.dataset.first) : "";
    const last  = (form && form.dataset && form.dataset.last)  ? String(form.dataset.last)  : "";
    const expected = (first + " " + last).trim().replace(/\s+/g, " ");
    if(!expected){
      return confirm({{ _('Delete this profile entry?')|tojson }});
    }
    const typed = prompt(`Type the profile first and last name to delete:\n${expected}`);
    if(!typed) return false;
    const norm = s => String(s||"").trim().replace(/\s+/g, " ").toLowerCase();
    if(norm(typed) !== norm(expected)){
      alert("Name doesn't match.");
      return false;
    }
    const inp = form.querySelector('input[name="confirm_full"]');
    if(inp) inp.value = typed.trim();
    return confirm({{ _('Delete this profile entry?')|tojson }});
  }catch(e){
    return false;
  }
};
</script>

<script nonce="{{ csp_nonce }}">
(function(){
  // Cross-browser viewport fix:
  // iOS Safari and some Android browsers report unstable 100vh values when the toolbar/keyboard changes.
  // We keep a CSS variable synced to the visual viewport for all pages, and use it more aggressively on chat screens.
  function setAppHeight(){
    try{
      const vv = window.visualViewport;
      const h = vv && vv.height ? vv.height : window.innerHeight;
      document.documentElement.style.setProperty("--app-height", Math.round(h) + "px");
    }catch(e){}
  }

  setAppHeight();
  window.addEventListener("resize", setAppHeight);
  window.addEventListener("orientationchange", ()=>{ setTimeout(setAppHeight, 120); });
  window.addEventListener("pageshow", ()=>{ setTimeout(setAppHeight, 0); setTimeout(setAppHeight, 160); });
  if(window.visualViewport){
    window.visualViewport.addEventListener("resize", setAppHeight);
    window.visualViewport.addEventListener("scroll", setAppHeight);
  }

  if(!document.body.classList.contains("chat-mode")) return;

  // When focusing the textarea, make sure the latest message is visible.
  const msgBox = document.getElementById("msgBox") || document.getElementById("gMsgBox");
  const bottom = document.getElementById("bottomSentinel");
  const ta = document.querySelector(".chat-composer textarea, #gSendForm textarea");
  function scrollBottom(){
    try{
      if(bottom && bottom.scrollIntoView) bottom.scrollIntoView({block:"end"});
      else if(msgBox) msgBox.scrollTop = msgBox.scrollHeight;
    }catch(e){}
  }
  if(ta) ta.addEventListener("focus", ()=>{ scrollBottom(); setTimeout(scrollBottom, 50); setTimeout(setAppHeight, 120); });
})();
</script>

{% block scripts %}{% endblock %}

<script nonce="{{ csp_nonce }}">

// CSRF: auto-inject hidden token into POST forms + attach token to same-origin fetch() mutations.
(function(){
  const meta = document.querySelector('meta[name="csrf-token"]');
  const token = meta ? (meta.content || "") : "";
  if(token){
    // Forms (classic submit)
    document.querySelectorAll('form[method="post"]').forEach((f)=>{
      if(!f.querySelector('input[name="csrf_token"]')){
        const i=document.createElement("input");
        i.type="hidden"; i.name="csrf_token"; i.value=token;
        f.appendChild(i);
      }
    });

    // Fetch (AJAX)
    const _fetch = window.fetch.bind(window);
    window.fetch = function(input, init){
      try{
        init = init || {};
        const method = String(init.method || "GET").toUpperCase();
        if(method !== "GET" && method !== "HEAD" && method !== "OPTIONS"){
          // same-origin only
          const url = (typeof input === "string") ? input : (input && input.url) ? input.url : "";
          const sameOrigin = (!url.startsWith("http")) || url.startsWith(window.location.origin);
          if(sameOrigin){
            const h = new Headers(init.headers || {});
            if(!h.get("X-CSRF-Token")) h.set("X-CSRF-Token", token);
            init.headers = h;
          }
        }
      }catch(e){}
      return _fetch(input, init);
    };
  }
})();
</script>
</body>

</html>
"""

TEMPLATES["landing.html"] = r"""
{% extends "base.html" %}
{% block content %}
<style>
  /* Make the welcome screen non-scrollable and fit in one viewport */
  main.container{padding:0!important;}
  body{overflow:hidden;}
  .welcome-card{max-height: calc(var(--app-height, 100vh) - 120px); overflow:hidden;}
  .welcome-card .alert{font-size:clamp(.72rem,2.6vw,.9rem); line-height:1.25;}
</style>
<div class="row justify-content-center">
  <div class="col-12 col-lg-7">
    <div class="card-soft p-4 p-md-5">
      <div class="d-flex flex-column flex-md-row justify-content-between align-items-start gap-3">
        <div>
          <h1 class="mb-1">ButSystem</h1>
          <div class="small-muted">Choose how you want to enter.</div>

          </div>
</div>
      <hr/>
      <div class="row g-3">
        <div class="col-12 col-md-6">
          <div class="card-soft p-3 h-100">
            <h4>Sign in</h4>
            <div class="small-muted mb-3">For existing users.</div>
            <a class="btn btn-accent w-100" href="{{ url_for('login') }}">Sign In</a>
          </div>
        </div>
        <div class="col-12 col-md-6">
          <div class="card-soft p-3 h-100">
            <h4>Request access</h4>
            <div class="small-muted mb-3">New account requests require admin approval.</div>
            <a class="btn btn-ghost w-100" href="{{ url_for('signup') }}">Request Access</a>
          </div>
        </div>
      </div>
      <div class="small-muted mt-3">
        Tip: Camera/mic features (if used) may require HTTPS — use the Cloudflared link.
      </div>
    </div>
  </div>
</div>
{% endblock %}
"""

TEMPLATES["loading.html"] = r"""{% extends "base.html" %}
{% block content %}
<style nonce="{{ csp_nonce }}">html,body{height:100%;overflow:hidden;} :root{--welcome-top-pad:clamp(8px,3.6vh,26px);} .page-wrap{height:calc(var(--app-height, 100vh) - var(--nav-h,64px));padding-top:var(--welcome-top-pad);box-sizing:border-box;} .welcome-card{max-height:calc(var(--app-height, 100vh) - var(--nav-h,64px) - 24px - var(--welcome-top-pad));overflow:hidden;} .welcome-card .alert-notice{font-size:clamp(0.72rem,1.25vh,0.92rem);line-height:1.25;} .welcome-card .h4{font-size:clamp(1.05rem,3.2vw,1.35rem);} .welcome-card .small-muted{font-size:clamp(0.78rem,2.4vw,0.95rem);} @media (max-height:720px){ .welcome-card{padding:1rem !important;} .welcome-card img[data-logo]{height:72px !important;width:72px !important;border-radius:20px !important;} .welcome-card .my-3{margin-top:.6rem !important;margin-bottom:.6rem !important;} .welcome-card .mt-3{margin-top:.7rem !important;} }</style>
<div class="d-flex align-items-start justify-content-center page-wrap">
  <div class="card-soft p-3 p-md-4 text-center welcome-card" style="max-width:560px;width:100%;">
    <div class="h4 mb-2">{{ _("Welcome") }} {{ display_name }}!</div>
    <div class="small-muted mb-2">{{ _("Entering…") }}</div>
    <div class="small-muted mb-2">{{ _("Please wait — this may take 10–20 seconds.") }}</div>
    <div class="d-flex justify-content-center my-3">
      <img data-logo src="{{ logo_dark }}" alt="logo" style="height:88px;width:88px;border-radius:24px;object-fit:cover;"/>
    </div>
    <div class="small-muted">{{ _("ButSystem is preparing your session.") }}</div>
    <div class="alert alert-notice text-start mt-3 mb-0" style="font-size:.92rem;">
      <div class="fw-bold mb-2">{{ _("Important notice") }}</div>
      <ul class="mb-0 ps-3">
        <li>{{ _("This system is NOT affiliated with police, military, or any government agency.") }}</li>
        <li>{{ _("It is for personal use only. Only create profiles for people who have given you explicit consent.") }}</li>
        <li>{{ _("Do not use this system for harassment, stalking, or any illegal activity. The creators and maintainers are not responsible for misuse.") }}</li>
</ul>
    </div>
  </div>
</div>

<script nonce="{{ csp_nonce }}">
(async ()=>{
  const t0 = Date.now();
  // Warm up session + online state while we show a friendly loading screen.
  try{ await fetch("{{ url_for('api_ping') }}", {method:"POST"}); }catch(e){}
  try{ await fetch("{{ url_for('api_bootstrap') }}"); }catch(e){}

  // Preload news into the server cache in the background (faster News page later).
  try{
    const qs = new URLSearchParams();
    qs.set("lang", "{{ lang }}");
    await fetch("{{ url_for('api_news') }}?" + qs.toString(), {cache:"no-store"});
  }catch(e){}

  // Keep the loading screen visible for a random 10–20 seconds (each login).
  const targetMs = 10000 + Math.floor(Math.random() * 10001); // 10,000–20,000
  const elapsed = Date.now() - t0;
  const remain = Math.max(0, targetMs - elapsed);
  setTimeout(()=>{ window.location.replace("{{ url_for('profiler') }}"); }, remain);
})();
</script>
{% endblock %}"""





TEMPLATES["news.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="d-flex flex-column flex-md-row justify-content-between align-items-start gap-2 mb-3">
  <div>
    <h3 class="mb-1">{{ _("News") }}</h3>
    <div class="small-muted">
      {% if lang=="el" %}
        Παγκόσμια νέα για κυβερνοασφάλεια, χάκινγκ, Termux, DedSec Project, ίντερνετ, κρύπτο και άλλα σχετικά θέματα.
      {% else %}
        Worldwide news about cybersecurity, hacking, Termux, the DedSec Project, the internet, crypto, and related topics.
      {% endif %}
    </div>
  </div>

  <div class="d-flex gap-2 flex-wrap align-items-center justify-content-end">
    <div class="input-group input-group-sm" style="max-width:420px;min-width:260px;">
      <input class="form-control" id="newsSearchInput"
             placeholder="{{ 'Search keywords…' if lang=='en' else 'Αναζήτηση λέξεων…' }}"
             autocomplete="off">
      <button class="btn btn-ghost" id="newsSearchBtn" type="button">{{ "Search" if lang=="en" else "Αναζήτηση" }}</button>
      <button class="btn btn-ghost" id="newsClearBtn" type="button" title="{{ 'Clear' if lang=='en' else 'Καθαρισμός' }}">✕</button>
    </div>

    <button class="btn btn-ghost btn-sm" id="newsCatsToggle" type="button">
      {{ "Categories ⬇️" if lang=="en" else "Κατηγορίες ⬇️" }}
    </button>

    <button class="btn btn-ghost" id="newsRefresh" type="button">{{ "Refresh" if lang=="en" else "Ανανέωση" }}</button>
  </div>
</div>

<div class="card-soft p-3 mb-3">
  <div id="newsCatsPanel" style="display:none;">
    <div class="d-flex flex-wrap gap-2" id="newsTopics">
      {% for t in topics %}
        <button class="btn {% if loop.first %}btn-accent{% else %}btn-ghost{% endif %} btn-sm"
                type="button" data-topic="{{ t.key }}">{{ t.label }}</button>
      {% endfor %}
    </div>
    <hr class="my-3"/>
  </div>

  <div class="small-muted" id="newsMeta"></div>
</div>

<div id="newsList" class="d-grid gap-2"></div>
<button class="btn btn-ghost w-100 mt-3" id="newsMore" type="button" style="display:none;">
  {{ "Load more" if lang=="en" else "Φόρτωσε περισσότερα" }}
</button>
{% endblock %}

{% block scripts %}
<script nonce="{{ csp_nonce }}">
(function(){
  const list = document.getElementById("newsList");
  const more = document.getElementById("newsMore");
  const meta = document.getElementById("newsMeta");
  const refreshBtn = document.getElementById("newsRefresh");
  const topicWrap = document.getElementById("newsTopics");

  const catsToggle = document.getElementById("newsCatsToggle");
  const catsPanel = document.getElementById("newsCatsPanel");

  const searchInput = document.getElementById("newsSearchInput");
  const searchBtn = document.getElementById("newsSearchBtn");
  const clearBtn = document.getElementById("newsClearBtn");

  let all = [];
  let topic = "all";
  let limit = 20;
  let searchTerm = "";

  function esc(s){
    return String(s||"").replace(/[&<>"']/g, c=>({ "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;" }[c]));
  }

  function getTopicLabel(key){
    try{
      const b = topicWrap ? topicWrap.querySelector(`button[data-topic="${CSS.escape(key)}"]`) : null;
      return b ? (b.textContent || key) : key;
    }catch(e){
      return key;
    }
  }

  function setCats(open){
    if(!catsToggle || !catsPanel) return;
    const isOpen = !!open;
    catsPanel.style.display = isOpen ? "block" : "none";
    catsToggle.textContent = isOpen
      ? {{ ('"Categories ⬆️"' if lang=="en" else '"Κατηγορίες ⬆️"')|safe }}
      : {{ ('"Categories ⬇️"' if lang=="en" else '"Κατηγορίες ⬇️"')|safe }};
  }

  function pickBtn(key){
    if(!topicWrap) return;
    topicWrap.querySelectorAll("button[data-topic]").forEach(b=>{
      const on = (b.dataset.topic === key);
      b.classList.toggle("btn-accent", on);
      b.classList.toggle("btn-ghost", !on);
    });
  }

  function matchesSearch(it){
    const t = (searchTerm||"").trim().toLowerCase();
    if(!t) return true;
    const hay = `${it.title||""} ${it.source||""} ${it.topic||""} ${it.url||""}`.toLowerCase();
    return hay.includes(t);
  }

  function filtered(){
    let items = all;
    if(topic !== "all"){
      items = items.filter(it => String(it.topic_key||"") === topic);
    }
    items = items.filter(matchesSearch);
    return items;
  }

  function render(){
    const items = filtered();
    const show = items.slice(0, limit);
    const tLabel = getTopicLabel(topic);

    const prefix = {{ ('"items"' if lang=="en" else '"άρθρα"')|safe }};
    const noNews = {{ ('"No news yet."' if lang=="en" else '"Δεν υπάρχουν νέα ακόμα."')|safe }};
    const topicTxt = {{ ('"Topic"' if lang=="en" else '"Κατηγορία"')|safe }};
    const searchTxt = {{ ('"Search"' if lang=="en" else '"Αναζήτηση"')|safe }};

    let metaStr = items.length ? `${items.length} ${prefix}` : noNews;
    metaStr += ` • ${topicTxt}: ${tLabel}`;
    if((searchTerm||"").trim()){
      metaStr += ` • ${searchTxt}: "${searchTerm.trim()}"`;
    }
    meta.textContent = metaStr;

    if(!show.length){
      list.innerHTML = `<div class="card-soft p-3 small-muted">{{ "No news found." if lang=="en" else "Δεν βρέθηκαν νέα." }}</div>`;
      more.style.display = "none";
      return;
    }

    list.innerHTML = show.map(it=>{
      const t = esc(it.title);
      const u = esc(it.url);
      const src = esc(it.source || "");
      const top = esc(it.topic || "");
      const pub = esc(it.published || "");
      return `
        <div class="card-soft p-3">
          <div class="fw-bold mb-1"><a href="${u}" target="_blank" rel="noreferrer" class="text-decoration-none">${t}</a></div>
          <div class="d-flex flex-wrap gap-2 align-items-center">
            <span class="pill online">${top || "News"}</span>
            ${src ? `<span class="small-muted">${src}</span>` : ""}
            ${pub ? `<span class="small-muted">• ${pub}</span>` : ""}
          </div>
        </div>
      `;
    }).join("");

    more.style.display = (items.length > limit) ? "block" : "none";
  }

  async function load(force){
    list.innerHTML = `<div class="card-soft p-3 small-muted">{{ "Loading…" if lang=="en" else "Φόρτωση…" }}</div>`;
    try{
      const qs = new URLSearchParams();
      qs.set("lang", "{{ lang }}");
      if(force) qs.set("force", "1");
      const r = await fetch("{{ url_for('api_news') }}?" + qs.toString(), {cache:"no-store"});
      const j = await r.json();
      all = (j && j.items) ? j.items : [];
    }catch(e){
      all = [];
    }
    limit = 20;
    render();
  }

  // Categories panel toggle
  if(catsToggle){
    catsToggle.addEventListener("click", ()=>{
      const openNow = (catsPanel && catsPanel.style.display !== "none");
      setCats(!openNow);
    });
  }

  // Topic buttons
  if(topicWrap){
    topicWrap.addEventListener("click", (e)=>{
      const b = e.target.closest("button[data-topic]");
      if(!b) return;
      topic = b.dataset.topic || "all";
      limit = 20;
      pickBtn(topic);
      render();
    });
  }

  // Search
  function applySearch(){
    searchTerm = (searchInput && searchInput.value) ? String(searchInput.value) : "";
    limit = 20;
    render();
  }
  if(searchBtn) searchBtn.addEventListener("click", applySearch);
  if(searchInput){
    searchInput.addEventListener("keydown", (e)=>{
      if(e.key === "Enter"){
        e.preventDefault();
        applySearch();
      }
    });
  }
  if(clearBtn){
    clearBtn.addEventListener("click", ()=>{
      if(searchInput) searchInput.value = "";
      searchTerm = "";
      limit = 20;
      render();
    });
  }

  // Load more
  if(more){
    more.addEventListener("click", ()=>{
      limit += 20;
      render();
    });
  }

  // Refresh
  if(refreshBtn){
    refreshBtn.addEventListener("click", ()=>load(true));
  }

  // Init
  pickBtn(topic);
  setCats(false);
  load(false);
})();
</script>
{% endblock %}

"""

TEMPLATES["profile_view.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="row g-3 justify-content-center">
  <div class="col-12 col-lg-7">
    <div class="card-soft p-4">
      <div class="d-flex justify-content-between align-items-start gap-3">
        <div class="d-flex gap-3 align-items-start">
          <div style="width:72px;height:72px;border-radius:16px;overflow:hidden;background:rgba(255,255,255,0.06);display:flex;align-items:center;justify-content:center;">
            <img src="{{ url_for('profile_pic', username=public.username) }}" alt="Profile picture"
                 class="pfp-clickable" style="width:72px;height:72px;object-fit:cover;display:block;border-radius:14px;" onclick="toggleImageModal(this.src)"
                 onerror='this.style.display="none";this.parentElement.innerHTML="<span class=&quot;small-muted&quot;>"+{{ _("No pic")|tojson }}+"</span>";'>
          </div>
          <div>
            <h3 class="mb-1">{{ public.nickname }}</h3>
            <div class="small-muted">@{{ public.username }}</div>
            
          </div>
        </div>
        <div class="d-flex gap-2">
          <a class="btn btn-accent" href="{{ url_for('profile_edit') }}">{{ _('Edit') }}</a>
        </div>
      </div>

      {% if public.bio %}
        <hr class="my-3"/>
        <div style="white-space:pre-wrap;">{{ public.bio }}</div>
      {% endif %}

      {% if public.links and public.links|length>0 %}
        <hr class="my-3"/>
        <div class="small-muted mb-2">{{ _('Links') }}</div>
        <div class="d-flex flex-column gap-2">
          {% for l in public.links %}
            <a class="link-plain" href="{{ l }}" target="_blank" rel="noopener">{{ l }}</a>
          {% endfor %}
        </div>
      {% endif %}
    </div>
  </div>
</div>
{% endblock %}
"""

TEMPLATES["login.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-12 col-lg-5">
    <div class="card-soft p-4">
      <h3 class="mb-1">{{ _('Sign in') }}</h3>
      <div class="small-muted mb-3">{{ _('Existing users only.') }}</div>
      <form method="post">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <div class="mb-3">
          <label class="form-label">{{ _('Username') }}</label>
          <input class="form-control" name="username" autocomplete="username" required>
        </div>
        <div class="mb-3">
          <label class="form-label">{{ _('Password') }}</label>
          <input class="form-control" name="password" type="password" autocomplete="current-password" required>
        </div>
        <button class="btn btn-accent w-100" type="submit">{{ _('Enter') }}</button>
      <div class="text-center mt-2"><a class="link-light" href="{{ url_for('recover') }}">{{ _('Forgot password?') }}</a></div>
      </form>

      <div class="small-muted mt-3">{{ _('Need access? Use') }} <a class="link-light" href="{{ url_for('signup') }}">{{ _('Request Access') }}</a> {{ _('and wait for approval.') }}</div>
      <div class="small-muted mt-1">{{ _('Already have an account but this is a new device/server?') }} <a class="link-light" href="{{ url_for('device_access') }}">{{ _('Request device auto‑login') }}</a>.</div>
    </div>
  </div>
</div>

{% endblock %}
"""

TEMPLATES["signup.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-12 col-lg-6">
    <div class="card-soft p-4">
      <h3 class="mb-1">Request Access</h3>
      <div class="small-muted mb-3">Confirm username and password twice.</div>
      <form method="post">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <div class="row g-3">
          <div class="col-12 col-md-6">
            <label class="form-label">Username</label>
            <input class="form-control" name="u1" required>
          </div>
          <div class="col-12 col-md-6">
            <label class="form-label">Confirm username</label>
            <input class="form-control" name="u2" required>
          </div>
          <div class="col-12 col-md-6">
            <label class="form-label">Password</label>
            <input class="form-control" name="p1" type="password" required>
          </div>
          <div class="col-12 col-md-6">
            <label class="form-label">Confirm password</label>
            <input class="form-control" name="p2" type="password" required>
          </div>
        </div>
        <button class="btn btn-accent w-100 mt-3" type="submit">Send Request</button>
      </form>
      <div class="small-muted mt-3">Your request is held until the admin approves it in the terminal.</div>
    </div>
  </div>
</div>
{% endblock %}
"""

TEMPLATES["device_access.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-12 col-lg-6">
    <div class="card-soft p-4">
      <h3 class="mb-1">{{ _("Device auto‑login") }}</h3>
      <div class="small-muted mb-3">
        {{ _("Request approval from admin to allow this device to auto‑login without entering credentials.") }}
        <div class="mt-1">{{ _("Note: If 2FA is enabled on your account, auto‑login is disabled and you must sign in normally.") }}</div>
      </div>

      <div class="card-soft p-3 mb-3">
        <div class="fw-semibold mb-2">{{ _("Admins") }}</div>
        <div class="d-flex flex-wrap gap-2">
          {% for a in admins %}
            <span class="pill online">@{{ a }}</span>
          {% endfor %}
          {% if not admins %}
            <span class="small-muted">—</span>
          {% endif %}
        </div>
      </div>

      <form method="post" action="{{ url_for('device_access') }}" class="mb-2">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <div class="mb-3">
          <label class="form-label">{{ _("Username") }}</label>
          <input class="form-control" name="username" autocomplete="username" required>
        </div>
        <button class="btn btn-accent w-100" type="submit">{{ _("Request approval") }}</button>
      </form>

      {% if status %}
        <div class="small-muted mt-2">
          {{ _("Status") }}: <span class="pill {% if status=='approved' %}online{% elif status=='pending' %}offline{% else %}offline{% endif %}">{{ status }}</span>
        </div>
      {% endif %}

      <div class="small-muted mt-3">
        {{ _("When approved, this page will log you in automatically.") }}
      </div>
    </div>
  </div>
</div>

<script>
(async function(){
  // poll for approval while user is on this page
  async function poll(){
    try{
      const r = await fetch("{{ url_for('device_access_poll') }}", {headers: {"Accept":"application/json"}});
      const j = await r.json();
      if(j && j.ok && j.status === "approved" && j.logged_in){
        window.location.href = "{{ url_for('loading') }}";
        return;
      }
    }catch(e){}
    setTimeout(poll, 4000);
  }
  setTimeout(poll, 1200);
})();
</script>
<script nonce="{{ csp_nonce }}">
(function(){
  async function postSimple(url){
    try{
      const r = await fetch(url, {method:"POST", headers:{"X-Requested-With":"XMLHttpRequest","X-CSRF-Token": {{ csrf_token|tojson }}}});
      const data = await r.json().catch(()=>({}));
      if(data && data.reload){ window.location.reload(); }
    }catch(e){}
  }
  const panicBtn = document.getElementById("panicBtn");
  const resumeBtn = document.getElementById("resumePrivacyBtn");
  const resumeInline = document.getElementById("resumePrivacyBtnInline");
  if(panicBtn){ panicBtn.addEventListener("click", function(ev){ ev.preventDefault(); postSimple("{{ url_for('privacy_panic') }}"); }); }
  if(resumeBtn){ resumeBtn.addEventListener("click", function(ev){ ev.preventDefault(); postSimple("{{ url_for('privacy_resume') }}"); }); }
  if(resumeInline){ resumeInline.addEventListener("click", function(ev){ ev.preventDefault(); postSimple("{{ url_for('privacy_resume') }}"); }); }
})();
</script>
{% endblock %}
"""



TEMPLATES["profile.html"] = r"""{% extends "base.html" %}
{% block content %}
<div class="row g-3">
  <div class="col-12 col-lg-5">
    <div class="card-soft p-4">
      <h3 class="mb-1">{{ _('My Profile') }}</h3>
      <div class="small-muted mb-3">Nickname is what others will see. Username stays the same.</div>

      <form method="post" action="{{ url_for('profile_save') }}">
        <div class="mb-3">
          <label class="form-label">{{ _('Nickname') }}</label>
          <input class="form-control" name="nickname" maxlength="48" value="{{ my_profile.nickname }}" required>
        </div>
        <div class="mb-3">
          <label class="form-label">{{ _('Bio') }}</label>
          <textarea class="form-control" name="bio" rows="4" maxlength="800">{{ my_profile.bio }}</textarea>
        </div>
        <div class="mb-3">
          <label class="form-label">Links (one per line, must start with http:// or https:// or mailto:)</label>
          <textarea class="form-control" name="links" rows="4" maxlength="2000">{% for l in my_profile.links %}{{ l }}{% if not loop.last %}\n{% endif %}{% endfor %}</textarea>
        </div>

        <hr class="my-3"/>

        <details class="opt-details">
          <summary class="opt-summary" data-closed="⬇️ Optional" data-open="⬆️ Optional">⬇️ Optional</summary>
          <div class="row g-2 mt-3">
  <div class="col-12 col-md-6">
    <label class="form-label">{{ _('Email') }}</label>
    <input class="form-control" name="email" maxlength="120" value="{{ my_profile.email }}">
  </div>
  <div class="col-12 col-md-6">
    <label class="form-label">Phone Number</label>
    <input class="form-control" name="phone" maxlength="40" value="{{ my_profile.phone }}" inputmode="tel">
  </div>
  <div class="col-12 col-md-6">
    <label class="form-label">{{ _('Car Model') }}</label>
    <input class="form-control" name="car_model" maxlength="80" value="{{ my_profile.car_model }}">
  </div>
  <div class="col-12 col-md-6">
    <label class="form-label">{{ _('Job') }}</label>
    <input class="form-control" name="job" maxlength="120" value="{{ my_profile.job }}">
  </div>
<div class="col-12 col-md-6">
    <label class="form-label">{{ _('ID Number') }}</label>
    <input class="form-control" name="id_number" maxlength="80" value="{{ my_profile.id_number }}">
  </div>
  <div class="col-12 col-md-6">
    <label class="form-label">{{ _('Tax Number') }}</label>
    <input class="form-control" name="tax_number" maxlength="80" value="{{ my_profile.tax_number }}">
  </div>

  <div class="col-12 col-md-6">
    <label class="form-label">{{ _('License Plate') }}</label>
    <input class="form-control" name="license_plate" maxlength="40" value="{{ my_profile.license_plate }}">
  </div>
  <div class="col-6 col-md-3">
    <label class="form-label">{{ _('Height') }}</label>
    <input class="form-control" name="height" maxlength="24" value="{{ my_profile.height }}" placeholder="e.g. 180 cm">
  </div>
  <div class="col-6 col-md-3">
    <label class="form-label">{{ _('Weight') }}</label>
    <input class="form-control" name="weight" maxlength="24" value="{{ my_profile.weight }}" placeholder="e.g. 75 kg">
  </div>

  <div class="col-12 col-md-6">
    <label class="form-label">{{ _('Hair Color') }}</label>
    <input class="form-control" name="hair_color" maxlength="40" value="{{ my_profile.hair_color }}">
  </div>
  <div class="col-12 col-md-6">
    <label class="form-label">{{ _('Eye Color') }}</label>
    <input class="form-control" name="eye_color" maxlength="40" value="{{ my_profile.eye_color }}">
  </div>

  
  <div class="col-12 col-md-4">
    <label class="form-label">{{ _('Country') }}</label>
    <input class="form-control" name="country" maxlength="80" value="{{ my_profile.country }}">
  </div>
  <div class="col-12 col-md-4">
    <label class="form-label">{{ _('State') }}</label>
    <input class="form-control" name="state" maxlength="80" value="{{ my_profile.state }}">
  </div>
  <div class="col-12 col-md-4">
    <label class="form-label">{{ _('Town') }}</label>
    <input class="form-control" name="town" maxlength="80" value="{{ my_profile.town }}">
  </div>

  <div class="col-12 col-md-6">
    <label class="form-label">{{ _('City') }}</label>
    <input class="form-control" name="city" maxlength="80" value="{{ my_profile.city }}">
  </div>
  <div class="col-12 col-md-6">
    <label class="form-label">{{ _('Address') }}</label>
    <input class="form-control" name="address" maxlength="200" value="{{ my_profile.address }}">
  </div>

  <div class="col-12 col-lg-6">
    <label class="form-label">Family Members (up to 10, one per line)</label>
    <textarea class="form-control" name="family_members" rows="4" maxlength="2000">{{ my_profile.family_members }}</textarea>
  </div>
  <div class="col-12 col-lg-6">
    <label class="form-label">Close Friends (up to 10, one per line)</label>
    <textarea class="form-control" name="close_friends" rows="4" maxlength="2000">{{ my_profile.close_friends }}</textarea>
  </div>
</div>
        </details>

        <button class="btn btn-accent w-100 mt-3" type="submit">{{ _('Save profile changes') }}</button>
      </form>
    </div>
  </div>

  <div class="col-12 col-lg-7">
    <div class="card-soft p-4">
      <h3 class="mb-3">{{ _('Profile Picture') }}</h3>
      {% if my_profile.has_pic %}
        <div class="d-flex align-items-center gap-3 mb-3">
          <img class="avatar pfp-clickable" style="width:64px;height:64px;" src="{{ url_for('profile_pic', username=user) }}" alt="pfp" onclick="toggleImageModal(this.src)"/>
          <div class="small-muted">{{ _('Visible to logged-in users.') }}</div>
        </div>
        <form method="post" action="{{ url_for('profile_pic_remove') }}">
          <button class="btn btn-ghost" type="submit" onclick='return confirm({{ _("Remove profile picture?")|tojson }})'>{{ _('Remove picture') }}</button>
        </form>
        <hr/>
      {% else %}
        <div class="small-muted mb-3">{{ _('No picture set yet.') }}</div>
      {% endif %}

      <form method="post" action="{{ url_for('profile_pic_upload') }}" enctype="multipart/form-data">
        <div class="mb-3">
          <label class="form-label">Upload picture (jpg/png/webp)</label>
          <input class="form-control" type="file" name="pic" accept="image/*" required>
        </div>
        <button class="btn btn-accent" type="submit">{{ _('Upload') }}</button>
      </form>

      <hr/>
      <div class="small-muted">{{ _('Your profile data is stored locally in ButSystem.') }}</div>
    </div>
  </div>
</div>
{% endblock %}"""




TEMPLATES["admin.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-start gap-2 mb-3">
  <div>
    <h3 class="mb-1">Admin</h3>
    <div class="small-muted">Kick users (force logout), delete accounts, manage admins, </div>
  </div>
  <div class="d-flex gap-2 flex-wrap">
    <a class="btn btn-ghost" href="{{ url_for('admin_logs') }}">{{ _('Logs') }}</a>
  </div>
</div>

<div class="card-soft p-3 mb-3">
  <form onsubmit="return false;" class="d-flex gap-2">
    <input id="groupsSearchInput" class="form-control" placeholder="{{ _('Search groups...') }}">
    <button class="btn btn-ghost" type="button" id="groupsSearchBtn">{{ _('Search') }}</button>
  </form>
</div>

<div class="card-soft p-3">
  <div class="table-responsive">
    <table class="table table-sm align-middle mb-0">
      <thead>
        <tr>
          <th>User</th>
          <th>Role</th>
          <th>Created</th>
          <th class="text-end">{{ _('Actions') }}</th>
        </tr>
      </thead>
      <tbody>
        {% for u in users %}
        <tr>
          <td><span class="mono">@{{ u.username }}</span></td>
          <td>{% if u.is_admin %}<span class="pill online">admin</span>{% else %}<span class="pill offline">user</span>{% endif %}</td>
          <td class="small-muted">{{ u.created_at }}</td>
          <td class="text-end">
            {% if u.username != me %}
            {% if u.is_admin %}
            <form class="d-inline" method="post" action="{{ url_for('admin_demote') }}" onsubmit="return confirm('Remove admin from @{{ u.username }}?');">
              <input type="hidden" name="username" value="{{ u.username }}"/>
              <button class="btn btn-sm btn-ghost" type="submit">Demote</button>
            </form>
            {% else %}
            <form class="d-inline" method="post" action="{{ url_for('admin_promote') }}" onsubmit="return confirm('Make @{{ u.username }} an admin on this device?');">
              <input type="hidden" name="username" value="{{ u.username }}"/>
              <button class="btn btn-sm btn-ghost" type="submit">Promote</button>
            </form>
            {% endif %}
            <form class="d-inline" method="post" action="{{ url_for('admin_kick_user') }}">
              <input type="hidden" name="username" value="{{ u.username }}"/>
              <button class="btn btn-sm btn-ghost" type="submit">Kick</button>
            </form>
            <form class="d-inline" method="post" action="{{ url_for('admin_delete_user') }}" onsubmit="return confirm('Delete account @{{ u.username }}? This removes their login + public profile.');">
              <input type="hidden" name="username" value="{{ u.username }}"/>
              <button class="btn btn-sm btn-danger" type="submit">{{ _('Delete') }}</button>
            </form>
            <a class="btn btn-sm btn-ghost" href="{{ url_for('admin_user_files', username=u.username) }}">Files</a>
            {% else %}
            <span class="small-muted">—</span>
            {% endif %}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>


<div class="card-soft p-3 mt-3">
  <h5 class="mb-2">{{ _("Device access requests") }}</h5>
  <div class="small-muted mb-3">{{ _("Approve devices that request auto‑login without credentials. (2FA accounts must sign in normally.)") }}</div>

  <div class="card-soft p-3 mb-3">
    <form onsubmit="return false;" class="d-flex gap-2">
      <input id="devReqSearchInput" class="form-control" placeholder="{{ _('Search device requests...') }}">
      <button class="btn btn-ghost" type="button" id="devReqSearchBtn">{{ _('Search') }}</button>
    </form>
  </div>

  <div class="table-responsive">
    <table class="table table-sm align-middle mb-0" id="devReqTable">
      <thead>
        <tr>
          <th>{{ _("User") }}</th>
          <th>{{ _("Requested at") }}</th>
          <th>{{ _("IP") }}</th>
          <th class="text-end">{{ _("Actions") }}</th>
        </tr>
      </thead>
      <tbody>
        {% for r in devreq %}
        <tr>
          <td><span class="mono">@{{ r.username }}</span><div class="small-muted">fp: {{ r.device_fp[:12] }}…</div></td>
          <td class="small-muted">{{ r.requested_at }}</td>
          <td class="small-muted">{{ r.requested_ip }}</td>
          <td class="text-end">
            <form class="d-inline" method="post" action="{{ url_for('admin_device_approve') }}" onsubmit="return confirm('Approve this device for @{{ r.username }}?');">
              <input type="hidden" name="req_id" value="{{ r.id }}"/>
              <button class="btn btn-sm btn-ghost" type="submit">{{ _("Approve") }}</button>
            </form>
            <form class="d-inline" method="post" action="{{ url_for('admin_device_deny') }}" onsubmit="return confirm('Deny this device request for @{{ r.username }}?');">
              <input type="hidden" name="req_id" value="{{ r.id }}"/>
              <button class="btn btn-sm btn-danger" type="submit">{{ _("Deny") }}</button>
            </form>
          </td>
        </tr>
        {% else %}
        <tr><td colspan="4" class="small-muted">—</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>


<div class="card-soft p-3 mt-3">
  <h5 class="mb-2 text-danger">Danger zone</h5>
  <div class="small-muted mb-3">Admin-only actions. Use carefully.</div>

  <div class="row g-3">
    <div class="col-12 col-lg-6">
      <div class="p-3 rounded-3 border border-danger border-opacity-25">
        <div class="fw-semibold mb-1">Delete my admin account</div>
        <div class="small-muted mb-2">This removes your login + public profile but does <b>not</b> delete stored files.</div>
        <form method="post" action="{{ url_for('admin_delete_me') }}" onsubmit="return confirm('Delete your admin account? You will be logged out.');">
          <div class="mb-2">
            <input class="form-control form-control-sm" type="password" name="password" placeholder="Confirm password" required>
          </div>
          <button class="btn btn-sm btn-outline-danger" type="submit">Delete my account</button>
        </form>
      </div>
    </div>

    <div class="col-12 col-lg-6">
      <div class="p-3 rounded-3 border border-danger border-opacity-25">
        <div class="fw-semibold mb-1">Delete ButSystem (self‑destruct)</div>
        <div class="small-muted mb-2">Deletes the entire app data folder from phone storage. Requires username + password.</div>
        <form method="post" action="{{ url_for('admin_self_destruct') }}" onsubmit="return confirm('This will delete ALL ButSystem data from storage. Continue?');">
          <div class="row g-2 mb-2">
            <div class="col-6"><input class="form-control form-control-sm" name="username" placeholder="Username" required></div>
            <div class="col-6"><input class="form-control form-control-sm" type="password" name="password" placeholder="Password" required></div>
          </div>
          <button class="btn btn-sm btn-danger" type="submit">Self‑destruct</button>
        </form>
      </div>
    </div>
  </div>
</div>

{% endblock %}
"""
TEMPLATES["admin_logs.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-start gap-2 mb-3 flex-wrap">
  <div>
    <h3 class="mb-1">{{ _("Admin logs") }}</h3>
    <div class="small-muted">{{ _("View log files stored by ButSystem.") }}</div>
  </div>
  <a class="btn btn-ghost" href="{{ url_for('admin_panel') }}">{{ _("Back") }}</a>
</div>
<div class="row g-3">
  <div class="col-12 col-lg-4">
    <div class="card-soft p-3">
      <div class="fw-semibold mb-2">{{ _("Log files") }}</div>
      {% if files %}
      <div class="d-grid gap-2">
        {% for f in files %}
        <a class="btn btn-ghost text-start" href="{{ url_for('admin_logs', name=f.name) }}">{{ f.name }} <span class="small-muted">({{ f.size }} B)</span></a>
        {% endfor %}
      </div>
      {% else %}
      <div class="small-muted">{{ _("No log files found.") }}</div>
      {% endif %}
    </div>
  </div>
  <div class="col-12 col-lg-8">
    <div class="card-soft p-3">
      <div class="fw-semibold mb-2">{{ selected_name or _("Select a log") }}</div>
      <pre style="white-space:pre-wrap;word-break:break-word;max-height:70dvh;overflow:auto;margin:0">{{ selected_content or _("Choose a log file from the left.") }}</pre>
    </div>
  </div>
</div>
{% endblock %}
"""

TEMPLATES["files.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="d-flex flex-column flex-md-row justify-content-between align-items-start gap-2 mb-3">
  <div>
    <h3 class="mb-1">Files</h3>
    <div class="small-muted">Path: /{{ relpath }} <span class="badge badge-soft ms-2">Encrypted</span></div>
  </div>
  <div class="d-flex flex-wrap gap-2">
    <a class="btn btn-ghost" href="{{ url_for('files', p=parent_relpath, sort=sort, order=order) }}">Up</a>
    <button class="btn btn-ghost" data-bs-toggle="collapse" data-bs-target="#mkdirBox">New folder</button>
    <button class="btn btn-accent" data-bs-toggle="collapse" data-bs-target="#uploadBox">{{ _('Upload') }}</button>

    <form class="d-flex gap-2" method="get" action="{{ url_for('files') }}">
      <input type="hidden" name="p" value="{{ relpath }}">
      <select class="form-select" name="sort">
        <option value="name" {% if sort=='name' %}selected{% endif %}>Sort: name</option>
        <option value="mtime" {% if sort=='mtime' %}selected{% endif %}>Sort: modified</option>
        <option value="size" {% if sort=='size' %}selected{% endif %}>Sort: size</option>
        <option value="type" {% if sort=='type' %}selected{% endif %}>Sort: type</option>
      </select>
      <select class="form-select" name="order">
        <option value="asc" {% if order=='asc' %}selected{% endif %}>Asc</option>
        <option value="desc" {% if order=='desc' %}selected{% endif %}>Desc</option>
      </select>
      <button class="btn btn-ghost" type="submit">Apply</button>
    </form>
  </div>
</div>

<div id="mkdirBox" class="collapse mb-3">
  <div class="card-soft p-3">
    <form method="post" action="{{ url_for('mkdir') }}">
      <input type="hidden" name="p" value="{{ relpath }}">
      <div class="row g-2 align-items-end">
        <div class="col-12 col-md-8">
          <label class="form-label">Folder name</label>
          <input class="form-control" name="name" required>
        </div>
        <div class="col-12 col-md-4">
          <button class="btn btn-ghost w-100" type="submit">Create</button>
        </div>
      </div>
    </form>
  </div>
</div>

<div id="uploadBox" class="collapse mb-3">
  <div class="card-soft p-3">
    <form id="vaultUploadForm" method="post" action="{{ url_for('upload') }}" enctype="multipart/form-data">
      <input type="hidden" name="p" value="{{ relpath }}">
      <div class="row g-2 align-items-end">
        <div class="col-12 col-md-8">
          <label class="form-label">Choose file</label>
          <input id="vaultFileInput" class="form-control" type="file" name="file" required>
        </div>
        <div class="col-12 col-md-4">
          <button class="btn btn-accent w-100" type="submit">{{ _('Upload') }}</button>
        </div>
      </div>
      <div id="vaultUploadProg" class="mt-3" style="display:none;">
  <div class="progress">
    <div id="vaultUploadBar" class="progress-bar" role="progressbar" style="width:0%"></div>
  </div>
  <div id="vaultUploadText" class="small-muted mt-2">Uploading…</div>
</div>
<div class="small-muted mt-2">Vault files are stored after upload.</div>
    </form>
  </div>
</div>

<div class="card-soft p-3">
  <div class="table-responsive">
    <table class="table table-dark table-striped align-middle mb-0">
      <thead>
        <tr>
          <th style="width:40%">{{ _('Name') }}</th>
          <th style="width:18%">Type</th>
          <th style="width:12%">Size</th>
          <th style="width:18%">Modified</th>
          <th style="width:12%">{{ _('Actions') }}</th>
        </tr>
      </thead>
      <tbody>
        {% for e in entries %}
          <tr>
            <td>
              {% if e.is_dir %}
                📁 <a href="{{ url_for('files', p=child_path(relpath, e.name), sort=sort, order=order) }}">{{ e.name }}</a>
              {% else %}
                📄 {{ e.name }}
              {% endif %}
            </td>
            <td><span class="small-muted">{{ e.kind }}</span></td>
            <td>{{ e.size_h }}</td>
            <td class="small-muted">{{ e.mtime_h }}</td>
            <td class="d-flex flex-wrap gap-2">
              {% if e.is_dir %}
                <form method="post" action="{{ url_for('delete') }}" style="display:inline;">
                  <input type="hidden" name="p" value="{{ child_path(relpath, e.name) }}">
                  <input type="hidden" name="is_dir" value="1">
                  <button class="btn btn-sm btn-ghost" type="submit" onclick="return confirm('Delete folder and everything inside?')">{{ _('Delete') }}</button>
                </form>
              {% else %}
                <a class="btn btn-sm btn-ghost" href="{{ url_for('view_file', p=child_path(relpath, e.name)) }}" target="_blank">Open</a>
                <a class="btn btn-sm btn-ghost" href="{{ url_for('download', p=child_path(relpath, e.name)) }}">{{ _('Download') }}</a>
                <form method="post" action="{{ url_for('delete') }}" style="display:inline;">
                  <input type="hidden" name="p" value="{{ child_path(relpath, e.name) }}">
                  <input type="hidden" name="is_dir" value="0">
                  <button class="btn btn-sm btn-ghost" type="submit" onclick="return confirm('Delete file?')">{{ _('Delete') }}</button>
                </form>
              {% endif %}
            </td>
          </tr>
        {% endfor %}
        {% if not entries %}
          <tr><td colspan="5" class="small-muted">Empty folder.</td></tr>
        {% endif %}
      </tbody>
    </table>
  </div>
</div>
<script nonce="{{ csp_nonce }}">

const MSG_UPLOAD_FAIL = {{ _("Upload failed. Please retry.")|tojson }};
const MSG_DONE_REFRESH = {{ _("Done. Refreshing…")|tojson }};
(function(){
  const form = document.getElementById('vaultUploadForm');
  const input = document.getElementById('vaultFileInput');
  const prog = document.getElementById('vaultUploadProg');
  const bar = document.getElementById('vaultUploadBar');
  const txt = document.getElementById('vaultUploadText');
  if(!form || !input || !window.fetch) return;

  const csrf = (document.querySelector('meta[name="csrf-token"]')||{}).content || '';

  async function jpost(url, obj){
    const r = await fetch(url, {
      method:'POST',
      headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},
      body: JSON.stringify(obj||{})
    });
    return {ok:r.ok, json: await r.json().catch(()=>({}))};
  }

  form.addEventListener('submit', async (e) => {
    const file = input.files && input.files[0];
    if(!file) return;
    // Use chunked uploader for larger files; fallback to normal POST for tiny files.
    if(file.size < 2*1024*1024) return;

    e.preventDefault();
    prog.style.display = '';
    bar.style.width = '0%';
    txt.textContent = 'Starting…';

    const rel = (form.querySelector('input[name="p"]')||{}).value || '';
    const chunkSize = 8 * 1024 * 1024; // 8 MiB
    const totalChunks = Math.max(1, Math.ceil(file.size / chunkSize));

    const init = await jpost('{{ url_for("api_upload_init") }}', {p: rel, filename: file.name, total_chunks: totalChunks});
    if(!init.ok || !init.json.ok){
      txt.textContent = 'Init failed. Falling back…';
      form.submit();
      return;
    }
    const uploadId = init.json.upload_id;

    for(let i=0;i<totalChunks;i++){
      const start = i*chunkSize;
      const end = Math.min(file.size, start+chunkSize);
      const blob = file.slice(start, end);
      const fd = new FormData();
      fd.append('upload_id', uploadId);
      fd.append('index', String(i));
      fd.append('total', String(totalChunks));
      fd.append('chunk', blob, file.name + '.part');

      txt.textContent = `Uploading… ${i+1}/${totalChunks}`;
      const r = await fetch('{{ url_for("api_upload_chunk") }}', {method:'POST', headers:{'X-CSRF-Token':csrf}, body: fd});
      const j = await r.json().catch(()=>({}));
      if(!r.ok || !j.ok){
        txt.textContent = MSG_UPLOAD_FAIL;
        return;
      }
      const pct = Math.round(((i+1)/totalChunks)*100);
      bar.style.width = pct + '%';
    }

    txt.textContent = MSG_DONE_REFRESH;
    window.location.reload();
  });
})();
</script>
{% endblock %}
"""

TEMPLATES["chats.html"] = r"""{% extends "base.html" %}
{% block content %}
<div class="chat-shell">
  <div class="chat-list">
    <div class="card-soft p-3 mb-3">
      <h4 class="mb-1">Chats</h4>
      <div class="small-muted">Online Now {{ online_count }} / Offline Now {{ offline_count }}</div>
      <div class="small-muted">Type to search users (username or nickname)</div>

      <div class="suggest-wrap mt-2">
        <input id="userSearch" class="form-control" placeholder="Search user..." autocomplete="off">
        <div id="suggestBox" class="suggest-list"></div>
      </div>
      <div class="d-flex gap-2 mt-2 flex-wrap">
        <a class="btn btn-ghost btn-sm" href="{{ url_for('profiler') }}">{{ _('Back') }}</a>
        <a class="btn btn-ghost btn-sm" href="{{ url_for('groups') }}">Groups</a>
      </div>
    </div>

    <div class="card-soft p-3">
      <div class="small-muted mb-2">{{ _("Pinned") }}</div>
      <a class="user-item text-decoration-none" href="{{ url_for('chat_with', username=me) }}">
        <div class="avatar-wrap {% if has_active_story(me) %}story-ring{% endif %}">
          {% if self_has_pic %}
            <img class="avatar-img pfp-clickable" src="{{ url_for('profile_pic', username=me) }}" alt="" onclick="toggleImageModal(this.src)">
          {% else %}
            <div class="avatar-fallback"><img data-logo class="avatar-img" src="{{ logo_dark }}" alt="logo"></div>
          {% endif %}
        </div>
        <div class="flex-grow-1">
          <div class="fw-bold">{{ _("Saved messages") }}</div>
          <div class="small-muted">@{{ me }}</div>
        </div>
        <span class="pill online">📌</span>
      </a>

      <hr class="my-3"/>

      <div class="small-muted mb-2">Online</div>
      {% if users|selectattr("online")|list %}
        {% for u in users if u.online %}
          <a class="user-item text-decoration-none" href="{{ url_for('chat_with', username=u.username) }}">
            <div class="avatar-wrap {% if has_active_story(u.username) %}story-ring{% endif %}">
              {% if u.has_pic %}
                <img class="avatar-img pfp-clickable" src="{{ url_for('profile_pic', username=u.username) }}" alt="" onclick="toggleImageModal(this.src)">
              {% else %}
                <div class="avatar-fallback"><img data-logo class="avatar-img" src="{{ logo_dark }}" alt="logo"></div>
              {% endif %}
            </div>
            <div class="flex-grow-1">
              <div class="fw-bold">{{ u.nickname }}</div>
              <div class="small-muted">@{{ u.username }}</div>
            </div>
            {% set uc = unread_map.get(u.username, 0) %}
            <span class="pill online">Online</span>
            {% if uc and uc>0 %}<span class="notif-badge ms-2">{{ uc }}</span>{% endif %}
          </a>
        {% endfor %}
      {% else %}
        <div class="small-muted">Online Now 0</div>
      {% endif %}

      <hr class="my-3"/>

      <div class="small-muted mb-2">Offline</div>
      {% if users|rejectattr("online")|list %}
        {% for u in users if not u.online %}
          <a class="user-item text-decoration-none" href="{{ url_for('chat_with', username=u.username) }}">
            <div class="avatar-wrap {% if has_active_story(u.username) %}story-ring{% endif %}">
              {% if u.has_pic %}
                <img class="avatar-img pfp-clickable" src="{{ url_for('profile_pic', username=u.username) }}" alt="" onclick="toggleImageModal(this.src)">
              {% else %}
                <div class="avatar-fallback"><img data-logo class="avatar-img" src="{{ logo_dark }}" alt="logo"></div>
              {% endif %}
            </div>
            <div class="flex-grow-1">
              <div class="fw-bold">{{ u.nickname }}</div>
              <div class="small-muted">@{{ u.username }}</div>
            </div>
            {% set uc = unread_map.get(u.username, 0) %}
            <span class="pill offline">Offline</span>
            {% if uc and uc>0 %}<span class="notif-badge ms-2">{{ uc }}</span>{% endif %}
          </a>
        {% endfor %}
      {% else %}
        <div class="small-muted">Offline Now 0</div>
      {% endif %}
    </div>
  </div>

  <div class="chat-thread"></div>
</div>
{% endblock %}

{% block scripts %}
<script nonce="{{ csp_nonce }}">
(function(){
  const inp = document.getElementById("userSearch");
  const box = document.getElementById("suggestBox");
  let t=null;

  function esc(s){ return (s||"").replace(/[&<>"]/g, c=>({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;" }[c])); }

  function item(u){
    const pic = u.has_pic ? `<img class="avatar-img pfp-clickable" src="/profile/pic/${encodeURIComponent(u.username)}" alt="" onclick="toggleImageModal(this.src)">` : `<div class="avatar-fallback"><img data-logo class="avatar-img" src="{{ logo_dark }}" alt="logo"></div>`;
    const status = u.online ? `<span class="pill online">Online</span>` : `<span class="pill offline">Offline</span>`;
    const ringCls = u.has_story ? " story-ring" : "";
    return `<a class="suggest-item" href="/chat/${encodeURIComponent(u.username)}">
      <div class="d-flex align-items-center gap-2 flex-wrap justify-content-end">
        <div class="avatar-wrap${ringCls}">${pic}</div>
        <div class="text-start">
          <div class="suggest-name">${esc(u.nickname||u.username)}</div>
          <div class="small-muted">@${esc(u.username)}</div>
        </div>
      </div>
      ${status}
    </a>`;
  }

  async function query(q){
    const r = await fetch(`/api/users?q=${encodeURIComponent(q)}`);
    if(!r.ok) return;
    const data = await r.json();
    const users = data.users || [];
    if(!users.length){ box.style.display="none"; box.innerHTML=""; return; }
    box.innerHTML = users.map(item).join("");
    box.style.display="block";
  }

  if(inp){
    inp.addEventListener("input", ()=>{
      const q = inp.value.trim();
      if(t) clearTimeout(t);
      if(!q){ box.style.display="none"; box.innerHTML=""; return; }
      t=setTimeout(()=>query(q), 120);
    });
    inp.addEventListener("focus", ()=>{ const q=inp.value.trim(); if(q) query(q); });
    inp.addEventListener("blur", ()=>setTimeout(()=>{ box.style.display="none"; }, 180));
  }
})();
</script>
{% endblock %}"""

TEMPLATES["chat_thread.html"] = r"""{% extends "base.html" %}
{% block content %}
<div class="chat-shell">
  <div class="chat-list">
    <div class="card-soft p-3 mb-3">
      <h4 class="mb-1">Chats</h4>
      <div class="small-muted">Online Now {{ online_count }} / Offline Now {{ offline_count }}</div>
      <div class="small-muted">Type to search users (username or nickname)</div>
      <div class="suggest-wrap mt-2">
        <input id="userSearch" class="form-control" placeholder="Search user..." autocomplete="off">
        <div id="suggestBox" class="suggest-list"></div>
      </div>
      <div class="d-flex gap-2 mt-2 flex-wrap">
        <a class="btn btn-ghost btn-sm" href="{{ url_for('chats') }}">{{ _('Back') }}</a>
        <a class="btn btn-ghost btn-sm" href="{{ url_for('profiler') }}">Home</a>
      </div>
    </div>

    <div class="card-soft p-3">
      <div class="small-muted mb-2">{{ _("Pinned") }}</div>
      <a class="user-item text-decoration-none {% if peer==me %}active{% endif %}" href="{{ url_for('chat_with', username=me) }}">
        <div class="avatar-wrap {% if has_active_story(me) %}story-ring{% endif %}">
          {% if self_has_pic %}
            <img class="avatar-img pfp-clickable" src="{{ url_for('profile_pic', username=me) }}" alt="" onclick="toggleImageModal(this.src)">
          {% else %}
            <div class="avatar-fallback"><img data-logo class="avatar-img" src="{{ logo_dark }}" alt="logo"></div>
          {% endif %}
        </div>
        <div class="flex-grow-1">
          <div class="fw-bold">{{ _("Saved messages") }}</div>
          <div class="small-muted">@{{ me }}</div>
        </div>
        <span class="pill online">📌</span>
      </a>

      <hr class="my-3"/>

      <div class="small-muted mb-2">Online</div>
      {% if users|selectattr("online")|list %}
        {% for u in users if u.online %}
          <a class="user-item text-decoration-none {% if u.username==peer %}active{% endif %}" href="{{ url_for('chat_with', username=u.username) }}">
            <div class="avatar-wrap {% if has_active_story(u.username) %}story-ring{% endif %}">
              {% if u.has_pic %}
                <img class="avatar-img pfp-clickable" src="{{ url_for('profile_pic', username=u.username) }}" alt="" onclick="toggleImageModal(this.src)">
              {% else %}
                <div class="avatar-fallback"><img data-logo class="avatar-img" src="{{ logo_dark }}" alt="logo"></div>
              {% endif %}
            </div>
            <div class="flex-grow-1">
              <div class="fw-bold">{{ u.nickname }}</div>
              <div class="small-muted">@{{ u.username }}</div>
            </div>
            {% set uc = unread_map.get(u.username, 0) %}
            <span class="pill online">Online</span>
            {% if uc and uc>0 %}<span class="notif-badge ms-2">{{ uc }}</span>{% endif %}
          </a>
        {% endfor %}
      {% else %}
        <div class="small-muted">Online Now 0</div>
      {% endif %}

      <hr class="my-3"/>

      <div class="small-muted mb-2">Offline</div>
      {% if users|rejectattr("online")|list %}
        {% for u in users if not u.online %}
          <a class="user-item text-decoration-none {% if u.username==peer %}active{% endif %}" href="{{ url_for('chat_with', username=u.username) }}">
            <div class="avatar-wrap {% if has_active_story(u.username) %}story-ring{% endif %}">
              {% if u.has_pic %}
                <img class="avatar-img pfp-clickable" src="{{ url_for('profile_pic', username=u.username) }}" alt="" onclick="toggleImageModal(this.src)">
              {% else %}
                <div class="avatar-fallback"><img data-logo class="avatar-img" src="{{ logo_dark }}" alt="logo"></div>
              {% endif %}
            </div>
            <div class="flex-grow-1">
              <div class="fw-bold">{{ u.nickname }}</div>
              <div class="small-muted">@{{ u.username }}</div>
            </div>
            {% set uc = unread_map.get(u.username, 0) %}
            <span class="pill offline">Offline</span>
            {% if uc and uc>0 %}<span class="notif-badge ms-2">{{ uc }}</span>{% endif %}
          </a>
        {% endfor %}
      {% else %}
        <div class="small-muted">Offline Now 0</div>
      {% endif %}
    </div>
  </div>

  <div class="chat-thread">
    <div class="card-soft p-3">
      <div class="d-flex justify-content-between align-items-start gap-2">
        <div>
          <div class="d-flex align-items-center gap-2 flex-wrap">
            {% if peer_display|lower != "saved messages" %}<h4 class="mb-0">{{ peer_display }}</h4>{% endif %}
            {% if not is_self_chat %}<span class="small-muted" style="white-space:nowrap">{{ "🟢 online" if peer_online else "⚫ offline" }}</span>{% endif %}
            {% if not is_self_chat and has_active_story(peer) %}<a class="btn btn-ghost btn-sm" href="{{ url_for('story_view_user', username=peer) }}">🟣 {{ _('Story') }}</a>{% endif %}
          </div>
        </div>
</div>
    </div>

    <div class="card-soft p-3 mt-3" style="height:60vh; overflow:auto;" id="msgBox">
      {% for m in messages %}
        <div class="msg-row {{ 'me' if m.sender==me else 'them' }}">
          <div class="bubble {{ 'me' if m.sender==me else 'them' }}" data-mid="{{ m.id }}" data-kind="{{ m.kind }}" data-sender="{{ m.sender }}">
            {% if m.kind == "text" %}
              <span class="msg-text">{{ m.body }}</span>
              {% if m.edited_at_local %}<span class="small-muted"> (edited)</span>{% endif %}
            {% elif m.kind == "voice" %}
              <audio controls preload="metadata">
                <source src="{{ url_for('dm_voice_stream', vid=m.voice_id) }}" type="{{ m.voice_mime }}">
              </audio>
            {% elif m.kind == "file" %}
              {% if m.file_is_image %}
                <img src="{{ url_for('dm_file_stream', fid=m.file_id) }}" alt="{{ m.file_name }}"/>
              {% elif m.file_is_video %}
                <video controls playsinline preload="metadata">
                  <source src="{{ url_for('dm_file_stream', fid=m.file_id) }}" type="{{ m.file_mime }}">
                </video>
              {% elif m.file_is_audio %}
                <audio controls preload="metadata">
                  <source src="{{ url_for('dm_file_stream', fid=m.file_id) }}" type="{{ m.file_mime }}">
                </audio>
              {% else %}
                <a class="file-chip" href="{{ url_for('dm_file_download', fid=m.file_id) }}">📎 {{ m.file_name }}</a>
                <div class="small-muted mt-1">{{ m.file_size_h }}</div>
              {% endif %}
            {% else %}
              <span class="msg-text">{{ m.body }}</span>
            {% endif %}
          </div>
          <div class="msg-meta">
    <span class="ts" data-utc="{{ m.created_at_utc }}">{{ m.created_at_local }}</span>{% if m.deleted %} • deleted{% endif %}
    {% if m.sender==me %}
      <span class="dm-ticks {% if m.read_at_local %}seen{% elif m.delivered_at_local %}delivered{% else %}sent{% endif %}" data-mid="{{ m.id }}"
            title="{% if m.read_at_local %}Seen {{ m.read_at_local }}{% elif m.delivered_at_local %}Delivered{% else %}Sent{% endif %}">
        {% if m.read_at_local %}✔✔{% elif m.delivered_at_local %}✔✔{% else %}✔{% endif %}
      </span>
    {% endif %}
  </div>
        </div>
      {% endfor %}
    </div>

    <div class="card-soft p-3 mt-3">
      <form method="post" action="{{ url_for('dm_send', username=peer) }}" enctype="multipart/form-data" id="sendForm">
        <div class="d-flex gap-2 align-items-end">
          <textarea class="form-control msg-input" name="body" rows="1" placeholder="Message..." style="resize:none;"></textarea>
          <button class="btn btn-accent btn-send" type="submit" aria-label="Send" title="Send">➡️</button>
        </div>

      <div class="composer-actions mt-2" aria-label="Message actions">
        <input class="file-hidden" type="file" name="file" id="fileInput">
        <label class="btn btn-ghost btn-sm icon-only mb-0" for="fileInput" title="Send file" aria-label="Send file">📎</label>

        <input class="file-hidden" type="file" name="gif" id="gifInput" accept="image/gif">
        <button class="btn btn-ghost btn-sm icon-only" type="button" id="gifBtn" title="GIFs" aria-label="GIFs">🖼️</button>

        <input class="file-hidden" type="file" name="voice" id="voiceInput" accept="audio/*">
        <button class="btn btn-ghost btn-sm icon-only" type="button" id="recBtn" title="Send voice message" aria-label="Send voice message">🎙️</button>
      </div>
      <div class="small-muted mt-1 composer-status" id="recStatus" aria-live="polite"></div>
      </form>
    </div>
  </div>
</div>

  <div id="actionSheet">
    <div class="sheet">
      <button type="button" id="actEdit">✏️ Edit message</button>
      <button type="button" id="actDelete" class="danger">🗑️ Delete</button>
      <button type="button" id="actCancel" class="closex">Cancel</button>
    </div>
  </div>
{% endblock %}

{% block scripts %}
<script nonce="{{ csp_nonce }}">

const MSG_VOICE_UPLOAD_FAIL = {{ _("Upload failed. Please choose an audio file.")|tojson }};
(function(){
  try{ if("scrollRestoration" in history) history.scrollRestoration = "manual"; }catch(e){}
  // Keep presence alive (scoped by host)
  async function ping(){
    try{ await fetch("/api/ping", {method:"POST"}); }catch(e){}
  }
  setInterval(ping, 15000);
  ping();

  // Faster presence refresh in chats list/header (no page refresh)
  async function refreshPresence(){
    try{
      const r = await fetch("/api/presence", {headers:{"Accept":"application/json"}});
      if(!r.ok) return;
      const data = await r.json().catch(()=>null);
      const map = (data && data.items) ? data.items : {};
      document.querySelectorAll('.user-item').forEach(a=>{
        try{
          const h = a.getAttribute('href') || '';
          const m = h.match(/\/chat\/([^/?#]+)/);
          if(!m) return;
          const u = decodeURIComponent(m[1]);
          const pill = a.querySelector('.pill.online, .pill.offline');
          if(!pill) return;
          const on = !!map[u];
          pill.classList.remove('online','offline');
          pill.classList.add(on ? 'online' : 'offline');
          pill.textContent = on ? 'Online' : 'Offline';
        }catch(e){}
      });
      const head = document.querySelector('.chat-thread .small-muted[style*="white-space"]');
      const peer = {{ peer|tojson }};
      if(head && peer && peer !== {{ me|tojson }}) head.textContent = (map[peer] ? '🟢 online' : '⚫ offline');
    }catch(e){}
  }
  setInterval(refreshPresence, 1200);
  setTimeout(refreshPresence, 120);

  // Scroll to bottom on load
  const box = document.getElementById("msgBox");
  if(box){ box.scrollTop = box.scrollHeight; }

  // Search suggestions
  const inp = document.getElementById("userSearch");
  const sb = document.getElementById("suggestBox");
  let t=null;
  function esc(s){ return (s||"").replace(/[&<>"]/g, c=>({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;" }[c])); }
  function item(u){
    const pic = u.has_pic ? `<img class="avatar-img pfp-clickable" src="/profile/pic/${encodeURIComponent(u.username)}" alt="" onclick="toggleImageModal(this.src)">` : `<div class="avatar-fallback"><img data-logo class="avatar-img" src="{{ logo_dark }}" alt="logo"></div>`;
    const status = u.online ? `<span class="pill online">Online</span>` : `<span class="pill offline">Offline</span>`;
    const ringCls = u.has_story ? " story-ring" : "";
    return `<a class="suggest-item" href="/chat/${encodeURIComponent(u.username)}">
      <div class="d-flex align-items-center gap-2 flex-wrap justify-content-end">
        <div class="avatar-wrap${ringCls}">${pic}</div>
        <div class="text-start">
          <div class="suggest-name">${esc(u.nickname||u.username)}</div>
          <div class="small-muted">@${esc(u.username)}</div>
        </div>
      </div>
      ${status}
    </a>`;
  }
  async function query(q){
    const r = await fetch(`/api/users?q=${encodeURIComponent(q)}`);
    if(!r.ok) return;
    const data = await r.json();
    const users = data.users || [];
    if(!users.length){ sb.style.display="none"; sb.innerHTML=""; return; }
    sb.innerHTML = users.map(item).join("");
    sb.style.display="block";
  }
  if(inp){
    inp.addEventListener("input", ()=>{
      const q = inp.value.trim();
      if(t) clearTimeout(t);
      if(!q){ sb.style.display="none"; sb.innerHTML=""; return; }
      t=setTimeout(()=>query(q), 120);
    });
    inp.addEventListener("focus", ()=>{ const q=inp.value.trim(); if(q) query(q); });
    inp.addEventListener("blur", ()=>setTimeout(()=>{ sb.style.display="none"; }, 180));
  }

  // Voice recording (mobile friendly)
  const recBtn = document.getElementById("recBtn");
  const recStatus = document.getElementById("recStatus");
  const form = document.getElementById("sendForm");
  const fileInput = form ? form.querySelector('input[name="file"]') : null;
  const gifInput = form ? form.querySelector('input[name="gif"]') : null;
  const gifBtn = document.getElementById("gifBtn");
  const voiceInput = form ? form.querySelector('input[name="voice"]') : null;
  const bodyTa = form ? form.querySelector('textarea[name="body"]') : null;
  // 1-line composer that grows like Instagram (Shift+Enter for newline)
  function autoGrowTa(){
    if(!bodyTa) return;
    bodyTa.style.height = "auto";
    const h = Math.min(bodyTa.scrollHeight, 160);
    bodyTa.style.height = h + "px";
  }
  if(bodyTa && form){
    bodyTa.addEventListener("input", autoGrowTa);
    bodyTa.addEventListener("keydown", (e)=>{
      if(e.key === "Enter" && !e.shiftKey){
        e.preventDefault();
        try{ form.requestSubmit(); }
        catch(err){ try{ form.dispatchEvent(new Event("submit", {cancelable:true, bubbles:true})); }catch(e2){} }
      }
    });
    autoGrowTa();
  }

  let mediaRec=null, chunks=[], stream=null;

  // --- Connections.py style send: no full page refresh ---
  async function sendFormData(fd){
    if(!form) return;
    try{
      const resp = await fetch(form.action, {
        method: "POST",
        body: fd,
        headers: {"X-Requested-With":"XMLHttpRequest", "Accept":"application/json"}
      });
      const data = await resp.json().catch(()=>null);
      if(!resp.ok || !data || !data.ok){ throw new Error((data && data.error) || "Send failed"); }
      if(data.html){
        const box = document.getElementById("msgBox");
        box.insertAdjacentHTML("beforeend", data.html);
        const added = box.lastElementChild;
        try{ if(window.butFormatTimes) window.butFormatTimes(added); }catch(e){}
        // attach long-press handlers to the new bubble
        const newBubble = box.querySelector(`.bubble[data-mid="${data.id}"]`);
        if(newBubble) attachLongPress(newBubble);
        // keep view at bottom like Connections.py
        box.scrollTop = box.scrollHeight;
      }
      // reset composer fields
      if(bodyTa) bodyTa.value = "";
      if(fileInput) fileInput.value = "";
      if(gifInput) gifInput.value = "";
      if(voiceInput) voiceInput.value = "";
    }catch(e){
      alert(e.message || "Send failed");
    }
  }

  if(form){
    form.addEventListener("submit", async (e)=>{
      e.preventDefault();
      const fd = new FormData(form);
      await sendFormData(fd);
    });
  }


  async function stopAll(){
    try{ if(mediaRec && mediaRec.state!=="inactive") mediaRec.stop(); }catch(e){}
    try{ if(stream){ stream.getTracks().forEach(t=>t.stop()); } }catch(e){}
    mediaRec=null; stream=null; chunks=[];
  }

  async function startRec(){
    await stopAll();
    try{
      if(fileInput) fileInput.value='';
      if(bodyTa) bodyTa.value='';
      stream = await navigator.mediaDevices.getUserMedia({audio:true});
      mediaRec = new MediaRecorder(stream);
      chunks=[];
      mediaRec.ondataavailable = e=>{ if(e.data && e.data.size) chunks.push(e.data); };
      mediaRec.onstop = async ()=>{
        // iOS Safari often blocks programmatic assignment to input.files (DataTransfer),
        // so we upload the recording directly via fetch(FormData) to keep it reliable.
        try{
          const mime = (mediaRec && mediaRec.mimeType) ? mediaRec.mimeType : "audio/webm";
          const blob = new Blob(chunks, {type: mime});
          recStatus.textContent = "Recorded ✓ uploading…";

          const fd = new FormData(form);
          // Replace any chosen voice file with the recorded blob.
          try{ fd.delete("voice"); }catch(e){}
          fd.append("voice", blob, "voice.webm");

          await sendFormData(fd);
        }catch(e){
          // Fallback: let user pick an audio file if recording upload fails.
          recStatus.textContent = MSG_VOICE_UPLOAD_FAIL;
          try{ if(voiceInput) voiceInput.click(); }catch(e2){}
        }
        stopAll();
      };
      mediaRec.start();
      recStatus.textContent = {{ _("Recording… tap again to stop")|tojson }};
      recBtn.textContent = "⏹️";
    }catch(e){
      recStatus.textContent = "Mic blocked / not available.";
      recBtn.textContent = "🎙️";
      stopAll();
    }
  }

  // Browser fallback: if MediaRecorder is missing (some iOS versions), open file picker.
  if(recBtn && (!window.MediaRecorder || !navigator.mediaDevices)){
    recBtn.addEventListener("click", ()=>{ try{ if(voiceInput) voiceInput.click(); }catch(e){} recStatus.textContent = {{ _("Recording not supported here. Choose an audio file.")|tojson }}; });
  }

  if(recBtn && window.MediaRecorder && navigator.mediaDevices){
    recBtn.addEventListener("click", async ()=>{
      if(mediaRec && mediaRec.state==="recording"){
        try{ mediaRec.stop(); }catch(e){}
        recBtn.textContent = "🎙️";
      }else{
        await startRec();
      }
    });
  }
  // Auto-send files immediately when chosen

  if(gifBtn && gifInput){
    gifBtn.addEventListener("click", ()=>{ try{ gifInput.click(); }catch(e){} });
  }
  if(gifInput){
    gifInput.addEventListener("change", ()=>{
      if(!gifInput.files || !gifInput.files.length) return;
      if(bodyTa) bodyTa.value = "";
      if(voiceInput) voiceInput.value = "";
      if(fileInput) fileInput.value = "";
      try{ if(form.requestSubmit) form.requestSubmit(); else form.dispatchEvent(new Event("submit", {cancelable:true, bubbles:true})); }catch(e){ try{ form.dispatchEvent(new Event("submit", {cancelable:true, bubbles:true})); }catch(e2){} }
    });
  }


  if(voiceInput){
    voiceInput.addEventListener("change", ()=>{
      if(!voiceInput.files || !voiceInput.files.length) return;
      if(bodyTa) bodyTa.value = "";
      if(fileInput) fileInput.value = "";
      if(gifInput) gifInput.value = "";
      try{ if(form.requestSubmit) form.requestSubmit(); else form.dispatchEvent(new Event("submit", {cancelable:true, bubbles:true})); }catch(e){ try{ form.dispatchEvent(new Event("submit", {cancelable:true, bubbles:true})); }catch(e2){} }
    });
  }
  if(fileInput){
    fileInput.addEventListener("change", ()=>{
      if(!fileInput.files || !fileInput.files.length) return;
      if(bodyTa) bodyTa.value = "";
      if(voiceInput) voiceInput.value = "";
      try{ if(form.requestSubmit) form.requestSubmit(); else form.dispatchEvent(new Event("submit", {cancelable:true, bubbles:true})); }catch(e){ try{ form.dispatchEvent(new Event("submit", {cancelable:true, bubbles:true})); }catch(e2){} }
    });
  }

  // Long-press actions (edit/delete)
  const sheet = document.getElementById("actionSheet");
  const actEdit = document.getElementById("actEdit");
  const actDelete = document.getElementById("actDelete");
  const actCancel = document.getElementById("actCancel");
  let holdTimer=null, activeMid=null, activeKind=null, activeEl=null;

  function closeSheet(){ if(sheet) sheet.style.display="none"; activeMid=null; activeKind=null; activeEl=null; }
  if(sheet){
    sheet.addEventListener("click", (e)=>{ if(e.target === sheet) closeSheet(); });
  }
  if(actCancel) actCancel.addEventListener("click", closeSheet);

  function openSheet(mid, kind, el){
    activeMid = mid; activeKind = kind; activeEl = el;
    if(!sheet) return;
    // Edit only for text
    if(actEdit) actEdit.style.display = (kind === "text") ? "block" : "none";
    if(actDelete) actDelete.textContent = (kind === "voice" || kind === "file") ? "🗑️ Delete attachment" : "🗑️ Delete";
    sheet.style.display="flex";
  }

  function attachLongPress(el){
    const mid = el.getAttribute("data-mid");
    const kind = el.getAttribute("data-kind");
    const sender = el.getAttribute("data-sender");
    if(!mid || !kind) return;
    // only allow actions for my own messages
    if(sender !== "{{ me }}") return;

    const start = ()=>{
      holdTimer = setTimeout(()=>openSheet(mid, kind, el), 420);
    };
    const cancel = ()=>{
      if(holdTimer){ clearTimeout(holdTimer); holdTimer=null; }
    };
    el.addEventListener("pointerdown", start);
    el.addEventListener("pointerup", cancel);
    el.addEventListener("pointercancel", cancel);
    el.addEventListener("pointerleave", cancel);
    el.addEventListener("touchmove", cancel, {passive:true});
    // Right-click fallback
    el.addEventListener("contextmenu", (e)=>{ e.preventDefault(); openSheet(mid, kind, el); });
  }

  document.querySelectorAll(".bubble[data-mid]").forEach(attachLongPress);

  async function apiPost(url, payload){
    const r = await fetch(url, {method:"POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(payload||{})});
    let data=null;
    try{ data = await r.json(); }catch(e){}
    if(!r.ok || !data || !data.ok) throw new Error((data && data.error) || "Request failed");
    return data;
  }

  if(actDelete){
    actDelete.addEventListener("click", async ()=>{
      if(!activeMid) return;
      try{
        await apiPost(`/api/dm/message/${activeMid}/delete`, {});
        if(activeEl){
          activeEl.innerHTML = `<span class="small-muted">Deleted</span>`;
          activeEl.setAttribute("data-kind","deleted");
        }
      }catch(e){
        alert(e.message || "Delete failed");
      }finally{ closeSheet(); }
    });
  }

  if(actEdit){
    actEdit.addEventListener("click", async ()=>{
      if(!activeMid || !activeEl) return;
      const cur = (activeEl.querySelector(".msg-text")||{}).textContent || "";
      const next = prompt("Edit message:", cur);
      if(next === null) return;
      const trimmed = next.trim();
      if(!trimmed){ alert("Message cannot be empty."); return; }
      try{
        await apiPost(`/api/dm/message/${activeMid}/edit`, {body: trimmed});
        let span = activeEl.querySelector(".msg-text");
        if(!span){
          span = document.createElement("span");
          span.className = "msg-text";
          activeEl.innerHTML = "";
          activeEl.appendChild(span);
        }
        span.textContent = trimmed;
      }catch(e){
        alert(e.message || "Edit failed");
      }finally{ closeSheet(); }
    });
  }

  
  // Calls disabled (audio/video removed).

})();
</script>
{% endblock %}"""


# Mobile/IG-like chat page (no left sidebar). This is what /chat/<username> renders.
TEMPLATES["chat_locked.html"] = r"""{% extends "base.html" %}
{% block content %}
<div class="card-soft p-3">
  <div class="d-flex justify-content-between align-items-start gap-2 flex-wrap">
    <div>
      <h4 class="mb-1">🔒 {{ peer_display }}</h4>
      <div class="small-muted">{{ _('This chat is locked with a PIN.') if lang=='en' else 'Αυτή η συνομιλία είναι κλειδωμένη με PIN.' }}</div>
    </div>
    <a class="btn btn-ghost" href="{{ url_for('chats') }}">{{ _('Back') }}</a>
  </div>
</div>
<div class="card-soft p-3 mt-3">
  <form method="post" action="{{ url_for('dm_lock_unlock', username=peer) }}" class="d-flex gap-2 flex-wrap align-items-end">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <div>
      <label class="form-label">{{ _('PIN') }}</label>
      <input class="form-control" type="password" name="pin" inputmode="numeric" pattern="[0-9]*" minlength="4" maxlength="12" required>
    </div>
    <button class="btn btn-accent" type="submit">{{ _('Unlock') if lang=='en' else 'Ξεκλείδωμα' }}</button>
  </form>
  <div class="small-muted mt-2">{{ _('Use 4 to 12 digits.') if lang=='en' else 'Χρησιμοποίησε 4 έως 12 ψηφία.' }}</div>
</div>
{% endblock %}
"""

TEMPLATES["group_locked.html"] = r"""{% extends "base.html" %}
{% block content %}
<div class="card-soft p-3">
  <div class="d-flex justify-content-between align-items-start gap-2 flex-wrap">
    <div>
      <h4 class="mb-1">🔒 {{ g.name }}</h4>
      <div class="small-muted">{{ _('This group is locked with a PIN.') if lang=='en' else 'Αυτή η ομάδα είναι κλειδωμένη με PIN.' }}</div>
    </div>
    <a class="btn btn-ghost" href="{{ url_for('groups') }}">{{ _('Back') }}</a>
  </div>
</div>
<div class="card-soft p-3 mt-3">
  <form method="post" action="{{ url_for('group_lock_unlock', gid=g.id) }}" class="d-flex gap-2 flex-wrap align-items-end">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <div>
      <label class="form-label">{{ _('PIN') }}</label>
      <input class="form-control" type="password" name="pin" inputmode="numeric" pattern="[0-9]*" minlength="4" maxlength="12" required>
    </div>
    <button class="btn btn-accent" type="submit">{{ _('Unlock') if lang=='en' else 'Ξεκλείδωμα' }}</button>
  </form>
  <div class="small-muted mt-2">{{ _('Use 4 to 12 digits.') if lang=='en' else 'Χρησιμοποίησε 4 έως 12 ψηφία.' }}</div>
</div>
{% endblock %}
"""

TEMPLATES["chat_page.html"] = r"""{% extends "base.html" %}
{% block content %}
<div class="chat-page">
  <div class="chat-top">
    <div class="card-soft p-3">
      <div class="d-flex justify-content-between align-items-start gap-2">
        <div>
          <div class="d-flex align-items-center gap-2 flex-wrap">
            {% if peer_display|lower != "saved messages" %}<h4 class="mb-0">{{ peer_display }}</h4>{% endif %}
            {% if not is_self_chat %}<span class="small-muted" style="white-space:nowrap">{{ "🟢 online" if peer_online else "⚫ offline" }}</span>{% endif %}
          </div>
        </div>
        {% if (not is_self_chat) and ENABLE_CALLS %}<div class="d-flex gap-2 flex-wrap">
          <button class="btn btn-ghost btn-chat-top" type="button" id="callAudioBtn">📞 {{ _("Call") }}</button>
          <button class="btn btn-ghost btn-chat-top" type="button" id="callVideoBtn">📹 {{ _("Call") }}</button>
        </div>{% endif %}
      </div>
    </div>
  </div>

  <div class="card-soft p-3 mt-3">
    <div class="small-muted mb-2">🔐 {{ _('Chat PIN lock') if lang=='en' else 'Κλείδωμα συνομιλίας με PIN' }}</div>
    {% if has_chat_pin %}
      <div class="d-flex gap-2 flex-wrap align-items-end">
        <form method="post" action="{{ url_for('dm_lock_set', username=peer) }}" class="d-flex gap-2 flex-wrap align-items-end">
          <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
          <div>
            <label class="form-label small-muted">{{ _('Change PIN') if lang=='en' else 'Αλλαγή PIN' }}</label>
            <input class="form-control" type="password" name="pin" inputmode="numeric" pattern="[0-9]*" minlength="4" maxlength="12" required>
          </div>
          <button class="btn btn-ghost" type="submit">{{ _('Save') if lang=='en' else 'Αποθήκευση' }}</button>
        </form>
        <form method="post" action="{{ url_for('dm_lock_close', username=peer) }}">
          <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
          <button class="btn btn-ghost" type="submit">{{ _('Lock now') if lang=='en' else 'Κλείδωσε τώρα' }}</button>
        </form>
        <form method="post" action="{{ url_for('dm_lock_remove', username=peer) }}">
          <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
          <button class="btn btn-danger" type="submit">{{ _('Remove PIN') if lang=='en' else 'Αφαίρεση PIN' }}</button>
        </form>
      </div>
    {% else %}
      <form method="post" action="{{ url_for('dm_lock_set', username=peer) }}" class="d-flex gap-2 flex-wrap align-items-end">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <div>
          <label class="form-label small-muted">{{ _('Set PIN') if lang=='en' else 'Ορισμός PIN' }}</label>
          <input class="form-control" type="password" name="pin" inputmode="numeric" pattern="[0-9]*" minlength="4" maxlength="12" required>
        </div>
        <button class="btn btn-accent" type="submit">{{ _('Enable') if lang=='en' else 'Ενεργοποίηση' }}</button>
      </form>
    {% endif %}
  </div>

  <div class="chat-messages" id="msgBox">
    {% for m in messages %}
      <div class="msg-row {{ 'me' if m.sender==me else 'them' }}">
        <div class="bubble {{ 'me' if m.sender==me else 'them' }}" data-mid="{{ m.id }}" data-kind="{{ m.kind }}" data-sender="{{ m.sender }}">
            {% if m.kind == "text" %}
              <span class="msg-text">{{ m.body }}</span>
              {% if m.edited_at_local %}<span class="small-muted"> (edited)</span>{% endif %}
            {% elif m.kind == "voice" %}
              <audio controls preload="metadata">
                <source src="{{ url_for('dm_voice_stream', vid=m.voice_id) }}" type="{{ m.voice_mime }}">
              </audio>
            {% elif m.kind == "file" %}
              {% if m.file_is_image %}
                <img src="{{ url_for('dm_file_stream', fid=m.file_id) }}" alt="{{ m.file_name }}"/>
              {% elif m.file_is_video %}
                <video controls playsinline preload="metadata">
                  <source src="{{ url_for('dm_file_stream', fid=m.file_id) }}" type="{{ m.file_mime }}">
                </video>
              {% elif m.file_is_audio %}
                <audio controls preload="metadata">
                  <source src="{{ url_for('dm_file_stream', fid=m.file_id) }}" type="{{ m.file_mime }}">
                </audio>
              {% else %}
                <a class="file-chip" href="{{ url_for('dm_file_download', fid=m.file_id) }}">📎 {{ m.file_name }}</a>
                <div class="small-muted mt-1">{{ m.file_size_h }}</div>
              {% endif %}
            {% else %}
              <span class="msg-text">{{ m.body }}</span>
            {% endif %}
        </div>
        <div class="msg-meta">
    <span class="ts" data-utc="{{ m.created_at_utc }}">{{ m.created_at_local }}</span>{% if m.deleted %} • deleted{% endif %}
    {% if m.sender==me %}
      <span class="dm-ticks {% if m.read_at_local %}seen{% elif m.delivered_at_local %}delivered{% else %}sent{% endif %}" data-mid="{{ m.id }}"
            title="{% if m.read_at_local %}Seen {{ m.read_at_local }}{% elif m.delivered_at_local %}Delivered{% else %}Sent{% endif %}">
        {% if m.read_at_local %}✔✔{% elif m.delivered_at_local %}✔✔{% else %}✔{% endif %}
      </span>
    {% endif %}
  </div>
      </div>
    {% endfor %}
    <div id="bottomSentinel" style="height:1px"></div>
  </div>

  <div class="chat-composer">
    <form method="post" action="{{ url_for('dm_send', username=peer) }}" enctype="multipart/form-data" id="sendForm">
      <input type="hidden" name="gif_url" id="gifUrl" value="">
      <div class="composer-row">
        <textarea class="form-control msg-input" name="body" rows="1" placeholder="Message..." style="resize:none;"></textarea>

        <input class="file-hidden" type="file" name="file" id="fileInput">
        <label class="btn btn-ghost btn-sm icon-only mb-0" for="fileInput" title="Send file" aria-label="Send file">📎</label>

        <button class="btn btn-ghost btn-sm gif-text-btn" type="button" id="gifBtn" title="GIFs" aria-label="GIFs">GIF</button>

        <input class="file-hidden" type="file" name="voice" id="voiceInput" accept="audio/*">
        <button class="btn btn-ghost btn-sm icon-only" type="button" id="recBtn" title="Send voice message" aria-label="Send voice message">🎙️</button>

        <button class="btn btn-accent btn-send" type="submit" aria-label="Send" title="Send">➡️</button>
      </div>
      <div class="small-muted mt-1 composer-status" id="recStatus" aria-live="polite"></div>
    </form>
  </div>
</div>

<!-- GIF picker modal -->
<div class="modal fade" id="gifModal" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered modal-lg">
    <div class="modal-content" style="background:var(--panel); border:1px solid var(--border);">
      <div class="modal-header" style="border-color:var(--border);">
        <h5 class="modal-title">GIFs</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <div class="d-flex gap-2 mb-2">
          <input class="form-control" id="gifSearch" placeholder="Search GIFs…" autocomplete="off">
          <button class="btn btn-ghost" type="button" id="gifSearchBtn">{{ _('Search') }}</button>
        </div>
        <div class="small-muted mb-2" id="gifHint">Trending</div>
        <div class="gif-grid" id="gifGrid"></div>
      </div>
    </div>
  </div>
</div>

  <div id="actionSheet">
    <div class="sheet">
      <button type="button" id="actEdit">✏️ Edit message</button>
      <button type="button" id="actDelete" class="danger">🗑️ Delete</button>
      <button type="button" id="actCancel" class="closex">Cancel</button>
    </div>
  </div>
{% endblock %}

{% block scripts %}

  <div id="callPanel" class="card-soft p-2 mb-2" style="display:none;">
    <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-2">
      <div class="small-muted" id="callStatus">{{ _("Ready") }}</div>
      <button type="button" class="btn btn-ghost btn-sm" id="toggleVideosBtn" title="{{ _('Collapse/Expand') }}" aria-label="{{ _('Collapse/Expand') }}">▾</button>
    </div>
    <div class="d-flex flex-wrap gap-2 align-items-center mb-2">
      <button id="joinBtn" class="btn btn-accent btn-sm" type="button" aria-label="{{ _('Join Call') }}" title="{{ _('Join Call') }}">📞 <span class="d-none d-sm-inline">{{ _("Join") }}</span></button>
      <button id="muteBtn" class="btn btn-ghost btn-sm" type="button" disabled aria-label="{{ _('Mute') }}" title="{{ _('Mute / Unmute') }}"><span id="muteIcon">🎤</span> <span class="d-none d-sm-inline">{{ _("Mute") }}</span></button>
      <button id="videoBtn" class="btn btn-ghost btn-sm" type="button" disabled aria-label="{{ _('Camera') }}" title="{{ _('Camera On / Off') }}"><span id="videoIcon">🎥</span> <span class="d-none d-sm-inline">{{ _("Cam") }}</span></button>
      <button id="switchCamBtn" class="btn btn-ghost btn-sm" type="button" disabled aria-label="{{ _('Switch Camera') }}" title="{{ _('Switch Camera') }}">🔄 <span class="d-none d-sm-inline">{{ _("Flip") }}</span></button>
      <button id="allCamsBtn" class="btn btn-ghost btn-sm" type="button" disabled aria-label="{{ _('Overlay') }}" title="{{ _('Overlay call') }}"><span id="allCamsIcon">🎯</span> <span class="d-none d-sm-inline">{{ _("All") }}</span></button>
      <button id="hideCamBtn" class="btn btn-ghost btn-sm" type="button" disabled aria-label="{{ _('Hide cameras') }}" title="{{ _('Hide cameras (keep audio)') }}"><span id="hideCamIcon">🙈</span> <span class="d-none d-sm-inline">{{ _("Hide") }}</span></button>
      <button id="leaveBtn" class="btn btn-danger btn-sm" type="button" disabled aria-label="{{ _('Leave Call') }}" title="{{ _('Leave Call') }}">📴 <span class="d-none d-sm-inline">{{ _("Leave") }}</span></button>
    </div>
    <div id="videos" style="position:relative; width:100%; height:min(46vh,420px); background:rgba(0,0,0,0.28); border:1px solid var(--border); border-radius:14px; overflow:hidden;">
      <video id="remote" autoplay playsinline style="position:absolute; inset:0; width:100%; height:100%; object-fit:cover; background:#000;"></video>
      <video id="local" autoplay muted playsinline style="position:absolute; left:10px; bottom:10px; width:32%; max-width:180px; height:30%; max-height:180px; object-fit:cover; border-radius:12px; border:1px solid rgba(255,255,255,0.18); box-shadow:0 12px 30px rgba(0,0,0,0.35);"></video>
    </div>
    <div class="small-muted mt-2">Tip: camera/mic require HTTPS on most browsers.</div>
  </div>


<script nonce="{{ csp_nonce }}">

const MSG_VOICE_UPLOAD_FAIL = {{ _("Upload failed. Please choose an audio file.")|tojson }};
(function(){
  // Keep presence alive
  async function ping(){ try{ await fetch("/api/ping", {method:"POST"}); }catch(e){} }
  setInterval(ping, 15000); ping();

  // Scroll to bottom on load
  const box = document.getElementById("msgBox");
  const bottom = document.getElementById("bottomSentinel");
  function scrollToBottom(){
    if(!box) return;
    // Prefer sentinel (handles dynamic heights after images load)
    if(bottom && bottom.scrollIntoView){
      bottom.scrollIntoView({block:"end"});
    }else{
      box.scrollTop = box.scrollHeight;
    }
  }
  // Initial scroll + a couple of delayed passes for media/layout
  scrollToBottom();
  requestAnimationFrame(scrollToBottom);
  setTimeout(scrollToBottom, 60);
  setTimeout(scrollToBottom, 240);
  window.addEventListener("load", ()=>{ scrollToBottom(); setTimeout(scrollToBottom, 320); });
  window.addEventListener("pageshow", ()=>{ scrollToBottom(); setTimeout(scrollToBottom, 200); });
  // If any images/videos load later, keep view pinned to bottom
  if(box){
    box.querySelectorAll("img,video").forEach(el=>{
      el.addEventListener("load", scrollToBottom, {once:true});
      el.addEventListener("loadedmetadata", scrollToBottom, {once:true});
    });
  }

  const form = document.getElementById("sendForm");
  const fileInput = form ? form.querySelector('input[name="file"]') : null;
  const voiceInput = form ? form.querySelector('input[name="voice"]') : null;
  const bodyTa = form ? form.querySelector('textarea[name="body"]') : null;
  const gifUrl = document.getElementById("gifUrl");
  // 1-line composer that grows like Instagram (Shift+Enter for newline)
  function autoGrowTa(){
    if(!bodyTa) return;
    bodyTa.style.height = "auto";
    const h = Math.min(bodyTa.scrollHeight, 160);
    bodyTa.style.height = h + "px";
  }
  if(bodyTa && form){
    bodyTa.addEventListener("input", autoGrowTa);
    bodyTa.addEventListener("keydown", (e)=>{
      if(e.key === "Enter" && !e.shiftKey){
        e.preventDefault();
        requestSend();
      }
    });
  autoGrowTa();
}

// --- Connections.py style send: no full page refresh ---
function requestSend(){
  if(!form) return;
  try{
    if(form.requestSubmit) form.requestSubmit();
    else form.dispatchEvent(new Event("submit", {cancelable:true, bubbles:true}));
  }catch(e){
    try{ form.dispatchEvent(new Event("submit", {cancelable:true, bubbles:true})); }catch(e2){}
  }
}

function isNearBottom(){
  try{
    if(!box) return true;
    return (box.scrollHeight - box.scrollTop - box.clientHeight) < 160;
  }catch(e){ return true; }
}

function isElementNearViewport(el){
  try{
    if(!el || !box) return false;
    const top = el.offsetTop || 0;
    const bottomY = top + (el.offsetHeight || 0);
    const viewTop = box.scrollTop || 0;
    const viewBottom = viewTop + (box.clientHeight || 0);
    const pad = 220;
    return (bottomY >= (viewTop - pad)) && (top <= (viewBottom + pad));
  }catch(e){ return false; }
}

function upsertHtmlRow(html, opts){
  // Stable DOM updates:
  //  - Append truly new rows
  //  - If a row already exists, update ONLY its text/meta when needed
  //  - Avoid replacing existing media elements (img/video/audio) unless the attachment is actually upgrading
  if(!html || !box) return null;

  const sentinel = bottom || document.getElementById("bottomSentinel");
  const parent = sentinel ? sentinel.parentNode : box;
  const pinned = (opts && typeof opts.pinned === "boolean") ? opts.pinned : isNearBottom();

  const tmp = document.createElement("div");
  tmp.innerHTML = html;
  let lastEl = null;

  function sigFromRow(row){
    const b = row && row.querySelector ? row.querySelector(".bubble[data-mid]") : null;
    if(!b) return "";
    const kind = b.getAttribute("data-kind") || "";
    if(kind === "text"){
      const t = (b.querySelector(".msg-text")||{}).textContent || "";
      const edited = b.textContent.includes("(edited)") ? "1" : "0";
      const deleted = b.textContent.toLowerCase().includes("deleted") ? "1" : "0";
      return `text|${t}|${edited}|${deleted}`;
    }
    if(kind === "voice"){
      const s = b.querySelector("audio source")?.getAttribute("src") || "";
      return `voice|${s}`;
    }
    if(kind === "file"){
      let src = "";
      const img = b.querySelector("img"); if(img) src = img.getAttribute("src") || "";
      const vs = b.querySelector("video source"); if(vs) src = vs.getAttribute("src") || src;
      const as = b.querySelector("audio source"); if(as) src = as.getAttribute("src") || src;
      const link = b.querySelector("a.file-chip")?.getAttribute("href") || "";
      return `file|${src}|${link}`;
    }
    if(kind === "deleted") return "deleted";
    return kind;
  }

  function updateExisting(existingRow, newRow){
    try{
      const eBubble = existingRow.querySelector(".bubble[data-mid]");
      const nBubble = newRow.querySelector(".bubble[data-mid]");
      const eSig = sigFromRow(existingRow);
      const nSig = sigFromRow(newRow);

      // Update bubble only when content truly changed.
      if(eBubble && nBubble && eSig !== nSig){
        const eKind = eBubble.getAttribute("data-kind") || "";
        const nKind = nBubble.getAttribute("data-kind") || "";

        if(eKind !== nKind){
          // Kind changed (e.g., placeholder -> file/voice). Replace bubble node.
          eBubble.replaceWith(nBubble);
        }else if(nKind === "text"){
          // Text edits/deletes: update in-place
          const eTxt = eBubble.querySelector(".msg-text");
          const nTxt = nBubble.querySelector(".msg-text");
          if(eTxt && nTxt){
            eTxt.textContent = nTxt.textContent;
            // keep edited marker if present
            if(nBubble.innerHTML.includes("(edited)") && !eBubble.innerHTML.includes("(edited)")){
              eBubble.innerHTML = nBubble.innerHTML;
            }
          }else{
            eBubble.innerHTML = nBubble.innerHTML;
          }
        }else{
          // Attachments: only replace when upgrading (e.g., empty src -> real src)
          const eSrc = eBubble.querySelector("source")?.getAttribute("src") || eBubble.querySelector("img")?.getAttribute("src") || "";
          const nSrc = nBubble.querySelector("source")?.getAttribute("src") || nBubble.querySelector("img")?.getAttribute("src") || "";
          if((!eSrc && nSrc) || (eSig !== nSig)){
            eBubble.innerHTML = nBubble.innerHTML;
          }
        }
        // Ensure long-press actions still work after bubble replacement
        try{
          const nb = existingRow.querySelector(".bubble[data-mid]");
          if(nb) attachLongPress(nb);
        }catch(e){}
      }

      // Always update meta (timestamps / seen status) without touching media elements.
      const eMeta = existingRow.querySelector(".msg-meta");
      const nMeta = newRow.querySelector(".msg-meta");
      if(eMeta && nMeta){
        eMeta.innerHTML = nMeta.innerHTML;
      }

      // Re-format timestamps
      try{ if(window.butFormatTimes) window.butFormatTimes(existingRow); }catch(e){}
    }catch(e){}
  }

  while(tmp.firstElementChild){
    const el = tmp.firstElementChild;
    tmp.removeChild(el);

    const b = el.querySelector && el.querySelector(".bubble[data-mid]");
    const mid = b ? b.getAttribute("data-mid") : null;

    if(mid){
      const existingBubble = box.querySelector(`.bubble[data-mid="${mid}"]`);
      if(existingBubble){
        const existingRow = existingBubble.closest(".msg-row") || existingBubble.parentElement;
        if(existingRow){
          updateExisting(existingRow, el);
          lastEl = existingRow;
        }
        continue;
      }
    }

    if(sentinel && parent) parent.insertBefore(el, sentinel);
    else box.appendChild(el);
    lastEl = el;

    try{ if(window.butFormatTimes) window.butFormatTimes(lastEl); }catch(e){}
    try{
      const nb = lastEl.querySelector && lastEl.querySelector(".bubble[data-mid]");
      if(nb) attachLongPress(nb);
    }catch(e){}

    if(pinned && lastEl){
      try{
        lastEl.querySelectorAll("img").forEach(img=>{
          img.addEventListener("load", ()=>scrollToBottom(), {once:true});
        });
        lastEl.querySelectorAll("video,audio").forEach(m=>{
          m.addEventListener("loadedmetadata", ()=>scrollToBottom(), {once:true});
        });
      }catch(e){}
    }
  }

  if(pinned) scrollToBottom();
  return lastEl;
}


// Update delivery/seen ticks in-place without re-rendering message bubbles (keeps media stable).
function applyStatusUpdates(upds){
  if(!upds || !upds.length) return;
  for(const u of upds){
    try{
      const mid = u.id;
      const el = document.querySelector(`.dm-ticks[data-mid="${mid}"]`);
      if(!el) continue;

      const seen = !!u.read_at_local;
      const delivered = !!u.delivered_at_local;

      // Determine class + glyphs
      el.classList.remove("sent","delivered","seen");
      if(seen){
        el.classList.add("seen");
        el.textContent = "✔✔";
        el.title = "Seen " + u.read_at_local;
      }else if(delivered){
        el.classList.add("delivered");
        el.textContent = "✔✔";
        el.title = "Delivered";
      }else{
        el.classList.add("sent");
        el.textContent = "✔";
        el.title = "Sent";
      }
    }catch(e){}
  }
}




let lastId = {{ last_id|int if last_id is defined else 0 }};

async function sendFormData(fd){
  if(!form) return;
  const pinned = isNearBottom();

  const resp = await fetch(form.action, {
    method: "POST",
    body: fd,
    headers: {"X-Requested-With":"XMLHttpRequest", "Accept":"application/json"}
  });

  if(resp && resp.redirected){
    window.location.href = resp.url;
    return;
  }

  const data = await resp.json().catch(()=>null);
  if(!resp.ok || !data || !data.ok){
    throw new Error((data && data.error) || "Send failed");
  }

  if(typeof data.id === "number") lastId = Math.max(lastId, data.id);
  if(data.html) upsertHtmlRow(data.html, {pinned});
  try{ await pollNew(); }catch(e){}

  // reset composer fields
  try{ if(bodyTa) bodyTa.value = ""; }catch(e){}
  try{ if(fileInput) fileInput.value = ""; }catch(e){}
  try{ if(voiceInput) voiceInput.value = ""; }catch(e){}
  try{ if(gifUrl) gifUrl.value = ""; }catch(e){}
  autoGrowTa();

  if(pinned) scrollToBottom();
}

if(form){
  form.addEventListener("submit", async (e)=>{
    e.preventDefault();

    // If text is being sent, do not also send a previously-selected file/voice/GIF.
    const txt = (bodyTa && bodyTa.value) ? bodyTa.value.trim() : "";
    if(txt.length){
      try{ if(fileInput) fileInput.value = ""; }catch(e){}
      try{ if(voiceInput) voiceInput.value = ""; }catch(e){}
      try{ if(gifUrl) gifUrl.value = ""; }catch(e){}
    }

    const fd = new FormData(form);
    try{
      await sendFormData(fd);
    }catch(err){
      alert((err && err.message) ? err.message : "Send failed");
    }
  });
}

// Poll for new messages so receiving doesn't require refresh.
async function pollNew(){
  try{
    const sinceId = (lastId||0);
    let statusSince = window._dmStatusSince || "";
    const r = await fetch(`/api/dm/{{ peer }}/since?id=${encodeURIComponent(sinceId)}&html=1&status_since=${encodeURIComponent(statusSince)}`, {headers: {"Accept":"application/json"}});
    if(!r.ok) return;
    const data = await r.json().catch(()=>null);
    const msgs = data && data.messages ? data.messages : [];
    // Apply delivery/seen status updates even if there are no new message rows.
    try{ if(data && data.status_updates) applyStatusUpdates(data.status_updates); }catch(e){}
    if(!msgs.length){ emptyStreak = Math.min(20, emptyStreak+1); return; }
    emptyStreak = 0;
    const pinned = isNearBottom();
    for(const m of msgs){
      if(m && typeof m.id === "number") lastId = Math.max(lastId, m.id);
      if(m && m.html) upsertHtmlRow(m.html, {pinned});
    }
    if(pinned) scrollToBottom();
  }catch(e){}
}
// Smart polling (dynamic interval to save battery/data and keep the UI smooth)
let pollTimer=null;
let emptyStreak=0;
let lastActivity=Date.now();

function noteActivity(){ lastActivity = Date.now(); }
document.addEventListener("visibilitychange", ()=>{ noteActivity(); schedulePoll(80); });
if(box){ box.addEventListener("scroll", noteActivity, {passive:true}); }
if(bodyTa){ bodyTa.addEventListener("input", noteActivity, {passive:true}); }

function computeDelay(){
  // Faster when the tab is visible and user is active; slower when hidden/idle.
  if(document.hidden) return 8000;
  const idleMs = Date.now() - lastActivity;
  if(idleMs < 12000) return 500;
  if(idleMs < 30000) return 1200;
  // Back off more if nothing is happening
  if(emptyStreak >= 8) return 8000;
  if(emptyStreak >= 4) return 4500;
  return 3000;
}

function schedulePoll(delay){
  if(pollTimer) clearTimeout(pollTimer);
  pollTimer = setTimeout(pollLoop, delay);
}

async function pollLoop(){
  await pollNew();
  schedulePoll(computeDelay());
}

// Kick off
schedulePoll(50);
// Prevent accidental attachment carry-over: when user types, clear attachment inputs.
  if(bodyTa){
    bodyTa.addEventListener("input", ()=>{
      const v = bodyTa.value || "";
      if(v.trim().length){
        if(fileInput) fileInput.value = "";
        if(voiceInput) voiceInput.value = "";
        if(gifUrl) gifUrl.value = "";
      }
    });
  }

  // Auto-send normal attachments immediately
  if(fileInput){
    fileInput.addEventListener("change", ()=>{
      if(!fileInput.files || !fileInput.files.length) return;
      if(bodyTa) bodyTa.value = "";
      if(voiceInput) voiceInput.value = "";
      if(gifUrl) gifUrl.value = "";
      requestSend();
    });
  }
  // Auto-send voice attachment immediately when chosen
  if(voiceInput){
    voiceInput.addEventListener("change", ()=>{
      if(!voiceInput.files || !voiceInput.files.length) return;
      if(bodyTa) bodyTa.value = "";
      if(fileInput) fileInput.value = "";
      if(gifUrl) gifUrl.value = "";
      requestSend();
    });
  }


  // Voice recording (same logic as before)
  const recBtn = document.getElementById("recBtn");
  const recStatus = document.getElementById("recStatus");
  let mediaRec=null, chunks=[], stream=null;
  async function stopAll(){
    try{ if(mediaRec && mediaRec.state!=="inactive") mediaRec.stop(); }catch(e){}
    try{ if(stream){ stream.getTracks().forEach(t=>t.stop()); } }catch(e){}
    mediaRec=null; stream=null; chunks=[];
  }
  async function startRec(){
    await stopAll();
    try{
      if(fileInput) fileInput.value='';
      if(gifUrl) gifUrl.value='';
      if(bodyTa) bodyTa.value='';
      stream = await navigator.mediaDevices.getUserMedia({audio:true});
      mediaRec = new MediaRecorder(stream);
      chunks=[];
      mediaRec.ondataavailable = e=>{ if(e.data && e.data.size) chunks.push(e.data); };
      mediaRec.onstop = async ()=>{
    try{
      const mime = (mediaRec && mediaRec.mimeType) ? mediaRec.mimeType : "audio/webm";
      const blob = new Blob(chunks, {type: mime});
      recStatus.textContent = "Recorded ✓ uploading…";
      const fd = new FormData();
      // Build a clean payload so Flask reads the recorded blob (avoid duplicate empty "voice" fields on some browsers)
      fd.append("body", "");
      fd.append("voice", blob, "voice.webm");
      await sendFormData(fd);
      recStatus.textContent = "";
    }catch(e){
      recStatus.textContent = (e && e.message) ? e.message : MSG_VOICE_UPLOAD_FAIL;
      try{ if(voiceInput) voiceInput.click(); }catch(e2){}
    }
    stopAll();
  };
      mediaRec.start();
      recStatus.textContent = {{ _("Recording… tap again to stop")|tojson }};
      recBtn.textContent = "⏹️";
    }catch(e){
      recStatus.textContent = "Mic blocked / not available.";
      recBtn.textContent = "🎙️";
      stopAll();
    }
  }
  if(recBtn && (!window.MediaRecorder || !navigator.mediaDevices)){
    recBtn.addEventListener("click", ()=>{ try{ if(voiceInput) voiceInput.click(); }catch(e){} recStatus.textContent = {{ _("Recording not supported here. Choose an audio file.")|tojson }}; });
  }
  if(recBtn && window.MediaRecorder && navigator.mediaDevices){
    recBtn.addEventListener("click", async ()=>{
      if(mediaRec && mediaRec.state==="recording"){ try{ mediaRec.stop(); }catch(e){} recBtn.textContent = "🎙️"; }
      else{ await startRec(); }
    });
  }

  // GIF picker (Tenor demo key). Sends a URL, backend downloads and stores it.
  const gifBtn = document.getElementById("gifBtn");
  const gifModalEl = document.getElementById("gifModal");
  const gifGrid = document.getElementById("gifGrid");
  const gifSearch = document.getElementById("gifSearch");
  const gifSearchBtn = document.getElementById("gifSearchBtn");
  const gifHint = document.getElementById("gifHint");
  let gifModal=null;
  try{ if(gifModalEl) gifModal = new bootstrap.Modal(gifModalEl); }catch(e){}

  function renderGifs(items){
    if(!gifGrid) return;
    gifGrid.innerHTML = (items||[]).map(it=>{
      const url = it && it.url;
      const prev = it && (it.preview || it.url);
      if(!url) return "";
      return `<button type="button" class="gif-item" data-url="${url}"><img src="${prev}" alt="gif"></button>`;
    }).join("");
  }

  async function fetchTenor(endpoint){
    const r = await fetch(endpoint);
    if(!r.ok) return [];
    const data = await r.json().catch(()=>null);
    const out = [];
    const results = (data && data.results) || [];
    for(const g of results){
      const media = g.media || g.media_formats || {};
      // Tenor v1 uses media[0].gif.url; v2 uses media_formats.gif.url
      let gif = null, tiny = null;
      if(Array.isArray(g.media) && g.media[0]){
        gif = g.media[0].gif && g.media[0].gif.url;
        tiny = (g.media[0].tinygif && g.media[0].tinygif.url) || gif;
      }else{
        gif = media.gif && media.gif.url;
        tiny = (media.tinygif && media.tinygif.url) || (media.nanogif && media.nanogif.url) || gif;
      }
      if(gif){ const send = tiny || gif; out.push({url: send, preview: tiny || gif}); }
    }
    return out;
  }

  async function loadTrending(){
    if(gifHint) gifHint.textContent = "Trending";
    const key = "LIVDSRZULELA";
    const url = `https://g.tenor.com/v1/trending?key=${encodeURIComponent(key)}&limit=24&media_filter=minimal`;
    const items = await fetchTenor(url);
    renderGifs(items);
  }
  async function doSearch(q){
    const qq = (q||"").trim();
    if(!qq) return loadTrending();
    if(gifHint) gifHint.textContent = `Results for “${qq}”`;
    const key = "LIVDSRZULELA";
    const url = `https://g.tenor.com/v1/search?q=${encodeURIComponent(qq)}&key=${encodeURIComponent(key)}&limit=24&media_filter=minimal`;
    const items = await fetchTenor(url);
    renderGifs(items);
  }

  if(gifBtn && gifModal){
    gifBtn.addEventListener("click", async ()=>{
      gifModal.show();
      await loadTrending();
      try{ if(gifSearch) gifSearch.focus(); }catch(e){}
    });
  }
  if(gifSearchBtn){ gifSearchBtn.addEventListener("click", ()=>doSearch(gifSearch && gifSearch.value)); }
  if(gifSearch){
    gifSearch.addEventListener("keydown", (e)=>{ if(e.key==="Enter"){ e.preventDefault(); doSearch(gifSearch.value); } });
  }
  if(gifGrid){
    gifGrid.addEventListener("click", (e)=>{
      const btn = e.target && e.target.closest && e.target.closest(".gif-item");
      if(!btn) return;
      const url = btn.getAttribute("data-url");
      if(!url) return;
      if(bodyTa) bodyTa.value = "";
      if(fileInput) fileInput.value = "";
      if(voiceInput) voiceInput.value = "";
      if(gifUrl) gifUrl.value = url;
      try{ if(gifModal) gifModal.hide(); }catch(e){}
      requestSend();
    });
  }

  // Long-press actions (edit/delete)
  const sheet = document.getElementById("actionSheet");
  const actEdit = document.getElementById("actEdit");
  const actDelete = document.getElementById("actDelete");
  const actCancel = document.getElementById("actCancel");
  let holdTimer=null, activeMid=null, activeKind=null, activeEl=null;
  function closeSheet(){ if(sheet) sheet.style.display="none"; activeMid=null; activeKind=null; activeEl=null; }
  if(sheet){ sheet.addEventListener("click", (e)=>{ if(e.target === sheet) closeSheet(); }); }
  if(actCancel) actCancel.addEventListener("click", closeSheet);
  function openSheet(mid, kind, el){
    activeMid = mid; activeKind = kind; activeEl = el;
    if(!sheet) return;
    if(actEdit) actEdit.style.display = (kind === "text") ? "block" : "none";
    if(actDelete) actDelete.textContent = (kind === "voice" || kind === "file") ? "🗑️ Delete attachment" : "🗑️ Delete";
    sheet.style.display="flex";
  }
  function attachLongPress(el){
    const mid = el.getAttribute("data-mid");
    const kind = el.getAttribute("data-kind");
    const sender = el.getAttribute("data-sender");
    if(!mid || !kind) return;
    if(sender !== "{{ me }}") return;
    const start = ()=>{ holdTimer = setTimeout(()=>openSheet(mid, kind, el), 420); };
    const cancel = ()=>{ if(holdTimer){ clearTimeout(holdTimer); holdTimer=null; } };
    el.addEventListener("pointerdown", start);
    el.addEventListener("pointerup", cancel);
    el.addEventListener("pointercancel", cancel);
    el.addEventListener("pointerleave", cancel);
    el.addEventListener("touchmove", cancel, {passive:true});
    el.addEventListener("contextmenu", (e)=>{ e.preventDefault(); openSheet(mid, kind, el); });
  }
  document.querySelectorAll(".bubble[data-mid]").forEach(attachLongPress);

  async function apiPost(url, payload){
    const r = await fetch(url, {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(payload||{})});
    let data=null; try{ data = await r.json(); }catch(e){}
    if(!r.ok || !data || !data.ok) throw new Error((data && data.error) || "Request failed");
    return data;
  }

  // Video call (WebRTC) - simple signaling (polling)
  const callAudioBtn = document.getElementById("callAudioBtn");
  const callVideoBtn = document.getElementById("callVideoBtn");
  const callPanel = document.getElementById("callPanel");
  const callStatus = document.getElementById("callStatus");

  const joinBtn = document.getElementById("joinBtn");
  const leaveBtn = document.getElementById("leaveBtn");
  const muteBtn = document.getElementById("muteBtn");
  const videoBtn = document.getElementById("videoBtn");
  const switchCamBtn = document.getElementById("switchCamBtn");
  const allCamsBtn = document.getElementById("allCamsBtn");
  const hideCamBtn = document.getElementById("hideCamBtn");
  const toggleVideosBtn = document.getElementById("toggleVideosBtn");

  const muteIcon = document.getElementById("muteIcon");
  const videoIcon = document.getElementById("videoIcon");
  const allCamsIcon = document.getElementById("allCamsIcon");
  const hideCamIcon = document.getElementById("hideCamIcon");

  const localVideo = document.getElementById("local");
  const remoteVideo = document.getElementById("remote");
  const videos = document.getElementById("videos");

  let pc=null, callId=null, sigLast=0, sigTimer=null;
  let localStream=null;
  let pendingOffer=null;
  let pendingIce=[];
  let wantVideo=false;
  let isMuted=false, videoOff=false, hideCameras=false, overlayMode=false, videosCollapsed=false;

  function setStatus(s){ try{ if(callStatus) callStatus.textContent = s; }catch(e){} }
  function showPanel(on){
    if(!callPanel) return;
    callPanel.style.display = on ? "" : "none";
    document.body.classList.toggle("callpanel-open", !!on);
  }
  function updateButtons(inCall){
    try{
      if(joinBtn) joinBtn.disabled = !!inCall && !pendingOffer;
      if(leaveBtn) leaveBtn.disabled = !inCall;
      if(muteBtn) muteBtn.disabled = !inCall;
      if(videoBtn) videoBtn.disabled = !inCall;
      if(switchCamBtn) switchCamBtn.disabled = !inCall;
      if(allCamsBtn) allCamsBtn.disabled = !inCall;
      if(hideCamBtn) hideCamBtn.disabled = !inCall;
    }catch(e){}
  }

  async function sendSignal(kind, payload){
    if(!callId) return;
    await apiPost(`/api/call/${callId}/signal`, {kind, payload: payload||{}});
  }

  async function ensurePC(){
    if(pc) return;
    pc = new RTCPeerConnection({
      iceServers: [{urls:"stun:stun.l.google.com:19302"}]
    });
    pc.onicecandidate = (ev)=>{
      if(ev && ev.candidate){
        sendSignal("ice", ev.candidate).catch(()=>{});
      }
    };
    pc.ontrack = (ev)=>{
      try{
        if(remoteVideo && ev.streams && ev.streams[0]){
          remoteVideo.srcObject = ev.streams[0];
        }
      }catch(e){}
    };
    pc.onconnectionstatechange = ()=>{
      try{
        const s = pc.connectionState || "";
        if(s==="connected") setStatus("Connected");
        if(s==="failed" || s==="disconnected") setStatus("Disconnected");
      }catch(e){}
    };
  }

  async function startLocal(){
    if(localStream) return localStream;
    const constraints = {audio:true, video: !!wantVideo};
    localStream = await navigator.mediaDevices.getUserMedia(constraints);
    try{
      if(localVideo) localVideo.srcObject = localStream;
    }catch(e){}
    await ensurePC();
    localStream.getTracks().forEach(t=>pc.addTrack(t, localStream));
    return localStream;
  }

  async function beginOutgoing(){
    showPanel(true);
    setStatus("Starting…");
    const j = await apiPost(`/api/call/start/{{ peer }}`, {});
    callId = j.call_id;
    sigLast = 0;
    await ensurePC();
    await startLocal();
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    await sendSignal("offer", offer);
    updateButtons(true);
    setStatus("Calling…");
    if(!sigTimer) sigTimer = setInterval(pollSignals, 700);
  }

  async function acceptOffer(offer){
    showPanel(true);
    await ensurePC();
    pendingOffer = null;
    await startLocal();
    await pc.setRemoteDescription(new RTCSessionDescription(offer));
    // add queued ICE
    try{
      for(const c of pendingIce){ await pc.addIceCandidate(new RTCIceCandidate(c)); }
      pendingIce = [];
    }catch(e){}
    const ans = await pc.createAnswer();
    await pc.setLocalDescription(ans);
    await sendSignal("answer", ans);
    updateButtons(true);
    setStatus("Connecting…");
    if(!sigTimer) sigTimer = setInterval(pollSignals, 700);
  }

  async function pollSignals(){
    if(!callId) return;
    try{
      const r = await fetch(`/api/call/${callId}/poll?since=${sigLast}`, {cache:"no-store"});
      const j = await r.json();
      if(!j || !j.ok) return;
      const items = j.items || [];
      for(const it of items){
        sigLast = Math.max(sigLast, Number(it.id||0));
        if(it.sender === "{{ me }}") continue;
        let payload = null;
        try{ payload = (typeof it.payload === "string") ? JSON.parse(it.payload) : it.payload; }catch(e){ payload = it.payload; }

        if(it.kind === "offer"){
          pendingOffer = payload;
          setStatus("Incoming… tap Join");
          updateButtons(false);
          showPanel(true);
        }else if(it.kind === "answer"){
          try{
            await ensurePC();
            await pc.setRemoteDescription(new RTCSessionDescription(payload));
            setStatus("Connected");
            updateButtons(true);
          }catch(e){}
        }else if(it.kind === "ice"){
          try{
            if(pc && pc.remoteDescription){
              await pc.addIceCandidate(new RTCIceCandidate(payload));
            }else{
              pendingIce.push(payload);
            }
          }catch(e){}
        }else if(it.kind === "hangup"){
          stopCall();
        }
      }
    }catch(e){}
  }

  async function peekForIncoming(){
    try{
      const r = await fetch(`/api/call/peek/{{ peer }}`, {cache:"no-store"});
      const j = await r.json();
      if(!j || !j.ok) return;
      if(j.call_id && !callId){
        callId = j.call_id;
        sigLast = 0;
        setStatus("Incoming… tap Join");
        showPanel(true);
        updateButtons(false);
        if(!sigTimer) sigTimer = setInterval(pollSignals, 700);
      }
    }catch(e){}
  }

  function stopCall(){
    try{
      if(sigTimer){ clearInterval(sigTimer); sigTimer=null; }
    }catch(e){}
    try{
      if(pc){ pc.onicecandidate=null; pc.ontrack=null; pc.close(); pc=null; }
    }catch(e){}
    try{
      if(localStream){
        localStream.getTracks().forEach(t=>{ try{ t.stop(); }catch(e){} });
        localStream = null;
      }
    }catch(e){}
    try{ if(remoteVideo) remoteVideo.srcObject = null; }catch(e){}
    try{ if(localVideo) localVideo.srcObject = null; }catch(e){}
    callId = null;
    sigLast = 0;
    pendingOffer = null;
    pendingIce = [];
    isMuted=false; videoOff=false; hideCameras=false;
    if(muteIcon) muteIcon.textContent="🎤";
    if(videoIcon) videoIcon.textContent="🎥";
    if(hideCamIcon) hideCamIcon.textContent="🙈";
    if(allCamsIcon) allCamsIcon.textContent="🎯";
    setStatus("Ready");
    updateButtons(false);
    showPanel(false);
  }

  if(joinBtn){
    joinBtn.addEventListener("click", async (ev)=>{
      try{ ev.preventDefault(); }catch(e){}
      try{
        if(pendingOffer){
          await acceptOffer(pendingOffer);
        }else if(!callId){
          await beginOutgoing();
        }else{
          // waiting for offer
          setStatus("Waiting for connection…");
        }
      }catch(e){
        setStatus((e && e.message) ? e.message : "Call failed (HTTPS required)");
        if(joinBtn) joinBtn.disabled = false;
      }
    });
  }
  if(leaveBtn){
    leaveBtn.addEventListener("click", async (ev)=>{
      try{ ev.preventDefault(); }catch(e){}
      try{ if(callId) await apiPost(`/api/call/${callId}/end`, {}); }catch(e){}
      stopCall();
    });
  }
  if(muteBtn){
    muteBtn.addEventListener("click", ()=>{
      isMuted = !isMuted;
      if(muteIcon) muteIcon.textContent = isMuted ? "🔇" : "🎤";
      try{
        if(localStream){
          const a = localStream.getAudioTracks();
          if(a && a[0]) a[0].enabled = !isMuted;
        }
      }catch(e){}
    });
  }
  if(videoBtn){
    videoBtn.addEventListener("click", ()=>{
      videoOff = !videoOff;
      if(videoIcon) videoIcon.textContent = videoOff ? "🚫" : "🎥";
      try{
        if(localStream){
          const v = localStream.getVideoTracks();
          if(v && v[0]) v[0].enabled = !videoOff && !hideCameras;
        }
      }catch(e){}
    });
  }
  if(hideCamBtn){
    hideCamBtn.addEventListener("click", ()=>{
      hideCameras = !hideCameras;
      if(hideCamIcon) hideCamIcon.textContent = hideCameras ? "👁️" : "🙈";
      try{
        if(videos) videos.style.display = hideCameras ? "none" : "";
        if(localStream){
          const v = localStream.getVideoTracks();
          if(v && v[0]) v[0].enabled = !videoOff && !hideCameras;
        }
      }catch(e){}
    });
  }
  if(toggleVideosBtn){
    toggleVideosBtn.addEventListener("click", ()=>{
      videosCollapsed = !videosCollapsed;
      try{
        if(videos){
          videos.style.display = videosCollapsed ? "none" : (hideCameras ? "none" : "");
        }
        toggleVideosBtn.textContent = videosCollapsed ? "▴" : "▾";
      }catch(e){}
    });
  }
  if(allCamsBtn){
    allCamsBtn.addEventListener("click", ()=>{
      overlayMode = !overlayMode;
      if(allCamsIcon) allCamsIcon.textContent = overlayMode ? "📌" : "🎯";
      try{
        if(!callPanel) return;
        if(overlayMode){
          callPanel.style.position="fixed";
          callPanel.style.left="12px";
          callPanel.style.right="12px";
          callPanel.style.top="70px";
          callPanel.style.zIndex="5500";
          callPanel.style.maxWidth="980px";
          callPanel.style.margin="0 auto";
        }else{
          callPanel.style.position="";
          callPanel.style.left="";
          callPanel.style.right="";
          callPanel.style.top="";
          callPanel.style.zIndex="";
          callPanel.style.maxWidth="";
          callPanel.style.margin="";
        }
      }catch(e){}
    });
  }

  // Call buttons: set desired mode then open panel
  function bindCallBtn(btn, video){
    if(!btn) return;
    btn.addEventListener("click", async (ev)=>{
      try{ ev.preventDefault(); }catch(e){}
      wantVideo = !!video;
      showPanel(true);
      // If an incoming call exists, just show panel; otherwise start outgoing
      try{
        if(!callId){
          await peekForIncoming();
        }
        if(!callId){
          setStatus("Ready");
          updateButtons(false);
          // start immediately with user gesture
          await beginOutgoing();
        }
      }catch(e){
        setStatus((e && e.message) ? e.message : "Call failed (HTTPS required)");
      }
    });
  }
  bindCallBtn(callAudioBtn, false);
  bindCallBtn(callVideoBtn, true);

  // Passive incoming detection
  setInterval(peekForIncoming, 1500);
  if(actDelete){
    actDelete.addEventListener("click", async ()=>{
      if(!activeMid) return;
      try{
        await apiPost(`/api/dm/message/${activeMid}/delete`, {});
        if(activeEl){ activeEl.innerHTML = `<span class="small-muted">Deleted</span>`; activeEl.setAttribute("data-kind","deleted"); }
      }catch(e){ alert(e.message || "Delete failed"); }
      finally{ closeSheet(); }
    });
  }
  if(actEdit){
    actEdit.addEventListener("click", async ()=>{
      if(!activeMid || !activeEl) return;
      const cur = (activeEl.querySelector(".msg-text")||{}).textContent || "";
      const next = prompt("Edit message:", cur);
      if(next === null) return;
      const trimmed = next.trim();
      if(!trimmed){ alert("Message cannot be empty."); return; }
      try{
        await apiPost(`/api/dm/message/${activeMid}/edit`, {body: trimmed});
        let span = activeEl.querySelector(".msg-text");
        if(!span){ span=document.createElement("span"); span.className="msg-text"; activeEl.innerHTML=""; activeEl.appendChild(span); }
        span.textContent = trimmed;
      }catch(e){ alert(e.message || "Edit failed"); }
      finally{ closeSheet(); }
    });
  }


  async function apiPost(url, payload){
    const r = await fetch(url, {
      method:"POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(payload||{})
    });
    let data=null;
    try{ data = await r.json(); }catch(e){}
    if(!r.ok || !data || !data.ok) throw new Error((data && data.error) || "Request failed");
    return data;
  }

  async function pushLocation(coords){
    const now = Date.now();
    if(now - lastPush < 2500) return;
    lastPush = now;

    await apiPost("/api/location/update", {
      lat: coords.latitude,
      lon: coords.longitude,
      accuracy: coords.accuracy || null,
      sharing: true
    });
    lastSent.textContent = "Updated: " + new Date().toLocaleTimeString();
    shareState.textContent = "Sharing";
  }

  async function startWatch(){
    if(!navigator.geolocation){
      geoStatus.textContent = "Geolocation not supported.";
      return;
    }

    // Chrome/Android requires HTTPS (or localhost) for the permission prompt.
    if(!window.isSecureContext){
      const msg = "Geolocation requires HTTPS (or localhost) to request permission.";
      geoStatus.textContent = msg;
      if(secureNote){
        secureNote.style.display = "block";
        secureNote.textContent = msg + " Use the Cloudflared HTTPS link shown in the terminal.";
      }
      try{
        alert(
          "Location permission requires HTTPS (or localhost).\n\n" +
          "Tip: Use the Cloudflared HTTPS link shown on the terminal.\n" +
          "Then tap Start sharing again."
        );
      }catch(e){}
      // Continue anyway; some environments may still allow it.
    } else {
      if(secureNote) secureNote.style.display = "none";
    }

    watching = true;
    shareBtn.textContent = "Stop sharing";
    shareState.textContent = "Sharing";
    geoStatus.textContent = "Requesting permission…";

    // Trigger the permission prompt from a user gesture (button click).
    try{
      const pos = await new Promise((resolve, reject)=>{
        navigator.geolocation.getCurrentPosition(
          (p)=>resolve(p),
          (err)=>reject(err),
          { enableHighAccuracy:true, maximumAge:0, timeout:10000 }
        );
      });
      geoStatus.textContent = "";
      await pushLocation(pos.coords);
    }catch(err){
      watching = false;
      shareBtn.textContent = "Start sharing";
      shareState.textContent = "Not sharing";
      geoStatus.textContent = (err && err.message) ? err.message : "Location unavailable.";
      return;
    }

    watchId = navigator.geolocation.watchPosition(
      (pos)=>{
        geoStatus.textContent = "";
        pushLocation(pos.coords).catch(e=>{ geoStatus.textContent = e.message || "Update failed"; });
      },
      (err)=>{
        geoStatus.textContent = (err && err.message) ? err.message : "Location unavailable.";
      },
      { enableHighAccuracy:true, maximumAge:2000, timeout:10000 }
    );
  }

  async function stopWatch(){
    watching = false;
    shareBtn.textContent = "Start sharing";
    shareState.textContent = "Not sharing";
    lastSent.textContent = "";
    geoStatus.textContent = "";
    try{ if(watchId !== null) navigator.geolocation.clearWatch(watchId); }catch(e){}
    watchId = null;
    try{ await apiPost("/api/location/stop", {}); }catch(e){}
  }

  if(shareBtn){
    shareBtn.addEventListener("click", async ()=>{
      try{
        if(watching) await stopWatch();
        else await startWatch();
      }catch(e){
        geoStatus.textContent = (e && e.message) ? e.message : "Location unavailable.";
      }
    });
  }

  async function refresh(){
    try{
      const r = await fetch("/api/locations");
      const data = await r.json();
      const items = data.items || [];
      if(!items.length){
        locList.innerHTML = `<div class="card-soft p-3 small-muted">No one is sharing location right now.</div>`;
        return;
      }
      locList.innerHTML = items.map(it=>{
        const q = encodeURIComponent((it.lat||0)+","+(it.lon||0));
        const gmap = `https://www.google.com/maps?q=${q}`;
        return `
          <a class="card-soft p-3 d-flex align-items-center justify-content-between gap-2 text-decoration-none hover-lift"
             href="${gmap}" target="_blank" rel="noopener">
            <div class="min-w-0">
              <div class="fw-semibold">${it.user}</div>
              <div class="small-muted">Accuracy: ${Math.round(it.accuracy||0)}m • Updated ${fmtAge(it.updated_at)} ago</div>
            </div>
            <span class="btn btn-sm btn-ghost">Open in Google Maps</span>
          </a>
        `;
      }).join("");
    }catch(e){
      locList.innerHTML = `<div class="card-soft p-3 small-muted">Refresh failed.</div>`;
    }
  }

  refresh();
  setInterval(refresh, 5000);
})();
</script>
{% endblock %}
"""




TEMPLATES["live_locations.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="d-flex flex-column flex-md-row justify-content-between align-items-start gap-2 mb-3">
  <div>
    <h3 class="mb-1">{{ _("Live Locations") }}</h3>
    <div class="small-muted">{{ _("Tip: Keep this page open while sharing. Your position updates automatically.") }}</div>
  </div>

  <div class="d-flex gap-2 flex-wrap align-items-center justify-content-end">
    <span class="badge rounded-pill text-bg-secondary" id="shareState">{{ _("Not sharing") }}</span>
    <button class="btn btn-accent btn-sm" id="btnStart" type="button">{{ _("Start sharing") }}</button>
    <button class="btn btn-ghost btn-sm" id="btnStop" type="button" disabled>{{ _("Stop sharing") }}</button>
    <button class="btn btn-ghost btn-sm" id="btnRefresh" type="button">{{ _("Refresh") if lang=="en" else "Ανανέωση" }}</button>
  </div>
</div>

<div class="card-soft p-3 mb-3">
  <div class="small-muted mb-2">{{ _("Live location") }}</div>
  <div id="myStatus" class="small-muted">{{ _("Requesting permission…") }}</div>
  <div id="myCoords" class="small-muted mt-2" style="display:none;"></div>
  <div id="geoHint" class="small-muted mt-2" style="display:none;"></div>
</div>

<div class="card-soft p-3">
  <div class="d-flex justify-content-between align-items-center mb-2">
    <div class="small-muted">{{ _("People") }}</div>
    <div class="small-muted" id="lastRefresh"></div>
  </div>
  <div id="locList" class="d-grid gap-2"></div>
  <div id="emptyState" class="small-muted" style="display:none;">{{ _("No one is sharing location right now.") }}</div>
</div>

<script nonce="{{ csp_nonce }}">
(function(){
  const elState = document.getElementById("shareState");
  const elMyStatus = document.getElementById("myStatus");
  const elMyCoords = document.getElementById("myCoords");
  const elGeoHint = document.getElementById("geoHint");
  const elList = document.getElementById("locList");
  const elEmpty = document.getElementById("emptyState");
  const elLast = document.getElementById("lastRefresh");
  const btnStart = document.getElementById("btnStart");
  const btnStop = document.getElementById("btnStop");
  const btnRefresh = document.getElementById("btnRefresh");

  const TXT_UPDATED = {{ _("Updated")|tojson }};


  let watchId = null;
  let sharing = false;

  function isSecureContextOk(){
    // Some browsers require HTTPS for geolocation permission prompts.
    if(location.protocol === "https:") return true;
    if(location.hostname === "localhost" || location.hostname === "127.0.0.1") return true;
    return false;
  }

  function setShareUI(on){
    sharing = !!on;
    if(elState){
      elState.textContent = on ? {{ _("Sharing")|tojson }} : {{ _("Not sharing")|tojson }};
      elState.className = on ? "badge rounded-pill text-bg-success" : "badge rounded-pill text-bg-secondary";
    }
    if(btnStart) btnStart.disabled = on;
    if(btnStop) btnStop.disabled = !on;
  }

  async function postJSON(url, body){
    const res = await fetch(url, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(body || {})
    });
    let j = null;
    try{ j = await res.json(); }catch(e){}
    if(!res.ok || !j || j.ok !== true){
      const msg = (j && j.error) ? j.error : "Request failed";
      throw new Error(msg);
    }
    return j;
  }

  async function updateLocation(pos){
    const c = pos && pos.coords ? pos.coords : null;
    if(!c) return;
    const payload = {
      lat: c.latitude,
      lon: c.longitude,
      accuracy: c.accuracy,
      sharing: true
    };
    await postJSON("{{ url_for('api_location_update') }}", payload);
    if(elMyCoords){
      elMyCoords.style.display = "";
      elMyCoords.textContent = `lat ${c.latitude.toFixed(6)}, lon ${c.longitude.toFixed(6)}${(c.accuracy?(" • ±"+Math.round(c.accuracy)+"m"):"")}`;
    }
    if(elMyStatus) elMyStatus.textContent = {{ _("Updated")|tojson }};
  }

  function onGeoError(err){
    try{
      if(elMyStatus){
        if(err && (err.code === 1) && !isSecureContextOk()){
          elMyStatus.textContent = {{ _("Geolocation requires HTTPS to request permission.")|tojson }};
        }else if(err && err.message){
          elMyStatus.textContent = err.message;
        }else{
          elMyStatus.textContent = {{ _("Location unavailable.")|tojson }};
        }
      }
    }catch(e){}
    setShareUI(false);
  }

  async function startSharing(){
    if(!navigator.geolocation){
      if(elMyStatus) elMyStatus.textContent = {{ _("Geolocation not supported.")|tojson }};
      return;
    }
    if(!isSecureContextOk()){
      if(elMyStatus) elMyStatus.textContent = {{ _("Geolocation requires HTTPS to request permission.")|tojson }};
      if(elGeoHint){
        elGeoHint.style.display = "";
        elGeoHint.textContent = {{ _("Geolocation requires HTTPS to request permission.")|tojson }};
      }
      return;
    }
    setShareUI(true);
    if(elMyStatus) elMyStatus.textContent = {{ _("Requesting permission…")|tojson }};

    try{
      watchId = navigator.geolocation.watchPosition(async (pos)=>{
        try{ await updateLocation(pos); }catch(e){}
      }, onGeoError, {
        enableHighAccuracy: true,
        maximumAge: 2000,
        timeout: 15000
      });
    }catch(e){
      onGeoError(e);
    }
  }

  async function stopSharing(){
    try{
      if(watchId !== null){
        navigator.geolocation.clearWatch(watchId);
        watchId = null;
      }
    }catch(e){}
    try{
      await fetch("{{ url_for('api_location_stop') }}", {method:"POST"});
    }catch(e){}
    setShareUI(false);
    if(elMyStatus) elMyStatus.textContent = {{ _("Not sharing")|tojson }};
  }

  function fmtLocal(utc){
    try{
      const d = new Date(utc);
      if(isNaN(d.getTime())) return "";
      return d.toLocaleString([], {year:"numeric", month:"2-digit", day:"2-digit", hour:"2-digit", minute:"2-digit"});
    }catch(e){ return ""; }
  }

  function renderList(items){
    if(!elList) return;
    elList.innerHTML = "";
    const arr = Array.isArray(items) ? items : [];
    if(arr.length === 0){
      if(elEmpty) elEmpty.style.display = "";
      return;
    }
    if(elEmpty) elEmpty.style.display = "none";

    arr.forEach(it=>{
      const card = document.createElement("div");
      card.className = "card-soft p-3 d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center gap-2";

      const left = document.createElement("div");
      left.innerHTML = `<div style="font-weight:700">${(it.nickname||it.username||"")}</div>
                        <div class="small-muted">@${(it.username||"")}</div>
                        <div class="small-muted">${TXT_UPDATED}: ${fmtLocal(it.updated_at||"")}${(it.accuracy?(" • ±"+Math.round(it.accuracy)+"m"):"")}</div>`;

      const right = document.createElement("div");
      right.className = "d-flex gap-2 flex-wrap";
      const a = document.createElement("a");
      a.className = "btn btn-ghost btn-sm";
      a.target = "_blank";
      a.rel = "noopener";
      const lat = Number(it.lat), lon = Number(it.lon);
      a.href = `https://www.google.com/maps?q=${lat},${lon}`;
      a.textContent = {{ _("Open in Google Maps")|tojson }};
      right.appendChild(a);

      card.appendChild(left);
      card.appendChild(right);
      elList.appendChild(card);
    });
  }

  async function refreshLocations(){
    try{
      const res = await fetch("{{ url_for('api_locations') }}", {cache:"no-store"});
      const j = await res.json();
      if(j && j.ok){
        renderList(j.items || []);
        if(elLast) elLast.textContent = ({{ _("Updated")|tojson }} + ": " + (new Date()).toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"}));
      }
    }catch(e){}
  }

  if(btnStart) btnStart.addEventListener("click", ()=>{ startSharing(); });
  if(btnStop) btnStop.addEventListener("click", ()=>{ stopSharing(); });
  if(btnRefresh) btnRefresh.addEventListener("click", ()=>{ refreshLocations(); });

  // Initial state
  setShareUI(false);
  if(!navigator.geolocation){
    if(elMyStatus) elMyStatus.textContent = {{ _("Geolocation not supported.")|tojson }};
  }else if(!isSecureContextOk()){
    if(elMyStatus) elMyStatus.textContent = {{ _("Geolocation requires HTTPS to request permission.")|tojson }};
  }else{
    if(elMyStatus) elMyStatus.textContent = {{ _("Not sharing")|tojson }};
  }

  refreshLocations();
  setInterval(refreshLocations, 5000);

  // Safety: stop sharing on page unload
  window.addEventListener("beforeunload", ()=>{ if(sharing) { try{ stopSharing(); }catch(e){} } });
})();
</script>
{% endblock %}
"""
TEMPLATES["groups.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="d-flex flex-column flex-md-row justify-content-between align-items-start gap-2 mb-3">
  <div>
    <h3 class="mb-1">Groups</h3>
    <div class="small-muted">Chat groups with admins.</div>
  </div>
  <button class="btn btn-accent" data-bs-toggle="collapse" data-bs-target="#createBox">Create group</button>
</div>

<div id="createBox" class="collapse mb-3">
  <div class="card-soft p-3">
    <form method="post" action="{{ url_for('group_create') }}">
      <div class="row g-2">
        <div class="col-12 col-md-4">
          <label class="form-label">Group name</label>
          <input class="form-control" name="name" maxlength="64" required>
        </div>
        <div class="col-12 col-md-8">
          <label class="form-label">Members (comma separated usernames)</label>
          <input class="form-control" name="members" placeholder="alice,bob,charlie">
          <div class="small-muted mt-1">You become owner. You can promote admins in the group page.</div>
        </div>
        <div class="col-12">
          <button class="btn btn-ghost w-100" type="submit">Create</button>
        </div>
      </div>
    </form>
  </div>
</div>

<div class="card-soft p-3">
  <div class="table-responsive">
    <table class="table table-dark table-striped align-middle mb-0">
      <thead>
        <tr><th>{{ _('Name') }}</th><th>Your role</th><th>Created</th><th>{{ _('Actions') }}</th></tr>
      </thead>
      <tbody>
        {% for g in gs %}
          <tr>
            <td>👥 <a href="{{ url_for('group_chat', gid=g.id) }}">{{ g.name }}</a></td>
            <td class="small-muted">{{ g.my_role }}</td>
            <td class="small-muted">{{ g.created_at }}</td>
            <td class="d-flex gap-2 flex-wrap">
              <a class="btn btn-sm btn-accent" href="{{ url_for('group_chat', gid=g.id) }}">Open</a>
              {% if g.my_role == 'owner' %}
                <form method="post" action="{{ url_for('group_delete', gid=g.id) }}" style="display:inline;">
                  <button class="btn btn-sm btn-ghost" type="submit" onclick="return confirm('Delete group and all messages?')">{{ _('Delete') }}</button>
                </form>
              {% else %}
                <form method="post" action="{{ url_for('group_leave', gid=g.id) }}" style="display:inline;">
                  <button class="btn btn-sm btn-ghost" type="submit" onclick="return confirm('Leave group?')">Leave</button>
                </form>
              {% endif %}
            </td>
          </tr>
        {% endfor %}
        {% if not gs %}
          <tr><td colspan="4" class="small-muted">You are not in any groups yet.</td></tr>
        {% endif %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
{% block scripts %}
<script nonce="{{ csp_nonce }}">
(function(){
  const inp=document.getElementById('groupsSearchInput');
  const btn=document.getElementById('groupsSearchBtn');
  function run(){
    const q=((inp&&inp.value)||'').toLowerCase().trim();
    document.querySelectorAll('table tbody tr').forEach(tr=>{
      const txt=(tr.innerText||'').toLowerCase();
      tr.style.display = (!q || txt.includes(q)) ? '' : 'none';
    });
  }
  if(inp) inp.addEventListener('input', run);
  if(btn) btn.addEventListener('click', run);
})();
</script>
{% endblock %}
"""

TEMPLATES["group_chat.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="chat-page">
  <div class="chat-top">
    <div class="card-soft p-3">
      <div class="d-flex justify-content-between align-items-start gap-2 flex-wrap">
        <div class="min-w-0">
          <div class="d-flex align-items-center gap-2 flex-wrap">
            <h4 class="mb-0">👥 {{ g.name }}</h4>
            <span class="small-muted" style="white-space:nowrap">{{ _("Role") }}: <b>{{ my_role }}</b></span>
            <span class="small-muted" style="white-space:nowrap">• {{ _("Owner") }}: {{ g.owner }}</span>
          </div>
          <div class="small-muted mt-1">
            {{ _("Group chat") }} • {{ members|length }} {{ _("members") if lang=="en" else "μέλη" }}
          </div>
        </div>

        <div class="d-flex gap-2 flex-wrap">
          <a class="btn btn-ghost btn-chat-top" href="{{ url_for('groups') }}">{{ _("Back") }}</a>
          {% if ENABLE_CALLS and (members|length > 1) %}
            <button class="btn btn-ghost btn-chat-top" type="button" data-bs-toggle="modal" data-bs-target="#callPickModal">📞/📹 {{ _("Call") }}</button>
          {% endif %}
          {% if my_role in ['owner','admin'] %}
            <button class="btn btn-ghost btn-chat-top" type="button" data-bs-toggle="collapse" data-bs-target="#memberBox">{{ _("Members") }}</button>
          {% endif %}
        </div>
      </div>
    </div>

    {% if my_role in ['owner','admin'] %}
    <div id="memberBox" class="collapse mt-3">
      <div class="card-soft p-3">
        <div class="row g-3">
          <div class="col-12 col-lg-6">
            <div class="small-muted mb-2">{{ _("Members") }}</div>
            <div class="d-flex flex-wrap gap-2 mb-3">
              {% for m in members %}
                <span class="badge badge-soft">
                  {{ "🟢" if m.online else "⚫" }} {{ m.username }} ({{ m.role }})
                </span>
              {% endfor %}
            </div>

            <form method="post" action="{{ url_for('group_add_member', gid=g.id) }}" class="mb-3">
              <label class="form-label">{{ _("Add member") if lang=="en" else "Προσθήκη μέλους" }}</label>
              <div class="d-flex gap-2">
                <input class="form-control" name="username" list="userList2" required>
                <button class="btn btn-ghost" type="submit">{{ _("Add") }}</button>
              </div>
              <datalist id="userList2">{% for u in all_users %}<option value="{{ u }}">{% endfor %}</datalist>
            </form>
          </div>

          <div class="col-12 col-lg-6">
            <div class="small-muted mb-2">{{ _("Admins") if lang=="en" else "Διαχειριστές" }}</div>
            <div class="d-flex flex-wrap gap-2 mb-3">
              {% for m in members if m.role in ['owner','admin'] %}
                <span class="badge badge-soft">{{ "🟢" if m.online else "⚫" }} {{ m.username }} ({{ m.role }})</span>
              {% endfor %}
            </div>

            <form method="post" action="{{ url_for('group_set_admin', gid=g.id) }}" class="mb-3">
              <label class="form-label">{{ _("Set admin") if lang=="en" else "Ορισμός διαχειριστή" }}</label>
              <div class="d-flex gap-2">
                <input class="form-control" name="username" list="memberList2" required>
                <select class="form-select" name="make">
                  <option value="1">{{ _("Make admin") if lang=="en" else "Κάνε διαχειριστή" }}</option>
                  <option value="0">{{ _("Remove admin") if lang=="en" else "Αφαίρεση διαχειριστή" }}</option>
                </select>
                <button class="btn btn-ghost" type="submit">{{ _("Apply") if lang=="en" else "Εφαρμογή" }}</button>
              </div>
              <datalist id="memberList2">{% for m in members %}<option value="{{ m.username }}">{% endfor %}</datalist>
            </form>

            <form method="post" action="{{ url_for('group_remove_member', gid=g.id) }}">
              <label class="form-label">{{ _("Remove member") if lang=="en" else "Αφαίρεση μέλους" }}</label>
              <div class="d-flex gap-2">
                <input class="form-control" name="username" list="memberList3" required>
                <button class="btn btn-ghost" type="submit">{{ _("Remove") }}</button>
              </div>
              <datalist id="memberList3">{% for m in members %}<option value="{{ m.username }}">{% endfor %}</datalist>
            </form>
          </div>
        </div>
      </div>
    </div>
    {% endif %}
  </div>

  <div class="card-soft p-3 mt-3">
    <div class="small-muted mb-2">🔐 {{ _('Group PIN lock') if lang=='en' else 'Κλείδωμα ομάδας με PIN' }}</div>
    {% if has_group_pin %}
      <div class="d-flex gap-2 flex-wrap align-items-end">
        <form method="post" action="{{ url_for('group_lock_set', gid=g.id) }}" class="d-flex gap-2 flex-wrap align-items-end">
          <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
          <div>
            <label class="form-label small-muted">{{ _('Change PIN') if lang=='en' else 'Αλλαγή PIN' }}</label>
            <input class="form-control" type="password" name="pin" inputmode="numeric" pattern="[0-9]*" minlength="4" maxlength="12" required>
          </div>
          <button class="btn btn-ghost" type="submit">{{ _('Save') if lang=='en' else 'Αποθήκευση' }}</button>
        </form>
        <form method="post" action="{{ url_for('group_lock_close', gid=g.id) }}">
          <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
          <button class="btn btn-ghost" type="submit">{{ _('Lock now') if lang=='en' else 'Κλείδωσε τώρα' }}</button>
        </form>
        <form method="post" action="{{ url_for('group_lock_remove', gid=g.id) }}">
          <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
          <button class="btn btn-danger" type="submit">{{ _('Remove PIN') if lang=='en' else 'Αφαίρεση PIN' }}</button>
        </form>
      </div>
    {% else %}
      <form method="post" action="{{ url_for('group_lock_set', gid=g.id) }}" class="d-flex gap-2 flex-wrap align-items-end">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <div>
          <label class="form-label small-muted">{{ _('Set PIN') if lang=='en' else 'Ορισμός PIN' }}</label>
          <input class="form-control" type="password" name="pin" inputmode="numeric" pattern="[0-9]*" minlength="4" maxlength="12" required>
        </div>
        <button class="btn btn-accent" type="submit">{{ _('Enable') if lang=='en' else 'Ενεργοποίηση' }}</button>
      </form>
    {% endif %}
  </div>

  <div class="chat-messages" id="gMsgBox" aria-live="polite">
    {% for m in messages %}
      <div class="msg-row {{ 'me' if m.sender==me else 'them' }}">
        <div class="bubble {{ 'me' if m.sender==me else 'them' }}" data-mid="{{ m.id }}" data-kind="{{ m.kind }}" data-sender="{{ m.sender }}">
          {% if m.sender!=me %}<div class="discuss-sender">@{{ m.sender }}</div>{% endif %}
          {% if m.kind == "text" %}
            <span class="msg-text">{{ m.body }}</span>
          {% elif m.kind == "voice" %}
            <audio controls preload="metadata">
              <source src="{{ url_for('group_voice_stream', vid=m.voice_id) }}" type="{{ m.voice_mime }}">
            </audio>
          {% endif %}
          <div class="meta small-muted">{{ m.created_at_local }}</div>
        </div>
      </div>
    {% endfor %}
  </div>

  <div class="chat-input">
    <form id="gSendForm" class="card-soft p-2" autocomplete="off">
      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
      <div class="d-flex gap-2 align-items-end flex-wrap">
        <div class="flex-grow-1 min-w-0">
          <textarea class="form-control" name="body" id="gBody" rows="1" placeholder="{{ _('Message') }}" autocomplete="off"></textarea>
        </div>

        <div class="d-flex gap-2 align-items-center">
          <label class="btn btn-ghost btn-sm mb-0" title="{{ _('Voice') if lang=='en' else 'Φωνή' }}">
            🎙️ <input type="file" name="voice" id="gVoice" accept="audio/*" hidden>
          </label>
          <button class="btn btn-accent" type="submit" id="gSendBtn">{{ _("Send") }}</button>
        </div>
      </div>
      <div class="small-muted mt-1" id="gHint"></div>
    </form>
  </div>
</div>

{% if ENABLE_CALLS and (members|length > 1) %}
<div class="modal fade" id="callPickModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog modal-dialog-scrollable">
    <div class="modal-content card-soft">
      <div class="modal-header">
        <h5 class="modal-title">{{ _("Call") }}</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
        <div class="small-muted mb-2">{{ _("Choose a member to call") if lang=="en" else "Επέλεξε μέλος για κλήση" }}</div>
        <div class="list-group">
          {% for m in members %}
            {% if m.username != me %}
              <div class="list-group-item d-flex justify-content-between align-items-center gap-2">
                <div class="min-w-0">
                  <div class="fw-semibold text-truncate">{{ m.username }}</div>
                  <div class="small-muted">{{ "🟢 online" if m.online else "⚫ offline" }}</div>
                </div>
                <div class="d-flex gap-2 flex-wrap">
                  <button class="btn btn-ghost btn-sm" type="button" onclick="startMemberCall('{{ m.username }}','audio')" title="Audio">📞</button>
                  <button class="btn btn-ghost btn-sm" type="button" onclick="startMemberCall('{{ m.username }}','video')" title="Video">📹</button>
                </div>
              </div>
            {% endif %}
          {% endfor %}
        </div>
      </div>
    </div>
  </div>
</div>
{% endif %}

<script>
(function(){
  // ----- Group chat AJAX send + poll (same behavior as before, UI aligned to DM chat) -----
  const box = document.getElementById("gMsgBox");
  const form = document.getElementById("gSendForm");
  const bodyEl = document.getElementById("gBody");
  const voiceEl = document.getElementById("gVoice");
  const hint = document.getElementById("gHint");
  let lastId = {{ messages[-1].id if messages else 0 }};

  function scrollToBottom(){
    try { box.scrollTop = box.scrollHeight; } catch(e){}
  }
  scrollToBottom();

  // auto-grow textarea (like chat)
  function autoGrow(el){
    el.style.height = "auto";
    el.style.height = Math.min(140, el.scrollHeight) + "px";
  }
  bodyEl.addEventListener("input", ()=>autoGrow(bodyEl));
  autoGrow(bodyEl);

  function escapeHtml(s){
    return (s||"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;");
  }

  function renderMsg(m){
    const me = "{{ me }}";
    const row = document.createElement("div");
    row.className = "msg-row " + (m.sender===me ? "me" : "them");
    const b = document.createElement("div");
    b.className = "bubble " + (m.sender===me ? "me" : "them");
    b.dataset.mid = m.id;
    b.dataset.kind = m.kind;
    b.dataset.sender = m.sender;

    let inner = "";
    if(m.sender!==me) inner += `<div class="discuss-sender">@${escapeHtml(m.sender)}</div>`;
    if(m.kind==="text"){
      inner += `<span class="msg-text">${escapeHtml(m.body||"")}</span>`;
    } else if(m.kind==="voice"){
      inner += `<audio controls preload="metadata"><source src="${m.voice_url}" type="${escapeHtml(m.voice_mime||"audio/webm")}"></audio>`;
    }
    inner += `<div class="meta small-muted">${escapeHtml(m.created_at_local||"")}</div>`;
    b.innerHTML = inner;
    row.appendChild(b);
    return row;
  }

  async function gSend(){
    const fd = new FormData(form);
    // Always include voice file if selected
    if(voiceEl && voiceEl.files && voiceEl.files[0]){
      fd.set("voice", voiceEl.files[0]);
    }
    const res = await fetch("{{ url_for('group_send', gid=g.id) }}", { method:"POST", body:fd, headers: {"X-Requested-With":"XMLHttpRequest"} });
    const j = await res.json().catch(()=>null);
    if(!j || !j.ok){
      hint.textContent = (j && j.error) ? j.error : "Error";
      return;
    }
    hint.textContent = "";
    bodyEl.value = "";
    voiceEl.value = "";
    autoGrow(bodyEl);
    // append message immediately
    if(j.message){
      lastId = Math.max(lastId||0, Number(j.message.id||0));
      box.appendChild(renderMsg(j.message));
      scrollToBottom();
    }
  }

  form.addEventListener("submit", function(ev){
    ev.preventDefault();
    gSend();
  });

  async function pollNew(){
    const url = `{{ url_for('group_poll', gid=g.id) }}?after=${encodeURIComponent(lastId||0)}`;
    const res = await fetch(url, { method:"GET" });
    const j = await res.json().catch(()=>null);
    if(!j || !j.ok) return;
    const items = j.items || [];
    for(const m of items){
      lastId = Math.max(lastId||0, Number(m.id||0));
      box.appendChild(renderMsg(m));
    }
    if(items.length) scrollToBottom();
  }

  // Adaptive polling like previous template
  let gPollTimer = null;
  let gEmptyStreak = 0;
  function gDelay(){ return Math.min(2200, 450 + gEmptyStreak*150); }
  function gSchedule(d){
    if(gPollTimer) clearTimeout(gPollTimer);
    gPollTimer = setTimeout(gLoop, d);
  }
  async function gLoop(){
    const before = lastId||0;
    await pollNew();
    if((lastId||0) === before) gEmptyStreak = Math.min(20, gEmptyStreak+1);
    else gEmptyStreak = 0;
    gSchedule(gDelay());
  }
  gSchedule(80);

  // Keep presence fresh
  setInterval(()=>fetch("/api/ping", {method:"POST"}), 15000);

  // ----- Calls: 1:1 calls from inside group (picker) -----
  window.startMemberCall = async function(peer, mode){
    try{
      // close modal
      const m = document.getElementById("callPickModal");
      if(m){
        const inst = bootstrap.Modal.getInstance(m);
        if(inst) inst.hide();
      }
    }catch(e){}
    // Reuse the DM call UI by navigating to the direct chat thread, then auto-start call.
    // This keeps backend unchanged and avoids reintroducing passkeys or new call rooms.
    try{
      const url = "{{ url_for('chat_with', username='__PEER__') }}".replace("__PEER__", encodeURIComponent(peer));
      const u = new URL(url, window.location.origin);
      u.searchParams.set("autocall", mode==="video" ? "video" : "audio");
      window.location.href = u.toString();
    }catch(e){
      // fallback: open chat without autocall
      window.location.href = "{{ url_for('chat_with', username='__PEER__') }}".replace("__PEER__", encodeURIComponent(peer));
    }
  };
})();
</script>
{% endblock %}

"""

TEMPLATES["profiler.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="d-flex flex-column flex-md-row justify-content-between align-items-start gap-2 mb-3">
  <div>
    <h3 class="mb-1">Profiler</h3>
    <div class="small-muted">Create/search encrypted profiles (first/last/info + encrypted attachments).</div>
  </div>
  <div class="d-flex gap-2 flex-wrap">
    <button class="btn btn-accent" data-bs-toggle="collapse" data-bs-target="#createBox">{{ _('Create profile') }}</button>
    <form method="post" action="{{ url_for('profiler_export') }}">
      <button class="btn btn-ghost" type="submit">{{ _('Export Profiles') }}</button>
    </form>
    <form method="post" action="{{ url_for('profiler_combine') }}">
      <button class="btn btn-ghost" type="submit">{{ _('Combine Profiles') }}</button>
    </form>
  </div>
</div>

<div class="card-soft p-3 mb-3">
  <form method="get" action="{{ url_for('profiler') }}">
    <label class="form-label">{{ _('Search') }}</label>
    <div class="d-flex gap-2">
      <div class="suggest-wrap w-100">
      <input id="profSearch" class="form-control" name="q" value="{{ q }}" placeholder="Search (decrypts your entries to match)" autocomplete="off">
      <div id="profSuggest" class="suggest-list"></div>
    </div>
      <button class="btn btn-ghost" type="submit">Go</button>
    </div>
    <div class="small-muted mt-2">Search is done locally in the app by decrypting your entries (still stored encrypted).</div>
  </form>
</div>

<div id="createBox" class="collapse mb-3">
  <div class="card-soft p-3">
    <form method="post" action="{{ url_for('profiler_create') }}" enctype="multipart/form-data">
      <div class="row g-2">
        <div class="col-12 col-md-6">
          <label class="form-label">{{ _('First Name') }}</label>
          <input class="form-control" name="first" required maxlength="120">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">{{ _('Last Name') }}</label>
          <input class="form-control" name="last" required maxlength="120">
        </div>
        <div class="col-12">
          <label class="form-label">{{ _('Information') }}</label>
          <textarea class="form-control" name="info" rows="4" maxlength="10000" required></textarea>
        </div>
        <div class="col-12 mt-2">
  <details class="opt-details">
    <summary class="opt-summary" data-closed="⬇️ Optional" data-open="⬆️ Optional">⬇️ Optional</summary>
    <div class="row g-2 mt-2">

        <div class="col-12 col-md-6">
          <label class="form-label">Phone Number (optional)</label>
          <input class="form-control" name="opt_phone" value="" maxlength="60">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">Email (optional)</label>
          <input class="form-control" type="email" name="opt_email" value="" maxlength="120">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">Car Model (optional)</label>
          <input class="form-control" name="opt_car_model" value="" maxlength="120">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">License Plate (optional)</label>
          <input class="form-control" name="opt_license_plate" value="" maxlength="60">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">ID Number (optional)</label>
          <input class="form-control" name="opt_id_number" value="" maxlength="80">
        </div>
        <div class="col-12 col-md-3">
          <label class="form-label">Height (cm) (optional)</label>
          <input class="form-control" name="opt_height_cm" value="" maxlength="10" inputmode="numeric">
        </div>
        <div class="col-12 col-md-3">
          <label class="form-label">Weight (kg) (optional)</label>
          <input class="form-control" name="opt_weight_kg" value="" maxlength="10" inputmode="numeric">
        </div>
        <div class="col-12 col-md-3">
          <label class="form-label">Eye Color (optional)</label>
          <input class="form-control" name="opt_eye_color" value="" maxlength="40">
        </div>
        <div class="col-12 col-md-3">
          <label class="form-label">Hair Color (optional)</label>
          <input class="form-control" name="opt_hair_color" value="" maxlength="40">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">Job (optional)</label>
          <input class="form-control" name="opt_job" value="" maxlength="120">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">Country (optional)</label>
          <input class="form-control" name="opt_country" value="" maxlength="120">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">State (optional)</label>
          <input class="form-control" name="opt_state" value="" maxlength="120">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">Town (optional)</label>
          <input class="form-control" name="opt_town" value="" maxlength="120">
        </div>
        <div class="col-12">
          <label class="form-label">Address (optional)</label>
          <input class="form-control" name="opt_address" value="" maxlength="300">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">Family Members (up to 10) (optional)</label>
          <textarea class="form-control" name="opt_family_members" rows="4" maxlength="2000" placeholder="One per line"></textarea>
          <div class="small-muted mt-1">Tip: one name per line (only first 10 saved).</div>
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">Close Friends (up to 10) (optional)</label>
          <textarea class="form-control" name="opt_close_friends" rows="4" maxlength="2000" placeholder="One per line"></textarea>
          <div class="small-muted mt-1">Tip: one name per line (only first 10 saved).</div>
        </div>

        <div class="col-12">
          <label class="form-label">Attachments (optional)</label>
          <input class="form-control" type="file" name="att" multiple>
          <div class="small-muted mt-1">Attachments are stored (not encrypted).</div>
        </div>
    </div>
  </details>
</div>

        <div class="col-12">
          <button class="btn btn-ghost w-100" type="submit">{{ _('Save (encrypted)') }}</button>
        </div>
      </div>
    </form>
  </div>
</div>

<div class="card-soft p-3">
  <div class="table-responsive">
    <table class="table table-dark table-striped align-middle mb-0">
      <thead><tr><th>ID</th><th>{{ _('Name') }}</th><th>{{ _('Updated') }}</th><th>{{ _('Actions') }}</th></tr></thead>
      <tbody>
        {% for e in entries %}
          <tr>
            <td class="small-muted">#{{ e.id }}</td>
            <td><b>{{ e.first }}</b> {{ e.last }}</td>
            <td class="small-muted">{{ e.updated_at }}</td>
            <td class="d-flex gap-2 flex-wrap">
              <a class="btn btn-sm btn-ghost" href="{{ url_for('profiler_view_only', eid=e.id) }}">{{ _('View') }}</a>
              <a class="btn btn-sm btn-accent" href="{{ url_for('profiler_view', eid=e.id) }}">{{ _('Edit') }}</a>
              <form method="post" action="{{ url_for('profiler_delete', eid=e.id) }}" style="display:inline;" data-first="{{ e.first|e }}" data-last="{{ e.last|e }}" onsubmit="return window.butConfirmProfilerDelete(this);">
                <input type="hidden" name="confirm_full" value="">
                <button class="btn btn-sm btn-ghost" type="submit">{{ _('Delete') }}</button>
              </form>
            </td>
          </tr>
        {% endfor %}
        {% if not entries %}
          <tr><td colspan="4" class="small-muted">{{ _('No entries yet.') }}</td></tr>
        {% endif %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
{% block scripts %}
<script nonce="{{ csp_nonce }}">
(function(){
  const inp = document.getElementById("profSearch");
  const box = document.getElementById("profSuggest");
  let t=null;
  function esc(s){ return (s||"").replace(/[&<>"']/g, c=>({ "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;" }[c])); }
  function render(items){
    if(!items || !items.length){ box.style.display="none"; box.innerHTML=""; return; }
    box.style.display="block";
    box.innerHTML = items.slice(0,10).map(e =>
      `<a class="suggest-item" href="/profiler/${e.id}/view">
         <div class="suggest-left">
           <span class="suggest-name">${esc(e.name)}</span>
         </div>
         <span class="kbd">#${e.id}</span>
       </a>`
    ).join("");
  }
  async function query(q){
    const r = await fetch(`/api/profiler_suggest?q=${encodeURIComponent(q)}`);
    if(!r.ok) return;
    const data = await r.json();
    render(data.entries || []);
  }
  if(inp){
    inp.addEventListener("input", ()=>{
      const q = inp.value.trim();
      if(t) clearTimeout(t);
      if(!q){ box.style.display="none"; box.innerHTML=""; return; }
      t=setTimeout(()=>query(q), 120);
    });
    inp.addEventListener("focus", ()=>{ const q=inp.value.trim(); if(q) query(q); });
    inp.addEventListener("blur", ()=>setTimeout(()=>{ box.style.display="none"; }, 150));
  }
})();
</script>
{% endblock %}
"""


TEMPLATES["bounty.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="d-flex flex-column flex-md-row justify-content-between align-items-start gap-2 mb-3">
  <div>
    <h3 class="mb-1">{{ _('Bounty') }}</h3>
    <div class="small-muted">{{ _('Admins can add, edit, or remove a bounty for an existing Profiler entry.') }}</div>
  </div>
  <a class="btn btn-ghost" href="{{ url_for('profiler') }}">{{ _('Profiler') }}</a>
</div>

<div class="card-soft p-3 mb-3">
  <form method="get" action="{{ url_for('bounty') }}">
    <label class="form-label">{{ _('Search profile to manage bounty') }}</label>
    <div class="d-flex gap-2">
      <input class="form-control" name="q" value="{{ q }}" placeholder="{{ _('Search by ID, name, or owner') }}">
      <button class="btn btn-ghost" type="submit">{{ _('Go') }}</button>
    </div>
    {% if selected_id %}<input type="hidden" name="eid" value="{{ selected_id }}">{% endif %}
    <div class="small-muted mt-2">{{ _('Profiles are hidden by default. Search first, then select one result.') }}</div>
  </form>
</div>

{% if q %}
<div class="card-soft p-3 mb-3">
  <div class="d-flex justify-content-between align-items-center mb-2">
    <div class="fw-bold">{{ _('Search results') }}</div>
    <div class="small-muted">{{ entries|length }} {{ _('shown') }}</div>
  </div>
  <div class="table-responsive">
    <table class="table table-dark table-striped align-middle mb-0">
      <thead>
        <tr>
          <th>ID</th><th>{{ _('Name') }}</th><th>{{ _('Owner') }}</th><th>{{ _('Bounty') }}</th><th>{{ _('Actions') }}</th>
        </tr>
      </thead>
      <tbody>
      {% for e in entries %}
        <tr>
          <td class="small-muted">#{{ e.id }}</td>
          <td><b>{{ e.first }}</b> {{ e.last }}</td>
          <td class="small-muted">{{ e.owner }}</td>
          <td>{% if e.bounty_price is not none %}<b>{{ e.bounty_price_display }}</b>{% else %}<span class="small-muted">—</span>{% endif %}</td>
          <td><a class="btn btn-sm btn-ghost" href="{{ url_for('bounty', q=q, eid=e.id) }}">{{ _('Select') }}</a></td>
        </tr>
      {% endfor %}
      {% if not entries %}<tr><td colspan="5" class="small-muted">{{ _('No profiles found.') }}</td></tr>{% endif %}
      </tbody>
    </table>
  </div>
</div>
{% endif %}

<div class="card-soft p-3 mb-3">
  {% if selected %}
    <div class="mb-3">
      <div><b>{{ _('Selected') }}:</b> #{{ selected.id }} • {{ selected.first }} {{ selected.last }}</div>
      <div class="small-muted">{{ _('Owner') }}: {{ selected.owner }}</div>
      {% if selected.bounty_price is not none %}
        <div class="small-muted">{{ _('Current bounty') }}: {{ selected.bounty_price_display }}{% if selected.bounty_updated_at %} • {{ _('Updated') }} {{ selected.bounty_updated_at }}{% endif %}{% if selected.bounty_set_by %} • {{ _('by') }} {{ selected.bounty_set_by }}{% endif %}</div>
        <div class="small-muted">{{ _('Reason') }}: {{ selected.bounty_reason or '—' }}</div>
      {% else %}
        <div class="small-muted">{{ _('No bounty set.') }}</div>
      {% endif %}
    </div>

    <form method="post" action="{{ url_for('bounty_set') }}">
      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
      <input type="hidden" name="eid" value="{{ selected.id }}">
      <div class="row g-2 align-items-end">
        <div class="col-12 col-lg-3">
          <label class="form-label">{{ _('Bounty price') }}</label>
          <input class="form-control" type="number" step="0.01" min="0" name="price" value="{{ selected_bounty_value }}" placeholder="0.00" required>
          <div class="small-muted mt-1">{{ _('Currency changes by language ($ EN / € EL).') }}</div>
        </div>
        <div class="col-12 col-lg-7">
          <label class="form-label">{{ _('Reason') }}</label>
          <textarea class="form-control" name="reason" rows="2" maxlength="333" required placeholder="{{ _('Required (max 333 characters)') }}">{{ selected_reason_value }}</textarea>
          <div class="small-muted mt-1">{{ _('Reason is required and limited to 333 characters.') }}</div>
        </div>
        <div class="col-12 col-lg-2 d-grid">
          <button class="btn btn-accent" type="submit">{% if selected_has_bounty %}{{ _('Update Bounty') }}{% else %}{{ _('Add Bounty') }}{% endif %}</button>
        </div>
      </div>
    </form>

    <div class="d-flex gap-2 mt-3 flex-wrap">
      <a class="btn btn-sm btn-ghost" href="{{ url_for('profiler_view_only', eid=selected.id) }}">{{ _('View') }}</a>
      {% if selected.bounty_price is not none %}
      <form method="post" action="{{ url_for('bounty_remove') }}" onsubmit="return confirm('{{ _('Remove bounty from this profile?') }}');">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <input type="hidden" name="eid" value="{{ selected.id }}">
        <button class="btn btn-sm btn-ghost" type="submit">{{ _('Remove Bounty') }}</button>
      </form>
      {% endif %}
    </div>
  {% else %}
    <div class="small-muted">{{ _('Search and select a profile to add or edit a bounty.') }}</div>
  {% endif %}
</div>
{% endblock %}
"""

TEMPLATES["profiler_view.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="card-soft p-4">
  <div class="d-flex justify-content-between align-items-start gap-2">
    <div>
      <h3 class="mb-1">Profiler Entry #{{ e.id }}</h3>
      <div class="small-muted"> • Owner: {{ e.owner }}</div>
    </div>
    <a class="btn btn-ghost" href="{{ url_for('profiler') }}">{{ _('Back') }}</a>
  </div>
  <hr/>

  {% if e.bounty_price is not none %}
  <div class="card-soft p-3 mb-3">
    <div class="fw-bold mb-1">{{ _('Bounty') }}</div>
    <div><b>{{ e.bounty_price_display or e.bounty_price }}</b></div>
    <div class="small-muted">{{ _('Reason') }}: {{ e.bounty_reason or '—' }}</div>
    {% if e.bounty_updated_at or e.bounty_set_by %}
      <div class="small-muted">{% if e.bounty_updated_at %}{{ _('Updated') }} {{ e.bounty_updated_at }}{% endif %}{% if e.bounty_set_by %}{% if e.bounty_updated_at %} • {% endif %}{{ _('by') }} {{ e.bounty_set_by }}{% endif %}</div>
    {% endif %}
  </div>
  {% endif %}

  <form method="post" action="{{ url_for('profiler_update', eid=e.id) }}" enctype="multipart/form-data" data-first="{{ e.first|e }}" data-last="{{ e.last|e }}">
    <input type="hidden" name="confirm_full" value="">
    <div class="row g-2">
      <div class="col-12 col-md-6">
        <label class="form-label">{{ _('First Name') }}</label>
        <input class="form-control" name="first" value="{{ e.first }}" required maxlength="120">
      </div>
      <div class="col-12 col-md-6">
        <label class="form-label">{{ _('Last Name') }}</label>
        <input class="form-control" name="last" value="{{ e.last }}" required maxlength="120">
      </div>
      <div class="col-12">
        <label class="form-label">{{ _('Information') }}</label>
        <textarea class="form-control" name="info" rows="5" maxlength="10000" required>{{ e.info }}</textarea>
      </div>
        <div class="col-12 mt-2">
  <details class="opt-details">
    <summary class="opt-summary" data-closed="⬇️ Optional" data-open="⬆️ Optional">⬇️ Optional</summary>
    <div class="row g-2 mt-2">

        <div class="col-12 col-md-6">
          <label class="form-label">Phone Number (optional)</label>
          <input class="form-control" name="opt_phone" value="{{ e.opt.get('phone','') if e is defined else '' }}" maxlength="60">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">Email (optional)</label>
          <input class="form-control" type="email" name="opt_email" value="{{ e.opt.get('email','') if e is defined else '' }}" maxlength="120">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">Car Model (optional)</label>
          <input class="form-control" name="opt_car_model" value="{{ e.opt.get('car_model','') if e is defined else '' }}" maxlength="120">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">License Plate (optional)</label>
          <input class="form-control" name="opt_license_plate" value="{{ e.opt.get('license_plate','') if e is defined else '' }}" maxlength="60">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">ID Number (optional)</label>
          <input class="form-control" name="opt_id_number" value="{{ e.opt.get('id_number','') if e is defined else '' }}" maxlength="80">
        </div>
        <div class="col-12 col-md-3">
          <label class="form-label">Height (cm) (optional)</label>
          <input class="form-control" name="opt_height_cm" value="{{ e.opt.get('height_cm','') if e is defined else '' }}" maxlength="10" inputmode="numeric">
        </div>
        <div class="col-12 col-md-3">
          <label class="form-label">Weight (kg) (optional)</label>
          <input class="form-control" name="opt_weight_kg" value="{{ e.opt.get('weight_kg','') if e is defined else '' }}" maxlength="10" inputmode="numeric">
        </div>
        <div class="col-12 col-md-3">
          <label class="form-label">Eye Color (optional)</label>
          <input class="form-control" name="opt_eye_color" value="{{ e.opt.get('eye_color','') if e is defined else '' }}" maxlength="40">
        </div>
        <div class="col-12 col-md-3">
          <label class="form-label">Hair Color (optional)</label>
          <input class="form-control" name="opt_hair_color" value="{{ e.opt.get('hair_color','') if e is defined else '' }}" maxlength="40">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">Job (optional)</label>
          <input class="form-control" name="opt_job" value="{{ e.opt.get('job','') if e is defined else '' }}" maxlength="120">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">Country (optional)</label>
          <input class="form-control" name="opt_country" value="{{ e.opt.get('country','') if e is defined else '' }}" maxlength="120">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">State (optional)</label>
          <input class="form-control" name="opt_state" value="{{ e.opt.get('state','') if e is defined else '' }}" maxlength="120">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">Town (optional)</label>
          <input class="form-control" name="opt_town" value="{{ e.opt.get('town','') if e is defined else '' }}" maxlength="120">
        </div>
        <div class="col-12">
          <label class="form-label">Address (optional)</label>
          <input class="form-control" name="opt_address" value="{{ e.opt.get('address','') if e is defined else '' }}" maxlength="300">
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">Family Members (up to 10) (optional)</label>
          <textarea class="form-control" name="opt_family_members" rows="4" maxlength="2000" placeholder="One per line">{{ e.opt.get('family_members','') if e is defined else '' }}</textarea>
          <div class="small-muted mt-1">Tip: one name per line (only first 10 saved).</div>
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">Close Friends (up to 10) (optional)</label>
          <textarea class="form-control" name="opt_close_friends" rows="4" maxlength="2000" placeholder="One per line">{{ e.opt.get('close_friends','') if e is defined else '' }}</textarea>
          <div class="small-muted mt-1">Tip: one name per line (only first 10 saved).</div>
        </div>

      <div class="col-12">
        <label class="form-label">Add attachment (optional)</label>
        <input class="form-control" type="file" name="att">
      </div>
    </div>
  </details>
</div>

      <div class="col-12 d-flex gap-2 flex-wrap">
        <button class="btn btn-accent" type="submit">{{ _('Save changes') }}</button>
        <button class="btn btn-ghost" type="submit" formaction="{{ url_for('profiler_delete', eid=e.id) }}" formmethod="post" onclick="return window.butConfirmProfilerDelete(this.form);">{{ _('Delete') }}</button>
      </div>
    </div>
  </form>

  <hr/>
  <h5 class="mb-2">{{ _('Attachments') }}</h5>
  {% if attachments %}
    <div class="d-flex flex-column gap-2">
      {% for a in attachments %}
        <div class="card-soft p-3 d-flex justify-content-between align-items-center flex-wrap gap-2">
          <div>
            <div><b>{{ a.filename }}</b></div>
            <div class="small-muted">{{ a.mime }}</div>
          </div>
          <div class="d-flex gap-2">
            <a class="btn btn-sm btn-ghost" href="{{ url_for('profiler_att_download', aid=a.id) }}">{{ _('Download') }}</a>
            <form method="post" action="{{ url_for('profiler_att_delete', aid=a.id) }}" style="display:inline;">
              <button class="btn btn-sm btn-ghost" type="submit" onclick='return confirm({{ _("Delete attachment?")|tojson }})'>{{ _('Delete') }}</button>
            </form>
          </div>
        </div>
      {% endfor %}
    </div>
  {% else %}
    <div class="small-muted">{{ _('No attachments.') }}</div>
  {% endif %}
</div>
{% endblock %}
"""

TEMPLATES["profiler_view_only.html"] = r"""{% extends "base.html" %}
{% block content %}
<div class="d-flex flex-column flex-md-row justify-content-between align-items-start gap-2 mb-3">
  <div>
    <h3 class="mb-1">Profiler • View</h3>
    <div class="small-muted">Entry #{{ e.id }} • Updated {{ e.updated_at }}</div>
  </div>
  <div class="d-flex gap-2 flex-wrap">
    <a class="btn btn-ghost" href="{{ url_for('profiler') }}">{{ _('Back') }}</a>
    <a class="btn btn-accent" href="{{ url_for('profiler_view', eid=e.id) }}">{{ _('Edit') }}</a>
  </div>
</div>

<div class="card-soft p-3">
{% if e.bounty_price is not none %}
  <div class="card-soft p-3 mb-3">
    <div class="fw-bold mb-1">{{ _('Bounty') }}</div>
    <div><b>{{ e.bounty_price_display or e.bounty_price }}</b></div>
    <div class="small-muted">{{ _('Reason') }}: {{ e.bounty_reason or '—' }}</div>
    {% if e.bounty_updated_at or e.bounty_set_by %}
      <div class="small-muted">{% if e.bounty_updated_at %}{{ _('Updated') }} {{ e.bounty_updated_at }}{% endif %}{% if e.bounty_set_by %}{% if e.bounty_updated_at %} • {% endif %}{{ _('by') }} {{ e.bounty_set_by }}{% endif %}</div>
    {% endif %}
  </div>
  {% endif %}

  <div class="row g-3">
    <div class="col-12 col-md-6">
      <label class="form-label">{{ _('First Name') }}</label>
      <div class="read-box">{{ e.first }}</div>
    </div>
    <div class="col-12 col-md-6">
      <label class="form-label">{{ _('Last Name') }}</label>
      <div class="read-box">{{ e.last }}</div>
    </div>
    <div class="col-12">
      <label class="form-label">{{ _('Information') }}</label>
      <div class="read-box">{{ e.info }}</div>
    </div>
    {% set o = e.opt or {} %}
    {% if o and (o.get('phone') or o.get('email') or o.get('car_model') or o.get('license_plate') or o.get('id_number') or o.get('height_cm') or o.get('weight_kg') or o.get('eye_color') or o.get('hair_color') or o.get('job') or o.get('country') or o.get('state') or o.get('town') or o.get('address') or o.get('family_members') or o.get('close_friends')) %}
    <div class="col-12">
      <label class="form-label mt-2">{{ _('Optional details') }}</label>
      <div class="read-box">
        {% for key,label in [
          ('phone','Phone Number'),
          ('email','Email'),
          ('car_model','Car Model'),
          ('license_plate','License Plate'),
          ('id_number','ID Number'),
          ('height_cm','Height (cm)'),
          ('weight_kg','Weight (kg)'),
          ('eye_color','Eye Color'),
          ('hair_color','Hair Color'),
          ('job','Job'),
          ('country','Country'),
          ('state','State'),
          ('town','Town'),
          ('address','Address')
        ] %}
          {% if o.get(key) %}
            <div><b>{{ label }}:</b> {{ o.get(key) }}</div>
          {% endif %}
        {% endfor %}
        {% if o.get('family_members') %}
          <div class="mt-2"><b>Family Members:</b><br>{{ o.get('family_members')|e|replace('
','<br>')|safe }}</div>
        {% endif %}
        {% if o.get('close_friends') %}
          <div class="mt-2"><b>Close Friends:</b><br>{{ o.get('close_friends')|e|replace('
','<br>')|safe }}</div>
        {% endif %}
      </div>
    </div>
    {% endif %}

  </div>
</div>

<div class="card-soft p-3 mt-3">
  <div class="d-flex justify-content-between align-items-start gap-2">
    <div>
      <h5 class="mb-1">{{ _('Attachments') }}</h5>
      <div class="small-muted">Attachments stored inside Profiler.</div>
    </div>
    <a class="btn btn-ghost btn-sm" href="{{ url_for('profiler_view', eid=e.id) }}">{{ _('Add attachment') }}</a>
  </div>
  <hr/>
  {% if attachments %}
    <div class="d-grid gap-2">
      {% for a in attachments %}
        <div class="user-item">
          <div class="avatar-fallback">📎</div>
          <div class="flex-grow-1">
            <div class="fw-bold">{{ a.filename }}</div>
            <div class="small-muted">{{ a.size_h }}</div>
          </div>
          <a class="btn btn-ghost btn-sm" href="{{ url_for('profiler_att_download', aid=a.id) }}">{{ _('Download') }}</a>
        </div>
      {% endfor %}
    </div>
  {% else %}
    <div class="small-muted">{{ _('No attachments.') }}</div>
  {% endif %}
</div>

<div class="card-soft p-3 mt-3">
  <form method="post" action="{{ url_for('profiler_delete', eid=e.id) }}" data-first="{{ e.first|e }}" data-last="{{ e.last|e }}" onsubmit="return window.butConfirmProfilerDelete(this);">
    <input type="hidden" name="confirm_full" value="">
    <button class="btn btn-ghost" type="submit">{{ _('Delete') }}</button>
  </form>
</div>
{% endblock %}"""

# ---------------------------
# ---------------------------




TEMPLATES["admin_user_files.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="d-flex flex-column flex-md-row justify-content-between align-items-start gap-2 mb-3">
  <div>
    <h3 class="mb-1">User Files – @{{ username }}</h3>
    <div class="small-muted">Path: /{{ relpath }}</div>
  </div>
  <div class="d-flex flex-wrap gap-2">
    <a class="btn btn-ghost" href="{{ url_for('admin_user_files', username=username, p=parent_relpath, sort=sort, order=order) }}">Up</a>
    <a class="btn btn-ghost" href="{{ url_for('admin_panel') }}">Back to Admin</a>
  </div>
</div>

<div class="card-soft p-3">
  <div class="table-responsive">
    <table class="table table-dark table-striped align-middle mb-0">
      <thead>
        <tr>
          <th style="width:40%">{{ _('Name') }}</th>
          <th style="width:18%">Type</th>
          <th style="width:12%">Size</th>
          <th style="width:18%">Modified</th>
          <th style="width:12%">{{ _('Actions') }}</th>
        </tr>
      </thead>
      <tbody>
        {% for e in entries %}
          <tr>
            <td>
              {% if e.is_dir %}
                📁 <a href="{{ url_for('admin_user_files', username=username, p=child_path(relpath, e.name), sort=sort, order=order) }}">{{ e.name }}</a>
              {% else %}
                📄 {{ e.name }}
              {% endif %}
            </td>
            <td><span class="small-muted">{{ e.kind }}</span></td>
            <td>{{ e.size_h }}</td>
            <td class="small-muted">{{ e.mtime_h }}</td>
            <td>
              {% if not e.is_dir %}
                <a class="btn btn-sm btn-ghost" href="{{ url_for('admin_user_download', username=username, p=child_path(relpath, e.name)) }}">{{ _('Download') }}</a>
              {% endif %}
            </td>
          </tr>
        {% endfor %}
        {% if not entries %}
          <tr><td colspan="5" class="small-muted">Empty folder.</td></tr>
        {% endif %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
"""

# ---------------------------
# Load templates
# ---------------------------

TEMPLATES["settings_security.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="row g-3">
  <div class="col-12 col-lg-6">
    <div class="card-soft p-4">
      <div class="d-flex justify-content-between align-items-start gap-2 flex-wrap mb-2"><div><h3 class="mb-1">{{ _("Settings") }}</h3></div><a class="btn btn-ghost" href="{{ request.referrer or url_for('profiler') }}">{{ _("Back") }}</a></div>
      <div class="small-muted">{{ _("Account security") }}</div>
      <hr class="my-3"/>

      <h5 class="mb-2">{{ _("Change password") }}</h5>
      <form method="post" action="{{ url_for('settings_change_password') }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <div class="mb-2">
          <label class="form-label">{{ _("Current password") }}</label>
          <input class="form-control" type="password" name="current_password" required>
        </div>
        <div class="mb-2">
          <label class="form-label">{{ _("New password") }}</label>
          <input class="form-control" type="password" name="new_password" required>
        </div>
        <div class="mb-3">
          <label class="form-label">{{ _("Confirm new password") }}</label>
          <input class="form-control" type="password" name="new_password2" required>
        </div>
        <button class="btn btn-accent" type="submit">{{ _("Update") }}</button>
      </form>
    </div>
  </div>

  <div class="col-12 col-lg-6">
    <div class="card-soft p-4">
      <h5 class="mb-2">{{ _("2-factor authentication (security questions)") }}</h5>
      <div class="small-muted mb-3">{{ _("Not as strong as an authenticator app, but it adds an extra step after your password.") }}</div>

      <form method="post" action="{{ url_for('settings_security_questions') }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

        <div class="mb-2">
          <label class="form-label">{{ _("Question 1") }}</label>
          <input class="form-control" name="q1" maxlength="120" value="{{ sec.q1 }}" placeholder="{{ _('e.g. What was your first pet\'s name?') }}">
        </div>
        <div class="mb-2">
          <label class="form-label">{{ _("Answer 1") }}</label>
          <input class="form-control" name="a1" maxlength="120" placeholder="{{ _("Leave blank to keep existing answer") }}">
        </div>

        <div class="mb-2">
          <label class="form-label">{{ _("Question 2") }}</label>
          <input class="form-control" name="q2" maxlength="120" value="{{ sec.q2 }}" placeholder="{{ _("e.g. City you were born in?") }}">
        </div>
        <div class="mb-2">
          <label class="form-label">{{ _("Answer 2") }}</label>
          <input class="form-control" name="a2" maxlength="120" placeholder="{{ _("Leave blank to keep existing answer") }}">
        </div>

        <div class="mb-2">
          <label class="form-label">{{ _("Question 3") }}</label>
          <input class="form-control" name="q3" maxlength="120" value="{{ sec.q3 }}" placeholder="{{ _('e.g. Favorite teacher\'s last name?') }}">
        </div>
        <div class="mb-3">
          <label class="form-label">{{ _("Answer 3") }}</label>
          <input class="form-control" name="a3" maxlength="120" placeholder="{{ _("Leave blank to keep existing answer") }}">
        </div>

        <div class="form-check mb-3">
          <input class="form-check-input" type="checkbox" id="en2fa" name="enable_2fa" value="1" {% if sec.enabled %}checked{% endif %}>
          <label class="form-check-label" for="en2fa">{{ _("Enable 2FA on login") }}</label>
        </div>

        <button class="btn btn-accent" type="submit">{{ _("Save") }}</button>
      </form>

      <div class="small-muted mt-3">{{ _("Password recovery uses these same questions at") }} <span class="kbd">/recover</span>.</div>
    </div>
  </div>

  <div class="col-12">
    <div class="card-soft p-4">
      <div class="d-flex justify-content-between align-items-center gap-2 mb-2"><h5 class="mb-0">{{ _("Appearance") }}</h5><a class="btn btn-sm btn-ghost" href="{{ url_for('settings_appearance_page') }}">{{ _("Open full appearance settings") }}</a></div>
      <div class="small-muted mb-3">{{ _("Customize theme style, accent color, and font (saved per account).") }}</div>

      <form method="post" action="{{ url_for('settings_appearance') }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <div class="row g-2">
          <div class="col-12 col-md-6">
            <label class="form-label">{{ _("Theme style") }}</label>
            <select class="form-select" name="ui_theme">
              {% for t in ui_theme_choices %}
                <option value="{{ t.key }}" {% if prefs.ui_theme_key == t.key %}selected{% endif %}>{{ _(t.label) }}</option>
              {% endfor %}
            </select>
            <div class="small-muted mt-2">{{ _("This changes the saved color style for the interface.") }}</div>
          </div>
          <div class="col-12 col-md-6">
            <label class="form-label">{{ _("Appearance mode") }}</label>
            <select class="form-select" id="themeModeSelect" name="theme_mode">
              <option value="dark">{{ _("Dark") }}</option>
              <option value="light">{{ _("Light") }}</option>
              <option value="system">{{ _("System") }}</option>
            </select>
            <div class="small-muted mt-2">{{ _("This changes only the dark/light mode for this browser on this device.") }}</div>
          </div>
          <div class="col-12 col-md-6">
            <label class="form-label">{{ _("Accent color") }}</label>
            <select class="form-select" name="accent">
              {% for c in accent_choices %}
                <option value="{{ c.key }}" {% if prefs.accent_key == c.key %}selected{% endif %}>{{ c.label }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="col-12 col-md-6">
            <label class="form-label">{{ _("Font") }}</label>
            <select class="form-select" name="font">
              {% for f in font_choices %}
                <option value="{{ f.key }}" {% if prefs.font_key == f.key %}selected{% endif %}>{{ f.label }}</option>
              {% endfor %}
            </select>
          </div>
        </div>
        <button class="btn btn-accent mt-3" type="submit">{{ _("Save") }}</button>
      </form>
    </div>
  </div>

</div>
{% endblock %}
{% block scripts %}
<script nonce="{{ csp_nonce }}">
(function(){
  const form = document.querySelector('form[action="{{ url_for('settings_appearance') }}"]');
  const sel = document.getElementById('themeModeSelect');
  if(!sel) return;
  try{ if(window.butGetThemeMode) sel.value = window.butGetThemeMode(); }catch(e){}
  const applyNow = ()=>{ try{ if(window.butSetThemeMode) window.butSetThemeMode(sel.value || 'dark'); }catch(e){} };
  sel.addEventListener('change', applyNow);
  if(form){ form.addEventListener('submit', applyNow); }
})();
</script>
{% endblock %}
"""


TEMPLATES["settings_appearance.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="row g-3">
  <div class="col-12 col-xl-8">
    <div class="card-soft p-4">
      <div class="d-flex flex-wrap justify-content-between gap-2 align-items-start mb-3">
        <div>
          <h3 class="mb-1">{{ _("Appearance") }}</h3>
          <div class="small-muted">{{ _("Themes and fonts are here. Choose your saved interface style for this account.") }}</div>
        </div>
        <div class="d-flex gap-2 flex-wrap">
          <a class="btn btn-ghost" href="{{ url_for('settings_root') }}">{{ _("Security settings") }}</a>
        </div>
      </div>
      <form method="post" action="{{ url_for('settings_appearance') }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <div class="row g-3">
          <div class="col-12 col-md-6">
            <label class="form-label">{{ _("Theme style") }}</label>
            <select class="form-select" name="ui_theme">
              {% for t in ui_theme_choices %}
                <option value="{{ t.key }}" {% if prefs.ui_theme_key == t.key %}selected{% endif %}>{{ _(t.label) }}</option>
              {% endfor %}
            </select>
            <div class="small-muted mt-2">{{ _("30 saved color styles are available here.") }}</div>
          </div>
          <div class="col-12 col-md-6">
            <label class="form-label">{{ _("Appearance mode") }}</label>
            <select class="form-select" id="themeModeSelect" name="theme_mode">
              <option value="dark">{{ _("Dark") }}</option>
              <option value="light">{{ _("Light") }}</option>
              <option value="system">{{ _("System") }}</option>
            </select>
            <div class="small-muted mt-2">{{ _("This changes only the dark/light mode for this browser on this device.") }}</div>
          </div>
          <div class="col-12 col-md-6">
            <label class="form-label">{{ _("Accent color") }}</label>
            <select class="form-select" name="accent">
              {% for c in accent_choices %}
                <option value="{{ c.key }}" {% if prefs.accent_key == c.key %}selected{% endif %}>{{ c.label }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="col-12 col-md-6">
            <label class="form-label">{{ _("Font") }}</label>
            <select class="form-select" name="font">
              {% for f in font_choices %}
                <option value="{{ f.key }}" {% if prefs.font_key == f.key %}selected{% endif %}>{{ _(f.label) }}</option>
              {% endfor %}
            </select>
            <div class="small-muted mt-2">{{ _("12 Greek and English friendly font stacks are available here.") }}</div>
          </div>
        </div>
        <button class="btn btn-accent mt-3" type="submit">{{ _("Save") }}</button>
      </form>
    </div>
  </div>
</div>
{% endblock %}
{% block scripts %}
<script nonce="{{ csp_nonce }}">
(function(){
  const sel = document.getElementById('themeModeSelect');
  if(!sel) return;
  try{ if(window.butGetThemeMode) sel.value = window.butGetThemeMode(); }catch(e){}
  const applyNow = ()=>{ try{ if(window.butSetThemeMode) window.butSetThemeMode(sel.value || 'dark'); }catch(e){} };
  sel.addEventListener('change', applyNow);
})();
</script>
{% endblock %}
"""

TEMPLATES["two_factor.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-12 col-md-8 col-lg-6">
    <div class="card-soft p-4">
      <h3 class="mb-1">2FA check</h3>
      <div class="small-muted mb-3">Answer the questions to finish logging in as <b>@{{ username }}</b>.</div>

      <form method="post" action="{{ url_for('two_factor') }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        {% for i,q in qs %}
          <div class="mb-3">
            <label class="form-label">{{ q }}</label>
            <input class="form-control" type="password" name="a{{ i+1 }}" required>
          </div>
        {% endfor %}
        <button class="btn btn-accent w-100" type="submit">Verify</button>
      </form>
      <div class="text-center mt-3"><a class="link-light" href="{{ url_for('login') }}">Back to login</a></div>
    </div>
  </div>
</div>
{% endblock %}
"""

TEMPLATES["recover.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-12 col-md-10 col-lg-7">
    <div class="card-soft p-4">
      <h3 class="mb-1">Password recovery</h3>
      <div class="small-muted mb-3">Recover your account using your security questions.</div>

      {% if not ask %}
        <form method="post" action="{{ url_for('recover') }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
          <input type="hidden" name="step" value="user">
          <div class="mb-3">
            <label class="form-label">Username</label>
            <input class="form-control" name="username" required>
          </div>
          <button class="btn btn-accent" type="submit">Continue</button>
        </form>
      {% else %}
        <form method="post" action="{{ url_for('recover') }}">
          <input type="hidden" name="step" value="reset">
          <input type="hidden" name="username" value="{{ username }}">
          <div class="mb-3"><span class="badge badge-soft">@{{ username }}</span></div>

          {% for n,q in qs %}
            <div class="mb-3">
              <label class="form-label">{{ q }}</label>
              <input class="form-control" type="password" name="a{{ n }}" required>
            </div>
          {% endfor %}

          <hr class="my-3"/>

          <div class="mb-2">
            <label class="form-label">New password</label>
            <input class="form-control" type="password" name="new_password" required>
          </div>
          <div class="mb-3">
            <label class="form-label">Confirm new password</label>
            <input class="form-control" type="password" name="new_password2" required>
          </div>

          <button class="btn btn-accent" type="submit">Reset password</button>
        </form>
      {% endif %}

      <div class="text-center mt-3"><a class="link-light" href="{{ url_for('login') }}">Back to login</a></div>
    </div>
  </div>
</div>
{% endblock %}
"""

TEMPLATES["face_detector.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="d-flex flex-column flex-md-row justify-content-between align-items-start gap-2 mb-3">
  <div>
    <h3 class="mb-1">{{ _("Face Detector") }}</h3>
  </div>
  <div class="small-muted">{{ _("Saved captures go to your Downloads/ButSystem/Face Detector folder when available.") }}</div>
</div>

<div class="card-soft p-3 p-md-4 fd-root">
  <div class="fd-top-info mb-3">
    <div class="fd-status-line" id="fdStatus">{{ _("Ready. Tap Start camera.") }}</div>
    <div class="fd-sub-line" id="fdServerStatus">{{ _("SERVER: STANDBY") }}</div>
    <div class="fd-sub-line" id="fdSourceStatus">{{ _("SOURCE: LIVE CAMERA") }}</div>
  </div>

  <div class="fd-controls mb-3">
    <button class="btn btn-ghost fd-ctrl" type="button" id="fdStart">{{ _("Start camera") }}</button>
    <button class="btn btn-ghost fd-ctrl" type="button" id="fdSwitch">{{ _("Switch camera") }}</button>
    <label class="btn btn-ghost mb-0 fd-ctrl" for="fdUpload">{{ _("Upload photo/video") }}</label>
    <input id="fdUpload" type="file" accept="image/*,video/*" hidden>
    <button class="btn btn-accent fd-ctrl" type="button" id="fdSave">{{ _("Save result") }}</button>
    <button class="btn btn-ghost fd-ctrl" type="button" id="fdBackLive">{{ _("Back to live camera") }}</button>
    {% if is_admin and fd_bounty_refs %}
      <select class="form-control fd-ctrl fd-select" id="fdRefSelect">
        <option value="">{{ _("Bounty reference photo") }}</option>
        {% for ref in fd_bounty_refs %}
          <option value="{{ ref.preview_url }}">#{{ ref.id }} • {{ ref.first }} {{ ref.last }}{% if ref.bounty_price_display %} • {{ ref.bounty_price_display }}{% endif %}</option>
        {% endfor %}
      </select>
      <button class="btn btn-ghost fd-ctrl" type="button" id="fdClearRef">{{ _("Clear reference") }}</button>
      <div class="fd-ctrl fd-ref-note small-muted">{{ _("Manual side-by-side review only.") }}</div>
    {% endif %}
  </div>

  <div class="fd-review-layout{% if not (is_admin and fd_bounty_refs) %} no-ref{% endif %}">
    <div class="fd-stage-wrap">
      <div class="fd-stage">
        <video id="fdVideo" playsinline muted autoplay></video>
        <canvas id="fdCanvas"></canvas>
      </div>
    </div>

    {% if is_admin and fd_bounty_refs %}
    <aside class="fd-ref-panel">
      <div class="fd-ref-head">{{ _("Bounty reference") }}</div>
      <div class="fd-ref-box" id="fdRefBox">
        <img id="fdRefImg" alt="{{ _("Reference photo") }}" hidden>
        <div class="small-muted" id="fdRefEmpty">{{ _("Select a bounty profile photo to review beside the live camera. No automatic face matching is performed.") }}</div>
      </div>
    </aside>
    {% endif %}
  </div>
</div>

<style>
.fd-root{position:relative;}
.fd-top-info{display:inline-flex;flex-direction:column;gap:4px;background:rgba(12,12,12,.55);border:1px solid var(--border);border-radius:16px;padding:10px 14px;backdrop-filter:blur(8px)}
.fd-status-line{font-weight:800;letter-spacing:.04em;color:var(--accent)}
.fd-sub-line{font-size:.86rem;color:var(--text-muted)}
.fd-controls{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;align-items:stretch}
.fd-controls .fd-ctrl{display:flex;align-items:center;justify-content:center;min-height:46px;padding:.55rem .75rem;font-size:.95rem;text-align:center;line-height:1.2;white-space:normal}
.fd-select{appearance:auto;justify-content:flex-start!important}
.fd-ref-note{border:1px dashed var(--border);border-radius:14px;padding:.55rem .75rem;background:rgba(255,255,255,.02)}
.fd-review-layout{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(280px,.85fr);gap:14px;align-items:stretch}
.fd-review-layout.no-ref{grid-template-columns:minmax(0,1fr)}
.fd-stage-wrap{min-width:0}
.fd-stage{position:relative;width:100%;max-width:1200px;margin:0 auto;min-height:460px;aspect-ratio:16/10;overflow:hidden;border:1px solid var(--border);border-radius:18px;background:#000}
.fd-stage video,.fd-stage canvas{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;border-radius:18px}
.fd-stage video{z-index:1;background:#000;visibility:visible;transform:scaleX(-1)}
.fd-stage canvas{z-index:2;pointer-events:none;transform:scaleX(-1)}
.fd-ref-panel{display:flex;flex-direction:column;gap:10px;border:1px solid var(--border);border-radius:18px;padding:12px;background:rgba(255,255,255,.02);min-height:460px}
.fd-ref-head{font-weight:700;color:var(--accent)}
.fd-ref-box{position:relative;flex:1;min-height:380px;border:1px solid var(--border);border-radius:16px;overflow:hidden;background:#080808;display:flex;align-items:center;justify-content:center;padding:12px}
.fd-ref-box img{display:block;width:100%;height:100%;object-fit:contain;border-radius:12px;background:#000}
@media (min-width: 768px){
  .fd-controls .fd-ctrl{min-height:48px;font-size:1rem}
  .fd-stage{min-height:600px;aspect-ratio:16/10}
}
@media (max-width: 900px){
  .fd-review-layout{grid-template-columns:1fr}
  .fd-ref-panel{min-height:unset}
  .fd-ref-box{min-height:260px}
}
@media (max-width: 520px){
  .fd-controls .fd-ctrl{padding:.5rem .45rem;font-size:.86rem}
}
</style>

<script nonce="{{ csp_nonce }}" src="https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/face_mesh.js"></script>
<script nonce="{{ csp_nonce }}" src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js"></script>
<script nonce="{{ csp_nonce }}" src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js"></script>
<script nonce="{{ csp_nonce }}">
(function(){
  const I18N = {{ fd_i18n|tojson }};
  const videoEl = document.getElementById('fdVideo');
  const canvasEl = document.getElementById('fdCanvas');
  const ctx = canvasEl.getContext('2d');
  const uploadEl = document.getElementById('fdUpload');
  const btnStart = document.getElementById('fdStart');
  const btnSwitch = document.getElementById('fdSwitch');
  const btnSave = document.getElementById('fdSave');
  const btnBackLive = document.getElementById('fdBackLive');
  const statusEl = document.getElementById('fdStatus');
  const serverStatusEl = document.getElementById('fdServerStatus');
  const sourceStatusEl = document.getElementById('fdSourceStatus');
  const refSelect = document.getElementById('fdRefSelect');
  const refImg = document.getElementById('fdRefImg');
  const refEmpty = document.getElementById('fdRefEmpty');
  const btnClearRef = document.getElementById('fdClearRef');

  videoEl.muted = true;
  videoEl.setAttribute('muted', '');
  videoEl.setAttribute('playsinline', '');
  videoEl.setAttribute('webkit-playsinline', '');

  let currentFacing = 'user';
  let cameraActive = null;
  let stream = null;
  let sourceMode = 'camera';
  let uploadedImage = null;
  let uploadedVideo = null;
  let uploadLoop = null;
  let liveLoop = null;
  let processing = false;
  let lastSource = null;
  let currentFaceBoxes = [];
  let currentUploadName = '';

  function setStatus(msg){ statusEl.textContent = msg || ''; }
  function setServer(msg){ serverStatusEl.textContent = msg || ''; }
  function setSource(msg){ sourceStatusEl.textContent = msg || ''; }
  function sleep(ms){ return new Promise(r=>setTimeout(r, ms)); }
  function showReference(url){
    if(!refImg || !refEmpty) return;
    if(!url){
      refImg.hidden = true; refImg.removeAttribute('src');
      refEmpty.hidden = false;
      setStatus(I18N.referenceCleared || 'Reference photo cleared.');
      return;
    }
    refImg.onload = ()=>{ refImg.hidden = false; refEmpty.hidden = true; setStatus(I18N.referenceLoaded || 'Reference photo loaded.'); };
    refImg.onerror = ()=>{ refImg.hidden = true; refEmpty.hidden = false; setStatus('Could not load the selected reference photo.'); };
    refImg.src = url;
  }
  function updateSourceLabel(extra=''){
    let label = I18N.sourceLive || 'SOURCE: LIVE CAMERA';
    if(sourceMode === 'upload-image') label = I18N.sourcePhoto || 'SOURCE: UPLOADED PHOTO';
    else if(sourceMode === 'upload-video') label = I18N.sourceVideo || 'SOURCE: UPLOADED VIDEO';
    if(extra) label += ' | ' + extra;
    setSource(label);
  }
  function sizeCanvasFrom(source){
    const w = source.videoWidth || source.naturalWidth || source.width || 1280;
    const h = source.videoHeight || source.naturalHeight || source.height || 720;
    canvasEl.width = w; canvasEl.height = h;
  }
  function stopLive(){
    if(liveLoop){ cancelAnimationFrame(liveLoop); liveLoop = null; }
    try{ if(cameraActive && typeof cameraActive.stop === 'function'){ cameraActive.stop(); } }catch(e){}
    cameraActive = null;
    if(stream){ try{ stream.getTracks().forEach(t=>t.stop()); }catch(e){} }
    stream = null;
    if(videoEl.srcObject){ try{ videoEl.srcObject.getTracks().forEach(t=>t.stop()); }catch(e){} }
    videoEl.srcObject = null;
    try{ videoEl.pause(); }catch(e){}
  }
  function stopUploadMedia(){
    if(uploadLoop){ cancelAnimationFrame(uploadLoop); uploadLoop = null; }
    if(uploadedVideo){ try{ uploadedVideo.pause(); }catch(e){} if(uploadedVideo.src && uploadedVideo.src.startsWith('blob:')){ try{ URL.revokeObjectURL(uploadedVideo.src); }catch(e){} } }
    if(uploadedImage && uploadedImage.src && uploadedImage.src.startsWith('blob:')){ try{ URL.revokeObjectURL(uploadedImage.src); }catch(e){} }
    uploadedImage = null; uploadedVideo = null;
  }
  function calcDist(p1, p2) { return Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2)); }
  function calcAngle(p1, p2) { return Math.atan2(p2.y - p1.y, p2.x - p1.x) * 180 / Math.PI; }
  function getEmotion(landmarks, faceWidth, faceHeight) {
      const mouthOpen = calcDist(landmarks[13], landmarks[14]) / faceHeight;
      const mouthWidth = calcDist(landmarks[61], landmarks[291]) / faceWidth;
      const browInnerDist = calcDist(landmarks[55], landmarks[285]) / faceWidth;
      const eyeOpen = (calcDist(landmarks[159], landmarks[145]) + calcDist(landmarks[386], landmarks[374])) / (2 * faceHeight);
      if (mouthOpen > 0.08 && eyeOpen > 0.045) return (I18N.emotionSurprised || 'SURPRISED') + ' 😲';
      if (mouthWidth > 0.40 && mouthOpen > 0.02) return (I18N.emotionHappy || 'HAPPY') + ' 😊';
      if (browInnerDist < 0.22 && eyeOpen < 0.035) return (I18N.emotionAngry || 'ANGRY') + ' 😠';
      if (mouthWidth < 0.32 && mouthOpen < 0.02) return (I18N.emotionSad || 'SAD') + ' 😔';
      return (I18N.emotionNeutral || 'NEUTRAL') + ' 😐';
  }

  if (typeof FaceMesh === 'undefined') { setStatus('MediaPipe failed to load. Refresh the page and try again.'); return; }
  const faceMesh = new FaceMesh({ locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}` });
  faceMesh.setOptions({ maxNumFaces: 3, refineLandmarks: true, minDetectionConfidence: 0.6, minTrackingConfidence: 0.6 });
  faceMesh.onResults((results) => {
    const source = results.image; if(!source) return;
    lastSource = source; sizeCanvasFrom(source); currentFaceBoxes = [];
    ctx.save();
    ctx.clearRect(0,0,canvasEl.width,canvasEl.height);
    ctx.drawImage(source, 0, 0, canvasEl.width, canvasEl.height);
    const faces = results.multiFaceLandmarks || [];
    if (faces.length) {
      setServer((I18N.serverAnalyzing || 'SERVER: ANALYZING'));
      let faceCount = 0;
      for (const landmarks of faces) {
        faceCount++;
        const xs = landmarks.map(p => p.x), ys = landmarks.map(p => p.y);
        const minX = Math.max(0, Math.min(...xs) - 0.04), maxX = Math.min(1, Math.max(...xs) + 0.04);
        const minY = Math.max(0, Math.min(...ys) - 0.06), maxY = Math.min(1, Math.max(...ys) + 0.06);
        currentFaceBoxes.push({
          x: Math.round(minX * canvasEl.width), y: Math.round(minY * canvasEl.height),
          width: Math.round((maxX - minX) * canvasEl.width), height: Math.round((maxY - minY) * canvasEl.height)
        });

        if (typeof drawConnectors !== 'undefined' && typeof drawLandmarks !== 'undefined') {
          try{ drawConnectors(ctx, landmarks, FACEMESH_TESSELATION, {color: '#B57EDC44', lineWidth: 0.5}); }catch(e){}
          try{ drawConnectors(ctx, landmarks, FACEMESH_FACE_OVAL, {color: '#B57EDC', lineWidth: 1.5}); }catch(e){}
          try{ drawConnectors(ctx, landmarks, FACEMESH_RIGHT_EYEBROW, {color: '#B57EDC', lineWidth: 1.5}); }catch(e){}
          try{ drawConnectors(ctx, landmarks, FACEMESH_LEFT_EYEBROW, {color: '#B57EDC', lineWidth: 1.5}); }catch(e){}
          try{ drawConnectors(ctx, landmarks, FACEMESH_RIGHT_EYE, {color: '#B57EDC', lineWidth: 1.5}); }catch(e){}
          try{ drawConnectors(ctx, landmarks, FACEMESH_LEFT_EYE, {color: '#B57EDC', lineWidth: 1.5}); }catch(e){}
          try{ drawConnectors(ctx, landmarks, FACEMESH_LIPS, {color: '#B57EDC', lineWidth: 1.5}); }catch(e){}
          try{ drawConnectors(ctx, landmarks, FACEMESH_RIGHT_IRIS, {color: '#B57EDC', lineWidth: 2}); }catch(e){}
          try{ drawConnectors(ctx, landmarks, FACEMESH_LEFT_IRIS, {color: '#B57EDC', lineWidth: 2}); }catch(e){}
          try{ drawLandmarks(ctx, landmarks, {color: '#B57EDC', fillColor: '#FFF', lineWidth: 0.5, radius: 0.8}); }catch(e){}
        }

        const pTop = landmarks[10], pBottom = landmarks[152], pLeft = landmarks[234], pRight = landmarks[454];
        const faceHeight = calcDist(pTop, pBottom); const faceWidth = calcDist(pLeft, pRight);
        const roll = -calcAngle(landmarks[33], landmarks[263]);
        const noseOffsetX = ((landmarks[1].x - pLeft.x) / (pRight.x - pLeft.x)) - 0.5;
        const noseOffsetY = ((landmarks[1].y - pTop.y) / (pBottom.y - pTop.y)) - 0.5;
        const yaw = noseOffsetX * 100; const pitch = noseOffsetY * 100;
        const jawWidth = calcDist(landmarks[132], landmarks[361]) / faceWidth;
        const noseWidth = calcDist(landmarks[129], landmarks[358]) / faceWidth;
        let shapeStr = (faceHeight / faceWidth > 1.35) ? (I18N.long || 'LONG') : ((faceHeight / faceWidth < 1.25) ? (I18N.round || 'ROUND') : (I18N.oval || 'OVAL'));
        let jawStr = (jawWidth > 0.8) ? (I18N.broad || 'BROAD') : (I18N.narrow || 'NARROW');
        const leftEyeOpen = calcDist(landmarks[159], landmarks[145]) / faceHeight * 100;
        const rightEyeOpen = calcDist(landmarks[386], landmarks[374]) / faceHeight * 100;
        const eyeSpacing = calcDist(landmarks[159], landmarks[386]) / faceWidth;
        let eyeSetStr = (eyeSpacing > 0.44) ? (I18N.wide || 'WIDE') : ((eyeSpacing < 0.4) ? (I18N.close || 'CLOSE') : (I18N.avg || 'AVG'));
        let gaze = I18N.center || 'CENTER';
        if (landmarks[468]) {
            const irisL_offset = (landmarks[468].x - landmarks[33].x) / (landmarks[133].x - landmarks[33].x);
            if (irisL_offset < 0.4) gaze = I18N.right || 'RIGHT';
            else if (irisL_offset > 0.6) gaze = I18N.left || 'LEFT';
            else if (landmarks[468].y < landmarks[159].y + 0.01) gaze = I18N.up || 'UP';
        }
        const browL = calcDist(landmarks[52], landmarks[159]) / faceHeight;
        const browR = calcDist(landmarks[282], landmarks[386]) / faceHeight;
        const browLStr = browL > 0.12 ? (I18N.raise || 'RAISE') : (browL < 0.08 ? (I18N.furrow || 'FURROW') : (I18N.neut || 'NEUT'));
        const browRStr = browR > 0.12 ? (I18N.raise || 'RAISE') : (browR < 0.08 ? (I18N.furrow || 'FURROW') : (I18N.neut || 'NEUT'));
        const mouthOpen = calcDist(landmarks[13], landmarks[14]) / faceHeight * 100;
        const mouthW = calcDist(landmarks[61], landmarks[291]) / faceWidth * 100;
        const asymEye = Math.abs(leftEyeOpen - rightEyeOpen);
        const asymBrow = Math.abs(browL - browR) * 100;
        const totalAsym = (asymEye + asymBrow).toFixed(2);
        const emotion = getEmotion(landmarks, faceWidth, faceHeight);

        ctx.scale(-1, 1); ctx.translate(-canvasEl.width, 0);
        const faceLeftPx = (1 - pLeft.x) * canvasEl.width;
        const faceRightPx = (1 - pRight.x) * canvasEl.width;
        const faceTopPx = pTop.y * canvasEl.height;
        const lines = [
            `[ ${I18N.faceId || 'ID'}: ${faceCount} | ${emotion} ]`,
            `${I18N.pose || 'POSE'}  | Yaw:${yaw.toFixed(1)}° Pch:${pitch.toFixed(1)}° Rol:${roll.toFixed(1)}°`,
            `${I18N.shape || 'SHAPE'} | Face:${shapeStr} Jaw:${jawStr} NoseW:${(noseWidth*100).toFixed(1)}%`,
            `${I18N.eyes || 'EYES'}  | ${eyeSetStr} Set | Gaze: ${gaze}`,
            `      | Opn L:${leftEyeOpen.toFixed(2)} R:${rightEyeOpen.toFixed(2)}`,
            `${I18N.brows || 'BROWS'} | L:${browLStr} R:${browRStr}`,
            `${I18N.mouth || 'MOUTH'} | Wdh:${mouthW.toFixed(1)}% Opn:${mouthOpen.toFixed(2)}%`,
            `${I18N.asym || 'ASYM'}  | Score: ${totalAsym}%`
        ];
        ctx.font = 'bold 11px monospace'; ctx.strokeStyle='black'; ctx.lineWidth=2.5; ctx.lineJoin='round';
        const blockWidth = 210, blockHeight = lines.length * 16;
        let textX = faceLeftPx + 15; if (textX + blockWidth > canvasEl.width) textX = faceRightPx - blockWidth - 15;
        textX = Math.max(10, Math.min(textX, canvasEl.width - blockWidth - 10));
        let startY = faceTopPx - blockHeight - 10; if (startY < 15) startY = faceTopPx + (faceHeight * canvasEl.height) + 20;
        startY = Math.max(15, Math.min(startY, canvasEl.height - blockHeight - 10));
        lines.forEach((line, idx) => {
          const y = startY + (idx * 16);
          ctx.strokeText(line, textX, y);
          if (idx === 0) ctx.fillStyle = '#00FFCC';
          else if (line.includes(I18N.asym || 'ASYM') && Number(totalAsym) > 5) ctx.fillStyle = '#FF4444';
          else ctx.fillStyle = 'white';
          ctx.fillText(line, textX, y);
        });
        ctx.translate(canvasEl.width, 0); ctx.scale(-1, 1);
      }
      const sourceTag = (sourceMode === 'camera') ? (I18N.live || 'LIVE') : (I18N.upload || 'UPLOAD');
      setStatus(`${I18N.analyzing || 'ANALYZING'} ${sourceTag} ${faceCount} FACE(S)`);
    } else {
      const sourceTag = (sourceMode === 'camera') ? (I18N.live || 'LIVE') : (I18N.upload || 'UPLOAD');
      setStatus(`${sourceTag} ${I18N.ready || 'READY'} | ${I18N.noFaceDetected || 'No face detected.'}`);
      setServer(I18N.serverStandby || 'SERVER: STANDBY');
    }
    ctx.restore();
  });

  async function acquireCameraStream(){
    const seq = [
      { video: { facingMode: { exact: currentFacing } }, audio: false },
      { video: { facingMode: { ideal: currentFacing }, width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false },
      { video: { width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false },
      { video: true, audio: false }
    ];
    let lastErr = null;
    for (const constraints of seq){
      try { return await navigator.mediaDevices.getUserMedia(constraints); }
      catch(err){ lastErr = err; }
    }
    throw lastErr || new Error('camera_failed');
  }

  async function waitForVideo(){
    if(videoEl.readyState >= 2 && videoEl.videoWidth > 0) return;
    await new Promise((resolve, reject) => {
      let done = false;
      const ok = () => { if(done) return; done = true; cleanup(); resolve(); };
      const bad = () => { if(done) return; done = true; cleanup(); reject(new Error('video_not_ready')); };
      const cleanup = () => { videoEl.removeEventListener('loadedmetadata', ok); videoEl.removeEventListener('canplay', ok); clearTimeout(timer); };
      videoEl.addEventListener('loadedmetadata', ok, {once:true});
      videoEl.addEventListener('canplay', ok, {once:true});
      const timer = setTimeout(bad, 6000);
    });
  }

  async function startCamera(){
    stopUploadMedia();
    stopLive();
    sourceMode = 'camera';
    updateSourceLabel(currentFacing === 'environment' ? 'BACK CAMERA' : 'FRONT CAMERA');
    setStatus(I18N.startingCamera || 'Starting camera...');
    try{
      if(!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia){ throw new Error('media_unsupported'); }
      await sleep(220);
      stream = await acquireCameraStream();
      videoEl.srcObject = stream;
      videoEl.style.visibility = 'visible';
      try{ await videoEl.play(); }catch(e){}
      await waitForVideo();
      sizeCanvasFrom(videoEl);

      if(typeof Camera !== 'undefined'){
        cameraActive = new Camera(videoEl, {
          onFrame: async () => {
            if(sourceMode !== 'camera' || processing) return;
            processing = true;
            try{ await faceMesh.send({ image: videoEl }); }catch(err){ console.error(err); }
            processing = false;
          },
          width: videoEl.videoWidth || 1280,
          height: videoEl.videoHeight || 720
        });
        await cameraActive.start();
      }else{
        const loop = async () => {
          if(sourceMode !== 'camera') return;
          if(videoEl.readyState >= 2 && !processing){
            processing = true;
            try{ await faceMesh.send({ image: videoEl }); }catch(e){ console.error(e); }
            processing = false;
          }
          liveLoop = requestAnimationFrame(loop);
        };
        liveLoop = requestAnimationFrame(loop);
      }
      setStatus(I18N.liveCamera || 'Live camera ready.');
    }catch(err){
      console.error(err);
      const msg = `${I18N.cameraError || 'Failed to acquire camera feed.'} ${err && err.name ? err.name + ': ' : ''}${err && err.message ? err.message : ''}`.trim();
      setStatus(msg);
      try{ alert(msg); }catch(e){}
    }
  }

  async function backToLiveCamera(){ currentFacing = 'user'; await startCamera(); }

  async function handleUpload(file){
    if(!file) return;
    currentUploadName = file.name || 'uploaded_media';
    stopLive(); stopUploadMedia();
    if(file.type.startsWith('image/')){
      sourceMode = 'upload-image'; updateSourceLabel(currentUploadName);
      const url = URL.createObjectURL(file); const img = new Image();
      img.onload = async () => { uploadedImage = img; setStatus(I18N.analyzingUpload || 'Analyzing uploaded media...'); try{ await faceMesh.send({ image: img }); }catch(err){ console.error(err); setStatus(I18N.uploadFailed || 'Upload analysis failed.'); } };
      img.src = url; return;
    }
    if(file.type.startsWith('video/')){
      sourceMode = 'upload-video'; updateSourceLabel(currentUploadName);
      const url = URL.createObjectURL(file); const v = document.createElement('video');
      v.src = url; v.playsInline = true; v.muted = true; v.loop = true; v.autoplay = true;
      v.onloadeddata = async () => {
        uploadedVideo = v;
        try{
          await uploadedVideo.play(); setStatus(I18N.analyzingUpload || 'Analyzing uploaded media...');
          const loop = async () => {
            if(sourceMode !== 'upload-video' || !uploadedVideo) return;
            if(uploadedVideo.readyState >= 2 && !uploadedVideo.paused && !uploadedVideo.ended && !processing){
              processing = true; try{ await faceMesh.send({ image: uploadedVideo }); }catch(e){} processing = false;
            }
            uploadLoop = requestAnimationFrame(loop);
          };
          uploadLoop = requestAnimationFrame(loop);
        }catch(err){ console.error(err); setStatus(I18N.videoPlaybackBlocked || 'Video playback blocked.'); }
      };
      try{ v.load(); }catch(e){}
      return;
    }
    setStatus(I18N.unsupportedFile || 'Please choose a photo or video file.');
  }

  async function saveResult(){
    if(!canvasEl.width || !canvasEl.height){ setStatus(I18N.nothingToSave || 'Nothing to save yet.'); return; }
    setStatus(I18N.serverUploading || 'SERVER: UPLOADING...');
    try{
      const filename = `FaceDetector_Result_${Date.now()}.png`;
      const dataUrl = canvasEl.toDataURL('image/png');
      const resp = await fetch("{{ url_for('face_detector_save') }}", { method:'POST', headers:{ 'Content-Type':'application/json', 'X-CSRF-Token': {{ csrf_token|tojson }} }, body: JSON.stringify({ filename, filedata: dataUrl }) });
      const data = await resp.json(); if(!resp.ok || !data.ok) throw new Error(data.error || 'save_failed');
      setServer(I18N.serverSaved || 'SERVER: SAVED');
      setStatus((I18N.savedTo || 'Saved to') + ': ' + (data.path || filename));
      setTimeout(()=>setServer(I18N.serverStandby || 'SERVER: STANDBY'), 2500);
    }catch(err){ console.error(err); setServer(I18N.serverDisconnected || 'SERVER: DISCONNECTED'); setStatus(I18N.saveFailed || 'Could not save the result.'); }
  }

  btnStart.addEventListener('click', ()=>{ startCamera(); });
  btnSwitch.addEventListener('click', async ()=>{ if(sourceMode !== 'camera'){ await backToLiveCamera(); return; } currentFacing = (currentFacing === 'user') ? 'environment' : 'user'; await startCamera(); });
  btnSave.addEventListener('click', saveResult);
  btnBackLive.addEventListener('click', backToLiveCamera);
  uploadEl.addEventListener('change', (ev)=>{ const f = ev.target.files && ev.target.files[0]; handleUpload(f); ev.target.value=''; });
  if(refSelect){ refSelect.addEventListener('change', ()=>{ showReference(refSelect.value || ''); }); }
  if(btnClearRef){ btnClearRef.addEventListener('click', ()=>{ if(refSelect) refSelect.value=''; showReference(''); }); }
})();
</script>
{% endblock %}
"""

app.jinja_loader = DictLoader(TEMPLATES)

@app.context_processor
def inject_ctx():
    """inject_ctx.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    def child_path(rel, name):
        """child_path.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    rel: Parameter.
    name: Parameter.

Returns:
    Varies.
"""
        rel = (rel or "").strip("/")
        return f"{rel}/{name}" if rel else name
    u = current_user()
    prefs = get_user_prefs(u) if u else dict(DEFAULT_PREFS)
    but_css = BUT_CSS + prefs_css(prefs)
    try:
        story_users = _story_active_usernames() if u else set()
    except Exception:
        story_users = set()
    def has_active_story(username):
        try:
            return bool(username and (username in story_users))
        except Exception:
            return False
    return dict(
        but_css=but_css,
        user=u,
        user_prefs=prefs,
        my_profile=getattr(g, "my_profile", None),
        child_path=child_path,
        request=request,
        is_admin=user_is_admin(current_user()),
        has_active_story=has_active_story,
        story_active_users=story_users,
        log_path=LOG_PATH,
        app_data_dir=BASE_DIR,
        watermark=WATERMARK,
        notifications=getattr(g, "notifs", None),
    )

@app.before_request
def _attach_profile_and_presence():
    # Presence is scoped by the host used to reach the app (local vs cloudflared vs tor).
    """_attach_profile_and_presence.

Internal helper function.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    # Presence is scoped by the host used to reach the app (local vs cloudflared vs tor).
    g.scope = current_scope()
    u = current_user()
    if u:
        g.my_profile = type("Obj", (), get_profile(u))()
        mark_online(u, g.scope)

        # Notifications (numbered indicators)
        dm_total, dm_by = dm_unread_counts(u)
        g.notifs = type("Obj", (), {
            "dm_total": dm_total,
            "dm_by_sender": dm_by,
        })()
    else:
        g.my_profile = None
        g.notifs = type("Obj", (), {
            "dm_total": 0,
            "dm_by_sender": {},
        })()

# ---------------------------
# Auth / abuse rate limiting
# ---------------------------

_login_fail = {}
_login_lock = threading.Lock()
_action_hits = {}
_action_lock = threading.Lock()

def _rl_key(bucket: str, ident: str) -> str:
    return f"{bucket}:{ident or '?'}"

def _rate_limit_hit(bucket: str, ident: str, limit: int, window_sec: int) -> bool:
    """Sliding-window rate limiter stored in memory for this process.

Used for abusive login / signup / recovery / admin bursts.
"""
    now = time.time()
    key = _rl_key(bucket, ident)
    with _action_lock:
        hits = [t for t in _action_hits.get(key, []) if (now - t) <= window_sec]
        if len(hits) >= limit:
            _action_hits[key] = hits
            return True
        hits.append(now)
        _action_hits[key] = hits
        return False

def _too_many_attempts(ip: str, username: str = "") -> bool:
    """Return True when login/2FA attempts should be temporarily blocked."""
    user = (username or "").strip().lower()
    with _login_lock:
        now = time.time()
        checks = [ip]
        if user:
            checks.extend([f"user:{user}", f"combo:{ip}|{user}"])
        for key in checks:
            rec = _login_fail.get(key, {"n": 0, "t": now})
            if now - rec["t"] > 10 * 60:
                _login_fail[key] = {"n": 0, "t": now}
                continue
            if rec["n"] >= 10:
                return True
        return False

def _mark_fail(ip: str, username: str = ""):
    """Record a failed login/2FA attempt by IP and, when known, by username."""
    user = (username or "").strip().lower()
    with _login_lock:
        now = time.time()
        keys = [ip]
        if user:
            keys.extend([f"user:{user}", f"combo:{ip}|{user}"])
        for key in keys:
            rec = _login_fail.get(key, {"n": 0, "t": now})
            if now - rec["t"] > 10 * 60:
                rec = {"n": 0, "t": now}
            rec["n"] += 1
            _login_fail[key] = rec

def _clear_fail(ip: str, username: str = ""):
    user = (username or "").strip().lower()
    with _login_lock:
        for key in [ip, f"user:{user}" if user else "", f"combo:{ip}|{user}" if user else ""]:
            if key:
                _login_fail.pop(key, None)

def _password_strength_error(password: str, username: str = "") -> Optional[str]:
    pw = str(password or "")
    if len(pw) < 10:
        return "Password must be at least 10 characters."
    if len(pw) > 256:
        return "Password is too long."
    low = pw.lower()
    u = (username or "").strip().lower()
    if u and u in low:
        return "Password must not contain your username."
    score = 0
    score += bool(re.search(r"[a-z]", pw))
    score += bool(re.search(r"[A-Z]", pw))
    score += bool(re.search(r"\d", pw))
    score += bool(re.search(r"[^A-Za-z0-9]", pw))
    if score < 3:
        return "Password must include at least 3 of these: lowercase, uppercase, number, symbol."
    common = {"password", "123456", "12345678", "qwerty", "letmein", "admin", "dedsec", "welcome"}
    if any(c in low for c in common):
        return "Password is too easy to guess."
    return None

def _host_is_allowed(hostname: str) -> bool:
    host = (hostname or "").strip().lower()
    if not host:
        return False
    if host in {"localhost", "127.0.0.1", "::1"}:
        return True
    if host.endswith(".trycloudflare.com") or host.endswith(".onion"):
        return True
    try:
        ip_obj = ipaddress.ip_address(host)
        return bool(ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local)
    except Exception:
        pass
    # Allow normal domain names used by reverse proxies / custom domains.
    if re.fullmatch(r"[a-z0-9.-]{1,253}", host) and "." in host:
        return True
    return False

# ---------------------------
# Routes: auth/home
# ---------------------------

@app.route("/landing")
def landing():
    return index()

@app.route("/")
def index():
    """index.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    if is_logged_in():
        return redirect(url_for("profiler"))
    return render_template("landing.html", title="ButSystem")

@app.route("/home")
@login_required
def home():
    """Deprecated landing/dashboard page.

    The prior dashboard page shown after login was removed per request.
    We keep the route to avoid breaking old bookmarks, but redirect users
    to Profiler (the new landing page).
    """
    return redirect(url_for("profiler"))

@app.route("/loading")
@login_required
def loading():
    """Small loading screen shown right after login.

    This prevents the user from briefly seeing intermediate pages while the
    session, profile row, and other bootstrap data is prepared.
    """
    me = current_user()
    try:
        prof = get_profile(me)
        display_name = (prof.get("nickname") or "").strip() or me
    except Exception:
        display_name = me

    return render_template("loading.html", title="Loading", display_name=display_name)

@app.route("/api/bootstrap")
@login_required
def api_bootstrap():
    """Lightweight bootstrap endpoint used by the loading screen."""
    me = current_user()
    try:
        prof = get_profile(me)
    except Exception:
        prof = {"nickname": me, "bio": "", "links": []}
    return jsonify({"ok": True, "me": me, "profile": {"nickname": prof.get("nickname") or me}})
# ---------------------------
# World News (RSS aggregation; cached)
# ---------------------------

# Cache is per-language (English/Greek), refreshed every _NEWS_TTL seconds.
_NEWS_CACHE = {"ts": {"en": 0.0, "el": 0.0}, "items": {"en": [], "el": []}}  # in-memory cache
_NEWS_LOCK = threading.Lock()
_NEWS_TTL = 20 * 60  # seconds

# Topics the user asked for (plus similar). We use Google News RSS search to get "worldwide" coverage.
NEWS_TOPICS = [
    ("cybersecurity", {"en": "Cybersecurity", "el": "Κυβερνοασφάλεια"},
     {"en": "cybersecurity OR infosec OR \"data breach\"", "el": "κυβερνοασφάλεια OR ασφάλεια πληροφοριών OR \"διαρροή δεδομένων\""}),

    ("hacking", {"en": "Hacking", "el": "Χάκινγκ"},
     {"en": "hacking OR hacker OR \"zero day\"", "el": "χάκινγκ OR χάκερ OR \"μηδενικής ημέρας\""}),

    ("termux", {"en": "Termux", "el": "Termux"},
     {"en": "Termux", "el": "Termux"}),

    ("dedsec", {"en": "DedSec Project", "el": "DedSec Project"},
     {"en": "\"DedSec\" OR \"DedSec Project\"", "el": "\"DedSec\" OR \"DedSec Project\""}),

    ("internet", {"en": "Internet", "el": "Ίντερνετ"},
     {"en": "internet (privacy OR security OR scam)", "el": "διαδίκτυο (ιδιωτικότητα OR ασφάλεια OR απάτη)"}),

    ("crypto", {"en": "Crypto", "el": "Κρύπτο"},
     {"en": "cryptocurrency OR crypto OR bitcoin OR ethereum", "el": "κρυπτονόμισμα OR crypto OR bitcoin OR ethereum"}),

    # Extra categories (10+)
    ("privacy", {"en": "Privacy", "el": "Ιδιωτικότητα"},
     {"en": "privacy OR tracking OR surveillance OR \"data protection\"", "el": "ιδιωτικότητα OR παρακολούθηση OR επιτήρηση OR \"προστασία δεδομένων\""}),

    ("ransomware", {"en": "Ransomware", "el": "Ransomware"},
     {"en": "ransomware OR cyber extortion", "el": "ransomware OR \"εκβιαστικό λογισμικό\" OR εκβιασμός"}),

    ("malware", {"en": "Malware", "el": "Κακόβουλο λογισμικό"},
     {"en": "malware OR trojan OR botnet OR spyware", "el": "κακόβουλο λογισμικό OR trojan OR botnet OR spyware"}),

    ("vulnerabilities", {"en": "Vulnerabilities", "el": "Ευπάθειες"},
     {"en": "CVE OR vulnerability OR security patch", "el": "CVE OR ευπάθεια OR \"ενημέρωση ασφαλείας\""}),

    ("phishing", {"en": "Phishing & Scams", "el": "Phishing & Απάτες"},
     {"en": "phishing OR scam OR social engineering", "el": "phishing OR απάτη OR \"κοινωνική μηχανική\""}),

    ("mobile", {"en": "Mobile Security", "el": "Ασφάλεια Κινητών"},
     {"en": "Android security OR iOS security OR mobile malware", "el": "ασφάλεια Android OR ασφάλεια iOS OR κακόβουλο λογισμικό κινητών"}),

    ("ai_security", {"en": "AI Security", "el": "Ασφάλεια AI"},
     {"en": "AI security OR LLM security OR prompt injection OR jailbreak", "el": "ασφάλεια AI OR \"ασφάλεια τεχνητής νοημοσύνης\" OR LLM OR \"prompt injection\" OR jailbreak"}),

    ("devsecops", {"en": "DevSecOps", "el": "DevSecOps"},
     {"en": "DevSecOps OR supply chain security OR CI/CD security", "el": "DevSecOps OR \"ασφάλεια εφοδιαστικής αλυσίδας\" OR ασφάλεια CI/CD"}),

    ("osint", {"en": "OSINT", "el": "OSINT"},
     {"en": "OSINT OR \"open source intelligence\"", "el": "OSINT OR \"πληροφορίες ανοιχτών πηγών\""}),

    ("darkweb", {"en": "Dark Web", "el": "Dark Web"},
     {"en": "dark web OR darknet OR onion", "el": "dark web OR darknet OR onion"}),
]


def _google_news_rss(query: str, lang: str) -> str:
    """Build a Google News RSS search URL for the requested UI language."""
    lang = "el" if lang == "el" else "en"
    if lang == "el":
        hl, gl, ceid = "el", "GR", "GR:el"
    else:
        hl, gl, ceid = "en-US", "US", "US:en"
    q = urllib.parse.quote_plus(query)
    return f"https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"

def _news_feeds_for_lang(lang: str) -> List[Tuple[str, str, str, str, bool]]:
    """Return a list of feeds: (source_label, url, topic_key, topic_label, is_google)."""
    lang = "el" if lang == "el" else "en"
    feeds: List[Tuple[str, str, str, str, bool]] = []

    # Direct feeds for English (fast + high quality).
    if lang == "en":
        feeds.extend([
            ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews?format=xml", "cybersecurity", "Cybersecurity", False),
            ("BleepingComputer", "https://www.bleepingcomputer.com/feed/", "cybersecurity", "Cybersecurity", False),
            ("KrebsOnSecurity", "https://krebsonsecurity.com/feed/", "cybersecurity", "Cybersecurity", False),
            ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml", "crypto", "Crypto", False),
        ])

    # Google News RSS searches for worldwide coverage + the specific topics.
    for key, labels, queries in NEWS_TOPICS:
        topic_label = labels.get(lang, labels["en"])
        q = queries.get(lang, queries["en"])
        feeds.append(("Google News", _google_news_rss(q, lang), key, topic_label, True))

    return feeds

def _norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def _parse_rss_items(xml_bytes: bytes, source: str, topic_key: str, topic_label: str, is_google: bool) -> List[Dict[str, str]]:
    """Parse RSS/Atom bytes into a list of items: {title,url,source,topic_key,topic,published}."""
    out: List[Dict[str, str]] = []
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_bytes)
    except Exception:
        return out

    def txt(el):
        if el is None:
            return ""
        return _norm_space("".join(el.itertext()))

    def norm_title(t: str) -> Tuple[str, str]:
        """For Google News RSS, try to split 'Title - Publisher'."""
        if not is_google:
            return t, source
        t = (t or "").strip()
        if " - " in t:
            a, b = t.rsplit(" - ", 1)
            if a.strip() and b.strip():
                return a.strip(), b.strip()
        return t, source

    def push_item(title: str, link: str, pub: str):
        if not link:
            return
        t, s = norm_title(title or "Untitled")
        out.append({
            "title": t or "Untitled",
            "url": link,
            "source": s or source,
            "topic_key": topic_key,
            "topic": topic_label,
            "published": pub or "",
        })

    # RSS 2.0
    try:
        channel = root.find("channel")
        if channel is not None:
            for item in channel.findall("item")[:35]:
                title = txt(item.find("title")) or "Untitled"
                link = txt(item.find("link"))
                pub = txt(item.find("pubDate")) or txt(item.find("date"))
                push_item(title, link, pub)
            if out:
                return out
    except Exception:
        pass

    # Atom
    try:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("a:entry", ns)[:35]:
            title = txt(entry.find("a:title", ns)) or "Untitled"
            link_el = entry.find("a:link", ns)
            link = ""
            if link_el is not None:
                link = link_el.get("href") or ""
            pub = txt(entry.find("a:updated", ns)) or txt(entry.find("a:published", ns))
            push_item(title, link, pub)
    except Exception:
        pass

    return out

def _fetch_url(url: str, timeout: int = 7) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ButSystem/1.1 (+RSS)",
            "Accept": "application/xml,text/xml,application/rss+xml,application/atom+xml,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def _fetch_news_uncached(lang: str) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    for source, url, tkey, tlabel, is_google in _news_feeds_for_lang(lang):
        try:
            xmlb = _fetch_url(url, timeout=7)
            items.extend(_parse_rss_items(xmlb, source, tkey, tlabel, is_google))
        except Exception:
            continue

    # Sort by published date (best effort). If parsing fails, keep feed order.
    def parse_dt(p: str) -> float:
        p = (p or "").strip()
        if not p:
            return 0.0
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(p)
            return dt.timestamp()
        except Exception:
            pass
        try:
            dt = datetime.fromisoformat(p.replace("Z", "+00:00"))
            return dt.timestamp()
        except Exception:
            return 0.0

    items.sort(key=lambda it: parse_dt(it.get("published") or ""), reverse=True)

    # Deduplicate by URL (keep the first occurrence)
    seen = set()
    uniq = []
    for it in items:
        u = (it.get("url") or "").strip()
        if not u or u in seen:
            continue
        seen.add(u)
        uniq.append(it)
    return uniq[:60]

def get_news_items(lang: str, force: bool = False) -> List[Dict[str, str]]:
    """Return cached news items (per-language)."""
    lang = "el" if lang == "el" else "en"
    now = time.time()
    with _NEWS_LOCK:
        ts = float(_NEWS_CACHE["ts"].get(lang, 0.0) or 0.0)
        cached = list(_NEWS_CACHE["items"].get(lang, []) or [])
        if cached and not force and (now - ts) < _NEWS_TTL:
            return cached

    # Refresh outside lock (avoid blocking other requests)
    try:
        fresh = _fetch_news_uncached(lang)
    except Exception:
        fresh = []

    with _NEWS_LOCK:
        _NEWS_CACHE["ts"][lang] = time.time()
        _NEWS_CACHE["items"][lang] = fresh

    return list(fresh)

@app.route("/news")
@login_required
def news():
    """News page: worldwide headlines by topic, in EN/EL based on the UI language."""
    lang = get_lang()
    # UI topics list with labels in the current language
    topics = [{"key": "all", "label": ("All" if lang == "en" else "Όλα")}]
    for key, labels, _q in NEWS_TOPICS:
        topics.append({"key": key, "label": labels.get(lang, labels["en"])})
    return render_template("news.html", title=_("News"), topics=topics)

@app.route("/api/news")
@login_required
def api_news():
    """Return worldwide headlines (RSS aggregated) in the current language."""
    lang = (request.args.get("lang") or get_lang() or "en").strip().lower()
    if lang not in ("en", "el"):
        lang = get_lang()
    force = (request.args.get("force") == "1")
    items = []
    try:
        items = get_news_items(lang, force=force)
    except Exception:
        items = []
    return jsonify({"ok": True, "lang": lang, "items": items})


@app.route("/login", methods=["GET", "POST"])
def login():
    """login.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    if request.method == "POST":
        ip = _client_ip() or "?"
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if _too_many_attempts(ip, username):
            log_security_event("login_rate_limited", detail=f"user={username or '-'} ip={ip}", level="warning")
            flash("Too many attempts. Try again later.")
            return render_template("login.html", title=_("Login"))
        if _rate_limit_hit("login_post", ip, limit=20, window_sec=300):
            flash("Too many attempts. Try again later.")
            return render_template("login.html", title=_("Login"))

        conn = db_connect()
        row = conn.execute("SELECT pw_hash, is_admin, admin_device_id FROM users WHERE username=?", (username,)).fetchone()
        conn.close()
        if row and check_password_hash(row["pw_hash"], password):
            # Block admin login from any non-local link/device to prevent remote takeovers.
            try:
                is_admin = bool(int(row["is_admin"]) == 1)
            except Exception:
                is_admin = False
            if is_admin:
                bound = (row["admin_device_id"] or "").strip()
                if bound and bound != DEVICE_ID:
                    _mark_fail(ip, username)
                    flash("This admin profile is bound to a different device.")
                    return render_template("login.html", title=_("Login"))
            # Session capacity (per link/session scope): max 66 users + 1 admin.
            try:
                sc = current_scope()
                if not scope_capacity_ok(username, is_admin, sc):
                    flash("This session is full (max 66 users + 1 admin). Try again later.")
                    return render_template("login.html", title=_("Login"))
            except Exception:
                pass



            # If security-question 2FA is enabled, require the extra step.
            if user_2fa_enabled(username):
                session.pop("u", None)
                session["pre_2fa"] = username
                session.permanent = True
                return redirect(url_for("two_factor"))

            _clear_fail(ip, username)
            return _complete_login_session(username, is_admin)
        _mark_fail(ip, username)
        flash("Invalid credentials.")
    return render_template("login.html", title=_("Login"))

@app.route("/logout")
@login_required
def logout():
    """logout.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    session.pop("u", None)
    session.pop("login_at", None)
    flash("Logged out.")
    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    """signup.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    if request.method == "POST":
        ip = _client_ip() or "?"
        if _rate_limit_hit("signup_post", ip, limit=8, window_sec=3600):
            flash("Too many signup attempts. Try again later.")
            return render_template("signup.html", title="Request Access")

        u1 = (request.form.get("u1") or "").strip()
        u2 = (request.form.get("u2") or "").strip()
        p1 = request.form.get("p1") or ""
        p2 = request.form.get("p2") or ""

        if not u1 or not p1:
            flash("Username and password are required.")
            return render_template("signup.html", title="Request Access")
        if u1 != u2:
            flash("Usernames do not match.")
            return render_template("signup.html", title="Request Access")
        if p1 != p2:
            flash("Passwords do not match.")
            return render_template("signup.html", title="Request Access")
        pw_err = _password_strength_error(p1, u1)
        if pw_err:
            flash(pw_err)
            return render_template("signup.html", title="Request Access")
        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,32}", u1):
            flash("Username must be 3-32 chars: letters, numbers, _ . -")
            return render_template("signup.html", title="Request Access")

        ip = _client_ip() or "?"
        pw_hash = generate_password_hash(p1)

        conn = db_connect()
        exists = conn.execute("SELECT 1 FROM users WHERE username=?", (u1,)).fetchone()
        if exists:
            conn.close()
            flash("That username already exists. Please login.")
            return redirect(url_for("login"))

        pend = conn.execute("SELECT status FROM pending_users WHERE username=?", (u1,)).fetchone()
        if pend:
            conn.close()
            if pend["status"] == "pending":
                flash("Your request is already pending approval.")
            elif pend["status"] == "denied":
                flash("Your request was denied.")
            else:
                flash("Your request was approved. You can login now.")
            return redirect(url_for("login"))

        conn.execute(
            "INSERT INTO pending_users(username, pw_hash, requested_ip, requested_at, status) VALUES(?,?,?,?, 'pending')",
            (u1, pw_hash, ip, now_z())
        )
        conn.commit()
        conn.close()

        try:
            PENDING_QUEUE.put_nowait(u1)
        except Exception:
            pass

        flash("Request sent. Wait for admin approval.")
        return redirect(url_for("login"))

    return render_template("signup.html", title="Request Access")

# ---------------------------
# Device auto-login approval flow
# ---------------------------

@app.route("/device_access", methods=["GET", "POST"])
def device_access():
    """Request admin approval to trust this device for auto-login.
    Works only for accounts without 2FA enabled.
    """
    # If already logged in, nothing to do.
    if is_logged_in():
        return redirect(url_for("index"))
    admins = _admins_list()
    status = None

    fp = (request.cookies.get(DEVICE_FP_COOKIE) or "").strip()

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        if not username:
            flash(_("Username is required."))
            resp = redirect(url_for("device_access"))
            _ensure_device_fp_cookie(resp)
            return resp

        # 2FA users must use normal login.
        if user_2fa_enabled(username):
            flash(_("Auto‑login is disabled because 2FA is enabled on this account. Please sign in normally."))
            resp = redirect(url_for("login"))
            _ensure_device_fp_cookie(resp)
            return resp

        # Ensure device fp exists.
        resp = redirect(url_for("device_access"))
        if not fp:
            fp = secrets.token_urlsafe(24)
            resp.set_cookie(DEVICE_FP_COOKIE, fp, max_age=180*24*3600, httponly=True, samesite="Lax", secure=False)

        # If this device is already trusted for that user, do nothing.
        try:
            conn = db_connect()
            row = conn.execute("SELECT 1 FROM trusted_devices WHERE username=? AND device_fp=? AND status='approved' LIMIT 1", (username, fp)).fetchone()
            conn.close()
            if row:
                flash(_("This device is already approved for auto‑login."))
                return resp
        except Exception:
            pass

        ip = _client_ip() or "?"
        ua = (request.headers.get("User-Agent") or "")[:500]
        try:
            conn = db_connect()
            # avoid duplicates: keep most recent request
            conn.execute(
                "INSERT INTO device_access_requests(username, device_fp, requested_ip, user_agent, requested_at, status) VALUES(?,?,?,?,?, 'pending')",
                (username, fp, ip, ua, now_z())
            )
            conn.commit()
            conn.close()
            flash(_("Request sent to admin."))
        except Exception:
            flash(_("Request failed. Please try again."))

        return resp

    # GET: show latest status for this device fp (if any)
    try:
        if fp:
            conn = db_connect()
            row = conn.execute(
                "SELECT status FROM device_access_requests WHERE device_fp=? ORDER BY id DESC LIMIT 1",
                (fp,)
            ).fetchone()
            conn.close()
            if row:
                status = row["status"]
    except Exception:
        status = None

    resp = render_template("device_access.html", title=_("Device auto‑login"), admins=admins, status=status)
    return resp

@app.route("/device_access/poll")
def device_access_poll():
    """Client polls this endpoint for approval.
    When approved, it issues a trusted device token cookie and logs the user in (if 2FA is not enabled).
    """
    if is_logged_in():
        return jsonify({"ok": True, "status": "approved", "logged_in": True})
    fp = (request.cookies.get(DEVICE_FP_COOKIE) or "").strip()
    if not fp:
        return jsonify({"ok": True, "status": "none", "logged_in": False})

    conn = db_connect()
    row = conn.execute(
        "SELECT id, username, status, approved_by FROM device_access_requests WHERE device_fp=? ORDER BY id DESC LIMIT 1",
        (fp,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"ok": True, "status": "none", "logged_in": False})

    status = row["status"]
    if status != "approved":
        return jsonify({"ok": True, "status": status, "logged_in": False})

    username = row["username"]
    # If 2FA enabled, do not auto-login.
    if user_2fa_enabled(username):
        return jsonify({"ok": True, "status": "approved", "logged_in": False, "needs_login": True})

    # issue token and login
    try:
        token = _issue_trusted_device(username, fp, approved_by=(row["approved_by"] or None))
        session["u"] = username
        session.permanent = True
        session["login_at"] = now_z()
        ensure_profile_row(username)
        resp = jsonify({"ok": True, "status": "approved", "logged_in": True})
        _set_device_token_cookie(resp, token)
        return resp
    except Exception:
        return jsonify({"ok": False, "status": "error", "logged_in": False}), 500


# ---------------------------
# User profile (encrypted)
# ---------------------------

@app.route("/profile")
@login_required
def profile():
    """Show how your profile looks to other users.

    This is a read-only *public view* of your profile (within the app), matching
    what others will see when viewing you.
    """
    me = current_user()
    prof = get_profile(me)
    # Only show the public fields here to avoid accidentally exposing private info.
    public = {
        "username": me,
        "nickname": prof.get("nickname") or me,
        "bio": prof.get("bio") or "",
        "links": prof.get("links") or [],
    }
    return render_template("profile_view.html", title="My Profile", public=public)

@app.route("/profile/edit")
@login_required
def profile_edit():
    """Edit your profile fields."""
    return render_template("profile.html", title="Edit Profile")

@app.route("/profile/save", methods=["POST"])
@login_required

def profile_save():
    """profile_save.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    nickname = (request.form.get("nickname") or "").strip()
    bio = (request.form.get("bio") or "").strip()
    links_raw = (request.form.get("links") or "").strip()

    links: List[str] = []
    for line in links_raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if not (line.startswith("http://") or line.startswith("https://") or line.startswith("mailto:")):
            continue
        links.append(line[:300])

    # Optional fields
    def _lines10(val: str) -> str:
        """_lines10.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    val: Parameter.

Returns:
    Varies.
"""
        items = []
        for line in (val or "").splitlines():
            line = line.strip()
            if not line:
                continue
            items.append(line[:120])
            if len(items) >= 10:
                break
        return "\n".join(items)

    extras = {
        "email": (request.form.get("email") or "").strip(),
        "phone": (request.form.get("phone") or "").strip(),
        "car_model": (request.form.get("car_model") or "").strip(),
        "license_plate": (request.form.get("license_plate") or "").strip(),
        "id_number": (request.form.get("id_number") or "").strip(),
        "tax_number": (request.form.get("tax_number") or "").strip(),
        "height": (request.form.get("height") or "").strip(),
        "weight": (request.form.get("weight") or "").strip(),
        "eye_color": (request.form.get("eye_color") or "").strip(),
        "hair_color": (request.form.get("hair_color") or "").strip(),
        "job": (request.form.get("job") or "").strip(),
        "country": (request.form.get("country") or "").strip(),
        "state": (request.form.get("state") or "").strip(),
        "town": (request.form.get("town") or "").strip(),
        "city": (request.form.get("city") or "").strip(),
        "address": (request.form.get("address") or "").strip(),
        "family_members": _lines10(request.form.get("family_members") or ""),
        "close_friends": _lines10(request.form.get("close_friends") or ""),
    }

    # Basic length limits (keep DB small)
    for k in list(extras.keys()):
        extras[k] = extras[k][:200]

    set_profile(current_user(), nickname, bio[:800], links, extras=extras)
    flash("Profile saved.")
    return redirect(url_for("profile"))


# ---------------------------
# Account security: password change + security questions 2FA + recovery
# ---------------------------

def _norm_answer(s: str) -> str:
    """_norm_answer.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    s: Parameter.

Returns:
    Varies.
"""
    return (s or "").strip().lower()

def get_user_security(username: str) -> dict:
    """get_user_security.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    username: Parameter.

Returns:
    Varies.
"""
    conn = db_connect()
    row = conn.execute("SELECT * FROM user_security WHERE username=?", (username,)).fetchone()
    conn.close()
    if not row:
        return {"enabled": 0, "q1": "", "q2": "", "q3": ""}
    return {
        "enabled": int(row["enabled"] or 0),
        "q1": row["q1"] or "",
        "q2": row["q2"] or "",
        "q3": row["q3"] or "",
    }

def user_2fa_enabled(username: str) -> bool:
    """user_2fa_enabled.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    username: Parameter.

Returns:
    Varies.
"""
    try:
        sec = get_user_security(username)
        return bool(int(sec.get("enabled") or 0) == 1 and sec.get("q1") and sec.get("q2") and sec.get("q3"))
    except Exception:
        return False

def set_user_security(username: str, q1: str, q2: str, q3: str, a1: str, a2: str, a3: str, enabled: bool):
    """set_user_security.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    username: Parameter.
    q1: Parameter.
    q2: Parameter.
    q3: Parameter.
    a1: Parameter.
    a2: Parameter.
    a3: Parameter.
    enabled: Parameter.

Returns:
    Varies.
"""
    q1, q2, q3 = (q1 or "").strip()[:120], (q2 or "").strip()[:120], (q3 or "").strip()[:120]
    # Store hashed answers (PBKDF2 via werkzeug)
    a1h = generate_password_hash(_norm_answer(a1)) if a1 else None
    a2h = generate_password_hash(_norm_answer(a2)) if a2 else None
    a3h = generate_password_hash(_norm_answer(a3)) if a3 else None
    en = 1 if enabled else 0

    conn = db_connect()
    conn.execute(
        """INSERT INTO user_security(username,q1,q2,q3,a1_hash,a2_hash,a3_hash,enabled,updated_at)
             VALUES(?,?,?,?,?,?,?,?,?)
             ON CONFLICT(username) DO UPDATE SET
               q1=excluded.q1, q2=excluded.q2, q3=excluded.q3,
               a1_hash=COALESCE(excluded.a1_hash, user_security.a1_hash),
               a2_hash=COALESCE(excluded.a2_hash, user_security.a2_hash),
               a3_hash=COALESCE(excluded.a3_hash, user_security.a3_hash),
               enabled=excluded.enabled,
               updated_at=excluded.updated_at
        """,
        (username, q1, q2, q3, a1h, a2h, a3h, en, now_z())
    )
    conn.commit()
    conn.close()

def verify_security_answers(username: str, answers: dict) -> bool:
    """verify_security_answers.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    username: Parameter.
    answers: Parameter.

Returns:
    Varies.
"""
    conn = db_connect()
    row = conn.execute("SELECT a1_hash,a2_hash,a3_hash FROM user_security WHERE username=?", (username,)).fetchone()
    conn.close()
    if not row:
        return False
    for k, col in (("a1", "a1_hash"), ("a2", "a2_hash"), ("a3", "a3_hash")):
        if k in answers:
            h = row[col]
            if not h or not check_password_hash(h, _norm_answer(answers.get(k, ""))):
                return False
    return True

@app.route("/settings", methods=["GET"])
@login_required
def settings_root():
    """Main settings entry point."""
    return redirect(url_for("settings_security"))

@app.route("/settings/security", methods=["GET"])
@login_required
def settings_security():
    """Security settings page (2FA security questions, UI preferences)."""
    u = current_user()

    # Defensive defaults to prevent 500s if DB isn't ready yet
    sec = {"enabled": 0, "q1": "", "q2": "", "q3": ""}
    prefs = dict(DEFAULT_PREFS)

    try:
        if u:
            sec = get_user_security(u) or sec
            prefs = get_user_prefs(u) or prefs
    except Exception as e:
        try:
            app.logger.exception("settings_security failed: %s", e)
        except Exception:
            pass

    return render_template(
        "settings_security.html",
        title="Settings",
        sec=sec,
        prefs=prefs,
        accent_choices=ACCENT_CHOICES,
        font_choices=FONT_CHOICES,
        ui_theme_choices=UI_THEME_CHOICES,
    )

@app.route("/settings/password", methods=["POST"])
@login_required
def settings_change_password():
    """settings_change_password.

Internal helper function.

This docstring was added automatically to improve maintainability.

Returns:
    Varies.
"""
    me = current_user()
    cur_pw = request.form.get("current_password") or ""
    new_pw = request.form.get("new_password") or ""
    new_pw2 = request.form.get("new_password2") or ""
    if not new_pw or new_pw != new_pw2:
        flash("Passwords do not match.")
        return redirect(url_for("settings_security"))
    pw_err = _password_strength_error(new_pw, me)
    if pw_err:
        flash(pw_err)
        return redirect(url_for("settings_security"))

    conn = db_connect()
    row = conn.execute("SELECT pw_hash FROM users WHERE username=?", (me,)).fetchone()
    if not row or not check_password_hash(row["pw_hash"], cur_pw):
        conn.close()
        flash("Wrong current password.")
        return redirect(url_for("settings_security"))

    conn.execute("UPDATE users SET pw_hash=? WHERE username=?", (generate_password_hash(new_pw), me))
    conn.commit()
    conn.close()
    flash("Password changed.")
    return redirect(url_for("settings_security"))

@app.route("/settings/security_questions", methods=["POST"])
@login_required
def settings_security_questions():
    """settings_security_questions.

Internal helper function.

This docstring was added automatically to improve maintainability.

Returns:
    Varies.
"""
    me = current_user()
    q1 = request.form.get("q1") or ""
    q2 = request.form.get("q2") or ""
    q3 = request.form.get("q3") or ""
    a1 = request.form.get("a1") or ""
    a2 = request.form.get("a2") or ""
    a3 = request.form.get("a3") or ""
    enabled = (request.form.get("enable_2fa") == "1")

    # Require all questions, and require answers when enabling for the first time.
    existing = get_user_security(me)
    need_answers = enabled and (not existing.get("q1") or not existing.get("q2") or not existing.get("q3"))
    if enabled and (not q1 or not q2 or not q3):
        flash("All fields required.")
        return redirect(url_for("settings_security"))
    if need_answers and (not a1 or not a2 or not a3):
        flash("All fields required.")
        return redirect(url_for("settings_security"))

    set_user_security(me, q1, q2, q3, a1, a2, a3, enabled)
    flash("Saved.")
    return redirect(url_for("settings_security"))

@app.route("/two_factor", methods=["GET", "POST"])
def two_factor():
    """two_factor.

Internal helper function.

This docstring was added automatically to improve maintainability.

Returns:
    Varies.
"""
    # Only reachable right after password verification
    u = session.get("pre_2fa")
    if not u:
        return redirect(url_for("login"))

    ip = _client_ip() or "?"
    if request.method == "POST" and _too_many_attempts(ip, u):
        flash("Too many attempts. Try again later.")
        session.pop("pre_2fa", None)
        session.pop("two_factor_idxs", None)
        return redirect(url_for("login"))

    conn = db_connect()
    row = conn.execute("SELECT q1,q2,q3 FROM user_security WHERE username=?", (u,)).fetchone()
    conn.close()
    if not row:
        session.pop("pre_2fa", None)
        return redirect(url_for("login"))

    questions = [row["q1"] or "", row["q2"] or "", row["q3"] or ""]
    # Choose 2 questions per login attempt
    if request.method == "GET":
        idxs = sorted(secrets.choice([[0,1],[0,2],[1,2]]))
        session["two_factor_idxs"] = idxs
        qs = [(i, questions[i]) for i in idxs]
        return render_template("two_factor.html", title="2FA", username=u, qs=qs)

    idxs = session.get("two_factor_idxs") or [0, 1]
    answers = {}
    for i in idxs:
        answers[f"a{i+1}"] = request.form.get(f"a{i+1}") or ""
    if not verify_security_answers(u, answers):
        _mark_fail(ip, u)
        flash("Invalid credentials.")
        return redirect(url_for("two_factor"))

        # Session capacity (per link/session scope): max 66 users + 1 admin.
    try:
        sc = current_scope()
        is_admin = user_is_admin(u)
        if not scope_capacity_ok(u, is_admin, sc):
            flash("This session is full (max 66 users + 1 admin). Try again later.")
            session.pop("pre_2fa", None)
            session.pop("two_factor_idxs", None)
            return redirect(url_for("login"))
    except Exception:
        pass

# Success: finalize login
    session.pop("pre_2fa", None)
    session.pop("two_factor_idxs", None)
    _clear_fail(ip, u)
    flash("Logged in.")
    return _complete_login_session(u, user_is_admin(u))



@app.route("/settings/appearance", methods=["GET"])
@login_required
def settings_appearance_page():
    u = current_user()
    prefs = dict(DEFAULT_PREFS)
    try:
        if u:
            prefs = get_user_prefs(u) or prefs
    except Exception:
        pass
    return render_template(
        "settings_appearance.html",
        title="Settings",
        prefs=prefs,
        accent_choices=ACCENT_CHOICES,
        font_choices=FONT_CHOICES,
        ui_theme_choices=UI_THEME_CHOICES,
    )

@app.route("/settings/appearance", methods=["POST"])
@login_required
def settings_appearance():
    """Update UI appearance settings (theme style, accent color, font) for the current user."""
    me = current_user()
    accent = (request.form.get("accent") or "").strip()
    font = (request.form.get("font") or "").strip()
    ui_theme = (request.form.get("ui_theme") or "").strip()
    set_user_prefs(me, accent, font, ui_theme)
    flash("Appearance updated.")
    return redirect(url_for("settings_appearance_page"))

@app.route("/recover", methods=["GET", "POST"])
def recover():
    """recover.

Internal helper function.

This docstring was added automatically to improve maintainability.

Returns:
    Varies.
"""
    # Password recovery using security questions
    if request.method == "GET":
        return render_template("recover.html", title="Recover")

    ip = _client_ip() or "?"
    if _rate_limit_hit("recover_post", ip, limit=10, window_sec=1800):
        flash("Too many recovery attempts. Try again later.")
        return render_template("recover.html", title="Recover")

    step = request.form.get("step") or "user"
    username = (request.form.get("username") or "").strip()

    if step == "user":
        if not username:
            flash("Username is required.")
            return render_template("recover.html", title="Recover")
        conn = db_connect()
        row = conn.execute("SELECT q1,q2,q3,enabled FROM user_security WHERE username=?", (username,)).fetchone()
        conn.close()
        if not row or not (row["q1"] and row["q2"] and row["q3"]):
            flash("Recovery is not set up for this user.")
            return render_template("recover.html", title="Recover")
        qs = [(1, row["q1"]), (2, row["q2"]), (3, row["q3"])]
        return render_template("recover.html", title="Recover", username=username, qs=qs, ask=True)

    # step == 'reset'
    new_pw = request.form.get("new_password") or ""
    new_pw2 = request.form.get("new_password2") or ""
    if not username or not new_pw or new_pw != new_pw2:
        flash("Passwords do not match.")
        return render_template("recover.html", title="Recover")
    pw_err = _password_strength_error(new_pw, username)
    if pw_err:
        flash(pw_err)
        return render_template("recover.html", title="Recover")

    answers = {
        "a1": request.form.get("a1") or "",
        "a2": request.form.get("a2") or "",
        "a3": request.form.get("a3") or "",
    }
    if not verify_security_answers(username, answers):
        flash("Invalid credentials.")
        return render_template("recover.html", title="Recover")

    conn = db_connect()
    conn.execute("UPDATE users SET pw_hash=? WHERE username=?", (generate_password_hash(new_pw), username))
    conn.commit()
    conn.close()
    flash("Password changed.")
    return redirect(url_for("login"))

@app.route("/profile/pic/upload", methods=["POST"])
@login_required
def profile_pic_upload():
    """profile_pic_upload.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    f = request.files.get("pic")
    if not f or not f.filename:
        flash("No picture selected.")
        return redirect(url_for("profile"))
    try:
        mime = _validate_profile_pic_upload(f)
    except ValueError:
        flash("Only images allowed.")
        return redirect(url_for("profile"))
    try:
        set_profile_pic(current_user(), f.stream, mime)
        flash("Profile picture updated.")
    except ValueError as ve:
        if str(ve) == "pfp_too_large":
            flash("Picture too large (max 10MB).")
        else:
            flash("Upload failed.")
    except Exception as e:
        log.exception("PFP upload failed: %s", e)
        flash("Upload failed.")
    return redirect(url_for("profile"))

@app.route("/profile/pic/remove", methods=["POST"])
@login_required
def profile_pic_remove():
    """profile_pic_remove.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    try:
        remove_profile_pic(current_user())
        flash("Profile picture removed.")
    except Exception:
        flash("Remove failed.")
    return redirect(url_for("profile"))

@app.route("/profile/pic/<username>")
@login_required
def profile_pic(username: str):
    """Serve a user's profile picture.

    New uploads are stored plaintext. If an older encrypted blob exists, we
    decrypt it on the fly for backwards compatibility.
    """
    ensure_profile_row(username)
    conn = db_connect()
    row = conn.execute("SELECT pic_path, pic_mime FROM profiles WHERE username=?", (username,)).fetchone()
    conn.close()
    if not row or not row["pic_path"] or not os.path.exists(row["pic_path"]):
        abort(404)

    mime = row["pic_mime"] or "image/jpeg"
    sp = row["pic_path"]

    try:
        if is_encrypted_file(sp):
            gen = aesgcm_decrypt_generator(sp)
            resp = Response(gen, mimetype=mime)
        else:
            from flask import send_file
            resp = send_file(sp, mimetype=mime, as_attachment=False, conditional=True, max_age=0)
    except Exception:
        abort(404)

    resp.headers["Cache-Control"] = "no-store"
    return resp


# ---------------------------
# Files (NOT encrypted)
# ---------------------------


def list_dir_entries(username: str, rel: str, sort: str, order: str):
    """list_dir_entries.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    username: Parameter.
    rel: Parameter.
    sort: Parameter.
    order: Parameter.

Returns:
    Varies.
"""
    ap = abs_user_path(username, rel)
    os.makedirs(ap, exist_ok=True)
    if not os.path.isdir(ap):
        raise ValueError("Not a directory")

    entries = []
    for name in os.listdir(ap):
        full = os.path.join(ap, name)
        try:
            st = os.stat(full)
        except Exception:
            continue
        is_dir = os.path.isdir(full)
        kind = "Folder" if is_dir else guess_mime(name)
        entries.append({"name": name, "is_dir": is_dir, "kind": kind, "size": st.st_size, "mtime": st.st_mtime})

    reverse = (order == "desc")

    def k_name(e):
        """k_name.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    e: Parameter.

Returns:
    Varies.
"""
        return (0 if e["is_dir"] else 1, e["name"].lower())
    def k_mtime(e):
        """k_mtime.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    e: Parameter.

Returns:
    Varies.
"""
        return (0 if e["is_dir"] else 1, e["mtime"])
    def k_size(e):
        """k_size.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    e: Parameter.

Returns:
    Varies.
"""
        return (0 if e["is_dir"] else 1, e["size"])
    def k_type(e):
        """k_type.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    e: Parameter.

Returns:
    Varies.
"""
        return (0 if e["is_dir"] else 1, e["kind"].lower(), e["name"].lower())

    if sort == "mtime":
        entries.sort(key=k_mtime, reverse=reverse)
    elif sort == "size":
        entries.sort(key=k_size, reverse=reverse)
    elif sort == "type":
        entries.sort(key=k_type, reverse=reverse)
    else:
        entries.sort(key=k_name, reverse=reverse)

    class Obj: pass
    out = []
    for e in entries:
        o = Obj()
        o.name = e["name"]
        o.is_dir = e["is_dir"]
        o.kind = e["kind"]
        o.size_h = "-" if e["is_dir"] else human_size(int(e["size"]))
        o.mtime_h = datetime.fromtimestamp(e["mtime"]).isoformat(sep=" ", timespec="seconds")
        out.append(o)
    return out

@app.route("/files")
@login_required
def files():
    """files.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    rel = request.args.get("p", "") or ""
    sort = (request.args.get("sort") or "name").lower()
    order = (request.args.get("order") or "asc").lower()
    if sort not in ("name", "mtime", "size", "type"):
        sort = "name"
    if order not in ("asc", "desc"):
        order = "asc"

    try:
        rel = safe_relpath(rel)
        entries = list_dir_entries(current_user(), rel, sort, order)
    except Exception:
        flash("Invalid path.")
        return redirect(url_for("files"))

    parent = "/".join(rel.split("/")[:-1]) if rel else ""
    return render_template("files.html", title="Files", relpath=rel, parent_relpath=parent,
                           entries=entries, sort=sort, order=order)

@app.route("/mkdir", methods=["POST"])
@login_required
def mkdir():
    """mkdir.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    rel = request.form.get("p", "") or ""
    name = (request.form.get("name") or "").strip()
    if not name:
        return redirect(url_for("files", p=rel))
    try:
        rel = safe_relpath(rel)
        name = secure_filename(name)
        if not name:
            raise ValueError("bad name")
        ap = abs_user_path(current_user(), rel)
        newp = os.path.join(ap, name)
        os.makedirs(newp, exist_ok=False)
        flash("Folder created.")
    except FileExistsError:
        flash("Folder already exists.")
    except Exception:
        flash("Could not create folder.")
    return redirect(url_for("files", p=rel))

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    """Upload a file into the user vault (plaintext).

    Per your request, vault files are stored without encryption. (Older installs
    may still contain encrypted blobs; downloading them remains supported.)
    """
    rel = request.form.get("p", "") or ""
    f = request.files.get("file")
    if not f or not f.filename:
        flash("No file selected.")
        return redirect(url_for("files", p=rel))

    # Enforce vault file limit (333MB).
    fsz = _filestorage_size(f)
    if fsz is not None and fsz > FILES_MAX_BYTES:
        flash("File too large (max 333MB).")
        return redirect(url_for("files", p=rel))

    try:
        rel = safe_relpath(rel)
        filename = _validate_vault_upload_filename(f.filename, getattr(f, "mimetype", None))
        if not filename:
            raise ValueError("bad filename")

        dest_dir = abs_user_path(current_user(), rel)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, filename)

        size = _save_plain_upload(f, dest_path)
        if int(size) > FILES_MAX_BYTES:
            try:
                os.remove(dest_path)
            except Exception:
                pass
            flash("File too large (max 333MB).")
            return redirect(url_for("files", p=rel))
        flash("Uploaded.")
    except ValueError as ve:
        if str(ve) in ("forbidden_type", "unsupported_type"):
            flash("Forbidden file type.")
        else:
            flash("Upload failed.")
    except Exception as e:
        log.exception("Upload failed: %s", e)
        flash("Upload failed.")

    return redirect(url_for("files", p=rel))

# ---------------------------
# Fast/resumable upload API (chunked)
# ---------------------------

UPLOAD_LOCK = threading.Lock()

def _upload_meta_path(upload_id: str) -> str:
    """_upload_meta_path.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    upload_id: Parameter.

Returns:
    Varies.
"""
    return os.path.join(TMP_UPLOAD_DIR, f"{upload_id}.json")

def _upload_tmp_path(upload_id: str) -> str:
    """_upload_tmp_path.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    upload_id: Parameter.

Returns:
    Varies.
"""
    return os.path.join(TMP_UPLOAD_DIR, f"{upload_id}.part")

@app.route("/api/upload/init", methods=["POST"])
@login_required
def api_upload_init():
    """api_upload_init.

Internal helper function.

This docstring was added automatically to improve maintainability.

Returns:
    Varies.
"""
    data = request.get_json(silent=True) or {}
    rel = data.get("p", "") or ""
    filename = secure_filename((data.get("filename") or "").strip())
    total = int(data.get("total_chunks") or 0)
    if not filename or total <= 0 or total > 5000:
        return jsonify({"ok": False, "error": "bad_request"}), 400
    try:
        filename = _validate_vault_upload_filename(filename)
    except ValueError:
        return jsonify({"ok": False, "error": "forbidden_type"}), 400
    try:
        rel = safe_relpath(rel)
    except Exception:
        return jsonify({"ok": False, "error": "bad_path"}), 400

    upload_id = base64.urlsafe_b64encode(os.urandom(18)).decode("ascii").rstrip("=")
    meta = {
        "u": current_user(),
        "p": rel,
        "filename": filename,
        "total_chunks": total,
        "received": [],
        "created_at": now_z(),
    }
    os.makedirs(TMP_UPLOAD_DIR, exist_ok=True)
    with open(_upload_meta_path(upload_id), "w", encoding="utf-8") as f:
        json.dump(meta, f)
    return jsonify({"ok": True, "upload_id": upload_id})

@app.route("/api/upload/chunk", methods=["POST"])
@login_required
def api_upload_chunk():
    """Upload a single vault chunk (sequential, resumable).

    Notes:
      - We require sequential chunk indices (0..total-1) because we append to a temp file.
      - Duplicate/retried chunks are safely ignored (won't corrupt the file).
      - Total size is capped at FILES_MAX_BYTES.
    """
    upload_id = (request.form.get("upload_id") or "").strip()
    try:
        idx = int(request.form.get("index") or 0)
        total = int(request.form.get("total") or 0)
    except Exception:
        return jsonify({"ok": False, "error": "bad_request"}), 400

    chunk = request.files.get("chunk")
    if not upload_id or total <= 0 or chunk is None or total > 5000:
        return jsonify({"ok": False, "error": "bad_request"}), 400
    if idx < 0 or idx >= total:
        return jsonify({"ok": False, "error": "bad_index"}), 400

    meta_path = _upload_meta_path(upload_id)
    if not os.path.exists(meta_path):
        return jsonify({"ok": False, "error": "not_found"}), 404

    done = False
    received_n = 0

    with UPLOAD_LOCK:
        try:
            meta = json.loads(open(meta_path, "r", encoding="utf-8").read() or "{}")
        except Exception:
            return jsonify({"ok": False, "error": "bad_meta"}), 400
        if meta.get("u") != current_user():
            return jsonify({"ok": False, "error": "forbidden"}), 403
        if int(meta.get("total_chunks") or 0) != total:
            return jsonify({"ok": False, "error": "bad_total"}), 400

        rec = sorted(set(int(x) for x in (meta.get("received") or [])))
        expected = len(rec)

        # If the client retried a chunk we already have, acknowledge without rewriting.
        if idx < expected:
            received_n = expected
            done = (received_n >= total)
            return jsonify({"ok": True, "done": done, "received": received_n, "total": total})

        # Enforce sequential upload order (prevents corruption and index-skipping).
        if idx != expected:
            return jsonify({"ok": False, "error": "out_of_order", "expected": expected}), 409

        # Append chunk to temp file
        tmp_path = _upload_tmp_path(upload_id)
        os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
        mode = "ab" if os.path.exists(tmp_path) else "wb"
        with open(tmp_path, mode) as out:
            shutil.copyfileobj(chunk.stream, out, length=8 * 1024 * 1024)

        # Enforce 333MB total cap for vault uploads.
        try:
            cur_bytes = int(os.path.getsize(tmp_path))
        except Exception:
            cur_bytes = 0
        if cur_bytes > FILES_MAX_BYTES:
            # Cleanup and reject the upload.
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            try:
                os.remove(meta_path)
            except Exception:
                pass
            return jsonify({"ok": False, "error": "too_large", "max": FILES_MAX_BYTES}), 413

        rec.append(idx)
        meta["received"] = rec
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f)

        received_n = len(rec)
        done = (received_n >= total)

        if done:
            # Finalize once we have all chunks.
            rel = safe_relpath(meta.get("p") or "")
            dest_dir = abs_user_path(current_user(), rel)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, meta.get("filename") or "upload.bin")
            os.replace(tmp_path, dest_path)
            try:
                os.remove(meta_path)
            except Exception:
                pass

    return jsonify({"ok": True, "done": done, "received": received_n, "total": total})

@app.route("/delete", methods=["POST"])
@login_required
def delete():
    """delete.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    rel = request.form.get("p", "") or ""
    is_dir = request.form.get("is_dir", "0") == "1"
    try:
        rel = safe_relpath(rel)
        if rel == "":
            raise ValueError("refuse_root")
        ap = abs_user_path(current_user(), rel)
        if is_dir:
            shutil.rmtree(ap)
            flash("Folder deleted.")
        else:
            os.remove(ap)
            flash("File deleted.")
    except ValueError as ve:
        if str(ve) == "refuse_root":
            flash("Cannot delete the vault root folder.")
        else:
            flash("Delete failed.")
    except Exception:
        flash("Delete failed.")
    parent = "/".join(rel.split("/")[:-1]) if rel else ""
    return redirect(url_for("files", p=parent))

@app.route("/download")
@login_required
def download():
    """Download a vault file."""
    p = request.args.get("p", "") or ""
    try:
        p = safe_relpath(p)
        ap = abs_user_path(current_user(), p)
        if os.path.isdir(ap):
            flash("Cannot download a folder.")
            return redirect(url_for("files", p="/".join(p.split("/")[:-1])))

        if not os.path.exists(ap):
            flash("File not found.")
            return redirect(url_for("files", p="/".join(p.split("/")[:-1])))

        filename = os.path.basename(ap)
        mime = guess_mime(filename)

        if is_encrypted_file(ap):
            gen = aesgcm_decrypt_generator(ap)
            resp = Response(gen, mimetype=mime)
            resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        else:
            from flask import send_file
            resp = send_file(
                ap,
                mimetype=mime,
                as_attachment=True,
                download_name=filename,
                conditional=True,
                max_age=0,
            )

        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.exception("Download failed: %s", e)
        flash("Download failed.")
        return redirect(url_for("files"))

@app.route("/view")
@login_required
def view_file():
    """View a vault file.

    For safety, we allow inline rendering only for non-active content types
    (images/video/audio/pdf/text). HTML/SVG/XML are forced to download to
    prevent stored XSS on the app origin.
    """
    p = request.args.get("p", "") or ""
    try:
        p = safe_relpath(p)
        ap = abs_user_path(current_user(), p)
        if os.path.isdir(ap) or (not os.path.exists(ap)):
            abort(404)

        filename = os.path.basename(ap)
        mime = guess_mime(filename)
        inline_ok = is_inline_safe(mime, filename)

        from flask import send_file

        if is_encrypted_file(ap):
            gen = aesgcm_decrypt_generator(ap)
            resp = Response(gen, mimetype=(mime if inline_ok else "application/octet-stream"))
        else:
            resp = send_file(
                ap,
                mimetype=(mime if inline_ok else "application/octet-stream"),
                as_attachment=(not inline_ok),
                conditional=True,
                max_age=0,
            )

        disp_type = "inline" if inline_ok else "attachment"
        resp.headers["Content-Disposition"] = f'{disp_type}; filename="{filename}"'
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.exception("View failed: %s", e)
        flash("Open failed.")
        return redirect(url_for("files"))

# ---------------------------
# Admin panel (kick / delete users)
# ---------------------------

@app.route("/admin")
@login_required
def admin_panel():
    """admin_panel.

Admin-only route handler.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    require_admin()
    conn = db_connect()
    rows = conn.execute("SELECT username, is_admin, created_at FROM users ORDER BY is_admin DESC, username ASC").fetchall()
    devreq = conn.execute("SELECT id, username, device_fp, requested_ip, requested_at, status FROM device_access_requests WHERE status='pending' ORDER BY id DESC LIMIT 200").fetchall()
    conn.close()
    class Obj:
        def __init__(self, d):
            """__init__.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    self: Parameter.
    d: Parameter.

Returns:
    Varies.
"""
            self.__dict__.update(d)
    return render_template("admin.html", title="Admin", users=[Obj(dict(r)) for r in rows], devreq=[Obj(dict(r)) for r in (devreq or [])], me=current_user())

@app.route("/admin/logs")
@login_required
def admin_logs():
    require_admin()
    selected_name = os.path.basename((request.args.get("name") or "").strip())
    files = []
    try:
        for name in sorted(os.listdir(LOG_DIR)):
            path = os.path.join(LOG_DIR, name)
            if os.path.isfile(path):
                files.append({"name": name, "size": os.path.getsize(path)})
    except Exception:
        files = []
    selected_content = ""
    if selected_name:
        path = os.path.join(LOG_DIR, selected_name)
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    selected_content = f.read()[-200000:]
            except Exception as e:
                selected_content = f"Could not read log: {e}"
    return render_template("admin_logs.html", title="Admin logs", files=files, selected_name=selected_name, selected_content=selected_content)




@app.route("/admin/device_approve", methods=["POST"])
@login_required
def admin_device_approve():
    require_admin()
    try:
        log_security_event("admin_action", detail="approve_device_request", username=current_user(), level="info")
    except Exception:
        pass
    rid = (request.form.get("req_id") or "").strip()
    if not rid.isdigit():
        return redirect(url_for("admin_panel"))
    conn = db_connect()
    row = conn.execute("SELECT id, username, device_fp, status FROM device_access_requests WHERE id=?", (int(rid),)).fetchone()
    if not row:
        conn.close()
        flash("Request not found.")
        return redirect(url_for("admin_panel"))
    if row["status"] != "pending":
        conn.close()
        flash("Request already handled.")
        return redirect(url_for("admin_panel"))
    conn.execute(
        "UPDATE device_access_requests SET status='approved', approved_by=?, approved_at=? WHERE id=?",
        (current_user(), now_z(), int(rid))
    )
    conn.commit()
    conn.close()
    flash(f"Approved device request for @{row['username']}.")
    return redirect(url_for("admin_panel"))

@app.route("/admin/device_deny", methods=["POST"])
@login_required
def admin_device_deny():
    require_admin()
    try:
        log_security_event("admin_action", detail="deny_device_request", username=current_user(), level="info")
    except Exception:
        pass
    rid = (request.form.get("req_id") or "").strip()
    if not rid.isdigit():
        return redirect(url_for("admin_panel"))
    conn = db_connect()
    row = conn.execute("SELECT id, username, status FROM device_access_requests WHERE id=?", (int(rid),)).fetchone()
    if not row:
        conn.close()
        flash("Request not found.")
        return redirect(url_for("admin_panel"))
    if row["status"] != "pending":
        conn.close()
        flash("Request already handled.")
        return redirect(url_for("admin_panel"))
    conn.execute(
        "UPDATE device_access_requests SET status='denied', approved_by=?, approved_at=? WHERE id=?",
        (current_user(), now_z(), int(rid))
    )
    conn.commit()
    conn.close()
    flash(f"Denied device request for @{row['username']}.")
    return redirect(url_for("admin_panel"))

@app.route("/admin/promote", methods=["POST"])
@login_required
def admin_promote():
    """admin_promote.

Admin-only route handler.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    require_admin()
    try:
        log_security_event("admin_action", detail="promote_user", username=current_user(), level="info")
    except Exception:
        pass
    u = (request.form.get("username") or "").strip()
    if not u:
        return redirect(url_for("admin_panel"))
    # Do not promote self redundantly
    conn = db_connect()
    row = conn.execute("SELECT is_admin FROM users WHERE username=?", (u,)).fetchone()
    if not row:
        conn.close()
        flash("User not found.")
        return redirect(url_for("admin_panel"))
    if int(row["is_admin"]) == 1:
        conn.close()
        flash("User is already an admin.")
        return redirect(url_for("admin_panel"))

    # Promote + bind to this device (admin actions are allowed only locally on the host device)
    conn.execute("UPDATE users SET is_admin=1, admin_device_id=? WHERE username=?", (DEVICE_ID, u))
    conn.commit()
    conn.close()
    flash(f"Promoted @{u} to admin.")
    return redirect(url_for("admin_panel"))

@app.route("/admin/demote", methods=["POST"])
@login_required
def admin_demote():
    """admin_demote.

Admin-only route handler.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    require_admin()
    try:
        log_security_event("admin_action", detail="demote_user", username=current_user(), level="info")
    except Exception:
        pass
    u = (request.form.get("username") or "").strip()
    if not u:
        return redirect(url_for("admin_panel"))
    if u == current_user():
        flash("You cannot demote yourself here.")
        return redirect(url_for("admin_panel"))

    conn = db_connect()
    # Ensure we don't remove the last admin
    admins = conn.execute("SELECT COUNT(*) AS c FROM users WHERE is_admin=1").fetchone()
    if admins and int(admins["c"]) <= 1:
        conn.close()
        flash("Refusing to remove the last admin.")
        return redirect(url_for("admin_panel"))

    row = conn.execute("SELECT is_admin FROM users WHERE username=?", (u,)).fetchone()
    if not row:
        conn.close()
        flash("User not found.")
        return redirect(url_for("admin_panel"))
    if int(row["is_admin"]) != 1:
        conn.close()
        flash("User is not an admin.")
        return redirect(url_for("admin_panel"))

    conn.execute("UPDATE users SET is_admin=0, admin_device_id=NULL WHERE username=?", (u,))
    conn.commit()
    conn.close()
    flash(f"Removed admin from @{u}.")
    return redirect(url_for("admin_panel"))

@app.route("/admin/kick", methods=["POST"])
@login_required
def admin_kick_user():
    """admin_kick_user.

Admin-only route handler.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    require_admin()
    try:
        log_security_event("admin_action", detail="kick_user", username=current_user(), level="info")
    except Exception:
        pass
    u = (request.form.get("username") or "").strip()
    if not u or u == current_user():
        return redirect(url_for("admin_panel"))
    conn = db_connect()
    conn.execute("UPDATE users SET logout_at=? WHERE username=?", (now_z(), u))
    conn.commit()
    conn.close()
    flash(f"Kicked @{u} (forced logout).")
    return redirect(url_for("admin_panel"))

@app.route("/admin/delete", methods=["POST"])
@login_required
def admin_delete_user():
    """admin_delete_user.

Admin-only route handler.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    require_admin()
    try:
        log_security_event("admin_action", detail="delete_user", username=current_user(), level="info")
    except Exception:
        pass
    u = (request.form.get("username") or "").strip()
    if not u or u == current_user():
        return redirect(url_for("admin_panel"))

    conn = db_connect()
    # Prevent deleting the last admin
    if user_is_admin(u):
        row = conn.execute("SELECT COUNT(*) AS c FROM users WHERE is_admin=1").fetchone()
        if row and int(row["c"]) <= 1:
            conn.close()
            flash("Cannot delete the last admin.")
            return redirect(url_for("admin_panel"))

    # Remove account + public profile + memberships
    conn.execute("DELETE FROM profiles WHERE username=?", (u,))
    conn.execute("DELETE FROM group_members WHERE username=?", (u,))
    conn.execute("DELETE FROM users WHERE username=?", (u,))
    conn.commit()
    conn.close()

    # Also remove their vault directory (encrypted files)
    try:
        shutil.rmtree(user_root(u), ignore_errors=True)
    except Exception:
        pass

    flash(f"Deleted @{u}.")
    return redirect(url_for("admin_panel"))




@app.route("/admin/delete_me", methods=["POST"])
@login_required
def admin_delete_me():
    """Delete the currently logged-in admin account (keeps files)."""
    require_admin()
    try:
        log_security_event("admin_action", detail="delete_self_admin", username=current_user(), level="info")
    except Exception:
        pass
    me = current_user()
    password = request.form.get("password") or ""

    conn = db_connect()
    row = conn.execute("SELECT pw_hash FROM users WHERE username=?", (me,)).fetchone()
    if not row or not check_password_hash(row["pw_hash"], password):
        conn.close()
        flash("Wrong password.")
        return redirect(url_for("admin_panel"))

    # Remove login + public profile + memberships (DO NOT delete files on disk)
    conn.execute("DELETE FROM profiles WHERE username=?", (me,))
    conn.execute("DELETE FROM group_members WHERE username=?", (me,))
    conn.execute("DELETE FROM users WHERE username=?", (me,))
    conn.commit()
    conn.close()

    session.clear()
    flash("Admin account deleted. If no admins remain, restart to create a new admin.")
    return redirect(url_for("login"))

@app.route("/admin/self_destruct", methods=["POST"])
@login_required
def admin_self_destruct():
    """Delete all ButSystem data from storage. Admin-only, requires creds."""
    require_admin()
    try:
        log_security_event("admin_action", detail="self_destruct_attempt", username=current_user(), level="info")
    except Exception:
        pass
    u = (request.form.get("username") or "").strip()
    p = request.form.get("password") or ""
    me = current_user()

    if not u or u != me:
        flash("Username must match your current session.")
        return redirect(url_for("admin_panel"))

    conn = db_connect()
    row = conn.execute("SELECT pw_hash, is_admin FROM users WHERE username=?", (u,)).fetchone()
    conn.close()
    if not row or not int(row["is_admin"]) or not check_password_hash(row["pw_hash"], p):
        flash("Invalid credentials.")
        return redirect(url_for("admin_panel"))

    # Safety: only delete our own app folder
    target = os.path.abspath(BASE_DIR)
    if os.path.basename(target) != "ButSystem" or target in ("/", "/storage", "/storage/emulated", "/storage/emulated/0", os.path.abspath(HOMEWORK_ROOT)):
        flash("Refusing to delete an unsafe path.")
        return redirect(url_for("admin_panel"))

    try:
        shutil.rmtree(target, ignore_errors=True)
        try:
            shutil.rmtree(os.path.abspath(TOR_DIR), ignore_errors=True)
        except Exception:
            pass

    except Exception:
        pass

    session.clear()
    flash("ButSystem deleted from storage. Server shutting down.")

    # Best-effort shutdown (Werkzeug)
    try:
        func = request.environ.get("werkzeug.server.shutdown")
        if func:
            func()
    except Exception:
        pass

    # If shutdown func isn't available, exit hard after responding.
    def _exit_soon():
        """_exit_soon.

Internal helper function.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
        try:
            time.sleep(1.0)
        finally:
            os._exit(0)

    threading.Thread(target=_exit_soon, daemon=True).start()
    return redirect(url_for("login"))


# ---------------------------
# Chats (DM)
# ---------------------------

def _local_time_str(utc_iso: Optional[str]) -> Optional[str]:
    """_local_time_str.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    utc_iso: Parameter.

Returns:
    Varies.
"""
    if not utc_iso:
        return None
    try:
        # display as-is (UTC) but friendly; device local could vary; keep consistent
        dt = datetime.fromisoformat(utc_iso.replace("Z",""))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return utc_iso

def _dm_store_voice(dm_id: int, file_storage) -> Tuple[int, str]:
    """Store a DM voice message (plaintext on disk)."""
    mime = _validate_chat_voice_upload(file_storage)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO dm_voice(dm_id, mime, stored_path, created_at) VALUES(?,?,?,?)",
                (dm_id, mime, "PENDING", now_z()))
    vid = cur.lastrowid

    stored_path = os.path.join(ATT_DIR, f"dm_voice_{vid}.bin")
    size = 0
    try:
        size = _save_plain_upload(file_storage, stored_path)
    except Exception:
        # Keep DB row; caller will show error.
        conn.close()
        raise

    # Store final path immediately (no background encryption step).
    conn.execute("UPDATE dm_voice SET stored_path=? WHERE id=?", (stored_path, vid))
    conn.execute("UPDATE dm_messages SET has_voice=1 WHERE id=?", (dm_id,))
    conn.commit()
    conn.close()
    return vid, mime


    _save_plain_upload(file_storage, tmp_plain)

    def finalize(ok: bool, err: Optional[str]):
        """finalize.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    ok: Parameter.
    err: Parameter.

Returns:
    Varies.
"""
        c = db_connect()
        if ok and os.path.exists(stored_path):
            c.execute("UPDATE dm_voice SET stored_path=? WHERE id=?", (stored_path, vid))
        c.commit()
        c.close()

    _bg_encrypt_file(tmp_plain, stored_path, finalize)

    conn.execute("UPDATE dm_messages SET has_voice=1 WHERE id=?", (dm_id,))
    conn.commit()
    conn.close()
    return vid, mime


def _dm_store_file(dm_id: int, file_storage) -> Dict[str, str]:
    """Store a regular DM attachment (plaintext on disk)."""
    filename, mime = _validate_chat_file_upload(file_storage)

    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO dm_files(dm_id, filename, mime, stored_path, size, created_at) VALUES(?,?,?,?,?,?)",
        (dm_id, filename, mime, "PENDING", 0, now_z())
    )
    fid = cur.lastrowid

    stored_path = os.path.join(DM_FILES_DIR, f"dm_file_{fid}.bin")

    # Save upload bytes directly (no background encryption).
    size = _save_plain_upload(file_storage, stored_path)
    if int(size) > CHAT_MAX_BYTES:
        try:
            os.remove(stored_path)
        except Exception:
            pass
        conn.execute("DELETE FROM dm_files WHERE id=?", (fid,))
        conn.execute("UPDATE dm_messages SET has_file=0 WHERE id=?", (dm_id,))
        conn.commit()
        conn.close()
        raise ValueError("too_large")

    conn.execute("UPDATE dm_files SET stored_path=?, size=? WHERE id=?", (stored_path, int(size), fid))
    conn.execute("UPDATE dm_messages SET has_file=1 WHERE id=?", (dm_id,))
    conn.commit()
    conn.close()

    return {"id": fid, "mime": mime, "filename": filename, "size": int(size)}


def _discussion_store_voice_tx(conn, msg_id: int, file_storage) -> Tuple[int, str, str]:
    """Store a discussion voice message atomically within an existing DB transaction."""
    mime = _validate_chat_voice_upload(file_storage)
    cur = conn.cursor()
    cur.execute("INSERT INTO discussion_voice(msg_id, mime, stored_path, created_at) VALUES(?,?,?,?)",
                (msg_id, mime, "PENDING", now_z()))
    vid = cur.lastrowid
    stored_path = os.path.join(ATT_DIR, f"discussion_voice_{vid}.bin")
    size = _save_plain_upload(file_storage, stored_path)
    if int(size) > CHAT_MAX_BYTES:
        try:
            os.remove(stored_path)
        except Exception:
            pass
        raise ValueError("too_large")
    conn.execute("UPDATE discussion_voice SET stored_path=? WHERE id=?", (stored_path, vid))
    conn.execute("UPDATE discussion_messages SET has_voice=1 WHERE id=?", (msg_id,))
    return vid, mime, stored_path


def _discussion_store_file_tx(conn, msg_id: int, file_storage) -> Dict[str, Any]:
    """Store a discussion file attachment atomically within an existing DB transaction."""
    filename, mime = _validate_chat_file_upload(file_storage)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO discussion_files(msg_id, filename, mime, stored_path, size, created_at) VALUES(?,?,?,?,?,?)",
        (msg_id, filename, mime, "PENDING", 0, now_z()),
    )
    fid = cur.lastrowid
    stored_path = os.path.join(DISC_FILES_DIR, f"discussion_file_{fid}.bin")
    size = _save_plain_upload(file_storage, stored_path)
    if int(size) > CHAT_MAX_BYTES:
        try:
            os.remove(stored_path)
        except Exception:
            pass
        raise ValueError("too_large")
    conn.execute(
        "UPDATE discussion_files SET stored_path=?, size=?, mime=?, filename=? WHERE id=?",
        (stored_path, int(size), mime, filename, fid),
    )
    conn.execute("UPDATE discussion_messages SET has_file=1 WHERE id=?", (msg_id,))
    return {"id": fid, "mime": mime, "filename": filename, "size": int(size), "stored_path": stored_path}


def _discussion_store_remote_gif_tx(conn, msg_id: int, gif_url: str) -> Dict[str, Any]:
    """Download and store a remote GIF/clip for discussion within an existing DB transaction."""
    gif_url = (gif_url or "").strip()
    if not gif_url:
        raise ValueError("Empty gif url")
    u = urllib.parse.urlparse(gif_url)
    if u.scheme not in ("http", "https"):
        raise ValueError("GIF url must be http(s)")

    _validate_remote_media_url(gif_url)

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO discussion_files(msg_id, filename, mime, stored_path, size, created_at) VALUES(?,?,?,?,?,?)",
        (msg_id, "gif.gif", "image/gif", "PENDING", 0, now_z()),
    )
    fid = cur.lastrowid
    stored_path = os.path.join(DISC_FILES_DIR, f"discussion_file_{fid}.bin")

    max_bytes = CHAT_MAX_BYTES  # 33 MB
    size = 0
    mime = "image/gif"
    filename = "gif.gif"

    req = urllib.request.Request(
        gif_url,
        headers={
            "User-Agent": "ButSystem/1.0 (+https://example.invalid)",
            "Accept": "image/gif,image/*,video/*,*/*;q=0.8",
        },
        method="GET",
    )
    with _safe_urlopen(req, timeout=12) as resp:
        ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype:
            mime = ctype
        if not (mime == "image/gif" or mime.startswith("video/")):
            path = (u.path or "").lower()
            if not (path.endswith(".gif") or path.endswith(".mp4") or path.endswith(".webm")):
                raise ValueError(f"Unsupported GIF mime: {mime}")
            if path.endswith(".mp4"):
                mime = "video/mp4"
            elif path.endswith(".webm"):
                mime = "video/webm"
            else:
                mime = "image/gif"

        if mime == "image/gif":
            filename = f"gif_{fid}.gif"
        elif mime == "video/mp4":
            filename = f"gif_{fid}.mp4"
        elif mime == "video/webm":
            filename = f"gif_{fid}.webm"
        else:
            filename = f"file_{fid}"

        with open(stored_path, "wb") as f:
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise ValueError("GIF too large")
                f.write(chunk)

    conn.execute(
        "UPDATE discussion_files SET stored_path=?, size=?, mime=?, filename=? WHERE id=?",
        (stored_path, int(size), mime, filename, fid),
    )
    conn.execute("UPDATE discussion_messages SET has_file=1 WHERE id=?", (msg_id,))
    return {"id": fid, "mime": mime, "filename": filename, "size": int(size), "stored_path": stored_path}

def _dm_store_voice_tx(conn, dm_id: int, file_storage) -> Tuple[int, str, str]:
    """Store a DM voice message using an existing DB connection/transaction.

    This prevents a race where other clients can see the message before the attachment
    is saved/linked, which previously caused "blank" voice/file rows until a refresh.
    """
    mime = _validate_chat_voice_upload(file_storage)
    cur = conn.cursor()
    cur.execute("INSERT INTO dm_voice(dm_id, mime, stored_path, created_at) VALUES(?,?,?,?)",
                (dm_id, mime, "PENDING", now_z()))
    vid = cur.lastrowid
    stored_path = os.path.join(ATT_DIR, f"dm_voice_{vid}.bin")
    size = _save_plain_upload(file_storage, stored_path)
    if int(size) > CHAT_MAX_BYTES:
        try:
            os.remove(stored_path)
        except Exception:
            pass
        raise ValueError("too_large")
    conn.execute("UPDATE dm_voice SET stored_path=? WHERE id=?", (stored_path, vid))
    conn.execute("UPDATE dm_messages SET has_voice=1 WHERE id=?", (dm_id,))
    return vid, mime, stored_path


def _dm_store_file_tx(conn, dm_id: int, file_storage) -> Dict[str, Any]:
    """Store a DM attachment using an existing DB connection/transaction."""
    filename, mime = _validate_chat_file_upload(file_storage)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO dm_files(dm_id, filename, mime, stored_path, size, created_at) VALUES(?,?,?,?,?,?)",
        (dm_id, filename, mime, "PENDING", 0, now_z())
    )
    fid = cur.lastrowid
    stored_path = os.path.join(DM_FILES_DIR, f"dm_file_{fid}.bin")
    size = _save_plain_upload(file_storage, stored_path)
    if int(size) > CHAT_MAX_BYTES:
        try:
            os.remove(stored_path)
        except Exception:
            pass
        conn.execute("DELETE FROM dm_files WHERE id=?", (fid,))
        raise ValueError("too_large")
    conn.execute("UPDATE dm_files SET stored_path=?, size=? WHERE id=?", (stored_path, int(size), fid))
    conn.execute("UPDATE dm_messages SET has_file=1 WHERE id=?", (dm_id,))
    return {"id": fid, "mime": mime, "filename": filename, "size": int(size), "stored_path": stored_path}



def _validate_remote_media_url(url: str):
    """Validate a remote media URL to reduce SSRF risk.

    We block localhost/private/link-local/reserved IPs (including via DNS),
    and we only allow http(s) URLs.
    """
    u = urllib.parse.urlparse((url or "").strip())
    if u.scheme not in ("http", "https"):
        raise ValueError("URL must be http(s)")
    host = (u.hostname or "").strip().lower()
    if not host:
        raise ValueError("Missing host")
    # Block obvious local hostnames
    if host in ("localhost",) or host.endswith(".local") or host.endswith(".internal"):
        raise ValueError("Local hostnames are not allowed")

    def _bad_ip(ip: str) -> bool:
        try:
            a = ipaddress.ip_address(ip)
            return (
                a.is_private
                or a.is_loopback
                or a.is_link_local
                or a.is_reserved
                or a.is_multicast
                or a.is_unspecified
            )
        except Exception:
            return True

    # If hostname is a literal IP, validate directly.
    if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host) or ":" in host:
        if _bad_ip(host.strip("[]")):
            raise ValueError("Private IPs are not allowed")
        return

    # DNS resolve and block any non-public results.
    try:
        for fam, _, _, _, sockaddr in socket.getaddrinfo(host, None):
            ip = sockaddr[0]
            if _bad_ip(ip):
                raise ValueError("Private IPs are not allowed")
    except ValueError:
        raise
    except Exception:
        # If we cannot resolve safely, reject.
        raise ValueError("Unresolvable host")

class _SafeHTTPRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Let urllib build the redirected request, then validate the target.
        new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_req is None:
            return None
        _validate_remote_media_url(new_req.full_url)
        return new_req

_safe_urlopen_opener = urllib.request.build_opener(_SafeHTTPRedirectHandler())

def _safe_urlopen(req: urllib.request.Request, timeout: int = 12):
    """urlopen with strict redirect + host checks (SSRF hardening)."""
    _validate_remote_media_url(req.full_url)
    return _safe_urlopen_opener.open(req, timeout=timeout)

def _dm_store_remote_gif_tx(conn, dm_id: int, gif_url: str) -> Dict[str, Any]:
    """Download and store a remote GIF using an existing DB connection/transaction."""
    gif_url = (gif_url or "").strip()
    if not gif_url:
        raise ValueError("Empty gif url")
    u = urllib.parse.urlparse(gif_url)
    if u.scheme not in ("http", "https"):
        raise ValueError("GIF url must be http(s)")

    _validate_remote_media_url(gif_url)


    cur = conn.cursor()
    cur.execute(
        "INSERT INTO dm_files(dm_id, filename, mime, stored_path, size, created_at) VALUES(?,?,?,?,?,?)",
        (dm_id, "gif.gif", "image/gif", "PENDING", 0, now_z())
    )
    fid = cur.lastrowid
    stored_path = os.path.join(DM_FILES_DIR, f"dm_file_{fid}.bin")

    max_bytes = CHAT_MAX_BYTES  # 33 MB
    size = 0
    mime = "image/gif"
    filename = "gif.gif"

    req = urllib.request.Request(
        gif_url,
        headers={
            "User-Agent": "ButSystem/1.0 (+https://example.invalid)",
            "Accept": "image/gif,image/*,video/*,*/*;q=0.8",
        },
        method="GET",
    )
    with _safe_urlopen(req, timeout=12) as resp:
        ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype:
            mime = ctype
        if not (mime == "image/gif" or mime.startswith("video/")):
            path = (u.path or "").lower()
            if not (path.endswith(".gif") or path.endswith(".mp4") or path.endswith(".webm")):
                raise ValueError(f"Unsupported GIF mime: {mime}")
            if path.endswith(".mp4"):
                mime = "video/mp4"
            elif path.endswith(".webm"):
                mime = "video/webm"
            else:
                mime = "image/gif"

        if mime == "image/gif":
            filename = f"gif_{fid}.gif"
        elif mime == "video/mp4":
            filename = f"gif_{fid}.mp4"
        elif mime == "video/webm":
            filename = f"gif_{fid}.webm"
        else:
            filename = f"file_{fid}"

        with open(stored_path, "wb") as f:
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise ValueError("GIF too large")
                f.write(chunk)

    conn.execute("UPDATE dm_files SET stored_path=?, size=?, mime=?, filename=? WHERE id=?",
                 (stored_path, int(size), mime, filename, fid))
    conn.execute("UPDATE dm_messages SET has_file=1 WHERE id=?", (dm_id,))
    return {"id": fid, "mime": mime, "filename": filename, "size": int(size), "stored_path": stored_path}

def _dm_store_remote_gif(dm_id: int, gif_url: str) -> Dict[str, str]:
    """Download and store a remote GIF (or short MP4) as a DM attachment.

    This enables an Instagram-like GIF picker that sends a URL rather than an uploaded file.
    We keep this intentionally strict for safety:
      - only http(s)
      - size cap
    """
    gif_url = (gif_url or "").strip()
    if not gif_url:
        raise ValueError("Empty gif url")

    try:
        u = urllib.parse.urlparse(gif_url)
    except Exception as e:
        raise ValueError("Bad gif url") from e
    if u.scheme not in ("http", "https"):
        raise ValueError("GIF url must be http(s)")

    # Insert DB row first so we have a deterministic stored_path.
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO dm_files(dm_id, filename, mime, stored_path, size, created_at) VALUES(?,?,?,?,?,?)",
        (dm_id, "gif.gif", "image/gif", "PENDING", 0, now_z())
    )
    fid = cur.lastrowid
    stored_path = os.path.join(DM_FILES_DIR, f"dm_file_{fid}.bin")
    conn.commit()
    conn.close()

    # Download with a cap to avoid abuse.
    max_bytes = CHAT_MAX_BYTES  # 33 MB
    size = 0
    mime = "image/gif"
    filename = "gif.gif"

    req = urllib.request.Request(
        gif_url,
        headers={
            "User-Agent": "ButSystem/1.0 (+https://example.invalid)",
            "Accept": "image/gif,image/*,video/*,*/*;q=0.8",
        },
        method="GET",
    )
    try:
        with _safe_urlopen(req, timeout=12) as resp:
            ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            if ctype:
                mime = ctype
            # Allow gif and mp4/webm (many "GIFs" are delivered as mp4)
            if not (mime == "image/gif" or mime.startswith("video/")):
                # Some CDNs mislabel; fall back to extension check
                path = (u.path or "").lower()
                if not (path.endswith(".gif") or path.endswith(".mp4") or path.endswith(".webm")):
                    raise ValueError(f"Unsupported GIF mime: {mime}")
                if path.endswith(".mp4"):
                    mime = "video/mp4"
                elif path.endswith(".webm"):
                    mime = "video/webm"
                else:
                    mime = "image/gif"

            if mime == "image/gif":
                filename = f"gif_{fid}.gif"
            elif mime == "video/mp4":
                filename = f"gif_{fid}.mp4"
            elif mime == "video/webm":
                filename = f"gif_{fid}.webm"
            else:
                filename = f"file_{fid}"

            with open(stored_path, "wb") as f:
                while True:
                    chunk = resp.read(64 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > max_bytes:
                        raise ValueError("GIF too large")
                    f.write(chunk)
    except urllib.error.HTTPError as e:
        # Clean up DB row on failure.
        try:
            c = db_connect()
            c.execute("DELETE FROM dm_files WHERE id=?", (fid,))
            c.execute("UPDATE dm_messages SET has_file=0 WHERE id=?", (dm_id,))
            c.commit()
            c.close()
        except Exception:
            pass
        raise ValueError(f"GIF download failed ({e.code})") from e
    except Exception:
        try:
            if os.path.exists(stored_path):
                os.remove(stored_path)
        except Exception:
            pass
        try:
            c = db_connect()
            c.execute("DELETE FROM dm_files WHERE id=?", (fid,))
            c.execute("UPDATE dm_messages SET has_file=0 WHERE id=?", (dm_id,))
            c.commit()
            c.close()
        except Exception:
            pass
        raise

    # Update DB row + message flag.
    conn = db_connect()
    conn.execute("UPDATE dm_files SET stored_path=?, size=?, mime=?, filename=? WHERE id=?",
                 (stored_path, int(size), mime, filename, fid))
    conn.execute("UPDATE dm_messages SET has_file=1 WHERE id=?", (dm_id,))
    conn.commit()
    conn.close()
    return {"id": fid, "mime": mime, "filename": filename, "size": int(size)}


@app.route("/dm/file/<int:fid>")
@login_required
def dm_file_stream(fid: int):
    """Inline media stream for DM attachments.

    We only allow inline rendering for safe media types; active content
    (HTML/SVG/XML) is forced to download to prevent stored XSS.
    """
    me = current_user()
    conn = db_connect()
    row = conn.execute("""
        SELECT f.id, f.filename, f.mime, f.stored_path, m.sender, m.recipient
        FROM dm_files f
        JOIN dm_messages m ON m.id=f.dm_id
        WHERE f.id=?
    """, (fid,)).fetchone()
    conn.close()
    if not row or (me != row["sender"] and me != row["recipient"]):
        abort(404)
    peer = row["recipient"] if row["sender"] == me else row["sender"]
    if not _chat_lock_is_unlocked(me, "dm", peer):
        return redirect(url_for("chat_with", username=peer))
    sp = row["stored_path"]
    if not sp or not os.path.exists(sp):
        abort(404)

    filename = row["filename"] or f"dm-file-{fid}"
    mime = row["mime"] or guess_mime(filename)
    inline_ok = is_inline_safe(mime, filename)

    try:
        from flask import send_file
        if is_encrypted_file(sp):
            gen = aesgcm_decrypt_generator(sp)
            resp = Response(gen, mimetype=(mime if inline_ok else "application/octet-stream"))
        else:
            resp = send_file(
                sp,
                mimetype=(mime if inline_ok else "application/octet-stream"),
                as_attachment=(not inline_ok),
                conditional=True,
                max_age=0,
            )
    except Exception:
        abort(404)

    disp_type = "inline" if inline_ok else "attachment"
    resp.headers["Content-Disposition"] = f'{disp_type}; filename="{filename}"'
    resp.headers["Cache-Control"] = "no-store"
    return resp

@app.route("/dm/file/<int:fid>/download")
@login_required
def dm_file_download(fid: int):
    """Download attachment with a filename."""
    me = current_user()
    conn = db_connect()
    row = conn.execute("""
        SELECT f.id, f.filename, f.mime, f.stored_path, m.sender, m.recipient
        FROM dm_files f
        JOIN dm_messages m ON m.id=f.dm_id
        WHERE f.id=?
    """, (fid,)).fetchone()
    conn.close()
    if not row or (me != row["sender"] and me != row["recipient"]):
        abort(404)
    peer = row["recipient"] if row["sender"] == me else row["sender"]
    if not _chat_lock_is_unlocked(me, "dm", peer):
        return redirect(url_for("chat_with", username=peer))

    sp = row["stored_path"]
    if not sp or not os.path.exists(sp):
        abort(404)

    filename = row["filename"] or f"file_{fid}"
    mime = row["mime"] or "application/octet-stream"

    try:
        if is_encrypted_file(sp):
            gen = aesgcm_decrypt_generator(sp)
            headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
            return Response(gen, mimetype=mime, headers=headers)
    except Exception:
        abort(404)

    from flask import send_file
    return send_file(sp, mimetype=mime, as_attachment=True, download_name=filename)

@app.route("/discussion/file/<int:fid>")
@login_required
def discussion_file_stream(fid: int):
    """Inline media stream for Discussion attachments."""
    _feature_tables_init()
    me = current_user()
    conn = db_connect()
    row = conn.execute("""
        SELECT f.id, f.filename, f.mime, f.stored_path
        FROM discussion_files f
        WHERE f.id=?
    """, (fid,)).fetchone()
    conn.close()
    if not row:
        abort(404)
    sp = row["stored_path"]
    if not sp or not os.path.exists(sp):
        abort(404)

    filename = row["filename"] or f"discussion-file-{fid}"
    mime = row["mime"] or guess_mime(filename)
    inline_ok = is_inline_safe(mime, filename)

    try:
        from flask import send_file
        if is_encrypted_file(sp):
            gen = aesgcm_decrypt_generator(sp)
            resp = Response(gen, mimetype=(mime if inline_ok else "application/octet-stream"))
        else:
            resp = send_file(
                sp,
                mimetype=(mime if inline_ok else "application/octet-stream"),
                as_attachment=(not inline_ok),
                conditional=True,
                max_age=0,
            )
    except Exception:
        abort(404)

    disp_type = "inline" if inline_ok else "attachment"
    resp.headers["Content-Disposition"] = f'{disp_type}; filename="{filename}"'
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/discussion/file/<int:fid>/download")
@login_required
def discussion_file_download(fid: int):
    """Download a Discussion attachment with a filename."""
    _feature_tables_init()
    conn = db_connect()
    row = conn.execute("""
        SELECT id, filename, mime, stored_path
        FROM discussion_files
        WHERE id=?
    """, (fid,)).fetchone()
    conn.close()
    if not row:
        abort(404)

    sp = row["stored_path"]
    if not sp or not os.path.exists(sp):
        abort(404)

    filename = row["filename"] or f"file_{fid}"
    mime = row["mime"] or "application/octet-stream"

    try:
        if is_encrypted_file(sp):
            gen = aesgcm_decrypt_generator(sp)
            headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
            return Response(gen, mimetype=mime, headers=headers)
    except Exception:
        abort(404)

    from flask import send_file
    return send_file(sp, mimetype=mime, as_attachment=True, download_name=filename)


@app.route("/discussion/voice/<int:vid>")
@login_required
def discussion_voice_stream(vid: int):
    """Stream a Discussion voice message."""
    _feature_tables_init()
    conn = db_connect()
    row = conn.execute("""
        SELECT id, mime, stored_path
        FROM discussion_voice
        WHERE id=?
    """, (vid,)).fetchone()
    conn.close()
    if not row:
        abort(404)

    sp = row["stored_path"]
    if not sp or not os.path.exists(sp):
        abort(404)

    mime = row["mime"] or "audio/webm"
    try:
        if is_encrypted_file(sp):
            gen = aesgcm_decrypt_generator(sp)
            resp = Response(gen, mimetype=mime)
        else:
            from flask import send_file
            resp = send_file(sp, mimetype=mime, as_attachment=False, conditional=True, max_age=0)
    except Exception:
        abort(404)

    resp.headers["Cache-Control"] = "no-store"
    return resp

@app.route("/chats")
@login_required
def chats():
    """chats.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    me = current_user()
    # Mark any pending incoming DMs as delivered when the user opens the Chats list.
    # This enables 'delivered' ticks even before a chat is opened (seen).
    try:
        conn0 = db_connect()
        conn0.execute(
            "UPDATE dm_messages SET delivered_at=? WHERE recipient=? AND delivered_at IS NULL",
            (now_z(), me),
        )
        conn0.commit()
        conn0.close()
    except Exception:
        pass

    cards, online_count, offline_count = user_cards(g.scope, exclude=me)
    _dm_total, unread_map = dm_unread_counts(me)
    # Self-chat ("Saved messages") is always available and should be pinned at the top.
    # We expose `self_has_pic` so templates can show either the profile picture or a fallback avatar.
    try:
        ensure_profile_row(me)
        conn = db_connect()
        prow = conn.execute("SELECT pic_path FROM profiles WHERE username=?", (me,)).fetchone()
        conn.close()
        self_has_pic = bool(prow and prow["pic_path"] and os.path.exists(prow["pic_path"]))
    except Exception:
        self_has_pic = False
    return render_template(
        "chats.html",
        title="Chats",
        me=me,
        users=cards,
        self_has_pic=self_has_pic,
        unread_map=unread_map,
        online_count=online_count,
        offline_count=offline_count,
    )

@app.route("/chat/<username>")
@login_required
def chat_with(username: str):
    """chat_with.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    username: Parameter.

Returns:
    Varies.
"""
    me = current_user()
    username = username.strip()
    peer_display = username
    is_self_chat = (username == me)
    if is_self_chat:
        peer_display = "Saved messages"

    conn = db_connect()
    exists = conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone()
    if not exists:
        conn.close()
        flash("User not found.")
        return redirect(url_for("chats"))

    has_chat_pin = _chat_lock_exists(me, "dm", username)
    chat_unlocked = _chat_lock_is_unlocked(me, "dm", username)
    peer_online = (True if username == me else is_online(username, g.scope))
    if has_chat_pin and not chat_unlocked:
        conn.close()
        return render_template(
            "chat_locked.html",
            title=f"Chat {username}",
            me=me,
            peer=username,
            peer_display=peer_display,
            is_self_chat=is_self_chat,
            peer_online=peer_online,
        )

    try:
        conn.execute("""
            UPDATE dm_messages SET delivered_at=?
            WHERE sender=? AND recipient=? AND delivered_at IS NULL
        """, (now_z(), username, me))
        conn.execute("""
            UPDATE dm_messages SET read_at=?
            WHERE sender=? AND recipient=? AND read_at IS NULL
        """, (now_z(), username, me))
        conn.commit()

        rows = conn.execute("""
            SELECT id, sender, recipient, body_enc, created_at, delivered_at, read_at, has_voice, has_file, edited_at, deleted_at
            FROM dm_messages
            WHERE (sender=? AND recipient=?) OR (sender=? AND recipient=?)
            ORDER BY id ASC
            LIMIT 400
        """, (me, username, username, me)).fetchall()
    except sqlite3.OperationalError:
        try:
            conn.close()
        except Exception:
            pass
        try:
            db_init()
        except Exception:
            pass
        conn = db_connect()
        try:
            conn.execute("""
                UPDATE dm_messages SET delivered_at=?
                WHERE sender=? AND recipient=? AND delivered_at IS NULL
            """, (now_z(), username, me))
            conn.execute("""
                UPDATE dm_messages SET read_at=?
                WHERE sender=? AND recipient=? AND read_at IS NULL
            """, (now_z(), username, me))
            conn.commit()

            rows = conn.execute("""
                SELECT id, sender, recipient, body_enc, created_at, delivered_at, read_at, has_voice, has_file, edited_at, deleted_at
                FROM dm_messages
                WHERE (sender=? AND recipient=?) OR (sender=? AND recipient=?)
                ORDER BY id ASC
                LIMIT 400
            """, (me, username, username, me)).fetchall()
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            flash("Internal error opening chat. Please try again.")
            return redirect(url_for("chats"))

    msgs = []
    last_id = 0
    for r in rows:
        last_id = max(last_id, int(r["id"]))
        if r["has_voice"]:
            v = conn.execute("SELECT id, mime FROM dm_voice WHERE dm_id=? ORDER BY id DESC LIMIT 1", (r["id"],)).fetchone()
        else:
            v = None
        if r["has_file"]:
            f = conn.execute("SELECT id, filename, mime, size FROM dm_files WHERE dm_id=? ORDER BY id DESC LIMIT 1", (r["id"],)).fetchone()
        else:
            f = None
        try:
            body = aesgcm_decrypt_text(r["body_enc"])
        except Exception:
            body = "[decrypt failed]"
        msgs.append({
            "id": r["id"],
            "sender": r["sender"],
            "kind": ("deleted" if r["deleted_at"] else ("voice" if r["has_voice"] else ("file" if r["has_file"] else "text"))),
            "deleted": True if r["deleted_at"] else False,
            "body": ("[deleted]" if r["deleted_at"] else (body if (not r["has_voice"] and not r["has_file"]) else "")),
            "created_at_local": _local_time_str(r["created_at"]),
            "created_at_utc": r["created_at"],
            "delivered_at_local": _local_time_str(r["delivered_at"]) if (r["sender"] == me and r["delivered_at"]) else None,
            "delivered_at_utc": (r["delivered_at"] if (r["sender"] == me and r["delivered_at"]) else None),
            "delivered_at_local": _local_time_str(r["delivered_at"]) if (r["sender"] == me and r["delivered_at"]) else None,
            "delivered_at_utc": (r["delivered_at"] if (r["sender"] == me and r["delivered_at"]) else None),
            "read_at_local": _local_time_str(r["read_at"]) if r["sender"] == me else None,
            "read_at_utc": r["read_at"] if r["sender"] == me else None,
            "edited_at_local": _local_time_str(r["edited_at"]) if r["edited_at"] else None,
            "edited_at_utc": r["edited_at"] if r["edited_at"] else None,
            "voice_id": v["id"] if v else None,
            "voice_mime": v["mime"] if v else "audio/webm",
            "file_id": f["id"] if f else None,
            "file_name": f["filename"] if f else None,
            "file_mime": f["mime"] if f else None,
            "file_size_h": human_size(int(f["size"])) if (f and f["size"] is not None) else "",
            "file_is_image": True if (f and (f["mime"] or "").startswith("image/")) else False,
            "file_is_video": True if (f and (f["mime"] or "").startswith("video/")) else False,
            "file_is_audio": True if (f and (f["mime"] or "").startswith("audio/")) else False
        })
    conn.close()

    return render_template(
        "chat_page.html",
        title=f"Chat {username}",
        me=me,
        peer=username,
        peer_display=peer_display,
        is_self_chat=is_self_chat,
        peer_online=peer_online,
        messages=msgs,
        last_id=last_id,
        has_chat_pin=has_chat_pin,
    )


def _dm_build_message_dict(conn, r, me: str) -> Dict[str, Any]:
    """Build a DM message view dict (same logic as chat_with) for one dm_messages row."""
    if r["has_voice"]:
        v = conn.execute("SELECT id, mime FROM dm_voice WHERE dm_id=? ORDER BY id DESC LIMIT 1", (r["id"],)).fetchone()
    else:
        v = None
    if r["has_file"]:
        f = conn.execute("SELECT id, filename, mime, size FROM dm_files WHERE dm_id=? ORDER BY id DESC LIMIT 1", (r["id"],)).fetchone()
    else:
        f = None
    try:
        body = aesgcm_decrypt_text(r["body_enc"])
    except Exception:
        body = "[decrypt failed]"
    msg = {
        "id": r["id"],
        "sender": r["sender"],
        "kind": ("deleted" if r["deleted_at"] else ("voice" if r["has_voice"] else ("file" if r["has_file"] else "text"))),
        "deleted": True if r["deleted_at"] else False,
        "body": ("[deleted]" if r["deleted_at"] else (body if (not r["has_voice"] and not r["has_file"]) else "")),
        "created_at_local": _local_time_str(r["created_at"]),
        "created_at_utc": r["created_at"],
        "read_at_local": _local_time_str(r["read_at"]) if r["sender"] == me else None,
        "read_at_utc": r["read_at"] if r["sender"] == me else None,
        "edited_at_local": _local_time_str(r["edited_at"]) if r["edited_at"] else None,
        "voice_id": v["id"] if v else None,
        "voice_mime": v["mime"] if v else "audio/webm",
        "file_id": f["id"] if f else None,
        "file_name": f["filename"] if f else None,
        "file_mime": f["mime"] if f else None,
        "file_size_h": human_size(int(f["size"])) if (f and f["size"] is not None) else "",
        "file_is_image": True if (f and (f["mime"] or "").startswith("image/")) else False,
        "file_is_video": True if (f and (f["mime"] or "").startswith("video/")) else False,
        "file_is_audio": True if (f and (f["mime"] or "").startswith("audio/")) else False
    }
    return msg



_DM_ROW_TEMPLATE = r"""
<div class="msg-row {{ 'me' if m.sender==me else 'them' }}">
  <div class="bubble {{ 'me' if m.sender==me else 'them' }}" data-mid="{{ m.id }}" data-kind="{{ m.kind }}" data-sender="{{ m.sender }}">
    {% if m.kind == 'text' %}
      <span class="msg-text">{{ m.body }}</span>
      {% if m.edited_at_local %}<span class="small-muted"> (edited)</span>{% endif %}
    {% elif m.kind == 'voice' %}
      <audio controls preload="metadata">
        <source src="{{ url_for('dm_voice_stream', vid=m.voice_id) }}" type="{{ m.voice_mime }}">
      </audio>
    {% elif m.kind == 'file' %}
      {% if m.file_is_image %}
        <img src="{{ url_for('dm_file_stream', fid=m.file_id) }}" alt="{{ m.file_name }}"/>
      {% elif m.file_is_video %}
        <video controls playsinline preload="metadata">
          <source src="{{ url_for('dm_file_stream', fid=m.file_id) }}" type="{{ m.file_mime }}">
        </video>
      {% elif m.file_is_audio %}
        <audio controls preload="metadata">
          <source src="{{ url_for('dm_file_stream', fid=m.file_id) }}" type="{{ m.file_mime }}">
        </audio>
      {% else %}
        <a class="file-chip" href="{{ url_for('dm_file_download', fid=m.file_id) }}">📎 {{ m.file_name }}</a>
        <div class="small-muted mt-1">{{ m.file_size_h }}</div>
      {% endif %}
    {% elif m.kind == 'deleted' %}
      <span class="small-muted">Deleted</span>
    {% else %}
      <span class="msg-text">{{ m.body }}</span>
    {% endif %}
  </div>
  <div class="msg-meta">
    <span class="ts" data-utc="{{ m.created_at_utc }}">{{ m.created_at_local }}</span>{% if m.deleted %} • deleted{% endif %}
    {% if m.sender==me %}
      {% if m.read_at_local %} • seen <span class="ts" data-utc="{{ m.read_at_utc }}">{{ m.read_at_local }}</span>{% else %} • sent{% endif %}
    {% endif %}
  </div>
</div>
"""

_GROUP_ROW_TEMPLATE = r"""
<div class="mb-2" data-gmid="{{ m.id }}">
  <div class="bubble {{ 'me' if m.sender==me else 'them' }}">
    {% if m.kind == "text" %}
      <div class="small-muted mb-1">{{ m.sender }}</div>
      {{ m.body }}
    {% else %}
      <div class="small-muted mb-1">{{ m.sender }} • Voice</div>
      <audio controls preload="metadata" style="width:100%">
        <source src="{{ url_for('group_voice_stream', vid=m.voice_id) }}" type="{{ m.voice_mime }}">
      </audio>
    {% endif %}
  </div>
  <div class="msg-meta {{ 'text-end' if m.sender==me else '' }}"><span class="ts" data-utc="{{ m.created_at_utc }}">{{ m.created_at_local }}</span></div>
</div>
"""


def _render_dm_row_html(m: Dict[str, Any], me: str) -> str:
    """Render one DM message row to HTML for AJAX updates."""
    return render_template_string(_DM_ROW_TEMPLATE, m=m, me=me)


@app.route("/chat/<username>/send", methods=["POST"])
@login_required
def dm_send(username: str):
    """Send a DM message (text, file, GIF, and/or voice).

    Important stability notes:
      - The message and its attachments are committed atomically (single DB transaction),
        so other clients never see a "blank" placeholder that requires refresh.
      - AJAX returns a fully-rendered row for immediate DOM append (no page reload).
    """
    me = current_user()
    username = (username or "").strip()

    is_ajax = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in (request.headers.get("Accept", ""))
    )

    body = (request.form.get("body") or "").strip()
    voice = request.files.get("voice")
    upfile = request.files.get("file")
    gif = request.files.get("gif")
    gif_url = (request.form.get("gif_url") or "").strip()

    # Enforce per-attachment size limits (33MB) to keep chats fast/stable.
    if voice and getattr(voice, "filename", ""):
        vsz = _filestorage_size(voice)
        if vsz is not None and vsz > CHAT_MAX_BYTES:
            if is_ajax:
                return jsonify(ok=False, error="Voice message too large (max 33MB)."), 413
            flash("Voice message too large (max 33MB).")
            return redirect(url_for("chat_with", username=username))
    if upfile and getattr(upfile, "filename", ""):
        fsz = _filestorage_size(upfile)
        if fsz is not None and fsz > CHAT_MAX_BYTES:
            if is_ajax:
                return jsonify(ok=False, error="File too large (max 33MB)."), 413
            flash("File too large (max 33MB).")
            return redirect(url_for("chat_with", username=username))
    if gif and getattr(gif, "filename", ""):
        gsz = _filestorage_size(gif)
        if gsz is not None and gsz > CHAT_MAX_BYTES:
            if is_ajax:
                return jsonify(ok=False, error="GIF too large (max 33MB)."), 413
            flash("GIF too large (max 33MB).")
            return redirect(url_for("chat_with", username=username))

    # Prefer an explicit file; otherwise accept GIF as a file attachment.
    chosen_file = (
        upfile if (upfile and getattr(upfile, "filename", "")) else (gif if (gif and getattr(gif, "filename", "")) else None)
    )

    if voice and getattr(voice, "filename", ""):
        try:
            _validate_chat_voice_upload(voice)
        except ValueError as ve:
            msg = "Unsupported voice file type."
            if str(ve) == "forbidden_type":
                msg = "Forbidden file type."
            if is_ajax:
                return jsonify(ok=False, error=msg), 400
            flash(msg)
            return redirect(url_for("chat_with", username=username))
    if chosen_file and getattr(chosen_file, "filename", ""):
        try:
            _validate_chat_file_upload(chosen_file)
        except ValueError as ve:
            msg = "Unsupported file type."
            if str(ve) == "forbidden_type":
                msg = "Forbidden file type."
            if is_ajax:
                return jsonify(ok=False, error=msg), 400
            flash(msg)
            return redirect(url_for("chat_with", username=username))

    has_voice = bool(voice and getattr(voice, "filename", ""))
    has_file = bool(chosen_file and getattr(chosen_file, "filename", ""))
    has_gif_url = bool(gif_url)

    if (not body) and (not has_voice) and (not has_file) and (not has_gif_url):
        if is_ajax:
            return jsonify(ok=False, error="Write a message or attach voice/file."), 400
        flash("Write a message or attach voice/file.")
        return redirect(url_for("chat_with", username=username))

    conn = db_connect()
    saved_paths = []
    try:
        exists = conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone()
        if not exists:
            raise ValueError("User not found")

        cur = conn.cursor()
        cur.execute(
            "INSERT INTO dm_messages(sender, recipient, body_enc, created_at, delivered_at, read_at, has_voice, has_file) VALUES(?,?,?,?,NULL,NULL,?,?)",
            (
                me,
                username,
                aesgcm_encrypt_text(body or ""),
                now_z(),
                1 if has_voice else 0,
                1 if (has_file or has_gif_url) else 0,
            ),
        )
        dm_id = cur.lastrowid

        # Store attachments within the SAME transaction so polling clients never see a placeholder.
        if has_voice:
            _, _, sp = _dm_store_voice_tx(conn, dm_id, voice)
            saved_paths.append(sp)

        if has_file:
            info = _dm_store_file_tx(conn, dm_id, chosen_file)
            saved_paths.append(info["stored_path"])

        if (not has_file) and has_gif_url:
            info = _dm_store_remote_gif_tx(conn, dm_id, gif_url)
            saved_paths.append(info["stored_path"])

        conn.commit()

        if is_ajax:
            r = conn.execute(
                "SELECT id, sender, recipient, body_enc, created_at, delivered_at, read_at, has_voice, has_file, edited_at, deleted_at FROM dm_messages WHERE id=?",
                (dm_id,),
            ).fetchone()
            if r is None:
                return jsonify(ok=False, error="Message not found"), 404
            msg = _dm_build_message_dict(conn, r, me)
            html_row = _render_dm_row_html(msg, me)
            return jsonify(ok=True, id=dm_id, html=html_row)

        return redirect(url_for("chat_with", username=username))

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass

        # Remove any files written before the failure.
        for sp in saved_paths:
            try:
                if sp and os.path.exists(sp):
                    os.remove(sp)
            except Exception:
                pass

        log.exception("dm_send failed: %s", e)
        if is_ajax:
            return jsonify(ok=False, error="Send failed"), 500
        flash("Send failed.")
        return redirect(url_for("chat_with", username=username))
    finally:
        try:
            conn.close()
        except Exception:
            pass

@app.route("/dm/voice/<int:vid>")
@login_required
def dm_voice_stream(vid: int):
    """Stream a DM voice message."""
    me = current_user()
    conn = db_connect()
    row = conn.execute("""
        SELECT v.id, v.mime, v.stored_path, m.sender, m.recipient
        FROM dm_voice v
        JOIN dm_messages m ON m.id=v.dm_id
        WHERE v.id=?
    """, (vid,)).fetchone()
    conn.close()
    if not row or (me != row["sender"] and me != row["recipient"]):
        abort(404)
    peer = row["recipient"] if row["sender"] == me else row["sender"]
    if not _chat_lock_is_unlocked(me, "dm", peer):
        return redirect(url_for("chat_with", username=peer))
    sp = row["stored_path"]
    if not sp or not os.path.exists(sp):
        abort(404)

    mime = row["mime"] or "audio/webm"
    try:
        if is_encrypted_file(sp):
            gen = aesgcm_decrypt_generator(sp)
            resp = Response(gen, mimetype=mime)
        else:
            from flask import send_file
            resp = send_file(sp, mimetype=mime, as_attachment=False, conditional=True, max_age=0)
    except Exception:
        abort(404)

    resp.headers["Cache-Control"] = "no-store"
    return resp


# API: typeahead

def _user_match_score(q: str, u: str) -> int:
    """_user_match_score.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    q: Parameter.
    u: Parameter.

Returns:
    Varies.
"""
    q = q.lower()
    u2 = u.lower()
    if u2.startswith(q):
        return 0
    if q in u2:
        return 1
    return 2

@app.route("/api/users")
@login_required
def api_users():
    """api_users.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    me = current_user()
    q = (request.args.get("q") or "").strip()
    cards, _, _ = user_cards(g.scope, exclude=me)

    if q:
        ql = q.lower()
        # Prefer username matches, then nickname matches
        def score(c):
            """score.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    c: Parameter.

Returns:
    Varies.
"""
            u = c["username"].lower()
            n = str(c["nickname"]).lower()
            # smaller is better
            s1 = _user_match_score(q, c["username"])
            s2 = 0 if ql in u else 3
            s3 = 1 if ql in n else 4
            return (s1, s2, s3, len(u), u)
        cards.sort(key=score)
        cards = [c for c in cards if (ql in c["username"].lower() or ql in str(c["nickname"]).lower())][:12]
    else:
        cards = cards[:12]

    try:
        story_users = _story_active_usernames()
    except Exception:
        story_users = set()
    for c in cards:
        try:
            c["has_story"] = (c.get("username") in story_users)
        except Exception:
            c["has_story"] = False

    return jsonify({"users": cards})

@app.route("/api/ping", methods=["POST"])
@login_required
def api_ping():
    """api_ping.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    mark_online(current_user(), g.scope)
    return jsonify({"ok": True})

@app.route("/api/dm/<peer>/since")
@login_required
def api_dm_since(peer: str):
    """api_dm_since.

Chat/group feature helper or route handler.

This docstring was expanded to make future maintenance easier.

Args:
    peer: Parameter.

Returns:
    Varies.
"""
    me = current_user()
    peer = peer.strip()
    if not _chat_lock_is_unlocked(me, "dm", peer):
        return jsonify(ok=False, locked=True, error="PIN required"), 423
    try:
        since_id = int(request.args.get("id") or 0)
    except Exception:
        since_id = 0

    conn = db_connect()
    # Mark newly received messages as delivered (recipient fetched them).
    try:
        conn.execute(
            "UPDATE dm_messages SET delivered_at=? WHERE sender=? AND recipient=? AND delivered_at IS NULL",
            (now_z(), peer, me),
        )
        conn.commit()
    except Exception:
        pass

    # Mark as read when the chat tab is open (this endpoint is called by the active chat view).
    try:
        conn.execute(
            "UPDATE dm_messages SET read_at=? WHERE sender=? AND recipient=? AND read_at IS NULL",
            (now_z(), peer, me),
        )
        conn.commit()
    except Exception:
        pass


    rows = conn.execute("""
        SELECT id, sender, recipient, body_enc, created_at, delivered_at, read_at, has_voice, has_file, edited_at, deleted_at
        FROM dm_messages
        WHERE id > ? AND ((sender=? AND recipient=?) OR (sender=? AND recipient=?))
        ORDER BY id ASC
        LIMIT 120
    """, (since_id, me, peer, peer, me)).fetchall()

    out = []
    want_html = (request.args.get('html') == '1')
    for r in rows:
        if r["has_voice"]:
            v = conn.execute("SELECT id, mime FROM dm_voice WHERE dm_id=? ORDER BY id DESC LIMIT 1", (r["id"],)).fetchone()
        else:
            v = None
        if r["has_file"]:
            f = conn.execute("SELECT id, filename, mime, size FROM dm_files WHERE dm_id=? ORDER BY id DESC LIMIT 1", (r["id"],)).fetchone()
        else:
            f = None
        try:
            body = aesgcm_decrypt_text(r["body_enc"])
        except Exception:
            body = "[decrypt failed]"
        out.append({
            "id": r["id"],
            "sender": r["sender"],
            "kind": ("deleted" if r["deleted_at"] else ("voice" if r["has_voice"] else ("file" if r["has_file"] else "text"))),
            "deleted": True if r["deleted_at"] else False,
            "body": ("[deleted]" if r["deleted_at"] else (body if (not r["has_voice"] and not r["has_file"]) else "")),
            "created_at_local": _local_time_str(r["created_at"]),
            "created_at_utc": r["created_at"],
            "read_at_local": _local_time_str(r["read_at"]) if r["sender"] == me else None,
            "read_at_utc": r["read_at"] if r["sender"] == me else None,
            "edited_at_local": _local_time_str(r["edited_at"]) if r["edited_at"] else None,
            "voice_id": v["id"] if v else None,
            "voice_mime": v["mime"] if v else "audio/webm",
            "file_id": f["id"] if f else None,
            "file_name": f["filename"] if f else None,
            "file_mime": f["mime"] if f else None,
            "file_size_h": human_size(int(f["size"])) if (f and f["size"] is not None) else "",
            "file_is_image": True if (f and (f["mime"] or "").startswith("image/")) else False,
            "file_is_video": True if (f and (f["mime"] or "").startswith("video/")) else False,
            "file_is_audio": True if (f and (f["mime"] or "").startswith("audio/")) else False
        })
        if want_html:
            try:
                out[-1]['html'] = _render_dm_row_html(out[-1], me)
            except Exception:
                pass
    # Status updates for delivery/seen ticks (for messages I sent to this peer).
    status_since = (request.args.get("status_since") or "").strip()
    if not status_since:
        status_since = "1970-01-01T00:00:00Z"
    updates = []
    try:
        urows = conn.execute(
            """
            SELECT id, delivered_at, read_at
            FROM dm_messages
            WHERE sender=? AND recipient=? AND (
              (delivered_at IS NOT NULL AND delivered_at > ?) OR
              (read_at IS NOT NULL AND read_at > ?)
            )
            ORDER BY id DESC
            LIMIT 120
            """,
            (me, peer, status_since, status_since),
        ).fetchall()
        for ur in urows:
            updates.append({
                "id": int(ur["id"]),
                "delivered_at_local": _local_time_str(ur["delivered_at"]) if ur["delivered_at"] else None,
                "delivered_at_utc": ur["delivered_at"],
                "read_at_local": _local_time_str(ur["read_at"]) if ur["read_at"] else None,
                "read_at_utc": ur["read_at"],
            })
    except Exception:
        pass

    conn.close()
    return jsonify({"ok": True, "messages": out, "status_updates": updates, "server_now": now_z()})


@app.route("/api/group/<int:gid>/since")
@login_required
def api_group_since(gid: int):
    """Return new group messages since a given id (AJAX polling).

    This endpoint lets group chats update in-place (no full page refresh)
    when messages are sent/received.

    Query params:
        id: Last seen group message id (integer).
        html: If '1', include pre-rendered HTML rows for easy DOM append.

    Returns:
        JSON: {ok: true, messages: [...]} where each message may include html.
    """
    me = current_user()
    # Only members can poll a group's messages
    if not group_role(gid, me):
        abort(403)

    try:
        since_id = int(request.args.get("id") or 0)
    except Exception:
        since_id = 0

    want_html = (request.args.get("html") == "1")

    conn = db_connect()
    rows = conn.execute(
        """
        SELECT id, sender, body_enc, created_at
        FROM group_messages
        WHERE group_id=? AND id > ?
        ORDER BY id ASC
        LIMIT 120
        """,
        (gid, since_id),
    ).fetchall()

    out = []
    for r in rows:
        v = conn.execute(
            "SELECT id, mime FROM group_voice WHERE gm_id=? ORDER BY id DESC LIMIT 1",
            (r["id"],),
        ).fetchone()
        has_voice = bool(v)
        try:
            body_txt = aesgcm_decrypt_text(r["body_enc"])
        except Exception:
            body_txt = "[decrypt failed]"

        m = {
            "id": r["id"],
            "sender": r["sender"],
            "kind": "voice" if has_voice else "text",
            "body": body_txt if not has_voice else "",
            "created_at_local": _local_time_str(r["created_at"]),
            "created_at_utc": r["created_at"],
            "voice_id": v["id"] if v else None,
            "voice_mime": v["mime"] if v else "audio/webm",
        }

        item = dict(m)
        if want_html:
            try:
                item["html"] = render_template_string(_GROUP_ROW_TEMPLATE, m=m, me=me)
            except Exception:
                item["html"] = ""

        out.append(item)

    conn.close()
    return jsonify(ok=True, messages=out)

@app.route("/api/dm/message/<int:mid>/edit", methods=["POST"])
@login_required
def api_dm_edit(mid: int):
    """api_dm_edit.

Chat/group feature helper or route handler.

This docstring was expanded to make future maintenance easier.

Args:
    mid: Parameter.

Returns:
    Varies.
"""
    me = current_user()
    data = request.get_json(silent=True) or {}
    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"ok": False, "error": "Empty message"}), 400

    conn = db_connect()
    r = conn.execute("SELECT sender, recipient, has_voice, has_file, deleted_at FROM dm_messages WHERE id=?", (mid,)).fetchone()
    if not r or r["sender"] != me:
        conn.close()
        return jsonify({"ok": False, "error": "Not allowed"}), 403
    if r["deleted_at"]:
        conn.close()
        return jsonify({"ok": False, "error": "Message deleted"}), 400
    if r["has_voice"] or r["has_file"]:
        conn.close()
        return jsonify({"ok": False, "error": "Only text messages can be edited"}), 400

    conn.execute("UPDATE dm_messages SET body_enc=?, edited_at=? WHERE id=?", (aesgcm_encrypt_text(body), now_z(), mid))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/dm/message/<int:mid>/delete", methods=["POST"])
@login_required
def api_dm_delete(mid: int):
    """api_dm_delete.

Chat/group feature helper or route handler.

This docstring was expanded to make future maintenance easier.

Args:
    mid: Parameter.

Returns:
    Varies.
"""
    me = current_user()
    conn = db_connect()
    r = conn.execute("SELECT sender, recipient, has_voice, has_file FROM dm_messages WHERE id=?", (mid,)).fetchone()
    if not r or r["sender"] != me:
        conn.close()
        return jsonify({"ok": False, "error": "Not allowed"}), 403

    # Remove attachments from disk + tables
    if r["has_voice"]:
        rows = conn.execute("SELECT id, stored_path FROM dm_voice WHERE dm_id=?", (mid,)).fetchall()
        for vr in rows:
            try:
                if vr["stored_path"] and os.path.exists(vr["stored_path"]):
                    os.remove(vr["stored_path"])
            except Exception:
                pass
        conn.execute("DELETE FROM dm_voice WHERE dm_id=?", (mid,))
    if r["has_file"]:
        rows = conn.execute("SELECT id, stored_path FROM dm_files WHERE dm_id=?", (mid,)).fetchall()
        for fr in rows:
            try:
                if fr["stored_path"] and os.path.exists(fr["stored_path"]):
                    os.remove(fr["stored_path"])
            except Exception:
                pass
        conn.execute("DELETE FROM dm_files WHERE dm_id=?", (mid,))

    conn.execute(
        "UPDATE dm_messages SET body_enc=?, has_voice=0, has_file=0, deleted_at=? WHERE id=?",
        (aesgcm_encrypt_text(""), now_z(), mid)
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

# ---------------------------
# Video call signaling (WebRTC)
# ---------------------------

@app.route("/api/call/start/<peer>", methods=["POST"])
@login_required
def api_call_start(peer: str):
    """api_call_start.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    peer: Parameter.

Returns:
    Varies.
"""
    if not ENABLE_CALLS:
        return jsonify({"ok": False, "error": "Calls disabled"}), 404
    me = current_user()
    peer = peer.strip()
    if peer == me:
        return jsonify({"ok": False, "error": "Invalid peer"}), 400
    conn = db_connect()
    exists = conn.execute("SELECT 1 FROM users WHERE username=?", (peer,)).fetchone()
    if not exists:
        conn.close()
        return jsonify({"ok": False, "error": "User not found"}), 404

    # Reuse any active call between the two users
    row = conn.execute("""
        SELECT id FROM dm_calls
        WHERE status='active' AND ((a=? AND b=?) OR (a=? AND b=?))
        ORDER BY id DESC LIMIT 1
    """, (me, peer, peer, me)).fetchone()
    if row:
        call_id = row["id"]
    else:
        cur = conn.cursor()
        cur.execute("INSERT INTO dm_calls(a,b,status,created_at) VALUES(?,?, 'active', ?)", (me, peer, now_z()))
        call_id = cur.lastrowid
        conn.commit()
    conn.close()
    return jsonify({"ok": True, "call_id": call_id})

@app.route("/api/call/peek/<peer>")
@login_required
def api_call_peek(peer: str):
    """If there is an active call between me and peer, return call_id (used to start polling)."""
    if not ENABLE_CALLS:
        return jsonify({"ok": False, "error": "Calls disabled"}), 404
    me = current_user()
    peer = peer.strip()
    conn = db_connect()
    row = conn.execute("""
        SELECT id FROM dm_calls
        WHERE status='active' AND ((a=? AND b=?) OR (a=? AND b=?))
        ORDER BY id DESC LIMIT 1
    """, (me, peer, peer, me)).fetchone()
    conn.close()
    if not row:
        return jsonify({"ok": True, "call_id": None})
    return jsonify({"ok": True, "call_id": row["id"], "since": 0})

@app.route("/api/call/<int:call_id>/signal", methods=["POST"])
@login_required
def api_call_signal(call_id: int):
    """api_call_signal.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    call_id: Parameter.

Returns:
    Varies.
"""
    if not ENABLE_CALLS:
        return jsonify({"ok": False, "error": "Calls disabled"}), 404
    me = current_user()
    data = request.get_json(silent=True) or {}
    kind = (data.get("kind") or "").strip()
    payload = data.get("payload")
    if kind not in ("ring","offer","answer","ice","hangup"):
        return jsonify({"ok": False, "error": "Bad signal"}), 400

    conn = db_connect()
    call = conn.execute("SELECT a,b,status FROM dm_calls WHERE id=?", (call_id,)).fetchone()
    if not call or call["status"] != "active" or (me != call["a"] and me != call["b"]):
        conn.close()
        return jsonify({"ok": False, "error": "Not allowed"}), 403

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO dm_call_signals(call_id, sender, kind, payload, created_at) VALUES(?,?,?,?,?)",
        (call_id, me, kind, payload if isinstance(payload, str) else json.dumps(payload or {}), now_z())
    )
    sid = cur.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "id": sid})

@app.route("/api/call/<int:call_id>/poll")
@login_required
def api_call_poll(call_id: int):
    """api_call_poll.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    call_id: Parameter.

Returns:
    Varies.
"""
    if not ENABLE_CALLS:
        return jsonify({"ok": False, "error": "Calls disabled"}), 404
    me = current_user()
    try:
        since = int(request.args.get("since") or 0)
    except Exception:
        since = 0
    conn = db_connect()
    call = conn.execute("SELECT a,b,status FROM dm_calls WHERE id=?", (call_id,)).fetchone()
    if not call or call["status"] != "active" or (me != call["a"] and me != call["b"]):
        conn.close()
        return jsonify({"ok": False, "error": "Not allowed"}), 403

    rows = conn.execute("""
        SELECT id, sender, kind, payload, created_at
        FROM dm_call_signals
        WHERE call_id=? AND id > ?
        ORDER BY id ASC
        LIMIT 120
    """, (call_id, since)).fetchall()
    conn.close()
    return jsonify({"ok": True, "items": [dict(r) for r in rows]})

@app.route("/api/call/<int:call_id>/end", methods=["POST"])
@login_required
def api_call_end(call_id: int):
    """api_call_end.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    call_id: Parameter.

Returns:
    Varies.
"""
    if not ENABLE_CALLS:
        return jsonify({"ok": False, "error": "Calls disabled"}), 404
    me = current_user()
    conn = db_connect()
    call = conn.execute("SELECT a,b,status FROM dm_calls WHERE id=?", (call_id,)).fetchone()
    if not call or call["status"] != "active" or (me != call["a"] and me != call["b"]):
        conn.close()
        return jsonify({"ok": False, "error": "Not allowed"}), 403
    conn.execute("UPDATE dm_calls SET status='ended', ended_at=? WHERE id=?", (now_z(), call_id))
    conn.execute("INSERT INTO dm_call_signals(call_id, sender, kind, payload, created_at) VALUES(?,?,?,?,?)",
                 (call_id, me, "hangup", "{}", now_z()))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})




# ---------------------------
# Live location sharing
# ---------------------------

@app.route("/locations")
@login_required
def live_locations():
    """live_locations.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    me = current_user()
    return render_template("live_locations.html", title="Live Locations", me=me)

@app.route("/api/location/update", methods=["POST"])
@login_required
def api_location_update():
    """api_location_update.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    me = current_user()
    data = request.get_json(silent=True) or {}
    try:
        lat = float(data.get("lat"))
        lon = float(data.get("lon"))
    except Exception:
        return jsonify({"ok": False, "error": "Invalid coordinates"}), 400
    try:
        acc = float(data.get("accuracy")) if data.get("accuracy") is not None else None
    except Exception:
        acc = None
    sharing = 1 if bool(data.get("sharing")) else 0
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return jsonify({"ok": False, "error": "Invalid coordinates"}), 400

    conn = db_connect()
    conn.execute("""
        INSERT INTO user_locations(username, lat, lon, accuracy, sharing, updated_at)
        VALUES(?,?,?,?,?,?)
        ON CONFLICT(username) DO UPDATE SET
            lat=excluded.lat, lon=excluded.lon, accuracy=excluded.accuracy,
            sharing=excluded.sharing, updated_at=excluded.updated_at
    """, (me, lat, lon, acc, sharing, now_z()))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/location/stop", methods=["POST"])
@login_required
def api_location_stop():
    """api_location_stop.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    me = current_user()
    conn = db_connect()
    conn.execute("UPDATE user_locations SET sharing=0, updated_at=? WHERE username=?", (now_z(), me))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/locations")
@login_required
def api_locations():
    """api_locations.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    conn = db_connect()
    rows = conn.execute("""
        SELECT l.username, l.lat, l.lon, l.accuracy, l.updated_at, p.nickname_enc
        FROM user_locations l
        LEFT JOIN profiles p ON p.username=l.username
        WHERE l.sharing=1 AND l.lat IS NOT NULL AND l.lon IS NOT NULL
        ORDER BY l.updated_at DESC
        LIMIT 200
    """).fetchall()
    items = []
    for r in rows:
        nick = r["username"]
        try:
            if r["nickname_enc"]:
                nick = aesgcm_decrypt_text(r["nickname_enc"]) or nick
        except Exception:
            nick = r["username"]
        items.append({
            "username": r["username"],
            "nickname": nick,
            "lat": float(r["lat"]),
            "lon": float(r["lon"]),
            "accuracy": float(r["accuracy"]) if r["accuracy"] is not None else None,
            "updated_at": r["updated_at"]
        })
    conn.close()
    return jsonify({"ok": True, "items": items})


# ---------------------------
# Groups (chat + admins)
# ---------------------------

def all_usernames() -> List[str]:
    """all_usernames.

Internal helper function.

This docstring was added automatically to improve maintainability.

Returns:
    Varies.
"""
    conn = db_connect()
    rows = conn.execute("SELECT username FROM users ORDER BY username COLLATE NOCASE").fetchall()
    conn.close()
    return [r["username"] for r in rows]

def group_role(gid: int, username: str) -> Optional[str]:
    """group_role.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    gid: Parameter.
    username: Parameter.

Returns:
    Varies.
"""
    conn = db_connect()
    row = conn.execute("SELECT role FROM group_members WHERE group_id=? AND username=?", (gid, username)).fetchone()
    conn.close()
    return row["role"] if row else None

@app.route("/groups")
@login_required
def groups():
    """List groups for the current user (with auto-heal schema)."""
    me = current_user()
    # Ensure group tables exist even on upgraded databases
    try:
        db_init()
    except Exception:
        pass

    def _fetch_rows():
        conn = db_connect()
        try:
            rows = conn.execute(
                """
                SELECT g.id, g.name, g.owner, g.created_at, m.role AS my_role
                FROM groups g
                JOIN group_members m ON m.group_id=g.id
                WHERE m.username=?
                ORDER BY g.id DESC
                """,
                (me,),
            ).fetchall()
            return rows
        finally:
            conn.close()

    try:
        rows = _fetch_rows()
    except Exception:
        # One more attempt after ensuring schema (covers 'no such table' cases)
        try:
            db_init()
        except Exception:
            pass
        rows = _fetch_rows()

    class Obj:
        def __init__(self, r):
            self.__dict__.update(dict(r))

    return render_template("groups.html", title="Groups", gs=[Obj(r) for r in rows])

@app.route("/groups/create", methods=["POST"])
@login_required
def group_create():
    """group_create.

Chat/group feature helper or route handler.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    me = current_user()
    name = (request.form.get("name") or "").strip()[:64]
    members_raw = (request.form.get("members") or "").strip()
    if not name:
        flash("Group name required.")
        return redirect(url_for("groups"))

    members = set()
    if members_raw:
        for part in members_raw.split(","):
            part = part.strip()
            if part:
                members.add(part)
    members.add(me)

    valid = set(all_usernames())
    members = [m for m in members if m in valid]

    conn = db_connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO groups(name, owner, created_at) VALUES(?,?,?)", (name, me, now_z()))
    gid = cur.lastrowid
    for m in members:
        role = "owner" if m == me else "member"
        cur.execute("INSERT OR IGNORE INTO group_members(group_id, username, role, added_at) VALUES(?,?,?,?)",
                    (gid, m, role, now_z()))
    conn.commit()
    conn.close()
    flash("Group created.")
    return redirect(url_for("group_chat", gid=gid))

@app.route("/groups/<int:gid>/delete", methods=["POST"])
@login_required
def group_delete(gid: int):
    """group_delete.

Chat/group feature helper or route handler.

This docstring was expanded to make future maintenance easier.

Args:
    gid: Parameter.

Returns:
    Varies.
"""
    me = current_user()
    if group_role(gid, me) != "owner":
        abort(403)
    conn = db_connect()
    conn.execute("DELETE FROM groups WHERE id=?", (gid,))
    conn.commit()
    conn.close()
    flash("Group deleted.")
    return redirect(url_for("groups"))

@app.route("/groups/<int:gid>/leave", methods=["POST"])
@login_required
def group_leave(gid: int):
    """group_leave.

Chat/group feature helper or route handler.

This docstring was expanded to make future maintenance easier.

Args:
    gid: Parameter.

Returns:
    Varies.
"""
    me = current_user()
    if group_role(gid, me) == "owner":
        flash("Owner cannot leave. Delete the group instead.")
        return redirect(url_for("groups"))
    conn = db_connect()
    conn.execute("DELETE FROM group_members WHERE group_id=? AND username=?", (gid, me))
    conn.commit()
    conn.close()
    flash("Left group.")
    return redirect(url_for("groups"))

@app.route("/groups/<int:gid>/members/add", methods=["POST"])
@login_required
def group_add_member(gid: int):
    """group_add_member.

Chat/group feature helper or route handler.

This docstring was expanded to make future maintenance easier.

Args:
    gid: Parameter.

Returns:
    Varies.
"""
    me = current_user()
    role = group_role(gid, me)
    if role not in ("owner", "admin"):
        abort(403)
    username = (request.form.get("username") or "").strip()
    if not username:
        return redirect(url_for("group_chat", gid=gid))
    conn = db_connect()
    exists = conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone()
    if not exists:
        conn.close()
        flash("User does not exist.")
        return redirect(url_for("group_chat", gid=gid))
    conn.execute("INSERT OR IGNORE INTO group_members(group_id, username, role, added_at) VALUES(?,?,?,?)",
                 (gid, username, "member", now_z()))
    conn.commit()
    conn.close()
    flash("Member added.")
    return redirect(url_for("group_chat", gid=gid))

@app.route("/groups/<int:gid>/members/remove", methods=["POST"])
@login_required
def group_remove_member(gid: int):
    """group_remove_member.

Chat/group feature helper or route handler.

This docstring was expanded to make future maintenance easier.

Args:
    gid: Parameter.

Returns:
    Varies.
"""
    me = current_user()
    role = group_role(gid, me)
    if role not in ("owner", "admin"):
        abort(403)
    username = (request.form.get("username") or "").strip()
    if not username or username == me:
        return redirect(url_for("group_chat", gid=gid))
    # admins cannot remove owner
    if group_role(gid, username) == "owner":
        flash("Cannot remove owner.")
        return redirect(url_for("group_chat", gid=gid))
    conn = db_connect()
    conn.execute("DELETE FROM group_members WHERE group_id=? AND username=?", (gid, username))
    conn.commit()
    conn.close()
    flash("Member removed.")
    return redirect(url_for("group_chat", gid=gid))

@app.route("/groups/<int:gid>/admins/promote", methods=["POST"])
@login_required
def group_promote_admin(gid: int):
    """group_promote_admin.

Admin-only route handler.

This docstring was expanded to make future maintenance easier.

Args:
    gid: Parameter.

Returns:
    Varies.
"""
    me = current_user()
    if group_role(gid, me) != "owner":
        abort(403)
    username = (request.form.get("username") or "").strip()
    if not username:
        return redirect(url_for("group_chat", gid=gid))
    if group_role(gid, username) != "member":
        return redirect(url_for("group_chat", gid=gid))
    conn = db_connect()
    conn.execute("UPDATE group_members SET role='admin' WHERE group_id=? AND username=?", (gid, username))
    conn.commit()
    conn.close()
    flash("Promoted to admin.")
    return redirect(url_for("group_chat", gid=gid))

@app.route("/groups/<int:gid>/admins/demote", methods=["POST"])
@login_required
def group_demote_admin(gid: int):
    """group_demote_admin.

Admin-only route handler.

This docstring was expanded to make future maintenance easier.

Args:
    gid: Parameter.

Returns:
    Varies.
"""
    me = current_user()
    if group_role(gid, me) != "owner":
        abort(403)
    username = (request.form.get("username") or "").strip()
    if not username:
        return redirect(url_for("group_chat", gid=gid))
    if group_role(gid, username) != "admin":
        return redirect(url_for("group_chat", gid=gid))
    conn = db_connect()
    conn.execute("UPDATE group_members SET role='member' WHERE group_id=? AND username=?", (gid, username))
    conn.commit()
    conn.close()
    flash("Admin removed.")
    return redirect(url_for("group_chat", gid=gid))

def _group_store_voice(gm_id: int, file_storage) -> Tuple[int, str]:
    """Store a group voice message (plaintext on disk)."""
    mime = _validate_chat_voice_upload(file_storage)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO group_voice(gm_id, mime, stored_path, created_at) VALUES(?,?,?,?)",
                (gm_id, mime, "PENDING", now_z()))
    vid = cur.lastrowid

    stored_path = os.path.join(ATT_DIR, f"group_voice_{vid}.bin")
    try:
        size = _save_plain_upload(file_storage, stored_path)
        if int(size) > CHAT_MAX_BYTES:
            try:
                os.remove(stored_path)
            except Exception:
                pass
            conn.execute("DELETE FROM group_voice WHERE id=?", (vid,))
            conn.commit()
            conn.close()
            raise ValueError("too_large")
    except Exception:
        conn.close()
        raise

    conn.execute("UPDATE group_voice SET stored_path=? WHERE id=?", (stored_path, vid))
    conn.commit()
    conn.close()
    return vid, mime


    _save_plain_upload(file_storage, tmp_plain)

    def finalize(ok: bool, err: Optional[str]):
        """finalize.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    ok: Parameter.
    err: Parameter.

Returns:
    Varies.
"""
        c = db_connect()
        if ok and os.path.exists(stored_path):
            c.execute("UPDATE group_voice SET stored_path=? WHERE id=?", (stored_path, vid))
        c.commit()
        c.close()

    _bg_encrypt_file(tmp_plain, stored_path, finalize)
    conn.commit()
    conn.close()
    return vid, mime

def _group_store_voice_tx(conn, gm_id: int, file_storage) -> Tuple[int, str, str]:
    """Store a group voice message using an existing DB connection/transaction."""
    mime = _validate_chat_voice_upload(file_storage)
    cur = conn.cursor()
    cur.execute("INSERT INTO group_voice(gm_id, mime, stored_path, created_at) VALUES(?,?,?,?)",
                (gm_id, mime, "PENDING", now_z()))
    vid = cur.lastrowid
    stored_path = os.path.join(ATT_DIR, f"group_voice_{vid}.bin")
    size = _save_plain_upload(file_storage, stored_path)
    if int(size) > CHAT_MAX_BYTES:
        try:
            os.remove(stored_path)
        except Exception:
            pass
        raise ValueError("too_large")
    conn.execute("UPDATE group_voice SET stored_path=? WHERE id=?", (stored_path, vid))
    return vid, mime, stored_path

@app.route("/chat/<username>/lock/set", methods=["POST"])
@login_required
def dm_lock_set(username: str):
    me = current_user()
    username = (username or "").strip()
    conn = db_connect()
    exists = conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    if not exists:
        flash("User not found.")
        return redirect(url_for("chats"))
    pin = request.form.get("pin") or ""
    try:
        _chat_lock_set(me, "dm", username, pin)
        flash("Chat PIN saved.")
    except ValueError:
        flash("PIN must be 4 to 12 digits.")
    return redirect(url_for("chat_with", username=username))


@app.route("/chat/<username>/lock/unlock", methods=["POST"])
@login_required
def dm_lock_unlock(username: str):
    me = current_user()
    username = (username or "").strip()
    pin = request.form.get("pin") or ""
    if _chat_lock_verify_and_unlock(me, "dm", username, pin):
        flash("Chat unlocked.")
    else:
        flash("Wrong PIN.")
    return redirect(url_for("chat_with", username=username))


@app.route("/chat/<username>/lock/remove", methods=["POST"])
@login_required
def dm_lock_remove(username: str):
    me = current_user()
    username = (username or "").strip()
    _chat_lock_remove(me, "dm", username)
    flash("Chat PIN removed.")
    return redirect(url_for("chat_with", username=username))


@app.route("/chat/<username>/lock/close", methods=["POST"])
@login_required
def dm_lock_close(username: str):
    me = current_user()
    username = (username or "").strip()
    _chat_lock_clear_session(me, "dm", username)
    flash("Chat locked.")
    return redirect(url_for("chat_with", username=username))


@app.route("/groups/<int:gid>/lock/set", methods=["POST"])
@login_required
def group_lock_set(gid: int):
    me = current_user()
    if not group_role(gid, me):
        abort(403)
    pin = request.form.get("pin") or ""
    try:
        _chat_lock_set(me, "group", gid, pin)
        flash("Group PIN saved.")
    except ValueError:
        flash("PIN must be 4 to 12 digits.")
    return redirect(url_for("group_chat", gid=gid))


@app.route("/groups/<int:gid>/lock/unlock", methods=["POST"])
@login_required
def group_lock_unlock(gid: int):
    me = current_user()
    if not group_role(gid, me):
        abort(403)
    pin = request.form.get("pin") or ""
    if _chat_lock_verify_and_unlock(me, "group", gid, pin):
        flash("Group unlocked.")
    else:
        flash("Wrong PIN.")
    return redirect(url_for("group_chat", gid=gid))


@app.route("/groups/<int:gid>/lock/remove", methods=["POST"])
@login_required
def group_lock_remove(gid: int):
    me = current_user()
    if not group_role(gid, me):
        abort(403)
    _chat_lock_remove(me, "group", gid)
    flash("Group PIN removed.")
    return redirect(url_for("group_chat", gid=gid))


@app.route("/groups/<int:gid>/lock/close", methods=["POST"])
@login_required
def group_lock_close(gid: int):
    me = current_user()
    if not group_role(gid, me):
        abort(403)
    _chat_lock_clear_session(me, "group", gid)
    flash("Group locked.")
    return redirect(url_for("group_chat", gid=gid))


@app.route("/groups/<int:gid>/chat")
@login_required
def group_chat(gid: int):
    """group_chat.

Chat/group feature helper or route handler.

This docstring was expanded to make future maintenance easier.

Args:
    gid: Parameter.

Returns:
    Varies.
"""
    me = current_user()
    role = group_role(gid, me)
    if not role:
        abort(403)

    conn = db_connect()
    g_row = conn.execute("SELECT * FROM groups WHERE id=?", (gid,)).fetchone()
    if not g_row:
        conn.close()
        abort(404)

    mem_rows = conn.execute("SELECT username, role FROM group_members WHERE group_id=? ORDER BY username COLLATE NOCASE", (gid,)).fetchall()
    members = []
    for r in mem_rows:
        members.append({"username": r["username"], "role": r["role"], "online": is_online(r["username"], current_scope())})

    has_group_pin = _chat_lock_exists(me, "group", gid)
    group_unlocked = _chat_lock_is_unlocked(me, "group", gid)

    class Obj:
        def __init__(self, r):
            """__init__.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    self: Parameter.
    r: Parameter.

Returns:
    Varies.
"""
            self.__dict__.update(dict(r))

    if has_group_pin and not group_unlocked:
        conn.close()
        return render_template("group_locked.html", title="Group chat",
                               g=Obj(g_row), my_role=role, members=[type("M", (), m)() for m in members],
                               all_users=all_usernames(), me=me)

    msg_rows = conn.execute("""
        SELECT id, sender, body_enc, created_at
        FROM group_messages WHERE group_id=? ORDER BY id ASC LIMIT 400
    """, (gid,)).fetchall()

    messages = []
    for r in msg_rows:
        v = conn.execute("SELECT id, mime FROM group_voice WHERE gm_id=? ORDER BY id DESC LIMIT 1", (r["id"],)).fetchone()
        has_voice = bool(v)
        try:
            body = aesgcm_decrypt_text(r["body_enc"])
        except Exception:
            body = "[decrypt failed]"
        messages.append({
            "id": r["id"],
            "sender": r["sender"],
            "kind": "voice" if has_voice else "text",
            "body": body if not has_voice else "",
            "created_at_local": _local_time_str(r["created_at"]),
            "created_at_utc": r["created_at"],
            "voice_id": v["id"] if v else None,
            "voice_mime": v["mime"] if v else "audio/webm"
        })

    conn.close()

    return render_template("group_chat.html", title="Group chat",
                           g=Obj(g_row), my_role=role, members=[type("M", (), m)() for m in members],
                           all_users=all_usernames(), me=me, messages=messages, has_group_pin=has_group_pin)

@app.route("/groups/<int:gid>/send", methods=["POST"])
@login_required
def group_send(gid: int):
    """Send a group message (text and/or voice) without forcing a page refresh when called via AJAX.

    Stability:
      - Commit the group message + voice attachment atomically (single transaction)
        so polling clients never see a blank placeholder voice row.
    """
    me = current_user()
    role = group_role(gid, me)
    if not _chat_lock_is_unlocked(me, "group", gid):
        return _locked_json_or_redirect("group", gid)
    if not role:
        abort(403)

    is_ajax = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in (request.headers.get("Accept", ""))
    )

    body = (request.form.get("body") or "").strip()
    voice = request.files.get("voice")
    has_voice = bool(voice and getattr(voice, "filename", ""))

    if has_voice:
        try:
            _validate_chat_voice_upload(voice)
        except ValueError as ve:
            msg = "Unsupported voice file type."
            if str(ve) == "forbidden_type":
                msg = "Forbidden file type."
            if is_ajax:
                return jsonify(ok=False, error=msg), 400
            flash(msg)
            return redirect(url_for("group_chat", gid=gid))
        vsz = _filestorage_size(voice)
        if vsz is not None and vsz > CHAT_MAX_BYTES:
            if is_ajax:
                return jsonify(ok=False, error="Voice message too large (max 33MB)."), 413
            flash("Voice message too large (max 33MB).")
            return redirect(url_for("group_chat", gid=gid))

    if not body and not has_voice:
        if is_ajax:
            return jsonify(ok=False, error="empty"), 400
        flash("Write a message or attach voice.")
        return redirect(url_for("group_chat", gid=gid))

    conn = db_connect()
    saved_paths = []
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO group_messages(group_id, sender, body_enc, created_at) VALUES(?,?,?,?)",
            (gid, me, aesgcm_encrypt_text(body or ""), now_z()),
        )
        gm_id = cur.lastrowid

        if has_voice:
            _, _, sp = _group_store_voice_tx(conn, gm_id, voice)
            saved_paths.append(sp)

        conn.commit()

        if is_ajax:
            r = conn.execute("SELECT id, sender, body_enc, created_at FROM group_messages WHERE id=?", (gm_id,)).fetchone()
            v = conn.execute("SELECT id, mime FROM group_voice WHERE gm_id=? ORDER BY id DESC LIMIT 1", (gm_id,)).fetchone()
            if not r:
                return jsonify(ok=False, error="not_found"), 404
            has_voice2 = bool(v)
            try:
                body_txt = aesgcm_decrypt_text(r["body_enc"])
            except Exception:
                body_txt = "[decrypt failed]"
            m = {
                "id": r["id"],
                "sender": r["sender"],
                "kind": "voice" if has_voice2 else "text",
                "body": body_txt if not has_voice2 else "",
                "created_at_local": _local_time_str(r["created_at"]),
                "created_at_utc": r["created_at"],
                "voice_id": v["id"] if v else None,
                "voice_mime": v["mime"] if v else "audio/webm",
            }
            html_row = render_template_string(_GROUP_ROW_TEMPLATE, m=m, me=me)
            m["voice_url"] = (url_for("group_voice_stream", vid=m["voice_id"]) if m.get("voice_id") else None)
            return jsonify(ok=True, id=gm_id, html=html_row, message=m)

        return redirect(url_for("group_chat", gid=gid))

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        for sp in saved_paths:
            try:
                if sp and os.path.exists(sp):
                    os.remove(sp)
            except Exception:
                pass
        log.exception("group_send failed: %s", e)
        if is_ajax:
            return jsonify(ok=False, error="Send failed"), 500
        flash("Send failed.")
        return redirect(url_for("group_chat", gid=gid))
    finally:
        try:
            conn.close()
        except Exception:
            pass




@app.route("/groups/<int:gid>/poll")
@login_required
def group_poll(gid: int):
    """Return new group messages after a given message id (AJAX polling)."""
    me = current_user()
    role = group_role(gid, me)
    if not _chat_lock_is_unlocked(me, "group", gid):
        return jsonify(ok=False, locked=True, error="PIN required"), 423
    if not role:
        abort(403)

    after = request.args.get("after", "0").strip()
    try:
        after_id = int(after)
    except Exception:
        after_id = 0

    conn = db_connect()
    try:
        rows = conn.execute(
            """
            SELECT id, sender, body_enc, created_at
            FROM group_messages
            WHERE group_id=? AND id>?
            ORDER BY id ASC
            LIMIT 80
            """,
            (gid, after_id),
        ).fetchall()

        items = []
        for r in rows:
            v = conn.execute("SELECT id, mime FROM group_voice WHERE gm_id=? ORDER BY id DESC LIMIT 1", (r["id"],)).fetchone()
            has_voice = bool(v)
            try:
                body_txt = aesgcm_decrypt_text(r["body_enc"])
            except Exception:
                body_txt = "[decrypt failed]"
            items.append({
                "id": int(r["id"]),
                "sender": r["sender"],
                "kind": "voice" if has_voice else "text",
                "body": body_txt if not has_voice else "",
                "created_at_local": _local_time_str(r["created_at"]),
                "created_at_utc": r["created_at"],
                "voice_id": v["id"] if v else None,
                "voice_mime": v["mime"] if v else "audio/webm",
                "voice_url": (url_for("group_voice_stream", vid=v["id"]) if v else None),
            })
        return jsonify(ok=True, items=items)
    finally:
        try:
            conn.close()
        except Exception:
            pass

@app.route("/group/voice/<int:vid>")
@login_required
def group_voice_stream(vid: int):
    """Stream a group voice message."""
    me = current_user()
    conn = db_connect()
    row = conn.execute("""
        SELECT v.id, v.mime, v.stored_path, m.group_id
        FROM group_voice v
        JOIN group_messages m ON m.id=v.gm_id
        WHERE v.id=?
    """, (vid,)).fetchone()
    conn.close()
    if not row:
        abort(404)
    if not group_role(int(row["group_id"]), me):
        abort(403)
    if not _chat_lock_is_unlocked(me, "group", int(row["group_id"])):
        return redirect(url_for("group_chat", gid=int(row["group_id"])))

    sp = row["stored_path"]
    if not sp or not os.path.exists(sp):
        abort(404)

    mime = row["mime"] or "audio/webm"
    try:
        if is_encrypted_file(sp):
            gen = aesgcm_decrypt_generator(sp)
            resp = Response(gen, mimetype=mime)
        else:
            from flask import send_file
            resp = send_file(sp, mimetype=mime, as_attachment=False, conditional=True, max_age=0)
    except Exception:
        abort(404)

    resp.headers["Cache-Control"] = "no-store"
    return resp


# ----------
# -----------------
# Profiler (text encrypted; attachments plaintext)
# ---------------------------


# ---------------- Profiler optional fields helpers ----------------

PROFILER_OPTIONAL_KEYS = [
    "phone", "email", "car_model", "license_plate", "id_number",
    "height_cm", "weight_kg", "eye_color", "hair_color", "job",
    "country", "state", "town", "address", "family_members", "close_friends" ]

def profiler_collect_optional(form) -> Dict[str, str]:
    """profiler_collect_optional.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    form: Parameter.

Returns:
    Varies.
"""
    def clean(s: str) -> str:
        """clean.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    s: Parameter.

Returns:
    Varies.
"""
        return (s or "").strip()

    out: Dict[str, str] = {}
    out["phone"] = clean(form.get("opt_phone"))
    out["email"] = clean(form.get("opt_email"))
    out["car_model"] = clean(form.get("opt_car_model"))
    out["license_plate"] = clean(form.get("opt_license_plate"))
    out["id_number"] = clean(form.get("opt_id_number"))
    out["height_cm"] = clean(form.get("opt_height_cm"))
    out["weight_kg"] = clean(form.get("opt_weight_kg"))
    out["eye_color"] = clean(form.get("opt_eye_color"))
    out["hair_color"] = clean(form.get("opt_hair_color"))
    out["job"] = clean(form.get("opt_job"))
    out["country"] = clean(form.get("opt_country"))
    out["state"] = clean(form.get("opt_state"))
    out["town"] = clean(form.get("opt_town"))
    out["address"] = clean(form.get("opt_address"))

    fam = clean(form.get("opt_family_members"))
    if fam:
        lines = [ln.strip() for ln in fam.replace("\r", "").split("\n") if ln.strip()]
        out["family_members"] = "\n".join(lines[:10])

    fr = clean(form.get("opt_close_friends"))
    if fr:
        lines = [ln.strip() for ln in fr.replace("\r", "").split("\n") if ln.strip()]
        out["close_friends"] = "\n".join(lines[:10])

    # Drop empties
    out = {k: v for k, v in out.items() if v}
    return out

def profiler_encrypt_optional(opt: Dict[str, str]) -> str:
    """profiler_encrypt_optional.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    opt: Parameter.

Returns:
    Varies.
"""
    try:
        if not opt:
            return ""
        return aesgcm_encrypt_text(json.dumps(opt, ensure_ascii=False))
    except Exception:
        return ""

def profiler_decrypt_optional(optional_enc: Optional[str]) -> Dict[str, str]:
    """profiler_decrypt_optional.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    optional_enc: Parameter.

Returns:
    Varies.
"""
    if not optional_enc:
        return {}
    try:
        raw = aesgcm_decrypt_text(optional_enc)
        data = json.loads(raw) if raw else {}
        if isinstance(data, dict):
            # keep only known keys, but don't break older/newer
            return {k: str(v) for k, v in data.items() if v is not None}
        return {}
    except Exception:
        return {}

# ---------------------------
# Auto-sync: My Profile -> Profiler (per-user, encrypted)
# ---------------------------

_AUTOSYNC_TYPE = "user_profile"

def _split_name_from_nick(nick: str, fallback_last: str) -> Tuple[str, str]:
    """Split a nickname into first/last. Ensures last is non-empty."""
    nick = (nick or "").strip()
    if not nick:
        return fallback_last, fallback_last
    parts = [p for p in re.split(r"\s+", nick) if p]
    if not parts:
        return fallback_last, fallback_last
    first = parts[0].strip()
    last = " ".join(parts[1:]).strip()
    if not last:
        last = fallback_last
    return first[:120], last[:120]

def _clean_num(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    # Keep digits and a dot/comma (best-effort).
    s2 = re.sub(r"[^0-9\.,]", "", s)
    return s2.strip()

def profiler_sync_from_user_profile(username: str):
    """Ensure a user's My Profile is mirrored into their Profiler list.

    This creates (or updates) one special encrypted Profiler entry owned by the same user.
    No username is excluded from the profile -> profiler sync.
    """
    if not username:
        return
    prof = get_profile(username) or {}
    nick = (prof.get("nickname") or "").strip() or username
    first, last = _split_name_from_nick(nick, fallback_last=username)

    bio = (prof.get("bio") or "").strip()
    links = prof.get("links") or []
    # Keep info concise but useful.
    lines = [f"Auto-synced from ButSystem My Profile (@{username})."]
    if bio:
        lines += ["", "Bio:", bio]
    if links:
        lines += ["", "Links:"]
        for l in links:
            if l:
                lines.append(f"- {str(l).strip()}")
    info = "\n".join(lines).strip()[:10000]

    # Optional mapping (best-effort)
    opt: Dict[str, str] = {}
    def add(k: str, v: Any):
        v = (str(v) if v is not None else "").strip()
        if v:
            opt[k] = v

    add("phone", prof.get("phone"))
    add("email", prof.get("email"))
    add("car_model", prof.get("car_model"))
    add("license_plate", prof.get("license_plate"))
    add("id_number", prof.get("id_number"))
    add("height_cm", _clean_num(prof.get("height")))
    add("weight_kg", _clean_num(prof.get("weight")))
    add("eye_color", prof.get("eye_color"))
    add("hair_color", prof.get("hair_color"))
    add("job", prof.get("job"))
    add("country", prof.get("country"))
    add("state", prof.get("state"))
    add("town", prof.get("town"))
    add("address", prof.get("address"))
    add("family_members", prof.get("family_members"))
    add("close_friends", prof.get("close_friends"))

    opt["autosync_type"] = _AUTOSYNC_TYPE
    opt["autosync_username"] = username

    # Find existing autosync entry for this user.
    conn = db_connect()
    rows = conn.execute("SELECT id, optional_enc FROM profiler_entries WHERE owner=?", (username,)).fetchall()
    target_id = None
    for r in rows:
        try:
            o = profiler_decrypt_optional(r["optional_enc"] or "")
            if (o.get("autosync_type") == _AUTOSYNC_TYPE) and (o.get("autosync_username") == username):
                target_id = int(r["id"])
                break
        except Exception:
            continue

    first_enc = aesgcm_encrypt_text(first)
    last_enc = aesgcm_encrypt_text(last)
    info_enc = aesgcm_encrypt_text(info)
    opt_enc = profiler_encrypt_optional(opt)

    if target_id is None:
        conn.execute(
            "INSERT INTO profiler_entries(owner, first_enc, last_enc, info_enc, optional_enc, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (username, first_enc, last_enc, info_enc, opt_enc, now_z(), now_z()),
        )
    else:
        conn.execute(
            "UPDATE profiler_entries SET first_enc=?, last_enc=?, info_enc=?, optional_enc=?, updated_at=? WHERE id=? AND owner=?",
            (first_enc, last_enc, info_enc, opt_enc, now_z(), target_id, username),
        )
    conn.commit()
    conn.close()



def profiler_list(owner: str) -> List[Dict[str, str]]:
    """profiler_list.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    owner: Parameter.

Returns:
    Varies.
"""
    conn = db_connect()
    rows = conn.execute("""
        SELECT id, owner, first_enc, last_enc, info_enc, created_at, updated_at,
               bounty_price, bounty_set_by, bounty_updated_at, bounty_reason
        FROM profiler_entries WHERE owner=? ORDER BY id DESC LIMIT 500
    """, (owner,)).fetchall()
    conn.close()

    out = []
    for r in rows:
        try:
            first = aesgcm_decrypt_text(r["first_enc"])
        except Exception:
            first = "[decrypt failed]"
        try:
            last = aesgcm_decrypt_text(r["last_enc"])
        except Exception:
            last = "[decrypt failed]"
        out.append({
            "id": r["id"],
            "owner": r["owner"],
            "first": first,
            "last": last,
            "updated_at": r["updated_at"],
            "created_at": r["created_at"],
            "bounty_price": (float(r["bounty_price"]) if ("bounty_price" in r.keys() and r["bounty_price"] is not None) else None),
            "bounty_set_by": (r["bounty_set_by"] if "bounty_set_by" in r.keys() else None),
            "bounty_updated_at": (r["bounty_updated_at"] if "bounty_updated_at" in r.keys() else None),
            "bounty_reason": (r["bounty_reason"] if "bounty_reason" in r.keys() else None),
            "bounty_price_display": (_fmt_bounty_price(r["bounty_price"]) if ("bounty_price" in r.keys() and r["bounty_price"] is not None) else None),
        })
    return out

def profiler_get(owner: str, eid: int) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    """profiler_get.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    owner: Parameter.
    eid: Parameter.

Returns:
    Varies.
"""
    conn = db_connect()
    r = conn.execute("""
        SELECT * FROM profiler_entries WHERE id=? AND owner=?
    """, (eid, owner)).fetchone()
    if not r:
        conn.close()
        raise KeyError("not found")
    att = conn.execute("""
        SELECT id, entry_id, filename_enc, mime_enc, stored_path, created_at
        FROM profiler_attachments WHERE entry_id=? ORDER BY id DESC
    """, (eid,)).fetchall()
    conn.close()

    def dtxt(x, fallback):
        """dtxt.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    x: Parameter.
    fallback: Parameter.

Returns:
    Varies.
"""
        try: return aesgcm_decrypt_text(x)
        except Exception: return fallback

    entry = {
        "id": r["id"],
        "owner": r["owner"],
        "first": dtxt(r["first_enc"], "[decrypt failed]"),
        "last": dtxt(r["last_enc"], "[decrypt failed]"),
        "info": dtxt(r["info_enc"], "[decrypt failed]"),
        "opt": profiler_decrypt_optional(r["optional_enc"] if "optional_enc" in r.keys() else None),
        "bounty_price": (float(r["bounty_price"]) if ("bounty_price" in r.keys() and r["bounty_price"] is not None) else None),
        "bounty_set_by": (r["bounty_set_by"] if "bounty_set_by" in r.keys() else None),
        "bounty_updated_at": (r["bounty_updated_at"] if "bounty_updated_at" in r.keys() else None),
        "bounty_reason": (r["bounty_reason"] if "bounty_reason" in r.keys() else None),
        "bounty_price_display": (_fmt_bounty_price(r["bounty_price"]) if ("bounty_price" in r.keys() and r["bounty_price"] is not None) else None),
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }
    atts = []
    for a in att:
        atts.append({
            "id": a["id"],
            "filename": dtxt(a["filename_enc"], "file"),
            "mime": dtxt(a["mime_enc"], "application/octet-stream"),
            "created_at": a["created_at"],
            "stored_path": a["stored_path"],
        })
    return entry, atts

def profiler_store_attachment(eid: int, file_storage):
    """Store a profiler attachment (plaintext on disk).

    Profiler *text fields* remain encrypted in the database; only binary attachments
    are stored without encryption (per your request).
    """
    if not file_storage or not getattr(file_storage, "filename", ""):
        return

    filename, mime = _validate_report_upload(file_storage)

    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO profiler_attachments(entry_id, filename_enc, mime_enc, stored_path, created_at)
        VALUES(?,?,?,?,?)
    """, (eid, aesgcm_encrypt_text(filename), aesgcm_encrypt_text(mime), "PENDING", now_z()))
    aid = cur.lastrowid

    stored_path = os.path.join(ATT_DIR, f"prof_att_{aid}.bin")
    try:
        size = _save_plain_upload(file_storage, stored_path)
        # Keep profiler attachments reasonably bounded to avoid DoS.
        if int(size) > CHAT_MAX_BYTES:
            try:
                os.remove(stored_path)
            except Exception:
                pass
            conn.execute("DELETE FROM profiler_attachments WHERE id=?", (aid,))
            conn.commit()
            conn.close()
            raise ValueError("too_large")
        conn.execute("UPDATE profiler_attachments SET stored_path=? WHERE id=?", (stored_path, aid))
        conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _bounty_currency_symbol() -> str:
    try:
        return "€" if get_lang() == "el" else "$"
    except Exception:
        return "$"

def _fmt_bounty_amount_plain(val: Any) -> str:
    try:
        f = float(val)
    except Exception:
        return ""
    if f.is_integer():
        return str(int(f))
    s = f"{f:.2f}".rstrip("0").rstrip(".")
    return s or "0"

def _fmt_bounty_price(val: Any) -> str:
    """Format bounty price with localized currency symbol."""
    amt = _fmt_bounty_amount_plain(val)
    if not amt:
        return ""
    return f"{_bounty_currency_symbol()}{amt}"

def _complete_login_session(username: str, is_admin: bool) -> Response:
    # Drop stale session data on successful login while keeping a fresh CSRF token.
    try:
        session.clear()
    except Exception:
        pass
    session["u"] = username
    session.permanent = True
    session["login_at"] = now_z()
    session["_csrf"] = secrets.token_urlsafe(32)
    ensure_profile_row(username)
    try:
        prof = get_profile(username)
        if prof.get("nickname") == username and not prof.get("bio") and not prof.get("links"):
            set_profile(username, username, "", [])
    except Exception:
        pass
    resp = redirect(url_for("loading"))
    try:
        # Auto-login on this device (trusted-device cookie)
        fp = (request.cookies.get(DEVICE_FP_COOKIE) or "").strip()
        if not fp:
            fp = secrets.token_urlsafe(24)
            resp.set_cookie(DEVICE_FP_COOKIE, fp, max_age=180*24*3600, httponly=True, samesite="Lax", secure=request.is_secure)
        token = _issue_trusted_device(username, fp, approved_by=(username if is_admin else None))
        _set_device_token_cookie(resp, token)
    except Exception:
        pass
    return resp

def profiler_all_entries_for_bounty(search_q: str = "") -> List[Dict[str, Any]]:
    """Admin helper: list profiler entries across all owners with decrypted names + bounty info."""
    conn = db_connect()
    rows = conn.execute("""
        SELECT id, owner, first_enc, last_enc, bounty_price, bounty_set_by, bounty_updated_at, bounty_reason
        FROM profiler_entries
        ORDER BY id DESC
        LIMIT 5000
    """).fetchall()
    conn.close()

    q = (search_q or "").strip().lower()
    out: List[Dict[str, Any]] = []
    for r in rows:
        try:
            first = aesgcm_decrypt_text(r["first_enc"])
        except Exception:
            first = "[decrypt failed]"
        try:
            last = aesgcm_decrypt_text(r["last_enc"])
        except Exception:
            last = "[decrypt failed]"
        item = {
            "id": r["id"],
            "owner": r["owner"],
            "first": first,
            "last": last,
            "bounty_price": (float(r["bounty_price"]) if r["bounty_price"] is not None else None),
            "bounty_set_by": r["bounty_set_by"],
            "bounty_updated_at": r["bounty_updated_at"],
            "bounty_reason": (r["bounty_reason"] if "bounty_reason" in r.keys() else None),
        }
        item["bounty_price_display"] = _fmt_bounty_price(item["bounty_price"]) if item["bounty_price"] is not None else ""
        item["bounty_reason"] = (item.get("bounty_reason") or "").strip()
        if q:
            blob = f'{item["id"]} {item["owner"]} {first} {last}'.lower()
            if q not in blob:
                continue
        out.append(item)
    return out



def _face_detector_bounty_preview_source(eid: int) -> Optional[Dict[str, Any]]:
    """Return the best available image source for a bounty profiler entry.

    This is for manual side-by-side review only. It does not perform any
    biometric comparison or matching.
    """
    conn = db_connect()
    row = conn.execute(
        "SELECT id, owner, bounty_price FROM profiler_entries WHERE id=?",
        (eid,),
    ).fetchone()
    if not row or row["bounty_price"] is None:
        conn.close()
        return None

    att_rows = conn.execute(
        "SELECT id, filename_enc, mime_enc, stored_path FROM profiler_attachments WHERE entry_id=? ORDER BY id ASC",
        (eid,),
    ).fetchall()
    conn.close()

    for a in att_rows:
        sp = a["stored_path"]
        if not sp or not os.path.exists(sp):
            continue
        try:
            mime = (aesgcm_decrypt_text(a["mime_enc"]) or "").strip().lower()
        except Exception:
            mime = ""
        if mime.startswith("image/"):
            return {"kind": "attachment", "aid": int(a["id"]), "mime": mime, "path": sp, "owner": row["owner"]}

    # Fallback to the owner's profile picture when available.
    conn = db_connect()
    prow = conn.execute("SELECT pic_path, pic_mime FROM profiles WHERE username=?", (row["owner"],)).fetchone()
    conn.close()
    if prow and prow["pic_path"] and os.path.exists(prow["pic_path"]):
        return {
            "kind": "profile_pic",
            "username": row["owner"],
            "mime": (prow["pic_mime"] or "image/jpeg"),
            "path": prow["pic_path"],
            "owner": row["owner"],
        }
    return None


def _face_detector_bounty_refs(limit: int = 120) -> List[Dict[str, Any]]:
    """Admin-only list of bounty entries that have a previewable image."""
    out: List[Dict[str, Any]] = []
    for item in profiler_all_entries_for_bounty(""):
        if item.get("bounty_price") is None:
            continue
        src = _face_detector_bounty_preview_source(int(item["id"]))
        if not src:
            continue
        item = dict(item)
        item["preview_url"] = url_for("face_detector_bounty_preview", eid=int(item["id"]))
        out.append(item)
        if len(out) >= int(limit):
            break
    return out

def _face_detector_i18n() -> Dict[str, str]:
    return {
        "ready": _("Ready."),
        "readyTapStart": _("Ready. Tap Start camera."),
        "startingCamera": _("Starting camera..."),
        "liveCamera": _("Live camera ready."),
        "cameraError": _("Failed to acquire camera feed."),
        "cameraBusyTip": _("Tip: On phones, if the camera is busy in another app, close that app first and then tap Start camera again."),
        "analyzingUpload": _("Analyzing uploaded media..."),
        "uploadFailed": _("Could not analyze the uploaded media."),
        "unsupportedFile": _("Please choose a photo or video file."),
        "nothingToSave": _("Nothing to save yet."),
        "saveFailed": _("Could not save the result."),
        "savedTo": _("Saved to"),
        "serverStandby": _("SERVER: STANDBY"),
        "serverUploading": _("SERVER: UPLOADING..."),
        "serverSaved": _("SERVER: SAVED"),
        "serverDisconnected": _("SERVER: DISCONNECTED"),
        "serverAnalyzing": _("SERVER: ANALYZING"),
        "sourceLive": _("SOURCE: LIVE CAMERA"),
        "sourcePhoto": _("SOURCE: UPLOADED PHOTO"),
        "sourceVideo": _("SOURCE: UPLOADED VIDEO"),
        "noFaceDetected": _("No face detected."),
        "detectedFaces": _("Detected faces"),
        "saveFacesFailed": _("No detected faces to save yet."),
        "photoSaved": _("Photo saved."),
        "recordingSaved": _("Recording saved."),
        "recordingNotSupported": _("Browser does not support WebM recording."),
        "videoPlaybackBlocked": _("Video playback blocked."),
        "live": _("LIVE"),
        "upload": _("UPLOAD"),
        "analyzing": _("ANALYZING"),
        "recording": _("RECORDING"),
        "face": _("Face"),
        "faceId": _("ID"),
        "emotionHappy": _("HAPPY"),
        "emotionSad": _("SAD"),
        "emotionAngry": _("ANGRY"),
        "emotionSurprised": _("SURPRISED"),
        "emotionNeutral": _("NEUTRAL"),
        "pose": _("POSE"),
        "shape": _("SHAPE"),
        "eyes": _("EYES"),
        "brows": _("BROWS"),
        "mouth": _("MOUTH"),
        "asym": _("ASYM"),
        "center": _("CENTER"),
        "left": _("LEFT"),
        "right": _("RIGHT"),
        "up": _("UP"),
        "long": _("LONG"),
        "round": _("ROUND"),
        "oval": _("OVAL"),
        "broad": _("BROAD"),
        "narrow": _("NARROW"),
        "wide": _("WIDE"),
        "close": _("CLOSE"),
        "avg": _("AVG"),
        "raise": _("RAISE"),
        "furrow": _("FURROW"),
        "neut": _("NEUT"),
        "manualReview": _("MANUAL REVIEW"),
        "referenceLoaded": _("Reference photo loaded."),
        "referenceCleared": _("Reference photo cleared."),
    }

def _safe_face_detector_filename(name: str) -> str:
    base = secure_filename((name or "").strip()) or f"FaceDetector_{int(time.time())}.png"
    root, ext = os.path.splitext(base)
    ext = ext.lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".webm", ".mp4"):
        ext = ".png"
    root = (root or "FaceDetector")[:80]
    return f"{root}{ext}"

@app.route("/face-detector")
@login_required
def face_detector_page():
    bounty_refs = []
    if user_is_admin(current_user()):
        try:
            bounty_refs = _face_detector_bounty_refs()
        except Exception:
            bounty_refs = []
    return render_template(
        "face_detector.html",
        title=_("Face Detector"),
        fd_i18n=_face_detector_i18n(),
        fd_bounty_refs=bounty_refs,
    )

@app.route("/face-detector/bounty-preview/<int:eid>")
@login_required
def face_detector_bounty_preview(eid: int):
    require_admin()
    src = _face_detector_bounty_preview_source(eid)
    if not src:
        abort(404)
    if src.get("kind") == "profile_pic":
        return redirect(url_for("profile_pic", username=src["username"]))
    aid = int(src.get("aid") or 0)
    if not aid:
        abort(404)
    row_owner = src.get("owner")
    sp = src.get("path")
    mime = src.get("mime") or "image/jpeg"
    if not sp or not os.path.exists(sp):
        abort(404)
    try:
        if is_encrypted_file(sp):
            resp = Response(aesgcm_decrypt_generator(sp), mimetype=mime)
        else:
            resp = send_file(sp, mimetype=mime, as_attachment=False, conditional=True, max_age=0)
    except Exception:
        abort(404)
    resp.headers["Cache-Control"] = "no-store"
    return resp

@app.route("/face-detector/save", methods=["POST"])
@login_required
def face_detector_save():
    try:
        data = request.get_json(silent=True) or {}
        filename = _safe_face_detector_filename(data.get("filename") or "")
        filedata = (data.get("filedata") or "").strip()
        m = re.match(r"^data:((?:image/(?:png|jpeg|jpg|webp))|(?:video/(?:webm|mp4)));base64,(.+)$", filedata, flags=re.I | re.S)
        if not m:
            return jsonify({"ok": False, "error": "invalid_data"}), 400
        payload = base64.b64decode(m.group(2), validate=True)
        if not payload or len(payload) > (35 * 1024 * 1024):
            return jsonify({"ok": False, "error": "invalid_size"}), 400
        out_path = os.path.join(FACE_DETECTOR_DIR, filename)
        with open(out_path, "wb") as f:
            f.write(payload)
        return jsonify({"ok": True, "path": out_path})
    except Exception as e:
        log.exception("Face detector save failed: %s", e)
        return jsonify({"ok": False, "error": "save_failed"}), 500


@app.route("/bounty")

@login_required
def bounty():
    """Admin page for adding/editing/removing profiler bounties."""
    require_admin()
    q = (request.args.get("q") or "").strip()
    selected_id = request.args.get("eid", type=int)

    entries: List[Dict[str, Any]] = []
    if q:
        entries = profiler_all_entries_for_bounty(q)[:100]

    selected = None
    if selected_id is not None:
        # fetch selected entry even when it is not shown because no search results are displayed by default
        for e in (entries + profiler_all_entries_for_bounty("")):
            if int(e["id"]) == int(selected_id):
                selected = e
                break

    class Obj:
        def __init__(self, d):
            self.__dict__.update(d)

    selected_bounty_value = ""
    selected_reason_value = ""
    selected_has_bounty = False
    if selected and selected.get("bounty_price") is not None:
        selected_bounty_value = _fmt_bounty_amount_plain(selected.get("bounty_price"))
        selected_reason_value = (selected.get("bounty_reason") or "")[:333]
        selected_has_bounty = True
    elif selected:
        selected_reason_value = (selected.get("bounty_reason") or "")[:333]

    return render_template(
        "bounty.html",
        title=_("Bounty"),
        q=q,
        selected_id=selected_id,
        selected=Obj(selected) if selected else None,
        selected_bounty_value=selected_bounty_value,
        selected_reason_value=selected_reason_value,
        selected_has_bounty=selected_has_bounty,
        entries=[Obj(e) for e in entries],
    )

@app.route("/bounty/set", methods=["POST"])
@login_required
def bounty_set():
    """Add or edit a bounty price on an existing profiler entry (admin only)."""
    require_admin()
    eid = request.form.get("eid", type=int)
    price_raw = (request.form.get("price") or "").strip()
    reason = (request.form.get("reason") or "").strip()
    if not eid:
        flash(_("Select a profile first."))
        return redirect(url_for("bounty"))
    if not reason:
        flash(_("Bounty reason is required."))
        return redirect(url_for("bounty", eid=eid))
    if len(reason) > 333:
        flash(_("Bounty reason must be 333 characters or less."))
        return redirect(url_for("bounty", eid=eid))
    try:
        price = float(price_raw.replace(",", ""))
        if price < 0:
            raise ValueError
    except Exception:
        flash(_("Invalid bounty price."))
        return redirect(url_for("bounty", eid=eid))

    conn = db_connect()
    exists = conn.execute("SELECT id FROM profiler_entries WHERE id=?", (eid,)).fetchone()
    if not exists:
        conn.close()
        flash(_("Profile not found."))
        return redirect(url_for("bounty"))

    conn.execute(
        "UPDATE profiler_entries SET bounty_price=?, bounty_set_by=?, bounty_updated_at=?, bounty_reason=? WHERE id=?",
        (price, current_user(), now_z(), reason, eid)
    )
    conn.commit()
    conn.close()
    flash(_("Bounty saved for profile") + f" #{eid}.")
    return redirect(url_for("bounty", eid=eid))

@app.route("/bounty/remove", methods=["POST"])
@login_required
def bounty_remove():
    """Remove a bounty from a profiler entry (admin only)."""
    require_admin()
    eid = request.form.get("eid", type=int)
    if not eid:
        flash(_("Select a profile first."))
        return redirect(url_for("bounty"))

    conn = db_connect()
    exists = conn.execute("SELECT id FROM profiler_entries WHERE id=?", (eid,)).fetchone()
    if not exists:
        conn.close()
        flash(_("Profile not found."))
        return redirect(url_for("bounty"))

    conn.execute(
        "UPDATE profiler_entries SET bounty_price=NULL, bounty_set_by=NULL, bounty_updated_at=?, bounty_reason=NULL WHERE id=?",
        (now_z(), eid)
    )
    conn.commit()
    conn.close()
    flash(_("Bounty removed from profile") + f" #{eid}.")
    return redirect(url_for("bounty", eid=eid))


@app.route("/profiler")
@login_required
def profiler():
    """profiler.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    owner = current_user()
    q = (request.args.get("q") or "").strip().lower()
    entries = profiler_list(owner)

    # Search (decrypts locally)
    if q:
        filtered = []
        conn = db_connect()
        rows = conn.execute("SELECT id, first_enc, last_enc, info_enc, optional_enc, updated_at FROM profiler_entries WHERE owner=? ORDER BY id DESC", (owner,)).fetchall()
        conn.close()
        for r in rows:
            try:
                first = aesgcm_decrypt_text(r["first_enc"])
                last = aesgcm_decrypt_text(r["last_enc"])
                info = aesgcm_decrypt_text(r["info_enc"])
            except Exception:
                continue
            opt = profiler_decrypt_optional(r["optional_enc"] if "optional_enc" in r.keys() else None)
            opt_blob = " ".join([str(v) for v in opt.values()])
            blob = f"{first} {last} {info} {opt_blob}".lower()
            if q in blob:
                filtered.append({"id": r["id"], "first": first, "last": last, "updated_at": r["updated_at"]})
        entries = filtered[:200]

    class Obj:
        def __init__(self, d):
            """__init__.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    self: Parameter.
    d: Parameter.

Returns:
    Varies.
"""
            self.__dict__.update(d)
    return render_template("profiler.html", title="Profiler", entries=[Obj(e) for e in entries], q=q)

@app.route("/profiler/export", methods=["POST"])
@login_required
def profiler_export():
    """profiler_export.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    owner = current_user()
    # Export all of *your* encrypted profiles into a zip in Downloads
    try:
        conn = db_connect()
        entries = conn.execute("SELECT id, first_enc, last_enc, info_enc, optional_enc, created_at, updated_at FROM profiler_entries WHERE owner=? ORDER BY id ASC", (owner,)).fetchall()
        att_rows = conn.execute("SELECT entry_id, filename_enc, mime_enc, stored_path, created_at FROM profiler_attachments WHERE entry_id IN (SELECT id FROM profiler_entries WHERE owner=?) ORDER BY id ASC", (owner,)).fetchall()
        conn.close()

        # Build export structure
        export = []
        atts_by_entry = {}
        for a in att_rows:
            atts_by_entry.setdefault(a["entry_id"], []).append(dict(a))

        tmp_dir = os.path.join(BASE_DIR, "_tmp_profiler_export")
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)
        os.makedirs(tmp_dir, exist_ok=True)

        att_out_root = os.path.join(tmp_dir, "attachments")
        os.makedirs(att_out_root, exist_ok=True)

        for r in entries:
            try:
                first = aesgcm_decrypt_text(r["first_enc"])
                last = aesgcm_decrypt_text(r["last_enc"])
                info = aesgcm_decrypt_text(r["info_enc"])
            except Exception:
                continue

            item = {
                "first": first,
                "last": last,
                "info": info,
                "optional": profiler_decrypt_optional(r["optional_enc"] if "optional_enc" in r.keys() else None),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
                "attachments": []
            }

            for a in atts_by_entry.get(r["id"], []):
                try:
                    fn = aesgcm_decrypt_text(a["filename_enc"])
                    mime = aesgcm_decrypt_text(a["mime_enc"])
                except Exception:
                    fn, mime = "file", "application/octet-stream"
                rel = f"{r['id']}/{fn}"
                item["attachments"].append({"filename": fn, "mime": mime, "path": rel})

                # Decrypt attachment into temp folder so it can be zipped
                src = a["stored_path"]
                dst = os.path.join(att_out_root, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                try:
                    if is_encrypted_file(src):
                        with open(dst, "wb") as out:
                            for chunk in aesgcm_decrypt_generator(src):
                                out.write(chunk)
                    else:
                        shutil.copy2(src, dst)
                except Exception:
                    pass

            export.append(item)

        with open(os.path.join(tmp_dir, "profiles.json"), "w", encoding="utf-8") as f:
            json.dump({"owner": owner, "exported_at": now_z(), "profiles": export}, f, ensure_ascii=False, indent=2)

        out_dir = downloads_dir()
        os.makedirs(out_dir, exist_ok=True)
        out_zip = os.path.join(out_dir, "Profiler.zip")

        # If exists, write a new numbered zip like Profiler-1.zip etc.
        if os.path.exists(out_zip):
            n = 1
            while True:
                cand = os.path.join(out_dir, f"Profiler-{n}.zip")
                if not os.path.exists(cand):
                    out_zip = cand
                    break
                n += 1

        with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.write(os.path.join(tmp_dir, "profiles.json"), arcname="profiles.json")
            for root, _, files in os.walk(att_out_root):
                for fn in files:
                    full = os.path.join(root, fn)
                    arc = os.path.relpath(full, tmp_dir)
                    z.write(full, arcname=arc)

        shutil.rmtree(tmp_dir, ignore_errors=True)
        flash(f"Exported to: {out_zip}")
    except Exception as e:
        log.exception("Profiler export failed: %s", e)
        flash("Export failed.")
    return redirect(url_for("profiler"))

@app.route("/profiler/combine", methods=["POST"])
@login_required
def profiler_combine():
    """profiler_combine.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    owner = current_user()
    try:
        ddir = downloads_dir()
        # Pick latest Profiler*.zip by mtime
        zips = sorted(glob.glob(os.path.join(ddir, "Profiler*.zip")), key=lambda p: os.path.getmtime(p))
        if not zips:
            flash("No Profiler.zip found in Downloads.")
            return redirect(url_for("profiler"))
        latest = zips[-1]

        tmp_dir = os.path.join(BASE_DIR, "_tmp_profiler_import")
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)
        os.makedirs(tmp_dir, exist_ok=True)

        with zipfile.ZipFile(latest, "r") as z:
            z.extractall(tmp_dir)

        meta_path = os.path.join(tmp_dir, "profiles.json")
        if not os.path.isfile(meta_path):
            shutil.rmtree(tmp_dir, ignore_errors=True)
            flash("Invalid zip: missing profiles.json")
            return redirect(url_for("profiler"))

        meta = json.load(open(meta_path, "r", encoding="utf-8"))
        profiles = meta.get("profiles") or []

        # Existing fingerprints to avoid duplicates
        conn = db_connect()
        existing = conn.execute("SELECT first_enc, last_enc, info_enc FROM profiler_entries WHERE owner=?", (owner,)).fetchall()
        existing_fp = set()
        for r in existing:
            try:
                fp = (aesgcm_decrypt_text(r["first_enc"]).strip().lower(),
                      aesgcm_decrypt_text(r["last_enc"]).strip().lower(),
                      aesgcm_decrypt_text(r["info_enc"]).strip().lower())
                existing_fp.add(fp)
            except Exception:
                pass

        imported = 0
        for p in profiles:
            first = (p.get("first") or "").strip()
            last = (p.get("last") or "").strip()
            info = (p.get("info") or "").strip()
            opt = p.get("optional") or {}
            if not isinstance(opt, dict):
                opt = {}
            if not (first or last or info):
                continue
            fp = (first.lower(), last.lower(), info.lower())
            if fp in existing_fp:
                continue

            now = now_z()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO profiler_entries(owner, first_enc, last_enc, info_enc, optional_enc, created_at, updated_at) VALUES(?,?,?,?,?,?,?)",
                (owner, aesgcm_encrypt_text(first), aesgcm_encrypt_text(last), aesgcm_encrypt_text(info), profiler_encrypt_optional(opt), now, now)
            )
            entry_id = cur.lastrowid

            # Attachments
            for a in (p.get("attachments") or []):
                rel = a.get("path") or ""
                src = os.path.join(tmp_dir, "attachments", rel)
                if not os.path.isfile(src):
                    continue
                fn = (a.get("filename") or os.path.basename(src) or "file").strip()
                mime = (a.get("mime") or guess_mime(fn)).strip()

                dst = os.path.join(PROF_ATT_DIR, owner, f"{entry_id}_{secrets.token_hex(8)}")
                os.makedirs(os.path.dirname(dst), exist_ok=True)

                # Encrypt at rest
                with open(src, "rb") as f:
                    aesgcm_encrypt_stream(f, dst)

                cur.execute(
                    "INSERT INTO profiler_attachments(entry_id, filename_enc, mime_enc, stored_path, created_at) VALUES(?,?,?,?,?)",
                    (entry_id, aesgcm_encrypt_text(fn), aesgcm_encrypt_text(mime), dst, now)
                )

            conn.commit()
            existing_fp.add(fp)
            imported += 1

        conn.close()
        shutil.rmtree(tmp_dir, ignore_errors=True)
        flash(f"Combined {imported} new profile(s) from {os.path.basename(latest)}")
    except Exception as e:
        log.exception("Profiler combine failed: %s", e)
        flash("Combine failed.")
    return redirect(url_for("profiler"))


@app.route("/profiler/create", methods=["POST"])
@login_required
def profiler_create():
    """profiler_create.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    owner = current_user()
    first = (request.form.get("first") or "").strip()
    last = (request.form.get("last") or "").strip()
    info = (request.form.get("info") or "").strip()
    opt = profiler_collect_optional(request.form)
    files = request.files.getlist("att")

    if not first or not last or not info:
        flash("All fields required.")
        return redirect(url_for("profiler"))

    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO profiler_entries(owner, first_enc, last_enc, info_enc, optional_enc, created_at, updated_at)
        VALUES(?,?,?,?,?,?,?)
    """, (owner, aesgcm_encrypt_text(first), aesgcm_encrypt_text(last), aesgcm_encrypt_text(info), profiler_encrypt_optional(opt), now_z(), now_z()))
    eid = cur.lastrowid
    conn.commit()
    conn.close()

    for f in files or []:
        if f and f.filename:
            try:
                profiler_store_attachment(eid, f)
            except Exception as e:
                log.exception("Profiler attachment failed: %s", e)

    flash("Profiler entry saved.")
    return redirect(url_for("profiler"))

@app.route("/profiler/<int:eid>")
@login_required
def profiler_view(eid: int):
    """profiler_view.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    eid: Parameter.

Returns:
    Varies.
"""
    owner = current_user()
    try:
        entry, atts = profiler_get(owner, eid)
    except KeyError:
        abort(404)
    if entry.get("bounty_price") is not None and not entry.get("bounty_price_display"):
        entry["bounty_price_display"] = _fmt_bounty_price(entry.get("bounty_price"))
    if entry.get("bounty_price") is not None and not entry.get("bounty_price_display"):
        entry["bounty_price_display"] = _fmt_bounty_price(entry.get("bounty_price"))
    class Obj:
        def __init__(self, d):
            """__init__.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    self: Parameter.
    d: Parameter.

Returns:
    Varies.
"""
            self.__dict__.update(d)
    return render_template("profiler_view.html", title="Profiler entry", e=Obj(entry), attachments=[Obj(a) for a in atts])


@app.route("/profiler/<int:eid>/view")
@login_required
def profiler_view_only(eid: int):
    """profiler_view_only.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    eid: Parameter.

Returns:
    Varies.
"""
    owner = current_user()
    try:
        entry, atts = profiler_get(owner, eid)
    except KeyError:
        abort(404)
    class Obj:
        def __init__(self, d):
            """__init__.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    self: Parameter.
    d: Parameter.

Returns:
    Varies.
"""
            self.__dict__.update(d)
    return render_template(
        "profiler_view_only.html",
        title="Profiler view",
        e=Obj(entry),
        attachments=[Obj(a) for a in atts],
    )

@app.route("/profiler/<int:eid>/update", methods=["POST"])
@login_required
def profiler_update(eid: int):
    """profiler_update.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    eid: Parameter.

Returns:
    Varies.
"""
    owner = current_user()
    first = (request.form.get("first") or "").strip()
    last = (request.form.get("last") or "").strip()
    info = (request.form.get("info") or "").strip()
    opt = profiler_collect_optional(request.form)
    att = request.files.get("att")

    conn = db_connect()
    row = conn.execute("SELECT 1 FROM profiler_entries WHERE id=? AND owner=?", (eid, owner)).fetchone()
    if not row:
        conn.close()
        abort(404)

    conn.execute("""
        UPDATE profiler_entries SET first_enc=?, last_enc=?, info_enc=?, optional_enc=?, updated_at=?
        WHERE id=? AND owner=?
    """, (aesgcm_encrypt_text(first), aesgcm_encrypt_text(last), aesgcm_encrypt_text(info), profiler_encrypt_optional(opt), now_z(), eid, owner))
    conn.commit()
    conn.close()

    if att and att.filename:
        try:
            profiler_store_attachment(eid, att)
        except Exception as e:
            log.exception("Profiler attachment failed: %s", e)

    flash("Updated.")
    return redirect(url_for("profiler"))

@app.route("/profiler/<int:eid>/delete", methods=["POST"])
@login_required
def profiler_delete(eid: int):
    """Delete a Profiler entry (requires typing first+last name).

    Requested safety: user must type the profile's first and last name before deletion.
    """
    owner = current_user()

    # Load entry to validate the confirmation name.
    conn = db_connect()
    row = conn.execute(
        "SELECT first_enc, last_enc FROM profiler_entries WHERE id=? AND owner=?",
        (eid, owner),
    ).fetchone()
    if not row:
        conn.close()
        abort(404)

    try:
        first = aesgcm_decrypt_text(row["first_enc"]) or ""
        last = aesgcm_decrypt_text(row["last_enc"]) or ""
    except Exception:
        first, last = "", ""

    expected = re.sub(r"\s+", " ", f"{first} {last}".strip()).strip()
    typed = (request.form.get("confirm_full") or "").strip()
    typed_n = re.sub(r"\s+", " ", typed).strip()

    if not typed_n:
        conn.close()
        flash("Type the profile first and last name to delete it.")
        return redirect(request.referrer or url_for("profiler_view", eid=eid))

    if typed_n.casefold() != expected.casefold():
        conn.close()
        flash("Name doesn't match. Deletion cancelled.")
        return redirect(request.referrer or url_for("profiler_view", eid=eid))

    # Confirmed: delete.
    conn.execute("DELETE FROM profiler_entries WHERE id=? AND owner=?", (eid, owner))
    conn.commit()
    conn.close()
    flash("Deleted.")
    return redirect(url_for("profiler"))



@app.route("/profiler/att/<int:aid>/download")
@login_required
def profiler_att_download(aid: int):
    """Download a profiler attachment."""
    owner = current_user()
    conn = db_connect()
    row = conn.execute("""
        SELECT a.id, a.filename_enc, a.mime_enc, a.stored_path, e.owner
        FROM profiler_attachments a
        JOIN profiler_entries e ON e.id=a.entry_id
        WHERE a.id=?
    """, (aid,)).fetchone()
    conn.close()
    if not row or row["owner"] != owner:
        abort(404)
    sp = row["stored_path"]
    if not sp or not os.path.exists(sp):
        abort(404)

    try:
        filename = aesgcm_decrypt_text(row["filename_enc"])
    except Exception:
        filename = "attachment"
    try:
        mime = aesgcm_decrypt_text(row["mime_enc"])
    except Exception:
        mime = "application/octet-stream"

    try:
        if is_encrypted_file(sp):
            gen = aesgcm_decrypt_generator(sp)
            resp = Response(gen, mimetype=mime)
            resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        else:
            from flask import send_file
            resp = send_file(
                sp,
                mimetype=mime,
                as_attachment=True,
                download_name=filename,
                conditional=True,
                max_age=0,
            )
    except Exception:
        abort(404)

    resp.headers["Cache-Control"] = "no-store"
    return resp

@app.route("/profiler/att/<int:aid>/delete", methods=["POST"])
@login_required
def profiler_att_delete(aid: int):
    """profiler_att_delete.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    aid: Parameter.

Returns:
    Varies.
"""
    owner = current_user()
    conn = db_connect()
    row = conn.execute("""
        SELECT a.stored_path, e.owner
        FROM profiler_attachments a
        JOIN profiler_entries e ON e.id=a.entry_id
        WHERE a.id=?
    """, (aid,)).fetchone()
    if not row or row["owner"] != owner:
        conn.close()
        abort(404)
    sp = row["stored_path"]
    conn.execute("DELETE FROM profiler_attachments WHERE id=?", (aid,))
    conn.commit()
    conn.close()
    try:
        if sp and os.path.exists(sp):
            os.remove(sp)
    except Exception:
        pass
    flash("Attachment deleted.")
    return redirect(url_for("profiler"))

# ---------------------------
# Admin browse user files
# ---------------------------
@app.route("/admin/files/<username>")
@login_required
def admin_user_files(username: str):
    """admin_user_files.

Admin-only route handler.

This docstring was expanded to make future maintenance easier.

Args:
    username: Parameter.

Returns:
    Varies.
"""
    require_admin()
    # ensure user exists
    conn = db_connect()
    exists = conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    if not exists:
        flash("User not found.")
        return redirect(url_for("admin_panel"))

    rel = request.args.get("p", "") or ""
    sort = (request.args.get("sort") or "name").lower()
    order = (request.args.get("order") or "asc").lower()
    if sort not in ("name", "mtime", "size", "type"):
        sort = "name"
    if order not in ("asc", "desc"):
        order = "asc"

    try:
        # use user_root(username) to get absolute path, then apply safe_relpath
        root = user_root(username)
        rel = safe_relpath(rel)
        ap = os.path.abspath(os.path.join(root, rel))
        if not ap.startswith(os.path.abspath(root) + os.sep) and ap != os.path.abspath(root):
            raise ValueError("Path traversal")
        os.makedirs(ap, exist_ok=True)
        entries = _list_dir_entries_raw(ap, sort, order)
    except Exception as e:
        flash(f"Cannot browse: {e}")
        return redirect(url_for("admin_panel"))

    parent = "/".join(rel.split("/")[:-1]) if rel else ""
    return render_template("admin_user_files.html", username=username, relpath=rel, parent_relpath=parent,
                           entries=entries, sort=sort, order=order)

def _list_dir_entries_raw(ap: str, sort: str, order: str):
    """_list_dir_entries_raw.

Internal helper function.

This docstring was expanded to make future maintenance easier.

Args:
    ap: Parameter.
    sort: Parameter.
    order: Parameter.

Returns:
    Varies.
"""
    entries = []
    for name in os.listdir(ap):
        full = os.path.join(ap, name)
        try:
            st = os.stat(full)
        except:
            continue
        is_dir = os.path.isdir(full)
        kind = "Folder" if is_dir else guess_mime(name)
        entries.append({"name": name, "is_dir": is_dir, "kind": kind, "size": st.st_size, "mtime": st.st_mtime})

    reverse = (order == "desc")
    def k_name(e):
        """k_name.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    e: Parameter.

Returns:
    Varies.
"""
        return (0 if e["is_dir"] else 1, e["name"].lower())
    def k_mtime(e):
        """k_mtime.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    e: Parameter.

Returns:
    Varies.
"""
        return (0 if e["is_dir"] else 1, e["mtime"])
    def k_size(e):
        """k_size.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    e: Parameter.

Returns:
    Varies.
"""
        return (0 if e["is_dir"] else 1, e["size"])
    def k_type(e):
        """k_type.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    e: Parameter.

Returns:
    Varies.
"""
        return (0 if e["is_dir"] else 1, e["kind"].lower(), e["name"].lower())

    if sort == "mtime":
        entries.sort(key=k_mtime, reverse=reverse)
    elif sort == "size":
        entries.sort(key=k_size, reverse=reverse)
    elif sort == "type":
        entries.sort(key=k_type, reverse=reverse)
    else:
        entries.sort(key=k_name, reverse=reverse)

    class Obj: pass
    out = []
    for e in entries:
        o = Obj()
        o.name = e["name"]
        o.is_dir = e["is_dir"]
        o.kind = e["kind"]
        o.size_h = "-" if e["is_dir"] else human_size(int(e["size"]))
        o.mtime_h = datetime.fromtimestamp(e["mtime"]).isoformat(sep=" ", timespec="seconds")
        out.append(o)
    return out

@app.route("/admin/files/<username>/download")
@login_required
def admin_user_download(username: str):
    """Admin-only: download any user's vault file."""
    require_admin()
    p = request.args.get("p", "") or ""
    try:
        root = user_root(username)
        rel = safe_relpath(p)
        ap = os.path.abspath(os.path.join(root, rel))
        root_abs = os.path.abspath(root)
        if not ap.startswith(root_abs + os.sep) and ap != root_abs:
            raise ValueError("Path traversal")
        if os.path.isdir(ap):
            flash("Cannot download a folder.")
            return redirect(url_for("admin_user_files", username=username, p="/".join(p.split("/")[:-1])))

        if not os.path.exists(ap):
            flash("File not found.")
            return redirect(url_for("admin_user_files", username=username, p="/".join(p.split("/")[:-1])))

        filename = os.path.basename(ap)
        mime = guess_mime(filename)

        if is_encrypted_file(ap):
            gen = aesgcm_decrypt_generator(ap)
            resp = Response(gen, mimetype=mime)
            resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        else:
            from flask import send_file
            resp = send_file(
                ap,
                mimetype=mime,
                as_attachment=True,
                download_name=filename,
                conditional=True,
                max_age=0,
            )

        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception:
        flash("Download failed.")
        return redirect(url_for("admin_user_files", username=username))

# ---------------------------
# Admin approval worker (Terminal prompt)
# ---------------------------


PENDING_QUEUE = queue.Queue()

def pending_requests_bootstrap():
    """pending_requests_bootstrap.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    try:
        conn = db_connect()
        rows = conn.execute("SELECT username FROM pending_users WHERE status='pending' ORDER BY id ASC").fetchall()
        conn.close()
        for r in rows:
            try:
                PENDING_QUEUE.put_nowait(r["username"])
            except Exception:
                pass
    except Exception:
        pass

def approval_prompt(username: str):
    """Run an interactive approve/deny prompt in the *main thread*.

    Termux/Android terminals can fail to show `input()` prompts reliably when they
    happen inside background threads. This function is meant to be called from
    the main loop so the prompt always appears.
    """
    if not username:
        return
    try:
        conn = db_connect()
        row = conn.execute("""SELECT username, requested_ip, requested_at, status, pw_hash
                              FROM pending_users WHERE username=?""", (username,)).fetchone()
        if not row or row["status"] != "pending":
            conn.close()
            return

        sys.stdout.write("\n")
        sys.stdout.flush()
        prompt = (f"[ButSystem] Signup request: '{row['username']}' from {row['requested_ip']} "
                  f"at {row['requested_at']}  Approve? (y/N): ")
        try:
            ans = input(prompt).strip().lower()
        except EOFError:
            # No TTY / stdin closed.
            ans = ""

        if ans == "y":
            conn.execute("INSERT OR IGNORE INTO users(username, pw_hash, is_admin, created_at) VALUES(?,?,0,?)",
                         (row["username"], row["pw_hash"], now_z()))
            conn.execute("UPDATE pending_users SET status='approved' WHERE username=?", (username,))
            conn.commit()
            user_root(username)
            ensure_profile_row(username)
            try:
                set_profile(username, username, "", [])
            except Exception:
                pass
            sys.stdout.write(f"[ButSystem] Approved: {username}\n")
        else:
            conn.execute("UPDATE pending_users SET status='denied' WHERE username=?", (username,))
            conn.commit()
            sys.stdout.write(f"[ButSystem] Denied: {username}\n")
        sys.stdout.flush()
        conn.close()
    except Exception as e:
        log.exception("Approval prompt error: %s", e)
        try:
            sys.stdout.write("[ButSystem] Approval error (see logs).\n")
            sys.stdout.flush()
        except Exception:
            pass

def approval_worker():
    """Deprecated: kept for compatibility. Use approval_prompt() in main thread."""
    while True:
        username = PENDING_QUEUE.get()
        approval_prompt(username)

# ---------------------------
# Links: cloudflared + tor (best-effort)
# ---------------------------

def have_cmd(cmd: str) -> bool:
    """have_cmd.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    cmd: Parameter.

Returns:
    Varies.
"""
    res = _run(["bash", "-lc", f"command -v {cmd} >/dev/null 2>&1"], check=False)
    return bool(res and res.returncode == 0)

def termux_pkg_install(pkg: str) -> bool:
    """termux_pkg_install.

Internal helper function.

This docstring was added automatically to improve maintainability.

Args:
    pkg: Parameter.

Returns:
    Varies.
"""
    res = _run(["bash", "-lc", f"pkg install -y {pkg}"], check=False)
    return bool(res and res.returncode == 0)

def find_free_port(preferred=6969):
    """find_free_port.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    preferred: Parameter.

Returns:
    Varies.
"""
    def _try(p):
        """_try.

Internal helper function.

This docstring was expanded to make future maintenance easier.

Args:
    p: Parameter.

Returns:
    Varies.
"""
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", p))
            return True
        except OSError:
            return False
        finally:
            try:
                s.close()
            except Exception:
                pass
    if _try(preferred):
        return preferred
    for p in range(5000, 9000):
        if _try(p):
            return p
    return 6969

def local_ip():
    """local_ip.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

CLOUDFLARED_URL = None
CLOUDFLARED_PROC = None

TOR_ONION = None
TOR_PROC = None
TOR_HS_DIR = None

def start_cloudflared(port: int):
    """Start a Cloudflare quick tunnel (best-effort) and set CLOUDFLARED_URL.

    Uses the more robust output-parsing logic from Connections.py.
    """
    global CLOUDFLARED_URL, CLOUDFLARED_PROC
    try:
        if not have_cmd("cloudflared") and _is_termux():
            termux_pkg_install("cloudflared")
        if not have_cmd("cloudflared"):
            log.warning("cloudflared not available")
            return

        cmd = ["cloudflared", "tunnel", "--url", f"https://localhost:{port}", "--no-autoupdate", "--no-tls-verify"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        CLOUDFLARED_PROC = proc

        start_time = time.time()
        # Wait up to 180s for the public URL (some devices are slow on first run)
        while time.time() - start_time < 180:
            if proc.stdout is None:
                break
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    break
                time.sleep(0.2)
                continue
            m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if m:
                CLOUDFLARED_URL = m.group(0)
                return
        # If we get here: tunnel may still be starting; keep proc running but URL unknown
        log.warning("cloudflared tunnel started but URL was not detected in time")
    except Exception as e:
        log.exception("cloudflared start failed: %s", e)


def start_tor_hidden_service(port: int):
    """Start Tor with an ephemeral hidden service and set TOR_ONION.

    This fixes common issues with a static HiddenServiceDir (stale keys/permissions),
    by using a fresh directory each run (logic adapted from Connections.py).
    """
    global TOR_ONION, TOR_PROC, TOR_HS_DIR
    try:
        if not have_cmd("tor") and _is_termux():
            termux_pkg_install("tor")
        if not have_cmd("tor"):
            log.warning("tor not available")
            return

        # Ensure base folder exists
        os.makedirs(TOR_DIR, exist_ok=True)

        # Fresh hidden-service + data dir each run
        run_id = secrets.token_hex(4)
        data_dir = os.path.join(TOR_DIR, f"data_{run_id}")
        hs_dir = os.path.join(TOR_DIR, f"hs_{run_id}")
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(hs_dir, exist_ok=True)
        TOR_HS_DIR = hs_dir

        # Tor prefers 0700 perms
        try:
            os.chmod(data_dir, 0o700)
            os.chmod(hs_dir, 0o700)
        except Exception:
            pass

        torrc = os.path.join(TOR_DIR, f"torrc_{run_id}")
        torrc_text = "\n".join([
            f"DataDirectory {data_dir}",
            "SocksPort 0",
            "ControlPort 0",
            "Log notice stdout",
            f"HiddenServiceDir {hs_dir}",
            f"HiddenServicePort 80 127.0.0.1:{port}",
        ]) + "\n"
        with open(torrc, "w", encoding="utf-8") as f:
            f.write(torrc_text)

        proc = subprocess.Popen(
            ["tor", "-f", torrc],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        TOR_PROC = proc

        hostname_path = os.path.join(hs_dir, "hostname")
        deadline = time.time() + 180
        while time.time() < deadline:
            if proc.poll() is not None:
                log.warning("Tor exited unexpectedly while starting hidden service")
                break
            if os.path.exists(hostname_path):
                onion = open(hostname_path, "r", encoding="utf-8").read().strip()
                if onion.endswith(".onion"):
                    TOR_ONION = onion
                    return
            time.sleep(0.5)

        log.warning("Tor started but onion hostname was not found in time")
    except Exception as e:
        log.exception("tor start failed: %s", e)
# ---------------------------
# First-run: create admin (creator)
# ---------------------------

def any_admin_exists() -> bool:
    """any_admin_exists.

Internal helper function.

This docstring was added automatically to improve maintainability.

Returns:
    Varies.
"""
    conn = db_connect()
    row = conn.execute("SELECT 1 FROM users WHERE is_admin=1 LIMIT 1").fetchone()
    conn.close()
    return bool(row)

def prompt_creator_account():
    """prompt_creator_account.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    print("[ButSystem] First run: create the CREATOR (admin) account.")
    while True:
        u1 = input("Admin username: ").strip()
        u2 = input("Confirm username: ").strip()
        if u1 != u2 or not u1:
            print("Usernames do not match. Try again.\n")
            continue
        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,32}", u1):
            print("Username must be 3-32 chars: letters, numbers, _ . -\n")
            continue

        p1 = input("Admin password (min 8 chars): ").strip()
        p2 = input("Confirm password: ").strip()
        if p1 != p2 or len(p1) < 8:
            print("Passwords do not match / too short. Try again.\n")
            continue

        conn = db_connect()
        try:
            conn.execute("INSERT INTO users(username, pw_hash, is_admin, created_at, admin_device_id) VALUES(?,?,1,?,?)",
                         (u1, generate_password_hash(p1), now_z(), DEVICE_ID))
            conn.commit()
            conn.close()
            user_root(u1)
            ensure_profile_row(u1)
            try:
                set_profile(u1, u1, "", [])
            except Exception:
                pass
            print("[ButSystem] Admin created.\n")
            return
        except sqlite3.IntegrityError:
            conn.close()
            print("That username already exists. Try again.\n")

# ---------------------------
# WSGI server (threaded, quiet)
# ---------------------------

from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server
from socketserver import ThreadingMixIn

class QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        """log_message.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Args:
    self: Parameter.
    format: Parameter.
    *args: Parameter.

Returns:
    Varies.
"""
        return

class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True

_LOCAL_CERT_PATH = os.path.join(KEYS_DIR, "local_https_cert.pem")
_LOCAL_KEY_PATH = os.path.join(KEYS_DIR, "local_https_key.pem")

def _write_local_https_cert(cert_path: str, key_path: str, san_hosts: list[str]):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"ButSystem Local HTTPS")])
    san_entries = []
    seen = set()
    for raw in san_hosts:
        host = str(raw or "").strip()
        if not host or host in seen:
            continue
        seen.add(host)
        try:
            san_entries.append(x509.IPAddress(ipaddress.ip_address(host)))
            continue
        except Exception:
            pass
        san_entries.append(x509.DNSName(host))
    now = datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(private_key=key, algorithm=hashes.SHA256())
    )
    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    try:
        os.chmod(key_path, 0o600)
    except Exception:
        pass


def _ensure_local_https_material(lan_ip: str):
    sans = ["localhost", "127.0.0.1", "::1"]
    if lan_ip:
        sans.append(lan_ip)
    needs_new = True
    try:
        if os.path.exists(_LOCAL_CERT_PATH) and os.path.exists(_LOCAL_KEY_PATH):
            needs_new = False
    except Exception:
        needs_new = True
    if needs_new:
        _write_local_https_cert(_LOCAL_CERT_PATH, _LOCAL_KEY_PATH, sans)
    return _LOCAL_CERT_PATH, _LOCAL_KEY_PATH


def start_server(host: str, port: int, use_https: bool = True, lan_ip: str = ""):
    httpd = make_server(host, port, app, server_class=ThreadingWSGIServer, handler_class=QuietHandler)
    if use_https:
        cert_path, key_path = _ensure_local_https_material(lan_ip)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    return httpd

# ---------------------------
# Main
# ---------------------------

def clear_screen():
    """clear_screen.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    try:
        os.system("clear")
    except Exception:
        pass

def main():
    """main.

Route handler or application helper.

This docstring was expanded to make future maintenance easier.

Returns:
    Varies.
"""
    if not any_admin_exists():
        prompt_creator_account()

    pending_requests_bootstrap()
    # approval prompts are handled in the main loop (TTY-safe)

    port = find_free_port(6969)
    host = "0.0.0.0"
    lan = local_ip()
    httpd = start_server(host, port, use_https=True, lan_ip=lan)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    threading.Thread(target=start_cloudflared, args=(port,), daemon=True).start()
    threading.Thread(target=start_tor_hidden_service, args=(port,), daemon=True).start()

    local_url = f"https://{lan}:{port}"
    localhost_url = f"https://127.0.0.1:{port}"

    deadline = time.time() + 180
    while time.time() < deadline:
        if (CLOUDFLARED_URL is not None) and (TOR_ONION is not None):
            break
        time.sleep(0.2)

    clear_screen()

    # Print ONLY the generated links (as requested earlier)
    print(f"LOCAL:       {local_url}")
    print(f"LOCALHOST:   {localhost_url}")
    print(f"CLOUDFLARED: {CLOUDFLARED_URL or ('UNAVAILABLE (see ' + LOG_PATH + ')')}")
    print(f"TOR:         {('http://' + TOR_ONION) if TOR_ONION else ('UNAVAILABLE (see ' + LOG_PATH + ')')}")

    try:
        while True:
            # Poll for access requests and show y/N prompt in the terminal.
            try:
                username = PENDING_QUEUE.get_nowait()
            except queue.Empty:
                username = None
            if username:
                approval_prompt(username)
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    try:
        httpd.shutdown()
    except Exception:
        pass


# ---------------------------
# Reports + Discussion (added)
# ---------------------------
# Report upload helpers (size/path protections kept; file-type blocking disabled per request).
_REPORT_ALLOWED_EXTS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp",
    ".pdf", ".txt", ".csv",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".rar", ".7z",
}
_REPORT_DENY_EXTS = {
    ".html", ".htm", ".xhtml", ".svg", ".xml", ".js", ".mjs",
    ".exe", ".msi", ".dll", ".bat", ".cmd", ".com", ".scr",
    ".ps1", ".sh", ".php", ".py", ".pl", ".jar", ".apk",
}
_REPORT_ALLOWED_MIMES = {
    "application/pdf", "text/plain", "text/csv",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/zip", "application/x-zip-compressed",
    "application/x-rar-compressed", "application/vnd.rar",
    "application/x-7z-compressed",
}
_REPORT_DENY_MIMES = {
    "text/html", "application/xhtml+xml", "image/svg+xml", "application/xml", "text/xml",
    "application/x-msdownload", "application/x-dosexec", "application/java-archive",
    "application/x-sh", "application/x-shellscript", "text/javascript", "application/javascript",
}
_REPORT_MAX_ATTACH_PER_REQUEST = 10


# Reusable validation for legacy upload endpoints (Profiler / Files / Chat / PFP).
_CHAT_MEDIA_EXTS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp",
    ".mp4", ".webm", ".mov", ".m4v", ".avi", ".mkv",
    ".mp3", ".wav", ".ogg", ".oga", ".m4a", ".aac", ".flac", ".opus",
}
_CHAT_MEDIA_MIME_PREFIXES = ("image/", "audio/", "video/")
_VOICE_ALLOWED_EXTS = {".webm", ".ogg", ".oga", ".wav", ".mp3", ".m4a", ".aac", ".flac", ".opus", ".mp4"}
_VOICE_ALLOWED_MIMES = {
    "audio/webm", "video/webm", "audio/ogg", "application/ogg",
    "audio/wav", "audio/x-wav", "audio/wave",
    "audio/mpeg", "audio/mp3",
    "audio/mp4", "audio/x-m4a", "audio/aac",
    "audio/flac", "audio/x-flac", "audio/opus",
}
_PFP_ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
_PFP_DENY_MIMES = {"image/svg+xml"}

def _upload_filename_mime(file_storage, default_name: str = "file") -> Tuple[str, str, str]:
    """Return (safe_filename, ext, normalized_mime) for an uploaded file."""
    raw_name = (getattr(file_storage, "filename", "") or "").strip()
    filename = secure_filename(raw_name) or default_name
    ext = pathlib.Path(filename).suffix.lower()
    mime = (getattr(file_storage, "mimetype", "") or "").strip().lower()
    if not mime or mime == "application/octet-stream":
        mime = (guess_mime(filename) or "application/octet-stream").lower()
    return filename, ext, mime

def _reject_risky_upload_type(filename: str, mime: str) -> None:
    """File-type blocking disabled per user request; kept as a no-op hook."""
    return None

def _validate_vault_upload_filename(filename: str, mime: Optional[str] = None) -> str:
    """Validate/sanitize a vault filename (no file-type blocking)."""
    safe_name = secure_filename(filename or "") or "file"
    return safe_name

def _validate_chat_file_upload(file_storage) -> Tuple[str, str]:
    """Validate a chat attachment (DM/group file/gif) and return (filename, mime)."""
    filename, _ext, mime = _upload_filename_mime(file_storage, default_name="file")
    # File-type blocking intentionally disabled per user request; keep filename sanitization.
    return filename, mime

def _validate_chat_voice_upload(file_storage) -> str:
    """Validate a voice note upload and return normalized MIME."""
    filename, ext, mime = _upload_filename_mime(file_storage, default_name="voice.webm")
    _reject_risky_upload_type(filename, mime)
    if not (ext in _VOICE_ALLOWED_EXTS or mime in _VOICE_ALLOWED_MIMES or mime.startswith("audio/")):
        raise ValueError("unsupported_voice_type")
    if mime.startswith("video/webm"):
        mime = "audio/webm"
    return mime

def _validate_profile_pic_upload(file_storage) -> str:
    """Validate profile picture upload type and return normalized MIME."""
    filename, ext, mime = _upload_filename_mime(file_storage, default_name="avatar")
    if mime in _PFP_DENY_MIMES:
        raise ValueError("forbidden_type")
    if not mime.startswith("image/"):
        raise ValueError("image_only")
    if ext and ext not in _PFP_ALLOWED_EXTS:
        # Keep profile pics to common raster formats only (no SVG/HTML/XBM/etc).
        raise ValueError("unsupported_type")
    return mime

def _validate_report_upload(file_storage):
    """Validate report attachment size and return (safe_name, mime)."""
    if not file_storage or not getattr(file_storage, "filename", ""):
        raise ValueError("empty")
    filename = secure_filename(getattr(file_storage, "filename", "") or "") or "attachment"
    mime = (getattr(file_storage, "mimetype", "") or "").strip().lower()
    if not mime or mime == "application/octet-stream":
        mime = (guess_mime(filename) or "application/octet-stream").lower()
    # File-type blocking intentionally disabled per user request; keep size/path protections.
    try:
        size = _filestorage_size(file_storage)
        if size is not None and int(size) > CHAT_MAX_BYTES:
            raise ValueError("too_large")
    except ValueError:
        raise
    except Exception:
        pass
    return filename, mime

def _safe_report_att_path(stored_path: str) -> Optional[str]:
    """Return a verified absolute path for report attachments, else None."""
    try:
        if not stored_path:
            return None
        real = os.path.realpath(str(stored_path))
        base = os.path.realpath(ATT_DIR)
        if real == base or not real.startswith(base + os.sep):
            return None
        bn = os.path.basename(real)
        if not bn.startswith("report_att_"):
            return None
        if not os.path.isfile(real):
            return None
        return real
    except Exception:
        return None

_discussion_send_lock = threading.Lock()
_discussion_last_send_ts = {}

def _discussion_local_cooldown_ok(username: str, cooldown_s: float = 5.0):
    """Process-local anti-race throttle for discussion sends."""
    now = time.time()
    with _discussion_send_lock:
        last = float(_discussion_last_send_ts.get(username) or 0.0)
        wait = cooldown_s - (now - last)
        if wait > 0:
            return False, wait
        return True, 0.0

def _discussion_mark_sent(username: str):
    with _discussion_send_lock:
        _discussion_last_send_ts[username] = time.time()

def _feature_tables_init():
    """Initialize optional feature tables (reports + public discussion).

    This function is safe to call multiple times. It also performs lightweight
    migrations for older installs (adds missing columns / tables).
    """
    conn = db_connect()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT NOT NULL,
                title_enc TEXT NOT NULL,
                subject_enc TEXT NOT NULL,
                text_enc TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS report_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                filename_enc TEXT,
                mime_enc TEXT,
                stored_path TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            /* Public discussion (chat-style, like DMs but without calls) */
            CREATE TABLE IF NOT EXISTS discussion_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                body_enc TEXT NOT NULL,
                created_at TEXT NOT NULL,
                has_voice INTEGER NOT NULL DEFAULT 0,
                has_file INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS discussion_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                msg_id INTEGER NOT NULL,
                filename TEXT,
                mime TEXT,
                stored_path TEXT,
                size INTEGER,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS discussion_voice (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                msg_id INTEGER NOT NULL,
                mime TEXT,
                stored_path TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )

        # Lightweight migrations for older DBs (columns may be missing).
        try:
            conn.execute("ALTER TABLE discussion_messages ADD COLUMN has_voice INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE discussion_messages ADD COLUMN has_file INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass

        conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass

def _report_store_attachment(rid: int, file_storage):
    if not file_storage or not getattr(file_storage, "filename", ""):
        return
    filename, mime = _validate_report_upload(file_storage)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO report_attachments(report_id, filename_enc, mime_enc, stored_path, created_at) VALUES(?,?,?,?,?)",
        (rid, aesgcm_encrypt_text(filename), aesgcm_encrypt_text(mime), "PENDING", now_z()),
    )
    aid = cur.lastrowid
    sp = os.path.join(ATT_DIR, f"report_att_{aid}.bin")
    try:
        size = _save_plain_upload(file_storage, sp)
        if int(size) > CHAT_MAX_BYTES:
            try:
                os.remove(sp)
            except Exception:
                pass
            conn.execute("DELETE FROM report_attachments WHERE id=?", (aid,))
            conn.commit()
            raise ValueError("too_large")
        conn.execute("UPDATE report_attachments SET stored_path=? WHERE id=?", (sp, aid))
        conn.commit()
    finally:
        conn.close()


def _report_decode(row):
    try:
        title = aesgcm_decrypt_text(row["title_enc"])
    except Exception:
        title = "[decrypt failed]"
    try:
        subject = aesgcm_decrypt_text(row["subject_enc"])
    except Exception:
        subject = "[decrypt failed]"
    try:
        text = aesgcm_decrypt_text(row["text_enc"])
    except Exception:
        text = "[decrypt failed]"
    return {
        "id": int(row["id"]),
        "owner": row["owner"],
        "title": title,
        "subject": subject,
        "text": text,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"] or row["created_at"],
    }


@app.route("/reports")
@login_required
def reports():
    _feature_tables_init()
    me = current_user()
    q_raw = (request.args.get("q") or "").strip()
    q = q_raw.lower()
    conn = db_connect()
    rows = conn.execute("SELECT * FROM reports ORDER BY id DESC LIMIT 300").fetchall()
    items = []
    for r in rows:
        d = _report_decode(r)
        if q and q not in (f"{d['title']} {d['subject']} {d['text']} {d['owner']}".lower()):
            continue
        att_rows = conn.execute("SELECT id FROM report_attachments WHERE report_id=? ORDER BY id ASC", (d["id"],)).fetchall()
        d["attachments"] = [int(a["id"]) for a in att_rows]
        d["updated_at_local"] = _local_time_str(d["updated_at"])
        items.append(d)
    conn.close()
    class Obj:
        def __init__(self, d):
            self.__dict__.update(d)
    return render_template("reports.html", title="Reports", items=[Obj(i) for i in items], q=q_raw, me=me)


@app.route("/reports/create", methods=["POST"])
@login_required
def report_create():
    _feature_tables_init()
    me = current_user()
    title = (request.form.get("title") or "").strip()[:200]
    subject = (request.form.get("subject") or "").strip()[:300]
    text = (request.form.get("text") or "").strip()[:20000]
    if not title or not subject or not text:
        flash("Report title, subject and text are required.")
        return redirect(url_for("reports"))
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reports(owner, title_enc, subject_enc, text_enc, created_at, updated_at) VALUES(?,?,?,?,?,?)",
        (me, aesgcm_encrypt_text(title), aesgcm_encrypt_text(subject), aesgcm_encrypt_text(text), now_z(), now_z()),
    )
    rid = cur.lastrowid
    conn.commit()
    conn.close()
    upload_errors = 0
    upload_ok = 0
    for idx, f in enumerate((request.files.getlist("files") or []), start=1):
        if idx > _REPORT_MAX_ATTACH_PER_REQUEST:
            upload_errors += 1
            break
        if f and f.filename:
            try:
                _report_store_attachment(rid, f)
                upload_ok += 1
            except Exception as e:
                upload_errors += 1
                log.warning("Report attachment rejected/failed (create): %s", e)
    if upload_errors:
        flash("Some attachments were rejected (type/size) or failed to upload.")
    flash("Report created.")
    return redirect(url_for("reports"))


@app.route("/reports/<int:rid>/edit", methods=["POST"])
@login_required
def report_edit(rid: int):
    _feature_tables_init()
    me = current_user()
    conn = db_connect()
    row = conn.execute("SELECT * FROM reports WHERE id=?", (rid,)).fetchone()
    if not row:
        conn.close(); abort(404)
    if row["owner"] != me and not user_is_admin(me):
        conn.close(); abort(403)
    title = (request.form.get("title") or "").strip()[:200]
    subject = (request.form.get("subject") or "").strip()[:300]
    text = (request.form.get("text") or "").strip()[:20000]
    if not title or not subject or not text:
        conn.close(); flash("All report fields are required."); return redirect(url_for("reports"))
    conn.execute(
        "UPDATE reports SET title_enc=?, subject_enc=?, text_enc=?, updated_at=? WHERE id=?",
        (aesgcm_encrypt_text(title), aesgcm_encrypt_text(subject), aesgcm_encrypt_text(text), now_z(), rid),
    )
    conn.commit(); conn.close()
    upload_errors = 0
    upload_ok = 0
    for idx, f in enumerate((request.files.getlist("files") or []), start=1):
        if idx > _REPORT_MAX_ATTACH_PER_REQUEST:
            upload_errors += 1
            break
        if f and f.filename:
            try:
                _report_store_attachment(rid, f)
                upload_ok += 1
            except Exception as e:
                upload_errors += 1
                log.warning("Report attachment rejected/failed (edit): %s", e)
    if upload_errors:
        flash("Some attachments were rejected (type/size) or failed to upload.")
    flash("Report updated.")
    return redirect(url_for("reports"))


@app.route("/reports/<int:rid>/delete", methods=["POST"])
@login_required
def report_delete(rid: int):
    _feature_tables_init()
    if not user_is_admin(current_user()):
        abort(403)
    conn = db_connect()
    rows = conn.execute("SELECT stored_path FROM report_attachments WHERE report_id=?", (rid,)).fetchall()
    conn.execute("DELETE FROM report_attachments WHERE report_id=?", (rid,))
    conn.execute("DELETE FROM reports WHERE id=?", (rid,))
    conn.commit(); conn.close()
    for r in rows:
        try:
            if r["stored_path"] and os.path.exists(r["stored_path"]):
                os.remove(r["stored_path"])
        except Exception:
            pass
    flash("Report deleted.")
    return redirect(url_for("reports"))


@app.route("/reports/att/<int:aid>/download")
@login_required
def report_att_download(aid: int):
    _feature_tables_init()
    conn = db_connect()
    row = conn.execute(
        "SELECT a.id, a.filename_enc, a.mime_enc, a.stored_path, a.report_id FROM report_attachments a JOIN reports r ON r.id=a.report_id WHERE a.id=?",
        (aid,),
    ).fetchone()
    conn.close()
    safe_path = _safe_report_att_path(row["stored_path"]) if row else None
    if not row or not safe_path:
        abort(404)
    try:
        filename = aesgcm_decrypt_text(row["filename_enc"])
    except Exception:
        filename = "attachment"
    try:
        mime = aesgcm_decrypt_text(row["mime_enc"])
    except Exception:
        mime = "application/octet-stream"
    filename = secure_filename(filename or "attachment") or "attachment"
    resp = send_file(safe_path, mimetype=mime, as_attachment=True, download_name=filename, conditional=True, max_age=0)
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Download-Options"] = "noopen"
    return resp


_DISCUSS_ROW_TEMPLATE = r"""
<div class="msg-row {{ 'me' if m.sender==me else 'them' }}">
  <div class="bubble {{ 'me' if m.sender==me else 'them' }}" data-mid="{{ m.id }}" data-kind="{{ m.kind }}" data-sender="{{ m.sender }}">
    {% if m.sender!=me %}<div class="discuss-sender">@{{ m.sender }}</div>{% endif %}
    {% if m.kind == "text" %}
      <span class="msg-text">{{ m.body }}</span>
    {% elif m.kind == "voice" %}
      <audio controls preload="metadata">
        <source src="{{ url_for('discussion_voice_stream', vid=m.voice_id) }}" type="{{ m.voice_mime }}">
      </audio>
    {% elif m.kind == "file" %}
      {% if m.file_is_image %}
        <img src="{{ url_for('discussion_file_stream', fid=m.file_id) }}" alt="{{ m.file_name }}"/>
      {% elif m.file_is_video %}
        <video controls playsinline preload="metadata">
          <source src="{{ url_for('discussion_file_stream', fid=m.file_id) }}" type="{{ m.file_mime }}">
        </video>
      {% elif m.file_is_audio %}
        <audio controls preload="metadata">
          <source src="{{ url_for('discussion_file_stream', fid=m.file_id) }}" type="{{ m.file_mime }}">
        </audio>
      {% else %}
        <a class="file-chip" href="{{ url_for('discussion_file_download', fid=m.file_id) }}">📎 {{ m.file_name }}</a>
        <div class="small-muted mt-1">{{ m.file_size_h }}</div>
      {% endif %}
    {% else %}
      <span class="msg-text">{{ m.body }}</span>
    {% endif %}
  </div>
  <div class="msg-meta">
    <span class="ts" data-utc="{{ m.created_at_utc }}">{{ m.created_at_local }}</span>
  </div>
</div>
"""

def _discussion_build_message_dict(conn, r, me: str) -> Dict[str, Any]:
    """Build a Discussion message view dict (like DMs)."""
    v = None
    f = None
    try:
        if int(r.get("has_voice") or 0):
            v = conn.execute("SELECT id, mime FROM discussion_voice WHERE msg_id=? ORDER BY id DESC LIMIT 1", (r["id"],)).fetchone()
    except Exception:
        v = None
    try:
        if int(r.get("has_file") or 0):
            f = conn.execute("SELECT id, filename, mime, size FROM discussion_files WHERE msg_id=? ORDER BY id DESC LIMIT 1", (r["id"],)).fetchone()
    except Exception:
        f = None

    try:
        body = aesgcm_decrypt_text(r["body_enc"])
    except Exception:
        body = "[decrypt failed]"

    kind = ("voice" if v else ("file" if f else "text"))

    return {
        "id": int(r["id"]),
        "sender": r["sender"],
        "kind": kind,
        "body": body if kind == "text" else (body if body else ""),
        "created_at_local": _local_time_str(r["created_at"]),
        "created_at_utc": r["created_at"],
        "voice_id": v["id"] if v else None,
        "voice_mime": v["mime"] if v else "audio/webm",
        "file_id": f["id"] if f else None,
        "file_name": f["filename"] if f else None,
        "file_mime": f["mime"] if f else None,
        "file_size_h": human_size(int(f["size"])) if (f and f["size"] is not None) else "",
        "file_is_image": True if (f and (f["mime"] or "").startswith("image/")) else False,
        "file_is_video": True if (f and (f["mime"] or "").startswith("video/")) else False,
        "file_is_audio": True if (f and (f["mime"] or "").startswith("audio/")) else False,
    }


def _render_discussion_row_html(m: Dict[str, Any], me: str) -> str:
    return render_template_string(_DISCUSS_ROW_TEMPLATE, m=m, me=me)


@app.route("/discussion")
@login_required
def discussion():
    _feature_tables_init()
    q_raw = (request.args.get("q") or "").strip()
    q = q_raw.lower()
    me = current_user()
    conn = db_connect()
    try:
        rows = conn.execute(
            "SELECT id, sender, body_enc, created_at, has_voice, has_file FROM discussion_messages ORDER BY id DESC LIMIT 300"
        ).fetchall()
        items = []
        for r in rows:
            rr = dict(r)
            msg = _discussion_build_message_dict(conn, rr, me)
            # server-side filter for initial page render
            if q:
                hay = f"{msg.get('sender','')} {msg.get('body','')}".lower()
                if q not in hay:
                    continue
            items.append(msg)
        items.reverse()
    finally:
        conn.close()

    class Obj:
        def __init__(self, d):
            self.__dict__.update(d)

    return render_template(
        "discussion.html",
        title="Discussion",
        items=[Obj(x) for x in items],
        q=q_raw,
        me=me,
    )


@app.route("/discussion/send", methods=["POST"])
@login_required
def discussion_send():
    """Send a discussion message (text, file, GIF, and/or voice)."""
    _feature_tables_init()
    me = current_user()

    is_ajax = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in (request.headers.get("Accept", ""))
    )

    body = (request.form.get("body") or "").strip()
    voice = request.files.get("voice")
    upfile = request.files.get("file")
    gif = request.files.get("gif")
    gif_url = (request.form.get("gif_url") or "").strip()

    # Size limits (33MB) for chat stability.
    if voice and getattr(voice, "filename", ""):
        vsz = _filestorage_size(voice)
        if vsz is not None and vsz > CHAT_MAX_BYTES:
            if is_ajax:
                return jsonify(ok=False, error=_("Voice message too large (max 33MB).")), 413
            flash(_("Voice message too large (max 33MB)."))
            return redirect(url_for("discussion"))
    if upfile and getattr(upfile, "filename", ""):
        fsz = _filestorage_size(upfile)
        if fsz is not None and fsz > CHAT_MAX_BYTES:
            if is_ajax:
                return jsonify(ok=False, error=_("File too large (max 33MB).")), 413
            flash(_("File too large (max 33MB)."))
            return redirect(url_for("discussion"))
    if gif and getattr(gif, "filename", ""):
        gsz = _filestorage_size(gif)
        if gsz is not None and gsz > CHAT_MAX_BYTES:
            if is_ajax:
                return jsonify(ok=False, error=_("GIF too large (max 33MB).")), 413
            flash(_("GIF too large (max 33MB)."))
            return redirect(url_for("discussion"))

    chosen_file = (
        upfile if (upfile and getattr(upfile, "filename", "")) else (gif if (gif and getattr(gif, "filename", "")) else None)
    )

    if voice and getattr(voice, "filename", ""):
        try:
            _validate_chat_voice_upload(voice)
        except ValueError as ve:
            msg = _("Unsupported voice file type.")
            if str(ve) == "forbidden_type":
                msg = _("Forbidden file type.")
            if is_ajax:
                return jsonify(ok=False, error=msg), 400
            flash(msg)
            return redirect(url_for("discussion"))

    if chosen_file and getattr(chosen_file, "filename", ""):
        try:
            _validate_chat_file_upload(chosen_file)
        except ValueError as ve:
            msg = _("Unsupported file type.")
            if str(ve) == "forbidden_type":
                msg = _("Forbidden file type.")
            if is_ajax:
                return jsonify(ok=False, error=msg), 400
            flash(msg)
            return redirect(url_for("discussion"))

    has_voice = bool(voice and getattr(voice, "filename", ""))
    has_file = bool(chosen_file and getattr(chosen_file, "filename", ""))
    has_gif_url = bool(gif_url)

    if (not body) and (not has_voice) and (not has_file) and (not has_gif_url):
        if is_ajax:
            return jsonify(ok=False, error=_("Write a message or attach voice/file.")), 400
        flash(_("Write a message or attach voice/file."))
        return redirect(url_for("discussion"))

    # Anti-spam cooldown (server-side). UI does not show the cooldown banner.
    ok_local, _wait_local = _discussion_local_cooldown_ok(me, 5.0)
    if not ok_local:
        if is_ajax:
            return jsonify(ok=False, error=_("Please wait 5 seconds before sending another discussion message.")), 429
        flash(_("Please wait 5 seconds before sending another discussion message."))
        return redirect(url_for("discussion"))

    conn = db_connect()
    saved_paths = []
    try:
        last = conn.execute(
            "SELECT created_at FROM discussion_messages WHERE sender=? ORDER BY id DESC LIMIT 1",
            (me,),
        ).fetchone()
        if last:
            try:
                dt = datetime.fromisoformat(str(last["created_at"]).replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if (datetime.now(timezone.utc) - dt).total_seconds() < 5:
                    if is_ajax:
                        return jsonify(ok=False, error=_("Please wait 5 seconds before sending another discussion message.")), 429
                    flash(_("Please wait 5 seconds before sending another discussion message."))
                    return redirect(url_for("discussion"))
            except Exception:
                pass

        cur = conn.cursor()
        cur.execute(
            "INSERT INTO discussion_messages(sender, body_enc, created_at, has_voice, has_file) VALUES(?,?,?,?,?)",
            (
                me,
                aesgcm_encrypt_text(body or ""),
                now_z(),
                1 if has_voice else 0,
                1 if (has_file or has_gif_url) else 0,
            ),
        )
        msg_id = cur.lastrowid

        if has_voice:
            _, _, sp = _discussion_store_voice_tx(conn, msg_id, voice)
            saved_paths.append(sp)

        if has_file:
            info = _discussion_store_file_tx(conn, msg_id, chosen_file)
            saved_paths.append(info["stored_path"])

        if (not has_file) and has_gif_url:
            info = _discussion_store_remote_gif_tx(conn, msg_id, gif_url)
            saved_paths.append(info["stored_path"])

        conn.commit()
        _discussion_mark_sent(me)

        if is_ajax:
            r = conn.execute(
                "SELECT id, sender, body_enc, created_at, has_voice, has_file FROM discussion_messages WHERE id=?",
                (msg_id,),
            ).fetchone()
            if r is None:
                return jsonify(ok=False, error="not_found"), 404
            msg = _discussion_build_message_dict(conn, dict(r), me)
            html_row = _render_discussion_row_html(msg, me)
            return jsonify(ok=True, id=msg_id, html=html_row)

        return redirect(url_for("discussion"))

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        for sp in saved_paths:
            try:
                if sp and os.path.exists(sp):
                    os.remove(sp)
            except Exception:
                pass
        log.exception("discussion_send failed: %s", e)
        if is_ajax:
            return jsonify(ok=False, error=_("Send failed.")), 500
        flash(_("Send failed."))
        return redirect(url_for("discussion"))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.route("/api/discussion/since")
@login_required
def api_discussion_since():
    _feature_tables_init()
    me = current_user()
    try:
        since_id = int(request.args.get("id") or 0)
    except Exception:
        since_id = 0
    conn = db_connect()
    try:
        rows = conn.execute(
            "SELECT id, sender, body_enc, created_at, has_voice, has_file FROM discussion_messages WHERE id>? ORDER BY id ASC LIMIT 120",
            (since_id,),
        ).fetchall()
        out = []
        for r in rows:
            msg = _discussion_build_message_dict(conn, dict(r), me)
            html_row = _render_discussion_row_html(msg, me)
            out.append({"id": int(msg["id"]), "sender": msg["sender"], "html": html_row})
    finally:
        conn.close()

    return jsonify({"ok": True, "messages": out})

@app.route("/api/presence")
@login_required
def api_presence():
    me = current_user()
    scope = current_scope()
    try:
        online = online_usernames(scope)
    except Exception:
        online = set()
    conn = db_connect()
    rows = conn.execute("SELECT username FROM users WHERE username<>?", (me,)).fetchall()
    conn.close()
    items = {r["username"]: (r["username"] in online) for r in rows}
    return jsonify({"ok": True, "items": items, "server_now": now_z()})


TEMPLATES["reports.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="d-flex align-items-center justify-content-between gap-2 flex-wrap mb-3"><h3 class="mb-0">{{ _('Reports') }}</h3></div>
<div class="row g-3">
  <div class="col-12 col-lg-5">
    <div class="card-soft p-3">
      <div class="fw-semibold mb-2">{{ _('Create report') }}</div>
      <form method="post" action="{{ url_for('report_create') }}" enctype="multipart/form-data">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <input class="form-control mb-2" name="title" placeholder="{{ _('Title') }}" required>
        <input class="form-control mb-2" name="subject" placeholder="{{ _('Subject') }}" required>
        <textarea class="form-control mb-2" name="text" rows="5" placeholder="{{ _('Text') }}" required></textarea>
        <input class="form-control mb-2" type="file" name="files" multiple>
        <button class="btn btn-accent" type="submit">{{ _('Create report') }}</button>
      </form>
    </div>
  </div>
  <div class="col-12 col-lg-7">
    <div class="card-soft p-3">
      <form method="get" class="d-flex gap-2 mb-3">
        <input class="form-control" name="q" value="{{ q }}" placeholder="{{ _('Search reports...') }}">
        <button class="btn btn-ghost" type="submit">{{ _('Search') }}</button>
      </form>
      {% for r in items %}
        <div class="card-soft p-3 mb-3">
          <div class="fw-bold">{{ r.title }}</div>
          <div class="small-muted">{{ _('Subject') }}: {{ r.subject }}</div>
          <div class="small-muted">{{ _('By') }} @{{ r.owner }} • {{ r.updated_at_local if r.updated_at_local is defined else r.updated_at }}</div>
          <div class="mt-2" style="white-space:pre-wrap">{{ r.text }}</div>
          <div class="mt-2">
            {% for aid in r.attachments %}<a class="btn btn-sm btn-ghost me-2 mb-2" href="{{ url_for('report_att_download', aid=aid) }}">{{ _('Attachment') }} #{{ aid }}</a>{% endfor %}
          </div>
          {% if r.owner == me or is_admin %}
          <details class="mt-2"><summary>{{ _('Edit report') }}</summary>
            <form method="post" action="{{ url_for('report_edit', rid=r.id) }}" enctype="multipart/form-data" class="mt-2">
              <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
              <input class="form-control mb-2" name="title" value="{{ r.title }}" required>
              <input class="form-control mb-2" name="subject" value="{{ r.subject }}" required>
              <textarea class="form-control mb-2" name="text" rows="4" required>{{ r.text }}</textarea>
              <input class="form-control mb-2" type="file" name="files" multiple>
              <button class="btn btn-ghost btn-sm" type="submit">{{ _('Save edit') }}</button>
            </form>
          </details>
          {% endif %}
          {% if is_admin %}
          <form method="post" action="{{ url_for('report_delete', rid=r.id) }}" class="mt-2" onsubmit="return confirm('{{ _('Delete report?') }}')">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <button class="btn btn-danger btn-sm" type="submit">{{ _('Delete report') }}</button>
          </form>
          {% endif %}
        </div>
      {% else %}
        <div class="small-muted">{{ _('No reports found.') }}</div>
      {% endfor %}
    </div>
  </div>
</div>
{% endblock %}
"""


TEMPLATES["discussion.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="chat-page">
  <div class="chat-top">
    <div class="card-soft p-3 discussion-header">
      <div class="d-flex align-items-start justify-content-between gap-2 flex-wrap">
        <div class="min-w-0">
          <h4 class="mb-0">{{ _('Discussion') }}</h4>
          <div class="small-muted">{{ _('Public room (text).') }}</div>
        </div>

        <form method="get" class="d-flex gap-2 discussion-search">
          <input class="form-control" name="q" value="{{ q }}" placeholder="{{ _('Search discussion...') }}" autocomplete="off">
          <button class="btn btn-ghost" type="submit">{{ _('Search') }}</button>
        </form>
      </div>
    </div>
  </div>

  <div class="chat-messages" id="discussionBox" aria-live="polite">
    {% for m in items %}
      <div class="msg-row {{ 'me' if m.sender==me else 'them' }}">
        <div class="bubble {{ 'me' if m.sender==me else 'them' }}" data-mid="{{ m.id }}" data-kind="{{ m.kind }}" data-sender="{{ m.sender }}">
          {% if m.sender!=me %}<div class="discuss-sender">@{{ m.sender }}</div>{% endif %}

          {% if m.kind == "text" %}
            <span class="msg-text">{{ m.body }}</span>
          {% elif m.kind == "voice" %}
            <audio controls preload="metadata">
              <source src="{{ url_for('discussion_voice_stream', vid=m.voice_id) }}" type="{{ m.voice_mime }}">
            </audio>
          {% elif m.kind == "file" %}
            {% if m.file_is_image %}
              <img src="{{ url_for('discussion_file_stream', fid=m.file_id) }}" alt="{{ m.file_name }}"/>
            {% elif m.file_is_video %}
              <video controls playsinline preload="metadata">
                <source src="{{ url_for('discussion_file_stream', fid=m.file_id) }}" type="{{ m.file_mime }}">
              </video>
            {% elif m.file_is_audio %}
              <audio controls preload="metadata">
                <source src="{{ url_for('discussion_file_stream', fid=m.file_id) }}" type="{{ m.file_mime }}">
              </audio>
            {% else %}
              <a class="file-chip" href="{{ url_for('discussion_file_download', fid=m.file_id) }}">📎 {{ m.file_name }}</a>
              <div class="small-muted mt-1">{{ m.file_size_h }}</div>
            {% endif %}
          {% else %}
            <span class="msg-text">{{ m.body }}</span>
          {% endif %}
        </div>

        <div class="msg-meta">
          <span class="ts" data-utc="{{ m.created_at_utc }}">{{ m.created_at_local }}</span>
        </div>
      </div>
    {% else %}
      <div class="small-muted text-center mt-2">{{ _('No messages yet.') }}</div>
    {% endfor %}
    <div id="bottomSentinel" style="height:1px"></div>
  </div>

  <div class="chat-composer">
    <form method="post" action="{{ url_for('discussion_send') }}" enctype="multipart/form-data" id="discussionSendForm" autocomplete="off">
      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
      <input type="hidden" name="gif_url" id="gifUrl" value="">
      <div class="composer-row">
        <textarea class="form-control msg-input" name="body" id="discussionInput" rows="1" placeholder="{{ _('Message...') }}" style="resize:none;"></textarea>

        <input class="file-hidden" type="file" name="file" id="fileInput">
        <label class="btn btn-ghost btn-sm icon-only mb-0" for="fileInput" title="{{ _('Send file') }}" aria-label="{{ _('Send file') }}">📎</label>

        <button class="btn btn-ghost btn-sm gif-text-btn" type="button" id="gifBtn" title="{{ _('GIFs') }}" aria-label="{{ _('GIFs') }}">GIF</button>

        <input class="file-hidden" type="file" name="voice" id="voiceInput" accept="audio/*">
        <button class="btn btn-ghost btn-sm icon-only" type="button" id="recBtn" title="{{ _('Send voice message') }}" aria-label="{{ _('Send voice message') }}">🎙️</button>

        <button class="btn btn-accent btn-send" type="submit" id="discussionSendBtn" aria-label="{{ _('Send') }}" title="{{ _('Send') }}">➡️</button>
      </div>
      <div class="small-muted mt-1 composer-status" id="recStatus" aria-live="polite"></div>
    </form>
  </div>
</div>

<!-- GIF picker modal -->
<div class="modal fade" id="gifModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered modal-lg">
    <div class="modal-content card-soft">
      <div class="modal-header border-0">
        <h5 class="modal-title">{{ _('GIFs') }}</h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="{{ _('Close') }}"></button>
      </div>
      <div class="modal-body">
        <div class="d-flex gap-2 mb-2">
          <input class="form-control" id="gifSearch" placeholder="{{ _('Search GIFs...') }}">
          <button class="btn btn-ghost" type="button" id="gifSearchBtn">{{ _('Search') }}</button>
        </div>
        <div class="small-muted mb-2" id="gifHint"></div>
        <div id="gifGrid" class="gif-grid"></div>
      </div>
    </div>
  </div>
</div>

<style>
  /* Discussion polish + mobile fixes */
  .discuss-sender{ font-size:.78rem; opacity:.85; margin-bottom:2px; }
  .discussion-header{ padding: .9rem; }
  .discussion-search{ flex: 1 1 auto; min-width: 240px; justify-content:flex-end; }
  @media (max-width: 576px){
    .chat-top{ padding: 10px 10px 0 10px; }
    .discussion-search{ width:100%; justify-content:stretch; }
    .discussion-search input{ flex:1 1 auto; min-width:0; }
    .discussion-search button{ white-space:nowrap; }
    .composer-row{ gap:.35rem; }
    .gif-text-btn{ padding: .22rem .42rem; font-size: .78rem; }
    .composer-row .btn{ padding: .22rem .42rem; }
    .btn-send{ padding: .26rem .52rem; }
  }
  @media (min-width: 992px){
    .bubble{ max-width: 72%; }
  }
</style>
{% endblock %}

{% block scripts %}
<script nonce="{{ csp_nonce }}">
(function(){
  const box = document.getElementById("discussionBox");
  const form = document.getElementById("discussionSendForm");
  const sendBtn = document.getElementById("discussionSendBtn");
  const bodyTa = document.getElementById("discussionInput");
  const fileInput = document.getElementById("fileInput");
  const voiceInput = document.getElementById("voiceInput");
  const gifUrl = document.getElementById("gifUrl");
  const recBtn = document.getElementById("recBtn");
  const recStatus = document.getElementById("recStatus");
  const bottom = document.getElementById("bottomSentinel");

  const MSG_SEND_FAIL = {{ _("Send failed.")|tojson }};
  const MSG_VOICE_UPLOAD_FAIL = {{ _("Voice upload failed.")|tojson }};
  const MSG_RECORDING = {{ _("Recording… tap again to stop")|tojson }};
  const MSG_RECORDING_UNSUPPORTED = {{ _("Recording not supported here. Choose an audio file.")|tojson }};
  const MSG_RECORDED_UPLOADING = {{ _("Recorded ✓ uploading…")|tojson }};
  const MSG_MIC_BLOCKED = {{ _("Mic blocked / not available.")|tojson }};

  function nearBottom(){
    try{
      if(!box) return true;
      return (box.scrollHeight - box.scrollTop - box.clientHeight) < 180;
    }catch(e){ return true; }
  }
  function scrollBottom(){
    try{
      if(!box) return;
      box.scrollTop = box.scrollHeight;
    }catch(e){}
  }

  function autoGrowTa(){
    if(!bodyTa) return;
    bodyTa.style.height = "auto";
    const h = Math.min(bodyTa.scrollHeight, 160);
    bodyTa.style.height = h + "px";
  }
  if(bodyTa){
    bodyTa.addEventListener("input", autoGrowTa);
    bodyTa.addEventListener("keydown", (e)=>{
      if(e.key === "Enter" && !e.shiftKey){
        e.preventDefault();
        requestSend();
      }
    });
    autoGrowTa();
  }

  // Track last message id
  let lastId = 0;
  document.querySelectorAll('#discussionBox [data-mid]').forEach(el=>{
    const n = parseInt(el.getAttribute('data-mid')||'0', 10);
    if(n > lastId) lastId = n;
  });

  const activeQ = (((new URLSearchParams(window.location.search)).get('q'))||'').toLowerCase().trim();

  function appendHtmlRow(html){
    if(!html || !box) return;
    const stick = nearBottom();
    const tmp = document.createElement("div");
    tmp.innerHTML = html;
    const node = tmp.firstElementChild;
    if(node){
      if(bottom && bottom.parentNode){
        bottom.parentNode.insertBefore(node, bottom);
      }else{
        box.appendChild(node);
      }
    }
    if(stick) scrollBottom();
  }

  async function sendFormData(fd){
    if(!form) return;
    try{
      if(sendBtn) sendBtn.disabled = true;
      const r = await fetch(form.action, {
        method: "POST",
        headers: {"X-Requested-With":"XMLHttpRequest", "Accept":"application/json"},
        body: fd
      });
      const data = await r.json().catch(()=>null);
      if(!r.ok || !data || !data.ok){
        const err = (data && data.error) ? data.error : MSG_SEND_FAIL;
        if(recStatus) recStatus.textContent = err;
        return;
      }
      if(recStatus) recStatus.textContent = "";
      if(data.html) appendHtmlRow(data.html);
      if(typeof data.id === "number") lastId = Math.max(lastId, data.id);
      // Clear inputs
      if(bodyTa) bodyTa.value = "";
      if(fileInput) fileInput.value = "";
      if(voiceInput) voiceInput.value = "";
      if(gifUrl) gifUrl.value = "";
      autoGrowTa();
      scrollBottom();
    }catch(e){
      if(recStatus) recStatus.textContent = MSG_SEND_FAIL;
    }finally{
      if(sendBtn) sendBtn.disabled = false;
    }
  }

  function requestSend(){
    if(!form) return;
    const fd = new FormData(form);
    // If this is a plain Enter send, strip empty file fields for stability on some browsers.
    sendFormData(fd);
  }

  if(form){
    form.addEventListener("submit", (e)=>{
      e.preventDefault();
      requestSend();
    });
  }

  // Auto-send file when chosen
  if(fileInput){
    fileInput.addEventListener("change", ()=>{
      if(!fileInput.files || !fileInput.files.length) return;
      if(bodyTa) bodyTa.value = "";
      if(voiceInput) voiceInput.value = "";
      if(gifUrl) gifUrl.value = "";
      requestSend();
    });
  }
  // Auto-send selected voice file
  if(voiceInput){
    voiceInput.addEventListener("change", ()=>{
      if(!voiceInput.files || !voiceInput.files.length) return;
      if(bodyTa) bodyTa.value = "";
      if(fileInput) fileInput.value = "";
      if(gifUrl) gifUrl.value = "";
      requestSend();
    });
  }

  // Voice record (MediaRecorder). Sends blob directly.
  let stream=null, mediaRec=null, chunks=[];
  function stopAll(){
    try{ if(mediaRec && mediaRec.state==="recording") mediaRec.stop(); }catch(e){}
    try{ if(stream) stream.getTracks().forEach(t=>t.stop()); }catch(e){}
    stream=null; mediaRec=null; chunks=[];
  }
  async function startRec(){
    await stopAll();
    try{
      if(fileInput) fileInput.value='';
      if(gifUrl) gifUrl.value='';
      if(bodyTa) bodyTa.value='';
      stream = await navigator.mediaDevices.getUserMedia({audio:true});
      mediaRec = new MediaRecorder(stream);
      chunks=[];
      mediaRec.ondataavailable = e=>{ if(e.data && e.data.size) chunks.push(e.data); };
      mediaRec.onstop = async ()=>{
        try{
          const mime = (mediaRec && mediaRec.mimeType) ? mediaRec.mimeType : "audio/webm";
          const blob = new Blob(chunks, {type: mime});
          if(recStatus) recStatus.textContent = MSG_RECORDED_UPLOADING;
          const fd = new FormData();
          fd.append("csrf_token", form ? (form.querySelector('input[name="csrf_token"]')||{}).value || "" : "");
          fd.append("body", "");
          fd.append("voice", blob, "voice.webm");
          await sendFormData(fd);
          if(recStatus) recStatus.textContent = "";
        }catch(e){
          if(recStatus) recStatus.textContent = (e && e.message) ? e.message : MSG_VOICE_UPLOAD_FAIL;
          try{ if(voiceInput) voiceInput.click(); }catch(e2){}
        }
        stopAll();
      };
      mediaRec.start();
      if(recStatus) recStatus.textContent = MSG_RECORDING;
      if(recBtn) recBtn.textContent = "⏹️";
    }catch(e){
      if(recStatus) recStatus.textContent = MSG_MIC_BLOCKED;
      if(recBtn) recBtn.textContent = "🎙️";
      stopAll();
    }
  }
  if(recBtn && (!window.MediaRecorder || !navigator.mediaDevices)){
    recBtn.addEventListener("click", ()=>{
      try{ if(voiceInput) voiceInput.click(); }catch(e){}
      if(recStatus) recStatus.textContent = MSG_RECORDING_UNSUPPORTED;
    });
  }
  if(recBtn && window.MediaRecorder && navigator.mediaDevices){
    recBtn.addEventListener("click", async ()=>{
      if(mediaRec && mediaRec.state==="recording"){ try{ mediaRec.stop(); }catch(e){} if(recBtn) recBtn.textContent = "🎙️"; }
      else{ await startRec(); }
    });
  }

  // GIF picker (Tenor demo key). Sends URL, backend downloads and stores it.
  const gifBtn = document.getElementById("gifBtn");
  const gifModalEl = document.getElementById("gifModal");
  const gifGrid = document.getElementById("gifGrid");
  const gifSearch = document.getElementById("gifSearch");
  const gifSearchBtn = document.getElementById("gifSearchBtn");
  const gifHint = document.getElementById("gifHint");
  let gifModal=null;
  try{ if(gifModalEl) gifModal = new bootstrap.Modal(gifModalEl); }catch(e){}

  function renderGifs(items){
    if(!gifGrid) return;
    gifGrid.innerHTML = (items||[]).map(it=>{
      const url = it && it.url;
      const prev = it && (it.preview || it.url);
      if(!url) return "";
      return `<button type="button" class="gif-item" data-url="${url}"><img src="${prev}" alt="gif"/></button>`;
    }).join("");
  }

  async function fetchTenor(q){
    // Tenor v1 endpoints tend to have better browser CORS compatibility than v2.
    const key = "LIVDSRZULELA"; // Tenor demo key
    const limit = 24;
    const url = (q && q.trim())
      ? `https://g.tenor.com/v1/search?q=${encodeURIComponent(q.trim())}&key=${encodeURIComponent(key)}&limit=${limit}&media_filter=minimal`
      : `https://g.tenor.com/v1/trending?key=${encodeURIComponent(key)}&limit=${limit}&media_filter=minimal`;

    const r = await fetch(url, {cache:"no-store"});
    const data = await r.json().catch(()=>null);
    const res = (data && data.results) ? data.results : [];
    const items = res.map(x=>{
      try{
        const media = (x.media && x.media[0]) ? x.media[0] : {};
        const tiny = (media.tinygif || media.nanogif || media.gif || {});
        const full = (media.gif || media.mediumgif || media.tinygif || {});
        const preview = tiny.url || full.url || "";
        const url = full.url || tiny.url || "";
        return {url, preview};
      }catch(e){ return null; }
    }).filter(Boolean).filter(x=>x.url);
    return items;
  }

  async function openGifs(q){
    try{
      if(gifHint) gifHint.textContent = {{ _("Loading…")|tojson }};
      const items = await fetchTenor(q);
      renderGifs(items);
      if(gifHint) gifHint.textContent = items.length ? "" : {{ _("No results.")|tojson }};
    }catch(e){
      if(gifHint) gifHint.textContent = {{ _("GIF search failed.")|tojson }};
    }
  }

  if(gifBtn){
    gifBtn.addEventListener("click", ()=>{
      if(gifModal) gifModal.show();
      openGifs("");
    });
  }
  if(gifSearchBtn){
    gifSearchBtn.addEventListener("click", ()=>openGifs((gifSearch && gifSearch.value||"").trim()));
  }
  if(gifSearch){
    gifSearch.addEventListener("keydown", (e)=>{
      if(e.key==="Enter"){ e.preventDefault(); openGifs((gifSearch.value||"").trim()); }
    });
  }
  if(gifGrid){
    gifGrid.addEventListener("click", (e)=>{
      const btn = e.target && e.target.closest ? e.target.closest(".gif-item") : null;
      if(!btn) return;
      const url = btn.getAttribute("data-url") || "";
      if(!url) return;
      if(gifUrl) gifUrl.value = url;
      if(bodyTa) bodyTa.value = "";
      if(fileInput) fileInput.value = "";
      if(voiceInput) voiceInput.value = "";
      if(gifModal) gifModal.hide();
      requestSend();
    });
  }

  // Poll for new messages
  async function poll(){
    try{
      const r = await fetch(`/api/discussion/since?id=${encodeURIComponent(lastId)}`, {headers: {"Accept":"application/json"}});
      if(!r.ok) return;
      const data = await r.json().catch(()=>null);
      const msgs = (data && data.messages) ? data.messages : [];
      if(!msgs.length) return;

      // remove "No messages yet"
      const empty = box && box.querySelector(".small-muted.text-center");
      if(empty) empty.remove();

      msgs.forEach(m=>{
        const mid = Number(m.id||0);
        if(mid <= lastId) return;
        lastId = Math.max(lastId, mid);

        if(activeQ){
          // best-effort filter on sender + rendered text content
          const sender = String(m.sender||"").toLowerCase();
          if(!sender.includes(activeQ)){
            // if not in sender, still append (because attachment rows might not have text); keep server-side filter for initial page
            // but for live updates we don't hide attachments unexpectedly.
          }
        }
        appendHtmlRow(m.html);
      });
    }catch(e){}
  }

  setTimeout(scrollBottom, 80);
  setInterval(poll, 1100);
  setTimeout(poll, 220);
})();
</script>
{% endblock %}
"""



# ---------------------------
# Stories (24h stories, max 5/day)
# ---------------------------
_STORY_ACTIVE_HOURS = 24
_STORY_DAILY_LIMIT = 5
_STORY_MAX_BYTES = CHAT_MAX_BYTES  # reuse app attachment size limit (33MB)
_STORY_REACTION_MAX_TEXT = 220
_STORY_REACTION_MIN_INTERVAL_SEC = 1.5
_STORY_REACTION_THROTTLE = {}  # (viewer, owner) -> monotonic ts
_STORY_REACTION_THROTTLE_LOCK = threading.Lock()

def _stories_tables_init():
    try:
        conn = db_connect()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT NOT NULL,
                filename TEXT,
                mime TEXT,
                stored_path TEXT NOT NULL,
                size INTEGER,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass

def _story_cutoff_z() -> str:
    return (datetime.utcnow() - timedelta(hours=_STORY_ACTIVE_HOURS)).isoformat(timespec="seconds") + "Z"

def _story_today_start_z() -> str:
    n = datetime.utcnow()
    return n.strftime("%Y-%m-%dT00:00:00Z")

def _story_safe_path(sp: str) -> Optional[str]:
    try:
        if not sp:
            return None
        real = os.path.realpath(str(sp))
        base = os.path.realpath(ATT_DIR)
        if real == base or not real.startswith(base + os.sep):
            return None
        bn = os.path.basename(real)
        if not bn.startswith("story_"):
            return None
        if not os.path.isfile(real):
            return None
        return real
    except Exception:
        return None

def _story_is_media(mime: str) -> Tuple[bool, bool]:
    m = (mime or "").lower()
    return m.startswith("image/"), m.startswith("video/")

def _story_active_usernames() -> set:
    _stories_tables_init()
    conn = db_connect()
    try:
        rows = conn.execute(
            "SELECT DISTINCT owner FROM stories WHERE created_at>=? ORDER BY owner COLLATE NOCASE ASC",
            (_story_cutoff_z(),)
        ).fetchall()
        return {r["owner"] for r in rows}
    except Exception:
        return set()
    finally:
        conn.close()

def _story_store_upload(owner: str, file_storage) -> int:
    if not file_storage or not getattr(file_storage, "filename", ""):
        raise ValueError("missing_file")
    filename = secure_filename(getattr(file_storage, "filename", "") or "") or "story"
    mime = (getattr(file_storage, "mimetype", "") or "").strip().lower()
    if not mime or mime == "application/octet-stream":
        mime = (guess_mime(filename) or "application/octet-stream").lower()

    is_img = mime.startswith("image/")
    is_vid = mime.startswith("video/")
    if not (is_img or is_vid):
        # Allow only photo/video for Stories.
        raise ValueError("story_photo_video_only")

    try:
        size = _filestorage_size(file_storage)
        if size is not None and int(size) > _STORY_MAX_BYTES:
            raise ValueError("too_large")
    except ValueError:
        raise
    except Exception:
        pass

    conn = db_connect()
    try:
        cur = conn.cursor()
        # max 5 per UTC day
        cnt = cur.execute(
            "SELECT COUNT(*) AS c FROM stories WHERE owner=? AND created_at>=?",
            (owner, _story_today_start_z())
        ).fetchone()
        if cnt and int(cnt["c"] or 0) >= _STORY_DAILY_LIMIT:
            raise ValueError("story_daily_limit")

        cur.execute(
            "INSERT INTO stories(owner, filename, mime, stored_path, size, created_at) VALUES(?,?,?,?,?,?)",
            (owner, filename, mime, "PENDING", 0, now_z())
        )
        sid = int(cur.lastrowid)
        sp = os.path.join(ATT_DIR, f"story_{sid}.bin")
        try:
            size = int(_save_plain_upload(file_storage, sp))
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
        if size > _STORY_MAX_BYTES:
            try:
                os.remove(sp)
            except Exception:
                pass
            conn.execute("DELETE FROM stories WHERE id=?", (sid,))
            conn.commit()
            raise ValueError("too_large")
        conn.execute("UPDATE stories SET stored_path=?, size=? WHERE id=?", (sp, size, sid))
        conn.commit()
        return sid
    finally:
        try:
            conn.close()
        except Exception:
            pass

def _story_user_cards(scope: str, q: str = "") -> List[Dict[str, Any]]:
    _stories_tables_init()
    cutoff = _story_cutoff_z()
    conn = db_connect()
    try:
        latest_rows = conn.execute("""
            SELECT owner, COUNT(*) AS story_count, MAX(id) AS latest_id, MAX(created_at) AS latest_at
            FROM stories
            WHERE created_at>=?
            GROUP BY owner
            ORDER BY MAX(created_at) DESC, owner COLLATE NOCASE ASC
        """, (cutoff,)).fetchall()
    finally:
        conn.close()
    if not latest_rows:
        return []
    info = {r["owner"]: {"story_count": int(r["story_count"] or 0), "latest_id": int(r["latest_id"] or 0), "latest_at": r["latest_at"]} for r in latest_rows}
    cards, _, _ = user_cards(scope, exclude=None)
    ql = (q or "").strip().lower()
    out = []
    for c in cards:
        u = c["username"]
        if u not in info:
            continue
        if ql and (ql not in u.lower()) and (ql not in str(c.get("nickname") or "").lower()):
            continue
        d = dict(c)
        d.update(info[u])
        d["latest_at_local"] = _local_time_str(info[u]["latest_at"])
        out.append(d)
    out.sort(key=lambda x: (-(int(x.get("latest_id") or 0)), str(x.get("nickname") or x.get("username")).lower()))
    return out

def _stories_for_user(username: str) -> List[Dict[str, Any]]:
    _stories_tables_init()
    conn = db_connect()
    try:
        rows = conn.execute("""
            SELECT id, owner, filename, mime, stored_path, size, created_at
            FROM stories
            WHERE owner=? AND created_at>=?
            ORDER BY id ASC
        """, (username, _story_cutoff_z())).fetchall()
    finally:
        conn.close()
    out = []
    for r in rows:
        mime = (r["mime"] or "application/octet-stream")
        is_img, is_vid = _story_is_media(mime)
        out.append({
            "id": int(r["id"]),
            "owner": r["owner"],
            "filename": r["filename"] or f"story-{r['id']}",
            "mime": mime,
            "size": int(r["size"] or 0),
            "size_h": human_size(int(r["size"] or 0)),
            "created_at": r["created_at"],
            "created_at_local": _local_time_str(r["created_at"]),
            "is_image": is_img,
            "is_video": is_vid,
        })
    return out


def _story_owner_visible_in_scope(owner: str, scope: str) -> bool:
    try:
        if not owner:
            return False
        cards, _, _ = user_cards(scope, exclude=None)
        for c in cards:
            if c.get("username") == owner:
                return True
        return False
    except Exception:
        return False


def _story_reaction_norm_text(raw: str) -> str:
    txt = (raw or "").replace("\x00", " ")
    txt = re.sub(r"[\r\n\t]+", " ", txt)
    txt = re.sub(r"\s{2,}", " ", txt).strip()
    if len(txt) > _STORY_REACTION_MAX_TEXT:
        txt = txt[:_STORY_REACTION_MAX_TEXT].rstrip()
    return txt


def _story_reaction_throttle_ok(viewer: str, owner: str) -> bool:
    key = (str(viewer or ""), str(owner or ""))
    now_m = time.monotonic()
    with _STORY_REACTION_THROTTLE_LOCK:
        prev = float(_STORY_REACTION_THROTTLE.get(key) or 0.0)
        if prev and (now_m - prev) < float(_STORY_REACTION_MIN_INTERVAL_SEC):
            return False
        _STORY_REACTION_THROTTLE[key] = now_m
        # tiny cleanup to avoid unbounded growth
        if len(_STORY_REACTION_THROTTLE) > 4096:
            cutoff = now_m - 3600.0
            for k, v in list(_STORY_REACTION_THROTTLE.items()):
                try:
                    if float(v) < cutoff:
                        _STORY_REACTION_THROTTLE.pop(k, None)
                except Exception:
                    _STORY_REACTION_THROTTLE.pop(k, None)
        return True


def _dm_store_existing_file_tx(conn, dm_id: int, src_path: str, filename: str, mime: str) -> Dict[str, Any]:
    """Copy an existing server-side file into DM attachments inside an open transaction."""
    fn = secure_filename(filename or "file") or "file"
    mm = (mime or guess_mime(fn) or "application/octet-stream").strip().lower()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO dm_files(dm_id, filename, mime, stored_path, size, created_at) VALUES(?,?,?,?,?,?)",
        (dm_id, fn, mm, "PENDING", 0, now_z())
    )
    fid = int(cur.lastrowid)
    dst = os.path.join(DM_FILES_DIR, f"dm_file_{fid}.bin")
    size = 0
    try:
        with open(src_path, "rb") as rf, open(dst, "wb") as wf:
            while True:
                chunk = rf.read(64 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > CHAT_MAX_BYTES:
                    raise ValueError("too_large")
                wf.write(chunk)
    except Exception:
        try:
            if os.path.exists(dst):
                os.remove(dst)
        except Exception:
            pass
        conn.execute("DELETE FROM dm_files WHERE id=?", (fid,))
        raise

    conn.execute("UPDATE dm_files SET stored_path=?, size=? WHERE id=?", (dst, int(size), fid))
    conn.execute("UPDATE dm_messages SET has_file=1 WHERE id=?", (dm_id,))
    return {"id": fid, "stored_path": dst, "size": int(size), "mime": mm, "filename": fn}


def _send_story_reaction_dm(sender: str, recipient: str, story_row, reaction_text: str) -> int:
    """Send a DM that contains the story media + a text reaction."""
    if not sender or not recipient:
        raise ValueError("bad_users")
    body_text = f"📸 Story reaction: {reaction_text}" if reaction_text else "📸 Story reaction"
    src_path = _story_safe_path(story_row["stored_path"])
    if not src_path:
        raise ValueError("story_missing")
    filename = story_row["filename"] or f"story-{int(story_row['id'])}"
    mime = story_row["mime"] or guess_mime(filename) or "application/octet-stream"

    conn = db_connect()
    saved_paths = []
    try:
        exists = conn.execute("SELECT 1 FROM users WHERE username=?", (recipient,)).fetchone()
        if not exists:
            raise ValueError("recipient_missing")

        cur = conn.cursor()
        cur.execute(
            "INSERT INTO dm_messages(sender, recipient, body_enc, created_at, delivered_at, read_at, has_voice, has_file) VALUES(?,?,?,?,NULL,NULL,0,1)",
            (sender, recipient, aesgcm_encrypt_text(body_text), now_z()),
        )
        dm_id = int(cur.lastrowid)
        info = _dm_store_existing_file_tx(conn, dm_id, src_path, filename, mime)
        saved_paths.append(info.get("stored_path"))
        conn.commit()
        return dm_id
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        for sp in saved_paths:
            try:
                if sp and os.path.exists(sp):
                    os.remove(sp)
            except Exception:
                pass
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass

@app.route("/stories")
@login_required
def stories():
    _stories_tables_init()
    me = current_user()
    q = (request.args.get("q") or "").strip()
    users = _story_user_cards(g.scope, q=q)
    mine = [x for x in users if x.get("username") == me]
    others = [x for x in users if x.get("username") != me]
    return render_template("stories.html", title="Stories", q=q, me=me, mine=mine, users=others, daily_limit=_STORY_DAILY_LIMIT)

@app.route("/stories/upload", methods=["POST"])
@login_required
def story_upload():
    _stories_tables_init()
    me = current_user()
    fs = request.files.get("story")
    if not fs or not getattr(fs, "filename", ""):
        flash("Select a photo or video.")
        return redirect(url_for("stories"))
    try:
        _story_store_upload(me, fs)
        flash("Story uploaded.")
    except ValueError as ve:
        code = str(ve)
        if code == "story_daily_limit":
            flash("You can upload up to 5 stories per day.")
        elif code == "story_photo_video_only":
            flash("Stories support only photos or videos.")
        elif code == "too_large":
            flash("Story file is too large.")
        else:
            flash("Story upload failed.")
    except Exception as e:
        log.exception("Story upload failed: %s", e)
        flash("Story upload failed.")
    return redirect(url_for("stories"))

@app.route("/stories/view/<username>")
@login_required
def story_view_user(username: str):
    _stories_tables_init()
    viewer = current_user()
    username = (username or "").strip()
    if not username:
        return redirect(url_for("stories"))
    try:
        idx = int(request.args.get("i") or 0)
    except Exception:
        idx = 0
    items = _stories_for_user(username)
    if not items:
        flash("No active stories for this user.")
        return redirect(url_for("stories"))
    if idx < 0:
        idx = 0
    if idx >= len(items):
        idx = len(items) - 1
    cur = items[idx]
    prev_url = url_for("story_view_user", username=username, i=idx-1) if idx > 0 else None
    next_url = url_for("story_view_user", username=username, i=idx+1) if idx < (len(items)-1) else None
    owner_has_pic = False
    try:
        ensure_profile_row(username)
        conn2 = db_connect()
        prow = conn2.execute("SELECT pic_path FROM profiles WHERE username=?", (username,)).fetchone()
        conn2.close()
        owner_has_pic = bool(prow and prow["pic_path"] and os.path.exists(prow["pic_path"]))
    except Exception:
        owner_has_pic = False
    return render_template(
        "story_viewer.html",
        title=f"Story @{username}",
        viewer=viewer,
        owner=username,
        story=cur,
        idx=idx,
        total=len(items),
        prev_url=prev_url,
        next_url=next_url,
        leave_url=url_for("stories"),
        owner_has_pic=owner_has_pic
    )


@app.route("/stories/react/<int:sid>", methods=["POST"])
@login_required
def story_react(sid: int):
    _stories_tables_init()
    viewer = current_user()
    reaction = _story_reaction_norm_text((request.form.get("reaction") or request.form.get("reaction_text") or ""))
    try:
        ret_i = int(request.form.get("i") or 0)
    except Exception:
        ret_i = 0

    if not reaction:
        flash("Reaction cannot be empty.")
        return redirect(url_for("stories"))
    if len(reaction) > _STORY_REACTION_MAX_TEXT:
        # Defensive, _story_reaction_norm_text already truncates.
        reaction = reaction[:_STORY_REACTION_MAX_TEXT]

    conn = db_connect()
    try:
        row = conn.execute(
            "SELECT id, owner, filename, mime, stored_path, size, created_at FROM stories WHERE id=? AND created_at>=?",
            (sid, _story_cutoff_z()),
        ).fetchone()
    finally:
        conn.close()

    if not row:
        flash("Story is no longer available.")
        return redirect(url_for("stories"))

    owner = (row["owner"] or "").strip()
    if not owner:
        flash("Story is no longer available.")
        return redirect(url_for("stories"))
    if owner == viewer:
        flash("You cannot react to your own story.")
        return redirect(url_for("story_view_user", username=owner, i=max(0, ret_i)))

    sc = current_scope()
    if not _story_owner_visible_in_scope(owner, sc):
        abort(403)

    if not _story_reaction_throttle_ok(viewer, owner):
        flash("Story reactions are rate limited. Try again.")
        return redirect(url_for("story_view_user", username=owner, i=max(0, ret_i)))

    try:
        _send_story_reaction_dm(viewer, owner, row, reaction)
        flash("Story reaction sent to chat.")
    except ValueError as ve:
        code = str(ve)
        if code == "too_large":
            flash("Story file is too large.")
        elif code in ("story_missing", "recipient_missing"):
            flash("Story is no longer available.")
        else:
            flash("Failed to send story reaction.")
    except Exception as e:
        log.exception("story_react failed: %s", e)
        flash("Failed to send story reaction.")

    # Stay in the viewer; user can also open the DM manually.
    return redirect(url_for("story_view_user", username=owner, i=max(0, ret_i)))

@app.route("/stories/media/<int:sid>")
@login_required
def story_media(sid: int):
    _stories_tables_init()
    me = current_user()
    conn = db_connect()
    try:
        row = conn.execute(
            "SELECT id, owner, filename, mime, stored_path, created_at FROM stories WHERE id=? AND created_at>=?",
            (sid, _story_cutoff_z()),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        abort(404)
    owner = (row["owner"] or "").strip()
    if not owner:
        abort(404)
    if owner != me and not _story_owner_visible_in_scope(owner, current_scope()):
        abort(403)
    sp = _story_safe_path(row["stored_path"])
    if not sp:
        abort(404)
    mime = (row["mime"] or guess_mime(row["filename"] or "") or "application/octet-stream").strip().lower()
    is_img, is_vid = _story_is_media(mime)
    if not (is_img or is_vid):
        abort(404)
    resp = send_file(sp, mimetype=mime, as_attachment=False, conditional=True, max_age=0)
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp

# Stories translations + UI polish
try:
    TRANSLATIONS_EL.update({
        "Stories": "Ιστορίες",
        "Story": "Ιστορία",
        "Upload story": "Ανέβασε ιστορία",
        "Quick story": "Γρήγορη ιστορία",
        "Select a photo or video.": "Επίλεξε φωτογραφία ή βίντεο.",
        "Story uploaded.": "Η ιστορία ανέβηκε.",
        "Story upload failed.": "Απέτυχε η μεταφόρτωση ιστορίας.",
        "Stories support only photos or videos.": "Οι ιστορίες υποστηρίζουν μόνο φωτογραφίες ή βίντεο.",
        "You can upload up to 5 stories per day.": "Μπορείς να ανεβάσεις έως 5 ιστορίες την ημέρα.",
        "Story file is too large.": "Το αρχείο ιστορίας είναι πολύ μεγάλο.",
        "No active stories right now.": "Δεν υπάρχουν ενεργές ιστορίες τώρα.",
        "No active stories for this user.": "Δεν υπάρχουν ενεργές ιστορίες για αυτόν τον χρήστη.",
        "Search stories users...": "Αναζήτηση χρηστών με ιστορίες...",
        "Take photo/video and upload instantly": "Τράβα φωτογραφία/βίντεο και ανέβασέ το αμέσως",
        "Active for 24 hours": "Ενεργό για 24 ώρες",
        "Today": "Σήμερα",
        "Back": "Πίσω",
        "Next": "Επόμενο",
        "Leave": "Έξοδος",
        "Leave stories": "Έξοδος από ιστορίες",
        "Story #": "Ιστορία #",
        "Uploading...": "Μεταφόρτωση...",
        "Open media": "Άνοιγμα πολυμέσου",
        "React to story": "Αντίδραση στην ιστορία",
        "Quick reactions": "Γρήγορες αντιδράσεις",
        "Type emoji or text...": "Γράψε emoji ή κείμενο...",
        "Send reaction": "Στείλε αντίδραση",
        "Story reaction sent to chat.": "Η αντίδραση στην ιστορία στάλθηκε στη συνομιλία.",
        "Failed to send story reaction.": "Αποτυχία αποστολής αντίδρασης ιστορίας.",
        "Story is no longer available.": "Η ιστορία δεν είναι πλέον διαθέσιμη.",
        "You cannot react to your own story.": "Δεν μπορείς να αντιδράσεις στη δική σου ιστορία.",
        "Reaction cannot be empty.": "Η αντίδραση δεν μπορεί να είναι κενή.",
        "Story reactions are rate limited. Try again.": "Οι αντιδράσεις ιστορίας έχουν όριο συχνότητας. Δοκίμασε ξανά.",
    })
except Exception:
    pass


# Device auto-login translations
try:
    TRANSLATIONS_EL.update({
        "Device auto‑login": "Αυτόματη σύνδεση συσκευής",
        "Request approval from admin to allow this device to auto‑login without entering credentials.": "Ζήτησε έγκριση από τον διαχειριστή ώστε αυτή η συσκευή να συνδέεται αυτόματα χωρίς να βάζεις στοιχεία.",
        "Note: If 2FA is enabled on your account, auto‑login is disabled and you must sign in normally.": "Σημείωση: Αν είναι ενεργό το 2FA στον λογαριασμό σου, η αυτόματη σύνδεση απενεργοποιείται και πρέπει να συνδεθείς κανονικά.",
        "Admins": "Διαχειριστές",
        "Request approval": "Αίτημα έγκρισης",
        "Status": "Κατάσταση",
        "When approved, this page will log you in automatically.": "Όταν εγκριθεί, αυτή η σελίδα θα σε συνδέσει αυτόματα.",
        "Username is required.": "Απαιτείται όνομα χρήστη.",
        "Auto‑login is disabled because 2FA is enabled on this account. Please sign in normally.": "Η αυτόματη σύνδεση απενεργοποιείται επειδή είναι ενεργό το 2FA σε αυτόν τον λογαριασμό. Συνδέσου κανονικά.",
        "This device is already approved for auto‑login.": "Αυτή η συσκευή είναι ήδη εγκεκριμένη για αυτόματη σύνδεση.",
        "Request sent to admin.": "Το αίτημα στάλθηκε στον διαχειριστή.",
        "Request failed. Please try again.": "Το αίτημα απέτυχε. Δοκίμασε ξανά.",
        "Device access requests": "Αιτήματα πρόσβασης συσκευής",
        "Approve devices that request auto‑login without credentials. (2FA accounts must sign in normally.)": "Έγκρινε συσκευές που ζητούν αυτόματη σύνδεση χωρίς στοιχεία. (Λογαριασμοί με 2FA πρέπει να συνδέονται κανονικά.)",
        "Search device requests...": "Αναζήτηση αιτημάτων συσκευής...",
        "Requested at": "Ζητήθηκε",
        "Approve": "Έγκριση",
        "Upload up to 5 stories per day. Stories are visible for 24 hours.": "Ανέβασε έως 5 ιστορίες την ημέρα. Οι ιστορίες είναι ορατές για 24 ώρες.",
        "Users with stories show a purple ring on their profile picture.": "Οι χρήστες με ιστορίες έχουν μωβ/λεβάντα δαχτυλίδι γύρω από τη φωτογραφία προφίλ.",
        "You can react with emoji/text — the reaction is sent in chat together with the story.": "Μπορείς να αντιδράσεις με emoji/κείμενο — η αντίδραση στέλνεται στη συνομιλία μαζί με την ιστορία.",
        "After you login once, the app can remember this device so you don’t need credentials next time.": "Αφού συνδεθείς μία φορά, η εφαρμογή μπορεί να θυμάται αυτή τη συσκευή ώστε να μη χρειάζονται στοιχεία την επόμενη φορά.",
        "On a new server/device, you can request approval from an admin (admins are shown by name).": "Σε νέο διακομιστή/συσκευή, μπορείς να ζητήσεις έγκριση από διαχειριστή (οι διαχειριστές εμφανίζονται με όνομα).",
        "Deny": "Απόρριψη",
    })
except Exception:
    pass

# Bounty translations
try:
    TRANSLATIONS_EL.update({
        "Bounty": "Επικήρυξη",
        "Admins can add, edit, or remove a bounty for an existing Profiler entry.": "Οι διαχειριστές μπορούν να προσθέτουν, να επεξεργάζονται ή να αφαιρούν επικήρυξη για υπάρχουσα καταχώρηση Profiler.",
        "Search profile to manage bounty": "Αναζήτηση προφίλ για διαχείριση επικήρυξης",
        "Search by ID, name, or owner": "Αναζήτηση με ID, όνομα ή ιδιοκτήτη",
        "Profiles are hidden by default. Search first, then select one result.": "Τα προφίλ είναι κρυμμένα από προεπιλογή. Κάνε πρώτα αναζήτηση και μετά επίλεξε ένα αποτέλεσμα.",
        "Search results": "Αποτελέσματα αναζήτησης",
        "shown": "εμφανίζονται",
        "Selected": "Επιλεγμένο",
        "Current bounty": "Τρέχουσα επικήρυξη",
        "Bounty price": "Ποσό επικήρυξης",
        "Currency changes by language ($ EN / € EL).": "Το νόμισμα αλλάζει ανά γλώσσα ($ στα Αγγλικά / € στα Ελληνικά).",
        "Required (max 333 characters)": "Υποχρεωτικό (μέχρι 333 χαρακτήρες)",
        "Reason is required and limited to 333 characters.": "Η αιτία είναι υποχρεωτική και έως 333 χαρακτήρες.",
        "Update Bounty": "Ενημέρωση επικήρυξης",
        "Add Bounty": "Προσθήκη επικήρυξης",
        "Remove Bounty": "Αφαίρεση επικήρυξης",
        "Remove bounty from this profile?": "Αφαίρεση επικήρυξης από αυτό το προφίλ;",
        "Search and select a profile to add or edit a bounty.": "Κάνε αναζήτηση και επίλεξε προφίλ για προσθήκη ή επεξεργασία επικήρυξης.",
        "Bounty reason is required.": "Η αιτία επικήρυξης είναι υποχρεωτική.",
        "Bounty reason must be 333 characters or less.": "Η αιτία επικήρυξης πρέπει να είναι έως 333 χαρακτήρες.",
        "Bounty saved for profile": "Η επικήρυξη αποθηκεύτηκε για το προφίλ",
        "Bounty removed from profile": "Η επικήρυξη αφαιρέθηκε από το προφίλ",









        "Sign in": "Σύνδεση",
        "Existing users only.": "Μόνο για υπάρχοντες χρήστες.",
        "or": "ή",















        "Admins can also manage Profiler bounties from the Bounty page.": "Οι διαχειριστές μπορούν επίσης να διαχειρίζονται επικηρύξεις Profiler από τη σελίδα Bounty.",

    })
except Exception:
    pass

try:
    BUT_CSS += r"""
/* Stories */
.avatar-wrap.story-ring{
  position: relative;
  border-radius: 16px;
  padding: 2px;
  width: 46px;
  height: 46px;
  flex: 0 0 46px;
  background: linear-gradient(135deg, #b48cff, #d7b6ff, #9f7bff);
  box-shadow: 0 0 0 2px rgba(180,140,255,0.16);
}
.avatar-wrap.story-ring .avatar-img,
.avatar-wrap.story-ring .avatar-fallback{
  width: 42px;
  height: 42px;
}
.story-user-card{
  display:flex; align-items:center; justify-content:space-between; gap:10px;
  border:1px solid var(--border); border-radius:16px; padding:10px 12px; background:var(--panel);
}
.story-user-card + .story-user-card{ margin-top:10px; }
.story-view-shell{
  max-width: 760px; margin: 0 auto;
}
.story-stage{
  position: relative;
  border:1px solid var(--border);
  border-radius:18px;
  background: rgba(0,0,0,.25);
  min-height: min(70vh, 560px);
  display:flex; align-items:center; justify-content:center;
  overflow:hidden;
}
.story-stage img, .story-stage video{
  width:100%; max-height:min(70vh, 560px); object-fit: contain; background:#000;
}
.story-progress{
  display:grid; grid-template-columns: repeat(auto-fit, minmax(16px,1fr)); gap:6px;
}
.story-progress .seg{
  height:4px; border-radius:999px; background: rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.08);
}
.story-progress .seg.on{ background:#c8a8ff; border-color:#c8a8ff; }
.story-react-box{ border:1px solid var(--border); border-radius:16px; background:var(--panel); padding:12px; }
.story-react-quick{ display:flex; flex-wrap:wrap; gap:8px; }
.story-react-quick .btn{ min-width:44px; }

"""
except Exception:
    pass

TEMPLATES["stories.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="d-flex align-items-center justify-content-between gap-2 flex-wrap mb-3">
  <h3 class="mb-0">{{ _('Stories') }}</h3>
  <div class="small-muted">{{ _('Active for 24 hours') }} • {{ _('Today') }}: {{ daily_limit }}/day</div>
</div>

<div class="row g-3">
  <div class="col-12 col-lg-5">
    <div class="card-soft p-3 mb-3">
      <div class="fw-semibold mb-2">{{ _('Quick story') }}</div>
      <form method="post" action="{{ url_for('story_upload') }}" enctype="multipart/form-data" id="storyUploadForm">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <input class="form-control mb-2" type="file" name="story" id="storyFileInput" accept="image/*,video/*" capture>
        <div class="small-muted mb-2">{{ _('Take photo/video and upload instantly') }} • {{ _('You can upload up to 5 stories per day.') }}</div>
        <button class="btn btn-accent" type="submit" id="storyUploadBtn">{{ _('Upload story') }}</button>
      </form>
    </div>

    {% if mine %}
    <div class="card-soft p-3">
      <div class="fw-semibold mb-2">@{{ me }}</div>
      {% for u in mine %}
      <a class="story-user-card text-decoration-none" href="{{ url_for('story_view_user', username=u.username) }}">
        <div class="d-flex align-items-center gap-2">
          <div class="avatar-wrap story-ring">
            {% if u.has_pic %}
              <img class="avatar-img pfp-clickable" src="{{ url_for('profile_pic', username=u.username) }}" alt="" onclick="toggleImageModal(this.src)">
            {% else %}
              <div class="avatar-fallback"><img data-logo class="avatar-img" src="{{ logo_dark }}" alt="logo"></div>
            {% endif %}
          </div>
          <div>
            <div class="fw-bold">{{ u.nickname }}</div>
            <div class="small-muted">@{{ u.username }} • {{ u.story_count }} {{ _('Story') if u.story_count==1 else _('Stories') }}</div>
          </div>
        </div>
        <span class="pill online">▶</span>
      </a>
      {% endfor %}
    </div>
    {% endif %}
  </div>

  <div class="col-12 col-lg-7">
    <div class="card-soft p-3">
      <form method="get" class="d-flex gap-2 mb-3">
        <input class="form-control" name="q" value="{{ q }}" placeholder="{{ _('Search stories users...') }}">
        <button class="btn btn-ghost" type="submit">{{ _('Search') }}</button>
      </form>

      {% for u in users %}
        <a class="story-user-card text-decoration-none" href="{{ url_for('story_view_user', username=u.username) }}">
          <div class="d-flex align-items-center gap-2">
            <div class="avatar-wrap story-ring">
              {% if u.has_pic %}
                <img class="avatar-img pfp-clickable" src="{{ url_for('profile_pic', username=u.username) }}" alt="" onclick="toggleImageModal(this.src)">
              {% else %}
                <div class="avatar-fallback"><img data-logo class="avatar-img" src="{{ logo_dark }}" alt="logo"></div>
              {% endif %}
            </div>
            <div>
              <div class="fw-bold">{{ u.nickname }}</div>
              <div class="small-muted">@{{ u.username }} • {{ u.story_count }} {{ _('Stories') }} • {{ u.latest_at_local }}</div>
            </div>
          </div>
          <div class="d-flex align-items-center gap-2">
            <span class="pill {{ 'online' if u.online else 'offline' }}">{{ '🟢' if u.online else '⚫' }}</span>
            <span class="btn btn-ghost btn-sm">▶</span>
          </div>
        </a>
      {% else %}
        <div class="small-muted">{{ _('No active stories right now.') }}</div>
      {% endfor %}
    </div>
  </div>
</div>
{% endblock %}
{% block scripts %}
<script nonce="{{ csp_nonce }}">
(function(){
  const fi = document.getElementById('storyFileInput');
  const form = document.getElementById('storyUploadForm');
  const btn = document.getElementById('storyUploadBtn');
  if(fi && form){
    fi.addEventListener('change', ()=>{
      if(!fi.files || !fi.files.length) return;
      if(btn){ btn.disabled = true; btn.textContent = {{ _('Uploading...')|tojson }}; }
      form.submit();
    });
  }
})();
</script>
{% endblock %}
"""

TEMPLATES["story_viewer.html"] = r"""
{% extends "base.html" %}
{% block content %}
<div class="story-view-shell">
  <div class="d-flex align-items-center justify-content-between gap-2 flex-wrap mb-3">
    <div class="d-flex align-items-center gap-2">
      <div class="avatar-wrap {% if has_active_story(owner) %}story-ring{% endif %}">
        {% if owner_has_pic %}
          <img class="avatar-img" src="{{ url_for('profile_pic', username=owner) }}" alt="">
        {% else %}
          <div class="avatar-fallback"><img data-logo class="avatar-img" src="{{ logo_dark }}" alt="logo"></div>
        {% endif %}
      </div>
      <div>
        <div class="fw-bold">@{{ owner }}</div>
        <div class="small-muted">{{ story.created_at_local }} • {{ idx + 1 }}/{{ total }}</div>
      </div>
    </div>
    <a class="btn btn-ghost" href="{{ leave_url }}">{{ _('Leave') }}</a>
  </div>

  <div class="story-progress mb-2">
    {% for i in range(total) %}
      <div class="seg {% if i <= idx %}on{% endif %}"></div>
    {% endfor %}
  </div>

  <div class="story-stage">
    {% if story.is_image %}
      <img src="{{ url_for('story_media', sid=story.id) }}" alt="{{ _('Story') }}">
    {% elif story.is_video %}
      <video src="{{ url_for('story_media', sid=story.id) }}" controls autoplay playsinline></video>
    {% else %}
      <div class="p-4 text-center">
        <div class="fw-bold mb-2">{{ _('Story') }} #{{ story.id }}</div>
        <a class="btn btn-accent" href="{{ url_for('story_media', sid=story.id) }}">{{ _('Open media') }}</a>
      </div>
    {% endif %}
  </div>

  {% if viewer != owner %}
  <div class="story-react-box mt-3">
    <div class="fw-semibold mb-2">{{ _('React to story') }}</div>
    <div class="small-muted mb-2">{{ _('Quick reactions') }}</div>
    <div class="story-react-quick mb-2">
      {% for emo in ['🔥','😍','😂','😮','👏','❤️'] %}
      <form method="post" action="{{ url_for('story_react', sid=story.id) }}" class="d-inline">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <input type="hidden" name="i" value="{{ idx }}">
        <button class="btn btn-ghost btn-sm" type="submit" name="reaction" value="{{ emo }}">{{ emo }}</button>
      </form>
      {% endfor %}
    </div>
    <form method="post" action="{{ url_for('story_react', sid=story.id) }}" class="d-flex gap-2 flex-wrap">
      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
      <input type="hidden" name="i" value="{{ idx }}">
      <input class="form-control" style="min-width:240px" maxlength="220" name="reaction_text" placeholder="{{ _('Type emoji or text...') }}">
      <button class="btn btn-accent" type="submit">{{ _('Send reaction') }}</button>
      <a class="btn btn-ghost" href="{{ url_for('chat_with', username=owner) }}">{{ _('Chats') }}</a>
    </form>
  </div>
  {% endif %}

  <div class="d-flex align-items-center justify-content-between gap-2 mt-3 flex-wrap">
    <div class="d-flex gap-2">
      {% if prev_url %}
        <a class="btn btn-ghost" href="{{ prev_url }}">{{ _('Back') }}</a>
      {% else %}
        <button class="btn btn-ghost" type="button" disabled>{{ _('Back') }}</button>
      {% endif %}
      {% if next_url %}
        <a class="btn btn-accent" href="{{ next_url }}">{{ _('Next') }}</a>
      {% else %}
        <button class="btn btn-accent" type="button" disabled>{{ _('Next') }}</button>
      {% endif %}
    </div>
    <a class="btn btn-ghost" href="{{ leave_url }}">{{ _('Leave stories') }}</a>
  </div>
</div>
{% endblock %}
{% block scripts %}
<script nonce="{{ csp_nonce }}">
(function(){
  document.addEventListener('keydown', (e)=>{
    if(e.key === 'ArrowLeft'){ const a = document.querySelector('a[href="{{ prev_url or "" }}"]'); if({{ 'true' if prev_url else 'false' }}) window.location.href = {{ (prev_url or '')|tojson }}; }
    if(e.key === 'ArrowRight'){ if({{ 'true' if next_url else 'false' }}) window.location.href = {{ (next_url or '')|tojson }}; }
    if(e.key === 'Escape'){ window.location.href = {{ leave_url|tojson }}; }
  });
})();
</script>
{% endblock %}
"""

try:
    BUT_CSS += r"""
body[data-ui-theme="forest"]{ --panel:#08150e; --panel2:rgba(8,21,14,0.68); --nav:#041008; --border:rgba(105,219,124,0.36); --accent:#69db7c; --accent-hover:#b2f2bb; --bubble-them:rgba(8,24,15,0.78);} 
body.light-theme[data-ui-theme="forest"]{ --panel:#f4fff6; --panel2:rgba(244,255,246,0.88); --nav:#ffffff; --border:rgba(37,123,54,0.22); --accent:#257b36; --accent-hover:#329a46; --bubble-them:rgba(232,246,235,0.95);} 
body[data-ui-theme="midnight"]{ --panel:#070916; --panel2:rgba(8,10,24,0.70); --nav:#03050f; --border:rgba(108,117,255,0.30); --accent:#8a94ff; --accent-hover:#bac1ff; --bubble-them:rgba(11,14,31,0.82);} 
body.light-theme[data-ui-theme="midnight"]{ --panel:#f7f8ff; --panel2:rgba(247,248,255,0.90); --nav:#ffffff; --border:rgba(74,82,173,0.20); --accent:#4a52ad; --accent-hover:#5f69d6; --bubble-them:rgba(236,238,252,0.96);} 
body[data-ui-theme="neon"]{ --panel:#0d0714; --panel2:rgba(13,7,20,0.70); --nav:#09040f; --border:rgba(255,0,191,0.32); --accent:#00f0ff; --accent-hover:#76fbff; --bubble-them:rgba(20,10,29,0.82);} 
body.light-theme[data-ui-theme="neon"]{ --panel:#fbf9ff; --panel2:rgba(251,249,255,0.90); --nav:#ffffff; --border:rgba(0,145,167,0.20); --accent:#0091a7; --accent-hover:#00b6d0; --bubble-them:rgba(242,237,250,0.96);} 
body[data-ui-theme="lavender"]{ --panel:#120d1d; --panel2:rgba(18,13,29,0.70); --nav:#0b0714; --border:rgba(205,147,255,0.34); --accent:#cd93ff; --accent-hover:#e2c1ff; --bubble-them:rgba(24,16,39,0.82);} 
body.light-theme[data-ui-theme="lavender"]{ --panel:#fbf8ff; --panel2:rgba(251,248,255,0.90); --nav:#ffffff; --border:rgba(132,88,173,0.20); --accent:#8458ad; --accent-hover:#9d6ecb; --bubble-them:rgba(242,236,250,0.96);} 
body[data-ui-theme="cyber"]{ --panel:#091117; --panel2:rgba(9,17,23,0.70); --nav:#050c11; --border:rgba(0,255,214,0.30); --accent:#00ffd6; --accent-hover:#8dfff0; --text-on-accent:#06100f; --bubble-them:rgba(13,22,29,0.82);} 
body.light-theme[data-ui-theme="cyber"]{ --panel:#f5ffff; --panel2:rgba(245,255,255,0.90); --nav:#ffffff; --border:rgba(0,136,116,0.22); --accent:#008874; --accent-hover:#00a88f; --bubble-them:rgba(232,248,247,0.96);} 
body[data-ui-theme="emerald"]{ --panel:#071612; --panel2:rgba(7,22,18,0.70); --nav:#04100d; --border:rgba(0,214,143,0.34); --accent:#00d68f; --accent-hover:#7ff0c4; --bubble-them:rgba(10,25,20,0.82);} 
body.light-theme[data-ui-theme="emerald"]{ --panel:#f3fffb; --panel2:rgba(243,255,251,0.90); --nav:#ffffff; --border:rgba(0,123,87,0.22); --accent:#007b57; --accent-hover:#00996d; --bubble-them:rgba(229,247,240,0.96);} 
body[data-ui-theme="sunset"]{ --panel:#1a0d08; --panel2:rgba(26,13,8,0.72); --nav:#130805; --border:rgba(255,147,79,0.34); --accent:#ff934f; --accent-hover:#ffc08f; --text-on-accent:#220f06; --bubble-them:rgba(31,15,9,0.82);} 
body.light-theme[data-ui-theme="sunset"]{ --panel:#fff8f2; --panel2:rgba(255,248,242,0.90); --nav:#ffffff; --border:rgba(196,101,31,0.22); --accent:#c4651f; --accent-hover:#df7b2f; --bubble-them:rgba(252,239,229,0.96);} 
body[data-ui-theme="ice"]{ --panel:#08131a; --panel2:rgba(8,19,26,0.70); --nav:#041018; --border:rgba(158,221,255,0.34); --accent:#9edcff; --accent-hover:#d5f0ff; --text-on-accent:#08131a; --bubble-them:rgba(10,23,31,0.82);} 
body.light-theme[data-ui-theme="ice"]{ --panel:#f5fcff; --panel2:rgba(245,252,255,0.90); --nav:#ffffff; --border:rgba(76,128,164,0.22); --accent:#4c80a4; --accent-hover:#639bc4; --bubble-them:rgba(233,244,250,0.96);} 
body[data-ui-theme="coffee"]{ --panel:#18110b; --panel2:rgba(24,17,11,0.72); --nav:#120d08; --border:rgba(181,135,99,0.34); --accent:#b58763; --accent-hover:#d0ae93; --bubble-them:rgba(30,21,13,0.82);} 
body.light-theme[data-ui-theme="coffee"]{ --panel:#fdf8f4; --panel2:rgba(253,248,244,0.90); --nav:#ffffff; --border:rgba(124,87,59,0.22); --accent:#7c573b; --accent-hover:#9b6d4a; --bubble-them:rgba(244,235,227,0.96);} 
body[data-ui-theme="obsidian"]{ --panel:#060606; --panel2:rgba(10,10,10,0.74); --nav:#030303; --border:rgba(255,255,255,0.16); --accent:#d9d9d9; --accent-hover:#ffffff; --text-on-accent:#101010; --bubble-them:rgba(17,17,17,0.86);} 
body.light-theme[data-ui-theme="obsidian"]{ --panel:#fafafa; --panel2:rgba(250,250,250,0.92); --nav:#ffffff; --border:rgba(90,90,90,0.22); --accent:#4a4a4a; --accent-hover:#666666; --text-on-accent:#ffffff; --bubble-them:rgba(238,238,238,0.96);} 
body[data-ui-theme="royal"]{ --panel:#0e0b1b; --panel2:rgba(14,11,27,0.72); --nav:#090613; --border:rgba(139,92,246,0.34); --accent:#8b5cf6; --accent-hover:#b39aff; --bubble-them:rgba(20,15,36,0.82);} 
body.light-theme[data-ui-theme="royal"]{ --panel:#faf7ff; --panel2:rgba(250,247,255,0.90); --nav:#ffffff; --border:rgba(97,69,173,0.20); --accent:#6145ad; --accent-hover:#7b5ccc; --bubble-them:rgba(239,234,250,0.96);} 
body[data-ui-theme="peach"]{ --panel:#180d0b; --panel2:rgba(24,13,11,0.72); --nav:#120806; --border:rgba(255,172,142,0.34); --accent:#ffac8e; --accent-hover:#ffd0bf; --text-on-accent:#1d0f0b; --bubble-them:rgba(28,16,13,0.82);} 
body.light-theme[data-ui-theme="peach"]{ --panel:#fff9f7; --panel2:rgba(255,249,247,0.90); --nav:#ffffff; --border:rgba(184,102,75,0.22); --accent:#b8664b; --accent-hover:#d07d5e; --bubble-them:rgba(250,238,234,0.96);} 
body[data-ui-theme="terminal"]{ --panel:#07100a; --panel2:rgba(7,16,10,0.72); --nav:#040a06; --border:rgba(77,255,125,0.34); --accent:#4dff7d; --accent-hover:#a3ffbb; --text-on-accent:#07100a; --bubble-them:rgba(10,19,12,0.84);} 
body.light-theme[data-ui-theme="terminal"]{ --panel:#f6fff8; --panel2:rgba(246,255,248,0.90); --nav:#ffffff; --border:rgba(34,128,57,0.22); --accent:#228039; --accent-hover:#2fa64b; --bubble-them:rgba(233,248,236,0.96);} 
body[data-ui-theme="storm"]{ --panel:#0c1116; --panel2:rgba(12,17,22,0.72); --nav:#080c10; --border:rgba(144,164,174,0.30); --accent:#90a4ae; --accent-hover:#b7c5cb; --bubble-them:rgba(16,22,29,0.84);} 
body.light-theme[data-ui-theme="storm"]{ --panel:#f7fafc; --panel2:rgba(247,250,252,0.90); --nav:#ffffff; --border:rgba(88,102,112,0.22); --accent:#586670; --accent-hover:#6f7f8a; --bubble-them:rgba(236,241,244,0.96);} 
body[data-ui-theme="mint"]{ --panel:#081512; --panel2:rgba(8,21,18,0.72); --nav:#04100d; --border:rgba(122,255,206,0.34); --accent:#7affce; --accent-hover:#b7ffe4; --text-on-accent:#07130f; --bubble-them:rgba(10,24,20,0.84);} 
body.light-theme[data-ui-theme="mint"]{ --panel:#f5fffc; --panel2:rgba(245,255,252,0.90); --nav:#ffffff; --border:rgba(44,141,108,0.22); --accent:#2c8d6c; --accent-hover:#39aa84; --bubble-them:rgba(232,247,242,0.96);} 
body[data-ui-theme="plum"]{ --panel:#140a16; --panel2:rgba(20,10,22,0.72); --nav:#0d0610; --border:rgba(196,113,237,0.34); --accent:#c471ed; --accent-hover:#e0b0ff; --bubble-them:rgba(23,12,26,0.84);} 
body.light-theme[data-ui-theme="plum"]{ --panel:#fcf7ff; --panel2:rgba(252,247,255,0.90); --nav:#ffffff; --border:rgba(119,61,152,0.22); --accent:#773d98; --accent-hover:#9250b6; --bubble-them:rgba(242,234,248,0.96);} 
body[data-ui-theme="gold"]{ --panel:#171304; --panel2:rgba(23,19,4,0.72); --nav:#100d03; --border:rgba(255,215,87,0.34); --accent:#ffd757; --accent-hover:#ffe79d; --text-on-accent:#1c1604; --bubble-them:rgba(28,23,6,0.84);} 
body.light-theme[data-ui-theme="gold"]{ --panel:#fffdf4; --panel2:rgba(255,253,244,0.90); --nav:#ffffff; --border:rgba(163,126,17,0.22); --accent:#a37e11; --accent-hover:#c59615; --bubble-them:rgba(247,242,222,0.96);} 
body[data-ui-theme="volcano"]{ --panel:#1b0906; --panel2:rgba(27,9,6,0.72); --nav:#130604; --border:rgba(255,93,56,0.34); --accent:#ff5d38; --accent-hover:#ff9e8a; --bubble-them:rgba(31,11,7,0.84);} 
body.light-theme[data-ui-theme="volcano"]{ --panel:#fff7f4; --panel2:rgba(255,247,244,0.90); --nav:#ffffff; --border:rgba(180,64,31,0.22); --accent:#b4401f; --accent-hover:#d95b34; --bubble-them:rgba(249,233,227,0.96);} 
body[data-ui-theme="glacier"]{ --panel:#061118; --panel2:rgba(6,17,24,0.72); --nav:#040b10; --border:rgba(107,208,255,0.34); --accent:#6bd0ff; --accent-hover:#bdeeff; --text-on-accent:#061118; --bubble-them:rgba(9,20,28,0.84);} 
body.light-theme[data-ui-theme="glacier"]{ --panel:#f4fcff; --panel2:rgba(244,252,255,0.90); --nav:#ffffff; --border:rgba(46,116,148,0.22); --accent:#2e7494; --accent-hover:#3d93bc; --bubble-them:rgba(231,244,249,0.96);} 
body[data-ui-theme="nightshade"]{ --panel:#100914; --panel2:rgba(16,9,20,0.72); --nav:#09050b; --border:rgba(154,120,255,0.34); --accent:#9a78ff; --accent-hover:#c7b6ff; --bubble-them:rgba(18,11,23,0.84);} 
body.light-theme[data-ui-theme="nightshade"]{ --panel:#fbf9ff; --panel2:rgba(251,249,255,0.90); --nav:#ffffff; --border:rgba(89,66,155,0.22); --accent:#59429b; --accent-hover:#7157bc; --bubble-them:rgba(239,236,249,0.96);} 
body[data-ui-theme="sand"]{ --panel:#17110a; --panel2:rgba(23,17,10,0.72); --nav:#100b06; --border:rgba(224,192,137,0.32); --accent:#e0c089; --accent-hover:#f0d8af; --text-on-accent:#181108; --bubble-them:rgba(27,21,13,0.84);} 
body.light-theme[data-ui-theme="sand"]{ --panel:#fffaf3; --panel2:rgba(255,250,243,0.90); --nav:#ffffff; --border:rgba(145,112,56,0.22); --accent:#917038; --accent-hover:#b38b45; --bubble-them:rgba(246,239,225,0.96);} 
body[data-ui-theme="aqua"]{ --panel:#071518; --panel2:rgba(7,21,24,0.72); --nav:#040e10; --border:rgba(79,227,214,0.34); --accent:#4fe3d6; --accent-hover:#a6f5ee; --text-on-accent:#071518; --bubble-them:rgba(9,23,27,0.84);} 
body.light-theme[data-ui-theme="aqua"]{ --panel:#f4fffe; --panel2:rgba(244,255,254,0.90); --nav:#ffffff; --border:rgba(29,127,119,0.22); --accent:#1d7f77; --accent-hover:#28a094; --bubble-them:rgba(229,247,245,0.96);} 
body[data-ui-theme="orchid"]{ --panel:#140b18; --panel2:rgba(20,11,24,0.72); --nav:#0d0610; --border:rgba(231,140,255,0.34); --accent:#e78cff; --accent-hover:#f3c3ff; --bubble-them:rgba(23,13,28,0.84);} 
body.light-theme[data-ui-theme="orchid"]{ --panel:#fff7ff; --panel2:rgba(255,247,255,0.90); --nav:#ffffff; --border:rgba(145,71,165,0.22); --accent:#9147a5; --accent-hover:#b05fc6; --bubble-them:rgba(247,235,249,0.96);} 

"""
except Exception:
    pass


try:
    BUT_CSS += r"""
/* Extra saved theme styles (Settings). The top-bar button still toggles only dark/light. */
body[data-ui-theme="matrix"]{
  --panel:#07130c;
  --panel2:rgba(8, 20, 12, 0.64);
  --nav:#030a05;
  --border:rgba(110,255,166,0.40);
  --accent:#74ffaf;
  --accent-hover:#b0ffd0;
  --bubble-them:rgba(8,20,12,0.72);
  --shadow:0 18px 50px rgba(0,24,8,0.42);
}
body.light-theme[data-ui-theme="matrix"]{
  --panel:#f5fff7;
  --panel2:rgba(245,255,247,0.82);
  --nav:#ffffff;
  --border:rgba(25,135,84,0.24);
  --accent:#198754;
  --accent-hover:#20a76a;
  --bubble-them:rgba(232,248,238,0.92);
}
body[data-ui-theme="ocean"]{
  --panel:#08121d;
  --panel2:rgba(10,22,34,0.66);
  --nav:#050d16;
  --border:rgba(116,192,252,0.38);
  --accent:#74c0fc;
  --accent-hover:#a5d8ff;
  --bubble-them:rgba(11,26,40,0.76);
}
body.light-theme[data-ui-theme="ocean"]{
  --panel:#f4fbff;
  --panel2:rgba(244,251,255,0.84);
  --nav:#ffffff;
  --border:rgba(36,112,176,0.22);
  --accent:#2470b0;
  --accent-hover:#2f86d0;
  --bubble-them:rgba(232,243,252,0.94);
}
body[data-ui-theme="amber"]{
  --panel:#1b1205;
  --panel2:rgba(30,21,8,0.66);
  --nav:#120b03;
  --border:rgba(255,193,7,0.34);
  --accent:#ffc107;
  --accent-hover:#ffd65c;
  --text-on-accent:#1b1205;
  --bubble-them:rgba(30,21,8,0.78);
}
body.light-theme[data-ui-theme="amber"]{
  --panel:#fffaf1;
  --panel2:rgba(255,250,241,0.86);
  --nav:#ffffff;
  --border:rgba(201,129,0,0.22);
  --accent:#c98100;
  --accent-hover:#e39f27;
  --bubble-them:rgba(251,242,221,0.96);
}
body[data-ui-theme="crimson"]{
  --panel:#1a070b;
  --panel2:rgba(29,10,15,0.66);
  --nav:#120407;
  --border:rgba(255,107,107,0.34);
  --accent:#ff6b6b;
  --accent-hover:#ffa8a8;
  --bubble-them:rgba(30,10,15,0.78);
}
body.light-theme[data-ui-theme="crimson"]{
  --panel:#fff5f6;
  --panel2:rgba(255,245,246,0.84);
  --nav:#ffffff;
  --border:rgba(184,53,76,0.22);
  --accent:#b8354c;
  --accent-hover:#d5536c;
  --bubble-them:rgba(252,233,237,0.95);
}
body[data-ui-theme="silver"]{
  --panel:#111318;
  --panel2:rgba(18,20,25,0.68);
  --nav:#0b0d10;
  --border:rgba(210,218,226,0.30);
  --accent:#d2dae2;
  --accent-hover:#eef2f5;
  --text-on-accent:#0b0d10;
  --bubble-them:rgba(22,24,30,0.82);
}
body.light-theme[data-ui-theme="silver"]{
  --panel:#fbfcfd;
  --panel2:rgba(251,252,253,0.88);
  --nav:#ffffff;
  --border:rgba(97,108,120,0.22);
  --accent:#616c78;
  --accent-hover:#778392;
  --text-on-accent:#ffffff;
  --bubble-them:rgba(238,241,244,0.96);
}
body[data-ui-theme="rose"]{
  --panel:#180911;
  --panel2:rgba(25,10,18,0.68);
  --nav:#10050b;
  --border:rgba(247,131,172,0.34);
  --accent:#f783ac;
  --accent-hover:#ffb3c6;
  --text-on-accent:#180911;
  --bubble-them:rgba(26,10,19,0.80);
}
body.light-theme[data-ui-theme="rose"]{
  --panel:#fff7fb;
  --panel2:rgba(255,247,251,0.88);
  --nav:#ffffff;
  --border:rgba(181,72,117,0.22);
  --accent:#b54875;
  --accent-hover:#cf5f8f;
  --bubble-them:rgba(252,237,245,0.96);
}
"""
except Exception:
    pass



try:
    TRANSLATIONS_EL.update({
        "Face Detector": "Ανιχνευτής προσώπου",
        "Open the built-in camera or upload a photo/video to detect faces.": "Άνοιξε την ενσωματωμένη κάμερα ή ανέβασε φωτογραφία/βίντεο για ανίχνευση προσώπων.",
        "Use the save button to store a captured result in your Downloads/ButSystem/Face Detector folder when available.": "Χρησιμοποίησε το κουμπί αποθήκευσης για να αποθηκεύσεις το αποτέλεσμα στον φάκελο Downloads/ButSystem/Face Detector όταν είναι διαθέσιμος.",
        "The top bar theme button still switches only between dark and light. Extra style presets are available in Settings.": "Το κουμπί θέματος στην πάνω μπάρα συνεχίζει να αλλάζει μόνο μεταξύ σκούρου και φωτεινού. Επιπλέον στυλ υπάρχουν στις Ρυθμίσεις.",
        "Use the built-in camera or upload a photo/video to detect faces.": "Χρησιμοποίησε την ενσωματωμένη κάμερα ή ανέβασε φωτογραφία/βίντεο για να ανιχνεύσεις πρόσωπα.",
        "Saved captures go to your Downloads/ButSystem/Face Detector folder when available.": "Οι αποθηκευμένες λήψεις πηγαίνουν στον φάκελο Downloads/ButSystem/Face Detector όταν είναι διαθέσιμος.",
        "Start camera": "Έναρξη κάμερας",
        "Switch camera": "Εναλλαγή κάμερας",
        "Upload photo/video": "Μεταφόρτωση φωτογραφίας/βίντεο",
        "Save result": "Αποθήκευση αποτελέσματος",
        "Back to live camera": "Επιστροφή στη ζωντανή κάμερα",
        "Ready.": "Έτοιμο.",
        "Tip: On phones, camera access may require HTTPS or the same browser permissions used by the rest of ButSystem.": "Στα τηλέφωνα, η πρόσβαση στην κάμερα μπορεί να απαιτεί HTTPS ή τα ίδια δικαιώματα browser που χρησιμοποιεί το υπόλοιπο ButSystem.",
        "Starting camera...": "Εκκίνηση κάμερας...",
        "Live camera ready.": "Η ζωντανή κάμερα είναι έτοιμη.",
        "Camera access failed. Try HTTPS or grant camera permission.": "Η πρόσβαση στην κάμερα απέτυχε. Δοκίμασε HTTPS ή δώσε άδεια κάμερας.",
        "Analyzing uploaded media...": "Ανάλυση ανεβασμένου μέσου...",
        "Could not analyze the uploaded media.": "Δεν ήταν δυνατή η ανάλυση του ανεβασμένου μέσου.",
        "Please choose a photo or video file.": "Επίλεξε αρχείο φωτογραφίας ή βίντεο.",
        "Face": "Πρόσωπο",
        "Detected faces": "Ανιχνευμένα πρόσωπα",
        "No face detected.": "Δεν ανιχνεύτηκε πρόσωπο.",
        "Saving result...": "Αποθήκευση αποτελέσματος...",
        "Saved to": "Αποθηκεύτηκε στο",
        "Could not save the result.": "Δεν ήταν δυνατή η αποθήκευση του αποτελέσματος.",
        "Nothing to save yet.": "Δεν υπάρχει ακόμη κάτι για αποθήκευση.",
        "Theme style": "Στυλ θέματος",
        "Customize theme style, accent color, and font (saved per account).": "Προσαρμόστε το στυλ θέματος, το χρώμα έμφασης και τη γραμματοσειρά (αποθηκεύεται ανά λογαριασμό).",
        "This changes the saved color style for the interface. The top button still only switches between dark and light.": "Αυτό αλλάζει το αποθηκευμένο στυλ χρωμάτων της διεπαφής. Το πάνω κουμπί συνεχίζει να αλλάζει μόνο μεταξύ σκούρου και φωτεινού.",
        "Default": "Προεπιλογή",
        "Matrix": "Matrix",
        "Ocean": "Ωκεανός",
        "Amber": "Κεχριμπάρι",
        "Crimson": "Βαθυκόκκινο",
        "Silver": "Ασημί",
        "Appearance mode": "Λειτουργία εμφάνισης",
        "Dark": "Σκούρο",
        "Light": "Φωτεινό",
        "System": "Συστήματος",
        "Choose dark/light mode and color style.": "Επίλεξε σκούρο/φωτεινό και στυλ χρωμάτων.",
        "This changes only the dark/light mode for this browser on this device.": "Αυτό αλλάζει μόνο τη φωτεινή/σκούρα λειτουργία για αυτόν τον browser σε αυτή τη συσκευή.",
        "This changes the saved color style for the interface.": "Αυτό αλλάζει το αποθηκευμένο στυλ χρωμάτων της διεπαφής.",
        "Rose": "Ροζ",
        "Panic": "Πανικός",
        "Resume": "Συνέχεια",
        "Panic mode is active. Sensitive content is blurred until you resume.": "Η λειτουργία πανικού είναι ενεργή. Το ευαίσθητο περιεχόμενο είναι θολωμένο μέχρι να συνεχίσεις.",
        "Appearance": "Εμφάνιση",
        "Themes and fonts are here. Choose your saved interface style for this account.": "Τα θέματα και οι γραμματοσειρές είναι εδώ. Επίλεξε το αποθηκευμένο στυλ διεπαφής για αυτόν τον λογαριασμό.",
        "Security settings": "Ρυθμίσεις ασφαλείας",
        "30 saved color styles are available here.": "Εδώ υπάρχουν 30 αποθηκευμένα χρωματικά στυλ.",
        "12 Greek and English friendly font stacks are available here.": "Εδώ υπάρχουν 12 στοίβες γραμματοσειρών φιλικές για Ελληνικά και Αγγλικά.",
        "Open full appearance settings": "Άνοιγμα πλήρων ρυθμίσεων εμφάνισης",
        "Forest": "Δάσος",
        "Midnight": "Μεσάνυχτα",
        "Neon": "Νέον",
        "Lavender": "Λεβάντα",
        "Cyber": "Κυβερνο",
        "Emerald": "Σμαραγδί",
        "Sunset": "Ηλιοβασίλεμα",
        "Ice": "Πάγος",
        "Coffee": "Καφές",
        "Obsidian": "Οψιδιανός",
        "Royal": "Βασιλικό",
        "Peach": "Ροδάκινο",
        "Terminal": "Τερματικό",
        "Storm": "Καταιγίδα",
        "Mint": "Μέντα",
        "Plum": "Δαμάσκηνο",
        "Gold": "Χρυσό",
        "Volcano": "Ηφαίστειο",
        "Glacier": "Παγετώνας",
        "Nightshade": "Νυχτολούλουδο",
        "Sand": "Άμμος",
        "Aqua": "Aqua",
        "Orchid": "Ορχιδέα",
        "System": "Συστήματος",
        "Clean Sans": "Καθαρό Sans",
        "Readable Sans": "Ευανάγνωστο Sans",
        "Compact Sans": "Συμπαγές Sans",
        "Humanist Sans": "Humanist Sans",
        "Modern UI": "Μοντέρνο UI",
        "Rounded UI": "Στρογγυλεμένο UI",
        "Wide Sans": "Φαρδύ Sans",
        "News Serif": "News Serif",
        "Classic Serif": "Κλασικό Serif",
        "Monospace": "Μονοπλάτος",
        "Terminal Mono": "Μονοπλάτος Τερματικού",
        "Back to settings": "Πίσω στις ρυθμίσεις",
        "Ready. Tap Start camera.": "Έτοιμο. Πάτησε Εκκίνηση κάμερας.",
        "Tip: On phones, if the camera is busy in another app, close that app first and then tap Start camera again.": "Στα κινητά, αν η κάμερα χρησιμοποιείται από άλλη εφαρμογή, κλείσ' την πρώτα και μετά πάτησε ξανά Εκκίνηση κάμερας.",
    })
except Exception:
    pass

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.exception("Fatal error: %s", e)
        print("ButSystem crashed. See logs at " + LOG_PATH)
        raise
