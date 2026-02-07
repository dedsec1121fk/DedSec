#!/usr/bin/env python3
# Butterfly Chat + DedSec's Database (Unified Login Script)

import os
import sys
import time
import re
import subprocess
import shutil
import socket
import secrets
import html
import binascii
import signal
import threading
import mimetypes
import datetime
import contextlib
import pathlib
import logging
import functools
from collections import OrderedDict
from base64 import b64decode

# Try import requests to avoid runtime errors later; don't crash if it's missing
try:
    import requests
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
except Exception:
    requests = None

# Try imports for both apps
try:
    from flask import Flask, render_template_string, request, redirect, send_from_directory, session, url_for, flash, get_flashed_messages, Blueprint
    from flask_socketio import SocketIO, emit, join_room, leave_room
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
except ImportError:
    pass # Will be handled by install_requirements

# ----------------------------
# Termux-aware helper functions (Combined)
# ----------------------------
def install_requirements(termux_opt=True):
    print("Checking and installing Python requirements (if needed)...")
    try:
        import pkgutil
        # Combined requirements from both scripts
        reqs = ["flask", "flask_socketio", "requests", "cryptography"]
        to_install = []
        for r in reqs:
            if not pkgutil.find_loader(r):
                to_install.append(r)
        
        if to_install:
            cmd = [sys.executable, "-m", "pip", "install", "--no-cache-dir"] + to_install
            print("Installing:", " ".join(to_install))
            subprocess.run(cmd, check=True)
            
    except Exception as e:
        print("WARNING: automatic pip install failed or unavailable:", e)
        
    # Attempt to install cloudflared and openssh on Termux (best-effort)
    if termux_opt and os.path.exists("/data/data/com.termux"):
        print("Attempting to install Termux packages (cloudflared, openssh, tor)...")
        if shutil.which("cloudflared") is None:
            os.system("pkg update -y > /dev/null 2>&1 && pkg install cloudflared -y > /dev/null 2>&1")
        if shutil.which("ssh") is None:
            os.system("pkg update -y > /dev/null 2>&1 && pkg install openssh -y > /dev/null 2>&1")
        if shutil.which("tor") is None:
            os.system("pkg update -y > /dev/null 2>&1 && pkg install tor -y > /dev/null 2>&1")
    return

def generate_self_signed_cert(cert_path="cert.pem", key_path="key.pem"):
    # generate cert only if missing
    if os.path.exists(cert_path) and os.path.exists(key_path):
        return
    try:
        # Imports are already at top, just use them
        print(f"Generating new SSL certificate at {cert_path}...")
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        with open(key_path, "wb") as f:
            f.write(key.private_bytes(encoding=Encoding.PEM, format=PrivateFormat.TraditionalOpenSSL, encryption_algorithm=NoEncryption()))
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
        ])
        cert = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(key.public_key()) \
            .serial_number(x509.random_serial_number()).not_valid_before(datetime.datetime.utcnow()) \
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365)) \
            .add_extension(x509.SubjectAlternativeName([x509.DNSName(u"localhost")]), critical=False) \
            .sign(key, hashes.SHA256())
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(Encoding.PEM))
    except Exception as e:
        print("WARNING: cryptography module missing or failed; skipping cert generation:", e)
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

def start_server_process(secret_key, verbose_mode):
    # This single process will run both apps
    # Note: Only one key is needed now, passed as both --server and --db-password
    cmd = [sys.executable, __file__, "--server", secret_key, "--db-password", secret_key]
    if not verbose_mode:
        cmd.append("--quiet")
    return subprocess.Popen(cmd)

def wait_for_server(url, timeout=20):
    print(f"Waiting for local server at {url}...")
    start_time = time.time()
    try:
        import requests
    except Exception:
        return False
        
    while time.time() - start_time < timeout:
        try:
            # Check the chat health endpoint
            response = requests.get(url, verify=False, timeout=1)
            if response.status_code == 200:
                print(f"Server at {url} is up and running.")
                return True
        except requests.RequestException:
            time.sleep(0.5)
    print(f"Error: Local server at {url} did not start within the timeout period.")
    return False

# --- 50 GB limit for Butterfly Chat ---
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024 * 1024  # 53,687,091,200 bytes

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
    
    cmd = ["cloudflared", "tunnel", "--url", f"{proto}://localhost:{port}"]

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
def start_tor_hidden_service(local_http_port=5000, hs_virtual_port=80, name="Butterfly Chat"):
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
        f"HiddenServiceDir {hs_dir}",
        f"HiddenServicePort {hs_virtual_port} 127.0.0.1:{local_http_port}",
    ]) + "\n"

    torrc_path.write_text(torrc, encoding="utf-8")

    print(f"🧅 Starting Tor hidden service for {name}... please wait.")
    try:
        proc = subprocess.Popen(
            ["tor", "-f", str(torrc_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
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
        
        if full_path.is_dir():
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
    # Prefer parsed global if present, otherwise fall back to argv parsing
    try:
        k = globals().get("SECRET_KEY_SERVER")
        if k:
            return k
    except Exception:
        pass
    try:
        if "--server" in sys.argv:
            i = sys.argv.index("--server") + 1
            if i < len(sys.argv):
                return sys.argv[i]
    except Exception:
        pass
    return None

# ==== DB AUTHENTICATION DECORATOR ====
# This decorator protects the DB routes
def db_auth_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        server_key = _get_server_secret_key()
        # Accept token from query OR form (important for POST like /db/upload)
        token = request.values.get('token', '')
        # If token is valid, also establish a session so subsequent requests work too
        if server_key and token == server_key:
            session['db_logged_in'] = True
        if not session.get('db_logged_in') and not (server_key and token == server_key):
            return redirect(url_for('index_chat'))
        return f(*args, **kwargs)
    return decorated_function

# Bridge route: allow the front-end to set DB session via token (useful for some in-app browsers)
@db_blueprint.route("/auth", methods=["GET"])
def db_auth_bridge():
    server_key = _get_server_secret_key()
    token = request.args.get("token", "")
    if server_key and token == server_key:
        session["db_logged_in"] = True
        return "OK", 200
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
<script>
    function toggleInfo(event, id) {
        event.stopPropagation();
        document.querySelectorAll('.info-popup').forEach(p => {
            if (p.id !== 'info-' + id) p.style.display = 'none';
        });
        const popup = document.getElementById('info-' + id);
        popup.style.display = popup.style.display === 'block' ? 'none' : 'block';
    }
    document.addEventListener('click', () => {
        document.querySelectorAll('.info-popup').forEach(p => p.style.display = 'none');
    });
</script>
</head>

<body>
<div class="topbar">
  <a class="back-btn" href="/">← Back to Butterfly Chat</a>
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
        <button class="icon-button" onclick="document.getElementById('file-upload-input').click()">
            ⬆️ Upload File
        </button>

        <form id="upload-form" action="{{ url_for('database.upload_file', token=token) }}" method="POST" enctype="multipart/form-data" style="display:none;">
            <input type="file" name="file" id="file-upload-input" onchange="document.getElementById('upload-form').submit()" multiple />
            <input type="hidden" name="sort" value="{{ request.args.get('sort', 'a-z') }}" />
            <input type="hidden" name="token" value="{{ token }}" />
        </form>
    </div>

    <form class="form-group" action="{{ url_for('database.index') }}" method="GET">
        <input type="hidden" name="token" value="{{ token }}" />
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
                    <button class="button info-button" onclick="toggleInfo(event, '{{ loop.index0 ~ category }}')">ℹ️ Info</button>
                    <div class="info-popup" id="info-{{ loop.index0 ~ category }}" onclick="event.stopPropagation()">
                        <b>Type:</b> {{ info['mimetype'] }}<br/>
                        <b>Size:</b> {{ info['size'] | filesizeformat }}<br/>
                        <b>Added:</b> {{ info['mtime_str'] }}
                    </div>

                    <a href="{{ url_for('database.download_file', filename=f, token=token) }}" class="button" download onclick="return confirm(&quot;Download &apos;{{ f }}&apos; now?&quot;)">⬇️ Download</a>

                    <a href="{{ url_for('database.delete_path', filename=f, sort=sort, token=token) }}" class="button delete-button" onclick="return confirm(&quot;Delete &apos;{{ f }}&apos;? This cannot be undone.&quot;)">🗑️ Delete</a>
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
    # Keep a stable token in the URL so POST/GET actions don't bounce back to chat
    token = request.args.get("token") or _get_server_secret_key() or ""
    
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
                                  token=token)


@db_blueprint.route("/upload", methods=["POST"])
@db_auth_required
def upload_file():
    uploaded_files = request.files.getlist("file")
    sort = request.form.get("sort", "a-z")
    
    uploaded_count = 0
    
    for file in uploaded_files:
        if file and file.filename:
            filename = os.path.basename(file.filename)
            try:
                file.save(BASE_DIR / filename)
                uploaded_count += 1
            except Exception:
                flash(f"Error uploading {filename}.", 'error')

    if uploaded_count > 0:
        flash(f"Successfully uploaded {uploaded_count} file(s).", 'success')
            
    return redirect(url_for('database.index', sort=sort, token=request.values.get('token','')))

@db_blueprint.route("/download/<filename>", methods=["GET"])
@db_auth_required
def download_file(filename):
    basename = os.path.basename(filename)
    full_path = BASE_DIR / basename
    
    if full_path.exists() and full_path.is_file():
        return send_from_directory(BASE_DIR, basename, as_attachment=True)
    
    flash("Download path invalid or restricted.", 'error')
    return redirect(url_for('database.index', sort=request.args.get('sort', 'a-z'), token=request.values.get('token','')))

# --- FILE MANAGEMENT ROUTES ---

@db_blueprint.route("/delete_path", methods=["GET"])
@db_auth_required
def delete_path():
    filename_to_delete = request.args.get("filename") 
    sort = request.args.get("sort", "a-z")
    
    if filename_to_delete:
        item_name = os.path.basename(filename_to_delete)
        full_path = BASE_DIR / item_name
        
        if full_path.exists() and full_path.is_file():
            try:
                full_path.unlink()
                flash(f"File '{item_name}' successfully deleted.", 'success')
            except Exception as e:
                flash(f"Error deleting '{item_name}': {e}", 'error')
        else:
            flash(f"File '{item_name}' not found or is a folder.", 'error')
                
    return redirect(url_for('database.index', sort=sort, token=request.values.get('token','')))


# -------------------------------------------------------------------
#
# PART 2: FOX CHAT CODE (Main App)
#
# -------------------------------------------------------------------

app = Flask("chat")
# SECRET_KEY_SERVER will be set by server main
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
connected_users = {}
VIDEO_ROOM = "global_video_room"

# In-memory chat history for the current server session (not persisted)
CHAT_HISTORY = OrderedDict()
CHAT_HISTORY_MAX = 300  # number of messages to keep
CHAT_HISTORY_LOCK = threading.Lock()

# --- Register the Database Blueprint ---
app.register_blueprint(db_blueprint)

# --- MODIFIED FOR VIBER UI + THEMES ---
HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes" />
<title>Butterfly Chat</title>
<script src="https://cdn.socket.io/4.6.1/socket.io.min.js"></script>
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
<div id="login-overlay"><div id="login-box"><h2>Enter Secret Key</h2><input type="text" id="key-input" placeholder="Paste key here..."><button id="connect-btn">Connect</button><p id="login-error"></p></div></div>

<div id="main-content">
    <div class="header">
        <div class="header-left">
            <div class="avatar" aria-label="Butterfly Chat">
                <picture>
                    <source srcset="https://raw.githubusercontent.com/dedsec1121fk/dedsec1121fk.github.io/e0fab73c56ea9e68109f540f302b407ced1b14b3/Assets/Images/Logos/White%20Purple%20Butterfly%20Logo.jpeg" media="(prefers-color-scheme: light)">
                    <img id="chatLogo" src="https://raw.githubusercontent.com/dedsec1121fk/dedsec1121fk.github.io/e0fab73c56ea9e68109f540f302b407ced1b14b3/Assets/Images/Logos/Black%20Purple%20Butterfly%20Logo.jpeg" alt="Butterfly Logo">
                </picture>
            </div>
            <div class="title-wrap">
                <div class="title">Butterfly Chat</div>
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
            <button id="recordButton" onclick="toggleRecording()" title="Voice Message">🎙️</button>
            <button id="sendBtn" onclick="sendMessage()" title="Send" style="display:none;">&#10148;</button>
        </div>
        <div class="button-row">
            <button id="liveCameraBtn" onclick="openLiveCamera()" title="Camera">📸</button>
            <button onclick="sendFile()" title="Attach File">📄</button>
            <button id="dbButton" onclick="openDatabase()" title="DedSec's Database">🛡️</button>
            <button id="infoButton" onclick="showInfo()" title="Information">ℹ️</button>
        </div>
        <input type="file" id="fileInput" style="display:none">
    </div>
</div>



<script>
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
    const savedKey = localStorage.getItem("secretKey") || sessionStorage.getItem("secretKey");

    // If we already have a key (shared across tabs/windows), auto-connect and never flash the prompt.
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
        if (secretKey) {
            loginError.textContent = 'Connecting...';
            localStorage.setItem("secretKey", secretKey);
            sessionStorage.setItem("secretKey", secretKey);
            initializeChat(secretKey);
        } else {
            loginError.textContent = 'Key cannot be empty.';
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
});


function openDatabase() {
    // Open DedSec's Database in a new window/tab (shares cookies with the main app)
    const key = sessionStorage.getItem('secretKey') || '';
    const url = key ? (`/db/?token=${encodeURIComponent(key)}`) : '/db/';
    window.open(url, '_blank', 'noopener,noreferrer');
}
document.addEventListener('DOMContentLoaded', () => {
    if (dbClose && dbOverlay) {
        dbClose.onclick = () => {
            dbOverlay.style.display = 'none';
            if (iframe) iframe.src = 'about:blank';
        };
        dbOverlay.addEventListener('click', (e) => {
            if (e.target === dbOverlay) dbClose.click();
        });
    }
});

function showInfo() {
    const infoText = `Butterfly Chat — Help & Info

Links you see in the launcher:
• Cloudflared link (https://*.trycloudflare.com) — Works in ANY iOS browser (Safari/Chrome/etc.) ✅
• Local link (http://LAN_IP:PORT) — Works in ANY iOS browser ✅ (only when your iPhone is on the same Wi‑Fi / hotspot)
• Tor .onion link — Requires a Tor-capable browser/app ❗️
  iOS Safari/Chrome cannot open .onion domains. Use an iOS Tor browser (e.g. Onion Browser) to open it.

Chat basics:
• Type a message and press Send or Enter.
• 🎙️ Hold/press to record a voice message. Tap again to stop & send.
• 📷 Camera: take a photo and send it.
• 📎 Attach: send a file (up to 50GB).
• 🛡️ Database: opens DedSec's Database (your shared files).

Call controls (Instagram‑style):
• 🎤 Mute / Unmute microphone
• 🎥 Camera On / Off
• 📴 Leave call
• 🔄 Switch camera (front/back)

Security notes:
• Cloudflared is HTTPS end‑to‑end between your iPhone and Cloudflare, then tunneled to your device.
• Local link is plain HTTP on your local network (fastest). Only share it with people on your Wi‑Fi/hotspot.
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
    const socket = io({ auth: { token: secretKey } });
    socket.on('connect_error', () => {
        document.getElementById('login-error').textContent = 'Invalid Key. Please try again.';
        // Clear both, to avoid auto-loop across tabs/windows
        try { localStorage.removeItem("secretKey"); } catch(e) {}
        try { sessionStorage.removeItem("secretKey"); } catch(e) {}
        document.getElementById('main-content').style.display = 'none';
        document.getElementById('login-overlay').style.display = 'flex';
    });
    socket.on('connect', () => {
        document.getElementById('login-overlay').style.display = 'none';
        document.getElementById('main-content').style.display = 'flex';
        const st = document.getElementById('statusText'); if (st) st.textContent = 'Secure • Encrypted • Connected'; 
        let username = localStorage.getItem("username");
        if (!username) {
            let promptedName = prompt("Enter your username:");
            username = promptedName ? promptedName.trim() : "User" + Math.floor(Math.random() * 1000);
            localStorage.setItem("username", username);
        }
        document.querySelectorAll('.secure-watermark').forEach(el => el.setAttribute('data-watermark', username));
        socket.emit("join", username);
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

    const MAX_FILE_SIZE = 50 * 1024 * 1024 * 1024; // 50 GB
    const fileInput = document.getElementById('fileInput');
    const chat = document.getElementById('chat');
    const chatContainer = document.getElementById('chat-container');
    const messageInput = document.getElementById('message');

    function handleFileSelection(file) {
        if (!file) return;
        if (file.size > MAX_FILE_SIZE) {
            // Use custom alert
            showCustomAlert(`File is too large. Max: 50 GB`);
            return;
        }
        let reader = new FileReader();
        reader.onload = () => emitFile(reader.result, file.type, file.name);
        reader.readAsDataURL(file);
    };
    fileInput.addEventListener('change', e => { handleFileSelection(e.target.files[0]); e.target.value = ''; });

    function generateId() { return 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5); };
    window.sendMessage = () => {
        const text = messageInput.value.trim();
        if (!text) return;
        // Escape HTML before sending
        const safeText = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
        socket.emit("message", { id: generateId(), username: localStorage.getItem("username"), message: safeText });
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
                    const reader = new FileReader();
                    reader.onloadend = () => socket.emit("message", { id: generateId(), username: localStorage.getItem("username"), message: reader.result, fileType: blob.type, filename: `voice-message.webm` });
                    reader.readAsDataURL(blob);
                };
                mediaRecorder.start();
            }).catch(err => showCustomAlert("Microphone access was denied."));
        }
    };
    
    window.sendFile = () => fileInput.click();
    
    function emitFile(dataURL, type, name) {
        socket.emit("message", { id: generateId(), username: localStorage.getItem("username"), message: dataURL, fileType: type, filename: name });
    };

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
        let existingPreview = document.getElementById('media-preview-overlay');
        if (existingPreview) existingPreview.remove();
        const overlay = document.createElement('div');
        overlay.id = 'media-preview-overlay';
        let previewContent;
        
        const base64Data = data.message.split(',')[1];
        if (!base64Data) {
            showCustomAlert("Error reading file data.");
            return;
        }

        if (data.fileType.startsWith('image/')) {
            previewContent = document.createElement('img');
        } else if (data.fileType.startsWith('video/')) {
            previewContent = document.createElement('video');
            previewContent.controls = true;
            previewContent.autoplay = true;
            previewContent.playsInline = true;
        } else if (data.fileType.startsWith('audio/')) {
            previewContent = document.createElement('audio');
            previewContent.controls = true;
            previewContent.autoplay = true;
        } else {
            previewContent = document.createElement('div');
            previewContent.className = 'file-placeholder';
            previewContent.textContent = '📄';
        }
        
        if (previewContent.src !== undefined) previewContent.src = data.message;
        
        const controls = document.createElement('div');
        controls.id = 'media-preview-controls';
        
        const closeBtn = document.createElement('button');
        closeBtn.textContent = 'Close (X)';
        closeBtn.onclick = () => overlay.remove();
        
        const downloadLink = document.createElement('a');
        downloadLink.textContent = 'Download';
        downloadLink.href = data.message;
        downloadLink.download = data.filename;
        controls.appendChild(downloadLink);
        
        if (data.username === localStorage.getItem("username")) {
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
        captureBtn.innerHTML = '<span class="ig-ico">⚪</span><span class="ig-lbl">Capture</span>';
        const switchBtn = document.createElement('button');
        switchBtn.className = 'ig-cam-btn';
        switchBtn.innerHTML = '<span class="ig-ico">🔄</span><span class="ig-lbl">Flip</span>';
        const closeBtn = document.createElement('button');
        closeBtn.className = 'ig-cam-btn ig-cam-danger';
        closeBtn.innerHTML = '<span class="ig-ico">✕</span><span class="ig-lbl">Close</span>';
        
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
            const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
            const filename = `capture-${Date.now()}.jpg`;
            emitFile(dataUrl, 'image/jpeg', filename);
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
        
        const isSelf = data.username === localStorage.getItem("username");
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
        
        let messageText = data.message;
        if (data.fileType && messageText.startsWith('data:')) {
            // It's a file with base64 data
            const fileLink = document.createElement('span');
            fileLink.className = 'file-link';
            fileLink.textContent = data.filename;

            // Always show who sent the file
            const fileLabel = document.createElement('div');
            fileLabel.className = 'file-label';
            fileLabel.textContent = `${data.username}: ${data.filename || 'file'}`;
            content.appendChild(fileLabel);
            
            if (data.filename.includes('voice-message.webm') || data.fileType.startsWith('audio/')) {
                const audio = document.createElement('audio');
                audio.src = data.message;
                audio.controls = true;
                audio.setAttribute('controlsList', 'nodownload');
                content.appendChild(audio);
            } else if (data.fileType.startsWith('image/')) {
                const img = document.createElement('img');
                img.src = data.message;
                img.alt = data.filename;
                img.style.cursor = 'zoom-in';
                img.onclick = () => showMediaPreview(data);
                content.appendChild(img);
            } else if (data.fileType.startsWith('video/')) {
                const video = document.createElement('video');
                video.src = data.message;
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

        if (isSelf && data.username !== 'System') {
            const actions = document.createElement('div');
            actions.className = 'message-actions';
            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = '❌';
            deleteBtn.title = 'Delete';
            deleteBtn.onclick = () => socket.emit('delete_message', { id: data.id });
            
            if (!data.fileType) {
                const editBtn = document.createElement('button');
                editBtn.textContent = '📝';
                editBtn.title = 'Edit';
                editBtn.onclick = () => toggleEdit(data.id, data.message);
                actions.appendChild(editBtn);
            }
            actions.appendChild(deleteBtn);
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

    function toggleEdit(id, currentText) {
        const contentDiv = document.getElementById(`content-${id}`);
        if (contentDiv.querySelector('input')) return; 

        contentDiv.innerHTML = '';
        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentText;
        input.className = 'edit-input';
        
        const saveBtn = document.createElement('button');
        saveBtn.textContent = 'Save';
        saveBtn.onclick = () => {
            const newText = input.value.trim();
            if (newText && newText !== currentText) {
                const safeNewText = newText.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
                socket.emit('edit_message', { id: id, new_message: safeNewText });
            } else {
                contentDiv.textContent = currentText;
            }
        };
        
        const cancelBtn = document.createElement('button');
        cancelBtn.textContent = 'Cancel';
        cancelBtn.onclick = () => contentDiv.textContent = currentText;

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

# --- Butterfly Chat Server Routes ---

@app.route('/')
def index_chat():
    return render_template_string(HTML)

@app.route('/health')
def health_check():
    return "OK", 200

@socketio.on('connect')
def handle_connect(auth):
    token = None
    try:
        token = auth.get('token') if auth else None
    except Exception:
        token = None
        
    # Find the SECRET_KEY_SERVER in sys.argv (set by launcher)
    key = None
    if "--server" in sys.argv:
        try:
            key_index = sys.argv.index("--server") + 1
            if key_index < len(sys.argv):
                key = sys.argv[key_index]
        except Exception:
            pass
            
    if token != key:
        # Reject connection
        return False
        
    # --- UNIFIED LOGIN ---
    # Log them into the DB session as well
    session['db_logged_in'] = True
    
    connected_users[request.sid] = {'username': 'pending'}
    return True

@socketio.on("join")
def handle_join(username):
    safe_username = html.escape(username)
    if request.sid in connected_users:
        connected_users[request.sid]['username'] = safe_username

    # Send in-memory chat history for the current server session to the user who just joined
    try:
        with CHAT_HISTORY_LOCK:
            history = list(CHAT_HISTORY.values())
        emit("chat_history", history, room=request.sid)
    except Exception:
        pass

    emit('message', {'id': f'join_{int(time.time())}','username': 'System','message': f'{safe_username} has joined.'}, broadcast=True)
@socketio.on("message")
def handle_message(data):
    if not isinstance(data, dict): return
    
    data['username'] = html.escape(data.get('username', 'Anonymous'))
    data['id'] = html.escape(str(data.get('id', '')))

    if data.get('fileType'):
        try:
            if ',' not in data['message']: return
            header, encoded = data['message'].split(",", 1)
            
            # Check size before decoding
            # This is an approximation, but good for catching huge payloads early
            # A base64 string is ~33% larger than the binary data
            decoded_len_approx = (len(encoded) * 3) // 4
            if decoded_len_approx > MAX_FILE_SIZE_BYTES:
                emit("message", {'id': f'reject_{int(time.time())}', 'username': 'System', 'message': 'File rejected: exceeds server limit (50GB).'}, room=request.sid)
                return
                
            # A full decode is too memory-intensive for 50GB.
            # We will trust the client-side check for the exact limit
            # and rely on the approximation above as a basic safeguard.
            # A more robust solution would involve streaming uploads,
            # but that's a major architecture change.
            
            # Quick check for valid base64 characters
            if re.search(r'[^a-zA-Z0-9+/=]', encoded):
                 return # Invalid characters
            
        except Exception:
            return 
            
        data['filename'] = html.escape(data.get('filename', 'file'))
        data['fileType'] = html.escape(data.get('fileType', 'application/octet-stream'))
    else:
        data['message'] = html.escape(data.get('message', ''))
        
    # Store chat history for the current server session
    try:
        item = dict(data)
        # Avoid storing huge base64 payloads in memory (late joiners will see a placeholder)
        if item.get("fileType") and isinstance(item.get("message"), str) and item["message"].startswith("data:"):
            fname = item.get("filename", "file")
            item["message"] = f"[file] {fname}"
        with CHAT_HISTORY_LOCK:
            mid = item.get("id")
            if mid:
                CHAT_HISTORY[mid] = item
                while len(CHAT_HISTORY) > CHAT_HISTORY_MAX:
                    CHAT_HISTORY.popitem(last=False)
    except Exception:
        pass

    emit("message", data, broadcast=True)

@socketio.on("delete_message")
def handle_delete(data):
    safe_id = html.escape(str(data.get('id', '')))

    try:
        with CHAT_HISTORY_LOCK:
            CHAT_HISTORY.pop(safe_id, None)
    except Exception:
        pass

    emit("delete_message", {'id': safe_id}, broadcast=True)
@socketio.on("edit_message")
def handle_edit(data):
    if not isinstance(data, dict) or 'id' not in data or 'new_message' not in data:
        return
    safe_id = html.escape(str(data['id']))
    new_message_safe = html.escape(data['new_message'])

    # Determine editor username from current socket session
    editor = "Anonymous"
    try:
        editor = connected_users.get(request.sid, {}).get('username', "Anonymous")
    except Exception:
        editor = "Anonymous"

    # Update in-memory history so late joiners see the edited message
    try:
        with CHAT_HISTORY_LOCK:
            if safe_id in CHAT_HISTORY:
                item = dict(CHAT_HISTORY[safe_id])
                if not item.get("fileType"):
                    item["message"] = new_message_safe + " (edited)"
                CHAT_HISTORY[safe_id] = item
    except Exception:
        pass

    emit("message_edited", {'id': safe_id, 'new_message': new_message_safe, 'username': editor}, broadcast=True)

@socketio.on("join-room")
def join_video():
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

@socketio.on("signal")
def signal(data):
    target_sid = data.get('to')
    if target_sid in connected_users:
        emit("signal", {"from": request.sid, "data": data['data']}, to=target_sid)

@socketio.on("disconnect")
def on_disconnect():
    leave_room(VIDEO_ROOM)
    emit("user-left", {"sid": request.sid}, to=VIDEO_ROOM)
    username = "A user"
    if request.sid in connected_users:
        username = connected_users[request.sid].get('username', 'A user')
        if username == 'pending': username = 'A user'
        del connected_users[request.sid]
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
    server_process = None
    tunnel_proc = None
    tor_proc = None

    try:
        # Install requirements for both apps
        install_requirements()
        
        try:
            # --- ONLY ONE KEY IS NEEDED ---
            SECRET_KEY = input("🔑 Create a one-time Secret Key for this session: ").strip()
            if not SECRET_KEY:
                print("No secret key entered. Exiting.")
                sys.exit(1)
                
        except Exception:
            print("FATAL: Could not read input for key. Exiting.")
            sys.exit(1)
            
        # Pass the single key to the server process
        server_process = start_server_process(SECRET_KEY, VERBOSE_MODE)
        
        # Wait for the single server
        server_ready = wait_for_server("http://localhost:5000/health")
        
        if server_ready:
            local_ip = get_local_ip()
            local_url = f"http://{local_ip}:5000"
            online_url = None

            # Start BOTH Tor hidden-service and Cloudflare tunnel (best-effort)
            onion_url = None
            online_url = None

            if shutil.which("tor"):
                tor_proc, onion_url, _hs_dir = start_tor_hidden_service(5000, 80, "Butterfly Chat")
            else:
                print("'tor' not installed, so no Onion Link was generated.")

            if shutil.which("cloudflared"):
                tunnel_proc, online_url = start_cloudflared_tunnel(5000, "http", "Butterfly Chat")
            else:
                print("'cloudflared' not installed, so no Online Link was generated.")

            os.system('cls' if os.name == 'nt' else 'clear')
            print(
f"""✅ Butterfly Chat is now live!
=================================================================
🔑 Your one-time Secret Key (for login):
   {SECRET_KEY}
=================================================================
--- Server URL ---
🧅 Onion (Tor):           {onion_url or 'N/A'}
🔗 Online (Internet):     {online_url or 'N/A'}
🏠 Local (LAN/Hotspot):   {local_url}
🏠 Local (This device):    http://127.0.0.1:5000

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
        except Exception: pass
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
    
    # --- Get Keys/Passwords from args ---
    SECRET_KEY_SERVER = None
    DB_PASSWORD_SERVER = None
    QUIET_MODE_SERVER = "--quiet" in sys.argv
    
    try:
        key_index = sys.argv.index("--server") + 1
        if key_index < len(sys.argv):
            SECRET_KEY_SERVER = sys.argv[key_index]
    except Exception:
        pass
        
    try:
        # This will be the same as the secret key, as passed by the launcher
        db_pass_index = sys.argv.index("--db-password") + 1
        if db_pass_index < len(sys.argv):
            DB_PASSWORD_SERVER = sys.argv[db_pass_index]
    except Exception:
        pass

    if not SECRET_KEY_SERVER or not DB_PASSWORD_SERVER:
        print("FATAL: Server started without a secret key.")
        sys.exit(1)

    # --- Set passwords for the apps ---
    SERVER_PASSWORD = DB_PASSWORD_SERVER # Set global for DB blueprint (though now unused)
    app.config['SECRET_KEY'] = SECRET_KEY_SERVER # Main secret key for session
    
    if QUIET_MODE_SERVER:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
    else:
        print(f"Starting server with key: {SECRET_KEY_SERVER[:4]}...")
        
    # --- Start Main Server (Chat + DB) ---
    print("Starting Butterfly Chat (with DB) server on http://localhost:5000...")
    try:
        # This one command runs the Flask app, the SocketIO, AND the DB blueprint
        socketio.run(app, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Failed to start server: {e}")
        print("Make sure cert.pem and key.pem are present.")