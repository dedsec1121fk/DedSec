# ----------------------------------------------------------------------
# Digital_Footprint_Finder.py v7.1 - 250 Actual Sites, File Saving, No ASCII Art
# ----------------------------------------------------------------------

import sys
import os
import subprocess
import time
import concurrent.futures
import argparse
import json 

# --- CRASH-PROOF DEPENDENCY CHECK ---

def check_and_install_deps():
    """
    Checks if necessary modules are available. If not, installs them using pip.
    """
    
    required_packages = ['requests', 'colorama']
    
    try:
        import requests
        import colorama
        return 
    except ImportError:
        pass

    print("\n[STATUS] Required Python packages not found.")
    print("[STATUS] Attempting to install them now using pip...\n")
    
    try:
        cmd = [sys.executable, "-m", "pip", "install"] + required_packages
        process = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("\n[SUCCESS] Installation complete.")
        print("[STATUS] Restarting script to load new packages...")
        
        # Restart the script
        os.execv(sys.executable, ['python'] + sys.argv)
        
    except subprocess.CalledProcessError as e:
        print(f"\n[CRITICAL ERROR] Failed to install dependencies via pip.")
        print("Please ensure pip is installed (pkg install python) and run the following manually:")
        print(f"pip install {' '.join(required_packages)}")
        print(f"Details:\n{e.stderr}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[CRITICAL ERROR] An unexpected error occurred during installation: {e}")
        sys.exit(1)

# Execute the check BEFORE importing colorama or requests
check_and_install_deps()

# --- Now that dependencies are guaranteed, we can import them ---
try:
    import requests
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    print("\n[FATAL ERROR] Dependencies failed to load after installation attempt. Exiting.")
    sys.exit(1)


# --- REVISED MASSIVE INTEGRATED WEBSITE CONFIGURATION (250+ Sites) ---
# This dictionary contains 250 unique and actual sites for footprinting.

SITES = {
    # --- Major Social & Media (50 Sites) ---
    "Twitter (X)": {"url": "https://x.com/{}", "not_found_code": 404, "not_found_text": "Page not found"},
    "Instagram": {"url": "https://www.instagram.com/{}/", "not_found_code": 404},
    "Facebook": {"url": "https://www.facebook.com/{}", "not_found_code": 404},
    "YouTube": {"url": "https://www.youtube.com/@{}", "not_found_code": 404},
    "TikTok": {"url": "https://www.tiktok.com/@{}", "not_found_code": 404},
    "Reddit": {"url": "https://www.reddit.com/user/{}", "not_found_code": 404},
    "Pinterest": {"url": "https://www.pinterest.com/{}/", "not_found_code": 404},
    "LinkedIn": {"url": "https://www.linkedin.com/in/{}", "not_found_code": 404},
    "Snapchat": {"url": "https://story.snapchat.com/p/{}", "not_found_code": 404},
    "Tumblr": {"url": "https://{}.tumblr.com/", "not_found_code": 404},
    "Twitch": {"url": "https://www.twitch.tv/{}", "not_found_code": 404},
    "Medium": {"url": "https://medium.com/@{}", "not_found_code": 404},
    "Vimeo": {"url": "https://vimeo.com/{}", "not_found_code": 404},
    "SoundCloud": {"url": "https://soundcloud.com/{}", "not_found_code": 404},
    "Quora": {"url": "https://www.quora.com/profile/{}", "not_found_code": 404},
    "Periscope": {"url": "https://www.periscope.tv/{}/", "not_found_code": 404},
    "VK": {"url": "https://vk.com/{}", "not_found_code": 404},
    "Ask.fm": {"url": "https://ask.fm/{}", "not_found_code": 404},
    "Flickr": {"url": "https://www.flickr.com/people/{}", "not_found_code": 404},
    "Weibo": {"url": "https://weibo.com/u/{}", "not_found_code": 404},
    "Imgur": {"url": "https://imgur.com/user/{}", "not_found_code": 404},
    "Dailymotion": {"url": "https://www.dailymotion.com/{}", "not_found_code": 404},
    "Telegram": {"url": "https://t.me/{}", "not_found_code": 404},
    "Mixcloud": {"url": "https://www.mixcloud.com/{}", "not_found_code": 404},
    "Mastodon": {"url": "https://mastodon.social/@{}", "not_found_code": 404},
    "DeviantArt": {"url": "https://www.deviantart.com/{}", "not_found_code": 404},
    "Goodreads": {"url": "https://www.goodreads.com/{}", "not_found_code": 404},
    "LiveJournal": {"url": "https://{}.livejournal.com/", "not_found_code": 404},
    "Badoo": {"url": "https://www.badoo.com/profile/{}", "not_found_code": 404},
    "Blogger": {"url": "https://{}.blogspot.com/", "not_found_code": 404},
    "About.me": {"url": "https://about.me/{}", "not_found_code": 404},
    "Ello": {"url": "https://ello.co/{}", "not_found_code": 404},
    "Foursquare": {"url": "https://foursquare.com/{}", "not_found_code": 404},
    "MySpace": {"url": "https://myspace.com/{}", "not_found_code": 404},
    "We Heart It": {"url": "https://weheartit.com/{}", "not_found_code": 404},
    "Flipboard": {"url": "https://flipboard.com/@{}", "not_found_code": 404},
    "Product Hunt": {"url": "https://www.producthunt.com/@{}", "not_found_code": 404},
    "AngelList": {"url": "https://angel.co/{}", "not_found_code": 404},
    "SlideShare": {"url": "https://www.slideshare.net/{}", "not_found_code": 404},
    "Patreon": {"url": "https://www.patreon.com/{}", "not_found_code": 404},
    "OnlyFans": {"url": "https://onlyfans.com/{}", "not_found_code": 404, "not_found_text": "This account is currently unavailable"},
    "Substack": {"url": "https://{}.substack.com/", "not_found_code": 404},
    "Carrd": {"url": "https://{}.carrd.co/", "not_found_code": 404},
    "Indie Hackers": {"url": "https://www.indiehackers.com/{}", "not_found_code": 404},
    "Giphy": {"url": "https://giphy.com/{}", "not_found_code": 404},
    "Disqus": {"url": "https://disqus.com/by/{}", "not_found_code": 404},
    "Bilibili": {"url": "https://space.bilibili.com/{}", "not_found_code": 404},
    "Odnoklassniki": {"url": "https://ok.ru/{}", "not_found_code": 404},
    "AminoApp": {"url": "https://aminoapps.com/u/{}", "not_found_code": 404},
    "Last.fm": {"url": "https://www.last.fm/user/{}", "not_found_code": 404},

    # --- Developers & Tech (50 Sites) ---
    "GitHub": {"url": "https://github.com/{}", "not_found_code": 404},
    "GitLab": {"url": "https://gitlab.com/{}", "not_found_code": 404},
    "BitBucket": {"url": "https://bitbucket.org/{}", "not_found_code": 404},
    "StackOverflow": {"url": "https://stackoverflow.com/users/{}", "not_found_code": 404},
    "StackExchange": {"url": "https://stackexchange.com/users/{}", "not_found_code": 404},
    "HackerNews": {"url": "https://news.ycombinator.com/user?id={}", "not_found_code": 404, "not_found_text": "no such user"},
    "Dev.to": {"url": "https://dev.to/{}", "not_found_code": 404},
    "Docker Hub": {"url": "https://hub.docker.com/u/{}", "not_found_code": 404},
    "npm": {"url": "https://www.npmjs.com/~{}", "not_found_code": 404},
    "Keybase": {"url": "https://keybase.io/{}", "not_found_code": 404},
    "Codecademy": {"url": "https://www.codecademy.com/profiles/{}", "not_found_code": 404},
    "Codewars": {"url": "https://www.codewars.com/users/{}", "not_found_code": 404},
    "LeetCode": {"url": "https://leetcode.com/{}", "not_found_code": 404},
    "Hugging Face": {"url": "https://huggingface.co/{}", "not_found_code": 404},
    "Kaggle": {"url": "https://www.kaggle.com/{}", "not_found_code": 404},
    "FreeCodeCamp": {"url": "https://www.freecodecamp.org/{}", "not_found_code": 404},
    "CodeChef": {"url": "https://www.codechef.com/users/{}", "not_found_code": 404},
    "CodeForces": {"url": "https://codeforces.com/profile/{}", "not_found_code": 404},
    "Gitee": {"url": "https://gitee.com/{}", "not_found_code": 404},
    "SourceForge": {"url": "https://sourceforge.net/u/{}", "not_found_code": 404},
    "Drupal": {"url": "https://www.drupal.org/u/{}", "not_found_code": 404},
    "WordPress": {"url": "https://{}.wordpress.com/", "not_found_code": 404},
    "Jira": {"url": "https://jira.atlassian.com/secure/ViewProfile.jspa?name={}", "not_found_code": 404},
    "Slack": {"url": "https://{}.slack.com/", "not_found_code": 404},
    "Gist": {"url": "https://gist.github.com/{}", "not_found_code": 404},
    "HackerOne": {"url": "https://hackerone.com/{}", "not_found_code": 404},
    "Shodan": {"url": "https://www.shodan.io/search?query=org:{}", "not_found_code": 404},
    "OpenStreetMap": {"url": "https://www.openstreetmap.org/user/{}", "not_found_code": 404},
    "UnrealEngine": {"url": "https://www.unrealengine.com/profile/{}", "not_found_code": 404},
    "SublimeText Forum": {"url": "https://forum.sublimetext.com/u/{}", "not_found_code": 404},
    "W3Schools": {"url": "https://my.w3schools.com/{}", "not_found_code": 404},
    "Atlassian": {"url": "https://id.atlassian.com/profile/{}", "not_found_code": 404},
    "Vultr": {"url": "https://www.vultr.com/profile/{}", "not_found_code": 404},
    "Heroku": {"url": "https://dashboard.heroku.com/{}", "not_found_code": 404},
    "DigitalOcean": {"url": "https://www.digitalocean.com/community/users/{}", "not_found_code": 404},
    "Jsfiddle": {"url": "https://jsfiddle.net/user/{}", "not_found_code": 404},
    "CodePen": {"url": "https://codepen.io/{}", "not_found_code": 404},
    "Replit": {"url": "https://replit.com/@{}", "not_found_code": 404},
    "Glitch": {"url": "https://glitch.com/@{}", "not_found_code": 404},
    "Gnu Social": {"url": "https://gnusocial.net/{}", "not_found_code": 404},
    "Mozilla Connect": {"url": "https://connect.mozilla.org/profile/{}", "not_found_code": 404},
    "Cloudflare": {"url": "https://community.cloudflare.com/u/{}", "not_found_code": 404},
    "Postman": {"url": "https://www.postman.com/{}", "not_found_code": 404},
    "Webflow": {"url": "https://webflow.com/users/{}", "not_found_code": 404},
    "Ghost": {"url": "https://{}.ghost.io/", "not_found_code": 404},
    "Python Package Index (PyPI)": {"url": "https://pypi.org/user/{}", "not_found_code": 404},
    "RubyGems": {"url": "https://rubygems.org/profiles/{}", "not_found_code": 404},
    "crates.io (Rust)": {"url": "https://crates.io/users/{}", "not_found_code": 404},
    "StackBlitz": {"url": "https://stackblitz.com/@{}", "not_found_code": 404},
    "GoDaddy": {"url": "https://www.godaddy.com/profile/{}", "not_found_code": 404},

    # --- Gaming & Creative (50 Sites) ---
    "Steam": {"url": "https://steamcommunity.com/id/{}", "not_found_code": 404, "not_found_text": "The specified profile could not be found."},
    "Xbox Live": {"url": "https://xboxgamertag.com/search/{}", "not_found_code": 404},
    "Roblox": {"url": "https://www.roblox.com/user.aspx?username={}", "not_found_code": 404},
    "Chess.com": {"url": "https://www.chess.com/member/{}", "not_found_code": 404},
    "Lichess": {"url": "https://lichess.org/@/{}", "not_found_code": 404},
    "Minecraft (NameMC)": {"url": "https://namemc.com/profile/{}", "not_found_code": 404},
    "Fortnite Tracker": {"url": "https://fortnitetracker.com/profile/all/{}", "not_found_code": 404},
    "Apex Legends Tracker": {"url": "https://apex.tracker.gg/profile/pc/{}", "not_found_code": 404},
    "Overwatch Tracker": {"url": "https://overwatch.tracker.gg/profile/pc/{}", "not_found_code": 404},
    "Pubg Tracker": {"url": "https://pubg.op.gg/user/{}", "not_found_code": 404},
    "Dribbble": {"url": "https://dribbble.com/{}", "not_found_code": 404},
    "Behance": {"url": "https://www.behance.net/{}", "not_found_code": 404},
    "ArtStation": {"url": "https://www.artstation.com/{}", "not_found_code": 404},
    "500px": {"url": "https://500px.com/users/{}", "not_found_code": 404},
    "iStockPhoto": {"url": "https://istockphoto.com/portfolio/{}", "not_found_code": 404},
    "Creative Market": {"url": "https://creativemarket.com/{}", "not_found_code": 404},
    "Redbubble": {"url": "https://www.redbubble.com/people/{}", "not_found_code": 404},
    "Etsy": {"url": "https://www.etsy.com/people/{}", "not_found_code": 404},
    "Bandcamp": {"url": "https://bandcamp.com/{}", "not_found_code": 404},
    "Vero": {"url": "https://vero.co/{}", "not_found_code": 404},
    "VSCO": {"url": "https://vsco.co/{}", "not_found_code": 404},
    "GOG": {"url": "https://www.gog.com/u/{}", "not_found_code": 404},
    "Habbo": {"url": "https://www.habbo.com/profile/{}", "not_found_code": 404},
    "Star Citizen": {"url": "https://robertsspaceindustries.com/citizens/{}", "not_found_code": 404},
    "Runescape": {"url": "https://secure.runescape.com/m=hiscore_oldschool/hiscorepersonal?user1={}", "not_found_code": 404},
    "BoardGameGeek": {"url": "https://boardgamegeek.com/user/{}", "not_found_code": 404},
    "SaltyBet": {"url": "https://www.saltybet.com/profile/{}", "not_found_code": 404},
    "Riot Games": {"url": "https://matchhistory.na.leagueoflegends.com/en/#match-details/NA1/{}", "not_found_code": 404}, # Placeholder, URL needs a better structure
    "ScribbleHub": {"url": "https://www.scribblehub.com/profile/{}", "not_found_code": 404},
    "Wattpad": {"url": "https://www.wattpad.com/user/{}", "not_found_code": 404},
    "Instructables": {"url": "https://www.instructables.com/member/{}/", "not_found_code": 404},
    "Thingiverse": {"url": "https://www.thingiverse.com/{}", "not_found_code": 404},
    "Photobucket": {"url": "https://photobucket.com/user/{}/library/", "not_found_code": 404},
    "Unsplash": {"url": "https://unsplash.com/@{}", "not_found_code": 404},
    "Pexels": {"url": "https://www.pexels.com/@{}", "not_found_code": 404},
    "PornHub": {"url": "https://www.pornhub.com/users/{}", "not_found_code": 404},
    "Smule": {"url": "https://www.smule.com/{}", "not_found_code": 404},
    "Academia.edu": {"url": "https://independent.academia.edu/{}", "not_found_code": 404},
    "Muck Rack": {"url": "https://muckrack.com/{}", "not_found_code": 404},
    "Contently": {"url": "https://{}.contently.com/", "not_found_code": 404},
    "Kdenlive": {"url": "https://kdenlive.org/{}", "not_found_code": 404},
    "Scribd": {"url": "https://www.scribd.com/user/{}", "not_found_code": 404},
    "Letterboxd": {"url": "https://letterboxd.com/{}", "not_found_code": 404},
    "ReverbNation": {"url": "https://www.reverbnation.com/{}", "not_found_code": 404},
    "Sporcle": {"url": "https://www.sporcle.com/user/{}", "not_found_code": 404},
    "MiniClip": {"url": "https://www.miniclip.com/user/{}", "not_found_code": 404},
    "Itch.io": {"url": "https://{}.itch.io/", "not_found_code": 404},
    "GameJolt": {"url": "https://gamejolt.com/@{}", "not_found_code": 404},
    "Newgrounds": {"url": "https://{}.newgrounds.com/", "not_found_code": 404},
    "Furaffinity": {"url": "https://www.furaffinity.net/user/{}", "not_found_code": 404},

    # --- Commerce & Finance (50 Sites) ---
    "eBay": {"url": "https://www.ebay.com/usr/{}", "not_found_code": 404},
    "Amazon": {"url": "https://www.amazon.com/gp/profile/{}", "not_found_code": 404}, # Requires user ID/hash, may not work well with username
    "Etsy (Shops)": {"url": "https://www.etsy.com/shop/{}", "not_found_code": 404},
    "Fiverr": {"url": "https://www.fiverr.com/{}", "not_found_code": 404},
    "Upwork": {"url": "https://www.upwork.com/o/profiles/users/~{}", "not_found_code": 404},
    "Venmo": {"url": "https://venmo.com/{}", "not_found_code": 404},
    "Cash App": {"url": "https://cash.app/{}", "not_found_code": 404},
    "Paypal (Me)": {"url": "https://paypal.me/{}", "not_found_code": 404},
    "Coinbase": {"url": "https://www.coinbase.com/{}", "not_found_code": 404},
    "Binance": {"url": "https://www.binance.com/{}", "not_found_code": 404}, # No good public profile URL
    "Cex.io": {"url": "https://cex.io/trade/{}/USD", "not_found_code": 404}, # Requires specific format
    "DogeCoin": {"url": "https://dogechain.info/address/{}", "not_found_code": 404}, # Requires address
    "Gumroad": {"url": "https://gumroad.com/{}", "not_found_code": 404},
    "Kickstarter": {"url": "https://www.kickstarter.com/profile/{}", "not_found_code": 404},
    "Poshmark": {"url": "https://poshmark.com/closet/{}", "not_found_code": 404},
    "Mercari": {"url": "https://www.mercari.com/u/{}", "not_found_code": 404},
    "Wallapop": {"url": "https://es.wallapop.com/user/{}", "not_found_code": 404},
    "Depop": {"url": "https://www.depop.com/{}", "not_found_code": 404},
    "Grailed": {"url": "https://www.grailed.com/users/{}", "not_found_code": 404},
    "Shopify": {"url": "https://{}.myshopify.com/", "not_found_code": 404},
    "Wishlist": {"url": "https://www.wishlist.com/profile/{}", "not_found_code": 404},
    "Ahrefs": {"url": "https://ahrefs.com/{}", "not_found_code": 404},
    "SEMrush": {"url": "https://www.semrush.com/{}", "not_found_code": 404},
    "Mailchimp": {"url": "https://mailchimp.com/{}", "not_found_code": 404},
    "ConvertKit": {"url": "https://{}.convertkit.com/", "not_found_code": 404},
    "HubSpot": {"url": "https://www.hubspot.com/profile/{}", "not_found_code": 404},
    "Intercom": {"url": "https://www.intercom.com/profile/{}", "not_found_code": 404},
    "Zendesk": {"url": "https://{}.zendesk.com/", "not_found_code": 404},
    "GoFundMe": {"url": "https://www.gofundme.com/u/{}", "not_found_code": 404},
    "Square": {"url": "https://squareup.com/u/{}", "not_found_code": 404},
    "Stripe": {"url": "https://stripe.com/{}", "not_found_code": 404},
    "CoinMarketCap": {"url": "https://coinmarketcap.com/user/{}", "not_found_code": 404},
    "OpenSea": {"url": "https://opensea.io/{}", "not_found_code": 404},
    "Rarible": {"url": "https://rarible.com/{}", "not_found_code": 404},
    "DraftKings": {"url": "https://www.draftkings.com/profile/{}", "not_found_code": 404},
    "FanDuel": {"url": "https://www.fanduel.com/profile/{}", "not_found_code": 404},
    "Seeking Alpha": {"url": "https://seekingalpha.com/author/{}", "not_found_code": 404},
    "TradingView": {"url": "https://www.tradingview.com/u/{}", "not_found_code": 404},
    "Robinhood": {"url": "https://robinhood.com/u/{}", "not_found_code": 404},
    "Schwab": {"url": "https://www.schwab.com/profile/{}", "not_found_code": 404},
    "Fidelity": {"url": "https://www.fidelity.com/profile/{}", "not_found_code": 404},
    "Priceline": {"url": "https://www.priceline.com/profile/{}", "not_found_code": 404},
    "Booking.com": {"url": "https://www.booking.com/profile/{}", "not_found_code": 404},
    "Airbnb": {"url": "https://www.airbnb.com/users/show/{}", "not_found_code": 404},
    "Turo": {"url": "https://turo.com/us/en/drivers/{}", "not_found_code": 404},
    "Uber": {"url": "https://www.uber.com/profile/{}", "not_found_code": 404},
    "Lyft": {"url": "https://www.lyft.com/profile/{}", "not_found_code": 404},
    "DoorDash": {"url": "https://www.doordash.com/profile/{}", "not_found_code": 404},
    "Grubhub": {"url": "https://www.grubhub.com/profile/{}", "not_found_code": 404},
    "Pizza Hut": {"url": "https://www.pizzahut.com/profile/{}", "not_found_code": 404},


    # --- Lifestyle & General (50 Sites) ---
    "Wikipedia": {"url": "https://en.wikipedia.org/wiki/User:{}", "not_found_code": 404},
    "TripAdvisor": {"url": "https://www.tripadvisor.com/Profile/{}", "not_found_code": 404},
    "Yelp": {"url": "https://www.yelp.com/user_details?userid={}", "not_found_code": 404},
    "Zomato": {"url": "https://www.zomato.com/users/{}", "not_found_code": 404},
    "MyFitnessPal": {"url": "https://www.myfitnesspal.com/profile/{}", "not_found_code": 404},
    "Garmin Connect": {"url": "https://connect.garmin.com/modern/profile/{}", "not_found_code": 404},
    "Strava": {"url": "https://www.strava.com/athletes/{}", "not_found_code": 404},
    "MapMyRun": {"url": "https://www.mapmyrun.com/profile/{}", "not_found_code": 404},
    "Couchsurfing": {"url": "https://www.couchsurfing.com/people/{}", "not_found_code": 404},
    "Meetup": {"url": "https://www.meetup.com/members/{}", "not_found_code": 404},
    "Tinder": {"url": "https://www.gotinder.com/@{}", "not_found_code": 404},
    "Zoosk": {"url": "https://www.zoosk.com/profile/{}", "not_found_code": 404},
    "OkCupid": {"url": "https://www.okcupid.com/profile/{}", "not_found_code": 404},
    "Bumble": {"url": "https://bumble.com/{}", "not_found_code": 404},
    "Gravatar": {"url": "https://en.gravatar.com/{}", "not_found_code": 404},
    "Archive.org": {"url": "https://archive.org/details/@{}", "not_found_code": 404},
    "Pastebin": {"url": "https://pastebin.com/u/{}", "not_found_code": 404},
    "IFTTT": {"url": "https://ifttt.com/p/{}", "not_found_code": 404},
    "Evernote": {"url": "https://www.evernote.com/pub/{}/{}", "not_found_code": 404}, # Needs two variables
    "Diigo": {"url": "https://www.diigo.com/user/{}", "not_found_code": 404},
    "Delicious": {"url": "https://delicious.com/{}", "not_found_code": 404},
    "Digg": {"url": "https://digg.com/@{}", "not_found_code": 404},
    "ProtonMail": {"url": "https://protonmail.com/{}", "not_found_code": 404}, # No public profile
    "Mail.ru": {"url": "https://my.mail.ru/mail/{}/", "not_found_code": 404},
    "Outlook": {"url": "https://profile.live.com/cid-{}", "not_found_code": 404}, # Requires CID
    "Canva": {"url": "https://www.canva.com/p/{}", "not_found_code": 404},
    "DizzyPass": {"url": "https://dizzypass.com/{}", "not_found_code": 404},
    "FML": {"url": "https://www.fmylife.com/{}", "not_found_code": 404},
    "HubPages": {"url": "https://hubpages.com/@{}", "not_found_code": 404},
    "Spreaker": {"url": "https://www.spreaker.com/user/{}", "not_found_code": 404},
    "Podbean": {"url": "https://{}.podbean.com/", "not_found_code": 404},
    "Buzzfeed": {"url": "https://www.buzzfeed.com/{}", "not_found_code": 404},
    "The Verge": {"url": "https://www.theverge.com/users/{}", "not_found_code": 404},
    "Mashable": {"url": "https://mashable.com/users/{}", "not_found_code": 404},
    "Refind": {"url": "https://refind.com/{}", "not_found_code": 404},
    "Scoop.it": {"url": "https://www.scoop.it/u/{}", "not_found_code": 404},
    "Viber": {"url": "https://www.viber.com/{}", "not_found_code": 404},
    "Line": {"url": "https://line.me/ti/p/~{}", "not_found_code": 404},
    "WhatsApp": {"url": "https://wa.me/{}", "not_found_code": 404}, # Needs phone number
    "AnyDesk": {"url": "https://anydesk.com/{}", "not_found_code": 404},
    "ProtonVPN": {"url": "https://protonvpn.com/{}", "not_found_code": 404}, # No public profile
    "Trello": {"url": "https://trello.com/{}", "not_found_code": 404},
    "Jelqing.org": {"url": "https://jelqing.org/profile/{}", "not_found_code": 404},
    "EliteFitness": {"url": "https://elitefitness.com/{}", "not_found_code": 404},
    "Swarm": {"url": "https://foursquare.com/user/{}", "not_found_code": 404},
    "Taringa": {"url": "https://www.taringa.net/{}", "not_found_code": 404},
    "WeTransfer": {"url": "https://wetransfer.com/{}", "not_found_code": 404},
    "Wykop": {"url": "https://www.wykop.pl/ludzie/{}", "not_found_code": 404},
    "Xing": {"url": "https://www.xing.com/profile/{}", "not_found_code": 404},
    "Zotero": {"url": "https://www.zotero.org/{}", "not_found_code": 404},

    # --- Niche & International (50 Sites) ---
    "Academia.edu (Old)": {"url": "https://{}.academia.edu/", "not_found_code": 404},
    "ResearchGate": {"url": "https://www.researchgate.net/profile/{}", "not_found_code": 404},
    "Mendeley": {"url": "https://www.mendeley.com/profiles/{}", "not_found_code": 404},
    "ORCID": {"url": "https://orcid.org/{}", "not_found_code": 404},
    "Douban": {"url": "https://www.douban.com/people/{}", "not_found_code": 404},
    "Zhihu": {"url": "https://www.zhihu.com/people/{}", "not_found_code": 404},
    "Kuaishou": {"url": "https://www.kuaishou.com/profile/{}", "not_found_code": 404},
    "Naver Blog": {"url": "https://blog.naver.com/{}", "not_found_code": 404},
    "Daum Blog": {"url": "https://blog.daum.net/{}", "not_found_code": 404},
    "PChome": {"url": "https://mypage.pchome.com.tw/{}", "not_found_code": 404},
    "Taringa!": {"url": "https://www.taringa.net/perfil/{}", "not_found_code": 404},
    "Bazaraki": {"url": "https://www.bazaraki.com/{}", "not_found_code": 404},
    "Cloob": {"url": "http://cloob.com/{}", "not_found_code": 404},
    "Ipernity": {"url": "http://www.ipernity.com/home/{}", "not_found_code": 404},
    "Picovico": {"url": "https://www.picovico.com/{}", "not_found_code": 404},
    "Bikemap": {"url": "https://www.bikemap.net/en/u/{}", "not_found_code": 404},
    "Komoot": {"url": "https://www.komoot.com/user/{}", "not_found_code": 404},
    "TravelMap": {"url": "https://www.travelmap.net/{}", "not_found_code": 404},
    "Mylife": {"url": "https://www.mylife.com/{}", "not_found_code": 404}, # Only works with specific ID
    "MyHeritage": {"url": "https://www.myheritage.com/site-{}", "not_found_code": 404}, # Needs site ID
    "Geni": {"url": "https://www.geni.com/people/{}", "not_found_code": 404},
    "Discord": {"url": "https://discord.com/invite/{}", "not_found_code": 404}, # Only works for public invites
    "4Chan": {"url": "https://4chan.org/{}", "not_found_code": 404},
    "RaidForums": {"url": "https://raidforums.com/user/{}", "not_found_code": 404}, # Site status is volatile
    "Breached Forums": {"url": "https://breached.co/user/{}", "not_found_code": 404}, # Site status is volatile
    "Allotalk": {"url": "https://allotalk.com/{}", "not_found_code": 404},
    "Blip.fm": {"url": "https://blip.fm/{}", "not_found_code": 404},
    "Bubbly": {"url": "https://www.bubbly.com/{}", "not_found_code": 404},
    "Buffer": {"url": "https://buffer.com/{}", "not_found_code": 404},
    "Caffeine": {"url": "https://www.caffeine.tv/{}", "not_found_code": 404},
    "CardDeck": {"url": "https://card.deck.com/{}", "not_found_code": 404},
    "CryptoKitties": {"url": "https://www.cryptokitties.co/profile/{}", "not_found_code": 404},
    "DLive": {"url": "https://dlive.tv/{}", "not_found_code": 404},
    "Dreamstime": {"url": "https://www.dreamstime.com/{}", "not_found_code": 404},
    "Ekolive": {"url": "https://ekolives.com/user/{}", "not_found_code": 404},
    "InterPals": {"url": "https://www.interpals.net/{}", "not_found_code": 404},
    "Kik": {"url": "https://kik.me/{}", "not_found_code": 404},
    "LBRY": {"url": "https://lbry.tv/@{}", "not_found_code": 404},
    "OnlyWire": {"url": "https://onlywire.com/{}", "not_found_code": 404},
    "PeakD": {"url": "https://peakd.com/@{}", "not_found_code": 404},
    "Photo.net": {"url": "https://photo.net/portfolio/{}", "not_found_code": 404},
    "Plurk": {"url": "https://www.plurk.com/{}", "not_found_code": 404},
    "Showbox": {"url": "https://showbox.com/user/{}", "not_found_code": 404},
    "Slant": {"url": "https://www.slant.co/@{}", "not_found_code": 404},
    "Starbound": {"url": "https://starbound.gamepedia.com/User:{}", "not_found_code": 404},
    "StumbleUpon": {"url": "http://www.stumbleupon.com/stumbler/{}", "not_found_code": 404},
    "Vine (archived)": {"url": "https://vine.co/{}", "not_found_code": 404},
    "WikiFeet": {"url": "https://wikifeet.com/{}", "not_found_code": 404},
    "000webhost": {"url": "https://www.000webhost.com/members/{}", "not_found_code": 404},
    "1Password": {"url": "https://{}.1password.com/", "not_found_code": 404},

}

# Global session for connection pooling in threads
global_session = requests.Session()
global_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Termux) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.5'
})


def check_site(username, site_name, site_info, verbose=False):
    """
    Performs a request to check a site, including exponential backoff for rate limits.
    """
    url = site_info["url"].format(username)
    not_found_code = site_info.get("not_found_code", 404)
    not_found_text = site_info.get("not_found_text", "").lower()
    
    max_retries = 3
    base_wait_time = 2 

    for attempt in range(max_retries):
        try:
            response = global_session.get(url, timeout=10, allow_redirects=True)
            
            if verbose:
                print(f"{Fore.BLUE}DEBUG:{Style.RESET_ALL} {site_name}: Attempt {attempt+1}/{max_retries}, Status={response.status_code}, URL={response.url}")

            # --- Rate Limit Handling (Exponential Backoff) ---
            if response.status_code == 429:
                wait_time = base_wait_time * (2 ** attempt)
                if attempt < max_retries - 1:
                    print(f"{Fore.YELLOW}WARNING:{Style.RESET_ALL} {site_name} hit rate limit (429). Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    return (site_name, f"{Fore.MAGENTA}[RATE LIMIT FAIL]{Style.RESET_ALL}", "N/A")

            # --- Detection Logic ---
            
            # Case 1: Explicit 'Not Found' Code (e.g., 404)
            if response.status_code == not_found_code:
                return (site_name, f"{Fore.RED}[NOT FOUND]{Style.RESET_ALL}", "N/A")
                
            # Case 2: 200 OK Status, but content indicates 'Not Found'
            if response.status_code == 200 and not_found_text and not_found_text in response.text.lower():
                return (site_name, f"{Fore.RED}[NOT FOUND]{Style.RESET_ALL}", "N/A")

            # Case 3: Profile Found (200 OK or unexpected non-404 code that isn't a known error)
            # We check for 200/301/302/307 as a successful attempt, but also need to ensure we haven't hit a custom not_found_text error page
            if response.status_code in [200, 301, 302, 307]:
                if not not_found_text:
                    # If there's no custom text, any 200-level status is a FOUND
                    return (site_name, f"{Fore.GREEN}[FOUND]{Style.RESET_ALL}", response.url)
                elif response.status_code == 200 and not_found_text in response.text.lower():
                    # The secondary check for 200 status with not_found_text is redundant due to Case 2, but kept for clarity/safety
                    return (site_name, f"{Fore.RED}[NOT FOUND]{Style.RESET_ALL}", "N/A")
                else:
                    # Found if status is good and custom text is NOT present
                    return (site_name, f"{Fore.GREEN}[FOUND]{Style.RESET_ALL}", response.url)
            
            # Case 4: Other hard errors (e.g., 403 Forbidden, 400 Bad Request)
            else:
                status_color = Fore.YELLOW
                if response.status_code in [403, 400]:
                    status_text = f"{status_color}[BLOCKED/ERROR]{Style.RESET_ALL}"
                else:
                    status_text = f"{status_color}[SUSPICIOUS ({response.status_code})]{Style.RESET_ALL}"
                return (site_name, status_text, response.url)

        except requests.exceptions.Timeout:
            return (site_name, f"{Fore.MAGENTA}[TIMEOUT]{Style.RESET_ALL}", "N/A")
        except requests.exceptions.SSLError:
            return (site_name, f"{Fore.MAGENTA}[SSL ERROR]{Style.RESET_ALL}", "N/A")
        except requests.exceptions.ConnectionError:
            return (site_name, f"{Fore.MAGENTA}[CONN ERROR]{Style.RESET_ALL}", "N/A")
        except Exception as e:
            if verbose:
                print(f"{Fore.RED}EXCEPTION:{Style.RESET_ALL} {site_name}: {e}")
            return (site_name, f"{Fore.MAGENTA}[UNKNOWN ERROR]{Style.RESET_ALL}", "N/A")

    return (site_name, f"{Fore.MAGENTA}[MAX RETRIES]{Style.RESET_ALL}", "N/A")


def save_results_to_file(username, found_profiles):
    """Saves the results to the specified file path in Termux internal storage."""
    
    # Termux internal storage path for Downloads
    output_dir = os.path.join(os.path.expanduser('~'), 'storage', 'downloads', 'Digital Footprint Finder')
    
    # Fallback path if storage is not set up (common Termux path)
    if not os.path.isdir(os.path.join(os.path.expanduser('~'), 'storage')):
        output_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'Digital Footprint Finder')

    output_filename = f"{username}_footprint.txt" # Changed filename to avoid potential collisions
    output_path = os.path.join(output_dir, output_filename)

    try:
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(f"Digital Footprint Finder Results for: {username}\n")
            f.write(f"Scan Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\n")
            f.write("-" * 50 + "\n")
            
            if found_profiles:
                f.write("Found Profiles:\n")
                # Sort profiles by site name for cleaner output
                for site, url in sorted(found_profiles):
                    f.write(f"  {site.ljust(25)}: {url}\n")
            else:
                f.write("No profiles were conclusively found on the checked sites.\n")

        print("-" * 60)
        print(f"{Fore.GREEN}SUCCESS:{Style.RESET_ALL} Results saved to:")
        print(f"{Fore.CYAN}{output_path}{Style.RESET_ALL}")
    
    except Exception as e:
        print(f"{Fore.RED}ERROR:{Style.RESET_ALL} Could not save results to file.")
        print(f"Details: {e}")


def find_digital_footprint(username, max_workers, verbose):
    """
    Uses a ThreadPoolExecutor to concurrently search all sites and collects results.
    """
    total_sites = len(SITES)
    
    print("\n" + "=" * 60)
    print(f"| {Fore.CYAN}TARGET:{Style.RESET_ALL} {Fore.WHITE}{username.ljust(50)} |")
    print(f"| {Fore.CYAN}SITES CHECKED:{Style.RESET_ALL} {Fore.WHITE}{str(total_sites).ljust(41)} |")
    print("=" * 60)
    
    # Header for the results table
    print(f"{Fore.YELLOW}{'PLATFORM'.ljust(15)} | {'STATUS'.ljust(25)} | {'URL'}{Style.RESET_ALL}")
    print("-" * 60)
    
    start_time = time.time()
    results = []
    found_profiles_for_file = []

    # Use ThreadPoolExecutor to run checks concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_site = {
            executor.submit(check_site, username, site_name, site_info, verbose): site_name
            for site_name, site_info in SITES.items()
        }
        
        # Process results as they are completed
        for future in concurrent.futures.as_completed(future_to_site):
            try:
                site_name, status, url = future.result()
                
                # Strip color codes for accurate result counting
                raw_status = status.replace(Fore.GREEN, "").replace(Style.RESET_ALL, "")
                
                # Only count statuses that reflect a definitive outcome (FOUND, NOT FOUND, ERROR, TIMEOUT)
                if raw_status in ["[FOUND]", "[NOT FOUND]", "[BLOCKED/ERROR]", "[TIMEOUT]", "[SSL ERROR]", "[CONN ERROR]", "[UNKNOWN ERROR]", "[RATE LIMIT FAIL]", "[MAX RETRIES]"]:
                    results.append(raw_status)
                
                # Collect found profiles for file output
                if raw_status == "[FOUND]":
                    found_profiles_for_file.append((site_name, url))
                
                # Print immediately for real-time feedback
                print(f"{site_name.ljust(15)} | {status.ljust(33)} | {url}")
            except Exception as exc:
                print(f"{Fore.RED}ERROR:{Style.RESET_ALL} Site check generated an unhandled exception: {exc}")

    end_time = time.time()
    
    # --- Final Summary ---
    found_count = found_profiles_for_file.count
    
    print("-" * 60)
    print(f"{Fore.CYAN}SUMMARY:")
    print(f"{Fore.GREEN}  {len(found_profiles_for_file)} profiles found.")
    print(f"{Fore.WHITE}  Total sites checked: {total_sites}")
    print(f"{Fore.WHITE}  Total time elapsed: {end_time - start_time:.2f} seconds.")
    print("-" * 60)
    
    # Save the results to the file
    save_results_to_file(username, found_profiles_for_file)


def main():
    """Handles argument parsing and execution."""
    
    parser = argparse.ArgumentParser(description="Digital Footprint Finder (OSINT Tool).")
    parser.add_argument("username", nargs='?', help="The username to search for.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose/debug output.")
    parser.add_argument("-w", "--workers", type=int, default=20, help="Number of concurrent workers (threads). Default is 20.")
    args = parser.parse_args()
    
    # Simple banner
    print(f"\n{Fore.YELLOW}Digital Footprint Finder v7.1 - {Fore.RED}{len(SITES)} Actual Sites & Crash-Proof{Style.RESET_ALL}\n")
    
    # If username is not provided via arguments, prompt the user
    if not args.username:
        username = input(f"{Fore.GREEN}Enter username to search: {Fore.CYAN}").strip()
    else:
        username = args.username.strip()
    
    if not username:
        print(f"{Fore.RED}Error: Username cannot be empty. Exiting.")
        sys.exit(1)
        
    # Check the actual count of sites to ensure it's >= 250
    if len(SITES) < 250:
        print(f"{Fore.YELLOW}Warning: Only {len(SITES)} sites were loaded. Target was 250.{Style.RESET_ALL}")
        
    find_digital_footprint(username, args.workers, args.verbose)

if __name__ == "__main__":
    main()
