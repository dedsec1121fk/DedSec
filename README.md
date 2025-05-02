![Custom Purple Fox Logo](https://github.com/dedsec1121fk/DedSec/blob/f5fabcbd129e7cc233a728f78299a4db5abd00fb/Extra%20Content/Images/Custom%20Purple%20Fox%20Logo.png?raw=true)

# DedSec Project

[![Visit ded-sec.space](https://img.shields.io/badge/🌐%20Website-ded--sec.space-007EC6?style=for-the-badge)](https://www.ded-sec.space)
[![Follow on Instagram](https://img.shields.io/badge/Instagram-Follow%20on%20Instagram-E4405F?logo=instagram&logoColor=white)](https://www.instagram.com/loukas_floros?igsh=MnR2eTdxaTN5ZHZi)
[![Become a Patron](https://img.shields.io/badge/Patreon-Become%20a%20Patron-orange?logo=patreon)](https://www.patreon.com/c/dedsec1121fk/membership?redirect=true)

**Secure Use Disclaimer:**
This project is provided solely for educational purposes. Any unauthorized use or attempts to bypass security controls are strictly prohibited. By downloading or using this project, you agree to take full responsibility for all actions performed with it. You are required to use the project in full compliance with all applicable laws and security policies. The creator of this project is not liable for any direct, indirect, or consequential damages or legal actions arising from unauthorized or unsafe use. Always follow best security practices and organizational guidelines when handling this project.

---

## Installation & Setup

- Ελληνική Μετάφραση των οδηγιών μπορεί να βρεθεί στην ιστοσελίδα μου για το [DedSec Project.](https://www.ded-sec.space)

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
   termux-setup-storage && pkg update -y && pkg upgrade -y && pkg install python git fzf nodejs openssh nano jq wget unzip curl proot openssl aapt rust cloudflared
   ```

   Then, install the necessary Python dependencies:

   ```bash
   pip install flask blessed flask-socketio werkzeug requests datetime geopy pydub pycryptodome mutagen rust cryptography phonenumbers pycountry
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
   cd DedSec/Scripts && python Settings.py
   ```
   > **Tip:** You can always open the menu later by typing `m` in your Termux terminal.

---

## Scripts & Their Functionalities

Below is a summary of each script provided in the DedSec toolkit:

1. **Communication**
  -Lets you talk with encrypted chat with other people with the same link,  no nicknames are saved, no password needs, also it lets you exchange files, voice messages and video calls.

2. **Android App Launcher**
  -Displays all your downloaded Android apps and lets you launch, delete, or view information about them.

3. **Radio**
  -A full offline radio with Greek and not only artists.

4. **Phishing Attacks**
  -Lets you take images from front or back camera, record sound, find the exact location (with address and a nearby store if available) from a person. Also it lets you take card credentials, Personal Info etc. Everything is saved in folders in internal storage Downloads folder.

5. **Tools**
  -Lets you update the project, install or update the required packages and modules, change the prompt username, change the menu style, view the credits of the project creators, upload, search, and delete files. The device that starts the program acts as the server, simple text encryption and decryption, and a link generator helps you generate public links for your programs.

6. **Extra Content**
  -Contains photos, unused scripts, unused voice overs and more.

---

- **Phishing Scripts Background Images:**
  - **Login_Page_Back_Camera.py** and **Login_Page_Front_Camera.py** use a background image named **camera.jpg** saved in:  
    `~/storage/downloads/Camera-Phish`
  - **Login_Page_Location.py** uses a background image named **locate.jpg** saved in:  
    `~/storage/downloads/LocationData`
  - **DedSlot_Front_Camera.py**, **DedSlot_Location.py**, and **DedSlot_Microphone.py** use a background image named **casino.jpg** saved in:  
    `~/storage/downloads/Camera-Phish`

- **Other Data Storage:**
  - **Card Details:** Files are saved in:  
    `~/storage/downloads/CardActivations`
  - **Location Data:** Files (aside from the image) are saved in:  
    `~/storage/downloads/LocationData`
  - **Audio Recordings:** Files are saved in:  
    `~/storage/downloads/Recordings`
- **Data_Grabber.py:**
  - User details (a text file with personal data and the uploaded photo) are saved in a folder named after the user inside:  
    `~/storage/downloads/People's Lives`

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