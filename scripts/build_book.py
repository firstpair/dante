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
from build_vault import CANTICA, ENGLISH_HEADER, ITALIAN_HEADER, RAW, ROOT, VERSION, parse_gutenberg  # noqa: E402

ROMAN = ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII",
         "XIX", "XX", "XXI", "XXII", "XXIII", "XXIV", "XXV", "XXVI", "XXVII", "XXVIII", "XXIX", "XXX", "XXXI", "XXXII", "XXXIII", "XXXIV")
PARTS = {
    "inferno": "Thirty-four cantos: the descent through the nine circles, from the dark wood on the night before Good Friday to the frozen centre of the earth.",
    "purgatorio": "Thirty-three cantos: the mountain of seven terraces rising from the southern ocean to the Earthly Paradise, where Beatrice takes Virgil's place.",
    "paradiso": "Thirty-three cantos: the ascent through the spheres to the Empyrean and the vision of the Love that moves the sun and the other stars.",
}
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
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "book" / "build" / "firstpair" / "commedia.md"
    italian = parse_gutenberg(RAW / "italian.txt", ITALIAN_HEADER)
    english = parse_gutenberg(RAW / "english.txt", ENGLISH_HEADER)
    out = ["---", 'title: "La Divina Commedia"', f'version: "{VERSION}"', "---", "", ABOUT.strip(), ""]
    tercets = 0
    for cantica, (label, count) in CANTICA.items():
        out += [f"# {label} {{.part .unnumbered}}", "", PARTS[cantica], ""]
        for canto in range(1, count + 1):
            source = italian[(cantica, canto)]; en = english[(cantica, canto)][: len(source)]
            if len(en) < len(source): raise RuntimeError(f"{label} {canto}: Italian {len(source)} lines, English {len(en)}")
            out += [f"# {label} · Canto {ROMAN[canto]} {{#{cantica}-{canto:02d}}}", ""]
            for start in range(0, len(source), 3):
                out += [f'::: {{.tercet data-line="{start + 1}"}}', "::: {.it}", line_block(source[start:start + 3]), ":::",
                        "::: {.en}", line_block(en[start:start + 3]), ":::", ":::", ""]
                tercets += 1
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{output}: 100 cantos, {tercets} tercets")


if __name__ == "__main__":
    main()
