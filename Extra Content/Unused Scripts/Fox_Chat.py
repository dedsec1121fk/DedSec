import os
import signal
import subprocess
import random
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, disconnect

app = Flask(__name__)
socketio = SocketIO(app)

# Global variables to store messages, users, IPs, and chat room settings.
messages = []
active_users = {}
user_ips = {}

# Chat room limits and admin identification.
allowed_users_count = 8  # Default allowed users.
admin_id = None  # Will be set once the first user joins.

# Updated HTML template for the chat application without file sharing.
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
        .user-message { color: green; }
        .other-message { color: white; }
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

    <script>
        var socket = io.connect(window.location.origin);
        var nickname = '';

        socket.on('message', function(msg) {
            document.getElementById('messages').innerHTML += msg;
        });

        // Only the first user (admin) will receive this event.
        socket.on('prompt_limit', function(defaultLimit) {
            var newLimit = prompt("You are the first user. Enter allowed number of chat participants:", defaultLimit);
            if(newLimit && !isNaN(newLimit)) {
                socket.emit("set_limit", parseInt(newLimit));
            }
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
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@socketio.on('join')
def handle_join(nickname):
    global admin_id, allowed_users_count
    if len(active_users) >= allowed_users_count:
        emit('message', "<div class='other-message'>Chat room limit reached. Please try again later.</div>")
        disconnect()
        return

    active_users[request.sid] = nickname
    user_ips[request.sid] = request.remote_addr

    if admin_id is None:
        admin_id = request.sid
        emit('prompt_limit', allowed_users_count)

    emit('message', f"<div class='other-message'>{nickname} has joined the chat.</div>", broadcast=True)
    for msg in messages:
        emit('message', msg)

@socketio.on("set_limit")
def handle_set_limit(new_limit):
    global allowed_users_count
    if request.sid == admin_id:
        allowed_users_count = new_limit
        emit('message', f"<div class='other-message'>Admin has set the chat limit to {allowed_users_count} users.</div>", broadcast=True)

@socketio.on('message')
def handle_message(msg):
    nickname = active_users.get(request.sid, "Unknown User")
    sanitized_msg = msg.replace("<", "&lt;").replace(">", "&gt;")
    message_with_nickname = f"<div class='other-message'>{nickname}: {sanitized_msg}</div>"
    messages.append(message_with_nickname)
    emit('message', message_with_nickname, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    global admin_id
    if request.sid in active_users:
        nickname = active_users.pop(request.sid, "Unknown User")
        user_ips.pop(request.sid, None)
        emit('message', f"<div class='other-message'>{nickname} has left the chat.</div>", broadcast=True)
        if request.sid == admin_id:
            admin_id = None

def get_random_port():
    return random.randint(1024, 65535)

def main():
    port = get_random_port()
    socketio.run(app, host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()
