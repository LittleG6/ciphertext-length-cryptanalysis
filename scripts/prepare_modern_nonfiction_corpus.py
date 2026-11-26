#!/usr/bin/env python3
"""Freeze four post-2019 nonfiction sources and extract prose for evaluation."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
import unicodedata
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "corpus/modern_nonfiction_20260926"
BOOKS = [
    dict(id="not_yet_imagined_2020", title="Not Yet Imagined: A Study of Hubble Space Telescope Operations",
         authors="Christopher Gainor", publication_date="2020", date_precision="year",
         publisher="NASA", genre="space history", format="epub",
         source_url="https://science.nasa.gov/wp-content/uploads/2023/07/not-yet-imagined.epub",
         landing_url="https://science.nasa.gov/mission/hubble/multimedia/e-books/not-yet-imagined-a-study-of-hubble-space-telescope-operations/",
         bibliographic_url="https://www.govinfo.gov/app/details/GOVPUB-NAS-PURL-gpo152941",
         rights="NASA freely distributed publication; retain attribution; third-party illustrations excluded from derived text",
         date_evidence="GovInfo Date Issued and EPUB cataloguing page give 2020, NASA SP-2020-4237; EPUB metadata 2020-12-03. Public promotion occurred in 2021; the current NASA file URL is dated 2023. Bibliographic year is recorded separately from announcement/upload dates."),
    dict(id="introduction_anthropology_2022", slug="introduction-anthropology", title="Introduction to Anthropology",
         authors="Jennifer Hasty; David G. Lewis; Marjorie M. Snipes", publication_date="2022-02-23",
         date_precision="day", publisher="OpenStax", genre="anthropology", format="html.zip"),
    dict(id="introduction_political_science_2022", slug="introduction-political-science", title="Introduction to Political Science",
         authors="Mark Carl Rom; Masaki Hidaka; Rachel Bzostek Walker", publication_date="2022-05-18",
         date_precision="day", publisher="OpenStax", genre="political science", format="html.zip"),
    dict(id="introduction_philosophy_2022", slug="introduction-philosophy", title="Introduction to Philosophy",
         authors="Nathan Smith", publication_date="2022-06-15", date_precision="day",
         publisher="OpenStax", genre="philosophy", format="html.zip"),
]
for _book in BOOKS[1:]:
    _book.update(landing_url=f"https://openstax.org/books/{_book['slug']}/pages/1-introduction",
                 rights="CC BY-NC-SA 4.0", license_url="https://creativecommons.org/licenses/by-nc-sa/4.0/",
                 date_evidence="Publication date in publisher's Citation information; this frozen web revision may contain later errata.")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def state(payload: bytes) -> dict:
    match = re.search(r"window\.__PRELOADED_STATE__ = (.*?)</script>", payload.decode(), re.S)
    if not match:
        raise ValueError("Missing OpenStax book state")
    return json.loads(match[1])["content"]


def fetch(url: str) -> bytes:
    for attempt in range(3):
        try:
            request = Request(url, headers={"User-Agent": "noncommercial-corpus-study/1.0"})
            with urlopen(request, timeout=60) as response:
                return response.read()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def leaves(node: dict):
    for child in node.get("contents", []):
        if child.get("contents"):
            yield from leaves(child)
        else:
            yield child


def download(workers: int) -> None:
    raw = DEST / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    for book in BOOKS:
        path = raw / f"{book['id']}.{book['format']}"
        if book["format"] == "epub":
            if not path.exists():
                payload = fetch(book["source_url"])
                if not zipfile.is_zipfile(__import__("io").BytesIO(payload)):
                    raise ValueError("Source is not an EPUB archive")
                path.write_bytes(payload)
                write_json(path.with_suffix(".download.json"), dict(url=book["source_url"], downloaded_at=datetime.now(timezone.utc).isoformat(), sha256=sha(payload)))
            continue
        source_path = raw / f"{book['id']}.source.json"
        if path.exists():
            with zipfile.ZipFile(path) as archive:
                initial = archive.read("1-introduction.html")
        else:
            initial = fetch(book["landing_url"])
        info = state(initial)["book"]
        selected = [p for p in leaves(info["tree"]) if p.get("toc_target_type") in {"intro", "numbered-section"}]
        excluded = [p for p in leaves(info["tree"]) if p not in selected]
        if not selected or len({p['slug'] for p in selected}) != len(selected):
            raise ValueError("Empty or duplicate source pages")
        with zipfile.ZipFile(path, "a", compression=zipfile.ZIP_DEFLATED) as archive:
            existing = set(archive.namelist())
            if "1-introduction.html" not in existing:
                archive.writestr("1-introduction.html", initial)
                existing.add("1-introduction.html")
            def retrieve(page):
                url = f"https://openstax.org/books/{book['slug']}/pages/{page['slug']}"
                payload = fetch(url)
                received = state(payload)
                if received['book']['contentVersion'] != info['contentVersion'] or received['book']['archiveVersion'] != info['archiveVersion']:
                    raise ValueError(f"Source version changed: {url}")
                if received['page']['id'] != page['id'].split('@')[0]:
                    raise ValueError(f"Wrong page: {url}")
                return page['slug'] + '.html', payload
            pending = [p for p in selected if p['slug'] + '.html' not in existing]
            with ThreadPoolExecutor(max_workers=workers) as pool:
                tasks = [pool.submit(retrieve, p) for p in pending]
                for index, task in enumerate(as_completed(tasks), 1):
                    name, payload = task.result()
                    archive.writestr(name, payload)
                    if index % 20 == 0 or index == len(tasks):
                        print(f"{book['id']}: {index}/{len(tasks)} new pages", flush=True)
        previous = json.loads(source_path.read_text()) if source_path.exists() else {}
        write_json(source_path, dict(downloaded_at=previous.get('downloaded_at', datetime.now(timezone.utc).isoformat()),
                   content_version=info['contentVersion'], archive_version=info['archiveVersion'],
                   selected_pages=selected, excluded_pages=excluded,
                   source_url_template=f"https://openstax.org/books/{book['slug']}/pages/{{slug}}"))


class HTMLTree(HTMLParser):
    void = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, payload: bytes):
        super().__init__(convert_charrefs=True)
        self.root = ET.Element("root")
        self.stack = [self.root]
        self.feed(payload.decode("utf-8"))

    def handle_starttag(self, tag, attrs):
        node = ET.SubElement(self.stack[-1], tag, {k: v or "" for k, v in attrs})
        if tag not in self.void:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.void:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        parent = self.stack[-1]
        if len(parent):
            parent[-1].tail = (parent[-1].tail or "") + data
        else:
            parent.text = (parent.text or "") + data


def tag(node):
    return node.tag.split("}")[-1]


def inline_text(node):
    if tag(node) in {'br', 'hr'} or node.get('data-type') == 'newline':
        return ' '
    parts = [node.text or ""]
    for child in node:
        cls = child.get("class", "").lower()
        drop = tag(child) in {"sup", "math", "script", "style"} or any(w in cls for w in ["endnote-reference", "endnote-ref", "footnote-number"]) or child.get('role') == 'doc-noteref'
        if not drop:
            parts.append(inline_text(child))
        parts.append(child.tail or "")
    return "".join(parts)


def clean_paragraph(text):
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u00ad", "").replace("\u200b", "").replace("\ufeff", "")
    for a, b in {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl"}.items():
        text = text.replace(a, b)
    text = re.sub(r'(?:https?://|www\.)[^\s<>]+', lambda m: m[0][len(m[0].rstrip('.,;:)]}')):], text)
    text = re.sub(r'\(\s*\)|\[\s*\]', '', text)
    return re.sub(r"\s+", " ", text).strip()


def extract(book):
    raw_path = DEST / "raw" / f"{book['id']}.{book['format']}"
    sections = []
    with zipfile.ZipFile(raw_path) as archive:
        if book['format'] == 'epub':
            opf = ET.fromstring(archive.read('OEBPS/content.opf'))
            ns = {'o': 'http://www.idpf.org/2007/opf'}
            mapping = {e.get('id'): e.get('href') for e in opf.findall('o:manifest/o:item', ns)}
            names = ['OEBPS/' + mapping[e.get('idref')] for e in opf.findall('o:spine/o:itemref', ns)]
            names = [n for n in names if any(k in n for k in ['_Prologue.', '_Ch_', '_ConcC.'])]
            assert len(names) == 11, names
            for name in names:
                root = ET.fromstring(archive.read(name))
                paragraphs = [clean_paragraph(inline_text(p)) for p in root.iter() if tag(p) == 'p' and p.get('class', '').startswith('Body_Body-Text')]
                sections.append((name, paragraphs, sha(archive.read(name))))
        else:
            metadata = json.loads((DEST / 'raw' / f"{book['id']}.source.json").read_text())
            for page in metadata['selected_pages']:
                name = page['slug'] + '.html'
                payload = archive.read(name)
                root = HTMLTree(payload).root
                containers = [n for n in root.iter() if n.get('data-type') == 'page']
                if len(containers) != 1:
                    raise ValueError(f"Unexpected page container count: {name}: {len(containers)}")
                paragraphs = []
                def walk(node, blocked=False):
                    cls = node.get('class', '').lower()
                    dtype = node.get('data-type', '')
                    blocked = blocked or tag(node) in {'figure', 'figcaption', 'table', 'aside', 'script', 'style', 'nav'} or dtype in {'note', 'abstract', 'exercise', 'footnote', 'glossary', 'references', 'example'} or any(w in cls for w in ['learning-objectives', 'os-figure', 'os-table', 'os-note', 'os-footnote', 'chapter-outline'])
                    if blocked:
                        return
                    if tag(node) == 'p':
                        paragraphs.append(clean_paragraph(inline_text(node)))
                        return
                    for child in node:
                        walk(child, blocked)
                walk(containers[0])
                if not paragraphs:
                    raise ValueError(f"No prose extracted: {name}")
                sections.append((name, paragraphs, sha(payload)))
    return raw_path, sections


def stats(text):
    words = re.findall('[a-z]+', text.lower())
    windows = [len(set(words[i:i + 1000])) / 1000 for i in range(0, len(words) - 999, 1000)]
    return dict(word_tokens=len(words), word_types=len(set(words)), mean_word_length=round(sum(map(len, words)) / len(words), 4),
                mean_ttr_nonoverlap_1000=round(sum(windows) / len(windows), 4), ttr_windows=len(windows),
                approximate_sentence_count=len(re.findall(r'[.!?]+(?:[”\"’\']?)(?:\s|$)', text)))


def prepare():
    records = []
    for directory in ['test', 'letters', 'audit', 'licenses']:
        (DEST / directory).mkdir(parents=True, exist_ok=True)
    for book in BOOKS:
        raw_path, sections = extract(book)
        text_parts, audit, offset = [], [], 0
        for name, paras, digest in sections:
            paras = [p for p in paras if p and re.search('[A-Za-z]', p)]
            section = '\n\n'.join(paras)
            count = len(re.sub('[^a-z]', '', section.lower()))
            audit.append(dict(source_member=name, source_sha256=digest, paragraphs=len(paras),
                              letter_start=offset, letter_end=offset + count))
            offset += count
            text_parts.append(section)
        text = '\n\n'.join(text_parts) + '\n'
        letters = re.sub('[^a-z]', '', text.lower())
        if len(letters) < 100000 or '\ufffd' in text:
            raise ValueError(f"Invalid cleaned document: {book['id']}")
        clean_path = DEST / 'test' / f"{book['id']}.txt"
        letters_path = DEST / 'letters' / f"{book['id']}.txt"
        clean_path.write_text(text, encoding='utf-8')
        letters_path.write_text(letters + '\n', encoding='ascii')
        write_json(DEST / 'audit' / f"{book['id']}.sections.json", audit)
        (DEST / 'licenses' / f"{book['id']}.txt").write_text(
            f"{book['authors']}. {book['title']}. {book['publisher']}, {book['publication_date']}.\n"
            f"Access for free at {book['landing_url']}\n{book['rights']}\n{book.get('license_url', '')}\n"
            "Derived research corpus: main prose extracted; navigation, images, tables, notes, exercises and ancillary matter excluded; Unicode/whitespace normalized. Read and redistribute with this attribution file.\n", encoding='utf-8')
        record = dict(book, raw_path=raw_path.relative_to(ROOT).as_posix(), clean_path=clean_path.relative_to(ROOT).as_posix(),
                      letters_path=letters_path.relative_to(ROOT).as_posix(), raw_sha256=sha(raw_path.read_bytes()),
                      clean_sha256=sha(clean_path.read_bytes()), letters_sha256=sha(letters_path.read_bytes()),
                      normalized_letter_count=len(letters), sections=len(sections), paragraphs=sum(x['paragraphs'] for x in audit), **stats(text))
        if book['format'] != 'epub':
            meta = json.loads((DEST / 'raw' / f"{book['id']}.source.json").read_text())
            record.update(content_version=meta['content_version'], archive_version=meta['archive_version'])
        records.append(record)
        print(f"{book['id']}: {len(letters):,} letters, {record['word_tokens']:,} words, {len(sections)} sections", flush=True)
    write_json(DEST / 'corpus_manifest.json', dict(corpus_name='Modern nonfiction test corpus v1', cutoff='publication year >= 2020',
               prepared_at=datetime.now(timezone.utc).isoformat(), split='test only; original eight-work fiction training corpus fixed',
               experiment_status='prepared; formal experiment not run', documents=records))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.workers <= 8:
        parser.error('--workers must be between 1 and 8')
    if args.download:
        download(args.workers)
    prepare()


if __name__ == '__main__':
    main()
