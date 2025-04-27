#!/usr/bin/env python3
import sys
import subprocess
import threading
import random
import time
import os

# -----------------------
# Auto-install dependencies
# -----------------------
def _install(pkg):
    subprocess.run([sys.executable, "-m", "pip", "install", pkg], stdout=subprocess.DEVNULL)

for _pkg in ("requests", "wcwidth"):
    try:
        __import__(_pkg)
    except ImportError:
        _install(_pkg)

import curses
import requests
from wcwidth import wcwidth

# -----------------------
# Repo config
# -----------------------
REPO_URL     = "https://github.com/dedsec1121fk/DedSec-Radio"
REPO_API_URL = "https://api.github.com/repos/dedsec1121fk/DedSec-Radio"
LOCAL_DIR    = os.path.expanduser("~/Radio")

def _run(cmd, cwd=None):
    try:
        return subprocess.run(cmd, shell=True, cwd=cwd,
                              capture_output=True, text=True)
    except:
        return None

def _clone():
    os.chdir(os.path.expanduser("~"))
    _run(f"git clone {REPO_URL} Radio")

def _update():
    if os.path.isdir(LOCAL_DIR):
        _run("git fetch", cwd=LOCAL_DIR)
        res = _run("git rev-list HEAD..origin/main --count", cwd=LOCAL_DIR)
        try:
            if int(res.stdout.strip()) > 0:
                _run("git reset --hard origin/main", cwd=LOCAL_DIR)
                _run("git pull", cwd=LOCAL_DIR)
        except:
            pass
    else:
        _clone()

# -----------------------
# Termux volume helper
# -----------------------
def set_volume(pct: int):
    # Map 0–100% to 0–15 music volume
    lvl = int(pct * 15 / 100)
    try:
        subprocess.run(["termux-volume", "music", str(lvl)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        pass

# -----------------------
# Radio playback
# -----------------------
def stop_music():
    # Ensure any playing media is stopped
    subprocess.run(["termux-media-player", "stop"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def list_stations():
    if not os.path.isdir(LOCAL_DIR):
        return []
    return [d for d in os.listdir(LOCAL_DIR)
            if os.path.isdir(os.path.join(LOCAL_DIR, d)) and not d.startswith('.')]

def list_songs(st):
    p = os.path.join(LOCAL_DIR, st)
    return [f for f in os.listdir(p) if f.lower().endswith('.mp3')]

def play_song(path, stop_evt):
    stop_music()
    try:
        proc = subprocess.Popen(["termux-media-player", "play", path],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        return
    while not stop_evt.is_set():
        time.sleep(0.1)
    proc.terminate()

def play_station(st, stop_evt, now_playing):
    stop_evt.clear()
    stop_music()
    songs = list_songs(st)
    if not songs:
        now_playing[0] = "No songs."
        return
    random.shuffle(songs)
    for s in songs:
        if stop_evt.is_set():
            return
        now_playing[0] = s
        play_song(os.path.join(LOCAL_DIR, st, s), stop_evt)

# -----------------------
# Curses UI
# -----------------------
ASCII = ["📻DedSec Radio📻"]

def wrap(txt, w):
    lines, cur, width = [], "", 0
    for ch in txt:
        wc = max(wcwidth(ch), 1)
        if width + wc > w:
            lines.append(cur); cur, width = ch, wc
        else:
            cur += ch; width += wc
    if cur:
        lines.append(cur)
    return lines

def draw_center(stdscr, y, txt, w, maxl=None):
    lines = wrap(txt, w)
    for i, ln in enumerate(lines[: maxl or len(lines)]):
        x = max((w - sum(max(wcwidth(c),1) for c in ln)) // 2, 0)
        try:
            stdscr.addstr(y + i, x, ln, curses.color_pair(1))
        except curses.error:
            pass

def prompt_download(stdscr):
    sz = "unknown"
    try:
        r = requests.get(REPO_API_URL, timeout=2)
        if r.status_code == 200:
            sz = f"{r.json().get('size',0)/1024:.2f} MB"
    except:
        pass
    prompt = f"Repo missing (size {sz}). Download? (y/n): "
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    stdscr.addstr(h // 2, max((w - len(prompt)) // 2, 0), prompt)
    stdscr.refresh()
    while True:
        c = stdscr.getch()
        if c in (ord('y'), ord('Y')):
            _clone()
            return True
        if c in (ord('n'), ord('N')):
            return False

def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
    stdscr.nodelay(True)
    stdscr.timeout(100)

    # ensure repo present
    if not os.path.isdir(LOCAL_DIR):
        if not prompt_download(stdscr):
            return
    else:
        _update()

    stations = list_stations()
    if not stations:
        stdscr.addstr(0, 0, "No stations found!", curses.color_pair(1))
        stdscr.refresh()
        time.sleep(2)
        return

    # frequency list
    n = len(stations)
    lo, hi = 88.0, 108.0
    freqs = ([lo + i*(hi-lo)/(n-1) for i in range(n)]
             if n > 1 else [(lo+hi)/2])

    # state
    idx = 0
    vol = 0
    line = 0  # 0=freq dial, 1=vol dial
    now = [""]
    stop_evt = threading.Event()
    thread = None

    def start(i):
        nonlocal thread, stop_evt
        if thread and thread.is_alive():
            stop_evt.set()
            thread.join(0.5)
        stop_evt = threading.Event()
        thread = threading.Thread(
            target=play_station,
            args=(stations[i], stop_evt, now),
            daemon=True
        )
        thread.start()

    # init
    set_volume(vol)
    start(idx)
    blocks = [" ", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        # header
        for i, ln in enumerate(ASCII):
            draw_center(stdscr, i, ln, w)
        draw_center(stdscr, len(ASCII),
                    "↑/↓ switch line, ←/→ change, q quit", w)

        # station info
        info = f"{freqs[idx]:.1f} FM — {stations[idx]}"
        draw_center(stdscr, len(ASCII) + 2, info, w)

        # freq dial
        y0 = len(ASCII) + 4
        L, R = f"{lo:.1f}", f"{hi:.1f}"
        dlen = max(w - len(L) - len(R) - 2, 0)
        dial = L + "-" * dlen + R
        x0 = (w - len(dial)) // 2
        attr = curses.color_pair(2) if line == 0 else curses.color_pair(1)
        stdscr.addstr(y0, x0, dial, attr)
        pos = int((freqs[idx] - lo) / (hi - lo) * dlen) if hi != lo else 0
        stdscr.addstr(y0 + 1, x0 + len(L) + pos, "^", curses.color_pair(1))

        # volume dial
        y1 = y0 + 4
        VL, VR = "0%", "100%"
        vlen = max(w - len(VL) - len(VR) - 2, 0)
        vd = VL + "-" * vlen + VR
        x1 = (w - len(vd)) // 2
        attr2 = curses.color_pair(2) if line == 1 else curses.color_pair(1)
        stdscr.addstr(y1, x1, vd, attr2)
        vpos = int(vol / 100 * vlen)
        stdscr.addstr(y1 + 1, x1 + len(VL) + vpos, "^", curses.color_pair(1))
        draw_center(stdscr, y1 + 3, f"Volume: {vol}%", w)

        # now playing
        y2 = y1 + 6
        draw_center(stdscr, y2, f"🎶 Now: {now[0]}", w, maxl=2)

        # visualizer
        y3 = y2 + 3
        vw = max(w - 4, 1)
        viz = "".join(blocks[random.randint(0, 8)] for _ in range(vw))
        stdscr.addstr(y3, (w - len(viz)) // 2, viz, curses.color_pair(1))

        stdscr.refresh()

        c = stdscr.getch()
        if c in (ord('q'), ord('Q')):
            stop_evt.set()
            stop_music()
            break
        elif c == curses.KEY_UP:
            line = max(0, line - 1)
        elif c == curses.KEY_DOWN:
            line = min(1, line + 1)
        elif c in (curses.KEY_LEFT, curses.KEY_RIGHT):
            if line == 0:
                old = idx
                idx = max(0, idx - 1) if c == curses.KEY_LEFT else min(n - 1, idx + 1)
                if idx != old:
                    start(idx)
            else:
                vol = max(0, vol - 5) if c == curses.KEY_LEFT else min(100, vol + 5)
                set_volume(vol)

        time.sleep(0.05)

    # ensure music is stopped on exit
    stop_music()

if __name__ == "__main__":
    curses.wrapper(main)

