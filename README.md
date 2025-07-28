
![Custom Purple Fox Logo](https://github.com/dedsec1121fk/DedSec/blob/f5fabcbd129e7cc233a728f78299a4db5abd00fb/Extra%20Content/Images/Custom%20Purple%20Fox%20Logo.png?raw=true)

# DedSec Project

[![🌐 Visit Website](https://img.shields.io/badge/Website-ded--sec.space-blue?style=for-the-badge)](https://www.ded-sec.space)  
> Ελληνική μετάφραση υπάρχει στην παραπάνω σελίδα.
[![Contact Us On Telegram](https://img.shields.io/badge/Telegram-Contact%20Us-blue?style=for-the-badge&logo=telegram)](https://t.me/dedsecproject)

> **A standalone DedSec Project application will be soon available with even more features. Stay tuned for updates and release info.**

---

## About The DedSec Project

The DedSec Project is a free, community-driven initiative inspired by the cyber-resistance themes of Ubisoft’s Watch Dogs series. Our mission is to empower users with tools and knowledge for digital freedom, security, and privacy awareness. We provide a suite of utilities for ethical security testing, secure communication, and system customization, all available at no cost.

Why use it? Because everyone deserves access to knowledge, privacy, and control over their digital life. We're not here for profit—we're here to give power back to the people. Whether you're a tech enthusiast, digital activist, or just someone curious about cybersecurity, the DedSec Project invites you to be part of the movement.

Welcome to the resistance.

---

## Disclaimer

**For Educational Use Only:**  
This project is intended for educational and research purposes only. It should be used exclusively in controlled, authorized environments for security testing and learning. Any use of these tools for unauthorized activities, including but not limited to accessing systems you do not own or have explicit permission to test, is strictly prohibited. By using this software, you assume full responsibility for your actions and agree to comply with all applicable local, state, and federal laws. The developers and contributors are not liable for any damage, misuse, or legal consequences resulting from your use of this project. Use ethically and responsibly.

---

## Installation & Setup

### Requirements

- **Device:** Android with [Termux](https://f-droid.org/) installed.
- **Storage:** Min **3GB** free. _(Radio takes more storage; images/recordings also consume space.)_
- **RAM:** Min **2GB**

### Step-by-Step Installation

1. **Install Termux & Add-Ons**  
_Note:_ To install APKs (e.g., F-Droid), ensure:  
- Enabled unknown sources (Settings > Security > **Install Unknown Apps**)  
- Download F-Droid, get Termux from [F-Droid](https://f-droid.org)  
- Install add-ons: Termux:API, Termux:Styling  
- Allow `fdroid` process when prompted

2. **Run Setup Commands**
```bash
termux-setup-storage && pkg update -y && pkg upgrade -y && pkg install python git fzf nodejs openssh nano jq wget unzip curl proot openssl aapt rust cloudflared
```

```bash
pip install flask blessed flask-socketio werkzeug requests datetime geopy pydub pycryptodome mutagen rust cryptography phonenumbers pycountry
```

```bash
pkg install termux-api
```

3. **Clone Repository**
```bash
git clone https://github.com/dedsec1121fk/DedSec
```

_Tip:_ If you get this error  
`ModuleNotFoundError: No module named 'requests'`  
run:  
```bash
pip install requests
```

4. **Choose Menu Style**
```bash
cd DedSec/Scripts && python Settings.py
```

_Tip:_ Open menu later by typing `m` in Termux

---

## Scripts & Their Functionalities

Summary of each script in the DedSec toolkit:

- **Fox Chat**  
Encrypted chat, file/voice/video calls. No saved nicks/passwords.

- **Android App Launcher**  
Displays and manages downloaded Android apps.

- **Radio**  
Offline radio (Greek/int'l artists).

- **Phishing Attacks**  
Capture camera images, audio, exact location (address/store). Get card/personal info. All saved in Downloads.
  - `Card Details.py` → `~/storage/downloads/CardActivations/`
  - `Data Grabber.py` → `~/storage/downloads/People's Lives/{user}/`
  - `FaceFriends.py` → `~/storage/downloads/FaceFriends/`
  - `Google Free Money.py` → `~/storage/downloads/GoogleFreeMoney/`
  - `Insta Followers.py` → `~/storage/downloads/FreeFollowers/`
  - `Login Page Back Camera.py` → `~/storage/downloads/Camera-Phish-Back/`
  - `Login Page Front Camera.py` → `~/storage/downloads/Camera-Phish-Front/`
  - `Login Page Location.py` → `~/storage/downloads/LocationData/`
  - `Login Page Microphone.py` → `~/storage/downloads/Recordings/`
  - `Snap Friends.py` → `~/storage/downloads/SnapFriends/`
  - `Tik Followers.py` → `~/storage/downloads/TikFollowers/`

- **Settings**  
Update project, install/update packages/modules, change username/menu style, view credits.

- **DedSec Database**  
Upload, search, delete files. Device is server, files saved in hidden folder.

- **HTML Finder**  
A utility to inspect, download, and locally edit any public webpage. It automatically downloads the main HTML file and its assets (CSS, JS, images, icons, media), saves them in a local folder, and opens the page in a terminal editor.  
Files are stored under:  
`~/storage/downloads/<website_name>/index.html`  
Assets: `css/`, `js/`, `images/`, etc.  
Supports editing via `nano`, `vim`, or any CLI editor.  
Optional browser preview with `termux-open-url`.

-   **URL Masker (`Masker.py`)** A tool to conceal and shorten URLs. It first attempts to use the `is.gd` service to create a link with a randomly generated, human-readable alias (e.g., `VerifyAccount42`). If this fails, it automatically falls back to `cleanuri.com` to generate a standard shortened URL.

-   **SocialBrute (`SocialBrute.py`)** An advanced multi-service brute-force tool for social media platforms including Facebook, Instagram, LinkedIn, Reddit, VK, and others. It features multi-threading, proxy rotation (with Tor support), realistic user agents, and exponential backoff to evade detection. The tool can resume interrupted sessions and uses the `rockyou.txt` wordlist by default. Any successfully discovered credentials are saved in an encrypted format under `~/storage/downloads/SocialBrute/`.

- **Extra Content**  
Photos, unused scripts, voice overs, more.

---

## Legal & Ethical Notice

The tools and scripts within the DedSec Project are provided for educational, research, and ethical security testing purposes. Users are expected to adhere to the highest ethical standards, including respecting privacy and obtaining explicit, written authorization before testing any system or network. Unauthorized activities such as attempting to breach systems without consent, data theft, fraud, or any form of malicious attack are illegal and strictly forbidden. The user bears all responsibility for complying with applicable laws, including those governing cybersecurity and data privacy. The authors disclaim all liability for any direct or indirect damages that may result from the use or misuse of this software. If you are uncertain about the legality of your intended actions, consult a qualified legal professional.

---

## Donate With Crypto POL (Polygon)

```
0x8a88c8bCCc1cCD1bB02622465EA9051051eB06Ff
```

---

## Credits

**Creator:** dedsec1121fk  
**Music Artists:** BFR TEAM, PLANNO MAN, KouNouPi, ADDICTED, JAVASPA.ZY.A2.N, ICE, Lefka City, HXLX, Giannis Vardis, Lavyrinthos, Komis X, GR$, Sakin, XALILOP1, Family Lockations, Dafne Kritharas, NANCIIE, Grave_North, YungKapa, Aroy, Pi Thita,Ecostones Band,Bossikan,B-Mat,Stamatis Kapiris  
**Art Artist:** Christina Chatzidimitriou  
**Voice Overs:** Dimitra Isxuropoulou  
**Technical Help:** lamprouil, UKI_hunter, kostas_xrs._21.7

---

© 2025 DedSec Project. All rights reserved.
