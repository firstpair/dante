# Sources, rights, and attribution

- Italian: Dante Alighieri, *La Divina Commedia*, Project Gutenberg ebook
  1012. Dante died in 1321; the source text is public domain. Project
  Gutenberg marks this ebook public domain in the United States. Its license
  notice remains in `sources/raw/italian.txt`.
- English: Henry Wadsworth Longfellow translation, Project Gutenberg ebook
  1004. Longfellow died in 1882; the translation is public domain. Its license
  notice remains in `sources/raw/english.txt`.
- Russian: Mikhail Lozinsky translation, obtained from Lib.ru. Lozinsky died
  in 1955 and the authorial term expired in Russia on 1 January 2026. Its US
  copyright status is less straightforward because publication began after
  1930. The study vault and bundle built with `--translations en,ru` are
  therefore local copies and must not be published or redistributed without
  a jurisdiction-specific rights review. The public edition (the default
  build, and everything on First Pair Press) contains only the Italian and
  Longfellow's English.
- Dictionaries: FreeDict `ita-eng` and `ita-rus`, release 2025.11.23, derived
  from Wiktionary via WikDict/DBnary and distributed under CC BY-SA 3.0.
  The complete FreeDict `COPYING` files are included in the built vault. The
  analyser and senses come from the English (and, in the study copy, Russian
  and Italian) Wiktionary extractions pinned by FirstPair, CC BY-SA 4.0.
- Cover and header art: `images/dante-header.png`, First Pair Press.

Only the general reader code, schemas, and tests belong upstream in FirstPair;
the Russian text and generated local vault do not.
