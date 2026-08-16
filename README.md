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


Step-by-step instructions to install and set up the DedSec Project on your Android device.

### Requirements

| Component | Minimum Specification |
| :-------- | :-------------------- |
| **Device** | Android phone or tablet with Termux installed |
| **Storage** | Minimum **8GB** free space |
| **RAM** | Minimum **2GB** |
| **Internet** | Needed for first installation and updates |

### Before You Start

F-Droid is an alternative app store for Android that provides free and open-source software. It's the recommended way to install Termux and other security tools.

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

The script will handle the complete installation. After setup, you must change the prompt, change the menu style (list or numbered menu styles are the best for new users), choose the language, and run the Save DedSec Project option on your first run so your backup package is created immediately. Save DedSec Project may take a while depending on your internet connection, and the terminal may stay blank until it is ready. Run Save DedSec Project again a few times every year to keep your saved DedSec Project package fresh and ready if you ever need it. After that, close Termux from your phone's notification panel using the exit button, then open Termux again. Tip: You can quickly open the menu by typing 'e' (English) or 'g' (Greek) in Termux.

##### 5. Complete the post-setup configuration

After setup finishes, do the following:

- change the **prompt**
- change the **menu style**
- for new users, **list** or **numbered** menu styles are the best choices
- choose your **language**
- run **Save DedSec Project** on your first run so your backup package is created immediately
- run **Save DedSec Project** again a few times every year to keep your saved package fresh and ready if you need it
- a manual **Save DedSec Project** operation may take a while depending on your internet connection, and the terminal may stay blank until it is ready
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

Run setup again so the consolidated dependency manager checks local files, updates dependencies, and opens the menu:

```bash
bash Setup.sh
```

To update dependencies without opening the menu, use:

```bash
bash Setup.sh --update-only
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
- Run **Save DedSec Project** on the first run, then run it again a few times every year to keep the saved package fresh. It may take a while depending on your internet connection.
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

Do not start by opening random scripts. The free Academy gives the project an order: setup first, then lessons, practice, and the next lesson.

- [Guide For Installation](https://ded-sec.space/Pages/guide-for-installation.html) — website path: `Pages/guide-for-installation.html`
- [Learn About The Tools](https://ded-sec.space/Pages/learn-about-the-tools.html) — website path: `Pages/learn-about-the-tools.html`
- [Assistance](https://ded-sec.space/Pages/assistance.html) — website path: `Pages/assistance.html`

Then download our free e-book:

- [Master Termux In 7 Days](https://ded-sec.space/Assets/Master%20Termux%20In%207%20Days%20English.pdf) — website path: `Assets/Master Termux In 7 Days English.pdf`

ButSystem is one of the project’s most distinctive all-in-one systems, built specifically for the DedSec Project ecosystem. Despite that exclusive positioning, the version documented here is available free through the project files and repository, with no separate Store purchase required.:

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
- **Update Packages & Modules:** runs the consolidated `Setup.sh --no-run` dependency routine, which checks local Termux packages and Python modules first, updates installed items, and downloads anything still missing without opening a second menu process.
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
4. run **Save DedSec Project** on your first run, then use it again whenever you want to refresh your backup
5. connect GitHub only if you want GitHub stats, prompt syncing, or Sponsors-Only access
6. enable or disable menu auto-start depending on how you use Termux
7. use **Update Packages & Modules** when dependencies need refreshing
8. use **VPN & Tor Utilities** only when you want those optional network controls

### Save Reminder

`Setup.sh` installs and verifies the project dependencies but does not create a backup automatically. Use **Save DedSec Project** from Settings on your first run and whenever you want to refresh the backup in your phone Downloads folder. A save may take a while depending on your internet connection, and the terminal may stay blank until it is ready.

</details>

<a id="explore-the-toolkit"></a>

<details>
<summary><strong>Explore The Toolkit</strong></summary>


This page is the map of the project: what each tool does, why it exists, and what real problem pushed me to build it. Start with the list, follow what catches your eye, and let the tools explain the project by themselves.

> **CRITICAL NOTICE:** The following scripts are included for **educational and defensive purposes only**. Their role is to help users understand how tools, lures, and simulations work so they can improve awareness, testing discipline, and self-protection in controlled environments.

### Toolkit Summary

- **Developer Base:** 11 tools
- **Network Tools:** 10 tools
- **Other Tools:** 5 tools
- **Games:** 6 tools
- **Personal Information Capture:** 17 tools
- **Social Media / Fake Pages:** 25 tools
- **No Category:** 3 tools
- **Sponsors-Only:** 6 tools in the $3 tier / 9 tools in the $9 tier

**Total listed on tools page:** 86 tools

---
<a id="developer-base"></a>

<h2>Developer Base</h2>


<details>
<summary>File Converter</summary>




**What It Helps With:** Converting images, documents, audio, video, and archives directly on Android when moving the job to a desktop would slow you down.

**Description:** A powerful file converter supporting 40+ formats. Organizes Downloads. Advanced interactive file converter for Termux using curses interface. Supports 40 different file formats across images, documents, audio, video, and archives. Features automatic dependency installation, organized folder structure, and comprehensive conversion capabilities. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Converted files are saved under /storage/emulated/0/Download/File Converter/, inside format folders such as JPG, PNG, PDF, MP3, MP4, ZIP, TXT, and others.`


</details>

<details>
<summary>File Type Checker</summary>




**What It Helps With:** Identifying what a file really is and checking suspicious characteristics before you trust or open it.

**Description:** Advanced file analysis and security scanner that detects file types, extracts metadata, calculates cryptographic hashes, and identifies potential threats. Features magic byte detection, entropy analysis, steganography detection, virus scanning via VirusTotal API, and automatic quarantine of suspicious files. Supports analysis of files up to 50GB. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Files are scanned in /sdcard/Download/File Type Checker/ on Termux, or ~/Downloads/File Type Checker/ outside Termux. Quarantined files stay in the same folder and are renamed with the .dangerous suffix.`


</details>

<details>
<summary>Mobile Desktop</summary>




**What It Helps With:** Running a Linux desktop-style environment from Termux without root when terminal-only apps are not enough.

**Description:** Termux Linux Desktop Manager (no root): sets up a proot-distro desktop environment with VNC/X11 options and a built-in program manager for install/update/remove. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Manager settings are stored in ~/.termux_linux_vnc_manager/config.json. Generated launchers are installed in $PREFIX/bin/ as vnc-<system>. The Linux distributions themselves are managed by proot-distro.`


</details>

<details>
<summary>Mobile Developer Setup</summary>




**What It Helps With:** Preparing a repeatable phone-first development environment instead of installing and configuring every dependency manually.

**Description:** Automates a mobile web-dev environment in Termux: installs common dev tools, configures paths, and provides quick-start project scaffolding. Built for Termux with clear prompts and organized outputs.

**Save Location:** `State and backup archives are stored in ~/.mobile-dev-setup/ (including backups/ and state.json). Helper scripts are stored in ~/.mobile-dev-setup-Tools/, plugins in ~/.zsh-plugins/, and Termux appearance files in ~/.termux/.`


</details>

<details>
<summary>Simple Websites Creator</summary>




**What It Helps With:** Building simple websites from a phone when you want a guided starting structure instead of creating every file by hand.

**Description:** A comprehensive website builder that creates responsive HTML websites with customizable layouts, colors, fonts, and SEO settings. Features include multiple hosting guides, real-time preview, mobile-friendly designs, and professional templates. Perfect for creating portfolios, business sites, or personal blogs directly from your terminal. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Created websites are saved in /storage/emulated/0/Download/Websites/.`


</details>

<details>
<summary>Smart Notes</summary>




**What It Helps With:** Keeping technical notes, ideas, commands, and project information organized while working from a phone.

**Description:** Terminal note-taking app with reminders. Advanced note-taking application with reminder functionality, featuring both TUI (Text User Interface) and CLI support. Includes sophisticated reminder system with due dates, automatic command execution, external editor integration, and comprehensive note organization capabilities. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Notes: ~/.smart_notes.json | Settings: ~/.smart_notes_config.json | Error log: ~/.smart_notes_error.log.`


</details>

<details>
<summary>Dead Man's Switch</summary>




**What It Helps With:** Preparing a user-confirmed emergency fallback workflow with trusted contacts, status files, and optional device data when a planned check-in does not happen.

**Description:** Termux emergency/SOS helper built around the I Need Help mode. After first-time setup and clear user confirmations, it can make the dead-mans-switch GitHub repository public, generate a GitHub Pages emergency website, upload organized emergency files, capture available camera photos, microphone recordings, and location updates at adjustable intervals through Termux:API permissions, and send SMS alerts with the website/repository link to configured trusted contacts. It also includes create/update uploads, overwrite sync, visibility controls, legacy repository migration, previous-history backups, logs, and a kill/cleanup option.

**Save Location:** `Main local folder: ~/storage/downloads/Dead Man's Switch/ (normally the phone Download folder; fallback /storage/emulated/0/Download/Dead Man's Switch/). Settings: ~/.dead_switch_settings.json. Logs and previous repository backups are stored inside the main folder under Logs/ and History/.`


</details>

<details>
<summary>Tree Explorer</summary>




**What It Helps With:** Understanding large folder and project structures quickly so you can find the file or directory you actually need.

**Description:** File-system explorer for Termux: browse folders, search files, find duplicates by hash, and clean empty directories with safe prompts. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Tree Explorer does not create a default results folder. Exports are written only to the path you choose with --export FILE or through the interactive export prompt. Installing the command copies it to $PREFIX/bin/supertree by default.`


</details>

<details>
<summary>Devices Finder</summary>




**What It Helps With:** Discovering and classifying devices on a local network you own or are authorized to inspect, without requiring root.

**Description:** Local-network device discovery tool for Termux that works without root. Separates live-host discovery from service scanning to reduce false positives, classifies devices using ports, banners, hostnames, and vendor hints, includes interactive scan profiles and type filters, and can optionally enrich results with mDNS, UPnP, SNMP, and NetBIOS clues. Exports JSON, TXT, CSV, and HTML reports. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Reports are saved in ~/storage/downloads/Devices Finder/ as devices_scan_<timestamp>.json, .txt, .csv, and .html. Fallbacks are ~/downloads/Devices Finder/ and then ./Devices Finder Output/.`


</details>

<details>
<summary>Free Internet</summary>




**What It Helps With:** Keeping browsing, saved pages, search, screenshots, and private vault data organized in one local-first Termux workflow.

**Description:** Local-first browser and secure vault for Termux. It combines multiple search engines, bookmarks, history, saved pages, ad/tracker cleanup, Lite mode, country-based proxy routing with smart/strict/direct modes, optional Tor support, encrypted vault entries powered by OpenSSL, and a built-in full-page website screenshot tool. Built for Termux with clear prompts and organized outputs.

**Save Location:** `On Termux, all data is stored in ~/Free Internet/; outside Termux it uses ~/.free_internet/. Browser data is in browser/, saved pages in browser/saved/, screenshots in Tools/screenshots/, and the encrypted vault database in vault/vault.db.`


</details>


<details>
<summary>DedSec's Server</summary>




**What It Helps With:** Sharing and managing large files from Termux through a controlled local/self-hosted server instead of relying on a third-party file host.

**Description:** Multi-server file hosting and management platform for Termux. It creates separate named server profiles with open guest access or administrator-only protection, multiple administrator accounts, uploads up to 30 GB with live chunked progress, folder creation and ZIP downloads, file moves, renames and deletions, categories, search, filters, sorting, details, comments, user sessions, and complete activity and security logs. Each server starts localhost and local-network access and automatically attempts to generate Cloudflare and Tor links. It also includes light and dark themes, separate English and Greek editions, confirmation prompts for changes, rate limiting, CSRF protection, storage-safety checks, and automatic dependency setup. Built for Termux with clear controls and organized storage.

**Save Location:** `All data is stored under ~/DedSec's Server/. The English and Greek editions use separate English/ and Greek/ folders. Server files are stored in <edition>/Servers/<server-id>/, configuration in <edition>/Config/config.json, temporary session data in <edition>/Runtime/, comments in <edition>/Comments/, and each server's audit logs in its hidden .dedsec-server/logs/ folder.`


</details>


<a id="network-tools"></a>

<h2>Network Tools</h2>


<details>
<summary>Bug Hunter</summary>




**What It Helps With:** Organizing authorized web-security reconnaissance and misconfiguration checks into one repeatable audit workflow.

**Description:** Bug Hunter (no-root) — an authorized web security recon & misconfiguration scanner. Audits security headers and cookie flags, fingerprints technologies, checks DNS (SPF/DMARC/CAA), analyzes TLS/certificate expiry, tests CORS and HTTP methods, finds exposed sensitive files, crawls the site, and analyzes JavaScript for endpoints and leaked secrets. Includes optional directory discovery and Wayback URL recon, plus de-duplicated reports (JSON/CSV/HTML/PDF). Use only on targets you own or have explicit permission to test.

**Save Location:** `The default output folder is ./bughunter_out/ in the directory where the script is run. Use --output PATH to choose another folder. Reports include report.json, report.csv, report.html, optional report.pdf, and optional live/checkpoint files.`


</details>

<details>
<summary>Dark</summary>




**What It Helps With:** Collecting and organizing public Tor/.onion OSINT in authorized research without manually visiting and recording every result.

**Description:** A specialized Dark Web OSINT tool and crawler designed for Tor network analysis. It features automated Tor connectivity, an Ahmia search integration, and a recursive crawler for .onion sites. The tool utilizes a modular plugin system to extract specific data types (Emails, BTC/XMR addresses, PGP keys, Phones) and supports saving snapshots. It offers both a Curses TUI and CLI mode, with results exportable to JSON, CSV, and TXT. Use only on systems you own or have explicit permission to test.

**Save Location:** `Results are stored in /sdcard/Download/DarkNet/ with fallback to ~/DarkNet/. JSON, CSV, TXT, snapshots, and plugin output are written there; plugins are stored in its plugins/ subfolder.`


</details>

<details>
<summary>DedSec's Network</summary>




**What It Helps With:** Combining common network diagnostics, OSINT, downloading, and authorized web-audit tasks so you do not need a separate script for each check.

**Description:** An advanced, non-root network toolkit optimized for speed and stability. Features a recursive website downloader with ZIP support, multi-threaded port scanner, internet speed testing, subnet calculator, and extensive OSINT tools (WHOIS, DNS, Reverse IP, Subdomain Enum). Includes web auditing scanners for SQLi, XSS, CMS detection, and SSH brute-forcing. Maintains a local SQLite audit log. Use only on systems you own or have explicit permission to test.

**Save Location:** `Configuration, audit_results.db, and wordlists are stored in ~/DedSec's Network/ on Termux, or ./DedSec's Network/ elsewhere. Downloaded websites go to /storage/emulated/0/Download/Websites/<domain>/, with fallbacks to /sdcard/Download/Websites/, ~/DedSec's Network/Websites/, or ~/Downloads/Websites/ outside Termux.`


</details>

<details>
<summary>Digital Footprint Finder</summary>




**What It Helps With:** Checking where a username appears publicly while reducing obvious false positives and keeping the results exportable.

**Description:** Conservative OSINT username checker built for best practical results with low false-positives. Scans a large site list via packs (core/extended) with optional Sherlock database, using multi-signal scoring (status/redirects, title/meta/canonical/text) and per-domain concurrency limits for stability. Detects anti-bot/JS challenges as POSSIBLE (never falsely FOUND), supports optional search-engine dorking, and can import/export custom site lists. Exports reports to TXT/JSON/CSV and optional HTML. Use only on systems you own or have explicit permission to test.

**Save Location:** `Reports are stored in ~/storage/downloads/Digital Footprint Finder/. If that path is unavailable, the script falls back to /sdcard/Download/Digital Footprint Finder/, then ~/Digital Footprint Finder/, then the current directory. Files use <username>_<timestamp>.txt, with optional .json, .csv, and .html exports.`


</details>

<details>
<summary>Connections.py</summary>




**What It Helps With:** Running your own authenticated chat, video-call, and file-sharing space from Termux with server-enforced message ownership and access controls.

**Description:** Self-hosted Connections server for Termux combining real-time chat, WebRTC video calls, chunked file sharing, and DedSec's Database in one authenticated interface. Supports files up to 150 MB, a strong automatically generated one-time secret key, Cloudflare and Tor access, rate limiting, CSRF-protected Database actions, server-controlled identities and message ownership, and moderator controls where the first user to join can delete any message while other users can delete or edit only their own. Chat files are transferred in protected chunks instead of oversized Socket.IO/Base64 messages, and LAN exposure is disabled by default unless explicitly enabled. Use only on systems and networks you own or are authorized to operate.

**Save Location:** `Shared files are stored in ~/Downloads/DedSec's Database/. If that folder cannot be created, the fallback is ./DedSec_Database_Files/ in the current directory. Tor runtime data is stored separately in ~/.foxchat_tor/.`


</details>

<details>
<summary>Link Shield</summary>




**What It Helps With:** Inspecting redirects, HTTPS, domains, and suspicious URL patterns before opening an unfamiliar link.

**Description:** Security-focused URL inspector: follows redirects, checks HTTPS/SSL, flags suspicious domains/patterns, and generates a risk report before you open a link. Use only on systems you own or have explicit permission to test.

**Save Location:** `No dedicated output folder is created. linkshield_config_en.json, user-named JSON/Markdown reports, and linkshield_batch_report.json/.csv are saved in the current working directory.`


</details>

<details>
<summary>Masker</summary>




**What It Helps With:** Creating readable test links and checking redirect behavior for your own demos and authorized awareness workflows.

**Description:** URL helper for creating clean, readable test links and checking redirect behavior in your own workflows. It is presented for organization, demos, and authorized awareness training only, never to disguise harmful links or trick people.

**Save Location:** `No files are saved. The generated masked URL is printed in the terminal.`


</details>

<details>
<summary>QR Code Generator</summary>




**What It Helps With:** Turning text or links into QR codes quickly from Termux for sharing, testing, or printed workflows.

**Description:** Python-based QR code generator that creates QR codes for URLs and saves them in the Downloads/QR Codes folder. Features automatic dependency installation, user-friendly interface, and error handling for reliable operation. Use only on systems you own or have explicit permission to test.

**Save Location:** `Generated PNG images are saved in ~/storage/downloads/QR Codes/.`


</details>

<details>
<summary>Sod</summary>




**What It Helps With:** Measuring how an application you control behaves under load so performance limits can be found before real users hit them.

**Description:** A comprehensive load testing tool for web applications, featuring multiple testing methods (HTTP, WebSocket, database simulation, file upload, mixed workload), real-time metrics, and auto-dependency installation. Advanced performance testing framework with realistic user behavior simulation, detailed analytics, and system resource monitoring. Use only on systems you own or have explicit permission to test.

**Save Location:** `The configuration file load_test_config.json is saved in the current working directory. Test results are displayed in the terminal and are not written to a report file.`


</details>

<details>
<summary>Store Scrapper</summary>




**What It Helps With:** Extracting and organizing public product/category data from stores you are allowed to analyze instead of collecting it manually page by page.

**Description:** Single-file Python store scraper for Termux that works without root. Tries multiple ways to discover categories and products across regular HTML pages and many JS-style stores by reading HTML, JSON-LD, embedded JSON, sitemaps, Shopify endpoints, WooCommerce APIs, generic product cards, breadcrumbs, OpenGraph/meta tags, and internal links. Saves while running, starts full product scraping the moment each product is found, shows live terminal status, uses Enter as the default for prompts, and organizes results into store/category/product folders with downloaded images. Use only on systems you own or have explicit permission to test.

**Save Location:** `Product data is saved under ~/storage/downloads/Store Scrapper/<Store>/<Category>/<Product>/. If Termux Downloads is unavailable, it uses ~/downloads/Store Scrapper/. Product folders can contain FOUND.txt, metadata.json, summary.txt, description.txt, images/, and images.json; discovery and run-state files are stored in the store output tree.`


</details>


<a id="personal-information-capture-educational-use-only"></a>

<h2>Personal Information Capture (Educational Use Only)</h2>


These scripts are training simulations intended to help users understand how deceptive personal-data collection pages may be presented, so they can better recognize and defend against them in controlled environments.

<details>
<summary>Fake Back Camera Page</summary>




**What It Helps With:** Running authorized awareness demonstrations that show how deceptive pages may request camera access, so permission prompts and social-engineering risks are easier to recognize.

**Description:** Fake Back Camera Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Back Camera. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Captured back-camera images and related text data are saved in ~/storage/downloads/Camera-Phish-Back/.`


</details>

<details>
<summary>Fake Back Camera Video Page</summary>




**What It Helps With:** Running authorized awareness demonstrations that show how deceptive pages may request camera access, so permission prompts and social-engineering risks are easier to recognize.

**Description:** Fake Back Camera Video Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Back Camera Video. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Recorded back-camera WEBM videos and related text data are saved in ~/storage/downloads/Back Camera Videos/.`


</details>

<details>
<summary>Fake Card Details Page</summary>




**What It Helps With:** Demonstrating in an authorized lab how fake verification/data-entry flows can pressure users into sharing sensitive information, so those patterns are easier to recognize.

**Description:** Fake Card Details Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Card Details. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Submitted card-activation data is saved in ~/storage/downloads/CardActivations/.`


</details>

<details>
<summary>Fake Chrome Verification Page</summary>




**What It Helps With:** Demonstrating in an authorized lab how fake verification/data-entry flows can pressure users into sharing sensitive information, so those patterns are easier to recognize.

**Description:** Fake Chrome Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Chrome Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Chrome verification output, including location JSON, face video, device scan, system information, and summaries, is saved in ~/storage/downloads/Chrome Verification/.`


</details>

<details>
<summary>Fake Data Grabber Page</summary>




**What It Helps With:** Demonstrating in an authorized lab how fake verification/data-entry flows can pressure users into sharing sensitive information, so those patterns are easier to recognize.

**Description:** Fake Data Grabber Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Data Grabber. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Collected application information is saved under ~/storage/downloads/Peoples_Lives/, including application_info.txt.`


</details>

<details>
<summary>Fake Discord Verification Page</summary>




**What It Helps With:** Demonstrating in an authorized lab how fake verification/data-entry flows can pressure users into sharing sensitive information, so those patterns are easier to recognize.

**Description:** Fake Discord Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Discord Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Discord verification output, including location JSON, face video, ID, phone, payment, and summary files, is saved in ~/storage/downloads/Discord Verification/.`


</details>

<details>
<summary>Fake Facebook Verification Page</summary>




**What It Helps With:** Demonstrating in an authorized lab how fake verification/data-entry flows can pressure users into sharing sensitive information, so those patterns are easier to recognize.

**Description:** Fake Facebook Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Facebook Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Facebook verification output, including location JSON, face video, ID images, and summary files, is saved in ~/storage/downloads/Facebook Verification/.`


</details>

<details>
<summary>Fake Front Camera Page</summary>




**What It Helps With:** Running authorized awareness demonstrations that show how deceptive pages may request camera access, so permission prompts and social-engineering risks are easier to recognize.

**Description:** Fake Front Camera Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Front Camera. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Captured front-camera images and related text data are saved in ~/storage/downloads/Camera-Phish-Front/.`


</details>

<details>
<summary>Fake Front Camera Video Page</summary>




**What It Helps With:** Running authorized awareness demonstrations that show how deceptive pages may request camera access, so permission prompts and social-engineering risks are easier to recognize.

**Description:** Fake Front Camera Video Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Front Camera Video. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Recorded front-camera WEBM videos and related text data are saved in ~/storage/downloads/Front Camera Videos/.`


</details>

<details>
<summary>Fake Google Location Page</summary>




**What It Helps With:** Running authorized awareness demonstrations that show how deceptive pages may request or expose location data.

**Description:** Fake Google Location Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Google Location. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Location JSON files are saved in ~/storage/downloads/Locations/.`


</details>

<details>
<summary>Fake Instagram Verification Page</summary>




**What It Helps With:** Demonstrating in an authorized lab how fake verification/data-entry flows can pressure users into sharing sensitive information, so those patterns are easier to recognize.

**Description:** Fake Instagram Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Instagram Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Instagram verification output, including location JSON, face video, voice audio, ID documents, and summary files, is saved in ~/storage/downloads/Instagram Verification/.`


</details>

<details>
<summary>Fake Location Page</summary>




**What It Helps With:** Running authorized awareness demonstrations that show how deceptive pages may request or expose location data.

**Description:** Fake Location Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Location. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Location JSON files are saved in ~/storage/downloads/Locations/.`


</details>

<details>
<summary>Fake Microphone Page</summary>




**What It Helps With:** Running authorized awareness demonstrations that show how deceptive pages may request microphone access.

**Description:** Fake Microphone Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Microphone. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Recorded audio, converted WAV files, and related text data are saved in ~/storage/downloads/Recordings/.`


</details>

<details>
<summary>Fake OnlyFans Verification Page</summary>




**What It Helps With:** Demonstrating in an authorized lab how fake verification/data-entry flows can pressure users into sharing sensitive information, so those patterns are easier to recognize.

**Description:** Fake OnlyFans Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around OnlyFans Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `OnlyFans verification output, including location JSON, face video, ID, payment, and summary files, is saved in ~/storage/downloads/OnlyFans Verification/.`


</details>

<details>
<summary>Fake Steam Verification Page</summary>




**What It Helps With:** Demonstrating in an authorized lab how fake verification/data-entry flows can pressure users into sharing sensitive information, so those patterns are easier to recognize.

**Description:** Fake Steam Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Steam Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Steam verification output, including location JSON, face video, ID, Steam Guard, phone, payment, and summary files, is saved in ~/storage/downloads/Steam Verification/.`


</details>

<details>
<summary>Fake Twitch Verification Page</summary>




**What It Helps With:** Demonstrating in an authorized lab how fake verification/data-entry flows can pressure users into sharing sensitive information, so those patterns are easier to recognize.

**Description:** Fake Twitch Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around Twitch Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `Twitch verification output, including location JSON, face video, ID, payment, and summary files, is saved in ~/storage/downloads/Twitch Verification/.`


</details>

<details>
<summary>Fake YouTube Verification Page</summary>




**What It Helps With:** Demonstrating in an authorized lab how fake verification/data-entry flows can pressure users into sharing sensitive information, so those patterns are easier to recognize.

**Description:** Fake YouTube Verification Page is a consent-based awareness demo for teaching how deceptive permission prompts can pressure people into sharing sensitive access around YouTube Verification. Use it only in a lab, with dummy data, screenshots, or clear permission from participants. It is not presented as a tool for stealing information.

**Save Location:** `YouTube verification output, including location JSON, face video, ID, payment, and summary files, is saved in ~/storage/downloads/YouTube Verification/.`


</details>


<a id="fake-pages-educational-use-only"></a>

<h2>Fake Pages (Educational Use Only)</h2>


These scripts are educational simulations intended to help users recognize social-engineering patterns, fake reward pages, fake verification flows, and imitation brand pages often used to pressure people into unsafe actions.

<details>
<summary>Fake Apple iCloud Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake Apple iCloud Page is a mock phishing-awareness page for teaching how fake Apple iCloud offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Apple iCloud/.`


</details>

<details>
<summary>Fake Discord Nitro Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake Discord Nitro Page is a mock phishing-awareness page for teaching how fake Discord Nitro offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Discord Nitro/.`


</details>

<details>
<summary>Fake Epic Games Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake Epic Games Page is a mock phishing-awareness page for teaching how fake Epic Games offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Epic Games/.`


</details>

<details>
<summary>Fake Facebook Friends Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake Facebook Friends Page is a mock phishing-awareness page for teaching how fake Facebook Friends offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Facebook Friends/.`


</details>

<details>
<summary>Fake Free Robux Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake Free Robux Page is a mock phishing-awareness page for teaching how fake Free Robux offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Roblox Robux/.`


</details>

<details>
<summary>Fake GitHub Pro Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake GitHub Pro Page is a mock phishing-awareness page for teaching how fake GitHub Pro offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/GitHub Pro/.`


</details>

<details>
<summary>Fake Google Free Money Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake Google Free Money Page is a mock phishing-awareness page for teaching how fake Google Free Money offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Google Free Money/.`


</details>

<details>
<summary>Fake Instagram Followers Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake Instagram Followers Page is a mock phishing-awareness page for teaching how fake Instagram Followers offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Instagram Followers/.`


</details>

<details>
<summary>Fake MetaMask Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake MetaMask Page is a mock phishing-awareness page for teaching how fake MetaMask offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/MetaMask/.`


</details>

<details>
<summary>Fake Microsoft 365 Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake Microsoft 365 Page is a mock phishing-awareness page for teaching how fake Microsoft 365 offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Microsoft 365/.`


</details>

<details>
<summary>Fake OnlyFans Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake OnlyFans Page is a mock phishing-awareness page for teaching how fake OnlyFans offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/OnlyFans/.`


</details>

<details>
<summary>Fake PayPal Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake PayPal Page is a mock phishing-awareness page for teaching how fake PayPal offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form and card data is written to ~/storage/downloads/PayPal/.`


</details>

<details>
<summary>Fake Pinterest Pro Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake Pinterest Pro Page is a mock phishing-awareness page for teaching how fake Pinterest Pro offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Pinterest Pro/.`


</details>

<details>
<summary>Fake PlayStation Network Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake PlayStation Network Page is a mock phishing-awareness page for teaching how fake PlayStation Network offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/PlayStation Network/.`


</details>

<details>
<summary>Fake Reddit Karma Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake Reddit Karma Page is a mock phishing-awareness page for teaching how fake Reddit Karma offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Reddit Karma/.`


</details>

<details>
<summary>Fake Snapchat Friends Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake Snapchat Friends Page is a mock phishing-awareness page for teaching how fake Snapchat Friends offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Snapchat Friends/.`


</details>

<details>
<summary>Fake Steam Games Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake Steam Games Page is a mock phishing-awareness page for teaching how fake Steam Games offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Steam Games/.`


</details>

<details>
<summary>Fake Steam Wallet Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake Steam Wallet Page is a mock phishing-awareness page for teaching how fake Steam Wallet offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Steam Wallet/.`


</details>

<details>
<summary>Fake TikTok Followers Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake TikTok Followers Page is a mock phishing-awareness page for teaching how fake TikTok Followers offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/TikTok Followers/.`


</details>

<details>
<summary>Fake Trust Wallet Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake Trust Wallet Page is a mock phishing-awareness page for teaching how fake Trust Wallet offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Trust Wallet/.`


</details>

<details>
<summary>Fake Twitch Subs Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake Twitch Subs Page is a mock phishing-awareness page for teaching how fake Twitch Subs offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Twitch Subs/.`


</details>

<details>
<summary>Fake Twitter Followers Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake Twitter Followers Page is a mock phishing-awareness page for teaching how fake Twitter Followers offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Twitter Followers/.`


</details>

<details>
<summary>Fake What's Up Dude Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake What's Up Dude Page is a mock phishing-awareness page for teaching how fake What's Up Dude offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/WhatsUp Dude/.`


</details>

<details>
<summary>Fake Xbox Live Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake Xbox Live Page is a mock phishing-awareness page for teaching how fake Xbox Live offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/Xbox Live/.`


</details>

<details>
<summary>Fake YouTube Subscribers Page</summary>




**What It Helps With:** Demonstrating in an authorized phishing-awareness lab how a convincing look-alike offer or login page can mislead users.

**Description:** Fake YouTube Subscribers Page is a mock phishing-awareness page for teaching how fake YouTube Subscribers offers, giveaways, upgrades, or login prompts manipulate trust. Use it only for education, screenshots, or consent-based training with dummy accounts. Never use it to collect real credentials, cards, wallets, or private information.

**Save Location:** `Saved form data is written to ~/storage/downloads/YouTube Subscribers/.`


</details>


<a id="games"></a>

<h2>Games</h2>


<details>
<summary>Buzz</summary>




**What It Helps With:** Practicing programming logic, terminal interaction, and project structure through a playable local experience.

**Description:** A text-only trivia party game for Termux with a fixed built-in database of 15,000 questions (no runtime generation). Supports 1–2 players (pass-and-play), multiple round types, difficulty filtering (All/Easy/Medium/Hard), profiles, settings, and highscores. Lightweight terminal game with quick controls and replay value.

**Save Location:** `All game data is stored in ~/Buzz/data/: questions_en.jsonl.gz, highscores.json, profiles.json, and settings.json.`


</details>

<details>
<summary>CTF God</summary>




**What It Helps With:** Practicing programming logic, terminal interaction, and project structure through a playable local experience.

**Description:** Full‑screen Curses CTF game for Termux with story mode, missions, daily challenges, random boss levels, hint shop economy, achievements & ranks, challenge pack import/export, tournament mode, and anti‑cheat/integrity checks. Includes a built‑in level editor. Lightweight terminal game with quick controls and replay value.

**Save Location:** `Challenge workspaces are stored in /storage/emulated/0/Download/CTF God/; fallback paths are ~/storage/downloads/CTF God/ and ~/CTF God/. Profiles, progress, packs, and custom challenges are stored in ~/.ctf_god/ (state.json, custom.json, packs/).`


</details>

<details>
<summary>Detective</summary>




**What It Helps With:** Practicing programming logic, terminal interaction, and project structure through a playable local experience.

**Description:** A story-driven Terminal detective game for Termux with an expanded fixed case library, richer lore dossiers, district rumors, side stories, and bonus story threads. Track evidence, interrogate suspects, review suspect rosters, build an ASCII case board and timeline, and manage progress with 3 save slots plus autosave. Includes 4 difficulties, note/evidence tracking, checkpoint hints, and quick commands like :help, :guide, :lore, :suspects, :board, :timeline, :hint, and :save.

**Save Location:** `All saves are stored in ~/Detective/: player.json, highscores.json, and savegame_slot1.json through savegame_slot3.json.`


</details>

<details>
<summary>Tamagotchi</summary>




**What It Helps With:** Practicing programming logic, terminal interaction, and project structure through a playable local experience.

**Description:** A fully featured terminal pet game. Feed, play, clean, and train your pet. Don't let it die. Advanced virtual pet simulation game with comprehensive pet management system. Features include pet evolution through life stages (Egg, Child, Teen, Adult, Elder), personality traits, skill development, mini-games, job system, and legacy retirement. Includes detailed statistics tracking. Lightweight terminal game with quick controls and replay value.

**Save Location:** `The Tamagotchi save is stored in ~/.termux_tamagotchi_v8.json.`


</details>

<details>
<summary>Pet Friends</summary>




**What It Helps With:** Practicing programming logic, terminal interaction, and project structure through a playable local experience.

**Description:** Pet Friends.py is a full-screen idle virtual-companion game for Termux with 160+ real, legendary, and mythical pets. Adopt, feed, pet, bathe, train, bond with, rename, recolor, and evolve companions while completing quests, contracts, expeditions, achievements, festivals, adventure-board progress, and rarity-based crates. It includes animated ASCII pets, locally generated sound effects and continuous background music, educational species facts with mythology clearly labelled, economy and upgrades, care requests, local-network battles and trades, and persistent progress without third-party Python packages.

**Save Location:** `Game progress is saved in ~/Pet Friends/petfriends_save.json. Generated sound effects and background music are stored in ~/Pet Friends/sounds/.`


</details>

<details>
<summary>Terminal Arcade</summary>




**What It Helps With:** Practicing programming logic, terminal interaction, and project structure through a playable local experience.

**Description:** All-in-one terminal arcade pack with multiple mini-games in a single script. Saves data in ~/Terminal Arcade/ and runs smoothly on Termux/Linux terminals. Lightweight terminal game with quick controls and replay value.

**Save Location:** `Arcade data is stored in ~/Terminal Arcade/. High scores and recent score history are saved in ~/Terminal Arcade/highscores.json.`


</details>


<a id="other-tools"></a>

<h2>Other Tools</h2>


<details>
<summary>Android App Launcher</summary>




**What It Helps With:** Launching and organizing Android apps from a Termux-centered workflow when you want quicker access from the terminal.

**Description:** A utility to manage Android apps directly from the terminal. It can launch apps, extract APK files, uninstall apps, and analyze security permissions. Advanced Android application management and security analysis tool. Features include app launching, APK extraction, permission inspection, security analysis, and tracker detection. Includes comprehensive security reporting for installed applications. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Extracted APK files are saved in ~/storage/shared/Download/Extracted APK's/. Security reports are saved in ~/storage/shared/Download/App_Security_Reports/ as <app>_security_report.txt.`


</details>

<details>
<summary>Loading Screen</summary>




**What It Helps With:** Adding a reusable loading/transition experience to local projects so long startup steps feel clearer to the user.

**Description:** Customize your Termux startup with ASCII art loading screens. Supports custom art, delay timers, and automated setup/cleanup for one-time display. Built for Termux with clear prompts and organized outputs.

**Save Location:** `No separate output folder is created. The selected loading screen is written directly into ~/.bash_profile.`


</details>

<details>
<summary>Password Master</summary>




**What It Helps With:** Creating and managing stronger password-generation/checking workflows instead of relying on memorable but weak patterns.

**Description:** Comprehensive password management suite featuring encrypted vault storage, password generation, strength analysis, and improvement tools. Includes AES-256 encrypted vault with master password protection, random password generator, passphrase generator, password strength analyzer, and password improvement suggestions. Features clipboard integration. Built for Termux with clear prompts and organized outputs.

**Save Location:** `The encrypted vault is saved as ./my_vault.enc in the current working directory. Backups are saved in /storage/emulated/0/Download/Password Master Backup/vault_backup.enc, or ~/Downloads/Password Master Backup/ outside Android.`


</details>

<details>
<summary>Termux Backup Restore</summary>




**What It Helps With:** Backing up and restoring Termux project files before updates, migrations, or risky changes.

**Description:** Backup & restore for Termux: creates a zipped backup of your Termux files to Downloads and can restore them with integrity checks. Built for Termux with clear prompts and organized outputs.

**Save Location:** `The backup archive is saved as /storage/emulated/0/Download/name_backup.zip. Split parts are created beside that archive. backup_config.json is stored in the current working directory.`


</details>

<details>
<summary>Termux Repair Wizard</summary>




**What It Helps With:** Diagnosing common Termux setup/package problems through a guided repair flow instead of trying random commands.

**Description:** DedSec Termux Repair Wizard is a no-root diagnostic and repair suite for repository and mirror errors, apt/dpkg failures, storage access, permissions, TLS certificates, caches, Python/pip, and shell/PATH problems. Its Script Keeper scans one script or an entire folder without directly launching the scripts, recognizes more than 20 languages plus extensionless shebang files, checks syntax, runtimes, commands, imports, modules, and common project manifests, and can install missing Termux and language-specific dependencies after confirmation. For newer Python releases, it also tries compatible replacement packages for removed standard-library modules. Every Script Keeper run produces a categorized report of installed items, fixes, warnings, failures, and syntax issues.

**Save Location:** `Most repairs are applied directly to Termux packages, storage permissions, $HOME permissions, and shell files such as ~/.bashrc, ~/.profile, and ~/.zshrc. Script Keeper reports are saved as ~/DedSec/logs/script_keeper_<timestamp>.log.`


</details>


<a id="no-category"></a>

<h2>No Category</h2>


<details>
<summary>Extra Content</summary>




**What It Helps With:** Finding optional resources, templates, and bonus material without searching through the repository manually.

**Description:** Extra bonus content hub: quick access to additional resources, templates, and optional add-ons included in the DedSec toolkit. Built for Termux with clear prompts and organized outputs.

**Save Location:** `The repository Extra Content folder is copied to ~/storage/downloads/Extra Content/.`


</details>

<details>
<summary>Settings.py</summary>




**What It Helps With:** Controlling updates, menus, language, backups, GitHub connection, sponsor scripts, and other DedSec Project settings from one launcher.

**Description:** Settings.py is the central control panel for the DedSec Project. It shows project and device information; updates the project from the main or backup source; refreshes Termux packages and Python modules; checks and downloads Sponsors-Only scripts through a connected GitHub account; creates a DedSec Project backup in Downloads; changes the Termux prompt; connects or disconnects GitHub; shows GitHub stats; syncs the prompt with the GitHub username; scans Termux usage stats; manages optional VPN and Tor utilities; switches between List, Grid, Choose By Number, and DedSec OS menu styles; controls menu auto-start; saves the English or Greek language choice; displays credits; and safely uninstalls the project. DedSec OS adds a browser-based local workspace with a file browser, safe text editor, terminal view, session manager, DedSec apps launcher, Linux package store actions, notifications, fullscreen and split-view controls, sidebar controls, wallpaper support, display name settings, terminal color settings, project action buttons, language controls, prompt controls, password login, optional authenticator-style 2FA, and recovery through three security questions. Built for Termux with clear prompts and organized outputs.

**Save Location:** `Language: ~/Language.json | Termux configuration backup: ~/Termux.zip | Project archive: /storage/emulated/0/Download/DedSec Project Legacy Save.zip | GitHub account: ~/.dedsec_github_account.json | Usage stats: ~/.dedsec_termux_usage_stats.json | Network utility data: ~/.dedsec_network_utilities/ and ~/.dedsec_network_utilities.json.`


</details>

<details>
<summary>DedSec Market</summary>




**What It Helps With:** Browsing, installing, updating, and launching supported GitHub projects from a phone-friendly Termux interface.

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




**What It Helps With:** Experimenting with face detection on permitted images or camera input as a sponsor-only computer-vision tool.

**Description:** Local browser-based face analysis tool for Termux that works without root. It uses MediaPipe Face Mesh on the live camera feed, supports both front and back camera, tracks up to 3 faces, draws detailed facial landmark overlays instead of simple boxes, and also lets you upload photos or videos for analysis directly from the interface. It can capture PNG snapshots, record WEBM video, save cropped detected faces separately, and provide both a local network link and an optional Cloudflare public link.

**Save Location:** `On Termux, captures, recordings, uploaded results, and saved face crops are stored in: ~/storage/downloads/Face Detector/. If Termux storage is unavailable, it falls back to ~/Face Detector/. On non-Termux systems it uses ~/Downloads/Face Detector/, with fallback to ~/Face Detector/. Internal web files, certificates, and helper binaries are stored in ~/.face_detector_studio/.`


</details>

<details>
<summary>Face Detector Heavy.py</summary>




**What It Helps With:** Running a heavier face-detection workflow when you need more processing options and your device can handle the extra load.

**Description:** Expanded heavy-analysis version of the face detector for Termux, built without root. Along with live camera use, front/back camera switching, photo and video uploads, PNG snapshots, WEBM recording, and saved face crops, it raises tracking up to 30 faces and adds TensorFlow COCO-SSD object detection on top of the MediaPipe face mesh pipeline. It shows richer on-screen telemetry such as face count, animal/object detection, pose and gaze estimates, facial proportions, mouth and brow state, asymmetry scoring, and other visual analysis details, while still supporting both a local network link and an optional Cloudflare public link.

**Save Location:** `On Termux, captures, recordings, uploaded results, and saved face crops are stored in: ~/storage/downloads/Face Detector/. If Termux storage is unavailable, it falls back to ~/Face Detector/. On non-Termux systems it uses ~/Downloads/Face Detector/, with fallback to ~/Face Detector/. Internal web files, certificates, and helper binaries are stored in ~/.face_detector_studio/.`


</details>

<details>
<summary>Face Swap.py</summary>




**What It Helps With:** Testing face-swap image transformation on media you have permission to use.

**Description:** Local browser-based face swap tool for Termux that works without root. It opens a local camera page, lets you upload a source face image, switch between the front and back camera, and blend the uploaded face over the live camera using MediaPipe Face Mesh. The current version focuses on a smooth face-lock approach: it locks the uploaded face once, follows the live face, moves key feature patches for expressions, includes smoothing, feathering, opacity, blend, and skin-tone matching controls, and can save PNG snapshots from the browser. Use it only with your own images or with clear permission.

**Save Location:** `On Termux, saved photos are stored in: /storage/emulated/0/Download/Face Swap/ or ~/storage/downloads/Face Swap/, with fallback to ~/Face Swap/. On non-Termux systems it uses ~/Downloads/Face Swap/, with fallback to ~/Face Swap/.`


</details>

<details>
<summary>Steganography.py</summary>




**What It Helps With:** Learning how data can be hidden in and recovered from files for authorized security and forensic practice.

**Description:** Password-based steganography suite for Termux. It can generate random black-and-white PNG carrier images, encrypt secret text with a password-derived Fernet key, hide the encrypted text inside PNG images using LSB steganography, and batch-decode hidden messages from all images placed in the Decrypt folder. Extracted messages are automatically saved as separate .txt files, and the script can also optionally clean processed images from the decode folder after scanning.

**Save Location:** `Main folder: /storage/emulated/0/Download/Steganography/ | Carrier/output images: /Encrypt | Images to scan for hidden messages: /Decrypt | Extracted text files: /Decrypted Texts.`


</details>

<details>
<summary>AR Terror.py</summary>




**What It Helps With:** Exploring local browser-based AR effects, camera interaction, recording, and immersive storytelling from Termux.

**Description:** Local browser-based AR horror experience for Termux that works without root. It launches a full-screen camera-driven web page where you explore the environment, collect hidden logs into an archive/inventory system, use atmospheric visual and audio effects, switch between front and back camera, and record evidence as WEBM while the experience runs. It can also expose both a local network link and an optional Cloudflare public link.

**Save Location:** `On Termux, recorded evidence is saved in: ~/storage/downloads/AR Terror/. If Termux storage is unavailable, it falls back to ~/AR Terror/. On non-Termux systems it uses ~/Downloads/AR Terror/, with fallback to ~/AR Terror/. Internal web files, certificates, and helper binaries are stored in ~/.ar_terror_studio/.`


</details>

<details>
<summary>Login Stealer.py</summary>




**What It Helps With:** Demonstrating credential-capture risk in a controlled, explicitly authorized awareness lab so users can recognize deceptive login flows.

**Description:** Login Stealer.py is a fully working controlled login-security simulation tool for Termux that helps demonstrate how fake login pages, copied authentication screens, redirects, session behavior, and verification-style traps can make users trust the wrong page. It is built for awareness training, lab demonstrations, screenshots, and dummy-account testing so beginners can understand how phishing-style login tricks look before they fall for them in real life. It should be used only with dummy data, test accounts, or clear permission-based demonstrations, and it is not presented as a tool for stealing real accounts, private credentials, cookies, cards, wallets, or personal information.

**Save Location:** `Main folder: /storage/emulated/0/Download/Login Stealer/ | Use only dummy data, test accounts, or permission-based lab demonstrations.`


</details>

<details>
<summary>Widget Maker.py</summary>




**What It Helps With:** Creating reusable phone/Termux widgets so common commands or project actions are easier to launch.

**Description:** DedSec Widget Maker is a no-root Termux helper that creates Android home-screen launchers for DedSec Project scripts through Termux:Widget. It recursively scans Termux home, shared storage, and common phone folders for DedSec, sponsor, exclusive, and related Python scripts, including scripts inside every accessible folder and subfolder. It then creates managed shortcuts in ~/.shortcuts. Each widget opens a small menu with Run, Show Script Path, and Exit, validates the Python file before launching it, keeps a manifest in ~/.dedsec_widget_maker/, and can update or delete all managed widgets when your script collection changes.

**Save Location:** `Managed widget launchers are created in: ~/.shortcuts/ | State and manifest are stored in: ~/.dedsec_widget_maker/manifest.json. The original scripts are not moved; each widget points back to the detected source file.`


</details>

<details>
<summary>Kraken Trader.py</summary>




**What It Helps With:** Researching markets, paper-testing strategies, recording trades, and organizing risk calculations before considering any live action.

**Description:** Kraken Trader.py is a Termux trading research and portfolio assistant for the Kraken API. It starts in paper mode by default, shows a 10-second risk disclaimer, stores everything under ~/Kraken Trader/, and uses numbered menus for pair analysis, market scanning, dashboards, Sage-style strategy labs, advanced tools, beginner guides, risk/reward calculators, backtests, DCA and grid tools, paper wallet trading, paper bot loops, Kraken account tools, live order menus, order management, watchlists, crypto plus stock/ETF monitoring, reports, journals, logs, mode switching, diagnostics, and settings. It is built for education, organization, and safer paper testing; it is not financial advice and it does not guarantee profit.

**Save Location:** `Main folder: ~/Kraken Trader/ | Config, paper wallet, watchlists, presets, alerts, baskets, DCA/grid assists, webhook logs, forward tests, reports, cache, journals, trade logs, and error logs are stored inside it. Optional report copies can be saved to Downloads if enabled.`


</details>

<details>
<summary>Noob Hacker.py</summary>




**What It Helps With:** Learning cybersecurity concepts through a more game-like progression with lessons, examples, and practice.

**Description:** Noob Hacker.py is a safe offline terminal learning game for Termux that teaches absolute beginners programming, Python basics, Termux/Bash habits, debugging, local-only cybersecurity thinking, defender workflows, report writing, projects, quizzes, and playable practice games. It is built as a single Python script, works without root, keeps practice inside fictional/local labs, includes English and Greek versions, supports self-tests, save migration, progress tracking, and many beginner-friendly lessons designed to guide someone from zero knowledge into practical safe skills. It does not attack real targets, scan the internet, steal accounts, or teach malware.

**Save Location:** `Main folder: ~/Noob Hacker/ | Save file: ~/Noob Hacker/save.json | Mission log: ~/Noob Hacker/mission_log.txt | CTF labs: ~/Noob Hacker/CTF_Labs/ | Exports: ~/Noob Hacker/Exports/.`


</details>


<a id="butsystempy-exclusive"></a>

<h2>ButSystem.py (Exclusive)</h2>


ButSystem.py is a self-hosted, local-first private workspace for Termux that combines private communication, encrypted records, an advanced file vault, news and weather tools, and automatically generated local, Cloudflared, and Tor access links in one browser interface.

**Exclusive to DedSec Project — included free:** ButSystem is one of the project’s most distinctive all-in-one systems, built specifically for the DedSec Project ecosystem. Despite that exclusive positioning, the version documented here is available free through the project files and repository, with no separate Store purchase required.

### Core ButSystem Feature Areas
- **Chats, Groups & Stories:** Live direct messages, group chats, saved messages, GIFs, voice notes, file sharing, the discussion room, stories, and call flows where browser and device support allow it.
- **Security, Access & Control:** User approval, device access requests, remembered-device login, optional security-question 2FA, chat PIN locks, online status, reports, admin pages, and appearance or account settings.
- **Profiles, Vault & Tools:** Profile editing, an advanced private file vault, opt-in live locations, encrypted Profiler records with search, import, export, and combine tools, administrator bounty controls, and the built-in Face Detector.
- **Weather, Links & Sharing:** Search weather by place or current location, view detailed forecasts for up to 14 days, and use generated HTTPS, Cloudflared, or Tor links with downloadable QR codes. Vault files can also be shared through controlled links with optional passwords, expiry, and revocation.

### All ButSystem Areas
- **Navigation & Menu Flow:** The burger menu is the main control hub of ButSystem. From there you move between chats, saved messages, discussion, groups, calls, stories, live locations, files, news, weather, profiles, Profiler, reports, notifications, admin pages, settings, help, and login or logout actions, while the language toggle keeps the interface available in both English and Greek.
- **Authentication & Access:** ButSystem opens through its landing, loading, login, and signup flow, then adds extra access control where needed. That includes user approval, device access requests, remembered-device login, optional security-question two-factor checks, and password recovery or reset actions so access stays tied to approved users and approved devices.
- **Direct Messages:** The DM area is built for day-to-day private conversation. You can open a chat, write and send text, edit or delete messages, search conversation content, attach media or files, use GIFs, record or play voice notes, and work with chat protections such as PIN locks and visible online status where those controls are enabled.
- **Discussion Room:** Discussion works more like a shared stream than a one-to-one chat. It is the place for broader entries, category-based posting, search, refresh, loading more content, and opening a specific entry when you want a calmer shared space separate from normal DMs.
- **Groups:** The Groups area lets users build shared spaces with roles and moderation controls. You can create a group, invite or add members, check the member list, manage owner or admin actions such as promote, demote, or remove, leave a group when needed, and continue the conversation through the related group chat with messages and attachments.
- **Calls & Live Communication:** Where browser support and device permissions allow it, ButSystem includes call flows for starting, joining, accepting, denying, muting, and ending a live call. The exact experience depends on microphone permissions and the current browser environment, so the call layer is treated as a live feature area rather than a static page.
- **Stories & Live Locations:** ButSystem also covers lighter live-sharing tools. Stories provide creation, viewing, and reaction controls, while Live Locations is reserved for opt-in location sharing with start, stop, refresh, and clear consent or warning prompts before location data is actively shared.
- **Files, Vault & Saved Media:** The Files and Vault area works like a private server-style file manager. It supports folders and navigation, normal or chunked uploads with cancellation, search, categories, file-type filters, sorting, previews, opening and downloading, rename, move, bulk actions, deletion, comments, activity history, detailed size, MIME, and date metadata, optional SHA-256, and controlled share links with optional passwords, expiry times, and revocation.
- **Profile, Account & Appearance:** Your own profile area handles identity and account presentation. From there users can view or edit profile data, save changes, upload or remove a profile picture, adjust account settings, control appearance options, and access stronger account actions such as account deletion or the self-destruct danger zone where that workflow is enabled.
- **Profiler, Bounty & Face Detector:** The Profiler side is where ButSystem becomes a structured information workspace. It supports encrypted profiler entries, view and edit flows, local search, export and combine tools, bounty management where that module is enabled, and the built-in Face Detector area used for local face-detection workflows and similarity-style comparison support inside the broader ButSystem environment.
- **Reports, Admin & Security Settings:** The control layer of ButSystem is split across reports, admin pages, and security settings. This is where users create or update reports, where admins approve or deny access and device requests, manage people and user files, and where account holders configure two-factor settings, device-login rules, password-reset paths, privacy options, and other safeguards that keep the workspace organized and controlled.
- **News & Topic Feed:** The News area gives the workspace a dedicated place for topic-based updates without mixing them into private chats. Users can open the feed, move between available topics, refresh the current view, and read updates from the same local interface used for the rest of ButSystem.
- **Weather & Forecasts:** Search by city, village, or postal code, use the device's current location, refresh results, and view current conditions plus forecasts for up to 14 days. The page can show current and apparent temperature, humidity, wind and gusts, precipitation, cloud cover, pressure, rain probability, UV, sunrise, and sunset. Coordinates are used for the request and are not saved by ButSystem.
- **Generated HTTPS, Cloudflared & Tor Links:** At startup, ButSystem serves local HTTPS with a generated self-signed certificate, prints LAN and localhost URLs, and automatically attempts a Cloudflared quick tunnel and a Tor hidden service. The landing page displays whichever links are available and generates a fresh downloadable QR code for each one.
- **Presence, Delivery & Live State:** ButSystem keeps active areas responsive with heartbeat-based online status, unread message counts, delivery and read state, polling for new direct or group messages, and live refresh paths for discussion, locations, calls, and other changing data. This makes the interface feel current without needing a separate desktop client.
- **Attachments, Previews & Large Uploads:** Files are handled according to where they are used. Direct messages, groups, discussion, and stories support the relevant file, image, voice, or media attachments; profiles support profile pictures; and the vault adds previews, metadata, organization, sharing, and chunked transfer for larger uploads so they are not forced through one fragile request.
- **Local Data Protection & Persistence:** Account records, settings, messages, encrypted text fields, keys, logs, and workspace data are kept in ButSystem's own local folders. The script prefers the phone's shared Homework storage when available so important app state can survive a Termux reinstall, while sensitive text and Profiler content use the built-in encryption layer.
- **Search, Export & Record Workflows:** Several areas are designed for finding, filtering, and moving information instead of only displaying it. Users can search conversations, discussion entries, vault files, reports, and Profiler records; filter and sort the vault; open focused details; import, export, or combine Profiler records; and download attachments when a local copy is needed.
- **Privacy Pause, Logs & Recovery Controls:** The system includes operational safeguards for moments when access must be stopped or reviewed. Privacy pause and resume actions can temporarily protect the workspace, security events are written to local logs, admins can inspect log files, and recovery tools cover forgotten passwords, approved devices, forced sign-out, account deletion, and full reset workflows.

### Forgot The Password? Start ButSystem Fresh

Use this only when recovery is impossible and you accept losing every old ButSystem account, password, setting, message, vault file, key, and log. Stop ButSystem first, run the command in Termux, then start ButSystem.py again so it creates a completely fresh workspace.

**Warning:** This command permanently deletes the saved ButSystem data folders. It does not delete the ButSystem.py script itself.

**Save Location:** `Main persistent data: /storage/emulated/0/Homework/ButSystem/ (also available as ~/storage/shared/Homework/ButSystem/) | Fallback: ~/Homework/ButSystem/ | Legacy data migrated from: ~/ButSystem/ | Face Detector captures: Downloads/ButSystem/Face Detector/ | Tor runtime data: ~/.ButSystem_tor/`

Use only on systems you own or where you have explicit permission.

</details>

<a id="contact-us--credits"></a>

<details>
<summary><strong>Contact Us & Credits</strong></summary>


### Contact Us

Get in touch with our team and meet the talented people behind the DedSec Project.

* **Main Website:** [https://ded-sec.space](https://ded-sec.space)
* **Main DedSec Project Repository:** [https://github.com/dedsec1121fk/DedSec](https://github.com/dedsec1121fk/DedSec)
* **Backup Website:** [https://ded-sec.online](https://ded-sec.online)
* **Backup DedSec Project Repository:** [https://github.com/sal-scar/DedSec](https://github.com/sal-scar/DedSec)
* **WhatsApp:** [+37257263676](https://wa.me/37257263676)
* **Telegram Profile:** [@dedsecproject](https://t.me/dedsecproject)
* **Discord Server:** [https://discord.gg/fcAuYS4JEv](https://discord.gg/fcAuYS4JEv)
* **Telegram Channel:** [https://t.me/dedsec_project_channel](https://t.me/dedsec_project_channel)
* **X Profile:** [https://x.com/DedSecProject](https://x.com/DedSecProject)

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




Βήμα-βήμα οδηγίες για την εγκατάσταση και ρύθμιση του DedSec Project στη συσκευή σας Android.

### Απαιτήσεις

| Στοιχείο | Ελάχιστη Προδιαγραφή |
| :-------- | :------------------- |
| **Συσκευή** | Κινητό ή tablet Android με εγκατεστημένο Termux |
| **Αποθηκευτικός χώρος** | Ελάχιστο **8GB** ελεύθερος χώρος |
| **RAM** | Ελάχιστο **2GB** |
| **Internet** | Απαιτείται για την πρώτη εγκατάσταση και τις ενημερώσεις |

### Πριν Ξεκινήσεις

Το F-Droid είναι ένα εναλλακτικό κατάστημα εφαρμογών για Android που παρέχει ελεύθερο και ανοιχτού κώδικα λογισμικό. Είναι ο συνιστώμενος τρόπος για να εγκαταστήσετε το Termux και άλλα εργαλεία ασφαλείας.

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

Το script θα αναλάβει την πλήρη εγκατάσταση. Μετά την εγκατάσταση, πρέπει να αλλάξετε το prompt, να αλλάξετε το στυλ του μενού (τα στυλ λίστας ή αριθμημένου μενού είναι τα καλύτερα για νέους χρήστες), να επιλέξετε γλώσσα και να τρέξετε την επιλογή Save DedSec Project στο πρώτο σας άνοιγμα ώστε να δημιουργηθεί αμέσως το backup package. Το Save DedSec Project μπορεί να πάρει λίγη ώρα ανάλογα με τη σύνδεσή σας στο internet και το terminal μπορεί να μένει κενό μέχρι να ολοκληρωθεί. Τρέχετε ξανά το Save DedSec Project λίγες φορές κάθε χρόνο ώστε το αποθηκευμένο πακέτο του DedSec Project να μένει φρέσκο και έτοιμο αν το χρειαστείτε. Μετά από αυτό, κλείστε το Termux από το πάνελ ειδοποιήσεων του κινητού σας χρησιμοποιώντας το κουμπί εξόδου και έπειτα ανοίξτε ξανά το Termux. Συμβουλή: Μπορείτε να ανοίξετε γρήγορα το μενού πληκτρολογώντας 'e' (Αγγλικά) ή 'g' (Ελληνικά) στο Termux.

##### 5. Ολοκλήρωσε τη ρύθμιση μετά το setup

Αφού ολοκληρωθεί το setup, κάνε τα εξής:

- άλλαξε το **prompt**
- άλλαξε το **στυλ του μενού**
- για νέους χρήστες, τα **list** ή **numbered** menu styles είναι οι καλύτερες επιλογές
- διάλεξε τη **γλώσσα** σου
- τρέξε το **Save DedSec Project** στο πρώτο σου άνοιγμα ώστε να δημιουργηθεί αμέσως το backup package σου
- τρέξε ξανά το **Save DedSec Project** λίγες φορές κάθε χρόνο ώστε το αποθηκευμένο package να μένει ενημερωμένο και έτοιμο αν το χρειαστείς
- ένα manual **Save DedSec Project** μπορεί να πάρει λίγη ώρα ανάλογα με τη σύνδεσή σου στο internet και το terminal μπορεί να μένει κενό μέχρι να ολοκληρωθεί
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

Τρέξε ξανά το setup ώστε ο ενιαίος dependency manager να ελέγξει τα τοπικά αρχεία, να ενημερώσει dependencies και να ανοίξει το menu:

```bash
bash Setup.sh
```

Για ενημέρωση dependencies χωρίς να ανοίξει το menu, χρησιμοποίησε:

```bash
bash Setup.sh --update-only
```

Αυτό είναι χρήσιμο μετά από μεγάλες αλλαγές στο project, νέα dependencies ή menu updates.

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
- Τρέξε το **Save DedSec Project** στο πρώτο άνοιγμα και ξανά λίγες φορές κάθε χρόνο ώστε το αποθηκευμένο package να μένει ενημερωμένο. Η διαδικασία μπορεί να πάρει λίγη ώρα ανάλογα με τη σύνδεσή σου.
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

Μην ξεκινήσεις ανοίγοντας τυχαία scripts. Η δωρεάν Academy βάζει το project σε σειρά: πρώτα setup, μετά μαθήματα, practice και το επόμενο lesson.

- [Οδηγός Εγκατάστασης](https://ded-sec.space/Pages/guide-for-installation.html) — website path: `Pages/guide-for-installation.html`
- [Μάθετε για τα Εργαλεία](https://ded-sec.space/Pages/learn-about-the-tools.html) — website path: `Pages/learn-about-the-tools.html`
- [Βοήθεια](https://ded-sec.space/Pages/assistance.html) — website path: `Pages/assistance.html`

Μετά κατέβασε το δωρεάν e-book μας:

- [Master Termux In 7 Days](https://ded-sec.space/Assets/Master%20Termux%20In%207%20Days%20Greek.pdf) — website path: `Assets/Master Termux In 7 Days Greek.pdf`

Το ButSystem είναι ένα από τα πιο ξεχωριστά ολοκληρωμένα συστήματα του project και έχει δημιουργηθεί ειδικά για το οικοσύστημα του DedSec Project. Παρότι αποτελεί ένα από τα πιο αποκλειστικά εργαλεία του, η έκδοση που περιγράφεται εδώ διατίθεται δωρεάν μέσα από τα αρχεία και το repository, χωρίς ξεχωριστή αγορά από το Store.:

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
- **Update Packages & Modules:** εκτελεί την ενιαία dependency διαδικασία `Setup.sh --no-run`, η οποία ελέγχει πρώτα τα τοπικά Termux packages και Python modules, ενημερώνει τα εγκατεστημένα στοιχεία και κατεβάζει ό,τι λείπει χωρίς να ανοίξει δεύτερο menu process.
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
4. τρέξε το **Save DedSec Project** στο πρώτο σου άνοιγμα και χρησιμοποίησέ το ξανά όποτε θέλεις να ανανεώσεις το backup σου
5. σύνδεσε GitHub μόνο αν θέλεις GitHub stats, prompt syncing ή Sponsors-Only access
6. ενεργοποίησε ή απενεργοποίησε το menu auto-start ανάλογα με το πώς χρησιμοποιείς το Termux
7. χρησιμοποίησε το **Update Packages & Modules** όταν χρειάζεται ανανέωση dependencies
8. χρησιμοποίησε το **VPN & Tor Utilities** μόνο όταν θέλεις αυτά τα προαιρετικά network controls

### Υπενθύμιση Αποθήκευσης

Το `Setup.sh` εγκαθιστά και ελέγχει τα dependencies του project, αλλά δεν δημιουργεί backup αυτόματα. Χρησιμοποίησε το **Save DedSec Project** από τα Settings στο πρώτο σου άνοιγμα και ξανά όποτε θέλεις να ανανεώσεις το backup στα Downloads του κινητού σου. Η αποθήκευση μπορεί να πάρει λίγη ώρα ανάλογα με τη σύνδεσή σου στο internet και το terminal μπορεί να μένει κενό μέχρι να ολοκληρωθεί.

</details>

<a id="greek-toolkit"></a>

<details>
<summary><strong>Εξερευνήστε την Εργαλειοθήκη</strong></summary>


Αυτή η σελίδα είναι ο χάρτης του project: τι κάνει κάθε εργαλείο, γιατί υπάρχει και ποιο πραγματικό πρόβλημα με έσπρωξε να το φτιάξω. Ξεκίνα από τη λίστα, άνοιξε ό,τι σου τραβάει το μάτι και άσε τα εργαλεία να εξηγήσουν μόνα τους το project.

> **ΚΡΙΣΙΜΗ ΣΗΜΕΙΩΣΗ:** Τα παρακάτω scripts περιλαμβάνονται μόνο για **εκπαιδευτικούς και αμυντικούς σκοπούς**. Ο ρόλος τους είναι να βοηθούν τους χρήστες να κατανοούν πώς λειτουργούν εργαλεία, lures και simulations, ώστε να βελτιώνουν την επίγνωση, την πειθαρχία στις δοκιμές και την αυτοπροστασία τους μέσα σε ελεγχόμενα περιβάλλοντα.

### Σύνοψη Toolkit

- **Developer Base:** 11 εργαλεία
- **Network Tools:** 10 εργαλεία
- **Other Tools:** 5 εργαλεία
- **Games:** 6 εργαλεία
- **Personal Information Capture:** 17 εργαλεία
- **Social Media / Fake Pages:** 25 εργαλεία
- **No Category:** 3 εργαλεία
- **Sponsors-Only:** 6 εργαλεία στο $3 tier / 9 εργαλεία στο $9 tier

**Συνολικά καταχωρημένα στη σελίδα εργαλείων:** 86 εργαλεία

---
<a id="greek-developer-base"></a>

<h2>Βάση Προγραμματιστή</h2>


<details>
<summary>File Converter</summary>




**Τι Βοηθά Να Λύσεις:** Μετατροπή εικόνων, εγγράφων, ήχου, βίντεο και archives απευθείας στο Android, όταν η μεταφορά της δουλειάς σε υπολογιστή θα σε καθυστερούσε.

**Περιγραφή:** Ένας ισχυρός μετατροπέας αρχείων που υποστηρίζει 40+ μορφές. Οργανώνει τις Λήψεις. Προηγμένος διαδραστικός μετατροπέας αρχείων για Termux χρησιμοποιώντας διεπαφή curses. Υποστηρίζει 40 διαφορετικές μορφές αρχείων σε εικόνες, έγγραφα, ήχο, βίντεο και αρχεία. Διαθέτει αυτόματη εγκατάσταση εξαρτήσεων, οργανωμένη δομή φακέλων και ολοκληρωμένες δυνατότητες μετατροπής. Σχεδιασμένο για το Termux, με σαφείς οδηγίες και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Τα αρχεία που έχουν μετατραπεί αποθηκεύονται στο /storage/emulated/0/Download/File Converter/, μέσα σε φακέλους ανά μορφή όπως JPG, PNG, PDF, MP3, MP4, ZIP, TXT και άλλα.`


</details>

<details>
<summary>File Type Checker</summary>




**Τι Βοηθά Να Λύσεις:** Αναγνώριση του πραγματικού τύπου ενός αρχείου και έλεγχος ύποπτων χαρακτηριστικών πριν το εμπιστευτείς ή το ανοίξεις.

**Περιγραφή:** Προηγμένος αναλυτής αρχείων και σαρωτής ασφαλείας που εντοπίζει τύπους αρχείων, εξάγει μεταδεδομένα, υπολογίζει κρυπτογραφικά hashes και αναγνωρίζει πιθανές απειλές. Διαθέτει ανίχνευση magic byte, ανάλυση εντροπίας, ανίχνευση steganography, σάρωση ιών μέσω VirusTotal API και αυτόματη καραντίνα ύποπτων αρχείων. Σχεδιασμένο για το Termux, με σαφείς οδηγίες και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Τα αρχεία ελέγχονται στο /sdcard/Download/File Type Checker/ στο Termux ή στο ~/Downloads/File Type Checker/ εκτός Termux. Τα αρχεία που τέθηκαν σε καραντίνα μένουν στον ίδιο φάκελο και μετονομάζονται με κατάληξη .dangerous.`


</details>

<details>
<summary>Mobile Desktop</summary>




**Τι Βοηθά Να Λύσεις:** Χρήση περιβάλλοντος Linux τύπου desktop μέσα από Termux χωρίς root, όταν οι εφαρμογές μόνο τερματικού δεν αρκούν.

**Περιγραφή:** Διαχειριστής Linux Desktop για Termux (χωρίς root): στήνει proot-distro περιβάλλον με επιλογές VNC/X11 και πρόγραμμα διαχείρισης εφαρμογών (install/update/remove). Σχεδιασμένο για το Termux, με σαφείς οδηγίες και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Οι ρυθμίσεις του διαχειριστή αποθηκεύονται στο ~/.termux_linux_vnc_manager/config.json. Οι εκκινητές που δημιουργούνται εγκαθίστανται στο $PREFIX/bin/ ως vnc-<system>. Οι διανομές Linux διαχειρίζονται από το proot-distro.`


</details>

<details>
<summary>Mobile Developer Setup</summary>




**Τι Βοηθά Να Λύσεις:** Δημιουργία επαναλήψιμου περιβάλλοντος ανάπτυξης από κινητό αντί για χειροκίνητη εγκατάσταση και ρύθμιση κάθε εξάρτησης.

**Περιγραφή:** Αυτοματοποιεί περιβάλλον ανάπτυξης ιστοσελίδων σε Termux: εγκαθιστά βασικά εργαλεία, ρυθμίζει διαδρομές και δίνει γρήγορο έτοιμη βασική δομή έργου. Σχεδιασμένο για το Termux, με σαφείς οδηγίες και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Το state και τα αρχεία αντιγράφων ασφαλείας αποθηκεύονται στο ~/.mobile-dev-setup/ (μαζί με backups/ και state.json). Τα βοηθητικά scripts μπαίνουν στο ~/.mobile-dev-setup-Tools/, τα πρόσθετα στο ~/.zsh-plugins/ και τα αρχεία εμφάνισης του Termux στο ~/.termux/.`


</details>

<details>
<summary>Simple Websites Creator</summary>




**Τι Βοηθά Να Λύσεις:** Δημιουργία απλών websites από κινητό όταν θέλεις καθοδηγούμενη αρχική δομή αντί να φτιάχνεις κάθε αρχείο χειροκίνητα.

**Περιγραφή:** Ένας ολοκληρωμένος δημιουργός ιστοσελίδων που δημιουργεί ανταποκρινόμενες HTML ιστοσελίδες με προσαρμόσιμη διάταξη, χρώματα, γραμματοσειρές και ρυθμίσεις SEO. Χαρακτηριστικά περιλαμβάνουν πολλαπλούς οδηγούς φιλοξενίας, προεπισκόπηση σε πραγματικό χρόνο, φιλικά για κινητά σχέδια και επαγγελματικά πρότυπα. Σχεδιασμένο για το Termux, με σαφείς οδηγίες και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Οι ιστοσελίδες που δημιουργούνται αποθηκεύονται στο /storage/emulated/0/Download/Websites/.`


</details>

<details>
<summary>Smart Notes</summary>




**Τι Βοηθά Να Λύσεις:** Οργάνωση τεχνικών σημειώσεων, ιδεών, εντολών και πληροφοριών project όταν δουλεύεις από κινητό.

**Περιγραφή:** Εφαρμογή σημειώσεων terminal με υπενθυμίσεις. Προηγμένη εφαρμογή σημειώσεων με λειτουργικότητα υπενθύμισης, που διαθέτει τόσο TUI (Διεπαφή Κειμένου) όσο και υποστήριξη CLI. Περιλαμβάνει εξελιγμένο σύστημα υπενθυμίσεων με ημερομηνίες λήξης, αυτόματη εκτέλεση εντολών, ενσωμάτωση εξωτερικού επεξεργαστή και ολοκληρωμένες δυνατότητες οργάνωσης σημειώσεων. Σχεδιασμένο για το Termux, με σαφείς οδηγίες και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Σημειώσεις: ~/.smart_notes.json | Ρυθμίσεις: ~/.smart_notes_config.json | Αρχείο καταγραφής σφαλμάτων: ~/.smart_notes_error.log.`


</details>

<details>
<summary>Dead Man's Switch</summary>




**Τι Βοηθά Να Λύσεις:** Προετοιμασία επιβεβαιωμένης από τον χρήστη ροής έκτακτης ανάγκης με έμπιστες επαφές, αρχεία κατάστασης και προαιρετικά δεδομένα συσκευής όταν δεν γίνει προγραμματισμένο check-in.

**Περιγραφή:** Emergency/SOS εργαλείο για Termux που βασίζεται στη λειτουργία I Need Help. Μετά το first-time setup και καθαρές επιβεβαιώσεις από τον χρήστη, μπορεί να κάνει public το dead-mans-switch GitHub repository, να δημιουργήσει GitHub Pages emergency website, να ανεβάσει οργανωμένα emergency αρχεία, να τραβήξει διαθέσιμες φωτογραφίες από κάμερες, ηχογραφήσεις μικροφώνου και location updates σε ρυθμιζόμενα χρονικά διαστήματα μέσω Termux:API δικαιώματα, και να στείλει SMS alerts με το website/repository link σε configured trusted contacts. Περιλαμβάνει επίσης create/update uploads, overwrite sync, visibility controls, legacy repository migration, previous-history αντίγραφα ασφαλείας, logs και kill/cleanup option.

**Τοποθεσία Αποθήκευσης:** `Κύριος τοπικός φάκελος: ~/storage/downloads/Dead Man's Switch/ (κανονικά ο φάκελος Download του τηλεφώνου, με εναλλακτική διαδρομή /storage/emulated/0/Download/Dead Man's Switch/). Ρυθμίσεις: ~/.dead_switch_settings.json. Τα logs και τα προηγούμενα αντίγραφα ασφαλείας του αποθετηρίου αποθηκεύονται μέσα στον κύριο φάκελο στα Logs/ και History/.`


</details>

<details>
<summary>Tree Explorer</summary>




**Τι Βοηθά Να Λύσεις:** Γρήγορη κατανόηση μεγάλων δομών φακέλων και projects ώστε να βρίσκεις το αρχείο ή directory που πραγματικά χρειάζεσαι.

**Περιγραφή:** Εξερευνητής αρχείων για Termux: περιήγηση φακέλων, αναζήτηση αρχείων, εύρεση διπλότυπων με hash και καθαρισμός άδειων φακέλων με ασφαλείς επιλογές. Σχεδιασμένο για το Termux, με σαφείς οδηγίες και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Το Tree Explorer δεν δημιουργεί default φάκελο αποτελεσμάτων. Οι εξαγωγές γράφονται μόνο στη διαδρομή που επιλέγεις με --export FILE ή από τη διαδραστική επιλογή εξαγωγής. Η εγκατάσταση της εντολής το αντιγράφει από προεπιλογή στο $PREFIX/bin/supertree.`


</details>

<details>
<summary>Devices Finder</summary>




**Τι Βοηθά Να Λύσεις:** Εντοπισμός και ταξινόμηση συσκευών σε τοπικό δίκτυο που σου ανήκει ή έχεις άδεια να ελέγξεις, χωρίς να απαιτείται root.

**Περιγραφή:** Εργαλείο ανακάλυψης συσκευών τοπικού δικτύου για Termux που λειτουργεί χωρίς root. Διαχωρίζει τον εντοπισμό ενεργών συσκευών από τη σάρωση υπηρεσιών για να μειώνει τα λανθασμένα θετικά αποτελέσματα, αναγνωρίζει τύπους συσκευών με βάση θύρες, στοιχεία υπηρεσιών, ονόματα συσκευών και ενδείξεις κατασκευαστή, περιλαμβάνει διαδραστικά προφίλ σάρωσης και φίλτρα τύπου, και προαιρετικά εμπλουτίζει τα αποτελέσματα με mDNS, UPnP, SNMP και ενδείξεις NetBIOS. Εξάγει αναφορές JSON, TXT, CSV και HTML. Σχεδιασμένο για το Termux, με σαφείς οδηγίες και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Οι αναφορές αποθηκεύονται στο ~/storage/downloads/Devices Finder/ ως devices_scan_<timestamp>.json, .txt, .csv και .html. Οι εναλλακτικές διαδρομές είναι ~/downloads/Devices Finder/ και μετά ./Devices Finder Output/.`


</details>

<details>
<summary>Free Internet</summary>




**Τι Βοηθά Να Λύσεις:** Οργάνωση browsing, αποθηκευμένων σελίδων, αναζήτησης, screenshots και ιδιωτικών δεδομένων vault σε μία local-first ροή Termux.

**Περιγραφή:** Browser με τοπική αποθήκευση ως προτεραιότητα και ασφαλές θησαυροφυλάκιο για Termux. Συνδυάζει πολλαπλές μηχανές αναζήτησης, σελιδοδείκτες, ιστορικό, αποθηκευμένες σελίδες, καθαρισμό διαφημίσεων και ιχνηλάτες, ελαφριά λειτουργία, δρομολόγηση μέσω διακομιστή μεσολάβησης ανά χώρα με smart/strict/direct modes, προαιρετική υποστήριξη Tor, κρυπτογραφημένες εγγραφές θησαυροφυλακίου μέσω OpenSSL και ενσωματωμένο εργαλείο στιγμιότυπα ολόκληρων ιστοσελίδων. Σχεδιασμένο για το Termux, με σαφείς οδηγίες και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Στο Termux όλα τα δεδομένα αποθηκεύονται στον φάκελο ~/Free Internet/, ενώ σε άλλα συστήματα χρησιμοποιείται το ~/.free_internet/. Τα δεδομένα περιήγησης βρίσκονται στο browser/, οι αποθηκευμένες σελίδες στο browser/saved/, τα στιγμιότυπα οθόνης στο Tools/screenshots/ και η κρυπτογραφημένη βάση του θησαυροφυλακίου στο vault/vault.db.`


</details>


<details>
<summary>DedSec's Server</summary>




**Τι Βοηθά Να Λύσεις:** Κοινή χρήση και διαχείριση μεγάλων αρχείων από Termux μέσω ελεγχόμενου local/self-hosted server αντί για τρίτη υπηρεσία φιλοξενίας.

**Περιγραφή:** Πλατφόρμα φιλοξενίας και διαχείρισης αρχείων πολλαπλών διακομιστών για Termux. Δημιουργεί ξεχωριστά προφίλ server με όνομα, ανοιχτή πρόσβαση επισκεπτών ή προστασία μόνο για διαχειριστές, πολλαπλούς λογαριασμούς διαχειριστών, μεταφορτώσεις έως 30 GB με ζωντανή τμηματική πρόοδο, δημιουργία φακέλων και λήψεις ZIP, μετακινήσεις, μετονομασίες και διαγραφές αρχείων, κατηγορίες, αναζήτηση, φίλτρα, ταξινόμηση, λεπτομέρειες, σχόλια, συνεδρίες χρηστών και πλήρη αρχεία καταγραφής δραστηριότητας και ασφάλειας. Κάθε server ξεκινά πρόσβαση μέσω localhost και τοπικού δικτύου και προσπαθεί αυτόματα να δημιουργήσει συνδέσμους Cloudflare και Tor. Περιλαμβάνει επίσης φωτεινό και σκοτεινό θέμα, ξεχωριστές αγγλικές και ελληνικές εκδόσεις, επιβεβαιώσεις για αλλαγές, περιορισμό αποτυχημένων προσπαθειών, προστασία CSRF, ελέγχους ασφαλείας αποθηκευτικού χώρου και αυτόματη εγκατάσταση εξαρτήσεων. Σχεδιασμένο για το Termux, με σαφείς επιλογές και οργανωμένη αποθήκευση.

**Τοποθεσία Αποθήκευσης:** `Όλα τα δεδομένα αποθηκεύονται κάτω από το ~/DedSec's Server/. Οι αγγλικές και ελληνικές εκδόσεις χρησιμοποιούν ξεχωριστούς φακέλους English/ και Greek/. Τα αρχεία κάθε server αποθηκεύονται στο <edition>/Servers/<server-id>/, οι ρυθμίσεις στο <edition>/Config/config.json, τα προσωρινά δεδομένα συνεδρίας στο <edition>/Runtime/, τα σχόλια στο <edition>/Comments/ και τα αρχεία καταγραφής κάθε server στον κρυφό φάκελο .dedsec-server/logs/ του server.`


</details>


<a id="greek-network-tools"></a>

<h2>Εργαλεία Δικτύου</h2>


<details>
<summary>Bug Hunter</summary>




**Τι Βοηθά Να Λύσεις:** Οργάνωση εξουσιοδοτημένου web-security reconnaissance και ελέγχων misconfiguration σε μία επαναλήψιμη ροή audit.

**Περιγραφή:** Bug Hunter (χωρίς root) — εξουσιοδοτημένο εργαλείο αναγνώρισης web ασφάλειας και ελέγχου κακής ρύθμισης. Ελέγχει security headers και cookie flags, ανιχνεύει τεχνολογίες, κάνει DNS ελέγχους (SPF/DMARC/CAA), αναλύει TLS/λήξη πιστοποιητικού, ελέγχει CORS και HTTP μεθόδους, βρίσκει εκτεθειμένα ευαίσθητα αρχεία, κάνει crawl στο site και αναλύει JavaScript για endpoints και πιθανές διαρροές μυστικών. Υποστηρίζει προαιρετικό directory discovery και Wayback recon, και παράγει απο-διπλοποιημένες αναφορές (JSON/CSV/HTML/PDF). Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

**Τοποθεσία Αποθήκευσης:** `Ο προεπιλεγμένος φάκελος αποτελεσμάτων είναι το ./bughunter_out/ μέσα στον κατάλογο εκτέλεσης του script. Με την επιλογή --output PATH μπορείς να ορίσεις διαφορετικό φάκελο. Οι αναφορές περιλαμβάνουν τα report.json, report.csv και report.html, καθώς και προαιρετικά αρχεία report.pdf, ζωντανής παρακολούθησης και σημείων επαναφοράς.`


</details>

<details>
<summary>Dark</summary>




**Τι Βοηθά Να Λύσεις:** Συλλογή και οργάνωση δημόσιου Tor/.onion OSINT σε εξουσιοδοτημένη έρευνα χωρίς χειροκίνητη καταγραφή κάθε αποτελέσματος.

**Περιγραφή:** Ένα εξειδικευμένο εργαλείο OSINT και crawler για το Dark Web, σχεδιασμένο για ανάλυση δικτύου Tor. Διαθέτει αυτοματοποιημένη σύνδεση Tor, ενσωμάτωση αναζήτησης Ahmia και αναδρομικό crawler για ιστοσελίδες .onion. Το εργαλείο χρησιμοποιεί ένα αρθρωτό σύστημα πρόσθετων για την εξαγωγή συγκεκριμένων τύπων δεδομένων (Email, διευθύνσεις BTC/XMR, κλειδιά PGP, Τηλέφωνα) και υποστηρίζει την αποθήκευση στιγμιότυπων. Προσφέρει λειτουργία Curses TUI και CLI, με αποτελέσματα εξαγώγιμα σε JSON, CSV και TXT. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

**Τοποθεσία Αποθήκευσης:** `Τα αποτελέσματα αποθηκεύονται στο /sdcard/Download/DarkNet/ με εναλλακτική διαδρομή στο ~/DarkNet/. JSON, CSV, TXT, snapshots και αποτελέσματα πρόσθετων γράφονται εκεί, ενώ τα πρόσθετα αποθηκεύονται στον υποφάκελο plugins/.`


</details>

<details>
<summary>DedSec's Network</summary>




**Τι Βοηθά Να Λύσεις:** Συνδυασμός συνηθισμένων network diagnostics, OSINT, downloading και εξουσιοδοτημένων web-audit εργασιών ώστε να μη χρειάζεσαι ξεχωριστό script για κάθε έλεγχο.

**Περιγραφή:** Μια προηγμένη εργαλειοθήκη δικτύου χωρίς root. Διαθέτει αναδρομικό πρόγραμμα λήψης ιστοσελίδων με υποστήριξη ZIP, πολυνηματικό σαρωτή θυρών, δοκιμή ταχύτητας internet και εργαλεία OSINT (WHOIS, DNS, Reverse IP). Περιλαμβάνει σαρωτές ελέγχου ιστού για SQLi, XSS, ανίχνευση CMS και SSH brute-force. Διατηρεί τοπικό αρχείο καταγραφής ελέγχου SQLite. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

**Τοποθεσία Αποθήκευσης:** `Τα config, audit_results.db και wordlists αποθηκεύονται στο ~/DedSec's Network/ στο Termux ή στο ./DedSec's Network/ αλλού. Οι ιστοσελίδες που έχουν ληφθεί μπαίνουν στο /storage/emulated/0/Download/Websites/<domain>/, με εναλλακτικές διαδρομές τα /sdcard/Download/Websites/, ~/DedSec's Network/Websites/ ή ~/Downloads/Websites/ εκτός Termux.`


</details>

<details>
<summary>Digital Footprint Finder</summary>




**Τι Βοηθά Να Λύσεις:** Έλεγχος του πού εμφανίζεται δημόσια ένα username, με μείωση προφανών false positives και δυνατότητα export των αποτελεσμάτων.

**Περιγραφή:** Συντηρητικό εργαλείο OSINT ελέγχου usernames με στόχο τα καλύτερα πρακτικά αποτελέσματα και ελάχιστα ψευδώς θετικά. Σαρώνει μεγάλο πλήθος sites μέσω packs (core/extended) με προαιρετική βάση Sherlock, χρησιμοποιώντας βαθμολόγηση πολλαπλών σημάτων (status/redirects, title/meta/canonical/text) και όρια ταυτόχρονης σύνδεσης ανά domain για σταθερότητα. Ανιχνεύει anti-bot/JS challenges ως POSSIBLE (ποτέ ψευδώς FOUND), υποστηρίζει προαιρετικό search-engine dorking και εισαγωγή/εξαγωγή προσαρμοσμένων λιστών sites. Εξάγει αναφορές σε TXT/JSON/CSV και προαιρετικά HTML. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

**Τοποθεσία Αποθήκευσης:** `Οι αναφορές αποθηκεύονται στο ~/storage/downloads/Digital Footprint Finder/. Αν δεν είναι διαθέσιμο, το script χρησιμοποιεί /sdcard/Download/Digital Footprint Finder/, μετά ~/Digital Footprint Finder/ και τέλος τον τρέχοντα κατάλογο. Τα αρχεία έχουν μορφή <username>_<timestamp>.txt, με προαιρετικά .json, .csv και .html εξαγωγές.`


</details>

<details>
<summary>Connections.py</summary>




**Τι Βοηθά Να Λύσεις:** Λειτουργία δικού σου πιστοποιημένου χώρου chat, video call και κοινής χρήσης αρχείων από το Termux, με έλεγχο ιδιοκτησίας μηνυμάτων και δικαιωμάτων πρόσβασης από τον server.

**Περιγραφή:** Αυτοφιλοξενούμενος server Connections για Termux που συνδυάζει chat σε πραγματικό χρόνο, κλήσεις βίντεο WebRTC, μεταφορά αρχείων σε τμήματα και το DedSec's Database σε ένα ενιαίο περιβάλλον με πιστοποίηση. Υποστηρίζει αρχεία έως 150 MB, ισχυρό αυτόματα δημιουργημένο μυστικό κλειδί μίας χρήσης, πρόσβαση μέσω Cloudflare και Tor, περιορισμό ρυθμού αιτημάτων, ενέργειες Database με προστασία CSRF, ταυτότητες και ιδιοκτησία μηνυμάτων που ελέγχονται από τον server, καθώς και δικαιώματα moderator όπου ο πρώτος χρήστης που συνδέεται μπορεί να διαγράφει οποιοδήποτε μήνυμα, ενώ οι υπόλοιποι μπορούν να διαγράφουν ή να επεξεργάζονται μόνο τα δικά τους. Τα αρχεία του chat μεταφέρονται σε προστατευμένα τμήματα αντί για υπερβολικά μεγάλα Socket.IO/Base64 μηνύματα και η πρόσβαση μέσω LAN είναι απενεργοποιημένη από προεπιλογή, εκτός αν ενεργοποιηθεί ρητά. Χρησιμοποίησέ το μόνο σε συστήματα και δίκτυα που σου ανήκουν ή έχεις άδεια να διαχειρίζεσαι.

**Τοποθεσία Αποθήκευσης:** `Τα κοινόχρηστα αρχεία αποθηκεύονται στο ~/Downloads/DedSec's Database/. Αν ο φάκελος δεν μπορεί να δημιουργηθεί, το fallback είναι ./DedSec_Database_Files/ στον τρέχοντα κατάλογο. Τα δεδομένα λειτουργίας του Tor αποθηκεύονται ξεχωριστά στο ~/.foxchat_tor/.`


</details>

<details>
<summary>Link Shield</summary>




**Τι Βοηθά Να Λύσεις:** Έλεγχος redirects, HTTPS, domains και ύποπτων URL patterns πριν ανοίξεις έναν άγνωστο σύνδεσμο.

**Περιγραφή:** Εργαλείο ελέγχου συνδέσμων: ακολουθεί redirects, ελέγχει HTTPS/SSL, εντοπίζει ύποπτα domains/μοτίβα και βγάζει αναφορά ρίσκου πριν ανοίξεις σύνδεσμο. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

**Τοποθεσία Αποθήκευσης:** `Δεν δημιουργείται ξεχωριστός φάκελος αποτελεσμάτων. Το linkshield_config_en.json, τα user-named JSON/Markdown αναφορές και τα linkshield_batch_report.json/.csv αποθηκεύονται στον τρέχοντα κατάλογο.`


</details>

<details>
<summary>Masker</summary>




**Τι Βοηθά Να Λύσεις:** Δημιουργία καθαρών test links και έλεγχος redirect behavior για δικά σου demos και εξουσιοδοτημένα awareness workflows.

**Περιγραφή:** URL helper για καθαρά, ευανάγνωστους δοκιμαστικούς συνδέσμους και έλεγχο συμπεριφορά ανακατεύθυνσης στα δικά σου workflows. Παρουσιάζεται μόνο για οργάνωση, demos και εξουσιοδοτημένη εκπαίδευση ευαισθητοποίησης, ποτέ για να κρύψει κακόβουλα links ή να ξεγελάσει κόσμο.

**Τοποθεσία Αποθήκευσης:** `Δεν αποθηκεύονται αρχεία. Το URL που δημιουργήθηκε εμφανίζεται στο terminal.`


</details>

<details>
<summary>QR Code Generator</summary>




**Τι Βοηθά Να Λύσεις:** Μετατροπή κειμένου ή links σε QR codes γρήγορα από Termux για sharing, testing ή έντυπες ροές.

**Περιγραφή:** Δημιουργός κωδικού QR βασισμένος σε Python που δημιουργεί κωδικούς QR για URLs και τους αποθηκεύει στο φάκελο Downloads/QR Codes. Διαθέτει αυτόματη εγκατάσταση εξαρτήσεων, φιλική προς τον χρήστη διεπαφή και χειρισμό σφαλμάτων για αξιόπιστη λειτουργία. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

**Τοποθεσία Αποθήκευσης:** `Τα εικόνες PNG που δημιουργούνται αποθηκεύονται στο ~/storage/downloads/QR Codes/.`


</details>

<details>
<summary>Sod</summary>




**Τι Βοηθά Να Λύσεις:** Μέτρηση της συμπεριφοράς εφαρμογής που ελέγχεις υπό φορτίο ώστε να εντοπίζονται performance limits πριν τα συναντήσουν πραγματικοί χρήστες.

**Περιγραφή:** Ένα ολοκληρωμένο εργαλείο δοκιμής φόρτου για εφαρμογές web, με πολλαπλές μεθόδους δοκιμής (HTTP, WebSocket, προσομοίωση βάσης δεδομένων, μεταφόρτωση αρχείων, μικτό φόρτο εργασίας), μετρήσεις σε πραγματικό χρόνο και αυτόματη εγκατάσταση εξαρτήσεων. Προηγμένο πλαίσιο δοκιμής απόδοσης με ρεαλιστική προσομοίωση συμπεριφοράς χρήστη. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

**Τοποθεσία Αποθήκευσης:** `Το αρχείο ρυθμίσεων load_test_config.json αποθηκεύεται στον τρέχοντα κατάλογο. Τα αποτελέσματα δοκιμών εμφανίζονται στο terminal και δεν γράφονται σε αρχείο αναφοράς.`


</details>

<details>
<summary>Store Scrapper</summary>




**Τι Βοηθά Να Λύσεις:** Εξαγωγή και οργάνωση δημόσιων δεδομένων προϊόντων/κατηγοριών από stores που επιτρέπεται να αναλύσεις αντί για χειροκίνητη συλλογή ανά σελίδα.

**Περιγραφή:** Μονοαρχείο Python store scrapper για Termux που λειτουργεί χωρίς root. Δοκιμάζει πολλούς τρόπους για να βρίσκει κατηγορίες και προϊόντα σε απλές HTML σελίδες αλλά και σε πολλά JS-style stores, διαβάζοντας HTML, JSON-LD, embedded JSON, sitemaps, Shopify endpoints, WooCommerce APIs, generic product cards, breadcrumbs, OpenGraph/meta tags και εσωτερικούς συνδέσμους. Αποθηκεύει όσο τρέχει, ξεκινά πλήρες scraping προϊόντος μόλις βρεθεί κάθε προϊόν, δείχνει live κατάσταση στο terminal, χρησιμοποιεί το Enter ως προεπιλογή στα prompts και οργανώνει τα αποτελέσματα σε φακέλους store/category/product με κατεβασμένες εικόνες. Χρησιμοποίησέ το μόνο σε συστήματα που σου ανήκουν ή έχεις ρητή άδεια να ελέγξεις.

**Τοποθεσία Αποθήκευσης:** `Τα δεδομένα προϊόντων αποθηκεύονται στο ~/storage/downloads/Store Scrapper/<Store>/<Category>/<Product>/. Αν το Termux Downloads δεν είναι διαθέσιμο, χρησιμοποιείται το ~/downloads/Store Scrapper/. Οι φάκελοι προϊόντων μπορούν να περιέχουν FOUND.txt, metadata.json, summary.txt, description.txt, images/ και images.json, ενώ τα αρχεία εντοπισμού και κατάστασης εκτέλεσης μένουν στη δομή αποτελεσμάτων του καταστήματος.`


</details>


<a id="greek-personal-information-capture"></a>

<h2>Συλλογή Προσωπικών Πληροφοριών (Μόνο για Εκπαιδευτική Χρήση)</h2>


Αυτά τα scripts είναι training simulations που έχουν στόχο να βοηθούν τους χρήστες να κατανοούν πώς μπορεί να παρουσιάζονται παραπλανητικές σελίδες συλλογής προσωπικών δεδομένων, ώστε να τις αναγνωρίζουν και να αμύνονται καλύτερα απέναντί τους σε ελεγχόμενα περιβάλλοντα.

<details>
<summary>Fake Back Camera Page</summary>




**Τι Βοηθά Να Λύσεις:** Εκτέλεση εξουσιοδοτημένων awareness demos που δείχνουν πώς παραπλανητικές σελίδες μπορεί να ζητούν πρόσβαση στην κάμερα, ώστε να αναγνωρίζονται ευκολότερα permission prompts και social-engineering risks.

**Περιγραφή:** Το Fake Back Camera Page είναι εκπαιδευτική επίδειξη ευαισθητοποίησης με συναίνεση για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Back Camera. Χρησιμοποίησέ το μόνο σε ελεγχόμενο εργαστήριο, με δοκιμαστικά δεδομένα, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Οι καταγεγραμμένες εικόνες της πίσω κάμερας και τα σχετικά δεδομένα κειμένου αποθηκεύονται στο ~/storage/downloads/Camera-Phish-Back/.`


</details>

<details>
<summary>Fake Back Camera Video Page</summary>




**Τι Βοηθά Να Λύσεις:** Εκτέλεση εξουσιοδοτημένων awareness demos που δείχνουν πώς παραπλανητικές σελίδες μπορεί να ζητούν πρόσβαση στην κάμερα, ώστε να αναγνωρίζονται ευκολότερα permission prompts και social-engineering risks.

**Περιγραφή:** Το Fake Back Camera Video Page είναι εκπαιδευτική επίδειξη ευαισθητοποίησης με συναίνεση για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Back Camera Video. Χρησιμοποίησέ το μόνο σε ελεγχόμενο εργαστήριο, με δοκιμαστικά δεδομένα, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα καταγεγραμμένα βίντεο WEBM της πίσω κάμερας και τα σχετικά δεδομένα κειμένου αποθηκεύονται στο ~/storage/downloads/Back Camera Videos/.`


</details>

<details>
<summary>Fake Card Details Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο lab του πώς fake verification/data-entry flows μπορούν να πιέσουν χρήστες να μοιραστούν ευαίσθητες πληροφορίες, ώστε αυτά τα patterns να αναγνωρίζονται ευκολότερα.

**Περιγραφή:** Το Fake Card Details Page είναι εκπαιδευτική επίδειξη ευαισθητοποίησης με συναίνεση για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Card Details. Χρησιμοποίησέ το μόνο σε ελεγχόμενο εργαστήριο, με δοκιμαστικά δεδομένα, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα υποβληθέντα δεδομένα ενεργοποίησης κάρτας αποθηκεύονται στο ~/storage/downloads/CardActivations/.`


</details>

<details>
<summary>Fake Chrome Verification Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο lab του πώς fake verification/data-entry flows μπορούν να πιέσουν χρήστες να μοιραστούν ευαίσθητες πληροφορίες, ώστε αυτά τα patterns να αναγνωρίζονται ευκολότερα.

**Περιγραφή:** Το Fake Chrome Verification Page είναι εκπαιδευτική επίδειξη ευαισθητοποίησης με συναίνεση για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Chrome Verification. Χρησιμοποίησέ το μόνο σε ελεγχόμενο εργαστήριο, με δοκιμαστικά δεδομένα, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα δεδομένα επαλήθευσης του Chrome, μαζί με τα σχετικά αρχεία καταγραφής και τις συνοπτικές αναφορές, αποθηκεύονται στον φάκελο ~/storage/downloads/Chrome Verification/.`


</details>

<details>
<summary>Fake Data Grabber Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο lab του πώς fake verification/data-entry flows μπορούν να πιέσουν χρήστες να μοιραστούν ευαίσθητες πληροφορίες, ώστε αυτά τα patterns να αναγνωρίζονται ευκολότερα.

**Περιγραφή:** Το Fake Data Grabber Page είναι εκπαιδευτική επίδειξη ευαισθητοποίησης με συναίνεση για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Data Grabber. Χρησιμοποίησέ το μόνο σε ελεγχόμενο εργαστήριο, με δοκιμαστικά δεδομένα, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα collected application information αποθηκεύονται στο ~/storage/downloads/Peoples_Lives/, μαζί με το application_info.txt.`


</details>

<details>
<summary>Fake Discord Verification Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο lab του πώς fake verification/data-entry flows μπορούν να πιέσουν χρήστες να μοιραστούν ευαίσθητες πληροφορίες, ώστε αυτά τα patterns να αναγνωρίζονται ευκολότερα.

**Περιγραφή:** Το Fake Discord Verification Page είναι εκπαιδευτική επίδειξη ευαισθητοποίησης με συναίνεση για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Discord Verification. Χρησιμοποίησέ το μόνο σε ελεγχόμενο εργαστήριο, με δοκιμαστικά δεδομένα, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα δεδομένα επαλήθευσης του Discord, μαζί με τα σχετικά αρχεία καταγραφής και τις συνοπτικές αναφορές, αποθηκεύονται στον φάκελο ~/storage/downloads/Discord Verification/.`


</details>

<details>
<summary>Fake Facebook Verification Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο lab του πώς fake verification/data-entry flows μπορούν να πιέσουν χρήστες να μοιραστούν ευαίσθητες πληροφορίες, ώστε αυτά τα patterns να αναγνωρίζονται ευκολότερα.

**Περιγραφή:** Το Fake Facebook Verification Page είναι εκπαιδευτική επίδειξη ευαισθητοποίησης με συναίνεση για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Facebook Verification. Χρησιμοποίησέ το μόνο σε ελεγχόμενο εργαστήριο, με δοκιμαστικά δεδομένα, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα δεδομένα επαλήθευσης του Facebook, μαζί με τα σχετικά αρχεία καταγραφής και τις συνοπτικές αναφορές, αποθηκεύονται στον φάκελο ~/storage/downloads/Facebook Verification/.`


</details>

<details>
<summary>Fake Front Camera Page</summary>




**Τι Βοηθά Να Λύσεις:** Εκτέλεση εξουσιοδοτημένων awareness demos που δείχνουν πώς παραπλανητικές σελίδες μπορεί να ζητούν πρόσβαση στην κάμερα, ώστε να αναγνωρίζονται ευκολότερα permission prompts και social-engineering risks.

**Περιγραφή:** Το Fake Front Camera Page είναι εκπαιδευτική επίδειξη ευαισθητοποίησης με συναίνεση για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Front Camera. Χρησιμοποίησέ το μόνο σε ελεγχόμενο εργαστήριο, με δοκιμαστικά δεδομένα, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Οι καταγεγραμμένες εικόνες της μπροστινής κάμερας και τα σχετικά δεδομένα κειμένου αποθηκεύονται στο ~/storage/downloads/Camera-Phish-Front/.`


</details>

<details>
<summary>Fake Front Camera Video Page</summary>




**Τι Βοηθά Να Λύσεις:** Εκτέλεση εξουσιοδοτημένων awareness demos που δείχνουν πώς παραπλανητικές σελίδες μπορεί να ζητούν πρόσβαση στην κάμερα, ώστε να αναγνωρίζονται ευκολότερα permission prompts και social-engineering risks.

**Περιγραφή:** Το Fake Front Camera Video Page είναι εκπαιδευτική επίδειξη ευαισθητοποίησης με συναίνεση για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Front Camera Video. Χρησιμοποίησέ το μόνο σε ελεγχόμενο εργαστήριο, με δοκιμαστικά δεδομένα, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα καταγεγραμμένα βίντεο WEBM της μπροστινής κάμερας και τα σχετικά δεδομένα κειμένου αποθηκεύονται στο ~/storage/downloads/Front Camera Videos/.`


</details>

<details>
<summary>Fake Google Location Page</summary>




**Τι Βοηθά Να Λύσεις:** Εκτέλεση εξουσιοδοτημένων awareness demos που δείχνουν πώς παραπλανητικές σελίδες μπορεί να ζητούν ή να εκθέτουν δεδομένα τοποθεσίας.

**Περιγραφή:** Το Fake Google Location Page είναι εκπαιδευτική επίδειξη ευαισθητοποίησης με συναίνεση για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Google Location. Χρησιμοποίησέ το μόνο σε ελεγχόμενο εργαστήριο, με δοκιμαστικά δεδομένα, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αρχεία τοποθεσίας JSON αποθηκεύονται στον φάκελο ~/storage/downloads/Locations/.`


</details>

<details>
<summary>Fake Instagram Verification Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο lab του πώς fake verification/data-entry flows μπορούν να πιέσουν χρήστες να μοιραστούν ευαίσθητες πληροφορίες, ώστε αυτά τα patterns να αναγνωρίζονται ευκολότερα.

**Περιγραφή:** Το Fake Instagram Verification Page είναι εκπαιδευτική επίδειξη ευαισθητοποίησης με συναίνεση για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Instagram Verification. Χρησιμοποίησέ το μόνο σε ελεγχόμενο εργαστήριο, με δοκιμαστικά δεδομένα, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα δεδομένα επαλήθευσης του Instagram, μαζί με τα σχετικά αρχεία καταγραφής και τις συνοπτικές αναφορές, αποθηκεύονται στον φάκελο ~/storage/downloads/Instagram Verification/.`


</details>

<details>
<summary>Fake Location Page</summary>




**Τι Βοηθά Να Λύσεις:** Εκτέλεση εξουσιοδοτημένων awareness demos που δείχνουν πώς παραπλανητικές σελίδες μπορεί να ζητούν ή να εκθέτουν δεδομένα τοποθεσίας.

**Περιγραφή:** Το Fake Location Page είναι εκπαιδευτική επίδειξη ευαισθητοποίησης με συναίνεση για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Location. Χρησιμοποίησέ το μόνο σε ελεγχόμενο εργαστήριο, με δοκιμαστικά δεδομένα, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αρχεία τοποθεσίας JSON αποθηκεύονται στον φάκελο ~/storage/downloads/Locations/.`


</details>

<details>
<summary>Fake Microphone Page</summary>




**Τι Βοηθά Να Λύσεις:** Εκτέλεση εξουσιοδοτημένων awareness demos που δείχνουν πώς παραπλανητικές σελίδες μπορεί να ζητούν πρόσβαση στο μικρόφωνο.

**Περιγραφή:** Το Fake Microphone Page είναι εκπαιδευτική επίδειξη ευαισθητοποίησης με συναίνεση για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Microphone. Χρησιμοποίησέ το μόνο σε ελεγχόμενο εργαστήριο, με δοκιμαστικά δεδομένα, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα καταγεγραμμένα audio, τα converted WAV files και τα σχετικά δεδομένα κειμένου αποθηκεύονται στο ~/storage/downloads/Recordings/.`


</details>

<details>
<summary>Fake OnlyFans Verification Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο lab του πώς fake verification/data-entry flows μπορούν να πιέσουν χρήστες να μοιραστούν ευαίσθητες πληροφορίες, ώστε αυτά τα patterns να αναγνωρίζονται ευκολότερα.

**Περιγραφή:** Το Fake OnlyFans Verification Page είναι εκπαιδευτική επίδειξη ευαισθητοποίησης με συναίνεση για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από OnlyFans Verification. Χρησιμοποίησέ το μόνο σε ελεγχόμενο εργαστήριο, με δοκιμαστικά δεδομένα, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα δεδομένα επαλήθευσης του OnlyFans, μαζί με τα σχετικά αρχεία καταγραφής και τις συνοπτικές αναφορές, αποθηκεύονται στον φάκελο ~/storage/downloads/OnlyFans Verification/.`


</details>

<details>
<summary>Fake Steam Verification Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο lab του πώς fake verification/data-entry flows μπορούν να πιέσουν χρήστες να μοιραστούν ευαίσθητες πληροφορίες, ώστε αυτά τα patterns να αναγνωρίζονται ευκολότερα.

**Περιγραφή:** Το Fake Steam Verification Page είναι εκπαιδευτική επίδειξη ευαισθητοποίησης με συναίνεση για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Steam Verification. Χρησιμοποίησέ το μόνο σε ελεγχόμενο εργαστήριο, με δοκιμαστικά δεδομένα, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα δεδομένα επαλήθευσης του Steam, μαζί με τα σχετικά αρχεία καταγραφής και τις συνοπτικές αναφορές, αποθηκεύονται στον φάκελο ~/storage/downloads/Steam Verification/.`


</details>

<details>
<summary>Fake Twitch Verification Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο lab του πώς fake verification/data-entry flows μπορούν να πιέσουν χρήστες να μοιραστούν ευαίσθητες πληροφορίες, ώστε αυτά τα patterns να αναγνωρίζονται ευκολότερα.

**Περιγραφή:** Το Fake Twitch Verification Page είναι εκπαιδευτική επίδειξη ευαισθητοποίησης με συναίνεση για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από Twitch Verification. Χρησιμοποίησέ το μόνο σε ελεγχόμενο εργαστήριο, με δοκιμαστικά δεδομένα, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα δεδομένα επαλήθευσης του Twitch, μαζί με τα σχετικά αρχεία καταγραφής και τις συνοπτικές αναφορές, αποθηκεύονται στον φάκελο ~/storage/downloads/Twitch Verification/.`


</details>

<details>
<summary>Fake YouTube Verification Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο lab του πώς fake verification/data-entry flows μπορούν να πιέσουν χρήστες να μοιραστούν ευαίσθητες πληροφορίες, ώστε αυτά τα patterns να αναγνωρίζονται ευκολότερα.

**Περιγραφή:** Το Fake YouTube Verification Page είναι εκπαιδευτική επίδειξη ευαισθητοποίησης με συναίνεση για να δείχνει πώς παραπλανητικά permission prompts μπορούν να πιέσουν κάποιον να μοιραστεί ευαίσθητη πρόσβαση γύρω από YouTube Verification. Χρησιμοποίησέ το μόνο σε ελεγχόμενο εργαστήριο, με δοκιμαστικά δεδομένα, screenshots ή καθαρή άδεια από συμμετέχοντες. Δεν παρουσιάζεται ως εργαλείο κλοπής πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα δεδομένα επαλήθευσης του YouTube, μαζί με τα σχετικά αρχεία καταγραφής και τις συνοπτικές αναφορές, αποθηκεύονται στον φάκελο ~/storage/downloads/YouTube Verification/.`


</details>


<a id="greek-fake-pages"></a>

<h2>Ψεύτικες Σελίδες (Μόνο για Εκπαιδευτική Χρήση)</h2>


Αυτά τα scripts είναι εκπαιδευτικά simulations που έχουν στόχο να βοηθούν τους χρήστες να αναγνωρίζουν social-engineering patterns, ψεύτικες reward pages, ψεύτικες verification flows και imitation brand pages που συχνά χρησιμοποιούνται για να πιέζουν ανθρώπους σε μη ασφαλείς ενέργειες.

<details>
<summary>Fake Apple iCloud Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake Apple iCloud Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Apple iCloud προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/Apple iCloud/.`


</details>

<details>
<summary>Fake Discord Nitro Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake Discord Nitro Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Discord Nitro προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/Discord Nitro/.`


</details>

<details>
<summary>Fake Epic Games Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake Epic Games Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Epic Games προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/Epic Games/.`


</details>

<details>
<summary>Fake Facebook Friends Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake Facebook Friends Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Facebook Friends προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/Facebook Friends/.`


</details>

<details>
<summary>Fake Free Robux Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake Free Robux Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Free Robux προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/Roblox Robux/.`


</details>

<details>
<summary>Fake GitHub Pro Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake GitHub Pro Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες GitHub Pro προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/GitHub Pro/.`


</details>

<details>
<summary>Fake Google Free Money Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake Google Free Money Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Google Free Money προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/Google Free Money/.`


</details>

<details>
<summary>Fake Instagram Followers Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake Instagram Followers Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Instagram Followers προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/Instagram Followers/.`


</details>

<details>
<summary>Fake MetaMask Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake MetaMask Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες MetaMask προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/MetaMask/.`


</details>

<details>
<summary>Fake Microsoft 365 Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake Microsoft 365 Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Microsoft 365 προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/Microsoft 365/.`


</details>

<details>
<summary>Fake OnlyFans Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake OnlyFans Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες OnlyFans προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/OnlyFans/.`


</details>

<details>
<summary>Fake PayPal Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake PayPal Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες PayPal προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας και της κάρτας γράφονται στον φάκελο ~/storage/downloads/PayPal/.`


</details>

<details>
<summary>Fake Pinterest Pro Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake Pinterest Pro Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Pinterest Pro προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/Pinterest Pro/.`


</details>

<details>
<summary>Fake PlayStation Network Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake PlayStation Network Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες PlayStation Network προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/PlayStation Network/.`


</details>

<details>
<summary>Fake Reddit Karma Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake Reddit Karma Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Reddit Karma προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/Reddit Karma/.`


</details>

<details>
<summary>Fake Snapchat Friends Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake Snapchat Friends Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Snapchat Friends προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/Snapchat Friends/.`


</details>

<details>
<summary>Fake Steam Games Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake Steam Games Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Steam Games προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/Steam Games/.`


</details>

<details>
<summary>Fake Steam Wallet Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake Steam Wallet Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Steam Wallet προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/Steam Wallet/.`


</details>

<details>
<summary>Fake TikTok Followers Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake TikTok Followers Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες TikTok Followers προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/TikTok Followers/.`


</details>

<details>
<summary>Fake Trust Wallet Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake Trust Wallet Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Trust Wallet προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/Trust Wallet/.`


</details>

<details>
<summary>Fake Twitch Subs Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake Twitch Subs Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Twitch Subs προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/Twitch Subs/.`


</details>

<details>
<summary>Fake Twitter Followers Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake Twitter Followers Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Twitter Followers προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/Twitter Followers/.`


</details>

<details>
<summary>Fake What's Up Dude Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake What's Up Dude Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες What's Up Dude προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/WhatsUp Dude/.`


</details>

<details>
<summary>Fake Xbox Live Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake Xbox Live Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες Xbox Live προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/Xbox Live/.`


</details>

<details>
<summary>Fake YouTube Subscribers Page</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη σε εξουσιοδοτημένο phishing-awareness lab του πώς μια πειστική look-alike προσφορά ή login page μπορεί να παραπλανήσει χρήστες.

**Περιγραφή:** Το Fake YouTube Subscribers Page είναι mock phishing-awareness page για να δείχνει πώς ψεύτικες YouTube Subscribers προσφορές, giveaways, upgrades ή login prompts χειραγωγούν την εμπιστοσύνη. Χρησιμοποίησέ το μόνο για εκπαίδευση, screenshots ή consent-based training με dummy accounts. Ποτέ για συλλογή πραγματικών credentials, καρτών, wallets ή προσωπικών πληροφοριών.

**Τοποθεσία Αποθήκευσης:** `Τα αποθηκευμένα δεδομένα της φόρμας γράφονται στον φάκελο ~/storage/downloads/YouTube Subscribers/.`


</details>


<a id="greek-games"></a>

<h2>Παιχνίδια</h2>


<details>
<summary>Buzz</summary>




**Τι Βοηθά Να Λύσεις:** Εξάσκηση σε λογική προγραμματισμού, terminal interaction και δομή project μέσα από ένα playable local experience.

**Περιγραφή:** Ένα text-only παιχνίδι trivia για Termux με ενσωματωμένη σταθερή βάση 15.000 ερωτήσεων (χωρίς δημιουργία κατά την εκτέλεση). Υποστηρίζει 1–2 παίκτες (pass-and-play), πολλούς τύπους γύρων, φίλτρο δυσκολίας (Όλες/Εύκολες/Μέτριες/Δύσκολες), προφίλ, ρυθμίσεις και πίνακες βαθμολογίας. Ελαφρύ παιχνίδι τερματικού με γρήγορους χειρισμούς και δυνατότητα επανάληψης.

**Τοποθεσία Αποθήκευσης:** `Όλα τα δεδομένα του παιχνιδιού αποθηκεύονται στο ~/Buzz/data/: questions_en.jsonl.gz, highscores.json, profiles.json και settings.json.`


</details>

<details>
<summary>CTF God</summary>




**Τι Βοηθά Να Λύσεις:** Εξάσκηση σε λογική προγραμματισμού, terminal interaction και δομή project μέσα από ένα playable local experience.

**Περιγραφή:** Πλήρες CTF παιχνίδι για Termux σε fullscreen Curses, με story mode, αποστολές, daily challenges, τυχαία boss levels, κατάστημα hints, achievements & ranks, εισαγωγή/εξαγωγή challenge packs, tournament mode και anti‑cheat/integrity checks. Περιλαμβάνει ενσωματωμένο level editor. Ελαφρύ παιχνίδι τερματικού με γρήγορους χειρισμούς και δυνατότητα επανάληψης.

**Τοποθεσία Αποθήκευσης:** `Οι χώροι εργασίας των προκλήσεων αποθηκεύονται στο /storage/emulated/0/Download/CTF God/, με εναλλακτικές διαδρομές τα ~/storage/downloads/CTF God/ και ~/CTF God/. Τα προφίλ, πρόοδος, πακέτα και προσαρμοσμένες προκλήσεις αποθηκεύονται στο ~/.ctf_god/ (state.json, custom.json, packs/).`


</details>

<details>
<summary>Detective</summary>




**Τι Βοηθά Να Λύσεις:** Εξάσκηση σε λογική προγραμματισμού, terminal interaction και δομή project μέσα από ένα playable local experience.

**Περιγραφή:** Ένα story-driven παιχνίδι ντετέκτιβ για Termux στο terminal με διευρυμένη σταθερή βιβλιοθήκη υποθέσεων, πλουσιότερα lore dossiers, φήμες περιοχών, side stories και επιπλέον story threads. Παρακολουθήστε στοιχεία, ανακρίνετε υπόπτους, δείτε suspect rosters, χτίστε ASCII case board και timeline και διαχειριστείτε την πρόοδο με 3 save slots και autosave. Περιλαμβάνει 4 δυσκολίες, notes/evidence tracking, checkpoint hints και γρήγορες εντολές όπως :help, :guide, :lore, :suspects, :board, :timeline, :hint και :save.

**Τοποθεσία Αποθήκευσης:** `Όλες οι αποθηκεύσεις αποθηκεύονται στο ~/Detective/: player.json, highscores.json και savegame_slot1.json έως savegame_slot3.json.`


</details>

<details>
<summary>Tamagotchi</summary>




**Τι Βοηθά Να Λύσεις:** Εξάσκηση σε λογική προγραμματισμού, terminal interaction και δομή project μέσα από ένα playable local experience.

**Περιγραφή:** Ένα πλήρως χαρακτηριστικό παιχνίδι κατοικίδιου terminal. Τρέφετε, παίζετε, καθαρίζετε και εκπαιδεύετε το κατοικίδιό σας. Μην το αφήσετε να πεθάνει. Προηγμένο παιχνίδι προσομοίωσης εικονικού κατοικίδιου με ολοκληρωμένο σύστημα διαχείρισης. Χαρακτηριστικά περιλαμβάνουν εξέλιξη κατοικίδιου μέσα από στάδια ζωής, χαρακτηριστικά προσωπικότητας, ανάπτυξη δεξιοτήτων, μίνι παιχνίδια, σύστημα εργασίας και συνταξιοδότηση κληρονομιάς. Ελαφρύ παιχνίδι τερματικού με γρήγορους χειρισμούς και δυνατότητα επανάληψης.

**Τοποθεσία Αποθήκευσης:** `Η αποθήκευση του Tamagotchi αποθηκεύεται στο ~/.termux_tamagotchi_v8.json.`


</details>

<details>
<summary>Pet Friends</summary>




**Τι Βοηθά Να Λύσεις:** Εξάσκηση σε λογική προγραμματισμού, terminal interaction και δομή project μέσα από ένα playable local experience.

**Περιγραφή:** Το Pet Friends.py είναι ένα fullscreen idle παιχνίδι εικονικών συντρόφων για Termux με πάνω από 160 πραγματικά, θρυλικά και μυθικά κατοικίδια. Υιοθέτησε, τάισε, χάιδεψε, πλύνε, εκπαίδευσε, δέσου, μετονόμασε, άλλαξε χρώμα και εξέλιξε τους συντρόφους σου, ολοκληρώνοντας quests, contracts, expeditions, achievements, festivals, adventure-board progress και crates με διαφορετικές σπανιότητες. Περιλαμβάνει animated ASCII pets, τοπικά παραγόμενα sound effects και συνεχή background music, εκπαιδευτικά facts για κάθε είδος με τη μυθολογία καθαρά επισημασμένη, economy και upgrades, care requests, local-network battles και trades, καθώς και μόνιμη αποθήκευση προόδου χωρίς third-party Python packages.

**Τοποθεσία Αποθήκευσης:** `Η πρόοδος του παιχνιδιού αποθηκεύεται στο ~/Pet Friends/petfriends_save.json. Τα παραγόμενα sound effects και η background music αποθηκεύονται στο ~/Pet Friends/sounds/.`


</details>

<details>
<summary>Terminal Arcade</summary>




**Τι Βοηθά Να Λύσεις:** Εξάσκηση σε λογική προγραμματισμού, terminal interaction και δομή project μέσα από ένα playable local experience.

**Περιγραφή:** Πακέτο arcade για τερματικό με πολλά mini-games σε ένα script. Αποθηκεύει δεδομένα στο ~/Terminal Arcade/ και τρέχει ομαλά σε Termux/Linux. Ελαφρύ παιχνίδι τερματικού με γρήγορους χειρισμούς και δυνατότητα επανάληψης.

**Τοποθεσία Αποθήκευσης:** `Τα δεδομένα του arcade αποθηκεύονται στο ~/Terminal Arcade/. Τα υψηλότερες βαθμολογίες και το πρόσφατο ιστορικό βαθμολογιών αποθηκεύονται στο ~/Terminal Arcade/highscores.json.`


</details>


<a id="greek-other-tools"></a>

<h2>Άλλα Εργαλεία</h2>


<details>
<summary>Android App Launcher</summary>




**Τι Βοηθά Να Λύσεις:** Εκκίνηση και οργάνωση Android εφαρμογών από Termux-centered workflow όταν θέλεις γρηγορότερη πρόσβαση από το terminal.

**Περιγραφή:** Βοηθητικό πρόγραμμα για διαχείριση εφαρμογών Android απευθείας από το terminal. Μπορεί να εκκινήσει εφαρμογές, να εξάγει αρχεία APK, να απεγκαταστήσει εφαρμογές και να αναλύσει δικαιώματα ασφαλείας. Προηγμένο εργαλείο διαχείρισης εφαρμογών Android και ανάλυσης ασφαλείας. Σχεδιασμένο για το Termux, με σαφείς οδηγίες και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Τα αρχεία APK που εξάγονται αποθηκεύονται στον φάκελο ~/storage/shared/Download/Extracted APK's/. Οι αναφορές ασφαλείας αποθηκεύονται στο ~/storage/shared/Download/App_Security_Reports/ με όνομα <app>_security_report.txt.`


</details>

<details>
<summary>Loading Screen</summary>




**Τι Βοηθά Να Λύσεις:** Προσθήκη επαναχρησιμοποιήσιμου loading/transition experience σε local projects ώστε τα μεγάλα startup βήματα να είναι πιο ξεκάθαρα στον χρήστη.

**Περιγραφή:** Εξατομίκευση εκκίνησης Termux με ASCII art loading screens. Υποστηρίζει custom art, καθυστέρηση και αυτόματο setup/cleanup για εμφάνιση μία φορά. Σχεδιασμένο για το Termux, με σαφείς οδηγίες και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Δεν δημιουργείται ξεχωριστός φάκελος αποτελεσμάτων. Το επιλεγμένη οθόνη φόρτωσης γράφεται απευθείας στο ~/.bash_profile.`


</details>

<details>
<summary>Password Master</summary>




**Τι Βοηθά Να Λύσεις:** Δημιουργία και διαχείριση ισχυρότερων ροών password generation/checking αντί για εύκολα απομνημονεύσιμα αλλά αδύναμα patterns.

**Περιγραφή:** Ολοκληρωμένο σύνολο διαχείρισης κωδικών πρόσβασης με κρυπτογραφημένη αποθήκευση θησαυροφυλακίου, δημιουργία κωδικών, ανάλυση ισχύος και εργαλεία βελτίωσης. Περιλαμβάνει AES-256 κρυπτογραφημένο θησαυροφυλάκιο με προστασία κύριου κωδικού πρόσβασης, γεννήτρια τυχαίων κωδικών, γεννήτρια φράσεων πρόσβασης, αναλυτή ισχύος κωδικού και προτάσεις βελτίωσης κωδικών. Σχεδιασμένο για το Termux, με σαφείς οδηγίες και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Το encrypted vault αποθηκεύεται ως ./my_vault.enc στον τρέχοντα κατάλογο. Τα αντίγραφα ασφαλείας αποθηκεύονται στο /storage/emulated/0/Download/Password Master Backup/vault_backup.enc ή στο ~/Downloads/Password Master Backup/ εκτός Android.`


</details>

<details>
<summary>Termux Backup Restore</summary>




**Τι Βοηθά Να Λύσεις:** Δημιουργία και επαναφορά backups αρχείων Termux πριν από updates, migrations ή αλλαγές με ρίσκο.

**Περιγραφή:** Δημιουργία και επαναφορά αντιγράφων ασφαλείας για Termux: δημιουργεί συμπιεσμένο αντίγραφο ασφαλείας των αρχείων σου στα Downloads και μπορεί να τα επαναφέρει με ελέγχους ακεραιότητας. Σχεδιασμένο για το Termux, με σαφείς οδηγίες και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Το αρχείο αντιγράφου ασφαλείας αποθηκεύεται ως /storage/emulated/0/Download/name_backup.zip. Τα τμήματα διαχωρισμένου αρχείου δημιουργούνται δίπλα στο archive. Το backup_config.json αποθηκεύεται στον τρέχοντα κατάλογο.`


</details>

<details>
<summary>Termux Repair Wizard</summary>




**Τι Βοηθά Να Λύσεις:** Διάγνωση συνηθισμένων προβλημάτων setup/packages στο Termux μέσω καθοδηγούμενης ροής αντί για τυχαίες εντολές.

**Περιγραφή:** Το DedSec Termux Repair Wizard είναι ένα πακέτο διάγνωσης και επιδιόρθωσης χωρίς root για σφάλματα αποθετηρίων και mirrors, αποτυχίες apt/dpkg, πρόσβαση στον αποθηκευτικό χώρο, δικαιώματα, TLS certificates, προσωρινά αρχεία, Python/pip και προβλήματα shell/PATH. Η λειτουργία Script Keeper σαρώνει ένα script ή ολόκληρο φάκελο χωρίς να εκτελεί άμεσα τα scripts, αναγνωρίζει περισσότερες από 20 γλώσσες μαζί με αρχεία χωρίς επέκταση που περιέχουν shebang, ελέγχει σύνταξη, περιβάλλοντα εκτέλεσης, εντολές, imθύρες, modules και συνηθισμένα αρχεία manifest έργων, και μπορεί μετά από επιβεβαίωση να εγκαταστήσει εξαρτήσεις που λείπουν από Termux ή από τα αντίστοιχα διαχειριστές πακέτων κάθε γλώσσας. Για νεότερες εκδόσεις Python δοκιμάζει επίσης συμβατά εναλλακτικά πακέτα για modules της βασικής βιβλιοθήκης που έχουν αφαιρεθεί. Κάθε εκτέλεση του Script Keeper δημιουργεί κατηγοριοποιημένη αναφορά με εγκαταστάσεις, διορθώσεις, προειδοποιήσεις, αποτυχίες και συντακτικά προβλήματα.

**Τοποθεσία Αποθήκευσης:** `Οι περισσότερες επιδιορθώσεις εφαρμόζονται απευθείας στα πακέτα του Termux, στα δικαιώματα αποθήκευσης, στα $HOME δικαιώματα και σε αρχεία κελύφους όπως ~/.bashrc, ~/.profile και ~/.zshrc. Οι αναφορές του Script Keeper αποθηκεύονται ως ~/DedSec/logs/script_keeper_<timestamp>.log.`


</details>


<a id="greek-no-category"></a>

<h2>Χωρίς Κατηγορία</h2>


<details>
<summary>Extra Content</summary>




**Τι Βοηθά Να Λύσεις:** Εύρεση προαιρετικών resources, templates και bonus υλικού χωρίς χειροκίνητη αναζήτηση σε όλο το repository.

**Περιγραφή:** Κόμβος extra περιεχομένου: γρήγορη πρόσβαση σε πρόσθετους πόρους, templates και προαιρετικά add-ons του DedSec toolkit. Σχεδιασμένο για το Termux, με σαφείς οδηγίες και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Ο φάκελος Extra Content του repository αντιγράφεται στο ~/storage/downloads/Extra Content/.`


</details>

<details>
<summary>Settings.py</summary>




**Τι Βοηθά Να Λύσεις:** Έλεγχος updates, menus, γλώσσας, backups, GitHub σύνδεσης, sponsor scripts και άλλων ρυθμίσεων του DedSec Project από έναν launcher.

**Περιγραφή:** Το Settings.py είναι ο κεντρικός πίνακας ελέγχου του DedSec Project. Εμφανίζει πληροφορίες για το έργο και τη συσκευή, ενημερώνει το έργο από την κύρια ή την εφεδρική πηγή, ανανεώνει πακέτα του Termux και λειτουργικές μονάδες της Python, ελέγχει και κατεβάζει scripts αποκλειστικά για χορηγούς μέσω συνδεδεμένου λογαριασμού GitHub, δημιουργεί αντίγραφο ασφαλείας στις Λήψεις, αλλάζει το prompt του Termux, διαχειρίζεται τη σύνδεση με το GitHub και εμφανίζει στατιστικά χρήσης. Υποστηρίζει επίσης προαιρετικά εργαλεία VPN και Tor, διαφορετικά στυλ μενού, αυτόματη εκκίνηση, επιλογή Αγγλικών ή Ελληνικών, προβολή συντελεστών και ασφαλή απεγκατάσταση. Το DedSec OS προσθέτει έναν τοπικό χώρο εργασίας μέσω προγράμματος περιήγησης, με διαχείριση αρχείων και συνεδριών, ασφαλή επεξεργαστή κειμένου, προβολή τερματικού, εκκίνηση εφαρμογών, ειδοποιήσεις, πλήρη ή διαιρεμένη προβολή, ρυθμίσεις εμφάνισης, έλεγχο γλώσσας και prompt, σύνδεση με κωδικό, προαιρετικό έλεγχο δύο παραγόντων και ανάκτηση μέσω τριών ερωτήσεων ασφαλείας. Σχεδιασμένο για το Termux, με σαφείς οδηγίες και οργανωμένα αποτελέσματα.

**Τοποθεσία Αποθήκευσης:** `Γλώσσα: ~/Language.json | Αντίγραφο ρυθμίσεων Termux: ~/Termux.zip | Αρχείο έργου: /storage/emulated/0/Download/DedSec Project Legacy Save.zip | Λογαριασμός GitHub: ~/.dedsec_github_account.json | Στατιστικά χρήσης: ~/.dedsec_termux_usage_stats.json | Δεδομένα εργαλείων δικτύου: ~/.dedsec_network_utilities/ και ~/.dedsec_network_utilities.json.`


</details>

<details>
<summary>DedSec Market</summary>




**Τι Βοηθά Να Λύσεις:** Περιήγηση, εγκατάσταση, ενημέρωση και εκκίνηση υποστηριζόμενων GitHub projects από phone-friendly Termux interface.

**Περιγραφή:** Curses-based market αποθετηρίων GitHub για Termux που εμφανίζει τα projects με το όνομα του project αντί για το ακατέργαστο όνομα του repository. Καθαρίζει και εμφανίζει σωστά το κείμενο των README, δείχνει releases και issues, υποστηρίζει ενέργειες install/update/delete και launch, κρατά watchlist και αποθηκεύει cache/state για πιο γρήγορη επαναχρησιμοποίηση. Σχεδιασμένο για το Termux, με σαφείς οδηγίες και οργανωμένα αποτελέσματα.

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




**Τι Βοηθά Να Λύσεις:** Πειραματισμός με face detection σε επιτρεπόμενες εικόνες ή camera input ως sponsor-only εργαλείο computer vision.

**Περιγραφή:** Τοπικό browser-based εργαλείο ανάλυσης προσώπου για Termux που λειτουργεί χωρίς root. Χρησιμοποιεί MediaPipe Face Mesh στο live feed της κάμερας, υποστηρίζει μπροστινή και πίσω κάμερα, παρακολουθεί έως και 3 πρόσωπα, σχεδιάζει αναλυτικά facial landmark overlays αντί για απλά boxes και επιτρέπει επίσης upload φωτογραφιών ή βίντεο για ανάλυση απευθείας από το interface. Μπορεί να τραβά PNG snapshots, να γράφει WEBM βίντεο, να αποθηκεύει ξεχωριστά cropped detected faces και να παρέχει τόσο local network link όσο και προαιρετικό δημόσιο Cloudflare link.

**Τοποθεσία Αποθήκευσης:** `Στο Termux, τα captures, τα recordings, τα uploaded results και τα αποθηκευμένα face crops μπαίνουν στο: ~/storage/downloads/Face Detector/. Αν το storage του Termux δεν είναι διαθέσιμο, γίνεται fallback στο ~/Face Detector/. Σε συστήματα εκτός Termux χρησιμοποιείται το ~/Downloads/Face Detector/, με εναλλακτική διαδρομή στο ~/Face Detector/. Τα εσωτερικά web αρχεία, τα certificates και τα helper binaries αποθηκεύονται στο ~/.face_detector_studio/.`


</details>

<details>
<summary>Face Detector Heavy.py</summary>




**Τι Βοηθά Να Λύσεις:** Χρήση βαρύτερης ροής face detection όταν χρειάζεσαι περισσότερες processing επιλογές και η συσκευή μπορεί να σηκώσει το επιπλέον φορτίο.

**Περιγραφή:** Πιο βαριά και επεκταμένη έκδοση ανάλυσης του face detector για Termux, χωρίς ανάγκη για root. Εκτός από live χρήση κάμερας, εναλλαγή μπροστινής/πίσω κάμερας, upload φωτογραφιών και βίντεο, PNG snapshots, WEBM recording και αποθήκευση face crops, ανεβάζει την παρακολούθηση έως και σε 30 πρόσωπα και προσθέτει TensorFlow COCO-SSD object detection πάνω στο pipeline του MediaPipe face mesh. Εμφανίζει πιο πλούσιο on-screen telemetry όπως face count, animal/object detection, εκτιμήσεις pose και gaze, facial proportions, κατάσταση στόματος και φρυδιών, asymmetry scoring και άλλα visual analysis στοιχεία, ενώ συνεχίζει να υποστηρίζει local network link και προαιρετικό δημόσιο Cloudflare link.

**Τοποθεσία Αποθήκευσης:** `Στο Termux, τα captures, τα recordings, τα uploaded results και τα αποθηκευμένα face crops μπαίνουν στο: ~/storage/downloads/Face Detector/. Αν το storage του Termux δεν είναι διαθέσιμο, γίνεται fallback στο ~/Face Detector/. Σε συστήματα εκτός Termux χρησιμοποιείται το ~/Downloads/Face Detector/, με εναλλακτική διαδρομή στο ~/Face Detector/. Τα εσωτερικά web αρχεία, τα certificates και τα helper binaries αποθηκεύονται στο ~/.face_detector_studio/.`


</details>

<details>
<summary>Face Swap.py</summary>




**Τι Βοηθά Να Λύσεις:** Δοκιμή face-swap μετασχηματισμού σε media που έχεις άδεια να χρησιμοποιήσεις.

**Περιγραφή:** Τοπικό browser-based εργαλείο face swap για Termux που λειτουργεί χωρίς root. Ανοίγει μια local camera σελίδα, σου επιτρέπει να ανεβάσεις μια source face εικόνα, να αλλάξεις ανάμεσα σε μπροστινή και πίσω κάμερα και να κάνεις blend το ανεβασμένο πρόσωπο πάνω στο live camera feed με MediaPipe Face Mesh. Η τρέχουσα έκδοση εστιάζει σε smooth face-lock λογική: κλειδώνει το ανεβασμένο πρόσωπο μία φορά, ακολουθεί το live πρόσωπο, κινεί βασικά feature patches για expressions, περιλαμβάνει smoothing, feathering, opacity, blend και skin-tone matching controls και μπορεί να αποθηκεύει PNG snapshots από τον browser. Χρησιμοποίησέ το μόνο με δικές σου εικόνες ή με ξεκάθαρη άδεια.

**Τοποθεσία Αποθήκευσης:** `Στο Termux, οι αποθηκευμένες φωτογραφίες μπαίνουν στο: /storage/emulated/0/Download/Face Swap/ ή στο ~/storage/downloads/Face Swap/, με εναλλακτική διαδρομή στο ~/Face Swap/. Σε συστήματα εκτός Termux χρησιμοποιείται το ~/Downloads/Face Swap/, με εναλλακτική διαδρομή στο ~/Face Swap/.`


</details>

<details>
<summary>Steganography.py</summary>




**Τι Βοηθά Να Λύσεις:** Εκμάθηση του πώς δεδομένα μπορούν να κρύβονται και να ανακτώνται από αρχεία για εξουσιοδοτημένη πρακτική ασφάλειας και forensics.

**Περιγραφή:** Σουίτα steganography με κωδικό για Termux. Μπορεί να δημιουργεί τυχαίες ασπρόμαυρες PNG εικόνες-φορείς, να κρυπτογραφεί μυστικό κείμενο με password-derived Fernet key, να κρύβει το κρυπτογραφημένο κείμενο μέσα σε PNG εικόνες με LSB steganography και να κάνει batch αποκωδικοποίηση κρυμμένων μηνυμάτων από όλες τις εικόνες που τοποθετούνται στον φάκελο Decrypt. Τα εξαγόμενα μηνύματα αποθηκεύονται αυτόματα ως ξεχωριστά αρχεία .txt και το script μπορεί προαιρετικά να καθαρίζει τις ήδη επεξεργασμένες εικόνες από τον φάκελο αποκωδικοποίησης μετά το scan.

**Τοποθεσία Αποθήκευσης:** `Κύριος φάκελος: /storage/emulated/0/Download/Steganography/ | Carrier/output εικόνες: /Encrypt | Εικόνες για έλεγχο κρυμμένων μηνυμάτων: /Decrypt | Εξαγόμενα αρχεία κειμένου: /Decrypted Texts.`


</details>

<details>
<summary>AR Terror.py</summary>




**Τι Βοηθά Να Λύσεις:** Πειραματισμός με local browser-based AR effects, camera interaction, recording και immersive storytelling από Termux.

**Περιγραφή:** Τοπική browser-based AR horror εμπειρία για Termux που λειτουργεί χωρίς root. Εκκινεί μια full-screen camera-driven ιστοσελίδα όπου εξερευνάς το περιβάλλον, συλλέγεις κρυμμένα logs μέσα σε archive/inventory σύστημα, χρησιμοποιείς ατμοσφαιρικά visual και audio effects, αλλάζεις ανάμεσα σε μπροστινή και πίσω κάμερα και γράφεις evidence σε WEBM όσο τρέχει η εμπειρία. Μπορεί επίσης να παρέχει τόσο local network link όσο και προαιρετικό δημόσιο Cloudflare link.

**Τοποθεσία Αποθήκευσης:** `Στο Termux, το καταγεγραμμένα evidence αποθηκεύεται στο: ~/storage/downloads/AR Terror/. Αν το storage του Termux δεν είναι διαθέσιμο, γίνεται fallback στο ~/AR Terror/. Σε συστήματα εκτός Termux χρησιμοποιείται το ~/Downloads/AR Terror/, με εναλλακτική διαδρομή στο ~/AR Terror/. Τα εσωτερικά web αρχεία, τα certificates και τα helper binaries αποθηκεύονται στο ~/.ar_terror_studio/.`


</details>

<details>
<summary>Login Stealer.py</summary>




**Τι Βοηθά Να Λύσεις:** Επίδειξη του κινδύνου credential capture σε ελεγχόμενο, ρητά εξουσιοδοτημένο awareness lab ώστε οι χρήστες να αναγνωρίζουν παραπλανητικά login flows.

**Περιγραφή:** Το Login Stealer.py είναι ένα fully working controlled login-security simulation tool για Termux που δείχνει πώς ψεύτικες login σελίδες, αντιγραμμένες authentication οθόνες, redirects, session behavior και verification-style παγίδες μπορούν να κάνουν έναν χρήστη να εμπιστευτεί λάθος σελίδα. Είναι φτιαγμένο για awareness training, lab demonstrations, screenshots και dummy-account testing ώστε οι αρχάριοι να καταλαβαίνουν πώς φαίνονται τα phishing-style login tricks πριν πέσουν σε κάτι πραγματικό. Πρέπει να χρησιμοποιείται μόνο με dummy δεδομένα, test accounts ή ξεκάθαρες permission-based παρουσιάσεις και δεν παρουσιάζεται ως εργαλείο για κλοπή πραγματικών λογαριασμών, private credentials, cookies, κάρτες, wallets ή προσωπικές πληροφορίες.

**Τοποθεσία Αποθήκευσης:** `Κύριος φάκελος: /storage/emulated/0/Download/Login Stealer/ | Χρήση μόνο με dummy δεδομένα, test accounts ή permission-based lab demonstrations.`


</details>

<details>
<summary>Widget Maker.py</summary>




**Τι Βοηθά Να Λύσεις:** Δημιουργία επαναχρησιμοποιήσιμων phone/Termux widgets ώστε συνηθισμένες εντολές ή actions να ξεκινούν ευκολότερα.

**Περιγραφή:** Το DedSec Widget Maker είναι no-root helper για Termux που δημιουργεί Android home-screen launchers για scripts του DedSec Project μέσω Termux:Widget. Σαρώνει αναδρομικά το Termux home, το shared storage και συνηθισμένους φακέλους του κινητού για DedSec, sponsor, exclusive και σχετικά Python scripts, μαζί με scripts μέσα σε κάθε προσβάσιμο φάκελο και υποφάκελο. Μετά δημιουργεί managed shortcuts στο ~/.shortcuts. Κάθε widget ανοίγει μικρό menu με Run, Show Script Path και Exit, ελέγχει το Python αρχείο πριν το τρέξει, κρατά manifest στο ~/.dedsec_widget_maker/ και μπορεί να κάνει update ή delete όλα τα managed widgets όταν αλλάζει η συλλογή των scripts σου.

**Τοποθεσία Αποθήκευσης:** `Τα managed widget launchers δημιουργούνται στο: ~/.shortcuts/ | Το state και το manifest αποθηκεύονται στο: ~/.dedsec_widget_maker/manifest.json. Τα αρχικά scripts δεν μετακινούνται· κάθε widget δείχνει πίσω στο detected source file.`


</details>

<details>
<summary>Kraken Trader.py</summary>




**Τι Βοηθά Να Λύσεις:** Έρευνα αγορών, paper-testing στρατηγικών, καταγραφή trades και οργάνωση risk calculations πριν εξεταστεί οποιαδήποτε live ενέργεια.

**Περιγραφή:** Το Kraken Trader.py είναι Termux trading research και portfolio assistant για το Kraken API. Ξεκινά σε paper mode από προεπιλογή, εμφανίζει risk disclaimer με countdown 10 δευτερολέπτων, αποθηκεύει τα πάντα στο ~/Kraken Trader/ και χρησιμοποιεί numbered menus για pair analysis, market scanning, dashboards, Sage-style strategy labs, advanced tools, beginner guides, risk/reward calculators, backtests, DCA και grid tools, paper wallet trading, paper bot loops, Kraken account tools, live order menus, order management, watchlists, crypto μαζί με stock/ETF monitoring, αναφορές, journals, logs, mode switching, diagnostics και settings. Είναι φτιαγμένο για εκπαίδευση, οργάνωση και πιο ασφαλές paper testing· δεν είναι financial advice και δεν εγγυάται κέρδος.

**Τοποθεσία Αποθήκευσης:** `Κύριος φάκελος: ~/Kraken Trader/ | Στο εσωτερικό του αποθηκεύονται οι ρυθμίσεις, το δοκιμαστικό πορτοφόλι, οι λίστες παρακολούθησης, οι προεπιλογές, οι ειδοποιήσεις, τα καλάθια, τα εργαλεία DCA και grid, τα αρχεία καταγραφής webhook, οι δοκιμές προώθησης, οι αναφορές, η προσωρινή μνήμη, τα ημερολόγια συναλλαγών και τα αρχεία σφαλμάτων. Προαιρετικά, αντίγραφα των αναφορών μπορούν να αποθηκεύονται και στις Λήψεις.`


</details>

<details>
<summary>Noob Hacker.py</summary>




**Τι Βοηθά Να Λύσεις:** Εκμάθηση εννοιών κυβερνοασφάλειας μέσα από πιο game-like progression με lessons, examples και practice.

**Περιγραφή:** Το Noob Hacker.py είναι ασφαλές offline terminal learning game για Termux που μαθαίνει σε απόλυτους αρχάριους προγραμματισμό, βασικά Python, συνήθειες Termux/Bash, debugging, local-only cybersecurity thinking, defender workflows, report writing, projects, quizzes και playable practice games. Είναι φτιαγμένο ως ένα μόνο Python script, λειτουργεί χωρίς root, κρατά την εξάσκηση σε φανταστικά/local labs, περιλαμβάνει English και Greek εκδόσεις, υποστηρίζει self-tests, save migration, progress tracking και πολλά beginner-friendly μαθήματα που οδηγούν κάποιον από μηδενική γνώση σε πρακτικές ασφαλείς δεξιότητες. Δεν επιτίθεται σε πραγματικούς στόχους, δεν σαρώνει το internet, δεν κλέβει λογαριασμούς και δεν μαθαίνει malware.

**Τοποθεσία Αποθήκευσης:** `Κύριος φάκελος: ~/Noob Hacker/ | Save file: ~/Noob Hacker/save.json | Mission log: ~/Noob Hacker/mission_log.txt | CTF labs: ~/Noob Hacker/CTF_Labs/ | Εξαγωγές: ~/Noob Hacker/Exports/.`


</details>


<a id="greek-butsystem"></a>

<h2>ButSystem.py (Αποκλειστικό)</h2>


Το ButSystem.py είναι ένας αυτοφιλοξενούμενος, local-first ιδιωτικός χώρος εργασίας για Termux που συνδυάζει ιδιωτική επικοινωνία, κρυπτογραφημένες εγγραφές, προηγμένο vault αρχείων, ειδήσεις και καιρό, καθώς και αυτόματα δημιουργημένους τοπικούς συνδέσμους, Cloudflared και Tor σε ένα ενιαίο περιβάλλον browser.

**Αποκλειστικό στο DedSec Project — περιλαμβάνεται δωρεάν:** Το ButSystem είναι ένα από τα πιο ξεχωριστά ολοκληρωμένα συστήματα του project και έχει δημιουργηθεί ειδικά για το οικοσύστημα του DedSec Project. Παρότι αποτελεί ένα από τα πιο αποκλειστικά εργαλεία του, η έκδοση που περιγράφεται εδώ διατίθεται δωρεάν μέσα από τα αρχεία και το repository, χωρίς ξεχωριστή αγορά από το Store.

### Βασικοί Τομείς Λειτουργιών ButSystem
- **Συνομιλίες, Ομάδες & Stories:** Ζωντανά προσωπικά μηνύματα, ομαδικές συνομιλίες, αποθηκευμένα μηνύματα, GIFs, φωνητικές σημειώσεις, κοινή χρήση αρχείων, χώρος συζήτησης, stories και λειτουργίες κλήσεων όπου το browser και η συσκευή το υποστηρίζουν.
- **Ασφάλεια, Πρόσβαση & Έλεγχος:** Έγκριση χρηστών, αιτήματα πρόσβασης συσκευών, σύνδεση από αποθηκευμένη συσκευή, προαιρετικό 2FA με ερωτήσεις ασφαλείας, κλειδώματα συνομιλιών με PIN, κατάσταση σύνδεσης, αναφορές, σελίδες διαχείρισης και ρυθμίσεις εμφάνισης ή λογαριασμού.
- **Προφίλ, Vault & Εργαλεία:** Επεξεργασία προφίλ, προηγμένο ιδιωτικό vault αρχείων, προαιρετικές ζωντανές τοποθεσίες, κρυπτογραφημένες εγγραφές Profiler με αναζήτηση, εισαγωγή, εξαγωγή και συνδυασμό, διαχείριση bounties από administrator και το ενσωματωμένο Face Detector.
- **Καιρός, Σύνδεσμοι & Κοινή Χρήση:** Αναζήτησε καιρό βάσει τοποθεσίας ή τρέχουσας θέσης, δες αναλυτική πρόγνωση έως 14 ημερών και χρησιμοποίησε συνδέσμους HTTPS, Cloudflared ή Tor με QR κωδικούς για λήψη. Τα αρχεία του vault μπορούν επίσης να κοινοποιούνται μέσω ελεγχόμενων συνδέσμων με προαιρετικό κωδικό, λήξη και ανάκληση.

### Όλες οι Περιοχές του ButSystem
- **Πλοήγηση & Ροή Μενού:** Το μενού πλοήγησης είναι ο βασικός κόμβος ελέγχου του ButSystem. Από εκεί μετακινείσαι ανάμεσα σε συνομιλίες, αποθηκευμένα μηνύματα, συζητήσεις, ομάδες, κλήσεις, stories, ζωντανές τοποθεσίες, αρχεία, ειδήσεις, καιρό, προφίλ, Profiler, αναφορές, ειδοποιήσεις, σελίδες διαχείρισης, ρυθμίσεις, βοήθεια και ενέργειες σύνδεσης ή αποσύνδεσης. Η επιλογή γλώσσας διατηρεί το περιβάλλον διαθέσιμο στα Αγγλικά και στα Ελληνικά.
- **Ταυτοποίηση & Πρόσβαση:** Το ButSystem ανοίγει μέσα από ροή αρχικής σελίδας, φόρτωσης, σύνδεσης και εγγραφής και μετά προσθέτει επιπλέον έλεγχο πρόσβασης όπου χρειάζεται. Αυτό περιλαμβάνει έγκριση χρήστη, αιτήματα πρόσβασης συσκευών, σύνδεση από αποθηκευμένη συσκευή, προαιρετικούς ελέγχους δύο παραγόντων με ερωτήσεις ασφαλείας και ενέργειες ανάκτησης ή επαναφοράς κωδικού ώστε η πρόσβαση να μένει δεμένη με εγκεκριμένους χρήστες και συσκευές.
- **Άμεσα Μηνύματα:** Η περιοχή προσωπικών μηνυμάτων είναι σχεδιασμένη για καθημερινές ιδιωτικές συνομιλίες. Μπορείς να στείλεις, να επεξεργαστείς ή να διαγράψεις μηνύματα, να αναζητήσεις περιεχόμενο, να επισυνάψεις πολυμέσα ή αρχεία, να χρησιμοποιήσεις GIF, να ηχογραφήσεις φωνητικές σημειώσεις και να ενεργοποιήσεις προστασίες όπως κλείδωμα με PIN και ένδειξη σύνδεσης.
- **Discussion Room:** Η περιοχή «Συζήτηση» λειτουργεί ως κοινή ροή και όχι ως προσωπική συνομιλία. Προσφέρει δημοσιεύσεις ανά κατηγορία, αναζήτηση, ανανέωση, φόρτωση επιπλέον περιεχομένου και άνοιγμα συγκεκριμένων καταχωρήσεων σε έναν ήρεμο κοινόχρηστο χώρο, ξεχωριστό από τα προσωπικά μηνύματα.
- **Ομάδες:** Η περιοχή «Ομάδες» επιτρέπει τη δημιουργία κοινόχρηστων χώρων με ρόλους και εργαλεία εποπτείας. Μπορείς να δημιουργήσεις ομάδα, να προσκαλέσεις ή να προσθέσεις μέλη, να ελέγξεις τη λίστα τους, να διαχειριστείς ενέργειες ιδιοκτήτη ή διαχειριστή, να αποχωρήσεις όταν χρειάζεται και να συνεχίσεις τη συζήτηση στην αντίστοιχη ομαδική συνομιλία με μηνύματα και συνημμένα.
- **Κλήσεις & Live Επικοινωνία:** Όπου το επιτρέπουν το πρόγραμμα περιήγησης και τα δικαιώματα της συσκευής, το ButSystem υποστηρίζει έναρξη, συμμετοχή, αποδοχή, απόρριψη, σίγαση και τερματισμό ζωντανής κλήσης. Η εμπειρία εξαρτάται από την άδεια μικροφώνου και το τρέχον περιβάλλον του προγράμματος περιήγησης.
- **Stories & Live Τοποθεσίες:** Το ButSystem καλύπτει και πιο ελαφριά εργαλεία ζωντανής κοινοποίησης. Τα Stories παρέχουν χειριστήρια δημιουργίας, προβολής και αντιδράσεων, ενώ το Live Locations προορίζεται για προαιρετική κοινοποίηση τοποθεσίας με έναρξη, διακοπή, ανανέωση και σαφή μηνύματα συναίνεσης ή προειδοποίησης πριν κοινοποιηθεί ενεργά η τοποθεσία.
- **Αρχεία, Vault & Αποθηκευμένα Media:** Η περιοχή Αρχεία και Vault λειτουργεί σαν ιδιωτικός server-style file manager. Υποστηρίζει φακέλους και πλοήγηση, κανονικά ή τμηματικά uploads με ακύρωση, αναζήτηση, κατηγορίες, φίλτρα τύπου αρχείου, ταξινόμηση, προεπισκοπήσεις, άνοιγμα και λήψη, μετονομασία, μετακίνηση, μαζικές ενέργειες, διαγραφή, σχόλια, ιστορικό δραστηριότητας, αναλυτικά στοιχεία μεγέθους, MIME και ημερομηνιών, προαιρετικό SHA-256 και ελεγχόμενους συνδέσμους κοινής χρήσης με προαιρετικό κωδικό, χρόνο λήξης και ανάκληση.
- **Προφίλ, Λογαριασμός & Εμφάνιση:** Η δική σου περιοχή προφίλ διαχειρίζεται την ταυτότητα και την παρουσίαση του λογαριασμού. Από εκεί οι χρήστες μπορούν να βλέπουν ή να επεξεργάζονται δεδομένα προφίλ, να αποθηκεύουν αλλαγές, να ανεβάζουν ή να αφαιρούν εικόνα προφίλ, να ρυθμίζουν ρυθμίσεις λογαριασμού, να ελέγχουν επιλογές εμφάνισης και να έχουν πρόσβαση σε ισχυρότερα ενέργειες λογαριασμού όπως διαγραφή λογαριασμού ή το επικίνδυνη ζώνη οριστικής διαγραφής όπου αυτό το ροή εργασίας είναι ενεργό.
- **Profiler, Διαχείριση Υποθέσεων & Face Detector:** Η πλευρά του Profiler είναι εκεί όπου το ButSystem γίνεται δομημένος χώρος πληροφοριών. Υποστηρίζει κρυπτογραφημένες εγγραφές Profiler, ροές προβολής και επεξεργασίας, τοπική αναζήτηση, εργαλεία εξαγωγής και συνδυασμού, διαχείριση bounties όπου αυτό το module είναι ενεργό και την ενσωματωμένη περιοχή Face Detector που χρησιμοποιείται για τοπικές διαδικασίες ανίχνευσης προσώπου και υποστήριξη σύγκρισης ομοιότητας μέσα στο ευρύτερο περιβάλλον του ButSystem.
- **Reports, Admin & Ρυθμίσεις Ασφάλειας:** Το επίπεδο ελέγχου του ButSystem χωρίζεται σε αναφορές, σελίδες διαχείρισης και ρυθμίσεις ασφάλειας. Εδώ οι χρήστες δημιουργούν ή ενημερώνουν αναφορές, εδώ οι διαχειριστές εγκρίνουν ή απορρίπτουν αιτήματα πρόσβασης και συσκευών, διαχειρίζονται άτομα και αρχεία χρηστών και εδώ οι κάτοχοι λογαριασμού ρυθμίζουν ρυθμίσεις ελέγχου δύο παραγόντων, κανόνες σύνδεσης συσκευών, διαδικασίες επαναφοράς κωδικού, επιλογές ιδιωτικότητας και άλλες δικλείδες που κρατούν το χώρος εργασίας οργανωμένο και ελεγχόμενο.
- **Νέα & Θεματική Ροή:** Η περιοχή Ειδήσεις δίνει στο χώρος εργασίας έναν ξεχωριστό χώρο για θεματικές ενημερώσεις χωρίς να ανακατεύονται με τα ιδιωτικές συνομιλίες. Οι χρήστες μπορούν να ανοίγουν το ροή ειδήσεων, να κινούνται ανάμεσα στα διαθέσιμα θέματα, να κάνουν ανανέωση στην τρέχουσα προβολή και να διαβάζουν ενημερώσεις από το ίδιο τοπικό περιβάλλον που χρησιμοποιείται για το υπόλοιπο ButSystem.
- **Καιρός & Προβλέψεις:** Μπορείς να αναζητήσεις πόλη, χωριό ή ταχυδρομικό κώδικα, να χρησιμοποιήσεις την τρέχουσα τοποθεσία της συσκευής, να ανανεώσεις τα αποτελέσματα και να δεις τρέχουσες συνθήκες μαζί με πρόγνωση έως 14 ημερών. Η σελίδα μπορεί να εμφανίσει πραγματική και αισθητή θερμοκρασία, υγρασία, άνεμο και ριπές, βροχόπτωση, νεφοκάλυψη, πίεση, πιθανότητα βροχής, UV, ανατολή και δύση. Οι συντεταγμένες χρησιμοποιούνται για το αίτημα και δεν αποθηκεύονται από το ButSystem.
- **Αυτόματοι Σύνδεσμοι HTTPS, Cloudflared & Tor:** Κατά την εκκίνηση, το ButSystem σερβίρει τοπικό HTTPS με αυτοδημιούργητο self-signed certificate, εμφανίζει συνδέσμους LAN και localhost και δοκιμάζει αυτόματα να δημιουργήσει Cloudflared quick tunnel και Tor hidden service. Η αρχική σελίδα εμφανίζει όσους συνδέσμους είναι διαθέσιμοι και δημιουργεί νέο QR κωδικό για λήψη για καθέναν από αυτούς.
- **Παρουσία, Παράδοση & Live Κατάσταση:** Το ButSystem κρατά τις ενεργές περιοχές άμεσο και ενημερωμένο με κατάσταση σύνδεσης μέσω περιοδικού ελέγχου, μετρητές μη αναγνωσμένα μηνύματα, κατάσταση παράδοσης και ανάγνωσης, περιοδικό έλεγχο για νέα προσωπικά ή ομαδικά μηνύματα και ζωντανές διαδικασίες ανανέωσης για συζητήσεις, locations, calls και άλλα δεδομένα που αλλάζουν. Έτσι το περιβάλλον παραμένει ενημερωμένο χωρίς να χρειάζεται ξεχωριστό εφαρμογή υπολογιστή.
- **Συνημμένα, Προεπισκοπήσεις & Μεγάλα Αρχεία:** Τα αρχεία διαχειρίζονται ανάλογα με το σημείο χρήσης τους. Τα προσωπικά μηνύματα, οι ομάδες, οι συζητήσεις και τα stories υποστηρίζουν τα αντίστοιχα συνημμένα αρχεία, εικόνες, φωνητικό ή άλλο πολυμεσικό υλικό, τα προφίλ υποστηρίζουν εικόνες προφίλ και το vault προσθέτει προεπισκοπήσεις, metadata, οργάνωση, κοινή χρήση και τμηματική μεταφορά για μεγαλύτερα uploads ώστε να μην εξαρτώνται από ένα μόνο εύθραυστο αίτημα.
- **Τοπική Προστασία Δεδομένων & Μόνιμη Αποθήκευση:** Τα αρχεία λογαριασμών, ρυθμίσεις, messages, κρυπτογραφημένα πεδία κειμένου, κλειδιά, αρχεία καταγραφής και δεδομένα χώρου εργασίας διατηρούνται στους δικούς του τοπικούς φακέλους του ButSystem. Το script προτιμά το κοινόχρηστο φάκελο Homework του κινητού όταν είναι διαθέσιμο ώστε σημαντικό κατάσταση της εφαρμογής να μπορεί να επιβιώσει από επανεγκατάσταση του Termux, ενώ το ευαίσθητο κείμενο και το Profiler content χρησιμοποιούν το ενσωματωμένο επίπεδο κρυπτογράφησης.
- **Αναζήτηση, Εξαγωγή & Διαχείριση Εγγραφών:** Αρκετές περιοχές είναι σχεδιασμένες για αναζήτηση, φιλτράρισμα και μετακίνηση πληροφοριών, όχι μόνο για προβολή. Οι χρήστες μπορούν να αναζητούν συνομιλίες, καταχωρήσεις συζητήσεων, αρχεία του vault, αναφορές και εγγραφές Profiler, να φιλτράρουν και να ταξινομούν το vault, να ανοίγουν αναλυτικές προβολές, να εισάγουν, να εξάγουν ή να συνδυάζουν εγγραφές Profiler και να κατεβάζουν συνημμένα όταν χρειάζονται τοπικό αντίγραφο.
- **Παύση Απορρήτου, Αρχεία Καταγραφής & Έλεγχοι Ανάκτησης:** Το σύστημα περιλαμβάνει λειτουργικές δικλείδες ασφαλείας για στιγμές όπου η πρόσβαση πρέπει να σταματήσει ή να ελεγχθεί. Τα ενέργειες παύσης και επαναφοράς απορρήτου μπορούν να προστατεύσουν προσωρινά το χώρος εργασίας, τα συμβάντα ασφαλείας γράφονται σε τοπικά αρχεία καταγραφής, οι διαχειριστές μπορούν να επιθεωρούν αρχεία καταγραφής και τα εργαλεία ανάκτησης καλύπτουν ξεχασμένους κωδικούς, εγκεκριμένες συσκευές, υποχρεωτική αποσύνδεση, διαγραφή λογαριασμού και διαδικασίες πλήρους επαναφοράς.

### Ξέχασες Τον Κωδικό; Ξεκίνα Το ButSystem Από Την Αρχή

Χρησιμοποίησέ το μόνο όταν η ανάκτηση είναι αδύνατη και αποδέχεσαι ότι θα χαθούν όλοι οι παλιοί λογαριασμοί, κωδικοί, ρυθμίσεις, μηνύματα, αρχεία θησαυροφυλακίου, κλειδιά και αρχεία καταγραφής του ButSystem. Σταμάτησε πρώτα το ButSystem, τρέξε την εντολή στο Termux και μετά άνοιξε ξανά το ButSystem.py ώστε να δημιουργήσει ένα εντελώς νέο χώρο εργασίας.

**Προειδοποίηση:** αυτή η εντολή διαγράφει μόνιμα τους φακέλους αποθηκευμένων δεδομένων του ButSystem. Δεν διαγράφει το ίδιο το script ButSystem.py.

**Τοποθεσία Αποθήκευσης:** `Κύρια persistent data: /storage/emulated/0/Homework/ButSystem/ (διαθέσιμα επίσης ως ~/storage/shared/Homework/ButSystem/) | Fallback: ~/Homework/ButSystem/ | Legacy data που μεταφέρονται από: ~/ButSystem/ | Face Detector captures: Downloads/ButSystem/Face Detector/ | Tor runtime data: ~/.ButSystem_tor/`

Να χρησιμοποιείται μόνο σε συστήματα που σου ανήκουν ή για τα οποία έχεις ρητή άδεια.

</details>

<a id="greek-contact"></a>

<details>
<summary><strong>Επικοινωνία και Συντελεστές</strong></summary>


### Επικοινωνία

Επικοινωνήστε με την ομάδα μας και γνωρίστε τα ταλαντούχα άτομα πίσω από το DedSec Project.

* **Κύριο Website:** [https://ded-sec.space](https://ded-sec.space)
* **Κύριο Repository του DedSec Project:** [https://github.com/dedsec1121fk/DedSec](https://github.com/dedsec1121fk/DedSec)
* **Εφεδρικό Website:** [https://ded-sec.online](https://ded-sec.online)
* **Εφεδρικό Repository του DedSec Project:** [https://github.com/sal-scar/DedSec](https://github.com/sal-scar/DedSec)
* **WhatsApp:** [+37257263676](https://wa.me/37257263676)
* **Προφίλ Telegram:** [@dedsecproject](https://t.me/dedsecproject)
* **Discord Server:** [https://discord.gg/fcAuYS4JEv](https://discord.gg/fcAuYS4JEv)
* **Κανάλι Telegram:** [https://t.me/dedsec_project_channel](https://t.me/dedsec_project_channel)
* **Προφίλ X:** [https://x.com/DedSecProject](https://x.com/DedSecProject)

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
