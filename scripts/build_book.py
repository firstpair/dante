#!/usr/bin/env python3
"""Write the aligned Italian–English manuscript for the unified FirstPair builder.

Reads the same Project Gutenberg sources as the vault build and emits Pandoc
Markdown: one chapter per canto, every tercet as a ``.tercet`` div holding an
Italian and an English line block. ``book/aligned.lua`` turns those divs into
Typst grids; ``book/epub.css`` lays them out as columns in HTML and EPUB.
"""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_vault import ROOT, VERSION  # noqa: E402
import translations as T  # noqa: E402
CANTICA, RAW = T.CANTICA, T.RAW
BOOKS = {
    # edition -> (translation id, translation label for the page, right-column language)
    "en": ("en-longfellow", "Henry Wadsworth Longfellow's English", "en"),
    "ru": ("ru-min", "Dmitry Min's Russian", "ru"),
}

ROMAN = ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII",
         "XIX", "XX", "XXI", "XXII", "XXIII", "XXIV", "XXV", "XXVI", "XXVII", "XXVIII", "XXIX", "XXX", "XXXI", "XXXII", "XXXIII", "XXXIV")
PARTS = {
    "inferno": "Thirty-four cantos: the descent through the nine circles, from the dark wood on the night before Good Friday to the frozen centre of the earth.",
    "purgatorio": "Thirty-three cantos: the mountain of seven terraces rising from the southern ocean to the Earthly Paradise, where Beatrice takes Virgil's place.",
    "paradiso": "Thirty-three cantos: the ascent through the spheres to the Empyrean and the vision of the Love that moves the sun and the other stars.",
}
ABOUT_RU = """# About this edition {.unnumbered}

This is the complete *Commedia* — Inferno, Purgatorio, and Paradiso — with
Dante's Italian on the left of every tercet and Dmitry Min's Russian on the
right. Min (1818–1885) translated the poem in Dante's own metre, line for
line, between 1855 and his death; the Purgatorio and Paradiso appeared
posthumously in 1902 and 1904. His spelling has been modernised by rule from
the pre-1918 orthography of those editions. The alignment is structural: line
by line within each canto, three lines to a row, so a reader learning
Italian can always find the Russian for the verse in front of them.

Both texts are in the public domain. The Italian is Project Gutenberg ebook
1012; Min's translation is transcribed by Lib.ru/Классика from the 1855, 1902
and 1904 editions. The small numbers in the margin count the lines of each
canto.

The same edition is available from First Pair Press as an Obsidian vault and
as an Emacs Info bundle, both with four English and five Russian translations
that can stand beside the Italian, and a dictionary that analyses every
Italian word — elisions, truncations, and Dante's old spellings restored to
their modern headword — with English and Russian senses.
"""
ABOUT = """# About this edition {.unnumbered}

This is the complete *Commedia* — Inferno, Purgatorio, and Paradiso — with
Dante's Italian on the left of every tercet and Henry Wadsworth Longfellow's
English on the right. The alignment is structural: line by line within each
canto, three lines to a row, so a reader learning Italian can always find the
English for the verse in front of them. It does not assert word-for-word
equivalence, and Longfellow's line order occasionally differs from Dante's
within a tercet.

Both texts are in the public domain. The Italian is Project Gutenberg ebook
1012; Longfellow's translation (1867) is Project Gutenberg ebook 1004. The
small numbers in the margin count the lines of each canto.

The same edition is available from First Pair Press as an Obsidian vault and
as an Emacs Info bundle. Both add what a printed page cannot: select any
Italian word and the reader analyses its form — elisions, truncations, and
Dante's old spellings restored to their modern headword — and shows the
English senses, with usage examples from the poem itself.
"""


def escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("*", "\\*").replace("_", "\\_").replace("[", "\\[").replace("]", "\\]").replace("<", "\\<").replace("#", "\\#")


def line_block(lines: list[str]) -> str:
    return "\n".join(f"| {escape(line)}" for line in lines)


def main() -> None:
    edition = sys.argv[1] if len(sys.argv) > 1 else "en"
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "book" / "build" / "firstpair" / f"commedia-{edition}.md"
    translation_id, credit, lang = BOOKS[edition]
    italian = T.parse_gutenberg(RAW / "italian.txt", T.ITALIAN_HEADER)
    expected = {key: len(lines) for key, lines in italian.items()}
    translation = next(t for t in T.TRANSLATIONS if t.id == translation_id)
    english = T.load_texts((translation,), expected)[translation_id]
    about = ABOUT if edition == "en" else ABOUT_RU
    out = ["---", 'title: "La Divina Commedia"', f'version: "{VERSION}"', "---", "", about.strip(), ""]
    tercets = 0
    for cantica, (label, count) in CANTICA.items():
        out += [f"# {label} {{.part .unnumbered}}", "", PARTS[cantica], ""]
        for canto in range(1, count + 1):
            source = italian[(cantica, canto)]; en = english[(cantica, canto)][: len(source)]
            if len(en) < len(source): en = en + [""] * (len(source) - len(en))
            out += [f"# {label} · Canto {ROMAN[canto]} {{#{cantica}-{canto:02d}}}", ""]
            for start in range(0, len(source), 3):
                out += [f'::: {{.tercet data-line="{start + 1}"}}', "::: {.it}", line_block(source[start:start + 3]), ":::",
                        f"::: {{.{lang}}}", line_block(en[start:start + 3]), ":::", ":::", ""]
                tercets += 1
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{output}: 100 cantos, {tercets} tercets")


if __name__ == "__main__":
    main()
