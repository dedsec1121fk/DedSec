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

<details>
<summary><strong>🇬🇧 English</strong></summary>

The **DedSec Project** is a broad educational toolkit built for **Android + Termux**, bringing together many scripts, utilities, local web interfaces, and practice environments in one place. Its purpose is to help users learn how tools work, understand defensive awareness, and organize common Termux workflows from a single project.

This README is structured so the **installation process** and **every listed tool** include both **English** and **Greek** sections, similar to the bilingual style used in **README 2.md**.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **DedSec Project** είναι ένα ευρύ εκπαιδευτικό toolkit για **Android + Termux**, που συγκεντρώνει πολλά scripts, utilities, local web interfaces και περιβάλλοντα εξάσκησης σε ένα σημείο. Ο σκοπός του είναι να βοηθά τους χρήστες να μαθαίνουν πώς λειτουργούν τα εργαλεία, να κατανοούν καλύτερα την αμυντική επίγνωση και να οργανώνουν συνηθισμένα Termux workflows μέσα από ένα ενιαίο project.

Αυτό το README είναι δομημένο έτσι ώστε η **διαδικασία εγκατάστασης** και **κάθε καταχωρημένο εργαλείο** να περιλαμβάνουν και **English** και **Greek** ενότητες, παρόμοια με το δίγλωσσο στυλ που χρησιμοποιείται στο **README 2.md**.

</details>

## 📋 Table of Contents

* [How To Install And Setup The DedSec Project](#-how-to-install-and-setup-the-dedsec-project)
* [Settings & Configuration](#️-settings--configuration)
* [Explore The Toolkit](#️-explore-the-toolkit)
* [Developer Base](#-developer-base)
* [Network Tools](#-network-tools)
* [Personal Information Capture](#-personal-information-capture-educational-use-only)
* [Fake Pages](#-fake-pages-educational-use-only)
* [Games](#-games)
* [Other Tools](#️-other-tools)
* [No Category](#-no-category)
* [Sponsors-Only](#-sponsors-only)
* [ButSystem.py (Exclusive)](#-butsystempy-exclusive)
* [Contact Us & Credits](#-contact-us--credits)
* [Disclaimer & Terms of Use](#️-disclaimer--terms-of-use)

---

## 🚀 How To Install And Setup The DedSec Project

<details>
<summary><strong>🇬🇧 English</strong></summary>

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
- If storage access was denied earlier, run `termux-setup-storage` again.
- If Git is missing, run `pkg install git -y`.
- If you are already inside the DedSec folder, you do not need to clone the repository again.
- Using the F-Droid version of Termux is strongly recommended because some Play Store versions are outdated.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

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
- Αν η πρόσβαση αποθήκευσης είχε απορριφθεί νωρίτερα, τρέξε ξανά `termux-setup-storage`.
- Αν λείπει το Git, τρέξε `pkg install git -y`.
- Αν βρίσκεσαι ήδη μέσα στον φάκελο DedSec, δεν χρειάζεται να ξανακάνεις clone το repository.
- Προτείνεται έντονα η έκδοση του Termux από το F-Droid, επειδή κάποιες εκδόσεις του Play Store είναι παλιές.

</details>

---

## ⚙️ Settings & Configuration

<details>
<summary><strong>🇬🇧 English</strong></summary>

The DedSec Project includes a central **Settings.py** tool that manages the main configuration of the toolkit.

### Main Features

- project updates and package refresh
- persistent language preference (English / Greek)
- menu style selection: **list**, **grid**, or **number**
- terminal prompt customization
- system information display
- home scripts integration
- backup and restore support
- complete uninstall with cleanup
- automatic Termux bash configuration updates
- credits and project information

### First-Time Setup Focus

After installation, the main things to configure are:

1. your preferred language  
2. your menu style  
3. any system preferences you want  
4. project updates when needed

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το DedSec Project περιλαμβάνει το κεντρικό εργαλείο **Settings.py**, το οποίο διαχειρίζεται τη βασική ρύθμιση ολόκληρου του toolkit.

### Κύριες Δυνατότητες

- ενημερώσεις project και ανανέωση πακέτων
- μόνιμη επιλογή γλώσσας (English / Greek)
- επιλογή στυλ μενού: **list**, **grid** ή **number**
- παραμετροποίηση terminal prompt
- προβολή πληροφοριών συστήματος
- ενσωμάτωση home scripts
- υποστήριξη backup και restore
- πλήρες uninstall με καθαρισμό
- αυτόματες ενημερώσεις ρυθμίσεων bash στο Termux
- credits και πληροφορίες για το project

### Έμφαση στην Πρώτη Ρύθμιση

Μετά την εγκατάσταση, τα βασικά που χρειάζεται να ρυθμίσεις είναι:

1. τη γλώσσα που προτιμάς  
2. το στυλ μενού που θέλεις  
3. όποιες προτιμήσεις συστήματος σε εξυπηρετούν  
4. τις ενημερώσεις του project όταν χρειάζονται

</details>

---

## 🛡️ Explore The Toolkit

<details>
<summary><strong>🇬🇧 English</strong></summary>

> **CRITICAL NOTICE:** The following scripts are included for **educational and defensive purposes only**. Their role is to help users understand how tools, lures, and simulations work so they can improve awareness, testing discipline, and self-protection in controlled environments.

### Toolkit Summary

- **Developer Base:** 9 tools
- **Network Tools:** 10 tools
- **Other Tools:** 6 tools
- **Games:** 5 tools
- **Personal Information Capture:** 17 tools
- **Social Media / Fake Pages:** 25 tools
- **No Category:** 3 tools
- **Sponsors-Only:** 4 tools

**Total listed on tools page:** 79 tools

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

> **ΚΡΙΣΙΜΗ ΣΗΜΕΙΩΣΗ:** Τα παρακάτω scripts περιλαμβάνονται μόνο για **εκπαιδευτικούς και αμυντικούς σκοπούς**. Ο ρόλος τους είναι να βοηθούν τους χρήστες να κατανοούν πώς λειτουργούν εργαλεία, lures και simulations, ώστε να βελτιώνουν την επίγνωση, την πειθαρχία στις δοκιμές και την αυτοπροστασία τους μέσα σε ελεγχόμενα περιβάλλοντα.

### Σύνοψη Toolkit

- **Developer Base:** 9 εργαλεία
- **Network Tools:** 10 εργαλεία
- **Other Tools:** 6 εργαλεία
- **Games:** 5 εργαλεία
- **Personal Information Capture:** 17 εργαλεία
- **Social Media / Fake Pages:** 25 εργαλεία
- **No Category:** 3 εργαλεία
- **Sponsors-Only:** 4 εργαλεία

**Συνολικά καταχωρημένα στη σελίδα εργαλείων:** 79 εργαλεία

</details>

---
## 🧑‍💻 Developer Base

### • File Converter

<details>
<summary><strong>🇬🇧 English</strong></summary>

**File Converter** is a powerful file converter supporting 40+ formats and intended to simplify format changes directly from Termux.

**Save Location:** ~/storage/downloads/File Converter/

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **File Converter** είναι ένας ισχυρός μετατροπέας αρχείων που υποστηρίζει 40+ formats και έχει σχεδιαστεί για να απλοποιεί τις αλλαγές μορφής απευθείας μέσα από το Termux.

**Τοποθεσία Αποθήκευσης:** ~/storage/downloads/File Converter/

</details>

### • File Type Checker

<details>
<summary><strong>🇬🇧 English</strong></summary>

**File Type Checker** is an advanced file analysis and security scanner that detects file types, extracts metadata, calculates cryptographic hashes, and identifies potential threats.

**Save Location:** Scan folder: ~/Downloads/File Type Checker/ | Quarantined files use the `.dangerous` extension

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **File Type Checker** είναι ένα προηγμένο εργαλείο ανάλυσης αρχείων και security scanner που ανιχνεύει τύπους αρχείων, εξάγει metadata, υπολογίζει cryptographic hashes και εντοπίζει πιθανούς κινδύνους.

**Τοποθεσία Αποθήκευσης:** Φάκελος σάρωσης: ~/Downloads/File Type Checker/ | Τα quarantined αρχεία χρησιμοποιούν την κατάληξη `.dangerous`

</details>

### • Mobile Desktop

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Mobile Desktop** is a Termux Linux Desktop Manager without root that sets up a proot-distro desktop environment with VNC/X11 options and a built-in program manager for install, update, and removal workflows.

**Save Location:** Scan folders created in the current directory: scan_[target]_[date]

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Mobile Desktop** είναι ένας Termux Linux Desktop Manager χωρίς root που στήνει περιβάλλον desktop μέσω proot-distro με επιλογές VNC/X11 και ενσωματωμένο program manager για install, update και removal workflows.

**Τοποθεσία Αποθήκευσης:** Οι scan φάκελοι δημιουργούνται στο τρέχον directory: scan_[target]_[date]

</details>

### • Mobile Developer Setup

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Mobile Developer Setup** automates a mobile web-development environment in Termux by installing common developer tools, configuring paths, and providing quick-start project scaffolding.

**Save Location:** Scan folders created in the current directory: scan_[target]_[date]

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Mobile Developer Setup** αυτοματοποιεί ένα mobile web-development environment στο Termux εγκαθιστώντας κοινά developer tools, ρυθμίζοντας paths και παρέχοντας quick-start project scaffolding.

**Τοποθεσία Αποθήκευσης:** Οι scan φάκελοι δημιουργούνται στο τρέχον directory: scan_[target]_[date]

</details>

### • Simple Websites Creator

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Simple Websites Creator** is a comprehensive website builder that creates responsive HTML websites with customizable layouts, colors, fonts, and SEO settings.

**Save Location:** ~/storage/downloads/Websites/

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Simple Websites Creator** είναι ένας ολοκληρωμένος website builder που δημιουργεί responsive HTML websites με παραμετροποιήσιμα layouts, χρώματα, γραμματοσειρές και SEO settings.

**Τοποθεσία Αποθήκευσης:** ~/storage/downloads/Websites/

</details>

### • Smart Notes

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Smart Notes** is a terminal note-taking app with reminder support for quick personal organization inside Termux.

**Save Location:** ~/.smart_notes.json

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Smart Notes** είναι μια terminal εφαρμογή σημειώσεων με υποστήριξη υπενθυμίσεων για γρήγορη προσωπική οργάνωση μέσα στο Termux.

**Τοποθεσία Αποθήκευσης:** ~/.smart_notes.json

</details>

### • Dead Switch

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Dead Switch** syncs your `~/storage/downloads/Dead Switch/` folder to a GitHub repository with safety controls such as create-only-new uploads, overwrite sync, visibility toggle, and a one-click kill switch.

**Save Location:** ~/storage/downloads/Dead Switch/

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Dead Switch** συγχρονίζει τον φάκελο `~/storage/downloads/Dead Switch/` με ένα GitHub repository, με safety controls όπως create-only-new uploads, overwrite sync, visibility toggle και one-click kill switch.

**Τοποθεσία Αποθήκευσης:** ~/storage/downloads/Dead Switch/

</details>

### • Tree Explorer

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Tree Explorer** is a file-system explorer for Termux that lets you browse folders, search files, find duplicates by hash, and clean empty directories with safe prompts.

**Save Location:** Scan folders created in the current directory: scan_[target]_[date]

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Tree Explorer** είναι ένας file-system explorer για Termux που σου επιτρέπει να περιηγείσαι σε φακέλους, να αναζητάς αρχεία, να βρίσκεις duplicates μέσω hash και να καθαρίζεις άδειους φακέλους με ασφαλή prompts.

**Τοποθεσία Αποθήκευσης:** Οι scan φάκελοι δημιουργούνται στο τρέχον directory: scan_[target]_[date]

</details>

### • Devices Finder

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Devices Finder** is a local-network device discovery tool for Termux that works without root. It separates live-host discovery from service scanning to reduce false positives, classifies devices using ports, banners, hostnames, and vendor hints, and can export JSON, TXT, CSV, and HTML reports.

**Save Location:** ~/storage/downloads/Devices Finder/ as devices_scan_[timestamp].json/.txt/.csv/.html (falls back to ~/downloads/Devices Finder/ or the current directory)

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Devices Finder** είναι ένα local-network εργαλείο ανακάλυψης συσκευών για Termux που λειτουργεί χωρίς root. Χωρίζει το live-host discovery από το service scanning ώστε να μειώνει false positives, ταξινομεί συσκευές με βάση ports, banners, hostnames και vendor hints και μπορεί να εξάγει JSON, TXT, CSV και HTML reports.

**Τοποθεσία Αποθήκευσης:** ~/storage/downloads/Devices Finder/ ως devices_scan_[timestamp].json/.txt/.csv/.html (με fallback στο ~/downloads/Devices Finder/ ή στο τρέχον directory)

</details>


---

## 🔧 Network Tools

### • Bug Hunter

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Bug Hunter** is an authorized web security recon and misconfiguration scanner. It performs DNS checks (SPF/DMARC/CAA), TLS and certificate expiry checks, security header and cookie-flag audits, tech fingerprinting, CORS / HTTP methods checks, crawling, and JavaScript endpoint or secret analysis.

**Save Location:** Reports are saved in the output folder (default: bughunter_out/): report.json, report.csv, report.html, and optionally report.pdf

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Bug Hunter** είναι ένα authorized web security recon και misconfiguration scanner. Εκτελεί DNS ελέγχους (SPF/DMARC/CAA), ελέγχους TLS και λήξης πιστοποιητικών, audits για security headers και cookie flags, tech fingerprinting, ελέγχους CORS / HTTP methods, crawling και ανάλυση JavaScript endpoints ή secrets.

**Τοποθεσία Αποθήκευσης:** Τα reports αποθηκεύονται στον output φάκελο (default: bughunter_out/): report.json, report.csv, report.html και προαιρετικά report.pdf

</details>

### • Dark

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Dark** is a specialized dark-web OSINT tool and crawler designed for Tor-network analysis.

**Save Location:** /sdcard/Download/DarkNet (or ~/DarkNet if storage is inaccessible)

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Dark** είναι ένα εξειδικευμένο dark-web OSINT εργαλείο και crawler σχεδιασμένο για ανάλυση του Tor network.

**Τοποθεσία Αποθήκευσης:** /sdcard/Download/DarkNet (ή ~/DarkNet αν το storage δεν είναι προσβάσιμο)

</details>

### • DedSec's Network

<details>
<summary><strong>🇬🇧 English</strong></summary>

**DedSec's Network** is an advanced non-root network toolkit optimized for speed and stability.

**Save Location:** ~/DedSec's Network

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **DedSec's Network** είναι ένα προηγμένο non-root network toolkit βελτιστοποιημένο για ταχύτητα και σταθερότητα.

**Τοποθεσία Αποθήκευσης:** ~/DedSec's Network

</details>

### • Digital Footprint Finder

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Digital Footprint Finder** is a conservative OSINT username scanner with pack-based coverage, multi-signal verification to reduce false positives, FOUND vs POSSIBLE result grouping, and optional DuckDuckGo dorking with TXT, JSON, CSV, and HTML exports.

**Save Location:** ~/storage/downloads/Digital Footprint Finder/[username]_[YYYYMMDD_HHMMSS].txt plus optional .json/.csv/.html (falls back to /sdcard/Download when Termux storage is unavailable)

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Digital Footprint Finder** είναι ένας conservative OSINT username scanner με pack-based coverage, multi-signal verification για μείωση false positives, ομαδοποίηση FOUND vs POSSIBLE αποτελεσμάτων και προαιρετικό DuckDuckGo dorking με εξαγωγές TXT, JSON, CSV και HTML.

**Τοποθεσία Αποθήκευσης:** ~/storage/downloads/Digital Footprint Finder/[username]_[YYYYMMDD_HHMMSS].txt και προαιρετικά .json/.csv/.html (με fallback στο /sdcard/Download όταν το Termux storage δεν είναι διαθέσιμο)

</details>

### • Connections.py

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Connections.py** is a secure chat and file-sharing server with real-time messaging, file sharing up to 50GB, WebRTC video calls, integrated file management, and optional Cloudflare tunneling. It combines Butterfly Chat and DedSec's Database under a unified secret-key authentication system.

**Save Location:** Downloads go to `~/Downloads/DedSec's Database`

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Connections.py** είναι ένας ασφαλής chat και file-sharing server με real-time messaging, διαμοιρασμό αρχείων έως 50GB, WebRTC βιντεοκλήσεις, ενσωματωμένη διαχείριση αρχείων και προαιρετικό Cloudflare tunneling. Συνδυάζει το Butterfly Chat και το DedSec's Database κάτω από ένα ενιαίο secret-key authentication system.

**Τοποθεσία Αποθήκευσης:** Τα downloads πηγαίνουν στο `~/Downloads/DedSec's Database`

</details>

### • Link Shield

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Link Shield** is a security-focused URL inspector that follows redirects, checks HTTPS and SSL, flags suspicious domains and patterns, and generates a risk report before you open a link.

**Save Location:** Scan folders created in the current directory: scan_[target]_[date]

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Link Shield** είναι ένας security-focused URL inspector που ακολουθεί redirects, ελέγχει HTTPS και SSL, επισημαίνει ύποπτα domains και patterns και δημιουργεί risk report πριν ανοίξεις έναν σύνδεσμο.

**Τοποθεσία Αποθήκευσης:** Οι scan φάκελοι δημιουργούνται στο τρέχον directory: scan_[target]_[date]

</details>

### • Masker

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Masker** is a URL masker for presentation, demonstration, and controlled testing workflows.

**Save Location:** N/A (output shown on screen)

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Masker** είναι ένα URL masker για presentation, demonstration και controlled testing workflows.

**Τοποθεσία Αποθήκευσης:** N/A (η έξοδος εμφανίζεται στην οθόνη)

</details>

### • QR Code Generator

<details>
<summary><strong>🇬🇧 English</strong></summary>

**QR Code Generator** is a Python-based QR code generator that creates QR codes for URLs and saves them in a dedicated Downloads folder.

**Save Location:** ~/storage/downloads/QR Codes/

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **QR Code Generator** είναι ένας Python-based QR code generator που δημιουργεί QR codes για URLs και τα αποθηκεύει σε ειδικό φάκελο στα Downloads.

**Τοποθεσία Αποθήκευσης:** ~/storage/downloads/QR Codes/

</details>

### • Sod

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Sod** is a load-testing tool for web applications with multiple test methods such as HTTP, WebSocket, database simulation, file upload, and mixed workload scenarios.

**Save Location:** Configuration: load_test_config.json in the script directory | Results: displayed in terminal

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Sod** είναι ένα load-testing εργαλείο για web applications με πολλαπλές μεθόδους δοκιμής όπως HTTP, WebSocket, database simulation, file upload και mixed workload scenarios.

**Τοποθεσία Αποθήκευσης:** Configuration: load_test_config.json στο script directory | Results: εμφανίζονται στο terminal

</details>

### • Store Scrapper

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Store Scrapper** is a single-file Python store scraper for Termux that works without root. It can discover categories and products across regular HTML stores and many JS-style stores by reading HTML, JSON-LD, embedded JSON, sitemaps, Shopify endpoints, WooCommerce APIs, meta tags, breadcrumbs, and internal links while saving results as it runs.

**Save Location:** ~/storage/downloads/Store Scrapper/<Store>/<Category>/<Product>/ with metadata.json, summary.txt, description.txt, images/, images.json, category state files, and FINAL_REPORT.txt

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Store Scrapper** είναι ένα single-file Python store scraper για Termux που λειτουργεί χωρίς root. Μπορεί να ανακαλύπτει categories και products σε κανονικά HTML stores αλλά και σε πολλά JS-style stores διαβάζοντας HTML, JSON-LD, embedded JSON, sitemaps, Shopify endpoints, WooCommerce APIs, meta tags, breadcrumbs και internal links, ενώ αποθηκεύει αποτελέσματα καθώς τρέχει.

**Τοποθεσία Αποθήκευσης:** ~/storage/downloads/Store Scrapper/<Store>/<Category>/<Product>/ με metadata.json, summary.txt, description.txt, images/, images.json, category state files και FINAL_REPORT.txt

</details>


---

## 📱 Personal Information Capture (Educational Use Only)

<details>
<summary><strong>🇬🇧 English</strong></summary>

These scripts are training simulations intended to help users understand how deceptive personal-data collection pages may be presented, so they can better recognize and defend against them in controlled environments.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Αυτά τα scripts είναι training simulations που έχουν στόχο να βοηθούν τους χρήστες να κατανοούν πώς μπορεί να παρουσιάζονται παραπλανητικές σελίδες συλλογής προσωπικών δεδομένων, ώστε να τις αναγνωρίζουν και να αμύνονται καλύτερα απέναντί τους σε ελεγχόμενα περιβάλλοντα.

</details>

### • Fake Back Camera Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Back Camera Page** is an educational simulation page themed around a fake back-camera capture flow. It is meant to show how deceptive pages may request permissions, recordings, location data, account details, or fake verification steps so you can recognize the warning signs in a controlled environment.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Back Camera Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη ροή λήψης από πίσω κάμερα. Έχει σχεδιαστεί για να δείχνει πώς παραπλανητικές σελίδες μπορεί να ζητούν άδειες, καταγραφές, δεδομένα τοποθεσίας, στοιχεία λογαριασμού ή ψεύτικα βήματα επαλήθευσης, ώστε να αναγνωρίζεις τα προειδοποιητικά σημάδια σε ελεγχόμενο περιβάλλον.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Back Camera Video Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Back Camera Video Page** is an educational simulation page themed around a fake back-camera video flow. It is meant to show how deceptive pages may request permissions, recordings, location data, account details, or fake verification steps so you can recognize the warning signs in a controlled environment.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Back Camera Video Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη ροή βίντεο από πίσω κάμερα. Έχει σχεδιαστεί για να δείχνει πώς παραπλανητικές σελίδες μπορεί να ζητούν άδειες, καταγραφές, δεδομένα τοποθεσίας, στοιχεία λογαριασμού ή ψεύτικα βήματα επαλήθευσης, ώστε να αναγνωρίζεις τα προειδοποιητικά σημάδια σε ελεγχόμενο περιβάλλον.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Card Details Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Card Details Page** is an educational simulation page themed around a fake card-details collection page. It is meant to show how deceptive pages may request permissions, recordings, location data, account details, or fake verification steps so you can recognize the warning signs in a controlled environment.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Card Details Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα συλλογής στοιχείων κάρτας. Έχει σχεδιαστεί για να δείχνει πώς παραπλανητικές σελίδες μπορεί να ζητούν άδειες, καταγραφές, δεδομένα τοποθεσίας, στοιχεία λογαριασμού ή ψεύτικα βήματα επαλήθευσης, ώστε να αναγνωρίζεις τα προειδοποιητικά σημάδια σε ελεγχόμενο περιβάλλον.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Chrome Verification Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Chrome Verification Page** is an educational simulation page themed around a fake Chrome verification prompt. It is meant to show how deceptive pages may request permissions, recordings, location data, account details, or fake verification steps so you can recognize the warning signs in a controlled environment.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Chrome Verification Page** είναι μια εκπαιδευτική simulation page με θέμα ένα ψεύτικο prompt επαλήθευσης Chrome. Έχει σχεδιαστεί για να δείχνει πώς παραπλανητικές σελίδες μπορεί να ζητούν άδειες, καταγραφές, δεδομένα τοποθεσίας, στοιχεία λογαριασμού ή ψεύτικα βήματα επαλήθευσης, ώστε να αναγνωρίζεις τα προειδοποιητικά σημάδια σε ελεγχόμενο περιβάλλον.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Data Grabber Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Data Grabber Page** is an educational simulation page themed around a fake broad data-collection page. It is meant to show how deceptive pages may request permissions, recordings, location data, account details, or fake verification steps so you can recognize the warning signs in a controlled environment.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Data Grabber Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα ευρείας συλλογής δεδομένων. Έχει σχεδιαστεί για να δείχνει πώς παραπλανητικές σελίδες μπορεί να ζητούν άδειες, καταγραφές, δεδομένα τοποθεσίας, στοιχεία λογαριασμού ή ψεύτικα βήματα επαλήθευσης, ώστε να αναγνωρίζεις τα προειδοποιητικά σημάδια σε ελεγχόμενο περιβάλλον.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Discord Verification Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Discord Verification Page** is an educational simulation page themed around a fake Discord verification flow. It is meant to show how deceptive pages may request permissions, recordings, location data, account details, or fake verification steps so you can recognize the warning signs in a controlled environment.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Discord Verification Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη ροή επαλήθευσης Discord. Έχει σχεδιαστεί για να δείχνει πώς παραπλανητικές σελίδες μπορεί να ζητούν άδειες, καταγραφές, δεδομένα τοποθεσίας, στοιχεία λογαριασμού ή ψεύτικα βήματα επαλήθευσης, ώστε να αναγνωρίζεις τα προειδοποιητικά σημάδια σε ελεγχόμενο περιβάλλον.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Facebook Verification Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Facebook Verification Page** is an educational simulation page themed around a fake Facebook verification flow. It is meant to show how deceptive pages may request permissions, recordings, location data, account details, or fake verification steps so you can recognize the warning signs in a controlled environment.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Facebook Verification Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη ροή επαλήθευσης Facebook. Έχει σχεδιαστεί για να δείχνει πώς παραπλανητικές σελίδες μπορεί να ζητούν άδειες, καταγραφές, δεδομένα τοποθεσίας, στοιχεία λογαριασμού ή ψεύτικα βήματα επαλήθευσης, ώστε να αναγνωρίζεις τα προειδοποιητικά σημάδια σε ελεγχόμενο περιβάλλον.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Front Camera Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Front Camera Page** is an educational simulation page themed around a fake front-camera capture flow. It is meant to show how deceptive pages may request permissions, recordings, location data, account details, or fake verification steps so you can recognize the warning signs in a controlled environment.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Front Camera Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη ροή λήψης από μπροστινή κάμερα. Έχει σχεδιαστεί για να δείχνει πώς παραπλανητικές σελίδες μπορεί να ζητούν άδειες, καταγραφές, δεδομένα τοποθεσίας, στοιχεία λογαριασμού ή ψεύτικα βήματα επαλήθευσης, ώστε να αναγνωρίζεις τα προειδοποιητικά σημάδια σε ελεγχόμενο περιβάλλον.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Front Camera Video Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Front Camera Video Page** is an educational simulation page themed around a fake front-camera video flow. It is meant to show how deceptive pages may request permissions, recordings, location data, account details, or fake verification steps so you can recognize the warning signs in a controlled environment.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Front Camera Video Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη ροή βίντεο από μπροστινή κάμερα. Έχει σχεδιαστεί για να δείχνει πώς παραπλανητικές σελίδες μπορεί να ζητούν άδειες, καταγραφές, δεδομένα τοποθεσίας, στοιχεία λογαριασμού ή ψεύτικα βήματα επαλήθευσης, ώστε να αναγνωρίζεις τα προειδοποιητικά σημάδια σε ελεγχόμενο περιβάλλον.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Google Location Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Google Location Page** is an educational simulation page themed around a fake Google-themed location prompt. It is meant to show how deceptive pages may request permissions, recordings, location data, account details, or fake verification steps so you can recognize the warning signs in a controlled environment.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Google Location Page** είναι μια εκπαιδευτική simulation page με θέμα ένα ψεύτικο Google-themed prompt τοποθεσίας. Έχει σχεδιαστεί για να δείχνει πώς παραπλανητικές σελίδες μπορεί να ζητούν άδειες, καταγραφές, δεδομένα τοποθεσίας, στοιχεία λογαριασμού ή ψεύτικα βήματα επαλήθευσης, ώστε να αναγνωρίζεις τα προειδοποιητικά σημάδια σε ελεγχόμενο περιβάλλον.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Instagram Verification Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Instagram Verification Page** is an educational simulation page themed around a fake Instagram verification flow. It is meant to show how deceptive pages may request permissions, recordings, location data, account details, or fake verification steps so you can recognize the warning signs in a controlled environment.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Instagram Verification Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη ροή επαλήθευσης Instagram. Έχει σχεδιαστεί για να δείχνει πώς παραπλανητικές σελίδες μπορεί να ζητούν άδειες, καταγραφές, δεδομένα τοποθεσίας, στοιχεία λογαριασμού ή ψεύτικα βήματα επαλήθευσης, ώστε να αναγνωρίζεις τα προειδοποιητικά σημάδια σε ελεγχόμενο περιβάλλον.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Location Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Location Page** is an educational simulation page themed around a fake location-sharing request page. It is meant to show how deceptive pages may request permissions, recordings, location data, account details, or fake verification steps so you can recognize the warning signs in a controlled environment.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Location Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα αιτήματος κοινοποίησης τοποθεσίας. Έχει σχεδιαστεί για να δείχνει πώς παραπλανητικές σελίδες μπορεί να ζητούν άδειες, καταγραφές, δεδομένα τοποθεσίας, στοιχεία λογαριασμού ή ψεύτικα βήματα επαλήθευσης, ώστε να αναγνωρίζεις τα προειδοποιητικά σημάδια σε ελεγχόμενο περιβάλλον.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Microphone Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Microphone Page** is an educational simulation page themed around a fake microphone access request. It is meant to show how deceptive pages may request permissions, recordings, location data, account details, or fake verification steps so you can recognize the warning signs in a controlled environment.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Microphone Page** είναι μια εκπαιδευτική simulation page με θέμα ένα ψεύτικο αίτημα πρόσβασης στο μικρόφωνο. Έχει σχεδιαστεί για να δείχνει πώς παραπλανητικές σελίδες μπορεί να ζητούν άδειες, καταγραφές, δεδομένα τοποθεσίας, στοιχεία λογαριασμού ή ψεύτικα βήματα επαλήθευσης, ώστε να αναγνωρίζεις τα προειδοποιητικά σημάδια σε ελεγχόμενο περιβάλλον.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake OnlyFans Verification Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake OnlyFans Verification Page** is an educational simulation page themed around a fake OnlyFans verification flow. It is meant to show how deceptive pages may request permissions, recordings, location data, account details, or fake verification steps so you can recognize the warning signs in a controlled environment.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake OnlyFans Verification Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη ροή επαλήθευσης OnlyFans. Έχει σχεδιαστεί για να δείχνει πώς παραπλανητικές σελίδες μπορεί να ζητούν άδειες, καταγραφές, δεδομένα τοποθεσίας, στοιχεία λογαριασμού ή ψεύτικα βήματα επαλήθευσης, ώστε να αναγνωρίζεις τα προειδοποιητικά σημάδια σε ελεγχόμενο περιβάλλον.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Steam Verification Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Steam Verification Page** is an educational simulation page themed around a fake Steam verification flow. It is meant to show how deceptive pages may request permissions, recordings, location data, account details, or fake verification steps so you can recognize the warning signs in a controlled environment.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Steam Verification Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη ροή επαλήθευσης Steam. Έχει σχεδιαστεί για να δείχνει πώς παραπλανητικές σελίδες μπορεί να ζητούν άδειες, καταγραφές, δεδομένα τοποθεσίας, στοιχεία λογαριασμού ή ψεύτικα βήματα επαλήθευσης, ώστε να αναγνωρίζεις τα προειδοποιητικά σημάδια σε ελεγχόμενο περιβάλλον.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Twitch Verification Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Twitch Verification Page** is an educational simulation page themed around a fake Twitch verification flow. It is meant to show how deceptive pages may request permissions, recordings, location data, account details, or fake verification steps so you can recognize the warning signs in a controlled environment.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Twitch Verification Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη ροή επαλήθευσης Twitch. Έχει σχεδιαστεί για να δείχνει πώς παραπλανητικές σελίδες μπορεί να ζητούν άδειες, καταγραφές, δεδομένα τοποθεσίας, στοιχεία λογαριασμού ή ψεύτικα βήματα επαλήθευσης, ώστε να αναγνωρίζεις τα προειδοποιητικά σημάδια σε ελεγχόμενο περιβάλλον.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake YouTube Verification Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake YouTube Verification Page** is an educational simulation page themed around a fake YouTube verification flow. It is meant to show how deceptive pages may request permissions, recordings, location data, account details, or fake verification steps so you can recognize the warning signs in a controlled environment.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake YouTube Verification Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη ροή επαλήθευσης YouTube. Έχει σχεδιαστεί για να δείχνει πώς παραπλανητικές σελίδες μπορεί να ζητούν άδειες, καταγραφές, δεδομένα τοποθεσίας, στοιχεία λογαριασμού ή ψεύτικα βήματα επαλήθευσης, ώστε να αναγνωρίζεις τα προειδοποιητικά σημάδια σε ελεγχόμενο περιβάλλον.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>


---

## 📱 Fake Pages (Educational Use Only)

<details>
<summary><strong>🇬🇧 English</strong></summary>

These scripts are educational simulations intended to help users recognize social-engineering patterns, fake reward pages, fake verification flows, and imitation brand pages often used to pressure people into unsafe actions.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Αυτά τα scripts είναι εκπαιδευτικά simulations που έχουν στόχο να βοηθούν τους χρήστες να αναγνωρίζουν social-engineering patterns, ψεύτικες reward pages, ψεύτικες verification flows και imitation brand pages που συχνά χρησιμοποιούνται για να πιέζουν ανθρώπους σε μη ασφαλείς ενέργειες.

</details>

### • Fake Apple iCloud Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Apple iCloud Page** is an educational simulation page themed around a fake Apple iCloud page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Apple iCloud Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα Apple iCloud. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Discord Nitro Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Discord Nitro Page** is an educational simulation page themed around a fake Discord Nitro offer page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Discord Nitro Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα προσφοράς Discord Nitro. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Epic Games Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Epic Games Page** is an educational simulation page themed around a fake Epic Games page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Epic Games Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα Epic Games. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Facebook Friends Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Facebook Friends Page** is an educational simulation page themed around a fake Facebook friends-related page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Facebook Friends Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα σχετική με Facebook friends. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Free Robux Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Free Robux Page** is an educational simulation page themed around a fake free Robux reward page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Free Robux Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα δωρεάν Robux. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake GitHub Pro Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake GitHub Pro Page** is an educational simulation page themed around a fake GitHub Pro upgrade page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake GitHub Pro Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα αναβάθμισης GitHub Pro. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Google Free Money Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Google Free Money Page** is an educational simulation page themed around a fake Google free-money reward page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Google Free Money Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα υποτιθέμενης δωρεάν χρηματικής ανταμοιβής από Google. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Instagram Followers Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Instagram Followers Page** is an educational simulation page themed around a fake Instagram followers boost page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Instagram Followers Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα ενίσχυσης followers για Instagram. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake MetaMask Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake MetaMask Page** is an educational simulation page themed around a fake MetaMask page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake MetaMask Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα MetaMask. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Microsoft 365 Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Microsoft 365 Page** is an educational simulation page themed around a fake Microsoft 365 page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Microsoft 365 Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα Microsoft 365. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake OnlyFans Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake OnlyFans Page** is an educational simulation page themed around a fake OnlyFans page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake OnlyFans Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα OnlyFans. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake PayPal Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake PayPal Page** is an educational simulation page themed around a fake PayPal page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake PayPal Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα PayPal. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Pinterest Pro Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Pinterest Pro Page** is an educational simulation page themed around a fake Pinterest Pro page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Pinterest Pro Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα Pinterest Pro. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake PlayStation Network Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake PlayStation Network Page** is an educational simulation page themed around a fake PlayStation Network page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake PlayStation Network Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα PlayStation Network. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Reddit Karma Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Reddit Karma Page** is an educational simulation page themed around a fake Reddit Karma reward page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Reddit Karma Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα ανταμοιβής Reddit Karma. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Snapchat Friends Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Snapchat Friends Page** is an educational simulation page themed around a fake Snapchat friends-related page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Snapchat Friends Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα σχετική με Snapchat friends. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Steam Games Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Steam Games Page** is an educational simulation page themed around a fake Steam games reward page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Steam Games Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα υποτιθέμενων Steam games. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Steam Wallet Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Steam Wallet Page** is an educational simulation page themed around a fake Steam Wallet page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Steam Wallet Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα Steam Wallet. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake TikTok Followers Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake TikTok Followers Page** is an educational simulation page themed around a fake TikTok followers boost page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake TikTok Followers Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα ενίσχυσης followers για TikTok. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Trust Wallet Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Trust Wallet Page** is an educational simulation page themed around a fake Trust Wallet page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Trust Wallet Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα Trust Wallet. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Twitch Subs Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Twitch Subs Page** is an educational simulation page themed around a fake Twitch subscriptions reward page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Twitch Subs Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα ανταμοιβής Twitch subs. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Twitter Followers Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Twitter Followers Page** is an educational simulation page themed around a fake Twitter followers boost page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Twitter Followers Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα ενίσχυσης followers για Twitter. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake What's Up Dude Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake What's Up Dude Page** is an educational simulation page themed around a fake casual or bait-style social page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake What's Up Dude Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη casual ή bait-style social page. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake Xbox Live Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake Xbox Live Page** is an educational simulation page themed around a fake Xbox Live page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake Xbox Live Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα Xbox Live. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>

### • Fake YouTube Subscribers Page

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Fake YouTube Subscribers Page** is an educational simulation page themed around a fake YouTube subscribers boost page. It is designed to help you recognize persuasive wording, visual tricks, urgency prompts, reward claims, and fake login or verification flows commonly used in scam pages and social-engineering lures.

**Save Location:** Check the website tools catalog or script page for the current save path used by this tool.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Fake YouTube Subscribers Page** είναι μια εκπαιδευτική simulation page με θέμα μια ψεύτικη σελίδα ενίσχυσης subscribers για YouTube. Έχει σχεδιαστεί για να σε βοηθά να αναγνωρίζεις πειστική διατύπωση, οπτικά τεχνάσματα, προτροπές επείγοντος, υποσχέσεις ανταμοιβής και ψεύτικες ροές σύνδεσης ή επαλήθευσης που χρησιμοποιούνται συχνά σε scam pages και social-engineering lures.

**Τοποθεσία Αποθήκευσης:** Δες το website tools catalog ή τη σελίδα του script για το τρέχον path αποθήκευσης που χρησιμοποιεί αυτό το εργαλείο.

</details>


---

## 🎮 Games

### • Buzz

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Buzz** is a text-only trivia party game for Termux with a fixed built-in database of 15,000 questions and no runtime generation.

**Save Location:** ~/Buzz/ (data/ for DB, profiles, settings, highscores)

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Buzz** είναι ένα text-only trivia party game για Termux με σταθερή ενσωματωμένη βάση 15.000 ερωτήσεων και χωρίς runtime generation.

**Τοποθεσία Αποθήκευσης:** ~/Buzz/ (data/ για DB, profiles, settings και highscores)

</details>

### • CTF God

<details>
<summary><strong>🇬🇧 English</strong></summary>

**CTF God** is a full-screen curses CTF game for Termux with story mode, missions, daily challenges, boss levels, an in-game economy, achievements, ranks, and challenge packs.

**Save Location:** /storage/emulated/0/Download/CTF God/files (fallback: ~/storage/downloads/CTF God/...) | Game state & packs: ~/.ctf_god/

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **CTF God** είναι ένα full-screen curses CTF game για Termux με story mode, missions, daily challenges, boss levels, in-game economy, achievements, ranks και challenge packs.

**Τοποθεσία Αποθήκευσης:** /storage/emulated/0/Download/CTF God/files (fallback: ~/storage/downloads/CTF God/...) | Game state & packs: ~/.ctf_god/

</details>

### • Detective

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Detective** is a story-driven terminal detective game for Termux with a large fixed case library, richer lore dossiers, district rumors, side stories, suspect rosters, evidence-board tools, timeline views, multiple difficulties, manual saves, autosave, and investigation commands.

**Save Location:** ~/Detective/ (player config, autosave/manual saves, and case progress)

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Detective** είναι ένα story-driven terminal detective game για Termux με μεγάλη σταθερή βιβλιοθήκη υποθέσεων, πλουσιότερα lore dossiers, district rumors, side stories, suspect rosters, εργαλεία evidence board, timeline views, πολλαπλές δυσκολίες, manual saves, autosave και investigation commands.

**Τοποθεσία Αποθήκευσης:** ~/Detective/ (player config, autosave/manual saves και case progress)

</details>

### • Tamagotchi

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Tamagotchi** is a fully featured terminal pet game.

**Save Location:** ~/.termux_tamagotchi_v8.json

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Tamagotchi** είναι ένα πλήρως εξοπλισμένο terminal pet game.

**Τοποθεσία Αποθήκευσης:** ~/.termux_tamagotchi_v8.json

</details>

### • Terminal Arcade

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Terminal Arcade** is an all-in-one terminal arcade pack with multiple mini-games in a single script.

**Save Location:** Scan folders created in the current directory: scan_[target]_[date]

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Terminal Arcade** είναι ένα all-in-one terminal arcade pack με πολλά mini-games μέσα σε ένα μόνο script.

**Τοποθεσία Αποθήκευσης:** Οι scan φάκελοι δημιουργούνται στο τρέχον directory: scan_[target]_[date]

</details>


---

## 🛠️ Other Tools

### • Android App Launcher

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Android App Launcher** is a utility for managing Android apps directly from the terminal, including extraction and reporting workflows.

**Save Location:** Extracted APKs: ~/storage/shared/Download/Extracted APK's | Reports: ~/storage/shared/Download/App_Security_Reports

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Android App Launcher** είναι ένα utility για διαχείριση Android apps απευθείας από το terminal, συμπεριλαμβανομένων workflows εξαγωγής και αναφορών.

**Τοποθεσία Αποθήκευσης:** Extracted APKs: ~/storage/shared/Download/Extracted APK's | Reports: ~/storage/shared/Download/App_Security_Reports

</details>

### • Loading Screen

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Loading Screen** lets you customize your Termux startup with ASCII art loading screens.

**Save Location:** Modifies `.bash_profile` and `bash.bashrc`

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Loading Screen** σου επιτρέπει να παραμετροποιείς το startup του Termux με ASCII art loading screens.

**Τοποθεσία Αποθήκευσης:** Τροποποιεί τα `.bash_profile` και `bash.bashrc`

</details>

### • Password Master

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Password Master** is a comprehensive password-management suite featuring encrypted vault storage, password generation, strength analysis, and password-improvement tools.

**Save Location:** Vault file: my_vault.enc in the script directory | Backups: ~/Downloads/Password Master Backup/

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Password Master** είναι μια ολοκληρωμένη password-management σουίτα με encrypted vault storage, δημιουργία κωδικών, ανάλυση ισχύος κωδικών και εργαλεία βελτίωσης κωδικών.

**Τοποθεσία Αποθήκευσης:** Vault file: my_vault.enc στο script directory | Backups: ~/Downloads/Password Master Backup/

</details>

### • Termux Backup Restore

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Termux Backup Restore** creates zipped backups of your Termux files to Downloads and can restore them with integrity checks.

**Save Location:** Scan folders created in the current directory: scan_[target]_[date]

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Termux Backup Restore** δημιουργεί zipped backups των αρχείων του Termux στα Downloads και μπορεί να τα επαναφέρει με integrity checks.

**Τοποθεσία Αποθήκευσης:** Οι scan φάκελοι δημιουργούνται στο τρέχον directory: scan_[target]_[date]

</details>

### • Termux Repair Wizard

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Termux Repair Wizard** is a troubleshooting wizard for Termux that checks common issues, suggests fixes, and can run safe repair commands step by step.

**Save Location:** Scan folders created in the current directory: scan_[target]_[date]

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Termux Repair Wizard** είναι ένα troubleshooting wizard για Termux που ελέγχει συνηθισμένα προβλήματα, προτείνει διορθώσεις και μπορεί να τρέξει ασφαλείς repair commands βήμα προς βήμα.

**Τοποθεσία Αποθήκευσης:** Οι scan φάκελοι δημιουργούνται στο τρέχον directory: scan_[target]_[date]

</details>

### • FaveSites.py

<details>
<summary><strong>🇬🇧 English</strong></summary>

**FaveSites.py** is a lightweight Termux bookmark manager that saves and organizes favorite websites for quick access.

**Save Location:** ~/FaveSites/ (auto-created if it does not exist)

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **FaveSites.py** είναι ένας lightweight Termux bookmark manager που αποθηκεύει και οργανώνει αγαπημένα websites για γρήγορη πρόσβαση.

**Τοποθεσία Αποθήκευσης:** ~/FaveSites/ (δημιουργείται αυτόματα αν δεν υπάρχει)

</details>


---

## 📁 No Category

### • Extra Content

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Extra Content** is an extra bonus-content hub that gives quick access to additional resources, templates, and optional add-ons included in the DedSec toolkit.

**Save Location:** Scan folders created in the current directory: scan_[target]_[date]

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Extra Content** είναι ένα extra bonus-content hub που δίνει γρήγορη πρόσβαση σε επιπλέον resources, templates και προαιρετικά add-ons που περιλαμβάνονται στο DedSec toolkit.

**Τοποθεσία Αποθήκευσης:** Οι scan φάκελοι δημιουργούνται στο τρέχον directory: scan_[target]_[date]

</details>

### • Settings

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Settings** is the central control hub for the DedSec ecosystem.

**Save Location:** Language config: ~/Language.json | Backups: ~/Termux.zip

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Settings** είναι ο κεντρικός κόμβος ελέγχου για το οικοσύστημα του DedSec.

**Τοποθεσία Αποθήκευσης:** Ρύθμιση γλώσσας: ~/Language.json | Backups: ~/Termux.zip

</details>


### • DedSec Market

<details>
<summary><strong>🇬🇧 English</strong></summary>

**DedSec Market** is a curses-based GitHub repository market for Termux that displays projects by project name instead of the raw repository name. It fetches README text cleanly, shows releases and issues, supports install, update, delete, and launch actions, keeps a watchlist, and stores cache/state for faster reuse.

**Save Location:** App data: `~/DedSec Market/` (`cache/`, `state.json`) | Installed repositories: `~/<repo-name>`

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **DedSec Market** είναι ένα curses-based GitHub repository market για Termux που εμφανίζει τα projects με το όνομα του project αντί για το ακατέργαστο όνομα του repository. Καθαρίζει και εμφανίζει σωστά το κείμενο των README, δείχνει releases και issues, υποστηρίζει ενέργειες install, update, delete και launch, κρατά watchlist και αποθηκεύει cache/state για πιο γρήγορη επαναχρησιμοποίηση.

**Τοποθεσία Αποθήκευσης:** Δεδομένα εφαρμογής: `~/DedSec Market/` (`cache/`, `state.json`) | Εγκατεστημένα repositories: `~/<repo-name>`

</details>

---

## 💜 Sponsors-Only

<details>
<summary><strong>🇬🇧 English</strong></summary>

To access the scripts in this category, you need an active monthly GitHub subscription starting from **$3**.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Για να αποκτήσεις πρόσβαση στα scripts αυτής της κατηγορίας, χρειάζεσαι ενεργή μηνιαία GitHub συνδρομή από **$3** και πάνω.

</details>

### • Face Detector.py

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Face Detector.py** is a local browser-based face analysis tool for Termux that works without root. It uses MediaPipe Face Mesh on the live camera feed, supports both front and back camera, tracks up to 3 faces, draws detailed facial landmark overlays instead of simple boxes, and now also lets you upload photos or videos for analysis directly from the interface. It can capture PNG snapshots, record WEBM video, save cropped detected faces separately, and provide both a local network link and an optional Cloudflare public link.

**Save Location:** On Termux, captures, recordings, uploaded results, and saved face crops are stored in `~/storage/downloads/Face Detector/`. If Termux storage is unavailable, it falls back to `~/Face Detector/`. On non-Termux systems it uses `~/Downloads/Face Detector/`, with fallback to `~/Face Detector/`. Internal web files, certificates, and helper binaries are stored in `~/.face_detector_studio/`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Face Detector.py** είναι ένα τοπικό browser-based εργαλείο ανάλυσης προσώπου για Termux που λειτουργεί χωρίς root. Χρησιμοποιεί MediaPipe Face Mesh στο live feed της κάμερας, υποστηρίζει μπροστινή και πίσω κάμερα, παρακολουθεί έως και 3 πρόσωπα, σχεδιάζει αναλυτικά facial landmark overlays αντί για απλά boxes και πλέον επιτρέπει επίσης upload φωτογραφιών ή βίντεο για ανάλυση απευθείας από το interface. Μπορεί να τραβά PNG snapshots, να γράφει WEBM βίντεο, να αποθηκεύει ξεχωριστά cropped detected faces και να παρέχει τόσο local network link όσο και προαιρετικό δημόσιο Cloudflare link.

**Τοποθεσία Αποθήκευσης:** Στο Termux, τα captures, recordings, uploaded results και τα αποθηκευμένα face crops μπαίνουν στο `~/storage/downloads/Face Detector/`. Αν το Termux storage δεν είναι διαθέσιμο, γίνεται fallback στο `~/Face Detector/`. Σε συστήματα εκτός Termux χρησιμοποιείται το `~/Downloads/Face Detector/`, με fallback στο `~/Face Detector/`. Τα internal web files, τα certificates και τα helper binaries αποθηκεύονται στο `~/.face_detector_studio/`.

</details>

### • Face Detector Heavy.py

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Face Detector Heavy.py** is the expanded heavy-analysis version of the face detector for Termux, built without root. In addition to live camera use, front/back camera switching, photo and video uploads, PNG snapshots, WEBM recording, and saved face crops, it raises face tracking up to 30 faces and adds TensorFlow COCO-SSD object detection on top of the MediaPipe face mesh pipeline. It overlays richer on-screen telemetry such as face count, animal/object detection, pose and gaze estimates, facial proportions, mouth and brow state, asymmetry scoring, and other visual analysis details, while still supporting a local network link and an optional Cloudflare public link.

**Save Location:** On Termux, captures, recordings, uploaded results, and saved face crops are stored in `~/storage/downloads/Face Detector/`. If Termux storage is unavailable, it falls back to `~/Face Detector/`. On non-Termux systems it uses `~/Downloads/Face Detector/`, with fallback to `~/Face Detector/`. Internal web files, certificates, and helper binaries are stored in `~/.face_detector_studio/`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Face Detector Heavy.py** είναι η πιο βαριά και επεκταμένη έκδοση ανάλυσης του face detector για Termux, χωρίς ανάγκη για root. Εκτός από live χρήση κάμερας, εναλλαγή μπροστινής/πίσω κάμερας, upload φωτογραφιών και βίντεο, PNG snapshots, WEBM recording και αποθήκευση face crops, ανεβάζει την παρακολούθηση έως και σε 30 πρόσωπα και προσθέτει TensorFlow COCO-SSD object detection πάνω στο pipeline του MediaPipe face mesh. Εμφανίζει πιο πλούσιο on-screen telemetry όπως face count, animal/object detection, εκτιμήσεις pose και gaze, facial proportions, κατάσταση στόματος και φρυδιών, asymmetry scoring και άλλα visual analysis στοιχεία, ενώ συνεχίζει να υποστηρίζει local network link και προαιρετικό δημόσιο Cloudflare link.

**Τοποθεσία Αποθήκευσης:** Στο Termux, τα captures, recordings, uploaded results και τα αποθηκευμένα face crops μπαίνουν στο `~/storage/downloads/Face Detector/`. Αν το Termux storage δεν είναι διαθέσιμο, γίνεται fallback στο `~/Face Detector/`. Σε συστήματα εκτός Termux χρησιμοποιείται το `~/Downloads/Face Detector/`, με fallback στο `~/Face Detector/`. Τα internal web files, τα certificates και τα helper binaries αποθηκεύονται στο `~/.face_detector_studio/`.

</details>

### • Steganography.py

<details>
<summary><strong>🇬🇧 English</strong></summary>

**Steganography.py** is a password-based steganography suite for Termux. It can generate random black-and-white PNG carrier images, encrypt secret text with a password-derived Fernet key, hide the encrypted text inside PNG images using LSB steganography, and batch-decode hidden messages from all images placed in the Decrypt folder. Extracted messages are automatically saved as separate `.txt` files, and the script can also optionally clean processed images from the decode folder after scanning.

**Save Location:** Main folder: `/storage/emulated/0/Download/Steganography/` | Carrier/output images: `/Encrypt` | Images to scan for hidden messages: `/Decrypt` | Extracted text files: `/Decrypted Texts`

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **Steganography.py** είναι μια password-based steganography suite για Termux. Μπορεί να δημιουργεί τυχαίες ασπρόμαυρες PNG εικόνες-φορείς, να κρυπτογραφεί μυστικό κείμενο με password-derived Fernet key, να κρύβει το κρυπτογραφημένο κείμενο μέσα σε PNG εικόνες με LSB steganography και να κάνει batch αποκωδικοποίηση κρυμμένων μηνυμάτων από όλες τις εικόνες που τοποθετούνται στον φάκελο Decrypt. Τα εξαγόμενα μηνύματα αποθηκεύονται αυτόματα ως ξεχωριστά `.txt` αρχεία και το script μπορεί προαιρετικά να καθαρίζει τις ήδη επεξεργασμένες εικόνες από τον φάκελο αποκωδικοποίησης μετά το scan.

**Τοποθεσία Αποθήκευσης:** Κύριος φάκελος: `/storage/emulated/0/Download/Steganography/` | Carrier/output εικόνες: `/Encrypt` | Εικόνες για έλεγχο κρυμμένων μηνυμάτων: `/Decrypt` | Εξαγόμενα αρχεία κειμένου: `/Decrypted Texts`

</details>


### • AR Terror.py

<details>
<summary><strong>🇬🇧 English</strong></summary>

**AR Terror.py** is a local browser-based AR horror experience for Termux that works without root. It launches a full-screen camera-driven web page where you explore the environment, collect hidden logs into an archive/inventory system, use atmospheric visual and audio effects, switch between front and back camera, and record evidence as WEBM while the experience runs. It can also expose both a local network link and an optional Cloudflare public link.

**Save Location:** On Termux, recorded evidence is saved in `~/storage/downloads/AR Terror/`. If Termux storage is unavailable, it falls back to `~/AR Terror/`. On non-Termux systems it uses `~/Downloads/AR Terror/`, with fallback to `~/AR Terror/`. Internal web files, certificates, and helper binaries are stored in `~/.ar_terror_studio/`.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **AR Terror.py** είναι μια τοπική browser-based AR horror εμπειρία για Termux που λειτουργεί χωρίς root. Εκκινεί μια full-screen camera-driven ιστοσελίδα όπου εξερευνάς το περιβάλλον, συλλέγεις κρυμμένα logs μέσα σε archive/inventory σύστημα, χρησιμοποιείς ατμοσφαιρικά visual και audio effects, αλλάζεις ανάμεσα σε μπροστινή και πίσω κάμερα και γράφεις evidence σε WEBM όσο τρέχει η εμπειρία. Μπορεί επίσης να παρέχει τόσο local network link όσο και προαιρετικό δημόσιο Cloudflare link.

**Τοποθεσία Αποθήκευσης:** Στο Termux, το recorded evidence αποθηκεύεται στο `~/storage/downloads/AR Terror/`. Αν το Termux storage δεν είναι διαθέσιμο, γίνεται fallback στο `~/AR Terror/`. Σε συστήματα εκτός Termux χρησιμοποιείται το `~/Downloads/AR Terror/`, με fallback στο `~/AR Terror/`. Τα internal web files, τα certificates και τα helper binaries αποθηκεύονται στο `~/.ar_terror_studio/`.

</details>

---

## 🦋 ButSystem.py (Exclusive)

<details>
<summary><strong>🇬🇧 English</strong></summary>

**ButSystem.py** is a self-hosted, **local-first** workspace that you run on your own device through Termux. It is built for private coordination and structured workflows, with clear screens, predictable controls, and an interface designed to keep work organized.

### What it includes

- authentication and access workflows
- login and signup flows
- optional 2FA and recovery actions
- direct messages with media and attachments
- groups with role-based controls
- call-related flows where supported
- file and vault navigation
- profile editing and account actions
- profiler, reports, and bounty-style workflow areas where enabled
- admin management screens
- security-focused settings

### How to use

1. Run **ButSystem.py** from your DedSec setup.
2. Open the generated local link in your browser.
3. Use the burger menu to switch between sections such as chats, groups, calls, files, profile, settings, and admin.
4. Configure **Settings → Security** before inviting other people.

### Reminder

Use only on systems you own or where you have explicit permission.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

Το **ButSystem.py** είναι ένα self-hosted, **local-first** workspace που το τρέχεις στη δική σου συσκευή μέσω Termux. Έχει σχεδιαστεί για private coordination και structured workflows, με καθαρές οθόνες, προβλέψιμα controls και interface φτιαγμένο ώστε να κρατά την εργασία οργανωμένη.

### Τι περιλαμβάνει

- authentication και access workflows
- login και signup flows
- προαιρετικό 2FA και recovery actions
- direct messages με media και attachments
- groups με role-based controls
- call-related flows όπου υποστηρίζονται
- file και vault navigation
- profile editing και account actions
- profiler, reports και bounty-style workflow areas όπου είναι ενεργά
- admin management screens
- settings με έμφαση στην ασφάλεια

### Πώς χρησιμοποιείται

1. Τρέξε το **ButSystem.py** μέσα από το DedSec setup σου.
2. Άνοιξε στο browser το local link που θα δημιουργηθεί.
3. Χρησιμοποίησε το burger menu για να αλλάζεις μεταξύ ενοτήτων όπως chats, groups, calls, files, profile, settings και admin.
4. Ρύθμισε το **Settings → Security** πριν καλέσεις άλλα άτομα.

### Υπενθύμιση

Να χρησιμοποιείται μόνο σε συστήματα που σου ανήκουν ή για τα οποία έχεις ρητή άδεια.

</details>

---

## 💬 Contact Us & Credits

<details>
<summary><strong>🇬🇧 English</strong></summary>

### Contact Us

For questions, support, or general inquiries, connect with the DedSec Project community through the official channels below:

* **Main Website:** [https://ded-sec.space](https://ded-sec.space)
* **Main DedSec Project Repository:** [https://github.com/dedsec1121fk/DedSec](https://github.com/dedsec1121fk/DedSec)
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

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

### Επικοινωνία

Για ερωτήσεις, υποστήριξη ή γενικές πληροφορίες, μπορείς να συνδεθείς με το DedSec Project μέσα από τα παρακάτω επίσημα κανάλια:

* **Κύριο Website:** [https://ded-sec.space](https://ded-sec.space)
* **Κύριο Repository του DedSec Project:** [https://github.com/dedsec1121fk/DedSec](https://github.com/dedsec1121fk/DedSec)
* **Εφεδρικό Website:** [https://ded-sec.online](https://ded-sec.online)
* **Εφεδρικό Repository του DedSec Project:** [https://github.com/sal-scar/DedSec](https://github.com/sal-scar/DedSec)
* **📱 WhatsApp:** [+37257263676](https://wa.me/37257263676)
* **📸 Instagram:** [@dedsec_project_official](https://www.instagram.com/dedsec_project_official)
* **✈️ Telegram:** [@dedsecproject](https://t.me/dedsecproject)
* **💬 Discord Server:** [https://discord.gg/fcAuYS4JEv](https://discord.gg/fcAuYS4JEv)

### Συντελεστές

* **Creator:** dedsec1121fk
* **Contributors:** gr3ysec, Sal Scar
* **Art Artists:** Christina Chatzidimitriou
* **Testers:** Javier
* **Legal Documents:** Lampros Spyrou
* **Discord Server Maintenance:** Talha
* **Past Help:** lamprouil, UKI_hunter

</details>

---

## ⚠️ Disclaimer & Terms of Use

<details>
<summary><strong>🇬🇧 English</strong></summary>

> **PLEASE READ CAREFULLY BEFORE PROCEEDING.**

This project, including all associated tools, scripts, and documentation, is provided strictly for **educational, research, and ethical security testing purposes**. It is intended for use only in controlled, authorized environments by users who have obtained explicit permission from the owners of any systems they test.

1. **Assumption of Risk and Responsibility:** You are solely responsible for your actions and for any consequences that may arise from using or misusing this software.
2. **Prohibited Activities:** Unauthorized or malicious activity is strictly prohibited.
3. **No Warranty:** The software is provided **AS IS** without guarantees.
4. **Limitation of Liability:** The developers, contributors, and distributors are not liable for claims, damages, or losses arising from the software or its use.

</details>

<details>
<summary><strong>🇬🇷 Ελληνικά</strong></summary>

> **ΠΑΡΑΚΑΛΩ ΔΙΑΒΑΣΕ ΠΡΟΣΕΚΤΙΚΑ ΠΡΙΝ ΣΥΝΕΧΙΣΕΙΣ.**

Αυτό το project, μαζί με όλα τα σχετικά εργαλεία, scripts και έγγραφα, παρέχεται αυστηρά για **εκπαιδευτικούς, ερευνητικούς και ethical security testing σκοπούς**. Προορίζεται να χρησιμοποιείται μόνο σε ελεγχόμενα και εξουσιοδοτημένα περιβάλλοντα από χρήστες που έχουν λάβει ρητή άδεια από τους ιδιοκτήτες των συστημάτων που δοκιμάζουν.

1. **Ανάληψη Κινδύνου και Ευθύνης:** Είσαι αποκλειστικά υπεύθυνος για τις πράξεις σου και για οποιεσδήποτε συνέπειες μπορεί να προκύψουν από τη χρήση ή την κακή χρήση αυτού του λογισμικού.
2. **Απαγορευμένες Δραστηριότητες:** Οποιαδήποτε μη εξουσιοδοτημένη ή κακόβουλη δραστηριότητα απαγορεύεται αυστηρά.
3. **Καμία Εγγύηση:** Το λογισμικό παρέχεται **ΩΣ ΕΧΕΙ** χωρίς εγγυήσεις.
4. **Περιορισμός Ευθύνης:** Οι δημιουργοί, οι contributors και οι διανομείς δεν φέρουν ευθύνη για απαιτήσεις, ζημιές ή απώλειες που προκύπτουν από το λογισμικό ή τη χρήση του.

</details>
