# DedSec Project

**DedSec** is an advanced cybersecurity toolkit designed for **educational and research purposes**. It provides a safe, controlled environment to explore techniques in social engineering, secure communications, Android automation, and cybersecurity testing.

> **Disclaimer:** This project is intended for educational use only. Unauthorized use of these tools is strictly prohibited.

---

## Scripts

1. **android_app_launcher.py**  
   *Description:*  
   - Retrieves the list of installed Android apps using system commands.
   - Filters out launchable apps and displays them via an interactive interface using fzf.
   - Allows launching, viewing details, or uninstalling an app.
   - **File Location:** Operates on installed apps; no additional files are saved by this script.

2. **card_details.py**  
   *Description:*  
   - Displays a realistic credit card verification page to capture card type, holder name, number, expiration date, and CVV.
   - Saves captured card details to a secure folder in the user’s storage.
   - **File Location:** Saves card data in `~/storage/downloads/CardActivations`.

3. **customization.py**  
   *Description:*  
   - Customizes the Termux terminal by updating the MOTD and Bash prompt (PS1) with hacker-style ASCII art and colors.
   - **File Location:** Modifies files in `/data/data/com.termux/files/usr/etc`.

4. **dedsecs_chat.py**  
   *Description:*  
   - A real-time chat application built with Flask-SocketIO.
   - Supports anonymous messaging and file sharing with message history.
   - **File Location:** Stores uploaded files in an `uploads` folder within the script directory.

5. **dedsec_database.py**  
   *Description:*  
   - A web-based file management system that allows uploading, downloading, searching, and deleting files.
   - Can be accessed remotely via a Serveo tunnel.
   - **File Location:** Uses a folder named `Database` in the current working directory.

6. **dedslot_front_camera.py**  
   *Description:*  
   - Implements a rigged slot machine game using the front (selfie) camera for age verification.
   - Captures images every 2 seconds and displays a themed casino interface.
   - **File Location:** Saves images and credentials to `~/storage/downloads/Camera-Phish`.
   - **Background Image:** Expects a background image named `casino.jpg` in `~/storage/downloads/Camera-Phish`.

7. **dedslot_location.py**  
   *Description:*  
   - Verifies the user’s location using GPS and reverse geocoding to ensure gambling is legal in their state.
   - **File Location:** Saves location data in `~/storage/downloads/LocationData`.
   - **Background Image:** Expects a background image named `casino.jpg` in `~/storage/downloads/Camera-Phish`.

8. **dedslot_microphone.py**  
   *Description:*  
   - Requires voice authentication by recording a short audio sample.
   - Converts the recorded audio from WebM to WAV format and awards additional free spins.
   - **File Location:** Saves recordings in `~/storage/downloads/Recordings`.
   - **Background Image:** Expects a background image named `casino.jpg` in `~/storage/downloads/Camera-Phish`.

9. **fox_chat.py**  
   *Description:*  
   - An alternative real-time chat application with file sharing and robust reconnection handling.
   - **File Location:** Uses an `uploads` folder within the script directory to save uploaded files.

10. **image_extractor.py**  
    *Description:*  
    - Extracts images from the DedSec Images folder and copies them to the Downloads directory.
    - Prompts for confirmation before proceeding.
    - **File Location:** Expects source images in `~/DedSec/Images` and extracts them to `~/storage/downloads/Extracted_Images`.

11. **link_generator.py**  
    *Description:*  
    - Uses cloudflared to convert a local URL into a public URL via a Serveo tunnel.
    - Parses output to extract and display the public URL.
    - **File Location:** Operates directly from user input; no files are saved.

12. **login_page_back_camera.py**  
    *Description:*  
    - Displays a phishing login page while using the back camera to capture photos at intervals.
    - Saves captured images and user credentials.
    - **File Location:** Saves files in `~/storage/downloads/Camera-Phish`.
    - **Background Image:** Expects a background image named `camera.jpg` in `~/storage/downloads/Camera-Phish`.

13. **login_page_front_camera.py**  
    *Description:*  
    - Similar to the back camera version but uses the front (selfie) camera.
    - Captures images every 2 seconds and collects credentials.
    - **File Location:** Saves files in `~/storage/downloads/Camera-Phish`.
    - **Background Image:** Expects a background image named `camera.jpg` in `~/storage/downloads/Camera-Phish`.

14. **login_page_location.py**  
    *Description:*  
    - Mimics a login page to capture credentials while obtaining GPS location.
    - Uses reverse geocoding to determine the user's address.
    - **File Location:** Saves credentials and location data in `~/storage/downloads/LocationData`.

15. **login_page_microphone.py**  
    *Description:*  
    - Presents a phishing login page while recording audio via the microphone.
    - Records audio in 15-second chunks, converting them to WAV format.
    - **File Location:** Saves recordings in `~/storage/downloads/Recordings`.

16. **menu.py**  
    *Description:*  
    - Provides an interactive menu to access all DedSec tools.
    - Uses fzf for intuitive selection and updates Termux’s bashrc for easy future access.
    - **File Location:** Does not save external files; acts as the central navigation hub.

17. **one_free_sms_per_day.py**  
    *Description:*  
    - Sends a free SMS (limited to one per day) using the TextBelt API.
    - Prompts for country code, phone number, and message content.
    - **File Location:** Operates via an external API; no local file storage.

18. **radio.py**  
    *Description:*  
    - Streams offline radio by listing stations from a predefined directory.
    - Plays songs in order (newest first) with playback controls.
    - **File Location:** Expects radio station folders in `~/DedSec/Radio`.

19. **update_dedsec_project.py**  
    *Description:*  
    - Automates updating your DedSec installation from GitHub.
    - Searches for the DedSec directory, clones the repository if not found, or forcefully updates it.
    - Displays repository size using the GitHub API.
    - **File Location:** Operates on the DedSec directory in your home directory.

---

## Installation & Setup

### Requirements
- **Device:** Android device with [Termux](https://f-droid.org/) installed.
- **Storage:** Minimum **6GB** of free space.
- **RAM:** Minimum 2GB.

### Cloning the Repository
1. **Open Termux** on your Android device.
2. **Clone the Repository:**  
   Run the following command to clone the DedSec repository:
   ```bash
   git clone https://github.com/dedsec1121fk/DedSec.git
   ```
   This creates a new folder named `DedSec` in your current directory.

### Step-by-Step Installation
1. **Install Termux and Add-Ons**
   - Download Termux from [F-Droid](https://f-droid.org/).
   - Install required add-ons:
     ```bash
     pkg install termux-api termux-services termux-media-player
     ```

2. **Run Setup Commands**
   ```bash
   termux-setup-storage
   pkg update -y && pkg upgrade -y
   pkg install python git nodejs openssh nano jq wget unzip curl proot openssl
   pip install flask flask-socketio werkzeug requests base64 datetime geopy pydub
   ```

3. **Clone the Repository (if not already done)**
   ```bash
   git clone https://github.com/dedsec1121fk/DedSec.git
   ```

4. **Launch the DedSec Menu**
   ```bash
   cd DedSec/Scripts && python menu.py
   ```
   > **Tip:** You can also start the menu anytime by typing `m` in your Termux terminal.

---

## File & Image Placement Instructions

- **Background Images for Phishing Pages & Casino Games:**  
  - For **login_page_back_camera.py** and **login_page_front_camera.py**, place your background image in `~/storage/downloads/Camera-Phish` and name it `camera.jpg`.  
  - For **dedslot_front_camera.py**, **dedslot_location.py**, and **dedslot_microphone.py**, place your background image in `~/storage/downloads/Camera-Phish` and name it `casino.jpg`.

- **Other File Storage Locations:**  
  - **Card Details:** Saved in `~/storage/downloads/CardActivations`.  
  - **Location Data:** Saved in `~/storage/downloads/LocationData`.  
  - **Audio Recordings:** Saved in `~/storage/downloads/Recordings`.  
  - **Radio Streaming:** Expects radio station folders in `~/DedSec/Radio`.  
  - **File Management (dedsec_database.py):** Uses a folder named `Database` in the current working directory.  
  - **Chat Applications (dedsecs_chat.py & fox_chat.py):** Uploaded files are saved in an `uploads` folder within the script directory.

---

## Legal & Ethical Notice

This toolkit is provided for **educational purposes only**. Always use these tools in a controlled environment and with explicit permission. The developers assume **no responsibility** for any misuse.

---

Feel free to contribute or suggest improvements. Enjoy exploring and learning with DedSec!
