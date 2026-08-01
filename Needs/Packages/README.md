# Vendored Termux Packages

`Cache/<architecture>/` is the repository-owned offline package store. It is designed to contain the real Termux `.deb` files for the complete recursive dependency closure, not only a list of package names.

## Current package resolution

- `termux-required.txt` contains required root packages.
- `termux-optional.txt` contains optional feature roots.
- `package-lock-aarch64.json` records the exact resolved versions, source paths, sizes, SHA-256 checksums, dependencies, and mirror URLs.
- `download-plan-aarch64.tsv` is the same resolution in a simple machine-readable table.
- `Indexes/aarch64/` contains compressed package-index snapshots used for the current resolution audit.
- `Cache/cache-manifest.json` describes files that are actually present in the cache.

The current AArch64 lock resolves the complete required closure and all currently available optional closures. `avahi` remains listed as optional because `Devices Finder.py` can use `avahi-resolve-address`, but the package is not present in the current Termux main or X11 indexes; Setup treats that feature as optional.

## Safe refresh behavior

`.github/workflows/update-needs.yml` runs every Sunday and can also be started manually. The maintenance program:

1. Resolves the current package indexes.
2. Downloads the full new closure into a separate temporary staging directory.
3. Retries downloads and rotates across official/current mirrors.
4. Validates every package against the repository SHA-256 value.
5. Splits any file larger than 45 MiB into ordered GitHub-safe parts.
6. Validates the complete staged set.
7. Keeps a rollback copy while atomically replacing the old cache.
8. Uploads the verified set as a workflow artifact before committing it.

The old cache is never deleted before the complete replacement has downloaded and passed validation.

## Setup behavior

`bash Setup.sh` checks and installs locally stored `.deb` files before refreshing any repository. It then asks Termux repositories for newer versions and downloads only unresolved or missing items before launching the menu.

A split package can be reconstructed manually with:

```bash
bash Needs/Packages/reconstruct-package.sh Needs/Packages/Cache/aarch64/package.deb.part001
```
