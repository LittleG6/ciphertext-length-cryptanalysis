"""Command-line entry point."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
import sys

from .analysis import write_summary
from .experiment import (
    ExperimentConfig,
    read_csv,
    read_documents,
    run_experiment,
    run_single_pilot,
)
from .plotting import plot_summary


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _paths(values: list[str] | None, default: str) -> list[Path]:
    return [Path(value) for value in values] if values else [PROJECT_ROOT / default]


def _file_record(path: Path) -> dict[str, str]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
    }


def command_run(args: argparse.Namespace) -> int:
    config = ExperimentConfig.from_json(args.config)
    train_paths = _paths(args.train, "data/sample_train.txt")
    test_paths = _paths(args.test, "data/sample_test.txt")
    overlap = {path.resolve() for path in train_paths} & {path.resolve() for path in test_paths}
    if overlap:
        raise ValueError("training and test files must be document-disjoint")
    print(f"Training documents: {len(train_paths)}; test documents: {len(test_paths)}")
    print(
        f"Trials: {len(config.lengths) * config.trials_per_length}; "
        f"workers: {args.workers}; batch size: {args.batch_size}; "
        f"resume: {args.resume}; output: {args.output}"
    )
    source_paths = sorted((PROJECT_ROOT / "substitution_rank").glob("*.py"))
    rows = run_experiment(
        read_documents(train_paths),
        read_documents(test_paths),
        config,
        args.output,
        workers=args.workers,
        metadata_extra={
            "workers_requested": args.workers,
            "command": sys.argv,
            "runtime": {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "machine": platform.machine(),
                "processor": platform.processor(),
            },
            "config": _file_record(Path(args.config)),
            "training_documents": [_file_record(path) for path in train_paths],
            "test_documents": [_file_record(path) for path in test_paths],
            "source_files": [_file_record(path) for path in source_paths],
        },
        batch_size=args.batch_size,
        resume=args.resume,
    )
    prefix = Path(args.output).with_suffix("")
    summary_path, threshold_path = write_summary(rows, prefix)
    print(f"Completed. Summary: {summary_path}; thresholds: {threshold_path}")
    return 0


def command_analyze(args: argparse.Namespace) -> int:
    rows = read_csv(args.input)
    prefix = Path(args.output_prefix) if args.output_prefix else Path(args.input).with_suffix("")
    summary_path, threshold_path = write_summary(rows, prefix)
    print(f"Wrote {summary_path} and {threshold_path}")
    return 0


def command_pilot(args: argparse.Namespace) -> int:
    config = ExperimentConfig.from_json(args.config)
    train_paths = _paths(args.train, "data/sample_train.txt")
    test_paths = _paths(args.test, "data/sample_test.txt")
    overlap = {path.resolve() for path in train_paths} & {path.resolve() for path in test_paths}
    if overlap:
        raise ValueError("training and test files must be document-disjoint")
    paths = run_single_pilot(
        read_documents(train_paths),
        read_documents(test_paths),
        config,
        args.output_dir,
    )
    print("Pilot files: " + ", ".join(str(path) for path in paths))
    return 0


def command_plot(args: argparse.Namespace) -> int:
    paths = plot_summary(args.summary, args.output_dir, args.trials)
    print("Created: " + ", ".join(str(path) for path in paths))
    return 0


def command_show_config(args: argparse.Namespace) -> int:
    config = ExperimentConfig.from_json(args.config)
    print(json.dumps({**config.__dict__, "search": config.search.__dict__}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="subrank",
        description="Top-k ranking experiments for correct plaintexts in monoalphabetic substitution ciphers",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Train the language model and run individual trials")
    run.add_argument("--config", default=PROJECT_ROOT / "configs/pilot/pilot_100_trials_per_length.json")
    run.add_argument("--train", nargs="+", help="Training document paths (must be disjoint from test documents)")
    run.add_argument("--test", nargs="+", help="Test document paths")
    run.add_argument("--output", default=PROJECT_ROOT / "results/pilot.csv")
    run.add_argument("--workers", type=int, default=1)
    run.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of completed trials between checkpoints (default: 100)",
    )
    run.add_argument(
        "--resume",
        action="store_true",
        help="Skip completed (length, trial) pairs using the same CSV and metadata",
    )
    run.set_defaults(func=command_run)

    pilot = subparsers.add_parser("pilot", help="Run a trial at length 100 and export all Top-100 candidates")
    pilot.add_argument("--config", default=PROJECT_ROOT / "configs/pilot/pilot_length100_one_trial.json")
    pilot.add_argument("--train", nargs="+", help="Training document paths (must be disjoint from test documents)")
    pilot.add_argument("--test", nargs="+", help="Test document paths")
    pilot.add_argument("--output-dir", default=PROJECT_ROOT / "results/pilot_length100")
    pilot.set_defaults(func=command_pilot)

    analyze = subparsers.add_parser("analyze", help="Recompute summaries from an existing trial CSV")
    analyze.add_argument("--input", required=True)
    analyze.add_argument("--output-prefix")
    analyze.set_defaults(func=command_analyze)

    plot = subparsers.add_parser("plot", help="Generate paper figures from summary.csv")
    plot.add_argument("--summary", required=True)
    plot.add_argument("--trials", help="Trial CSV; when provided, also generate a score-gap box plot")
    plot.add_argument("--output-dir", default=PROJECT_ROOT / "results/figures")
    plot.set_defaults(func=command_plot)

    show = subparsers.add_parser("show-config", help="Inspect the parsed experiment configuration")
    show.add_argument("--config", default=PROJECT_ROOT / "configs/pilot/pilot_100_trials_per_length.json")
    show.set_defaults(func=command_show_config)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "workers", 1) < 1:
        parser.error("--workers must be at least 1")
    if getattr(args, "batch_size", 1) < 1:
        parser.error("--batch-size must be at least 1")
    try:
        return args.func(args)
    except (ValueError, RuntimeError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
