# Security Policy — DedSec Project

DedSec Project is an educational cybersecurity toolkit (often used on Android via Termux) that bundles scripts and utilities under a menu-driven interface. The intention is to support **authorized, consent-based** learning, testing, and defensive checks.

> **No unauthorized use:** Do not use DedSec Project to test, access, disrupt, or attack systems you do not own or have **explicit written permission** to test.

---

## Supported versions

Security fixes are provided on a best‑effort basis for:

- The latest version on the `main` branch
- The most recent tagged release (if/when releases are published)

If you are on an older copy, please update first and verify the issue still exists.

---

## Reporting a vulnerability (Responsible / Coordinated Disclosure)

### Preferred: private report via GitHub

If the repository has GitHub Security Advisories enabled:

1. Open the repository on GitHub
2. Go to **Security** → **Report a vulnerability**
3. Submit your report with the details listed below

(If the button is not available, use the fallback contact method.)

### Fallback: official project channels

If private reporting on GitHub is not available, contact the maintainer via an official project channel and clearly mark your message as a **SECURITY REPORT**.

---

## Please do NOT

- Open a public GitHub Issue for an active vulnerability
- Post exploit code or step-by-step instructions that enable real‑world harm
- Share stolen data, secrets, tokens, credentials, or private keys  
  (If you accidentally access sensitive data: **stop immediately** and report what happened.)

---

## What to include in a report

To help reproduce and fix the issue quickly, include:

- A clear description of the vulnerability and why it matters
- The affected component/tool/script name and file path (if known)
- Minimal reproduction steps (safe, non-destructive)
- Expected vs actual behavior
- Environment details:
  - Android version + device model
  - Termux version (and whether Termux:API is installed)
  - Python / Node / Bash versions (as relevant)
- Logs, stack traces, screenshots (redact secrets!)
- Impact estimate (examples: data exposure, auth bypass, command injection, path traversal)

---

## Coordinated disclosure timeline (best effort)

- We will acknowledge a report as soon as practical
- We may ask clarifying questions or request a safer proof-of-concept
- We will work on a fix and coordinate a reasonable disclosure window with the reporter
- We will credit you in release notes/advisory (unless you prefer anonymity)

---

## Scope: what we consider a “security issue” here

Valid security findings generally include:

- Command injection / code execution via user-controlled input
- Path traversal / arbitrary file read-write
- Credential or secret leakage (tokens, API keys, session cookies, private keys)
- Unsafe update/install behaviors (e.g., executing untrusted remote code without integrity checks)
- Vulnerable web UIs bundled with the project (auth bypass, IDOR, SSRF, XSS where relevant)
- Dangerous default configurations **when the tool claims to be safe/defensive**

Usually out of scope:

- Issues in third‑party dependencies **without a demonstrable impact** on this project
- Social engineering and physical attacks
- Denial‑of‑service reports that require unrealistic traffic volumes or non-default setups

---

## Security expectations for contributors

### 1) Never commit secrets

- Do not commit API keys, tokens, passwords, cookies, session IDs, private keys, or credential dumps
- Use environment variables or user prompts for secrets
- If you suspect a secret was committed: rotate it immediately and report the incident privately

### 2) Treat all input as hostile

Across Python / Bash / JS:

- Validate and sanitize any user input
- Avoid `eval`, unsafe shell interpolation, or concatenating commands
- Prefer safe subprocess invocation with argument lists (Python) and strict quoting (Bash)
- Do not auto-execute downloaded content unless integrity-checked and user-consented

### 3) Safe file operations

- Use a dedicated output directory per tool
- Prevent directory traversal when handling filenames/paths
- Don’t delete user data outside the project folder unless the user explicitly confirmed

### 4) Safer networking defaults

- Default to **read-only / passive** modes when possible
- Require explicit confirmation for actions that could:
  - send traffic to third parties,
  - generate phishing simulations,
  - scan networks,
  - perform brute-force-like checks

### 5) Dependency and supply-chain hygiene

- Pin dependencies where feasible
- Prefer official package managers (pkg/pip/npm) over untrusted one-liners
- If you download remote assets:
  - use HTTPS,
  - verify checksums/signatures when available,
  - log sources clearly

---

## Handling reports: maintainer checklist

1. Reproduce safely, minimize user impact
2. Classify severity and affected versions
3. Create a private fix branch (avoid leaking details)
4. Add regression tests (when practical)
5. Release fix + notes (and advisory if appropriate)
6. Credit reporter (if desired) and communicate clearly

---

## Thank you

Thanks for helping keep DedSec Project safer for everyone.
