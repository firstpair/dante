# FirstPair Library Contract

slug: dante-commedia
shelf: literature
default_edition: full

This file is the library deployment contract read by the centralized FirstPair
publisher (`~/src/firstpair`). Keep the key-value header simple and unbulleted.

## Ownership

This repository owns the public Italian–English edition of Dante's *Commedia*:
the source acquisition (`scripts/fetch_sources.py`), the aligned manuscript
generator (`scripts/build_book.py`), `book.build.json`, the cover
(`cover/cover.typ` → `cover/dante-commedia-cover.png`) and header image
(`images/dante-header.png`), the vault and Emacs builder
(`scripts/build_vault.py`, `vault.build.json`), the source-owned vault
validator (`scripts/check-obsidian-vault.py`), the reviewed dictionary
supplements, and the guide fragments under `docs/`. FirstPair owns the unified
book builder, the Reader plugin, the Emacs Info writers and reader, the pinned
Wiktionary extractions, the catalog, hosted readers, Blob uploads, and
deployment.

The public edition is **full** (both texts are public domain; see `RIGHTS.md`).
The Russian study copy built with `--translations en,ru` is never published.

## Build

```sh
./scripts/uv run python scripts/fetch_sources.py
./scripts/uv run python scripts/build_vault.py "dist/Dante Commedia Vault"
./scripts/uv run python scripts/check-obsidian-vault.py "dist/Dante Commedia Vault"
git commit …   # the vault build refreshes vault.build.json; the Emacs bundle binds to HEAD
"$HOME/src/firstpair/publishing/scripts/build-library-book.sh" --repo-root "$(git rev-parse --show-toplevel)"
"$HOME/src/firstpair/publishing/scripts/firstpair-emacs" build vault.build.json --product desktop
"$HOME/src/firstpair/publishing/scripts/firstpair-emacs" validate --bundle "dist/Dante Commedia Emacs"
"$HOME/src/firstpair/publishing/scripts/firstpair-vault" guide vault.build.json --product desktop --output dist/dante-commedia-vault-guide.md
```

Outputs are ignored by Git: the book package in `book/dist-full/`, the vault
and Emacs bundle under `dist/`, and the composed vault guide (its build
identity names the commit being published, so it is generated after the last
commit rather than tracked).

## Publish

```sh
cd "$HOME/src/firstpair"
npm run library:publish -- "$HOME/src/dante" --full \
  --vault-dir "dist/Dante Commedia Vault" --vault-guide dist/dante-commedia-vault-guide.md --emacs \
  --title "Dante — La Divina Commedia" --kicker "Aligned edition" --tags "finished,literature,Dante,Italian" \
  --description "The complete Commedia with Dante's Italian beside Longfellow's English, tercet by tercet, and a learner's dictionary that restores every old form to its headword — as a book, an Obsidian vault, and an Emacs Info bundle." \
  --dry-run --no-build --no-smoke --no-deploy --no-icloud
npm run library:publish -- "$HOME/src/dante" --full \
  --vault-dir "dist/Dante Commedia Vault" --vault-guide dist/dante-commedia-vault-guide.md --emacs
```

Both repositories must be clean and pushed before the live run; the Emacs
bundle's manifest must name the pushed HEAD.
