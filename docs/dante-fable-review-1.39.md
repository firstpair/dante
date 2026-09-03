# FirstPair Emacs Reader 1.39 — Fable's Review

*Written 2026-09-02, before the Fable 5.1 update. Reader package 1.39
(`firstpair-reader-1.39`), FirstPair `a06038f`, Dante `4b45bbc`, 1Unix
`081ea2ba`. Study bundle: `dante-commedia-study-emacs (1.0.0-4b45bbc5).zip`.*

## Disposition

Reader 1.41 restores this checkbox model after Reader 1.40 briefly and
incorrectly returned to primary/second slots. The approved small state is one
ordered list of checked editions per language plus one language-order list:
selecting an unchecked edition adds it, selecting a checked edition removes
it, and the header controls ordering. Reader 1.41 also migrates a 1.40
primary/second pair into two checked editions. The obsolete **2nd** control is
removed from the 1Unix strip.

## What the reader is now

A phone-first parallel-text reading machine built on stock Info. The book is
an indirect Info manual (subfiles of ~250 KB, so a canto opens in ~0.15 s
where the 9.1 MB monolith took minutes on iSH); the reading surface is three
bars plus a header row; the dictionary is a compact two-senses-per-language
pane with `m` for more; and translations are now fully elastic:

- **Per-language ordered selections** (`firstpair-reader-translation-selections`)
  replaced the old primary/second slot pair. Any number of editions of a
  language can be on screen; `firstpair-reader-language-order` orders the
  language blocks themselves.
- **Tr-Eng / Tr-Rus menus are checkboxes** (None stays a radio that hides the
  language). Checking adds, unchecking removes, removing the last hides the
  language, and choosing an edition of a hidden language restores it.
- **The header row is the control surface**: ` EN Longfellow ◀Cary | RU Мин ` —
  tap a name to hide it, ◀ to move it earlier in its language, EN/RU to bring
  that block first. The 2nd button is gone; `b` adds one more edition or
  collapses to one.
- **Reordering is physical.** Each tercet's translation blocks are permuted
  bodily in the Info buffer. The Italian lines never move, so marked-word
  positions from `marked.tsv` stay exact; blocks must be separated by single
  blank lines or the unit is left untouched. Region rows come from a
  buffer-local cache (`firstpair-reader--regions`) that tracks the moved
  lines and is invalidated by advice on `Info-insert-file-contents` whenever
  Info re-reads pristine bytes.

## The Codex line of work (1.17–1.38), reviewed

Strong throughout. The compact dictionary (1.17) is the right phone shape;
lemma-true glosses cut the homograph noise at both build time
(`_matching_entry_items`, `PART_PRIORITY`) and read time
(`--rank-glosses`, with the `via …` pivot escape preserving
Russian-through-English); Return navigation (1.18) with the three-way guard
(role, source node, link-at-point) is careful; the borrowed-window trick for
tiny frames is elegant. The stale-package fix (`package-installed-p` at ≥ the
bundle's version in `init.el`) closes the exact shadowing bug class we hit on
iSH. The persistent-navigation contract (1.37–1.38) co-designed with 1Unix —
atomic DECSET 1003 taps at the touch-down cell, a native key strip bypassing
mouse decoding, capture-phase suppression of WebKit compatibility events — is
the reason touch works at all.

Coverage trade from the stricter gloss filter: Russian covered 11,412 →
11,410 (*fabi*, *ostiense* lost) against derived entries 1,954 → 2,368 and
corrected name restorations (Alberigo, Ruggieri/Rubicante/Rusticucci). Good
trade.

## Risks and watch items

1. **The buffer rewrite is the sharpest tool in the box.** Its safety rests on
   two invariants: single-blank-line separation between blocks (checked per
   unit, mismatches skipped) and cache invalidation on every pristine re-read
   (the `Info-insert-file-contents` advice). A path that mutates node text
   without that function would desynchronize line numbers. None is known.
2. **`format-mode-line` is inert in batch Emacs** — returns "" always. Tests
   flatten header lists themselves; don't chase ghost failures there.
3. **Gloss ranking keys off the first reading's entry** in
   `firstpair-lexicon-definitions`; a wrong top homograph could filter
   compatible form glosses. `PART_PRIORITY` mitigates; watch for user reports
   of missing senses.
4. **1Unix strip label**: resolved in build 822 by removing the obsolete
   `2nd` button. The `b` keyboard command remains available for "one more /
   back to one," while the native strip matches the checkbox-first UI.
5. **Version numbering across agents.** The 1.39 release was first shipped
   mislabeled 1.20 because Codex commits in the same worktree had taken the
   headers to 1.38 mid-refactor. Fixed (release deleted, 1.39 cut, sha256
   sidecar regenerated). Rule going forward: reread the Version headers and
   `git log` immediately before `firstpair-emacs package`.

## Test posture

30 tests green, including the rewritten terminal-menu test (checkbox
toggling, in-language reorder with buffer-order proof, language-block order,
marks surviving reorder, one-shot TTY feedback) and the indirect-subfile
test (Emacs opens a node straight from a subfile). Validation of the study
bundle: 132 nodes, no unresolved references, no lexicon failures, manifest
bound to `4b45bbc`.

## Outstanding

- **Public English and Russian Emacs bundles are still the old builds**
  (`5ca23ea`): monolithic Info, pre-split, pre-1.17 dictionary, old loader.
  Republishing both versions through `library:publish --emacs` is the big
  pending item.
- Phone check of the header row as a tap surface (row 2: tap a name → the
  edition disappears and tercets re-flow).
- Physical phone acceptance of Reader 1.41 and 1Unix build 822 after both are
  installed together.
