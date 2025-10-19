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
        'America/New_York', 'America/Los_Angeles', 'Asia/Tokyo', 'Australia/Sydney'
    ])

TIMEZONES = load_timezones()

# -----------------
# Core File Logic
# -----------------

def load_notes():
    """Loads notes from the JSON file."""
    if not os.path.exists(NOTES_FILE):
        return {}
    try:
        with open(NOTES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading notes: {e}. Starting with an empty set.")
        return {}

def save_notes(notes):
    """Saves notes to the JSON file."""
    try:
        with open(NOTES_FILE, 'w') as f:
            json.dump(notes, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving notes: {e}")

# -----------------
# Reminder Logic
# -----------------

def _parse_reminder_data(note_content: str) -> dict:
    """Parses reminder metadata from the beginning of a note."""
    data = {}
    lines = note_content.split('\n')
    for line in lines:
        if line.strip().startswith('#reminder:'):
            parts = line.split(':', 2)
            if len(parts) == 3:
                key = parts[1].strip()
                value = parts[2].strip()
                data[key] = value
        elif not line.strip(): # Stop on first empty line
            break
        elif not line.strip().startswith('#'): # Stop on first non-comment/non-empty line
            break
    return data

def get_reminder_content(note_content: str) -> str:
    """Removes metadata lines from note content for display."""
    lines = note_content.split('\n')
    content_lines = []
    metadata_done = False
    for line in lines:
        if not metadata_done and line.strip().startswith('#reminder:'):
            continue
        if not metadata_done and not line.strip():
            metadata_done = True
            continue
        if not metadata_done and not line.strip().startswith('#'):
            metadata_done = True
            
        if metadata_done:
            content_lines.append(line)
    return '\n'.join(content_lines).strip()

def run_reminders(auto_run=False):
    """Checks and executes overdue reminders."""
    notes = load_notes()
    reminders_run = 0
    
    if not dateparser:
        if auto_run: return # Cannot run without dateutil
        print('Cannot run reminders: The dateutil library is required.')
        print('Please install it with: pip install python-dateutil')
        return

    print("\n--- Checking Reminders ---")
    
    for name, content in notes.items():
        data = _parse_reminder_data(content)
        
        # Check for reminder trigger
        if 'due' in data:
            try:
                # Use dateparser to handle flexible date formats
                due_time = dateparser.parse(data['due'])
                
                # Assume local timezone if none is specified in 'due' string
                if due_time.tzinfo is None or due_time.tzinfo.utcoffset(due_time) is None:
                    # Best-effort localization (assuming system local time)
                    due_time = due_time.astimezone(datetime.now().astimezone().tzinfo)
                    
                if due_time < datetime.now().astimezone():
                    print(f"\n🔔 Reminder Overdue: {name} (Due: {data['due']})")
                    print("-" * (len(name) + 20))
                    print(get_reminder_content(content))
                    
                    command = data.get('run_cmd')
                    if command:
                        print(f"\n[!] Executing command: {command}")
                        try:
                            # Use shlex to safely split the command string
                            process = subprocess.run(shlex.split(command), capture_output=True, text=True, timeout=10)
                            print(f"Command Output:\n{process.stdout}")
                            if process.stderr:
                                print(f"Command Error:\n{process.stderr}")
                            print(f"Command finished with exit code {process.returncode}")
                        except Exception as e:
                            print(f"❌ Error executing command: {e}")
                            
                    # Remove the reminder metadata after execution (if set to auto_remove)
                    if data.get('auto_remove', 'False').lower() == 'true':
                        print("\n[!] Auto-removing reminder metadata...")
                        new_lines = []
                        for line in content.split('\n'):
                            if not line.strip().startswith('#reminder:'):
                                new_lines.append(line)
                        notes[name] = '\n'.join(new_lines).strip()
                        save_notes(notes)
                    
                    reminders_run += 1
                    print("-" * (len(name) + 20))
                    
            except Exception as e:
                print(f"❌ Error parsing date for note {name}: {e}")
                
    if reminders_run == 0:
        print("No overdue reminders found.")

    return reminders_run

# -----------------
# TUI Logic (Curses)
# -----------------

class TUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.notes = load_notes()
        self.config = self._load_config()
        self.current_selection = 0
        self.filter_text = ""
        self.current_notes = self.get_filtered_notes()
        self._init_curses()

    def _load_config(self):
        """Loads configuration or returns default."""
        if not os.path.exists(CONFIG_FILE):
            return {"last_opened_note": None, "editor_cmd": "$EDITOR"}
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {"last_opened_note": None, "editor_cmd": "$EDITOR"}

    def _save_config(self):
        """Saves current configuration."""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self._log_error(f"Config Save Error: {e}")

    def _log_error(self, message):
        """Logs an error with a timestamp."""
        try:
            with open(ERROR_LOG, 'a') as f:
                f.write(f"[{datetime.now().isoformat()}] {message}\n")
        except Exception:
            pass # Failsafe

    def _init_curses(self):
        """Initializes curses settings."""
        curses.cbreak()
        curses.noecho()
        self.stdscr.keypad(True)
        try:
            curses.curs_set(0) # Hide cursor
        except curses.error:
            pass
            
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK) # Default
            curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Title
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Filter/Warning
            curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)  # Highlight background
            curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK) # Reminder
            curses.init_pair(6, curses.COLOR_RED, curses.COLOR_BLACK)   # Error/Overdue

    def get_filtered_notes(self):
        """Filters notes based on the current filter text."""
        notes = sorted(self.notes.keys(), key=str.lower)
        if not self.filter_text:
            return notes
            
        filter_lower = self.filter_text.lower()
        
        # Exact match / starts with
        filtered = [name for name in notes if name.lower().startswith(filter_lower)]
        # Contains
        filtered.extend([name for name in notes if filter_lower in name.lower() and name not in filtered])
        # Fuzzy match (similarity ratio)
        filtered.extend([
            name for name in notes 
            if name not in filtered and SequenceMatcher(None, filter_lower, name.lower()).ratio() > 0.3
        ])

        return filtered

    def _draw_main_screen(self):
        """Draws the main list screen."""
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        
        # 1. Title Bar
        title = " Smart Notes - TUI "
        self.stdscr.attron(curses.A_BOLD | curses.color_pair(2))
        self.stdscr.addstr(0, w//2 - len(title)//2, title)
        self.stdscr.addstr(0, 0, f"({len(self.current_notes)}/{len(self.notes)})")
        self.stdscr.attroff(curses.A_BOLD | curses.color_pair(2))
        
        # 2. Filter/Help Bar
        filter_text = f"Filter: {self.filter_text.ljust(w - 20)}"
        self.stdscr.attron(curses.A_REVERSE | curses.color_pair(3))
        self.stdscr.addstr(1, 0, filter_text)
        self.stdscr.addstr(1, w - 19, "h: Help / q: Quit")
        self.stdscr.attroff(curses.A_REVERSE | curses.color_pair(3))
        
        # 3. Note List
        display_start = max(0, self.current_selection - (h - 5) // 2)
        
        for idx in range(h - 3):
            list_index = display_start + idx
            y = 2 + idx
            
            if list_index >= len(self.current_notes):
                break
                
            note_name = self.current_notes[list_index]
            display_name = note_name.ljust(w - 1)
            
            is_selected = list_index == self.current_selection
            
            # Check for reminder status
            has_reminder = False
            is_overdue = False
            
            try:
                data = _parse_reminder_data(self.notes.get(note_name, ""))
                if 'due' in data:
                    has_reminder = True
                    due_time = dateparser.parse(data['due']).astimezone(datetime.now().astimezone().tzinfo)
                    if due_time < datetime.now().astimezone():
                        is_overdue = True
            except Exception:
                pass # Ignore parsing errors during draw

            # Set colors
            attr = curses.color_pair(1)
            if is_selected:
                attr = curses.A_BOLD | curses.color_pair(4)
            elif is_overdue:
                attr = curses.A_BOLD | curses.color_pair(6)
            elif has_reminder:
                attr = curses.color_pair(5)
            
            # Draw
            self.stdscr.attron(attr)
            self.stdscr.addstr(y, 0, display_name[:w-1])
            self.stdscr.attroff(attr)

        # 4. Status/Key Bindings Bar
        status_text = "ENTER: Open | d: Delete | a: Add/Edit | /: Filter | r: Reminders"
        self.stdscr.attron(curses.A_REVERSE)
        self.stdscr.addstr(h-1, 0, status_text.ljust(w))
        self.stdscr.attroff(curses.A_REVERSE)
        
        self.stdscr.refresh()

    def _handle_filter_input(self):
        """Allows user to enter filter text."""
        curses.curs_set(1) # Show cursor
        self.stdscr.nodelay(False) # Blocking input
        
        h, w = self.stdscr.getmaxyx()
        # Create a tiny window for input at the top
        input_win = curses.newwin(1, w - 8, 1, 8)
        input_win.attron(curses.A_REVERSE | curses.color_pair(3))
        
        inp = list(self.filter_text)
        
        while True:
            input_win.clear()
            display_text = ''.join(inp)
            input_win.addstr(0, 0, display_text[:w-9])
            input_win.refresh()
            
            ch = self.stdscr.getch()
            
            if ch in (10, 13): # Enter
                self.filter_text = ''.join(inp).strip()
                break
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                if inp:
                    inp.pop()
            elif ch == 27 or ch == ord('/'): # ESC or / cancels filter
                break
            elif 32 <= ch <= 126: # Printable characters
                inp.append(chr(ch))
        
        curses.curs_set(0)
        self.filter_text = ''.join(inp).strip()
        self.current_notes = self.get_filtered_notes()
        self.current_selection = 0
        self.stdscr.nodelay(True) # Non-blocking input again

    def _open_note_view(self, note_name):
        """Opens a read-only view of the note content."""
        h, w = self.stdscr.getmaxyx()
        
        # Prepare content
        content = self.notes.get(note_name, "NOTE NOT FOUND")
        display_content = [f"--- Note: {note_name} ---"]
        
        data = _parse_reminder_data(content)
        if data:
            display_content.append("--- Metadata ---")
            for k, v in data.items():
                display_content.append(f"  {k}: {v}")
            display_content.append("--- Content ---")
        
        display_content.append(get_reminder_content(content))
        
        # Handle scrolling
        scroll_pos = 0
        
        while True:
            self.stdscr.clear()
            
            # Title
            title = f" Note: {note_name} "
            self.stdscr.attron(curses.A_BOLD | curses.color_pair(2))
            self.stdscr.addstr(0, w//2 - len(title)//2, title)
            self.stdscr.attroff(curses.A_BOLD | curses.color_pair(2))
            
            # Content
            max_lines = h - 2
            for i in range(max_lines):
                line_index = scroll_pos + i
                y = 1 + i
                if line_index < len(display_content):
                    line = display_content[line_index][:w-1]
                    self.stdscr.addstr(y, 0, line)
                else:
                    break
                    
            # Status line
            status_text = "Scroll: UP/DOWN | q: Close | e: Edit"
            self.stdscr.attron(curses.A_REVERSE)
            self.stdscr.addstr(h-1, 0, status_text.ljust(w))
            self.stdscr.attroff(curses.A_REVERSE)
            
            self.stdscr.refresh()
            key = self.stdscr.getch()
            
            if key in (ord('q'), ord('Q'), 27): # q or ESC
                break
            elif key in (curses.KEY_UP, ord('k')):
                scroll_pos = max(0, scroll_pos - 1)
            elif key in (curses.KEY_DOWN, ord('j')):
                scroll_pos = min(len(display_content) - max_lines, scroll_pos + 1)
            elif key in (ord('e'), ord('E')):
                self._external_edit(note_name)
                # Re-load content after external edit
                self.notes = load_notes() 
                self.config['last_opened_note'] = note_name
                self._save_config()
                # Break and redraw main screen
                break 

        self.stdscr.clear()

    def _get_input(self, prompt, default=''):
        """Gets single-line input from user."""
        curses.curs_set(1)
        self.stdscr.nodelay(False)
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        
        input_win = curses.newwin(3, w-4, h//2 - 1, 2)
        input_win.box()
        
        # Center prompt
        p_x = w//2 - len(prompt)//2 - 2
        p_x = max(1, p_x)
        
        input_win.addstr(0, p_x, prompt, curses.A_BOLD | curses.color_pair(2))
        
        inp = list(default)
        pos = len(inp)
        
        while True:
            input_win.addstr(1, 1, ' ' * (w - 6)) # Clear input line
            display_text = ''.join(inp)
            
            # Check for max length
            max_len = w - 6
            start_index = max(0, pos - max_len)
            display_text = display_text[start_index:]
            
            input_win.addstr(1, 1, display_text, curses.A_BOLD)
            input_win.move(1, 1 + pos - start_index)
            input_win.refresh()
            
            try:
                ch = self.stdscr.getch()
            except:
                ch = -1
            
            if ch in (10, 13): # Enter
                curses.curs_set(0)
                self.stdscr.nodelay(True)
                return ''.join(inp).strip()
            elif ch in (3, 27): # Ctrl+C or ESC
                curses.curs_set(0)
                self.stdscr.nodelay(True)
                return None
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                if pos > 0:
                    inp.pop(pos - 1)
                    pos -= 1
            elif ch == curses.KEY_LEFT:
                pos = max(0, pos - 1)
            elif ch == curses.KEY_RIGHT:
                pos = min(len(inp), pos + 1)
            elif 32 <= ch <= 255:
                if len(inp) < 255: # Max 255 chars
                    inp.insert(pos, chr(ch))
                    pos += 1
            
    def _display_message(self, message):
        """Displays a message and waits for a keypress."""
        curses.curs_set(0)
        self.stdscr.nodelay(False)
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        
        lines = message.split('\n')
        
        # Center and display lines
        for i, line in enumerate(lines):
            y = h//2 - len(lines)//2 + i
            x = w//2 - len(line)//2
            if 0 <= y < h:
                try:
                    self.stdscr.addstr(y, x, line)
                except curses.error:
                    pass
                    
        # Wait for keypress message
        wait_msg = "Press any key to continue..."
        self.stdscr.attron(curses.A_REVERSE)
        self.stdscr.addstr(h-1, 0, wait_msg.ljust(w))
        self.stdscr.attroff(curses.A_REVERSE)
        
        self.stdscr.refresh()
        self.stdscr.getch()
        self.stdscr.nodelay(True)

    def _external_edit(self, note_name=None):
        """Launches external editor for a note."""
        
        # 1. Prepare temp file with current content
        temp_file = os.path.join(HOME, f".smart_notes_temp_{os.getpid()}.txt")
        initial_content = self.notes.get(note_name, "") if note_name else ""
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(initial_content)
        except Exception as e:
            self._display_message(f"Error preparing temp file: {e}")
            return
            
        # 2. Get editor command
        editor_cmd = self.config.get("editor_cmd", "$EDITOR")
        editor_cmd = os.environ.get('EDITOR', 'vi') if editor_cmd == '$EDITOR' else editor_cmd
        
        full_command = f"{editor_cmd} {shlex.quote(temp_file)}"

        # 3. Leave curses mode and launch editor
        curses.endwin()
        try:
            print(f"Launching external editor: {full_command}")
            subprocess.run(shlex.split(full_command), check=True)
            print("Editor closed. Reading new content...")
            
            # 4. Read content back
            with open(temp_file, 'r', encoding='utf-8') as f:
                new_content = f.read().strip()
            
            # 5. Handle saving
            if not note_name:
                # New note case
                name = input("Enter new note name: ").strip()
                if not name:
                    print("Canceled: Empty name.")
                    return
                if name in self.notes:
                    if input('Replace existing? (y/N): ').lower() != 'y':
                        print('Canceled.')
                        return
                
                self.notes[name] = new_content
                self.config['last_opened_note'] = name
            else:
                # Existing note case
                self.notes[note_name] = new_content
                self.config['last_opened_note'] = note_name
                
            save_notes(self.notes)
            self._save_config()
            print("Note saved.")

        except subprocess.CalledProcessError:
            print("Editor failed with an error. Note not saved.")
        except KeyboardInterrupt:
            print("\nEditing canceled by user.")
        except Exception as e:
            print(f"An error occurred during external edit: {e}")
            self._log_error(f"External Edit Error: {e}\n{traceback.format_exc()}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            # Re-initialize curses state
            self.stdscr = curses.initscr() 
            self._init_curses()
            
            # Re-filter/re-select
            self.current_notes = self.get_filtered_notes()
            if note_name:
                try:
                    self.current_selection = self.current_notes.index(note_name)
                except ValueError:
                    self.current_selection = 0

    def _delete_note(self, note_name):
        """Deletes a note after confirmation."""
        confirmation = self._get_input(f"Delete '{note_name}'? (Y/n): ", default='n')
        if confirmation and confirmation.lower() in ('y', 'yes'):
            del self.notes[note_name]
            save_notes(self.notes)
            if self.config.get('last_opened_note') == note_name:
                self.config['last_opened_note'] = None
                self._save_config()
                
            self.current_notes = self.get_filtered_notes()
            self.current_selection = min(self.current_selection, len(self.current_notes) - 1)
            self._display_message(f"Note '{note_name}' deleted.")
        else:
            self._display_message("Deletion canceled.")

    def _help_screen(self):
        """Displays the TUI help screen."""
        help_text = """
Smart Notes - Help

Key Bindings:
  UP/DOWN/k/j : Move selection
  ENTER       : Open/View selected note
  e (View)    : Edit selected note with external editor
  a           : Add a new note (launches external editor)
  d           : Delete selected note (with confirmation)
  /           : Start filtering the list
  r           : Run overdue reminders (checks all notes)
  q / ESC     : Quit the application
  h           : Show this help screen

Editor Configuration:
- Uses the environment variable $EDITOR (e.g., nano, vi).
- To change it, edit: ~/.smart_notes_config.json
  Example: {"editor_cmd": "nano"}

Reminder Format (Start of note):
#reminder:due: YYYY-MM-DD HH:MM:SS (e.g., 2025-10-20 18:00)
#reminder:run_cmd: command to execute (e.g., 'notify-send "Reminder"')
#reminder:auto_remove: True (removes metadata after command runs)

Files:
- Notes: ~/.smart_notes.json
- Config: ~/.smart_notes_config.json
- Error Log: ~/.smart_notes_error.log
"""
        self._display_message(help_text)

    def run(self):
        """Main TUI loop."""
        
        # Check for reminders on startup
        if run_reminders(auto_run=True) > 0:
            self._display_message("Overdue reminders were run. Press a key to continue to notes.")

        # Try to restore last selection
        last_note = self.config.get('last_opened_note')
        if last_note and last_note in self.current_notes:
            try:
                self.current_selection = self.current_notes.index(last_note)
            except ValueError:
                self.current_selection = 0
                
        self.stdscr.nodelay(True) # Non-blocking input

        while True:
            self._draw_main_screen()
            key = self.stdscr.getch()
            
            if key == curses.KEY_UP or key == ord('k'):
                self.current_selection = (self.current_selection - 1) % len(self.current_notes) if self.current_notes else 0
            elif key == curses.KEY_DOWN or key == ord('j'):
                self.current_selection = (self.current_selection + 1) % len(self.current_notes) if self.current_notes else 0
            elif key == curses.KEY_ENTER or key in [10, 13]: # ENTER
                if self.current_notes:
                    note_name = self.current_notes[self.current_selection]
                    self._open_note_view(note_name)
            elif key == ord('q') or key == ord('Q') or key == 27: # q or ESC
                break
            elif key == ord('a') or key == ord('A'):
                self._external_edit() # Add new note
            elif key == ord('d') or key == ord('D'):
                if self.current_notes:
                    self._delete_note(self.current_notes[self.current_selection])
            elif key == ord('h') or key == ord('H'):
                self._help_screen()
            elif key == ord('/'):
                self._handle_filter_input()
            elif key == ord('r') or key == ord('R'):
                run_reminders()
                self._display_message("Reminder check complete. Press a key to continue to notes.")
                self.notes = load_notes() # Refresh notes in case auto_remove was used

# -----------------
# Console/CLI Logic
# -----------------

def cli_add_note():
    """Adds a note via standard console input (for Termux widget/automation)."""
    notes = load_notes()
    name = input('Enter note name: ').strip()
    if not name:
        print('Canceled: empty name')
        return
    if name in notes:
        if input('Replace existing? (y/N): ').lower() not in ('y', 'yes'):
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
    print('  --add            -> add note via command line')
    print('  --run-reminders  -> execute overdue reminders')
    print('  --help           -> this help screen')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == '--add':
            cli_add_note()
        elif arg == '--run-reminders':
            run_reminders()
        elif arg == '--help':
            print_help()
        else:
            print(f"Unknown argument: {arg}. Use --help for usage.")
    else:
        # TUI Mode
        try:
            curses.wrapper(TUI)
        except curses.error as e:
            print(f"Error in TUI (curses): {e}. Falling back to console.")
            print("To add a note, use: python3 Smart\\ Notes.py --add")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            traceback.print_exc()
