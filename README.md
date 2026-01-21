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

* [How To Install And Setup The DedSec Project](#🚀-how-to-install-and-setup-the-dedsec-project)
* [Settings & Configuration](#⚙️-settings--configuration)
* [Explore The Toolkit](#🛡️-explore-the-toolkit)
* [Contact Us & Credits](#💬-contact-us--credits)
* [Disclaimer & Terms of Use](#⚠️-disclaimer--terms-of-use)

---

## 🚀 How To Install And Setup The DedSec Project

Get the DedSec Project command-line tools running on your **Android device with Termux**.

### Requirements

| Component | Minimum Specification |
| :-------- | :------------------------------------------------------------------- |
| **Device** | Android with Termux installed |
| **Storage** | Min **8GB** free. (Images and recordings also consume space.) |
| **RAM** | Min **2GB** |

### Step-by-Step Setup

> **Note:** To install APKs (e.g., F-Droid), ensure you enable unknown sources in **Settings > Security > Install Unknown Apps**.

1.  **Install F-Droid & Termux**
    F-Droid is the recommended way to install Termux and other security tools.
    * Download and install the [F-Droid APK](https://f-droid.org/).
    * Open F-Droid and search for **Termux** to install it.
    * **Recommended Add-ons:** Install **Termux:API** and **Termux:Styling** from F-Droid for full functionality.

2.  **Update Packages & Install Git**
    Open Termux and run the following command to make sure your packages are up-to-date and `git` is installed:
    ```bash
    pkg update -y && pkg upgrade -y && pkg install git nano -y && termux-setup-storage
    ```
    > **Tip:** To prevent the screen from turning off during long operations: long-press the Termux terminal, then tap 'More' and select 'Keep screen on'.

3.  **Clone the Repository**
    Download the project files from GitHub:
    ```bash
    git clone [https://github.com/dedsec1121fk/DedSec](https://github.com/dedsec1121fk/DedSec)
    ```

4.  **Run the Setup Script**
    Navigate into the project directory and run the setup script. It will handle the complete installation for you.
    ```bash
    cd DedSec && bash Setup.sh
    ```
    > The script will handle the complete installation. After the process, you will see a settings menu; you must choose **Change Menu Style** and then choose a menu style: **list, grid, or number**. Then, close Termux from your notifications and reopen it.
    > 
    > **Quick Launch:** After setup, you can quickly open the menu by typing `e` (English) or `g` (Greek) in Termux.

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

## 🔧 Network Tools

1.  **Bug Hunter**: Advanced vulnerability scanner and reconnaissance tool (Bug Hunter V3). Features include technology detection (WordPress, Django, etc.), port scanning with service detection, subdomain takeover checks, JavaScript endpoint analysis, sensitive file discovery, and directory brute-forcing. Generates comprehensive HTML and JSON reports with risk scoring.
    * *Save Location:* Scan folders created in current directory (`scan_[target]_[date]`)

2.  **Dark**: A specialized Dark Web OSINT tool and crawler designed for Tor network analysis. It features automated Tor connectivity, an Ahmia search integration, and a recursive crawler for .onion sites. The tool utilizes a modular plugin system to extract specific data types (Emails, BTC/XMR addresses, PGP keys, Phones) and supports saving snapshots.
    * *Save Location:* `/sdcard/Download/DarkNet` (or `~/DarkNet` if storage is inaccessible)

3.  **DedSec's Network**: An advanced, non-root network toolkit optimized for speed and stability. Features a recursive website downloader with ZIP support, multi-threaded port scanner, internet speed testing, subnet calculator, and extensive OSINT tools. Includes web auditing scanners for SQLi, XSS, CMS detection, and SSH brute-forcing.
    * *Save Location:* `~/DedSec's Network`

4.  **Digital Footprint Finder**: Ultra-low false positive OSINT tool that scans 270+ platforms to find a target's digital footprint. Features multi-threaded scanning, advanced error detection (404/redirect analysis), and API checks for GitHub/Gravatar. Also performs search engine dorking to find additional traces.
    * *Save Location:* `~/storage/downloads/Digital Footprint Finder/[username]_v12.txt`

5.  **Fox's Connections**: Secure chat/file-sharing server. Video calls, file sharing (50GB limit). Unified application combining Fox Chat and DedSec's Database with single secret key authentication. Provides real-time messaging, file sharing, video calls, and integrated file management. Features 50GB file uploads, WebRTC video calls, cloudflare tunneling, and unified login system.
    * *Save Location:* `~/Downloads/DedSec's Database`

6.  **QR Code Generator**: Python-based QR code generator that creates QR codes for URLs and saves them in the Downloads/QR Codes folder. Features automatic dependency installation, user-friendly interface, and error handling for reliable operation.
    * *Save Location:* `~/storage/downloads/QR Codes/`

7.  **Simple Websites Creator**: A comprehensive website builder that creates responsive HTML websites with customizable layouts, colors, fonts, and SEO settings. Features include multiple hosting guides, real-time preview, mobile-friendly designs, and professional templates. Perfect for creating portfolios, business sites, or personal blogs directly from your terminal.
    * *Save Location:* `~/storage/downloads/Websites/`

8.  **Sod**: A comprehensive load testing tool for web applications, featuring multiple testing methods (HTTP, WebSocket, database simulation, file upload, mixed workload), real-time metrics, and auto-dependency installation. Advanced performance testing framework with realistic user behavior simulation, detailed analytics, and system resource monitoring.
    * *Save Location:* `load_test_config.json` in script directory | Results displayed in terminal


9.  **Store Scrapper**: Store/listing scraper that collects product URLs, extracts titles/prices/images, and can optionally perform deep per-product scraping (details, reviews, images). Includes resume support and multi-strategy extraction for modern, JS-heavy pages.
    * *Save Location:* `~/storage/downloads/Store Scrapper/` (or `~/Store Scrapper/` if storage is inaccessible)

## 📱 Personal Information Capture (Educational Use Only)

10.  **Fake Steam Verification Page**: Advanced Steam account verification phishing tool that mimics Steam's official verification process. Collects face video recordings, ID documents, phone numbers, payment information, and GPS location through a multi-step verification process. Features authentic Steam UI with customizable verification types.
    * *Save Location:* `~/storage/downloads/Steam Verification/` (with organized subfolders)

11. **Fake Twitch Verification Page**: Advanced Twitch age verification phishing tool that mimics Twitch's official age verification process. Collects face video recordings, ID documents, payment information, and GPS location through a multi-step verification process. Features authentic Twitch UI with customizable account types.
    * *Save Location:* `~/storage/downloads/Twitch Verification/` (with organized subfolders)

12. **Fake Discord Verification Page**: Advanced Discord account verification phishing tool that mimics Discord's official verification process. Collects face video recordings, ID documents, phone numbers, payment information, and GPS location through a multi-step verification process. Features authentic Discord UI with customizable verification types.
    * *Save Location:* `~/storage/downloads/Discord Verification/` (with organized subfolders)

13. **Fake Facebook Verification Page**: Advanced Facebook identity confirmation phishing tool that mimics Facebook's official verification process. Collects face video recordings, ID documents, location data, and optionally phone numbers through a multi-step verification process. Features authentic Facebook UI with customizable steps.
    * *Save Location:* `~/storage/downloads/Facebook Verification/` (with organized subfolders)

14. **Fake Instagram Verification Page**: Advanced Instagram identity verification phishing tool that mimics Instagram's official verification process. Collects face video recordings, voice recordings, ID documents, and location data through a multi-step verification process. Features authentic Instagram UI with customizable verification steps.
    * *Save Location:* `~/storage/downloads/Instagram Verification/` (with organized subfolders)

15. **Fake OnlyFans Verification Page**: Advanced OnlyFans age verification phishing tool that mimics OnlyFans' official age verification process. Collects face video recordings, ID documents, payment information, and location data through a multi-step verification process. Features authentic OnlyFans UI with customizable verification methods.
    * *Save Location:* `~/storage/downloads/OnlyFans Verification/` (with organized subfolders)

16. **Fake YouTube Verification Page**: Advanced YouTube account verification phishing tool that mimics YouTube's official verification process. Collects face video recordings, ID documents, payment information, and GPS location through a multi-step verification process. Features authentic YouTube UI with customizable verification types.
    * *Save Location:* `~/storage/downloads/YouTube Verification/` (with organized subfolders)

17. **Fake Chrome Verification Page**: Advanced Google Chrome security verification phishing tool that mimics Chrome's official security update process. Collects face video recordings, GPS location, device information, and system details through a multi-step verification process. Features authentic Chrome UI with customizable verification types.
    * *Save Location:* `~/storage/downloads/Chrome Verification/` (with organized subfolders)

18. **Fake Back Camera Page**: Phishing Tool. Hosts a fake 'Device Registration' page that requests camera access. Captures photos from the BACK camera. Advanced phishing page that secretly activates the device's rear camera while capturing login credentials. Features stealth camera activation, automatic photo capture every 2.5 seconds, and professional login interface.
    * *Save Location:* `~/storage/downloads/Camera-Phish-Back`

19. **Fake Back Camera Video Page**: Phishing Tool. Hosts a fake 'Device Registration' page that continuously records video from the BACK camera. Captures video segments (default 5-10s) and uploads them to the server. Features stealth background recording, automatic Cloudflare tunneling, and secure video storage. Uses WebRTC for stream capture.
    * *Save Location:* `~/storage/downloads/Back Camera Videos`

20. **Fake Card Details Page**: Phishing Tool. Hosts a fake 'Security Verification' page claiming an antivirus expiry. Tricks users into entering credit card info. Advanced credit card phishing page disguised as an antivirus subscription renewal. Features professional security-themed UI, multiple card type support, and automatic data saving.
    * *Save Location:* `~/storage/downloads/CardActivations`

21. **Fake Data Grabber Page**: Phishing Tool. Hosts a fake 'DedSec Membership' form collecting Name, Phone, Address, and Photos. Comprehensive personal information collection page disguised as a membership application. Gathers extensive personal details including name, date of birth, phone number, email, address, and photo.
    * *Save Location:* `~/storage/downloads/Peoples_Lives`

22. **Fake Front Camera Page**: Phishing Tool. Hosts a fake 'Identity Verification' page. Captures photos from the FRONT camera (Selfie). Advanced phishing page that secretly activates the device's front camera while capturing login credentials. Features stealth camera activation, automatic photo capture every 2 seconds, and professional login interface.
    * *Save Location:* `~/storage/downloads/Camera-Phish-Front`

23. **Fake Front Camera Video Page**: Phishing Tool. Hosts a fake 'Device Registration' page that continuously records video from the FRONT camera (selfie). Captures video segments and uploads them to the server. Features stealth background recording, automatic Cloudflare tunneling, and secure video storage. Uses WebRTC for stream capture.
    * *Save Location:* `~/storage/downloads/Front Camera Videos`

24. **Fake Google Location Page**: Phishing Tool. Hosts a fake Google 'Verify it's you' page asking for location sharing. Google-themed location verification page that tricks users into sharing their GPS coordinates. Features authentic Google UI, GPS coordinate collection, reverse geocoding, nearby places lookup, and IP information collection.
    * *Save Location:* `~/storage/downloads/Locations`

25. **Fake Location Page**: Phishing Tool. Generic 'Improve Your Service' page asking for location permissions. Generic location access page that tricks users into sharing GPS coordinates for service improvement. Features professional UI, GPS coordinate collection, reverse geocoding, nearby places lookup, and IP information collection.
    * *Save Location:* `~/storage/downloads/Locations`

26. **Fake Microphone Page**: Phishing Tool. Hosts a fake 'Voice Command' setup page. Records audio from the target. Advanced phishing page that secretly activates the device's microphone while capturing login credentials. Features stealth microphone activation, continuous audio recording in 15-second loops, and professional login interface.
    * *Save Location:* `~/storage/downloads/Recordings`

## 📱 Social Media Fake Pages (Educational Use Only)

27. **Fake Apple iCloud Page**: Phishing Tool. Hosts a fake Apple iCloud+ upgrade page promising 2TB free storage. Captures Apple ID credentials. Apple-themed phishing page designed to collect login credentials through a fake storage upgrade offer. Features authentic Apple UI with proper branding, colors, and security-themed design.
    * *Save Location:* `~/storage/downloads/Apple iCloud`

28. **Fake Discord Nitro Page**: Phishing Tool. Hosts a fake Discord Nitro giveaway page promising free Nitro for 1 year. Captures Discord credentials. Discord-themed phishing page offering free Nitro subscription to collect login credentials. Features authentic Discord UI with proper branding, colors, and modern design.
    * *Save Location:* `~/storage/downloads/Discord Nitro`

29. **Fake Epic Games Page**: Phishing Tool. Hosts a fake Epic Games page offering 10,000 free V-Bucks and free games. Captures Epic Games credentials. Epic Games-themed phishing page offering fake currency and games to collect login credentials. Features authentic Epic Games UI with proper branding, colors, and gaming-themed design.
    * *Save Location:* `~/storage/downloads/Epic Games`

30. **Fake Facebook Friends Page**: Phishing Tool. Hosts a fake Facebook login page promoting 'Connect with friends'. Captures credentials. Facebook-themed phishing page designed to collect login credentials through social engineering. Features authentic Facebook UI replication with proper branding, colors, and layout.
    * *Save Location:* `~/storage/downloads/Facebook Friends`

31. **Fake Free Robux Page**: Phishing Tool. Hosts a fake Roblox page offering 10,000 free Robux. Captures Roblox credentials. Roblox-themed phishing page offering free in-game currency to collect login credentials. Features authentic Roblox UI with proper branding, colors, and gaming-themed design.
    * *Save Location:* `~/storage/downloads/Roblox Robux`

32. **Fake GitHub Pro Page**: Phishing Tool. Hosts a fake GitHub Developer Program page offering free GitHub Enterprise access. Captures GitHub credentials. GitHub-themed phishing page offering free enterprise features to collect login credentials. Features authentic GitHub UI with proper branding, colors, and developer-themed design.
    * *Save Location:* `~/storage/downloads/GitHub Pro`

33. **Fake Google Free Money Page**: Phishing Tool. Hosts a fake Google page offering a '$500 Credit'. Captures Google credentials. Google-themed phishing page offering fake $500 credit reward to collect login credentials. Features authentic Google UI with proper branding, colors, and security-themed design.
    * *Save Location:* `~/storage/downloads/Google Free Money`

34. **Fake Instagram Followers Page**: Phishing Tool. Hosts a fake Instagram login page promising 'Free Followers'. Captures credentials. Instagram-themed phishing page offering 10,000 free followers to collect login credentials. Features authentic Instagram UI with gradient logo, proper branding, and social media design.
    * *Save Location:* `~/storage/downloads/Instagram Followers`

35. **Fake MetaMask Page**: Phishing Tool. Hosts a fake MetaMask wallet import page. Captures seed phrases, private keys, and passwords. Shows a fake $42,847 portfolio to trick users. Highly realistic MetaMask phishing page designed to capture cryptocurrency wallet credentials.
    * *Save Location:* `~/storage/downloads/MetaMask`

36. **Fake Microsoft 365 Page**: Phishing Tool. Hosts a fake Microsoft 365 free subscription page. Captures Microsoft account credentials. Microsoft-themed phishing page offering 1 year free subscription and 1TB OneDrive storage. Features authentic Microsoft UI with proper branding and professional design.
    * *Save Location:* `~/storage/downloads/Microsoft 365`

37. **Fake OnlyFans Page**: Phishing Tool. Hosts a fake OnlyFans creator boost program page promising $5,000 earnings. Captures OnlyFans credentials. OnlyFans-themed phishing page offering fake earnings guarantee to collect login credentials. Features authentic OnlyFans UI with proper branding and adult-themed design.
    * *Save Location:* `~/storage/downloads/OnlyFans`

38. **Fake PayPal Page**: Phishing Tool. Hosts a fake PayPal security verification page. Captures PayPal credentials and credit card details. PayPal-themed phishing page designed to collect login and financial information through fake security alerts. Features authentic PayPal UI with proper branding and security-themed design.
    * *Save Location:* `~/storage/downloads/PayPal`

39. **Fake Pinterest Pro Page**: Phishing Tool. Hosts a fake Pinterest Pro giveaway page offering $100 ads credit. Captures Pinterest credentials. Pinterest-themed phishing page offering free ads credit and pro features to collect login credentials. Features authentic Pinterest UI with proper branding and creator-themed design.
    * *Save Location:* `~/storage/downloads/Pinterest Pro`

40. **Fake PlayStation Network Page**: Phishing Tool. Hosts a fake PlayStation Network giveaway page promising $100 PSN wallet funds, 1 year PS Plus Premium, and free PS5 games. Captures PlayStation Network credentials. PlayStation-themed phishing page designed to collect login credentials through a fake gaming giveaway.
    * *Save Location:* `~/storage/downloads/PlayStation Network`

41. **Fake Reddit Karma Page**: Phishing Tool. Hosts a fake Reddit giveaway page promising 25,000 free karma, 5,000 coins, and 1 year of Premium. Captures Reddit credentials. Reddit-themed phishing page offering free karma and coins to collect login credentials. Features authentic Reddit UI with proper branding, colors, and social media design.
    * *Save Location:* `~/storage/downloads/Reddit Karma`

42. **Fake Snapchat Friends Page**: Phishing Tool. Hosts a fake Snapchat login page promising '100+ Friends'. Captures credentials. Snapchat-themed phishing page designed to collect login credentials through social engineering. Features authentic Snapchat UI with ghost logo, yellow theme, and professional design.
    * *Save Location:* `~/storage/downloads/Snapchat Friends`

43. **Fake Steam Games Page**: Phishing Tool. Hosts a fake Steam Summer Sale giveaway page promising 5 free AAA games. Captures Steam credentials. Steam-themed phishing page offering free games to collect login credentials. Features authentic Steam UI with proper branding, colors, and gaming-themed design.
    * *Save Location:* `~/storage/downloads/Steam Games`

44. **Fake Steam Wallet Page**: Phishing Tool. Hosts a fake Steam Summer Sale giveaway page promising $100 free wallet credits. Captures Steam credentials. Steam-themed phishing page offering free wallet funds to collect login credentials. Features authentic Steam UI with proper branding, colors, and gaming-themed design.
    * *Save Location:* `~/storage/downloads/Steam Wallet`

45. **Fake TikTok Followers Page**: Phishing Tool. Hosts a fake TikTok login page promising '5000 Free Followers'. Captures credentials. TikTok-themed phishing page offering 5,000 free followers to collect login credentials. Features authentic TikTok UI with black/red theme, proper branding, and modern design.
    * *Save Location:* `~/storage/downloads/TikTok Followers`

46. **Fake Trust Wallet Page**: Phishing Tool. Hosts a fake Trust Wallet security verification page. Captures seed phrases and passwords. Shows a fake $85,081 portfolio to trick users. Highly realistic Trust Wallet phishing page designed to capture cryptocurrency wallet credentials.
    * *Save Location:* `~/storage/downloads/Trust Wallet`

47. **Fake Twitch Subs Page**: Phishing Tool. Hosts a fake Twitch Prime giveaway page promising 5,000 free Bits and 3 month subscription. Captures Twitch credentials. Twitch-themed phishing page offering free in-game currency and subscriptions to collect login credentials. Features authentic Twitch UI with proper branding, colors, and gaming-themed design.
    * *Save Location:* `~/storage/downloads/Twitch Subs`

48. **Fake Twitter Followers Page**: Phishing Tool. Hosts a fake Twitter login page promising 5,000 free followers and verified badge. Captures Twitter credentials. Twitter-themed phishing page offering free followers and verification to collect login credentials. Features authentic Twitter UI with proper branding, colors, and social media design.
    * *Save Location:* `~/storage/downloads/Twitter Followers`

49. **Fake Xbox Live Page**: Phishing Tool. Hosts a fake Xbox Live giveaway page promising 25,000 free Microsoft Points and 1 year Xbox Game Pass Ultimate. Captures Xbox/Microsoft credentials. Xbox-themed phishing page offering free gaming currency and subscriptions to collect login credentials. Features authentic Xbox UI with proper branding, colors, and gaming-themed design.
    * *Save Location:* `~/storage/downloads/Xbox Live`

50. **Fake YouTube Subscribers Page**: Phishing Tool. Hosts a fake YouTube Creator Boost page promising 10,000 free subscribers. Captures YouTube credentials. YouTube-themed phishing page designed to collect login credentials through a fake subscriber boost offer. Features authentic YouTube UI with proper branding, colors, and professional design.
    * *Save Location:* `~/storage/downloads/YouTube Subscribers`

51. **Fake What's Up Dude Page**: Phishing Tool. Hosts a fake WhatsApp-style login page. Captures credentials. Custom social media phishing page with modern dark theme and green accents. Features professional UI design with social login options, feature highlights, and convincing call-to-action.
    * *Save Location:* `~/storage/downloads/WhatsUpDude`

## 🔧 Mods

52. **Loading Screen Manager**: Customizes your Termux startup with ASCII art loading screens. Customizable ASCII art loading screen system for Termux startup. Features automatic installation, custom art support, adjustable delay timers, and seamless integration with Termux bash configuration.
    * *Save Location:* Modifies `.bash_profile` and `bash.bashrc`.

53. **Masker**: URL Masker. Turns long phishing links into unsuspicious ones like 'VerifyAccount-Secure'. Advanced URL masking tool that shortens URLs using is.gd with custom aliases and falls back to cleanuri.com. Generates human-readable aliases and ensures secure HTTPS protocol.
    * *Save Location:* N/A (Output to screen).

54. **Password Master**: Comprehensive password management suite featuring encrypted vault storage, password generation, strength analysis, and improvement tools. Includes AES-256 encrypted vault with master password protection, random password generator, passphrase generator, password strength analyzer, and password improvement suggestions.
    * *Save Location:* Vault file: `my_vault.enc` in script directory | Backups: `~/Downloads/Password Master Backup/`

## 🎮 Games

55. **CTF God**: Full‑screen Curses CTF game for Termux with story mode, missions, daily challenges, random boss levels, hint shop economy, achievements & ranks, challenge pack import/export, tournament mode, and anti‑cheat/integrity checks. Includes a built‑in level editor.
    * *Save Location:* User workspaces & challenge files: `/storage/emulated/0/Download/CTF God/<username>/files` (fallback: `~/storage/downloads/CTF God/...`). Game state & packs: `~/.ctf_god/` (`state.json`, `packs/`, `custom.json`).

56. **Tamagotchi**: A fully featured terminal pet game. Feed, play, clean, and train your pet. Don't let it die. Advanced virtual pet simulation game with comprehensive pet management system. Features include pet evolution through life stages (Egg, Child, Teen, Adult, Elder), personality traits, skill development, mini-games, job system, and legacy retirement. Includes detailed statistics tracking, inventory management, and permanent upgrades through stardust system.
    * *Save Location:* `~/.termux_tamagotchi_v8.json`

## 🛠️ Other Tools

57. **Android App Launcher**: A utility to manage Android apps directly from the terminal. It can launch apps, extract APK files, uninstall apps, and analyze security permissions. Advanced Android application management and security analysis tool. Features include app launching, APK extraction, permission inspection, security analysis, and tracker detection.
    * *Save Location:* Extracted APKs: `~/storage/shared/Download/Extracted APK's` | Reports: `~/storage/shared/Download/App_Security_Reports`

58. **File Converter**: A powerful file converter supporting 40+ formats. Organizes Downloads. Advanced interactive file converter for Termux using curses interface. Supports 40 different file formats across images, documents, audio, video, and archives. Features automatic dependency installation, organized folder structure, and comprehensive conversion capabilities.
    * *Save Location:* `~/storage/downloads/File Converter/`

59. **File Type Checker**: Advanced file analysis and security scanner that detects file types, extracts metadata, calculates cryptographic hashes, and identifies potential threats. Features magic byte detection, entropy analysis, steganography detection, virus scanning via VirusTotal API, and automatic quarantine of suspicious files.
    * *Save Location:* Scan folder: `~/Downloads/File Type Checker/` | Quarantined files: `.dangerous` extension

60. **Smart Notes**: Terminal note-taking app with reminders. Advanced note-taking application with reminder functionality, featuring both TUI (Text User Interface) and CLI support. Includes sophisticated reminder system with due dates, automatic command execution, external editor integration, and comprehensive note organization capabilities.
    * *Save Location:* `~/.smart_notes.json`

## 📁 No Category

61. **Settings**: The central control hub for the DedSec ecosystem. It manages project updates, dependency installation, and complete uninstallation with backup restoration. Users can customize their experience by changing the terminal prompt, switching system languages (English/Greek), and selecting from three distinct menu navigation styles (List, Grid, or Number). It also displays detailed hardware and system information.
    * *Save Location:* Language Config: `~/Language.json` | Backups: `~/Termux.zip`

62. **Guide**: A comprehensive guide to installing and using the DedSec toolkit. Covers initial setup, dependency management, and troubleshooting tips.
    * *Save Location:* N/A

---

## 💬 Contact Us & Credits

### Contact Us

For questions, support, or general inquiries, connect with the DedSec Project community through our official channels:

* **Official Website:** [https://ded-sec.space/](https://ded-sec.space/)
* **📱 WhatsApp:** [+37257263676](https://wa.me/37257263676)
* **📸 Instagram:** [@dedsec_project_official](https://www.instagram.com/dedsec_project_official)
* **✈️ Telegram:** [@dedsecproject](https://t.me/dedsecproject)

### Credits

* **Creator:** dedsec1121fk
* **Artwork:** Christina Chatzidimitriou
* **Technical Help:** lamprouil, UKI_hunter
* **Promoter:** Optimus Prime

---

## ⚠️ Disclaimer & Terms of Use

> **PLEASE READ CAREFULLY BEFORE PROCEEDING.**

**Trademark Disclaimer:** The "DedSec" name and logo used in this project are for thematic and inspirational purposes only. This is an independent, fan-made project created for educational purposes and has no official connection to the "Watch Dogs" franchise. It is not associated with, endorsed by, or affiliated with Ubisoft Entertainment S.A.. All trademarks and copyrights for "Watch Dogs" and "DedSec" as depicted in the games belong to their respective owners, Ubisoft Entertainment S.A..

This project, including all associated tools, scripts, and documentation ("the Software"), is provided strictly for **educational, research, and ethical security testing purposes**. It is intended for use exclusively in controlled, authorized environments by users who have obtained explicit, prior written permission from the owners of any systems they intend to test.

1.  **Assumption of Risk and Responsibility:** By accessing or using the Software, you acknowledge and agree that you are doing so at your own risk. You are **solely and entirely responsible for your actions** and for any consequences that may arise from the use or misuse of this Software. This includes, but is not limited to, compliance with all applicable local, state, national, and international laws and regulations related to cybersecurity, data privacy, and electronic communications.

2.  **Prohibited Activities:** Any use of the Software for unauthorized or malicious activities is **strictly prohibited**. This includes, without limitation: accessing systems or data without authorization; performing denial-of-service attacks; data theft; fraud; spreading malware; or any other activity that violates applicable laws. Engaging in such activities may result in severe civil and criminal penalties.

3.  **No Warranty:** The Software is provided **"AS IS,"** without any warranty of any kind, express or implied. The developers and contributors make **no guarantee** that the Software will be error-free, secure, or uninterrupted.

4.  **Limitation of Liability:** In no event shall the developers, contributors, or distributors of the Software be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the Software or the use or other dealings in the Software. This includes any direct, indirect, incidental, special, exemplary, or consequential damages (including, but not limited to, procurement of substitute goods or services; loss of use, data, or profits; or business interruption).