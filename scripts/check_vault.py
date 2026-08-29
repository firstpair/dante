#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else None
if root is None or not root.is_dir(): raise SystemExit("usage: check_vault.py VAULT")
parallel = json.loads((root / "_data/parallel-reader.json").read_text(encoding="utf-8"))
assert parallel["schema"] == "firstpair-parallel-reader-v1"
assert [item["id"] for item in parallel["translations"]] == ["ru", "en"]
assert parallel["sourceLanguage"]["position"] == "left"
assert all(item["defaultVisible"] for item in parallel["translations"])
assert parallel["sourceLanguage"]["position"] == "right"
assert len(parallel["pages"]) == 100
units = 0
for page in parallel["pages"]:
    chapter = json.loads((root / page["path"]).read_text(encoding="utf-8")); assert chapter["units"]
    for unit in chapter["units"]:
        assert set(unit["translations"]) == {"en", "ru"}; assert unit["source"]; units += 1
for name, minimum in (("it-en", 29660), ("it-ru", 14137)):
    value = json.loads((root / f"_data/dictionaries/{name}.json").read_text(encoding="utf-8"))
    assert sum(len(entries) for entries in value["entries"].values()) >= minimum
plugin = (root / ".obsidian/plugins/firstpair-reader/main.js").read_text(encoding="utf-8")
for token in ("parallel-reader.json", "language-toggle", "openDictionary", "unit.translations"): assert token in plugin
for unsafe in ("workspace.json", "workspace-mobile.json", "workspaces.json"): assert not (root / ".obsidian" / unsafe).exists()
print(json.dumps({"passed": True, "cantos": 100, "alignedUnits": units, "languages": ["it", "en", "ru"]}))
