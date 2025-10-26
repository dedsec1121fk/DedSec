# DedSec's Database.py
# Made by DedSec Project/dedsec1121fk!

import os
import sys
import subprocess
import threading
import time
import mimetypes
import datetime
import contextlib
import socket
import pathlib
from flask import Flask, render_template_string, request, redirect, send_from_directory, session, url_for, flash, get_flashed_messages
import getpass 

# ==== AUTO-INSTALL & SETUP ====
def install_dependencies():
    """Silently installs required packages."""
    packages = ["openssh", "cloudflared", "python", "pip"]
    for pkg in packages:
        subprocess.call(["pkg", "install", "-y", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.call(["pip", "install", "--upgrade", "pip"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.call(["pip", "install", "--upgrade", "flask"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    install_dependencies()
except Exception as e:
    print(f"⚠️  Warning: Dependency installation failed. The script might not run correctly. Error: {e}")

BASE_DIR = pathlib.Path("Database")
BASE_DIR.mkdir(exist_ok=True)


# ==== GLOBAL CONFIG & APP SETUP ====
app = Flask(__name__)
app.secret_key = os.urandom(32) 
port = 5002
SERVER_PASSWORD = None 

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
def get_local_ip():
    """Finds the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

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

def start_cloudflared_tunnel(port):
    """Starts a cloudflared tunnel, reads output for the URL, and lets the process run."""
    public_link = None
    
    try:
        process = subprocess.Popen(
            ["cloudflared", "tunnel", "--protocol", "http2", "--url", f"http://localhost:{port}"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            bufsize=1
        )
        
        start_time = time.time()
        while time.time() - start_time < 15:
            line = process.stdout.readline()
            
            if "trycloudflare.com" in line:
                for word in line.split():
                    if word.startswith("https://") and "trycloudflare.com" in word:
                        public_link = word.strip()
                        return public_link 
            
            if not line:
                time.sleep(0.5)

        return public_link

    except Exception:
        return None

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

app.jinja_env.filters['filesizeformat'] = filesizeformat

# ==== HTML TEMPLATES ====
login_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DedSec's Database - Authentication</title>
    <style>
        body {
            background-color: #0d021a; color: #e0e0e0; font-family: 'Segoe UI', sans-serif;
            display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0;
        }
        .login-container {
            background-color: #1a0f29; padding: 40px; border-radius: 10px;
            box-shadow: 0 0 25px rgba(128, 0, 128, 0.6); text-align: center;
            border: 1px solid #800080;
        }
        h1 { color: #fff; margin-bottom: 25px; }
        input[type="password"] {
            width: 100%; padding: 12px; margin-bottom: 20px; border-radius: 5px; border: 1px solid #4a2f4a;
            background: #2a1f39; color: #fff; box-sizing: border-box; font-size: 16px;
        }
        input[type="submit"] {
            background-color: #000; color: #fff; cursor: pointer; border-radius: 5px;
            padding: 12px 25px; border: 1px solid #800080; font-size: 16px; transition: all 0.3s ease;
        }
        input[type="submit"]:hover { background-color: #800080; box-shadow: 0 0 10px #800080; }
        .error { color: #ff4d4d; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>DedSec's Database Access</h1>
        <form method="POST">
            <input type="password" name="password" placeholder="Enter Session Password" required autofocus>
            <input type="submit" value="Authenticate">
        </form>
        {% if error %}
            <p class="error">{{ error }}</p>
        {% endif %}
    </div>
</body>
</html>
'''

# --- Template updated with robust confirmation prompts ---
html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=yes" />
<title>DedSec's Database - Files</title>
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
    <h1>DedSec's Database</h1>

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
        
        <form id="upload-form" action="/upload" method="POST" enctype="multipart/form-data" style="display:none;">
            <input type="file" name="file" id="file-upload-input" onchange="document.getElementById('upload-form').submit()" multiple />
            <input type="hidden" name="sort" value="{{ request.args.get('sort', 'a-z') }}" />
        </form>
    </div>
    
    <form class="form-group" action="/" method="GET">
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
                <div class="filename">
                    📄 {{ f }}
                </div>
                
                <div class="buttons">
                    <button class="button info-button" onclick="toggleInfo(event, '{{ loop.index0 ~ category }}')">Info</button>
                    <div class="info-popup" id="info-{{ loop.index0 ~ category }}" onclick="event.stopPropagation()">
                        <b>Type:</b> {{ info['mimetype'] }}<br/>
                        <b>Size:</b> {{ info['size'] | filesizeformat }}<br/>
                        <b>Added:</b> {{ info['mtime_str'] }}
                    </div>
                    
                    <a href="/download/{{ f }}" class="button" download onclick="return confirm(&quot;Download &apos;{{ f }}&apos; now?&quot;)">Download</a>
                    
                    <a href="/delete_path?filename={{ f }}&sort={{ sort }}" class="button delete-button" onclick="return confirm(&quot;Delete &apos;{{ f }}&apos;? This cannot be undone.&quot;)">Delete</a>
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

# ==== FLASK ROUTING & AUTH ====

@app.before_request
def require_login():
    """Redirects to login page if user is not authenticated."""
    if not session.get('logged_in') and request.endpoint not in ('login', 'static'):
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user authentication."""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == SERVER_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template_string(login_template, error="Invalid password. Please try again.")
    return render_template_string(login_template)

@app.route("/", methods=["GET"])
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
    categorized_files = {cat: [] for cat in list(FILE_CATEGORIES.keys()) + ['Other']}
    for p in current_files:
        category = get_file_category(p)
        categorized_files[category].append(p)
        
    messages = get_flashed_messages(with_categories=True)

    return render_template_string(html_template, 
                                  categorized_files=categorized_files, 
                                  files_info=files_info, 
                                  request=request, 
                                  sort=sort,
                                  all_filenames=all_filenames,
                                  messages=messages)


@app.route("/upload", methods=["POST"])
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
            
    return redirect(url_for('index', sort=sort))

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    basename = os.path.basename(filename)
    full_path = BASE_DIR / basename
    
    if full_path.exists() and full_path.is_file():
        return send_from_directory(BASE_DIR, basename, as_attachment=True)
    
    flash("Download path invalid or restricted.", 'error')
    return redirect(url_for('index', sort=request.args.get('sort', 'a-z')))

# --- FILE MANAGEMENT ROUTES ---

@app.route("/delete_path", methods=["GET"])
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
                
    return redirect(url_for('index', sort=sort))

# ==== MAIN EXECUTION ====
def run_flask():
    """Runs the Flask web server with logging suppressed."""
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host="0.0.0.0", port=port)

# Made by DedSec Project/dedsec1121fk!

if __name__ == "__main__":
    try:
        SERVER_PASSWORD = input("🔑 Create a password for this server session (visible in terminal): ")
        if not SERVER_PASSWORD:
            print("❌ A password is required to start the server. Shutting down.")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\nShutdown requested.")
        sys.exit(0)

    with suppress_stdout_stderr():
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        time.sleep(3)
        public_link = start_cloudflared_tunnel(port)

    local_ip = get_local_ip()
    local_link = f"http://{local_ip}:{port}"

    print("\n" + "="*40)
    print("✅ DedSec's Database is now live!")
    print("="*40)

    if public_link:
        print(f"🔗 Online Link (Internet):     {public_link}")
    else:
        print("⚠️  Online Link (Internet):     Could not generate public link.")

    print(f"🏠 Offline Link (Hotspot/LAN): {local_link}")
    print("\nUsers must enter the password you just created to gain access.")
    print("Press Ctrl+C to shut down.")

    try:
        while True:
            time.sleep(3600) 
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")