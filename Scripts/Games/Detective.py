#!/usr/bin/env python3
# Detective.py — Termux detective game (self-contained)
# Saves everything in ~/Detective/
#
# This version:
# - 90 FIXED, PREFIXED, UNIQUE stories (no story generation during play)
# - Long-case pacing: accusation locked until 40 minutes elapsed
# - Save/Load: 3 slots + autosave + manual :save
# - Rich actions, interrogation, ASCII visuals (:board, :timeline, :guide)

import os
import json
import time
import datetime
import textwrap
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

APP_NAME = "Detective.py"
SAVE_DIR_NAME = "Detective"
WRAP = 78

REQUIRED_MINUTES_PER_CASE = 40
SAVE_SLOTS = [1, 2, 3]

DIFFICULTIES = {
    "1": {"name": "Rookie",    "hint_tokens": 7, "strict": 0, "min_actions": 2, "time_bonus": 1.0},
    "2": {"name": "Detective", "hint_tokens": 4, "strict": 1, "min_actions": 3, "time_bonus": 1.1},
    "3": {"name": "Noir",      "hint_tokens": 2, "strict": 2, "min_actions": 4, "time_bonus": 1.25},
    "4": {"name": "Legend",    "hint_tokens": 1, "strict": 3, "min_actions": 4, "time_bonus": 1.4},
}

SAFETY_NOTE = (
    "Content note: This game may include non-graphic references to serious crimes "
    "including homicide, corruption, and sexual assault. It avoids explicit detail."
)

# ----------------------------- Fixed story library (90) -----------------------------
BLUEPRINTS: List[Dict[str, Any]] = [{'id': 'A01', 'title': 'A01 — Rivergate Balcony File', 'case_type': 'murder', 'setting': 'a high-rise overlooking a canal', 'victim_role': 'a property developer', 'hook': 'The scene looks ordinary until you check what should have been impossible.', 'victim_name': 'Casey Bennett', 'date': 'January 04, 2025', 'weather': 'cold drizzle', 'smell': 'bleach and metal', 'suspects': [{'name': 'Jon Yilmaz', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Dana Santos', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Noah Vallis', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Samira Khan', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'to stop a blackmail payoff', 'method': 'loosened railing bolts', 'key': 'fresh wrench marks'}, 'supports': ["a door that was 'locked' but not latched", 'a witness who changes wording under pressure', 'a contradicted alibi minute-by-minute', 'a photo edited, but not where people claim', 'an access attempt minutes before the reported time', 'a timeline that depends on the wrong clock'], 'reds': ["a partial fingerprint that doesn't match anyone here", "a witness who 'remembers' after being prompted", 'a key that belongs to somewhere else'], 'anchors': [('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.')]}, {'id': 'A02', 'title': 'A02 — Cold Ink Newsroom Memo', 'case_type': 'political', 'setting': 'an independent newspaper office', 'victim_role': 'an investigative editor', 'hook': 'A complaint is filed, and the timeline is the weapon.', 'victim_name': 'Taylor Delphi', 'date': 'January 07, 2025', 'weather': 'dry wind', 'smell': 'coffee and dust', 'suspects': [{'name': 'Jules Yilmaz', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Aris Sato', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Sofia Markou', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Lucas Vallis', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'to bury a donor list', 'method': 'stole draft + staged a break-in', 'key': 'printer log timestamp'}, 'supports': ['a timeline that depends on the wrong clock', 'a staff roster with a late change', "a door that was 'locked' but not latched", 'a maintenance schedule that was quietly edited', 'a printed document with a subtle formatting difference', 'an object moved against habit'], 'reds': ["a broken object that looks important but isn't", 'a rumor about secret debts', 'a misread CCTV reflection'], 'anchors': [('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.')]}, {'id': 'A03', 'title': 'A03 — Silk Road Motel Pattern', 'case_type': 'sexual_assault', 'setting': 'a roadside motel off a dim highway', 'victim_role': 'a traveling musician', 'hook': 'A clean story is offered immediately. Your job is to find what it avoids.', 'victim_name': 'Jamie Kane', 'date': 'January 10, 2025', 'weather': 'humid night air', 'smell': 'ozone and damp paper', 'suspects': [{'name': 'Aris Ibrahim', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Aris Santos', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Aris Rossi', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Dimitri Kline', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 0, 'motive': 'predation + silencing', 'method': 'coercion and intimidation', 'key': 'door camera gap + keycard data'}, 'supports': ['a quiet payment made in an odd amount', 'a missing entry in the visitor log', 'a second copy of a report with one word changed', "a door that was 'locked' but not latched", 'a message thread with deleted lines', 'a maintenance schedule that was quietly edited'], 'reds': ['a misread CCTV reflection', 'a key that belongs to somewhere else', 'a dramatic argument overheard earlier'], 'anchors': [('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.')]}, {'id': 'A04', 'title': 'A04 — Vanished Ledger Office Switch', 'case_type': 'murder', 'setting': 'a municipal finance office', 'victim_role': 'a whistleblower accountant', 'hook': 'A perfect alibi depends on one assumption you can test.', 'victim_name': 'Jordan Kane', 'date': 'January 13, 2025', 'weather': 'sharp winter cold', 'smell': 'salt and engine oil', 'suspects': [{'name': 'Lucas Delphi', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Theo Kerr', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Nadia Delphi', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Dana Kerr', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'embezzlement cover-up', 'method': 'forged resignation + shredding', 'key': 'ink mismatch on signature'}, 'supports': ['call history showing a short, repeated number', 'a quiet payment made in an odd amount', 'an object moved against habit', 'an access attempt minutes before the reported time', 'a staff roster with a late change', "a door that was 'locked' but not latched"], 'reds': ['a dramatic argument overheard earlier', 'an old threat letter with no date', 'a viral post with a cropped timestamp'], 'anchors': [('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement.")]}, {'id': 'A05', 'title': 'A05 — Midnight Docks Signal', 'case_type': 'political', 'setting': 'a container terminal at night', 'victim_role': 'a customs broker', 'hook': 'A perfect alibi depends on one assumption you can test.', 'victim_name': 'Morgan Petros', 'date': 'January 16, 2025', 'weather': 'heavy coastal mist', 'smell': 'perfume over disinfectant', 'suspects': [{'name': 'Elena Kerr', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Sofia Wu', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Lea Vallis', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Mikhail Kline', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 0, 'motive': 'covering a financial fraud', 'method': 'poison slipped into a drink', 'key': 'security log gap'}, 'supports': ['a suspicious purchase record', 'a delivery receipt with a serial gap', 'an object moved against habit', 'a witness who changes wording under pressure', 'a contradicted alibi minute-by-minute', 'a second copy of a report with one word changed'], 'reds': ['a misread CCTV reflection', 'an old threat letter with no date', 'a dramatic argument overheard earlier'], 'anchors': [('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.')]}, {'id': 'A06', 'title': 'A06 — Opera Opera House Case', 'case_type': 'murder', 'setting': 'a restored opera house backstage', 'victim_role': 'a cultural minister', 'hook': 'A missing object matters more than the object itself.', 'victim_name': 'Riley Lennox', 'date': 'January 19, 2025', 'weather': 'late-summer heat', 'smell': 'old books and varnish', 'suspects': [{'name': 'Lucas Hale', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Lucas Santos', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Mikhail Okoye', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Alex Khan', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'political leverage', 'method': 'staged accident', 'key': 'CCTV angle blind spot'}, 'supports': ['a quiet payment made in an odd amount', 'a photo edited, but not where people claim', 'a maintenance schedule that was quietly edited', "a door that was 'locked' but not latched", 'a handwritten note with familiar pressure pattern', 'pollen trace matching a specific place'], 'reds': ['a key that belongs to somewhere else', 'a rumor about secret debts', "a partial fingerprint that doesn't match anyone here"], 'anchors': [('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.')]}, {'id': 'A07', 'title': 'A07 — Pinecrest Cabin Signal', 'case_type': 'political', 'setting': 'a forest cabin community', 'victim_role': 'a retired firefighter', 'hook': 'Everyone agrees on the headline, but nobody agrees on the minutes.', 'victim_name': 'Avery Hwang', 'date': 'January 22, 2025', 'weather': 'electric storm air', 'smell': 'citrus cleaner', 'suspects': [{'name': 'Mina Kerr', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Omar Nassar', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Elias Nielsen', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Dimitri Tanaka', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'silencing a witness', 'method': 'tampered equipment', 'key': 'tool mark evidence'}, 'supports': ['a maintenance schedule that was quietly edited', 'a delivery receipt with a serial gap', 'a photo edited, but not where people claim', 'a small scratch pattern consistent with a hurried tool', 'a witness who changes wording under pressure', 'a quiet payment made in an odd amount'], 'reds': ["a partial fingerprint that doesn't match anyone here", 'a fake social media screenshot', 'a misleading anonymous tip email'], 'anchors': [('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.')]}, {'id': 'A08', 'title': 'A08 — Clinic Clinic Pattern', 'case_type': 'sexual_assault', 'setting': 'a private clinic reception area', 'victim_role': 'a graduate student', 'hook': 'A perfect alibi depends on one assumption you can test.', 'victim_name': 'Drew Delphi', 'date': 'January 25, 2025', 'weather': 'cold drizzle', 'smell': 'bleach and metal', 'suspects': [{'name': 'Mikhail Hart', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Jon Baird', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Dimitri Khan', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Omar Vega', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'career sabotage', 'method': 'edited logs', 'key': 'keypad code change record'}, 'supports': ['a printed document with a subtle formatting difference', 'a message thread with deleted lines', 'a suspicious purchase record', 'an access attempt minutes before the reported time', 'a quiet payment made in an odd amount', 'a delivery receipt with a serial gap'], 'reds': ['an old threat letter with no date', 'a fake social media screenshot', "a witness who 'remembers' after being prompted"], 'anchors': [('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.')]}, {'id': 'A09', 'title': 'A09 — Split Vote Council Memo', 'case_type': 'murder', 'setting': 'a city council chamber', 'victim_role': 'a council aide', 'hook': 'A statement arrives early, too polished to be spontaneous.', 'victim_name': 'Riley Novak', 'date': 'January 28, 2025', 'weather': 'dry wind', 'smell': 'coffee and dust', 'suspects': [{'name': 'Dana Volkov', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Aris Arden', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Hana Volkov', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Mina Santos', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'protecting an accomplice', 'method': 'misdirected delivery', 'key': 'badge access anomaly'}, 'supports': ["a door that was 'locked' but not latched", 'a suspicious purchase record', 'a staff roster with a late change', 'a contradicted alibi minute-by-minute', 'a second copy of a report with one word changed', 'a quiet payment made in an odd amount'], 'reds': ['a viral post with a cropped timestamp', 'a fake social media screenshot', "a partial fingerprint that doesn't match anyone here"], 'anchors': [('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.')]}, {'id': 'A10', 'title': 'A10 — Blue Velvet Gallery Case', 'case_type': 'political', 'setting': 'a modern art gallery', 'victim_role': 'an art patron', 'hook': 'A statement arrives early, too polished to be spontaneous.', 'victim_name': 'Taylor Hwang', 'date': 'January 31, 2025', 'weather': 'humid night air', 'smell': 'ozone and damp paper', 'suspects': [{'name': 'Ivo Kerr', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Iris Volkov', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Lea Novak', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Jules Volkov', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'avoiding exposure', 'method': 'swapped two identical folders', 'key': 'metadata timestamp mismatch'}, 'supports': ['a contradicted alibi minute-by-minute', 'an access attempt minutes before the reported time', 'a printed document with a subtle formatting difference', 'a handwritten note with familiar pressure pattern', 'a staff roster with a late change', 'a delivery receipt with a serial gap'], 'reds': ['a misread CCTV reflection', 'a dramatic argument overheard earlier', 'a rumor about secret debts'], 'anchors': [('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.')]}, {'id': 'A11', 'title': 'A11 — Harborline Train Night', 'case_type': 'murder', 'setting': 'a commuter train mid-route', 'victim_role': 'a logistics manager', 'hook': 'A complaint is filed, and the timeline is the weapon.', 'victim_name': 'Morgan Kerr', 'date': 'February 03, 2025', 'weather': 'sharp winter cold', 'smell': 'salt and engine oil', 'suspects': [{'name': 'Hana Nielsen', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Mara Markou', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Samira Tanaka', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Lea Petros', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'coercion and control', 'method': 'removed a safety stop', 'key': 'soil/pollen trace'}, 'supports': ['a missing entry in the visitor log', 'a witness who changes wording under pressure', 'an access attempt minutes before the reported time', 'a quiet payment made in an odd amount', 'pollen trace matching a specific place', 'a suspicious purchase record'], 'reds': ["a broken object that looks important but isn't", 'a rumor about secret debts', "a partial fingerprint that doesn't match anyone here"], 'anchors': [('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement.")]}, {'id': 'A12', 'title': 'A12 — Charity Banquet Signal', 'case_type': 'political', 'setting': 'a charity banquet hall', 'victim_role': 'a fundraiser', 'hook': 'A complaint is filed, and the timeline is the weapon.', 'victim_name': 'Sam Hart', 'date': 'February 06, 2025', 'weather': 'heavy coastal mist', 'smell': 'perfume over disinfectant', 'suspects': [{'name': 'Hana Ibrahim', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Dana Tanaka', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Jules Khan', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Omar Rossi', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'insurance payout', 'method': 'covert recording + smear', 'key': 'call detail record'}, 'supports': ['pollen trace matching a specific place', 'a small scratch pattern consistent with a hurried tool', 'a delivery receipt with a serial gap', 'a staff roster with a late change', 'a printed document with a subtle formatting difference', 'a timeline that depends on the wrong clock'], 'reds': ["a partial fingerprint that doesn't match anyone here", 'a key that belongs to somewhere else', 'a misread CCTV reflection'], 'anchors': [('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.')]}, {'id': 'A13', 'title': 'A13 — Saffron Alley Signal', 'case_type': 'sexual_assault', 'setting': 'a nightlife district alley', 'victim_role': 'a bartender', 'hook': 'The scene looks ordinary until you check what should have been impossible.', 'victim_name': 'Casey Novak', 'date': 'February 09, 2025', 'weather': 'late-summer heat', 'smell': 'old books and varnish', 'suspects': [{'name': 'Nadia Kline', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Mikhail Ibrahim', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Kostas Rossi', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Aris Kane', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'revenge for a past betrayal', 'method': 'loosened railing bolts', 'key': 'receipt serial gap'}, 'supports': ['pollen trace matching a specific place', 'a delivery receipt with a serial gap', 'a timeline that depends on the wrong clock', 'a suspicious purchase record', 'call history showing a short, repeated number', 'an object moved against habit'], 'reds': ['a fake social media screenshot', 'a dramatic argument overheard earlier', 'a key that belongs to somewhere else'], 'anchors': [('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.')]}, {'id': 'A14', 'title': 'A14 — Campus Boardroom Signal', 'case_type': 'murder', 'setting': 'a university boardroom', 'victim_role': 'a dean', 'hook': 'A perfect alibi depends on one assumption you can test.', 'victim_name': 'Riley Hart', 'date': 'February 12, 2025', 'weather': 'electric storm air', 'smell': 'citrus cleaner', 'suspects': [{'name': 'Talia Petros', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Jon Vega', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Ivo Baird', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Lucas Pappas', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'jealousy over a secret relationship', 'method': 'stole draft + staged a break-in', 'key': 'elevator panel smear pattern'}, 'supports': ['a photo edited, but not where people claim', 'a witness who changes wording under pressure', 'a second copy of a report with one word changed', 'a maintenance schedule that was quietly edited', 'a suspicious purchase record', 'call history showing a short, repeated number'], 'reds': ['a suspicious-looking stranger nearby', "a broken object that looks important but isn't", 'a fake social media screenshot'], 'anchors': [('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.')]}, {'id': 'A15', 'title': 'A15 — Windswept Lighthouse File', 'case_type': 'political', 'setting': 'a coastal lighthouse stairwell', 'victim_role': 'a marine biologist', 'hook': 'The scene looks ordinary until you check what should have been impossible.', 'victim_name': 'Morgan Roux', 'date': 'February 15, 2025', 'weather': 'cold drizzle', 'smell': 'bleach and metal', 'suspects': [{'name': 'Theo Hart', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Mikhail Khan', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Jon Hart', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Aris Markou', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 0, 'motive': 'to stop a blackmail payoff', 'method': 'coercion and intimidation', 'key': 'tamper seal mismatch'}, 'supports': ['a witness who changes wording under pressure', 'a message thread with deleted lines', 'a handwritten note with familiar pressure pattern', 'a quiet payment made in an odd amount', 'a printed document with a subtle formatting difference', 'a missing entry in the visitor log'], 'reds': ["a broken object that looks important but isn't", 'a dramatic argument overheard earlier', "a witness who 'remembers' after being prompted"], 'anchors': [('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.')]}, {'id': 'A16', 'title': 'A16 — Backroom Contract Ledger', 'case_type': 'murder', 'setting': 'a construction office backroom', 'victim_role': 'a procurement officer', 'hook': 'A statement arrives early, too polished to be spontaneous.', 'victim_name': 'Quinn Hart', 'date': 'February 18, 2025', 'weather': 'dry wind', 'smell': 'coffee and dust', 'suspects': [{'name': 'Talia Nielsen', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Selene Hale', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Theo Vallis', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Maya Baird', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'to bury a donor list', 'method': 'forged resignation + shredding', 'key': 'fresh wrench marks'}, 'supports': ['a maintenance schedule that was quietly edited', 'a small scratch pattern consistent with a hurried tool', 'a photo edited, but not where people claim', 'pollen trace matching a specific place', 'a second copy of a report with one word changed', 'an access attempt minutes before the reported time'], 'reds': ['a key that belongs to somewhere else', 'a misread CCTV reflection', "a broken object that looks important but isn't"], 'anchors': [('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.')]}, {'id': 'A17', 'title': 'A17 — Alleyway Statement Night', 'case_type': 'political', 'setting': 'a crowded festival zone', 'victim_role': 'a volunteer', 'hook': 'A statement arrives early, too polished to be spontaneous.', 'victim_name': 'Avery Hart', 'date': 'February 21, 2025', 'weather': 'humid night air', 'smell': 'ozone and damp paper', 'suspects': [{'name': 'Elena Volkov', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Hana Kerr', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Mina Baird', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Aris Nielsen', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'predation + silencing', 'method': 'poison slipped into a drink', 'key': 'printer log timestamp'}, 'supports': ['a delivery receipt with a serial gap', 'an object moved against habit', 'a small scratch pattern consistent with a hurried tool', 'a suspicious purchase record', 'an access attempt minutes before the reported time', 'a witness who changes wording under pressure'], 'reds': ['a misread CCTV reflection', "a partial fingerprint that doesn't match anyone here", 'a misleading anonymous tip email'], 'anchors': [('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.')]}, {'id': 'A18', 'title': 'A18 — Quartz Hill Pharmacy Memo', 'case_type': 'sexual_assault', 'setting': 'a late-night pharmacy', 'victim_role': 'a pharmacist', 'hook': 'A perfect alibi depends on one assumption you can test.', 'victim_name': 'Jordan Kane', 'date': 'February 24, 2025', 'weather': 'sharp winter cold', 'smell': 'salt and engine oil', 'suspects': [{'name': 'Dana Serrano', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Mikhail Sato', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Elena Markou', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Mina Kane', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'embezzlement cover-up', 'method': 'staged accident', 'key': 'door camera gap + keycard data'}, 'supports': ['a staff roster with a late change', "a door that was 'locked' but not latched", 'a second copy of a report with one word changed', 'a timeline that depends on the wrong clock', 'a printed document with a subtle formatting difference', 'pollen trace matching a specific place'], 'reds': ["a partial fingerprint that doesn't match anyone here", 'a key that belongs to somewhere else', 'a misread CCTV reflection'], 'anchors': [('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement.")]}, {'id': 'A19', 'title': 'A19 — Redacted Email Ledger', 'case_type': 'murder', 'setting': 'a ministerial IT department', 'victim_role': 'a sysadmin', 'hook': 'A clean story is offered immediately. Your job is to find what it avoids.', 'victim_name': 'Drew Bennett', 'date': 'February 27, 2025', 'weather': 'heavy coastal mist', 'smell': 'perfume over disinfectant', 'suspects': [{'name': 'Priya Khan', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Nadia Hale', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Lea Wu', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Nadia Baird', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'covering a financial fraud', 'method': 'tampered equipment', 'key': 'ink mismatch on signature'}, 'supports': ['a missing entry in the visitor log', 'a message thread with deleted lines', 'a staff roster with a late change', 'an object moved against habit', 'a second copy of a report with one word changed', 'a timeline that depends on the wrong clock'], 'reds': ['a misleading anonymous tip email', 'a viral post with a cropped timestamp', "a witness who 'remembers' after being prompted"], 'anchors': [('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.')]}, {'id': 'A20', 'title': 'A20 — Orchard Estate Night', 'case_type': 'political', 'setting': 'a countryside estate lodge', 'victim_role': 'a family heir', 'hook': 'A complaint is filed, and the timeline is the weapon.', 'victim_name': 'Taylor Hwang', 'date': 'March 02, 2025', 'weather': 'late-summer heat', 'smell': 'old books and varnish', 'suspects': [{'name': 'Iris Vega', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Talia Tanaka', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Ivo Yilmaz', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Talia Santos', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 0, 'motive': 'political leverage', 'method': 'edited logs', 'key': 'security log gap'}, 'supports': ['call history showing a short, repeated number', 'a message thread with deleted lines', 'a suspicious purchase record', 'a handwritten note with familiar pressure pattern', 'a second copy of a report with one word changed', 'a staff roster with a late change'], 'reds': ["a broken object that looks important but isn't", 'a rumor about secret debts', 'a dramatic argument overheard earlier'], 'anchors': [('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.')]}, {'id': 'A21', 'title': 'A21 — Embassy Briefcase Case', 'case_type': 'murder', 'setting': 'an embassy reception corridor', 'victim_role': 'a diplomat', 'hook': 'A statement arrives early, too polished to be spontaneous.', 'victim_name': 'Morgan Delphi', 'date': 'March 05, 2025', 'weather': 'electric storm air', 'smell': 'citrus cleaner', 'suspects': [{'name': 'Yara Hale', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Niko Vallis', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Mina Sato', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Elena Khan', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'silencing a witness', 'method': 'misdirected delivery', 'key': 'CCTV angle blind spot'}, 'supports': ['a message thread with deleted lines', 'an access attempt minutes before the reported time', 'a witness who changes wording under pressure', 'a maintenance schedule that was quietly edited', 'a suspicious purchase record', 'a delivery receipt with a serial gap'], 'reds': ['a viral post with a cropped timestamp', 'a misread CCTV reflection', 'a fake social media screenshot'], 'anchors': [('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.')]}, {'id': 'A22', 'title': 'A22 — Seabed Grant Incident', 'case_type': 'political', 'setting': 'a research institute wing', 'victim_role': 'a grant reviewer', 'hook': 'A complaint is filed, and the timeline is the weapon.', 'victim_name': 'Avery Lennox', 'date': 'March 08, 2025', 'weather': 'cold drizzle', 'smell': 'bleach and metal', 'suspects': [{'name': 'Hana Okoye', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Iris Rowan', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Jules Santos', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Samira Volkov', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'career sabotage', 'method': 'swapped two identical folders', 'key': 'tool mark evidence'}, 'supports': ['a handwritten note with familiar pressure pattern', 'a missing entry in the visitor log', "a door that was 'locked' but not latched", 'a delivery receipt with a serial gap', 'call history showing a short, repeated number', 'a printed document with a subtle formatting difference'], 'reds': ['a misread CCTV reflection', 'a key that belongs to somewhere else', "a partial fingerprint that doesn't match anyone here"], 'anchors': [('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.')]}, {'id': 'A23', 'title': 'A23 — Neon Arcade Night', 'case_type': 'sexual_assault', 'setting': 'a retro arcade floor', 'victim_role': 'an e-sports coach', 'hook': 'Everyone agrees on the headline, but nobody agrees on the minutes.', 'victim_name': 'Jordan Novak', 'date': 'March 11, 2025', 'weather': 'dry wind', 'smell': 'coffee and dust', 'suspects': [{'name': 'Dana Markou', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Omar Delphi', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Mikhail Serrano', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Theo Nassar', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'protecting an accomplice', 'method': 'removed a safety stop', 'key': 'keypad code change record'}, 'supports': ['a contradicted alibi minute-by-minute', 'a staff roster with a late change', 'a suspicious purchase record', 'pollen trace matching a specific place', 'call history showing a short, repeated number', 'a photo edited, but not where people claim'], 'reds': ['a fake social media screenshot', 'a viral post with a cropped timestamp', 'a dramatic argument overheard earlier'], 'anchors': [('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.')]}, {'id': 'A24', 'title': 'A24 — Hollowbrook Wedding File', 'case_type': 'murder', 'setting': 'a wedding venue kitchen', 'victim_role': 'the best man', 'hook': 'A small detail doesn’t match the rest. That’s the crack you start with.', 'victim_name': 'Jamie Delphi', 'date': 'March 14, 2025', 'weather': 'humid night air', 'smell': 'ozone and damp paper', 'suspects': [{'name': 'Omar Arden', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Mara Delphi', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Elias Kerr', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Yara Delphi', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 0, 'motive': 'avoiding exposure', 'method': 'covert recording + smear', 'key': 'badge access anomaly'}, 'supports': ["a door that was 'locked' but not latched", 'a staff roster with a late change', 'a missing entry in the visitor log', 'pollen trace matching a specific place', 'an object moved against habit', 'a witness who changes wording under pressure'], 'reds': ["a partial fingerprint that doesn't match anyone here", 'a rumor about secret debts', 'a dramatic argument overheard earlier'], 'anchors': [('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.')]}, {'id': 'A25', 'title': 'A25 — Quiet Interview Radio Shadow', 'case_type': 'political', 'setting': 'a radio station control booth', 'victim_role': 'a host', 'hook': 'A clean story is offered immediately. Your job is to find what it avoids.', 'victim_name': 'Avery Delphi', 'date': 'March 17, 2025', 'weather': 'sharp winter cold', 'smell': 'salt and engine oil', 'suspects': [{'name': 'Yara Okoye', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Lucas Lavoie', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Maya Rowan', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Ivo Sato', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'coercion and control', 'method': 'loosened railing bolts', 'key': 'metadata timestamp mismatch'}, 'supports': ['a printed document with a subtle formatting difference', 'pollen trace matching a specific place', 'a staff roster with a late change', 'a photo edited, but not where people claim', 'a delivery receipt with a serial gap', 'a suspicious purchase record'], 'reds': ["a witness who 'remembers' after being prompted", 'a fake social media screenshot', 'a misread CCTV reflection'], 'anchors': [('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement.")]}, {'id': 'A26', 'title': 'A26 — Citrine Audit Memo', 'case_type': 'murder', 'setting': 'a corporate audit room', 'victim_role': 'an auditor', 'hook': 'A complaint is filed, and the timeline is the weapon.', 'victim_name': 'Drew Hwang', 'date': 'March 20, 2025', 'weather': 'heavy coastal mist', 'smell': 'perfume over disinfectant', 'suspects': [{'name': 'Rami Pappas', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Hana Tanaka', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Kostas Kane', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Aris Lavoie', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'insurance payout', 'method': 'stole draft + staged a break-in', 'key': 'soil/pollen trace'}, 'supports': ['an object moved against habit', 'a printed document with a subtle formatting difference', 'a witness who changes wording under pressure', 'a message thread with deleted lines', 'a delivery receipt with a serial gap', 'an access attempt minutes before the reported time'], 'reds': ['a rumor about secret debts', 'a misread CCTV reflection', 'a fake social media screenshot'], 'anchors': [('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.')]}, {'id': 'A27', 'title': 'A27 — After Hours Library Signal', 'case_type': 'political', 'setting': 'a university library stacks', 'victim_role': 'a night guard', 'hook': 'A perfect alibi depends on one assumption you can test.', 'victim_name': 'Jordan Kane', 'date': 'March 23, 2025', 'weather': 'late-summer heat', 'smell': 'old books and varnish', 'suspects': [{'name': 'Dana Vallis', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Nadia Volkov', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Nadia Kane', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Kostas Lavoie', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 0, 'motive': 'revenge for a past betrayal', 'method': 'coercion and intimidation', 'key': 'call detail record'}, 'supports': ['a delivery receipt with a serial gap', 'a maintenance schedule that was quietly edited', 'a missing entry in the visitor log', 'an access attempt minutes before the reported time', 'a timeline that depends on the wrong clock', 'a contradicted alibi minute-by-minute'], 'reds': ["a partial fingerprint that doesn't match anyone here", 'a rumor about secret debts', 'a suspicious-looking stranger nearby'], 'anchors': [('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.')]}, {'id': 'A28', 'title': 'A28 — Kestrel Park Park Ledger', 'case_type': 'sexual_assault', 'setting': 'a public park trail', 'victim_role': 'a jogger', 'hook': 'A complaint is filed, and the timeline is the weapon.', 'victim_name': 'Jamie Roux', 'date': 'March 26, 2025', 'weather': 'electric storm air', 'smell': 'citrus cleaner', 'suspects': [{'name': 'Selene Santos', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Noah Hale', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Samira Santos', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Kostas Kline', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 0, 'motive': 'jealousy over a secret relationship', 'method': 'forged resignation + shredding', 'key': 'receipt serial gap'}, 'supports': ['a staff roster with a late change', 'a suspicious purchase record', 'a timeline that depends on the wrong clock', 'a witness who changes wording under pressure', 'a small scratch pattern consistent with a hurried tool', 'a contradicted alibi minute-by-minute'], 'reds': ['a fake social media screenshot', "a witness who 'remembers' after being prompted", "a partial fingerprint that doesn't match anyone here"], 'anchors': [('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.')]}, {'id': 'A29', 'title': 'A29 — Snowbound Bus Ledger', 'case_type': 'murder', 'setting': 'a stranded coach bus', 'victim_role': 'a tour guide', 'hook': 'A perfect alibi depends on one assumption you can test.', 'victim_name': 'Sam Bennett', 'date': 'March 29, 2025', 'weather': 'cold drizzle', 'smell': 'bleach and metal', 'suspects': [{'name': 'Talia Nassar', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Yara Haddad', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Kostas Rowan', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Iris Hart', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'to stop a blackmail payoff', 'method': 'poison slipped into a drink', 'key': 'elevator panel smear pattern'}, 'supports': ['a timeline that depends on the wrong clock', 'a quiet payment made in an odd amount', 'a second copy of a report with one word changed', 'a photo edited, but not where people claim', 'a printed document with a subtle formatting difference', 'a message thread with deleted lines'], 'reds': ['an old threat letter with no date', 'a rumor about secret debts', 'a fake social media screenshot'], 'anchors': [('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.')]}, {'id': 'A30', 'title': 'A30 — Elm Law Office Memo', 'case_type': 'political', 'setting': 'a legal office conference room', 'victim_role': 'a paralegal', 'hook': 'A missing object matters more than the object itself.', 'victim_name': 'Drew Lennox', 'date': 'April 01, 2025', 'weather': 'dry wind', 'smell': 'coffee and dust', 'suspects': [{'name': 'Nadia Serrano', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Priya Kerr', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Hana Markou', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Samira Kane', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'to bury a donor list', 'method': 'staged accident', 'key': 'tamper seal mismatch'}, 'supports': ['an object moved against habit', 'a missing entry in the visitor log', 'a handwritten note with familiar pressure pattern', 'pollen trace matching a specific place', 'a second copy of a report with one word changed', 'a photo edited, but not where people claim'], 'reds': ['a misread CCTV reflection', 'a key that belongs to somewhere else', 'a misleading anonymous tip email'], 'anchors': [('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.')]}, {'id': 'A31', 'title': 'A31 — Jet Manifest Airport Signal', 'case_type': 'murder', 'setting': 'a small airport hangar', 'victim_role': 'a lobbyist', 'hook': 'A perfect alibi depends on one assumption you can test.', 'victim_name': 'Jordan Novak', 'date': 'April 04, 2025', 'weather': 'humid night air', 'smell': 'ozone and damp paper', 'suspects': [{'name': 'Aris Serrano', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Elena Nielsen', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Rami Santos', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Kostas Markou', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'predation + silencing', 'method': 'tampered equipment', 'key': 'fresh wrench marks'}, 'supports': ['a handwritten note with familiar pressure pattern', 'a staff roster with a late change', 'an access attempt minutes before the reported time', 'a delivery receipt with a serial gap', 'a small scratch pattern consistent with a hurried tool', 'a photo edited, but not where people claim'], 'reds': ["a partial fingerprint that doesn't match anyone here", 'a suspicious-looking stranger nearby', 'a viral post with a cropped timestamp'], 'anchors': [('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.')]}, {'id': 'A32', 'title': 'A32 — Sunset Marina Marina Switch', 'case_type': 'political', 'setting': 'a marina pier at dusk', 'victim_role': 'a boat mechanic', 'hook': 'Everyone agrees on the headline, but nobody agrees on the minutes.', 'victim_name': 'Jordan Sato', 'date': 'April 07, 2025', 'weather': 'sharp winter cold', 'smell': 'salt and engine oil', 'suspects': [{'name': 'Samira Rowan', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Lea Nielsen', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Elena Vallis', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Theo Petros', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'embezzlement cover-up', 'method': 'edited logs', 'key': 'printer log timestamp'}, 'supports': ['a handwritten note with familiar pressure pattern', 'a maintenance schedule that was quietly edited', 'pollen trace matching a specific place', 'a timeline that depends on the wrong clock', 'a printed document with a subtle formatting difference', 'a message thread with deleted lines'], 'reds': ['a misread CCTV reflection', "a broken object that looks important but isn't", 'a fake social media screenshot'], 'anchors': [('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement.")]}, {'id': 'A33', 'title': 'A33 — Museum Donation Museum Signal', 'case_type': 'sexual_assault', 'setting': 'a city museum storage wing', 'victim_role': 'a curator', 'hook': 'A small detail doesn’t match the rest. That’s the crack you start with.', 'victim_name': 'Morgan Sato', 'date': 'April 10, 2025', 'weather': 'heavy coastal mist', 'smell': 'perfume over disinfectant', 'suspects': [{'name': 'Yara Wu', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Talia Markou', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Jon Wu', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Jon Kane', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'covering a financial fraud', 'method': 'misdirected delivery', 'key': 'door camera gap + keycard data'}, 'supports': ['a timeline that depends on the wrong clock', 'call history showing a short, repeated number', 'a printed document with a subtle formatting difference', 'a small scratch pattern consistent with a hurried tool', 'an access attempt minutes before the reported time', 'a maintenance schedule that was quietly edited'], 'reds': ["a witness who 'remembers' after being prompted", 'a dramatic argument overheard earlier', 'a fake social media screenshot'], 'anchors': [('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.')]}, {'id': 'A34', 'title': 'A34 — Aster Lane Apartment Incident', 'case_type': 'murder', 'setting': 'a dense apartment block lobby', 'victim_role': 'a tenant', 'hook': 'Everyone agrees on the headline, but nobody agrees on the minutes.', 'victim_name': 'Casey Bennett', 'date': 'April 13, 2025', 'weather': 'late-summer heat', 'smell': 'old books and varnish', 'suspects': [{'name': 'Sofia Nassar', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Hana Arden', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Talia Sato', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Mikhail Vallis', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'political leverage', 'method': 'swapped two identical folders', 'key': 'ink mismatch on signature'}, 'supports': ['a handwritten note with familiar pressure pattern', 'pollen trace matching a specific place', 'a witness who changes wording under pressure', 'a photo edited, but not where people claim', 'a message thread with deleted lines', "a door that was 'locked' but not latched"], 'reds': ['a key that belongs to somewhere else', "a partial fingerprint that doesn't match anyone here", 'a suspicious-looking stranger nearby'], 'anchors': [('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.')]}, {'id': 'A35', 'title': 'A35 — Night Shift Records Memo', 'case_type': 'political', 'setting': 'a police records office', 'victim_role': 'a clerk', 'hook': 'A statement arrives early, too polished to be spontaneous.', 'victim_name': 'Sam Petros', 'date': 'April 16, 2025', 'weather': 'electric storm air', 'smell': 'citrus cleaner', 'suspects': [{'name': 'Niko Pappas', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Jon Khan', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Niko Nielsen', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Kostas Nassar', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'silencing a witness', 'method': 'removed a safety stop', 'key': 'security log gap'}, 'supports': ['a maintenance schedule that was quietly edited', 'an object moved against habit', 'a message thread with deleted lines', 'a second copy of a report with one word changed', 'a missing entry in the visitor log', 'a delivery receipt with a serial gap'], 'reds': ['a rumor about secret debts', "a partial fingerprint that doesn't match anyone here", 'a key that belongs to somewhere else'], 'anchors': [('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.')]}, {'id': 'A36', 'title': 'A36 — Glasshouse Conservatory Night', 'case_type': 'murder', 'setting': 'a botanical conservatory', 'victim_role': 'a horticulturist', 'hook': 'A complaint is filed, and the timeline is the weapon.', 'victim_name': 'Drew Bennett', 'date': 'April 19, 2025', 'weather': 'cold drizzle', 'smell': 'bleach and metal', 'suspects': [{'name': 'Dana Vega', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Lea Hart', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Alex Okoye', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Selene Nielsen', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'career sabotage', 'method': 'covert recording + smear', 'key': 'CCTV angle blind spot'}, 'supports': ['a quiet payment made in an odd amount', 'a staff roster with a late change', 'a contradicted alibi minute-by-minute', 'a message thread with deleted lines', 'an access attempt minutes before the reported time', 'an object moved against habit'], 'reds': ['a fake social media screenshot', "a broken object that looks important but isn't", 'a suspicious-looking stranger nearby'], 'anchors': [('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.')]}, {'id': 'A37', 'title': 'A37 — Keypad Therapy Pattern', 'case_type': 'political', 'setting': 'a therapy clinic hallway', 'victim_role': 'a patient', 'hook': 'The scene looks ordinary until you check what should have been impossible.', 'victim_name': 'Casey Novak', 'date': 'April 22, 2025', 'weather': 'dry wind', 'smell': 'coffee and dust', 'suspects': [{'name': 'Theo Yilmaz', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Hana Hale', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Samira Petros', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Alex Nassar', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'protecting an accomplice', 'method': 'loosened railing bolts', 'key': 'tool mark evidence'}, 'supports': ['a staff roster with a late change', 'a contradicted alibi minute-by-minute', 'a maintenance schedule that was quietly edited', 'an access attempt minutes before the reported time', 'a quiet payment made in an odd amount', 'call history showing a short, repeated number'], 'reds': ['a key that belongs to somewhere else', 'a fake social media screenshot', 'an old threat letter with no date'], 'anchors': [('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.')]}, {'id': 'A38', 'title': 'A38 — Rook & Crown Casino File', 'case_type': 'sexual_assault', 'setting': 'a small casino pit', 'victim_role': 'a pit boss', 'hook': 'A small detail doesn’t match the rest. That’s the crack you start with.', 'victim_name': 'Jamie Lennox', 'date': 'April 25, 2025', 'weather': 'humid night air', 'smell': 'ozone and damp paper', 'suspects': [{'name': 'Theo Pappas', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Maya Haddad', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Theo Arden', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Aris Khan', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'avoiding exposure', 'method': 'stole draft + staged a break-in', 'key': 'keypad code change record'}, 'supports': ['a missing entry in the visitor log', 'a witness who changes wording under pressure', 'a timeline that depends on the wrong clock', 'a handwritten note with familiar pressure pattern', 'a printed document with a subtle formatting difference', 'an access attempt minutes before the reported time'], 'reds': ['a rumor about secret debts', 'a key that belongs to somewhere else', "a witness who 'remembers' after being prompted"], 'anchors': [('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.')]}, {'id': 'A39', 'title': 'A39 — Election Van Campaign Incident', 'case_type': 'murder', 'setting': 'a campaign headquarters', 'victim_role': 'a field organizer', 'hook': 'A missing object matters more than the object itself.', 'victim_name': 'Morgan Roux', 'date': 'April 28, 2025', 'weather': 'sharp winter cold', 'smell': 'salt and engine oil', 'suspects': [{'name': 'Lucas Arden', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Maya Tanaka', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Jon Petros', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Priya Wu', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'coercion and control', 'method': 'coercion and intimidation', 'key': 'badge access anomaly'}, 'supports': ['a delivery receipt with a serial gap', 'a staff roster with a late change', 'a printed document with a subtle formatting difference', 'a witness who changes wording under pressure', 'an object moved against habit', 'a second copy of a report with one word changed'], 'reds': ['an old threat letter with no date', 'a misleading anonymous tip email', "a witness who 'remembers' after being prompted"], 'anchors': [('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement.")]}, {'id': 'A40', 'title': 'A40 — Bitter Coffee Cafe Signal', 'case_type': 'political', 'setting': 'a cafe service counter', 'victim_role': 'a food critic', 'hook': 'Everyone agrees on the headline, but nobody agrees on the minutes.', 'victim_name': 'Avery Hwang', 'date': 'May 01, 2025', 'weather': 'heavy coastal mist', 'smell': 'perfume over disinfectant', 'suspects': [{'name': 'Kostas Kerr', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Rami Lavoie', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Nadia Lavoie', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Talia Haddad', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'insurance payout', 'method': 'forged resignation + shredding', 'key': 'metadata timestamp mismatch'}, 'supports': ['a witness who changes wording under pressure', 'a timeline that depends on the wrong clock', 'a photo edited, but not where people claim', 'an object moved against habit', 'a delivery receipt with a serial gap', 'a message thread with deleted lines'], 'reds': ["a witness who 'remembers' after being prompted", 'a fake social media screenshot', 'a suspicious-looking stranger nearby'], 'anchors': [('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.')]}, {'id': 'A41', 'title': 'A41 — Rivergate Balcony Shadow', 'case_type': 'murder', 'setting': 'a high-rise overlooking a canal', 'victim_role': 'a property developer', 'hook': 'A perfect alibi depends on one assumption you can test.', 'victim_name': 'Drew Bennett', 'date': 'May 04, 2025', 'weather': 'late-summer heat', 'smell': 'old books and varnish', 'suspects': [{'name': 'Lucas Kerr', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Talia Khan', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Selene Sato', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Elias Tanaka', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'revenge for a past betrayal', 'method': 'poison slipped into a drink', 'key': 'soil/pollen trace'}, 'supports': ['a small scratch pattern consistent with a hurried tool', 'a missing entry in the visitor log', 'call history showing a short, repeated number', 'a witness who changes wording under pressure', 'a photo edited, but not where people claim', 'an object moved against habit'], 'reds': ['an old threat letter with no date', 'a suspicious-looking stranger nearby', 'a misread CCTV reflection'], 'anchors': [('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.')]}, {'id': 'A42', 'title': 'A42 — Cold Ink Newsroom Memo 42', 'case_type': 'political', 'setting': 'an independent newspaper office', 'victim_role': 'an investigative editor', 'hook': 'The scene looks ordinary until you check what should have been impossible.', 'victim_name': 'Quinn Arden', 'date': 'May 07, 2025', 'weather': 'electric storm air', 'smell': 'citrus cleaner', 'suspects': [{'name': 'Mikhail Yilmaz', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Jon Serrano', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Priya Nielsen', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Alex Novak', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'jealousy over a secret relationship', 'method': 'staged accident', 'key': 'call detail record'}, 'supports': ['a second copy of a report with one word changed', 'an access attempt minutes before the reported time', "a door that was 'locked' but not latched", 'call history showing a short, repeated number', 'a quiet payment made in an odd amount', 'a staff roster with a late change'], 'reds': ['a misread CCTV reflection', 'a viral post with a cropped timestamp', 'a suspicious-looking stranger nearby'], 'anchors': [('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.')]}, {'id': 'A43', 'title': 'A43 — Silk Road Motel Memo', 'case_type': 'sexual_assault', 'setting': 'a roadside motel off a dim highway', 'victim_role': 'a traveling musician', 'hook': 'The scene looks ordinary until you check what should have been impossible.', 'victim_name': 'Avery Kerr', 'date': 'May 10, 2025', 'weather': 'cold drizzle', 'smell': 'bleach and metal', 'suspects': [{'name': 'Kostas Volkov', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Theo Haddad', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Lea Kerr', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Iris Nielsen', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'to stop a blackmail payoff', 'method': 'tampered equipment', 'key': 'receipt serial gap'}, 'supports': ['a delivery receipt with a serial gap', 'an access attempt minutes before the reported time', 'a staff roster with a late change', 'a contradicted alibi minute-by-minute', 'a timeline that depends on the wrong clock', 'a second copy of a report with one word changed'], 'reds': ['a misread CCTV reflection', 'a suspicious-looking stranger nearby', "a broken object that looks important but isn't"], 'anchors': [('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.')]}, {'id': 'A44', 'title': 'A44 — Vanished Ledger Office Night', 'case_type': 'murder', 'setting': 'a municipal finance office', 'victim_role': 'a whistleblower accountant', 'hook': 'A missing object matters more than the object itself.', 'victim_name': 'Casey Hart', 'date': 'May 13, 2025', 'weather': 'dry wind', 'smell': 'coffee and dust', 'suspects': [{'name': 'Kostas Tanaka', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Nadia Novak', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Niko Delphi', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Lea Tanaka', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'to bury a donor list', 'method': 'edited logs', 'key': 'elevator panel smear pattern'}, 'supports': ['an access attempt minutes before the reported time', 'a staff roster with a late change', 'a timeline that depends on the wrong clock', 'a contradicted alibi minute-by-minute', 'call history showing a short, repeated number', 'a witness who changes wording under pressure'], 'reds': ['a misread CCTV reflection', 'an old threat letter with no date', 'a rumor about secret debts'], 'anchors': [('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.')]}, {'id': 'A45', 'title': 'A45 — Midnight Docks Ledger', 'case_type': 'political', 'setting': 'a container terminal at night', 'victim_role': 'a customs broker', 'hook': 'The scene looks ordinary until you check what should have been impossible.', 'victim_name': 'Taylor Petros', 'date': 'May 16, 2025', 'weather': 'humid night air', 'smell': 'ozone and damp paper', 'suspects': [{'name': 'Niko Rossi', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Aris Vallis', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Yara Nielsen', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Omar Lavoie', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'predation + silencing', 'method': 'misdirected delivery', 'key': 'tamper seal mismatch'}, 'supports': ['pollen trace matching a specific place', "a door that was 'locked' but not latched", 'a message thread with deleted lines', 'a small scratch pattern consistent with a hurried tool', 'a missing entry in the visitor log', 'a contradicted alibi minute-by-minute'], 'reds': ['a misread CCTV reflection', "a partial fingerprint that doesn't match anyone here", 'a misleading anonymous tip email'], 'anchors': [('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.')]}, {'id': 'A46', 'title': 'A46 — Opera Opera House Night', 'case_type': 'murder', 'setting': 'a restored opera house backstage', 'victim_role': 'a cultural minister', 'hook': 'A small detail doesn’t match the rest. That’s the crack you start with.', 'victim_name': 'Sam Arden', 'date': 'May 19, 2025', 'weather': 'sharp winter cold', 'smell': 'salt and engine oil', 'suspects': [{'name': 'Lucas Wu', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Nadia Kerr', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Rami Hart', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Rami Kerr', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'embezzlement cover-up', 'method': 'swapped two identical folders', 'key': 'fresh wrench marks'}, 'supports': ['a second copy of a report with one word changed', 'a quiet payment made in an odd amount', 'a staff roster with a late change', 'a delivery receipt with a serial gap', 'a timeline that depends on the wrong clock', 'a missing entry in the visitor log'], 'reds': ['a fake social media screenshot', 'an old threat letter with no date', 'a rumor about secret debts'], 'anchors': [('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement.")]}, {'id': 'A47', 'title': 'A47 — Pinecrest Cabin Switch', 'case_type': 'political', 'setting': 'a forest cabin community', 'victim_role': 'a retired firefighter', 'hook': 'A complaint is filed, and the timeline is the weapon.', 'victim_name': 'Jamie Arden', 'date': 'May 22, 2025', 'weather': 'heavy coastal mist', 'smell': 'perfume over disinfectant', 'suspects': [{'name': 'Sofia Vega', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Nadia Arden', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Jon Sato', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Omar Pappas', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 0, 'motive': 'covering a financial fraud', 'method': 'removed a safety stop', 'key': 'printer log timestamp'}, 'supports': ['a timeline that depends on the wrong clock', 'a suspicious purchase record', 'a delivery receipt with a serial gap', 'a small scratch pattern consistent with a hurried tool', 'call history showing a short, repeated number', 'an access attempt minutes before the reported time'], 'reds': ['a misread CCTV reflection', "a partial fingerprint that doesn't match anyone here", "a broken object that looks important but isn't"], 'anchors': [('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.')]}, {'id': 'A48', 'title': 'A48 — Clinic Clinic Memo', 'case_type': 'sexual_assault', 'setting': 'a private clinic reception area', 'victim_role': 'a graduate student', 'hook': 'The scene looks ordinary until you check what should have been impossible.', 'victim_name': 'Riley Petros', 'date': 'May 25, 2025', 'weather': 'late-summer heat', 'smell': 'old books and varnish', 'suspects': [{'name': 'Samira Nielsen', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Theo Sato', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Noah Nassar', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Aris Rowan', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'political leverage', 'method': 'covert recording + smear', 'key': 'door camera gap + keycard data'}, 'supports': ['a witness who changes wording under pressure', 'a missing entry in the visitor log', 'call history showing a short, repeated number', 'a message thread with deleted lines', 'a staff roster with a late change', 'a small scratch pattern consistent with a hurried tool'], 'reds': ["a broken object that looks important but isn't", 'a suspicious-looking stranger nearby', 'a key that belongs to somewhere else'], 'anchors': [('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.')]}, {'id': 'A49', 'title': 'A49 — Split Vote Council Signal', 'case_type': 'murder', 'setting': 'a city council chamber', 'victim_role': 'a council aide', 'hook': 'A missing object matters more than the object itself.', 'victim_name': 'Casey Bennett', 'date': 'May 28, 2025', 'weather': 'electric storm air', 'smell': 'citrus cleaner', 'suspects': [{'name': 'Dimitri Vega', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Hana Khan', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Mara Hale', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Mikhail Pappas', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'silencing a witness', 'method': 'loosened railing bolts', 'key': 'ink mismatch on signature'}, 'supports': ['a staff roster with a late change', 'a timeline that depends on the wrong clock', 'a quiet payment made in an odd amount', 'an access attempt minutes before the reported time', 'a witness who changes wording under pressure', 'a handwritten note with familiar pressure pattern'], 'reds': ["a broken object that looks important but isn't", "a partial fingerprint that doesn't match anyone here", 'an old threat letter with no date'], 'anchors': [('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.')]}, {'id': 'A50', 'title': 'A50 — Blue Velvet Gallery Switch', 'case_type': 'political', 'setting': 'a modern art gallery', 'victim_role': 'an art patron', 'hook': 'The scene looks ordinary until you check what should have been impossible.', 'victim_name': 'Taylor Roux', 'date': 'May 31, 2025', 'weather': 'cold drizzle', 'smell': 'bleach and metal', 'suspects': [{'name': 'Alex Baird', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Mina Nassar', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Lea Serrano', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Iris Kline', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'career sabotage', 'method': 'stole draft + staged a break-in', 'key': 'security log gap'}, 'supports': ['a small scratch pattern consistent with a hurried tool', 'a contradicted alibi minute-by-minute', 'a photo edited, but not where people claim', 'a staff roster with a late change', 'a printed document with a subtle formatting difference', 'pollen trace matching a specific place'], 'reds': ["a partial fingerprint that doesn't match anyone here", 'an old threat letter with no date', 'a key that belongs to somewhere else'], 'anchors': [('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.')]}, {'id': 'A51', 'title': 'A51 — Harborline Train Incident', 'case_type': 'murder', 'setting': 'a commuter train mid-route', 'victim_role': 'a logistics manager', 'hook': 'Everyone agrees on the headline, but nobody agrees on the minutes.', 'victim_name': 'Drew Petros', 'date': 'June 03, 2025', 'weather': 'dry wind', 'smell': 'coffee and dust', 'suspects': [{'name': 'Sofia Yilmaz', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Lea Rowan', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Jules Wu', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Iris Kane', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'protecting an accomplice', 'method': 'coercion and intimidation', 'key': 'CCTV angle blind spot'}, 'supports': ['a missing entry in the visitor log', 'a suspicious purchase record', 'a timeline that depends on the wrong clock', 'a contradicted alibi minute-by-minute', 'a printed document with a subtle formatting difference', "a door that was 'locked' but not latched"], 'reds': ['a misread CCTV reflection', "a witness who 'remembers' after being prompted", 'a viral post with a cropped timestamp'], 'anchors': [('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.')]}, {'id': 'A52', 'title': 'A52 — Charity Banquet File', 'case_type': 'political', 'setting': 'a charity banquet hall', 'victim_role': 'a fundraiser', 'hook': 'A clean story is offered immediately. Your job is to find what it avoids.', 'victim_name': 'Quinn Lennox', 'date': 'June 06, 2025', 'weather': 'humid night air', 'smell': 'ozone and damp paper', 'suspects': [{'name': 'Jules Lavoie', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Aris Baird', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Nadia Santos', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Noah Rowan', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'avoiding exposure', 'method': 'forged resignation + shredding', 'key': 'tool mark evidence'}, 'supports': ['a contradicted alibi minute-by-minute', 'a suspicious purchase record', 'a small scratch pattern consistent with a hurried tool', 'a delivery receipt with a serial gap', 'call history showing a short, repeated number', 'a photo edited, but not where people claim'], 'reds': ['an old threat letter with no date', 'a fake social media screenshot', "a witness who 'remembers' after being prompted"], 'anchors': [('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.')]}, {'id': 'A53', 'title': 'A53 — Saffron Alley Signal 53', 'case_type': 'sexual_assault', 'setting': 'a nightlife district alley', 'victim_role': 'a bartender', 'hook': 'A missing object matters more than the object itself.', 'victim_name': 'Drew Arden', 'date': 'June 09, 2025', 'weather': 'sharp winter cold', 'smell': 'salt and engine oil', 'suspects': [{'name': 'Selene Haddad', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Sofia Lavoie', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Mikhail Santos', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Dana Rowan', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'coercion and control', 'method': 'poison slipped into a drink', 'key': 'keypad code change record'}, 'supports': ['a second copy of a report with one word changed', 'a missing entry in the visitor log', "a door that was 'locked' but not latched", 'call history showing a short, repeated number', 'pollen trace matching a specific place', 'a witness who changes wording under pressure'], 'reds': ['a dramatic argument overheard earlier', 'a viral post with a cropped timestamp', 'a key that belongs to somewhere else'], 'anchors': [('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement.")]}, {'id': 'A54', 'title': 'A54 — Campus Boardroom Ledger', 'case_type': 'murder', 'setting': 'a university boardroom', 'victim_role': 'a dean', 'hook': 'A missing object matters more than the object itself.', 'victim_name': 'Avery Kane', 'date': 'June 12, 2025', 'weather': 'heavy coastal mist', 'smell': 'perfume over disinfectant', 'suspects': [{'name': 'Elena Sato', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Kostas Baird', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Hana Vallis', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Maya Hart', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 0, 'motive': 'insurance payout', 'method': 'staged accident', 'key': 'badge access anomaly'}, 'supports': ['a quiet payment made in an odd amount', 'a missing entry in the visitor log', 'a message thread with deleted lines', 'a maintenance schedule that was quietly edited', 'a handwritten note with familiar pressure pattern', 'a staff roster with a late change'], 'reds': ['an old threat letter with no date', 'a fake social media screenshot', 'a suspicious-looking stranger nearby'], 'anchors': [('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.')]}, {'id': 'A55', 'title': 'A55 — Windswept Lighthouse Incident', 'case_type': 'political', 'setting': 'a coastal lighthouse stairwell', 'victim_role': 'a marine biologist', 'hook': 'A statement arrives early, too polished to be spontaneous.', 'victim_name': 'Jamie Petros', 'date': 'June 15, 2025', 'weather': 'late-summer heat', 'smell': 'old books and varnish', 'suspects': [{'name': 'Priya Haddad', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Talia Hart', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Elias Petros', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Noah Kline', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'revenge for a past betrayal', 'method': 'tampered equipment', 'key': 'metadata timestamp mismatch'}, 'supports': ['a quiet payment made in an odd amount', 'a contradicted alibi minute-by-minute', "a door that was 'locked' but not latched", 'a witness who changes wording under pressure', 'a printed document with a subtle formatting difference', 'a missing entry in the visitor log'], 'reds': ['a viral post with a cropped timestamp', 'an old threat letter with no date', "a witness who 'remembers' after being prompted"], 'anchors': [('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.')]}, {'id': 'A56', 'title': 'A56 — Backroom Contract Shadow', 'case_type': 'murder', 'setting': 'a construction office backroom', 'victim_role': 'a procurement officer', 'hook': 'Everyone agrees on the headline, but nobody agrees on the minutes.', 'victim_name': 'Riley Novak', 'date': 'June 18, 2025', 'weather': 'electric storm air', 'smell': 'citrus cleaner', 'suspects': [{'name': 'Hana Santos', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Niko Baird', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Noah Serrano', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Mara Serrano', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'jealousy over a secret relationship', 'method': 'edited logs', 'key': 'soil/pollen trace'}, 'supports': ['a second copy of a report with one word changed', 'a staff roster with a late change', "a door that was 'locked' but not latched", 'a delivery receipt with a serial gap', 'a suspicious purchase record', 'a missing entry in the visitor log'], 'reds': ['a viral post with a cropped timestamp', 'a key that belongs to somewhere else', 'a suspicious-looking stranger nearby'], 'anchors': [('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.')]}, {'id': 'A57', 'title': 'A57 — Alleyway Statement Case', 'case_type': 'political', 'setting': 'a crowded festival zone', 'victim_role': 'a volunteer', 'hook': 'A missing object matters more than the object itself.', 'victim_name': 'Quinn Kerr', 'date': 'June 21, 2025', 'weather': 'cold drizzle', 'smell': 'bleach and metal', 'suspects': [{'name': 'Hana Yilmaz', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Dana Nassar', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Noah Ibrahim', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Iris Petros', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'to stop a blackmail payoff', 'method': 'misdirected delivery', 'key': 'call detail record'}, 'supports': ['a delivery receipt with a serial gap', 'a witness who changes wording under pressure', 'a maintenance schedule that was quietly edited', 'a handwritten note with familiar pressure pattern', 'a staff roster with a late change', 'a timeline that depends on the wrong clock'], 'reds': ['a dramatic argument overheard earlier', "a partial fingerprint that doesn't match anyone here", 'a misread CCTV reflection'], 'anchors': [('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.')]}, {'id': 'A58', 'title': 'A58 — Quartz Hill Pharmacy Night', 'case_type': 'sexual_assault', 'setting': 'a late-night pharmacy', 'victim_role': 'a pharmacist', 'hook': 'A perfect alibi depends on one assumption you can test.', 'victim_name': 'Riley Hart', 'date': 'June 24, 2025', 'weather': 'dry wind', 'smell': 'coffee and dust', 'suspects': [{'name': 'Aris Volkov', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Sofia Vallis', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Niko Okoye', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Selene Serrano', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'to bury a donor list', 'method': 'swapped two identical folders', 'key': 'receipt serial gap'}, 'supports': ['a small scratch pattern consistent with a hurried tool', 'a second copy of a report with one word changed', 'a witness who changes wording under pressure', 'a quiet payment made in an odd amount', 'a message thread with deleted lines', 'call history showing a short, repeated number'], 'reds': ['a rumor about secret debts', "a partial fingerprint that doesn't match anyone here", 'a misleading anonymous tip email'], 'anchors': [('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.')]}, {'id': 'A59', 'title': 'A59 — Redacted Email Shadow', 'case_type': 'murder', 'setting': 'a ministerial IT department', 'victim_role': 'a sysadmin', 'hook': 'A clean story is offered immediately. Your job is to find what it avoids.', 'victim_name': 'Jordan Hwang', 'date': 'June 27, 2025', 'weather': 'humid night air', 'smell': 'ozone and damp paper', 'suspects': [{'name': 'Kostas Yilmaz', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Jules Serrano', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Kostas Okoye', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Omar Rowan', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'predation + silencing', 'method': 'removed a safety stop', 'key': 'elevator panel smear pattern'}, 'supports': ["a door that was 'locked' but not latched", 'an access attempt minutes before the reported time', 'a second copy of a report with one word changed', 'a quiet payment made in an odd amount', 'pollen trace matching a specific place', 'call history showing a short, repeated number'], 'reds': ['an old threat letter with no date', "a partial fingerprint that doesn't match anyone here", 'a misleading anonymous tip email'], 'anchors': [('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.')]}, {'id': 'A60', 'title': 'A60 — Orchard Estate Switch', 'case_type': 'political', 'setting': 'a countryside estate lodge', 'victim_role': 'a family heir', 'hook': 'A missing object matters more than the object itself.', 'victim_name': 'Jordan Hart', 'date': 'June 30, 2025', 'weather': 'sharp winter cold', 'smell': 'salt and engine oil', 'suspects': [{'name': 'Niko Hale', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Theo Hale', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Selene Rowan', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Niko Kline', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'embezzlement cover-up', 'method': 'covert recording + smear', 'key': 'tamper seal mismatch'}, 'supports': ['a quiet payment made in an odd amount', 'a handwritten note with familiar pressure pattern', 'a small scratch pattern consistent with a hurried tool', 'a photo edited, but not where people claim', "a door that was 'locked' but not latched", 'a second copy of a report with one word changed'], 'reds': ['a dramatic argument overheard earlier', 'a fake social media screenshot', 'a rumor about secret debts'], 'anchors': [('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement.")]}, {'id': 'A61', 'title': 'A61 — Embassy Briefcase Night', 'case_type': 'murder', 'setting': 'an embassy reception corridor', 'victim_role': 'a diplomat', 'hook': 'A clean story is offered immediately. Your job is to find what it avoids.', 'victim_name': 'Avery Kerr', 'date': 'July 03, 2025', 'weather': 'heavy coastal mist', 'smell': 'perfume over disinfectant', 'suspects': [{'name': 'Dimitri Petros', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Lucas Kane', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Nadia Nassar', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Mikhail Baird', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'covering a financial fraud', 'method': 'loosened railing bolts', 'key': 'fresh wrench marks'}, 'supports': ['a small scratch pattern consistent with a hurried tool', 'a missing entry in the visitor log', 'call history showing a short, repeated number', 'a suspicious purchase record', 'a timeline that depends on the wrong clock', 'pollen trace matching a specific place'], 'reds': ['a key that belongs to somewhere else', 'a dramatic argument overheard earlier', 'an old threat letter with no date'], 'anchors': [('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.')]}, {'id': 'A62', 'title': 'A62 — Seabed Grant Pattern', 'case_type': 'political', 'setting': 'a research institute wing', 'victim_role': 'a grant reviewer', 'hook': 'The scene looks ordinary until you check what should have been impossible.', 'victim_name': 'Morgan Petros', 'date': 'July 06, 2025', 'weather': 'late-summer heat', 'smell': 'old books and varnish', 'suspects': [{'name': 'Dana Wu', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Lea Arden', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Kostas Hale', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Mikhail Wu', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'political leverage', 'method': 'stole draft + staged a break-in', 'key': 'printer log timestamp'}, 'supports': ['a photo edited, but not where people claim', 'an access attempt minutes before the reported time', 'a quiet payment made in an odd amount', 'a maintenance schedule that was quietly edited', 'a timeline that depends on the wrong clock', 'an object moved against habit'], 'reds': ['a misread CCTV reflection', 'a fake social media screenshot', "a witness who 'remembers' after being prompted"], 'anchors': [('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.')]}, {'id': 'A63', 'title': 'A63 — Neon Arcade Signal', 'case_type': 'sexual_assault', 'setting': 'a retro arcade floor', 'victim_role': 'an e-sports coach', 'hook': 'A clean story is offered immediately. Your job is to find what it avoids.', 'victim_name': 'Sam Arden', 'date': 'July 09, 2025', 'weather': 'electric storm air', 'smell': 'citrus cleaner', 'suspects': [{'name': 'Iris Nassar', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Sofia Pappas', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Mara Baird', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Lucas Rossi', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 0, 'motive': 'silencing a witness', 'method': 'coercion and intimidation', 'key': 'door camera gap + keycard data'}, 'supports': ['an object moved against habit', 'a delivery receipt with a serial gap', 'a maintenance schedule that was quietly edited', 'a staff roster with a late change', 'a quiet payment made in an odd amount', 'call history showing a short, repeated number'], 'reds': ['a fake social media screenshot', 'an old threat letter with no date', 'a rumor about secret debts'], 'anchors': [('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.')]}, {'id': 'A64', 'title': 'A64 — Hollowbrook Wedding Switch', 'case_type': 'murder', 'setting': 'a wedding venue kitchen', 'victim_role': 'the best man', 'hook': 'A statement arrives early, too polished to be spontaneous.', 'victim_name': 'Quinn Arden', 'date': 'July 12, 2025', 'weather': 'cold drizzle', 'smell': 'bleach and metal', 'suspects': [{'name': 'Alex Haddad', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Theo Delphi', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Mina Petros', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Alex Kerr', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'career sabotage', 'method': 'forged resignation + shredding', 'key': 'ink mismatch on signature'}, 'supports': ['a maintenance schedule that was quietly edited', "a door that was 'locked' but not latched", 'pollen trace matching a specific place', 'a witness who changes wording under pressure', 'an object moved against habit', 'a staff roster with a late change'], 'reds': ['a misleading anonymous tip email', 'a key that belongs to somewhere else', 'a fake social media screenshot'], 'anchors': [('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.')]}, {'id': 'A65', 'title': 'A65 — Quiet Interview Radio Pattern', 'case_type': 'political', 'setting': 'a radio station control booth', 'victim_role': 'a host', 'hook': 'A perfect alibi depends on one assumption you can test.', 'victim_name': 'Sam Delphi', 'date': 'July 15, 2025', 'weather': 'dry wind', 'smell': 'coffee and dust', 'suspects': [{'name': 'Sofia Ibrahim', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Omar Wu', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Mina Rowan', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Lea Volkov', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'protecting an accomplice', 'method': 'poison slipped into a drink', 'key': 'security log gap'}, 'supports': ['an access attempt minutes before the reported time', 'call history showing a short, repeated number', 'a small scratch pattern consistent with a hurried tool', 'a suspicious purchase record', 'a second copy of a report with one word changed', 'a maintenance schedule that was quietly edited'], 'reds': ['a viral post with a cropped timestamp', 'a fake social media screenshot', 'a misread CCTV reflection'], 'anchors': [('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.')]}, {'id': 'A66', 'title': 'A66 — Citrine Audit Ledger', 'case_type': 'murder', 'setting': 'a corporate audit room', 'victim_role': 'an auditor', 'hook': 'A small detail doesn’t match the rest. That’s the crack you start with.', 'victim_name': 'Jamie Lennox', 'date': 'July 18, 2025', 'weather': 'humid night air', 'smell': 'ozone and damp paper', 'suspects': [{'name': 'Niko Arden', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Dimitri Yilmaz', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Talia Delphi', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Mara Ibrahim', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 0, 'motive': 'avoiding exposure', 'method': 'staged accident', 'key': 'CCTV angle blind spot'}, 'supports': ['a missing entry in the visitor log', 'an object moved against habit', 'a delivery receipt with a serial gap', 'a staff roster with a late change', 'an access attempt minutes before the reported time', 'a handwritten note with familiar pressure pattern'], 'reds': ['a key that belongs to somewhere else', 'a fake social media screenshot', 'a rumor about secret debts'], 'anchors': [('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.')]}, {'id': 'A67', 'title': 'A67 — After Hours Library Shadow', 'case_type': 'political', 'setting': 'a university library stacks', 'victim_role': 'a night guard', 'hook': 'A clean story is offered immediately. Your job is to find what it avoids.', 'victim_name': 'Casey Sato', 'date': 'July 21, 2025', 'weather': 'sharp winter cold', 'smell': 'salt and engine oil', 'suspects': [{'name': 'Ivo Ibrahim', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Talia Rossi', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Elias Hale', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Dimitri Lavoie', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'coercion and control', 'method': 'tampered equipment', 'key': 'tool mark evidence'}, 'supports': ['a small scratch pattern consistent with a hurried tool', 'a quiet payment made in an odd amount', 'pollen trace matching a specific place', 'a suspicious purchase record', 'a delivery receipt with a serial gap', "a door that was 'locked' but not latched"], 'reds': ['a suspicious-looking stranger nearby', 'a dramatic argument overheard earlier', 'a rumor about secret debts'], 'anchors': [('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement.")]}, {'id': 'A68', 'title': 'A68 — Kestrel Park Park File', 'case_type': 'sexual_assault', 'setting': 'a public park trail', 'victim_role': 'a jogger', 'hook': 'A perfect alibi depends on one assumption you can test.', 'victim_name': 'Avery Kane', 'date': 'July 24, 2025', 'weather': 'heavy coastal mist', 'smell': 'perfume over disinfectant', 'suspects': [{'name': 'Sofia Hale', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Lea Khan', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Kostas Santos', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Aris Kerr', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'insurance payout', 'method': 'edited logs', 'key': 'keypad code change record'}, 'supports': ['an access attempt minutes before the reported time', 'an object moved against habit', 'a timeline that depends on the wrong clock', 'pollen trace matching a specific place', 'a missing entry in the visitor log', 'a handwritten note with familiar pressure pattern'], 'reds': ["a broken object that looks important but isn't", "a witness who 'remembers' after being prompted", 'a key that belongs to somewhere else'], 'anchors': [('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.')]}, {'id': 'A69', 'title': 'A69 — Snowbound Bus Case', 'case_type': 'murder', 'setting': 'a stranded coach bus', 'victim_role': 'a tour guide', 'hook': 'A statement arrives early, too polished to be spontaneous.', 'victim_name': 'Casey Hart', 'date': 'July 27, 2025', 'weather': 'late-summer heat', 'smell': 'old books and varnish', 'suspects': [{'name': 'Maya Volkov', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Theo Baird', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Mina Rossi', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Yara Yilmaz', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'revenge for a past betrayal', 'method': 'misdirected delivery', 'key': 'badge access anomaly'}, 'supports': ['a timeline that depends on the wrong clock', 'a maintenance schedule that was quietly edited', 'a delivery receipt with a serial gap', 'a small scratch pattern consistent with a hurried tool', 'a witness who changes wording under pressure', 'a second copy of a report with one word changed'], 'reds': ["a witness who 'remembers' after being prompted", 'a misread CCTV reflection', 'an old threat letter with no date'], 'anchors': [('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.')]}, {'id': 'A70', 'title': 'A70 — Elm Law Office Ledger', 'case_type': 'political', 'setting': 'a legal office conference room', 'victim_role': 'a paralegal', 'hook': 'A clean story is offered immediately. Your job is to find what it avoids.', 'victim_name': 'Casey Petros', 'date': 'July 30, 2025', 'weather': 'electric storm air', 'smell': 'citrus cleaner', 'suspects': [{'name': 'Mara Vega', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Mina Volkov', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Rami Serrano', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Mikhail Rossi', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'jealousy over a secret relationship', 'method': 'swapped two identical folders', 'key': 'metadata timestamp mismatch'}, 'supports': ['a quiet payment made in an odd amount', 'an object moved against habit', 'a message thread with deleted lines', 'pollen trace matching a specific place', 'a handwritten note with familiar pressure pattern', 'a witness who changes wording under pressure'], 'reds': ['a misread CCTV reflection', 'a suspicious-looking stranger nearby', "a broken object that looks important but isn't"], 'anchors': [('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.')]}, {'id': 'A71', 'title': 'A71 — Jet Manifest Airport Shadow', 'case_type': 'murder', 'setting': 'a small airport hangar', 'victim_role': 'a lobbyist', 'hook': 'A complaint is filed, and the timeline is the weapon.', 'victim_name': 'Sam Novak', 'date': 'August 02, 2025', 'weather': 'cold drizzle', 'smell': 'bleach and metal', 'suspects': [{'name': 'Selene Volkov', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Mikhail Kane', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Theo Volkov', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Samira Arden', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'to stop a blackmail payoff', 'method': 'removed a safety stop', 'key': 'soil/pollen trace'}, 'supports': ['a delivery receipt with a serial gap', 'a witness who changes wording under pressure', 'a second copy of a report with one word changed', 'a contradicted alibi minute-by-minute', "a door that was 'locked' but not latched", 'an object moved against habit'], 'reds': ['a rumor about secret debts', 'a fake social media screenshot', 'an old threat letter with no date'], 'anchors': [('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.')]}, {'id': 'A72', 'title': 'A72 — Sunset Marina Marina Incident', 'case_type': 'political', 'setting': 'a marina pier at dusk', 'victim_role': 'a boat mechanic', 'hook': 'Everyone agrees on the headline, but nobody agrees on the minutes.', 'victim_name': 'Jamie Petros', 'date': 'August 05, 2025', 'weather': 'dry wind', 'smell': 'coffee and dust', 'suspects': [{'name': 'Elena Santos', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Priya Nassar', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Iris Pappas', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Ivo Rowan', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 0, 'motive': 'to bury a donor list', 'method': 'covert recording + smear', 'key': 'call detail record'}, 'supports': ['a missing entry in the visitor log', 'a second copy of a report with one word changed', 'a delivery receipt with a serial gap', "a door that was 'locked' but not latched", 'a quiet payment made in an odd amount', 'an object moved against habit'], 'reds': ['a misleading anonymous tip email', 'a key that belongs to somewhere else', "a partial fingerprint that doesn't match anyone here"], 'anchors': [('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.')]}, {'id': 'A73', 'title': 'A73 — Museum Donation Museum Signal 73', 'case_type': 'sexual_assault', 'setting': 'a city museum storage wing', 'victim_role': 'a curator', 'hook': 'A small detail doesn’t match the rest. That’s the crack you start with.', 'victim_name': 'Avery Delphi', 'date': 'August 08, 2025', 'weather': 'humid night air', 'smell': 'ozone and damp paper', 'suspects': [{'name': 'Yara Vallis', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Mina Markou', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Priya Vega', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Aris Wu', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'predation + silencing', 'method': 'loosened railing bolts', 'key': 'receipt serial gap'}, 'supports': ['a maintenance schedule that was quietly edited', 'a contradicted alibi minute-by-minute', 'pollen trace matching a specific place', "a door that was 'locked' but not latched", 'a timeline that depends on the wrong clock', 'a message thread with deleted lines'], 'reds': ['a key that belongs to somewhere else', 'a misread CCTV reflection', 'a misleading anonymous tip email'], 'anchors': [('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.')]}, {'id': 'A74', 'title': 'A74 — Aster Lane Apartment Shadow', 'case_type': 'murder', 'setting': 'a dense apartment block lobby', 'victim_role': 'a tenant', 'hook': 'A clean story is offered immediately. Your job is to find what it avoids.', 'victim_name': 'Drew Kerr', 'date': 'August 11, 2025', 'weather': 'sharp winter cold', 'smell': 'salt and engine oil', 'suspects': [{'name': 'Mikhail Hale', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Rami Baird', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Samira Sato', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Priya Hale', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'embezzlement cover-up', 'method': 'stole draft + staged a break-in', 'key': 'elevator panel smear pattern'}, 'supports': ['a small scratch pattern consistent with a hurried tool', 'a timeline that depends on the wrong clock', 'pollen trace matching a specific place', 'a printed document with a subtle formatting difference', 'a message thread with deleted lines', 'a handwritten note with familiar pressure pattern'], 'reds': ["a witness who 'remembers' after being prompted", 'a viral post with a cropped timestamp', 'an old threat letter with no date'], 'anchors': [('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement.")]}, {'id': 'A75', 'title': 'A75 — Night Shift Records Night', 'case_type': 'political', 'setting': 'a police records office', 'victim_role': 'a clerk', 'hook': 'Everyone agrees on the headline, but nobody agrees on the minutes.', 'victim_name': 'Taylor Novak', 'date': 'August 14, 2025', 'weather': 'heavy coastal mist', 'smell': 'perfume over disinfectant', 'suspects': [{'name': 'Mina Ibrahim', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Noah Haddad', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Mara Hart', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Yara Tanaka', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'covering a financial fraud', 'method': 'coercion and intimidation', 'key': 'tamper seal mismatch'}, 'supports': ['a handwritten note with familiar pressure pattern', 'a contradicted alibi minute-by-minute', 'a maintenance schedule that was quietly edited', 'a second copy of a report with one word changed', 'a witness who changes wording under pressure', 'a timeline that depends on the wrong clock'], 'reds': ["a partial fingerprint that doesn't match anyone here", 'a misleading anonymous tip email', 'a viral post with a cropped timestamp'], 'anchors': [('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.')]}, {'id': 'A76', 'title': 'A76 — Glasshouse Conservatory Memo', 'case_type': 'murder', 'setting': 'a botanical conservatory', 'victim_role': 'a horticulturist', 'hook': 'A clean story is offered immediately. Your job is to find what it avoids.', 'victim_name': 'Morgan Hart', 'date': 'August 17, 2025', 'weather': 'late-summer heat', 'smell': 'old books and varnish', 'suspects': [{'name': 'Ivo Kline', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Elias Hart', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Jon Nassar', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Dana Hale', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'political leverage', 'method': 'forged resignation + shredding', 'key': 'fresh wrench marks'}, 'supports': ['a small scratch pattern consistent with a hurried tool', 'call history showing a short, repeated number', 'a photo edited, but not where people claim', 'a staff roster with a late change', 'a witness who changes wording under pressure', 'a maintenance schedule that was quietly edited'], 'reds': ['an old threat letter with no date', "a broken object that looks important but isn't", 'a viral post with a cropped timestamp'], 'anchors': [('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.')]}, {'id': 'A77', 'title': 'A77 — Keypad Therapy Case', 'case_type': 'political', 'setting': 'a therapy clinic hallway', 'victim_role': 'a patient', 'hook': 'A small detail doesn’t match the rest. That’s the crack you start with.', 'victim_name': 'Casey Bennett', 'date': 'August 20, 2025', 'weather': 'electric storm air', 'smell': 'citrus cleaner', 'suspects': [{'name': 'Nadia Nielsen', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Ivo Wu', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Lucas Rowan', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Lea Delphi', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'silencing a witness', 'method': 'poison slipped into a drink', 'key': 'printer log timestamp'}, 'supports': ['a printed document with a subtle formatting difference', 'call history showing a short, repeated number', 'a timeline that depends on the wrong clock', 'pollen trace matching a specific place', 'an access attempt minutes before the reported time', 'a suspicious purchase record'], 'reds': ['a viral post with a cropped timestamp', 'an old threat letter with no date', 'a misread CCTV reflection'], 'anchors': [('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.')]}, {'id': 'A78', 'title': 'A78 — Rook & Crown Casino Memo', 'case_type': 'sexual_assault', 'setting': 'a small casino pit', 'victim_role': 'a pit boss', 'hook': 'A statement arrives early, too polished to be spontaneous.', 'victim_name': 'Riley Roux', 'date': 'August 23, 2025', 'weather': 'cold drizzle', 'smell': 'bleach and metal', 'suspects': [{'name': 'Hana Baird', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Elias Markou', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Jules Vega', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Samira Baird', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'career sabotage', 'method': 'staged accident', 'key': 'door camera gap + keycard data'}, 'supports': ['a printed document with a subtle formatting difference', 'an access attempt minutes before the reported time', 'a staff roster with a late change', 'a quiet payment made in an odd amount', 'a second copy of a report with one word changed', "a door that was 'locked' but not latched"], 'reds': ['a misread CCTV reflection', 'a key that belongs to somewhere else', 'a fake social media screenshot'], 'anchors': [('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.')]}, {'id': 'A79', 'title': 'A79 — Election Van Campaign Incident 79', 'case_type': 'murder', 'setting': 'a campaign headquarters', 'victim_role': 'a field organizer', 'hook': 'A complaint is filed, and the timeline is the weapon.', 'victim_name': 'Drew Bennett', 'date': 'August 26, 2025', 'weather': 'dry wind', 'smell': 'coffee and dust', 'suspects': [{'name': 'Samira Vega', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Priya Okoye', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Aris Okoye', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Maya Okoye', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'protecting an accomplice', 'method': 'tampered equipment', 'key': 'ink mismatch on signature'}, 'supports': ['a quiet payment made in an odd amount', 'a delivery receipt with a serial gap', 'a second copy of a report with one word changed', 'a suspicious purchase record', 'a message thread with deleted lines', 'pollen trace matching a specific place'], 'reds': ['an old threat letter with no date', 'a dramatic argument overheard earlier', 'a misleading anonymous tip email'], 'anchors': [('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.')]}, {'id': 'A80', 'title': 'A80 — Bitter Coffee Cafe Switch', 'case_type': 'political', 'setting': 'a cafe service counter', 'victim_role': 'a food critic', 'hook': 'A complaint is filed, and the timeline is the weapon.', 'victim_name': 'Quinn Kerr', 'date': 'August 29, 2025', 'weather': 'humid night air', 'smell': 'ozone and damp paper', 'suspects': [{'name': 'Mikhail Tanaka', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Samira Hale', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Elias Novak', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Mikhail Lavoie', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'avoiding exposure', 'method': 'edited logs', 'key': 'security log gap'}, 'supports': ['a timeline that depends on the wrong clock', 'a staff roster with a late change', 'a quiet payment made in an odd amount', 'a delivery receipt with a serial gap', 'an access attempt minutes before the reported time', 'a contradicted alibi minute-by-minute'], 'reds': ['a viral post with a cropped timestamp', 'a suspicious-looking stranger nearby', 'a misleading anonymous tip email'], 'anchors': [('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.')]}, {'id': 'A81', 'title': 'A81 — Rivergate Balcony Switch', 'case_type': 'murder', 'setting': 'a high-rise overlooking a canal', 'victim_role': 'a property developer', 'hook': 'The scene looks ordinary until you check what should have been impossible.', 'victim_name': 'Casey Sato', 'date': 'September 01, 2025', 'weather': 'sharp winter cold', 'smell': 'salt and engine oil', 'suspects': [{'name': 'Ivo Nassar', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Noah Markou', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Priya Novak', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Omar Hale', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 0, 'motive': 'coercion and control', 'method': 'misdirected delivery', 'key': 'CCTV angle blind spot'}, 'supports': ['a maintenance schedule that was quietly edited', 'a quiet payment made in an odd amount', 'a timeline that depends on the wrong clock', 'a second copy of a report with one word changed', "a door that was 'locked' but not latched", 'a handwritten note with familiar pressure pattern'], 'reds': ['a fake social media screenshot', 'a rumor about secret debts', 'a key that belongs to somewhere else'], 'anchors': [('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement.")]}, {'id': 'A82', 'title': 'A82 — Cold Ink Newsroom Night', 'case_type': 'political', 'setting': 'an independent newspaper office', 'victim_role': 'an investigative editor', 'hook': 'A small detail doesn’t match the rest. That’s the crack you start with.', 'victim_name': 'Riley Kane', 'date': 'September 04, 2025', 'weather': 'heavy coastal mist', 'smell': 'perfume over disinfectant', 'suspects': [{'name': 'Selene Khan', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Elena Haddad', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Dimitri Sato', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Mara Yilmaz', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 0, 'motive': 'insurance payout', 'method': 'swapped two identical folders', 'key': 'tool mark evidence'}, 'supports': ['a printed document with a subtle formatting difference', 'a missing entry in the visitor log', 'a second copy of a report with one word changed', 'a staff roster with a late change', 'a timeline that depends on the wrong clock', 'a quiet payment made in an odd amount'], 'reds': ["a broken object that looks important but isn't", 'a suspicious-looking stranger nearby', 'an old threat letter with no date'], 'anchors': [('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.')]}, {'id': 'A83', 'title': 'A83 — Silk Road Motel Signal', 'case_type': 'sexual_assault', 'setting': 'a roadside motel off a dim highway', 'victim_role': 'a traveling musician', 'hook': 'A missing object matters more than the object itself.', 'victim_name': 'Casey Novak', 'date': 'September 07, 2025', 'weather': 'late-summer heat', 'smell': 'old books and varnish', 'suspects': [{'name': 'Aris Novak', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Selene Nassar', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Yara Rossi', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Selene Petros', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'revenge for a past betrayal', 'method': 'removed a safety stop', 'key': 'keypad code change record'}, 'supports': ['pollen trace matching a specific place', 'a delivery receipt with a serial gap', 'a printed document with a subtle formatting difference', 'a handwritten note with familiar pressure pattern', 'a suspicious purchase record', 'an object moved against habit'], 'reds': ['a key that belongs to somewhere else', 'a misread CCTV reflection', 'a misleading anonymous tip email'], 'anchors': [('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.')]}, {'id': 'A84', 'title': 'A84 — Vanished Ledger Office Shadow', 'case_type': 'murder', 'setting': 'a municipal finance office', 'victim_role': 'a whistleblower accountant', 'hook': 'A clean story is offered immediately. Your job is to find what it avoids.', 'victim_name': 'Drew Hwang', 'date': 'September 10, 2025', 'weather': 'electric storm air', 'smell': 'citrus cleaner', 'suspects': [{'name': 'Omar Nielsen', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Ivo Rossi', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Theo Kane', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Lucas Volkov', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'jealousy over a secret relationship', 'method': 'covert recording + smear', 'key': 'badge access anomaly'}, 'supports': ['a photo edited, but not where people claim', 'pollen trace matching a specific place', 'a quiet payment made in an odd amount', 'a staff roster with a late change', 'a missing entry in the visitor log', 'a delivery receipt with a serial gap'], 'reds': ['a suspicious-looking stranger nearby', "a witness who 'remembers' after being prompted", 'a dramatic argument overheard earlier'], 'anchors': [('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.')]}, {'id': 'A85', 'title': 'A85 — Midnight Docks Switch', 'case_type': 'political', 'setting': 'a container terminal at night', 'victim_role': 'a customs broker', 'hook': 'A missing object matters more than the object itself.', 'victim_name': 'Quinn Roux', 'date': 'September 13, 2025', 'weather': 'cold drizzle', 'smell': 'bleach and metal', 'suspects': [{'name': 'Lea Markou', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Maya Sato', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Talia Vallis', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Jon Santos', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'to stop a blackmail payoff', 'method': 'loosened railing bolts', 'key': 'metadata timestamp mismatch'}, 'supports': ['call history showing a short, repeated number', 'a contradicted alibi minute-by-minute', "a door that was 'locked' but not latched", 'a quiet payment made in an odd amount', 'a handwritten note with familiar pressure pattern', 'a staff roster with a late change'], 'reds': ['a rumor about secret debts', "a witness who 'remembers' after being prompted", 'a suspicious-looking stranger nearby'], 'anchors': [('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.')]}, {'id': 'A86', 'title': 'A86 — Opera Opera House Incident', 'case_type': 'murder', 'setting': 'a restored opera house backstage', 'victim_role': 'a cultural minister', 'hook': 'Everyone agrees on the headline, but nobody agrees on the minutes.', 'victim_name': 'Morgan Kane', 'date': 'September 16, 2025', 'weather': 'dry wind', 'smell': 'coffee and dust', 'suspects': [{'name': 'Selene Kerr', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Nadia Rossi', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Jon Kline', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Hana Rossi', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 3, 'motive': 'to bury a donor list', 'method': 'stole draft + staged a break-in', 'key': 'soil/pollen trace'}, 'supports': ['a second copy of a report with one word changed', 'a handwritten note with familiar pressure pattern', 'an object moved against habit', 'a small scratch pattern consistent with a hurried tool', 'pollen trace matching a specific place', 'a maintenance schedule that was quietly edited'], 'reds': ["a partial fingerprint that doesn't match anyone here", 'a rumor about secret debts', 'a suspicious-looking stranger nearby'], 'anchors': [('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.')]}, {'id': 'A87', 'title': 'A87 — Pinecrest Cabin Pattern', 'case_type': 'political', 'setting': 'a forest cabin community', 'victim_role': 'a retired firefighter', 'hook': 'The scene looks ordinary until you check what should have been impossible.', 'victim_name': 'Morgan Petros', 'date': 'September 19, 2025', 'weather': 'humid night air', 'smell': 'ozone and damp paper', 'suspects': [{'name': 'Dimitri Arden', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Priya Yilmaz', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Selene Baird', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Selene Yilmaz', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'predation + silencing', 'method': 'coercion and intimidation', 'key': 'call detail record'}, 'supports': ['a photo edited, but not where people claim', 'a witness who changes wording under pressure', 'a handwritten note with familiar pressure pattern', 'a missing entry in the visitor log', "a door that was 'locked' but not latched", 'a small scratch pattern consistent with a hurried tool'], 'reds': ['a suspicious-looking stranger nearby', 'a fake social media screenshot', 'a misread CCTV reflection'], 'anchors': [('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.')]}, {'id': 'A88', 'title': 'A88 — Clinic Clinic Pattern 88', 'case_type': 'sexual_assault', 'setting': 'a private clinic reception area', 'victim_role': 'a graduate student', 'hook': 'A clean story is offered immediately. Your job is to find what it avoids.', 'victim_name': 'Avery Arden', 'date': 'September 22, 2025', 'weather': 'sharp winter cold', 'smell': 'salt and engine oil', 'suspects': [{'name': 'Sofia Arden', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Nadia Rowan', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Noah Nielsen', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Theo Okoye', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 1, 'motive': 'embezzlement cover-up', 'method': 'forged resignation + shredding', 'key': 'receipt serial gap'}, 'supports': ['a suspicious purchase record', 'a missing entry in the visitor log', 'a staff roster with a late change', 'a handwritten note with familiar pressure pattern', 'a witness who changes wording under pressure', 'a quiet payment made in an odd amount'], 'reds': ['a key that belongs to somewhere else', 'a misread CCTV reflection', 'an old threat letter with no date'], 'anchors': [('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement.")]}, {'id': 'A89', 'title': 'A89 — Split Vote Council Ledger', 'case_type': 'murder', 'setting': 'a city council chamber', 'victim_role': 'a council aide', 'hook': 'A clean story is offered immediately. Your job is to find what it avoids.', 'victim_name': 'Jamie Petros', 'date': 'September 25, 2025', 'weather': 'heavy coastal mist', 'smell': 'perfume over disinfectant', 'suspects': [{'name': 'Rami Vega', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Omar Serrano', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Lea Santos', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Elias Ibrahim', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 0, 'motive': 'covering a financial fraud', 'method': 'poison slipped into a drink', 'key': 'elevator panel smear pattern'}, 'supports': ['a message thread with deleted lines', 'a quiet payment made in an odd amount', 'a printed document with a subtle formatting difference', 'a delivery receipt with a serial gap', 'a photo edited, but not where people claim', 'pollen trace matching a specific place'], 'reds': ['a misleading anonymous tip email', "a partial fingerprint that doesn't match anyone here", 'a viral post with a cropped timestamp'], 'anchors': [('T+00', 'Incident discovered / reported.'), ('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.')]}, {'id': 'A90', 'title': 'A90 — Blue Velvet Gallery Memo', 'case_type': 'political', 'setting': 'a modern art gallery', 'victim_role': 'an art patron', 'hook': 'A clean story is offered immediately. Your job is to find what it avoids.', 'victim_name': 'Riley Sato', 'date': 'September 28, 2025', 'weather': 'late-summer heat', 'smell': 'old books and varnish', 'suspects': [{'name': 'Mina Tanaka', 'role': 'Inner circle', 'summary': 'Had direct access and knows routines. Emotions are complicated.'}, {'name': 'Nadia Sato', 'role': 'Professional rival', 'summary': 'Competes with the victim and benefits from their downfall. Claims distance.'}, {'name': 'Talia Hale', 'role': 'Fixer / operator', 'summary': 'Understands systems, logs, and how to erase footprints. Calm under pressure.'}, {'name': 'Rami Haddad', 'role': 'Outsider witness', 'summary': 'Was nearby. Details are vivid, but the order is strange.'}], 'truth': {'culprit': 2, 'motive': 'political leverage', 'method': 'staged accident', 'key': 'tamper seal mismatch'}, 'supports': ['pollen trace matching a specific place', 'an object moved against habit', 'a message thread with deleted lines', 'a timeline that depends on the wrong clock', 'a maintenance schedule that was quietly edited', 'a small scratch pattern consistent with a hurried tool'], 'reds': ["a broken object that looks important but isn't", 'a misleading anonymous tip email', "a witness who 'remembers' after being prompted"], 'anchors': [('T+15', 'A statement is given that shifts key wording.'), ('T-90', 'Victim responds to a message / sets an appointment.'), ('T-60', 'Victim confirms a meeting.'), ('T-45', 'A system log shows activity.'), ('T-30', "A witness reports a 'sound' or unusual movement."), ('T-15', 'Someone enters or exits a restricted area.'), ('T+00', 'Incident discovered / reported.')]}]

# ----------------------------- File/OS helpers -----------------------------

def home_dir() -> str:
    return os.path.expanduser("~")

def save_dir() -> str:
    return os.path.join(home_dir(), SAVE_DIR_NAME)

def ensure_save_dir() -> None:
    os.makedirs(save_dir(), exist_ok=True)

def path_in_save(name: str) -> str:
    return os.path.join(save_dir(), name)

def wrap(text: str, width: int = WRAP) -> str:
    out = []
    for line in text.splitlines():
        if not line.strip():
            out.append("")
        else:
            out.append(textwrap.fill(line, width=width))
    return "\n".join(out)

def clear() -> None:
    os.system("clear" if os.name != "nt" else "cls")

def press_enter() -> None:
    input("\n[Press Enter] ")

def now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")

def safe_int(s: str, default: int = 0) -> int:
    try:
        return int(s)
    except Exception:
        return default

def normalize(s: str) -> str:
    s = s.strip().lower()
    out = []
    for ch in s:
        if ch.isalnum() or ch.isspace():
            out.append(ch)
    return " ".join("".join(out).split())

def minutes_elapsed(start_epoch: float) -> int:
    return max(0, int((time.time() - start_epoch) // 60))

# ----------------------------- Data model -----------------------------

@dataclass
class Action:
    label: str
    text: str
    evidence_add: List[str]
    note_prompt: Optional[str] = None

@dataclass
class Scene:
    title: str
    intro: str
    actions: List[Action]
    checkpoint_question: str
    checkpoint_answers: List[str]
    hint: str
    checkpoint_evidence_add: List[str]

@dataclass
class Case:
    case_id: str
    title: str
    case_type: str
    difficulty_key: str
    setup: str
    suspects: List[Dict[str, str]]
    scenes: List[Scene]
    solution: Dict[str, Any]

@dataclass
class SaveGame:
    version: int
    slot: int
    created_at: str
    updated_at: str
    case: Dict[str, Any]
    scene_index: int
    seen_actions: Dict[str, List[int]]
    notes: List[str]
    evidence: List[str]
    hint_tokens_left: int
    start_time_epoch: float

HIGHSCORES_FILE = "highscores.json"

SENSE_LINES = [
    "You listen to the room the way other people listen to music.",
    "Everyone wants the first story to be the final story.",
    "A good lie doesn't add details; it removes the inconvenient ones.",
    "You watch hands. You watch feet. You watch what people look at when they think nobody is watching.",
    "The truth is rarely dramatic. It's just consistent.",
]

# ----------------------------- Deterministic case builder -----------------------------

def build_case(bp: Dict[str, Any], difficulty_key: str) -> Case:
    cid = bp["id"]
    title = bp["title"]
    ctype = bp["case_type"]
    setting = bp["setting"]
    victim_role = bp["victim_role"]
    hook = bp["hook"]
    victim_name = bp["victim_name"]
    date = bp["date"]
    weather = bp["weather"]
    smell = bp["smell"]
    suspects = bp["suspects"]
    truth = bp["truth"]
    key = truth["key"]
    motive = truth["motive"]
    method = truth["method"]
    culprit_idx = int(truth["culprit"])
    culprit_name = suspects[culprit_idx]["name"]
    supports = bp["supports"]
    reds = bp["reds"]
    anchors = bp["anchors"]

    strict = DIFFICULTIES[difficulty_key]["strict"]

    def acc(*answers: str) -> List[str]:
        norms = [normalize(a) for a in answers]
        if strict >= 2:
            return norms[:1]
        if strict == 1:
            return norms[:2] if len(norms) > 1 else norms
        return norms

    setup = f"""
CASE PREFIX: {cid}
TITLE: {title}
TYPE: {ctype.upper()}

DATE: {date}
LOCATION: {setting}

VICTIM: {victim_name}, {victim_role}.
HOOK: {hook}

ATMOSPHERE: {weather}. The place smells like {smell}.

LONG CASE RULE:
- You cannot accuse until at least {REQUIRED_MINUTES_PER_CASE} minutes have passed since starting the case.

TIP:
- Use :note often.
- Use :board and :timeline for ASCII visuals.
""".strip()

    suspect_block = "\n".join([f"{i+1}) {s['name']} — {s['role']}: {s['summary']}" for i, s in enumerate(suspects)])
    target = suspects[culprit_idx]["name"]
    sense = SENSE_LINES[(int(cid[1:]) - 1) % len(SENSE_LINES)]

    scenes: List[Scene] = []

    def action(label: str, text: str, ev: List[str], note_prompt: Optional[str] = None) -> Action:
        return Action(label=label, text=text, evidence_add=ev, note_prompt=note_prompt)

    def add_scene(title_s: str, intro: str, actions: List[Action], q: str, answers: List[str], hint: str, cev: List[str]):
        scenes.append(Scene(title=title_s, intro=intro, actions=actions,
                            checkpoint_question=q, checkpoint_answers=answers,
                            hint=hint, checkpoint_evidence_add=cev))

    stage_titles = [
        "Arrival & Scene Control",
        "Victim Profile & Pressure Points",
        "Suspects & First Impressions",
        "Key Forensics (Anchor)",
        "Timeline Reconstruction I",
        "Witness Interview I",
        "Systems & Access I",
        "Red Herring I",
        "Interview: Language & Control",
        "Reenactment & Physical Logic",
        "Timeline Reconstruction II",
        "Systems & Access II",
        "Support Thread Deep Dive",
        "Motive: Follow the Benefit",
        "Method: How It Was Done",
        "Cross-Check: Contradictions",
        "Red Herring II",
        "Evidence Board (ASCII)",
        "Trap the Lie",
        "Final Logic (Ready)",
    ]

    add_scene(
        stage_titles[0],
        f"""[{cid}] ARRIVAL
You arrive at {setting}. The air feels staged: too tidy, too rehearsed.
{sense}

A uniformed officer gives you the short version and hands you a clipped note card:
"Case file date: {date}. Four people closest to {victim_name} tonight."
""".strip(),
        [
            action("Ask for the initial call transcript (exact words)",
                   "The caller used unusually specific wording. You copy the phrasing exactly and circle one verb.",
                   ["Initial call transcript copied"], "What exact wording felt 'too sure'?"),
            action("Walk the perimeter and photograph what others ignore",
                   "You photograph seams, corners, and the places nobody looks because they look boring.",
                   ["Perimeter photos taken"]),
            action("Ask who sealed the scene and when",
                   "Chain-of-custody begins with the first person who says 'I handled it.'",
                   ["Scene sealing time recorded"]),
            action("Ask what the first responder touched",
                   "They hesitate, then list items. Hesitation is either guilt or fear. Either is useful.",
                   ["First responder contact list noted"]),
            action("Check what was NOT photographed (and why)",
                   "A tech admits someone requested an angle be avoided 'for privacy'. Privacy is often a curtain.",
                   ["Photo coverage gap noted"], "Which angle/area was avoided?"),
        ],
        "Checkpoint: What is the DATE on the case file?",
        acc(date),
        f"It's on the note card and in the setup: {date}.",
        [f"Date recorded: {date}"]
    )

    add_scene(
        stage_titles[1],
        f"""[{cid}] VICTIM
The victim, {victim_name}, was not careless. That matters.
A colleague describes recent behavior: guarded meetings, shorter emails, a habit of checking behind them.

{sense}
""".strip(),
        [
            action("Ask about the victim's last week in detail",
                   f"Two unusual events stand out: a canceled meeting and a sudden focus on {motive}.",
                   [f"Victim linked to motive theme: {motive}"], "Which event felt most suspicious and why?"),
            action("Search the desk / workspace carefully",
                   "A drawer is open as if searched quickly. Papers are neat except for one corner handled too often.",
                   ["Desk searched in a hurry", "Frequently handled paper corner"]),
            action("Ask what the victim always carried",
                   "They mention a small personal item. Not valuable, but meaningful. If it's missing, someone wanted it.",
                   ["Victim carried a small personal item"]),
            action("Ask: 'Who did the victim trust?'",
                   "Trust leaves patterns: who they answered quickly, who they avoided, who they met quietly.",
                   ["Victim trust circle discussed"]),
            action("Check recent security behavior (password changes, access habits)",
                   "The victim recently changed one password and enabled an extra factor. People do that when they feel watched.",
                   ["Security behavior change noted"]),
        ],
        "Checkpoint: What was the victim described as (one word)?",
        acc("guarded", "cautious", "precise"),
        "The colleague described them as guarded/cautious.",
        ["Victim described as guarded/cautious"]
    )

    add_scene(
        stage_titles[2],
        f"""[{cid}] SUSPECTS
You list the four primary suspects and watch reactions when you speak the victim's name:
{suspect_block}

{sense}
""".strip(),
        [
            action("Address all four together (observe micro-reactions)",
                   "One steps back when you mention the missing item. Another leans in as if to manage the narrative.",
                   ["Group reaction: micro-movement when missing item mentioned"]),
            action("Ask each: 'When did you last see the victim?' (force sequence)",
                   "Two answers are 'about' a time. One is a story. One is a defense.",
                   ["Last-seen answers collected"]),
            action("Ask each: 'Who else should I speak to?'",
                   "A good witness suggests names. A liar suggests a scapegoat. You mark who tries to steer you.",
                   ["Steering behavior noted"]),
            action("Ask each: 'What do you think happened?' (trap framing)",
                   "Their first guess reveals what they want you to believe.",
                   ["Framing statements collected"]),
            action("Observe hands/clothing subtly for trace",
                   "Nothing dramatic. But you notice one detail that could match a tool, a surface, or an environment.",
                   ["Hands/clothing observed for trace clues"], "What detail stood out (fabric/dirt/scratch/smell)?"),
        ],
        "Checkpoint: How many primary suspects are there?",
        acc("4", "four"),
        "You listed them as 1 through 4.",
        ["Suspects list confirmed: 4"]
    )

    add_scene(
        stage_titles[3],
        f"""[{cid}] KEY ANCHOR
Forensics gives you your first hard anchor: {key}.
It doesn’t shout a name, but it shouts intention.
Someone nearby watches the evidence bagging too carefully.

{sense}
""".strip(),
        [
            action("Ask for a plain explanation of the anchor",
                   f"The tech explains what {key} means in practical terms and why it matters.",
                   [f"Key clue understood: {key}"]),
            action("Ask: 'What would this look like if accidental?'",
                   "They describe how accident differs. Small differences, consistent pattern.",
                   ["Accident-vs-intent differences logged"]),
            action("Ask: 'Who had access to the relevant area/system?'",
                   "Access is never just keys. It's habit, permission, and confidence.",
                   ["Access discussion recorded"]),
            action("Ask about when the anchor likely happened",
                   "They estimate a window. You compare it to suspect statements.",
                   ["Anchor timing window estimated"]),
            action("Request chain-of-custody detail",
                   "You confirm who touched what and when. Liars hate paperwork.",
                   ["Chain-of-custody confirmed"]),
        ],
        "Checkpoint: What is the key forensic anchor mentioned? (exact phrase)",
        acc(key),
        f"It appears in the intro: {key}.",
        [f"Key clue pinned: {key}"]
    )

    def make_support_scene(title_s: str, label: str, clue: str, q: str, hint: str, ev: List[str], actions: List[Action]):
        add_scene(
            title_s,
            f"""[{cid}] {label}
{sense}
Support clue: {clue}.
""".strip(),
            actions,
            q,
            acc(clue),
            hint,
            ev
        )

    # Support scenes 5-7 and 11-13
    make_support_scene(
        stage_titles[4], "TIMELINE I", supports[0],
        "Checkpoint: What clue narrows the time window? (exact phrase)",
        "It is labeled as the support clue in this scene.",
        [f"Support pinned: {supports[0]}"],
        [
            action("Get a minute-by-minute account from the first witness",
                   "They narrate cleanly, but skip a small gap. Gaps are where truth hides.",
                   ["Witness sequence recorded (gap noted)"], "What moment felt skipped?"),
            action("Compare all time sources (clocks, logs, receipts)",
                   "Two sources disagree by a few minutes. That tiny difference decides everything.",
                   ["Time sources compared (discrepancy found)"]),
            action("Ask: 'Who benefits if the window is narrow?'",
                   "Someone answers too quickly. Someone else refuses to answer at all.",
                   ["Benefit-of-window reactions noted"]),
            action("Draft anchors in your notebook",
                   "You write anchor points. A timeline is a trap you set for lies.",
                   ["Timeline anchors drafted"]),
            action("Pressure-test an alibi against distance",
                   "You walk the distance and imagine the pace. Some alibis become fiction instantly.",
                   ["Alibi distance test performed"]),
        ]
    )

    make_support_scene(
        stage_titles[5], "WITNESS I", supports[1],
        "Checkpoint: Repeat the SECOND support clue phrase (exact).",
        "It is printed as the support clue in the intro.",
        [f"Support pinned: {supports[1]}"],
        [
            action("Ask open question: 'Tell me what you remember, no interruptions.'",
                   "They talk until they reach the part they don't want to talk about. You mark that hesitation.",
                   ["Witness hesitation noted"]),
            action("Ask closed question: 'What did you hear first, exactly?'",
                   "Their wording changes when you remove their freedom to narrate.",
                   ["Witness wording shift recorded"]),
            action("Ask: 'What did you do right after?'",
                   "Actions reveal priorities. Priorities reveal motives.",
                   ["Witness actions-after recorded"]),
            action("Cross-check witness with a neutral observer",
                   "A neutral observer confirms some details and contradicts one.",
                   ["Witness cross-check contradiction found"]),
            action("Pin the support clue properly",
                   "You connect the clue to a person and a place.",
                   [f"Support linked: {supports[1]}"], "Who does this clue point toward, and why?"),
        ]
    )

    make_support_scene(
        stage_titles[6], "SYSTEMS I", supports[2],
        "Checkpoint: Type the THIRD support clue phrase exactly.",
        "It is the support clue in the intro.",
        [f"Support pinned: {supports[2]}"],
        [
            action("Request raw logs (not summaries)",
                   "Summaries are where lies get smuggled in. Raw logs are blunt.",
                   ["Raw logs requested"]),
            action("Compare official doc to backup copy",
                   "A formatting difference appears. Different author, different machine, or different intent.",
                   ["Formatting anomaly noted"]),
            action("Ask: 'Who can alter this without obvious traces?'",
                   "A name comes up. Not proof, but direction.",
                   ["Skill-to-alter discussion recorded"]),
            action("Look for the outlier line",
                   "You find it: the line that doesn't match the rest. Outliers are fingerprints.",
                   ["Outlier line found"]),
            action("Map access to suspects",
                   "You list who has keys, codes, habits, and opportunity. Access is a ladder.",
                   ["Access-to-suspects map drafted"]),
        ]
    )

    # Red herring I
    add_scene(
        stage_titles[7],
        f"""[{cid}] RED HERRING I
Information arrives that tries to hijack your attention.
Red herring: {reds[0]}.
It feels important because it feels emotional.
""".strip(),
        [
            action("Ask who started the rumor/story",
                   "It traces back to someone who wasn't present. Interesting.",
                   ["Red herring source traced (indirect origin)"]),
            action("Ask for proof, not vibes",
                   "The speaker gets offended. Offense is not evidence.",
                   ["Proof demanded; emotional resistance noted"]),
            action("Check if it changes the timeline shape",
                   "It doesn't. The case stays the same shape. You refuse the bait.",
                   ["Red herring does not affect timeline"]),
            action("Write it under NOISE in your notebook",
                   "Labeling weakens its power.",
                   [f"Red herring logged: {reds[0]}"]),
            action("Ask: 'Who benefits if I chase this?'",
                   "The answer is always someone who needs you distracted.",
                   ["Distraction-benefit question asked"]),
        ],
        "Checkpoint: Is this SUPPORT or RED HERRING?",
        acc("red", "red herring", "herring"),
        "It is labeled 'Red herring'.",
        ["Red herring categorized"]
    )

    # Interview
    add_scene(
        stage_titles[8],
        f"""[{cid}] INTERVIEW
You interview {target}. Their language is careful, like they're drafting a statement rather than remembering a night.
They avoid verbs that imply agency.
{sense}
""".strip(),
        [
            action("Ask: 'Start one hour before. Walk me through.'",
                   "They start later than you asked. That's a dodge.",
                   ["Interview: started timeline late (dodge)"]),
            action("Ask about the key anchor directly",
                   f"When you say '{key}', they pause, then ask: 'Does that really matter?'",
                   ["Interview: reacted oddly to key clue"]),
            action("Ask about motive-theme indirectly",
                   "They answer anyway, as if waiting for the topic. Readiness is suspicious.",
                   [f"Interview: pre-loaded response on motive theme: {motive}"]),
            action("Offer silence and wait",
                   "Silence makes people fill the room. They volunteer an unnecessary detail.",
                   ["Interview: volunteered unnecessary detail"], "What unnecessary detail did they mention?"),
            action("Ask: 'Who would you blame if you had to?'",
                   "A liar produces a scapegoat quickly. Truth takes time.",
                   ["Interview: scapegoat attempt recorded"]),
        ],
        "Checkpoint: Which suspect did you interview in this scene? (full name)",
        acc(target),
        "The scene says the name at the top.",
        [f"Interviewed: {target}"]
    )

    # Reenactment
    add_scene(
        stage_titles[9],
        f"""[{cid}] REENACTMENT
You walk the path the victim would have walked. The body of a case is geometry:
angles, distances, friction, time.
{sense}
""".strip(),
        [
            action("Measure distances with your steps",
                   "You estimate travel times. Some alibis become impossible.",
                   ["Travel-time plausibility checked"]),
            action("Identify social pressure points",
                   "You learn one pressure point: a reason the victim would hesitate or comply.",
                   ["Victim hesitation trigger identified"]),
            action("Check habitual patterns",
                   "Habit is baseline. The incident breaks it. The break is a clue.",
                   ["Habit deviation noted"]),
            action("Write an if/then chain",
                   "If motive is real, method must be quiet. If method is quiet, access must be confident.",
                   ["If/then chain recorded"]),
            action("Record a 'simple physics' summary",
                   "Accidents are sloppy. Intent is consistent.",
                   ["Physics summary written"], "What physical detail makes 'accident' unlikely?"),
        ],
        "Checkpoint: Type the word GEOMETRY.",
        acc("geometry"),
        "The scene calls the case 'geometry'.",
        ["Reenactment confirmed"]
    )

    # Remaining support scenes 11-13
    make_support_scene(
        stage_titles[10], "TIMELINE II", supports[3],
        "Checkpoint: What support clue is featured here? (exact phrase)",
        "It is labeled as the support clue in this scene.",
        [f"Support pinned: {supports[3]}"],
        [
            action("Rebuild the 'missing minutes' table",
                   "You build a small table of who could be where, and when.",
                   ["Missing-minutes table built"]),
            action("Ask each suspect for a specific minute marker",
                   "Liars hate minute markers. Truth tolerates them.",
                   ["Minute-marker responses collected"]),
            action("Check the 'wrong clock' hypothesis",
                   "One suspect relied on a clock that runs fast.",
                   ["Wrong-clock reliance detected"]),
            action("Add an anchor to your timeline",
                   "Anchors are nails for lies.",
                   ["Timeline anchor added"]),
            action("Write the strongest contradiction you have so far",
                   "One clean sentence. No drama. Just logic.",
                   ["Strongest contradiction drafted"], "Write your strongest contradiction sentence."),
        ]
    )

    make_support_scene(
        stage_titles[11], "SYSTEMS II", supports[4],
        "Checkpoint: Name this support clue (exact phrase).",
        "It is labeled as the support clue in this scene.",
        [f"Support pinned: {supports[4]}"],
        [
            action("Audit access histories (who accessed, when, from where)",
                   "Patterns appear: someone accesses only when it benefits them.",
                   ["Access history pattern noted"]),
            action("Check for a 'late roster change'",
                   "Small schedule edits are big opportunities.",
                   ["Roster/schedule edits checked"]),
            action("Ask: 'Who trained new staff on procedure?'",
                   "Training equals influence. Influence equals opportunity.",
                   ["Training influence recorded"]),
            action("Compare two identical-looking records",
                   "Identical isn't same. You find a mismatch you can't unsee.",
                   ["Record mismatch found"]),
            action("Link the support clue to a suspect capability",
                   "You connect procedure to a person who understands it.",
                   [f"Support linked: {supports[4]}"], "Who benefits from procedure knowledge here?"),
        ]
    )

    make_support_scene(
        stage_titles[12], "DEEP DIVE", supports[5],
        "Checkpoint: Repeat this support clue phrase (exact).",
        "It is labeled as the support clue in this scene.",
        [f"Support pinned: {supports[5]}"],
        [
            action("Return to the person who mentioned it first",
                   "They 'correct' themselves. Corrections are interesting.",
                   ["Follow-up triggered a correction"]),
            action("Check physical trace consistency",
                   "The detail matches one location but not another. Narrowing begins.",
                   ["Trace consistency checked"]),
            action("Ask: 'Who would think to manipulate this detail?'",
                   "Only someone familiar with procedure would try.",
                   ["Procedure-familiar set narrowed"]),
            action("Write the detail as a testable claim",
                   "Truth can be tested. Lies must be believed.",
                   ["Detail rewritten as testable claim"], "Rewrite the clue as a testable claim."),
            action("Pin it under SUPPORT and circle once",
                   "One circle means 'important'. Two circles means 'confirmed'.",
                   [f"Support pinned: {supports[5]}"]),
        ]
    )

    # Motive
    add_scene(
        stage_titles[13],
        f"""[{cid}] MOTIVE
You interrogate the 'why' without letting anyone sell you a story.
Motive theme: {motive}.
{sense}
""".strip(),
        [
            action("Ask: 'Who gains money, power, or safety from this?'",
                   "Two suspects gain something. Only one gains broadly.",
                   ["Benefit analysis: one suspect gains broadly"]),
            action("Ask: 'Who loses if the truth is known?'",
                   "Someone flinches at a word you didn't emphasize.",
                   ["Reaction to 'truth' noted"]),
            action("Check for leverage signals (secrets, pressure, threats)",
                   "Leverage is currency. You find a hint of it.",
                   ["Leverage hint found"]),
            action("Ask a neutral party: 'What would scare the victim most?'",
                   "Fear points you at motive.",
                   ["Victim fear angle recorded"]),
            action("Write motive in your own words",
                   "One sentence. If you can’t compress it, you can’t test it.",
                   [f"Motive pinned: {motive}"], "Write your one-sentence motive summary."),
        ],
        "Checkpoint: Type the motive phrase exactly as shown.",
        acc(motive),
        f"It's written as the motive theme: {motive}.",
        [f"Motive confirmed: {motive}"]
    )

    # Method
    add_scene(
        stage_titles[14],
        f"""[{cid}] METHOD
If the motive is {motive}, then the method is likely: {method}.
You compare what had to happen against what people say happened.
{sense}
""".strip(),
        [
            action("List prerequisites for the method (access, timing, tools)",
                   "You identify what the perpetrator needed. That list filters suspects.",
                   ["Method prerequisites listed"]),
            action("Ask a tech: 'Simplest way to do it?'",
                   "Crimes often use the simplest path. Complexity is for movies.",
                   ["Simplest-path method explanation logged"]),
            action("Find the point of no return on your timeline",
                   "Every case has a moment after which it can't be undone.",
                   ["Point-of-no-return identified"]),
            action("State your reconstruction out loud",
                   "Saying it exposes weak logic. You tighten it.",
                   ["Reconstruction spoken and refined"]),
            action("Write the method as a three-step sequence",
                   "Step 1, step 2, step 3. If you can sequence it, you can test it.",
                   [f"Method pinned: {method}"], "Write the method in three steps."),
        ],
        "Checkpoint: What is the likely METHOD? (exact phrase)",
        acc(method),
        "It's printed in the intro after 'method is likely'.",
        [f"Method confirmed: {method}"]
    )

    # Contradictions
    add_scene(
        stage_titles[15],
        f"""[{cid}] CROSS-CHECK
Now you cross-check. Truth aligns across sources. Lies only align with themselves.
{sense}
""".strip(),
        [
            action("Pick a suspect statement and restate it precisely",
                   "Precision is the enemy of lies.",
                   ["One suspect statement pinned precisely"]),
            action("Test it against timeline anchors",
                   "The statement collides with an anchor. Something can't be true.",
                   ["Statement conflicts with timeline anchor"]),
            action("Test it against access rules / skill requirements",
                   "Only one suspect fits the access + skill combo.",
                   ["Access+skill filter narrows suspects"]),
            action("Write the contradiction in one line",
                   "One line. No drama. Just logic.",
                   ["Contradiction stated cleanly"], "Write your contradiction sentence."),
            action("Ask: 'If this is a lie, what is it protecting?'",
                   "Lies protect a thing. You name the thing.",
                   ["Protected-thing hypothesis written"], "What is the lie protecting?"),
        ],
        "Checkpoint: Type CONTRADICTION to proceed.",
        acc("contradiction"),
        "The scene is about contradictions.",
        ["Contradiction checkpoint passed"]
    )

    # Red herring II
    add_scene(
        stage_titles[16],
        f"""[{cid}] RED HERRING II
A new piece of information arrives with the tone of certainty.
Red herring: {reds[1]}.
It looks official. That’s why it’s dangerous.
""".strip(),
        [
            action("Ask: 'Who produced this? When?'",
                   "The answer is vague. Vague is how fake things survive.",
                   ["Red herring provenance questioned (vague)"]),
            action("Check if it matches other evidence",
                   "It doesn't. It's incompatible with your anchors.",
                   ["Red herring conflicts with anchors"]),
            action("Ask a neutral party to interpret it",
                   "They shrug: 'Could mean anything.' Exactly.",
                   ["Neutral read: ambiguous / weak"]),
            action("Label it as likely planted distraction",
                   "You write: 'Looks loud. Doesn’t fit.' Then you move on.",
                   [f"Red herring logged: {reds[1]}", "Marked as likely distraction"]),
            action("Ask: 'Who benefits if this becomes the headline?'",
                   "A distraction that becomes public is the best distraction.",
                   ["Headline-distraction analysis recorded"]),
        ],
        "Checkpoint: Does this clue align with your timeline anchors? (yes/no)",
        acc("no", "not", "doesnt", "doesn't"),
        "It conflicts with anchors in your analysis.",
        ["Timeline mismatch confirmed"]
    )

    # Board
    add_scene(
        stage_titles[17],
        f"""[{cid}] BOARD
You pin everything on your evidence board.

KEY: {key}
SUPPORT: {supports[0]}
SUPPORT: {supports[1]}
SUPPORT: {supports[2]}
SUPPORT: {supports[3]}
SUPPORT: {supports[4]}
SUPPORT: {supports[5]}
RED: {reds[0]}
RED: {reds[1]}
RED: {reds[2]}
""".strip(),
        [
            action("Open :board (visual) and compare with your notes",
                   "You spot one mismatch between what you wrote and what the case says. You correct it.",
                   ["Notes corrected after board review"]),
            action("Ask: 'Which clue is the hinge?'",
                   f"The hinge is {key}. Everything else supports it or distracts from it.",
                   ["Hinge clue identified"]),
            action("Ask: 'Which clue is easiest to fake?'",
                   "Usually the loudest one. You label reds as potentially planted.",
                   ["Red herrings flagged as easy-to-fake"]),
            action("Write your top 3 remaining questions",
                   "Good detectives end with questions, not conclusions.",
                   ["Open questions written"], "Write your top 3 remaining questions."),
            action("Summarize the case in 5 bullets",
                   "If you can summarize it, you can explain it, and if you can explain it, you can prove it.",
                   ["Five-bullet summary written"], "Write 5 bullet summary lines."),
        ],
        "Checkpoint: Name ONE item labeled RED (type a few words).",
        acc(reds[0], reds[1], reds[2]),
        "Any of the 'RED:' lines work.",
        ["Evidence board summarized"]
    )

    # Trap
    add_scene(
        stage_titles[18],
        f"""[{cid}] TRAP
You pick one suspect statement and try to break it, cleanly and quietly.
{sense}
""".strip(),
        [
            action("Ask one suspect the same question twice (hours apart)",
                   "Consistency is a signature. Their answer shifts.",
                   ["Answer-shift observed"]),
            action("Check if any statement uses learned jargon",
                   "Some words only come from inside knowledge.",
                   ["Inside-jargon check performed"]),
            action("Test the key anchor against the suspect’s story",
                   "The key anchor refuses to bend.",
                   ["Key anchor vs story test logged"]),
            action("Write the 'one sentence accusation' draft",
                   "If you can't accuse in one sentence, you don't have the case.",
                   ["Accusation sentence drafted"], "Write your one-sentence accusation draft."),
            action("Choose which red herring was most tempting and why",
                   "Knowing the bait helps you avoid it next time.",
                   ["Tempting red herring analyzed"], "Which red herring tempted you most, and why?"),
        ],
        "Checkpoint: Type the word READY to proceed to final scene.",
        acc("ready"),
        "Type READY.",
        ["Trap scene passed"]
    )

    # Final
    add_scene(
        stage_titles[19],
        f"""[{cid}] FINAL LOGIC
You ask:
- Who benefits?
- Who had access?
- Who could execute '{method}' calmly?

One suspect had both motive ({motive}) and the practical ability to exploit '{key}'.

Now you choose—when the case is old enough to close.
""".strip(),
        [
            action("Review suspects one more time",
                   "You read each summary and compare it to your evidence list. One summary feels like a mask.",
                   ["Final suspect review completed"]),
            action("Use :timeline (visual) to check flow",
                   "The timeline visual makes one alibi collapse immediately.",
                   ["Timeline visual used to collapse an alibi"]),
            action("Use :notes to skim your earliest notes",
                   "Early notes are honest. Late notes are confident. You balance them.",
                   ["Notes skim completed"]),
            action("List the top 3 evidence items that matter most",
                   "Weight beats volume.",
                   ["Top 3 evidence items listed"], "List your top 3 evidence items."),
            action("Write your final theory in 3 sentences",
                   "Sentence 1: motive. Sentence 2: method. Sentence 3: culprit.",
                   ["Final theory written"], "Write your 3-sentence final theory."),
        ],
        "Checkpoint: Type CLOSE to enter accusation phase.",
        acc("close"),
        "Type CLOSE.",
        ["Ready for accusation"]
    )

    explanation = (
        f"You conclude that {culprit_name} is responsible. The turning point was {key}, "
        f"which supported your reconstruction of {method}. Combined with motive ({motive}) and the supporting "
        f"threads, their story could not hold."
    )

    solution = dict(
        culprit_name=culprit_name,
        motive=motive,
        method=method,
        key_evidence=key,
        evidence_support=supports,
        evidence_red=reds,
        timeline_anchors=anchors,
        explanation=explanation,
    )

    return Case(
        case_id=cid,
        title=title,
        case_type=ctype,
        difficulty_key=difficulty_key,
        setup=setup,
        suspects=suspects,
        scenes=scenes,
        solution=solution,
    )

# ----------------------------- Persistence -----------------------------

def load_json(path: str, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path: str, data: Any) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def savegame_path(slot: int) -> str:
    return path_in_save(f"savegame_slot{slot}.json")

def highscores_path() -> str:
    return path_in_save(HIGHSCORES_FILE)

def load_highscores() -> Dict[str, Any]:
    hs = load_json(highscores_path(), {"scores": []})
    if "scores" not in hs or not isinstance(hs["scores"], list):
        hs = {"scores": []}
    return hs

def add_highscore(entry: Dict[str, Any]) -> None:
    hs = load_highscores()
    hs["scores"].append(entry)
    hs["scores"].sort(key=lambda x: x.get("score", 0), reverse=True)
    hs["scores"] = hs["scores"][:50]
    save_json(highscores_path(), hs)

def pretty_highscores(limit: int = 15) -> str:
    hs = load_highscores()["scores"][:limit]
    if not hs:
        return "No highscores yet."
    lines = []
    for i, e in enumerate(hs, start=1):
        lines.append(
            f"{i:>2}. {e.get('player','?'):<12}  {e.get('score',0):>6}  "
            f"{e.get('difficulty','?'):<10}  {e.get('case_id','?')}  "
            f"{e.get('minutes',0):>4}m  {e.get('when','')}"
        )
    return "\n".join(lines)

def save_game(sg: SaveGame) -> None:
    ensure_save_dir()
    sg.updated_at = now_iso()
    save_json(savegame_path(sg.slot), asdict(sg))

def load_save_game(slot: int) -> Optional[SaveGame]:
    data = load_json(savegame_path(slot), None)
    if not data:
        return None
    try:
        return SaveGame(**data)
    except Exception:
        return None

def delete_save_game(slot: int) -> None:
    try:
        os.remove(savegame_path(slot))
    except Exception:
        pass

def slot_has_save(slot: int) -> bool:
    return os.path.exists(savegame_path(slot))

# ----------------------------- UI helpers -----------------------------

def banner() -> None:
    clear()
    print("=" * WRAP)
    print(f"{APP_NAME}  —  Terminal Detective Game".center(WRAP))
    print("=" * WRAP)
    print(wrap(SAFETY_NOTE))
    print("=" * WRAP)

def menu_choice(prompt: str, options: List[str]) -> str:
    while True:
        ch = input(prompt).strip()
        if ch in options:
            return ch
        print("Invalid choice.")

def print_block(text: str) -> None:
    print(wrap(text))

def stamp() -> str:
    return datetime.datetime.now().strftime("%H:%M")

def take_note(notes: List[str]) -> None:
    print("\nAdd note. Empty line to finish.")
    while True:
        line = input("> ").rstrip("\n")
        if not line.strip():
            break
        notes.append(f"[{stamp()}] {line}")
    print("Note saved.")

def review_notes(notes: List[str]) -> None:
    print("\n" + "-" * WRAP)
    print("NOTES".center(WRAP))
    print("-" * WRAP)
    if not notes:
        print("(No notes yet.)")
    else:
        for n in notes[-400:]:
            print(wrap(n))
    print("-" * WRAP)

def review_evidence(evidence: List[str]) -> None:
    print("\n" + "-" * WRAP)
    print("EVIDENCE".center(WRAP))
    print("-" * WRAP)
    if not evidence:
        print("(No evidence logged yet.)")
    else:
        for i, e in enumerate(evidence, start=1):
            print(wrap(f"{i}. {e}"))
    print("-" * WRAP)

def show_tutorial_diagrams() -> None:
    banner()
    print_block("ASCII GUIDE (quick visuals)")
    print("-" * WRAP)
    print(wrap(r"""
Evidence Board (sample)
+------------------------------+
|            CASE              |
|                              |
|   [KEY] -----> [METHOD]      |
|     |             |          |
|     v             v          |
| [SUPPORT]      [MOTIVE]      |
|     |             |          |
|     v             v          |
|   [ALIBI] ----> [SUSPECT]    |
|                              |
|   [RED] = loud distraction   |
+------------------------------+

Timeline (sample)
T-90  T-60  T-45  T-30  T-15  T+00  T+15
 |     |     |     |     |     |     |
 Msg  Meet  Log  Sound Restr Disc  Shift

Commands:
:help :guide :note :notes :evidence :board :timeline :hint :save :quit
"""))
    print("-" * WRAP)
    press_enter()

def command_help() -> None:
    print("\nCommands:")
    print("  :help       Show commands")
    print("  :guide      ASCII 'graphic' explanation screens")
    print("  :note       Add a quick note")
    print("  :notes      Review notes")
    print("  :evidence   Review evidence")
    print("  :board      Show evidence board (ASCII)")
    print("  :timeline   Show timeline anchors (ASCII)")
    print("  :hint       Use a hint token to reveal checkpoint hint")
    print("  :save       Save and exit to main menu")
    print("  :quit       Quit without saving\n")

def draw_board(case: Case) -> None:
    sol = case.solution
    key = sol.get("key_evidence", "?")
    method = sol.get("method", "?")
    motive = sol.get("motive", "?")
    sups = sol.get("evidence_support", [])
    reds = sol.get("evidence_red", [])
    banner()
    print_block("EVIDENCE BOARD (ASCII)")
    print("-" * WRAP)
    lines = [
        "+------------------------------------------------------------+",
        "|                         CASE BOARD                         |",
        "+------------------------------------------------------------+",
        f"|  KEY:    {key[:54]:<54} |",
        f"|  METHOD: {method[:54]:<54} |",
        f"|  MOTIVE: {motive[:54]:<54} |",
        "+------------------------------------------------------------+",
        "|  SUPPORT THREADS:                                          |",
    ]
    for s in sups[:6]:
        lines.append(f"|   - {s[:56]:<56} |")
    lines.append("|  RED HERRINGS (LOUD, TEMPTING):                             |")
    for r in reds[:3]:
        lines.append(f"|   - {r[:56]:<56} |")
    lines.append("+------------------------------------------------------------+")
    print("\n".join(lines))
    press_enter()

def draw_timeline(case: Case) -> None:
    anchors = case.solution.get("timeline_anchors", [])
    banner()
    print_block("TIMELINE ANCHORS (ASCII)")
    print("-" * WRAP)
    labels = ["T-90","T-60","T-45","T-30","T-15","T+00","T+15"]
    print(" ".join([l.ljust(7) for l in labels]))
    print(" ".join(["|".ljust(7) for _ in labels]))
    order = {lab:i for i,lab in enumerate(labels)}
    events = [""] * len(labels)
    for lab, desc in anchors:
        if lab in order:
            events[order[lab]] = desc
    wraps = [textwrap.wrap(events[i], width=7) or [""] for i in range(len(labels))]
    max_lines = max(len(w) for w in wraps)
    for li in range(max_lines):
        row = []
        for i in range(len(labels)):
            part = wraps[i][li] if li < len(wraps[i]) else ""
            row.append(part.ljust(7))
        print(" ".join(row))
    print("-" * WRAP)
    print_block("Anchors are not full truth. Use them to break alibis.")
    press_enter()

def handle_command(cmd: str, sg: SaveGame, case: Case, current_scene: Optional[Scene]) -> Optional[str]:
    if cmd == ":help":
        command_help()
        return None
    if cmd == ":guide":
        show_tutorial_diagrams()
        return None
    if cmd == ":note":
        take_note(sg.notes)
        save_game(sg)
        return None
    if cmd == ":notes":
        review_notes(sg.notes)
        press_enter()
        return None
    if cmd == ":evidence":
        review_evidence(sg.evidence)
        press_enter()
        return None
    if cmd == ":board":
        draw_board(case)
        return None
    if cmd == ":timeline":
        draw_timeline(case)
        return None
    if cmd == ":hint":
        if current_scene is None:
            print("No active scene.")
            return None
        if sg.hint_tokens_left <= 0:
            print("No hint tokens left on this difficulty.")
            time.sleep(1.0)
            return None
        sg.hint_tokens_left -= 1
        save_game(sg)
        print(f"Hint token used. Remaining: {sg.hint_tokens_left}")
        print_block("HINT: " + current_scene.hint)
        press_enter()
        return "hint_requested"
    if cmd == ":save":
        save_game(sg)
        print("Saved.")
        time.sleep(0.8)
        return "save_menu"
    if cmd == ":quit":
        return "quit_nosave"
    return None

# ----------------------------- Serialization -----------------------------

def _case_to_dict(case: Case) -> Dict[str, Any]:
    return {
        "case_id": case.case_id,
        "title": case.title,
        "case_type": case.case_type,
        "difficulty_key": case.difficulty_key,
        "setup": case.setup,
        "suspects": case.suspects,
        "scenes": [
            {
                "title": sc.title,
                "intro": sc.intro,
                "actions": [asdict(a) for a in sc.actions],
                "checkpoint_question": sc.checkpoint_question,
                "checkpoint_answers": sc.checkpoint_answers,
                "hint": sc.hint,
                "checkpoint_evidence_add": sc.checkpoint_evidence_add,
            } for sc in case.scenes
        ],
        "solution": case.solution,
    }

def _dict_to_case(data: Dict[str, Any]) -> Case:
    scenes = []
    for sc in data["scenes"]:
        acts = [Action(**a) for a in sc["actions"]]
        scenes.append(Scene(
            title=sc["title"],
            intro=sc["intro"],
            actions=acts,
            checkpoint_question=sc["checkpoint_question"],
            checkpoint_answers=sc["checkpoint_answers"],
            hint=sc["hint"],
            checkpoint_evidence_add=sc["checkpoint_evidence_add"],
        ))
    return Case(
        case_id=data["case_id"],
        title=data["title"],
        case_type=data["case_type"],
        difficulty_key=data["difficulty_key"],
        setup=data["setup"],
        suspects=data["suspects"],
        scenes=scenes,
        solution=data["solution"],
    )

# ----------------------------- Gameplay -----------------------------

def choose_difficulty() -> str:
    banner()
    print_block("Choose difficulty:")
    for k in sorted(DIFFICULTIES.keys()):
        d = DIFFICULTIES[k]
        print(f"  [{k}] {d['name']:<10}  hint tokens: {d['hint_tokens']}  min actions/scene: {d['min_actions']}")
    print()
    return menu_choice("Difficulty: ", list(DIFFICULTIES.keys()))

def choose_case_blueprint() -> Dict[str, Any]:
    import random
    return random.choice(BLUEPRINTS)

def first_time_player_name() -> str:
    ensure_save_dir()
    cfg_path = path_in_save("player.json")
    cfg = load_json(cfg_path, {})
    if isinstance(cfg, dict) and cfg.get("player"):
        return str(cfg["player"])
    banner()
    print_block("Enter your detective name (used for highscores):")
    name = input("> ").strip()[:24] or "Detective"
    save_json(cfg_path, {"player": name})
    return name

def pick_slot_for_new_case() -> int:
    banner()
    print_block("Choose a SAVE SLOT for this case:")
    for s in SAVE_SLOTS:
        status = "USED" if slot_has_save(s) else "EMPTY"
        print(f"  [{s}] Slot {s} — {status}")
    print()
    ch = menu_choice("Slot: ", [str(s) for s in SAVE_SLOTS])
    slot = int(ch)
    if slot_has_save(slot):
        banner()
        print_block(f"Slot {slot} already has a saved case.")
        overwrite = menu_choice("Overwrite? [y/n]: ", ["y","n","Y","N"])
        if overwrite.lower() != "y":
            return pick_slot_for_new_case()
        delete_save_game(slot)
    return slot

def pick_slot_to_load() -> Optional[int]:
    banner()
    print_block("Load which slot?")
    available = []
    for s in SAVE_SLOTS:
        if slot_has_save(s):
            sg = load_save_game(s)
            label = f"{sg.case.get('case_id','?')} — {sg.case.get('title','?')}" if sg else "(corrupt save)"
            print(f"  [{s}] Slot {s} — {label}")
            available.append(str(s))
        else:
            print(f"  [{s}] Slot {s} — EMPTY")
    if not available:
        print("\nNo saves found.")
        press_enter()
        return None
    print("  [B] Back")
    ch = menu_choice("Choice: ", available + ["B","b"])
    if ch.lower() == "b":
        return None
    return int(ch)

def new_case_flow(player: str) -> None:
    difficulty_key = choose_difficulty()
    slot = pick_slot_for_new_case()
    bp = choose_case_blueprint()
    case = build_case(bp, difficulty_key)
    sg = SaveGame(
        version=4,
        slot=slot,
        created_at=now_iso(),
        updated_at=now_iso(),
        case=_case_to_dict(case),
        scene_index=0,
        seen_actions={},
        notes=[],
        evidence=[],
        hint_tokens_left=DIFFICULTIES[difficulty_key]["hint_tokens"],
        start_time_epoch=time.time(),
    )
    save_game(sg)
    play_case(sg, player)

def continue_case_flow(player: str) -> None:
    slot = pick_slot_to_load()
    if slot is None:
        return
    sg = load_save_game(slot)
    if not sg:
        banner()
        print("Save could not be loaded.")
        press_enter()
        return
    play_case(sg, player)

def play_case(sg: SaveGame, player: str) -> None:
    ensure_save_dir()
    case = _dict_to_case(sg.case)
    diff = DIFFICULTIES[case.difficulty_key]

    banner()
    print_block(f"Player: {player}   Difficulty: {diff['name']}   Slot: {sg.slot}")
    print("=" * WRAP)
    print_block(case.setup)
    print("=" * WRAP)
    print_block("Tip: type :guide for ASCII visuals. Type :help for commands.")
    press_enter()

    while sg.scene_index < len(case.scenes):
        scene = case.scenes[sg.scene_index]
        min_actions = diff["min_actions"]
        key = str(sg.scene_index)
        if key not in sg.seen_actions:
            sg.seen_actions[key] = []

        while True:
            banner()
            mins = minutes_elapsed(sg.start_time_epoch)
            remaining = max(0, REQUIRED_MINUTES_PER_CASE - mins)

            print_block(f"CASE {case.case_id}: {case.title}")
            print("-" * WRAP)
            print_block(f"Scene {sg.scene_index + 1}/{len(case.scenes)} — {scene.title}")
            print("-" * WRAP)
            print_block(scene.intro)
            print()
            print("Actions:")
            for i, a in enumerate(scene.actions, start=1):
                seen = "✓" if (i-1) in sg.seen_actions[key] else " "
                print(f"  [{i}] ({seen}) {a.label}")
            print()
            print(f"Progress: actions viewed {len(sg.seen_actions[key])}/{len(scene.actions)} "
                  f"(need {min_actions} before checkpoint).  Hint tokens: {sg.hint_tokens_left}")
            if remaining > 0:
                print(f"Long Case Timer: {mins}m elapsed — accusation unlocks in {remaining}m.")
            else:
                print(f"Long Case Timer: {mins}m elapsed — accusation UNLOCKED.")
            print("\nType a number to act, 'C' for checkpoint, or :help.\n")

            choice = input("> ").strip()

            if choice.startswith(":"):
                action_res = handle_command(choice, sg, case, scene)
                if action_res == "save_menu":
                    return
                if action_res == "quit_nosave":
                    banner()
                    print("Progress not saved.")
                    press_enter()
                    return
                continue

            if choice.lower() == "c":
                if len(sg.seen_actions[key]) < min_actions:
                    print(f"You should explore more first. Need at least {min_actions} actions on this difficulty.")
                    time.sleep(1.2)
                    continue

                banner()
                print_block(f"CHECKPOINT — {scene.title}")
                print("-" * WRAP)
                print_block("Answer based on what you read and what you wrote down.")
                print()
                ans = input(scene.checkpoint_question + "\n> ").strip()

                if ans.startswith(":"):
                    action_res = handle_command(ans, sg, case, scene)
                    if action_res == "save_menu":
                        return
                    if action_res == "quit_nosave":
                        banner()
                        print("Progress not saved.")
                        press_enter()
                        return
                    continue

                if normalize(ans) in [normalize(a) for a in scene.checkpoint_answers]:
                    for e in scene.checkpoint_evidence_add:
                        if e not in sg.evidence:
                            sg.evidence.append(e)
                    sg.scene_index += 1
                    save_game(sg)
                    break
                else:
                    print("Not quite. Re-read the scene, your notes, and your evidence.")
                    print("Tip: use :hint if you have tokens.")
                    time.sleep(1.4)
                    continue

            idx = safe_int(choice, -1)
            if 1 <= idx <= len(scene.actions):
                a = scene.actions[idx-1]
                if (idx-1) not in sg.seen_actions[key]:
                    sg.seen_actions[key].append(idx-1)

                banner()
                print_block(f"{scene.title} — {a.label}")
                print("-" * WRAP)
                print_block(a.text)

                for e in a.evidence_add:
                    if e and e not in sg.evidence:
                        sg.evidence.append(e)

                if a.note_prompt:
                    print()
                    print_block("Note prompt: " + a.note_prompt)
                    if input("Add a note now? (y/n) > ").strip().lower().startswith("y"):
                        line = input("Note > ").rstrip("\n")
                        if line.strip():
                            sg.notes.append(f"[{stamp()}] {line}")

                save_game(sg)
                press_enter()
                continue

            print("Choose an action number, 'C' for checkpoint, or a command like :help.")
            time.sleep(1.0)

    accusation_phase(sg, case, player)

def accusation_phase(sg: SaveGame, case: Case, player: str) -> None:
    diff = DIFFICULTIES[case.difficulty_key]
    sol = case.solution
    culprit = sol["culprit_name"]

    def suspect_dialogue(name: str) -> Dict[str, str]:
        evasive = (normalize(name) == normalize(culprit))
        base = {
            "alibi": "I already told the officer where I was. Same story.",
            "victim": "We had history. Complicated, but not violent.",
            "evidence": "You're looking at the wrong thing. People always do.",
            "pressure": "I don't like this. Let's keep it professional.",
            "detail": "I remember the small things: a sound, a glance, the order people moved.",
        }
        if evasive:
            base["alibi"] = "I was around, in and out. Time gets fuzzy during stressful nights."
            base["victim"] = "They were... intense. Some people make enemies by breathing."
            base["evidence"] = "That could mean anything. You're reading into it."
            base["pressure"] = "If this turns into a spectacle, everyone loses."
            base["detail"] = "It's hard to recall. Everything happened so fast."
        else:
            base["alibi"] = "I can give you a clean sequence. I remember because it was unusual."
            base["victim"] = "They were scared of something. I thought it was paranoia."
            base["evidence"] = "If you check the logs properly, you'll see what I mean."
            base["pressure"] = "Do what you have to do. Just don't let them twist it."
            base["detail"] = "Ask the others why their times don't match their movements."
        return base

    while True:
        banner()
        mins = minutes_elapsed(sg.start_time_epoch)
        remaining = max(0, REQUIRED_MINUTES_PER_CASE - mins)
        print_block("ACCUSATION PHASE")
        print("-" * WRAP)
        if remaining > 0:
            print_block(f"Accusation is LOCKED until {REQUIRED_MINUTES_PER_CASE} minutes have passed.")
            print_block(f"Elapsed: {mins}m. Remaining: {remaining}m.")
            print()
            print_block("Use this time to interrogate, review, and tighten your theory.")
        else:
            print_block(f"Accusation is UNLOCKED (elapsed: {mins}m).")
        print()
        print("Menu:")
        print("  [1] Review evidence")
        print("  [2] Review notes")
        print("  [3] Interrogate a suspect")
        print("  [4] View evidence board (ASCII)")
        print("  [5] View timeline (ASCII)")
        print("  [6] Accuse" + (" (LOCKED)" if remaining > 0 else ""))
        print("  [7] Save and exit to menu")
        print()
        ch = menu_choice("Choice: ", ["1","2","3","4","5","6","7"])

        if ch == "1":
            banner()
            review_evidence(sg.evidence)
            press_enter()
        elif ch == "2":
            banner()
            review_notes(sg.notes)
            press_enter()
        elif ch == "3":
            banner()
            print("Suspects:")
            for i, s in enumerate(case.suspects, start=1):
                print(wrap(f"  [{i}] {s['name']} — {s['role']}: {s['summary']}"))
            sidx = menu_choice("\nPick suspect (1-4) or B to go back: ", ["1","2","3","4","B","b"])
            if sidx.lower() == "b":
                continue
            sname = case.suspects[int(sidx)-1]["name"]
            dlg = suspect_dialogue(sname)
            while True:
                banner()
                print_block(f"Interrogation: {sname}")
                print("-" * WRAP)
                print("Ask about:")
                print("  [1] Alibi")
                print("  [2] Relationship with victim")
                print("  [3] Evidence interpretation")
                print("  [4] Pressure / motive angle")
                print("  [5] Specific detail")
                print("  [6] Back")
                q = menu_choice("Choice: ", ["1","2","3","4","5","6"])
                if q == "6":
                    break
                k = {"1":"alibi","2":"victim","3":"evidence","4":"pressure","5":"detail"}[q]
                banner()
                print_block(f"{sname} says:")
                print("-" * WRAP)
                print_block(dlg[k])
                if input("\nAdd this to notes? (y/n) > ").strip().lower().startswith("y"):
                    sg.notes.append(f"[{stamp()}] {sname}: {dlg[k]}")
                    save_game(sg)
                press_enter()
        elif ch == "4":
            draw_board(case)
        elif ch == "5":
            draw_timeline(case)
        elif ch == "7":
            save_game(sg)
            banner()
            print("Saved.")
            press_enter()
            return
        elif ch == "6":
            if remaining > 0:
                banner()
                print_block(f"Accusation is still locked. Wait {remaining} more minutes.")
                print_block("Tip: interrogate suspects and refine notes while time passes.")
                press_enter()
                continue
            break

    banner()
    print_block("ACCUSATION")
    print("-" * WRAP)
    for i, s in enumerate(case.suspects, start=1):
        print(wrap(f"  [{i}] {s['name']} — {s['role']}: {s['summary']}"))
    print()

    while True:
        ch = input("Accuse suspect number (1-4) > ").strip()
        idx = safe_int(ch, -1)
        if idx in (1,2,3,4):
            accused = case.suspects[idx-1]["name"]
            break
        print("Choose 1-4.")

    banner()
    print_block("FINAL DEDUCTIONS")
    print("-" * WRAP)
    q1 = input("1) What was the KEY EVIDENCE? (short phrase)\n> ").strip()
    q2 = input("2) What was the METHOD? (short phrase)\n> ").strip()
    q3 = input("3) What was the MOTIVE? (short phrase)\n> ").strip()

    elapsed_min = max(1, minutes_elapsed(sg.start_time_epoch))

    correct_accuse = (normalize(accused) == normalize(sol["culprit_name"]))
    key_ok = (normalize(sol["key_evidence"]) in normalize(q1) or normalize(q1) in normalize(sol["key_evidence"]))
    method_ok = (normalize(sol["method"]) in normalize(q2) or normalize(q2) in normalize(sol["method"]))
    motive_ok = (normalize(sol["motive"]) in normalize(q3) or normalize(q3) in normalize(sol["motive"]))

    base = 1400
    base += 700 if correct_accuse else 0
    base += 240 if key_ok else 0
    base += 240 if method_ok else 0
    base += 240 if motive_ok else 0

    note_bonus = min(450, len(sg.notes) * 12)
    base += note_bonus

    t = elapsed_min
    if t < 40:
        time_factor = 0.85
    elif t < 55:
        time_factor = 1.12
    elif t < 75:
        time_factor = 1.18
    else:
        time_factor = 1.14

    score = int(base * time_factor * diff["time_bonus"])

    banner()
    print_block(("✅ Correct. " if correct_accuse else "❌ Incorrect. ") + f"You accused {accused}.")
    print()
    print_block("Case Resolution:")
    print_block(sol["explanation"])
    print()
    print("Your deductions:")
    print(f"  Key evidence: {'OK' if key_ok else 'MISS'}")
    print(f"  Method:       {'OK' if method_ok else 'MISS'}")
    print(f"  Motive:       {'OK' if motive_ok else 'MISS'}")
    print(f"  Notes bonus:  +{note_bonus}")
    print(f"  Time:         {elapsed_min} minutes")
    print(f"  Score:        {score}")
    print()

    add_highscore({
        "player": player,
        "score": score,
        "difficulty": diff["name"],
        "case_id": case.case_id,
        "minutes": elapsed_min,
        "correct": bool(correct_accuse),
        "when": now_iso(),
    })

    delete_save_game(sg.slot)
    press_enter()

# ----------------------------- Menus -----------------------------

def show_highscores() -> None:
    banner()
    print_block("HIGHSCORES (Top 15)")
    print("-" * WRAP)
    print(pretty_highscores(15))
    print("-" * WRAP)
    press_enter()

def settings_screen() -> None:
    banner()
    print_block("Settings / Info")
    print("-" * WRAP)
    print_block("All data is saved in: " + save_dir())
    print()
    print("Files:")
    print(" - " + highscores_path())
    for s in SAVE_SLOTS:
        print(" - " + savegame_path(s))
    print("-" * WRAP)
    press_enter()

def main_menu() -> None:
    ensure_save_dir()
    player = first_time_player_name()
    while True:
        banner()
        print_block(f"Welcome, {player}.")
        print()
        print(f"Stories available (fixed): {len(BLUEPRINTS)}  |  Long case minimum: {REQUIRED_MINUTES_PER_CASE} minutes")
        print()
        print("  [1] New Case (random from fixed library)")
        print("  [2] Load Case (choose slot)")
        print("  [3] Highscores")
        print("  [4] ASCII Guide (graphics)")
        print("  [5] Settings / Save Folder Info")
        print("  [6] Quit")
        print()
        ch = menu_choice("Choice: ", ["1","2","3","4","5","6"])
        if ch == "1":
            new_case_flow(player)
        elif ch == "2":
            continue_case_flow(player)
        elif ch == "3":
            show_highscores()
        elif ch == "4":
            show_tutorial_diagrams()
        elif ch == "5":
            settings_screen()
        elif ch == "6":
            banner()
            print("Goodbye.")
            return

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nExiting.")
