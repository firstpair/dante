# Dante — La Divina Commedia

A reproducible aligned edition of Dante's complete *Commedia* for readers
learning Italian: the Italian beside its translation, tercet by tercet, in
three forms built from the same sources — a book (PDF, EPUB, HTML), an
Obsidian vault with the FirstPair Reader, and an Emacs Info bundle. Italian
is always the leftmost column; on narrow iOS layouts each aligned tercet is a
swipeable horizontal strip. Selecting an Italian word opens an offline
dictionary whose analyser restores Dante's elisions, truncations, and old
spellings to their modern headwords (FirstPair's shared Italian lexicon over
the Wiktionary extractions, FreeDict, and a reviewed supplement).

Two editions come from one build:

- **Public** (`--translations en`, the default): Italian and Longfellow's
  English, both public domain. Published on First Pair Press as
  `dante-commedia`; see `FIRSTPAIR.md`.
- **Study copy** (`--translations en,ru`): adds Lozinsky's Russian (Russian
  in the middle when both translations are on) and the Russian dictionaries.
  Local only; never published (see `RIGHTS.md`).

## Build

The project pins current stable GIL-enabled (non-`t`) CPython 3.14.7 exactly.

```sh
./scripts/bootstrap-uv.sh
./scripts/uv sync
./scripts/uv run python scripts/fetch_sources.py
./scripts/uv run python scripts/build_vault.py "dist/Dante Commedia Vault"
./scripts/uv run python scripts/check-obsidian-vault.py "dist/Dante Commedia Vault"
./scripts/uv run python scripts/build_vault.py dist/Dante-Multilingual-Vault --translations en,ru
./scripts/uv run python scripts/check-obsidian-vault.py dist/Dante-Multilingual-Vault
```

The acquisition step verifies the pinned FreeDict SHA-512 digests and records
source URLs and SHA-256 hashes in `sources/PROVENANCE.json`. The Wiktionary
extractions are pinned by FirstPair (`publishing/emacs/lexicon/italian/`) and
fetched once with `firstpair-emacs lexicon --language italian`.

The public vault build writes `vault.build.json` and the study build
`vault.build.study.json`; the Emacs editions follow (each bundle binds to the
committed HEAD, so commit first):

```sh
~/src/firstpair/publishing/scripts/firstpair-emacs build vault.build.json --product desktop
~/src/firstpair/publishing/scripts/firstpair-emacs validate --bundle "dist/Dante Commedia Emacs"
~/src/firstpair/publishing/scripts/firstpair-emacs build vault.build.study.json --product desktop
~/src/firstpair/publishing/scripts/firstpair-emacs validate --bundle dist/Dante-Emacs
```

The book package (`book/dist-full/`) is built by FirstPair's unified builder
from `book.build.json`; `scripts/build_book.py` writes the aligned manuscript
and `book/aligned.lua` sets each tercet as a two-column grid:

```sh
~/src/firstpair/publishing/scripts/build-library-book.sh --repo-root "$PWD"
```

`sources/dictionaries/coverage.json` records which Italian forms have no
English or Russian entry; `sources/dictionaries/*supplement.json` are the
reviewed additions.

The Lozinsky-based study vault and Emacs bundle are local copies. Do not
publish them without the rights review described in `RIGHTS.md`; the public
edition never contains the Russian text or dictionaries, and
`scripts/check-obsidian-vault.py` refuses a public vault with Cyrillic in it.

See [RIGHTS.md](RIGHTS.md) for the redistribution basis and attribution.

The language pipeline, its measured coverage, and what remains are recorded
in [docs/LANGUAGE-PIPELINE-REPORT.md](docs/LANGUAGE-PIPELINE-REPORT.md).
