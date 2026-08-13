"""命令行入口。"""

from __future__ import annotations

import argparse
import json
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
        f"workers: {args.workers}; output: {args.output}"
    )
    rows = run_experiment(
        read_documents(train_paths),
        read_documents(test_paths),
        config,
        args.output,
        workers=args.workers,
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
        description="单表代换密码正确解密 Top-k 排名实验",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="训练语言模型并运行逐次实验")
    run.add_argument("--config", default=PROJECT_ROOT / "config/pilot.json")
    run.add_argument("--train", nargs="+", help="训练文档路径（与测试文档不得重合）")
    run.add_argument("--test", nargs="+", help="测试文档路径")
    run.add_argument("--output", default=PROJECT_ROOT / "results/pilot.csv")
    run.add_argument("--workers", type=int, default=1)
    run.set_defaults(func=command_run)

    pilot = subparsers.add_parser("pilot", help="运行长度100并导出完整Top-100候选")
    pilot.add_argument("--config", default=PROJECT_ROOT / "config/pilot_single.json")
    pilot.add_argument("--train", nargs="+", help="训练文档路径（与测试文档不得重合）")
    pilot.add_argument("--test", nargs="+", help="测试文档路径")
    pilot.add_argument("--output-dir", default=PROJECT_ROOT / "results/pilot_length100")
    pilot.set_defaults(func=command_pilot)

    analyze = subparsers.add_parser("analyze", help="重新汇总已有逐次实验 CSV")
    analyze.add_argument("--input", required=True)
    analyze.add_argument("--output-prefix")
    analyze.set_defaults(func=command_analyze)

    plot = subparsers.add_parser("plot", help="从 summary.csv 生成论文图")
    plot.add_argument("--summary", required=True)
    plot.add_argument("--trials", help="逐次实验 CSV；提供后额外生成评分差距箱线图")
    plot.add_argument("--output-dir", default=PROJECT_ROOT / "results/figures")
    plot.set_defaults(func=command_plot)

    show = subparsers.add_parser("show-config", help="检查解析后的实验配置")
    show.add_argument("--config", default=PROJECT_ROOT / "config/pilot.json")
    show.set_defaults(func=command_show_config)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "workers", 1) < 1:
        parser.error("--workers must be at least 1")
    try:
        return args.func(args)
    except (ValueError, RuntimeError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
