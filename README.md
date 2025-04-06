# DedSec Project

**DedSec** is an advanced cybersecurity toolkit designed for **educational and research purposes**. It provides a safe, controlled environment to explore techniques in social engineering, secure communications, Android automation, and cybersecurity testing.

**Disclaimer:** This project is intended for educational use only. Unauthorized use of these tools is strictly prohibited.

---

## Overview

DedSec offers a collection of Python scripts that cover a wide range of functionalities—from managing Android applications and file systems to simulating phishing pages and voice-authenticated games. The toolkit is built to run on Android devices via Termux, requiring a modest amount of storage and memory, and includes a series of interactive, terminal-based applications.

---

## Installation & Setup

### Requirements
- **Device:** Android device with [Termux](https://f-droid.org/) installed.
- **Storage:** Minimum **6GB** of free space.
- **RAM:** Minimum **2GB**.

### Step-by-Step Installation

1. **Install Termux and Add-Ons**
   - Download Termux from [F-Droid](https://f-droid.org/).
   - Install required add-ons: Termux:API, Termux:Styling.

2. **Run Setup Commands**

   First, open your Termux terminal and run the following command to set up storage, update packages, and install the required tools:

   ```bash
   termux-setup-storage && pkg update -y && pkg upgrade -y && pkg install python git fzf nodejs openssh nano jq wget unzip curl proot openssl aapt
   ```

   Then, install the necessary Python dependencies:

   ```bash
   pip install flask blessed flask-socketio werkzeug requests datetime geopy pydub pycryptodome
   ```

3. **Clone the Repository**
   ```bash
   git clone https://github.com/dedsec1121fk/DedSec.git
   ```

4. **Choose Menu Style**
   ```bash
   cd DedSec/Scripts && python settings.py
   ```
   > **Tip:** You can always open the menu later by typing `m` in your Termux terminal.

5. **Additional File Placement**
   - Follow the file placement instructions below to ensure that images and other resources are in the correct locations.

---

## File & Image Placement Instructions

- **Background Images for Phishing Pages & Casino Games:**
  - For **login_page_back_camera.py** and **login_page_front_camera.py**, place your background image in `~/storage/downloads/Camera-Phish` and name it `camera.jpg`.
  - For **login_page_location.py**, place your background image in `~/storage/downloads/LocationData` and name it `locate.jpg`.
  - For **dedslot_front_camera.py**, **dedslot_location.py**, and **dedslot_microphone.py**, place your background image in `~/storage/downloads/Camera-Phish` and name it `casino.jpg`.

- **Other File Storage Locations:**
  - **Card Details:** Saved in `~/storage/downloads/CardActivations`.
  - **Location Data:** Saved in `~/storage/downloads/LocationData`.
  - **Audio Recordings:** Saved in `~/storage/downloads/Recordings`.
  - **Radio Streaming:** Expects radio station folders in `~/DedSec/Radio`.
  - **File Management (dedsec_database.py):** Uses a folder named `Database` in the current working directory.
  - **Chat Applications (dedsecs_chats.py & fox_chat.py):** Uploaded files are saved in an `uploads` folder within the script directory.

---

## Scripts & Their Functionalities

Below is a summary of each script provided in the DedSec toolkit:

1. **android_app_launcher.py**  
   - Retrieves a comprehensive list of installed Android apps using system commands.
   - Filters out apps that are launchable and displays them in an interactive interface for efficient searching, selection, launching, detailed viewing, or uninstallation.

2. **card_details.py**  
   - Simulates a realistic credit card verification page.
   - Captures key details such as card type (Visa, Mastercard, etc.), cardholder name, card number, expiration date, and CVV.
   - Saves the collected data securely on the device.

3. **dedsec_database.py**  
   - Provides a web-based file management system.
   - Enables uploading, downloading, searching, and deletion of files.
   - Remote access is supported through a Serveo tunnel.

4. **dedsec_file_manager.py**  
   - A terminal-based file manager using a curses-based interface.
   - Allows operations like opening, deleting, renaming, copying, moving files, and navigating directories.
   - Includes an interactive menu for streamlined file management.

5. **dedsec_music_player.py**  
   - A terminal-based music player designed for Termux.
   - Automatically identifies music folders and supports multiple audio file formats.
   - Features controls such as play, pause, next, previous, shuffle, and stop.

6. **dedsecs_chats.py**  
   - A real-time chat application built with Flask-SocketIO.
   - Facilitates anonymous messaging and file sharing while keeping a history of conversations.

7. **dedslot_front_camera.py**  
   - A slot machine-style game that uses the front camera (selfie camera) to guess the user’s age.
   - Captures images at regular intervals while displaying a casino-like interface.

8. **dedslot_location.py**  
   - Uses the device’s GPS to determine the current location.
   - Validates the legality of gambling activities by checking the user’s state.

9. **dedslot_microphone.py**  
   - Incorporates voice authentication in a gaming context.
   - Records a brief audio sample, converts it from WebM to WAV, and rewards additional free spins based on successful conversion.

10. **fox_chat.py**  
    - An alternative real-time chat application.
    - Supports instant messaging and file sharing with robust reconnection handling during network disruptions.

11. **link_generator.py**  
    - Converts a local-only web address to a public URL.
    - Uses cloudflared and a Serveo tunnel to obtain and display the new public URL.

12. **login_page_back_camera.py**  
    - Creates a phishing-style login page that mimics legitimate interfaces.
    - Activates the back camera to capture photos while the user enters their credentials.
    - Archives the captured images and the sensitive login data.

13. **login_page_front_camera.py**  
    - Similar to the back camera version but uses the front (selfie) camera.
    - Captures images at two-second intervals while logging keystrokes and credentials.

14. **login_page_location.py**  
    - Mimics a genuine login page to capture user credentials.
    - Silently retrieves the device’s GPS coordinates to determine and save the user’s address.

15. **login_page_microphone.py**  
    - Presents a deceptive login interface.
    - Activates the device’s microphone to record short audio snippets while the user logs in.
    - Saves the recordings as audio files.

16. **one_free_sms_per_day.py**  
    - Sends one free SMS per day using an online service.
    - Prompts for the country code, phone number, and message content before sending.

17. **radio.py**  
    - Functions as an offline radio by listing files from a designated folder.
    - Allows the user to select and stream audio files as if tuning into a radio station.

18. **settings.py**  
    - Provides system information including hardware specs and storage details.
    - Manages repository and package updates.
    - Offers customization for the Termux interface, such as color themes,promt name and menu style.

19. **text_encryptor_and_decryptor.py**  
    - A terminal-based utility for encrypting and decrypting text.
    - Uses AES-256-GCM encryption with a user-provided password (minimum 8 characters) and PBKDF2 key derivation.
    - Features a curses-based menu for easy operation.

---

## Legal & Ethical Notice

**Disclaimer & Legal Notice:**

- **Educational & Research Use:**  
  This toolkit is provided exclusively for educational, research, and ethical security testing purposes in controlled environments. All tools are intended solely for learning and should only be used on systems where you have explicit authorization.

- **Prohibited Uses:**  
  The use, reproduction, or distribution of any part of this toolkit for unauthorized, malicious, or illegal activities—including unauthorized system access, data breaches, identity theft, or fraud—is strictly prohibited. Misuse may result in severe civil and criminal penalties.

- **User Responsibility:**  
  By using this toolkit, you agree that you are solely responsible for ensuring your actions comply with all applicable local, national, and international laws, regulations, and policies. Secure explicit permission from system owners before conducting any security assessments or tests.

- **Liability Disclaimer:**  
  The authors, contributors, and distributors of this toolkit disclaim all liability for any direct, indirect, incidental, or consequential damages arising from its use or misuse.

- **Ethical Standards:**  
  You are expected to adhere to ethical hacking guidelines. Always act with integrity and respect privacy. Use these tools only in environments where you have documented permission.

- **Export/Import Controls:**  
  This repository may be subject to export and import control laws. It is your responsibility to ensure compliance with all such legal restrictions when using or transferring any part of this software.

- **Consult Legal Counsel:**  
  If you have any doubts regarding the legal implications of using these tools in your jurisdiction or for your intended purpose, please consult a qualified legal professional.