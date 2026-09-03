Each canto is one node. Every tercet appears in Italian first, then in the
English translation you have chosen — Longfellow by default; `C-c C-v`
rotates the column through Cary, Norton, and (in the Inferno) Sibbald, and
`C-c C-b` shows a second English translation under the first. `C-c C-t`
hides and restores the translations in place, so the Italian never moves;
translations that do not keep Dante's line count are marked ≈ in the column
header. The edition line beneath the top bar reports what is visible; it does
not remove or reorder translations.

Put point on any Italian word and press `C-c C-d`: the compact dictionary
starts with one bold Italian headword, then shows up to two English senses,
one unwrapped line each, from the English Wiktionary and FreeDict. Press `RET`
in the poem to advance to the next Italian word and open it with the current
dictionary language. `m` or **More** reveals any remaining senses and **Less**
folds them again. A form the edition cannot explain is reported as such, never
guessed.

Both texts are public domain (Project Gutenberg ebooks 1012 and 1004); the
license notices are in `evidence/` beside the Texinfo source.
