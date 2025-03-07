# DedSec Project

**DedSec** is a cybersecurity toolkit designed for educational and research purposes. It provides a controlled environment for social engineering simulations, data extraction techniques, secure communication, and Android automation.

---

## Features

### Phishing Simulations
- **Camera Phishing:** Automatically captures images using both front and back cameras.
- **Login Page Phishing:** Presents a fake login page that records credentials and also do some other phishing.
- **Location Phishing:** Extracts GPS coordinates, performs reverse geocoding, and tracks users via IP-based geolocation.
- **Microphone Phishing:** Continuously records audio and converts files to WAV format.

### Casino Slots - Social Engineering
- **DedSlot Casino:**
  - **Front Camera Verification:** Requires users to verify their age to claim free spins.
  - **Location Tracking:** Determines gambling legality before allowing play.
  - **Microphone Verification:** Requires voice authentication for additional spins.
  - **Rigged Spins:** Ensures users can never win the jackpot.

### Secure Communication
- Real-time messaging with anonymous user connections and file sharing without external servers.

### Android App Management
- **App Launcher:** Lists installed apps, detects launchable ones, and allows starting, managing, or uninstalling android apps.

### Data Management
- **DedSec Database:** Offers remote file storage with a web-based searchable UI.
  - **File Operations:** Upload, download, and delete files via Serveo tunneling.
  - **Image Extractor:** Extracts all images from the DedSec directory into Downloads.
  - **Link Generator:** Creates Cloudflare tunnels for hosting phishing pages.

### Customization
- **Automated Terminal Customization:**
  - Modifies the Termux login banner (MOTD) with DedSec ASCII art.
  - Updates the Bash prompt (PS1) for a hacker-style terminal.

### Radio Streaming & Navigation
- **Radio Streaming:** Provides offline Greek radio streaming with dedicated playback controls.
- **Interactive Menu:** Simplifies navigation to access all DedSec tools.
- **Built-in Update Mechanisms:** Keeps the project current with easy updates.

---

## Getting Started

### Requirements
- **Device:** Compatible with all Android devices.
- **Storage:** At least 3GB of free space.
- **RAM:** Minimum 2GB.

### Installation

1. **Install Termux**
   - Download Termux from [F-Droid](https://f-droid.org/).

2. **Install Termux Add-Ons**
   - Termux:API
   - Termux:Styling

3. **Run the Setup Commands**

   Open Termux and execute the following commands:

       termux-setup-storage
       pkg update -y
       pkg upgrade -y
       pkg install python
       pkg install python-pip
       pkg install openssh
       pkg install nodejs
       pkg install termux-api
       pkg install git
       pkg install curl
       pkg install requests
       pkg install termux-media-player
       pkg install nano
       pkg install jq
       pkg install wget
       pkg install proot
       pkg install openssl
       pkg install php
       pkg install clang
       pkg install openssl-tool
       pkg install libjpeg-turbo
       pkg install ffmpeg
       pkg install tmux
       pkg install unzip
       pkg install termux-auth
       pkg install termux-services
       pkg install cloudflared
       pip install flask flask-socketio werkzeug base64 datetime re subprocess signal random threading time os flask-cors termux-wake-lock sshd

4. **Launch the Interactive Menu**

   Navigate to the DedSec Scripts directory and start the menu:

       cd DedSec/Scripts && python menu.py

   > **Note:** Ensure that the required images (e.g., `camera.jpg`, `casino.jpg`, `record.jpg`, `locate.jpg`) are placed in their respective folders within your Downloads directory for full functionality,also you can start the menu by typing m anywhere inside your Termux environment.

---

## Legal & Ethical Notice

This toolkit is provided for **educational purposes only**. Always use these tools in a controlled environment with explicit permission. The authors assume no responsibility for any misuse.

---

Enjoy exploring DedSec responsibly!
