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
* [Community & Contact](#-community--contact)
* [Legal Disclaimer & Terms of Use](#️-legal-disclaimer--terms-of-use)

---

## 🚀 Installation & Usage (Command-Line Tools)

Get the DedSec Project command-line tools running on your **Android device with Termux**.

### Requirements

| Component | Minimum Specification |
| :-------- | :------------------------------------------------------------------- |
| **Device** | Android with [Termux](https://f-droid.org/) installed |
| **Storage** | **3GB** of free space (The Radio feature requires more storage; images and recordings also consume space.) |
| **RAM** | **2GB** |

### Step-by-Step Setup

> **Note:** For best results, install Termux from the [F-Droid](https://f-droid.org/) store. This ensures you can also install necessary add-ons like `Termux:API`. You may need to enable "**Install Unknown Apps**" in your Android settings.

1.  **Update Packages & Install Git**
    Open Termux and run the following command to make sure your packages are up-to-date and `git` is installed:
    ```bash
    pkg update -y && pkg upgrade -y && pkg install git nano -y
    ```

2.  **Clone the Repository**
    Download the project files from GitHub:
    ```bash
    git clone [https://github.com/dedsec1121fk/DedSec](https://github.com/dedsec1121fk/DedSec)
    ```

3.  **Run the Setup Script**
    Navigate into the project directory and run the setup script. It will handle the complete installation for you.
    ```bash
    cd DedSec && bash Setup.sh
    ```
    > After the installation finishes, a settings menu will appear. You must choose a menu style (list or grid). Then, close Termux from your notifications and reopen it to start.
    > 
    > You can open the main menu later by just typing `m` in Termux.

---

## 🛡️ Digital Self-Defense Toolkit

> **CRITICAL NOTICE:** The following scripts are included for **educational and defensive purposes ONLY**. Their function is to demonstrate how common attacks work, so you can learn to recognize and protect yourself against them. They should only be used in a controlled environment, **on your own devices and accounts**, for self-testing.

### Toolkit Summary

The toolkit includes the following main features:

1.  **Fox Chat**: A secure, **end-to-end encrypted chat** application. Features include text messaging, voice notes, file sharing (up to **25MB**), live camera capture, and **peer-to-peer video calls**.
2.  **DedSec Database**: A **self-hosted, web-based file storage server**. It allows you to upload, download, and manage files through a local or online link. All uploaded files are stored in a **`Database`** folder created in the script's directory.
3.  **Radio**: An **offline music player** that allows you to download music "stations" from the official DedSec repository and play them locally. All downloaded music is saved to the **`~/DedSec-Radio`** folder in your Termux home directory.
4.  **OSINTDS**: A comprehensive tool for **Open Source Intelligence (OSINT)** gathering and web reconnaissance. It performs scans for **WHOIS and DNS records, open ports, subdomains, and directories**, and checks for common vulnerabilities like **SQLi and XSS**. It also includes an interactive **HTML Inspector** to download a full copy of a website for offline analysis. All reports and downloaded websites are saved in a dedicated folder inside **`[Your Downloads]/OSINTDS/`**.
5.  **Phishing Demonstrations**: Modules that demonstrate how a malicious webpage can trick a user into giving away access to their device's camera, microphone, and location, or into entering personal details and card information. These scripts are for testing on your own devices to understand the importance of verifying links before clicking them. Any demonstration credentials or data you enter are saved locally into appropriately named folders inside your phone's main **Downloads** folder for you to review.
6.  **URL Masker**: An educational tool to demonstrate how links can be disguised, helping you learn to identify potentially malicious URLs by showing how a seemingly innocent link can redirect to a different destination.
7.  **Android App Launcher**: A utility to **manage installed applications** on your Android device. You can use it to quickly launch, view details for, or uninstall any launchable app.
8.  **Settings**: A central control panel to manage the DedSec Project. Use it to view system information, **update all project scripts and required packages**, **change the Termux prompt style**, and switch between list or grid menu layouts. This script modifies your **`/data/data/com.termux/files/usr/etc/bash.bashrc`** file to apply changes.
9.  **Loading Screen**: Installs a custom **ASCII art loading screen** that appears when you start Termux. You can use the default art, provide your own, and set the display duration. This script works by adding configuration to your **`~/.bash_profile`**.

---

## 💬 Community & Contact
For questions, support, or general inquiries, connect with the DedSec Project community through our official channels:

* **Official Website:** [https://ded-sec.space/](https://ded-sec.space/)
* **Official Store:** [https://dedsec1121fk.gumroad.com](https://dedsec1121fk.gumroad.com)
* **📱 WhatsApp:** +37257263676
* **📸 Instagram:** @dedsec_project_official
* **✈️ Telegram:** @dedsecproject

---

## ⚠️ Legal Disclaimer & Terms of Use

> **PLEASE READ CAREFULLY BEFORE PROCEEDING**.

**Trademark Disclaimer:** The "DedSec" name and logo used in this project are for thematic and inspirational purposes only. This is an independent, fan-made project created for educational purposes and has no official connection to the "Watch Dogs" franchise. It is not associated with, endorsed by, or affiliated with Ubisoft Entertainment S.A. All trademarks and copyrights for "Watch Dogs" and "DedSec" as depicted in the games belong to their respective owners, Ubisoft Entertainment S.A.

This project, including all associated tools, scripts, and documentation ("the Software"), is provided strictly for **educational, research, and ethical security testing purposes**. It is intended for use exclusively in controlled, authorized environments by users who have obtained explicit, prior written permission from the owners of any systems they intend to test.

1.  **Assumption of Risk and Responsibility:** By accessing or using the Software, you acknowledge and agree that you are doing so at your own risk. You are **solely and entirely responsible for your actions** and for any consequences that may arise from the use or misuse of this Software. This includes, but is not limited to, compliance with all applicable local, state, national, and international laws and regulations related to cybersecurity, data privacy, and electronic communications.

2.  **Prohibited Activities:** Any use of the Software for unauthorized or malicious activities is **strictly prohibited**. This includes, without limitation: accessing systems, systems, or data without authorization; performing denial-of-service attacks; data theft; fraud; spreading malware; or any other activity that violates applicable laws. Engaging in such activities may result in severe civil and criminal penalties.

3.  **No Warranty:** The Software is provided **"AS IS,"** without any warranty of any kind, express or implied. This includes, but is not limited to, the implied warranties of merchantability, fitness for a particular purpose, and non-infringement. The developers and contributors make **no guarantee** that the Software will be error-free, secure, or uninterrupted.

4.  **Limitation of Liability:** In no event shall the developers, contributors, or distributors of the Software be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the Software or the use or other dealings in the Software. This includes any direct, indirect, incidental, special, exemplary, or consequential damages (including, but not to, procurement of substitute goods or services; loss of use, data, or profits; or business interruption).

---

### Privacy Policy Summary

We are committed to protecting your privacy. **We do not store or transmit your personal data.** We use third-party services like Google AdSense, which may use cookies for advertising. Please review their policies. By using our service, you agree to our full Privacy Policy.

> **By using the Software, you confirm that you have read, understood, and agree to be bound by all the terms and conditions outlined in this disclaimer and our full Privacy Policy.**