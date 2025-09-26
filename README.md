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

Welcome to the DedSec Project! Our mission is to empower you by revealing how real-world threats operate. This toolkit is packed with educational scripts, showing you how phishing attacks steal camera images and location data, or how to chat securely with an encrypted client. Everything here is completely free and designed to turn you from a target into a defender.

## 📋 Table of Contents

* [Installation](#-installation--usage)
* [Digital Self-Defense Toolkit](#-digital-self-defense-toolkit)
* [Portfolio & GitHub](#-portfolio--github)
* [Collaborations](#-collaborations)
* [Legal Disclaimer](#️-legal-disclaimer)
* [Community & Contact](#-community--contact)
* [Credits](#-credits)

---

## 🚀 Installation & Usage

Get the DedSec Project running on your Android device with Termux.

### Requirements

| Component | Minimum Specification                                      |
| :-------- | :--------------------------------------------------------- |
| **Device** | Android with [Termux](https://f-droid.org/) installed      |
| **Storage** | **3GB** of free space                                      |
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

* **Fox Chat**: Encrypted chat, along with file sharing, voice messages, and video calls.
* **Android App Launcher**: Displays and manages downloaded Android apps.
* **Radio**: Features an offline radio with Greek and international artists.
* **DedSec Database**: Lets you upload, search for, and delete files on a local server hosted by your device.
* **HTML Finder**: A utility to inspect, download, and locally edit any public webpage.
* **URL Masker (Masker.py)**: A tool to conceal and shorten URLs.
* **SocialBrute**: An advanced multi-service brute-force tool for social media platforms.
* **Settings**: Allows you to update the project, install or update packages and modules, change your username and menu style, and view credits.
* **Extra Content**: Contains photos, unused scripts, voice-overs, and more.

<details>
  <summary><strong>🎣 Phishing Attack Demonstrations (Click to expand)</strong></summary>
  
  This educational module simulates real phishing attacks to help you understand their mechanics. It demonstrates capturing camera images, audio, location, credit card data, and personal information. All captured data is saved in your device's `Downloads` folder.
  <ul>
    <li><b>Fake Card Details Page.py</b>: Saves credit card info to <code>~/storage/downloads/CardActivations/</code>.</li>
    <li><b>Fake Data Grabber Page.py</b>: Saves personal info/photo to <code>~/storage/downloads/Peoples_Lives/{user}/</code>.</li>
    <li><b>Fake FaceFriends Page.py</b>: Stores credentials to <code>~/storage/downloads/FaceFriends/</code>.</li>
    <li><b>Fake Google Free Money Page.py</b>: Saves credentials to <code>~/storage/downloads/GoogleFreeMoney/</code>.</li>
    <li><b>Fake Insta Followers Page.py</b>: Saves credentials to <code>~/storage/downloads/FreeFollowers/</code>.</li>
    <li><b>Fake Back Camera Page.py</b>: Stores images/credentials to <code>~/storage/downloads/Camera-Phish-Back/</code>.</li>
    <li><b>Fake Front Camera Page.py</b>: Saves front camera photos/credentials to <code>~/storage/downloads/Camera-Phish-Front/</code>.</li>
    <li><b>Fake Location Page.py</b>: Stores location data (GPS, address, IP) to <code>~/storage/downloads/Locations/</code>.</li>
    <li><b>Fake Microphone Page.py</b>: Saves mic recordings/credentials to <code>~/storage/downloads/Recordings/</code>.</li>
    <li><b>Fake Snap Friends Page.py</b>: Stores credentials to <code>~/storage/downloads/SnapFriends/</code>.</li>
    <li><b>Fake Tik Followers Page.py</b>: Saves credentials to <code>~/storage/downloads/TikFollowers/</code>.</li>
  </ul>
  <strong>Remember:</strong> Only use these scripts on your own devices for learning purposes.
</details>

---

## 📂 Portfolio & GitHub

Explore our other projects and source code.

* **Portfolio**
    * [ICE Project](https://www.ded-sec.space/ICE-Project/)
    * [Scav Project](https://www.ded-sec.space/Scav-Project)
* **Repositories**
    * [DedSec (The Official Project)](https://github.com/dedsec1121fk/DedSec)
    * [DedSec-Radio (Audio Files)](https://github.com/dedsec1121fk/DedSec-Radio)
    * [Website Source Code](https://github.com/dedsec1121fk/dedsec1121fk.github.io)

---

## 🤝 Collaborations

* **Python Gym Clothing**
    * Visit the [Official Store](https://pythongymclothing.com/) and use discount code `dedsec` for 10% off.
* **AdGen**
    * [Create customized ads](https://adgenai.space/main.php) for your product using AI.

---

## ⚖️ Legal Disclaimer

> **CRITICAL NOTICE: PLEASE READ CAREFULLY BEFORE PROCEEDING.**
>
> This project, including all associated tools, scripts, and documentation ("the Software"), is provided strictly for **educational, research, and ethical security testing purposes**. It is intended for use exclusively in controlled, authorized environments by users who have obtained explicit, prior written permission from the owners of any systems they intend to test.
>
> **1. Assumption of Risk and Responsibility:** By accessing or using the Software, you acknowledge and agree that you are doing so at your own risk. You are solely and entirely responsible for your actions and for any consequences that may arise from the use or misuse of this Software.
>
> **2. Prohibited Activities:** Any use of the Software for unauthorized or malicious activities is strictly prohibited. This includes, without limitation: accessing systems without authorization, data theft, or any other activity that violates applicable laws. Engaging in such activities may result in severe civil and criminal penalties.
>
> **3. No Warranty:** The Software is provided "AS IS," without any warranty of any kind, express or implied.
>
> **4. Limitation of Liability:** In no event shall the developers, contributors, or distributors of the Software be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the Software or the use or other dealings in the Software.

---

## 🌐 Community & Contact

Connect with the DedSec Project community through our official channels:

* **📱 WhatsApp:** [+37257263676](https://wa.me/37257263676)
* **📸 Instagram:** [@dedsec\_project\_official](https://www.instagram.com/dedsec_project_official)
* **✈️ Telegram:** [@dedsecproject](https://t.me/dedsecproject)
* **🤖 Reddit:** [u/dedsec\_project](https://www.reddit.com/user/dedsec_project/)

---

## ✨ Credits

This project was made possible by the following contributors:

* **Creator:** dedsec1121fk
* **Music Artists:** BFR TEAM, PLANNO MAN, KouNouPi, ADDICTED, JAVASPA, ICE, Lefka City, Lavyrinthos, Komis X, GR$, Sakin, Christina Markesini, Grave\_North, Aroy, Pi Thita, Bossikan, Lau Jr, XALILOP, Scav, PS, ARES127, ELG FAMILY, Zepo & Xan
* **Artwork:** Christina Chatzidimitriou
* **Voice-overs:** Dimitra Isxuropoulou
* **Producer:** JK
* **Technical Help:** lamprouil, UKI\_hunter
