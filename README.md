# DedSec Project

[https://www.ded-sec.space](https://www.ded-sec.space)  
Εκεί θα βρείτε και Ελληνική μετάφραση.

[https://t.me/dedsecproject](https://t.me/dedsecproject)

> **A standalone DedSec Project application will be soon available with even more features. Stay tuned for updates and release info.**

-----

## Project Overview

The DedSec Project is a free, community-driven initiative inspired by the underground resistance and cyber-revolution themes of Ubisoft’s *Watch Dogs* series. Just like the in-game DedSec, our project empowers everyday users with tools for digital freedom, security, and awareness.

We provide hacking-style utilities, phishing tools, secure communication platforms, and system customization options—**all without charging a cent**.

> **Why use it?** Because everyone deserves access to knowledge, privacy, and control over their digital life.

-----

## Secure Use Disclaimer

This project is provided solely for educational purposes. Any unauthorized use or attempts to bypass security controls are strictly prohibited. By downloading or using this project, you agree to take full responsibility for all actions performed with it. You must comply with all applicable laws and security policies. The creator of this project is not liable for any direct, indirect, or consequential damages or legal actions arising from unauthorized or unsafe use.

-----

## Installation & Setup

### Requirements

  - **Device:** Android with [Termux](https://f-droid.org/) installed.  
  - **Storage:** Minimum **3GB** free. (*Radio and media content consume additional space.*)  
  - **RAM:** Minimum **2GB**.

### Step-by-Step Installation

1.  **Install Termux & Add-Ons**

    *Note:* To install APKs (e.g., F-Droid), ensure:

      - **Unknown sources** enabled (Settings > Security > Install Unknown Apps).  
      - Download F-Droid and install Termux from it.  
      - Add-ons: Termux:API, Termux:Styling.  
      - Allow the `fdeokd` process when prompted.

2.  **Run Setup Commands**

    ```bash
    termux-setup-storage && pkg update -y && pkg upgrade -y && pkg install python git fzf nodejs openssh nano jq wget unzip curl proot openssl aapt rust cloudflared
    ```

    ```bash
    pip install flask blessed flask-socketio werkzeug requests datetime geopy pydub pycryptodome mutagen rust cryptography phonenumbers pycountry
    ```

    ```bash
    pkg install termux-api
    ```

3.  **Clone the Repository**

    ```bash
    git clone https://github.com/dedsec1121fk/DedSec
    ```

    *Tip:* If you see `ModuleNotFoundError: No module named 'requests'`, run:

    ```bash
    pip install requests
    ```

4.  **Choose Menu Style**

    ```bash
    cd DedSec/Scripts && python Settings.py
    ```

    *Tip:* Reopen the menu later by typing `m` in Termux.

-----

## Scripts & Functionalities

  - **Fox Chat:** Encrypted chat with file exchange, voice & video calls. No saved nicknames or passwords.  
  - **Android App Launcher:** Browse and manage installed Android apps.  
  - **Radio:** Offline radio featuring Greek and international artists.  
  - **Phishing Attacks:** Tools to capture camera images, audio, location, and personal/card data. Saved in `~/storage/downloads/`:  
      - `Card Details.py` → `CardActivations/`  
      - `Data Grabber.py` → `People's Lives/{user}/`  
      - `Login Page Back Camera.py` → `Camera-Phish-Back/`  
      - `Login Page Front Camera.py` → `Camera-Phish-Front/`  
      - `Login Page Location.py` → `LocationData/`  
      - `Login Page Microphone.py` → `Recordings/`  
      - **FaceFriends.py**: Simulates a Facebook-like login page. → `FaceFriends/`  
      - **Google Free Money.py**: Mimics a Google reward claim page. → `GoogleFreeMoney/`  
      - **Insta Followers.py**: Fake Instagram followers generator page. → `FreeFollowers/`  
      - **Snap Friends.py**: Snapchat-themed friend connection page. → `SnapFriends/`  
      - **Tik Followers.py**: Fake TikTok followers page. → `TikFollowers/`  
  - **Settings:** Update, manage packages, change username/menu, view credits.  
  - **DedSec Database:** Upload, search, and delete files via local server. Hidden folder storage.  
  - **HTML Finder:** A utility to inspect, download, and locally edit any public webpage.  
      - Downloads main HTML and assets (CSS, JS, images, icons, media).  
      - Saves files in: `~/storage/downloads/<website_name>/index.html`  
      - Subfolders: `css/`, `js/`, `images/`, etc.  
      - Supports editing with `nano`, `vim`, etc.  
      - Optional browser preview with `termux-open-url`.  
  - **Extra Content:** Includes photos, unused scripts, voice overs, and more.

-----

## Legal & Ethical Notice

  - **Educational & Research Use:** Authorized, ethical testing in controlled environments only.  
  - **Prohibited Uses:** Unauthorized access, data breaches, identity theft, fraud.  
  - **User Responsibility:** Always obtain permission before testing.  
  - **Liability Disclaimer:** Authors are not liable for misuse.  
  - **Ethical Standards:** Follow guidelines. Respect privacy.  
  - **Legal Compliance:** Follow all laws. Seek legal advice if needed.

-----

## Welcome to the resistance.

-----

## Credits

**Creator:** dedsec1121fk  
**Music Artists:** BFR TEAM, PLANNO MAN, KouNouPi, ADDICTED, JAVASPA.ZY.A2.N, ICE, Lefka City, HXLX, Giannis Vardis, Lavyrinthos, Komis X, GR$, Sugar Boy, Sakin, XALILOP1, Family Lockations, Dafne Kritharas, NANCIIE, Grave\_North  
**Art Artist:** Christina Chatzidimitriou  
**Voice Overs:** Dimitra Isxuropoulou  
**Technical Help:** lamprouil, UKI\_hunter  

-----

© 2025 DedSec Project. All rights reserved.
