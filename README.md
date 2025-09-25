# DedSec Project

![DedSec Project Logo](https://raw.githubusercontent.com/dedsec1121fk/dedsec1121fk.github.io/ef4b1f5775f5a6fb7cf331d8f868ea744c43e41b/Assets/Images/Custom%20Purple%20Fox%20Logo.png)

### [Official Project Website: www.ded-sec.space](https://ded-sec.space/)

Welcome to your free guide to **digital self-defense**! 🦊 Our mission is to empower you by revealing how real-world threats operate. This toolkit is packed with educational scripts designed to turn you from a target into a defender. Learn how phishing attacks work, how to secure your communications, and more.

---

## 🚀 Installation & Usage

Get the DedSec Project running on your Android device with Termux.

### Requirements
* **Device:** Android with [Termux](https://f-droid.org/) installed.
* **Storage:** Minimum **3GB** of free space.
* **RAM:** Minimum **2GB**.

### Step-by-Step Setup

1.  **Grant Storage Permission & Install Packages**
    Open Termux and run the following command to set up storage and install the necessary packages:
    ```bash
    termux-setup-storage && pkg update -y && pkg upgrade -y && pkg install aapt clang cloudflared curl ffmpeg fzf git jq libffi libffi-dev libxml2 libxslt nano ncurses nodejs openssh openssl openssl-tool proot python rust unzip wget zip -y
    ```

2.  **Install Python Libraries**
    Install the required Python modules using pip:
    ```bash
    pip install blessed bs4 cryptography flask flask-socketio geopy mutagen phonenumbers pycountry pydub pycryptodome requests werkzeug
    ```

3.  **Install Termux API**
    This package is needed for the scripts to interact with Android's features:
    ```bash
    pkg install termux-api
    ```

4.  **Clone the Repository**
    Download the project files from GitHub:
    ```bash
    git clone [https://github.com/dedsec1121fk/DedSec](https://github.com/dedsec1121fk/DedSec)
    ```

5.  **Run the Project**
    Navigate into the project directory and run the settings script to choose your menu style:
    ```bash
    cd DedSec/Scripts && python Settings.py
    ```
    > **Tip:** You can open the menu later by just typing `m` in Termux.

---

## 🛡️ Digital Self-Defense Toolkit

This toolkit contains scripts for **educational and defensive purposes only**. Their function is to demonstrate how common attacks work so you can learn to recognize and protect yourself against them.

* **Fox Chat:** A fully encrypted chat client with file sharing, voice messages, and video calls. 💬
* **Phishing Demonstrations:** A suite of scripts showing how attackers capture data. Learn how they can access cameras, microphones, location, and credentials to better defend yourself.
* **DedSec Database:** A local server solution that lets you upload, search for, and delete files on your own device.
* **URL Masker:** A tool to demonstrate how malicious links can be concealed and shortened.
* **SocialBrute:** An advanced multi-service brute-force tool to demonstrate password attack vectors on social media platforms.
* **HTML Finder:** A utility to inspect, download, and locally edit any public webpage.
* **And More:** The project also includes an offline radio, an app launcher, and extra content.

---

## ⚖️ Legal Notice

> **CRITICAL NOTICE:** This project, including all associated tools and scripts, is provided strictly for **educational, research, and ethical security testing purposes**. It is intended for use exclusively in controlled, authorized environments.
>
> By accessing or using this software, you acknowledge that you are doing so at your own risk. You are solely responsible for your actions and for any consequences that may arise from its use or misuse. Any use of the software for unauthorized or malicious activities is **strictly prohibited**.
>
> In no event shall the developers or contributors be liable for any claim, damages, or other liability arising from, out of, or in connection with the software.

---

## 📞 Contact & Socials

Connect with the DedSec Project community through our official channels:

* [<img src="https://img.icons8.com/color/48/000000/whatsapp--v1.png" width="20"/> WhatsApp](https://wa.me/37257263676)
* [<img src="https://img.icons8.com/fluent/48/000000/instagram-new.png" width="20"/> Instagram](https://www.instagram.com/dedsec_project_official)
* [<img src="https://img.icons8.com/color/48/000000/telegram-app.png" width="20"/> Telegram](https://t.me/dedsecproject)
* [<img src="https://img.icons8.com/color/48/000000/reddit.png" width="20"/> Reddit](https://www.reddit.com/user/dedsec_project/)