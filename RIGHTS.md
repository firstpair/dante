# Sources, rights, and attribution

All texts in the public editions are in the public domain in the United
States and in the countries of origin; dictionaries are under Creative
Commons licences that permit redistribution with attribution.

## Italian

- Dante Alighieri, *La Divina Commedia*, Project Gutenberg ebook 1012. The
  poem is public domain; Project Gutenberg's licence notice remains in
  `Sources/italian.txt`.

## English translations (Project Gutenberg)

- Henry Wadsworth Longfellow (1807–1882), *The Divine Comedy* (1867), ebook 1004.
- Henry Francis Cary (1772–1844), *The Vision; or Hell, Purgatory, and Paradise* (1814), ebook 8800.
- Charles Eliot Norton (1827–1908), *The Divine Comedy*, prose (1891–1892), ebooks 1995, 1996, 1997.
- James Romanes Sibbald (1834–1908), *The Inferno* (1884), ebook 41537.

## Russian translations (Lib.ru/Классика, az.lib.ru)

Transcribed by Lib.ru volunteers from the printed editions, in the original
pre-1918 orthography; this edition also offers each modernised by rule
(`modernise_russian` in `scripts/translations.py`).

- Дмитрий Егорович Мин (1818–1885), *Ад* (1855), *Чистилище* (1902), *Рай* (1904).
- Дмитрий Дмитриевич Минаев (1835–1889), *Чистилище* and *Рай* (1874–1879, Wolff edition).
- В. А. Петров, *Ад* in terza rima (1887).
- А. П. Фёдоров, *Ад* in verse (1898).
- В. В. Чуйко (1839–1899), *Ад* in prose (1894).

## Local study copy only

- Михаил Леонидович Лозинский (1886–1955), *Божественная комедия*
  (1939–1945), obtained from Lib.ru. The authorial term expired in Russia on
  1 January 2026, but the translation was first published after 1930 and its
  United States status is unsettled. It is carried only by the `study`
  edition, which is never published or redistributed; the validator refuses
  it in any public vault.

## Dictionaries

- FreeDict `ita-eng` and `ita-rus`, release 2025.11.23, derived from
  Wiktionary via WikDict/DBnary, CC BY-SA 3.0; the `COPYING` files travel
  with every vault.
- Wiktionary extractions by Wiktextract, published by Kaikki.org, pinned by
  FirstPair (`publishing/emacs/lexicon/italian/SOURCES.json`): the English
  Wiktionary's Italian entries (analysis and English senses), the Russian
  Wiktionary's Italian entries and Russian translation tables, the Italian
  Wiktionary's translation tables, and the English Wiktionary's English
  senses as a pivot. CC BY-SA 4.0.
- `sources/dictionaries/*supplement.json`: reviewed additions by First Pair, CC BY-SA 4.0.

## Art

- `images/dante-header.png` and the covers rendered from it: First Pair Press.

Only the general reader code, schemas, and tests belong upstream in
FirstPair; the texts and generated vaults do not.
