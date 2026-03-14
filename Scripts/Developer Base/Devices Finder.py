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
#  ANSI COLORS (works in Termux terminal)
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
    print(ccolor(YELLOW, "  ⚠ For devices on your own network only."))
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
        print(ccolor(YELLOW, "\n\n  [!] Interrupt received. Exiting cleanly..."))
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


# ─────────────────────────────────────────────
#  DEFAULT OUTPUT DIRECTORY
# ─────────────────────────────────────────────
def resolve_default_output_dir():
    candidates = [
        os.path.expanduser("~/storage/downloads/Devices Finder"),
        os.path.expanduser("~/downloads/Devices Finder"),
        os.path.join(os.getcwd(), "Devices Finder Output"),
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
#  DEPENDENCIES
# ─────────────────────────────────────────────
def install_dependency(package, is_pip=False):
    if is_pip:
        cmd = [sys.executable, "-m", "pip", "install", package]
        info(f"Installing Python package: {package}")
    else:
        cmd = ["pkg", "install", "-y", package]
        info(f"Installing system package: {package}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            success(f"Installed {package}")
            return True
        error(result.stderr.strip() or f"Could not install {package}")
        return False
    except Exception as exc:
        error(f"Installation error for {package}: {exc}")
        return False



def command_exists(command):
    try:
        result = subprocess.run([command, "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False



def check_dependencies(deep_scan=False):
    info("Checking dependencies...")
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

    warn("Missing dependencies found. Trying automatic install...")
    all_ok = True
    for package, is_pip in missing:
        if not install_dependency(package, is_pip=is_pip):
            all_ok = False

    if not all_ok:
        error("Some dependencies could not be installed automatically.")
        print(ccolor(WHITE, "  Install them manually with:"))
        for package, is_pip in missing:
            if is_pip:
                print(ccolor(WHITE, f"    pip install {package}"))
            else:
                print(ccolor(WHITE, f"    pkg install {package}"))
        sys.exit(1)

    divider()
    return True


# ─────────────────────────────────────────────
#  NETWORK HELPERS
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
    """Best-effort local IP and subnet detection without requiring root."""
    # Method 1: UDP socket route trick
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("1.1.1.1", 80))
        local_ip = sock.getsockname()[0]
        sock.close()
        subnet = local_ip.rsplit(".", 1)[0] + ".0/24"
        success(f"Local IP detected → {local_ip}")
        return subnet, local_ip
    except Exception:
        pass

    # Method 2: ip route
    route = run_command(["ip", "-4", "route"])
    if route:
        src_match = re.search(r"src\s+(\d+\.\d+\.\d+\.\d+)", route)
        cidr_match = re.search(r"(\d+\.\d+\.\d+\.\d+/\d+)", route)
        local_ip = src_match.group(1) if src_match else None
        subnet = cidr_match.group(1) if cidr_match else None
        if local_ip and subnet:
            success(f"Local IP detected via ip route → {local_ip}")
            return subnet, local_ip
        if local_ip:
            subnet = local_ip.rsplit(".", 1)[0] + ".0/24"
            success(f"Local IP detected via ip route → {local_ip}")
            return subnet, local_ip

    # Method 3: ifconfig
    output = run_command(["ifconfig"])
    if output:
        match = re.search(r"inet\s(?:addr:)?(\d+\.\d+\.\d+\.\d+)", output)
        if match:
            local_ip = match.group(1)
            subnet = local_ip.rsplit(".", 1)[0] + ".0/24"
            success(f"Local IP detected via ifconfig → {local_ip}")
            return subnet, local_ip

    error("Could not auto-detect subnet.")
    return None, None



def expand_exclude_list(exclude_list):
    return ",".join(item.strip() for item in exclude_list.split(",") if item.strip())


# ─────────────────────────────────────────────
#  MAC / VENDOR HELPERS
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
#  PORTS / SIGNATURES
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
    515: "LPD Printer",
    548: "AFP",
    554: "RTSP",
    631: "IPP Printer",
    1025: "RPC / Service",
    1400: "Sonos",
    3389: "RDP",
    5357: "WSD Printer",
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
    9100: "Raw Printer",
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
#  DISCOVERY FUNCTIONS (broad device detection)
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
        warn(f"Nmap host discovery failed, continuing with ARP/neigh only: {exc}")

    if exclude_self and local_ip and local_ip in records:
        records.pop(local_ip, None)

    for rec in records.values():
        rec["presence_confidence"] = calculate_presence_confidence(rec.get("discovery_sources", set()), rec.get("mac", ""))
        rec["vendor"] = lookup_mac_vendor(rec.get("mac", ""))

    return dict(sorted(records.items(), key=lambda item: host_sort_key(item[0])))


# ─────────────────────────────────────────────
#  ENRICHMENT HELPERS
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
#  SERVICE SCAN / CLASSIFICATION
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
        add("camera", 45 + min(20, 5 * len(matches)), f"Camera-signature ports open: {', '.join(map(str, matches))}")
    if ports & PRINTER_PORTS:
        matches = sorted(ports & PRINTER_PORTS)
        add("printer", 50 + min(15, 5 * len(matches)), f"Printer-signature ports open: {', '.join(map(str, matches))}")
    if ports & STORAGE_PORTS:
        matches = sorted(ports & STORAGE_PORTS)
        add("storage", 28 + min(18, 6 * len(matches)), f"File-sharing/storage ports open: {', '.join(map(str, matches))}")
    if ports & MEDIA_PORTS:
        matches = sorted(ports & MEDIA_PORTS)
        add("tv", 28 + min(18, 6 * len(matches)), f"Media/streaming ports open: {', '.join(map(str, matches))}")
    if ports & PC_PORTS:
        matches = sorted(ports & PC_PORTS)
        add("pc", 20 + min(15, 5 * len(matches)), f"PC/workstation ports open: {', '.join(map(str, matches))}")
    if ports & PHONE_PORTS:
        matches = sorted(ports & PHONE_PORTS)
        add("phone", 25 + min(12, 6 * len(matches)), f"Mobile-device ports open: {', '.join(map(str, matches))}")

    if 53 in ports and ports & GENERIC_WEB_PORTS:
        add("router", 25, "DNS + web admin combination detected")
    if ip.endswith(".1") and ports & GENERIC_WEB_PORTS:
        add("router", 12, "Common gateway address with web admin port")
    if 1400 in ports:
        add("speaker", 50, "Sonos port 1400 detected")
    if 3389 in ports or 5900 in ports:
        add("pc", 25, "Remote desktop / VNC service detected")
    if 62078 in ports:
        add("phone", 45, "Apple sync service detected (62078)")
    if 8008 in ports or 8009 in ports:
        add("tv", 35, "Chromecast-compatible port detected")
    if 8060 in ports:
        add("tv", 45, "Roku ECP port detected")
    if 32400 in ports:
        add("tv", 25, "Plex media service detected")

    # Keyword hints
    for kind, keywords in TYPE_HINTS.items():
        for keyword in keywords:
            if keyword in text:
                add(kind, 30, f"Keyword fingerprint matched: {keyword}")
                break

    # Vendor hints
    vendor_l = safe_lower(vendor)
    if "apple" in vendor_l:
        add("phone", 8, "Apple vendor hint")
        add("tv", 6, "Apple vendor hint")
    if "synology" in vendor_l or "qnap" in vendor_l:
        add("storage", 35, f"Vendor hint: {vendor}")
    if "raspberry pi" in vendor_l:
        add("iot", 20, "Raspberry Pi vendor hint")
    if "vmware" in vendor_l or "virtualbox" in vendor_l or "parallels" in vendor_l:
        add("vm", 45, f"Virtualization vendor hint: {vendor}")
    if any(name in vendor_l for name in ["hp", "brother", "epson", "canon"]):
        add("printer", 18, f"Printer vendor hint: {vendor}")

    # Deep-scan signals
    upnp_server = safe_lower(extra_info.get("upnp", {}).get("server", ""))
    if "roku" in upnp_server:
        add("tv", 45, "UPnP server indicates Roku")
    if "sonos" in upnp_server:
        add("speaker", 45, "UPnP server indicates Sonos")
    if "printer" in upnp_server:
        add("printer", 25, "UPnP server indicates printer")

    snmp_desc = safe_lower(extra_info.get("snmp", {}).get("description", ""))
    if "printer" in snmp_desc:
        add("printer", 30, "SNMP description indicates printer")
    if "router" in snmp_desc or "gateway" in snmp_desc:
        add("router", 22, "SNMP description indicates router")

    netbios_names = " ".join(extra_info.get("netbios", []))
    if netbios_names:
        add("pc", 18, "NetBIOS names discovered")

    # False-positive suppression
    if ports and ports.issubset(GENERIC_WEB_PORTS):
        for kind in ("camera", "printer", "storage", "tv", "phone"):
            scores[kind] -= 20
        add("router", 10, "Only generic web ports are open")

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
#  OUTPUT HELPERS
# ─────────────────────────────────────────────
def type_label(confidence):
    if confidence >= 80:
        return "Strong match", "[!!!]", RED
    if confidence >= 55:
        return "Probable", "[!!] ", YELLOW
    if confidence >= 35:
        return "Possible", "[!]  ", CYAN
    return "Unknown", "[?]  ", DIM



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
        success(f"Output directory: {output_dir}")
    except Exception:
        warn(f"Could not create {output_dir}. Falling back to current directory.")
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
        handle.write("Devices Finder Report\n")
        handle.write(f"Scan time: {timestamp}\n")
        handle.write(f"Target subnet: {subnet}\n")
        handle.write(f"Duration: {scan_duration:.1f} seconds\n")
        handle.write("=" * 70 + "\n\n")
        if not results:
            handle.write("No devices were discovered.\n")
        else:
            for item in results:
                label, _, _ = type_label(item.get("type_confidence", 0))
                handle.write(f"IP: {item['ip']}\n")
                handle.write(f"Live confidence: {item.get('presence_confidence', 0)}%\n")
                handle.write(f"Type: {item.get('device_type', 'unknown')} ({label}, {item.get('type_confidence', 0)}%)\n")
                if item.get("device_name"):
                    handle.write(f"Name: {item['device_name']}\n")
                if item.get("mac"):
                    vendor = item.get("vendor") or lookup_mac_vendor(item.get("mac", ""))
                    handle.write(f"MAC: {item['mac']}\n")
                    if vendor:
                        handle.write(f"Vendor: {vendor}\n")
                handle.write(f"Discovery sources: {', '.join(sorted(item.get('discovery_sources', [])))}\n")
                if item.get("open_ports"):
                    handle.write(f"Open ports: {format_ports(item['open_ports'])}\n")
                if item.get("type_reasons"):
                    handle.write("Why:\n")
                    for reason in item["type_reasons"]:
                        handle.write(f"  - {reason}\n")
                extra = item.get("extra_info", {})
                if extra.get("hostname"):
                    handle.write(f"DNS hostname: {extra['hostname']}\n")
                if extra.get("mdns_name"):
                    handle.write(f"mDNS name: {extra['mdns_name']}\n")
                if extra.get("netbios"):
                    handle.write(f"NetBIOS: {', '.join(extra['netbios'])}\n")
                handle.write("\n")
        handle.write("=" * 70 + "\n")

    csv_path = os.path.join(output_dir, base_filename + ".csv")
    with open(csv_path, "w", encoding="utf-8") as handle:
        handle.write(
            "IP,Live Confidence,Device Type,Type Confidence,Name,MAC,Vendor,Discovery Sources,Open Ports,Reasons\n"
        )
        for item in results:
            handle.write(
                f"{item['ip']},{item.get('presence_confidence', 0)},{item.get('device_type', 'unknown')},"
                f"{item.get('type_confidence', 0)},\"{item.get('device_name', '')}\",{item.get('mac', '')},"
                f"\"{item.get('vendor', '')}\",\"{' '.join(sorted(item.get('discovery_sources', [])))}\","
                f"\"{' '.join(str(p) for p in item.get('open_ports', []))}\","
                f"\"{'; '.join(item.get('type_reasons', []))}\"\n"
            )

    html_path = os.path.join(output_dir, base_filename + ".html")
    with open(html_path, "w", encoding="utf-8") as handle:
        handle.write("<html><head><meta charset='utf-8'><title>Devices Finder Report</title>")
        handle.write(
            "<style>body{font-family:sans-serif;background:#111;color:#eee;padding:20px}"
            "table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:8px;text-align:left}"
            "th{background:#222}tr:nth-child(even){background:#181818}</style></head><body>"
        )
        handle.write(f"<h2>Devices Finder Report</h2><p>Scan time: {timestamp}<br>Subnet: {subnet}<br>Duration: {scan_duration:.1f}s</p>")
        if not results:
            handle.write("<p>No devices were discovered.</p>")
        else:
            handle.write(
                "<table><tr><th>IP</th><th>Live</th><th>Type</th><th>Type Conf.</th><th>Name</th><th>MAC</th><th>Vendor</th><th>Sources</th><th>Ports</th><th>Reasons</th></tr>"
            )
            for item in results:
                handle.write(
                    f"<tr><td>{item['ip']}</td><td>{item.get('presence_confidence', 0)}%</td>"
                    f"<td>{item.get('device_type', 'unknown')}</td><td>{item.get('type_confidence', 0)}%</td>"
                    f"<td>{item.get('device_name', '')}</td><td>{item.get('mac', '')}</td><td>{item.get('vendor', '')}</td>"
                    f"<td>{', '.join(sorted(item.get('discovery_sources', [])))}</td>"
                    f"<td>{format_ports(item.get('open_ports', []))}</td>"
                    f"<td>{'<br>'.join(item.get('type_reasons', []))}</td></tr>"
                )
            handle.write("</table>")
        handle.write("</body></html>")

    success(f"Results saved to {output_dir}")
    for path in (json_path, txt_path, csv_path, html_path):
        print(ccolor(DIM, f"  - {os.path.basename(path)}"))



def filter_results_by_type(results, wanted_type):
    if wanted_type == "all":
        return results
    return [item for item in results if item.get("device_type") == wanted_type]



def print_summary(results):
    print()
    print(ccolor(CYAN + BOLD, "  -- DISCOVERED DEVICES --"))
    print()

    if not results:
        warn("No devices were discovered.")
        print(ccolor(DIM, "  This can happen if the network blocks discovery or the subnet is wrong."))
        return

    for index, item in enumerate(results, 1):
        label, icon, color = type_label(item.get("type_confidence", 0))
        device_type = item.get("device_type", "unknown")
        print(ccolor(color, f"  ┌─ #{index} ─────────────────────────"))
        print(ccolor(color, "  │") + " " + ccolor(GREEN, "LIVE") + " " + ccolor(WHITE, item["ip"]))
        print(ccolor(color, "  │") + f" Live confidence : {presence_bar(item.get('presence_confidence', 0))}")
        print(ccolor(color, "  │") + f" Type            : {ccolor(BOLD, device_type)}  {ccolor(color, label)} ({item.get('type_confidence', 0)}%)")
        if item.get("device_name"):
            print(ccolor(color, "  │") + f" Name            : {ccolor(WHITE, item['device_name'])}")
        if item.get("mac"):
            mac_line = item["mac"]
            if item.get("vendor"):
                mac_line += f" ({item['vendor']})"
            print(ccolor(color, "  │") + f" MAC             : {ccolor(WHITE, mac_line)}")
        print(ccolor(color, "  │") + f" Sources         : {ccolor(WHITE, ', '.join(sorted(item.get('discovery_sources', []))))}")
        if item.get("open_ports"):
            print(ccolor(color, "  │") + f" Open ports      : {ccolor(WHITE, format_ports(item['open_ports']))}")
        extra = item.get("extra_info", {})
        if extra.get("hostname"):
            print(ccolor(color, "  │") + f" DNS             : {ccolor(WHITE, extra['hostname'])}")
        if extra.get("mdns_name"):
            print(ccolor(color, "  │") + f" mDNS            : {ccolor(WHITE, extra['mdns_name'])}")
        if extra.get("snmp", {}).get("description"):
            print(ccolor(color, "  │") + f" SNMP            : {ccolor(WHITE, extra['snmp']['description'][:80])}")
        print(ccolor(color, "  │") + " Why:")
        for reason in item.get("type_reasons", []):
            print(ccolor(color, "  │") + "  " + ccolor(GREEN, "✓") + " " + reason)
        if not item.get("type_reasons"):
            print(ccolor(color, "  │") + "  " + ccolor(YELLOW, "•") + " Host is live, but the type is still unknown")
        print(ccolor(color, "  └──────────────────────────────────"))
        print()

    type_totals = defaultdict(int)
    for item in results:
        type_totals[item.get("device_type", "unknown")] += 1

    divider()
    summary_parts = []
    for kind, count in sorted(type_totals.items()):
        summary_parts.append(f"{kind}:{count}")
    print("  " + ccolor(WHITE, " | ".join(summary_parts)))
    divider()


# ─────────────────────────────────────────────
#  MAIN SCAN LOGIC
# ─────────────────────────────────────────────
def scan_network(subnet, ports, verbose=False, exclude_self=False, self_ip=None,
                 timing="T4", exclude_targets=None, max_hostgroup=None,
                 deep_scan=False):
    divider()
    info(f"Target subnet : {ccolor(WHITE, subnet)}")
    info(f"Ports         : {ccolor(WHITE, ', '.join(map(str, ports)))}")
    if exclude_targets:
        info(f"Exclude       : {ccolor(WHITE, exclude_targets)}")
    if deep_scan:
        info(ccolor(WHITE, "Deep scan enabled (mDNS / UPnP / SNMP / NetBIOS)"))
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

    success(f"Discovered {len(records)} live or recently seen device(s)")
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
            "  " + ccolor(GREEN, "[LIVE]") + " " + ccolor(WHITE, ip) + name_part +
            "  →  " + ccolor(color, f"{device_type} ({label}, {type_confidence}%)")
        )

        results.append(record)

    results.sort(key=lambda item: (-item.get("presence_confidence", 0), -item.get("type_confidence", 0), host_sort_key(item["ip"])))
    duration = (datetime.datetime.now() - start).total_seconds()
    return results, duration


# ─────────────────────────────────────────────
#  INTERACTIVE MENU
# ─────────────────────────────────────────────
def interactive_menu():
    while True:
        print(ccolor(CYAN + BOLD, "\n  Interactive Scan Mode"))
        print(ccolor(DIM, "  ---------------------"))
        print("  1. Balanced device scan (recommended)")
        print("  2. Cameras / NVR / DVR")
        print("  3. Media / TV / streaming devices")
        print("  4. Computers / NAS / servers")
        print("  5. Printers")
        print("  6. Enter custom ports")
        print("  7. Help")
        print("  0. Exit")

        choice = input(ccolor(YELLOW, "\n  Select [0-7]: ")).strip()
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
            value = input("  Enter ports (example: 22,80,443,445): ").strip()
            try:
                ports = [int(item.strip()) for item in value.split(",") if item.strip()]
                if not ports:
                    raise ValueError
                return sorted(set(ports))
            except Exception:
                error("Invalid port list.")
                continue
        if choice == "7":
            print()
            print("  This version first discovers live devices using ARP / neighbor table / nmap host discovery,")
            print("  then it scans only those discovered hosts. This reduces false positives and finds devices")
            print("  even when they do not expose web pages or camera ports.")
            print()
            print("  Important changes:")
            print("    • 80/443/8080 alone no longer cause camera-style false positives")
            print("    • devices are shown as live even when their exact type is still unknown")
            print("    • type identification now uses combined evidence: ports + banners + hostnames + vendors")
            print("    • deep scan is optional and adds mDNS, UPnP, SNMP, NetBIOS clues")
            print()
            input("  Press Enter to return...")
            continue
        warn("Invalid choice.")


# ─────────────────────────────────────────────
#  ARGUMENTS
# ─────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="Devices Finder – local network device discovery without root.",
        epilog=(
            "Examples:\n"
            "  python 'Devices Finder.py' --interactive\n"
            "  python 'Devices Finder.py' --subnet 192.168.1.0/24\n"
            "  python 'Devices Finder.py' --exclude-self --filter camera --deep-scan\n"
            "  python 'Devices Finder.py' --ports 22,80,443,445,631,554,8009,9100\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--subnet", "-s", help="Target subnet, for example 192.168.1.0/24")
    parser.add_argument("--ports", "-p", help="Comma-separated TCP ports to scan after discovery")
    parser.add_argument("--output-dir", "-o", default=DEFAULT_OUTPUT_DIR, help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--filter", "-f", choices=["all", "camera", "printer", "router", "storage", "pc", "phone", "tv", "speaker", "game_console", "iot", "vm", "unknown"], default="all", help="Show only one device type")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose nmap output")
    parser.add_argument("--no-color", action="store_true", help="Disable colored terminal output")
    parser.add_argument("--interactive", "-i", action="store_true", help="Choose a scan profile from a menu")
    parser.add_argument("--exclude-self", action="store_true", help="Hide your own device from the final results")
    parser.add_argument("--exclude", help="Comma-separated IPs or ranges to exclude")
    parser.add_argument("--timing", "-T", choices=["T0", "T1", "T2", "T3", "T4", "T5"], default="T4", help="Nmap timing template (default: T4)")
    parser.add_argument("--max-hostgroup", type=int, help="Nmap max-hostgroup value for the service scan")
    parser.add_argument("--deep-scan", action="store_true", help="Add mDNS, UPnP, SNMP and NetBIOS enrichment")
    return parser.parse_args()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
def main():
    global USE_COLOR
    args = parse_args()

    if args.no_color:
        USE_COLOR = False

    banner()
    print(ccolor(DIM, "  This script discovers devices on the same local network without root."))
    print(ccolor(DIM, "  It reduces false positives by separating live-host discovery from type detection."))
    print()

    check_dependencies(deep_scan=args.deep_scan)

    if args.interactive or (not args.ports and not args.subnet):
        ports = interactive_menu()
    elif args.ports:
        try:
            ports = sorted(set(int(item.strip()) for item in args.ports.split(",") if item.strip()))
        except ValueError:
            error("Invalid port list. Use comma-separated integers.")
            sys.exit(1)
    else:
        ports = DEFAULT_PORTS

    detected_subnet, local_ip = get_local_subnet()
    subnet = args.subnet or detected_subnet
    if args.subnet:
        success(f"Using user-specified subnet → {subnet}")
    if not subnet:
        error("Cannot continue without a subnet. Use --subnet.")
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
        info(f"Filtered by '{args.filter}': {len(results)}/{before} shown")

    print_summary(results)
    save_results(results, args, subnet, duration)


if __name__ == "__main__":
    main()
