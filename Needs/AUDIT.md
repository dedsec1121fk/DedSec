# Dependency Audit Report

- Python files currently present in the project: 178
- Audited Python distributions: 49
- Required Termux package roots: 48
- Optional Termux package roots: 6
- Current AArch64 recursive package closure: 245 package records
- Current AArch64 resolved download size: approximately 372.06 MiB
- Optional root unavailable in the current Termux indexes: `avahi`
- The incorrect manifest name `espeak-ng` was corrected to the current Termux package name `espeak`.
- Embedded local imports such as `games` and `launcher` are not treated as PyPI distributions.
- The two existing `Tree Explorer.py` syntax corrections are retained.

`package-lock-aarch64.json` records exact package versions, dependency metadata, source files, mirror URLs, sizes, and SHA-256 checksums. The maintenance workflow recalculates and validates the real cache before replacement.
