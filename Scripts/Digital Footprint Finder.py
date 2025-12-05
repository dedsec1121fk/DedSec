# ----------------------------------------------------------------------
# Digital_Footprint_Finder_v9.py - Specific File Saving Update
# Optimized for Termux (No Root)
# ----------------------------------------------------------------------

import sys
import os
import subprocess
import time
import concurrent.futures
import argparse
import random
import json

# --- CRASH-PROOF DEPENDENCY CHECK ---
def check_and_install_deps():
    required_packages = ['requests', 'colorama', 'bs4'] 
    try:
        import requests
        import colorama
        import bs4
    except ImportError:
        print("\n[STATUS] Installing required dependencies (requests, colorama, beautifulsoup4)...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + required_packages)
            print("[SUCCESS] Dependencies installed. Restarting script...")
            os.execv(sys.executable, ['python'] + sys.argv)
        except Exception as e:
            print(f"[ERROR] Could not install dependencies: {e}")
            sys.exit(1)

check_and_install_deps()

import requests
from colorama import Fore, Style, init
from bs4 import BeautifulSoup

init(autoreset=True)

# --- CONFIGURATION ---

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
]

# ----------------------------------------------------------------------
# API CHECK FUNCTIONS
# ----------------------------------------------------------------------

def check_github_api(username):
    url = f"https://api.github.com/users/{username}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return True, data.get('html_url'), f"Name: {data.get('name')}"
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
            return True, profile_url, "Gravatar Profile"
    except:
        pass
    return False, None, None

# ----------------------------------------------------------------------
# SEARCH ENGINE DORKING (DuckDuckGo HTML)
# ----------------------------------------------------------------------

def dork_search(username):
    print(f"\n{Fore.YELLOW}[*] Running Search Engine Dork for '{username}'...{Style.RESET_ALL}")
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
        print(f"{Fore.RED}[!] Dorking failed: {e}{Style.RESET_ALL}")
        
    return found_links

# ----------------------------------------------------------------------
# SITE LIST & LOGIC
# ----------------------------------------------------------------------

SITES = {
    "Twitter": {"url": "https://nitter.net/{}", "check_str": "Profile not found"},
    "Instagram": {"url": "https://www.instagram.com/{}/", "check_str": "Page Not Found"},
    "Facebook": {"url": "https://www.facebook.com/{}", "check_str": "content isn't available"},
    "YouTube": {"url": "https://www.youtube.com/@{}", "check_str": "404 Not Found"}, 
    "TikTok": {"url": "https://www.tiktok.com/@{}", "check_str": "Couldn't find this account"},
    "Reddit": {"url": "https://www.reddit.com/user/{}", "check_str": "Sorry, nobody on Reddit goes by that name"},
    "Pinterest": {"url": "https://www.pinterest.com/{}/", "check_str": "We couldn't find that page"},
    "Medium": {"url": "https://medium.com/@{}", "check_str": "404"},
    "Vimeo": {"url": "https://vimeo.com/{}", "check_str": "404 Not Found"},
    "SoundCloud": {"url": "https://soundcloud.com/{}", "check_str": "We can't find that user"},
    "Spotify": {"url": "https://open.spotify.com/user/{}", "check_str": "Page not found"},
    "Pastebin": {"url": "https://pastebin.com/u/{}", "check_str": "Not Found"},
    "Wikipedia": {"url": "https://en.wikipedia.org/wiki/User:{}", "check_str": "User account \"{}\" does not exist"},
    "TripAdvisor": {"url": "https://www.tripadvisor.com/Profile/{}", "check_str": "This page is not available"},
    "Blogger": {"url": "https://{}.blogspot.com/", "check_str": "Blog not found"},
    "WordPress": {"url": "https://{}.wordpress.com/", "check_str": "doesn’t exist"},
    "Tumblr": {"url": "https://{}.tumblr.com/", "check_str": "There's nothing here"},
    "Flickr": {"url": "https://www.flickr.com/people/{}", "check_str": "404"},
    "Steam": {"url": "https://steamcommunity.com/id/{}", "check_str": "The specified profile could not be found"},
    "Freelancer": {"url": "https://www.freelancer.com/u/{}", "check_str": "Page not found"},
    "Patreon": {"url": "https://www.patreon.com/{}", "check_str": "404"},
    "BitBucket": {"url": "https://bitbucket.org/{}", "check_str": "Resource not found"},
    "GitLab": {"url": "https://gitlab.com/{}", "check_str": "Page Not Found"},
    "DeviantArt": {"url": "https://www.deviantart.com/{}", "check_str": "404 Not Found"},
    "About.me": {"url": "https://about.me/{}", "check_str": "404"},
    "Disqus": {"url": "https://disqus.com/by/{}", "check_str": "Page Not Found"},
    "SlideShare": {"url": "https://www.slideshare.net/{}", "check_str": "404"},
    "Quora": {"url": "https://www.quora.com/profile/{}", "check_str": "Page Not Found"},
    "Imgur": {"url": "https://imgur.com/user/{}", "check_str": "404"},
    "ProductHunt": {"url": "https://www.producthunt.com/@{}", "check_str": "Page Not Found"},
    "Slack": {"url": "https://{}.slack.com", "check_str": "There is no workspace"},
    "CodePen": {"url": "https://codepen.io/{}", "check_str": "404"},
    "Replit": {"url": "https://replit.com/@{}", "check_str": "404"},
    "TradingView": {"url": "https://www.tradingview.com/u/{}", "check_str": "404"},
    "Giphy": {"url": "https://giphy.com/{}", "check_str": "404"},
    "9GAG": {"url": "https://9gag.com/u/{}", "check_str": "404"},
    "Roblox": {"url": "https://www.roblox.com/user.aspx?username={}", "check_str": "Page cannot be found"},
    "Gumroad": {"url": "https://gumroad.com/{}", "check_str": "Page not found"},
    "Twitch": {"url": "https://m.twitch.tv/{}", "check_str": "content is unavailable"},
    "Linktree": {"url": "https://linktr.ee/{}", "check_str": "The page you’re looking for doesn’t exist"},
    "OnlyFans": {"url": "https://onlyfans.com/{}", "check_str": "page not found"},
    "Cash App": {"url": "https://cash.app/${}", "check_str": "Not Found"},
}

def analyze_site(site_name, url_template, username, verbose=False):
    url = url_template.format(username)
    check_str = SITES[site_name].get("check_str")
    headers = {'User-Agent': random.choice(USER_AGENTS), 'Accept-Language': 'en-US,en;q=0.9'}

    try:
        r = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        if r.status_code == 404: return None
        if r.status_code != 200: return None

        soup = BeautifulSoup(r.text, 'html.parser')
        page_text = soup.get_text().lower()
        page_title = soup.title.string.lower() if soup.title else ""
        
        if check_str and check_str.lower() in page_text: return None
        if "not found" in page_title or "404" in page_title: return None

        return url
    except Exception as e:
        if verbose: print(f"{Fore.RED}Error checking {site_name}: {e}{Style.RESET_ALL}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("username", nargs='?')
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    print(f"\n{Fore.CYAN}Digital Footprint Finder v9 (File Save Update){Style.RESET_ALL}")
    
    if not args.username:
        username = input(f"{Fore.GREEN}Enter username: {Fore.WHITE}").strip()
    else:
        username = args.username.strip()

    if not username: sys.exit("Username required.")

    found_list = []
    
    # API Checks
    print(f"\n{Fore.BLUE}[*] Checking APIs...{Style.RESET_ALL}")
    gh_exists, gh_url, gh_info = check_github_api(username)
    if gh_exists: 
        print(f"{Fore.GREEN}[+] GitHub: {Fore.WHITE}{gh_url}")
        found_list.append(("GitHub", gh_url))
        
    gr_exists, gr_url, _ = check_gravatar_api(username)
    if gr_exists:
        print(f"{Fore.GREEN}[+] Gravatar: {Fore.WHITE}{gr_url}")
        found_list.append(("Gravatar", gr_url))

    # Site Scrape
    print(f"\n{Fore.BLUE}[*] Scanning Platforms...{Style.RESET_ALL}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        future_to_site = {executor.submit(analyze_site, s, i['url'], username, args.verbose): s for s, i in SITES.items()}
        for future in concurrent.futures.as_completed(future_to_site):
            site = future_to_site[future]
            try:
                if res := future.result():
                    print(f"{Fore.GREEN}[+] {site.ljust(15)}: {Fore.WHITE}{res}")
                    found_list.append((site, res))
            except: pass

    # Dorking
    dork_results = dork_search(username)
    
    # --- UPDATED SAVE LOGIC ---
    # 1. Determine base Downloads folder for Termux
    base_dir = os.path.join(os.path.expanduser('~'), 'storage', 'downloads')
    
    # Fallback checks if storage isn't mapped correctly
    if not os.path.exists(base_dir):
        if os.path.exists("/sdcard/Download"):
             base_dir = "/sdcard/Download"
        else:
             base_dir = os.path.expanduser('~') # Last resort: Home folder

    # 2. Create 'Digital Footprint Finder' folder
    save_dir = os.path.join(base_dir, 'Digital Footprint Finder')
    try:
        os.makedirs(save_dir, exist_ok=True)
    except Exception as e:
        print(f"{Fore.RED}[!] Error creating folder {save_dir}: {e}")
        # Fallback to local directory if permission denied
        save_dir = "." 
    
    # 3. Set filename to username.txt
    filename = os.path.join(save_dir, f"{username}.txt")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Footprint Report for: {username}\n")
        f.write("="*40 + "\n\n")
        f.write("DIRECT MATCHES:\n")
        for site, url in found_list:
            f.write(f"- {site}: {url}\n")
        f.write("\nSEARCH RESULTS:\n")
        if dork_results:
            for title, link in dork_results:
                f.write(f"- {title}: {link}\n")
        else:
            f.write("No search results found.\n")

    print("\n" + "="*60)
    print(f"{Fore.GREEN}Scan Complete.")
    print(f"File Saved: {Fore.CYAN}{filename}{Style.RESET_ALL}")
    print("="*60)

if __name__ == "__main__":
    main()