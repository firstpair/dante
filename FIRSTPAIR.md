# FirstPair Library Contract

slug: dante-commedia
shelf: literature
default_edition: full

This file is the library deployment contract read by the centralized FirstPair
publisher (`~/src/firstpair`). Keep the key-value header simple and unbulleted.

## Ownership

This repository owns the aligned editions of Dante's *Commedia*: source
acquisition (`scripts/fetch_sources.py`), the translations registry, parsers,
and alignment (`scripts/translations.py`), the vault and Emacs builder
(`scripts/build_vault.py`, `vault.build*.json`), the manuscript generator
(`scripts/build_book.py`), `book.build.json` and `book.russian.build.json`,
the covers (`cover/*.typ` → `cover/*.png`) and header image
(`images/dante-header.png`), the source-owned validator
(`scripts/check-obsidian-vault.py`), the reviewed dictionary supplements, and
the guide fragments under `docs/`. FirstPair owns the unified book builder,
the Reader plugin, the Emacs Info writers and reader, the pinned Wiktionary
extractions, the catalog, hosted readers, Blob uploads, and deployment.

Two titles are published from this repository, both **full** (every text is
public domain; see `RIGHTS.md`):

| Title | Slug | Book | Vault | Emacs |
| --- | --- | --- | --- | --- |
| Italian and English | `dante-commedia` | `book/dist-full` | `dist/Dante Commedia Vault` | `dist/Dante Commedia Emacs` |
| Italian, English, and Russian | `dante-commedia-russian` | `book/dist-russian` | `dist/Dante Commedia Vault Russian` | `dist/Dante Commedia Emacs Russian` |

The study edition with Lozinsky's Russian is never published.

## Build

```sh
./scripts/uv run python scripts/fetch_sources.py
./scripts/uv run python scripts/build_vault.py "dist/Dante Commedia Vault" --edition en
./scripts/uv run python scripts/build_vault.py "dist/Dante Commedia Vault Russian" --edition ru
./scripts/uv run python scripts/check-obsidian-vault.py "dist/Dante Commedia Vault"
./scripts/uv run python scripts/check-obsidian-vault.py "dist/Dante Commedia Vault Russian"
git commit …   # vault builds refresh vault.build*.json; the Emacs bundles bind to HEAD
"$HOME/src/firstpair/publishing/scripts/build-library-book.sh" --repo-root "$(git rev-parse --show-toplevel)"
"$HOME/src/firstpair/publishing/scripts/build-library-book.sh" --repo-root "$(git rev-parse --show-toplevel)" --config book.russian.build.json
"$HOME/src/firstpair/publishing/scripts/firstpair-emacs" build vault.build.json --product desktop
"$HOME/src/firstpair/publishing/scripts/firstpair-emacs" build vault.build.russian.json --product desktop
"$HOME/src/firstpair/publishing/scripts/firstpair-emacs" validate --bundle "dist/Dante Commedia Emacs"
"$HOME/src/firstpair/publishing/scripts/firstpair-emacs" validate --bundle "dist/Dante Commedia Emacs Russian"
"$HOME/src/firstpair/publishing/scripts/firstpair-vault" guide vault.build.json --product desktop --output dist/dante-commedia-vault-guide.md
"$HOME/src/firstpair/publishing/scripts/firstpair-vault" guide vault.build.russian.json --product desktop --output dist/dante-commedia-russian-vault-guide.md
cp cover/dante-commedia-russian-cover.png book/dist-russian/cover.png   # the second title is published from its dist directory,
cp images/dante-header.png book/dist-russian/headboard.png             # so its card images sit beside it
```

Outputs are ignored by Git: the book packages under `book/dist-*/`, the
vaults, bundles, and composed guides under `dist/` (a guide's build identity
names the commit being published, so it is generated after the last commit).

## Publish

Both repositories clean and pushed; the bundles' manifests must name the
pushed HEAD. Dry run first, then live.

```sh
cd "$HOME/src/firstpair"
npm run library:publish -- "$HOME/src/dante" --full \
  --vault-dir "dist/Dante Commedia Vault" --vault-guide dist/dante-commedia-vault-guide.md --emacs \
  --title "Dante — La Divina Commedia" --kicker "Aligned edition" --tags "finished,literature,Dante,Italian" \
  --description "The complete Commedia with Dante's Italian beside four English translations — Longfellow, Cary, Norton, Sibbald — tercet by tercet, and a dictionary that analyses every Italian word: a book, an Obsidian vault, and an Emacs Info bundle." \
  --dry-run --no-build --no-smoke --no-deploy --no-icloud
npm run library:publish -- "$HOME/src/dante" --full \
  --vault-dir "dist/Dante Commedia Vault" --vault-guide dist/dante-commedia-vault-guide.md --emacs

npm run library:publish -- "$HOME/src/dante/book/dist-russian" --slug dante-commedia-russian --full \
  --vault-dir "$HOME/src/dante/dist/Dante Commedia Vault Russian" --vault-guide "$HOME/src/dante/dist/dante-commedia-russian-vault-guide.md" \
  --emacs-dir "$HOME/src/dante/dist/Dante Commedia Emacs Russian" \
  --title "Dante — La Divina Commedia (with Russian)" --kicker "Aligned edition" --tags "finished,literature,Dante,Italian,Russian" \
  --description "The complete Commedia with Dante's Italian beside four English and five Russian translations — Longfellow, Cary, Norton, Sibbald; Min, Petrov, Fedorov, Chuiko, Minaev — tercet by tercet, and a dictionary that analyses every Italian word in English and Russian: a book, an Obsidian vault, and an Emacs Info bundle." \
  --dry-run --no-build --no-smoke --no-deploy --no-icloud
npm run library:publish -- "$HOME/src/dante/book/dist-russian" --slug dante-commedia-russian --full \
  --vault-dir "$HOME/src/dante/dist/Dante Commedia Vault Russian" --vault-guide "$HOME/src/dante/dist/dante-commedia-russian-vault-guide.md" \
  --emacs-dir "$HOME/src/dante/dist/Dante Commedia Emacs Russian"
```
