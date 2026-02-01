import requests
import random
import string
from typing import List

# --- Constants ---
# Defined at the module level for clarity and efficiency.
PREFIXES: List[str] = ["Verify", "Secure", "Access", "Update", "Connect", "Login", "Portal", "Check"]
SUFFIXES: List[str] = ["Account", "Now", "Secure", "User", "Info", "System", "Session", "Auth"]

def generate_alias() -> str:
    """Generates a random, human-readable alias for the URL."""
    prefix = random.choice(PREFIXES)
    suffix = random.choice(SUFFIXES)
    digits = ''.join(random.choices(string.digits, k=2))
    return f"{prefix}{suffix}{digits}"

def shorten_with_isgd(session: requests.Session, url: str, alias: str) -> str:
    """
    Attempts to shorten a URL using is.gd with a custom alias.
    Raises a ValueError if the is.gd API returns a known error message.
    """
    api_url = "https://is.gd/create.php"
    params = {"format": "simple", "url": url, "shorturl": alias}
    response = session.get(api_url, params=params)
    response.raise_for_status()  # Raise an exception for HTTP errors (e.g., 4xx, 5xx)
    
    short_url = response.text.strip()
    if short_url.startswith("Error:"):
        # is.gd returns a 200 OK status even for errors, so we must check the body.
        raise ValueError(short_url)
        
    return short_url

def shorten_with_cleanuri(session: requests.Session, url: str) -> str:
    """Shortens a URL using the cleanuri.com API as a fallback."""
    api_url = "https://cleanuri.com/api/v1/shorten"
    response = session.post(api_url, data={'url': url})
    response.raise_for_status()
    return response.json()["result_url"]

def auto_mask_url(url: str) -> str:
    """
    Masks a URL by shortening it.
    
    It first tries is.gd with a custom alias. If that fails, it falls back
    to cleanuri.com for a standard shortened URL.
    """
    # Default to https:// for security if no protocol is specified.
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    alias = generate_alias()
    
    # Use a session object for efficient, repeated requests.
    with requests.Session() as session:
        # Attempt 1: is.gd with a custom alias
        try:
            print(f"🔁 Attempting is.gd with alias: {alias}")
            return shorten_with_isgd(session, url, alias)
        except Exception as e1:
            print(f"⚠️ is.gd failed: {e1}")
            # Attempt 2: Fallback to cleanuri.com
            try:
                print("🔁 Falling back to cleanuri.com...")
                return shorten_with_cleanuri(session, url)
            except Exception as e2:
                return f"❌ All attempts failed:\n  - is.gd: {e1}\n  - cleanuri.com: {e2}"

def main() -> None:
    """Main function to run the URL masker."""
    print("🔐 Auto URL Masker\n")
    user_url = input("🔗 Paste the URL to mask: ").strip()

    if not user_url:
        print("❌ No URL entered. Exiting.")
        return

    masked_url = auto_mask_url(user_url)
    print(f"\n✅ Masked URL: {masked_url}")

if __name__ == "__main__":
    main()