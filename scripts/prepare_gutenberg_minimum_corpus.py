#!/usr/bin/env python3
"""Prepare the frozen 8-train/4-test Project Gutenberg corpus.

The raw UTF-8 snapshots must already exist under
corpus/formal_minimum/raw/{train,test}. This script deterministically extracts
the main prose, removes illustration blocks, writes cleaned files, and freezes
all checksums and sizes in CSV/JSON manifests.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import unicodedata


ROOT = Path(__file__).resolve().parent.parent
CORPUS_ROOT = ROOT / "corpus" / "formal_minimum"
START_MARKER = re.compile(r"^\*\*\* START OF THE PROJECT GUTENBERG EBOOK .+?\*\*\*\s*$", re.MULTILINE)
END_MARKER = re.compile(r"^\*\*\* END OF THE PROJECT GUTENBERG EBOOK .+?\*\*\*\s*$", re.MULTILINE)
ILLUSTRATION_BLOCK = re.compile(r"\[(?:Illustration|Illustration:).*?\]", re.IGNORECASE | re.DOTALL)


BOOKS = (
    {
        "pg_id": 1342,
        "split": "train",
        "filename": "pg1342_pride_and_prejudice.txt",
        "title": "Pride and Prejudice",
        "author": "Jane Austen",
        "year": 1813,
        "start_phrase": "It is a truth universally acknowledged",
    },
    {
        "pg_id": 1400,
        "split": "train",
        "filename": "pg1400_great_expectations.txt",
        "title": "Great Expectations",
        "author": "Charles Dickens",
        "year": 1861,
        "start_phrase": "My father’s family name being Pirrip",
    },
    {
        "pg_id": 2701,
        "split": "train",
        "filename": "pg2701_moby_dick.txt",
        "title": "Moby-Dick; or, The Whale",
        "author": "Herman Melville",
        "year": 1851,
        "start_phrase": "Call me Ishmael.",
    },
    {
        "pg_id": 1661,
        "split": "train",
        "filename": "pg1661_sherlock_holmes.txt",
        "title": "The Adventures of Sherlock Holmes",
        "author": "Arthur Conan Doyle",
        "year": 1892,
        "start_phrase": "To Sherlock Holmes she is always _the_ woman.",
    },
    {
        "pg_id": 84,
        "split": "train",
        "filename": "pg84_frankenstein.txt",
        "title": "Frankenstein; or, The Modern Prometheus",
        "author": "Mary Wollstonecraft Shelley",
        "year": 1818,
        "start_phrase": "You will rejoice to hear that no disaster has accompanied",
    },
    {
        "pg_id": 345,
        "split": "train",
        "filename": "pg345_dracula.txt",
        "title": "Dracula",
        "author": "Bram Stoker",
        "year": 1897,
        "start_phrase": "_3 May. Bistritz._--Left Munich",
    },
    {
        "pg_id": 74,
        "split": "train",
        "filename": "pg74_tom_sawyer.txt",
        "title": "The Adventures of Tom Sawyer",
        "author": "Mark Twain",
        "year": 1876,
        "start_phrase": "“Tom!”",
    },
    {
        "pg_id": 1260,
        "split": "train",
        "filename": "pg1260_jane_eyre.txt",
        "title": "Jane Eyre: An Autobiography",
        "author": "Charlotte Brontë",
        "year": 1847,
        "start_phrase": "There was no possibility of taking a walk that day.",
    },
    {
        "pg_id": 35,
        "split": "test",
        "filename": "pg35_time_machine.txt",
        "title": "The Time Machine",
        "author": "H. G. Wells",
        "year": 1895,
        "start_phrase": "The Time Traveller (for so it will be convenient to speak of him)",
    },
    {
        "pg_id": 120,
        "split": "test",
        "filename": "pg120_treasure_island.txt",
        "title": "Treasure Island",
        "author": "Robert Louis Stevenson",
        "year": 1883,
        "start_phrase": "Squire Trelawney, Dr. Livesey, and the rest of these gentlemen",
    },
    {
        "pg_id": 174,
        "split": "test",
        "filename": "pg174_dorian_gray.txt",
        "title": "The Picture of Dorian Gray",
        "author": "Oscar Wilde",
        "year": 1890,
        "start_phrase": "The studio was filled with the rich odour of roses",
    },
    {
        "pg_id": 55,
        "split": "test",
        "filename": "pg55_wizard_of_oz.txt",
        "title": "The Wonderful Wizard of Oz",
        "author": "L. Frank Baum",
        "year": 1900,
        "start_phrase": "Dorothy lived in the midst of the great Kansas prairies",
    },
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def letter_count(text: str) -> int:
    return sum("a" <= char <= "z" for char in text.lower())


def clean_text(raw_text: str, start_phrase: str) -> str:
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
    body = ILLUSTRATION_BLOCK.sub("", body)
    body = re.sub(r"\n[ \t]+\n", "\n\n", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip() + "\n"


def build_manifest() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for book in BOOKS:
        split = str(book["split"])
        filename = str(book["filename"])
        raw_path = CORPUS_ROOT / "raw" / split / filename
        clean_path = CORPUS_ROOT / split / filename
        if not raw_path.is_file():
            raise FileNotFoundError(f"missing raw snapshot: {raw_path}")
        cleaned = clean_text(raw_path.read_text(encoding="utf-8-sig"), str(book["start_phrase"]))
        clean_path.parent.mkdir(parents=True, exist_ok=True)
        clean_path.write_text(cleaned, encoding="utf-8", newline="\n")
        letters = letter_count(cleaned)
        if letters < 500:
            raise ValueError(f"cleaned document is unexpectedly short: {clean_path}")
        records.append(
            {
                "pg_id": book["pg_id"],
                "split": split,
                "title": book["title"],
                "author": book["author"],
                "publication_year": book["year"],
                "official_landing_url": f"https://www.gutenberg.org/ebooks/{book['pg_id']}",
                "source_text_url": f"https://www.gutenberg.org/cache/epub/{book['pg_id']}/pg{book['pg_id']}.txt",
                "raw_path": raw_path.relative_to(ROOT).as_posix(),
                "clean_path": clean_path.relative_to(ROOT).as_posix(),
                "body_start_phrase": book["start_phrase"],
                "raw_bytes": raw_path.stat().st_size,
                "clean_bytes": clean_path.stat().st_size,
                "normalized_letter_count": letters,
                "fourgram_windows": letters - 3,
                "raw_sha256": sha256(raw_path),
                "clean_sha256": sha256(clean_path),
            }
        )
    return records


def validate(records: list[dict[str, object]]) -> None:
    train_authors = {str(row["author"]) for row in records if row["split"] == "train"}
    test_authors = {str(row["author"]) for row in records if row["split"] == "test"}
    overlap = train_authors & test_authors
    if overlap:
        raise ValueError(f"author leakage across split: {sorted(overlap)}")
    if sum(row["split"] == "train" for row in records) != 8:
        raise ValueError("the minimum formal training split must contain exactly 8 documents")
    if sum(row["split"] == "test" for row in records) != 4:
        raise ValueError("the minimum formal test split must contain exactly 4 documents")


def write_manifests(records: list[dict[str, object]]) -> None:
    csv_path = CORPUS_ROOT / "corpus_manifest.csv"
    json_path = CORPUS_ROOT / "corpus_manifest.json"
    fieldnames = list(records[0])
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    totals = {}
    for split in ("train", "test"):
        split_rows = [row for row in records if row["split"] == split]
        totals[split] = {
            "documents": len(split_rows),
            "authors": len({str(row["author"]) for row in split_rows}),
            "clean_bytes": sum(int(row["clean_bytes"]) for row in split_rows),
            "normalized_letter_count": sum(int(row["normalized_letter_count"]) for row in split_rows),
            "fourgram_windows": sum(int(row["fourgram_windows"]) for row in split_rows),
        }
    payload = {
        "corpus_name": "Project Gutenberg minimum formal corpus v1",
        "prepared_on": "2026-07-26",
        "split_rule": "document-disjoint and author-disjoint; eight training works and four test works",
        "cleaning_rule": "extract from the frozen work-specific first prose phrase to the Project Gutenberg END marker; remove illustration blocks; normalize NFC and line endings",
        "experiment_normalization": "the experiment later lowercases, maps non-a-z to spaces, collapses whitespace, then removes spaces because include_spaces=false",
        "totals": totals,
        "documents": records,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    records = build_manifest()
    validate(records)
    write_manifests(records)
    train_letters = sum(int(row["normalized_letter_count"]) for row in records if row["split"] == "train")
    test_letters = sum(int(row["normalized_letter_count"]) for row in records if row["split"] == "test")
    print(f"Prepared {len(records)} documents: train letters={train_letters:,}; test letters={test_letters:,}")
    print(f"Manifest: {CORPUS_ROOT / 'corpus_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
