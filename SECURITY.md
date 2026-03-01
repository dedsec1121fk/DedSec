# Security Policy

The DedSec Project is an **educational cybersecurity toolkit**. We take security reports seriously and we want to fix legitimate issues quickly and responsibly.

> **Important:** Do **not** use this project (or any report you submit) to perform unauthorized testing, data access, or attacks. Only test systems you own or have **explicit permission** to test.

---

## Supported Versions

Security fixes are provided on a **best‑effort** basis for:

- **The latest version on the `main` branch**
- The **most recent release** (if releases are published)

If you are using an older copy, please update first and verify whether the issue still exists.

---

## Reporting a Vulnerability (Responsible Disclosure)

### Preferred method (private)
1. **GitHub Security Advisories (recommended):**
   - Go to the repository **Security** tab → **Report a vulnerability** (if available).
2. If that option is not available, contact the maintainer via the official channels below and clearly state that your message is a **security report**.

### Official contact channels (fallback)
- Website: https://ded-sec.space/
- Telegram: https://t.me/dedsecproject
- Instagram: https://www.instagram.com/dedsec_project_official
- WhatsApp: https://wa.me/37257263676

### Please do NOT
- Open a public GitHub Issue for an active vulnerability.
- Publish proof‑of‑concept exploit code that enables real-world harm.
- Share stolen data or secrets (tokens, passwords, private keys). If you accidentally access sensitive data, stop immediately and report what happened.

---

## What to Include in Your Report

To help us reproduce and fix the issue faster, include:

- A clear description of the vulnerability and why it matters
- Affected component/tool/script name (and file path, if possible)
- Steps to reproduce (as minimal as possible)
- Expected vs actual behavior
- Your environment:
  - Device / Android version
  - Termux version (and whether Termux:API is installed)
  - Python version / Node version (if relevant)
- Any logs, stack traces, or screenshots
- If applicable, an estimate of impact (e.g., data exposure, auth bypass, RCE, SSRF, path traversal)

---

## Coordinated Disclosure

- Please allow us reasonable time to investigate and patch before public disclosure.
- We may ask follow-up questions or request a safer proof-of-concept.
- After a fix is available, we’ll try to credit you (unless you prefer to remain anonymous).

---

## Scope Notes

The project includes tools that interact with networks, web content, and user-generated inputs. **Valid security findings** generally include issues such as:

- Authentication / authorization bypass in included web UIs
- Sensitive data exposure (tokens, private keys, credentials, personal data)
- Remote code execution or command injection
- Path traversal / arbitrary file read-write
- Insecure default configurations (where the tool claims to be secure)
- Vulnerabilities caused by unsafe handling of tunnels, callbacks, or user-provided URLs

**Out of scope** (usually):
- Issues in third-party dependencies or external services *without* a demonstrable impact in this project
- Social engineering and physical attacks
- Denial-of-service reports that only involve unrealistic traffic volumes or non-default setups

---

## Third‑Party Components

This project uses third-party tools and libraries. If the issue is upstream, please still report it to us with details, and also consider reporting it to the upstream project.

---

Thank you for helping keep the DedSec Project safer.
