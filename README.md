![Custom Purple Fox Logo](https://github.com/dedsec1121fk/DedSec/blob/f5fabcbd129e7cc233a728f78299a4db5abd00fb/Extra%20Content/Images/Custom%20Purple%20Fox%20Logo.png?raw=true)

# DedSec Project

> **A standalone DedSec Project application will be soon available with even more features. Stay tuned for updates and release info.**

<div align="center">

[![Visit ded-sec.space](https://img.shields.io/badge/🌐%20Website-ded--sec.space-007EC6?style=for-the-badge)](https://www.ded-sec.space)
<a href="https://github.com/dedsec1121fk/DedSec" target="_blank"><img alt="GitHub Repo" src="https://img.shields.io/badge/GitHub-View%20on%20GitHub-blue?logo=github"/></a>
<a href="https://www.patreon.com/c/dedsec1121fk/membership?redirect=true" target="_blank"><img alt="Become a Patron" src="https://img.shields.io/badge/Patreon-Become%20a%20Patron-orange?logo=patreon"/></a>
<a href="https://www.instagram.com/username112104?igsh=MnR2eTdxaTN5ZHZi" target="_blank"><img alt="Instagram" src="https://img.shields.io/badge/Instagram-Follow%20Me-purple?logo=instagram"/></a>

</div>

---

## About The Project

The DedSec Project is a free, community-driven initiative inspired by the underground resistance and cyber-revolution themes of Ubisoft’s Watch Dogs series. Just like the in-game DedSec, our project empowers everyday users with tools for digital freedom, security, and awareness. We provide hacking-style utilities, phishing tools, secure communication platforms, and system customization—all without charging a cent.

Why use it? Because everyone deserves access to knowledge, privacy, and control over their digital life. We're not here for profit—we're here to give power back to the people. Whether you're a tech enthusiast, digital activist, or just someone curious about cybersecurity, the DedSec Project invites you to be part of the movement.

**Welcome to the resistance.**

---

### **Secure Use Disclaimer**
This project is provided solely for educational purposes. Any unauthorized use or attempts to bypass security controls are strictly prohibited. By downloading or using this project, you agree to take full responsibility for all actions performed with it. You are required to use the project in full compliance with all applicable laws and security policies. The creator of this project is not liable for any direct, indirect, or consequential damages or legal actions arising from unauthorized or unsafe use. Always follow best security practices and organizational guidelines when handling this project.

---

## Installation & Setup

- For instructions in other languages, please visit the [DedSec Project Website](https://www.ded-sec.space).

### Requirements
* **Device:** Android with [Termux](https://f-droid.org/) installed.
* **Storage:** Minimum **3GB** free. (Radio, images, and recordings will consume more space).
* **RAM:** Minimum **2GB**.

### Step-by-Step Installation

1.  **Install Termux & Add-Ons**
    > **Note:** To install APKs (e.g., F-Droid), ensure you have enabled unknown sources in `Settings > Security > Install Unknown Apps`. Download Termux from [F-Droid](https://f-droid.org/) and install the following add-ons: Termux:API, Termux:Styling.

2.  **Run Setup Commands**
    Open Termux and run the following commands:
    ```bash
    termux-setup-storage && pkg update -y && pkg upgrade -y && pkg install python git fzf nodejs openssh nano jq wget unzip curl proot openssl aapt rust cloudflared
    ```
   
   
    ```bash
    pip install flask blessed flask-socketio werkzeug requests datetime geopy pydub pycryptodome mutagen rust cryptography phonenumbers pycountry
    ```
   
   
    ```bash
    pkg install termux-api
    ```
   
   

3.  **Clone Repository**
    ```bash
    git clone [https://github.com/dedsec1121fk/DedSec](https://github.com/dedsec1121fk/DedSec)
    ```
   
   
    > **Tip:** If you encounter a `ModuleNotFoundError: No module named 'requests'`, run `pip install requests` and try again.

4.  **Choose Menu Style**
    ```bash
    cd DedSec/Scripts && python Settings.py
    ```
   
   
    > **Tip:** You can open the menu later by typing `m` in Termux.

---

## Scripts & Their Functionalities

1.  **Fox Chat**
    Encrypted chat with file, voice, and video calls. No saved nicknames or passwords.

2.  **Android App Launcher**
    Displays and manages your downloaded Android apps.

3.  **Radio**
    Offline radio featuring Greek and international artists.

4.  **Phishing Attacks**
    Capture camera images, audio, and precise location. Can also obtain card and personal info. All data is saved to your `Downloads` folder.
    * **Card Details.py**: Saves credit card info to `~/storage/downloads/CardActivations/`.
    * **Data Grabber.py**: Saves personal info/photo to `~/storage/downloads/People's Lives/{user}/`.
    * **Login Page Back Camera.py**: Stores images/credentials to `~/storage/downloads/Camera-Phish-Back/`.
    * **Login Page Front Camera.py**: Saves front camera photos/credentials to `~/storage/downloads/Camera-Phish-Front/`.
    * **Login Page Location.py**: Stores location data/credentials to `~/storage/downloads/LocationData/`.
    * **Login Page Microphone.py**: Saves mic recordings/credentials to `~/storage/downloads/Recordings/`.

5.  **Settings**
    Update the project, install/update packages, change username/menu style, and view credits.

6.  **DedSec Database**
    Upload, search, and delete files. Your device acts as the server, and files are saved in a hidden folder.

7.  **Extra Content**
    Contains photos, unused scripts, voice-overs, and more.

---

## Donate

Support the project by donating with Crypto.
**POL (Polygon) Address:**