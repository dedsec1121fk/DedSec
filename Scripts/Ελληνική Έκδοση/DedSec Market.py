#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import curses
import html as html_lib
import json
import os
import re
import shutil
import subprocess
import tempfile
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

LANG = "gr"

TEXT = {'app_name': 'DedSec Market Ελληνικά', 'invalid_repo_url': 'Μη έγκυρο GitHub repository URL: {url}', 'no_readme_description': 'Δεν υπάρχει διαθέσιμη περιγραφή README.', 'git_missing_and_no_pkg': 'Το git δεν είναι εγκατεστημένο και δεν βρέθηκε το pkg του Termux.', 'git_install_failed': 'Απέτυχε η αυτόματη εγκατάσταση του git.\n{output}', 'no_cache': 'Χωρίς cache', 'unknown': 'Άγνωστο', 'github_request_failed': 'Αποτυχία αιτήματος GitHub: {message}', 'network_error': 'Σφάλμα δικτύου: {reason}', 'readme_fetch_failed': 'Αποτυχία λήψης README: {message}', 'no_release_notes': 'Δεν υπάρχουν σημειώσεις έκδοσης.', 'cache_with_age': 'cache ({age})', 'live_cached_now': 'ζωντανά (μπήκε τώρα σε cache)', 'cache_fallback_with_age': 'fallback από cache ({age})', 'unnamed_release': 'Έκδοση χωρίς όνομα', 'download_repo_failed': 'Απέτυχε η ξανά λήψη του repository πριν την αντικατάσταση των αρχείων.\n{output}', 'already_installed': 'Αυτή η εφαρμογή είναι ήδη εγκατεστημένη.', 'not_installed': 'Αυτή η εφαρμογή δεν είναι εγκατεστημένη.', 'installed_folder_missing': 'Ο εγκατεστημένος φάκελος δεν βρέθηκε στον δίσκο.', 'update_success_replaced': 'Η ενημέρωση ολοκληρώθηκε. Το repository κατέβηκε ξανά και τα παλιά αρχεία αντικαταστάθηκαν στο:\n{path}', 'no_installed_apps': 'Δεν βρέθηκαν εγκατεστημένες εφαρμογές.', 'no_launch_target': 'Δεν βρέθηκε εκκινήσιμο κύριο αρχείο στο εγκατεστημένο repository.', 'unsupported_launch_target': 'Μη υποστηριζόμενο αρχείο εκκίνησης: {name}', 'launching_file': 'Το DedSec Market εκκινεί: {name}', 'path_label': 'Διαδρομή: {path}', 'ctrlc_stop': 'Πάτησε Ctrl+C μέσα στην εφαρμογή που άνοιξε αν θέλεις να τη σταματήσεις.', 'press_enter_return': 'Πάτησε Enter για να επιστρέψεις στο DedSec Market...', 'press_any_key_continue': 'Πάτησε οποιοδήποτε πλήκτρο για συνέχεια', 'confirm_line': 'Πάτησε Y για επιβεβαίωση ή N για ακύρωση', 'find_apps': 'Εύρεση Εφαρμογών', 'installed_apps': 'Εγκατεστημένες Εφαρμογές', 'watchlist': 'Λίστα Παρακολούθησης', 'update_all_installed': 'Ενημέρωση Όλων των Εγκατεστημένων', 'exit': 'Έξοδος', 'main_menu': 'Κύριο Μενού', 'data_folder': 'Φάκελος δεδομένων: {path}', 'main_menu_footer': 'Βελάκια: μετακίνηση | Enter: άνοιγμα | Q: έξοδος', 'total_count': 'Σύνολο: {count}', 'search_status': 'Αναζήτηση: {query}', 'type_to_search': '(γράψε για αναζήτηση)', 'no_apps_found': 'Δεν βρέθηκαν εφαρμογές.', 'installed_flag': 'Εγκατεστημένο', 'watchlist_flag': 'Watchlist', 'list_footer_basic': 'Enter: λεπτομέρειες | B: πίσω', 'list_footer_search': 'Πληκτρολόγηση: αναζήτηση | Backspace: διαγραφή | Esc: καθαρισμός', 'loading_repository_details': 'Φόρτωση λεπτομερειών repository...', 'please_wait': 'Περίμενε', 'source_label': 'Πηγή: {source}', 'none': 'Κανένα', 'tag_label': 'Tag', 'name_label': 'Όνομα', 'published_label': 'Δημοσιεύτηκε', 'notes_label': 'Σημειώσεις', 'no_github_release': 'Δεν βρέθηκε GitHub release.', 'project_name': 'Όνομα Project', 'full_repository': 'Πλήρες Repository', 'creator': 'Δημιουργός', 'repository_label': 'Repository', 'stars': 'Stars', 'forks': 'Forks', 'watchers': 'Watchers', 'open_issues': 'Ανοιχτά Issues', 'installed_status': 'Εγκατεστημένο', 'watchlist_status': 'Watchlist', 'yes': 'Ναι', 'no': 'Όχι', 'install_path': 'Διαδρομή Εγκατάστασης', 'latest_release': 'Τελευταία Έκδοση:', 'contributors': 'Contributors:', 'latest_open_issues': 'Ανοιχτά Issues (τελευταία):', 'no_open_issues_found': 'Δεν βρέθηκαν ανοιχτά issues.', 'readme_english_cleaned': 'README (καθαρισμένο Αγγλικό):', 'back_footer': 'B: πίσω', 'refresh_footer': 'R: ανανέωση', 'update_footer': 'U: ενημέρωση', 'delete_footer': 'D: διαγραφή', 'run_footer': 'X: εκτέλεση', 'install_footer': 'I: εγκατάσταση', 'watchlist_footer': 'W: watchlist', 'scroll_footer': 'Βελάκια: κύλιση', 'added_to_watchlist': 'Προστέθηκε στη watchlist.', 'removed_from_watchlist': 'Αφαιρέθηκε από τη watchlist.', 'installed_successfully_to': 'Η εγκατάσταση ολοκληρώθηκε στο:\n{path}', 'updated_successfully': 'Η ενημέρωση ολοκληρώθηκε.', 'delete_confirm': 'Να διαγραφεί αυτή η εγκατεστημένη εφαρμογή από το home directory σου;', 'deleted_path': 'Διαγράφηκε:\n{path}', 'returned_from': 'Επιστροφή από:\n{name}'}

APP_NAME = TEXT["app_name"]
SCRIPT_NAME = APP_NAME + ".py"
DATA_DIR = Path.home() / APP_NAME
CACHE_DIR = DATA_DIR / "cache"
STATE_FILE = DATA_DIR / "state.json"
USER_AGENT = "DedSec-Market-Termux/1.2"
GITHUB_API = "https://api.github.com"
CACHE_TTL_SECONDS = 1800
PARSER_VERSION = 6

REPOSITORIES = [
    {"url": "https://github.com/dedsec1121fk/Offline-Survival-Project"},
    {"url": "https://github.com/dedsec1121fk/Corrupted-Files-Project"},
]

SESSION_CACHE = {}


class MarketError(Exception):
    pass


def tr(key, **kwargs):
    value = TEXT.get(key, key)
    if kwargs:
        try:
            return value.format(**kwargs)
        except Exception:
            return value
    return value


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def default_state():
    return {"installed": {}, "watchlist": []}


def load_state():
    ensure_data_dir()
    if not STATE_FILE.exists():
        state = default_state()
        save_state(state)
        return state
    try:
        with STATE_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = default_state()
        save_state(data)
        return data
    if not isinstance(data, dict):
        data = default_state()
    data.setdefault("installed", {})
    data.setdefault("watchlist", [])
    return data


def save_state(state):
    ensure_data_dir()
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def parse_repo_url(url):
    parsed = urllib.parse.urlparse(url)
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2:
        raise MarketError(tr("invalid_repo_url", url=url))
    owner, repo = parts[0], parts[1]
    return owner, repo


def repo_slug(owner, repo):
    return f"{owner}/{repo}"


def clean_repo_name(repo_name):
    name = repo_name.replace("_", " ").replace("-", " ").strip()
    name = re.sub(r"\s+", " ", name)
    if not name:
        return repo_name
    words = []
    for word in name.split():
        if word.isupper() and len(word) <= 5:
            words.append(word)
        else:
            words.append(word.capitalize())
    return " ".join(words)


def normalize_repo_entry(entry):
    owner, repo = parse_repo_url(entry["url"])
    slug = repo_slug(owner, repo)
    display_name = entry.get("display_name") or clean_repo_name(repo)
    return {
        "owner": owner,
        "repo": repo,
        "slug": slug,
        "url": entry["url"],
        "display_name": display_name,
    }


APPS = [normalize_repo_entry(entry) for entry in REPOSITORIES]
APP_MAP = {app["slug"]: app for app in APPS}


def contains_greek(text):
    for char in text:
        code = ord(char)
        if 0x0370 <= code <= 0x03FF or 0x1F00 <= code <= 0x1FFF:
            return True
    return False


def english_ratio(text):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    latin = sum(1 for c in letters if "A" <= c <= "Z" or "a" <= c <= "z")
    return latin / max(len(letters), 1)


class ReadmeHTMLTextExtractor(HTMLParser):
    BLOCK_TAGS = {
        "p", "div", "section", "article", "details", "summary", "ul", "ol",
        "li", "br", "hr", "table", "tr", "td", "th", "h1", "h2", "h3",
        "h4", "h5", "h6", "blockquote"
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip_tag = None

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in {"script", "style"}:
            self.skip_tag = tag
            return
        if self.skip_tag:
            return
        if tag == "img":
            return
        if tag == "li":
            self.parts.append("\n• ")
        elif tag in {"br", "hr"}:
            self.parts.append("\n")
        elif tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self.skip_tag == tag:
            self.skip_tag = None
            return
        if self.skip_tag:
            return
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if self.skip_tag:
            return
        if data:
            self.parts.append(data)

    def get_text(self):
        return "".join(self.parts)


def html_to_text(text):
    parser = ReadmeHTMLTextExtractor()
    parser.feed(text)
    parser.close()
    return parser.get_text()


def strip_markdown(text):
    text = re.sub(r"```[^\n]*\n(.*?)```", lambda m: "\n" + m.group(1).strip() + "\n", text, flags=re.DOTALL)
    text = re.sub(r"~~~[^\n]*\n(.*?)~~~", lambda m: "\n" + m.group(1).strip() + "\n", text, flags=re.DOTALL)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"<style.*?>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script.*?>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    if "<" in text and ">" in text:
        text = html_to_text(text)
    text = re.sub(r"`([^`]+)`", r"\1", text)

    cleaned_lines = []
    previous_blank = False
    for raw_line in text.splitlines():
        line = html_lib.unescape(raw_line).replace("\xa0", " ").strip()
        if not line:
            if not previous_blank:
                cleaned_lines.append("")
            previous_blank = True
            continue
        if line in {"---", "***", "___"}:
            continue
        if re.match(r"^\|?\s*[-: ]+\|[-|: ]*$", line):
            continue
        line = re.sub(r"^#{1,6}\s*", "", line)
        line = re.sub(r"^>\s*", "", line)
        bullet_match = re.match(r"^[-*+]\s+(.*)$", line)
        if bullet_match:
            line = "• " + bullet_match.group(1).strip()
        else:
            number_match = re.match(r"^(\d+)\.\s+(.*)$", line)
            if number_match:
                line = f"{number_match.group(1)}. {number_match.group(2).strip()}"
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            cleaned_lines.append(line)
            previous_blank = False
    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_details_english_section(readme_text):
    details_pattern = re.compile(r"<details[^>]*>(.*?)</details>", re.IGNORECASE | re.DOTALL)
    summary_pattern = re.compile(r"<summary[^>]*>(.*?)</summary>", re.IGNORECASE | re.DOTALL)
    sections = []
    for block_match in details_pattern.finditer(readme_text):
        block = block_match.group(1)
        summary_match = summary_pattern.search(block)
        if not summary_match:
            continue
        summary_text = strip_markdown(summary_match.group(1)).lower()
        if "english" in summary_text or "🇬🇧" in summary_text or summary_text.strip() == "en":
            inner = summary_pattern.sub("", block, count=1).strip()
            if inner:
                sections.append(inner)
    if not sections:
        return None
    return "\n\n".join(sections)


def extract_heading_english_section(readme_text):
    lines = readme_text.splitlines()
    sections = []
    capture = []
    in_english = False
    english_level = None

    def flush_capture():
        nonlocal capture
        result = "\n".join(capture).strip()
        if result:
            sections.append(result)
        capture = []

    for line in lines:
        stripped = line.strip()
        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            hashes, heading_text = heading_match.groups()
            heading_lower = strip_markdown(heading_text).lower()
            if "english" in heading_lower or "🇬🇧" in heading_lower:
                if in_english:
                    flush_capture()
                in_english = True
                english_level = len(hashes)
                capture = []
                continue
            if in_english and len(hashes) <= (english_level or 6):
                flush_capture()
                in_english = False
        if in_english:
            capture.append(line)
    if in_english:
        flush_capture()
    if not sections:
        return None
    return "\n\n".join(sections)


def extract_english_summary(readme_text, repo_description=""):
    if not readme_text:
        return repo_description or tr("no_readme_description")
    preferred = extract_details_english_section(readme_text)
    if not preferred:
        preferred = extract_heading_english_section(readme_text)
    if preferred:
        cleaned = strip_markdown(preferred)
        return cleaned or repo_description or tr("no_readme_description")
    cleaned = strip_markdown(readme_text)
    kept_blocks = []
    for block in re.split(r"\n\s*\n", cleaned):
        block = block.strip()
        if not block:
            continue
        if contains_greek(block) and english_ratio(block) < 0.6:
            continue
        kept_blocks.append(block)
    full_text = "\n\n".join(kept_blocks).strip()
    return full_text or repo_description or tr("no_readme_description")


def run_command(command, cwd=None):
    process = subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return process.returncode, process.stdout.strip()


def ensure_git():
    if shutil.which("git"):
        return
    pkg = shutil.which("pkg")
    if not pkg:
        raise MarketError(tr("git_missing_and_no_pkg"))
    code, output = run_command([pkg, "install", "-y", "git"])
    if code != 0 or not shutil.which("git"):
        raise MarketError(tr("git_install_failed", output=output))


def cache_path_for_slug(slug):
    safe = slug.replace("/", "__")
    return CACHE_DIR / f"{safe}.json"


def normalize_cached_info(cached):
    if not isinstance(cached, dict):
        return None
    normalized = dict(cached)
    if "description" in normalized and isinstance(normalized["description"], str):
        normalized["description"] = strip_markdown(normalized["description"])
    release = normalized.get("release")
    if isinstance(release, dict) and isinstance(release.get("notes"), str):
        release["notes"] = strip_markdown(release["notes"])
    return normalized


def load_cached_info(slug):
    path = cache_path_for_slug(slug)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return normalize_cached_info(data)
    except Exception:
        return None


def save_cached_info(slug, info):
    path = cache_path_for_slug(slug)
    data = dict(info)
    data["_cached_at"] = int(time.time())
    data["_parser_version"] = PARSER_VERSION
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def cache_is_fresh(cached):
    if not cached:
        return False
    if int(cached.get("_parser_version", 0)) != PARSER_VERSION:
        return False
    cached_at = int(cached.get("_cached_at", 0))
    return (time.time() - cached_at) <= CACHE_TTL_SECONDS


def human_cache_age(cached):
    if not cached:
        return tr("no_cache")
    cached_at = int(cached.get("_cached_at", 0))
    if cached_at <= 0:
        return tr("unknown")
    seconds = int(time.time() - cached_at)
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    return f"{hours}h ago"


def github_request(url, not_found_ok=False):
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read()
            return json.loads(body.decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        if not_found_ok and e.code == 404:
            return None
        try:
            body = e.read().decode("utf-8", errors="replace")
            payload = json.loads(body)
            message = payload.get("message", str(e))
        except Exception:
            message = str(e)
        raise MarketError(tr("github_request_failed", message=message))
    except urllib.error.URLError as e:
        raise MarketError(tr("network_error", reason=e.reason))


def github_readme(owner, repo):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/readme"
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
            content = payload.get("content", "")
            if payload.get("encoding") == "base64" and content:
                return base64.b64decode(content).decode("utf-8", errors="replace")
            return ""
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return ""
        try:
            body = e.read().decode("utf-8", errors="replace")
            payload = json.loads(body)
            message = payload.get("message", str(e))
        except Exception:
            message = str(e)
        raise MarketError(tr("readme_fetch_failed", message=message))
    except urllib.error.URLError as e:
        raise MarketError(tr("network_error", reason=e.reason))


def summarize_release_body(body):
    if not body:
        return tr("no_release_notes")
    body = strip_markdown(body)
    parts = []
    for block in re.split(r"\n\s*\n", body):
        block = block.strip()
        if not block:
            continue
        parts.append(block)
        if len(parts) >= 3:
            break
    summary = "\n\n".join(parts).strip()
    return summary or tr("no_release_notes")


def get_repo_info(app, refresh=False):
    slug = app["slug"]
    if slug in SESSION_CACHE and not refresh:
        return SESSION_CACHE[slug]
    cached = load_cached_info(slug)
    if cached and cache_is_fresh(cached) and not refresh:
        cached["_source"] = tr("cache_with_age", age=human_cache_age(cached))
        SESSION_CACHE[slug] = cached
        return cached
    owner, repo = app["owner"], app["repo"]
    try:
        repo_data = github_request(f"{GITHUB_API}/repos/{owner}/{repo}")
        contributors = github_request(f"{GITHUB_API}/repos/{owner}/{repo}/contributors?per_page=100")
        issues_data = github_request(f"{GITHUB_API}/repos/{owner}/{repo}/issues?state=open&per_page=20")
        release_data = github_request(f"{GITHUB_API}/repos/{owner}/{repo}/releases/latest", not_found_ok=True)
        readme_text = github_readme(owner, repo)
        creator = repo_data.get("owner", {}).get("login") or owner
        contributor_names = []
        if isinstance(contributors, list):
            for person in contributors:
                login = person.get("login")
                if login:
                    contributor_names.append(login)
        issue_titles = []
        if isinstance(issues_data, list):
            for item in issues_data:
                if "pull_request" in item:
                    continue
                title = item.get("title")
                if title:
                    issue_titles.append(title)
        release_info = None
        if isinstance(release_data, dict):
            release_info = {
                "tag": release_data.get("tag_name") or tr("unknown"),
                "name": release_data.get("name") or tr("unnamed_release"),
                "published_at": release_data.get("published_at") or tr("unknown"),
                "notes": summarize_release_body(release_data.get("body", "")),
                "url": release_data.get("html_url") or "",
            }
        info = {
            "slug": slug,
            "display_name": app["display_name"],
            "url": app["url"],
            "full_name": repo_data.get("full_name", slug),
            "creator": creator,
            "description": extract_english_summary(readme_text, repo_data.get("description", "")),
            "stars": int(repo_data.get("stargazers_count", 0)),
            "forks": int(repo_data.get("forks_count", 0)),
            "watchers": int(repo_data.get("subscribers_count", repo_data.get("watchers_count", 0))),
            "issues_count": int(repo_data.get("open_issues_count", 0)),
            "issues": issue_titles,
            "contributors": contributor_names,
            "default_branch": repo_data.get("default_branch", "main"),
            "release": release_info,
            "_source": tr("live_cached_now"),
        }
        save_cached_info(slug, info)
        SESSION_CACHE[slug] = info
        return info
    except Exception:
        if cached:
            cached["_source"] = tr("cache_fallback_with_age", age=human_cache_age(cached))
            SESSION_CACHE[slug] = cached
            return cached
        raise


def suggested_install_path(app):
    return Path.home() / app["repo"]


def unique_install_path(base_path):
    if not base_path.exists():
        return base_path
    counter = 1
    while True:
        candidate = Path(str(base_path) + f"-{counter}")
        if not candidate.exists():
            return candidate
        counter += 1


def clone_repo_to_temp(app):
    ensure_git()
    temp_dir = Path(tempfile.mkdtemp(prefix="dedsec_market_update_"))
    clone_path = temp_dir / app["repo"]
    code, output = run_command(["git", "clone", "--depth", "1", app["url"], str(clone_path)])
    if code != 0:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise MarketError(tr("download_repo_failed", output=output))
    git_dir = clone_path / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir, ignore_errors=True)
    return temp_dir, clone_path


def clear_directory_contents(path, keep_names=None):
    keep_names = set(keep_names or [])
    for entry in path.iterdir():
        if entry.name in keep_names:
            continue
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink(missing_ok=True)


def copy_directory_contents(src, dst):
    for entry in src.iterdir():
        target = dst / entry.name
        if entry.is_dir() and not entry.is_symlink():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(entry, target)
        else:
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            shutil.copy2(entry, target)


def install_app(app, state):
    slug = app["slug"]
    if slug in state["installed"]:
        raise MarketError(tr("already_installed"))
    base_path = suggested_install_path(app)
    install_path = unique_install_path(base_path)
    temp_dir, clone_path = clone_repo_to_temp(app)
    try:
        shutil.move(str(clone_path), str(install_path))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    state["installed"][slug] = {
        "display_name": app["display_name"],
        "path": str(install_path),
        "repo_url": app["url"],
        "installed_at": int(time.time()),
    }
    save_state(state)
    return install_path


def update_app(app, state):
    slug = app["slug"]
    item = state["installed"].get(slug)
    if not item:
        raise MarketError(tr("not_installed"))
    path = Path(item["path"])
    if not path.exists():
        raise MarketError(tr("installed_folder_missing"))
    temp_dir, clone_path = clone_repo_to_temp(app)
    try:
        clear_directory_contents(path, keep_names={".git"})
        copy_directory_contents(clone_path, path)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    item["updated_at"] = int(time.time())
    item["last_update_mode"] = "full_redownload_replace"
    save_state(state)
    return tr("update_success_replaced", path=path)


def update_all_installed(state):
    installed_slugs = [slug for slug in state["installed"] if slug in APP_MAP]
    if not installed_slugs:
        return [tr("no_installed_apps")]
    results = []
    for slug in installed_slugs:
        app = APP_MAP[slug]
        try:
            message = update_app(app, state)
            results.append(f"• {app['display_name']}: {message}")
        except Exception as e:
            results.append(f"• {app['display_name']}: {e}")
    return results


def delete_app(app, state):
    slug = app["slug"]
    item = state["installed"].get(slug)
    if not item:
        raise MarketError(tr("not_installed"))
    path = Path(item["path"])
    if path.exists():
        shutil.rmtree(path)
    state["installed"].pop(slug, None)
    save_state(state)
    return path


def toggle_watchlist(app, state):
    slug = app["slug"]
    watchlist = state["watchlist"]
    if slug in watchlist:
        watchlist.remove(slug)
        save_state(state)
        return False
    watchlist.append(slug)
    watchlist.sort()
    save_state(state)
    return True


def walk_limited(base_path, max_depth=2):
    base_depth = len(base_path.parts)
    for root, dirs, files in os.walk(base_path):
        root_path = Path(root)
        current_depth = len(root_path.parts) - base_depth
        if current_depth >= max_depth:
            dirs[:] = []
        yield root_path, files


def detect_launch_target(app, install_path):
    install_path = Path(install_path)
    if not install_path.exists():
        return None
    repo_name = app["repo"]
    cleaned_name = clean_repo_name(repo_name)
    candidate_names = [
        f"{cleaned_name}.py",
        f"{repo_name}.py",
        "main.py", "app.py", "run.py", "start.py", "launch.py", "index.py",
        "install.sh", "setup.sh", "start.sh", "run.sh",
    ]
    candidate_names_lower = [name.lower() for name in candidate_names]
    scored = []
    for root_path, files in walk_limited(install_path, max_depth=3):
        for file_name in files:
            lower = file_name.lower()
            file_path = root_path / file_name
            score = 0
            if lower in candidate_names_lower:
                score += 100 - candidate_names_lower.index(lower)
            if lower.endswith(".py"):
                score += 10
            if lower.endswith(".sh"):
                score += 5
            if "main" in lower or "start" in lower or "run" in lower:
                score += 4
            if score > 0:
                scored.append((score, file_path))
    if not scored:
        return None
    scored.sort(key=lambda item: (-item[0], len(str(item[1]))))
    return scored[0][1]


def run_installed_app(stdscr, app, state):
    slug = app["slug"]
    item = state["installed"].get(slug)
    if not item:
        raise MarketError(tr("not_installed"))
    install_path = Path(item["path"])
    if not install_path.exists():
        raise MarketError(tr("installed_folder_missing"))
    target = detect_launch_target(app, install_path)
    if not target:
        raise MarketError(tr("no_launch_target"))
    if target.suffix.lower() == ".py":
        command = ["python", str(target)]
    elif target.suffix.lower() == ".sh":
        command = ["bash", str(target)]
    else:
        raise MarketError(tr("unsupported_launch_target", name=target.name))

    curses.def_prog_mode()
    curses.endwin()
    try:
        print("\n" + tr("launching_file", name=target.name))
        print(tr("path_label", path=target))
        print("\n" + tr("ctrlc_stop") + "\n")
        subprocess.run(command, cwd=str(target.parent))
        input("\n" + tr("press_enter_return"))
    finally:
        curses.reset_prog_mode()
        stdscr.refresh()
    return target


def init_colors():
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)


def add_line(stdscr, y, x, text, attr=0):
    height, width = stdscr.getmaxyx()
    if y < 0 or y >= height or x >= width:
        return
    try:
        stdscr.addnstr(y, x, text, max(0, width - x - 1), attr)
    except curses.error:
        pass


def draw_header(stdscr, title, subtitle=""):
    height, width = stdscr.getmaxyx()
    stdscr.erase()
    title_text = f" {APP_NAME} - {title} "
    add_line(stdscr, 0, 0, title_text[:width - 1], curses.A_BOLD | curses.color_pair(1))
    if subtitle:
        add_line(stdscr, 1, 0, subtitle[:width - 1], curses.color_pair(3))
    if height > 2:
        add_line(stdscr, 2, 0, "-" * (width - 1), curses.A_DIM)


def draw_footer(stdscr, text):
    height, width = stdscr.getmaxyx()
    add_line(stdscr, height - 1, 0, " " * (width - 1))
    add_line(stdscr, height - 1, 0, text[:width - 1], curses.A_DIM)


def center_message(stdscr, lines, attr=0):
    height, width = stdscr.getmaxyx()
    start_y = max(0, height // 2 - len(lines) // 2)
    for index, line in enumerate(lines):
        x = max(0, (width - len(line)) // 2)
        add_line(stdscr, start_y + index, x, line, attr)


def prompt_message(stdscr, title, message, wait_for_key=True):
    draw_header(stdscr, title)
    lines = []
    width = max(20, stdscr.getmaxyx()[1] - 6)
    for block in str(message).split("\n"):
        wrapped = textwrap.wrap(block, width=width) or [""]
        lines.extend(wrapped)
    center_message(stdscr, lines, curses.color_pair(2))
    if wait_for_key:
        draw_footer(stdscr, tr("press_any_key_continue"))
    stdscr.refresh()
    if wait_for_key:
        stdscr.getch()


def prompt_confirm(stdscr, title, message):
    while True:
        draw_header(stdscr, title)
        lines = []
        width = max(20, stdscr.getmaxyx()[1] - 6)
        for block in str(message).split("\n"):
            wrapped = textwrap.wrap(block, width=width) or [""]
            lines.extend(wrapped)
        lines.append("")
        lines.append(tr("confirm_line"))
        center_message(stdscr, lines, curses.color_pair(4))
        stdscr.refresh()
        key = stdscr.getch()
        if key in (ord("y"), ord("Y")):
            return True
        if key in (ord("n"), ord("N"), 27):
            return False


def wrap_text_preserving_lines(text, width):
    wrapped = []
    for raw_line in str(text).splitlines():
        if not raw_line.strip():
            wrapped.append("")
            continue
        bullet_prefix = ""
        content = raw_line.rstrip()
        if content.startswith("• "):
            bullet_prefix = "• "
            content = content[2:].strip()
        line_width = max(10, width - len(bullet_prefix))
        pieces = textwrap.wrap(content, width=line_width, break_long_words=False, break_on_hyphens=False) or [""]
        for i, piece in enumerate(pieces):
            if bullet_prefix and i == 0:
                wrapped.append(bullet_prefix + piece)
            elif bullet_prefix:
                wrapped.append("  " + piece)
            else:
                wrapped.append(piece)
    return wrapped


def main_menu(stdscr, state):
    items = [
        tr("find_apps"),
        tr("installed_apps"),
        tr("watchlist"),
        tr("update_all_installed"),
        tr("exit"),
    ]
    selected = 0
    while True:
        draw_header(stdscr, tr("main_menu"), tr("data_folder", path=DATA_DIR))
        for idx, item in enumerate(items):
            y = 4 + idx
            attr = curses.A_REVERSE if idx == selected else 0
            if item == tr("exit"):
                attr |= curses.color_pair(4)
            add_line(stdscr, y, 2, item, attr)
        draw_footer(stdscr, tr("main_menu_footer"))
        stdscr.refresh()
        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            return
        elif key in (curses.KEY_UP, ord("k")):
            selected = (selected - 1) % len(items)
        elif key in (curses.KEY_DOWN, ord("j")):
            selected = (selected + 1) % len(items)
        elif key in (10, 13, curses.KEY_ENTER):
            choice = items[selected]
            if choice == tr("find_apps"):
                app_list_screen(stdscr, state, tr("find_apps"), APPS)
            elif choice == tr("installed_apps"):
                installed = [APP_MAP[slug] for slug in state["installed"] if slug in APP_MAP]
                app_list_screen(stdscr, state, tr("installed_apps"), installed, allow_search=False)
            elif choice == tr("watchlist"):
                watched = [APP_MAP[slug] for slug in state["watchlist"] if slug in APP_MAP]
                app_list_screen(stdscr, state, tr("watchlist"), watched, allow_search=False)
            elif choice == tr("update_all_installed"):
                prompt_message(stdscr, tr("update_all_installed"), "\n".join(update_all_installed(state)))
            elif choice == tr("exit"):
                return


def app_list_screen(stdscr, state, title, apps, allow_search=True):
    selected = 0
    query = ""
    while True:
        if allow_search and query:
            filtered = [app for app in apps if query.lower() in app["display_name"].lower() or query.lower() in app["slug"].lower()]
        else:
            filtered = list(apps)
        if selected >= len(filtered) and filtered:
            selected = len(filtered) - 1
        if selected < 0:
            selected = 0
        subtitle = tr("total_count", count=len(filtered))
        if allow_search:
            subtitle += " | " + tr("search_status", query=(query or tr("type_to_search")))
        draw_header(stdscr, title, subtitle)
        if not filtered:
            add_line(stdscr, 4, 2, tr("no_apps_found"), curses.color_pair(4))
        else:
            max_rows = max(1, stdscr.getmaxyx()[0] - 7)
            start = 0
            if selected >= max_rows:
                start = selected - max_rows + 1
            visible = filtered[start:start + max_rows]
            for idx, app in enumerate(visible):
                actual = start + idx
                installed = app["slug"] in state["installed"]
                watched = app["slug"] in state["watchlist"]
                flags = []
                if installed:
                    flags.append(tr("installed_flag"))
                if watched:
                    flags.append(tr("watchlist_flag"))
                line = app["display_name"]
                if flags:
                    line += "  [" + ", ".join(flags) + "]"
                attr = curses.A_REVERSE if actual == selected else 0
                add_line(stdscr, 4 + idx, 2, line, attr)
        footer = tr("list_footer_basic")
        if allow_search:
            footer += " | " + tr("list_footer_search")
        draw_footer(stdscr, footer)
        stdscr.refresh()
        key = stdscr.getch()
        if key in (ord("b"), ord("B"), 27):
            return
        elif key in (curses.KEY_UP, ord("k")):
            if filtered:
                selected = (selected - 1) % len(filtered)
        elif key in (curses.KEY_DOWN, ord("j")):
            if filtered:
                selected = (selected + 1) % len(filtered)
        elif key in (10, 13, curses.KEY_ENTER):
            if filtered:
                app_detail_screen(stdscr, state, filtered[selected])
        elif allow_search:
            if key in (curses.KEY_BACKSPACE, 127, 8):
                query = query[:-1]
                selected = 0
            elif key == 27:
                query = ""
                selected = 0
            elif 32 <= key <= 126:
                query += chr(key)
                selected = 0


def app_detail_screen(stdscr, state, app):
    scroll = 0
    info = None
    error_message = None
    while True:
        if info is None and error_message is None:
            draw_header(stdscr, app["display_name"], tr("loading_repository_details"))
            draw_footer(stdscr, tr("please_wait"))
            stdscr.refresh()
            try:
                info = get_repo_info(app)
            except Exception as e:
                error_message = str(e)
        subtitle = app["slug"]
        if info and info.get("_source"):
            subtitle = f"{app['slug']} | {tr('source_label', source=info['_source'])}"
        draw_header(stdscr, app["display_name"], subtitle)
        height, width = stdscr.getmaxyx()
        if error_message:
            wrapped = []
            for block in error_message.split("\n"):
                wrapped.extend(textwrap.wrap(block, width=max(20, width - 4)) or [""])
            for idx, line in enumerate(wrapped[:max(1, height - 6)]):
                add_line(stdscr, 4 + idx, 2, line, curses.color_pair(4))
        else:
            installed = app["slug"] in state["installed"]
            watched = app["slug"] in state["watchlist"]
            contributors_text = ", ".join(info["contributors"]) if info["contributors"] else tr("none")
            release = info.get("release")
            if release:
                release_text = (
                    f"{tr('tag_label')}: {release['tag']}\n"
                    f"{tr('name_label')}: {release['name']}\n"
                    f"{tr('published_label')}: {release['published_at']}\n"
                    f"{tr('notes_label')}:\n{release['notes']}"
                )
            else:
                release_text = tr("no_github_release")
            install_path = state["installed"].get(app["slug"], {}).get("path", tr("not_installed"))
            body_blocks = [
                f"{tr('project_name')}: {info['display_name']}",
                f"{tr('full_repository')}: {info['full_name']}",
                f"{tr('creator')}: {info['creator']}",
                f"{tr('repository_label')}: {info['url']}",
                f"{tr('stars')}: {info['stars']}  |  {tr('forks')}: {info['forks']}  |  {tr('watchers')}: {info['watchers']}",
                f"{tr('open_issues')}: {info['issues_count']}",
                f"{tr('installed_status')}: {tr('yes') if installed else tr('no')}  |  {tr('watchlist_status')}: {tr('yes') if watched else tr('no')}",
                f"{tr('install_path')}: {install_path}",
                "",
                tr("latest_release"),
                release_text,
                "",
                tr("contributors"),
                contributors_text,
                "",
                tr("latest_open_issues"),
                ("\n".join(f"• {title}" for title in info['issues']) if info['issues'] else tr("no_open_issues_found")),
                "",
                tr("readme_english_cleaned"),
                info["description"],
            ]
            wrapped_lines = []
            for block in body_blocks:
                if block == "":
                    wrapped_lines.append("")
                else:
                    wrapped_lines.extend(wrap_text_preserving_lines(block, max(20, width - 4)))
            view_height = max(1, height - 6)
            max_scroll = max(0, len(wrapped_lines) - view_height)
            scroll = min(scroll, max_scroll)
            visible = wrapped_lines[scroll:scroll + view_height]
            for idx, line in enumerate(visible):
                add_line(stdscr, 4 + idx, 2, line)
        footer_parts = [tr("back_footer"), tr("refresh_footer")]
        if not error_message:
            if app["slug"] in state["installed"]:
                footer_parts.extend([tr("update_footer"), tr("delete_footer"), tr("run_footer")])
            else:
                footer_parts.append(tr("install_footer"))
            footer_parts.append(tr("watchlist_footer"))
            footer_parts.append(tr("scroll_footer"))
        draw_footer(stdscr, " | ".join(footer_parts))
        stdscr.refresh()
        key = stdscr.getch()
        if key in (ord("b"), ord("B")):
            return
        elif key in (ord("r"), ord("R")):
            SESSION_CACHE.pop(app["slug"], None)
            info = None
            error_message = None
            scroll = 0
        elif key in (curses.KEY_UP, ord("k")):
            scroll = max(0, scroll - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            scroll += 1
        elif key in (curses.KEY_PPAGE,):
            scroll = max(0, scroll - 10)
        elif key in (curses.KEY_NPAGE,):
            scroll += 10
        elif key in (ord("w"), ord("W")):
            added = toggle_watchlist(app, state)
            prompt_message(stdscr, app["display_name"], tr("added_to_watchlist") if added else tr("removed_from_watchlist"))
        elif key in (ord("i"), ord("I")) and app["slug"] not in state["installed"]:
            try:
                path = install_app(app, state)
                prompt_message(stdscr, app["display_name"], tr("installed_successfully_to", path=path))
            except Exception as e:
                prompt_message(stdscr, app["display_name"], str(e))
        elif key in (ord("u"), ord("U")) and app["slug"] in state["installed"]:
            try:
                output = update_app(app, state)
                prompt_message(stdscr, app["display_name"], output or tr("updated_successfully"))
            except Exception as e:
                prompt_message(stdscr, app["display_name"], str(e))
        elif key in (ord("d"), ord("D")) and app["slug"] in state["installed"]:
            confirm = prompt_confirm(stdscr, app["display_name"], tr("delete_confirm"))
            if confirm:
                try:
                    path = delete_app(app, state)
                    prompt_message(stdscr, app["display_name"], tr("deleted_path", path=path))
                except Exception as e:
                    prompt_message(stdscr, app["display_name"], str(e))
        elif key in (ord("x"), ord("X")) and app["slug"] in state["installed"]:
            try:
                target = run_installed_app(stdscr, app, state)
                prompt_message(stdscr, app["display_name"], tr("returned_from", name=target.name))
            except Exception as e:
                prompt_message(stdscr, app["display_name"], str(e))


def verify_terminal():
    if not os.environ.get("TERM"):
        os.environ["TERM"] = "xterm-256color"


def run_market(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    curses.noecho()
    curses.cbreak()
    init_colors()
    state = load_state()
    main_menu(stdscr, state)


def main():
    verify_terminal()
    ensure_data_dir()
    try:
        curses.wrapper(run_market)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"{APP_NAME} crashed: {e}")


if __name__ == "__main__":
    main()
