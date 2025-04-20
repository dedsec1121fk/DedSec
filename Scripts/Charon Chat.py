from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit
from cryptography.fernet import Fernet

app = Flask(__name__)
app.config['SECRET_KEY'] = Fernet.generate_key()
socketio = SocketIO(app)

cipher = Fernet(app.config['SECRET_KEY'])

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
      overflow: hidden;
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
      border-top: 1px solid #333;
      border-bottom: 1px solid #333;
    }
    .chat-message {
      margin-bottom: 8px;
      word-break: break-word;
    }
    .chat-message strong {
      color: #76ff03;
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
    }
    input[type="text"] {
      flex: 1;
      min-width: 55%;
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
    /* Hidden file input */
    #fileInput {
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
    <button id="recordButton" onclick="toggleRecording()">Record Voice</button>
    <button onclick="sendFile()">Send File</button>
    <button onclick="decryptMessages()">Decrypt</button>
    <button onclick="encryptMessages()">Encrypt Again</button>
    <input type="file" id="fileInput" />
  </div>

  <script>
    // User and socket initialization.
    let storedUsername = localStorage.getItem("username");
    let username = (storedUsername && storedUsername !== "None") ? storedUsername : prompt("Enter your username:");
    localStorage.setItem("username", username);
    const socket = io();
    if(username) {
      socket.emit("join", username);
    }

    // Voice recording state variables.
    let mediaRecorder;
    let recordedChunks = [];
    let isRecording = false;

    // Toggle voice recording on/off.
    function toggleRecording(){
      if(isRecording){
        mediaRecorder.stop();
        isRecording = false;
        document.getElementById("recordButton").textContent = "Record Voice";
      } else {
        if(navigator.mediaDevices && navigator.mediaDevices.getUserMedia){
          navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
              mediaRecorder = new MediaRecorder(stream);
              recordedChunks = [];
              mediaRecorder.ondataavailable = function(e) {
                if(e.data && e.data.size > 0){
                  recordedChunks.push(e.data);
                }
              };
              mediaRecorder.onstop = function(){
                let blob = new Blob(recordedChunks, { type: 'audio/webm' });
                let reader = new FileReader();
                reader.readAsDataURL(blob);
                reader.onloadend = function(){
                  let base64data = reader.result;
                  fetch("/encrypt_message", {
                    method: "POST",
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: base64data})
                  })
                  .then(res => res.json())
                  .then(data => {
                    socket.emit("message", {username, encrypted: data.encrypted, isVoice: true});
                  });
                };
              };
              mediaRecorder.start();
              isRecording = true;
              document.getElementById("recordButton").textContent = "Stop Recording";
            })
            .catch(err => {
              alert("Unable to access microphone: " + err);
            });
        } else {
          alert("Your browser does not support voice recording");
        }
      }
    }

    // Send a text message.
    function sendMessage() {
      const input = document.getElementById("message");
      const message = input.value.trim();
      if (!message) return;
      fetch("/encrypt_message", {
        method: "POST",
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message})
      })
      .then(res => res.json())
      .then(data => {
        socket.emit("message", {username, encrypted: data.encrypted});
        input.value = "";
      });
    }

    // File sending: trigger the hidden file input.
    function sendFile() {
      document.getElementById("fileInput").click();
    }

    // Handle file selection.
    document.getElementById("fileInput").addEventListener("change", function(event) {
      const file = event.target.files[0];
      if(!file) return;
      const reader = new FileReader();
      reader.onload = function(e) {
        const base64data = e.target.result;  // Contains a Data URL with metadata.
        fetch("/encrypt_message", {
          method: "POST",
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message: base64data})
        })
        .then(res => res.json())
        .then(data => {
          // Determine file type based on MIME type.
          let fileType = "file";
          if(file.type.startsWith("image/")){
            fileType = "image";
          } else if(file.type.startsWith("video/")){
            fileType = "video";
          }
          socket.emit("message", {
            username,
            encrypted: data.encrypted,
            isFile: true,
            fileType: fileType,
            filename: file.name
          });
        });
      };
      reader.readAsDataURL(file);
      // Reset the input so the same file can be selected again if needed.
      event.target.value = "";
    });

    // Display incoming messages.
    socket.on("message", function(data) {
      const chat = document.getElementById("chat");
      const div = document.createElement("div");
      div.className = "chat-message";
      const header = "<strong>" + data.username + ":</strong> ";
      if(data.isVoice){
        div.setAttribute("data-isvoice", "true");
        div.innerHTML = header + "Voice Message (encrypted)";
        div.setAttribute("data-encrypted", data.encrypted);
      }
      else if(data.isFile){
        div.setAttribute("data-isfile", "true");
        // Display a generic placeholder along with the filename.
        div.innerHTML = header + "File (" + data.filename + ") [encrypted]";
        div.setAttribute("data-encrypted", data.encrypted);
        // Store file metadata for later use during decryption.
        div.setAttribute("data-filetype", data.fileType);
        div.setAttribute("data-filename", data.filename);
      }
      else {
        div.innerHTML = header + data.encrypted.replace(/</g, "&lt;");
        if (!data.plain) {
          div.setAttribute("data-encrypted", data.encrypted);
        }
      }
      chat.appendChild(div);
      chat.scrollTop = chat.scrollHeight;
    });

    // Decrypt messages and handle various types.
    function decryptMessages() {
      document.querySelectorAll('.chat-message[data-encrypted]').forEach(msg => {
        fetch("/decrypt_message", {
          method: "POST",
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message: msg.getAttribute("data-encrypted")})
        })
        .then(res => res.json())
        .then(data => {
          const header = msg.innerHTML.split(":</strong>")[0] + ":</strong> ";
          // Check if this is a voice message.
          if(msg.getAttribute("data-isvoice")){
            let audio = document.createElement("audio");
            audio.controls = true;
            audio.src = data.decrypted;
            msg.innerHTML = header;
            msg.appendChild(audio);
            msg.removeAttribute("data-encrypted");
            msg.setAttribute("data-decrypted", data.decrypted);
          }
          // File messages
          else if(msg.getAttribute("data-isfile")){
            const fileType = msg.getAttribute("data-filetype");
            const filename = msg.getAttribute("data-filename");
            // For images: display an image.
            if(fileType === "image"){
              let img = document.createElement("img");
              img.src = data.decrypted;
              img.style.maxWidth = "100%";
              msg.innerHTML = header + "Image (" + filename + "): ";
              msg.appendChild(img);
            }
            // For videos: display a video player.
            else if(fileType === "video"){
              let video = document.createElement("video");
              video.src = data.decrypted;
              video.controls = true;
              video.style.maxWidth = "100%";
              msg.innerHTML = header + "Video (" + filename + "): ";
              msg.appendChild(video);
            }
            // For other files: provide a download link.
            else {
              let link = document.createElement("a");
              link.href = data.decrypted;
              link.download = filename;
              link.textContent = "Download " + filename;
              msg.innerHTML = header + "File (" + filename + "): ";
              msg.appendChild(link);
            }
            msg.removeAttribute("data-encrypted");
            msg.setAttribute("data-decrypted", data.decrypted);
          }
          // Text messages.
          else {
            msg.innerHTML = header + " " + data.decrypted.replace(/</g, "&lt;");
            msg.setAttribute("data-decrypted", data.decrypted);
          }
        });
      });
    }

    // Re-encrypt messages using stored decrypted text.
    function encryptMessages() {
      document.querySelectorAll('.chat-message[data-encrypted], .chat-message[data-decrypted]').forEach(msg => {
        let isVoice = msg.getAttribute("data-isvoice");
        let isFile = msg.getAttribute("data-isfile");
        let plainText = msg.getAttribute("data-decrypted") || msg.textContent.split(": ").slice(1).join(": ");
        fetch("/encrypt_message", {
          method: "POST",
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message: plainText})
        })
        .then(res => res.json())
        .then(data => {
          const header = msg.innerHTML.split(":</strong>")[0] + ":</strong>";
          if(isVoice){
            msg.innerHTML = header + " Voice Message (encrypted)";
          }
          else if(isFile){
            // Revert to a generic file placeholder.
            const fileType = msg.getAttribute("data-filetype");
            const filename = msg.getAttribute("data-filename");
            msg.innerHTML = header + " File (" + filename + ") [encrypted]";
          }
          else {
            msg.innerHTML = header + " " + data.encrypted.replace(/</g, "&lt;");
          }
          msg.setAttribute("data-encrypted", data.encrypted);
          msg.removeAttribute("data-decrypted");
        });
      });
    }
  </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@socketio.on('join')
def handle_join(username):
    if username:
        emit('message', {'username': 'System', 'encrypted': f'{username} has joined the chat.', 'plain': True}, broadcast=True)

@socketio.on('message')
def handle_message(data):
    emit('message', data, broadcast=True)

@app.route('/encrypt_message', methods=['POST'])
def encrypt_message():
    data = request.get_json()
    encrypted = cipher.encrypt(data['message'].encode()).decode()
    return jsonify({'encrypted': encrypted})

@app.route('/decrypt_message', methods=['POST'])
def decrypt_message():
    data = request.get_json()
    try:
        decrypted = cipher.decrypt(data['message'].encode()).decode()
        return jsonify({'decrypted': decrypted})
    except Exception:
        return jsonify({'decrypted': '[Decryption Failed]'}), 400

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)

