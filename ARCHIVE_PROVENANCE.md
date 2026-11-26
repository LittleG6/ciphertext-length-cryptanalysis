# Archive Provenance

The archived trial CSV files, existing experiment metadata, source texts, corpus manifests, and exported figures retain their supplied content. Historical metadata records the paths, environment, and source hashes used when those experiments ran.

Comments, docstrings, command-line help, runtime messages, and documentation are provided in English. These text changes affect current source-file hashes. They do not replace the historical source hashes recorded in experiment metadata.

## Repository Layout

- Configurations are stored under `configs/`; command-line defaults and script paths use that directory.
- The modern corpus is stored under `corpus/modern_nonfiction_20260926/`, matching the paths recorded in its manifest. Its runner reads its configuration from `configs/modern_nonfiction_20260926/`.
- Identical copies of the archive-capacity analysis script are represented by one file at `results/archive_capacity_sensitivity_20260730/analyze_archive_capacity.py`.
- Both distinct MATLAB plotting scripts are retained, with a separate filename for the revised version.

The combined formal-experiment runner normalizes search defaults through `SearchConfig` when checking whether a paired baseline can be derived from main-experiment records. This includes the proposal-scope and early-stopping fields as well as the temperature fields. Saved experimental records are not altered by this consistency-check adjustment.

Package version `0.1.0` is retained from the supplied code. Installation metadata includes the analysis dependencies and explicit package discovery.

## Corpus Checksums

The modern corpus retains its original preparation checksum list as `SHA256SUMS.original.txt`. The accompanying `SHA256SUMS.txt` describes the redistributed paths and English documentation. The original raw, cleaned, and letters-only text bytes are unchanged.

## Archived Results and Fresh Runs

Archived results should be analyzed as supplied. To start fresh formal searches, use a separate working copy and preserve its existing `results/` directory as `archived_results/` before running the experiment scripts. Resume only outputs generated with the same code, configuration, and input paths; historical archives are not checkpoints from a new installation.
