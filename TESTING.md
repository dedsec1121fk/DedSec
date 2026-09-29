# DedSec Project Testing Guide

---

<a id="english-testing"></a>

# English

> **Για να μεταβείτε στην Ελληνική έκδοση, συνεχίστε [Πατώντας Εδώ](#greek-testing).**

DedSec Project uses a public automated test suite under `tests/` and runs it through GitHub Actions.

<details>
<summary><strong>Standard Test Command</strong></summary>

From the repository root:

```bash
python -m pytest
```

</details>

<details>
<summary><strong>Development Dependencies</strong></summary>

Install with:

```bash
python -m pip install -r requirements-dev.txt
```

Development requirements are separate from the runtime dependencies used by DedSec.

On Termux, `pytest` can be installed and the suite can run locally. If Ruff or ShellCheck is inconvenient to install locally on Android, GitHub Actions is the authoritative lint run.

</details>

<details>
<summary><strong>What The Baseline Tests Cover</strong></summary>

The initial suite includes:

- Python syntax compilation for repository `.py` files,
- Bash syntax validation,
- required repository structure and documentation,
- safe `Setup.sh --help` checks,
- invalid setup option handling,
- safe `Setup-Termux.sh --help` checks,
- cross-platform contract checks for Termux, Ubuntu, Kali Linux, and Linux Mint.

The tests do **not** import or execute operational Python tools simply to check syntax.

</details>

<details>
<summary><strong>Recent Major-Change Evidence</strong></summary>

The v1.0.2 release introduced major cross-platform setup and launch behavior.

`tests/test_cross_platform_contract.py` provides regression coverage for:

- supported platforms,
- desktop `.venv` behavior,
- Termux setup routing,
- setup CLI error handling,
- platform variables,
- `Run.sh` launch contract,
- cross-platform documentation.

</details>

<details>
<summary><strong>Linting</strong></summary>

Python:

```bash
ruff check .
```

Shell source is checked with:

- `bash -n`,
- ShellCheck in GitHub Actions.

</details>

<details>
<summary><strong>Adding Tests</strong></summary>

Major new functionality and significant behavior changes must add or update automated tests.

Good tests should:

- avoid real external systems,
- use temporary directories,
- mock side effects,
- use local fixtures,
- verify pure transformations and validation,
- prefer non-operative CLI modes.

For hardware- or Android-specific behavior that cannot safely run in CI, test the platform-independent portion automatically and document manual verification in the pull request.

</details>

<details>
<summary><strong>Expected Result</strong></summary>

```text
pytest: PASS
ruff: PASS
shell syntax: PASS
ShellCheck: PASS
CodeQL: no unresolved confirmed medium-or-higher exploitable finding introduced by the change
```

Failures must be fixed or clearly demonstrated to be false positives before merge.

</details>

---

<a id="greek-testing"></a>

# Ελληνικά

> **To return to the English version, continue [By Clicking Here](#english-testing).**

Το DedSec Project χρησιμοποιεί δημόσιο automated test suite στον φάκελο `tests/` και το εκτελεί μέσω GitHub Actions.

<details>
<summary><strong>Βασική Εντολή Tests</strong></summary>

Από τη ρίζα του repository:

```bash
python -m pytest
```

</details>

<details>
<summary><strong>Development Dependencies</strong></summary>

Εγκατάσταση:

```bash
python -m pip install -r requirements-dev.txt
```

Τα development requirements είναι ξεχωριστά από τα runtime dependencies του DedSec.

Στο Termux μπορεί να εγκατασταθεί το `pytest` και να τρέξει το suite τοπικά. Αν Ruff ή ShellCheck δεν είναι πρακτικό να εγκατασταθούν στο Android, το GitHub Actions θεωρείται το authoritative lint run.

</details>

<details>
<summary><strong>Τι Καλύπτουν Τα Βασικά Tests</strong></summary>

Το αρχικό suite περιλαμβάνει:

- Python syntax compilation για `.py` files,
- Bash syntax validation,
- έλεγχο repository structure και documentation,
- ασφαλή `Setup.sh --help` checks,
- invalid setup option handling,
- ασφαλή `Setup-Termux.sh --help` checks,
- cross-platform contract checks για Termux, Ubuntu, Kali Linux και Linux Mint.

Τα tests **δεν κάνουν import ή execute τα operational Python tools** μόνο για syntax checking.

</details>

<details>
<summary><strong>Απόδειξη Πρόσφατης Σημαντικής Αλλαγής</strong></summary>

Το release v1.0.2 εισήγαγε σημαντικό cross-platform setup και launch behavior.

Το `tests/test_cross_platform_contract.py` καλύπτει:

- supported platforms,
- desktop `.venv` behavior,
- Termux setup routing,
- setup CLI error handling,
- platform variables,
- το launch contract του `Run.sh`,
- cross-platform documentation.

</details>

<details>
<summary><strong>Linting</strong></summary>

Python:

```bash
ruff check .
```

Το shell source ελέγχεται με:

- `bash -n`,
- ShellCheck μέσω GitHub Actions.

</details>

<details>
<summary><strong>Προσθήκη Tests</strong></summary>

Κάθε σημαντική νέα λειτουργία και ουσιαστική αλλαγή behavior πρέπει να προσθέτει ή να ενημερώνει automated tests.

Τα tests πρέπει κατά προτίμηση να:

- αποφεύγουν πραγματικά external systems,
- χρησιμοποιούν temporary directories,
- κάνουν mock side effects,
- χρησιμοποιούν local fixtures,
- ελέγχουν pure transformations και validation,
- προτιμούν non-operative CLI modes.

Για hardware- ή Android-specific behavior που δεν μπορεί να τρέξει με ασφάλεια σε CI, πρέπει να καλύπτεται αυτόματα το platform-independent μέρος και να τεκμηριώνεται manual verification στο pull request.

</details>

<details>
<summary><strong>Αναμενόμενο Αποτέλεσμα</strong></summary>

```text
pytest: PASS
ruff: PASS
shell syntax: PASS
ShellCheck: PASS
CodeQL: χωρίς unresolved confirmed medium-or-higher exploitable finding που εισήχθη από την αλλαγή
```

Failures πρέπει να διορθώνονται ή να τεκμηριώνονται καθαρά ως false positives πριν από merge.

</details>
