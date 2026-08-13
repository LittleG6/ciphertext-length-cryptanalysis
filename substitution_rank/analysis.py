"""从逐次记录生成 Hit@k、MRR、区间和阈值表。"""

from __future__ import annotations

from collections import defaultdict
import csv
import json
import math
from pathlib import Path
from typing import Any

from .metrics import mean, wilson_interval

DEFAULT_K_VALUES = (1, 5, 10, 50, 100, 1000)


def summarize(rows: list[dict[str, Any]], k_values: tuple[int, ...] = DEFAULT_K_VALUES) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["length"])].append(row)
    summary: list[dict[str, Any]] = []
    for length, group in sorted(grouped.items()):
        item: dict[str, Any] = {
            "length": length,
            "trials": len(group),
            "mrr": mean(
                1 / int(row["rank"]) if str(row.get("rank", "")) else 0.0
                for row in group
            ),
            "mean_score_gap": mean(float(row["score_gap"]) for row in group),
            "mean_wrong_score_mean": mean(float(row["wrong_score_mean"]) for row in group),
            "mean_wrong_score_median": mean(float(row["wrong_score_median"]) for row in group),
            "mean_wrong_score_std": mean(float(row["wrong_score_std"]) for row in group),
            "mean_true_score_percentile": mean(
                float(row["true_score_percentile"]) for row in group
            ),
            "mean_true_score_z": mean(float(row["true_score_z"]) for row in group),
            "mean_character_accuracy": mean(float(row["character_accuracy"]) for row in group),
            "mean_key_accuracy": mean(float(row["observed_key_accuracy"]) for row in group),
            "mean_seconds": mean(float(row["elapsed_seconds"]) for row in group),
        }
        for k in k_values:
            successes = sum(
                bool(str(row.get("rank", ""))) and int(row["rank"]) <= k for row in group
            )
            low, high = wilson_interval(successes, len(group))
            item[f"hit@{k}"] = successes / len(group)
            item[f"hit@{k}_low"] = low
            item[f"hit@{k}_high"] = high
        for label in ("top1_success", "scoring_failure", "search_failure"):
            item[f"proportion_{label}"] = sum(row["failure_type"] == label for row in group) / len(group)
        summary.append(item)
    return summary


def empirical_thresholds(
    summary: list[dict[str, Any]],
    k_values: tuple[int, ...] = DEFAULT_K_VALUES,
    targets: tuple[float, ...] = (0.90, 0.95),
) -> list[dict[str, Any]]:
    thresholds = []
    for k in k_values:
        for target in targets:
            point = next((r for r in summary if r[f"hit@{k}"] >= target), None)
            stable = next((r for r in summary if r[f"hit@{k}_low"] >= target), None)
            thresholds.append({
                "k": k,
                "target": target,
                "point_estimate_length": point["length"] if point else None,
                "wilson_supported_length": stable["length"] if stable else None,
            })
    return thresholds


def write_table(rows: list[dict[str, Any]], path: str | Path) -> None:
    if not rows:
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_summary(rows: list[dict[str, Any]], output_prefix: str | Path) -> tuple[Path, Path]:
    prefix = Path(output_prefix)
    result = summarize(rows)
    summary_path = prefix.with_name(prefix.name + "_summary.csv")
    threshold_path = prefix.with_name(prefix.name + "_thresholds.json")
    write_table(result, summary_path)
    threshold_path.write_text(
        json.dumps(empirical_thresholds(result), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary_path, threshold_path
