#!/usr/bin/env python3
"""
Tamagotchi
"""

import os, json, time, threading, random, subprocess, sys

# -------------------- CONFIG --------------------
HOME = os.path.expanduser("~")
SAVE_PATH = os.path.join(HOME, ".termux_tamagotchi_v8.json") # v8 save file
AUTOSAVE_INTERVAL = 60
DECAY_PER_MIN = {
    "hunger": 1.0, "happiness": 0.5, "energy": 0.7, "cleanliness": 0.4,
    "health": 0.0 
}
MAX_XP_PER_LEVEL = 100
RETIRE_LEVEL = 25 # v8: Level an Elder must be to retire
AGE_TO_CHILD = 3     # Minutes (Hatch from Egg)
AGE_TO_TEEN = 720    # Minutes (12 hours)
AGE_TO_ADULT = 2160  # Minutes (36 hours total)
AGE_TO_ELDER = 5760  # Minutes (4 days total)
SECONDS_PER_DAY = 86400

# -------------------- DEFAULT PET --------------------
DEFAULT_PET = {
    "name": "Tama",
    "created_at": time.time(),
    "last_tick": time.time(),
    "hunger": 80,
    "happiness": 80,
    "energy": 80,
    "cleanliness": 90,
    "health": 100,
    "is_sick": False,
    "age_minutes": 0,
    "age_stage": "Egg",
    "evolution_type": "None",
    "hobby": "None", # v8
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
    "personality": random.choice(["Playful", "Lazy", "Grumpy", "Smart", "Curious"]),
    "coins": 50,
    "inventory": {
        "Special Food": 1, "New Toy": 0, "Medicine": 0, "Book": 1,
        "Energy Drink": 0, "Rare Snack": 0, "Vitamins": 0,
    },
    "decor": [], # v8: List of owned decor items
    "skills": {
        "intelligence": 0, "agility": 0, "charm": 0,
        "strength": 0, "luck": 0, "focus": 0, # v8
    },
    "current_event": {
        "type": "None", "last_update": 0,
    },
    "dialogue": "...",
    # v8: Legacy system. These stats persist across retirement!
    "stardust": 0,
    "legacy_bonus": {
        "xp_mod": 1.0,
        "coin_mod": 1.0,
        "sp_mod": 1.0, # Not used for purchase, but for 'Focus'
    },
}

# -------------------- v6/v7: DAILY EVENTS --------------------
DAILY_EVENTS = [
    "None", "Sunny Day", "Rainy Day", "Market Day", "Sick Day",
    "Double XP Day", "Festival Day", "Heat Wave", "Good Fortune",
]

def check_daily_event(pet):
    now = time.time()
    last_update = pet.get("current_event", {}).get("last_update", 0)
    
    if now - last_update > SECONDS_PER_DAY:
        pet["current_event"]["type"] = random.choice(DAILY_EVENTS)
        pet["current_event"]["last_update"] = now
        event_name = pet["current_event"]["type"]
        if event_name != "None":
            notify("📅 Daily Event!", f"Today is a {event_name}!")
        # (Dialogue updates omitted for brevity, logic is the same as v7)
        if event_name == "Sick Day": pet["is_sick"] = True

# -------------------- v8: SKILLS & MODIFIERS --------------------
def add_skill(pet, skill, amount):
    mod = 1.0
    p = pet["personality"]
    if skill == "intelligence" and p == "Smart": mod = 1.5
    elif skill == "agility" and p == "Curious": mod = 1.3
    elif skill == "charm" and p == "Playful": mod = 1.3
    elif skill == "strength" and p == "Playful": mod = 1.2
    elif skill == "focus" and p == "Smart": mod = 1.3 # v8
    elif skill == "focus" and p == "Lazy": mod = 1.5 # v8
        
    pet["skills"][skill] = round(pet["skills"][skill] + (amount * mod), 2)

def get_skill_level(pet, skill):
    return int(pet["skills"][skill] // 10) + 1

def get_charm_discount(pet):
    level = get_skill_level(pet, "charm")
    return min(0.30, level * 0.01)

def get_intel_bonus(pet):
    level = get_skill_level(pet, "intelligence")
    # v8: Decor bonus
    mod = 1.1 if "Bookshelf" in pet["decor"] else 1.0
    return (1.0 + (level * 0.05)) * mod

def get_agility_bonus(pet):
    level = get_skill_level(pet, "agility")
    return 1.0 + (level * 0.05)

def get_strength_bonus(pet):
    level = get_skill_level(pet, "strength")
    mod = 1.1 if "Training Mat" in pet["decor"] else 1.0 # v8
    return (1.0 + (level * 0.05)) * mod

def get_luck_bonus(pet):
    level = get_skill_level(pet, "luck")
    mod = 1.0 + (level * 0.03)
    if pet["current_event"]["type"] == "Good Fortune": mod *= 2.0
    return mod

def get_focus_bonus(pet): # v8
    """Focus increases chance to get bonus SP on level up"""
    level = get_skill_level(pet, "focus")
    # 5% chance per level to get +1 SP. Capped at 50%
    return min(0.5, level * 0.05)

# -------------------- PERSONALITY MODS (v7/v8) --------------------
PERSONALITY_MODS = {
    "Playful": {
        "happiness_decay": 1.2, "energy_decay": 1.1,
        "play_happiness": 1.5, "play_xp": 1.2,
        "strength_gain": 1.2, "charm_gain": 1.2,
    },
    "Lazy": {
        "energy_decay": 0.7, "hunger_decay": 1.1,
        "play_happiness": 0.5, "play_energy": 0.5, "sleep_energy": 1.3,
        "strength_gain": 0.5, "focus_gain": 1.5,
    },
    "Grumpy": {
        "happiness_decay": 1.3, "play_happiness": 0.7,
        "feed_happiness": 0.5, "clean_happiness": 0.7,
    },
    "Smart": {
        "game_xp": 1.5, "game_happiness": 1.2,
        "int_gain": 1.5, "focus_gain": 1.3,
    },
    "Curious": {
        "happiness_decay": 0.9, "walk_coins": 1.5, "walk_xp": 1.3,
        "agi_gain": 1.3, "luck_gain": 1.5,
    },
}
def get_mod(pet, key):
    return PERSONALITY_MODS.get(pet["personality"], {}).get(key, 1.0)

# -------------------- DIALOGUE (v7/v8) --------------------
DIALOGUE = {
    "Default": {
        "happy": ["I feel great!", "Life is good."],
        "excited": ["BEST DAY EVER!", "WOWOWOW!"],
        "neutral": ["Hmm.", "...", "Just vibing."],
        "hungry": ["My tummy is rumbling...", "Food, please?"],
        "sleepy": ["*yawn*", "I need a nap."],
        "dirty": ["I feel icky.", "Bath time?"],
        "sad": ["Feeling a bit down.", "I could use a hug."],
        "sick": ["*cough*", "I don't feel so good..."],
        "train": ["Hup, hup, hup!", "Feeling stronger!"],
        "job": ["Time to earn some coins.", "Off to work!"],
        "meditate": ["Ooooommmm...", "Inner peace."], # v8
    },
    "Playful": {
        "happy": ["Let's play!", "Catch me if you can!", "Play play play!"],
        "train": ["Is this a game? I'll win!", "Look how fast I am!"],
    },
    "Lazy": {
        "sleepy": ["My default state.", "Good night.", "Wake me up never."],
        "train": ["*pant*... Already done?", "This is too much work."],
        "job": ["Do I *have* to?"],
        "meditate": ["Is this just... napping with extra steps?"], # v8
    },
    "Grumpy": {
        "neutral": ["Whatever.", "Leave me alone.", "What do you want?"],
        "hungry": ["Where is my food?! NOW!", "You're late."],
    },
    "Smart": {
        "neutral": ["Pondering the universe.", "I require stimulation."],
        "game": ["That was... simple.", "Try to challenge me next time."],
        "read": ["Ah, new information!", "Fascinating."],
        "job": ["My intellect is a valuable resource."],
        "meditate": ["Clearing my mind for new thoughts."], # v8
    },
    "Curious": {
        "neutral": ["What are you doing?", "What's over there?"],
        "walk": ["Let's go explore!", "Adventure time!"],
    },
    # v8: Hobby-specific dialogue
    "Hobby_Gaming": ["Time to smash my high score!", "Just one more level..."],
    "Hobby_Reading": ["I wonder what happens in the next chapter?", "So lost in this book!"],
    "Hobby_Training": ["Gotta get those gains!", "Feel the burn!"],
}

def update_dialogue(pet, context=None):
    if pet["age_stage"] == "Egg":
        pet["dialogue"] = random.choice(["...", "*tap tap*", "...", "...", "*wiggle*"])
        return
        
    m = mood(pet)
    p = pet["personality"]
    
    # v8: Hobby context
    if context == "game" and pet["hobby"] == "Gaming":
        context = "Hobby_Gaming"
    elif context == "read" and pet["hobby"] == "Reading":
        context = "Hobby_Reading"
    elif context == "train" and pet["hobby"] == "Training":
        context = "Hobby_Training"
    
    if "Day" in pet["current_event"]["type"] and not context: return
    
    options = DIALOGUE.get(p, {}).get(context or m, [])
    if not options:
        options = DIALOGUE.get("Default", {}).get(context or m, ["..."])
        
    pet["dialogue"] = random.choice(options)

# -------------------- UTILS --------------------
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
        notify("🏆 Achievement Unlocked!", key_name)
        print(f"*** 🏆 Achievement Unlocked: {key_name} ***")
        add_xp(pet, 25)

def save_pet(pet):
    try:
        with open(SAVE_PATH, "w") as f:
            json.dump(pet, f, indent=2)
    except Exception as e:
        print(f"Error saving pet: {e}")

def load_pet():
    if not os.path.exists(SAVE_PATH):
        print("No save file found, creating a new pet!")
        save_pet(DEFAULT_PET)
        return DEFAULT_PET.copy()
    try:
        with open(SAVE_PATH, "r") as f:
            data = json.load(f)
        
        # v8: More robust merging for new top-level AND nested keys
        merged_pet = DEFAULT_PET.copy()
        
        # Copy legacy stats first, as they are independent
        merged_pet["stardust"] = data.get("stardust", 0)
        merged_pet["legacy_bonus"] = DEFAULT_PET["legacy_bonus"].copy()
        merged_pet["legacy_bonus"].update(data.get("legacy_bonus", {}))
        
        # Now merge the current pet's data
        for k, v in data.items():
            if k in ["stardust", "legacy_bonus"]: continue # Already handled
            
            if k in merged_pet and isinstance(merged_pet[k], dict):
                merged_pet[k].update(data[k])
            else:
                merged_pet[k] = data[k]
        
        # Final pass to ensure all *new* default keys/sub-keys exist
        for k, v_default in DEFAULT_PET.items():
            if k not in merged_pet:
                merged_pet[k] = v_default
            elif isinstance(v_default, dict):
                for sk, sv_default in v_default.items():
                    if sk not in merged_pet[k]:
                        merged_pet[k][sk] = sv_default
                         
        return merged_pet
    except Exception as e:
        print(f"Error loading save, creating new pet. Error: {e}")
        # os.remove(SAVE_PATH) # Risky, let's just make a new one
        save_pet(DEFAULT_PET)
        return DEFAULT_PET.copy()

# v8: Hobby Assignment
def assign_hobby(pet):
    if pet["hobby"] != "None": return
    
    print(f"\n🌟 {pet['name']} is growing up and needs a hobby!")
    skills = pet["skills"]
    
    # Find highest skill
    # We exclude luck/focus as they aren't "activities"
    activity_skills = {
        "intelligence": skills["intelligence"],
        "agility": skills["agility"],
        "strength": skills["strength"],
    }
    highest_skill_name = max(activity_skills, key=activity_skills.get)
    
    if highest_skill_name == "intelligence":
        # Check if they read more or game more
        if skills["intelligence"] > (skills["agility"] + skills["strength"]):
             pet["hobby"] = "Reading"
        else:
             pet["hobby"] = "Gaming"
    elif highest_skill_name == "strength":
        pet["hobby"] = "Training"
    elif highest_skill_name == "agility":
        pet["hobby"] = "Gaming" # Agility contributes to gaming
    else:
        pet["hobby"] = "Gaming" # Default
        
    print(f"Based on their skills, their new hobby is {pet['hobby']}!")
    pet["dialogue"] = f"I've decided I really love {pet['hobby']}!"
    time.sleep(1.5)

def tick(pet):
    now = time.time()
    elapsed = now - pet["last_tick"]
    minutes = elapsed / 60
    if minutes <= 0: return

    if pet["age_stage"] == "Egg":
        pet["age_minutes"] += minutes
        pet["last_tick"] = now
        if pet["age_minutes"] > AGE_TO_CHILD:
            pet["age_stage"] = "Child"
            pet["dialogue"] = "Hello world!"
            notify("🥚 Hatched!", f"Your new pet {pet['name']} has hatched!")
            grant_achievement(pet, "hatched")
        return

    event = pet["current_event"]["type"]
    decay_mult = 1.0
    if event == "Sick Day": decay_mult = 1.5
    if event == "Sunny Day": decay_mult = 0.7
    # v8: Focus reduces negative event impact
    if decay_mult > 1.0:
        decay_mult -= (get_focus_bonus(pet) * 0.5) # Focus bonus is 50% effective here
    
    for stat, decay in DECAY_PER_MIN.items():
        if stat == "health": continue
        
        mod = get_mod(pet, f"{stat}_decay") * decay_mult
        
        # v8: Decor passive bonuses
        if stat == "happiness" and "Plush Rug" in pet["decor"]: mod *= 0.9
        if stat == "cleanliness" and "Auto-Cleaner" in pet["decor"]: mod *= 0.8
        
        # Event mods
        if event == "Sunny Day" and stat == "happiness": mod *= 0.5
        if event == "Rainy Day" and stat == "energy": mod *= 0.7
        if event == "Rainy Day" and stat == "cleanliness": mod *= 1.5
        if event == "Heat Wave" and stat == "energy": mod *= 2.0
            
        pet[stat] = clamp(pet[stat] - (decay * mod * minutes))
    
    # Health & Sickness logic (same as v7)
    health_decay = 0
    if pet["is_sick"]: health_decay += 0.5 * minutes
    if pet["hunger"] < 5: health_decay += (0.2 * minutes) * (5 - pet["hunger"])
    if pet["energy"] < 5: health_decay += 0.1 * minutes
    pet["health"] = clamp(pet["health"] - health_decay)
    if pet["cleanliness"] < 10 and not pet["is_sick"] and random.random() < (0.1 * minutes):
        pet["is_sick"] = True
        pet["dialogue"] = "*achoo!* I feel sick..."
        notify("🤒 Sickness!", f"{pet['name']} got sick from being dirty!")
    if pet["health"] < 20: pet["is_sick"] = True
    elif pet["health"] > 80 and pet["is_sick"] and event != "Sick Day":
        pet["is_sick"] = False
        pet["dialogue"] = "Phew... I'm feeling better now."
        
    pet["age_minutes"] += minutes
    pet["last_tick"] = now

    # Age Stage & Evolution Logic
    if pet["age_stage"] == "Child" and pet["age_minutes"] > AGE_TO_TEEN:
        pet["age_stage"] = "Teen"
        pet["level"] += 1; add_xp(pet, 50); pet["happiness"] = clamp(pet["happiness"] + 30)
        notify("🎉 Grown Up!", f"{pet['name']} is now a Teen!")
        grant_achievement(pet, "reached_teen")
        assign_hobby(pet) # v8
        
    elif pet["age_stage"] == "Teen" and pet["age_minutes"] > AGE_TO_ADULT:
        pet["age_stage"] = "Adult"
        pet["level"] += 2; add_xp(pet, 100); pet["happiness"] = clamp(pet["happiness"] + 50)
        
        sk = pet["skills"]
        stats = pet
        mental_score = sk["intelligence"] + sk["charm"]
        physical_score = sk["strength"] + sk["agility"]
        avg_care = (stats["hunger"] + stats["happiness"] + stats["energy"] + stats["cleanliness"]) / 4
        
        evo_type = "Average"
        if avg_care < 40: evo_type = "Slacker"
        elif mental_score > (physical_score * 1.3): evo_type = "Genius"
        elif physical_score > (mental_score * 1.3): evo_type = "Athlete"
            
        pet["evolution_type"] = evo_type
        notify("✨ EVOLVED! ✨", f"{pet['name']} evolved into a {evo_type} Adult!")
        grant_achievement(pet, "evolved")

    elif pet["age_stage"] == "Adult" and pet["age_minutes"] > AGE_TO_ELDER:
        pet["age_stage"] = "Elder"
        pet["level"] += 1; add_xp(pet, 50); pet["dialogue"] = "Back in my day..."
        notify("🕰️ Elder!", f"{pet['name']} is now a wise Elder.")
        grant_achievement(pet, "reached_elder")

# -------------------- LEVEL & XP --------------------
def level_up(pet):
    threshold = MAX_XP_PER_LEVEL * pet["level"]
    if pet["xp"] >= threshold:
        pet["xp"] -= threshold
        pet["level"] += 1
        pet["happiness"] = clamp(pet["happiness"] + 20)
        
        # v8: Skill Point gain logic
        sp_gain = 1
        if random.random() < get_focus_bonus(pet):
            sp_gain += 1
            print("✨ Your 'Focus' grants you an EXTRA Skill Point! ✨")
        
        pet["skill_points"] += sp_gain
        notify("🎉 Level Up!", f"{pet['name']} reached Level {pet['level']}! You got {sp_gain} Skill Point(s)!")
        if pet["level"] >= 10:
            grant_achievement(pet, "level_10")

def add_xp(pet, amount):
    # v8: Apply Legacy Bonus
    legacy_mod = pet.get("legacy_bonus", {}).get("xp_mod", 1.0)
    
    intel_bonus = get_intel_bonus(pet)
    luck_bonus = (get_luck_bonus(pet) - 1.0) * 0.5 + 1.0
    event_mod = 1.0
    if pet["current_event"]["type"] == "Double XP Day": event_mod = 2.0
    if pet["evolution_type"] == "Genius": intel_bonus *= 1.2
    
    final_amount = amount * intel_bonus * luck_bonus * event_mod * legacy_mod
    pet["xp"] += final_amount
    level_up(pet)
    # Return formatted amount for printing
    return f"{final_amount:.1f}"

# -------------------- MOODS & EXPRESSIONS (v7) --------------------
# (This section is identical to v7, contains ASCII art for all stages)
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
    "Egg": {"neutral": " ( ..... ) ", "happy": " ( ..'.. ) ", "sick": " ( ..... ) ", "excited": " ( ..'.. ) ", "hungry": " ( ..... ) ", "sleepy": " ( ..... ) ", "dirty": " ( ..... ) ", "sad": " ( ..... ) "},
    "Child": {"happy": " ( ^‿^ ) ", "excited": " ( ✧∀✧ ) ", "neutral": " ( •‿• ) ", "hungry": " ( ˘﹏˘ ) ", "sleepy": " ( -_- ) zZ", "dirty": " ( •~• ) ", "sad": " ( ;﹏; ) ", "sick": " ( x_x ) "},
    "Teen": {"happy": " ( ^v^ ) ", "excited": " ( 🤩 ) ", "neutral": " ( -v- ) ", "hungry": " ( T_T ) ", "sleepy": " ( u_u ) zZ", "dirty": " ( >.< ) ", "sad": " ( ._.) ", "sick": " ( X_X ) "},
    "Adult_Average": {"happy": "c( ^‿^ )っ", "excited": "c( ✧∀✧ )っ", "neutral": "c( •‿• )っ", "hungry": "c( ˘﹏˘ )っ", "sleepy": "c( -_- )っ zZ", "dirty": "c( •~• )っ", "sad": "c( ;﹏; )っ", "sick": "c( x_x )っ"},
    "Adult_Genius": {"happy": "o( ^‿^ )o", "excited": "o( ✧∀✧ )o", "neutral": "o( •_• )o", "hungry": "o( ˘_˘ )o", "sleepy": "o( -_- )o zZ", "dirty": "o( •~• )o", "sad": "o( ;_; )o", "sick": "o( x_x )o"},
    "Adult_Athlete": {"happy": "V( ^o^ )V", "excited": "V( >O< )V", "neutral": "V( •-• )V", "hungry": "V( >_< )V", "sleepy": "V( -_- )V zZ", "dirty": "V( •~• )V", "sad": "V( ._. )V", "sick": "V( x_x )V"},
    "Adult_Slacker": {"happy": "~( ^o^ )~", "excited": "~( *O* )~", "neutral": "~( ._. )~", "hungry": "~( >o< )~", "sleepy": "~( -_- )~ zZ", "dirty": "~( T_T )~", "sad": "~( ;o; )~", "sick": "~( x_x )~"},
    "Elder": {"happy": "c[ ^‿^ ]ɔ", "excited": "c[ ✧∀✧ ]ɔ", "neutral": "c[ •‿• ]ɔ", "hungry": "c[ ˘﹏˘ ]ɔ", "sleepy": "c[ -_- ]ɔ zZ", "dirty": "c[ •~• ]ɔ", "sad": "c[ ;﹏; ]ɔ", "sick": "c[ x_x ]ɔ"}
}
def ascii_pet(pet):
    m = mood(pet)
    stage = pet["age_stage"]
    evo = pet["evolution_type"]
    art_key = f"Adult_{evo}" if stage == "Adult" else stage
    stage_art = EXPRESSIONS.get(art_key, EXPRESSIONS.get(stage, EXPRESSIONS["Child"]))
    art = stage_art.get(m, stage_art["neutral"])
    return f"  /\\_/\\ \n {art}"
# -------------------- END ASCII --------------------

def status_text(pet):
    if pet["age_stage"] == "Egg":
        return f"Age: {int(pet['age_minutes'])} min (Hatches at {AGE_TO_CHILD} min)"
        
    lvl_prog = int((pet["xp"] / (MAX_XP_PER_LEVEL * pet["level"])) * 20)
    bar = "█" * lvl_prog + "-" * (20 - lvl_prog)
    
    # v8: Home display
    home_str = ", ".join(pet["decor"]) if pet["decor"] else "Bare"

    status = "Healthy"
    if pet["is_sick"]: status = "Sick! 🤒"
    
    evo_str = f" ({pet['evolution_type']})" if pet['age_stage'] in ["Adult", "Elder"] else ""

    return (
        f"Level {pet['level']} ({pet['age_stage']}{evo_str}) | XP: {int(pet['xp'])}/{MAX_XP_PER_LEVEL * pet['level']}\n"
        f"[{bar}]\n"
        f"Health : {int(pet['health'])}/100 | Status: {status}\n"
        f"Hunger : {int(pet['hunger'])}/100 | Happy : {int(pet['happiness'])}/100\n"
        f"Energy : {int(pet['energy'])}/100 | Clean : {int(pet['cleanliness'])}/100\n"
        f"Hobby  : {pet['hobby']} | Coins : {pet['coins']} ¢ | Stardust: {pet['stardust']} ✨\n"
        f"Home   : {home_str}\n"
    )

# v8: New Stats Screen
def show_stats(pet):
    os.system("clear" if os.name != 'nt' else 'cls')
    print(f"--- 📊 Stats for {pet['name']} ---")
    
    # Skills
    skills = pet['skills']
    sk_int = f"Int: {get_skill_level(pet, 'intelligence')} ({skills['intelligence']:.1f})"
    sk_agi = f"Agi: {get_skill_level(pet, 'agility')} ({skills['agility']:.1f})"
    sk_cha = f"Cha: {get_skill_level(pet, 'charm')} ({skills['charm']:.1f})"
    sk_str = f"Str: {get_skill_level(pet, 'strength')} ({skills['strength']:.1f})"
    sk_lck = f"Lck: {get_skill_level(pet, 'luck')} ({skills['luck']:.1f})"
    sk_foc = f"Foc: {get_skill_level(pet, 'focus')} ({skills['focus']:.1f})"
    
    print("\n--- Skills ---")
    print(f"Available SP: {pet['skill_points']}")
    print(f"{sk_int} | {sk_agi} | {sk_cha}")
    print(f"{sk_str} | {sk_lck} | {sk_foc}")
    
    # Inventory
    print("\n--- 🎒 Inventory ---")
    inv_items = [f"{name} x{count}" for name, count in pet["inventory"].items() if count > 0]
    inv_str = ", ".join(inv_items) if inv_items else "Empty"
    print(inv_str)

    # Achievements
    print("\n--- 🏆 Achievements ---")
    achs = [name.replace("_", " ").title() for name, done in pet["achievements"].items() if done]
    print(", ".join(achs) if achs else "None yet!")
    
    # Legacy
    print("\n--- ✨ Legacy Bonuses ---")
    bonus = pet["legacy_bonus"]
    print(f"XP Bonus: +{(bonus['xp_mod'] - 1.0)*100:.0f}% | Coin Bonus: +{(bonus['coin_mod'] - 1.0)*100:.0f}%")
    
    input("\n(Press Enter to return...)")

# -------------------- ACTIONS (v8) --------------------
def feed(pet):
    if pet["age_stage"] == "Egg": print("You can't feed an egg!"); return
    pet["hunger"] = clamp(pet["hunger"] + 25)
    mod = get_mod(pet, "feed_happiness")
    pet["happiness"] = clamp(pet["happiness"] + 3 * mod)
    xp = add_xp(pet, 5)
    print(f"🍎 You fed your pet some basic food. XP +{xp}!")

def play(pet):
    if pet["age_stage"] == "Egg": print("You can't play with an egg!"); return
    if pet["energy"] < 10 or pet["is_sick"]:
        print("Too tired or sick to play."); update_dialogue(pet, "sleepy"); return
    
    hap_mod = get_mod(pet, "play_happiness")
    # v8: Decor bonus
    if "Toy Box" in pet["decor"]: hap_mod *= 1.2
    
    nrg_mod = get_mod(pet, "play_energy") * (1 / get_strength_bonus(pet))
    xp_mod = get_mod(pet, "play_xp")
    
    pet["happiness"] = clamp(pet["happiness"] + 15 * hap_mod)
    pet["energy"] = clamp(pet["energy"] - 10 * nrg_mod)
    pet["cleanliness"] = clamp(pet["cleanliness"] - 5)
    
    xp = add_xp(pet, 10 * xp_mod)
    add_skill(pet, "agility", 0.5 * get_mod(pet, "agi_gain"))
    add_skill(pet, "charm", 0.2 * get_mod(pet, "cha_gain"))
    add_skill(pet, "strength", 0.2 * get_mod(pet, "strength_gain"))
    
    print(f"🎾 You played! XP +{xp}. Agi +0.5, Cha +0.2, Str +0.2")

def sleep(pet):
    if pet["age_stage"] == "Egg": print("The egg is... resting."); return
    print("💤 Sleeping...")
    mod = get_mod(pet, "sleep_energy")
    if pet["current_event"]["type"] == "Heat Wave": mod *= 0.7
    # v8: Decor bonus
    if "Cozy Bed" in pet["decor"]: mod *= 1.2
        
    pet["energy"] = clamp(pet["energy"] + 40 * mod)
    pet["hunger"] = clamp(pet["hunger"] - 10)
    if not pet["is_sick"]:
        pet["health"] = clamp(pet["health"] + 10)
        
    xp = add_xp(pet, 5)
    print(f"😴 Well-rested! Energy +{int(40*mod)}. Health up. XP +{xp}")

def clean(pet):
    if pet["age_stage"] == "Egg": print("You polished the egg."); return
    mod = get_mod(pet, "clean_happiness")
    pet["cleanliness"] = clamp(pet["cleanliness"] + 50)
    pet["happiness"] = clamp(pet["happiness"] + 10 * mod)
    xp = add_xp(pet, 8)
    add_skill(pet, "charm", 0.5 * get_mod(pet, "cha_gain"))
    if pet["is_sick"] and pet["cleanliness"] > 90:
        pet["health"] = clamp(pet["health"] + 5)
        print("Cleanliness helps fight the sickness!")
    print(f"🧼 All clean! XP +{xp}. Cha +0.5")

def read_book(pet):
    if pet["age_stage"] == "Egg": print("The egg can't read."); return
    if pet["inventory"].get("Book", 0) <= 0:
        print("You don't have any 'Book' items. Buy one at the shop!"); return
    if pet["energy"] < 15 or pet["is_sick"]:
        print("Too tired or sick to read a book."); update_dialogue(pet, "sleepy"); return

    pet["inventory"]["Book"] -= 1
    pet["energy"] = clamp(pet["energy"] - 10)
    pet["happiness"] = clamp(pet["happiness"] + 5)
    
    xp_mod = 1.0
    hap_mod = 1.0
    # v8: Hobby bonus
    if pet["hobby"] == "Reading":
        xp_mod = 1.3
        hap_mod = 2.0
        print("📖 This is their favorite hobby!")
    
    pet["happiness"] = clamp(pet["happiness"] + (5 * hap_mod))
    xp = add_xp(pet, 20 * xp_mod)
    add_skill(pet, "intelligence", 2.0 * get_mod(pet, "int_gain"))
    print(f"📚 {pet['name']} read a book! XP +{xp}. Int +2.0")
    update_dialogue(pet, "read")
    
    # Check achievement
    read_count = 5 - pet["inventory"].get("Book", 0) # Just a simple check
    if read_count >= 5:
        grant_achievement(pet, "bookworm_5")

# v8: New Meditate Action
def meditate(pet):
    if pet["age_stage"] == "Egg": print("The egg is already at peace."); return
    if pet["energy"] < 10 or pet["is_sick"]:
        print("Too tired or sick to meditate."); update_dialogue(pet, "sleepy"); return

    print(f"🧘 {pet['name']} is meditating...")
    update_dialogue(pet, "meditate")
    
    pet["energy"] = clamp(pet["energy"] - 5)
    pet["happiness"] = clamp(pet["happiness"] + 5) # Calming
    
    xp = add_xp(pet, 10)
    add_skill(pet, "focus", 1.0 * get_mod(pet, "focus_gain"))
    print(f"Ooommm... XP +{xp}. Foc +1.0. Happiness +5.")
    
    if get_skill_level(pet, "focus") >= 5:
        grant_achievement(pet, "zen_master_5")

def train(pet):
    if pet["age_stage"] not in ["Teen", "Adult", "Elder"]:
        print("Your pet is too young to train!"); return
    if pet["energy"] < 20 or pet["is_sick"]:
        print("Too tired or sick to train."); update_dialogue(pet, "sleepy"); return
    
    print(f"🏋️ {pet['name']} is training hard!")
    update_dialogue(pet, "train")
    
    nrg_mod = (1 / get_strength_bonus(pet))
    pet["energy"] = clamp(pet["energy"] - 20 * nrg_mod)
    pet["hunger"] = clamp(pet["hunger"] - 5)
    pet["cleanliness"] = clamp(pet["cleanliness"] - 10)
    
    xp_mod = 1.0
    # v8: Hobby bonus
    if pet["hobby"] == "Training":
        xp_mod = 1.3
        pet["happiness"] = clamp(pet["happiness"] + 10)
        print("🏋️ This is their favorite hobby!")
    
    xp = add_xp(pet, 15 * xp_mod)
    add_skill(pet, "strength", 1.5 * get_mod(pet, "strength_gain"))
    add_skill(pet, "agility", 1.0 * get_mod(pet, "agi_gain"))
    
    print(f"Phew! Great workout! XP +{xp}. Str +1.5, Agi +1.0")

def work_job(pet):
    if pet["age_stage"] not in ["Adult", "Elder"]:
        print("Only Adults and Elders can work a job."); return
    if pet["energy"] < 30 or pet["is_sick"]:
        print("Too tired or sick to work."); update_dialogue(pet, "sleepy"); return
        
    print("\n--- 🧑‍💼 Available Jobs ---")
    print(f"[1] Library Assistant (Needs: INT Lvl {get_skill_level(pet, 'intelligence')})")
    print(f"[2] Package Mover (Needs: STR Lvl {get_skill_level(pet, 'strength')})")
    print(f"[3] Shop Greeter (Needs: CHA Lvl {get_skill_level(pet, 'charm')})")
    print("(Enter 'exit' to cancel)")
    choice = input("Choose a job: > ").strip()
    
    base_pay, skill_used = 0, "intelligence"
    if choice == "1": skill_used, base_pay = "intelligence", 20; print("Sorting books...")
    elif choice == "2": skill_used, base_pay = "strength", 20; print("Moving packages...")
    elif choice == "3": skill_used, base_pay = "charm", 20; print("Greeting customers...")
    else: print("Cancelled job."); return

    update_dialogue(pet, "job")
    pet["energy"] = clamp(pet["energy"] - 30)
    pet["happiness"] = clamp(pet["happiness"] - 5)
    
    skill_bonus = (get_skill_level(pet, skill_used) - 1) * 10
    luck_bonus = int(random.randint(0, 5) * get_luck_bonus(pet))
    legacy_mod = pet.get("legacy_bonus", {}).get("coin_mod", 1.0) # v8
    
    pay = int((base_pay + skill_bonus + luck_bonus) * legacy_mod)
    
    pet["coins"] += pay
    xp = add_xp(pet, 10)
    
    print(f"Finished work! Earned {pay}¢ (Legacy Mod: {legacy_mod*100:.0f}%).")
    print(f"XP +{xp}. Energy -30, Happy -5.")
    if pet["coins"] >= 1000:
        grant_achievement(pet, "rich_1000")

def spend_sp(pet):
    if pet["skill_points"] <= 0:
        print("You have no Skill Points to spend! Level up to earn them."); return
        
    print("\n--- 🔥 Spend Skill Points ---")
    print(f"You have {pet['skill_points']} SP.")
    print("[1] Intelligence (+5)")
    print("[2] Agility (+5)")
    print("[3] Charm (+5)")
    print("[4] Strength (+5)")
    print("[5] Luck (+5)")
    print("[6] Focus (+5)") # v8
    print("(Enter 'exit' to cancel)")
    
    choice = input("Spend 1 SP on: > ").strip()
    skill_key = None
    
    if choice == "1": skill_key = "intelligence"
    elif choice == "2": skill_key = "agility"
    elif choice == "3": skill_key = "charm"
    elif choice == "4": skill_key = "strength"
    elif choice == "5": skill_key = "luck"
    elif choice == "6": skill_key = "focus" # v8
    else: print("Cancelled."); return
    
    pet["skills"][skill_key] += 5
    pet["skill_points"] -= 1
    print(f"Power up! {skill_key.title()} increased by 5! You have {pet['skill_points']} SP left.")


# -------------------- SHOPS (v8) --------------------
SHOP_ITEMS = {
    "1": {"name": "Special Food", "price": 15},
    "2": {"name": "New Toy", "price": 25},
    "3": {"name": "Medicine", "price": 40},
    "4": {"name": "Book", "price": 50},
    "5": {"name": "Energy Drink", "price": 35},
    "6": {"name": "Rare Snack", "price": 100},
    "7": {"name": "Vitamins", "price": 30},
}
DECOR_ITEMS = { # v8
    "1": {"name": "Cozy Bed", "price": 250, "desc": "Improves sleep energy gain"},
    "2": {"name": "Plush Rug", "price": 150, "desc": "Slows happiness decay"},
    "3": {"name": "Bookshelf", "price": 300, "desc": "Boosts INT XP gain"},
    "4": {"name": "Toy Box", "price": 200, "desc": "Boosts 'Play' happiness"},
    "5": {"name": "Training Mat", "price": 300, "desc": "Boosts STR actions"},
    "6": {"name": "Auto-Cleaner", "price": 500, "desc": "Slows cleanliness decay"},
}
STARDUST_UPGRADES = { # v8
    "1": {"name": "Legacy XP Boost", "cost": 5, "key": "xp_mod", "amount": 0.01},
    "2": {"name": "Legacy Coin Boost", "cost": 5, "key": "coin_mod", "amount": 0.01},
}

def shop_menu(pet):
    print("\n--- 🏪 Welcome to the Shop! ---")
    print("[1] Buy Items (Food, Toys, etc.)")
    print("[2] Buy Decor (Home Upgrades)")
    print("[3] Stardust Upgrades (Permanent)")
    print("(Enter 'exit' to leave)")
    
    choice = input("> ").strip()
    if choice == "1": buy_item(pet)
    elif choice == "2": buy_decor(pet)
    elif choice == "3": buy_stardust_upgrade(pet)
    else: print("Leaving shop.")

def buy_item(pet):
    print("\n--- 🏪 Item Shop ---")
    charm_discount = get_charm_discount(pet)
    event_discount = 0.25 if pet["current_event"]["type"] == "Market Day" else 0.0
    total_discount = charm_discount + event_discount
    if total_discount > 0: print(f"Today's Discount: {total_discount*100:.0f}%!")
    
    for key, item in SHOP_ITEMS.items():
        price = int(item['price'] * (1.0 - total_discount))
        print(f"[{key}] {item['name']} - {price}¢")
    print(f"You have {pet['coins']}¢. (Enter 'exit' to leave)")
    
    choice = input("What to buy? > ").strip().lower()
    if choice in SHOP_ITEMS:
        item = SHOP_ITEMS[choice]
        price = int(item['price'] * (1.0 - total_discount))
        if pet["coins"] >= price:
            pet["coins"] -= price
            item_name = item["name"]
            pet["inventory"][item_name] = pet["inventory"].get(item_name, 0) + 1
            print(f"🛒 You bought 1 {item_name}! You have {pet['inventory'][item_name]}.")
            add_xp(pet, 2)
        else: print("Not enough coins!")
    else: print("Invalid item.")

def buy_decor(pet): # v8
    print("\n--- 🏠 Decor Shop ---")
    print(f"You have {pet['coins']}¢.")
    
    for key, item in DECOR_ITEMS.items():
        owned = " (Owned)" if item["name"] in pet["decor"] else ""
        print(f"[{key}] {item['name']} - {item['price']}¢{owned}\n    ({item['desc']})")
    print("(Enter 'exit' to leave)")
    
    choice = input("What to buy? > ").strip().lower()
    if choice in DECOR_ITEMS:
        item = DECOR_ITEMS[choice]
        item_name = item["name"]
        price = item["price"]
        
        if item_name in pet["decor"]:
            print("You already own that item!"); return
        if pet["coins"] >= price:
            pet["coins"] -= price
            pet["decor"].append(item_name)
            print(f"🛋️ You bought 1 {item_name}! Your home looks nicer.")
            add_xp(pet, 15)
            if len(pet["decor"]) >= 3:
                grant_achievement(pet, "home_decorator_3")
        else: print("Not enough coins!")
    else: print("Invalid item.")

def buy_stardust_upgrade(pet): # v8
    print("\n--- ✨ Stardust Shop (Permanent Upgrades) ---")
    print(f"You have {pet['stardust']} Stardust ✨.")
    
    for key, item in STARDUST_UPGRADES.items():
        current_mod = pet["legacy_bonus"].get(item["key"], 1.0)
        current_bonus_pct = (current_mod - 1.0) * 100
        print(f"[{key}] {item['name']} - Cost: {item['cost']} ✨\n    (Current: +{current_bonus_pct:.0f}%, Buy for: +{item['amount']*100:.0f}%)")
    print("(Enter 'exit' to leave)")

    choice = input("What to buy? > ").strip().lower()
    if choice in STARDUST_UPGRADES:
        item = STARDUST_UPGRADES[choice]
        cost = item["cost"]
        if pet["stardust"] >= cost:
            pet["stardust"] -= cost
            key = item["key"]
            pet["legacy_bonus"][key] = pet["legacy_bonus"].get(key, 1.0) + item["amount"]
            print(f"🌌 Legacy Powered Up! Your {item['name']} is now +{(pet['legacy_bonus'][key] - 1.0)*100:.0f}%.")
        else: print("Not enough Stardust! Retire an Elder to get more.")
    else: print("Invalid item.")

def use_item(pet):
    if pet["age_stage"] == "Egg": print("The egg doesn't need items."); return
    print("\n--- 🎒 Your Inventory ---")
    items = [name for name, count in pet["inventory"].items() if count > 0]
    if not items:
        print("Inventory is empty. Visit the shop to buy items!"); return
    for i, name in enumerate(items, 1): print(f"[{i}] {name} (x{pet['inventory'][name]})")
    print("(Enter 'exit' to cancel)")
    
    try:
        choice = input("Use which item? > ").strip().lower()
        if choice == "exit": return
        item_name = items[int(choice) - 1]
        
        if pet["inventory"][item_name] > 0:
            pet["inventory"][item_name] -= 1
            if item_name == "Special Food":
                pet["hunger"] = clamp(pet["hunger"] + 60); pet["happiness"] = clamp(pet["happiness"] + 20)
                print(f"Wow! Delicious! XP +{add_xp(pet, 15)}")
            elif item_name == "New Toy":
                pet["happiness"] = clamp(pet["happiness"] + 50); pet["energy"] = clamp(pet["energy"] - 15)
                add_skill(pet, "agility", 1.0)
                print(f"So fun! XP +{add_xp(pet, 20)}. Agi +1.0")
            elif item_name == "Medicine":
                if pet["is_sick"] or pet["health"] < 100:
                    pet["is_sick"] = False; pet["health"] = clamp(pet["health"] + 50); pet["happiness"] = clamp(pet["happiness"] + 10)
                    print("Ah, much better! Feeling healthy again!")
                else:
                    pet["happiness"] = clamp(pet["happiness"] - 10); print("You don't need medicine! Yuck.")
                add_xp(pet, 10)
            elif item_name == "Book":
                print("You can't 'use' a book. Try the '[r]ead' action instead."); pet["inventory"]["Book"] += 1
            elif item_name == "Energy Drink":
                pet["energy"] = clamp(pet["energy"] + 60); pet["hunger"] = clamp(pet["hunger"] - 20)
                print(f"BUZZ! Full of energy! XP +{add_xp(pet, 5)}")
            elif item_name == "Rare Snack":
                pet["hunger"] = 100; pet["happiness"] = 100; pet["energy"] = 100
                print(f"Incredible! That was the best snack ever! XP +{add_xp(pet, 30)}")
            elif item_name == "Vitamins":
                pet["health"] = clamp(pet["health"] + 25)
                print(f"Glug glug! Health boosted! XP +{add_xp(pet, 5)}")
        else: print("You don't have that item!")
    except (ValueError, IndexError): print("Invalid choice.")

# -------------------- WALK ACTION (v7) --------------------
def walk(pet):
    if pet["age_stage"] == "Egg": print("The egg... rolls a bit."); return
    if pet["current_event"]["type"] == "Rainy Day": print("It's raining too hard!"); return
    if pet["energy"] < 20 or pet["is_sick"]: print("Too tired or sick for a walk."); return
        
    print("🚶 Going for a walk..."); update_dialogue(pet, "walk")
    pet["energy"] = clamp(pet["energy"] - 15)
    
    xp_mod = get_mod(pet, "walk_xp")
    coin_mod = get_mod(pet, "walk_coins") * pet.get("legacy_bonus", {}).get("coin_mod", 1.0)
    luck_mod = get_luck_bonus(pet)
    
    if pet["current_event"]["type"] == "Sunny Day": coin_mod *= 1.5
    
    event_roll = random.random() * luck_mod
    if event_roll > 1.2:
        coins = int(random.randint(50, 100) * coin_mod)
        pet["coins"] += coins; pet["happiness"] = clamp(pet["happiness"] + 20)
        print(f"🍀 Super lucky! You found a wallet with {coins}¢! XP +{add_xp(pet, 20 * xp_mod)}")
    elif event_roll > 0.7:
        coins = int(random.randint(10, 25) * coin_mod * luck_mod)
        pet["coins"] += coins
        print(f"You found {coins}¢! XP +{add_xp(pet, 5 * xp_mod)}")
    elif event_roll > 0.4:
        pet["happiness"] = clamp(pet["happiness"] + 15)
        print(f"What a lovely walk! XP +{add_xp(pet, 10 * xp_mod)}")
    else:
        pet["cleanliness"] = clamp(pet["cleanliness"] - 30); pet["happiness"] = clamp(pet["happiness"] - 10)
        print(f"Oh no! You fell in a mud puddle! XP +{add_xp(pet, 5 * xp_mod)}"); update_dialogue(pet, "dirty")
    
    add_skill(pet, "agility", 0.3 * get_mod(pet, "agi_gain"))
    add_skill(pet, "luck", 0.1 * get_mod(pet, "luck_gain"))

# -------------------- MINI-GAMES (v8) --------------------
def get_game_mods(pet):
    xp_mod = get_mod(pet, "game_xp")
    hap_mod = get_mod(pet, "game_happiness")
    if pet["current_event"]["type"] == "Festival Day": xp_mod *= 2.0
    if pet["evolution_type"] == "Genius": xp_mod *= 1.3; hap_mod *= 1.2
    
    # v8: Hobby bonus
    if pet["hobby"] == "Gaming":
        xp_mod *= 1.3
        hap_mod *= 2.0
        print("🎮 This is their favorite hobby! Extra XP/Joy!")
        
    return xp_mod, hap_mod

def game_guess_number(pet):
    if pet["age_stage"] == "Egg": print("..."); return
    print("\n🎮 Guess the Number (1-5)!")
    num = random.randint(1, 5)
    xp_mod, hap_mod = get_game_mods(pet)
    try:
        guess = int(input("Your guess: "))
        if guess == num:
            xp = add_xp(pet, 20 * xp_mod)
            print(f"🎉 Correct! XP +{xp}")
            pet["happiness"] = clamp(pet["happiness"] + 15 * hap_mod)
        else:
            xp = add_xp(pet, 5 * xp_mod)
            print(f"❌ Wrong! It was {num}. XP +{xp}")
            pet["happiness"] = clamp(pet["happiness"] - 3)
    except: print("Invalid input!")
    update_dialogue(pet, "game")

def game_rps(pet):
    if pet["age_stage"] == "Egg": print("..."); return
    print("\n✊✋✌️ Rock-Paper-Scissors!")
    moves = ["rock", "paper", "scissors"]
    comp = random.choice(moves)
    xp_mod, hap_mod = get_game_mods(pet)
    try:
        player = input("Choose rock/paper/scissors: ").lower()
        if player not in moves: print("Invalid move!"); return
        print(f"Pet chooses: {comp}")
        if player == comp:
            xp = add_xp(pet, 5 * xp_mod)
            print(f"🤝 Draw! XP +{xp}")
        elif (player == "rock" and comp == "scissors") or \
             (player == "scissors" and comp == "paper") or \
             (player == "paper" and comp == "rock"):
            xp = add_xp(pet, 15 * xp_mod)
            print(f"🎉 You win! XP +{xp}")
            pet["happiness"] = clamp(pet["happiness"] + 10 * hap_mod)
        else:
            xp = add_xp(pet, 5 * xp_mod)
            print(f"😢 You lose! XP +{xp}")
            pet["happiness"] = clamp(pet["happiness"] - 5)
    except: print("Error in game")
    update_dialogue(pet, "game")

def game_study(pet):
    if pet["age_stage"] == "Egg": print("..."); return
    print("\n🧠 Study Time! Answer the question.");
    if pet["energy"] < 10: print("Too tired to study."); return
    xp_mod, hap_mod = get_game_mods(pet)
    pet["energy"] = clamp(pet["energy"] - 5)
    question = random.choice(STUDY_QUESTIONS) # (Using v7's list)
    try:
        answer = input(f"Q: {question['q']} > ").strip().lower()
        if answer == question['a']:
            xp = add_xp(pet, 25 * xp_mod)
            print(f"🎉 Correct! So smart! XP +{xp}")
            pet["happiness"] = clamp(pet["happiness"] + 10 * hap_mod)
            add_skill(pet, "intelligence", 1.0 * get_mod(pet, "int_gain"))
        else:
            xp = add_xp(pet, 5 * xp_mod)
            print(f"❌ Wrong! The answer was '{question['a']}'. XP +{xp}")
            pet["happiness"] = clamp(pet["happiness"] - 3)
            add_skill(pet, "intelligence", 0.1)
    except: print("Error in game")
    update_dialogue(pet, "game")

def game_typing(pet):
    if pet["age_stage"] == "Egg": print("..."); return
    print("\n⌨️ Typing Speed Test! Type the word FAST!")
    if pet["energy"] < 10: print("Too tired to type."); return
    xp_mod, hap_mod = get_game_mods(pet)
    pet["energy"] = clamp(pet["energy"] - 5)
    word = random.choice(TYPING_WORDS) # (Using v7's list)
    try:
        print(f"Type this word: {word}")
        start_time = time.time()
        answer = input("> ").strip().lower()
        end_time = time.time()
        if answer == word:
            time_taken = end_time - start_time
            xp_reward = clamp(20 - (time_taken * 2), 5, 30)
            xp = add_xp(pet, xp_reward * xp_mod)
            print(f"🎉 Perfect! Time: {time_taken:.2f}s. XP +{xp}")
            pet["happiness"] = clamp(pet["happiness"] + 10 * hap_mod)
            add_skill(pet, "agility", 0.5 * get_mod(pet, "agi_gain"))
            add_skill(pet, "intelligence", 0.2 * get_mod(pet, "int_gain"))
        else:
            xp = add_xp(pet, 2 * xp_mod)
            print(f"❌ Wrong! You typed '{answer}'. XP +{xp}")
            pet["happiness"] = clamp(pet["happiness"] - 3)
    except: print("Error in game")
    update_dialogue(pet, "game")

# -------------------- v8: LEGACY / RETIREMENT --------------------
def retire_pet(pet):
    if pet["age_stage"] != "Elder":
        print("Only Elders can retire."); return pet
    if pet["level"] < RETIRE_LEVEL:
        print(f"Your pet must be at least Level {RETIRE_LEVEL} to retire."); return pet

    print(f"\n--- 🌌 Cosmic Retirement ---")
    print(f"{pet['name']} has lived a long, full life (Level {pet['level']}).")
    
    # Calculate Stardust
    stardust_gain = (pet["level"] // 2) + (sum(pet["skills"].values()) // 10)
    stardust_gain = int(stardust_gain)
    
    print(f"Retiring will end this pet's journey and grant you {stardust_gain} Stardust ✨.")
    print("This Stardust can be used to buy permanent upgrades for your *next* pet.")
    
    confirm = input("Are you sure you want to retire? (yes/no) > ").strip().lower()
    
    if confirm == "yes":
        print(f"Goodbye, {pet['name']}! Your legacy will live on...")
        time.sleep(2)
        
        # Create the new pet, but carry over legacy stats
        new_pet = DEFAULT_PET.copy()
        new_pet["stardust"] = pet["stardust"] + stardust_gain
        new_pet["legacy_bonus"] = pet["legacy_bonus"].copy() # Carry over old bonuses
        
        save_pet(new_pet) # Save the new pet
        grant_achievement(new_pet, "cosmic_legacy_1") # Grant on the new pet
        
        print("\n\nA new egg appears, shimmering with cosmic energy...")
        print(f"You have a total of {new_pet['stardust']} Stardust.")
        time.sleep(3)
        return new_pet
    else:
        print("Retirement cancelled."); return pet

# -------------------- AUTO SAVE --------------------
def auto_save_loop(pet, stop_event):
    while not stop_event.is_set():
        time.sleep(AUTOSAVE_INTERVAL)
        if stop_event.is_set(): break
        check_daily_event(pet)
        tick(pet)
        save_pet(pet)

# -------------------- MAIN LOOP --------------------
def main():
    pet = load_pet()
    if pet.get("name", "Tama") == "Tama" and pet["age_minutes"] < 1:
        # --- First Time Setup ---
        name = input(f"Name your new pet (default {pet['name']}): ").strip()
        if name: pet["name"] = name
        
        print("\nChoose a personality:")
        personalities = ["Playful", "Lazy", "Grumpy", "Smart", "Curious"]
        for i, p in enumerate(personalities, 1): print(f"[{i}] {p}")
        try:
            choice = int(input("> ")) - 1
            if 0 <= choice < len(personalities): pet["personality"] = personalities[choice]
        except: pet["personality"] = "Curious"
        
        # v8: Grant starting skill points
        if pet["personality"] == "Smart": add_skill(pet, "intelligence", 3); add_skill(pet, "focus", 3)
        if pet["personality"] == "Playful": add_skill(pet, "charm", 3); add_skill(pet, "strength", 3)
        if pet["personality"] == "Curious": add_skill(pet, "agility", 3); add_skill(pet, "luck", 3)
            
        print(f"Your pet is {pet['personality']}!")
        check_daily_event(pet)
        save_pet(pet)
        print(f"\nYour new pet egg is incubating. It will hatch in {AGE_TO_CHILD} minutes.")
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
                print(f"*** 🔥 You have {pet['skill_points']} Skill Point(s) to spend! Press [k] ***")
            
            event = pet["current_event"]["type"]
            if event != "None": print(f"*** EVENT: {event} ***")
            
            print(f"--- {pet['name']} says ---")
            print(f"> {pet['dialogue']}")
            print(ascii_pet(pet))
            print(status_text(pet))
            print("-" * 20)
            print("Actions: [f]eed [p]lay [s]leep [c]lean [r]ead")
            print("         [w]alk [t]rain [m]editate [j]ob [u]se")
            print("Manage:  [shop] [k]spend_sp [st]ats")
            print("Games:   [1]Guess [2]RPS [3]Study [4]Typing")
            if pet["age_stage"] == "Elder":
                 print(f"Legacy:  [retire] (Lvl {pet['level']}/{RETIRE_LEVEL})")
            print("System:  [z]save [q]quit")
            print("-" * 20)
            
            if pet["age_stage"] == "Egg":
                cmd = input("> ").strip().lower()
            elif pet["is_sick"] and pet["health"] < 10:
                print(f"{pet['name']} is too sick to do anything! Use Medicine!")
                cmd = input("> ").strip().lower()
                if cmd not in ['u', 'q', 'z', 'st']: cmd = 'blocked'
            else:
                cmd = input("> ").strip().lower()
            
            # --- Standard Actions ---
            if cmd == "f": feed(pet)
            elif cmd == "p": play(pet)
            elif cmd == "s": sleep(pet)
            elif cmd == "c": clean(pet)
            elif cmd == "r": read_book(pet)
            elif cmd == "w": walk(pet)
            elif cmd == "t": train(pet)
            elif cmd == "j": work_job(pet)
            elif cmd == "u": use_item(pet)
            
            # --- v8 Actions ---
            elif cmd == "m": meditate(pet)
            elif cmd == "shop": shop_menu(pet) # v8
            elif cmd == "k": spend_sp(pet)
            elif cmd == "st": show_stats(pet) # v8
            elif cmd == "retire" and pet["age_stage"] == "Elder":
                new_pet = retire_pet(pet) # v8
                if new_pet["name"] != pet["name"]: # Check if retirement happened
                    pet = new_pet # Start the new pet's life
                    continue # Restart loop immediately

            # --- Games ---
            elif cmd == "1": game_guess_number(pet)
            elif cmd == "2": game_rps(pet)
            elif cmd == "3": game_study(pet)
            elif cmd == "4" : game_typing(pet)
            
            # --- System ---
            elif cmd in ("z", "save"): save_pet(pet); print("💾 Saved!")
            elif cmd in ("q", "quit", "exit"): print("Saving and exiting..."); save_pet(pet); break
            elif cmd == "blocked": pass
            elif pet["age_stage"] == "Egg": print("The egg just sits there...")
            else: print("❓ Unknown command.")
                
            time.sleep(0.7)
            save_pet(pet)
            
    except KeyboardInterrupt:
        print("\nCaught interrupt. Saving and exiting...")
        save_pet(pet)
    finally:
        stop_event.set()
        saver.join(timeout=1)
        print(f"Goodbye! Come back and visit {pet['name']} soon!")
        sys.exit(0)

if __name__ == "__main__":
    main()