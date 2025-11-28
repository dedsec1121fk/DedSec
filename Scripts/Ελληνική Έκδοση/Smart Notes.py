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

HOME = os.path.expanduser('~')
NOTES_FILE = os.path.join(HOME, '.smart_notes.json')
CONFIG_FILE = os.path.join(HOME, '.smart_notes_config.json')
ERROR_LOG = os.path.join(HOME, '.smart_notes_error.log')

# Βεβαιωθείτε ότι τα αρχεία υπάρχουν
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
        pass
    return sorted([
        'UTC', 'Europe/Athens', 'Europe/London', 'Europe/Berlin', 'Europe/Paris',
        'America/New_York', 'America/Los_Angeles', 'Asia/Tokyo', 'Australia/Sydney'
    ])

TIMEZONES = load_timezones()

# -----------------
# Βασική Λογική Αρχείων
# -----------------

def load_notes():
    """Φορτώνει τις σημειώσεις από το αρχείο JSON."""
    if not os.path.exists(NOTES_FILE):
        return {}
    try:
        with open(NOTES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Σφάλμα φόρτωσης σημειώσεων: {e}. Ξεκινάμε με κενό σύνολο.")
        return {}

def save_notes(notes):
    """Αποθηκεύει τις σημειώσεις στο αρχείο JSON."""
    try:
        with open(NOTES_FILE, 'w') as f:
            json.dump(notes, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης σημειώσεων: {e}")

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
        elif not line.strip(): # Σταματά στην πρώτη κενή γραμμή
            break
        elif not line.strip().startswith('#'): # Σταματά στην πρώτη μη-σχόλιο/μη-κενή γραμμή
            break
    return data

def get_reminder_content(note_content: str) -> str:
    """Αφαιρεί τις γραμμές μεταδεδομένων από το περιεχόμενο σημείωσης για εμφάνιση."""
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
    """Ελέγχει και εκτελεί εκπρόθεσμες υπενθυμίσεις."""
    notes = load_notes()
    reminders_run = 0
    
    if not dateparser:
        if auto_run: return # Δεν μπορεί να τρέξει χωρίς dateutil
        print('Δεν μπορώ να εκτελέσω υπενθυμίσεις: Απαιτείται η βιβλιοθήκη dateutil.')
        print('Παρακαλώ εγκαταστήστε την με: pip install python-dateutil')
        return

    print("\n--- Έλεγχος Υπενθυμίσεων ---")
    
    for name, content in notes.items():
        data = _parse_reminder_data(content)
        
        # Έλεγχος για ενεργοποίηση υπενθύμισης
        if 'due' in data:
            try:
                # Χρήση dateparser για ευέλικτη ανάλυση μορφών ημερομηνιών
                due_time = dateparser.parse(data['due'])
                
                # Υπόθεση τοπικής ζώνης ώρας αν δεν έχει καθοριστεί στο string 'due'
                if due_time.tzinfo is None or due_time.tzinfo.utcoffset(due_time) is None:
                    # Εντοπισμός (υποθέτοντας τοπική ώρα συστήματος)
                    due_time = due_time.astimezone(datetime.now().astimezone().tzinfo)
                    
                if due_time < datetime.now().astimezone():
                    print(f"\n🔔 Εκπρόθεσμη Υπενθύμιση: {name} (Προθεσμία: {data['due']})")
                    print("-" * (len(name) + 25))
                    print(get_reminder_content(content))
                    
                    command = data.get('run_cmd')
                    if command:
                        print(f"\n[!] Εκτέλεση εντολής: {command}")
                        try:
                            # Χρήση shlex για ασφαλή διαχωρισμό string εντολής
                            process = subprocess.run(shlex.split(command), capture_output=True, text=True, timeout=10)
                            print(f"Έξοδος Εντολής:\n{process.stdout}")
                            if process.stderr:
                                print(f"Σφάλμα Εντολής:\n{process.stderr}")
                            print(f"Η εντολή ολοκληρώθηκε με κωδικό εξόδου {process.returncode}")
                        except Exception as e:
                            print(f"❌ Σφάλμα εκτέλεσης εντολής: {e}")
                            
                    # Αφαίρεση μεταδεδομένων υπενθύμισης μετά την εκτέλεση (αν έχει οριστεί auto_remove)
                    if data.get('auto_remove', 'False').lower() == 'true':
                        print("\n[!] Αυτόματη αφαίρεση μεταδεδομένων υπενθύμισης...")
                        new_lines = []
                        for line in content.split('\n'):
                            if not line.strip().startswith('#reminder:'):
                                new_lines.append(line)
                        notes[name] = '\n'.join(new_lines).strip()
                        save_notes(notes)
                    
                    reminders_run += 1
                    print("-" * (len(name) + 25))
                    
            except Exception as e:
                print(f"❌ Σφάλμα ανάλυσης ημερομηνίας για σημείωση {name}: {e}")
                
    if reminders_run == 0:
        print("Δεν βρέθηκαν εκπρόθεσμες υπενθυμίσεις.")

    return reminders_run

# -----------------
# Λογική Απλής Αριθμημένης Διεπαφής
# -----------------

class SimpleTUI:
    def __init__(self):
        self.notes = load_notes()
        self.config = self._load_config()
        self.filter_text = ""
        self.current_notes = self.get_filtered_notes()

    def _load_config(self):
        """Φορτώνει τη διαμόρφωση ή επιστρέφει την προεπιλεγμένη."""
        if not os.path.exists(CONFIG_FILE):
            return {"last_opened_note": None, "editor_cmd": "$EDITOR"}
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {"last_opened_note": None, "editor_cmd": "$EDITOR"}

    def _save_config(self):
        """Αποθηκεύει την τρέχουσα διαμόρφωση."""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self._log_error(f"Σφάλμα Αποθήκευσης Διαμόρφωσης: {e}")

    def _log_error(self, message):
        """Καταγράφει ένα σφάλμα με χρονική σήμανση."""
        try:
            with open(ERROR_LOG, 'a') as f:
                f.write(f"[{datetime.now().isoformat()}] {message}\n")
        except Exception:
            pass # Ασφάλεια

    def get_filtered_notes(self):
        """Φιλτράρει σημειώσεις βάσει του τρέχοντος κειμένου φίλτρου."""
        notes = sorted(self.notes.keys(), key=str.lower)
        if not self.filter_text:
            return notes
            
        filter_lower = self.filter_text.lower()
        
        # Ακριβές ταίριασμα / ξεκινά με
        filtered = [name for name in notes if name.lower().startswith(filter_lower)]
        # Περιέχει
        filtered.extend([name for name in notes if filter_lower in name.lower() and name not in filtered])
        # Ασαφές ταίριασμα (λόγος ομοιότητας)
        filtered.extend([
            name for name in notes 
            if name not in filtered and SequenceMatcher(None, filter_lower, name.lower()).ratio() > 0.3
        ])

        return filtered

    def _display_main_screen(self):
        """Εμφανίζει την κύρια οθόνη λίστας."""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # Τίτλος
        print("=" * 60)
        print(" " * 20 + "Έξυπνες Σημειώσεις" + " " * 20)
        print("=" * 60)
        print(f"Σημειώσεις: {len(self.current_notes)}/{len(self.notes)}")
        
        if self.filter_text:
            print(f"Φίλτρο: {self.filter_text}")
        
        print("-" * 60)
        
        # Λίστα Σημειώσεων με αριθμούς
        if not self.current_notes:
            print("Δεν βρέθηκαν σημειώσεις.")
        else:
            for idx, note_name in enumerate(self.current_notes, 1):
                # Έλεγχος κατάστασης υπενθύμισης
                has_reminder = False
                is_overdue = False
                
                try:
                    data = _parse_reminder_data(self.notes.get(note_name, ""))
                    if 'due' in data:
                        has_reminder = True
                        if dateparser:
                            due_time = dateparser.parse(data['due']).astimezone(datetime.now().astimezone().tzinfo)
                            if due_time < datetime.now().astimezone():
                                is_overdue = True
                except Exception:
                    pass
                
                # Μορφοποίηση εμφάνισης με δείκτες
                indicator = ""
                if is_overdue:
                    indicator = " [ΕΚΠΡΟΘΕΣΜΗ!]"
                elif has_reminder:
                    indicator = " [ΥΠΕΝΘΥΜΙΣΗ]"
                
                print(f"{idx:2d}. {note_name}{indicator}")
        
        print("-" * 60)
        print("Εντολές: αριθμός=Άνοιγμα | π=Προσθήκη | δ=Διαγραφή | φ=Φίλτρο | υ=Υπενθυμίσεις | β=Βοήθεια | ε=Έξοδος")
        print("-" * 60)

    def _open_note_view(self, note_name):
        """Ανοίγει μια προβολή μόνο ανάγνωσης του περιεχομένου της σημείωσης."""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        content = self.notes.get(note_name, "Η ΣΗΜΕΙΩΣΗ ΔΕΝ ΒΡΕΘΗΚΕ")
        
        print("=" * 60)
        print(f"Σημείωση: {note_name}")
        print("=" * 60)
        
        data = _parse_reminder_data(content)
        if data:
            print("--- Μεταδεδομένα ---")
            for k, v in data.items():
                print(f"  {k}: {v}")
            print("--- Περιεχόμενο ---")
        
        print(get_reminder_content(content))
        print("=" * 60)
        input("Πατήστε Enter για συνέχεια...")

    def _external_edit(self, note_name=None):
        """Εκκινεί εξωτερικό επεξεργαστή για μια σημείωση."""
        
        # 1. Προετοιμασία προσωρινού αρχείου με τρέχον περιεχόμενο
        temp_file = os.path.join(HOME, f".smart_notes_temp_{os.getpid()}.txt")
        initial_content = self.notes.get(note_name, "") if note_name else ""
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(initial_content)
        except Exception as e:
            print(f"Σφάλμα προετοιμασίας προσωρινού αρχείου: {e}")
            return
            
        # 2. Λήψη εντολής επεξεργαστή
        editor_cmd = self.config.get("editor_cmd", "$EDITOR")
        editor_cmd = os.environ.get('EDITOR', 'vi') if editor_cmd == '$EDITOR' else editor_cmd
        
        full_command = f"{editor_cmd} {shlex.quote(temp_file)}"

        # 3. Εκκίνηση επεξεργαστή
        try:
            print(f"Εκκίνηση εξωτερικού επεξεργαστή: {full_command}")
            subprocess.run(shlex.split(full_command), check=True)
            print("Ο επεξεργαστής έκλεισε. Ανάγνωση νέου περιεχομένου...")
            
            # 4. Ανάγνωση περιεχομένου πίσω
            with open(temp_file, 'r', encoding='utf-8') as f:
                new_content = f.read().strip()
            
            # 5. Χειρισμός αποθήκευσης
            if not note_name:
                # Περίπτωση νέας σημείωσης
                name = input("Εισάγετε όνομα νέας σημείωσης: ").strip()
                if not name:
                    print("Ακυρώθηκε: Κενό όνομα.")
                    return
                if name in self.notes:
                    if input('Αντικατάσταση υπάρχουσας; (ν/Ο): ').lower() != 'ν':
                        print('Ακυρώθηκε.')
                        return
                
                self.notes[name] = new_content
                self.config['last_opened_note'] = name
            else:
                # Περίπτωση υπάρχουσας σημείωσης
                self.notes[note_name] = new_content
                self.config['last_opened_note'] = note_name
                
            save_notes(self.notes)
            self._save_config()
            print("Η σημείωση αποθηκεύτηκε.")

        except subprocess.CalledProcessError:
            print("Ο επεξεργαστής απέτυχε με σφάλμα. Η σημείωση δεν αποθηκεύτηκε.")
        except KeyboardInterrupt:
            print("\nΗ επεξεργασία ακυρώθηκε από τον χρήστη.")
        except Exception as e:
            print(f"Παρουσιάστηκε σφάλμα κατά την εξωτερική επεξεργασία: {e}")
            self._log_error(f"Σφάλμα Εξωτερικής Επεξεργασίας: {e}\n{traceback.format_exc()}")
        finally:
            # Καθαρισμός προσωρινού αρχείου
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            # Επαν-φιλτράρισμα/επαν-επιλογή
            self.current_notes = self.get_filtered_notes()

    def _delete_note(self, note_name):
        """Διαγράφει μια σημείωση μετά από επιβεβαίωση."""
        confirmation = input(f"Διαγραφή '{note_name}'; (ν/Ο): ").strip().lower()
        if confirmation in ('ν', 'ναι'):
            del self.notes[note_name]
            save_notes(self.notes)
            if self.config.get('last_opened_note') == note_name:
                self.config['last_opened_note'] = None
                self._save_config()
                
            self.current_notes = self.get_filtered_notes()
            print(f"Η σημείωση '{note_name}' διαγράφηκε.")
        else:
            print("Η διαγραφή ακυρώθηκε.")
        input("Πατήστε Enter για συνέχεια...")

    def _help_screen(self):
        """Εμφανίζει την οθόνη βοήθειας."""
        os.system('clear' if os.name == 'posix' else 'cls')
        help_text = """
Έξυπνες Σημειώσεις - Βοήθεια

Εντολές:
  αριθμός    : Άνοιγμα/Προβολή επιλεγμένης σημείωσης (π.χ., '1' για πρώτη σημείωση)
  π          : Προσθήκη νέας σημείωσης (εκκινεί εξωτερικό επεξεργαστή)
  δ αριθμός  : Διαγραφή επιλεγμένης σημείωσης (π.χ., 'δ 1' για διαγραφή πρώτης σημείωσης)
  φ          : Ορισμός κειμένου φίλτρου
  υ          : Εκτέλεση εκπρόθεσμων υπενθυμίσεων (ελέγχει όλες τις σημειώσεις)
  ε          : Έξοδος από την εφαρμογή
  β          : Εμφάνιση αυτής της οθόνης βοήθειας

Διαμόρφωση Επεξεργαστή:
- Χρησιμοποιεί τη μεταβλητή περιβάλλοντος $EDITOR (π.χ., nano, vi).
- Για αλλαγή, επεξεργαστείτε: ~/.smart_notes_config.json
  Παράδειγμα: {"editor_cmd": "nano"}

Μορφή Υπενθύμισης (Αρχή σημείωσης):
#reminder:due: ΕΕΕΕ-ΜΜ-ΗΗ ΩΩ:ΛΛ:ΔΔ (π.χ., 2025-10-20 18:00)
#reminder:run_cmd: εντολή προς εκτέλεση (π.χ., 'notify-send "Υπενθύμιση"')
#reminder:auto_remove: True (αφαιρεί τα μεταδεδομένα μετά την εκτέλεση)

Αρχεία:
- Σημειώσεις: ~/.smart_notes.json
- Διαμόρφωση: ~/.smart_notes_config.json
- Αρχείο Σφαλμάτων: ~/.smart_notes_error.log
"""
        print(help_text)
        input("Πατήστε Enter για συνέχεια...")

    def run(self):
        """Κύριος βρόχος διεπαφής."""
        
        # Έλεγχος για υπενθυμίσεις κατά την εκκίνηση
        if run_reminders(auto_run=True) > 0:
            input("Εκτελέστηκαν εκπρόθεσμες υπενθυμίσεις. Πατήστε Enter για συνέχεια στις σημειώσεις.")

        while True:
            self._display_main_screen()
            command = input("Εισάγετε εντολή: ").strip().lower()
            
            if command == 'ε':
                break
            elif command == 'π':
                self._external_edit() # Προσθήκη νέας σημείωσης
            elif command == 'β':
                self._help_screen()
            elif command == 'φ':
                self.filter_text = input("Εισάγετε κείμενο φίλτρου: ").strip()
                self.current_notes = self.get_filtered_notes()
            elif command == 'υ':
                run_reminders()
                input("Ο έλεγχος υπενθυμίσεων ολοκληρώθηκε. Πατήστε Enter για συνέχεια στις σημειώσεις.")
                self.notes = load_notes() # Ανανέωση σημειώσεων σε περίπτωση χρήσης auto_remove
            elif command.startswith('δ '):
                # Διαγραφή με αριθμό: "δ 1"
                try:
                    num = int(command[2:].strip())
                    if 1 <= num <= len(self.current_notes):
                        note_name = self.current_notes[num - 1]
                        self._delete_note(note_name)
                    else:
                        print("Μη έγκυρος αριθμός σημείωσης.")
                        input("Πατήστε Enter για συνέχεια...")
                except ValueError:
                    print("Μη έγκυρη μορφή. Χρησιμοποιήστε 'δ αριθμός' (π.χ., 'δ 1')")
                    input("Πατήστε Enter για συνέχεια...")
            elif command.isdigit():
                # Άνοιγμα σημείωσης με αριθμό
                num = int(command)
                if 1 <= num <= len(self.current_notes):
                    note_name = self.current_notes[num - 1]
                    self._open_note_view(note_name)
                else:
                    print("Μη έγκυρος αριθμός σημείωσης.")
                    input("Πατήστε Enter για συνέχεια...")
            else:
                print("Άγνωστη εντολή. Πληκτρολογήστε 'β' για βοήθεια.")
                input("Πατήστε Enter για συνέχεια...")

# -----------------
# Λογική Κονσόλας/Γραμμής Εντολών
# -----------------

def cli_add_note():
    """Προσθέτει μια σημείωση μέσω τυπικής εισαγωγής κονσόλας (για widget/αυτοματοποίηση Termux)."""
    notes = load_notes()
    name = input('Εισάγετε όνομα σημείωσης: ').strip()
    if not name:
        print('Ακυρώθηκε: κενό όνομα')
        return
    if name in notes:
        if input('Αντικατάσταση υπάρχουσας; (ν/Ο): ').lower() not in ('ν', 'ναι'):
            print('Ακυρώθηκε')
            return
    print('Εκκίνηση επεξεργαστή. Τερματισμός με γραμμή που περιέχει μόνο .save')
    try:
        lines = []
        while True:
            ln = input()
            if ln.strip() == '.save':
                break
            lines.append(ln)
        new = '\n'.join(lines)
    except KeyboardInterrupt:
        print('\nΑκυρώθηκε')
        return
    notes[name] = new
    save_notes(notes)
    print('Αποθηκεύτηκε.')

# Βοήθεια
def print_help():
    print('Έξυπνες Σημειώσεις - Termux')
    print('Εντολές:')
    print('  (χωρίς ορίσματα) -> απλή αριθμημένη διεπαφή')
    print('  --add            -> προσθήκη σημείωσης μέσω γραμμής εντολών')
    print('  --run-reminders  -> εκτέλεση εκπρόθεσμων υπενθυμίσεων')
    print('  --help           -> αυτή η οθόνη βοήθειας')

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
            print(f"Άγνωστο όρισμα: {arg}. Χρησιμοποιήστε --help για χρήση.")
    else:
        # Λειτουργία Απλής Αριθμημένης Διεπαφής
        try:
            tui = SimpleTUI()
            tui.run()
        except KeyboardInterrupt:
            print("\nΑντίο!")
        except Exception as e:
            print(f"Παρουσιάστηκε μη αναμενόμενο σφάλμα: {e}")
            traceback.print_exc()