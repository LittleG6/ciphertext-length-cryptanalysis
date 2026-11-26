#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "$script_dir/.." && pwd)"
script_path="$script_dir/$(basename "${BASH_SOURCE[0]}")"
original_args=("$@")

worker_count=4
batch_size=100
dry_run=0
use_caffeinate=1

usage() {
  printf '%s\n' \
    "Usage: bash scripts/run_all_formal_experiments.sh [options]" \
    "" \
    "Run the full formal experiment suite unattended, with automatic validation, resumption, summaries, plots, and audits." \
    "" \
    "Options:" \
    "  --workers N       Number of worker processes; default: 4" \
    "  --batch-size N    Trials per checkpoint batch; default: 100" \
    "  --dry-run         Check the environment and list tasks without running experiments" \
    "  --no-caffeinate   Do not use macOS caffeinate to prevent sleep" \
    "  -h, --help        Show this help message"
}

while (($#)); do
  case "$1" in
    --workers)
      worker_count="${2:?--workers requires an integer argument}"
      shift 2
      ;;
    --batch-size)
      batch_size="${2:?--batch-size requires an integer argument}"
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    --no-caffeinate)
      use_caffeinate=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! [[ "$worker_count" =~ ^[1-9][0-9]*$ ]]; then
  printf '%s\n' "--workers must be a positive integer" >&2
  exit 2
fi
if ! [[ "$batch_size" =~ ^[1-9][0-9]*$ ]]; then
  printf '%s\n' "--batch-size must be a positive integer" >&2
  exit 2
fi

cd "$project_root"

if ((dry_run == 0 && use_caffeinate == 1)) \
  && [[ "${SUBRANK_CAFFEINATED:-0}" != "1" ]] \
  && command -v caffeinate >/dev/null 2>&1; then
  exec env SUBRANK_CAFFEINATED=1 caffeinate -im "$script_path" "${original_args[@]}"
fi

mkdir -p results/logs tmp/matplotlib
run_stamp="$(date '+%Y%m%d_%H%M%S')"
run_log="results/logs/all_formal_experiments_${run_stamp}.log"
pid_file="results/all_formal_experiments.pid"

if [[ -f "$pid_file" ]]; then
  existing_pid="$(tr -dc '0-9' < "$pid_file")"
  if [[ -n "$existing_pid" ]] && kill -0 "$existing_pid" 2>/dev/null; then
    printf 'A full experiment run is already active, PID=%s\n' "$existing_pid" >&2
    exit 2
  fi
fi
printf '%s\n' "$$" > "$pid_file"

cleanup() {
  exit_code="${1:-0}"
  if [[ -f "$pid_file" ]] && [[ "$(tr -dc '0-9' < "$pid_file")" == "$$" ]]; then
    rm -f "$pid_file"
  fi
  if ((exit_code == 0)); then
    finish_message="All tasks completed successfully: $(date '+%Y-%m-%d %H:%M:%S')"
    printf '\n%s\n' "$finish_message"
    printf '\n%s\n' "$finish_message" >&3
  else
    finish_message="The run failed with exit code $exit_code. Run the same command again to resume automatically."
    printf '\n%s\n' "$finish_message" >&2
    printf '\n%s\n' "$finish_message" >&4
  fi
}
trap 'cleanup $?' EXIT

exec 3>&1 4>&2
printf 'The unattended experiment run has started; detailed progress is written to: %s\n' "$run_log" >&3
exec >> "$run_log" 2>&1
export PYTHONUNBUFFERED=1
export MPLCONFIGDIR="$project_root/tmp/matplotlib"

experiment_python="python3"
if ! command -v "$experiment_python" >/dev/null 2>&1; then
  printf '%s\n' "python3 was not found" >&2
  exit 2
fi

plot_python=""
for candidate in python3 python3.12 python3.13 python3.11; do
  if command -v "$candidate" >/dev/null 2>&1 \
    && "$candidate" -c 'import matplotlib, substitution_rank' >/dev/null 2>&1; then
    plot_python="$candidate"
    break
  fi
done
if [[ -z "$plot_python" ]]; then
  printf '%s\n' "No Python runtime with both matplotlib and substitution_rank was found" >&2
  exit 2
fi

train_documents=(
  corpus/formal_minimum/train/pg1342_pride_and_prejudice.txt
  corpus/formal_minimum/train/pg1400_great_expectations.txt
  corpus/formal_minimum/train/pg2701_moby_dick.txt
  corpus/formal_minimum/train/pg1661_sherlock_holmes.txt
  corpus/formal_minimum/train/pg84_frankenstein.txt
  corpus/formal_minimum/train/pg345_dracula.txt
  corpus/formal_minimum/train/pg74_tom_sawyer.txt
  corpus/formal_minimum/train/pg1260_jane_eyre.txt
)
test_documents=(
  corpus/formal_minimum/test/pg35_time_machine.txt
  corpus/formal_minimum/test/pg120_treasure_island.txt
  corpus/formal_minimum/test/pg174_dorian_gray.txt
  corpus/formal_minimum/test/pg55_wizard_of_oz.txt
)

computed_labels=(
  formal_minimum
  predefined_budget_restarts10
  predefined_budget_restarts100
  predefined_order3
  predefined_order5
)
computed_configs=(
  configs/main/formal.json
  configs/sensitivity/predefined_budget_restarts10.json
  configs/sensitivity/predefined_budget_restarts100.json
  configs/sensitivity/predefined_order3.json
  configs/sensitivity/predefined_order5.json
)
computed_outputs=(
  results/formal_minimum.csv
  results/predefined_budget_restarts10.csv
  results/predefined_budget_restarts100.csv
  results/predefined_order3.csv
  results/predefined_order5.csv
)

all_labels=(
  formal_minimum
  predefined_budget_restarts10
  predefined_budget_restarts30
  predefined_budget_restarts100
  predefined_order3
  predefined_order4
  predefined_order5
)
all_configs=(
  configs/main/formal.json
  configs/sensitivity/predefined_budget_restarts10.json
  configs/sensitivity/predefined_budget_restarts30.json
  configs/sensitivity/predefined_budget_restarts100.json
  configs/sensitivity/predefined_order3.json
  configs/sensitivity/predefined_order4.json
  configs/sensitivity/predefined_order5.json
)
all_outputs=(
  results/formal_minimum.csv
  results/predefined_budget_restarts10.csv
  results/predefined_budget_restarts30.csv
  results/predefined_budget_restarts100.csv
  results/predefined_order3.csv
  results/predefined_order4.csv
  results/predefined_order5.csv
)

for required_path in \
  "${train_documents[@]}" \
  "${test_documents[@]}" \
  "${all_configs[@]}" \
  corpus/formal_minimum/corpus_manifest.json; do
  if [[ ! -f "$required_path" ]]; then
    printf 'Missing formal experiment input: %s\n' "$required_path" >&2
    exit 2
  fi
done

printf '%s\n' \
  "============================================================" \
  "Full formal experiment suite for Top-k ranking in monoalphabetic substitution ciphers" \
  "Start time: $(date '+%Y-%m-%d %H:%M:%S')" \
  "Worker processes: $worker_count" \
  "Checkpoint batch size: $batch_size" \
  "Experiment runtime: $experiment_python" \
  "Plotting runtime: $plot_python" \
  "Log: $run_log" \
  "Computed trials: 15,200 unique trials" \
  "Derived baselines: 2,100 records selected from main-experiment trials with matching seeds" \
  "Final result set: 17,300 records" \
  "============================================================"

printf '\n[1/6] Validate code and configurations\n'
"$experiment_python" -m tests.run_validation
"$experiment_python" -m compileall -q substitution_rank tests
for config_path in "${all_configs[@]}"; do
  "$experiment_python" -m json.tool "$config_path" >/dev/null
done
bash -n scripts/run_formal_minimum.sh

if ((dry_run == 1)); then
  printf '\nDRY RUN: The following computation tasks would run in order\n'
  for index in "${!computed_labels[@]}"; do
    printf '  %s: %s -> %s\n' \
      "${computed_labels[$index]}" \
      "${computed_configs[$index]}" \
      "${computed_outputs[$index]}"
  done
  printf '%s\n' \
    "  predefined_budget_restarts30: derived from formal_minimum" \
    "  predefined_order4: derived from formal_minimum" \
    "DRY RUN complete. No experiments were run."
  exit 0
fi

validate_result() {
  local config_path="$1"
  local output_path="$2"
  local require_parallel="$3"
  "$experiment_python" - "$config_path" "$output_path" "$require_parallel" <<'PY'
import csv
import json
import sys
from collections import Counter
from pathlib import Path

config_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
require_parallel = sys.argv[3] == "1"
metadata_path = output_path.with_suffix(".metadata.json")
config = json.loads(config_path.read_text(encoding="utf-8"))
metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
with output_path.open(encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle))

expected = len(config["lengths"]) * int(config["trials_per_length"])
assert len(rows) == expected, (output_path, len(rows), expected)
pairs = [(int(row["length"]), int(row["trial"])) for row in rows]
assert len(set(pairs)) == expected
counts = Counter(length for length, _ in pairs)
assert counts == Counter({int(length): int(config["trials_per_length"]) for length in config["lengths"]})

valid_mechanisms = {
    "top1_success",
    "retained_below_top1",
    "visited_then_pruned",
    "never_visited",
}
for row in rows:
    assert row["mechanism_type"] in valid_mechanisms
    ever = row["true_ever_visited"] == "True"
    retained = row["true_retained"] == "True"
    pruned = row["true_pruned"] == "True"
    if row["rank"]:
        assert retained and ever
    if pruned:
        assert ever and not retained
    if row["mechanism_type"] == "visited_then_pruned":
        assert ever and pruned and not retained
    if row["mechanism_type"] == "never_visited":
        assert not ever and not retained

state = metadata["run_state"]
assert state["status"] == "completed"
assert int(state["completed_trials"]) == expected
assert int(state["remaining_trials"]) == 0
if require_parallel:
    assert state.get("parallel_fallback") is False
print(f"AUDIT PASS: {output_path} rows={expected}")
PY
}

run_compute_job() {
  local label="$1"
  local config_path="$2"
  local output_path="$3"
  local metadata_path="${output_path%.csv}.metadata.json"

  printf '\nRun computation task: %s\n' "$label"
  if [[ -f "$output_path" || -f "$metadata_path" ]]; then
    "$experiment_python" -m substitution_rank run \
      --config "$config_path" \
      --train "${train_documents[@]}" \
      --test "${test_documents[@]}" \
      --workers "$worker_count" \
      --batch-size "$batch_size" \
      --resume \
      --output "$output_path"
  else
    "$experiment_python" -m substitution_rank run \
      --config "$config_path" \
      --train "${train_documents[@]}" \
      --test "${test_documents[@]}" \
      --workers "$worker_count" \
      --batch-size "$batch_size" \
      --output "$output_path"
  fi

  require_parallel=0
  if ((worker_count > 1)); then
    require_parallel=1
  fi
  validate_result "$config_path" "$output_path" "$require_parallel"
}

derive_main_subset() {
  local target_config="$1"
  local target_output="$2"
  local purpose="$3"
  "$experiment_python" - \
    results/formal_minimum.csv \
    results/formal_minimum.metadata.json \
    "$target_config" \
    "$target_output" \
    "$purpose" <<'PY'
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

source_path = Path(sys.argv[1])
source_metadata_path = Path(sys.argv[2])
target_config_path = Path(sys.argv[3])
target_path = Path(sys.argv[4])
purpose = sys.argv[5]

source_metadata = json.loads(source_metadata_path.read_text(encoding="utf-8"))
target_config = json.loads(target_config_path.read_text(encoding="utf-8"))
normalized_config = dict(target_config)
from dataclasses import asdict
from substitution_rank.search import SearchConfig
normalized_config["search"] = asdict(SearchConfig(**target_config["search"]))
for key in ("seed", "ngram_order", "alpha", "include_spaces", "search"):
    assert source_metadata[key] == normalized_config[key], f"cannot derive: mismatch in {key}"

with source_path.open(encoding="utf-8", newline="") as handle:
    reader = csv.DictReader(handle)
    fieldnames = reader.fieldnames
    rows = [
        row
        for row in reader
        if int(row["length"]) in {int(value) for value in target_config["lengths"]}
        and int(row["trial"]) < int(target_config["trials_per_length"])
    ]

expected = len(target_config["lengths"]) * int(target_config["trials_per_length"])
assert fieldnames is not None
assert len(rows) == expected
assert len({(row["length"], row["trial"]) for row in rows}) == expected
rows.sort(key=lambda row: (int(row["length"]), int(row["trial"])))
target_path.parent.mkdir(parents=True, exist_ok=True)
with target_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

now = datetime.now(timezone.utc).isoformat()
metadata = dict(normalized_config)
metadata["run_provenance"] = {
    "derivation": purpose,
    "derived_from": str(source_path.resolve()),
    "derived_from_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
    "source_metadata": str(source_metadata_path.resolve()),
    "selection": {
        "lengths": target_config["lengths"],
        "trial_range": [0, int(target_config["trials_per_length"]) - 1],
    },
}
metadata["run_state"] = {
    "status": "completed",
    "expected_trials": expected,
    "completed_trials": expected,
    "remaining_trials": 0,
    "batch_size": None,
    "started_at": now,
    "updated_at": now,
    "completed_at": now,
    "parallel_fallback": False,
    "derived_without_recomputation": True,
}
metadata_path = target_path.with_suffix(".metadata.json")
temporary = metadata_path.with_suffix(metadata_path.suffix + ".tmp")
temporary.write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
temporary.replace(metadata_path)
print(f"DERIVED: {target_path} rows={expected}")
PY
  "$experiment_python" -m substitution_rank analyze --input "$target_output"
  validate_result "$target_config" "$target_output" 0
}

printf '\n[2/6] Run a multiprocessing preflight check on the formal corpus\n'
preflight_workers=1
if ((worker_count > 1)); then
  preflight_workers=2
fi
"$experiment_python" -m substitution_rank run \
  --config configs/smoke/formal_corpus_smoke.json \
  --train "${train_documents[@]}" \
  --test "${test_documents[@]}" \
  --workers "$preflight_workers" \
  --batch-size 1 \
  --output results/formal_minimum_smoke/unattended_preflight.csv
preflight_require_parallel=0
if ((preflight_workers > 1)); then
  preflight_require_parallel=1
fi
validate_result \
  configs/smoke/formal_corpus_smoke.json \
  results/formal_minimum_smoke/unattended_preflight.csv \
  "$preflight_require_parallel"

printf '\n[3/6] Run the main experiment\n'
run_compute_job \
  formal_minimum \
  configs/main/formal.json \
  results/formal_minimum.csv

printf '\n[4/6] Derive two strictly paired baselines from the main experiment\n'
derive_main_subset \
  configs/sensitivity/predefined_budget_restarts30.json \
  results/predefined_budget_restarts30.csv \
  "30-restart budget baseline selected from the matching main-experiment trials"
derive_main_subset \
  configs/sensitivity/predefined_order4.json \
  results/predefined_order4.csv \
  "4-gram model baseline selected from the matching main-experiment trials"

printf '\n[5/6] Run the four remaining robustness experiments\n'
for index in 1 2 3 4; do
  run_compute_job \
    "${computed_labels[$index]}" \
    "${computed_configs[$index]}" \
    "${computed_outputs[$index]}"
done

printf '\n[6/6] Generate summaries, thresholds, figures, and the final status manifest\n'
for index in "${!all_labels[@]}"; do
  label="${all_labels[$index]}"
  config_path="${all_configs[$index]}"
  output_path="${all_outputs[$index]}"
  "$experiment_python" -m substitution_rank analyze --input "$output_path"
  "$plot_python" -m substitution_rank plot \
    --summary "${output_path%.csv}_summary.csv" \
    --trials "$output_path" \
    --output-dir "results/${label}_figures"
  validate_result "$config_path" "$output_path" 0
done

status_path="results/all_formal_experiments_status.json"
status_args=()
for index in "${!all_labels[@]}"; do
  status_args+=(
    "${all_labels[$index]}"
    "${all_configs[$index]}"
    "${all_outputs[$index]}"
  )
done
"$experiment_python" - "$status_path" "${status_args[@]}" <<'PY'
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

status_path = Path(sys.argv[1])
items = []
arguments = sys.argv[2:]
assert len(arguments) % 3 == 0
for index in range(0, len(arguments), 3):
    label, config_name, output_name = arguments[index:index + 3]
    config_path = Path(config_name)
    output_path = Path(output_name)
    metadata_path = output_path.with_suffix(".metadata.json")
    summary_path = output_path.with_name(output_path.stem + "_summary.csv")
    threshold_path = output_path.with_name(output_path.stem + "_thresholds.json")
    with output_path.open(encoding="utf-8", newline="") as handle:
        row_count = sum(1 for _ in csv.DictReader(handle))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    items.append({
        "label": label,
        "config": str(config_path.resolve()),
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "output": str(output_path.resolve()),
        "output_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        "rows": row_count,
        "derived_without_recomputation": bool(
            metadata["run_state"].get("derived_without_recomputation", False)
        ),
        "metadata": str(metadata_path.resolve()),
        "summary": str(summary_path.resolve()),
        "thresholds": str(threshold_path.resolve()),
        "figures": str((Path("results") / f"{label}_figures").resolve()),
        "status": metadata["run_state"]["status"],
    })

payload = {
    "status": "completed",
    "completed_at": datetime.now(timezone.utc).isoformat(),
    "computed_unique_trials": 15200,
    "derived_baseline_rows": 2100,
    "total_result_rows": sum(item["rows"] for item in items),
    "experiments": items,
}
temporary = status_path.with_suffix(status_path.suffix + ".tmp")
temporary.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
temporary.replace(status_path)
print(f"FINAL STATUS: {status_path} total_rows={payload['total_result_rows']}")
PY

printf '%s\n' \
  "============================================================" \
  "All formal experiments, derived baselines, summaries, plots, and audits are complete." \
  "Final status: $status_path" \
  "Full log: $run_log" \
  "End time: $(date '+%Y-%m-%d %H:%M:%S')" \
  "============================================================"
