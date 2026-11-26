# File Locations

The numbered sections in README.md describe groups of materials. The files are stored at the paths below.

| README section | Actual location |
| --- | --- |
| 01 Main Experiment | `results/formal_minimum.csv`, its metadata and summary files, and `configs/main/formal.json` |
| 02 Search Budget | `results/predefined_budget_restarts*.csv` and `configs/sensitivity/` |
| 02 Language Model Order | `results/predefined_order*.csv` and `configs/sensitivity/` |
| 02 Archive Capacity | `results/archive_capacity_sensitivity_20260730/` and `configs/sensitivity/archive_*.json` |
| 03 Derived Analyses | `results/paper_analysis/` |
| 04 New Supplementary Experiments | `results/reviewer_supplement_20260903/`, its configuration directory, and the corresponding scripts |
| 05 Experiment Code and Corpora | `substitution_rank/`, `scripts/`, `tests/`, `data/`, `configs/`, and `corpus/` |
| 06 MATLAB Plotting Code | `scripts/plot_paper_figures_embedded.m` and `scripts/plot_paper_figures_revised.m` |
| Paper Figures | `results/matlab_paper_figures/` and `results/matlab_paper_figures_revised/` |

The four prepared modern nonfiction works are included under `corpus/modern_nonfiction_20260926/`. Their formal search experiments have not been run. The completed historical nonfiction results use Douglass, Darwin, Thoreau, and Franklin.

See REPRODUCIBILITY.md for installation and running instructions. The modern corpus input check can be run from the project root:

```sh
python3 scripts/run_modern_nonfiction_experiment.py --check
```

That command validates the corpus and configuration without running a search. The modern input texts, original source files, manifests, and attribution/license files are preserved. The original preparation checksum list is retained as `SHA256SUMS.original.txt`; `SHA256SUMS.txt` describes this redistributed layout and English documentation.

See PAPER_MAP.md for the manuscript correspondence and ARCHIVE_PROVENANCE.md for the relationship between historical records and the current repository layout.
