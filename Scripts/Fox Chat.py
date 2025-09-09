#!/usr/bin/env python3
import os
import subprocess
import time
import re
import sys
import shutil
import socket # Added to find the local IP address

# Auto-install/update requirements
def install_requirements():
    os.system("pip install flask flask_socketio requests > /dev/null 2>&1")
    if not shutil.which("cloudflared"):
        os.system("pkg update -y > /dev/null 2>&1 && pkg install cloudflared -y > /dev/null 2>&1")
    if not shutil.which("tor"):
        os.system("pkg install tor -y > /dev/null 2>&1")

# NEW: Function to get the local IP address
def get_local_ip():
    """Finds the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be a reachable address
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1' # Fallback to localhost
    finally:
        s.close()
    return IP

# Start Tor and wait for it to initialize
def start_tor():
    tor_process = subprocess.Popen(["tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(10)
    return tor_process

# Start Flask Chat server in background
def start_chat_server():
    return subprocess.Popen([sys.executable, __file__, "--server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# MODIFIED: Start cloudflared and print both online and offline links
def generate_and_print_links():
    """Starts cloudflared, gets links, and prints them to the console."""
    cmd = ["cloudflared", "tunnel", "--url", "http://localhost:5000"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    # Get the local IP for the offline/hotspot link
    local_ip = get_local_ip()
    local_url = f"http://{local_ip}:5000"

    print("\n🚀 Starting services... please wait for the links.")

    for line in process.stdout:
        # Search for the public cloudflared URL
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            online_url = match.group(0)

            # Clear the console for a clean output
            os.system('cls' if os.name == 'nt' else 'clear')

            print("✅ Fox Chat is now live!")
            print("===========================")
            print(f"🔗 Online Link (Internet):     {online_url}")
            print(f"🏠 Offline Link (Hotspot/LAN): {local_url}")
            print("\nShare the appropriate link with others.")
            print("Press Ctrl+C to stop the server.")

            return process # Return the running process

    # Fallback in case cloudflared fails to generate a link
    print("\n⚠️ Could not generate an online link.")
    print(f"You can still use the Offline Link: {local_url}")
    return process

if __name__ == '__main__' and "--server" not in sys.argv:
    install_requirements()
    tor = start_tor()
    server = start_chat_server()
    time.sleep(5)
    # The function now handles printing the links
    tunnel = generate_and_print_links()
    try:
        # Keep the script running until interrupted
        tunnel.wait()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        tunnel.terminate()
        tor.terminate()
        server.terminate()
        sys.exit()

# ---------------------------------------
# FLASK FOX CHAT SERVER WITH FULL HTML
# (This part of the code remains unchanged)
# ---------------------------------------

from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Fox Chat</title>
<script src="https://cdn.socket.io/4.6.1/socket.io.min.js"></script>
<style>
*, *::before, *::after {
  box-sizing: border-box;
}
body {
  margin:0; padding:0;
  font-family:sans-serif;
  background:#121212;
  color:#e0e0e0;
  overflow-x:hidden;
}
h1.header {
  text-align:center;
  background:#1e1e1e;
  margin:0;
  padding:12px;
  font-size:1.5em;
  color:#9c27b0;
  border-bottom:1px solid #333;
}
/* Video grid */
#videos {
  display:none;
  padding:8px;
  background:#000;
  flex-wrap:wrap;
  gap:6px;
  width:100%;
}
#videos.show {
  display:flex;
}
#videos video {
  display:none;
  width:calc(25%-8px);
  max-width:120px;
  height:auto;
  object-fit:cover;
  border:2px solid #333;
  border-radius:6px;
}
#videos.show video {
  display:block;
}
#local {
  display:none;
}
/* Top controls */
#controls {
  display:flex;
  flex-wrap:wrap;
  justify-content:center;
  gap:8px;
  padding:12px;
  background:#1e1e1e;
  width:100%;
}
#controls button {
  flex:1 1 100px;
  max-width:150px;
  min-width:80px;
  padding:10px;
  background:#2c2c2c;
  color:#fff;
  border:1px solid #333;
  border-radius:4px;
  transition:background .2s;
}
#controls button:hover:not(:disabled){
  background:#3a3a3a;
}
#controls button:disabled{
  opacity:0.4;
}
/* Chat area */
#chat-container{
  padding:0 12px 100px;
  width:100%;
}
#chat{
  width:100%;
  height:240px;
  overflow-y:auto;
  background:#181818;
  border-top:1px solid #333;
  padding:12px;
  margin-top:8px;
  border-radius:4px;
}
.chat-message{
  margin-bottom:10px;
  position:relative;
  word-break:break-word;
  max-width:100%;
}
.chat-message strong{
  color:#4caf50;
}
.delete-btn{
  position:absolute;
  top:2px;
  right:2px;
  background:none;
  color:#f44336;
  cursor:pointer;
}
/* Thumbnails */
.chat-message img, .chat-message video{
  max-width:80px;
  max-height:80px;
  cursor:pointer;
  transition:all .2s;
  border:1px solid #333;
  border-radius:4px;
}
.chat-message img.expanded, .chat-message video.expanded{
  position:fixed;
  top:50%;
  left:50%;
  transform:translate(-50%,-50%);
  max-width:90vw;
  max-height:90vh;
  z-index:200;
}
/* Filename & download */
.filename{
  display:block;
  margin-top:4px;
  color:#ccc;
}
.download-link{
  margin-left:8px;
  color:#90caf9;
  text-decoration:none;
}
.download-link:hover{
  text-decoration:underline;
}
/* Bottom controls */
.controls{
  position:fixed;
  bottom:0;
  left:0;
  right:0;
  display:flex;
  flex-wrap:wrap;
  justify-content:center;
  gap:8px;
  padding:10px;
  background:#1e1e1e;
}
.controls input[type="text"]{
  flex:1 1 200px;
  max-width:60%;
  min-width:120px;
  padding:10px;
  background:#2c2c2c;
  color:#e0e0e0;
  border:1px solid #333;
  border-radius:4px;
}
.controls button{
  flex:0 1 50px;
  padding:10px;
  background:#2c2c2c;
  border:1px solid #333;
  border-radius:4px;
}
.controls button:hover:not(:disabled){
  background:#3a3a3a;
}
</style>
</head>
<body>
<h1 class="header">Fox Chat</h1>
<div id="videos">
  <video id="local" autoplay muted playsinline></video>
</div>
<div id="controls">
  <button id="joinBtn">Join Call</button>
  <button id="muteBtn" disabled>Mute</button>
  <button id="videoBtn" disabled>Cam Off</button>
  <button id="leaveBtn" disabled>Leave</button>
</div>
<div id="chat-container">
  <div id="chat"></div>
  <div class="controls">
    <input id="message" type="text" placeholder="Type a message..." autocomplete="off"/>
    <button onclick="sendMessage()">Send</button>
    <button id="recordButton" onclick="toggleRecording()">🎙️</button>
    <button onclick="sendFile()">📄</button>
    <button onclick="openCamera()">📷</button>
    <input type="file" id="fileInput" style="display:none"/>
    <input type="file" id="cameraInput" accept="image/*,video/*" capture style="display:none"/>
  </div>
</div>
<script>
const socket = io();
let username = localStorage.getItem("username");
if(!username){
  do{
    username = prompt("Enter your username:");
  }while(!username);
  localStorage.setItem("username",username);
}
socket.emit("join",username);
function genId(){
  return 'msg_'+Date.now()+'_'+Math.random().toString(36).substr(2,5);
}
// Text messaging function
function sendMessage(){
  let txt = document.getElementById("message").value.trim();
  if(!txt) return;
  socket.emit("message",{ id:genId(), username, message:txt });
  document.getElementById("message").value='';
}
// Voice recording
let mediaRecorder, recordedChunks=[], isRecording=false;
function toggleRecording(){
  let btn=document.getElementById("recordButton");
  if(isRecording){
    mediaRecorder.stop();
    isRecording=false;
    btn.textContent='🎙️';
  } else {
    navigator.mediaDevices.getUserMedia({audio:true})
      .then(stream=>{
        recordedChunks=[];
        mediaRecorder=new MediaRecorder(stream);
        mediaRecorder.ondataavailable=e=>{
          if(e.data.size) recordedChunks.push(e.data);
        };
        mediaRecorder.onstop=()=>{
          let blob=new Blob(recordedChunks,{type:'audio/mp4'});
          let reader=new FileReader();
          reader.onloadend=()=>socket.emit("message",{ id:genId(), username, message:reader.result, isVoice:true });
          reader.readAsDataURL(blob);
        };
        mediaRecorder.start();
        isRecording=true;
        btn.textContent='🛑';
      })
      .catch(_=>alert("Microphone access denied"));
  }
}
// File & image upload
function compressImage(file,cb){
  let r=new FileReader();
  r.onload=()=>{
    let img=new Image();
    img.onload=()=>{
      let MAX=800,scale=Math.min(MAX/img.width,1);
      let c=document.createElement('canvas');
      c.width=img.width*scale;
      c.height=img.height*scale;
      c.getContext('2d').drawImage(img,0,0,c.width,c.height);
      cb(c.toDataURL(file.type,0.7));
    };
    img.src=r.result;
  };
  r.readAsDataURL(file);
}
function sendFile(){
  fileInput.click();
}
fileInput.addEventListener('change',e=>{
  let f=e.target.files[0];
  if(!f)return;
  if(f.type.startsWith('image/')){
    compressImage(f,dataURL=>emitFile(dataURL,'image',f.name));
  } else {
    let rd=new FileReader();
    rd.onload=()=>emitFile(rd.result,f.type.startsWith('video/')?'video':'file',f.name);
    rd.readAsDataURL(f);
  }
  e.target.value='';
});
function openCamera(){
  cameraInput.click();
}
cameraInput.addEventListener('change',e=>{
  let f=e.target.files[0];
  if(!f)return;
  if(f.type.startsWith('image/')){
    compressImage(f,dataURL=>emitFile(dataURL,'image',f.name));
  } else {
    let rd=new FileReader();
    rd.onload=()=>emitFile(rd.result,'video',f.name);
    rd.readAsDataURL(f);
  }
  e.target.value='';
});
function emitFile(dataURL,type,name){
  socket.emit("message",{ id:genId(), username, message:dataURL, isFile:true, fileType:type, filename:name });
}
// Render incoming
socket.on("message",d=>{
  let c=document.getElementById('chat');
  let div=document.createElement('div');
  div.className='chat-message';
  div.id=d.id;
  div.innerHTML=`<strong>${d.username}:</strong> `;
  if(d.isVoice){
    let a=document.createElement('audio');
    a.controls=true;
    a.src=d.message;
    div.appendChild(a);
  } else if(d.isFile){
    if(d.fileType==='image'||d.fileType==='video'){
      let el=document.createElement(d.fileType);
      el.src=d.message;
      el.onclick=()=>el.classList.toggle('expanded');
      div.appendChild(el);
    }
    let fn=document.createElement('span');
    fn.className='filename';
    fn.textContent=d.filename;
    div.appendChild(fn);
    let dl=document.createElement('a');
    dl.href=d.message;
    dl.download=d.filename;
    dl.textContent='⬇️';
    dl.className='download-link';
    div.appendChild(dl);
  } else {
    div.innerHTML+=d.message.replace(/</g,'&lt;');
  }
  if(d.username===username){
    let btn=document.createElement('button');
    btn.className='delete-btn';
    btn.textContent='❌';
    btn.onclick=()=>socket.emit('delete_message',{id:d.id});
    div.appendChild(btn);
  }
  c.appendChild(div);
  c.scrollTop=c.scrollHeight;
});
socket.on('delete_message',d=>{
  let e=document.getElementById(d.id);
  if(e) e.remove();
});

// Video Call
const videos=document.getElementById('videos'),
  localVideo=document.getElementById('local'),
  joinBtn=document.getElementById('joinBtn'),
  muteBtn=document.getElementById('muteBtn'),
  videoBtn=document.getElementById('videoBtn'),
  leaveBtn=document.getElementById('leaveBtn');
let localStream, peerConnections = {}, isMuted = false, videoOff = false;

joinBtn.onclick = async () => {
  try {
    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    localVideo.srcObject = localStream;
    localVideo.play();
    videos.classList.add('show');
    joinBtn.disabled = true;
    muteBtn.disabled = false;
    videoBtn.disabled = false;
    leaveBtn.disabled = false;
    socket.emit('join-room');
  } catch {
    alert('Camera/Mic permission denied or error.');
  }
};

muteBtn.onclick = () => {
  if(!localStream) return;
  isMuted = !isMuted;
  localStream.getAudioTracks()[0].enabled = !isMuted;
  muteBtn.textContent = isMuted ? 'Unmute' : 'Mute';
};

videoBtn.onclick = () => {
  if(!localStream) return;
  videoOff = !videoOff;
  localStream.getVideoTracks()[0].enabled = !videoOff;
  videoBtn.textContent = videoOff ? 'Cam On' : 'Cam Off';
};

leaveBtn.onclick = () => {
  socket.emit('leave-room');
  for(let id in peerConnections){
    peerConnections[id].close();
  }
  peerConnections = {};
  if(localStream){
    localStream.getTracks().forEach(track => track.stop());
  }
  localVideo.srcObject = null;
  videos.classList.remove('show');
  joinBtn.disabled = false;
  muteBtn.disabled = true;
  videoBtn.disabled = true;
  leaveBtn.disabled = true;
};

socket.on('all-users', data => {
  data.users.forEach(id => {
    if(id === socket.id) return;
    createPeerConnection(id, true);
  });
});

socket.on('user-joined', data => {
  if(data.sid === socket.id) return;
  createPeerConnection(data.sid, false);
});

socket.on('user-left', data => {
  if(peerConnections[data.sid]){
    peerConnections[data.sid].close();
    delete peerConnections[data.sid];
    let vid = document.getElementById(`video_${data.sid}`);
    if(vid) vid.remove();
  }
});

socket.on('signal', async data => {
  let pc = peerConnections[data.from];
  if(!pc) pc = createPeerConnection(data.from, false);
  if(data.data.sdp){
    await pc.setRemoteDescription(new RTCSessionDescription(data.data.sdp));
    if(data.data.sdp.type === 'offer'){
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);
      socket.emit('signal', { to: data.from, data: { sdp: pc.localDescription } });
    }
  } else if(data.data.candidate){
    await pc.addIceCandidate(new RTCIceCandidate(data.data.candidate));
  }
});

function createPeerConnection(id, isOfferer){
  const pc = new RTCPeerConnection({
    iceServers: [{urls: "stun:stun.l.google.com:19302"}]
  });
  peerConnections[id] = pc;

  pc.onicecandidate = event => {
    if(event.candidate){
      socket.emit('signal', { to: id, data: { candidate: event.candidate } });
    }
  };

  pc.ontrack = event => {
    let vid = document.getElementById(`video_${id}`);
    if(!vid){
      vid = document.createElement('video');
      vid.id = `video_${id}`;
      vid.autoplay = true;
      vid.playsInline = true;
      vid.width = 120;
      videos.appendChild(vid);
    }
    vid.srcObject = event.streams[0];
  };

  if(localStream){
    localStream.getTracks().forEach(track => pc.addTrack(track, localStream));
  }

  if(isOfferer){
    pc.createOffer()
      .then(offer => pc.setLocalDescription(offer))
      .then(() => {
        socket.emit('signal', { to: id, data: { sdp: pc.localDescription } });
      });
  }

  return pc;
}
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@socketio.on("join")
def handle_join(username):
    emit('message', {
        'id': f'join_{username}_{int(time.time())}',
        'username': 'System',
        'message': f'{username} has joined.'
    }, broadcast=True)

@socketio.on("message")
def handle_message(data):
    emit("message", data, broadcast=True)

@socketio.on("delete_message")
def handle_delete(data):
    emit("delete_message", {'id': data['id']}, broadcast=True)

@socketio.on("join-room")
def join_video():
    join_room("global")
    users = [sid for sid in socketio.server.manager.rooms['/'].get("global", []) if sid != request.sid]
    emit("all-users", {"users": users}, room=request.sid)
    emit("user-joined", {"sid": request.sid}, room="global", include_self=False)

@socketio.on("leave-room")
def leave_video():
    leave_room("global")
    emit("user-left", {"sid": request.sid}, room="global", include_self=False)

@socketio.on("signal")
def signal(data):
    emit("signal", {"from": request.sid, "data": data['data']}, room=data['to'])

@socketio.on("disconnect")
def on_disconnect():
    leave_room("global")
    emit("user-left", {"sid": request.sid}, room="global", include_self=False)

if __name__ == '__main__' and "--server" in sys.argv:
    socketio.run(app, host='0.0.0.0', port=5000)
