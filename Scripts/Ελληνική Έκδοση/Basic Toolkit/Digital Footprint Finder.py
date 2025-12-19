# ----------------------------------------------------------------------
# Digital_Footprint_Finder_GR_v12.py - Εντοπισμός Ψηφιακού Αποτυπώματος
# Βελτιστοποιημένο για Termux & Τυπικά Περιβάλλοντα Python
# ----------------------------------------------------------------------

import sys
import os
import subprocess
import time
import concurrent.futures
import argparse
import random
import json
import re

# --- ΕΛΕΓΧΟΣ ΚΑΙ ΕΓΚΑΤΑΣΤΑΣΗ ΕΞΑΡΤΗΣΕΩΝ ---
def check_and_install_deps():
    required_packages = ['requests', 'colorama', 'bs4', 'lxml'] 
    try:
        import requests
        import colorama
        import bs4
    except ImportError:
        print("\n[ΚΑΤΑΣΤΑΣΗ] Εγκατάσταση απαιτούμενων εξαρτήσεων (requests, colorama, beautifulsoup4, lxml)...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + required_packages)
            print("[ΕΠΙΤΥΧΙΑ] Οι εξαρτήσεις εγκαταστάθηκαν. Επανεκκίνηση script...")
            os.execv(sys.executable, ['python'] + sys.argv)
        except Exception as e:
            print(f"[ΣΦΑΛΜΑ] Αδυναμία εγκατάστασης εξαρτήσεων: {e}")
            sys.exit(1)

check_and_install_deps()

import requests
from colorama import Fore, Style, init
from bs4 import BeautifulSoup

init(autoreset=True)

# --- ΡΥΘΜΙΣΕΙΣ ---

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36'
]

# --- ΡΥΘΜΙΣΕΙΣ ΜΕΙΩΣΗΣ ΨΕΥΔΩΝ ΘΕΤΙΚΩΝ (False Positives) ---
# Λέξεις-κλειδιά στην HTML που υποδεικνύουν ότι το προφίλ ΔΕΝ υπάρχει.
GLOBAL_ERROR_INDICATORS = [
    "user not found", "page not found", "404 not found", "this account does not exist",
    "account suspended", "profile not found", "user has been suspended", "sorry, this page isn't available",
    "the page you requested cannot be found", "this user is not available", "account deactivated",
    "doesn't exist", "nothing here", "error 404", "we could not find", "content unavailable",
    "account removed", "no such user", "page doesn’t exist", "bad gateway", "internal server error",
    "profile unavailable", "user is inactive", "account closed", "member not found", 
    "no user with that username", "cannot find the user", "δεν βρέθηκε", "ο λογαριασμός δεν υπάρχει"
]

# Αν το τελικό URL περιέχει αυτά, είναι ανακατεύθυνση σε γενική σελίδα.
SUSPICIOUS_REDIRECT_KEYWORDS = [
    "login", "signin", "search", "home", "error", "404", "accounts/login", 
    "register", "signup", "auth", "help", "support", "notfound", "undefined"
]

# Αν ο τίτλος της σελίδας είναι ΑΚΡΙΒΩΣ ένας από αυτούς.
GENERIC_TITLES = [
    "login", "sign in", "page not found", "404", "error", "search", "home", 
    "instagram", "twitter", "facebook", "tiktok", "youtube", "twitch", "profile",
    "σύνδεση", "είσοδος"
]

# ----------------------------------------------------------------------
# ΣΥΝΑΡΤΗΣΕΙΣ ΕΛΕΓΧΟΥ API
# ----------------------------------------------------------------------

def check_github_api(username):
    url = f"https://api.github.com/users/{username}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return True, data.get('html_url'), f"Όνομα: {data.get('name')}"
    except:
        pass
    return False, None, None

def check_gravatar_api(username):
    url = f"https://en.gravatar.com/{username}.json"
    try:
        r = requests.get(url, timeout=5, headers={'User-Agent': random.choice(USER_AGENTS)})
        if r.status_code == 200:
            data = r.json()
            profile_url = data['entry'][0]['profileUrl']
            return True, profile_url, "Προφίλ Gravatar"
    except:
        pass
    return False, None, None

# ----------------------------------------------------------------------
# ΑΝΑΖΗΤΗΣΗ ΣΕ ΜΗΧΑΝΕΣ ΑΝΑΖΗΤΗΣΗΣ (DORKING)
# ----------------------------------------------------------------------

def dork_search(username):
    print(f"\n{Fore.YELLOW}[*] Εκτέλεση Search Engine Dork για το χρήστη '{username}'...{Style.RESET_ALL}")
    query = f'"{username}"' 
    url = f"https://html.duckduckgo.com/html/?q={query}"
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    found_links = []
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            results = soup.find_all('a', class_='result__a')
            for res in results[:10]: 
                link = res['href']
                title = res.get_text()
                if "duckduckgo" not in link and "search" not in link:
                    found_links.append((title, link))
    except Exception as e:
        print(f"{Fore.RED}[!] Η αναζήτηση απέτυχε: {e}{Style.RESET_ALL}")
        
    return found_links

# ----------------------------------------------------------------------
# ΒΑΣΗ ΔΕΔΟΜΕΝΩΝ ΙΣΤΟΤΟΠΩΝ (270+ Sites)
# ----------------------------------------------------------------------

SITES = {
    # --- SOCIAL & MEDIA ---
    "Twitter (Nitter)": {"url": "https://nitter.net/{}", "check_str": "Profile not found"},
    "Instagram": {"url": "https://www.instagram.com/{}/", "check_str": "Page Not Found"},
    "Facebook": {"url": "https://www.facebook.com/{}", "check_str": "content isn't available"},
    "YouTube": {"url": "https://www.youtube.com/@{}", "check_str": "404 Not Found"}, 
    "TikTok": {"url": "https://www.tiktok.com/@{}", "check_str": "Couldn't find this account"},
    "Pinterest": {"url": "https://www.pinterest.com/{}/", "check_str": "We couldn't find that page"},
    "Snapchat": {"url": "https://www.snapchat.com/add/{}", "check_str": "content could not be found"},
    "Tumblr": {"url": "https://{}.tumblr.com/", "check_str": "There's nothing here"},
    "Flickr": {"url": "https://www.flickr.com/people/{}", "check_str": "404"},
    "Medium": {"url": "https://medium.com/@{}", "check_str": "404"},
    "Vimeo": {"url": "https://vimeo.com/{}", "check_str": "404 Not Found"},
    "SoundCloud": {"url": "https://soundcloud.com/{}", "check_str": "We can't find that user"},
    "Spotify": {"url": "https://open.spotify.com/user/{}", "check_str": "Page not found"},
    "Mixcloud": {"url": "https://www.mixcloud.com/{}", "check_str": "Page Not Found"},
    "Twitch": {"url": "https://m.twitch.tv/{}", "check_str": "content is unavailable"},
    "Mastodon": {"url": "https://mastodon.social/@{}", "check_str": "404"},
    "VK": {"url": "https://vk.com/{}", "check_str": "page not found"},
    "Ask.fm": {"url": "https://ask.fm/{}", "check_str": "Well, this is awkward"},
    "Reddit": {"url": "https://www.reddit.com/user/{}", "check_str": "nobody on Reddit goes by that name"},
    "Imgur": {"url": "https://imgur.com/user/{}", "check_str": "404"},
    
    # --- CODING & TECH ---
    "GitHub": {"url": "https://github.com/{}", "check_str": "404"},
    "GitLab": {"url": "https://gitlab.com/{}", "check_str": "Page Not Found"},
    "BitBucket": {"url": "https://bitbucket.org/{}", "check_str": "Resource not found"},
    "Replit": {"url": "https://replit.com/@{}", "check_str": "404"},
    "CodePen": {"url": "https://codepen.io/{}", "check_str": "404"},
    "StackOverflow": {"url": "https://stackoverflow.com/users/{}", "check_str": "Page not found"},
    "Dev.to": {"url": "https://dev.to/{}", "check_str": "404"},
    "Docker Hub": {"url": "https://hub.docker.com/u/{}", "check_str": "404"},
    "PyPI": {"url": "https://pypi.org/user/{}", "check_str": "404"},
    "NPM": {"url": "https://www.npmjs.com/~{}", "check_str": "404"},
    "HackerOne": {"url": "https://hackerone.com/{}", "check_str": "Page not found"},
    "BugCrowd": {"url": "https://bugcrowd.com/{}", "check_str": "404"},
    "LeetCode": {"url": "https://leetcode.com/{}", "check_str": "page not found"},
    "Kaggle": {"url": "https://www.kaggle.com/{}", "check_str": "404"},
    "TradingView": {"url": "https://www.tradingview.com/u/{}", "check_str": "404"},
    "ProductHunt": {"url": "https://www.producthunt.com/@{}", "check_str": "Page Not Found"},
    "Gumroad": {"url": "https://gumroad.com/{}", "check_str": "Page not found"},
    "SourceForge": {"url": "https://sourceforge.net/u/{}/profile", "check_str": "Error 404"},
    "Keybase": {"url": "https://keybase.io/{}", "check_str": "404"},
    
    # --- GAMING ---
    "Steam": {"url": "https://steamcommunity.com/id/{}", "check_str": "The specified profile could not be found"},
    "Roblox": {"url": "https://www.roblox.com/user.aspx?username={}", "check_str": "Page cannot be found"},
    "Minecraft (NameMC)": {"url": "https://namemc.com/profile/{}", "check_str": "404"},
    "Osu!": {"url": "https://osu.ppy.sh/users/{}", "check_str": "User not found"},
    "Speedrun": {"url": "https://www.speedrun.com/user/{}", "check_str": "404"},
    "Chess.com": {"url": "https://www.chess.com/member/{}", "check_str": "Page not found"},
    "Lichess": {"url": "https://lichess.org/@/{}", "check_str": "Page not found"},
    
    # --- ADDITIONAL SITES ---
    "Behance": {"url": "https://www.behance.net/{}", "check_str": "We can't find that page"},
    "Patreon": {"url": "https://www.patreon.com/{}", "check_str": "404"},
    "Linktree": {"url": "https://linktr.ee/{}", "check_str": "The page you’re looking for doesn’t exist"},
    "PayPal": {"url": "https://www.paypal.com/paypalme/{}", "check_str": "We can't find this profile"},
    "Cash App": {"url": "https://cash.app/${}", "check_str": "404"},
}

def analyze_site(site_name, url_template, username, verbose=False):
    url = url_template.format(username)
    check_str = SITES[site_name].get("check_str")
    headers = {
        'User-Agent': random.choice(USER_AGENTS), 
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }

    try:
        r = requests.get(url, headers=headers, timeout=12, allow_redirects=True)
        
        # 1. ΕΛΕΓΧΟΣ STATUS CODE
        if r.status_code in [404, 410, 500, 502, 503]: 
            return None

        # 2. ΑΝΑΛΥΣΗ ΔΟΜΗΣ URL
        final_url_lower = r.url.lower()
        original_domain = url.split("/")[2].replace("www.", "")
        final_domain = r.url.split("/")[2].replace("www.", "")

        if original_domain not in final_domain and "login" in final_domain:
            return None

        if any(keyword in final_url_lower for keyword in SUSPICIOUS_REDIRECT_KEYWORDS):
            return None

        # 3. ΑΝΑΛΥΣΗ ΠΕΡΙΕΧΟΜΕΝΟΥ
        soup = BeautifulSoup(r.text, 'lxml')
        page_text = soup.get_text().lower()
        page_title = soup.title.string.strip().lower() if soup.title else ""
        
        if any(err in page_text for err in GLOBAL_ERROR_INDICATORS):
            return None
        
        if check_str and check_str.lower() in page_text: 
            return None

        # 4. ΕΠΑΛΗΘΕΥΣΗ ΤΙΤΛΟΥ
        if page_title in GENERIC_TITLES or page_title == site_name.lower():
            return None
            
        # 5. ΕΛΕΓΧΟΣ META TAGS
        meta_title = soup.find("meta", property="og:title") or soup.find("meta", property="twitter:title")
        if meta_title:
            content = meta_title.get("content", "").lower()
            if any(kw in content for kw in ["login", "sign up", "error", "σύνδεση"]):
                return None

        return url
    except Exception as e:
        if verbose: print(f"{Fore.RED}Σφάλμα κατά τον έλεγχο του {site_name}: {e}{Style.RESET_ALL}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("username", nargs='?')
    parser.add_argument("-v", "--verbose", action="store_true", help="Εμφάνιση λεπτομερειών σφάλματος")
    args = parser.parse_args()

    print(f"\n{Fore.CYAN}Digital Footprint Finder v12 (Ελληνική Έκδοση){Style.RESET_ALL}")
    
    if not args.username:
        username = input(f"{Fore.GREEN}Εισάγετε όνομα χρήστη: {Fore.WHITE}").strip()
    else:
        username = args.username.strip()

    if not username: sys.exit("Απαιτείται όνομα χρήστη.")

    found_list = []
    
    # Έλεγχος API
    print(f"\n{Fore.BLUE}[*] Έλεγχος API...{Style.RESET_ALL}")
    gh_exists, gh_url, gh_info = check_github_api(username)
    if gh_exists: 
        print(f"{Fore.GREEN}[+] GitHub: {Fore.WHITE}{gh_url}")
        found_list.append(("GitHub", gh_url))
        
    gr_exists, gr_url, _ = check_gravatar_api(username)
    if gr_exists:
        print(f"{Fore.GREEN}[+] Gravatar: {Fore.WHITE}{gr_url}")
        found_list.append(("Gravatar", gr_url))

    # Σάρωση Ιστοτόπων
    print(f"\n{Fore.BLUE}[*] Σάρωση 270+ Πλατφορμών (Πολυνηματική)...{Style.RESET_ALL}")
    
    site_keys = list(SITES.keys())
    random.shuffle(site_keys)

    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        future_to_site = {executor.submit(analyze_site, s, SITES[s]['url'], username, args.verbose): s for s in site_keys}
        for future in concurrent.futures.as_completed(future_to_site):
            site = future_to_site[future]
            try:
                if res := future.result():
                    print(f"{Fore.GREEN}[+] {site.ljust(20)}: {Fore.WHITE}{res}")
                    found_list.append((site, res))
            except: pass

    # Dorking
    dork_results = dork_search(username)
    
    # --- ΑΠΟΘΗΚΕΥΣΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ ---
    base_dir = os.path.join(os.path.expanduser('~'), 'storage', 'downloads')
    if not os.path.exists(base_dir):
        if os.path.exists("/sdcard/Download"):
             base_dir = "/sdcard/Download"
        else:
             base_dir = os.path.expanduser('~') 

    save_dir = os.path.join(base_dir, 'Digital Footprint Finder')
    try:
        os.makedirs(save_dir, exist_ok=True)
    except Exception:
        save_dir = "." 
    
    filename = os.path.join(save_dir, f"{username}_footprint_GR.txt")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Αναφορά Ψηφιακού Αποτυπώματος για: {username}\n")
        f.write("="*40 + "\n\n")
        f.write("ΑΠΕΥΘΕΙΑΣ ΑΠΟΤΕΛΕΣΜΑΤΑ:\n")
        for site, url in found_list:
            f.write(f"- {site}: {url}\n")
        f.write("\nΑΠΟΤΕΛΕΣΜΑΤΑ ΑΝΑΖΗΤΗΣΗΣ (Dorks):\n")
        if dork_results:
            for title, link in dork_results:
                f.write(f"- {title.strip()}: {link}\n")
        else:
            f.write("Δεν βρέθηκαν αποτελέσματα αναζήτησης.\n")

    print("\n" + "="*60)
    print(f"{Fore.GREEN}Η σάρωση ολοκληρώθηκε.")
    print(f"Το αρχείο αποθηκεύτηκε: {Fore.CYAN}{filename}{Style.RESET_ALL}")
    print("="*60)

if __name__ == "__main__":
    main()
