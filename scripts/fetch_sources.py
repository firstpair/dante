#!/usr/bin/env python3
"""Fetch and normalize pinned, redistributable source material."""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import tarfile
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "sources" / "raw"
USER_AGENT = "DanteMultilingualVault/0.1 (https://github.com/firstpair)"
GUTENBERG = {
    "italian.txt": "https://www.gutenberg.org/cache/epub/1012/pg1012.txt",
    "english.txt": "https://www.gutenberg.org/cache/epub/1004/pg1004.txt",
}
DICTIONARIES = {
    "ita-eng": {
        "url": "https://download.freedict.org/dictionaries/ita-eng/2025.11.23/freedict-ita-eng-2025.11.23.src.tar.xz",
        "sha512": "86b505604204cfcc311fd03dd7e5aa2a73f6c9991c2d29af214dc22d6769c12449d810e07a39abfe70899c12dfb693c0fb447b0cc8ff69e9375eae5ffae07483",
    },
    "ita-rus": {
        "url": "https://download.freedict.org/dictionaries/ita-rus/2025.11.23/freedict-ita-rus-2025.11.23.src.tar.xz",
        "sha512": "c6766e21a96cdd91804ec6985660f33d6c4743139e9afc641c295c8f207355e5480c7af396198010528fc9ffeb93c713f5deb07d367ec80910bdad1c8ec648f7",
    },
}
API = "https://ru.wikisource.org/w/api.php"
RUSSIAN_URL = "https://lib.ru/POEZIQ/DANTE/comedy.txt"
ROMAN = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI", "XXII", "XXIII", "XXIV", "XXV", "XXVI", "XXVII", "XXVIII", "XXIX", "XXX", "XXXI", "XXXII", "XXXIII", "XXXIV")


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


class PoemParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(); self.depth = 0; self.poem_depth = 0; self.skip_depth = 0
        self.current: list[str] = []; self.poems: list[list[str]] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "div":
            self.depth += 1
            if "poem" in attrs.get("class", "").split() and not self.poem_depth:
                self.poem_depth = self.depth; self.current = []
        if self.poem_depth and tag in {"br", "p"}: self.current.append("\n")
        if self.poem_depth and tag in {"style", "sup"}: self.skip_depth += 1
        if self.poem_depth and tag == "span" and "linenumright" in attrs.get("class", "").split(): self.skip_depth += 1

    def handle_endtag(self, tag):
        if self.poem_depth and tag in {"style", "sup", "span"} and self.skip_depth: self.skip_depth -= 1
        if tag == "div":
            if self.poem_depth == self.depth:
                text = "".join(self.current).replace("\xa0", " ")
                lines = [" ".join(line.split()) for line in text.splitlines() if line.strip()]
                if lines: self.poems.append(lines)
                self.poem_depth = 0; self.current = []
            self.depth -= 1

    def handle_data(self, data):
        if self.poem_depth and not self.skip_depth: self.current.append(data)


def parse_poems(html: str) -> list[list[str]]:
    parser = PoemParser(); parser.feed(html); return parser.poems


def api_parse(title: str) -> tuple[str, int]:
    query = urllib.parse.urlencode({"action": "parse", "page": title, "prop": "text|revid", "format": "json", "formatversion": 2})
    value = json.loads(download(f"{API}?{query}"))
    if "error" in value: raise RuntimeError(f"Wikisource {title}: {value['error']['info']}")
    return value["parse"]["text"], value["parse"]["revid"]


def fetch_russian() -> tuple[list[dict], list[dict]]:
    cantos: list[dict] = []; revisions: list[dict] = []
    specs = (
        ("inferno", "Божественная комедия (Данте; Мин)/Ад/ДО", 34),
        ("purgatorio", "Божественная комедия (Данте; Мин)/Чистилище/ДО", 33),
        ("paradiso", "Божественная комедия. Рай (Данте; Мин)/ДО", 33),
    )
    for cantica, title, count in specs:
        html, revision = api_parse(title)
        poems = [poem for poem in parse_poems(html) if 100 <= len(poem) <= 160]
        if len(poems) < count: raise RuntimeError(f"{cantica} yielded only {len(poems)} canto poems")
        for number, poem in enumerate(poems[:count], 1):
            cantos.append({"cantica": cantica, "canto": number, "lines": poem})
            print(f"Russian {cantica} {number:02d}: {len(poem)} lines")
        revisions.append({"title": title, "revision": revision})
    if len(cantos) != 100: raise RuntimeError(f"Expected 100 Russian cantos, got {len(cantos)}")
    return cantos, revisions


def extract_dictionary(archive: bytes, name: str) -> tuple[bytes, bytes]:
    with tempfile.NamedTemporaryFile(suffix=".tar.xz") as temporary:
        temporary.write(archive); temporary.flush()
        with tarfile.open(temporary.name, "r:xz") as bundle:
            tei = bundle.extractfile(f"{name}/{name}.tei")
            copying = bundle.extractfile(f"{name}/COPYING")
            if tei is None or copying is None: raise RuntimeError(f"Incomplete {name} archive")
            return tei.read(), copying.read()


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True); provenance = {"schema": "dante-source-provenance-v1", "files": {}}
    for filename, url in GUTENBERG.items():
        payload = download(url); (RAW / filename).write_bytes(payload)
        provenance["files"][filename] = {"url": url, "sha256": hashlib.sha256(payload).hexdigest()}
    for name, metadata in DICTIONARIES.items():
        archive = download(metadata["url"])
        actual = hashlib.sha512(archive).hexdigest()
        if actual != metadata["sha512"]: raise RuntimeError(f"SHA-512 mismatch for {name}: {actual}")
        tei, copying = extract_dictionary(archive, name)
        (RAW / f"{name}.tei").write_bytes(tei); (RAW / f"{name}-COPYING.txt").write_bytes(copying)
        provenance["files"][f"{name}.tei"] = {"url": metadata["url"], "release": "2025.11.23", "archiveSha512": actual, "sha256": hashlib.sha256(tei).hexdigest()}
    russian = download(RUSSIAN_URL)
    decoded = russian.decode("koi8-r")
    encoded = decoded.encode("utf-8")
    (RAW / "russian-lozinsky.html").write_bytes(encoded)
    provenance["files"]["russian-lozinsky.html"] = {"url": RUSSIAN_URL, "translator": "Mikhail Leonidovich Lozinsky", "sha256": hashlib.sha256(encoded).hexdigest(), "redistribution": "local-study-copy; review US rights before publication"}
    (ROOT / "sources" / "PROVENANCE.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__": main()
