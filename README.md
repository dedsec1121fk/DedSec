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

* [How To Install And Setup The DedSec Project](#-how-to-install-and-setup-the-dedsec-project)
* [Settings & Configuration](#️-settings--configuration)
* [Explore The Toolkit](#️-explore-the-toolkit)
* [Contact Us & Credits](#-contact-us--credits)
* [Disclaimer & Terms of Use](#️-disclaimer--terms-of-use)

---

## 🚀 How To Install And Setup The DedSec Project

Get the DedSec Project command-line tools running on your **Android device with Termux**.

### Requirements

| Component | Minimum Specification |
| :-------- | :------------------------------------------------------------------- |
| **Device** | Android with Termux installed |
| **Storage** | Min **8GB** free. (Images and recordings also consume space.) |
| **RAM** | Min **2GB** |

<details>
<summary><strong>🇬🇧 English</strong></summary>

### Step-by-Step Setup

> To install APKs such as F-Droid, enable unknown sources in **Settings > Security > Install Unknown Apps** if your phone requires it.

1. **Install F-Droid and Termux**
   - Download and install **F-Droid**.
   - Open F-Droid and install **Termux**.
   - Recommended add-ons: **Termux:API** and **Termux:Styling**.

2. **Update packages and grant storage access**

```bash
pkg update -y && pkg upgrade -y && pkg install git nano -y && termux-setup-storage
```

3. **Clone the DedSec repository**

```bash
git clone https://github.com/dedsec1121fk/DedSec
```

4. **Open the folder and run setup**

```bash
cd DedSec && bash Setup.sh
```

5. **Choose your interface language and menu style**
   - In the settings menu, choose **Change Menu Style**.
   - Select the style you want: **list**, **grid**, or **number**.
   - Close Termux from notifications and reopen it after setup finishes.

6. **Quick launch after installation**
   - Type `e` to open the **English** menu.
   - Type `g` to open the **Greek** menu.

### Important Notes

- Keep the screen awake during long installs if needed.
- The project settings can later change language, style, backups, updates, and more.
- If the installation script downloads packages on first setup, let it finish fully before closing Termux.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

### Βήματα Εγκατάστασης

> Για να εγκαταστήσεις APK όπως το F-Droid, ενεργοποίησε την εγκατάσταση από άγνωστες πηγές από **Ρυθμίσεις > Ασφάλεια > Install Unknown Apps**, αν το απαιτεί η συσκευή σου.

1. **Εγκατάσταση F-Droid και Termux**
   - Κατέβασε και εγκατέστησε το **F-Droid**.
   - Άνοιξε το F-Droid και εγκατέστησε το **Termux**.
   - Προτεινόμενα add-ons: **Termux:API** και **Termux:Styling**.

2. **Ενημέρωσε τα packages και δώσε πρόσβαση στο storage**

```bash
pkg update -y && pkg upgrade -y && pkg install git nano -y && termux-setup-storage
```

3. **Κάνε clone το repository του DedSec**

```bash
git clone https://github.com/dedsec1121fk/DedSec
```

4. **Μπες στον φάκελο και τρέξε το setup**

```bash
cd DedSec && bash Setup.sh
```

5. **Διάλεξε γλώσσα περιβάλλοντος και στυλ μενού**
   - Στο settings menu διάλεξε **Change Menu Style**.
   - Επίλεξε το στυλ που θέλεις: **list**, **grid** ή **number**.
   - Κλείσε το Termux από τις ειδοποιήσεις και άνοιξέ το ξανά αφού τελειώσει η εγκατάσταση.

6. **Γρήγορη εκκίνηση μετά την εγκατάσταση**
   - Πληκτρολόγησε `e` για να ανοίξεις το **English** menu.
   - Πληκτρολόγησε `g` για να ανοίξεις το **Greek** menu.

### Σημαντικές Σημειώσεις

- Κράτα την οθόνη ανοιχτή κατά τη διάρκεια μεγάλων εγκαταστάσεων αν χρειάζεται.
- Από το settings tool μπορείς αργότερα να αλλάξεις γλώσσα, στυλ, backups, updates και άλλα.
- Αν το installation script κατεβάζει packages στην πρώτη εκτέλεση, άφησέ το να ολοκληρωθεί πλήρως πριν κλείσεις το Termux.

</details>

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
- **Sponsors-Only:** 2 tools

**Total listed on tools page:** 76 tools


## 🧑‍💻 Developer Base

### • File Converter

<details>
<summary><strong>🇬🇧 English</strong></summary>

A powerful file converter supporting 40+ formats.

**Save Location:** ~/storage/downloads/File Converter/

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Ένας ισχυρός μετατροπέας αρχείων που υποστηρίζει 40+ μορφές.

**Τοποθεσία Αποθήκευσης:** ~/storage/downloads/File Converter/

</details>

### • File Type Checker

<details>
<summary><strong>🇬🇧 English</strong></summary>

Advanced file analysis and security scanner that detects file types, extracts metadata, calculates cryptographic hashes, and identifies potential threats.

**Save Location:** ~/Downloads/File Type Checker/ | Quarantined files use the `.dangerous` extension.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Προηγμένο εργαλείο ανάλυσης αρχείων και ελέγχου ασφαλείας που εντοπίζει τύπους αρχείων, εξάγει μεταδεδομένα, υπολογίζει κρυπτογραφικά hashes και αναγνωρίζει πιθανούς κινδύνους.

**Τοποθεσία Αποθήκευσης:** ~/Downloads/File Type Checker/ | Τα αρχεία καραντίνας χρησιμοποιούν την κατάληξη `.dangerous`.

</details>

### • Mobile Desktop

<details>
<summary><strong>🇬🇧 English</strong></summary>

Termux Linux desktop manager without root. It sets up a proot-distro desktop environment with VNC/X11 options and includes a built-in program manager for installing, updating, and removing desktop components.

**Save Location:** Scan folders created in the current directory as `scan_[target]_[date]`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Διαχειριστής Linux desktop για Termux χωρίς root. Δημιουργεί περιβάλλον proot-distro με επιλογές VNC/X11 και περιλαμβάνει ενσωματωμένο διαχειριστή προγραμμάτων για εγκατάσταση, ενημέρωση και αφαίρεση στοιχείων του desktop.

**Τοποθεσία Αποθήκευσης:** Φάκελοι σάρωσης που δημιουργούνται στον τρέχοντα κατάλογο ως `scan_[target]_[date]`.

</details>

### • Mobile Developer Setup

<details>
<summary><strong>🇬🇧 English</strong></summary>

Automates a mobile web-development environment in Termux by installing common development tools, configuring paths, and providing quick-start project scaffolding.

**Save Location:** Scan folders created in the current directory as `scan_[target]_[date]`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Αυτοματοποιεί ένα mobile web-development περιβάλλον στο Termux εγκαθιστώντας συνηθισμένα εργαλεία ανάπτυξης, ρυθμίζοντας paths και παρέχοντας γρήγορο project scaffolding.

**Τοποθεσία Αποθήκευσης:** Φάκελοι σάρωσης που δημιουργούνται στον τρέχοντα κατάλογο ως `scan_[target]_[date]`.

</details>

### • Simple Websites Creator

<details>
<summary><strong>🇬🇧 English</strong></summary>

A comprehensive website builder that creates responsive HTML websites with customizable layouts, colors, fonts, and SEO settings.

**Save Location:** ~/storage/downloads/Websites/

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Ένα ολοκληρωμένο εργαλείο δημιουργίας ιστοσελίδων που φτιάχνει responsive HTML websites με παραμετροποιήσιμα layouts, χρώματα, γραμματοσειρές και ρυθμίσεις SEO.

**Τοποθεσία Αποθήκευσης:** ~/storage/downloads/Websites/

</details>

### • Smart Notes

<details>
<summary><strong>🇬🇧 English</strong></summary>

Terminal note-taking app with reminders.

**Save Location:** ~/.smart_notes.json

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εφαρμογή σημειώσεων για terminal με υπενθυμίσεις.

**Τοποθεσία Αποθήκευσης:** ~/.smart_notes.json

</details>

### • Dead Switch

<details>
<summary><strong>🇬🇧 English</strong></summary>

Syncs your `~/storage/downloads/Dead Switch/` folder to a GitHub repository with safety controls, visibility toggle options, and optional Termux:API notification buttons.

**Save Location:** ~/storage/downloads/Dead Switch/

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Συγχρονίζει τον φάκελο `~/storage/downloads/Dead Switch/` σε GitHub repository με επιλογές ασφαλείας, αλλαγή ορατότητας και προαιρετικά κουμπιά ειδοποιήσεων μέσω Termux:API.

**Τοποθεσία Αποθήκευσης:** ~/storage/downloads/Dead Switch/

</details>

### • Tree Explorer

<details>
<summary><strong>🇬🇧 English</strong></summary>

File-system explorer for Termux that lets you browse folders, search files, find duplicates by hash, and clean empty directories with safe prompts.

**Save Location:** Scan folders created in the current directory as `scan_[target]_[date]`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εξερευνητής συστήματος αρχείων για Termux που σου επιτρέπει να περιηγείσαι σε φακέλους, να αναζητάς αρχεία, να βρίσκεις διπλότυπα με hash και να καθαρίζεις άδειους φακέλους με ασφαλείς προτροπές.

**Τοποθεσία Αποθήκευσης:** Φάκελοι σάρωσης που δημιουργούνται στον τρέχοντα κατάλογο ως `scan_[target]_[date]`.

</details>

### • Devices Finder

<details>
<summary><strong>🇬🇧 English</strong></summary>

Local-network device discovery tool for Termux without root. It separates live-host discovery from service scanning, classifies devices using multiple hints, supports interactive scan profiles, and exports JSON, TXT, CSV, and HTML reports.

**Save Location:** ~/storage/downloads/Devices Finder/ as `devices_scan_[timestamp].json/.txt/.csv/.html` (fallback to `~/downloads/Devices Finder/` or the current directory).

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εργαλείο εντοπισμού συσκευών τοπικού δικτύου για Termux χωρίς root. Ξεχωρίζει την ανακάλυψη ενεργών hosts από το service scanning, ταξινομεί συσκευές με πολλαπλά hints, υποστηρίζει interactive scan profiles και εξάγει αναφορές JSON, TXT, CSV και HTML.

**Τοποθεσία Αποθήκευσης:** ~/storage/downloads/Devices Finder/ ως `devices_scan_[timestamp].json/.txt/.csv/.html` (fallback σε `~/downloads/Devices Finder/` ή στον τρέχοντα κατάλογο).

</details>


## 🔧 Network Tools

### • Bug Hunter

<details>
<summary><strong>🇬🇧 English</strong></summary>

Authorized web security recon and misconfiguration scanner for defensive use. It performs DNS checks, TLS and certificate checks, security-header and cookie audits, tech fingerprinting, crawling, and JavaScript endpoint analysis, and it can export JSON, CSV, HTML, and PDF reports.

**Save Location:** Output folder (default: `bughunter_out/`) with `report.json`, `report.csv`, `report.html`, and optionally `report.pdf`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εγκεκριμένο εργαλείο αναγνώρισης web security και ελέγχου κακών ρυθμίσεων για αμυντική χρήση. Εκτελεί DNS ελέγχους, TLS και certificate checks, ελέγχους security headers και cookies, tech fingerprinting, crawling και ανάλυση JavaScript endpoints, και μπορεί να εξάγει αναφορές JSON, CSV, HTML και PDF.

**Τοποθεσία Αποθήκευσης:** Φάκελος εξόδου (προεπιλογή: `bughunter_out/`) με `report.json`, `report.csv`, `report.html` και προαιρετικά `report.pdf`.

</details>

### • Dark

<details>
<summary><strong>🇬🇧 English</strong></summary>

A specialized Dark Web OSINT tool and crawler designed for Tor network analysis.

**Save Location:** /sdcard/Download/DarkNet (or `~/DarkNet` if storage is inaccessible).

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εξειδικευμένο εργαλείο και crawler Dark Web OSINT σχεδιασμένο για ανάλυση του δικτύου Tor.

**Τοποθεσία Αποθήκευσης:** /sdcard/Download/DarkNet (ή `~/DarkNet` αν ο αποθηκευτικός χώρος δεν είναι προσβάσιμος).

</details>

### • DedSec's Network

<details>
<summary><strong>🇬🇧 English</strong></summary>

An advanced non-root network toolkit optimized for speed and stability.

**Save Location:** ~/DedSec's Network

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Προηγμένο network toolkit χωρίς root, βελτιστοποιημένο για ταχύτητα και σταθερότητα.

**Τοποθεσία Αποθήκευσης:** ~/DedSec's Network

</details>

### • Digital Footprint Finder

<details>
<summary><strong>🇬🇧 English</strong></summary>

Conservative OSINT username scanner with pack-based coverage, multi-signal verification to reduce false positives, FOUND versus POSSIBLE results, optional search-engine dorking, and TXT/JSON/CSV/HTML export support.

**Save Location:** `~/storage/downloads/Digital Footprint Finder/[username]_[YYYYMMDD_HHMMSS].txt` plus optional `.json`, `.csv`, and `.html` (falls back to `/sdcard/Download`).

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Συντηρητικός OSINT scanner για usernames με κάλυψη μέσω packs, επαλήθευση με πολλαπλά σήματα για λιγότερα false positives, αποτελέσματα FOUND έναντι POSSIBLE, προαιρετικό search-engine dorking και υποστήριξη εξαγωγής TXT/JSON/CSV/HTML.

**Τοποθεσία Αποθήκευσης:** `~/storage/downloads/Digital Footprint Finder/[username]_[YYYYMMDD_HHMMSS].txt` μαζί με προαιρετικά `.json`, `.csv` και `.html` (fallback στο `/sdcard/Download`).

</details>

### • Connections.py

<details>
<summary><strong>🇬🇧 English</strong></summary>

Secure chat and file-sharing server with real-time messaging, large-file sharing, and WebRTC video-call support. It combines chat and database-style file features under one local-first workflow.

**Save Location:** Downloads to `~/Downloads/DedSec's Database`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Ασφαλής server για chat και διαμοιρασμό αρχείων με real-time messaging, μεταφορά μεγάλων αρχείων και υποστήριξη WebRTC video calls. Συνδυάζει δυνατότητες chat και διαχείρισης αρχείων σε ένα local-first workflow.

**Τοποθεσία Αποθήκευσης:** Οι λήψεις αποθηκεύονται στο `~/Downloads/DedSec's Database`.

</details>

### • Link Shield

<details>
<summary><strong>🇬🇧 English</strong></summary>

Security-focused URL inspector that follows redirects, checks HTTPS and SSL, flags suspicious domains or patterns, and generates a risk report before you open a link.

**Save Location:** Scan folders created in the current directory as `scan_[target]_[date]`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εργαλείο ελέγχου URL με έμφαση στην ασφάλεια που ακολουθεί redirects, ελέγχει HTTPS και SSL, επισημαίνει ύποπτα domains ή patterns και δημιουργεί risk report πριν ανοίξεις έναν σύνδεσμο.

**Τοποθεσία Αποθήκευσης:** Φάκελοι σάρωσης που δημιουργούνται στον τρέχοντα κατάλογο ως `scan_[target]_[date]`.

</details>

### • Masker

<details>
<summary><strong>🇬🇧 English</strong></summary>

URL masking utility.

**Save Location:** N/A — output is shown directly on screen.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εργαλείο απόκρυψης/μάσκαρεματος URL.

**Τοποθεσία Αποθήκευσης:** Δεν υπάρχει αποθήκευση — το αποτέλεσμα εμφανίζεται απευθείας στην οθόνη.

</details>

### • QR Code Generator

<details>
<summary><strong>🇬🇧 English</strong></summary>

Python-based QR code generator that creates QR codes for URLs and saves them in a Downloads folder.

**Save Location:** ~/storage/downloads/QR Codes/

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

QR code generator βασισμένο σε Python που δημιουργεί QR codes για URLs και τα αποθηκεύει σε φάκελο των Downloads.

**Τοποθεσία Αποθήκευσης:** ~/storage/downloads/QR Codes/

</details>

### • Sod

<details>
<summary><strong>🇬🇧 English</strong></summary>

Comprehensive load-testing tool for web applications with multiple testing methods such as HTTP, WebSocket, database simulation, file upload, and mixed workloads.

**Save Location:** `load_test_config.json` in the script directory | results shown in the terminal.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Ολοκληρωμένο εργαλείο load testing για web applications με πολλαπλές μεθόδους δοκιμής όπως HTTP, WebSocket, προσομοίωση βάσης δεδομένων, file upload και mixed workloads.

**Τοποθεσία Αποθήκευσης:** `load_test_config.json` στον φάκελο του script | τα αποτελέσματα εμφανίζονται στο terminal.

</details>

### • Store Scrapper

<details>
<summary><strong>🇬🇧 English</strong></summary>

Single-file Python store scraper for Termux without root. It discovers categories and products across many store types, saves while running, downloads images, and organizes output by store, category, and product.

**Save Location:** `~/storage/downloads/Store Scrapper/<Store>/<Category>/<Product>/` with files such as `metadata.json`, `summary.txt`, `description.txt`, `images/`, `images.json`, category state files, and `FINAL_REPORT.txt`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Single-file store scraper σε Python για Termux χωρίς root. Ανακαλύπτει κατηγορίες και προϊόντα σε πολλούς τύπους καταστημάτων, αποθηκεύει κατά τη διάρκεια της λειτουργίας, κατεβάζει εικόνες και οργανώνει το αποτέλεσμα ανά store, category και product.

**Τοποθεσία Αποθήκευσης:** `~/storage/downloads/Store Scrapper/<Store>/<Category>/<Product>/` με αρχεία όπως `metadata.json`, `summary.txt`, `description.txt`, `images/`, `images.json`, state files κατηγοριών και `FINAL_REPORT.txt`.

</details>


## 🎮 Games

### • Buzz

<details>
<summary><strong>🇬🇧 English</strong></summary>

Text-only trivia party game for Termux with a fixed built-in database of 15,000 questions.

**Save Location:** ~/Buzz/ (`data/` for database, profiles, settings, and highscores).

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Text-only trivia party game για Termux με ενσωματωμένη σταθερή βάση 15.000 ερωτήσεων.

**Τοποθεσία Αποθήκευσης:** ~/Buzz/ (`data/` για database, profiles, settings και highscores).

</details>

### • CTF God

<details>
<summary><strong>🇬🇧 English</strong></summary>

Full-screen Curses CTF game for Termux with story mode, missions, daily challenges, random boss levels, a hint-shop economy, achievements, ranks, and challenge packs.

**Save Location:** `/storage/emulated/0/Download/CTF God/files` (fallback to `~/storage/downloads/CTF God/...`) | game state and packs in `~/.ctf_god/`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Full-screen Curses CTF game για Termux με story mode, missions, daily challenges, random boss levels, σύστημα hint shop, achievements, ranks και challenge packs.

**Τοποθεσία Αποθήκευσης:** `/storage/emulated/0/Download/CTF God/files` (fallback σε `~/storage/downloads/CTF God/...`) | το game state και τα packs αποθηκεύονται στο `~/.ctf_god/`.

</details>

### • Detective

<details>
<summary><strong>🇬🇧 English</strong></summary>

Story-driven terminal detective game for Termux with a large fixed case library, lore dossiers, rumors, side stories, suspect rosters, evidence-board and timeline views, 4 difficulties, autosave, manual saves, and helper commands such as `:help`, `:lore`, `:timeline`, and `:save`.

**Save Location:** `~/Detective/` for player config, autosave/manual saves, and case progress.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Story-driven detective game για terminal στο Termux με μεγάλη σταθερή βιβλιοθήκη υποθέσεων, lore dossiers, φήμες, side stories, suspect rosters, views για evidence board και timeline, 4 δυσκολίες, autosave, manual saves και βοηθητικές εντολές όπως `:help`, `:lore`, `:timeline` και `:save`.

**Τοποθεσία Αποθήκευσης:** `~/Detective/` για player config, autosave/manual saves και πρόοδο υποθέσεων.

</details>

### • Tamagotchi

<details>
<summary><strong>🇬🇧 English</strong></summary>

A fully featured terminal pet game.

**Save Location:** ~/.termux_tamagotchi_v8.json

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Πλήρως εξοπλισμένο terminal pet game.

**Τοποθεσία Αποθήκευσης:** ~/.termux_tamagotchi_v8.json

</details>

### • Terminal Arcade

<details>
<summary><strong>🇬🇧 English</strong></summary>

All-in-one terminal arcade pack with multiple mini-games in a single script.

**Save Location:** Scan folders created in the current directory as `scan_[target]_[date]`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

All-in-one terminal arcade pack με πολλά mini-games μέσα σε ένα μόνο script.

**Τοποθεσία Αποθήκευσης:** Φάκελοι σάρωσης που δημιουργούνται στον τρέχοντα κατάλογο ως `scan_[target]_[date]`.

</details>


## 🛠️ Other Tools

### • Android App Launcher

<details>
<summary><strong>🇬🇧 English</strong></summary>

Utility to manage Android apps directly from the terminal.

**Save Location:** Extracted APKs: `~/storage/shared/Download/Extracted APK's` | reports: `~/storage/shared/Download/App_Security_Reports`

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εργαλείο για διαχείριση εφαρμογών Android απευθείας από το terminal.

**Τοποθεσία Αποθήκευσης:** Extracted APKs: `~/storage/shared/Download/Extracted APK's` | reports: `~/storage/shared/Download/App_Security_Reports`

</details>

### • Loading Screen

<details>
<summary><strong>🇬🇧 English</strong></summary>

Customize your Termux startup with ASCII art loading screens.

**Save Location:** Modifies `.bash_profile` and `bash.bashrc`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Προσαρμογή του startup του Termux με loading screens από ASCII art.

**Τοποθεσία Αποθήκευσης:** Τροποποιεί τα `.bash_profile` και `bash.bashrc`.

</details>

### • Password Master

<details>
<summary><strong>🇬🇧 English</strong></summary>

Comprehensive password-management suite featuring encrypted vault storage, password generation, strength analysis, and improvement tools.

**Save Location:** `my_vault.enc` in the script directory | backups in `~/Downloads/Password Master Backup/`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Ολοκληρωμένη σουίτα διαχείρισης κωδικών με κρυπτογραφημένο vault, δημιουργία κωδικών, ανάλυση ισχύος και εργαλεία βελτίωσης.

**Τοποθεσία Αποθήκευσης:** `my_vault.enc` στον φάκελο του script | backups στο `~/Downloads/Password Master Backup/`.

</details>

### • Termux Backup Restore

<details>
<summary><strong>🇬🇧 English</strong></summary>

Backup and restore tool for Termux that creates a zipped backup of your Termux files to Downloads and can restore them with integrity checks.

**Save Location:** Scan folders created in the current directory as `scan_[target]_[date]`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εργαλείο backup και restore για Termux που δημιουργεί zipped backup των αρχείων Termux στα Downloads και μπορεί να τα επαναφέρει με integrity checks.

**Τοποθεσία Αποθήκευσης:** Φάκελοι σάρωσης που δημιουργούνται στον τρέχοντα κατάλογο ως `scan_[target]_[date]`.

</details>

### • Termux Repair Wizard

<details>
<summary><strong>🇬🇧 English</strong></summary>

Troubleshooting wizard for Termux that checks common issues such as mirrors, packages, and permissions, suggests fixes, and runs safe repair commands step by step.

**Save Location:** Scan folders created in the current directory as `scan_[target]_[date]`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Wizard αντιμετώπισης προβλημάτων για Termux που ελέγχει συνηθισμένα ζητήματα όπως mirrors, packages και permissions, προτείνει λύσεις και εκτελεί ασφαλείς εντολές επιδιόρθωσης βήμα βήμα.

**Τοποθεσία Αποθήκευσης:** Φάκελοι σάρωσης που δημιουργούνται στον τρέχοντα κατάλογο ως `scan_[target]_[date]`.

</details>

### • FaveSites.py

<details>
<summary><strong>🇬🇧 English</strong></summary>

Lightweight Termux bookmark manager that saves and organizes your favorite websites for quick access.

**Save Location:** `~/FaveSites/` in your Termux home folder.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Ελαφρύς bookmark manager για Termux που αποθηκεύει και οργανώνει τις αγαπημένες σου ιστοσελίδες για γρήγορη πρόσβαση.

**Τοποθεσία Αποθήκευσης:** `~/FaveSites/` στον home φάκελο του Termux.

</details>


## 📁 No Category

### • Extra Content

<details>
<summary><strong>🇬🇧 English</strong></summary>

Extra bonus-content hub with quick access to additional resources, templates, and optional add-ons included in the DedSec toolkit.

**Save Location:** Scan folders created in the current directory as `scan_[target]_[date]`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Κόμβος extra bonus content με γρήγορη πρόσβαση σε επιπλέον resources, templates και προαιρετικά add-ons του DedSec toolkit.

**Τοποθεσία Αποθήκευσης:** Φάκελοι σάρωσης που δημιουργούνται στον τρέχοντα κατάλογο ως `scan_[target]_[date]`.

</details>

### • Settings

<details>
<summary><strong>🇬🇧 English</strong></summary>

Central control hub for the DedSec ecosystem, including language configuration, updates, backups, and general project controls.

**Save Location:** Language config: `~/Language.json` | backups: `~/Termux.zip`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Κεντρικός κόμβος ελέγχου για το οικοσύστημα DedSec, που περιλαμβάνει ρυθμίσεις γλώσσας, ενημερώσεις, backups και γενικούς ελέγχους του project.

**Τοποθεσία Αποθήκευσης:** Language config: `~/Language.json` | backups: `~/Termux.zip`.

</details>


## 💜 Sponsors-Only

To access the scripts in this category, you need an active monthly GitHub subscription of **$10 or $15**.

### • Face Detector.py

<details>
<summary><strong>🇬🇧 English</strong></summary>

Local browser-based face-mesh detection tool for Termux without root. It uses the live camera feed, tracks up to 3 faces with MediaPipe Face Mesh, draws detailed landmark overlays and on-screen analysis instead of simple square boxes, supports PNG photo capture and WEBM video recording, lets you switch between front and back camera, and can provide both a local network link and an optional Cloudflare public link.

**Save Location:** On Termux: `~/storage/downloads/Face Detector/` | fallback: `~/Face Detector/` | non-Termux: `~/Downloads/Face Detector/` with fallback to `~/Face Detector/` | internal web files and helper data in `~/.face_detector_studio/`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Τοπικό browser-based εργαλείο ανίχνευσης face mesh για Termux χωρίς root. Χρησιμοποιεί live camera feed, παρακολουθεί έως και 3 πρόσωπα με MediaPipe Face Mesh, σχεδιάζει αναλυτικά landmark overlays και on-screen ανάλυση αντί για απλά τετράγωνα πλαίσια, υποστηρίζει PNG λήψεις φωτογραφιών και WEBM εγγραφή βίντεο, επιτρέπει εναλλαγή μπροστινής και πίσω κάμερας και μπορεί να δώσει local network link καθώς και προαιρετικό δημόσιο Cloudflare link.

**Τοποθεσία Αποθήκευσης:** Στο Termux: `~/storage/downloads/Face Detector/` | fallback: `~/Face Detector/` | εκτός Termux: `~/Downloads/Face Detector/` με fallback στο `~/Face Detector/` | εσωτερικά web files και helper data στο `~/.face_detector_studio/`.

</details>

### • Steganography.py

<details>
<summary><strong>🇬🇧 English</strong></summary>

Password-based steganography suite for Termux. It can generate random black-and-white PNG cover images, encrypt secret text with a password-derived Fernet key, hide the encrypted text inside PNG images using LSB steganography, and batch-decode hidden messages from images placed in the Decrypt folder.

**Save Location:** Main folder: `/storage/emulated/0/Download/Steganography/` | encrypt images: `/Encrypt` | images to decode: `/Decrypt` | recovered text files: `/Decrypted Texts`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Σουίτα steganography με κωδικό για Termux. Μπορεί να δημιουργεί τυχαίες ασπρόμαυρες PNG εικόνες-φορείς, να κρυπτογραφεί μυστικό κείμενο με Fernet key που παράγεται από κωδικό, να κρύβει το κρυπτογραφημένο κείμενο μέσα σε PNG εικόνες με LSB steganography και να κάνει batch αποκωδικοποίηση κρυμμένων μηνυμάτων από εικόνες που μπαίνουν στον φάκελο Decrypt.

**Τοποθεσία Αποθήκευσης:** Κύριος φάκελος: `/storage/emulated/0/Download/Steganography/` | εικόνες για κρυπτογράφηση: `/Encrypt` | εικόνες για αποκωδικοποίηση: `/Decrypt` | ανακτημένα αρχεία κειμένου: `/Decrypted Texts`.

</details>


## 📱 Personal Information Capture (Educational Use Only)

These scripts are **training simulations** intended to help you understand how personal-data collection attacks are presented, so you can learn to recognize and defend against them.


### • Fake Back Camera Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational training simulation that demonstrates how pages may be styled to request back camera access, helping users recognize social-engineering patterns and suspicious permission or data requests.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική προσομοίωση που δείχνει πώς μπορούν να σχεδιαστούν σελίδες για να ζητούν πρόσβαση στην πίσω κάμερα, βοηθώντας τον χρήστη να αναγνωρίζει μοτίβα social engineering και ύποπτα αιτήματα για δικαιώματα ή δεδομένα.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Back Camera Video Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational training simulation that demonstrates how pages may be styled to request camera video access, helping users recognize social-engineering patterns and suspicious permission or data requests.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική προσομοίωση που δείχνει πώς μπορούν να σχεδιαστούν σελίδες για να ζητούν πρόσβαση σε βίντεο κάμερας, βοηθώντας τον χρήστη να αναγνωρίζει μοτίβα social engineering και ύποπτα αιτήματα για δικαιώματα ή δεδομένα.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Card Details Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational training simulation that demonstrates how pages may be styled to request payment-card data entry prompts, helping users recognize social-engineering patterns and suspicious permission or data requests.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική προσομοίωση που δείχνει πώς μπορούν να σχεδιαστούν σελίδες για να ζητούν προτροπές εισαγωγής στοιχείων κάρτας πληρωμής, βοηθώντας τον χρήστη να αναγνωρίζει μοτίβα social engineering και ύποπτα αιτήματα για δικαιώματα ή δεδομένα.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Chrome Verification Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational training simulation that demonstrates how pages may be styled to request Chrome-style verification or login prompts, helping users recognize social-engineering patterns and suspicious permission or data requests.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική προσομοίωση που δείχνει πώς μπορούν να σχεδιαστούν σελίδες για να ζητούν προτροπές επαλήθευσης ή σύνδεσης τύπου Chrome, βοηθώντας τον χρήστη να αναγνωρίζει μοτίβα social engineering και ύποπτα αιτήματα για δικαιώματα ή δεδομένα.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Data Grabber Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational training simulation that demonstrates how pages may be styled to request broad personal-data collection prompts, helping users recognize social-engineering patterns and suspicious permission or data requests.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική προσομοίωση που δείχνει πώς μπορούν να σχεδιαστούν σελίδες για να ζητούν γενικές προτροπές συλλογής προσωπικών δεδομένων, βοηθώντας τον χρήστη να αναγνωρίζει μοτίβα social engineering και ύποπτα αιτήματα για δικαιώματα ή δεδομένα.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Discord Verification Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational training simulation that demonstrates how pages may be styled to request Discord-style verification or login prompts, helping users recognize social-engineering patterns and suspicious permission or data requests.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική προσομοίωση που δείχνει πώς μπορούν να σχεδιαστούν σελίδες για να ζητούν προτροπές επαλήθευσης ή σύνδεσης τύπου Discord, βοηθώντας τον χρήστη να αναγνωρίζει μοτίβα social engineering και ύποπτα αιτήματα για δικαιώματα ή δεδομένα.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Facebook Verification Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational training simulation that demonstrates how pages may be styled to request Facebook-style verification or login prompts, helping users recognize social-engineering patterns and suspicious permission or data requests.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική προσομοίωση που δείχνει πώς μπορούν να σχεδιαστούν σελίδες για να ζητούν προτροπές επαλήθευσης ή σύνδεσης τύπου Facebook, βοηθώντας τον χρήστη να αναγνωρίζει μοτίβα social engineering και ύποπτα αιτήματα για δικαιώματα ή δεδομένα.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Front Camera Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational training simulation that demonstrates how pages may be styled to request front camera access, helping users recognize social-engineering patterns and suspicious permission or data requests.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική προσομοίωση που δείχνει πώς μπορούν να σχεδιαστούν σελίδες για να ζητούν πρόσβαση στην μπροστινή κάμερα, βοηθώντας τον χρήστη να αναγνωρίζει μοτίβα social engineering και ύποπτα αιτήματα για δικαιώματα ή δεδομένα.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Front Camera Video Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational training simulation that demonstrates how pages may be styled to request camera video access, helping users recognize social-engineering patterns and suspicious permission or data requests.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική προσομοίωση που δείχνει πώς μπορούν να σχεδιαστούν σελίδες για να ζητούν πρόσβαση σε βίντεο κάμερας, βοηθώντας τον χρήστη να αναγνωρίζει μοτίβα social engineering και ύποπτα αιτήματα για δικαιώματα ή δεδομένα.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Google Location Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational training simulation that demonstrates how pages may be styled to request location-sharing prompts styled around Google-like flows, helping users recognize social-engineering patterns and suspicious permission or data requests.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική προσομοίωση που δείχνει πώς μπορούν να σχεδιαστούν σελίδες για να ζητούν προτροπές κοινοποίησης τοποθεσίας με στυλ παρόμοιο με Google, βοηθώντας τον χρήστη να αναγνωρίζει μοτίβα social engineering και ύποπτα αιτήματα για δικαιώματα ή δεδομένα.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Instagram Verification Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational training simulation that demonstrates how pages may be styled to request Instagram-style verification or login prompts, helping users recognize social-engineering patterns and suspicious permission or data requests.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική προσομοίωση που δείχνει πώς μπορούν να σχεδιαστούν σελίδες για να ζητούν προτροπές επαλήθευσης ή σύνδεσης τύπου Instagram, βοηθώντας τον χρήστη να αναγνωρίζει μοτίβα social engineering και ύποπτα αιτήματα για δικαιώματα ή δεδομένα.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Location Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational training simulation that demonstrates how pages may be styled to request location-sharing prompts, helping users recognize social-engineering patterns and suspicious permission or data requests.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική προσομοίωση που δείχνει πώς μπορούν να σχεδιαστούν σελίδες για να ζητούν προτροπές κοινοποίησης τοποθεσίας, βοηθώντας τον χρήστη να αναγνωρίζει μοτίβα social engineering και ύποπτα αιτήματα για δικαιώματα ή δεδομένα.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Microphone Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational training simulation that demonstrates how pages may be styled to request microphone access, helping users recognize social-engineering patterns and suspicious permission or data requests.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική προσομοίωση που δείχνει πώς μπορούν να σχεδιαστούν σελίδες για να ζητούν πρόσβαση στο μικρόφωνο, βοηθώντας τον χρήστη να αναγνωρίζει μοτίβα social engineering και ύποπτα αιτήματα για δικαιώματα ή δεδομένα.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake OnlyFans Verification Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational training simulation that demonstrates how pages may be styled to request OnlyFans-style verification or login prompts, helping users recognize social-engineering patterns and suspicious permission or data requests.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική προσομοίωση που δείχνει πώς μπορούν να σχεδιαστούν σελίδες για να ζητούν προτροπές επαλήθευσης ή σύνδεσης τύπου OnlyFans, βοηθώντας τον χρήστη να αναγνωρίζει μοτίβα social engineering και ύποπτα αιτήματα για δικαιώματα ή δεδομένα.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Steam Verification Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational training simulation that demonstrates how pages may be styled to request Steam-style verification or login prompts, helping users recognize social-engineering patterns and suspicious permission or data requests.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική προσομοίωση που δείχνει πώς μπορούν να σχεδιαστούν σελίδες για να ζητούν προτροπές επαλήθευσης ή σύνδεσης τύπου Steam, βοηθώντας τον χρήστη να αναγνωρίζει μοτίβα social engineering και ύποπτα αιτήματα για δικαιώματα ή δεδομένα.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Twitch Verification Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational training simulation that demonstrates how pages may be styled to request Twitch-style verification or login prompts, helping users recognize social-engineering patterns and suspicious permission or data requests.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική προσομοίωση που δείχνει πώς μπορούν να σχεδιαστούν σελίδες για να ζητούν προτροπές επαλήθευσης ή σύνδεσης τύπου Twitch, βοηθώντας τον χρήστη να αναγνωρίζει μοτίβα social engineering και ύποπτα αιτήματα για δικαιώματα ή δεδομένα.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake YouTube Verification Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational training simulation that demonstrates how pages may be styled to request YouTube-style verification or login prompts, helping users recognize social-engineering patterns and suspicious permission or data requests.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική προσομοίωση που δείχνει πώς μπορούν να σχεδιαστούν σελίδες για να ζητούν προτροπές επαλήθευσης ή σύνδεσης τύπου YouTube, βοηθώντας τον χρήστη να αναγνωρίζει μοτίβα social engineering και ύποπτα αιτήματα για δικαιώματα ή δεδομένα.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


## 📱 Fake Pages (Educational Use Only)

These scripts are **training simulations** intended to help you recognize social-engineering patterns used in fake social media pages.


### • Fake Apple iCloud Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around Apple iCloud bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου Apple iCloud, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Discord Nitro Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around Discord Nitro bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου Discord Nitro, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Epic Games Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around Epic Games bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου Epic Games, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Facebook Friends Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around Facebook Friends bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου Facebook Friends, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Free Robux Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around Free Robux bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου Free Robux, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake GitHub Pro Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around GitHub Pro bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου GitHub Pro, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Google Free Money Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around Google Free Money bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου Google Free Money, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Instagram Followers Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around Instagram Followers bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου Instagram Followers, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake MetaMask Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around MetaMask bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου MetaMask, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Microsoft 365 Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around Microsoft 365 bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου Microsoft 365, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake OnlyFans Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around OnlyFans bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου OnlyFans, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake PayPal Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around PayPal bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου PayPal, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Pinterest Pro Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around Pinterest Pro bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου Pinterest Pro, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake PlayStation Network Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around PlayStation Network bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου PlayStation Network, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Reddit Karma Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around Reddit Karma bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου Reddit Karma, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Snapchat Friends Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around Snapchat Friends bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου Snapchat Friends, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Steam Games Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around Steam Games bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου Steam Games, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Steam Wallet Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around Steam Wallet bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου Steam Wallet, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake TikTok Followers Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around TikTok Followers bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου TikTok Followers, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Trust Wallet Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around Trust Wallet bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου Trust Wallet, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Twitch Subs Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around Twitch Subs bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου Twitch Subs, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Twitter Followers Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around Twitter Followers bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου Twitter Followers, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake What's Up Dude Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around What's Up Dude bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου What's Up Dude, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake Xbox Live Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around Xbox Live bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου Xbox Live, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


### • Fake YouTube Subscribers Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

Educational simulation page styled around YouTube Subscribers bait themes so users can learn to identify impersonation, giveaway, follower, wallet, subscription, or account-upgrade style scams.

**Save Location:** Check the website tools catalog for the save location used by this page/script.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Εκπαιδευτική σελίδα προσομοίωσης βασισμένη σε δέλεαρ τύπου YouTube Subscribers, ώστε ο χρήστης να μαθαίνει να αναγνωρίζει απάτες μίμησης, giveaway, followers, wallet, subscription ή ψεύτικα account upgrades.

**Τοποθεσία Αποθήκευσης:** Έλεγξε τον κατάλογο εργαλείων του website για την τοποθεσία αποθήκευσης που χρησιμοποιεί αυτή η σελίδα/το script.

</details>


## 🦋 ButSystem.py (Exclusive)

### • ButSystem.py

<details>
<summary><strong>🇬🇧 English</strong></summary>

**ButSystem.py** is a self-hosted, local-first workspace that runs on your own device through Termux. It is built for private coordination and structured workflows, with modules for auth and access control, direct messages, groups, call-related flows, file and vault actions, profile management, security settings, and admin actions where permitted.

It is intended for organized personal or team use on systems you own or control, with a workflow centered around a generated local link and a browser interface.

**Save Location:** Check the script and its generated workspace folders on your device after setup.

**How to Use:** Run **ButSystem.py** from your DedSec setup, open the generated local link in your browser, and use the burger menu to switch modules such as Chats, Groups, Calls, Files, Profile, Settings, and Admin.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **ButSystem.py** είναι ένα self-hosted, local-first workspace που τρέχει στη δική σου συσκευή μέσω Termux. Είναι φτιαγμένο για ιδιωτικό συντονισμό και οργανωμένα workflows, με modules για έλεγχο πρόσβασης και σύνδεσης, direct messages, groups, ροές σχετικές με κλήσεις, ενέργειες για files και vault, διαχείριση προφίλ, ρυθμίσεις ασφαλείας και admin actions όπου επιτρέπεται.

Προορίζεται για οργανωμένη προσωπική ή ομαδική χρήση σε συστήματα που σου ανήκουν ή ελέγχεις, με κεντρικό workflow ένα generated local link και browser interface.

**Τοποθεσία Αποθήκευσης:** Έλεγξε το script και τους generated workspace φακέλους στη συσκευή σου μετά το setup.

**Πώς Χρησιμοποιείται:** Τρέξε το **ButSystem.py** από το DedSec setup, άνοιξε το generated local link στον browser σου και χρησιμοποίησε το burger menu για εναλλαγή μεταξύ modules όπως Chats, Groups, Calls, Files, Profile, Settings και Admin.

</details>


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
