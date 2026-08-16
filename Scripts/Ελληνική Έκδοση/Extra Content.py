import os
import shutil

def main():
    # Λήψη του αρχικού καταλόγου του χρήστη στο Termux
    home = os.path.expanduser("~")
    
    # Ορισμός της διαδρομής του φακέλου προέλευσης (συμπεριλαμβανομένου του ίδιου του φακέλου)
    source_folder = os.path.join(home, "DedSec", "Extra Content")
    
    # Ορισμός του φακέλου προορισμού όπου θα αντιγραφεί ολόκληρος ο φάκελος
    destination_folder = os.path.join(home, "storage", "downloads", "Extra Content")
    
    # Έλεγχος αν υπάρχει ο φάκελος προέλευσης
    if not os.path.exists(source_folder):
        print(f"[X] Ο φάκελος προέλευσης δεν βρέθηκε: {source_folder}")
        return
    
    # Δημιουργία του φακέλου προορισμού αν δεν υπάρχει
    # Η shutil.copytree μπορεί να δημιουργήσει τον φάκελο, αλλά θα εξασφαλίσουμε ότι ο γονικός του υπάρχει
    parent_destination = os.path.join(home, "storage", "downloads")
    if not os.path.exists(parent_destination):
        print(f"[X] Ο γονικός φάκελος προορισμού δεν βρέθηκε: {parent_destination}")
        return
    
    try:
        # Αντιγραφή ολόκληρου του φακέλου (συμπεριλαμβανομένου του ονόματος και όλου του περιεχομένου του)
        shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)
        print(f"[✓] Η εξαγωγή ολοκληρώθηκε! Ο φάκελος 'Extra Content' έχει αντιγραφεί στη διαδρομή: {destination_folder}")
    except Exception as e:
        print(f"[X] Σφάλμα κατά την αντιγραφή του φακέλου: {e}")

if __name__ == '__main__':
    main()