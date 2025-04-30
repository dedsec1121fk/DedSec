[DedSec Logo](Extra Content/Images/Custom Purple Fox Logo.png)

# DedSec Project

[![Website](https://img.shields.io/badge/🌐%20Website-ded--sec.space-007EC6?style=for-the-badge)](https://www.ded-sec.space)  
[![Instagram](https://img.shields.io/badge/Instagram-@loukas__floros-E4405F?style=for-the-badge)](https://www.instagram.com/loukas_floros)  
[![Patreon](https://img.shields.io/badge/Become%20a%20Patron-Patreon-FF424D?style=for-the-badge)](https://www.patreon.com/c/dedsec1121fk/membership?redirect=true)

> **DedSec Project** is your all-in-one educational security & productivity toolkit—packed with Python demos, utilities, phishing-attack frameworks, and fun extras.

---

## 📖 Table of Contents

1. [About](#-about)  
2. [Features](#-features)  
3. [Prerequisites & Dependencies](#-prerequisites--dependencies)  
4. [Installation](#-installation)  
5. [Usage](#-usage)  
   - [Core Scripts](#core-scripts)  
   - [Phishing-Attack Demos](#phishing-attack-demos)  
   - [Android App Launcher](#android-app-launcher)  
   - [Extras & Unused Scripts](#extras--unused-scripts)  
6. [Folder Structure](#-folder-structure)  
7. [Stickers & Media](#-stickers--media)  
8. [Secure-Use & Ethics](#-secure-use--ethics)  
9. [License](#-license)  
10. [Contributing](#-contributing)  
11. [Contacts & Support](#-contacts--support)

---

## 🤔 About

DedSec Project is a curated collection of Python-based demos and utilities designed **solely for educational purposes**.  
Learn how phishing pages harvest data, simulate radio scanning, perform text encryption, launch Android apps programmatically, and explore toy scripts—all within one repository.

---

## ✨ Features

- **Phishing-Attack Demos**  
  - Location, Microphone, Camera (Front/Back) spoofing pages  
  - Credit-card details grabber  
  - Login-page clones for credentials capture  
  - Dynamic country-code Data Grabber (stores submissions with timestamps)

- **Encryption Utility**  
  - Full-screen curses interface  
  - AES-256 text encryptor & decryptor with PBKDF2 key derivation  

- **Radio Scanner Demo**  
  - Simulated FM/AM streams via command-line  
  - Auto-installs `requests` & `wcwidth`  

- **Android App Launcher**  
  - Enumerate installed APKs via adb shell  
  - Launch any package by name  

- **Extras & Unused Scripts**  
  - Blank-page demos for Location, Microphone, Front/Back Camera (Flask + geopy)  
  - Chatbot experiments (`DedSec's_Chat.py`, `Fox_Chat.py`)  

- **PNG Stickers & Media**  
  - Remixable assets for slides, demos, TikToks  

---

## ⚙️ Prerequisites & Dependencies

- **Python** 3.8+  
- **Pip** (for installing required packages)

Required Python packages (auto-installed by scripts or via `pip install`):

```text
Flask
requests
wcwidth
pycryptodome
pycountry
phonenumbers
geopy
Werkzeug
```

Optional system tools:

- **Android Debug Bridge (adb)** — for Android App Launcher  
- **Git** — for Radio demo auto-clone/update  

---

## 🚀 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/dedsec1121fk/DedSec.git
   cd DedSec
   ```

2. **(Recommended) Create & activate a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate    # Linux/macOS
   venv\Scripts\activate       # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install Flask requests wcwidth pycryptodome pycountry phonenumbers geopy
   ```

---

## 🏃 Usage

### Core Scripts

All “core” demos live in `Scripts/`. Run any with:

```bash
cd Scripts
python "Script Name.py"
```

| Script                            | Description                                                |
|-----------------------------------|------------------------------------------------------------|
| `Text Encryptor And Decryptor.py` | Full-screen AES-256 text encryptor/decryptor (curses UI)   |
| `Radio.py`                        | Simulated FM/AM radio scanner (auto-installs deps)         |
| `Android App Launcher.py`         | List & launch Android apps via ADB                         |
| `Extra Content.py`                | Miscellaneous demos & test routines                        |

### Phishing-Attack Demos

Located in `Scripts/Phishing Attacks/`:

```bash
cd "Scripts/Phishing Attacks"
```

| Script                             | Function                                                       |
|------------------------------------|----------------------------------------------------------------|
| `DedSlot Location.py`              | Spoof location-request page & log coords with timestamp        |
| `DedSlot Microphone.py`            | Front/mic capture demo                                          |
| `DedSlot Front Camera.py`          | Photo capture via front camera                                  |
| `Card Details.py`                  | Credit-card form & secure save to `~/storage/downloads/Peoples_Lives` |
| `Login Page Location.py`           | Clone login page + geolocation grabber                          |
| `Login Page Microphone.py`         | Clone login page + mic permission grab                          |
| `Login Page Back Camera.py`        | Clone login page + back-camera capture                          |
| `Login Page Front Camera.py`       | Clone login page + front-camera capture                         |
| `Data Grabber.py`                  | Advanced form: dynamic country codes, phone parsing, file upload |

Each demo launches a Flask server at `http://127.0.0.1:5000`. Open your browser to interact and watch the console/output folder for saved data.

### Android App Launcher

```bash
cd Scripts
python "Android App Launcher.py"
```

- Requires `adb` in your PATH  
- Lists all installed APK packages and lets you choose one to launch  

### Extras & Unused Scripts

Find toy/demo scripts in `Extra Content/Unused Scripts/`:

- **Chatbots:** `DedSec's_Chat.py`, `Fox_Chat.py`  
- **Blank-page Demos:**  
  - `Blank_Page_Location.py`  
  - `Blank_Page_Microphone.py`  
  - `Blank_Page_Front_Camera.py`  
  - `Blank_Page_Back_Camera.py`  

Each is a basic Flask stub that logs incoming data (geopy used for reverse geocoding in location demo).

---

## 📂 Folder Structure

```
DedSec/
├── Extra Content/
│   ├── Images/…                 # Logo, graphics
│   ├── Stickers/                # PNG sticker assets
│   └── Unused Scripts/          # Toy/demo code
├── Scripts/
│   ├── Android App Launcher.py
│   ├── Radio.py
│   ├── Text Encryptor And Decryptor.py
│   ├── Extra Content.py
│   └── Phishing Attacks/
│       ├── Card Details.py
│       ├── Data Grabber.py
│       ├── DedSlot Location.py
│       ├── DedSlot Microphone.py
│       ├── DedSlot Front Camera.py
│       ├── Login Page Location.py
│       ├── Login Page Microphone.py
│       ├── Login Page Back Camera.py
│       └── Login Page Front Camera.py
├── LICENSE.txt
└── README.md
```

---

## 🖼️ Stickers & Media

Browse and remix **PNG stickers** in `Extra Content/Stickers/` for your presentations, social-media posts, or demo slides.

---

## 🔒 Secure-Use & Ethics

> **Educational Use Only.** You **must** obtain explicit permission before deploying or testing any component against real systems.

- **User Responsibility:** You agree to use these tools lawfully and ethically.  
- **Disclaimer:** Authors bear no liability for misuse.  
- **Privacy & Legal:** Comply with local laws, GDPR, and organizational policies.  
- **Export Controls:** Verify export/import regulations in your jurisdiction.  
- **Legal Advice:** When in doubt, consult a qualified attorney.

---

## 📜 License

**DedSec – Proprietary License**  
© 2025 dedsec1121fk. All rights reserved.

- Personal & non-commercial use only.  
- No modification, distribution, or reverse-engineering.  
- See [`LICENSE.txt`](LICENSE.txt) for full terms.

---

## 🤝 Contributing

*Contributions are currently closed.*  
Feature requests or discussion via Instagram DM or Patreon only.

---

## 📬 Contacts & Support

- 🌐 Website: [ded-sec.space](https://www.ded-sec.space)  
- 📷 Instagram: [@loukas_floros](https://www.instagram.com/loukas_floros)  
- 💖 Patreon: [Become a Patron](https://www.patreon.com/c/dedsec1121fk/membership?redirect=true)  

---

> “Knowledge is power, but only if shared responsibly.” – DedSec Team  
```