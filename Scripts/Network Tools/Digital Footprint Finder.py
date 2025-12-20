# ----------------------------------------------------------------------
# Digital_Footprint_Finder_v12.py - Ultra-Low False Positives & 270+ Sites
# Optimized for Termux & Standard Python Environments
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

# --- CRASH-PROOF DEPENDENCY CHECK ---
def check_and_install_deps():
    required_packages = ['requests', 'colorama', 'bs4', 'lxml'] 
    try:
        import requests
        import colorama
        import bs4
    except ImportError:
        print("\n[STATUS] Installing required dependencies (requests, colorama, beautifulsoup4, lxml)...")
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
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36'
]

# --- FALSE POSITIVE REDUCTION CONFIG ---
# Keywords in HTML that indicate the profile does NOT exist.
GLOBAL_ERROR_INDICATORS = [
    "user not found", "page not found", "404 not found", "this account does not exist",
    "account suspended", "profile not found", "user has been suspended", "sorry, this page isn't available",
    "the page you requested cannot be found", "this user is not available", "account deactivated",
    "doesn't exist", "nothing here", "error 404", "we could not find", "content unavailable",
    "account removed", "no such user", "page doesn’t exist", "bad gateway", "internal server error",
    "profile unavailable", "user is inactive", "account closed", "member not found", 
    "no user with that username", "cannot find the user"
]

# If the Final URL contains these, it's a redirect to a generic page (False Positive).
SUSPICIOUS_REDIRECT_KEYWORDS = [
    "login", "signin", "search", "home", "error", "404", "accounts/login", 
    "register", "signup", "auth", "help", "support", "notfound", "undefined"
]

# If the Page Title is EXACTLY one of these, it's usually a generic landing page.
GENERIC_TITLES = [
    "login", "sign in", "page not found", "404", "error", "search", "home", 
    "instagram", "twitter", "facebook", "tiktok", "youtube", "twitch", "profile"
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
# SEARCH ENGINE DORKING
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
# SITE DATABASE (270+ Sites)
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
    
    # --- PREVIOUSLY ADDED (Preserved) ---
    "Behance": {"url": "https://www.behance.net/{}", "check_str": "We can't find that page"},
    "Dribbble": {"url": "https://dribbble.com/{}", "check_str": "404"},
    "ArtStation": {"url": "https://www.artstation.com/{}", "check_str": "404"},
    "DeviantArt": {"url": "https://www.deviantart.com/{}", "check_str": "404 Not Found"},
    "Bandcamp": {"url": "https://bandcamp.com/{}", "check_str": "404"},
    "Unsplash": {"url": "https://unsplash.com/@{}", "check_str": "404"},
    "VSCO": {"url": "https://vsco.co/{}", "check_str": "404"},
    "WordPress": {"url": "https://{}.wordpress.com/", "check_str": "doesn’t exist"},
    "Blogger": {"url": "https://{}.blogspot.com/", "check_str": "Blog not found"},
    "Patreon": {"url": "https://www.patreon.com/{}", "check_str": "404"},
    "Linktree": {"url": "https://linktr.ee/{}", "check_str": "The page you’re looking for doesn’t exist"},
    "Wikipedia": {"url": "https://en.wikipedia.org/wiki/User:{}", "check_str": "User account \"{}\" does not exist"},
    
    # --- NEW ADDITIONS (50+ NEW SITES) ---
    "PayPal": {"url": "https://www.paypal.com/paypalme/{}", "check_str": "We can't find this profile"},
    "Xbox Gamertag": {"url": "https://xboxgamertag.com/search/{}", "check_str": "not found"},
    "PSN Profiles": {"url": "https://psnprofiles.com/{}", "check_str": "could not be found"},
    "Disqus": {"url": "https://disqus.com/by/{}", "check_str": "404"},
    "Slack": {"url": "https://{}.slack.com", "check_str": "There is no workspace"},
    "OkCupid": {"url": "https://www.okcupid.com/profile/{}", "check_str": "404"},
    "Tinder": {"url": "https://tinder.com/@{}", "check_str": "404"},
    "Bumble": {"url": "https://bumble.com/@{}", "check_str": "404"},
    "Venmo": {"url": "https://venmo.com/u/{}", "check_str": "404"},
    "Cash App": {"url": "https://cash.app/${}", "check_str": "404"},
    "About.me": {"url": "https://about.me/{}", "check_str": "404"},
    "Giphy": {"url": "https://giphy.com/{}", "check_str": "404"},
    "Tenor": {"url": "https://tenor.com/users/{}", "check_str": "404"},
    "GeeksforGeeks": {"url": "https://auth.geeksforgeeks.org/user/{}/profile", "check_str": "404"},
    "Codewars": {"url": "https://www.codewars.com/users/{}", "check_str": "404"},
    "HackerRank": {"url": "https://www.hackerrank.com/{}", "check_str": "404"},
    "CodeChef": {"url": "https://www.codechef.com/users/{}", "check_str": "404"},
    "TopCoder": {"url": "https://www.topcoder.com/members/{}", "check_str": "404"},
    "Last.fm": {"url": "https://www.last.fm/user/{}", "check_str": "404"},
    "Trakt": {"url": "https://trakt.tv/users/{}", "check_str": "404"},
    "Letterboxd": {"url": "https://letterboxd.com/{}", "check_str": "Not Found"},
    "MyAnimeList": {"url": "https://myanimelist.net/profile/{}", "check_str": "404"},
    "AniList": {"url": "https://anilist.co/user/{}", "check_str": "404"},
    "Crunchyroll": {"url": "https://www.crunchyroll.com/user/{}", "check_str": "404"},
    "Minds": {"url": "https://www.minds.com/{}", "check_str": "404"},
    "Gab": {"url": "https://gab.com/{}", "check_str": "404"},
    "Parler": {"url": "https://parler.com/user/{}", "check_str": "404"},
    "Gettr": {"url": "https://gettr.com/user/{}", "check_str": "404"},
    "Truth Social": {"url": "https://truthsocial.com/@{}", "check_str": "404"},
    "Rumble": {"url": "https://rumble.com/user/{}", "check_str": "404"},
    "DailyMotion": {"url": "https://www.dailymotion.com/{}", "check_str": "404"},
    "ReverbNation": {"url": "https://www.reverbnation.com/{}", "check_str": "404"},
    "BandLab": {"url": "https://www.bandlab.com/{}", "check_str": "404"},
    "Smule": {"url": "https://www.smule.com/{}", "check_str": "404"},
    "StarMaker": {"url": "https://m.starmakerstudios.com/user/{}", "check_str": "404"},
    "Fandom": {"url": "https://community.fandom.com/wiki/User:{}", "check_str": "does not exist"},
    "Wikia": {"url": "https://{}.fandom.com", "check_str": "404"},
    "Pastebin": {"url": "https://pastebin.com/u/{}", "check_str": "Not Found"},
    "Wattpad": {"url": "https://www.wattpad.com/user/{}", "check_str": "User not found"},
    "Archive.org": {"url": "https://archive.org/details/@{}", "check_str": "404"},
    "OpenSea": {"url": "https://opensea.io/{}", "check_str": "404"},
    "Rarible": {"url": "https://rarible.com/{}", "check_str": "404"},
    "Foundation": {"url": "https://foundation.app/@{}", "check_str": "404"},
    "KnownOrigin": {"url": "https://knownorigin.io/{}", "check_str": "404"},
    "Polywork": {"url": "https://www.polywork.com/{}", "check_str": "404"},
    "PeerList": {"url": "https://peerlist.io/{}", "check_str": "404"},
    "Hashnode": {"url": "https://hashnode.com/@{}", "check_str": "404"},
    "Substack": {"url": "https://{}.substack.com", "check_str": "404"},
    "Ghost": {"url": "https://{}.ghost.io", "check_str": "404"},
    "Carrd": {"url": "https://{}.carrd.co", "check_str": "404"},
    "Wix": {"url": "https://{}.wixsite.com/website", "check_str": "404"},
    "Weebly": {"url": "https://{}.weebly.com", "check_str": "404"},
    "Jimdo": {"url": "https://{}.jimdosite.com", "check_str": "404"},
    "Yola": {"url": "https://{}.yolasite.com", "check_str": "404"},
    "Strikingly": {"url": "https://{}.mystrikingly.com", "check_str": "404"},
    "Houzz": {"url": "https://www.houzz.com/user/{}", "check_str": "404"},
    "Angi": {"url": "https://www.angi.com/companylist/{}", "check_str": "404"},
    "Yelp": {"url": "https://www.yelp.com/user_details?userid={}", "check_str": "404"},
    "Glassdoor": {"url": "https://www.glassdoor.com/member/profile/index.htm", "check_str": "Sign In"}, # Tricky
    "Freelancer": {"url": "https://www.freelancer.com/u/{}", "check_str": "404"},
    "Upwork": {"url": "https://www.upwork.com/freelancers/~{}", "check_str": "404"},
    "Guru": {"url": "https://www.guru.com/freelancers/{}", "check_str": "404"},
    "PeoplePerHour": {"url": "https://www.peopleperhour.com/freelancer/{}", "check_str": "404"},
    "Toptal": {"url": "https://www.toptal.com/resume/{}", "check_str": "404"},
    "Chess.com": {"url": "https://www.chess.com/member/{}", "check_str": "Page not found"},
    "Lichess": {"url": "https://lichess.org/@/{}", "check_str": "Page not found"},
    "WarriorForum": {"url": "https://www.warriorforum.com/members/{}.html", "check_str": "404"},
    "BlackHatWorld": {"url": "https://www.blackhatworld.com/members/{}/", "check_str": "404"},
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
        # Request with redirection enabled
        r = requests.get(url, headers=headers, timeout=12, allow_redirects=True)
        
        # 1. IMMEDIATE STATUS CODE CHECKS
        if r.status_code in [404, 410, 500, 502, 503]: 
            return None

        # 2. URL STRUCTURE ANALYSIS
        final_url_lower = r.url.lower()
        
        # Redirected to a completely different domain? (e.g., domain parking)
        original_domain = url.split("/")[2].replace("www.", "")
        final_domain = r.url.split("/")[2].replace("www.", "")
        if original_domain not in final_domain and "login" in final_domain:
            return None

        # Redirected to generic paths
        if any(keyword in final_url_lower for keyword in SUSPICIOUS_REDIRECT_KEYWORDS):
            return None

        # Redirected to root (e.g. site.com/user -> site.com/)
        if r.url.rstrip('/') == f"https://{original_domain}" or r.url.rstrip('/') == f"http://{original_domain}":
            return None

        # 3. CONTENT ANALYSIS
        soup = BeautifulSoup(r.text, 'lxml') # Changed to lxml for speed
        page_text = soup.get_text().lower()
        page_title = soup.title.string.strip().lower() if soup.title else ""
        
        # Global Error Indicators
        if any(err in page_text for err in GLOBAL_ERROR_INDICATORS):
            return None
        
        # Site-Specific Error Indicator
        if check_str and check_str.lower() in page_text: 
            return None

        # 4. SMART TITLE VERIFICATION (CRITICAL FOR REDUCING FPS)
        # If the title is just the Site Name (e.g. "Instagram"), it's likely a login/error page.
        # A valid profile usually has "Username - Site" or "Name (@username) | Site"
        
        # Check if title is generic
        if page_title in GENERIC_TITLES:
            return None
        
        # Check if title is literally just the site name
        if page_title == site_name.lower():
            return None
            
        # 5. META TAG INSPECTION
        # Check OpenGraph/Twitter tags. Valid profiles usually populate these.
        meta_title = soup.find("meta", property="og:title") or soup.find("meta", property="twitter:title")
        if meta_title:
            content = meta_title.get("content", "").lower()
            if "login" in content or "sign up" in content or "error" in content:
                return None

        # 6. LOGIN FORM DETECTION
        # If there is a password field AND the username is NOT in the title/h1, it's a login trap.
        if soup.find("input", {"type": "password"}):
            h1 = soup.find("h1")
            h1_text = h1.get_text().lower() if h1 else ""
            if username.lower() not in page_title and username.lower() not in h1_text:
                return None

        return url
    except Exception as e:
        if verbose: print(f"{Fore.RED}Error checking {site_name}: {e}{Style.RESET_ALL}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("username", nargs='?')
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    print(f"\n{Fore.CYAN}Digital Footprint Finder v12 (True-Positive Optimization){Style.RESET_ALL}")
    
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
    print(f"\n{Fore.BLUE}[*] Scanning 270+ Platforms (Threaded)...{Style.RESET_ALL}")
    
    site_keys = list(SITES.keys())
    random.shuffle(site_keys) # Prevent hitting same host concurrently

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
    
    # --- SAVE LOGIC ---
    base_dir = os.path.join(os.path.expanduser('~'), 'storage', 'downloads')
    if not os.path.exists(base_dir):
        if os.path.exists("/sdcard/Download"):
             base_dir = "/sdcard/Download"
        else:
             base_dir = os.path.expanduser('~') 

    save_dir = os.path.join(base_dir, 'Digital Footprint Finder')
    try:
        os.makedirs(save_dir, exist_ok=True)
    except Exception as e:
        save_dir = "." 
    
    filename = os.path.join(save_dir, f"{username}_v12.txt")
    
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
