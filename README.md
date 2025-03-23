# DedSec Project

**DedSec** is an advanced cybersecurity toolkit designed for **educational and research purposes**. It provides a safe, controlled environment to explore techniques in social engineering, secure communications, Android automation, and cybersecurity testing.

> **Disclaimer:** This project is intended for educational use only. Unauthorized use of these tools is strictly prohibited.

---

## Scripts

1. **android_app_launcher.py**  
   - Retrieves the list of installed Android apps using system commands.
   - Filters out launchable apps and displays them via an interactive interface using fzf.
   - Allows launching, viewing details, or uninstalling an app.

2. **card_details.py**  
   - Displays a realistic credit card verification page to capture card type, holder name, number, expiration date, and CVV.
   - Saves captured card details to a secure folder in the user’s storage.

3. **dedsecs_chat.py**  
   - A real-time chat application built with Flask-SocketIO.
   - Supports anonymous messaging and file sharing with message history.

4. **dedsec_database.py**  
   - A web-based file management system that allows uploading, downloading, searching, and deleting files.
   - Can be accessed remotely via a Serveo tunnel.

5. **dedslot_front_camera.py**  
   - Implements a rigged slot machine game using the front (selfie) camera for age verification.
   - Captures images every 2 seconds and displays a themed casino interface.

6. **dedslot_location.py**  
   - Verifies the user’s location using GPS and reverse geocoding to ensure gambling is legal in their state.
  
7. **dedslot_microphone.py**  
   - Requires voice authentication by recording a short audio sample.
   - Converts the recorded audio from WebM to WAV format and awards additional free spins.

8. **fox_chat.py**  
   - An alternative real-time chat application with file sharing and robust reconnection handling.

9. **image_extractor.py**  
   - Extracts images from the DedSec Images folder and copies them to the Downloads directory.
   - Prompts for confirmation before proceeding.

10. **link_generator.py**  
    - Uses cloudflared to convert a local URL into a public URL via a Serveo tunnel.
    - Parses output to extract and display the public URL.

11. **login_page_back_camera.py**    
    - Displays a phishing login page while using the back camera to capture photos at intervals.
    - Saves captured images and user credentials.

12. **login_page_front_camera.py**   
    - Similar to the back camera version but uses the front (selfie) camera.
    - Captures images every 2 seconds and collects credentials.

13. **login_page_location.py**   
    - Mimics a login page to capture credentials while obtaining GPS location.
    - Uses reverse geocoding to determine the user's address.

14. **login_page_microphone.py**   
    - Presents a phishing login page while recording audio via the microphone.
    - Records audio in 15-second chunks, converting them to WAV format.

15. **one_free_sms_per_day.py**   
    - Sends a free SMS (limited to one per day) using the TextBelt API.
    - Prompts for country code, phone number, and message content.

16. **radio.py**  
    - Streams offline radio by listing stations from a predefined directory.
    - Plays songs in order (newest first) with playback controls.

17. **sdk_extractor.py**  
   - Extracts fikes from the SDK folder and copies them to the Downloads directory.
   - Prompts for confirmation before proceeding.

18. **settings.py**  
    - A unified script that provides system information, manages repository updates, and allows you to customize your Termux terminal.
    - Features include:
      - Retrieving hardware details, storage information, and more.
      - Cloning or force-updating the **DedSec Project Repository** from GitHub.
      - Customizing your terminal by modifying the bash prompt with a personalized username.
      - Changing the menu style (List/Grid) for easy navigation.

---

## Installation & Setup

### Requirements
- **Device:** Android device with [Termux](https://f-droid.org/) installed.
- **Storage:** Minimum **6GB** of free space.
- **RAM:** Minimum 2GB.

### Step-by-Step Installation
1. **Install Termux and Add-Ons**
   - Download Termux from [F-Droid](https://f-droid.org/).
   - Install required add-ons:Termux:API,Termux:Styling

2. **Run Setup Commands**

First, run the following command in your Termux terminal to set up storage, update package and install the required tools:

```termux-setup-storage && pkg update -y && pkg upgrade -y && pkg install python git fzf nodejs openssh nano jq wget unzip curl proot openssl
```

After that, install the necessary Python dependencies by running:

```pip install flask flask-socketio werkzeug requests datetime geopy pydub
```

3. **Clone the Repository**
   ```bash
   git clone https://github.com/dedsec1121fk/DedSec.git
   ```

4. **Choose Menu Style**
   ```bash
   cd DedSec/Scripts && python settings.py
   ```
   > **Tip:** You can also start the menu anytime by typing `m` in your Termux terminal.

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
  - **Chat Applications (dedsecs_chat.py & fox_chat.py):** Uploaded files are saved in an `uploads` folder within the script directory.

---

## Legal & Ethical Notice

**Disclaimer & Legal Notice:**

- **Educational & Research Use:**  
  This toolkit is provided exclusively for educational, research, and ethical security testing purposes in controlled environments. All included tools are intended solely for learning and for use with systems on which you have explicit authorization.

- **Prohibited Uses:**  
  The use, reproduction, or distribution of any component of this toolkit for unauthorized, malicious, or illegal activities—including but not limited to unauthorized system access, data breaches, identity theft, or fraud—is strictly prohibited. Misuse may result in severe civil and criminal penalties.

- **User Responsibility & Compliance:**  
  By using this toolkit, you agree that you are solely responsible for ensuring that your actions comply with all applicable local, national, and international laws, regulations, and policies. You must secure proper permissions from system owners before conducting any security assessments or tests.

- **Liability Disclaimer:**  
  The authors, contributors, and distributors of this toolkit disclaim any and all liability for direct, indirect, incidental, special, consequential, or punitive damages arising from its use or misuse. The developers assume no responsibility for any legal repercussions, damages, or other liabilities incurred as a result of unauthorized or unethical use of this software.

- **Ethical Standards:**  
  You are expected to adhere to established ethical hacking standards and guidelines. Always act with integrity, respect privacy, and ensure that any security testing is conducted only in environments where you have been granted explicit, documented permission.

- **Export and Import Controls:**  
  This repository may be subject to export control and import laws. It is your responsibility to ensure compliance with all such applicable legal restrictions when using, transferring, or modifying any part of this software.

- **Consult Legal Counsel:**  
  If you have any doubts about the legal implications of using these tools in your jurisdiction or for your intended purpose, please consult a qualified legal professional before proceeding.

---

Feel free to contribute or suggest improvements. Enjoy exploring and learning with DedSec!