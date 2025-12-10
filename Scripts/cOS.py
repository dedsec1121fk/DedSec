import sys
import os
import time
import subprocess
import threading

# --- Dependency Check and Auto-Install (Identical) ---
def install_package(package):
    """Installs a missing pip package using the subprocess module."""
    print(f"\n[SETUP] Installing missing package: {package}...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print(f"[SETUP] {package} installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Failed to install {package}. Please run 'pip install {package}' manually.")
        print(f"Details: {e}")
        return False
    except FileNotFoundError:
        print("\n[ERROR] Python or pip command not found. Ensure Termux has Python installed ('pkg install python').")
        return False

# Attempt to import the required library
try:
    import websocket
except ImportError:
    if not install_package("websocket-client"):
        sys.exit(1)
    try:
        import websocket
    except ImportError:
        print("[FATAL] Required 'websocket' module is still missing. Exiting.")
        sys.exit(1)

# --- Core Chat Logic ---

SERVER_URL = "wss://echo.websocket.org" 
current_username = ""
last_sent_message = None 

def get_prompt():
    """Dynamically generates the prompt based on the chosen username."""
    return f"{current_username}: "

def on_message(ws, message):
    """
    CALLED WHEN A MESSAGE IS RECEIVED.
    
    Filters out the echo message and the "Request served by" meta-message.
    """
    global last_sent_message
    
    # Filter out the "Request served by" metadata message
    if message.startswith("Request served by"):
        return

    # Filter out the message echoed back from the server
    if message == last_sent_message:
        last_sent_message = None
        return
    
    try:
        # Clear the input line
        sys.stdout.write("\r\x1b[K") 
        print(f"{message}") 
        # Reprint the custom prompt
        sys.stdout.write(get_prompt())
        sys.stdout.flush()
    except Exception:
        pass

def on_error(ws, error):
    print(f"\n[ERROR] Connection Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"\n--- DISCONNECTED ---")
    print("The chat session has ended.")

def on_open(ws):
    """
    Called when connection is established.
    
    --- CHANGED THE CONNECTION MESSAGE HERE ---
    """
    print(f"--- CONNECTED TO cOS ---")
    print(f"You can now send messages.")

def connect_to_public_chat():
    global current_username
    global last_sent_message
    
    current_username = input("Choose a username: ")
    
    ws = websocket.WebSocketApp(
        SERVER_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    wst = threading.Thread(target=ws.run_forever, daemon=True)
    wst.start()
    
    # Wait for the connection thread to stabilize and print initial messages
    time.sleep(1) 

    while True:
        try:
            message = input(get_prompt())
            
            if message.lower() == 'exit':
                ws.close()
                break
            
            # The message construction is key to showing the username
            full_message = f"[{current_username}]: {message}"
            
            last_sent_message = full_message

            ws.send(full_message)

        except KeyboardInterrupt:
            ws.close()
            break
        except Exception:
            time.sleep(1)
            pass

if __name__ == "__main__":
    print("Welcome to cOS Global Public Chat. Checking dependencies...")
    
    if sys.platform != 'win32':
        sys.stdout.write("\033[H\033[J")
    
    connect_to_public_chat()