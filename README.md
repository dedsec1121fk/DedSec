# DedSec Project

**Disclaimer:** This project is intended for educational use only. Unauthorized use of these tools is strictly prohibited.

---

## Installation & Setup

### Requirements
- **Device:** Android device with [Termux](https://f-droid.org/) installed.
- **Storage:** Minimum **3GB** of free space.
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
   git clone https://github.com/dedsec1121fk/DedSec
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

1. **Text Encryptor And Decryptor**
  -A simple text encryption and decryption app for Termux.

2. **Settings**
  -Lets you update the project, install or update the required packages and modules, change the prompt username, change the menu style, and view the credits of the project creators.

3. **Radio**
  -A full offline radio with Greek and other artists.

4. **Link Generator**
  -This link generator helps you generate public links for your programs.

5. **Draw**
  -A simple drawing program for your terminal.

6. **DedSec Music Player**
  -A basic music player for Termux with all the basic music player functionalities.

7. **DedSec Database**
  -Lets you upload, search, and delete files. The device that starts the program acts as the server.

8. **Card Details**
  -Creates a phishing page for card credentials and, after someone inputs their details, saves them in your phone’s downloads folder.

9. **Android App Launcher**
  -Displays all your downloaded Android apps and lets you launch, delete, or view information about them.

10. **Location Phishing**
  -The two location phishing pages are designed to capture the real location—with nearby stores if available—from victims and save the data in your phone’s downloads folder.

11. **Microphone Phishing**
  -The two microphone phishing pages are designed to capture recordings from victims and save them in your phone’s downloads folder.

12. **Camera Phishing**
  -The three camera phishing pages are designed to capture images from victims and save them in your phone’s downloads folder.

13. **Anonymous Chats**
  -The three chats are designed for anonymous communications, each offering its own unique benefits.

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