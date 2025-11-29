#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import subprocess
import time
import shutil
import curses
import calendar
import shlex
import traceback
from datetime import datetime, timedelta
from difflib import SequenceMatcher

HOME = os.path.expanduser('~')
NOTES_FILE = os.path.join(HOME, '.smart_notes.json')
CONFIG_FILE = os.path.join(HOME, '.smart_notes_config.json')
ERROR_LOG = os.path.join(HOME, '.smart_notes_error.log')

# Ensure files exist
for path, default in [(NOTES_FILE, {}), (CONFIG_FILE, {})]:
    if not os.path.exists(path):
        try:
            with open(path, 'w') as f:
                json.dump(default, f)
        except Exception:
            pass

# Optional dependencies
try:
    from dateutil import parser as dateparser
except Exception:
    dateparser = None

# Load timezones
def load_timezones():
    try:
        from zoneinfo import available_timezones
        tzs = sorted([t for t in available_timezones() if '/' in t])
        if tzs:
            return tzs
    except Exception:
        pass
    try:
        import pytz
        return sorted(list(pytz.all_timezones))
    except Exception:
        pass
    return sorted([
        'UTC', 'Europe/Athens', 'Europe/London', 'Europe/Berlin', 'Europe/Paris',
        'America/New_York', 'America/Los_Angeles', 'America/Chicago', 'Asia/Tokyo',
        'Asia/Shanghai', 'Asia/Kolkata', 'Asia/Dubai', 'Australia/Sydney',
        'Pacific/Auckland', 'Africa/Johannesburg'
    ])

# Load countries
def load_countries():
    try:
        import pycountry
        names = [c.name for c in pycountry.countries]
        return sorted(set(names))
    except Exception:
        return sorted([
            'Greece', 'United States', 'United Kingdom', 'Germany', 'France', 'Spain',
            'Italy', 'India', 'China', 'Japan', 'Australia', 'Canada', 'Brazil', 'Russia',
            'South Africa', 'Egypt', 'Turkey', 'Mexico', 'Netherlands', 'Sweden'
        ])

TIMEZONES = load_timezones()
COUNTRIES = load_countries()

# --- I/O helpers ---

def _safe_read_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def load_notes():
    raw = _safe_read_json(NOTES_FILE)
    if not isinstance(raw, dict):
        raw = {}
    norm = {}
    for k, v in raw.items():
        if k == '_reminders':
            norm[k] = v if isinstance(v, list) else []
            continue
        if isinstance(v, str):
            norm[k] = v
        else:
            try:
                norm[k] = json.dumps(v, indent=2, ensure_ascii=False)
            except Exception:
                norm[k] = str(v)
    return norm


def save_notes(notes):
    try:
        with open(NOTES_FILE, 'w') as f:
            json.dump(notes, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def load_config():
    cfg = _safe_read_json(CONFIG_FILE)
    return cfg if isinstance(cfg, dict) else {}


def save_config(cfg):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(cfg, f, indent=2)
        return True
    except Exception:
        return False


def ensure_termux_api():
    return bool(shutil.which('termux-notification'))

# --- utilities ---

def log_exception(exc: Exception):
    try:
        with open(ERROR_LOG, 'a') as f:
            f.write('\n--- %s ---\n' % datetime.now().isoformat())
            traceback.print_exc(file=f)
    except Exception:
        pass


def score_query(a, b):
    return SequenceMatcher(None, (a or '').lower(), (b or '').lower()).ratio()


def reinit_curses():
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    try:
        curses.curs_set(0)
    except Exception:
        pass
    stdscr.clear()
    return stdscr


def centered_addstr(win, y, text, attr=0):
    try:
        h, w = win.getmaxyx()
        x = max(0, (w - len(text)) // 2)
        win.addstr(y, x, text, attr)
    except Exception:
        pass

# --- curses UI components ---

def curses_editor(stdscr, initial_text):
    curses.curs_set(1)
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    lines = initial_text.split('\n') if initial_text else ['']
    cursor_y, cursor_x = 0, 0
    while True:
        stdscr.erase()
        title = ' Nano-like editor — Ctrl+X save, Ctrl+C cancel '
        stdscr.attron(curses.A_REVERSE)
        centered_addstr(stdscr, 0, title[:w-1])
        stdscr.attroff(curses.A_REVERSE)
        max_display = h - 4
        start = 0
        if cursor_y >= max_display:
            start = cursor_y - max_display + 1
        for idx in range(start, min(start + max_display, len(lines))):
            ln = lines[idx]
            try:
                stdscr.addstr(2 + idx - start, 2, ln[:w-4])
            except Exception:
                pass
        status = f"Ln {cursor_y+1}, Col {cursor_x+1} — Ctrl+X=save"
        centered_addstr(stdscr, h-2, status[:w-1])
        try:
            stdscr.move(2 + cursor_y - start, 2 + cursor_x)
        except Exception:
            pass
        stdscr.refresh()
        ch = stdscr.getch()
        if ch == 24:  # Ctrl+X
            curses.curs_set(0)
            return '\n'.join(lines)
        elif ch in (3,):  # Ctrl+C
            curses.curs_set(0)
            return None
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            if cursor_x > 0:
                lines[cursor_y] = lines[cursor_y][:cursor_x-1] + lines[cursor_y][cursor_x:]
                cursor_x -= 1
            else:
                if cursor_y > 0:
                    prev = lines[cursor_y-1]
                    cur = lines.pop(cursor_y)
                    cursor_x = len(prev)
                    lines[cursor_y-1] = prev + cur
                    cursor_y -= 1
        elif ch == curses.KEY_LEFT:
            if cursor_x > 0:
                cursor_x -= 1
            elif cursor_y > 0:
                cursor_y -= 1
                cursor_x = len(lines[cursor_y])
        elif ch == curses.KEY_RIGHT:
            if cursor_x < len(lines[cursor_y]):
                cursor_x += 1
            elif cursor_y < len(lines)-1:
                cursor_y += 1
                cursor_x = 0
        elif ch == curses.KEY_UP:
            if cursor_y > 0:
                cursor_y -= 1
                cursor_x = min(cursor_x, len(lines[cursor_y]))
        elif ch == curses.KEY_DOWN:
            if cursor_y < len(lines)-1:
                cursor_y += 1
                cursor_x = min(cursor_x, len(lines[cursor_y]))
        elif ch in (10, 13):
            cur = lines[cursor_y]
            left = cur[:cursor_x]
            right = cur[cursor_x:]
            lines[cursor_y] = left
            lines.insert(cursor_y+1, right)
            cursor_y += 1
            cursor_x = 0
        elif ch == curses.KEY_DC:
            if cursor_x < len(lines[cursor_y]):
                lines[cursor_y] = lines[cursor_y][:cursor_x] + lines[cursor_y][cursor_x+1:]
            else:
                if cursor_y < len(lines)-1:
                    lines[cursor_y] = lines[cursor_y] + lines.pop(cursor_y+1)
        elif 0 <= ch <= 255:
            lines[cursor_y] = lines[cursor_y][:cursor_x] + chr(ch) + lines[cursor_y][cursor_x:]
            cursor_x += 1
        cursor_x = max(0, min(cursor_x, len(lines[cursor_y])))
        if cursor_y < 0:
            cursor_y = 0
        if cursor_y >= len(lines):
            cursor_y = len(lines)-1


def curses_input(stdscr, prompt, default=''):
    curses.curs_set(1)
    h,w = stdscr.getmaxyx()
    inp = list(default)
    pos = len(inp)
    while True:
        stdscr.erase()
        centered_addstr(stdscr, h//2 - 2, prompt)
        disp = ''.join(inp)
        x = max(0, (w - len(disp)) // 2)
        try:
            stdscr.addstr(h//2, x, disp[:w-2])
        except Exception:
            pass
        stdscr.move(h//2, x + pos)
        stdscr.refresh()
        ch = stdscr.getch()
        if ch in (10,13):
            curses.curs_set(0)
            return disp
        elif ch in (27,):
            curses.curs_set(0)
            return None
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            if pos > 0:
                inp.pop(pos-1)
                pos -= 1
        elif ch == curses.KEY_LEFT:
            pos = max(0, pos-1)
        elif ch == curses.KEY_RIGHT:
            pos = min(len(inp), pos+1)
        elif 0 <= ch <= 255:
            inp.insert(pos, chr(ch))
            pos += 1


def curses_select_from_list(stdscr, title, options, start_index=0):
    curses.curs_set(0)
    if not options:
        return None
    idx = start_index
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        centered_addstr(stdscr, 1, title)
        per_page = max(6, h - 8)
        page = idx // per_page
        start = page * per_page
        end = min(len(options), start + per_page)
        for i in range(start, end):
            attr = curses.A_REVERSE if i == idx else 0
            centered_addstr(stdscr, 3 + i - start, f" {options[i]} ", attr)
        centered_addstr(stdscr, h-2, 'Up/Down move, Left/Right page, Enter select, / search, ESC cancel')
        stdscr.refresh()
        ch = stdscr.getch()
        if ch in (curses.KEY_UP,):
            idx = (idx - 1) % len(options)
        elif ch in (curses.KEY_DOWN,):
            idx = (idx + 1) % len(options)
        elif ch == curses.KEY_LEFT:
            idx = max(0, idx - per_page)
        elif ch == curses.KEY_RIGHT:
            idx = min(len(options)-1, idx + per_page)
        elif ch in (10,13):
            return options[idx]
        elif ch == 27:
            return None
        elif ch == ord('/'):
            q = curses_input(stdscr, 'Search:')
            if q:
                ql = q.lower()
                for i,opt in enumerate(options):
                    if ql in opt.lower():
                        idx = i
                        break

# Search
def curses_search(stdscr, notes):
    try:
        curses.curs_set(1)
        h, w = stdscr.getmaxyx()
        query = ''
        matches = []
        selected = 0
        keys = [k for k in notes.keys() if k != '_reminders']
        while True:
            stdscr.erase()
            centered_addstr(stdscr, 1, ' Search Notes (type to filter) — Enter select, ESC back ')
            stdscr.addstr(3, max(2, (w - 60)//2), 'Query: ' + query + ' ')
            scored = []
            for k in keys:
                s = score_query(query, k) if query else 0
                s2 = score_query(query, notes.get(k, '')) if query else 0
                score = max(s, s2)
                scored.append((score, k))
            scored.sort(reverse=True)
            matches = [k for sc,k in scored if sc>0 or not query][:min(20, len(scored))]
            start_y = 5
            for idx, key in enumerate(matches):
                marker = '>' if idx == selected else ' '
                line = f"{marker} {key}"
                try:
                    stdscr.addstr(start_y+idx, max(2, (w - 60)//2), line[:60])
                except Exception:
                    pass
            stdscr.refresh()
            ch = stdscr.getch()
            if ch in (27,):
                curses.curs_set(0)
                return None
            elif ch in (10,13):
                if not matches:
                    continue
                curses.curs_set(0)
                return matches[selected]
            elif ch == curses.KEY_UP:
                selected = max(0, selected-1)
            elif ch == curses.KEY_DOWN:
                selected = min(len(matches)-1, selected+1)
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                query = query[:-1]
                selected = 0
            elif 0 <= ch <= 255:
                query += chr(ch)
                selected = 0
    except Exception as e:
        log_exception(e)
        error_dialog(stdscr, 'Search error', traceback.format_exc())
        return None

# Confirm dialog
def confirm_dialog(stdscr, text):
    h,w = stdscr.getmaxyx()
    while True:
        stdscr.erase()
        centered_addstr(stdscr, h//2 - 1, text + ' (Y/N)')
        centered_addstr(stdscr, h//2 + 1, 'Y: Yes    N: No')
        stdscr.refresh()
        ch = stdscr.getch()
        if ch in (ord('y'), ord('Y')):
            return True
        elif ch in (ord('n'), ord('N'), 27):
            return False

# View note
def view_note_curses(stdscr, title, content):
    try:
        h,w = stdscr.getmaxyx()
        stdscr.clear()
        if not isinstance(content, str):
            try:
                content = json.dumps(content, indent=2, ensure_ascii=False)
            except Exception:
                content = str(content)
        lines = content.split('\n')
        pos = 0
        while True:
            stdscr.erase()
            centered_addstr(stdscr, 1, f' {title} ')
            for i in range(min(h-6, len(lines)-pos)):
                try:
                    stdscr.addstr(3+i, 2, lines[pos+i][:w-4])
                except Exception:
                    pass
            centered_addstr(stdscr, h-2, 'Up/Down scroll, B for back')
            stdscr.refresh()
            ch = stdscr.getch()
            if ch == curses.KEY_DOWN:
                if pos + (h-6) < len(lines):
                    pos += 1
            elif ch == curses.KEY_UP:
                pos = max(0, pos-1)
            elif ch in (ord('b'), ord('B'), 27):
                return
    except Exception as e:
        log_exception(e)
        error_dialog(stdscr, 'View error', traceback.format_exc())

# Actions for note
def action_for_note(stdscr, key, notes):
    try:
        h,w = stdscr.getmaxyx()
        while True:
            stdscr.erase()
            centered_addstr(stdscr, 1, f' Note: {key} ')
            content = notes.get(key, '')
            if not isinstance(content, str):
                try:
                    preview_text = json.dumps(content, indent=2, ensure_ascii=False)
                except Exception:
                    preview_text = str(content)
            else:
                preview_text = content
            preview = preview_text.split('\n')[:10]
            for i,line in enumerate(preview):
                try:
                    stdscr.addstr(3+i, 2, line[:w-4])
                except Exception:
                    pass
            centered_addstr(stdscr, h-4, 'V: View  E: Edit  D: Delete  B: Back')
            stdscr.refresh()
            ch = stdscr.getch()
            if ch in (ord('v'), ord('V')):
                view_note_curses(stdscr, key, content)
            elif ch in (ord('e'), ord('E')):
                initial = preview_text if isinstance(content, (dict, list)) else str(content)
                new = curses_editor(stdscr, initial)
                if new is not None:
                    notes[key] = new
                    save_notes(notes)
            elif ch in (ord('d'), ord('D')):
                confirmed = confirm_dialog(stdscr, f'Delete note "{key}"?')
                if confirmed:
                    notes.pop(key, None)
                    save_notes(notes)
                    return
            elif ch in (ord('b'), ord('B'), 27):
                return
    except Exception as e:
        log_exception(e)
        error_dialog(stdscr, 'Note action error', traceback.format_exc())

# Add note (curses)
def add_note_curses(stdscr):
    try:
        notes = load_notes()
        name = curses_input(stdscr, 'Note name:')
        if name is None or not name.strip():
            return
        name = name.strip()
        if name in notes:
            overwrite = curses_input(stdscr, 'Overwrite existing? (y/N):', 'N')
            if not overwrite or overwrite.lower() not in ('y'):
                return
        new = curses_editor(stdscr, notes.get(name, ''))
        if new is None:
            return
        notes[name] = new
        save_notes(notes)
    except Exception as e:
        log_exception(e)
        error_dialog(stdscr, 'Add note error', traceback.format_exc())

# Date/time picker
def curses_date_picker(stdscr, initial_dt=None):
    try:
        curses.curs_set(0)
        now = datetime.now()
        year = initial_dt.year if initial_dt else now.year
        month = initial_dt.month if initial_dt else now.month
        day = initial_dt.day if initial_dt else now.day
        hour = initial_dt.hour if initial_dt else now.hour
        minute = initial_dt.minute if initial_dt else 0
        fields = ['year','month','day','hour','minute','confirm']
        idx = 0
        while True:
            stdscr.erase()
            h,w = stdscr.getmaxyx()
            centered_addstr(stdscr, 1, ' Select date & time for reminder ')
            centered_addstr(stdscr, 3, f' Year:   {year} ', curses.A_REVERSE if fields[idx]=='year' else 0)
            centered_addstr(stdscr, 5, f' Month:  {month} ', curses.A_REVERSE if fields[idx]=='month' else 0)
            centered_addstr(stdscr, 7, f' Day:    {day} ', curses.A_REVERSE if fields[idx]=='day' else 0)
            centered_addstr(stdscr, 9, f' Hour:   {hour:02d} ', curses.A_REVERSE if fields[idx]=='hour' else 0)
            centered_addstr(stdscr, 11, f' Minute: {minute:02d} ', curses.A_REVERSE if fields[idx]=='minute' else 0)
            centered_addstr(stdscr, 13, f' [ Confirm ] ', curses.A_REVERSE if fields[idx]=='confirm' else 0)
            centered_addstr(stdscr, h-2, 'Left/Right field, Up/Down value, Enter confirm, ESC cancel')
            stdscr.refresh()
            ch = stdscr.getch()
            if ch == curses.KEY_LEFT:
                idx = (idx - 1) % len(fields)
            elif ch == curses.KEY_RIGHT:
                idx = (idx + 1) % len(fields)
            elif ch == curses.KEY_UP:
                if fields[idx] == 'year':
                    year += 1
                elif fields[idx] == 'month':
                    month = 12 if month == 12 else month + 1
                    _, mdays = calendar.monthrange(year, month)
                    if day > mdays:
                        day = mdays
                elif fields[idx] == 'day':
                    _, mdays = calendar.monthrange(year, month)
                    day = 1 if day >= mdays else day + 1
                elif fields[idx] == 'hour':
                    hour = (hour + 1) % 24
                elif fields[idx] == 'minute':
                    minute = (minute + 1) % 60
            elif ch == curses.KEY_DOWN:
                if fields[idx] == 'year':
                    year = max(now.year, year - 1)
                elif fields[idx] == 'month':
                    month = 1 if month == 1 else month - 1
                    _, mdays = calendar.monthrange(year, month)
                    if day > mdays:
                        day = mdays
                elif fields[idx] == 'day':
                    _, mdays = calendar.monthrange(year, month)
                    day = mdays if day <= 1 else day - 1
                elif fields[idx] == 'hour':
                    hour = (hour - 1) % 24
                elif fields[idx] == 'minute':
                    minute = (minute - 1) % 60
            elif ch in (10,13):
                if fields[idx] == 'confirm':
                    try:
                        picked = datetime(year, month, day, hour, minute)
                        if picked <= datetime.now():
                            centered_addstr(stdscr, (h//2)+6, 'Please select a future time', curses.A_BOLD)
                            stdscr.refresh()
                            time.sleep(1.2)
                            continue
                        return picked
                    except Exception:
                        centered_addstr(stdscr, (h//2)+6, 'Invalid date, adjust values', curses.A_BOLD)
                        stdscr.refresh()
                        time.sleep(1.2)
                        continue
            elif ch == 27:
                return None
    except Exception as e:
        log_exception(e)
        error_dialog(stdscr, 'Date picker error', traceback.format_exc())
        return None

# Reminders menu
def curses_reminders_menu(stdscr):
    try:
        notes = load_notes()
        reminders = notes.get('_reminders', [])
        idx = 0
        options = ['Add reminder','List reminders','Delete reminder','Back']
        while True:
            stdscr.erase()
            h,w = stdscr.getmaxyx()
            centered_addstr(stdscr, 1, ' Calendar / Reminders ')
            total_h = len(options) * 2
            start_y = max(3, (h - total_h) // 2)
            for i,opt in enumerate(options):
                centered_addstr(stdscr, start_y + i*2, f" {opt} ", curses.A_REVERSE if i==idx else 0)
            stdscr.refresh()
            ch = stdscr.getch()
            if ch == curses.KEY_UP:
                idx = (idx - 1) % len(options)
            elif ch == curses.KEY_DOWN:
                idx = (idx + 1) % len(options)
            elif ch in (10,13):
                choice = options[idx]
                if choice == 'Add reminder':
                    title = curses_input(stdscr, 'Reminder title:')
                    if title is None:
                        continue
                    title = title.strip()
                    dt = curses_date_picker(stdscr)
                    if dt is None:
                        continue
                    note_text = curses_editor(stdscr, '')
                    if note_text is None:
                        note_text = ''
                    reminders.append({'title': title, 'datetime': dt.isoformat(), 'text': note_text})
                    notes['_reminders'] = reminders
                    save_notes(notes)
                    scheduled = schedule_termux_notification(title, dt, note_text)
                    stdscr.erase()
                    centered_addstr(stdscr, h//2, 'Reminder saved.' + (' Scheduled.' if scheduled else ' Saved (not scheduled).'))
                    stdscr.refresh()
                    time.sleep(1.2)
                elif choice == 'List reminders':
                    stdscr.erase()
                    centered_addstr(stdscr, 1, ' Scheduled reminders ')
                    if not reminders:
                        centered_addstr(stdscr, h//2, 'No reminders')
                    else:
                        for i,r in enumerate(reminders[:h-6]):
                            centered_addstr(stdscr, 3+i, f"{i+1}) {r['title']} at {r['datetime']}")
                    centered_addstr(stdscr, h-2, 'Press any key to continue')
                    stdscr.refresh()
                    stdscr.getch()
                elif choice == 'Delete reminder':
                    if not reminders:
                        stdscr.erase()
                        centered_addstr(stdscr, h//2, 'No reminders to delete')
                        stdscr.refresh()
                        time.sleep(1.0)
                    else:
                        opts = [f"{r['title']} @ {r['datetime']}" for r in reminders]
                        sel = curses_select_from_list(stdscr, 'Select reminder to delete', opts)
                        if sel is None:
                            continue
                        sel_idx = opts.index(sel)
                        if confirm_dialog(stdscr, f'Delete "{reminders[sel_idx]["title"]}"?'):
                            reminders.pop(sel_idx)
                            notes['_reminders'] = reminders
                            save_notes(notes)
                elif choice == 'Back':
                    return
            elif ch == 27:
                return
    except Exception as e:
        log_exception(e)
        error_dialog(stdscr, 'Reminders error', traceback.format_exc())

# Scheduler (creates a small shell script safely quoted)
def schedule_termux_notification(title, dt, text):
    try:
        job_bin = shutil.which('termux-job-scheduler')
        notif_bin = shutil.which('termux-notification')
        if not notif_bin:
            return False
        epoch_ms = int(dt.timestamp() * 1000)
        if job_bin:
            job_id = f"smart_notes_{int(time.time())}"
            script_path = os.path.join(HOME, f'.smart_notes_job_{job_id}.sh')
            safe_title = shlex.quote(title)
            safe_text = shlex.quote(text or '')
            try:
                with open(script_path, 'w') as f:
                    f.write('#!/data/data/com.termux/files/usr/bin/sh\n')
                    f.write(f'termux-notification --title {safe_title} --content {safe_text}\n')
                os.chmod(script_path, 0o755)
                subprocess.check_call([
                    'termux-job-scheduler', '-s', job_id, '-t', str(epoch_ms),
                    '--service', 'com.termux.job.JobService', '-c', f'sh {shlex.quote(script_path)}'
                ])
                return True
            except Exception:
                return False
        else:
            at_bin = shutil.which('at')
            if at_bin:
                try:
                    # Use at if available (best-effort)
                    cmd = f'termux-notification --title {shlex.quote(title)} --content {shlex.quote(text or "")}'
                    at_time_str = dt.strftime('%H:%M %Y-%m-%d')
                    p = subprocess.Popen(['at', '-M', at_time_str], stdin=subprocess.PIPE)
                    p.communicate(input=(cmd + "\n").encode())
                    return True
                except Exception:
                    return False
    except Exception:
        return False
    return False

# Run pending reminders
def run_pending_reminders():
    notes = load_notes()
    reminders = notes.get('_reminders', [])
    now = datetime.now()
    changed = False
    for r in list(reminders):
        try:
            dt = datetime.fromisoformat(r['datetime'])
        except Exception:
            continue
        if dt <= now:
            if ensure_termux_api():
                try:
                    subprocess.check_call(['termux-notification', '--title', r['title'], '--content', r.get('text','')])
                except Exception:
                    pass
            reminders.remove(r)
            changed = True
    if changed:
        notes['_reminders'] = reminders
        save_notes(notes)

# Main menu
def main_menu(stdscr):
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    try:
        curses.curs_set(0)
    except Exception:
        pass
    while True:
        notes = load_notes()
        options = ['Add Note','Search Note','Calendar / Reminders','Settings (country/timezone)','Exit']
        idx = 0
        try:
            while True:
                stdscr.erase()
                h, w = stdscr.getmaxyx()
                centered_addstr(stdscr, 1, ' Smart Notes — Termux ')
                total_h = len(options) * 2
                start_y = max(3, (h - total_h) // 2)
                for i, opt in enumerate(options):
                    y = start_y + i*2
                    attr = curses.A_REVERSE if i == idx else 0
                    centered_addstr(stdscr, y, f" {opt} ", attr)
                stdscr.refresh()
                ch = stdscr.getch()
                if ch in (curses.KEY_UP,):
                    idx = (idx - 1) % len(options)
                elif ch in (curses.KEY_DOWN,):
                    idx = (idx + 1) % len(options)
                elif ch in (10,13):
                    choice = options[idx]
                    if choice == 'Add Note':
                        add_note_curses(stdscr)
                        break
                    elif choice == 'Search Note':
                        key = curses_search(stdscr, notes)
                        if key:
                            action_for_note(stdscr, key, notes)
                        break
                    elif choice == 'Calendar / Reminders':
                        curses_reminders_menu(stdscr)
                        break
                    elif choice == 'Settings (country/timezone)':
                        sel_country = curses_select_from_list(stdscr, 'Select country (ESC to cancel)', COUNTRIES + ['Custom'])
                        if sel_country is None:
                            break
                        if sel_country == 'Custom':
                            sel_country = curses_input(stdscr, 'Enter country name:')
                            if sel_country is None:
                                break
                        sel_tz = curses_select_from_list(stdscr, 'Select timezone (ESC to cancel)', TIMEZONES + ['Custom'])
                        if sel_tz is None:
                            break
                        if sel_tz == 'Custom':
                            sel_tz = curses_input(stdscr, 'Enter timezone (e.g. Europe/Athens):')
                            if sel_tz is None:
                                break
                        cfg = load_config()
                        cfg['country'] = sel_country
                        cfg['timezone'] = sel_tz
                        save_config(cfg)
                        stdscr.erase()
                        centered_addstr(stdscr, h//2, 'Settings saved.')
                        stdscr.refresh()
                        time.sleep(1.0)
                        break
                    elif choice == 'Exit':
                        return
                elif ch in (27,):
                    return
        except Exception as e:
            log_exception(e)
            error_dialog(stdscr, 'Unexpected error in main menu', traceback.format_exc())

# CLI fallback add
def add_note_interactive():
    notes = load_notes()
    print('\n=== Add Note ===')
    name = input('Note name: ').strip()
    if not name:
        print('Canceled: empty name')
        return
    if name in notes:
        if input('Overwrite existing? (y/N): ').lower() not in ('y'):
            print('Canceled')
            return
    print('Starting editor. Terminate with a line containing only .save')
    try:
        lines = []
        while True:
            ln = input()
            if ln.strip() == '.save':
                break
            lines.append(ln)
        new = '\n'.join(lines)
    except KeyboardInterrupt:
        print('\nCanceled')
        return
    notes[name] = new
    save_notes(notes)
    print('Saved.')

# Help
def print_help():
    print('Smart Notes - Termux')
    print('Commands:')
    print('  (no arguments) -> curses environment')
    print('  --add          -> add note via command line')
    print('  --run-reminders-> run pending reminders')
    print('  --help         -> this help')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == '--add':
            add_note_interactive(); sys.exit(0)
        if arg == '--run-reminders':
            run_pending_reminders(); sys.exit(0)
        if arg in ('-h','--help'):
            print_help(); sys.exit(0)
    try:
        curses.wrapper(main_menu)
    except Exception as e:
        log_exception(e)
        print('Fatal error — logged to', ERROR_LOG)
        traceback.print_exc()
