
#!/usr/bin/env python3
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Fox Chat</title>
  <script src="https://cdn.socket.io/4.6.1/socket.io.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    body { margin:0; padding:0; font-family:sans-serif; background:#121212; color:#e0e0e0; overflow-x:hidden; }
    h1.header { text-align:center; background:#1e1e1e; margin:0; padding:12px; font-size:1.5em; color:#9c27b0; border-bottom:1px solid #333; }

    /* Video grid */
    #videos { display:none; padding:8px; background:#000; flex-wrap:wrap; gap:6px; width:100%; }
    #videos.show { display:flex; }
    #videos video { display:none; width:calc(25%-8px); max-width:120px; height:auto; object-fit:cover; border:2px solid #333; border-radius:6px; }
    #videos.show video { display:block; }
    #local { display:none; }

    /* Top controls */
    #controls { display:flex; flex-wrap:wrap; justify-content:center; gap:8px; padding:12px; background:#1e1e1e; width:100%; }
    #controls button { flex:1 1 100px; max-width:150px; min-width:80px; padding:10px; background:#2c2c2c; color:#fff; border:1px solid #333; border-radius:4px; transition:background .2s; }
    #controls button:hover:not(:disabled){ background:#3a3a3a; }
    #controls button:disabled{ opacity:0.4; }

    /* Chat area */
    #chat-container{ padding:0 12px 100px; width:100%; }
    #chat{ width:100%; height:240px; overflow-y:auto; background:#181818; border-top:1px solid #333; padding:12px; margin-top:8px; border-radius:4px; }
    .chat-message{ margin-bottom:10px; position:relative; word-break:break-word; max-width:100%; }
    .chat-message strong{ color:#4caf50; }
    .delete-btn{ position:absolute; top:2px; right:2px; background:none; color:#f44336; cursor:pointer; }

    /* Thumbnails */
    .chat-message img, .chat-message video{
      max-width:80px; max-height:80px; cursor:pointer; transition:all .2s; border:1px solid #333; border-radius:4px;
    }
    .chat-message img.expanded, .chat-message video.expanded{
      position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); max-width:90vw; max-height:90vh; z-index:200;
    }

    /* Filename & download */
    .filename{ display:block; margin-top:4px; color:#ccc; }
    .download-link{ margin-left:8px; color:#90caf9; text-decoration:none; }
    .download-link:hover{ text-decoration:underline; }

    /* Bottom controls */
    .controls{ position:fixed; bottom:0; left:0; right:0; display:flex; flex-wrap:wrap; justify-content:center; gap:8px; padding:10px; background:#1e1e1e; }
    .controls input[type="text"]{ flex:1 1 200px; max-width:60%; min-width:120px; padding:10px; background:#2c2c2c; color:#e0e0e0; border:1px solid #333; border-radius:4px; }
    .controls button{ flex:0 1 50px; padding:10px; background:#2c2c2c; border:1px solid #333; border-radius:4px; }
    .controls button:hover:not(:disabled){ background:#3a3a3a; }
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
      <button onclick="sendFile()">📁</button>
      <button onclick="openCamera()">📷</button>
      <input type="file" id="fileInput" style="display:none"/>
      <input type="file" id="cameraInput" accept="image/*,video/*" capture style="display:none"/>
    </div>
  </div>

<script>
  const socket = io();
  let username = localStorage.getItem("username");
  if(!username){
    do{ username = prompt("Enter your username:"); }while(!username);
    localStorage.setItem("username",username);
  }
  socket.emit("join",username);

  function genId(){ return 'msg_'+Date.now()+'_'+Math.random().toString(36).substr(2,5); }

  // Text messaging
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
      mediaRecorder.stop(); isRecording=false; btn.textContent='🎙️';
    } else {
      navigator.mediaDevices.getUserMedia({audio:true})
        .then(stream=>{
          recordedChunks=[];
          mediaRecorder=new MediaRecorder(stream);
          mediaRecorder.ondataavailable=e=>{ if(e.data.size) recordedChunks.push(e.data); };
          mediaRecorder.onstop=()=>{
            let blob=new Blob(recordedChunks,{type:'audio/mp4'});
            let reader=new FileReader();
            reader.onloadend=()=>socket.emit("message",{ id:genId(), username, message:reader.result, isVoice:true });
            reader.readAsDataURL(blob);
          };
          mediaRecorder.start(); isRecording=true; btn.textContent='🛑';
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
        c.width=img.width*scale; c.height=img.height*scale;
        c.getContext('2d').drawImage(img,0,0,c.width,c.height);
        cb(c.toDataURL(file.type,0.7));
      };
      img.src=r.result;
    };
    r.readAsDataURL(file);
  }
  function sendFile(){ fileInput.click(); }
  fileInput.addEventListener('change',e=>{
    let f=e.target.files[0]; if(!f)return;
    if(f.type.startsWith('image/')){
      compressImage(f,dataURL=>emitFile(dataURL,'image',f.name));
    } else {
      let rd=new FileReader();
      rd.onload=()=>emitFile(rd.result,f.type.startsWith('video/')?'video':'file',f.name);
      rd.readAsDataURL(f);
    }
    e.target.value='';
  });
  function openCamera(){ cameraInput.click(); }
  cameraInput.addEventListener('change',e=>{
    let f=e.target.files[0]; if(!f)return;
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
    let div=document.createElement('div'); div.className='chat-message'; div.id=d.id;
    div.innerHTML=`<strong>${d.username}:</strong> `;
    if(d.isVoice){
      let a=document.createElement('audio'); a.controls=true; a.src=d.message; div.appendChild(a);
    } else if(d.isFile){
      if(d.fileType==='image'||d.fileType==='video'){
        let el=document.createElement(d.fileType); el.src=d.message;
        el.onclick=()=>el.classList.toggle('expanded'); div.appendChild(el);
      }
      let fn=document.createElement('span'); fn.className='filename'; fn.textContent=d.filename; div.appendChild(fn);
      let dl=document.createElement('a'); dl.href=d.message; dl.download=d.filename;
      dl.textContent='⬇️'; dl.className='download-link'; div.appendChild(dl);
    } else {
      div.innerHTML+=d.message.replace(/</g,'&lt;');
    }
    if(d.username===username){
      let btn=document.createElement('button'); btn.className='delete-btn'; btn.textContent='🗑️';
      btn.onclick=()=>socket.emit('delete_message',{id:d.id}); div.appendChild(btn);
    }
    c.appendChild(div); c.scrollTop=c.scrollHeight;
  });
  socket.on('delete_message',d=>{let e=document.getElementById(d.id); if(e) e.remove();});

  // Video Call
  const videos=document.getElementById('videos'),
        localVideo=document.getElementById('local'),
        joinBtn=document.getElementById('joinBtn'),
        muteBtn=document.getElementById('muteBtn'),
        videoBtn=document.getElementById('videoBtn'),
        leaveBtn=document.getElementById('leaveBtn');
  let localStream, peers={}, muted=false, camOff=false;

  joinBtn.onclick=async()=>{
    joinBtn.disabled=true;
    try{ localStream=await navigator.mediaDevices.getUserMedia({video:true,audio:true}); }
    catch{ alert("Camera/mic denied"); joinBtn.disabled=false; return; }
    videos.classList.add('show');
    localVideo.style.display='block'; localVideo.srcObject=localStream;
    socket.emit("join-room");
    [muteBtn,videoBtn,leaveBtn].forEach(b=>b.disabled=false);
  };
  muteBtn.onclick=()=>{
    muted=!muted; localStream.getAudioTracks().forEach(t=>t.enabled=!muted);
    muteBtn.textContent=muted?"Unmute":"Mute";
  };
  videoBtn.onclick=()=>{
    camOff=!camOff; localStream.getVideoTracks().forEach(t=>t.enabled=!camOff);
    videoBtn.textContent=camOff?"Cam On":"Cam Off";
  };
  leaveBtn.onclick=()=>{
    socket.emit("leave-room");
    Object.values(peers).forEach(pc=>pc.close()); peers={};
    document.querySelectorAll('#videos.show video').forEach(v=>v.remove());
    if(localStream)localStream.getTracks().forEach(t=>t.stop());
    localVideo.srcObject=null; videos.classList.remove('show');
    [muteBtn,videoBtn,leaveBtn].forEach(b=>b.disabled=true); joinBtn.disabled=false;
  };

  function createPeer(id, initiator){
    const pc=new RTCPeerConnection({iceServers:[{urls:"stun:stun.l.google.com:19302"}]});
    localStream.getTracks().forEach(t=>pc.addTrack(t,localStream));
    pc.ontrack=e=>addRemote(id,e.streams[0]);
    pc.onicecandidate=e=>e.candidate&&socket.emit('signal',{to:id,data:{candidate:e.candidate}});
    if(initiator){
      pc.onnegotiationneeded=async()=>{
        let offer=await pc.createOffer();
        await pc.setLocalDescription(offer);
        socket.emit('signal',{to:id,data:{desc:pc.localDescription}});
      };
    }
    return pc;
  }

  function addRemote(id,stream){
    if(document.getElementById('v_'+id))return;
    let v=document.createElement('video');
    v.id='v_'+id; v.autoplay=true; v.playsInline=true; v.srcObject=stream;
    videos.appendChild(v);
  }

  socket.on('all-users',({users})=>users.forEach(u=>peers[u]=createPeer(u,true)));
  socket.on('user-joined',({sid})=>peers[sid]=createPeer(sid,false));
  socket.on('user-left',({sid})=>{
    if(peers[sid])peers[sid].close(); delete peers[sid];
    let e=document.getElementById('v_'+sid); if(e)e.remove();
  });
  socket.on('signal',async({from,data})=>{
    let pc=peers[from]||(peers[from]=createPeer(from,false));
    if(data.desc){
      await pc.setRemoteDescription(data.desc);
      if(data.desc.type==='offer'){
        let ans=await pc.createAnswer();
        await pc.setLocalDescription(ans);
        socket.emit('signal',{to:from,data:{desc:pc.localDescription}});
      }
    }
    if(data.candidate)pc.addIceCandidate(data.candidate).catch(console.error);
  });
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@socketio.on("join")
def handle_join(username):
    emit('message',{'id':f'join_{username}_{int(time.time())}','username':'System','message':f'{username} has joined.'},broadcast=True)

@socketio.on("message")
def handle_message(data):
    emit("message", data, broadcast=True)

@socketio.on("delete_message")
def handle_delete(data):
    emit("delete_message", {'id': data['id']}, broadcast=True)

@socketio.on("join-room")
def join_video():
    join_room("global")
    users=[sid for sid in socketio.server.manager.rooms['/'].get("global",[]) if sid!=request.sid]
    emit("all-users",{"users":users},room=request.sid)
    emit("user-joined",{"sid":request.sid},room="global",include_self=False)

@socketio.on("leave-room")
def leave_video():
    leave_room("global")
    emit("user-left",{"sid":request.sid},room="global",include_self=False)

@socketio.on("signal")
def signal(data):
    emit("signal",{"from":request.sid,"data":data['data']},room=data['to'])

@socketio.on("disconnect")
def on_disconnect():
    leave_room("global")
    emit("user-left",{"sid":request.sid},room="global",include_self=False)

if __name__ == '__main__':
    socketio.run(app,host='0.0.0.0',port=5000)
