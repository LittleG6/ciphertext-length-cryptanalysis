#!/usr/bin/env python3
"""Run the four compact reviewer-response experiment groups with resume support."""

from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import traceback

from substitution_rank.experiment import ExperimentConfig
from substitution_rank.supplement import file_record, run_stage


ROOT = Path(__file__).resolve().parent.parent
CONFIG_ROOT = ROOT / "configs" / "reviewer_supplement_20260903"
RESULT_ROOT = ROOT / "results" / "reviewer_supplement_20260903"
TRAIN_PATHS = [
    ROOT / "corpus/formal_minimum/train/pg1342_pride_and_prejudice.txt",
    ROOT / "corpus/formal_minimum/train/pg1400_great_expectations.txt",
    ROOT / "corpus/formal_minimum/train/pg2701_moby_dick.txt",
    ROOT / "corpus/formal_minimum/train/pg1661_sherlock_holmes.txt",
    ROOT / "corpus/formal_minimum/train/pg84_frankenstein.txt",
    ROOT / "corpus/formal_minimum/train/pg345_dracula.txt",
    ROOT / "corpus/formal_minimum/train/pg74_tom_sawyer.txt",
    ROOT / "corpus/formal_minimum/train/pg1260_jane_eyre.txt",
]
FICTION_TEST_PATHS = [
    ROOT / "corpus/formal_minimum/test/pg35_time_machine.txt",
    ROOT / "corpus/formal_minimum/test/pg120_treasure_island.txt",
    ROOT / "corpus/formal_minimum/test/pg174_dorian_gray.txt",
    ROOT / "corpus/formal_minimum/test/pg55_wizard_of_oz.txt",
]
NONFICTION_TEST_PATHS = [
    ROOT / "corpus/reviewer_nonfiction_20260903/test/pg23_frederick_douglass.txt",
    ROOT / "corpus/reviewer_nonfiction_20260903/test/pg1228_origin_of_species.txt",
    ROOT / "corpus/reviewer_nonfiction_20260903/test/pg205_walden.txt",
    ROOT / "corpus/reviewer_nonfiction_20260903/test/pg148_franklin_autobiography.txt",
]
STAGES = (
    ("effort_original", "effort_original.json", FICTION_TEST_PATHS, ()),
    ("effort_controlled_hc", "effort_controlled_hc.json", FICTION_TEST_PATHS, (3, 4, 5)),
    ("search_controlled_sa", "search_controlled_sa.json", FICTION_TEST_PATHS, (3, 4, 5)),
    ("alpha_001", "alpha_001.json", FICTION_TEST_PATHS, ()),
    ("alpha_1", "alpha_1.json", FICTION_TEST_PATHS, ()),
    ("nonfiction_controlled_hc", "nonfiction_controlled_hc.json", NONFICTION_TEST_PATHS, ()),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def validate_stage(name: str, rows: list[dict[str, str]], config: ExperimentConfig) -> dict[str, object]:
    expected = len(config.lengths) * config.trials_per_length
    pairs = {(int(row["length"]), int(row["trial"])) for row in rows}
    if len(rows) != expected or len(pairs) != expected:
        raise ValueError(f"{name}: expected {expected} unique rows, found {len(rows)}/{len(pairs)}")
    controlled = config.search.proposal_scope == "non_neutral" and not config.search.early_stopping
    if controlled:
        expected_proposals = config.search.restarts * config.search.iterations
        for row in rows:
            if int(row["total_proposals"]) != expected_proposals:
                raise ValueError(f"{name}: effective proposal budget invariant failed")
            if int(row["neutral_proposals"]) != 0 or int(row["early_stopped_restarts"]) != 0:
                raise ValueError(f"{name}: neutral/early-stop control invariant failed")
            if int(row["score_calls"]) != expected_proposals + config.search.restarts + 1:
                raise ValueError(f"{name}: score-call invariant failed")
    if name in {"effort_controlled_hc", "search_controlled_sa"}:
        for row in rows:
            if row["rerank_order4_rank"] != row["rank"]:
                raise ValueError(f"{name}: order-4 fixed-pool rank does not reproduce source rank")
            if row["rerank_order4_oracle_rank"] != row["oracle_rank"]:
                raise ValueError(f"{name}: order-4 oracle rank does not reproduce source rank")
            if not row["candidate_pool_sha256"]:
                raise ValueError(f"{name}: missing candidate-pool digest")
    return {
        "rows": len(rows),
        "unique_tasks": len(pairs),
        "lengths": list(config.lengths),
        "controlled_budget_verified": controlled,
        "rerank_identity_verified": name in {"effort_controlled_hc", "search_controlled_sa"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=250)
    parser.add_argument("--stage", choices=["all", *(stage[0] for stage in STAGES)], default="all")
    parser.add_argument("--pilot-trials", type=int, default=0, help="use a separate pilot directory with N trials/length")
    args = parser.parse_args()
    if args.workers < 1 or args.batch_size < 1 or args.pilot_trials < 0:
        parser.error("workers/batch-size must be positive and pilot-trials non-negative")

    output_root = RESULT_ROOT / f"pilot_{args.pilot_trials}" if args.pilot_trials else RESULT_ROOT
    output_root.mkdir(parents=True, exist_ok=True)
    status_path = output_root / "status.json"
    selected = [stage for stage in STAGES if args.stage in {"all", stage[0]}]
    status: dict[str, object] = {
        "suite": "reviewer_supplement_20260903",
        "mode": "pilot" if args.pilot_trials else "formal",
        "status": "running",
        "current_stage": None,
        "started_at": utc_now(),
        "updated_at": utc_now(),
        "workers": args.workers,
        "batch_size": args.batch_size,
        "runner": file_record(Path(__file__)),
        "stages": {},
    }
    if status_path.exists():
        previous = json.loads(status_path.read_text(encoding="utf-8"))
        status["started_at"] = previous.get("started_at", status["started_at"])
        status["stages"] = previous.get("stages", {})
    write_json_atomic(status_path, status)

    try:
        for name, config_name, test_paths, rerank_orders in selected:
            config_path = CONFIG_ROOT / config_name
            config = ExperimentConfig.from_json(config_path)
            if args.pilot_trials:
                config = replace(config, trials_per_length=args.pilot_trials)
            status["current_stage"] = name
            status["updated_at"] = utc_now()
            status["stages"][name] = {
                "status": "running",
                "config": file_record(config_path),
                "started_at": utc_now(),
            }
            write_json_atomic(status_path, status)
            print(f"stage={name} status=starting", flush=True)
            rows = run_stage(
                name=name,
                config=config,
                train_paths=TRAIN_PATHS,
                test_paths=test_paths,
                output_path=output_root / f"{name}.csv",
                rerank_orders=rerank_orders,
                workers=args.workers,
                batch_size=args.batch_size,
                resume=True,
            )
            validation = validate_stage(name, rows, config)
            status["stages"][name].update({
                "status": "completed",
                "completed_at": utc_now(),
                "validation": validation,
            })
            status["updated_at"] = utc_now()
            write_json_atomic(status_path, status)
            print(f"stage={name} status=completed rows={len(rows)}", flush=True)
        status.update({
            "status": "completed",
            "current_stage": None,
            "updated_at": utc_now(),
            "completed_at": utc_now(),
        })
        write_json_atomic(status_path, status)
        print("suite status=completed", flush=True)
        return 0
    except BaseException as error:
        status.update({
            "status": "failed",
            "updated_at": utc_now(),
            "error": {"type": type(error).__name__, "message": str(error)},
        })
        if status.get("current_stage"):
            status["stages"][str(status["current_stage"])]["status"] = "failed"
        write_json_atomic(status_path, status)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
