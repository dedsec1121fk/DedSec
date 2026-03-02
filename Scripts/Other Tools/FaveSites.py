#!/usr/bin/env python3

import argparse
import base64
import json
import os
import secrets
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlparse

APP_TITLE = "FaveSites"
DB_NAME = "favesites.db"

# PBKDF2 iterations for vault key derivation
KDF_ITERATIONS = 390_000  # adjust if device is slow

# PBKDF2 iterations for security question answer hashing
SQ_KDF_ITERATIONS = 250_000


# ---------------------------
# Bootstrap / auto-install
# ---------------------------

def _run(cmd: list[str]) -> bool:
    try:
        p = subprocess.run(cmd, check=False)
        return p.returncode == 0
    except Exception:
        return False


def which(name: str) -> Optional[str]:
    for p in os.environ.get("PATH", "").split(os.pathsep):
        cand = Path(p) / name
        if cand.exists() and os.access(str(cand), os.X_OK):
            return str(cand)
    return None


def _is_termux() -> bool:
    prefix = os.environ.get("PREFIX", "")
    return "com.termux" in prefix or "TERMUX_VERSION" in os.environ


def _ensure_termux_packages() -> None:
    if not _is_termux():
        return
    if not (Path("/data/data/com.termux/files/usr/bin/pkg").exists() or which("pkg")):
        return
    _run(["pkg", "update", "-y"])
    # termux-api optional, but helpful for biometrics
    _run(["pkg", "install", "-y", "python", "openssl", "termux-api"])


def _pip_install(packages: list[str]) -> bool:
    return _run([sys.executable, "-m", "pip", "install", "--upgrade", *packages])


def ensure_deps() -> None:
    missing = []
    try:
        import flask  # noqa: F401
    except Exception:
        missing.append("flask")
    try:
        import cryptography  # noqa: F401
    except Exception:
        missing.append("cryptography")

    if not missing:
        return

    print(f"[{APP_TITLE}] Missing Python packages: {', '.join(missing)}")
    print(f"[{APP_TITLE}] Attempting to install automatically with pip...")

    try:
        _ensure_termux_packages()
    except Exception:
        pass

    ok = _pip_install(missing)
    if not ok:
        print(f"[{APP_TITLE}] Auto-install failed.")
        print("Try manually in Termux:")
        print("  pkg install python openssl termux-api")
        print("  pip install flask cryptography")
        sys.exit(1)


ensure_deps()

from flask import (  # noqa: E402
    Flask,
    abort,
    flash,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)
from cryptography.hazmat.primitives import hashes  # noqa: E402
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # noqa: E402
from cryptography.fernet import Fernet, InvalidToken  # noqa: E402


# ---------------------------
# DB helpers
# ---------------------------

def now_ts() -> int:
    return int(time.time())


def connect(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    return con


def init_db(db_path: Path) -> None:
    con = connect(db_path)
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (
            k TEXT PRIMARY KEY,
            v BLOB NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            username_enc BLOB,
            password_enc BLOB,
            notes_enc BLOB,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """
    )
    con.commit()
    con.close()


def meta_get(con: sqlite3.Connection, key: str) -> Optional[bytes]:
    row = con.execute("SELECT v FROM meta WHERE k=?", (key,)).fetchone()
    return row["v"] if row else None


def meta_set(con: sqlite3.Connection, key: str, value: bytes) -> None:
    con.execute(
        "INSERT INTO meta(k, v) VALUES(?, ?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
        (key, value),
    )
    con.commit()


def meta_del(con: sqlite3.Connection, key: str) -> None:
    con.execute("DELETE FROM meta WHERE k=?", (key,))
    con.commit()


# ---------------------------
# Vault crypto
# ---------------------------

def kdf_key(master_password: str, salt: bytes) -> bytes:
    if not master_password:
        raise ValueError("Master password cannot be empty.")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    key = kdf.derive(master_password.encode("utf-8"))
    return base64.urlsafe_b64encode(key)


def make_fernet(master_password: str, salt: bytes) -> Fernet:
    return Fernet(kdf_key(master_password, salt))


def is_configured(db_path: Path) -> bool:
    con = connect(db_path)
    ok = bool(meta_get(con, "salt") and meta_get(con, "verifier"))
    con.close()
    return ok


def set_master_password(db_path: Path, master_password: str) -> None:
    con = connect(db_path)
    salt = os.urandom(16)
    f = make_fernet(master_password, salt)
    verifier = f.encrypt(b"FaveSites verifier v1")
    meta_set(con, "salt", salt)
    meta_set(con, "verifier", verifier)
    con.close()


def verify_master_password(db_path: Path, master_password: str) -> bool:
    con = connect(db_path)
    salt = meta_get(con, "salt")
    verifier = meta_get(con, "verifier")
    con.close()
    if not salt or not verifier:
        return False
    try:
        f = make_fernet(master_password, salt)
        plain = f.decrypt(verifier, ttl=None)
        return plain == b"FaveSites verifier v1"
    except Exception:
        return False


def get_salt(db_path: Path) -> bytes:
    con = connect(db_path)
    salt = meta_get(con, "salt")
    con.close()
    if not salt:
        raise RuntimeError("Vault not configured.")
    return salt


def enc_optional(f: Fernet, s: str) -> Optional[bytes]:
    s = (s or "").strip()
    if not s:
        return None
    return f.encrypt(s.encode("utf-8"))


def dec_optional(f: Fernet, b: Optional[bytes]) -> str:
    if not b:
        return ""
    return f.decrypt(b, ttl=None).decode("utf-8")


# ---------------------------
# Favicons
# ---------------------------

def domain_from_url(u: str) -> str:
    try:
        p = urlparse(u.strip())
        host = p.netloc or p.path
        host = host.split("/")[0].strip()
        return host
    except Exception:
        return ""


def favicon_for_url(u: str, size: int = 96) -> str:
    host = domain_from_url(u)
    if not host:
        return ""
    return f"https://www.google.com/s2/favicons?domain={host}&sz={size}"


# ---------------------------
# Security Questions "2FA"
# ---------------------------

def _sq_hash(answer: str, salt: bytes) -> bytes:
    answer = (answer or "").strip().lower().encode("utf-8")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=SQ_KDF_ITERATIONS,
    )
    return kdf.derive(answer)


def sq_pack(questions_and_answers: list[Tuple[str, str]]) -> bytes:
    """
    Store: list of {q, salt_b64, hash_b64}
    """
    packed = []
    for q, a in questions_and_answers:
        s = os.urandom(16)
        h = _sq_hash(a, s)
        packed.append({
            "q": (q or "").strip(),
            "salt": base64.b64encode(s).decode("ascii"),
            "hash": base64.b64encode(h).decode("ascii"),
        })
    return json.dumps({"v": 1, "items": packed}).encode("utf-8")


def sq_verify_blob(blob: bytes, answers: list[str]) -> bool:
    try:
        data = json.loads(blob.decode("utf-8"))
        items = data.get("items", [])
        if len(items) != len(answers):
            return False
        for item, ans in zip(items, answers):
            s = base64.b64decode(item["salt"])
            h = base64.b64decode(item["hash"])
            h2 = _sq_hash(ans, s)
            if not secrets.compare_digest(h, h2):
                return False
        return True
    except Exception:
        return False


# ---------------------------
# Biometrics (Termux)
# ---------------------------

def biometric_available() -> bool:
    return bool(which("termux-fingerprint"))


def bio_key_path(data_dir: Path) -> Path:
    return data_dir / "bio.key"


def bio_key_load_or_create(data_dir: Path) -> bytes:
    p = bio_key_path(data_dir)
    if p.exists():
        return p.read_bytes()
    key = secrets.token_bytes(32)
    p.write_bytes(key)
    try:
        os.chmod(p, 0o600)
    except Exception:
        pass
    return key


def bio_encrypt_master(data_dir: Path, master: str) -> bytes:
    key = base64.urlsafe_b64encode(bio_key_load_or_create(data_dir))
    f = Fernet(key)
    return f.encrypt(master.encode("utf-8"))


def bio_decrypt_master(data_dir: Path, token: bytes) -> str:
    key = base64.urlsafe_b64encode(bio_key_load_or_create(data_dir))
    f = Fernet(key)
    return f.decrypt(token, ttl=None).decode("utf-8")


def termux_biometric_check(timeout_sec: int = 60) -> bool:
    exe = which("termux-fingerprint")
    if not exe:
        return False
    try:
        p = subprocess.run([exe], capture_output=True, text=True, timeout=timeout_sec)
        if p.returncode != 0:
            return False
        data = json.loads(p.stdout or "{}")
        return str(data.get("auth_result", "")).upper() in ("AUTH_RESULT_SUCCESS", "SUCCESS")
    except Exception:
        return False


# ---------------------------
# Auth gates
# ---------------------------

def require_unlocked():
    if "master" not in session:
        return redirect(url_for("login", next=request.path))
    return None


def sq_enabled(db_path: Path) -> bool:
    con = connect(db_path)
    blob = meta_get(con, "sq_blob")
    con.close()
    return bool(blob)


def sq_questions(db_path: Path) -> list[str]:
    con = connect(db_path)
    blob = meta_get(con, "sq_blob")
    con.close()
    if not blob:
        return []
    try:
        data = json.loads(blob.decode("utf-8"))
        return [it.get("q", "") for it in data.get("items", [])]
    except Exception:
        return []


# ---------------------------
# UI (theme toggle moon/sun + launcher grid 5x5)
# ---------------------------

BASE_HTML = """
<!doctype html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{{ title }} · {{ app_title }}</title>

  <style>
    :root{
      --nm-abyss-blue: #000000;
      --nm-darkest: rgba(10, 10, 18, 0.72);  /* nav / top surfaces */
      --nm-nav-solid: #0b0a12;          /* solid top bar */
      --nm-menu-solid: #0e0d18;         /* solid burger menu */
      --nm-dark: rgba(14, 14, 24, 0.58);     /* cards */
      --nm-container: rgba(18, 18, 30, 0.52);
      --nm-disclaimer-bg: #0a0a12;
      --nm-neutral-btn-bg: rgba(255, 255, 255, 0.10);
      --nm-border: rgba(205, 147, 255, 0.50);
      --nm-accent: #cd93ff;
      --nm-accent-hover: #e2c1ff;
      --nm-text: rgba(255, 255, 255, 0.92);
      --nm-text-muted: rgba(255, 255, 255, 0.74);
      --nm-text-accent: rgba(255, 255, 255, 0.96);
      --nm-danger: #ff6b6b;
      --nm-danger-hover: #ff8787;
      --nm-success: #51cf66;
      --nm-warning: #ffd43b;
      --nm-text-on-accent: #0b0a12;
      --nm-text-on-status: #0b0a12;
      --nm-fade: rgba(0,0,0,0);
      --glow-rgb: 205, 147, 255;
      --shadow-elev-1: 0 10px 30px rgba(0,0,0,0.35);
      --shadow-elev-2: 0 18px 50px rgba(0,0,0,0.42);
      --shadow-elev-3: 0 24px 70px rgba(0,0,0,0.55);
      --nav-h: 70px;
      --vh: 1vh;
      --safe-area-inset-top: env(safe-area-inset-top, 0px);
      --safe-area-inset-right: env(safe-area-inset-right, 0px);
      --safe-area-inset-left: env(safe-area-inset-left, 0px);
      --font-primary: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
      --font-secondary: 'Orbitron', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
      --font-mono: 'Roboto Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      --radius-sm: 12px;
      --radius-md: 16px;
      --radius-lg: 22px;
      --radius-pill: 999px;
      --z-backdrop: -2;
      --z-noise: -1;
      --z-base: 1;
      --z-header: 1000;
      --z-modal-overlay: 1010;
      --z-banner: 1100;
      --safe-area-inset-bottom: env(safe-area-inset-bottom, 10px);
      --ease-out-cubic: cubic-bezier(0.23, 1, 0.32, 1);
      --ease-out-back: cubic-bezier(0.34, 1.56, 0.64, 1);
      --ease-in-out-quad: cubic-bezier(0.45, 0, 0.55, 1);
      --ease-in-out-cubic: cubic-bezier(0.65, 0, 0.35, 1);
      --glass-blur: 16px;
      --glass-sat: 140%;
      --focus-ring: 0 0 0 3px rgba(205, 147, 255, 0.35);

      /* FaveSites UI vars mapped to DedSec palette */
      --bg0: var(--nm-abyss-blue);
      --bg1: var(--nm-nav-solid);
      --card: var(--nm-container);
      --cardHi: rgba(255,255,255,.06);
      --stroke: var(--nm-border);
      --stroke2: color-mix(in srgb, var(--nm-border) 70%, rgba(255,255,255,.30));
      --text: var(--nm-text);
      --muted: var(--nm-text-muted);
      --accent: var(--nm-accent);
      --accent2: var(--nm-success);
      --danger: var(--nm-danger);
      --shadow2: var(--shadow-elev-1);
      --radius: 20px;
      --radius2: 16px;
    }

    html[data-theme="light"]{
      --nm-abyss-blue: #ffffff;
      --nm-darkest: rgba(255, 255, 255, 0.82);
      --nm-nav-solid: #ffffff;          /* solid top bar */
      --nm-menu-solid: #ffffff;         /* solid burger menu */
      --nm-dark: rgba(255, 255, 255, 0.70);
      --nm-container: rgba(255, 255, 255, 0.62);
      --nm-disclaimer-bg: #ffffff;
      --nm-neutral-btn-bg: rgba(0, 0, 0, 0.06);
      --nm-border: rgba(123, 31, 162, 0.35);
      --nm-accent: #7b1fa2;
      --nm-accent-hover: #9c27b0;
      --nm-text: rgba(10, 10, 18, 0.92);
      --nm-text-muted: rgba(10, 10, 18, 0.70);
      --nm-text-accent: rgba(10, 10, 18, 0.96);
      --nm-danger: #d6336c;
      --nm-danger-hover: #e64980;
      --nm-success: #2f9e44;
      --nm-warning: #f59f00;
      --nm-text-on-accent: rgba(255, 255, 255, 0.96);
      --nm-text-on-status: rgba(255, 255, 255, 0.96);
      --glow-rgb: 123, 31, 162;
      --nm-fade: rgba(255,255,255,0);
      --shadow-elev-1: 0 10px 30px rgba(0,0,0,0.12);
      --shadow-elev-2: 0 18px 50px rgba(0,0,0,0.16);
      --shadow-elev-3: 0 24px 70px rgba(0,0,0,0.20);

      /* FaveSites UI vars mapped to DedSec palette */
      --bg0: var(--nm-abyss-blue);
      --bg1: var(--nm-nav-solid);
      --card: var(--nm-container);
      --cardHi: rgba(2,6,23,.04);
      --stroke: var(--nm-border);
      --stroke2: rgba(15,23,42,.22);
      --text: var(--nm-text);
      --muted: var(--nm-text-muted);
      --accent: var(--nm-accent);
      --accent2: var(--nm-success);
      --danger: var(--nm-danger);
      --shadow2: var(--shadow-elev-1);
    }

    *{ box-sizing:border-box; }
    body{
      margin:0;
      color:var(--text);
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, sans-serif;
      background:
        radial-gradient(900px 600px at 18% 10%, color-mix(in srgb, var(--accent) 22%, transparent), transparent 55%),
        radial-gradient(900px 600px at 86% 20%, color-mix(in srgb, var(--accent2) 16%, transparent), transparent 55%),
        linear-gradient(180deg, var(--bg0), var(--bg1));
      min-height:100vh;
    }

    a{ color:inherit; text-decoration:none; }
    .container{ max-width: 1100px; margin: 0 auto; padding: 14px; }

    header{
      position: sticky;
      top: 0;
      z-index: 20;
      backdrop-filter: blur(12px);
      border-bottom: 1px solid color-mix(in srgb, var(--stroke) 70%, transparent);
      background: linear-gradient(180deg,
        color-mix(in srgb, var(--bg0) 75%, transparent),
        color-mix(in srgb, var(--bg0) 30%, transparent)
      );
    }

    .topbar{
      display:flex; flex-wrap:wrap;
      align-items:center; justify-content:space-between;
      gap: 10px;
      padding: 12px 14px;
    }

    .brand{ display:flex; gap:12px; align-items:center; }
    .brand h1{ margin:0; font-size: 18px; letter-spacing:.2px; }

    .nav{ display:flex; gap:10px; flex-wrap:wrap; align-items:center; }

    .pill{
      width: 44px; height: 44px;
      border-radius: 999px;
      border: 1px solid var(--stroke);
      background: color-mix(in srgb, var(--card) 20%, transparent);
      display:grid; place-items:center;
      transition: transform .12s ease, border-color .12s ease, background .12s ease;
      user-select:none;
      font-size: 18px;
    }
    .pill:hover{
      transform: translateY(-1px);
      border-color: var(--stroke2);
      background: color-mix(in srgb, var(--accent) 10%, transparent);
    }

    /* Moon/Sun toggle */
    .themebtn{
      width: 44px; height: 44px;
      border-radius: 999px;
      border: 1px solid var(--stroke);
      background: color-mix(in srgb, var(--card) 18%, transparent);
      display:grid; place-items:center;
      cursor:pointer;
      transition: transform .12s ease, border-color .12s ease, background .12s ease;
      user-select:none;
      font-size: 18px;
      color: var(--text);
    }
    .themebtn:hover{
      transform: translateY(-1px);
      border-color: var(--stroke2);
      background: color-mix(in srgb, var(--accent) 10%, transparent);
    }

    .flash{
      padding: 12px 12px;
      border-radius: var(--radius2);
      border: 1px solid var(--stroke);
      background: color-mix(in srgb, var(--accent2) 12%, transparent);
      margin: 12px 0;
      box-shadow: var(--shadow2);
    }

    .card{
      background: linear-gradient(180deg, var(--cardHi), color-mix(in srgb, var(--cardHi) 60%, transparent));
      border: 1px solid var(--stroke);
      border-radius: var(--radius);
      padding: 16px;
      box-shadow: var(--shadow2);
    }

    label{ font-weight: 760; display:block; margin: 12px 0 8px; font-size: 13px; }
    input, textarea{
      width:100%;
      padding: 12px 12px;
      border-radius: 14px;
      border: 1px solid var(--stroke);
      background: color-mix(in srgb, var(--card) 22%, transparent);
      color: var(--text);
      outline:none;
      transition: border-color .12s ease, background .12s ease, box-shadow .12s ease;
    }
    input:focus, textarea:focus{
      border-color: color-mix(in srgb, var(--accent) 55%, transparent);
      box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent) 16%, transparent);
    }
    textarea{ min-height: 110px; resize: vertical; }

    .row{ display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
    .btn{
      cursor:pointer;
      padding: 10px 12px;
      border-radius: 14px;
      border: 1px solid var(--stroke);
      background: color-mix(in srgb, var(--card) 18%, transparent);
      text-decoration:none;
      display:inline-flex; align-items:center; gap:8px;
      transition: transform .12s ease, border-color .12s ease, background .12s ease;
      user-select:none;
      font-size: 14px;
      color: var(--text);
    }
    .btn:hover{
      transform: translateY(-1px);
      border-color: var(--stroke2);
      background: color-mix(in srgb, var(--accent) 12%, transparent);
    }
    .btn.primary{
      border-color: color-mix(in srgb, var(--accent) 55%, transparent);
      background: color-mix(in srgb, var(--accent) 14%, transparent);
    }
    .btn.danger{
      border-color: color-mix(in srgb, var(--danger) 55%, transparent);
      background: color-mix(in srgb, var(--danger) 10%, transparent);
    }
    .btn.ghost{ background: transparent; }

    .muted{ color: var(--muted); }
    .sep{ height:1px; background: var(--stroke); margin: 14px 0; }

    /* 5x5 launcher grid */
    .grid5{
      display:grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
    }

    .app{
      border-radius: 18px;
      border: 1px solid var(--stroke);
      background: color-mix(in srgb, var(--cardHi) 70%, transparent);
      padding: 10px 8px 12px;
      display:flex;
      flex-direction:column;
      align-items:center;
      gap: 8px;
      box-shadow: 0 10px 26px rgba(0,0,0,.18);
      position: relative;
      overflow: hidden;
    }
    .app:hover{
      border-color: var(--stroke2);
      background: color-mix(in srgb, var(--accent) 8%, transparent);
      transform: translateY(-1px);
      transition: transform .12s ease;
    }

    .appIcon{
      width: 52px; height: 52px;
      border-radius: 18px;
      background: color-mix(in srgb, var(--muted) 16%, transparent);
      border: 1px solid var(--stroke);
      display:grid; place-items:center;
      overflow:hidden;
    }
    .appIcon img{ width: 30px; height: 30px; }

    .appTitle{
      font-weight: 820;
      font-size: 12px;
      line-height: 1.1;
      text-align:center;
      max-width: 100%;
      overflow:hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .dots{
      position:absolute;
      top: 8px;
      right: 8px;
      width: 28px; height: 28px;
      border-radius: 999px;
      border: 1px solid var(--stroke);
      background: color-mix(in srgb, var(--card) 18%, transparent);
      display:grid; place-items:center;
      font-size: 14px;
      opacity: .92;
    }
    .dots:hover{ border-color: var(--stroke2); }

    code{
      padding: 2px 8px;
      border-radius: 999px;
      border: 1px solid var(--stroke);
      background: color-mix(in srgb, var(--card) 18%, transparent);
    }

    .footer-tip{ margin-top: 18px; font-size: 12px; color: var(--muted); }

    @media (prefers-reduced-motion: reduce){
      *{ transition:none !important; scroll-behavior:auto !important; }
    }
  </style>
</head>

<body>
<header>
  <div class="topbar">
    <div class="brand">
      <div><h1>{{ app_title }}</h1></div>
    </div>

    <div class="nav">
      <button class="themebtn" type="button" id="themeToggle" onclick="toggleTheme()" title="Toggle theme">🌙</button>

      {% if session.get("master") %}
        <a class="pill" href="{{ url_for('index') }}" title="Home">🏠</a>
        <a class="pill" href="{{ url_for('add') }}" title="Add">➕</a>
        <a class="pill" href="{{ url_for('settings') }}" title="Settings">⚙️</a>
        <a class="pill" href="{{ url_for('logout') }}" title="Lock">🔒</a>
      {% else %}
        <a class="pill" href="{{ url_for('login') }}" title="Unlock">🔓</a>
      {% endif %}
    </div>
  </div>
</header>

<main class="container">
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      {% for m in messages %}
        <div class="flash">{{ m }}</div>
      {% endfor %}
    {% endif %}
  {% endwith %}

  {{ body|safe }}

  <div class="footer-tip">
    Tip: keep this bound to <code>127.0.0.1</code>. Use a strong master password.
  </div>
</main>

<script>
function applyTheme(t){
  document.documentElement.setAttribute("data-theme", t);
  localStorage.setItem("favesites_theme", t);
  const btn = document.getElementById("themeToggle");
  if(btn) btn.textContent = (t === "dark") ? "🌙" : "☀️";
}
function toggleTheme(){
  const t = document.documentElement.getAttribute("data-theme") || "dark";
  applyTheme(t === "dark" ? "light" : "dark");
}
(function initTheme(){
  const saved = localStorage.getItem("favesites_theme") || "dark";
  applyTheme(saved === "light" ? "light" : "dark");
})();

async function copyText(id){
  const el = document.getElementById(id);
  if(!el) return;
  const v = el.value || el.textContent || "";
  try { await navigator.clipboard.writeText(v); alert("Copied!"); }
  catch(e){ prompt("Copy:", v); }
}
</script>
</body>
</html>
"""


# ---------------------------
# Flask app
# ---------------------------

def create_app(data_dir: Path) -> Flask:
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(32)

    db_path = data_dir / DB_NAME
    init_db(db_path)

    app.jinja_env.globals["favicon"] = favicon_for_url

    # ---------- Home ----------
    @app.route("/", methods=["GET"])
    def index():
        gate = require_unlocked()
        if gate:
            return gate

        q = (request.args.get("q") or "").strip()
        con = connect(db_path)
        if q:
            rows = con.execute(
                "SELECT * FROM sites WHERE title LIKE ? OR url LIKE ? ORDER BY updated_at DESC",
                (f"%{q}%", f"%{q}%"),
            ).fetchall()
        else:
            rows = con.execute("SELECT * FROM sites ORDER BY updated_at DESC").fetchall()
        con.close()

        body = render_template_string(
            """
            <div class="card">
              <form method="get" action="{{ url_for('index') }}">
                <label>Search</label>
                <div class="row">
                  <input name="q" value="{{ q }}" placeholder="Search title or URL..." />
                  <button class="btn primary" type="submit">🔎 Search</button>
                  <a class="btn ghost" href="{{ url_for('index') }}">Clear</a>
                </div>
              </form>
            </div>

            <div class="sep"></div>

            {% if not rows %}
              <div class="card">
                <div class="muted">No sites yet. Tap ➕ to add.</div>
              </div>
            {% else %}
              <div class="grid5">
                {% for r in rows %}
                  <div class="app">
                    <a class="dots" href="{{ url_for('view', site_id=r['id']) }}" title="More">⋯</a>
                    <a href="{{ r['url'] }}" target="_blank" rel="noreferrer">
                      <div class="appIcon">
                        <img alt="" src="{{ favicon(r['url']) }}" onerror="this.style.display='none';" />
                        <span class="muted" style="font-size:14px;" aria-hidden="true">🌐</span>
                      </div>
                    </a>
                    <div class="appTitle" title="{{ r['title'] }}">{{ r["title"] }}</div>
                  </div>
                {% endfor %}
              </div>
            {% endif %}
            """,
            rows=rows,
            q=q,
        )
        return render_template_string(BASE_HTML, title="Home", app_title=APP_TITLE, body=body)

    # ---------- Setup ----------
    @app.route("/setup", methods=["GET", "POST"])
    def setup():
        if is_configured(db_path):
            return redirect(url_for("login"))
        if request.method == "POST":
            p1 = request.form.get("p1") or ""
            p2 = request.form.get("p2") or ""
            if len(p1) < 8:
                flash("Master password must be at least 8 characters.")
            elif p1 != p2:
                flash("Passwords do not match.")
            else:
                set_master_password(db_path, p1)
                flash("Vault initialized. Please unlock.")
                return redirect(url_for("login"))

        body = render_template_string(
            """
            <div class="card">
              <h2 style="margin:0 0 8px 0;">First-time setup</h2>
              <p class="muted" style="margin:0;">Create a master password.</p>
              <form method="post">
                <label>Master password</label>
                <input type="password" name="p1" required />
                <label>Confirm</label>
                <input type="password" name="p2" required />
                <div class="row" style="margin-top:14px;">
                  <button class="btn primary" type="submit">✨ Create vault</button>
                </div>
              </form>
            </div>
            """,
        )
        return render_template_string(BASE_HTML, title="Setup", app_title=APP_TITLE, body=body)

    # ---------- Login ----------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if not is_configured(db_path):
            return redirect(url_for("setup"))

        con = connect(db_path)
        bio_token = meta_get(con, "bio_master_enc")
        sq_blob = meta_get(con, "sq_blob")
        con.close()
        bio_enabled = bool(bio_token)
        bio_avail = biometric_available()
        sq_is_enabled = bool(sq_blob)

        nxt = request.args.get("next") or url_for("index")

        if request.method == "POST":
            mp = request.form.get("master") or ""
            if verify_master_password(db_path, mp):
                # If security questions enabled, go to SQ verification
                if sq_is_enabled:
                    session.pop("master", None)
                    session["pending_master"] = mp
                    session["next_after_unlock"] = nxt
                    return redirect(url_for("sq_verify"))
                session["master"] = mp
                flash("Unlocked.")
                return redirect(nxt)
            flash("Wrong master password.")

        body = render_template_string(
            """
            <div class="card">
              <h2 style="margin:0 0 8px 0;">Unlock</h2>
              <p class="muted" style="margin:0;">Enter your master password.</p>

              <form method="post">
                <label>Master password</label>
                <input type="password" name="master" required />
                <div class="row" style="margin-top:14px;">
                  <button class="btn primary" type="submit">🔓 Unlock</button>
                </div>
              </form>

              {% if bio_enabled and bio_avail %}
                <div class="sep"></div>
                <form method="post" action="{{ url_for('bio_unlock') }}">
                  <button class="btn" type="submit">🪪 Use fingerprint/face</button>
                </form>
              {% endif %}

              {% if sq_is_enabled %}
                <div class="sep"></div>
                <div class="muted" style="font-size:12px;">Security questions are enabled.</div>
              {% endif %}
            </div>
            """,
            bio_enabled=bio_enabled,
            bio_avail=bio_avail,
            sq_is_enabled=sq_is_enabled,
        )
        return render_template_string(BASE_HTML, title="Unlock", app_title=APP_TITLE, body=body)

    @app.route("/logout")
    def logout():
        session.pop("master", None)
        session.pop("pending_master", None)
        session.pop("next_after_unlock", None)
        flash("Locked.")
        return redirect(url_for("login"))

    # ---------- Security Questions verify ----------
    @app.route("/sq_verify", methods=["GET", "POST"])
    def sq_verify():
        if not is_configured(db_path):
            return redirect(url_for("setup"))

        # Must have pending master from password or biometric
        pending = session.get("pending_master")
        if not pending:
            return redirect(url_for("login"))

        con = connect(db_path)
        blob = meta_get(con, "sq_blob")
        con.close()
        if not blob:
            # Not enabled anymore
            session["master"] = pending
            session.pop("pending_master", None)
            flash("Unlocked.")
            return redirect(session.pop("next_after_unlock", None) or url_for("index"))

        questions = sq_questions(db_path)

        if request.method == "POST":
            answers = [
                request.form.get("a1") or "",
                request.form.get("a2") or "",
                request.form.get("a3") or "",
            ]
            if sq_verify_blob(blob, answers):
                session["master"] = pending
                session.pop("pending_master", None)
                flash("Unlocked.")
                return redirect(session.pop("next_after_unlock", None) or url_for("index"))
            flash("Security answers are incorrect.")

        body = render_template_string(
            """
            <div class="card">
              <h2 style="margin:0 0 8px 0;">Security check</h2>
              <p class="muted" style="margin:0;">Answer your security questions.</p>
              <form method="post">
                <label>{{ q1 }}</label>
                <input name="a1" required />
                <label>{{ q2 }}</label>
                <input name="a2" required />
                <label>{{ q3 }}</label>
                <input name="a3" required />
                <div class="row" style="margin-top:14px;">
                  <button class="btn primary" type="submit">Continue</button>
                  <a class="btn ghost" href="{{ url_for('logout') }}">Cancel</a>
                </div>
              </form>
            </div>
            """,
            q1=questions[0] if len(questions) > 0 else "Question 1",
            q2=questions[1] if len(questions) > 1 else "Question 2",
            q3=questions[2] if len(questions) > 2 else "Question 3",
        )
        return render_template_string(BASE_HTML, title="Security check", app_title=APP_TITLE, body=body)

    # ---------- Biometric unlock ----------
    @app.route("/bio_unlock", methods=["POST"])
    def bio_unlock():
        if not is_configured(db_path):
            return redirect(url_for("setup"))

        con = connect(db_path)
        token = meta_get(con, "bio_master_enc")
        sq_blob = meta_get(con, "sq_blob")
        con.close()

        if not token:
            flash("Biometric quick unlock is not enabled.")
            return redirect(url_for("login"))
        if not biometric_available():
            flash("Biometric not available. Install Termux:API app + pkg termux-api.")
            return redirect(url_for("login"))
        if not termux_biometric_check():
            flash("Biometric unlock failed or cancelled.")
            return redirect(url_for("login"))

        try:
            master = bio_decrypt_master(data_dir, token)
        except Exception:
            flash("Biometric data corrupted. Disable and re-enable in Settings.")
            return redirect(url_for("login"))

        if not verify_master_password(db_path, master):
            flash("Stored biometric unlock no longer matches this vault. Disable and re-enable in Settings.")
            return redirect(url_for("login"))

        nxt = url_for("index")
        # If security questions enabled, continue to SQ verify
        if sq_blob:
            session.pop("master", None)
            session["pending_master"] = master
            session["next_after_unlock"] = nxt
            return redirect(url_for("sq_verify"))

        session["master"] = master
        flash("Unlocked with biometrics.")
        return redirect(nxt)

    # ---------- Add ----------
    @app.route("/add", methods=["GET", "POST"])
    def add():
        gate = require_unlocked()
        if gate:
            return gate

        if request.method == "POST":
            title = (request.form.get("title") or "").strip()
            url = (request.form.get("url") or "").strip()
            username = request.form.get("username") or ""
            password = request.form.get("password") or ""
            notes = request.form.get("notes") or ""
            if not title or not url:
                flash("Title and URL are required.")
            else:
                salt = get_salt(db_path)
                f = make_fernet(session["master"], salt)
                con = connect(db_path)
                con.execute(
                    """
                    INSERT INTO sites(title, url, username_enc, password_enc, notes_enc, created_at, updated_at)
                    VALUES(?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        title,
                        url,
                        enc_optional(f, username),
                        enc_optional(f, password),
                        enc_optional(f, notes),
                        now_ts(),
                        now_ts(),
                    ),
                )
                con.commit()
                con.close()
                flash("Saved.")
                return redirect(url_for("index"))

        body = render_template_string(
            """
            <div class="card">
              <h2 style="margin:0 0 8px 0;">Add site</h2>
              <form method="post">
                <label>Title</label>
                <input name="title" placeholder="e.g., Gmail" required />
                <label>URL</label>
                <input name="url" placeholder="https://mail.google.com" required />
                <label>Username (optional)</label>
                <input name="username" autocomplete="username" />
                <label>Password (optional)</label>
                <input name="password" type="password" autocomplete="current-password" />
                <label>Notes (optional)</label>
                <textarea name="notes" placeholder="Notes..."></textarea>
                <div class="row" style="margin-top:14px;">
                  <button class="btn primary" type="submit">💾 Save</button>
                  <a class="btn ghost" href="{{ url_for('index') }}">Cancel</a>
                </div>
              </form>
            </div>
            """,
        )
        return render_template_string(BASE_HTML, title="Add", app_title=APP_TITLE, body=body)

    # ---------- View / Edit / Delete ----------
    def get_site_or_404(site_id: int):
        con = connect(db_path)
        row = con.execute("SELECT * FROM sites WHERE id=?", (site_id,)).fetchone()
        con.close()
        if not row:
            abort(404)
        return row

    @app.route("/view/<int:site_id>")
    def view(site_id: int):
        gate = require_unlocked()
        if gate:
            return gate

        row = get_site_or_404(site_id)
        salt = get_salt(db_path)
        f = make_fernet(session["master"], salt)

        try:
            username = dec_optional(f, row["username_enc"])
            password = dec_optional(f, row["password_enc"])
            notes = dec_optional(f, row["notes_enc"])
        except InvalidToken:
            flash("Decryption failed. Please unlock again.")
            return redirect(url_for("logout"))

        body = render_template_string(
            """
            <div class="card">
              <div class="row" style="justify-content:space-between;">
                <div>
                  <div style="font-weight:900; font-size:18px;">{{ r["title"] }}</div>
                  <div class="muted" style="font-size:12px; word-break:break-all;">{{ r["url"] }}</div>
                </div>
                <div class="row">
                  <a class="btn primary" target="_blank" rel="noreferrer" href="{{ r["url"] }}">↗ Open</a>
                  <a class="btn" href="{{ url_for('edit', site_id=r['id']) }}">✏ Edit</a>
                  <a class="btn ghost" href="{{ url_for('index') }}">← Home</a>
                </div>
              </div>
            </div>

            <div class="sep"></div>

            <div class="card">
              <h3 style="margin:0 0 8px 0;">🔐 Credentials</h3>
              <label>Username</label>
              <div class="row">
                <input id="u" value="{{ username }}" readonly />
                <button class="btn" type="button" onclick="copyText('u')">📋 Copy</button>
              </div>
              <label>Password</label>
              <div class="row">
                <input id="p" value="{{ password }}" readonly />
                <button class="btn" type="button" onclick="copyText('p')">📋 Copy</button>
              </div>
              <label>Notes</label>
              <div class="row">
                <textarea id="n" readonly>{{ notes }}</textarea>
                <button class="btn" type="button" onclick="copyText('n')">📋 Copy</button>
              </div>

              <div class="sep"></div>
              <form method="post" action="{{ url_for('delete', site_id=r['id']) }}" onsubmit="return confirm('Delete this entry?');">
                <button class="btn danger" type="submit">🗑 Delete</button>
              </form>
            </div>
            """,
            r=row,
            username=username,
            password=password,
            notes=notes,
        )
        return render_template_string(BASE_HTML, title="View", app_title=APP_TITLE, body=body)

    @app.route("/edit/<int:site_id>", methods=["GET", "POST"])
    def edit(site_id: int):
        gate = require_unlocked()
        if gate:
            return gate

        row = get_site_or_404(site_id)
        salt = get_salt(db_path)
        f = make_fernet(session["master"], salt)

        if request.method == "POST":
            title = (request.form.get("title") or "").strip()
            url = (request.form.get("url") or "").strip()
            username = request.form.get("username") or ""
            password = request.form.get("password") or ""
            notes = request.form.get("notes") or ""
            if not title or not url:
                flash("Title and URL are required.")
            else:
                con = connect(db_path)
                con.execute(
                    """
                    UPDATE sites
                    SET title=?, url=?, username_enc=?, password_enc=?, notes_enc=?, updated_at=?
                    WHERE id=?
                    """,
                    (
                        title,
                        url,
                        enc_optional(f, username),
                        enc_optional(f, password),
                        enc_optional(f, notes),
                        now_ts(),
                        site_id,
                    ),
                )
                con.commit()
                con.close()
                flash("Updated.")
                return redirect(url_for("view", site_id=site_id))

        try:
            username = dec_optional(f, row["username_enc"])
            password = dec_optional(f, row["password_enc"])
            notes = dec_optional(f, row["notes_enc"])
        except InvalidToken:
            flash("Decryption failed. Please unlock again.")
            return redirect(url_for("logout"))

        body = render_template_string(
            """
            <div class="card">
              <h2 style="margin:0 0 8px 0;">Edit site</h2>
              <form method="post">
                <label>Title</label>
                <input name="title" value="{{ r['title'] }}" required />
                <label>URL</label>
                <input name="url" value="{{ r['url'] }}" required />
                <label>Username (optional)</label>
                <input name="username" value="{{ username }}" autocomplete="username" />
                <label>Password (optional)</label>
                <input name="password" type="password" value="{{ password }}" autocomplete="current-password" />
                <label>Notes (optional)</label>
                <textarea name="notes">{{ notes }}</textarea>
                <div class="row" style="margin-top:14px;">
                  <button class="btn primary" type="submit">💾 Save</button>
                  <a class="btn ghost" href="{{ url_for('view', site_id=r['id']) }}">Cancel</a>
                </div>
              </form>
            </div>
            """,
            r=row,
            username=username,
            password=password,
            notes=notes,
        )
        return render_template_string(BASE_HTML, title="Edit", app_title=APP_TITLE, body=body)

    @app.route("/delete/<int:site_id>", methods=["POST"])
    def delete(site_id: int):
        gate = require_unlocked()
        if gate:
            return gate
        con = connect(db_path)
        con.execute("DELETE FROM sites WHERE id=?", (site_id,))
        con.commit()
        con.close()
        flash("Deleted.")
        return redirect(url_for("index"))

    # ---------- Settings ----------
    @app.route("/settings", methods=["GET"])
    def settings():
        gate = require_unlocked()
        if gate:
            return gate

        con = connect(db_path)
        bio_enabled = bool(meta_get(con, "bio_master_enc"))
        sq_is_enabled = bool(meta_get(con, "sq_blob"))
        con.close()

        body = render_template_string(
            """
            <div class="card">
              <h2 style="margin:0 0 8px 0;">Settings</h2>
              <div class="muted" style="font-size:12px;">Manage password, security questions, and biometrics.</div>

              <div class="sep"></div>

              <div class="row">
                <a class="btn primary" href="{{ url_for('change_password') }}">🔑 Change password</a>
                <a class="btn" href="{{ url_for('security_questions') }}">🛡️ Security questions {% if sq %}(On){% else %}(Off){% endif %}</a>
                <a class="btn" href="{{ url_for('biometric_settings') }}">🪪 Biometrics {% if bio %}(On){% else %}(Off){% endif %}</a>
                <a class="btn ghost" href="{{ url_for('index') }}">← Home</a>
              </div>
            </div>
            """,
            bio=bio_enabled,
            sq=sq_is_enabled,
        )
        return render_template_string(BASE_HTML, title="Settings", app_title=APP_TITLE, body=body)

    # Change password (re-encrypt everything)
    @app.route("/settings/change_password", methods=["GET", "POST"])
    def change_password():
        gate = require_unlocked()
        if gate:
            return gate

        if request.method == "POST":
            oldp = request.form.get("oldp") or ""
            newp1 = request.form.get("newp1") or ""
            newp2 = request.form.get("newp2") or ""

            if oldp != session.get("master"):
                flash("Old password is incorrect.")
            elif len(newp1) < 8:
                flash("New password must be at least 8 characters.")
            elif newp1 != newp2:
                flash("New passwords do not match.")
            else:
                # Re-encrypt all site fields with new password, keep same salt
                salt = get_salt(db_path)
                f_old = make_fernet(oldp, salt)
                f_new = make_fernet(newp1, salt)

                con = connect(db_path)
                rows = con.execute("SELECT id, username_enc, password_enc, notes_enc FROM sites").fetchall()
                for r in rows:
                    try:
                        u = dec_optional(f_old, r["username_enc"])
                        p = dec_optional(f_old, r["password_enc"])
                        n = dec_optional(f_old, r["notes_enc"])
                    except Exception:
                        con.close()
                        flash("Re-encryption failed. Vault may be locked. Try again.")
                        return redirect(url_for("change_password"))

                    con.execute(
                        "UPDATE sites SET username_enc=?, password_enc=?, notes_enc=?, updated_at=? WHERE id=?",
                        (
                            enc_optional(f_new, u),
                            enc_optional(f_new, p),
                            enc_optional(f_new, n),
                            now_ts(),
                            r["id"],
                        ),
                    )

                # Update verifier for new password
                verifier = f_new.encrypt(b"FaveSites verifier v1")
                meta_set(con, "verifier", verifier)

                # If biometrics enabled, re-encrypt stored master too
                bio_tok = meta_get(con, "bio_master_enc")
                if bio_tok:
                    meta_set(con, "bio_master_enc", bio_encrypt_master(data_dir, newp1))

                con.commit()
                con.close()

                # Update session master
                session["master"] = newp1
                flash("Password changed.")
                return redirect(url_for("settings"))

        body = render_template_string(
            """
            <div class="card">
              <h2 style="margin:0 0 8px 0;">Change password</h2>
              <form method="post">
                <label>Old password</label>
                <input type="password" name="oldp" required />
                <label>New password</label>
                <input type="password" name="newp1" required />
                <label>Confirm new password</label>
                <input type="password" name="newp2" required />
                <div class="row" style="margin-top:14px;">
                  <button class="btn primary" type="submit">Save</button>
                  <a class="btn ghost" href="{{ url_for('settings') }}">Cancel</a>
                </div>
              </form>
            </div>
            """,
        )
        return render_template_string(BASE_HTML, title="Change password", app_title=APP_TITLE, body=body)

    # Security questions settings (3 questions)
    @app.route("/settings/security_questions", methods=["GET", "POST"])
    def security_questions():
        gate = require_unlocked()
        if gate:
            return gate

        con = connect(db_path)
        blob = meta_get(con, "sq_blob")
        con.close()
        enabled = bool(blob)
        existing_q = sq_questions(db_path) if enabled else ["", "", ""]

        if request.method == "POST":
            action = (request.form.get("action") or "").strip()
            if action == "disable":
                con = connect(db_path)
                meta_del(con, "sq_blob")
                con.close()
                flash("Security questions disabled.")
                return redirect(url_for("security_questions"))

            # enable/update
            q1 = (request.form.get("q1") or "").strip()
            q2 = (request.form.get("q2") or "").strip()
            q3 = (request.form.get("q3") or "").strip()
            a1 = (request.form.get("a1") or "").strip()
            a2 = (request.form.get("a2") or "").strip()
            a3 = (request.form.get("a3") or "").strip()

            if not (q1 and q2 and q3 and a1 and a2 and a3):
                flash("Please fill all questions and answers.")
            else:
                blob2 = sq_pack([(q1, a1), (q2, a2), (q3, a3)])
                con = connect(db_path)
                meta_set(con, "sq_blob", blob2)
                con.close()
                flash("Security questions saved.")
                return redirect(url_for("security_questions"))

        body = render_template_string(
            """
            <div class="card">
              <h2 style="margin:0 0 8px 0;">Security questions</h2>
              <p class="muted" style="margin:0;">Acts like a local 2nd step after password/biometric unlock.</p>

              <div class="sep"></div>

              <form method="post">
                <input type="hidden" name="action" value="save" />
                <label>Question 1</label>
                <input name="q1" value="{{ q1 }}" placeholder="e.g., First school name?" required />
                <label>Answer 1</label>
                <input name="a1" placeholder="Answer" required />

                <label>Question 2</label>
                <input name="q2" value="{{ q2 }}" placeholder="e.g., Favorite city?" required />
                <label>Answer 2</label>
                <input name="a2" placeholder="Answer" required />

                <label>Question 3</label>
                <input name="q3" value="{{ q3 }}" placeholder="e.g., Pet name?" required />
                <label>Answer 3</label>
                <input name="a3" placeholder="Answer" required />

                <div class="row" style="margin-top:14px;">
                  <button class="btn primary" type="submit">Save / Enable</button>
                  <a class="btn ghost" href="{{ url_for('settings') }}">Back</a>
                </div>
              </form>

              {% if enabled %}
                <div class="sep"></div>
                <form method="post" onsubmit="return confirm('Disable security questions?');">
                  <input type="hidden" name="action" value="disable" />
                  <button class="btn danger" type="submit">Disable</button>
                </form>
              {% endif %}
            </div>
            """,
            enabled=enabled,
            q1=existing_q[0] if len(existing_q) > 0 else "",
            q2=existing_q[1] if len(existing_q) > 1 else "",
            q3=existing_q[2] if len(existing_q) > 2 else "",
        )
        return render_template_string(BASE_HTML, title="Security questions", app_title=APP_TITLE, body=body)

    # Biometrics settings
    @app.route("/settings/biometrics", methods=["GET", "POST"])
    def biometric_settings():
        gate = require_unlocked()
        if gate:
            return gate

        con = connect(db_path)
        token = meta_get(con, "bio_master_enc")
        con.close()
        enabled = bool(token)
        avail = biometric_available()

        if request.method == "POST":
            action = (request.form.get("action") or "").strip()
            if action == "enable":
                if not avail:
                    flash("Biometrics not available. Install Termux:API app + pkg termux-api.")
                else:
                    # require a biometric prompt to enable
                    if not termux_biometric_check():
                        flash("Biometric check cancelled.")
                    else:
                        con = connect(db_path)
                        meta_set(con, "bio_master_enc", bio_encrypt_master(data_dir, session["master"]))
                        con.close()
                        flash("Biometric quick unlock enabled.")
                        return redirect(url_for("biometric_settings"))
            elif action == "disable":
                con = connect(db_path)
                meta_del(con, "bio_master_enc")
                con.close()
                flash("Biometric quick unlock disabled.")
                return redirect(url_for("biometric_settings"))

        body = render_template_string(
            """
            <div class="card">
              <h2 style="margin:0 0 8px 0;">Biometrics</h2>
              <p class="muted" style="margin:0;">Enable/disable fingerprint/face quick unlock (Termux:API).</p>

              <div class="sep"></div>

              <div class="muted" style="font-size:12px;">
                Availability: {% if avail %}<b>Detected</b>{% else %}<b>Not detected</b>{% endif %}
                · Command: <code>termux-fingerprint</code>
              </div>

              <div class="sep"></div>

              {% if enabled %}
                <form method="post" onsubmit="return confirm('Disable biometrics?');">
                  <input type="hidden" name="action" value="disable" />
                  <button class="btn danger" type="submit">Disable</button>
                </form>
              {% else %}
                <form method="post">
                  <input type="hidden" name="action" value="enable" />
                  <button class="btn primary" type="submit">Enable</button>
                </form>
              {% endif %}

              <div class="sep"></div>
              <a class="btn ghost" href="{{ url_for('settings') }}">Back</a>
            </div>
            """,
            enabled=enabled,
            avail=avail,
        )
        return render_template_string(BASE_HTML, title="Biometrics", app_title=APP_TITLE, body=body)

    return app



# ---------------------------
# Default storage directory
# ---------------------------

def default_data_dir() -> Path:
    """
    Where to store persistent data by default.

    - Termux: use shared storage so it's visible in Android file manager:
        ~/storage/shared/FaveSites
      (requires: termux-setup-storage at least once)

    - Other systems: use a hidden folder in the user's home:
        ~/.favesites
    """
    home = Path.home()
    if _is_termux():
        shared = home / "storage" / "shared"
        # If shared storage isn't set up yet, fall back to home folder.
        if shared.exists():
            return shared / "FaveSites"
        return home / "FaveSites"
    return home / ".favesites"

# ---------------------------
# Auto-open browser
# ---------------------------

def open_in_browser(url: str) -> None:
    try:
        if which("termux-open-url"):
            subprocess.Popen(["termux-open-url", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        if which("xdg-open"):
            subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
    except Exception:
        pass
    print(f"[{APP_TITLE}] Open this in your browser: {url}")


def open_after_delay(url: str, delay: float = 0.8) -> None:
    def _worker():
        time.sleep(delay)
        open_in_browser(url)
    threading.Thread(target=_worker, daemon=True).start()


def main():
    parser = argparse.ArgumentParser(description="FaveSites — local favorites launcher + encrypted credential vault")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="Port to serve on (default: 5000)")
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Directory to store data (default: Termux shared storage ~/storage/shared/FaveSites, otherwise ~/.favesites)"
    )
    parser.add_argument("--no-open", action="store_true", help="Don't auto-open the browser")
    args = parser.parse_args()

    if args.data_dir:
        data_dir = Path(args.data_dir).expanduser().resolve()
    else:
        data_dir = default_data_dir()

    data_dir.mkdir(parents=True, exist_ok=True)

    app = create_app(data_dir)

    url = f"http://{args.host}:{args.port}"
    print(f"[{APP_TITLE}] Starting on {url}")
    print(f"[{APP_TITLE}] Database: {data_dir / DB_NAME}")
    print(f"[{APP_TITLE}] Press Ctrl+C to stop.")

    if not args.no_open:
        open_after_delay(url)

    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
