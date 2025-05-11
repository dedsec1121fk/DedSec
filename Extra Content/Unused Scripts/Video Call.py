#!/usr/bin/env python3
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DedSec's Video Chat</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { height: 100%; width: 100%; overflow: hidden; background: #000; color: #fff; font-family: sans-serif; }
    body { display: flex; flex-direction: column; }
    #videos { display: grid; flex: 1; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 4px; padding: 4px; }
    video { width: 100%; aspect-ratio: 1/1; object-fit: cover; border: 1px solid #444; border-radius: 4px; }
    #controls { display: flex; gap: 4px; padding: 6px; background: #111; }
    button { flex: 1; padding: 10px; font-size: 1rem; background: #333; color: #fff; border: none; border-radius: 4px; }
    button.active { background: #0084ff; }
    button:disabled { opacity: 0.4; }
    #status { padding: 4px; font-size: 0.9rem; text-align: center; }
  </style>
</head>
<body>
  <div id="videos">
    <video id="local" autoplay playsinline muted></video>
  </div>
  <div id="controls">
    <button id="joinBtn">Join Call</button>
    <button id="muteBtn" disabled>Mute</button>
    <button id="videoBtn" disabled>Cam Off</button>
    <button id="fsBtn" disabled>Fullscreen</button>
    <button id="leaveBtn" disabled>Leave</button>
  </div>
  <div id="status">Status: Disconnected</div>

  <script src="https://cdn.socket.io/4.6.1/socket.io.min.js"></script>
  <script>
    const socket = io({ reconnection: true, reconnectionAttempts: Infinity, timeout: 20000 });
    const videos = document.getElementById("videos");
    const localVideo = document.getElementById("local");
    const joinBtn = document.getElementById("joinBtn");
    const muteBtn = document.getElementById("muteBtn");
    const videoBtn = document.getElementById("videoBtn");
    const fsBtn = document.getElementById("fsBtn");
    const leaveBtn = document.getElementById("leaveBtn");
    const statusDiv = document.getElementById("status");

    let localStream, peers = {}, muted = false, camOff = false, hbInterval;

    function updateStatus(text) {
      statusDiv.textContent = 'Status: ' + text;
    }

    function setControls(on) {
      [muteBtn, videoBtn, fsBtn, leaveBtn].forEach(b => b.disabled = !on);
    }

    joinBtn.onclick = async () => {
      joinBtn.disabled = true;
      updateStatus('Requesting media...');
      try {
        localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      } catch (e) {
        alert("Camera/microphone access denied.");
        joinBtn.disabled = false;
        updateStatus('Permission denied');
        return;
      }

      localVideo.srcObject = localStream;
      localVideo.muted = false;
      localVideo.removeAttribute('muted');
      localStream.getAudioTracks().forEach(t => t.enabled = true);
      localStream.getVideoTracks().forEach(t => t.enabled = true);

      setControls(true);
      updateStatus('Connecting...');
      socket.emit("join", {});
      hbInterval = setInterval(() => { if (socket.connected) socket.emit('ping'); }, 15000);
    };

    function createPeer(id, initiator) {
      const pc = new RTCPeerConnection({
        iceServers: [
          { urls: "stun:stun.l.google.com:19302" },
          { urls: "stun:stun1.l.google.com:19302" }
        ]
      });

      localStream.getTracks().forEach(t => pc.addTrack(t, localStream));

      pc.onicecandidate = e => {
        if (e.candidate) socket.emit("signal", { to: id, data: { candidate: e.candidate } });
      };

      pc.oniceconnectionstatechange = () => {
        const state = pc.iceConnectionState;
        console.log(`Peer ${id} ICE state: ${state}`);
        if (state === 'failed' || state === 'disconnected') {
          updateStatus('Reconnecting...');
          pc.restartIce();
        }
      };

      pc.ontrack = e => addRemoteVideo(id, e.streams[0]);

      if (initiator) {
        pc.onnegotiationneeded = async () => {
          const offer = await pc.createOffer();
          await pc.setLocalDescription(offer);
          socket.emit("signal", { to: id, data: { desc: pc.localDescription } });
        };
      }

      return pc;
    }

    function addRemoteVideo(id, stream) {
      if (document.getElementById("v_" + id)) return;
      const v = document.createElement("video");
      v.id = "v_" + id; v.autoplay = true; v.playsInline = true; v.srcObject = stream;
      v.addEventListener('click', () => {
        if (!document.fullscreenElement) v.requestFullscreen();
        else document.exitFullscreen();
      });
      videos.appendChild(v);
    }

    muteBtn.onclick = () => {
      muted = !muted;
      localStream.getAudioTracks().forEach(t => t.enabled = !muted);
      muteBtn.classList.toggle('active', muted);
      muteBtn.textContent = muted ? 'Unmute' : 'Mute';
    };

    videoBtn.onclick = () => {
      camOff = !camOff;
      localStream.getVideoTracks().forEach(t => t.enabled = !camOff);
      videoBtn.classList.toggle('active', camOff);
      videoBtn.textContent = camOff ? 'Cam On' : 'Cam Off';
    };

    fsBtn.onclick = () => {
      if (!document.fullscreenElement) localVideo.requestFullscreen();
      else document.exitFullscreen();
    };

    leaveBtn.onclick = () => {
      socket.emit("leave", {});
      cleanup();
      updateStatus('Disconnected');
    };

    function cleanup() {
      clearInterval(hbInterval);
      Object.values(peers).forEach(pc => pc.close());
      peers = {};
      document.querySelectorAll("video[id^='v_']").forEach(v => v.remove());
      if (localStream) {
        localStream.getTracks().forEach(t => t.stop());
        localVideo.srcObject = null;
      }
      setControls(false);
      joinBtn.disabled = false;
    }

    window.addEventListener('beforeunload', () => {
      socket.emit("leave", {});
    });

    socket.on("connect", () => updateStatus('Connected to signaling'));
    socket.on("disconnect", () => updateStatus('Signaling disconnected'));

    socket.on("all-users", ({ users }) => {
      updateStatus('Exchanging offers');
      users.forEach(id => peers[id] = createPeer(id, true));
    });

    socket.on("user-joined", ({ sid }) => {
      updateStatus('Peer joined');
      peers[sid] = createPeer(sid, false);
    });

    socket.on("user-left", ({ sid }) => {
      if (peers[sid]) peers[sid].close();
      delete peers[sid];
      const v = document.getElementById("v_" + sid);
      if (v) v.remove();
      updateStatus('Peer left');
    });

    socket.on("signal", async ({ from, data }) => {
      const pc = peers[from] || (peers[from] = createPeer(from, false));
      if (data.desc) {
        await pc.setRemoteDescription(data.desc);
        if (data.desc.type === "offer") {
          const ans = await pc.createAnswer();
          await pc.setLocalDescription(ans);
          socket.emit("signal", { to: from, data: { desc: pc.localDescription } });
        }
      }
      if (data.candidate) pc.addIceCandidate(data.candidate).catch(console.error);
    });
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@socketio.on("join")
def on_join(data):
    join_room("global")
    users = [s for s in socketio.server.manager.rooms['/'].get("global", []) if s != request.sid]
    emit("all-users", {"users": users}, room=request.sid)
    emit("user-joined", {"sid": request.sid}, room="global", include_self=False)

@socketio.on("leave")
def on_leave(data):
    leave_room("global")
    emit("user-left", {"sid": request.sid}, room="global", include_self=False)

@socketio.on("signal")
def on_signal(data):
    emit("signal", {"from": request.sid, "data": data['data']}, room=data['to'])

@socketio.on("disconnect")
def on_disconnect():
    leave_room("global")
    emit("user-left", {"sid": request.sid}, room="global", include_self=False)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)

