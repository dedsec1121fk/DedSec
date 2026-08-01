# Vendored Python modules

`Cache/` stores installable wheels and source archives. `Setup.sh` uses these files before consulting PyPI.

The Sunday workflow prefers portable source distributions and resolves their dependency closure. If a project does not publish a source distribution, the workflow accepts only a universal `*-none-any.whl` fallback; it does not commit Linux runner-specific wheels as Android dependencies.
