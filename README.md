# Ciphertext Length Cryptanalysis

This file summarizes the main experiment results, additional experiment results, derived analyses, paper figures, and MATLAB plotting code currently used in the paper.

For exact file locations, see [FILE_LAYOUT.md](FILE_LAYOUT.md). The [manuscript guide](PAPER_MAP.md) links the materials to the paper. Installation and running instructions are in [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

**File Descriptions**

## 01 Main Experiment

`formal_minimum.csv`: Results for **11 ciphertext lengths**, with **1,000 trials per length**, for a total of **11,000 main experiment records**.

The same directory contains metadata, summaries, thresholds, the overall status file, and the formal experiment configuration.

## 02 Additional Experiments

### Search Budget

Results, metadata, summaries, thresholds, and configurations for **10, 30, and 100 restarts**.

The **30-restart condition** is a control baseline extracted from the main experiment under matched conditions for paired comparisons.

### Language Model Order

Results, metadata, summaries, thresholds, and configurations for the **3-gram, 4-gram, and 5-gram models**.

The **4-gram condition** is a control baseline extracted from the main experiment under matched conditions for paired comparisons.

### Archive Capacity

Archive-capacity sensitivity results for **K = 100, 500, 1000, and 2000**.

**K = 1000** is the read-only paired baseline from the main experiment; the results for the other capacities were obtained from new runs.

## 03 Derived Analyses for the Paper

Derived analysis files used for the paper's tables, paired differences, results stratified by work, and failure-mechanism statistics.

## 04 New Supplementary Experiments

Revised supplementary experiments and the associated analysis code.

## 05 Experiment Code and Corpora

All experiment code and the training and test corpora used in the experiments.

Includes the four newly added modern nonfiction texts.

These modern texts are prepared supplementary materials; their formal search experiments have not been run. The completed nonfiction results use the historical works by Douglass, Darwin, Thoreau, and Franklin.

## 06 MATLAB Plotting Code

The plotting script for the paper, with embedded data and no dependence on external CSV files.

The original script is retained as `scripts/plot_paper_figures_embedded.m`. The revised script from the experiment-code directory is provided separately as `scripts/plot_paper_figures_revised.m`; it contains the numerical ciphertext-length axes and supplementary-experiment figures.

### Paper Figures

`results/matlab_paper_figures/`

The figures currently used in the paper, with both **600 dpi PNG** and **vector PDF** versions in each set.

The revised figure exports are retained separately under `results/matlab_paper_figures_revised/`.
