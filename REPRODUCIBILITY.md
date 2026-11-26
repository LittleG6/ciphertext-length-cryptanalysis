# ciphertext-length-cryptanalysis
Code and experimental materials for the paper: "The Effect of Ciphertext Length on the Top-k Ranking of the Correct Plaintext in Monoalphabetic Substitution Ciphers"

This repository contains the search implementation, experiment configurations, corpora, archived trial results, and analysis code. Run the commands below from the repository root.

## Environment and installation

Python 3.10 or later is required. The core experiments use Python's standard library. Install the analysis dependencies for figures and archived-result analysis:

```sh
python3 -m pip install -e '.[analysis]'
```

The analysis extra includes matplotlib, NumPy, pandas, and Pillow. The MATLAB figure script requires MATLAB separately.

## Quick check

```sh
python3 -m tests.run_validation
python3 -m substitution_rank run --config configs/demo/demo_sample_corpus.json --output work/demo.csv
```

The demo uses the small texts in `data/`. Its output is separate from the archived paper results.

## Configurations and corpora

| Path | Purpose |
| --- | --- |
| `configs/main/formal.json` | Main experiment: 11 ciphertext lengths, 1,000 trials per length |
| `configs/demo/`, `configs/smoke/`, `configs/pilot/` | Demo, smoke, and pilot settings |
| `configs/sensitivity/` | Paper sensitivity settings for search budget, model order, and archive capacity |
| `configs/reviewer_supplement_20260903/` | Controlled search, fixed-pool reranking, smoothing, and nonfiction supplement |
| `configs/exploratory/` | Earlier exploratory settings; see its README before interpreting them |
| `corpus/formal_minimum/` | Eight training works, four fiction test works, and corpus manifests |
| `corpus/reviewer_nonfiction_20260903/` | Four historical nonfiction test works and their manifests |

The original `configs/` layout is retained. The configurations in `configs/exploratory/` are not the exact settings used for the paper's sensitivity results.

The main experiment contains 11,000 trials. The original search-budget, model-order, and archive-capacity sensitivity comparisons use 300 trials per configured length and condition. The controlled-search, smoothing, and nonfiction supplement uses 500 trials per configured length and condition; fixed-pool reranking uses the corresponding controlled-search pools.

The completed nonfiction results use Douglass's *Narrative of the Life of Frederick Douglass*, Darwin's *On the Origin of Species*, Thoreau's *Walden*, and Franklin's *Autobiography*. The separate modern nonfiction preparation package has no completed formal-search results and is not included in these reported results.

## Run experiments

For a fresh full run, use a separate copy of the repository and rename that copy's existing `results/` directory to `archived_results/` before starting. The runners create new files under `results/`. Historical archives retain their original provenance and cannot be resumed from a different checkout. Resume only runs started with the same code, configuration, and input paths.

Run the main experiment with four workers and checkpoints every 100 trials:

```sh
bash scripts/run_formal_minimum.sh 4 100
```

To resume an interrupted main run, append `--resume` as the third argument. The combined main, search-budget, and model-order suite is available through:

```sh
bash scripts/run_all_formal_experiments.sh --workers 4 --batch-size 100
```

Run the reviewer supplement with:

```sh
python3 scripts/run_reviewer_supplement_experiments.py --workers 4
```

These commands start full searches. The supplement runner supports `--stage` for an individual stage and `--pilot-trials 1` for a separate pilot output directory. See each script's `--help` output for its options.

## Archived results and analysis

| Path | Contents |
| --- | --- |
| `results/formal_minimum.csv` | Main trial records, with accompanying metadata and summaries |
| `results/predefined_*.csv` | Original search-budget and model-order sensitivity results |
| `results/archive_capacity_sensitivity_20260730/` | Archive-capacity results and their analysis script |
| `results/reviewer_supplement_20260903/` | Controlled-search, reranking, smoothing, and historical nonfiction results |
| `results/paper_analysis/` | Derived tables and main-result analyses |
| `results/matlab_paper_figures/` and `results/matlab_paper_figures_revised/` | Archived original and revised figure exports |

Recreate the derived analyses from the archived trial CSV files:

```sh
python3 scripts/analyze_paper_results.py
python3 scripts/analyze_reviewer_supplement.py
python3 results/archive_capacity_sensitivity_20260730/analyze_archive_capacity.py
```

The main analysis writes to `results/paper_analysis/`; the supplement analysis writes summaries under its result directory. Source trial CSV files are read as inputs. Derived files in the output directories may be replaced.

The original MATLAB script `scripts/plot_paper_figures_embedded.m` and the revised script `scripts/plot_paper_figures_revised.m` render their embedded values; neither script reruns the cryptanalysis experiments. The revised script uses numerical ciphertext-length axes and includes the supplementary-experiment figures. Original and revised figure exports are retained in separate directories.

Archived metadata preserves the execution paths, environment information, and source hashes recorded when those experiments ran. Current checkout paths may differ from those historical records.
