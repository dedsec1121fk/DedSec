#!/usr/bin/env python3
import os
import subprocess
import time
import re
import sys
import shutil
import socket
import secrets
import html
from base64 import b64decode
import binascii

try:
    import requests
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

def install_requirements():
    print("Έλεγχος και εγκατάσταση απαιτήσεων...")
    try:
        requirements = ["flask", "flask_socketio", "requests", "pyopenssl", "cryptography"]
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + requirements,
            check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"ΣΦΑΛΜΑ: Αποτυχία εγκατάστασης των απαιτούμενων πακέτων Python.\n{e.stderr}")
        sys.exit(1)

    if not shutil.which("cloudflared"):
        print("\n--- Απαιτείται Εγκατάσταση του 'cloudflared' ---")
        if "linux" in sys.platform and os.path.exists("/data/data/com.termux"):
            os.system("pkg update -y > /dev/null 2>&1 && pkg install cloudflared -y > /dev/null 2>&1")
        else:
            print("Παρακαλώ εγκαταστήστε το 'cloudflared' χρησιμοποιώντας τον διαχειριστή πακέτων του συστήματός σας.")

        if not shutil.which("cloudflared"):
            print("ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Το 'cloudflared' δεν βρέθηκε. Μόνο ο Σύνδεσμος Εκτός Σύνδεσης θα είναι διαθέσιμος.")
        else:
            print("Το 'cloudflared' εγκαταστάθηκε με επιτυχία.")
    print("Οι απαιτήσεις είναι ενημερωμένες.")

def generate_self_signed_cert(cert_path="cert.pem", key_path="key.pem"):
    if os.path.exists(cert_path) and os.path.exists(key_path): return
    print(f"Δημιουργία νέου πιστοποιητικού SSL στη διαδρομή {cert_path}...")
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
    import datetime
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with open(key_path, "wb") as f: f.write(key.private_bytes(encoding=Encoding.PEM, format=PrivateFormat.TraditionalOpenSSL, encryption_algorithm=NoEncryption()))
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"), x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),])
    cert = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(datetime.datetime.utcnow()).not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365)).add_extension(x509.SubjectAlternativeName([x509.DNSName(u"localhost")]), critical=False).sign(key, hashes.SHA256())
    with open(cert_path, "wb") as f: f.write(cert.public_bytes(Encoding.PEM))

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(('10.255.255.255', 1)); IP = s.getsockname()[0]
    except Exception: IP = '127.0.0.1'
    finally: s.close()
    return IP

def start_chat_server(secret_key, verbose_mode):
    cmd = [sys.executable, __file__, "--server", secret_key]
    if not verbose_mode:
        cmd.append("--quiet")
    return subprocess.Popen(cmd)

def wait_for_server(url, timeout=20):
    print("Αναμονή για την έναρξη του τοπικού διακομιστή...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, verify=False, timeout=1)
            if response.status_code == 200:
                print("Ο διακομιστής είναι σε λειτουργία.")
                return True
        except requests.ConnectionError: time.sleep(0.5)
    print("Σφάλμα: Ο τοπικός διακομιστής δεν ξεκίνησε εντός του χρονικού ορίου.")
    return False

def generate_and_print_links(secret_key):
    local_ip = get_local_ip()
    local_url = f"https://{local_ip}:5000"

    if not shutil.which("cloudflared"):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"✅ Το Fox Chat είναι τώρα ζωντανό!\n=================================================================\n🔑 Το μοναδικό σας Μυστικό Κλειδί (ΑΝΤΙΓΡΑΨΤΕ ΤΟ ΑΚΡΙΒΩΣ):\n   {secret_key}\n=================================================================\n🏠 Σύνδεσμος Εκτός Σύνδεσης (Hotspot/LAN): {local_url}\n\nΤο 'cloudflared' δεν είναι εγκατεστημένο, επομένως δεν δημιουργήθηκε Online Σύνδεσμος.\nΠατήστε Ctrl+C για να σταματήσετε τον διακομιστή.")
        return None

    cmd = ["cloudflared", "tunnel", "--url", "https://localhost:5000", "--no-tls-verify"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    print("\n🚀 Εκκίνηση του Cloudflare tunnel... παρακαλώ περιμένετε.")

    for line in iter(process.stdout.readline, ''):
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            online_url = match.group(0)
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"✅ Το Fox Chat είναι τώρα ζωντανό και ΑΣΦΑΛΕΣ!\n=================================================================\n🔑 Το μοναδικό σας Μυστικό Κλειδί (ΑΝΤΙΓΡΑΨΤΕ ΤΟ ΑΚΡΙΒΩΣ):\n   {secret_key}\n=================================================================\n🔗 Online Σύνδεσμος (Internet):     {online_url}\n🏠 Σύνδεσμος Εκτός Σύνδεσης (Hotspot/LAN): {local_url}\n\nΜοιραστείτε τον σύνδεσμο ΚΑΙ το Μυστικό Κλειδί με άλλους.\nΠατήστε Ctrl+C για να σταματήσετε τον διακομιστή.")
            return process
    print("\n⚠️ Δεν ήταν δυνατή η δημιουργία online συνδέσμου από το Cloudflare.")
    return process

if __name__ == '__main__' and "--server" not in sys.argv:
    VERBOSE_MODE = "--verbose" in sys.argv
    if VERBOSE_MODE: print("--- Εκτέλεση σε Αναλυτική Λειτουργία (Verbose Mode) ---")
    server_process, tunnel_process = None, None
    try:
        install_requirements()
        import requests
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        generate_self_signed_cert()
        SECRET_KEY = secrets.token_hex(16)
        server_process = start_chat_server(SECRET_KEY, VERBOSE_MODE)
        if wait_for_server("https://localhost:5000/health"):
            tunnel_process = generate_and_print_links(SECRET_KEY)
            if tunnel_process: tunnel_process.wait()
            else: server_process.wait()
        else:
            print("\nΚρίσιμο σφάλμα: Ο διακομιστής συνομιλίας απέτυχε να ξεκινήσει. Τερματισμός.")
    except KeyboardInterrupt: print("\nΤερματισμός των διακομιστών...")
    except Exception as e: print(f"\nΠροέκυψε ένα μη αναμενόμενο σφάλμα: {e}")
    finally:
        if tunnel_process and tunnel_process.poll() is None: tunnel_process.terminate()
        if server_process and server_process.poll() is None: server_process.terminate()
        sys.exit()

from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024
SECRET_KEY_SERVER = sys.argv[2] if len(sys.argv) > 2 else None
QUIET_MODE_SERVER = "--quiet" in sys.argv
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY_SERVER
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
connected_users = {}
VIDEO_ROOM = "global_video_room"

HTML = '''
<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Ασφαλής Συνομιλία Fox</title>
<script src="https://cdn.socket.io/4.6.1/socket.io.min.js"></script>
<style>
body,html{height:100%;margin:0;padding:0;font-family:sans-serif;background:#121212;color:#e0e0e0;overflow-x:hidden}
#login-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);display:flex;justify-content:center;align-items:center;z-index:1000}
#login-box{background:#1e1e1e;padding:25px;border-radius:8px;text-align:center;box-shadow:0 0 15px rgba(0,0,0,0.5)}
#login-box h2{margin-top:0;color:#9c27b0}
#login-box input{width:90%;padding:10px;margin:15px 0;background:#2c2c2c;border:1px solid #333;color:#e0e0e0;border-radius:4px}
#login-box button{width:95%;padding:10px;background:#4caf50;border:none;color:#fff;border-radius:4px;cursor:pointer}
#login-error{color:#f44336;margin-top:10px;height:1em}
#main-content{display:none}
.header{text-align:center;background:#1e1e1e;margin:0;padding:12px;font-size:1.5em;color:#9c27b0;border-bottom:1px solid #333}
#videos{display:none;padding:8px;background:#000;flex-wrap:wrap;gap:6px;width:100%;position:relative}
#videos.show{display:flex}
#videos video{display:none;width:calc(25% - 8px);max-width:120px;height:auto;object-fit:cover;border:2px solid #333;border-radius:6px;cursor:zoom-in}
#videos.show video{display:block}
#controls{display:flex;flex-wrap:wrap;justify-content:center;gap:8px;padding:12px;background:#1e1e1e;width:100%}#controls button{flex:1 1 100px;max-width:150px;min-width:80px;padding:10px;background:#2c2c2c;color:#fff;border:1px solid #333;border-radius:4px}#controls button:hover:not(:disabled){background:#3a3a3a}#controls button:disabled{opacity:.4}
#chat-container{padding:0 12px 100px;width:100%;position:relative}
#chat{width:100%;height:240px;overflow-y:auto;background:#181818;padding:12px;margin-top:8px;border-radius:4px}
.chat-message{margin-bottom:10px;display:flex;align-items:flex-start;gap:8px;word-break:break-word}
.chat-message strong{color:#4caf50;flex-shrink:0}
.message-content{flex-grow:1}
.message-actions{display:flex;gap:5px}
.message-actions button{background:none;border:none;cursor:pointer;font-size:1em;padding:2px 5px}
.file-link{cursor:pointer;color:#90caf9;text-decoration:underline}
.controls{position:fixed;bottom:0;left:0;right:0;display:flex;flex-wrap:wrap;gap:8px;padding:10px;background:#1e1e1e}
.controls input[type=text]{flex:1 1 200px;max-width:60%;min-width:120px;padding:10px;background:#2c2c2c;color:#e0e0e0;border:1px solid #333;border-radius:4px}
.controls button{flex:0 1 50px;padding:10px;background:#2c2c2c;border:1px solid #333;border-radius:4px}

/* --- UI & FEATURE STYLES --- */
#media-preview-overlay, #camera-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);display:flex;flex-direction:column;justify-content:center;align-items:center;z-index:3000}
#media-preview-overlay img, #media-preview-overlay video, #media-preview-overlay audio{max-width:90vw;max-height:80vh;border:2px solid #fff}
#media-preview-overlay .file-placeholder{font-size:5em;color:#fff}
#media-preview-controls, #camera-controls{display:flex;gap:15px;margin-top:15px;flex-wrap:wrap;justify-content:center}
#media-preview-controls button, #media-preview-controls a, #camera-controls button{background:#2c2c2c;color:#fff;border:1px solid #333;border-radius:4px;padding:10px 15px;cursor:pointer;text-decoration:none;font-size:1em}
#camera-preview{max-width:100%;max-height:80vh;border:2px solid #333;background:#000}
.edit-input{background:#3a3a3a;color:#e0e0e0;border:1px solid #555;border-radius:4px;width:80%}
.fullscreen-video{position:fixed !important;top:0;left:0;width:100vw;height:100vh;max-width:none !important;max-height:none !important;margin:0;background-color:#000;object-fit:contain;z-index:2000;border-radius:0 !important;border:none !important}
.close-fullscreen-btn{position:fixed;top:15px;right:15px;z-index:2001;background:rgba(0,0,0,0.5);color:#fff;border:1px solid #fff;border-radius:50%;width:40px;height:40px;font-size:24px;line-height:40px;text-align:center;cursor:pointer}
.secure-watermark{position:absolute;top:0;left:0;width:100%;height:100%;overflow:hidden;pointer-events:none;z-index:100}
.secure-watermark::before{content:attr(data-watermark);position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-30deg);font-size:3em;color:rgba(255,255,255,0.08);white-space:nowrap}
#video-controls-header{display:none;text-align:center;padding:5px;background-color:#1e1e1e}
#videos.show + #video-controls-header{display:block}
#toggleVideosBtn{background:none;border:none;color:#fff;font-size:1.5em;cursor:pointer}
#videos.collapsed{display:none}
</style>
</head>
<body>
<div id="login-overlay"><div id="login-box"><h2>Εισάγετε το Μυστικό Κλειδί</h2><input type="text" id="key-input" placeholder="Επικολλήστε το κλειδί εδώ..."><button id="connect-btn">Σύνδεση</button><p id="login-error"></p></div></div>
<div id="main-content"><h1 class="header">Ασφαλής Συνομιλία Fox</h1><div id="controls"><button id="joinBtn">Συμμετοχή στην Κλήση</button><button id="muteBtn" disabled>Σίγαση</button><button id="videoBtn" disabled>Κάμερα Off</button><button id="leaveBtn" disabled>Αποχώρηση</button><button id="switchCamBtn" disabled>🔄 Αλλαγή Κάμερας</button></div><div id="videos"><div class="secure-watermark"></div><video id="local" autoplay muted playsinline></video></div><div id="video-controls-header"><button id="toggleVideosBtn">▲</button></div><div id="chat-container"><div class="secure-watermark"></div><div id="chat"></div><div class="controls"><input id="message" type="text" placeholder="Πληκτρολογήστε ένα μήνυμα..." autocomplete="off"><button onclick="sendMessage()">Αποστολή</button><button id="recordButton" onclick="toggleRecording()">🎙️</button><button onclick="sendFile()">📄</button><button id="liveCameraBtn" onclick="openLiveCamera()">📸</button><input type="file" id="fileInput" style="display:none"></div></div></div>
<script>
document.addEventListener('DOMContentLoaded', () => {
    const keyInput = document.getElementById('key-input');
    const connectBtn = document.getElementById('connect-btn');
    const loginError = document.getElementById('login-error');
    const savedKey = sessionStorage.getItem("secretKey");
    if (savedKey) keyInput.value = savedKey;
    connectBtn.onclick = () => {
        const secretKey = keyInput.value.trim();
        if (secretKey) {
            loginError.textContent = 'Σύνδεση σε εξέλιξη...';
            sessionStorage.setItem("secretKey", secretKey);
            initializeChat(secretKey);
        } else {
            loginError.textContent = 'Το κλειδί δεν μπορεί να είναι κενό.';
        }
    };
});

function initializeChat(secretKey) {
    const socket = io({ auth: { token: secretKey } });
    socket.on('connect_error', () => {
        document.getElementById('login-error').textContent = 'Μη έγκυρο Κλειδί. Παρακαλώ δοκιμάστε ξανά.';
        sessionStorage.removeItem("secretKey");
    });
    socket.on('connect', () => {
        document.getElementById('login-overlay').style.display = 'none';
        document.getElementById('main-content').style.display = 'block';
        let username = localStorage.getItem("username");
        if (!username) {
            let promptedName = prompt("Εισάγετε το όνομα χρήστη σας:");
            username = promptedName ? promptedName.trim() : "Χρήστης" + Math.floor(Math.random() * 1000);
            localStorage.setItem("username", username);
        }
        document.querySelectorAll('.secure-watermark').forEach(el => el.setAttribute('data-watermark', username));
        socket.emit("join", username);
    });

    const MAX_FILE_SIZE = 25 * 1024 * 1024;
    const fileInput = document.getElementById('fileInput');
    const chat = document.getElementById('chat');
    const messageInput = document.getElementById('message');

    function handleFileSelection(file) {
        if (!file) return;
        if (file.size > MAX_FILE_SIZE) {
            alert(`Το αρχείο είναι πολύ μεγάλο.`);
            return;
        }
        let reader = new FileReader();
        reader.onload = () => emitFile(reader.result, file.type, file.name);
        reader.readAsDataURL(file);
    };
    fileInput.addEventListener('change', e => { handleFileSelection(e.target.files[0]); e.target.value = ''; });

    function generateId() { return 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5); };
    window.sendMessage = () => {
        const text = messageInput.value.trim();
        if (!text) return;
        socket.emit("message", { id: generateId(), username: localStorage.getItem("username"), message: text });
        messageInput.value = '';
    };
    messageInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendMessage(); });
    
    let mediaRecorder, recordedChunks = [], isRecording = false;
    window.toggleRecording = () => {
        let recordButton = document.getElementById("recordButton");
        if (isRecording) {
            mediaRecorder.stop();
        } else {
            navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
                isRecording = true;
                recordButton.textContent = '🛑';
                recordedChunks = [];
                mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
                mediaRecorder.ondataavailable = e => { if (e.data.size > 0) recordedChunks.push(e.data); };
                mediaRecorder.onstop = () => {
                    isRecording = false;
                    recordButton.textContent = '🎙️';
                    stream.getTracks().forEach(track => track.stop());
                    const blob = new Blob(recordedChunks, { type: 'audio/webm' });
                    const reader = new FileReader();
                    reader.onloadend = () => socket.emit("message", { id: generateId(), username: localStorage.getItem("username"), message: reader.result, fileType: blob.type, filename: `voice-message.webm` });
                    reader.readAsDataURL(blob);
                };
                mediaRecorder.start();
            }).catch(err => alert("Η πρόσβαση στο μικρόφωνο απορρίφθηκε."));
        }
    };
    
    window.sendFile = () => fileInput.click();
    
    function emitFile(dataURL, type, name) {
        socket.emit("message", { id: generateId(), username: localStorage.getItem("username"), message: dataURL, fileType: type, filename: name });
    };

    function showMediaPreview(data) {
        let existingPreview = document.getElementById('media-preview-overlay');
        if (existingPreview) existingPreview.remove();
        const overlay = document.createElement('div');
        overlay.id = 'media-preview-overlay';
        let previewContent;
        if (data.fileType.startsWith('image/')) {
            previewContent = document.createElement('img');
        } else if (data.fileType.startsWith('video/')) {
            previewContent = document.createElement('video');
            previewContent.controls = true;
            previewContent.autoplay = true;
        } else if (data.fileType.startsWith('audio/')) {
            previewContent = document.createElement('audio');
            previewContent.controls = true;
            previewContent.autoplay = true;
        } else {
            previewContent = document.createElement('div');
            previewContent.className = 'file-placeholder';
            previewContent.textContent = '📄';
        }
        if (previewContent.src !== undefined) previewContent.src = data.message;
        const controls = document.createElement('div');
        controls.id = 'media-preview-controls';
        const closeBtn = document.createElement('button');
        closeBtn.textContent = 'Κλείσιμο (X)';
        closeBtn.onclick = () => overlay.remove();
        const downloadLink = document.createElement('a');
        downloadLink.textContent = 'Λήψη';
        downloadLink.href = data.message;
        downloadLink.download = data.filename;
        controls.appendChild(downloadLink);
        if (data.username === localStorage.getItem("username")) {
            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = 'Διαγραφή';
            deleteBtn.onclick = () => { socket.emit('delete_message', { id: data.id }); overlay.remove(); };
            controls.appendChild(deleteBtn);
        }
        controls.appendChild(closeBtn);
        overlay.appendChild(previewContent);
        overlay.appendChild(controls);
        document.body.appendChild(overlay);
    }
    
    let liveCameraStream;
    let liveCameraFacingMode = 'user';
    window.openLiveCamera = () => {
        const overlay = document.createElement('div');
        overlay.id = 'camera-overlay';
        const video = document.createElement('video');
        video.id = 'camera-preview';
        video.autoplay = true;
        const controls = document.createElement('div');
        controls.id = 'camera-controls';
        const captureBtn = document.createElement('button');
        captureBtn.textContent = 'Λήψη Φωτογραφίας';
        const switchBtn = document.createElement('button');
        switchBtn.textContent = 'Αλλαγή Κάμερας';
        const closeBtn = document.createElement('button');
        closeBtn.textContent = 'Κλείσιμο';
        
        const startStream = (facingMode) => {
            if (liveCameraStream) {
                liveCameraStream.getTracks().forEach(track => track.stop());
            }
            navigator.mediaDevices.getUserMedia({ video: { facingMode: facingMode } })
                .then(stream => {
                    liveCameraStream = stream;
                    video.srcObject = stream;
                })
                .catch(err => {
                    alert('Δεν ήταν δυνατή η πρόσβαση στην κάμερα. Ελέγξτε τις άδειες.');
                    overlay.remove();
                });
        };
        
        closeBtn.onclick = () => {
            if (liveCameraStream) liveCameraStream.getTracks().forEach(track => track.stop());
            overlay.remove();
        };
        switchBtn.onclick = () => {
            liveCameraFacingMode = liveCameraFacingMode === 'user' ? 'environment' : 'user';
            startStream(liveCameraFacingMode);
        };
        captureBtn.onclick = () => {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
            const filename = `capture-${Date.now()}.jpg`;
            emitFile(dataUrl, 'image/jpeg', filename);
            closeBtn.onclick();
        };
        
        controls.appendChild(captureBtn);
        controls.appendChild(switchBtn);
        controls.appendChild(closeBtn);
        overlay.appendChild(video);
        overlay.appendChild(controls);
        document.body.appendChild(overlay);
        startStream(liveCameraFacingMode);
    };

    socket.on("message", data => {
        const div = document.createElement('div');
        div.className = 'chat-message';
        div.id = data.id;
        const strong = document.createElement('strong');
        strong.textContent = `${data.username}:`;
        const content = document.createElement('div');
        content.className = 'message-content';
        content.id = `content-${data.id}`;
        
        if (data.filename === 'voice-message.webm') {
            const audio = document.createElement('audio');
            audio.src = data.message;
            audio.controls = true;
            audio.setAttribute('controlsList', 'nodownload');
            content.appendChild(audio);
        } else if (data.fileType) {
            const fileLink = document.createElement('span');
            fileLink.className = 'file-link';
            fileLink.textContent = data.filename;
            fileLink.onclick = () => showMediaPreview(data);
            content.appendChild(fileLink);
        } else {
            content.textContent = data.message;
        }

        div.appendChild(strong);
        div.appendChild(content);

        if (data.username === localStorage.getItem("username") && data.username !== 'System') {
            const actions = document.createElement('div');
            actions.className = 'message-actions';
            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = '❌';
            deleteBtn.title = 'Διαγραφή';
            deleteBtn.onclick = () => socket.emit('delete_message', { id: data.id });
            if (!data.fileType) {
                const editBtn = document.createElement('button');
                editBtn.textContent = '📝';
                editBtn.title = 'Επεξεργασία';
                editBtn.onclick = () => toggleEdit(data.id, data.message);
                actions.appendChild(editBtn);
            }
            actions.appendChild(deleteBtn);
            div.appendChild(actions);
        }
        chat.appendChild(div);
        chat.scrollTop = chat.scrollHeight;
    });

    socket.on('delete_message', data => {
        const element = document.getElementById(data.id);
        if (element) element.remove();
    });

    function toggleEdit(id, currentText) {
        const contentDiv = document.getElementById(`content-${id}`);
        const isEditing = contentDiv.querySelector('input');
        if (isEditing) {
            contentDiv.textContent = currentText;
        } else {
            contentDiv.innerHTML = '';
            const input = document.createElement('input');
            input.type = 'text';
            input.value = currentText;
            input.className = 'edit-input';
            const saveBtn = document.createElement('button');
            saveBtn.textContent = 'Αποθήκευση';
            saveBtn.onclick = () => {
                const newText = input.value.trim();
                if (newText && newText !== currentText) {
                    socket.emit('edit_message', { id: id, new_message: newText });
                } else {
                    contentDiv.textContent = currentText;
                }
            };
            input.onkeydown = (e) => { if(e.key === 'Enter') saveBtn.click(); if(e.key === 'Escape') contentDiv.textContent = currentText; };
            contentDiv.appendChild(input);
            contentDiv.appendChild(saveBtn);
            input.focus();
        }
    }

    socket.on('message_edited', data => {
        const contentDiv = document.getElementById(`content-${data.id}`);
        if(contentDiv) contentDiv.textContent = data.new_message;
    });
    
    const videos = document.getElementById('videos'), localVideo = document.getElementById('local');
    const joinBtn = document.getElementById('joinBtn'), muteBtn = document.getElementById('muteBtn');
    const videoBtn = document.getElementById('videoBtn'), leaveBtn = document.getElementById('leaveBtn');
    const switchCamBtn = document.getElementById('switchCamBtn');
    let localStream, peerConnections = {}, isMuted = false, videoOff = false, currentFacingMode = 'user';
    
    let fullscreenState = { element: null, parent: null, nextSibling: null };
    function toggleFullscreen(videoElement) {
        if (fullscreenState.element) {
            fullscreenState.parent.insertBefore(fullscreenState.element, fullscreenState.nextSibling);
            fullscreenState.element.classList.remove('fullscreen-video');
            document.querySelector('.close-fullscreen-btn')?.remove();
            fullscreenState = { element: null, parent: null, nextSibling: null };
            return;
        }
        if (videoElement) {
            fullscreenState.element = videoElement;
            fullscreenState.parent = videoElement.parentNode;
            fullscreenState.nextSibling = videoElement.nextSibling;
            document.body.appendChild(videoElement);
            videoElement.classList.add('fullscreen-video');
            const closeBtn = document.createElement('button');
            closeBtn.textContent = 'X';
            closeBtn.className = 'close-fullscreen-btn';
            closeBtn.onclick = () => toggleFullscreen(null);
            document.body.appendChild(closeBtn);
        }
    }
    
    const addFullscreenListener = (videoElement) => {
        videoElement.onclick = () => {
            if (!document.querySelector('.fullscreen-video')) {
                 toggleFullscreen(videoElement);
            }
        };
    };
    addFullscreenListener(localVideo);

    const toggleVideosBtn = document.getElementById('toggleVideosBtn');
    toggleVideosBtn.onclick = () => {
        videos.classList.toggle('collapsed');
        toggleVideosBtn.textContent = videos.classList.contains('collapsed') ? '▼' : '▲';
    };

    const toggleCallButtons = (inCall) => {
        joinBtn.disabled = inCall;
        [muteBtn, videoBtn, leaveBtn, switchCamBtn].forEach(b => b.disabled = !inCall);
    };
    joinBtn.onclick = async () => {
        try {
            localStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: currentFacingMode }, audio: true });
            localVideo.srcObject = localStream;
            localVideo.play();
            videos.classList.add('show');
            toggleCallButtons(true);
            socket.emit('join-room');
        } catch (err) {
            alert('Δεν ήταν δυνατή η έναρξη του βίντεο. Ελέγξτε τις άδειες.');
        }
    };
    leaveBtn.onclick = () => {
        socket.emit('leave-room');
        for (let id in peerConnections) peerConnections[id].close();
        peerConnections = {};
        if (localStream) localStream.getTracks().forEach(track => track.stop());
        videos.classList.remove('show');
        document.querySelectorAll('#videos video:not(#local)').forEach(v => v.remove());
        if (fullscreenState.element) toggleFullscreen(null);
        toggleCallButtons(false);
    };
    switchCamBtn.onclick = async () => {
        if (!localStream) return;
        currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
        try {
            localStream.getTracks().forEach(track => track.stop());
            const newStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: currentFacingMode }, audio: true });
            localStream = newStream;
            localVideo.srcObject = localStream;
            for (const id in peerConnections) {
                const sender = peerConnections[id].getSenders().find(s => s.track && s.track.kind === 'video');
                if (sender) sender.replaceTrack(newStream.getVideoTracks()[0]);
            }
        } catch (err) {
            alert('Αποτυχία αλλαγής κάμερας.');
            currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
        }
    };
    muteBtn.onclick = () => {
        isMuted = !isMuted;
        localStream.getAudioTracks()[0].enabled = !isMuted;
        muteBtn.textContent = isMuted ? 'Κατάργηση Σίγασης' : 'Σίγαση';
    };
    videoBtn.onclick = () => {
        videoOff = !videoOff;
        localStream.getVideoTracks()[0].enabled = !videoOff;
        videoBtn.textContent = videoOff ? 'Κάμερα On' : 'Κάμερα Off';
    };
    socket.on('all-users', data => {
        data.users.forEach(id => {
            if (id !== socket.id) createPeerConnection(id, true);
        });
    });
    socket.on('user-joined', data => {
        if (data.sid !== socket.id) createPeerConnection(data.sid, false);
    });
    socket.on('user-left', data => {
        if (peerConnections[data.sid]) {
            peerConnections[data.sid].close();
            delete peerConnections[data.sid];
            let vid = document.getElementById(`video_${data.sid}`);
            if (vid) {
                if(fullscreenState.element === vid) toggleFullscreen(null);
                vid.remove();
            }
        }
    });
    socket.on('signal', async data => {
        let pc = peerConnections[data.from] || createPeerConnection(data.from, false);
        if (data.data.sdp) {
            await pc.setRemoteDescription(new RTCSessionDescription(data.data.sdp));
            if (data.data.sdp.type === 'offer') {
                const answer = await pc.createAnswer();
                await pc.setLocalDescription(answer);
                socket.emit('signal', { to: data.from, data: { sdp: pc.localDescription } });
            }
        } else if (data.data.candidate) {
            await pc.addIceCandidate(new RTCIceCandidate(data.data.candidate));
        }
    });
    function createPeerConnection(id, isOfferer) {
        const pc = new RTCPeerConnection({ iceServers: [{ urls: "stun:stun.l.google.com:19302" }] });
        peerConnections[id] = pc;
        pc.onicecandidate = e => {
            if (e.candidate) socket.emit('signal', { to: id, data: { candidate: e.candidate } });
        };
        pc.ontrack = e => {
            let vid = document.getElementById(`video_${id}`);
            if (!vid) {
                vid = document.createElement('video');
                vid.id = `video_${id}`;
                vid.autoplay = true;
                vid.playsInline = true;
                addFullscreenListener(vid);
                videos.appendChild(vid);
            }
            vid.srcObject = e.streams[0];
        };
        if (localStream) localStream.getTracks().forEach(track => pc.addTrack(track, localStream));
        if (isOfferer) {
            pc.createOffer()
              .then(offer => pc.setLocalDescription(offer))
              .then(() => socket.emit('signal', { to: id, data: { sdp: pc.localDescription } }));
        }
        return pc;
    }
}
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/health')
def health_check():
    return "OK", 200

@socketio.on('connect')
def handle_connect(auth):
    token = auth.get('token') if auth else None
    if token != SECRET_KEY_SERVER:
        return False
    connected_users[request.sid] = {'username': 'pending'}
    return True

@socketio.on("join")
def handle_join(username):
    safe_username = html.escape(username)
    if request.sid in connected_users:
        connected_users[request.sid]['username'] = safe_username
    emit('message', {'id': f'join_{int(time.time())}','username': 'System','message': f'Ο/Η {safe_username} συνδέθηκε.'}, broadcast=True)

@socketio.on("message")
def handle_message(data):
    if not isinstance(data, dict): return
    data['username'] = html.escape(data.get('username', 'Anonymous'))
    if data.get('fileType'):
        try:
            header, encoded = data['message'].split(",", 1)
            b64decode(encoded)
        except (ValueError, binascii.Error): return
        data['filename'] = html.escape(data.get('filename', 'file'))
        data['fileType'] = html.escape(data.get('fileType', 'application/octet-stream'))
    else:
        data['message'] = html.escape(data.get('message', ''))
    emit("message", data, broadcast=True)

@socketio.on("delete_message")
def handle_delete(data):
    emit("delete_message", {'id': data.get('id')}, broadcast=True)

@socketio.on("edit_message")
def handle_edit(data):
    if not isinstance(data, dict) or 'id' not in data or 'new_message' not in data:
        return
    new_message_safe = html.escape(data['new_message'])
    emit("message_edited", {'id': data['id'], 'new_message': new_message_safe}, broadcast=True)

@socketio.on("join-room")
def join_video():
    join_room(VIDEO_ROOM)
    users_in_room = [sid for sid in socketio.server.manager.rooms['/'].get(VIDEO_ROOM, []) if sid != request.sid]
    emit("all-users", {"users": users_in_room})

@socketio.on("leave-room")
def leave_video():
    leave_room(VIDEO_ROOM)
    emit("user-left", {"sid": request.sid}, to=VIDEO_ROOM, include_self=False)

@socketio.on("signal")
def signal(data):
    target_sid = data.get('to')
    if target_sid in connected_users:
        emit("signal", {"from": request.sid, "data": data['data']}, to=target_sid)

@socketio.on("disconnect")
def on_disconnect():
    leave_room(VIDEO_ROOM)
    emit("user-left", {"sid": request.sid}, to=VIDEO_ROOM)
    if request.sid in connected_users: del connected_users[request.sid]

if __name__ == '__main__' and "--server" in sys.argv:
    if not SECRET_KEY_SERVER:
        print("ΚΡΙΣΙΜΟ ΣΦΑΛΜΑ: Ο διακομιστής ξεκίνησε χωρίς μυστικό κλειδί.")
        sys.exit(1)
    if QUIET_MODE_SERVER:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
    else:
        print(f"Εκκίνηση διακομιστή με κλειδί: {SECRET_KEY_SERVER}")
    socketio.run(app, host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'key.pem'))