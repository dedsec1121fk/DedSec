#!/usr/bin/env python3

import argparse
import fnmatch
import hashlib
import json as _json
import os
import re
import stat
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union


# ==========================
# i18n (English + Greek)
# ==========================
LANGS = ("en",)

I18N: Dict[str, str] = {'choice_1_4': 'Choice [1-4] (default 1): ',
 'clean_dupes_title': '\nClean duplicates (safe trash)',
 'dupes_algo': 'Hash algorithm (1=md5, 2=sha256) default 2: ',
 'dupes_groups': 'Found {n} duplicate group(s).',
 'dupes_none': '(no duplicates found)',
 'dupes_title': '\nDuplicate files (hash)',
 'empty_found': 'Found {n} empty folder(s).',
 'empty_title': '\nEmpty folders',
 'enter_path': 'Enter path: ',
 'err_export': "Error: couldn't export to '{path}': {err}",
 'err_open': "Error: can't open path.",
 'err_path_missing': "Error: path '{path}' does not exist.",
 'explorer_help': 'Commands: number=open, u=up, i=info, p=preview, q=quit',
 'explorer_not_dir': 'Not a folder.',
 'explorer_path': 'Current: {path}',
 'explorer_pick': 'Pick: ',
 'explorer_preview_fail': "Can't preview this file.",
 'explorer_preview_lines': 'Preview lines (default 30): ',
 'explorer_title': '\nExplorer mode',
 'help_body': 'Run menu (default):\n'
              '  python "Tree Explorer.py"\n'
              'Open menu:\n'
              '  python "Tree Explorer.py" --menu\n'
              'Install (no root):\n'
              '  python "Tree Explorer.py" --install\n'
              '\n'
              'Extra examples:\n'
              '  python "Tree Explorer.py" --folder-sizes --top 30 /sdcard\n'
              '  python "Tree Explorer.py" --recent 7 --top 200 /sdcard\n'
              '  python "Tree Explorer.py" --clean-dupes --min-size 1048576 /sdcard\n'
              '  python "Tree Explorer.py" --remove-empty /sdcard\n'
              '\n'
              'Advanced flags:\n'
              '  -L <depth>  -S  --dirs-only  --size  --json  --summary  --top N\n'
              '  --ignore PATTERN  --only PATTERN  --follow-symlinks\n'
              '  --no-color  --no-hidden  --rich  --export FILE\n',
 'help_title': '\nHelp / Βοήθεια',
 'info_perms': 'perms',
 'info_size': 'size',
 'info_type': 'type',
 'info_unreadable': '(unreadable)',
 'install_err_bin': "Error: can't create bin dir: {path} ({err})",
 'install_err_failed': 'Error: install failed: {err}',
 'install_err_prefix': "Error: couldn't detect Termux PREFIX. Set PREFIX env var or run inside Termux.",
 'install_ok': 'Installed! Run it as:\n  {alias}\nOr with options:\n  {alias} -L 2 --size -S /sdcard',
 'kind_dir': 'dir',
 'kind_file': 'file',
 'kind_symlink': 'symlink',
 'label_files_word': 'files',
 'label_keep': 'Keep',
 'label_trash': 'Trash',
 'menu_0': '0) Exit',
 'menu_1': '1) Quick view (depth 2, sizes, sort by size)',
 'menu_10': '10) Top-N largest files',
 'menu_11': '11) Find empty folders',
 'menu_12': '12) Find duplicate files (hash)',
 'menu_13': '13) Trash files by pattern (safe move)',
 'menu_14': '14) Folder sizes report (Top-N)',
 'menu_15': '15) Recent files (last N days)',
 'menu_16': '16) Clean duplicates (keep newest, trash rest)',
 'menu_17': '17) Remove empty folders (safe move)',
 'menu_2': '2) Custom view (choose options)',
 'menu_3': '3) Only folders',
 'menu_4': '4) JSON export',
 'menu_5': "5) Install command 'supertree' (no root)",
 'menu_6': '6) Help',
 'menu_8': '8) Explorer mode (navigate folders by numbers)',
 'menu_9': '9) Search (glob / contains / regex)',
 'menu_title': '\n=== Tree Explorer Menu ===',
 'path_1': '1) Current folder (.)',
 'path_2': '2) Termux home (~)',
 'path_3': '3) /sdcard (shared storage)',
 'path_4': '4) Type another path',
 'pick_path': '\nPick a path:',
 'placeholder_empty': '(empty)',
 'placeholder_none': '(none)',
 'prompt_action': 'Choose: ',
 'prompt_confirm': 'Type YES to confirm: ',
 'prompt_days': 'Days (default 7): ',
 'prompt_depth_default': 'Depth (-1 for unlimited) (default {default}): ',
 'prompt_export': 'Export output to file? (enter path, blank = no)',
 'prompt_follow': 'Follow symlinked folders? (unsafe)',
 'prompt_hide_dot': 'Hide dotfiles?',
 'prompt_ignore': 'Ignore patterns (comma separated, optional)',
 'prompt_index': 'Number: ',
 'prompt_min_size': 'Min size bytes (default 1): ',
 'prompt_only': 'Only include patterns (comma separated, optional)',
 'prompt_rich': 'Prettier output with Rich? (auto-install)',
 'prompt_sizes': 'Show sizes?',
 'prompt_sort': 'Sort by size?',
 'prompt_summary': 'Show summary (totals)?',
 'prompt_top': 'Top-N (enter number, default 20): ',
 'recent_title': '\nRecent files',
 'remove_empty_title': '\nRemove empty folders (safe trash)',
 'rich_fallback': "Note: couldn't install/use 'rich'; falling back to built-in output.",
 'search_done': 'Found {n} result(s).',
 'search_max': 'Max results (0 = unlimited, default 200): ',
 'search_none': '(no results)',
 'search_query': 'Enter search query: ',
 'search_title': '\nSearch mode',
 'search_type': 'Search type:\n  1) glob (*.mp3)\n  2) contains (text)\n  3) regex',
 'sizes_title': '\nFolder sizes report',
 'summary_dirs': 'Folders',
 'summary_errors': 'Errors',
 'summary_files': 'Files',
 'summary_skipped': 'Skipped',
 'summary_title': '\nSummary',
 'summary_total': 'Total size',
 'trash_confirm_msg': "This will MOVE items into '{trash}'. It won't permanently delete them.",
 'trash_done': 'Moved {n} item(s) to trash.',
 'trash_found': 'Matched {n} item(s).',
 'trash_none': '(no matches)',
 'trash_pattern': 'Enter pattern to trash (glob, e.g. *.tmp): ',
 'trash_skip': 'Skipped {n} item(s).',
 'trash_title': '\nTrash files (safe move)',
 'unknown_choice': 'Unknown choice.',
 'yes_no': '[Y/n]: ',
 'yes_no_default_no': '[y/N]: '}

def t(key: str, lang: str, **kwargs) -> str:
    pack = I18N.get(key, {})
    text = pack.get(lang) or pack.get("en") or key
    try:
        return text.format(**kwargs)
    except Exception:
        return text


# ------------------ ANSI coloring ------------------
RESET = "\033[0m"
DIRC = "\033[1;34m"
EXEC = "\033[1;32m"
LINKC = "\033[1;36m"

def colorize(name: str, mode: int, no_color: bool) -> str:
    if no_color:
        return name
    if stat.S_ISDIR(mode):
        return f"{DIRC}{name}{RESET}"
    if stat.S_ISLNK(mode):
        return f"{LINKC}{name}{RESET}"
    if stat.S_ISREG(mode) and (mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)):
        return f"{EXEC}{name}{RESET}"
    return name


# ------------------ size helpers ------------------
UNITS = ("B", "KB", "MB", "GB", "TB", "PB")

def format_size(num_bytes: int) -> str:
    s = float(max(0, num_bytes))
    unit = 0
    while s >= 1024.0 and unit < len(UNITS) - 1:
        s /= 1024.0
        unit += 1
    return f"{s:.2f} {UNITS[unit]}"

def safe_lstat(path: Path) -> Optional[os.stat_result]:
    try:
        return path.lstat()
    except OSError:
        return None


def normalize_patterns(raw: str) -> List[str]:
    if not raw.strip():
        return []
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]


def match_any(path: Path, name: str, patterns: List[str]) -> bool:
    if not patterns:
        return False
    s1 = name
    s2 = str(path.as_posix())
    for pat in patterns:
        if fnmatch.fnmatchcase(s1, pat) or fnmatch.fnmatchcase(s2, pat):
            return True
    return False


@dataclass
class WalkStats:
    files: int = 0
    dirs: int = 0
    total_size: int = 0
    skipped: int = 0
    errors: int = 0


def get_total_size(
    path: Path,
    *,
    follow_symlinks: bool,
    ignore: List[str],
    only: List[str],
    include_hidden: bool,
    stats: Optional[WalkStats] = None,
    _seen_dirs: Optional[Set[Tuple[int, int]]] = None,
) -> int:
    if _seen_dirs is None:
        _seen_dirs = set()

    st = safe_lstat(path)
    if st is None:
        if stats:
            stats.errors += 1
        return 0

def t(key: str, lang: str, **kwargs) -> str:
    text = I18N.get(key, key)
    try:
        return text.format(**kwargs)
    except Exception:
        return text


    if match_any(path, name, ignore):
        if stats:
            stats.skipped += 1
        return 0

    is_dir = stat.S_ISDIR(mode) or (stat.S_ISLNK(mode) and follow_symlinks and path.is_dir())
    if only and not is_dir and not match_any(path, name, only):
        if stats:
            stats.skipped += 1
        return 0

    if stat.S_ISLNK(mode) and not follow_symlinks:
        if stats:
            stats.files += 1
            stats.total_size += int(st.st_size)
        return int(st.st_size)

    if not stat.S_ISDIR(mode):
        if stats:
            stats.files += 1
            stats.total_size += int(st.st_size)
        return int(st.st_size)

    if follow_symlinks:
        key = (int(st.st_dev), int(st.st_ino))
        if key in _seen_dirs:
            if stats:
                stats.skipped += 1
            return 0
        _seen_dirs.add(key)

    if stats:
        stats.dirs += 1

    total = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                if entry.name in (".", ".."):
                    continue
                try:
                    total += get_total_size(
                        path / entry.name,
                        follow_symlinks=follow_symlinks,
                        ignore=ignore,
                        only=only,
                        include_hidden=include_hidden,
                        stats=stats,
                        _seen_dirs=_seen_dirs,
                    )
                except Exception:
                    if stats:
                        stats.errors += 1
                    continue
    except OSError:
        if stats:
            stats.errors += 1
        return 0

    return total


# ------------------ optional Rich output ------------------
def ensure_pip_package(pkg: str, import_name: Optional[str] = None) -> bool:
    name = import_name or pkg
    try:
        __import__(name)
        return True
    except Exception:
        pass
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--user", pkg],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        __import__(name)
        return True
    except Exception:
        return False


# ------------------ model ------------------
@dataclass
class Entry:
    name: str
    path: Path
    mode: int
    is_dir: bool
    size: int
    total_size: int


def scan_entries(
    base: Path,
    *,
    dirs_only: bool,
    include_hidden: bool,
    need_sizes: bool,
    sort_by_size: bool,
    follow_symlinks: bool,
    ignore: List[str],
    only: List[str],
) -> List[Entry]:
    entries: List[Entry] = []
    try:
        with os.scandir(base) as it:
            for de in it:
                if de.name in (".", ".."):
                    continue
                if not include_hidden and de.name.startswith("."):
                    continue

                p = base / de.name

                if match_any(p, de.name, ignore):
                    continue

                if only and not match_any(p, de.name, only) and not p.is_dir():
                    continue

                try:
                    st = de.stat(follow_symlinks=follow_symlinks)
                except OSError:
                    continue

                mode = st.st_mode
                is_dir = stat.S_ISDIR(mode)

                if dirs_only and not is_dir:
                    continue

                size = int(st.st_size)

                total = size
                if (need_sizes or sort_by_size) and is_dir:
                    total = get_total_size(
                        p,
                        follow_symlinks=follow_symlinks,
                        ignore=ignore,
                        only=only,
                        include_hidden=include_hidden,
                        stats=None,
                    )

                entries.append(Entry(de.name, p, mode, is_dir, size, int(total)))
    except OSError:
        return []

    entries.sort(key=(lambda e: (-e.total_size, e.name.lower())) if sort_by_size else (lambda e: e.name.lower()))
    return entries


# ------------------ tree output ------------------
def build_tree_text(
    path: Path,
    *,
    max_depth: int,
    dirs_only: bool,
    show_size: bool,
    sort_by_size: bool,
    no_color: bool,
    include_hidden: bool,
    follow_symlinks: bool,
    ignore: List[str],
    only: List[str],
) -> str:
    lines: List[str] = []
    root_st = safe_lstat(path)
    root_mode = root_st.st_mode if root_st else 0
    lines.append(colorize(str(path), root_mode, no_color))

    def _walk(cur: Path, depth: int, prefix: str) -> None:
        if max_depth != -1 and depth > max_depth:
            return

        need_sizes = show_size or sort_by_size
        ents = scan_entries(
            cur,
            dirs_only=dirs_only,
            include_hidden=include_hidden,
            need_sizes=need_sizes,
            sort_by_size=sort_by_size,
            follow_symlinks=follow_symlinks,
            ignore=ignore,
            only=only,
        )

        for idx, e in enumerate(ents):
            last = (idx == len(ents) - 1)
            branch = "└── " if last else "├── "
            next_prefix = prefix + ("    " if last else "│   ")

            label = colorize(e.name, e.mode, no_color)
            if show_size:
                label += f" [{format_size(e.total_size)}]"
            lines.append(prefix + branch + label)

            if e.is_dir:
                _walk(e.path, depth + 1, next_prefix)

    if path.is_dir():
        _walk(path, 1, "")

    return "\n".join(lines)


# ------------------ JSON output ------------------
JsonNode = Union[str, Dict[str, "JsonNode"], Dict[str, Union[str, int]]]

def build_json(
    path: Path,
    *,
    max_depth: int,
    dirs_only: bool,
    show_size: bool,
    sort_by_size: bool,
    include_hidden: bool,
    follow_symlinks: bool,
    ignore: List[str],
    only: List[str],
) -> Dict[str, JsonNode]:
    def file_value(p: Path) -> JsonNode:
        if show_size:
            st = safe_lstat(p)
            return {"type": "file", "size": int(st.st_size) if st else 0}
        return "file"

    def _walk(cur: Path, depth: int) -> Dict[str, JsonNode]:
        if max_depth != -1 and depth > max_depth:
            return {}
        need_sizes = show_size or sort_by_size
        ents = scan_entries(
            cur,
            dirs_only=dirs_only,
            include_hidden=include_hidden,
            need_sizes=need_sizes,
            sort_by_size=sort_by_size,
            follow_symlinks=follow_symlinks,
            ignore=ignore,
            only=only,
        )
        out: Dict[str, JsonNode] = {}
        for e in ents:
            if e.is_dir:
                child = _walk(e.path, depth + 1)
                out[e.name] = {"type": "dir", "size": e.total_size, "children": child} if show_size else child
            else:
                out[e.name] = file_value(e.path)
        return out

    root_name = str(path)
    if path.is_dir():
        tree = _walk(path, 1)
        if show_size:
            root_size = get_total_size(
                path,
                follow_symlinks=follow_symlinks,
                ignore=ignore,
                only=only,
                include_hidden=include_hidden,
                stats=None,
            )
            return {root_name: {"type": "dir", "size": root_size, "children": tree}}
        return {root_name: tree}

    return {root_name: file_value(path)}


# ------------------ Top-N largest files ------------------
def list_top_largest_files(
    root: Path,
    *,
    top_n: int,
    max_depth: int,
    include_hidden: bool,
    follow_symlinks: bool,
    ignore: List[str],
    only: List[str],
) -> List[Tuple[int, Path]]:
    results: List[Tuple[int, Path]] = []
    seen_dirs: Set[Tuple[int, int]] = set()

    def _walk(cur: Path, depth: int) -> None:
        if max_depth != -1 and depth > max_depth:
            return

        st = safe_lstat(cur)
        if st and stat.S_ISDIR(st.st_mode) and follow_symlinks:
            key = (int(st.st_dev), int(st.st_ino))
            if key in seen_dirs:
                return
            seen_dirs.add(key)

        try:
            with os.scandir(cur) as it:
                for de in it:
                    if de.name in (".", ".."):
                        continue
                    p = cur / de.name

                    if not include_hidden and de.name.startswith("."):
                        continue
                    if match_any(p, de.name, ignore):
                        continue
                    if only and not match_any(p, de.name, only) and not p.is_dir():
                        continue

                    try:
                        st2 = de.stat(follow_symlinks=follow_symlinks)
                    except OSError:
                        continue

                    mode = st2.st_mode
                    if stat.S_ISDIR(mode):
                        _walk(p, depth + 1)
                    else:
                        results.append((int(st2.st_size), p))
        except OSError:
            return

    if root.is_dir():
        _walk(root, 1)
    else:
        st = safe_lstat(root)
        if st:
            results.append((int(st.st_size), root))

    results.sort(key=lambda x: x[0], reverse=True)
    return results[: max(0, top_n)]

def format_top_list(items: List[Tuple[int, Path]]) -> str:
    lines = []
    for i, (sz, p) in enumerate(items, start=1):
        lines.append(f"{i:>2}. {format_size(sz):>10}  {p}")
    return "\n".join(lines) if lines else ""


# ------------------ Summary ------------------
def build_summary_text(lang: str, stats: WalkStats) -> str:
    lines = [
        t("summary_title", lang),
        f"{t('summary_files', lang)}: {stats.files}",
        f"{t('summary_dirs', lang)}: {stats.dirs}",
        f"{t('summary_total', lang)}: {format_size(stats.total_size)}",
        f"{t('summary_skipped', lang)}: {stats.skipped}",
        f"{t('summary_errors', lang)}: {stats.errors}",
    ]
    return "\n".join(lines)


# ------------------ Search + path iteration ------------------
def iter_paths(
    root: Path,
    *,
    max_depth: int,
    include_hidden: bool,
    follow_symlinks: bool,
    ignore: List[str],
) -> Iterable[Path]:
    seen_dirs: Set[Tuple[int, int]] = set()

    def _walk(cur: Path, depth: int) -> Iterable[Path]:
        st = safe_lstat(cur)
        if st is None:
            return
        yield cur

        mode = st.st_mode
        if stat.S_ISLNK(mode) and not follow_symlinks:
            return
        if not stat.S_ISDIR(mode):
            return

        if follow_symlinks:
            key = (int(st.st_dev), int(st.st_ino))
            if key in seen_dirs:
                return
            seen_dirs.add(key)

        if max_depth != -1 and depth >= max_depth:
            return

        try:
            with os.scandir(cur) as it:
                for de in it:
                    if de.name in (".", ".."):
                        continue
                    if not include_hidden and de.name.startswith("."):
                        continue
                    p = cur / de.name
                    if match_any(p, de.name, ignore):
                        continue
                    yield from _walk(p, depth + 1)
        except OSError:
            return

    if root.exists():
        yield from _walk(root, 0)

def search_paths(
    root: Path,
    *,
    mode: str,
    query: str,
    max_results: int,
    max_depth: int,
    include_hidden: bool,
    follow_symlinks: bool,
    ignore: List[str],
) -> List[Path]:
    results: List[Path] = []
    rx: Optional[re.Pattern] = None
    if mode == "regex":
        try:
            rx = re.compile(query)
        except re.error:
            rx = None

    for p in iter_paths(root, max_depth=max_depth, include_hidden=include_hidden, follow_symlinks=follow_symlinks, ignore=ignore):
        name = p.name
        ok = False
        if mode == "glob":
            ok = fnmatch.fnmatchcase(name, query) or fnmatch.fnmatchcase(str(p.as_posix()), query)
        elif mode == "contains":
            q = query.lower()
            ok = q in name.lower() or q in str(p).lower()
        elif mode == "regex" and rx is not None:
            ok = bool(rx.search(name) or rx.search(str(p)))
        if ok:
            results.append(p)
            if max_results > 0 and len(results) >= max_results:
                break
    return results


# ------------------ Empty folders ------------------
def find_empty_folders(
    root: Path,
    *,
    max_depth: int,
    include_hidden: bool,
    follow_symlinks: bool,
    ignore: List[str],
) -> List[Path]:
    empties: List[Path] = []
    for p in iter_paths(root, max_depth=max_depth, include_hidden=include_hidden, follow_symlinks=follow_symlinks, ignore=ignore):
        if not p.is_dir():
            continue
        try:
            has_any = False
            with os.scandir(p) as it:
                for de in it:
                    if de.name in (".", ".."):
                        continue
                    if not include_hidden and de.name.startswith("."):
                        continue
                    if match_any(p / de.name, de.name, ignore):
                        continue
                    has_any = True
                    break
            if not has_any:
                empties.append(p)
        except OSError:
            continue
    return empties


# ------------------ Duplicate files (hash) ------------------
def hash_file(path: Path, algo: str) -> Optional[str]:
    h = hashlib.md5() if algo == "md5" else hashlib.sha256()
    try:
        with path.open("rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None

def find_duplicates(
    root: Path,
    *,
    max_depth: int,
    include_hidden: bool,
    follow_symlinks: bool,
    ignore: List[str],
    min_size: int,
    algo: str,
) -> Dict[str, List[Path]]:
    size_map: Dict[int, List[Path]] = {}
    for p in iter_paths(root, max_depth=max_depth, include_hidden=include_hidden, follow_symlinks=follow_symlinks, ignore=ignore):
        if p.is_dir():
            continue
        try:
            st = p.stat()
        except OSError:
            continue
        if int(st.st_size) < min_size:
            continue
        size_map.setdefault(int(st.st_size), []).append(p)

    dupes: Dict[str, List[Path]] = {}
    for sz, paths in size_map.items():
        if len(paths) < 2:
            continue
        for p in paths:
            digest = hash_file(p, algo)
            if digest:
                dupes.setdefault(f"{algo}:{digest}:{sz}", []).append(p)

    return {k: v for k, v in dupes.items() if len(v) > 1}

def format_dupes(lang: str, dupes: Dict[str, List[Path]]) -> str:
    lines: List[str] = []
    for k, paths in sorted(dupes.items(), key=lambda kv: len(kv[1]), reverse=True):
        _, digest, sz = k.split(":", 2)
        lines.append(f"\n== {format_size(int(sz))}  {digest}  ({len(paths)} {t('label_files_word', lang)}) ==")
        for p in paths:
            lines.append(f"  - {p}")
    return "\n".join(lines).strip()


# ------------------ Trash (safe move) ------------------
def move_to_trash(base_root: Path, items: List[Path]) -> Tuple[int, int, Path]:
    """
    Moves files or folders into <base_root>/.TreeExplorerTrash/<relative_path>.
    Returns (moved, skipped, trash_dir).
    """
    base = base_root if base_root.is_dir() else base_root.parent
    trash_dir = base / ".TreeExplorerTrash"
    moved = 0
    skipped = 0

    # Move deeper paths first (helps for directories)
    items_sorted = sorted(items, key=lambda p: len(str(p)), reverse=True)

    for item in items_sorted:
        try:
            rel = item.relative_to(base)
        except Exception:
            rel = Path(item.name)

        dest = trash_dir / rel
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                stem = dest.stem
                suf = dest.suffix
                i = 1
                while True:
                    cand = dest.with_name(f"{stem}__{i}{suf}")
                    if not cand.exists():
                        dest = cand
                        break
                    i += 1
            item.rename(dest)
            moved += 1
        except Exception:
            skipped += 1

    return moved, skipped, trash_dir

def collect_matching_items(
    root: Path,
    *,
    pattern: str,
    max_depth: int,
    include_hidden: bool,
    follow_symlinks: bool,
    ignore: List[str],
) -> List[Path]:
    out: List[Path] = []
    for p in iter_paths(root, max_depth=max_depth, include_hidden=include_hidden, follow_symlinks=follow_symlinks, ignore=ignore):
        if p == root:
            continue
        if fnmatch.fnmatchcase(p.name, pattern) or fnmatch.fnmatchcase(str(p.as_posix()), pattern):
            out.append(p)
    return out


# ------------------ Folder sizes report (Top-N immediate children) ------------------
def folder_sizes_report(
    root: Path,
    *,
    top_n: int,
    include_hidden: bool,
    follow_symlinks: bool,
    ignore: List[str],
) -> List[Tuple[int, Path]]:
    items: List[Tuple[int, Path]] = []
    if not root.is_dir():
        st = safe_lstat(root)
        if st:
            return [(int(st.st_size), root)]
        return []

    try:
        with os.scandir(root) as it:
            for de in it:
                if de.name in (".", ".."):
                    continue
                if not include_hidden and de.name.startswith("."):
                    continue
                p = root / de.name
                if match_any(p, de.name, ignore):
                    continue
                try:
                    st = de.stat(follow_symlinks=follow_symlinks)
                except OSError:
                    continue
                if stat.S_ISDIR(st.st_mode):
                    sz = get_total_size(p, follow_symlinks=follow_symlinks, ignore=ignore, only=[], include_hidden=include_hidden, stats=None)
                else:
                    sz = int(st.st_size)
                items.append((int(sz), p))
    except OSError:
        return []

    items.sort(key=lambda x: x[0], reverse=True)
    return items[: max(0, top_n)]

def format_sizes_report(items: List[Tuple[int, Path]]) -> str:
    total = sum(sz for sz, _ in items) or 1
    lines: List[str] = []
    for i, (sz, p) in enumerate(items, start=1):
        pct = (sz * 100.0) / total
        lines.append(f"{i:>2}. {format_size(sz):>10}  {pct:>6.2f}%  {p}")
    return "\n".join(lines) if lines else ""


# ------------------ Recent files (mtime) ------------------
def list_recent_files(
    root: Path,
    *,
    days: int,
    max_results: int,
    max_depth: int,
    include_hidden: bool,
    follow_symlinks: bool,
    ignore: List[str],
) -> List[Tuple[float, Path, int]]:
    cutoff = time.time() - (max(0, days) * 86400)
    items: List[Tuple[float, Path, int]] = []
    for p in iter_paths(root, max_depth=max_depth, include_hidden=include_hidden, follow_symlinks=follow_symlinks, ignore=ignore):
        if p.is_dir():
            continue
        try:
            st = p.stat()
        except OSError:
            continue
        if st.st_mtime >= cutoff:
            items.append((float(st.st_mtime), p, int(st.st_size)))
    items.sort(key=lambda x: x[0], reverse=True)
    if max_results > 0:
        items = items[:max_results]
    return items

def format_recent(items: List[Tuple[float, Path, int]]) -> str:
    lines: List[str] = []
    for i, (mt, p, sz) in enumerate(items, start=1):
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mt))
        lines.append(f"{i:>2}. {ts}  {format_size(sz):>10}  {p}")
    return "\n".join(lines) if lines else ""


# ------------------ Clean duplicates (keep newest, trash others) ------------------
def clean_duplicates_keep_newest(
    dupes: Dict[str, List[Path]],
    *,
    base_root: Path,
) -> Tuple[List[Path], List[Path]]:
    """Returns (kept, to_trash)."""
    kept: List[Path] = []
    trash: List[Path] = []
    for _, paths in dupes.items():
        # choose newest by mtime; fallback to first
        best = None
        best_mtime = -1.0
        for p in paths:
            try:
                mt = p.stat().st_mtime
            except OSError:
                mt = 0.0
            if mt > best_mtime:
                best_mtime = mt
                best = p
        if best is None:
            best = paths[0]
        kept.append(best)
        for p in paths:
            if p != best:
                trash.append(p)
    # de-duplicate trash list
    uniq_trash = []
    seen = set()
    for p in trash:
        sp = str(p)
        if sp not in seen:
            seen.add(sp)
            uniq_trash.append(p)
    return kept, uniq_trash


# ------------------ Termux install helpers ------------------
def termux_prefix() -> Optional[Path]:
    p = os.environ.get("PREFIX")
    if p:
        return Path(p)
    guess = Path("/data/data/com.termux/files/usr")
    return guess if guess.exists() else None


# ------------------ Prompts (localized) ------------------
def prompt_path(lang: str, default: Path) -> Path:
    print(t("pick_path", lang))
    print("  " + t("path_1", lang))
    print("  " + t("path_2", lang))
    print("  " + t("path_3", lang))
    print("  " + t("path_4", lang))
    choice = input(t("choice_1_4", lang)).strip() or "1"
    if choice == "2":
        return Path(os.environ.get("HOME", str(Path.home())))
    if choice == "3":
        return Path("/sdcard")
    if choice == "4":
        p = input(t("enter_path", lang)).strip()
        return Path(p).expanduser() if p else default
    return default

def prompt_int(lang: str, default: int, key: str = "prompt_depth_default") -> int:
    val = input(t(key, lang, default=default)).strip()
    if not val:
        return default
    try:
        return int(val)
    except ValueError:
        return default

def yesno(lang: str, label_key: str, default: bool) -> bool:
    label = t(label_key, lang)
    suffix = t("yes_no", lang) if default else t("yes_no_default_no", lang)
    val = input(f"{label} {suffix}").strip().lower()
    if not val:
        return default
    yes_set = {"y", "yes", "1", "true", "ν", "ναι"}
    no_set = {"n", "no", "0", "false", "ο", "όχι", "οχι"}
    if val in yes_set:
        return True
    if val in no_set:
        return False
    return default

def prompt_text(lang: str, key: str, default: str = "") -> str:
    s = input(f"{t(key, lang)}: ").strip()
    return s if s else default


def choose_language(lang: str) -> str:
    c = input(t("prompt_action", lang)).strip()
    if c == "2":
        new_lang = "el"
    elif c == "1":
        new_lang = "en"
    else:
        print(t("unknown_choice", lang))
        return lang

    label = "Ελληνικά" if new_lang == "el" else "English"
    return new_lang


# ------------------ Export helper ------------------
def export_text(lang: str, export_path: str, content: str) -> None:
    if not export_path.strip():
        return
    p = Path(export_path).expanduser()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    except Exception as e:
        print(t("err_export", lang, path=p, err=e), file=sys.stderr)


# ------------------ Installer (no root) ------------------
def install_self(lang: str, alias: str = "supertree") -> int:
    pref = termux_prefix()
    if not pref:
        print(t("install_err_prefix", lang), file=sys.stderr)
        return 1

    bin_dir = pref / "bin"
    try:
        bin_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(t("install_err_bin", lang, path=bin_dir, err=e), file=sys.stderr)
        return 1

    src = Path(__file__).resolve()
    dst = bin_dir / alias

    try:
        dst.write_bytes(src.read_bytes())
        mode = dst.stat().st_mode
        dst.chmod(mode | 0o111)
    except Exception as e:
        print(t("install_err_failed", lang, err=e), file=sys.stderr)
        return 1

    print(t("install_ok", lang, alias=alias))
    return 0


# ------------------ Explorer mode ------------------
def file_info_text(lang: str, p: Path) -> str:
    st = safe_lstat(p)
    if not st:
        return f"{p} {t('info_unreadable', lang)}"
    mode = st.st_mode
    kind_key = 'kind_dir' if stat.S_ISDIR(mode) else 'kind_symlink' if stat.S_ISLNK(mode) else 'kind_file'
    kind = t(kind_key, lang)
    size = int(st.st_size)
    return (
        f"{p}\n"
        f"  {t('info_type', lang)}: {kind}\n"
        f"  {t('info_size', lang)}: {format_size(size)}\n"
        f"  {t('info_perms', lang)}: {oct(mode & 0o777)}"
    )

def preview_text_file(p: Path, lines: int) -> str:
    try:
        out_lines: List[str] = []
        with p.open("r", encoding="utf-8", errors="replace") as f:
            for _ in range(max(1, lines)):
                line = f.readline()
                if not line:
                    break
                out_lines.append(line.rstrip("\n"))
        return "\n".join(out_lines)
    except Exception:
        return ""

def explorer_mode(lang: str) -> None:
    print(t("explorer_title", lang))
    cur = prompt_path(lang, Path(".")).expanduser()
            ents.sort(key=lambda d: (0 if d.is_dir(follow_symlinks=False) else 1, d.name.lower()))
        except Exception:
            print(t("err_open", lang))
            return

        for i, de in enumerate(ents, start=1):
            p = cur / de.name
            st = safe_lstat(p)
            mode = st.st_mode if st else 0
            label = colorize(de.name, mode, False)
            suffix = "/" if de.is_dir(follow_symlinks=False) else ""
            print(f"{i:>2}) {label}{suffix}")

        cmd = input(t("explorer_pick", lang)).strip().lower()
        if cmd in ("q", "quit", "exit"):
            return
        if cmd in ("u", ".."):
            parent = cur.parent
            if parent != cur:
                cur = parent
            continue
        if cmd == "i":
            pick = input(t('prompt_index', lang)).strip()
            if not pick.isdigit():
                continue
            idx = int(pick) - 1
            if 0 <= idx < len(ents):
                p = cur / ents[idx].name
                print(file_info_text(lang, p))
            continue
        if cmd == "p":
            pick = input(t('prompt_index', lang)).strip()
            if not pick.isdigit():
                continue
            idx = int(pick) - 1
            if 0 <= idx < len(ents):
                p = cur / ents[idx].name
                if p.is_dir():
                    print(t("explorer_not_dir", lang))
                    continue
                try:
                    ln_raw = input(t("explorer_preview_lines", lang)).strip()
                    ln = int(ln_raw) if ln_raw else 30
                except ValueError:
                    ln = 30
                txt = preview_text_file(p, ln)
                if not txt:
                    print(t("explorer_preview_fail", lang))
                else:
                    print("\n" + txt)
            continue

        if cmd.isdigit():
            idx = int(cmd) - 1
            if 0 <= idx < len(ents):
                p = cur / ents[idx].name
                if p.is_dir():
                    cur = p
                else:
                    print(file_info_text(lang, p))
            continue


# ------------------ Menu actions ------------------
def run_quick(lang: str) -> None:
    target = prompt_path(lang, Path("."))
    if not target.exists():
        print(t("err_path_missing", lang, path=target))
        return
    text = build_tree_text(
        target,
        max_depth=2,
        dirs_only=False,
        show_size=True,
        sort_by_size=True,
        no_color=False,
        include_hidden=True,
        follow_symlinks=False,
        ignore=[],
        only=[],
    )
    print(text)
    export_path = prompt_text(lang, "prompt_export", "")
    export_text(lang, export_path, text)

def run_custom(lang: str) -> None:
    target = prompt_path(lang, Path("."))
    if not target.exists():
        print(t("err_path_missing", lang, path=target))
        return

    show_size = yesno(lang, "prompt_sizes", True)
    sort_size = yesno(lang, "prompt_sort", False)
    hide_dot = yesno(lang, "prompt_hide_dot", False)
    include_hidden = not hide_dot
    depth = prompt_int(lang, -1)
    follow = yesno(lang, "prompt_follow", False)

    ignore = normalize_patterns(prompt_text(lang, "prompt_ignore", ""))
    only = normalize_patterns(prompt_text(lang, "prompt_only", ""))

    top_n = 0
    try:
        top_n = int(prompt_text(lang, "prompt_top", "0") or "0")
    except ValueError:
        top_n = 0

    show_summary = yesno(lang, "prompt_summary", True)
    export_path = prompt_text(lang, "prompt_export", "")
    use_rich = yesno(lang, "prompt_rich", False)

    if top_n > 0:
        items = list_top_largest_files(
            target,
            top_n=top_n,
            max_depth=depth,
            include_hidden=include_hidden,
            follow_symlinks=follow,
            ignore=ignore,
            only=only,
        )
        out = format_top_list(items) or t('placeholder_empty', lang)
        stats = WalkStats() if show_summary else None
        if stats is not None:
            _ = get_total_size(target, follow_symlinks=follow, ignore=ignore, only=only, include_hidden=include_hidden, stats=stats)
            out = (out + "\n" + build_summary_text(lang, stats)).strip()
        print(out)
        export_text(lang, export_path, out)
        return

    stats = WalkStats() if show_summary else None
    if stats is not None:
        _ = get_total_size(target, follow_symlinks=follow, ignore=ignore, only=only, include_hidden=include_hidden, stats=stats)

    if use_rich:
        ok = ensure_pip_package("rich", "rich")
        if ok:
            from rich.console import Console
            from rich.tree import Tree
            from rich.text import Text

            console = Console()

            def rich_label(e: Entry) -> Text:
                txt = Text(e.name)
                if stat.S_ISDIR(e.mode):
                    txt.stylize("bold blue")
                elif stat.S_ISLNK(e.mode):
                    txt.stylize("bold cyan")
                elif stat.S_ISREG(e.mode) and (e.mode & 0o111):
                    txt.stylize("bold green")
                if show_size:
                    txt.append(f" [{format_size(e.total_size)}]")
                return txt

            def build_rich_tree(cur: Path, d: int, node: Tree) -> None:
                if depth != -1 and d > depth:
                    return
                need_sizes = show_size or sort_size
                ents = scan_entries(
                    cur,
                    dirs_only=False,
                    include_hidden=include_hidden,
                    need_sizes=need_sizes,
                    sort_by_size=sort_size,
                    follow_symlinks=follow,
                    ignore=ignore,
                    only=only,
                )
                for e in ents:
                    child = node.add(rich_label(e))
                    if e.is_dir:
                        build_rich_tree(e.path, d + 1, child)

            root = Tree(str(target))
            if target.is_dir():
                build_rich_tree(target, 1, root)
            console.print(root)

            if stats is not None:
                print(build_summary_text(lang, stats))

            if export_path:
                text = build_tree_text(
                    target,
                    max_depth=depth,
                    dirs_only=False,
                    show_size=show_size,
                    sort_by_size=sort_size,
                    no_color=True,
                    include_hidden=include_hidden,
                    follow_symlinks=follow,
                    ignore=ignore,
                    only=only,
                )
                if stats is not None:
                    text = (text + "\n" + build_summary_text(lang, stats)).strip()
                export_text(lang, export_path, text)
            return

        print(t("rich_fallback", lang), file=sys.stderr)

    text = build_tree_text(
        target,
        max_depth=depth,
        dirs_only=False,
        show_size=show_size,
        sort_by_size=sort_size,
        no_color=False,
        include_hidden=include_hidden,
        follow_symlinks=follow,
        ignore=ignore,
        only=only,
    )
    if stats is not None:
        text = (text + "\n" + build_summary_text(lang, stats)).strip()
    print(text)
    export_text(lang, export_path, text)

def run_only_folders(lang: str) -> None:
    target = prompt_path(lang, Path("."))
    if not target.exists():
        print(t("err_path_missing", lang, path=target))
        return

    depth = prompt_int(lang, 2)
    show_size = yesno(lang, "prompt_sizes", False)
    hide_dot = yesno(lang, "prompt_hide_dot", False)
    include_hidden = not hide_dot
    ignore = normalize_patterns(prompt_text(lang, "prompt_ignore", ""))
    only = normalize_patterns(prompt_text(lang, "prompt_only", ""))

    text = build_tree_text(
        target,
        max_depth=depth,
        dirs_only=True,
        show_size=show_size,
        sort_by_size=False,
        no_color=False,
        include_hidden=include_hidden,
        follow_symlinks=False,
        ignore=ignore,
        only=only,
    )
    print(text)
    export_path = prompt_text(lang, "prompt_export", "")
    export_text(lang, export_path, text)

def run_json(lang: str) -> None:
    target = prompt_path(lang, Path("."))
    if not target.exists():
        print(t("err_path_missing", lang, path=target))
        return

    show_size = yesno(lang, "prompt_sizes", True)
    hide_dot = yesno(lang, "prompt_hide_dot", False)
    include_hidden = not hide_dot
    depth = prompt_int(lang, 3)
    follow = yesno(lang, "prompt_follow", False)
    ignore = normalize_patterns(prompt_text(lang, "prompt_ignore", ""))
    only = normalize_patterns(prompt_text(lang, "prompt_only", ""))

    obj = build_json(
        target,
        max_depth=depth,
        dirs_only=False,
        show_size=show_size,
        sort_by_size=False,
        include_hidden=include_hidden,
        follow_symlinks=follow,
        ignore=ignore,
        only=only,
    )
    out = _json.dumps(obj, ensure_ascii=False, indent=2)
    print(out)
    export_path = prompt_text(lang, "prompt_export", "")
    export_text(lang, export_path, out)

def run_search(lang: str) -> None:
    print(t("search_title", lang))
    root = prompt_path(lang, Path("."))
    if not root.exists():
        print(t("err_path_missing", lang, path=root))
        return

    print(t("search_type", lang))
    c = input(t("prompt_action", lang)).strip()
    mode = "glob" if c == "1" else "contains" if c == "2" else "regex" if c == "3" else "glob"
    query = input(t("search_query", lang)).strip()
    if not query:
        return

    try:
        max_results = int(input(t("search_max", lang)).strip() or "200")
    except ValueError:
        max_results = 200
    if max_results < 0:
        max_results = 0

    depth = prompt_int(lang, 8)
    hide_dot = yesno(lang, "prompt_hide_dot", False)
    include_hidden = not hide_dot
    follow = yesno(lang, "prompt_follow", False)
    ignore = normalize_patterns(prompt_text(lang, "prompt_ignore", ""))

    results = search_paths(root, mode=mode, query=query, max_results=max_results, max_depth=depth, include_hidden=include_hidden, follow_symlinks=follow, ignore=ignore)

    print(t("search_done", lang, n=len(results)))
    if not results:
        print(t("search_none", lang))
        return

    out = "\n".join(str(p) for p in results)
    print(out)
    export_path = prompt_text(lang, "prompt_export", "")
    export_text(lang, export_path, out)

def run_top(lang: str) -> None:
    root = prompt_path(lang, Path("."))
    if not root.exists():
        print(t("err_path_missing", lang, path=root))
        return
    try:
        n = int(prompt_text(lang, "prompt_top", "20") or "20")
    except ValueError:
        n = 20
    depth = prompt_int(lang, 8)
    hide_dot = yesno(lang, "prompt_hide_dot", False)
    include_hidden = not hide_dot
    follow = yesno(lang, "prompt_follow", False)
    ignore = normalize_patterns(prompt_text(lang, "prompt_ignore", ""))
    only = normalize_patterns(prompt_text(lang, "prompt_only", ""))

    items = list_top_largest_files(root, top_n=max(1, n), max_depth=depth, include_hidden=include_hidden, follow_symlinks=follow, ignore=ignore, only=only)
    out = format_top_list(items) or t('placeholder_empty', lang)
    print(out)
    export_path = prompt_text(lang, "prompt_export", "")
    export_text(lang, export_path, out)

def run_empty_dirs(lang: str) -> None:
    print(t("empty_title", lang))
    root = prompt_path(lang, Path("."))
    if not root.exists():
        print(t("err_path_missing", lang, path=root))
        return
    depth = prompt_int(lang, 8)
    hide_dot = yesno(lang, "prompt_hide_dot", False)
    include_hidden = not hide_dot
    follow = yesno(lang, "prompt_follow", False)
    ignore = normalize_patterns(prompt_text(lang, "prompt_ignore", ""))

    empties = find_empty_folders(root, max_depth=depth, include_hidden=include_hidden, follow_symlinks=follow, ignore=ignore)
    print(t("empty_found", lang, n=len(empties)))
    out = "\n".join(str(p) for p in empties) if empties else ""
    if out:
        print(out)
    export_path = prompt_text(lang, "prompt_export", "")
    export_text(lang, export_path, out)

def run_dupes(lang: str) -> None:
    print(t("dupes_title", lang))
    root = prompt_path(lang, Path("."))
    if not root.exists():
        print(t("err_path_missing", lang, path=root))
        return
    depth = prompt_int(lang, 8)
    hide_dot = yesno(lang, "prompt_hide_dot", False)
    include_hidden = not hide_dot
    follow = yesno(lang, "prompt_follow", False)
    ignore = normalize_patterns(prompt_text(lang, "prompt_ignore", ""))

    try:
        min_size = int(prompt_text(lang, "prompt_min_size", "1") or "1")
    except ValueError:
        min_size = 1
    algo_choice = input(t("dupes_algo", lang)).strip() or "2"
    algo = "md5" if algo_choice == "1" else "sha256"

    dupes = find_duplicates(root, max_depth=depth, include_hidden=include_hidden, follow_symlinks=follow, ignore=ignore, min_size=max(1, min_size), algo=algo)
    print(t("dupes_groups", lang, n=len(dupes)))
    if not dupes:
        print(t("dupes_none", lang))
        return
    out = format_dupes(lang, dupes)
    print(out)
    export_path = prompt_text(lang, "prompt_export", "")
    export_text(lang, export_path, out)

def run_trash_pattern(lang: str) -> None:
    print(t("trash_title", lang))
    root = prompt_path(lang, Path("."))
    if not root.exists():
        print(t("err_path_missing", lang, path=root))
        return
    pattern = input(t("trash_pattern", lang)).strip()
    if not pattern:
        return
    depth = prompt_int(lang, 12)
    hide_dot = yesno(lang, "prompt_hide_dot", False)
    include_hidden = not hide_dot
    follow = yesno(lang, "prompt_follow", False)
    ignore = normalize_patterns(prompt_text(lang, "prompt_ignore", ""))

    items = collect_matching_items(root, pattern=pattern, max_depth=depth, include_hidden=include_hidden, follow_symlinks=follow, ignore=ignore)
    trash_dir_preview = (root if root.is_dir() else root.parent) / ".TreeExplorerTrash"
    print(t("trash_confirm_msg", lang, trash=trash_dir_preview))
    print(t("trash_found", lang, n=len(items)))
    if not items:
        print(t("trash_none", lang))
        return

    preview = "\n".join(f" - {p}" for p in items[:20])
    print(preview + ("\n..." if len(items) > 20 else ""))

    confirm = input(t("prompt_confirm", lang)).strip()
    if confirm != "YES":
        return

    moved, skipped, _trash_dir = move_to_trash(root, items)
    print(t("trash_done", lang, n=moved))
    if skipped:
        print(t("trash_skip", lang, n=skipped))

def run_sizes_report(lang: str) -> None:
    print(t("sizes_title", lang))
    root = prompt_path(lang, Path("."))
    if not root.exists():
        print(t("err_path_missing", lang, path=root))
        return
    hide_dot = yesno(lang, "prompt_hide_dot", False)
    include_hidden = not hide_dot
    follow = yesno(lang, "prompt_follow", False)
    ignore = normalize_patterns(prompt_text(lang, "prompt_ignore", ""))
    try:
        top_n = int(prompt_text(lang, "prompt_top", "20") or "20")
    except ValueError:
        top_n = 20

    items = folder_sizes_report(root, top_n=max(1, top_n), include_hidden=include_hidden, follow_symlinks=follow, ignore=ignore)
    out = format_sizes_report(items) or t('placeholder_empty', lang)
    print(out)
    export_path = prompt_text(lang, "prompt_export", "")
    export_text(lang, export_path, out)

def run_recent(lang: str) -> None:
    print(t("recent_title", lang))
    root = prompt_path(lang, Path("."))
    if not root.exists():
        print(t("err_path_missing", lang, path=root))
        return
    try:
        days = int(prompt_text(lang, "prompt_days", "7") or "7")
    except ValueError:
        days = 7
    try:
        top_n = int(prompt_text(lang, "prompt_top", "200") or "200")
    except ValueError:
        top_n = 200
    depth = prompt_int(lang, 10)
    hide_dot = yesno(lang, "prompt_hide_dot", False)
    include_hidden = not hide_dot
    follow = yesno(lang, "prompt_follow", False)
    ignore = normalize_patterns(prompt_text(lang, "prompt_ignore", ""))

    items = list_recent_files(root, days=max(0, days), max_results=max(0, top_n), max_depth=depth, include_hidden=include_hidden, follow_symlinks=follow, ignore=ignore)
    out = format_recent(items) or t('placeholder_empty', lang)
    print(out)
    export_path = prompt_text(lang, "prompt_export", "")
    export_text(lang, export_path, out)

def run_clean_dupes(lang: str) -> None:
    print(t("clean_dupes_title", lang))
    root = prompt_path(lang, Path("."))
    if not root.exists():
        print(t("err_path_missing", lang, path=root))
        return
    depth = prompt_int(lang, 12)
    hide_dot = yesno(lang, "prompt_hide_dot", False)
    include_hidden = not hide_dot
    follow = yesno(lang, "prompt_follow", False)
    ignore = normalize_patterns(prompt_text(lang, "prompt_ignore", ""))
    try:
        min_size = int(prompt_text(lang, "prompt_min_size", "1") or "1")
    except ValueError:
        min_size = 1

    dupes = find_duplicates(root, max_depth=depth, include_hidden=include_hidden, follow_symlinks=follow, ignore=ignore, min_size=max(1, min_size), algo="sha256")
    if not dupes:
        print(t("dupes_none", lang))
        return

    kept, to_trash = clean_duplicates_keep_newest(dupes, base_root=root)
    print(f"{t('label_keep', lang)}: {len(kept)}")
    print(f"{t('label_trash', lang)}: {len(to_trash)}")
    preview = "\n".join(f" - {p}" for p in to_trash[:20])
    print(preview + ("\n..." if len(to_trash) > 20 else ""))

    trash_dir_preview = (root if root.is_dir() else root.parent) / ".TreeExplorerTrash"
    print(t("trash_confirm_msg", lang, trash=trash_dir_preview))
    confirm = input(t("prompt_confirm", lang)).strip()
    if confirm != "YES":
        return

    moved, skipped, _trash_dir = move_to_trash(root, to_trash)
    print(t("trash_done", lang, n=moved))
    if skipped:
        print(t("trash_skip", lang, n=skipped))

def run_remove_empty(lang: str) -> None:
    print(t("remove_empty_title", lang))
    root = prompt_path(lang, Path("."))
    if not root.exists():
        print(t("err_path_missing", lang, path=root))
        return
    depth = prompt_int(lang, 12)
    hide_dot = yesno(lang, "prompt_hide_dot", False)
    include_hidden = not hide_dot
    follow = yesno(lang, "prompt_follow", False)
    ignore = normalize_patterns(prompt_text(lang, "prompt_ignore", ""))

    empties = find_empty_folders(root, max_depth=depth, include_hidden=include_hidden, follow_symlinks=follow, ignore=ignore)
    # never move root itself
    empties = [p for p in empties if p != root]
    print(t("empty_found", lang, n=len(empties)))
    if not empties:
        return

    preview = "\n".join(f" - {p}" for p in empties[:20])
    print(preview + ("\n..." if len(empties) > 20 else ""))

    trash_dir_preview = (root if root.is_dir() else root.parent) / ".TreeExplorerTrash"
    print(t("trash_confirm_msg", lang, trash=trash_dir_preview))
    confirm = input(t("prompt_confirm", lang)).strip()
    if confirm != "YES":
        return

    moved, skipped, _trash_dir = move_to_trash(root, empties)
    print(t("trash_done", lang, n=moved))
    if skipped:
        print(t("trash_skip", lang, n=skipped))


# ------------------ Menu loop ------------------
def menu_loop(start_lang: str) -> int:
    lang = start_lang if start_lang in LANGS else "en"

    while True:
        print(t("menu_title", lang))
        # Required original structure (1-7)
        print(t("menu_1", lang))
        print(t("menu_2", lang))
        print(t("menu_3", lang))
        print(t("menu_4", lang))
        print(t("menu_5", lang))
        print(t("menu_6", lang))
        print(t("menu_7", lang))
        # Extras
        print(t("menu_8", lang))
        print(t("menu_9", lang))
        print(t("menu_10", lang))
        print(t("menu_11", lang))
        print(t("menu_12", lang))
        print(t("menu_13", lang))
        print(t("menu_14", lang))
        print(t("menu_15", lang))
        print(t("menu_16", lang))
        print(t("menu_17", lang))
        print(t("menu_0", lang))

        c = input(t("prompt_action", lang)).strip()

        if c == "0":
            return 0
        if c == "1":
            run_quick(lang); continue
        if c == "2":
            run_custom(lang); continue
        if c == "3":
            run_only_folders(lang); continue
        if c == "4":
            run_json(lang); continue
        if c == "5":
            install_self(lang, "supertree"); continue
        if c == "6":
            print(t("help_title", lang)); print(t("help_body", lang)); continue
        if c == "7":
            lang = choose_language(lang); continue
        if c == "8":
            explorer_mode(lang); continue
        if c == "9":
            run_search(lang); continue
        if c == "10":
            run_top(lang); continue
        if c == "11":
            run_empty_dirs(lang); continue
        if c == "12":
            run_dupes(lang); continue
        if c == "13":
            run_trash_pattern(lang); continue
        if c == "14":
            run_sizes_report(lang); continue
        if c == "15":
            run_recent(lang); continue
        if c == "16":
            run_clean_dupes(lang); continue
        if c == "17":
            run_remove_empty(lang); continue

        print(t("unknown_choice", lang))


# ------------------ CLI entry ------------------
def main(argv: Optional[List[str]] = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]

    if not argv:
        return menu_loop("en")

    parser = argparse.ArgumentParser(
        prog="tree_explorer",
        add_help=False,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("path", nargs="?", default=".", help="Path to display (default: current directory)")
    parser.add_argument("--lang", default="en", help="Language: en or el")
    parser.add_argument("--menu", action="store_true", help="Open interactive menu")

    # classic tree flags
    parser.add_argument("-L", dest="max_depth", type=int, default=-1, help="Limit recursion depth (-1 = unlimited)")
    parser.add_argument("-S", dest="sort_by_size", action="store_true", help="Sort entries by total size (largest first)")
    parser.add_argument("--dirs-only", action="store_true", help="Show only directories")
    parser.add_argument("--size", action="store_true", help="Show file sizes (and directory total sizes)")
    parser.add_argument("--json", action="store_true", help="Output as valid JSON")
    parser.add_argument("--summary", action="store_true", help="Show totals summary")
    parser.add_argument("--top", type=int, default=0, help="Top-N (used by several modes)")
    parser.add_argument("--export", default="", help="Export output to file")
    parser.add_argument("--follow-symlinks", action="store_true", help="Follow symlinked directories (unsafe)")
    parser.add_argument("--ignore", action="append", default=[], help="Ignore glob pattern (repeatable)")
    parser.add_argument("--only", action="append", default=[], help="Only include glob pattern (repeatable)")

    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    parser.add_argument("--hidden", dest="include_hidden", action="store_true", default=True, help="Include dotfiles (default: included)")
    parser.add_argument("--no-hidden", dest="include_hidden", action="store_false", help="Exclude dotfiles")
    parser.add_argument("--rich", action="store_true", help="Use Rich for nicer output (auto-installs if missing)")

    # extra CLI actions (without menu)
    parser.add_argument("--search", default="", help="Search query (use with --search-mode glob|contains|regex)")
    parser.add_argument("--search-mode", default="glob", choices=["glob", "contains", "regex"], help="Search mode")
    parser.add_argument("--search-max", type=int, default=200, help="Max search results (0 = unlimited)")
    parser.add_argument("--empty-dirs", action="store_true", help="Find empty folders under path")
    parser.add_argument("--dupes", action="store_true", help="Find duplicate files under path")
    parser.add_argument("--min-size", type=int, default=1, help="Min size bytes for --dupes / --clean-dupes")
    parser.add_argument("--hash", dest="hash_algo", default="sha256", choices=["md5", "sha256"], help="Hash algo for --dupes")
    parser.add_argument("--trash", default="", help="Trash items matching glob pattern (safe move)")
    parser.add_argument("--folder-sizes", action="store_true", help="Folder sizes report (Top-N immediate children)")
    parser.add_argument("--recent", type=int, default=-1, help="List files modified within last N days")
    parser.add_argument("--clean-dupes", action="store_true", help="Trash duplicates (keep newest)")
    parser.add_argument("--remove-empty", action="store_true", help="Trash empty folders")

    # install/help
    parser.add_argument("--install", action="store_true", help="Install as 'supertree' into $PREFIX/bin (no root)")
    parser.add_argument("--alias", default="supertree", help="Name to install as (used with --install)")
    parser.add_argument("-h", "--help", action="store_true", help="Show help")

    args = parser.parse_args(argv)
    lang = args.lang if args.lang in LANGS else "en"

    if args.help:
        print(t("help_title", lang))
        print(t("help_body", lang))
        return 0

    if args.install:
        return install_self(lang, args.alias)

    if args.menu:
        return menu_loop(lang)

    root = Path(args.path).expanduser()
    if not root.exists():
        print(t("err_path_missing", lang, path=root), file=sys.stderr)
        return 1

    ignore = list(args.ignore or [])
    only = list(args.only or [])

    # Search
    if args.search:
        results = search_paths(
            root,
            mode=args.search_mode,
            query=args.search,
            max_results=max(0, args.search_max),
            max_depth=args.max_depth if args.max_depth != -1 else 999999,
            include_hidden=args.include_hidden,
            follow_symlinks=args.follow_symlinks,
            ignore=ignore,
        )
        out = "\n".join(str(p) for p in results) if results else ""
        print(out if out else t("search_none", lang))
        export_text(lang, args.export, out)
        return 0

    # Empty dirs list
    if args.empty_dirs:
        empties = find_empty_folders(
            root,
            max_depth=args.max_depth if args.max_depth != -1 else 999999,
            include_hidden=args.include_hidden,
            follow_symlinks=args.follow_symlinks,
            ignore=ignore,
        )
        out = "\n".join(str(p) for p in empties) if empties else ""
        print(out if out else t('placeholder_none', lang))
        export_text(lang, args.export, out)
        return 0

    # Duplicates list
    if args.dupes:
        dupes = find_duplicates(
            root,
            max_depth=args.max_depth if args.max_depth != -1 else 999999,
            include_hidden=args.include_hidden,
            follow_symlinks=args.follow_symlinks,
            ignore=ignore,
            min_size=max(1, args.min_size),
            algo=args.hash_algo,
        )
        out = format_dupes(lang, dupes) if dupes else ""
        print(out if out else t("dupes_none", lang))
        export_text(lang, args.export, out)
        return 0

    # Trash by pattern (safe)
    if args.trash:
        items = collect_matching_items(
            root,
            pattern=args.trash,
            max_depth=args.max_depth if args.max_depth != -1 else 999999,
            include_hidden=args.include_hidden,
            follow_symlinks=args.follow_symlinks,
            ignore=ignore,
        )
        if not items:
            print(t("trash_none", lang))
            return 0
        moved, skipped, _trash_dir = move_to_trash(root, items)
        print(t("trash_done", lang, n=moved))
        if skipped:
            print(t("trash_skip", lang, n=skipped))
        return 0

    # Folder sizes report
    if args.folder_sizes:
        top_n = args.top if args.top > 0 else 20
        items = folder_sizes_report(root, top_n=top_n, include_hidden=args.include_hidden, follow_symlinks=args.follow_symlinks, ignore=ignore)
        out = format_sizes_report(items) or t('placeholder_empty', lang)
        print(out)
        export_text(lang, args.export, out)
        return 0

    # Recent files
    if args.recent >= 0:
        days = args.recent
        top_n = args.top if args.top > 0 else 200
        items = list_recent_files(
            root,
            days=days,
            max_results=top_n,
            max_depth=args.max_depth if args.max_depth != -1 else 999999,
            include_hidden=args.include_hidden,
            follow_symlinks=args.follow_symlinks,
            ignore=ignore,
        )
        out = format_recent(items) or t('placeholder_empty', lang)
        print(out)
        export_text(lang, args.export, out)
        return 0

    # Clean duplicates (safe trash keep newest)
    if args.clean_dupes:
        dupes = find_duplicates(
            root,
            max_depth=args.max_depth if args.max_depth != -1 else 999999,
            include_hidden=args.include_hidden,
            follow_symlinks=args.follow_symlinks,
            ignore=ignore,
            min_size=max(1, args.min_size),
            algo="sha256",
        )
        if not dupes:
            print(t("dupes_none", lang))
            return 0
        kept, to_trash = clean_duplicates_keep_newest(dupes, base_root=root)
        moved, skipped, _trash_dir = move_to_trash(root, to_trash)
        print(t("trash_done", lang, n=moved))
        if skipped:
            print(t("trash_skip", lang, n=skipped))
        return 0

    # Remove empty folders (safe trash)
    if args.remove_empty:
        empties = find_empty_folders(
            root,
            max_depth=args.max_depth if args.max_depth != -1 else 999999,
            include_hidden=args.include_hidden,
            follow_symlinks=args.follow_symlinks,
            ignore=ignore,
        )
        empties = [p for p in empties if p != root]
        if not empties:
            print(t('placeholder_none', lang))
            return 0
        moved, skipped, _trash_dir = move_to_trash(root, empties)
        print(t("trash_done", lang, n=moved))
        if skipped:
            print(t("trash_skip", lang, n=skipped))
        return 0

    # Top-N largest files
    if args.top and args.top > 0 and not args.json:
        items = list_top_largest_files(
            root,
            top_n=args.top,
            max_depth=args.max_depth if args.max_depth != -1 else 999999,
            include_hidden=args.include_hidden,
            follow_symlinks=args.follow_symlinks,
            ignore=ignore,
            only=only,
        )
        out = format_top_list(items) or t('placeholder_empty', lang)
        print(out)
        export_text(lang, args.export, out)
        return 0

    # JSON output
    if args.json:
        obj = build_json(
            root,
            max_depth=args.max_depth,
            dirs_only=args.dirs_only,
            show_size=args.size,
            sort_by_size=args.sort_by_size,
            include_hidden=args.include_hidden,
            follow_symlinks=args.follow_symlinks,
            ignore=ignore,
            only=only,
        )
        out = _json.dumps(obj, ensure_ascii=False, indent=2)
        print(out)
        export_text(lang, args.export, out)
        return 0

    # Tree output (rich optional)
    stats = WalkStats() if args.summary else None
    if stats is not None:
        _ = get_total_size(root, follow_symlinks=args.follow_symlinks, ignore=ignore, only=only, include_hidden=args.include_hidden, stats=stats)

    if args.rich:
        ok = ensure_pip_package("rich", "rich")
        if ok:
            from rich.console import Console
            from rich.tree import Tree
            from rich.text import Text

            console = Console()

            def rich_label(e: Entry) -> Text:
                txt = Text(e.name)
                if not args.no_color:
                    if stat.S_ISDIR(e.mode):
                        txt.stylize("bold blue")
                    elif stat.S_ISLNK(e.mode):
                        txt.stylize("bold cyan")
                    elif stat.S_ISREG(e.mode) and (e.mode & 0o111):
                        txt.stylize("bold green")
                if args.size:
                    txt.append(f" [{format_size(e.total_size)}]")
                return txt

            def build_rich_tree(cur: Path, d: int, node: Tree) -> None:
                if args.max_depth != -1 and d > args.max_depth:
                    return
                need_sizes = args.size or args.sort_by_size
                ents = scan_entries(
                    cur,
                    dirs_only=args.dirs_only,
                    include_hidden=args.include_hidden,
                    need_sizes=need_sizes,
                    sort_by_size=args.sort_by_size,
                    follow_symlinks=args.follow_symlinks,
                    ignore=ignore,
                    only=only,
                )
                for e in ents:
                    child = node.add(rich_label(e))
                    if e.is_dir:
                        build_rich_tree(e.path, d + 1, child)

            root_node = Tree(str(root))
            if root.is_dir():
                build_rich_tree(root, 1, root_node)
            console.print(root_node)

            if stats is not None:
                print(build_summary_text(lang, stats))

            if args.export:
                text = build_tree_text(
                    root,
                    max_depth=args.max_depth,
                    dirs_only=args.dirs_only,
                    show_size=args.size,
                    sort_by_size=args.sort_by_size,
                    no_color=True,
                    include_hidden=args.include_hidden,
                    follow_symlinks=args.follow_symlinks,
                    ignore=ignore,
                    only=only,
                )
                if stats is not None:
                    text = (text + "\n" + build_summary_text(lang, stats)).strip()
                export_text(lang, args.export, text)
            return 0

        print(t("rich_fallback", lang), file=sys.stderr)

    text = build_tree_text(
        root,
        max_depth=args.max_depth,
        dirs_only=args.dirs_only,
        show_size=args.size,
        sort_by_size=args.sort_by_size,
        no_color=args.no_color,
        include_hidden=args.include_hidden,
        follow_symlinks=args.follow_symlinks,
        ignore=ignore,
        only=only,
    )
    if stats is not None:
        text = (text + "\n" + build_summary_text(lang, stats)).strip()
    print(text)
    export_text(lang, args.export, text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
