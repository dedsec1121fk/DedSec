from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'replace-with-a-secure-key'
socketio = SocketIO(app)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0,viewport-fit=cover">
  <title>Charon Chat</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
  <style>
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      padding: 0;
      height: 100vh;
      background: #121212;
      color: #e0e0e0;
      font-family: sans-serif;
      /* allow scrolling inside chat rather than hiding overflow */
    }
    .container {
      display: flex;
      flex-direction: column;
      height: 100%;
    }
    h1 {
      text-align: center;
      margin: 10px 0;
      font-size: 1.5em;
    }
    #chat {
      flex: 1;
      overflow-y: auto;
      background: #1e1e1e;
      padding: 10px;
      padding-bottom: 80px; /* leave space for the controls */
      border-top: 1px solid #333;
      border-bottom: 1px solid #333;
    }
    .chat-message {
      position: relative;
      margin-bottom: 8px;
      word-break: break-word;
      padding-right: 30px;
    }
    .chat-message strong {
      color: #76ff03;
    }
    .chat-message img,
    .chat-message video {
      max-width: 200px;
      max-height: 200px;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .chat-message img.expanded,
    .chat-message video.expanded {
      max-width: 100%;
      max-height: none;
    }
    .delete-btn {
      position: absolute;
      top: 2px;
      right: 2px;
      background: transparent;
      border: none;
      color: #ff5252;
      cursor: pointer;
      font-size: 0.9em;
    }
    .controls {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: #222;
      padding: 8px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: center;
      gap: 6px;
      border-top: 1px solid #444;
      z-index: 10;
    }
    input[type="text"] {
      flex: 1;
      min-width: 40%;
      padding: 8px;
      border-radius: 4px;
      border: none;
    }
    button {
      padding: 8px 12px;
      border: none;
      border-radius: 4px;
      background: #444;
      color: white;
      cursor: pointer;
    }
    button:hover {
      background: #666;
    }
    #fileInput,
    #cameraInput {
      display: none;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Charon Chat</h1>
    <div id="chat"></div>
  </div>

  <div class="controls">
    <input id="message" type="text" placeholder="Type your message..." />
    <button onclick="sendMessage()">Send Text</button>
    <button id="recordButton" onclick="toggleRecording()">🎙️</button>
    <button onclick="sendFile()">📁</button>
    <button onclick="openCamera()">📷</button>
    <input type="file" id="fileInput" />
    <input type="file" id="cameraInput" accept="image/*,video/*" capture />
  </div>

  <script>
    const socket = io();
    let username = localStorage.getItem("username");
    if (!username) {
      do {
        username = prompt("Enter your username:");
      } while (!username || !username.trim());
      username = username.trim();
      localStorage.setItem("username", username);
    }
    socket.emit("join", username);

    function genId() {
      return 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2,5);
    }

    function sendMessage() {
      const input = document.getElementById("message");
      const text = input.value.trim();
      if (!text) return;
      const id = genId();
      socket.emit("message", { id, username, message: text });
      input.value = "";
    }

    // Voice recording
    let mediaRecorder, recordedChunks = [], isRecording = false;
    function toggleRecording() {
      const btn = document.getElementById("recordButton");
      if (isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        btn.textContent = '🎙️';
      } else {
        navigator.mediaDevices.getUserMedia({ audio: true })
          .then(stream => {
            let options = { mimeType: 'audio/mp4' };
            try { mediaRecorder = new MediaRecorder(stream, options); }
            catch { mediaRecorder = new MediaRecorder(stream); }
            recordedChunks = [];
            mediaRecorder.ondataavailable = e => { if (e.data.size) recordedChunks.push(e.data); };
            mediaRecorder.onstop = () => {
              const blob = new Blob(recordedChunks, { type: mediaRecorder.mimeType });
              const reader = new FileReader();
              reader.onloadend = () => {
                const id = genId();
                socket.emit("message", { id, username, message: reader.result, isVoice: true });
              };
              reader.readAsDataURL(blob);
            };
            mediaRecorder.start();
            isRecording = true;
            btn.textContent = '🛑';
          })
          .catch(err => alert("Microphone access denied: " + err));
      }
    }

    // Image compression helper
    function compressImage(file, callback) {
      const reader = new FileReader();
      reader.onload = () => {
        const img = new Image();
        img.onload = () => {
          const MAX_WIDTH = 800;
          const scale = Math.min(MAX_WIDTH / img.width, 1);
          const canvas = document.createElement('canvas');
          canvas.width = img.width * scale;
          canvas.height = img.height * scale;
          canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
          callback(canvas.toDataURL(file.type, 0.7));
        };
        img.src = reader.result;
      };
      reader.readAsDataURL(file);
    }

    // File upload
    function sendFile() { fileInput.click(); }
    fileInput.addEventListener("change", e => {
      const file = e.target.files[0];
      if (!file) return;
      const id = genId();
      if (file.type.startsWith("image/")) {
        compressImage(file, dataURL => {
          socket.emit("message", {
            id, username,
            message: dataURL,
            isFile: true,
            fileType: "image",
            filename: file.name
          });
        });
      } else {
        const reader = new FileReader();
        reader.onload = () => {
          const type = file.type.startsWith("video/") ? "video" : "file";
          socket.emit("message", {
            id, username,
            message: reader.result,
            isFile: true,
            fileType: type,
            filename: file.name
          });
        };
        reader.readAsDataURL(file);
      }
      e.target.value = "";
    });

    // Camera capture
    function openCamera() { cameraInput.click(); }
    cameraInput.addEventListener("change", e => {
      const file = e.target.files[0];
      if (!file) return;
      const id = genId();
      if (file.type.startsWith("image/")) {
        compressImage(file, dataURL => {
          socket.emit("message", {
            id, username,
            message: dataURL,
            isFile: true,
            fileType: "image",
            filename: file.name
          });
        });
      } else {
        const reader = new FileReader();
        reader.onload = () => {
          socket.emit("message", {
            id, username,
            message: reader.result,
            isFile: true,
            fileType: "video",
            filename: file.name
          });
        };
        reader.readAsDataURL(file);
      }
      e.target.value = "";
    });

    // Render and deletion
    socket.on("message", data => {
      const chat = document.getElementById("chat");
      const { id, username: user, message, isVoice, isFile, fileType, filename } = data;
      const div = document.createElement("div");
      div.className = "chat-message";
      div.id = id;
      div.innerHTML = `<strong>${user}:</strong> `;
      if (isVoice) {
        const audio = document.createElement("audio");
        audio.controls = true;
        audio.src = message;
        div.appendChild(audio);
      } else if (isFile) {
        if (fileType === "image") {
          const img = document.createElement("img");
          img.src = message;
          img.onclick = () => img.classList.toggle("expanded");
          div.appendChild(img);
        } else if (fileType === "video") {
          const video = document.createElement("video");
          video.controls = true;
          video.playsInline = true;
          video.src = message;
          video.onclick = () => video.classList.toggle("expanded");
          div.appendChild(video);
        } else {
          const link = document.createElement("a");
          link.href = message;
          link.download = filename;
          link.textContent = "Download " + filename;
          div.appendChild(link);
        }
      } else {
        div.innerHTML += message.replace(/</g, "&lt;");
      }
      if (user === username) {
        const btn = document.createElement("button");
        btn.className = "delete-btn";
        btn.textContent = "🗑️";
        btn.onclick = () => socket.emit("delete_message", { id });
        div.appendChild(btn);
      }
      chat.appendChild(div);
      chat.scrollTop = chat.scrollHeight;
    });

    socket.on("delete_message", data => {
      const el = document.getElementById(data.id);
      if (el) el.remove();
    });
  </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@socketio.on('join')
def handle_join(username):
    emit('message', {
        'id': f'join_{username}_{int(__import__("time").time())}',
        'username': 'System',
        'message': f'{username} has joined the chat.',
        'plain': True
    }, broadcast=True)

@socketio.on('message')
def handle_message(data):
    emit('message', data, broadcast=True)

@socketio.on('delete_message')
def handle_delete(data):
    emit('delete_message', {'id': data['id']}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)

