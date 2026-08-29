#!/usr/bin/env python3
"""Build the complete offline Dante Obsidian vault and the Emacs build config.

The vault's dictionaries and the Emacs bundle's are projected by the shared
FirstPair language layer from the same sources, so both readers tell a
learner the same thing about every word of the Commedia.
"""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import unicodedata
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "sources" / "raw"
FIRSTPAIR = ROOT.parents[0] / "firstpair"
FIRSTPAIR_PLUGIN = FIRSTPAIR / "publishing" / "vault" / "plugin" / "firstpair-reader"
sys.path[:0] = [str(FIRSTPAIR / "publishing" / "emacs"), str(FIRSTPAIR / "publishing" / "vault")]

from firstpair_emacs import corpus, dictionaries, glosses  # noqa: E402
from firstpair_emacs.languages import get as get_language  # noqa: E402

CANTICA = {"inferno": ("Inferno", 34), "purgatorio": ("Purgatorio", 33), "paradiso": ("Paradiso", 33)}
ITALIAN_HEADER = re.compile(r"^(Inferno|Purgatorio|Paradiso)\s+•\s+Canto\s+([IVXLCDM]+)$", re.I)
ENGLISH_HEADER = re.compile(r"^(Inferno|Purgatorio|Paradiso):\s+Canto\s+([IVXLCDM]+)$", re.I)
NS = {"tei": "http://www.tei-c.org/ns/1.0"}
FREEDICT_RELEASE = "2025.11.23"
EMACS_SUPPLEMENT = "sources/dictionaries/italian-supplement.json"
RUSSIAN_SUPPLEMENT = "sources/dictionaries/italian-russian-supplement.json"


def roman(value: str) -> int:
    numbers = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0; previous = 0
    for character in reversed(value.upper()):
        current = numbers[character]; total += -current if current < previous else current; previous = max(previous, current)
    return total


def parse_gutenberg(path: Path, pattern: re.Pattern) -> dict[tuple[str, int], list[str]]:
    result: dict[tuple[str, int], list[str]] = {}; current = None
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip(); match = pattern.match(line)
        if match:
            current = (match.group(1).casefold(), roman(match.group(2))); result[current] = []; continue
        if current and line.startswith("*** END OF THE PROJECT GUTENBERG"): current = None
        elif current and line:
            normalized = " ".join(line.split()); result[current].append(normalized)
            if normalized in {"l’amor che move il sole e l’altre stelle.", "The Love which moves the sun and the other stars."}: current = None
    if len(result) != 100: raise RuntimeError(f"{path.name}: expected 100 cantos, got {len(result)}")
    for key, lines in result.items():
        if not 100 <= len(lines) <= 160: raise RuntimeError(f"{path.name} {key}: implausible {len(lines)} lines")
    return result


def parse_russian() -> dict[tuple[str, int], list[str]]:
    text = (RAW / "russian-lozinsky.html").read_text(encoding="utf-8")
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


def freedict_lemmas(path: Path, fold) -> dict[str, tuple[dict[str, object], ...]]:
    """FreeDict translations keyed by normalised lemma, in the shared dictionary shape.

    Only the translations are kept; the Italian-language definition notes that
    follow them in the TEI are not translations and are left out.
    """

    root = ET.parse(path).getroot(); entries: dict[str, list[dict[str, object]]] = defaultdict(list)
    for node in root.findall(".//tei:entry", NS):
        orth = node.findtext("tei:form/tei:orth", default="", namespaces=NS).strip()
        if not orth: continue
        pos = node.findtext("tei:gramGrp/tei:pos", default="", namespaces=NS).strip()
        translations = []
        for quote in node.findall(".//tei:cit[@type='trans']/tei:quote", NS):
            value = " ".join("".join(quote.itertext()).split())
            if value and value not in translations: translations.append(value)
        if translations:
            entries[fold(orth)].append({"headword": orth, "partOfSpeech": pos, "definitions": translations})
    return {key: tuple(value) for key, value in entries.items()}


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def emacs_config(pages: list[dict[str, str]], vault_output: str) -> dict:
    return {
        "$schema": "https://firstpair.org/schemas/vault.build.schema.json",
        "schemaVersion": 1,
        "slug": "dante-commedia",
        "title": "Dante — La Divina Commedia",
        "profile": "triptych",
        "sourceCommit": "HEAD",
        "plugin": True,
        "guide": {"bookSpecific": "guide-emacs.md"},
        "reader": [
            {"id": page["id"], "title": page["title"], "source": f"{vault_output}/{page['path']}", "part": page["part"]}
            for page in pages
        ],
        "products": {"desktop": {"output": vault_output, "edition": "full"}},
        "emacs": {
            "direntry": {"category": "Books", "name": "dante-commedia", "description": "Dante's Commedia with English and Russian, aligned tercet by tercet."},
            "subtitle": "La Divina Commedia, with Longfellow and Lozinsky",
            "author": "Dante Alighieri",
            "parts": [
                {"title": "Inferno", "description": "Thirty-four cantos: the descent."},
                {"title": "Purgatorio", "description": "Thirty-three cantos: the mountain."},
                {"title": "Paradiso", "description": "Thirty-three cantos: the spheres."},
            ],
            "lexicon": {
                "language": "italian", "mode": "projected", "sourceId": "it", "minimumLength": 3,
                "supplement": EMACS_SUPPLEMENT,
                "translations": [
                    {"id": "en", "label": "English", "dictionary": "dist/dictionaries/it-en-freedict.json"},
                    {"id": "ru", "label": "Русский", "glossary": ["ruwiktionary-italian", "ruwiktionary-russian-translations"],
                     "dictionary": "dist/dictionaries/it-ru-freedict.json", "supplement": RUSSIAN_SUPPLEMENT},
                ],
            },
            "records": [],
            "products": {"desktop": {"output": "dist/Dante-Emacs", "edition": "full", "maxFiles": 400, "maxBytes": 200000000}},
        },
    }


def main() -> None:
    if len(sys.argv) != 2: raise SystemExit("usage: build_vault.py OUTPUT")
    output = Path(sys.argv[1]).resolve()
    if output.exists(): raise SystemExit(f"refusing to replace existing output: {output}")
    required = ("italian.txt", "english.txt", "russian-lozinsky.html", "ita-eng.tei", "ita-rus.tei")
    missing = [name for name in required if not (RAW / name).is_file()]
    if missing: raise SystemExit(f"fetch sources first; missing: {', '.join(missing)}")
    italian = parse_gutenberg(RAW / "italian.txt", ITALIAN_HEADER)
    english = parse_gutenberg(RAW / "english.txt", ENGLISH_HEADER)
    russian = parse_russian()

    # The shared Italian analyser, pinned by FirstPair, plus this edition's reviewed supplement.
    spec = corpus.load_corpus("italian")
    cache = corpus.ensure(spec, allow_download=False)
    language = get_language("italian")
    language.load(cache, (ROOT / EMACS_SUPPLEMENT,))
    fold = language.normalise

    output.mkdir(parents=True); data = output / "_data"; chapters = data / "chapters"; chapters.mkdir(parents=True)
    pages = []; alignment = []; vocabulary: list[str] = []; examples: dict[str, list[str]] = defaultdict(list)
    for cantica, (label, count) in CANTICA.items():
        for canto in range(1, count + 1):
            key = (cantica, canto); source = italian[key]; en = english[key]; ru = russian[key]
            if len(en) < len(source): raise RuntimeError(f"{label} {canto}: Italian {len(source)} != English {len(en)}")
            en = en[:len(source)]
            if len(source) - len(ru) > 2: raise RuntimeError(f"{label} {canto}: Italian {len(source)} != Russian {len(ru)}")
            ru = ru[:len(source)] + [""] * max(0, len(source) - len(ru))
            slug = f"{cantica}-{canto:02d}"; units = []
            for start in range(0, max(len(source), len(ru)), 3):
                units.append({"id": f"{slug}-lines-{start + 1:03d}-{min(start + 3, len(source)):03d}", "source": source[start:start + 3], "translations": {"ru": ru[start:start + 3], "en": en[start:start + 3]}})
            for line in source:
                for _, surface in language.tokens(line):
                    vocabulary.append(surface)
                    key_form = fold(surface)
                    if key_form and line not in examples[key_form] and len(examples[key_form]) < 2: examples[key_form].append(line)
            path = f"_data/chapters/{slug}.json"; title = f"{label} — Canto {canto}"
            write_json(output / path, {"schema": "firstpair-aligned-chapter-v1", "id": slug, "title": title, "units": units})
            pages.append({"id": slug, "title": title, "path": path, "part": label})
            alignment.append({"id": slug, "italianLines": len(source), "englishLines": len(en), "russianLines": len(ru), "units": len(units)})

    # Dictionaries: FreeDict by lemma (title-owned), Russian Wiktionary by FirstPair pin, reviewed supplements.
    freedict_dir = ROOT / "dist" / "dictionaries"; freedict_dir.mkdir(parents=True, exist_ok=True)
    freedict = {}
    for pair, target in (("ita-eng", "en"), ("ita-rus", "ru")):
        lemmas = freedict_lemmas(RAW / f"{pair}.tei", fold)
        freedict[target] = lemmas
        write_json(freedict_dir / f"it-{target}-freedict.json", {
            "schema": "firstpair-reader-dictionary-v1", "sourceLanguage": "it", "targetLanguage": target,
            "license": "CC BY-SA 3.0", "attribution": f"FreeDict {pair} {FREEDICT_RELEASE} / WikDict / Wiktionary / DBnary",
            "entries": {key: list(value) for key, value in sorted(lemmas.items())},
        })
    ru_index = None; ru_names = []
    for identifier in ("ruwiktionary-italian", "ruwiktionary-russian-translations"):
        item = corpus.glossary(spec, identifier)
        index = glosses.load_glossary(corpus.ensure_glossary(spec, item, allow_download=False), item, fold=fold)
        ru_index = index if ru_index is None else glosses.merge(ru_index, index)
        ru_names.append(item.name)
    ru_supplement = glosses.load_supplement(ROOT / RUSSIAN_SUPPLEMENT, fold=fold)
    payload_en, report_en = dictionaries.project(
        language, vocabulary, target="en", label="English", license="CC BY-SA 4.0",
        attribution=f"{spec.name}; FreeDict ita-eng {FREEDICT_RELEASE}; usage examples from Dante's Commedia",
        dictionary=freedict["en"], dictionary_name=f"FreeDict ita-eng {FREEDICT_RELEASE}", examples=examples,
    )
    payload_ru, report_ru = dictionaries.project(
        language, vocabulary, target="ru", label="Русский", license="CC BY-SA 4.0",
        attribution=f"{'; '.join(ru_names)}; FreeDict ita-rus {FREEDICT_RELEASE}; First Pair reviewed supplement",
        glossary=ru_index, glossary_name="; ".join(ru_names), dictionary=freedict["ru"], dictionary_name=f"FreeDict ita-rus {FREEDICT_RELEASE}",
        supplement=ru_supplement, supplement_name="First Pair reviewed Russian supplement", examples=examples,
    )
    write_json(data / "dictionaries" / "it-en.json", payload_en)
    write_json(data / "dictionaries" / "it-ru.json", payload_ru)
    coverage = {"schema": "dante-dictionary-coverage-v1", "italianForms": report_en["forms"], "analysed": report_en["analysed"],
                "english": {"covered": report_en["covered"], "missing": report_en["missing"]},
                "russian": {"covered": report_ru["covered"], "missing": report_ru["missing"]},
                "unanalysed": report_en["unanalysed"]}
    write_json(data / "dictionaries" / "coverage.json", coverage)
    (ROOT / "sources" / "dictionaries" / "coverage.json").write_text(json.dumps(coverage, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    write_json(data / "parallel-reader.json", {
        "schema": "firstpair-parallel-reader-v1", "title": "Dante — Commedia", "unit": "tercet",
        "sourceLanguage": {"id": "it", "lang": "it", "label": "Italiano", "position": "left"},
        "translations": [{"id": "ru", "lang": "ru", "label": "Русский", "defaultVisible": True}, {"id": "en", "lang": "en", "label": "English", "defaultVisible": True}],
        "dictionaries": {"en": {"path": "_data/dictionaries/it-en.json"}, "ru": {"path": "_data/dictionaries/it-ru.json"}}, "pages": pages,
    })
    write_json(data / "reader.json", pages); write_json(data / "alignment-report.json", alignment); write_json(data / "targets.json", [])
    toc = ["# Dante — La Divina Commedia", "", "Open **FirstPair Reader** from the ribbon or command palette.", "",
           "Italian is always the leftmost column. With both translations on, Russian stands in the middle and English on the right; with one, it stands beside the Italian.", ""]
    for cantica, (label, count) in CANTICA.items():
        toc.extend([f"## {label}", ""] + [f"- {label} — Canto {number}" for number in range(1, count + 1)] + [""])
    (output / "Home.md").write_text("\n".join(toc), encoding="utf-8")
    (output / "Reader").mkdir(); (output / "Reader" / "About the alignment.md").write_text((ROOT / "guide.md").read_text(encoding="utf-8"), encoding="utf-8")
    sources = output / "Sources"; sources.mkdir()
    shutil.copy2(ROOT / "RIGHTS.md", sources / "RIGHTS.md"); shutil.copy2(ROOT / "sources" / "PROVENANCE.json", sources / "PROVENANCE.json")
    for name in ("italian.txt", "english.txt", "russian-lozinsky.html", "ita-eng-COPYING.txt", "ita-rus-COPYING.txt"): shutil.copy2(RAW / name, sources / name)
    obsidian = output / ".obsidian"; (obsidian / "plugins").mkdir(parents=True)
    shutil.copytree(FIRSTPAIR_PLUGIN, obsidian / "plugins" / "firstpair-reader")
    write_json(obsidian / "community-plugins.json", ["firstpair-reader"]); write_json(obsidian / "core-plugins.json", ["file-explorer", "search", "bookmarks", "outline"])
    files = sorted(str(path.relative_to(output)) for path in output.rglob("*") if path.is_file())
    digest = hashlib.sha256("\n".join(f"{path} {hashlib.sha256((output / path).read_bytes()).hexdigest()}" for path in files).encode()).hexdigest()
    write_json(output / "VAULT-MANIFEST.json", {"schema": "dante-multilingual-vault-v1", "cantos": 100, "alignmentUnit": "tercet", "languages": ["it", "ru", "en"],
        "dictionaryEntries": {"it-en": len(payload_en["entries"]), "it-ru": len(payload_ru["entries"])}, "coverage": {k: coverage[k] for k in ("italianForms", "analysed")},
        "files": len(files), "payloadDigest": digest})
    config_path = ROOT / "vault.build.json"
    config_path.write_text(json.dumps(emacs_config(pages, str(output.relative_to(ROOT)) if output.is_relative_to(ROOT) else str(output)), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"vault": str(output), "cantos": 100, "italianForms": report_en["forms"], "analysed": report_en["analysed"],
                      "englishCovered": report_en["covered"], "russianCovered": report_ru["covered"],
                      "unanalysed": len(report_en["unanalysed"]), "russianMissing": len(report_ru["missing"])}, ensure_ascii=False))


if __name__ == "__main__": main()
