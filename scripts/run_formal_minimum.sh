#!/usr/bin/env bash
set -euo pipefail

worker_count="${1:-1}"
batch_size="${2:-100}"
resume_mode="${3:-}"
if [[ -n "$resume_mode" && "$resume_mode" != "--resume" ]]; then
  echo "The third argument must be empty or --resume" >&2
  exit 2
fi

run_args=(
  --config configs/main/formal.json
  --train
  corpus/formal_minimum/train/pg1342_pride_and_prejudice.txt
  corpus/formal_minimum/train/pg1400_great_expectations.txt
  corpus/formal_minimum/train/pg2701_moby_dick.txt
  corpus/formal_minimum/train/pg1661_sherlock_holmes.txt
  corpus/formal_minimum/train/pg84_frankenstein.txt
  corpus/formal_minimum/train/pg345_dracula.txt
  corpus/formal_minimum/train/pg74_tom_sawyer.txt
  corpus/formal_minimum/train/pg1260_jane_eyre.txt
  --test
  corpus/formal_minimum/test/pg35_time_machine.txt
  corpus/formal_minimum/test/pg120_treasure_island.txt
  corpus/formal_minimum/test/pg174_dorian_gray.txt
  corpus/formal_minimum/test/pg55_wizard_of_oz.txt
  --workers "$worker_count"
  --batch-size "$batch_size"
  --output results/formal_minimum.csv
)
if [[ "$resume_mode" == "--resume" ]]; then
  run_args+=(--resume)
fi
python3 -m substitution_rank run "${run_args[@]}"
