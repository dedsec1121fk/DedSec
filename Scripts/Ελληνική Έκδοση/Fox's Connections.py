#!/usr/bin/env python3
# Fox Chat + DedSec's Database (Unified Login Script) - Greek Version
#
# Both apps are now served from a SINGLE server and URL with ONE secret key.
# - Fox Chat is at: [Your_URL]/
# - Database is at: [Your_URL]/db
#
# Fox Chat: Full UI restored, 10GB uploads, Termux-friendly
# DedSec's Database: Made by DedSec Project/dedsec1121fk!
# Combined and UI modified by Gemini
# Greek translation by Assistant

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
    print("Έλεγχος και εγκατάσταση απαιτήσεων Python (αν χρειαστεί)...")
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
            print("Εγκατάσταση:", " ".join(to_install))
            subprocess.run(cmd, check=True)
            
    except Exception as e:
        print("ΠΡΟΕΙΔΟΠΟΙΗΣΗ: η αυτόματη εγκατάσταση pip απέτυχε ή δεν είναι διαθέσιμη:", e)
        
    # Attempt to install cloudflared and openssh on Termux (best-effort)
    if termux_opt and os.path.exists("/data/data/com.termux"):
        print("Προσπάθεια εγκατάστασης πακέτων Termux (cloudflared, openssh)...")
        if shutil.which("cloudflared") is None:
            os.system("pkg update -y > /dev/null 2>&1 && pkg install cloudflared -y > /dev/null 2>&1")
        if shutil.which("ssh") is None:
            os.system("pkg update -y > /dev/null 2>&1 && pkg install openssh -y > /dev/null 2&>1")
    return

def generate_self_signed_cert(cert_path="cert.pem", key_path="key.pem"):
    # generate cert only if missing
    if os.path.exists(cert_path) and os.path.exists(key_path):
        return
    try:
        # Imports are already at top, just use them
        print(f"Δημιουργία νέου πιστοποιητικού SSL στο {cert_path}...")
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        with open(key_path, "wb") as f:
            f.write(key.private_bytes(encoding=Encoding.PEM, format=PrivateFormat.TraditionalOpenSSL, encryption_algorithm=NoEncryption()))
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"GR"),
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
        print("ΠΡΟΕΙΔΟΠΟΙΗΣΗ: λείπει το module cryptography ή απέτυχε η δημιουργία πιστοποιητικού:", e)
        return

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
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
    print(f"Αναμονή για τοπικό διακομιστή στο {url}...")
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
                print(f"Ο διακομιστής στο {url} είναι ενεργός και λειτουργεί.")
                return True
        except requests.RequestException:
            time.sleep(0.5)
    print(f"Σφάλμα: Ο τοπικός διακομιστής στο {url} δεν ξεκίνησε εντός του χρονικού ορίου.")
    return False

# 10 GB limit for Fox Chat
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 * 1024  # 10,737,418,240 bytes

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

def start_cloudflared_tunnel(port, proto="https", name=""):
    """Starts a cloudflared tunnel, reads output for the URL, and lets the process run."""
    print(f"🚀 Εκκίνηση σήραγγας Cloudflare για {name} (port {port})... παρακαλώ περιμένετε.")
    
    cmd = ["cloudflared", "tunnel", "--url", f"{proto}://localhost:{port}", "--no-tls-verify"]

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        
        start_time = time.time()
        # Wait up to 15s for the URL
        while time.time() - start_time < 15:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                print(f"⚠️ Η διαδικασία Cloudflare για {name} τερματίστηκε απροσδόκητα.")
                return None, None
                
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if match:
                online_url = match.group(0)
                print(f"✅ Η σήραγγα Cloudflare για {name} είναι ενεργή.")
                return process, online_url
            
            time.sleep(0.2)

        print(f"⚠️ Δεν βρέθηκε URL Cloudflare για {name} στην έξοδο.")
        return process, None # Return process anyway, maybe it's just slow

    except Exception as e:
        print(f"❌ Αποτυχία εκκίνησης σήραγγας Cloudflare για {name}: {e}")
        return None, None


def graceful_shutdown(signum, frame):
    print("Κλείσιμο με ασφάλεια...")
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
    BASE_DIR = DOWNLOADS_DIR / "Βάση Δεδομένων DedSec"
    BASE_DIR.mkdir(exist_ok=True, parents=True)
except Exception as e:
    print(f"ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Δεν ήταν δυνατή η δημιουργία φακέλου στο φάκελο Λήψεις ({e}). Χρήση τοπικού φακέλου.")
    BASE_DIR = pathlib.Path("Αρχεία_Βάσης_Δεδομένων_DedSec")
    BASE_DIR.mkdir(exist_ok=True)


# Define file categories for organization
FILE_CATEGORIES = {
    'Εικόνες': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
    'Βίντεο': ['.mp4', '.mov', '.avi', '.mkv', '.webm'],
    'Ήχος': ['.mp3', '.wav', '.ogg', '.flac'],
    'Έγγραφα': ['.pdf', '.doc', '.docx', '.txt', '.ppt', '.pptx', '.xls', '.xlsx', '.md', '.csv'],
    'Αρχεία': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'Κώδικας': ['.py', '.js', '.html', '.css', '.json', '.xml', '.sh', '.c', '.cpp'],
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
        file_type = mimetypes.guess_type(full_path)[0] or "Άγνωστο"

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
    return 'Άλλα'

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

# ==== HTML TEMPLATES (DB) ====
# Note: url_for() is now used for all links/actions
html_template_db = '''
<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=yes" />
<title>Βάση Δεδομένων DedSec - Αρχεία</title>
<style>
    /* Global Reset and Base Styles */
    body {
        background-color: #0d021a; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 10px;
    }
    .container {
        background-color: #1a0f29; padding: 15px; border-radius: 10px; margin: auto;
        box-shadow: 0 0 25px rgba(128, 0, 128, 0.6); border: 1px solid #800080;
        max-width: 100%;
        min-height: 90vh;
    }
    
    /* Typography */
    h1 { color: #fff; text-align: center; border-bottom: 1px solid #4a2f4a; padding-bottom: 10px; }
    h2 { margin-top: 25px; font-size: 1.2em; color: #c080c0; border-left: 5px solid #800080; padding-left: 10px; }
    
    /* Flash Messages */
    .flash { padding: 10px; margin-bottom: 15px; border-radius: 5px; font-weight: bold; }
    .flash.success { background-color: #004d00; border: 1px solid #00ff00; color: #00ff00; }
    .flash.error { background-color: #4d0000; border: 1px solid #ff4d4d; color: #ff4d4d; }
    .flash.warning { background-color: #4d4d00; border: 1px solid #ffff00; color: #ffff00; }

    /* Forms and Inputs */
    .form-group {
        display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 15px; padding: 10px; 
        background: #2a1f39; border-radius: 6px; 
    }
    input, select, .button {
        padding: 8px; border-radius: 4px; border: 1px solid #4a2f4a; background: #1a0f29; color: #fff;
    }
    input[type="submit"] {
        background-color: #000; color: #fff; cursor: pointer; border-color: #800080; transition: all 0.3s ease;
    }
    input[type="submit"]:hover { background-color: #800080; box-shadow: 0 0 10px #800080; }

    /* Manager Section */
    .manager-section { 
        margin-top: 20px; 
        background: #3a2f49;
        padding: 10px;
        border-radius: 6px;
        text-align: center; /* Centering the button */
    }
    .icon-button {
        padding: 10px 15px;
        font-size: 1em;
        font-weight: bold;
        background-color: #000;
        color: #fff;
        border: 1px solid #800080;
        cursor: pointer;
        border-radius: 4px;
        transition: all 0.3s ease;
        display: inline-block; /* Allows text-align: center to work */
        margin: 5px 0; 
    }
    .icon-button:hover {
        background-color: #800080;
        box-shadow: 0 0 10px #800080;
    }
    
    /* File List Items */
    .file-item {
        background: #2a1f39; padding: 10px 12px; border-radius: 6px; display: flex; 
        flex-direction: column;
        align-items: flex-start;
        gap: 10px; margin-bottom: 8px; transition: background-color 0.2s ease;
        max-width: 100%;
        box-sizing: border-box;
    }
    .file-item:hover { background: #3a2f49; }
    
    .filename { 
        flex-grow: 1; font-weight: bold; 
        word-wrap: break-word; 
        white-space: normal;
        max-width: 100%;
        font-size: 1.1em;
    }
    .buttons { 
        display: flex; gap: 6px; flex-wrap: wrap; 
        max-width: 100%;
    }
    .button { 
        text-decoration: none; font-size: 0.9em; padding: 6px 10px;
        background-color: #000;
    }
    .delete-button { background-color:#8b0000; }
    .delete-button:hover { background-color:#ff4d4d; }
    
    /* Info Popup */
    .info-popup {
        display: none; position: absolute; background: #1a0f29; border: 1px solid #800080; border-radius: 5px;
        padding: 10px; color: #e0e0e0; z-index: 10; box-shadow: 0 5px 15px rgba(0,0,0,0.5); font-size: 0.9em;
    }

    /* Media Query for larger screens */
    @media (min-width: 600px) {
        .file-item {
            flex-direction: row;
            align-items: center;
        }
    }
    
    .footer { text-align: center; margin-top: 20px; font-size: 0.8em; color: #6a4f6a; }
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
<div class="container">
    <h1>Βάση Δεδομένων DedSec</h1>

    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="flash {{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <div class="manager-section">
        <button class="icon-button" onclick="document.getElementById('file-upload-input').click()">
            ⬆️ Αποστολή Αρχείου
        </button>
        
        <form id="upload-form" action="{{ url_for('database.upload_file') }}" method="POST" enctype="multipart/form-data" style="display:none;">
            <input type="file" name="file" id="file-upload-input" onchange="document.getElementById('upload-form').submit()" multiple />
            <input type="hidden" name="sort" value="{{ request.args.get('sort', 'a-z') }}" />
        </form>
    </div>
    
    <form class="form-group" action="{{ url_for('database.index') }}" method="GET">
        <input type="search" name="query" list="fileSuggestions" placeholder="Αναζήτηση αρχείων στη Βάση Δεδομένων..." value="{{ request.args.get('query', '') }}" style="flex-grow:1;" />
        
        <datalist id="fileSuggestions">
            {% for filename in all_filenames %}
                <option value="{{ filename }}">
            {% endfor %}
        </datalist>
        
        <select name="sort">
            <option value="a-z" {% if sort=='a-z' %}selected{% endif %}>Ταξινόμηση Α-Ω</option>
            <option value="z-a" {% if sort=='z-a' %}selected{% endif %}>Ταξινόμηση Ω-Α</option>
            <option value="newest" {% if sort=='newest' %}selected{% endif %}>Πιο Πρόσφατα</option>
            <option value="oldest" {% if sort=='oldest' %}selected{% endif %}>Πιο Παλιά</option>
            <option value="biggest" {% if sort=='biggest' %}selected{% endif %}>Μεγαλύτερα Αρχεία</option>
            <option value="smallest" {% if sort=='smallest' %}selected{% endif %}>Μικρότερα Αρχεία</option>
        </select>
        <input type="submit" value="Φίλτρο" />
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
                <div class="filename">
                    📄 {{ f }}
                </div>
                
                <div class="buttons">
                    <button class="button info-button" onclick="toggleInfo(event, '{{ loop.index0 ~ category }}')">Πληροφορίες</button>
                    <div class="info-popup" id="info-{{ loop.index0 ~ category }}" onclick="event.stopPropagation()">
                        <b>Τύπος:</b> {{ info['mimetype'] }}<br/>
                        <b>Μέγεθος:</b> {{ info['size'] | filesizeformat }}<br/>
                        <b>Προστέθηκε:</b> {{ info['mtime_str'] }}
                    </div>
                    
                    <a href="{{ url_for('database.download_file', filename=f) }}" class="button" download onclick="return confirm(&quot;Λήψη &apos;{{ f }}&apos; τώρα;&quot;)">Λήψη</a>
                    
                    <a href="{{ url_for('database.delete_path', filename=f, sort=sort) }}" class="button delete-button" onclick="return confirm(&quot;Διαγραφή &apos;{{ f }}&apos;? Αυτή η ενέργεια δεν μπορεί να αναιρεθεί.&quot;)">Διαγραφή</a>
                </div>
            </div>
            {% endfor %}
            </div>
        {% endif %}
    {% endfor %}

    {% if not found_files %}
        <p style="text-align:center; margin-top:30px;">
        {% if request.args.get('query') %}
            Δεν βρέθηκαν αρχεία που να ταιριάζουν με την αναζήτησή σας στη Βάση Δεδομένων.
        {% else %}
            Η Βάση Δεδομένων είναι άδεια. Χρησιμοποιήστε το κουμπί ⬆️ Αποστολή για να προσθέσετε αρχεία.
        {% endif %}
        </p>
    {% endif %}
    <div class="footer">Δημιουργήθηκε από το DedSec Project/dedsec1121fk!</div>
</div>
</body>
</html>
'''

# ==== FLASK ROUTING & AUTH (DB) ====
# No password required anymore for the DB. Access is open to anyone with the link.
# The main chat is still protected by the secret key.

@db_blueprint.route("/", methods=["GET"])
def index():
    query = request.args.get("query", "").lower()
    sort = request.args.get("sort", "a-z")
    
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
    categorized_files = {cat: [] for cat in list(FILE_CATEGORIES.keys()) + ['Άλλα']}
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
                                  messages=messages)


@db_blueprint.route("/upload", methods=["POST"])
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
                flash(f"Σφάλμα κατά την αποστολή του {filename}.", 'error')

    if uploaded_count > 0:
        flash(f"Επιτυχής αποστολή {uploaded_count} αρχείου/ων.", 'success')
            
    return redirect(url_for('database.index', sort=sort))

@db_blueprint.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    basename = os.path.basename(filename)
    full_path = BASE_DIR / basename
    
    if full_path.exists() and full_path.is_file():
        return send_from_directory(BASE_DIR, basename, as_attachment=True)
    
    flash("Μη έγκυρη ή περιορισμένη διαδρομή λήψης.", 'error')
    return redirect(url_for('database.index', sort=request.args.get('sort', 'a-z')))

# --- FILE MANAGEMENT ROUTES ---

@db_blueprint.route("/delete_path", methods=["GET"])
def delete_path():
    filename_to_delete = request.args.get("filename") 
    sort = request.args.get("sort", "a-z")
    
    if filename_to_delete:
        item_name = os.path.basename(filename_to_delete)
        full_path = BASE_DIR / item_name
        
        if full_path.exists() and full_path.is_file():
            try:
                full_path.unlink()
                flash(f"Το αρχείο '{item_name}' διαγράφηκε επιτυχώς.", 'success')
            except Exception as e:
                flash(f"Σφάλμα κατά τη διαγραφή του '{item_name}': {e}", 'error')
        else:
            flash(f"Το αρχείο '{item_name}' δεν βρέθηκε ή είναι φάκελος.", 'error')
                
    return redirect(url_for('database.index', sort=sort))


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

# --- Register the Database Blueprint ---
app.register_blueprint(db_blueprint)

# Full original HTML UI (restored). I used your original long UI, with client-side MAX_FILE_SIZE set to 10GB.
# --- MODIFIED FOR INSTAGRAM DM UI ---
HTML = '''
<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Fox Chat</title>
<script src="https://cdn.socket.io/4.6.1/socket.io.min.js"></script>
<style>
/* --- Global & Login --- */
body,html{height:100%;margin:0;padding:0;font-family:sans-serif;background:#121212;color:#e0e0e0;overflow:hidden;}
#login-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);display:flex;justify-content:center;align-items:center;z-index:1000}
#login-box{background:#1e1e1e;padding:25px;border-radius:8px;text-align:center;box-shadow:0 0 15px rgba(0,0,0,0.5)}
#login-box h2{margin-top:0;color:#9c27b0}
#login-box input{width:90%;padding:10px;margin:15px 0;background:#2c2c2c;border:1px solid #333;color:#e0e0e0;border-radius:4px}
#login-box button{width:95%;padding:10px;background:#4caf50;border:none;color:#fff;border-radius:4px;cursor:pointer}
#login-error{color:#f44336;margin-top:10px;height:1em}

/* --- Main Layout (Flex Column) --- */
#main-content{display:none; display: flex; flex-direction: column; height: 100%;} 

/* --- Header (IG Style) --- */
.header{
    display: flex;
    justify-content: space-between;
    align-items: center;
    background:#1e1e1e;
    margin:0;
    padding: 10px 15px;
    font-size:1.5em;
    color:#9c27b0;
    border-bottom:1px solid #333; 
    flex-shrink: 0;
}
#toggleCallUIBtn {
    background: none;
    border: none;
    color: #fff;
    font-size: 1.5rem;
    cursor: pointer;
}

/* --- Call UI (Hidden by default) --- */
#call-ui-container { display: none; flex-shrink: 0; }
#main-content.show-call #call-ui-container { display: block; }

#controls{display:flex;flex-wrap:wrap;justify-content:center;gap:8px;padding:12px;background:#1e1e1e;width:100%;}
#controls button{flex:1 1 100px;max-width:150px;min-width:80px;padding:10px;background:#2c2c2c;color:#fff;border:1px solid #333;border-radius:4px}
#controls button:hover:not(:disabled){background:#3a3a3a}
#controls button:disabled{opacity:.4}

#videos{display:none;padding:8px;background:#000;flex-wrap:wrap;gap:6px;width:100%;position:relative;}
#videos video{width:calc(25% - 8px);max-width:120px;height:auto;object-fit:cover;border:2px solid #333;border-radius:6px;cursor:zoom-in}
#videos video:not(#local){display:none} 
#videos #local{display:block;} 
#videos.show{display:flex} 
#videos.show video:not(#local){display:block} 

#video-controls-header{display:none;text-align:center;padding:5px;background-color:#1e1e1e;}
#videos.show + #video-controls-header{display:block}
#toggleVideosBtn{background:none;border:none;color:#fff;font-size:1.5em;cursor:pointer}
#videos.collapsed{display:none !important} 

/* --- Chat Container (Takes remaining space) --- */
#chat-container{
    padding: 10px;
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
    color: #aaa;
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
}
.chat-message.self .message-content{
    background: #3737a1; /* IG Blue */
    color: #fff;
    border-bottom-right-radius: 5px;
}
.chat-message.other .message-content{
    background: #3a3a3a; /* Dark Grey */
    color: #e0e0e0;
    border-bottom-left-radius: 5px;
}

/* Specific styling for media in bubbles */
.message-content img, .message-content video, .message-content audio {
    max-width: 100%;
    border-radius: 10px;
    display: block;
}
.message-content audio {
    width: 100%;
}
.file-link{cursor:pointer;color:#90caf9;text-decoration:underline; font-weight: bold;}


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
    color: #888;
}
.message-actions button:hover {
    color: #fff;
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

/* --- Input Bar (Fixed Bottom) --- */
.controls{
    position:sticky; /* Changed from fixed to sticky to bottom of flex container */
    bottom:0;
    left:0;
    right:0;
    display:flex;
    flex-wrap:nowrap; /* Don't wrap */
    gap: 8px;
    padding: 10px;
    background:#1e1e1e; 
    z-index: 10;
    align-items: center;
    flex-shrink: 0;
}
#message {
    flex-grow: 1;
    background: #2c2c2c;
    border: 1px solid #333;
    color: #e0e0e0;
    border-radius: 20px;
    padding: 10px 15px;
    font-size: 1em;
    line-height: 1.4;
    max-height: 100px; /* Allow resizing */
    resize: none;
}
.controls button {
    background: none;
    border: none;
    color: #fff;
    font-size: 1.5em;
    cursor: pointer;
    padding: 5px;
    flex-shrink: 0;
}
.controls button#sendBtn {
    font-size: 1em;
    font-weight: bold;
    color: #4caf50;
    padding: 8px 10px;
}

/* --- UI & FEATURE STYLES --- */
#media-preview-overlay, #camera-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);display:flex;flex-direction:column;justify-content:center;align-items:center;z-index:3000}
#media-preview-overlay img, #media-preview-overlay video, #media-preview-overlay audio{max-width:90vw;max-height:80vh;border:2px solid #fff}
#media-preview-overlay .file-placeholder{font-size:5em;color:#fff}
#media-preview-controls, #camera-controls{display:flex;gap:15px;margin-top:15px;flex-wrap:wrap;justify-content:center}
#media-preview-controls button, #media-preview-controls a, #camera-controls button{background:#2c2c2c;color:#fff;border:1px solid #333;border-radius:4px;padding:10px 15px;cursor:pointer;text-decoration:none;font-size:1em}
#camera-preview{max-width:100%;max-height:80vh;border:2px solid #333;background:#000}
.edit-input{background:#3a3a3a;color:#e0e0e0;border:1px solid #555;border-radius:4px;width:80%}
.fullscreen-video{position:fixed !important;top:0;left:0;width:100vw;height:100vh;max-width:none !important;max-height:none !important;margin:0;background-color:#000;object-fit:contain;z-index:2000;border-radius:0 !important;border:none !important}
.close-fullscreen-btn{position:fixed;top:15px;right:15px;z-index:2001;background:rgba(0,0,0,0.5);color:#fff;border:1px solid #fff;border-radius:50%;width:40px;height:40px;font-size:24px;line-height:40px;text-align:center;cursor:pointer}
.secure-watermark{position:absolute;top:0;left:0;width:100%;height:100%;overflow:hidden;pointer-events:none;z-index:100}
.secure-watermark::before{content:attr(data-watermark);position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-30deg);font-size:3em;color:rgba(255,255,255,0.08);white-space:nowrap}
</style>
</head>
<body>
<div id="login-overlay"><div id="login-box"><h2>Εισάγετε Μυστικό Κλειδί</h2><input type="text" id="key-input" placeholder="Επικολλήστε το κλειδί εδώ..."><button id="connect-btn">Σύνδεση</button><p id="login-error"></p></div></div>

<div id="main-content">
    <h1 class="header">
        <span>Fox Chat</span>
        <button id="toggleCallUIBtn">📞</button>
    </h1>
    
    <div id="call-ui-container">
        <div id="controls">
            <button id="joinBtn">Σύνδεση σε Κλήση</button>
            <button id="muteBtn" disabled>Σίγαση</button>
            <button id="videoBtn" disabled>Κάμερα Off</button>
            <button id="leaveBtn" disabled>Αποχώρηση</button>
            <button id="switchCamBtn" disabled>🔄 Αλλαγή Κάμερας</button>
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
        <button id="liveCameraBtn" onclick="openLiveCamera()" title="Κάμερα">📸</button>
        <button onclick="sendFile()" title="Επισύναψη Αρχείου">📄</button>
        <button id="recordButton" onclick="toggleRecording()" title="Φωνητικό Μήνυμα">🎙️</button>
        <textarea id="message" placeholder="Πληκτρολογήστε ένα μήνυμα..." rows="1"></textarea>
        <button id="sendBtn" onclick="sendMessage()">Αποστολή</button>
        <button id="dbButton" onclick="window.open('/db', '_blank');" title="Βάση Δεδομένων DedSec">🛡️</button>
        <button id="infoButton" onclick="showInfo()" title="Πληροφορίες">ℹ️</button>
        <input type="file" id="fileInput" style="display:none">
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', () => {
    const keyInput = document.getElementById('key-input');
    const connectBtn = document.getElementById('connect-btn');
    const loginError = document.getElementById('login-error');
    const savedKey = sessionStorage.getItem("secretKey");
    if (savedKey) keyInput.value = savedKey;
    connectBtn.onclick = () => {
        const secretKey = keyInput.value.trim();
        if (secretKey) {
            loginError.textContent = 'Σύνδεση...';
            sessionStorage.setItem("secretKey", secretKey);
            initializeChat(secretKey);
        } else {
            loginError.textContent = 'Το κλειδί δεν μπορεί να είναι κενό.';
        }
    };
    
    // Auto-resize textarea
    const messageInput = document.getElementById('message');
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
});

function showInfo() {
    const infoText = `Καλώς ήρθατε στο Fox Chat!

--- Πώς να Χρησιμοποιήσετε ---

Συνομιλία:
• Πληκτρολογήστε ένα μήνυμα στο πλαίσιο και πατήστε 'Αποστολή' ή Enter.
• 📸: Ανοίξτε την κάμερα της συσκευής σας για να τραβήξετε και να στείλετε μια φωτογραφία.
• 📄: Επισυνάψτε και στείλτε οποιοδήποτε αρχείο από τη συσκευή σας (μέχρι 10GB).
• 🎙️: Πατήστε για εγγραφή φωνητικού μηνύματος. Πατήστε ξανά για διακοπή και αποστολή.
• 🛡️: Ανοίγει τη βάση δεδομένων αρχείων σε νέα καρτέλα. Μπορείτε να ανεβάζετε, κατεβάζετε και να διαχειρίζεστε αρχεία εκεί.

Βίντεο Κλήση:
• Πατήστε το εικονίδιο 📞 στην κορυφή για να εμφανίσετε τα στοιχεία ελέγχου κλήσης.
• Σύνδεση σε Κλήση: Ξεκινά την κάμερα/μικρόφωνό σας και σας συνδέει στην κλήση.
• Σίγαση/Κάμερα Off: Εναλλαγή μικροφώνου και κάμερας.
• Αποχώρηση: Αποσυνδέει από την βίντεο κλήση.
• 🔄: Εναλλαγή μεταξύ μπροστινής και πίσω κάμερας.
• Κάντε κλικ σε οποιαδήποτε ροή βίντεο για να την δείτε σε πλήρη οθόνη.

Μηνύματα:
• Τα δικά σας μηνύματα έχουν κουμπιά 📝 (επεξεργασία) και ❌ (διαγραφή).
• Κάντε κλικ σε αποσταλμένες εικόνες/βίντεο για προεπισκόπηση.`;
    alert(infoText.trim());
}

function initializeChat(secretKey) {
    const socket = io({ auth: { token: secretKey } });
    socket.on('connect_error', () => {
        document.getElementById('login-error').textContent = 'Μη έγκυρο Κλειδί. Παρακαλώ δοκιμάστε ξανά.';
        sessionStorage.removeItem("secretKey");
    });
    socket.on('connect', () => {
        document.getElementById('login-overlay').style.display = 'none';
        document.getElementById('main-content').style.display = 'flex'; 
        let username = localStorage.getItem("username");
        if (!username) {
            let promptedName = prompt("Εισάγετε το όνομα χρήστη σας:");
            username = promptedName ? promptedName.trim() : "Χρήστης" + Math.floor(Math.random() * 1000);
            localStorage.setItem("username", username);
        }
        document.querySelectorAll('.secure-watermark').forEach(el => el.setAttribute('data-watermark', username));
        socket.emit("join", username);
    });
    
    // --- NEW: Toggle Call UI ---
    document.getElementById('toggleCallUIBtn').onclick = () => {
        document.getElementById('main-content').classList.toggle('show-call');
    };

    const MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024; // 10 GB
    const fileInput = document.getElementById('fileInput');
    const chat = document.getElementById('chat');
    const chatContainer = document.getElementById('chat-container');
    const messageInput = document.getElementById('message');

    function handleFileSelection(file) {
        if (!file) return;
        if (file.size > MAX_FILE_SIZE) {
            alert(`Το αρχείο είναι πολύ μεγάλο. Μέγιστο: 10 GB`);
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
    };
    messageInput.addEventListener('keydown', (e) => { 
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); // Prevent newline
            sendMessage(); 
        }
    });
    
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
                    recordButton.style.color = 'white';
                    stream.getTracks().forEach(track => track.stop());
                    const blob = new Blob(recordedChunks, { type: 'audio/webm' });
                    const reader = new FileReader();
                    reader.onloadend = () => socket.emit("message", { id: generateId(), username: localStorage.getItem("username"), message: reader.result, fileType: blob.type, filename: `voice-message.webm` });
                    reader.readAsDataURL(blob);
                };
                mediaRecorder.start();
            }).catch(err => alert("Η πρόσβαση στο μικρόφωνο απορρίφθηκε."));
        }
    };
    
    window.sendFile = () => fileInput.click();
    
    function emitFile(dataURL, type, name) {
        socket.emit("message", { id: generateId(), username: localStorage.getItem("username"), message: dataURL, fileType: type, filename: name });
    };

    function showMediaPreview(data) {
        let existingPreview = document.getElementById('media-preview-overlay');
        if (existingPreview) existingPreview.remove();
        const overlay = document.createElement('div');
        overlay.id = 'media-preview-overlay';
        let previewContent;
        
        const base64Data = data.message.split(',')[1];
        if (!base64Data) {
            alert("Σφάλμα ανάγνωσης δεδομένων αρχείου.");
            return;
        }

        if (data.fileType.startsWith('image/')) {
            previewContent = document.createElement('img');
        } else if (data.fileType.startsWith('video/')) {
            previewContent = document.createElement('video');
            previewContent.controls = true;
            previewContent.autoplay = true;
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
        closeBtn.textContent = 'Κλείσιμο (X)';
        closeBtn.onclick = () => overlay.remove();
        
        const downloadLink = document.createElement('a');
        downloadLink.textContent = 'Λήψη';
        downloadLink.href = data.message;
        downloadLink.download = data.filename;
        controls.appendChild(downloadLink);
        
        if (data.username === localStorage.getItem("username")) {
            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = 'Διαγραφή';
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
        const controls = document.createElement('div');
        controls.id = 'camera-controls';
        const captureBtn = document.createElement('button');
        captureBtn.textContent = 'Λήψη';
        const switchBtn = document.createElement('button');
        switchBtn.textContent = 'Αλλαγή Κάμερας';
        const closeBtn = document.createElement('button');
        closeBtn.textContent = 'Κλείσιμο';
        
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
                    alert('Δεν ήταν δυνατή η πρόσβαση στην κάμερα. Ελέγξτε τα δικαιώματα.');
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

    socket.on("message", data => {
        const div = document.createElement('div');
        div.className = 'chat-message';
        div.id = data.id;
        
        const isSelf = data.username === localStorage.getItem("username");
        if (isSelf) {
            div.classList.add('self');
        } else {
            div.classList.add('other');
        }

        // Wrapper for bubble + username
        const bubbleWrapper = document.createElement('div');
        bubbleWrapper.className = 'message-bubble-wrapper';

        // Add username for 'other'
        if (!isSelf && data.username !== 'Σύστημα') {
            const strong = document.createElement('strong');
            strong.textContent = `${data.username}:`;
            bubbleWrapper.appendChild(strong);
        }
        
        const content = document.createElement('div');
        content.className = 'message-content';
        content.id = `content-${data.id}`;
        
        let messageText = data.message;
        if (data.fileType && messageText.startsWith('data:')) {
            // It's a file with base64 data
            const fileLink = document.createElement('span');
            fileLink.className = 'file-link';
            fileLink.textContent = data.filename;
            
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
                video.onclick = () => showMediaPreview(data);
                content.appendChild(video);
            } else {
                fileLink.onclick = () => showMediaPreview(data);
                content.appendChild(fileLink);
            }
        } else {
            // It's a text message
            content.textContent = messageText;
            if (data.username === 'Σύστημα') {
                content.style.background = 'none';
                content.style.color = '#888';
                content.style.textAlign = 'center';
                div.style.maxWidth = '100%';
                div.style.justifyContent = 'center';
            }
        }

        bubbleWrapper.appendChild(content);
        div.appendChild(bubbleWrapper);

        if (isSelf && data.username !== 'Σύστημα') {
            const actions = document.createElement('div');
            actions.className = 'message-actions';
            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = '❌';
            deleteBtn.title = 'Διαγραφή';
            deleteBtn.onclick = () => socket.emit('delete_message', { id: data.id });
            
            if (!data.fileType) {
                const editBtn = document.createElement('button');
                editBtn.textContent = '📝';
                editBtn.title = 'Επεξεργασία';
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
        saveBtn.textContent = 'Αποθήκευση';
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
        cancelBtn.textContent = 'Ακύρωση';
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
        if(contentDiv) contentDiv.textContent = data.new_message + ' (επεξεργασμένο)';
    });
    
    // ----------------------------------------------------------------------------------
    // FULL WEBRTC LOGIC RESTORED & FIXED
    // ----------------------------------------------------------------------------------

    const videos = document.getElementById('videos'), localVideo = document.getElementById('local');
    const joinBtn = document.getElementById('joinBtn'), muteBtn = document.getElementById('muteBtn');
    const videoBtn = document.getElementById('videoBtn'), leaveBtn = document.getElementById('leaveBtn');
    const switchCamBtn = document.getElementById('switchCamBtn');
    const toggleVideosBtn = document.getElementById('toggleVideosBtn'); 
    
    let localStream, peerConnections = {}, isMuted = false, videoOff = false, currentFacingMode = 'user';
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

    // Video toggle (collapse/expand)
    toggleVideosBtn.onclick = () => {
        videos.classList.toggle('collapsed');
        toggleVideosBtn.textContent = videos.classList.contains('collapsed') ? '▼' : '▲';
    };

    const toggleCallButtons = (inCall) => {
        joinBtn.disabled = inCall;
        [muteBtn, videoBtn, leaveBtn, switchCamBtn].forEach(b => b.disabled = !inCall);
    };

    // Join Call
    joinBtn.onclick = async () => {
        try {
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
            alert('Δεν ήταν δυνατή η εκκίνηση βίντεο. Ελέγξτε τα δικαιώματα.');
        }
    };
    
    // Leave Call
    leaveBtn.onclick = () => {
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
    };

    // Switch Camera
    switchCamBtn.onclick = async () => {
        if (!localStream) return;
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
            alert('Αποτυχία αλλαγής κάμερας.');
            currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
        }
    };

    // Mute/Unmute Audio
    muteBtn.onclick = () => {
        if (!localStream) return;
        isMuted = !isMuted;
        localStream.getAudioTracks().forEach(track => track.enabled = !isMuted);
        muteBtn.textContent = isMuted ? 'Κατάργηση Σίγασης' : 'Σίγαση';
    };

    // Video On/Off
    videoBtn.onclick = () => {
        if (!localStream) return;
        videoOff = !videoOff;
        localStream.getVideoTracks().forEach(track => track.enabled = !videoOff);
        videoBtn.textContent = videoOff ? 'Κάμερα On' : 'Κάμερα Off';
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

# --- Fox Chat Server Routes ---

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
    emit('message', {'id': f'join_{int(time.time())}','username': 'Σύστημα','message': f'{safe_username} έχει συνδεθεί.'}, broadcast=True)

@socketio.on("message")
def handle_message(data):
    if not isinstance(data, dict): return
    
    data['username'] = html.escape(data.get('username', 'Ανώνυμος'))
    data['id'] = html.escape(str(data.get('id', '')))

    if data.get('fileType'):
        try:
            if ',' not in data['message']: return
            header, encoded = data['message'].split(",", 1)
            
            decoded_len = (len(encoded) * 3) // 4
            if decoded_len > MAX_FILE_SIZE_BYTES:
                emit("message", {'id': f'reject_{int(time.time())}', 'username': 'Σύστημα', 'message': 'Απόρριψη αρχείου: υπερβαίνει το όριο διακομιστή.'}, room=request.sid)
                return
                
            binascii.a2b_base64(encoded.encode('utf-8'))
            
        except (ValueError, binascii.Error, IndexError):
            return 
            
        data['filename'] = html.escape(data.get('filename', 'αρχείο'))
        data['fileType'] = html.escape(data.get('fileType', 'application/octet-stream'))
    else:
        data['message'] = html.escape(data.get('message', ''))
        
    emit("message", data, broadcast=True)

@socketio.on("delete_message")
def handle_delete(data):
    safe_id = html.escape(str(data.get('id', '')))
    emit("delete_message", {'id': safe_id}, broadcast=True)

@socketio.on("edit_message")
def handle_edit(data):
    if not isinstance(data, dict) or 'id' not in data or 'new_message' not in data:
        return
    safe_id = html.escape(str(data['id']))
    new_message_safe = html.escape(data['new_message'])
    emit("message_edited", {'id': safe_id, 'new_message': new_message_safe}, broadcast=True)

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
    if request.sid in connected_users: del connected_users[request.sid]


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

    try:
        # Install requirements for both apps
        install_requirements()
        # Generate cert for chat app
        generate_self_signed_cert()
        
        try:
            # --- ONLY ONE KEY IS NEEDED ---
            SECRET_KEY = input("🔑 Δημιουργήστε ένα μυστικό κλειδί μίας χρήσης για αυτή τη συνεδρία: ").strip()
            if not SECRET_KEY:
                print("Δεν εισήχθη μυστικό κλειδί. Έξοδος.")
                sys.exit(1)
                
        except Exception:
            print("ΚΡΙΣΙΜΟ: Δεν ήταν δυνατή η ανάγνωση εισόδου για το κλειδί. Έξοδος.")
            sys.exit(1)
            
        # Pass the single key to the server process
        server_process = start_server_process(SECRET_KEY, VERBOSE_MODE)
        
        # Wait for the single server
        server_ready = wait_for_server("https://localhost:5000/health")
        
        if server_ready:
            local_ip = get_local_ip()
            local_url = f"https://{local_ip}:5000"
            online_url = None
            
            if shutil.which("cloudflared"):
                tunnel_proc, online_url = start_cloudflared_tunnel(5000, "https", "Fox Chat")
            else:
                 print("Το 'cloudflared' δεν είναι εγκατεστημένο, οπότε δεν δημιουργήθηκε Διαδικτυακός Σύνδεσμος.")

            os.system('cls' if os.name == 'nt' else 'clear')
            print(
f"""✅ Το Fox Chat είναι πλέον ενεργό!
=================================================================
🔑 Το μυστικό κλειδί μίας χρήσης σας (για σύνδεση):
   {SECRET_KEY}
=================================================================
--- Διεύθυνση Διακομιστή ---
🔗 Διαδικτυακά (Internet):     {online_url or 'Δ/Υ'}
🏠 Εσωτερικά (Hotspot/LAN): {local_url}

Πατήστε Ctrl+C για να σταματήσετε τον διακομιστή."""
            )
            
            # Wait for user to press Ctrl+C
            try:
                while True:
                    time.sleep(3600)
            except KeyboardInterrupt:
                pass # Handled by finally
        else:
            print("\nΚρίσιμο σφάλμα: Ο διακομιστής απέτυχε να ξεκινήσει. Έξοδος.")
            
    except KeyboardInterrupt:
        print("\nΤερματισμός διακομιστών...")
    except Exception as e:
        print(f"\nΠροέκυψε ένα μη αναμενόμενο σφάλμα: {e}")
    finally:
        # Terminate all subprocesses
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
        print("ΚΡΙΣΙΜΟ: Ο διακομιστής ξεκίνησε χωρίς μυστικό κλειδί.")
        sys.exit(1)

    # --- Set passwords for the apps ---
    SERVER_PASSWORD = DB_PASSWORD_SERVER # Set global for DB blueprint
    app.config['SECRET_KEY'] = SECRET_KEY_SERVER # Main secret key for session
    
    if QUIET_MODE_SERVER:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
    else:
        print(f"Εκκίνηση διακομιστή με κλειδί: {SECRET_KEY_SERVER[:4]}...")
        
    # --- Start Main Server (Chat + DB) ---
    print("Εκκίνηση διακομιστή Fox Chat (με Βάση Δεδομένων) στο https://localhost:5000...")
    try:
        # This one command runs the Flask app, the SocketIO, AND the DB blueprint
        socketio.run(app, host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'key.pem'))
    except Exception as e:
        print(f"Αποτυχία εκκίνησης διακομιστή: {e}")
        print("Βεβαιωθείτε ότι τα cert.pem και key.pem είναι παρόντα.")