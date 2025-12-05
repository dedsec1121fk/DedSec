#!/usr/bin/env python3
import curses
import textwrap
import sys
import os

# ==============================================================================
#  SCRIPT DATABASE & CONFIGURATION (UPDATED WITH NEW SCRIPTS)
# ==============================================================================

# This dictionary contains all the manual data organized by categories
GUIDE_DATA = {
    "Basic Toolkit": {
        "Simple Websites Creator.py": {
            "Description": "A comprehensive website builder that creates responsive HTML websites with customizable layouts, colors, fonts, and SEO settings. Features include multiple hosting guides, real-time preview, mobile-friendly designs, and professional templates. Perfect for creating portfolios, business sites, or personal blogs directly from your terminal.",
            "How to Use": "1. Run the script. 2. Choose 'Create Website' from the menu. 3. Follow the prompts to customize your site. 4. Access publishing guides to deploy your website online.",
            "Save Location": "Websites are saved in: ~/storage/downloads/Websites/",
            "Requirements": "Requires Termux storage permissions (run `termux-setup-storage` first) and Python 3.",
            "Tips": "Use the built-in publishing guide to deploy your website for free on platforms like GitHub Pages, Netlify, or Vercel.",
            "Features": [
                "Responsive HTML Website Generation",
                "Customizable Layouts & Color Schemes",
                "Font Selection & Typography Controls",
                "SEO & Meta Tag Configuration",
                "Mobile-First Responsive Design",
                "Built-in Publishing Guides (6 Free Hosting Options)",
                "Professional Templates & Components",
                "Website Management (Edit, List, Delete)",
                "Cross-Platform Compatibility"
            ]
        },
        "Sod.py": {
            "Description": "A comprehensive load testing tool for web applications, featuring multiple testing methods (HTTP, WebSocket, database simulation, file upload, mixed workload), real-time metrics, and auto-dependency installation. Advanced performance testing framework with realistic user behavior simulation, detailed analytics, and system resource monitoring. Perfect for stress testing your own web applications and APIs.",
            "How to Use": "1. Run the script (auto-installs dependencies first). 2. Configure target IP/port in the menu. 3. Select test type (HTTP, WebSocket, Database, etc.). 4. Set thread count and duration. 5. Monitor real-time metrics during testing.",
            "Save Location": "Configuration: load_test_config.json in script directory | Results: Displayed in terminal",
            "Requirements": "Python 3.6+, internet connectivity. Auto-installs: requests, urllib3, websocket-client, psutil",
            "Tips": "Use 'Mixed Workload' for realistic user simulation and monitor system resources during high-load tests to avoid overwhelming your device.",
            "Features": [
                "Multiple Testing Methods (HTTP, WebSocket, Database, File Upload)",
                "Real-Time Performance Metrics & Analytics",
                "Auto-Dependency Installation & Management",
                "Realistic User Behavior Simulation",
                "System Resource Monitoring (CPU, RAM, Network)",
                "Adaptive Rate Limiting & Connection Pooling",
                "Response Time Percentiles (P50, P95, P99)",
                "Bandwidth & Throughput Monitoring",
                "Configuration Persistence & Save/Load",
                "Comprehensive Test Summary Reports"
            ]
        },
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
            "Description": "An all-in-one advanced network toolkit. Includes network scanning, port scanning, SSH auditing, OSINT gathering, and vulnerability testing. Comprehensive network and security toolkit for Termux and Linux systems. Features internet speed testing, subnet calculation, DNS record lookup, web crawling, subdomain enumeration, and security scanning capabilities. Auto-installs dependencies and provides both interactive TUI and CLI interfaces.",
            "How to Use": "1. Run the script (use --install flag first time for dependencies). 2. Navigate through categories (Network, OSINT, Web Security). 3. Select tools like Port Scanner, WHOIS Lookup, or SQL Injection Tester.",
            "Save Location": "Reports and logs are saved in: ~/DedSec_Tools/",
            "Requirements": "Run with --install flag first to auto-install dependencies (requests, paramiko, speedtest-cli, etc.)",
            "Tips": "The SSH Brute Force tool tests common passwords - use only on systems you own for security testing.",
            "Features": [
                "Port Scanning & Network Discovery",
                "Internet Speed Testing & IP Information",
                "WHOIS Lookup & DNS Record Analysis",
                "Subdomain Enumeration & Web Crawling",
                "HTTP Header Analysis & CMS Detection",
                "SQL Injection & XSS Vulnerability Testing",
                "SSH Brute Force Auditing",
                "Auto-Dependency Installation",
                "Interactive TUI & CLI Modes",
                "Audit Logging & Results Database"
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
            "Description": "A Dark Web (Tor) crawler and search engine tool. It allows you to crawl .onion links, search via Ahmia, and extract data like emails and crypto addresses. Comprehensive dark web intelligence and reconnaissance platform with advanced crawling, analysis, and data extraction capabilities. Features automated Tor network integration with background service management, intelligent web crawling with configurable depth and domain restrictions, and powerful data extraction for emails, cryptocurrencies, PGP keys, and contact information. Includes a modular plugin architecture with pre-built analyzers for metadata, links, content cleaning, and automated exports.",
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
                "Multiple Export Formats (JSON, CSV, TXT) with Organized Storage",
                "Automatic HTML Snapshots for Forensic Analysis",
                "Flexible SOCKS Proxy Support (Default: Tor)",
                "Cross-Platform Compatibility (Termux, Linux, Android)",
                "Automatic Dependency Installation & Environment Setup",
                "Real-time Progress Monitoring & Status Updates",
                "Customizable Crawling Delays & Request Throttling",
                "Comprehensive Error Handling & Connection Resilience"
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
            "Description": "A powerful file converter supporting 40+ formats. Advanced interactive file converter for Termux using curses interface. Supports 40 different file formats across images, documents, audio, video, and archives. Features automatic dependency installation, organized folder structure, and comprehensive conversion capabilities. Includes automatic system package installation, Python library management, and robust error handling for reliable file processing.",
            "How to Use": "1. Move files to `~/storage/downloads/File Converter/[FormatFolder]`. 2. Run script. 3. Select input folder, file, and output format. 4. Convert.",
            "Save Location": "~/storage/downloads/File Converter/",
            "Requirements": "Auto-installs ffmpeg, unrar, and Python libraries (Pillow, reportlab, python-docx, etc.)",
            "Tips": "Auto-creates folders on first run. Use the multi-image to PDF feature for combining multiple images.",
            "Features": [
                "40+ Supported File Formats",
                "Curses-based Interactive UI",
                "Automatic System Dependency Installation",
                "Python Library Auto-Installation",
                "Organized Folder Structure (40 format folders)",
                "Image Format Conversion & Multi-Image to PDF",
                "Document Format Conversion (PDF, DOCX, ODT, HTML, etc.)",
                "Audio/Video Conversion (via FFmpeg)",
                "Archive Extraction (ZIP, RAR, 7Z, TAR, GZ)",
                "Data Conversion (CSV to JSON, JSON to CSV)",
                "Text Extraction from Various Document Formats",
                "Robust Error Handling & Progress Feedback"
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
            "Description": "Configuration manager. Handles language, menu style, and uninstallation. Central configuration and management tool for the DedSec Project. Provides comprehensive system control including project updates, language selection, menu style customization, prompt configuration, and system information display with persistent language preference and icon-based menu navigation. Features Home Scripts integration, backup/restore functionality, and complete uninstall capability.",
            "How to Use": "Run to change between List/Grid menu or English/Greek. Use --menu [style] for direct menu access.",
            "Save Location": "Config: `~/.smart_notes_config.json`. Language: `~/Language.json`",
            "Requirements": "None.",
            "Tips": "Use this to uninstall the whole project or switch between English and Greek interfaces.",
            "Features": [
                "Project Update & Package Management",
                "Persistent Language Preference (JSON-based)", 
                "Icon-Based Menu Navigation with Home Scripts Integration",
                "Menu Style Customization (List/Grid/Number)",
                "Custom Prompt Configuration",
                "System Information & Hardware Details",
                "Home Scripts Integration (Access scripts in home directory)",
                "Automatic Configuration Backup & Restore",
                "Complete Project Uninstall with Cleanup",
                "Automatic Bash Configuration Updates",
                "Credits & Project Information"
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
        },
        "My AI.py": {
            "Description": "A powerful CLI AI assistant powered by Google's Gemini API with bilingual English/Greek support. Features persistent memory, Aiden Pearce persona from Watch Dogs, and natural conversation flow. The assistant maintains context across sessions and can handle coding, analysis, creative writing, and technical tasks with tactical precision.",
            "How to Use": "1. Run script (first time: enter Gemini API key). 2. Chat naturally in English or Greek. 3. Use commands: 'delete history' to clear memory, 'exit' to quit. 4. Supports piped input: echo 'question' | python3 MyAI.py",
            "Save Location": "Config: ~/.local/share/my_ai/config.json | History: ~/.local/share/my_ai/history.json",
            "Requirements": "Gemini API key (free from Google AI Studio), Python 3.7+, requests library.",
            "Tips": "The AI remembers previous conversations. Use clear prompts for technical tasks. Can switch languages mid-conversation.",
            "Features": [
                "Gemini API Integration (gemini-1.5-flash model)",
                "Bilingual English/Greek Support with Auto-Detection",
                "Persistent Chat Memory Across Sessions",
                "Aiden Pearce Persona (Tactical/Cynical Tone)",
                "Natural Conversation Flow with Context Retention",
                "Command Control (Delete History, Exit)",
                "Piped Input Support for Automation",
                "Configurable System Instructions",
                "Auto-Dependency Installation",
                "Cross-Platform Compatibility (Termux/Linux)"
            ]
        },
        "I'm The Truth.py": {
            "Description": "A massive collection of 400+ Christian stories, wisdom, and parables from Orthodox tradition. Features include warrior saints, Old Testament stories, modern saints, desert fathers wisdom, and Jesus' parables. Interactive TUI with search, random selection, and categorized browsing for spiritual growth and meditation.",
            "How to Use": "1. Run script. 2. Navigate categories with arrow keys. 3. Press Enter to read stories. 4. Use '/' to search, 'R' for random, 'Q' to quit.",
            "Save Location": "No file saving - all content embedded in script.",
            "Requirements": "rich library (auto-installed), Python 3.6+.",
            "Tips": "Use search function to find specific stories. Random feature provides daily inspiration.",
            "Features": [
                "400+ Stories Across Multiple Categories",
                "Interactive TUI with Rich Formatting",
                "Search Functionality Across All Content",
                "Random Story Selection",
                "Categories: Warrior Saints, Old Testament, Modern Saints, Parables, Desert Fathers",
                "Spiritual Lessons & Practical Applications",
                "Auto-Installation of Dependencies",
                "Cross-Platform Terminal Support"
            ]
        },
        "File Type Checker.py": {
            "Description": "Advanced file security analysis tool that detects malware, steganography, and suspicious content. Features magic byte detection, entropy analysis, VirusTotal integration, metadata extraction, and automatic quarantine. Handles files up to 50GB with smart buffering to avoid memory overload. Perfect for analyzing downloads and unknown files.",
            "How to Use": "1. Place files in ~/Downloads/File Type Checker folder. 2. Run script. 3. View detailed security reports for each file. 4. Risky files are automatically quarantined.",
            "Save Location": "Scan folder: ~/Downloads/File Type Checker/ | Quarantined files: .dangerous extension",
            "Requirements": "rich, requests, exifread libraries (auto-installed), internet for VirusTotal.",
            "Tips": "Set VIRUSTOTAL_API_KEY in script for cloud scanning. Large files analyzed via head/tail sampling.",
            "Features": [
                "Magic Byte & File Signature Detection",
                "Entropy Analysis for Encryption/Packing Detection",
                "VirusTotal Cloud Scanning Integration",
                "Steganography Detection (Hidden Data in Images)",
                "Metadata Extraction (EXIF, GPS, etc.)",
                "String Pattern Matching (IPs, Emails, Malware Signatures)",
                "PE Header Analysis for Executables",
                "PDF/Office Macro Detection",
                "Automatic Quarantine of Risky Files",
                "Smart Buffering for Large Files (up to 50GB)",
                "Rich Terminal Interface with Color-Coded Reports"
            ]
        }
    },
    
    "Mods": {
        "URL Masker.py": {
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
        "Loading Screen Manager.py": {
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
        },
        "Password Master.py": {
            "Description": "A comprehensive password management suite with encrypted vault, password generator, analyzer, and improver. Features military-grade encryption (PBKDF2 + Fernet), zxcvbn strength analysis, and clipboard integration. Includes password generation with passphrases, strength improvement tools, and secure vault management with export/backup capabilities.",
            "How to Use": "1. Run script. 2. Set master password for vault (first time). 3. Choose Vault (store passwords) or Security Tools (generate/analyze). 4. Follow menu prompts.",
            "Save Location": "Vault: my_vault.enc in script directory | Backups: ~/Downloads/Password Master Backup/",
            "Requirements": "colorama, zxcvbn, cryptography libraries (auto-installed).",
            "Tips": "Use a strong master password and backup vault regularly. Passphrase generator creates memorable but strong passwords.",
            "Features": [
                "Encrypted Password Vault with Master Password",
                "Password Generator (Random & Passphrase)",
                "Password Strength Analyzer (zxcvbn algorithm)",
                "Password Improver Tool",
                "Clipboard Integration for Secure Copying",
                "Vault Management (Add, Search, Delete, Export)",
                "Automatic Dependency Installation",
                "Cross-Platform (Termux, Linux, Windows)",
                "Backup/Restore Functionality"
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
            "Description": "Phishing Tool. Hosts a fake Facebook login page promoting 'Connect with friends'. Captures credentials. Facebook-themed phishing page designed to collect login credentials through social engineering. Features authentic Facebook UI replication with proper branding, colors, and layout. Creates convincing login interface that captures usernames and passwords, then redirects with realistic loading animation. Automatically generates public access links via cloudflare tunneling.",
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
            "Description": "Phishing Tool. Hosts a fake Snapchat login page promising '100+ Friends'. Captures credentials. Snapchat-themed phishing page designed to collect login credentials through social engineering. Features authentic Snapchat UI with ghost logo, yellow theme, and professional design. Promises instant friends addition to lure users into entering credentials. Automatically generates public access links via cloudflare tunneling.",
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
            "Description": "Phishing Tool. Hosts a fake Google page offering a '$500 Credit'. Captures Google credentials. Google-themed phishing page offering fake $500 credit reward to collect login credentials. Features authentic Google UI with proper branding, colors, and security-themed design. Uses reward psychology to trick users into entering credentials. Automatically generates public access links via cloudflare tunneling.",
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
            "Description": "Phishing Tool. Hosts a fake Instagram login page promising 'Free Followers'. Captures credentials. Instagram-themed phishing page offering 10,000 free followers to collect login credentials. Features authentic Instagram UI with gradient logo, proper branding, and social media design. Uses follower growth promise to lure users into entering credentials. Automatically generates public access links via cloudflare tunneling.",
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
        "Fake TikTok Followers Page.py": {
            "Description": "Phishing Tool. Hosts a fake TikTok login page promising '5000 Free Followers'. Captures credentials. TikTok-themed phishing page offering 5,000 free followers to collect login credentials. Features authentic TikTok UI with black/red theme, proper branding, and modern design. Uses follower growth promise and social proof to lure users into entering credentials. Automatically generates public access links via cloudflare tunneling.",
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
        "What's Up Dude Page.py": {
            "Description": "Phishing Tool. Hosts a fake WhatsApp-style login page. Captures credentials. Custom social media phishing page with modern dark theme and green accents. Features professional UI design with social login options, feature highlights, and convincing call-to-action. Uses connection psychology to lure users into entering credentials. Automatically generates public access links via cloudflare tunneling.",
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

def format_list_item(name, category_name=""):
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
    elif "Websites" in name:
        icon = "🌐"
    elif "Sod" in name:
        icon = "⚡"
    elif "File Converter" in name:
        icon = "🔄"
    elif "Dark" in name:
        icon = "🌑"
    elif "AI" in name:
        icon = "🤖"
    elif "Truth" in name:
        icon = "📖"
    elif "File Type Checker" in name:
        icon = "🔍"
    elif "Password" in name:
        icon = "🔒"
    
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
            
            display_text = format_list_item(tool_name, category_name)
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