# DedSec Project

![Custom Purple Fox Logo](https://github.com/dedsec1121fk/DedSec/blob/f5fabcbd129e7cc233a728f78299a4db5abd00fb/Extra%20Content/Images/Custom%20Purple%20Fox%20Logo.png?raw=true)

[![Visit ded-sec.space](https://img.shields.io/badge/🌐%20Website-ded--sec.space-007EC6?style=for-the-badge)](https://www.ded-sec.space)
[![Become a Patron](https://img.shields.io/badge/Patreon-Become%20a%20Patron-orange?logo=patreon)](https://www.patreon.com/c/dedsec1121fk/membership?redirect=true)

## Overview

DedSec is a comprehensive toolkit designed for ethical security testing, research, and learning purposes. It comes with a wide variety of tools and features, ranging from encrypted communication to phishing simulation scripts. This project is intended solely for educational purposes and adheres to ethical hacking guidelines.

---

## Secure Use Disclaimer

This project is provided solely for educational purposes. Any unauthorized use or attempts to bypass security controls are strictly prohibited. By downloading or using this project, you agree to take full responsibility for all actions performed with it. You are required to use the project in full compliance with all applicable laws and security policies. The creator of this project is not liable for any direct, indirect, or consequential damages or legal actions arising from unauthorized or unsafe use. Always follow best security practices and organizational guidelines when handling this project.

---

## Features

- **Encrypted Communication:** Securely talk, exchange files, send voice messages, and make video calls, with no nicknames or passwords required.
- **App Management:** Launch, delete, or view information about Android apps.
- **Offline Radio:** Includes a collection of Greek and international artists.
- **Phishing Simulation:** Simulates phishing attacks for educational purposes, including capturing images, audio, location, and more.
- **Tools Suite:** Update the project, manage files, encrypt or decrypt text, and generate public links.
- **Extra Content:** A variety of additional resources, including unused scripts, photos, and more.

---

## Installation & Setup

### Requirements

- **Device:** Android device with [Termux](https://f-droid.org/) installed.
- **Storage:** Minimum **3GB** of free space.
- **RAM:** Minimum **2GB**.

 **Step-by-Step Installation**
 
1. **Install Termux and Add-Ons**
   - Download Termux from [F-Droid](https://f-droid.org/).
   - Install required add-ons: Termux:API, Termux:Styling.

2. **Setup Commands**
   - Open Termux and run:
     ```bash
     termux-setup-storage && pkg update -y && pkg upgrade -y && pkg install python git fzf nodejs openssh nano jq wget unzip curl proot openssl aapt rust cloudflared
     ```
   - Install Python dependencies:
     ```bash
     pip install flask blessed flask-socketio werkzeug requests datetime geopy pydub pycryptodome mutagen rust cryptography phonenumbers pycountry
     ```
   - Install Termux:API:
     ```bash
     pkg install termux-api
     ```

 3. **Clone the Repository**
   ```bash
   git clone https://github.com/dedsec1121fk/DedSec
```
 4.**Choose Menu Style**
```
   cd DedSec/Scripts && python Settings.py
```
> **Tip:** Open the menu later by typing `m` in Termux.


## Scripts & Functionalities

### Communication
- Encrypted chat, file exchange, voice messages, and video calls.

### Android App Launcher
- Manage downloaded Android apps (launch, delete, or view information).

### Offline Radio
- Access music offline, featuring Greek and international artists.

### Phishing Attacks
- Capture images, sound, location, card credentials, and personal info. All data is saved in organized folders.

### Tools
- Update the project, manage files, encrypt text, generate public links, and more.

### Extra Content
- Unused scripts, photos, and voiceovers.

---

## Data Storage Paths

### Phishing Scripts Background Images
- Various phishing scripts use images like `camera.jpg`, `locate.jpg`, and `casino.jpg` stored in directories under `~/storage/downloads/`.

### User Data
- **Card details:** `~/storage/downloads/CardActivations`
- **Location data:** `~/storage/downloads/LocationData`
- **Audio recordings:** `~/storage/downloads/Recordings`
- **Personal data:** `~/storage/downloads/People's Lives` (organized in user-specific folders).

---

## Legal & Ethical Notice

### Educational & Research Use
This toolkit is provided exclusively for educational, research, and ethical security testing purposes in controlled environments. All tools are intended solely for learning and should only be used on systems where you have explicit authorization.

### Prohibited Uses
- Unauthorized use, data breaches, identity theft, or fraud are strictly prohibited.

### User Responsibility
- Ensure compliance with applicable laws and obtain explicit permission before conducting security tests.

### Liability Disclaimer
- The authors disclaim all liability for damages arising from misuse.

### Ethical Standards
- Adhere to ethical hacking guidelines and respect privacy.

### Export/Import Controls
- Comply with export and import control laws.

### Consult Legal Counsel
- If in doubt, consult a qualified legal professional.

---

## Frequently Asked Questions (FAQs)

### Can I run this toolkit on a rooted device?
- No root is required to use this toolkit.

### What happens if I don't have enough storage?
- Ensure minimum **3GB** of free space is available. Larger storage is needed for functionalities like offline radio.

### Is this toolkit safe to use?
- Yes, if used responsibly and within the boundaries of ethical hacking practices.

---

## Contribution Guidelines

We welcome contributions to improve DedSec! Follow these steps to contribute:

1. Fork the repository.
2. Create a new branch for your changes.
3. Submit a pull request with a description of your changes.

---

## Support & Resources

- **Website:** [ded-sec.space](https://www.ded-sec.space)
- **Patreon:** [Support us](https://www.patreon.com/c/dedsec1121fk/membership?redirect=true)
