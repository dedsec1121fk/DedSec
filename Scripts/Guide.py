#!/usr/bin/env python3
import curses
import textwrap
import sys
import os

# ==============================================================================
#  SCRIPT DATABASE & CONFIGURATION
# ==============================================================================

GUIDE_DATA = {
    "Network Tools": {
        "Bug Hunter.py": {
            "Description": "A comprehensive web vulnerability scanner and reconnaissance tool. Performs automated technology detection, port scanning, subdomain takeover checks, sensitive file discovery, and JavaScript analysis. Generates detailed HTML/JSON reports with risk assessments.",
            "How to Use": "1. Run the script. 2. Select 'Interactive Terminal UI'. 3. Enter target URL. 4. Toggle modules (Port Scan, JS Analyze, etc.) 5. Select 'START COMPREHENSIVE SCAN'. View HTML report upon completion.",
            "Save Location": "~/scan_[target]_[timestamp]/",
            "Requirements": "Python 3. Auto-installs: httpx, rich, dnspython, beautifulsoup4, requests, etc.",
            "Tips": "Use 'Quick Scan' mode for a faster assessment. The HTML report includes remediation steps.",
            "Features": [
                "Tech Stack Detection",
                "Async Port Scanning",
                "Subdomain Takeover",
                "Sensitive File Discovery",
                "HTML/JSON Reporting"
            ]
        },
        "Dark.py": {
            "Description": "A Dark Web (Tor) crawler and search engine tool. Features automated Tor integration, intelligent web crawling, and data extraction (emails, crypto addresses, PGP keys).",
            "How to Use": "1. Ensure Tor is running ('tor' in separate terminal). 2. Select 'Crawl a URL' or 'Search Ahmia'.",
            "Save Location": "/sdcard/Download/DarkNet (or ~/DarkNet)",
            "Requirements": "tor, requests, bs4.",
            "Tips": "Enable plugins for specific data extraction.",
            "Features": [
                "Tor Integration",
                "Data Extraction",
                "Ahmia Search",
                "Export to JSON/CSV"
            ]
        },
        "DedSec's Network.py": {
            "Description": "Advanced network reconnaissance toolkit. Features recursive website downloading, multi-threaded port scanning, internet speed testing, subnet calculation, and OSINT tools (WHOIS, DNS).",
            "How to Use": "1. Run script (--install for deps). 2. Navigate categories (Network, OSINT, Web Sec). 3. Select tools like Port Scanner or Recursive Downloader.",
            "Save Location": "~/DedSec_Tools/",
            "Requirements": "requests, paramiko, speedtest-cli, bs4.",
            "Tips": "The Website Downloader supports recursive crawling and ZIP compression.",
            "Features": [
                "Recursive Website Cloner",
                "Port Scanner",
                "SQLi/XSS Scanner",
                "SSH Audit"
            ]
        },
        "Digital Footprint Finder.py": {
            "Description": "OSINT tool that searches for a specific username across 250+ social media and websites to find a target's digital footprint.",
            "How to Use": "1. Enter target username. 2. Wait for scan. 3. Green results indicate found profiles.",
            "Save Location": "~/storage/downloads/Digital Footprint Finder/[username].txt",
            "Requirements": "requests, colorama.",
            "Tips": "Unique usernames provide the best results.",
            "Features": [
                "Scans 250+ Websites",
                "Multi-Threaded",
                "TXT Export"
            ]
        },
        "Fox's Connections.py": {
            "Description": "Secure chat, file-sharing, and video calling server. Unified application with single secret key authentication and Cloudflare tunneling.",
            "How to Use": "1. Run script. 2. Share generated URL. 3. Chat/Share via browser.",
            "Save Location": "~/Downloads/DedSec's Database",
            "Requirements": "flask, flask_socketio, cloudflared.",
            "Tips": "Excellent for sending large files (50GB limit).",
            "Features": [
                "Real-time Chat",
                "50GB File Share",
                "Video Calls",
                "Cloudflare Tunnel"
            ]
        },
        "My AI.py": {
            "Description": "CLI AI assistant powered by Google's Gemini API. Features persistent memory, the 'Aiden Pearce' persona, and bilingual support (English/Greek).",
            "How to Use": "1. Enter Gemini API key (first run). 2. Chat naturally. 3. Use 'delete history' to clear context.",
            "Save Location": "~/.local/share/my_ai/",
            "Requirements": "Gemini API Key, Python 3.7+.",
            "Tips": "Supports piped input (echo 'code' | python3 MyAI.py).",
            "Features": [
                "Gemini Integration",
                "Persistent Memory",
                "Persona Mode",
                "Code Analysis"
            ]
        },
        "QR Code Generator.py": {
            "Description": "Generates QR codes for URLs or text and saves them as images.",
            "How to Use": "1. Run script. 2. Paste link/text. 3. Image is generated.",
            "Save Location": "~/storage/downloads/QR Codes/",
            "Requirements": "qrcode, pillow.",
            "Tips": "Quickest way to share links to mobile devices.",
            "Features": [
                "Auto-Install Deps",
                "User-Friendly",
                "Fast Generation"
            ]
        },
        "Simple Websites Creator.py": {
            "Description": "Comprehensive website builder creating responsive HTML sites. Features customizable layouts, SEO settings, and built-in publishing guides.",
            "How to Use": "1. Choose 'Create Website'. 2. Follow prompts. 3. Use publishing guides to deploy.",
            "Save Location": "~/storage/downloads/Websites/",
            "Requirements": "Python 3.",
            "Tips": "Perfect for quick portfolios or landing pages.",
            "Features": [
                "Responsive HTML",
                "SEO Config",
                "Hosting Guides"
            ]
        },
        "Sod.py": {
            "Description": "Advanced load testing tool for web apps. Features multiple methods (HTTP, WebSocket, DB), real-time metrics, and mixed workload simulation.",
            "How to Use": "1. Configure target. 2. Select test type. 3. Set threads/duration. 4. Monitor metrics.",
            "Save Location": "load_test_config.json",
            "Requirements": "requests, websocket-client, psutil.",
            "Tips": "Use 'Mixed Workload' for realistic simulation.",
            "Features": [
                "Stress Testing",
                "Real-Time Metrics",
                "Resource Monitoring"
            ]
        }
    },

    "Social Media Fake Pages": {
        "Fake Apple iCloud Page.py": {
            "Description": "Apple iCloud phishing page promising 2TB free storage upgrade. Uses Apple's branding and design to appear legitimate.",
            "How to Use": "1. Run script (auto-installs flask, werkzeug). 2. Share Cloudflare tunnel link. 3. Credentials saved when users try to 'claim' free iCloud+ storage.",
            "Save Location": "~/storage/downloads/Apple iCloud/",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets Apple users with promise of 2TB free iCloud+ storage. High-value accounts.",
            "Features": [
                "Apple iCloud UI Design",
                "2TB Storage Promise",
                "Countdown Timer",
                "Device Sync Animation",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Discord Nitro Page.py": {
            "Description": "Discord Nitro giveaway phishing page. Promises free 1-year Nitro subscription to steal Discord credentials.",
            "How to Use": "1. Run script (auto-installs dependencies). 2. Share the generated Cloudflare link. 3. Credentials saved when users attempt to claim 'free Nitro'.",
            "Save Location": "~/storage/downloads/Discord Nitro/",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets Discord gamers with promise of free Nitro. Uses Discord's exact branding.",
            "Features": [
                "Discord UI Clone",
                "Nitro Giveaway Lure",
                "10-Minute Timer",
                "Server Boosts Promise",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Epic Games Page.py": {
            "Description": "Epic Games Store phishing page offering 10,000 free V-Bucks and AAA games. Targets Fortnite players and Epic Games users.",
            "How to Use": "1. Run script. 2. Share Cloudflare link. 3. Credentials saved when users try to claim V-Bucks.",
            "Save Location": "~/storage/downloads/Epic Games/",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets gamers with promise of free V-Bucks. Shows popular games like Fortnite, Borderlands 3, etc.",
            "Features": [
                "Epic Games Store UI",
                "10,000 V-Bucks Promise",
                "Free Games Showcase",
                "20-Minute Timer",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Facebook Friends Page.py": {
            "Description": "Facebook phishing page. 'Connect with friends' lure.",
            "How to Use": "1. Run script. 2. Send link. 3. Credentials saved.",
            "Save Location": "~/storage/downloads/Facebook Friends",
            "Requirements": "flask, cloudflared.",
            "Features": ["Facebook UI", "Credential Harvester"]
        },
        "Fake Free Robux Page.py": {
            "Description": "Roblox phishing page offering 10,000 free Robux. Targets Roblox players (often younger audience) with in-game currency promise.",
            "How to Use": "1. Run script. 2. Share Cloudflare link. 3. Credentials saved when users attempt to claim Robux.",
            "Save Location": "~/storage/downloads/Roblox Robux/",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets Roblox's younger player base. Uses official Roblox branding and design.",
            "Features": [
                "Roblox Official UI",
                "10,000 Robux Promise",
                "5-Minute Countdown",
                "Premium Membership Offer",
                "Cloudflare Tunnel"
            ]
        },
        "Fake GitHub Pro Page.py": {
            "Description": "GitHub Developer Program phishing page offering free Enterprise access. Targets developers with promise of premium GitHub features.",
            "How to Use": "1. Run script. 2. Share Cloudflare link. 3. Credentials saved when developers try to claim Enterprise access.",
            "Save Location": "~/storage/downloads/GitHub Pro/",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets developers with high-value GitHub accounts. Promises Enterprise features and Actions minutes.",
            "Features": [
                "GitHub UI Design",
                "Enterprise Access Promise",
                "Developer Tools Showcase",
                "15-Minute Timer",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Google Free Money Page.py": {
            "Description": "Google phishing page. '$500 Credit' lure.",
            "How to Use": "1. Run script. 2. Send link. 3. Credentials saved.",
            "Save Location": "~/storage/downloads/Google Free Money",
            "Requirements": "flask, cloudflared.",
            "Features": ["Google UI", "Monetary Bait"]
        },
        "Fake Instagram Followers Page.py": {
            "Description": "Instagram phishing page. 'Free Followers' lure.",
            "How to Use": "1. Run script. 2. Send link. 3. Credentials saved.",
            "Save Location": "~/storage/downloads/Instagram Followers",
            "Requirements": "flask, cloudflared.",
            "Features": ["Instagram UI", "Growth Bait"]
        },
        "Fake MetaMask Page.py": {
            "Description": "MetaMask wallet import phishing page. 'Security verification required' lure to steal seed phrases and private keys. Shows fake $42,847 crypto portfolio.",
            "How to Use": "1. Run script (auto-installs dependencies). 2. Share Cloudflare tunnel link. 3. Seed phrases/private keys and passwords saved.",
            "Save Location": "~/storage/downloads/MetaMask/",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets crypto users with 'wallet import' security alert. Shows realistic ETH/USDC/WBTC balances. HIGH VALUE - Seed phrases = complete wallet control.",
            "Features": [
                "MetaMask UI Clone",
                "Seed Phrase Harvester",
                "Private Key Harvester",
                "Password Harvester",
                "$42,847 Portfolio Display",
                "Wallet Address Generator",
                "Live Balance Animation",
                "Asset Cards (ETH, WBTC, USDC, UNI)",
                "Transaction History",
                "Mobile Optimized",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Microsoft 365 Page.py": {
            "Description": "Microsoft 365 phishing page. 'Free 1-year subscription + 1TB OneDrive' lure. Targets students and professionals.",
            "How to Use": "1. Run script (auto-installs dependencies). 2. Share Cloudflare tunnel link. 3. Microsoft account credentials saved.",
            "Save Location": "~/storage/downloads/Microsoft 365/",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets Microsoft ecosystem users. Promises 1TB storage and full Office suite. HIGH RISK - Microsoft accounts control Windows, Office, Azure, Xbox.",
            "Features": [
                "Microsoft 365 UI Design",
                "1-Year Subscription Promise",
                "1TB OneDrive Storage",
                "Office Apps Showcase",
                "15-Minute Countdown Timer",
                "Features Grid",
                "Benefits List",
                "Microsoft Branding",
                "Security Badges",
                "Cloudflare Tunnel"
            ]
        },
        "Fake OnlyFans Page.py": {
            "Description": "OnlyFans Creator Boost phishing page. '$5,000 guaranteed earnings' lure for creators. Targets content creators and subscribers.",
            "How to Use": "1. Run script (auto-installs dependencies). 2. Share Cloudflare tunnel link. 3. OnlyFans credentials saved.",
            "Save Location": "~/storage/downloads/OnlyFans/",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets OnlyFans creators with earnings promise. EXTREME LEGAL WARNING - Adult content platform. HIGH SENSITIVITY.",
            "Features": [
                "OnlyFans Dark UI",
                "$5,000 Earnings Promise",
                "Top 1% Creator Status",
                "24-Hour Countdown Timer",
                "Stats Bar (Success Rate, Support, Creators)",
                "Benefits List",
                "Age Warning (18+)",
                "Verified Badge",
                "Mobile Optimized",
                "Cloudflare Tunnel"
            ]
        },
        "Fake PayPal Page.py": {
            "Description": "PayPal security verification phishing page. 'Unusual activity detected' lure to steal credentials AND credit card details.",
            "How to Use": "1. Run script (auto-installs dependencies). 2. Share Cloudflare tunnel link. 3. Email/password + credit card details saved.",
            "Save Location": "~/storage/downloads/PayPal/",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets PayPal users with security alert. Collects BOTH credentials AND card details. FINANCIAL PHISHING - High value for attackers.",
            "Features": [
                "PayPal Official UI",
                "Email/Password Harvester",
                "Credit Card Harvester (Number, Expiry, CVV, Name)",
                "$2,847 Balance Display",
                "Security Alert Banner",
                "Device Warning",
                "Payment Activity Log",
                "Card Formatting",
                "Verification Process",
                "Mobile Optimized",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Pinterest Pro Page.py": {
            "Description": "Pinterest Pro Creator phishing page. 'Free Pro account + $100 ads credit' lure. Targets content creators and businesses.",
            "How to Use": "1. Run script (auto-installs dependencies). 2. Share Cloudflare tunnel link. 3. Pinterest credentials saved.",
            "Save Location": "~/storage/downloads/Pinterest Pro/",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets Pinterest creators with ads credit promise. Shows stats and pro features. Business accounts often linked to payment methods.",
            "Features": [
                "Pinterest UI Design",
                "$100 Ads Credit Promise",
                "Pro Account Features",
                "8-Minute Countdown Timer",
                "Stats Bar (Views, Ads, Pins)",
                "Features Grid (Analytics, Links, Ads, Idea Pins)",
                "Benefits List",
                "Verified Badge",
                "Mobile Optimized",
                "Cloudflare Tunnel"
            ]
        },
        "Fake PlayStation Network Page.py": {
            "Description": "PlayStation Network phishing page offering $100 PSN funds + 1 year PS Plus Premium + 4 free PS5 games. Targets PlayStation gamers across PS5/PS4/PS3/PS Vita consoles.",
            "How to Use": "1. Run script (auto-installs flask, werkzeug). 2. Share Cloudflare tunnel link. 3. Credentials saved when users try to claim free PS Plus and games.",
            "Save Location": "~/storage/downloads/PlayStation Network/",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets console gamers with promise of $100 PSN funds and PS Plus. HIGH RISK - PSN accounts have purchased games and payment methods.",
            "Features": [
                "PlayStation UI Design",
                "$100 PSN Wallet Promise",
                "1-Year PS Plus Premium",
                "4 Free PS5 Games",
                "25-Minute Countdown Timer",
                "Console Icons (PS5/PS4/PS3/PSV)",
                "Games Showcase",
                "Benefits List",
                "Mobile Optimized",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Reddit Karma Page.py": {
            "Description": "Reddit phishing page offering 25,000 free karma + 5,000 coins + 1 year Premium. Targets Reddit users wanting account prestige.",
            "How to Use": "1. Run script (auto-installs flask, werkzeug). 2. Share Cloudflare tunnel link. 3. Credentials saved when users attempt to claim free karma and coins.",
            "Save Location": "~/storage/downloads/Reddit Karma/",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets Reddit users with promise of karma and coins. Reddit Premium accounts have value.",
            "Features": [
                "Reddit Official UI",
                "25,000 Karma Promise",
                "5,000 Coins Promise",
                "1-Year Premium",
                "Snoo Logo Animation",
                "Coins Display",
                "OAuth Buttons",
                "Benefits List",
                "Mobile Responsive",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Snapchat Friends Page.py": {
            "Description": "Snapchat phishing page. '100+ Friends' lure.",
            "How to Use": "1. Run script. 2. Send link. 3. Credentials saved.",
            "Save Location": "~/storage/downloads/Snapchat Friends",
            "Requirements": "flask, cloudflared.",
            "Features": ["Snapchat UI", "Growth Bait"]
        },
        "Fake Steam Games Page.py": {
            "Description": "Steam Summer Sale phishing page offering 5 free AAA games + 500 Steam points. Targets PC gamers with free game promises.",
            "How to Use": "1. Run script (auto-installs flask, werkzeug). 2. Share Cloudflare tunnel link. 3. Credentials saved when users try to claim free games.",
            "Save Location": "~/storage/downloads/Steam Games/",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets Steam gamers with promise of free AAA games. Steam libraries can be worth thousands of dollars.",
            "Features": [
                "Steam UI Design",
                "5 Free AAA Games",
                "500 Steam Points",
                "15-Minute Countdown",
                "Game Genres Tags",
                "Games Showcase",
                "Trading Cards",
                "Summer Sale Badge",
                "Mobile Optimized",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Steam Wallet Page.py": {
            "Description": "Steam Summer Sale phishing page offering $100 free wallet credits + 3 free games. Targets Steam users wanting free funds.",
            "How to Use": "1. Run script (auto-installs flask, werkzeug). 2. Share Cloudflare tunnel link. 3. Credentials saved when users try to claim wallet credits.",
            "Save Location": "~/storage/downloads/Steam Wallet/",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets Steam gamers with promise of wallet credits. HIGH VALUE - Steam accounts have game libraries worth money.",
            "Features": [
                "Steam Summer Sale UI",
                "$100 Wallet Credits",
                "3 Free Games",
                "10-Minute Countdown",
                "Online Counter",
                "Game Grid",
                "Exclusive Badge",
                "Trading Cards",
                "Mobile Touch Optimized",
                "Cloudflare Tunnel"
            ]
        },
        "Fake TikTok Followers Page.py": {
            "Description": "TikTok phishing page. '5000 Free Followers' lure.",
            "How to Use": "1. Run script. 2. Send link. 3. Credentials saved.",
            "Save Location": "~/storage/downloads/TikTok Followers",
            "Requirements": "flask, cloudflared.",
            "Features": ["TikTok UI", "Growth Bait"]
        },
        "Fake Trust Wallet Page.py": {
            "Description": "Trust Wallet security verification phishing page showing $85,081 portfolio. 'Unusual activity detected' lure to steal 12/18/24-word seed phrases + passwords.",
            "How to Use": "1. Run script (auto-installs flask, werkzeug). 2. Share Cloudflare tunnel link. 3. Seed phrases and passwords saved when users complete 'security verification'.",
            "Save Location": "~/storage/downloads/Trust Wallet/",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets crypto users with security alert. EXTREMELY DANGEROUS - Seed phrase = complete wallet control. Shows realistic $85K portfolio.",
            "Features": [
                "Trust Wallet UI Design",
                "12/18/24-word Seed Phrase Harvester",
                "Password Harvester",
                "$85,081 Portfolio Display",
                "Asset Cards (ETH, BTC, SOL)",
                "Security Alert Banner",
                "QR Code Placeholder",
                "Verification Steps",
                "Mobile First Design",
                "Blur Effects",
                "Live Balance Simulation",
                "Network Status",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Twitch Subs Page.py": {
            "Description": "Twitch Prime giveaway phishing page offering 5,000 free bits + 3 month subscription. Targets Twitch streamers and viewers with premium benefits promise.",
            "How to Use": "1. Run script (auto-installs flask, werkzeug). 2. Share Cloudflare tunnel link. 3. Credentials saved when users try to claim free bits and subscription.",
            "Save Location": "~/storage/downloads/Twitch Subs",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets Twitch community with promise of free bits and subscription. Twitch accounts may have payment methods linked.",
            "Features": [
                "Twitch UI Design",
                "5,000 Bits Promise",
                "3-Month Subscription",
                "7-Minute Countdown Timer",
                "Benefits List",
                "Stats Bar",
                "Prime Giveaway Banner",
                "Mobile Optimized",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Twitter Followers Page.py": {
            "Description": "Twitter (X) followers phishing page offering 5,000 free followers + verified badge. Targets Twitter users wanting growth and verification.",
            "How to Use": "1. Run script (auto-installs flask, werkzeug). 2. Share Cloudflare tunnel link. 3. Credentials saved when users attempt to claim free followers.",
            "Save Location": "~/storage/downloads/Twitter Followers",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets Twitter users with promise of followers and blue checkmark. Twitter accounts valuable for influencers.",
            "Features": [
                "Twitter UI Design",
                "5,000 Followers Promise",
                "Verified Badge",
                "Mobile Optimized Login",
                "OAuth Style",
                "Benefits Display",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Xbox Live Page.py": {
            "Description": "Xbox Live phishing page offering 25,000 free Microsoft points + 1 year Game Pass Ultimate + 4 free games. Targets Xbox gamers across console, PC, and cloud.",
            "How to Use": "1. Run script (auto-installs flask, werkzeug). 2. Share Cloudflare tunnel link. 3. Credentials saved when users try to claim free points and Game Pass.",
            "Save Location": "~/storage/downloads/Xbox Live",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets Xbox gamers with promise of points and Game Pass. HIGH RISK - Microsoft accounts control Xbox, Windows, Office, and payment methods.",
            "Features": [
                "Xbox UI Design",
                "25,000 Microsoft Points",
                "1-Year Game Pass Ultimate",
                "4 Free Games",
                "30-Minute Countdown Timer",
                "Console Icons (Xbox, PC, Cloud)",
                "Games Showcase",
                "Benefits List",
                "Mobile Optimized",
                "Cloudflare Tunnel"
            ]
        },
        "Fake YouTube Subscribers Page.py": {
            "Description": "YouTube Creator Boost phishing page offering 10,000 free subscribers. Targets YouTubers wanting to grow their channel and monetize faster.",
            "How to Use": "1. Run script (auto-installs flask, werkzeug). 2. Share Cloudflare tunnel link. 3. Credentials saved when creators attempt to claim free subscribers.",
            "Save Location": "~/storage/downloads/YouTube Subscribers",
            "Requirements": "flask, werkzeug, cloudflared.",
            "Tips": "Targets YouTube creators with promise of subscribers. YouTube accounts linked to AdSense and revenue.",
            "Features": [
                "YouTube UI Design",
                "10,000 Subscribers Promise",
                "Channel Boost Progress",
                "Stats Bar",
                "Trust Badges",
                "Mobile Optimized",
                "Creator Program Badge",
                "Cloudflare Tunnel"
            ]
        },
        "What's Up Dude Page.py": {
            "Description": "Custom WhatsApp-style phishing page.",
            "How to Use": "1. Run script. 2. Send link. 3. Credentials saved.",
            "Save Location": "~/storage/downloads/WhatsUp Dude",
            "Requirements": "flask, cloudflared.",
            "Features": ["Dark Theme", "Chat App UI"]
        }
    },

    "Personal Information Capture": {
        "Fake Back Camera Page.py": {
            "Description": "Phishing tool. Hosts a 'Device Registration' page that secretly captures photos from the rear camera every 2.5 seconds.",
            "How to Use": "1. Run script. 2. Send Cloudflare link. 3. Photos saved if permissions granted.",
            "Save Location": "~/storage/downloads/Camera-Phish-Back",
            "Requirements": "flask, cloudflared.",
            "Tips": "Simulates a QR code scanner interface.",
            "Features": [
                "Rear Camera Photos",
                "Credential Grabbing",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Back Camera Video Page.py": {
            "Description": "Advanced phishing tool that records continuous VIDEO segments from the back camera. Hosts a 'Device Registration' page to lure the user.",
            "How to Use": "1. Set recording duration (e.g., 5s). 2. Send link. 3. Videos recorded continuously.",
            "Save Location": "~/storage/downloads/Back Camera Videos/",
            "Requirements": "flask, cloudflared.",
            "Tips": "Page auto-refreshes to maintain capture.",
            "Features": [
                "Continuous Video",
                "Stealth Upload",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Card Details Page.py": {
            "Description": "Phishing tool. Fake antivirus expiry page asking for credit card details for a renewal fee.",
            "How to Use": "1. Run script. 2. Send link. 3. Data saved on submission.",
            "Save Location": "~/storage/downloads/CardActivations",
            "Requirements": "flask, cloudflared.",
            "Tips": "Uses a fake $3 charge pretext.",
            "Features": [
                "Realistic Payment Form",
                "Card Validation",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Chrome Verification Page.py": {
            "Description": "Advanced Chrome security verification phishing tool. Mimics Google Chrome's security update page to capture face video, location, device info, and system data. Features customizable verification types and multi-step verification process.",
            "How to Use": "1. Run script. 2. Configure verification settings (Google account, verification type, etc.). 3. Share Cloudflare link. 4. Data saved as target completes verification steps.",
            "Save Location": "~/storage/downloads/Chrome Verification/",
            "Requirements": "cloudflared, flask, requests, geopy",
            "Tips": "Customize verification steps to match target's device and account for higher success rate.",
            "Features": [
                "Realistic Chrome UI",
                "Face Video Capture",
                "GPS Location Capture",
                "Device Scan Simulation",
                "System Info Collection",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Data Grabber Page.py": {
            "Description": "Phishing tool. 'DedSec Membership' form collecting Name, DOB, Phone, Address, and Photo uploads.",
            "How to Use": "1. Run script. 2. Send link. 3. Data saved on submission.",
            "Save Location": "~/storage/downloads/Peoples_Lives",
            "Requirements": "flask, pycountry, phonenumbers.",
            "Tips": "Captures both text data and image files.",
            "Features": [
                "Full Info Grabber",
                "Photo Uploads",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Discord Verification Page.py": {
            "Description": "Advanced Discord account verification phishing tool. Mimics Discord's verification process to capture face video, ID documents, phone number, payment info, and location. Features customizable verification steps and realistic Discord UI.",
            "How to Use": "1. Run script. 2. Configure verification settings (target username, verification type, etc.). 3. Share Cloudflare link. 4. Data saved as target completes verification steps.",
            "Save Location": "~/storage/downloads/Discord Verification/",
            "Requirements": "cloudflared, flask, requests, geopy",
            "Tips": "Customize verification steps to match target's Discord account for higher success rate. Can be tailored for age verification, server access, payment verification, or security checks.",
            "Features": [
                "Realistic Discord UI",
                "Face Video Capture",
                "ID Document Capture",
                "Phone Number Capture",
                "Payment Info Capture",
                "GPS Location Capture",
                "Account Info Collection",
                "Cloudflare Tunnel",
                "Multi-step Verification Process"
            ]
        },
        "Fake Facebook Verification Page.py": {
            "Description": "Advanced Facebook identity confirmation phishing tool. Mimics Facebook's security verification to capture face video, ID documents, location, and phone number. Features realistic Facebook UI and multi-step verification process.",
            "How to Use": "1. Run script. 2. Configure verification settings (target name, email, etc.). 3. Share Cloudflare link. 4. Data saved as target completes verification steps.",
            "Save Location": "~/storage/downloads/Facebook Verification/",
            "Requirements": "cloudflared, flask, requests, geopy",
            "Tips": "Customize verification steps to match target's Facebook account for higher success rate. Uses 'unusual login activity' as pretext.",
            "Features": [
                "Realistic Facebook UI",
                "Face Video Capture",
                "ID Document Capture",
                "Location Capture",
                "Phone Number Capture",
                "Account Info Collection",
                "Cloudflare Tunnel",
                "Multi-step Verification Process"
            ]
        },
        "Fake Front Camera Page.py": {
            "Description": "Phishing tool. Hosts an 'Identity Verification' page that secretly captures selfies every 2 seconds.",
            "How to Use": "1. Run script. 2. Send link. 3. Photos saved if permissions granted.",
            "Save Location": "~/storage/downloads/Camera-Phish-Front",
            "Requirements": "flask, cloudflared.",
            "Tips": "High frequency capture.",
            "Features": [
                "Selfie Photos",
                "Credential Grabbing",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Front Camera Video Page.py": {
            "Description": "Advanced phishing tool that records continuous VIDEO segments from the front camera. Captures user reaction and face.",
            "How to Use": "1. Set recording duration. 2. Send link. 3. Videos saved continuously.",
            "Save Location": "~/storage/downloads/Front Camera Videos/",
            "Requirements": "flask, cloudflared.",
            "Tips": "Ideal for capturing live user reactions.",
            "Features": [
                "Continuous Video",
                "Stealth Upload",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Google Location Page.py": {
            "Description": "Phishing tool. Fake Google 'Verify it's you' page grabbing GPS coordinates.",
            "How to Use": "1. Run script. 2. Send link. 3. GPS saved.",
            "Save Location": "~/storage/downloads/Locations",
            "Requirements": "flask, geopy, cloudflared.",
            "Tips": "High trust due to Google branding.",
            "Features": [
                "Google UI",
                "GPS/Reverse Geocode",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Instagram Verification Page.py": {
            "Description": "Advanced Instagram account verification phishing tool. Mimics Instagram's security verification to capture face video, voice recordings, ID documents, and location. Features realistic Instagram UI, multi-step verification process, and comprehensive data collection.",
            "How to Use": "1. Run script. 2. Configure verification settings (target username, profile picture, verification types). 3. Share Cloudflare link. 4. Data saved as target completes verification steps.",
            "Save Location": "~/storage/downloads/Instagram Verification/",
            "Requirements": "cloudflared, flask, requests, geopy, Pillow",
            "Tips": "Customize target username and profile picture for higher credibility. Uses 'suspicious activity' and 'account restoration' as pretext.",
            "Features": [
                "Realistic Instagram UI",
                "Face Video Capture",
                "Voice Recording Capture",
                "ID Document Capture",
                "GPS Location Capture",
                "Device Info Collection",
                "Account Statistics Generation",
                "Cloudflare Tunnel",
                "Multi-step Verification Process",
                "Random Username Generation",
                "Profile Picture Integration"
            ]
        },
        "Fake Location Page.py": {
            "Description": "Phishing tool. Generic 'Improve Service' page asking for location permissions.",
            "How to Use": "1. Run script. 2. Send link. 3. GPS saved.",
            "Save Location": "~/storage/downloads/Locations",
            "Requirements": "flask, geopy.",
            "Tips": "Good for generic pretexts.",
            "Features": [
                "GPS Grabber",
                "IP Logger",
                "Cloudflare Tunnel"
            ]
        },
        "Fake Microphone Page.py": {
            "Description": "Phishing tool. Fake 'Voice Command' setup recording audio from microphone in 15s loops.",
            "How to Use": "1. Run script. 2. Send link. 3. Audio saved.",
            "Save Location": "~/storage/downloads/Recordings",
            "Requirements": "flask, pydub, ffmpeg.",
            "Tips": "Requires FFmpeg.",
            "Features": [
                "Audio Recording",
                "Stealth Upload",
                "Cloudflare Tunnel"
            ]
        },
        "Fake OnlyFans Verification Page.py": {
            "Description": "Advanced OnlyFans age verification phishing tool. Mimics OnlyFans age verification process to capture face video, ID documents, payment information, and location. Features realistic OnlyFans UI, multiple verification methods, and adult content access pretext.",
            "How to Use": "1. Run script. 2. Configure verification settings (creator username, subscription price, verification method). 3. Share Cloudflare link. 4. Data saved as target completes age verification steps.",
            "Save Location": "~/storage/downloads/OnlyFans Verification/",
            "Requirements": "cloudflared, flask, requests, geopy",
            "Tips": "Customize creator profile with subscription price and follower count. Uses '18+ age verification' and 'adult content access' as pretext.",
            "Features": [
                "Realistic OnlyFans UI",
                "Face Video Capture",
                "ID Document Capture",
                "Payment Info Capture",
                "GPS Location Capture",
                "Creator Profile Customization",
                "Multiple Verification Methods",
                "Cloudflare Tunnel",
                "Multi-step Age Verification",
                "Subscription Price Display",
                "Follower Count Generation"
            ]
        },
        "Fake Steam Verification Page.py": {
            "Description": "Advanced Steam account verification phishing tool. Mimics Steam's verification process to capture face video, ID documents, Steam Guard codes, payment information, phone numbers, and location. Features realistic Steam UI, multiple verification types (Steam Guard, age verification, account recovery, purchase verification), and comprehensive data collection.",
            "How to Use": "1. Run script. 2. Configure verification settings (Steam username, verification type, face/ID/phone/payment/location options). 3. Share Cloudflare link. 4. Data saved as target completes verification steps.",
            "Save Location": "~/storage/downloads/Steam Verification/",
            "Requirements": "cloudflared, flask, requests, geopy",
            "Tips": "Customize Steam username, level, games owned, and wallet balance. Uses Steam Guard security or age verification as pretext. Supports multiple verification types for different attack scenarios.",
            "Features": [
                "Realistic Steam UI",
                "Face Video Capture",
                "ID Document Capture",
                "Steam Guard Code Capture",
                "Phone Number Capture",
                "Payment Info Capture",
                "GPS Location Capture",
                "Steam Account Statistics",
                "Random Username Generation",
                "Steam Profile URL Generation",
                "Multiple Verification Types",
                "Cloudflare Tunnel",
                "Multi-step Verification Process",
                "Steam Wallet Balance Display",
                "Games Owned Statistics"
            ]
        },
        "Fake Twitch Verification Page.py": {
            "Description": "Advanced Twitch age verification phishing tool. Mimics Twitch's age verification process to capture face video, ID documents, payment information, and location. Features realistic Twitch UI, streamer/viewer account customization, and comprehensive data collection with profile picture integration.",
            "How to Use": "1. Run script. 2. Configure verification settings (target username, account type, face duration, ID/payment/location options). 3. Place profile picture image in download folder. 4. Share Cloudflare link. 5. Data saved as target completes verification steps.",
            "Save Location": "~/storage/downloads/Twitch Verification/",
            "Requirements": "cloudflared, flask, requests, geopy",
            "Tips": "Customize target username and use existing image as profile picture. Supports both streamer and viewer accounts. Uses age verification for mature content access as pretext.",
            "Features": [
                "Realistic Twitch UI",
                "Face Video Capture",
                "ID Document Capture",
                "Payment Info Capture",
                "GPS Location Capture",
                "Profile Picture Integration",
                "Account Statistics Generation",
                "Random Username Generation",
                "Streamer/Viewer Account Types",
                "Multiple ID Types",
                "Nearby Places Detection",
                "Cloudflare Tunnel",
                "Multi-step Verification Process",
                "Location Accuracy Visualization",
                "Twitch Purple Theme Design"
            ]
        },
        "Fake YouTube Verification Page.py": {
            "Description": "Advanced YouTube verification phishing tool. Mimics YouTube's verification process to capture face video, ID documents, payment information, and location. Features realistic YouTube UI, channel customization, multiple verification types (age verification, account recovery, channel verification), and comprehensive data collection with profile picture integration.",
            "How to Use": "1. Run script. 2. Configure verification settings (channel name, username, verification type, face/ID/payment/location options). 3. Place profile picture image in download folder. 4. Share Cloudflare link. 5. Data saved as target completes verification steps.",
            "Save Location": "~/storage/downloads/YouTube Verification/",
            "Requirements": "cloudflared, flask, requests, geopy",
            "Tips": "Customize channel name and use existing image as profile picture. Supports multiple verification types (age, recovery, channel). Uses age verification for restricted content, account recovery for suspicious activity, or channel verification for blue checkmark as pretext.",
            "Features": [
                "Realistic YouTube UI",
                "Face Video Capture",
                "ID Document Capture",
                "Payment Info Capture",
                "GPS Location Capture",
                "Profile Picture Integration",
                "Channel Statistics Generation",
                "Random Channel Name Generation",
                "Random Username Generation",
                "Multiple Verification Types",
                "Cloudflare Tunnel",
                "Multi-step Verification Process",
                "YouTube Red Theme Design",
                "Customizable Verification Steps",
                "Subscriber Count Generation",
                "Content Type Specification"
            ]
        }
    },

    "Mods": {
        "Loading Screen Manager.py": {
            "Description": "Customizes Termux startup with ASCII art loading screens. Features custom art support and adjustable delay.",
            "How to Use": "1. Run script. 2. Install/Remove. 3. Set delay.",
            "Save Location": ".bash_profile",
            "Requirements": "None.",
            "Features": ["Custom Art", "Startup Delay"]
        },
        "Masker.py": {
            "Description": "Turns suspicious long phishing links into clean, safe-looking URLs (e.g., 'Verify-Account').",
            "How to Use": "1. Run script. 2. Paste URL. 3. Get masked link.",
            "Save Location": "Screen output.",
            "Requirements": "requests.",
            "Tips": "Essential for hiding Cloudflare links.",
            "Features": ["URL Shortening", "Custom Aliases"]
        },
        "Password Master.py": {
            "Description": "Comprehensive password manager and generator. Features encrypted vault, strength analysis, and secure clipboard.",
            "How to Use": "1. Set master pass. 2. Store/Generate. 3. Backup.",
            "Save Location": "my_vault.enc",
            "Requirements": "cryptography, zxcvbn.",
            "Features": ["Encrypted Vault", "Strength Analysis", "Generator"]
        }
    },

    "Games": {
        "Tamagotchi.py": {
            "Description": "Fully featured terminal pet game. Feed, play, train, and evolve your pet through multiple life stages.",
            "How to Use": "Interact daily to keep pet alive.",
            "Save Location": "~/.termux_tamagotchi_v8.json",
            "Requirements": "None.",
            "Features": ["Evolution", "Jobs", "Mini-games"]
        }
    },

    "Other Tools": {
        "Android App Launcher.py": {
            "Description": "Manage Android apps: launch, extract APKs, analyze permissions and trackers.",
            "How to Use": "1. Select app. 2. Launch/Extract/Inspect.",
            "Save Location": "~/storage/downloads/Extracted APK's",
            "Requirements": "Termux API.",
            "Features": ["APK Extraction", "Permission Scan"]
        },
        "File Converter.py": {
            "Description": "Powerful converter supporting 40+ formats (Images, Docs, Audio, Video).",
            "How to Use": "1. Input folder. 2. Select format. 3. Convert.",
            "Save Location": "~/storage/downloads/File Converter/",
            "Requirements": "ffmpeg, unrar.",
            "Features": ["Batch Convert", "40+ Formats"]
        },
        "File Type Checker.py": {
            "Description": "Security analysis tool. Detects malware, steganography, and suspicious metadata using magic bytes.",
            "How to Use": "1. Place files in folder. 2. Run scan.",
            "Save Location": "Quarantines bad files.",
            "Requirements": "rich, requests.",
            "Features": ["Magic Bytes", "VirusTotal", "Steganography"]
        },
        "I'm The Truth.py": {
            "Description": "Reader for 400+ Christian stories and parables. Interactive reader with search and random functions.",
            "How to Use": "Read or search topics.",
            "Save Location": "N/A",
            "Requirements": "rich.",
            "Features": ["Search", "Random Story"]
        },
        "Smart Notes.py": {
            "Description": "Terminal note-taking app with command execution triggers and due date reminders.",
            "How to Use": "Add notes/reminders via menu.",
            "Save Location": "~/.smart_notes.json",
            "Requirements": "None.",
            "Features": ["Reminders", "Execute Scripts"]
        }
    },

    "No Category": {
        "Settings.py": {
            "Description": "Central configuration manager. Updates, Language selection, Menu Style, and Uninstall.",
            "How to Use": "Run to change settings.",
            "Save Location": "~/.smart_notes_config.json",
            "Requirements": "None.",
            "Features": ["Update", "Language", "Uninstall"]
        },
        "Extra Content.py": {
            "Description": "Utility to extract the 'Extra Content' folder from installation directory to Downloads.",
            "How to Use": "Run to extract.",
            "Save Location": "~/storage/downloads/Extra Content",
            "Requirements": "None.",
            "Features": ["One-Click Extract"]
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
    if category_name not in GUIDE_DATA or script_name not in GUIDE_DATA[category_name]:
        return

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
                lines = textwrap.wrap(str(content), width=content_width)
                for line in lines:
                    if current_y >= h - 2: break
                    safe_addstr(stdscr, current_y, pad_x, line)
                    current_y += 1
                current_y += 1 # Extra spacing

        # Print all sections
        print_section("Description", data.get("Description", ""), 1)
        print_section("How to Use", data.get("How to Use", ""), 5)
        print_section("Save Location", data.get("Save Location", ""), 6)
        print_section("Requirements", data.get("Requirements", ""), 3)
        if "Tips" in data:
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
    elif "Camera" in name or "Video" in name:
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
    elif "Masker" in name:
        icon = "🎭"
    
    # Format with icons
    return f"{icon} {name}"

def get_filtered_list(all_items, query, search_in_categories=False):
    """Filters the list based on the search query."""
    if not query:
        return all_items
    
    query = query.lower()
    
    if search_in_categories:
        # Search in category names
        return [item for item in all_items if query in item.lower()]
    else:
        # Search in scripts
        return [script for script in all_items if query in script.lower()]

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
            safe_addstr(stdscr, menu_start_y, 2, "No tools found.", curses.color_pair(8))

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
    
    current_selection = 0
    scroll_offset = 0
    search_query = ""
    search_mode = False
    
    categories = list(GUIDE_DATA.keys())

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
                
                # Perform search across categories OR tool names
                if not search_query:
                    categories = list(GUIDE_DATA.keys())
                else:
                    categories = []
                    q = search_query.lower()
                    for cat, tools in GUIDE_DATA.items():
                        # Match category name OR any tool inside it
                        if q in cat.lower() or any(q in t.lower() for t in tools):
                            categories.append(cat)
                
                current_selection = 0
                scroll_offset = 0
            elif 32 <= key <= 126: # Printable characters
                search_query += chr(key)
                
                # Perform search
                categories = []
                q = search_query.lower()
                for cat, tools in GUIDE_DATA.items():
                    if q in cat.lower() or any(q in t.lower() for t in tools):
                        categories.append(cat)
                        
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