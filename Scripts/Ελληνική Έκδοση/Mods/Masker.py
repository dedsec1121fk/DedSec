import requests
import random
import string
from typing import List

# --- Σταθερές ---
# Ορίζονται σε επίπεδο μονάδας για σαφήνεια και αποδοτικότητα.
PREFIXES: List[str] = ["Verify", "Secure", "Access", "Update", "Connect", "Login", "Portal", "Check"]
SUFFIXES: List[str] = ["Account", "Now", "Secure", "User", "Info", "System", "Session", "Auth"]

def generate_alias() -> str:
    """Δημιουργεί ένα τυχαίο, ευανάγνωστο ψευδώνυμο για το URL."""
    prefix = random.choice(PREFIXES)
    suffix = random.choice(SUFFIXES)
    digits = ''.join(random.choices(string.digits, k=2))
    return f"{prefix}{suffix}{digits}"

def shorten_with_isgd(session: requests.Session, url: str, alias: str) -> str:
    """
    Προσπαθεί να συντομεύσει ένα URL χρησιμοποιώντας το is.gd με ένα προσαρμοσμένο ψευδώνυμο.
    Εγείρει ValueError αν το API του is.gd επιστρέψει ένα γνωστό μήνυμα σφάλματος.
    """
    api_url = "https://is.gd/create.php"
    params = {"format": "simple", "url": url, "shorturl": alias}
    response = session.get(api_url, params=params)
    response.raise_for_status()  # Εγείρει μια εξαίρεση για σφάλματα HTTP (π.χ. 4xx, 5xx)
    
    short_url = response.text.strip()
    if short_url.startswith("Error:"):
        # Το is.gd επιστρέφει κατάσταση 200 OK ακόμη και για σφάλματα, επομένως πρέπει να ελέγξουμε το περιεχόμενο.
        raise ValueError(short_url)
        
    return short_url

def shorten_with_cleanuri(session: requests.Session, url: str) -> str:
    """Συντομεύει ένα URL χρησιμοποιώντας το API του cleanuri.com ως εναλλακτική λύση."""
    api_url = "https://cleanuri.com/api/v1/shorten"
    response = session.post(api_url, data={'url': url})
    response.raise_for_status()
    return response.json()["result_url"]

def auto_mask_url(url: str) -> str:
    """
    Μασκάρει ένα URL συντομεύοντάς το.
    
    Αρχικά, δοκιμάζει το is.gd με ένα προσαρμοσμένο ψευδώνυμο. Αν αποτύχει, χρησιμοποιεί
    ως εναλλακτική λύση το cleanuri.com για ένα τυπικό συντομευμένο URL.
    """
    # Προεπιλογή σε https:// για λόγους ασφαλείας αν δεν καθοριστεί πρωτόκολλο.
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    alias = generate_alias()
    
    # Χρήση αντικειμένου session για αποδοτικές, επαναλαμβανόμενες αιτήσεις.
    with requests.Session() as session:
        # Προσπάθεια 1: is.gd με προσαρμοσμένο ψευδώνυμο
        try:
            print(f"🔁 Δοκιμάζεται το is.gd με ψευδώνυμο: {alias}")
            return shorten_with_isgd(session, url, alias)
        except Exception as e1:
            print(f"⚠️ Το is.gd απέτυχε: {e1}")
            # Προσπάθεια 2: Εναλλακτική λύση με cleanuri.com
            try:
                print("🔁 Επιστροφή στο cleanuri.com...")
                return shorten_with_cleanuri(session, url)
            except Exception as e2:
                return f"❌ Όλες οι προσπάθειες απέτυχαν:\n  - is.gd: {e1}\n  - cleanuri.com: {e2}"

def main() -> None:
    """Κύρια συνάρτηση για την εκτέλεση του μασκαρίσματος URL."""
    print("🔐 Αυτόματο μασκάρισμα URL\n")
    user_url = input("🔗 Επικολλήστε το URL για μασκάρισμα: ").strip()

    if not user_url:
        print("❌ Δεν εισήχθη URL. Έξοδος.")
        return

    masked_url = auto_mask_url(user_url)
    print(f"\n✅ Μασκαρισμένο URL: {masked_url}")

if __name__ == "__main__":
    main()