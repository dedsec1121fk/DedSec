#!/usr/bin/env python3
"""
Bug Hunter (no-root) — an authorized web security recon & misconfiguration scanner.

Design goals (v4):
- Capable by default; you can switch to safer/passive behavior with --safe-mode and --no-dirb.
- No runtime auto-install. Clear dependency hints instead.
- Bounded async concurrency (no massive task lists).
- Actionable reporting (JSON/CSV/HTML/PDF), de-duplicated findings, scope summary.
- Works without root (connect-based port checks; no raw sockets).

DISCLAIMER
Use only on targets you own or have explicit permission to test.

Dependencies
Required:  httpx
Optional (recommended): rich, beautifulsoup4, dnspython, reportlab

Install:
  python3 -m pip install -U httpx rich beautifulsoup4 dnspython reportlab
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import ipaddress
import json
import logging
import os
import random
import re
import socket
import ssl
import sys
import textwrap
from collections import Counter, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Deque, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse, parse_qsl

# ---------------- Optional imports ----------------

def _try_import(name: str):
    try:
        return __import__(name)
    except Exception:
        return None

httpx = _try_import("httpx")
rich = _try_import("rich")
bs4 = _try_import("bs4")
dns = _try_import("dns")  # dnspython
reportlab = _try_import("reportlab")


# ---------------- Logging ----------------

class _PlainFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        return base.replace("\n", " ").strip()

def setup_logger(debug: bool) -> logging.Logger:
    logger = logging.getLogger("bug_hunter")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.handlers.clear()

    if rich:
        try:
            from rich.logging import RichHandler
            handler = RichHandler(rich_tracebacks=debug, show_time=False, show_level=True, show_path=False)
            fmt = logging.Formatter("%(message)s")
            handler.setFormatter(fmt)
            logger.addHandler(handler)
            return logger
        except Exception:
            pass

    handler = logging.StreamHandler()
    handler.setFormatter(_PlainFormatter("%(levelname)s: %(message)s"))
    logger.addHandler(handler)
    return logger


# ---------------- Data models ----------------

SEV_ORDER = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "Info": 0}

@dataclass(frozen=True)
class Finding:
    category: str
    severity: str
    url: str
    details: str
    evidence: str = ""
    remediation: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def key(self) -> str:
        # Dedupe key: stable across runs except timestamp
        h = hashlib.sha256()
        h.update(self.category.encode())
        h.update(self.severity.encode())
        h.update(self.url.encode())
        h.update(self.details.encode())
        h.update(self.evidence.encode())
        return h.hexdigest()

@dataclass
class Technology:
    name: str
    version: str = ""
    confidence: int = 50
    source: str = ""

@dataclass
class ScopeInfo:
    target: str
    base_url: str
    hostname: str
    port: Optional[int]
    scheme: str
    resolved_ips: List[str] = field(default_factory=list)
    start_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_utc: str = ""

@dataclass
class ScanStats:
    http_requests: int = 0
    http_errors: int = 0
    bytes_downloaded: int = 0
    status_counts: Counter = field(default_factory=Counter)
    rate_limited: int = 0


# ---------------- Helpers ----------------

CSV_INJECTION_PREFIXES = ("=", "+", "-", "@")

def csv_safe(s: Any) -> str:
    """Mitigate CSV formula injection & ensure string."""
    if s is None:
        return ""
    out = str(s)
    if out.startswith(CSV_INJECTION_PREFIXES):
        return "'" + out
    return out

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()

def normalize_url(url: str) -> str:
    # Remove fragment; keep query
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path or "/", p.params, p.query, ""))

def first_nonempty_group(m: re.Match) -> str:
    for g in m.groups():
        if g:
            return g
    return m.group(0) or ""


# ---------------- Signatures / patterns ----------------

SEC_HEADERS = {
    "strict-transport-security": ("HSTS", "Add HSTS with a long max-age and includeSubDomains; preload if appropriate."),
    "content-security-policy": ("CSP", "Define a restrictive Content-Security-Policy to reduce XSS risk."),
    "x-frame-options": ("Clickjacking", "Set X-Frame-Options (DENY or SAMEORIGIN) or use CSP frame-ancestors."),
    "x-content-type-options": ("MIME Sniffing", "Set X-Content-Type-Options: nosniff."),
    "referrer-policy": ("Referrer Policy", "Set a Referrer-Policy appropriate for the site."),
    "permissions-policy": ("Permissions Policy", "Use Permissions-Policy to restrict powerful features."),
    "cross-origin-opener-policy": ("COOP", "Consider COOP to isolate browsing context and mitigate XS leaks."),
    "cross-origin-resource-policy": ("CORP", "Consider CORP to restrict resource loading across origins."),
    "cross-origin-embedder-policy": ("COEP", "Consider COEP when feasible to enable cross-origin isolation."),
}

COOKIE_FLAG_REMEDIATION = {
    "Secure": "Mark cookies as Secure so they're only sent over HTTPS.",
    "HttpOnly": "Mark cookies as HttpOnly to reduce XSS cookie theft risk.",
    "SameSite": "Set SameSite (Lax/Strict/None) to reduce CSRF risk; if None, also require Secure."
}

TECH_SIGS = [
    # (name, regex, source)
    ("nginx", re.compile(r"\bnginx(?:/([\d.]+))?\b", re.I), "header"),
    ("apache", re.compile(r"\bapache(?:/([\d.]+))?\b", re.I), "header"),
    ("cloudflare", re.compile(r"\bcloudflare\b", re.I), "header"),
    ("iis", re.compile(r"\bmicrosoft-iis(?:/([\d.]+))?\b", re.I), "header"),
    ("php", re.compile(r"\bphp(?:/([\d.]+))?\b", re.I), "header"),
    ("express", re.compile(r"\bexpress\b", re.I), "header"),
    ("wordpress", re.compile(r"wp-content|wp-includes|<meta[^>]+name=['\"]generator['\"][^>]+wordpress\s*([\d.]+)?", re.I), "body"),
    ("drupal", re.compile(r"\bdrupal\b|sites/all|sites/default", re.I), "body"),
    ("joomla", re.compile(r"\bjoomla\b|/components/com_", re.I), "body"),
]

VULN_PATTERNS: Dict[str, List[re.Pattern]] = {
    "SQL_Error_Disclosure": [
        re.compile(r"you have an error in your sql syntax", re.I),
        re.compile(r"unclosed quotation mark after the character string", re.I),
        re.compile(r"pg_query\(\):", re.I),
        re.compile(r"mysql_fetch", re.I),
    ],
    "Stack_Trace_Disclosure": [
        re.compile(r"traceback \(most recent call last\):", re.I),
        re.compile(r"system\.nullreferenceexception", re.I),
        re.compile(r"org\.springframework\.", re.I),
        re.compile(r"at\s+[\w.$]+\([\w.]+:\d+\)", re.I),
    ],
    "Debug_Keywords": [
        re.compile(r"\bdebug\b|\bdevelopment\b|\bstaging\b", re.I),
    ],
}

SECRET_PATTERNS: Dict[str, re.Pattern] = {
    "AWS_Access_Key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "AWS_Secret_Key": re.compile(r"\b(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])\b"),
    "Google_API_Key": re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"),
    "Stripe_Live_Key": re.compile(r"\bsk_live_[0-9a-zA-Z]{24,}\b"),
    "Private_Key_Block": re.compile(r"-----BEGIN (?:RSA|EC|DSA|OPENSSH) PRIVATE KEY-----"),
}

COMMON_SENSITIVE = [
    ".env", ".env.local", ".git/config", ".svn/entries", "composer.json", "composer.lock",
    "package.json", "yarn.lock", "pnpm-lock.yaml",
    "config.php", "wp-config.php", "settings.php",
    "web.config", "appsettings.json", "appsettings.Production.json",
    "phpinfo.php", "info.php", "server-status", "server-info",
    "backup.zip", "backup.tar.gz", "db.sql", "dump.sql",
    "swagger.json", "openapi.json",
    ".well-known/security.txt", "security.txt",
    "robots.txt", "sitemap.xml",
]

DEFAULT_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 465, 587, 993, 995,
    1433, 1521, 2049, 2375, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 9000
]

DEFAULT_DIR_WORDLIST = [
    "admin", "login", "administrator", "dashboard", "cpanel", "api", "graphql", "v1", "v2",
    "swagger", "openapi", "docs", "doc", "internal", "private",
    ".git", ".svn", ".env", "backup", "backups", "old", "dev", "test", "staging",
    "uploads", "upload", "static", "assets", "images", "js", "css"
]


# ---------------- Scanner ----------------

class BugHunter:
    def __init__(
        self,
        target: str,
        out_dir: Path,
        *,
        concurrency: int = 30,
        timeout: float = 12.0,
        user_agent: str = "BugHunter/4 (authorized-testing)",
        rate_limit_rps: float = 0.0,
        debug: bool = False,
        unsafe_active_tests: bool = False,
    ) -> None:
        if httpx is None:
            raise RuntimeError("Missing dependency: httpx. Install with: python3 -m pip install -U httpx")

        self.logger = setup_logger(debug)
        self.debug = debug
        self.unsafe_active_tests = unsafe_active_tests

        self.target = target if target.startswith(("http://", "https://")) else "https://" + target
        parsed = urlparse(self.target)

        # Correct parsing: hostname is without port; netloc may include port.
        self.scheme = parsed.scheme or "https"
        self.hostname = parsed.hostname or parsed.netloc.split(":")[0]
        self.port = parsed.port
        self.base_url = f"{self.scheme}://{parsed.netloc}" if parsed.netloc else f"{self.scheme}://{self.hostname}"
        self.base_url = self.base_url.rstrip("/")

        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)

        self.concurrency = max(1, int(concurrency))
        self.timeout = float(timeout)
        self.user_agent = user_agent
        self.rate_limit_rps = float(rate_limit_rps) if rate_limit_rps else 0.0
        self._rate_lock = asyncio.Lock()
        self._last_req_ts = 0.0

        self.sem = asyncio.Semaphore(self.concurrency)

        self.scope = ScopeInfo(
            target=self.target,
            base_url=self.base_url,
            hostname=self.hostname,
            port=self.port,
            scheme=self.scheme,
        )
        self.stats = ScanStats()
        self._findings: Dict[str, Finding] = {}
        self.technologies: Dict[str, Technology] = {}
        self.discovered_urls: Set[str] = set()
        self.discovered_js: Set[str] = set()
        self.discovered_endpoints: Set[str] = set()
        self.open_ports: List[int] = []

        self._client: Optional["httpx.AsyncClient"] = None

    # ---------- core plumbing ----------

    async def _throttle(self) -> None:
        if self.rate_limit_rps <= 0:
            return
        async with self._rate_lock:
            now = asyncio.get_running_loop().time()
            min_gap = 1.0 / self.rate_limit_rps
            wait = (self._last_req_ts + min_gap) - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_req_ts = asyncio.get_running_loop().time()

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> Optional["httpx.Response"]:
        assert self._client is not None
        url = normalize_url(url)
        hdrs = {"User-Agent": self.user_agent, "Accept": "*/*"}
        if headers:
            hdrs.update(headers)

        async with self.sem:
            await self._throttle()
            try:
                r = await self._client.request(method, url, headers=hdrs, follow_redirects=follow_redirects)
                self.stats.http_requests += 1
                self.stats.status_counts[str(r.status_code)] += 1
                if r.status_code == 429:
                    self.stats.rate_limited += 1
                # r.content triggers download; only count bytes when accessed
                return r
            except Exception as e:
                self.stats.http_errors += 1
                if self.debug:
                    self.logger.exception(f"HTTP {method} failed: {url} ({e})")
                else:
                    self.logger.debug(f"HTTP {method} failed: {url} ({e})")
                return None

    def add_finding(self, finding: Finding) -> None:
        # Normalize severity
        sev = finding.severity.capitalize()
        if sev not in SEV_ORDER:
            sev = "Info"
        finding = Finding(
            category=finding.category,
            severity=sev,
            url=normalize_url(finding.url),
            details=finding.details.strip(),
            evidence=finding.evidence.strip(),
            remediation=finding.remediation.strip(),
            timestamp=finding.timestamp,
        )
        self._findings.setdefault(finding.key(), finding)

    def add_tech(self, name: str, version: str = "", confidence: int = 50, source: str = "") -> None:
        key = name.lower()
        existing = self.technologies.get(key)
        if existing:
            # keep highest confidence; prefer version if new has it
            if confidence > existing.confidence:
                existing.confidence = confidence
            if version and (not existing.version):
                existing.version = version
            if source and (not existing.source):
                existing.source = source
        else:
            self.technologies[key] = Technology(name=name, version=version, confidence=confidence, source=source)

    # ---------- parsing & discovery ----------

    def _same_host(self, url: str) -> bool:
        try:
            p = urlparse(url)
            if not p.netloc:
                return True
            return (p.hostname or "").lower() == self.hostname.lower()
        except Exception:
            return False

    def _extract_links(self, html: str, base: str) -> Set[str]:
        links: Set[str] = set()

        if bs4:
            try:
                from bs4 import BeautifulSoup  # type: ignore
                soup = BeautifulSoup(html, "html.parser")
                for a in soup.find_all("a", href=True):
                    links.add(urljoin(base, a["href"]))
                for s in soup.find_all("script", src=True):
                    src = urljoin(base, s["src"])
                    links.add(src)
                for l in soup.find_all("link", href=True):
                    links.add(urljoin(base, l["href"]))
                return links
            except Exception:
                pass

        # Fallback: regex-based extraction
        for m in re.finditer(r"""(?:href|src)=['"]([^'"]+)['"]""", html, flags=re.I):
            links.add(urljoin(base, m.group(1)))
        return links

    def _extract_js_urls(self, html: str, base: str) -> Set[str]:
        out: Set[str] = set()
        if bs4:
            try:
                from bs4 import BeautifulSoup  # type: ignore
                soup = BeautifulSoup(html, "html.parser")
                for s in soup.find_all("script", src=True):
                    out.add(urljoin(base, s["src"]))
                return out
            except Exception:
                pass
        for m in re.finditer(r"""<script[^>]+src=['"]([^'"]+)['"]""", html, flags=re.I):
            out.add(urljoin(base, m.group(1)))
        return out

    def _extract_endpoints_from_js(self, js_text: str) -> Set[str]:
        # Extract absolute URLs and common API-like paths.
        endpoints: Set[str] = set()

        # Absolute URLs
        for m in re.finditer(r"""https?://[^\s'"]+""", js_text):
            endpoints.add(m.group(0))

        # Relative paths that look like endpoints
        for m in re.finditer(r"""['"](/(?:api|graphql|v1|v2|admin|internal|private|auth)[^'"]*)['"]""", js_text, flags=re.I):
            endpoints.add(urljoin(self.base_url + "/", m.group(1)))

        return endpoints

    def _scan_secrets(self, blob: str, where: str) -> None:
        for name, pat in SECRET_PATTERNS.items():
            if pat.search(blob):
                self.add_finding(Finding(
                    category="Possible_Secret_Leak",
                    severity="High" if name in ("Private_Key_Block",) else "Medium",
                    url=where,
                    details=f"Pattern matched: {name}",
                    evidence=(pat.search(blob).group(0)[:80] if pat.search(blob) else ""),
                    remediation="Remove secrets from client-facing files; rotate/revoke exposed credentials; add secret scanning to CI."
                ))

    # ---------- individual checks ----------

    async def resolve_dns(self) -> None:
        ips: Set[str] = set()

        # Basic A/AAAA via socket (works without dnspython)
        try:
            for family, _, _, _, sockaddr in socket.getaddrinfo(self.hostname, None):
                if family == socket.AF_INET:
                    ips.add(sockaddr[0])
                elif family == socket.AF_INET6:
                    ips.add(sockaddr[0])
        except Exception as e:
            self.add_finding(Finding(
                category="DNS_Resolution_Failed",
                severity="Low",
                url=self.base_url,
                details=f"Failed to resolve hostname: {e}",
                remediation="Check DNS records and availability."
            ))

        # Additional records via dnspython if available
        if dns:
            try:
                import dns.resolver  # type: ignore

                def _txt(name: str) -> List[str]:
                    try:
                        answers = dns.resolver.resolve(name, "TXT")
                        txts = []
                        for r in answers:
                            # dnspython returns bytes segments; join
                            segs = []
                            for s in getattr(r, "strings", []):
                                segs.append(s.decode(errors="ignore") if isinstance(s, (bytes, bytearray)) else str(s))
                            if segs:
                                txts.append("".join(segs))
                            else:
                                txts.append(str(r))
                        return txts
                    except Exception:
                        return []

                # SPF / DMARC (TXT records)
                spf = [t for t in _txt(self.hostname) if "v=spf1" in t.lower()]
                if not spf:
                    self.add_finding(Finding(
                        category="Email_SPF_Missing",
                        severity="Info",
                        url=self.hostname,
                        details="No SPF record detected (v=spf1) on apex/host.",
                        remediation="Publish an SPF record if the domain sends email; verify alignment with your mail providers."
                    ))
                dmarc = _txt(f"_dmarc.{self.hostname}")
                if not any("v=dmarc1" in t.lower() for t in dmarc):
                    self.add_finding(Finding(
                        category="Email_DMARC_Missing",
                        severity="Info",
                        url=self.hostname,
                        details="No DMARC record detected at _dmarc.",
                        remediation="Publish a DMARC policy (start with p=none) to improve spoofing resistance."
                    ))

                # CAA
                try:
                    caa = dns.resolver.resolve(self.hostname, "CAA")
                    _ = list(caa)  # if exists, fine
                except Exception:
                    self.add_finding(Finding(
                        category="CAA_Missing",
                        severity="Info",
                        url=self.hostname,
                        details="No CAA record detected.",
                        remediation="Consider publishing CAA to restrict which CAs can issue certificates for the domain."
                    ))

            except Exception as e:
                self.logger.debug(f"DNS extra checks skipped: {e}")

        self.scope.resolved_ips = sorted(ips)

    async def tls_analysis(self) -> None:
        if self.scheme != "https":
            return
        host = self.hostname
        port = self.port or 443

        def _probe() -> Dict[str, Any]:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    version = ssock.version()
            return {"cert": cert, "cipher": cipher, "tls_version": version}

        try:
            info = await asyncio.to_thread(_probe)
        except Exception as e:
            self.add_finding(Finding(
                category="TLS_Handshake_Failed",
                severity="Low",
                url=f"{host}:{port}",
                details=f"TLS connection failed: {e}",
                remediation="Check certificate validity and TLS configuration."
            ))
            return

        tls_ver = info.get("tls_version", "")
        cipher = info.get("cipher", ("", "", ""))[0]
        self.add_finding(Finding(
            category="TLS_Info",
            severity="Info",
            url=f"{host}:{port}",
            details=f"Negotiated {tls_ver} with cipher {cipher}",
        ))

        cert = info.get("cert") or {}
        # Expiration check
        try:
            not_after = cert.get("notAfter")
            # Format like 'Jun  1 12:00:00 2026 GMT'
            exp = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            days = (exp - datetime.now(timezone.utc)).days
            if days < 0:
                sev = "High"
                det = f"Certificate expired {abs(days)} days ago (expired on {exp.date()})"
            elif days <= 14:
                sev = "Medium"
                det = f"Certificate expires soon ({days} days left, on {exp.date()})"
            else:
                sev = "Info"
                det = f"Certificate valid until {exp.date()} ({days} days left)"
            self.add_finding(Finding(
                category="TLS_Certificate_Expiry",
                severity=sev,
                url=f"{host}:{port}",
                details=det,
                remediation="Renew and deploy a valid certificate before expiration; automate renewals where possible."
            ))
        except Exception:
            pass

    async def fetch_baseline(self) -> Tuple[Optional[str], Dict[str, str], List[str], str]:
        """Fetch / and return (body, headers, set-cookie, final_url)."""
        r = await self._request("GET", self.base_url + "/")
        if not r:
            return None, {}, [], self.base_url + "/"

        final_url = str(r.url)
        headers = {k.lower(): v for k, v in r.headers.items()}
        cookies = r.headers.get_list("set-cookie") if hasattr(r.headers, "get_list") else ([r.headers.get("set-cookie")] if r.headers.get("set-cookie") else [])
        body = ""
        try:
            body = r.text or ""
            self.stats.bytes_downloaded += len(r.content or b"")
        except Exception:
            body = ""
        return body, headers, [c for c in cookies if c], final_url

    async def check_security_headers(self, headers: Dict[str, str], url: str) -> None:
        for key, (title, remediation) in SEC_HEADERS.items():
            if key not in headers:
                self.add_finding(Finding(
                    category="Missing_Security_Header",
                    severity="Low" if key in ("referrer-policy", "permissions-policy", "cross-origin-resource-policy", "cross-origin-opener-policy", "cross-origin-embedder-policy") else "Medium",
                    url=url,
                    details=f"Missing header: {key} ({title})",
                    remediation=remediation
                ))

        # Cookie flags
        # We can't reliably parse all cookies without a library; do a best-effort for Set-Cookie header strings.
        set_cookies = headers.get("set-cookie", "")
        if set_cookies:
            # Split on comma only when it looks like multiple cookies; best-effort
            parts = re.split(r",(?=[^;]+?=)", set_cookies)
            for c in parts:
                c_l = c.lower()
                missing: List[str] = []
                if "secure" not in c_l and self.scheme == "https":
                    missing.append("Secure")
                if "httponly" not in c_l:
                    missing.append("HttpOnly")
                if "samesite" not in c_l:
                    missing.append("SameSite")
                if missing:
                    self.add_finding(Finding(
                        category="Cookie_Flags_Missing",
                        severity="Low",
                        url=url,
                        details=f"Cookie missing flags: {', '.join(missing)}",
                        evidence=c.strip()[:200],
                        remediation=" ".join(COOKIE_FLAG_REMEDIATION[m] for m in missing if m in COOKIE_FLAG_REMEDIATION)
                    ))

    async def detect_tech(self, headers: Dict[str, str], body: str, url: str) -> None:
        # Correct header matching: build "key: value" lines and search
        header_lines = "\n".join([f"{k}: {v}" for k, v in headers.items()]).lower()
        body_l = (body or "").lower()

        for name, pat, src in TECH_SIGS:
            hay = header_lines if src == "header" else body_l
            m = pat.search(hay)
            if m:
                ver = ""
                if m.lastindex:
                    ver = first_nonempty_group(m)
                self.add_tech(name=name, version=ver or "", confidence=80 if src == "header" else 70, source=src)
        # Hint from headers
        if "x-powered-by" in headers:
            self.add_tech(headers["x-powered-by"].split()[0], source="header", confidence=60)

        # Store a finding for tech summary (Info)
        if self.technologies:
            tech_list = ", ".join(
                sorted({f"{t.name}{('/' + t.version) if t.version else ''}" for t in self.technologies.values()})
            )
            self.add_finding(Finding(
                category="Tech_Detected",
                severity="Info",
                url=url,
                details=f"Detected: {tech_list}"
            ))

    async def check_vuln_patterns(self, url: str, body: str) -> None:
        if not body:
            return
        for vname, patterns in VULN_PATTERNS.items():
            for pat in patterns:
                if pat.search(body):
                    sev = "Medium" if vname != "Debug_Keywords" else "Low"
                    self.add_finding(Finding(
                        category=vname,
                        severity=sev,
                        url=url,
                        details=f"Response contains indicators of {vname.replace('_', ' ')}",
                        evidence=pat.pattern[:120],
                        remediation="Review error handling and disable verbose debug output in production."
                    ))
                    break

    async def check_cors(self, url: str) -> None:
        # Non-destructive: send Origin header and evaluate response.
        origin = f"https://{''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(10))}.example"
        r = await self._request("GET", url, headers={"Origin": origin})
        if not r:
            return
        aco = r.headers.get("access-control-allow-origin", "")
        acc = r.headers.get("access-control-allow-credentials", "")

        if aco == "*":
            if acc.lower() == "true":
                self.add_finding(Finding(
                    category="CORS_Misconfig",
                    severity="High",
                    url=url,
                    details="Access-Control-Allow-Origin is '*' while Allow-Credentials is true.",
                    remediation="Do not combine '*' with credentials. Reflect/allow only trusted origins or disable credentials."
                ))
            else:
                self.add_finding(Finding(
                    category="CORS_Wildcard",
                    severity="Low",
                    url=url,
                    details="Access-Control-Allow-Origin is '*'.",
                    remediation="Consider restricting CORS to trusted origins if the resource is sensitive."
                ))
        elif aco and aco.strip() == origin:
            self.add_finding(Finding(
                category="CORS_Reflects_Origin",
                severity="Medium",
                url=url,
                details="CORS appears to reflect arbitrary Origin.",
                evidence=f"Origin: {origin} -> ACAO: {aco}",
                remediation="Validate Origin against an allowlist; avoid reflecting arbitrary Origin values."
            ))

    async def check_http_methods(self, url: str) -> None:
        # Always do OPTIONS. Active probing (TRACE/PUT/DELETE/CONNECT) is controlled by --safe-mode.
        r = await self._request("OPTIONS", url)
        if r and "allow" in r.headers:
            allow = r.headers.get("allow", "")
            self.add_finding(Finding(
                category="HTTP_Methods_Allowed",
                severity="Info",
                url=url,
                details=f"Allow: {allow}"
            ))

        if not self.unsafe_active_tests:
            return

        # Active probing (still non-destructive in intent; can be risky on misconfigured servers)
        for m in ["TRACE", "PUT", "DELETE", "CONNECT"]:
            rr = await self._request(m, url, follow_redirects=False)
            if rr and rr.status_code < 500 and rr.status_code not in (404, 405):
                self.add_finding(Finding(
                    category="Potential_Risky_HTTP_Method",
                    severity="Medium",
                    url=url,
                    details=f"{m} returned status {rr.status_code}",
                    remediation="Disable unnecessary HTTP methods on edge/proxy/app servers."
                ))

    async def check_sensitive_files(self) -> None:
        async def _check(path: str) -> None:
            url = urljoin(self.base_url + "/", path.lstrip("/"))
            r = await self._request("GET", url, follow_redirects=False)
            if not r:
                return
            if r.status_code in (200, 206):
                # Basic heuristic: avoid flagging common public files too strongly
                sev = "High" if any(x in path for x in (".env", ".git", "wp-config", "appsettings")) else "Medium"
                self.add_finding(Finding(
                    category="Sensitive_File_Exposed",
                    severity=sev,
                    url=url,
                    details=f"Accessible sensitive path: {path} (HTTP {r.status_code})",
                    remediation="Remove from web root; deny access at web server; move secrets to env/secret store."
                ))
                try:
                    body = r.text[:20000]
                    self._scan_secrets(body, url)
                except Exception:
                    pass
            elif r.status_code in (301, 302, 307, 308):
                loc = r.headers.get("location", "")
                if loc and ("login" in loc.lower() or "signin" in loc.lower()):
                    self.add_finding(Finding(
                        category="Sensitive_Path_Redirect",
                        severity="Info",
                        url=url,
                        details=f"{path} redirects to {loc}",
                    ))

        await self._run_stream(_check, COMMON_SENSITIVE)

    async def port_scan(self, ports: List[int]) -> None:
        # Connect scan without root. Keep concurrency bounded.
        host = self.hostname

        async def _check_port(p: int) -> None:
            try:
                async with self.sem:
                    fut = asyncio.open_connection(host, p)
                    reader, writer = await asyncio.wait_for(fut, timeout=self.timeout)
                    writer.close()
                    try:
                        await writer.wait_closed()
                    except Exception:
                        pass
                    self.open_ports.append(p)
            except Exception:
                return

        await self._run_stream(_check_port, ports)
        self.open_ports.sort()
        if self.open_ports:
            self.add_finding(Finding(
                category="Open_Ports",
                severity="Info",
                url=host,
                details=f"Open TCP ports (connect scan): {', '.join(map(str, self.open_ports))}",
                remediation="Close or firewall non-essential services; ensure management ports require strong auth."
            ))

    async def directory_bruteforce(self, wordlist: List[str]) -> None:
        # Controlled by --safe-mode (active probes off) and --no-dirb.
        if not self.unsafe_active_tests:
            self.add_finding(Finding(
                category="Directory_Bruteforce_Skipped",
                severity="Info",
                url=self.base_url,
                details="Directory brute-force is disabled in safe mode (remove --safe-mode to enable active probes)."
            ))
            return

        async def _check(seg: str) -> None:
            url = urljoin(self.base_url + "/", seg.strip("/") + "/")
            r = await self._request("GET", url, follow_redirects=False)
            if not r:
                return
            if r.status_code in (200, 204, 301, 302, 307, 308, 401, 403):
                sev = "Low"
                if r.status_code == 200 and ("index of /" in (r.text or "").lower()):
                    sev = "Medium"
                    self.add_finding(Finding(
                        category="Directory_Listing",
                        severity=sev,
                        url=url,
                        details="Possible directory listing detected (Index of /).",
                        remediation="Disable directory listing on the web server."
                    ))
                self.add_finding(Finding(
                    category="Interesting_Path",
                    severity=sev,
                    url=url,
                    details=f"Potentially interesting path discovered (HTTP {r.status_code})"
                ))

        await self._run_stream(_check, wordlist)

    async def crawl(self, depth: int = 2, max_pages: int = 200) -> None:
        # Depth-limited BFS. Uses deque for O(1) pops.
        seen: Set[str] = set()
        q: Deque[Tuple[str, int]] = deque()
        start = self.base_url + "/"
        q.append((start, 0))
        seen.add(normalize_url(start))

        while q and len(seen) <= max_pages:
            url, d = q.popleft()
            if d > depth:
                continue
            r = await self._request("GET", url)
            if not r:
                continue

            ct = r.headers.get("content-type", "")
            if "text/html" not in ct.lower():
                continue

            try:
                body = r.text or ""
                self.stats.bytes_downloaded += len(r.content or b"")
            except Exception:
                body = ""

            self.discovered_urls.add(url)

            # Basic vulns / secrets in pages
            await self.check_vuln_patterns(url, body)
            self._scan_secrets(body, url)

            links = self._extract_links(body, url)
            for link in links:
                link = normalize_url(link)
                if not self._same_host(link):
                    continue
                if link not in seen:
                    seen.add(link)
                    if d + 1 <= depth:
                        q.append((link, d + 1))

            # Capture JS sources for later
            for jsu in self._extract_js_urls(body, url):
                jsu = normalize_url(jsu)
                if self._same_host(jsu):
                    self.discovered_js.add(jsu)

        if self.discovered_urls:
            self.add_finding(Finding(
                category="Crawl_Summary",
                severity="Info",
                url=self.base_url,
                details=f"Crawled {len(self.discovered_urls)} HTML pages (depth={depth}, max_pages={max_pages})."
            ))

    async def analyze_js(self, max_files: int = 50) -> None:
        js_list = list(self.discovered_js)[:max_files]
        if not js_list:
            return

        async def _fetch(js_url: str) -> None:
            r = await self._request("GET", js_url)
            if not r:
                return
            ct = r.headers.get("content-type", "")
            if "javascript" not in ct.lower() and not js_url.lower().endswith((".js", ".mjs")):
                return
            try:
                txt = r.text or ""
                self.stats.bytes_downloaded += len(r.content or b"")
            except Exception:
                return

            self._scan_secrets(txt, js_url)

            endpoints = self._extract_endpoints_from_js(txt)
            for ep in endpoints:
                ep_n = normalize_url(ep)
                self.discovered_endpoints.add(ep_n)

        await self._run_stream(_fetch, js_list)

        if self.discovered_endpoints:
            self.add_finding(Finding(
                category="JS_Endpoints_Discovered",
                severity="Info",
                url=self.base_url,
                details=f"Discovered {len(self.discovered_endpoints)} endpoints/URLs from JavaScript.",
            ))

    async def passive_wayback(self, limit: int = 200) -> None:
        # Passive recon: list known URLs from the Wayback Machine (CDX API).
        # Opt-in? This does not touch the target directly but calls an external service.
        # We'll do it only if user enables unsafe_active_tests OR explicit module.
        # (Still safe to run; respecting privacy/scope is on user.)
        if not self.unsafe_active_tests:
            return

        cdx = "https://web.archive.org/cdx/search/cdx"
        params = {
            "url": self.hostname + "/*",
            "output": "json",
            "fl": "original",
            "collapse": "urlkey",
            "filter": "statuscode:200",
            "limit": str(limit),
        }
        qs = "&".join(f"{k}={httpx.QueryParams({k:v})[k]}" for k, v in params.items())
        url = f"{cdx}?{qs}"

        r = await self._request("GET", url)
        if not r:
            return
        try:
            data = r.json()
            if isinstance(data, list) and len(data) > 1:
                urls = [row[0] for row in data[1:] if row and isinstance(row, list)]
                # Keep only same host
                urls = [normalize_url(u) for u in urls if self._same_host(u)]
                for u in urls:
                    self.discovered_urls.add(u)
                self.add_finding(Finding(
                    category="Wayback_URLs",
                    severity="Info",
                    url=self.hostname,
                    details=f"Retrieved {len(urls)} unique URLs from Wayback Machine (limit={limit})."
                ))
        except Exception as e:
            self.logger.debug(f"Wayback parse failed: {e}")

    # ---------- bounded streaming runner ----------

    async def _run_stream(self, fn, items: Iterable[Any]) -> None:
        # Streaming task runner: keeps bounded number of tasks to reduce memory.
        pending: Set[asyncio.Task] = set()
        max_pending = max(10, self.concurrency * 2)

        async def _wrap(it):
            try:
                await fn(it)
            except Exception as e:
                if self.debug:
                    self.logger.exception(f"Task failed for {it}: {e}")
                else:
                    self.logger.debug(f"Task failed for {it}: {e}")

        for it in items:
            pending.add(asyncio.create_task(_wrap(it)))
            if len(pending) >= max_pending:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                _ = done  # just drain

        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

    # ---------- orchestrator ----------

    async def scan(
        self,
        *,
        do_ports: bool = True,
        ports: Optional[List[int]] = None,
        do_dns: bool = True,
        do_tls: bool = True,
        do_headers: bool = True,
        do_tech: bool = True,
        do_cors: bool = True,
        do_methods: bool = True,
        do_sensitive: bool = True,
        do_crawl: bool = True,
        crawl_depth: int = 2,
        max_pages: int = 200,
        do_js: bool = True,
        do_dirb: bool = False,
        dir_wordlist: Optional[List[str]] = None,
        do_wayback: bool = False,
    ) -> None:
        limits = httpx.Limits(max_connections=self.concurrency, max_keepalive_connections=max(10, self.concurrency // 2))
        timeout = httpx.Timeout(self.timeout)
        async with httpx.AsyncClient(limits=limits, timeout=timeout, verify=True) as client:
            self._client = client

            self.logger.info(f"Target: {self.base_url}  (host={self.hostname}, port={self.port or 'default'})")
            if not self.unsafe_active_tests:
                self.logger.info("Safe mode enabled: active probes disabled (remove --safe-mode to re-enable).")

            if do_dns:
                await self.resolve_dns()

            # Baseline
            body, headers, setcookies, final = await self.fetch_baseline()
            if body is None:
                self.add_finding(Finding(
                    category="Target_Unreachable",
                    severity="High",
                    url=self.base_url,
                    details="Failed to fetch baseline page.",
                    remediation="Verify the target is reachable and that you have permission to test it."
                ))
            else:
                if do_headers:
                    await self.check_security_headers(headers, final)
                if do_tech:
                    await self.detect_tech(headers, body, final)
                await self.check_vuln_patterns(final, body)
                self._scan_secrets(body, final)

                # quick endpoint discovery (passive, on-target)
                for p in ("robots.txt", "sitemap.xml", ".well-known/security.txt", "security.txt"):
                    self.discovered_urls.add(urljoin(self.base_url + "/", p))

            if do_tls:
                await self.tls_analysis()

            if do_ports and self.hostname:
                await self.port_scan(ports or DEFAULT_PORTS)

            if do_cors:
                await self.check_cors(final)

            if do_methods:
                await self.check_http_methods(final)

            if do_sensitive:
                await self.check_sensitive_files()

            if do_crawl:
                await self.crawl(depth=crawl_depth, max_pages=max_pages)

            if do_js:
                await self.analyze_js()

            if do_dirb:
                await self.directory_bruteforce(dir_wordlist or DEFAULT_DIR_WORDLIST)

            if do_wayback:
                await self.passive_wayback()

            self._client = None
            self.scope.end_utc = now_utc()

    # ---------- exports ----------

    def findings(self) -> List[Finding]:
        fs = list(self._findings.values())
        fs.sort(key=lambda f: (-SEV_ORDER.get(f.severity, 0), f.category, f.url))
        return fs

    def _summary(self) -> Dict[str, Any]:
        fs = self.findings()
        by_sev = Counter(f.severity for f in fs)
        by_cat = Counter(f.category for f in fs)
        return {
            "scope": asdict(self.scope),
            "stats": {
                "http_requests": self.stats.http_requests,
                "http_errors": self.stats.http_errors,
                "bytes_downloaded": self.stats.bytes_downloaded,
                "status_counts": dict(self.stats.status_counts),
                "rate_limited_429": self.stats.rate_limited,
            },
            "counts": {
                "total_findings": len(fs),
                "by_severity": dict(by_sev),
                "top_categories": by_cat.most_common(10),
            },
            "open_ports": self.open_ports,
            "technologies": [asdict(t) for t in sorted(self.technologies.values(), key=lambda x: (-x.confidence, x.name.lower()))],
            "discovered": {
                "urls": sorted(self.discovered_urls)[:1000],
                "js_files": sorted(self.discovered_js)[:500],
                "endpoints": sorted(self.discovered_endpoints)[:1000],
            }
        }

    def export_json(self) -> Path:
        out = self.out_dir / "report.json"
        payload = self._summary()
        payload["findings"] = [asdict(f) for f in self.findings()]
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return out

    def export_csv(self) -> Path:
        out = self.out_dir / "report.csv"
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            w.writerow(["timestamp", "severity", "category", "url", "details", "evidence", "remediation"])
            for fd in self.findings():
                w.writerow([
                    csv_safe(fd.timestamp),
                    csv_safe(fd.severity),
                    csv_safe(fd.category),
                    csv_safe(fd.url),
                    csv_safe(fd.details),
                    csv_safe(fd.evidence),
                    csv_safe(fd.remediation),
                ])
        return out

    def export_html(self) -> Path:
        out = self.out_dir / "report.html"
        data = self._summary()
        findings = [asdict(f) for f in self.findings()]

        # Simple self-contained HTML (no jinja dependency)
        def esc(s: str) -> str:
            return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        rows = []
        for fnd in findings:
            rows.append(
                f"<tr>"
                f"<td>{esc(fnd['timestamp'])}</td>"
                f"<td class='sev sev-{esc(fnd['severity']).lower()}'>{esc(fnd['severity'])}</td>"
                f"<td>{esc(fnd['category'])}</td>"
                f"<td><a href='{esc(fnd['url'])}' target='_blank' rel='noreferrer'>{esc(fnd['url'])}</a></td>"
                f"<td>{esc(fnd['details'])}</td>"
                f"</tr>"
            )
        html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bug Hunter Report</title>
<style>
body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 24px; }}
h1 {{ margin: 0 0 8px 0; }}
.small {{ color: #666; }}
.card {{ border: 1px solid #ddd; border-radius: 12px; padding: 16px; margin: 12px 0; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
th, td {{ border-bottom: 1px solid #eee; padding: 10px; text-align: left; vertical-align: top; }}
th {{ background: #fafafa; position: sticky; top: 0; }}
.sev {{ font-weight: 700; }}
.sev-critical {{ color: #7a0012; }}
.sev-high {{ color: #b10000; }}
.sev-medium {{ color: #c26d00; }}
.sev-low {{ color: #1f5b99; }}
.sev-info {{ color: #444; }}
input {{ padding: 8px; width: 360px; max-width: 100%; border-radius: 10px; border: 1px solid #ccc; }}
.badge {{ display:inline-block; padding: 2px 8px; border-radius: 999px; background:#f2f2f2; margin-right:6px; }}
</style>
</head>
<body>
<h1>🐛 Bug Hunter Report</h1>
<div class="small">Generated: {esc(data['scope']['end_utc'] or now_utc())} (UTC) — Target: {esc(data['scope']['base_url'])}</div>

<div class="card">
<b>Scope</b><br>
<span class="badge">Host: {esc(data['scope']['hostname'])}</span>
<span class="badge">IPs: {esc(", ".join(data['scope']['resolved_ips']))}</span>
<span class="badge">Open Ports: {esc(", ".join(map(str, data.get('open_ports', []))))}</span>
<div class="small" style="margin-top:8px">
HTTP requests: {data['stats']['http_requests']} — Errors: {data['stats']['http_errors']} — 429s: {data['stats']['rate_limited_429']}
</div>
</div>

<div class="card">
<b>Findings</b> (total: {len(findings)})<br>
<input id="q" placeholder="Filter… (severity/category/url/text)" oninput="filter()">
<table id="t">
<thead>
<tr><th>Time (UTC)</th><th>Severity</th><th>Category</th><th>URL</th><th>Details</th></tr>
</thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
</div>

<div class="card">
<b>Outputs</b><br>
<ul>
  <li>JSON: report.json</li>
  <li>CSV: report.csv</li>
  <li>PDF: report.pdf</li>
</ul>
</div>

<script>
function filter(){{
  const q = document.getElementById('q').value.toLowerCase();
  const rows = document.querySelectorAll('#t tbody tr');
  for (const r of rows){{
    const txt = r.innerText.toLowerCase();
    r.style.display = txt.includes(q) ? '' : 'none';
  }}
}}
</script>
</body>
</html>"""
        out.write_text(html, encoding="utf-8")
        return out

    def export_pdf(self) -> Optional[Path]:
        if reportlab is None:
            self.logger.info("PDF export skipped (install reportlab to enable).")
            return None
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            from reportlab.pdfgen import canvas
        except Exception:
            self.logger.info("PDF export skipped (reportlab import failed).")
            return None

        out = self.out_dir / "report.pdf"
        c = canvas.Canvas(str(out), pagesize=letter)
        w, h = letter

        def draw_wrapped(x, y, text, width_chars=95, leading=12):
            lines = []
            for para in str(text).splitlines():
                lines.extend(textwrap.wrap(para, width=width_chars) or [""])
            for line in lines:
                nonlocal_y[0] -= leading
                if nonlocal_y[0] < 72:
                    c.showPage()
                    nonlocal_y[0] = h - 72
                    c.setFont("Helvetica", 10)
                c.drawString(x, nonlocal_y[0], line)

        c.setTitle("Bug Hunter Report")
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, h - 72, "Bug Hunter Report")
        c.setFont("Helvetica", 10)
        c.drawString(72, h - 90, f"Target: {self.scope.base_url}")
        c.drawString(72, h - 104, f"Generated: {self.scope.end_utc or now_utc()} (UTC)")
        c.drawString(72, h - 118, f"Host: {self.scope.hostname}  IPs: {', '.join(self.scope.resolved_ips)}")
        c.drawString(72, h - 132, f"Open Ports: {', '.join(map(str, self.open_ports))}")

        nonlocal_y = [h - 156]
        c.setFont("Helvetica-Bold", 12)
        c.drawString(72, nonlocal_y[0], "Summary")
        c.setFont("Helvetica", 10)
        nonlocal_y[0] -= 14
        summary = self._summary()
        draw_wrapped(72, nonlocal_y[0], f"HTTP requests: {summary['stats']['http_requests']}, errors: {summary['stats']['http_errors']}, 429s: {summary['stats']['rate_limited_429']}")
        draw_wrapped(72, nonlocal_y[0], f"Total findings: {summary['counts']['total_findings']}  By severity: {summary['counts']['by_severity']}")

        nonlocal_y[0] -= 8
        c.setFont("Helvetica-Bold", 12)
        c.drawString(72, nonlocal_y[0], "Findings (sorted by severity)")
        c.setFont("Helvetica", 9)
        nonlocal_y[0] -= 12

        for fnd in self.findings():
            draw_wrapped(72, nonlocal_y[0], f"[{fnd.severity}] {fnd.category} — {fnd.url}", width_chars=110, leading=11)
            if fnd.details:
                draw_wrapped(90, nonlocal_y[0], f"Details: {fnd.details}", width_chars=105, leading=11)
            if fnd.remediation:
                draw_wrapped(90, nonlocal_y[0], f"Fix: {fnd.remediation}", width_chars=105, leading=11)
            nonlocal_y[0] -= 6

        c.save()
        return out


# ---------------- CLI ----------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Bug Hunter (no-root) — authorized recon & misconfiguration scanner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("target", help="Target URL or hostname (https assumed if scheme omitted)")
    p.add_argument("-o", "--output", default="bughunter_out", help="Output directory")
    p.add_argument("--quick", action="store_true", help="Quick scan (lower depth, fewer probes)")
    p.add_argument("--full", action="store_true", help="Full scan (deeper crawl, more discovery)")
    p.add_argument("--timeout", type=float, default=12.0, help="HTTP/TCP timeout seconds")
    p.add_argument("-c", "--concurrency", type=int, default=30, help="Max concurrent tasks")
    p.add_argument("--rate", type=float, default=0.0, help="Optional rate limit (requests per second, 0=off)")
    p.add_argument("--user-agent", default="BugHunter/4 (authorized-testing)", help="User-Agent header")
    p.add_argument("--no-port-scan", action="store_true", help="Disable connect-based port scan")
    p.add_argument("--ports", default="", help="Comma-separated ports to scan (blank=default set)")
    p.add_argument("--crawl-depth", type=int, default=2, help="Crawl depth (0 disables crawling)")
    p.add_argument("--max-pages", type=int, default=200, help="Max pages to crawl")
    p.add_argument("--no-js", action="store_true", help="Disable JS analysis")
    p.add_argument("--no-dns", action="store_true", help="Disable DNS checks")
    p.add_argument("--no-tls", action="store_true", help="Disable TLS checks")
    p.add_argument("--no-sensitive", action="store_true", help="Disable sensitive file checks")
    p.add_argument("--no-cors", action="store_true", help="Disable CORS check")
    p.add_argument("--no-methods", action="store_true", help="Disable HTTP methods check")
    # Enabled by default; use --no-dirb to disable.
    dirb_group = p.add_mutually_exclusive_group()
    dirb_group.add_argument("--dirb", dest="dirb", action="store_true", help="Enable directory brute-force")
    dirb_group.add_argument("--no-dirb", dest="dirb", action="store_false", help="Disable directory brute-force")
    p.add_argument("--dirb-wordlist", default="", help="Optional custom wordlist file for dirb")
    # Enabled by default; use --no-wayback to disable.
    wb_group = p.add_mutually_exclusive_group()
    wb_group.add_argument("--wayback", dest="wayback", action="store_true", help="Enable passive Wayback URL discovery (external service)")
    wb_group.add_argument("--no-wayback", dest="wayback", action="store_false", help="Disable Wayback URL discovery")

    # Active probes are enabled by default; use --safe-mode to disable.
    active_group = p.add_mutually_exclusive_group()
    active_group.add_argument("--unsafe-active-tests", dest="unsafe_active_tests", action="store_true",
                              help="Enable active probes (dirb, risky method probing)")
    active_group.add_argument("--safe-mode", dest="unsafe_active_tests", action="store_false",
                              help="Disable active probes (safer/passive behavior)")
    p.add_argument("--debug", action="store_true", help="Verbose debug logging")
    p.set_defaults(dirb=True, wayback=True, unsafe_active_tests=True)
    return p.parse_args(argv)


def read_wordlist(path: str) -> List[str]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    out: List[str] = []
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            out.append(s)
    return out


async def main_async(args: argparse.Namespace) -> int:
    out_dir = Path(args.output)
    hunter = BugHunter(
        args.target,
        out_dir,
        concurrency=args.concurrency,
        timeout=args.timeout,
        user_agent=args.user_agent,
        rate_limit_rps=args.rate,
        debug=args.debug,
        unsafe_active_tests=args.unsafe_active_tests,
    )

    # Profiles
    crawl_depth = args.crawl_depth
    max_pages = args.max_pages
    ports = None

    if args.quick:
        crawl_depth = min(crawl_depth, 1)
        max_pages = min(max_pages, 80)
    if args.full:
        crawl_depth = max(crawl_depth, 3)
        max_pages = max(max_pages, 400)
        if args.concurrency < 50:
            hunter.concurrency = 50  # mild bump
            hunter.sem = asyncio.Semaphore(hunter.concurrency)

    if args.ports.strip():
        try:
            ports = [int(x.strip()) for x in args.ports.split(",") if x.strip()]
        except Exception:
            raise ValueError("Invalid --ports. Use comma-separated integers, e.g. 80,443,8080")

    dir_wordlist = DEFAULT_DIR_WORDLIST
    if args.dirb_wordlist:
        dir_wordlist = read_wordlist(args.dirb_wordlist)

    await hunter.scan(
        do_ports=not args.no_port_scan,
        ports=ports,
        do_dns=not args.no_dns,
        do_tls=not args.no_tls,
        do_headers=True,
        do_tech=True,
        do_cors=not args.no_cors,
        do_methods=not args.no_methods,
        do_sensitive=not args.no_sensitive,
        do_crawl=(crawl_depth > 0),
        crawl_depth=crawl_depth,
        max_pages=max_pages,
        do_js=not args.no_js,
        do_dirb=args.dirb,
        dir_wordlist=dir_wordlist,
        do_wayback=args.wayback,
    )

    # Exports
    j = hunter.export_json()
    c = hunter.export_csv()
    h = hunter.export_html()
    p = hunter.export_pdf()

    logger = hunter.logger
    logger.info(f"Wrote: {j}")
    logger.info(f"Wrote: {c}")
    logger.info(f"Wrote: {h}")
    if p:
        logger.info(f"Wrote: {p}")

    # Console summary
    fs = hunter.findings()
    sev_counts = Counter(f.severity for f in fs)
    top = ", ".join([f"{k}={sev_counts.get(k,0)}" for k in ["Critical","High","Medium","Low","Info"]])
    logger.info(f"Findings: {len(fs)} ({top})")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    # Friendly dependency hints (no auto-install)
    missing: List[str] = []
    if httpx is None:
        missing.append("httpx (required)")
    if missing:
        print("Missing dependencies:\n  - " + "\n  - ".join(missing), file=sys.stderr)
        print("\nInstall:\n  python3 -m pip install -U httpx\n", file=sys.stderr)
        return 2

    try:
        return asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
