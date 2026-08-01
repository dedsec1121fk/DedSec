<a id="english-modules-readme"></a>

# Vendored Python Modules

> **Για να μεταβείτε στην πλήρη Ελληνική έκδοση, συνεχίστε [Πατώντας Εδώ](#greek-modules-readme).**

`Needs/Modules` stores the audited Python dependency manifest and the repository-owned module cache used by DedSec Project.

## Files

- `requirements.txt` lists the Python distributions required by the audited project scripts.
- `Cache/` stores installable wheels and source archives.
- `import-map.json` maps imported module names to their installable distribution names.
- `source-import-audit.json` records the source files and imports found during the audit.
- `declared-legacy.txt` records older dependency declarations retained for compatibility and review.

## Installation behavior

`Setup.sh` checks `Cache/` before consulting PyPI. It attempts to restore or upgrade each requirement from local artifacts first, then uses the configured package index only for newer or unresolved items.

The local pass uses `--no-index` and does not silently substitute unrelated packages. The online pass retries requirements individually when a bulk operation fails, so one unavailable dependency does not prevent all remaining modules from being checked.

Run dependency maintenance without opening the DedSec menu:

```bash
bash Setup.sh --update-only
```

## Weekly maintenance

The Sunday workflow prefers portable source distributions. When a project does not publish a source archive, the maintenance program uses only a verified compatible fallback, such as a universal wheel or an immutable official source tag. Downloaded artifacts are checksum-verified before the staged cache can replace the active cache.

---

<a id="greek-modules-readme"></a>

# Αποθηκευμένα Python Modules

> **To return to the full English version, continue by [Clicking Here](#english-modules-readme).**

Το `Needs/Modules` αποθηκεύει το ελεγμένο Python dependency manifest και το module cache του repository που χρησιμοποιεί το DedSec Project.

## Αρχεία

- Το `requirements.txt` περιέχει τις Python distributions που απαιτούν τα ελεγμένα scripts του project.
- Το `Cache/` αποθηκεύει installable wheels και source archives.
- Το `import-map.json` αντιστοιχίζει τα imported module names με τα distribution names που εγκαθίστανται.
- Το `source-import-audit.json` καταγράφει τα source files και imports που βρέθηκαν κατά τον έλεγχο.
- Το `declared-legacy.txt` καταγράφει παλιότερα dependency declarations που διατηρούνται για compatibility και review.

## Συμπεριφορά εγκατάστασης

Το `Setup.sh` ελέγχει το `Cache/` πριν επικοινωνήσει με το PyPI. Προσπαθεί πρώτα να επαναφέρει ή να αναβαθμίσει κάθε requirement από τα τοπικά artifacts και χρησιμοποιεί το configured package index μόνο για νεότερα ή unresolved items.

Το local pass χρησιμοποιεί `--no-index` και δεν αντικαθιστά σιωπηλά dependencies με άσχετα packages. Αν αποτύχει ένα bulk operation, το online pass δοκιμάζει τα requirements ξεχωριστά, ώστε ένα unavailable dependency να μην εμποδίσει τον έλεγχο όλων των υπόλοιπων modules.

Για dependency maintenance χωρίς να ανοίξει το DedSec menu:

```bash
bash Setup.sh --update-only
```

## Εβδομαδιαία συντήρηση

Το Sunday workflow προτιμά portable source distributions. Όταν ένα project δεν δημοσιεύει source archive, το maintenance program χρησιμοποιεί μόνο επαληθευμένο compatible fallback, όπως universal wheel ή immutable official source tag. Τα downloaded artifacts επαληθεύονται με checksum πριν το staged cache μπορέσει να αντικαταστήσει το ενεργό cache.
