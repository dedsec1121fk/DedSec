#!/usr/bin/env python3
import os, sys, json, time, base64, hashlib, random, textwrap, zlib, re, datetime
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Tuple

APP_NAME = "CTF God"
STATE_VERSION = 9

# Scoring
SPEED_BONUS_RATIO = 0.30
HINT_PENALTY = 10
MIN_POINTS = 5

# Hint shop economy
COINS_PER_SOLVE_BASE = 15
COINS_PER_BOSS = 50
HINT_COST = 25
REVEAL_COST = 60   # small reveal (e.g., first 5 chars of flag)
RESET_COOLDOWN_COST = 40

# Anti-cheat thresholds
MAX_WRONG_PER_60S = 6
MAX_WRONG_PER_10M = 18
COOLDOWN_SECONDS = 180   # 3 minutes on trigger
SUSPICION_SCORE_TRIGGER = 8  # triggers cooldown
SUSPICION_DECAY_PER_MIN = 1

ANDROID_ROOT = Path("/storage/emulated/0/Download/CTF God")

# ---------- Utils ----------

def clear():
    os.system("clear" if os.name != "nt" else "cls")

def hr():
    print("-" * 72)

def wrap(txt: str, width: int = 72) -> str:
    return "\n".join(textwrap.fill(l, width) for l in txt.splitlines())

def ensure(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def flag(seed: str, cid: str) -> str:
    return f"FLAG{{{sha256_str(seed + '::' + cid)[:10]}}}"

def press(msg: str = "\nΠάτησε Enter..."):
    input(msg)

def normalize_username(name: str) -> str:
    name = name.strip()
    name = re.sub(r"\s+", "_", name)
    name = "".join(c for c in name if (c.isalnum() or c in "_-."))
    return (name[:24] or "Agent")

def rot13(s: str) -> str:
    return s.translate(str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm"
    ))

def caesar(s: str, shift: int) -> str:
    out = []
    for ch in s:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + shift) % 26 + 97))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + shift) % 26 + 65))
        else:
            out.append(ch)
    return "".join(out)

def now() -> int:
    return int(time.time())

def today_key() -> str:
    # local date in ISO-like compact form; Termux uses device time
    d = datetime.date.today()
    return f"{d.year:04}{d.month:02}{d.day:02}"

# ---------- Data models ----------

@dataclass
class Challenge:
    cid: str
    title: str
    category: str
    diff: str
    intro: str
    files: List[str]
    points: int
    hint_texts: List[str]
    flag_value: str
    hints_used: int = 0

@dataclass
class Boss:
    bid: str
    title: str
    points: int
    description: str
    folder: str
    stages: List[str]

@dataclass
class Mission:
    mid: str
    title: str
    objective: str
    unlock_after: Optional[str]  # previous mission id or None
    requires_solves: List[str]   # challenge/boss ids that must be solved
    reward_coins: int
    reward_points: int

# ---------- Main Game ----------

class CTFGod:
    def __init__(self):
        self.home = Path.home()
        self.base = self.home / ".ctf_god"
        ensure(self.base)

        self.state_file = self.base / "state.json"
        self.custom_file = self.base / "custom.json"
        self.packs_dir = self.base / "packs"
        ensure(self.packs_dir)

        self.state = self._load_state()
        self.custom = self._load_custom()

        self.root = self._resolve_android_root()
        ensure(self.root)

        self.user: str = ""
        self.profile: Dict = {}
        self.ws: Path = self.root

        self.challenges: List[Challenge] = []
        self.bosses: List[Boss] = []
        self.missions: List[Mission] = []

        self.integrity: Dict[str, str] = {}
        self.prefer_curses = bool(self.state.get("prefer_curses", False))

    # ---------- Storage resolution ----------

    def _resolve_android_root(self) -> Path:
        if ANDROID_ROOT.parent.parent.parent.exists():
            return ANDROID_ROOT
        termux_download = self.home / "storage" / "downloads" / "CTF God"
        if termux_download.parent.exists():
            return termux_download
        return self.home / "CTF God"

    # ---------- Persistence ----------

    def _load_state(self) -> Dict:
        if self.state_file.exists():
            try:
                s = json.loads(self.state_file.read_text(encoding="utf-8"))
                s.setdefault("version", STATE_VERSION)
                s.setdefault("profiles", {})
                s.setdefault("tournaments", {})
                s.setdefault("prefer_curses", False)
                return s
            except Exception:
                bak = self.base / f"state_corrupt_{now()}.json"
                try: self.state_file.replace(bak)
                except Exception: pass
        s = {"version": STATE_VERSION, "profiles": {}, "tournaments": {}, "prefer_curses": False}
        self.state_file.write_text(json.dumps(s, indent=2), encoding="utf-8")
        return s

    def _save_state(self):
        self.state["version"] = STATE_VERSION
        self.state["prefer_curses"] = self.prefer_curses
        self.state_file.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def _load_custom(self) -> Dict:
        if self.custom_file.exists():
            try:
                d = json.loads(self.custom_file.read_text(encoding="utf-8"))
                d.setdefault("levels", [])
                return d
            except Exception:
                bak = self.base / f"custom_corrupt_{now()}.json"
                try: self.custom_file.replace(bak)
                except Exception: pass
        d = {"levels": []}
        self.custom_file.write_text(json.dumps(d, indent=2), encoding="utf-8")
        return d

    def _save_custom(self):
        self.custom_file.write_text(json.dumps(self.custom, indent=2), encoding="utf-8")

    # ---------- Profiles ----------

    def login(self):
        while True:
            clear()
            print("=== CTF GOD ===")
            hr()
            users = sorted(self.state["profiles"].keys())
            if users:
                for i, u in enumerate(users, 1):
                    p = self.state["profiles"][u]
                    print(f"{i}) {u:24} | σκορ {p.get('score',0):6} | νομίσματα {p.get('coins',0):5} | βαθμίδα {p.get('rank','Rookie')}")
                hr()
            cmd = input("Όνομα χρήστη / αριθμός / new / ui / q: ").strip().lower()

            if cmd == "q":
                sys.exit(0)

            if cmd == "ui":
                self.prefer_curses = not self.prefer_curses
                self._save_state()
                print("Η προτίμηση UI ορίστηκε σε:", "CURSES" if self.prefer_curses else "CLI")
                press()
                continue

            if cmd == "new":
                name = normalize_username(input("Νέο όνομα χρήστη: "))
                self._create_profile(name)
                self._select_profile(name)
                return

            if cmd.isdigit() and users:
                idx = int(cmd)
                if 1 <= idx <= len(users):
                    self._select_profile(users[idx - 1])
                    return

            name = normalize_username(cmd)
            self._create_profile(name)
            self._select_profile(name)
            return

    def _create_profile(self, name: str):
        if name in self.state["profiles"]:
            return
        self.state["profiles"][name] = {
            "seed": sha256_str(os.urandom(12).hex())[:20],
            "score": 0,
            "coins": 0,
            "solved": {},        # cid -> {"time": elapsed, "points": gained, "ts": epoch}
            "attempts": {},      # cid -> count
            "rank": "Rookie",
            "achievements": {},  # name -> True
            "stats": {
                "total_solves": 0,
                "boss_kills": 0,
                "no_hint_solves": 0,
                "fast_solves": 0,
                "packs_exported": 0,
                "tournament_submits": 0,
                "daily_solves": 0,
                "missions_done": 0,
                "shop_purchases": 0,
            },
            "missions": {"done": {}, "active": "M1"},
            "daily": {"last_key": "", "solved": {}},  # date_key -> True
            "anti": {
                "wrong_log": [],          # list of epoch seconds for wrong submits (recent)
                "suspicion": 0,           # suspicion score
                "cooldown_until": 0,      # epoch sec
                "last_decay": now(),
            }
        }
        self._save_state()

    def _select_profile(self, name: str):
        self.user = name
        self.profile = self.state["profiles"][name]
        self.ws = self.root / name
        ensure(self.ws)
        self._build_all()
        self._generate_all_if_needed()

    # ---------- Anti-cheat / brute-force detection ----------

    def _anti(self) -> Dict:
        return self.profile.setdefault("anti", {"wrong_log": [], "suspicion": 0, "cooldown_until": 0, "last_decay": now()})

    def _anti_decay(self):
        anti = self._anti()
        t = now()
        last = int(anti.get("last_decay", t))
        if t <= last:
            return
        minutes = (t - last) // 60
        if minutes > 0:
            anti["suspicion"] = max(0, int(anti.get("suspicion", 0)) - minutes * SUSPICION_DECAY_PER_MIN)
            anti["last_decay"] = t

        # drop old wrong logs > 10 minutes
        wl = anti.get("wrong_log", [])
        anti["wrong_log"] = [x for x in wl if (t - x) <= 600]

    def _anti_in_cooldown(self) -> Tuple[bool, int]:
        anti = self._anti()
        t = now()
        until = int(anti.get("cooldown_until", 0))
        if t < until:
            return True, (until - t)
        return False, 0

    def _anti_record_wrong(self, attempted_flag: str):
        anti = self._anti()
        self._anti_decay()
        t = now()
        anti.setdefault("wrong_log", []).append(t)

        # brute-force suspicion patterns
        # - too many wrong attempts quickly
        last_60 = [x for x in anti["wrong_log"] if (t - x) <= 60]
        last_600 = anti["wrong_log"]

        suspicion = int(anti.get("suspicion", 0))

        if len(last_60) >= MAX_WRONG_PER_60S:
            suspicion += 4
        if len(last_600) >= MAX_WRONG_PER_10M:
            suspicion += 5

        # pattern: many different "FLAG{...}" shapes suggests guessing
        if attempted_flag.startswith("FLAG{") and attempted_flag.endswith("}") and len(attempted_flag) < 40:
            suspicion += 1

        anti["suspicion"] = suspicion

        if suspicion >= SUSPICION_SCORE_TRIGGER:
            anti["cooldown_until"] = t + COOLDOWN_SECONDS

    def _anti_on_correct(self):
        # reward correct behavior: drop suspicion faster
        anti = self._anti()
        self._anti_decay()
        anti["suspicion"] = max(0, int(anti.get("suspicion", 0)) - 2)

    # ---------- Achievements & ranks ----------

    def _update_rank_and_achievements(self):
        solved_count = len(self.profile.get("solved", {}))
        boss_kills = self.profile.get("stats", {}).get("boss_kills", 0)
        score = int(self.profile.get("score", 0))

        if solved_count < 3:
            rank = "Rookie"
        elif solved_count < 8:
            rank = "Operator"
        elif solved_count < 15:
            rank = "Elite"
        else:
            rank = "CTF God"

        ach = self.profile.setdefault("achievements", {})
        stats = self.profile.setdefault("stats", {})

        if solved_count >= 1: ach["First Blood"] = True
        if solved_count >= 5: ach["Hacker"] = True
        if solved_count >= 10: ach["Elite Mind"] = True
        if solved_count >= 20: ach["Legend"] = True

        if boss_kills >= 1: ach["Boss Slayer"] = True
        if boss_kills >= 3: ach["Boss Hunter"] = True

        if stats.get("no_hint_solves", 0) >= 5: ach["No-Hint Streak"] = True
        if stats.get("fast_solves", 0) >= 5: ach["Speedrunner"] = True

        if stats.get("packs_exported", 0) >= 1: ach["Pack Creator"] = True
        if stats.get("tournament_submits", 0) >= 1: ach["Competitor"] = True
        if stats.get("daily_solves", 0) >= 3: ach["Daily Grinder"] = True
        if stats.get("missions_done", 0) >= 3: ach["Story Runner"] = True
        if stats.get("shop_purchases", 0) >= 3: ach["Black Market"] = True

        if score >= 1000: ach["Four Digits"] = True
        if score >= 5000: ach["High Roller"] = True

        self.profile["rank"] = rank

    # ---------- Challenge & Boss library ----------

    def _reg(self, cid: str, title: str, category: str, diff: str,
             intro: str, files: List[str], points: int, hints: List[str]):
        self.challenges.append(Challenge(
            cid=cid, title=title, category=category, diff=diff,
            intro=intro, files=files, points=points, hint_texts=hints,
            flag_value=flag(self.profile["seed"], cid)
        ))

    def _build_missions(self):
        # Story missions: unlock chain with requirements.
        self.missions = [
            Mission("M1", "Boot Sequence", "Solve any EASY crypto challenge (C1-C5).", None, ["C1"], 40, 40),
            Mission("M2", "Signal Trace", "Solve 2 challenges total.", "M1", ["C1","C2"], 60, 60),
            Mission("M3", "Log Breach", "Solve a forensics challenge (C7/C8/C9).", "M2", ["C9"], 80, 80),
            Mission("M4", "First Boss Contact", "Defeat BOSS1.", "M3", ["BOSS1"], 120, 120),
            Mission("M5", "Ghost Packet", "Defeat BOSS2.", "M4", ["BOSS2"], 160, 160),
            Mission("M6", "Kernel of Truth", "Defeat BOSS3.", "M5", ["BOSS3"], 220, 220),
        ]

    def _build_all(self):
        self.challenges = []
        self.bosses = []
        self._build_missions()

        # Built-ins (same “big library” core, trimmed slightly to keep size manageable but still huge)
        self._reg("C1","Base64 Warmup","Crypto","Easy",
                  "Κάνε decode το base64 string στο αρχείο για να βρεις το flag.",
                  ["easy/b64.txt"], 50,
                  ["Try: base64 -d file", "In Python: base64.b64decode(...)"])

        self._reg("C2","ROT13 Hotline","Crypto","Easy",
                  "Εφάρμοσε ROT13 για να αποκαλυφθεί το flag.",
                  ["easy/rot13.txt"], 60,
                  ["Try: tr 'A-Za-z' 'N-ZA-Mn-za-m'", "In Python: codecs.decode(s,'rot_13')"])

        self._reg("C3","Hex Whisper","Crypto","Easy",
                  "Κάνε hex-decode το περιεχόμενο για να αποκαλυφθεί το flag.",
                  ["easy/hex.txt"], 70,
                  ["Try: xxd -r -p file", "In Python: bytes.fromhex(...)"])

        self._reg("C4","Caesar Street","Crypto","Easy",
                  "Ένα Caesar cipher κρύβει το flag. Βρες το shift.",
                  ["easy/caesar.txt"], 80,
                  ["Brute shifts 1..25", "Search for 'FLAG{' pattern"])

        self._reg("C5","Decode URL","Web","Easy",
                  "Το URL percent-encoding κρύβει το flag.",
                  ["easy/url.txt"], 70,
                  ["In python: urllib.parse.unquote(...)", "Look for %7B and %7D"])

        self._reg("C6","XOR Solo Byte","Crypto","Medium",
                  "A single-byte XOR was used and then hex-encoded. Recover the flag.",
                  ["medium/xor_hex.txt"], 130,
                  ["Try brute force key 0..255", "Search for 'FLAG{' in output"])

        self._reg("C7","Zlib Capsule","Forensics","Medium",
                  "The file contains a zlib-compressed blob. Extract and decompress it.",
                  ["medium/capsule.bin"], 120,
                  ["Look for zlib header 78 9C", "Use python zlib.decompress(...)"])

        self._reg("C8","Strings Hunter","Forensics","Medium",
                  "A binary has the flag embedded. Find it.",
                  ["medium/blob.bin"], 110,
                  ["strings file | grep FLAG", "Or scan ASCII ranges"])

        self._reg("C9","Log Grep 101","Forensics","Medium",
                  "Somewhere in the logs there's a suspicious line containing the flag.",
                  ["medium/system.log"], 125,
                  ["grep FLAG -n file", "grep -i alert file"])

        self._reg("C10","Hash Match","Crypto","Medium",
                  "You are given a hash and a small wordlist. Find the matching word, then follow the rule.",
                  ["medium/hash.txt","medium/words.txt"], 140,
                  ["Compute sha256(word) for each word", "Compare to hash in hash.txt"])

        self._reg("C11","Layer Cake","Crypto","Hard",
                  "Multiple layers: reverse -> base64 -> zlib. Reveal the flag.",
                  ["hard/layers.txt"], 200,
                  ["Reverse first", "Then base64 decode, then zlib decompress"])

        self._reg("C12","Two-Step XOR","Crypto","Hard",
                  "Double-XOR with two bytes alternating (k1,k2). Recover the flag.",
                  ["hard/xor2.txt"], 220,
                  ["Use known plaintext 'FLAG{'", "Try deriving k1/k2 from prefix"])

        self._reg("C13","Fake PNG","Forensics","Hard",
                  "A file claims to be PNG, but the real payload is appended. Extract the tail.",
                  ["hard/fake.png"], 210,
                  ["PNG ends with IEND", "Anything after may be payload"])

        self._reg("C14","Config Leak","Misc","Hard",
                  "A config file includes the flag, obfuscated with base64 and junk.",
                  ["hard/app.conf"], 190,
                  ["Find base64-like segment", "Strip junk then decode"])

        self._reg("C15","Mini VM","Reverse","Hard",
                  "A tiny bytecode executes operations. Simulate it to recover the flag.",
                  ["hard/bytecode.txt"], 240,
                  ["Write a mini interpreter", "Steps are simple"])

        self._reg("C16","DedSec Morse","Crypto","Medium",
                  "Morse-like dots/dashes map to binary. Decode to recover the flag.",
                  ["medium/morseish.txt"], 145,
                  ["Map '.'->0 and '-'->1 (or vice versa)", "Group into bytes"])

        self._reg("C17","Base32 Beacon","Crypto","Easy",
                  "Base32 encoding. Decode to reveal the flag.",
                  ["easy/b32.txt"], 75,
                  ["python base64.b32decode", "Padding matters"])

        self._reg("C18","Gzip Note","Forensics","Medium",
                  "A gzip file hides the flag in plain text. Extract it.",
                  ["medium/note.gz"], 130,
                  ["gzip -dc file", "Or python gzip module"])

        self._reg("C19","JSON Treasure","Misc","Easy",
                  "A JSON file contains the flag among many keys.",
                  ["easy/treasure.json"], 65,
                  ["grep FLAG file", "Pretty print and search"])

        self._reg("C20","Time Lock","Crypto","Hard",
                  "A timestamp and rule produce the expected flag. Recreate the derivation locally.",
                  ["hard/timelock.txt"], 230,
                  ["Use sha256 on (timestamp + seed)", "Follow the rule exactly"])

        self._reg("C21","Chunks","Crypto","Medium",
                  "The flag was split into chunks and shuffled. Reassemble by index.",
                  ["medium/chunks.txt"], 160,
                  ["Sort by idx", "Join chunks"])

        self._reg("C22","ROT47 Tunnel","Crypto","Medium",
                  "ROT47 was applied. Decode the text.",
                  ["medium/rot47.txt"], 160,
                  ["ROT47 ASCII 33..126", "Write a tiny decoder"])

        self._reg("C23","Manifest Rebuild","Forensics","Hard",
                  "A manifest hides a base64 payload across lines. Rebuild and decode it.",
                  ["hard/manifest.txt"], 220,
                  ["Concatenate payload lines", "Base64 decode"])

        self._reg("C24","Regex Minefield","Misc","Medium",
                  "A messy text contains many fake flags. Find the real one by rule at top.",
                  ["medium/regex.txt"], 155,
                  ["Use regex", "Follow the rule shown"])

        self._reg("C25","Packet Shuffle","Forensics","Hard",
                  "A payload is split into numbered fragments. Reassemble and decode it.",
                  ["hard/packet.txt"], 215,
                  ["Sort by number", "Decode layers"])

        # Custom levels
        for lvl in self.custom.get("levels", []):
            cid = f"U_{lvl['id']}"
            title = lvl.get("title", f"Custom {lvl['id']}")
            intro = lvl.get("intro", "Solve the custom challenge.")
            points = int(lvl.get("points", 120))
            ext = lvl.get("ext", "txt")
            files = [f"custom/{lvl['id']}.{ext}"]
            hints = lvl.get("hints", ["Try reading the file carefully."])
            self._reg(cid, title, "Custom", "Custom", intro, files, points, hints)

        # Bosses
        self.bosses.append(Boss(
            bid="BOSS1", title="Operation Black Signal", points=350,
            description="Decode → Decompress → Hunt logs → Final Flag",
            folder="boss/BOSS1",
            stages=[
                "Decode stage1.txt (base64) → keyword",
                "Decompress stage2.bin (zlib) → verify",
                "Search stage3.log → FINAL_FLAG"
            ]
        ))
        self.bosses.append(Boss(
            bid="BOSS2", title="Ghost Packet", points=450,
            description="Reassemble packet → Extract payload → Decompress → Final Flag",
            folder="boss/BOSS2",
            stages=[
                "Reassemble packet parts in order",
                "base64 decode + zlib decompress",
                "Output is FINAL_FLAG"
            ]
        ))
        self.bosses.append(Boss(
            bid="BOSS3", title="Kernel of Truth", points=600,
            description="Compute key → XOR decrypt vault → Final Flag",
            folder="boss/BOSS3",
            stages=[
                "Compute key from program numbers",
                "XOR-decrypt vault hex with key",
                "Output is FINAL_FLAG"
            ]
        ))

    # ---------- Integrity ----------

    def _hash(self, p: Path) -> str:
        return sha256_bytes(p.read_bytes())

    def _integrity_path(self) -> Path:
        return self.ws / ".integrity.json"

    def _write_integrity(self):
        self._integrity_path().write_text(json.dumps(self.integrity, indent=2), encoding="utf-8")

    def integrity_ok(self) -> bool:
        ip = self._integrity_path()
        if not ip.exists():
            return True
        try:
            ref = json.loads(ip.read_text(encoding="utf-8"))
        except Exception:
            return False
        for path_s, h in ref.items():
            p = Path(path_s)
            if not p.exists():
                return False
            try:
                if self._hash(p) != h:
                    return False
            except Exception:
                return False
        return True

    def repair_workspace(self):
        try: (self.ws / ".generated").unlink()
        except Exception: pass
        self._generate_all_if_needed(force=True)

    # ---------- Generation ----------

    def _generate_all_if_needed(self, force: bool = False):
        marker = self.ws / ".generated"
        if marker.exists() and not force:
            return

        self.integrity = {}

        # Ensure dirs
        for d in ["easy","medium","hard","boss","custom","random","daily","story"]:
            ensure(self.ws / d)

        seed = self.profile["seed"]

        # challenges
        for c in self.challenges:
            for rel in c.files:
                ensure((self.ws / rel).parent)

            if c.cid == "C1":
                (self.ws / c.files[0]).write_text(base64.b64encode(c.flag_value.encode()).decode(), encoding="utf-8")
            elif c.cid == "C2":
                (self.ws / c.files[0]).write_text(rot13(c.flag_value), encoding="utf-8")
            elif c.cid == "C3":
                (self.ws / c.files[0]).write_text(c.flag_value.encode().hex(), encoding="utf-8")
            elif c.cid == "C4":
                (self.ws / c.files[0]).write_text(caesar(c.flag_value, 7), encoding="utf-8")
            elif c.cid == "C5":
                s = c.flag_value.replace("{","%7B").replace("}","%7D").replace("_","%5F")
                (self.ws / c.files[0]).write_text(s, encoding="utf-8")
            elif c.cid == "C6":
                key = 42
                enc = bytes([b ^ key for b in c.flag_value.encode()]).hex()
                (self.ws / c.files[0]).write_text(enc, encoding="utf-8")
            elif c.cid == "C7":
                payload = zlib.compress((c.flag_value + "::capsule").encode())
                data = os.urandom(48) + payload + os.urandom(48)
                (self.ws / c.files[0]).write_bytes(data)
            elif c.cid == "C8":
                data = os.urandom(300) + b"---" + c.flag_value.encode() + b"---" + os.urandom(300)
                (self.ws / c.files[0]).write_bytes(data)
            elif c.cid == "C9":
                lines = [f"INFO ok {i}" for i in range(250)]
                lines.insert(173, f"ALERT FLAG={c.flag_value}")
                (self.ws / c.files[0]).write_text("\n".join(lines), encoding="utf-8")
            elif c.cid == "C10":
                target_word = "dedsec"
                target_hash = sha256_str(target_word)
                (self.ws / c.files[0]).write_text(f"sha256={target_hash}\nrule=Find matching word then submit the challenge flag.\n", encoding="utf-8")
                words = ["alpha","bravo","charlie","dedsec","omega","system","phantom"]
                random.shuffle(words)
                (self.ws / c.files[1]).write_text("\n".join(words) + "\n", encoding="utf-8")
            elif c.cid == "C11":
                (self.ws / c.files[0]).write_text(base64.b64encode(zlib.compress(c.flag_value.encode())).decode()[::-1], encoding="utf-8")
            elif c.cid == "C12":
                k1, k2 = 13, 37
                raw = c.flag_value.encode()
                enc = bytes([(b ^ (k1 if i % 2 == 0 else k2)) for i, b in enumerate(raw)]).hex()
                (self.ws / c.files[0]).write_text(enc, encoding="utf-8")
            elif c.cid == "C13":
                png_header = b"\x89PNG\r\n\x1a\n" + os.urandom(64)
                payload = b"PAYLOAD:" + base64.b64encode(c.flag_value.encode())
                (self.ws / c.files[0]).write_bytes(png_header + b"IEND" + os.urandom(8) + payload)
            elif c.cid == "C14":
                junk = "###" + base64.b64encode(c.flag_value.encode()).decode() + "%%%"
                (self.ws / c.files[0]).write_text(f"[app]\nname=dedsec\nsecret={junk}\n", encoding="utf-8")
            elif c.cid == "C15":
                bc = ["# Mini VM", "PUSH " + c.flag_value.encode().hex(), "XOR 23", "REV", "OUT"]
                (self.ws / c.files[0]).write_text("\n".join(bc) + "\n", encoding="utf-8")
            elif c.cid == "C16":
                b64 = base64.b64encode(c.flag_value.encode()).decode()
                bits = "".join(f"{ord(ch):08b}" for ch in b64)
                morseish = bits.replace("0",".").replace("1","-")
                (self.ws / c.files[0]).write_text(morseish, encoding="utf-8")
            elif c.cid == "C17":
                (self.ws / c.files[0]).write_text(base64.b32encode(c.flag_value.encode()).decode(), encoding="utf-8")
            elif c.cid == "C18":
                import gzip
                data = ("NOTE:\n" + c.flag_value + "\n").encode()
                with gzip.open(self.ws / c.files[0], "wb") as f:
                    f.write(data)
            elif c.cid == "C19":
                obj = {"noise": [random.randint(1, 999) for _ in range(10)], "flag": c.flag_value, "ok": True}
                (self.ws / c.files[0]).write_text(json.dumps(obj, indent=2), encoding="utf-8")
            elif c.cid == "C20":
                ts = 1700000000
                (self.ws / c.files[0]).write_text(f"timestamp={ts}\nrule=flag=FLAG{{sha256(str(ts)+seed)[:10]}}\n", encoding="utf-8")
            elif c.cid == "C21":
                parts = [(i, c.flag_value[i:i+3]) for i in range(0, len(c.flag_value), 3)]
                random.shuffle(parts)
                (self.ws / c.files[0]).write_text("\n".join(f"{i}:{chunk}" for i,chunk in parts), encoding="utf-8")
            elif c.cid == "C22":
                def rot47_encode(s: str) -> str:
                    out=[]
                    for ch in s:
                        o=ord(ch)
                        if 33<=o<=126:
                            out.append(chr(33+((o-33+47)%94)))
                        else:
                            out.append(ch)
                    return "".join(out)
                (self.ws / c.files[0]).write_text(rot47_encode(c.flag_value), encoding="utf-8")
            elif c.cid == "C23":
                b = base64.b64encode(c.flag_value.encode()).decode()
                lines = [b[i:i+12] for i in range(0, len(b), 12)]
                manifest = ["<manifest>", "<payload>"] + lines + ["</payload>", "</manifest>"]
                (self.ws / c.files[0]).write_text("\n".join(manifest), encoding="utf-8")
            elif c.cid == "C24":
                real = c.flag_value
                fake = [f"FLAG{{{sha256_str(str(i))[:10]}}}" for i in range(25)]
                random.shuffle(fake)
                top = "RULE: Only one flag appears exactly once. Pick the unique one.\n"
                text = "\n".join(fake[:12] + [real] + fake[12:] + [real])  # duplicate real to make unique logic? No.
                # Make real unique: remove duplicates and add duplicates for others.
                fake2 = fake[:]
                fake2 += random.sample(fake, 5)  # duplicates for fakes
                random.shuffle(fake2)
                lines = fake2[:]
                # ensure real appears exactly once:
                lines.insert(random.randint(3, len(lines)-3), real)
                (self.ws / c.files[0]).write_text(top + "\n".join(lines), encoding="utf-8")
            elif c.cid == "C25":
                payload = base64.b64encode(zlib.compress(c.flag_value.encode())).decode()
                parts = [(i, payload[i:i+10]) for i in range(0, len(payload), 10)]
                random.shuffle(parts)
                (self.ws / c.files[0]).write_text("\n".join(f"{i}:{chunk}" for i,chunk in parts), encoding="utf-8")
            elif c.cid.startswith("U_"):
                custom_id = c.cid[2:]
                lvl = next((x for x in self.custom.get("levels", []) if str(x.get("id")) == custom_id), None)
                ctype = (lvl.get("type","plain") if lvl else "plain")
                rel = c.files[0]
                p = self.ws / rel
                payload = c.flag_value

                if ctype == "plain":
                    p.write_text(payload, encoding="utf-8")
                elif ctype == "base64":
                    p.write_text(base64.b64encode(payload.encode()).decode(), encoding="utf-8")
                elif ctype == "rot13":
                    p.write_text(rot13(payload), encoding="utf-8")
                elif ctype == "xor":
                    key = int(lvl.get("key", 42)) if lvl else 42
                    p.write_text(bytes([b ^ key for b in payload.encode()]).hex(), encoding="utf-8")
                elif ctype == "layered":
                    p.write_text(base64.b64encode(zlib.compress(payload.encode())).decode()[::-1], encoding="utf-8")
                else:
                    p.write_text(payload, encoding="utf-8")

            # hash files
            for rel in c.files:
                p = self.ws / rel
                if p.exists():
                    self.integrity[str(p)] = self._hash(p)

        # bosses
        self._generate_bosses(seed)

        # story brief
        story = self.ws / "story" / "README.txt"
        story.write_text(
            "STORY MODE FILES LIVE HERE.\n"
            "You can solve missions from the game menu.\n"
            "Boss folders are inside /boss.\n", encoding="utf-8"
        )
        self.integrity[str(story)] = self._hash(story)

        self._write_integrity()
        marker.write_text("ok", encoding="utf-8")

    def _generate_bosses(self, seed: str):
        # BOSS1
        b1 = self.ws / "boss" / "BOSS1"
        ensure(b1)
        keyword = "PHANTOM"
        (b1 / "stage1.txt").write_text(base64.b64encode(keyword.encode()).decode(), encoding="utf-8")
        (b1 / "stage2.bin").write_bytes(zlib.compress(keyword.encode()))
        lines = [f"INFO line {i}" for i in range(220)]
        lines.insert(133, f"ALERT FINAL_FLAG={flag(seed,'BOSS1')}")
        (b1 / "stage3.log").write_text("\n".join(lines), encoding="utf-8")

        # BOSS2
        b2 = self.ws / "boss" / "BOSS2"
        ensure(b2)
        payload = base64.b64encode(zlib.compress(flag(seed, "BOSS2").encode())).decode()
        parts = [(i, payload[i:i+8]) for i in range(0, len(payload), 8)]
        random.shuffle(parts)
        (b2 / "packet_parts.txt").write_text("\n".join(f"{i}:{chunk}" for i, chunk in parts), encoding="utf-8")
        (b2 / "instructions.txt").write_text(
            "Reassemble payload by sorting idx, join chunks.\n"
            "Then base64-decode and zlib-decompress.\n"
            "Output is FINAL_FLAG.\n", encoding="utf-8"
        )

        # BOSS3
        b3 = self.ws / "boss" / "BOSS3"
        ensure(b3)
        nums = [random.randint(10, 99) for _ in range(30)]
        (b3 / "program.txt").write_text(
            "RULE: key = (sum(NUMS) % 256)\nNUMS:\n" + " ".join(map(str, nums)) + "\n", encoding="utf-8"
        )
        key = sum(nums) % 256
        final_flag = flag(seed, "BOSS3").encode()
        vault = bytes([b ^ key for b in final_flag]).hex()
        (b3 / "vault.txt").write_text(
            "Decrypt: hex bytes XOR key.\nDATA:\n" + vault + "\n", encoding="utf-8"
        )

        for bdir in [b1, b2, b3]:
            for f in bdir.iterdir():
                if f.is_file():
                    self.integrity[str(f)] = self._hash(f)

    # ---------- Daily challenge ----------

    def _daily_id(self) -> str:
        return "D" + today_key()

    def ensure_daily(self) -> Challenge:
        dkey = today_key()
        daily_state = self.profile.setdefault("daily", {"last_key": "", "solved": {}})
        # deterministic daily flag per user+date:
        cid = self._daily_id()
        dflag = flag(self.profile["seed"], cid)

        # create a daily file if missing (or new day)
        rel = f"daily/{cid}.txt"
        p = self.ws / rel
        ensure(p.parent)

        # Use a different template each day (deterministic):
        rnd = random.Random(sha256_str(self.profile["seed"] + dkey))
        template = rnd.choice(["b64","rot13","layered","xor"])
        intro = ""
        if template == "b64":
            p.write_text(base64.b64encode(dflag.encode()).decode(), encoding="utf-8")
            intro = "Daily: κάνε decode το base64 για να βρεις το flag."
        elif template == "rot13":
            p.write_text(rot13(dflag), encoding="utf-8")
            intro = "Daily: εφάρμοσε ROT13 για να βρεις το flag."
        elif template == "layered":
            p.write_text(base64.b64encode(zlib.compress(dflag.encode())).decode()[::-1], encoding="utf-8")
            intro = "Daily: reverse -> base64 -> zlib."
        else:
            key = 42
            p.write_text(bytes([b ^ key for b in dflag.encode()]).hex(), encoding="utf-8")
            intro = "Daily: single-byte XOR σε hex. Δοκίμασε κλειδί (bruteforce)."

        # update integrity map (daily is part of integrity)
        self.integrity[str(p)] = self._hash(p)
        self._write_integrity()

        daily_state["last_key"] = dkey
        return Challenge(
            cid=cid, title="Daily Ops", category="Daily", diff="Daily",
            intro=intro, files=[rel], points=180,
            hint_texts=["Do it step-by-step. Use base64/zlib/rot13 tools."],
            flag_value=dflag
        )

    # ---------- Hint shop ----------

    def _coins(self) -> int:
        return int(self.profile.get("coins", 0))

    def _add_coins(self, amt: int):
        self.profile["coins"] = int(self.profile.get("coins", 0)) + int(amt)

    def _spend_coins(self, amt: int) -> bool:
        c = self._coins()
        if c < amt:
            return False
        self.profile["coins"] = c - amt
        self.profile.setdefault("stats", {}).setdefault("shop_purchases", 0)
        self.profile["stats"]["shop_purchases"] += 1
        return True

    def shop_menu(self):
        while True:
            clear()
            self._update_rank_and_achievements()
            self._save_state()
            print("Κατάστημα Υποδείξεων — Black Market")
            hr()
            print("Νομίσματα:", self._coins())
            hr()
            print(f"1) Buy 1 hint for current challenge (-{HINT_COST} coins)")
            print(f"2) Buy tiny reveal (first 5 chars of flag) (-{REVEAL_COST} coins)")
            print(f"3) Buy cooldown reset (-{RESET_COOLDOWN_COST} coins)")
            print("0) Πίσω")
            hr()
            c = input("> ").strip()
            if c == "0":
                return c
            if c in ("1","2","3"):
                return c

    # ---------- Packs (Import/Export) ----------

    def export_pack(self, name: str) -> Path:
        name = normalize_username(name)
        pack = {"pack_version": 3, "created": now(), "levels": self.custom.get("levels", [])}
        p = self.packs_dir / f"{name}.json"
        p.write_text(json.dumps(pack, indent=2), encoding="utf-8")
        self.profile.setdefault("stats", {}).setdefault("packs_exported", 0)
        self.profile["stats"]["packs_exported"] += 1
        self._update_rank_and_achievements()
        self._save_state()
        return p

    def import_pack(self, name: str) -> Tuple[bool, str]:
        name = normalize_username(name)
        p = self.packs_dir / f"{name}.json"
        if not p.exists():
            return False, "Pack not found."
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return False, "Pack is invalid JSON."
        levels = data.get("levels", [])
        if not isinstance(levels, list):
            return False, "Pack format invalid."

        existing = self.custom.get("levels", [])
        added = 0
        for lvl in levels:
            if lvl not in existing:
                existing.append(lvl)
                added += 1

        self.custom["levels"] = existing
        self._save_custom()
        self._build_all()
        self.repair_workspace()
        return True, f"Imported {added} levels."

    def list_packs(self) -> List[str]:
        return [p.stem for p in sorted(self.packs_dir.glob("*.json"))]

    # ---------- Τουρνουά mode ----------

    def tournament_create(self, name: str):
        name = normalize_username(name)
        self.state.setdefault("tournaments", {})
        self.state["tournaments"][name] = {"created": now(), "locked": False, "scores": {}}
        self._save_state()

    def tournament_lock(self, name: str) -> Tuple[bool, str]:
        name = normalize_username(name)
        t = self.state.get("tournaments", {}).get(name)
        if not t:
            return False, "Τουρνουά not found."
        t["locked"] = True
        self._save_state()
        return True, "Τουρνουά locked."

    def tournament_submit(self, name: str) -> Tuple[bool, str]:
        name = normalize_username(name)
        t = self.state.get("tournaments", {}).get(name)
        if not t:
            return False, "Τουρνουά not found."
        if t.get("locked"):
            return False, "Τουρνουά locked."
        t.setdefault("scores", {})[self.user] = int(self.profile.get("score", 0))
        self.profile.setdefault("stats", {}).setdefault("tournament_submits", 0)
        self.profile["stats"]["tournament_submits"] += 1
        self._update_rank_and_achievements()
        self._save_state()
        return True, "Score submitted."

    def tournament_leaderboard(self, name: str) -> Tuple[bool, str, List[Tuple[str,int]]]:
        name = normalize_username(name)
        t = self.state.get("tournaments", {}).get(name)
        if not t:
            return False, "Τουρνουά not found.", []
        status = "LOCKED" if t.get("locked") else "OPEN"
        scores = [(u, int(s)) for u, s in t.get("scores", {}).items()]
        scores.sort(key=lambda x: -x[1])
        return True, status, scores

    # ---------- Scoring ----------

    def _compute_points(self, base_points: int, elapsed_sec: int, hints_used: int) -> int:
        bonus_budget = int(base_points * SPEED_BONUS_RATIO)
        bonus = max(0, bonus_budget - elapsed_sec)
        gained = base_points + bonus - (hints_used * HINT_PENALTY)
        return max(MIN_POINTS, gained)

    def _award_solve_coins(self, base_points: int, is_daily: bool = False):
        # coin reward tied to difficulty. Daily gives a bit more.
        bonus = 10 if is_daily else 0
        self._add_coins(COINS_PER_SOLVE_BASE + int(base_points / 20) + bonus)

    # ---------- Story mode ----------

    def story_status(self) -> Tuple[Mission, bool]:
        mstate = self.profile.setdefault("missions", {"done": {}, "active": "M1"})
        active_id = mstate.get("active", "M1")
        m = next((x for x in self.missions if x.mid == active_id), self.missions[0])
        done = bool(mstate.get("done", {}).get(m.mid))
        return m, done

    def _mission_is_unlocked(self, m: Mission) -> bool:
        if m.unlock_after is None:
            return True
        done = self.profile.setdefault("missions", {"done": {}}).get("done", {})
        return bool(done.get(m.unlock_after))

    def _mission_is_completed(self, m: Mission) -> bool:
        solved = self.profile.get("solved", {})
        return all(req in solved for req in m.requires_solves)

    def _mission_complete_and_advance(self, m: Mission):
        mstate = self.profile.setdefault("missions", {"done": {}, "active": "M1"})
        done = mstate.setdefault("done", {})
        if done.get(m.mid):
            return
        done[m.mid] = True
        self.profile.setdefault("stats", {}).setdefault("missions_done", 0)
        self.profile["stats"]["missions_done"] += 1

        # reward
        self._add_coins(m.reward_coins)
        self.profile["score"] = int(self.profile.get("score", 0)) + int(m.reward_points)

        # advance
        nxt = None
        for x in self.missions:
            if x.unlock_after == m.mid:
                nxt = x
                break
        if nxt:
            mstate["active"] = nxt.mid

        self._update_rank_and_achievements()
        self._save_state()

    # ---------- UI (CLI) ----------

    def cli_main_menu(self):
        while True:
            clear()
            self._update_rank_and_achievements()
            self._save_state()

            cooldown, left = self._anti_in_cooldown()
            cd_line = f" | COOLDOWN {left}s" if cooldown else ""

            print(f"{APP_NAME} — {self.user} | Βαθμίδα: {self.profile.get('rank','Rookie')} | Σκορ: {self.profile.get('score',0)} | Νομίσματα: {self._coins()}{cd_line}")
            print("Φάκελος εργασίας:", self.ws)
            hr()
            print("1) Προκλήσεις")
            print("2) Επίπεδα Boss")
            print("3) Ημερήσια Πρόκληση")
            print("4) Story Mode (Αποστολές)")
            print("5) Τυχαία Πρόκληση (+)")
            print("6) Κατάστημα Υποδείξεων")
            print("7) Επεξεργαστής Επιπέδων")
            print("8) Πακέτα (εισαγωγή/εξαγωγή)")
            print("9) Τουρνουά")
            print("10) Επιτεύγματα & Στατιστικά")
            print("11) Έλεγχος Ακεραιότητας / Επιδιόρθωση")
            print("0) Έξοδος")
            hr()
            c = input("> ").strip()

            if c == "1":
                self.cli_challenge_list()
            elif c == "2":
                self.cli_boss_menu()
            elif c == "3":
                self.cli_daily()
            elif c == "4":
                self.cli_story()
            elif c == "5":
                r = self.add_random_challenge()
                print("\nΠροστέθηκε τυχαία πρόκληση:", r.cid, "-", r.title)
                print("Αρχείο:", self.ws / r.files[0])
                press()
            elif c == "6":
                self.cli_shop()
            elif c == "7":
                self.cli_level_editor()
            elif c == "8":
                self.cli_packs()
            elif c == "9":
                self.cli_tournament()
            elif c == "10":
                self.cli_achievements()
            elif c == "11":
                self.cli_integrity()
            elif c == "0":
                self._save_state()
                sys.exit(0)

    def _sorted_challenges(self) -> List[Challenge]:
        order = {"Easy":0,"Medium":1,"Hard":2,"Custom":3,"Daily":4,"Random":5}
        return sorted(self.challenges, key=lambda x: (order.get(x.diff, 9), x.category, x.title))

    def cli_challenge_list(self):
        while True:
            clear()
            solved = self.profile.get("solved", {})
            print("Προκλήσεις")
            hr()
            items = self._sorted_challenges()
            for i, c in enumerate(items, 1):
                s = "✓" if c.cid in solved else " "
                print(f"{i:2}) [{s}] {c.cid:6} {c.title:24} [{c.diff:6}] ({c.category}) +{c.points}")
            hr()
            cmd = input("Διάλεξε # ή 0 για πίσω: ").strip()
            if cmd == "0":
                return
            if cmd.isdigit():
                idx = int(cmd) - 1
                if 0 <= idx < len(items):
                    self.cli_play_challenge(items[idx])

    def _cooldown_gate(self) -> bool:
        self._anti_decay()
        cooldown, left = self._anti_in_cooldown()
        if cooldown:
            print(f"⚠️ Anti-cheat cooldown active. Wait {left}s.")
            print("Tip: Use Κατάστημα Υποδείξεων -> cooldown reset (costs coins).")
            press()
            return True
        return False

    def cli_play_challenge(self, c: Challenge, is_daily: bool = False):
        if self._cooldown_gate():
            return
        if not self.integrity_ok():
            print("Ο έλεγχος ακεραιότητας απέτυχε. Χρησιμοποίησε Έλεγχος Ακεραιότητας -> Επιδιόρθωση.")
            press()
            return

        start = time.time()
        while True:
            clear()
            print(f"{c.cid} — {c.title} [{c.diff}] ({c.category})")
            hr()
            print(wrap(c.intro))
            print("\nΑρχεία:")
            for f in c.files:
                print(" -", self.ws / f)
            hr()
            print("1) Υποβολή flag")
            print("2) Υπόδειξη (-10 πόντοι)")
            print("3) Κατάστημα (αγορά hint/reveal/reset cooldown)")
            print("0) Πίσω")
            cmd = input("> ").strip()

            if cmd == "1":
                fl = input("FLAG: ").strip()
                # attempts + anti-cheat
                self.profile.setdefault("attempts", {})
                self.profile["attempts"][c.cid] = self.profile["attempts"].get(c.cid, 0) + 1

                if fl == c.flag_value:
                    elapsed = int(time.time() - start)
                    gained = self._compute_points(c.points, elapsed, c.hints_used)

                    solved = self.profile.setdefault("solved", {})
                    if c.cid not in solved:
                        solved[c.cid] = {"time": elapsed, "points": gained, "ts": now()}
                        self.profile["score"] = int(self.profile.get("score", 0)) + gained
                        self.profile.setdefault("stats", {}).setdefault("total_solves", 0)
                        self.profile["stats"]["total_solves"] += 1
                        if c.hints_used == 0:
                            self.profile["stats"]["no_hint_solves"] = self.profile["stats"].get("no_hint_solves", 0) + 1
                        if elapsed <= 30:
                            self.profile["stats"]["fast_solves"] = self.profile["stats"].get("fast_solves", 0) + 1

                        # coins
                        self._award_solve_coins(c.points, is_daily=is_daily)

                        # daily stat
                        if is_daily:
                            self.profile["stats"]["daily_solves"] = self.profile["stats"].get("daily_solves", 0) + 1

                    self._anti_on_correct()
                    self._update_rank_and_achievements()
                    self._save_state()
                    print(f"\n✅ Σωστό! +{gained} pts | time={elapsed}s | hints={c.hints_used}")
                    print(f"💰 Coins now: {self._coins()}")
                    press()
                    return
                else:
                    self._anti_record_wrong(fl)
                    cooldown, left = self._anti_in_cooldown()
                    if cooldown:
                        print(f"\n❌ Λάθος. Anti-cheat triggered cooldown: {left}s.")
                    else:
                        print("\n❌ Λάθος flag.")
                    self._save_state()
                    press()

            elif cmd == "2":
                c.hints_used += 1
                hint = c.hint_texts[min(c.hints_used - 1, len(c.hint_texts) - 1)]
                print("\nΥπόδειξη:", hint)
                press()

            elif cmd == "3":
                self.cli_shop(current_challenge=c)
            elif cmd == "0":
                return

    def cli_boss_menu(self):
        while True:
            clear()
            print("Επίπεδα Boss")
            hr()
            solved = self.profile.get("solved", {})
            for i, b in enumerate(self.bosses, 1):
                s = "✓" if b.bid in solved else "🔥"
                print(f"{i}) [{s}] {b.title:20} +{b.points}  ({b.description})")
            hr()
            cmd = input("Διάλεξε #, 0 για πίσω: ").strip()
            if cmd == "0":
                return
            if cmd.isdigit():
                idx = int(cmd) - 1
                if 0 <= idx < len(self.bosses):
                    self.cli_play_boss(self.bosses[idx])

    def cli_play_boss(self, b: Boss):
        if self._cooldown_gate():
            return
        if not self.integrity_ok():
            print("Ο έλεγχος ακεραιότητας απέτυχε. Χρησιμοποίησε Επιδιόρθωση.")
            press()
            return

        clear()
        print(f"BOSS — {b.title}")
        hr()
        print(wrap(b.description))
        print("\nFolder:", self.ws / b.folder)
        print("\nStages:")
        for s in b.stages:
            print(" -", s)
        press("\nΠάτησε Enter όταν είσαι έτοιμος να υποβάλεις το FINAL FLAG...")

        fl = input("FINAL FLAG: ").strip()
        real = flag(self.profile["seed"], b.bid)
        if fl == real:
            solved = self.profile.setdefault("solved", {})
            if b.bid not in solved:
                solved[b.bid] = {"time": 0, "points": b.points, "ts": now()}
                self.profile["score"] = int(self.profile.get("score", 0)) + b.points
                self.profile.setdefault("stats", {}).setdefault("boss_kills", 0)
                self.profile["stats"]["boss_kills"] += 1
                self._add_coins(COINS_PER_BOSS)
            self._anti_on_correct()
            self._update_rank_and_achievements()
            self._save_state()
            print(f"\n🏆 ΝΙΚΗΣΕΣ ΤΟ BOSS! +{b.points} pts | +{COINS_PER_BOSS} coins")
        else:
            self._anti_record_wrong(fl)
            cooldown, left = self._anti_in_cooldown()
            if cooldown:
                print(f"\n❌ Λάθος. Cooldown triggered: {left}s.")
            else:
                print("\n❌ Λάθος.")
        press()

    def cli_daily(self):
        d = self.ensure_daily()
        daily_state = self.profile.setdefault("daily", {"solved": {}})
        if daily_state.get("solved", {}).get(d.cid):
            clear()
            print("Ημερήσια Πρόκληση")
            hr()
            print("✅ ✅ Ήδη λυμένο σήμερα:", d.cid)
            print("Έλα ξανά αύριο για νέο daily.")
            press()
            return
        self.cli_play_challenge(d, is_daily=True)
        # if solved, mark
        if d.cid in self.profile.get("solved", {}):
            daily_state.setdefault("solved", {})[d.cid] = True
            self._save_state()

    def cli_story(self):
        while True:
            clear()
            mstate = self.profile.setdefault("missions", {"done": {}, "active": "M1"})
            done = mstate.get("done", {})
            print("Story Mode — Αποστολές")
            hr()
            for m in self.missions:
                if not self._mission_is_unlocked(m):
                    continue
                status = "✓" if done.get(m.mid) else ("▶" if m.mid == mstate.get("active") else " ")
                print(f"[{status}] {m.mid} — {m.title}")
                print("    Στόχος:", m.objective)
            hr()
            print("1) Έλεγχος ολοκλήρωσης τρέχουσας αποστολής")
            print("2) Πάρε ανταμοιβή αποστολής (αν ολοκληρώθηκε)")
            print("0) Πίσω")
            hr()
            c = input("> ").strip()
            if c == "0":
                return
            cur, _ = self.story_status()
            if c == "1":
                ok = self._mission_is_completed(cur)
                print("\nΤρέχουσα αποστολή:", cur.mid, "-", cur.title)
                print("Ολοκληρώθηκε:", "YES ✅" if ok else "NO ❌")
                print("Απαιτεί λύση:", ", ".join(cur.requires_solves))
                press()
            elif c == "2":
                if self._mission_is_completed(cur):
                    self._mission_complete_and_advance(cur)
                    print("\n🏁 Η αποστολή ολοκληρώθηκε! Πήρες ανταμοιβές:")
                    print(f"+{cur.reward_points} pts, +{cur.reward_coins} coins")
                    nxt, _ = self.story_status()
                    print("Επόμενη αποστολή:", nxt.mid, "-", nxt.title)
                else:
                    print("\nΔεν έχει ολοκληρωθεί ακόμα.")
                press()

    def cli_shop(self, current_challenge: Optional[Challenge] = None):
        choice = self.shop_menu()
        if choice == "0":
            return
        if choice == "1":
            if current_challenge is None:
                print("\nΔεν υπάρχει ενεργή πρόκληση. Άνοιξε πρώτα μία πρόκληση.")
                press()
                return
            if not self._spend_coins(HINT_COST):
                print("\nΔεν έχεις αρκετά νομίσματα.")
                press()
                return
            # give a hint without adding hint penalty (shop hint is separate from in-challenge hint penalty)
            idx = min(current_challenge.hints_used, len(current_challenge.hint_texts) - 1)
            hint = current_challenge.hint_texts[idx]
            current_challenge.hints_used += 1  # still counts as hint use for scoring fairness
            self._save_state()
            print("\n🛒 Αγόρασες hint:", hint)
            press()
            return

        if choice == "2":
            if current_challenge is None:
                print("\nΔεν υπάρχει ενεργή πρόκληση. Άνοιξε πρώτα μία πρόκληση.")
                press()
                return
            if not self._spend_coins(REVEAL_COST):
                print("\nΔεν έχεις αρκετά νομίσματα.")
                press()
                return
            reveal = current_challenge.flag_value[:5] + "..."
            self._save_state()
            print("\n🛒 Μικρή αποκάλυψη:", reveal)
            press()
            return

        if choice == "3":
            if not self._spend_coins(RESET_COOLDOWN_COST):
                print("\nΔεν έχεις αρκετά νομίσματα.")
                press()
                return
            anti = self._anti()
            anti["cooldown_until"] = 0
            anti["suspicion"] = max(0, int(anti.get("suspicion", 0)) - 3)
            self._save_state()
            print("\n🛒 Αγοράστηκε reset cooldown.")
            press()
            return

    def cli_level_editor(self):
        clear()
        print("Επεξεργαστής Επιπέδων (Custom Challenge)")
        hr()
        lvl_id = normalize_username(input("ID Επιπέδου (μοναδικό): "))
        title = input("Τίτλος: ").strip() or f"Custom {lvl_id}"
        intro = input("Εισαγωγή/Ιστορία: ").strip() or "Solve the custom challenge."
        points = int((input("Πόντοι (π.χ. 120): ").strip() or "120"))
        print("\nΕπιλογές τύπου: plain / base64 / rot13 / xor / layered")
        ctype = input("Τύπος: ").strip().lower() or "plain"
        ext = "txt"
        hints = []
        print("\nΠρόσθεσε έως 3 hints (κενό για τέλος):")
        for i in range(3):
            h = input(f"Hint {i+1}: ").strip()
            if not h:
                break
            hints.append(h)
        if not hints:
            hints = ["Try analyzing the encoding/format."]

        key = 42
        if ctype == "xor":
            key = int((input("Κλειδί XOR (0-255, προεπιλογή 42): ").strip() or "42"))

        level_obj = {"id": lvl_id, "title": title, "intro": intro, "points": points, "type": ctype, "ext": ext, "hints": hints}
        if ctype == "xor":
            level_obj["key"] = key

        levels = self.custom.setdefault("levels", [])
        for i, lvl in enumerate(levels):
            if str(lvl.get("id")) == lvl_id:
                levels[i] = level_obj
                break
        else:
            levels.append(level_obj)

        self._save_custom()
        self._build_all()
        self.repair_workspace()
        print("\n✅ Το custom επίπεδο αποθηκεύτηκε & δημιουργήθηκε στο:")
        print(" ", self.ws / f"custom/{lvl_id}.txt")
        press()

    def cli_packs(self):
        while True:
            clear()
            packs = self.list_packs()
            print("Πακέτα Προκλήσεων")
            hr()
            print("Διαθέσιμα πακέτα:", ", ".join(packs) if packs else "(κανένα)")
            hr()
            print("1) Εξαγωγή των custom επιπέδων μου")
            print("2) Εισαγωγή πακέτου")
            print("0) Πίσω")
            hr()
            c = input("> ").strip()
            if c == "0":
                return
            if c == "1":
                name = input("Όνομα πακέτου: ").strip()
                p = self.export_pack(name)
                print("\nΕξήχθη στο:", p)
                press()
            elif c == "2":
                name = input("Όνομα πακέτου (χωρίς .json): ").strip()
                ok, msg = self.import_pack(name)
                print("\n" + msg)
                press()

    def cli_tournament(self):
        while True:
            clear()
            print("Τουρνουά Mode (offline)")
            hr()
            tournaments = sorted(self.state.get("tournaments", {}).keys())
            if tournaments:
                for t in tournaments:
                    lock = "LOCKED" if self.state["tournaments"][t].get("locked") else "OPEN"
                    print(f"- {t} ({lock})")
            else:
                print("(δεν υπάρχουν τουρνουά ακόμα)")
            hr()
            print("1) Δημιουργία τουρνουά")
            print("2) Κλείδωμα τουρνουά")
            print("3) Υποβολή σκορ")
            print("4) Προβολή κατάταξης")
            print("0) Πίσω")
            hr()
            c = input("> ").strip()
            if c == "0":
                return
            if c == "1":
                name = input("Τουρνουά name: ").strip()
                self.tournament_create(name)
                print("\nΔημιουργήθηκε.")
                press()
            elif c == "2":
                name = input("Τουρνουά name: ").strip()
                ok, msg = self.tournament_lock(name)
                print("\n" + msg)
                press()
            elif c == "3":
                name = input("Τουρνουά name: ").strip()
                ok, msg = self.tournament_submit(name)
                print("\n" + msg)
                press()
            elif c == "4":
                name = input("Τουρνουά name: ").strip()
                ok, status, scores = self.tournament_leaderboard(name)
                if not ok:
                    print("\n" + status)
                    press()
                    continue
                print(f"\nΚατάταξη ({status})")
                hr()
                for i, (u, s) in enumerate(scores, 1):
                    print(f"{i:2}) {u:24} {s}")
                press()

    def cli_achievements(self):
        clear()
        self._update_rank_and_achievements()
        self._save_state()
        print("Επιτεύγματα & Στατιστικά")
        hr()
        ach = self.profile.get("achievements", {})
        if not ach:
            print("(κανένα επίτευγμα ακόμα)")
        else:
            for k in sorted(ach.keys()):
                print("✓", k)
        hr()
        print("Βαθμίδα:", self.profile.get("rank", "Rookie"))
        print("Σκορ:", self.profile.get("score", 0))
        print("Νομίσματα:", self._coins())
        stats = self.profile.get("stats", {})
        print("\nΣτατιστικά:")
        for k in ["total_solves","boss_kills","daily_solves","missions_done","no_hint_solves","fast_solves","packs_exported","tournament_submits","shop_purchases"]:
            print(f"- {k}: {stats.get(k,0)}")
        anti = self._anti()
        print("\nAnti-cheat: υποψία=", anti.get("suspicion",0), "cooldown_until=", anti.get("cooldown_until",0))
        press()

    def cli_integrity(self):
        clear()
        print("Έλεγχος Ακεραιότητας / Επιδιόρθωση")
        hr()
        ok = self.integrity_ok()
        print("Κατάσταση ακεραιότητας:", "OK ✅" if ok else "ΑΠΕΤΥΧΕ ❌")
        print("\nΑν ΑΠΕΤΥΧΕ, συνήθως σημαίνει ότι τα αρχεία τροποποιήθηκαν ή χάλασαν.")
        hr()
        print("1) Επιδιόρθωση φακέλου (επαν-δημιουργία αρχείων)")
        print("0) Πίσω")
        hr()
        c = input("> ").strip()
        if c == "1":
            self.repair_workspace()
            print("\nΕπιδιορθώθηκε. Η ακεραιότητα θα πρέπει να είναι OK τώρα.")
            press()

    # ---------- Run ----------

    def run(self):
        if str(self.root).startswith("/storage/emulated/0") and not Path("/storage/emulated/0").exists():
            clear()
            print("Η πρόσβαση αποθήκευσης δεν είναι έτοιμη.")
            hr()
            print("Τρέξε μία φορά στο Termux:  termux-setup-storage")
            print("Μετά κάνε επανεκκίνηση το Termux και τρέξε ξανά το παιχνίδι.")
            press()
            return

        # (Curses UI exists in v8; v9 keeps CLI as the “full features” interface for stability.)
        # You can still toggle UI preference in login if you want; fallback always works.
        self.cli_main_menu()

# ---------------- Entry ----------------

def main():
    g = CTFGod()
    g.login()
    g.run()

if __name__ == "__main__":
    main()
