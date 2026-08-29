#!/usr/bin/env python3
"""Source-owned validator for a built Dante vault, run by the FirstPair publisher.

The vault declares its translations in ``_data/parallel-reader.json``. The
public edition carries English only and must contain no trace of Lozinsky's
Russian; the local study copy carries Russian and English.
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
translations = [item["id"] for item in parallel["translations"]]
assert translations in (["en"], ["ru", "en"]), translations
assert parallel["sourceLanguage"]["position"] == "left"
assert all(item["defaultVisible"] for item in parallel["translations"])
assert len(parallel["pages"]) == 100
assert set(parallel["dictionaries"]) == set(translations)
public = translations == ["en"]
units = 0
for page in parallel["pages"]:
    text = (root / page["path"]).read_text(encoding="utf-8"); chapter = json.loads(text); assert chapter["units"]
    if public: assert not CYRILLIC.search(text), f"Cyrillic text in public chapter {page['path']}"
    for unit in chapter["units"]:
        assert set(unit["translations"]) == set(translations); assert unit["source"]; units += 1
minimums = {"it-en": 29660, "it-ru": 14137}
for code in translations:
    index = json.loads((root / f"_data/dictionaries/it-{code}/index.json").read_text(encoding="utf-8"))
    assert index["schema"] == "firstpair-reader-dictionary-index-v1"
    total = 0
    for shard in index["shards"].values():
        path = root / f"_data/dictionaries/it-{code}" / shard
        assert path.stat().st_size <= 4_500_000, f"{path} too large for sync"
        total += sum(len(entries) for entries in json.loads(path.read_text(encoding="utf-8"))["entries"].values())
    assert total >= minimums[f"it-{code}"], (code, total)
sources = sorted(path.name for path in (root / "Sources").iterdir())
if public:
    assert "russian-lozinsky.html" not in sources and "ita-rus-COPYING.txt" not in sources, sources
    assert not (root / "_data/dictionaries/it-ru").exists()
else:
    assert "russian-lozinsky.html" in sources
manifest = json.loads((root / "VAULT-MANIFEST.json").read_text(encoding="utf-8"))
assert manifest["languages"] == (["it", "en"] if public else ["it", "ru", "en"])
plugin = (root / ".obsidian/plugins/firstpair-reader/main.js").read_text(encoding="utf-8")
for token in ("parallel-reader.json", "language-toggle", "openDictionary", "unit.translations", "firstpair:page:", "dictionary-index-v1", "page--stacked"): assert token in plugin
for unsafe in ("workspace.json", "workspace-mobile.json", "workspaces.json"): assert not (root / ".obsidian" / unsafe).exists()
print(json.dumps({"passed": True, "cantos": 100, "alignedUnits": units, "languages": manifest["languages"], "edition": "public" if public else "study"}))
