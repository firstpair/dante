#!/usr/bin/env python3
"""Fetch and normalize pinned, redistributable source material."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tarfile
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "sources" / "raw"
USER_AGENT = "DanteCommedia/1.0 (https://github.com/firstpair/dante)"
# Every text here is public domain: Dante's Italian and the English
# translations from Project Gutenberg, Min's Russian from Wikisource.
GUTENBERG = {
    "italian.txt": "https://www.gutenberg.org/cache/epub/1012/pg1012.txt",
    "english-longfellow.txt": "https://www.gutenberg.org/cache/epub/1004/pg1004.txt",
    "english-cary.txt": "https://www.gutenberg.org/cache/epub/8800/pg8800.txt",
    "english-norton-1.txt": "https://www.gutenberg.org/cache/epub/1995/pg1995.txt",
    "english-norton-2.txt": "https://www.gutenberg.org/cache/epub/1996/pg1996.txt",
    "english-norton-3.txt": "https://www.gutenberg.org/cache/epub/1997/pg1997.txt",
    "english-sibbald-inferno.txt": "https://www.gutenberg.org/cache/epub/41537/pg41537.txt",
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
RUSSIAN_URL = "https://lib.ru/POEZIQ/DANTE/comedy.txt"
ROMAN = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI", "XXII", "XXIII", "XXIV", "XXV", "XXVI", "XXVII", "XXVIII", "XXIX", "XXX", "XXXI", "XXXII", "XXXIII", "XXXIV")


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


# Lib.ru/Классика keeps the nineteenth-century Russian translations in their
# original orthography, Windows-1251 encoded. All are public domain: every
# translator died before 1926 (Min 1885, Minaev 1889, Chuiko 1899; Petrov and
# Fedorov published in the 1880s–90s). Stored re-encoded as UTF-8 HTML.
AZLIB = {
    "russian-min-inferno.html": ("http://az.lib.ru/d/dante_a/dante_ad1-oldorfo.shtml", "Dmitry Egorovich Min (1818–1885), Inferno, 1855 edition"),
    "russian-min-purgatorio.html": ("http://az.lib.ru/d/dante_a/dante_ch1-oldorfo.shtml", "Dmitry Egorovich Min, Purgatorio, 1902 edition"),
    "russian-min-paradiso.html": ("http://az.lib.ru/d/dante_a/text_1904_paradiso-oldorfo.shtml", "Dmitry Egorovich Min, Paradiso, 1904 edition"),
    "russian-minaev-purgatorio.html": ("http://az.lib.ru/d/dante_a/dante_ch2-oldorfo.shtml", "Dmitry Dmitrievich Minaev (1835–1889), Purgatorio, Wolff edition"),
    "russian-minaev-paradiso.html": ("http://az.lib.ru/d/dante_a/dante_ray1-oldorfo.shtml", "Dmitry Dmitrievich Minaev, Paradiso (1879), Wolff edition"),
    "russian-petrov-inferno.html": ("http://az.lib.ru/d/dante_a/text_1871_inferno-oldorfo.shtml", "V. A. Petrov, Inferno in terza rima, 1887"),
    "russian-fedorov-inferno.html": ("http://az.lib.ru/d/dante_a/text_1898_inferno-oldorfo.shtml", "A. P. Fedorov, Inferno in verse, 1898"),
    "russian-chuiko-inferno.html": ("http://az.lib.ru/d/dante_a/text_1894_ad_chuyko-oldorfo.shtml", "V. V. Chuiko, Inferno in prose, 1894"),
}


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
    for filename, (url, description) in AZLIB.items():
        payload = download(url).decode("cp1251", "replace").encode("utf-8"); (RAW / filename).write_bytes(payload)
        provenance["files"][filename] = {"url": url, "translator": description, "orthography": "pre-1918, as transcribed by Lib.ru/Классика", "sha256": hashlib.sha256(payload).hexdigest()}
    russian = download(RUSSIAN_URL)
    decoded = russian.decode("koi8-r")
    encoded = decoded.encode("utf-8")
    (RAW / "russian-lozinsky.html").write_bytes(encoded)
    provenance["files"]["russian-lozinsky.html"] = {"url": RUSSIAN_URL, "translator": "Mikhail Leonidovich Lozinsky", "sha256": hashlib.sha256(encoded).hexdigest(), "redistribution": "local-study-copy; review US rights before publication"}
    (ROOT / "sources" / "PROVENANCE.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__": main()
