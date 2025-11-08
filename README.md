<div align="center">
  <img src="https://raw.githubusercontent.com/dedsec1121fk/dedsec1121fk.github.io/ef4b1f5775f5a6fb7cf331d8f868ea744c43e41b/Assets/Images/Custom%20Purple%20Fox%20Logo.png" alt="DedSec Project Logo" width="150"/>
  <h1>DedSec Project</h1>
  <p>
    <a href="https://ded-sec.space/"><strong>Official Website</strong></a>
  </p>
  
  <p>
    <img src="https://img.shields.io/badge/Purpose-Educational-blue.svg" alt="Purpose: Educational">
    <img src="https://img.shields.io/badge/Platform-Android%20(Termux)-brightgreen.svg" alt="Platform: Android (Termux)">
    <img src="https://img.shields.io/badge/Language-Python%20%7C%20JS%20%7C%20Shell-yellow.svg" alt="Language: Python | JS | Shell">
    <img src="https://img.shields.io/badge/Interface-EN%20%7C%20GR-lightgrey.svg" alt="Interface: EN | GR">
  </p>
</div>

---

The **DedSec Project** is a toolkit designed for educational purposes, providing scripts and guides that cover everything from understanding phishing attacks to turning your phone into a portable, powerful command-line environment. Everything here is completely free and designed to help you shift from being a target to being a defender.

## 📋 Table of Contents

* [Understand What The DedSec Project Does](#🛡️-understand-what-the-dedsec-project-does)
* [How To Install And Setup The DedSec Project](#🚀-how-to-install-and-setup-the-dedsec-project)
* [Contact Us & Credits](#💬-contact-us--credits)
* [Disclaimer & Terms of Use](#⚠️-disclaimer--terms-of-use)

---

## 🛡️ Understand What The DedSec Project Does

> **CRITICAL NOTICE:** The following scripts are included for **educational and defensive purposes ONLY**. Their function is to demonstrate how common attacks work, so you can learn to recognize and protect yourself against them. They should only be used in a controlled environment, **on your own devices and accounts**, for self-testing.

### Toolkit Summary

The toolkit includes the following main categories and tools:

#### 🛠️ Basic Toolkit

1. **Android App Launcher**: Advanced Android application management and security analysis tool with APK extraction, permission inspection, and tracker detection.
2. **DedSec's Network Toolkit**: Comprehensive network and security toolkit featuring Wi-Fi scanning, port scanning, OSINT gathering, vulnerability assessment, and SSH honeypot defense.
3. **Digital Footprint Finder**: Advanced OSINT tool for discovering digital footprints across multiple platforms with stealth mode operation and comprehensive reporting.
4. **Extra Content**: Utility script for managing and extracting extra content in the DedSec toolkit.
5. **File Converter**: Advanced interactive file converter supporting 40+ formats across images, documents, audio, video, and archives.
6. **Fox's Connections**: Unified application combining Fox Chat and DedSec's Database with real-time messaging, 50GB file sharing, and WebRTC video calls.
7. **QR Code Generator**: Python-based QR code generator that creates QR codes for URLs with automatic dependency installation.
8. **Settings**: Central configuration and management tool for project updates, language selection, menu customization, and system information.
9. **Smart Notes**: Advanced note-taking application with reminder functionality, TUI/CLI support, and automatic command execution.

#### 🔧 Mods

10. **URL Masker**: Advanced URL masking tool that shortens URLs using is.gd with custom aliases and cleanuri.com fallback.
11. **Loading Screen Manager**: Customizable ASCII art loading screen system for Termux startup with adjustable delay timers.

#### 📱 Personal Information Capture (Educational Use Only)

12. **Fake Back Camera Page**: Secretly activates device's rear camera while capturing login credentials with automatic photo capture.
13. **Fake Front Camera Page**: Secretly activates device's front camera while capturing login credentials.
14. **Fake Card Details Page**: Credit card phishing page disguised as antivirus subscription renewal.
15. **Fake Data Grabber Page**: Comprehensive personal information collection disguised as membership application.
16. **Fake Google Location Page**: Google-themed location verification page that tricks users into sharing GPS coordinates.
17. **Fake Location Page**: Generic location access page for GPS coordinate collection.
18. **Fake Microphone Page**: Secretly activates device's microphone while capturing login credentials with continuous audio recording.

#### 📱 Social Media Fake Pages (Educational Use Only)

19. **Fake Facebook Friends Page**: Facebook-themed phishing page with authentic UI replication.
20. **Fake Snapchat Friends Page**: Snapchat-themed phishing page with ghost logo and yellow theme.
21. **Fake Google Free Money Page**: Google-themed phishing page offering fake $500 credit reward.
22. **Fake Instagram Followers Page**: Instagram-themed phishing page offering 10,000 free followers.
23. **Fake TikTok Followers Page**: TikTok-themed phishing page offering 5,000 free followers.
24. **What's Up Dude Page**: Custom social media phishing page with modern dark theme and green accents.

---

## 🚀 How To Install And Setup The DedSec Project

Get the DedSec Project command-line tools running on your **Android device with Termux**.

### Requirements

| Component | Minimum Specification |
| :-------- | :------------------------------------------------------------------- |
| **Device** | Android with [Termux](https://f-droid.org/) installed |
| **Storage** | Min **8GB** free. (Images and recordings also consume space.) |
| **RAM** | Min **2GB** |

### Step-by-Step Setup

> **Note:** To install APKs (e.g., F-Droid), ensure you:
> - Enable unknown sources (Settings > Security > **Install Unknown Apps**).
> - Download F-Droid, then get Termux from [F-Droid](https://f-droid.org/).
> - Install add-ons: Termux:API, Termux:Styling.
> - Allow the `fdroid` process when prompted.

1.  **Update Packages & Install Git**
    Open Termux and run the following command to make sure your packages are up-to-date and `git` is installed:
    ```bash
    pkg update -y && pkg upgrade -y && pkg install git nano -y && termux-setup-storage
    ```
    > **Important:** Open the Termux application on your device before copying and pasting the command above.

2.  **Clone the Repository**
    Download the project files from GitHub:
    ```bash
    git clone https://github.com/dedsec1121fk/DedSec
    ```

3.  **Run the Setup Script**
    Navigate into the project directory and run the setup script. It will handle the complete installation for you.
    ```bash
    cd DedSec && bash Setup.sh
    ```
    > The script will handle the complete installation. After the process, you will see a settings menu, you must choose **Change Menu Style** and then choose a menu style: **list or grid**. Then, close Termux from your notifications and reopen it.
    > 
    > **Tip:** After setup, you can quickly open the menu by typing `e` (for the English version) or `g` (for the Greek version) in Termux.

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

### Privacy Policy Summary

We are committed to protecting your privacy. **We do not store or transmit your personal data**. We use third-party services like Google AdSense, which may use cookies for advertising. Please review their policies. By using our service, you agree to our full Privacy Policy.

> **By using the Software, you confirm that you have read, understood, and agree to be bound by all the terms and conditions outlined in this disclaimer and our full Privacy Policy.**