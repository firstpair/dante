# Dante Multilingual Vault

A reproducible Obsidian vault for reading Dante's complete *Commedia* with
aligned English and Russian translations. Italian is the
rightmost desktop column. English and Russian have persistent independent
toggles; on narrow iOS layouts each aligned tercet is a swipeable horizontal
strip. Selecting an Italian word opens an offline FreeDict drawer.

## Build

The project pins current stable GIL-enabled (non-`t`) CPython 3.14.7 exactly.

```sh
./scripts/bootstrap-uv.sh
./scripts/uv sync
./scripts/uv run python scripts/fetch_sources.py
./scripts/uv run python scripts/build_vault.py dist/Dante-Multilingual-Vault
./scripts/uv run python scripts/check_vault.py dist/Dante-Multilingual-Vault
```

The acquisition step verifies the pinned FreeDict SHA-512 digests and records
source URLs and SHA-256 hashes in `sources/PROVENANCE.json`.

The Lozinsky-based generated vault is a local study copy. Do not publish it
without the rights review described in `RIGHTS.md`.

See [RIGHTS.md](RIGHTS.md) for the redistribution basis and attribution.
