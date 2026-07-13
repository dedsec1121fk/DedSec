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
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

LANG = "en"

TEXT = {'app_name': 'DedSec Market',
 'invalid_repo_url': 'Invalid GitHub repository URL: {url}',
 'no_readme_description': 'No README description available.',
 'git_missing_and_no_pkg': 'git is not installed and Termux pkg was not found.',
 'git_install_failed': 'Failed to install git automatically.\n{output}',
 'no_cache': 'No cache',
 'unknown': 'Unknown',
 'github_request_failed': 'GitHub request failed: {message}',
 'network_error': 'Network error: {reason}',
 'readme_fetch_failed': 'Failed to fetch README: {message}',
 'no_release_notes': 'No release notes available.',
 'cache_with_age': 'cache ({age})',
 'live_cached_now': 'live (cached now)',
 'cache_fallback_with_age': 'cache fallback ({age})',
 'unnamed_release': 'Unnamed release',
 'download_repo_failed': 'Failed to download the repository again before replacing files.\n{output}',
 'already_installed': 'This app is already installed.',
 'not_installed': 'This app is not installed.',
 'installed_folder_missing': 'Installed folder was not found on disk.',
 'update_success_replaced': 'Update completed. The repository was downloaded again and the old files were '
                            'replaced in:\n'
                            '{path}',
 'no_installed_apps': 'No installed apps were found.',
 'no_launch_target': 'No launchable main file was detected in the installed repository.',
 'unsupported_launch_target': 'Unsupported launch target: {name}',
 'launching_file': 'DedSec Market is launching: {name}',
 'path_label': 'Path: {path}',
 'ctrlc_stop': 'Press Ctrl+C inside the launched app if you want to stop it.',
 'press_enter_return': 'Press Enter to return to DedSec Market...',
 'press_any_key_continue': 'Press any key to continue',
 'confirm_line': 'Press Y to confirm or N to cancel',
 'find_apps': 'Find Apps',
 'installed_apps': 'Installed Apps',
 'watchlist': 'Watchlist',
 'update_all_installed': 'Update All Installed',
 'exit': 'Exit',
 'main_menu': 'Main Menu',
 'data_folder': 'Data folder: {path}',
 'main_menu_footer': 'Arrow keys: move | Enter: open | Q: quit',
 'total_count': 'Total: {count}',
 'search_status': 'Search: {query}',
 'type_to_search': '(type to search)',
 'no_apps_found': 'No apps found.',
 'installed_flag': 'Installed',
 'watchlist_flag': 'Watchlist',
 'list_footer_basic': 'Enter: details | B: back',
 'list_footer_search': 'Type: search | Backspace: delete | Esc: clear',
 'loading_repository_details': 'Loading repository details...',
 'please_wait': 'Please wait',
 'source_label': 'Source: {source}',
 'none': 'None',
 'tag_label': 'Tag',
 'name_label': 'Name',
 'published_label': 'Published',
 'notes_label': 'Notes',
 'no_github_release': 'No GitHub release found.',
 'project_name': 'Project Name',
 'full_repository': 'Full Repository',
 'creator': 'Creator',
 'repository_label': 'Repository',
 'stars': 'Stars',
 'forks': 'Forks',
 'watchers': 'Watchers',
 'open_issues': 'Open Issues',
 'installed_status': 'Installed',
 'watchlist_status': 'Watchlist',
 'yes': 'Yes',
 'no': 'No',
 'install_path': 'Install Path',
 'latest_release': 'Latest Release:',
 'contributors': 'Contributors:',
 'latest_open_issues': 'Open Issues (latest):',
 'no_open_issues_found': 'No open issues found.',
 'readme_language_cleaned': 'README (English section when available):',
 'back_footer': 'B: back',
 'refresh_footer': 'R: refresh',
 'update_footer': 'U: update',
 'delete_footer': 'D: delete',
 'run_footer': 'X: run',
 'install_footer': 'I: install',
 'watchlist_footer': 'W: watchlist',
 'scroll_footer': 'Arrows: scroll',
 'added_to_watchlist': 'Added to watchlist.',
 'removed_from_watchlist': 'Removed from watchlist.',
 'installed_successfully_to': 'Installed successfully to:\n{path}',
 'updated_successfully': 'Updated successfully.',
 'delete_confirm': 'Delete this installed app from your home directory?',
 'deleted_path': 'Deleted:\n{path}',
 'returned_from': 'Returned from:\n{name}',
 'seconds_ago': '{count}s ago',
 'minutes_ago': '{count}m ago',
 'hours_ago': '{count}h ago',
 'unsafe_install_path': 'Refusing to use an unsafe installation path: {path}',
 'download_repository': 'Downloading Repository',
 'installing_files': 'Installing Files',
 'updating_repository': 'Updating Repository',
 'replacing_files': 'Replacing Old Files',
 'restoring_files': 'Restoring Previous Files',
 'cleaning_temporary_files': 'Cleaning Temporary Files',
 'operation_complete': 'Operation Complete',
 'progress_label': 'Progress: {percent}%',
 'progress_wait': 'Please wait. Do not close Termux during this operation.',
 'starting_download': 'Starting repository download...',
 'preparing_installation': 'Preparing installation...',
 'preparing_update': 'Preparing update...',
 'install_move_failed': 'The repository was downloaded, but installation failed.\n{output}',
 'update_replace_failed': 'The new repository was downloaded, but replacing the installed files failed. '
                          'The previous installation was restored.\n'
                          '{output}',
 'update_restore_failed': 'The update failed and the previous installation could not be restored '
                          'automatically. Backup folder:\n'
                          '{backup}\n'
                          '\n'
                          'Error:\n'
                          '{output}',
 'update_item': 'Updating {current}/{total}: {name}',
 'download_output': 'Git: {message}',
 'python_missing': 'Python was not found.',
 'bash_missing': 'Bash was not found.',
 'git_output_unavailable': 'Unable to read git output.'}

APP_NAME = TEXT["app_name"]
DATA_DIR = Path.home() / APP_NAME
CACHE_DIR = DATA_DIR / "cache"
STATE_FILE = DATA_DIR / "state.json"
USER_AGENT = "DedSec-Market-Termux/1.3"
GITHUB_API = "https://api.github.com"
CACHE_TTL_SECONDS = 1800
PARSER_VERSION = 8

REPOSITORIES = [
    {"url": "https://github.com/dedsec1121fk/Offline-Survival-Project"},
    {"url": "https://github.com/dedsec1121fk/Corrupted-Files-Project"},
    {"url": "https://github.com/dedsec1121fk/Pocket-AI"},
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


def atomic_write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(path.name + ".tmp")
    try:
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def save_state(state):
    ensure_data_dir()
    atomic_write_json(STATE_FILE, state)


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
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"~~([^~]+)~~", r"\1", text)

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


def normalize_language_code(language):
    value = str(language or "en").strip().lower()
    if value in {"el", "gr", "greek", "ellinika", "ελληνικά", "ελληνικα"}:
        return "el"
    return "en"


def remove_accents(text):
    normalized = unicodedata.normalize("NFD", str(text))
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def language_character_counts(text):
    greek = 0
    latin = 0
    for char in str(text):
        code = ord(char)
        if 0x0370 <= code <= 0x03FF or 0x1F00 <= code <= 0x1FFF:
            greek += 1
        elif "A" <= char <= "Z" or "a" <= char <= "z":
            latin += 1
    return greek, latin


def normalize_language_label(text):
    value = strip_markdown(str(text or ""))
    value = html_lib.unescape(value).replace("\xa0", " ").strip().lower()
    value = remove_accents(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t\r\n#>*_`[](){}.!?")


def detect_language_label(text):
    value = normalize_language_label(text)
    if not value:
        return None

    english_aliases = {"english", "en", "eng", "αγγλικα", "αγγλικη εκδοση", "🇬🇧", "🇺🇸"}
    greek_aliases = {"greek", "el", "gr", "ellinika", "ελληνικα", "ελληνικη εκδοση", "🇬🇷"}

    if value in english_aliases:
        return "en"
    if value in greek_aliases:
        return "el"

    compact = re.sub(r"\s+", " ", value).strip()
    if re.fullmatch(r"(?:🇬🇧|🇺🇸)?\s*(?:english|en|eng|αγγλικα|αγγλικη εκδοση)", compact):
        return "en"
    if re.fullmatch(r"(?:🇬🇷)?\s*(?:greek|el|gr|ellinika|ελληνικα|ελληνικη εκδοση)", compact):
        return "el"

    for separator in ("—", "–", "|", ":"):
        if separator in value:
            tail = value.rsplit(separator, 1)[-1].strip(" -")
            if tail in english_aliases:
                return "en"
            if tail in greek_aliases:
                return "el"

    suffix_match = re.search(
        r"(?:^|\s[-—–|:]\s*)(english|en|greek|el|gr|ellinika|ελληνικα|🇬🇧|🇬🇷)\s*$",
        value,
    )
    if suffix_match:
        token = suffix_match.group(1)
        return "el" if token in greek_aliases else "en"
    return None


def extract_details_language_sections(readme_text, language):
    target = normalize_language_code(language)
    details_pattern = re.compile(r"<details[^>]*>(.*?)</details>", re.IGNORECASE | re.DOTALL)
    summary_pattern = re.compile(r"<summary[^>]*>(.*?)</summary>", re.IGNORECASE | re.DOTALL)
    sections = []
    for block_match in details_pattern.finditer(readme_text):
        block = block_match.group(1)
        summary_match = summary_pattern.search(block)
        if not summary_match:
            continue
        if detect_language_label(summary_match.group(1)) != target:
            continue
        inner = summary_pattern.sub("", block, count=1).strip()
        if inner:
            sections.append(inner)
    return sections


def extract_heading_language_sections(readme_text, language):
    target = normalize_language_code(language)
    lines = readme_text.splitlines()
    target_levels = []
    in_code_fence = False

    for line in lines:
        stripped = line.strip()
        if re.match(r"^(?:```|~~~)", stripped):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match and detect_language_label(heading_match.group(2)) == target:
            target_levels.append(len(heading_match.group(1)))

    if not target_levels:
        return []
    preferred_level = min(target_levels)

    sections = []
    capture = None
    capture_level = None
    in_code_fence = False

    for line in lines:
        stripped = line.strip()
        if re.match(r"^(?:```|~~~)", stripped):
            in_code_fence = not in_code_fence
            if capture is not None:
                capture.append(line)
            continue

        heading_match = None if in_code_fence else re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            hashes, heading_text = heading_match.groups()
            level = len(hashes)
            marker = detect_language_label(heading_text)

            if capture is not None and level <= (capture_level or 6):
                result = "\n".join(capture).strip()
                if result:
                    sections.append(result)
                capture = None
                capture_level = None

            if marker == target and level == preferred_level:
                capture = []
                capture_level = level
                continue

        if capture is not None:
            capture.append(line)

    if capture is not None:
        result = "\n".join(capture).strip()
        if result:
            sections.append(result)
    return sections



def extract_interleaved_language_section(readme_text, language):
    target = normalize_language_code(language)
    lines = readme_text.splitlines()
    plain_markers = []
    in_code_fence = False

    for line in lines:
        stripped = line.strip()
        if re.match(r"^(?:```|~~~)", stripped):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence or not stripped or stripped.startswith("#"):
            continue
        marker = detect_language_label(stripped)
        if marker:
            plain_markers.append(marker)

    if len(plain_markers) < 4 or "en" not in plain_markers or "el" not in plain_markers:
        return None

    output = []
    pending_shared = []
    active_language = None
    in_code_fence = False

    for line in lines:
        stripped = line.strip()
        if re.match(r"^(?:```|~~~)", stripped):
            in_code_fence = not in_code_fence
            if active_language == target:
                output.append(line)
            elif active_language is None:
                pending_shared.append(line)
            continue

        marker = None if in_code_fence else detect_language_label(
            re.sub(r"^#{1,6}\s+", "", stripped)
        )
        if marker:
            active_language = marker
            if marker == target and pending_shared:
                output.extend(pending_shared)
            pending_shared = []
            continue

        heading_match = None if in_code_fence else re.match(r"^(#{1,6})\s+", stripped)
        if heading_match:
            if active_language == target:
                active_language = None
                pending_shared = [line]
            elif active_language is not None:
                active_language = None
                pending_shared = [line]
            else:
                pending_shared.append(line)
            continue

        if active_language == target:
            output.append(line)
        elif active_language is None:
            pending_shared.append(line)

    result = "\n".join(output).strip()
    return result or None



def filter_embedded_opposite_language_sections(text, language):
    target = normalize_language_code(language)
    opposite = "el" if target == "en" else "en"
    output = []
    skip_level = None
    in_code_fence = False

    for line in str(text or "").splitlines():
        stripped = line.strip()
        if re.match(r"^(?:```|~~~)", stripped):
            in_code_fence = not in_code_fence
            if skip_level is None:
                output.append(line)
            continue

        heading_match = None if in_code_fence else re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            level = len(heading_match.group(1))
            marker = detect_language_label(heading_match.group(2))

            if skip_level is not None:
                if level > skip_level:
                    continue
                skip_level = None

            if marker == opposite:
                skip_level = level
                continue
            if marker == target:
                continue

        if skip_level is None:
            output.append(line)

    return "\n".join(output).strip()


def dominant_text_language(text):
    cleaned = strip_markdown(text)
    greek, latin = language_character_counts(cleaned)
    if greek >= 20 and greek >= latin * 0.18:
        return "el"
    if latin >= 20 and greek <= latin * 0.08:
        return "en"
    return None


def extract_inferred_h1_sections(readme_text, language):
    target = normalize_language_code(language)
    lines = readme_text.splitlines()
    sections = []
    current = []
    in_code_fence = False

    for line in lines:
        stripped = line.strip()
        if re.match(r"^(?:```|~~~)", stripped):
            in_code_fence = not in_code_fence
        if not in_code_fence and re.match(r"^#\s+", stripped):
            if current:
                sections.append("\n".join(current).strip())
            current = [line]
        elif current:
            current.append(line)
    if current:
        sections.append("\n".join(current).strip())

    classified = [(dominant_text_language(section), section) for section in sections]
    languages_found = {lang for lang, _ in classified if lang}
    if not {"en", "el"}.issubset(languages_found):
        return []
    return [section for lang, section in classified if lang == target]


def language_candidate_score(text, language):
    target = normalize_language_code(language)
    cleaned = strip_markdown(text)
    greek, latin = language_character_counts(cleaned)
    total = greek + latin
    if not cleaned or total < 20:
        return -1
    if target == "el":
        if greek < 15:
            return -1
        purity = greek / max(total, 1)
    else:
        if latin < 15:
            return -1
        purity = latin / max(total, 1)
    return len(cleaned) * (0.65 + purity)


def fallback_language_blocks(readme_text, language):
    target = normalize_language_code(language)
    cleaned = strip_markdown(readme_text)
    kept_blocks = []
    for block in re.split(r"\n\s*\n", cleaned):
        block = block.strip()
        if not block:
            continue
        greek, latin = language_character_counts(block)
        if target == "el":
            if greek >= 3:
                kept_blocks.append(block)
        else:
            if latin >= 3 and greek <= max(2, latin * 0.35):
                kept_blocks.append(block)
    return "\n\n".join(kept_blocks).strip()


def extract_language_summary(readme_text, repo_description="", language=None):
    target = normalize_language_code(language or LANG)
    if not readme_text:
        return repo_description or tr("no_readme_description")

    candidates = []
    details_sections = extract_details_language_sections(readme_text, target)
    if details_sections:
        details_text = "\n\n".join(details_sections)
        if language_candidate_score(details_text, target) >= 0:
            cleaned_details = strip_markdown(details_text)
            if cleaned_details:
                return cleaned_details
    heading_candidates = []
    for heading_section in extract_heading_language_sections(readme_text, target):
        filtered_section = filter_embedded_opposite_language_sections(heading_section, target)
        if filtered_section:
            heading_candidates.append(filtered_section)
            candidates.append(filtered_section)

    interleaved = extract_interleaved_language_section(readme_text, target)
    if interleaved:
        candidates.append(interleaved)

    if not heading_candidates:
        candidates.extend(extract_inferred_h1_sections(readme_text, target))

    best_text = None
    best_score = -1
    for candidate in candidates:
        score = language_candidate_score(candidate, target)
        if score > best_score:
            best_text = strip_markdown(candidate)
            best_score = score

    if best_text:
        return best_text

    fallback = fallback_language_blocks(readme_text, target)
    if fallback and language_candidate_score(fallback, target) >= 0:
        return fallback

    cleaned = strip_markdown(readme_text)
    return repo_description or cleaned or tr("no_readme_description")



def run_command(command, cwd=None):
    process = subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
    )
    return process.returncode, process.stdout.strip()


GIT_PROGRESS_PHASES = (
    ("enumerating objects", 0, 8),
    ("counting objects", 8, 18),
    ("compressing objects", 18, 32),
    ("receiving objects", 32, 82),
    ("resolving deltas", 82, 96),
    ("checking out files", 96, 100),
    ("updating files", 96, 100),
)


def report_progress(progress_callback, percent, status):
    if progress_callback is None:
        return
    percent = max(0, min(100, int(round(percent))))
    try:
        progress_callback(percent, str(status or ""))
    except Exception:
        # A display failure must not corrupt an installation or update.
        pass


def parse_git_progress(line, previous_percent=0):
    cleaned = re.sub(r"^remote:\s*", "", str(line or "").strip(), flags=re.IGNORECASE)
    lowered = cleaned.lower()
    percent_match = re.search(r"(\d{1,3})%", cleaned)
    if percent_match:
        phase_percent = max(0, min(100, int(percent_match.group(1))))
        for phase, start, end in GIT_PROGRESS_PHASES:
            if phase in lowered:
                overall = start + ((end - start) * phase_percent / 100.0)
                return max(previous_percent, int(round(overall))), cleaned
        return max(previous_percent, phase_percent), cleaned
    return previous_percent, cleaned


def run_git_clone(command, cwd=None, progress_callback=None):
    output_parts = []
    current_percent = 0
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
    )
    if process.stdout is None:
        process.kill()
        process.wait()
        raise MarketError(tr("download_repo_failed", output=tr("git_output_unavailable")))

    pending = ""
    try:
        while True:
            chunk = process.stdout.read(512)
            if not chunk:
                break
            pending += chunk.decode("utf-8", errors="replace")
            parts = re.split(r"[\r\n]+", pending)
            pending = parts.pop() if parts else ""
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                output_parts.append(part)
                current_percent, message = parse_git_progress(part, current_percent)
                report_progress(
                    progress_callback,
                    current_percent,
                    tr("download_output", message=message),
                )

        if pending.strip():
            output_parts.append(pending.strip())
            current_percent, message = parse_git_progress(pending.strip(), current_percent)
            report_progress(
                progress_callback,
                current_percent,
                tr("download_output", message=message),
            )
        return_code = process.wait()
        return return_code, "\n".join(output_parts).strip()
    except BaseException:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        raise
    finally:
        process.stdout.close()


def scale_progress_callback(progress_callback, start_percent, end_percent):
    if progress_callback is None:
        return None

    def scaled(percent, status):
        span = max(0, end_percent - start_percent)
        overall = start_percent + (span * max(0, min(100, percent)) / 100.0)
        report_progress(progress_callback, overall, status)

    return scaled


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
    atomic_write_json(path, data)


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
    seconds = max(0, int(time.time() - cached_at))
    if seconds < 60:
        return tr("seconds_ago", count=seconds)
    minutes = seconds // 60
    if minutes < 60:
        return tr("minutes_ago", count=minutes)
    hours = minutes // 60
    return tr("hours_ago", count=hours)


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
            "description": extract_language_summary(readme_text, repo_data.get("description", ""), LANG),
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


def validate_install_path(app, path, must_exist=True):
    path = Path(path).expanduser()
    home = Path.home().resolve()
    resolved = path.resolve(strict=False)
    expected_name = app["repo"]
    valid_name = resolved.name == expected_name or bool(
        re.fullmatch(re.escape(expected_name) + r"-\d+", resolved.name)
    )
    if resolved.parent != home or not valid_name or path.is_symlink():
        raise MarketError(tr("unsafe_install_path", path=path))
    if must_exist and (not path.exists() or not path.is_dir()):
        raise MarketError(tr("installed_folder_missing"))
    return path


def unique_backup_path(path):
    path = Path(path)
    base = path.with_name(f".{path.name}.dedsec-market-backup")
    if not base.exists():
        return base
    counter = 1
    while True:
        candidate = path.with_name(f".{path.name}.dedsec-market-backup-{counter}")
        if not candidate.exists():
            return candidate
        counter += 1


def clone_repo_to_temp(app, progress_callback=None):
    ensure_git()
    ensure_data_dir()
    report_progress(progress_callback, 0, tr("starting_download"))
    temp_dir = Path(
        tempfile.mkdtemp(prefix="download_", dir=str(DATA_DIR))
    )
    clone_path = temp_dir / app["repo"]
    command = ["git", "clone", "--depth", "1", "--progress", app["url"], str(clone_path)]
    try:
        code, output = run_git_clone(command, progress_callback=progress_callback)
    except BaseException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    if code != 0 or not clone_path.is_dir():
        shutil.rmtree(temp_dir, ignore_errors=True)
        limited_output = "\n".join(output.splitlines()[-30:])
        raise MarketError(tr("download_repo_failed", output=limited_output or tr("unknown")))
    git_dir = clone_path / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir, ignore_errors=True)
    report_progress(progress_callback, 100, tr("download_repository"))
    return temp_dir, clone_path


def install_app(app, state, progress_callback=None):
    slug = app["slug"]
    if slug in state["installed"]:
        raise MarketError(tr("already_installed"))
    base_path = suggested_install_path(app)
    install_path = validate_install_path(app, unique_install_path(base_path), must_exist=False)
    report_progress(progress_callback, 0, tr("preparing_installation"))
    temp_dir, clone_path = clone_repo_to_temp(
        app,
        scale_progress_callback(progress_callback, 2, 88),
    )
    moved = False
    try:
        report_progress(progress_callback, 92, tr("installing_files"))
        shutil.move(str(clone_path), str(install_path))
        moved = True
        state["installed"][slug] = {
            "display_name": app["display_name"],
            "path": str(install_path),
            "repo_url": app["url"],
            "installed_at": int(time.time()),
        }
        save_state(state)
        report_progress(progress_callback, 98, tr("cleaning_temporary_files"))
        shutil.rmtree(temp_dir, ignore_errors=True)
        report_progress(progress_callback, 100, tr("operation_complete"))
        return install_path
    except BaseException as e:
        state["installed"].pop(slug, None)
        if moved and install_path.exists():
            shutil.rmtree(install_path, ignore_errors=True)
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        if isinstance(e, MarketError):
            raise
        raise MarketError(tr("install_move_failed", output=e)) from e
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def update_app(app, state, progress_callback=None):
    slug = app["slug"]
    item = state["installed"].get(slug)
    if not item:
        raise MarketError(tr("not_installed"))
    path = validate_install_path(app, item["path"], must_exist=True)
    old_item = dict(item)
    report_progress(progress_callback, 0, tr("preparing_update"))
    temp_dir, clone_path = clone_repo_to_temp(
        app,
        scale_progress_callback(progress_callback, 2, 84),
    )
    backup_path = unique_backup_path(path)
    old_moved = False
    new_moved = False
    try:
        report_progress(progress_callback, 88, tr("replacing_files"))
        shutil.move(str(path), str(backup_path))
        old_moved = True
        shutil.move(str(clone_path), str(path))
        new_moved = True
        item["updated_at"] = int(time.time())
        item["last_update_mode"] = "full_redownload_atomic_replace"
        save_state(state)
        report_progress(progress_callback, 97, tr("cleaning_temporary_files"))
        shutil.rmtree(backup_path, ignore_errors=True)
        report_progress(progress_callback, 100, tr("operation_complete"))
        return tr("update_success_replaced", path=path)
    except BaseException as e:
        item.clear()
        item.update(old_item)
        restore_error = None
        try:
            report_progress(progress_callback, 90, tr("restoring_files"))
            if new_moved and path.exists():
                shutil.rmtree(path, ignore_errors=True)
            if old_moved and backup_path.exists():
                shutil.move(str(backup_path), str(path))
        except BaseException as restore_exception:
            restore_error = restore_exception

        if restore_error is not None:
            raise MarketError(
                tr("update_restore_failed", backup=backup_path, output=restore_error)
            ) from e
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        if isinstance(e, MarketError):
            raise
        raise MarketError(tr("update_replace_failed", output=e)) from e
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def update_all_installed(state, progress_callback=None):
    installed_slugs = [slug for slug in state["installed"] if slug in APP_MAP]
    if not installed_slugs:
        return [tr("no_installed_apps")]
    results = []
    total = len(installed_slugs)
    for index, slug in enumerate(installed_slugs):
        app = APP_MAP[slug]

        def item_progress(percent, status, index=index, app=app):
            overall = ((index + max(0, min(100, percent)) / 100.0) / total) * 100.0
            prefix = tr(
                "update_item",
                current=index + 1,
                total=total,
                name=app["display_name"],
            )
            report_progress(progress_callback, overall, f"{prefix}\n{status}")

        try:
            message = update_app(app, state, item_progress)
            results.append(f"• {app['display_name']}: {message}")
        except Exception as e:
            results.append(f"• {app['display_name']}: {e}")
    report_progress(progress_callback, 100, tr("operation_complete"))
    return results


def delete_app(app, state):
    slug = app["slug"]
    item = state["installed"].get(slug)
    if not item:
        raise MarketError(tr("not_installed"))
    path = validate_install_path(app, item["path"], must_exist=False)
    if path.exists():
        if not path.is_dir():
            raise MarketError(tr("unsafe_install_path", path=path))
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
    install_path = validate_install_path(app, item["path"], must_exist=True)
    target = detect_launch_target(app, install_path)
    if not target:
        raise MarketError(tr("no_launch_target"))
    if target.suffix.lower() == ".py":
        python_command = shutil.which("python") or shutil.which("python3")
        if not python_command:
            raise MarketError(tr("python_missing"))
        command = [python_command, str(target)]
    elif target.suffix.lower() == ".sh":
        bash_command = shutil.which("bash")
        if not bash_command:
            raise MarketError(tr("bash_missing"))
        command = [bash_command, str(target)]
    else:
        raise MarketError(tr("unsupported_launch_target", name=target.name))

    curses.def_prog_mode()
    curses.endwin()
    try:
        print("\n" + tr("launching_file", name=target.name))
        print(tr("path_label", path=target))
        print("\n" + tr("ctrlc_stop") + "\n")
        subprocess.run(command, cwd=str(target.parent), check=False)
        input("\n" + tr("press_enter_return"))
    finally:
        curses.reset_prog_mode()
        stdscr.refresh()
    return target


def init_colors():
    if not curses.has_colors():
        return
    curses.start_color()
    try:
        curses.use_default_colors()
        background = -1
    except curses.error:
        background = curses.COLOR_BLACK
    curses.init_pair(1, curses.COLOR_CYAN, background)
    curses.init_pair(2, curses.COLOR_GREEN, background)
    curses.init_pair(3, curses.COLOR_YELLOW, background)
    curses.init_pair(4, curses.COLOR_RED, background)
    curses.init_pair(5, curses.COLOR_MAGENTA, background)


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


def draw_progress_screen(stdscr, title, percent, status=""):
    percent = max(0, min(100, int(round(percent))))
    draw_header(stdscr, title, tr("progress_label", percent=percent))
    height, width = stdscr.getmaxyx()
    usable_width = max(3, width - 6)
    inner_width = max(1, min(56, usable_width - 2))
    filled = int(round(inner_width * percent / 100.0))
    bar = "[" + ("#" * filled) + ("-" * (inner_width - filled)) + "]"
    bar_y = max(3, min(height - 3, height // 2 - 1))
    bar_x = max(0, (width - len(bar)) // 2)
    add_line(stdscr, bar_y, bar_x, bar, curses.A_BOLD | curses.color_pair(2))

    status_lines = []
    for block in str(status or "").splitlines():
        status_lines.extend(textwrap.wrap(block, width=max(10, width - 6)) or [""])
    for index, line in enumerate(status_lines[:max(0, height - bar_y - 3)]):
        x = max(0, (width - len(line)) // 2)
        add_line(stdscr, bar_y + 2 + index, x, line, curses.color_pair(3))
    draw_footer(stdscr, tr("progress_wait"))
    stdscr.refresh()


def make_progress_callback(stdscr, title):
    last = {"percent": None, "status": None}

    def callback(percent, status):
        normalized_percent = max(0, min(100, int(round(percent))))
        normalized_status = str(status or "")
        if last["percent"] == normalized_percent and last["status"] == normalized_status:
            return
        last["percent"] = normalized_percent
        last["status"] = normalized_status
        draw_progress_screen(stdscr, title, normalized_percent, normalized_status)

    return callback


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
                progress = make_progress_callback(stdscr, tr("update_all_installed"))
                results = update_all_installed(state, progress)
                prompt_message(stdscr, tr("update_all_installed"), "\n".join(results))
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
                tr("readme_language_cleaned"),
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
                progress = make_progress_callback(stdscr, tr("download_repository"))
                path = install_app(app, state, progress)
                prompt_message(stdscr, app["display_name"], tr("installed_successfully_to", path=path))
            except Exception as e:
                prompt_message(stdscr, app["display_name"], str(e))
        elif key in (ord("u"), ord("U")) and app["slug"] in state["installed"]:
            try:
                progress = make_progress_callback(stdscr, tr("updating_repository"))
                output = update_app(app, state, progress)
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
    try:
        curses.curs_set(0)
    except curses.error:
        pass
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
