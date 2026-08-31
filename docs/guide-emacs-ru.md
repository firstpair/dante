Each canto is one node. Every tercet appears in Italian first, then in the
translations you have chosen — Longfellow's English and Min's Russian by
default; `C-c C-v` rotates a language's column through its translations
(Cary, Norton, Sibbald; Petrov, Fedorov, Chuiko, Minaev, Min in the spelling
of his editions), and `C-c C-b` shows a second translation of the same
language under the first. `C-c C-t`
hides and restores the translations in place, so the Italian never moves;
translations that do not keep Dante's line count are marked ≈ in the column
header.

Put point on any Italian word and press `C-c C-d`: the compact dictionary
starts with one bold Italian headword, then shows up to two English and two
Russian senses, one unwrapped line each, from the Wiktionaries and FreeDict.
Press `RET` in the poem to advance to the next Italian word and open it with
the current dictionary languages. `m` or **More** reveals any remaining
senses and **Less** folds them again. A form the edition cannot explain is
reported as such, never guessed.

Both texts are public domain (Project Gutenberg ebooks 1012 and 1004); the
license notices are in `evidence/` beside the Texinfo source.
