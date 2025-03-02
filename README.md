## DedSec Project

DedSec is a versatile cybersecurity toolkit for educational and research purposes. It demonstrates how deceptive web pages and scripts can simulate social engineering attacks, data extraction techniques, secure communication, and radio streaming—all within a controlled environment.

##What You Can Do

Phishing Simulations:
Create deceptive interfaces that request access to cameras, microphones, and geolocation data.

##Real-Time Communication:
Utilize built-in chat systems to explore secure messaging and understand risks related to unauthorized data access.

##Data Management:
Extract images, generate custom links, and manage information efficiently with automated tools.

##Customizations:
Personalize themes and settings to tailor the toolkit to your workflow.

##Radio Streaming:
Stream radio content, including offline Greek stations, with easy-to-use playback controls.

##Streamlined Navigation:
Access all DedSec tools via an interactive menu with built-in update mechanisms to keep the project current.

##Getting Started

Requirements

Device: Compatible with all Android devices

Storage: At least 3GB of free space

RAM: Minimum 2GB

Installation

Install Termux:
Download Termux from F-Droid.

Install Termux Add-Ons:

Termux:API

Termux:Styling

Run the Setup Commands:
Copy and paste the following commands into Termux:

''
termux-setup-storage pkg update -y && pkg upgrade -y pkg install -y python python-pip openssh nodejs termux-api git curl requests termux-media-player nano jq wget proot openssl php clang openssl-tool libjpeg-turbo ffmpeg tmux unzip termux-auth termux-services cloudflared pip install flask flask-socketio werkzeug base64 datetime re subprocess signal random threading time os flask-cors termux-wake-lock sshd 
''

Launch the Interactive Menu:

cd DedSec/Scripts && python menu.py 

This menu provides quick access to all DedSec tools.

Note: Place the required images (e.g., camera.jpg, casino.jpg, record.jpg, locate.jpg) in their respective folders within your Downloads directory for full functionality.

##Legal & Ethical Notice

This toolkit is provided for educational purposes only. Always use these tools in a controlled environment with explicit permission. The authors assume no responsibility for misuse.

##Enjoy exploring DedSec responsibly!
