#!/usr/bin/env python3
"""Source-owned validator for a built Dante vault, run by the FirstPair publisher.

The vault declares its languages and translations in
``_data/parallel-reader.json``. Public editions must not carry Lozinsky's
Russian; the English-only edition must contain no Cyrillic in its chapters.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
import sys

CYRILLIC = re.compile(r"[Ѐ-ӿ]")
root = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else None
if root is None or not root.is_dir(): raise SystemExit("usage: check-obsidian-vault.py VAULT")
parallel = json.loads((root / "_data/parallel-reader.json").read_text(encoding="utf-8"))
assert parallel["schema"] == "firstpair-parallel-reader-v1"
translations = parallel["translations"]; ids = [t["id"] for t in translations]
languages = [l["id"] for l in parallel["languages"]]
assert languages in (["en"], ["en", "ru"]), languages
assert parallel["sourceLanguage"]["position"] == "left"
assert len(parallel["pages"]) == 100
assert set(parallel["dictionaries"]) == set(languages)
for code in languages:
    assert sum(1 for t in translations if t["lang"] == code and t["default"]) == 1, f"one default translation per language ({code})"
manifest = json.loads((root / "VAULT-MANIFEST.json").read_text(encoding="utf-8"))
edition = manifest["edition"]
public = edition in ("en", "ru")
if public: assert "ru-lozinsky" not in ids, "Lozinsky's Russian must not be published"
else: assert "ru-lozinsky" in ids
units = 0
for page in parallel["pages"]:
    text = (root / page["path"]).read_text(encoding="utf-8"); chapter = json.loads(text); assert chapter["units"]
    if edition == "en": assert not CYRILLIC.search(text), f"Cyrillic text in English-edition chapter {page['path']}"
    covering = {t["id"] for t in translations if page["part"] in t["coverage"]}
    for unit in chapter["units"]:
        assert set(unit["translations"]) == covering, (page["id"], set(unit["translations"]) ^ covering); assert unit["source"]; units += 1
minimums = {"it-en": 29660, "it-ru": 14137}
for code in languages:
    index = json.loads((root / f"_data/dictionaries/it-{code}/index.json").read_text(encoding="utf-8"))
    assert index["schema"] == "firstpair-reader-dictionary-index-v1"
    total = 0
    for shard in index["shards"].values():
        path = root / f"_data/dictionaries/it-{code}" / shard
        assert path.stat().st_size <= 4_500_000, f"{path} too large for sync"
        total += sum(len(entries) for entries in json.loads(path.read_text(encoding="utf-8"))["entries"].values())
    assert total >= minimums[f"it-{code}"], (code, total)
sources = sorted(path.name for path in (root / "Sources").iterdir())
if public: assert "russian-lozinsky.html" not in sources, sources
if edition == "en": assert not any(name.startswith("russian-") for name in sources), sources
assert manifest["languages"] == ["it"] + languages and manifest["translations"] == ids
plugin = (root / ".obsidian/plugins/firstpair-reader/main.js").read_text(encoding="utf-8")
for token in ("parallel-reader.json", "language-toggle", "openDictionary", "unit.translations", "firstpair:page:", "dictionary-index-v1", "page--stacked"): assert token in plugin
for unsafe in ("workspace.json", "workspace-mobile.json", "workspaces.json"): assert not (root / ".obsidian" / unsafe).exists()
print(json.dumps({"passed": True, "edition": edition, "cantos": 100, "alignedUnits": units, "languages": manifest["languages"], "translations": ids}, ensure_ascii=False))
