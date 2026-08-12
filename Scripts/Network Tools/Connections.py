#!/usr/bin/env python3
# Connections + DedSec's Database (Unified Login Script)

import os
import json
import ipaddress
import sys
import time
import re
import subprocess
import shutil
import socket
import secrets
import signal
import threading
import mimetypes
import datetime
import contextlib
import pathlib
import logging
import functools
import atexit
from collections import OrderedDict

# Import the only non-stdlib runtime dependencies.
#
# Important for Termux: this project does NOT require pyca/cryptography. The
# previous self-signed-certificate helper was unused by the running server and
# forced pip to compile a Rust-backed package on Android. Cloudflare/Tor provide
# the secure remote transports used by this script, so removing that dependency
# makes startup smaller, more reliable, and reduces the dependency attack surface.
def _import_runtime_dependencies():
    try:
        from flask import (
            Flask, Blueprint, flash, get_flashed_messages, redirect, g,
            render_template_string, request, send_from_directory, session,
            url_for,
        )
        from flask_socketio import SocketIO, emit, join_room, leave_room
    except ImportError:
        packages = ["flask", "flask-socketio"]
        print("Installing required Python packages...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--no-cache-dir", *packages],
                check=True,
            )
        except Exception as exc:
            raise SystemExit(f"FATAL: Could not install required Python packages: {exc}")

        from flask import (
            Flask, Blueprint, flash, get_flashed_messages, redirect, g,
            render_template_string, request, send_from_directory, session,
            url_for,
        )
        from flask_socketio import SocketIO, emit, join_room, leave_room

    return {
        "Flask": Flask,
        "Blueprint": Blueprint,
        "flash": flash,
        "get_flashed_messages": get_flashed_messages,
        "redirect": redirect,
        "g": g,
        "render_template_string": render_template_string,
        "request": request,
        "send_from_directory": send_from_directory,
        "session": session,
        "url_for": url_for,
        "SocketIO": SocketIO,
        "emit": emit,
        "join_room": join_room,
        "leave_room": leave_room,
    }

_runtime = _import_runtime_dependencies()
globals().update(_runtime)
del _runtime

# ----------------------------
# Termux-aware helper functions
# ----------------------------
def _is_termux():
    return os.path.isdir("/data/data/com.termux/files/usr")

def _termux_install_package(binary_name, package_name):
    """Best-effort install of an optional Termux package without running pkg update."""
    if shutil.which(binary_name):
        return True
    try:
        result = subprocess.run(
            ["pkg", "install", "-y", package_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0 and shutil.which(binary_name) is not None
    except Exception:
        return False

def install_requirements(termux_opt=True):
    # Flask and Flask-SocketIO are already guaranteed by the bootstrap above.
    print("Python requirements satisfied.")
    if termux_opt and _is_termux():
        print("Checking optional Termux transports (cloudflared, tor)...")
        for binary, package in (("cloudflared", "cloudflared"), ("tor", "tor")):
            if not _termux_install_package(binary, package):
                print(f"WARNING: optional package '{package}' is unavailable; {binary} transport will be skipped.")
    return

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Use a public DNS server to find the most likely outbound IP
        s.connect(('8.8.8.8', 80))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def start_server_process(secret_key, verbose_mode, allow_lan=False):
    """Start the server while keeping the login secret out of argv/environment."""
    cmd = [sys.executable, __file__, "--server"]
    if not verbose_mode:
        cmd.append("--quiet")
    if allow_lan:
        cmd.append("--allow-lan")

    child_env = os.environ.copy()
    child_env.pop("CONNECTIONS_SECRET_KEY", None)

    # POSIX/Termux: transfer the secret through an anonymous inherited pipe. The
    # child receives only the FD number in its environment, not the secret itself.
    if os.name == "posix":
        read_fd, write_fd = os.pipe()
        os.set_inheritable(read_fd, True)
        child_env["CONNECTIONS_SECRET_FD"] = str(read_fd)
        try:
            process = subprocess.Popen(
                cmd, env=child_env, pass_fds=(read_fd,), close_fds=True
            )
        finally:
            os.close(read_fd)
        try:
            os.write(write_fd, secret_key.encode("utf-8"))
        finally:
            os.close(write_fd)
        return process

    # Compatibility fallback for non-POSIX platforms. Termux never uses this.
    child_env["CONNECTIONS_SECRET_KEY"] = secret_key
    return subprocess.Popen(cmd, env=child_env)

def _read_server_secret():
    """Read the one-time login secret once, preferring the anonymous pipe."""
    fd_text = os.environ.pop("CONNECTIONS_SECRET_FD", None)
    if fd_text:
        try:
            fd = int(fd_text)
            chunks = []
            total = 0
            while total <= 1024:
                chunk = os.read(fd, min(256, 1025 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
            os.close(fd)
            if total > 1024:
                return None
            return b"".join(chunks).decode("utf-8", "strict")
        except Exception:
            try:
                os.close(int(fd_text))
            except Exception:
                pass
            return None

    # Explicit/manual server launches can use this compatibility fallback.
    return os.environ.pop("CONNECTIONS_SECRET_KEY", None)

def wait_for_server(url, timeout=20):
    print(f"Waiting for local server at {url}...")
    start_time = time.time()
    from urllib.request import urlopen
    while time.time() - start_time < timeout:
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    print(f"Server at {url} is up and running.")
                    return True
        except Exception:
            time.sleep(0.5)
    print(f"Error: Local server at {url} did not start within the timeout period.")
    return False

# Resource limits. Chat files are uploaded over a streamed HTTP endpoint instead
# of being embedded as base64 inside Socket.IO packets. This keeps a 150 MiB file
# from expanding to ~200 MiB of base64 and being copied repeatedly through browser
# and Python memory. Database files use the same per-file ceiling.
CHAT_FILE_MAX_BYTES = 150 * 1024 * 1024         # 150 MiB per chat attachment
CHAT_TOTAL_QUOTA_BYTES = 2 * 1024 * 1024 * 1024 # 2 GiB ephemeral chat-file quota
CHAT_PER_CLIENT_QUOTA_BYTES = 600 * 1024 * 1024   # 600 MiB per sender
CHAT_CHUNK_BYTES = 8 * 1024 * 1024              # 8 MiB per HTTP request
CHAT_REQUEST_MAX_BYTES = CHAT_CHUNK_BYTES + (256 * 1024)
SOCKET_MAX_PACKET_BYTES = 1024 * 1024            # files never travel in Socket.IO
DB_FILE_MAX_BYTES = 150 * 1024 * 1024            # 150 MiB per Database file
DB_CHUNK_BYTES = 8 * 1024 * 1024                 # 8 MiB per Database upload request
DB_TOTAL_QUOTA_BYTES = 8 * 1024 * 1024 * 1024   # 8 GiB total Database quota
DB_REQUEST_MAX_BYTES = DB_CHUNK_BYTES + (256 * 1024)
UPLOAD_CHUNK_BYTES = 1024 * 1024

@contextlib.contextmanager
def suppress_stdout_stderr():
    """Suppresses console output for cleaner execution."""
    with open(os.devnull, 'w') as devnull:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = devnull, devnull
        try:
            yield
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

def start_cloudflared_tunnel(port, proto="http", name=""):
    """Starts a cloudflared tunnel, reads output for the URL, and lets the process run."""
    print(f"🚀 Starting Cloudflare tunnel for {name} (port {port})... please wait.")
    
    cmd = ["cloudflared", "tunnel", "--no-autoupdate", "--url", f"{proto}://localhost:{port}"]

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        
        start_time = time.time()
        # Wait up to 15s for the URL
        while time.time() - start_time < 15:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                print(f"⚠️ Cloudflare process for {name} exited unexpectedly.")
                return None, None
                
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if match:
                online_url = match.group(0)
                print(f"✅ Cloudflare tunnel for {name} is live.")
                return process, online_url
            
            time.sleep(0.2)

        print(f"⚠️ Could not find Cloudflare URL for {name} in output.")
        return process, None # Return process anyway, maybe it's just slow

    except Exception as e:
        print(f"❌ Failed to start Cloudflare tunnel for {name}: {e}")
        return None, None



# ----------------------------
# Tor Hidden Service (Onion) Helper
# ----------------------------
def start_tor_hidden_service(local_http_port=5000, hs_virtual_port=80, name="Connections"):
    """Starts Tor with an ephemeral hidden service that maps hs_virtual_port -> localhost:local_https_port.
    Returns (tor_process, onion_url, hs_dir).
    """
    if shutil.which("tor") is None:
        return None, None, None

    base_dir = pathlib.Path.home() / ".foxchat_tor"
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        base_dir = pathlib.Path(".foxchat_tor")
        base_dir.mkdir(parents=True, exist_ok=True)

    # Use a fresh hidden-service dir each run (so onion changes every time)
    run_id = secrets.token_hex(4)
    tor_data_dir = base_dir / f"data_{run_id}"
    hs_dir = base_dir / f"hs_{run_id}"
    tor_data_dir.mkdir(parents=True, exist_ok=True)
    hs_dir.mkdir(parents=True, exist_ok=True)

    # Best-effort permission hardening (Tor prefers 0700 on *nix)
    try:
        os.chmod(tor_data_dir, 0o700)
        os.chmod(hs_dir, 0o700)
    except Exception:
        pass

    torrc_path = base_dir / f"torrc_{run_id}"
    torrc = "\n".join([
        f"DataDirectory {tor_data_dir}",
        "SocksPort 0",
        "ControlPort 0",
        "Log notice stdout",
        "HiddenServiceVersion 3",
        f"HiddenServiceDir {hs_dir}",
        f"HiddenServicePort {hs_virtual_port} 127.0.0.1:{local_http_port}",
    ]) + "\n"

    torrc_path.write_text(torrc, encoding="utf-8")
    try:
        os.chmod(torrc_path, 0o600)
    except Exception:
        pass

    print(f"🧅 Starting Tor hidden service for {name}... please wait.")
    try:
        proc = subprocess.Popen(
            ["tor", "-f", str(torrc_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        # Private onion keys/data are ephemeral for this run and are removed on shutdown.
        proc._connections_cleanup_paths = [hs_dir, tor_data_dir, torrc_path]
    except Exception as e:
        print(f"❌ Failed to start Tor: {e}")
        return None, None, None

    hostname_file = hs_dir / "hostname"
    start_time = time.time()
    onion_host = None

    # Wait up to 45 seconds for hostname to appear
    while time.time() - start_time < 45:
        if proc.poll() is not None:
            print("⚠️ Tor exited unexpectedly.")
            break
        try:
            if hostname_file.exists():
                onion_host = hostname_file.read_text(encoding="utf-8").strip()
                if onion_host:
                    break
        except Exception:
            pass
        time.sleep(0.5)

    if onion_host:
        onion_url = f"http://{onion_host}" if hs_virtual_port in (80, 0) else f"http://{onion_host}:{hs_virtual_port}"
        print("✅ Tor hidden service is live.")
        return proc, onion_url, hs_dir

    print("⚠️ Could not obtain onion address (hostname not found).")
    return proc, None, hs_dir


def graceful_shutdown(signum, frame):
    print("Shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)


# -------------------------------------------------------------------
#
# PART 1: DEDSEC'S DATABASE CODE (as a Blueprint)
#
# -------------------------------------------------------------------

# Create a Blueprint for the Database, prefixed with /db
db_blueprint = Blueprint('database', __name__, url_prefix='/db')

# ==== GLOBAL CONFIG & APP SETUP ====
SERVER_PASSWORD = None # This will be set by the server main function

# --- MODIFIED: Use the user's Downloads folder for storage ---
# This provides a cross-platform way to access the user's main downloads directory.
try:
    DOWNLOADS_DIR = pathlib.Path.home() / "Downloads"
    BASE_DIR = DOWNLOADS_DIR / "DedSec's Database"
    BASE_DIR.mkdir(exist_ok=True, parents=True)
except Exception as e:
    print(f"WARNING: Could not create directory in Downloads folder ({e}). Using a local folder instead.")
    BASE_DIR = pathlib.Path("DedSec_Database_Files")
    BASE_DIR.mkdir(exist_ok=True)

DB_PENDING_UPLOADS = {}
DB_UPLOAD_LOCK = threading.RLock()
DB_UPLOAD_SLOTS = threading.BoundedSemaphore(4)
DB_UPLOAD_ID_RE = re.compile(r'^[A-Za-z0-9_-]{20,80}$')
try:
    os.chmod(BASE_DIR, 0o700)
except OSError:
    pass
try:
    for _temp_path in BASE_DIR.glob('.dbchunk-*.part'):
        if _temp_path.is_file() or _temp_path.is_symlink():
            _temp_path.unlink(missing_ok=True)
except OSError:
    pass

# Define file categories for organization
FILE_CATEGORIES = {
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
    'Videos': ['.mp4', '.mov', '.avi', '.mkv', '.webm'],
    'Audio': ['.mp3', '.wav', '.ogg', '.flac'],
    'Documents': ['.pdf', '.doc', '.docx', '.txt', '.ppt', '.pptx', '.xls', '.xlsx', '.md', '.csv'],
    'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'Code': ['.py', '.js', '.html', '.css', '.json', '.xml', '.sh', '.c', '.cpp'],
}

# ==== HELPER FUNCTIONS ====
def get_file_info(filename):
    """Gathers metadata for a given file path. Skips directories."""
    try:
        full_path = BASE_DIR / filename
        
        if full_path.is_dir() or full_path.is_symlink():
            return None

        stat_info = full_path.stat()
        size_raw = stat_info.st_size
        mtime = stat_info.st_mtime
        file_type = mimetypes.guess_type(full_path)[0] or "Unknown"

        return {
            "size": size_raw,
            "mtime": mtime,
            "mtime_str": datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "mimetype": file_type,
        }
    except Exception:
        return None

def get_file_category(filename):
    """Returns the category of a file based on its extension."""
    ext = pathlib.Path(filename).suffix.lower()
    for category, extensions in FILE_CATEGORIES.items():
        if ext in extensions:
            return category
    return 'Other'


def _database_usage_bytes():
    total = 0
    try:
        for path in BASE_DIR.iterdir():
            try:
                if path.name.startswith(('.dbchunk-', '.upload-')):
                    continue
                if path.is_file() and not path.is_symlink():
                    total += path.stat().st_size
            except OSError:
                continue
    except OSError:
        pass
    return total

def _sanitize_upload_name(name):
    name = os.path.basename(str(name or "file")).strip()
    name = re.sub(r"[\x00-\x1f\x7f]", "_", name)
    if name in ("", ".", ".."):
        name = "file"
    # Keep room for duplicate suffixes and filesystem encoding overhead.
    return name[:220]

def _unique_database_target(filename):
    candidate = BASE_DIR / _sanitize_upload_name(filename)
    if not candidate.exists() and not candidate.is_symlink():
        return candidate
    stem, suffix = candidate.stem, candidate.suffix
    for index in range(1, 10000):
        alt = BASE_DIR / f"{stem} ({index}){suffix}"
        if not alt.exists() and not alt.is_symlink():
            return alt
    raise RuntimeError("Could not allocate a unique filename")

def _db_abort_pending_upload(upload_id):
    with DB_UPLOAD_LOCK:
        meta = DB_PENDING_UPLOADS.get(upload_id)
    if not meta:
        return
    upload_lock = meta.get('lock') or contextlib.nullcontext()
    with upload_lock:
        with DB_UPLOAD_LOCK:
            meta = DB_PENDING_UPLOADS.pop(upload_id, None)
        if not meta:
            return
        try:
            temp = BASE_DIR / meta.get('temp_name', '')
            if temp.parent == BASE_DIR and (temp.is_file() or temp.is_symlink()):
                temp.unlink(missing_ok=True)
        except Exception:
            pass


def _db_prune_stale_uploads(max_age_seconds=900):
    now = time.time()
    stale = []
    with DB_UPLOAD_LOCK:
        for upload_id, meta in list(DB_PENDING_UPLOADS.items()):
            if now - float(meta.get('last_activity', meta.get('created_at', now))) > max_age_seconds:
                stale.append(upload_id)
    for upload_id in stale:
        _db_abort_pending_upload(upload_id)


def _db_reserved_bytes_locked():
    total = 0
    for meta in DB_PENDING_UPLOADS.values():
        try:
            total += int(meta.get('expected_size', 0))
        except Exception:
            continue
    return total


def _db_create_pending_upload(owner_id, filename, expected_size):
    _db_prune_stale_uploads()
    filename = _sanitize_upload_name(filename)
    expected_size = int(expected_size)
    if expected_size <= 0 or expected_size > DB_FILE_MAX_BYTES:
        raise ValueError('file must be between 1 byte and 150 MB')

    with DB_UPLOAD_LOCK:
        if _database_usage_bytes() + _db_reserved_bytes_locked() + expected_size > DB_TOTAL_QUOTA_BYTES:
            raise ValueError('Database storage quota would be exceeded')
        owner_pending = sum(1 for m in DB_PENDING_UPLOADS.values() if m.get('owner_id') == owner_id)
        if owner_pending >= 2:
            raise ValueError('too many Database uploads are already in progress')
        if len(DB_PENDING_UPLOADS) >= 12:
            raise ValueError('the server already has too many Database uploads in progress')

        upload_id = secrets.token_urlsafe(24)
        temp_name = f'.dbchunk-{upload_id}-{secrets.token_hex(6)}.part'
        temp = BASE_DIR / temp_name
        with open(temp, 'xb'):
            pass
        try:
            os.chmod(temp, 0o600)
        except OSError:
            pass
        now = time.time()
        DB_PENDING_UPLOADS[upload_id] = {
            'upload_id': upload_id,
            'temp_name': temp_name,
            'filename': filename,
            'expected_size': expected_size,
            'received': 0,
            'next_index': 0,
            'owner_id': owner_id,
            'created_at': now,
            'last_activity': now,
            'lock': threading.Lock(),
        }
        return dict(DB_PENDING_UPLOADS[upload_id])


def _db_append_upload_chunk(upload_id, owner_id, chunk_index, stream, content_length=None):
    if not DB_UPLOAD_SLOTS.acquire(blocking=False):
        raise RuntimeError('too many Database upload chunks are being processed')
    try:
        with DB_UPLOAD_LOCK:
            meta = DB_PENDING_UPLOADS.get(upload_id)
            if not meta or meta.get('owner_id') != owner_id:
                raise PermissionError('upload not found')
            upload_lock = meta.get('lock')
        if upload_lock is None:
            raise ValueError('upload state is invalid')

        with upload_lock:
            with DB_UPLOAD_LOCK:
                meta = DB_PENDING_UPLOADS.get(upload_id)
                if not meta or meta.get('owner_id') != owner_id:
                    raise PermissionError('upload not found')
                if int(chunk_index) != int(meta.get('next_index', -1)):
                    raise ValueError('unexpected upload chunk order')
                remaining = int(meta['expected_size']) - int(meta['received'])
                if remaining <= 0:
                    raise ValueError('upload is already complete')
                expected_chunk_size = min(DB_CHUNK_BYTES, remaining)
                temp_name = meta['temp_name']
                expected_offset = int(meta['received'])
            if content_length is not None and int(content_length) != expected_chunk_size:
                raise ValueError('upload chunk has the wrong size')

            temp = BASE_DIR / temp_name
            if not temp.is_file() or temp.is_symlink() or temp.parent != BASE_DIR:
                raise ValueError('temporary Database upload file could not be verified')
            if temp.stat().st_size != expected_offset:
                raise ValueError('temporary Database upload size does not match state')

            written = 0
            try:
                with open(temp, 'ab') as handle:
                    while written < expected_chunk_size:
                        chunk = stream.read(min(UPLOAD_CHUNK_BYTES, expected_chunk_size - written))
                        if not chunk:
                            break
                        written += len(chunk)
                        handle.write(chunk)
                    if stream.read(1):
                        raise ValueError('upload chunk is too large')
                    handle.flush()
                if written != expected_chunk_size:
                    raise ValueError('upload chunk has the wrong size')
            except Exception:
                try:
                    with open(temp, 'r+b') as handle:
                        handle.truncate(expected_offset)
                except Exception:
                    pass
                raise

            with DB_UPLOAD_LOCK:
                meta = DB_PENDING_UPLOADS.get(upload_id)
                if not meta or meta.get('owner_id') != owner_id:
                    raise PermissionError('upload no longer exists')
                if int(meta.get('next_index', -1)) != int(chunk_index) or int(meta.get('received', -1)) != expected_offset:
                    raise ValueError('Database upload state changed unexpectedly')
                meta['received'] = expected_offset + written
                meta['next_index'] = int(meta['next_index']) + 1
                meta['last_activity'] = time.time()
                return int(meta['received']), int(meta['expected_size'])
    finally:
        DB_UPLOAD_SLOTS.release()


def _db_complete_upload(upload_id, owner_id):
    with DB_UPLOAD_LOCK:
        meta = DB_PENDING_UPLOADS.get(upload_id)
        if not meta or meta.get('owner_id') != owner_id:
            raise PermissionError('upload not found')
        upload_lock = meta.get('lock')
    if upload_lock is None:
        raise ValueError('upload state is invalid')

    with upload_lock:
        with DB_UPLOAD_LOCK:
            meta = DB_PENDING_UPLOADS.get(upload_id)
            if not meta or meta.get('owner_id') != owner_id:
                raise PermissionError('upload not found')
            if int(meta.get('received', 0)) != int(meta.get('expected_size', -1)):
                raise ValueError('upload is incomplete')
            meta = dict(meta)

        temp = BASE_DIR / meta['temp_name']
        if not temp.is_file() or temp.is_symlink() or temp.parent != BASE_DIR:
            raise ValueError('temporary Database upload file could not be verified')
        actual_size = temp.stat().st_size
        if actual_size != int(meta['expected_size']) or actual_size > DB_FILE_MAX_BYTES:
            raise ValueError('uploaded Database file size verification failed')

        with DB_UPLOAD_LOCK:
            current = DB_PENDING_UPLOADS.get(upload_id)
            if not current or current.get('owner_id') != owner_id:
                raise PermissionError('upload no longer exists')
            target = _unique_database_target(meta['filename'])
            os.replace(temp, target)
            try:
                os.chmod(target, 0o600)
            except OSError:
                pass
            DB_PENDING_UPLOADS.pop(upload_id, None)
            return target.name, actual_size

def _cleanup_db_pending_uploads():
    """Remove incomplete Database upload fragments on clean shutdown."""
    with DB_UPLOAD_LOCK:
        upload_ids = list(DB_PENDING_UPLOADS.keys())
    for upload_id in upload_ids:
        _db_abort_pending_upload(upload_id)


atexit.register(_cleanup_db_pending_uploads)


def filesizeformat(value):
    """Formats a file size in bytes into a human-readable string."""
    try:
        if value < 1024: return f"{value} B"
        for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} PB"
    except Exception:
        return "0 B"

# Register the filter with the blueprint
db_blueprint.add_app_template_filter(filesizeformat, 'filesizeformat')

# ==== DB AUTHENTICATION HELPERS ====

def _get_server_secret_key():
    # The child server receives this through an anonymous pipe at startup.
    key = globals().get("SECRET_KEY_SERVER")
    if key:
        return key
    # Compatibility fallback for an explicitly/manual server launch only.
    return os.environ.get("CONNECTIONS_SECRET_KEY")

# ==== DB AUTHENTICATION DECORATOR ====
# This decorator protects the DB routes
def db_auth_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('db_logged_in'):
            return redirect(url_for('index_chat'))
        return f(*args, **kwargs)
    return decorated_function

def _valid_csrf():
    expected = session.get('csrf_token', '')
    supplied = request.form.get('csrf_token', '') or request.headers.get('X-CSRF-Token', '')
    return bool(expected and supplied and secrets.compare_digest(str(expected), str(supplied)))

# Authenticate the Database without placing the secret key in the URL/history.
@db_blueprint.route("/auth", methods=["POST"])
def db_auth_bridge():
    ip = request.remote_addr or 'unknown'
    server_key = _get_server_secret_key() or ""
    token = request.headers.get("X-Connections-Key", "")
    valid = (
        isinstance(token, str) and 32 <= len(token) <= 256 and server_key and
        secrets.compare_digest(token, server_key)
    )
    if valid:
        _clear_auth_failures(ip)
        # Preserve the already-authenticated chat session when the Database opens.
        session["db_logged_in"] = True
        if not isinstance(session.get("db_session_id"), str) or len(session.get("db_session_id", "")) < 20:
            session["db_session_id"] = secrets.token_urlsafe(24)
        session["csrf_token"] = secrets.token_urlsafe(32)
        return "OK", 200

    if _auth_rate_limited(ip):
        return "Too Many Attempts", 429
    _record_auth_failure(ip)
    return "Forbidden", 403

# ==== HTML TEMPLATES (DB) ====
# Note: url_for() is now used for all links/actions
html_template_db = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=yes" />
<title>DedSec's Database</title>
<style>
    :root {
        --bg-color-main: #121212;
        --bg-color-header: #1e1e1e;
        --bg-color-input: #1e1e1e;
        --bg-color-input-field: #2c2c2c;
        --bg-color-bubble-self: #3737a1;
        --bg-color-bubble-other: #3a3a3a;
        --text-color-main: #e0e0e0;
        --text-color-muted: #a5a5a5;
        --accent: #3737a1;
        --border: rgba(255,255,255,0.08);
        --shadow: 0 10px 30px rgba(0,0,0,0.35);
        --radius: 16px;
    }
    body {
        background-color: var(--bg-color-main);
        color: var(--text-color-main);
        font-family: 'Segoe UI', sans-serif;
        margin: 0;
        padding: 10px;
    }
    .container {
        background-color: var(--bg-color-header); padding: 15px; border-radius: var(--radius); margin: auto;
        box-shadow: 0 0 25px rgba(128, 0, 128, 0.6); border: 1px solid #800080;
        max-width: 100%;
        min-height: 90vh;
    }
    h1 { color: #fff; text-align: center; border-bottom: 1px solid #4a2f4a; padding-bottom: 10px; margin-top: 6px; }
    h2 { margin-top: 25px; font-size: 1.2em; color: #c080c0; border-left: 5px solid #800080; padding-left: 10px; }

    .flash { padding: 10px; margin-bottom: 15px; border-radius: 5px; font-weight: bold; }
    .flash.success { background-color: #004d00; border: 1px solid #00ff00; color: #00ff00; }
    .flash.error { background-color: #4d0000; border: 1px solid #ff4d4d; color: #ff4d4d; }
    .flash.warning { background-color: #4d4d00; border: 1px solid #ffff00; color: #ffff00; }

    .form-group {
        display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 15px; padding: 10px;
        background: #2a1f39; border-radius: 6px;
    }
    input, select, .button {
        padding: 8px; border-radius: 4px; border: 1px solid #4a2f4a; background: #1a0f29; color: #fff;
        box-sizing: border-box;
    }
    input[type="submit"] {
        background-color: #000; color: #fff; cursor: pointer; border-color: #800080; transition: all 0.3s ease;
    }
    input[type="submit"]:hover { background-color: #800080; box-shadow: 0 0 10px #800080; }

    .manager-section {
        margin-top: 14px;
        background: #3a2f49;
        padding: 10px;
        border-radius: var(--radius);
        text-align: center;
    }
    .icon-button {
        padding: 10px 15px;
        font-size: 1em;
        font-weight: bold;
        background-color: #000;
        color: #fff;
        border: 1px solid #800080;
        cursor: pointer;
        border-radius: var(--radius);
        transition: all 0.3s ease;
        display: inline-block;
        margin: 5px 0;
    }
    .icon-button:hover { background-color: #800080; box-shadow: 0 0 10px #800080; }

    .file-item {
        background: #2a1f39; padding: 10px 12px; border-radius: var(--radius); display: flex;
        flex-direction: column; align-items: flex-start; gap: 10px; margin-bottom: 8px;
        transition: background-color 0.2s ease;
        max-width: 100%; box-sizing: border-box;
    }
    .file-item:hover { background: #3a2f49; }
    .filename {
        flex-grow: 1; font-weight: 700;
        word-wrap: break-word; white-space: normal;
        max-width: 100%;
        font-size: 1.05em;
        letter-spacing: 0.2px;
    }
    .buttons { display: flex; gap: 6px; flex-wrap: wrap; max-width: 100%; }
    .button {
        text-decoration: none; font-size: 0.9em; padding: 8px 12px;
        background-color: #000;
        border-radius: var(--radius);
        border: 1px solid #800080;
        color: #fff;
        cursor: pointer;
        transition: all 0.25s ease;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .button:hover { background-color: #800080; box-shadow: 0 0 10px rgba(128,0,128,0.45); }
    .delete-button { background-color:#8b0000; border-color: #ff4d4d; }
    .delete-button:hover { background-color:#ff4d4d; box-shadow: 0 0 10px rgba(255,77,77,0.45); }

    .info-popup {
        display: none; position: absolute; background: #1a0f29; border: 1px solid #800080; border-radius: var(--radius);
        padding: 10px; color: #e0e0e0; z-index: 10; box-shadow: 0 8px 20px rgba(0,0,0,0.55); font-size: 0.9em;
        max-width: 260px;
    }

    @media (min-width: 600px) {
        .file-item { flex-direction: row; align-items: center; }
    }

    .footer { text-align: center; margin-top: 20px; font-size: 0.8em; color: #6a4f6a; }

    .topbar{
        display:flex;
        justify-content:flex-start;
        align-items:center;
        margin-bottom:12px;
    }
    .back-btn{
        display:inline-flex;
        align-items:center;
        gap:8px;
        padding:10px 14px;
        border-radius:12px;
        text-decoration:none;
        color: var(--text-color-main);
        background: var(--bg-color-item);
        border: 1px solid rgba(255,255,255,0.10);
    }
    .back-btn:active{ transform: scale(0.98); }

</style>
<script nonce="{{ g.csp_nonce }}">
    function toggleInfo(event, id) {
        event.stopPropagation();
        document.querySelectorAll('.info-popup').forEach(p => {
            if (p.id !== 'info-' + id) p.style.display = 'none';
        });
        const popup = document.getElementById('info-' + id);
        if (popup) popup.style.display = popup.style.display === 'block' ? 'none' : 'block';
    }
    const DB_MAX_FILE_SIZE = 150 * 1024 * 1024;

    async function uploadDatabaseFile(file) {
        if (!file) return;
        if (file.size <= 0) {
            alert('Empty files cannot be uploaded.');
            return;
        }
        if (file.size > DB_MAX_FILE_SIZE) {
            alert('File is too large. Maximum file size is 150 MB.');
            return;
        }
        const csrfEl = document.getElementById('db-csrf-token');
        const statusEl = document.getElementById('db-upload-status');
        const csrf = csrfEl ? csrfEl.value : '';
        if (!csrf) {
            alert('Database session token is missing. Reload the page and try again.');
            return;
        }

        let uploadId = '';
        try {
            if (statusEl) statusEl.textContent = `Preparing ${file.name}...`;
            const initResponse = await fetch('/db/upload/init', {
                method: 'POST',
                credentials: 'same-origin',
                cache: 'no-store',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrf
                },
                body: JSON.stringify({ filename: file.name, size: file.size })
            });
            const initData = await initResponse.json().catch(() => ({}));
            if (!initResponse.ok || !initData.ok || !initData.upload_id) {
                throw new Error(initData.error || 'Could not initialize Database upload.');
            }

            uploadId = initData.upload_id;
            const chunkSize = Math.max(256 * 1024, Math.min(Number(initData.chunk_size) || (8 * 1024 * 1024), 8 * 1024 * 1024));
            let offset = 0;
            let chunkIndex = 0;
            while (offset < file.size) {
                const end = Math.min(offset + chunkSize, file.size);
                const chunk = file.slice(offset, end);
                if (statusEl) statusEl.textContent = `Uploading ${file.name}... ${Math.floor((offset / file.size) * 100)}%`;
                const response = await fetch(`/db/upload/${encodeURIComponent(uploadId)}/chunk`, {
                    method: 'POST',
                    credentials: 'same-origin',
                    cache: 'no-store',
                    headers: {
                        'Content-Type': 'application/octet-stream',
                        'X-CSRF-Token': csrf,
                        'X-Chunk-Index': String(chunkIndex)
                    },
                    body: chunk
                });
                const data = await response.json().catch(() => ({}));
                if (!response.ok || !data.ok) throw new Error(data.error || `Upload failed at chunk ${chunkIndex + 1}.`);
                offset = end;
                chunkIndex += 1;
            }

            if (statusEl) statusEl.textContent = `Finalizing ${file.name}...`;
            const completeResponse = await fetch(`/db/upload/${encodeURIComponent(uploadId)}/complete`, {
                method: 'POST',
                credentials: 'same-origin',
                cache: 'no-store',
                headers: { 'X-CSRF-Token': csrf }
            });
            const completeData = await completeResponse.json().catch(() => ({}));
            if (!completeResponse.ok || !completeData.ok) throw new Error(completeData.error || 'Could not finalize Database upload.');
            uploadId = '';
            if (statusEl) statusEl.textContent = `Uploaded ${completeData.filename || file.name}.`;
            window.location.reload();
        } catch (err) {
            if (uploadId) {
                try {
                    await fetch(`/db/upload/${encodeURIComponent(uploadId)}/abort`, {
                        method: 'POST',
                        credentials: 'same-origin',
                        cache: 'no-store',
                        headers: { 'X-CSRF-Token': csrf }
                    });
                } catch (_) {}
            }
            if (statusEl) statusEl.textContent = '';
            alert(err && err.message ? err.message : 'Database upload failed.');
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        const uploadTrigger = document.getElementById('db-upload-trigger');
        const uploadInput = document.getElementById('file-upload-input');
        if (uploadTrigger && uploadInput) uploadTrigger.addEventListener('click', () => uploadInput.click());
        if (uploadInput) uploadInput.addEventListener('change', () => {
            const file = uploadInput.files && uploadInput.files[0];
            uploadInput.value = '';
            if (file) uploadDatabaseFile(file);
        });

        document.querySelectorAll('.info-button').forEach(button => {
            button.addEventListener('click', event => toggleInfo(event, button.dataset.infoId || ''));
        });
        document.querySelectorAll('.info-popup').forEach(popup => {
            popup.addEventListener('click', event => event.stopPropagation());
        });
        document.querySelectorAll('.download-button').forEach(link => {
            link.addEventListener('click', event => {
                if (!confirm(`Download '${link.dataset.filename || 'file'}' now?`)) event.preventDefault();
            });
        });
        document.querySelectorAll('.delete-form').forEach(form => {
            form.addEventListener('submit', event => {
                if (!confirm(`Delete '${form.dataset.filename || 'file'}'? This cannot be undone.`)) event.preventDefault();
            });
        });
    });
    document.addEventListener('click', () => {
        document.querySelectorAll('.info-popup').forEach(p => p.style.display = 'none');
    });
</script>
</head>

<body>
<div class="topbar">
  <a class="back-btn" href="/">← Back to Connections</a>
</div>

<div class="container">
    <h1 style="margin-top:0;">DedSec's Database</h1>

    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="flash {{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <div class="manager-section">
        <button id="db-upload-trigger" class="icon-button">
            ⬆️ Upload File
        </button>
        <div style="margin-top:6px;font-size:.8em;color:var(--text-color-muted);">Up to 150 MB per file • streamed in protected 8 MiB chunks • 8 GiB total quota</div>
        <div id="db-upload-status" style="margin-top:6px;font-size:.8em;color:var(--text-color-muted);"></div>
        <input type="file" id="file-upload-input" style="display:none;" />
        <input type="hidden" id="db-csrf-token" value="{{ csrf_token }}" />
    </div>

    <form class="form-group" action="{{ url_for('database.index') }}" method="GET">
        <input type="search" name="query" list="fileSuggestions" placeholder="Search files in Database..." value="{{ request.args.get('query', '') }}" style="flex-grow:1;" />

        <datalist id="fileSuggestions">
            {% for filename in all_filenames %}
                <option value="{{ filename }}">
            {% endfor %}
        </datalist>

        <select name="sort">
            <option value="a-z" {% if sort=='a-z' %}selected{% endif %}>Sort A-Z</option>
            <option value="z-a" {% if sort=='z-a' %}selected{% endif %}>Sort Z-A</option>
            <option value="newest" {% if sort=='newest' %}selected{% endif %}>Newest First</option>
            <option value="oldest" {% if sort=='oldest' %}selected{% endif %}>Oldest First</option>
            <option value="biggest" {% if sort=='biggest' %}selected{% endif %}>Biggest First</option>
            <option value="smallest" {% if sort=='smallest' %}selected{% endif %}>Smallest First</option>
        </select>
        <input type="submit" value="Filter" />
    </form>

    {% set found_files = false %}
    {% for category, file_list in categorized_files.items() %}
        {% if file_list %}
            {% set found_files = true %}
            <h2>{{ category }}</h2>
            <div class="file-list">
            {% for f in file_list %}
            {% set info = files_info[f] %}
            <div class="file-item">
                <div class="filename">📄 {{ f }}</div>

                <div class="buttons">
                    <button class="button info-button" data-info-id="{{ loop.index0 ~ category }}">ℹ️ Info</button>
                    <div class="info-popup" id="info-{{ loop.index0 ~ category }}">
                        <b>Type:</b> {{ info['mimetype'] }}<br/>
                        <b>Size:</b> {{ info['size'] | filesizeformat }}<br/>
                        <b>Added:</b> {{ info['mtime_str'] }}
                    </div>

                    <a href="{{ url_for('database.download_file', filename=f) }}" class="button download-button" data-filename="{{ f }}" download>⬇️ Download</a>

                    <form action="{{ url_for('database.delete_path') }}" method="POST" class="delete-form" data-filename="{{ f }}" style="display:inline;">
                        <input type="hidden" name="filename" value="{{ f }}" />
                        <input type="hidden" name="sort" value="{{ sort }}" />
                        <input type="hidden" name="csrf_token" value="{{ csrf_token }}" />
                        <button type="submit" class="button delete-button">🗑️ Delete</button>
                    </form>
                </div>
            </div>
            {% endfor %}
            </div>
        {% endif %}
    {% endfor %}

    {% if not found_files %}
        <p style="text-align:center; margin-top:30px;">
        {% if request.args.get('query') %}
            No files match your search query in the Database.
        {% else %}
            The Database is empty. Use the ⬆️ Upload button to add files.
        {% endif %}
        </p>
    {% endif %}

    <div class="footer">Made by DedSec Project/dedsec1121fk!</div>
</div>
</body>
</html>
'''

# ==== FLASK ROUTING & AUTH (DB) ====

@db_blueprint.route("/", methods=["GET"])
@db_auth_required
def index():
    query = request.args.get("query", "").lower()
    sort = request.args.get("sort", "a-z")
    csrf_token = session.get('csrf_token') or secrets.token_urlsafe(32)
    session['csrf_token'] = csrf_token
    
    search_terms = query.split()

    try:
        full_contents = [p.name for p in BASE_DIR.iterdir()]
    except Exception:
        full_contents = []
    
    current_files = []
    files_info = {}
    all_filenames = []
    
    for item in full_contents:
        info = get_file_info(item)
        if info is not None: 
            all_filenames.append(item)
            item_lower = item.lower()
            
            if not search_terms or all(term in item_lower for term in search_terms):
                current_files.append(item)
                files_info[item] = info

    # Sorting logic
    reverse_map = {"z-a": True, "newest": True, "biggest": True}
    sort_key_map = {
        "a-z": lambda p: p.lower(), "z-a": lambda p: p.lower(),
        "oldest": lambda p: files_info[p]["mtime"], "newest": lambda p: files_info[p]["mtime"],
        "smallest": lambda p: files_info[p]["size"], "biggest": lambda p: files_info[p]["size"],
    }
    current_files.sort(key=sort_key_map.get(sort, lambda p: p.lower()), reverse=reverse_map.get(sort, False))

    # Categorization logic
    categorized_files = {cat: [] for cat in list(FILE_CATEGORIES.keys()) + ['Other']}
    for p in current_files:
        category = get_file_category(p)
        categorized_files[category].append(p)
        
    messages = get_flashed_messages(with_categories=True)

    return render_template_string(html_template_db, 
                                  categorized_files=categorized_files, 
                                  files_info=files_info, 
                                  request=request, 
                                  sort=sort,
                                  all_filenames=all_filenames,
                                  messages=messages,
                                  csrf_token=csrf_token)


def _db_upload_owner():
    if not session.get('db_logged_in'):
        return None
    owner_id = session.get('db_session_id')
    if not isinstance(owner_id, str) or not DB_UPLOAD_ID_RE.fullmatch(owner_id):
        return None
    return owner_id


@db_blueprint.route('/upload/init', methods=['POST'])
def db_upload_init():
    owner_id = _db_upload_owner()
    if not owner_id:
        return {'ok': False, 'error': 'Authentication required.'}, 401
    if not _valid_csrf():
        return {'ok': False, 'error': 'Invalid CSRF token.'}, 403
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return {'ok': False, 'error': 'Invalid upload metadata.'}, 400
    try:
        size = int(data.get('size', 0))
    except Exception:
        size = 0
    try:
        meta = _db_create_pending_upload(owner_id, data.get('filename', 'file'), size)
    except ValueError as exc:
        return {'ok': False, 'error': str(exc)}, 413
    except Exception:
        logging.exception('Database upload initialization failed')
        return {'ok': False, 'error': 'Could not initialize Database upload.'}, 500
    return {
        'ok': True,
        'upload_id': meta['upload_id'],
        'chunk_size': DB_CHUNK_BYTES,
        'expected_size': meta['expected_size'],
    }, 200


@db_blueprint.route('/upload/<upload_id>/chunk', methods=['POST'])
def db_upload_chunk(upload_id):
    owner_id = _db_upload_owner()
    if not owner_id:
        return {'ok': False, 'error': 'Authentication required.'}, 401
    if not _valid_csrf():
        return {'ok': False, 'error': 'Invalid CSRF token.'}, 403
    if not DB_UPLOAD_ID_RE.fullmatch(upload_id or ''):
        return {'ok': False, 'error': 'Upload not found.'}, 404
    try:
        chunk_index = int(request.headers.get('X-Chunk-Index', '-1'))
    except Exception:
        return {'ok': False, 'error': 'Invalid chunk index.'}, 400
    if chunk_index < 0 or chunk_index > 64:
        return {'ok': False, 'error': 'Invalid chunk index.'}, 400
    if request.content_length is not None and request.content_length > DB_CHUNK_BYTES:
        return {'ok': False, 'error': 'Upload chunk is too large.'}, 413
    try:
        received, expected = _db_append_upload_chunk(
            upload_id, owner_id, chunk_index, request.stream, request.content_length
        )
    except PermissionError:
        return {'ok': False, 'error': 'Upload not found.'}, 404
    except RuntimeError as exc:
        return {'ok': False, 'error': str(exc)}, 429
    except ValueError as exc:
        return {'ok': False, 'error': str(exc)}, 409
    except Exception:
        logging.exception('Database upload chunk failed')
        return {'ok': False, 'error': 'Database upload chunk failed.'}, 500
    return {'ok': True, 'received': received, 'expected_size': expected}, 200


@db_blueprint.route('/upload/<upload_id>/complete', methods=['POST'])
def db_upload_complete(upload_id):
    owner_id = _db_upload_owner()
    if not owner_id:
        return {'ok': False, 'error': 'Authentication required.'}, 401
    if not _valid_csrf():
        return {'ok': False, 'error': 'Invalid CSRF token.'}, 403
    if not DB_UPLOAD_ID_RE.fullmatch(upload_id or ''):
        return {'ok': False, 'error': 'Upload not found.'}, 404
    try:
        stored_name, stored_size = _db_complete_upload(upload_id, owner_id)
    except PermissionError:
        return {'ok': False, 'error': 'Upload not found.'}, 404
    except ValueError as exc:
        return {'ok': False, 'error': str(exc)}, 409
    except Exception:
        logging.exception('Database upload completion failed')
        return {'ok': False, 'error': 'Could not finalize Database upload.'}, 500
    return {'ok': True, 'filename': stored_name, 'size': stored_size}, 200


@db_blueprint.route('/upload/<upload_id>/abort', methods=['POST'])
def db_upload_abort(upload_id):
    owner_id = _db_upload_owner()
    if not owner_id:
        return {'ok': False}, 401
    if not _valid_csrf():
        return {'ok': False}, 403
    if not DB_UPLOAD_ID_RE.fullmatch(upload_id or ''):
        return {'ok': True}, 200
    with DB_UPLOAD_LOCK:
        meta = DB_PENDING_UPLOADS.get(upload_id)
        if meta and meta.get('owner_id') != owner_id:
            return {'ok': False}, 403
    _db_abort_pending_upload(upload_id)
    return {'ok': True}, 200


@db_blueprint.route("/download/<filename>", methods=["GET"])
@db_auth_required
def download_file(filename):
    basename = os.path.basename(filename)
    full_path = BASE_DIR / basename
    
    if full_path.exists() and full_path.is_file() and not full_path.is_symlink():
        return send_from_directory(BASE_DIR, basename, as_attachment=True)
    
    flash("Download path invalid or restricted.", 'error')
    return redirect(url_for('database.index', sort=request.args.get('sort', 'a-z')))

# --- FILE MANAGEMENT ROUTES ---

@db_blueprint.route("/delete_path", methods=["POST"])
@db_auth_required
def delete_path():
    if not _valid_csrf():
        return "Forbidden", 403
    filename_to_delete = request.form.get("filename") 
    sort = request.form.get("sort", "a-z")
    
    if filename_to_delete:
        item_name = os.path.basename(filename_to_delete)
        full_path = BASE_DIR / item_name
        
        if full_path.exists() and full_path.is_file() and not full_path.is_symlink() and not item_name.startswith('.upload-'):
            try:
                full_path.unlink()
                flash(f"File '{item_name}' successfully deleted.", 'success')
            except Exception as e:
                flash(f"Error deleting '{item_name}': {e}", 'error')
        else:
            flash(f"File '{item_name}' not found or is a folder.", 'error')
                
    return redirect(url_for('database.index', sort=sort))


# -------------------------------------------------------------------
#
# PART 2: FOX CHAT CODE (Main App)
#
# -------------------------------------------------------------------

app = Flask("chat")
# SECRET_KEY_SERVER will be set by server main
socketio = SocketIO(
    app,
    async_mode='threading',
    max_http_buffer_size=SOCKET_MAX_PACKET_BYTES,
    ping_interval=25,
    ping_timeout=20,
    logger=False,
    engineio_logger=False,
)  # Same-origin CORS protection is intentionally left at its secure default
connected_users = {}
VIDEO_ROOM = "global_video_room"

# Security/session state
FIRST_JOINED_CLIENT_ID = None
CLIENT_IDENTITIES = {}  # client_id -> private per-client secret for anti-spoofing
USER_STATE_LOCK = threading.Lock()
AUTH_FAILURES = {}
AUTH_LOCK = threading.Lock()
AUTH_WINDOW_SECONDS = 60
AUTH_MAX_FAILURES = 5
AUTH_BLOCK_SECONDS = 300
MESSAGE_RATE_WINDOW_SECONDS = 10
MESSAGE_RATE_MAX = 25
MAX_TEXT_MESSAGE_CHARS = 20000
MAX_USERNAME_CHARS = 48
MAX_CONNECTED_USERS = 100
MAX_CLIENT_IDENTITIES = 2048
MAX_SIGNAL_PAYLOAD_CHARS = 65536
CLIENT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{16,128}$")

# Ephemeral streamed chat-file storage. Files live only for the current server
# session and are removed on clean shutdown/startup. Random on-disk names prevent
# user-controlled paths from ever becoming filesystem paths.
CHAT_FILE_DIR = pathlib.Path.home() / ".connections_runtime" / "chat_files"
CHAT_FILES = {}  # file_id -> metadata
CHAT_PENDING_UPLOADS = {}  # upload_id -> in-progress chunked upload metadata
CHAT_FILES_LOCK = threading.RLock()
CHAT_UPLOAD_SLOTS = threading.BoundedSemaphore(6)
CHAT_UPLOAD_EVENTS = {}
CHAT_UPLOAD_WINDOW_SECONDS = 600
CHAT_UPLOAD_MAX_PER_WINDOW = 8
CHAT_FILE_ID_RE = re.compile(r'^[A-Za-z0-9_-]{20,80}$')
SAFE_INLINE_MEDIA_TYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'video/mp4', 'video/webm', 'video/ogg',
    'audio/mpeg', 'audio/mp4', 'audio/ogg', 'audio/wav', 'audio/webm',
}

def _prepare_chat_file_store():
    try:
        runtime_dir = CHAT_FILE_DIR.parent
        runtime_dir.mkdir(parents=True, exist_ok=True)
        CHAT_FILE_DIR.mkdir(parents=True, exist_ok=True)
        for directory in (runtime_dir, CHAT_FILE_DIR):
            try:
                os.chmod(directory, 0o700)
            except OSError:
                pass
        # Chat history is in-memory, so leftovers from a prior crashed run are
        # never valid. Delete only regular files/symlinks inside our private dir.
        for path in CHAT_FILE_DIR.iterdir():
            try:
                if path.is_file() or path.is_symlink():
                    path.unlink()
            except OSError:
                pass
    except Exception as exc:
        print(f"WARNING: could not prepare private chat-file storage: {exc}")

def _cleanup_chat_file_store():
    with CHAT_FILES_LOCK:
        CHAT_FILES.clear()
        CHAT_PENDING_UPLOADS.clear()
        CHAT_UPLOAD_EVENTS.clear()
    try:
        if CHAT_FILE_DIR.exists():
            for path in CHAT_FILE_DIR.iterdir():
                try:
                    if path.is_file() or path.is_symlink():
                        path.unlink()
                except OSError:
                    pass
    except OSError:
        pass

def _chat_storage_usage_locked():
    total = 0
    for meta in CHAT_FILES.values():
        try:
            total += int(meta.get('size', 0))
        except Exception:
            continue
    return total

def _delete_chat_file(file_id):
    if not isinstance(file_id, str):
        return
    with CHAT_FILES_LOCK:
        meta = CHAT_FILES.pop(file_id, None)
    if not meta:
        return
    try:
        path = CHAT_FILE_DIR / meta.get('stored_name', '')
        if path.parent == CHAT_FILE_DIR and (path.is_file() or path.is_symlink()):
            path.unlink(missing_ok=True)
    except Exception:
        pass

_prepare_chat_file_store()
atexit.register(_cleanup_chat_file_store)

# In-memory chat history for the current server session (not persisted)
CHAT_HISTORY = OrderedDict()
CHAT_HISTORY_MAX = 300  # number of messages to keep
CHAT_HISTORY_LOCK = threading.Lock()

# --- Register the Database Blueprint ---
app.register_blueprint(db_blueprint)

# Separate the Flask session-signing secret from the user-facing login key.
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SESSION_COOKIE_NAME'] = 'connections_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
# Secure cannot be forced globally because Tor onion services are intentionally
# accessed with http:// over Tor. Direct LAN HTTP is disabled by default instead.
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_REFRESH_EACH_REQUEST'] = False
app.config['MAX_CONTENT_LENGTH'] = max(DB_REQUEST_MAX_BYTES, CHAT_REQUEST_MAX_BYTES)
app.config['MAX_FORM_MEMORY_SIZE'] = 2 * 1024 * 1024
app.config['MAX_FORM_PARTS'] = 100

@app.before_request
def prepare_request_security_context():
    # Per-response nonce allows our inline application scripts without enabling
    # arbitrary inline JavaScript or HTML event-handler execution.
    g.csp_nonce = secrets.token_urlsafe(18)

@app.after_request
def add_security_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('X-Permitted-Cross-Domain-Policies', 'none')
    response.headers.setdefault('Referrer-Policy', 'no-referrer')
    response.headers.setdefault('Cross-Origin-Opener-Policy', 'same-origin')
    response.headers.setdefault('Permissions-Policy', 'camera=(self), microphone=(self), geolocation=(), payment=(), usb=()')
    nonce = getattr(g, 'csp_nonce', '')
    response.headers.setdefault(
        'Content-Security-Policy',
        f"default-src 'self'; script-src 'self' 'nonce-{nonce}' https://cdn.socket.io; script-src-attr 'none'; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' https://raw.githubusercontent.com; "
        "media-src 'self' blob:; connect-src 'self' ws: wss:; object-src 'none'; worker-src 'none'; "
        "base-uri 'none'; form-action 'self'; frame-ancestors 'self'; manifest-src 'none'"
    )
    response.headers.setdefault('Cross-Origin-Resource-Policy', 'same-origin')
    response.headers.setdefault('Origin-Agent-Cluster', '?1')
    response.headers.setdefault('Cache-Control', 'no-store, max-age=0')
    response.headers.setdefault('Pragma', 'no-cache')

    # Cloudflare Tunnel connects to this process over loopback HTTP. Only add
    # HSTS when the browser-facing request is known to be HTTPS.
    try:
        remote = ipaddress.ip_address(request.remote_addr or '127.0.0.1')
        forwarded_https = (
            remote.is_loopback and request.headers.get('CF-Ray') and
            request.headers.get('X-Forwarded-Proto', '').lower() == 'https'
        )
        if request.is_secure or forwarded_https:
            response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000')
    except ValueError:
        pass
    return response

# --- MODIFIED FOR VIBER UI + THEMES ---
HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes" />
<title>Connections</title>
<script src="https://cdn.socket.io/4.8.3/socket.io.min.js" integrity="sha384-kzavj5fiMwLKzzD1f8S7TeoVIEi7uKHvbTA3ueZkrzYq75pNQUiUi6Dy98Q3fxb0" crossorigin="anonymous"></script>
<style>
/* --- CSS Variables for Theming --- */
:root {
    --bg-color-main: #121212;
    --bg-color-header: #1e1e1e;
    --bg-color-input: #1e1e1e;
    --bg-color-input-field: #2c2c2c;
    --bg-color-bubble-self: #3737a1;
    --bg-color-bubble-other: #3a3a3a;
    --text-color-main: #e0e0e0;
    --text-color-header: #9c27b0;
    --text-color-light: #aaa;
    --text-color-self: #fff;
    --text-color-other: #e0e0e0;
    --text-color-btn: #fff;
    --border-color: #333;
    --shadow-color: rgba(0,0,0,0.5);
    --link-color: #90caf9;
    --accent-color-green: #4caf50;
    --accent-color-red: #f44336;
}
.light-theme {
    --bg-color-main: #ffffff;
    --bg-color-header: #ffffff;
    --bg-color-input: #ffffff;
    --bg-color-input-field: #f0f2f5;
    --bg-color-bubble-self: #0084ff;
    --bg-color-bubble-other: #e4e6eb;
    --text-color-main: #050505;
    --text-color-header: #800080; /* Kept purple */
    --text-color-light: #65676b;
    --text-color-self: #fff;
    --text-color-other: #050505;
    --text-color-btn: #050505;
    --border-color: #ced0d4;
    --shadow-color: rgba(0,0,0,0.1);
    --link-color: #0062cc;
    --accent-color-green: #28a745;
    --accent-color-red: #dc3545;
}

/* --- Global & Login --- */
body,html{height:100%;margin:0;padding:0;font-family:sans-serif;background:radial-gradient(1200px 800px at 10% 0%, rgba(156,39,176,0.18), transparent 60%), radial-gradient(1200px 800px at 90% 100%, rgba(128,0,128,0.14), transparent 55%), var(--bg-color-main);color:var(--text-color-main);overflow:hidden;}
#login-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);display:none;justify-content:center;align-items:center;z-index:1000}
#login-box{background:var(--bg-color-header);padding:25px;border-radius:8px;text-align:center;box-shadow:0 0 15px var(--shadow-color)}
#login-box h2{margin-top:0;color:var(--text-color-header)}
#login-box input{width:90%;padding:10px;margin:15px 0;background:var(--bg-color-input-field);border:1px solid var(--border-color);color:var(--text-color-main);border-radius:4px}
#login-box button{width:95%;padding:10px;background:var(--accent-color-green);border:none;color:#fff;border-radius:4px;cursor:pointer}
#login-error{color:var(--accent-color-red);margin-top:10px;height:1em}

/* --- Main Layout (Flex Column) --- */
#main-content{display:none; flex-direction: column; height: 100%;} 

/* --- Header (Instagram-ish) --- */
.header{
    display:flex;
    justify-content:space-between;
    align-items:center;
    background: linear-gradient(135deg, rgba(156,39,176,0.18), rgba(128,0,128,0.08));
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    padding: 10px 14px;
    border-bottom: 1px solid var(--border-color);
    flex-shrink: 0;
}
.header-left{display:flex;align-items:center;gap:12px;min-width:0;}
.avatar{
    width:36px;height:36px;border-radius:50%;
    display:flex;align-items:center;justify-content:center;
    background: linear-gradient(135deg, var(--accent-purple), #3a2a55);
    overflow:hidden;
    flex: 0 0 auto;
}
.avatar img{
    width:100%;
    height:100%;
    object-fit:cover;
    display:block;
}

.title-wrap{display:flex;flex-direction:column;min-width:0;}
.title{
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text-color-main);
    letter-spacing: .2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.subtitle{
    font-size: .78rem;
    color: var(--text-color-light);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.header-right{display:flex;align-items:center;gap:10px;}
#toggleCallUIBtn, #themeToggleBtn{
    width:36px;height:36px;border-radius:50%;
    background: var(--bg-color-input-field);
    border: 1px solid var(--border-color);
    color: var(--text-color-btn);
    font-size: 1.1rem;
    cursor: pointer;
    display:flex;align-items:center;justify-content:center;
    transition: transform .12s ease, background-color .12s ease;
}
#toggleCallUIBtn:active, #themeToggleBtn:active{transform: scale(.96);}


/* --- Call UI (Hidden by default) --- */
#call-ui-container { 
    display: none; 
    flex-shrink: 0;
    margin: 10px 0 12px;
    border: 1px solid var(--border-color);
    border-radius: 18px;
    overflow: hidden;
    background: rgba(255,255,255,0.03);
}
.light-theme #call-ui-container { background: rgba(0,0,0,0.03); }
#main-content.show-call #call-ui-container { display: block; }

/* --- Overlay Call Mode (shows video over chat) --- */
#main-content.call-overlay #call-ui-container{
    display:block;
    position: fixed;
    left: 12px;
    right: 12px;
    top: 70px;
    z-index: 5500;
    max-width: 980px;
    margin: 0 auto;
    box-shadow: 0 18px 50px rgba(0,0,0,0.45);
}
#main-content.call-overlay #call-ui-container{ backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); }

/* Video stage */
#videos{
    position: relative;
    width: 100%;
    height: min(46vh, 420px);
    background: rgba(0,0,0,0.35);
    border-bottom: 1px solid var(--border-color);
    overflow: hidden;
}
.light-theme #videos{ background: rgba(0,0,0,0.08); }

#videos video{
    width: 100%;
    height: 100%;
    object-fit: cover;
    background: #000;
}

/* Main remote stream takes the stage */
#videos .remote-main{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    border-radius: 0;
}

/* Additional remotes become thumbnails */
#videos .remote-thumb{
    position: absolute;
    right: 10px;
    top: 10px;
    width: 34%;
    max-width: 170px;
    height: 28%;
    max-height: 160px;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.18);
    box-shadow: 0 12px 30px rgba(0,0,0,0.30);
}

/* Local preview PIP */
#local{
    position: absolute;
    left: 10px;
    bottom: 10px;
    width: 32%;
    max-width: 170px;
    height: 30%;
    max-height: 170px;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.18);
    box-shadow: 0 12px 30px rgba(0,0,0,0.30);
    object-fit: cover;
}

/* --- Grid mode: show all cameras at once --- */
#videos.grid-mode{
    display:grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    grid-auto-rows: 1fr;
    gap: 8px;
    padding: 8px;
    height: min(58vh, 520px);
}
#videos.grid-mode video{
    position: relative !important;
    inset: auto !important;
    width: 100% !important;
    height: 100% !important;
    max-width: none !important;
    max-height: none !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255,255,255,0.18);
    box-shadow: 0 12px 30px rgba(0,0,0,0.30);
    object-fit: cover;
}
.light-theme #videos.grid-mode video{ border-color: rgba(0,0,0,0.18); }

/* --- Hide mode: keep audio, hide camera windows --- */
#videos.videos-hidden{
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
    border-bottom: 0 !important;
    overflow: hidden !important;
}
#videos.videos-hidden video{
    width: 1px !important;
    height: 1px !important;
    opacity: 0 !important;
    position: absolute !important;
    left: -9999px !important;
    top: -9999px !important;
}

/* Small-screen tweaks */
@media (max-width: 420px){
    #videos{ height: min(40vh, 360px); }
    #local{ width: 38%; height: 32%; }
    #videos .remote-thumb{ width: 38%; height: 26%; }
}

/* Controls bar (bottom) */
.ig-controls{
    display:flex;
    gap:10px;
    padding: 10px;
    justify-content: space-between;
    align-items: stretch;
    flex-wrap: wrap;
    background: rgba(0,0,0,0.10);
}
.light-theme .ig-controls{ background: rgba(0,0,0,0.04); }

.ig-btn{
    flex: 1 1 0;
    min-width: 64px;
    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;
    gap:4px;
    padding:10px 10px;
    border-radius:14px;
    border:1px solid var(--border-color);
    background:rgba(255,255,255,0.06);
    color:var(--text-color-btn);
    cursor:pointer;
    transition:transform .08s ease, background .15s ease, border-color .15s ease;
}
.light-theme .ig-btn{ background: rgba(0,0,0,0.04); }
.ig-btn:active{ transform: scale(.98); }
.ig-btn:hover{ background: rgba(255,255,255,0.10); border-color: rgba(128,0,128,0.9); }
.ig-btn:disabled{ opacity:.45; cursor:not-allowed; transform:none; }
.ig-btn .ig-ico{ font-size:18px; line-height:18px; }
.ig-btn .ig-lbl{ font-size:11px; letter-spacing:.2px; }
.ig-primary{ background: rgba(128,0,128,0.30); }
.ig-primary:hover{ background: rgba(128,0,128,0.38); }
.ig-danger{ background: rgba(139,0,0,0.35); border-color: rgba(139,0,0,0.55); }
.ig-danger:hover{ background: rgba(139,0,0,0.45); }

/* Remove the old collapse toggle line if present */
#video-controls-header{ display:none !important; }
#toggleVideosBtn{ display:none !important; }
#chat-container{
    padding: 12px 12px 18px;
    width:100%;
    position:relative; 
    flex-grow: 1; 
    overflow-y: auto;
    display: flex;
    flex-direction: column;
}
/* This is the inner container that holds messages */
#chat{
    width: 100%;
    display: flex;
    flex-direction: column;
    flex-grow: 1; /* Allows it to grow, but container scrolls */
}

/* --- Chat Bubbles (IG Style) --- */
.chat-message{
    display: flex;
    align-items: center;
    max-width: 75%;
    margin-bottom: 12px;
    gap: 8px;
    word-break: break-word;
}
.chat-message.self{
    align-self: flex-end;
    flex-direction: row-reverse; /* Bubble on right, actions on left */
}
.chat-message.other{
    align-self: flex-start;
}

.chat-message strong {
    display: none; /* Hide username by default */
}
.chat-message.other strong {
    /* Show username above bubble for 'other' */
    display: block;
    font-size: 0.8em;
    color: var(--text-color-light);
    margin-left: 15px;
    margin-bottom: 2px;
    /* We need to wrap strong and content in a div for this */
}

/* This wrapper will hold the username and bubble */
.message-bubble-wrapper {
    display: flex;
    flex-direction: column;
}

.message-content{
    padding: 10px 15px;
    border-radius: 20px;
    line-height: 1.4;
    box-shadow: 0 6px 18px rgba(0,0,0,0.18);
}
.chat-message.self .message-content{
    background: var(--bg-color-bubble-self);
    color: var(--text-color-self);
    border-bottom-right-radius: 5px;
}
.chat-message.other .message-content{
    background: var(--bg-color-bubble-other);
    color: var(--text-color-other);
    border-bottom-left-radius: 5px;
}

/* Specific styling for media in bubbles */
.message-content img, .message-content video, .message-content audio {
    max-width: 100%;
    border-radius: var(--radius);
    display: block;
}
.message-content audio {
    width: 100%;
}
.file-link{cursor:pointer;color:var(--link-color);text-decoration:underline; font-weight: bold;}


.message-actions{
    display: flex;
    gap: 5px;
}
.message-actions button{
    background:none;
    border:none;
    cursor:pointer;
    font-size:1.1em;
    padding: 2px 5px;
    color: var(--text-color-light);
}
.message-actions button:hover {
    color: var(--text-color-main);
}
.chat-message.other {
    /* Re-order for other: [bubble] [actions] */
    align-items: flex-end;
}
.chat-message.other .message-actions {
    order: 2;
}
.chat-message.other .message-bubble-wrapper {
    order: 1;
}
.chat-message.self {
     align-items: flex-end;
}
.chat-message.self .message-actions {
    order: 1;
}
.chat-message.self .message-bubble-wrapper {
    order: 2;
}

/* --- Input Bar (Viber Style) --- */
.controls{
    position:sticky;
    bottom:0;
    left:0;
    right:0;
    display:flex;
    flex-direction: column; /* CHANGED */
    gap: 8px;
    padding: 10px;
    background: linear-gradient(180deg, rgba(0,0,0,0), var(--bg-color-input) 25%);
    z-index: 10;
    /* align-items: center; <-- REMOVED */
    flex-shrink: 0;
    border-top: 1px solid var(--border-color);
}
#message {
    flex-grow: 1;
    background: var(--bg-color-input-field);
    border: 1px solid var(--border-color);
    color: var(--text-color-main);
    border-radius: 999px;
    padding: 10px 14px;
    font-size: 1em;
    line-height: 1.4;
    max-height: 100px; /* Allow resizing */
    resize: none;
}
.controls button {
    background: none;
    border: none;
    color: var(--text-color-btn);
    font-size: 1.5em;
    cursor: pointer;
    padding: 5px;
    flex-shrink: 0;
}
.controls button#sendBtn {
    font-size: 1.5em; /* Match other icons */
    color: var(--accent-color-green);
    padding: 5px 10px; /* Adjust padding */
}

/* --- NEW CSS for Input Layout --- */
.input-row {
    display: flex;
    align-items: flex-end; /* Align to bottom as textarea grows */
    gap: 8px;
    width: 100%;
}
.button-row {
    display: flex;
    justify-content: space-around;
    gap: 8px;
    width: 100%;
}
.button-row button {
    flex-grow: 1; /* Make buttons share space */
    padding: 8px; /* Give them a bit more padding */
}
/* --- END NEW CSS --- */


/* --- UI & FEATURE STYLES --- */
#media-preview-overlay, #camera-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);display:flex;flex-direction:column;justify-content:center;align-items:center;z-index:3000}
.light-theme #media-preview-overlay, .light-theme #camera-overlay { background: rgba(255,255,255,0.9); }

#media-preview-overlay img, #media-preview-overlay video, #media-preview-overlay audio{max-width:90vw;max-height:80vh;border:2px solid #fff}
.light-theme #media-preview-overlay img, .light-theme #media-preview-overlay video, .light-theme #media-preview-overlay audio { border-color: #000; }

#media-preview-overlay .file-placeholder{font-size:5em;color:#fff}
.light-theme #media-preview-overlay .file-placeholder { color: #000; }

#media-preview-controls, #camera-controls{display:flex;gap:15px;margin-top:15px;flex-wrap:wrap;justify-content:center}

/* Instagram-like camera overlay controls */
.ig-cam-controls{display:flex;gap:10px;margin-top:18px;flex-wrap:wrap;justify-content:center}
.ig-cam-btn{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;min-width:74px;padding:10px 12px;border-radius:16px;border:1px solid var(--border-color);background:rgba(255,255,255,0.06);color:var(--text-color-btn);cursor:pointer}
.light-theme .ig-cam-btn{background:rgba(0,0,0,0.04)}
.ig-cam-btn:active{transform:scale(0.98)}
.ig-cam-btn .ig-ico{font-size:18px;line-height:18px}
.ig-cam-btn .ig-lbl{font-size:11px}
.ig-cam-primary{background:rgba(128,0,128,0.28)}
.ig-cam-danger{background:rgba(139,0,0,0.35);border-color:rgba(139,0,0,0.55)}

#media-preview-controls button, #media-preview-controls a, #camera-controls button{background:var(--bg-color-input-field);color:var(--text-color-btn);border:1px solid var(--border-color);border-radius:4px;padding:10px 15px;cursor:pointer;text-decoration:none;font-size:1em}
#camera-preview{max-width:100%;max-height:80vh;border:2px solid var(--border-color);background:#000}
.edit-input{background:var(--bg-color-bubble-other);color:var(--text-color-other);border:1px solid var(--border-color);border-radius:4px;width:80%}
.fullscreen-video{position:fixed !important;top:0;left:0;width:100vw;height:100vh;max-width:none !important;max-height:none !important;margin:0;background-color:#000;object-fit:contain;z-index:2000;border-radius:0 !important;border:none !important}
.close-fullscreen-btn{position:fixed;top:15px;right:15px;z-index:2001;background:rgba(0,0,0,0.5);color:#fff;border:1px solid #fff;border-radius:50%;width:40px;height:40px;font-size:24px;line-height:40px;text-align:center;cursor:pointer}
.secure-watermark{position:absolute;top:0;left:0;width:100%;height:100%;overflow:hidden;pointer-events:none;z-index:100}
.secure-watermark::before{content:attr(data-watermark);position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-30deg);font-size:3em;color:rgba(255,255,255,0.08);white-space:nowrap}
.light-theme .secure-watermark::before { color: rgba(0,0,0,0.06); }

/* --- In-App Database Modal (IG-like) --- */
    position:fixed; inset:0;
    background: rgba(0,0,0,0.7);
    z-index: 6000;
    padding: 14px;
    box-sizing:border-box;
    display:flex;
    align-items:center;
    justify-content:center;
}
    width:100%;
    max-width: 900px;
    height: 90vh;
    background: var(--bg-color-header);
    border: 1px solid var(--border-color);
    border-radius: 18px;
    box-shadow: 0 22px 60px rgba(0,0,0,0.55);
    overflow:hidden;
    display:flex;
    flex-direction:column;
}
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding: 12px 14px;
    border-bottom: 1px solid var(--border-color);
    background: linear-gradient(180deg, rgba(156,39,176,0.14), rgba(0,0,0,0));
}
    font-weight: 700;
    letter-spacing: 0.2px;
    color: var(--text-color-header);
}
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-color-main);
    border-radius: 12px;
    padding: 6px 10px;
    cursor:pointer;
}
    flex:1;
    width:100%;
    border:0;
    background: var(--bg-color-main);
}

</style>
</head>
<body>
<div id="login-overlay"><div id="login-box"><h2>Enter One-Time Secret Key</h2><input type="password" id="key-input" maxlength="256" placeholder="Paste key here..." autocomplete="off" autocapitalize="none" spellcheck="false"><button id="connect-btn">Connect</button><p id="login-error"></p></div></div>

<div id="main-content">
    <div class="header">
        <div class="header-left">
            <div class="avatar" aria-label="Connections">
                <picture>
                    <source srcset="https://raw.githubusercontent.com/dedsec1121fk/dedsec1121fk.github.io/e0fab73c56ea9e68109f540f302b407ced1b14b3/Assets/Images/Logos/White%20Purple%20Butterfly%20Logo.jpeg" media="(prefers-color-scheme: light)">
                    <img id="chatLogo" src="https://raw.githubusercontent.com/dedsec1121fk/dedsec1121fk.github.io/e0fab73c56ea9e68109f540f302b407ced1b14b3/Assets/Images/Logos/Black%20Purple%20Butterfly%20Logo.jpeg" alt="Butterfly Logo">
                </picture>
            </div>
            <div class="title-wrap">
                <div class="title">Connections</div>
                <div class="subtitle" id="statusText">Secure • Ready</div>
            </div>
        </div>
        <div class="header-right">
            <button id="themeToggleBtn" title="Toggle Theme" aria-label="Toggle theme">☀️</button>
            <button id="toggleCallUIBtn" title="Toggle Call" aria-label="Toggle call UI">📞</button>
        </div>
    </div>
    
    <div id="call-ui-container">
        <div id="controls" class="ig-controls">
            <button id="joinBtn" class="ig-btn ig-primary" aria-label="Join Call" title="Join Call">
                <span class="ig-ico">📞</span><span class="ig-lbl">Join</span>
            </button>
            <button id="muteBtn" class="ig-btn" disabled aria-label="Mute" title="Mute / Unmute">
                <span class="ig-ico" id="muteIcon">🎤</span><span class="ig-lbl">Mute</span>
            </button>
            <button id="videoBtn" class="ig-btn" disabled aria-label="Camera" title="Camera On / Off">
                <span class="ig-ico" id="videoIcon">🎥</span><span class="ig-lbl">Cam</span>
            </button>
            <button id="switchCamBtn" class="ig-btn" disabled aria-label="Switch Camera" title="Switch Camera">
                <span class="ig-ico">🔄</span><span class="ig-lbl">Flip</span>
            </button>
            <button id="allCamsBtn" class="ig-btn" disabled aria-label="Show all cameras" title="Show all cameras (overlay chat)">
                <span class="ig-ico" id="allCamsIcon">🔳</span><span class="ig-lbl">All</span>
            </button>
            <button id="hideCamBtn" class="ig-btn" disabled aria-label="Hide cameras" title="Hide cameras (keep audio)">
                <span class="ig-ico" id="hideCamIcon">🙈</span><span class="ig-lbl">Hide</span>
            </button>
            <button id="leaveBtn" class="ig-btn ig-danger" disabled aria-label="Leave Call" title="Leave Call">
                <span class="ig-ico">📴</span><span class="ig-lbl">Leave</span>
            </button>
        </div>
        <div id="videos">
            <div class="secure-watermark"></div>
            <video id="local" autoplay muted playsinline></video>
        </div>
        <div id="video-controls-header">
            <button id="toggleVideosBtn">▲</button>
        </div>
    </div>
    
    <div id="chat-container">
        <div class="secure-watermark"></div>
        <div id="chat"></div>
    </div>
    
    <div class="controls">
        <div class="input-row">
            <textarea id="message" placeholder="Type a message..." rows="1"></textarea>
            <button id="recordButton" title="Voice Message">🎙️</button>
            <button id="sendBtn" title="Send" style="display:none;">&#10148;</button>
        </div>
        <div class="button-row">
            <button id="liveCameraBtn" title="Camera">📸</button>
            <button id="attachButton" title="Attach File">📄</button>
            <button id="dbButton" title="DedSec's Database">🛡️</button>
            <button id="infoButton" title="Information">ℹ️</button>
        </div>
        <input type="file" id="fileInput" style="display:none">
    </div>
</div>



<script nonce="{{ g.csp_nonce }}">
// --- Theme Toggle Logic ---
function applyTheme(theme) {
    const toggleBtn = document.getElementById('themeToggleBtn');
    if (theme === 'light') {
        document.body.classList.add('light-theme');
        if (toggleBtn) toggleBtn.textContent = '🌙';
    } else {
        document.body.classList.remove('light-theme');
        if (toggleBtn) toggleBtn.textContent = '☀️';
    }
    const logo = document.getElementById('chatLogo');
    if (logo) {
        logo.src = theme === 'light' ? 'https://raw.githubusercontent.com/dedsec1121fk/dedsec1121fk.github.io/e0fab73c56ea9e68109f540f302b407ced1b14b3/Assets/Images/Logos/White%20Purple%20Butterfly%20Logo.jpeg' : 'https://raw.githubusercontent.com/dedsec1121fk/dedsec1121fk.github.io/e0fab73c56ea9e68109f540f302b407ced1b14b3/Assets/Images/Logos/Black%20Purple%20Butterfly%20Logo.jpeg';
    }

}

function toggleTheme() {
    const currentTheme = localStorage.getItem('theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', newTheme);
    applyTheme(newTheme);
}
// --- End Theme Logic ---


document.addEventListener('DOMContentLoaded', () => {
    // Apply saved theme on load
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);
    document.getElementById('themeToggleBtn').onclick = toggleTheme;

    const keyInput = document.getElementById('key-input');
    const connectBtn = document.getElementById('connect-btn');
    const loginError = document.getElementById('login-error');
    // Never persist the login key across browser restarts. Remove legacy copies.
    try { localStorage.removeItem("secretKey"); } catch(e) {}
    const savedKey = sessionStorage.getItem("secretKey");

    // If this tab already authenticated during the current browser session, reconnect.
    if (savedKey) {
        keyInput.value = savedKey;
        document.getElementById('login-overlay').style.display = 'none';
        document.getElementById('main-content').style.display = 'none';
        loginError.textContent = 'Connecting...';
        initializeChat(savedKey);
    } else {
        document.getElementById('main-content').style.display = 'none';
        document.getElementById('login-overlay').style.display = 'flex';
    }

    connectBtn.onclick = () => {
        const secretKey = keyInput.value.trim();
        if (secretKey.length >= 32 && secretKey.length <= 256) {
            loginError.textContent = 'Connecting...';
            sessionStorage.setItem("secretKey", secretKey);
            initializeChat(secretKey);
        } else {
            loginError.textContent = 'Invalid key format.';
        }
    };
    
    // Auto-resize textarea and toggle Send/Mic buttons
    const messageInput = document.getElementById('message');
    const sendBtn = document.getElementById('sendBtn');
    const recordBtn = document.getElementById('recordButton');
    
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        
        // Viber-like button toggle
        if (this.value.trim().length > 0) {
            sendBtn.style.display = 'block';
            recordBtn.style.display = 'none';
        } else {
            sendBtn.style.display = 'none';
            recordBtn.style.display = 'block';
        }
    });

    recordBtn.addEventListener('click', () => { if (window.toggleRecording) window.toggleRecording(); });
    sendBtn.addEventListener('click', () => { if (window.sendMessage) window.sendMessage(); });
    const liveCameraBtn = document.getElementById('liveCameraBtn');
    const attachBtn = document.getElementById('attachButton');
    const dbBtn = document.getElementById('dbButton');
    const infoBtn = document.getElementById('infoButton');
    if (liveCameraBtn) liveCameraBtn.addEventListener('click', () => { if (window.openLiveCamera) window.openLiveCamera(); });
    if (attachBtn) attachBtn.addEventListener('click', () => { if (window.sendFile) window.sendFile(); });
    if (dbBtn) dbBtn.addEventListener('click', openDatabase);
    if (infoBtn) infoBtn.addEventListener('click', showInfo);
});


async function openDatabase() {
    const key = sessionStorage.getItem('secretKey') || '';
    if (!key) return;

    // Open immediately so mobile popup blockers still treat this as a user action.
    const dbWindow = window.open('about:blank', '_blank');
    try {
        const response = await fetch('/db/auth', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'X-Connections-Key': key }
        });
        if (!response.ok) throw new Error('Database authentication failed');
        if (dbWindow) dbWindow.location = '/db/';
        else window.location.href = '/db/';
    } catch (e) {
        if (dbWindow) dbWindow.close();
        alert('Could not authenticate to the Database.');
    }
}
function showInfo() {
    const infoText = `Connections — Help & Info

Links you see in the launcher:
• Cloudflared link (https://*.trycloudflare.com) — Works in ANY iOS browser (Safari/Chrome/etc.) ✅
• Local LAN link — Disabled by default. Start with --allow-lan only on a trusted Wi‑Fi / hotspot.
• Tor .onion link — Requires a Tor-capable browser/app ❗️
  iOS Safari/Chrome cannot open .onion domains. Use an iOS Tor browser (e.g. Onion Browser) to open it.

Chat basics:
• Type a message and press Send or Enter.
• 🎙️ Hold/press to record a voice message. Tap again to stop & send.
• 📷 Camera: take a photo and send it.
• 📎 Attach: send a chat file (up to 150 MiB). Files are streamed instead of base64-embedded.
• 🛡️ Database: opens DedSec's Database (your shared files).

Call controls (Instagram‑style):
• 🎤 Mute / Unmute microphone
• 🎥 Camera On / Off
• 📴 Leave call
• 🔄 Switch camera (front/back)

Security notes:
• Cloudflared uses HTTPS from the browser to Cloudflare and a tunnel from Cloudflare to this device; Cloudflare remains part of the trust path.
• Direct LAN access is disabled by default. Use --allow-lan only on a trusted Wi‑Fi/hotspot; that route is plain HTTP.
• Tor hides your device location/IP, but you must open the .onion link with a Tor-capable browser.

Tip:
Your key is stored only for this session (sessionStorage). If you restart the page/server, you’ll enter the new key again.`;
    
    // Use a custom modal instead of alert()
    const infoModal = document.createElement('div');
    infoModal.id = 'info-modal-overlay';
    infoModal.style = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);display:flex;justify-content:center;align-items:center;z-index:5000;padding:15px;box-sizing:border-box;';
    infoModal.onclick = () => infoModal.remove();
    
    const infoBox = document.createElement('div');
    infoBox.id = 'info-modal-box';
    infoBox.style = 'background:var(--bg-color-header);color:var(--text-color-main);padding:20px;border-radius:8px;max-width:500px;width:100%;max-height:80vh;overflow-y:auto;border:1px solid var(--border-color);';
    infoBox.onclick = (e) => e.stopPropagation(); // Prevent modal from closing when clicking box
    
    const infoPre = document.createElement('pre');
    infoPre.style = 'white-space:pre-wrap;font-family:inherit;font-size:1em;';
    infoPre.textContent = infoText.trim();
    
    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'Close';
    closeBtn.style = 'width:100%;padding:10px;margin-top:15px;background:var(--accent-color-green);border:none;color:#fff;border-radius:4px;cursor:pointer;';
    closeBtn.onclick = () => infoModal.remove();
    
    infoBox.appendChild(infoPre);
    infoBox.appendChild(closeBtn);
    infoModal.appendChild(infoBox);
    document.body.appendChild(infoModal);
}

function initializeChat(secretKey) {
    function randomHex(bytesLength) {
        const bytes = new Uint8Array(bytesLength);
        crypto.getRandomValues(bytes);
        return Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
    }

    function getOrCreateClientIdentity() {
        let id = sessionStorage.getItem('connectionsClientId');
        let privateSecret = sessionStorage.getItem('connectionsClientSecret');
        if (!id || !/^[A-Za-z0-9_-]{16,128}$/.test(id)) {
            id = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : randomHex(24);
            sessionStorage.setItem('connectionsClientId', id);
        }
        if (!privateSecret || !/^[A-Fa-f0-9]{64,128}$/.test(privateSecret)) {
            privateSecret = randomHex(32);
            sessionStorage.setItem('connectionsClientSecret', privateSecret);
        }
        return { id, privateSecret };
    }

    const clientIdentity = getOrCreateClientIdentity();
    const clientId = clientIdentity.id;
    let currentIsModerator = false;
    let httpCsrfToken = '';
    let httpAuthPromise = null;

    async function authenticateHttpSession() {
        const response = await fetch('/chat/auth', {
            method: 'POST',
            credentials: 'same-origin',
            cache: 'no-store',
            headers: {
                'X-Connections-Key': secretKey,
                'X-Client-ID': clientIdentity.id,
                'X-Client-Secret': clientIdentity.privateSecret
            }
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || !data.ok || !data.csrf_token) {
            throw new Error('Could not establish the protected file-transfer session.');
        }
        httpCsrfToken = data.csrf_token;
        return true;
    }

    const socket = io({ auth: {
        token: secretKey,
        client_id: clientIdentity.id,
        client_secret: clientIdentity.privateSecret
    } });
    socket.on('connect_error', () => {
        document.getElementById('login-error').textContent = 'Invalid Key or too many attempts. Please try again.';
        try { sessionStorage.removeItem("secretKey"); } catch(e) {}
        document.getElementById('main-content').style.display = 'none';
        document.getElementById('login-overlay').style.display = 'flex';
    });
    socket.on('connect', () => {
        document.getElementById('login-overlay').style.display = 'none';
        document.getElementById('main-content').style.display = 'flex';
        try { document.getElementById('key-input').value = ''; } catch(e) {}
        const st = document.getElementById('statusText'); if (st) st.textContent = 'Authenticated • Connected'; 
        let username = localStorage.getItem("username");
        if (!username) {
            let promptedName = prompt("Enter your username:");
            username = promptedName ? promptedName.trim() : "User" + Math.floor(Math.random() * 1000);
            localStorage.setItem("username", username);
        }
        document.querySelectorAll('.secure-watermark').forEach(el => el.setAttribute('data-watermark', username));
        socket.emit("join", username);
    });

    socket.on('session_info', data => {
        currentIsModerator = !!(data && data.is_moderator);
        const st = document.getElementById('statusText');
        if (st) st.textContent = currentIsModerator ? 'Authenticated • Connected • Moderator' : 'Authenticated • Connected';
        httpAuthPromise = authenticateHttpSession().catch(err => {
            httpCsrfToken = '';
            console.error('Protected file-transfer authentication failed:', err);
            throw err;
        });
    });

    socket.on('action_error', data => {
        showCustomAlert((data && data.message) ? data.message : 'That action is not allowed.');
    });
    
    // --- NEW: Toggle Call UI ---
    document.getElementById('toggleCallUIBtn').onclick = () => {
        const main = document.getElementById('main-content');
        main.classList.toggle('show-call');
        // If user hides the call UI, also exit overlay/hide modes safely
        if (!main.classList.contains('show-call')) {
            if (window._resetCallViewModes) window._resetCallViewModes();
        }
    };

    const MAX_FILE_SIZE = 150 * 1024 * 1024; // 150 MB; server enforces the same limit
    const SAFE_IMAGE_TYPES = new Set(['image/jpeg', 'image/png', 'image/gif', 'image/webp']);
    const SAFE_VIDEO_TYPES = new Set(['video/mp4', 'video/webm', 'video/ogg']);
    const SAFE_AUDIO_TYPES = new Set(['audio/mpeg', 'audio/mp4', 'audio/ogg', 'audio/wav', 'audio/webm']);
    const fileInput = document.getElementById('fileInput');
    const chat = document.getElementById('chat');
    const chatContainer = document.getElementById('chat-container');
    const messageInput = document.getElementById('message');

    async function uploadChatFile(fileOrBlob, filename) {
        if (!fileOrBlob) return;
        const size = Number(fileOrBlob.size || 0);
        if (size <= 0) {
            showCustomAlert('Empty files cannot be sent.');
            return;
        }
        if (size > MAX_FILE_SIZE) {
            showCustomAlert('File is too large. Maximum file size is 150 MB.');
            return;
        }
        if (!httpAuthPromise) {
            showCustomAlert('The secure file-transfer session is still starting. Try again in a moment.');
            return;
        }

        let uploadId = '';
        const st = document.getElementById('statusText');
        const previousStatus = st ? st.textContent : '';
        try {
            await httpAuthPromise;
            if (!httpCsrfToken) throw new Error('Missing protected upload token.');

            const safeName = (filename || fileOrBlob.name || 'file').toString().slice(0, 220);
            const fileType = (fileOrBlob.type || 'application/octet-stream').toString().slice(0, 120);
            if (st) st.textContent = `Preparing ${safeName}...`;

            const initResponse = await fetch('/chat/upload/init', {
                method: 'POST',
                credentials: 'same-origin',
                cache: 'no-store',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': httpCsrfToken
                },
                body: JSON.stringify({ filename: safeName, file_type: fileType, size })
            });
            const initData = await initResponse.json().catch(() => ({}));
            if (!initResponse.ok || !initData.ok || !initData.upload_id) {
                throw new Error(initData.error || 'Could not initialize upload.');
            }

            uploadId = initData.upload_id;
            const chunkSize = Math.max(256 * 1024, Math.min(Number(initData.chunk_size) || (8 * 1024 * 1024), 8 * 1024 * 1024));
            let chunkIndex = 0;
            let offset = 0;

            while (offset < size) {
                const end = Math.min(offset + chunkSize, size);
                const chunk = fileOrBlob.slice(offset, end);
                const progressBefore = Math.floor((offset / size) * 100);
                if (st) st.textContent = `Uploading ${safeName}... ${progressBefore}%`;

                const chunkResponse = await fetch(`/chat/upload/${encodeURIComponent(uploadId)}/chunk`, {
                    method: 'POST',
                    credentials: 'same-origin',
                    cache: 'no-store',
                    headers: {
                        'Content-Type': 'application/octet-stream',
                        'X-CSRF-Token': httpCsrfToken,
                        'X-Chunk-Index': String(chunkIndex)
                    },
                    body: chunk
                });
                const chunkData = await chunkResponse.json().catch(() => ({}));
                if (!chunkResponse.ok || !chunkData.ok) {
                    throw new Error(chunkData.error || `Upload failed at chunk ${chunkIndex + 1}.`);
                }

                offset = end;
                chunkIndex += 1;
            }

            if (st) st.textContent = `Finalizing ${safeName}...`;
            const completeResponse = await fetch(`/chat/upload/${encodeURIComponent(uploadId)}/complete`, {
                method: 'POST',
                credentials: 'same-origin',
                cache: 'no-store',
                headers: { 'X-CSRF-Token': httpCsrfToken }
            });
            const completeData = await completeResponse.json().catch(() => ({}));
            if (!completeResponse.ok || !completeData.ok || !completeData.file_id) {
                throw new Error(completeData.error || 'Could not finalize upload.');
            }

            uploadId = '';
            socket.emit('file_message', { file_id: completeData.file_id });
        } catch (err) {
            if (uploadId) {
                try {
                    await fetch(`/chat/upload/${encodeURIComponent(uploadId)}/abort`, {
                        method: 'POST',
                        credentials: 'same-origin',
                        cache: 'no-store',
                        headers: { 'X-CSRF-Token': httpCsrfToken }
                    });
                } catch (_) {}
            }
            showCustomAlert(err && err.message ? err.message : 'File upload failed.');
        } finally {
            if (st) st.textContent = previousStatus || (currentIsModerator ? 'Authenticated • Connected • Moderator' : 'Authenticated • Connected');
        }
    }

    function handleFileSelection(file) {
        if (!file) return;
        uploadChatFile(file, file.name);
    }
    fileInput.addEventListener('change', e => { handleFileSelection(e.target.files[0]); e.target.value = ''; });

    window.sendMessage = () => {
        const text = messageInput.value.trim();
        if (!text) return;
        // Send raw text; it is rendered with textContent, never innerHTML.
        socket.emit("message", { message: text });
        messageInput.value = '';
        messageInput.style.height = 'auto'; // Reset height
        messageInput.style.height = (messageInput.scrollHeight) + 'px'; // Recalculate for 1 line
        
        // Toggle buttons back
        document.getElementById('sendBtn').style.display = 'none';
        document.getElementById('recordButton').style.display = 'block';
    };
    
    // --- KEYDOWN LISTENER REMOVED ---
    
    let mediaRecorder, recordedChunks = [], isRecording = false;
    window.toggleRecording = () => {
        let recordButton = document.getElementById("recordButton");
        if (isRecording) {
            mediaRecorder.stop();
        } else {
            navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
                isRecording = true;
                recordButton.textContent = '🔴';
                recordButton.style.color = 'red';
                recordedChunks = [];
                mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
                mediaRecorder.ondataavailable = e => { if (e.data.size > 0) recordedChunks.push(e.data); };
                mediaRecorder.onstop = () => {
                    isRecording = false;
                    recordButton.textContent = '🎙️';
                    recordButton.style.color = 'var(--text-color-btn)';
                    stream.getTracks().forEach(track => track.stop());
                    const blob = new Blob(recordedChunks, { type: 'audio/webm' });
                    uploadChatFile(blob, 'voice-message.webm');
                };
                mediaRecorder.start();
            }).catch(err => showCustomAlert("Microphone access was denied."));
        }
    };
    
    window.sendFile = () => fileInput.click();
    
    function emitFile(blobOrFile, type, name) {
        if (!(blobOrFile instanceof Blob)) {
            showCustomAlert('Unsupported file source.');
            return;
        }
        uploadChatFile(blobOrFile, name || 'file');
    }

    function showCustomAlert(message) {
        // Re-using the info modal structure for alerts
        const alertModal = document.createElement('div');
        alertModal.id = 'alert-modal-overlay';
        alertModal.style = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);display:flex;justify-content:center;align-items:center;z-index:5001;padding:15px;box-sizing:border-box;';
        alertModal.onclick = () => alertModal.remove();
        
        const alertBox = document.createElement('div');
        alertBox.id = 'alert-modal-box';
        alertBox.style = 'background:var(--bg-color-header);color:var(--text-color-main);padding:20px;border-radius:8px;max-width:500px;width:100%;text-align:center;border:1px solid var(--border-color);';
        alertBox.onclick = (e) => e.stopPropagation();
        
        const alertText = document.createElement('p');
        alertText.textContent = message;
        alertText.style = 'margin:0;font-size:1.1em;';
        
        const closeBtn = document.createElement('button');
        closeBtn.textContent = 'OK';
        closeBtn.style = 'width:100%;padding:10px;margin-top:20px;background:var(--accent-color-green);border:none;color:#fff;border-radius:4px;cursor:pointer;';
        closeBtn.onclick = () => alertModal.remove();
        
        alertBox.appendChild(alertText);
        alertBox.appendChild(closeBtn);
        alertModal.appendChild(alertBox);
        document.body.appendChild(alertModal);
    }

    function showMediaPreview(data) {
        if (!data || !data.fileId) {
            showCustomAlert('This file is no longer available.');
            return;
        }
        let existingPreview = document.getElementById('media-preview-overlay');
        if (existingPreview) existingPreview.remove();
        const overlay = document.createElement('div');
        overlay.id = 'media-preview-overlay';
        let previewContent;
        const fileUrl = `/chat/file/${encodeURIComponent(data.fileId)}`;

        if (SAFE_IMAGE_TYPES.has(data.fileType)) {
            previewContent = document.createElement('img');
        } else if (SAFE_VIDEO_TYPES.has(data.fileType)) {
            previewContent = document.createElement('video');
            previewContent.controls = true;
            previewContent.autoplay = true;
            previewContent.playsInline = true;
        } else if (SAFE_AUDIO_TYPES.has(data.fileType)) {
            previewContent = document.createElement('audio');
            previewContent.controls = true;
            previewContent.autoplay = true;
        } else {
            previewContent = document.createElement('div');
            previewContent.className = 'file-placeholder';
            previewContent.textContent = '📄';
        }

        if (previewContent.src !== undefined) previewContent.src = fileUrl;

        const controls = document.createElement('div');
        controls.id = 'media-preview-controls';

        const closeBtn = document.createElement('button');
        closeBtn.textContent = 'Close (X)';
        closeBtn.onclick = () => overlay.remove();

        const downloadLink = document.createElement('a');
        downloadLink.textContent = 'Download';
        downloadLink.href = `${fileUrl}?download=1`;
        downloadLink.download = data.filename || 'file';
        controls.appendChild(downloadLink);

        const canDeleteMedia = !!data.owner_id && (data.owner_id === clientId || currentIsModerator);
        if (canDeleteMedia) {
            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = 'Delete';
            deleteBtn.onclick = () => { socket.emit('delete_message', { id: data.id }); overlay.remove(); };
            controls.appendChild(deleteBtn);
        }
        controls.appendChild(closeBtn);

        overlay.appendChild(previewContent);
        overlay.appendChild(controls);
        document.body.appendChild(overlay);
    }
    
    let liveCameraStream;
    let liveCameraFacingMode = 'user';
    window.openLiveCamera = () => {
        const overlay = document.createElement('div');
        overlay.id = 'camera-overlay';
        const video = document.createElement('video');
        video.id = 'camera-preview';
        video.autoplay = true;
        video.playsInline = true; // Added for iOS compatibility
        const controls = document.createElement('div');
        controls.id = 'camera-controls';
        controls.className = 'ig-cam-controls';
        const captureBtn = document.createElement('button');
        captureBtn.className = 'ig-cam-btn ig-cam-primary';
        captureBtn.textContent = '⚪ Capture';
        const switchBtn = document.createElement('button');
        switchBtn.className = 'ig-cam-btn';
        switchBtn.textContent = '🔄 Flip';
        const closeBtn = document.createElement('button');
        closeBtn.className = 'ig-cam-btn ig-cam-danger';
        closeBtn.textContent = '✕ Close';
        
        const startStream = (facingMode) => {
            if (liveCameraStream) {
                liveCameraStream.getTracks().forEach(track => track.stop());
            }
            navigator.mediaDevices.getUserMedia({ video: { facingMode: facingMode } })
                .then(stream => {
                    liveCameraStream = stream;
                    video.srcObject = stream;
                })
                .catch(err => {
                    showCustomAlert('Could not access camera. Please check permissions.');
                    overlay.remove();
                });
        };
        
        closeBtn.onclick = () => {
            if (liveCameraStream) liveCameraStream.getTracks().forEach(track => track.stop());
            overlay.remove();
        };
        switchBtn.onclick = () => {
            liveCameraFacingMode = liveCameraFacingMode === 'user' ? 'environment' : 'user';
            startStream(liveCameraFacingMode);
        };
        captureBtn.onclick = () => {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            const filename = `capture-${Date.now()}.jpg`;
            canvas.toBlob(blob => {
                if (blob) emitFile(blob, 'image/jpeg', filename);
                else showCustomAlert('Could not encode the captured image.');
            }, 'image/jpeg', 0.8);
            closeBtn.onclick();
        };
        
        controls.appendChild(captureBtn);
        controls.appendChild(switchBtn);
        controls.appendChild(closeBtn);
        overlay.appendChild(video);
        overlay.appendChild(controls);
        document.body.appendChild(overlay);
        startStream(liveCameraFacingMode);
    };

    function renderChatMessage(data) {
        if (!data || !data.id) return;
        if (document.getElementById(data.id)) return;
        const div = document.createElement('div');
        div.className = 'chat-message';
        div.id = data.id;
        
        const isSelf = !!data.owner_id && data.owner_id === clientId;
        if (isSelf) {
            div.classList.add('self');
        } else {
            div.classList.add('other');
        }

        // Wrapper for bubble
        const bubbleWrapper = document.createElement('div');
        bubbleWrapper.className = 'message-bubble-wrapper';
        const content = document.createElement('div');
        content.className = 'message-content';
        content.id = `content-${data.id}`;
        
        let messageText = data.message || '';
        if (data.fileType && data.fileId) {
            const fileUrl = `/chat/file/${encodeURIComponent(data.fileId)}`;
            const fileLink = document.createElement('span');
            fileLink.className = 'file-link';
            fileLink.textContent = data.filename || 'file';

            // Always show who sent the file
            const fileLabel = document.createElement('div');
            fileLabel.className = 'file-label';
            const sizeText = Number.isFinite(Number(data.fileSize)) ? ` (${(Number(data.fileSize) / (1024 * 1024)).toFixed(1)} MB)` : '';
            fileLabel.textContent = `${data.username}: ${data.filename || 'file'}${sizeText}`;
            content.appendChild(fileLabel);

            if ((data.filename || '').includes('voice-message.webm') || SAFE_AUDIO_TYPES.has(data.fileType)) {
                const audio = document.createElement('audio');
                audio.src = fileUrl;
                audio.controls = true;
                audio.setAttribute('controlsList', 'nodownload');
                content.appendChild(audio);
            } else if (SAFE_IMAGE_TYPES.has(data.fileType)) {
                const img = document.createElement('img');
                img.src = fileUrl;
                img.alt = data.filename || 'image';
                img.style.cursor = 'zoom-in';
                img.onclick = () => showMediaPreview(data);
                content.appendChild(img);
            } else if (SAFE_VIDEO_TYPES.has(data.fileType)) {
                const video = document.createElement('video');
                video.src = fileUrl;
                video.controls = true;
                video.playsInline = true;
                video.onclick = () => showMediaPreview(data);
                content.appendChild(video);
            } else {
                fileLink.onclick = () => showMediaPreview(data);
                content.appendChild(fileLink);
            }
        } else {
            // It's a text message
            content.textContent = `${data.username}: ${messageText}`;
            if (data.username === 'System') {
                content.style.background = 'none';
                content.style.color = 'var(--text-color-light)';
                content.style.textAlign = 'center';
                div.style.maxWidth = '100%';
                div.style.justifyContent = 'center';
            }
        }

        bubbleWrapper.appendChild(content);
        div.appendChild(bubbleWrapper);

        const canDelete = !!data.owner_id && (isSelf || currentIsModerator);
        if ((isSelf || canDelete) && data.username !== 'System') {
            const actions = document.createElement('div');
            actions.className = 'message-actions';
            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = '❌';
            deleteBtn.title = 'Delete';
            deleteBtn.onclick = () => socket.emit('delete_message', { id: data.id });
            
            if (isSelf && !data.fileType) {
                const editBtn = document.createElement('button');
                editBtn.textContent = '📝';
                editBtn.title = 'Edit';
                editBtn.onclick = () => toggleEdit(data.id, data.username, data.message);
                actions.appendChild(editBtn);
            }
            if (canDelete) actions.appendChild(deleteBtn);
            div.appendChild(actions);
        }
        
        const wasAtBottom = chatContainer.scrollHeight - chatContainer.scrollTop - chatContainer.clientHeight < 100;
        
        chat.appendChild(div);
        
        if (wasAtBottom) {
             requestAnimationFrame(() => chatContainer.scrollTop = chatContainer.scrollHeight);
        }
    }

    socket.on("chat_history", history => {
        if (!Array.isArray(history)) return;
        history.forEach(m => renderChatMessage(m));
    });

    socket.on("message", data => {
        renderChatMessage(data);
    });
    socket.on('delete_message', data => {
        const element = document.getElementById(data.id);
        if (element) element.remove();
    });

    function toggleEdit(id, username, currentText) {
        const contentDiv = document.getElementById(`content-${id}`);
        if (contentDiv.querySelector('input')) return; 

        contentDiv.replaceChildren();
        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentText;
        input.className = 'edit-input';
        
        const saveBtn = document.createElement('button');
        saveBtn.textContent = 'Save';
        saveBtn.onclick = () => {
            const newText = input.value.trim();
            if (newText && newText !== currentText) {
                socket.emit('edit_message', { id: id, new_message: newText });
            } else {
                contentDiv.textContent = `${username}: ${currentText}`;
            }
        };
        
        const cancelBtn = document.createElement('button');
        cancelBtn.textContent = 'Cancel';
        cancelBtn.onclick = () => contentDiv.textContent = `${username}: ${currentText}`;

        input.onkeydown = (e) => { 
            if(e.key === 'Enter') saveBtn.click(); 
            if(e.key === 'Escape') cancelBtn.click();
        };
        
        contentDiv.appendChild(input);
        contentDiv.appendChild(saveBtn);
        contentDiv.appendChild(cancelBtn);
        input.focus();
    }

    socket.on('message_edited', data => {
        const contentDiv = document.getElementById(`content-${data.id}`);
        if(contentDiv) {
            let prefix = '';
            if (data.username) {
                prefix = `${data.username}: `;
            } else {
                // Best-effort: preserve existing "username: " prefix if present
                const existing = (contentDiv.textContent || '');
                const idx = existing.indexOf(': ');
                if (idx > -1) prefix = existing.slice(0, idx + 2);
            }
            contentDiv.textContent = prefix + data.new_message + ' (edited)';
        }
    });
    
    // ----------------------------------------------------------------------------------
    // FULL WEBRTC LOGIC RESTORED & FIXED
    // ----------------------------------------------------------------------------------

    const videos = document.getElementById('videos'), localVideo = document.getElementById('local');
    const joinBtn = document.getElementById('joinBtn'), muteBtn = document.getElementById('muteBtn');
    const videoBtn = document.getElementById('videoBtn'), leaveBtn = document.getElementById('leaveBtn');
    const switchCamBtn = document.getElementById('switchCamBtn');
    const toggleVideosBtn = document.getElementById('toggleVideosBtn');
    const allCamsBtn = document.getElementById('allCamsBtn');
    const hideCamBtn = document.getElementById('hideCamBtn');

    let localStream, peerConnections = {}, isMuted = false, videoOff = false, currentFacingMode = 'user';
    let gridOverlay = false, hideCameras = false;
    const iceServers = [{ urls: "stun:stun.l.google.com:19302" }]; 

    // Fullscreen logic
    let fullscreenState = { element: null, parent: null, nextSibling: null };
    function toggleFullscreen(videoElement) {
        if (fullscreenState.element) {
            // Close fullscreen
            fullscreenState.parent.insertBefore(fullscreenState.element, fullscreenState.nextSibling);
            fullscreenState.element.classList.remove('fullscreen-video');
            document.querySelector('.close-fullscreen-btn')?.remove();
            fullscreenState = { element: null, parent: null, nextSibling: null };
            return;
        }
        if (videoElement) {
            // Open fullscreen
            fullscreenState.element = videoElement;
            fullscreenState.parent = videoElement.parentNode;
            fullscreenState.nextSibling = videoElement.nextSibling;
            document.body.appendChild(videoElement);
            videoElement.classList.add('fullscreen-video');
            const closeBtn = document.createElement('button');
            closeBtn.textContent = 'X';
            closeBtn.className = 'close-fullscreen-btn';
            closeBtn.onclick = (e) => { e.stopPropagation(); toggleFullscreen(null); }; 
            document.body.appendChild(closeBtn);
        }
    }
    window.toggleFullscreen = toggleFullscreen; // Expose globally

    const addFullscreenListener = (videoElement) => {
        videoElement.onclick = () => {
            if (!document.querySelector('.fullscreen-video')) {
                 toggleFullscreen(videoElement);
            }
        };
    };
    addFullscreenListener(localVideo);

    // --- Call view modes (Grid + Overlay, Hide Cameras) ---
    const updateViewButtons = () => {
        if (allCamsBtn) {
            const ico = document.getElementById('allCamsIcon');
            const lbl = allCamsBtn.querySelector('.ig-lbl');
            if (ico) ico.textContent = gridOverlay ? '📺' : '🔳';
            if (lbl) lbl.textContent = gridOverlay ? 'Overlay' : 'All';
        }
        if (hideCamBtn) {
            const ico = document.getElementById('hideCamIcon');
            const lbl = hideCamBtn.querySelector('.ig-lbl');
            if (ico) ico.textContent = hideCameras ? '👁️' : '🙈';
            if (lbl) lbl.textContent = hideCameras ? 'Show' : 'Hide';
        }
        // If cameras are hidden, switching camera is not meaningful
        const inCallNow = !!(joinBtn && joinBtn.disabled); // joinBtn disabled when in-call
        if (switchCamBtn) switchCamBtn.disabled = (!inCallNow) || hideCameras;
    };

    // Reset helper exposed for other UI buttons (e.g., header call toggle)
    window._resetCallViewModes = () => {
        gridOverlay = false;
        hideCameras = false;
        document.getElementById('main-content').classList.remove('call-overlay');
        videos.classList.remove('grid-mode');
        videos.classList.remove('videos-hidden');
        updateViewButtons();
    };

    const stopLocalVideo = async () => {
        if (!localStream) return;
        const vTracks = localStream.getVideoTracks();
        if (!vTracks || vTracks.length === 0) return;
        vTracks.forEach(t => {
            try { t.stop(); } catch(e) {}
            try { localStream.removeTrack(t); } catch(e) {}
        });
        // Detach camera from outgoing peers (keep audio)
        for (const id in peerConnections) {
            const pc = peerConnections[id];
            try {
                pc.getSenders().forEach(sender => {
                    if (sender && sender.track && sender.track.kind === 'video') {
                        try { sender.replaceTrack(null); } catch(e) {}
                    }
                });
            } catch(e) {}
        }
        // Update local preview
        try { localVideo.srcObject = localStream; } catch(e) {}
        videoOff = true;
        const vi = document.getElementById('videoIcon');
        const lbl = videoBtn ? videoBtn.querySelector('.ig-lbl') : null;
        if (vi) vi.textContent = '🚫';
        if (lbl) lbl.textContent = 'Cam On';
    };

    const resumeLocalVideo = async () => {
        if (!localStream) return;
        // If already has video, just ensure it's enabled
        if (localStream.getVideoTracks().length > 0) {
            localStream.getVideoTracks().forEach(t => t.enabled = true);
            return;
        }
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: currentFacingMode, width: 320, height: 240 },
            audio: false
        });
        const newVideoTrack = stream.getVideoTracks()[0];
        if (!newVideoTrack) return;

        localStream.addTrack(newVideoTrack);

        // Replace on each peer (no renegotiation needed when sender exists)
        for (const id in peerConnections) {
            const pc = peerConnections[id];
            try {
                const sender = pc.getSenders().find(s => s.track && s.track.kind === 'video') ||
                               pc.getSenders().find(s => !s.track); // fallback if track was null
                if (sender && sender.replaceTrack) {
                    try { await sender.replaceTrack(newVideoTrack); } catch(e) {}
                } else {
                    // Last-resort: add track (may trigger renegotiation)
                    try { pc.addTrack(newVideoTrack, localStream); } catch(e) {}
                }
            } catch(e) {}
        }

        // Update local preview
        localVideo.srcObject = localStream;
        try { await localVideo.play(); } catch(e) {}

        videoOff = false;
        const vi = document.getElementById('videoIcon');
        const lbl = videoBtn ? videoBtn.querySelector('.ig-lbl') : null;
        if (vi) vi.textContent = '🎥';
        if (lbl) lbl.textContent = 'Cam Off';
    };

    const setGridOverlay = (enabled) => {
        gridOverlay = enabled;
        if (gridOverlay) {
            hideCameras = false;
            videos.classList.remove('videos-hidden');
            videos.classList.add('grid-mode');
            document.getElementById('main-content').classList.add('show-call');
            document.getElementById('main-content').classList.add('call-overlay');
            // If local camera was fully stopped (hide mode), bring it back when entering grid/overlay
            if (localStream && localStream.getVideoTracks().length === 0) {
                resumeLocalVideo().catch(() => {});
            }
        } else {
            videos.classList.remove('grid-mode');
            document.getElementById('main-content').classList.remove('call-overlay');
        }
        updateViewButtons();
    };

    const setHideCameras = async (enabled) => {
        hideCameras = enabled;
        if (hideCameras) {
            // Close fullscreen if a video is fullscreened
            if (fullscreenState.element) toggleFullscreen(null);
            // Exit grid/overlay and hide the entire video stage
            setGridOverlay(false);
            await stopLocalVideo();
            videos.classList.add('videos-hidden');
        } else {
            videos.classList.remove('videos-hidden');
            try { await resumeLocalVideo(); } catch(e) {
                console.error('Failed to resume camera:', e);
            }
        }
        updateViewButtons();
    };

    if (allCamsBtn) {
        allCamsBtn.onclick = () => setGridOverlay(!gridOverlay);
    }
    if (hideCamBtn) {
        hideCamBtn.onclick = async () => { await setHideCameras(!hideCameras); };
    }

    // Video toggle (collapse/expand)
    toggleVideosBtn.onclick = () => {
        videos.classList.toggle('collapsed');
        toggleVideosBtn.textContent = videos.classList.contains('collapsed') ? '▼' : '▲';
    };

    const toggleCallButtons = (inCall) => {
        joinBtn.disabled = inCall;
        [muteBtn, videoBtn, leaveBtn, switchCamBtn, allCamsBtn, hideCamBtn].forEach(b => {
            if (b) b.disabled = !inCall;
        });
        // If cameras are hidden, keep switchCam disabled even in-call
        if (switchCamBtn) switchCamBtn.disabled = !inCall || hideCameras;
        updateViewButtons();
    };

    // Join Call
    joinBtn.onclick = async () => {
        try {
            // Reset view modes on fresh join
            if (window._resetCallViewModes) window._resetCallViewModes();

            localStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: currentFacingMode, width: 320, height: 240 }, audio: true });
            localVideo.srcObject = localStream;
            localVideo.play();
            videos.classList.add('show');
            videos.classList.remove('collapsed');
            toggleVideosBtn.textContent = '▲';
            toggleCallButtons(true);
            socket.emit('join-room');
        } catch (err) {
            console.error("Error accessing media devices:", err); 
            showCustomAlert('Could not start video. Please check permissions.');
        }
    };
    
    // Leave Call
    leaveBtn.onclick = () => {
        // Reset view modes
        if (window._resetCallViewModes) window._resetCallViewModes();

        socket.emit('leave-room');
        for (let id in peerConnections) peerConnections[id].close();
        peerConnections = {};
        if (localStream) localStream.getTracks().forEach(track => track.stop());
        localStream = null; 
        localVideo.srcObject = null; 
        videos.classList.remove('show'); 
        videos.classList.add('collapsed');
        document.querySelectorAll('#videos video:not(#local)').forEach(v => v.remove());
        if (fullscreenState.element) toggleFullscreen(null);
        toggleCallButtons(false);
        
        // --- ADDED ---
        // Hide the entire call UI container
        document.getElementById('main-content').classList.remove('show-call');
    };

    // Switch Camera
    switchCamBtn.onclick = async () => {
        if (!localStream) return;
        if (hideCameras) return;
        currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
        try {
            localStream.getTracks().forEach(track => track.stop());
            
            const newStream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: currentFacingMode, width: 320, height: 240 }, 
                audio: true 
            });
            localStream = newStream;
            localVideo.srcObject = localStream; 
            
            for (const id in peerConnections) {
                const pc = peerConnections[id];
                if (pc.getSenders) {
                    pc.getSenders().forEach(sender => {
                        if (sender.track && sender.track.kind === 'video' && newStream.getVideoTracks().length > 0) {
                            sender.replaceTrack(newStream.getVideoTracks()[0]);
                        } else if (sender.track && sender.track.kind === 'audio' && newStream.getAudioTracks().length > 0) {
                             sender.replaceTrack(newStream.getAudioTracks()[0]);
                        }
                    });
                }
            }
        } catch (err) {
            console.error('Failed to switch camera:', err);
            showCustomAlert('Failed to switch camera.');
            currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
        }
    };

    // Mute/Unmute Audio
    muteBtn.onclick = () => {
        if (!localStream) return;
        isMuted = !isMuted;
        localStream.getAudioTracks().forEach(track => track.enabled = !isMuted);
        const mi = document.getElementById('muteIcon');
        const lbl = muteBtn.querySelector('.ig-lbl');
        if (mi) mi.textContent = isMuted ? '🔇' : '🎤';
        if (lbl) lbl.textContent = isMuted ? 'Unmute' : 'Mute';
    };

    // Video On/Off
    videoBtn.onclick = async () => {
        if (!localStream) return;

        // If cameras are hidden, show them + resume camera first
        if (hideCameras) {
            await setHideCameras(false);
            return;
        }

        // If camera was fully stopped (no video tracks), restart it
        if (localStream.getVideoTracks().length === 0) {
            try { await resumeLocalVideo(); } catch(e) {}
            return;
        }

        videoOff = !videoOff;
        localStream.getVideoTracks().forEach(track => track.enabled = !videoOff);
        const vi = document.getElementById('videoIcon');
        const lbl = videoBtn.querySelector('.ig-lbl');
        if (vi) vi.textContent = videoOff ? '🚫' : '🎥';
        if (lbl) lbl.textContent = videoOff ? 'Cam On' : 'Cam Off';
    };

    // Handle existing users when joining
    socket.on('all-users', data => {
        data.users.forEach(id => {
            createPeerConnection(id, true); // True means create an offer
        });
    });

    // Handle new user joining
    socket.on('user-joined', data => {
        if (localStream) { 
            createPeerConnection(data.sid, true);
        }
    });

    // Handle user leaving
    socket.on('user-left', data => {
        if (peerConnections[data.sid]) {
            peerConnections[data.sid].close();
            delete peerConnections[data.sid];
            let vid = document.getElementById(`video_${data.sid}`);
            if (vid) {
                if(fullscreenState.element === vid) toggleFullscreen(null);
                vid.remove();
            }
            if (document.querySelectorAll('#videos video:not(#local)').length === 0 && !localStream) {
                 videos.classList.remove('show');
                 videos.classList.add('collapsed');
            }
        }
    });

    // Handle signaling data (SDP and ICE)
    socket.on('signal', async data => {
        const id = data.from;
        let pc = peerConnections[id];

        if (!pc) {
            pc = createPeerConnection(id, false);
        }

        if (data.data.sdp) {
            try {
                await pc.setRemoteDescription(new RTCSessionDescription(data.data.sdp));
                
                if (data.data.sdp.type === 'offer') {
                    const answer = await pc.createAnswer();
                    await pc.setLocalDescription(answer);
                    socket.emit('signal', { to: id, data: { sdp: pc.localDescription } });
                }
            } catch (e) {
                console.error("Error handling remote SDP:", e);
            }
        } else if (data.data.candidate) {
            try {
                await pc.addIceCandidate(new RTCIceCandidate(data.data.candidate));
            } catch (e) {
                 console.error("Error adding ICE candidate:", e);
            }
        }
    });

    // Core Peer Connection creation function
    function createPeerConnection(id, isOfferer) {
        const pc = new RTCPeerConnection({ iceServers: iceServers });
        peerConnections[id] = pc;

        pc.onicecandidate = e => {
            if (e.candidate) socket.emit('signal', { to: id, data: { candidate: e.candidate } });
        };

        pc.ontrack = e => {
            let vid = document.getElementById(`video_${id}`);
            if (!vid) {
                vid = document.createElement('video');
                vid.id = `video_${id}`;
                vid.autoplay = true;
                vid.playsInline = true;
                vid.muted = false;
                addFullscreenListener(vid);

                // Practical mobile layout:
                // - first remote becomes the main stage
                // - additional remotes become thumbnails
                const hasMain = videos.querySelector('.remote-main') !== null;
                vid.className = hasMain ? 'remote-thumb' : 'remote-main';

                videos.appendChild(vid);
                videos.classList.add('show');
            }
            vid.srcObject = e.streams[0];
        };

        if (localStream) { 
            localStream.getTracks().forEach(track => pc.addTrack(track, localStream));
        }

        if (isOfferer) {
            pc.onnegotiationneeded = () => {
                 pc.createOffer()
                    .then(offer => pc.setLocalDescription(offer))
                    .then(() => socket.emit('signal', { to: id, data: { sdp: pc.localDescription } }))
                    .catch(e => console.error("Error creating offer:", e));
            };
        }
        return pc;
    }
}
</script>
</body>
</html>
'''

# --- Connections Server Routes ---

def _clean_username(value):
    value = str(value or '').strip()
    value = re.sub(r'[\x00-\x1f\x7f]', '', value)
    value = value[:MAX_USERNAME_CHARS]
    return value or f"User-{secrets.token_hex(2)}"

def _auth_rate_limited(ip):
    now = time.time()
    with AUTH_LOCK:
        entry = AUTH_FAILURES.get(ip)
        if not entry:
            return False
        failures = [t for t in entry.get('failures', []) if now - t < AUTH_WINDOW_SECONDS]
        blocked_until = entry.get('blocked_until', 0)
        AUTH_FAILURES[ip] = {'failures': failures, 'blocked_until': blocked_until}
        return blocked_until > now

def _record_auth_failure(ip):
    now = time.time()
    with AUTH_LOCK:
        entry = AUTH_FAILURES.setdefault(ip, {'failures': [], 'blocked_until': 0})
        entry['failures'] = [t for t in entry['failures'] if now - t < AUTH_WINDOW_SECONDS]
        entry['failures'].append(now)
        if len(entry['failures']) >= AUTH_MAX_FAILURES:
            entry['blocked_until'] = now + AUTH_BLOCK_SECONDS

def _clear_auth_failures(ip):
    with AUTH_LOCK:
        AUTH_FAILURES.pop(ip, None)

def _message_rate_limited(user):
    now = time.time()
    times = [t for t in user.get('message_times', []) if now - t < MESSAGE_RATE_WINDOW_SECONDS]
    if len(times) >= MESSAGE_RATE_MAX:
        user['message_times'] = times
        return True
    times.append(now)
    user['message_times'] = times
    return False

def _current_user():
    return connected_users.get(request.sid)

def _emit_action_error(message):
    emit('action_error', {'message': message}, room=request.sid)

def _remember_chat_item(item):
    evicted_file_ids = []
    with CHAT_HISTORY_LOCK:
        CHAT_HISTORY[item['id']] = dict(item)
        while len(CHAT_HISTORY) > CHAT_HISTORY_MAX:
            _old_id, old_item = CHAT_HISTORY.popitem(last=False)
            if isinstance(old_item, dict) and old_item.get('fileId'):
                evicted_file_ids.append(old_item.get('fileId'))
    for file_id in evicted_file_ids:
        _delete_chat_file(file_id)

@app.route('/')
def index_chat():
    return render_template_string(HTML)

@app.route('/health')
def health_check():
    return "OK", 200

def _connected_user_by_client_id(client_id):
    if not isinstance(client_id, str):
        return None
    with USER_STATE_LOCK:
        for user in connected_users.values():
            if user.get('client_id') == client_id and user.get('username') != 'pending':
                return user
    return None

def _http_chat_user():
    if not session.get('chat_logged_in'):
        return None
    client_id = session.get('chat_client_id')
    if not isinstance(client_id, str) or not CLIENT_ID_RE.fullmatch(client_id):
        return None
    return _connected_user_by_client_id(client_id)

def _valid_chat_csrf():
    expected = session.get('chat_csrf_token', '')
    supplied = request.headers.get('X-CSRF-Token', '')
    return bool(
        isinstance(expected, str) and isinstance(supplied, str) and
        expected and supplied and secrets.compare_digest(expected, supplied)
    )

def _abort_pending_upload(upload_id):
    with CHAT_FILES_LOCK:
        meta = CHAT_PENDING_UPLOADS.get(upload_id)
    if not meta:
        return
    upload_lock = meta.get('lock')
    if upload_lock is None:
        upload_lock = contextlib.nullcontext()
    with upload_lock:
        with CHAT_FILES_LOCK:
            meta = CHAT_PENDING_UPLOADS.pop(upload_id, None)
        if not meta:
            return
        try:
            temp = CHAT_FILE_DIR / meta.get('temp_name', '')
            if temp.parent == CHAT_FILE_DIR and (temp.is_file() or temp.is_symlink()):
                temp.unlink(missing_ok=True)
        except Exception:
            pass

def _prune_stale_chat_uploads(max_age_seconds=900):
    now = time.time()
    stale_files = []
    stale_pending = []
    with CHAT_FILES_LOCK:
        for file_id, meta in list(CHAT_FILES.items()):
            if not meta.get('claimed') and now - float(meta.get('created_at', now)) > max_age_seconds:
                stale_files.append(file_id)
        for upload_id, meta in list(CHAT_PENDING_UPLOADS.items()):
            if now - float(meta.get('last_activity', meta.get('created_at', now))) > max_age_seconds:
                stale_pending.append(upload_id)
    for file_id in stale_files:
        _delete_chat_file(file_id)
    for upload_id in stale_pending:
        _abort_pending_upload(upload_id)


def _chat_upload_rate_limited(client_id):
    now = time.time()
    with CHAT_FILES_LOCK:
        events = [t for t in CHAT_UPLOAD_EVENTS.get(client_id, []) if now - t < CHAT_UPLOAD_WINDOW_SECONDS]
        if len(events) >= CHAT_UPLOAD_MAX_PER_WINDOW:
            CHAT_UPLOAD_EVENTS[client_id] = events
            return True
        events.append(now)
        CHAT_UPLOAD_EVENTS[client_id] = events
        return False


def _chat_reserved_usage_locked(owner_id=None):
    total = 0
    for meta in CHAT_PENDING_UPLOADS.values():
        if owner_id is None or meta.get('owner_id') == owner_id:
            try:
                total += int(meta.get('expected_size', 0))
            except Exception:
                continue
    return total


def _create_pending_chat_upload(owner_id, filename, file_type, expected_size):
    _prune_stale_chat_uploads()
    filename = _sanitize_upload_name(filename)
    file_type = str(file_type or 'application/octet-stream').lower().strip()
    if not re.fullmatch(r'[A-Za-z0-9.+_-]+/[A-Za-z0-9.+_-]+', file_type):
        file_type = 'application/octet-stream'
    expected_size = int(expected_size)
    if expected_size <= 0 or expected_size > CHAT_FILE_MAX_BYTES:
        raise ValueError('file must be between 1 byte and 150 MB')

    with CHAT_FILES_LOCK:
        current_total = _chat_storage_usage_locked()
        reserved_total = _chat_reserved_usage_locked()
        current_owner = sum(int(m.get('size', 0)) for m in CHAT_FILES.values() if m.get('owner_id') == owner_id)
        reserved_owner = _chat_reserved_usage_locked(owner_id)
        if current_total + reserved_total + expected_size > CHAT_TOTAL_QUOTA_BYTES:
            raise ValueError('temporary chat-file storage quota would be exceeded')
        if current_owner + reserved_owner + expected_size > CHAT_PER_CLIENT_QUOTA_BYTES:
            raise ValueError('your temporary chat-file quota would be exceeded')
        owner_pending = sum(1 for m in CHAT_PENDING_UPLOADS.values() if m.get('owner_id') == owner_id)
        if owner_pending >= 2:
            raise ValueError('you already have too many uploads in progress')
        if len(CHAT_PENDING_UPLOADS) >= 12:
            raise ValueError('the server already has too many uploads in progress')

        upload_id = secrets.token_urlsafe(24)
        temp_name = f'.chunk-{upload_id}-{secrets.token_hex(6)}.part'
        temp = CHAT_FILE_DIR / temp_name
        with open(temp, 'xb'):
            pass
        try:
            os.chmod(temp, 0o600)
        except OSError:
            pass
        now = time.time()
        CHAT_PENDING_UPLOADS[upload_id] = {
            'upload_id': upload_id,
            'temp_name': temp_name,
            'filename': filename,
            'file_type': file_type,
            'expected_size': expected_size,
            'received': 0,
            'next_index': 0,
            'owner_id': owner_id,
            'created_at': now,
            'last_activity': now,
            'lock': threading.Lock(),
        }
        return dict(CHAT_PENDING_UPLOADS[upload_id])


def _append_chat_upload_chunk(upload_id, owner_id, chunk_index, stream, content_length=None):
    if not CHAT_UPLOAD_SLOTS.acquire(blocking=False):
        raise RuntimeError('too many upload chunks are being processed')
    try:
        with CHAT_FILES_LOCK:
            meta = CHAT_PENDING_UPLOADS.get(upload_id)
            if not meta or meta.get('owner_id') != owner_id:
                raise PermissionError('upload not found')
            upload_lock = meta.get('lock')
        if upload_lock is None:
            raise ValueError('upload state is invalid')

        with upload_lock:
            with CHAT_FILES_LOCK:
                meta = CHAT_PENDING_UPLOADS.get(upload_id)
                if not meta or meta.get('owner_id') != owner_id:
                    raise PermissionError('upload not found')
                if int(chunk_index) != int(meta.get('next_index', -1)):
                    raise ValueError('unexpected upload chunk order')
                remaining = int(meta['expected_size']) - int(meta['received'])
                if remaining <= 0:
                    raise ValueError('upload is already complete')
                expected_chunk_size = min(CHAT_CHUNK_BYTES, remaining)
                temp_name = meta['temp_name']
                expected_offset = int(meta['received'])
            if content_length is not None and int(content_length) != expected_chunk_size:
                raise ValueError('upload chunk has the wrong size')

            temp = CHAT_FILE_DIR / temp_name
            if not temp.is_file() or temp.is_symlink() or temp.parent != CHAT_FILE_DIR:
                raise ValueError('temporary upload file could not be verified')
            if temp.stat().st_size != expected_offset:
                raise ValueError('temporary upload size does not match upload state')

            written = 0
            try:
                with open(temp, 'ab') as handle:
                    while written < expected_chunk_size:
                        chunk = stream.read(min(UPLOAD_CHUNK_BYTES, expected_chunk_size - written))
                        if not chunk:
                            break
                        written += len(chunk)
                        handle.write(chunk)
                    # Reject any extra byte beyond the expected chunk boundary.
                    if stream.read(1):
                        raise ValueError('upload chunk is too large')
                    handle.flush()
                if written != expected_chunk_size:
                    raise ValueError('upload chunk has the wrong size')
            except Exception:
                try:
                    with open(temp, 'r+b') as handle:
                        handle.truncate(expected_offset)
                except Exception:
                    pass
                raise

            with CHAT_FILES_LOCK:
                meta = CHAT_PENDING_UPLOADS.get(upload_id)
                if not meta or meta.get('owner_id') != owner_id:
                    raise PermissionError('upload no longer exists')
                if int(meta.get('next_index', -1)) != int(chunk_index) or int(meta.get('received', -1)) != expected_offset:
                    raise ValueError('upload state changed unexpectedly')
                meta['received'] = expected_offset + written
                meta['next_index'] = int(meta['next_index']) + 1
                meta['last_activity'] = time.time()
                return int(meta['received']), int(meta['expected_size'])
    finally:
        CHAT_UPLOAD_SLOTS.release()

def _complete_chat_upload(upload_id, owner_id):
    with CHAT_FILES_LOCK:
        meta = CHAT_PENDING_UPLOADS.get(upload_id)
        if not meta or meta.get('owner_id') != owner_id:
            raise PermissionError('upload not found')
        upload_lock = meta.get('lock')
    if upload_lock is None:
        raise ValueError('upload state is invalid')

    with upload_lock:
        with CHAT_FILES_LOCK:
            meta = CHAT_PENDING_UPLOADS.get(upload_id)
            if not meta or meta.get('owner_id') != owner_id:
                raise PermissionError('upload not found')
            if int(meta.get('received', 0)) != int(meta.get('expected_size', -1)):
                raise ValueError('upload is incomplete')
            meta = dict(meta)

        temp = CHAT_FILE_DIR / meta['temp_name']
        if not temp.is_file() or temp.is_symlink() or temp.parent != CHAT_FILE_DIR:
            raise ValueError('temporary upload file could not be verified')
        actual_size = temp.stat().st_size
        if actual_size != int(meta['expected_size']) or actual_size > CHAT_FILE_MAX_BYTES:
            raise ValueError('uploaded file size verification failed')

        file_id = secrets.token_urlsafe(24)
        stored_name = f'{file_id}.blob'
        target = CHAT_FILE_DIR / stored_name
        with CHAT_FILES_LOCK:
            current = CHAT_PENDING_UPLOADS.get(upload_id)
            if not current or current.get('owner_id') != owner_id:
                raise PermissionError('upload no longer exists')
            os.replace(temp, target)
            try:
                os.chmod(target, 0o600)
            except OSError:
                pass
            CHAT_PENDING_UPLOADS.pop(upload_id, None)
            CHAT_FILES[file_id] = {
                'file_id': file_id,
                'stored_name': stored_name,
                'filename': meta['filename'],
                'file_type': meta['file_type'],
                'size': actual_size,
                'owner_id': owner_id,
                'claimed': False,
                'created_at': time.time(),
            }
            return dict(CHAT_FILES[file_id])

@app.route('/chat/auth', methods=['POST'])
def chat_http_auth():
    ip = request.remote_addr or 'unknown'
    token = request.headers.get('X-Connections-Key', '')
    client_id = request.headers.get('X-Client-ID', '')
    client_secret = request.headers.get('X-Client-Secret', '')
    key = _get_server_secret_key() or ''

    valid_shape = (
        isinstance(token, str) and 32 <= len(token) <= 256 and
        isinstance(client_id, str) and bool(CLIENT_ID_RE.fullmatch(client_id)) and
        isinstance(client_secret, str) and bool(re.fullmatch(r'[A-Fa-f0-9]{64,128}', client_secret))
    )
    if not valid_shape or not key or not secrets.compare_digest(token, key):
        if not _auth_rate_limited(ip):
            _record_auth_failure(ip)
        return {'ok': False}, 401

    with USER_STATE_LOCK:
        known_secret = CLIENT_IDENTITIES.get(client_id)
        if known_secret is None or not secrets.compare_digest(known_secret, client_secret):
            return {'ok': False}, 401

    # Require a live, fully joined Socket.IO connection for this identity. The
    # HTTP cookie alone is therefore not enough to access chat files later.
    if not _connected_user_by_client_id(client_id):
        return {'ok': False}, 409

    _clear_auth_failures(ip)
    previous_client_id = session.get('chat_client_id')
    existing_csrf = session.get('chat_csrf_token', '')
    session['chat_logged_in'] = True
    session['chat_client_id'] = client_id
    if previous_client_id != client_id or not isinstance(existing_csrf, str) or len(existing_csrf) < 32:
        session['chat_csrf_token'] = secrets.token_urlsafe(32)
    return {'ok': True, 'csrf_token': session['chat_csrf_token']}, 200

@app.route('/chat/upload/init', methods=['POST'])
def chat_upload_init():
    user = _http_chat_user()
    if not user:
        return {'ok': False, 'error': 'Authentication required.'}, 401
    if not _valid_chat_csrf():
        return {'ok': False, 'error': 'Invalid CSRF token.'}, 403
    if _chat_upload_rate_limited(user['client_id']):
        return {'ok': False, 'error': 'Too many file uploads. Try again later.'}, 429

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return {'ok': False, 'error': 'Invalid upload metadata.'}, 400
    filename = data.get('filename', 'file')
    file_type = data.get('file_type', 'application/octet-stream')
    try:
        expected_size = int(data.get('size', 0))
    except Exception:
        expected_size = 0
    try:
        meta = _create_pending_chat_upload(user['client_id'], filename, file_type, expected_size)
    except ValueError as exc:
        return {'ok': False, 'error': str(exc)}, 413
    except Exception:
        logging.exception('chat upload initialization failed')
        return {'ok': False, 'error': 'Could not initialize upload.'}, 500

    return {
        'ok': True,
        'upload_id': meta['upload_id'],
        'chunk_size': CHAT_CHUNK_BYTES,
        'expected_size': meta['expected_size'],
    }, 200


@app.route('/chat/upload/<upload_id>/chunk', methods=['POST'])
def chat_upload_chunk(upload_id):
    user = _http_chat_user()
    if not user:
        return {'ok': False, 'error': 'Authentication required.'}, 401
    if not _valid_chat_csrf():
        return {'ok': False, 'error': 'Invalid CSRF token.'}, 403
    if not CHAT_FILE_ID_RE.fullmatch(upload_id or ''):
        return {'ok': False, 'error': 'Upload not found.'}, 404
    try:
        chunk_index = int(request.headers.get('X-Chunk-Index', '-1'))
    except Exception:
        return {'ok': False, 'error': 'Invalid chunk index.'}, 400
    if chunk_index < 0 or chunk_index > 64:
        return {'ok': False, 'error': 'Invalid chunk index.'}, 400
    if request.content_length is not None and request.content_length > CHAT_CHUNK_BYTES:
        return {'ok': False, 'error': 'Upload chunk is too large.'}, 413

    try:
        received, expected = _append_chat_upload_chunk(
            upload_id, user['client_id'], chunk_index, request.stream, request.content_length
        )
    except PermissionError:
        return {'ok': False, 'error': 'Upload not found.'}, 404
    except RuntimeError as exc:
        return {'ok': False, 'error': str(exc)}, 429
    except ValueError as exc:
        return {'ok': False, 'error': str(exc)}, 409
    except Exception:
        logging.exception('chat upload chunk failed')
        return {'ok': False, 'error': 'Upload chunk failed.'}, 500

    return {'ok': True, 'received': received, 'expected_size': expected}, 200


@app.route('/chat/upload/<upload_id>/complete', methods=['POST'])
def chat_upload_complete(upload_id):
    user = _http_chat_user()
    if not user:
        return {'ok': False, 'error': 'Authentication required.'}, 401
    if not _valid_chat_csrf():
        return {'ok': False, 'error': 'Invalid CSRF token.'}, 403
    if not CHAT_FILE_ID_RE.fullmatch(upload_id or ''):
        return {'ok': False, 'error': 'Upload not found.'}, 404

    try:
        meta = _complete_chat_upload(upload_id, user['client_id'])
    except PermissionError:
        return {'ok': False, 'error': 'Upload not found.'}, 404
    except ValueError as exc:
        return {'ok': False, 'error': str(exc)}, 409
    except Exception:
        logging.exception('chat upload completion failed')
        return {'ok': False, 'error': 'Could not finalize upload.'}, 500

    return {
        'ok': True,
        'file_id': meta['file_id'],
        'filename': meta['filename'],
        'file_type': meta['file_type'],
        'size': meta['size'],
    }, 200


@app.route('/chat/upload/<upload_id>/abort', methods=['POST'])
def chat_upload_abort(upload_id):
    user = _http_chat_user()
    if not user:
        return {'ok': False}, 401
    if not _valid_chat_csrf():
        return {'ok': False}, 403
    if not CHAT_FILE_ID_RE.fullmatch(upload_id or ''):
        return {'ok': True}, 200
    with CHAT_FILES_LOCK:
        meta = CHAT_PENDING_UPLOADS.get(upload_id)
        if meta and meta.get('owner_id') != user['client_id']:
            return {'ok': False}, 403
    _abort_pending_upload(upload_id)
    return {'ok': True}, 200


@app.route('/chat/file/<file_id>', methods=['GET'])
def chat_file(file_id):
    if not CHAT_FILE_ID_RE.fullmatch(file_id or ''):
        return 'Not found', 404
    if not _http_chat_user():
        return 'Unauthorized', 401

    with CHAT_FILES_LOCK:
        meta = CHAT_FILES.get(file_id)
        if not meta or not meta.get('claimed'):
            return 'Not found', 404
        meta = dict(meta)

    target = CHAT_FILE_DIR / meta['stored_name']
    if not target.is_file() or target.is_symlink() or target.parent != CHAT_FILE_DIR:
        return 'Not found', 404

    force_download = request.args.get('download') == '1' or meta['file_type'] not in SAFE_INLINE_MEDIA_TYPES
    response = send_from_directory(
        CHAT_FILE_DIR, meta['stored_name'],
        as_attachment=force_download,
        download_name=meta['filename'],
        mimetype=(meta['file_type'] if meta['file_type'] in SAFE_INLINE_MEDIA_TYPES else 'application/octet-stream'),
        conditional=True,
        max_age=0,
    )
    response.headers['Cache-Control'] = 'private, no-store, max-age=0'
    return response

@socketio.on('connect')
def handle_connect(auth):
    ip = request.remote_addr or 'unknown'
    token = auth.get('token') if isinstance(auth, dict) else None
    client_id = auth.get('client_id') if isinstance(auth, dict) else None
    client_secret = auth.get('client_secret') if isinstance(auth, dict) else None
    key = _get_server_secret_key() or ''

    valid_client_id = isinstance(client_id, str) and bool(CLIENT_ID_RE.fullmatch(client_id))
    valid_client_secret = isinstance(client_secret, str) and bool(re.fullmatch(r'[A-Fa-f0-9]{64,128}', client_secret))
    valid_token_shape = isinstance(token, str) and 32 <= len(token) <= 256
    valid_token = valid_token_shape and bool(key) and secrets.compare_digest(token, key)

    if not valid_client_id or not valid_client_secret or not valid_token:
        # Throttle only failed credentials. A valid key can never be locked out by
        # somebody else's bad guesses (prevents a trivial authentication DoS).
        if not _auth_rate_limited(ip):
            _record_auth_failure(ip)
        return False

    # Prevent another authenticated user from impersonating an existing client_id/moderator.
    with USER_STATE_LOCK:
        if len(connected_users) >= MAX_CONNECTED_USERS:
            return False
        known_secret = CLIENT_IDENTITIES.get(client_id)
        if known_secret is None:
            if len(CLIENT_IDENTITIES) >= MAX_CLIENT_IDENTITIES:
                return False
            CLIENT_IDENTITIES[client_id] = client_secret
        elif not secrets.compare_digest(known_secret, client_secret):
            return False

        connected_users[request.sid] = {
            'username': 'pending',
            'client_id': client_id,
            'is_moderator': False,
            'message_times': [],
        }

    _clear_auth_failures(ip)
    return True

@socketio.on("join")
def handle_join(username):
    global FIRST_JOINED_CLIENT_ID
    user = _current_user()
    if not user or user.get('username') != 'pending':
        return

    safe_username = _clean_username(username)
    with USER_STATE_LOCK:
        if FIRST_JOINED_CLIENT_ID is None:
            FIRST_JOINED_CLIENT_ID = user['client_id']
        user['is_moderator'] = (user['client_id'] == FIRST_JOINED_CLIENT_ID)
        user['username'] = safe_username

    emit('session_info', {
        'client_id': user['client_id'],
        'is_moderator': user['is_moderator'],
    }, room=request.sid)

    try:
        with CHAT_HISTORY_LOCK:
            history = list(CHAT_HISTORY.values())
        emit("chat_history", history, room=request.sid)
    except Exception:
        pass

    emit('message', {
        'id': f'join_{secrets.token_hex(8)}',
        'username': 'System',
        'message': f'{safe_username} has joined.'
    }, broadcast=True)

@socketio.on("message")
def handle_message(data):
    user = _current_user()
    if not user or user.get('username') == 'pending' or not isinstance(data, dict):
        return
    if _message_rate_limited(user):
        _emit_action_error('You are sending messages too quickly. Please slow down.')
        return

    message = data.get('message', '')
    if not isinstance(message, str):
        return
    message = message.strip()
    if not message:
        return
    if len(message) > MAX_TEXT_MESSAGE_CHARS:
        _emit_action_error(f'Message too long. Maximum is {MAX_TEXT_MESSAGE_CHARS} characters.')
        return

    item = {
        'id': f"msg_{secrets.token_urlsafe(12)}",
        'username': user['username'],
        'owner_id': user['client_id'],
        'message': message,
    }
    _remember_chat_item(item)
    emit("message", item, broadcast=True)

@socketio.on("file_message")
def handle_file_message(data):
    user = _current_user()
    if not user or user.get('username') == 'pending' or not isinstance(data, dict):
        return
    if _message_rate_limited(user):
        _emit_action_error('You are sending messages too quickly. Please slow down.')
        return

    file_id = data.get('file_id', '')
    if not isinstance(file_id, str) or not CHAT_FILE_ID_RE.fullmatch(file_id):
        return

    with CHAT_FILES_LOCK:
        meta = CHAT_FILES.get(file_id)
        if not meta or meta.get('owner_id') != user.get('client_id') or meta.get('claimed'):
            _emit_action_error('That uploaded file is unavailable or does not belong to you.')
            return
        target = CHAT_FILE_DIR / meta.get('stored_name', '')
        if not target.is_file() or target.is_symlink() or target.parent != CHAT_FILE_DIR:
            _emit_action_error('Uploaded file could not be verified.')
            return
        meta['claimed'] = True
        file_meta = dict(meta)

    item = {
        'id': f"msg_{secrets.token_urlsafe(12)}",
        'username': user['username'],
        'owner_id': user['client_id'],
        'message': f"[file] {file_meta['filename']}",
        'fileId': file_id,
        'filename': file_meta['filename'],
        'fileType': file_meta['file_type'],
        'fileSize': file_meta['size'],
    }
    _remember_chat_item(item)
    emit("message", item, broadcast=True)

@socketio.on("delete_message")
def handle_delete(data):
    user = _current_user()
    if not user or not isinstance(data, dict):
        return
    message_id = str(data.get('id', ''))
    if not re.fullmatch(r'msg_[A-Za-z0-9_-]{8,64}', message_id):
        return

    file_id_to_delete = None
    with CHAT_HISTORY_LOCK:
        item = CHAT_HISTORY.get(message_id)
        if not item:
            _emit_action_error('Message no longer exists or cannot be managed.')
            return
        owns_message = item.get('owner_id') == user.get('client_id')
        if not owns_message and not user.get('is_moderator'):
            _emit_action_error('You can delete only your own messages.')
            return
        removed = CHAT_HISTORY.pop(message_id, None)
        if isinstance(removed, dict):
            file_id_to_delete = removed.get('fileId')

    if file_id_to_delete:
        _delete_chat_file(file_id_to_delete)
    emit("delete_message", {'id': message_id}, broadcast=True)

@socketio.on("edit_message")
def handle_edit(data):
    user = _current_user()
    if not user or not isinstance(data, dict):
        return
    message_id = str(data.get('id', ''))
    new_message = data.get('new_message', '')
    if not re.fullmatch(r'msg_[A-Za-z0-9_-]{8,64}', message_id) or not isinstance(new_message, str):
        return
    new_message = new_message.strip()
    if not new_message or len(new_message) > MAX_TEXT_MESSAGE_CHARS:
        _emit_action_error('Edited message is empty or too long.')
        return

    with CHAT_HISTORY_LOCK:
        item = CHAT_HISTORY.get(message_id)
        if not item:
            _emit_action_error('Message no longer exists or cannot be edited.')
            return
        if item.get('owner_id') != user.get('client_id'):
            _emit_action_error('You can edit only your own messages.')
            return
        if item.get('fileType'):
            _emit_action_error('File messages cannot be edited.')
            return
        updated = dict(item)
        updated['message'] = new_message + ' (edited)'
        CHAT_HISTORY[message_id] = updated

    emit("message_edited", {
        'id': message_id,
        'new_message': new_message,
        'username': user['username']
    }, broadcast=True)

@socketio.on("join-room")
def join_video():
    user = _current_user()
    if not user or user.get('username') == 'pending':
        return
    join_room(VIDEO_ROOM)
    users_in_room = []
    try:
        users_in_room = [sid for sid in socketio.server.manager.rooms['/'].get(VIDEO_ROOM, set()) if sid != request.sid]
    except Exception:
        users_in_room = []
    emit("all-users", {"users": users_in_room})
    emit("user-joined", {"sid": request.sid}, to=VIDEO_ROOM, include_self=False)

@socketio.on("leave-room")
def leave_video():
    leave_room(VIDEO_ROOM)
    emit("user-left", {"sid": request.sid}, to=VIDEO_ROOM, include_self=False)

def _video_room_members():
    try:
        return set(socketio.server.manager.rooms['/'].get(VIDEO_ROOM, set()))
    except Exception:
        return set()

@socketio.on("signal")
def signal(data):
    user = _current_user()
    if not user or user.get('username') == 'pending':
        return
    if not isinstance(data, dict) or not isinstance(data.get('data'), dict):
        return
    target_sid = data.get('to')
    if not isinstance(target_sid, str) or target_sid == request.sid:
        return
    try:
        if len(json.dumps(data['data'], separators=(',', ':'))) > MAX_SIGNAL_PAYLOAD_CHARS:
            return
    except Exception:
        return
    members = _video_room_members()
    if request.sid in members and target_sid in members and target_sid in connected_users:
        emit("signal", {"from": request.sid, "data": data['data']}, to=target_sid)

@socketio.on("disconnect")
def on_disconnect():
    leave_room(VIDEO_ROOM)
    emit("user-left", {"sid": request.sid}, to=VIDEO_ROOM)
    username = "A user"
    client_id = None
    client_still_connected = False
    with USER_STATE_LOCK:
        user = connected_users.pop(request.sid, None)
        if user:
            username = user.get('username', 'A user')
            client_id = user.get('client_id')
            if username == 'pending':
                username = 'A user'
            if client_id:
                client_still_connected = any(u.get('client_id') == client_id for u in connected_users.values())

    # In-progress uploads are useful only while this browser identity is live.
    # Remove abandoned temporary files immediately instead of waiting for TTL.
    if client_id and not client_still_connected:
        with CHAT_FILES_LOCK:
            abandoned = [uid for uid, meta in CHAT_PENDING_UPLOADS.items() if meta.get('owner_id') == client_id]
            unclaimed = [fid for fid, meta in CHAT_FILES.items() if meta.get('owner_id') == client_id and not meta.get('claimed')]
        for upload_id in abandoned:
            _abort_pending_upload(upload_id)
        for file_id in unclaimed:
            _delete_chat_file(file_id)

    emit('message', {'id': f'leave_{int(time.time())}','username': 'System','message': f'{username} has left.'}, broadcast=True)


# -------------------------------------------------------------------
#
# PART 3: LAUNCHER / MAIN
#
# -------------------------------------------------------------------

# ----------------------------
# Launcher mode (non-server)
# ----------------------------
if __name__ == '__main__' and "--server" not in sys.argv:
    VERBOSE_MODE = "--verbose" in sys.argv
    ALLOW_LAN = "--allow-lan" in sys.argv
    server_process = None
    tunnel_proc = None
    tor_proc = None
    tor_cleanup_paths = []

    try:
        install_requirements()

        # Always generate a high-entropy one-time login key. This removes weak
        # user-chosen passwords from the default security model.
        SECRET_KEY = secrets.token_urlsafe(32)

        # Transfer the key to the child through an anonymous pipe on Termux/POSIX.
        server_process = start_server_process(SECRET_KEY, VERBOSE_MODE, ALLOW_LAN)
        
        # Wait for the single server
        server_ready = wait_for_server("http://localhost:5000/health")
        
        if server_ready:
            local_ip = get_local_ip() if ALLOW_LAN else None
            local_url = f"http://{local_ip}:5000" if local_ip else None
            online_url = None

            # Start BOTH Tor hidden-service and Cloudflare tunnel (best-effort)
            onion_url = None
            online_url = None

            if shutil.which("tor"):
                tor_proc, onion_url, _hs_dir = start_tor_hidden_service(5000, 80, "Connections")
                if tor_proc is not None:
                    tor_cleanup_paths = list(getattr(tor_proc, "_connections_cleanup_paths", []))
            else:
                print("'tor' not installed, so no Onion Link was generated.")

            if shutil.which("cloudflared"):
                tunnel_proc, online_url = start_cloudflared_tunnel(5000, "http", "Connections")
            else:
                print("'cloudflared' not installed, so no Online Link was generated.")

            print('\033[2J\033[H', end='')
            print(
f"""✅ Connections is now live!
=================================================================
🔑 Your one-time Secret Key (for login):
   {SECRET_KEY}
=================================================================
--- Server URL ---
🧅 Onion (Tor):           {onion_url or 'N/A'}
🔗 Online (Internet):     {online_url or 'N/A'}
🏠 Local (LAN/Hotspot):   {local_url or 'Disabled by default (use --allow-lan)'}
🏠 Local (This device):    http://127.0.0.1:5000

{'⚠️  LAN mode is plain HTTP; use it only on a trusted network.' if ALLOW_LAN else '🔒 Direct LAN exposure is OFF. Cloudflare/Tor still work normally.'}

Press Ctrl+C to stop the server."""
            )
            
            # Wait for user to press Ctrl+C
            try:
                while True:
                    time.sleep(3600)
            except KeyboardInterrupt:
                pass # Handled by finally
        else:
            print("\nFatal: The server failed to start. Exiting.")
            
    except KeyboardInterrupt:
        print("\nShutting down servers...")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        # Terminate all subprocesses
        try:
            if tor_proc and tor_proc.poll() is None:
                tor_proc.terminate()
                try:
                    tor_proc.wait(timeout=5)
                except Exception:
                    tor_proc.kill()
        except Exception:
            pass
        for cleanup_path in tor_cleanup_paths:
            try:
                cleanup_path = pathlib.Path(cleanup_path)
                if cleanup_path.is_dir():
                    shutil.rmtree(cleanup_path, ignore_errors=True)
                else:
                    cleanup_path.unlink(missing_ok=True)
            except Exception:
                pass
        try:
            if tunnel_proc and tunnel_proc.poll() is None:
                tunnel_proc.terminate()
        except Exception: pass
        try:
            if server_process and server_process.poll() is None:
                server_process.terminate()
        except Exception: pass
        sys.exit()

# ----------------------------
# Server code below
# ----------------------------
if __name__ == '__main__' and "--server" in sys.argv:
    SECRET_KEY_SERVER = _read_server_secret()
    QUIET_MODE_SERVER = "--quiet" in sys.argv
    ALLOW_LAN_SERVER = "--allow-lan" in sys.argv
    BIND_HOST = '0.0.0.0' if ALLOW_LAN_SERVER else '127.0.0.1'

    if not SECRET_KEY_SERVER or not (32 <= len(SECRET_KEY_SERVER) <= 256):
        print("FATAL: Server did not receive a valid one-time secret key.")
        sys.exit(1)

    SERVER_PASSWORD = SECRET_KEY_SERVER

    if QUIET_MODE_SERVER:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
    else:
        print("Starting authenticated server...")

    print(f"Starting Connections (with DB) server on {BIND_HOST}:5000...")
    try:
        socketio.run(
            app, host=BIND_HOST, port=5000,
            debug=False, use_reloader=False, allow_unsafe_werkzeug=True
        )
    except Exception as e:
        print(f"Failed to start server: {e}")

