# Every Word of Dante: An Open, Aligned, Multi-Translation Commedia for Readers and Learners

*Alexy Khrabrov, First Pair Press — August 2026*

## Abstract

We describe an open edition of Dante's *Commedia* in which the Italian
stands beside any of nine translations — four English, five Russian, all in
the public domain — aligned tercet by tercet, and in which every one of the
poem's 12,766 distinct Italian word forms opens a dictionary that explains
the form itself: its elision, apocope, or fourteenth-century spelling,
restored to a modern headword, with senses in English and Russian and the
poem's own lines as examples. The edition is delivered in three readers
built from one source — a book, an Obsidian vault, and an Emacs Info
bundle — and its whole pipeline, from the acquisition of texts to the
publication of the readers, is a public repository designed so that a
student anywhere can add a translation, or a language, in an afternoon.

## 1. Why a poem needs a reader

Everyone who has tried to read Dante in Italian knows the two walls. The
first is the language: not Italian but Dante's Italian, whose *avea*, *fé*,
*ch'i'*, *ei*, *doppiero* and *etterno* are not in the pocket dictionary and
not in the one on the phone either. The second is the translation: it is on
the facing page of a good edition, but only one translation, chosen by a
publisher long ago, and it may be Longfellow's careful line-for-line English
when what you needed was Cary's freer blank verse, or Norton's prose, or,
if you grew up with Russian, Min's terza rima rather than Lozinsky's.

Digital editions could have removed both walls decades ago and mostly did
not. The sites that show a translation lock it to one; the sites with a
dictionary look up the surface form and say *no entry* for half of Dante's
words; and none of them let you turn a phone sideways and read three
columns.

This edition is our attempt to remove both walls at once, and to do it in
the open.

## 2. The texts

The Italian is Project Gutenberg's ebook 1012. The English translations are
Longfellow (1867, verse, line for line), Cary (1814, blank verse), Norton
(1891–92, prose), and Sibbald's Inferno (1884, terza rima), all from Project
Gutenberg. The Russian ones come from Lib.ru/Классика's transcriptions of the
nineteenth-century editions: Dmitry Min's complete Commedia in Dante's own
metre (Inferno 1855, Purgatorio 1902, Paradiso 1904), Vasily Petrov's terza
rima Inferno (1887), A. P. Fedorov's Inferno (1898), V. V. Chuiko's prose
Inferno (1894), and Dmitry Minaev's Purgatorio and Paradiso (1874–79). All
nine are public domain; the Russian ones are offered both in the spelling
of their editions and modernised by rule from the pre-1918 orthography. A
tenth, Mikhail Lozinsky's, and an eleventh, Alexander Ilyushin's complete
2008 edition in Dante's metre, live only in a local study edition of the same
build and are never published.

Acquisition is a script that records every URL and hash. Where the source
transcription loses a page — Wikisource's Min skips one in Purgatorio XVII;
Lib.ru's Min Inferno XVI lacks twenty-nine lines — the gap is left blank in
the aligned text rather than shifting what follows, and reported.

## 3. Alignment

The unit of alignment is the tercet: three Italian lines, the last row of a
canto shorter. A translation meets the tercets in one of three ways, chosen
by the shape of the translation, not by hand:

- **Line for line.** Longfellow, Sibbald, Min, Petrov, Fedorov, Lozinsky, and Ilyushin
  kept Dante's line count. Tercet *i* takes their lines 3*i*..3*i*+2, and
  every row shows the same verses.
- **Proportional.** Cary and Minaev wrote verse of their own length (Minaev
  runs to 1.5–2.5 times Dante's). Their lines are cut at the same fractions
  of the canto as the tercets.
- **Prose.** Norton and Chuiko are cut into sentences, and each sentence
  is placed by its share of the canto's characters.

The first is exact; the other two are approximate and are marked ≈ wherever
they are shown. This honesty is deliberate: an alignment that pretends to
be word-for-word teaches wrong things, and a reader who can see that a row
is approximate can also see, in the neighbouring rows, where the sentence
actually went.

## 4. Every word

The dictionary is the part of this edition we are proudest of, and the part
that cost the most. Dante's 12,766 word forms are analysed by a shared
FirstPair language layer (`firstpair_emacs.languages.italian`) over the
English Wiktionary's Italian entries: inflection tables give the forms,
and a set of restoration rules gives Dante — elisions (*ch'i'*, *l'altre*),
apocope (*amor*, *cammin*), the old endings (*avea*, *dicea*, *fuoro*),
enclitic pronouns with doubled consonants (*dimmi*, *vedestù*), spelling
alternations (*etterno*, *loco*), prothetic *i-*, paragoge, and the
Wiktionary's own "form of" links, followed even when written only as gloss
text ("Dantesque form of *gaietto*"). Of the 12,766 forms, 11,921 are
analysed to a headword (93.4 %; 98.9 % of the running text), and the entry
says *how*: "apocope of *amore*", "old form of *diceva*", "elision of *il*".

Senses come from the English Wiktionary and FreeDict for English, and for
Russian from the Russian Wiktionary, the Italian Wiktionary's translation
tables into Russian (inverted), a pivot through English senses, FreeDict,
and a small reviewed supplement — a second pass follows related lemmas and
gloss words, so that *gaetta* reaches *gaietto* and *gaietto* reaches
Russian. Russian covers 11,412 forms (95.7 %). Every entry carries the
poem's own lines as examples. An unanalysed form says so; nothing is
guessed.

One defect of this pipeline is worth recording because it is general: the
Wiktionary's conjugation tables name each verb's auxiliary as a form row
(`avére`, tagged *auxiliary, transitive*), and until we skipped those rows
*avere* and *essere* each resolved to eighteen thousand lemmas.

## 5. Three readers from one source

The same chapter files, tercet-aligned JSON, feed three products:

**The book** — PDF, EPUB and HTML — sets each tercet as a two-column grid
with Dante on the left and one translation on the right (Longfellow in the
English book, Min in the Russian), a small line number in the margin, and
each canto on its own page. Pandoc and Typst do the setting; a forty-line
filter turns the aligned markup into grids.

**The Obsidian vault** is for the phone and the desk. The FirstPair Reader
plugin shows the Italian in the first column and the enabled languages after
it; each column header names the translation and rotates through the
language's translations on a tap; **+** opens a second column of the same
language, so Longfellow and Cary can stand beside one tercet. On a phone
held upright the tercet stacks — Italian first, translations indented
beneath — and returns to columns when the phone is turned; the dictionary
opens over the empty column, or as a band across the bottom the reader can
drag to size, and it can stay open, keeping the last entry, while pages
turn. Dictionaries travel as prefix-keyed shards small enough for Obsidian
Sync.

**The Emacs bundle** is an Info manual written directly by the builder (not
by `makeinfo`, so that every marked word's position is exact), with a
references manual that opens below the text, `C-c C-d` for the dictionary in
a third window, `C-c C-t` to choose languages, `C-c C-v` to rotate a
language's translation, `C-c C-b` to show two. It runs wherever Emacs runs,
including an iPhone under iSH.

Because the three readers consume one data contract — `firstpair-aligned-
chapter-v1`, `firstpair-parallel-reader-v1`, `firstpair-reader-dictionary-
v1` — a translation added to the registry appears in all three without
further work.

## 6. A global resource

The edition is published at `firstpair.org/books/dante-commedia/`, one
library entry with an Italian–English version and an Italian–English–Russian
one, each as book, vault, and Emacs bundle. The repository
`github.com/firstpair/dante` is public. Its acquisition
script, parsers, registry, builders, validators, and guides are meant to be
copied: `docs/ADDING-TRANSLATIONS.md` walks a contributor from finding a
public-domain text to seeing it in the column header, and the same path
adds a language — German, Spanish, French, Polish, all of which have
public-domain Commedias on Wikisource — given an Italian→X dictionary of the
FreeDict or Wiktionary kind. The FirstPair framework it rests on
(`github.com/firstpair/firstpair`) carries the language layer, the readers,
and the publisher, and is not Dante-specific: the same machinery serves a
Latin text with Whitaker's WORDS.

We hope students of Italian will read Dante with the dictionary open and
students of Dante will read him with three translations open, and that both
will send us the tenth and eleventh translation.

## Acknowledgements

This work owes a debt to Professor Mark Liberman of the University of
Pennsylvania, a veteran of Bell Labs, who years ago built a pioneering Emacs
reader for studying Spanish that showed the dictionary translation of every
Spanish word. That reader is the origin of the idea here — that the right
tool for reading a foreign text is one in which every word can be asked —
and it is what inspired me to package my Obsidian vault approach as Emacs
again. Texinfo was also my own first hypertext approach to documentation,
in Philadelphia in 1994; it is a pleasure to find, thirty-two years later,
that an Info manual is still a fine way to read a poem.

The texts are the work of their translators and of the volunteers of
Project Gutenberg and Lib.ru/Классика; the dictionaries, of the Wiktionary
and FreeDict communities.

## References

- Dante Alighieri, *La Divina Commedia*, Project Gutenberg 1012.
- H. W. Longfellow (1867), PG 1004; H. F. Cary (1814), PG 8800; C. E. Norton
  (1891–92), PG 1995–1997; J. R. Sibbald (1884), PG 41537.
- Д. Е. Мин, *Божественная комедия* (1855, 1902, 1904); Д. Д. Минаев (1874–79);
  В. А. Петров (1887); А. П. Фёдоров (1898); В. В. Чуйко (1894) — Lib.ru/Классика.
- Kaikki.org Wiktionary extractions (Wiktextract); FreeDict ita-eng and
  ita-rus 2025.11.23.
- FirstPair: `publishing/emacs/EMACS-DELIVERY.md`,
  `publishing/skills/obsidian-reader-plugin-delivery.md`.
- This repository: `docs/LANGUAGE-PIPELINE-REPORT.md`, `docs/ADDING-TRANSLATIONS.md`.
