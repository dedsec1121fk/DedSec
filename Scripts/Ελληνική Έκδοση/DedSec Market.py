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
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

APP_NAME = "DedSec Market GR"
SCRIPT_NAME = "DedSec Market GR.py"
DATA_DIR = Path.home() / "DedSec Market GR"
CACHE_DIR = DATA_DIR / "cache"
STATE_FILE = DATA_DIR / "state.json"
USER_AGENT = "DedSec-Market-Termux-GR/1.1"
GITHUB_API = "https://api.github.com"
CACHE_TTL_SECONDS = 1800
PARSER_VERSION = 5

REPOSITORIES = [
    {
        "url": "https://github.com/dedsec1121fk/Offline-Survival-Project",
    },
    {
        "url": "https://github.com/dedsec1121fk/Corrupted-Files-Project",
    },
]

SESSION_CACHE = {}


class MarketError(Exception):
    pass


# -----------------------------
# General helpers
# -----------------------------

def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def default_state():
    return {
        "installed": {},
        "watchlist": []
    }


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
        raise MarketError(f"Μη έγκυρο URL αποθετηρίου GitHub: {url}")
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
    # Convert fenced code blocks to plain text content without markdown fences.
    text = re.sub(r"```[^\n]*\n(.*?)```", lambda m: "\n" + m.group(1).strip() + "\n", text, flags=re.DOTALL)
    text = re.sub(r"~~~[^\n]*\n(.*?)~~~", lambda m: "\n" + m.group(1).strip() + "\n", text, flags=re.DOTALL)

    # Remove HTML comments and noisy blocks.
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"<style.*?>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script.*?>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove markdown images and convert links to plain text labels.
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)

    # Convert HTML to plain text for mixed HTML/Markdown READMEs.
    if "<" in text and ">" in text:
        text = html_to_text(text)

    # Remove inline code markers while keeping the text inside them.
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


def is_noise_block(block):
    low = block.lower().strip()
    stop_headings = [
        "repository structure", "what each part does", "termux download",
        "install", "run and update", "main script features", "final note",
        "license", "contributing", "usage", "requirements"
    ]
    return any(low == item or low.startswith(item + ":") for item in stop_headings)


def extract_english_summary(readme_text, repo_description=""):
    if not readme_text:
        return repo_description or "Δεν υπάρχει διαθέσιμη περιγραφή README."

    preferred = extract_details_english_section(readme_text)
    if not preferred:
        preferred = extract_heading_english_section(readme_text)

    # If there is an explicit English section, return all of it after cleaning.
    if preferred:
        cleaned = strip_markdown(preferred)
        return cleaned or repo_description or "Δεν υπάρχει διαθέσιμη περιγραφή README."

    # Otherwise keep the whole cleaned README, but drop obviously non-English blocks.
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
    return full_text or repo_description or "Δεν υπάρχει διαθέσιμη περιγραφή README."


def extract_details_greek_section(readme_text):
    details_pattern = re.compile(r"<details[^>]*>(.*?)</details>", re.IGNORECASE | re.DOTALL)
    summary_pattern = re.compile(r"<summary[^>]*>(.*?)</summary>", re.IGNORECASE | re.DOTALL)

    sections = []
    for block_match in details_pattern.finditer(readme_text):
        block = block_match.group(1)
        summary_match = summary_pattern.search(block)
        if not summary_match:
            continue
        summary_text = strip_markdown(summary_match.group(1)).lower()
        if (
            "greek" in summary_text
            or "ελλην" in summary_text
            or "🇬🇷" in summary_text
            or summary_text.strip() in {"gr", "el", "ελ"}
        ):
            inner = summary_pattern.sub("", block, count=1).strip()
            if inner:
                sections.append(inner)

    if not sections:
        return None
    return "\n\n".join(sections)


def extract_heading_greek_section(readme_text):
    lines = readme_text.splitlines()
    sections = []
    capture = []
    in_greek = False
    greek_level = None

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
            if "greek" in heading_lower or "ελλην" in heading_lower or "🇬🇷" in heading_lower:
                if in_greek:
                    flush_capture()
                in_greek = True
                greek_level = len(hashes)
                capture = []
                continue
            if in_greek and len(hashes) <= (greek_level or 6):
                flush_capture()
                in_greek = False
        if in_greek:
            capture.append(line)

    if in_greek:
        flush_capture()

    if not sections:
        return None
    return "\n\n".join(sections)


def extract_greek_summary(readme_text, repo_description=""):
    if not readme_text:
        return repo_description or "Δεν υπάρχει διαθέσιμη περιγραφή README."

    preferred = extract_details_greek_section(readme_text)
    if not preferred:
        preferred = extract_heading_greek_section(readme_text)

    if preferred:
        cleaned = strip_markdown(preferred)
        return cleaned or repo_description or "Δεν υπάρχει διαθέσιμη περιγραφή README."

    cleaned = strip_markdown(readme_text)
    greek_blocks = []
    for block in re.split(r"\n\s*\n", cleaned):
        block = block.strip()
        if not block:
            continue
        if contains_greek(block):
            greek_blocks.append(block)

    greek_text = "\n\n".join(greek_blocks).strip()
    if greek_text:
        return greek_text

    return extract_english_summary(readme_text, repo_description)


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
        raise MarketError("Το git δεν είναι εγκατεστημένο και δεν βρέθηκε το pkg του Termux.")

    code, output = run_command([pkg, "install", "-y", "git"])
    if code != 0 or not shutil.which("git"):
        raise MarketError(f"Απέτυχε η αυτόματη εγκατάσταση του git.\n{output}")


# -----------------------------
# Cache helpers
# -----------------------------

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
        return "Δεν υπάρχει cache"
    cached_at = int(cached.get("_cached_at", 0))
    if cached_at <= 0:
        return "Άγνωστο"
    seconds = int(time.time() - cached_at)
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    return f"{hours}h ago"


# -----------------------------
# GitHub fetchers
# -----------------------------

def github_request(url, not_found_ok=False):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
        },
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
        raise MarketError(f"Το αίτημα προς GitHub απέτυχε: {message}")
    except urllib.error.URLError as e:
        raise MarketError(f"Σφάλμα δικτύου: {e.reason}")


def github_readme(owner, repo):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/readme"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
        },
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
        raise MarketError(f"Απέτυχε η λήψη του README: {message}")
    except urllib.error.URLError as e:
        raise MarketError(f"Σφάλμα δικτύου: {e.reason}")


def summarize_release_body(body):
    if not body:
        return "Δεν υπάρχουν διαθέσιμες σημειώσεις έκδοσης."
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
    return summary or "Δεν υπάρχουν διαθέσιμες σημειώσεις έκδοσης."


def get_repo_info(app, refresh=False):
    slug = app["slug"]
    if slug in SESSION_CACHE and not refresh:
        return SESSION_CACHE[slug]

    cached = load_cached_info(slug)
    if cached and cache_is_fresh(cached) and not refresh:
        cached["_source"] = f"cache ({human_cache_age(cached)})"
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
                "tag": release_data.get("tag_name") or "Άγνωστο",
                "name": release_data.get("name") or "Ανώνυμη έκδοση",
                "published_at": release_data.get("published_at") or "Άγνωστο",
                "notes": summarize_release_body(release_data.get("body", "")),
                "url": release_data.get("html_url") or "",
            }

        info = {
            "slug": slug,
            "display_name": app["display_name"],
            "url": app["url"],
            "full_name": repo_data.get("full_name", slug),
            "creator": creator,
            "description": extract_greek_summary(readme_text, repo_data.get("description", "")),
            "stars": int(repo_data.get("stargazers_count", 0)),
            "forks": int(repo_data.get("forks_count", 0)),
            "watchers": int(repo_data.get("subscribers_count", repo_data.get("watchers_count", 0))),
            "issues_count": int(repo_data.get("open_issues_count", 0)),
            "issues": issue_titles,
            "contributors": contributor_names,
            "default_branch": repo_data.get("default_branch", "main"),
            "release": release_info,
            "_source": "ζωντανά",
        }

        save_cached_info(slug, info)
        info["_source"] = f"ζωντανά (αποθηκεύτηκε τώρα)"
        SESSION_CACHE[slug] = info
        return info
    except Exception:
        if cached:
            cached["_source"] = f"cache fallback ({human_cache_age(cached)})"
            SESSION_CACHE[slug] = cached
            return cached
        raise


# -----------------------------
# Install / update / delete / run
# -----------------------------

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


def install_app(app, state):
    ensure_git()
    slug = app["slug"]
    if slug in state["installed"]:
        raise MarketError("Αυτή η εφαρμογή είναι ήδη εγκατεστημένη.")

    base_path = suggested_install_path(app)
    install_path = unique_install_path(base_path)

    code, output = run_command(["git", "clone", app["url"], str(install_path)])
    if code != 0:
        raise MarketError(f"Η εγκατάσταση απέτυχε.\n{output}")

    state["installed"][slug] = {
        "display_name": app["display_name"],
        "path": str(install_path),
        "repo_url": app["url"],
        "installed_at": int(time.time()),
    }
    save_state(state)
    return install_path


def update_app(app, state):
    ensure_git()
    slug = app["slug"]
    item = state["installed"].get(slug)
    if not item:
        raise MarketError("Αυτή η εφαρμογή δεν είναι εγκατεστημένη.")

    path = Path(item["path"])
    if not path.exists():
        raise MarketError("Ο εγκατεστημένος φάκελος δεν βρέθηκε στη συσκευή.")

    code, output = run_command(["git", "-C", str(path), "pull", "--ff-only"])
    if code != 0:
        raise MarketError(f"Η ενημέρωση απέτυχε.\n{output}")

    item["updated_at"] = int(time.time())
    save_state(state)
    return output or "Είναι ήδη ενημερωμένο."


def delete_app(app, state):
    slug = app["slug"]
    item = state["installed"].get(slug)
    if not item:
        raise MarketError("Αυτή η εφαρμογή δεν είναι εγκατεστημένη.")

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
        "main.py",
        "app.py",
        "run.py",
        "start.py",
        "launch.py",
        "index.py",
        "install.sh",
        "setup.sh",
        "start.sh",
        "run.sh",
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
        raise MarketError("Αυτή η εφαρμογή δεν είναι εγκατεστημένη.")

    install_path = Path(item["path"])
    if not install_path.exists():
        raise MarketError("Ο εγκατεστημένος φάκελος δεν βρέθηκε στη συσκευή.")

    target = detect_launch_target(app, install_path)
    if not target:
        raise MarketError("Δεν εντοπίστηκε αρχείο εκκίνησης στο εγκατεστημένο αποθετήριο.")

    if target.suffix.lower() == ".py":
        command = ["python", str(target)]
    elif target.suffix.lower() == ".sh":
        command = ["bash", str(target)]
    else:
        raise MarketError(f"Unsupported launch target: {target.name}")

    curses.def_prog_mode()
    curses.endwin()
    try:
        print(f"\n{APP_NAME} ανοίγει: {target.name}")
        print(f"Διαδρομή: {target}")
        print("\nΠάτα Ctrl+C μέσα στην εφαρμογή αν θέλεις να τη σταματήσεις.\n")
        subprocess.run(command, cwd=str(target.parent))
        input("\nΠάτα Enter για επιστροφή στο DedSec Market GR...")
    finally:
        curses.reset_prog_mode()
        stdscr.refresh()

    return target


# -----------------------------
# Curses UI helpers
# -----------------------------

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
    if y < 0 or y >= height:
        return
    if x >= width:
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
    for block in message.split("\n"):
        wrapped = textwrap.wrap(block, width=width) or [""]
        lines.extend(wrapped)
    center_message(stdscr, lines, curses.color_pair(2))
    if wait_for_key:
        draw_footer(stdscr, "Πάτα οποιοδήποτε πλήκτρο για συνέχεια")
    stdscr.refresh()
    if wait_for_key:
        stdscr.getch()


def prompt_confirm(stdscr, title, message):
    while True:
        draw_header(stdscr, title)
        lines = []
        width = max(20, stdscr.getmaxyx()[1] - 6)
        for block in message.split("\n"):
            wrapped = textwrap.wrap(block, width=width) or [""]
            lines.extend(wrapped)
        lines.append("")
        lines.append("Πάτα Y για επιβεβαίωση ή N για ακύρωση")
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
        pieces = textwrap.wrap(
            content,
            width=line_width,
            break_long_words=False,
            break_on_hyphens=False,
        ) or [""]
        for i, piece in enumerate(pieces):
            if bullet_prefix and i == 0:
                wrapped.append(bullet_prefix + piece)
            elif bullet_prefix:
                wrapped.append("  " + piece)
            else:
                wrapped.append(piece)
    return wrapped


# -----------------------------
# Screens
# -----------------------------

def main_menu(stdscr, state):
    items = [
        "Εύρεση Εφαρμογών",
        "Εγκατεστημένες Εφαρμογές",
        "Λίστα Παρακολούθησης",
        "Έξοδος",
    ]
    selected = 0

    while True:
        draw_header(stdscr, "Κύριο Μενού", f"Φάκελος δεδομένων: {DATA_DIR}")
        for idx, item in enumerate(items):
            y = 4 + idx
            attr = curses.A_REVERSE if idx == selected else 0
            if item == "Έξοδος":
                attr |= curses.color_pair(4)
            add_line(stdscr, y, 2, item, attr)
        draw_footer(stdscr, "Βελάκια: κίνηση | Enter: άνοιγμα | Q: έξοδος")
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
            if choice == "Εύρεση Εφαρμογών":
                app_list_screen(stdscr, state, "Εύρεση Εφαρμογών", APPS)
            elif choice == "Εγκατεστημένες Εφαρμογές":
                installed = [APP_MAP[slug] for slug in state["installed"] if slug in APP_MAP]
                app_list_screen(stdscr, state, "Εγκατεστημένες Εφαρμογές", installed, allow_search=False)
            elif choice == "Λίστα Παρακολούθησης":
                watched = [APP_MAP[slug] for slug in state["watchlist"] if slug in APP_MAP]
                app_list_screen(stdscr, state, "Λίστα Παρακολούθησης", watched, allow_search=False)
            elif choice == "Έξοδος":
                return



def app_list_screen(stdscr, state, title, apps, allow_search=True):
    selected = 0
    query = ""

    while True:
        if allow_search and query:
            filtered = [
                app for app in apps
                if query.lower() in app["display_name"].lower()
                or query.lower() in app["slug"].lower()
            ]
        else:
            filtered = list(apps)

        if selected >= len(filtered) and filtered:
            selected = len(filtered) - 1
        if selected < 0:
            selected = 0

        subtitle = f"Σύνολο: {len(filtered)}"
        if allow_search:
            subtitle += f" | Αναζήτηση: {query or '(γράψε για αναζήτηση)'}"
        draw_header(stdscr, title, subtitle)

        if not filtered:
            add_line(stdscr, 4, 2, "Δεν βρέθηκαν εφαρμογές.", curses.color_pair(4))
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
                    flags.append("Εγκατεστημένο")
                if watched:
                    flags.append("Λίστα Παρακολούθησης")
                line = app["display_name"]
                if flags:
                    line += "  [" + ", ".join(flags) + "]"
                attr = curses.A_REVERSE if actual == selected else 0
                add_line(stdscr, 4 + idx, 2, line, attr)

        footer = "Enter: λεπτομέρειες | B: πίσω"
        if allow_search:
            footer += " | Γράψε: αναζήτηση | Backspace: διαγραφή | Esc: καθάρισμα"
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
            draw_header(stdscr, app["display_name"], "Φόρτωση λεπτομερειών αποθετηρίου...")
            draw_footer(stdscr, "Παρακαλώ περίμενε")
            stdscr.refresh()
            try:
                info = get_repo_info(app)
            except Exception as e:
                error_message = str(e)

        subtitle = app["slug"]
        if info and info.get("_source"):
            subtitle = f"{app['slug']} | Πηγή: {info['_source']}"
        draw_header(stdscr, app["display_name"], subtitle)
        height, width = stdscr.getmaxyx()

        if error_message:
            wrapped = []
            for block in error_message.split("\n"):
                wrapped.extend(textwrap.wrap(block, width=max(20, width - 4)) or [""])
            for idx, line in enumerate(wrapped[: max(1, height - 6)]):
                add_line(stdscr, 4 + idx, 2, line, curses.color_pair(4))
        else:
            installed = app["slug"] in state["installed"]
            watched = app["slug"] in state["watchlist"]
            contributors_text = ", ".join(info["contributors"]) if info["contributors"] else "Κανένας"
            release = info.get("release")
            if release:
                release_text = (
                    f"Ετικέτα: {release['tag']}\n"
                    f"Όνομα: {release['name']}\n"
                    f"Δημοσιεύτηκε: {release['published_at']}\n"
                    f"Σημειώσεις:\n{release['notes']}"
                )
            else:
                release_text = "Δεν βρέθηκε έκδοση στο GitHub."

            install_path = state["installed"].get(app["slug"], {}).get("path", "Δεν είναι εγκατεστημένο")

            body_blocks = [
                f"Όνομα Έργου: {info['display_name']}",
                f"Πλήρες Αποθετήριο: {info['full_name']}",
                f"Δημιουργός: {info['creator']}",
                f"Αποθετήριο: {info['url']}",
                f"Αστέρια: {info['stars']}  |  Forks: {info['forks']}  |  Watchers: {info['watchers']}",
                f"Ανοιχτά Θέματα: {info['issues_count']}",
                f"Εγκατεστημένο: {'Ναι' if installed else 'Όχι'}  |  Λίστα Παρακολούθησης: {'Ναι' if watched else 'Όχι'}",
                f"Διαδρομή Εγκατάστασης: {install_path}",
                "",
                "Τελευταία Έκδοση:",
                release_text,
                "",
                "Συνεισφέροντες:",
                contributors_text,
                "",
                "Ανοιχτά Θέματα (τελευταία):",
                ("\n".join(f"- {title}" for title in info['issues']) if info['issues'] else "Δεν βρέθηκαν ανοιχτά θέματα."),
                "",
                "README (καθαρισμένο):",
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

        footer_parts = ["B: πίσω", "R: ανανέωση"]
        if error_message:
            footer_parts.append("Ξανά: R")
        else:
            if app["slug"] in state["installed"]:
                footer_parts.extend(["U: ενημέρωση", "D: διαγραφή", "X: εκτέλεση"])
            else:
                footer_parts.append("I: εγκατάσταση")
            footer_parts.append("W: λίστα παρακολούθησης")
            footer_parts.append("Βελάκια: κύλιση")
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
            message = "Προστέθηκε στη λίστα παρακολούθησης." if added else "Αφαιρέθηκε από τη λίστα παρακολούθησης."
            prompt_message(stdscr, app["display_name"], message)
        elif key in (ord("i"), ord("I")) and app["slug"] not in state["installed"]:
            try:
                path = install_app(app, state)
                prompt_message(stdscr, app["display_name"], f"Installed successfully to:\n{path}")
            except Exception as e:
                prompt_message(stdscr, app["display_name"], str(e))
        elif key in (ord("u"), ord("U")) and app["slug"] in state["installed"]:
            try:
                output = update_app(app, state)
                prompt_message(stdscr, app["display_name"], output or "Ενημερώθηκε με επιτυχία.")
            except Exception as e:
                prompt_message(stdscr, app["display_name"], str(e))
        elif key in (ord("d"), ord("D")) and app["slug"] in state["installed"]:
            confirm = prompt_confirm(stdscr, app["display_name"], "Να διαγραφεί αυτή η εγκατεστημένη εφαρμογή από τον αρχικό φάκελο;")
            if confirm:
                try:
                    path = delete_app(app, state)
                    prompt_message(stdscr, app["display_name"], f"Deleted:\n{path}")
                except Exception as e:
                    prompt_message(stdscr, app["display_name"], str(e))
        elif key in (ord("x"), ord("X")) and app["slug"] in state["installed"]:
            try:
                target = run_installed_app(stdscr, app, state)
                prompt_message(stdscr, app["display_name"], f"Returned from:\n{target.name}")
            except Exception as e:
                prompt_message(stdscr, app["display_name"], str(e))


# -----------------------------
# Entry point
# -----------------------------

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
        print(f"{APP_NAME} κόλλησε: {e}")


if __name__ == "__main__":
    main()
