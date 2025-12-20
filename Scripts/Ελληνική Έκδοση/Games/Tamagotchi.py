#!/usr/bin/env python3
"""
Tamagotchi
"""

import os, json, time, threading, random, subprocess, sys

# -------------------- ΡΥΘΜΙΣΕΙΣ --------------------
HOME = os.path.expanduser("~")
SAVE_PATH = os.path.join(HOME, ".termux_tamagotchi_v8_gr.json") # v8 αρχείο αποθήκευσης
AUTOSAVE_INTERVAL = 60
DECAY_PER_MIN = {
    "hunger": 1.0, "happiness": 0.5, "energy": 0.7, "cleanliness": 0.4,
    "health": 0.0 
}
MAX_XP_PER_LEVEL = 100
RETIRE_LEVEL = 25 # v8: Επίπεδο που πρέπει να έχει ένας Γηραιός για σύνταξη
AGE_TO_CHILD = 3     # Λεπτά (Από το Αβγό)
AGE_TO_TEEN = 720    # Λεπτά (12 ώρες)
AGE_TO_ADULT = 2160  # Λεπτά (36 ώρες συνολικά)
AGE_TO_ELDER = 5760  # Λεπτά (4 μέρες συνολικά)
SECONDS_PER_DAY = 86400

# -------------------- ΠΡΟΚΑΘΟΡΙΣΜΕΝΟ ΚΑΤΟΙΚΙΔΙΟ --------------------
DEFAULT_PET = {
    "name": "Τάμα",
    "created_at": time.time(),
    "last_tick": time.time(),
    "hunger": 80,
    "happiness": 80,
    "energy": 80,
    "cleanliness": 90,
    "health": 100,
    "is_sick": False,
    "age_minutes": 0,
    "age_stage": "Αβγό",
    "evolution_type": "Καμία",
    "hobby": "Καμία", # v8
    "xp": 0,
    "level": 1,
    "skill_points": 0,
    "achievements": {
        "hatched": False, "reached_teen": False, "evolved": False,
        "reached_elder": False, "level_10": False, "rich_1000": False,
        "bookworm_5": False, "master_gamer_10": False,
        "home_decorator_3": False, # v8
        "cosmic_legacy_1": False, # v8
        "zen_master_5": False, # v8
    },
    "personality": random.choice(["Παιχνιδιάρικο", "Τεμπέλικο", "Γκρινιάρικο", "Έξυπνο", "Περίεργο"]),
    "coins": 50,
    "inventory": {
        "Ειδικό Φαγητό": 1, "Καινούριο Παιχνίδι": 0, "Φάρμακο": 0, "Βιβλίο": 1,
        "Ενεργειακό Ποτό": 0, "Σπάνιο Σνακ": 0, "Βιταμίνες": 0,
    },
    "decor": [], # v8: Λίστα αντικειμένων διακόσμησης
    "skills": {
        "intelligence": 0, "agility": 0, "charm": 0,
        "strength": 0, "luck": 0, "focus": 0, # v8
    },
    "current_event": {
        "type": "Καμία", "last_update": 0,
    },
    "dialogue": "...",
    # v8: Σύστημα Κληρονομιάς. Αυτά τα στατιστικά παραμένουν μετά τη σύνταξη!
    "stardust": 0,
    "legacy_bonus": {
        "xp_mod": 1.0,
        "coin_mod": 1.0,
        "sp_mod": 1.0, # Δεν χρησιμοποιείται για αγορά, αλλά για 'Συγκέντρωση'
    },
}

# -------------------- v6/v7: ΚΑΘΗΜΕΡΙΝΑ ΓΕΓΟΝΟΤΑ --------------------
DAILY_EVENTS = [
    "Καμία", "Ηλιόλουστη Μέρα", "Βροχερή Μέρα", "Μέρα Αγοράς", "Μέρα Ασθένειας",
    "Διπλή XP Μέρα", "Μέρα Φεστιβάλ", "Καύσωνας", "Καλή Τύχη",
]

def check_daily_event(pet):
    now = time.time()
    last_update = pet.get("current_event", {}).get("last_update", 0)
    
    if now - last_update > SECONDS_PER_DAY:
        pet["current_event"]["type"] = random.choice(DAILY_EVENTS)
        pet["current_event"]["last_update"] = now
        event_name = pet["current_event"]["type"]
        if event_name != "Καμία":
            notify("📅 Καθημερινό Γεγονός!", f"Σήμερα είναι {event_name}!")
        if event_name == "Μέρα Ασθένειας": pet["is_sick"] = True

# -------------------- v8: ΙΚΑΝΟΤΗΤΕΣ & ΠΟΛΛΑΠΛΑΣΙΑΣΤΕΣ --------------------
def add_skill(pet, skill, amount):
    mod = 1.0
    p = pet["personality"]
    if skill == "intelligence" and p == "Έξυπνο": mod = 1.5
    elif skill == "agility" and p == "Περίεργο": mod = 1.3
    elif skill == "charm" and p == "Παιχνιδιάρικο": mod = 1.3
    elif skill == "strength" and p == "Παιχνιδιάρικο": mod = 1.2
    elif skill == "focus" and p == "Έξυπνο": mod = 1.3 # v8
    elif skill == "focus" and p == "Τεμπέλικο": mod = 1.5 # v8
        
    pet["skills"][skill] = round(pet["skills"][skill] + (amount * mod), 2)

def get_skill_level(pet, skill):
    return int(pet["skills"][skill] // 10) + 1

def get_charm_discount(pet):
    level = get_skill_level(pet, "charm")
    return min(0.30, level * 0.01)

def get_intel_bonus(pet):
    level = get_skill_level(pet, "intelligence")
    # v8: Μπόνους Διακόσμησης
    mod = 1.1 if "Ράφι Βιβλίων" in pet["decor"] else 1.0
    return (1.0 + (level * 0.05)) * mod

def get_agility_bonus(pet):
    level = get_skill_level(pet, "agility")
    return 1.0 + (level * 0.05)

def get_strength_bonus(pet):
    level = get_skill_level(pet, "strength")
    mod = 1.1 if "Χαλάκι Προπόνησης" in pet["decor"] else 1.0 # v8
    return (1.0 + (level * 0.05)) * mod

def get_luck_bonus(pet):
    level = get_skill_level(pet, "luck")
    mod = 1.0 + (level * 0.03)
    if pet["current_event"]["type"] == "Καλή Τύχη": mod *= 2.0
    return mod

def get_focus_bonus(pet): # v8
    """Η Συγκέντρωση αυξάνει την πιθανότητα για bonus SP στο level up"""
    level = get_skill_level(pet, "focus")
    # 5% πιθανότητα ανά επίπεδο για +1 SP. Μέγιστο 50%
    return min(0.5, level * 0.05)

# -------------------- ΠΟΛΛΑΠΛΑΣΙΑΣΤΕΣ ΠΡΟΣΩΠΙΚΟΤΗΤΑΣ (v7/v8) --------------------
PERSONALITY_MODS = {
    "Παιχνιδιάρικο": {
        "happiness_decay": 1.2, "energy_decay": 1.1,
        "play_happiness": 1.5, "play_xp": 1.2,
        "strength_gain": 1.2, "charm_gain": 1.2,
    },
    "Τεμπέλικο": {
        "energy_decay": 0.7, "hunger_decay": 1.1,
        "play_happiness": 0.5, "play_energy": 0.5, "sleep_energy": 1.3,
        "strength_gain": 0.5, "focus_gain": 1.5,
    },
    "Γκρινιάρικο": {
        "happiness_decay": 1.3, "play_happiness": 0.7,
        "feed_happiness": 0.5, "clean_happiness": 0.7,
    },
    "Έξυπνο": {
        "game_xp": 1.5, "game_happiness": 1.2,
        "int_gain": 1.5, "focus_gain": 1.3,
    },
    "Περίεργο": {
        "happiness_decay": 0.9, "walk_coins": 1.5, "walk_xp": 1.3,
        "agi_gain": 1.3, "luck_gain": 1.5,
    },
}
def get_mod(pet, key):
    return PERSONALITY_MODS.get(pet["personality"], {}).get(key, 1.0)

# -------------------- ΔΙΑΛΟΓΟΣ (v7/v8) --------------------
DIALOGUE = {
    "Προκαθορισμένο": {
        "happy": ["Αισθάνομαι υπέροcha!", "Η ζωή είναι ωραία."],
        "excited": ["Η ΚΑΛΥΤΕΡΗ ΜΕΡΑ ΠΟΤΕ!", "ΟΥΑΟΥΑΟΥ!"],
        "neutral": ["Χμμ.", "...", "Απλά χαλαρώνω."],
        "hungry": ["Η κοιλιά μου γουργουρίζει...", "Φαγητό, παρακαλώ;"],
        "sleepy": ["*yawn*", "Χρειάζομαι έναν υπνάκο."],
        "dirty": ["Αισθάνομαι αηδιαστικά.", "Ώρα για μπάνιο;"],
        "sad": ["Αισθάνομαι λίγο στεναχωρημένο.", "Θα ήθελα μια αγκαλιά."],
        "sick": ["*βήχας*", "Δεν αισθάνομαι τόσο καλά..."],
        "train": ["Χαπ, χαπ, χαπ!", "Αισθάνομαι πιο δυνατό!"],
        "job": ["Ώρα να κερδίσω μερικά νομίσματα.", "Πάω στη δουλειά!"],
        "meditate": ["Οοοοοομμμμ...", "Εσωτερική γαλήνη."], # v8
    },
    "Παιχνιδιάρικο": {
        "happy": ["Ας παίξουμε!", "Πιάσμε αν μπορείς!", "Παιχνίδι παιχνίδι παιχνίδι!"],
        "train": ["Αυτό είναι παιχνίδι; Θα κερδίσω!", "Κοίτα πόσο γρήγορος είμαι!"],
    },
    "Τεμπέλικο": {
        "sleepy": ["Η προκαθορισμένη μου κατάσταση.", "Καληνύχτα.", "Ξύπνησέ με ποτέ."],
        "train": ["*λαχάνιασμα*... Ήδη τελείωσε;", "Αυτό είναι πολύ δουλειά."],
        "job": ["Πρέπει *πραγματικά*;"],
        "meditate": ["Αυτό είναι απλά... υπνάκος με παραπάνω βήματα;"], # v8
    },
    "Γκρινιάρικο": {
        "neutral": ["Ό,τι να 'ναι.", "Άσε με ήσυχο.", "Τι θέλεις;"],
        "hungry": ["Πού είναι το φαγητό μου;! ΤΩΡΑ!", "Ήσουν αργός."],
    },
    "Έξυπνο": {
        "neutral": ["Σκέφτομαι το σύμπαν.", "Χρειάζομαι διέγερση."],
        "game": ["Αυτό ήταν... απλό.", "Προσπάθησε να με προκαλέσεις την επόμενη φορά."],
        "read": ["Α, νέες πληροφορίες!", "Συναρπαστικό."],
        "job": ["Η διανόησή μου είναι πολύτιμος πόρος."],
        "meditate": ["Καθαρίζω το μυαλό μου για νέες σκέψεις."], # v8
    },
    "Περίεργο": {
        "neutral": ["Τι κάνεις;", "Τι υπάρχει εκεί πέρα;"],
        "walk": ["Ας πάμε να εξερευνήσουμε!", "Ώρα περιπέτειας!"],
    },
    # v8: Ειδικός διάλογος για χόμπι
    "Hobby_Gaming": ["Ώρα να σπάσω το υψηλό μου σκορ!", "Απλά ένα ακόμη level..."],
    "Hobby_Reading": ["Αναρωτιέμαι τι συμβαίνει στο επόμενο κεφάλαιο;", "Έχω χαθεί σε αυτό το βιβλίο!"],
    "Hobby_Training": ["Πρέπει να κάνω gains!", "Νιώθω το κάψιμο!"],
}

def update_dialogue(pet, context=None):
    if pet["age_stage"] == "Αβγό":
        pet["dialogue"] = random.choice(["...", "*tap tap*", "...", "...", "*wiggle*"])
        return
        
    m = mood(pet)
    p = pet["personality"]
    
    # v8: Πλαίσιο χόμπι
    if context == "game" and pet["hobby"] == "Παιχνίδι":
        context = "Hobby_Gaming"
    elif context == "read" and pet["hobby"] == "Ανάγνωση":
        context = "Hobby_Reading"
    elif context == "train" and pet["hobby"] == "Προπόνηση":
        context = "Hobby_Training"
    
    if "Μέρα" in pet["current_event"]["type"] and not context: return
    
    options = DIALOGUE.get(p, {}).get(context or m, [])
    if not options:
        options = DIALOGUE.get("Προκαθορισμένο", {}).get(context or m, ["..."])
        
    pet["dialogue"] = random.choice(options)

# -------------------- ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ --------------------
def clamp(v, a=0, b=100): return max(a, min(b, v))

def notify(title, text):
    try:
        subprocess.run(["termux-notification", "--title", title, "--content", text], check=False)
    except:
        pass

def grant_achievement(pet, key):
    if not pet["achievements"].get(key, False):
        pet["achievements"][key] = True
        key_name = key.replace("_", " ").title()
        notify("🏆 Ξεκλείδωμα Επιτεύγματος!", key_name)
        print(f"*** 🏆 Ξεκλείδωμα Επιτεύγματος: {key_name} ***")
        add_xp(pet, 25)

def save_pet(pet):
    try:
        with open(SAVE_PATH, "w") as f:
            json.dump(pet, f, indent=2)
    except Exception as e:
        print(f"Σφάλμα αποθήκευσης κατοικίδιου: {e}")

def load_pet():
    if not os.path.exists(SAVE_PATH):
        print("Δεν βρέθηκε αρχείο αποθήκευσης, δημιουργία νέου κατοικίδιου!")
        save_pet(DEFAULT_PET)
        return DEFAULT_PET.copy()
    try:
        with open(SAVE_PATH, "r") as f:
            data = json.load(f)
        
        # v8: Πιο ισχυρή συγχώνευση για νέα κλειδιά
        merged_pet = DEFAULT_PET.copy()
        
        # Αντιγραφή στατιστικών κληρονομιάς πρώτα
        merged_pet["stardust"] = data.get("stardust", 0)
        merged_pet["legacy_bonus"] = DEFAULT_PET["legacy_bonus"].copy()
        merged_pet["legacy_bonus"].update(data.get("legacy_bonus", {}))
        
        # Τώρα συγχώνευση των δεδομένων του τρέχοντος κατοικίδιου
        for k, v in data.items():
            if k in ["stardust", "legacy_bonus"]: continue # Έχουν ήδη υποστεί επεξεργασία
            
            if k in merged_pet and isinstance(merged_pet[k], dict):
                merged_pet[k].update(data[k])
            else:
                merged_pet[k] = data[k]
        
        # Τελικός έλεγχος για ύπαρξη όλων των νέων προκαθορισμένων κλειδιών
        for k, v_default in DEFAULT_PET.items():
            if k not in merged_pet:
                merged_pet[k] = v_default
            elif isinstance(v_default, dict):
                for sk, sv_default in v_default.items():
                    if sk not in merged_pet[k]:
                        merged_pet[k][sk] = sv_default
                         
        return merged_pet
    except Exception as e:
        print(f"Σφάλμα φόρτωσης αποθήκευσης, δημιουργία νέου κατοικίδιου. Σφάλμα: {e}")
        save_pet(DEFAULT_PET)
        return DEFAULT_PET.copy()

# v8: Ανάθεση Χόμπι
def assign_hobby(pet):
    if pet["hobby"] != "Καμία": return
    
    print(f"\n🌟 {pet['name']} μεγαλώνει και χρειάζεται ένα χόμπι!")
    skills = pet["skills"]
    
    # Εύρεση υψηλότερης ικανότητας
    activity_skills = {
        "intelligence": skills["intelligence"],
        "agility": skills["agility"],
        "strength": skills["strength"],
    }
    highest_skill_name = max(activity_skills, key=activity_skills.get)
    
    if highest_skill_name == "intelligence":
        # Έλεγχος αν διάβαζε περισσότερο ή έπαιζε παιχνίδια
        if skills["intelligence"] > (skills["agility"] + skills["strength"]):
             pet["hobby"] = "Ανάγνωση"
        else:
             pet["hobby"] = "Παιχνίδι"
    elif highest_skill_name == "strength":
        pet["hobby"] = "Προπόνηση"
    elif highest_skill_name == "agility":
        pet["hobby"] = "Παιχνίδι" # Η ευκινησία συμβάλλει στα παιχνίδια
    else:
        pet["hobby"] = "Παιχνίδι" # Προκαθορισμένο
        
    print(f"Βάσει των ικανοτήτων του, το νέο του χόμπι είναι {pet['hobby']}!")
    pet["dialogue"] = f"Αποφάσισα ότι πραγματικά αγαπώ την {pet['hobby']}!"
    time.sleep(1.5)

def tick(pet):
    now = time.time()
    elapsed = now - pet["last_tick"]
    minutes = elapsed / 60
    if minutes <= 0: return

    if pet["age_stage"] == "Αβγό":
        pet["age_minutes"] += minutes
        pet["last_tick"] = now
        if pet["age_minutes"] > AGE_TO_CHILD:
            pet["age_stage"] = "Παιδί"
            pet["dialogue"] = "Γεια σου κόσμε!"
            notify("🥚 Εκκόλαψη!", f"Το νέο σου κατοικίδιο {pet['name']} εκκόλαφθηκε!")
            grant_achievement(pet, "hatched")
        return

    event = pet["current_event"]["type"]
    decay_mult = 1.0
    if event == "Μέρα Ασθένειας": decay_mult = 1.5
    if event == "Ηλιόλουστη Μέρα": decay_mult = 0.7
    # v8: Η Συγκέντρωση μειώνει την επίδραση αρνητικών γεγονότων
    if decay_mult > 1.0:
        decay_mult -= (get_focus_bonus(pet) * 0.5) # Το μπόνους Συγκέντρωσης είναι 50% αποτελεσματικό εδώ
    
    for stat, decay in DECAY_PER_MIN.items():
        if stat == "health": continue
        
        mod = get_mod(pet, f"{stat}_decay") * decay_mult
        
        # v8: Παθητικά μπόνους διακόσμησης
        if stat == "happiness" and "Χαλί από Πλισέ" in pet["decor"]: mod *= 0.9
        if stat == "cleanliness" and "Αυτόματο Καθαριστήριο" in pet["decor"]: mod *= 0.8
        
        # Πολλαπλασιαστές γεγονότων
        if event == "Ηλιόλουστη Μέρα" and stat == "happiness": mod *= 0.5
        if event == "Βροχερή Μέρα" and stat == "energy": mod *= 0.7
        if event == "Βροχερή Μέρα" and stat == "cleanliness": mod *= 1.5
        if event == "Καύσωνας" and stat == "energy": mod *= 2.0
            
        pet[stat] = clamp(pet[stat] - (decay * mod * minutes))
    
    # Λογική Υγείας & Ασθένειας (ίδια με v7)
    health_decay = 0
    if pet["is_sick"]: health_decay += 0.5 * minutes
    if pet["hunger"] < 5: health_decay += (0.2 * minutes) * (5 - pet["hunger"])
    if pet["energy"] < 5: health_decay += 0.1 * minutes
    pet["health"] = clamp(pet["health"] - health_decay)
    if pet["cleanliness"] < 10 and not pet["is_sick"] and random.random() < (0.1 * minutes):
        pet["is_sick"] = True
        pet["dialogue"] = "*ατσούμ!* Αισθάνομαι άρρωστο..."
        notify("🤒 Ασθένεια!", f"Το {pet['name']} αρρώστησε επειδή ήταν βρώμικο!")
    if pet["health"] < 20: pet["is_sick"] = True
    elif pet["health"] > 80 and pet["is_sick"] and event != "Μέρα Ασθένειας":
        pet["is_sick"] = False
        pet["dialogue"] = "Ουφ... Αισθάνομαι καλύτερα τώρα."
        
    pet["age_minutes"] += minutes
    pet["last_tick"] = now

    # Στάδιο Ηλικίας & Λογική Εξέλιξης
    if pet["age_stage"] == "Παιδί" and pet["age_minutes"] > AGE_TO_TEEN:
        pet["age_stage"] = "Εφηβικό"
        pet["level"] += 1; add_xp(pet, 50); pet["happiness"] = clamp(pet["happiness"] + 30)
        notify("🎉 Μεγάλωσε!", f"Το {pet['name']} είναι τώρα Εφηβικό!")
        grant_achievement(pet, "reached_teen")
        assign_hobby(pet) # v8
        
    elif pet["age_stage"] == "Εφηβικό" and pet["age_minutes"] > AGE_TO_ADULT:
        pet["age_stage"] = "Ενήλικο"
        pet["level"] += 2; add_xp(pet, 100); pet["happiness"] = clamp(pet["happiness"] + 50)
        
        sk = pet["skills"]
        stats = pet
        mental_score = sk["intelligence"] + sk["charm"]
        physical_score = sk["strength"] + sk["agility"]
        avg_care = (stats["hunger"] + stats["happiness"] + stats["energy"] + stats["cleanliness"]) / 4
        
        evo_type = "Μέτριο"
        if avg_care < 40: evo_type = "Τεμπέλικο"
        elif mental_score > (physical_score * 1.3): evo_type = "Ιδιοφυΐα"
        elif physical_score > (mental_score * 1.3): evo_type = "Αθλητικό"
            
        pet["evolution_type"] = evo_type
        notify("✨ ΕΞΕΛΙΞΗ! ✨", f"Το {pet['name']} εξελίχθηκε σε {evo_type} Ενήλικο!")
        grant_achievement(pet, "evolved")

    elif pet["age_stage"] == "Ενήλικο" and pet["age_minutes"] > AGE_TO_ELDER:
        pet["age_stage"] = "Γηραιό"
        pet["level"] += 1; add_xp(pet, 50); pet["dialogue"] = "Στην εποχή μου..."
        notify("🕰️ Γηραιό!", f"Το {pet['name']} είναι τώρα ένα σοφό Γηραιό.")
        grant_achievement(pet, "reached_elder")

# -------------------- ΕΠΙΠΕΔΟ & XP --------------------
def level_up(pet):
    threshold = MAX_XP_PER_LEVEL * pet["level"]
    if pet["xp"] >= threshold:
        pet["xp"] -= threshold
        pet["level"] += 1
        pet["happiness"] = clamp(pet["happiness"] + 20)
        
        # v8: Λογική απόκτησης Πόντων Ικανότητας
        sp_gain = 1
        if random.random() < get_focus_bonus(pet):
            sp_gain += 1
            print("✨ Η 'Συγκέντρωσή' σου σου χάρισε έναν ΕΠΙΠΛΕΟΝ Πόντο Ικανότητας! ✨")
        
        pet["skill_points"] += sp_gain
        notify("🎉 Αύξηση Επιπέδου!", f"Το {pet['name']} έφτασε στο Επίπεδο {pet['level']}! Πήρες {sp_gain} Πόντο(ους) Ικανότητας!")
        if pet["level"] >= 10:
            grant_achievement(pet, "level_10")

def add_xp(pet, amount):
    # v8: Εφαρμογή Μπόνους Κληρονομιάς
    legacy_mod = pet.get("legacy_bonus", {}).get("xp_mod", 1.0)
    
    intel_bonus = get_intel_bonus(pet)
    luck_bonus = (get_luck_bonus(pet) - 1.0) * 0.5 + 1.0
    event_mod = 1.0
    if pet["current_event"]["type"] == "Διπλή XP Μέρα": event_mod = 2.0
    if pet["evolution_type"] == "Ιδιοφυΐα": intel_bonus *= 1.2
    
    final_amount = amount * intel_bonus * luck_bonus * event_mod * legacy_mod
    pet["xp"] += final_amount
    level_up(pet)
    # Επιστροφή μορφοποιημένης ποσότητας για εκτύπωση
    return f"{final_amount:.1f}"

# -------------------- ΔΙΑΘΕΣΕΙΣ & ΕΚΦΡΑΣΕΙΣ (v7) --------------------
def mood(pet):
    h, ha, e, c, he = pet["hunger"], pet["happiness"], pet["energy"], pet["cleanliness"], pet["health"]
    if pet["is_sick"] or he < 25: return "sick"
    if h < 25: return "hungry"
    if e < 25: return "sleepy"
    if c < 25: return "dirty"
    if ha < 25: return "sad"
    if ha > 90: return "excited"
    if ha > 70: return "happy"
    return "neutral"
EXPRESSIONS = {
    "Αβγό": {"neutral": " ( ..... ) ", "happy": " ( ..'.. ) ", "sick": " ( ..... ) ", "excited": " ( ..'.. ) ", "hungry": " ( ..... ) ", "sleepy": " ( ..... ) ", "dirty": " ( ..... ) ", "sad": " ( ..... ) "},
    "Παιδί": {"happy": " ( ^‿^ ) ", "excited": " ( ✧∀✧ ) ", "neutral": " ( •‿• ) ", "hungry": " ( ˘﹏˘ ) ", "sleepy": " ( -_- ) zZ", "dirty": " ( •~• ) ", "sad": " ( ;﹏; ) ", "sick": " ( x_x ) "},
    "Εφηβικό": {"happy": " ( ^v^ ) ", "excited": " ( 🤩 ) ", "neutral": " ( -v- ) ", "hungry": " ( T_T ) ", "sleepy": " ( u_u ) zZ", "dirty": " ( >.< ) ", "sad": " ( ._.) ", "sick": " ( X_X ) "},
    "Ενήλικο_Μέτριο": {"happy": "c( ^‿^ )っ", "excited": "c( ✧∀✧ )っ", "neutral": "c( •‿• )っ", "hungry": "c( ˘﹏˘ )っ", "sleepy": "c( -_- )っ zZ", "dirty": "c( •~• )っ", "sad": "c( ;﹏; )っ", "sick": "c( x_x )っ"},
    "Ενήλικο_Ιδιοφυΐα": {"happy": "o( ^‿^ )o", "excited": "o( ✧∀✧ )o", "neutral": "o( •_• )o", "hungry": "o( ˘_˘ )o", "sleepy": "o( -_- )o zZ", "dirty": "o( •~• )o", "sad": "o( ;_; )o", "sick": "o( x_x )o"},
    "Ενήλικο_Αθλητικό": {"happy": "V( ^o^ )V", "excited": "V( >O< )V", "neutral": "V( •-• )V", "hungry": "V( >_< )V", "sleepy": "V( -_- )V zZ", "dirty": "V( •~• )V", "sad": "V( ._. )V", "sick": "V( x_x )V"},
    "Ενήλικο_Τεμπέλικο": {"happy": "~( ^o^ )~", "excited": "~( *O* )~", "neutral": "~( ._. )~", "hungry": "~( >o< )~", "sleepy": "~( -_- )~ zZ", "dirty": "~( T_T )~", "sad": "~( ;o; )~", "sick": "~( x_x )~"},
    "Γηραιό": {"happy": "c[ ^‿^ ]ɔ", "excited": "c[ ✧∀✧ ]ɔ", "neutral": "c[ •‿• ]ɔ", "hungry": "c[ ˘﹏˘ ]ɔ", "sleepy": "c[ -_- ]ɔ zZ", "dirty": "c[ •~• ]ɔ", "sad": "c[ ;﹏; ]ɔ", "sick": "c[ x_x ]ɔ"}
}
def ascii_pet(pet):
    m = mood(pet)
    stage = pet["age_stage"]
    evo = pet["evolution_type"]
    art_key = f"Ενήλικο_{evo}" if stage == "Ενήλικο" else stage
    stage_art = EXPRESSIONS.get(art_key, EXPRESSIONS.get(stage, EXPRESSIONS["Παιδί"]))
    art = stage_art.get(m, stage_art["neutral"])
    return f"  /\\_/\\ \n {art}"
# -------------------- ΤΕΛΟΣ ASCII --------------------

def status_text(pet):
    if pet["age_stage"] == "Αβγό":
        return f"Ηλικία: {int(pet['age_minutes'])} λεπ (Εκκολάπτεται στα {AGE_TO_CHILD} λεπ)"
        
    lvl_prog = int((pet["xp"] / (MAX_XP_PER_LEVEL * pet["level"])) * 20)
    bar = "█" * lvl_prog + "-" * (20 - lvl_prog)
    
    # v8: Εμφάνιση Σπιτιού
    home_str = ", ".join(pet["decor"]) if pet["decor"] else "Άδειο"

    status = "Υγιές"
    if pet["is_sick"]: status = "Άρρωστο! 🤒"
    
    evo_str = f" ({pet['evolution_type']})" if pet['age_stage'] in ["Ενήλικο", "Γηραιό"] else ""

    return (
        f"Επίπεδο {pet['level']} ({pet['age_stage']}{evo_str}) | XP: {int(pet['xp'])}/{MAX_XP_PER_LEVEL * pet['level']}\n"
        f"[{bar}]\n"
        f"Υγεία : {int(pet['health'])}/100 | Κατάσταση: {status}\n"
        f"Πείνα  : {int(pet['hunger'])}/100 | Ευτυχία : {int(pet['happiness'])}/100\n"
        f"Ενέργεια: {int(pet['energy'])}/100 | Καθαρότητα: {int(pet['cleanliness'])}/100\n"
        f"Χόμπι  : {pet['hobby']} | Νομίσματα : {pet['coins']} ¢ | Stardust: {pet['stardust']} ✨\n"
        f"Σπίτι  : {home_str}\n"
    )

# v8: Νέα Οθόνη Στατιστικών
def show_stats(pet):
    os.system("clear" if os.name != 'nt' else 'cls')
    print(f"--- 📊 Στατιστικά για {pet['name']} ---")
    
    # Ικανότητες
    skills = pet['skills']
    sk_int = f"Διαν: {get_skill_level(pet, 'intelligence')} ({skills['intelligence']:.1f})"
    sk_agi = f"Ευκιν: {get_skill_level(pet, 'agility')} ({skills['agility']:.1f})"
    sk_cha = f"Χαρισ: {get_skill_level(pet, 'charm')} ({skills['charm']:.1f})"
    sk_str = f"Δυν: {get_skill_level(pet, 'strength')} ({skills['strength']:.1f})"
    sk_lck = f"Τύχη: {get_skill_level(pet, 'luck')} ({skills['luck']:.1f})"
    sk_foc = f"Συγκ: {get_skill_level(pet, 'focus')} ({skills['focus']:.1f})"
    
    print("\n--- Ικανότητες ---")
    print(f"Διαθέσιμοι ΠΙ: {pet['skill_points']}")
    print(f"{sk_int} | {sk_agi} | {sk_cha}")
    print(f"{sk_str} | {sk_lck} | {sk_foc}")
    
    # Αποθήκη
    print("\n--- 🎒 Αποθήκη ---")
    inv_items = [f"{name} x{count}" for name, count in pet["inventory"].items() if count > 0]
    inv_str = ", ".join(inv_items) if inv_items else "Άδειο"
    print(inv_str)

    # Επιτεύγματα
    print("\n--- 🏆 Επιτεύγματα ---")
    achs = [name.replace("_", " ").title() for name, done in pet["achievements"].items() if done]
    print(", ".join(achs) if achs else "Κανένα ακόμη!")
    
    # Κληρονομιά
    print("\n--- ✨ Μπόνους Κληρονομιάς ---")
    bonus = pet["legacy_bonus"]
    print(f"Μπόνους XP: +{(bonus['xp_mod'] - 1.0)*100:.0f}% | Μπόνους Νομισμάτων: +{(bonus['coin_mod'] - 1.0)*100:.0f}%")
    
    input("\n(Πατήστε Enter για επιστροφή...)")

# -------------------- ΔΡΑΣΕΙΣ (v8) --------------------
def feed(pet):
    if pet["age_stage"] == "Αβγό": print("Δεν μπορείς να ταΐσεις ένα αβγό!"); return
    pet["hunger"] = clamp(pet["hunger"] + 25)
    mod = get_mod(pet, "feed_happiness")
    pet["happiness"] = clamp(pet["happiness"] + 3 * mod)
    xp = add_xp(pet, 5)
    print(f"🍎 Τάϊσες το κατοικίδιό σου βασικό φαγητό. XP +{xp}!")

def play(pet):
    if pet["age_stage"] == "Αβγό": print("Δεν μπορείς να παίξεις με ένα αβγό!"); return
    if pet["energy"] < 10 or pet["is_sick"]:
        print("Πολύ κουρασμένο ή άρρωστο για να παίξει."); update_dialogue(pet, "sleepy"); return
    
    hap_mod = get_mod(pet, "play_happiness")
    # v8: Μπόνους Διακόσμησης
    if "Κουτί Παιχνιδιών" in pet["decor"]: hap_mod *= 1.2
    
    nrg_mod = get_mod(pet, "play_energy") * (1 / get_strength_bonus(pet))
    xp_mod = get_mod(pet, "play_xp")
    
    pet["happiness"] = clamp(pet["happiness"] + 15 * hap_mod)
    pet["energy"] = clamp(pet["energy"] - 10 * nrg_mod)
    pet["cleanliness"] = clamp(pet["cleanliness"] - 5)
    
    xp = add_xp(pet, 10 * xp_mod)
    add_skill(pet, "agility", 0.5 * get_mod(pet, "agi_gain"))
    add_skill(pet, "charm", 0.2 * get_mod(pet, "cha_gain"))
    add_skill(pet, "strength", 0.2 * get_mod(pet, "strength_gain"))
    
    print(f"🎾 Παίξατε! XP +{xp}. Ευκιν +0.5, Χαρισ +0.2, Δυν +0.2")

def sleep(pet):
    if pet["age_stage"] == "Αβγό": print("Το αβγό... ξεκουράζεται."); return
    print("💤 Κοιμάται...")
    mod = get_mod(pet, "sleep_energy")
    if pet["current_event"]["type"] == "Καύσωνας": mod *= 0.7
    # v8: Μπόνους Διακόσμησης
    if "Ζεστό Κρεβάτι" in pet["decor"]: mod *= 1.2
        
    pet["energy"] = clamp(pet["energy"] + 40 * mod)
    pet["hunger"] = clamp(pet["hunger"] - 10)
    if not pet["is_sick"]:
        pet["health"] = clamp(pet["health"] + 10)
        
    xp = add_xp(pet, 5)
    print(f"😴 Καλά ξεκουρασμένο! Ενέργεια +{int(40*mod)}. Υγεία αυξήθηκε. XP +{xp}")

def clean(pet):
    if pet["age_stage"] == "Αβγό": print("Γυάλισες το αβγό."); return
    mod = get_mod(pet, "clean_happiness")
    pet["cleanliness"] = clamp(pet["cleanliness"] + 50)
    pet["happiness"] = clamp(pet["happiness"] + 10 * mod)
    xp = add_xp(pet, 8)
    add_skill(pet, "charm", 0.5 * get_mod(pet, "cha_gain"))
    if pet["is_sick"] and pet["cleanliness"] > 90:
        pet["health"] = clamp(pet["health"] + 5)
        print("Η καθαριότητα βοηθά στην καταπολέμηση της ασθένειας!")
    print(f"🧼 Όλα καθαρά! XP +{xp}. Χαρισ +0.5")

def read_book(pet):
    if pet["age_stage"] == "Αβγό": print("Το αβγό δεν μπορεί να διαβάσει."); return
    if pet["inventory"].get("Βιβλίο", 0) <= 0:
        print("Δεν έχεις αντικείμενα 'Βιβλίο'. Αγόρασε ένα από το κατάστημα!"); return
    if pet["energy"] < 15 or pet["is_sick"]:
        print("Πολύ κουρασμένο ή άρρωστο για να διαβάσει βιβλίο."); update_dialogue(pet, "sleepy"); return

    pet["inventory"]["Βιβλίο"] -= 1
    pet["energy"] = clamp(pet["energy"] - 10)
    pet["happiness"] = clamp(pet["happiness"] + 5)
    
    xp_mod = 1.0
    hap_mod = 1.0
    # v8: Μπόνους Χόμπι
    if pet["hobby"] == "Ανάγνωση":
        xp_mod = 1.3
        hap_mod = 2.0
        print("📖 Αυτό είναι το αγαπημένο του χόμπι!")
    
    pet["happiness"] = clamp(pet["happiness"] + (5 * hap_mod))
    xp = add_xp(pet, 20 * xp_mod)
    add_skill(pet, "intelligence", 2.0 * get_mod(pet, "int_gain"))
    print(f"📚 Το {pet['name']} διάβασε ένα βιβλίο! XP +{xp}. Διαν +2.0")
    update_dialogue(pet, "read")
    
    # Έλεγχος επιτεύγματος
    read_count = 5 - pet["inventory"].get("Βιβλίο", 0) # Απλός έλεγχος
    if read_count >= 5:
        grant_achievement(pet, "bookworm_5")

# v8: Νέα Δράση Διαλογισμού
def meditate(pet):
    if pet["age_stage"] == "Αβγό": print("Το αβγό είναι ήδη σε ηρεμία."); return
    if pet["energy"] < 10 or pet["is_sick"]:
        print("Πολύ κουρασμένο ή άρρωστο για διαλογισμό."); update_dialogue(pet, "sleepy"); return

    print(f"🧘 Το {pet['name']} διαλογίζεται...")
    update_dialogue(pet, "meditate")
    
    pet["energy"] = clamp(pet["energy"] - 5)
    pet["happiness"] = clamp(pet["happiness"] + 5) # Ηρεμία
    
    xp = add_xp(pet, 10)
    add_skill(pet, "focus", 1.0 * get_mod(pet, "focus_gain"))
    print(f"Οοοομμμ... XP +{xp}. Συγκ +1.0. Ευτυχία +5.")
    
    if get_skill_level(pet, "focus") >= 5:
        grant_achievement(pet, "zen_master_5")

def train(pet):
    if pet["age_stage"] not in ["Εφηβικό", "Ενήλικο", "Γηραιό"]:
        print("Το κατοικίδιό σου είναι πολύ μικρό για προπόνηση!"); return
    if pet["energy"] < 20 or pet["is_sick"]:
        print("Πολύ κουρασμένο ή άρρωστο για προπόνηση."); update_dialogue(pet, "sleepy"); return
    
    print(f"🏋️ Το {pet['name']} προπονείται σκληρά!")
    update_dialogue(pet, "train")
    
    nrg_mod = (1 / get_strength_bonus(pet))
    pet["energy"] = clamp(pet["energy"] - 20 * nrg_mod)
    pet["hunger"] = clamp(pet["hunger"] - 5)
    pet["cleanliness"] = clamp(pet["cleanliness"] - 10)
    
    xp_mod = 1.0
    # v8: Μπόνους Χόμπι
    if pet["hobby"] == "Προπόνηση":
        xp_mod = 1.3
        pet["happiness"] = clamp(pet["happiness"] + 10)
        print("🏋️ Αυτό είναι το αγαπημένο του χόμπι!")
    
    xp = add_xp(pet, 15 * xp_mod)
    add_skill(pet, "strength", 1.5 * get_mod(pet, "strength_gain"))
    add_skill(pet, "agility", 1.0 * get_mod(pet, "agi_gain"))
    
    print(f"Ουφ! Τέλεια προπόνηση! XP +{xp}. Δυν +1.5, Ευκιν +1.0")

def work_job(pet):
    if pet["age_stage"] not in ["Ενήλικο", "Γηραιό"]:
        print("Μόνο Ενήλικα και Γηραιά μπορούν να δουλέψουν."); return
    if pet["energy"] < 30 or pet["is_sick"]:
        print("Πολύ κουρασμένο ή άρρωστο για δουλειά."); update_dialogue(pet, "sleepy"); return
        
    print("\n--- 🧑‍💼 Διαθέσιμες Δουλειές ---")
    print(f"[1] Βοηθός Βιβλιοθήκης (Απαιτεί: Διαν Επ {get_skill_level(pet, 'intelligence')})")
    print(f"[2] Μεταφορέας Πακέτων (Απαιτεί: Δυν Επ {get_skill_level(pet, 'strength')})")
    print(f"[3] Υπεύθυνος Καλωσορίσματος (Απαιτεί: Χαρισ Επ {get_skill_level(pet, 'charm')})")
    print("(Εισάγετε 'exit' για ακύρωση)")
    choice = input("Επιλέξτε δουλειά: > ").strip()
    
    base_pay, skill_used = 0, "intelligence"
    if choice == "1": skill_used, base_pay = "intelligence", 20; print("Ταξινόμηση βιβλίων...")
    elif choice == "2": skill_used, base_pay = "strength", 20; print("Μεταφορά πακέτων...")
    elif choice == "3": skill_used, base_pay = "charm", 20; print("Καλωσόρισμα πελατών...")
    else: print("Ακύρωση δουλειάς."); return

    update_dialogue(pet, "job")
    pet["energy"] = clamp(pet["energy"] - 30)
    pet["happiness"] = clamp(pet["happiness"] - 5)
    
    skill_bonus = (get_skill_level(pet, skill_used) - 1) * 10
    luck_bonus = int(random.randint(0, 5) * get_luck_bonus(pet))
    legacy_mod = pet.get("legacy_bonus", {}).get("coin_mod", 1.0) # v8
    
    pay = int((base_pay + skill_bonus + luck_bonus) * legacy_mod)
    
    pet["coins"] += pay
    xp = add_xp(pet, 10)
    
    print(f"Ολοκληρώθηκε η δουλειά! Κέρδισες {pay}¢ (Πολλαπλασιαστής Κληρονομιάς: {legacy_mod*100:.0f}%).")
    print(f"XP +{xp}. Ενέργεια -30, Ευτυχία -5.")
    if pet["coins"] >= 1000:
        grant_achievement(pet, "rich_1000")

def spend_sp(pet):
    if pet["skill_points"] <= 0:
        print("Δεν έχεις Πόντο(ους) Ικανότητας για να ξοδέψεις! Αύξησε επίπεδο για να τους κερδίσεις."); return
        
    print("\n--- 🔥 Ξόδεμα Πόντων Ικανότητας ---")
    print(f"Έχεις {pet['skill_points']} ΠΙ.")
    print("[1] Διανόηση (+5)")
    print("[2] Ευκινησία (+5)")
    print("[3] Χαρισματικότητα (+5)")
    print("[4] Δύναμη (+5)")
    print("[5] Τύχη (+5)")
    print("[6] Συγκέντρωση (+5)") # v8
    print("(Εισάγετε 'exit' για ακύρωση)")
    
    choice = input("Ξόδεψε 1 ΠΙ για: > ").strip()
    skill_key = None
    
    if choice == "1": skill_key = "intelligence"
    elif choice == "2": skill_key = "agility"
    elif choice == "3": skill_key = "charm"
    elif choice == "4": skill_key = "strength"
    elif choice == "5": skill_key = "luck"
    elif choice == "6": skill_key = "focus" # v8
    else: print("Ακυρώθηκε."); return
    
    pet["skills"][skill_key] += 5
    pet["skill_points"] -= 1
    print(f"Ενίσχυση! Η {skill_key.title()} αυξήθηκε κατά 5! Έχεις {pet['skill_points']} ΠΙ ακόμη.")


# -------------------- ΚΑΤΑΣΤΗΜΑΤΑ (v8) --------------------
SHOP_ITEMS = {
    "1": {"name": "Ειδικό Φαγητό", "price": 15},
    "2": {"name": "Καινούριο Παιχνίδι", "price": 25},
    "3": {"name": "Φάρμακο", "price": 40},
    "4": {"name": "Βιβλίο", "price": 50},
    "5": {"name": "Ενεργειακό Ποτό", "price": 35},
    "6": {"name": "Σπάνιο Σνακ", "price": 100},
    "7": {"name": "Βιταμίνες", "price": 30},
}
DECOR_ITEMS = { # v8
    "1": {"name": "Ζεστό Κρεβάτι", "price": 250, "desc": "Βελτιώνει την απόκτηση ενέργειας από ύπνο"},
    "2": {"name": "Χαλί από Πλισέ", "price": 150, "desc": "Επιβραδύνει τη μείωση ευτυχίας"},
    "3": {"name": "Ράφι Βιβλίων", "price": 300, "desc": "Ενισχύει την απόκτηση XP Διανόησης"},
    "4": {"name": "Κουτί Παιχνιδιών", "price": 200, "desc": "Ενισχύει την ευτυχία από 'Παιχνίδι'"},
    "5": {"name": "Χαλάκι Προπόνησης", "price": 300, "desc": "Ενισχύει τις δράσεις Δύναμης"},
    "6": {"name": "Αυτόματο Καθαριστήριο", "price": 500, "desc": "Επιβραδύνει τη μείωση καθαρότητας"},
}
STARDUST_UPGRADES = { # v8
    "1": {"name": "Μπόνους Κληρονομιάς XP", "cost": 5, "key": "xp_mod", "amount": 0.01},
    "2": {"name": "Μπόνους Κληρονομιάς Νομισμάτων", "cost": 5, "key": "coin_mod", "amount": 0.01},
}

def shop_menu(pet):
    print("\n--- 🏪 Καλώς ήρθατε στο Κατάστημα! ---")
    print("[1] Αγορά Αντικειμένων (Φαγητό, Παιχνίδια, κλπ)")
    print("[2] Αγορά Διακόσμησης (Βελτιώσεις Σπιτιού)")
    print("[3] Βελτιώσεις Stardust (Μόνιμες)")
    print("(Εισάγετε 'exit' για έξοδο)")
    
    choice = input("> ").strip()
    if choice == "1": buy_item(pet)
    elif choice == "2": buy_decor(pet)
    elif choice == "3": buy_stardust_upgrade(pet)
    else: print("Έξοδος από κατάστημα.")

def buy_item(pet):
    print("\n--- 🏪 Κατάστημα Αντικειμένων ---")
    charm_discount = get_charm_discount(pet)
    event_discount = 0.25 if pet["current_event"]["type"] == "Μέρα Αγοράς" else 0.0
    total_discount = charm_discount + event_discount
    if total_discount > 0: print(f"Σημερινή Έκπτωση: {total_discount*100:.0f}%!")
    
    for key, item in SHOP_ITEMS.items():
        price = int(item['price'] * (1.0 - total_discount))
        print(f"[{key}] {item['name']} - {price}¢")
    print(f"Έχεις {pet['coins']}¢. (Εισάγετε 'exit' για έξοδο)")
    
    choice = input("Τι θέλεις να αγοράσεις; > ").strip().lower()
    if choice in SHOP_ITEMS:
        item = SHOP_ITEMS[choice]
        price = int(item['price'] * (1.0 - total_discount))
        if pet["coins"] >= price:
            pet["coins"] -= price
            item_name = item["name"]
            pet["inventory"][item_name] = pet["inventory"].get(item_name, 0) + 1
            print(f"🛒 Αγόρασες 1 {item_name}! Έχεις {pet['inventory'][item_name]}.")
            add_xp(pet, 2)
        else: print("Δεν έχεις αρκετά νομίσματα!")
    else: print("Μη έγκυρο αντικείμενο.")

def buy_decor(pet): # v8
    print("\n--- 🏠 Κατάστημα Διακόσμησης ---")
    print(f"Έχεις {pet['coins']}¢.")
    
    for key, item in DECOR_ITEMS.items():
        owned = " (Έχεις)" if item["name"] in pet["decor"] else ""
        print(f"[{key}] {item['name']} - {item['price']}¢{owned}\n    ({item['desc']})")
    print("(Εισάγετε 'exit' για έξοδο)")
    
    choice = input("Τι θέλεις να αγοράσεις; > ").strip().lower()
    if choice in DECOR_ITEMS:
        item = DECOR_ITEMS[choice]
        item_name = item["name"]
        price = item["price"]
        
        if item_name in pet["decor"]:
            print("Το έχεις ήδη αυτό το αντικείμενο!"); return
        if pet["coins"] >= price:
            pet["coins"] -= price
            pet["decor"].append(item_name)
            print(f"🛋️ Αγόρασες 1 {item_name}! Το σπίτι σου φαίνεται πιο ωραίο.")
            add_xp(pet, 15)
            if len(pet["decor"]) >= 3:
                grant_achievement(pet, "home_decorator_3")
        else: print("Δεν έχεις αρκετά νομίσματα!")
    else: print("Μη έγκυρο αντικείμενο.")

def buy_stardust_upgrade(pet): # v8
    print("\n--- ✨ Κατάστημα Stardust (Μόνιμες Βελτιώσεις) ---")
    print(f"Έχεις {pet['stardust']} Stardust ✨.")
    
    for key, item in STARDUST_UPGRADES.items():
        current_mod = pet["legacy_bonus"].get(item["key"], 1.0)
        current_bonus_pct = (current_mod - 1.0) * 100
        print(f"[{key}] {item['name']} - Κόστος: {item['cost']} ✨\n    (Τρέχον: +{current_bonus_pct:.0f}%, Αγορά για: +{item['amount']*100:.0f}%)")
    print("(Εισάγετε 'exit' για έξοδο)")

    choice = input("Τι θέλεις να αγοράσεις; > ").strip().lower()
    if choice in STARDUST_UPGRADES:
        item = STARDUST_UPGRADES[choice]
        cost = item["cost"]
        if pet["stardust"] >= cost:
            pet["stardust"] -= cost
            key = item["key"]
            pet["legacy_bonus"][key] = pet["legacy_bonus"].get(key, 1.0) + item["amount"]
            print(f"🌌 Ενίσχυση Κληρονομιάς! Το {item['name']} σου είναι τώρα +{(pet['legacy_bonus'][key] - 1.0)*100:.0f}%.")
        else: print("Δεν έχεις αρκετό Stardust! Στείλε έναν Γηραιό στη σύνταξη για να πάρεις περισσότερο.")
    else: print("Μη έγκυρο αντικείμενο.")

def use_item(pet):
    if pet["age_stage"] == "Αβγό": print("Το αβγό δεν χρειάζεται αντικείμενα."); return
    print("\n--- 🎒 Η Αποθήκη σου ---")
    items = [name for name, count in pet["inventory"].items() if count > 0]
    if not items:
        print("Η αποθήκη είναι άδεια. Επισκέψου το κατάστημα για να αγοράσεις αντικείμενα!"); return
    for i, name in enumerate(items, 1): print(f"[{i}] {name} (x{pet['inventory'][name]})")
    print("(Εισάγετε 'exit' για ακύρωση)")
    
    try:
        choice = input("Χρήση ποιου αντικειμένου; > ").strip().lower()
        if choice == "exit": return
        item_name = items[int(choice) - 1]
        
        if pet["inventory"][item_name] > 0:
            pet["inventory"][item_name] -= 1
            if item_name == "Ειδικό Φαγητό":
                pet["hunger"] = clamp(pet["hunger"] + 60); pet["happiness"] = clamp(pet["happiness"] + 20)
                print(f"Ουάου! Νόστιμο! XP +{add_xp(pet, 15)}")
            elif item_name == "Καινούριο Παιχνίδι":
                pet["happiness"] = clamp(pet["happiness"] + 50); pet["energy"] = clamp(pet["energy"] - 15)
                add_skill(pet, "agility", 1.0)
                print(f"Τόσο διασκεδαστικό! XP +{add_xp(pet, 20)}. Ευκιν +1.0")
            elif item_name == "Φάρμακο":
                if pet["is_sick"] or pet["health"] < 100:
                    pet["is_sick"] = False; pet["health"] = clamp(pet["health"] + 50); pet["happiness"] = clamp(pet["happiness"] + 10)
                    print("Α, πολύ καλύτερα! Αισθάνομαι υγιές ξανά!")
                else:
                    pet["happiness"] = clamp(pet["happiness"] - 10); print("Δεν χρειάζεσαι φάρμακο! Μπλιαχ.")
                add_xp(pet, 10)
            elif item_name == "Βιβλίο":
                print("Δεν μπορείς να 'χρησιμοποιήσεις' ένα βιβλίο. Δοκίμασε την ενέργεια '[r]ead'."); pet["inventory"]["Βιβλίο"] += 1
            elif item_name == "Ενεργειακό Ποτό":
                pet["energy"] = clamp(pet["energy"] + 60); pet["hunger"] = clamp(pet["hunger"] - 20)
                print(f"BUZZ! Γεμάτος ενέργεια! XP +{add_xp(pet, 5)}")
            elif item_name == "Σπάνιο Σνακ":
                pet["hunger"] = 100; pet["happiness"] = 100; pet["energy"] = 100
                print(f"Απίστευτο! Αυτό ήταν το καλύτερο σνακ ever! XP +{add_xp(pet, 30)}")
            elif item_name == "Βιταμίνες":
                pet["health"] = clamp(pet["health"] + 25)
                print(f"Γλουκ γλουκ! Η υγεία ενισχύθηκε! XP +{add_xp(pet, 5)}")
        else: print("Δεν έχεις αυτό το αντικείμενο!")
    except (ValueError, IndexError): print("Μη έγκυρη επιλογή.")

# -------------------- ΔΡΑΣΗ ΠΕΡΙΠΑΤΟΥ (v7) --------------------
def walk(pet):
    if pet["age_stage"] == "Αβγό": print("Το αβγό... κυλάει λίγο."); return
    if pet["current_event"]["type"] == "Βροχερή Μέρα": print("Βρέχει πολύ!"); return
    if pet["energy"] < 20 or pet["is_sick"]: print("Πολύ κουρασμένο ή άρρωστο για περίπατο."); return
        
    print("🚶 Πηγαίνουμε για περίπατο..."); update_dialogue(pet, "walk")
    pet["energy"] = clamp(pet["energy"] - 15)
    
    xp_mod = get_mod(pet, "walk_xp")
    coin_mod = get_mod(pet, "walk_coins") * pet.get("legacy_bonus", {}).get("coin_mod", 1.0)
    luck_mod = get_luck_bonus(pet)
    
    if pet["current_event"]["type"] == "Ηλιόλουστη Μέρα": coin_mod *= 1.5
    
    event_roll = random.random() * luck_mod
    if event_roll > 1.2:
        coins = int(random.randint(50, 100) * coin_mod)
        pet["coins"] += coins; pet["happiness"] = clamp(pet["happiness"] + 20)
        print(f"🍀 Σούπερ τυχερός! Βρήκες ένα πορτοφόλι με {coins}¢! XP +{add_xp(pet, 20 * xp_mod)}")
    elif event_roll > 0.7:
        coins = int(random.randint(10, 25) * coin_mod * luck_mod)
        pet["coins"] += coins
        print(f"Βρήκες {coins}¢! XP +{add_xp(pet, 5 * xp_mod)}")
    elif event_roll > 0.4:
        pet["happiness"] = clamp(pet["happiness"] + 15)
        print(f"Τι υπέροχος περίπατος! XP +{add_xp(pet, 10 * xp_mod)}")
    else:
        pet["cleanliness"] = clamp(pet["cleanliness"] - 30); pet["happiness"] = clamp(pet["happiness"] - 10)
        print(f"Ωχ όχι! Έπεσες σε μια λακκούβα λάσπης! XP +{add_xp(pet, 5 * xp_mod)}"); update_dialogue(pet, "dirty")
    
    add_skill(pet, "agility", 0.3 * get_mod(pet, "agi_gain"))
    add_skill(pet, "luck", 0.1 * get_mod(pet, "luck_gain"))

# -------------------- ΜΙΝΙ ΠΑΙΧΝΙΔΙΑ (v8) --------------------
def get_game_mods(pet):
    xp_mod = get_mod(pet, "game_xp")
    hap_mod = get_mod(pet, "game_happiness")
    if pet["current_event"]["type"] == "Μέρα Φεστιβάλ": xp_mod *= 2.0
    if pet["evolution_type"] == "Ιδιοφυΐα": xp_mod *= 1.3; hap_mod *= 1.2
    
    # v8: Μπόνους Χόμπι
    if pet["hobby"] == "Παιχνίδι":
        xp_mod *= 1.3
        hap_mod *= 2.0
        print("🎮 Αυτό είναι το αγαπημένο του χόμπι! Επιπλέον XP/Χαρά!")
        
    return xp_mod, hap_mod

def game_guess_number(pet):
    if pet["age_stage"] == "Αβγό": print("..."); return
    print("\n🎮 Μάντεψε τον Αριθμό (1-5)!")
    num = random.randint(1, 5)
    xp_mod, hap_mod = get_game_mods(pet)
    try:
        guess = int(input("Η εικασία σου: "))
        if guess == num:
            xp = add_xp(pet, 20 * xp_mod)
            print(f"🎉 Σωστά! XP +{xp}")
            pet["happiness"] = clamp(pet["happiness"] + 15 * hap_mod)
        else:
            xp = add_xp(pet, 5 * xp_mod)
            print(f"❌ Λάθος! Ήταν {num}. XP +{xp}")
            pet["happiness"] = clamp(pet["happiness"] - 3)
    except: print("Μη έγκυρη εισαγωγή!")
    update_dialogue(pet, "game")

def game_rps(pet):
    if pet["age_stage"] == "Αβγό": print("..."); return
    print("\n✊✋✌️ Πέτρα-Ψαλίδι-Χαρτί!")
    moves = ["πέτρα", "χαρτί", "ψαλίδι"]
    comp = random.choice(moves)
    xp_mod, hap_mod = get_game_mods(pet)
    try:
        player = input("Επίλεξε πέτρα/χαρτί/ψαλίδι: ").lower()
        if player not in moves: print("Μη έγκυρη κίνηση!"); return
        print(f"Το κατοικίδιο επιλέγει: {comp}")
        if player == comp:
            xp = add_xp(pet, 5 * xp_mod)
            print(f"🤝 Ισοπαλία! XP +{xp}")
        elif (player == "πέτρα" and comp == "ψαλίδι") or \
             (player == "ψαλίδι" and comp == "χαρτί") or \
             (player == "χαρτί" and comp == "πέτρα"):
            xp = add_xp(pet, 15 * xp_mod)
            print(f"🎉 Κέρδισες! XP +{xp}")
            pet["happiness"] = clamp(pet["happiness"] + 10 * hap_mod)
        else:
            xp = add_xp(pet, 5 * xp_mod)
            print(f"😢 Έχασες! XP +{xp}")
            pet["happiness"] = clamp(pet["happiness"] - 5)
    except: print("Σφάλμα στο παιχνίδι")
    update_dialogue(pet, "game")

# Προσθήκη λίστας ερωτήσεων και λέξεων για τα παιχνίδια
STUDY_QUESTIONS = [
    {"q": "Πόσα είναι 2+2;", "a": "4"},
    {"q": "Ποιο είναι το πρώτο γράμμα του αλφαβήτου;", "a": "α"},
    {"q": "Πόσες μέρες έχει η εβδομάδα;", "a": "7"},
]

TYPING_WORDS = ["γάτα", "σκύλος", "παπαγάλος", "dragon", "computer"]

def game_study(pet):
    if pet["age_stage"] == "Αβγό": print("..."); return
    print("\n🧠 Ώρα Μελέτης! Απάντησε στην ερώτηση.");
    if pet["energy"] < 10: print("Πολύ κουρασμένος για μελέτη."); return
    xp_mod, hap_mod = get_game_mods(pet)
    pet["energy"] = clamp(pet["energy"] - 5)
    question = random.choice(STUDY_QUESTIONS)
    try:
        answer = input(f"Ε: {question['q']} > ").strip().lower()
        if answer == question['a']:
            xp = add_xp(pet, 25 * xp_mod)
            print(f"🎉 Σωστά! Τόσο έξυπνος! XP +{xp}")
            pet["happiness"] = clamp(pet["happiness"] + 10 * hap_mod)
            add_skill(pet, "intelligence", 1.0 * get_mod(pet, "int_gain"))
        else:
            xp = add_xp(pet, 5 * xp_mod)
            print(f"❌ Λάθος! Η απάντηση ήταν '{question['a']}'. XP +{xp}")
            pet["happiness"] = clamp(pet["happiness"] - 3)
            add_skill(pet, "intelligence", 0.1)
    except: print("Σφάλμα στο παιχνίδι")
    update_dialogue(pet, "game")

def game_typing(pet):
    if pet["age_stage"] == "Αβγό": print("..."); return
    print("\n⌨️ Δοκιμασία Ταχύτητας Πληκτρολόγησης! Πληκτρολόγησε τη λέξη ΓΡΗΓΟΡΑ!")
    if pet["energy"] < 10: print("Πολύ κουρασμένος για πληκτρολόγηση."); return
    xp_mod, hap_mod = get_game_mods(pet)
    pet["energy"] = clamp(pet["energy"] - 5)
    word = random.choice(TYPING_WORDS)
    try:
        print(f"Πληκτρολόγησε αυτή τη λέξη: {word}")
        start_time = time.time()
        answer = input("> ").strip().lower()
        end_time = time.time()
        if answer == word:
            time_taken = end_time - start_time
            xp_reward = clamp(20 - (time_taken * 2), 5, 30)
            xp = add_xp(pet, xp_reward * xp_mod)
            print(f"🎉 Τέλεια! Χρόνος: {time_taken:.2f}δ. XP +{xp}")
            pet["happiness"] = clamp(pet["happiness"] + 10 * hap_mod)
            add_skill(pet, "agility", 0.5 * get_mod(pet, "agi_gain"))
            add_skill(pet, "intelligence", 0.2 * get_mod(pet, "int_gain"))
        else:
            xp = add_xp(pet, 2 * xp_mod)
            print(f"❌ Λάθος! Πληκτρολόγησες '{answer}'. XP +{xp}")
            pet["happiness"] = clamp(pet["happiness"] - 3)
    except: print("Σφάλμα στο παιχνίδι")
    update_dialogue(pet, "game")

# -------------------- v8: ΚΛΗΡΟΝΟΜΙΑ / ΣΥΝΤΑΞΗ --------------------
def retire_pet(pet):
    if pet["age_stage"] != "Γηραιό":
        print("Μόνο Γηραιοί μπορούν να πάνε στη σύνταξη."); return pet
    if pet["level"] < RETIRE_LEVEL:
        print(f"Το κατοικίδιό σου πρέπει να είναι τουλάχιστον Επίπεδο {RETIRE_LEVEL} για σύνταξη."); return pet

    print(f"\n--- 🌌 Κοσμική Σύνταξη ---")
    print(f"Το {pet['name']} έχει ζήσει μια μακρά, πλήρη ζωή (Επίπεδο {pet['level']}).")
    
    # Υπολογισμός Stardust
    stardust_gain = (pet["level"] // 2) + (sum(pet["skills"].values()) // 10)
    stardust_gain = int(stardust_gain)
    
    print(f"Η σύνταξη θα τελειώσει το ταξίδι αυτού του κατοικίδιου και θα σου δώσει {stardust_gain} Stardust ✨.")
    print("Αυτό το Stardust μπορεί να χρησιμοποιηθεί για αγορά μόνιμων βελτιώσεων για το *επόμενο* κατοικίδιό σου.")
    
    confirm = input("Είσαι σίγουρος ότι θέλεις να στείλεις στη σύνταξη; (ναι/όχι) > ").strip().lower()
    
    if confirm == "ναι":
        print(f"Αντίο, {pet['name']}! Η κληρονομιά σου θα ζήσει...")
        time.sleep(2)
        
        # Δημιουργία νέου κατοικίδιου, αλλά μεταφορά στατιστικών κληρονομιάς
        new_pet = DEFAULT_PET.copy()
        new_pet["stardust"] = pet["stardust"] + stardust_gain
        new_pet["legacy_bonus"] = pet["legacy_bonus"].copy() # Μεταφορά παλιών μπόνους
        
        save_pet(new_pet) # Αποθήκευση νέου κατοικίδιου
        grant_achievement(new_pet, "cosmic_legacy_1") # Χορήγηση στο νέο κατοικίδιο
        
        print("\n\nΈνα νέο αβγό εμφανίζεται, λαμπυρίζοντας με κοσμική ενέργεια...")
        print(f"Έχεις συνολικά {new_pet['stardust']} Stardust.")
        time.sleep(3)
        return new_pet
    else:
        print("Ακύρωση σύνταξης."); return pet

# -------------------- ΑΥΤΟΜΑΤΗ ΑΠΟΘΗΚΕΥΣΗ --------------------
def auto_save_loop(pet, stop_event):
    while not stop_event.is_set():
        time.sleep(AUTOSAVE_INTERVAL)
        if stop_event.is_set(): break
        check_daily_event(pet)
        tick(pet)
        save_pet(pet)

# -------------------- ΚΥΡΙΟΣ ΒΡΟΓΧΟΣ --------------------
def main():
    pet = load_pet()
    if pet.get("name", "Τάμα") == "Τάμα" and pet["age_minutes"] < 1:
        # --- Πρώτη Φορά Ρύθμιση ---
        name = input(f"Δώσε όνομα στο νέο σου κατοικίδιο (προκαθορισμένο {pet['name']}): ").strip()
        if name: pet["name"] = name
        
        print("\nΕπίλεξε μια προσωπικότητα:")
        personalities = ["Παιχνιδιάρικο", "Τεμπέλικο", "Γκρινιάρικο", "Έξυπνο", "Περίεργο"]
        for i, p in enumerate(personalities, 1): print(f"[{i}] {p}")
        try:
            choice = int(input("> ")) - 1
            if 0 <= choice < len(personalities): pet["personality"] = personalities[choice]
        except: pet["personality"] = "Περίεργο"
        
        # v8: Χορήγηση αρχικών πόντων ικανότητας
        if pet["personality"] == "Έξυπνο": add_skill(pet, "intelligence", 3); add_skill(pet, "focus", 3)
        if pet["personality"] == "Παιχνιδιάρικο": add_skill(pet, "charm", 3); add_skill(pet, "strength", 3)
        if pet["personality"] == "Περίεργο": add_skill(pet, "agility", 3); add_skill(pet, "luck", 3)
            
        print(f"Το κατοικίδιό σου είναι {pet['personality']}!")
        check_daily_event(pet)
        save_pet(pet)
        print(f"\nΤο νέο σου αβγό κατοικίδιο επωάζεται. Θα εκκολαφθεί σε {AGE_TO_CHILD} λεπτά.")
        time.sleep(2)

    check_daily_event(pet)
    stop_event = threading.Event()
    saver = threading.Thread(target=auto_save_loop, args=(pet, stop_event), daemon=True)
    saver.start()
    last_dialogue_update = 0

    try:
        while True:
            tick(pet)
            
            if time.time() - last_dialogue_update > 15:
                update_dialogue(pet)
                last_dialogue_update = time.time()
                
            os.system("clear" if os.name != 'nt' else 'cls')
            
            if pet["skill_points"] > 0:
                print(f"*** 🔥 Έχεις {pet['skill_points']} Πόντο(ους) Ικανότητας για να ξοδέψεις! Πάτα [k] ***")
            
            event = pet["current_event"]["type"]
            if event != "Καμία": print(f"*** ΓΕΓΟΝΟΣ: {event} ***")
            
            print(f"--- Το {pet['name']} λέει ---")
            print(f"> {pet['dialogue']}")
            print(ascii_pet(pet))
            print(status_text(pet))
            print("-" * 20)
            print("Ενέργειες: [f]eed [p]lay [s]leep [c]lean [r]ead")
            print("           [w]alk [t]rain [m]editate [j]ob [u]se")
            print("Διαχείριση:  [shop] [k]spend_sp [st]ats")
            print("Παιχνίδια:   [1]Μάντεψε [2]Πέτρα-Ψαλίδι-Χαρτί [3]Μελέτη [4]Πληκτρολόγηση")
            if pet["age_stage"] == "Γηραιό":
                 print(f"Κληρονομιά:  [retire] (Επ {pet['level']}/{RETIRE_LEVEL})")
            print("Σύστημα:  [z]save [q]quit")
            print("-" * 20)
            
            if pet["age_stage"] == "Αβγό":
                cmd = input("> ").strip().lower()
            elif pet["is_sick"] and pet["health"] < 10:
                print(f"Το {pet['name']} είναι πολύ άρρωστο για να κάνει τίποτα! Χρησιμοποίησε Φάρμακο!")
                cmd = input("> ").strip().lower()
                if cmd not in ['u', 'q', 'z', 'st']: cmd = 'blocked'
            else:
                cmd = input("> ").strip().lower()
            
            # --- Τυπικές Ενέργειες ---
            if cmd == "f": feed(pet)
            elif cmd == "p": play(pet)
            elif cmd == "s": sleep(pet)
            elif cmd == "c": clean(pet)
            elif cmd == "r": read_book(pet)
            elif cmd == "w": walk(pet)
            elif cmd == "t": train(pet)
            elif cmd == "j": work_job(pet)
            elif cmd == "u": use_item(pet)
            
            # --- v8 Ενέργειες ---
            elif cmd == "m": meditate(pet)
            elif cmd == "shop": shop_menu(pet) # v8
            elif cmd == "k": spend_sp(pet)
            elif cmd == "st": show_stats(pet) # v8
            elif cmd == "retire" and pet["age_stage"] == "Γηραιό":
                new_pet = retire_pet(pet) # v8
                if new_pet["name"] != pet["name"]: # Έλεγχος αν έγινε σύνταξη
                    pet = new_pet # Έναρξη ζωής νέου κατοικίδιου
                    continue # Άμεση επανεκκίνηση βρόχου

            # --- Παιχνίδια ---
            elif cmd == "1": game_guess_number(pet)
            elif cmd == "2": game_rps(pet)
            elif cmd == "3": game_study(pet)
            elif cmd == "4" : game_typing(pet)
            
            # --- Σύστημα ---
            elif cmd in ("z", "save"): save_pet(pet); print("💾 Αποθηκεύτηκε!")
            elif cmd in ("q", "quit", "exit"): print("Αποθήκευση και έξοδος..."); save_pet(pet); break
            elif cmd == "blocked": pass
            elif pet["age_stage"] == "Αβγό": print("Το αβγό απλά κάθεται εκεί...")
            else: print("❓ Άγνωστη εντολή.")
                
            time.sleep(0.7)
            save_pet(pet)
            
    except KeyboardInterrupt:
        print("\nΔιάκοψη. Αποθήκευση και έξοδος...")
        save_pet(pet)
    finally:
        stop_event.set()
        saver.join(timeout=1)
        print(f"Αντίο! Έλα πίσω να επισκεφτείς το {pet['name']} σύντομα!")
        sys.exit(0)

if __name__ == "__main__":
    main()