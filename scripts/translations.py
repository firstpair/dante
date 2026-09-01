#!/usr/bin/env python3
"""The translations of the Commedia this edition knows, their parsers, and alignment.

A translation is registered once, with the language it is in, who made it,
how it is shaped (verse line for line with Dante, verse of its own length,
or prose), and which editions may carry it. The builder aligns every
translation to the Italian tercets with the strategy its shape needs:

* ``line``          — the translator kept Dante's line count (Longfellow, Min,
                      Sibbald): tercet i takes lines 3i..3i+2.
* ``proportional``  — verse of a different length (Cary): the translation's
                      lines are cut at the same fractions as the tercets.
* ``prose``         — prose (Norton): sentences are distributed by their share
                      of the canto's characters.

Only ``line`` alignment asserts that a row shows the same verses; the other
two are approximate and are labelled so wherever they are shown.

To add a translation: put its source under ``sources/raw`` (see
``fetch_sources.py``), write a parser returning ``{(cantica, canto): lines}``
(lines for verse, paragraphs for prose), and append a ``Translation`` below.
``docs/ADDING-TRANSLATIONS.md`` walks through it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "sources" / "raw"
CANTICA = {"inferno": ("Inferno", 34), "purgatorio": ("Purgatorio", 33), "paradiso": ("Paradiso", 33)}
ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def roman(value: str) -> int:
    total = 0; previous = 0
    for character in reversed(value.upper()):
        current = ROMAN_VALUES[character]; total += -current if current < previous else current; previous = max(previous, current)
    return total


def gutenberg_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig")
    start = text.find("*** START OF THE PROJECT GUTENBERG EBOOK"); end = text.find("*** END OF THE PROJECT GUTENBERG EBOOK")
    if start < 0 or end < 0: raise RuntimeError(f"{path.name}: not a Project Gutenberg text")
    return text[text.index("\n", start) + 1:end]


# --- parsers -----------------------------------------------------------------

ITALIAN_HEADER = re.compile(r"^(Inferno|Purgatorio|Paradiso)\s+•\s+Canto\s+([IVXLCDM]+)$", re.I)
LONGFELLOW_HEADER = re.compile(r"^(Inferno|Purgatorio|Paradiso):\s+Canto\s+([IVXLCDM]+)$", re.I)
LAST_LINES = {"l’amor che move il sole e l’altre stelle.", "The Love which moves the sun and the other stars."}


def parse_gutenberg(path: Path, pattern: re.Pattern) -> dict[tuple[str, int], list[str]]:
    """Longfellow's and the Italian layout: a canto header line, then one verse per line."""

    result: dict[tuple[str, int], list[str]] = {}; current = None
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip(); match = pattern.match(line)
        if match:
            current = (match.group(1).casefold(), roman(match.group(2))); result[current] = []; continue
        if current and line.startswith("*** END OF THE PROJECT GUTENBERG"): current = None
        elif current and line.casefold() in CANTICA: current = None
        elif current and line:
            normalized = " ".join(line.split()); result[current].append(normalized)
            if normalized in LAST_LINES: current = None
    check_cantos(path.name, result)
    return result


def parse_cary(path: Path) -> dict[tuple[str, int], list[str]]:
    """Cary's blank verse (Gutenberg 8800): HELL / PURGATORY / PARADISE, then CANTO N and verse lines."""

    parts = {"HELL": "inferno", "PURGATORY": "purgatorio", "PARADISE": "paradiso"}
    result: dict[tuple[str, int], list[str]] = {}; cantica = None; canto = None
    for raw in gutenberg_body(path).splitlines():
        line = raw.strip()
        if line in parts and (canto is None or canto >= 33):
            cantica = parts[line]; canto = None; continue
        match = re.match(r"^CANTO ([IVXL]+)$", line)
        if match and cantica:
            canto = roman(match.group(1)); result[(cantica, canto)] = []; continue
        if cantica and canto and line: result[(cantica, canto)].append(" ".join(line.split()))
    check_cantos(path.name, result)
    return result


NOTE_MARK = re.compile(r"\[\d+\]")


def parse_norton(paths: tuple[Path, Path, Path]) -> dict[tuple[str, int], list[str]]:
    """Norton's prose (Gutenberg 1995–1997): per canto an argument paragraph, prose paragraphs, bracketed footnotes."""

    result: dict[tuple[str, int], list[str]] = {}
    for cantica, path in zip(CANTICA, paths, strict=True):
        body = gutenberg_body(path)
        # The table of contents repeats every canto header with its argument; the text is the second run.
        positions = [m.start() for m in re.finditer(r"^CANTO ([IVXL]+)\.$", body, re.M)]
        headers = [(m.start(), roman(m.group(1))) for m in re.finditer(r"^CANTO ([IVXL]+)\.$", body, re.M)]
        text_start = next(start for start, number in headers if number == 1 and start != positions[0])
        text_headers = [(start, number) for start, number in headers if start >= text_start]
        for index, (start, number) in enumerate(text_headers):
            end = text_headers[index + 1][0] if index + 1 < len(text_headers) else len(body)
            paragraphs = [" ".join(p.split()) for p in re.split(r"\n\s*\n", body[start:end]) if p.strip()]
            paragraphs = paragraphs[1:]  # the CANTO header itself
            if paragraphs: paragraphs = paragraphs[1:]  # the argument
            prose = [NOTE_MARK.sub("", p) for p in paragraphs if not re.match(r"^\[\d+\]", p)]
            prose = [p for p in prose if p and not p.isupper()]
            result[(cantica, number)] = prose
    check_cantos("norton", result, minimum=1, maximum=400)
    return result


def parse_sibbald(path: Path) -> dict[tuple[str, int], list[str]]:
    """Sibbald's terza rima Inferno (Gutenberg 41537): margin line numbers and bracketed note markers stripped."""

    body = gutenberg_body(path)
    headers = [(m.start(), roman(m.group(1))) for m in re.finditer(r"^\s*CANTO ([IVXL]+)\.\s*$", body, re.M)]
    text_start = [start for start, number in headers if number == 1][-1]
    text_headers = [(start, number) for start, number in headers if start >= text_start]
    result: dict[tuple[str, int], list[str]] = {}
    for index, (start, number) in enumerate(text_headers):
        end = text_headers[index + 1][0] if index + 1 < len(text_headers) else len(body)
        lines: list[str] = []
        for raw in body[start:end].splitlines()[1:]:
            if re.match(r"^\[\d+\]", raw.strip()): break  # the canto's notes follow its verse
            if not raw.startswith("  ") or not raw.strip(): continue
            line = re.sub(r"\s+\d+\s*$", "", raw)  # margin line number
            lines.append(" ".join(NOTE_MARK.sub("", line).split()))
        result[("inferno", number)] = lines
    check_cantos(path.name, result, expected=34)
    return result


def parse_lozinsky(path: Path) -> dict[tuple[str, int], list[str]]:
    text = path.read_text(encoding="utf-8")
    starts = list(re.finditer(r"<ul><a name=\d+></a><h2>ПЕСНЬ\s+[^<]+</h2></ul>", text))[:100]
    if len(starts) != 100: raise RuntimeError(f"Russian source has {len(starts)} canto headings")
    ordered = []
    for start in starts:
        following = re.search(r"<ul><a name=\d+></a><h2>", text[start.end():])
        end = start.end() + following.start() if following else len(text)
        lines = []
        for raw in text[start.end():end].splitlines():
            match = re.match(r"^\s{10,}(?:\d+\s+)?(\S.*)$", raw)
            if match: lines.append(" ".join(re.sub(r"<[^>]+>", "", match.group(1)).split()))
        ordered.append(lines)
    keys = [(cantica, number) for cantica, (_, count) in CANTICA.items() for number in range(1, count + 1)]
    return dict(zip(keys, ordered, strict=True))


def check_cantos(name: str, result: dict, *, expected: int = 100, minimum: int = 100, maximum: int = 160) -> None:
    if len(result) != expected: raise RuntimeError(f"{name}: expected {expected} cantos, got {len(result)}")
    for key, lines in result.items():
        if not minimum <= len(lines) <= maximum: raise RuntimeError(f"{name} {key}: implausible {len(lines)} lines")


# --- The owner's EPUBs (study edition only) -----------------------------------
#
# Reader-supplied, in-copyright translations are parsed straight from the
# EPUB in ``sources/raw`` (ignored by Git) and registered with the STUDY
# edition set, so no public build can carry them.

import html as _html
import zipfile


CPCL_PAGE = re.compile(r'<div class="page-html[^>]*rel="(\d+)"[^>]*>(.*?)(?=<div class="page-html|</article>)', re.S)
CPCL_PARAGRAPH = re.compile(r'<p class="([^"]+)"[^>]*>(.*?)</p>', re.S)


def _replace_ilyushin_lines(lines: list[str], old: tuple[str, ...], new: tuple[str, ...]) -> None:
    """Apply one reviewed correction to CPCL's OCR-derived line structure."""

    matches = [index for index in range(len(lines) - len(old) + 1) if tuple(lines[index:index + len(old)]) == old]
    if len(matches) != 1: raise RuntimeError(f"Ilyushin OCR correction matched {len(matches)} times: {old!r}")
    index = matches[0]; lines[index:index + len(old)] = new


def parse_ilyushin(path: Path, expected: dict[tuple[str, int], int]) -> dict[tuple[str, int], list[str]]:
    """Ilyushin's complete 2008 edition from the private CPCL study witness.

    The poem is pages 27--508. Its verse is marked as ``strofa`` paragraphs;
    pages 511 onward are commentary. Three reviewed corrections restore line
    breaks where the HTML OCR differs from the facsimile.
    """

    text = path.read_text(encoding="utf-8"); result: dict[tuple[str, int], list[str]] = {}
    parts = {"Ад": "inferno", "Чистилище": "purgatorio", "Рай": "paradiso"}
    cantica = None; canto = 0; current = None
    for page_match in CPCL_PAGE.finditer(text):
        page = int(page_match.group(1))
        if not 27 <= page <= 508: continue
        for css_class, body in CPCL_PARAGRAPH.findall(page_match.group(2)):
            plain = re.sub(r"<br\s*/?>", "\n", body, flags=re.I)
            plain = _html.unescape(re.sub(r"<[^>]+>", "", plain)).replace("\xad", "")
            lines = [" ".join(line.split()).replace("*", "") for line in plain.splitlines() if line.strip()]
            joined = "\n".join(lines)
            if joined in parts:
                cantica = parts[joined]; canto = 0; current = None
            elif css_class.split()[0] == "text" and re.fullmatch(r"Песнь\s+.+", joined, re.I):
                if cantica is None: raise RuntimeError(f"Ilyushin canto heading before cantica on page {page}")
                canto += 1; current = (cantica, canto); result[current] = []
            elif current and css_class.split()[0].startswith("strofa"):
                result[current].extend(lines)

    corrections = {
        ("inferno", 14): (("Катона, с войском шедшего могучим.", "у"), ("Катона, с войском шедшего могучим.",)),
        ("purgatorio", 18): (("Пряма ль, крива ль, — что ж нам в вину", "вменялось?»"), ("Пряма ль, крива ль, — что ж нам в вину вменялось?»",)),
        ("paradiso", 24): (("Вот так и этих хороводов разнообразный танец предстал моим взорам:", "Здесь сдержанно, а там как бы развязно..."),
                            ("Вот так и этих хороводов разно-", "образный танец предстал моим взорам:", "Здесь сдержанно, а там как бы развязно...")),
    }
    for key, (old, new) in corrections.items(): _replace_ilyushin_lines(result[key], old, new)
    check_cantos(path.name, result)
    mismatches = {key: (len(lines), expected[key]) for key, lines in result.items() if len(lines) != expected[key]}
    if mismatches: raise RuntimeError(f"Ilyushin line counts differ from the Italian: {mismatches}")
    return result


def epub_documents(path: Path) -> list[tuple[str, str]]:
    """The EPUB's documents in spine order, as (href, text) with tags turned into line breaks."""

    with zipfile.ZipFile(path) as archive:
        container = archive.read("META-INF/container.xml").decode("utf-8")
        opf_path = re.search(r'full-path="([^"]+)"', container).group(1)
        opf = archive.read(opf_path).decode("utf-8"); base = opf_path.rsplit("/", 1)[0] + "/" if "/" in opf_path else ""
        items = {}
        for tag in re.findall(r"<item [^>]*>", opf):
            identifier = re.search(r'id="([^"]+)"', tag); href = re.search(r'href="([^"]+)"', tag)
            if identifier and href: items[identifier.group(1)] = href.group(1)
        documents = []
        for idref in re.findall(r'<itemref idref="([^"]+)"', opf):
            href = items.get(idref)
            if not href or not href.endswith((".html", ".xhtml")): continue
            documents.append((href, archive.read(base + href).decode("utf-8")))
    return documents


def parse_epub_james(path: Path) -> dict[tuple[str, int], list[str]]:
    """Clive James (2013): one document per canto, headed CANTO n, a line number after every tenth line."""

    cantos: list[list[str]] = []
    for _, document in epub_documents(path):
        text = re.sub(r"<[^>]+>", "\n", document)
        lines = [" ".join(_html.unescape(line).replace("\xa0", " ").split()) for line in text.splitlines()]
        lines = [line for line in lines if line]
        if len(lines) > 2 and lines[0] == "The Divine Comedy" and re.match(r"^CANTO \d+$", lines[1], re.I):
            cantos.append([re.sub(r"\s+\d+$", "", line) for line in lines[2:]])
    keys = [(cantica, n) for cantica, (_, count) in CANTICA.items() for n in range(1, count + 1)]
    if len(cantos) != len(keys): raise RuntimeError(f"{path.name}: {len(cantos)} cantos, need {len(keys)}")
    return dict(zip(keys, cantos, strict=True))


def parse_epub_palma(path: Path) -> dict[tuple[str, int], list[str]]:
    """Michael Palma (2025): Chapter01–Chapter100, one <p class="verse"> or "verse1" per line."""

    documents = dict(epub_documents(path))
    keys = [(cantica, n) for cantica, (_, count) in CANTICA.items() for n in range(1, count + 1)]
    result = {}
    for number, key in enumerate(keys, 1):
        document = next((text for href, text in documents.items() if href.endswith(f"Chapter{number:02d}.xhtml")), None)
        if document is None: raise RuntimeError(f"{path.name}: Chapter{number:02d} missing")
        result[key] = [" ".join(_html.unescape(re.sub(r"<[^>]+>", "", m)).split()) for m in re.findall(r'<p class="verse1?">(.*?)</p>', document, re.S)]
    check_cantos(path.name, result)
    return result


# --- Russian orthography ------------------------------------------------------

PRE_REFORM = str.maketrans({"ѣ": "е", "Ѣ": "Е", "і": "и", "І": "И", "ѳ": "ф", "Ѳ": "Ф", "ѵ": "и", "Ѵ": "И"})


def modernise_russian(line: str) -> str:
    """Pre-1918 spelling to modern by rule: letters, final hard signs, and the adjective endings the reform changed."""

    text = line.translate(PRE_REFORM)
    text = re.sub(r"ъ(?=[\s,.;:!?…)»—\-]|$)", "", text)
    text = re.sub(r"(?<=[а-яё])(аго)\b", "ого", text); text = re.sub(r"(?<=[а-яё])(яго)\b", "его", text)
    text = re.sub(r"(?<=[а-яё])ыя\b", "ые", text); text = re.sub(r"(?<=[а-яё])ія\b", "ие", text)
    text = re.sub(r"\bея\b", "её", text); text = re.sub(r"\bЕя\b", "Её", text)
    text = re.sub(r"\bоне\b", "они", text); text = re.sub(r"\bОне\b", "Они", text)
    text = re.sub(r"\bодне\b", "одни", text); text = re.sub(r"\bОдне\b", "Одни", text)
    return text


# --- alignment ---------------------------------------------------------------

def units_of(source: list[str]) -> list[tuple[int, int]]:
    return [(start, min(start + 3, len(source))) for start in range(0, len(source), 3)]


def align_lines(source: list[str], lines: list[str]) -> list[list[str]]:
    if len(lines) < len(source) - 2: raise RuntimeError(f"line-aligned translation too short: {len(lines)} for {len(source)}")
    padded = lines[:len(source)] + [""] * max(0, len(source) - len(lines))
    return [padded[start:end] for start, end in units_of(source)]


def align_proportional(source: list[str], lines: list[str]) -> list[list[str]]:
    cuts = [round(start * len(lines) / len(source)) for start, _ in units_of(source)] + [len(lines)]
    return [lines[cuts[i]:cuts[i + 1]] for i in range(len(cuts) - 1)]


SENTENCE = re.compile(r"(?<=[.!?…»”’\"])\s+(?=[\"“‘«(A-ZА-ЯЁ])")


def align_prose(source: list[str], paragraphs: list[str]) -> list[list[str]]:
    sentences = [s for p in paragraphs for s in SENTENCE.split(p) if s]
    total = sum(len(s) for s in sentences) or 1
    unit_bounds = units_of(source); cells: list[list[str]] = [[] for _ in unit_bounds]
    consumed = 0
    for sentence in sentences:
        middle = (consumed + len(sentence) / 2) / total * len(source); consumed += len(sentence) + 1
        index = next((i for i, (start, end) in enumerate(unit_bounds) if middle < end), len(unit_bounds) - 1)
        cells[index].append(sentence)
    return [[" ".join(cell)] if cell else [] for cell in cells]


ALIGNERS = {"line": align_lines, "proportional": align_proportional, "prose": align_prose}


# --- registry ----------------------------------------------------------------

@dataclass(frozen=True)
class Translation:
    id: str
    lang: str
    label: str                 # the language as shown in the reader
    translator: str
    title: str                 # translator and date, as shown on the column
    years: str
    form: str                  # verse | prose
    alignment: str             # line | proportional | prose
    editions: frozenset[str]   # which editions may carry it
    default: bool = False      # the language's default translation in its editions
    coverage: tuple[str, ...] = tuple(CANTICA)  # cantiche covered
    rights: str = "public domain"
    orthography: str = ""
    source: str = ""

    def covers(self, cantica: str) -> bool: return cantica in self.coverage


PUBLIC = frozenset({"en", "ru", "study"}); RUSSIAN = frozenset({"ru", "study"}); STUDY = frozenset({"study"})
TRANSLATIONS: tuple[Translation, ...] = (
    Translation("en-longfellow", "en", "English", "Henry Wadsworth Longfellow", "Longfellow (1867)", "1867", "verse", "line", PUBLIC, default=True, source="english-longfellow.txt"),
    Translation("en-cary", "en", "English", "Henry Francis Cary", "Cary (1814)", "1814", "verse", "proportional", PUBLIC, source="english-cary.txt"),
    Translation("en-norton", "en", "English", "Charles Eliot Norton", "Norton (1891, prose)", "1891–1892", "prose", "prose", PUBLIC, source="english-norton-{1,2,3}.txt"),
    Translation("en-sibbald", "en", "English", "James Romanes Sibbald", "Sibbald (1884, Inferno)", "1884", "verse", "line", PUBLIC, coverage=("inferno",), source="english-sibbald-inferno.txt"),
    Translation("ru-min", "ru", "Русский", "Дмитрий Мин", "Мин (1855–1904)", "1855–1904", "verse", "line", RUSSIAN, default=True, orthography="modernised", source="russian-min-*.html"),
    Translation("ru-min-1855", "ru", "Русский", "Дмитрий Мин", "Мин (орфография изданий)", "1855–1904", "verse", "line", RUSSIAN, orthography="original", source="russian-min-*.html"),
    Translation("ru-petrov", "ru", "Русский", "В. А. Петров", "Петров (1887, Ад)", "1887", "verse", "line", RUSSIAN, coverage=("inferno",), orthography="modernised", source="russian-petrov-inferno.html"),
    Translation("ru-fedorov", "ru", "Русский", "А. П. Фёдоров", "Фёдоров (1898, Ад)", "1898", "verse", "line", RUSSIAN, coverage=("inferno",), orthography="modernised", source="russian-fedorov-inferno.html"),
    Translation("ru-chuiko", "ru", "Русский", "В. В. Чуйко", "Чуйко (1894, Ад, проза)", "1894", "prose", "prose", RUSSIAN, coverage=("inferno",), orthography="modernised", source="russian-chuiko-inferno.html"),
    Translation("ru-minaev", "ru", "Русский", "Дмитрий Минаев", "Минаев (1874–1879, Чистилище и Рай)", "1874–1879", "verse", "proportional", RUSSIAN, coverage=("purgatorio", "paradiso"), orthography="modernised", source="russian-minaev-*.html"),
    Translation("ru-lozinsky", "ru", "Русский", "Михаил Лозинский", "Лозинский (1939–1945)", "1939–1945", "verse", "line", STUDY, default=True,
                rights="local study copy; not for publication (see RIGHTS.md)", source="russian-lozinsky.html"),
    Translation("ru-ilyushin", "ru", "Русский", "Александр Илюшин", "Илюшин (2008)", "2008", "verse", "line", STUDY,
                rights="local study copy; not for publication (see RIGHTS.md)", source="russian-ilyushin-2008.html"),
    # The owner's own EPUBs, in copyright: study edition only.
    Translation("en-palma", "en", "English", "Michael Palma", "Palma (2025)", "2025", "verse", "line", STUDY,
                rights="local study copy; not for publication (see RIGHTS.md)", source="english-palma.epub"),
    Translation("en-james", "en", "English", "Clive James", "James (2013)", "2013", "verse", "proportional", STUDY,
                rights="local study copy; not for publication (see RIGHTS.md)", source="english-james.epub"),
)


def load_texts(translations: tuple[Translation, ...], expected: dict[tuple[str, int], int]) -> dict[str, dict[tuple[str, int], list[str]]]:
    """Parse the sources each selected translation needs, once. EXPECTED holds the Italian line count per canto."""

    texts: dict[str, dict] = {}
    wanted = {t.id for t in translations}
    modern = lambda parsed: {key: [modernise_russian(line) for line in lines] for key, lines in parsed.items()}
    if "en-longfellow" in wanted: texts["en-longfellow"] = parse_gutenberg(RAW / "english-longfellow.txt", LONGFELLOW_HEADER)
    if "en-cary" in wanted: texts["en-cary"] = parse_cary(RAW / "english-cary.txt")
    if "en-norton" in wanted: texts["en-norton"] = parse_norton(tuple(RAW / f"english-norton-{n}.txt" for n in (1, 2, 3)))
    if "en-sibbald" in wanted: texts["en-sibbald"] = parse_sibbald(RAW / "english-sibbald-inferno.txt")
    if wanted & {"ru-min", "ru-min-1855"}:
        original = {}
        for cantica in CANTICA: original.update(parse_azlib_numbered(RAW / f"russian-min-{cantica}.html", cantica, expected))
        if "ru-min-1855" in wanted: texts["ru-min-1855"] = original
        if "ru-min" in wanted: texts["ru-min"] = modern(original)
    if "ru-petrov" in wanted: texts["ru-petrov"] = modern(parse_azlib_numbered(RAW / "russian-petrov-inferno.html", "inferno", expected))
    if "ru-fedorov" in wanted: texts["ru-fedorov"] = modern(parse_azlib_numbered(RAW / "russian-fedorov-inferno.html", "inferno", expected))
    if "ru-chuiko" in wanted: texts["ru-chuiko"] = modern(parse_azlib_prose(RAW / "russian-chuiko-inferno.html", "inferno"))
    if "ru-minaev" in wanted:
        parsed = {}
        for cantica in ("purgatorio", "paradiso"): parsed.update(parse_azlib_linenumbered(RAW / f"russian-minaev-{cantica}.html", cantica))
        texts["ru-minaev"] = modern(parsed)
    if "ru-lozinsky" in wanted: texts["ru-lozinsky"] = parse_lozinsky(RAW / "russian-lozinsky.html")
    if "ru-ilyushin" in wanted: texts["ru-ilyushin"] = parse_ilyushin(RAW / "russian-ilyushin-2008.html", expected)
    if "en-palma" in wanted: texts["en-palma"] = parse_epub_palma(RAW / "english-palma.epub")
    if "en-james" in wanted: texts["en-james"] = parse_epub_james(RAW / "english-james.epub")
    return texts


def selected(edition: str) -> tuple[Translation, ...]:
    return tuple(t for t in TRANSLATIONS if edition in t.editions)


def describe(translation: Translation, default_visible: bool) -> dict:
    row = {"id": translation.id, "lang": translation.lang, "label": translation.label, "translator": translation.translator,
           "title": translation.title, "years": translation.years, "form": translation.form, "alignment": translation.alignment,
           "coverage": list(translation.coverage), "rights": translation.rights, "default": translation.default, "defaultVisible": default_visible}
    if translation.orthography: row["orthography"] = translation.orthography
    return row


# --- az.lib.ru (Lib.ru/Классика) old-orthography editions ---------------------
#
# The Russian nineteenth-century translations are transcribed there in their
# original spelling, Windows-1251 encoded, one <dd> per line. Canto headings
# are centred paragraphs (roman or ordinal), sometimes with OCR slips in the
# numeral, so cantos are taken in order of appearance. Verse lines carry the
# tercet number in front (Min, Petrov, Fedorov) or the line number behind
# (Minaev, Min's Paradiso); commentary follows each canto.

import html as _html

ORDINALS = {"ПЕРВАЯ": 1, "ВТОРАЯ": 2, "ТРЕТЬЯ": 3, "ЧЕТВЕРТАЯ": 4, "ПЯТАЯ": 5, "ШЕСТАЯ": 6, "СЕДЬМАЯ": 7, "ВОСЬМАЯ": 8, "ДЕВЯТАЯ": 9, "ДЕСЯТАЯ": 10,
            "ОДИННАДЦАТАЯ": 11, "ДВѢНАДЦАТАЯ": 12, "ТРИНАДЦАТАЯ": 13, "ЧЕТЫРНАДЦАТАЯ": 14, "ПЯТНАДЦАТАЯ": 15, "ШЕСТНАДЦАТАЯ": 16, "СЕМНАДЦАТАЯ": 17,
            "ВОСЕМНАДЦАТАЯ": 18, "ДЕВЯТНАДЦАТАЯ": 19, "ДВАДЦАТАЯ": 20, "ДВАДЦАТЬ ПЕРВАЯ": 21, "ДВАДЦАТЬ ВТОРАЯ": 22, "ДВАДЦАТЬ ТРЕТЬЯ": 23,
            "ДВАДЦАТЬ ЧЕТВЕРТАЯ": 24, "ДВАДЦАТЬ ПЯТАЯ": 25, "ДВАДЦАТЬ ШЕСТАЯ": 26, "ДВАДЦАТЬ СЕДЬМАЯ": 27, "ДВАДЦАТЬ ВОСЬМАЯ": 28, "ДВАДЦАТЬ ДЕВЯТАЯ": 29,
            "ТРИДЦАТАЯ": 30, "ТРИДЦАТЬ ПЕРВАЯ": 31, "ТРИДЦАТЬ ВТОРАЯ": 32, "ТРИДЦАТЬ ТРЕТЬЯ": 33, "ТРИДЦАТЬ ЧЕТВЕРТАЯ": 34}
# Headings survive OCR and entity slips: ПѢСНЬ, ПѣСНЯ, П122;СНЬ (a broken &#1122;).
AZ_HEADER = re.compile(r"^\s*П(?:Ѣ|ѣ|Е|е|122;)СН[ЬЯья]\s+(?:[IVXL]+|[А-ЯѢѣа-я -]+?)\s*[.:]?\s*$")


def azlib_lines(path: Path) -> list[str]:
    data = path.read_bytes()
    try: raw = data.decode("utf-8")
    except UnicodeDecodeError: raw = data.decode("cp1251", "replace")
    raw = _html.unescape(raw)
    body = raw[raw.find("<body"):] if "<body" in raw else raw
    body = re.sub(r"<script.*?</script>|<!--.*?-->", "", body, flags=re.S)
    body = re.sub(r"<sup>.*?</sup>", "", body, flags=re.S)
    body = re.sub(r"<(?:dd|p|br|/p|div)[^>]*>", "\n", body)
    return [" ".join(line.split()) for line in re.sub(r"<[^>]+>", "", body).splitlines()]


def azlib_headed(lines: list[str], count: int, *, last: bool = False) -> list[list[str]]:
    """Split into cantos at the headings, taking the first (or last) COUNT headings in order."""

    positions = [i for i, line in enumerate(lines) if AZ_HEADER.match(line)]
    if len(positions) < count: raise RuntimeError(f"found {len(positions)} canto headings, need {count}")
    positions = positions[-count:] if last else positions[:count]
    bounds = positions + [len(lines)]
    return [lines[bounds[i] + 1:bounds[i + 1]] for i in range(count)]


VERSE_NUMBER_FRONT = re.compile(r"^(\d+)[.)]?\s+(.*)$")
VERSE_NUMBER_BACK = re.compile(r"^(.*?)\s+(\d+)\s*$")


ARGUMENT = re.compile(r"^(Содержан|СОДЕРЖАН)|\.\s*--|\.--|\.—")
COMMENT_RANGE = re.compile(r"^\d+\s*--\s*\d+[.)]")


def azlib_verse(chunk: list[str], target: int) -> list[str]:
    """The canto's verse: after the argument, up to TARGET lines, stopping where the commentary begins.

    Verse lines carry a tercet number in front or a line number behind; the
    commentary that follows the canto is numbered too, but by the lines it
    explains, so its first number falls below the last verse number.
    """

    lines: list[str] = []; started = False; last_number = 0
    for line in chunk:
        if not line or (line.isupper() and len(line) > 3): continue  # section headings such as ПРИМѢЧАНІЯ
        if not started:
            # The argument precedes the verse: a long prose line, or one marked as such.
            if line.startswith(("Содержан", "СОДЕРЖАН")) or len(line) > 70: continue
            started = True
        if COMMENT_RANGE.match(line): break
        front = VERSE_NUMBER_FRONT.match(line); back = VERSE_NUMBER_BACK.match(line)
        number = int(front.group(1)) if front else (int(back.group(2)) if back and back.group(2).isdigit() and len(back.group(2)) <= 3 else 0)
        # Commentary is prose: a numbered line far longer than any verse opens it.
        if number and len(line) > 95: break
        if number: last_number = number
        text = front.group(2) if front else (back.group(1) if number else line)
        text = " ".join(re.sub(r"\)\s", " ", text).replace(" )", "").split()).strip()
        if text: lines.append(text)
        if len(lines) >= target: break
    return lines


def parse_azlib_numbered(path: Path, cantica: str, expected: dict[tuple[str, int], int], *, last: bool = False) -> dict[tuple[str, int], list[str]]:
    """Editions with headings and tercet or line numbers, kept to Dante's line count (Min, Petrov, Fedorov)."""

    count = CANTICA[cantica][1]; result = {}
    for number, chunk in enumerate(azlib_headed(azlib_lines(path), count, last=last), 1):
        target = expected[(cantica, number)]; lines = azlib_verse(chunk, target)
        if len(lines) < target * 0.7: raise RuntimeError(f"{path.name} {cantica} {number}: {len(lines)} lines, Italian has {target}")
        # A transcription may lack a few lines; the gap is left blank rather than shifting the alignment.
        result[(cantica, number)] = lines + [""] * (target - len(lines))
    return result


def parse_azlib_prose(path: Path, cantica: str, *, last: bool = True) -> dict[tuple[str, int], list[str]]:
    """Prose editions with headings (Chuiko): the paragraphs after the argument, notes left out."""

    count = CANTICA[cantica][1]; result = {}
    for number, chunk in enumerate(azlib_headed(azlib_lines(path), count, last=last), 1):
        paragraphs = [p for p in chunk if p and not p.startswith(")") and not re.match(r"^\d+\)", p)]
        paragraphs = [" ".join(re.sub(r"\s\)", "", p).split()) for p in paragraphs[1:]]  # the first paragraph is the argument
        result[(cantica, number)] = [p for p in paragraphs if p]
    return result


def parse_azlib_linenumbered(path: Path, cantica: str) -> dict[tuple[str, int], list[str]]:
    """Editions without headings but with a line number after every third line (Minaev).

    A number n names the n-th line of its canto, so it and the two lines
    before it are lines n-2..n; the numbering restarting at 3 opens the next
    canto; the one or two lines after the last multiple of three, before the
    notes, close it.
    """

    lines = azlib_lines(path); cantos: list[list[str]] = []; current: dict[int, str] = {}; previous_number = 0; recent: list[str] = []
    clean = lambda text: " ".join(text.replace(" )", "").split())
    def close():
        if current: cantos.append([current.get(k, "") for k in range(1, max(current) + 1)])
    for line in lines:
        if not line: continue
        back = VERSE_NUMBER_BACK.match(line)
        number = int(back.group(2)) if back and back.group(2).isdigit() and len(back.group(2)) <= 3 and len(line) < 95 else 0
        # A number is trusted when it opens a canto (3, or 6/9/12 when the OCR
        # lost the 3) or continues the count by a few tercets; any other number
        # is an OCR slip on an ordinary line.
        opens = number in (3, 6, 9, 12) and (not current or previous_number > 60)
        continues = bool(number and current and not opens and 0 < number - previous_number <= 12 and (number - previous_number) % 3 == 0)
        if opens or continues:
            if opens: close(); current = {}; previous_number = 0
            gap = number - previous_number
            for offset, earlier in enumerate(reversed(recent[-(gap - 1):] if gap > 1 else []), 1):
                current.setdefault(number - offset, clean(earlier))
            current[number] = clean(back.group(1)); previous_number = number; recent = []
            continue
        if line.startswith(")") or re.match(r"^\d+\)", line):
            # Notes: the lines still in RECENT that follow the last numbered line close the canto.
            if current and recent and previous_number:
                for offset, later in enumerate(recent[:2], 1): current[previous_number + offset] = clean(later)
                previous_number += min(2, len(recent))
            recent = []; continue
        recent.append(line)
    close()
    keys = [(cantica, n) for n in range(1, CANTICA[cantica][1] + 1)]
    if len(cantos) < len(keys): raise RuntimeError(f"{path.name}: reconstructed {len(cantos)} cantos, need {len(keys)}")
    return dict(zip(keys, cantos[:len(keys)], strict=True))
