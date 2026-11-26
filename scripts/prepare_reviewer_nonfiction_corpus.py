#!/usr/bin/env python3
"""Download, clean, and freeze the four-work nonfiction test corpus."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
CORPUS_ROOT = ROOT / "corpus" / "reviewer_nonfiction_20260903"
START_MARKER = re.compile(
    r"^\*\*\* START OF THE PROJECT GUTENBERG EBOOK .+?\*\*\*\s*$", re.MULTILINE
)
END_MARKER = re.compile(
    r"^\*\*\* END OF THE PROJECT GUTENBERG EBOOK .+?\*\*\*\s*$", re.MULTILINE
)
ILLUSTRATION_BLOCK = re.compile(
    r"\[(?:Illustration|Illustration:).*?\]", re.IGNORECASE | re.DOTALL
)

BOOKS = (
    {
        "pg_id": 23,
        "filename": "pg23_frederick_douglass.txt",
        "title": "Narrative of the Life of Frederick Douglass, an American Slave",
        "author": "Frederick Douglass",
        "genre": "memoir/history",
        "start_phrase": "I was born in Tuckahoe, near Hillsborough",
        "end_phrase": "\nTHE END",
    },
    {
        "pg_id": 1228,
        "filename": "pg1228_origin_of_species.txt",
        "title": "On the Origin of Species",
        "author": "Charles Darwin",
        "genre": "science",
        "start_phrase": "When on board H.M.S. ‘Beagle,’ as naturalist",
        "end_phrase": "\nINDEX.",
    },
    {
        "pg_id": 205,
        "filename": "pg205_walden.txt",
        "title": "Walden, and On The Duty Of Civil Disobedience",
        "author": "Henry David Thoreau",
        "genre": "essay/philosophy",
        "start_phrase": "When I wrote the following pages, or rather the bulk of them",
        "end_phrase": "\nTHE END",
    },
    {
        "pg_id": 148,
        "filename": "pg148_franklin_autobiography.txt",
        "title": "The Autobiography of Benjamin Franklin",
        "author": "Benjamin Franklin",
        "genre": "autobiography/history",
        "start_phrase": "Dear Son: I have ever had pleasure in obtaining any little anecdotes",
        "end_phrase": "[HERE THE AUTOBIOGRAPHY BREAKS OFF]",
    },
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_url(pg_id: int) -> str:
    return f"https://www.gutenberg.org/cache/epub/{pg_id}/pg{pg_id}.txt"


def download_raw(book: dict[str, object]) -> Path:
    raw_path = CORPUS_ROOT / "raw" / str(book["filename"])
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    if not raw_path.exists():
        request = Request(source_url(int(book["pg_id"])), headers={"User-Agent": "substitution-rank-study/0.1"})
        with urlopen(request, timeout=60) as response:
            payload = response.read()
        raw_path.write_bytes(payload)
    return raw_path


def clean_text(raw_text: str, start_phrase: str, end_phrase: str) -> str:
    text = unicodedata.normalize("NFC", raw_text.replace("\r\n", "\n").replace("\r", "\n"))
    start_match = START_MARKER.search(text)
    end_match = END_MARKER.search(text)
    if start_match is None or end_match is None or end_match.start() <= start_match.end():
        raise ValueError("Project Gutenberg START/END markers are missing or out of order")
    payload = text[start_match.end() : end_match.start()]
    body_start = payload.find(start_phrase)
    if body_start < 0:
        raise ValueError(f"body start phrase not found: {start_phrase!r}")
    body = payload[body_start:]
    body_end = body.find(end_phrase)
    if body_end < 0:
        raise ValueError(f"body end phrase not found: {end_phrase!r}")
    body = ILLUSTRATION_BLOCK.sub("", body[:body_end])
    body = re.sub(r"\n[ \t]+\n", "\n\n", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip() + "\n"


def normalized_letter_count(text: str) -> int:
    return sum("a" <= char <= "z" for char in text.lower())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    records: list[dict[str, object]] = []
    for book in BOOKS:
        raw_path = CORPUS_ROOT / "raw" / str(book["filename"])
        if args.download:
            raw_path = download_raw(book)
        if not raw_path.is_file():
            raise FileNotFoundError(f"missing raw snapshot: {raw_path}; rerun with --download")
        clean_path = CORPUS_ROOT / "test" / str(book["filename"])
        clean_path.parent.mkdir(parents=True, exist_ok=True)
        clean = clean_text(
            raw_path.read_text(encoding="utf-8-sig"),
            str(book["start_phrase"]),
            str(book["end_phrase"]),
        )
        clean_path.write_text(clean, encoding="utf-8", newline="\n")
        letters = normalized_letter_count(clean)
        if letters < 500:
            raise ValueError(f"cleaned document is unexpectedly short: {clean_path}")
        records.append({
            **book,
            "official_landing_url": f"https://www.gutenberg.org/ebooks/{book['pg_id']}",
            "source_text_url": source_url(int(book["pg_id"])),
            "raw_path": raw_path.relative_to(ROOT).as_posix(),
            "clean_path": clean_path.relative_to(ROOT).as_posix(),
            "raw_bytes": raw_path.stat().st_size,
            "clean_bytes": clean_path.stat().st_size,
            "normalized_letter_count": letters,
            "raw_sha256": sha256(raw_path),
            "clean_sha256": sha256(clean_path),
        })
    manifest = {
        "corpus_name": "Reviewer supplement nonfiction corpus v1",
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "split": "test only; original eight-work fiction training corpus remains fixed",
        "cleaning_rule": "extract between work-specific first and last body markers inside Gutenberg START/END; exclude indices/editorial appendices; remove illustration blocks; normalize NFC and line endings",
        "documents": records,
    }
    CORPUS_ROOT.mkdir(parents=True, exist_ok=True)
    (CORPUS_ROOT / "corpus_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (CORPUS_ROOT / "corpus_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print(f"prepared={len(records)} letters={sum(int(row['normalized_letter_count']) for row in records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
