import csv
import json
import os
import re
import socket
import ssl
import sys
import time
import hashlib
import urllib.parse
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict

USER_AGENT = "DedSec-LinkShield/5.0 (+safe-url-audit)"
TIMEOUT = 12
MAX_REDIRECTS = 18
PREVIEW_MAX_BYTES = 128_000
CONFIG_FILE = "linkshield_config_en.json"

SUSPICIOUS_TLDS = {
    "zip", "mov", "click", "top", "xyz", "work", "support", "help", "lol", "cam", "rest",
    "cfd", "gq", "tk", "ml", "cf", "ga"
}

URL_SHORTENERS = {
    "bit.ly", "t.co", "tinyurl.com", "goo.gl", "ow.ly", "is.gd", "buff.ly",
    "rebrand.ly", "cutt.ly", "soo.gd", "s.id", "rb.gy", "shorturl.at"
}

COMMON_DOMAINS = [
    "google.com", "accounts.google.com",
    "facebook.com", "instagram.com",
    "paypal.com", "microsoft.com", "live.com",
    "apple.com", "amazon.com",
    "discord.com", "steamcommunity.com",
    "tiktok.com", "x.com", "twitter.com",
]

TRACKING_PARAMS = {
    "utm_source","utm_medium","utm_campaign","utm_term","utm_content",
    "gclid","fbclid","msclkid","igshid","mc_cid","mc_eid",
    "ref","ref_","spm","yclid","_hsenc","_hsmi"
}

def ensure_requests() -> bool:
    try:
        import requests  # noqa
        return True
    except Exception:
        return False

def install_requests():
    import subprocess
    print("[*] Installing dependency: requests ...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=False)
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "requests"], check=False)

def have(cmd: str) -> bool:
    import shutil
    return shutil.which(cmd) is not None

def pkg_install(pkgs):
    import subprocess
    if not have("pkg"):
        return False
    if isinstance(pkgs, str):
        pkgs = [pkgs]
    print(f"[*] Installing via pkg: {' '.join(pkgs)}")
    subprocess.run(["pkg", "install", "-y", *pkgs], check=False)
    return True

def termux_clipboard_get() -> Optional[str]:
    if not have("termux-clipboard-get"):
        return None
    import subprocess
    try:
        p = subprocess.run(["termux-clipboard-get"], capture_output=True, text=True)
        s = (p.stdout or "").strip()
        return s if s else None
    except Exception:
        return None

def normalize_url(u: str) -> str:
    u = u.strip()
    if not u:
        return u
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", u):
        u = "http://" + u
    return u

def levenshtein(a: str, b: str) -> int:
    a, b = a.lower(), b.lower()
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            ins = cur[j - 1] + 1
            dele = prev[j] + 1
            rep = prev[j - 1] + (ca != cb)
            cur.append(min(ins, dele, rep))
        prev = cur
    return prev[-1]

def looks_like_ip(host: str) -> bool:
    return bool(re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host.strip()))

def punycode_to_unicode(host: str) -> str:
    try:
        return host.encode("ascii").decode("idna")
    except Exception:
        return host

def get_registeredish(host: str) -> str:
    parts = host.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host

def load_config() -> Dict:
    default = {
        "allow_domains": [],
        "deny_domains": [],
        "deny_keywords": ["free money", "gift card", "crypto giveaway"],
        "extra_shorteners": [],
        "treat_allow_as_low_risk": True
    }
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        for k, v in default.items():
            cfg.setdefault(k, v)
        return cfg
    except Exception:
        return default

def expand_url(url: str, timeout: int = TIMEOUT, max_hops: int = MAX_REDIRECTS):
    import requests
    chain = []
    cur = url
    err = None
    final = url

    for _ in range(max_hops):
        chain.append(cur)
        try:
            r = requests.head(cur, allow_redirects=False, timeout=timeout,
                              headers={"User-Agent": USER_AGENT})
            loc = r.headers.get("Location")
            if r.status_code in (301, 302, 303, 307, 308) and loc:
                cur = urllib.parse.urljoin(cur, loc)
                final = cur
                continue

            rg = requests.get(cur, allow_redirects=False, timeout=timeout, stream=True,
                              headers={"User-Agent": USER_AGENT})
            loc2 = rg.headers.get("Location")
            if rg.status_code in (301, 302, 303, 307, 308) and loc2:
                cur = urllib.parse.urljoin(cur, loc2)
                final = cur
                continue

            final = cur
            return chain, final, None
        except Exception as e:
            err = str(e)
            final = cur
            return chain, final, err

    return chain, final, "Too many redirects"

def dns_resolve(host: str) -> List[str]:
    ips = []
    try:
        infos = socket.getaddrinfo(host, None)
        for info in infos:
            ip = info[4][0]
            if ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    return ips

def tls_peek(host: str, port: int = 443, timeout: int = 6) -> Optional[dict]:
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                out = {}
                if "subject" in cert:
                    out["subject"] = " ".join("=".join(x) for tup in cert["subject"] for x in tup)
                if "issuer" in cert:
                    out["issuer"] = " ".join("=".join(x) for tup in cert["issuer"] for x in tup)
                for k in ("notBefore", "notAfter"):
                    if k in cert:
                        out[k] = cert[k]
                out["san"] = [v for (t, v) in cert.get("subjectAltName", []) if t == "DNS"]
                return out
    except Exception:
        return None

def safe_preview(url: str, timeout: int = TIMEOUT, max_bytes: int = PREVIEW_MAX_BYTES) -> dict:
    import requests
    out = {"ok": False}
    t0 = time.time()
    try:
        r = requests.get(url, timeout=timeout, stream=True, headers={"User-Agent": USER_AGENT})
        out["status_code"] = r.status_code
        out["headers"] = {k: v for k, v in r.headers.items()}
        out["content_type"] = (r.headers.get("Content-Type") or "").lower()
        out["content_length"] = r.headers.get("Content-Length")
        out["final_url"] = r.url

        title = None
        sample = b""
        if "text/html" in out["content_type"] or "application/xhtml" in out["content_type"] or out["content_type"] == "":
            data = b""
            for chunk in r.iter_content(chunk_size=8192):
                if not chunk:
                    break
                if len(data) < max_bytes:
                    data += chunk
                if len(sample) < 8192:
                    sample += chunk[: max(0, 8192 - len(sample))]
                if b"</title>" in data.lower() or len(data) >= max_bytes:
                    break
            try:
                text = data.decode("utf-8", errors="ignore")
                m = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
                if m:
                    title = re.sub(r"\s+", " ", m.group(1)).strip()
            except Exception:
                title = None
        else:
            for chunk in r.iter_content(chunk_size=4096):
                if not chunk:
                    break
                if len(sample) < 8192:
                    sample += chunk[: max(0, 8192 - len(sample))]
                if len(sample) >= 8192:
                    break

        out["title"] = title
        if sample:
            out["sample_sha256_8k"] = hashlib.sha256(sample).hexdigest()
            out["sample_bytes"] = len(sample)

        out["ok"] = True
    except Exception as e:
        out["error"] = str(e)
    out["response_time_ms"] = int((time.time() - t0) * 1000)
    return out

def clean_tracking_params(url: str) -> Tuple[str, List[str]]:
    p = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
    removed = []
    kept = []
    for k, v in q:
        if k.lower() in TRACKING_PARAMS or k.lower().startswith("utm_"):
            removed.append(k)
        else:
            kept.append((k, v))
    new_query = urllib.parse.urlencode(kept, doseq=True)
    cleaned = urllib.parse.urlunparse((p.scheme, p.netloc, p.path, p.params, new_query, p.fragment))
    return cleaned, sorted(set(removed))

def detect_encoded_params(url: str) -> List[str]:
    """Heuristics only."""
    parsed = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    notes = []

    for k, v in q:
        vv = v.strip()
        if len(vv) >= 80 and re.fullmatch(r"[A-Za-z0-9+/=_-]+", vv):
            # base64-ish
            notes.append(f"Param '{k}' looks base64-like (len {len(vv)})")
        if len(vv) >= 80 and re.fullmatch(r"[0-9a-fA-F]+", vv):
            notes.append(f"Param '{k}' looks hex-like (len {len(vv)})")
        if "%" in vv and len(vv) >= 120:
            notes.append(f"Param '{k}' is heavily percent-encoded (len {len(vv)})")

    # path encoding
    if "%" in parsed.path and len(parsed.path) >= 120:
        notes.append("Path is heavily percent-encoded")

    return notes

def chain_domain_hops(chain: List[str]) -> Tuple[List[str], int]:
    regs = []
    for u in chain:
        p = urllib.parse.urlparse(normalize_url(u))
        h = (p.hostname or "").lower()
        if h:
            regs.append(get_registeredish(h))
    # count changes
    changes = 0
    for i in range(1, len(regs)):
        if regs[i] != regs[i-1]:
            changes += 1
    return regs, changes

def whois_lookup(domain: str) -> Optional[str]:
    import subprocess
    if not have("whois"):
        pkg_install("whois")
    if not have("whois"):
        return None
    try:
        p = subprocess.run(["whois", domain], capture_output=True, text=True)
        txt = (p.stdout or "") + "\n" + (p.stderr or "")
        lines = txt.splitlines()[:80]
        return "\n".join(lines).strip()
    except Exception:
        return None

def analyze(final_url: str, cfg: Dict, chain: List[str]) -> Tuple[int, List[str], dict]:
    parsed = urllib.parse.urlparse(final_url)
    host = (parsed.hostname or "").strip().lower()
    scheme = (parsed.scheme or "").lower()

    reasons = []
    score = 0

    allow = set([x.lower() for x in cfg.get("allow_domains", [])])
    deny = set([x.lower() for x in cfg.get("deny_domains", [])])

    reg = get_registeredish(host) if host else ""
    regs, reg_changes = chain_domain_hops(chain)

    details = {
        "scheme": scheme,
        "host": host,
        "host_unicode": punycode_to_unicode(host) if host else "",
        "path": parsed.path or "",
        "query_len": len(parsed.query or ""),
        "port": parsed.port,
        "registrable": reg,
        "chain_registrables": regs,
        "chain_domain_changes": reg_changes,
        "is_shortener": host in (URL_SHORTENERS | set(cfg.get("extra_shorteners", []))) if host else False
    }

    if not host:
        reasons.append("No hostname detected")
        score += 60
        return min(100, score), reasons, details

    if host in deny or reg in deny:
        reasons.append("Domain matches local deny-list")
        score += 90

    if host in allow or reg in allow:
        reasons.append("Domain matches local allow-list")
        score -= 30

    if scheme not in ("http", "https"):
        reasons.append(f"Non-web scheme: {scheme}")
        score += 40

    if scheme == "http":
        reasons.append("Not HTTPS (HTTP only)")
        score += 18

    if "@" in final_url:
        reasons.append("Contains '@' (can hide real destination)")
        score += 22

    if looks_like_ip(host):
        reasons.append("Uses raw IP instead of domain")
        score += 20

    if host.startswith("xn--"):
        reasons.append("Punycode domain (possible look-alike)")
        score += 18

    if details["is_shortener"]:
        reasons.append("URL shortener domain (final destination may be hidden)")
        score += 10

    if reg_changes >= 2:
        reasons.append(f"Multiple domain hops in redirect chain ({reg_changes} changes)")
        score += 12

    if host.count("-") >= 3:
        reasons.append("Many hyphens in domain")
        score += 8

    path_q = (parsed.path or "") + "?" + (parsed.query or "")
    kw = ["login", "verify", "update", "secure", "account", "password", "billing", "wallet", "support", "signin"]
    hits = [k for k in kw if k in path_q.lower()]
    if hits:
        reasons.append("Suspicious keywords in path/query: " + ", ".join(hits[:8]))
        score += min(22, 4 * len(hits))

    for dk in [k.lower() for k in cfg.get("deny_keywords", [])]:
        if dk and dk in final_url.lower():
            reasons.append(f"Matches local deny keyword: '{dk}'")
            score += 25
            break

    if len(parsed.query or "") > 140:
        reasons.append("Very long query string")
        score += 10

    enc_notes = detect_encoded_params(final_url)
    if enc_notes:
        reasons.extend(enc_notes[:3])
        score += min(18, 6 * len(enc_notes))

    parts = host.split(".")
    tld = parts[-1] if parts else ""
    details["tld"] = tld
    if tld in SUSPICIOUS_TLDS:
        reasons.append(f"Often-abused TLD: .{tld}")
        score += 12

    if parsed.port and parsed.port not in (80, 443):
        reasons.append(f"Unusual port in URL: {parsed.port}")
        score += 10

    if len(parts) >= 4:
        reasons.append("Many subdomain levels")
        score += 6

    for d in COMMON_DOMAINS:
        dreg = get_registeredish(d)
        dist = levenshtein(reg, dreg)
        if reg != dreg and dist <= 2:
            reasons.append(f"Domain looks similar to '{dreg}' (distance {dist})")
            score += 22
            break

    score = max(0, min(100, score))
    if cfg.get("treat_allow_as_low_risk", True) and (host in allow or reg in allow):
        score = min(score, 10)

    return score, reasons, details

def verdict(score: int) -> str:
    if score >= 70:
        return "HIGH RISK"
    if score >= 40:
        return "SUSPICIOUS"
    if score >= 15:
        return "CAUTION"
    return "LOW RISK"

@dataclass
class ScanResult:
    original: str
    chain: List[str]
    final: str
    expand_error: Optional[str]
    score: int
    verdict: str
    reasons: List[str]
    dns: List[str]
    tls: Optional[dict]
    preview: Optional[dict]
    whois: Optional[str]
    cleaned_url: Optional[str]
    removed_tracking_params: List[str]
    details: dict

def scan_one(url: str, cfg: Dict, do_preview: bool = True, do_whois: bool = False) -> ScanResult:
    url = normalize_url(url)
    chain, final_url, err = expand_url(url)

    score, reasons, details = analyze(final_url, cfg, chain)
    host = details.get("host") or ""
    dns = dns_resolve(host) if host else []

    tls = tls_peek(host) if details.get("scheme") == "https" and host else None
    preview = safe_preview(final_url) if do_preview else None
    cleaned, removed = clean_tracking_params(final_url)

    whois_txt = whois_lookup(details.get("registrable","")) if do_whois and host else None

    return ScanResult(
        original=url,
        chain=chain,
        final=final_url,
        expand_error=err,
        score=score,
        verdict=verdict(score),
        reasons=reasons,
        dns=dns,
        tls=tls,
        preview=preview,
        whois=whois_txt,
        cleaned_url=cleaned if cleaned != final_url else None,
        removed_tracking_params=removed,
        details=details,
    )

def print_result(r: ScanResult):
    print("\n--- Link Shield Result ---")
    print(f"Original : {r.original}")
    if len(r.chain) > 1:
        print("Redirects:")
        for i, c in enumerate(r.chain, start=1):
            print(f"  {i}. {c}")
    print(f"Final    : {r.final}")

    if r.expand_error:
        print(f"\n[!] Expand error: {r.expand_error}")

    h = r.details.get("host") or ""
    hu = r.details.get("host_unicode") or ""
    if hu and hu != h:
        print(f"Host     : {h}  (unicode: {hu})")
    else:
        print(f"Host     : {h}")

    if r.details.get("chain_domain_changes", 0) > 0:
        print(f"Chain domains: {' -> '.join(r.details.get('chain_registrables', [])[:10])}")

    print(f"\nRisk     : {r.verdict} ({r.score}/100)")
    if r.reasons:
        print("Reasons  :")
        for x in r.reasons:
            print(f"  - {x}")
    else:
        print("Reasons  : None obvious")

    print("\nDNS/IPs  : " + (", ".join(r.dns) if r.dns else "(no resolution / unknown)"))

    if r.tls:
        print("\nTLS Cert :")
        for k in ("subject", "issuer", "notBefore", "notAfter"):
            if k in r.tls:
                print(f"  - {k}: {r.tls[k]}")
        sans = r.tls.get("san") if isinstance(r.tls, dict) else None
        if sans:
            print(f"  - SAN: {', '.join(sans[:8])}" + (" ..." if len(sans) > 8 else ""))

    if r.preview:
        print("\nPreview  :")
        if r.preview.get("ok"):
            print(f"  - HTTP status      : {r.preview.get('status_code')}")
            print(f"  - Response time    : {r.preview.get('response_time_ms')} ms")
            if r.preview.get("content_type"):
                print(f"  - Content-Type     : {r.preview.get('content_type')}")
            if r.preview.get("title"):
                print(f"  - Title            : {r.preview.get('title')}")
            if r.preview.get("sample_sha256_8k"):
                print(f"  - Sample SHA256(8k): {r.preview.get('sample_sha256_8k')}")
        else:
            print(f"  - Error: {r.preview.get('error')}")

    if r.cleaned_url and r.removed_tracking_params:
        print("\nClean URL: (removed trackers: " + ", ".join(r.removed_tracking_params[:8]) + (", ..." if len(r.removed_tracking_params)>8 else "") + ")")
        print(f"  {r.cleaned_url}")

def save_json(obj, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[*] Saved: {path}")

def export_markdown(r: ScanResult, path: str):
    lines = []
    lines.append("# Link Shield Report")
    lines.append(f"- Original: `{r.original}`")
    lines.append(f"- Final: `{r.final}`")
    lines.append(f"- Risk: **{r.verdict}** ({r.score}/100)")
    lines.append("")
    if r.reasons:
        lines.append("## Reasons")
        for x in r.reasons:
            lines.append(f"- {x}")
        lines.append("")
    lines.append("## Chain registrables")
    cr = r.details.get("chain_registrables", [])
    lines.append(" -> ".join(cr) if cr else "(none)")
    lines.append("")
    lines.append("## DNS/IPs")
    lines.append(", ".join(r.dns) if r.dns else "(none)")
    lines.append("")
    if r.preview and r.preview.get("ok"):
        lines.append("## Preview")
        lines.append(f"- HTTP status: {r.preview.get('status_code')}")
        lines.append(f"- Response time: {r.preview.get('response_time_ms')} ms")
        if r.preview.get("content_type"):
            lines.append(f"- Content-Type: {r.preview.get('content_type')}")
        if r.preview.get("title"):
            lines.append(f"- Title: {r.preview.get('title')}")
        if r.preview.get("sample_sha256_8k"):
            lines.append(f"- Sample SHA256(8k): {r.preview.get('sample_sha256_8k')}")
        lines.append("")
    if r.cleaned_url:
        lines.append("## Cleaned URL")
        lines.append(f"`{r.cleaned_url}`")
        lines.append("")
    if r.whois:
        lines.append("## WHOIS (excerpt)")
        lines.append("```")
        lines.extend(r.whois.splitlines()[:80])
        lines.append("```")
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[*] Markdown saved: {path}")

def export_csv(reports: List[dict], path: str):
    if not reports:
        return
    fields = ["original","final","score","verdict","host","registrable","chain_domain_changes"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in reports:
            det = r.get("details", {}) or {}
            w.writerow({
                "original": r.get("original",""),
                "final": r.get("final",""),
                "score": r.get("score",""),
                "verdict": r.get("verdict",""),
                "host": det.get("host",""),
                "registrable": det.get("registrable",""),
                "chain_domain_changes": det.get("chain_domain_changes",""),
            })
    print(f"[*] CSV saved: {path}")

def load_urls_from_file(path: str) -> List[str]:
    out = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            out.append(s)
    return out

def menu():
    cfg = load_config()
    if not ensure_requests():
        install_requests()
        if not ensure_requests():
            print("[!] Could not install 'requests'.")
            sys.exit(1)

    while True:
        print("\n=== DedSec Link Shield v5 (No-Root) ===")
        print("1) Scan a URL (preview on)")
        print("2) Scan from clipboard (Termux)")
        print("3) Scan with WHOIS (slower)")
        print("4) Batch scan from file (fast)")
        print("5) Config info")
        print("6) Exit")
        c = input("> ").strip()

        if c in ("1","3"):
            url = input("Paste URL (empty = clipboard): ").strip()
            if not url:
                clip = termux_clipboard_get()
                if not clip:
                    print("[!] Clipboard not available. Install: pkg install termux-api (and app)")
                    continue
                url = clip
            r = scan_one(url, cfg, do_preview=True, do_whois=(c=="3"))
            print_result(r)
            if input("\nExport report (JSON+MD)? (y/N): ").strip().lower() == "y":
                base = input("Base filename (default linkshield_report): ").strip() or "linkshield_report"
                save_json(r.__dict__, base + ".json")
                export_markdown(r, base + ".md")

        elif c == "2":
            clip = termux_clipboard_get()
            if not clip:
                print("[!] Clipboard not available. Install: pkg install termux-api (and app)")
                continue
            r = scan_one(clip, cfg, do_preview=True, do_whois=False)
            print_result(r)

        elif c == "4":
            fp = input("File path (one URL per line): ").strip()
            if not fp or not os.path.exists(fp):
                print("[!] File not found.")
                continue
            urls = load_urls_from_file(fp)
            if not urls:
                print("[!] No URLs found.")
                continue
            reports = []
            for i, u in enumerate(urls, start=1):
                print(f"\n[{i}/{len(urls)}] Scanning...")
                rr = scan_one(u, cfg, do_preview=False, do_whois=False)
                print_result(rr)
                reports.append(rr.__dict__)
            save_json(reports, "linkshield_batch_report.json")
            export_csv(reports, "linkshield_batch_report.csv")

        elif c == "5":
            print("\nConfig file:", CONFIG_FILE)
            print("Edit allow/deny lists to tune results (auto-created).")

        elif c == "6":
            break
        else:
            print("[!] Invalid choice.")

if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\n[!] Cancelled.")
