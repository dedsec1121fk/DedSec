import os
import sys
import subprocess
import threading
import time
import mimetypes
import datetime
import contextlib
from flask import Flask, render_template_string, request, redirect, send_from_directory

# ==== AUTOINSTALL SECTION ====
def install_dependencies():
    try:
        packages = ["tor", "openssh", "cloudflared", "python", "pip"]
        for pkg in packages:
            subprocess.call(["pkg", "install", "-y", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(["pip", "install", "--upgrade", "pip"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(["pip", "install", "--upgrade", "flask"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass  # Silently ignore install errors

install_dependencies()

# ==== TOR ANONYMIZATION ====
def start_tor():
    try:
        subprocess.Popen(["tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(10)
    except Exception:
        pass

start_tor()

if not os.path.exists("Database"):
    os.makedirs("Database")

app = Flask(__name__)
port = 5002

@contextlib.contextmanager
def suppress_stdout_stderr():
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = devnull
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

def run_flask():
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host="0.0.0.0", port=port)

def start_cloudflared_tunnel(port):
    try:
        process = subprocess.Popen(
            ["cloudflared", "tunnel", "--protocol", "http2", "--url", f"http://localhost:{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        while True:
            line = process.stdout.readline()
            if not line:
                break
            if "trycloudflare.com" in line:
                for word in line.split():
                    if word.startswith("https://"):
                        return word.strip()
        process.wait()
    except Exception:
        return None

def get_file_info(filename):
    path = os.path.join("Database", filename)
    try:
        size = os.path.getsize(path)
        mtime = os.path.getmtime(path)
        mtime_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        mimetype, _ = mimetypes.guess_type(path)
        mimetype = mimetype or "Unknown"
        return {
            "size": size,
            "mtime": mtime,
            "mtime_str": mtime_str,
            "mimetype": mimetype,
        }
    except Exception:
        return {
            "size": 0,
            "mtime": 0,
            "mtime_str": "Άγνωστο",
            "mimetype": "Άγνωστο"
        }

html_template = '''
<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Βάση Δεδομένων DedSec</title>
<style>
    body {
        background-color: #000;
        color: #fff;
        font-family: Arial, sans-serif;
        margin: 0; padding: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        min-height: 100vh;
    }
    .container {
        background-color: #121212;
        padding: 20px;
        border-radius: 10px;
        width: 95%;
        max-width: 700px;
        box-sizing: border-box;
        box-shadow: 0 0 10px #800080;
    }
    h1 {
        text-align: center;
        margin-bottom: 10px;
    }
    form {
        margin-top: 15px;
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 10px;
    }
    input[type="file"], input[type="search"], select {
        padding: 10px;
        border-radius: 5px;
        border: none;
        flex-grow: 1;
        min-width: 120px;
        box-sizing: border-box;
        background: #222;
        color: #fff;
    }
    input[type="submit"] {
        background-color: #000;
        color: #fff;
        cursor: pointer;
        border-radius: 5px;
        padding: 10px 20px;
        border: none;
        min-width: 100px;
        flex-grow: 0;
        transition: background-color 0.3s ease;
    }
    input[type="submit"]:hover {
        background-color: #800080;
        color: #fff;
    }
    .file-list {
        margin-top: 20px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        max-height: 60vh;
        overflow-y: auto;
    }
    .file-item {
        background: #1e1e1e;
        padding: 12px 15px;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        word-break: break-word;
    }
    .filename {
        flex-grow: 1;
        font-weight: bold;
    }
    .buttons {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }
    .button {
        background: #000;
        color: #fff;
        padding: 6px 10px;
        border-radius: 5px;
        text-decoration: none;
        cursor: pointer;
        border: none;
        transition: background-color 0.3s ease;
    }
    .button:hover {
        background-color: #800080;
        color: #fff;
    }
    .info-popup {
        background: #222;
        border-radius: 5px;
        padding: 10px;
        color: #800080;
        max-width: 250px;
        font-size: 0.9em;
        white-space: pre-wrap;
        position: absolute;
        z-index: 1000;
        box-shadow: 0 0 10px #800080;
        display: none;
    }
</style>
<script>
    function toggleInfo(id) {
        const popup = document.getElementById('info-' + id);
        if (popup.style.display === 'block') {
            popup.style.display = 'none';
        } else {
            document.querySelectorAll('.info-popup').forEach(p => p.style.display = 'none');
            popup.style.display = 'block';
        }
    }
    window.onclick = function(event) {
        if (!event.target.classList.contains('info-button')) {
            document.querySelectorAll('.info-popup').forEach(p => p.style.display = 'none');
        }
    };
</script>
</head>
<body>
<div class="container">
    <h1>Βάση Δεδομένων DedSec</h1>
    <form class="upload-form" action="/upload" method="POST" enctype="multipart/form-data">
        <input type="file" name="file" required />
        <input type="submit" value="Αποστολή" />
    </form>
    <form class="search-form" action="/" method="GET" style="margin-bottom:0;">
        <input type="search" name="query" placeholder="Αναζήτηση αρχείων..." value="{{ request.args.get('query', '') }}" />
        <select name="sort">
            <option value="a-z" {% if sort=='a-z' %}selected{% endif %}>Ταξινόμηση Α-Ω</option>
            <option value="z-a" {% if sort=='z-a' %}selected{% endif %}>Ταξινόμηση Ω-Α</option>
            <option value="oldest" {% if sort=='oldest' %}selected{% endif %}>Παλαιότερα προς Νεότερα</option>
            <option value="newest" {% if sort=='newest' %}selected{% endif %}>Νεότερα προς Παλαιότερα</option>
            <option value="smallest" {% if sort=='smallest' %}selected{% endif %}>Μικρότερο προς Μεγαλύτερο</option>
            <option value="biggest" {% if sort=='biggest' %}selected{% endif %}>Μεγαλύτερο προς Μικρότερο</option>
        </select>
        <input type="submit" value="Αναζήτηση & Ταξινόμηση" />
    </form>
    <div class="file-list">
        {% if files %}
            {% for f in files %}
            <div class="file-item">
                <div class="filename">{{ f }}</div>
                <div class="buttons">
                    <button class="button info-button" onclick="toggleInfo({{ loop.index0 }})" type="button">Πληροφορίες</button>
                    <a href="/download/{{ f }}" class="button" download>Λήψη</a>
                    <a href="/delete/{{ f }}" class="button" onclick="return confirm('Διαγραφή αυτού του αρχείου;')">Διαγραφή</a>
                </div>
                <div class="info-popup" id="info-{{ loop.index0 }}">
                    Μέγεθος: {{ files_info[f]['size'] | filesizeformat }}<br/>
                    Τύπος: {{ files_info[f]['mimetype'] }}<br/>
                    Μεταφορτώθηκε: {{ files_info[f]['mtime_str'] }}
                </div>
            </div>
            {% endfor %}
        {% elif request.args.get('query') %}
            <div>Δεν βρέθηκαν αρχεία που να ταιριάζουν.</div>
        {% else %}
            <div>Δεν έχουν μεταφορτωθεί αρχεία ακόμα.</div>
        {% endif %}
    </div>
</div>
</body>
</html>
'''

# Helper for human readable file sizes
def filesizeformat(value):
    try:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} PB"
    except Exception:
        return "0 B"

app.jinja_env.filters['filesizeformat'] = filesizeformat

@app.route("/", methods=["GET"])
def index():
    query = request.args.get("query", "").lower()
    sort = request.args.get("sort", "a-z")

    files = os.listdir("Database")
    files_info = {f: get_file_info(f) for f in files}

    if query:
        files = [f for f in files if query in f.lower()]

    # Sort by criteria
    if sort == "a-z":
        files.sort(key=lambda f: f.lower())
    elif sort == "z-a":
        files.sort(key=lambda f: f.lower(), reverse=True)
    elif sort == "oldest":
        files.sort(key=lambda f: files_info[f]["mtime"])
    elif sort == "newest":
        files.sort(key=lambda f: files_info[f]["mtime"], reverse=True)
    elif sort == "smallest":
        files.sort(key=lambda f: files_info[f]["size"])
    elif sort == "biggest":
        files.sort(key=lambda f: files_info[f]["size"], reverse=True)
    else:
        files.sort(key=lambda f: f.lower())  # Default fallback

    return render_template_string(html_template, files=files, files_info=files_info, request=request, sort=sort)

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    if file and file.filename:
        file.save(os.path.join("Database", file.filename))
    return redirect("/")

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    return send_from_directory("Database", filename, as_attachment=True)

@app.route("/delete/<filename>", methods=["GET"])
def delete_file(filename):
    try:
        os.remove(os.path.join("Database", filename))
    except:
        pass
    return redirect("/")

if __name__ == "__main__":
    with suppress_stdout_stderr():
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        time.sleep(3)
        public_link = start_cloudflared_tunnel(port)

    if public_link:
        print(f"Δημόσια Σύνδεση Βάσης Δεδομένων DedSec:\n{public_link}")
    else:
        print("Δεν ήταν δυνατή η δημιουργία σύνδεσης.")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nΤερματισμός...")