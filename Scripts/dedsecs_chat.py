import os
import signal
import subprocess
import random
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

# Global variables to store messages, users, and IPs
messages = []
active_users = {}
user_ips = {}
max_users = 8  # Maximum number of users allowed
user_count = 0  # Current number of users

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
                // Emit the message to the server
                socket.emit('message', msg);
                // Clear input field
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
    global user_count
    if user_count < max_users:
        # Store nickname for the user with auto-numbering
        auto_number = user_count + 1
        nickname_with_number = f"{nickname} - {auto_number}"
        active_users[request.sid] = nickname_with_number
        user_ips[request.sid] = request.remote_addr  # Store user's IP
        user_count += 1
        emit('message', f"{nickname_with_number} has joined the chat.", broadcast=True)
        
        # Send existing message history to the newly joined user
        for msg in messages:
            emit('message', msg)
    else:
        emit('message', "Chat is full. Please try again later.")

@socketio.on('reconnect')
def handle_reconnect(nickname):
    global user_count
    if user_count < max_users:
        # Check if the user is already connected
        if request.sid not in active_users:
            auto_number = user_count + 1
            nickname_with_number = f"{nickname} - {auto_number}"
            active_users[request.sid] = nickname_with_number
            user_ips[request.sid] = request.remote_addr  # Store user's IP
            user_count += 1
            emit('message', f"{nickname_with_number} has rejoined the chat.", broadcast=True)
            
            # Send existing message history to the rejoining user
            for msg in messages:
                emit('message', msg)
        else:
            emit('message', "You are already connected.")
    else:
        emit('message', "Chat is full. Please try again later.")

@socketio.on('disconnect')
def handle_disconnect():
    global user_count
    if request.sid in active_users:
        nickname = active_users[request.sid]
        del active_users[request.sid]
        del user_ips[request.sid]  # Remove IP when user disconnects
        user_count -= 1
        emit('message', f"{nickname} has left the chat.", broadcast=True)

        # Check if there are no more users, clear the history
        if user_count == 0:
            clear_chat_history()  # Clear history when last user leaves

@socketio.on('message')
def handle_message(msg):
    # Sanitize message to prevent XSS attacks
    sanitized_msg = msg.replace("<", "&lt;").replace(">", "&gt;")
    nickname = active_users.get(request.sid, "Unknown User")
    message_with_nickname = f"<div class='other-message'>{nickname}: {sanitized_msg}</div>"
    messages.append(message_with_nickname)  # Store the message in the history
    emit('message', message_with_nickname, broadcast=True)

def cleanup():
    # Clear all data
    clear_chat_history()
    active_users.clear()
    user_ips.clear()

def start_serveo(port):
    """Start the Serveo process."""
    serveo_process = subprocess.Popen(
        ['ssh', '-R', f'80:localhost:{port}', 'serveo.net'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return serveo_process

def get_serveo_link(process):
    """Get the Serveo link from the output of the process."""
    while True:
        output = process.stdout.readline()
        if output == b"" and process.poll() is not None:
            break
        if output:
            decoded_output = output.decode('utf-8')
            if 'Forwarding' in decoded_output:
                # Extract and print the Serveo link
                link_start = decoded_output.find("https://")
                link_end = decoded_output.find(" ", link_start)
                link = decoded_output[link_start:link_end]
                print(f"Chat available at: {link}")
                break

def clear_chat_history():
    """Clear the chat history by resetting the messages list."""
    global messages
    messages.clear()  # Reset the messages list

def get_random_port():
    """Get a random port between 1024 and 65535."""
    return random.randint(1024, 65535)

def main():
    # Get a random port for the Flask app
    port = get_random_port()

    # Start the Serveo process with the specified port
    serveo_process = start_serveo(port)

    # Start the Flask app
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

