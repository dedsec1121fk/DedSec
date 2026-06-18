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

<details>
<summary><strong>Table of Contents</strong></summary>


* [How To Install And Setup The DedSec Project](#how-to-install-and-setup-the-dedsec-project)
* [Website Help Paths](#website-help-paths)
* [Settings & Configuration](#settings--configuration)
* [Explore The Toolkit](#explore-the-toolkit)
* [Developer Base](#developer-base)
* [Network Tools](#network-tools)
* [Personal Information Capture](#personal-information-capture-educational-use-only)
* [Fake Pages](#fake-pages-educational-use-only)
* [Games](#games)
* [Other Tools](#other-tools)
* [No Category](#no-category)
* [Sponsors-Only](#sponsors-only)
* [ButSystem.py (Exclusive)](#butsystempy-exclusive)
* [Contact Us & Credits](#contact-us--credits)
* [Disclaimer & Terms of Use](#disclaimer--terms-of-use)

</details>

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
- [Assistance](https://ded-sec.space/assistance.html) — website path: `assistance.html`

Then download our free e-book:

- [Master Termux In 7 Days](https://ded-sec.space/Assets/Master%20Termux%20In%207%20Days%20English.pdf) — website path: `Assets/Master Termux In 7 Days English.pdf`

Check our exclusive ButSystem.py and become a real detective:

- [ButSystem.py (Exclusive)](https://ded-sec.space/Pages/butsystem-exclusive.html) — website path: `Pages/butsystem-exclusive.html`

If Termux or DedSec breaks, open Assistance first. If you need anything custom-made or direct help, check our Store.

- [Store](https://ded-sec.space/Pages/store.html) — website path: `Pages/store.html`
- [Assistance](https://ded-sec.space/assistance.html) — website path: `assistance.html`

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
- **Access Sponsors-Only Scripts:** checks whether GitHub is connected in Termux, asks the user to connect GitHub if needed, verifies sponsor access, and downloads or replaces the local Sponsors-Only folder when access is confirmed. The $3 tier includes the current sponsor scripts, while the $9 tier includes all $3 scripts plus Widget Maker.py, Kraken Trader.py, and Noob Hacker.py. If the account does not have access, it returns the user to the settings menu without downloading anything.
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

This option is for sponsors who have access to the tier-appropriate private sponsor repository. It first checks whether GitHub is connected. If GitHub is not connected, it asks whether to connect now and follows the same GitHub CLI login flow used by the GitHub stats system. After a successful connection, it checks repository access and downloads the Sponsors-Only scripts into Termux home storage. The $3 tier contains the existing sponsor scripts. The $9 tier contains every $3 script plus Widget Maker.py, Kraken Trader.py, and Noob Hacker.py. If an older local copy exists, it is replaced only after access is confirmed.

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
- **Games:** 5 tools
- **Personal Information Capture:** 17 tools
- **Social Media / Fake Pages:** 25 tools
- **No Category:** 3 tools
- **Sponsors-Only:** 5 tools in the $3 tier / 8 tools in the $9 tier

**Total listed on tools page:** 83 tools

---
<a id="developer-base"></a>

<h2>Developer Base</h2>


<details>
<summary>File Converter</summary>


**Description:** A powerful file converter supporting 40+ formats. Organizes Downloads. Advanced interactive file converter for Termux using curses interface. Supports 40 different file formats across images, documents, audio, video, and archives. Features automatic dependency installation, organized folder structure, and comprehensive conversion capabilities. Built for Termux with clear prompts and organized outputs.

Problem it solved for me: my phone kept receiving files in the wrong format. Example: converting an image, document, audio file, or archive from Downloads into something I could actually open, share, or use without touching a PC.

**Save Location:** ~/storage/downloads/File Converter/

</details>

<details>
<summary>File Type Checker</summary>


**Description:** Advanced file analysis and security scanner that detects file types, extracts metadata, calculates cryptographic hashes, and identifies potential threats. Features magic byte detection, entropy analysis, steganography detection, virus scanning via VirusTotal API, and automatic quarantine of suspicious files. Supports analysis of files up to 50GB. Built for Termux with clear prompts and organized outputs.

Problem it solved for me: I did not want to trust a file just because its name looked normal. Example: checking a ZIP, APK, image, or script from Downloads before keeping it, sharing it, or running it in Termux.

**Save Location:** Scan folder: ~/Downloads/File Type Checker/ | Quarantined files: .dangerous extension

</details>

<details>
<summary>Mobile Desktop</summary>


**Description:** Termux Linux Desktop Manager (no root): sets up a proot-distro desktop environment with VNC/X11 options and a built-in program manager for install/update/remove. Built for Termux with clear prompts and organized outputs.

Problem it solved for me: working only from a phone felt too small for serious work. Example: opening a desktop-style Linux workspace from Android when I needed a bigger environment for files, tools, and project testing.

**Save Location:** Scan folders created in current directory (scan_[target]_[date])

</details>

<details>
<summary>Mobile Developer Setup</summary>


**Description:** Automates a mobile web-dev environment in Termux: installs common dev tools, configures paths, and provides quick-start project scaffolding. Built for Termux with clear prompts and organized outputs.

Problem it solved for me: every clean Termux install wasted time with missing packages. Example: after a reinstall or new phone, I could prepare Python, Git, web tools, and project folders without rebuilding everything by memory.

**Save Location:** Scan folders created in current directory (scan_[target]_[date])

</details>

<details>
<summary>Simple Websites Creator</summary>


**Description:** A comprehensive website builder that creates responsive HTML websites with customizable layouts, colors, fonts, and SEO settings. Features include multiple hosting guides, real-time preview, mobile-friendly designs, and professional templates. Perfect for creating portfolios, business sites, or personal blogs directly from your terminal. Built for Termux with clear prompts and organized outputs.

Problem it solved for me: I often needed a quick page before I had time for a full website build. Example: making a small portfolio, tool page, store-style page, or project preview directly from Termux on Android.

**Save Location:** Websites are saved in: ~/storage/downloads/Websites/

</details>

<details>
<summary>Smart Notes</summary>


**Description:** Terminal note-taking app with reminders. Advanced note-taking application with reminder functionality, featuring both TUI (Text User Interface) and CLI support. Includes sophisticated reminder system with due dates, automatic command execution, external editor integration, and comprehensive note organization capabilities. Built for Termux with clear prompts and organized outputs.

Problem it solved for me: I kept losing the exact commands that fixed something. Example: saving the storage-permission fix, an update command, or a project idea with reminders so I could find it again later.

**Save Location:** ~/.smart_notes.json

</details>

<details>
<summary>Dead Man's Switch</summary>


**Description:** Termux emergency/SOS helper built around the I Need Help mode. After first-time setup and clear user confirmations, it can make the dead-mans-switch GitHub repository public, generate a GitHub Pages emergency website, upload organized emergency files, capture available camera photos, microphone recordings, and location updates at adjustable intervals through Termux:API permissions, and send SMS alerts with the website/repository link to configured trusted contacts. It also includes create/update uploads, overwrite sync, visibility controls, legacy repository migration, previous-history backups, logs, and a kill/cleanup option.

Problem solved for me: if something happens to me or I need help fast, I can quickly create a visible SOS-style emergency signal from my phone. The I Need Help mode can publish a shareable GitHub Pages link with location history, media captures, emergency details, and SMS alerts for trusted contacts, so I do not have to explain everything manually in a panic.

**Save Location:** `Local folder: ~/storage/downloads/Dead Man's Switch/ | Settings: ~/.dead_switch_settings.json | Repo: github.com/<you>/dead-mans-switch`

</details>

<details>
<summary>Tree Explorer</summary>


**Description:** File-system explorer for Termux: browse folders, search files, find duplicates by hash, and clean empty directories with safe prompts. Built for Termux with clear prompts and organized outputs.

Problem it solved for me: my Downloads and Scripts folders became a maze. Example: finding an old zip, locating a missing script, spotting duplicate backups, and cleaning empty folders without guessing paths by hand.

**Save Location:** Scan folders created in current directory (scan_[target]_[date])

</details>

<details>
<summary>Devices Finder</summary>


**Description:** Local-network device discovery tool for Termux that works without root. Separates live-host discovery from service scanning to reduce false positives, classifies devices using ports, banners, hostnames, and vendor hints, includes interactive scan profiles and type filters, and can optionally enrich results with mDNS, UPnP, SNMP, and NetBIOS clues. Exports JSON, TXT, CSV, and HTML reports. Built for Termux with clear prompts and organized outputs.

Problem it solved for me: when my Wi-Fi felt slow, I wanted to know what was actually connected. Example: identifying my phone, router, TV, or unknown devices on my own network before troubleshooting.

**Save Location:** Results are saved in: ~/storage/downloads/Devices Finder/ as devices_scan_[timestamp].json/.txt/.csv/.html (falls back to ~/downloads/Devices Finder/ or the current directory)

</details>

<details>
<summary>Free Internet</summary>


**Description:** Local-first browser and secure vault for Termux. It combines multiple search engines, bookmarks, history, saved pages, ad/tracker cleanup, Lite mode, country-based proxy routing with smart/strict/direct modes, optional Tor support, encrypted vault entries powered by OpenSSL, and a built-in full-page website screenshot tool. Built for Termux with clear prompts and organized outputs.

Problem it solved for me: I wanted one light browser workspace inside my phone setup instead of jumping between apps. Example: keeping bookmarks, saved pages, screenshots, private notes, history cleanup, and safer browsing options in one place.

**Save Location:** ~/Free Internet/ (browser/, vault/, browser/saved/, tools/screenshots/)

</details>


<a id="network-tools"></a>

<h2>Network Tools</h2>


<details>
<summary>Bug Hunter</summary>


**Description:** Bug Hunter (no-root) — an authorized web security recon & misconfiguration scanner. Audits security headers and cookie flags, fingerprints technologies, checks DNS (SPF/DMARC/CAA), analyzes TLS/certificate expiry, tests CORS and HTTP methods, finds exposed sensitive files, crawls the site, and analyzes JavaScript for endpoints and leaked secrets. Includes optional directory discovery and Wayback URL recon, plus de-duplicated reports (JSON/CSV/HTML/PDF). Use only on targets you own or have explicit permission to test.

Problem it solved for me: before sharing my own site, I wanted to catch obvious security and setup mistakes. Example: checking headers, SSL, DNS, cookies, and exposed files on a site I own.

**Save Location:** Reports are saved in the output folder (default: bughunter_out/): report.json, report.csv, report.html (and report.pdf if enabled)

</details>

<details>
<summary>Dark</summary>


**Description:** A specialized Dark Web OSINT tool and crawler designed for Tor network analysis. It features automated Tor connectivity, an Ahmia search integration, and a recursive crawler for .onion sites. The tool utilizes a modular plugin system to extract specific data types (Emails, BTC/XMR addresses, PGP keys, Phones) and supports saving snapshots. It offers both a Curses TUI and CLI mode, with results exportable to JSON, CSV, and TXT. Use only on systems you own or have explicit permission to test.

Problem it solved for me: I wanted to understand dark-web OSINT without treating it like a mystery or a toy. Example: safely saving public research notes from allowed sources while keeping the work organized.

**Save Location:** Results are saved in: /sdcard/Download/DarkNet (or ~/DarkNet if storage is inaccessible)

</details>

<details>
<summary>DedSec's Network</summary>


**Description:** An advanced, non-root network toolkit optimized for speed and stability. Features a recursive website downloader with ZIP support, multi-threaded port scanner, internet speed testing, subnet calculator, and extensive OSINT tools (WHOIS, DNS, Reverse IP, Subdomain Enum). Includes web auditing scanners for SQLi, XSS, CMS detection, and SSH brute-forcing. Maintains a local SQLite audit log. Use only on systems you own or have explicit permission to test.

Problem it solved for me: network checks were scattered across too many commands. Example: testing my own local server, checking DNS, measuring speed, downloading a site copy, or reviewing an authorized target from one menu.

**Save Location:** Reports and logs are saved in: ~/DedSec's Network

</details>

<details>
<summary>Digital Footprint Finder</summary>


**Description:** Conservative OSINT username checker built for best practical results with low false-positives. Scans a large site list via packs (core/extended) with optional Sherlock database, using multi-signal scoring (status/redirects, title/meta/canonical/text) and per-domain concurrency limits for stability. Detects anti-bot/JS challenges as POSSIBLE (never falsely FOUND), supports optional search-engine dorking, and can import/export custom site lists. Exports reports to TXT/JSON/CSV and optional HTML. Use only on systems you own or have explicit permission to test.

Problem it solved for me: I wanted to know where my username or project name appears online. Example: checking dedsec1121fk or DedSec Project across public sites before cleaning profiles or updating links.

**Save Location:** Results are saved in: ~/storage/downloads/Digital Footprint Finder/[username]_v12.txt

</details>

<details>
<summary>Connections.py</summary>


**Description:** Secure chat/file-sharing server. Video calls, file sharing (50GB limit). Unified application combining Butterfly Chat and DedSec's Database with single secret key authentication. Provides real-time messaging, file sharing, video calls, and integrated file management. Features 50GB file uploads, WebRTC video calls, cloudflare tunneling, and unified login system. Use only on systems you own or have explicit permission to test.

Problem it solved for me: I wanted a simple private space for chat and files without depending on random services. Example: sharing a big file or project folder between trusted devices through my own temporary server.

**Save Location:** Downloads to `~/Downloads/DedSec's Database`.

</details>

<details>
<summary>Link Shield</summary>


**Description:** Security-focused URL inspector: follows redirects, checks HTTPS/SSL, flags suspicious domains/patterns, and generates a risk report before you open a link. Use only on systems you own or have explicit permission to test.

Problem it solved for me: people send links that look harmless but hide redirects. Example: checking a strange message link before opening it on my phone.

**Save Location:** Scan folders created in current directory (scan_[target]_[date])

</details>

<details>
<summary>Masker</summary>


**Description:** URL helper for creating clean, readable test links and checking redirect behavior in your own workflows. It is presented for organization, demos, and authorized awareness training only, never to disguise harmful links or trick people.

Problem it solved for me: I needed clean test links for awareness demos without confusing long URLs. Example: showing how redirects work in a lesson using my own controlled links.

**Save Location:** N/A (Output to screen).

</details>

<details>
<summary>QR Code Generator</summary>


**Description:** Python-based QR code generator that creates QR codes for URLs and saves them in the Downloads/QR Codes folder. Features automatic dependency installation, user-friendly interface, and error handling for reliable operation. Use only on systems you own or have explicit permission to test.

Problem it solved for me: typing local links from Termux into another device is annoying. Example: generating a QR code for a local server link so I can open it fast from another phone.

**Save Location:** Images are saved to: ~/storage/downloads/QR Codes/

</details>

<details>
<summary>Sod</summary>


**Description:** A comprehensive load testing tool for web applications, featuring multiple testing methods (HTTP, WebSocket, database simulation, file upload, mixed workload), real-time metrics, and auto-dependency installation. Advanced performance testing framework with realistic user behavior simulation, detailed analytics, and system resource monitoring. Use only on systems you own or have explicit permission to test.

Problem it solved for me: I wanted to know if my own web apps could handle real use before sharing them. Example: load-testing a local or owned page with controlled traffic and reports.

**Save Location:** Configuration: load_test_config.json in script directory | Results: Displayed in terminal

</details>

<details>
<summary>Store Scrapper</summary>


**Description:** Single-file Python store scraper for Termux that works without root. Tries multiple ways to discover categories and products across regular HTML pages and many JS-style stores by reading HTML, JSON-LD, embedded JSON, sitemaps, Shopify endpoints, WooCommerce APIs, generic product cards, breadcrumbs, OpenGraph/meta tags, and internal links. Saves while running, starts full product scraping the moment each product is found, shows live terminal status, uses Enter as the default for prompts, and organizes results into store/category/product folders with downloaded images. Use only on systems you own or have explicit permission to test.

Problem it solved for me: product research from a phone gets messy fast. Example: pulling categories, products, images, and prices from a store into organized folders for comparison.

**Save Location:** `Creates folders in: ~/storage/downloads/Store Scrapper/<Store>/<Category>/<Product>/ (product folders can include FOUND.txt, metadata.json, summary.txt, description.txt, images/, images.json, plus discovery/state files).`

</details>


<a id="personal-information-capture-educational-use-only"></a>

<h2>Personal Information Capture (Educational Use Only)</h2>


These scripts are training simulations intended to help users understand how deceptive personal-data collection pages may be presented, so they can better recognize and defend against them in controlled environments.

<details>
<summary>Fake Back Camera Page</summary>


**Description:** Fake Back Camera Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Back Camera. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

Problem it solved for me: people often miss the risk behind camera permission from the back camera. Example: using a dummy consent-based demo to show how a fake “scan this” page can request camera access before a beginner thinks about why it needs it, without collecting real private data.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Back Camera Video Page</summary>


**Description:** Fake Back Camera Video Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Back Camera Video. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

Problem it solved for me: people often miss the risk behind video-recording permission from the back camera. Example: using a dummy consent-based demo to show how a page can make recording feel like a normal verification step, without collecting real private data.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Card Details Page</summary>


**Description:** Fake Card Details Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Card Details. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

Problem it solved for me: people often miss the risk behind card-detail forms. Example: using a dummy consent-based demo to show how a fake checkout can ask for card details before anything real is being bought, without collecting real private data.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Chrome Verification Page</summary>


**Description:** Fake Chrome Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Chrome Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

Problem it solved for me: people often miss the risk behind fake browser verification. Example: using a dummy consent-based demo to show how a page can pretend Chrome needs one more check to make people obey the prompt, without collecting real private data.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Data Grabber Page</summary>


**Description:** Fake Data Grabber Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Data Grabber. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

Problem it solved for me: people often miss the risk behind overreaching data forms. Example: using a dummy consent-based demo to show how a simple “continue” form can ask for too much private information, without collecting real private data.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Discord Verification Page</summary>


**Description:** Fake Discord Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Discord Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

Problem it solved for me: people often miss the risk behind Discord verification tricks. Example: using a dummy consent-based demo to show how a fake server check can pressure someone to type login details, without collecting real private data.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Facebook Verification Page</summary>


**Description:** Fake Facebook Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Facebook Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

Problem it solved for me: people often miss the risk behind Facebook verification tricks. Example: using a dummy consent-based demo to show how a page can copy the feeling of a normal Facebook security check, without collecting real private data.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Front Camera Page</summary>


**Description:** Fake Front Camera Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Front Camera. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

Problem it solved for me: people often miss the risk behind front-camera permission. Example: using a dummy consent-based demo to show how a “selfie verification” prompt can hide what access is being granted, without collecting real private data.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Front Camera Video Page</summary>


**Description:** Fake Front Camera Video Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Front Camera Video. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

Problem it solved for me: people often miss the risk behind front-camera video recording. Example: using a dummy consent-based demo to show how a fake live check can turn video recording into a casual click, without collecting real private data.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Google Location Page</summary>


**Description:** Fake Google Location Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Google Location. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

Problem it solved for me: people often miss the risk behind Google-style location prompts. Example: using a dummy consent-based demo to show how a familiar logo can make a location request feel more trustworthy than it is, without collecting real private data.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Instagram Verification Page</summary>


**Description:** Fake Instagram Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Instagram Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

Problem it solved for me: people often miss the risk behind Instagram verification tricks. Example: using a dummy consent-based demo to show how a fake follower or security page can push someone toward a dummy login box, without collecting real private data.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Location Page</summary>


**Description:** Fake Location Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Location. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

Problem it solved for me: people often miss the risk behind plain location prompts. Example: using a dummy consent-based demo to show how a page can ask for location with a weak excuse like “continue near you”, without collecting real private data.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Microphone Page</summary>


**Description:** Fake Microphone Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Microphone. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

Problem it solved for me: people often miss the risk behind microphone permission. Example: using a dummy consent-based demo to show how a fake voice check can make microphone access look harmless, without collecting real private data.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake OnlyFans Verification Page</summary>


**Description:** Fake OnlyFans Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around OnlyFans Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

Problem it solved for me: people often miss the risk behind OnlyFans verification tricks. Example: using a dummy consent-based demo to show how curiosity can make people ignore what a verification form is asking for, without collecting real private data.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Steam Verification Page</summary>


**Description:** Fake Steam Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Steam Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

Problem it solved for me: people often miss the risk behind Steam verification tricks. Example: using a dummy consent-based demo to show how a fake game-reward page can make login prompts look normal, without collecting real private data.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Twitch Verification Page</summary>


**Description:** Fake Twitch Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Twitch Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

Problem it solved for me: people often miss the risk behind Twitch verification tricks. Example: using a dummy consent-based demo to show how a fake streamer reward can make people click before checking the domain, without collecting real private data.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake YouTube Verification Page</summary>


**Description:** Fake YouTube Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around YouTube Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

Problem it solved for me: people often miss the risk behind YouTube verification tricks. Example: using a dummy consent-based demo to show how a fake channel or subscriber check can make a login box feel official, without collecting real private data.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>


<a id="fake-pages-educational-use-only"></a>

<h2>Fake Pages (Educational Use Only)</h2>


These scripts are educational simulations intended to help users recognize social-engineering patterns, fake reward pages, fake verification flows, and imitation brand pages often used to pressure people into unsafe actions.

<details>
<summary>Fake Apple iCloud Page</summary>


**Description:** Fake Apple iCloud Page is a mock phishing-awareness page for teaching how fake Apple iCloud offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on iCloud storage or locked-account warnings so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Discord Nitro Page</summary>


**Description:** Fake Discord Nitro Page is a mock phishing-awareness page for teaching how fake Discord Nitro offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on free Nitro offers so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Epic Games Page</summary>


**Description:** Fake Epic Games Page is a mock phishing-awareness page for teaching how fake Epic Games offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on free game or skin offers so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Facebook Friends Page</summary>


**Description:** Fake Facebook Friends Page is a mock phishing-awareness page for teaching how fake Facebook Friends offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on friend or profile-view promises so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Free Robux Page</summary>


**Description:** Fake Free Robux Page is a mock phishing-awareness page for teaching how fake Free Robux offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on free Robux promises so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake GitHub Pro Page</summary>


**Description:** Fake GitHub Pro Page is a mock phishing-awareness page for teaching how fake GitHub Pro offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on free GitHub Pro promises so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Google Free Money Page</summary>


**Description:** Fake Google Free Money Page is a mock phishing-awareness page for teaching how fake Google Free Money offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on fake Google reward messages so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Instagram Followers Page</summary>


**Description:** Fake Instagram Followers Page is a mock phishing-awareness page for teaching how fake Instagram Followers offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on free follower promises so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake MetaMask Page</summary>


**Description:** Fake MetaMask Page is a mock phishing-awareness page for teaching how fake MetaMask offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on wallet recovery or seed-phrase traps so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Microsoft 365 Page</summary>


**Description:** Fake Microsoft 365 Page is a mock phishing-awareness page for teaching how fake Microsoft 365 offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on fake Office renewal warnings so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake OnlyFans Page</summary>


**Description:** Fake OnlyFans Page is a mock phishing-awareness page for teaching how fake OnlyFans offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on curiosity-based login traps so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake PayPal Page</summary>


**Description:** Fake PayPal Page is a mock phishing-awareness page for teaching how fake PayPal offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on payment or refund warnings so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Pinterest Pro Page</summary>


**Description:** Fake Pinterest Pro Page is a mock phishing-awareness page for teaching how fake Pinterest Pro offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on fake creator upgrade offers so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake PlayStation Network Page</summary>


**Description:** Fake PlayStation Network Page is a mock phishing-awareness page for teaching how fake PlayStation Network offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on free PSN credit or account-warning pages so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Reddit Karma Page</summary>


**Description:** Fake Reddit Karma Page is a mock phishing-awareness page for teaching how fake Reddit Karma offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on karma boost promises so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Snapchat Friends Page</summary>


**Description:** Fake Snapchat Friends Page is a mock phishing-awareness page for teaching how fake Snapchat Friends offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on friend-view or unlock promises so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Steam Games Page</summary>


**Description:** Fake Steam Games Page is a mock phishing-awareness page for teaching how fake Steam Games offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on free Steam game claims so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Steam Wallet Page</summary>


**Description:** Fake Steam Wallet Page is a mock phishing-awareness page for teaching how fake Steam Wallet offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on free wallet balance claims so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake TikTok Followers Page</summary>


**Description:** Fake TikTok Followers Page is a mock phishing-awareness page for teaching how fake TikTok Followers offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on follower and view boost promises so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Trust Wallet Page</summary>


**Description:** Fake Trust Wallet Page is a mock phishing-awareness page for teaching how fake Trust Wallet offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on wallet recovery traps so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Twitch Subs Page</summary>


**Description:** Fake Twitch Subs Page is a mock phishing-awareness page for teaching how fake Twitch Subs offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on free subscription rewards so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Twitter Followers Page</summary>


**Description:** Fake Twitter Followers Page is a mock phishing-awareness page for teaching how fake Twitter Followers offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on fake follower growth offers so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake What's Up Dude Page</summary>


**Description:** Fake What's Up Dude Page is a mock phishing-awareness page for teaching how fake What's Up Dude offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on random friendly messages that hide forms so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake Xbox Live Page</summary>


**Description:** Fake Xbox Live Page is a mock phishing-awareness page for teaching how fake Xbox Live offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on free Xbox credit or login warnings so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>

<details>
<summary>Fake YouTube Subscribers Page</summary>


**Description:** Fake YouTube Subscribers Page is a mock phishing-awareness page for teaching how fake YouTube Subscribers offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

Problem it solved for me: scams work because the bait looks normal. Example: showing a dummy page based on subscriber boost promises so someone learns to check the domain, the request, and the promise before typing anything real.

**Save Location:** Training output should stay local to your own lab folder. Use dummy data only and never collect real private information.

</details>


<a id="games"></a>

<h2>Games</h2>


<details>
<summary>Buzz</summary>


**Description:** A text-only trivia party game for Termux with a fixed built-in database of 15,000 questions (no runtime generation). Supports 1–2 players (pass-and-play), multiple round types, difficulty filtering (All/Easy/Medium/Hard), profiles, settings, and highscores. Lightweight terminal game with quick controls and replay value.

Problem it solved for me: I wanted a no-internet game that still teaches something. Example: playing quick trivia during a break, in a waiting room, or when mobile data is weak.

**Save Location:** ~/Buzz/ (data/ for DB, profiles, settings, highscores)

</details>

<details>
<summary>CTF God</summary>


**Description:** Full‑screen Curses CTF game for Termux with story mode, missions, daily challenges, random boss levels, hint shop economy, achievements & ranks, challenge pack import/export, tournament mode, and anti‑cheat/integrity checks. Includes a built‑in level editor. Lightweight terminal game with quick controls and replay value.

Problem it solved for me: I wanted cybersecurity practice without touching real targets. Example: solving terminal CTF missions, hints, and boss levels inside a safe game environment.

**Save Location:** `User workspaces & challenge files: /storage/emulated/0/Download/CTF God/<username>/files (fallback: ~/storage/downloads/CTF God/...). Game state & packs: ~/.ctf_god/ (state.json, packs/, custom.json).`

</details>

<details>
<summary>Detective</summary>


**Description:** A story-driven Terminal detective game for Termux with an expanded fixed case library, richer lore dossiers, district rumors, side stories, and bonus story threads. Track evidence, interrogate suspects, review suspect rosters, build an ASCII case board and timeline, and manage progress with 3 save slots plus autosave. Includes 4 difficulties, note/evidence tracking, checkpoint hints, and quick commands like :help, :guide, :lore, :suspects, :board, :timeline, :hint, and :save.

Problem it solved for me: I wanted a story game that trains attention instead of just killing time. Example: reading clues, building a case board, and checking contradictions while playing from Termux.

**Save Location:** ~/Detective/ (player profile, slots, autosave, and case progress)

</details>

<details>
<summary>Tamagotchi</summary>


**Description:** A fully featured terminal pet game. Feed, play, clean, and train your pet. Don't let it die. Advanced virtual pet simulation game with comprehensive pet management system. Features include pet evolution through life stages (Egg, Child, Teen, Adult, Elder), personality traits, skill development, mini-games, job system, and legacy retirement. Includes detailed statistics tracking. Lightweight terminal game with quick controls and replay value.

Problem it solved for me: I wanted a tiny daily game that runs even on a simple phone. Example: feeding, training, and checking a terminal pet for five minutes without opening a heavy app.

**Save Location:** ~/.termux_tamagotchi_v8.json

</details>

<details>
<summary>Terminal Arcade</summary>


**Description:** All-in-one terminal arcade pack with multiple mini-games in a single script. Saves data in ~/Terminal Arcade/ and runs smoothly on Termux/Linux terminals. Lightweight terminal game with quick controls and replay value.

Problem it solved for me: I did not want ten different small game files everywhere. Example: opening one arcade pack from Termux when I want a quick Snake-style or mini-game break.

**Save Location:** Scan folders created in current directory (scan_[target]_[date])

</details>


<a id="other-tools"></a>

<h2>Other Tools</h2>


<details>
<summary>Android App Launcher</summary>


**Description:** A utility to manage Android apps directly from the terminal. It can launch apps, extract APK files, uninstall apps, and analyze security permissions. Advanced Android application management and security analysis tool. Features include app launching, APK extraction, permission inspection, security analysis, and tracker detection. Includes comprehensive security reporting for installed applications. Built for Termux with clear prompts and organized outputs.

Problem it solved for me: switching between terminal work and Android apps slowed everything down. Example: launching, checking, or extracting an app directly from Termux while building or testing.

**Save Location:** Extracted APKs: ~/storage/shared/Download/Extracted APK's | Reports: ~/storage/shared/Download/App_Security_Reports

</details>

<details>
<summary>Loading Screen</summary>


**Description:** Customize your Termux startup with ASCII art loading screens. Supports custom art, delay timers, and automated setup/cleanup for one-time display. Built for Termux with clear prompts and organized outputs.

Problem it solved for me: scripts felt unfinished when they opened with plain terminal chaos. Example: adding a clean loading screen so a tool feels like part of one project instead of random code.

**Save Location:** Modifies `.bash_profile` and `bash.bashrc`.

</details>

<details>
<summary>Password Master</summary>


**Description:** Comprehensive password management suite featuring encrypted vault storage, password generation, strength analysis, and improvement tools. Includes AES-256 encrypted vault with master password protection, random password generator, passphrase generator, password strength analyzer, and password improvement suggestions. Features clipboard integration. Built for Termux with clear prompts and organized outputs.

Problem it solved for me: project passwords, test logins, and tokens were too easy to lose. Example: keeping local test credentials organized instead of hiding them in random notes.

**Save Location:** Vault file: my_vault.enc in script directory | Backups: ~/Download/Password Master Backup

</details>

<details>
<summary>Termux Backup Restore</summary>


**Description:** Backup & restore for Termux: creates a zipped backup of your Termux files to Downloads and can restore them with integrity checks. Built for Termux with clear prompts and organized outputs.

Problem it solved for me: one phone problem could destroy days of Termux work. Example: backing up scripts and data before updates, then restoring them after reinstall or storage trouble.

**Save Location:** Scan folders created in current directory (scan_[target]_[date])

</details>

<details>
<summary>Termux Repair Wizard</summary>


**Description:** Troubleshooting wizard for Termux: checks common issues (mirrors, packages, permissions), suggests fixes, and runs safe repair commands step-by-step. Built for Termux with clear prompts and organized outputs.

Problem it solved for me: random fix commands can make Termux worse. Example: using a guided repair path for storage, package, Python, pip, and permission problems instead of guessing.

**Save Location:** Scan folders created in current directory (scan_[target]_[date])

</details>


<a id="no-category"></a>

<h2>No Category</h2>


<details>
<summary>Extra Content</summary>


**Description:** Extra bonus content hub: quick access to additional resources, templates, and optional add-ons included in the DedSec toolkit. Built for Termux with clear prompts and organized outputs.

Problem it solved for me: extra resources were scattered and easy to forget. Example: opening one hub for bonus templates, add-ons, and project extras instead of searching folders manually.

**Save Location:** Scan folders created in current directory (scan_[target]_[date])

</details>

<details>
<summary>Settings.py</summary>


**Description:** Settings.py is the central control panel for the DedSec Project. It shows project and device information; updates the project from the main or backup source; refreshes Termux packages and Python modules; checks and downloads Sponsors-Only scripts through a connected GitHub account; creates a DedSec Project backup in Downloads; changes the Termux prompt; connects or disconnects GitHub; shows GitHub stats; syncs the prompt with the GitHub username; scans Termux usage stats; manages optional VPN and Tor utilities; switches between List, Grid, Choose By Number, and DedSec OS menu styles; controls menu auto-start; saves the English or Greek language choice; displays credits; and safely uninstalls the project. DedSec OS adds a browser-based local workspace with a file browser, safe text editor, terminal view, session manager, DedSec apps launcher, Linux package store actions, notifications, fullscreen and split-view controls, sidebar controls, wallpaper support, display name settings, terminal color settings, project action buttons, language controls, prompt controls, password login, optional authenticator-style 2FA, and recovery through three security questions. Built for Termux with clear prompts and organized outputs.

Problem it solved for me: DedSec became too big to control from memory. Example: updating sources, refreshing packages, making a backup in Downloads, checking sponsor access, managing GitHub, and switching menu styles from one command center.

**Save Location:** Language config: ~/Language.json | Termux config backup: ~/Termux.zip | Save DedSec Project backup: Downloads

</details>

<details>
<summary>DedSec Market</summary>


**Description:** Curses-based GitHub repository market for Termux that displays projects by project name instead of raw repository name. It fetches README text cleanly, shows releases and issues, supports install/update/delete and launch actions, keeps a watchlist, and stores cache/state for faster reuse. Built for Termux with clear prompts and organized outputs.

Problem it solved for me: I did not want to remember every GitHub repo name and install command. Example: browsing projects by readable name, checking README text, installing, updating, deleting, and launching from one market-style menu.

**Save Location:** `App data: ~/DedSec Market/ (cache/, state.json) | Installed repositories: ~/<repo-name>`

</details>


<a id="sponsors-only"></a>

<h2>Sponsors-Only</h2>


Sponsors-Only access is now split into two GitHub Sponsors tiers:

| Tier | What it includes |
| :--- | :--------------- |
| **$3 Sponsor** | The existing sponsor scripts already listed on the website: Face Detector.py, Face Detector Heavy.py, Face Swap.py, Steganography.py, and AR Terror.py. |
| **$9 Pro Supporter** | Everything from the $3 tier, plus **Widget Maker.py**, **Kraken Trader.py**, and **Noob Hacker.py**. |

**• $3 Sponsor Scripts**


<details>
<summary>Face Detector.py</summary>


**Description:** Local browser-based face analysis tool for Termux that works without root. It uses MediaPipe Face Mesh on the live camera feed, supports both front and back camera, tracks up to 3 faces, draws detailed facial landmark overlays instead of simple boxes, and also lets you upload photos or videos for analysis directly from the interface. It can capture PNG snapshots, record WEBM video, save cropped detected faces separately, and provide both a local network link and an optional Cloudflare public link.

Problem it solved for me: I wanted a real browser camera demo from Termux without root. Example: opening a local link, switching cameras, detecting my own face landmarks, and saving test snapshots from my phone.

**Save Location:** On Termux, captures, recordings, uploaded results, and saved face crops are stored in: ~/storage/downloads/Face Detector/. If Termux storage is unavailable, it falls back to ~/Face Detector/. On non-Termux systems it uses ~/Downloads/Face Detector/, with fallback to ~/Face Detector/. Internal web files, certificates, and helper binaries are stored in ~/.face_detector_studio/.

</details>

<details>
<summary>Face Detector Heavy.py</summary>


**Description:** Expanded heavy-analysis version of the face detector for Termux, built without root. Along with live camera use, front/back camera switching, photo and video uploads, PNG snapshots, WEBM recording, and saved face crops, it raises tracking up to 30 faces and adds TensorFlow COCO-SSD object detection on top of the MediaPipe face mesh pipeline. It shows richer on-screen telemetry such as face count, animal/object detection, pose and gaze estimates, facial proportions, mouth and brow state, asymmetry scoring, and other visual analysis details, while still supporting both a local network link and an optional Cloudflare public link.

Problem it solved for me: I wanted to push the camera tool further for richer demos. Example: testing many faces, object detection, pose hints, and heavier telemetry on a controlled phone/browser setup.

**Save Location:** On Termux, captures, recordings, uploaded results, and saved face crops are stored in: ~/storage/downloads/Face Detector/. If Termux storage is unavailable, it falls back to ~/Face Detector/. On non-Termux systems it uses ~/Downloads/Face Detector/, with fallback to ~/Face Detector/. Internal web files, certificates, and helper binaries are stored in ~/.face_detector_studio/.

</details>

<details>
<summary>Face Swap.py</summary>


**Description:** Local browser-based face swap tool for Termux that works without root. It opens a local camera page, lets you upload a source face image, switch between the front and back camera, and blend the uploaded face over the live camera using MediaPipe Face Mesh. The current version focuses on a smooth face-lock approach: it locks the uploaded face once, follows the live face, moves key feature patches for expressions, includes smoothing, feathering, opacity, blend, and skin-tone matching controls, and can save PNG snapshots from the browser. Use it only with your own images or with clear permission.

Problem it solved for me: I wanted a local phone-friendly face swap demo without installing a heavy app. Example: opening a local link, uploading a test face image, switching cameras, tuning the blend, and saving a PNG result in Downloads.

**Save Location:** On Termux, saved photos are stored in: /storage/emulated/0/Download/Face Swap/ or ~/storage/downloads/Face Swap/, with fallback to ~/Face Swap/. On non-Termux systems it uses ~/Downloads/Face Swap/, with fallback to ~/Face Swap/.

</details>

<details>
<summary>Steganography.py</summary>


**Description:** Password-based steganography suite for Termux. It can generate random black-and-white PNG carrier images, encrypt secret text with a password-derived Fernet key, hide the encrypted text inside PNG images using LSB steganography, and batch-decode hidden messages from all images placed in the Decrypt folder. Extracted messages are automatically saved as separate .txt files, and the script can also optionally clean processed images from the decode folder after scanning.

Problem it solved for me: I wanted to understand hidden-message techniques safely. Example: hiding a harmless test note inside a PNG with a password and then decoding it later from the Decrypt folder.

**Save Location:** Main folder: /storage/emulated/0/Download/Steganography/ | Carrier/output images: /Encrypt | Images to scan for hidden messages: /Decrypt | Extracted text files: /Decrypted Texts

</details>

<details>
<summary>AR Terror.py</summary>


**Description:** Local browser-based AR horror experience for Termux that works without root. It launches a full-screen camera-driven web page where you explore the environment, collect hidden logs into an archive/inventory system, use atmospheric visual and audio effects, switch between front and back camera, and record evidence as WEBM while the experience runs. It can also expose both a local network link and an optional Cloudflare public link.

Problem it solved for me: I wanted to prove Termux can run creative browser experiences too, not only utilities. Example: opening a local AR horror page, using the camera, collecting logs, and recording a short evidence clip.

**Save Location:** On Termux, recorded evidence is saved in: ~/storage/downloads/AR Terror/. If Termux storage is unavailable, it falls back to ~/AR Terror/. On non-Termux systems it uses ~/Downloads/AR Terror/, with fallback to ~/AR Terror/. Internal web files, certificates, and helper binaries are stored in ~/.ar_terror_studio/.

</details>

<details>
<summary>Widget Maker.py</summary>


**Description:** DedSec Widget Maker is a no-root Termux helper that creates Android home-screen launchers for DedSec Project scripts through Termux:Widget. It recursively scans Termux home, shared storage, and common phone folders for DedSec, sponsor, exclusive, and related Python scripts, including scripts inside every accessible folder and subfolder. It then creates managed shortcuts in ~/.shortcuts. Each widget opens a small menu with Run, Show Script Path, and Exit, validates the Python file before launching it, keeps a manifest in ~/.dedsec_widget_maker/, and can update or delete all managed widgets when your script collection changes.

Problem it solved for me: I wanted one-tap Android shortcuts for every DedSec and sponsor script without manually writing Termux:Widget files. Example: scan all project folders, create widgets, refresh them later, and remove only the managed ones when needed.

**Save Location:** Managed widget launchers are created in: ~/.shortcuts/ | State and manifest are stored in: ~/.dedsec_widget_maker/manifest.json. The original scripts are not moved; each widget points back to the detected source file.

</details>

<details>
<summary>Kraken Trader.py</summary>


**Description:** Kraken Trader.py is a Termux trading research and portfolio assistant for the Kraken API. It starts in paper mode by default, shows a 10-second risk disclaimer, stores everything under ~/Kraken Trader/, and uses numbered menus for pair analysis, market scanning, dashboards, Sage-style strategy labs, advanced tools, beginner guides, risk/reward calculators, backtests, DCA and grid tools, paper wallet trading, paper bot loops, Kraken account tools, live order menus, order management, watchlists, crypto plus stock/ETF monitoring, reports, journals, logs, mode switching, diagnostics, and settings. It is built for education, organization, and safer paper testing; it is not financial advice and it does not guarantee profit.

Problem it solved for me: I wanted a single phone-friendly trading lab that keeps real money locked behind warnings while still letting me study markets, test strategies, journal decisions, and practice with paper mode first.

**Save Location:** Main folder: ~/Kraken Trader/ | Config, paper wallet, watchlists, presets, alerts, baskets, DCA/grid assists, webhook logs, forward tests, reports, cache, journals, trade logs, and error logs are stored inside it. Optional report copies can be saved to Downloads if enabled.

</details>

<details>
<summary>Noob Hacker.py</summary>


**Description:** Noob Hacker.py is a safe offline terminal learning game for Termux that teaches absolute beginners programming, Python basics, Termux/Bash habits, debugging, local-only cybersecurity thinking, defender workflows, report writing, projects, quizzes, and playable practice games. It is built as a single Python script, works without root, keeps practice inside fictional/local labs, includes English and Greek versions, supports self-tests, save migration, progress tracking, and many beginner-friendly lessons designed to guide someone from zero knowledge into practical safe skills. It does not attack real targets, scan the internet, steal accounts, or teach malware.

Problem it solved for me: I wanted one serious beginner-friendly learning game that can teach someone from zero without sending them to random unsafe tutorials. Example: open Termux, run one Python file, follow slow lessons, play safe practice games, learn Python/commands/debugging, and build confidence without touching real targets.

**Save Location:** Main folder: ~/Noob Hacker/ | Save file: ~/Noob Hacker/save.json | Mission log: ~/Noob Hacker/mission_log.txt | CTF labs: ~/Noob Hacker/CTF_Labs/ | Exports: ~/Noob Hacker/Exports/

</details>


<a id="butsystempy-exclusive"></a>

<h2>ButSystem.py (Exclusive)</h2>


**ButSystem.py** is a self-hosted, **local-first** workspace that runs on your own device through Termux. It is designed to bring private communication, organized files, access control, and structured profile workflows into one browser interface instead of scattering them across separate scripts and menus.

Rather than being only a chat page, ButSystem combines login and signup flow, user approval, device access control, remembered-device login, optional security-question 2FA, password recovery, direct messages, group chats, discussion space, stories, live-location sharing, file-vault navigation, profile editing, reports, admin controls, and security settings in one place. It also includes the **Profiler** area for encrypted profile entries, export and combine tools, bounty-related management where enabled, chat PIN locks, and the built-in **Face Detector** workflow that fits into the wider ButSystem environment.

In practice, you run the script, open the generated local link, and move through the system with the burger menu. That gives you a cleaner way to switch between chats, groups, calls, files, profile pages, Profiler, reports, settings, and admin tools without leaving the same local-first workspace.

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

<details>
<summary><strong>Περιεχόμενα</strong></summary>


* [Πώς να Εγκαταστήσετε και να Ρυθμίσετε το DedSec Project](#greek-installation)
* [Διαδρομές Βοήθειας Ιστοσελίδας](#greek-website-help)
* [Ρυθμίσεις και Παραμετροποίηση](#greek-settings)
* [Εξερευνήστε την Εργαλειοθήκη](#greek-toolkit)
* [Βάση Προγραμματιστή](#greek-developer-base)
* [Εργαλεία Δικτύου](#greek-network-tools)
* [Συλλογή Προσωπικών Πληροφοριών](#greek-personal-information-capture)
* [Ψεύτικες Σελίδες](#greek-fake-pages)
* [Παιχνίδια](#greek-games)
* [Άλλα Εργαλεία](#greek-other-tools)
* [Χωρίς Κατηγορία](#greek-no-category)
* [Μόνο για Χορηγούς](#greek-sponsors-only)
* [ButSystem.py (Αποκλειστικό)](#greek-butsystem)
* [Επικοινωνία και Συντελεστές](#greek-contact)
* [Αποποίηση Ευθύνης και Όροι Χρήσης](#greek-disclaimer)

</details>

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
- [Βοήθεια](https://ded-sec.space/assistance.html) — website path: `assistance.html`

Μετά κατέβασε το δωρεάν e-book μας:

- [Master Termux In 7 Days](https://ded-sec.space/Assets/Master%20Termux%20In%207%20Days%20Greek.pdf) — website path: `Assets/Master Termux In 7 Days Greek.pdf`

Δες το αποκλειστικό ButSystem.py και γίνε πραγματικός detective:

- [ButSystem.py (Αποκλειστικό)](https://ded-sec.space/Pages/butsystem-exclusive.html) — website path: `Pages/butsystem-exclusive.html`

Αν χαλάσει το Termux ή το DedSec, άνοιξε πρώτα τη Βοήθεια. Αν χρειάζεσαι κάτι custom-made ή άμεση βοήθεια, δες το Store μας.

- [Κατάστημα](https://ded-sec.space/Pages/store.html) — website path: `Pages/store.html`
- [Βοήθεια](https://ded-sec.space/assistance.html) — website path: `assistance.html`

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
- **Access Sponsors-Only Scripts:** ελέγχει αν το GitHub είναι συνδεδεμένο στο Termux, ζητά σύνδεση GitHub αν χρειάζεται, ελέγχει sponsor access και κατεβάζει ή αντικαθιστά τον τοπικό Sponsors-Only φάκελο όταν επιβεβαιωθεί η πρόσβαση. Το tier των $3 περιλαμβάνει τα υπάρχοντα sponsor scripts, ενώ το tier των $9 περιλαμβάνει όλα τα scripts των $3 μαζί με τα Widget Maker.py, Kraken Trader.py και Noob Hacker.py. Αν ο λογαριασμός δεν έχει πρόσβαση, επιστρέφει στο settings menu χωρίς να κατεβάσει τίποτα.
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

Αυτή η επιλογή είναι για sponsors που έχουν πρόσβαση στο αντίστοιχο private sponsor repository του tier τους. Πρώτα ελέγχει αν το GitHub είναι συνδεδεμένο. Αν δεν είναι, ρωτά αν θέλεις να συνδεθείς τώρα και χρησιμοποιεί την ίδια ροή GitHub CLI login με τα GitHub stats. Μετά από επιτυχημένη σύνδεση, ελέγχει πρόσβαση στο repository και κατεβάζει τα Sponsors-Only scripts στο home storage του Termux. Το tier των $3 περιλαμβάνει τα υπάρχοντα sponsor scripts. Το tier των $9 περιλαμβάνει κάθε script των $3 μαζί με τα Widget Maker.py, Kraken Trader.py και Noob Hacker.py. Αν υπάρχει παλιότερο τοπικό αντίγραφο, αντικαθίσταται μόνο αφού επιβεβαιωθεί η πρόσβαση.

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
- **Games:** 5 εργαλεία
- **Personal Information Capture:** 17 εργαλεία
- **Social Media / Fake Pages:** 25 εργαλεία
- **No Category:** 3 εργαλεία
- **Sponsors-Only:** 5 εργαλεία στο $3 tier / 8 εργαλεία στο $9 tier

**Συνολικά καταχωρημένα στη σελίδα εργαλείων:** 83 εργαλεία

---
<a id="greek-developer-base"></a>

<h2>Βάση Προγραμματιστή</h2>


<details>
<summary>File Converter</summary>


**Περιγραφή:** Ένας ισχυρός μετατροπέας αρχείων που υποστηρίζει 40+ μορφές. Οργανώνει τις Λήψεις. Προηγμένος διαδραστικός μετατροπέας αρχείων για Termux χρησιμοποιώντας διεπαφή curses. Υποστηρίζει 40 διαφορετικές μορφές αρχείων σε εικόνες, έγγραφα, ήχο, βίντεο και αρχεία. Διαθέτει αυτόματη εγκατάσταση εξαρτήσεων, οργανωμένη δομή φακέλων και ολοκληρωμένες δυνατότητες μετατροπής. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

Πρόβλημα που μου έλυσε: το κινητό μου γέμιζε αρχεία σε λάθος format. Παράδειγμα: μετατροπή εικόνας, εγγράφου, ήχου ή archive από τα Downloads σε κάτι που μπορώ να ανοίξω, να στείλω ή να χρησιμοποιήσω χωρίς PC.

**Τοποθεσία Αποθήκευσης:** ~/storage/downloads/File Converter/

</details>

<details>
<summary>File Type Checker</summary>


**Περιγραφή:** Προηγμένος αναλυτής αρχείων και σαρωτής ασφαλείας που εντοπίζει τύπους αρχείων, εξάγει μεταδεδομένα, υπολογίζει κρυπτογραφικά hashes και αναγνωρίζει πιθανές απειλές. Διαθέτει ανίχνευση magic byte, ανάλυση εντροπίας, ανίχνευση steganography, σάρωση ιών μέσω VirusTotal API και αυτόματη καραντίνα ύποπτων αρχείων. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

Πρόβλημα που μου έλυσε: δεν ήθελα να εμπιστεύομαι ένα αρχείο μόνο επειδή το όνομά του φαίνεται φυσιολογικό. Παράδειγμα: έλεγχος ZIP, APK, εικόνας ή script από τα Downloads πριν το κρατήσω, το στείλω ή το τρέξω στο Termux.

**Τοποθεσία Αποθήκευσης:** Φάκελος σάρωσης: ~/Downloads/File Type Checker/ | Αρχεία σε καραντίνα: κατάληξη .dangerous

</details>

<details>
<summary>Mobile Desktop</summary>


**Περιγραφή:** Διαχειριστής Linux Desktop για Termux (χωρίς root): στήνει proot-distro περιβάλλον με επιλογές VNC/X11 και πρόγραμμα διαχείρισης εφαρμογών (install/update/remove). Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

Πρόβλημα που μου έλυσε: η δουλειά μόνο από κινητό ήταν πολύ περιορισμένη για σοβαρή χρήση. Παράδειγμα: άνοιγμα desktop-style Linux χώρου από Android όταν χρειαζόμουν μεγαλύτερο περιβάλλον για αρχεία, εργαλεία και δοκιμές project.

**Τοποθεσία Αποθήκευσης:** Φάκελοι σάρωσης δημιουργούνται στον τρέχοντα κατάλογο

</details>

<details>
<summary>Mobile Developer Setup</summary>


**Περιγραφή:** Αυτοματοποιεί web-dev περιβάλλον σε Termux: εγκαθιστά βασικά εργαλεία, ρυθμίζει paths και δίνει γρήγορο project scaffolding. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

Πρόβλημα που μου έλυσε: κάθε καθαρή εγκατάσταση Termux μου έτρωγε χρόνο με χαμένα packages. Παράδειγμα: μετά από reinstall ή νέο κινητό, μπορώ να στήσω Python, Git, web tools και φακέλους project χωρίς να τα θυμάμαι όλα απ’ έξω.

**Τοποθεσία Αποθήκευσης:** Φάκελοι σάρωσης δημιουργούνται στον τρέχοντα κατάλογο

</details>

<details>
<summary>Simple Websites Creator</summary>


**Περιγραφή:** Ένας ολοκληρωμένος δημιουργός ιστοσελίδων που δημιουργεί ανταποκρινόμενες HTML ιστοσελίδες με προσαρμόσιμη διάταξη, χρώματα, γραμματοσειρές και ρυθμίσεις SEO. Χαρακτηριστικά περιλαμβάνουν πολλαπλούς οδηγούς φιλοξενίας, προεπισκόπηση σε πραγματικό χρόνο, φιλικά για κινητά σχέδια και επαγγελματικά πρότυπα. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

Πρόβλημα που μου έλυσε: πολλές φορές χρειαζόμουν μια γρήγορη σελίδα πριν προλάβω να φτιάξω ολόκληρο website. Παράδειγμα: μικρό portfolio, tool page, store-style page ή preview project απευθείας από Termux στο Android.

**Τοποθεσία Αποθήκευσης:** Οι ιστοσελίδες αποθηκεύονται σε: ~/storage/downloads/Websites/

</details>

<details>
<summary>Smart Notes</summary>


**Περιγραφή:** Εφαρμογή σημειώσεων terminal με υπενθυμίσεις. Προηγμένη εφαρμογή σημειώσεων με λειτουργικότητα υπενθύμισης, που διαθέτει τόσο TUI (Διεπαφή Κειμένου) όσο και υποστήριξη CLI. Περιλαμβάνει εξελιγμένο σύστημα υπενθυμίσεων με ημερομηνίες λήξης, αυτόματη εκτέλεση εντολών, ενσωμάτωση εξωτερικού επεξεργαστή και ολοκληρωμένες δυνατότητες οργάνωσης σημειώσεων. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

Πρόβλημα που μου έλυσε: έχανα τις ακριβείς εντολές που είχαν φτιάξει κάτι. Παράδειγμα: αποθήκευση fix για storage permissions, update command ή ιδέας project με reminders για να τα ξαναβρώ μετά.

**Τοποθεσία Αποθήκευσης:** ~/.smart_notes.json

</details>

<details>
<summary>Dead Man's Switch</summary>


**Περιγραφή:** Emergency/SOS εργαλείο για Termux που βασίζεται στη λειτουργία I Need Help. Μετά το first-time setup και καθαρές επιβεβαιώσεις από τον χρήστη, μπορεί να κάνει public το dead-mans-switch GitHub repository, να δημιουργήσει GitHub Pages emergency website, να ανεβάσει οργανωμένα emergency αρχεία, να τραβήξει διαθέσιμες φωτογραφίες από κάμερες, ηχογραφήσεις μικροφώνου και location updates σε ρυθμιζόμενα χρονικά διαστήματα μέσω Termux:API permissions, και να στείλει SMS alerts με το website/repository link σε configured trusted contacts. Περιλαμβάνει επίσης create/update uploads, overwrite sync, visibility controls, legacy repository migration, previous-history backups, logs και kill/cleanup option.

Πρόβλημα που μου λύνει: αν κάτι μου συμβεί ή χρειαστώ βοήθεια γρήγορα, μπορώ να δημιουργήσω άμεσα ένα ορατό SOS-style emergency signal από το κινητό μου. Το I Need Help μπορεί να δημοσιεύσει shareable GitHub Pages link με ιστορικό τοποθεσίας, media captures, emergency πληροφορίες και SMS alerts για trusted contacts, ώστε να μην χρειάζεται να εξηγήσω τα πάντα χειροκίνητα μέσα στον πανικό.

**Τοποθεσία Αποθήκευσης:** `Τοπικός φάκελος: ~/storage/downloads/Dead Man's Switch/ | Ρυθμίσεις: ~/.dead_switch_settings.json | Repo: github.com/<you>/dead-mans-switch`

</details>

<details>
<summary>Tree Explorer</summary>


**Περιγραφή:** Εξερευνητής αρχείων για Termux: περιήγηση φακέλων, αναζήτηση αρχείων, εύρεση διπλότυπων με hash και καθαρισμός άδειων φακέλων με ασφαλείς επιλογές. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

Πρόβλημα που μου έλυσε: οι φάκελοι Downloads και Scripts έγιναν λαβύρινθος. Παράδειγμα: εύρεση παλιού zip, χαμένου script, διπλών backups και άδειων φακέλων χωρίς να μαντεύω paths χειροκίνητα.

**Τοποθεσία Αποθήκευσης:** Φάκελοι σάρωσης δημιουργούνται στον τρέχοντα κατάλογο

</details>

<details>
<summary>Devices Finder</summary>


**Περιγραφή:** Εργαλείο ανακάλυψης συσκευών τοπικού δικτύου για Termux που λειτουργεί χωρίς root. Διαχωρίζει τον εντοπισμό live hosts από το service scanning για να μειώνει τα false positives, αναγνωρίζει τύπους συσκευών με βάση ports, banners, hostnames και vendor hints, περιλαμβάνει interactive scan profiles και φίλτρα τύπου, και προαιρετικά εμπλουτίζει τα αποτελέσματα με mDNS, UPnP, SNMP και NetBIOS clues. Εξάγει αναφορές JSON, TXT, CSV και HTML. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

Πρόβλημα που μου έλυσε: όταν το Wi-Fi φαινόταν αργό, ήθελα να ξέρω τι είναι όντως συνδεδεμένο. Παράδειγμα: αναγνώριση κινητού, router, TV ή άγνωστων συσκευών στο δικό μου δίκτυο πριν κάνω troubleshooting.

**Τοποθεσία Αποθήκευσης:** Τα αποτελέσματα αποθηκεύονται στο: ~/storage/downloads/Devices Finder/ ως devices_scan_[timestamp].json/.txt/.csv/.html (fallback στο ~/downloads/Devices Finder/ ή στον τρέχοντα κατάλογο)

</details>

<details>
<summary>Free Internet</summary>


**Περιγραφή:** Local-first browser και ασφαλές vault για Termux. Συνδυάζει πολλαπλές μηχανές αναζήτησης, bookmarks, ιστορικό, αποθηκευμένες σελίδες, καθαρισμό διαφημίσεων και trackers, Lite mode, δρομολόγηση μέσω proxy ανά χώρα με smart/strict/direct modes, προαιρετική υποστήριξη Tor, κρυπτογραφημένες εγγραφές vault μέσω OpenSSL και ενσωματωμένο εργαλείο full-page screenshots ιστοσελίδων. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

Πρόβλημα που μου έλυσε: ήθελα έναν ελαφρύ browser χώρο μέσα στο setup του κινητού αντί να πηδάω από app σε app. Παράδειγμα: bookmarks, saved pages, screenshots, private notes, καθάρισμα ιστορικού και πιο ασφαλείς επιλογές browsing σε ένα μέρος.

**Τοποθεσία Αποθήκευσης:** ~/Free Internet/ (browser/, vault/, browser/saved/, tools/screenshots/)

</details>


<a id="greek-network-tools"></a>

<h2>Εργαλεία Δικτύου</h2>


<details>
<summary>Bug Hunter</summary>


**Περιγραφή:** Bug Hunter (χωρίς root) — εξουσιοδοτημένο εργαλείο αναγνώρισης web ασφάλειας και ελέγχου κακής ρύθμισης. Ελέγχει security headers και cookie flags, ανιχνεύει τεχνολογίες, κάνει DNS ελέγχους (SPF/DMARC/CAA), αναλύει TLS/λήξη πιστοποιητικού, ελέγχει CORS και HTTP μεθόδους, βρίσκει εκτεθειμένα ευαίσθητα αρχεία, κάνει crawl στο site και αναλύει JavaScript για endpoints και πιθανές διαρροές μυστικών. Υποστηρίζει προαιρετικό directory discovery και Wayback recon, και παράγει απο-διπλοποιημένες αναφορές (JSON/CSV/HTML/PDF). Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

Πρόβλημα που μου έλυσε: πριν μοιραστώ το δικό μου site, ήθελα να βρίσκω βασικά λάθη ασφαλείας και setup. Παράδειγμα: έλεγχος headers, SSL, DNS, cookies και exposed files σε site που μου ανήκει.

**Τοποθεσία Αποθήκευσης:** Οι αναφορές αποθηκεύονται στον φάκελο εξόδου (προεπιλογή: bughunter_out/): report.json, report.csv, report.html (και report.pdf αν είναι διαθέσιμο)

</details>

<details>
<summary>Dark</summary>


**Περιγραφή:** Ένα εξειδικευμένο εργαλείο OSINT και crawler για το Dark Web, σχεδιασμένο για ανάλυση δικτύου Tor. Διαθέτει αυτοματοποιημένη σύνδεση Tor, ενσωμάτωση αναζήτησης Ahmia και αναδρομικό crawler για ιστοσελίδες .onion. Το εργαλείο χρησιμοποιεί ένα αρθρωτό σύστημα πρόσθετων για την εξαγωγή συγκεκριμένων τύπων δεδομένων (Email, διευθύνσεις BTC/XMR, κλειδιά PGP, Τηλέφωνα) και υποστηρίζει την αποθήκευση στιγμιότυπων. Προσφέρει λειτουργία Curses TUI και CLI, με αποτελέσματα εξαγώγιμα σε JSON, CSV και TXT. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

Πρόβλημα που μου έλυσε: ήθελα να καταλάβω το dark-web OSINT χωρίς να το βλέπω σαν μυστήριο ή παιχνίδι. Παράδειγμα: ασφαλής αποθήκευση δημόσιων research notes από επιτρεπτές πηγές με οργανωμένη δουλειά.

**Τοποθεσία Αποθήκευσης:** Τα αποτελέσματα αποθηκεύονται σε: /sdcard/Download/DarkNet

</details>

<details>
<summary>DedSec's Network</summary>


**Περιγραφή:** Μια προηγμένη εργαλειοθήκη δικτύου χωρίς root. Διαθέτει αναδρομικό πρόγραμμα λήψης ιστοσελίδων με υποστήριξη ZIP, πολυνηματικό σαρωτή θυρών, δοκιμή ταχύτητας internet και εργαλεία OSINT (WHOIS, DNS, Reverse IP). Περιλαμβάνει σαρωτές ελέγχου ιστού για SQLi, XSS, ανίχνευση CMS και SSH brute-force. Διατηρεί τοπικό αρχείο καταγραφής ελέγχου SQLite. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

Πρόβλημα που μου έλυσε: οι έλεγχοι δικτύου ήταν σκόρπιοι σε πολλές εντολές. Παράδειγμα: δοκιμή δικού μου local server, DNS check, speed test, site copy ή έλεγχος authorized στόχου από ένα menu.

**Τοποθεσία Αποθήκευσης:** Οι αναφορές και τα αρχεία καταγραφής αποθηκεύονται σε: ~/DedSec's Network

</details>

<details>
<summary>Digital Footprint Finder</summary>


**Περιγραφή:** Συντηρητικό εργαλείο OSINT ελέγχου usernames με στόχο τα καλύτερα πρακτικά αποτελέσματα και ελάχιστα ψευδώς θετικά. Σαρώνει μεγάλο πλήθος sites μέσω packs (core/extended) με προαιρετική βάση Sherlock, χρησιμοποιώντας βαθμολόγηση πολλαπλών σημάτων (status/redirects, title/meta/canonical/text) και όρια ταυτόχρονης σύνδεσης ανά domain για σταθερότητα. Ανιχνεύει anti-bot/JS challenges ως POSSIBLE (ποτέ ψευδώς FOUND), υποστηρίζει προαιρετικό search-engine dorking και εισαγωγή/εξαγωγή προσαρμοσμένων λιστών sites. Εξάγει αναφορές σε TXT/JSON/CSV και προαιρετικά HTML. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

Πρόβλημα που μου έλυσε: ήθελα να ξέρω πού εμφανίζεται το username ή το project name μου online. Παράδειγμα: έλεγχος dedsec1121fk ή DedSec Project σε δημόσια sites πριν καθαρίσω προφίλ ή ενημερώσω links.

**Τοποθεσία Αποθήκευσης:** Τα αποτελέσματα αποθηκεύονται σε: ~/storage/downloads/Digital Footprint Finder/[username]_v12.txt

</details>

<details>
<summary>Connections.py</summary>


**Περιγραφή:** Ασφαλής διακομιστής συνομιλίας/κοινής χρήσης αρχείων. Κλήσεις βίντεο, κοινή χρήση αρχείων (όριο 50GB). Ενοποιημένη εφαρμογή που συνδυάζει το Butterfly Chat και τη Βάση Δεδομένων DedSec με μοναδικό μυστικό κλειδί πιστοποίησης. Παρέχει ανταλλαγή μηνυμάτων σε πραγματικό χρόνο, κοινή χρήση αρχείων, κλήσεις βίντεο και ολοκληρωμένη διαχείριση αρχείων. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

Πρόβλημα που μου έλυσε: ήθελα έναν απλό ιδιωτικό χώρο για chat και αρχεία χωρίς τυχαίες υπηρεσίες. Παράδειγμα: αποστολή μεγάλου αρχείου ή φακέλου project ανάμεσα σε έμπιστες συσκευές μέσω δικού μου προσωρινού server.

**Τοποθεσία Αποθήκευσης:** Λήψεις στο `~/Downloads/DedSec's Database`.

</details>

<details>
<summary>Link Shield</summary>


**Περιγραφή:** Εργαλείο ελέγχου συνδέσμων: ακολουθεί redirects, ελέγχει HTTPS/SSL, εντοπίζει ύποπτα domains/μοτίβα και βγάζει αναφορά ρίσκου πριν ανοίξεις σύνδεσμο. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

Πρόβλημα που μου έλυσε: μου στέλνουν links που φαίνονται αθώα αλλά κρύβουν redirects. Παράδειγμα: έλεγχος περίεργου link από μήνυμα πριν το ανοίξω στο κινητό.

**Τοποθεσία Αποθήκευσης:** Φάκελοι σάρωσης δημιουργούνται στον τρέχοντα κατάλογο

</details>

<details>
<summary>Masker</summary>


**Περιγραφή:** URL helper για καθαρά, readable test links και έλεγχο redirect behavior στα δικά σου workflows. Παρουσιάζεται μόνο για οργάνωση, demos και authorized awareness training, ποτέ για να κρύψει κακόβουλα links ή να ξεγελάσει κόσμο.

Πρόβλημα που μου έλυσε: χρειαζόμουν καθαρά test links για awareness demos χωρίς τεράστια μπερδεμένα URLs. Παράδειγμα: δείχνω πώς δουλεύουν τα redirects σε μάθημα με δικά μου ελεγχόμενα links.

**Τοποθεσία Αποθήκευσης:** Δ/Υ (Έξοδος στην οθόνη).

</details>

<details>
<summary>QR Code Generator</summary>


**Περιγραφή:** Δημιουργός κωδικού QR βασισμένος σε Python που δημιουργεί κωδικούς QR για URLs και τους αποθηκεύει στο φάκελο Downloads/QR Codes. Διαθέτει αυτόματη εγκατάσταση εξαρτήσεων, φιλική προς τον χρήστη διεπαφή και χειρισμό σφαλμάτων για αξιόπιστη λειτουργία. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

Πρόβλημα που μου έλυσε: είναι κουραστικό να γράφω local links του Termux σε άλλη συσκευή. Παράδειγμα: δημιουργία QR code για local server link ώστε να το ανοίξω γρήγορα από άλλο κινητό.

**Τοποθεσία Αποθήκευσης:** Οι εικόνες αποθηκεύονται σε: ~/storage/downloads/QR Codes/

</details>

<details>
<summary>Sod</summary>


**Περιγραφή:** Ένα ολοκληρωμένο εργαλείο δοκιμής φόρτου για εφαρμογές web, με πολλαπλές μεθόδους δοκιμής (HTTP, WebSocket, προσομοίωση βάσης δεδομένων, μεταφόρτωση αρχείων, μικτό φόρτο εργασίας), μετρήσεις σε πραγματικό χρόνο και αυτόματη εγκατάσταση εξαρτήσεων. Προηγμένο πλαίσιο δοκιμής απόδοσης με ρεαλιστική προσομοίωση συμπεριφοράς χρήστη. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

Πρόβλημα που μου έλυσε: ήθελα να ξέρω αν τα δικά μου web apps αντέχουν πραγματική χρήση πριν τα μοιραστώ. Παράδειγμα: load test σε local ή δική μου σελίδα με ελεγχόμενο traffic και reports.

**Τοποθεσία Αποθήκευσης:** Διαμόρφωση: load_test_config.json στον κατάλογο σεναρίου | Αποτελέσματα: Εμφανίζονται στο terminal

</details>

<details>
<summary>Store Scrapper</summary>


**Περιγραφή:** Μονοαρχείο Python store scrapper για Termux που λειτουργεί χωρίς root. Δοκιμάζει πολλούς τρόπους για να βρίσκει κατηγορίες και προϊόντα σε απλές HTML σελίδες αλλά και σε πολλά JS-style stores, διαβάζοντας HTML, JSON-LD, embedded JSON, sitemaps, Shopify endpoints, WooCommerce APIs, generic product cards, breadcrumbs, OpenGraph/meta tags και εσωτερικούς συνδέσμους. Αποθηκεύει όσο τρέχει, ξεκινά πλήρες scraping προϊόντος μόλις βρεθεί κάθε προϊόν, δείχνει live κατάσταση στο terminal, χρησιμοποιεί το Enter ως προεπιλογή στα prompts και οργανώνει τα αποτελέσματα σε φακέλους store/category/product με κατεβασμένες εικόνες. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

Πρόβλημα που μου έλυσε: η έρευνα προϊόντων από κινητό γίνεται γρήγορα χάος. Παράδειγμα: κατέβασμα categories, products, εικόνων και τιμών από store σε οργανωμένους φακέλους για σύγκριση.

**Τοποθεσία Αποθήκευσης:** `Δημιουργεί φακέλους στο: ~/storage/downloads/Store Scrapper/<Store>/<Category>/<Product>/ (οι φάκελοι προϊόντων μπορούν να περιλαμβάνουν FOUND.txt, metadata.json, summary.txt, description.txt, images/, images.json, καθώς και αρχεία discovery/state).`

</details>


<a id="greek-personal-information-capture"></a>

<h2>Συλλογή Προσωπικών Πληροφοριών (Μόνο για Εκπαιδευτική Χρήση)</h2>


Αυτά τα scripts είναι training simulations που έχουν στόχο να βοηθούν τους χρήστες να κατανοούν πώς μπορεί να παρουσιάζονται παραπλανητικές σελίδες συλλογής προσωπικών δεδομένων, ώστε να τις αναγνωρίζουν και να αμύνονται καλύτερα απέναντί τους σε ελεγχόμενα περιβάλλοντα.

<details>
<summary>Fake Back Camera Page</summary>


**Περιγραφή:** Το Fake Back Camera Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Back Camera. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

Πρόβλημα που μου έλυσε: πολλοί δεν βλέπουν τον κίνδυνο πίσω από άδεια κάμερας από την πίσω κάμερα. Παράδειγμα: dummy consent-based demo που δείχνει πώς μια ψεύτικη σελίδα “scan this” μπορεί να ζητήσει κάμερα πριν ο αρχάριος σκεφτεί γιατί τη χρειάζεται, χωρίς συλλογή πραγματικών προσωπικών δεδομένων.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Back Camera Video Page</summary>


**Περιγραφή:** Το Fake Back Camera Video Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Back Camera Video. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

Πρόβλημα που μου έλυσε: πολλοί δεν βλέπουν τον κίνδυνο πίσω από άδεια εγγραφής βίντεο από την πίσω κάμερα. Παράδειγμα: dummy consent-based demo που δείχνει πώς μια σελίδα μπορεί να κάνει την εγγραφή να μοιάζει φυσιολογικό verification step, χωρίς συλλογή πραγματικών προσωπικών δεδομένων.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Card Details Page</summary>


**Περιγραφή:** Το Fake Card Details Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Card Details. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

Πρόβλημα που μου έλυσε: πολλοί δεν βλέπουν τον κίνδυνο πίσω από φόρμες καρτών. Παράδειγμα: dummy consent-based demo που δείχνει πώς ένα ψεύτικο checkout μπορεί να ζητήσει στοιχεία κάρτας πριν αγοραστεί οτιδήποτε πραγματικό, χωρίς συλλογή πραγματικών προσωπικών δεδομένων.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Chrome Verification Page</summary>


**Περιγραφή:** Το Fake Chrome Verification Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Chrome Verification. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

Πρόβλημα που μου έλυσε: πολλοί δεν βλέπουν τον κίνδυνο πίσω από ψεύτικο browser verification. Παράδειγμα: dummy consent-based demo που δείχνει πώς μια σελίδα μπορεί να προσποιηθεί ότι το Chrome χρειάζεται έναν ακόμα έλεγχο για να πατήσει ο χρήστης το prompt, χωρίς συλλογή πραγματικών προσωπικών δεδομένων.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Data Grabber Page</summary>


**Περιγραφή:** Το Fake Data Grabber Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Data Grabber. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

Πρόβλημα που μου έλυσε: πολλοί δεν βλέπουν τον κίνδυνο πίσω από φόρμες που ζητούν υπερβολικά δεδομένα. Παράδειγμα: dummy consent-based demo που δείχνει πώς μια απλή φόρμα “continue” μπορεί να ζητήσει υπερβολικά προσωπικά στοιχεία, χωρίς συλλογή πραγματικών προσωπικών δεδομένων.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Discord Verification Page</summary>


**Περιγραφή:** Το Fake Discord Verification Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Discord Verification. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

Πρόβλημα που μου έλυσε: πολλοί δεν βλέπουν τον κίνδυνο πίσω από κόλπα Discord verification. Παράδειγμα: dummy consent-based demo που δείχνει πώς ένα ψεύτικο server check μπορεί να πιέσει κάποιον να γράψει login στοιχεία, χωρίς συλλογή πραγματικών προσωπικών δεδομένων.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Facebook Verification Page</summary>


**Περιγραφή:** Το Fake Facebook Verification Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Facebook Verification. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

Πρόβλημα που μου έλυσε: πολλοί δεν βλέπουν τον κίνδυνο πίσω από κόλπα Facebook verification. Παράδειγμα: dummy consent-based demo που δείχνει πώς μια σελίδα μπορεί να αντιγράψει την αίσθηση κανονικού Facebook security check, χωρίς συλλογή πραγματικών προσωπικών δεδομένων.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Front Camera Page</summary>


**Περιγραφή:** Το Fake Front Camera Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Front Camera. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

Πρόβλημα που μου έλυσε: πολλοί δεν βλέπουν τον κίνδυνο πίσω από άδεια μπροστινής κάμερας. Παράδειγμα: dummy consent-based demo που δείχνει πώς ένα “selfie verification” prompt μπορεί να κρύψει τι πρόσβαση δίνεται, χωρίς συλλογή πραγματικών προσωπικών δεδομένων.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Front Camera Video Page</summary>


**Περιγραφή:** Το Fake Front Camera Video Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Front Camera Video. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

Πρόβλημα που μου έλυσε: πολλοί δεν βλέπουν τον κίνδυνο πίσω από βίντεο από μπροστινή κάμερα. Παράδειγμα: dummy consent-based demo που δείχνει πώς ένα fake live check μπορεί να κάνει την εγγραφή βίντεο να μοιάζει απλό κλικ, χωρίς συλλογή πραγματικών προσωπικών δεδομένων.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Google Location Page</summary>


**Περιγραφή:** Το Fake Google Location Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Google Location. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

Πρόβλημα που μου έλυσε: πολλοί δεν βλέπουν τον κίνδυνο πίσω από Google-style location prompts. Παράδειγμα: dummy consent-based demo που δείχνει πώς ένα γνώριμο logo μπορεί να κάνει ένα location request να φαίνεται πιο έμπιστο απ’ όσο είναι, χωρίς συλλογή πραγματικών προσωπικών δεδομένων.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Instagram Verification Page</summary>


**Περιγραφή:** Το Fake Instagram Verification Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Instagram Verification. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

Πρόβλημα που μου έλυσε: πολλοί δεν βλέπουν τον κίνδυνο πίσω από κόλπα Instagram verification. Παράδειγμα: dummy consent-based demo που δείχνει πώς μια ψεύτικη follower ή security σελίδα μπορεί να σπρώξει κάποιον σε dummy login box, χωρίς συλλογή πραγματικών προσωπικών δεδομένων.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Location Page</summary>


**Περιγραφή:** Το Fake Location Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Location. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

Πρόβλημα που μου έλυσε: πολλοί δεν βλέπουν τον κίνδυνο πίσω από απλά location prompts. Παράδειγμα: dummy consent-based demo που δείχνει πώς μια σελίδα μπορεί να ζητήσει τοποθεσία με αδύναμη δικαιολογία όπως “continue near you”, χωρίς συλλογή πραγματικών προσωπικών δεδομένων.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Microphone Page</summary>


**Περιγραφή:** Το Fake Microphone Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Microphone. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

Πρόβλημα που μου έλυσε: πολλοί δεν βλέπουν τον κίνδυνο πίσω από άδεια μικροφώνου. Παράδειγμα: dummy consent-based demo που δείχνει πώς ένα fake voice check μπορεί να κάνει την πρόσβαση στο μικρόφωνο να μοιάζει ακίνδυνη, χωρίς συλλογή πραγματικών προσωπικών δεδομένων.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake OnlyFans Verification Page</summary>


**Περιγραφή:** Το Fake OnlyFans Verification Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από OnlyFans Verification. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

Πρόβλημα που μου έλυσε: πολλοί δεν βλέπουν τον κίνδυνο πίσω από κόλπα OnlyFans verification. Παράδειγμα: dummy consent-based demo που δείχνει πώς η περιέργεια μπορεί να κάνει τον χρήστη να αγνοήσει τι ζητά μια φόρμα verification, χωρίς συλλογή πραγματικών προσωπικών δεδομένων.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Steam Verification Page</summary>


**Περιγραφή:** Το Fake Steam Verification Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Steam Verification. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

Πρόβλημα που μου έλυσε: πολλοί δεν βλέπουν τον κίνδυνο πίσω από κόλπα Steam verification. Παράδειγμα: dummy consent-based demo που δείχνει πώς μια ψεύτικη σελίδα game reward μπορεί να κάνει τα login prompts να μοιάζουν φυσιολογικά, χωρίς συλλογή πραγματικών προσωπικών δεδομένων.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Twitch Verification Page</summary>


**Περιγραφή:** Το Fake Twitch Verification Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Twitch Verification. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

Πρόβλημα που μου έλυσε: πολλοί δεν βλέπουν τον κίνδυνο πίσω από κόλπα Twitch verification. Παράδειγμα: dummy consent-based demo που δείχνει πώς ένα fake streamer reward μπορεί να κάνει τον χρήστη να πατήσει πριν ελέγξει το domain, χωρίς συλλογή πραγματικών προσωπικών δεδομένων.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake YouTube Verification Page</summary>


**Περιγραφή:** Το Fake YouTube Verification Page είναι consent-based awareness demo για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από YouTube Verification. Χρησιμοποίησέ το μόνο σε lab, με dummy data, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

Πρόβλημα που μου έλυσε: πολλοί δεν βλέπουν τον κίνδυνο πίσω από κόλπα YouTube verification. Παράδειγμα: dummy consent-based demo που δείχνει πώς ένα fake channel ή subscriber check μπορεί να κάνει ένα login box να φαίνεται επίσημο, χωρίς συλλογή πραγματικών προσωπικών δεδομένων.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>


<a id="greek-fake-pages"></a>

<h2>Ψεύτικες Σελίδες (Μόνο για Εκπαιδευτική Χρήση)</h2>


Αυτά τα scripts είναι εκπαιδευτικά simulations που έχουν στόχο να βοηθούν τους χρήστες να αναγνωρίζουν social-engineering patterns, ψεύτικες reward pages, ψεύτικες verification flows και imitation brand pages που συχνά χρησιμοποιούνται για να πιέζουν ανθρώπους σε μη ασφαλείς ενέργειες.

<details>
<summary>Fake Apple iCloud Page</summary>


**Περιγραφή:** Το Fake Apple iCloud Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Apple iCloud προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε iCloud storage ή locked-account warnings ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Discord Nitro Page</summary>


**Περιγραφή:** Το Fake Discord Nitro Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Discord Nitro προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε δωρεάν Nitro offers ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Epic Games Page</summary>


**Περιγραφή:** Το Fake Epic Games Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Epic Games προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε δωρεάν game ή skin offers ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Facebook Friends Page</summary>


**Περιγραφή:** Το Fake Facebook Friends Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Facebook Friends προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε υποσχέσεις για friends ή profile views ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Free Robux Page</summary>


**Περιγραφή:** Το Fake Free Robux Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Free Robux προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε υποσχέσεις για δωρεάν Robux ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake GitHub Pro Page</summary>


**Περιγραφή:** Το Fake GitHub Pro Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες GitHub Pro προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε υποσχέσεις για δωρεάν GitHub Pro ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Google Free Money Page</summary>


**Περιγραφή:** Το Fake Google Free Money Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Google Free Money προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε ψεύτικα Google reward messages ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Instagram Followers Page</summary>


**Περιγραφή:** Το Fake Instagram Followers Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Instagram Followers προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε υποσχέσεις για δωρεάν followers ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake MetaMask Page</summary>


**Περιγραφή:** Το Fake MetaMask Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες MetaMask προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε παγίδες wallet recovery ή seed phrase ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Microsoft 365 Page</summary>


**Περιγραφή:** Το Fake Microsoft 365 Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Microsoft 365 προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε ψεύτικες Office renewal προειδοποιήσεις ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake OnlyFans Page</summary>


**Περιγραφή:** Το Fake OnlyFans Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες OnlyFans προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε login traps που πατάνε στην περιέργεια ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake PayPal Page</summary>


**Περιγραφή:** Το Fake PayPal Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες PayPal προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε προειδοποιήσεις πληρωμής ή refund ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Pinterest Pro Page</summary>


**Περιγραφή:** Το Fake Pinterest Pro Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Pinterest Pro προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε ψεύτικα creator upgrade offers ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake PlayStation Network Page</summary>


**Περιγραφή:** Το Fake PlayStation Network Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες PlayStation Network προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε δωρεάν PSN credit ή account-warning σελίδες ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Reddit Karma Page</summary>


**Περιγραφή:** Το Fake Reddit Karma Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Reddit Karma προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε υποσχέσεις για karma boost ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Snapchat Friends Page</summary>


**Περιγραφή:** Το Fake Snapchat Friends Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Snapchat Friends προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε υποσχέσεις για friend-view ή unlock ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Steam Games Page</summary>


**Περιγραφή:** Το Fake Steam Games Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Steam Games προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε claims για δωρεάν Steam games ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Steam Wallet Page</summary>


**Περιγραφή:** Το Fake Steam Wallet Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Steam Wallet προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε claims για δωρεάν Steam wallet balance ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake TikTok Followers Page</summary>


**Περιγραφή:** Το Fake TikTok Followers Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες TikTok Followers προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε υποσχέσεις για followers και views ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Trust Wallet Page</summary>


**Περιγραφή:** Το Fake Trust Wallet Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Trust Wallet προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε παγίδες wallet recovery ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Twitch Subs Page</summary>


**Περιγραφή:** Το Fake Twitch Subs Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Twitch Subs προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε δωρεάν subscription rewards ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Twitter Followers Page</summary>


**Περιγραφή:** Το Fake Twitter Followers Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Twitter Followers προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε ψεύτικα follower growth offers ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake What's Up Dude Page</summary>


**Περιγραφή:** Το Fake What's Up Dude Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες What's Up Dude προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε τυχαία φιλικά μηνύματα που κρύβουν φόρμες ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake Xbox Live Page</summary>


**Περιγραφή:** Το Fake Xbox Live Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Xbox Live προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε δωρεάν Xbox credit ή login warnings ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>

<details>
<summary>Fake YouTube Subscribers Page</summary>


**Περιγραφή:** Το Fake YouTube Subscribers Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες YouTube Subscribers προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

Πρόβλημα που μου έλυσε: τα scams πιάνουν επειδή το δόλωμα φαίνεται φυσιολογικό. Παράδειγμα: dummy σελίδα βασισμένη σε υποσχέσεις για subscriber boost ώστε κάποιος να μάθει να ελέγχει domain, αίτημα και υπόσχεση πριν γράψει οτιδήποτε πραγματικό.

**Τοποθεσία Αποθήκευσης:** Τα training outputs πρέπει να μένουν τοπικά στον δικό σου lab φάκελο. Χρησιμοποίησε μόνο dummy data και ποτέ πραγματικές προσωπικές πληροφορίες.

</details>


<a id="greek-games"></a>

<h2>Παιχνίδια</h2>


<details>
<summary>Buzz</summary>


**Περιγραφή:** Ένα text-only παιχνίδι trivia για Termux με ενσωματωμένη σταθερή βάση 15.000 ερωτήσεων (χωρίς δημιουργία κατά την εκτέλεση). Υποστηρίζει 1–2 παίκτες (pass-and-play), πολλούς τύπους γύρων, φίλτρο δυσκολίας (Όλες/Εύκολες/Μέτριες/Δύσκολες), προφίλ, ρυθμίσεις και πίνακες βαθμολογίας. Ελαφρύ παιχνίδι τερματικού με γρήγορους χειρισμούς και δυνατότητα επανάληψης.

Πρόβλημα που μου έλυσε: ήθελα παιχνίδι χωρίς internet που να μαθαίνεις και κάτι. Παράδειγμα: γρήγορο trivia σε διάλειμμα, σε αναμονή ή όταν τα δεδομένα είναι αδύναμα.

**Τοποθεσία Αποθήκευσης:** ~/Buzz/ (data/ για DB, προφίλ, ρυθμίσεις, βαθμολογίες)

</details>

<details>
<summary>CTF God</summary>


**Περιγραφή:** Πλήρες CTF παιχνίδι για Termux σε fullscreen Curses, με story mode, αποστολές, daily challenges, τυχαία boss levels, κατάστημα hints, achievements & ranks, εισαγωγή/εξαγωγή challenge packs, tournament mode και anti‑cheat/integrity checks. Περιλαμβάνει ενσωματωμένο level editor. Ελαφρύ παιχνίδι τερματικού με γρήγορους χειρισμούς και δυνατότητα επανάληψης.

Πρόβλημα που μου έλυσε: ήθελα εξάσκηση cybersecurity χωρίς να αγγίζω πραγματικούς στόχους. Παράδειγμα: λύσιμο terminal CTF αποστολών, hints και boss levels μέσα σε ασφαλές game περιβάλλον.

**Τοποθεσία Αποθήκευσης:** `Φάκελοι χρήστη & αρχεία challenges: /storage/emulated/0/Download/CTF God/<username>/files (εναλλακτικά: ~/storage/downloads/CTF God/...). Κατάσταση παιχνιδιού & packs: ~/.ctf_god/ (state.json, packs/, custom.json).`

</details>

<details>
<summary>Detective</summary>


**Περιγραφή:** Ένα story-driven παιχνίδι ντετέκτιβ για Termux στο terminal με διευρυμένη σταθερή βιβλιοθήκη υποθέσεων, πλουσιότερα lore dossiers, φήμες περιοχών, side stories και επιπλέον story threads. Παρακολουθήστε στοιχεία, ανακρίνετε υπόπτους, δείτε suspect rosters, χτίστε ASCII case board και timeline και διαχειριστείτε την πρόοδο με 3 save slots και autosave. Περιλαμβάνει 4 δυσκολίες, notes/evidence tracking, checkpoint hints και γρήγορες εντολές όπως :help, :guide, :lore, :suspects, :board, :timeline, :hint και :save.

Πρόβλημα που μου έλυσε: ήθελα story game που να γυμνάζει την προσοχή αντί απλά να σκοτώνει χρόνο. Παράδειγμα: διάβασμα στοιχείων, case board και έλεγχος αντιφάσεων μέσα από το Termux.

**Τοποθεσία Αποθήκευσης:** ~/Detective/ (προφίλ παίκτη, save slots, autosave και πρόοδος υποθέσεων)

</details>

<details>
<summary>Tamagotchi</summary>


**Περιγραφή:** Ένα πλήρως χαρακτηριστικό παιχνίδι κατοικίδιου terminal. Τρέφετε, παίζετε, καθαρίζετε και εκπαιδεύετε το κατοικίδιό σας. Μην το αφήσετε να πεθάνει. Προηγμένο παιχνίδι προσομοίωσης εικονικού κατοικίδιου με ολοκληρωμένο σύστημα διαχείρισης. Χαρακτηριστικά περιλαμβάνουν εξέλιξη κατοικίδιου μέσα από στάδια ζωής, χαρακτηριστικά προσωπικότητας, ανάπτυξη δεξιοτήτων, μίνι παιχνίδια, σύστημα εργασίας και συνταξιοδότηση κληρονομιάς. Ελαφρύ παιχνίδι τερματικού με γρήγορους χειρισμούς και δυνατότητα επανάληψης.

Πρόβλημα που μου έλυσε: ήθελα ένα μικρό καθημερινό παιχνίδι που τρέχει και σε απλό κινητό. Παράδειγμα: τάισμα, training και γρήγορος έλεγχος terminal pet για πέντε λεπτά χωρίς βαρύ app.

**Τοποθεσία Αποθήκευσης:** ~/.termux_tamagotchi_v8.json

</details>

<details>
<summary>Terminal Arcade</summary>


**Περιγραφή:** Πακέτο arcade για τερματικό με πολλά mini-games σε ένα script. Αποθηκεύει δεδομένα στο ~/Terminal Arcade/ και τρέχει ομαλά σε Termux/Linux. Ελαφρύ παιχνίδι τερματικού με γρήγορους χειρισμούς και δυνατότητα επανάληψης.

Πρόβλημα που μου έλυσε: δεν ήθελα δέκα διαφορετικά μικρά game files παντού. Παράδειγμα: ανοίγω ένα arcade pack από Termux όταν θέλω γρήγορο Snake-style ή mini-game διάλειμμα.

**Τοποθεσία Αποθήκευσης:** Φάκελοι σάρωσης δημιουργούνται στον τρέχοντα κατάλογο

</details>


<a id="greek-other-tools"></a>

<h2>Άλλα Εργαλεία</h2>


<details>
<summary>Android App Launcher</summary>


**Περιγραφή:** Βοηθητικό πρόγραμμα για διαχείριση εφαρμογών Android απευθείας από το terminal. Μπορεί να εκκινήσει εφαρμογές, να εξάγει αρχεία APK, να απεγκαταστήσει εφαρμογές και να αναλύσει δικαιώματα ασφαλείας. Προηγμένο εργαλείο διαχείρισης εφαρμογών Android και ανάλυσης ασφαλείας. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

Πρόβλημα που μου έλυσε: η αλλαγή ανάμεσα σε terminal δουλειά και Android apps με καθυστερούσε. Παράδειγμα: άνοιγμα, έλεγχος ή εξαγωγή app απευθείας από Termux ενώ χτίζω ή δοκιμάζω.

**Τοποθεσία Αποθήκευσης:** Εξαγόμενα APK: ~/storage/shared/Download/Extracted APK's | Αναφορές: ~/storage/shared/Download/App_Security_Reports

</details>

<details>
<summary>Loading Screen</summary>


**Περιγραφή:** Εξατομίκευση εκκίνησης Termux με ASCII art loading screens. Υποστηρίζει custom art, καθυστέρηση και αυτόματο setup/cleanup για εμφάνιση μία φορά. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

Πρόβλημα που μου έλυσε: τα scripts έμοιαζαν πρόχειρα όταν άνοιγαν με απλό terminal χάος. Παράδειγμα: καθαρό loading screen ώστε ένα εργαλείο να μοιάζει μέρος ενός project και όχι τυχαίος κώδικας.

**Τοποθεσία Αποθήκευσης:** Τροποποιεί `.bash_profile` και `bash.bashrc`.

</details>

<details>
<summary>Password Master</summary>


**Περιγραφή:** Ολοκληρωμένο σύνολο διαχείρισης κωδικών πρόσβασης με κρυπτογραφημένη αποθήκευση θησαυροφυλακίου, δημιουργία κωδικών, ανάλυση ισχύος και εργαλεία βελτίωσης. Περιλαμβάνει AES-256 κρυπτογραφημένο θησαυροφυλάκιο με προστασία κύριου κωδικού πρόσβασης, γεννήτρια τυχαίων κωδικών, γεννήτρια φράσεων πρόσβασης, αναλυτή ισχύος κωδικού και προτάσεις βελτίωσης κωδικών. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

Πρόβλημα που μου έλυσε: passwords project, test logins και tokens χάνονταν εύκολα. Παράδειγμα: οργανωμένα local test credentials αντί να τα κρύβω σε τυχαίες σημειώσεις.

**Τοποθεσία Αποθήκευσης:** Αρχείο θησαυροφυλακίου: my_vault.enc | Αντίγραφα ασφαλείας: ~/Download/Password Master Backup

</details>

<details>
<summary>Termux Backup Restore</summary>


**Περιγραφή:** Backup & restore για Termux: δημιουργεί zip backup των αρχείων σου στα Downloads και μπορεί να τα επαναφέρει με ελέγχους ακεραιότητας. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

Πρόβλημα που μου έλυσε: ένα πρόβλημα στο κινητό μπορούσε να χαλάσει μέρες δουλειάς στο Termux. Παράδειγμα: backup scripts και data πριν από updates και restore μετά από reinstall ή θέμα storage.

**Τοποθεσία Αποθήκευσης:** Φάκελοι σάρωσης δημιουργούνται στον τρέχοντα κατάλογο

</details>

<details>
<summary>Termux Repair Wizard</summary>


**Περιγραφή:** Οδηγός επιδιόρθωσης Termux: ελέγχει συνηθισμένα προβλήματα (mirrors, πακέτα, δικαιώματα), προτείνει λύσεις και τρέχει ασφαλείς εντολές βήμα-βήμα. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

Πρόβλημα που μου έλυσε: τυχαίες εντολές για fix μπορούν να χαλάσουν περισσότερο το Termux. Παράδειγμα: guided repair για storage, packages, Python, pip και permissions αντί για μαντεψιές.

**Τοποθεσία Αποθήκευσης:** Φάκελοι σάρωσης δημιουργούνται στον τρέχοντα κατάλογο

</details>


<a id="greek-no-category"></a>

<h2>Χωρίς Κατηγορία</h2>


<details>
<summary>Extra Content</summary>


**Περιγραφή:** Κόμβος extra περιεχομένου: γρήγορη πρόσβαση σε πρόσθετους πόρους, templates και προαιρετικά add-ons του DedSec toolkit. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

Πρόβλημα που μου έλυσε: τα extra resources ήταν σκόρπια και εύκολο να ξεχαστούν. Παράδειγμα: ένα hub για bonus templates, add-ons και extras του project αντί να ψάχνω χειροκίνητα φακέλους.

**Τοποθεσία Αποθήκευσης:** Φάκελοι σάρωσης δημιουργούνται στον τρέχοντα κατάλογο

</details>

<details>
<summary>Settings.py</summary>


**Περιγραφή:** Το Settings.py είναι το κεντρικό control panel του DedSec Project. Εμφανίζει πληροφορίες project και συσκευής, ενημερώνει το project από την κύρια ή την backup πηγή, ανανεώνει Termux packages και Python modules, ελέγχει και κατεβάζει Sponsors-Only scripts μέσω συνδεδεμένου GitHub account, δημιουργεί backup του DedSec Project στα Downloads, αλλάζει το Termux prompt, συνδέει ή αποσυνδέει GitHub, εμφανίζει GitHub stats, συγχρονίζει το prompt με το GitHub username, σαρώνει Termux usage stats, διαχειρίζεται προαιρετικά VPN και Tor utilities, αλλάζει ανάμεσα σε List, Grid, Choose By Number και DedSec OS menu styles, ελέγχει το menu auto-start, αποθηκεύει επιλογή γλώσσας English ή Greek, εμφανίζει credits και κάνει ασφαλή απεγκατάσταση του project. Το DedSec OS προσθέτει browser-based local workspace με file browser, safe text editor, terminal view, session manager, DedSec apps launcher, Linux package store actions, notifications, fullscreen και split-view controls, sidebar controls, wallpaper support, display name settings, terminal color settings, project action buttons, language controls, prompt controls, password login, προαιρετικό authenticator-style 2FA και recovery μέσω τριών security questions. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

Πρόβλημα που μου έλυσε: το DedSec έγινε πολύ μεγάλο για να το ελέγχω από μνήμης. Παράδειγμα: updates, packages, backup στα Downloads, sponsor access, GitHub και menu styles από ένα command center.

**Τοποθεσία Αποθήκευσης:** Ρύθμιση γλώσσας: ~/Language.json | Backup ρυθμίσεων Termux: ~/Termux.zip | Save DedSec Project backup: Downloads

</details>

<details>
<summary>DedSec Market</summary>


**Περιγραφή:** Curses-based market αποθετηρίων GitHub για Termux που εμφανίζει τα projects με το όνομα του project αντί για το ακατέργαστο όνομα του repository. Καθαρίζει και εμφανίζει σωστά το κείμενο των README, δείχνει releases και issues, υποστηρίζει ενέργειες install/update/delete και launch, κρατά watchlist και αποθηκεύει cache/state για πιο γρήγορη επαναχρησιμοποίηση. Φτιαγμένο για Termux με καθαρές επιλογές και οργανωμένα αποτελέσματα.

Πρόβλημα που μου έλυσε: δεν ήθελα να θυμάμαι κάθε GitHub repo name και install command. Παράδειγμα: browsing projects με καθαρό όνομα, README, install, update, delete και launch από ένα market-style menu.

**Τοποθεσία Αποθήκευσης:** `Δεδομένα εφαρμογής: ~/DedSec Market/ (cache/, state.json) | Εγκατεστημένα repositories: ~/<repo-name>`

</details>


<a id="greek-sponsors-only"></a>

<h2>Μόνο για Χορηγούς</h2>


Το Sponsors-Only access χωρίζεται πλέον σε δύο GitHub Sponsors tiers:

| Tier | Τι περιλαμβάνει |
| :--- | :-------------- |
| **$3 Sponsor** | Τα υπάρχοντα sponsor scripts που εμφανίζονται ήδη στο website: Face Detector.py, Face Detector Heavy.py, Face Swap.py, Steganography.py και AR Terror.py. |
| **$9 Pro Supporter** | Όλα τα scripts του $3 tier, μαζί με τα **Widget Maker.py**, **Kraken Trader.py** και **Noob Hacker.py**. |

**• Scripts Χορηγών $3**


<details>
<summary>Face Detector.py</summary>


**Περιγραφή:** Τοπικό browser-based εργαλείο ανάλυσης προσώπου για Termux που λειτουργεί χωρίς root. Χρησιμοποιεί MediaPipe Face Mesh στο live feed της κάμερας, υποστηρίζει μπροστινή και πίσω κάμερα, παρακολουθεί έως και 3 πρόσωπα, σχεδιάζει αναλυτικά facial landmark overlays αντί για απλά boxes και επιτρέπει επίσης upload φωτογραφιών ή βίντεο για ανάλυση απευθείας από το interface. Μπορεί να τραβά PNG snapshots, να γράφει WEBM βίντεο, να αποθηκεύει ξεχωριστά cropped detected faces και να παρέχει τόσο local network link όσο και προαιρετικό δημόσιο Cloudflare link.

Πρόβλημα που μου έλυσε: ήθελα πραγματικό browser camera demo από Termux χωρίς root. Παράδειγμα: local link, αλλαγή κάμερας, detection στα δικά μου face landmarks και αποθήκευση test snapshots από το κινητό.

**Τοποθεσία Αποθήκευσης:** Στο Termux, τα captures, τα recordings, τα uploaded results και τα αποθηκευμένα face crops μπαίνουν στο: ~/storage/downloads/Face Detector/. Αν το storage του Termux δεν είναι διαθέσιμο, γίνεται fallback στο ~/Face Detector/. Σε συστήματα εκτός Termux χρησιμοποιείται το ~/Downloads/Face Detector/, με fallback στο ~/Face Detector/. Τα εσωτερικά web αρχεία, τα certificates και τα helper binaries αποθηκεύονται στο ~/.face_detector_studio/.

</details>

<details>
<summary>Face Detector Heavy.py</summary>


**Περιγραφή:** Πιο βαριά και επεκταμένη έκδοση ανάλυσης του face detector για Termux, χωρίς ανάγκη για root. Εκτός από live χρήση κάμερας, εναλλαγή μπροστινής/πίσω κάμερας, upload φωτογραφιών και βίντεο, PNG snapshots, WEBM recording και αποθήκευση face crops, ανεβάζει την παρακολούθηση έως και σε 30 πρόσωπα και προσθέτει TensorFlow COCO-SSD object detection πάνω στο pipeline του MediaPipe face mesh. Εμφανίζει πιο πλούσιο on-screen telemetry όπως face count, animal/object detection, εκτιμήσεις pose και gaze, facial proportions, κατάσταση στόματος και φρυδιών, asymmetry scoring και άλλα visual analysis στοιχεία, ενώ συνεχίζει να υποστηρίζει local network link και προαιρετικό δημόσιο Cloudflare link.

Πρόβλημα που μου έλυσε: ήθελα να πάω το camera tool πιο μακριά για πιο πλούσια demos. Παράδειγμα: δοκιμή πολλών προσώπων, object detection, pose hints και πιο βαρύ telemetry σε ελεγχόμενο phone/browser setup.

**Τοποθεσία Αποθήκευσης:** Στο Termux, τα captures, τα recordings, τα uploaded results και τα αποθηκευμένα face crops μπαίνουν στο: ~/storage/downloads/Face Detector/. Αν το storage του Termux δεν είναι διαθέσιμο, γίνεται fallback στο ~/Face Detector/. Σε συστήματα εκτός Termux χρησιμοποιείται το ~/Downloads/Face Detector/, με fallback στο ~/Face Detector/. Τα εσωτερικά web αρχεία, τα certificates και τα helper binaries αποθηκεύονται στο ~/.face_detector_studio/.

</details>

<details>
<summary>Face Swap.py</summary>


**Περιγραφή:** Τοπικό browser-based εργαλείο face swap για Termux που λειτουργεί χωρίς root. Ανοίγει μια local camera σελίδα, σου επιτρέπει να ανεβάσεις μια source face εικόνα, να αλλάξεις ανάμεσα σε μπροστινή και πίσω κάμερα και να κάνεις blend το ανεβασμένο πρόσωπο πάνω στο live camera feed με MediaPipe Face Mesh. Η τρέχουσα έκδοση εστιάζει σε smooth face-lock λογική: κλειδώνει το ανεβασμένο πρόσωπο μία φορά, ακολουθεί το live πρόσωπο, κινεί βασικά feature patches για expressions, περιλαμβάνει smoothing, feathering, opacity, blend και skin-tone matching controls και μπορεί να αποθηκεύει PNG snapshots από τον browser. Χρησιμοποίησέ το μόνο με δικές σου εικόνες ή με ξεκάθαρη άδεια.

Πρόβλημα που μου έλυσε: ήθελα ένα local phone-friendly face swap demo χωρίς να εγκαταστήσω βαριά εφαρμογή. Παράδειγμα: άνοιγμα local link, upload test face εικόνας, αλλαγή κάμερας, ρύθμιση blend και αποθήκευση PNG result στα Downloads.

**Τοποθεσία Αποθήκευσης:** Στο Termux, οι αποθηκευμένες φωτογραφίες μπαίνουν στο: /storage/emulated/0/Download/Face Swap/ ή στο ~/storage/downloads/Face Swap/, με fallback στο ~/Face Swap/. Σε συστήματα εκτός Termux χρησιμοποιείται το ~/Downloads/Face Swap/, με fallback στο ~/Face Swap/.

</details>

<details>
<summary>Steganography.py</summary>


**Περιγραφή:** Σουίτα steganography με κωδικό για Termux. Μπορεί να δημιουργεί τυχαίες ασπρόμαυρες PNG εικόνες-φορείς, να κρυπτογραφεί μυστικό κείμενο με password-derived Fernet key, να κρύβει το κρυπτογραφημένο κείμενο μέσα σε PNG εικόνες με LSB steganography και να κάνει batch αποκωδικοποίηση κρυμμένων μηνυμάτων από όλες τις εικόνες που τοποθετούνται στον φάκελο Decrypt. Τα εξαγόμενα μηνύματα αποθηκεύονται αυτόματα ως ξεχωριστά αρχεία .txt και το script μπορεί προαιρετικά να καθαρίζει τις ήδη επεξεργασμένες εικόνες από τον φάκελο αποκωδικοποίησης μετά το scan.

Πρόβλημα που μου έλυσε: ήθελα να καταλάβω τεχνικές hidden messages με ασφαλή τρόπο. Παράδειγμα: κρύβω ένα αθώο test note μέσα σε PNG με password και το αποκωδικοποιώ μετά από τον Decrypt φάκελο.

**Τοποθεσία Αποθήκευσης:** Κύριος φάκελος: /storage/emulated/0/Download/Steganography/ | Carrier/output εικόνες: /Encrypt | Εικόνες για έλεγχο κρυμμένων μηνυμάτων: /Decrypt | Εξαγόμενα αρχεία κειμένου: /Decrypted Texts

</details>

<details>
<summary>AR Terror.py</summary>


**Περιγραφή:** Τοπική browser-based AR horror εμπειρία για Termux που λειτουργεί χωρίς root. Εκκινεί μια full-screen camera-driven ιστοσελίδα όπου εξερευνάς το περιβάλλον, συλλέγεις κρυμμένα logs μέσα σε archive/inventory σύστημα, χρησιμοποιείς ατμοσφαιρικά visual και audio effects, αλλάζεις ανάμεσα σε μπροστινή και πίσω κάμερα και γράφεις evidence σε WEBM όσο τρέχει η εμπειρία. Μπορεί επίσης να παρέχει τόσο local network link όσο και προαιρετικό δημόσιο Cloudflare link.

Πρόβλημα που μου έλυσε: ήθελα να δείξω ότι το Termux μπορεί να τρέξει και δημιουργικά browser experiences, όχι μόνο utilities. Παράδειγμα: local AR horror page, χρήση κάμερας, συλλογή logs και εγγραφή μικρού evidence clip.

**Τοποθεσία Αποθήκευσης:** Στο Termux, το recorded evidence αποθηκεύεται στο: ~/storage/downloads/AR Terror/. Αν το storage του Termux δεν είναι διαθέσιμο, γίνεται fallback στο ~/AR Terror/. Σε συστήματα εκτός Termux χρησιμοποιείται το ~/Downloads/AR Terror/, με fallback στο ~/AR Terror/. Τα εσωτερικά web αρχεία, τα certificates και τα helper binaries αποθηκεύονται στο ~/.ar_terror_studio/.

</details>

<details>
<summary>Widget Maker.py</summary>


**Περιγραφή:** Το DedSec Widget Maker είναι no-root helper για Termux που δημιουργεί Android home-screen launchers για scripts του DedSec Project μέσω Termux:Widget. Σαρώνει αναδρομικά το Termux home, το shared storage και συνηθισμένους φακέλους του κινητού για DedSec, sponsor, exclusive και σχετικά Python scripts, μαζί με scripts μέσα σε κάθε προσβάσιμο φάκελο και υποφάκελο. Μετά δημιουργεί managed shortcuts στο ~/.shortcuts. Κάθε widget ανοίγει μικρό menu με Run, Show Script Path και Exit, ελέγχει το Python αρχείο πριν το τρέξει, κρατά manifest στο ~/.dedsec_widget_maker/ και μπορεί να κάνει update ή delete όλα τα managed widgets όταν αλλάζει η συλλογή των scripts σου.

Πρόβλημα που μου έλυσε: ήθελα one-tap Android shortcuts για κάθε DedSec και sponsor script χωρίς να γράφω χειροκίνητα Termux:Widget αρχεία. Παράδειγμα: σάρωση όλων των project folders, δημιουργία widgets, ανανέωσή τους αργότερα και διαγραφή μόνο των managed widgets όταν χρειάζεται.

**Τοποθεσία Αποθήκευσης:** Τα managed widget launchers δημιουργούνται στο: ~/.shortcuts/ | Το state και το manifest αποθηκεύονται στο: ~/.dedsec_widget_maker/manifest.json. Τα αρχικά scripts δεν μετακινούνται· κάθε widget δείχνει πίσω στο detected source file.

</details>

<details>
<summary>Kraken Trader.py</summary>


**Περιγραφή:** Το Kraken Trader.py είναι Termux trading research και portfolio assistant για το Kraken API. Ξεκινά σε paper mode από προεπιλογή, εμφανίζει risk disclaimer με countdown 10 δευτερολέπτων, αποθηκεύει τα πάντα στο ~/Kraken Trader/ και χρησιμοποιεί numbered menus για pair analysis, market scanning, dashboards, Sage-style strategy labs, advanced tools, beginner guides, risk/reward calculators, backtests, DCA και grid tools, paper wallet trading, paper bot loops, Kraken account tools, live order menus, order management, watchlists, crypto μαζί με stock/ETF monitoring, reports, journals, logs, mode switching, diagnostics και settings. Είναι φτιαγμένο για εκπαίδευση, οργάνωση και πιο ασφαλές paper testing· δεν είναι financial advice και δεν εγγυάται κέρδος.

Πρόβλημα που μου έλυσε: ήθελα ένα ενιαίο phone-friendly trading lab που κρατά τα πραγματικά χρήματα πίσω από προειδοποιήσεις, ενώ μου επιτρέπει να μελετάω αγορές, να δοκιμάζω στρατηγικές, να κρατάω journal αποφάσεων και να κάνω practice πρώτα με paper mode.

**Τοποθεσία Αποθήκευσης:** Κύριος φάκελος: ~/Kraken Trader/ | Config, paper wallet, watchlists, presets, alerts, baskets, DCA/grid assists, webhook logs, forward tests, reports, cache, journals, trade logs και error logs αποθηκεύονται μέσα σε αυτόν. Προαιρετικά report copies μπορούν να αποθηκευτούν στα Downloads αν ενεργοποιηθεί αυτή η επιλογή.

</details>

<details>
<summary>Noob Hacker.py</summary>


**Περιγραφή:** Το Noob Hacker.py είναι ασφαλές offline terminal learning game για Termux που μαθαίνει σε απόλυτους αρχάριους προγραμματισμό, βασικά Python, συνήθειες Termux/Bash, debugging, local-only cybersecurity thinking, defender workflows, report writing, projects, quizzes και playable practice games. Είναι φτιαγμένο ως ένα μόνο Python script, λειτουργεί χωρίς root, κρατά την εξάσκηση σε φανταστικά/local labs, περιλαμβάνει English και Greek εκδόσεις, υποστηρίζει self-tests, save migration, progress tracking και πολλά beginner-friendly μαθήματα που οδηγούν κάποιον από μηδενική γνώση σε πρακτικές ασφαλείς δεξιότητες. Δεν επιτίθεται σε πραγματικούς στόχους, δεν σαρώνει το internet, δεν κλέβει λογαριασμούς και δεν μαθαίνει malware.

Πρόβλημα που μου έλυσε: ήθελα ένα σοβαρό beginner-friendly learning game που μπορεί να μάθει κάποιον από το μηδέν χωρίς να τον στέλνει σε τυχαία unsafe tutorials. Παράδειγμα: ανοίγεις Termux, τρέχεις ένα Python αρχείο, ακολουθείς αργά μαθήματα, παίζεις ασφαλή practice games, μαθαίνεις Python/commands/debugging και χτίζεις αυτοπεποίθηση χωρίς να αγγίζεις πραγματικούς στόχους.

**Τοποθεσία Αποθήκευσης:** Κύριος φάκελος: ~/Noob Hacker/ | Save file: ~/Noob Hacker/save.json | Mission log: ~/Noob Hacker/mission_log.txt | CTF labs: ~/Noob Hacker/CTF_Labs/ | Exports: ~/Noob Hacker/Exports/

</details>


<a id="greek-butsystem"></a>

<h2>ButSystem.py (Αποκλειστικό)</h2>


Το **ButSystem.py** είναι ένα self-hosted, **local-first** workspace που τρέχει στη δική σου συσκευή μέσω Termux. Έχει σχεδιαστεί για να φέρνει ιδιωτική επικοινωνία, οργανωμένα αρχεία, έλεγχο πρόσβασης και structured profile workflows μέσα σε ένα browser interface αντί να τα σκορπίζει σε ξεχωριστά scripts και μενού.

Δεν είναι απλώς μια σελίδα chat. Το ButSystem ενώνει login και signup flow, user approval, device access control, remembered-device login, προαιρετικό 2FA με security questions, password recovery, direct messages, group chats, discussion space, stories, live-location sharing, file-vault navigation, profile editing, reports, admin controls και security settings σε ένα σημείο. Περιλαμβάνει επίσης την περιοχή **Profiler** για κρυπτογραφημένες profile entries, export και combine tools, bounty-related management όπου είναι ενεργό, chat PIN locks και το ενσωματωμένο **Face Detector** workflow που ταιριάζει μέσα στο ευρύτερο περιβάλλον του ButSystem.

Στην πράξη, τρέχεις το script, ανοίγεις το local link που δημιουργεί και κινείσαι μέσα στο σύστημα από το burger menu. Αυτό σου δίνει πιο καθαρό τρόπο να αλλάζεις ανάμεσα σε chats, groups, calls, files, profile pages, Profiler, reports, settings και admin tools χωρίς να βγαίνεις από το ίδιο local-first workspace.

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
