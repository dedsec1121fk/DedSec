# ----------------------------------------------------------------------
# Digital Footprint Finder
# Goal: best practical results with conservative true-positive detection.
# - Much larger coverage via packs + optional Sherlock DB (hundreds of sites)
# - Lower false-positives with multi-signal scoring (title/meta/canonical/text)
# - Better stability on mobile (HEAD-first, size-limited downloads, retries)
# - Anti-bot / JS-shell detection -> POSSIBLE (never falsely FOUND)
# - Per-domain concurrency limiting (reduces rate-limit blocks)
# - Local extensibility: load & export site lists as JSON
# - Optional HTML report (+ TXT/JSON/CSV)
#
# IMPORTANT / RESPONSIBLE USE
# Use this for self-audits or consent-based checks. Many sites restrict automation.
# This tool does NOT bypass logins, CAPTCHAs, paywalls, or anti-bot protections.
# ----------------------------------------------------------------------

from __future__ import annotations

import sys
import os
import subprocess
import time
import concurrent.futures
import argparse
import random
import json
import re
import html as html_escape
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse, parse_qs, unquote


# ----------------------------------------------------------------------
# CRASH-PROOF DEPENDENCY CHECK (Termux-friendly)
# ----------------------------------------------------------------------

def check_and_install_deps() -> None:
    """Ensure runtime dependencies exist (Termux-friendly)."""
    required_pip = ["requests", "colorama", "beautifulsoup4", "lxml"]
    try:
        import requests  # noqa: F401
        import colorama  # noqa: F401
        import bs4       # noqa: F401
        import lxml      # noqa: F401
    except Exception:
        print("\n[ΚΑΤΑΣΤΑΣΗ] Εγκατάσταση απαιτούμενων εξαρτήσεων (requests, colorama, beautifulsoup4, lxml)...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade"] + required_pip)
            print("[ΕΠΙΤΥΧΙΑ] Οι εξαρτήσεις εγκαταστάθηκαν. Επανεκκίνηση του script...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            print(f"[ΣΦΑΛΜΑ] Δεν ήταν δυνατή η εγκατάσταση εξαρτήσεων: {e}")
            sys.exit(1)


check_and_install_deps()

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from colorama import Fore, Style, init
from bs4 import BeautifulSoup

init(autoreset=True)


# ----------------------------------------------------------------------
# Networking / Heuristics
# ----------------------------------------------------------------------

USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36",
]

# Common phrases indicating missing users/pages (multi-language light set).
GLOBAL_ERROR_INDICATORS: List[str] = [
    "user not found", "page not found", "404 not found", "this account does not exist",
    "account suspended", "profile not found", "user has been suspended",
    "sorry, this page isn't available", "the page you requested cannot be found",
    "this user is not available", "account deactivated", "doesn't exist",
    "nothing here", "error 404", "we could not find", "content unavailable",
    "account removed", "no such user", "page doesn't exist", "member not found",
    "no user with that username", "cannot find the user", "not found", "page unavailable",
    "δεν βρέθηκε", "δεν υπάρχει", "δεν βρέθηκε η σελίδα", "δεν υπάρχει αυτός ο χρήστης",
    "usuario no encontrado", "página no encontrada", "utilisateur introuvable", "seite nicht gefunden",
]

# Anti-bot / challenge pages (treated as POSSIBLE).
ANTIBOT_INDICATORS: List[str] = [
    "just a moment", "checking your browser", "attention required", "cf-error-code",
    "cloudflare", "captcha", "verify you are human", "ddos protection",
    "access denied", "request blocked", "bot detection", "please enable cookies",
]

# Redirect paths that often indicate you're not on a profile.
SUSPICIOUS_REDIRECT_PATH_KEYWORDS: List[str] = [
    "login", "signin", "sign-in", "register", "signup", "sign-up", "auth",
    "help", "support", "error", "notfound", "search", "session", "password",
]

# Very generic titles often seen on landing/login pages.
GENERIC_TITLES: List[str] = ["login", "sign in", "page not found", "404", "error", "search", "home"]

# Status codes that mean "we cannot be sure" (blocked/rate-limited/auth required).
UNCERTAIN_STATUS = {401, 403, 429}

# Default maximum HTML to download per site (bytes).
DEFAULT_MAX_HTML_BYTES = 250_000  # 250 KB

# Sherlock maintained site database (downloaded only when using --pack sherlock/mega)
SHERLOCK_DATA_URL = "https://raw.githubusercontent.com/sherlock-project/sherlock/master/sherlock_project/resources/data.json"


# ----------------------------------------------------------------------
# Site specifications & packs
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class SiteSpec:
    """A conservative spec for username-based profile checking."""

    url: str
    check_str: Optional[str] = None          # negative indicator in HTML
    error_url: Optional[str] = None          # negative final-url indicator (Sherlock response_url)
    category: str = "General"
    reliability: str = "normal"             # normal | low
    notes: str = ""
    positive_hint: Optional[str] = None      # optional positive regex hint


# --- CORE: high-value, relatively stable patterns ---
CORE_SITES: Dict[str, SiteSpec] = {
    # Social / community
    "Reddit": SiteSpec("https://www.reddit.com/user/{}", "nobody on Reddit goes by that name", category="Social"),
    "Mastodon (mastodon.social)": SiteSpec("https://mastodon.social/@{}", "404", category="Fediverse", reliability="low"),
    "Pixelfed (pixelfed.social)": SiteSpec("https://pixelfed.social/{}", "404", category="Fediverse", reliability="low"),
    "Lemmy (lemmy.world)": SiteSpec("https://lemmy.world/u/{}", "404", category="Fediverse", reliability="low"),

    # Tech
    "GitHub": SiteSpec("https://github.com/{}", "404", category="Tech", positive_hint=r"https?://github\\.com/{}"),
    "GitLab": SiteSpec("https://gitlab.com/{}", "Page Not Found", category="Tech"),
    "Codeberg": SiteSpec("https://codeberg.org/{}", "404", category="Tech"),
    "SourceHut": SiteSpec("https://sr.ht/~{}/", "404", category="Tech"),
    "Dev.to": SiteSpec("https://dev.to/{}", "404", category="Tech"),
    "CodePen": SiteSpec("https://codepen.io/{}", "404", category="Tech"),
    "Replit": SiteSpec("https://replit.com/@{}", "404", category="Tech"),

    # Blogs / link-in-bio
    "Linktree": SiteSpec("https://linktr.ee/{}", "doesn't exist", category="Blogs"),
    "Carrd": SiteSpec("https://{}.carrd.co/", "404", category="Blogs", reliability="low"),
    "WordPress": SiteSpec("https://{}.wordpress.com/", "doesn't exist", category="Blogs"),
    "Blogger": SiteSpec("https://{}.blogspot.com/", "Blog not found", category="Blogs"),
    "GitHub Pages": SiteSpec("https://{}.github.io/", None, category="Blogs", reliability="low"),
    "GitLab Pages": SiteSpec("https://{}.gitlab.io/", None, category="Blogs", reliability="low"),
    "Neocities": SiteSpec("https://{}.neocities.org/", "Not Found", category="Blogs", reliability="low"),

    # Media / creators
    "SoundCloud": SiteSpec("https://soundcloud.com/{}", "We can't find that user", category="Media"),
    "Letterboxd": SiteSpec("https://letterboxd.com/{}/", "404", category="Media"),
    "MyAnimeList": SiteSpec("https://myanimelist.net/profile/{}", "404", category="Media"),
    "AniList": SiteSpec("https://anilist.co/user/{}/", "404", category="Media"),

    # Gaming
    "Steam": SiteSpec("https://steamcommunity.com/id/{}", "The specified profile could not be found", category="Gaming"),
    "Chess.com": SiteSpec("https://www.chess.com/member/{}", "Page not found", category="Gaming"),
    "Lichess": SiteSpec("https://lichess.org/@/{}", "Page not found", category="Gaming"),

    # Forums
    "Hacker News": SiteSpec("https://news.ycombinator.com/user?id={}", "No such user", category="Forums"),
    "Lobsters": SiteSpec("https://lobste.rs/~{}", "Not found", category="Forums"),
}


EXTENDED_SITES: Dict[str, SiteSpec] = {}
FORUM_SITES: Dict[str, SiteSpec] = {}
FEDIVERSE_SITES: Dict[str, SiteSpec] = {}


def _add_site(dst: Dict[str, SiteSpec], name: str, spec: SiteSpec) -> None:
    if name in CORE_SITES or name in EXTENDED_SITES or name in FORUM_SITES or name in FEDIVERSE_SITES:
        return
    dst[name] = spec


def add_extended_sites() -> None:
    """Add a large collection of common username-based URL patterns."""

    # Link-in-bio / landing pages
    for name, url, chk, rel in [
        ("About.me", "https://about.me/{}", "404", "normal"),
        ("AllMyLinks", "https://allmylinks.com/{}", "Page not found", "normal"),
        ("Beacons", "https://beacons.ai/{}", "404", "normal"),
        ("Bio.site", "https://bio.site/{}", "404", "normal"),
        ("Campsite", "https://campsite.bio/{}", "404", "normal"),
        ("Koji", "https://koji.to/{}", "404", "normal"),
        ("Lnk.Bio", "https://lnk.bio/{}", "404", "normal"),
        ("Solo.to", "https://solo.to/{}", "404", "normal"),
        ("Taplink", "https://taplink.cc/{}", "404", "normal"),
        ("Milkshake", "https://milkshake.app/{}", "404", "normal"),
        ("LinkPop", "https://linkpop.com/{}", "404", "normal"),
        ("Stan Store", "https://stan.store/{}", "404", "low"),
        ("Snipfeed", "https://snipfeed.co/{}", "404", "low"),
        ("Komi", "https://komi.io/{}", "404", "low"),
        ("bio.fm", "https://bio.fm/{}", "404", "low"),
        ("ContactInBio", "https://contactinbio.com/{}", "404", "low"),
        ("Linkfly", "https://linkfly.to/{}", "404", "low"),
        ("Linkr.bio", "https://linkr.bio/{}", "404", "low"),
        ("Tap.bio", "https://tap.bio/{}", "404", "low"),
    ]:
        _add_site(EXTENDED_SITES, name, SiteSpec(url, chk, category="Blogs", reliability=rel))

    # Social networks / comms (many are bot-sensitive)
    for name, url, chk, rel, notes in [
        ("X", "https://x.com/{}", "This account doesn't exist", "low", "Often blocks automation"),
        ("Threads", "https://www.threads.net/@{}", "Sorry, this page isn't available", "low", "JS/login heavy"),
        ("TikTok (alt)", "https://www.tiktok.com/@{}", "Couldn't find this account", "low", "Bot sensitive"),
        ("Instagram (alt)", "https://www.instagram.com/{}/", "Page Not Found", "low", "Bot sensitive"),
        ("Twitch (mobile)", "https://m.twitch.tv/{}", "content is unavailable", "low", "Bot sensitive"),
        ("Pinterest (alt)", "https://www.pinterest.com/{}/", "We couldn't find that page", "normal", ""),
        ("Tumblr (alt)", "https://{}.tumblr.com/", "There's nothing here", "normal", ""),
        ("VK", "https://vk.com/{}", "page not found", "low", "May block"),
        ("Telegram", "https://t.me/{}", "If you have <strong>Telegram</strong>", "low", "Some users private"),
        ("Discord (discadia)", "https://discadia.com/user/{}", "404", "low", "Third-party directory"),
        ("Bluesky", "https://bsky.app/profile/{}.bsky.social", "404", "low", "Handle varies by domain"),
        ("Substack", "https://{}.substack.com/", "There is nothing here", "low", "Subdomain based"),
        ("Ko-fi", "https://ko-fi.com/{}", "404", "low", "Payments (skip with --safe)"),
        ("Patreon", "https://www.patreon.com/{}", "404", "low", "Payments (skip with --safe)"),
        ("BuyMeACoffee", "https://www.buymeacoffee.com/{}", "404", "low", "Payments (skip with --safe)"),
    ]:
        cat = "Payments" if "Payments" in notes else "Social"
        _add_site(EXTENDED_SITES, name, SiteSpec(url, chk, category=cat, reliability=rel, notes=notes))

    # Dev / tech
    for name, url, chk, rel in [
        ("Bitbucket", "https://bitbucket.org/{}", "Resource not found", "normal"),
        ("HackerRank", "https://www.hackerrank.com/{}", "404", "normal"),
        ("Codeforces", "https://codeforces.com/profile/{}", "404", "normal"),
        ("CodeChef", "https://www.codechef.com/users/{}", "404", "normal"),
        ("AtCoder", "https://atcoder.jp/users/{}", "404", "normal"),
        ("Exercism", "https://exercism.org/profiles/{}", "404", "normal"),
        ("FreeCodeCamp", "https://www.freecodecamp.org/{}", "404", "normal"),
        ("Kaggle", "https://www.kaggle.com/{}", "404", "normal"),
        ("LeetCode", "https://leetcode.com/{}", "page not found", "low"),
        ("HackerOne", "https://hackerone.com/{}", "Page not found", "normal"),
        ("Bugcrowd", "https://bugcrowd.com/{}", "404", "normal"),
        ("CTFtime", "https://ctftime.org/user/{}", "404", "low"),
        ("TryHackMe", "https://tryhackme.com/p/{}", "404", "low"),
        ("Docker Hub", "https://hub.docker.com/u/{}", "404", "normal"),
        ("NPM", "https://www.npmjs.com/~{}", "404", "normal"),
        ("PyPI", "https://pypi.org/user/{}", "404", "low"),
        ("Packagist", "https://packagist.org/users/{}", "404", "normal"),
        ("Rubygems", "https://rubygems.org/profiles/{}", "404", "low"),
    ]:
        _add_site(EXTENDED_SITES, name, SiteSpec(url, chk, category="Tech", reliability=rel))

    # Media / portfolio
    for name, url, chk, rel in [
        ("YouTube (legacy)", "https://www.youtube.com/{}", "404", "low"),
        ("Vimeo", "https://vimeo.com/{}", "404", "normal"),
        ("Twitch (alt)", "https://www.twitch.tv/{}", "Sorry. Unless you've got a time machine", "low"),
        ("Bandcamp", "https://{}.bandcamp.com/", "404", "low"),
        ("Last.fm", "https://www.last.fm/user/{}", "User not found", "normal"),
        ("Trakt (alt)", "https://trakt.tv/users/{}", "404", "normal"),
        ("Unsplash", "https://unsplash.com/@{}", "404", "normal"),
        ("Pexels", "https://www.pexels.com/@{}", "404", "normal"),
        ("Pixabay", "https://pixabay.com/users/{}/", "404", "normal"),
        ("Behance", "https://www.behance.net/{}", "We can't find that page", "normal"),
        ("Dribbble", "https://dribbble.com/{}", "404", "normal"),
        ("ArtStation", "https://www.artstation.com/{}", "404", "normal"),
        ("DeviantArt", "https://www.deviantart.com/{}", "404", "normal"),
        ("Wattpad", "https://www.wattpad.com/user/{}", "User not found", "normal"),
        ("AO3", "https://archiveofourown.org/users/{}", "404", "normal"),
        ("Instructables", "https://www.instructables.com/member/{}", "404", "normal"),
        ("Thingiverse", "https://www.thingiverse.com/{}/about", "404", "normal"),
    ]:
        _add_site(EXTENDED_SITES, name, SiteSpec(url, chk, category="Media", reliability=rel))

    # Marketplaces
    for name, url, chk, rel in [
        ("Itch.io", "https://{}.itch.io/", "404", "normal"),
        ("Etsy", "https://www.etsy.com/people/{}", "404", "normal"),
        ("eBay", "https://www.ebay.com/usr/{}", "404", "normal"),
        ("Depop", "https://www.depop.com/{}", "404", "normal"),
        ("Poshmark", "https://poshmark.com/closet/{}", "404", "normal"),
        ("Fiverr", "https://www.fiverr.com/{}", "404", "low"),
    ]:
        _add_site(EXTENDED_SITES, name, SiteSpec(url, chk, category="Marketplaces", reliability=rel))




    # Reference / wiki / directories / misc (high ROI)
    for name, url, chk, rel, cat, notes in [
        ("Wikipedia (EN)", "https://en.wikipedia.org/wiki/User:{}", "There is currently no text in this page", "normal", "Community", ""),
        ("Wikidata", "https://www.wikidata.org/wiki/User:{}", "Wikidata does not have a page with this exact title", "normal", "Community", ""),
        ("Fandom (Community)", "https://community.fandom.com/wiki/User:{}", "There is currently no text in this page", "normal", "Community", ""),
        ("Fandom (Generic)", "https://{}.fandom.com/wiki/User:{}", "There is currently no text in this page", "low", "Community", "Wiki host varies"),
        ("Imgur", "https://imgur.com/user/{}", "404", "normal", "Media", ""),
        ("Gist (GitHub)", "https://gist.github.com/{}", "Not Found", "normal", "Tech", ""),
        ("Medium", "https://medium.com/@{}", "404", "low", "Blogs", "Often JS-heavy"),
        ("Hashnode", "https://hashnode.com/@{}", "404", "low", "Blogs", ""),
        ("Product Hunt", "https://www.producthunt.com/@{}", "404", "low", "Tech", ""),
        ("TradingView", "https://www.tradingview.com/u/{}", "Page not found", "low", "Finance", ""),
        ("Speaker Deck", "https://speakerdeck.com/{}", "404", "normal", "Tech", ""),
        ("SlideShare", "https://www.slideshare.net/{}", "404", "low", "Tech", ""),
        ("Mixcloud", "https://www.mixcloud.com/{}/", "404", "normal", "Media", ""),
        ("OpenSea", "https://opensea.io/{}", "404", "low", "Marketplaces", "Wallet/profile may differ"),
        ("Gumroad (subdomain)", "https://{}.gumroad.com", "404", "low", "Marketplaces", ""),
        ("Gumroad (path)", "https://gumroad.com/{}", "404", "low", "Marketplaces", ""),
        ("Open Collective", "https://opencollective.com/{}", "404", "normal", "Community", ""),
        ("Kick", "https://kick.com/{}", "404", "low", "Social", ""),
        ("Flickr (people)", "https://www.flickr.com/people/{}/", "404", "normal", "Media", ""),
        ("Flickr (photos)", "https://www.flickr.com/photos/{}/", "404", "normal", "Media", ""),
        ("Pastebin (alt)", "https://pastebin.com/u/{}", "Not Found", "normal", "Community", ""),
        ("Archive.org (profile)", "https://archive.org/details/@{}", "404", "low", "Community", ""),
        ("OpenStreetMap (alt)", "https://www.openstreetmap.org/user/{}", "Page not found", "normal", "Community", ""),
    ]:
        _add_site(EXTENDED_SITES, name, SiteSpec(url, chk, category=cat, reliability=rel, notes=notes))


    # More platforms (expanded)
    # Social / professional / identity
    for name, url, chk, rel, cat, notes in [
        ("LinkedIn", "https://www.linkedin.com/in/{}/", "Profile Not Found", "low", "Social", "Often blocks automation / requires login"),
        ("Snapchat", "https://www.snapchat.com/add/{}", "Sorry, this page isn't available", "low", "Social", "May be JS-heavy"),
        ("Minds", "https://www.minds.com/{}/", "404", "low", "Social", ""),
        ("Peerlist", "https://peerlist.io/{}", "404", "low", "Social", "Developer profiles"),
        ("Polywork", "https://www.polywork.com/{}", "404", "low", "Social", "Professional profiles"),
        ("Quora", "https://www.quora.com/profile/{}", "Page not found", "low", "Social", "Often name-based; may not match usernames"),
        ("Meetup", "https://www.meetup.com/members/{}", "404", "low", "Social", "Numeric IDs common"),
        ("Disqus", "https://disqus.com/by/{}/", "404", "low", "Community", "Commenting profiles"),
        ("Trello", "https://trello.com/{}", "Page not found", "low", "Productivity", "Public boards/users vary"),
        ("Keybase", "https://keybase.io/{}", "Not found", "low", "Community", "Service availability may vary"),
    ]:
        _add_site(EXTENDED_SITES, name, SiteSpec(url, chk, category=cat, reliability=rel, notes=notes))

    # Education / learning
    for name, url, chk, rel in [
        ("Duolingo", "https://www.duolingo.com/profile/{}", "404", "low"),
        ("Codecademy", "https://www.codecademy.com/profiles/{}", "404", "low"),
        ("Scratch", "https://scratch.mit.edu/users/{}/", "404", "normal"),
        ("Khan Academy", "https://www.khanacademy.org/profile/{}", "404", "low"),
    ]:
        _add_site(EXTENDED_SITES, name, SiteSpec(url, chk, category="Education", reliability=rel))

    # More dev / tech
    for name, url, chk, rel, notes in [
        ("Hugging Face", "https://huggingface.co/{}", "404", "normal", ""),
        ("StackBlitz", "https://stackblitz.com/@{}", "404", "low", ""),
        ("Glitch", "https://glitch.com/@{}", "404", "low", ""),
        ("JSFiddle", "https://jsfiddle.net/user/{}/", "404", "low", ""),
        ("CodeSandbox", "https://codesandbox.io/u/{}", "404", "low", ""),
        ("Launchpad", "https://launchpad.net/~{}", "404", "normal", ""),
        ("Read the Docs", "https://readthedocs.org/profiles/{}/", "404", "low", "Some users private"),
        ("Gitea.com", "https://gitea.com/{}", "404", "normal", ""),
        ("GitLab (freedesktop)", "https://gitlab.freedesktop.org/{}", "404", "normal", ""),
        ("GitLab (GNOME)", "https://gitlab.gnome.org/{}", "404", "normal", ""),
        ("KDE Invent", "https://invent.kde.org/{}", "404", "normal", ""),
        ("OpenHub", "https://www.openhub.net/accounts/{}", "404", "low", ""),
        ("StackShare", "https://stackshare.io/{}", "404", "low", ""),
        ("OpenProcessing", "https://openprocessing.org/user/{}", "404", "low", ""),
        ("Modrinth", "https://modrinth.com/user/{}", "404", "normal", "Modding profiles"),
    ]:
        _add_site(EXTENDED_SITES, name, SiteSpec(url, chk, category="Tech", reliability=rel, notes=notes))

    # More media / creators
    for name, url, chk, rel in [
        ("500px", "https://500px.com/{}", "404", "low"),
        ("Sketchfab", "https://sketchfab.com/{}", "404", "normal"),
        ("Newgrounds", "https://{}.newgrounds.com/", "404", "low"),
        ("Dailymotion", "https://www.dailymotion.com/{}", "404", "low"),
        ("Issuu", "https://issuu.com/{}", "404", "low"),
        ("Scribd", "https://www.scribd.com/{}", "404", "low"),
        ("BandLab", "https://www.bandlab.com/{}", "404", "low"),
        ("Audiomack", "https://audiomack.com/{}", "404", "low"),
        ("BeatStars", "https://www.beatstars.com/{}", "404", "low"),
        ("ReverbNation", "https://www.reverbnation.com/{}", "404", "low"),
    ]:
        _add_site(EXTENDED_SITES, name, SiteSpec(url, chk, category="Media", reliability=rel))

    # More gaming
    for name, url, chk, rel in [
        ("Speedrun.com", "https://www.speedrun.com/users/{}", "404", "normal"),
        ("Game Jolt", "https://gamejolt.com/@{}", "404", "low"),
        ("Mod DB", "https://www.moddb.com/members/{}", "404", "normal"),
        ("GOG (community)", "https://www.gog.com/u/{}", "404", "low"),
    ]:
        _add_site(EXTENDED_SITES, name, SiteSpec(url, chk, category="Gaming", reliability=rel))

    # More marketplaces
    for name, url, chk, rel in [
        ("Grailed", "https://www.grailed.com/{}", "404", "low"),
        ("Reverb (shop)", "https://reverb.com/shop/{}", "404", "low"),
        ("Ko-fi (alt)", "https://ko-fi.com/{}", "404", "low"),
        ("Liberapay", "https://liberapay.com/{}/", "404", "low"),
        ("Payhip", "https://payhip.com/{}", "404", "low"),
    ]:
        cat = "Payments" if name in {"Liberapay", "Payhip", "Ko-fi (alt)"} else "Marketplaces"
        _add_site(EXTENDED_SITES, name, SiteSpec(url, chk, category=cat, reliability=rel))

    # More wikis / community user pages
    for name, url, chk in [
        ("MediaWiki", "https://www.mediawiki.org/wiki/User:{}", "There is currently no text in this page"),
        ("Miraheze (Meta)", "https://meta.miraheze.org/wiki/User:{}", "There is currently no text in this page"),
        ("Wiktionary (EN)", "https://en.wiktionary.org/wiki/User:{}", "There is currently no text in this page"),
        ("Wikibooks (EN)", "https://en.wikibooks.org/wiki/User:{}", "There is currently no text in this page"),
    ]:
        _add_site(EXTENDED_SITES, name, SiteSpec(url, chk, category="Community", reliability="low"))


add_extended_sites()


# --- Forums pack: Discourse communities (/u/{user}/summary) ---
DISCOURSE_HOSTS = [
    "meta.discourse.org", "discuss.python.org", "discourse.mozilla.org", "discourse.ubuntu.com",
    "discussion.fedoraproject.org", "forums.docker.com", "community.cloudflare.com", "community.grafana.com",
    "community.home-assistant.io", "community.letsencrypt.org", "community.bitwarden.com",
    "forums.plex.tv", "forums.unrealengine.com", "discuss.hashicorp.com", "discuss.elastic.co",
    "discuss.kubernetes.io", "discuss.gradle.org", "discuss.pytorch.org", "discuss.tensorflow.org",
    "discuss.streamlit.io", "community.atlassian.com", "community.shopify.com", "community.adobe.com",
    "community.autodesk.com", "community.tableau.com", "community.zendesk.com", "community.salesforce.com",
    "community.zoom.com", "community.roku.com", "community.nvidia.com", "community.intel.com",
    "community.amd.com", "community.vivaldi.net", "community.brave.com",
    "forum.manjaro.org", "forums.opensuse.org", "forums.freebsd.org", "forum.proxmox.com",
    "forum.opnsense.org", "forum.mikrotik.com", "discuss.linuxcontainers.org", "discuss.privacyguides.net",
    "forum.torproject.net", "community.digitalocean.com", "community.linode.com",
    "community.signalusers.org", "community.wire.com", "community.ui.com", "community.mattermost.com",
    # extra open-source communities
    "discuss.rust-lang.org", "discuss.rubyonrails.org", "community.blender.org", "community.joplinapp.org",
    "community.obsproject.com", "community.netdata.cloud", "community.openvpn.net", "community.fly.io",
    # more communities
    "forum.snapcraft.io", "community.openhab.org", "community.traefik.io", "forum.level1techs.com", "discuss.huggingface.co", "discuss.haskell.org", "discuss.ocaml.org", "discuss.haproxy.org", "discuss.zeromq.org", "discuss.helm.sh", "discuss.cilium.io", "discuss.dapr.io", "discuss.envoyproxy.io", "discuss.istio.io", "community.postman.com", "community.algolia.com", "community.databricks.com", "community.mongodb.com", "community.neo4j.com", "community.sonarsource.com", "community.splunk.com", "community.influxdata.com", "community.gohugo.io", "community.gitea.io", "community.n8n.io", "forum.fairphone.com", "discuss.kde.org", "community.syncthing.net", "community.gnome.org", "forums.ankiweb.net", "forum.djangoproject.com", "talk.yunohost.org", "discuss.caprover.com", "discourse.pi-hole.net", "community.nodered.org", "community.openwrt.org", "discuss.openedx.org",
    "forum.obsidian.md",
    "discourse.julialang.org",
    "discuss.grapheneos.org",
    "community.openvpn.net",
    "forum.arduino.cc",
    "community.riot.im",
    "community.matrix.org",
    "community.zerotier.com",
    "discuss.swift.org",
    "forums.swift.org",
    "community.pulumi.com",
    "discuss.astro.build",
    "community.prusa3d.com",
    "community.ansible.com",
    "discuss.lensfun.org",
    "community.ohmyposh.dev",
    "forum.nim-lang.org",
    "discuss.golang.org",
    "discuss.python.org",
    "discourse.mcneel.com",
    "community.nitrokey.com",
    "community.gamedev.tv",
    "discuss.krita.org",
    "community.zephyrproject.org",
    "community.synology.com",
    "forums.plex.tv",
    "forums.ankiweb.net",
    "community.spiceworks.com",
    "discuss.tryton.org",

]


def add_forums() -> None:
    for host in sorted(set(DISCOURSE_HOSTS)):
        name = f"Forum ({host})"
        url = f"https://{host}/u/{{}}/summary"
        _add_site(FORUM_SITES, name, SiteSpec(url, None, category="Forums", reliability="low", notes="Discourse-style forum"))


add_forums()


# --- Fediverse pack: instance-based profiles (expanded) ---
MASTODON_INSTANCES = [
    "mastodon.social", "fosstodon.org", "hachyderm.io", "mastodon.world", "mstdn.social",
    "infosec.exchange", "techhub.social", "mastodon.online", "mastodon.cloud", "mastodon.art",
    "toots.social", "mathstodon.xyz", "scholar.social", "androiddev.social", "social.vivaldi.net",
    "mastodon.uno", "mastodon.app", "mastodon.green", "mastodon.ie", "mastodon.nz",
    "mastodon.scot", "indieweb.social", "mas.to", "mastodon.nl", "mastodon.sdf.org",
    "chaos.social", "social.tchncs.de", "metalhead.club", "front-end.social", "kolektiva.social",
    "mastodon.cat", "mastodon.es", "mastodon.it", "mastodon.fr", "mastodon.de", "mstdn.jp",
    "mastodon.lol", "mastodon.energy", "mastodon.gamedev.place", "mastodon.au", "c.im",
    "mastodon.boston", "mastodon.berlin", "mastodon.paris", "mastodon.gay",
    # extra instances
    "journa.host", "mastodon.education", "mastodon.science", "mastodon.top", "mastodon.pro",
    "mastodon.dev", "social.sdf.org", "mastodon.technology", "mstdn.party", "social.treehouse.systems",
    # more instances
    "social.opensource.org", "mastodon.gnome.org", "social.fossdroid.com", "mastodon.iftas.org", "social.linux.pizza", "social.freedombox.org", "social.nixos.org", "mastodon.africa", "mastodon.pt", "mastodon.se", "mastodon.no", "mastodon.pl",
    "mastodon.xyz",
    "mastodon.instance.social",
    "masto.ai",
    "masto.nu",
    "mastodon.frl",
    "mastodon.juggler.jp",
    "mstdn.io",
    "octodon.social",
    "mastodon.im",
    "mastodon.sandwich.net",
    "masto.pt",
    "mastodon.ro",
    "mastodon.fi",
    "mastodon.is",

]

PIXELFED_INSTANCES = [
    "pixelfed.social", "pixelfed.de", "pixelfed.eu", "pixelfed.uno", "pixelfed.art",
    "pixelfed.fr", "pixelfed.nl", "pixelfed.tokyo", "pixelfed.cloud", "pixelfed.cz",
    "pixelfed.au", "pixelfed.co.za",    "pixelfed.rocks",
    "pixelfed.dk",
    "pixelfed.ie",
    "pixelfed.es",
    "pixelfed.it",

]

LEMMY_INSTANCES = [
    "lemmy.world", "lemmy.ml", "beehaw.org", "sh.itjust.works", "lemmy.ca", "programming.dev",
    "lemm.ee", "lemmy.one", "lemmy.dbzer0.com", "sopuli.xyz", "feddit.de",
    "feddit.uk", "feddit.it", "lemmy.today", "lemmy.eco", "lemmy.fmhy.net",
    "lemmygrad.ml",    "lemmy.kya.moe",
    "lemmynsfw.com",
    "lemmy.zip",
    "lemmy.sdf.org",
    "lemmy.blahaj.zone",

]

KBIN_INSTANCES = ["kbin.social", "kbin.life", "kbin.earth"]
MISSKEY_INSTANCES = ["misskey.io", "misskey.social", "misskey.de", "misskey.design", "misskey.tokyo", "misskey.dev"]
PEERTUBE_INSTANCES = ["tilvids.com", "framatube.org", "peertube.social", "peertube.tv", "video.ploud.jp", "video.linux.it"]


def add_fediverse() -> None:
    for inst in sorted(set(MASTODON_INSTANCES)):
        _add_site(FEDIVERSE_SITES, f"Mastodon ({inst})", SiteSpec(f"https://{inst}/@{{}}", "404", category="Fediverse", reliability="low"))
    for inst in sorted(set(PIXELFED_INSTANCES)):
        _add_site(FEDIVERSE_SITES, f"Pixelfed ({inst})", SiteSpec(f"https://{inst}/{{}}", "404", category="Fediverse", reliability="low"))
    for inst in sorted(set(LEMMY_INSTANCES)):
        _add_site(FEDIVERSE_SITES, f"Lemmy ({inst})", SiteSpec(f"https://{inst}/u/{{}}", "404", category="Fediverse", reliability="low"))
    for inst in sorted(set(KBIN_INSTANCES)):
        _add_site(FEDIVERSE_SITES, f"kbin ({inst})", SiteSpec(f"https://{inst}/u/{{}}", "404", category="Fediverse", reliability="low"))
    for inst in sorted(set(MISSKEY_INSTANCES)):
        _add_site(FEDIVERSE_SITES, f"Misskey ({inst})", SiteSpec(f"https://{inst}/@{{}}", "404", category="Fediverse", reliability="low"))
    for inst in sorted(set(PEERTUBE_INSTANCES)):
        _add_site(FEDIVERSE_SITES, f"PeerTube ({inst})", SiteSpec(f"https://{inst}/accounts/{{}}", "404", category="Fediverse", reliability="low"))


add_fediverse()


PACKS: Dict[str, Dict[str, SiteSpec]] = {
    "core": CORE_SITES,
    "extended": EXTENDED_SITES,
    "forums": FORUM_SITES,
    "fediverse": FEDIVERSE_SITES,
}


def build_sites(pack: str) -> Dict[str, SiteSpec]:
    """Build the active site dict for a selected pack."""
    pack = (pack or "").strip().lower()
    if pack == "everything":
        merged: Dict[str, SiteSpec] = {}
        for p in ("core", "extended", "forums", "fediverse"):
            merged.update(PACKS[p])
        return merged
    if pack in PACKS:
        return dict(PACKS[pack])
    # default fallback
    merged = dict(CORE_SITES)
    merged.update(EXTENDED_SITES)
    merged.update(FORUM_SITES)
    merged.update(FEDIVERSE_SITES)
    return merged


# ----------------------------------------------------------------------
# Optional local site extension (JSON)
# ----------------------------------------------------------------------

def load_extra_sites_json(path: str) -> Dict[str, SiteSpec]:
    """Load user-supplied site specs from JSON."""
    extra: Dict[str, SiteSpec] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return extra
        for name, obj in data.items():
            if not isinstance(name, str) or not isinstance(obj, dict):
                continue
            url = str(obj.get("url", "")).strip()
            if "{}" not in url or not url.startswith(("http://", "https://")):
                continue
            extra[name.strip()] = SiteSpec(
                url=url,
                check_str=(obj.get("check_str") or None),
                error_url=(obj.get("error_url") or None),
                category=str(obj.get("category", "General")),
                reliability=str(obj.get("reliability", "normal")),
                notes=str(obj.get("notes", "")),
                positive_hint=(obj.get("positive_hint") or None),
            )
    except Exception:
        return extra
    return extra


def export_sites_json(path: str, sites: Dict[str, SiteSpec]) -> None:
    payload: Dict[str, dict] = {}
    for name, spec in sorted(sites.items(), key=lambda x: x[0].lower()):
        payload[name] = {
            "url": spec.url,
            "check_str": spec.check_str,
            "error_url": spec.error_url,
            "category": spec.category,
            "reliability": spec.reliability,
            "notes": spec.notes,
            "positive_hint": spec.positive_hint,
        }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


# ----------------------------------------------------------------------
# Sherlock loader (cached)
# ----------------------------------------------------------------------

def load_sherlock_sites(session: requests.Session, cache_path: str, refresh: bool, include_nsfw: bool) -> Dict[str, SiteSpec]:
    """Download Sherlock's data.json and convert to SiteSpec."""
    data_text: Optional[str] = None

    if (not refresh) and os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data_text = f.read()
        except Exception:
            data_text = None

    if data_text is None:
        print(f"{Fore.BLUE}[*] Λήψη βάσης δεδομένων ιστότοπων Sherlock...{Style.RESET_ALL}")
        try:
            r = session.get(SHERLOCK_DATA_URL, timeout=(6.0, 30.0), headers={"User-Agent": random.choice(USER_AGENTS)})
            r.raise_for_status()
            data_text = r.text
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    f.write(data_text)
            except Exception:
                pass
        except Exception as e:
            print(f"{Fore.RED}[!] Δεν ήταν δυνατή η λήψη της βάσης Sherlock: {e}{Style.RESET_ALL}")
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        data_text = f.read()
                except Exception:
                    return {}
            else:
                return {}

    try:
        data = json.loads(data_text)
    except Exception:
        return {}

    if not isinstance(data, dict):
        return {}

    out: Dict[str, SiteSpec] = {}

    for site_name, obj in data.items():
        if not isinstance(site_name, str) or site_name.startswith("$"):
            continue
        if not isinstance(obj, dict):
            continue
        if bool(obj.get("isNSFW", False)) and not include_nsfw:
            continue

        url = str(obj.get("url", "")).strip()
        if not url.startswith(("http://", "https://")) or "{}" not in url:
            continue

        error_type = str(obj.get("errorType", "")).strip().lower()
        error_msg = obj.get("errorMsg")
        error_url = obj.get("errorUrl") or None

        check_str: Optional[str] = None
        if error_type == "message":
            if isinstance(error_msg, list) and error_msg:
                check_str = str(error_msg[0])
            elif isinstance(error_msg, str):
                check_str = error_msg
        elif error_type == "response_url":
            # handled via error_url comparison
            pass
        else:
            error_url = None

        # Sherlock sites are frequently automation-sensitive: mark low reliability by default.
        out[f"Sherlock: {site_name}"] = SiteSpec(
            url=url,
            check_str=check_str,
            error_url=error_url,
            category="Sherlock",
            reliability="low",
            notes=f"Sherlock errorType={error_type or 'unknown'}",
        )

    return out


# ----------------------------------------------------------------------
# API checks (fast, high-confidence)
# ----------------------------------------------------------------------

def check_github_api(session: requests.Session, username: str, timeout: Tuple[float, float]) -> Tuple[bool, Optional[str], Optional[str]]:
    url = f"https://api.github.com/users/{username}"
    try:
        r = session.get(url, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            return True, data.get("html_url"), f"Name: {data.get('name')}"
    except Exception:
        pass
    return False, None, None


def check_gravatar_api(session: requests.Session, username: str, timeout: Tuple[float, float]) -> Tuple[bool, Optional[str], Optional[str]]:
    url = f"https://en.gravatar.com/{username}.json"
    try:
        r = session.get(url, timeout=timeout, headers={"User-Agent": random.choice(USER_AGENTS)})
        if r.status_code == 200:
            data = r.json()
            profile_url = data.get("entry", [{}])[0].get("profileUrl")
            if profile_url:
                return True, profile_url, "Gravatar Profile"
    except Exception:
        pass
    return False, None, None


# ----------------------------------------------------------------------
# DuckDuckGo HTML dork search (best-effort)
# ----------------------------------------------------------------------

def _extract_ddg_real_url(href: str) -> str:
    try:
        u = urlparse(href)
        qs = parse_qs(u.query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    except Exception:
        pass
    return href


def dork_search(session: requests.Session, username: str, timeout: Tuple[float, float], top_n: int = 10) -> List[Tuple[str, str]]:
    print(f"\n{Fore.YELLOW}[*] Έλεγχος μηχανής αναζήτησης (DuckDuckGo HTML) για '{username}'...{Style.RESET_ALL}")
    query = f'"{username}"'
    url = f"https://html.duckduckgo.com/html/?q={query}"
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    found_links: List[Tuple[str, str]] = []

    try:
        resp = session.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            results = soup.find_all("a", class_="result__a")
            for res in results[:max(1, min(int(top_n), 30))]:
                link = res.get("href") or ""
                title = (res.get_text() or "").strip()
                if not link:
                    continue
                real = _extract_ddg_real_url(link)
                if "duckduckgo" not in real and "search" not in real:
                    found_links.append((title, real))
        else:
            print(f"{Fore.RED}[!] Η αναζήτηση επέστρεψε HTTP {resp.status_code}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[!] Η αναζήτηση απέτυχε: {e}{Style.RESET_ALL}")

    return found_links


# ----------------------------------------------------------------------
# Core scanning logic
# ----------------------------------------------------------------------

@dataclass
class ScanResult:
    site: str
    category: str
    input_url: str
    final_url: str
    status: int
    confidence: str  # FOUND | POSSIBLE
    reason: str


def build_session() -> requests.Session:
    """Create a requests session with pooled retries."""
    session = requests.Session()
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        backoff_factor=0.55,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=80, pool_maxsize=80)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def safe_filename(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
    return name[:64] if name else "user"


def _norm_url(u: str) -> str:
    try:
        p = urlparse(u)
        return f"{p.scheme}://{p.netloc}{p.path}".rstrip("/")
    except Exception:
        return u.rstrip("/")


def extract_title_fast(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    return re.sub(r"\s+", " ", m.group(1)).strip()


def extract_meta_fast(html: str, prop: str) -> str:
    pattern = rf'<meta[^>]+(?:property|name)\s*=\s*["\']{re.escape(prop)}["\'][^>]+content\s*=\s*["\']([^"\']+)["\']'
    m = re.search(pattern, html, flags=re.IGNORECASE)
    return (m.group(1).strip() if m else "")


def extract_canonical_fast(html: str) -> str:
    m = re.search(r'<link[^>]+rel\s*=\s*["\']canonical["\'][^>]+href\s*=\s*["\']([^"\']+)["\']', html, flags=re.I)
    return (m.group(1).strip() if m else "")


def looks_like_login_or_generic(final_url: str) -> bool:
    try:
        u = urlparse(final_url)
        path_q = (u.path + "?" + (u.query or "")).lower()
        return any(k in path_q for k in SUSPICIOUS_REDIRECT_PATH_KEYWORDS)
    except Exception:
        return False


def looks_like_antibot(html_lower: str, title_lower: str) -> bool:
    hay = (title_lower + " " + html_lower)[:25000]
    return any(k in hay for k in ANTIBOT_INDICATORS)


def looks_like_js_shell(html_lower: str) -> bool:
    hints = [
        "enable javascript", "you need to enable javascript",
        "id=\"__next\"", "id=\"root\"", "data-reactroot",
        "<noscript>",
    ]
    return any(h in html_lower for h in hints)


def bounded_fetch_text(resp: requests.Response, max_bytes: int) -> str:
    """Read up to max_bytes from a streaming response."""
    try:
        content = b""
        for chunk in resp.iter_content(chunk_size=16384):
            if not chunk:
                break
            content += chunk
            if len(content) >= max_bytes:
                break
        try:
            return content.decode(resp.encoding or "utf-8", errors="ignore")
        except Exception:
            return content.decode("utf-8", errors="ignore")
    except Exception:
        try:
            return (resp.text or "")[:max_bytes]
        except Exception:
            return ""


def contains_user_token(text_lower: str, user_lower: str) -> bool:
    """Word-ish boundary match for usernames (reduces substring false positives)."""
    if not user_lower:
        return False
    pattern = rf"(?i)(^|[^a-z0-9_]){re.escape(user_lower)}([^a-z0-9_]|$)"
    return re.search(pattern, text_lower) is not None



def compute_url_signal(final_url: str, username: str) -> Tuple[int, List[str]]:
    """Lightweight URL-based signal. Helps avoid misses when pages are minimal."""
    user_l = (username or "").lower().lstrip("@")
    signals: List[str] = []
    score = 0
    if not user_l or not final_url:
        return 0, signals
    try:
        u = urlparse(final_url)
        host = (u.netloc or "").lower().split(":")[0]
        parts = [p for p in host.split(".") if p]
        if parts and parts[0] == user_l and len(parts) >= 2:
            signals.append("subdomain")
            score += 2

        path = (u.path or "").lower()
        segs = [seg for seg in path.split("/") if seg]
        for seg in segs[:8]:
            if seg == user_l or seg == f"@{user_l}" or seg == f"~{user_l}":
                signals.append("path")
                score += 1
                break
            if seg.startswith("@") and seg[1:] == user_l:
                signals.append("path")
                score += 1
                break

        q = (u.query or "").lower()
        if any(k in q for k in [f"user={user_l}", f"username={user_l}", f"handle={user_l}"]):
            signals.append("query")
            score += 1
    except Exception:
        pass
    return score, signals

def compute_signal_score(html: str, username: str, spec: SiteSpec) -> Tuple[int, List[str]]:
    """Return (score, signals). Higher score => more confident match."""
    user_l = username.lower()
    signals: List[str] = []
    score = 0

    title = extract_title_fast(html)
    title_l = title.lower().strip()

    # Title is a strong signal
    if title_l and (contains_user_token(title_l, user_l) or f"@{user_l}" in title_l):
        signals.append("title")
        score += 3

    og_title = extract_meta_fast(html, "og:title").lower()
    tw_title = extract_meta_fast(html, "twitter:title").lower()
    if og_title and (contains_user_token(og_title, user_l) or f"@{user_l}" in og_title):
        signals.append("og:title")
        score += 2
    if tw_title and (contains_user_token(tw_title, user_l) or f"@{user_l}" in tw_title):
        signals.append("twitter:title")
        score += 2

    canonical = extract_canonical_fast(html).lower()
    og_url = extract_meta_fast(html, "og:url").lower()
    if canonical and user_l in canonical:
        signals.append("canonical")
        score += 2
    if og_url and user_l in og_url:
        signals.append("og:url")
        score += 2

    # Optional positive regex hint
    if spec.positive_hint:
        try:
            patt = spec.positive_hint.replace("{}", re.escape(username))
            if re.search(patt, html, flags=re.I):
                signals.append("positive_hint")
                score += 2
        except Exception:
            pass

    # Visible text signal (more expensive)
    if score < 4:
        try:
            soup = BeautifulSoup(html, "lxml")
            for tag in soup(["script", "style", "noscript"]):
                tag.extract()
            text_l = soup.get_text(" ", strip=True).lower()
            if contains_user_token(text_l, user_l) or f"@{user_l}" in text_l:
                signals.append("visible_text")
                score += 2
        except Exception:
            pass

    return score, signals


class DomainLimiter:
    """Limit concurrent requests per domain (helps reduce blocks)."""

    def __init__(self, per_domain: int) -> None:
        self.per_domain = max(1, int(per_domain))
        self._locks: Dict[str, concurrent.futures.thread.Lock] = {}
        self._sems: Dict[str, "threading.Semaphore"] = {}

    def _get_sem(self, domain: str):
        import threading
        if domain not in self._sems:
            self._sems[domain] = threading.Semaphore(self.per_domain)
        return self._sems[domain]

    def acquire(self, url: str):
        import threading
        dom = ""
        try:
            dom = urlparse(url).netloc.lower()
        except Exception:
            dom = ""
        if not dom:
            dom = "_"
        sem = self._get_sem(dom)
        sem.acquire()
        return (dom, sem)

    def release(self, token) -> None:
        try:
            _, sem = token
            sem.release()
        except Exception:
            pass


def analyze_site(
    session: requests.Session,
    limiter: DomainLimiter,
    site_name: str,
    spec: SiteSpec,
    username: str,
    timeout: Tuple[float, float],
    jitter: Tuple[float, float],
    max_html_bytes: int,
    verbose: bool = False,
) -> Optional[ScanResult]:
    input_url = spec.url.format(username)

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    if jitter[1] > 0:
        time.sleep(random.uniform(jitter[0], jitter[1]))

    token = limiter.acquire(input_url)
    try:
        # HEAD-first (cheap)
        try:
            hr = session.head(input_url, headers=headers, timeout=timeout, allow_redirects=True)
            hs = int(getattr(hr, "status_code", 0) or 0)
            hu = getattr(hr, "url", input_url) or input_url

            if hs in (404, 410):
                return None
            if hs in UNCERTAIN_STATUS:
                return ScanResult(site_name, spec.category, input_url, hu, hs, "POSSIBLE", f"HTTP {hs} (μπλοκαρίστηκε/περιορισμός ρυθμού)")
            if looks_like_login_or_generic(hu) and spec.reliability != "low":
                return None
        except Exception:
            pass

        # GET (streamed)
        try:
            gr = session.get(input_url, headers=headers, timeout=timeout, allow_redirects=True, stream=True)
        except Exception as e:
            if verbose:
                print(f"{Fore.RED}Σφάλμα κατά τον έλεγχο του {site_name}: {e}{Style.RESET_ALL}")
            return ScanResult(site_name, spec.category, input_url, input_url, 0, "POSSIBLE", "Σφάλμα δικτύου / μπλοκαρίστηκε")

        status = int(getattr(gr, "status_code", 0) or 0)
        final_url = getattr(gr, "url", input_url) or input_url

        # Sherlock response_url negative
        if spec.error_url:
            try:
                if _norm_url(final_url) == _norm_url(str(spec.error_url)):
                    return None
            except Exception:
                pass

        if status in (404, 410):
            return None
        if status in UNCERTAIN_STATUS:
            return ScanResult(site_name, spec.category, input_url, final_url, status, "POSSIBLE", f"HTTP {status} (blocked/rate-limited)")
        if status >= 500:
            return ScanResult(site_name, spec.category, input_url, final_url, status, "POSSIBLE", f"HTTP {status} (σφάλμα διακομιστή)")

        if looks_like_login_or_generic(final_url):
            if spec.reliability == "low":
                return ScanResult(site_name, spec.category, input_url, final_url, status, "POSSIBLE", "Ανακατεύθυνση σε γενική/σελίδα σύνδεσης")
            return None

        ctype = (gr.headers.get("Content-Type") or "").lower()
        if ctype and ("text/html" not in ctype and "application/xhtml" not in ctype and "application/json" not in ctype):
            # Some profiles return JSON or non-HTML; keep conservative
            return ScanResult(site_name, spec.category, input_url, final_url, status, "POSSIBLE", f"Μη HTML content-type: {ctype.split(';')[0]}")

        html = bounded_fetch_text(gr, max_html_bytes)
        html_lower = html.lower()
        title_lower = extract_title_fast(html).lower().strip()

        if looks_like_antibot(html_lower, title_lower):
            return ScanResult(site_name, spec.category, input_url, final_url, status, "POSSIBLE", "Σελίδα anti-bot/πρόκλησης")

        if any(err in html_lower for err in GLOBAL_ERROR_INDICATORS):
            return None

        if spec.check_str:
            try:
                chk = spec.check_str.format(username).lower() if "{}" in spec.check_str else str(spec.check_str).lower()
                if chk and chk in html_lower:
                    return None
            except Exception:
                pass

        if title_lower in GENERIC_TITLES and spec.reliability != "low":
            return None

        if looks_like_js_shell(html_lower) and spec.reliability == "low":
            return ScanResult(site_name, spec.category, input_url, final_url, status, "POSSIBLE", "Σελίδα-κέλυφος με βαριά JS")

        score, signals = compute_signal_score(html, username, spec)
        u_score, u_signals = compute_url_signal(final_url, username)
        if u_score:
            score += u_score
            signals.extend(u_signals)

        # Thresholds tuned for conservative detection
        if spec.reliability == "low":
            if score >= 6:
                return ScanResult(site_name, spec.category, input_url, final_url, status, "FOUND", f"Ισχυρά σήματα: {', '.join(signals)}")
            return ScanResult(site_name, spec.category, input_url, final_url, status, "POSSIBLE", "Ασθενή σήματα (ο ιστότοπος συχνά μπλοκάρει αυτοματισμούς)")

        if score >= 5:
            return ScanResult(site_name, spec.category, input_url, final_url, status, "FOUND", f"Ισχυρά σήματα: {', '.join(signals)}")

        return ScanResult(site_name, spec.category, input_url, final_url, status, "POSSIBLE", "Δεν υπάρχουν ισχυρά σήματα προφίλ")

    finally:
        limiter.release(token)


# ----------------------------------------------------------------------
# Output / Saving
# ----------------------------------------------------------------------

def get_save_dir() -> str:
    """Prefer Termux downloads folder when available."""
    base_dir = os.path.join(os.path.expanduser("~"), "storage", "downloads")
    if not os.path.exists(base_dir):
        if os.path.exists("/sdcard/Download"):
            base_dir = "/sdcard/Download"
        elif os.path.exists(os.path.expanduser("~")):
            base_dir = os.path.expanduser("~")
        else:
            base_dir = "."
    save_dir = os.path.join(base_dir, "Digital Footprint Finder")
    try:
        os.makedirs(save_dir, exist_ok=True)
    except Exception:
        save_dir = "."
    return save_dir


def print_result(res: ScanResult) -> None:
    if res.confidence == "FOUND":
        color = Fore.GREEN
        tag = "[+]"
    else:
        color = Fore.YELLOW
        tag = "[?]"
    print(f"{color}{tag} {res.site.ljust(34)}{Style.RESET_ALL}: {Fore.WHITE}{res.final_url}{Style.RESET_ALL}")


def dedup(results: List[ScanResult]) -> List[ScanResult]:
    seen = set()
    out = []
    for r in results:
        key = (r.site.lower(), _norm_url(r.final_url).lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def group_by_category(results: List[ScanResult]) -> Dict[str, List[ScanResult]]:
    out: Dict[str, List[ScanResult]] = {}
    for r in results:
        out.setdefault(r.category, []).append(r)
    for k in out:
        out[k].sort(key=lambda x: x.site.lower())
    return dict(sorted(out.items(), key=lambda x: x[0].lower()))


def save_html_report(path: str, username: str, found: List[ScanResult], possible: List[ScanResult], dorks: List[Tuple[str, str]], meta: dict) -> None:
    def esc(s: str) -> str:
        return html_escape.escape(s, quote=True)

    def section(title: str, items: List[ScanResult]) -> str:
        rows = []
        for r in items:
            rows.append(
                f"<tr><td>{esc(r.category)}</td><td>{esc(r.site)}</td><td><a href='{esc(r.final_url)}' target='_blank' rel='noreferrer'>{esc(r.final_url)}</a></td><td>{r.status}</td><td>{esc(r.reason)}</td></tr>"
            )
        if not rows:
            rows.append(f"<tr><td colspan='5'><em>None</em></td></tr>")
        return (
            f"<h2>{esc(title)} ({len(items)})</h2>\n"
            "<table>\n<tr><th>Κατηγορία</th><th>Ιστότοπος</th><th>URL</th><th>HTTP</th><th>Αιτία</th></tr>\n"
            + "\n".join(rows)
            + "\n</table>\n"
        )

    dork_rows = []
    for t, u in dorks:
        dork_rows.append(f"<li><a href='{esc(u)}' target='_blank' rel='noreferrer'>{esc(t or u)}</a></li>")
    if not dork_rows:
        dork_rows.append("<li><em>None</em></li>")

    style = """
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,sans-serif;margin:24px;}
    h1{margin-bottom:0.2rem;}
    .meta{color:#555;margin-bottom:1.2rem;}
    table{border-collapse:collapse;width:100%;margin:10px 0 24px 0;}
    th,td{border:1px solid #ddd;padding:8px;vertical-align:top;}
    th{background:#f3f3f3;text-align:left;}
    .chip{display:inline-block;padding:2px 8px;border-radius:999px;background:#eee;margin-right:6px;font-size:12px;}
    """

    html_doc = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>Εντοπιστής Ψηφιακού Αποτυπώματος - {esc(username)}</title>
<style>{style}</style></head>
<body>
<h1>Εντοπιστής Ψηφιακού Αποτυπώματος</h1>
<div class='meta'>
  <span class='chip'>Όνομα χρήστη: <strong>{esc(username)}</strong></span>
  <span class='chip'>Δημιουργήθηκε: {esc(meta.get('generated',''))}</span>
  <span class='chip'>Πακέτο: {esc(meta.get('pack',''))}</span>
  <span class='chip'>Ιστότοποι που ελέγχθηκαν: {esc(str(meta.get('scanned',0)))}</span>
  <span class='chip'>Ασφαλής λειτουργία: {esc(str(meta.get('safe',False)))}</span>
</div>
{section('ΒΡΕΘΗΚΕ (υψηλότερη βεβαιότητα)', found)}
{section('ΠΙΘΑΝΟ (μπλοκαρισμένο/JS/σύνδεση/ασθενή σήματα)', possible)}
<h2>Αποτελέσματα μηχανής αναζήτησης (DuckDuckGo HTML)</h2>
<ul>\n{''.join(dork_rows)}\n</ul>
<p style='color:#666'>Σημείωση: Το εργαλείο δεν παρακάμπτει προστασίες. Πολλοί ιστότοποι μπλοκάρουν αυτοματοποιημένους ελέγχους.</p>
</body></html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html_doc)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Digital Footprint Finder - συντηρητικοί έλεγχοι παρουσίας ονόματος χρήστη σε πολλές πλατφόρμες."
    )
    parser.add_argument("username", nargs="?", help="Όνομα χρήστη προς έλεγχο")
    parser.add_argument("--pack", default="mega",
                        help="Πακέτο ιστότοπων: core | extended | forums | fediverse | everything | sherlock | mega (προεπιλογή: mega)")
    parser.add_argument("--sherlock-refresh", action="store_true", help="Υποχρεωτική επαναλήψη λήψης της βάσης Sherlock (όταν χρησιμοποιείται sherlock/mega)")
    parser.add_argument("--include-nsfw", action="store_true", help="Συμπερίληψη NSFW ιστότοπων του Sherlock (ΔΕΝ συνιστάται)")
    parser.add_argument("--max-sites", type=int, default=0, help="Όριο αριθμού ιστότοπων προς έλεγχο (0 = χωρίς όριο)")
    parser.add_argument("--extra-sites", default="", help="Φόρτωση επιπλέον ιστότοπων από αρχείο JSON (δες --export-sites)")
    parser.add_argument("--export-sites", default="", help="Εξαγωγή της *ενεργής* λίστας ιστότοπων (μετά τη συγχώνευση pack/extra) σε JSON και έξοδος")
    parser.add_argument("--list-packs", action="store_true", help="Λίστα πακέτων και έξοδος")
    parser.add_argument("--stats", action="store_true", help="Εμφάνιση στατιστικών κατηγοριών πριν τον έλεγχο")
        # Default: show POSSIBLE live. Use --no-show-possible to hide (Python 3.9+).
    try:
        _BoolOpt = argparse.BooleanOptionalAction
    except AttributeError:
        _BoolOpt = None
    if _BoolOpt:
        parser.add_argument("--show-possible", action=_BoolOpt, default=True,
                            help="Εμφάνιση POSSIBLE αποτελεσμάτων σε πραγματικό χρόνο (προεπιλογή: ενεργό). Χρησιμοποίησε --no-show-possible για απόκρυψη.")
    else:
        # Fallback for older Python: default on, allow --hide-possible
        parser.add_argument("--show-possible", action="store_true", default=True,
                            help="Εμφάνιση POSSIBLE αποτελεσμάτων σε πραγματικό χρόνο (προεπιλογή: ενεργό)")
        parser.add_argument("--hide-possible", action="store_false", dest="show_possible",
                            help="Απόκρυψη POSSIBLE αποτελεσμάτων σε πραγματικό χρόνο")
    parser.add_argument("-v", "--verbose", action="store_true", help="Εμφάνιση σφαλμάτων δικτύου/ανάλυσης")
    parser.add_argument("-t", "--threads", type=int, default=18, help="Μέγιστος αριθμός worker threads (προεπιλογή: 18)")
    parser.add_argument("--domain-limit", type=int, default=2, help="Μέγιστες ταυτόχρονες αιτήσεις ανά domain (προεπιλογή: 2)")
    parser.add_argument("--timeout", type=float, default=12.0, help="Timeout αιτήματος σε δευτερόλεπτα (προεπιλογή: 12)")
    parser.add_argument("--connect-timeout", type=float, default=5.0, help="Timeout σύνδεσης σε δευτερόλεπτα (προεπιλογή: 5)")
    parser.add_argument("--max-html-kb", type=int, default=int(DEFAULT_MAX_HTML_BYTES/1000), help="Μέγιστο HTML (KB) που κατεβαίνει ανά ιστότοπο (προεπιλογή: 250)")
    parser.add_argument("--no-dork", action="store_true", help="Απενεργοποίηση ελέγχου μηχανής αναζήτησης")
    parser.add_argument("--dork-top", type=int, default=10, help="Πόσα αποτελέσματα αναζήτησης να συμπεριληφθούν (προεπιλογή: 10)")
    parser.add_argument("--no-apis", action="store_true", help="Απενεργοποίηση ελέγχων API (GitHub/Gravatar)")
    parser.add_argument("--safe", action="store_true",
                        help="Παράλειψη κατηγοριών που είναι πιο πιθανό να είναι ευαίσθητες/μπλοκαρισμένες (Payments, Dating, NSFW)")
    parser.add_argument("--json", action="store_true", help="Επιπλέον αποθήκευση JSON μαζί με την αναφορά TXT")
    parser.add_argument("--csv", action="store_true", help="Επιπλέον αποθήκευση CSV μαζί με την αναφορά TXT")
    parser.add_argument("--html", action="store_true", help="Επιπλέον αποθήκευση αναφοράς HTML μαζί με την αναφορά TXT")
    parser.add_argument("--jitter", type=float, default=0.18,
                        help="Μέγιστη τυχαία καθυστέρηση (δευτ.) πριν από κάθε αίτημα (προεπιλογή: 0.18)")
    args = parser.parse_args()

    # Listing packs
    if args.list_packs:
        print("Πακέτα:")
        for name in ["core", "extended", "forums", "fediverse", "everything"]:
            sites = build_sites(name)
            print(f"- {name}: {len(sites)} ιστότοποι")
        print("- sherlock: Βάση Sherlock (λήψη κατά απαίτηση / αποθηκευμένη)")
        print("- mega: όλα + βάση Sherlock")
        return

    print(f"\n{Fore.CYAN}Digital Footprint Finder{Style.RESET_ALL}  "
          f"{Fore.WHITE}(συντηρητική ανίχνευση αληθών θετικών){Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}Σημείωση:{Style.RESET_ALL} Χρησιμοποίησέ το μόνο για usernames που σου ανήκουν ή έχεις άδεια να ελέγξεις.\n")

    username = (args.username or input(f"{Fore.GREEN}Δώσε όνομα χρήστη: {Fore.WHITE}")).strip()
    username = username.lstrip("@").strip()
    if not username:
        sys.exit("Απαιτείται όνομα χρήστη.")

    threads = max(1, min(int(args.threads), 64))
    timeout = (float(args.connect_timeout), float(args.timeout))
    jitter = (0.0, max(0.0, float(args.jitter)))
    max_html_bytes = max(50_000, min(int(args.max_html_kb) * 1000, 2_000_000))

    session = build_session()
    limiter = DomainLimiter(per_domain=int(args.domain_limit))

    # Build active site list (pack + optional Sherlock + optional extra-sites)
    pack = (args.pack or "everything").strip().lower()
    save_dir = get_save_dir()
    sherlock_cache = os.path.join(save_dir, "sherlock_data.json")

    sites: Dict[str, SiteSpec] = {}

    if pack == "mega":
        sites.update(build_sites("everything"))
        sites.update(load_sherlock_sites(session, sherlock_cache, bool(args.sherlock_refresh), bool(args.include_nsfw and (not args.safe))))
    elif pack == "sherlock":
        sites.update(load_sherlock_sites(session, sherlock_cache, bool(args.sherlock_refresh), bool(args.include_nsfw and (not args.safe))))
    else:
        sites.update(build_sites(pack))

    if args.extra_sites:
        sites.update(load_extra_sites_json(args.extra_sites))

    # Export current active list
    if args.export_sites:
        export_sites_json(args.export_sites, sites)
        print(f"Εξήχθησαν {len(sites)} ιστότοποι -> {args.export_sites}")
        return

    # Filter for safe mode
    def should_skip(spec: SiteSpec) -> bool:
        if not args.safe:
            return False
        return spec.category in {"Payments", "Dating", "NSFW"}

    items = [(k, v) for k, v in sites.items() if not should_skip(v)]
    random.shuffle(items)
    if args.max_sites and int(args.max_sites) > 0:
        items = items[:max(1, int(args.max_sites))]

    if args.stats:
        cat_counts: Dict[str, int] = {}
        for _, spec in items:
            cat_counts[spec.category] = cat_counts.get(spec.category, 0) + 1
        print(f"{Fore.BLUE}[*] Πλήθος ανά κατηγορία:{Style.RESET_ALL}")
        for cat, n in sorted(cat_counts.items(), key=lambda x: (-x[1], x[0].lower())):
            print(f"  - {cat}: {n}")

    found: List[ScanResult] = []
    possible: List[ScanResult] = []

    # API Checks
    if not args.no_apis:
        print(f"{Fore.BLUE}[*] Έλεγχος APIs...{Style.RESET_ALL}")
        gh_exists, gh_url, _ = check_github_api(session, username, timeout)
        if gh_exists and gh_url:
            r = ScanResult("GitHub (API)", "Tech", f"https://api.github.com/users/{username}", gh_url, 200, "FOUND", "Ταύτιση μέσω GitHub API")
            print_result(r)
            found.append(r)

        gr_exists, gr_url, _ = check_gravatar_api(session, username, timeout)
        if gr_exists and gr_url:
            r = ScanResult("Gravatar (API)", "General", f"https://en.gravatar.com/{username}.json", gr_url, 200, "FOUND", "Ταύτιση μέσω Gravatar JSON")
            print_result(r)
            found.append(r)

    # Site checks
    print(f"\n{Fore.BLUE}[*] Έλεγχος {len(items)} πλατφορμών (με νήματα)...{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Συμβουλή:{Style.RESET_ALL} προεπιλογές είναι --pack mega και --show-possible. Χρησιμοποίησε --pack core/extended/everything για μικρότερο εύρος· χρησιμοποίησε --no-show-possible για να κρύψεις τα POSSIBLE.\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        for site_name, spec in items:
            futures.append(executor.submit(
                analyze_site,
                session,
                limiter,
                site_name,
                spec,
                username,
                timeout,
                jitter,
                max_html_bytes,
                args.verbose,
            ))

        for fut in concurrent.futures.as_completed(futures):
            try:
                res = fut.result()
                if not res:
                    continue
                if res.confidence == "FOUND":
                    print_result(res)
                    found.append(res)
                else:
                    if args.show_possible:
                        print_result(res)
                    possible.append(res)
            except Exception as e:
                if args.verbose:
                    print(f"{Fore.RED}[!] Σφάλμα εργάτη: {e}{Style.RESET_ALL}")

    # Dorking
    dork_results: List[Tuple[str, str]] = []
    if not args.no_dork:
        dork_results = dork_search(session, username, timeout, top_n=int(args.dork_top))

    found = dedup(found)
    possible = dedup(possible)

    # Save
    safe_user = safe_filename(username)
    ts = time.strftime("%Y%m%d_%H%M%S")
    txt_path = os.path.join(save_dir, f"{safe_user}_{ts}.txt")
    json_path = os.path.join(save_dir, f"{safe_user}_{ts}.json")
    csv_path = os.path.join(save_dir, f"{safe_user}_{ts}.csv")
    html_path = os.path.join(save_dir, f"{safe_user}_{ts}.html")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("Αναφορά Digital Footprint Finder\n")
        f.write(f"Όνομα χρήστη: {username}\n")
        f.write(f"Δημιουργήθηκε: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Πακέτο: {pack}\n")
        f.write(f"Ιστότοποι που ελέγχθηκαν: {len(items)}\n")
        f.write(f"Ασφαλής λειτουργία: {bool(args.safe)}\n")
        f.write("=" * 70 + "\n\n")

        f.write("ΒΡΕΘΗΚΕ (υψηλότερη βεβαιότητα)\n")
        f.write("-" * 70 + "\n")
        if found:
            for r in found:
                f.write(f"- [{r.category}] {r.site}: {r.final_url}  (HTTP {r.status}; {r.reason})\n")
        else:
            f.write("Δεν βρέθηκαν αποτελέσματα υψηλής βεβαιότητας.\n")

        f.write("\nΠΙΘΑΝΟ (μπλοκαρισμένο/JS/σύνδεση/ασθενή σήματα)\n")
        f.write("-" * 70 + "\n")
        if possible:
            for r in possible:
                f.write(f"- [{r.category}] {r.site}: {r.final_url}  (HTTP {r.status}; {r.reason})\n")
        else:
            f.write("Δεν βρέθηκαν πιθανά αποτελέσματα.\n")

        f.write("\nΑΠΟΤΕΛΕΣΜΑΤΑ ΜΗΧΑΝΗΣ ΑΝΑΖΗΤΗΣΗΣ (DuckDuckGo HTML)\n")
        f.write("-" * 70 + "\n")
        if dork_results:
            for title, link in dork_results:
                f.write(f"- {title}: {link}\n")
        else:
            f.write("Κανένα αποτέλεσμα αναζήτησης (ή απενεργοποιημένο).\n")

        f.write("\nΣΗΜΕΙΩΣΕΙΣ\n")
        f.write("-" * 70 + "\n")
        f.write("• Το FOUND απαιτεί ισχυρά σήματα (τίτλος/meta/canonical/κείμενο).\n")
        f.write("• Το POSSIBLE σημαίνει μπλοκάρισμα, βαριά JS, απαιτείται σύνδεση ή ασθενή σήματα.\n")
        f.write("• Χρησιμοποίησε --pack mega για μέγιστη κάλυψη (περιλαμβάνει τη βάση Sherlock).\n")

    if args.json:
        payload = {
            "tool": "Digital Footprint Finder",
            "username": username,
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pack": pack,
            "safe": bool(args.safe),
            "scanned": len(items),
            "found": [r.__dict__ for r in found],
            "possible": [r.__dict__ for r in possible],
            "dork_results": [{"title": t, "url": u} for t, u in dork_results],
        }
        try:
            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump(payload, jf, ensure_ascii=False, indent=2)
        except Exception:
            pass

    if args.csv:
        try:
            import csv
            with open(csv_path, "w", newline="", encoding="utf-8") as cf:
                w = csv.writer(cf)
                w.writerow(["βεβαιότητα", "κατηγορία", "ιστότοπος", "τελικό_url", "status", "αιτία"])
                for r in found:
                    w.writerow([r.confidence, r.category, r.site, r.final_url, r.status, r.reason])
                for r in possible:
                    w.writerow([r.confidence, r.category, r.site, r.final_url, r.status, r.reason])
        except Exception:
            pass

    if args.html:
        try:
            meta = {
                "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "pack": pack,
                "scanned": len(items),
                "safe": bool(args.safe),
            }
            save_html_report(html_path, username, found, possible, dork_results, meta)
        except Exception:
            pass

    print("\n" + "=" * 70)
    print(f"{Fore.GREEN}Ο έλεγχος ολοκληρώθηκε.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Αποθηκεύτηκε TXT:{Style.RESET_ALL} {txt_path}")
    if args.json:
        print(f"{Fore.CYAN}Αποθηκεύτηκε JSON:{Style.RESET_ALL} {json_path}")
    if args.csv:
        print(f"{Fore.CYAN}Αποθηκεύτηκε CSV:{Style.RESET_ALL} {csv_path}")
    if args.html:
        print(f"{Fore.CYAN}Αποθηκεύτηκε HTML:{Style.RESET_ALL} {html_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
