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

# --- Command List ---
DELETE_COMMANDS = [
    "delete my chat history", "delete history", "clear chat", "clear history",
    "διαγραφή ιστορικού", "σβήσε το ιστορικό", "σβησε το ιστορικο", 
    "sbise to istoriko", "katharise to chat"
]

EXIT_COMMANDS = ["exit", "quit", "shutdown", "q", "έξοδος", "exodos"]

# --- Fallback Models (Self-Healing Logic) ---
# If one fails with 404, the script will try the next one automatically.
KNOWN_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-002",
    "gemini-1.5-flash-8b",
    "gemini-2.0-flash-exp", # Experimental
    "gemini-pro"            # Old reliable
]

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

# --- History Management ---
def load_history():
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
                return history if isinstance(history, list) else []
        except json.JSONDecodeError:
            return []
    return []

def save_history(history):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        print(f"{RED}[!] Could not save history: {e}{RESET}")

def delete_history():
    if HISTORY_FILE.exists():
        try:
            os.remove(HISTORY_FILE)
            return True
        except:
            return False
    return False

# --- Core Logic ---

def load_config():
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            
            # Auto-update persona if needed
            if config.get("system_instruction") != DEFAULT_CONFIG["system_instruction"]:
                config["system_instruction"] = DEFAULT_CONFIG["system_instruction"]
                with open(CONFIG_FILE, "w") as f:
                    json.dump(config, f, indent=4)
            
            return config
        except json.JSONDecodeError:
            print(f"{RED}[!] Config corrupted. Resetting...{RESET}")

    # First Run
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

def update_model_in_config(config, new_model):
    """Updates the model in the config file permanently."""
    config["model_name"] = new_model
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        print(f"{YELLOW}[*] System re-calibrated. Active model: {new_model}{RESET}")
    except:
        pass

def try_request(config, history, payload):
    """Attempts to send the request. If 404, it rotates models automatically."""
    api_key = config.get("api_key")
    current_model = config.get("model_name", "gemini-1.5-flash")
    
    # Create a list of models to try: Current one first, then the rest of the list
    models_to_try = [current_model] + [m for m in KNOWN_MODELS if m != current_model]
    
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        try:
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                # Success! If we switched models, save the new one.
                if model != current_model:
                    update_model_in_config(config, model)
                return response, model
            
            elif response.status_code == 404:
                # Model not found, try next loop iteration
                continue
            
            else:
                # Other error (400, 500, etc), return immediately
                return response, model

        except requests.exceptions.RequestException:
            continue

    # If all failed
    return None, current_model

def chat_loop(config, initial_input=None):
    history = load_history()
    
    if history and sys.stdin.isatty():
        print(f"{YELLOW}[*] Accessing encrypted logs... ({len(history) // 2} records){RESET}")
    
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

        if not user_text: continue

        if user_text.lower() in EXIT_COMMANDS: break
        
        if user_text.lower() in DELETE_COMMANDS:
            if delete_history():
                history = []
                print(f"{GREEN}[✓] Logs wiped.{RESET}")
            else:
                print(f"{YELLOW}[!] No logs.{RESET}")
            continue

        history.append({"role": "user", "parts": [{"text": user_text}]})

        payload = {
            "contents": history,
            "systemInstruction": {"parts": [{"text": config.get("system_instruction")}]},
            "generationConfig": config.get("generation_config")
        }

        print(f"{YELLOW}scanning ctOS...{RESET}", end="\r", flush=True)

        # Attempt request with auto-healing
        response, used_model = try_request(config, history, payload)
        
        print(" " * 20, end="\r") 

        if response and response.status_code == 200:
            data = response.json()
            if "candidates" in data and data["candidates"]:
                ai_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                print(f"{GREEN}AIDEN:{RESET} {ai_text}")
                history.append({"role": "model", "parts": [{"text": ai_text}]})
                save_history(history)
            else:
                print(f"{RED}[!] Blocked by firewall.{RESET}")
                history.pop()
        else:
            if response:
                print(f"{RED}Error {response.status_code}: {response.text}{RESET}")
            else:
                print(f"{RED}[!] Connection failed. All models unreachable.{RESET}")
            history.pop()

def main():
    config = load_config()
    args = sys.argv[1:]

    if "--config" in args:
        subprocess.call([os.getenv('EDITOR', 'nano'), str(CONFIG_FILE)])
        sys.exit(0)

    initial_input = None
    query_args = [a for a in args if not a.startswith("--")]

    if not sys.stdin.isatty():
        piped = sys.stdin.read().strip()
        if piped:
            initial_input = piped
            if query_args: initial_input += " " + " ".join(query_args)
    elif query_args:
        initial_input = " ".join(query_args)

    chat_loop(config, initial_input)

if __name__ == "__main__":
    main()