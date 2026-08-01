<a id="english-needs-readme"></a>

# DedSec Needs

> **Για να μεταβείτε στην πλήρη Ελληνική έκδοση, συνεχίστε [Πατώντας Εδώ](#greek-needs-readme).**

`Needs` contains the dependency manifests, vendored Python archives, Termux package-lock data, validation tools, first-run save support, logs, and GitHub maintenance automation used by DedSec Project.

## Stored dependencies

- `Modules/requirements.txt` is the audited Python dependency list.
- `Modules/Cache/` contains real portable Python wheels or source archives.
- `Packages/termux-required.txt` lists the required Termux package roots.
- `Packages/termux-optional.txt` lists optional feature packages.
- `Packages/package-lock-aarch64.json` records the resolved Termux dependency closure with exact versions, URLs, sizes, and SHA-256 checksums.
- `Packages/Cache/<architecture>/` is the repository-owned store for real Termux `.deb` files.
- Large `.deb` files can be stored as ordered `.part001`, `.part002`, and similar parts. `Setup.sh` reconstructs them temporarily before installation.
- A populated package cache includes `cache-manifest.json` with stored-file and reconstructed-package checksums.

## One setup script

Dependency installation and dependency-only updates are both handled by the root `Setup.sh`. The former `Needs/install.sh` and `Needs/update.sh` files are no longer needed.

Run the complete setup and open the DedSec menu:

```bash
bash Setup.sh
```

Update/check dependencies without opening the menu:

```bash
bash Setup.sh --update-only
```

Other supported options:

```text
--run
--no-run
--update-only
--required-only
--skip-system-update
--skip-repository-refresh
```

## Setup behavior

`Setup.sh` performs these operations in order:

1. Detects the device and package-manager environment.
2. Inspects the dependency files already stored under `Needs`.
3. Reconstructs split Termux packages when required.
4. Installs a local package only when it is missing or the cached version is newer.
5. Refreshes the configured repositories unless repository refresh was disabled.
6. Updates installed packages and downloads unresolved or missing packages.
7. Tries the local Python cache first, then updates modules and downloads unresolved requirements from PyPI.
8. Verifies manifests, caches, and installed imports.
9. On the first successful menu run, creates the one-time project-only save in Android Downloads.
10. Starts `Scripts/Settings.py`, unless `--no-run` or `--update-only` was selected.

Validate the manifests, local caches, and current installation manually:

```bash
python Needs/verify_needs.py --cache --installed
```

## Automatic maintenance

`.github/workflows/update-needs.yml` runs when relevant dependency files change, manually through **Run workflow**, and every Sunday.

The workflow builds and validates a complete replacement in a staging directory before touching the active cache. It retries downloads, uses fallback mirrors, verifies SHA-256 checksums, preserves a rollback copy during replacement, uploads the verified result as a workflow artifact, and only then commits the refreshed dependency files.

The repository must allow GitHub Actions **read and write** repository permissions so the workflow can commit cache updates.

## One-time first-run save

Before the first automatic menu launch, `Setup.sh` runs `Needs/first_run_save.py`. After a successful save it creates:

```text
~/storage/downloads/DedSec Project.zip
```

The archive contains only the current DedSec Project checkout. It is written only to Android internal-storage Downloads. The new archive is fully created and validated before replacing an older file. A completion marker is written under `Needs/State/` only after success, so later setup runs do not create another automatic save.

When Downloads access is missing, `Setup.sh` shows the `termux-setup-storage` permission message instead of hiding it. If permission is refused or unavailable, no completion marker is written and the next normal setup run retries the save.

---

<a id="greek-needs-readme"></a>

# Απαιτήσεις DedSec

> **To return to the full English version, continue by [Clicking Here](#english-needs-readme).**

Ο φάκελος `Needs` περιέχει τα dependency manifests, τα αποθηκευμένα Python archives, τα Termux package-lock δεδομένα, τα εργαλεία επαλήθευσης, την υποστήριξη του first-run save, τα logs και το GitHub maintenance automation που χρησιμοποιεί το DedSec Project.

## Αποθηκευμένα dependencies

- Το `Modules/requirements.txt` είναι η ελεγμένη λίστα Python dependencies.
- Το `Modules/Cache/` περιέχει πραγματικά portable Python wheels ή source archives.
- Το `Packages/termux-required.txt` περιέχει τα απαραίτητα βασικά Termux packages.
- Το `Packages/termux-optional.txt` περιέχει προαιρετικά packages για επιπλέον λειτουργίες.
- Το `Packages/package-lock-aarch64.json` καταγράφει ολόκληρο το resolved Termux dependency closure με ακριβείς εκδόσεις, URLs, μεγέθη και SHA-256 checksums.
- Το `Packages/Cache/<architecture>/` είναι ο αποθηκευτικός χώρος του repository για τα πραγματικά Termux `.deb` αρχεία.
- Μεγάλα `.deb` αρχεία μπορούν να αποθηκεύονται ως διαδοχικά `.part001`, `.part002` και παρόμοια μέρη. Το `Setup.sh` τα επανασυνθέτει προσωρινά πριν από την εγκατάσταση.
- Ένα συμπληρωμένο package cache περιλαμβάνει `cache-manifest.json` με checksums για τα αποθηκευμένα αρχεία και τα επανασυντεθειμένα packages.

## Ένα ενιαίο setup script

Η εγκατάσταση dependencies και η ενημέρωση μόνο των dependencies γίνονται πλέον από το κεντρικό `Setup.sh` στη ρίζα του project. Τα παλιά `Needs/install.sh` και `Needs/update.sh` δεν χρειάζονται πλέον.

Για πλήρες setup και αυτόματο άνοιγμα του DedSec menu:

```bash
bash Setup.sh
```

Για έλεγχο/ενημέρωση dependencies χωρίς να ανοίξει το menu:

```bash
bash Setup.sh --update-only
```

Άλλες διαθέσιμες επιλογές:

```text
--run
--no-run
--update-only
--required-only
--skip-system-update
--skip-repository-refresh
```

## Συμπεριφορά του Setup

Το `Setup.sh` εκτελεί με τη σειρά τα παρακάτω:

1. Εντοπίζει τη συσκευή και το διαθέσιμο package-manager environment.
2. Ελέγχει τα dependency αρχεία που υπάρχουν ήδη μέσα στο `Needs`.
3. Επανασυνθέτει split Termux packages όταν χρειάζεται.
4. Εγκαθιστά ένα τοπικό package μόνο όταν λείπει ή όταν η cached έκδοση είναι νεότερη.
5. Ανανεώνει τα configured repositories, εκτός αν έχει απενεργοποιηθεί το repository refresh.
6. Ενημερώνει τα εγκατεστημένα packages και κατεβάζει όσα λείπουν ή δεν έχουν επιλυθεί.
7. Δοκιμάζει πρώτα το τοπικό Python cache και μετά ενημερώνει modules και κατεβάζει unresolved requirements από το PyPI.
8. Επαληθεύει manifests, caches και εγκατεστημένα imports.
9. Στην πρώτη επιτυχημένη εκκίνηση του menu δημιουργεί το one-time project-only save στα Android Downloads.
10. Ανοίγει το `Scripts/Settings.py`, εκτός αν χρησιμοποιήθηκε `--no-run` ή `--update-only`.

Για χειροκίνητη επαλήθευση manifests, local caches και τρέχουσας εγκατάστασης:

```bash
python Needs/verify_needs.py --cache --installed
```

## Αυτόματη συντήρηση

Το `.github/workflows/update-needs.yml` εκτελείται όταν αλλάζουν σχετικά dependency αρχεία, χειροκίνητα από το **Run workflow** και κάθε Κυριακή.

Το workflow δημιουργεί και επαληθεύει ένα πλήρες replacement μέσα σε staging directory πριν αγγίξει το ενεργό cache. Επαναλαμβάνει αποτυχημένες λήψεις, χρησιμοποιεί fallback mirrors, επαληθεύει SHA-256 checksums, διατηρεί rollback copy κατά την αντικατάσταση, ανεβάζει το verified αποτέλεσμα ως workflow artifact και μόνο μετά κάνει commit τα ανανεωμένα dependency αρχεία.

Το repository πρέπει να επιτρέπει στο GitHub Actions **read and write** repository permissions, ώστε το workflow να μπορεί να κάνει commit τις ενημερώσεις του cache.

## One-time αποθήκευση στην πρώτη εκτέλεση

Πριν από το πρώτο αυτόματο άνοιγμα του menu, το `Setup.sh` εκτελεί το `Needs/first_run_save.py`. Μετά από επιτυχημένη αποθήκευση δημιουργείται:

```text
~/storage/downloads/DedSec Project.zip
```

Το archive περιέχει μόνο το τρέχον checkout του DedSec Project και γράφεται αποκλειστικά στα Downloads του Android internal storage. Το νέο archive δημιουργείται και επαληθεύεται πλήρως πριν αντικαταστήσει παλιότερο αρχείο. Completion marker γράφεται μέσα στο `Needs/State/` μόνο μετά από επιτυχία, ώστε επόμενα setup runs να μη δημιουργούν άλλο αυτόματο save.

Όταν λείπει η πρόσβαση στα Downloads, το `Setup.sh` εμφανίζει κανονικά το permission μήνυμα του `termux-setup-storage` αντί να το κρύβει. Αν η άδεια απορριφθεί ή δεν είναι διαθέσιμη, δεν γράφεται completion marker και η επόμενη κανονική εκτέλεση του setup δοκιμάζει ξανά.
