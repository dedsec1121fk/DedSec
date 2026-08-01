<a id="english-packages-readme"></a>

# Vendored Termux Packages

> **Για να μεταβείτε στην πλήρη Ελληνική έκδοση, συνεχίστε [Πατώντας Εδώ](#greek-packages-readme).**

`Needs/Packages/Cache/<architecture>/` is the repository-owned offline package store. It is designed to contain the real Termux `.deb` files for the complete recursive dependency closure, not only package names.

## Package resolution files

- `termux-required.txt` contains the required root packages.
- `termux-optional.txt` contains optional feature roots.
- `debian-required.txt` contains Debian/Ubuntu equivalents used outside Termux.
- `package-lock-aarch64.json` records exact resolved versions, source paths, sizes, SHA-256 checksums, dependencies, and mirror URLs.
- `download-plan-aarch64.tsv` provides the same resolution in a simpler machine-readable table.
- `Indexes/aarch64/` stores compressed package-index snapshots used by the current resolution audit.
- `Cache/cache-manifest.json` describes files that are actually present in the cache.

The current AArch64 lock covers the resolved required closure and all currently available optional closures. `avahi` remains optional because `Devices Finder.py` can use `avahi-resolve-address`, but that package may not exist in the active Termux repositories. `Setup.sh` treats an unavailable optional package as a warning rather than a fatal error.

## Local-first setup behavior

`bash Setup.sh` performs the local package pass before refreshing a repository. It:

1. Detects the current architecture.
2. Finds complete `.deb` files and ordered split parts.
3. Reconstructs split packages in a temporary directory.
4. Reads package names and versions with `dpkg-deb`.
5. Installs only missing packages or cached versions newer than the installed versions.
6. Refreshes repositories and asks them for newer or still-missing items.
7. Continues to the Python dependency pass and then opens the DedSec menu.

For dependency-only maintenance:

```bash
bash Setup.sh --update-only
```

A split package can be reconstructed manually with:

```bash
bash Needs/Packages/reconstruct-package.sh Needs/Packages/Cache/aarch64/package.deb.part001
```

## Safe weekly refresh

`.github/workflows/update-needs.yml` runs every Sunday and can also be started manually. The maintenance program:

1. Resolves current repository indexes.
2. Downloads the full new closure into a separate staging directory.
3. Retries downloads and rotates through configured mirrors.
4. Verifies every package against its repository SHA-256 value.
5. Splits files larger than the GitHub-safe threshold into ordered parts.
6. Validates the complete staged set.
7. Keeps a rollback copy while replacing the old cache.
8. Uploads the verified result as a workflow artifact before committing it.

The old cache is never deleted before the complete replacement has downloaded and passed validation.

---

<a id="greek-packages-readme"></a>

# Αποθηκευμένα Termux Packages

> **To return to the full English version, continue by [Clicking Here](#english-packages-readme).**

Το `Needs/Packages/Cache/<architecture>/` είναι ο offline package αποθηκευτικός χώρος του repository. Είναι σχεδιασμένο να περιέχει τα πραγματικά Termux `.deb` αρχεία για ολόκληρο το recursive dependency closure και όχι μόνο ονόματα packages.

## Αρχεία package resolution

- Το `termux-required.txt` περιέχει τα απαραίτητα root packages.
- Το `termux-optional.txt` περιέχει προαιρετικά feature roots.
- Το `debian-required.txt` περιέχει Debian/Ubuntu equivalents για χρήση εκτός Termux.
- Το `package-lock-aarch64.json` καταγράφει ακριβείς resolved versions, source paths, μεγέθη, SHA-256 checksums, dependencies και mirror URLs.
- Το `download-plan-aarch64.tsv` παρέχει το ίδιο resolution σε απλούστερο machine-readable table.
- Το `Indexes/aarch64/` αποθηκεύει compressed package-index snapshots που χρησιμοποιούνται από το τρέχον resolution audit.
- Το `Cache/cache-manifest.json` περιγράφει τα αρχεία που υπάρχουν πραγματικά μέσα στο cache.

Το τρέχον AArch64 lock καλύπτει το resolved required closure και όλα τα optional closures που είναι τώρα διαθέσιμα. Το `avahi` παραμένει optional επειδή το `Devices Finder.py` μπορεί να χρησιμοποιήσει το `avahi-resolve-address`, αλλά το package μπορεί να μην υπάρχει στα ενεργά Termux repositories. Το `Setup.sh` αντιμετωπίζει ένα unavailable optional package ως warning και όχι ως fatal error.

## Local-first συμπεριφορά setup

Το `bash Setup.sh` εκτελεί το local package pass πριν ανανεώσει repository. Συγκεκριμένα:

1. Εντοπίζει το architecture της συσκευής.
2. Βρίσκει πλήρη `.deb` αρχεία και ordered split parts.
3. Επανασυνθέτει split packages μέσα σε temporary directory.
4. Διαβάζει package names και versions με `dpkg-deb`.
5. Εγκαθιστά μόνο packages που λείπουν ή cached versions που είναι νεότερες από τις εγκατεστημένες.
6. Ανανεώνει τα repositories και ζητά νεότερα ή ακόμη missing items.
7. Συνεχίζει στο Python dependency pass και μετά ανοίγει το DedSec menu.

Για maintenance μόνο των dependencies:

```bash
bash Setup.sh --update-only
```

Ένα split package μπορεί να επανασυντεθεί χειροκίνητα με:

```bash
bash Needs/Packages/reconstruct-package.sh Needs/Packages/Cache/aarch64/package.deb.part001
```

## Ασφαλές εβδομαδιαίο refresh

Το `.github/workflows/update-needs.yml` εκτελείται κάθε Κυριακή και μπορεί επίσης να ξεκινήσει χειροκίνητα. Το maintenance program:

1. Κάνει resolve τα τρέχοντα repository indexes.
2. Κατεβάζει ολόκληρο το νέο closure σε ξεχωριστό staging directory.
3. Επαναλαμβάνει downloads και εναλλάσσεται ανάμεσα στα configured mirrors.
4. Επαληθεύει κάθε package με το repository SHA-256 value.
5. Χωρίζει αρχεία μεγαλύτερα από το GitHub-safe threshold σε ordered parts.
6. Επαληθεύει ολόκληρο το staged set.
7. Διατηρεί rollback copy κατά την αντικατάσταση του παλιού cache.
8. Ανεβάζει το verified αποτέλεσμα ως workflow artifact πριν το κάνει commit.

Το παλιό cache δεν διαγράφεται ποτέ πριν κατέβει και επαληθευτεί πλήρως το νέο replacement.
