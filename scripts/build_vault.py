#!/usr/bin/env python3
"""Build a Dante vault (and the matching Emacs build config) for one edition.

Editions, chosen with ``--edition``:

* ``en``    — Italian with the English translations (Longfellow, Cary, Norton,
              Sibbald), all public domain. Writes ``vault.build.json``.
* ``ru``    — adds the public-domain Russian translations (Min, Petrov,
              Fedorov, Chuiko, Minaev) and the Russian dictionary. Writes
              ``vault.build.russian.json``.
* ``study`` — adds Lozinsky's Russian, a local study copy that is never
              published (see RIGHTS.md). Writes ``vault.build.study.json`` and
              refreshes ``sources/dictionaries/coverage.json``.

Every translation is registered in ``scripts/translations.py`` with its
language, translator, and alignment strategy; the vault's dictionaries and
the Emacs bundle's are projected by the shared FirstPair language layer from
the same sources, so both readers tell a learner the same thing about every
word of the Commedia.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "sources" / "raw"
FIRSTPAIR = ROOT.parents[0] / "firstpair"
FIRSTPAIR_PLUGIN = FIRSTPAIR / "publishing" / "vault" / "plugin" / "firstpair-reader"
sys.path[:0] = [str(ROOT / "scripts"), str(FIRSTPAIR / "publishing" / "emacs"), str(FIRSTPAIR / "publishing" / "vault")]

from firstpair_emacs import corpus, dictionaries, glosses  # noqa: E402
from firstpair_emacs.languages import get as get_language  # noqa: E402
import translations as T  # noqa: E402

CANTICA = T.CANTICA
NS = {"tei": "http://www.tei-c.org/ns/1.0"}
FREEDICT_RELEASE = "2025.11.23"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
EMACS_SUPPLEMENT = "sources/dictionaries/italian-supplement.json"
RUSSIAN_SUPPLEMENT = "sources/dictionaries/italian-russian-supplement.json"
# Russian glossaries pinned by FirstPair, direct dictionaries before the English-sense pivot.
RUSSIAN_GLOSSARIES = ("ruwiktionary-italian", "itwiktionary-italian-translations", "ruwiktionary-russian-translations", "enwiktionary-english-pivot", "enwiktionary-english-glosses")
LANGUAGES = {"en": "English", "ru": "Русский"}
EDITIONS = {
    # edition -> (build config, Emacs bundle output, vault guide fragment, Emacs guide fragment, default Russian translation)
    "en": ("vault.build.json", "dist/Dante Commedia Emacs", "docs/guide-vault-en.md", "docs/guide-emacs-en.md", None),
    "ru": ("vault.build.russian.json", "dist/Dante Commedia Emacs Russian", "docs/guide-vault-ru.md", "docs/guide-emacs-ru.md", "ru-min"),
    "study": ("vault.build.study.json", "dist/Dante-Emacs", "docs/guide-vault-study.md", "docs/guide-emacs-study.md", "ru-lozinsky"),
}
ENGLISH_SOURCES = ("italian.txt", "english-longfellow.txt", "english-cary.txt", "english-norton-1.txt", "english-norton-2.txt", "english-norton-3.txt", "english-sibbald-inferno.txt", "ita-eng-COPYING.txt")
RUSSIAN_SOURCES = ("russian-min-inferno.html", "russian-min-purgatorio.html", "russian-min-paradiso.html", "russian-minaev-purgatorio.html", "russian-minaev-paradiso.html",
                   "russian-petrov-inferno.html", "russian-fedorov-inferno.html", "russian-chuiko-inferno.html", "ita-rus-COPYING.txt")


def freedict_lemmas(path: Path, fold) -> dict[str, tuple[dict[str, object], ...]]:
    """FreeDict translations keyed by normalised lemma, in the shared dictionary shape."""

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


def emacs_config(edition: str, pages: list[dict[str, str]], vault_output: str, languages: list[str]) -> dict:
    config_name, emacs_output, vault_guide, emacs_guide, _ = EDITIONS[edition]
    lexicon_translations = [{"id": "en", "label": "English", "dictionary": "dist/dictionaries/it-en-freedict.json"}]
    if "ru" in languages:
        lexicon_translations.append({"id": "ru", "label": "Русский", "glossary": list(RUSSIAN_GLOSSARIES),
                                     "dictionary": "dist/dictionaries/it-ru-freedict.json", "supplement": RUSSIAN_SUPPLEMENT})
    names = ", ".join(t.translator for t in T.selected(edition))
    return {
        "$schema": "https://firstpair.org/schemas/vault.build.schema.json",
        "schemaVersion": 1,
        "slug": "dante-commedia" if edition == "en" else f"dante-commedia-{'russian' if edition == 'ru' else 'study'}",
        "title": "Dante — La Divina Commedia",
        "profile": "triptych",
        "sourceCommit": "HEAD",
        "plugin": True,
        "guide": {"bookSpecific": vault_guide},
        "reader": [{"id": page["id"], "title": page["title"], "source": f"{vault_output}/{page['path']}", "part": page["part"]} for page in pages],
        "products": {"desktop": {"output": vault_output, "edition": "full"}},
        "emacs": {
            "launcher": "dante.sh",
            "guide": {"bookSpecific": emacs_guide},
            "direntry": {"category": "Books", "name": "dante-commedia", "description": f"Dante's Commedia aligned tercet by tercet with its translations: {names}."},
            "subtitle": "La Divina Commedia, with its translations",
            "author": "Dante Alighieri",
            "parts": [
                {"title": "Inferno", "description": "Thirty-four cantos: the descent."},
                {"title": "Purgatorio", "description": "Thirty-three cantos: the mountain."},
                {"title": "Paradiso", "description": "Thirty-three cantos: the spheres."},
            ],
            "aligned": {"index": f"{vault_output}/_data/parallel-reader.json"},
            "lexicon": {"language": "italian", "mode": "projected", "sourceId": "it", "minimumLength": 3, "supplement": EMACS_SUPPLEMENT, "translations": lexicon_translations},
            "records": [],
            "products": {"desktop": {"output": emacs_output, "edition": "full", "maxFiles": 400, "maxBytes": 400000000}},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("output", type=Path)
    parser.add_argument("--edition", choices=tuple(EDITIONS), default="en")
    args = parser.parse_args()
    edition = args.edition; config_name, _, vault_guide, _, russian_default = EDITIONS[edition]
    output = args.output.resolve()
    if output.exists(): raise SystemExit(f"refusing to replace existing output: {output}")
    chosen = T.selected(edition); languages = list(dict.fromkeys(t.lang for t in chosen))
    with_russian = "ru" in languages
    required = list(ENGLISH_SOURCES) + ["ita-eng.tei"] + ((list(RUSSIAN_SOURCES) + ["ita-rus.tei"]) if with_russian else []) + (["russian-lozinsky.html", "english-palma.epub", "english-james.epub"] if edition == "study" else [])
    missing = [name for name in required if not (RAW / name).is_file()]
    if missing: raise SystemExit(f"fetch sources first; missing: {', '.join(missing)}")
    italian = T.parse_gutenberg(RAW / "italian.txt", T.ITALIAN_HEADER)
    expected = {key: len(lines) for key, lines in italian.items()}
    texts = T.load_texts(chosen, expected)

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
            key = (cantica, canto); source = italian[key]
            aligned = {t.id: T.ALIGNERS[t.alignment](source, texts[t.id][key]) for t in chosen if t.covers(cantica) and key in texts[t.id]}
            slug = f"{cantica}-{canto:02d}"; units = []
            for index, (start, end) in enumerate(T.units_of(source)):
                units.append({"id": f"{slug}-lines-{start + 1:03d}-{end:03d}", "source": source[start:end],
                              "translations": {identifier: cells[index] for identifier, cells in aligned.items()}})
            for line in source:
                for _, surface in language.tokens(line):
                    vocabulary.append(surface)
                    key_form = fold(surface)
                    if key_form and line not in examples[key_form] and len(examples[key_form]) < 2: examples[key_form].append(line)
            path = f"_data/chapters/{slug}.json"; title = f"{label} — Canto {canto}"
            write_json(output / path, {"schema": "firstpair-aligned-chapter-v1", "id": slug, "title": title, "units": units})
            pages.append({"id": slug, "title": title, "path": path, "part": label})
            alignment.append({"id": slug, "italianLines": len(source), "units": len(units),
                              "translationLines": {identifier: sum(len([l for l in cell if l]) for cell in cells) for identifier, cells in aligned.items()}})

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
    ru_index = None; ru_names = []; ru_ids = []; gloss_pivot = None
    for identifier in RUSSIAN_GLOSSARIES if with_russian else ():
        item = corpus.glossary(spec, identifier)
        index = glosses.load_glossary(corpus.ensure_glossary(spec, item, allow_download=False), item, fold=fold)
        if item.kind == "gloss-pivot":
            gloss_pivot = index; continue
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
        if edition == "study":
            (ROOT / "sources" / "dictionaries" / "coverage.json").write_text(json.dumps(coverage, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    write_json(data / "dictionaries" / "coverage.json", coverage)

    # The reader index: every translation with its language, maker, and alignment; one default per language.
    defaults = {"en": "en-longfellow", "ru": russian_default}
    described = [T.describe(t, default_visible=(defaults.get(t.lang) == t.id)) for t in chosen]
    for row in described: row["default"] = defaults.get(row["lang"]) == row["id"]; row["coverage"] = [CANTICA[c][0] for c in row["coverage"]]
    write_json(data / "parallel-reader.json", {
        "schema": "firstpair-parallel-reader-v1", "title": "Dante — Commedia", "unit": "tercet",
        "sourceLanguage": {"id": "it", "lang": "it", "label": "Italiano", "position": "left"},
        "languages": [{"id": code, "label": LANGUAGES[code]} for code in languages],
        "translations": described,
        "dictionaries": {code: {"path": f"_data/dictionaries/it-{code}/index.json"} for code in languages}, "pages": pages,
    })
    write_json(data / "reader.json", pages); write_json(data / "alignment-report.json", alignment); write_json(data / "targets.json", [])
    listing = "; ".join(f"{LANGUAGES[code]}: " + ", ".join(t.title for t in chosen if t.lang == code) for code in languages)
    toc = ["# Dante — La Divina Commedia", "", "**[Open the Reader](firstpair:reader)** — or use the book icon in the ribbon, or the *Open Reader* command. Every canto below opens in the Reader.", "",
           f"Italian stands on the left; the translations follow. Translations in this vault — {listing}. The column header rotates among the translations of a language, and a second column of the same language can stand beside it.", "",
           "Select any Italian word to open its dictionary entry.", ""]
    for cantica, (label, count) in CANTICA.items():
        toc.extend([f"## {label}", ""] + [f"- [{label} — Canto {number}](firstpair:page:{cantica}-{number:02d})" for number in range(1, count + 1)] + [""])
    (output / "Home.md").write_text("\n".join(toc), encoding="utf-8")
    (output / "Reader").mkdir(); (output / "Reader" / "About the alignment.md").write_text((ROOT / vault_guide).read_text(encoding="utf-8"), encoding="utf-8")
    sources = output / "Sources"; sources.mkdir()
    shutil.copy2(ROOT / "RIGHTS.md", sources / "RIGHTS.md"); shutil.copy2(ROOT / "sources" / "PROVENANCE.json", sources / "PROVENANCE.json")
    for name in list(ENGLISH_SOURCES) + (list(RUSSIAN_SOURCES) if with_russian else []) + (["russian-lozinsky.html"] if edition == "study" else []):
        shutil.copy2(RAW / name, sources / name)
    obsidian = output / ".obsidian"; (obsidian / "plugins").mkdir(parents=True)
    shutil.copytree(FIRSTPAIR_PLUGIN, obsidian / "plugins" / "firstpair-reader")
    write_json(obsidian / "community-plugins.json", ["firstpair-reader"]); write_json(obsidian / "core-plugins.json", ["file-explorer", "search", "bookmarks", "outline"])
    files = sorted(str(path.relative_to(output)) for path in output.rglob("*") if path.is_file())
    digest = hashlib.sha256("\n".join(f"{path} {hashlib.sha256((output / path).read_bytes()).hexdigest()}" for path in files).encode()).hexdigest()
    write_json(output / "VAULT-MANIFEST.json", {"schema": "dante-multilingual-vault-v2", "version": VERSION, "edition": edition, "cantos": 100, "alignmentUnit": "tercet",
        "languages": ["it"] + languages, "translations": [t.id for t in chosen],
        "dictionaryEntries": {f"it-{code}": len(payload["entries"]) for code, payload in (("en", payload_en), ("ru", payload_ru)) if payload},
        "coverage": {k: coverage[k] for k in ("italianForms", "analysed")}, "files": len(files), "payloadDigest": digest})
    vault_output = str(output.relative_to(ROOT)) if output.is_relative_to(ROOT) else str(output)
    (ROOT / config_name).write_text(json.dumps(emacs_config(edition, pages, vault_output, languages), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"vault": str(output), "edition": edition, "config": config_name, "translations": [t.id for t in chosen], "cantos": 100,
                      "italianForms": report_en["forms"], "analysed": report_en["analysed"], "englishCovered": report_en["covered"], "russianCovered": report_ru["covered"],
                      "unanalysed": len(report_en["unanalysed"]), "russianMissing": len(report_ru["missing"]), "russianMissingLemmas": {"names": len(names), "common": len(common)}}, ensure_ascii=False))


if __name__ == "__main__": main()
