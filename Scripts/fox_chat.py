import os
import signal
import subprocess
import random
from flask import Flask, render_template_string, request, send_from_directory
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

# Global variables to store messages, users, and IPs
messages = []
active_users = {}
user_ips = {}
user_count = 0  # Current number of users (no limit now)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure upload folder exists

# HTML template for the chat application
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fox Chat</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
    <style>
        body { font-family: Arial, sans-serif; }
        #messages { height: 300px; overflow-y: scroll; border: 1px solid gray; margin-bottom: 10px; }
        .user-message { color: green; } /* User's own messages */
        .other-message { color: white; } /* Other users' messages */
        .file-message { color: blue; } /* File messages */
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
    <h1>Fox Chat</h1>
    <div id="messages"></div>
    <input id="message" placeholder="Message..." />
    <button onclick="sendMessage()">Send</button>
    <br><br>
    <input type="file" id="fileInput" />
    <button onclick="sendFile()">Send File</button>

    <script>
        var socket = io.connect(window.location.origin);
        var nickname = '';

        // Notify when a new message is received
        socket.on('message', function(msg) {
            document.getElementById('messages').innerHTML += msg;
        });

        // Check if nickname is saved in local storage
        if (localStorage.getItem('nickname')) {
            nickname = localStorage.getItem('nickname');
            socket.emit('reconnect', nickname);
        } else {
            // Prompt for nickname on connection
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
            var file = fileInput.files[0];
            if (file) {
                var formData = new FormData();
                formData.append("file", file);

                fetch("/upload", {
                    method: "POST",
                    body: formData
                }).then(response => response.json())
                  .then(data => {
                      if (data.success) {
                          socket.emit('file', data.file_url);
                      } else {
                          alert("File upload failed.");
                      }
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
        return {"success": False, "error": "No file part"}
    file = request.files['file']
    if file.filename == '':
        return {"success": False, "error": "No selected file"}
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    file_url = f"/uploads/{file.filename}"
    return {"success": True, "file_url": file_url}

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@socketio.on('join')
def handle_join(nickname):
    global user_count
    nickname_with_number = f"{nickname}"
    active_users[request.sid] = nickname_with_number
    user_ips[request.sid] = request.remote_addr  # Store user's IP
    user_count += 1
    emit('message', f"<div class='other-message'>{nickname_with_number} has joined the chat.</div>", broadcast=True)
    
    # Send existing message history to the newly joined user
    for msg in messages:
        emit('message', msg)

@socketio.on('reconnect')
def handle_reconnect(nickname):
    global user_count
    if request.sid not in active_users:
        nickname_with_number = f"{nickname}"
        active_users[request.sid] = nickname_with_number
        user_ips[request.sid] = request.remote_addr  # Store user's IP
        user_count += 1
        emit('message', f"<div class='other-message'>{nickname_with_number} has rejoined the chat.</div>", broadcast=True)
        
        # Send existing message history to the rejoining user
        for msg in messages:
            emit('message', msg)
    else:
        emit('message', "<div class='other-message'>You are already connected.</div>")

@socketio.on('disconnect')
def handle_disconnect():
    global user_count
    if request.sid in active_users:
        nickname = active_users[request.sid]
        del active_users[request.sid]
        del user_ips[request.sid]
        user_count -= 1
        emit('message', f"<div class='other-message'>{nickname} has left the chat.</div>", broadcast=True)

@socketio.on('message')
def handle_message(msg):
    sanitized_msg = msg.replace("<", "&lt;").replace(">", "&gt;")
    nickname = active_users.get(request.sid, "Unknown User")
    message_with_nickname = f"<div class='other-message'>{nickname}: {sanitized_msg}</div>"
    messages.append(message_with_nickname)
    emit('message', message_with_nickname, broadcast=True)

@socketio.on('file')
def handle_file(file_url):
    nickname = active_users.get(request.sid, "Unknown User")
    file_message = f"<div class='file-message'>{nickname} shared a file: <a href='{file_url}' target='_blank'>Download</a></div>"
    messages.append(file_message)
    emit('message', file_message, broadcast=True)

def cleanup():
    clear_chat_history()
    active_users.clear()
    user_ips.clear()

def start_serveo(port):
    serveo_process = subprocess.Popen(
        ['ssh', '-R', f'80:localhost:{port}', 'serveo.net'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return serveo_process

def get_serveo_link(process):
    while True:
        output = process.stdout.readline()
        if output == b"" and process.poll() is not None:
            break
        if output:
            decoded_output = output.decode('utf-8')
            if 'Forwarding' in decoded_output:
                link_start = decoded_output.find("https://")
                link_end = decoded_output.find(" ", link_start)
                link = decoded_output[link_start:link_end]
                print(f"Chat available at: {link}")
                break

def clear_chat_history():
    global messages
    messages.clear()

def get_random_port():
    return random.randint(1024, 65535)

def main():
    port = get_random_port()
    serveo_process = start_serveo(port)

    try:
        get_serveo_link(serveo_process)
        socketio.run(app, host='0.0.0.0', port=port)
    except Exception as e:
        print(f"Error starting server: {e}")
    finally:
        cleanup()
        serveo_process.kill()

if __name__ == '__main__':
    main()

