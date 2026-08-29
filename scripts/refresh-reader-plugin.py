#!/usr/bin/env python3
"""Plugin-only refresh of a built or live Dante vault.

The only write into an open vault that FirstPair doctrine allows: replace the
FirstPair Reader package (main.js, styles.css, manifest.json) with the source
under ~/src/firstpair, leaving data.json, workspace state, and every note
untouched, so an active Obsidian Sync uploads the new bytes.
"""
from __future__ import annotations
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parents[0] / "firstpair" / "publishing" / "vault" / "plugin" / "firstpair-reader"
FILES = ("main.js", "styles.css", "manifest.json")

vault = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else None
if vault is None or not (vault / "Home.md").is_file(): raise SystemExit("usage: refresh-reader-plugin.py VAULT")
target = vault / ".obsidian" / "plugins" / "firstpair-reader"; target.mkdir(parents=True, exist_ok=True)
for name in FILES: shutil.copy2(SOURCE / name, target / name)
version = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))["version"]
manifest_path = vault / "VAULT-MANIFEST.json"
if manifest_path.is_file():
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")); manifest["readerPlugin"] = version
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
print(json.dumps({"vault": str(vault), "readerPlugin": version, "files": list(FILES)}))
