#!/usr/bin/env python3
"""Build the complete offline Dante Obsidian vault."""

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
FIRSTPAIR_PLUGIN = ROOT.parents[0] / "firstpair" / "publishing" / "vault" / "plugin" / "firstpair-reader"
CANTICA = {"inferno": ("Inferno", 34), "purgatorio": ("Purgatorio", 33), "paradiso": ("Paradiso", 33)}
ITALIAN_HEADER = re.compile(r"^(Inferno|Purgatorio|Paradiso)\s+•\s+Canto\s+([IVXLCDM]+)$", re.I)
ENGLISH_HEADER = re.compile(r"^(Inferno|Purgatorio|Paradiso):\s+Canto\s+([IVXLCDM]+)$", re.I)
WORD = re.compile(r"[^\W\d_]+(?:[’'][^\W\d_]+)*", re.UNICODE)
NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def roman(value: str) -> int:
    numbers = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0; previous = 0
    for character in reversed(value.upper()):
        current = numbers[character]; total += -current if current < previous else current; previous = max(previous, current)
    return total


def normalize_word(value: str) -> str:
    return unicodedata.normalize("NFC", value).casefold().strip("’'")


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
    for index, start in enumerate(starts):
        following = re.search(r"<ul><a name=\d+></a><h2>", text[start.end():])
        end = start.end() + following.start() if following else len(text)
        block = text[start.end():end]
        lines = []
        for raw in block.splitlines():
            match = re.match(r"^\s{10,}(?:\d+\s+)?(\S.*)$", raw)
            if match: lines.append(" ".join(re.sub(r"<[^>]+>", "", match.group(1)).split()))
        ordered.append(lines)
    keys = [(cantica, number) for cantica, (_, count) in CANTICA.items() for number in range(1, count + 1)]
    result = dict(zip(keys, ordered, strict=True))
    if len(result) != 100: raise RuntimeError(f"Russian source has {len(result)} cantos")
    return result


def usage_examples(italian: dict[tuple[str, int], list[str]]) -> dict[str, list[str]]:
    examples: dict[str, list[str]] = defaultdict(list)
    for lines in italian.values():
        for line in lines:
            for token in WORD.findall(line):
                key = normalize_word(token)
                if line not in examples[key] and len(examples[key]) < 3: examples[key].append(line)
    return examples


def dictionary(path: Path, examples: dict[str, list[str]], target: str) -> dict:
    root = ET.parse(path).getroot(); entries: dict[str, list[dict]] = defaultdict(list)
    for node in root.findall(".//tei:entry", NS):
        orth = node.findtext("tei:form/tei:orth", default="", namespaces=NS).strip()
        if not orth: continue
        key = normalize_word(orth); pos = node.findtext("tei:gramGrp/tei:pos", default="", namespaces=NS).strip()
        translations = []
        for quote in node.findall(".//tei:cit[@type='trans']/tei:quote", NS):
            value = " ".join("".join(quote.itertext()).split())
            if value and value not in translations: translations.append(value)
        notes = []
        for definition in node.findall(".//tei:def", NS):
            value = " ".join("".join(definition.itertext()).split())
            if value and value not in notes: notes.append(value)
        if translations or notes:
            entries[key].append({"headword": orth, "partOfSpeech": pos, "definitions": translations + notes, "examples": examples.get(key, [])})
    return {"schema": "firstpair-offline-dictionary-v1", "sourceLanguage": "it", "targetLanguage": target, "license": "CC BY-SA 3.0", "attribution": "FreeDict 2025.11.23 / WikDict / Wiktionary / DBnary; usage examples from Dante's Commedia", "entries": dict(sorted(entries.items()))}


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2: raise SystemExit("usage: build_vault.py OUTPUT")
    output = Path(sys.argv[1]).resolve()
    if output.exists(): raise SystemExit(f"refusing to replace existing output: {output}")
    required = ("italian.txt", "english.txt", "russian-lozinsky.html", "ita-eng.tei", "ita-rus.tei")
    missing = [name for name in required if not (RAW / name).is_file()]
    if missing: raise SystemExit(f"fetch sources first; missing: {', '.join(missing)}")
    italian = parse_gutenberg(RAW / "italian.txt", ITALIAN_HEADER)
    english = parse_gutenberg(RAW / "english.txt", ENGLISH_HEADER)
    russian = parse_russian(); examples = usage_examples(italian)
    output.mkdir(parents=True); data = output / "_data"; chapters = data / "chapters"; chapters.mkdir(parents=True)
    pages = []; alignment = []
    for cantica, (label, count) in CANTICA.items():
        for canto in range(1, count + 1):
            key = (cantica, canto); source = italian[key]; en = english[key]; ru = russian[key]
            if len(en) < len(source): raise RuntimeError(f"{label} {canto}: Italian {len(source)} != English {len(en)}")
            en = en[:len(source)]
            if len(source) - len(ru) > 2: raise RuntimeError(f"{label} {canto}: Italian {len(source)} != Russian {len(ru)}")
            ru = ru[:len(source)] + [""] * max(0, len(source) - len(ru))
            slug = f"{cantica}-{canto:02d}"; units = []
            for start in range(0, max(len(source), len(ru)), 3):
                units.append({"id": f"{slug}-lines-{start + 1:03d}-{min(start + 3, len(source)):03d}", "source": source[start:start + 3], "translations": {"en": en[start:start + 3], "ru": ru[start:start + 3]}})
            path = f"_data/chapters/{slug}.json"; title = f"{label} — Canto {canto}"
            write_json(output / path, {"schema": "firstpair-aligned-chapter-v1", "id": slug, "title": title, "units": units})
            pages.append({"id": slug, "title": title, "path": path})
            alignment.append({"id": slug, "italianLines": len(source), "englishLines": len(en), "russianLines": len(ru), "units": len(units)})
    write_json(data / "parallel-reader.json", {
        "schema": "firstpair-parallel-reader-v1", "title": "Dante — Commedia", "unit": "tercet",
        "sourceLanguage": {"id": "it", "lang": "it", "label": "Italiano", "position": "right"},
        "translations": [{"id": "en", "lang": "en", "label": "English", "defaultVisible": True}, {"id": "ru", "lang": "ru", "label": "Русский", "defaultVisible": True}],
        "dictionaries": {"en": {"path": "_data/dictionaries/it-en.json"}, "ru": {"path": "_data/dictionaries/it-ru.json"}}, "pages": pages,
    })
    write_json(data / "reader.json", pages); write_json(data / "alignment-report.json", alignment); write_json(data / "targets.json", [])
    write_json(data / "dictionaries" / "it-en.json", dictionary(RAW / "ita-eng.tei", examples, "en"))
    write_json(data / "dictionaries" / "it-ru.json", dictionary(RAW / "ita-rus.tei", examples, "ru"))
    toc = ["# Dante — La Divina Commedia", "", "Open **FirstPair Reader** from the ribbon or command palette.", "", "Italian is always the rightmost column. Use the always-visible English and Russian checkboxes for two or three columns.", ""]
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
    write_json(output / "VAULT-MANIFEST.json", {"schema": "dante-multilingual-vault-v1", "cantos": 100, "alignmentUnit": "tercet", "languages": ["it", "en", "ru"], "dictionaryEntries": {"it-en": 29660, "it-ru": 14137}, "files": len(files), "payloadDigest": digest})


if __name__ == "__main__": main()
