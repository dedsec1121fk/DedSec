<div align="center">
  <img src="https://raw.githubusercontent.com/dedsec1121fk/dedsec1121fk.github.io/ef4b1f5775f5a6fb7cf331d8f868ea744c43e41b/Assets/Images/Custom%20Purple%20Fox%20Logo.png" alt="DedSec Project Logo" width="150"/>
  <h1>DedSec Project</h1>
  <p><strong>Your free guide to digital self-defense.</strong></p>
  <p>
    <a href="https://ded-sec.space/"><strong>Official Website</strong></a>
  </p>
  
  <p>
    <img src="https://img.shields.io/badge/Purpose-Educational-blue.svg" alt="Purpose: Educational">
    <img src="https://img.shields.io/badge/Platform-Android%20(Termux)-brightgreen.svg" alt="Platform: Android (Termux)">
    <img src="https://img.shields.io/badge/Language-Python%20%7C%20Shell-yellow.svg" alt="Language: Python | Shell">
  </p>
</div>

---

Welcome to the DedSec Project! Our mission is to empower you by revealing how real-world threats operate. This toolkit is packed with educational scripts designed to turn you from a target into a defender. Learn how phishing attacks work, how to secure your communications, and more, all within a controlled and ethical learning environment.

## 📋 Table of Contents

* [Installation](#-installation--usage)
* [Digital Self-Defense Toolkit](#-digital-self-defense-toolkit)
* [Legal Disclaimer](#-legal-disclaimer)
* [Community & Contact](#-community--contact)
* [Credits](#-credits)

---

## 🚀 Installation & Usage

Get the DedSec Project running on your Android device with Termux.

### Requirements

| Component | Minimum Specification |
| :-------- | :-------------------- |
| **Device**| Android with [Termux](https://f-droid.org/) installed |
| **Storage** | **3GB** of free space |
| **RAM** | **2GB** |

### Step-by-Step Setup

1.  **Install Packages & Grant Permissions**
    Open Termux and run the following command to set up storage and install necessary packages:
    ```bash
    termux-setup-storage && pkg update -y && pkg upgrade -y && pkg install aapt clang cloudflared curl ffmpeg fzf git jq libffi libffi-dev libxml2 libxslt nano ncurses nodejs openssh openssl openssl-tool proot python rust unzip wget zip -y
    ```

2.  **Install Python Libraries**
    Install the required Python modules using pip:
    ```bash
    pip install blessed bs4 cryptography flask flask-socketio geopy mutagen phonenumbers pycountry pydub pycryptodome requests werkzeug
    ```

3.  **Install Termux API**
    This package allows the scripts to interact with Android's native features:
    ```bash
    pkg install termux-api
    ```

4.  **Clone the Repository**
    Download the project files from GitHub:
    ```bash
    git clone [https://github.com/dedsec1121fk/DedSec](https://github.com/dedsec1121fk/DedSec)
    ```

5.  **Run the Project**
    Navigate into the project directory and run the settings script to begin:
    ```bash
    cd DedSec/Scripts && python Settings.py
    ```
    > **💡 Tip:** You can open the main menu later by just typing `m` in Termux.

---

## 🛡️ Digital Self-Defense Toolkit

This toolkit contains various scripts for **educational and defensive purposes only**. Their function is to demonstrate how common attacks work so you can learn to recognize and protect yourself against them.

* **Fox Chat**
    * Encrypted chat, along with file sharing, voice messages, and video calls.

* **Android App Launcher**
    * Displays and manages downloaded Android apps.

* **Radio**
    * Features an offline radio with Greek and international artists.

* **Settings**
    * Allows you to update the project, install or update packages and modules, change your username and menu style, and view credits.

* **DedSec Database**
    * Lets you upload, search for, and delete files. Your device acts as the server, and files are saved in a hidden folder.

* **HTML Finder**
    * A utility to inspect, download, and locally edit any public webpage.

* **URL Masker (Masker.py)**
    * A tool to conceal and shorten URLs.

* **SocialBrute**
    * An advanced multi-service brute-force tool for social media platforms.

* **Extra Content**
    * Contains photos, unused scripts, voice-overs, and more.

<details>
  <summary><strong>🎣 Phishing Attack Demonstrations (Click to expand)</strong></summary>
  
  This educational module simulates real phishing attacks to help you understand their mechanics. It can capture camera images, audio, and the target's exact location (address/store). It can also obtain credit card and personal information. All captured data is saved in the Downloads folder.
  <ul>
    <li><b>Card Details.py</b>: Saves credit card info to <code>~/storage/downloads/CardActivations/</code>.</li>
    <li><b>Data Grabber.py</b>: Saves personal info/photo to <code>~/storage/downloads/People's Lives/{user}/</code>.</li>
    <li><b>FaceFriends.py</b>: Stores credentials to <code>~/storage/downloads/FaceFriends/</code>.</li>
    <li><b>Google Free Money.py</b>: Saves credentials to <code>~/storage/downloads/GoogleFreeMoney/</code>.</li>
    <li><b>Insta Followers.py</b>: Saves credentials to <code>~/storage/downloads/FreeFollowers/</code>.</li>
    <li><b>Login Page Back Camera.py</b>: Stores images/credentials to <code>~/storage/downloads/Camera-Phish-Back/</code>.</li>
    <li><b>Login Page Front Camera.py</b>: Saves front camera photos/credentials to <code>~/storage/downloads/Camera-Phish-Front/</code>.</li>
    <li><b>Login Page Location.py</b>: Stores location data/credentials to <code>~/storage/downloads/Locations/</code>.</li>
    <li><b>Login Page Microphone.py</b>: Saves mic recordings/credentials to <code>~/storage/downloads/Recordings/</code>.</li>
    <li><b>Snap Friends.py</b>: Stores credentials to <code>~/storage/downloads/SnapFriends/</code>.</li>
    <li><b>Tik Followers.py</b>: Saves credentials to <code>~/storage/downloads/TikFollowers/</code>.</li>
  </ul>
  <strong>Remember:</strong> Only use these scripts on your own devices for learning purposes.
</details>

---

## ⚖️ Legal Disclaimer

> **CRITICAL NOTICE:** This project, including all associated tools and scripts, is provided strictly for **educational, research, and ethical security testing purposes**. It is intended for use exclusively in controlled, authorized environments.
>
> By accessing or using this software, you acknowledge that you are doing so at your own risk. You are solely responsible for your actions and for any consequences that may arise from its use or misuse. Any use of the software for unauthorized or malicious activities is **strictly prohibited**.
>
> In no event shall the developers or contributors be liable for any claim, damages, or other liability arising from, out of, or in connection with the software.

---

## 🌐 Community & Contact

Connect with the DedSec Project community through our official channels:

* **📱 WhatsApp:** [Join the conversation](https://wa.me/37257263676)
* **📸 Instagram:** [Follow for updates](https://www.instagram.com/dedsec_project_official)
* **✈️ Telegram:** [Official Channel](https://t.me/dedsecproject)
* **🤖 Reddit:** [Join the subreddit](https://www.reddit.com/user/dedsec_project/)

---

## ✨ Credits

This project was made possible by the following contributors:

* **Creator:** dedsec1121fk
* **Technical Help:** lamprouil, UKI_hunter
* **Artwork:** Christina Chatzidimitriou
* **Voice-overs:** Dimitra Isxuropoulou
* **Producer:** JK
* **Music Artists:** BFR TEAM, PLANNO MAN, KouNouPi, ADDICTED, JAVASPA, ICE, Lefka City, Lavyrinthos, Komis X, GR$, Sakin, Christina Markesini, Grave_North, Aroy, Pi Thita, Bossikan, Lau Jr, XALILOP, Scav, PS, ARES127, ELG FAMILY, Zepo & Xan