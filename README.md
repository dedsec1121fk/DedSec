<div align="center">
  <img src="https://raw.githubusercontent.com/dedsec1121fk/dedsec1121fk.github.io/ef4b1f5775f5a6fb7cf331d8f868ea744c43e41b/Assets/Images/Custom%20Purple%20Fox%20Logo.png" alt="DedSec Project Logo" width="150"/>
  <h1>DedSec Project</h1>
  <p>
    <a href="https://ded-sec.space/"><strong>Official Website</strong></a>
  </p>
  <p>
    <a href="https://github.com/sponsors/dedsec1121fk"><img src="https://img.shields.io/badge/Sponsor-❤-purple?style=for-the-badge&logo=GitHub" alt="Sponsor Project"></a>
  </p>
  
  <p>
    <img src="https://img.shields.io/badge/Purpose-Educational-blue.svg" alt="Purpose: Educational">
    <img src="https://img.shields.io/badge/Platform-Android%20(Termux)-brightgreen.svg" alt="Platform: Android (Termux)">
    <img src="https://img.shields.io/badge/Language-Python%20%7C%20JS%20%7C%20Shell-yellow.svg" alt="Language: Python | JS | Shell">
    <img src="https://img.shields.io/badge/Interface-EN%20%7C%20GR-lightgrey.svg" alt="Interface: EN | GR">
  </p>
</div>

---

The **DedSec Project** is a comprehensive cybersecurity toolkit designed for educational purposes, providing 32+ powerful tools that cover everything from network security analysis to ethical hacking education. Everything here is completely free and designed to help you shift from being a target to being a defender.

## 📋 Table of Contents

* [How To Install And Setup The DedSec Project](#🚀-how-to-install-and-setup-the-dedsec-project)
* [Settings & Configuration](#⚙️-settings--configuration)
* [Explore The Toolkit](#🛡️-explore-the-toolkit)
* [Contact Us & Credits](#💬-contact-us--credits)
* [Disclaimer & Terms of Use](#⚠️-disclaimer--terms-of-use)

---

## 🚀 How To Install And Setup The DedSec Project

Get the DedSec Project command-line tools running on your **Android device with Termux**.

### Requirements

| Component | Minimum Specification |
| :-------- | :------------------------------------------------------------------- |
| **Device** | Android with Termux installed |
| **Storage** | Min **8GB** free. (Images and recordings also consume space.) |
| **RAM** | Min **2GB** |

### Step-by-Step Setup

> **Note:** To install APKs (e.g., F-Droid), ensure you enable unknown sources in **Settings > Security > Install Unknown Apps**.

1.  **Install F-Droid & Termux**
    F-Droid is the recommended way to install Termux and other security tools.
    * Download and install the [F-Droid APK](https://f-droid.org/).
    * Open F-Droid and search for **Termux** to install it.
    * **Recommended Add-ons:** Install **Termux:API** and **Termux:Styling** from F-Droid for full functionality.

2.  **Update Packages & Install Git**
    Open Termux and run the following command to make sure your packages are up-to-date and `git` is installed:
    ```bash
    pkg update -y && pkg upgrade -y && pkg install git nano -y && termux-setup-storage
    ```
    > **Tip:** To prevent the screen from turning off during long operations: long-press the Termux terminal, then tap 'More' and select 'Keep screen on'.

3.  **Clone the Repository**
    Download the project files from GitHub:
    ```bash
    git clone [https://github.com/dedsec1121fk/DedSec](https://github.com/dedsec1121fk/DedSec)
    ```

4.  **Run the Setup Script**
    Navigate into the project directory and run the setup script. It will handle the complete installation for you.
    ```bash
    cd DedSec && bash Setup.sh
    ```
    > The script will handle the complete installation. After the process, you will see a settings menu; you must choose **Change Menu Style** and then choose a menu style: **list, grid, or number**. Then, close Termux from your notifications and reopen it.
    > 
    > **Quick Launch:** After setup, you can quickly open the menu by typing `e` (English) or `g` (Greek) in Termux.

---

## ⚙️ Settings & Configuration

The DedSec Project includes a comprehensive **Settings.py** tool that provides centralized control over your toolkit:

### Settings Features

- **Project Updates**: Automatic package management and updates
- **Language Selection**: Persistent language preference (English/Greek)
- **Menu Customization**: Choose between three menu styles: list, grid, or number selection
- **Prompt Configuration**: Customize your terminal prompt
- **System Information**: Display hardware details and system status
- **Home Scripts Integration**: Access and run scripts from your home directory
- **Backup & Restore**: Automatic configuration backup and restore functionality
- **Complete Uninstall**: Remove the project completely with cleanup
- **Automatic Bash Configuration**: Updates your Termux configuration automatically
- **Credits & Project Information**: View project credits and information

### First-Time Setup

After installation, access the settings menu to:
1. Select your preferred language
2. Choose your menu style (list/grid/number)
3. Configure system preferences
4. Update all tools to latest versions

---

## 🛡️ Explore The Toolkit

> **CRITICAL NOTICE:** The following scripts are included for **educational and defensive purposes ONLY**. Their function is to demonstrate how common attacks work, so you can learn to recognize and protect yourself against them. They should only be used in a controlled environment, **on your own devices and accounts**, for self-testing.

### Toolkit Summary

The toolkit includes the following main categories and tools:

#### 🛠️ Basic Toolkit

1.  **Android App Launcher**: Advanced Android application management and security analysis tool. Features include app launching, APK extraction, permission inspection, security analysis, and tracker detection.
    * *Save Location:* `~/storage/shared/Download/Extracted APK's` (APKs) | `~/storage/shared/Download/App_Security_Reports` (Reports)

2.  **Dark**: A specialized Dark Web OSINT tool and crawler designed for Tor network analysis. Features automated Tor connectivity, Ahmia search integration, and a recursive crawler for .onion sites.
    * *Save Location:* `/sdcard/Download/DarkNet` (or `~/DarkNet` if storage is inaccessible)

3.  **DedSec's Network Toolkit**: An advanced, non-root network toolkit optimized for speed and stability. Includes tools for connectivity testing, OSINT (Whois, DNS, Reverse IP), web auditing, and an SSH brute-forcer.
    * *Save Location:* `~/DedSec_Tools`

4.  **Digital Footprint Finder**: Advanced OSINT tool for discovering digital footprints across 250+ platforms. Features rapid, multi-threaded username scanning and advanced detection logic.
    * *Save Location:* `~/storage/downloads/Digital Footprint Finder/[username].txt`

5.  **Extra Content**: A simple utility script designed to move the 'Extra Content' folder from the DedSec installation directory to your phone's Downloads folder for easy access.
    * *Save Location:* `~/storage/downloads/Extra Content`

6.  **File Converter**: A powerful interactive file converter supporting 40+ formats across images, documents, audio, video, and archives.
    * *Save Location:* `~/storage/downloads/File Converter/`

7.  **File Type Checker**: Advanced file analysis and security scanner that detects file types, extracts metadata, calculates hashes, and identifies potential threats (magic byte detection, VirusTotal API).
    * *Save Location:* `/sdcard/Download/File Type Checker` (Quarantined files renamed with `.dangerous`)

8.  **Fox's Connections**: Secure chat/file-sharing server. Unified application combining Fox Chat and DedSec's Database. Features 50GB file uploads, WebRTC video calls, and Cloudflare tunneling.
    * *Save Location:* `~/Downloads/DedSec's Database`

9.  **I'm The Truth**: Comprehensive Orthodox Christian wisdom database featuring 400+ stories, parables, and teachings.
    * *Save Location:* Internal database.

10. **My AI**: Bilingual AI assistant (English/Greek) with persistent memory and persona customization (Aiden Pearce). Integrates with Gemini API for powerful AI capabilities.
    * *Save Location:* `~/.local/share/my_ai/config.json` (Config) | `~/.local/share/my_ai/history.json` (History)

11. **QR Code Generator**: Python-based QR code generator that creates QR codes for URLs.
    * *Save Location:* `~/storage/downloads/QR Codes/`

12. **Settings**: The central control hub. Manages project updates, language (English/Greek), menu styles (List/Grid/Number), and backups.
    * *Save Location:* `~/Language.json` (Config) | `~/Termux.zip` (Backups)

13. **Simple Websites Creator**: A comprehensive website builder that creates responsive HTML websites with customizable layouts and SEO settings.
    * *Save Location:* `~/storage/downloads/Websites/`

14. **Smart Notes**: Terminal note-taking app with reminder functionality, featuring both TUI and CLI support.
    * *Save Location:* `~/.smart_notes.json`

15. **Sod**: A comprehensive load testing tool for web applications. Features multiple testing methods (HTTP, WebSocket, database simulation) and real-time metrics.
    * *Save Location:* `load_test_config.json` (in script directory)

#### 🔧 Mods

16. **Loading Screen Manager**: Customizes your Termux startup with ASCII art loading screens.
    * *System Modification:* Modifies `.bash_profile` and `bash.bashrc`.

17. **Password Master**: Comprehensive password management suite featuring encrypted vault storage, generation, and strength analysis.
    * *Save Location:* `my_vault.enc` (in script directory) | `~/storage/emulated/0/Download/Password Master Backup` (Backups)

18. **URL Masker**: Advanced URL masking tool that shortens URLs using is.gd with custom aliases and falls back to cleanuri.com to create unsuspicious links.
    * *Output:* Displayed on screen.

#### 📱 Personal Information Capture (Educational Use Only)

19. **Fake Back Camera Page**: Phishing page that secretly activates the device's rear camera while capturing login credentials.
    * *Save Location:* `~/storage/downloads/Camera-Phish-Back`

20. **Fake Card Details Page**: Phishing page disguised as an antivirus subscription renewal to capture credit card information.
    * *Save Location:* `~/storage/downloads/CardActivations`

21. **Fake Data Grabber Page**: "DedSec Membership" form collecting Name, Phone, Address, and Photos.
    * *Save Location:* `~/storage/downloads/Peoples_Lives`

22. **Fake Front Camera Page**: Phishing page that secretly activates the device's front camera (selfie) while capturing login credentials.
    * *Save Location:* `~/storage/downloads/Camera-Phish-Front`

23. **Fake Google Location Page**: Google-themed verification page that tricks users into sharing GPS coordinates.
    * *Save Location:* `~/storage/downloads/Locations`

24. **Fake Location Page**: Generic "Improve Your Service" page asking for location permissions.
    * *Save Location:* `~/storage/downloads/Locations`

25. **Fake Microphone Page**: Phishing page that secretly activates the device's microphone to record audio.
    * *Save Location:* `~/storage/downloads/Recordings`

#### 📱 Social Media Fake Pages (Educational Use Only)

26. **Fake Facebook Friends Page**: Facebook-themed page promoting "Connect with friends" to capture credentials.
    * *Save Location:* `~/storage/downloads/FacebookFriends`

27. **Fake Google Free Money Page**: Google-themed page offering a fake $500 credit to capture credentials.
    * *Save Location:* `~/storage/downloads/GoogleFreeMoney`

28. **Fake Instagram Followers Page**: Instagram-themed page offering free followers to capture credentials.
    * *Save Location:* `~/storage/downloads/InstagramFollowers`

29. **Fake Snapchat Friends Page**: Snapchat-themed page promising instant friends addition.
    * *Save Location:* `~/storage/downloads/SnapchatFriends`

30. **Fake TikTok Followers Page**: TikTok-themed page offering free followers to capture credentials.
    * *Save Location:* `~/storage/downloads/TikTokFollowers`

31. **What's Up Dude Page**: Fake WhatsApp-style login page with a modern dark theme.
    * *Save Location:* `~/storage/downloads/WhatsUpDude`

#### 🎮 Games

32. **Tamagotchi**: A fully featured terminal pet game. Feed, play, clean, and train your pet through various life stages (Egg to Elder).
    * *Save Location:* `~/.termux_tamagotchi_v8.json`

---

## 💬 Contact Us & Credits

### Contact Us

For questions, support, or general inquiries, connect with the DedSec Project community through our official channels:

* **Official Website:** [https://ded-sec.space/](https://ded-sec.space/)
* **📱 WhatsApp:** [+37257263676](https://wa.me/37257263676)
* **📸 Instagram:** [@dedsec_project_official](https://www.instagram.com/dedsec_project_official)
* **✈️ Telegram:** [@dedsecproject](https://t.me/dedsecproject)

### Credits

* **Creator:** dedsec1121fk
* **Artwork:** Christina Chatzidimitriou
* **Technical Help:** lamprouil, UKI_hunter

---

## ⚠️ Disclaimer & Terms of Use

> **PLEASE READ CAREFULLY BEFORE PROCEEDING.**

**Trademark Disclaimer:** The "DedSec" name and logo used in this project are for thematic and inspirational purposes only. This is an independent, fan-made project created for educational purposes and has no official connection to the "Watch Dogs" franchise. It is not associated with, endorsed by, or affiliated with Ubisoft Entertainment S.A.. All trademarks and copyrights for "Watch Dogs" and "DedSec" as depicted in the games belong to their respective owners, Ubisoft Entertainment S.A..

This project, including all associated tools, scripts, and documentation ("the Software"), is provided strictly for **educational, research, and ethical security testing purposes**. It is intended for use exclusively in controlled, authorized environments by users who have obtained explicit, prior written permission from the owners of any systems they intend to test.

1.  **Assumption of Risk and Responsibility:** By accessing or using the Software, you acknowledge and agree that you are doing so at your own risk. You are **solely and entirely responsible for your actions** and for any consequences that may arise from the use or misuse of this Software. This includes, but is not limited to, compliance with all applicable local, state, national, and international laws and regulations related to cybersecurity, data privacy, and electronic communications.

2.  **Prohibited Activities:** Any use of the Software for unauthorized or malicious activities is **strictly prohibited**. This includes, without limitation: accessing systems or data without authorization; performing denial-of-service attacks; data theft; fraud; spreading malware; or any other activity that violates applicable laws. Engaging in such activities may result in severe civil and criminal penalties.

3.  **No Warranty:** The Software is provided **"AS IS,"** without any warranty of any kind, express or implied. The developers and contributors make **no guarantee** that the Software will be error-free, secure, or uninterrupted.

4.  **Limitation of Liability:** In no event shall the developers, contributors, or distributors of the Software be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the Software or the use or other dealings in the Software. This includes any direct, indirect, incidental, special, exemplary, or consequential damages (including, but not in, procurement of substitute goods or services; loss of use, data, or profits; or business interruption).

---