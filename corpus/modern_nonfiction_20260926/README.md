In this complete project, the prepared corpus is stored under corpus/modern_nonfiction_20260926/ and its configuration under configs/modern_nonfiction_20260926/. Formal search experiments have not been run.

# Four English Nonfiction Test Works Published After 2019

Downloading, body-text cleaning, letter-stream generation, and input validation are complete. **The formal search experiments for these modern corpora have not been run. Hit rates, figures, or tables from the older nonfiction corpora must not be presented as results for these four works.**

This directory provides replacements for the four historical nonfiction test texts in future experiments. The old corpora, experiment code, existing results, and archive package remain unchanged. The original training set of eight novels remains fixed; the four additional works are used only for testing.

## Works and Publication Dates

| Work | Author or editor | Publication date | Type | Valid letters after cleaning |
|---|---|---|---|---:|
| Not Yet Imagined: A Study of Hubble Space Telescope Operations | Christopher Gainor | 2020 (bibliographic year) | Spaceflight history | 464,343 |
| Introduction to Anthropology | Jennifer Hasty, David G. Lewis, Marjorie M. Snipes | 2022-02-23 | Anthropology textbook | 1,184,580 |
| Introduction to Political Science | Mark Carl Rom, Masaki Hidaka, Rachel Bzostek Walker | 2022-05-18 | Political science textbook | 941,288 |
| Introduction to Philosophy | Nathan Smith | 2022-06-15 | Philosophy textbook | 722,700 |

The total is **3,312,911** a–z letters. All four works satisfy the requirement of publication after 2019, meaning 2020 onward. A modern publication date does not imply that the historical events discussed or the quoted texts also date from 2020 onward.

Both the bibliographic page of the NASA book and [GovInfo Date Issued](https://www.govinfo.gov/app/details/GOVPUB-NAS-PURL-gpo152941) record 2020. Public promotion occurred in 2021, while 2023 in the current download URL is the upload-path year; an exact publication month and day are therefore not invented. The [official source](https://science.nasa.gov/mission/hubble/multimedia/e-books/not-yet-imagined-a-study-of-hubble-space-telescope-operations/) is an EPUB.

The publication dates of the three OpenStax textbooks come from Citation information on the official pages: [Anthropology](https://openstax.org/books/introduction-anthropology/pages/1-introduction), [Political Science](https://openstax.org/books/introduction-political-science/pages/1-introduction), and [Philosophy](https://openstax.org/books/introduction-philosophy/pages/1-introduction). The saved downloads are the official web versions accessed on 2026-09-26 and may include post-publication corrections; they are not claimed to match the 2022 first printings word for word. The specific contentVersion, archiveVersion, and SHA256 of each page have been frozen.

## Files and Cleaning Boundaries

- `raw/`: The complete NASA EPUB and the original HTML for all introductions and numbered body-text sections of the three textbooks, stored in separate ZIP files. Non-body pages such as tables of contents, chapter exercises, glossaries, summaries, and references were not downloaded for the textbooks. The raw ZIP files are not complete ebooks containing all supporting material.
- `test/`: Four UTF-8 body-text TXT files, retaining word boundaries, punctuation, and paragraphs for the existing experiment loader.
- `letters/`: Lowercase a–z letter streams without word boundaries, exactly matching the existing `letters_only` behavior, with only one newline retained at the end.
- `corpus_manifest.json`: Works, publication evidence, sources, versions, paths, statistics, and SHA256 values for the three file types.
- `audit/*.sections.json`: The original member file, checksum, paragraph count, and letter interval for each body-text section. Intervals use zero-based, left-closed and right-open notation.
- `audit/validation.json`: Results from the input validation that was actually run.
- `licenses/`: Attribution and licensing information for each work, which must be retained with the derived texts.

The NASA extraction includes the prologue, nine main chapters, and the conclusion, for 11 chapter units in total. Only paragraphs marked typographically as main body text were retained. The foreword, table of contents, figures, tables, captions, sidebars, chapter endnotes, appendices, index, and bibliography were excluded.

The OpenStax introductions and numbered body-text sections were extracted in the order of their official tables of contents, totaling 120, 106, and 65 sections. Body paragraphs and quotations within them were retained. Figures, tables, captions, learning objectives, teaching-tip boxes, exercises, references, navigation, and page-license footers were excluded. Superscript numerical citation markers were removed; parenthetical author–year citations were retained. Readable link text within the body was retained, while bare URLs were removed.

NFC, line endings, and whitespace were normalized; soft hyphens and zero-width characters were removed; common typographic ligatures were expanded. The authors' text was not rewritten, translated, or supplemented. Section titles were not mixed into body text. Sampling follows the original protocol: fragments may cross sentence or section joins, no additional boundary filtering is applied, and sections are not treated as independent works.

## Connection to the Existing Experiments

Run from the original project root (Python 3.10+; the additional scripts use only the standard library):

```sh
python3 scripts/prepare_modern_nonfiction_corpus.py
python3 scripts/run_modern_nonfiction_experiment.py --check
```

The first command cleans the texts again using only the frozen local sources. To download missing pages, use:

```sh
python3 scripts/prepare_modern_nonfiction_corpus.py --download
```

When ready for formal computation, run:

```sh
python3 scripts/run_modern_nonfiction_experiment.py --workers 4
```

The separate result directory is `results/modern_nonfiction_20260926/`; the old result directory is not overwritten. The formal configuration is the same as that of the original controlled nonfiction experiment: lengths 100/200/500, with 500 trials each and 1500 trials in total; seed=20260903; 4-gram, alpha=0.1; 30 restarts × 4000 effective proposals; candidate archive capacity 1000; no word boundaries, no neutral proposals counted, and no early stopping. Each of the four works remains equally likely to be selected, followed by uniform sampling of the letter starting position within the selected work. Retaining the random seed does not make fragments or trial results from the new and old corpora paired observations.

`--pilot-trials 1` runs one full-budget pilot trial per length under a separate `pilot_1/` directory. Neither this pilot nor the formal search was run for this delivery.

## Basic Text Statistics

The following statistics were computed before word boundaries were removed. A word is defined as a contiguous lowercase `[a-z]+` sequence, consistent with the project's letter range; accented words and abbreviations may be split. TTR is averaged over non-overlapping 1000-word windows, excluding a final segment with fewer than 1000 words, to reduce the effect of differences in full-text length on TTR.

| Short title | Words | Distinct words | Mean word length | Mean TTR over 1000-word windows |
|---|---:|---:|---:|---:|
| Not Yet Imagined | 92,728 | 6,969 | 5.0076 | 0.4249 |
| Anthropology | 225,531 | 15,211 | 5.2524 | 0.4388 |
| Political Science | 181,811 | 10,862 | 5.1773 | 0.4141 |
| Philosophy | 143,351 | 9,989 | 5.0415 | 0.4043 |

The exact table values are governed by `corpus_manifest.json`. These four works cover spaceflight history and three textbook fields in the humanities and social sciences. They can supplement the modern nonfiction condition, but they do not establish coverage of all genres such as modern news, speech, or social media. Word counts or TTR must not be treated directly as conclusions about reading difficulty.

## Licensing and the Original Preparation Package

The NASA source is retained in its officially distributed public version; images and other third-party material were not included in the cleaned text. Attribution for the three OpenStax web texts is retained under the CC BY-NC-SA 4.0 license identified at download, and the derived texts follow the same license. When viewing or transferring the materials, retain the `licenses/` notices and original sources together; do not distribute the body-text TXT files without their source information.

The original preparation package contained only the four new corpora, new preparation and execution scripts, and new configurations. Running the search requires the main project's `substitution_rank/` and eight training texts. That preparation package was not a backup of the entire code workspace and did not rewrite the previous experiment archive.
