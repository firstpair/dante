# Dante for learners of Italian: the language pipeline, the vault, and the Emacs edition

*Report of 2026-08-29. Dante commits `71a4cf9` … `a3adc53`; FirstPair commits `1afb2b4` … `14b1dc9`.*

## Purpose

This triptych exists so that a reader who knows Russian, English, or both can
learn Italian from the *Commedia*. Three requirements followed from that:
the Italian must come first, every Italian word must open an explanation the
reader can trust, and the two readers — the Obsidian vault and the Emacs Info
edition — must say the same thing about the same word. This report records
what was found, what was changed, the measured result, and what remains.

## What was found

**Column order.** The shared FirstPair Reader placed the source text last, so
the vault showed English, Russian, Italian. For a learner the original must
lead.

**Dictionary wiring.** The drawer was wired correctly but its data was poor.
The FreeDict `ita-eng` and `ita-rus` entries carried Wiktionary's
Italian-language definition notes after the one-word gloss, which is why an
English lookup showed one English word followed by Italian text. Worse,
FreeDict is a list of translation pairs keyed by lemma, not a dictionary: it
lacks even *a, in, il, è, più, senza, grande, fuori, loro*.

**Coverage.** Measured by exact headword over the vault's own text — 97,208
tokens, 13,603 distinct word types — FreeDict explained **17.9 % of the
types (43 % of tokens) in English and 12.8 % (36 %) in Russian**. The misses
were systematic, not random: elisions (`ch’io`, `l’altre`), apocope (`amor`,
`cammin`, `fuor`), archaic inflection (`dicea`, `avean`, `saria`), old
spellings (`sanza`, `elli`, `etterna`), enclitic pronouns (`dirmi`,
`mostrommi`), and the Gutenberg text's diaereses (`sapïenza`). A larger word
list alone would not have fixed this; morphology was required.

## What was built

### An Italian analyser in FirstPair

`publishing/emacs/firstpair_emacs/languages/italian.py` reads the English
Wiktionary extraction published by Kaikki (762 MB, pinned by digest in
`publishing/emacs/lexicon/italian/SOURCES.json`, cached once under
`~/.cache/firstpair/lexicon/italian/`): 152k lemmas, 806k inflected forms,
444k form-of links, English senses. On top of the dictionary it applies an
ordered list of restorations that each name what they did, so the reader is
told *apocope of amore*, *old form of diceva*, *elision of il*,
*mostrò + mi*, *written sapïenza* rather than given a silent guess:

- elided articles and clitics (`l’`, `ch’`, `d’`, `’l`, `’n`, `’nferno`);
- Dante's usual truncations and spellings (`sanza`, `elli`, `om`, `fuoro`,
  `fue`, `puote`, `disio`);
- apocope (`amor` → `amore`, `agnel` → `agnello`) and paragoge (`giùe` → `giù`);
- old verb endings (`-ea/-ia` → `-eva/-iva`, `-ean` → `-evano`, `-ria` →
  `-rebbe`, `-aro` → `-arono`) and old noun endings (`-ate/-ade` → `-à`);
- enclitic pronouns, including the doubled consonant after a stressed vowel
  (`mostrommi` = `mostrò` + `mi`);
- Tuscan spelling alternations checked against the dictionary (`etterna` →
  `eterna`, `move` → `muove`, `maravigliar` → `meravigliare`), a prothetic
  `i-` (`iscorta`), and Wiktionary's stress marks in conjugation tables
  (`hò`, `avére`), which are indexed both as written and unaccented.

Two data quirks mattered: form-of targets are sometimes phrases (`"avere and
(obsolete) havere"`, `"in il"`, `"third-person … of potere"`) and need
parsing; and links must be followed twice (`etterna → etterno → eterno`).
Suffix, prefix, and abbreviation entries are excluded so that `ïo` does not
resolve to the suffix *-io* and `ch’` to *Chieti*.

A reviewed supplement, `sources/dictionaries/italian-supplement.json`
(60 forms, English side) with its Russian twin, covers the frequent residue
the extraction lacks (`subitamente`, `dichina`, `sappiendo`, `folgór`,
`dicerò`, `evangelio` …). The mechanism is general: any title may declare
`emacs.lexicon.supplement`.

### One projection for both readers

`firstpair_emacs.dictionaries.project` takes a language, a text's
vocabulary, and a target language's sources, and returns a dictionary in the
shared `firstpair-reader-dictionary-v1` schema keyed by surface form — the
payload the Obsidian Reader's drawer loads and the data the Emacs builder
projects into `lexicon/glosses.tsv`. The vault's `_data/dictionaries/*.json`
and the bundle's tables therefore come from the same analyser and the same
sources: the two readers agree word for word.

Russian is drawn from four pinned glossaries, consulted in order, plus
FreeDict and the supplement:

1. Russian Wiktionary's Italian entries (Kaikki, 17k lemmas);
2. Italian Wiktionary's own translation tables into Russian (1.9k entries
   carry one);
3. Russian Wiktionary's Russian entries, inverted: every Italian word named
   in a translation table becomes a headword glossed by that Russian entry
   (76k rows carry tables, 24.8k distinct Italian cells);
4. a pivot through English Wiktionary's sense-level translation tables
   (3.2 GB): an Italian word listed for an English sense is glossed by the
   Russian words listed for the same sense, and the gloss names the sense it
   passed through — *насторо́женный, осторо́жный (wary: cautious of danger…)*.

Each scanned dump is cached as a small derived index keyed by its digest, so
the multi-gigabyte extractions are read once.

A **second pass** runs only where those direct sources give nothing, and
labels what it did: first the dictionary's own pointers — an entry's synonyms
and alternative forms, so *gaetta* → *gaietto* → *gaio* → *весёлый* is glossed
"via gaio"; then a pivot through the words of the entry's own English senses
against English Wiktionary's Russian tables, so *accismare* ("to adorn, to
deck out") is glossed *украшать (via English: adorn, to make more beautiful)*.
Names are excluded from the second pass. Wiktionary often writes a link only
as gloss text ("Dantesque form of gaietto"); such glosses are parsed into
links too, so *gaetta* reaches *gaietto* — "spotted, speckled",
*запятнанный* via *maculato* — and the inflection table of a linked entry
resolves through the link.

### The vault

`scripts/build_vault.py` now leads with Italian (the shared Reader leads with
the source column unless a title declares `sourceLanguage.position:
"right"`), declares the translations as `[ru, en]` — Russian in the middle
when both are on, either one beside the Italian when one is — keeps only
FreeDict's translations (not its Italian notes), builds both dictionaries
through the shared projection, and writes `vault.build.json` for the Emacs
edition and `sources/dictionaries/coverage.json`. The Reader also treats an
elided article as its own word, so `l’altre` offers *l’* and *altre*
separately.

### The Emacs edition

Reader pages are the vault's own chapter files in the shared
`firstpair-aligned-chapter-v1` schema. Each canto is one node; each tercet
renders as the Italian lines, then English, then Russian; `data/regions.tsv`
records the lines of every language, and `C-c C-t` cycles English, Русский,
both — hiding the other translation in place, so the Italian never moves.
Any Italian word answers to `C-c C-d`. The glossary of 20,020 entries splits
by initial letter. The bundle (`dist/Dante-Emacs`, 41 MB unpacked, 4.7 MB
zipped) validates: 134 nodes, every reference resolves, every lexicon check
passes.

Build order, from the repository root:

```sh
./scripts/uv run python scripts/fetch_sources.py
~/src/firstpair/publishing/scripts/firstpair-emacs lexicon --language italian
./scripts/uv run python scripts/build_vault.py dist/Dante-Multilingual-Vault
./scripts/uv run python scripts/check_vault.py dist/Dante-Multilingual-Vault
~/src/firstpair/publishing/scripts/firstpair-emacs build vault.build.json --product desktop
~/src/firstpair/publishing/scripts/firstpair-emacs validate --bundle dist/Dante-Emacs
```

## Measured result

Over the Commedia's 101,604 Italian tokens and 12,766 normalised word types:

| | Before (FreeDict, exact headword) | After |
| --- | --- | --- |
| Forms analysed to a headword with grammar | — | 11,921 of 12,766 types (93.4%), 98.9 % of tokens |
| English explanation | 2,436 types (17.9 %) | all 11,921 analysed forms |
| Russian explanation, direct sources | 1,745 types (12.8 %) | 9,591 of 11,882 analysed forms (80.7 %) |
| Russian explanation, with the labelled second pass | — | 11,412 of 11,921 analysed forms (95.7%); 6,799 entries derived and labelled |
| Vault dictionary entries | 28,245 / 13,529 (lemma-keyed, mostly unreachable) | 12,189 / 9,813 (form-keyed) |

The gap analysis in `sources/dictionaries/coverage.json` is honest by
construction: the analyser never fills a hole with a guess.

## What remains

- **845 unanalysed forms** (6.6% of types, about 1 % of tokens): hapax
  archaisms and proper names the extraction lacks — *Acheronte, Averroè,
  Bonagiunta* — which have neither English nor Russian. They belong in the
  reviewed supplement; the frequent ones are already there.
- **509 analysed forms without Russian**, behind 245 proper-name lemmas and
  241 common lemmas whose English senses are phrases the gloss pivot cannot
  safely reduce to a word. The remaining path is
  `italian-russian-supplement.json`, lemma by lemma from `coverage.json`. A
  proper name wants a transliteration rather than a translation, and the
  aligned Russian tercet already stands beside every Italian line.
- **Rights.** Lozinsky's Russian is public domain in Russia since 1 January
  2026 but of unsettled US status: the vault and the bundle stay local study
  copies until the review in `RIGHTS.md`. `fetch_sources.py` also knows the
  public-domain Dmitry Min translation on Wikisource, unused so far.

## Generalization in FirstPair

The work lives in FirstPair so that Cicero and Dante extend one library:
`firstpair_emacs.languages` (one contract — folding rule shipped as data,
analyser, projection, tables — with Latin served by Whitaker's WORDS and
Italian by Wiktionary), `firstpair_emacs.dictionaries` (the shared
projection), `firstpair_emacs.glosses` (four glossary kinds with a derived
cache), aligned chapters as reader pages with `data/regions.tsv`, and reader
1.6, which also italicises Info's `_emphasis_`, since Emacs's Info reader
shows the underscores literally. Cicero was rebuilt and validated on the
refactored Latin path. The contract is in
`publishing/emacs/EMACS-DELIVERY.md`; the workflow in
`publishing/skills/emacs-info-bundle.md`.
