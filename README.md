> **A standalone DedSec Project application will be available soon with even more features. Stay tuned for updates and release info.**


![Custom Purple Fox Logo](https://github.com/dedsec1121fk/DedSec/blob/f5fabcbd129e7cc233a728f78299a4db5abd00fb/Extra%20Content/Images/Custom%20Purple%20Fox%20Logo.png?raw=true)

# DedSec Project

[![Visit ded-sec.space](https://img.shields.io/badge/🌐%20Website-ded--sec.space-007EC6?style=for-the-badge)](https://www.ded-sec.space)
[![Become a Patron](https://img.shields.io/badge/Patreon-Become%20a%20Patron-orange?logo=patreon)](https://www.patreon.com/c/dedsec1121fk/membership?redirect=true)
[![Instagram](https://img.shields.io/badge/Instagram-Follow%20Me-purple?logo=instagram)](https://www.instagram.com/username112104?igsh=MnR2eTdxaTN5ZHZi)

**Secure Use Disclaimer:**
This project is provided solely for educational purposes. Any unauthorized use or attempts to bypass security controls are strictly prohibited. By downloading or using this project, you agree to take full responsibility for all actions performed with it. You are required to use the project in full compliance with all applicable laws and security policies. The creator of this project is not liable for any direct, indirect, or consequential damages or legal actions arising from unauthorized or unsafe use. Always follow best security practices and organizational guidelines when handling this project.

---

## Installation & Setup

- Ελληνική Μετάφραση των οδηγιών μπορεί να βρεθεί στην ιστοσελίδα μου για το [DedSec Project.](https://www.ded-sec.space)

### Requirements
- **Device:** Android device with [Termux](https://f-droid.org/) installed.

- **Storage:** Minimum **3GB** of free space.(Keep in mind that Radio takes much more storage if you choose to download it from the menu, and also remember that any taken images and recordings also consume storage.)
- **RAM:** Minimum **2GB**.

### Step-by-Step Installation

1.  **Install Termux and Add-Ons**

**Note:** To install APKs (like F-Droid), ensure the following:
- you’ve enabled app installations from unknown sources (Settings > Security > **Install Unknown Apps**).
   - Download F-Droid and from there download Termux from [F-Droid](https://f-droid.org/).
   - Install required add-ons: Termux:API, Termux:Styling.

**Note:** To install APKs (like F-Droid), ensure the following:
- you’ve enabled app installations from unknown sources (Settings > Security > **Install Unknown Apps**).
- You allow the `fdeokd` process to proceed when prompted.


2.  **Run Setup Commands**

    First, open your Termux terminal and run the following command to set up storage, update packages, and install the required tools:

    ```bash
    termux-setup-storage && pkg update -y && pkg upgrade -y && pkg install python git fzf nodejs openssh nano jq wget unzip curl proot openssl aapt rust cloudflared
    ```

    Then, install the necessary Python dependencies:

    ```bash
    pip install flask blessed flask-socketio werkzeug requests datetime geopy pydub pycryptodome mutagen rust cryptography phonenumbers pycountry
    ```
    
    Then, install Termux:API:
    ```bash
     pkg install termux-api
    ```

3.  **Clone the Repository**
    ```bash
    git clone [https://github.com/dedsec1121fk/DedSec](https://github.com/dedsec1121fk/DedSec)
    ```

4.  **Choose Menu Style**
    ```bash
    cd DedSec/Scripts && python Settings.py
    ```
    > **Tip:** You can always open the menu later by typing `m` in your Termux terminal.

---

## Scripts & Their Functionalities

Below is a summary of each script provided in the DedSec toolkit:

1.  **Fox Chat** - Lets you talk with encrypted chat with other people with the same link, no nicknames are saved, no password needs, also it lets you exchange files, voice messages and video calls.

2.  **Android App Launcher** - Displays all your downloaded Android apps and lets you launch, delete, or view information about them.

3.  **Radio** - A full offline radio with Greek and not only artists.

4.  **Phishing Attacks** - Lets you take images from front or back camera, record sound, find the exact location (with address and a nearby store if available) from a person. Also it lets you take card credentials, Personal Info etc. Everything is saved in folders in internal storage Downloads folder.
    * **Card Details.py**: Saves captured credit card information into the `~/storage/downloads/CardActivations/` directory.
    * **Data Grabber.py**: Creates a user-specific folder inside `~/storage/downloads/People's Lives/` where it saves submitted personal information and a photo.
    * **Login Page Back Camera.py**: Stores captured images and credentials in the `~/storage/downloads/Camera-Phish-Back/` directory.
    * **Login Page Front Camera.py**: Saves photos taken with the front camera and any submitted credentials to the `~/storage/downloads/Camera-Phish-Front/` directory.
    * **Login Page Location.py**: Saves location data and credentials to the `~/storage/downloads/LocationData/` directory.
    * **Login Page Microphone.py**: Stores microphone recordings and submitted credentials in the `~/storage/downloads/Recordings/` directory.

5.  **Settings** - Lets you update the project, install or update the required packages and modules, change the prompt username, change the menu style and view the credits of the project creators.

6.  **DedSec Database** - Lets you upload, search, and delete files. The device that starts the program acts as the server and saves the files in a hidden folder.

7.  **Extra Content** - Contains photos, unused scripts, unused voice overs and more.

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
