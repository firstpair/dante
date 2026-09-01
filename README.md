# Dante — La Divina Commedia, aligned with its translations

An open edition of Dante's complete *Commedia* for readers and learners of
Italian: the Italian beside any of nine public-domain translations — four
English (Longfellow, Cary, Norton, Sibbald) and five Russian (Min, Petrov,
Fedorov, Chuiko, Minaev) — aligned tercet by tercet, with a dictionary that
analyses every Italian word (elisions, truncations, and Dante's old spellings
restored to their modern headword) and answers in English and Russian. Three
readers are built from one source: a book (PDF, EPUB, HTML), an Obsidian
vault with the FirstPair Reader, and an Emacs Info bundle.

Published on First Pair Press as one title, **dante-commedia**, in two
language versions: *Italian and English*, and *Italian, English, and Russian*
(`https://firstpair.org/books/dante-commedia/`). The paper
`docs/PAPER.md` describes the edition; `docs/ADDING-TRANSLATIONS.md` shows how
to add a translation or a language; `docs/LANGUAGE-PIPELINE-REPORT.md` records
the dictionary pipeline and its coverage.

## Editions

| Edition | Flag | Texts | Output | Published |
| --- | --- | --- | --- | --- |
| English | `--edition en` | Italian + Longfellow, Cary, Norton, Sibbald | `dist/Dante Commedia Vault`, `dist/Dante Commedia Emacs`, `book/dist-full` | the title itself |
| Russian | `--edition ru` | + Min (modern and original spelling), Petrov, Fedorov, Chuiko, Minaev | `dist/Dante Commedia Vault Russian`, `dist/Dante Commedia Emacs Russian`, `book/dist-russian` | version `russian` |
| Study | `--edition study` | + Lozinsky, Ilyushin (2008), Palma, James | `dist/Dante-Multilingual-Vault`, `dist/Dante-Emacs` | never (see `RIGHTS.md`) |

Every translation is registered in `scripts/translations.py` with its
language, maker, and alignment: line for line (Longfellow, Sibbald, Min,
Petrov, Fedorov, Lozinsky, Ilyushin), proportional cuts for verse of another length
(Cary, Minaev), sentence distribution for prose (Norton, Chuiko). Approximate
alignments are marked ≈ in the readers.

## Build

The project pins CPython 3.14.7 with uv; FirstPair (`~/src/firstpair`) must be
checked out beside this repository.

```sh
./scripts/bootstrap-uv.sh
./scripts/uv sync
./scripts/uv run python scripts/fetch_sources.py                       # Gutenberg, Lib.ru, FreeDict; hashes to sources/PROVENANCE.json
~/src/firstpair/publishing/scripts/firstpair-emacs lexicon --language italian   # Wiktionary extractions, pinned by FirstPair
./scripts/uv run python scripts/build_vault.py "dist/Dante Commedia Vault" --edition en
./scripts/uv run python scripts/build_vault.py "dist/Dante Commedia Vault Russian" --edition ru
./scripts/uv run python scripts/build_vault.py dist/Dante-Multilingual-Vault --edition study
./scripts/uv run python scripts/check-obsidian-vault.py "dist/Dante Commedia Vault"
```

A vault build writes the edition's `vault.build*.json`; commit, then build
the Emacs bundles (they bind to the commit) and the books:

```sh
~/src/firstpair/publishing/scripts/firstpair-emacs build vault.build.json --product desktop
~/src/firstpair/publishing/scripts/firstpair-emacs build vault.build.russian.json --product desktop
~/src/firstpair/publishing/scripts/firstpair-emacs validate --bundle "dist/Dante Commedia Emacs"
~/src/firstpair/publishing/scripts/build-library-book.sh --repo-root "$PWD"                                   # Italian + Longfellow
~/src/firstpair/publishing/scripts/build-library-book.sh --repo-root "$PWD" --config book.russian.build.json  # Italian + Min
```

`scripts/refresh-reader-plugin.py VAULT` replaces only the Reader plugin in a
built or live vault, the one write allowed while Obsidian is open.

## Reading

**Obsidian.** Open the vault; `Home.md` links every canto into the Reader.
Italian is the first column; each translation column's header names the
translation and rotates through the language's translations; **+** opens a
second column of the same language. On a phone held upright the tercet
stacks; Settings → FirstPair Reader pins a layout, reserves the dictionary
column, keeps the dictionary open, or docks it at the bottom.

**Emacs.** `(load "…/init.el")`, then `M-x firstpair-read`. `C-c C-d` looks up
the word at point, `C-c C-t` chooses languages, `C-c C-v` rotates a
language's translation, `C-c C-b` shows a second one.

On iSH, keep the extracted bundle at `/root/books/Dante-Emacs` and install its
launcher beside it:

```sh
cd /root/books
curl -fLO https://firstpair.org/emacs/dante.sh
chmod +x dante.sh
./dante.sh
```

The launcher checks the small Reader version and SHA-256 record first. If that
version is already installed, it skips the package tar and opens Dante at once.

See `RIGHTS.md` for the redistribution basis of every text and dictionary,
and `FIRSTPAIR.md` for publication.
