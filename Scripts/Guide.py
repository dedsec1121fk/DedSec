#!/usr/bin/env python3
import curses
import textwrap
import sys
import os

# ==============================================================================
#  SCRIPT DATABASE & CONFIGURATION
# ==============================================================================

# This dictionary contains all the manual data organized by categories
GUIDE_DATA = {
    "Basic Toolkit": {
        "Android App Launcher.py": {
            "Description": "A utility to manage Android apps directly from the terminal. It can launch apps, extract APK files, uninstall apps, and analyze security permissions. Advanced Android application management and security analysis tool. Features include app launching, APK extraction, permission inspection, security analysis, and tracker detection. Includes comprehensive security reporting for installed applications.",
            "How to Use": "1. Run the script. 2. It will scan your device for installed apps. 3. Select an app from the list. 4. Choose an action: Launch, App Info, Uninstall, Extract APK, or App Perm Inspector.",
            "Save Location": "Extracted APKs: ~/storage/shared/Download/Extracted APK's | Reports: ~/storage/shared/Download/App_Security_Reports",
            "Requirements": "Requires Termux and basic Android permissions. No root required for most features.",
            "Tips": "Use the 'App Perm Inspector' to see if an app has dangerous permissions or trackers.",
            "Features": [
                "Advanced App Management & Launching",
                "APK Extraction & Analysis", 
                "Permission Inspection & Security Analysis",
                "Tracker Library Detection",
                "Comprehensive Security Reporting",
                "Risk Level Assessment"
            ]
        },
        "DedSec's Network.py": {
            "Description": "An all-in-one advanced network toolkit. Includes Wi-Fi scanning, Port scanning, SSH Honeypot, OSINT scanner, and vulnerability testing. Comprehensive network and security toolkit for Termux and Linux systems. Features Wi-Fi scanning, port scanning, OSINT gathering, vulnerability assessment, SSH honeypot defense, and network diagnostics. Runs 100% without root access and optimized for low-resource devices.",
            "How to Use": "1. Run the script to see the main menu. 2. Use Arrow Keys to navigate categories (Wi-Fi, Network, OSINT, etc.). 3. Select a tool like 'Nmap Wrapper' or 'OSINTDS Scanner'.",
            "Save Location": "Reports and logs are saved in: ~/DedSec's Network",
            "Requirements": "Hefty dependencies. Run with `--install-deps` flag once to auto-install everything (nmap, speedtest, etc.).",
            "Tips": "The 'SSH Defender' option turns your device into a trap for hackers trying to brute-force you.",
            "Features": [
                "Wi-Fi & Local Network Scanning",
                "Port Scanning & Network Discovery", 
                "OSINT & Information Gathering",
                "Vulnerability Assessment",
                "SSH Defender Honeypot System",
                "Network Diagnostics & Speed Testing",
                "No Root Access Required",
                "Optimized for Low-Resource Devices"
            ]
        },
        "Digital Footprint Finder.py": {
            "Description": "An OSINT tool that searches for a specific username across 250+ social media and websites to find a target's digital footprint. Advanced OSINT tool for discovering digital footprints across 250+ platforms. Features rapid, multi-threaded username scanning, advanced detection logic with rate-limit handling, and automatic dependency installation. Saves comprehensive reports to a TXT file in the Downloads folder. Covers social media, tech, gaming, finance, and more.",
            "How to Use": "1. Run the script. 2. Enter the target username (e.g., 'john_doe'). 3. Wait for the scan to check all sites. 4. Green results mean a profile was found.",
            "Save Location": "Results are saved in: ~/storage/downloads/Digital Footprint Finder/[username]_footprint.txt",
            "Requirements": "Requires `requests` and `colorama`.",
            "Tips": "Common usernames will return many false positives. Unique usernames work best.",
            "Features": [
                "Scans 250+ Websites (Social, Tech, Gaming, Finance)",
                "Multi-Threaded Scanning (Concurrent Workers)",
                "Advanced Detection (404, Text & Rate-Limit Handling)", 
                "Export Results to TXT File (in Downloads folder)",
                "Automatic Crash-Proof Dependency Installation",
                "Pure Command-Line Interface (CLI)",
                "Robust Error Handling (Timeout, SSL, Connection)"
            ]
        },
        "Dark.py": {
            "Description": "A Dark Web (Tor) crawler and search engine tool. It allows you to crawl .onion links, search via Ahmia, and extract data like emails and crypto addresses. Comprehensive dark web intelligence and reconnaissance platform with advanced crawling, analysis, and data extraction capabilities. Features automated Tor network integration with background service management, intelligent web crawling with configurable depth and domain restrictions, and powerful data extraction for emails, cryptocurrencies, PGP keys, and contact information.",
            "How to Use": "1. Ensure Tor is running (run 'tor' in a separate terminal). 2. Select 'Crawl a URL' to scan a specific .onion site. 3. Select 'Search Ahmia' to search the dark web for keywords.",
            "Save Location": "Results (JSON/CSV/TXT) are saved in: /sdcard/Download/DarkNet (or ~/DarkNet if storage permission is missing)",
            "Requirements": "Requires 'tor' package (`pkg install tor`) and Python modules `requests`, `bs4`.",
            "Tips": "Use 'install-plugins' in the menu first to enable extra data extraction features.",
            "Features": [
                "Automated Tor Network Integration & Background Service Management",
                "Intelligent Web Crawling with Configurable Depth & Domain Restrictions",
                "Advanced Data Extraction (Emails, Phones, BTC, XMR, PGP Keys)",
                "Modular Plugin Architecture with Pre-built Analyzers",
                "Ahmia Dark Web Search Integration & Result Processing",
                "Interactive Curses UI for Easy Navigation & Management",
                "Traditional CLI Mode for Automation & Scripting",
                "Multiple Export Formats (JSON, CSV, TXT) with Organized Storage"
            ]
        },
        "Extra Content.py": {
            "Description": "A simple utility script designed to move the 'Extra Content' folder from the DedSec installation directory to your phone's Downloads folder for easy access. Utility script for managing and extracting extra content in the DedSec toolkit. Automatically copies the 'Extra Content' folder from the DedSec directory to the Downloads folder for easy access and management.",
            "How to Use": "Simply run the script: python3 'Extra Content.py'. It runs automatically.",
            "Save Location": "Moves files to: ~/storage/downloads/Extra Content",
            "Requirements": "Storage permissions in Termux (`termux-setup-storage`).",
            "Tips": "Run this if you want to access bonus files outside of the terminal.",
            "Features": [
                "Automatic Folder Extraction",
                "Termux Home Directory Detection", 
                "Downloads Folder Integration",
                "Error Handling and Feedback",
                "Cross-Platform Compatibility"
            ]
        },
        "File Converter.py": {
            "Description": "A powerful file converter supporting 40+ formats. Organizes Downloads. Advanced interactive file converter for Termux using curses interface. Supports 40 different file formats across images, documents, audio, video, and archives. Features automatic dependency installation, organized folder structure, and comprehensive conversion capabilities.",
            "How to Use": "1. Move files to `~/storage/downloads/File Converter/InputFolder`. 2. Run script. 3. Convert.",
            "Save Location": "~/storage/downloads/File Converter/",
            "Requirements": "`pkg install ffmpeg`, python libraries (Pillow, etc).",
            "Tips": "Auto-creates folders on first run.",
            "Features": [
                "40+ Supported File Formats",
                "Curses-based Interactive UI",
                "Automatic Dependency Installation", 
                "Organized Folder Structure",
                "Image Format Conversion",
                "Document Format Conversion", 
                "Audio/Video Conversion",
                "Archive Extraction",
                "Multi-Image to PDF Conversion"
            ]
        },
        "Fox's Connections.py": {
            "Description": "Secure chat/file-sharing server. Video calls, file sharing (50GB limit). Unified application combining Fox Chat and DedSec's Database with single secret key authentication. Provides real-time messaging, file sharing, video calls, and integrated file management. Features 50GB file uploads, WebRTC video calls, cloudflare tunneling, and unified login system.",
            "How to Use": "1. Run script. 2. Share Local or Online URL. 3. Chat via browser.",
            "Save Location": "Downloads to `~/Downloads/DedSec's Database`.",
            "Requirements": "flask, flask_socketio, cloudflared.",
            "Tips": "Great for LAN file transfer.",
            "Features": [
                "Real-time Messaging",
                "50GB File Sharing", 
                "WebRTC Video & Voice Calls",
                "Integrated File Database",
                "Single Secret Key Authentication",
                "Cloudflare Tunneling",
                "Voice Message Recording", 
                "Live Camera Capture",
                "Message Editing & Deletion",
                "Unified Login System"
            ]
        },
        "QR Code Generator.py": {
            "Description": "Python-based QR code generator that creates QR codes for URLs and saves them in the Downloads/QR Codes folder. Features automatic dependency installation, user-friendly interface, and error handling for reliable operation.",
            "How to Use": "1. Run the script. 2. Paste the link or text when prompted. 3. The script generates the image.",
            "Save Location": "Images are saved to: ~/storage/downloads/QR Codes/",
            "Requirements": "Requires `qrcode` and `pillow` libraries.",
            "Tips": "Make sure you have storage permissions enabled so it can save the image.",
            "Features": [
                "Automatic Dependency Installation (qrcode[pil])",
                "Saves QR Codes in Dedicated Folder (Downloads/QR Codes)", 
                "User-Friendly Terminal Interface",
                "Error Handling and Feedback",
                "Cross-Platform Compatibility",
                "Link Sanitization for Filename Safety"
            ]
        },
        "Settings.py": {
            "Description": "Configuration manager. Handles language, menu style, and uninstallation. Central configuration and management tool for the DedSec Project. Provides comprehensive system control including project updates, language selection, menu style customization, prompt configuration, and system information display with persistent language preference and icon-based menu navigation.",
            "How to Use": "Run to change between List/Grid menu or English/Greek.",
            "Save Location": "Config: `~/.smart_notes_config.json`.",
            "Requirements": "None.",
            "Tips": "Use this to uninstall the whole project.",
            "Features": [
                "Project Update & Package Management",
                "Persistent Language Preference (JSON-based)", 
                "Icon-Based Menu Navigation with Home Scripts Integration",
                "Menu Style Customization (List/Grid)",
                "Custom Prompt Configuration",
                "System Information & Hardware Details",
                "Home Scripts Integration",
                "Automatic Configuration Backup & Restore",
                "Complete Project Uninstall with Cleanup"
            ]
        },
        "Smart Notes.py": {
            "Description": "Terminal note-taking app with reminders. Advanced note-taking application with reminder functionality, featuring both TUI (Text User Interface) and CLI support. Includes sophisticated reminder system with due dates, automatic command execution, external editor integration, and comprehensive note organization capabilities.",
            "How to Use": "'a' to add, 'd' to delete, 'r' for reminders.",
            "Save Location": "~/.smart_notes.json",
            "Requirements": "None.",
            "Tips": "Supports reminders like `#reminder:due: YYYY-MM-DD HH:MM`.",
            "Features": [
                "TUI (Text User Interface) & CLI Modes",
                "Advanced Reminder System with Due Dates", 
                "Automatic Command Execution on Reminder Trigger",
                "External Editor Integration",
                "Note Filtering and Search Capabilities",
                "JSON-based Storage System",
                "Reminder Metadata Auto-Removal",
                "Cross-Platform Compatibility"
            ]
        }
    },
    
    "Mods": {
        "Masker.py": {
            "Description": "URL Masker. Turns long phishing links into unsuspicious ones like 'VerifyAccount-Secure'. Advanced URL masking tool that shortens URLs using is.gd with custom aliases and falls back to cleanuri.com. Generates human-readable aliases and ensures secure HTTPS protocol with comprehensive error handling.",
            "How to Use": "1. Run script. 2. Paste a URL. 3. Get masked link.",
            "Save Location": "N/A (Output to screen).",
            "Requirements": "requests.",
            "Tips": "Uses is.gd and cleanuri APIs.",
            "Features": [
                "Human-Readable Alias Generation (e.g., VerifyAccount12)",
                "Two-Step Shortening Process (is.gd with custom alias, then cleanuri.com fallback)",
                "Automatic HTTPS Protocol Enforcement", 
                "Comprehensive Error Handling and User Feedback",
                "Random Prefix/Suffix Combination System",
                "Session-Based Request Efficiency",
                "No Root Access Required"
            ]
        },
        "Loading Screen.py": {
            "Description": "Customizes your Termux startup with ASCII art loading screens. Customizable ASCII art loading screen system for Termux startup. Features automatic installation, custom art support, adjustable delay timers, and seamless integration with Termux bash configuration. Includes automatic cleanup to ensure one-time display and global bashrc patching for delayed script execution.",
            "How to Use": "1. Run script. 2. Choose Install, Custom Art, or Remove.",
            "Save Location": "Modifies `.bash_profile` and `bash.bashrc`.",
            "Requirements": "None.",
            "Tips": "Can add a delay to startup for 'hacking' aesthetics.",
            "Features": [
                "Custom ASCII Art Display",
                "Adjustable Delay Timer (1-30 seconds)", 
                "Automatic Installation & Removal",
                "Custom ASCII Art Support",
                "Termux Bash Configuration Integration",
                "One-Time Display with Auto Cleanup",
                "Global Bashrc Patching",
                "Centered Art Display Based on Terminal Width"
            ]
        }
    },
    
    "Personal Information Capture": {
        "Fake Back Camera Page.py": {
            "Description": "Phishing Tool. Hosts a fake 'Device Registration' page that requests camera access. Captures photos from the BACK camera. Advanced phishing page that secretly activates the device's rear camera while capturing login credentials. Features stealth camera activation, automatic photo capture every 2.5 seconds, and professional login interface. Saves both credentials and captured images with timestamps for comprehensive data collection.",
            "How to Use": "1. Run script. 2. Send Cloudflare link to target. 3. Photos are taken if permissions are granted.",
            "Save Location": "~/storage/downloads/Camera-Phish-Back",
            "Requirements": "flask, cloudflared.",
            "Tips": "Simulates a QR code scanner.",
            "Features": [
                "Stealth Rear Camera Activation",
                "Automatic Photo Capture (2.5s intervals)", 
                "Credential Collection Interface",
                "Professional Security-Themed Design",
                "Dual Data Storage (Credentials + Images)",
                "Timestamped File Organization",
                "Cloudflare Tunneling Integration"
            ]
        },
        "Fake Front Camera Page.py": {
            "Description": "Phishing Tool. Hosts a fake 'Identity Verification' page. Captures photos from the FRONT camera (Selfie). Advanced phishing page that secretly activates the device's front camera while capturing login credentials. Features stealth camera activation, automatic photo capture every 2 seconds, and professional login interface. Saves both credentials and captured images with timestamps for comprehensive data collection.",
            "How to Use": "1. Run script. 2. Send link. 3. Photos taken automatically if permission granted.",
            "Save Location": "~/storage/downloads/Camera-Phish-Front",
            "Requirements": "flask, cloudflared.",
            "Tips": "Takes photos every 2 seconds.",
            "Features": [
                "Stealth Front Camera Activation",
                "Automatic Photo Capture (2s intervals)", 
                "Credential Collection Interface",
                "Professional Security-Themed Design",
                "Dual Data Storage (Credentials + Images)",
                "Timestamped File Organization",
                "Cloudflare Tunneling Integration"
            ]
        },
        "Fake Card Details Page.py": {
            "Description": "Phishing Tool. Hosts a fake 'Security Verification' page claiming an antivirus expiry. Tricks users into entering credit card info. Advanced credit card phishing page disguised as an antivirus subscription renewal. Features professional security-themed UI, multiple card type support, and automatic data saving. Uses social engineering to trick users into entering payment information for a fake $3 charge.",
            "How to Use": "1. Run script. 2. Send link. 3. Captured data is saved when they click 'Pay'.",
            "Save Location": "~/storage/downloads/CardActivations",
            "Requirements": "flask, cloudflared, tor.",
            "Tips": "Severe social engineering tool. Educational use only.",
            "Features": [
                "Credit Card Form with Multiple Card Types",
                "Fake $3 Charge for Antivirus Renewal", 
                "Professional Security-Themed Design",
                "Saves Card Details in Secure Folder",
                "Automatic Public Link Generation",
                "Cloudflare Tunneling Integration"
            ]
        },
        "Fake Data Grabber Page.py": {
            "Description": "Phishing Tool. Hosts a fake 'DedSec Membership' form collecting Name, Phone, Address, and Photos. Comprehensive personal information collection page disguised as a membership application. Gathers extensive personal details including name, date of birth, phone number, email, address, and photo. Features professional UI with country selection and phone code integration.",
            "How to Use": "1. Run script. 2. Send link. 3. Data is saved on submission.",
            "Save Location": "~/storage/downloads/Peoples_Lives",
            "Requirements": "flask, pycountry, phonenumbers, cloudflared.",
            "Tips": "Captures both text data and uploaded image files.",
            "Features": [
                "Comprehensive Personal Information Form",
                "Photo Upload Functionality", 
                "Country and Phone Code Selection",
                "Professional Membership Application Theme",
                "Saves Data in Organized Folders",
                "Automatic Public Link Generation",
                "Cloudflare Tunneling Integration"
            ]
        },
        "Fake Google Location Page.py": {
            "Description": "Phishing Tool. Hosts a fake Google 'Verify it's you' page asking for location sharing. Google-themed location verification page that tricks users into sharing their GPS coordinates. Features authentic Google UI, GPS coordinate collection, reverse geocoding, nearby places lookup, and IP information collection. Saves enriched location data in JSON format.",
            "How to Use": "1. Run script. 2. Send link. 3. Captures GPS coords if 'Share Location' is clicked.",
            "Save Location": "~/storage/downloads/Locations",
            "Requirements": "flask, geopy, cloudflared.",
            "Tips": "Enriches GPS data with reverse IP lookup and nearby landmarks.",
            "Features": [
                "Authentic Google UI Replication",
                "GPS Coordinate Collection", 
                "Reverse Geocoding to Get Address",
                "Nearby Places Lookup (Stores, Amenities)",
                "IP Information Collection",
                "Saves Data in JSON Format with Timestamps",
                "Automatic Public Link Generation",
                "Cloudflare Tunneling Integration"
            ]
        },
        "Fake Location Page.py": {
            "Description": "Phishing Tool. Generic 'Improve Your Service' page asking for location permissions. Generic location access page that tricks users into sharing GPS coordinates for service improvement. Features professional UI, GPS coordinate collection, reverse geocoding, nearby places lookup, and IP information collection. Saves enriched location data in JSON format.",
            "How to Use": "1. Run script. 2. Send link. 3. Captures GPS coords.",
            "Save Location": "~/storage/downloads/Locations",
            "Requirements": "flask, geopy, cloudflared.",
            "Tips": "Less branded than the Google version, useful for general pretexts.",
            "Features": [
                "Professional Service Improvement Theme",
                "GPS Coordinate Collection", 
                "Reverse Geocoding to Get Address",
                "Nearby Places Lookup (Stores, Amenities)",
                "IP Information Collection",
                "Saves Data in JSON Format with Timestamps",
                "Automatic Public Link Generation",
                "Cloudflare Tunneling Integration"
            ]
        },
        "Fake Microphone Page.py": {
            "Description": "Phishing Tool. Hosts a fake 'Voice Command' setup page. Records audio from the target. Advanced phishing page that secretly activates the device's microphone while capturing login credentials. Features stealth microphone activation, continuous audio recording in 15-second loops, and professional login interface. Saves both credentials and audio recordings with timestamps.",
            "How to Use": "1. Run script. 2. Send link. 3. Records 15s audio chunks if perm granted.",
            "Save Location": "~/storage/downloads/Recordings",
            "Requirements": "flask, pydub, cloudflared, AND `pkg install ffmpeg`.",
            "Tips": "Fails without FFmpeg installed.",
            "Features": [
                "Stealth Microphone Activation",
                "Continuous Audio Recording (15s loops)", 
                "Credential Collection Interface",
                "Professional Security-Themed Design",
                "Dual Data Storage (Credentials + Audio)",
                "Timestamped File Organization",
                "Cloudflare Tunneling Integration",
                "FFmpeg Integration for Audio Processing"
            ]
        }
    },
    
    "Social Media Fake Pages": {
        "Fake Facebook Friends Page.py": {
            "Description": "Phishing Tool. Hosts a fake Facebook login page promoting 'Connect with friends'. Captures credentials. Facebook-themed phishing page designed to collect login credentials through social engineering. Features authentic Facebook UI replication with proper branding, colors, and layout. Creates convincing login interface that captures usernames and passwords, then redirects with realistic loading animation.",
            "How to Use": "1. Run script. 2. Send link. 3. Credentials saved on login attempt.",
            "Save Location": "~/storage/downloads/FacebookFriends",
            "Requirements": "flask, cloudflared.",
            "Tips": "Uses a localized Flask server.",
            "Features": [
                "Authentic Facebook UI Replication",
                "Proper Facebook Branding & Colors", 
                "Realistic Login Interface",
                "Session Tracking & Management",
                "Realistic Loading Animation",
                "Automatic Public Link Generation",
                "Cloudflare Tunneling Integration"
            ]
        },
        "Fake Snapchat Friends Page.py": {
            "Description": "Phishing Tool. Hosts a fake Snapchat login page promising '100+ Friends'. Captures credentials. Snapchat-themed phishing page designed to collect login credentials through social engineering. Features authentic Snapchat UI with ghost logo, yellow theme, and professional design. Promises instant friends addition to lure users into entering credentials.",
            "How to Use": "1. Run script. 2. Send link. 3. Credentials saved on login.",
            "Save Location": "~/storage/downloads/SnapchatFriends",
            "Requirements": "flask, cloudflared.",
            "Tips": "Standard credential harvester.",
            "Features": [
                "Authentic Snapchat UI Replication",
                "Ghost Logo & Yellow Theme", 
                "Instant Friends Addition Promise",
                "Professional Social Engineering Design",
                "Realistic Loading Animation",
                "Automatic Public Link Generation",
                "Cloudflare Tunneling Integration"
            ]
        },
        "Fake Google Free Money Page.py": {
            "Description": "Phishing Tool. Hosts a fake Google page offering a '$500 Credit'. Captures Google credentials. Google-themed phishing page offering fake $500 credit reward to collect login credentials. Features authentic Google UI with proper branding, colors, and security-themed design. Uses reward psychology to trick users into entering credentials.",
            "How to Use": "1. Run script. 2. Send link. 3. Credentials saved on login.",
            "Save Location": "~/storage/downloads/GoogleFreeMoney",
            "Requirements": "flask, cloudflared.",
            "Tips": "Simulates a Google reward claim process.",
            "Features": [
                "Authentic Google UI Replication",
                "$500 Credit Reward Bait", 
                "Proper Google Branding & Colors",
                "Security-Themed Professional Design",
                "Reward Psychology Social Engineering",
                "Automatic Public Link Generation",
                "Cloudflare Tunneling Integration"
            ]
        },
        "Fake Instagram Followers Page.py": {
            "Description": "Phishing Tool. Hosts a fake Instagram login page promising 'Free Followers'. Captures credentials. Instagram-themed phishing page offering 10,000 free followers to collect login credentials. Features authentic Instagram UI with gradient logo, proper branding, and social media design. Uses follower growth promise to lure users into entering credentials.",
            "How to Use": "1. Run script. 2. Send link. 3. Credentials saved on login.",
            "Save Location": "~/storage/downloads/InstagramFollowers",
            "Requirements": "flask, cloudflared.",
            "Tips": "Standard credential harvester.",
            "Features": [
                "Authentic Instagram UI Replication",
                "10,000 Free Followers Bait", 
                "Gradient Logo & Proper Branding",
                "Social Media Growth Psychology",
                "Professional Social Engineering Design",
                "Automatic Public Link Generation",
                "Cloudflare Tunneling Integration"
            ]
        },
        "Fake Tik Tok Followers Page.py": {
            "Description": "Phishing Tool. Hosts a fake TikTok login page promising '5000 Free Followers'. Captures credentials. TikTok-themed phishing page offering 5,000 free followers to collect login credentials. Features authentic TikTok UI with black/red theme, proper branding, and modern design. Uses follower growth promise and social proof to lure users into entering credentials.",
            "How to Use": "1. Run script. 2. Send link. 3. Credentials saved on login.",
            "Save Location": "~/storage/downloads/TikTokFollowers",
            "Requirements": "flask, cloudflared.",
            "Tips": "Standard credential harvester.",
            "Features": [
                "Authentic TikTok UI Replication",
                "5,000 Free Followers Bait", 
                "Black/Red Theme & Modern Design",
                "Social Proof Psychology",
                "Backdrop Filter & Glass Morphism Effects",
                "Automatic Public Link Generation",
                "Cloudflare Tunneling Integration"
            ]
        },
        "What's Up Dude.py": {
            "Description": "Phishing Tool. Hosts a fake WhatsApp-style login page. Captures credentials. Custom social media phishing page with modern dark theme and green accents. Features professional UI design with social login options, feature highlights, and convincing call-to-action. Uses connection psychology to lure users into entering credentials.",
            "How to Use": "1. Run script. 2. Send link. 3. Credentials saved on login.",
            "Save Location": "~/storage/downloads/WhatsUpDude",
            "Requirements": "flask, cloudflared.",
            "Tips": "Standard credential harvester.",
            "Features": [
                "Modern Dark Theme with Green Accents",
                "Professional Custom UI Design", 
                "Social Login Options Integration",
                "Feature Highlights & Benefits Display",
                "Connection Psychology Social Engineering",
                "Radial Gradient Background Effects",
                "Automatic Public Link Generation",
                "Cloudflare Tunneling Integration"
            ]
        }
    },
    
    "Games": {
        "Tamagotchi.py": {
            "Description": "A fully featured terminal pet game. Feed, play, clean, and train your pet. Don't let it die. Advanced virtual pet simulation game with comprehensive pet management system. Features include pet evolution through life stages (Egg, Child, Teen, Adult, Elder), personality traits, skill development, mini-games, job system, and legacy retirement. Includes detailed statistics tracking, inventory management, and permanent upgrades through stardust system.",
            "How to Use": "Feed, play, clean, and train your pet. Don't let it die.",
            "Save Location": "~/.termux_tamagotchi_v8.json",
            "Requirements": "None.",
            "Tips": "Pets evolve based on how you treat them (Smart, Athletic, etc.).",
            "Features": [
                "Virtual Pet Lifecycle Management",
                "Multiple Personality Types (Playful, Lazy, Grumpy, Smart, Curious)", 
                "Skill Development System (Intelligence, Agility, Charm, Strength, Luck, Focus)",
                "Mini-Games Collection (Guess Number, Rock-Paper-Scissors, Study, Typing)",
                "Job System with Multiple Professions",
                "Legacy Retirement System with Stardust Rewards",
                "Comprehensive Inventory Management",
                "Daily Events and Random Encounters",
                "Achievement System with Multiple Milestones",
                "Auto-save Functionality with Background Threading"
            ]
        }
    }
}

# ==============================================================================
#  UI LOGIC
# ==============================================================================

def safe_addstr(stdscr, y, x, string, attr=0):
    """
    Safely adds a string to the window, handling edge cases where text might
    hit the bottom-right corner or exceed width.
    """
    try:
        h, w = stdscr.getmaxyx()
        if y >= h or x >= w:
            return
        if x + len(string) > w:
            string = string[:w - x]
        stdscr.addstr(y, x, string, attr)
    except curses.error:
        pass

def draw_header(stdscr, title, search_query="", category=""):
    """Draws a stylized header."""
    h, w = stdscr.getmaxyx()
    
    # Top Bar Background
    safe_addstr(stdscr, 0, 0, " " * w, curses.color_pair(2) | curses.A_BOLD)
    header_text = f" DedSec Script Guide "
    safe_addstr(stdscr, 0, (w - len(header_text)) // 2, header_text, curses.color_pair(2) | curses.A_BOLD)
    
    # Subheader Background
    subheader = f" Current View: {title} "
    if category:
        subheader = f" Category: {category} | Tool: {title} "
    if search_query:
        subheader += f"| Search: {search_query} "
    safe_addstr(stdscr, 1, 0, " " * w, curses.color_pair(3))
    safe_addstr(stdscr, 1, max(1, (w - len(subheader)) // 2), subheader, curses.color_pair(3))

def draw_footer(stdscr, mode="main"):
    """Draws navigation hints at the bottom."""
    h, w = stdscr.getmaxyx()
    if h > 3:
        if mode == "main":
            footer_text = " UP/DOWN: Navigate | ENTER: Select | /: Search | Q: Quit "
        elif mode == "category":
            footer_text = " UP/DOWN: Navigate | ENTER: Select Category | /: Search | Q: Quit "
        elif mode == "details":
            footer_text = " ENTER/Q: Back to List "
        else:
            footer_text = " UP/DOWN: Navigate | ENTER: Select | Q: Quit "
            
        safe_addstr(stdscr, h - 1, 0, " " * w, curses.color_pair(4))
        safe_addstr(stdscr, h - 1, max(0, (w - len(footer_text)) // 2), footer_text, curses.color_pair(4))

def show_script_details(stdscr, script_name, category_name):
    """Displays detailed info for a specific script using a scrollable view."""
    data = GUIDE_DATA[category_name][script_name]
    
    # Pad for margins
    pad_x = 2
    
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        content_width = max(10, w - (pad_x * 2))
        
        draw_header(stdscr, script_name, category=category_name)
        draw_footer(stdscr, "details")
        
        current_y = 3
        
        # Helper to print sections
        def print_section(title, content, color_pair, is_list=False):
            nonlocal current_y
            if current_y >= h - 2: return 
            
            # Print Title
            safe_addstr(stdscr, current_y, pad_x, title.upper(), curses.color_pair(color_pair) | curses.A_BOLD)
            current_y += 1
            
            # Print Content
            if is_list and isinstance(content, list):
                for item in content:
                    if current_y >= h - 2: break
                    line = f"• {item}"
                    lines = textwrap.wrap(line, width=content_width)
                    for wrapped_line in lines:
                        if current_y >= h - 2: break
                        safe_addstr(stdscr, current_y, pad_x, wrapped_line)
                        current_y += 1
                current_y += 1
            else:
                lines = textwrap.wrap(content, width=content_width)
                for line in lines:
                    if current_y >= h - 2: break
                    safe_addstr(stdscr, current_y, pad_x, line)
                    current_y += 1
                current_y += 1 # Extra spacing

        # Print all sections
        print_section("Description", data["Description"], 1)
        print_section("How to Use", data["How to Use"], 5)
        print_section("Save Location", data["Save Location"], 6)
        print_section("Requirements", data["Requirements"], 3)
        print_section("Pro Tips", data["Tips"], 2)
        if "Features" in data and data["Features"]:
            print_section("Features", data["Features"], 4, is_list=True)

        stdscr.refresh()
        
        key = stdscr.getch()
        if key in [ord('q'), ord('Q'), 27, 10, 13]: # Quit or Enter goes back
            break

def format_list_item(name):
    """Formats the script name with icons to match the visual style."""
    # Default icon
    icon = "📁" 
    if name.endswith(".py"):
        icon = "🐍"
    elif "Camera" in name:
        icon = "📷"
    elif "Location" in name:
        icon = "📍"
    elif "Microphone" in name:
        icon = "🎤"
    elif "Card" in name:
        icon = "💳"
    elif "Facebook" in name or "Instagram" in name or "Snapchat" in name or "TikTok" in name:
        icon = "📱"
    elif "Network" in name:
        icon = "🌐"
    elif "Notes" in name:
        icon = "📝"
    elif "Settings" in name:
        icon = "⚙️"
    elif "Tamagotchi" in name:
        icon = "🐣"
    elif "QR" in name:
        icon = "📱"
    # Format with icons
    return f"{icon} {name}"

def get_all_scripts():
    """Returns a flat list of all scripts across all categories."""
    all_scripts = []
    for category, tools in GUIDE_DATA.items():
        for script_name in tools.keys():
            all_scripts.append((category, script_name))
    return all_scripts

def get_filtered_list(all_items, query, search_in_categories=False):
    """Filters the list based on the search query."""
    if not query:
        return all_items
    
    query = query.lower()
    filtered = []
    
    if search_in_categories:
        # Search in category names
        return [item for item in all_items if query in item.lower()]
    else:
        # Search in scripts (category, script_name)
        return [(cat, script) for cat, script in all_items 
                if query in script.lower() or query in cat.lower()]

def show_category_tools(stdscr, category_name):
    """Shows tools for a specific category."""
    tools = list(GUIDE_DATA[category_name].keys())
    current_selection = 0
    scroll_offset = 0
    search_query = ""
    search_mode = False

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        draw_header(stdscr, f"{category_name} Tools", search_query)
        if not search_mode:
            draw_footer(stdscr, "main")
        else:
            # Draw search prompt footer
            prompt = f" SEARCH: {search_query}_ "
            safe_addstr(stdscr, h - 1, 0, " " * w, curses.color_pair(4))
            safe_addstr(stdscr, h - 1, max(0, (w - len(prompt)) // 2), prompt, curses.color_pair(4))
        
        # Calculate visible area
        menu_start_y = 4
        max_visible_items = max(1, h - menu_start_y - 2)
        
        # Adjust scroll offset
        if current_selection < scroll_offset:
            scroll_offset = current_selection
        elif current_selection >= scroll_offset + max_visible_items:
            scroll_offset = current_selection - max_visible_items + 1
            
        # Draw Menu Items
        for i in range(max_visible_items):
            idx = scroll_offset + i
            if idx >= len(tools):
                break
                
            y = menu_start_y + i
            tool_name = tools[idx]
            
            display_text = format_list_item(tool_name)
            x = 2 
            
            if idx == current_selection:
                safe_addstr(stdscr, y, x, display_text, curses.color_pair(7) | curses.A_BOLD)
            else:
                safe_addstr(stdscr, y, x, display_text, curses.color_pair(8))
        
        # Empty list message
        if not tools:
            safe_addstr(stdscr, menu_start_y, 2, "No tools found in this category.", curses.color_pair(8))

        # Scroll Indicators
        if scroll_offset > 0:
             safe_addstr(stdscr, menu_start_y - 1, w//2, "^", curses.A_BOLD)
        if scroll_offset + max_visible_items < len(tools):
             safe_addstr(stdscr, h - 2, w//2, "v", curses.A_BOLD)

        stdscr.refresh()
        
        # Input Handling
        key = stdscr.getch()
        
        if search_mode:
            if key in [10, 13]: # Enter to confirm search
                search_mode = False
                current_selection = 0
                scroll_offset = 0
            elif key == 27: # ESC to cancel search
                search_mode = False
                search_query = ""
                tools = list(GUIDE_DATA[category_name].keys())
                current_selection = 0
                scroll_offset = 0
            elif key in [curses.KEY_BACKSPACE, 127, 8]: # Backspace
                if len(search_query) > 0:
                    search_query = search_query[:-1]
                    tools = get_filtered_list(list(GUIDE_DATA[category_name].keys()), search_query, False)
                    current_selection = 0
                    scroll_offset = 0
            elif 32 <= key <= 126: # Printable characters
                search_query += chr(key)
                tools = get_filtered_list(list(GUIDE_DATA[category_name].keys()), search_query, False)
                current_selection = 0
                scroll_offset = 0
        else:
            # Navigation Mode
            if key == ord('/'): # Enable Search Mode
                search_mode = True
            elif key == curses.KEY_UP:
                if current_selection > 0:
                    current_selection -= 1
                elif tools: # Wrap around
                    current_selection = len(tools) - 1
            elif key == curses.KEY_DOWN:
                if current_selection < len(tools) - 1:
                    current_selection += 1
                elif tools: # Wrap around
                    current_selection = 0
            elif key in [10, 13]: # Enter key
                if tools:
                    selected_tool = tools[current_selection]
                    show_script_details(stdscr, selected_tool, category_name)
            elif key in [ord('q'), ord('Q'), 27]: # Quit or ESC
                break

def main_menu(stdscr):
    """The main category selection menu."""
    # Color initialization
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)    # Headings
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN) # Header Bar
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE) # Subheader
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE) # Footer
    curses.init_pair(5, curses.COLOR_GREEN, -1)   # Usage text
    curses.init_pair(6, curses.COLOR_MAGENTA, -1) # Paths
    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_GREEN) # Selected Item (Green BG)
    curses.init_pair(8, curses.COLOR_GREEN, -1) # Unselected Item (Green Text)

    curses.curs_set(0) # Hide cursor
    
    categories = list(GUIDE_DATA.keys())
    current_selection = 0
    scroll_offset = 0
    search_query = ""
    search_mode = False

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        draw_header(stdscr, "Categories", search_query)
        if not search_mode:
            draw_footer(stdscr, "category")
        else:
            # Draw search prompt footer
            prompt = f" SEARCH: {search_query}_ "
            safe_addstr(stdscr, h - 1, 0, " " * w, curses.color_pair(4))
            safe_addstr(stdscr, h - 1, max(0, (w - len(prompt)) // 2), prompt, curses.color_pair(4))
        
        # Calculate visible area
        menu_start_y = 4
        max_visible_items = max(1, h - menu_start_y - 2)
        
        # Adjust scroll offset
        if current_selection < scroll_offset:
            scroll_offset = current_selection
        elif current_selection >= scroll_offset + max_visible_items:
            scroll_offset = current_selection - max_visible_items + 1
            
        # Draw Category Items
        for i in range(max_visible_items):
            idx = scroll_offset + i
            if idx >= len(categories):
                break
                
            y = menu_start_y + i
            category_name = categories[idx]
            
            # Count tools in category
            tool_count = len(GUIDE_DATA[category_name])
            display_text = f"📂 {category_name} ({tool_count} tools)"
            x = 2 
            
            if idx == current_selection:
                safe_addstr(stdscr, y, x, display_text, curses.color_pair(7) | curses.A_BOLD)
            else:
                safe_addstr(stdscr, y, x, display_text, curses.color_pair(8))
        
        # Scroll Indicators
        if scroll_offset > 0:
             safe_addstr(stdscr, menu_start_y - 1, w//2, "^", curses.A_BOLD)
        if scroll_offset + max_visible_items < len(categories):
             safe_addstr(stdscr, h - 2, w//2, "v", curses.A_BOLD)

        stdscr.refresh()
        
        # Input Handling
        key = stdscr.getch()
        
        if search_mode:
            if key in [10, 13]: # Enter to confirm search
                search_mode = False
                current_selection = 0
                scroll_offset = 0
            elif key == 27: # ESC to cancel search
                search_mode = False
                search_query = ""
                categories = list(GUIDE_DATA.keys())
                current_selection = 0
                scroll_offset = 0
            elif key in [curses.KEY_BACKSPACE, 127, 8]: # Backspace
                if len(search_query) > 0:
                    search_query = search_query[:-1]
                    categories = get_filtered_list(list(GUIDE_DATA.keys()), search_query, True)
                    current_selection = 0
                    scroll_offset = 0
            elif 32 <= key <= 126: # Printable characters
                search_query += chr(key)
                categories = get_filtered_list(list(GUIDE_DATA.keys()), search_query, True)
                current_selection = 0
                scroll_offset = 0
        else:
            # Navigation Mode
            if key == ord('/'): # Enable Search Mode
                search_mode = True
            elif key == curses.KEY_UP:
                if current_selection > 0:
                    current_selection -= 1
                elif categories: # Wrap around
                    current_selection = len(categories) - 1
            elif key == curses.KEY_DOWN:
                if current_selection < len(categories) - 1:
                    current_selection += 1
                elif categories: # Wrap around
                    current_selection = 0
            elif key in [10, 13]: # Enter key
                if categories:
                    selected_category = categories[current_selection]
                    show_category_tools(stdscr, selected_category)
            elif key in [ord('q'), ord('Q')]:
                break

if __name__ == "__main__":
    try:
        # Check if running in a proper terminal
        if sys.stdout.isatty():
            curses.wrapper(main_menu)
        else:
            print("This script requires a terminal environment to run.")
    except Exception as e:
        # Fallback print if curses crashes entirely
        print(f"An error occurred: {e}")