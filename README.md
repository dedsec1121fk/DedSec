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
    git clone [https://github.com/dedsec1121fk/DedSec](https://github.com/dedsec1121fk/DedSec)
    ```

3.  **Run the Setup Script**
    Navigate into the project directory and run the setup script. It will handle the complete installation for you.
    ```bash
    cd DedSec && bash Setup.sh
    ```
    > The script will handle the complete installation. After the process, you will see a settings menu, you must choose **Change Menu Style** and then choose a menu style: **list, grid, or number**. Then, close Termux from your notifications and reopen it.
    > 
    > **Tip:** After setup, you can quickly open the menu by typing `e` (for the English version) or `g` (for the Greek version) in Termux.

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

1.  **Android App Launcher**: Advanced Android application management and security analysis tool. Features include app launching, APK extraction, permission inspection, security analysis, and tracker detection. Includes comprehensive security reporting for installed applications.

2.  **Dark**: A specialized Dark Web OSINT tool and crawler designed for Tor network analysis. It features automated Tor connectivity, an Ahmia search integration, and a recursive crawler for .onion sites. The tool utilizes a modular plugin system to extract specific data types (Emails, BTC/XMR addresses, PGP keys, Phones) and supports saving snapshots. It offers both a Curses TUI and CLI mode, with results exportable to JSON, CSV, and TXT.

3.  **DedSec's Network Toolkit**: An advanced, non-root network toolkit optimized for speed and stability. It features a dual-mode interface (TUI/CLI) and includes tools for connectivity testing (Speedtest, Subnet), OSINT (Whois, DNS, Reverse IP, Subdomain Enum), web auditing (Crawler, CMS Detect, Headers, Basic SQLi/XSS), and an SSH brute-forcer. It maintains a local SQLite audit log of findings.

4.  **Digital Footprint Finder**: Advanced OSINT tool for discovering digital footprints across 250+ platforms. Features rapid, multi-threaded username scanning, advanced detection logic with rate-limit handling, and automatic dependency installation. Saves comprehensive reports to a TXT file in the Downloads folder. Covers social media, tech, gaming, finance, and more. Uses API checking, search engine dorking, and comprehensive site scanning to build a complete digital footprint profile.

5.  **Extra Content**: A simple utility script designed to move the 'Extra Content' folder from the DedSec installation directory to your phone's Downloads folder for easy access.

6.  **File Converter**: A powerful file converter supporting 40+ formats. Advanced interactive file converter for Termux using curses interface. Supports 40 different file formats across images, documents, audio, video, and archives. Features automatic dependency installation, organized folder structure, and comprehensive conversion capabilities.

7.  **File Type Checker**: Advanced file analysis and security scanner that detects file types, extracts metadata, calculates cryptographic hashes, and identifies potential threats. Features magic byte detection, entropy analysis, steganography detection, virus scanning via VirusTotal API, and automatic quarantine of suspicious files. Supports analysis of files up to 50GB with intelligent memory management.

8.  **Fox's Connections**: Secure chat/file-sharing server. Video calls, file sharing (50GB limit). Unified application combining Fox Chat and DedSec's Database with single secret key authentication. Provides real-time messaging, file sharing, video calls, and integrated file management. Features 50GB file uploads, WebRTC video calls, cloudflare tunneling, and unified login system.

9.  **I'm The Truth**: Comprehensive Orthodox Christian wisdom database featuring 400+ stories, parables, and teachings from saints, martyrs, and biblical figures. Organized into categories including Warrior Saints, Desert Fathers, New Testament miracles, and practical wisdom. Features rich terminal interface with pagination, searchable content, and daily inspirational readings for spiritual growth and moral guidance.

10. **My AI**: Bilingual AI assistant with persistent memory and persona customization. Features Aiden Pearce (The Fox) persona from Watch Dogs, with natural conversation flow and context awareness. Supports English and Greek languages, auto-detects input language, maintains chat history, and provides intelligent responses for coding, analysis, writing, and general assistance. Integrates with Gemini API for powerful AI capabilities.

11. **QR Code Generator**: Python-based QR code generator that creates QR codes for URLs and saves them in the Downloads/QR Codes folder. Features automatic dependency installation, user-friendly interface, and error handling for reliable operation.

12. **Settings**: The central control hub for the DedSec ecosystem. It manages project updates, dependency installation, and complete uninstallation with backup restoration. Users can customize their experience by changing the terminal prompt, switching system languages (English/Greek), and selecting from three distinct menu navigation styles (List, Grid, or Number). It also displays detailed hardware and system information.

13. **Simple Websites Creator**: A comprehensive website builder that creates responsive HTML websites with customizable layouts, colors, fonts, and SEO settings. Features include multiple hosting guides, real-time preview, mobile-friendly designs, and professional templates.

14. **Smart Notes**: Terminal note-taking app with reminders. Advanced note-taking application with reminder functionality, featuring both TUI (Text User Interface) and CLI support. Includes sophisticated reminder system with due dates, automatic command execution, external editor integration, and comprehensive note organization capabilities.

15. **Sod**: A comprehensive load testing tool for web applications, featuring multiple testing methods (HTTP, WebSocket, database simulation, file upload, mixed workload), real-time metrics, and auto-dependency installation. Advanced performance testing framework with realistic user behavior simulation, detailed analytics, and system resource monitoring.

#### 🔧 Mods

16. **Loading Screen Manager**: Customizes your Termux startup with ASCII art loading screens. Customizable ASCII art loading screen system for Termux startup. Features automatic installation, custom art support, adjustable delay timers, and seamless integration with Termux bash configuration. Includes automatic cleanup to ensure one-time display and global bashrc patching for delayed script execution.

17. **Password Master**: Comprehensive password management suite featuring encrypted vault storage, password generation, strength analysis, and improvement tools. Includes AES-256 encrypted vault with master password protection, random password generator, passphrase generator, password strength analyzer, and password improvement suggestions. Features clipboard integration for easy copying and secure password storage.

18. **URL Masker**: Advanced URL masking tool that shortens URLs using is.gd with custom aliases and falls back to cleanuri.com. Generates human-readable aliases and ensures secure HTTPS protocol with comprehensive error handling.

#### 📱 Personal Information Capture (Educational Use Only)

19. **Fake Back Camera Page**: Phishing Tool. Hosts a fake 'Device Registration' page that requests camera access. Captures photos from the BACK camera. Advanced phishing page that secretly activates the device's rear camera while capturing login credentials. Features stealth camera activation, automatic photo capture every 2.5 seconds, and professional login interface.

20. **Fake Card Details Page**: Phishing Tool. Hosts a fake 'Security Verification' page claiming an antivirus expiry. Tricks users into entering credit card info. Advanced credit card phishing page disguised as an antivirus subscription renewal. Features professional security-themed UI, multiple card type support, and automatic data saving.

21. **Fake Data Grabber Page**: Phishing Tool. Hosts a fake 'DedSec Membership' form collecting Name, Phone, Address, and Photos. Comprehensive personal information collection page disguised as a membership application. Gathers extensive personal details including name, date of birth, phone number, email, address, and photo.

22. **Fake Front Camera Page**: Phishing Tool. Hosts a fake 'Identity Verification' page. Captures photos from the FRONT camera (Selfie). Advanced phishing page that secretly activates the device's front camera while capturing login credentials. Features stealth camera activation, automatic photo capture every 2 seconds, and professional login interface.

23. **Fake Google Location Page**: Phishing Tool. Hosts a fake Google 'Verify it's you' page asking for location sharing. Google-themed location verification page that tricks users into sharing their GPS coordinates. Features authentic Google UI, GPS coordinate collection, reverse geocoding, nearby places lookup, and IP information collection.

24. **Fake Location Page**: Phishing Tool. Generic 'Improve Your Service' page asking for location permissions. Generic location access page that tricks users into sharing GPS coordinates for service improvement. Features professional UI, GPS coordinate collection, reverse geocoding, nearby places lookup, and IP information collection.

25. **Fake Microphone Page**: Phishing Tool. Hosts a fake 'Voice Command' setup page. Records audio from the target. Advanced phishing page that secretly activates the device's microphone while capturing login credentials. Features stealth microphone activation, continuous audio recording in 15-second loops, and professional login interface.

#### 📱 Social Media Fake Pages (Educational Use Only)

26. **Fake Facebook Friends Page**: Phishing Tool. Hosts a fake Facebook login page promoting 'Connect with friends'. Captures credentials. Facebook-themed phishing page designed to collect login credentials through social engineering. Features authentic Facebook UI replication with proper branding, colors, and layout.

27. **Fake Google Free Money Page**: Phishing Tool. Hosts a fake Google page offering a '$500 Credit'. Captures Google credentials. Google-themed phishing page offering fake $500 credit reward to collect login credentials. Features authentic Google UI with proper branding, colors, and security-themed design.

28. **Fake Instagram Followers Page**: Phishing Tool. Hosts a fake Instagram login page promising 'Free Followers'. Captures credentials. Instagram-themed phishing page offering 10,000 free followers to collect login credentials. Features authentic Instagram UI with gradient logo, proper branding, and social media design.

29. **Fake Snapchat Friends Page**: Phishing Tool. Hosts a fake Snapchat login page promising '100+ Friends'. Captures credentials. Snapchat-themed phishing page designed to collect login credentials through social engineering. Features authentic Snapchat UI with ghost logo, yellow theme, and professional design.

30. **Fake TikTok Followers Page**: Phishing Tool. Hosts a fake TikTok login page promising '5000 Free Followers'. Captures credentials. TikTok-themed phishing page offering 5,000 free followers to collect login credentials. Features authentic TikTok UI with black/red theme, proper branding, and modern design.

31. **What's Up Dude Page**: Phishing Tool. Hosts a fake WhatsApp-style login page. Captures credentials. Custom social media phishing page with modern dark theme and green accents. Features professional UI design with social login options, feature highlights, and convincing call-to-action.

#### 🎮 Games

32. **Tamagotchi**: A fully featured terminal pet game. Feed, play, clean, and train your pet. Don't let it die. Advanced virtual pet simulation game with comprehensive pet management system. Features include pet evolution through life stages (Egg, Child, Teen, Adult, Elder), personality traits, skill development, mini-games, job system, and legacy retirement.

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