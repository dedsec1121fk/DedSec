<div align="center">
  <img src="https://raw.githubusercontent.com/dedsec1121fk/dedsec1121fk.github.io/47ad8e5cbaaee04af552ae6b90edc49cd75b324b/Assets/Images/Logos/Black%20Purple%20Butterfly%20Logo.jpeg" alt="DedSec Project Logo" width="150"/>
  <h1>DedSec Project</h1>
  <p>
    <a href="https://ded-sec.space/"><strong>Official Website</strong></a>
  </p>
  <p>
    <a href="https://github.com/sponsors/dedsec1121fk"><img src="https://img.shields.io/badge/Sponsor-DedSec-purple?style=for-the-badge&logo=GitHub" alt="Sponsor Project"></a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/Purpose-Educational-blue.svg" alt="Purpose: Educational">
    <img src="https://img.shields.io/badge/Platform-Android%20(Termux)-brightgreen.svg" alt="Platform: Android (Termux)">
    <img src="https://img.shields.io/badge/Language-Python%20%7C%20JS%20%7C%20Shell-yellow.svg" alt="Language: Python | JS | Shell">
    <img src="https://img.shields.io/badge/Interface-EN%20%7C%20GR-lightgrey.svg" alt="Interface: EN | GR">
  </p>
</div>

---

<a id="english-readme"></a>

# DedSec Project

> **Για να μεταβείτε στην πλήρη Ελληνική έκδοση, συνεχίστε [Πατώντας Εδώ](#greek-readme).**


The **DedSec Project** is a broad educational toolkit built for **Android + Termux**, bringing together many scripts, utilities, local web interfaces, and practice environments in one place. Its purpose is to help users learn how tools work, understand defensive awareness, and organize common Termux workflows from a single project.

<a id="table-of-contents"></a>

<h2>Table of Contents</h2>

* How To Install And Setup The DedSec Project
* Website Help Paths
* Settings & Configuration
* Explore The Toolkit
* Developer Base
* Network Tools
* Personal Information Capture
* Fake Pages
* Games
* Other Tools
* No Category
* Sponsors-Only
* ButSystem.py (Exclusive)
* Contact Us & Credits
* Disclaimer & Terms of Use

<a id="how-to-install-and-setup-the-dedsec-project"></a>

<details>
<summary><strong>How To Install And Setup The DedSec Project</strong></summary>


This section follows the installation HTML and shows the full setup flow for the **DedSec Project** on **Android with Termux**. It covers first-time installation, the exact post-setup steps you should follow, how to update an existing copy, and how to open the project again later without reinstalling it.

### Requirements

| Component | Minimum Specification |
| :-------- | :-------------------- |
| **Device** | Android phone or tablet with Termux installed |
| **Storage** | Minimum **8GB** free space |
| **RAM** | Minimum **2GB** |
| **Internet** | Needed for first installation and updates |

### Before You Start

- Install **Termux from F-Droid** for the best compatibility.
- If you install APK files manually, allow installation from unknown apps in your Android settings.
- When Termux asks for storage permission, allow it if you want the project to access Downloads and saved files.
- For long installs, long-press inside Termux, tap **More**, and enable **Keep screen on**.
- You can also customize the terminal appearance by long-pressing inside Termux, tapping **More**, and selecting **Style**.

### Installation Options

#### Option 1: First-Time Full Install

Use this path if you are installing the DedSec Project for the first time.

##### 1. Install F-Droid, then install Termux and the recommended add-ons

- Download and install **F-Droid**.
- Open F-Droid.
- Search for **Termux** and install it.
- Recommended extras: **Termux:API** and **Termux:Styling**.

##### 2. Open Termux and prepare packages

Important: open the **Termux** app on your device before copying and pasting the command below.

Run:

```bash
pkg update -y && pkg upgrade -y && pkg install git nano -y && termux-setup-storage
```

What this does:

- updates package lists
- upgrades installed packages
- installs `git` and `nano`
- requests storage access inside Termux

##### 3. Clone the DedSec Project repository

Run:

```bash
git clone https://github.com/dedsec1121fk/DedSec
```

This downloads the full project into a folder named `DedSec`.

##### 4. Enter the project folder and run setup

Run:

```bash
cd DedSec && bash Setup.sh
```

The script will handle the complete installation.

##### 5. Complete the post-setup configuration

After setup finishes, do the following:

- change the **prompt**
- change the **menu style**
- for new users, **list** or **numbered** menu styles are the best choices
- choose your **language**
- run the **Save DedSec Project** option on your first run so you create a fresh project save backup
- **Save DedSec Project** may take a while depending on your internet connection, and the terminal may stay blank until it is ready
- run **Save DedSec Project** again a few times every year to keep your saved DedSec Project package fresh and ready to restore if needed
- fully close Termux from your phone's **notification panel** using the **exit button**
- open Termux again

##### 6. Quick launch tip after setup

After reopening Termux, you can quickly open the project menu by typing:

- `e` for **English**
- `g` for **Greek**

#### Option 2: Update an Existing Installation

Use this if the project is already installed and you only want the newest files.

First enter the project folder:

```bash
cd ~/DedSec
```

Then pull the newest changes:

```bash
git pull
```

If needed, run setup again:

```bash
bash Setup.sh
```

This is useful after major project changes, new dependencies, or menu updates.

#### Option 3: Open the Project Later Without Reinstalling

If the project is already installed and configured, you usually do **not** need to reinstall it every time.

You can:

- open Termux and use the quick-launch command if it is already configured
- type `e` for **English** or `g` for **Greek** to open the menu quickly
- or manually enter the folder again:

```bash
cd ~/DedSec
```

If you need to run setup again manually:

```bash
bash Setup.sh
```

### Important Notes

- Keep an internet connection enabled during the first install.
- The first installation can take longer than normal because packages and tools may need to download.
- On your first run, open **Settings.py** and use **Save DedSec Project** so your project backup package is created immediately.
- **Save DedSec Project** may take a while depending on your internet connection, and the terminal may stay blank until it is ready.
- Run **Save DedSec Project** a few times every year to refresh that backup package and help keep your DedSec Project ready to recover.
- If storage access was denied earlier, run `termux-setup-storage` again.
- If Git is missing, run `pkg install git -y`.
- If you are already inside the DedSec folder, you do not need to clone the repository again.
- Using the F-Droid version of Termux is strongly recommended because some Play Store versions are outdated.

</details>

<a id="website-help-paths"></a>

<details>
<summary><strong>Website Help Paths</strong></summary>


This follows the same starter/help path from the website `index.html`, but here the website buttons are written as normal linked text. Each link also shows the exact website path.

**The best path to start is:**

Start with the installation guide, then learn what each tool does before running anything.

- [Guide For Installation](https://ded-sec.space/Pages/guide-for-installation.html) — website path: `Pages/guide-for-installation.html`
- [Learn About The Tools](https://ded-sec.space/Pages/learn-about-the-tools.html) — website path: `Pages/learn-about-the-tools.html`
- [Assistance](https://ded-sec.space/Pages/assistance.html) — website path: `Pages/assistance.html`

Then download our free e-book:

- [Master Termux In 7 Days](https://ded-sec.space/Assets/Master%20Termux%20In%207%20Days%20English.pdf) — website path: `Assets/Master Termux In 7 Days English.pdf`

Check our exclusive ButSystem.py and become a real detective:

- [ButSystem.py (Exclusive)](https://ded-sec.space/Pages/butsystem-exclusive.html) — website path: `Pages/butsystem-exclusive.html`

If Termux or DedSec breaks, open Assistance first. If you need anything custom-made or direct help, check our Store.

- [Store](https://ded-sec.space/Pages/store.html) — website path: `Pages/store.html`
- [Assistance](https://ded-sec.space/Pages/assistance.html) — website path: `Pages/assistance.html`

Check the menu (the three lines at the top right) to find more stuff like assistance, frequently asked questions, our vision, contact ways, etc.

</details>

<a id="settings--configuration"></a>

<details>
<summary><strong>Settings & Configuration</strong></summary>


The DedSec Project includes **Settings.py**, the central control panel for keeping the toolkit configured, updated, backed up, connected, and easy to open after installation.

### Main Settings Menu Options

- **About:** shows the latest DedSec Project update date, Termux storage usage, DedSec Project size, hardware details, internal storage, processor, RAM, carrier, kernel version, Android version, device model, manufacturer, uptime, battery status, and current Termux user.
- **DedSec Project Update (Source 1):** updates the installed project from the main `dedsec1121fk/DedSec` repository by fetching the newest files and applying the latest version.
- **DedSec Project Update (Source 2):** updates the installed project from the backup `sal-scar/DedSec` repository, useful when the first source is unavailable or when you want the mirror source.
- **Update Packages & Modules:** refreshes Termux packages and Python modules used by the project, including developer, networking, web, media, cryptography, API, and utility dependencies.
- **Access Sponsors-Only Scripts:** checks whether GitHub is connected in Termux, asks the user to connect GitHub if needed, verifies sponsor access, and downloads or replaces the local Sponsors-Only folder when access is confirmed. The $3 tier includes the current sponsor scripts, including Login Stealer.py, while the $9 tier includes all $3 scripts plus Widget Maker.py, Kraken Trader.py, and Noob Hacker.py. If the account does not have access, it returns the user to the settings menu without downloading anything.
- **Save DedSec Project:** creates a DedSec Project backup in your phone Downloads folder.
- **Change Prompt:** changes the username shown in the Termux prompt, sanitizes unsafe characters, updates `bash.bashrc`, and removes the default MOTD when needed.
- **GitHub Account:** opens a GitHub submenu for connecting with GitHub CLI, disconnecting the account, showing GitHub stats, and syncing the Termux prompt with the connected GitHub username.
- **Termux Usage Stats:** scans the local Termux workspace and shows tracked time, files scanned, files created, files edited, files deleted, latest created files, latest edited files, latest deleted files, programming languages used, shell commands found, and most active folders.
- **VPN & Tor Utilities:** provides optional no-root network privacy controls. It can enable or disable Tor, enable or disable proxy-based VPN routing, choose a VPN country, renew VPN proxies, update VPN/Tor tools, show connection status, and refresh shell exports so new Termux shells can reuse the selected network settings.
- **Change Menu Style:** lets you switch between **List Style**, **Grid Style**, **Choose By Number**, and **DedSec OS**. The selected style is saved so the project opens the same way next time.
- **Menu Auto-Start:** enables or disables automatic DedSec menu startup when Termux opens, depending on whether you want Termux to boot straight into the project menu or stay as a normal shell.
- **Choose Language / Επιλέξτε Γλώσσα:** saves the preferred language in `~/Language.json` and hides or shows the Greek folder depending on whether English or Greek is selected.
- **Credits:** displays the project creator, contributors, artist, legal document credit, Discord server maintenance credit, and past help credits.
- **Uninstall DedSec Project:** restores backed-up Termux configuration when possible, removes project configuration files, cleans startup changes, and gives the final command needed to remove the project folder safely.
- **Exit:** closes Settings.py and returns you to Termux.

### GitHub Account Submenu

The GitHub section can install or use `gh`, start the official GitHub login flow, save the connected username, disconnect the saved account, and show combined repository stats such as repositories counted, total stars, forks, watchers, commits, and rank. When connected, the prompt can automatically use the GitHub username, and the same connected account is used by **Access Sponsors-Only Scripts** to check private repository access.

### Access Sponsors-Only Scripts

This option is for sponsors who have access to the tier-appropriate private sponsor repository. It first checks whether GitHub is connected. If GitHub is not connected, it asks whether to connect now and follows the same GitHub CLI login flow used by the GitHub stats system. After a successful connection, it checks repository access and downloads the Sponsors-Only scripts into Termux home storage. The $3 tier contains the existing sponsor scripts, including Login Stealer.py. The $9 tier contains every $3 script plus Widget Maker.py, Kraken Trader.py, and Noob Hacker.py. If an older local copy exists, it is replaced only after access is confirmed.

### Termux Usage Stats

The usage stats section builds a local activity snapshot of your Termux workspace. On later scans, it compares changes and reports what was created, edited, or deleted. It also detects programming language usage by file extension, checks shell history commands, lists recent file activity, and highlights active folders.

### VPN & Tor Utilities

The network utilities section gives you optional controls for Tor and proxy-based VPN routing without root. Tor can be enabled or disabled from the menu. VPN routing can be enabled or disabled separately, uses a selectable country or refreshed proxy pool, and saves the chosen network state so it can be applied again when Termux starts. The status screen shows whether Tor and VPN routing are enabled, what country is selected, and which proxy is currently active.

### DedSec OS Mode

**DedSec OS** is the browser-based local workspace mode inside Settings.py. It adds a phone-first interface with a file browser, safe text editor, terminal view, session manager, DedSec apps launcher, Linux package store actions, notifications, fullscreen and split view controls, sidebar controls, wallpaper support, display name settings, terminal color settings, project/menu settings, menu auto-start controls, language controls, prompt controls, password login, optional authenticator-style 2FA, and password recovery through three security questions. It also includes project action buttons for updating both sources, updating packages/modules, accessing Sponsors-Only scripts, and opening credits.

### First-Time Setup Focus

After installation, the most important settings are:

1. choose your preferred language
2. choose your menu style
3. customize the prompt if you want
4. run **Save DedSec Project** on your first run
5. connect GitHub only if you want GitHub stats, prompt syncing, or Sponsors-Only access
6. enable or disable menu auto-start depending on how you use Termux
7. use **Update Packages & Modules** when dependencies need refreshing
8. use **VPN & Tor Utilities** only when you want those optional network controls

### Save DedSec Project Reminder

Use **Save DedSec Project** on your first run, then run it again a few times every year so your saved DedSec Project package stays fresh and ready if you ever need to restore it. It may take a while depending on your internet connection, and the terminal may stay blank until it is ready.

</details>

<a id="explore-the-toolkit"></a>

<details>
<summary><strong>Explore The Toolkit</strong></summary>


> **CRITICAL NOTICE:** The following scripts are included for **educational and defensive purposes only**. Their role is to help users understand how tools, lures, and simulations work so they can improve awareness, testing discipline, and self-protection in controlled environments.

### Toolkit Summary

- **Developer Base:** 10 tools
- **Network Tools:** 10 tools
- **Other Tools:** 5 tools
- **Games:** 6 tools
- **Personal Information Capture:** 17 tools
- **Social Media / Fake Pages:** 25 tools
- **No Category:** 3 tools
- **Sponsors-Only:** 6 tools in the $3 tier / 9 tools in the $9 tier

**Total listed on tools page:** 85 tools

---
<a id="developer-base"></a>

<h2>Developer Base</h2>


<details>
<summary>File Converter</summary>


**Description:** A powerful file converter supporting 40+ formats. Organizes Downloads. Advanced interactive file converter for Termux using curses interface. Supports 40 different file formats across images, documents, audio, video, and archives. Features automatic dependency installation, organized folder structure, and comprehensive conversion capabilities. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Converted files are saved under /storage/emulated/0/Download/File Converter/, inside format folders such as JPG, PNG, PDF, MP3, MP4, ZIP, TXT, and others.`

</details>

<details>
<summary>File Type Checker</summary>


**Description:** Advanced file analysis and security scanner that detects file types, extracts metadata, calculates cryptographic hashes, and identifies potential threats. Features magic byte detection, entropy analysis, steganography detection, virus scanning via VirusTotal API, and automatic quarantine of suspicious files. Supports analysis of files up to 50GB. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Files are scanned in /sdcard/Download/File Type Checker/ on Termux, or ~/Downloads/File Type Checker/ outside Termux. Quarantined files stay in the same folder and are renamed with the .dangerous suffix.`

</details>

<details>
<summary>Mobile Desktop</summary>


**Description:** Termux Linux Desktop Manager (no root): sets up a proot-distro desktop environment with VNC/X11 options and a built-in program manager for install/update/remove. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Manager settings are stored in ~/.termux_linux_vnc_manager/config.json. Generated launchers are installed in $PREFIX/bin/ as vnc-<system>. The Linux distributions themselves are managed by proot-distro.`

</details>

<details>
<summary>Mobile Developer Setup</summary>


**Description:** Automates a mobile web-dev environment in Termux: installs common dev tools, configures paths, and provides quick-start project scaffolding. Built for Termux with clear prompts and organized outputs.

**Save Location:** `State and backup archives are stored in ~/.mobile-dev-setup/ (including backups/ and state.json). Helper scripts are stored in ~/.mobile-dev-setup-tools/, plugins in ~/.zsh-plugins/, and Termux appearance files in ~/.termux/.`

</details>

<details>
<summary>Simple Websites Creator</summary>


**Description:** A comprehensive website builder that creates responsive HTML websites with customizable layouts, colors, fonts, and SEO settings. Features include multiple hosting guides, real-time preview, mobile-friendly designs, and professional templates. Perfect for creating portfolios, business sites, or personal blogs directly from your terminal. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Created websites are saved in /storage/emulated/0/Download/Websites/.`

</details>

<details>
<summary>Smart Notes</summary>


**Description:** Terminal note-taking app with reminders. Advanced note-taking application with reminder functionality, featuring both TUI (Text User Interface) and CLI support. Includes sophisticated reminder system with due dates, automatic command execution, external editor integration, and comprehensive note organization capabilities. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Notes: ~/.smart_notes.json | Settings: ~/.smart_notes_config.json | Error log: ~/.smart_notes_error.log`

</details>

<details>
<summary>Dead Man's Switch</summary>


**Description:** Termux emergency/SOS helper built around the I Need Help mode. After first-time setup and clear user confirmations, it can make the dead-mans-switch GitHub repository public, generate a GitHub Pages emergency website, upload organized emergency files, capture available camera photos, microphone recordings, and location updates at adjustable intervals through Termux:API permissions, and send SMS alerts with the website/repository link to configured trusted contacts. It also includes create/update uploads, overwrite sync, visibility controls, legacy repository migration, previous-history backups, logs, and a kill/cleanup option.

**Save Location:** `Main local folder: ~/storage/downloads/Dead Man's Switch/ (normally the phone Download folder; fallback /storage/emulated/0/Download/Dead Man's Switch/). Settings: ~/.dead_switch_settings.json. Logs and previous repository backups are stored inside the main folder under Logs/ and History/.`

</details>

<details>
<summary>Tree Explorer</summary>


**Description:** File-system explorer for Termux: browse folders, search files, find duplicates by hash, and clean empty directories with safe prompts. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Tree Explorer does not create a default results folder. Exports are written only to the path you choose with --export FILE or through the interactive export prompt. Installing the command copies it to $PREFIX/bin/supertree by default.`

</details>

<details>
<summary>Devices Finder</summary>


**Description:** Local-network device discovery tool for Termux that works without root. Separates live-host discovery from service scanning to reduce false positives, classifies devices using ports, banners, hostnames, and vendor hints, includes interactive scan profiles and type filters, and can optionally enrich results with mDNS, UPnP, SNMP, and NetBIOS clues. Exports JSON, TXT, CSV, and HTML reports. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Reports are saved in ~/storage/downloads/Devices Finder/ as devices_scan_<timestamp>.json, .txt, .csv, and .html. Fallbacks are ~/downloads/Devices Finder/ and then ./Devices Finder Output/.`

</details>

<details>
<summary>Free Internet</summary>


**Description:** Local-first browser and secure vault for Termux. It combines multiple search engines, bookmarks, history, saved pages, ad/tracker cleanup, Lite mode, country-based proxy routing with smart/strict/direct modes, optional Tor support, encrypted vault entries powered by OpenSSL, and a built-in full-page website screenshot tool. Built for Termux with clear prompts and organized outputs.

**Save Location:** `On Termux, all data is stored in ~/Free Internet/; outside Termux it uses ~/.free_internet/. Browser data is in browser/, saved pages in browser/saved/, screenshots in tools/screenshots/, and the encrypted vault database in vault/vault.db.`

</details>


<a id="network-tools"></a>

<h2>Network Tools</h2>


<details>
<summary>Bug Hunter</summary>


**Description:** Bug Hunter (no-root) — an authorized web security recon & misconfiguration scanner. Audits security headers and cookie flags, fingerprints technologies, checks DNS (SPF/DMARC/CAA), analyzes TLS/certificate expiry, tests CORS and HTTP methods, finds exposed sensitive files, crawls the site, and analyzes JavaScript for endpoints and leaked secrets. Includes optional directory discovery and Wayback URL recon, plus de-duplicated reports (JSON/CSV/HTML/PDF). Use only on targets you own or have explicit permission to test.

**Save Location:** `The default output folder is ./bughunter_out/ in the directory where the script is run. Use --output PATH to choose another folder. Reports include report.json, report.csv, report.html, optional report.pdf, and optional live/checkpoint files.`

</details>

<details>
<summary>Dark</summary>


**Description:** A specialized Dark Web OSINT tool and crawler designed for Tor network analysis. It features automated Tor connectivity, an Ahmia search integration, and a recursive crawler for .onion sites. The tool utilizes a modular plugin system to extract specific data types (Emails, BTC/XMR addresses, PGP keys, Phones) and supports saving snapshots. It offers both a Curses TUI and CLI mode, with results exportable to JSON, CSV, and TXT. Use only on systems you own or have explicit permission to test.

**Save Location:** `Results are stored in /sdcard/Download/DarkNet/ with fallback to ~/DarkNet/. JSON, CSV, TXT, snapshots, and plugin output are written there; plugins are stored in its plugins/ subfolder.`

</details>

<details>
<summary>DedSec's Network</summary>


**Description:** An advanced, non-root network toolkit optimized for speed and stability. Features a recursive website downloader with ZIP support, multi-threaded port scanner, internet speed testing, subnet calculator, and extensive OSINT tools (WHOIS, DNS, Reverse IP, Subdomain Enum). Includes web auditing scanners for SQLi, XSS, CMS detection, and SSH brute-forcing. Maintains a local SQLite audit log. Use only on systems you own or have explicit permission to test.

**Save Location:** `Configuration, audit_results.db, and wordlists are stored in ~/DedSec's Network/ on Termux, or ./DedSec's Network/ elsewhere. Downloaded websites go to /storage/emulated/0/Download/Websites/<domain>/, with fallbacks to /sdcard/Download/Websites/, ~/DedSec's Network/Websites/, or ~/Downloads/Websites/ outside Termux.`

</details>

<details>
<summary>Digital Footprint Finder</summary>


**Description:** Conservative OSINT username checker built for best practical results with low false-positives. Scans a large site list via packs (core/extended) with optional Sherlock database, using multi-signal scoring (status/redirects, title/meta/canonical/text) and per-domain concurrency limits for stability. Detects anti-bot/JS challenges as POSSIBLE (never falsely FOUND), supports optional search-engine dorking, and can import/export custom site lists. Exports reports to TXT/JSON/CSV and optional HTML. Use only on systems you own or have explicit permission to test.

**Save Location:** `Reports are stored in ~/storage/downloads/Digital Footprint Finder/. If that path is unavailable, the script falls back to /sdcard/Download/Digital Footprint Finder/, then ~/Digital Footprint Finder/, then the current directory. Files use <username>_<timestamp>.txt, with optional .json, .csv, and .html exports.`

</details>

<details>
<summary>Connections.py</summary>


**Description:** Secure chat/file-sharing server. Video calls, file sharing (50GB limit). Unified application combining Butterfly Chat and DedSec's Database with single secret key authentication. Provides real-time messaging, file sharing, video calls, and integrated file management. Features 50GB file uploads, WebRTC video calls, cloudflare tunneling, and unified login system. Use only on systems you own or have explicit permission to test.

**Save Location:** `Shared files are stored in ~/Downloads/DedSec's Database/. If that folder cannot be created, the fallback is ./DedSec_Database_Files/ in the current directory. Tor runtime data is stored separately in ~/.foxchat_tor/.`

</details>

<details>
<summary>Link Shield</summary>


**Description:** Security-focused URL inspector: follows redirects, checks HTTPS/SSL, flags suspicious domains/patterns, and generates a risk report before you open a link. Use only on systems you own or have explicit permission to test.

**Save Location:** `No dedicated output folder is created. linkshield_config_en.json, user-named JSON/Markdown reports, and linkshield_batch_report.json/.csv are saved in the current working directory.`

</details>

<details>
<summary>Masker</summary>


**Description:** URL helper for creating clean, readable test links and checking redirect behavior in your own workflows. It is presented for organization, demos, and authorized awareness training only, never to disguise harmful links or trick people.

**Save Location:** `No files are saved. The generated masked URL is printed in the terminal.`

</details>

<details>
<summary>QR Code Generator</summary>


**Description:** Python-based QR code generator that creates QR codes for URLs and saves them in the Downloads/QR Codes folder. Features automatic dependency installation, user-friendly interface, and error handling for reliable operation. Use only on systems you own or have explicit permission to test.

**Save Location:** `Generated PNG images are saved in ~/storage/downloads/QR Codes/.`

</details>

<details>
<summary>Sod</summary>


**Description:** A comprehensive load testing tool for web applications, featuring multiple testing methods (HTTP, WebSocket, database simulation, file upload, mixed workload), real-time metrics, and auto-dependency installation. Advanced performance testing framework with realistic user behavior simulation, detailed analytics, and system resource monitoring. Use only on systems you own or have explicit permission to test.

**Save Location:** `The configuration file load_test_config.json is saved in the current working directory. Test results are displayed in the terminal and are not written to a report file.`

</details>

<details>
<summary>Store Scrapper</summary>


**Description:** Single-file Python store scraper for Termux that works without root. Tries multiple ways to discover categories and products across regular HTML pages and many JS-style stores by reading HTML, JSON-LD, embedded JSON, sitemaps, Shopify endpoints, WooCommerce APIs, generic product cards, breadcrumbs, OpenGraph/meta tags, and internal links. Saves while running, starts full product scraping the moment each product is found, shows live terminal status, uses Enter as the default for prompts, and organizes results into store/category/product folders with downloaded images. Use only on systems you own or have explicit permission to test.

**Save Location:** `Product data is saved under ~/storage/downloads/Store Scrapper/<Store>/<Category>/<Product>/. If Termux Downloads is unavailable, it uses ~/downloads/Store Scrapper/. Product folders can contain FOUND.txt, metadata.json, summary.txt, description.txt, images/, and images.json; discovery and run-state files are stored in the store output tree.`

</details>


<a id="personal-information-capture-educational-use-only"></a>

<h2>Personal Information Capture (Educational Use Only)</h2>


These scripts are training simulations intended to help users understand how deceptive personal-data collection pages may be presented, so they can better recognize and defend against them in controlled environments.

<details>
<summary>Fake Back Camera Page</summary>


**Description:** Fake Back Camera Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Back Camera. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Captured back-camera images and related text data are saved in ~/storage/downloads/Camera-Phish-Back/.`

</details>

<details>
<summary>Fake Back Camera Video Page</summary>


**Description:** Fake Back Camera Video Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Back Camera Video. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Recorded back-camera WEBM videos and related text data are saved in ~/storage/downloads/Back Camera Videos/.`

</details>

<details>
<summary>Fake Card Details Page</summary>


**Description:** Fake Card Details Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Card Details. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Submitted card-activation data is saved in ~/storage/downloads/CardActivations/.`

</details>

<details>
<summary>Fake Chrome Verification Page</summary>


**Description:** Fake Chrome Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Chrome Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Chrome verification output, including location JSON, face video, device scan, system information, and summaries, is saved in ~/storage/downloads/Chrome Verification/.`

</details>

<details>
<summary>Fake Data Grabber Page</summary>


**Description:** Fake Data Grabber Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Data Grabber. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Collected application information is saved under ~/storage/downloads/Peoples_Lives/, including application_info.txt.`

</details>

<details>
<summary>Fake Discord Verification Page</summary>


**Description:** Fake Discord Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Discord Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Discord verification output, including location JSON, face video, ID, phone, payment, and summary files, is saved in ~/storage/downloads/Discord Verification/.`

</details>

<details>
<summary>Fake Facebook Verification Page</summary>


**Description:** Fake Facebook Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Facebook Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Facebook verification output, including location JSON, face video, ID images, and summary files, is saved in ~/storage/downloads/Facebook Verification/.`

</details>

<details>
<summary>Fake Front Camera Page</summary>


**Description:** Fake Front Camera Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Front Camera. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Captured front-camera images and related text data are saved in ~/storage/downloads/Camera-Phish-Front/.`

</details>

<details>
<summary>Fake Front Camera Video Page</summary>


**Description:** Fake Front Camera Video Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Front Camera Video. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Recorded front-camera WEBM videos and related text data are saved in ~/storage/downloads/Front Camera Videos/.`

</details>

<details>
<summary>Fake Google Location Page</summary>


**Description:** Fake Google Location Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Google Location. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Location JSON files are saved in ~/storage/downloads/Locations/.`

</details>

<details>
<summary>Fake Instagram Verification Page</summary>


**Description:** Fake Instagram Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Instagram Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Instagram verification output, including location JSON, face video, voice audio, ID documents, and summary files, is saved in ~/storage/downloads/Instagram Verification/.`

</details>

<details>
<summary>Fake Location Page</summary>


**Description:** Fake Location Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Location. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Location JSON files are saved in ~/storage/downloads/Locations/.`

</details>

<details>
<summary>Fake Microphone Page</summary>


**Description:** Fake Microphone Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Microphone. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Recorded audio, converted WAV files, and related text data are saved in ~/storage/downloads/Recordings/.`

</details>

<details>
<summary>Fake OnlyFans Verification Page</summary>


**Description:** Fake OnlyFans Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around OnlyFans Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `OnlyFans verification output, including location JSON, face video, ID, payment, and summary files, is saved in ~/storage/downloads/OnlyFans Verification/.`

</details>

<details>
<summary>Fake Steam Verification Page</summary>


**Description:** Fake Steam Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Steam Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Steam verification output, including location JSON, face video, ID, Steam Guard, phone, payment, and summary files, is saved in ~/storage/downloads/Steam Verification/.`

</details>

<details>
<summary>Fake Twitch Verification Page</summary>


**Description:** Fake Twitch Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Twitch Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Twitch verification output, including location JSON, face video, ID, payment, and summary files, is saved in ~/storage/downloads/Twitch Verification/.`

</details>

<details>
<summary>Fake YouTube Verification Page</summary>


**Description:** Fake YouTube Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around YouTube Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `YouTube verification output, including location JSON, face video, ID, payment, and summary files, is saved in ~/storage/downloads/YouTube Verification/.`

</details>


<a id="fake-pages-educational-use-only"></a>

<h2>Fake Pages (Educational Use Only)</h2>


These scripts are educational simulations intended to help users recognize social-engineering patterns, fake reward pages, fake verification flows, and imitation brand pages often used to pressure people into unsafe actions.

<details>
<summary>Fake Apple iCloud Page</summary>


**Description:** Fake Apple iCloud Page is a mock phishing-awareness page for teaching how fake Apple iCloud offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Apple iCloud/.`

</details>

<details>
<summary>Fake Discord Nitro Page</summary>


**Description:** Fake Discord Nitro Page is a mock phishing-awareness page for teaching how fake Discord Nitro offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Discord Nitro/.`

</details>

<details>
<summary>Fake Epic Games Page</summary>


**Description:** Fake Epic Games Page is a mock phishing-awareness page for teaching how fake Epic Games offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Epic Games/.`

</details>

<details>
<summary>Fake Facebook Friends Page</summary>


**Description:** Fake Facebook Friends Page is a mock phishing-awareness page for teaching how fake Facebook Friends offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Facebook Friends/.`

</details>

<details>
<summary>Fake Free Robux Page</summary>


**Description:** Fake Free Robux Page is a mock phishing-awareness page for teaching how fake Free Robux offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Roblox Robux/.`

</details>

<details>
<summary>Fake GitHub Pro Page</summary>


**Description:** Fake GitHub Pro Page is a mock phishing-awareness page for teaching how fake GitHub Pro offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/GitHub Pro/.`

</details>

<details>
<summary>Fake Google Free Money Page</summary>


**Description:** Fake Google Free Money Page is a mock phishing-awareness page for teaching how fake Google Free Money offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Google Free Money/.`

</details>

<details>
<summary>Fake Instagram Followers Page</summary>


**Description:** Fake Instagram Followers Page is a mock phishing-awareness page for teaching how fake Instagram Followers offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Instagram Followers/.`

</details>

<details>
<summary>Fake MetaMask Page</summary>


**Description:** Fake MetaMask Page is a mock phishing-awareness page for teaching how fake MetaMask offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/MetaMask/.`

</details>

<details>
<summary>Fake Microsoft 365 Page</summary>


**Description:** Fake Microsoft 365 Page is a mock phishing-awareness page for teaching how fake Microsoft 365 offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Microsoft 365/.`

</details>

<details>
<summary>Fake OnlyFans Page</summary>


**Description:** Fake OnlyFans Page is a mock phishing-awareness page for teaching how fake OnlyFans offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/OnlyFans/.`

</details>

<details>
<summary>Fake PayPal Page</summary>


**Description:** Fake PayPal Page is a mock phishing-awareness page for teaching how fake PayPal offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form and card data is written to ~/storage/downloads/PayPal/.`

</details>

<details>
<summary>Fake Pinterest Pro Page</summary>


**Description:** Fake Pinterest Pro Page is a mock phishing-awareness page for teaching how fake Pinterest Pro offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Pinterest Pro/.`

</details>

<details>
<summary>Fake PlayStation Network Page</summary>


**Description:** Fake PlayStation Network Page is a mock phishing-awareness page for teaching how fake PlayStation Network offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/PlayStation Network/.`

</details>

<details>
<summary>Fake Reddit Karma Page</summary>


**Description:** Fake Reddit Karma Page is a mock phishing-awareness page for teaching how fake Reddit Karma offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Reddit Karma/.`

</details>

<details>
<summary>Fake Snapchat Friends Page</summary>


**Description:** Fake Snapchat Friends Page is a mock phishing-awareness page for teaching how fake Snapchat Friends offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Snapchat Friends/.`

</details>

<details>
<summary>Fake Steam Games Page</summary>


**Description:** Fake Steam Games Page is a mock phishing-awareness page for teaching how fake Steam Games offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Steam Games/.`

</details>

<details>
<summary>Fake Steam Wallet Page</summary>


**Description:** Fake Steam Wallet Page is a mock phishing-awareness page for teaching how fake Steam Wallet offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Steam Wallet/.`

</details>

<details>
<summary>Fake TikTok Followers Page</summary>


**Description:** Fake TikTok Followers Page is a mock phishing-awareness page for teaching how fake TikTok Followers offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/TikTok Followers/.`

</details>

<details>
<summary>Fake Trust Wallet Page</summary>


**Description:** Fake Trust Wallet Page is a mock phishing-awareness page for teaching how fake Trust Wallet offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Trust Wallet/.`

</details>

<details>
<summary>Fake Twitch Subs Page</summary>


**Description:** Fake Twitch Subs Page is a mock phishing-awareness page for teaching how fake Twitch Subs offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Twitch Subs/.`

</details>

<details>
<summary>Fake Twitter Followers Page</summary>


**Description:** Fake Twitter Followers Page is a mock phishing-awareness page for teaching how fake Twitter Followers offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Twitter Followers/.`

</details>

<details>
<summary>Fake What's Up Dude Page</summary>


**Description:** Fake What's Up Dude Page is a mock phishing-awareness page for teaching how fake What's Up Dude offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/WhatsUp Dude/.`

</details>

<details>
<summary>Fake Xbox Live Page</summary>


**Description:** Fake Xbox Live Page is a mock phishing-awareness page for teaching how fake Xbox Live offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Xbox Live/.`

</details>

<details>
<summary>Fake YouTube Subscribers Page</summary>


**Description:** Fake YouTube Subscribers Page is a mock phishing-awareness page for teaching how fake YouTube Subscribers offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/YouTube Subscribers/.`

</details>


<a id="games"></a>

<h2>Games</h2>


<details>
<summary>Buzz</summary>


**Description:** A text-only trivia party game for Termux with a fixed built-in database of 15,000 questions (no runtime generation). Supports 1–2 players (pass-and-play), multiple round types, difficulty filtering (All/Easy/Medium/Hard), profiles, settings, and highscores. Lightweight terminal game with quick controls and replay value.

**Save Location:** `All game data is stored in ~/Buzz/data/: questions_en.jsonl.gz, highscores.json, profiles.json, and settings.json.`

</details>

<details>
<summary>CTF God</summary>


**Description:** Full‑screen Curses CTF game for Termux with story mode, missions, daily challenges, random boss levels, hint shop economy, achievements & ranks, challenge pack import/export, tournament mode, and anti‑cheat/integrity checks. Includes a built‑in level editor. Lightweight terminal game with quick controls and replay value.

**Save Location:** `Challenge workspaces are stored in /storage/emulated/0/Download/CTF God/; fallback paths are ~/storage/downloads/CTF God/ and ~/CTF God/. Profiles, progress, packs, and custom challenges are stored in ~/.ctf_god/ (state.json, custom.json, packs/).`

</details>

<details>
<summary>Detective</summary>


**Description:** A story-driven Terminal detective game for Termux with an expanded fixed case library, richer lore dossiers, district rumors, side stories, and bonus story threads. Track evidence, interrogate suspects, review suspect rosters, build an ASCII case board and timeline, and manage progress with 3 save slots plus autosave. Includes 4 difficulties, note/evidence tracking, checkpoint hints, and quick commands like :help, :guide, :lore, :suspects, :board, :timeline, :hint, and :save.

**Save Location:** `All saves are stored in ~/Detective/: player.json, highscores.json, and savegame_slot1.json through savegame_slot3.json.`

</details>

<details>
<summary>Tamagotchi</summary>


**Description:** A fully featured terminal pet game. Feed, play, clean, and train your pet. Don't let it die. Advanced virtual pet simulation game with comprehensive pet management system. Features include pet evolution through life stages (Egg, Child, Teen, Adult, Elder), personality traits, skill development, mini-games, job system, and legacy retirement. Includes detailed statistics tracking. Lightweight terminal game with quick controls and replay value.

**Save Location:** `The Tamagotchi save is stored in ~/.termux_tamagotchi_v8.json.`

</details>

<details>
<summary>Pet Friends</summary>


**Description:** An idle virtual-companion game for Termux with 160+ real, legendary, and mythical pets. Care for, train, rename, evolve, and collect companions while completing missions, quests, achievements, daily contracts, expeditions, treasure maps, festivals, upgrades, prestige goals, and rarity-based crates. It includes educational animal facts, clearly labelled mythology, animated ASCII pets, locally generated sound effects and background music, and optional local-network battles and trades.

**Save Location:** `The main save is stored in ~/Pet Friends/petfriends_save.json. Generated sound effects, background music, and Pet Friends audio-session files are stored in ~/Pet Friends/sounds/ and ~/Pet Friends/.pet_friends_audio.json.`

</details>

<details>
<summary>Terminal Arcade</summary>


**Description:** All-in-one terminal arcade pack with multiple mini-games in a single script. Saves data in ~/Terminal Arcade/ and runs smoothly on Termux/Linux terminals. Lightweight terminal game with quick controls and replay value.

**Save Location:** `Arcade data is stored in ~/Terminal Arcade/. High scores and recent score history are saved in ~/Terminal Arcade/highscores.json.`

</details>


<a id="other-tools"></a>

<h2>Other Tools</h2>


<details>
<summary>Android App Launcher</summary>


**Description:** A utility to manage Android apps directly from the terminal. It can launch apps, extract APK files, uninstall apps, and analyze security permissions. Advanced Android application management and security analysis tool. Features include app launching, APK extraction, permission inspection, security analysis, and tracker detection. Includes comprehensive security reporting for installed applications. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Extracted APK files are saved in ~/storage/shared/Download/Extracted APK's/. Security reports are saved in ~/storage/shared/Download/App_Security_Reports/ as <app>_security_report.txt.`

</details>

<details>
<summary>Loading Screen</summary>


**Description:** Customize your Termux startup with ASCII art loading screens. Supports custom art, delay timers, and automated setup/cleanup for one-time display. Built for Termux with clear prompts and organized outputs.

**Save Location:** `No separate output folder is created. The selected loading screen is written directly into ~/.bash_profile.`

</details>

<details>
<summary>Password Master</summary>


**Description:** Comprehensive password management suite featuring encrypted vault storage, password generation, strength analysis, and improvement tools. Includes AES-256 encrypted vault with master password protection, random password generator, passphrase generator, password strength analyzer, and password improvement suggestions. Features clipboard integration. Built for Termux with clear prompts and organized outputs.

**Save Location:** `The encrypted vault is saved as ./my_vault.enc in the current working directory. Backups are saved in /storage/emulated/0/Download/Password Master Backup/vault_backup.enc, or ~/Downloads/Password Master Backup/ outside Android.`

</details>

<details>
<summary>Termux Backup Restore</summary>


**Description:** Backup & restore for Termux: creates a zipped backup of your Termux files to Downloads and can restore them with integrity checks. Built for Termux with clear prompts and organized outputs.

**Save Location:** `The backup archive is saved as /storage/emulated/0/Download/name_backup.zip. Split parts are created beside that archive. backup_config.json is stored in the current working directory.`

</details>

<details>
<summary>Termux Repair Wizard</summary>


**Description:** A no-root Termux diagnosis and repair suite for package, repository, storage, certificate, cache, Python/pip, permission, and shell/PATH problems. It can test mirrors and network access, repair broken packages, reset apt lists, handle release-information and hash-sum errors, clean caches, reinstall essential tools, and run a complete guided repair sequence. Its **Script Keeper** option safely scans individual scripts or entire folders without directly launching them, recognizes Python, shell, JavaScript/TypeScript, Ruby, Perl, PHP, Lua, Go, Rust, C/C++, Java, Kotlin, R, PowerShell, Dart, Scala, Groovy, Elixir, Erlang, Tcl, Haskell, C#, shebang scripts, and common project manifests, checks syntax and required tooling, installs missing packages or modules, processes dependency manifests, and tries compatible replacement packages for Python modules removed from newer Python releases.

**Save Location:** `System repairs are applied directly to Termux packages, storage permissions, $HOME permissions, and shell files such as ~/.bashrc, ~/.profile, and ~/.zshrc. Script Keeper reports are saved in ~/DedSec/logs/ as script_keeper_<timestamp>.log.`

</details>


<a id="no-category"></a>

<h2>No Category</h2>


<details>
<summary>Extra Content</summary>


**Description:** Extra bonus content hub: quick access to additional resources, templates, and optional add-ons included in the DedSec toolkit. Built for Termux with clear prompts and organized outputs.

**Save Location:** `The repository Extra Content folder is copied to ~/storage/downloads/Extra Content/.`

</details>

<details>
<summary>Settings.py</summary>


**Description:** Settings.py is the central control panel for the DedSec Project. It shows project and device information; updates the project from the main or backup source; refreshes Termux packages and Python modules; checks and downloads Sponsors-Only scripts through a connected GitHub account; creates a DedSec Project backup in Downloads; changes the Termux prompt; connects or disconnects GitHub; shows GitHub stats; syncs the prompt with the GitHub username; scans Termux usage stats; manages optional VPN and Tor utilities; switches between List, Grid, Choose By Number, and DedSec OS menu styles; controls menu auto-start; saves the English or Greek language choice; displays credits; and safely uninstalls the project. DedSec OS adds a browser-based local workspace with a file browser, safe text editor, terminal view, session manager, DedSec apps launcher, Linux package store actions, notifications, fullscreen and split-view controls, sidebar controls, wallpaper support, display name settings, terminal color settings, project action buttons, language controls, prompt controls, password login, optional authenticator-style 2FA, and recovery through three security questions. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Language: ~/Language.json | Termux configuration backup: ~/Termux.zip | Project archive: /storage/emulated/0/Download/DedSec Project Legacy Save.zip | GitHub account: ~/.dedsec_github_account.json | Usage stats: ~/.dedsec_termux_usage_stats.json | Network utility data: ~/.dedsec_network_utilities/ and ~/.dedsec_network_utilities.json`

</details>

<details>
<summary>DedSec Market</summary>


**Description:** Curses-based GitHub repository market for Termux that displays projects by project name instead of raw repository name. It fetches README text cleanly, shows releases and issues, supports install/update/delete and launch actions, keeps a watchlist, and stores cache/state for faster reuse. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Market state and cache are stored in ~/DedSec Market/ (state.json and cache/). Installed repositories are placed directly in ~/<repository-name>/, adding -1, -2, and so on if that folder already exists.`

</details>


<a id="sponsors-only"></a>

<h2>Sponsors-Only</h2>


Sponsors-Only access is now split into two GitHub Sponsors tiers:

| Tier | What it includes |
| :--- | :--------------- |
| **$3 Sponsor** | The existing sponsor scripts already listed on the website: Face Detector.py, Face Detector Heavy.py, Face Swap.py, Steganography.py, AR Terror.py, and **Login Stealer.py**. |
| **$9 Pro Supporter** | Everything from the $3 tier, plus **Widget Maker.py**, **Kraken Trader.py**, and **Noob Hacker.py**. |

**• $3 Sponsor Scripts**


<details>
<summary>Face Detector.py</summary>


**Description:** Local browser-based face analysis tool for Termux that works without root. It uses MediaPipe Face Mesh on the live camera feed, supports both front and back camera, tracks up to 3 faces, draws detailed facial landmark overlays instead of simple boxes, and also lets you upload photos or videos for analysis directly from the interface. It can capture PNG snapshots, record WEBM video, save cropped detected faces separately, and provide both a local network link and an optional Cloudflare public link.

**Save Location:** On Termux, captures, recordings, uploaded results, and saved face crops are stored in: ~/storage/downloads/Face Detector/. If Termux storage is unavailable, it falls back to ~/Face Detector/. On non-Termux systems it uses ~/Downloads/Face Detector/, with fallback to ~/Face Detector/. Internal web files, certificates, and helper binaries are stored in ~/.face_detector_studio/.

</details>

<details>
<summary>Face Detector Heavy.py</summary>


**Description:** Expanded heavy-analysis version of the face detector for Termux, built without root. Along with live camera use, front/back camera switching, photo and video uploads, PNG snapshots, WEBM recording, and saved face crops, it raises tracking up to 30 faces and adds TensorFlow COCO-SSD object detection on top of the MediaPipe face mesh pipeline. It shows richer on-screen telemetry such as face count, animal/object detection, pose and gaze estimates, facial proportions, mouth and brow state, asymmetry scoring, and other visual analysis details, while still supporting both a local network link and an optional Cloudflare public link.

**Save Location:** On Termux, captures, recordings, uploaded results, and saved face crops are stored in: ~/storage/downloads/Face Detector/. If Termux storage is unavailable, it falls back to ~/Face Detector/. On non-Termux systems it uses ~/Downloads/Face Detector/, with fallback to ~/Face Detector/. Internal web files, certificates, and helper binaries are stored in ~/.face_detector_studio/.

</details>

<details>
<summary>Face Swap.py</summary>


**Description:** Local browser-based face swap tool for Termux that works without root. It opens a local camera page, lets you upload a source face image, switch between the front and back camera, and blend the uploaded face over the live camera using MediaPipe Face Mesh. The current version focuses on a smooth face-lock approach: it locks the uploaded face once, follows the live face, moves key feature patches for expressions, includes smoothing, feathering, opacity, blend, and skin-tone matching controls, and can save PNG snapshots from the browser. Use it only with your own images or with clear permission.

**Save Location:** On Termux, saved photos are stored in: /storage/emulated/0/Download/Face Swap/ or ~/storage/downloads/Face Swap/, with fallback to ~/Face Swap/. On non-Termux systems it uses ~/Downloads/Face Swap/, with fallback to ~/Face Swap/.

</details>

<details>
<summary>Steganography.py</summary>


**Description:** Password-based steganography suite for Termux. It can generate random black-and-white PNG carrier images, encrypt secret text with a password-derived Fernet key, hide the encrypted text inside PNG images using LSB steganography, and batch-decode hidden messages from all images placed in the Decrypt folder. Extracted messages are automatically saved as separate .txt files, and the script can also optionally clean processed images from the decode folder after scanning.

**Save Location:** Main folder: /storage/emulated/0/Download/Steganography/ | Carrier/output images: /Encrypt | Images to scan for hidden messages: /Decrypt | Extracted text files: /Decrypted Texts

</details>

<details>
<summary>AR Terror.py</summary>


**Description:** Local browser-based AR horror experience for Termux that works without root. It launches a full-screen camera-driven web page where you explore the environment, collect hidden logs into an archive/inventory system, use atmospheric visual and audio effects, switch between front and back camera, and record evidence as WEBM while the experience runs. It can also expose both a local network link and an optional Cloudflare public link.

**Save Location:** On Termux, recorded evidence is saved in: ~/storage/downloads/AR Terror/. If Termux storage is unavailable, it falls back to ~/AR Terror/. On non-Termux systems it uses ~/Downloads/AR Terror/, with fallback to ~/AR Terror/. Internal web files, certificates, and helper binaries are stored in ~/.ar_terror_studio/.

</details>

<details>
<summary>Login Stealer.py</summary>


**Description:** Login Stealer.py is a fully working controlled login-security simulation tool for Termux that helps demonstrate how fake login pages, copied authentication screens, redirects, session behavior, and verification-style traps can make users trust the wrong page. It is built for awareness training, lab demonstrations, screenshots, and dummy-account testing so beginners can understand how phishing-style login tricks look before they fall for them in real life. Use it only with dummy data, test accounts, or clear permission-based demonstrations. It is not presented as a tool for stealing real accounts, private credentials, cookies, cards, wallets, or personal information.

**Save Location:** Training output should stay inside your own local lab folder: `/storage/emulated/0/Download/Login Stealer/`. Use dummy data only, test accounts only, or clear permission-based demonstrations.

</details>

<details>
<summary>Widget Maker.py</summary>


**Description:** DedSec Widget Maker is a no-root Termux helper that creates Android home-screen launchers for DedSec Project scripts through Termux:Widget. It recursively scans Termux home, shared storage, and common phone folders for DedSec, sponsor, exclusive, and related Python scripts, including scripts inside every accessible folder and subfolder. It then creates managed shortcuts in ~/.shortcuts. Each widget opens a small menu with Run, Show Script Path, and Exit, validates the Python file before launching it, keeps a manifest in ~/.dedsec_widget_maker/, and can update or delete all managed widgets when your script collection changes.

**Save Location:** Managed widget launchers are created in: ~/.shortcuts/ | State and manifest are stored in: ~/.dedsec_widget_maker/manifest.json. The original scripts are not moved; each widget points back to the detected source file.

</details>

<details>
<summary>Kraken Trader.py</summary>


**Description:** Kraken Trader.py is a Termux trading research and portfolio assistant for the Kraken API. It starts in paper mode by default, shows a 10-second risk disclaimer, stores everything under ~/Kraken Trader/, and uses numbered menus for pair analysis, market scanning, dashboards, Sage-style strategy labs, advanced tools, beginner guides, risk/reward calculators, backtests, DCA and grid tools, paper wallet trading, paper bot loops, Kraken account tools, live order menus, order management, watchlists, crypto plus stock/ETF monitoring, reports, journals, logs, mode switching, diagnostics, and settings. It is built for education, organization, and safer paper testing; it is not financial advice and it does not guarantee profit.

**Save Location:** Main folder: ~/Kraken Trader/ | Config, paper wallet, watchlists, presets, alerts, baskets, DCA/grid assists, webhook logs, forward tests, reports, cache, journals, trade logs, and error logs are stored inside it. Optional report copies can be saved to Downloads if enabled.

</details>

<details>
<summary>Noob Hacker.py</summary>


**Description:** Noob Hacker.py is a safe offline terminal learning game for Termux that teaches absolute beginners programming, Python basics, Termux/Bash habits, debugging, local-only cybersecurity thinking, defender workflows, report writing, projects, quizzes, and playable practice games. It is built as a single Python script, works without root, keeps practice inside fictional/local labs, includes English and Greek versions, supports self-tests, save migration, progress tracking, and many beginner-friendly lessons designed to guide someone from zero knowledge into practical safe skills. It does not attack real targets, scan the internet, steal accounts, or teach malware.

**Save Location:** Main folder: ~/Noob Hacker/ | Save file: ~/Noob Hacker/save.json | Mission log: ~/Noob Hacker/mission_log.txt | CTF labs: ~/Noob Hacker/CTF_Labs/ | Exports: ~/Noob Hacker/Exports/

</details>


<a id="butsystempy-exclusive"></a>

<h2>ButSystem.py (Exclusive)</h2>


**ButSystem.py** is a self-hosted, **local-first** private workspace that runs on your own device through Termux and opens in a browser. It brings account access, communication, files, profiles, investigation-style records, and administration into one interface instead of splitting them across separate scripts.

It includes creator/admin setup, signup approval, approved-device requests, remembered-device login, optional security-question 2FA and password recovery, direct messages, group chats, the discussion room, stories, browser audio/video calls where supported, opt-in live locations, profiles, news, reports, appearance and security settings, and a private file vault with folder management, previews, downloads, deletion, and chunked uploads for larger files.

The **Profiler** supports locally stored encrypted text records, attachments, search, import and export, combining selected records, and bounty controls where enabled. ButSystem also provides chat PIN locks, unread, delivery and read state, online presence, user and device management, privacy pause, security logs, the built-in Face Detector, and local-network, Cloudflare, or Tor access options. Binary attachments remain local in the ButSystem data folders, while sensitive text fields use the built-in encryption layer.

**Save Location:** `Main persistent data: /storage/emulated/0/Homework/ButSystem/ (also available as ~/storage/shared/Homework/ButSystem/) | Fallback: ~/Homework/ButSystem/ | Legacy data migrated from: ~/ButSystem/ | Face Detector captures: Downloads/ButSystem/Face Detector/ | Tor runtime data: ~/.ButSystem_tor/`

Use only on systems you own or where you have explicit permission.


</details>

<a id="contact-us--credits"></a>

<details>
<summary><strong>Contact Us & Credits</strong></summary>


### Contact Us

For questions, support, or general inquiries, connect with the DedSec Project community through the official channels below:

* **Main Website:** [https://ded-sec.space](https://ded-sec.space)
* **Main DedSec Project Repository:** [https://github.com/dedsec1121fk/DedSec](https://github.com/dedsec1121fk/DedSec)
* **Backup Website:** [https://ded-sec.online](https://ded-sec.online)
* **Backup DedSec Project Repository:** [https://github.com/sal-scar/DedSec](https://github.com/sal-scar/DedSec)
* **WhatsApp:** [+37257263676](https://wa.me/37257263676)
* **Telegram:** [@dedsecproject](https://t.me/dedsecproject)
* **Discord Server:** [https://discord.gg/fcAuYS4JEv](https://discord.gg/fcAuYS4JEv)

### Credits

* **Creator:** dedsec1121fk
* **Contributors:** gr3ysec
* **Art Artists:** Christina Chatzidimitriou, 3A
* **Legal Documents:** Lampros Spyrou
* **Discord Server Maintenance:** Talha
* **Past Help:** Sal Scar, lamprouil, UKI_hunter

</details>

<a id="disclaimer--terms-of-use"></a>

<details>
<summary><strong>Disclaimer & Terms of Use</strong></summary>


> **PLEASE READ CAREFULLY BEFORE PROCEEDING.**

This project, including all associated tools, scripts, and documentation, is provided strictly for **educational, research, and ethical security testing purposes**. It is intended for use only in controlled, authorized environments by users who have obtained explicit permission from the owners of any systems they test.

1. **Assumption of Risk and Responsibility:** You are solely responsible for your actions and for any consequences that may arise from using or misusing this software.
2. **Prohibited Activities:** Unauthorized or malicious activity is strictly prohibited.
3. **No Warranty:** The software is provided **AS IS** without guarantees.
4. **Limitation of Liability:** The developers, contributors, and distributors are not liable for claims, damages, or losses arising from the software or its use.

</details>

<a id="greek-readme"></a>

# DedSec Project — Ελληνικά

> **Για να επιστρέψετε στην πλήρη Αγγλική έκδοση, συνεχίστε [Πατώντας Εδώ](#english-readme).**

Το **DedSec Project** είναι ένα ευρύ εκπαιδευτικό toolkit για **Android + Termux**, που συγκεντρώνει πολλά scripts, utilities, local web interfaces και περιβάλλοντα εξάσκησης σε ένα σημείο. Ο σκοπός του είναι να βοηθά τους χρήστες να μαθαίνουν πώς λειτουργούν τα εργαλεία, να κατανοούν καλύτερα την αμυντική επίγνωση και να οργανώνουν συνηθισμένα Termux workflows μέσα από ένα ενιαίο project.

<a id="greek-table-of-contents"></a>

<h2>Περιεχόμενα</h2>

* Πώς να Εγκαταστήσετε και να Ρυθμίσετε το DedSec Project
* Διαδρομές Βοήθειας Ιστοσελίδας
* Ρυθμίσεις και Παραμετροποίηση
* Εξερευνήστε την Εργαλειοθήκη
* Βάση Προγραμματιστή
* Εργαλεία Δικτύου
* Συλλογή Προσωπικών Πληροφοριών
* Ψεύτικες Σελίδες
* Παιχνίδια
* Άλλα Εργαλεία
* Χωρίς Κατηγορία
* Μόνο για Χορηγούς
* ButSystem.py (Αποκλειστικό)
* Επικοινωνία και Συντελεστές
* Αποποίηση Ευθύνης και Όροι Χρήσης

<a id="greek-installation"></a>

<details>
<summary><strong>Πώς να Εγκαταστήσετε και να Ρυθμίσετε το DedSec Project</strong></summary>


Αυτή η ενότητα ακολουθεί το installation HTML και δείχνει ολόκληρη τη ροή εγκατάστασης του **DedSec Project** σε **Android με Termux**. Περιλαμβάνει την πρώτη εγκατάσταση, τα ακριβή βήματα που πρέπει να ακολουθήσεις μετά το setup, τον τρόπο ενημέρωσης μιας υπάρχουσας εγκατάστασης και το πώς να ανοίγεις ξανά το project αργότερα χωρίς νέα εγκατάσταση.

### Απαιτήσεις

| Στοιχείο | Ελάχιστη Προδιαγραφή |
| :-------- | :------------------- |
| **Συσκευή** | Κινητό ή tablet Android με εγκατεστημένο Termux |
| **Αποθηκευτικός χώρος** | Ελάχιστο **8GB** ελεύθερος χώρος |
| **RAM** | Ελάχιστο **2GB** |
| **Internet** | Απαιτείται για την πρώτη εγκατάσταση και τις ενημερώσεις |

### Πριν Ξεκινήσεις

- Εγκατάστησε το **Termux από το F-Droid** για την καλύτερη συμβατότητα.
- Αν εγκαθιστάς APK αρχεία χειροκίνητα, επίτρεψε την εγκατάσταση από άγνωστες εφαρμογές στις ρυθμίσεις του Android.
- Όταν το Termux ζητήσει άδεια αποθήκευσης, δώσ' την αν θέλεις το project να έχει πρόσβαση στα Downloads και στα αποθηκευμένα αρχεία σου.
- Για μεγάλες εγκαταστάσεις, κράτησε πατημένο μέσα στο Termux, πάτησε **More** και ενεργοποίησε το **Keep screen on**.
- Μπορείς επίσης να παραμετροποιήσεις την εμφάνιση του terminal κρατώντας πατημένο μέσα στο Termux, πατώντας **More** και επιλέγοντας **Style**.

### Επιλογές Εγκατάστασης

#### Επιλογή 1: Πλήρης Πρώτη Εγκατάσταση

Χρησιμοποίησε αυτή τη διαδρομή αν εγκαθιστάς το DedSec Project για πρώτη φορά.

##### 1. Εγκατέστησε το F-Droid, μετά το Termux και τα προτεινόμενα πρόσθετα

- Κατέβασε και εγκατέστησε το **F-Droid**.
- Άνοιξε το F-Droid.
- Αναζήτησε το **Termux** και εγκατέστησέ το.
- Προτεινόμενα πρόσθετα: **Termux:API** και **Termux:Styling**.

##### 2. Άνοιξε το Termux και ετοίμασε τα πακέτα

Σημαντικό: άνοιξε πρώτα την εφαρμογή **Termux** στη συσκευή σου πριν αντιγράψεις και επικολλήσεις την παρακάτω εντολή.

Τρέξε:

```bash
pkg update -y && pkg upgrade -y && pkg install git nano -y && termux-setup-storage
```

Τι κάνει αυτό:

- ενημερώνει τις λίστες πακέτων
- αναβαθμίζει τα ήδη εγκατεστημένα πακέτα
- εγκαθιστά τα `git` και `nano`
- ζητά πρόσβαση αποθήκευσης μέσα στο Termux

##### 3. Κάνε clone το repository του DedSec Project

Τρέξε:

```bash
git clone https://github.com/dedsec1121fk/DedSec
```

Αυτό κατεβάζει ολόκληρο το project μέσα σε έναν φάκελο με όνομα `DedSec`.

##### 4. Μπες στον φάκελο του project και τρέξε το setup

Τρέξε:

```bash
cd DedSec && bash Setup.sh
```

Το script θα αναλάβει την πλήρη εγκατάσταση.

##### 5. Ολοκλήρωσε τη ρύθμιση μετά το setup

Αφού ολοκληρωθεί το setup, κάνε τα εξής:

- άλλαξε το **prompt**
- άλλαξε το **στυλ του μενού**
- για νέους χρήστες, τα **list** ή **numbered** menu styles είναι οι καλύτερες επιλογές
- διάλεξε τη **γλώσσα** σου
- τρέξε την επιλογή **Save DedSec Project** στο πρώτο σου άνοιγμα ώστε να δημιουργήσεις ένα φρέσκο project save backup
- το **Save DedSec Project** μπορεί να πάρει λίγη ώρα ανάλογα με τη σύνδεσή σου στο internet και το terminal μπορεί να μένει κενό μέχρι να ολοκληρωθεί
- τρέχε ξανά το **Save DedSec Project** λίγες φορές κάθε χρόνο ώστε να διατηρείς το αποθηκευμένο πακέτο του DedSec Project ενημερωμένο και έτοιμο για επαναφορά αν χρειαστεί
- κλείσε τελείως το Termux από το **πάνελ ειδοποιήσεων** του κινητού σου χρησιμοποιώντας το **κουμπί εξόδου**
- άνοιξε ξανά το Termux

##### 6. Συμβουλή γρήγορου ανοίγματος μετά το setup

Αφού ανοίξεις ξανά το Termux, μπορείς να ανοίξεις γρήγορα το μενού του project γράφοντας:

- `e` για **English**
- `g` για **Greek**

#### Επιλογή 2: Ενημέρωση Υπάρχουσας Εγκατάστασης

Χρησιμοποίησε αυτή την επιλογή αν το project είναι ήδη εγκατεστημένο και θέλεις μόνο τα πιο πρόσφατα αρχεία.

Πρώτα μπες στον φάκελο του project:

```bash
cd ~/DedSec
```

Μετά φέρε τις πιο νέες αλλαγές:

```bash
git pull
```

Αν χρειάζεται, τρέξε ξανά το setup:

```bash
bash Setup.sh
```

Αυτό είναι χρήσιμο μετά από μεγάλες αλλαγές στο project, νέες εξαρτήσεις ή ενημερώσεις στο μενού.

#### Επιλογή 3: Άνοιγμα του Project Αργότερα Χωρίς Νέα Εγκατάσταση

Αν το project είναι ήδη εγκατεστημένο και ρυθμισμένο, συνήθως **δεν** χρειάζεται να το ξαναεγκαθιστάς κάθε φορά.

Μπορείς:

- να ανοίξεις το Termux και να χρησιμοποιήσεις την εντολή γρήγορου ανοίγματος αν είναι ήδη ρυθμισμένη
- να γράψεις `e` για **English** ή `g` για **Greek** ώστε να ανοίξει γρήγορα το μενού
- ή να μπεις ξανά χειροκίνητα στον φάκελο:

```bash
cd ~/DedSec
```

Αν χρειάζεται να τρέξεις ξανά το setup χειροκίνητα:

```bash
bash Setup.sh
```

### Σημαντικές Σημειώσεις

- Κράτα ενεργή τη σύνδεση στο internet κατά την πρώτη εγκατάσταση.
- Η πρώτη εγκατάσταση μπορεί να πάρει περισσότερο χρόνο από το συνηθισμένο, επειδή ίσως χρειαστεί να κατέβουν πακέτα και εργαλεία.
- Στο πρώτο σου άνοιγμα, μπες στο **Settings.py** και χρησιμοποίησε το **Save DedSec Project** ώστε να δημιουργηθεί αμέσως το πακέτο backup του project σου.
- Το **Save DedSec Project** μπορεί να πάρει λίγη ώρα ανάλογα με τη σύνδεσή σου στο internet και το terminal μπορεί να μένει κενό μέχρι να ολοκληρωθεί.
- Τρέχε το **Save DedSec Project** λίγες φορές κάθε χρόνο για να ανανεώνεις αυτό το backup package και να βοηθάς το DedSec Project να παραμένει έτοιμο για επαναφορά.
- Αν η πρόσβαση αποθήκευσης είχε απορριφθεί νωρίτερα, τρέξε ξανά `termux-setup-storage`.
- Αν λείπει το Git, τρέξε `pkg install git -y`.
- Αν βρίσκεσαι ήδη μέσα στον φάκελο DedSec, δεν χρειάζεται να ξανακάνεις clone το repository.
- Προτείνεται έντονα η έκδοση του Termux από το F-Droid, επειδή κάποιες εκδόσεις του Play Store είναι παλιές.

</details>

<a id="greek-website-help"></a>

<details>
<summary><strong>Διαδρομές Βοήθειας Ιστοσελίδας</strong></summary>


Αυτή η ενότητα ακολουθεί το ίδιο starter/help path από το website `index.html`, αλλά εδώ τα website buttons είναι γραμμένα ως απλό linked text. Κάθε link δείχνει επίσης το ακριβές website path.

**Ο καλύτερος τρόπος για να ξεκινήσεις είναι:**

Ξεκίνα με τον οδηγό εγκατάστασης και μετά μάθε τι κάνει κάθε εργαλείο πριν τρέξεις οτιδήποτε.

- [Οδηγός Εγκατάστασης](https://ded-sec.space/Pages/guide-for-installation.html) — website path: `Pages/guide-for-installation.html`
- [Μάθετε για τα Εργαλεία](https://ded-sec.space/Pages/learn-about-the-tools.html) — website path: `Pages/learn-about-the-tools.html`
- [Βοήθεια](https://ded-sec.space/Pages/assistance.html) — website path: `Pages/assistance.html`

Μετά κατέβασε το δωρεάν e-book μας:

- [Master Termux In 7 Days](https://ded-sec.space/Assets/Master%20Termux%20In%207%20Days%20Greek.pdf) — website path: `Assets/Master Termux In 7 Days Greek.pdf`

Δες το αποκλειστικό ButSystem.py και γίνε πραγματικός detective:

- [ButSystem.py (Αποκλειστικό)](https://ded-sec.space/Pages/butsystem-exclusive.html) — website path: `Pages/butsystem-exclusive.html`

Αν χαλάσει το Termux ή το DedSec, άνοιξε πρώτα τη Βοήθεια. Αν χρειάζεσαι κάτι custom-made ή άμεση βοήθεια, δες το Store μας.

- [Κατάστημα](https://ded-sec.space/Pages/store.html) — website path: `Pages/store.html`
- [Βοήθεια](https://ded-sec.space/Pages/assistance.html) — website path: `Pages/assistance.html`

Δες το μενού (τις τρεις γραμμές πάνω δεξιά) για να βρεις περισσότερα όπως βοήθεια, συχνές ερωτήσεις, το όραμά μας, τρόπους επικοινωνίας, κτλ.

</details>

<a id="greek-settings"></a>

<details>
<summary><strong>Ρυθμίσεις και Παραμετροποίηση</strong></summary>


Το DedSec Project περιλαμβάνει το **Settings.py**, το κεντρικό control panel για να κρατάς το toolkit ρυθμισμένο, ενημερωμένο, αποθηκευμένο, συνδεδεμένο και εύκολο να ανοίξει ξανά μετά την εγκατάσταση.

### Κύριες Επιλογές του Settings Menu

- **About:** εμφανίζει την τελευταία ενημέρωση του DedSec Project, τον χώρο που χρησιμοποιεί το Termux, το μέγεθος του DedSec Project, στοιχεία hardware, internal storage, processor, RAM, carrier, kernel version, Android version, device model, manufacturer, uptime, battery status και τον τρέχοντα Termux user.
- **DedSec Project Update (Source 1):** ενημερώνει την εγκατεστημένη έκδοση από το κύριο repository `dedsec1121fk/DedSec`, φέρνοντας τα νεότερα αρχεία και εφαρμόζοντας την τελευταία έκδοση.
- **DedSec Project Update (Source 2):** ενημερώνει την εγκατεστημένη έκδοση από το backup repository `sal-scar/DedSec`, χρήσιμο όταν η πρώτη πηγή δεν είναι διαθέσιμη ή όταν θέλεις τη mirror source.
- **Update Packages & Modules:** ανανεώνει Termux packages και Python modules που χρησιμοποιεί το project, συμπεριλαμβανομένων developer, networking, web, media, cryptography, API και utility dependencies.
- **Access Sponsors-Only Scripts:** ελέγχει αν το GitHub είναι συνδεδεμένο στο Termux, ζητά σύνδεση GitHub αν χρειάζεται, ελέγχει sponsor access και κατεβάζει ή αντικαθιστά τον τοπικό Sponsors-Only φάκελο όταν επιβεβαιωθεί η πρόσβαση. Το tier των $3 περιλαμβάνει τα υπάρχοντα sponsor scripts, μαζί με το Login Stealer.py, ενώ το tier των $9 περιλαμβάνει όλα τα scripts των $3 μαζί με τα Widget Maker.py, Kraken Trader.py και Noob Hacker.py. Αν ο λογαριασμός δεν έχει πρόσβαση, επιστρέφει στο settings menu χωρίς να κατεβάσει τίποτα.
- **Save DedSec Project:** δημιουργεί backup του DedSec Project στα Downloads του κινητού.
- **Change Prompt:** αλλάζει το username που εμφανίζεται στο Termux prompt, καθαρίζει μη ασφαλείς χαρακτήρες, ενημερώνει το `bash.bashrc` και αφαιρεί το default MOTD όταν χρειάζεται.
- **GitHub Account:** ανοίγει GitHub submenu για σύνδεση με GitHub CLI, αποσύνδεση account, προβολή GitHub stats και συγχρονισμό του Termux prompt με το connected GitHub username.
- **Termux Usage Stats:** σαρώνει το local Termux workspace και εμφανίζει tracked time, files scanned, files created, files edited, files deleted, latest created files, latest edited files, latest deleted files, programming languages used, shell commands found και most active folders.
- **VPN & Tor Utilities:** παρέχει προαιρετικά no-root network privacy controls. Μπορεί να ενεργοποιήσει ή να απενεργοποιήσει Tor, να ενεργοποιήσει ή να απενεργοποιήσει proxy-based VPN routing, να επιλέξει χώρα VPN, να ανανεώσει VPN proxies, να ενημερώσει VPN/Tor tools, να δείξει connection status και να ανανεώσει shell exports ώστε νέα Termux shells να μπορούν να χρησιμοποιήσουν τις επιλεγμένες network ρυθμίσεις.
- **Change Menu Style:** επιτρέπει αλλαγή ανάμεσα σε **List Style**, **Grid Style**, **Choose By Number** και **DedSec OS**. Το επιλεγμένο style αποθηκεύεται ώστε το project να ανοίγει με τον ίδιο τρόπο την επόμενη φορά.
- **Menu Auto-Start:** ενεργοποιεί ή απενεργοποιεί την αυτόματη εκκίνηση του DedSec menu όταν ανοίγει το Termux, ανάλογα με το αν θέλεις το Termux να μπαίνει κατευθείαν στο project menu ή να μένει σαν κανονικό shell.
- **Choose Language / Επιλέξτε Γλώσσα:** αποθηκεύει την προτιμώμενη γλώσσα στο `~/Language.json` και κρύβει ή εμφανίζει τον ελληνικό φάκελο ανάλογα με το αν επιλεγεί English ή Greek.
- **Credits:** εμφανίζει creator, contributors, artist, legal document credit, Discord server maintenance credit και past help credits.
- **Uninstall DedSec Project:** επαναφέρει backed-up Termux configuration όπου γίνεται, αφαιρεί project configuration files, καθαρίζει startup αλλαγές και δίνει την τελική εντολή για ασφαλή αφαίρεση του project folder.
- **Exit:** κλείνει το Settings.py και σε επιστρέφει στο Termux.

### GitHub Account Submenu

Η ενότητα GitHub μπορεί να εγκαταστήσει ή να χρησιμοποιήσει το `gh`, να ξεκινήσει το official GitHub login flow, να αποθηκεύσει το connected username, να αποσυνδέσει το saved account και να εμφανίσει combined repository stats όπως repositories counted, total stars, forks, watchers, commits και rank. Όταν υπάρχει σύνδεση, το prompt μπορεί να χρησιμοποιεί αυτόματα το GitHub username και ο ίδιος συνδεδεμένος λογαριασμός χρησιμοποιείται από το **Access Sponsors-Only Scripts** για έλεγχο πρόσβασης στο private repository.

### Access Sponsors-Only Scripts

Αυτή η επιλογή είναι για sponsors που έχουν πρόσβαση στο αντίστοιχο private sponsor repository του tier τους. Πρώτα ελέγχει αν το GitHub είναι συνδεδεμένο. Αν δεν είναι, ρωτά αν θέλεις να συνδεθείς τώρα και χρησιμοποιεί την ίδια ροή GitHub CLI login με τα GitHub stats. Μετά από επιτυχημένη σύνδεση, ελέγχει πρόσβαση στο repository και κατεβάζει τα Sponsors-Only scripts στο home storage του Termux. Το tier των $3 περιλαμβάνει τα υπάρχοντα sponsor scripts, μαζί με το Login Stealer.py. Το tier των $9 περιλαμβάνει κάθε script των $3 μαζί με τα Widget Maker.py, Kraken Trader.py και Noob Hacker.py. Αν υπάρχει παλιότερο τοπικό αντίγραφο, αντικαθίσταται μόνο αφού επιβεβαιωθεί η πρόσβαση.

### Termux Usage Stats

Η ενότητα usage stats δημιουργεί local activity snapshot του Termux workspace. Σε επόμενα scans συγκρίνει τις αλλαγές και αναφέρει τι δημιουργήθηκε, επεξεργάστηκε ή διαγράφηκε. Επίσης εντοπίζει programming language usage από file extensions, ελέγχει shell history commands, εμφανίζει πρόσφατη δραστηριότητα αρχείων και δείχνει τους πιο ενεργούς φακέλους.

### VPN & Tor Utilities

Η ενότητα network utilities δίνει προαιρετικά controls για Tor και proxy-based VPN routing χωρίς root. Το Tor μπορεί να ενεργοποιηθεί ή να απενεργοποιηθεί από το menu. Το VPN routing ενεργοποιείται ή απενεργοποιείται ξεχωριστά, χρησιμοποιεί επιλεγμένη χώρα ή ανανεωμένο proxy pool και αποθηκεύει την επιλεγμένη network κατάσταση ώστε να εφαρμόζεται ξανά όταν ξεκινά το Termux. Η οθόνη status δείχνει αν είναι ενεργό το Tor και το VPN routing, ποια χώρα είναι επιλεγμένη και ποιο proxy είναι ενεργό.

### DedSec OS Mode

Το **DedSec OS** είναι το browser-based local workspace mode μέσα στο Settings.py. Προσθέτει phone-first interface με file browser, safe text editor, terminal view, session manager, DedSec apps launcher, Linux package store actions, notifications, fullscreen και split view controls, sidebar controls, wallpaper support, display name settings, terminal color settings, project/menu settings, menu auto-start controls, language controls, prompt controls, password login, optional authenticator-style 2FA και password recovery μέσω τριών security questions. Περιλαμβάνει επίσης project action buttons για ενημέρωση και από τις δύο πηγές, ενημέρωση packages/modules, πρόσβαση σε Sponsors-Only scripts και άνοιγμα credits.

### Έμφαση στην Πρώτη Ρύθμιση

Μετά την εγκατάσταση, οι πιο σημαντικές ρυθμίσεις είναι:

1. διάλεξε την προτιμώμενη γλώσσα
2. διάλεξε menu style
3. άλλαξε το prompt αν θέλεις
4. τρέξε το **Save DedSec Project** στο πρώτο σου άνοιγμα
5. σύνδεσε GitHub μόνο αν θέλεις GitHub stats, prompt syncing ή Sponsors-Only access
6. ενεργοποίησε ή απενεργοποίησε το menu auto-start ανάλογα με το πώς χρησιμοποιείς το Termux
7. χρησιμοποίησε το **Update Packages & Modules** όταν χρειάζεται ανανέωση dependencies
8. χρησιμοποίησε το **VPN & Tor Utilities** μόνο όταν θέλεις αυτά τα προαιρετικά network controls

### Υπενθύμιση για το Save DedSec Project

Χρησιμοποίησε το **Save DedSec Project** στο πρώτο σου άνοιγμα και μετά τρέχε το ξανά λίγες φορές κάθε χρόνο, ώστε το αποθηκευμένο πακέτο του DedSec Project να μένει ενημερωμένο και έτοιμο αν χρειαστεί επαναφορά. Μπορεί να πάρει λίγη ώρα ανάλογα με τη σύνδεσή σου στο internet και το terminal μπορεί να μένει κενό μέχρι να ολοκληρωθεί.

</details>

<a id="greek-toolkit"></a>

<details>
<summary><strong>Εξερευνήστε την Εργαλειοθήκη</strong></summary>


> **ΚΡΙΣΙΜΗ ΣΗΜΕΙΩΣΗ:** Τα παρακάτω scripts περιλαμβάνονται μόνο για **εκπαιδευτικούς και αμυντικούς σκοπούς**. Ο ρόλος τους είναι να βοηθούν τους χρήστες να κατανοούν πώς λειτουργούν εργαλεία, lures και simulations, ώστε να βελτιώνουν την επίγνωση, την πειθαρχία στις δοκιμές και την αυτοπροστασία τους μέσα σε ελεγχόμενα περιβάλλοντα.

### Σύνοψη Toolkit

- **Developer Base:** 10 εργαλεία
- **Network Tools:** 10 εργαλεία
- **Other Tools:** 5 εργαλεία
- **Games:** 6 εργαλεία
- **Personal Information Capture:** 17 εργαλεία
- **Social Media / Fake Pages:** 25 εργαλεία
- **No Category:** 3 εργαλεία
- **Sponsors-Only:** 6 εργαλεία στο $3 tier / 9 εργαλεία στο $9 tier

**Συνολικά καταχωρημένα στη σελίδα εργαλείων:** 85 εργαλεία

---
<a id="greek-developer-base"></a>

<h2>Βάση Προγραμματιστή</h2>


<details>
<summary>File Converter</summary>


**Περιγραφή:** Ένας ισχυρός μετατροπέας αρχείων που υποστηρίζει 40+ μορφές. Οργανώνει τις Λήψεις. Προηγμένος διαδραστικός μετατροπέας αρχείων για Termux χρησιμοποιώντας διεπαφή curses. Υποστηρίζει 40 διαφορετικές μορφές αρχείων σε εικόνες, έγγραφα, ήχο, βίντεο και αρχεία. Διαθέτει αυτόματη εγκατάσταση εξαρτήσεων, οργανωμένη δομή φακέλων και ολοκληρωμένες δυνατότητες μετατροπής. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Τα converted αρχεία αποθηκεύονται στο /storage/emulated/0/Download/File Converter/, μέσα σε φακέλους format όπως JPG, PNG, PDF, MP3, MP4, ZIP, TXT και άλλα.`

</details>

<details>
<summary>File Type Checker</summary>


**Περιγραφή:** Προηγμένος αναλυτής αρχείων και σαρωτής ασφαλείας που εντοπίζει τύπους αρχείων, εξάγει μεταδεδομένα, υπολογίζει κρυπτογραφικά hashes και αναγνωρίζει πιθανές απειλές. Διαθέτει ανίχνευση magic byte, ανάλυση εντροπίας, ανίχνευση steganography, σάρωση ιών μέσω VirusTotal API και αυτόματη καραντίνα ύποπτων αρχείων. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Τα αρχεία ελέγχονται στο /sdcard/Download/File Type Checker/ στο Termux ή στο ~/Downloads/File Type Checker/ εκτός Termux. Τα quarantined αρχεία μένουν στον ίδιο φάκελο και μετονομάζονται με κατάληξη .dangerous.`

</details>

<details>
<summary>Mobile Desktop</summary>


**Περιγραφή:** Διαχειριστής Linux Desktop για Termux (χωρίς root): στήνει proot-distro περιβάλλον με επιλογές VNC/X11 και πρόγραμμα διαχείρισης εφαρμογών (install/update/remove). Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Οι ρυθμίσεις του manager αποθηκεύονται στο ~/.termux_linux_vnc_manager/config.json. Τα generated launchers εγκαθίστανται στο $PREFIX/bin/ ως vnc-<system>. Τα Linux distributions διαχειρίζονται από το proot-distro.`

</details>

<details>
<summary>Mobile Developer Setup</summary>


**Περιγραφή:** Αυτοματοποιεί web-dev περιβάλλον σε Termux: εγκαθιστά βασικά εργαλεία, ρυθμίζει paths και δίνει γρήγορο project scaffolding. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Το state και τα backup archives αποθηκεύονται στο ~/.mobile-dev-setup/ (μαζί με backups/ και state.json). Τα helper scripts μπαίνουν στο ~/.mobile-dev-setup-tools/, τα plugins στο ~/.zsh-plugins/ και τα αρχεία εμφάνισης του Termux στο ~/.termux/.`

</details>

<details>
<summary>Simple Websites Creator</summary>


**Περιγραφή:** Ένας ολοκληρωμένος δημιουργός ιστοσελίδων που δημιουργεί ανταποκρινόμενες HTML ιστοσελίδες με προσαρμόσιμη διάταξη, χρώματα, γραμματοσειρές και ρυθμίσεις SEO. Χαρακτηριστικά περιλαμβάνουν πολλαπλούς οδηγούς φιλοξενίας, προεπισκόπηση σε πραγματικό χρόνο, φιλικά για κινητά σχέδια και επαγγελματικά πρότυπα. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Τα websites που δημιουργούνται αποθηκεύονται στο /storage/emulated/0/Download/Websites/.`

</details>

<details>
<summary>Smart Notes</summary>


**Περιγραφή:** Εφαρμογή σημειώσεων terminal με υπενθυμίσεις. Προηγμένη εφαρμογή σημειώσεων με λειτουργικότητα υπενθύμισης, που διαθέτει τόσο TUI (Διεπαφή Κειμένου) όσο και υποστήριξη CLI. Περιλαμβάνει εξελιγμένο σύστημα υπενθυμίσεων με ημερομηνίες λήξης, αυτόματη εκτέλεση εντολών, ενσωμάτωση εξωτερικού επεξεργαστή και ολοκληρωμένες δυνατότητες οργάνωσης σημειώσεων. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Σημειώσεις: ~/.smart_notes.json | Ρυθμίσεις: ~/.smart_notes_config.json | Error log: ~/.smart_notes_error.log`

</details>

<details>
<summary>Dead Man's Switch</summary>


**Περιγραφή:** Emergency/SOS εργαλείο για Termux που βασίζεται στη λειτουργία I Need Help. Μετά το first-time setup και καθαρές επιβεβαιώσεις από τον χρήστη, μπορεί να κάνει public το dead-mans-switch GitHub repository, να δημιουργήσει GitHub Pages emergency website, να ανεβάσει οργανωμένα emergency αρχεία, να τραβήξει διαθέσιμες φωτογραφίες από κάμερες, ηχογραφήσεις μικροφώνου και location updates σε ρυθμιζόμενα χρονικά διαστήματα μέσω Termux:API permissions, και να στείλει SMS alerts με το website/repository link σε configured trusted contacts. Περιλαμβάνει επίσης create/update uploads, overwrite sync, visibility controls, legacy repository migration, previous-history backups, logs και kill/cleanup option.

Πρόβλημα που μου λύνει: αν κάτι μου συμβεί ή χρειαστώ βοήθεια γρήγορα, μπορώ να δημιουργήσω άμεσα ένα ορατό SOS-style emergency signal από το κινητό μου. Το I Need Help μπορεί να δημοσιεύσει shareable GitHub Pages link με ιστορικό τοποθεσίας, media captures, emergency πληροφορίες και SMS alerts για trusted contacts, ώστε να μην χρειάζεται να εξηγήσω τα πάντα χειροκίνητα μέσα στον πανικό.

**Τοποθεσία Αποθήκευσης:** `Κύριος τοπικός φάκελος: ~/storage/downloads/Dead Man's Switch/ (κανονικά ο φάκελος Download του τηλεφώνου, με fallback /storage/emulated/0/Download/Dead Man's Switch/). Ρυθμίσεις: ~/.dead_switch_settings.json. Τα logs και τα προηγούμενα repository backups αποθηκεύονται μέσα στον κύριο φάκελο στα Logs/ και History/.`

</details>

<details>
<summary>Tree Explorer</summary>


**Περιγραφή:** Εξερευνητής αρχείων για Termux: περιήγηση φακέλων, αναζήτηση αρχείων, εύρεση διπλότυπων με hash και καθαρισμός άδειων φακέλων με ασφαλείς επιλογές. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Το Tree Explorer δεν δημιουργεί default φάκελο αποτελεσμάτων. Τα exports γράφονται μόνο στο path που επιλέγεις με --export FILE ή από το interactive export prompt. Η εγκατάσταση της εντολής το αντιγράφει από προεπιλογή στο $PREFIX/bin/supertree.`

</details>

<details>
<summary>Devices Finder</summary>


**Περιγραφή:** Εργαλείο ανακάλυψης συσκευών τοπικού δικτύου για Termux που λειτουργεί χωρίς root. Διαχωρίζει τον εντοπισμό live hosts από το service scanning για να μειώνει τα false positives, αναγνωρίζει τύπους συσκευών με βάση ports, banners, hostnames και vendor hints, περιλαμβάνει interactive scan profiles και φίλτρα τύπου, και προαιρετικά εμπλουτίζει τα αποτελέσματα με mDNS, UPnP, SNMP και NetBIOS clues. Εξάγει αναφορές JSON, TXT, CSV και HTML. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Τα reports αποθηκεύονται στο ~/storage/downloads/Devices Finder/ ως devices_scan_<timestamp>.json, .txt, .csv και .html. Τα fallbacks είναι ~/downloads/Devices Finder/ και μετά ./Devices Finder Output/.`

</details>

<details>
<summary>Free Internet</summary>


**Περιγραφή:** Local-first browser και ασφαλές vault για Termux. Συνδυάζει πολλαπλές μηχανές αναζήτησης, bookmarks, ιστορικό, αποθηκευμένες σελίδες, καθαρισμό διαφημίσεων και trackers, Lite mode, δρομολόγηση μέσω proxy ανά χώρα με smart/strict/direct modes, προαιρετική υποστήριξη Tor, κρυπτογραφημένες εγγραφές vault μέσω OpenSSL και ενσωματωμένο εργαλείο full-page screenshots ιστοσελίδων. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Στο Termux όλα τα δεδομένα αποθηκεύονται στο ~/Free Internet/, ενώ εκτός Termux χρησιμοποιείται το ~/.free_internet/. Τα browser data είναι στο browser/, οι saved pages στο browser/saved/, τα screenshots στο tools/screenshots/ και το encrypted vault database στο vault/vault.db.`

</details>


<a id="greek-network-tools"></a>

<h2>Εργαλεία Δικτύου</h2>


<details>
<summary>Bug Hunter</summary>


**Περιγραφή:** Bug Hunter (χωρίς root) — εξουσιοδοτημένο εργαλείο αναγνώρισης web ασφάλειας και ελέγχου κακής ρύθμισης. Ελέγχει security headers και cookie flags, ανιχνεύει τεχνολογίες, κάνει DNS ελέγχους (SPF/DMARC/CAA), αναλύει TLS/λήξη πιστοποιητικού, ελέγχει CORS και HTTP μεθόδους, βρίσκει εκτεθειμένα ευαίσθητα αρχεία, κάνει crawl στο site και αναλύει JavaScript για endpoints και πιθανές διαρροές μυστικών. Υποστηρίζει προαιρετικό directory discovery και Wayback recon, και παράγει απο-διπλοποιημένες αναφορές (JSON/CSV/HTML/PDF). Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

**Τοποθεσία Αποθήκευσης:** `Ο default output φάκελος είναι ./bughunter_out/ στον κατάλογο από όπου εκτελείται το script. Με --output PATH επιλέγεις άλλο φάκελο. Τα reports περιλαμβάνουν report.json, report.csv, report.html, προαιρετικό report.pdf και προαιρετικά live/checkpoint files.`

</details>

<details>
<summary>Dark</summary>


**Περιγραφή:** Ένα εξειδικευμένο εργαλείο OSINT και crawler για το Dark Web, σχεδιασμένο για ανάλυση δικτύου Tor. Διαθέτει αυτοματοποιημένη σύνδεση Tor, ενσωμάτωση αναζήτησης Ahmia και αναδρομικό crawler για ιστοσελίδες .onion. Το εργαλείο χρησιμοποιεί ένα αρθρωτό σύστημα πρόσθετων για την εξαγωγή συγκεκριμένων τύπων δεδομένων (Email, διευθύνσεις BTC/XMR, κλειδιά PGP, Τηλέφωνα) και υποστηρίζει την αποθήκευση στιγμιότυπων. Προσφέρει λειτουργία Curses TUI και CLI, με αποτελέσματα εξαγώγιμα σε JSON, CSV και TXT. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

**Τοποθεσία Αποθήκευσης:** `Τα αποτελέσματα αποθηκεύονται στο /sdcard/Download/DarkNet/ με fallback στο ~/DarkNet/. JSON, CSV, TXT, snapshots και plugin output γράφονται εκεί, ενώ τα plugins αποθηκεύονται στον υποφάκελο plugins/.`

</details>

<details>
<summary>DedSec's Network</summary>


**Περιγραφή:** Μια προηγμένη εργαλειοθήκη δικτύου χωρίς root. Διαθέτει αναδρομικό πρόγραμμα λήψης ιστοσελίδων με υποστήριξη ZIP, πολυνηματικό σαρωτή θυρών, δοκιμή ταχύτητας internet και εργαλεία OSINT (WHOIS, DNS, Reverse IP). Περιλαμβάνει σαρωτές ελέγχου ιστού για SQLi, XSS, ανίχνευση CMS και SSH brute-force. Διατηρεί τοπικό αρχείο καταγραφής ελέγχου SQLite. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

**Τοποθεσία Αποθήκευσης:** `Τα config, audit_results.db και wordlists αποθηκεύονται στο ~/DedSec's Network/ στο Termux ή στο ./DedSec's Network/ αλλού. Τα downloaded websites μπαίνουν στο /storage/emulated/0/Download/Websites/<domain>/, με fallbacks τα /sdcard/Download/Websites/, ~/DedSec's Network/Websites/ ή ~/Downloads/Websites/ εκτός Termux.`

</details>

<details>
<summary>Digital Footprint Finder</summary>


**Περιγραφή:** Συντηρητικό εργαλείο OSINT ελέγχου usernames με στόχο τα καλύτερα πρακτικά αποτελέσματα και ελάχιστα ψευδώς θετικά. Σαρώνει μεγάλο πλήθος sites μέσω packs (core/extended) με προαιρετική βάση Sherlock, χρησιμοποιώντας βαθμολόγηση πολλαπλών σημάτων (status/redirects, title/meta/canonical/text) και όρια ταυτόχρονης σύνδεσης ανά domain για σταθερότητα. Ανιχνεύει anti-bot/JS challenges ως POSSIBLE (ποτέ ψευδώς FOUND), υποστηρίζει προαιρετικό search-engine dorking και εισαγωγή/εξαγωγή προσαρμοσμένων λιστών sites. Εξάγει αναφορές σε TXT/JSON/CSV και προαιρετικά HTML. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

**Τοποθεσία Αποθήκευσης:** `Τα reports αποθηκεύονται στο ~/storage/downloads/Digital Footprint Finder/. Αν δεν είναι διαθέσιμο, το script χρησιμοποιεί /sdcard/Download/Digital Footprint Finder/, μετά ~/Digital Footprint Finder/ και τέλος τον τρέχοντα κατάλογο. Τα αρχεία έχουν μορφή <username>_<timestamp>.txt, με προαιρετικά .json, .csv και .html exports.`

</details>

<details>
<summary>Connections.py</summary>


**Περιγραφή:** Ασφαλής διακομιστής συνομιλίας/κοινής χρήσης αρχείων. Κλήσεις βίντεο, κοινή χρήση αρχείων (όριο 50GB). Ενοποιημένη εφαρμογή που συνδυάζει το Butterfly Chat και τη Βάση Δεδομένων DedSec με μοναδικό μυστικό κλειδί πιστοποίησης. Παρέχει ανταλλαγή μηνυμάτων σε πραγματικό χρόνο, κοινή χρήση αρχείων, κλήσεις βίντεο και ολοκληρωμένη διαχείριση αρχείων. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

**Τοποθεσία Αποθήκευσης:** `Τα shared files αποθηκεύονται στο ~/Downloads/DedSec's Database/. Αν ο φάκελος δεν μπορεί να δημιουργηθεί, το fallback είναι ./DedSec_Database_Files/ στον τρέχοντα κατάλογο. Τα Tor runtime data αποθηκεύονται ξεχωριστά στο ~/.foxchat_tor/.`

</details>

<details>
<summary>Link Shield</summary>


**Περιγραφή:** Εργαλείο ελέγχου συνδέσμων: ακολουθεί redirects, ελέγχει HTTPS/SSL, εντοπίζει ύποπτα domains/μοτίβα και βγάζει αναφορά ρίσκου πριν ανοίξεις σύνδεσμο. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

**Τοποθεσία Αποθήκευσης:** `Δεν δημιουργείται dedicated output φάκελος. Το linkshield_config_en.json, τα user-named JSON/Markdown reports και τα linkshield_batch_report.json/.csv αποθηκεύονται στον τρέχοντα κατάλογο.`

</details>

<details>
<summary>Masker</summary>


**Περιγραφή:** URL helper για καθαρά, readable test links και έλεγχο redirect behavior στα δικά σου workflows. Παρουσιάζεται μόνο για οργάνωση, demos και authorized awareness training, ποτέ για να κρύψει κακόβουλα links ή να ξεγελάσει κόσμο.

**Τοποθεσία Αποθήκευσης:** `Δεν αποθηκεύονται αρχεία. Το generated masked URL εμφανίζεται στο terminal.`

</details>

<details>
<summary>QR Code Generator</summary>


**Περιγραφή:** Δημιουργός κωδικού QR βασισμένος σε Python που δημιουργεί κωδικούς QR για URLs και τους αποθηκεύει στο φάκελο Downloads/QR Codes. Διαθέτει αυτόματη εγκατάσταση εξαρτήσεων, φιλική προς τον χρήστη διεπαφή και χειρισμό σφαλμάτων για αξιόπιστη λειτουργία. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

**Τοποθεσία Αποθήκευσης:** `Τα generated PNG images αποθηκεύονται στο ~/storage/downloads/QR Codes/.`

</details>

<details>
<summary>Sod</summary>


**Περιγραφή:** Ένα ολοκληρωμένο εργαλείο δοκιμής φόρτου για εφαρμογές web, με πολλαπλές μεθόδους δοκιμής (HTTP, WebSocket, προσομοίωση βάσης δεδομένων, μεταφόρτωση αρχείων, μικτό φόρτο εργασίας), μετρήσεις σε πραγματικό χρόνο και αυτόματη εγκατάσταση εξαρτήσεων. Προηγμένο πλαίσιο δοκιμής απόδοσης με ρεαλιστική προσομοίωση συμπεριφοράς χρήστη. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

**Τοποθεσία Αποθήκευσης:** `Το configuration file load_test_config.json αποθηκεύεται στον τρέχοντα κατάλογο. Τα test results εμφανίζονται στο terminal και δεν γράφονται σε report file.`

</details>

<details>
<summary>Store Scrapper</summary>


**Περιγραφή:** Μονοαρχείο Python store scrapper για Termux που λειτουργεί χωρίς root. Δοκιμάζει πολλούς τρόπους για να βρίσκει κατηγορίες και προϊόντα σε απλές HTML σελίδες αλλά και σε πολλά JS-style stores, διαβάζοντας HTML, JSON-LD, embedded JSON, sitemaps, Shopify endpoints, WooCommerce APIs, generic product cards, breadcrumbs, OpenGraph/meta tags και εσωτερικούς συνδέσμους. Αποθηκεύει όσο τρέχει, ξεκινά πλήρες scraping προϊόντος μόλις βρεθεί κάθε προϊόν, δείχνει live κατάσταση στο terminal, χρησιμοποιεί το Enter ως προεπιλογή στα prompts και οργανώνει τα αποτελέσματα σε φακέλους store/category/product με κατεβασμένες εικόνες. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

**Τοποθεσία Αποθήκευσης:** `Τα product data αποθηκεύονται στο ~/storage/downloads/Store Scrapper/<Store>/<Category>/<Product>/. Αν το Termux Downloads δεν είναι διαθέσιμο, χρησιμοποιείται το ~/downloads/Store Scrapper/. Οι product folders μπορούν να περιέχουν FOUND.txt, metadata.json, summary.txt, description.txt, images/ και images.json, ενώ τα discovery και run-state files μένουν στο store output tree.`

</details>


<a id="greek-personal-information-capture"></a>

<h2>Συλλογή Προσωπικών Πληροφοριών (Μόνο για Εκπαιδευτική Χρήση)</h2>


Αυτά τα scripts είναι training simulations που έχουν στόχο να βοηθούν τους χρήστες να κατανοούν πώς μπορεί να παρουσιάζονται παραπλανητικές σελίδες συλλογής προσωπικών δεδομένων, ώστε να τις αναγνωρίζουν και να αμύνονται καλύτερα απέναντί τους σε ελεγχόμενα περιβάλλοντα.

<details>
<summary>Fake Back Camera Page</summary>


**Περιγραφή:** Το Fake Back Camera Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Back Camera. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Οι captured εικόνες της πίσω κάμερας και τα σχετικά text data αποθηκεύονται στο ~/storage/downloads/Camera-Phish-Back/.`

</details>

<details>
<summary>Fake Back Camera Video Page</summary>


**Περιγραφή:** Το Fake Back Camera Video Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Back Camera Video. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα recorded WEBM videos της πίσω κάμερας και τα σχετικά text data αποθηκεύονται στο ~/storage/downloads/Back Camera Videos/.`

</details>

<details>
<summary>Fake Card Details Page</summary>


**Περιγραφή:** Το Fake Card Details Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Card Details. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα submitted card-activation data αποθηκεύονται στο ~/storage/downloads/CardActivations/.`

</details>

<details>
<summary>Fake Chrome Verification Page</summary>


**Περιγραφή:** Το Fake Chrome Verification Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Chrome Verification. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα Chrome verification outputs, μαζί με location JSON, face video, device scan, system information και summaries, αποθηκεύονται στο ~/storage/downloads/Chrome Verification/.`

</details>

<details>
<summary>Fake Data Grabber Page</summary>


**Περιγραφή:** Το Fake Data Grabber Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Data Grabber. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα collected application information αποθηκεύονται στο ~/storage/downloads/Peoples_Lives/, μαζί με το application_info.txt.`

</details>

<details>
<summary>Fake Discord Verification Page</summary>


**Περιγραφή:** Το Fake Discord Verification Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Discord Verification. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα Discord verification outputs, μαζί με location JSON, face video, ID, phone, payment και summary files, αποθηκεύονται στο ~/storage/downloads/Discord Verification/.`

</details>

<details>
<summary>Fake Facebook Verification Page</summary>


**Περιγραφή:** Το Fake Facebook Verification Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Facebook Verification. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα Facebook verification outputs, μαζί με location JSON, face video, ID images και summary files, αποθηκεύονται στο ~/storage/downloads/Facebook Verification/.`

</details>

<details>
<summary>Fake Front Camera Page</summary>


**Περιγραφή:** Το Fake Front Camera Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Front Camera. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Οι captured εικόνες της μπροστινής κάμερας και τα σχετικά text data αποθηκεύονται στο ~/storage/downloads/Camera-Phish-Front/.`

</details>

<details>
<summary>Fake Front Camera Video Page</summary>


**Περιγραφή:** Το Fake Front Camera Video Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Front Camera Video. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα recorded WEBM videos της μπροστινής κάμερας και τα σχετικά text data αποθηκεύονται στο ~/storage/downloads/Front Camera Videos/.`

</details>

<details>
<summary>Fake Google Location Page</summary>


**Περιγραφή:** Το Fake Google Location Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Google Location. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα location JSON files αποθηκεύονται στο ~/storage/downloads/Locations/.`

</details>

<details>
<summary>Fake Instagram Verification Page</summary>


**Περιγραφή:** Το Fake Instagram Verification Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Instagram Verification. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα Instagram verification outputs, μαζί με location JSON, face video, voice audio, ID documents και summary files, αποθηκεύονται στο ~/storage/downloads/Instagram Verification/.`

</details>

<details>
<summary>Fake Location Page</summary>


**Περιγραφή:** Το Fake Location Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Location. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα location JSON files αποθηκεύονται στο ~/storage/downloads/Locations/.`

</details>

<details>
<summary>Fake Microphone Page</summary>


**Περιγραφή:** Το Fake Microphone Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Microphone. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα recorded audio, τα converted WAV files και τα σχετικά text data αποθηκεύονται στο ~/storage/downloads/Recordings/.`

</details>

<details>
<summary>Fake OnlyFans Verification Page</summary>


**Περιγραφή:** Το Fake OnlyFans Verification Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από OnlyFans Verification. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα OnlyFans verification outputs, μαζί με location JSON, face video, ID, payment και summary files, αποθηκεύονται στο ~/storage/downloads/OnlyFans Verification/.`

</details>

<details>
<summary>Fake Steam Verification Page</summary>


**Περιγραφή:** Το Fake Steam Verification Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Steam Verification. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα Steam verification outputs, μαζί με location JSON, face video, ID, Steam Guard, phone, payment και summary files, αποθηκεύονται στο ~/storage/downloads/Steam Verification/.`

</details>

<details>
<summary>Fake Twitch Verification Page</summary>


**Περιγραφή:** Το Fake Twitch Verification Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Twitch Verification. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα Twitch verification outputs, μαζί με location JSON, face video, ID, payment και summary files, αποθηκεύονται στο ~/storage/downloads/Twitch Verification/.`

</details>

<details>
<summary>Fake YouTube Verification Page</summary>


**Περιγραφή:** Το Fake YouTube Verification Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από YouTube Verification. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα YouTube verification outputs, μαζί με location JSON, face video, ID, payment και summary files, αποθηκεύονται στο ~/storage/downloads/YouTube Verification/.`

</details>


<a id="greek-fake-pages"></a>

<h2>Ψεύτικες Σελίδες (Μόνο για Εκπαιδευτική Χρήση)</h2>


Αυτά τα scripts είναι εκπαιδευτικά simulations που έχουν στόχο να βοηθούν τους χρήστες να αναγνωρίζουν social-engineering patterns, ψεύτικες reward pages, ψεύτικες verification flows και imitation brand pages που συχνά χρησιμοποιούνται για να πιέζουν ανθρώπους σε μη ασφαλείς ενέργειες.

<details>
<summary>Fake Apple iCloud Page</summary>


**Περιγραφή:** Το Fake Apple iCloud Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Apple iCloud προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/Apple iCloud/.`

</details>

<details>
<summary>Fake Discord Nitro Page</summary>


**Περιγραφή:** Το Fake Discord Nitro Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Discord Nitro προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/Discord Nitro/.`

</details>

<details>
<summary>Fake Epic Games Page</summary>


**Περιγραφή:** Το Fake Epic Games Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Epic Games προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/Epic Games/.`

</details>

<details>
<summary>Fake Facebook Friends Page</summary>


**Περιγραφή:** Το Fake Facebook Friends Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Facebook Friends προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/Facebook Friends/.`

</details>

<details>
<summary>Fake Free Robux Page</summary>


**Περιγραφή:** Το Fake Free Robux Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Free Robux προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/Roblox Robux/.`

</details>

<details>
<summary>Fake GitHub Pro Page</summary>


**Περιγραφή:** Το Fake GitHub Pro Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες GitHub Pro προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/GitHub Pro/.`

</details>

<details>
<summary>Fake Google Free Money Page</summary>


**Περιγραφή:** Το Fake Google Free Money Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Google Free Money προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/Google Free Money/.`

</details>

<details>
<summary>Fake Instagram Followers Page</summary>


**Περιγραφή:** Το Fake Instagram Followers Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Instagram Followers προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/Instagram Followers/.`

</details>

<details>
<summary>Fake MetaMask Page</summary>


**Περιγραφή:** Το Fake MetaMask Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες MetaMask προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/MetaMask/.`

</details>

<details>
<summary>Fake Microsoft 365 Page</summary>


**Περιγραφή:** Το Fake Microsoft 365 Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Microsoft 365 προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/Microsoft 365/.`

</details>

<details>
<summary>Fake OnlyFans Page</summary>


**Περιγραφή:** Το Fake OnlyFans Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες OnlyFans προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/OnlyFans/.`

</details>

<details>
<summary>Fake PayPal Page</summary>


**Περιγραφή:** Το Fake PayPal Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες PayPal προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form και card data γράφονται στο ~/storage/downloads/PayPal/.`

</details>

<details>
<summary>Fake Pinterest Pro Page</summary>


**Περιγραφή:** Το Fake Pinterest Pro Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Pinterest Pro προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/Pinterest Pro/.`

</details>

<details>
<summary>Fake PlayStation Network Page</summary>


**Περιγραφή:** Το Fake PlayStation Network Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες PlayStation Network προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/PlayStation Network/.`

</details>

<details>
<summary>Fake Reddit Karma Page</summary>


**Περιγραφή:** Το Fake Reddit Karma Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Reddit Karma προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/Reddit Karma/.`

</details>

<details>
<summary>Fake Snapchat Friends Page</summary>


**Περιγραφή:** Το Fake Snapchat Friends Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Snapchat Friends προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/Snapchat Friends/.`

</details>

<details>
<summary>Fake Steam Games Page</summary>


**Περιγραφή:** Το Fake Steam Games Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Steam Games προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/Steam Games/.`

</details>

<details>
<summary>Fake Steam Wallet Page</summary>


**Περιγραφή:** Το Fake Steam Wallet Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Steam Wallet προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/Steam Wallet/.`

</details>

<details>
<summary>Fake TikTok Followers Page</summary>


**Περιγραφή:** Το Fake TikTok Followers Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες TikTok Followers προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/TikTok Followers/.`

</details>

<details>
<summary>Fake Trust Wallet Page</summary>


**Περιγραφή:** Το Fake Trust Wallet Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Trust Wallet προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/Trust Wallet/.`

</details>

<details>
<summary>Fake Twitch Subs Page</summary>


**Περιγραφή:** Το Fake Twitch Subs Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Twitch Subs προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/Twitch Subs/.`

</details>

<details>
<summary>Fake Twitter Followers Page</summary>


**Περιγραφή:** Το Fake Twitter Followers Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Twitter Followers προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/Twitter Followers/.`

</details>

<details>
<summary>Fake What's Up Dude Page</summary>


**Περιγραφή:** Το Fake What's Up Dude Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες What's Up Dude προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/WhatsUp Dude/.`

</details>

<details>
<summary>Fake Xbox Live Page</summary>


**Περιγραφή:** Το Fake Xbox Live Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Xbox Live προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/Xbox Live/.`

</details>

<details>
<summary>Fake YouTube Subscribers Page</summary>


**Περιγραφή:** Το Fake YouTube Subscribers Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες YouTube Subscribers προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα saved form data γράφονται στο ~/storage/downloads/YouTube Subscribers/.`

</details>


<a id="greek-games"></a>

<h2>Παιχνίδια</h2>


<details>
<summary>Buzz</summary>


**Περιγραφή:** Ένα text-only παιχνίδι trivia για Termux με ενσωματωμένη σταθερή βάση 15.000 ερωτήσεων (χωρίς δημιουργία κατά την εκτέλεση). Υποστηρίζει 1–2 παίκτες (pass-and-play), πολλούς τύπους γύρων, φίλτρο δυσκολίας (Όλες/Εύκολες/Μέτριες/Δύσκολες), προφίλ, ρυθμίσεις και πίνακες βαθμολογίας. Ελαφρύ παιχνίδι τερματικού με γρήγορους χειρισμούς και δυνατότητα επανάληψης.

**Τοποθεσία Αποθήκευσης:** `Όλα τα δεδομένα του παιχνιδιού αποθηκεύονται στο ~/Buzz/data/: questions_en.jsonl.gz, highscores.json, profiles.json και settings.json.`

</details>

<details>
<summary>CTF God</summary>


**Περιγραφή:** Πλήρες CTF παιχνίδι για Termux σε fullscreen Curses, με story mode, αποστολές, daily challenges, τυχαία boss levels, κατάστημα hints, achievements & ranks, εισαγωγή/εξαγωγή challenge packs, tournament mode και anti‑cheat/integrity checks. Περιλαμβάνει ενσωματωμένο level editor. Ελαφρύ παιχνίδι τερματικού με γρήγορους χειρισμούς και δυνατότητα επανάληψης.

**Τοποθεσία Αποθήκευσης:** `Τα challenge workspaces αποθηκεύονται στο /storage/emulated/0/Download/CTF God/, με fallbacks τα ~/storage/downloads/CTF God/ και ~/CTF God/. Τα profiles, progress, packs και custom challenges αποθηκεύονται στο ~/.ctf_god/ (state.json, custom.json, packs/).`

</details>

<details>
<summary>Detective</summary>


**Περιγραφή:** Ένα story-driven παιχνίδι ντετέκτιβ για Termux στο terminal με διευρυμένη σταθερή βιβλιοθήκη υποθέσεων, πλουσιότερα lore dossiers, φήμες περιοχών, side stories και επιπλέον story threads. Παρακολουθήστε στοιχεία, ανακρίνετε υπόπτους, δείτε suspect rosters, χτίστε ASCII case board και timeline και διαχειριστείτε την πρόοδο με 3 save slots και autosave. Περιλαμβάνει 4 δυσκολίες, notes/evidence tracking, checkpoint hints και γρήγορες εντολές όπως :help, :guide, :lore, :suspects, :board, :timeline, :hint και :save.

**Τοποθεσία Αποθήκευσης:** `Όλα τα saves αποθηκεύονται στο ~/Detective/: player.json, highscores.json και savegame_slot1.json έως savegame_slot3.json.`

</details>

<details>
<summary>Tamagotchi</summary>


**Περιγραφή:** Ένα πλήρως χαρακτηριστικό παιχνίδι κατοικίδιου terminal. Τρέφετε, παίζετε, καθαρίζετε και εκπαιδεύετε το κατοικίδιό σας. Μην το αφήσετε να πεθάνει. Προηγμένο παιχνίδι προσομοίωσης εικονικού κατοικίδιου με ολοκληρωμένο σύστημα διαχείρισης. Χαρακτηριστικά περιλαμβάνουν εξέλιξη κατοικίδιου μέσα από στάδια ζωής, χαρακτηριστικά προσωπικότητας, ανάπτυξη δεξιοτήτων, μίνι παιχνίδια, σύστημα εργασίας και συνταξιοδότηση κληρονομιάς. Ελαφρύ παιχνίδι τερματικού με γρήγορους χειρισμούς και δυνατότητα επανάληψης.

**Τοποθεσία Αποθήκευσης:** `Το save του Tamagotchi αποθηκεύεται στο ~/.termux_tamagotchi_v8.json.`

</details>

<details>
<summary>Pet Friends</summary>


**Περιγραφή:** Ένα idle παιχνίδι εικονικών συντρόφων για Termux με 160+ πραγματικά, θρυλικά και μυθολογικά κατοικίδια. Φροντίστε, εκπαιδεύστε, μετονομάστε, εξελίξτε και συλλέξτε συντρόφους, ολοκληρώνοντας αποστολές, quests, achievements, daily contracts, expeditions, treasure maps, festivals, upgrades, prestige στόχους και crates με διαφορετικές βαθμίδες σπανιότητας. Περιλαμβάνει εκπαιδευτικές πληροφορίες για ζώα, ξεκάθαρα επισημασμένη μυθολογία, κινούμενα ASCII κατοικίδια, τοπικά παραγόμενα ηχητικά εφέ και μουσική υπόκρουση, καθώς και προαιρετικές μάχες και ανταλλαγές μέσω τοπικού δικτύου.

**Τοποθεσία Αποθήκευσης:** `Το βασικό save αποθηκεύεται στο ~/Pet Friends/petfriends_save.json. Τα παραγόμενα ηχητικά εφέ, η μουσική υπόκρουση και τα αρχεία audio session του Pet Friends αποθηκεύονται στα ~/Pet Friends/sounds/ και ~/Pet Friends/.pet_friends_audio.json.`

</details>

<details>
<summary>Terminal Arcade</summary>


**Περιγραφή:** Πακέτο arcade για τερματικό με πολλά mini-games σε ένα script. Αποθηκεύει δεδομένα στο ~/Terminal Arcade/ και τρέχει ομαλά σε Termux/Linux. Ελαφρύ παιχνίδι τερματικού με γρήγορους χειρισμούς και δυνατότητα επανάληψης.

**Τοποθεσία Αποθήκευσης:** `Τα δεδομένα του arcade αποθηκεύονται στο ~/Terminal Arcade/. Τα high scores και το πρόσφατο score history αποθηκεύονται στο ~/Terminal Arcade/highscores.json.`

</details>


<a id="greek-other-tools"></a>

<h2>Άλλα Εργαλεία</h2>


<details>
<summary>Android App Launcher</summary>


**Περιγραφή:** Βοηθητικό πρόγραμμα για διαχείριση εφαρμογών Android απευθείας από το terminal. Μπορεί να εκκινήσει εφαρμογές, να εξάγει αρχεία APK, να απεγκαταστήσει εφαρμογές και να αναλύσει δικαιώματα ασφαλείας. Προηγμένο εργαλείο διαχείρισης εφαρμογών Android και ανάλυσης ασφαλείας. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Τα extracted APK files αποθηκεύονται στο ~/storage/shared/Download/Extracted APK's/. Τα security reports αποθηκεύονται στο ~/storage/shared/Download/App_Security_Reports/ ως <app>_security_report.txt.`

</details>

<details>
<summary>Loading Screen</summary>


**Περιγραφή:** Εξατομίκευση εκκίνησης Termux με ASCII art loading screens. Υποστηρίζει custom art, καθυστέρηση και αυτόματο setup/cleanup για εμφάνιση μία φορά. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Δεν δημιουργείται ξεχωριστός output φάκελος. Το selected loading screen γράφεται απευθείας στο ~/.bash_profile.`

</details>

<details>
<summary>Password Master</summary>


**Περιγραφή:** Ολοκληρωμένο σύνολο διαχείρισης κωδικών πρόσβασης με κρυπτογραφημένη αποθήκευση θησαυροφυλακίου, δημιουργία κωδικών, ανάλυση ισχύος και εργαλεία βελτίωσης. Περιλαμβάνει AES-256 κρυπτογραφημένο θησαυροφυλάκιο με προστασία κύριου κωδικού πρόσβασης, γεννήτρια τυχαίων κωδικών, γεννήτρια φράσεων πρόσβασης, αναλυτή ισχύος κωδικού και προτάσεις βελτίωσης κωδικών. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Το encrypted vault αποθηκεύεται ως ./my_vault.enc στον τρέχοντα κατάλογο. Τα backups αποθηκεύονται στο /storage/emulated/0/Download/Password Master Backup/vault_backup.enc ή στο ~/Downloads/Password Master Backup/ εκτός Android.`

</details>

<details>
<summary>Termux Backup Restore</summary>


**Περιγραφή:** Backup & restore για Termux: δημιουργεί zip backup των αρχείων σου στα Downloads και μπορεί να τα επαναφέρει με ελέγχους ακεραιότητας. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Το backup archive αποθηκεύεται ως /storage/emulated/0/Download/name_backup.zip. Τα split parts δημιουργούνται δίπλα στο archive. Το backup_config.json αποθηκεύεται στον τρέχοντα κατάλογο.`

</details>

<details>
<summary>Termux Repair Wizard</summary>


**Περιγραφή:** Μια no-root σουίτα διάγνωσης και επιδιόρθωσης για προβλήματα πακέτων, repositories, storage, πιστοποιητικών, cache, Python/pip, δικαιωμάτων και shell/PATH στο Termux. Μπορεί να ελέγξει mirrors και σύνδεση δικτύου, να διορθώσει broken packages, να επαναφέρει τα apt lists, να χειριστεί release-information και hash-sum errors, να καθαρίσει caches, να εγκαταστήσει ξανά βασικά εργαλεία και να εκτελέσει πλήρη καθοδηγούμενη διαδικασία επισκευής. Η επιλογή **Script Keeper** σαρώνει με ασφάλεια μεμονωμένα scripts ή ολόκληρους φακέλους χωρίς να τα εκτελεί απευθείας, αναγνωρίζει Python, shell, JavaScript/TypeScript, Ruby, Perl, PHP, Lua, Go, Rust, C/C++, Java, Kotlin, R, PowerShell, Dart, Scala, Groovy, Elixir, Erlang, Tcl, Haskell, C#, scripts με shebang και συνηθισμένα project manifests, ελέγχει syntax και απαιτούμενα εργαλεία, εγκαθιστά πακέτα ή modules που λείπουν, επεξεργάζεται dependency manifests και δοκιμάζει συμβατά replacement packages για Python modules που έχουν αφαιρεθεί από νεότερες εκδόσεις της Python.

**Τοποθεσία Αποθήκευσης:** `Οι επισκευές συστήματος εφαρμόζονται απευθείας στα Termux packages, στα storage permissions, στα $HOME permissions και σε shell files όπως ~/.bashrc, ~/.profile και ~/.zshrc. Τα reports του Script Keeper αποθηκεύονται στο ~/DedSec/logs/ ως script_keeper_<timestamp>.log.`

</details>


<a id="greek-no-category"></a>

<h2>Χωρίς Κατηγορία</h2>


<details>
<summary>Extra Content</summary>


**Περιγραφή:** Κόμβος extra περιεχομένου: γρήγορη πρόσβαση σε πρόσθετους πόρους, templates και προαιρετικά add-ons του DedSec toolkit. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Ο φάκελος Extra Content του repository αντιγράφεται στο ~/storage/downloads/Extra Content/.`

</details>

<details>
<summary>Settings.py</summary>


**Περιγραφή:** Το Settings.py είναι το κεντρικό control panel του DedSec Project. Εμφανίζει πληροφορίες project και συσκευής, ενημερώνει το project από την κύρια ή την backup πηγή, ανανεώνει Termux packages και Python modules, ελέγχει και κατεβάζει Sponsors-Only scripts μέσω συνδεδεμένου GitHub account, δημιουργεί backup του DedSec Project στα Downloads, αλλάζει το Termux prompt, συνδέει ή αποσυνδέει GitHub, εμφανίζει GitHub stats, συγχρονίζει το prompt με το GitHub username, σαρώνει Termux usage stats, διαχειρίζεται προαιρετικά VPN και Tor utilities, αλλάζει ανάμεσα σε List, Grid, Choose By Number και DedSec OS menu styles, ελέγχει το menu auto-start, αποθηκεύει επιλογή γλώσσας English ή Greek, εμφανίζει credits και κάνει ασφαλή απεγκατάσταση του project. Το DedSec OS προσθέτει browser-based local workspace με file browser, safe text editor, terminal view, session manager, DedSec apps launcher, Linux package store actions, notifications, fullscreen και split-view controls, sidebar controls, wallpaper support, display name settings, terminal color settings, project action buttons, language controls, prompt controls, password login, προαιρετικό authenticator-style 2FA και recovery μέσω τριών security questions. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Γλώσσα: ~/Language.json | Backup ρυθμίσεων Termux: ~/Termux.zip | Project archive: /storage/emulated/0/Download/DedSec Project Legacy Save.zip | GitHub account: ~/.dedsec_github_account.json | Usage stats: ~/.dedsec_termux_usage_stats.json | Network utility data: ~/.dedsec_network_utilities/ και ~/.dedsec_network_utilities.json`

</details>

<details>
<summary>DedSec Market</summary>


**Περιγραφή:** Curses-based market αποθετηρίων GitHub για Termux που εμφανίζει τα projects με το όνομα του project αντί για το ακατέργαστο όνομα του repository. Καθαρίζει και εμφανίζει σωστά το κείμενο των README, δείχνει releases και issues, υποστηρίζει ενέργειες install/update/delete και launch, κρατά watchlist και αποθηκεύει cache/state για πιο γρήγορη επαναχρησιμοποίηση. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Το Market state και cache αποθηκεύονται στο ~/DedSec Market/ (state.json και cache/). Τα installed repositories τοποθετούνται απευθείας στο ~/<repository-name>/, με -1, -2 κ.ο.κ. αν ο φάκελος υπάρχει ήδη.`

</details>


<a id="greek-sponsors-only"></a>

<h2>Μόνο για Χορηγούς</h2>


Το Sponsors-Only access χωρίζεται πλέον σε δύο GitHub Sponsors tiers:

| Tier | Τι περιλαμβάνει |
| :--- | :-------------- |
| **$3 Sponsor** | Τα υπάρχοντα sponsor scripts που εμφανίζονται ήδη στο website: Face Detector.py, Face Detector Heavy.py, Face Swap.py, Steganography.py, AR Terror.py και **Login Stealer.py**. |
| **$9 Pro Supporter** | Όλα τα scripts του $3 tier, μαζί με τα **Widget Maker.py**, **Kraken Trader.py** και **Noob Hacker.py**. |

**• Scripts Χορηγών $3**


<details>
<summary>Face Detector.py</summary>


**Περιγραφή:** Τοπικό browser-based εργαλείο ανάλυσης προσώπου για Termux που λειτουργεί χωρίς root. Χρησιμοποιεί MediaPipe Face Mesh στο live feed της κάμερας, υποστηρίζει μπροστινή και πίσω κάμερα, παρακολουθεί έως και 3 πρόσωπα, σχεδιάζει αναλυτικά facial landmark overlays αντί για απλά boxes και επιτρέπει επίσης upload φωτογραφιών ή βίντεο για ανάλυση απευθείας από το interface. Μπορεί να τραβά PNG snapshots, να γράφει WEBM βίντεο, να αποθηκεύει ξεχωριστά cropped detected faces και να παρέχει τόσο local network link όσο και προαιρετικό δημόσιο Cloudflare link.

**Τοποθεσία Αποθήκευσης:** Στο Termux, τα captures, τα recordings, τα uploaded results και τα αποθηκευμένα face crops μπαίνουν στο: ~/storage/downloads/Face Detector/. Αν το storage του Termux δεν είναι διαθέσιμο, γίνεται fallback στο ~/Face Detector/. Σε συστήματα εκτός Termux χρησιμοποιείται το ~/Downloads/Face Detector/, με fallback στο ~/Face Detector/. Τα εσωτερικά web αρχεία, τα certificates και τα helper binaries αποθηκεύονται στο ~/.face_detector_studio/.

</details>

<details>
<summary>Face Detector Heavy.py</summary>


**Περιγραφή:** Πιο βαριά και επεκταμένη έκδοση ανάλυσης του face detector για Termux, χωρίς ανάγκη για root. Εκτός από live χρήση κάμερας, εναλλαγή μπροστινής/πίσω κάμερας, upload φωτογραφιών και βίντεο, PNG snapshots, WEBM recording και αποθήκευση face crops, ανεβάζει την παρακολούθηση έως και σε 30 πρόσωπα και προσθέτει TensorFlow COCO-SSD object detection πάνω στο pipeline του MediaPipe face mesh. Εμφανίζει πιο πλούσιο on-screen telemetry όπως face count, animal/object detection, εκτιμήσεις pose και gaze, facial proportions, κατάσταση στόματος και φρυδιών, asymmetry scoring και άλλα visual analysis στοιχεία, ενώ συνεχίζει να υποστηρίζει local network link και προαιρετικό δημόσιο Cloudflare link.

**Τοποθεσία Αποθήκευσης:** Στο Termux, τα captures, τα recordings, τα uploaded results και τα αποθηκευμένα face crops μπαίνουν στο: ~/storage/downloads/Face Detector/. Αν το storage του Termux δεν είναι διαθέσιμο, γίνεται fallback στο ~/Face Detector/. Σε συστήματα εκτός Termux χρησιμοποιείται το ~/Downloads/Face Detector/, με fallback στο ~/Face Detector/. Τα εσωτερικά web αρχεία, τα certificates και τα helper binaries αποθηκεύονται στο ~/.face_detector_studio/.

</details>

<details>
<summary>Face Swap.py</summary>


**Περιγραφή:** Τοπικό browser-based εργαλείο face swap για Termux που λειτουργεί χωρίς root. Ανοίγει μια local camera σελίδα, σου επιτρέπει να ανεβάσεις μια source face εικόνα, να αλλάξεις ανάμεσα σε μπροστινή και πίσω κάμερα και να κάνεις blend το ανεβασμένο πρόσωπο πάνω στο live camera feed με MediaPipe Face Mesh. Η τρέχουσα έκδοση εστιάζει σε smooth face-lock λογική: κλειδώνει το ανεβασμένο πρόσωπο μία φορά, ακολουθεί το live πρόσωπο, κινεί βασικά feature patches για expressions, περιλαμβάνει smoothing, feathering, opacity, blend και skin-tone matching controls και μπορεί να αποθηκεύει PNG snapshots από τον browser. Χρησιμοποίησέ το μόνο με δικές σου εικόνες ή με ξεκάθαρη άδεια.

**Τοποθεσία Αποθήκευσης:** Στο Termux, οι αποθηκευμένες φωτογραφίες μπαίνουν στο: /storage/emulated/0/Download/Face Swap/ ή στο ~/storage/downloads/Face Swap/, με fallback στο ~/Face Swap/. Σε συστήματα εκτός Termux χρησιμοποιείται το ~/Downloads/Face Swap/, με fallback στο ~/Face Swap/.

</details>

<details>
<summary>Steganography.py</summary>


**Περιγραφή:** Σουίτα steganography με κωδικό για Termux. Μπορεί να δημιουργεί τυχαίες ασπρόμαυρες PNG εικόνες-φορείς, να κρυπτογραφεί μυστικό κείμενο με password-derived Fernet key, να κρύβει το κρυπτογραφημένο κείμενο μέσα σε PNG εικόνες με LSB steganography και να κάνει batch αποκωδικοποίηση κρυμμένων μηνυμάτων από όλες τις εικόνες που τοποθετούνται στον φάκελο Decrypt. Τα εξαγόμενα μηνύματα αποθηκεύονται αυτόματα ως ξεχωριστά αρχεία .txt και το script μπορεί προαιρετικά να καθαρίζει τις ήδη επεξεργασμένες εικόνες από τον φάκελο αποκωδικοποίησης μετά το scan.

**Τοποθεσία Αποθήκευσης:** Κύριος φάκελος: /storage/emulated/0/Download/Steganography/ | Carrier/output εικόνες: /Encrypt | Εικόνες για έλεγχο κρυμμένων μηνυμάτων: /Decrypt | Εξαγόμενα αρχεία κειμένου: /Decrypted Texts

</details>

<details>
<summary>AR Terror.py</summary>


**Περιγραφή:** Τοπική browser-based AR horror εμπειρία για Termux που λειτουργεί χωρίς root. Εκκινεί μια full-screen camera-driven ιστοσελίδα όπου εξερευνάς το περιβάλλον, συλλέγεις κρυμμένα logs μέσα σε archive/inventory σύστημα, χρησιμοποιείς ατμοσφαιρικά visual και audio effects, αλλάζεις ανάμεσα σε μπροστινή και πίσω κάμερα και γράφεις evidence σε WEBM όσο τρέχει η εμπειρία. Μπορεί επίσης να παρέχει τόσο local network link όσο και προαιρετικό δημόσιο Cloudflare link.

**Τοποθεσία Αποθήκευσης:** Στο Termux, το recorded evidence αποθηκεύεται στο: ~/storage/downloads/AR Terror/. Αν το storage του Termux δεν είναι διαθέσιμο, γίνεται fallback στο ~/AR Terror/. Σε συστήματα εκτός Termux χρησιμοποιείται το ~/Downloads/AR Terror/, με fallback στο ~/AR Terror/. Τα εσωτερικά web αρχεία, τα certificates και τα helper binaries αποθηκεύονται στο ~/.ar_terror_studio/.

</details>

<details>
<summary>Login Stealer.py</summary>


**Περιγραφή:** Το Login Stealer.py είναι ένα πλήρως λειτουργικό ελεγχόμενο login-security simulation εργαλείο για Termux που δείχνει πώς ψεύτικες σελίδες login, αντιγραμμένες authentication screens, redirects, session behavior και verification-style traps μπορούν να κάνουν έναν χρήστη να εμπιστευτεί λάθος σελίδα. Είναι φτιαγμένο για awareness training, lab demonstrations, screenshots και dummy-account testing, ώστε οι αρχάριοι να καταλάβουν πώς μοιάζουν τα phishing-style login tricks πριν πέσουν σε κάτι τέτοιο στην πραγματική ζωή. Χρησιμοποίησέ το μόνο με dummy data, test accounts ή ξεκάθαρες permission-based επιδείξεις. Δεν παρουσιάζεται ως εργαλείο για κλοπή πραγματικών λογαριασμών, private credentials, cookies, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** Το training output πρέπει να μένει μέσα στον δικό σου local lab φάκελο: `/storage/emulated/0/Download/Login Stealer/`. Χρησιμοποίησε μόνο dummy data, test accounts ή ξεκάθαρες permission-based επιδείξεις.

</details>

<details>
<summary>Widget Maker.py</summary>


**Περιγραφή:** Το DedSec Widget Maker είναι no-root helper για Termux που δημιουργεί Android home-screen launchers για scripts του DedSec Project μέσω Termux:Widget. Σαρώνει αναδρομικά το Termux home, το shared storage και συνηθισμένους φακέλους του κινητού για DedSec, sponsor, exclusive και σχετικά Python scripts, μαζί με scripts μέσα σε κάθε προσβάσιμο φάκελο και υποφάκελο. Μετά δημιουργεί managed shortcuts στο ~/.shortcuts. Κάθε widget ανοίγει μικρό menu με Run, Show Script Path και Exit, ελέγχει το Python αρχείο πριν το τρέξει, κρατά manifest στο ~/.dedsec_widget_maker/ και μπορεί να κάνει update ή delete όλα τα managed widgets όταν αλλάζει η συλλογή των scripts σου.

**Τοποθεσία Αποθήκευσης:** Τα managed widget launchers δημιουργούνται στο: ~/.shortcuts/ | Το state και το manifest αποθηκεύονται στο: ~/.dedsec_widget_maker/manifest.json. Τα αρχικά scripts δεν μετακινούνται· κάθε widget δείχνει πίσω στο detected source file.

</details>

<details>
<summary>Kraken Trader.py</summary>


**Περιγραφή:** Το Kraken Trader.py είναι Termux trading research και portfolio assistant για το Kraken API. Ξεκινά σε paper mode από προεπιλογή, εμφανίζει risk disclaimer με countdown 10 δευτερολέπτων, αποθηκεύει τα πάντα στο ~/Kraken Trader/ και χρησιμοποιεί numbered menus για pair analysis, market scanning, dashboards, Sage-style strategy labs, advanced tools, beginner guides, risk/reward calculators, backtests, DCA και grid tools, paper wallet trading, paper bot loops, Kraken account tools, live order menus, order management, watchlists, crypto μαζί με stock/ETF monitoring, reports, journals, logs, mode switching, diagnostics και settings. Είναι φτιαγμένο για εκπαίδευση, οργάνωση και πιο ασφαλές paper testing· δεν είναι financial advice και δεν εγγυάται κέρδος.

**Τοποθεσία Αποθήκευσης:** Κύριος φάκελος: ~/Kraken Trader/ | Config, paper wallet, watchlists, presets, alerts, baskets, DCA/grid assists, webhook logs, forward tests, reports, cache, journals, trade logs και error logs αποθηκεύονται μέσα σε αυτόν. Προαιρετικά report copies μπορούν να αποθηκευτούν στα Downloads αν ενεργοποιηθεί αυτή η επιλογή.

</details>

<details>
<summary>Noob Hacker.py</summary>


**Περιγραφή:** Το Noob Hacker.py είναι ασφαλές offline terminal learning game για Termux που μαθαίνει σε απόλυτους αρχάριους προγραμματισμό, βασικά Python, συνήθειες Termux/Bash, debugging, local-only cybersecurity thinking, defender workflows, report writing, projects, quizzes και playable practice games. Είναι φτιαγμένο ως ένα μόνο Python script, λειτουργεί χωρίς root, κρατά την εξάσκηση σε φανταστικά/local labs, περιλαμβάνει English και Greek εκδόσεις, υποστηρίζει self-tests, save migration, progress tracking και πολλά beginner-friendly μαθήματα που οδηγούν κάποιον από μηδενική γνώση σε πρακτικές ασφαλείς δεξιότητες. Δεν επιτίθεται σε πραγματικούς στόχους, δεν σαρώνει το internet, δεν κλέβει λογαριασμούς και δεν μαθαίνει malware.

**Τοποθεσία Αποθήκευσης:** Κύριος φάκελος: ~/Noob Hacker/ | Save file: ~/Noob Hacker/save.json | Mission log: ~/Noob Hacker/mission_log.txt | CTF labs: ~/Noob Hacker/CTF_Labs/ | Exports: ~/Noob Hacker/Exports/

</details>


<a id="greek-butsystem"></a>

<h2>ButSystem.py (Αποκλειστικό)</h2>


Το **ButSystem.py** είναι ένα self-hosted, **local-first** private workspace που τρέχει στη δική σου συσκευή μέσω Termux και ανοίγει σε browser. Συγκεντρώνει account access, επικοινωνία, αρχεία, profiles, investigation-style records και διαχείριση μέσα σε ένα interface, αντί να τα χωρίζει σε διαφορετικά scripts.

Περιλαμβάνει αρχικό creator/admin setup, έγκριση signup requests, approved-device requests, remembered-device login, προαιρετικό 2FA με security questions και password recovery, direct messages, group chats, discussion room, stories, browser audio/video calls όπου υποστηρίζονται, προαιρετικό live-location sharing, profiles, news, reports, appearance και security settings, καθώς και private file vault με διαχείριση φακέλων, previews, downloads, διαγραφή και chunked uploads για μεγαλύτερα αρχεία.

Το **Profiler** υποστηρίζει locally stored κρυπτογραφημένα text records, attachments, search, import και export, συνδυασμό επιλεγμένων records και bounty controls όπου είναι ενεργά. Το ButSystem παρέχει επίσης chat PIN locks, unread, delivery και read state, online presence, διαχείριση χρηστών και συσκευών, privacy pause, security logs, το ενσωματωμένο Face Detector και επιλογές πρόσβασης μέσω local network, Cloudflare ή Tor. Τα binary attachments παραμένουν τοπικά στους φακέλους δεδομένων του ButSystem, ενώ τα sensitive text fields χρησιμοποιούν το ενσωματωμένο encryption layer.

**Τοποθεσία Αποθήκευσης:** `Κύρια persistent data: /storage/emulated/0/Homework/ButSystem/ (διαθέσιμα επίσης ως ~/storage/shared/Homework/ButSystem/) | Fallback: ~/Homework/ButSystem/ | Legacy data που μεταφέρονται από: ~/ButSystem/ | Face Detector captures: Downloads/ButSystem/Face Detector/ | Tor runtime data: ~/.ButSystem_tor/`

Να χρησιμοποιείται μόνο σε συστήματα που σου ανήκουν ή για τα οποία έχεις ρητή άδεια.


</details>

<a id="greek-contact"></a>

<details>
<summary><strong>Επικοινωνία και Συντελεστές</strong></summary>


### Επικοινωνία

Για ερωτήσεις, υποστήριξη ή γενικές πληροφορίες, μπορείς να συνδεθείς με το DedSec Project μέσα από τα παρακάτω επίσημα κανάλια:

* **Κύριο Website:** [https://ded-sec.space](https://ded-sec.space)
* **Κύριο Repository του DedSec Project:** [https://github.com/dedsec1121fk/DedSec](https://github.com/dedsec1121fk/DedSec)
* **Εφεδρικό Website:** [https://ded-sec.online](https://ded-sec.online)
* **Εφεδρικό Repository του DedSec Project:** [https://github.com/sal-scar/DedSec](https://github.com/sal-scar/DedSec)
* **WhatsApp:** [+37257263676](https://wa.me/37257263676)
* **Telegram:** [@dedsecproject](https://t.me/dedsecproject)
* **Discord Server:** [https://discord.gg/fcAuYS4JEv](https://discord.gg/fcAuYS4JEv)

### Συντελεστές

* **Creator:** dedsec1121fk
* **Contributors:** gr3ysec
* **Art Artists:** Christina Chatzidimitriou, 3A
* **Legal Documents:** Lampros Spyrou
* **Discord Server Maintenance:** Talha
* **Past Help:** Sal Scar, lamprouil, UKI_hunter

</details>

<a id="greek-disclaimer"></a>

<details>
<summary><strong>Αποποίηση Ευθύνης και Όροι Χρήσης</strong></summary>


> **ΠΑΡΑΚΑΛΩ ΔΙΑΒΑΣΕ ΠΡΟΣΕΚΤΙΚΑ ΠΡΙΝ ΣΥΝΕΧΙΣΕΙΣ.**

Αυτό το project, μαζί με όλα τα σχετικά εργαλεία, scripts και έγγραφα, παρέχεται αυστηρά για **εκπαιδευτικούς, ερευνητικούς και ethical security testing σκοπούς**. Προορίζεται να χρησιμοποιείται μόνο σε ελεγχόμενα και εξουσιοδοτημένα περιβάλλοντα από χρήστες που έχουν λάβει ρητή άδεια από τους ιδιοκτήτες των συστημάτων που δοκιμάζουν.

1. **Ανάληψη Κινδύνου και Ευθύνης:** Είσαι αποκλειστικά υπεύθυνος για τις πράξεις σου και για οποιεσδήποτε συνέπειες μπορεί να προκύψουν από τη χρήση ή την κακή χρήση αυτού του λογισμικού.
2. **Απαγορευμένες Δραστηριότητες:** Οποιαδήποτε μη εξουσιοδοτημένη ή κακόβουλη δραστηριότητα απαγορεύεται αυστηρά.
3. **Καμία Εγγύηση:** Το λογισμικό παρέχεται **ΩΣ ΕΧΕΙ** χωρίς εγγυήσεις.
4. **Περιορισμός Ευθύνης:** Οι δημιουργοί, οι contributors και οι διανομείς δεν φέρουν ευθύνη για απαιτήσεις, ζημιές ή απώλειες που προκύπτουν από το λογισμικό ή τη χρήση του.

</details>
