<div align="center">
  <img src="https://raw.githubusercontent.com/dedsec1121fk/dedsec1121fk.github.io/ef4b1f5775f5a6fb7cf331d8f868ea744c43e41b/Assets/Images/Custom%20Purple%20Fox%20Logo.png" alt="DedSec Project Logo" width="150"/>
  <h1>DedSec Project</h1>
  <p><strong>DedSec has given you the truth, do what you will. Your free guide to digital self-defense.</strong></p>
  <p>
    <a href="https://ded-sec.space/"><strong>Official Website</strong></a>
    ·
    <a href="https://dedsec1121fk.gumroad.com"><strong>DedSec Store</strong></a>
  </p>
  
  <p>
    <img src="https://img.shields.io/badge/Purpose-Educational-blue.svg" alt="Purpose: Educational">
    <img src="https://img.shields.io/badge/Platform-Android%20(Termux)-brightgreen.svg" alt="Platform: Android (Termux)">
    <img src="https://img.shields.io/badge/Language-Python%20%7C%20JS%20%7C%20Shell-yellow.svg" alt="Language: Python | JS | Shell">
    <img src="https://img.shields.io/badge/Interface-EN%20%7C%20GR-lightgrey.svg" alt="Interface: EN | GR">
  </p>
</div>

---

Welcome to the **DedSec Project**! Our mission is to empower you by demonstrating how real-world digital threats operate. This toolkit is designed for educational purposes, providing scripts and guides that cover everything from understanding phishing attacks to turning your phone into a portable, powerful command-line environment. Everything here is completely free and designed to help you shift from being a target to being a defender.

## 📋 Table of Contents

* [Installation & Usage (Command-Line Tools)](#-installation--usage-command-line-tools)
* [Digital Self-Defense Toolkit](#️-digital-self-defense-toolkit)
* [Portfolio & GitHub](#-portfolio--github)
* [Collaborations](#-collaborations)
* [Community & Contact](#-community--contact)
* [Credits](#-credits)
* [Legal Disclaimer & Terms of Use](#️-legal-disclaimer--terms-of-use)

---

## 🚀 Installation & Usage (Command-Line Tools)

Get the DedSec Project command-line tools running on your **Android device with Termux**.

### Requirements

| Component | Minimum Specification                                                |
| :-------- | :------------------------------------------------------------------- |
| **Device** | Android with [Termux](https://f-droid.org/) installed               |
| **Storage** | **3GB** of free space (Radio, images, and recordings consume more.) |
| **RAM** | **2GB** |

### Step-by-Step Setup

> **Note:** For best results, install Termux from the [F-Droid](https://f-droid.org/) store. This ensures you can also install necessary add-ons like `Termux:API`. You may need to enable "**Install Unknown Apps**" in your Android settings.

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
    > **💡 Tip:** If you get an error like `ModuleNotFoundError: No module named 'requests'`, run `pip install requests` and try again.

5.  **Run the Project**
    Navigate into the project directory and run the settings script to begin:
    ```bash
    cd DedSec/Scripts && python Settings.py
    ```
    > **💡 Tip:** You can open the main menu later by just typing `m` in Termux.

---

## 🛡️ Digital Self-Defense Toolkit

> **CRITICAL NOTICE:** The following scripts are included for **educational and defensive purposes ONLY**. Their function is to demonstrate how common attacks work, so you can learn to recognize and protect yourself against them. They should only be used in a controlled environment, **on your own devices and accounts**, for self-testing.

* **Fox Chat & Utilities**: Includes various scripts like encrypted chat, an offline radio player, app management tools, and the settings menu to update the project.
* **Phishing Demonstrations**: Modules that demonstrate how a malicious webpage can trick a user into giving away access to their device's camera, microphone, and location. For your self-tests, any demonstration credentials or data you enter are saved locally into appropriately named folders inside your phone's main **Downloads** folder for you to review.
* **SocialBrute**: A script designed to demonstrate the weakness of simple or reused passwords. It shows how automated attacks work, highlighting the critical importance of using strong, unique passwords for every online account.
* **URL Masker & HTML Finder**: Educational tools to help you understand how web pages are structured and how links can be disguised.

---

## 💼 Portfolio & GitHub

### Other Projects

* [**ICE Project**](https://www.ded-sec.space/ICE-Project/)
* [**Scav Project**](https://www.ded-sec.space/Scav-Project)
* [**KuNuPi Project**](https://www.ded-sec.space/KuNuPi-Project/)

### Repositories

* [**DedSec (The Official Project)**](https://github.com/dedsec1121fk/DedSec)
* [**DedSec-Radio (Audio Files)**](https://github.com/dedsec1121fk/DedSec-Radio)

### Statistics

<div align="center">
  <img src="https://github-readme-stats.vercel.app/api?username=dedsec1121fk&show_icons=true&theme=transparent&border_color=9966ff&text_color=d0d8e0&title_color=9966ff&icon_color=e6d9ff" alt="GitHub Stats">
  <img src="https://github-readme-stats.vercel.app/api/top-langs/?username=dedsec1121fk&layout=compact&theme=transparent&border_color=9966ff&text_color=d0d8e0&title_color=9966ff&icon_color=e6d9ff" alt="Top Languages">
</div>

---

## 🤝 Collaborations

### Python Gym Clothing

Use the discount code below for 10% off at the official store!

**Discount Code:** `dedsec`

**[Visit The Official Store](https://pythongymclothing.com/)**

### AdGen

Create customized ads for your product using AI!

**[Create Your Ad](https://adgenai.space/main.php)**

---

## 🌐 Community & Contact

Connect with the DedSec Project community through our official channels:

* **📱 WhatsApp:** [+37257263676](https://wa.me/37257263676)
* **📸 Instagram:** [@dedsec\_project\_official](https://www.instagram.com/dedsec_project_official)
* **✈️ Telegram:** [@dedsecproject](https://t.me/dedsecproject)

---

## ✨ Credits

This project was made possible by the following contributors:

* **Creator:** dedsec1121fk
* **Music Artists:** BFR TEAM, PLANNO MAN, KouNouPi, ADDICTED, JAVASPA, ICE, Lefka City, Lavyrinthos, Komis X, GR$, Sakin, Christina Markesini, Grave\_North, Aroy, Pi Thita, Bossikan, Lau Jr, XALILOP, Scav, PS, ARES127, ELG FAMILY, Zepo & Xan
* **Producer:** JK
* **Artwork:** Christina Chatzidimitriou
* **Voice-overs:** Dimitra Isxuropoulou
* **Technical Help:** lamprouil, UKI\_hunter

---

## ⚖️ Legal Disclaimer & Terms of Use

> **PLEASE READ CAREFULLY BEFORE PROCEEDING.**
>
> **Trademark Disclaimer:** The "DedSec" name and logo used in this project are for thematic and inspirational purposes only. This is an independent, fan-made project created for educational purposes and has no official connection to the "Watch Dogs" franchise. It is not associated with, endorsed by, or affiliated with Ubisoft Entertainment S.A. All trademarks and copyrights for "Watch Dogs" and "DedSec" as depicted in the games belong to their respective owners, Ubisoft Entertainment S.A.
>
> This project, including all associated tools, scripts, and documentation ("the Software"), is provided strictly for **educational, research, and ethical security testing purposes**. It is intended for use exclusively in controlled, authorized environments by users who have obtained explicit, prior written permission from the owners of any systems they intend to test.
>
> **1. Assumption of Risk and Responsibility:** By accessing or using the Software, you acknowledge and agree that you are doing so at your own risk. You are solely and entirely responsible for your actions and for any consequences that may arise from the use or misuse of this Software. This includes, but is not limited to, compliance with all applicable local, state, national, and international laws and regulations related to cybersecurity, data privacy, and electronic communications.
>
> **2. Prohibited Activities:** Any use of the Software for unauthorized or malicious activities is strictly prohibited. This includes, without limitation: accessing systems, systems, or data without authorization; performing denial-of-service attacks; data theft; fraud; spreading malware; or any other activity that violates applicable laws. Engaging in such activities may result in severe civil and criminal penalties.
>
> **3. No Warranty:** The Software is provided "AS IS," without any warranty of any kind, express or implied. This includes, but is not limited to, the implied warranties of merchantability, fitness for a particular purpose, and non-infringement. The developers and contributors make no guarantee that the Software will be error-free, secure, or uninterrupted.
>
> **4. Limitation of Liability:** In no event shall the developers, contributors, or distributors of the Software be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the Software or the use or other dealings in the Software. This includes any direct, indirect, incidental, special, exemplary, or consequential damages (including, but not to, procurement of substitute goods or services; loss of use, data, or profits; or business interruption).
