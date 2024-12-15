import os
import signal
import subprocess
import random
from flask import Flask, render_template_string, request, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename

app = Flask(__name__)
socketio = SocketIO(app)

# Global variables to store messages, users, and IPs
messages = []
active_users = {}
user_ips = {}
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# HTML template for the chat application
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DedSec's Chat</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
    <style>
        body { font-family: Arial, sans-serif; }
        #messages { height: 300px; overflow-y: scroll; border: 1px solid gray; margin-bottom: 10px; }
        .user-message { color: green; } /* User's own messages */
        .other-message { color: white; } /* Other users' messages */
        @media (prefers-color-scheme: dark) {
            body { background-color: black; color: white; }
            #messages { border-color: lightgray; }
        }
        @media (prefers-color-scheme: light) {
            body { background-color: white; color: black; }
            #messages { border-color: darkgray; }
        }
    </style>
</head>
<body>
    <h1>DedSec's Chat</h1>
    <div id="messages"></div>
    <input id="message" placeholder="Message..." />
    <button onclick="sendMessage()">Send</button>
    <input type="file" id="fileInput" />
    <button onclick="sendFile()">Send File</button>

    <script>
        var socket = io.connect(window.location.origin);
        var nickname = '';

        socket.on('message', function(msg) {
            document.getElementById('messages').innerHTML += msg;
        });

        socket.on('file', function(fileLink) {
            document.getElementById('messages').innerHTML += `<div><a href="${fileLink}" target="_blank">Download File</a></div>`;
        });

        if (localStorage.getItem('nickname')) {
            nickname = localStorage.getItem('nickname');
            socket.emit('join', nickname);
        } else {
            nickname = prompt("Please enter your nickname:", "User");
            if (nickname) {
                localStorage.setItem('nickname', nickname);
                socket.emit('join', nickname);
            }
        }

        function sendMessage() {
            var msg = document.getElementById('message').value;
            if (msg.trim() !== '') {
                socket.emit('message', msg);
                document.getElementById('message').value = '';
            }
        }

        function sendFile() {
            var fileInput = document.getElementById('fileInput');
            if (fileInput.files.length > 0) {
                var file = fileInput.files[0];
                var formData = new FormData();
                formData.append('file', file);

                fetch('/upload', {
                    method: 'POST',
                    body: formData
                }).then(response => response.text()).then(link => {
                    socket.emit('file', link);
                });
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file uploaded', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return f"/uploads/{filename}"

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@socketio.on('join')
def handle_join(nickname):
    active_users[request.sid] = nickname
    user_ips[request.sid] = request.remote_addr
    emit('message', f"{nickname} has joined the chat.", broadcast=True)
    for msg in messages:
        emit('message', msg)

@socketio.on('message')
def handle_message(msg):
    nickname = active_users.get(request.sid, "Unknown User")
    sanitized_msg = msg.replace("<", "&lt;").replace(">", "&gt;")
    message_with_nickname = f"<div class='other-message'>{nickname}: {sanitized_msg}</div>"
    messages.append(message_with_nickname)
    emit('message', message_with_nickname, broadcast=True)

@socketio.on('file')
def handle_file(file_link):
    emit('file', file_link, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in active_users:
        nickname = active_users.pop(request.sid, "Unknown User")
        user_ips.pop(request.sid, None)
        emit('message', f"{nickname} has left the chat.", broadcast=True)

def get_random_port():
    return random.randint(1024, 65535)

def main():
    port = get_random_port()
    socketio.run(app, host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()

