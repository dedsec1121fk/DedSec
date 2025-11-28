#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import subprocess
import time
import shutil
import calendar
import shlex
import traceback
from datetime import datetime, timedelta
from difflib import SequenceMatcher

# Αρχεία Διαμόρφωσης
HOME = os.path.expanduser('~')
NOTES_FILE = os.path.join(HOME, '.smart_notes.json')
CONFIG_FILE = os.path.join(HOME, '.smart_notes_config.json')
ERROR_LOG = os.path.join(HOME, '.smart_notes_error.log')

# Βεβαιωθείτε ότι υπάρχουν τα αρχεία
for path, default in [(NOTES_FILE, {}), (CONFIG_FILE, {})]:
    if not os.path.exists(path):
        try:
            with open(path, 'w') as f:
                json.dump(default, f)
        except Exception:
            pass

# Προαιρετικές εξαρτήσεις
try:
    from dateutil import parser as dateparser
except Exception:
    dateparser = None

# Φόρτωση ζωνών ώρας
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
    # Χρησιμοποιήστε μια ελάχιστη προεπιλεγμένη λίστα αν δεν είναι εγκατεστημένα τα dateutil/pytz
        pass 
    return sorted([
        'UTC', 'Europe/Athens', 'Europe/London', 'Europe/Berlin', 'Europe/Paris',
        'America/New_York', 'America/Los_Angeles', 'Asia/Tokyo', 'Australia/Sydney'
    ])

TIMEZONES = load_timezones()

# -----------------
# Κεντρική Λογική Αρχείων
# -----------------

def load_notes():
    """Φορτώνει τις σημειώσεις από το αρχείο JSON."""
    if not os.path.exists(NOTES_FILE):
        return {}
    try:
        with open(NOTES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Σφάλμα φόρτωσης σημειώσεων: {e}. Εκκίνηση με κενό σύνολο.")
        return {}

def save_notes(notes):
    """Αποθηκεύει τις σημειώσεις στο αρχείο JSON."""
    try:
        with open(NOTES_FILE, 'w') as f:
            json.dump(notes, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης σημειώσεων: {e}")

def _load_config():
    """Φορτώνει τη διαμόρφωση ή επιστρέφει την προεπιλεγμένη."""
    if not os.path.exists(CONFIG_FILE):
        return {"last_opened_note": None, "editor_cmd": "$EDITOR"}
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {"last_opened_note": None, "editor_cmd": "$EDITOR"}

def _save_config(config):
    """Αποθηκεύει την τρέχουσα διαμόρφωση."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        _log_error(f"Σφάλμα Αποθήκευσης Διαμόρφωσης: {e}")

def _log_error(message):
    """Καταγράφει ένα σφάλμα με χρονική σήμανση."""
    try:
        with open(ERROR_LOG, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")
    except Exception:
        pass # Ασφαλής αποτυχία

# -----------------
# Λογική Υπενθυμίσεων
# -----------------

def _parse_reminder_data(note_content: str) -> dict:
    """Αναλύει τα μεταδεδομένα υπενθύμισης από την αρχή μιας σημείωσης."""
    data = {}
    lines = note_content.split('\n')
    for line in lines:
        if line.strip().startswith('#reminder:'):
            parts = line.split(':', 2)
            if len(parts) == 3:
                key = parts[1].strip()
                value = parts[2].strip()
                data[key] = value
        elif not line.strip(): # Σταματήστε στην πρώτη κενή γραμμή
            break
        elif not line.strip().startswith('#'): # Σταματήστε στην πρώτη μη-σχολιαστική/μη-κενή γραμμή
            break
    return data

def get_reminder_content(note_content: str) -> str:
    """Αφαιρεί τις γραμμές μεταδεδομένων από το περιεχόμενο της σημείωσης για εμφάνιση."""
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
    """Ελέγχει και εκτελεί τις ληξιπρόθεσμες υπενθυμίσεις."""
    notes = load_notes()
    reminders_run = 0
    
    if not dateparser:
        if auto_run: return 0 # Δεν μπορεί να εκτελεστεί χωρίς dateutil
        print('Δεν είναι δυνατή η εκτέλεση υπενθυμίσεων: Απαιτείται η βιβλιοθήκη dateutil.')
        print('Παρακαλώ εγκαταστήστε την με: pip install python-dateutil')
        return 0

    print("\n--- Έλεγχος Υπενθυμίσεων ---")
    
    # Λάβετε πληροφορίες τοπικής ζώνης ώρας
    local_tz = datetime.now().astimezone().tzinfo
    now_local = datetime.now().astimezone()
    
    notes_modified = False
    
    for name, content in notes.items():
        data = _parse_reminder_data(content)
        
        # Έλεγχος για ενεργοποίηση υπενθύμισης
        if 'due' in data:
            try:
                # Χρησιμοποιήστε τον dateparser για να χειριστείτε ευέλικτες μορφές ημερομηνίας
                due_time = dateparser.parse(data['due'])
                
                # Υποθέτουμε τοπική ζώνη ώρας αν δεν έχει καθοριστεί στη συμβολοσειρά 'due'
                if due_time.tzinfo is None or due_time.tzinfo.utcoffset(due_time) is None:
                    due_time = due_time.astimezone(local_tz)
                    
                if due_time < now_local:
                    print(f"\n🔔 Υπενθύμιση Ληξιπρόθεσμη: {name} (Λήξη: {data['due']})")
                    print("-" * (len(name) + 20))
                    print(get_reminder_content(content))
                    
                    command = data.get('run_cmd')
                    if command:
                        print(f"\n[!] Εκτέλεση εντολής: {command}")
                        try:
                            # Χρησιμοποιήστε shlex για ασφαλή διαχωρισμό της συμβολοσειράς εντολής
                            process = subprocess.run(shlex.split(command), capture_output=True, text=True, timeout=10)
                            print(f"Έξοδος Εντολής:\n{process.stdout}")
                            if process.stderr:
                                print(f"Σφάλμα Εντολής:\n{process.stderr}")
                            print(f"Η εντολή ολοκληρώθηκε με κωδικό εξόδου {process.returncode}")
                        except Exception as e:
                            print(f"❌ Σφάλμα κατά την εκτέλεση της εντολής: {e}")
                            
                    # Αφαιρέστε τα μεταδεδομένα υπενθύμισης μετά την εκτέλεση (αν έχει οριστεί auto_remove)
                    if data.get('auto_remove', 'False').lower() == 'true':
                        print("\n[!] Αυτόματη αφαίρεση μεταδεδομένων υπενθύμισης...")
                        new_lines = []
                        for line in content.split('\n'):
                            if not line.strip().startswith('#reminder:'):
                                new_lines.append(line)
                        notes[name] = '\n'.join(new_lines).strip()
                        notes_modified = True
                    
                    reminders_run += 1
                    print("-" * (len(name) + 20))
                    
            except Exception as e:
                print(f"❌ Σφάλμα ανάλυσης ημερομηνίας για τη σημείωση {name}: {e}")
    
    if notes_modified:
        save_notes(notes)

    if reminders_run == 0:
        print("Δεν βρέθηκαν ληξιπρόθεσμες υπενθυμίσεις.")
    
    print("--------------------------")
    
    return reminders_run

# -----------------
# Λογική Μενού Κονσόλας
# -----------------

class ConsoleApp:
    def __init__(self):
        self.notes = load_notes()
        self.config = _load_config()
        self.filter_text = ""
        self.current_notes = self._get_filtered_notes()

    def _get_filtered_notes(self, notes_dict=None):
        """Φιλτράρει τις σημειώσεις με βάση το τρέχον κείμενο φίλτρου."""
        if notes_dict is None:
            notes_dict = self.notes
            
        notes = sorted(notes_dict.keys(), key=str.lower)
        
        if not self.filter_text:
            return notes
            
        filter_lower = self.filter_text.lower()
        
        # Απλή αντιστοίχιση συμβολοσειράς
        filtered = [name for name in notes if filter_lower in name.lower()]
        
        return filtered

    def _update_notes_and_list(self):
        """Επαναφορτώνει τις σημειώσεις από το αρχείο και ενημερώνει τη φιλτραρισμένη λίστα."""
        self.notes = load_notes()
        self.current_notes = self._get_filtered_notes()

    def _external_edit(self, note_name=None):
        """Εκκινεί εξωτερικό επεξεργαστή για μια σημείωση."""
        
        # 1. Προετοιμάστε προσωρινό αρχείο με το τρέχον περιεχόμενο
        temp_file = os.path.join(HOME, f".smart_notes_temp_{os.getpid()}.txt")
        initial_content = self.notes.get(note_name, "") if note_name else ""
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(initial_content)
        except Exception as e:
            print(f"Σφάλμα προετοιμασίας προσωρινού αρχείου: {e}")
            return
            
        # 2. Λάβετε την εντολή επεξεργαστή
        editor_cmd = self.config.get("editor_cmd", "$EDITOR")
        editor_cmd = os.environ.get('EDITOR', 'vi') if editor_cmd == '$EDITOR' else editor_cmd
        
        full_command = f"{editor_cmd} {shlex.quote(temp_file)}"

        try:
            print(f"\nΕκκίνηση εξωτερικού επεξεργαστή: {full_command}")
            subprocess.run(shlex.split(full_command), check=True)
            print("Ο επεξεργαστής έκλεισε. Ανάγνωση νέου περιεχομένου...")
            
            # 3. Ανάγνωση περιεχομένου
            with open(temp_file, 'r', encoding='utf-8') as f:
                new_content = f.read().strip()
            
            # 4. Χειρισμός αποθήκευσης
            if not note_name:
                # Περίπτωση νέας σημείωσης
                name = input("Εισάγετε όνομα νέας σημείωσης: ").strip()
                if not name:
                    print("Ακυρώθηκε: Κενό όνομα.")
                    return
                if name in self.notes:
                    if input(f"Η σημείωση '{name}' υπάρχει ήδη. Αντικατάσταση υπάρχουσας; (y/N): ").lower() != 'y':
                        print('Ακυρώθηκε.')
                        return
                
                self.notes[name] = new_content
                self.config['last_opened_note'] = name
            else:
                # Περίπτωση υπάρχουσας σημείωσης
                self.notes[note_name] = new_content
                self.config['last_opened_note'] = note_name
                
            save_notes(self.notes)
            _save_config(self.config)
            print("Η σημείωση αποθηκεύτηκε.")

        except subprocess.CalledProcessError:
            print("Ο επεξεργαστής απέτυχε με σφάλμα. Η σημείωση δεν αποθηκεύτηκε.")
        except KeyboardInterrupt:
            print("\nΗ επεξεργασία ακυρώθηκε από τον χρήστη.")
        except Exception as e:
            print(f"Προέκυψε σφάλμα κατά την εξωτερική επεξεργασία: {e}")
            _log_error(f"Σφάλμα Εξωτερικής Επεξεργασίας: {e}\n{traceback.format_exc()}")
        finally:
            # Εκκαθάριση προσωρινού αρχείου
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            self._update_notes_and_list()

    def _delete_note(self, note_name):
        """Διαγράφει μια σημείωση μετά από επιβεβαίωση."""
        confirmation = input(f"Είστε σίγουροι ότι θέλετε να ΔΙΑΓΡΑΨΕΤΕ τη σημείωση '{note_name}'; (Y/n): ").strip()
        if confirmation.lower() in ('y', 'yes'):
            if note_name in self.notes:
                del self.notes[note_name]
                save_notes(self.notes)
                if self.config.get('last_opened_note') == note_name:
                    self.config['last_opened_note'] = None
                    _save_config(self.config)
                
                print(f"Η σημείωση '{note_name}' διαγράφηκε.")
            else:
                print(f"Η σημείωση '{note_name}' δεν βρέθηκε.")
            self._update_notes_and_list()
        else:
            print("Η διαγραφή ακυρώθηκε.")

    def _view_note(self, note_name):
        """Εμφανίζει το περιεχόμενο της σημείωσης και προσφέρει επιλογές επεξεργασίας/διαγραφής."""
        note_content = self.notes.get(note_name, "ΣΗΜΕΙΩΣΗ ΔΕΝ ΒΡΕΘΗΚΕ")
        
        print("\n" + "="*50)
        print(f"Σημείωση: {note_name}")
        print("="*50)
        
        data = _parse_reminder_data(note_content)
        if data:
            print("--- ΜΕΤΑΔΕΔΟΜΕΝΑ ---")
            for k, v in data.items():
                print(f"  {k}: {v}")
            print("--- ΠΕΡΙΕΧΟΜΕΝΟ ---")
        
        print(get_reminder_content(note_content))
        print("="*50)
        
        # Υπο-μενού
        while True:
            action = input("Ενέργειες: (e)πεξεργασία, (d)ιαγραφή, (b)πίσω στη λίστα: ").strip().lower()
            if action in ('e', 'ε'):
                self._external_edit(note_name)
                # Μετά την επεξεργασία, η λίστα σημειώσεων ανανεώνεται, επιστρέψτε στο κύριο μενού
                return
            elif action in ('d', 'δ'):
                self._delete_note(note_name)
                # Μετά τη διαγραφή, επιστρέψτε στο κύριο μενού
                return
            elif action in ('b', 'π'):
                break
            else:
                print("Μη έγκυρη ενέργεια. Παρακαλώ εισάγετε 'e', 'd', ή 'b'.")

    def _display_main_menu(self):
        """Εμφανίζει την κύρια λίστα σημειώσεων."""
        print("\n" + "#"*40)
        print(f" ΕΞΥΠΝΕΣ ΣΗΜΕΙΩΣΕΙΣ ({len(self.current_notes)}/{len(self.notes)})")
        print("#"*40)
        
        if self.filter_text:
            print(f"Τρέχον Φίλτρο: **{self.filter_text}** (d-καθαρισμός φίλτρου)")
        
        if not self.current_notes:
            print("Δεν βρέθηκαν σημειώσεις που να ταιριάζουν με το φίλτρο.")
            print("---")

        for i, name in enumerate(self.current_notes):
            # Έλεγχος για κατάσταση υπενθύμισης
            prefix = " "
            try:
                data = _parse_reminder_data(self.notes.get(name, ""))
                if 'due' in data:
                    prefix = "🔔"
                    if dateparser:
                        due_time = dateparser.parse(data['due']).astimezone(datetime.now().astimezone().tzinfo)
                        if due_time < datetime.now().astimezone():
                            prefix = "🔴" # Ληξιπρόθεσμη
            except Exception:
                pass # Αγνοήστε σφάλματα ανάλυσης για την εμφάνιση
                
            print(f"{i+1:3}. {prefix} {name}")
            
        print("---")
        print("Μενού: (1-n) Επιλογή Σημείωσης | (a)προσθήκη | (f)ίλτρο | (r)υπενθυμίσεις | (h)βοήθεια | (q)έξοδος")

    def _handle_filter_input(self):
        """Επιτρέπει στον χρήστη να εισάγει κείμενο φίλτρου."""
        new_filter = input(f"Εισάγετε κείμενο φίλτρου (Τρέχον: '{self.filter_text}'): ").strip()
        if new_filter:
            self.filter_text = new_filter
        elif new_filter == "" and self.filter_text:
            if input("Εκκαθάριση τρέχοντος φίλτρου; (y/N): ").lower() == 'y':
                self.filter_text = ""
            
        self.current_notes = self._get_filtered_notes()

    def _help_screen(self):
        """Εμφανίζει την οθόνη βοήθειας."""
        print("""
==================================================
Εύχρηστες Σημειώσεις - Βοήθεια Κονσόλας
==================================================
Εντολές:
  (1-n) : Επιλογή σημείωσης από τη λίστα
  a     : Προσθήκη νέας σημείωσης (εκκινεί εξωτερικό επεξεργαστή)
  f     : Ορισμός ή αλλαγή του κειμένου φίλτρου για τη λίστα σημειώσεων
  d     : Εκκαθάριση του τρέχοντος φίλτρου (διαθέσιμο μόνο αν υπάρχει ενεργό φίλτρο)
  r     : Εκτέλεση ληξιπρόθεσμων υπενθυμίσεων (ελέγχει όλες τις σημειώσεις και εκτελεί εντολές)
  h     : Εμφάνιση αυτής της οθόνης βοήθειας
  q     : Έξοδος από την εφαρμογή

Διαμόρφωση Επεξεργαστή:
- Χρησιμοποιεί την μεταβλητή περιβάλλοντος $EDITOR (π.χ. nano, vi) ως προεπιλογή.
- Για να την αλλάξετε, επεξεργαστείτε: ~/.smart_notes_config.json
  Παράδειγμα: {"editor_cmd": "nano"}

Μορφή Υπενθύμισης (Αρχή σημείωσης):
#reminder:due: ΕΤΟΣ-ΜΗΝΑΣ-ΗΜΕΡΑ ΩΩ:ΛΛ:ΔΔ (π.χ. 2025-10-20 18:00)
#reminder:run_cmd: εντολή προς εκτέλεση (π.χ. 'notify-send "Υπενθύμιση"')
#reminder:auto_remove: True (αφαιρεί τα μεταδεδομένα μετά την εκτέλεση της εντολής)

Αρχεία:
- Σημειώσεις: ~/.smart_notes.json
- Διαμόρφωση: ~/.smart_notes_config.json
- Αρχείο Καταγραφής Σφαλμάτων: ~/.smart_notes_error.log
==================================================
""")
        input("Πατήστε Enter για να συνεχίσετε...")

    def run(self):
        """Κύριος βρόχος κονσόλας."""
        
        # Έλεγχος για υπενθυμίσεις κατά την εκκίνηση
        if run_reminders(auto_run=True) > 0:
            input("Οι ληξιπρόθεσμες υπενθυμίσεις εκτελέστηκαν. Πατήστε Enter για να συνεχίσετε στις σημειώσεις.")
            self._update_notes_and_list()

        while True:
            self._display_main_menu()
            
            try:
                choice = input("Εισάγετε εντολή ή αριθμό σημείωσης: ").strip()
            except EOFError:
                print("\nΈξοδος από τις Έξυπνες Σημειώσεις.")
                break
            
            if not choice:
                continue

            # Χειρισμός εντολών μενού
            if choice.lower() in ('q', 'εξοδος'):
                print("Έξοδος από τις Έξυπνες Σημειώσεις.")
                break
            elif choice.lower() in ('a', 'προσθηκη'):
                self._external_edit() # Προσθήκη νέας σημείωσης
            elif choice.lower() in ('f', 'φιλτρο'):
                self._handle_filter_input()
            elif choice.lower() in ('d', 'καθαρισμος') and self.filter_text:
                self.filter_text = ""
                self._update_notes_and_list()
                print("Το φίλτρο καθαρίστηκε.")
            elif choice.lower() in ('r', 'υπενθυμισεις'):
                run_reminders()
                self._update_notes_and_list() # Ανανέωση σε περίπτωση που χρησιμοποιήθηκε auto_remove
            elif choice.lower() in ('h', 'βοηθεια'):
                self._help_screen()
            else:
                # Υποθέτουμε επιλογή αριθμού σημείωσης
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(self.current_notes):
                        note_name = self.current_notes[index]
                        self._view_note(note_name)
                    else:
                        print(f"Μη έγκυρος αριθμός σημείωσης: {choice}")
                except ValueError:
                    print(f"Μη έγκυρη εντολή ή αριθμός σημείωσης: {choice}")


# -----------------
# Λογική CLI
# -----------------

def cli_add_note():
    """Προσθέτει μια σημείωση μέσω τυπικής εισόδου κονσόλας (για Termux widget/automation)."""
    notes = load_notes()
    name = input('Εισάγετε όνομα νέας σημείωσης: ').strip()
    if not name:
        print('Ακυρώθηκε: κενό όνομα')
        return
    if name in notes:
        if input('Αντικατάσταση υπάρχουσας; (y/N): ').lower() not in ('y', 'yes'):
            print('Ακυρώθηκε')
            return
    
    print('Εκκίνηση εισόδου πολλαπλών γραμμών. Εισάγετε μια γραμμή που περιέχει μόνο ".save" για ολοκλήρωση και αποθήκευση.')
    try:
        lines = []
        while True:
            ln = sys.stdin.readline()
            if not ln: # Χειρισμός EOF
                break
            if ln.strip() == '.save':
                break
            lines.append(ln.rstrip('\n'))
        
        new = '\n'.join(lines)
        if not new.strip():
             if input('Το περιεχόμενο της σημείωσης είναι κενό. Αποθήκευση ούτως ή άλλως; (y/N): ').lower() != 'y':
                print('Ακυρώθηκε: Κενό περιεχόμενο.')
                return
             
    except KeyboardInterrupt:
        print('\nΑκυρώθηκε')
        return
        
    notes[name] = new
    save_notes(notes)
    print(f"Η σημείωση '{name}' αποθηκεύτηκε.")

# Βοήθεια για ορίσματα CLI
def print_cli_help():
    print('Έξυπνες Σημειώσεις - CLI/Κονσόλα')
    print('Χρήση: python3 Smart\\ Notes.py [ΕΝΤΟΛΗ]')
    print('Εντολές:')
    print('  (χωρίς ορίσματα) -> Εκκινεί διαδραστικό μενού κονσόλας')
    print('  --add            -> Προσθήκη σημείωσης μέσω γραμμής εντολών (χρησιμοποιεί διαδραστική είσοδο πολλαπλών γραμμών)')
    print('  --run-reminders  -> Εκτέλεση ληξιπρόθεσμων υπενθυμίσεων και εκτύπωση εξόδου')
    print('  --help           -> Αυτή η οθόνη βοήθειας')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == '--add':
            cli_add_note()
        elif arg == '--run-reminders':
            run_reminders()
        elif arg == '--help':
            print_cli_help()
        else:
            print(f"Άγνωστο όρισμα: {arg}. Χρησιμοποιήστε --help για βοήθεια.")
    else:
        # Λειτουργία Μενού Κονσόλας
        try:
            app = ConsoleApp()
            app.run()
        except KeyboardInterrupt:
            print("\nΈξοδος από τις Έξυπνες Σημειώσεις.")
        except Exception as e:
            print(f"Προέκυψε ένα απροσδόκητο σφάλμα: {e}")
            traceback.print_exc()