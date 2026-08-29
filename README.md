# Dante Multilingual Vault

A reproducible Obsidian vault for reading Dante's complete *Commedia* with
aligned English and Russian translations, for readers learning Italian
from either. Italian is always the leftmost column; Russian and English have
persistent toggles (Russian in the middle when both are on). On narrow iOS
layouts each aligned tercet is a swipeable horizontal strip. Selecting an
Italian word opens an offline dictionary drawer whose analyser restores
Dante's elisions, truncations, and old spellings to their modern headwords
(FirstPair's shared Italian lexicon over the English and Russian Wiktionary
extractions, FreeDict, and a reviewed supplement).

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
source URLs and SHA-256 hashes in `sources/PROVENANCE.json`. The Wiktionary
extractions are pinned by FirstPair (`publishing/emacs/lexicon/italian/`) and
fetched once with `firstpair-emacs lexicon --language italian`.

The vault build also writes `vault.build.json`; the Emacs edition follows:

```sh
~/src/firstpair/publishing/scripts/firstpair-emacs build vault.build.json --product desktop
~/src/firstpair/publishing/scripts/firstpair-emacs validate --bundle dist/Dante-Emacs
```

`sources/dictionaries/coverage.json` records which Italian forms have no
English or Russian entry; `sources/dictionaries/*supplement.json` are the
reviewed additions.

The Lozinsky-based generated vault and Emacs bundle are local study copies.
Do not publish them without the rights review described in `RIGHTS.md`.

See [RIGHTS.md](RIGHTS.md) for the redistribution basis and attribution.
