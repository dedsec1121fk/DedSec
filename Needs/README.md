# DedSec Needs

`Needs` contains dependency manifests, real vendored module archives, Termux package-lock data, validation tools, and maintenance automation for DedSec Project.

## Stored dependencies

- `Modules/requirements.txt` is the audited Python dependency list.
- `Modules/Cache/` contains real portable Python wheels or source archives.
- `Packages/termux-required.txt` lists required Termux package roots.
- `Packages/termux-optional.txt` lists optional package roots.
- `Packages/package-lock-aarch64.json` records the exact recursive Termux closure with versions, URLs, sizes, and SHA-256 checksums.
- `Packages/Cache/<architecture>/` is populated with the real Termux `.deb` files by the maintenance workflow.
- A large `.deb` is stored as ordered `.part001`, `.part002`, and similar files. Setup reconstructs it temporarily before installation.
- Each populated cache includes `cache-manifest.json` with stored-file and reconstructed-package checksums.

## Setup behavior

Run:

```bash
bash Setup.sh
```

Setup performs these operations in order:

1. Detects the device architecture and inspects the dependency files already stored in `Needs`.
2. Reconstructs split Termux packages when necessary.
3. Installs a local package only when it is missing or the cached version is newer than the installed version.
4. Refreshes the configured Termux repositories after the local pass.
5. Updates installed dependencies when a newer repository version exists and downloads anything still missing.
6. Tries the local Python cache first, then updates modules and downloads unresolved dependencies from PyPI.
7. Verifies the environment and starts `Scripts/Settings.py`.

Update dependencies without opening the menu:

```bash
bash Needs/update.sh
```

Validate manifests, local caches, and the current installation:

```bash
python Needs/verify_needs.py --cache --installed
```

## Automatic maintenance

`.github/workflows/update-needs.yml` runs immediately after relevant dependency files change, manually through **Run workflow**, and every Sunday.

The workflow creates and verifies the full replacement before touching the current cache. It uses multiple mirrors, retries transient failures, preserves a rollback copy during the swap, uploads the complete verified result as a workflow artifact, and only then commits the refreshed files.

The repository must allow GitHub Actions **read and write** repository permissions so the workflow can commit the package files.

## One-time first-run save

When `Setup.sh` finishes dependency setup and is about to start the menu, it runs
`Needs/first_run_save.py`. On the first successful run only, this creates:

```text
~/storage/downloads/DedSec Project.zip
```

The archive contains only this DedSec Project checkout. It is written only to
Android internal-storage Downloads. A complete temporary archive is built and
validated before it replaces an older archive. The completion marker is stored
under `Needs/State/`, so later runs start the menu without creating another save.
If Android storage permission is unavailable, no marker is written and setup
retries the save on the next run.
