import os
import subprocess
import threading
import time
from flask import Flask, render_template_string, request, redirect, send_from_directory

# Ensure the Database folder exists
if not os.path.exists("Database"):
    os.makedirs("Database")

# Function to kill processes using the specified port
def kill_port(port):
    try:
        subprocess.call(['fuser', '-k', f'{port}/tcp'])
        time.sleep(1)  # Give some time for port cleanup
    except Exception as e:
        print(f"Error killing port {port}: {e}")

# Function to start Serveo tunnel and return URL
def start_serveo_tunnel(port):
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
                    print(f"Serveo tunnel started. You can access the application via the provided Serveo URL: {line}")
    except Exception as e:
        print(f"Error starting Serveo tunnel: {e}")

# Function to start Flask app
def start_flask_app(port):
    app.run(host="0.0.0.0", port=port)

# Set port number
port = 5002  # Changed to a different port

# Kill any existing process using the port
kill_port(port)

# Start Serveo tunnel in a separate thread
serveo_thread = threading.Thread(target=start_serveo_tunnel, args=(port,))
serveo_thread.start()

# Start Flask app
app = Flask(__name__)

# HTML template for the web interface
html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DedSec Database</title>
    <style>
        body {
            background-color: #000000; /* Dark black background */
            color: #00ff00; /* Green text */
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            overflow-y: auto; /* Enable vertical scrolling */
        }
        .container {
            background-color: #1a1a1a;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.7);
            width: 100%;
            max-width: 600px; /* Center and limit the max-width */
            box-sizing: border-box; /* Include padding and border in element's total width and height */
        }
        h1 {
            color: #00ff00;
            text-align: center; /* Center the title */
        }
        .file-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 20px;
        }
        .file-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px;
            background-color: #333;
            border-radius: 5px;
            overflow: hidden;
        }
        .file-item span {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-size: 0.9em; /* Adjust size as needed */
        }
        .buttons {
            display: flex;
            gap: 10px;
        }
        .button {
            background-color: #000;
            color: #00ff00; /* Green text */
            border: none;
            padding: 8px 12px;
            cursor: pointer;
            border-radius: 5px;
            text-decoration: none; /* Remove underline from links */
        }
        .button:hover {
            background-color: #333;
        }
        .upload-form, .search-form {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-top: 20px;
        }
        input[type="file"], input[type="search"] {
            margin-bottom: 10px;
        }
        input[type="submit"] {
            background-color: #000;
            color: #00ff00;
            border: none;
            padding: 10px 20px;
            cursor: pointer;
            border-radius: 5px;
        }
        input[type="submit"]:hover {
            background-color: #333;
        }
        .error {
            color: #ff0000; /* Red color for errors */
            font-size: 1em;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>DedSec Database</h1>
        <form class="upload-form" action="/upload" method="POST" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <input type="submit" value="Upload File">
        </form>
        <form class="search-form" action="/" method="GET">
            <input type="search" name="query" placeholder="Search files..." value="{{ request.args.get('query', '') }}">
            <input type="submit" value="Search">
        </form>
        <div class="file-list">
            {% if files %}
                {% for filename in files %}
                <div class="file-item">
                    <span>{{ filename }}</span>
                    <div class="buttons">
                        <a href="/download/{{ filename }}" class="button" download>Download</a>
                        <a href="/delete/{{ filename }}" class="button" onclick="return confirm('Are you sure you want to delete this file?')">Delete</a>
                    </div>
                </div>
                {% endfor %}
            {% elif request.args.get('query') %}
                <div class="error">File Doesn't Exist</div>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

@app.route("/", methods=["GET"])
def index():
    query = request.args.get('query', '')
    if query:
        files = [f for f in os.listdir("Database") if query.lower() in f.lower()]
        files.sort()  # Sort files alphabetically
        if not files:
            return render_template_string(html_template, files=None)
        return render_template_string(html_template, files=files)
    else:
        return render_template_string(html_template, files=os.listdir("Database"))

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return render_template_string(html_template, files=os.listdir("Database"), error="No file part")
    file = request.files['file']
    if file.filename == '':
        return render_template_string(html_template, files=os.listdir("Database"), error="No selected file")
    try:
        file.save(os.path.join("Database", file.filename))
        return redirect("/")
    except Exception as e:
        return render_template_string(html_template, files=os.listdir("Database"), error=f"Error saving file: {e}")

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    try:
        return send_from_directory("Database", filename, as_attachment=True)
    except Exception as e:
        return render_template_string(html_template, files=os.listdir("Database"), error=f"Error downloading file: {e}")

@app.route("/delete/<filename>", methods=["GET"])
def delete_file(filename):
    file_path = os.path.join("Database", filename)
    if os.path.isfile(file_path):
        try:
            os.remove(file_path)
            return redirect("/")
        except Exception as e:
            return render_template_string(html_template, files=os.listdir("Database"), error=f"Error deleting file: {e}")
    return render_template_string(html_template, files=os.listdir("Database"), error="File not found")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
