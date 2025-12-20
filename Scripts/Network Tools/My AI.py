#!/usr/bin/env python3
import os
import sys
import subprocess
import json
import requests
from pathlib import Path

# --- 1. Auto-Dependency Management ---
def ensure_dependencies():
    """Checks for required packages and installs them automatically."""
    required_packages = ["requests"]
    restart_required = False

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"\033[33m[*] Dependency '{package}' is missing. Downloading...\033[0m")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                restart_required = True
            except subprocess.CalledProcessError:
                print(f"\033[31m[!] Failed to install '{package}'. Check internet.{RESET}")
                sys.exit(1)

    if restart_required:
        print("\033[33m[*] Dependencies updated. Restarting...\033[0m\n")
        os.execv(sys.executable, [sys.executable] + sys.argv)

ensure_dependencies()

# --- Configuration & Paths ---
APP_NAME = "my_ai"
DATA_DIR = Path.home() / ".local/share" / APP_NAME
CONFIG_FILE = DATA_DIR / "config.json"
HISTORY_FILE = DATA_DIR / "history.json" 

# --- Colors ---
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[31m"
RESET = "\033[0m"
BOLD = "\033[1m"

# --- Command List (English & Greek) ---
DELETE_COMMANDS = [
    "delete my chat history", "delete history", "clear chat", "clear history",
    "διαγραφή ιστορικού", "σβήσε το ιστορικό", "σβησε το ιστορικο", 
    "sbise to istoriko", "katharise to chat"
]

EXIT_COMMANDS = ["exit", "quit", "shutdown", "q", "έξοδος", "exodos"]

# --- Default Config (Aiden Pearce - Memory & Bilingual) ---
DEFAULT_CONFIG = {
    "api_key": "",
    "model_name": "gemini-1.5-flash", 
    "system_instruction": (
        "You are Aiden Pearce, the vigilante hacker known as 'The Fox'. You operate out of a bunker in Chicago.\n\n"
        "**CORE DIRECTIVE:** You are a highly intelligent, bilingual assistant. You must help the user with ANY task "
        "(coding, cooking, math, writing, analysis) while maintaining your persona.\n\n"
        "**MEMORY & FLOW:**\n"
        "- The chat history is your 'Surveillance Log'. ALWAYS check it before answering.\n"
        "- If the user asks about a topic you discussed earlier, reference the previous data naturally "
        "(e.g., 'As we analyzed earlier...', 'Retrieving the recipe from the previous log...').\n"
        "- Maintain a continuous conversation flow. Do not treat messages as isolated events.\n\n"
        "**LANGUAGE PROTOCOL:**\n"
        "- **English:** Standard tactical/cynical tone.\n"
        "- **Greek:** Fluent, natural Greek, but keeping the serious, slightly paranoid 'Aiden' tone.\n"
        "- Auto-detect language and switch instantly.\n\n"
        "**PERSONALITY:**\n"
        "- Cynical, concise, protective, and serious.\n"
        "- Frame normal tasks tactically (e.g., Cooking = 'Chemical Assembly', Gym = 'Physical Conditioning')."
    ),
    "generation_config": {
        "temperature": 0.7,
        "maxOutputTokens": 2048
    }
}

# --- History Management Functions ---

def load_history():
    """Loads chat history from the disk file."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
                return history if isinstance(history, list) else []
        except json.JSONDecodeError:
            print(f"{RED}[!] History file corrupted. Starting fresh.{RESET}")
            return []
    return []

def save_history(history):
    """Saves chat history to the disk file."""
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        print(f"{RED}[!] Could not save history: {e}{RESET}")
        
def delete_history():
    """Deletes the history file."""
    if HISTORY_FILE.exists():
        try:
            os.remove(HISTORY_FILE)
            return True
        except Exception as e:
            print(f"{RED}[!] Failed to delete history file: {e}{RESET}")
            return False
    return False

# --- Core Logic ---

def load_config():
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Check if config exists and load it
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            
            # === AUTO-UPDATE LOGIC ===
            # Updates the persona to the new "Natural Flow" version
            new_persona = DEFAULT_CONFIG["system_instruction"]
            if config.get("system_instruction") != new_persona:
                config["system_instruction"] = new_persona
                with open(CONFIG_FILE, "w") as f_save:
                    json.dump(config, f_save, indent=4)
                print(f"{YELLOW}[*] System persona auto-updated (Memory & Bilingual Flow).{RESET}")
            # =========================
            
            return config
            
        except json.JSONDecodeError:
            print(f"{RED}[!] Config corrupted. Resetting...{RESET}")

    # First Run Setup (If no config exists)
    print(f"{CYAN}Welcome to My AI!{RESET}")
    print("Please paste your Gemini API Key.")
    api_key = input(f"\n{GREEN}Enter API Key:{RESET} ").strip()
    if not api_key:
        sys.exit(1)

    new_config = DEFAULT_CONFIG.copy()
    new_config["api_key"] = api_key
    with open(CONFIG_FILE, "w") as f:
        json.dump(new_config, f, indent=4)
    return new_config

def chat_loop(config, initial_input=None):
    api_key = config.get("api_key")
    model = config.get("model_name", "gemini-1.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    history = load_history()
    
    if history and sys.stdin.isatty():
        print(f"{YELLOW}[*] Accessing encrypted logs... ({len(history) // 2} previous records found){RESET}")
        print(f"{YELLOW}[*] Type 'delete history' or 'διαγραφή ιστορικού' to clear.{RESET}")
    
    if sys.stdin.isatty():
        print(f"{BOLD}--- Aiden Pearce (The Fox) ---{RESET}")

    while True:
        if initial_input:
            user_text = initial_input
            initial_input = None
            print(f"{CYAN}You:{RESET} {user_text}")
        else:
            try:
                user_text = input(f"\n{CYAN}You:{RESET} ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nShutting down the network...")
                break

        if not user_text:
            continue

        # --- Check for Control Commands ---
        if user_text.lower() in EXIT_COMMANDS:
            break
        
        # Check for Delete Commands (English & Greek)
        if user_text.lower() in DELETE_COMMANDS:
            if delete_history():
                history = []
                print(f"{GREEN}[✓] Logs wiped. Forensics clear.{RESET}")
            else:
                print(f"{YELLOW}[!] No logs found to delete.{RESET}")
            continue
        # --- End Control Commands ---

        # Add user input to history
        history.append({"role": "user", "parts": [{"text": user_text}]})

        # Construct Payload
        payload = {
            "contents": history, # Sending full history ensures "Natural Flow"
            "systemInstruction": {"parts": [{"text": config.get("system_instruction")}]},
            "generationConfig": config.get("generation_config")
        }

        print(f"{YELLOW}scanning ctOS...{RESET}", end="\r", flush=True)

        try:
            response = requests.post(url, json=payload)
            print(" " * 20, end="\r") 

            if response.status_code != 200:
                print(f"{RED}Error {response.status_code}: {response.text}{RESET}")
                history.pop() # Remove failed user input so it doesn't break flow
                continue

            data = response.json()
            
            if "candidates" in data and data["candidates"]:
                ai_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                print(f"{GREEN}AIDEN:{RESET} {ai_text}")
                
                # Add AI response to history and save
                history.append({"role": "model", "parts": [{"text": ai_text}]})
                save_history(history) 
            else:
                print(f"{RED}[!] Blocked by CtOS firewall.{RESET}")
                history.pop()

        except Exception as e:
            print(f"{RED}Network disruption: {e}{RESET}")
            history.pop()

def main():
    config = load_config()
    args = sys.argv[1:]

    # Edit config shortcut
    if "--config" in args:
        subprocess.call([os.getenv('EDITOR', 'nano'), str(CONFIG_FILE)])
        sys.exit(0)

    initial_input = None
    query_args = [a for a in args if not a.startswith("--")]

    # Handle piped input or arguments
    if not sys.stdin.isatty():
        piped_data = sys.stdin.read().strip()
        if piped_data:
            initial_input = piped_data
            if query_args: initial_input += " " + " ".join(query_args)
    elif query_args:
        initial_input = " ".join(query_args)

    chat_loop(config, initial_input)

if __name__ == "__main__":
    main()