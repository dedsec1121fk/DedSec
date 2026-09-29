# Security Policy — DedSec Project

---

<a id="english-security"></a>

# English

> **Για να μεταβείτε στην Ελληνική έκδοση, συνεχίστε [Πατώντας Εδώ](#greek-security).**

DedSec Project is an educational cybersecurity toolkit intended for authorized, consent-based learning, testing, and defensive use.

> **No unauthorized use:** Do not test, access, disrupt, or attack systems you do not own or have explicit permission to test.

<details>
<summary><strong>Supported Versions</strong></summary>

Security fixes are provided on a best-effort basis for:

- the latest version on `main`,
- the most recent tagged release.

Update older installations before reporting an issue.

</details>

<details>
<summary><strong>Reporting A Vulnerability</strong></summary>

Preferred method:

1. Open the repository on GitHub.
2. Go to **Security** → **Report a vulnerability** when available.
3. Submit the report privately.

Do not publish an undisclosed vulnerability in a public GitHub issue.

If private reporting is unavailable, use an official project channel and clearly label the message **SECURITY REPORT**.

</details>

<details>
<summary><strong>Initial Response Target</strong></summary>

A valid security report will receive an initial response within **14 calendar days**.

This is an initial-response target, not a promise that every vulnerability will be fully fixed within 14 days.

</details>

<details>
<summary><strong>What To Include</strong></summary>

Include:

- a clear vulnerability description,
- affected component or file,
- safe reproduction steps,
- expected vs actual behavior,
- environment details,
- redacted logs/screenshots,
- impact estimate.

</details>

<details>
<summary><strong>Security Expectations For Contributors</strong></summary>

Contributors must:

- never commit real secrets,
- validate untrusted input,
- avoid unsafe command execution,
- use safe file operations,
- prefer safer networking defaults,
- review dependencies and remote sources,
- add/update tests for important behavior changes,
- address configured linter/static-analysis findings.

</details>

<details>
<summary><strong>Static Analysis</strong></summary>

GitHub CodeQL is used as a static-analysis layer.

Confirmed exploitable medium-or-higher findings should be fixed before affected new code is released, or as promptly as practical for already released code.

</details>

<details>
<summary><strong>Cryptography</strong></summary>

Security-sensitive code should use established cryptographic libraries and modern password/key derivation mechanisms.

Where applicable:

- use salted password derivation such as PBKDF2-HMAC-SHA256,
- use cryptographically secure randomness,
- do not use MD5 or SHA-1 as password hashes, signatures, or security-sensitive integrity mechanisms.

Legacy hashes may appear only in non-security contexts such as fingerprints, duplicate-file identification, or deterministic non-secret identifiers.

</details>

<details>
<summary><strong>Maintainer Checklist</strong></summary>

1. Reproduce safely.
2. Classify severity and affected versions.
3. Use a private fix branch when disclosure could expose the vulnerability.
4. Add a regression test when practical.
5. Run tests, linting, and static analysis.
6. Release the fix with appropriate notes/advisory.
7. Credit the reporter if desired.

</details>

---

<a id="greek-security"></a>

# Ελληνικά

> **To return to the English version, continue [By Clicking Here](#english-security).**

Το DedSec Project είναι ένα εκπαιδευτικό cybersecurity toolkit για εξουσιοδοτημένη, συναινετική εκμάθηση, δοκιμή και αμυντική χρήση.

> **Απαγορεύεται η μη εξουσιοδοτημένη χρήση:** Μην δοκιμάζεις, προσπελαύνεις, διακόπτεις ή επιτίθεσαι σε συστήματα που δεν σου ανήκουν ή για τα οποία δεν έχεις ρητή άδεια.

<details>
<summary><strong>Υποστηριζόμενες Εκδόσεις</strong></summary>

Security fixes παρέχονται best-effort για:

- την τελευταία έκδοση του `main`,
- το πιο πρόσφατο tagged release.

Κάνε update παλαιότερη εγκατάσταση πριν αναφέρεις issue.

</details>

<details>
<summary><strong>Αναφορά Vulnerability</strong></summary>

Προτιμώμενος τρόπος:

1. Άνοιξε το repository στο GitHub.
2. Πήγαινε **Security** → **Report a vulnerability** όταν είναι διαθέσιμο.
3. Στείλε την αναφορά ιδιωτικά.

Μην δημοσιεύεις undisclosed vulnerability σε public GitHub issue.

Αν private reporting δεν είναι διαθέσιμο, χρησιμοποίησε επίσημο project channel και γράψε καθαρά **SECURITY REPORT**.

</details>

<details>
<summary><strong>Initial Response Target</strong></summary>

Έγκυρη security αναφορά θα λάβει αρχική απάντηση μέσα σε **14 ημερολογιακές ημέρες**.

Αυτό αφορά initial response και όχι εγγύηση πλήρους fix μέσα σε 14 ημέρες.

</details>

<details>
<summary><strong>Τι Πρέπει Να Περιλαμβάνει Η Αναφορά</strong></summary>

Πρόσθεσε:

- καθαρή περιγραφή vulnerability,
- affected component ή file,
- safe reproduction steps,
- expected vs actual behavior,
- environment details,
- redacted logs/screenshots,
- impact estimate.

</details>

<details>
<summary><strong>Security Expectations Για Contributors</strong></summary>

Οι contributors πρέπει να:

- μην κάνουν commit πραγματικά secrets,
- κάνουν validation σε untrusted input,
- αποφεύγουν unsafe command execution,
- χρησιμοποιούν safe file operations,
- προτιμούν safer networking defaults,
- ελέγχουν dependencies και remote sources,
- προσθέτουν/ενημερώνουν tests για σημαντικές behavior changes,
- διορθώνουν configured linter/static-analysis findings.

</details>

<details>
<summary><strong>Static Analysis</strong></summary>

Το GitHub CodeQL χρησιμοποιείται ως static-analysis layer.

Confirmed exploitable findings severity medium ή υψηλότερο πρέπει να διορθώνονται πριν από release νέου affected code ή όσο το δυνατόν γρηγορότερα για ήδη released code.

</details>

<details>
<summary><strong>Cryptography</strong></summary>

Security-sensitive code πρέπει να χρησιμοποιεί καθιερωμένες cryptographic libraries και σύγχρονους μηχανισμούς password/key derivation.

Όπου εφαρμόζεται:

- χρησιμοποίησε salted password derivation όπως PBKDF2-HMAC-SHA256,
- χρησιμοποίησε cryptographically secure randomness,
- μην χρησιμοποιείς MD5 ή SHA-1 ως password hashes, signatures ή security-sensitive integrity mechanisms.

Legacy hashes μπορούν να εμφανίζονται μόνο σε non-security contexts όπως fingerprints, duplicate-file identification ή deterministic non-secret identifiers.

</details>

<details>
<summary><strong>Maintainer Checklist</strong></summary>

1. Ασφαλής αναπαραγωγή.
2. Κατηγοριοποίηση severity και affected versions.
3. Private fix branch όταν η disclosure μπορεί να αποκαλύψει vulnerability.
4. Regression test όπου είναι πρακτικό.
5. Tests, linting και static analysis.
6. Release fix με κατάλληλα notes/advisory.
7. Credit στον reporter αν το επιθυμεί.

</details>
