<div align="center">
  <img src="https://raw.githubusercontent.com/dedsec1121fk/dedsec1121fk.github.io/47ad8e5cbaaee04af552ae6b90edc49cd75b324b/Assets/Images/Logos/Black%20Purple%20Butterfly%20Logo.jpeg" alt="DedSec Project Logo" width="150"/>
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

The **DedSec Project** is a comprehensive cybersecurity toolkit designed for educational purposes, providing **63+ powerful tools** that cover everything from network security analysis to ethical hacking education. Everything here is completely free and designed to help you shift from being a target to being a defender.

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

The toolkit is organized into the following categories and tools:

- **Developer Base:** 9 tools
- **Network Tools:** 10 tools
- **Other Tools:** 6 tools
- **Games:** 5 tools
- **Personal Information Capture:** 17 tools
- **Social Media Fake Pages:** 25 tools
- **No Category:** 2 tools
- **Sponsors-Only:** 1 tool

**Total listed on tools page:** 75 tools
## 🧑‍💻 Developer Base

1. **File Converter**: A powerful file converter supporting 40+ formats.
    * *Save Location ~/storage/downloads/File Converter/*

2. **File Type Checker**: Advanced file analysis and security scanner that detects file types, extracts metadata, calculates cryptographic hashes, and identifies potential threats.
    * *Save Location Scan folder: ~/Downloads/File Type Checker/ | Quarantined files: .dangerous extension*

3. **Mobile Desktop**: Termux Linux Desktop Manager (no root): sets up a proot-distro desktop environment with VNC/X11 options and a built-in program manager for install/update/remov…
    * *Save Location Scan folders created in current directory (scan_[target]_[date])*

4. **Mobile Developer Setup**: Automates a mobile web-dev environment in Termux: installs common dev tools, configures paths, and provides quick-start project scaffolding.
    * *Save Location Scan folders created in current directory (scan_[target]_[date])*

5. **Simple Websites Creator**: A comprehensive website builder that creates responsive HTML websites with customizable layouts, colors, fonts, and SEO settings.
    * *Save Location Websites are saved in: ~/storage/downloads/Websites/*

6. **Smart Notes**: Terminal note-taking app with reminders.
    * *Save Location ~/.smart_notes.json*

7. **Dead Switch**: Syncs your `~/storage/downloads/Dead Switch/` folder to a GitHub repository with safety controls (create-only-new uploads, overwrite sync, and a one-click kill switch to wipe/delete the repo). Includes visibility toggle (public/private) and optional Termux:API notification buttons.
    * *Save Location ~/storage/downloads/Dead Switch/*

8. **Tree Explorer**: File-system explorer for Termux: browse folders, search files, find duplicates by hash, and clean empty directories with safe prompts.
    * *Save Location Scan folders created in current directory (scan_[target]_[date])*

9. **Devices Finder**: Local-network device discovery tool for Termux that works without root. It separates live-host discovery from service scanning to reduce false positives, classifies devices using ports, banners, hostnames, and vendor hints, includes interactive scan profiles and type filters, and can optionally enrich results with mDNS, UPnP, SNMP, and NetBIOS clues. It exports JSON, TXT, CSV, and HTML reports.
    * *Save Location Results are saved in: ~/storage/downloads/Devices Finder/ as devices_scan_[timestamp].json/.txt/.csv/.html (falls back to ~/downloads/Devices Finder/ or the current directory).*


## 🔧 Network Tools

1. **Bug Hunter**: Bug Hunter (no-root) — an authorized web security recon & misconfiguration scanner. Performs DNS (SPF/DMARC/CAA), TLS/cert expiry checks, security header & cookie-flag audits, tech fingerprinting, CORS/HTTP methods checks, sensitive file discovery, crawling, and JavaScript endpoint/secret analysis. Exports JSON/CSV/HTML/PDF reports.
    * *Save Location Reports are saved in the output folder (default: bughunter_out/): report.json, report.csv, report.html (and report.pdf if enabled)*

2. **Dark**: A specialized Dark Web OSINT tool and crawler designed for Tor network analysis.
    * *Save Location Results are saved in: /sdcard/Download/DarkNet (or ~/DarkNet if storage is inaccessible)*

3. **DedSec's Network**: An advanced, non-root network toolkit optimized for speed and stability.
    * *Save Location Reports and logs are saved in: ~/DedSec's Network*

4. **Digital Footprint Finder**: Conservative OSINT username scanner with pack-based coverage (core→mega incl. optional Sherlock DB), multi-signal verification to reduce false positives, and FOUND vs POSSIBLE results with optional DuckDuckGo dorking; can export TXT/JSON/CSV/HTML reports.
    * *Save Location Results are saved in: ~/storage/downloads/Digital Footprint Finder/[username]_[YYYYMMDD_HHMMSS].txt (plus optional .json/.csv/.html) — falls back to /sdcard/Download when Termux storage isn’t available*

5. **Connections.py**: Secure chat/file-sharing server with real-time messaging, file sharing (up to 50GB), and WebRTC video calls. Unified application combining Butterfly Chat and DedSec's Database with a single secret-key authentication system, integrated file management, and Cloudflare tunneling. Use only on systems you own or have explicit permission to test.
    * *Save Location Downloads to `~/Downloads/DedSec's Database`.*

6. **Link Shield**: Security-focused URL inspector: follows redirects, checks HTTPS/SSL, flags suspicious domains/patterns, and generates a risk report before you open a link.
    * *Save Location Scan folders created in current directory (scan_[target]_[date])*

7. **Masker**: URL Masker.
    * *Save Location N/A (Output to screen).*

8. **QR Code Generator**: Python-based QR code generator that creates QR codes for URLs and saves them in the Downloads/QR Codes folder.
    * *Save Location Images are saved to: ~/storage/downloads/QR Codes/*

9. **Sod**: A comprehensive load testing tool for web applications, featuring multiple testing methods (HTTP, WebSocket, database simulation, file upload, mixed workload),…
    * *Save Location Configuration: load_test_config.json in script directory | Results: Displayed in terminal*

10. **Store Scrapper**: Single-file Python store scraper for Termux that works without root. It tries multiple ways to discover categories and products across regular HTML pages and many JS-style stores by reading HTML, JSON-LD, embedded JSON, sitemaps, Shopify endpoints, WooCommerce APIs, generic product cards, breadcrumbs, OpenGraph/meta tags, and internal links. It saves while running, starts full product scraping the moment each product is found, shows live terminal status, uses Enter as the default for prompts, and organizes results into store/category/product folders with downloaded images. Use only on systems you own or have explicit permission to test.
    * *Save Location Results are saved in: ~/storage/downloads/Store Scrapper/<Store>/<Category>/<Product>/ with files such as metadata.json, summary.txt, description.txt, images/, images.json, category state files, and FINAL_REPORT.txt.*


## 📱 Personal Information Capture (Educational Use Only)

These scripts are **training simulations** intended to help you understand how personal-data collection attacks are presented, so you can learn to recognize and defend against them.

**Included tools:**
- **Fake Back Camera Page**
- **Fake Back Camera Video Page**
- **Fake Card Details Page**
- **Fake Chrome Verification Page**
- **Fake Data Grabber Page**
- **Fake Discord Verification Page**
- **Fake Facebook Verification Page**
- **Fake Front Camera Page**
- **Fake Front Camera Video Page**
- **Fake Google Location Page**
- **Fake Instagram Verification Page**
- **Fake Location Page**
- **Fake Microphone Page**
- **Fake OnlyFans Verification Page**
- **Fake Steam Verification Page**
- **Fake Twitch Verification Page**
- **Fake YouTube Verification Page**

> For full descriptions and save locations, check the website tools catalog.

## 📱 Fake Pages (Educational Use Only)

These scripts are **training simulations** intended to help you recognize social‑engineering patterns used in fake social media pages.

**Included tools:**
- **Fake Apple iCloud Page**
- **Fake Discord Nitro Page**
- **Fake Epic Games Page**
- **Fake Facebook Friends Page**
- **Fake Free Robux Page**
- **Fake GitHub Pro Page**
- **Fake Google Free Money Page**
- **Fake Instagram Followers Page**
- **Fake MetaMask Page**
- **Fake Microsoft 365 Page**
- **Fake OnlyFans Page**
- **Fake PayPal Page**
- **Fake Pinterest Pro Page**
- **Fake PlayStation Network Page**
- **Fake Reddit Karma Page**
- **Fake Snapchat Friends Page**
- **Fake Steam Games Page**
- **Fake Steam Wallet Page**
- **Fake TikTok Followers Page**
- **Fake Trust Wallet Page**
- **Fake Twitch Subs Page**
- **Fake Twitter Followers Page**
- **Fake What's Up Dude Page**
- **Fake Xbox Live Page**
- **Fake YouTube Subscribers Page**

> For full descriptions and save locations, check the website tools catalog.


## 🎮 Games

1. **Buzz**: A text-only trivia party game for Termux with a fixed built-in database of 15,000 questions (no runtime generation).
    * *Save Location ~/Buzz/ (data/ for DB, profiles, settings, highscores)*

2. **CTF God**: Full‑screen Curses CTF game for Termux with story mode, missions, daily challenges, random boss levels, hint shop economy, achievements & ranks, challenge pack…
    * *Save Location User workspaces & challenge files: /storage/emulated/0/Download/CTF God/ /files (fallback: ~/storage/downloads/CTF God/...). Game state & packs: ~/.ctf_god/ (state.json, packs/, custom.json).*

3. **Detective**: Story-driven terminal detective game for Termux with a large fixed case library, richer lore dossiers, district rumors, side stories, suspect rosters, evidence board and timeline views, and long-case pacing. Includes 4 difficulties (Rookie, Detective, Noir, Legend), 3 manual save slots plus autosave, note/evidence tracking, interrogation flow, checkpoint hints, and quick commands like `:help`, `:guide`, `:lore`, `:suspects`, `:board`, `:timeline`, `:hint`, and `:save`.
    * *Save Location `~/Detective/` (player config, autosave/manual saves, and case progress)*

    * *Gameplay Notes:* Accusations are intentionally locked until the case timer matures, so you investigate first instead of speed-running. The updated build also adds casefile lore screens with dossiers, district threads, legends, rumors, and lingering side-story beats.

4. **Tamagotchi**: A fully featured terminal pet game.
    * *Save Location ~/.termux_tamagotchi_v8.json*

5. **Terminal Arcade**: All-in-one terminal arcade pack with multiple mini-games in a single script.
    * *Save Location Scan folders created in current directory (scan_[target]_[date])*


## 🛠️ Other Tools

1. **Android App Launcher**: A utility to manage Android apps directly from the terminal.
    * *Save Location Extracted APKs: ~/storage/shared/Download/Extracted APK's | Reports: ~/storage/shared/Download/App_Security_Reports*

2. **Loading Screen**: Customize your Termux startup with ASCII art loading screens.
    * *Save Location Modifies `.bash_profile` and `bash.bashrc`.*

3. **Password Master**: Comprehensive password management suite featuring encrypted vault storage, password generation, strength analysis, and improvement tools.
    * *Save Location Vault file: my_vault.enc in script directory | Backups: ~/Downloads/Password Master Backup/*

4. **Termux Backup Restore**: Backup & restore for Termux: creates a zipped backup of your Termux files to Downloads and can restore them with integrity checks.
    * *Save Location Scan folders created in current directory (scan_[target]_[date])*

5. **Termux Repair Wizard**: Troubleshooting wizard for Termux: checks common issues (mirrors, packages, permissions), suggests fixes, and runs safe repair commands step-by-step.
    * *Save Location Scan folders created in current directory (scan_[target]_[date])*

6. **FaveSites.py**: A lightweight Termux bookmark manager that saves and organizes your favorite websites for quick access.
    * *Save Location Saved in your Termux home folder at: `~/FaveSites/` (auto-created if it doesn’t exist).* 


## 📁 No Category

1. **Extra Content**: Extra bonus content hub: quick access to additional resources, templates, and optional add-ons included in the DedSec toolkit.
    * *Save Location Scan folders created in current directory (scan_[target]_[date])*

2. **Settings**: The central control hub for the DedSec ecosystem.
    * *Save Location Language Config: ~/Language.json | Backups: ~/Termux.zip*


## 💜 Sponsors-Only

To access the scripts in this category, you need an active monthly GitHub subscription of **$10 or $15**.

1. **Face Detector.py**: Local face-detection tool for Termux that opens a browser-based interface, can detect faces from uploaded images or a live camera feed, and draws square boxes around detected faces.
    * *Save Location Generated files and temporary assets are handled locally by the script during use.*


## 🦋 ButSystem.py (Exclusive)

**ButSystem.py** is a self-hosted, **local-first** workspace you run on your own device (Termux).  
It’s built for **private coordination** and **structured workflows** — with clear screens, predictable controls, and an interface designed to keep you focused.

### What it includes (high level)
- **Auth & Access:** login/signup, device access approval, optional **2FA**, and recovery flows.
- **Chats (DM):** fast direct messages with attachments/media and practical moderation controls.
- **Groups:** group creation + member management (role-based actions like promote/demote/kick where permitted).
- **Calls:** call actions and related flows (join/leave, prompts, microphone permissions when supported).
- **Files / Vault:** upload, download, delete, folder management, and navigation.
- **Profile:** edit profile, picture management, and account actions (including a “danger zone” for irreversible actions).
- **Profiler / Reports / Bounty (where enabled):** structured record-keeping features and export options.
- **Admin:** approve/deny requests and manage users/files based on permissions.
- **Settings (Security):** password changes, session rules, privacy toggles, and security preferences.

### How to use
1. Open Termux and run **ButSystem.py** (via your DedSec setup).
2. Open the generated local link in your browser.
3. Use the **burger menu** to switch modules (Chats, Groups, Calls, Files, Profile, Settings, Admin).
4. Configure **Settings → Security** before inviting other people.

### Hypothetical scenarios (Batman-style, non-violent)
ButSystem is **not** for revenge or harm.  
The “Batman-style” mindset here means: **self-control, detective thinking, lawful evidence you already have, protecting people, and choosing responsible outcomes.**

### Fighting corruption (responsibly)
Use the system to **organize lawful documentation**, protect your accounts, and pursue **accountability through legal channels** (reporting, compliance, regulators, mediation, or professional advice as appropriate).

> **Reminder:** Use only on systems you own or where you have explicit permission. Misuse for unauthorized or harmful activity is prohibited.


## 💬 Contact Us & Credits

### Contact Us

For questions, support, or general inquiries, connect with the DedSec Project community through our official channels:

* **Main Website:** [https://ded-sec.space](https://ded-sec.space)
* **Main DedSec Project Repository:** [https://github.com/dedsec1121fk/DedSec](https://github.com/dedsec1121fk/DedSec)
* **In Case Something Happens To Our Main Links Visit The Backups:**
* **Backup Website:** [https://ded-sec.online](https://ded-sec.online)
* **Backup DedSec Project Repository:** [https://github.com/sal-scar/DedSec](https://github.com/sal-scar/DedSec)
* **📱 WhatsApp:** [+37257263676](https://wa.me/37257263676)
* **📸 Instagram:** [@dedsec_project_official](https://www.instagram.com/dedsec_project_official)
* **✈️ Telegram:** [@dedsecproject](https://t.me/dedsecproject)
* **💬 Discord Server:** [https://discord.gg/fcAuYS4JEv](https://discord.gg/fcAuYS4JEv)

### Credits

* **Creator:** dedsec1121fk
* **Contributors:** gr3ysec, Sal Scar
* **Art Artists:** Christina Chatzidimitriou
* **Testers:** Javier
* **Legal Documents:** Lampros Spyrou
* **Discord Server Maintenance:** Talha
* **Past Help:** lamprouil, UKI_hunter

---

## ⚠️ Disclaimer & Terms of Use

> **PLEASE READ CAREFULLY BEFORE PROCEEDING.**

This project, including all associated tools, scripts, and documentation ("the Software"), is provided strictly for **educational, research, and ethical security testing purposes**. It is intended for use exclusively in controlled, authorized environments by users who have obtained explicit, prior written permission from the owners of any systems they intend to test.

1.  **Assumption of Risk and Responsibility:** By accessing or using the Software, you acknowledge and agree that you are doing so at your own risk. You are **solely and entirely responsible for your actions** and for any consequences that may arise from the use or misuse of this Software. This includes, but is not limited to, compliance with all applicable local, state, national, and international laws and regulations related to cybersecurity, data privacy, and electronic communications.

2.  **Prohibited Activities:** Any use of the Software for unauthorized or malicious activities is **strictly prohibited**. This includes, without limitation: accessing systems or data without authorization; performing denial-of-service attacks; data theft; fraud; spreading malware; or any other activity that violates applicable laws. Engaging in such activities may result in severe civil and criminal penalties.

3.  **No Warranty:** The Software is provided **"AS IS,"** without any warranty of any kind, express or implied. The developers and contributors make **no guarantee** that the Software will be error-free, secure, or uninterrupted.

4.  **Limitation of Liability:** In no event shall the developers, contributors, or distributors of the Software be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the Software or the use or other dealings in the Software. This includes any direct, indirect, incidental, special, exemplary, or consequential damages (including, but not limited to, procurement of substitute goods or services; loss of use, data, or profits; or business interruption).
