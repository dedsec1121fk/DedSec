#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import re
import signal
import socket
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# ─────────────────────────────────────────────
#  ANSI ΧΡΩΜΑΤΑ (λειτουργούν στο Termux terminal)
# ─────────────────────────────────────────────
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
WHITE = "\033[97m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

USE_COLOR = True
EXIT_REQUESTED = False


def ccolor(color, text):
    if USE_COLOR:
        return f"{color}{text}{RESET}"
    return text


def banner():
    print(ccolor(CYAN + BOLD, "\n  Devices Finder v3.2"))
    print(ccolor(DIM, "  ------------------"))
    print(ccolor(YELLOW, "  ⚠ Μόνο για συσκευές στο δικό σου δίκτυο."))
    print()


def info(msg):
    print(ccolor(CYAN, "  [*] ") + msg)


def success(msg):
    print(ccolor(GREEN, "  [+] ") + msg)


def warn(msg):
    print(ccolor(YELLOW, "  [!] ") + msg)


def error(msg):
    print(ccolor(RED, "  [-] ") + msg)


def divider():
    print(ccolor(DIM, "  ------------------"))


def signal_handler(sig, frame):
    global EXIT_REQUESTED
    if not EXIT_REQUESTED:
        EXIT_REQUESTED = True
        print(ccolor(YELLOW, "\n\n  [!] Ελήφθη διακοπή. Έξοδος με ασφαλή τερματισμό..."))
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


# ─────────────────────────────────────────────
#  ΠΡΟΕΠΙΛΕΓΜΕΝΟΣ ΦΑΚΕΛΟΣ ΕΞΟΔΟΥ
# ─────────────────────────────────────────────
def resolve_default_output_dir():
    candidates = [
        os.path.expanduser("~/storage/downloads/Devices Finder GR"),
        os.path.expanduser("~/downloads/Devices Finder GR"),
        os.path.join(os.getcwd(), "Έξοδος Devices Finder GR"),
    ]
    for candidate in candidates:
        try:
            Path(candidate).mkdir(parents=True, exist_ok=True)
            return candidate
        except Exception:
            continue
    return os.getcwd()


DEFAULT_OUTPUT_DIR = resolve_default_output_dir()


# ─────────────────────────────────────────────
#  ΕΞΑΡΤΗΣΕΙΣ
# ─────────────────────────────────────────────
def install_dependency(package, is_pip=False):
    if is_pip:
        cmd = [sys.executable, "-m", "pip", "install", package]
        info(f"Εγκατάσταση Python πακέτου: {package}")
    else:
        cmd = ["pkg", "install", "-y", package]
        info(f"Εγκατάσταση system πακέτου: {package}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            success(f"Εγκαταστάθηκε: {package}")
            return True
        error(result.stderr.strip() or f"Δεν ήταν δυνατή η εγκατάσταση του {package}")
        return False
    except Exception as exc:
        error(f"Σφάλμα εγκατάστασης για {package}: {exc}")
        return False



def command_exists(command):
    try:
        result = subprocess.run([command, "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False



def check_dependencies(deep_scan=False):
    info("Έλεγχος εξαρτήσεων...")
    missing = []

    if not command_exists("nmap"):
        missing.append(("nmap", False))

    try:
        import nmap  # noqa: F401
    except ImportError:
        missing.append(("python-nmap", True))

    if deep_scan:
        if not command_exists("avahi-resolve-address"):
            missing.append(("avahi", False))
        if not command_exists("snmpget"):
            missing.append(("net-snmp", False))
        if not command_exists("nmblookup"):
            missing.append(("samba", False))

    if not missing:
        divider()
        return True

    warn("Βρέθηκαν ελλείπουσες εξαρτήσεις. Προσπάθεια αυτόματης εγκατάστασης...")
    all_ok = True
    for package, is_pip in missing:
        if not install_dependency(package, is_pip=is_pip):
            all_ok = False

    if not all_ok:
        error("Ορισμένες εξαρτήσεις δεν μπόρεσαν να εγκατασταθούν αυτόματα.")
        print(ccolor(WHITE, "  Εγκατέστησέ τες χειροκίνητα με:"))
        for package, is_pip in missing:
            if is_pip:
                print(ccolor(WHITE, f"    pip install {package}"))
            else:
                print(ccolor(WHITE, f"    pkg install {package}"))
        sys.exit(1)

    divider()
    return True


# ─────────────────────────────────────────────
#  ΒΟΗΘΗΤΙΚΑ ΔΙΚΤΥΟΥ
# ─────────────────────────────────────────────
def run_command(cmd, timeout=10):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result.stdout
    except Exception:
        return ""
    return ""



def get_local_subnet():
    """Εντοπισμός τοπικής IP και subnet χωρίς να απαιτείται root."""
    # Μέθοδος 1: κόλπο διαδρομής με UDP socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("1.1.1.1", 80))
        local_ip = sock.getsockname()[0]
        sock.close()
        subnet = local_ip.rsplit(".", 1)[0] + ".0/24"
        success(f"Εντοπίστηκε τοπική IP → {local_ip}")
        return subnet, local_ip
    except Exception:
        pass

    # Μέθοδος 2: ip route
    route = run_command(["ip", "-4", "route"])
    if route:
        src_match = re.search(r"src\s+(\d+\.\d+\.\d+\.\d+)", route)
        cidr_match = re.search(r"(\d+\.\d+\.\d+\.\d+/\d+)", route)
        local_ip = src_match.group(1) if src_match else None
        subnet = cidr_match.group(1) if cidr_match else None
        if local_ip and subnet:
            success(f"Εντοπίστηκε τοπική IP μέσω ip route → {local_ip}")
            return subnet, local_ip
        if local_ip:
            subnet = local_ip.rsplit(".", 1)[0] + ".0/24"
            success(f"Εντοπίστηκε τοπική IP μέσω ip route → {local_ip}")
            return subnet, local_ip

    # Μέθοδος 3: ifconfig
    output = run_command(["ifconfig"])
    if output:
        match = re.search(r"inet\s(?:addr:)?(\d+\.\d+\.\d+\.\d+)", output)
        if match:
            local_ip = match.group(1)
            subnet = local_ip.rsplit(".", 1)[0] + ".0/24"
            success(f"Εντοπίστηκε τοπική IP μέσω ifconfig → {local_ip}")
            return subnet, local_ip

    error("Δεν ήταν δυνατός ο αυτόματος εντοπισμός subnet.")
    return None, None



def expand_exclude_list(exclude_list):
    return ",".join(item.strip() for item in exclude_list.split(",") if item.strip())


# ─────────────────────────────────────────────
#  ΒΟΗΘΗΤΙΚΑ MAC / ΚΑΤΑΣΚΕΥΑΣΤΗ
# ─────────────────────────────────────────────
MAC_VENDORS = {
    "00:50:56": "VMware",
    "08:00:27": "Oracle VirtualBox",
    "3c:5a:b4": "Google",
    "44:65:0d": "Amazon",
    "00:1e:4f": "Apple",
    "28:6e:d4": "Apple",
    "2c:54:2d": "Apple",
    "4c:8b:30": "Apple",
    "60:30:d4": "Apple",
    "6c:70:9f": "Apple",
    "7c:6b:52": "Apple",
    "84:8e:0c": "Apple",
    "90:0c:27": "Apple",
    "b8:27:eb": "Raspberry Pi",
    "dc:a6:32": "Raspberry Pi",
    "e4:5f:01": "Raspberry Pi",
    "00:11:32": "Synology",
    "00:0c:29": "VMware",
    "00:1c:42": "Parallels",
    "00:50:f2": "Microsoft",
}



def normalize_mac(mac):
    if not mac:
        return ""
    return mac.lower().replace("-", ":")



def lookup_mac_vendor(mac):
    mac = normalize_mac(mac)
    if not mac:
        return ""
    parts = mac.split(":")
    if len(parts) < 3:
        return ""
    oui = ":".join(parts[:3])
    return MAC_VENDORS.get(oui, "")


# ─────────────────────────────────────────────
#  ΘΥΡΕΣ / ΥΠΟΓΡΑΦΕΣ
# ─────────────────────────────────────────────
PORT_CATEGORIES = {
    "balanced": [
        22, 23, 53, 80, 81, 88, 139, 443, 445, 515, 548, 554,
        631, 1025, 1400, 3389, 5357, 5900, 7000, 7001, 8000,
        8008, 8009, 8060, 8080, 8081, 8089, 8443, 8554, 8888,
        9000, 9100, 32400, 49152, 49153, 49154, 62078
    ],
    "cameras": [554, 8000, 8089, 8554, 9000, 34567, 37777, 37810, 49152, 49153, 49154, 80, 443, 8080, 8443],
    "media": [80, 443, 7000, 7001, 8008, 8009, 8060, 8443, 32400],
    "workstation": [22, 80, 139, 443, 445, 548, 3389, 5900],
    "printer": [80, 443, 515, 631, 5357, 8080, 8443, 9100],
}
DEFAULT_PORTS = sorted(set(PORT_CATEGORIES["balanced"]))

PORT_LABELS = {
    22: "SSH",
    23: "Telnet",
    53: "DNS",
    80: "HTTP",
    81: "HTTP Alt",
    88: "HTTP Alt",
    139: "NetBIOS",
    443: "HTTPS",
    445: "SMB",
    515: "Εκτυπωτής LPD",
    548: "AFP",
    554: "RTSP",
    631: "Εκτυπωτής IPP",
    1025: "RPC / Service",
    1400: "Sonos",
    3389: "RDP",
    5357: "Εκτυπωτής WSD",
    5900: "VNC",
    7000: "AirPlay",
    7001: "AirPlay TLS",
    8000: "SDK / Alt HTTP",
    8008: "Chromecast HTTP",
    8009: "Chromecast Cast",
    8060: "Roku ECP",
    8080: "HTTP Alt",
    8081: "HTTP Alt",
    8089: "V380 / Alt",
    8443: "HTTPS Alt",
    8554: "RTSP Alt",
    8888: "HTTP Alt",
    9000: "Vendor SDK",
    9100: "Εκτυπωτής Raw",
    32400: "Plex",
    34567: "Dahua DVR",
    37777: "Dahua SDK",
    37810: "Dahua Alt",
    49152: "ONVIF / Dynamic",
    49153: "ONVIF / Dynamic",
    49154: "ONVIF / Dynamic",
    62078: "iPhone / iPad Sync",
}

GENERIC_WEB_PORTS = {80, 81, 88, 443, 8080, 8081, 8443, 8888}
CAMERA_PORTS = {554, 8000, 8089, 8554, 9000, 34567, 37777, 37810, 49152, 49153, 49154}
PRINTER_PORTS = {515, 631, 5357, 9100}
STORAGE_PORTS = {139, 445, 548}
MEDIA_PORTS = {7000, 7001, 8008, 8009, 8060, 32400, 1400}
PC_PORTS = {22, 3389, 5900, 139, 445}
PHONE_PORTS = {62078, 7000, 7001}

TYPE_HINTS = {
    "camera": ["camera", "webcam", "ipcam", "cctv", "nvr", "dvr", "hikvision", "dahua", "reolink", "onvif", "v380", "foscam", "amcrest", "rtsp"],
    "printer": ["printer", "laserjet", "officejet", "inkjet", "brother", "epson", "canon", "cups", "ipp", "wsd"],
    "router": ["router", "gateway", "openwrt", "mikrotik", "ubiquiti", "edgeos", "asuswrt", "fritz", "tp-link", "netgear", "linksys"],
    "storage": ["nas", "synology", "qnap", "diskstation", "truenas", "freenas", "smb", "afp"],
    "pc": ["windows", "ubuntu", "debian", "linux", "fedora", "macos", "workstation", "desktop", "server", "rdp", "vnc", "ssh"],
    "phone": ["iphone", "ipad", "android", "smartphone", "mobile"],
    "tv": ["roku", "chromecast", "bravia", "webos", "tizen", "smart tv", "appletv", "apple tv", "shield", "plex"],
    "speaker": ["sonos", "bose", "alexa", "echo", "google home", "homepod", "speaker"],
    "game_console": ["playstation", "xbox", "nintendo", "ps4", "ps5", "switch"],
    "iot": ["shelly", "tasmota", "esphome", "home assistant", "smart plug", "tuya"],
    "vm": ["vmware", "virtualbox", "parallels", "hyper-v"],
}


# ─────────────────────────────────────────────
#  ΣΥΝΑΡΤΗΣΕΙΣ ΕΝΤΟΠΙΣΜΟΥ (ευρύς εντοπισμός συσκευών)
# ─────────────────────────────────────────────
def host_sort_key(ip):
    try:
        return tuple(int(part) for part in ip.split("."))
    except Exception:
        return (999, 999, 999, 999)



def add_discovery_record(records, ip, source, mac="", note=""):
    if not ip:
        return
    rec = records.setdefault(
        ip,
        {
            "ip": ip,
            "mac": "",
            "discovery_sources": set(),
            "discovery_notes": [],
        },
    )
    if mac and not rec.get("mac"):
        rec["mac"] = normalize_mac(mac)
    rec["discovery_sources"].add(source)
    if note and note not in rec["discovery_notes"]:
        rec["discovery_notes"].append(note)



def discover_from_proc_arp(records):
    try:
        with open("/proc/net/arp", "r", encoding="utf-8", errors="ignore") as handle:
            lines = handle.readlines()[1:]
        for line in lines:
            parts = line.split()
            if len(parts) >= 6:
                ip = parts[0]
                mac = parts[3]
                if mac != "00:00:00:00:00:00":
                    add_discovery_record(records, ip, "arp", mac=mac, note="Seen in ARP cache")
    except Exception:
        pass



def discover_from_ip_neigh(records):
    output = run_command(["ip", "neigh", "show"])
    if not output:
        return
    for line in output.splitlines():
        match = re.search(r"^(\d+\.\d+\.\d+\.\d+).+lladdr\s+([0-9a-fA-F:]{17}).*\s(REACHABLE|STALE|DELAY|PROBE|PERMANENT)$", line.strip())
        if match:
            ip, mac, state = match.groups()
            add_discovery_record(records, ip, "ip_neigh", mac=mac, note=f"Neighbor table state: {state}")



def discover_from_nmap_ping(subnet, timing="T4", exclude_targets=None):
    import nmap

    nm = nmap.PortScanner()
    args = f"-sn -n -{timing}"
    if exclude_targets:
        args += f" --exclude {exclude_targets}"
    nm.scan(hosts=subnet, arguments=args)
    results = {}
    for host in nm.all_hosts():
        status = nm[host].state() if "status" in nm[host] else "up"
        mac = ""
        if "addresses" in nm[host]:
            mac = nm[host]["addresses"].get("mac", "")
        results[host] = {"status": status, "mac": mac}
    return results



def calculate_presence_confidence(sources, mac=""):
    score = 0
    if "nmap_ping" in sources:
        score += 65
    if "arp" in sources:
        score += 20
    if "ip_neigh" in sources:
        score += 20
    if mac:
        score += 10
    return min(score, 100)



def discover_hosts(subnet, local_ip=None, exclude_self=False, exclude_targets=None, timing="T4"):
    records = {}

    discover_from_proc_arp(records)
    discover_from_ip_neigh(records)

    try:
        ping_results = discover_from_nmap_ping(subnet, timing=timing, exclude_targets=exclude_targets)
        for ip, payload in ping_results.items():
            add_discovery_record(records, ip, "nmap_ping", mac=payload.get("mac", ""), note="Responded to host discovery")
    except Exception as exc:
        warn(f"Η ανακάλυψη hosts με Nmap απέτυχε, συνέχεια μόνο με ARP/neigh: {exc}")

    if exclude_self and local_ip and local_ip in records:
        records.pop(local_ip, None)

    for rec in records.values():
        rec["presence_confidence"] = calculate_presence_confidence(rec.get("discovery_sources", set()), rec.get("mac", ""))
        rec["vendor"] = lookup_mac_vendor(rec.get("mac", ""))

    return dict(sorted(records.items(), key=lambda item: host_sort_key(item[0])))


# ─────────────────────────────────────────────
#  ΒΟΗΘΗΤΙΚΑ ΕΜΠΛΟΥΤΙΣΜΟΥ
# ─────────────────────────────────────────────
def reverse_dns(ip):
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except Exception:
        return ""



def mdns_name(ip):
    try:
        result = subprocess.run(["avahi-resolve-address", ip], capture_output=True, text=True, timeout=4)
        if result.returncode == 0:
            parts = result.stdout.strip().split()
            if len(parts) >= 2:
                return parts[1]
    except Exception:
        return ""
    return ""



def upnp_probe(ip):
    payload = (
        "M-SEARCH * HTTP/1.1\r\n"
        "HOST:239.255.255.250:1900\r\n"
        'MAN:"ssdp:discover"\r\n'
        "MX:1\r\n"
        "ST:ssdp:all\r\n\r\n"
    )
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(2.5)
    try:
        sock.sendto(payload.encode(), (ip, 1900))
        data, _ = sock.recvfrom(4096)
        text = data.decode(errors="ignore")
        headers = {}
        for line in text.split("\r\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()
        return {
            "server": headers.get("server", ""),
            "location": headers.get("location", ""),
            "st": headers.get("st", ""),
            "usn": headers.get("usn", ""),
        }
    except Exception:
        return {}
    finally:
        sock.close()



def snmp_info(ip):
    info_map = {}
    oids = {
        "sysname": "1.3.6.1.2.1.1.5.0",
        "description": "1.3.6.1.2.1.1.1.0",
    }
    for key, oid in oids.items():
        try:
            result = subprocess.run(
                ["snmpget", "-v2c", "-c", "public", "-t", "2", ip, oid],
                capture_output=True,
                text=True,
                timeout=4,
            )
            if result.returncode == 0:
                match = re.search(r"=\s+.*?:\s+(.+)", result.stdout)
                if match:
                    info_map[key] = match.group(1).strip()
        except Exception:
            continue
    return info_map



def netbios_info(ip):
    try:
        result = subprocess.run(["nmblookup", "-A", ip], capture_output=True, text=True, timeout=4)
        if result.returncode != 0:
            return []
        names = []
        for line in result.stdout.splitlines():
            if "<" in line and ">" in line:
                cleaned = line.strip()
                name = cleaned.split()[0]
                if name and name not in names:
                    names.append(name)
        return names[:5]
    except Exception:
        return []



def enrich_device(ip, deep_scan=False):
    data = {}
    hostname = reverse_dns(ip)
    if hostname:
        data["hostname"] = hostname
    if deep_scan:
        mdns = mdns_name(ip)
        if mdns:
            data["mdns_name"] = mdns
        upnp = upnp_probe(ip)
        if upnp:
            data["upnp"] = upnp
        snmp = snmp_info(ip)
        if snmp:
            data["snmp"] = snmp
        netbios = netbios_info(ip)
        if netbios:
            data["netbios"] = netbios
    return data


# ─────────────────────────────────────────────
#  ΣΑΡΩΣΗ ΥΠΗΡΕΣΙΩΝ / ΤΑΞΙΝΟΜΗΣΗ
# ─────────────────────────────────────────────
def safe_lower(text):
    return (text or "").lower()



def extract_device_name(service_info, vendor="", extra_info=None):
    extra_info = extra_info or {}
    search_text = service_info or ""
    patterns = [
        r"http-title:\s*([^|]+)",
        r"Server:\s*([^|]+)",
        r"ssl-cert:\s*subject=.*?commonName=([^/|]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    for key in ("hostname", "mdns_name"):
        if extra_info.get(key):
            return extra_info[key]

    upnp = extra_info.get("upnp", {})
    if upnp.get("server"):
        return upnp["server"][:80]

    snmp = extra_info.get("snmp", {})
    if snmp.get("sysname"):
        return snmp["sysname"]

    if vendor:
        return vendor
    return ""



def build_search_blob(service_info, device_name, vendor, extra_info):
    parts = [service_info or "", device_name or "", vendor or ""]
    for key in ("hostname", "mdns_name"):
        if extra_info.get(key):
            parts.append(extra_info[key])
    if extra_info.get("upnp"):
        parts.extend(extra_info["upnp"].values())
    if extra_info.get("snmp"):
        parts.extend(extra_info["snmp"].values())
    if extra_info.get("netbios"):
        parts.extend(extra_info["netbios"])
    return " ".join(str(item) for item in parts if item).lower()



def classify_device_type(ip, open_ports, service_info, device_name="", vendor="", extra_info=None):
    extra_info = extra_info or {}
    text = build_search_blob(service_info, device_name, vendor, extra_info)
    ports = set(open_ports)
    scores = defaultdict(int)
    reasons = defaultdict(list)

    def add(kind, points, reason):
        scores[kind] += points
        if reason not in reasons[kind]:
            reasons[kind].append(reason)

    # Port signatures
    if ports & CAMERA_PORTS:
        matches = sorted(ports & CAMERA_PORTS)
        add("camera", 45 + min(20, 5 * len(matches)), f"Ανοιχτές θύρες υπογραφής κάμερας: {', '.join(map(str, matches))}")
    if ports & PRINTER_PORTS:
        matches = sorted(ports & PRINTER_PORTS)
        add("printer", 50 + min(15, 5 * len(matches)), f"Ανοιχτές θύρες υπογραφής εκτυπωτή: {', '.join(map(str, matches))}")
    if ports & STORAGE_PORTS:
        matches = sorted(ports & STORAGE_PORTS)
        add("storage", 28 + min(18, 6 * len(matches)), f"Ανοιχτές θύρες διαμοιρασμού αρχείων/αποθήκευσης: {', '.join(map(str, matches))}")
    if ports & MEDIA_PORTS:
        matches = sorted(ports & MEDIA_PORTS)
        add("tv", 28 + min(18, 6 * len(matches)), f"Ανοιχτές θύρες media/streaming: {', '.join(map(str, matches))}")
    if ports & PC_PORTS:
        matches = sorted(ports & PC_PORTS)
        add("pc", 20 + min(15, 5 * len(matches)), f"Ανοιχτές θύρες PC/workstation: {', '.join(map(str, matches))}")
    if ports & PHONE_PORTS:
        matches = sorted(ports & PHONE_PORTS)
        add("phone", 25 + min(12, 6 * len(matches)), f"Ανοιχτές θύρες φορητής συσκευής: {', '.join(map(str, matches))}")

    if 53 in ports and ports & GENERIC_WEB_PORTS:
        add("router", 25, "Εντοπίστηκε συνδυασμός DNS + web admin")
    if ip.endswith(".1") and ports & GENERIC_WEB_PORTS:
        add("router", 12, "Συνηθισμένη διεύθυνση gateway με θύρα web admin")
    if 1400 in ports:
        add("speaker", 50, "Εντοπίστηκε η θύρα 1400 της Sonos")
    if 3389 in ports or 5900 in ports:
        add("pc", 25, "Εντοπίστηκε υπηρεσία απομακρυσμένης επιφάνειας εργασίας / VNC")
    if 62078 in ports:
        add("phone", 45, "Εντοπίστηκε υπηρεσία συγχρονισμού Apple (62078)")
    if 8008 in ports or 8009 in ports:
        add("tv", 35, "Εντοπίστηκε θύρα συμβατή με Chromecast")
    if 8060 in ports:
        add("tv", 45, "Εντοπίστηκε θύρα Roku ECP")
    if 32400 in ports:
        add("tv", 25, "Εντοπίστηκε υπηρεσία media Plex")

    # Keyword hints
    for kind, keywords in TYPE_HINTS.items():
        for keyword in keywords:
            if keyword in text:
                add(kind, 30, f"Ταίριαξε αποτύπωμα λέξης-κλειδιού: {keyword}")
                break

    # Vendor hints
    vendor_l = safe_lower(vendor)
    if "apple" in vendor_l:
        add("phone", 8, "Ένδειξη κατασκευαστή Apple")
        add("tv", 6, "Ένδειξη κατασκευαστή Apple")
    if "synology" in vendor_l or "qnap" in vendor_l:
        add("storage", 35, f"Ένδειξη κατασκευαστή: {vendor}")
    if "raspberry pi" in vendor_l:
        add("iot", 20, "Ένδειξη κατασκευαστή Raspberry Pi")
    if "vmware" in vendor_l or "virtualbox" in vendor_l or "parallels" in vendor_l:
        add("vm", 45, f"Ένδειξη εικονικοποίησης: {vendor}")
    if any(name in vendor_l for name in ["hp", "brother", "epson", "canon"]):
        add("printer", 18, f"Ένδειξη κατασκευαστή εκτυπωτή: {vendor}")

    # Deep-scan signals
    upnp_server = safe_lower(extra_info.get("upnp", {}).get("server", ""))
    if "roku" in upnp_server:
        add("tv", 45, "Ο UPnP server δείχνει Roku")
    if "sonos" in upnp_server:
        add("speaker", 45, "Ο UPnP server δείχνει Sonos")
    if "printer" in upnp_server:
        add("printer", 25, "Ο UPnP server δείχνει εκτυπωτή")

    snmp_desc = safe_lower(extra_info.get("snmp", {}).get("description", ""))
    if "printer" in snmp_desc:
        add("printer", 30, "Η περιγραφή SNMP δείχνει εκτυπωτή")
    if "router" in snmp_desc or "gateway" in snmp_desc:
        add("router", 22, "Η περιγραφή SNMP δείχνει router")

    netbios_names = " ".join(extra_info.get("netbios", []))
    if netbios_names:
        add("pc", 18, "Εντοπίστηκαν ονόματα NetBIOS")

    # False-positive suppression
    if ports and ports.issubset(GENERIC_WEB_PORTS):
        for kind in ("camera", "printer", "storage", "tv", "phone"):
            scores[kind] -= 20
        add("router", 10, "Είναι ανοιχτές μόνο γενικές web θύρες")

    if 631 in ports or 9100 in ports or 5357 in ports:
        scores["camera"] -= 35
        scores["router"] -= 10
    if 554 in ports or 8554 in ports or 37777 in ports:
        scores["printer"] -= 35
        scores["router"] -= 12
    if 445 in ports and not (ports & CAMERA_PORTS):
        scores["camera"] -= 25
    if 8008 in ports or 8060 in ports:
        scores["camera"] -= 20
    if 62078 in ports:
        scores["camera"] -= 20

    best_kind = "unknown"
    best_score = 0
    best_reasons = []
    for kind, score in scores.items():
        if score > best_score:
            best_kind = kind
            best_score = score
            best_reasons = reasons[kind]

    best_score = max(0, min(best_score, 100))
    if best_score < 35:
        return "unknown", best_score, ["Host found, but the type is not specific enough yet"]
    return best_kind, best_score, best_reasons[:5]



def scan_services(host_ips, ports, timing="T4", verbose=False, max_hostgroup=None):
    import nmap

    if not host_ips:
        return {}

    nm = nmap.PortScanner()
    port_str = ",".join(str(port) for port in sorted(set(ports)))
    targets = " ".join(host_ips)
    args = f"-sT -sV --version-light --open -Pn -n -{timing} -p {port_str}"
    if verbose:
        args += " -v"
    if max_hostgroup:
        args += f" --max-hostgroup {max_hostgroup}"
    args += " --host-timeout 15s"

    nm.scan(hosts=targets, arguments=args)
    data = {}
    for host in nm.all_hosts():
        host_data = {"ports": [], "service_info": ""}
        service_parts = []
        if "addresses" in nm[host] and nm[host]["addresses"].get("mac"):
            host_data["mac"] = nm[host]["addresses"].get("mac", "")
        if "vendor" in nm[host] and host_data.get("mac"):
            vendor_map = nm[host].get("vendor", {})
            host_data["vendor"] = vendor_map.get(host_data["mac"], "")
        tcp = nm[host].get("tcp", {})
        for port, port_data in sorted(tcp.items()):
            if port_data.get("state") != "open":
                continue
            host_data["ports"].append(port)
            pieces = [
                port_data.get("name", ""),
                port_data.get("product", ""),
                port_data.get("version", ""),
                port_data.get("extrainfo", ""),
            ]
            script_map = port_data.get("script", {}) or {}
            for script_name, script_output in script_map.items():
                pieces.append(f"{script_name}: {script_output}")
            joined = " ".join(piece for piece in pieces if piece).strip()
            if joined:
                service_parts.append(f"port {port}: {joined}")
        host_data["service_info"] = " | ".join(service_parts)
        data[host] = host_data
    return data


# ─────────────────────────────────────────────
#  ΒΟΗΘΗΤΙΚΑ ΕΞΟΔΟΥ
# ─────────────────────────────────────────────
def type_label(confidence):
    if confidence >= 80:
        return "Ισχυρή ταύτιση", "[!!!]", RED
    if confidence >= 55:
        return "Πιθανό", "[!!] ", YELLOW
    if confidence >= 35:
        return "Ενδεχόμενο", "[!]  ", CYAN
    return "Άγνωστο", "[?]  ", DIM


def display_device_type(kind):
    mapping = {
        "camera": "κάμερα",
        "printer": "εκτυπωτής",
        "router": "δρομολογητής",
        "storage": "αποθήκευση/NAS",
        "pc": "υπολογιστής",
        "phone": "κινητό",
        "tv": "τηλεόραση/media",
        "speaker": "ηχείο",
        "game_console": "κονσόλα",
        "iot": "συσκευή IoT",
        "vm": "εικονική μηχανή",
        "unknown": "άγνωστο",
    }
    return mapping.get(kind, kind)



def presence_bar(score):
    filled = min(20, max(0, int(score / 5)))
    empty = 20 - filled
    if score >= 90:
        color = GREEN
    elif score >= 70:
        color = YELLOW
    else:
        color = CYAN
    return "[" + ccolor(color, "█" * filled) + ccolor(DIM, "░" * empty) + "] " + ccolor(color, f"{score}%")



def format_ports(port_list):
    output = []
    for port in sorted(port_list):
        label = PORT_LABELS.get(port, "?")
        output.append(f"{port} ({label})")
    return ", ".join(output)



def save_results(results, args, subnet, scan_duration):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"devices_scan_{timestamp}"
    output_dir = args.output_dir

    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        success(f"Φάκελος εξόδου: {output_dir}")
    except Exception:
        warn(f"Δεν ήταν δυνατή η δημιουργία του {output_dir}. Χρήση του τρέχοντος φακέλου.")
        output_dir = os.getcwd()

    serializable_results = []
    for item in results:
        clone = dict(item)
        clone["discovery_sources"] = sorted(clone.get("discovery_sources", []))
        serializable_results.append(clone)

    json_path = os.path.join(output_dir, base_filename + ".json")
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "scan_time": timestamp,
                "target_subnet": subnet,
                "duration_seconds": scan_duration,
                "arguments": vars(args),
                "results": serializable_results,
            },
            handle,
            indent=2,
        )

    txt_path = os.path.join(output_dir, base_filename + ".txt")
    with open(txt_path, "w", encoding="utf-8") as handle:
        handle.write("Αναφορά Devices Finder\n")
        handle.write(f"Ώρα σάρωσης: {timestamp}\n")
        handle.write(f"Subnet στόχος: {subnet}\n")
        handle.write(f"Διάρκεια: {scan_duration:.1f} δευτερόλεπτα\n")
        handle.write("=" * 70 + "\n\n")
        if not results:
            handle.write("Δεν εντοπίστηκαν συσκευές.\n")
        else:
            for item in results:
                label, _, _ = type_label(item.get("type_confidence", 0))
                handle.write(f"IP: {item['ip']}\n")
                handle.write(f"Βεβαιότητα παρουσίας: {item.get('presence_confidence', 0)}%\n")
                handle.write(f"Τύπος: {display_device_type(item.get('device_type', 'unknown'))} ({label}, {item.get('type_confidence', 0)}%)\n")
                if item.get("device_name"):
                    handle.write(f"Όνομα: {item['device_name']}\n")
                if item.get("mac"):
                    vendor = item.get("vendor") or lookup_mac_vendor(item.get("mac", ""))
                    handle.write(f"MAC: {item['mac']}\n")
                    if vendor:
                        handle.write(f"Κατασκευαστής: {vendor}\n")
                handle.write(f"Πηγές εντοπισμού: {', '.join(sorted(item.get('discovery_sources', [])))}\n")
                if item.get("open_ports"):
                    handle.write(f"Ανοιχτές θύρες: {format_ports(item['open_ports'])}\n")
                if item.get("type_reasons"):
                    handle.write("Γιατί:\n")
                    for reason in item["type_reasons"]:
                        handle.write(f"  - {reason}\n")
                extra = item.get("extra_info", {})
                if extra.get("hostname"):
                    handle.write(f"Όνομα DNS host: {extra['hostname']}\n")
                if extra.get("mdns_name"):
                    handle.write(f"Όνομα mDNS: {extra['mdns_name']}\n")
                if extra.get("netbios"):
                    handle.write(f"NetBIOS: {', '.join(extra['netbios'])}\n")
                handle.write("\n")
        handle.write("=" * 70 + "\n")

    csv_path = os.path.join(output_dir, base_filename + ".csv")
    with open(csv_path, "w", encoding="utf-8") as handle:
        handle.write(
            "IP,Βεβαιότητα Παρουσίας,Τύπος Συσκευής,Βεβαιότητα Τύπου,Όνομα,MAC,Κατασκευαστής,Πηγές Εντοπισμού,Ανοιχτές Θύρες,Λόγοι\n"
        )
        for item in results:
            handle.write(
                f"{item['ip']},{item.get('presence_confidence', 0)},{display_device_type(item.get('device_type', 'unknown'))},"
                f"{item.get('type_confidence', 0)},\"{item.get('device_name', '')}\",{item.get('mac', '')},"
                f"\"{item.get('vendor', '')}\",\"{' '.join(sorted(item.get('discovery_sources', [])))}\","
                f"\"{' '.join(str(p) for p in item.get('open_ports', []))}\","
                f"\"{'; '.join(item.get('type_reasons', []))}\"\n"
            )

    html_path = os.path.join(output_dir, base_filename + ".html")
    with open(html_path, "w", encoding="utf-8") as handle:
        handle.write("<html><head><meta charset='utf-8'><title>Αναφορά Devices Finder</title>")
        handle.write(
            "<style>body{font-family:sans-serif;background:#111;color:#eee;padding:20px}"
            "table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:8px;text-align:left}"
            "th{background:#222}tr:nth-child(even){background:#181818}</style></head><body>"
        )
        handle.write(f"<h2>Αναφορά Devices Finder</h2><p>Ώρα σάρωσης: {timestamp}<br>Subnet: {subnet}<br>Διάρκεια: {scan_duration:.1f}s</p>")
        if not results:
            handle.write("<p>Δεν εντοπίστηκαν συσκευές.</p>")
        else:
            handle.write(
                "<table><tr><th>IP</th><th>Ζωντανό</th><th>Τύπος</th><th>Βεβαιότητα Τύπου</th><th>Όνομα</th><th>MAC</th><th>Κατασκευαστής</th><th>Πηγές</th><th>Θύρες</th><th>Λόγοι</th></tr>"
            )
            for item in results:
                handle.write(
                    f"<tr><td>{item['ip']}</td><td>{item.get('presence_confidence', 0)}%</td>"
                    f"<td>{display_device_type(item.get('device_type', 'unknown'))}</td><td>{item.get('type_confidence', 0)}%</td>"
                    f"<td>{item.get('device_name', '')}</td><td>{item.get('mac', '')}</td><td>{item.get('vendor', '')}</td>"
                    f"<td>{', '.join(sorted(item.get('discovery_sources', [])))}</td>"
                    f"<td>{format_ports(item.get('open_ports', []))}</td>"
                    f"<td>{'<br>'.join(item.get('type_reasons', []))}</td></tr>"
                )
            handle.write("</table>")
        handle.write("</body></html>")

    success(f"Τα αποτελέσματα αποθηκεύτηκαν στο {output_dir}")
    for path in (json_path, txt_path, csv_path, html_path):
        print(ccolor(DIM, f"  - {os.path.basename(path)}"))



def filter_results_by_type(results, wanted_type):
    if wanted_type == "all":
        return results
    return [item for item in results if item.get("device_type") == wanted_type]



def print_summary(results):
    print()
    print(ccolor(CYAN + BOLD, "  -- ΕΝΤΟΠΙΣΜΕΝΕΣ ΣΥΣΚΕΥΕΣ --"))
    print()

    if not results:
        warn("Δεν εντοπίστηκαν συσκευές.")
        print(ccolor(DIM, "  Αυτό μπορεί να συμβεί αν το δίκτυο μπλοκάρει τον εντοπισμό ή αν το subnet είναι λάθος."))
        return

    for index, item in enumerate(results, 1):
        label, icon, color = type_label(item.get("type_confidence", 0))
        device_type = display_device_type(item.get("device_type", "unknown"))
        print(ccolor(color, f"  ┌─ #{index} ─────────────────────────"))
        print(ccolor(color, "  │") + " " + ccolor(GREEN, "ONLINE") + " " + ccolor(WHITE, item["ip"]))
        print(ccolor(color, "  │") + f" Βεβαιότητα παρουσίας : {presence_bar(item.get('presence_confidence', 0))}")
        print(ccolor(color, "  │") + f" Τύπος             : {ccolor(BOLD, device_type)}  {ccolor(color, label)} ({item.get('type_confidence', 0)}%)")
        if item.get("device_name"):
            print(ccolor(color, "  │") + f" Όνομα            : {ccolor(WHITE, item['device_name'])}")
        if item.get("mac"):
            mac_line = item["mac"]
            if item.get("vendor"):
                mac_line += f" ({item['vendor']})"
            print(ccolor(color, "  │") + f" MAC             : {ccolor(WHITE, mac_line)}")
        print(ccolor(color, "  │") + f" Πηγές             : {ccolor(WHITE, ', '.join(sorted(item.get('discovery_sources', []))))}")
        if item.get("open_ports"):
            print(ccolor(color, "  │") + f" Ανοιχτές θύρες    : {ccolor(WHITE, format_ports(item['open_ports']))}")
        extra = item.get("extra_info", {})
        if extra.get("hostname"):
            print(ccolor(color, "  │") + f" DNS             : {ccolor(WHITE, extra['hostname'])}")
        if extra.get("mdns_name"):
            print(ccolor(color, "  │") + f" mDNS            : {ccolor(WHITE, extra['mdns_name'])}")
        if extra.get("snmp", {}).get("description"):
            print(ccolor(color, "  │") + f" SNMP            : {ccolor(WHITE, extra['snmp']['description'][:80])}")
        print(ccolor(color, "  │") + " Γιατί:")
        for reason in item.get("type_reasons", []):
            print(ccolor(color, "  │") + "  " + ccolor(GREEN, "✓") + " " + reason)
        if not item.get("type_reasons"):
            print(ccolor(color, "  │") + "  " + ccolor(YELLOW, "•") + "Η συσκευή είναι ενεργή, αλλά ο τύπος της παραμένει άγνωστος")
        print(ccolor(color, "  └──────────────────────────────────"))
        print()

    type_totals = defaultdict(int)
    for item in results:
        type_totals[item.get("device_type", "unknown")] += 1

    divider()
    summary_parts = []
    for kind, count in sorted(type_totals.items()):
        summary_parts.append(f"{display_device_type(kind)}:{count}")
    print("  " + ccolor(WHITE, " | ".join(summary_parts)))
    divider()


# ─────────────────────────────────────────────
#  ΚΥΡΙΑ ΛΟΓΙΚΗ ΣΑΡΩΣΗΣ
# ─────────────────────────────────────────────
def scan_network(subnet, ports, verbose=False, exclude_self=False, self_ip=None,
                 timing="T4", exclude_targets=None, max_hostgroup=None,
                 deep_scan=False):
    divider()
    info(f"Subnet στόχος : {ccolor(WHITE, subnet)}")
    info(f"Θύρες         : {ccolor(WHITE, ', '.join(map(str, ports)))}")
    if exclude_targets:
        info(f"Εξαίρεση      : {ccolor(WHITE, exclude_targets)}")
    if deep_scan:
        info(ccolor(WHITE, "Το deep scan είναι ενεργό (mDNS / UPnP / SNMP / NetBIOS)"))
    divider()
    print()

    start = datetime.datetime.now()

    records = discover_hosts(
        subnet=subnet,
        local_ip=self_ip,
        exclude_self=exclude_self,
        exclude_targets=exclude_targets,
        timing=timing,
    )

    if not records:
        duration = (datetime.datetime.now() - start).total_seconds()
        return [], duration

    success(f"Εντοπίστηκαν {len(records)} ενεργή ή πρόσφατα ορατή/ές συσκευή/ές")
    print()

    service_data = scan_services(
        host_ips=list(records.keys()),
        ports=ports,
        timing=timing,
        verbose=verbose,
        max_hostgroup=max_hostgroup,
    )

    results = []
    for ip, record in records.items():
        host_service = service_data.get(ip, {})
        if host_service.get("mac") and not record.get("mac"):
            record["mac"] = normalize_mac(host_service.get("mac", ""))
        record["vendor"] = host_service.get("vendor") or record.get("vendor") or lookup_mac_vendor(record.get("mac", ""))
        record["open_ports"] = sorted(host_service.get("ports", []))
        record["service_info"] = host_service.get("service_info", "")
        record["extra_info"] = enrich_device(ip, deep_scan=deep_scan)
        record["device_name"] = extract_device_name(
            record.get("service_info", ""),
            vendor=record.get("vendor", ""),
            extra_info=record.get("extra_info", {}),
        )
        device_type, type_confidence, type_reasons = classify_device_type(
            ip=ip,
            open_ports=record.get("open_ports", []),
            service_info=record.get("service_info", ""),
            device_name=record.get("device_name", ""),
            vendor=record.get("vendor", ""),
            extra_info=record.get("extra_info", {}),
        )
        record["device_type"] = device_type
        record["type_confidence"] = type_confidence
        record["type_reasons"] = type_reasons
        record["discovery_sources"] = sorted(record.get("discovery_sources", []))
        record["vendor"] = record.get("vendor", "")

        label, icon, color = type_label(type_confidence)
        name_part = f" - {record['device_name']}" if record.get("device_name") else ""
        print(
            "  " + ccolor(GREEN, "[ONLINE]") + " " + ccolor(WHITE, ip) + name_part +
            "  →  " + ccolor(color, f"{display_device_type(device_type)} ({label}, {type_confidence}%)")
        )

        results.append(record)

    results.sort(key=lambda item: (-item.get("presence_confidence", 0), -item.get("type_confidence", 0), host_sort_key(item["ip"])))
    duration = (datetime.datetime.now() - start).total_seconds()
    return results, duration


# ─────────────────────────────────────────────
#  ΔΙΑΔΡΑΣΤΙΚΟ ΜΕΝΟΥ
# ─────────────────────────────────────────────
def interactive_menu():
    while True:
        print(ccolor(CYAN + BOLD, "\n  Διαδραστική λειτουργία σάρωσης"))
        print(ccolor(DIM, "  ---------------------"))
        print("  1. Ισορροπημένη σάρωση συσκευών (προτείνεται)")
        print("  2. Κάμερες / NVR / DVR")
        print("  3. Media / TV / συσκευές streaming")
        print("  4. Υπολογιστές / NAS / servers")
        print("  5. Εκτυπωτές")
        print("  6. Εισαγωγή προσαρμοσμένων θυρών")
        print("  7. Βοήθεια")
        print("  0. Έξοδος")

        choice = input(ccolor(YELLOW, "\n  Επίλεξε [0-7]: ")).strip()
        if choice == "0":
            sys.exit(0)
        if choice == "1":
            return sorted(PORT_CATEGORIES["balanced"])
        if choice == "2":
            return sorted(PORT_CATEGORIES["cameras"])
        if choice == "3":
            return sorted(PORT_CATEGORIES["media"])
        if choice == "4":
            return sorted(PORT_CATEGORIES["workstation"])
        if choice == "5":
            return sorted(PORT_CATEGORIES["printer"])
        if choice == "6":
            value = input("  Δώσε θύρες (παράδειγμα: 22,80,443,445): ").strip()
            try:
                ports = [int(item.strip()) for item in value.split(",") if item.strip()]
                if not ports:
                    raise ValueError
                return sorted(set(ports))
            except Exception:
                error("Μη έγκυρη λίστα θυρών.")
                continue
        if choice == "7":
            print()
            print("  Αυτή η έκδοση πρώτα ανακαλύπτει ενεργές συσκευές με ARP / neighbor table / nmap host discovery,")
            print("  και μετά σαρώνει μόνο αυτά τα discovered hosts. Αυτό μειώνει τα false positives και βρίσκει συσκευές")
            print("  ακόμη και όταν δεν εκθέτουν web pages ή camera ports.")
            print()
            print("  Σημαντικές αλλαγές:")
            print("    • οι 80/443/8080 μόνες τους δεν προκαλούν πλέον false positives τύπου κάμερας")
            print("    • οι συσκευές εμφανίζονται ως ενεργές ακόμη κι όταν ο ακριβής τύπος τους είναι άγνωστος")
            print("    • η αναγνώριση τύπου χρησιμοποιεί πλέον συνδυασμένα στοιχεία: ports + banners + hostnames + vendors")
            print("    • το deep scan είναι προαιρετικό και προσθέτει ενδείξεις mDNS, UPnP, SNMP, NetBIOS")
            print()
            input("  Πάτα Enter για επιστροφή...")
            continue
        warn("Μη έγκυρη επιλογή.")


# ─────────────────────────────────────────────
#  ΟΡΙΣΜΑΤΑ
# ─────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="Devices Finder – εντοπισμός συσκευών τοπικού δικτύου χωρίς root.",
        epilog=(
            "Παραδείγματα:\n"
            "  python 'Devices Finder GR.py' --interactive\n"
            "  python 'Devices Finder GR.py' --subnet 192.168.1.0/24\n"
            "  python 'Devices Finder GR.py' --exclude-self --filter camera --deep-scan\n"
            "  python 'Devices Finder GR.py' --ports 22,80,443,445,631,554,8009,9100\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--subnet", "-s", help="Subnet στόχος, για παράδειγμα 192.168.1.0/24")
    parser.add_argument("--ports", "-p", help="TCP θύρες χωρισμένες με κόμμα για σάρωση μετά τον εντοπισμό")
    parser.add_argument("--output-dir", "-o", default=DEFAULT_OUTPUT_DIR, help=f"Φάκελος εξόδου (προεπιλογή: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--filter", "-f", choices=["all", "camera", "printer", "router", "storage", "pc", "phone", "tv", "speaker", "game_console", "iot", "vm", "unknown"], default="all", help="Εμφάνιση μόνο ενός τύπου συσκευής")
    parser.add_argument("--verbose", "-v", action="store_true", help="Αναλυτική έξοδος nmap")
    parser.add_argument("--no-color", action="store_true", help="Απενεργοποίηση χρωματισμένης εξόδου terminal")
    parser.add_argument("--interactive", "-i", action="store_true", help="Επιλογή προφίλ σάρωσης από μενού")
    parser.add_argument("--exclude-self", action="store_true", help="Απόκρυψη της δικής σου συσκευής από τα τελικά αποτελέσματα")
    parser.add_argument("--exclude", help="IPs ή εύρη χωρισμένα με κόμμα για εξαίρεση")
    parser.add_argument("--timing", "-T", choices=["T0", "T1", "T2", "T3", "T4", "T5"], default="T4", help="Πρότυπο timing του Nmap (προεπιλογή: T4)")
    parser.add_argument("--max-hostgroup", type=int, help="Τιμή max-hostgroup του Nmap για τη σάρωση υπηρεσιών")
    parser.add_argument("--deep-scan", action="store_true", help="Προσθήκη εμπλουτισμού mDNS, UPnP, SNMP και NetBIOS")
    return parser.parse_args()


# ─────────────────────────────────────────────
#  ΣΗΜΕΙΟ ΕΚΚΙΝΗΣΗΣ
# ─────────────────────────────────────────────
def main():
    global USE_COLOR
    args = parse_args()

    if args.no_color:
        USE_COLOR = False

    banner()
    print(ccolor(DIM, "  Αυτό το script εντοπίζει συσκευές στο ίδιο τοπικό δίκτυο χωρίς root."))
    print(ccolor(DIM, "  Μειώνει τα false positives χωρίζοντας τον εντοπισμό ενεργών hosts από την αναγνώριση τύπου."))
    print()

    check_dependencies(deep_scan=args.deep_scan)

    if args.interactive or (not args.ports and not args.subnet):
        ports = interactive_menu()
    elif args.ports:
        try:
            ports = sorted(set(int(item.strip()) for item in args.ports.split(",") if item.strip()))
        except ValueError:
            error("Μη έγκυρη λίστα θυρών. Χρησιμοποίησε ακέραιους χωρισμένους με κόμμα.")
            sys.exit(1)
    else:
        ports = DEFAULT_PORTS

    detected_subnet, local_ip = get_local_subnet()
    subnet = args.subnet or detected_subnet
    if args.subnet:
        success(f"Χρήση subnet που δόθηκε από τον χρήστη → {subnet}")
    if not subnet:
        error("Δεν μπορεί να συνεχίσει χωρίς subnet. Χρησιμοποίησε --subnet.")
        sys.exit(1)

    exclude_targets = expand_exclude_list(args.exclude) if args.exclude else None

    results, duration = scan_network(
        subnet=subnet,
        ports=ports,
        verbose=args.verbose,
        exclude_self=args.exclude_self,
        self_ip=local_ip,
        timing=args.timing,
        exclude_targets=exclude_targets,
        max_hostgroup=args.max_hostgroup,
        deep_scan=args.deep_scan,
    )

    if args.filter != "all":
        before = len(results)
        results = filter_results_by_type(results, args.filter)
        info(f"Φιλτραρίστηκαν κατά '{args.filter}': εμφανίζονται {len(results)}/{before}")

    print_summary(results)
    save_results(results, args, subnet, duration)


if __name__ == "__main__":
    main()
