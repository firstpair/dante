# Adding a translation, or a whole language, to the Commedia

This repository builds three readers of Dante from one set of sources: a
book (PDF, EPUB, HTML), an Obsidian vault with the FirstPair Reader, and an
Emacs Info bundle. Every translation is aligned to the Italian tercet by
tercet, and every Italian word opens a dictionary in the languages the
edition carries. This guide is for adding a translation — a fifth English
rendering, a German or Spanish one, a translation into a language the
edition does not yet speak — and having all three readers pick it up.

Everything is plain Python and JSON; no build step is hidden. The whole
addition is usually four steps and a few dozen lines.

## 1. Find a text you may redistribute

The public editions carry only texts that are public domain everywhere they
are served (translator dead more than seventy years, or first published
before 1930 for the United States). Good hunting grounds:

- **Project Gutenberg** (`gutenberg.org`) — the English translations here
  (Longfellow 1004, Cary 8800, Norton 1995–1997, Sibbald 41537) and the
  Italian (1012) come from it; it also holds Spanish (57303) and Friulian
  (16190) versions. The plain-text `pg<id>.txt` files are the easiest to
  parse.
- **Wikisource** in the target language — check that the page is a
  complete transcription, not a scan-transclusion with pages missing (Min's
  Purgatorio there skips a page in canto XVII, which is why the Russian
  comes from Lib.ru instead).
- **Lib.ru/Классика** (`az.lib.ru`) for Russian: nineteenth-century
  editions in their original orthography, Windows-1251 encoded.
- **Internet Archive** for OCR text of scanned editions (Anderson 1921,
  Langdon 1918–21, the Temple Classics prose) — usable, but budget time for
  cleaning.

Record the URL and a SHA-256 in `sources/PROVENANCE.json` by adding the
download to `scripts/fetch_sources.py` (`GUTENBERG` for plain text, `AZLIB`
for Lib.ru; add a similar table for another site). The fetcher writes into
`sources/raw/`, which is ignored by Git: sources are fetched, never
committed.

A translation still in copyright may be used **only** in the local study
edition (`--edition study`), which is never published; see `RIGHTS.md` and
the `STUDY` edition set in `scripts/translations.py`.

## 2. Write a parser

A parser turns the raw file into `{(cantica, canto): lines}`, where
`cantica` is `"inferno"`, `"purgatorio"`, or `"paradiso"` and `lines` is the
list of verse lines (or, for prose, paragraphs). Put it in
`scripts/translations.py` beside the others, which cover the usual shapes:

| Shape | Example | Parser |
| --- | --- | --- |
| A header line per canto, one verse per line | Longfellow, the Italian | `parse_gutenberg(path, header_regex)` |
| Cantica and canto headings, blank-verse lines | Cary | `parse_cary` |
| Prose paragraphs with bracketed footnotes | Norton | `parse_norton` |
| Verse with margin line numbers and note marks | Sibbald | `parse_sibbald` |
| Lib.ru old-orthography HTML, tercet or line numbers | Min, Petrov, Fedorov | `parse_azlib_numbered` |
| Lib.ru prose with headings | Chuiko | `parse_azlib_prose` |
| Lib.ru with no headings, a line number every third line | Minaev | `parse_azlib_linenumbered` |

Two habits make parsers robust: take cantos **in order of appearance**
rather than trusting the numeral in the heading (OCR turns XVII into XVI),
and stop the verse where the **commentary** begins (a numbered line far
longer than any verse, or a range like `94--102.`). If a transcription
lacks lines, leave the gap **blank** rather than shifting what follows —
`parse_azlib_numbered` pads to the Italian count.

`check_cantos(name, result)` at the end of a parser asserts the expected
number of cantos and a plausible line count; run it.

## 3. Register the translation

Append a `Translation` to `TRANSLATIONS` in `scripts/translations.py`:

```python
Translation("de-streckfuss", "de", "Deutsch", "Karl Streckfuß", "Streckfuß (1876)", "1876",
            "verse", "line", PUBLIC, default=True, source="german-streckfuss.txt"),
```

The fields:

- `id` — language code, hyphen, translator; used in chapter files, region
  tables, and the reader's remembered choices.
- `lang`, `label` — the language and its name as the reader shows it.
  The first translation registered for a language with `default=True` is the
  one shown until the reader chooses another.
- `title`, `years`, `form` (`verse` or `prose`).
- `alignment` — how its lines meet the tercets:
  - `line`: the translator kept Dante's line count (Longfellow, Sibbald,
    Min, Petrov, Fedorov, Lozinsky). Rows show the same verses.
  - `proportional`: verse of another length (Cary, Minaev). The lines are
    cut at the same fractions of the canto as the tercets. Marked ≈.
  - `prose`: sentences are distributed by their share of the canto's
    characters (Norton, Chuiko). Marked ≈.
- `editions` — which editions may carry it: `PUBLIC` (all), `RUSSIAN`
  (`ru` and `study`), or `STUDY` (local only). A new language wants its own
  edition set and a new entry in `EDITIONS` in `scripts/build_vault.py`.
- `coverage` — the cantiche it covers, when partial (`("inferno",)`).
- `orthography` — note `modernised` or `original` when spelling was changed
  by rule (`modernise_russian` shows the shape of such a rule).

Then teach `load_texts` to call your parser for the new id, and list the
raw file among the edition's sources (`ENGLISH_SOURCES`, `RUSSIAN_SOURCES`,
or a new tuple) so the vault's `Sources/` folder carries it with its licence
notice.

## 4. A new language needs a dictionary

The reader answers in the languages of the edition's translations. For a
language it does not yet speak you need a dictionary from Italian into it in
the shared `firstpair-reader-dictionary-v1` shape: entries keyed by the
folded Italian form, each a list of `{headword, partOfSpeech, definitions,
grammar?}`. The projection in `build_vault.py` shows the two sources that
work everywhere:

- **FreeDict** (`freedict.org`) publishes Italian→X dictionaries under
  CC BY-SA for many languages; `freedict_lemmas` reads their TEI.
- **Wiktionary** through Kaikki extractions, pinned by FirstPair in
  `~/src/firstpair/publishing/emacs/lexicon/italian/SOURCES.json` as
  *glossaries* of four kinds (entries, inverted translation tables, direct
  translation tables, and a pivot through English senses). The Russian
  dictionary is built from five of them; add the same kinds for the new
  language (the German Wiktionary's Italian entries and translation tables,
  say) and list them in `emacs.lexicon.translations` of the edition's
  `vault.build.json`.

`firstpair_emacs.dictionaries.project` then joins analyses of every Italian
form in the poem — elisions, apocope, Dante's old spellings — with the
senses, and `write_sharded` stores the result in files small enough to sync
to a phone.

## 5. Build and check

```sh
./scripts/uv run python scripts/fetch_sources.py
./scripts/uv run python scripts/build_vault.py "dist/Dante Commedia Vault Russian" --edition ru
./scripts/uv run python scripts/check-obsidian-vault.py "dist/Dante Commedia Vault Russian"
git commit -am "Add …"       # the Emacs bundle binds to a commit
~/src/firstpair/publishing/scripts/firstpair-emacs build vault.build.russian.json --product desktop
~/src/firstpair/publishing/scripts/firstpair-emacs validate --bundle "dist/Dante Commedia Emacs Russian"
```

The validator counts cantos and units, checks that every translation's
coverage matches what the chapters carry, refuses Lozinsky in a public
edition and Cyrillic in the English one, and measures the dictionary shards.
Open the vault in Obsidian (or the bundle with `M-x firstpair-read`) and
rotate the new translation into a column; `dist/…/_data/alignment-report.json`
lists, per canto, how many lines each translation contributed, which is the
quickest way to see a parser that lost a page.

## What the readers do with it

Nothing else changes. The Obsidian Reader lists the translation in its
language's column header, rotates to it on click, and can show it beside
another translation of the same language with **+**; the Emacs reader does
the same with `C-c C-v` and `C-c C-b`; both mark approximate alignment with
≈ and skip the translation on pages it does not cover. The book generator
(`scripts/build_book.py`) takes one translation per edition — set it in
`BOOKS` to print a new pairing.
