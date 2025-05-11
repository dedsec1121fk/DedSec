import os
from flask import Flask, render_template_string, request
from datetime import datetime
from werkzeug.utils import secure_filename

# New imports for dynamic country & dialing‑code lists
import pycountry
from phonenumbers import COUNTRY_CODE_TO_REGION_CODE

app = Flask(__name__)

# Base folder for saving applicant details
BASE_FOLDER = os.path.expanduser("~/storage/downloads/Peoples_Lives")
os.makedirs(BASE_FOLDER, exist_ok=True)

# Dynamically build full list of country dialing codes + names
COUNTRY_CODES = []
for code, regions in COUNTRY_CODE_TO_REGION_CODE.items():
    for region in regions:
        country = pycountry.countries.get(alpha_2=region)
        if country:
            COUNTRY_CODES.append({
                "code": f"+{code}",
                "country": country.name
            })
COUNTRY_CODES_SORTED = sorted(COUNTRY_CODES, key=lambda x: x["country"])

# Dynamically build full list of country names
COUNTRIES_SORTED = sorted([c.name for c in pycountry.countries])

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <meta name="color-scheme" content="light dark">
      <title>Become a DedSec Member Now!</title>
      <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
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
        body { font-family: 'Roboto', sans-serif; margin:0; padding:20px; display:flex; justify-content:center; }
        .container { padding:40px; max-width:600px; width:100%; border-radius:8px; }
        h2 { margin-top:0; font-weight:700; font-size:1.8em; }
        label { display:block; margin:15px 0 5px; font-weight:500; }
        input, select { width:100%; padding:10px; border-radius:4px; font-size:1em; }
        .phone-group { display:flex; gap:10px; }
        .phone-group select { flex:1; }
        .phone-group input { flex:2; }
        input[type="submit"] { border:none; padding:12px; font-size:1em; cursor:pointer; border-radius:4px; margin-top:20px; }
        input[type="submit"]:hover { opacity:0.9; }
      </style>
    </head>
    <body>
      <div class="container">
        <h2>Become a DedSec Member Now!</h2>
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
    ''', country_codes=COUNTRY_CODES_SORTED, countries=COUNTRIES_SORTED)

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
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <meta name="color-scheme" content="light dark">
      <title>Application Received</title>
      <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
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
        body { font-family: 'Roboto', sans-serif; margin:0; display:flex; justify-content:center; align-items:center; height:100vh; padding:20px; }
        .container { padding:30px; border-radius:8px; text-align:center; }
        h2 { margin:0; font-weight:700; font-size:1.8em; }
        p { margin:15px 0 0; font-size:1em; }
      </style>
    </head>
    <body>
      <div class="container">
        <h2>Thank You!</h2>
        <p>Your DedSec application has been successfully submitted.</p>
      </div>
    </body>
    </html>
    ''')

if __name__ == '__main__':
    app.run(debug=True)

