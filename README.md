# DedSec Project

**Secure Use Disclaimer:**
This project is provided solely for educational purposes. Any unauthorized use or attempts to bypass security controls are strictly prohibited. By downloading or using this project, you agree to take full responsibility for all actions performed with it. You are required to use the project in full compliance with all applicable laws and security policies. The creator of this project is not liable for any direct, indirect, or consequential damages or legal actions arising from unauthorized or unsafe use. Always follow best security practices and organizational guidelines when handling this project.

---

## Installation & Setup

### Requirements
- **Device:** Android device with [Termux](https://f-droid.org/) installed.
- **Storage:** Minimum **3GB** of free space.(Keep in mind that Radio takes much more storage if you choose to download it from the menu, and also remember that any taken images and recordings also consume storage.)
- **RAM:** Minimum **2GB**.

### Step-by-Step Installation

1. **Install Termux and Add-Ons**
   - Download Termux from [F-Droid](https://f-droid.org/).
   - Install required add-ons: Termux:API, Termux:Styling.

2. **Run Setup Commands**

   First, open your Termux terminal and run the following command to set up storage, update packages, and install the required tools:

   ```bash
   termux-setup-storage && pkg update -y && pkg upgrade -y && pkg install python git fzf nodejs openssh nano jq wget unzip curl proot openssl aapt rust clouflared
   ```

   Then, install the necessary Python dependencies:

   ```bash
   pip install flask blessed flask-socketio werkzeug requests datetime geopy pydub pycryptodome mutagen rust cryptography
   ```
   
   Then, install Termux:API:

   ```bash
    pkg install termux-api
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

---

## Scripts & Their Functionalities

Below is a summary of each script provided in the DedSec toolkit:

1. **Charon Chat**
  -Lets you talk with encrypted chat with other people with the same link,  no nicknames are saved, no password needs, also it lets you exchange files, voice messages and more.

2. **Android App Launcher**
  -Displays all your downloaded Android apps and lets you launch, delete, or view information about them.

3. **Radio**
  -A full offline radio with Greek and not only artists.

4. **Link Generator**
  -This link generator helps you generate public links for your programs.

5. **Phishing Attacks**
  -Lets you take images from front or back camera, record sound, find the exact location (with address and a nearby store if available) from a person. Also it lets you take card credentials. Everything is saved in folders in internal storage Downloads folder.

6. **Settings**
  -Lets you update the project, install or update the required packages and modules, change the prompt username, change the menu style, and view the credits of the project creators.

7. **DedSec Database**
  -Lets you upload, search, and delete files. The device that starts the program acts as the server.

8. **Text Encryptor And Decryptor**
  -A simple text encryption and decryption app for Termux.

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