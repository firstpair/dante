#!/usr/bin/env python3
"""Build the complete offline Dante Obsidian vault and the Emacs build config.

The vault's dictionaries and the Emacs bundle's are projected by the shared
FirstPair language layer from the same sources, so both readers tell a
learner the same thing about every word of the Commedia.

Two editions are built from one script, selected by ``--translations``:

* ``en`` (default): the public Italian–English edition — Gutenberg's Italian
  beside Longfellow, both public domain. It writes ``vault.build.json``, the
  configuration the FirstPair publisher reads.
* ``en,ru``: the local study copy that adds Lozinsky's Russian and the
  Russian dictionaries. It writes ``vault.build.study.json`` and refreshes
  ``sources/dictionaries/coverage.json``. Never publish it (see RIGHTS.md).
"""

from __future__ import annotations

import argparse
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
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
EMACS_SUPPLEMENT = "sources/dictionaries/italian-supplement.json"
RUSSIAN_SUPPLEMENT = "sources/dictionaries/italian-russian-supplement.json"
# Russian glossaries pinned by FirstPair, direct dictionaries before the English-sense pivot.
RUSSIAN_GLOSSARIES = ("ruwiktionary-italian", "itwiktionary-italian-translations", "ruwiktionary-russian-translations", "enwiktionary-english-pivot", "enwiktionary-english-glosses")
LANGUAGES = {"en": {"lang": "en", "label": "English"}, "ru": {"lang": "ru", "label": "Русский"}}
EDITIONS = {
    # translations -> (build config, Emacs bundle output, vault guide fragment, Emacs guide fragment)
    ("en",): ("vault.build.json", "dist/Dante Commedia Emacs", "docs/guide-vault.md", "docs/guide-emacs.md"),
    ("en", "ru"): ("vault.build.study.json", "dist/Dante-Emacs", "docs/guide-vault-study.md", "docs/guide-emacs-study.md"),
}


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


def emacs_config(pages: list[dict[str, str]], vault_output: str, translations: tuple[str, ...]) -> dict:
    _, emacs_output, vault_guide, emacs_guide = EDITIONS[translations]
    lexicon_translations = [{"id": "en", "label": "English", "dictionary": "dist/dictionaries/it-en-freedict.json"}]
    if "ru" in translations:
        lexicon_translations.append({"id": "ru", "label": "Русский", "glossary": list(RUSSIAN_GLOSSARIES),
                                     "dictionary": "dist/dictionaries/it-ru-freedict.json", "supplement": RUSSIAN_SUPPLEMENT})
    with_russian = "ru" in translations
    return {
        "$schema": "https://firstpair.org/schemas/vault.build.schema.json",
        "schemaVersion": 1,
        "slug": "dante-commedia",
        "title": "Dante — La Divina Commedia",
        "profile": "triptych",
        "sourceCommit": "HEAD",
        "plugin": True,
        "guide": {"bookSpecific": vault_guide},
        "reader": [
            {"id": page["id"], "title": page["title"], "source": f"{vault_output}/{page['path']}", "part": page["part"]}
            for page in pages
        ],
        "products": {"desktop": {"output": vault_output, "edition": "full"}},
        "emacs": {
            "guide": {"bookSpecific": emacs_guide},
            "direntry": {"category": "Books", "name": "dante-commedia",
                         "description": "Dante's Commedia with English and Russian, aligned tercet by tercet." if with_russian
                         else "Dante's Commedia with Longfellow's English, aligned tercet by tercet."},
            "subtitle": "La Divina Commedia, with Longfellow and Lozinsky" if with_russian else "La Divina Commedia, with Longfellow's English",
            "author": "Dante Alighieri",
            "parts": [
                {"title": "Inferno", "description": "Thirty-four cantos: the descent."},
                {"title": "Purgatorio", "description": "Thirty-three cantos: the mountain."},
                {"title": "Paradiso", "description": "Thirty-three cantos: the spheres."},
            ],
            "lexicon": {
                "language": "italian", "mode": "projected", "sourceId": "it", "minimumLength": 3,
                "supplement": EMACS_SUPPLEMENT,
                "translations": lexicon_translations,
            },
            "records": [],
            "products": {"desktop": {"output": emacs_output, "edition": "full", "maxFiles": 400, "maxBytes": 200000000}},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("output", type=Path)
    parser.add_argument("--translations", default="en", help="comma-separated translation ids: en (public) or en,ru (local study copy)")
    args = parser.parse_args()
    translations = tuple(dict.fromkeys(item.strip() for item in args.translations.split(",") if item.strip()))
    if translations not in EDITIONS: raise SystemExit(f"unsupported translations {args.translations!r}; use en or en,ru")
    with_russian = "ru" in translations
    config_name = EDITIONS[translations][0]
    output = args.output.resolve()
    if output.exists(): raise SystemExit(f"refusing to replace existing output: {output}")
    required = ["italian.txt", "english.txt", "ita-eng.tei"] + (["russian-lozinsky.html", "ita-rus.tei"] if with_russian else [])
    missing = [name for name in required if not (RAW / name).is_file()]
    if missing: raise SystemExit(f"fetch sources first; missing: {', '.join(missing)}")
    italian = parse_gutenberg(RAW / "italian.txt", ITALIAN_HEADER)
    english = parse_gutenberg(RAW / "english.txt", ENGLISH_HEADER)
    russian = parse_russian() if with_russian else None

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
            key = (cantica, canto); source = italian[key]; en = english[key]
            if len(en) < len(source): raise RuntimeError(f"{label} {canto}: Italian {len(source)} != English {len(en)}")
            en = en[:len(source)]; ru = []
            if with_russian:
                ru = russian[key]
                if len(source) - len(ru) > 2: raise RuntimeError(f"{label} {canto}: Italian {len(source)} != Russian {len(ru)}")
                ru = ru[:len(source)] + [""] * max(0, len(source) - len(ru))
            slug = f"{cantica}-{canto:02d}"; units = []
            for start in range(0, len(source), 3):
                unit_translations = {"en": en[start:start + 3]}
                if with_russian: unit_translations = {"ru": ru[start:start + 3], **unit_translations}
                units.append({"id": f"{slug}-lines-{start + 1:03d}-{min(start + 3, len(source)):03d}", "source": source[start:start + 3], "translations": unit_translations})
            for line in source:
                for _, surface in language.tokens(line):
                    vocabulary.append(surface)
                    key_form = fold(surface)
                    if key_form and line not in examples[key_form] and len(examples[key_form]) < 2: examples[key_form].append(line)
            path = f"_data/chapters/{slug}.json"; title = f"{label} — Canto {canto}"
            write_json(output / path, {"schema": "firstpair-aligned-chapter-v1", "id": slug, "title": title, "units": units})
            pages.append({"id": slug, "title": title, "path": path, "part": label})
            report = {"id": slug, "italianLines": len(source), "englishLines": len(en), "units": len(units)}
            if with_russian: report["russianLines"] = len(ru)
            alignment.append(report)

    # Dictionaries: FreeDict by lemma (title-owned), Russian Wiktionary by FirstPair pin, reviewed supplements.
    freedict_dir = ROOT / "dist" / "dictionaries"; freedict_dir.mkdir(parents=True, exist_ok=True)
    freedict = {}
    for pair, target in (("ita-eng", "en"), ("ita-rus", "ru"))[: 2 if with_russian else 1]:
        lemmas = freedict_lemmas(RAW / f"{pair}.tei", fold)
        freedict[target] = lemmas
        write_json(freedict_dir / f"it-{target}-freedict.json", {
            "schema": "firstpair-reader-dictionary-v1", "sourceLanguage": "it", "targetLanguage": target,
            "license": "CC BY-SA 3.0", "attribution": f"FreeDict {pair} {FREEDICT_RELEASE} / WikDict / Wiktionary / DBnary",
            "entries": {key: list(value) for key, value in sorted(lemmas.items())},
        })
    ru_index = None; ru_names = []; ru_ids = []; gloss_pivot = None; gloss_pivot_name = ""
    for identifier in RUSSIAN_GLOSSARIES if with_russian else ():
        item = corpus.glossary(spec, identifier)
        index = glosses.load_glossary(corpus.ensure_glossary(spec, item, allow_download=False), item, fold=fold)
        if item.kind == "gloss-pivot":
            gloss_pivot, gloss_pivot_name = index, item.name
            continue
        ru_index = index if ru_index is None else glosses.merge(ru_index, index)
        ru_names.append(item.name); ru_ids.append(identifier)
    payload_en, report_en = dictionaries.project(
        language, vocabulary, target="en", label="English", license="CC BY-SA 4.0",
        attribution=f"{spec.name}; FreeDict ita-eng {FREEDICT_RELEASE}; usage examples from Dante's Commedia",
        dictionary=freedict["en"], dictionary_name=f"FreeDict ita-eng {FREEDICT_RELEASE}", examples=examples,
    )
    dictionaries.write_sharded(payload_en, data / "dictionaries" / "it-en")
    coverage = {"schema": "dante-dictionary-coverage-v2", "italianForms": report_en["forms"], "analysed": report_en["analysed"],
                "english": {"covered": report_en["covered"], "missing": report_en["missing"]}, "unanalysed": report_en["unanalysed"]}
    payload_ru = None; report_ru = {"covered": 0, "missing": []}; names: dict[str, list[str]] = {}; common: dict[str, list[str]] = {}
    if with_russian:
        ru_supplement = glosses.load_supplement(ROOT / RUSSIAN_SUPPLEMENT, fold=fold)
        payload_ru, report_ru = dictionaries.project(
            language, vocabulary, target="ru", label="Русский", license="CC BY-SA 4.0",
            attribution=f"{'; '.join(ru_names)}; FreeDict ita-rus {FREEDICT_RELEASE}; First Pair reviewed supplement",
            glossary=ru_index, glossary_name=", ".join(ru_ids), dictionary=freedict["ru"], dictionary_name=f"FreeDict ita-rus {FREEDICT_RELEASE}",
            supplement=ru_supplement, supplement_name="First Pair reviewed Russian supplement", examples=examples,
            gloss_pivot=gloss_pivot, gloss_pivot_name="enwiktionary-english-glosses",
        )
        dictionaries.write_sharded(payload_ru, data / "dictionaries" / "it-ru")
        # Russian gaps by lemma, names apart: a proper name is explained by its
        # English entry and wants a transliteration, not a translation.
        names = defaultdict(list); common = defaultdict(list)
        for form in report_ru["missing"]:
            analyses = language.analyse(form)
            if not analyses: continue
            entry = language.entry(analyses[0].entry_id)
            (names if entry.part == "name" or entry.headword[:1].isupper() else common)[entry.headword].append(form)
        coverage["russian"] = {"covered": report_ru["covered"], "derivedEntries": report_ru.get("derivedEntries", 0), "missing": report_ru["missing"],
                               "missingLemmas": {"names": dict(sorted(names.items())), "common": dict(sorted(common.items()))}}
        (ROOT / "sources" / "dictionaries" / "coverage.json").write_text(json.dumps(coverage, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    write_json(data / "dictionaries" / "coverage.json", coverage)

    write_json(data / "parallel-reader.json", {
        "schema": "firstpair-parallel-reader-v1", "title": "Dante — Commedia", "unit": "tercet",
        "sourceLanguage": {"id": "it", "lang": "it", "label": "Italiano", "position": "left"},
        "translations": [{"id": code, **LANGUAGES[code], "defaultVisible": True} for code in (("ru", "en") if with_russian else ("en",))],
        "dictionaries": {code: {"path": f"_data/dictionaries/it-{code}/index.json"} for code in translations}, "pages": pages,
    })
    write_json(data / "reader.json", pages); write_json(data / "alignment-report.json", alignment); write_json(data / "targets.json", [])
    toc = ["# Dante — La Divina Commedia", "", "**[Open the Reader](firstpair:reader)** — or use the book icon in the ribbon, or the *Open Reader* command. Every canto below opens in the Reader.", "",
           ("Italian is always the leftmost column. With both translations on, Russian stands in the middle and English on the right; with one, it stands beside the Italian."
            if with_russian else "Italian stands on the left and Longfellow's English on the right; select any Italian word to open its dictionary entry."), ""]
    for cantica, (label, count) in CANTICA.items():
        toc.extend([f"## {label}", ""] + [f"- [{label} — Canto {number}](firstpair:page:{cantica}-{number:02d})" for number in range(1, count + 1)] + [""])
    (output / "Home.md").write_text("\n".join(toc), encoding="utf-8")
    (output / "Reader").mkdir(); (output / "Reader" / "About the alignment.md").write_text((ROOT / EDITIONS[translations][2]).read_text(encoding="utf-8"), encoding="utf-8")
    sources = output / "Sources"; sources.mkdir()
    shutil.copy2(ROOT / "RIGHTS.md", sources / "RIGHTS.md"); shutil.copy2(ROOT / "sources" / "PROVENANCE.json", sources / "PROVENANCE.json")
    for name in ["italian.txt", "english.txt", "ita-eng-COPYING.txt"] + (["russian-lozinsky.html", "ita-rus-COPYING.txt"] if with_russian else []): shutil.copy2(RAW / name, sources / name)
    obsidian = output / ".obsidian"; (obsidian / "plugins").mkdir(parents=True)
    shutil.copytree(FIRSTPAIR_PLUGIN, obsidian / "plugins" / "firstpair-reader")
    write_json(obsidian / "community-plugins.json", ["firstpair-reader"]); write_json(obsidian / "core-plugins.json", ["file-explorer", "search", "bookmarks", "outline"])
    files = sorted(str(path.relative_to(output)) for path in output.rglob("*") if path.is_file())
    digest = hashlib.sha256("\n".join(f"{path} {hashlib.sha256((output / path).read_bytes()).hexdigest()}" for path in files).encode()).hexdigest()
    write_json(output / "VAULT-MANIFEST.json", {"schema": "dante-multilingual-vault-v1", "version": VERSION, "cantos": 100, "alignmentUnit": "tercet",
        "languages": ["it"] + (["ru", "en"] if with_russian else ["en"]),
        "dictionaryEntries": {f"it-{code}": len(payload["entries"]) for code, payload in (("en", payload_en), ("ru", payload_ru)) if payload},
        "coverage": {k: coverage[k] for k in ("italianForms", "analysed")}, "files": len(files), "payloadDigest": digest})
    config_path = ROOT / config_name
    config_path.write_text(json.dumps(emacs_config(pages, str(output.relative_to(ROOT)) if output.is_relative_to(ROOT) else str(output), translations), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"vault": str(output), "config": config_name, "translations": list(translations), "cantos": 100, "italianForms": report_en["forms"], "analysed": report_en["analysed"],
                      "englishCovered": report_en["covered"], "russianCovered": report_ru["covered"],
                      "unanalysed": len(report_en["unanalysed"]), "russianMissing": len(report_ru["missing"]),
                      "russianMissingLemmas": {"names": len(names), "common": len(common)}}, ensure_ascii=False))


if __name__ == "__main__": main()
