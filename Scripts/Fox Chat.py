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

# --- Added for robust server checking ---
try:
    import requests
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

# --- Dependency Management ---
def install_requirements():
    """Installs required packages securely."""
    print("Checking and installing requirements...")
    try:
        requirements = ["flask", "flask_socketio", "requests", "pyopenssl", "cryptography"]
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + requirements,
            check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as e:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("ERROR: Failed to install required Python packages.")
        print(f"pip stderr:\n{e.stderr}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        sys.exit(1)

    if not shutil.which("cloudflared"):
        print("\n--- 'cloudflared' Installation Required ---")
        if "linux" in sys.platform and os.path.exists("/data/data/com.termux"):
            os.system("pkg update -y > /dev/null 2>&1 && pkg install cloudflared -y > /dev/null 2>&1")
        else:
            print("Please install 'cloudflared' using your system's package manager (e.g., brew, apt, etc.).")
        
        if not shutil.which("cloudflared"):
            print("WARNING: 'cloudflared' not found. Only the Offline Link will be available.")
        else:
            print("'cloudflared' installed successfully.")
    print("Requirements are up to date.")

def generate_self_signed_cert(cert_path="cert.pem", key_path="key.pem"):
    """Generates a self-signed SSL certificate if one doesn't exist."""
    if os.path.exists(cert_path) and os.path.exists(key_path): return
    print(f"Generating new SSL certificate at {cert_path}...")
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
    """Finds the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(('10.255.255.255', 1)); IP = s.getsockname()[0]
    except Exception: IP = '127.0.0.1'
    finally: s.close()
    return IP

def start_chat_server(secret_key, verbose_mode):
    """Starts the secure Flask Chat server in the background."""
    cmd = [sys.executable, __file__, "--server", secret_key]
    if not verbose_mode:
        cmd.append("--quiet")
    return subprocess.Popen(cmd)

def wait_for_server(url, timeout=20):
    """Polls the server's health check endpoint until it's responsive."""
    print("Waiting for local server to start...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, verify=False, timeout=1)
            if response.status_code == 200:
                print("Server is up and running.")
                return True
        except requests.ConnectionError: time.sleep(0.5)
    print("Error: Local server did not start within the timeout period.")
    return False

def generate_and_print_links(secret_key):
    """Starts cloudflared and prints secure links."""
    local_ip = get_local_ip()
    local_url = f"https://{local_ip}:5000"

    if not shutil.which("cloudflared"):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("✅ Fox Chat is now live!")
        print("=================================================================")
        print(f"🔑 Your one-time Secret Key (COPY THIS EXACTLY):")
        print(f"   {secret_key}")
        print("=================================================================")
        print(f"🏠 Offline Link (Hotspot/LAN): {local_url}")
        print("\n'cloudflared' not installed, so no Online Link was generated.")
        print("Press Ctrl+C to stop the server.")
        return None

    cmd = ["cloudflared", "tunnel", "--url", "https://localhost:5000", "--no-tls-verify"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    print("\n🚀 Starting Cloudflare tunnel... please wait.")
    
    for line in iter(process.stdout.readline, ''):
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            online_url = match.group(0)
            os.system('cls' if os.name == 'nt' else 'clear')
            print("✅ Fox Chat is now live and SECURED!")
            print("=================================================================")
            print(f"🔑 Your one-time Secret Key (COPY THIS EXACTLY):")
            print(f"   {secret_key}")
            print("=================================================================")
            print(f"🔗 Online Link (Internet):     {online_url}")
            print(f"🏠 Offline Link (Hotspot/LAN): {local_url}")
            print("\nShare the link AND the Secret Key with others.")
            print("Press Ctrl+C to stop the server.")
            return process
    print("\n⚠️ Could not generate an online link from Cloudflare.")
    return process

# --- Main Launcher Block ---
if __name__ == '__main__' and "--server" not in sys.argv:
    # --- FIXED: Quiet mode is now default. Use --verbose to see logs. ---
    VERBOSE_MODE = "--verbose" in sys.argv
    if VERBOSE_MODE:
        print("--- Running in Verbose Mode ---")
        
    server_process = None
    tunnel_process = None
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
            print("\nFatal: Chat server failed to start. Exiting.")
            
    except KeyboardInterrupt: print("\nShutting down servers...")
    except Exception as e: print(f"\nAn unexpected error occurred: {e}")
    finally:
        if tunnel_process and tunnel_process.poll() is None: tunnel_process.terminate()
        if server_process and server_process.poll() is None: server_process.terminate()
        sys.exit()

# ---------------------------------------
# SECURE FLASK FOX CHAT SERVER
# ---------------------------------------
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import time
import logging

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024
SECRET_KEY_SERVER = sys.argv[2] if len(sys.argv) > 2 else None
QUIET_MODE_SERVER = "--quiet" in sys.argv

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY_SERVER 
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Secure Fox Chat</title>
<script src="https://cdn.socket.io/4.6.1/socket.io.min.js"></script>
<style>
body,html{height:100%;margin:0;padding:0;font-family:sans-serif;background:#121212;color:#e0e0e0;overflow-x:hidden}
#login-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);display:flex;justify-content:center;align-items:center;z-index:1000}
#login-box{background:#1e1e1e;padding:25px;border-radius:8px;text-align:center;box-shadow:0 0 15px rgba(0,0,0,0.5)}
#login-box h2{margin-top:0;color:#9c27b0}
#login-box input{width:90%;padding:10px;margin:15px 0;background:#2c2c2c;border:1px solid #333;color:#e0e0e0;border-radius:4px}
#login-box button{width:95%;padding:10px;background:#4caf50;border:none;color:#fff;border-radius:4px;cursor:pointer}
#login-box button:hover{background:#5cb85c}
#login-error{color:#f44336;margin-top:10px;height:1em}
#main-content{display:none}
.header{text-align:center;background:#1e1e1e;margin:0;padding:12px;font-size:1.5em;color:#9c27b0;border-bottom:1px solid #333}
#videos{display:none;padding:8px;background:#000;flex-wrap:wrap;gap:6px;width:100%}
#videos.show{display:flex}
#videos video{display:none;width:calc(25% - 8px);max-width:120px;height:auto;object-fit:cover;border:2px solid #333;border-radius:6px}
#videos.show video{display:block}
#controls{display:flex;flex-wrap:wrap;justify-content:center;gap:8px;padding:12px;background:#1e1e1e;width:100%}#controls button{flex:1 1 100px;max-width:150px;min-width:80px;padding:10px;background:#2c2c2c;color:#fff;border:1px solid #333;border-radius:4px}#controls button:hover:not(:disabled){background:#3a3a3a}#controls button:disabled{opacity:.4}
#chat-container{padding:0 12px 100px;width:100%}#chat{width:100%;height:240px;overflow-y:auto;background:#181818;padding:12px;margin-top:8px;border-radius:4px}.chat-message{margin-bottom:10px;position:relative;word-break:break-word}.chat-message strong{color:#4caf50}.delete-btn{position:absolute;top:2px;right:2px;background:0 0;color:#f44336;cursor:pointer}.chat-message img,.chat-message video{max-width:80px;max-height:80px;cursor:pointer;border:1px solid #333;border-radius:4px}.chat-message img.expanded,.chat-message video.expanded{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);max-width:90vw;max-height:90vh;z-index:200}.filename{display:block;margin-top:4px;color:#ccc}.download-link{margin-left:8px;color:#90caf9}
.controls{position:fixed;bottom:0;left:0;right:0;display:flex;flex-wrap:wrap;gap:8px;padding:10px;background:#1e1e1e}.controls input[type=text]{flex:1 1 200px;max-width:60%;min-width:120px;padding:10px;background:#2c2c2c;color:#e0e0e0;border:1px solid #333;border-radius:4px}.controls button{flex:0 1 50px;padding:10px;background:#2c2c2c;border:1px solid #333;border-radius:4px}
</style>
</head>
<body>
<div id="login-overlay"><div id="login-box"><h2>Enter Secret Key</h2><input type="text" id="key-input" placeholder="Paste key here..."><button id="connect-btn">Connect</button><p id="login-error"></p></div></div>
<div id="main-content"><h1 class="header">Secure Fox Chat</h1><div id="videos"><video id="local" autoplay muted playsinline></video></div><div id="controls"><button id="joinBtn">Join Call</button><button id="muteBtn" disabled>Mute</button><button id="videoBtn" disabled>Cam Off</button><button id="leaveBtn" disabled>Leave</button><button id="switchCamBtn" disabled>🔄 Switch Cam</button></div><div id="chat-container"><div id="chat"></div><div class="controls"><input id="message" type="text" placeholder="Type a message..." autocomplete="off"><button onclick="sendMessage()">Send</button><button id="recordButton" onclick="toggleRecording()">🎙️</button><button onclick="sendFile()">📄</button><button onclick="openCamera()">📷</button><input type="file" id="fileInput" style="display:none"><input type="file" id="cameraInput" accept="image/*,video/*" capture style="display:none"></div></div></div>
<script>
document.addEventListener('DOMContentLoaded', () => {
    const keyInput = document.getElementById('key-input');
    const connectBtn = document.getElementById('connect-btn');
    const loginError = document.getElementById('login-error');
    const savedKey = sessionStorage.getItem("secretKey");
    if (savedKey) { keyInput.value = savedKey; }
    connectBtn.onclick = () => {
        const secretKey = keyInput.value.trim();
        if (secretKey) {
            loginError.textContent = 'Connecting...';
            sessionStorage.setItem("secretKey", secretKey);
            initializeChat(secretKey);
        } else {
            loginError.textContent = 'Key cannot be empty.';
        }
    };
});

function initializeChat(secretKey) {
    const socket = io({ auth: { token: secretKey } });
    socket.on('connect_error', (err) => {
        document.getElementById('login-error').textContent = 'Invalid Key. Please try again.';
        sessionStorage.removeItem("secretKey");
    });
    socket.on('connect', () => {
        document.getElementById('login-overlay').style.display = 'none';
        document.getElementById('main-content').style.display = 'block';
        let username = localStorage.getItem("username");
        if (!username) {
            do { username = prompt("Enter your username:"); } while (!username);
            localStorage.setItem("username", username);
        }
        socket.emit("join", username);
    });
    const MAX_FILE_SIZE = 25 * 1024 * 1024;
    function handleFileSelection(file) { if (!file || file.size > MAX_FILE_SIZE) return; if(file.type.startsWith('image/')){compressImage(file,dataURL=>emitFile(dataURL,'image',file.name))}else{let rd=new FileReader();rd.onload=()=>emitFile(rd.result,file.type.startsWith('video/')?'video':'file',file.name);rd.readAsDataURL(file)}};
    fileInput.addEventListener('change', e=>{handleFileSelection(e.target.files[0]);e.target.value=''});
    cameraInput.addEventListener('change', e=>{handleFileSelection(e.target.files[0]);e.target.value=''});
    function genId(){return'msg_'+Date.now()+'_'+Math.random().toString(36).substr(2,5)};
    window.sendMessage = ()=>{let txt=document.getElementById("message").value.trim();if(!txt)return;socket.emit("message",{id:genId(),username:localStorage.getItem("username"),message:txt});document.getElementById("message").value=''};
    let mediaRecorder,recordedChunks=[],isRecording=!1;
    window.toggleRecording=()=>{let btn=document.getElementById("recordButton");if(isRecording){mediaRecorder.stop();isRecording=!1;btn.textContent='🎙️'}else{navigator.mediaDevices.getUserMedia({audio:!0}).then(stream=>{recordedChunks=[];mediaRecorder=new MediaRecorder(stream);mediaRecorder.ondataavailable=e=>{if(e.data.size)recordedChunks.push(e.data)};mediaRecorder.onstop=()=>{let blob=new Blob(recordedChunks,{type:'audio/mp4'});let reader=new FileReader();reader.onloadend=()=>socket.emit("message",{id:genId(),username:localStorage.getItem("username"),message:reader.result,isVoice:!0});reader.readAsDataURL(blob)};mediaRecorder.start();isRecording=!0;btn.textContent='🛑'}).catch(_=>alert("Mic access denied"))}};
    function compressImage(file,cb){let r=new FileReader();r.onload=()=>{let img=new Image();img.onload=()=>{let MAX=800,scale=Math.min(MAX/img.width,1),c=document.createElement('canvas');c.width=img.width*scale;c.height=img.height*scale;c.getContext('2d').drawImage(img,0,0,c.width,c.height);cb(c.toDataURL(file.type,0.7))};img.src=r.result};r.readAsDataURL(file)};
    window.sendFile=()=>fileInput.click();window.openCamera=()=>cameraInput.click();
    function emitFile(dataURL,type,name){socket.emit("message",{id:genId(),username:localStorage.getItem("username"),message:dataURL,isFile:!0,fileType:type,filename:name})};
    socket.on("message",d=>{let c=document.getElementById('chat'),div=document.createElement('div');div.className='chat-message';div.id=d.id;div.innerHTML=`<strong>${d.username}:</strong> `;if(d.isVoice){let a=document.createElement('audio');a.controls=!0;a.src=d.message;div.appendChild(a)}else if(d.isFile){if(d.fileType==='image'||d.fileType==='video'){let el=document.createElement(d.fileType);el.src=d.message;el.onclick=()=>el.classList.toggle('expanded');div.appendChild(el)}let fn=document.createElement('span');fn.className='filename';fn.textContent=d.filename;div.appendChild(fn);let dl=document.createElement('a');dl.href=d.message;dl.download=d.filename;dl.textContent='⬇️';dl.className='download-link';div.appendChild(dl)}else{div.innerHTML+=d.message}if(d.username===localStorage.getItem("username")){let btn=document.createElement('button');btn.className='delete-btn';btn.textContent='❌';btn.onclick=()=>socket.emit('delete_message',{id:d.id});div.appendChild(btn)}c.appendChild(div);c.scrollTop=c.scrollHeight});
    socket.on('delete_message',d=>{let e=document.getElementById(d.id);if(e)e.remove()});
    const videos=document.getElementById('videos'),localVideo=document.getElementById('local'),joinBtn=document.getElementById('joinBtn'),muteBtn=document.getElementById('muteBtn'),videoBtn=document.getElementById('videoBtn'),leaveBtn=document.getElementById('leaveBtn'),switchCamBtn=document.getElementById('switchCamBtn');let localStream,peerConnections={},isMuted=!1,videoOff=!1,currentFacingMode='user';
    joinBtn.onclick=async()=>{try{localStream=await navigator.mediaDevices.getUserMedia({video:{facingMode:currentFacingMode},audio:!0});localVideo.srcObject=localStream;localVideo.play();videos.classList.add('show');joinBtn.disabled=!0;[muteBtn,videoBtn,leaveBtn,switchCamBtn].forEach(b=>b.disabled=!1);socket.emit('join-room')}catch(err){alert('Could not start video. Please check camera permissions.')}};
    leaveBtn.onclick=()=>{socket.emit('leave-room');for(let id in peerConnections){peerConnections[id].close()}peerConnections={};if(localStream){localStream.getTracks().forEach(track=>track.stop())}videos.classList.remove('show');joinBtn.disabled=!1;[muteBtn,videoBtn,leaveBtn,switchCamBtn].forEach(b=>b.disabled=!0)};
    switchCamBtn.onclick=async()=>{if(!localStream)return;currentFacingMode=currentFacingMode==='user'?'environment':'user';try{localStream.getTracks().forEach(track=>track.stop());const newStream=await navigator.mediaDevices.getUserMedia({video:{facingMode:currentFacingMode},audio:!0});localStream=newStream;localVideo.srcObject=localStream;const newVideoTrack=newStream.getVideoTracks()[0];for(const id in peerConnections){const sender=peerConnections[id].getSenders().find(s=>s.track&&s.track.kind==='video');if(sender){sender.replaceTrack(newVideoTrack)}}}catch(err){alert('Failed to switch camera. Your device may not have a second camera or permission was denied.');currentFacingMode=currentFacingMode==='user'?'environment':'user'}};
    muteBtn.onclick=()=>{isMuted=!isMuted;localStream.getAudioTracks()[0].enabled=!isMuted;muteBtn.textContent=isMuted?'Unmute':'Mute'};
    videoBtn.onclick=()=>{videoOff=!videoOff;localStream.getVideoTracks()[0].enabled=!videoOff;videoBtn.textContent=videoOff?'Cam On':'Cam Off'};
    socket.on('all-users',d=>{d.users.forEach(id=>{if(id!==socket.id)createPeerConnection(id,!0)})});
    socket.on('user-joined',d=>{if(d.sid!==socket.id)createPeerConnection(d.sid,!1)});
    socket.on('user-left',d=>{if(peerConnections[d.sid]){peerConnections[d.sid].close();delete peerConnections[d.sid];let vid=document.getElementById(`video_${d.sid}`);if(vid)vid.remove()}});
    socket.on('signal',async d=>{let pc=peerConnections[d.from]||createPeerConnection(d.from,!1);if(d.data.sdp){await pc.setRemoteDescription(new RTCSessionDescription(d.data.sdp));if(d.data.sdp.type==='offer'){const answer=await pc.createAnswer();await pc.setLocalDescription(answer);socket.emit('signal',{to:d.from,data:{sdp:pc.localDescription}})}}else if(d.data.candidate){await pc.addIceCandidate(new RTCIceCandidate(d.data.candidate))}});
    function createPeerConnection(id,isOfferer){const pc=new RTCPeerConnection({iceServers:[{urls:"stun:stun.l.google.com:19302"}]});peerConnections[id]=pc;pc.onicecandidate=e=>{if(e.candidate)socket.emit('signal',{to:id,data:{candidate:e.candidate}})};pc.ontrack=e=>{let vid=document.getElementById(`video_${id}`);if(!vid){vid=document.createElement('video');vid.id=`video_${id}`;vid.autoplay=!0;vid.playsInline=!0;videos.appendChild(vid)}vid.srcObject=e.streams[0]};if(localStream)localStream.getTracks().forEach(track=>pc.addTrack(track,localStream));if(isOfferer){pc.createOffer().then(offer=>pc.setLocalDescription(offer)).then(()=>socket.emit('signal',{to:id,data:{sdp:pc.localDescription}}))}return pc}
}
</script>
</body>
</html>
'''

# --- FIXED: Corrected typo from @app-route to @app.route ---
@app.route('/')
def index():
    return render_template_string(HTML)

# --- FIXED: Corrected typo from @app-route to @app.route ---
@app.route('/health')
def health_check():
    return "OK", 200

@socketio.on('connect')
def handle_connect(auth):
    token = auth.get('token') if auth else None
    if not QUIET_MODE_SERVER:
        print(f"--- Connection Attempt (SID: {request.sid}) ---")
        print(f"Expected: ...{SECRET_KEY_SERVER[-6:]}, Received: ...{token[-6:] if token else 'None'}")
    if token != SECRET_KEY_SERVER:
        if not QUIET_MODE_SERVER: print("Result: Auth FAILED.")
        return False
    if not QUIET_MODE_SERVER: print("Result: Auth SUCCESSFUL.")
    return True

@socketio.on("join")
def handle_join(username):
    safe_username = html.escape(username)
    emit('message', {'id': f'join_{int(time.time())}','username': 'System','message': f'{safe_username} has joined.'}, broadcast=True)

@socketio.on("message")
def handle_message(data):
    if not isinstance(data, dict): return
    data['username'] = html.escape(data.get('username', 'Anonymous'))
    if data.get('isFile'):
        try:
            header, encoded = data['message'].split(",", 1)
            file_data = b64decode(encoded)
            if len(file_data) > MAX_FILE_SIZE_BYTES: return
        except Exception: return
        data['filename'] = html.escape(data.get('filename', 'file'))
    else: data['message'] = html.escape(data.get('message', ''))
    emit("message", data, broadcast=True)

@socketio.on("delete_message")
def handle_delete(data):
    emit("delete_message", {'id': data.get('id')}, broadcast=True)

@socketio.on("join-room")
def join_video():
    join_room("global"); users = [sid for sid in socketio.server.manager.rooms['/'].get("global", []) if sid != request.sid]; emit("all-users", {"users": users}); emit("user-joined", {"sid": request.sid}, room="global", include_self=False)

@socketio.on("leave-room")
def leave_video():
    leave_room("global"); emit("user-left", {"sid": request.sid}, room="global", include_self=False)

@socketio.on("signal")
def signal(data):
    emit("signal", {"from": request.sid, "data": data['data']}, room="data['to']")

@socketio.on("disconnect")
def on_disconnect():
    leave_room("global"); emit("user-left", {"sid": request.sid}, room="global", include_self=False)

if __name__ == '__main__' and "--server" in sys.argv:
    if not SECRET_KEY_SERVER:
        print("FATAL: Server started without a secret key.")
        sys.exit(1)
    if QUIET_MODE_SERVER:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
    else:
        print(f"Starting server in verbose mode with key: {SECRET_KEY_SERVER}")
    socketio.run(app, host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'key.pem'))