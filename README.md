DedSec Project Overview

The DedSec project is a collection of tools and scripts designed for cybersecurity research and educational purposes. Each component demonstrates various techniques—ranging from deceptive permission requests to data extraction. Use these tools responsibly and only in controlled, authorized environments.

Project Features

1. blank_page_back_camera.py

Purpose: Demonstrates how a minimal webpage can trick users into granting back-camera access.

Key Functions: 

Generates a nearly blank webpage.

Requests permission for the device’s back camera.

Captures images or video streams once access is granted.

2. blank_page_front_camera.py

Purpose: Similar to the back camera script, but targets the front camera.

Key Functions: 

Displays a blank or innocuous page.

Requests front-camera permission.

Captures snapshots or video streams upon user consent.

3. blank_page_location.py

Purpose: Shows how a minimal webpage can gather geolocation data.

Key Functions: 

Uses HTML5/browser APIs to request geolocation.

Logs latitude, longitude, and additional metadata.

Stores or transmits the collected location data.

4. blank_page_microphone.py

Purpose: Demonstrates risks associated with deceptive microphone permission requests.

Key Functions: 

Presents a plain webpage.

Requests access to the microphone.

Records and saves audio once permission is approved.

5. customization.py

Purpose: Allows users to modify DedSec project settings and interface elements.

Key Functions: 

Updates visual styles, color schemes, and terminal prompts.

Persists user preferences.

Offers options to rollback to default settings.

6. dedsec_database.py

Purpose: Manages data storage and retrieval within the project.

Key Functions: 

Performs CRUD (Create, Read, Update, Delete) operations.

Interacts with lightweight databases (e.g., SQLite).

Maintains data integrity for project scripts.

7. dedsecs_chat.py

Purpose: Implements a secure, real-time chat system.

Key Functions: 

Uses socket connections or web-based interfaces.

May incorporate encryption for message protection.

Supports multi-user channels or group discussions.

8. dedslot_front_camera.py

Purpose: Offers advanced or stealth methods for front-camera capture.

Key Functions: 

Integrates additional checks or triggers before activation.

Stores or transmits captured media.

Incorporates obfuscation to reduce detection.

9. dedslot_location.py

Purpose: Provides enhanced techniques for gathering geolocation data.

Key Functions: 

Utilizes browser prompts, IP-based geolocation, or combined methods.

Logs precise coordinates and timestamps.

May include stealth or automation features.

10. dedslot_microphone.py

Purpose: Demonstrates advanced methods for capturing audio.

Key Functions: 

Incorporates hidden triggers or timing intervals.

Records audio and saves it locally or remotely.

Uses techniques to minimize user suspicion.

11. fox_chat.py

Purpose: An alternative chat platform using a different framework or protocol.

Key Functions: 

May employ unique encryption algorithms.

Supports multi-user sessions, direct messages, or broadcasts.

Focuses on performance and scalability.

12. image_extractor.py

Purpose: Automates bulk image retrieval for archiving or analysis.

Key Functions: 

Parses directories, websites, or data streams.

Filters images by file type or metadata.

Saves extracted images to a designated folder.

13. link_generator.py

Purpose: Creates customizable links for sharing, phishing simulations, or redirection.

Key Functions: 

Generates short or random URLs.

Tracks link usage and user interactions.

May integrate with third-party URL-shortening APIs.

14. login_page_back_camera.py

Purpose: Mimics a realistic login page while secretly activating the back camera.

Key Functions: 

Displays a convincing login interface.

Requests back-camera access in the background.

Captures video or images without user awareness.

15. login_page_front_camera.py

Purpose: Similar to the previous script, but targets the front camera.

Key Functions: 

Imitates a legitimate sign-in page.

Captures images or video from the front camera.

May log credentials alongside camera data.

16. login_page_location_hacker.py

Purpose: Uses a fake login page to collect geolocation data.

Key Functions: 

Leverages browser geolocation prompts or IP-based methods.

Logs user coordinates during the login process.

May combine location data with submitted credentials.

17. login_page_microphone.py

Purpose: Records microphone audio while displaying a deceptive login form.

Key Functions: 

Embeds microphone permission requests in the login flow.

Records audio once access is granted.

Potentially merges audio data with typed credentials.

18. menu.py

Purpose: Provides an interactive menu for launching DedSec tools.

Key Functions: 

Detects and lists available Python scripts.

Uses fzf for smooth navigation.

Updates Termux’s bashrc to auto-launch the menu at startup.

19. one_free_sms_per_day.py

Purpose: Demonstrates automated SMS sending for notifications or social engineering tests.

Key Functions: 

Integrates with an online SMS API.

Limits to one message per day.

Logs delivery status and errors.

20. radio.py

Purpose: Streams or plays radio content, with a focus on offline Greek stations.

Key Functions: 

Accesses pre-downloaded or live radio feeds.

Offers basic playback controls (play, pause, stop).

Allows switching between multiple stations.

21. update_dedsec_project.py

Purpose: Checks for and applies updates to keep the project current.

Key Functions: 

Verifies version numbers or file checksums.

Downloads and installs updates from a central repository.

Summarizes changes and improvements.

22. android_app_launcher.py

Purpose: Manages and launches installed Android applications from Termux.

Key Functions: 

Retrieves a list of installed apps with their APK paths.

Extracts friendly app labels using aapt.

Presents an interactive menu to Launch, view App Info, or Uninstall an app.

Legal Warning and Disclaimer

No Warranty:
These tools are provided "as is" without any warranties. The authors disclaim liability for errors, malfunctions, or any damages resulting from the use of these scripts.

Ethical Use:

Do not use these tools to invade privacy or access devices without explicit permission.

Unauthorized access (camera, microphone, location, etc.) is illegal and unethical.

Educational Purpose:
These resources are meant for research and educational purposes only. Always obtain explicit consent before testing on any system.

Acknowledgment:
By using these materials, you agree that you are solely responsible for your actions and will comply with all applicable laws and ethical guidelines.

Requirements to Get Started

Device: Any Android device (with or without root).

Storage: At least 3GB of free internal storage.

RAM: Minimum of 2GB.

DedSec Installation Guide

Prerequisites

Install Termux:
Download Termux from F-Droid.

Install Termux Add-Ons:

Termux:API

Termux:Styling
(Both available on F-Droid.)

Installation Steps

Copy and paste the following commands into Termux to install the necessary packages:

termux-setup-storage pkg update -y pkg upgrade -y pkg install -y python python-pip openssh nodejs termux-api git curl requests termux-media-player nano jq wget proot openssl php clang openssl-tool libjpeg-turbo ffmpeg tmux unzip termux-auth termux-services cloudflared pip install flask flask-socketio werkzeug base64 datetime re subprocess signal random threading time os flask-cors termux-wake-lock sshd 

Running the Menu

After installation, launch the interactive menu with:

cd DedSec/Scripts && python menu.py 

This menu will automatically launch when opening Termux, making it easy to access all DedSec tools.

Note: Files are saved in named folders (e.g., Camera-Phish). For proper functionality, place specific images (e.g., camera.jpg, casino.jpg, record.jpg, locate.jpg) in the corresponding folders within your Download directory.

