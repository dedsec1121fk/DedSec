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
        }
    },

    "Social Media Fake Pages": {
        "Fake Facebook Friends Page.py": {
            "Description": "Facebook phishing page. 'Connect with friends' lure.",
            "How to Use": "1. Run script. 2. Send link. 3. Credentials saved.",
            "Save Location": "~/storage/downloads/FacebookFriends",
            "Requirements": "flask, cloudflared.",
            "Features": ["Facebook UI", "Credential Harvester"]
        },
        "Fake Google Free Money Page.py": {
            "Description": "Google phishing page. '$500 Credit' lure.",
            "How to Use": "1. Run script. 2. Send link. 3. Credentials saved.",
            "Save Location": "~/storage/downloads/GoogleFreeMoney",
            "Requirements": "flask, cloudflared.",
            "Features": ["Google UI", "Monetary Bait"]
        },
        "Fake Instagram Followers Page.py": {
            "Description": "Instagram phishing page. 'Free Followers' lure.",
            "How to Use": "1. Run script. 2. Send link. 3. Credentials saved.",
            "Save Location": "~/storage/downloads/InstagramFollowers",
            "Requirements": "flask, cloudflared.",
            "Features": ["Instagram UI", "Growth Bait"]
        },
        "Fake Snapchat Friends Page.py": {
            "Description": "Snapchat phishing page. '100+ Friends' lure.",
            "How to Use": "1. Run script. 2. Send link. 3. Credentials saved.",
            "Save Location": "~/storage/downloads/SnapchatFriends",
            "Requirements": "flask, cloudflared.",
            "Features": ["Snapchat UI", "Growth Bait"]
        },
        "Fake TikTok Followers Page.py": {
            "Description": "TikTok phishing page. '5000 Free Followers' lure.",
            "How to Use": "1. Run script. 2. Send link. 3. Credentials saved.",
            "Save Location": "~/storage/downloads/TikTokFollowers",
            "Requirements": "flask, cloudflared.",
            "Features": ["TikTok UI", "Growth Bait"]
        },
        "What's Up Dude Page.py": {
            "Description": "Custom WhatsApp-style phishing page.",
            "How to Use": "1. Run script. 2. Send link. 3. Credentials saved.",
            "Save Location": "~/storage/downloads/WhatsUpDude",
            "Requirements": "flask, cloudflared.",
            "Features": ["Dark Theme", "Chat App UI"]
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