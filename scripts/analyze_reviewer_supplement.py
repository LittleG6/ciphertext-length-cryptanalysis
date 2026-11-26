#!/usr/bin/env python3
"""Validate and summarize the four reviewer-supplement experiment groups."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import statistics
from substitution_rank.metrics import wilson_interval


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RESULT_ROOT = ROOT / "results" / "reviewer_supplement_20260903"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def rank_success(row: dict[str, str], column: str, k: int) -> int:
    value = row.get(column, "").strip()
    return int(bool(value) and int(value) <= k)


def rank_reciprocal(row: dict[str, str], column: str) -> float:
    value = row.get(column, "").strip()
    return 1.0 / int(value) if value else 0.0


def mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else float("nan")


def normal_mean_ci(values: list[float]) -> tuple[float, float, float]:
    estimate = mean(values)
    if len(values) < 2:
        return estimate, float("nan"), float("nan")
    margin = 1.959963984540054 * statistics.stdev(values) / math.sqrt(len(values))
    return estimate, estimate - margin, estimate + margin


def mcnemar_exact_p(a_only: int, b_only: int) -> float:
    discordant = a_only + b_only
    if discordant == 0:
        return 1.0
    tail = sum(math.comb(discordant, i) for i in range(min(a_only, b_only) + 1)) / 2**discordant
    return min(1.0, 2 * tail)


def add_holm(rows: list[dict[str, object]]) -> None:
    indexed = sorted(enumerate(rows), key=lambda item: float(item[1]["p_value_raw"]))
    running = 0.0
    count = len(rows)
    for position, (index, row) in enumerate(indexed):
        adjusted = min(1.0, (count - position) * float(row["p_value_raw"]))
        running = max(running, adjusted)
        rows[index]["p_value_holm"] = running


def stage_summary(stage: str, rows: list[dict[str, str]], rank_column: str = "rank") -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for length in sorted({int(row["length"]) for row in rows}):
        group = [row for row in rows if int(row["length"]) == length]
        hit1 = sum(rank_success(row, rank_column, 1) for row in group)
        hit10 = sum(rank_success(row, rank_column, 10) for row in group)
        hit1_low, hit1_high = wilson_interval(hit1, len(group))
        hit10_low, hit10_high = wilson_interval(hit10, len(group))
        output.append({
            "stage": stage,
            "rank_column": rank_column,
            "length": length,
            "trials": len(group),
            "hit@1": hit1 / len(group),
            "hit@1_low": hit1_low,
            "hit@1_high": hit1_high,
            "hit@10": hit10 / len(group),
            "hit@10_low": hit10_low,
            "hit@10_high": hit10_high,
            "mrr": mean([rank_reciprocal(row, rank_column) for row in group]),
            "mean_total_proposals": mean([float(row["total_proposals"]) for row in group]),
            "mean_neutral_fraction": mean([float(row["neutral_proposal_fraction"]) for row in group]),
            "mean_early_stopped_restarts": mean([float(row["early_stopped_restarts"]) for row in group]),
            "mean_distinct_plaintexts": mean([float(row["distinct_plaintexts_visited"]) for row in group]),
            "mean_score_calls": mean([float(row["score_calls"]) for row in group]),
            "mean_seconds": mean([float(row["elapsed_seconds"]) for row in group]),
        })
    return output


def paired_binary_rows(
    comparison: str,
    baseline: list[dict[str, str]],
    alternative: list[dict[str, str]],
    columns: list[tuple[str, str, int]],
) -> list[dict[str, object]]:
    return paired_binary_column_rows(
        comparison,
        baseline,
        alternative,
        [(label, column, column, k) for label, column, k in columns],
    )


def paired_binary_column_rows(
    comparison: str,
    baseline: list[dict[str, str]],
    alternative: list[dict[str, str]],
    columns: list[tuple[str, str, str, int]],
) -> list[dict[str, object]]:
    base_map = {(int(row["length"]), int(row["trial"])): row for row in baseline}
    alt_map = {(int(row["length"]), int(row["trial"])): row for row in alternative}
    output: list[dict[str, object]] = []
    for length in sorted({key[0] for key in base_map} & {key[0] for key in alt_map}):
        keys = sorted(key for key in base_map if key[0] == length and key in alt_map)
        for label, baseline_column, alternative_column, k in columns:
            pairs = [
                (
                    rank_success(base_map[key], baseline_column, k),
                    rank_success(alt_map[key], alternative_column, k),
                )
                for key in keys
            ]
            differences = [alternative_value - baseline_value for baseline_value, alternative_value in pairs]
            estimate, low, high = normal_mean_ci(differences)
            base_only = sum(base_value == 1 and alt_value == 0 for base_value, alt_value in pairs)
            alt_only = sum(base_value == 0 and alt_value == 1 for base_value, alt_value in pairs)
            output.append({
                "comparison": comparison,
                "length": length,
                "metric": label,
                "pairs": len(pairs),
                "baseline_rate": mean([float(pair[0]) for pair in pairs]),
                "alternative_rate": mean([float(pair[1]) for pair in pairs]),
                "paired_difference_alt_minus_base": estimate,
                "difference_low": low,
                "difference_high": high,
                "baseline_only_successes": base_only,
                "alternative_only_successes": alt_only,
                "p_value_raw": mcnemar_exact_p(base_only, alt_only),
            })
    add_holm(output)
    return output


def effort_paired_rows(
    baseline: list[dict[str, str]], alternative: list[dict[str, str]]
) -> list[dict[str, object]]:
    base_map = {(int(row["length"]), int(row["trial"])): row for row in baseline}
    alt_map = {(int(row["length"]), int(row["trial"])): row for row in alternative}
    metrics = [
        "total_proposals",
        "neutral_proposal_fraction",
        "early_stopped_restarts",
        "distinct_plaintexts_visited",
        "score_calls",
        "elapsed_seconds",
    ]
    output: list[dict[str, object]] = []
    for length in sorted({key[0] for key in base_map} & {key[0] for key in alt_map}):
        keys = sorted(key for key in base_map if key[0] == length and key in alt_map)
        for metric in metrics:
            baseline_values = [float(base_map[key][metric]) for key in keys]
            alternative_values = [float(alt_map[key][metric]) for key in keys]
            differences = [alt - base for base, alt in zip(baseline_values, alternative_values)]
            estimate, low, high = normal_mean_ci(differences)
            output.append({
                "length": length,
                "metric": metric,
                "pairs": len(keys),
                "baseline_mean": mean(baseline_values),
                "controlled_mean": mean(alternative_values),
                "paired_difference_controlled_minus_original": estimate,
                "difference_low": low,
                "difference_high": high,
            })
    return output


def independent_domain_rows(
    fiction: list[dict[str, str]], nonfiction: list[dict[str, str]]
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for length in sorted({int(row["length"]) for row in nonfiction}):
        a = [row for row in fiction if int(row["length"]) == length]
        b = [row for row in nonfiction if int(row["length"]) == length]
        for label, k in (("hit@1", 1), ("hit@10", 10)):
            pa = mean([float(rank_success(row, "rank", k)) for row in a])
            pb = mean([float(rank_success(row, "rank", k)) for row in b])
            difference = pb - pa
            se = math.sqrt(pa * (1 - pa) / len(a) + pb * (1 - pb) / len(b))
            margin = 1.959963984540054 * se
            output.append({
                "length": length,
                "metric": label,
                "fiction_trials": len(a),
                "nonfiction_trials": len(b),
                "fiction_rate": pa,
                "nonfiction_rate": pb,
                "difference_nonfiction_minus_fiction": difference,
                "difference_low": difference - margin,
                "difference_high": difference + margin,
                "interval_method": "independent Wald 95% CI; domain samples are not treated as paired",
            })
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-root", type=Path, default=DEFAULT_RESULT_ROOT)
    args = parser.parse_args()
    result_root = args.result_root.resolve()
    names = [
        "effort_original",
        "effort_controlled_hc",
        "search_controlled_sa",
        "alpha_001",
        "alpha_1",
        "nonfiction_controlled_hc",
    ]
    tables = {name: read_rows(result_root / f"{name}.csv") for name in names}
    metadata_checks = {}
    for name in names:
        metadata = json.loads((result_root / f"{name}.metadata.json").read_text(encoding="utf-8"))
        state = metadata["run_state"]
        metadata_checks[name] = {
            "status": state["status"],
            "rows": len(tables[name]),
            "expected_trials": state["expected_trials"],
            "parallel_fallback": state["parallel_fallback"],
            "protocol_sha256": metadata["protocol_sha256"],
        }
        if state["status"] != "completed" or state["parallel_fallback"]:
            raise ValueError(f"invalid completion metadata for {name}")
        if len(tables[name]) != int(state["expected_trials"]):
            raise ValueError(f"row-count mismatch for {name}")

    summaries: list[dict[str, object]] = []
    for name, rows in tables.items():
        summaries.extend(stage_summary(name, rows))
    rerank_summaries: list[dict[str, object]] = []
    for name in ("effort_controlled_hc", "search_controlled_sa"):
        for order in (3, 4, 5):
            rerank_summaries.extend(stage_summary(name, tables[name], f"rerank_order{order}_rank"))

    effort_rows = effort_paired_rows(tables["effort_original"], tables["effort_controlled_hc"])
    effort_outcome_rows = paired_binary_rows(
        "controlled_hc_minus_original_hc",
        tables["effort_original"],
        tables["effort_controlled_hc"],
        [("hit@1", "rank", 1), ("hit@10", "rank", 10)],
    )
    searcher_rows: list[dict[str, object]] = []
    for order in (3, 4, 5):
        searcher_rows.extend(paired_binary_rows(
            f"controlled_sa_minus_controlled_hc_order{order}",
            tables["effort_controlled_hc"],
            tables["search_controlled_sa"],
            [("hit@1", f"rerank_order{order}_rank", 1), ("hit@10", f"rerank_order{order}_rank", 10)],
        ))
    add_holm(searcher_rows)
    reranker_rows: list[dict[str, object]] = []
    for name in ("effort_controlled_hc", "search_controlled_sa"):
        for alternative_order in (3, 5):
            reranker_rows.extend(paired_binary_column_rows(
                f"{name}_order{alternative_order}_minus_order4_same_pool",
                tables[name],
                tables[name],
                [
                    ("hit@1", "rerank_order4_rank", f"rerank_order{alternative_order}_rank", 1),
                    ("hit@10", "rerank_order4_rank", f"rerank_order{alternative_order}_rank", 10),
                ],
            ))
    add_holm(reranker_rows)
    alpha_rows = paired_binary_rows(
        "alpha_001_minus_alpha_01",
        tables["effort_controlled_hc"],
        tables["alpha_001"],
        [("hit@1", "rank", 1), ("hit@10", "rank", 10)],
    ) + paired_binary_rows(
        "alpha_1_minus_alpha_01",
        tables["effort_controlled_hc"],
        tables["alpha_1"],
        [("hit@1", "rank", 1), ("hit@10", "rank", 10)],
    )
    add_holm(alpha_rows)
    domain_rows = independent_domain_rows(
        tables["effort_controlled_hc"], tables["nonfiction_controlled_hc"]
    )

    summary_root = result_root / "summary"
    write_rows(summary_root / "stage_summary.csv", summaries)
    write_rows(summary_root / "fixed_pool_rerank_summary.csv", rerank_summaries)
    write_rows(summary_root / "effort_paired_differences.csv", effort_rows)
    write_rows(summary_root / "effort_outcome_paired_differences.csv", effort_outcome_rows)
    write_rows(summary_root / "searcher_paired_differences.csv", searcher_rows)
    write_rows(summary_root / "reranker_same_pool_paired_differences.csv", reranker_rows)
    write_rows(summary_root / "alpha_paired_differences.csv", alpha_rows)
    write_rows(summary_root / "domain_comparison.csv", domain_rows)

    report = {
        "suite": "reviewer_supplement_20260903",
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "result_root": str(result_root),
        "completion_checks": metadata_checks,
        "design": {
            "group_1": "original versus observed-symbol, no-early-stop hill climbing at 4 lengths",
            "group_2": "controlled hill climbing versus simulated annealing; each fixed Top-1000 pool reranked by 3/4/5-gram scorers",
            "group_3": "alpha 0.01 and 1.0 versus paired alpha 0.1 controlled baseline",
            "group_4": "four-work nonfiction test corpus versus four-work fiction baseline with training model fixed",
            "paired_interval": "normal 95% CI on paired differences",
            "binary_test": "exact McNemar with Holm adjustment within reported families",
        },
        "files": {
            "stage_summary": "summary/stage_summary.csv",
            "fixed_pool_rerank_summary": "summary/fixed_pool_rerank_summary.csv",
            "effort_paired_differences": "summary/effort_paired_differences.csv",
            "effort_outcome_paired_differences": "summary/effort_outcome_paired_differences.csv",
            "searcher_paired_differences": "summary/searcher_paired_differences.csv",
            "reranker_same_pool_paired_differences": "summary/reranker_same_pool_paired_differences.csv",
            "alpha_paired_differences": "summary/alpha_paired_differences.csv",
            "domain_comparison": "summary/domain_comparison.csv",
        },
    }
    (result_root / "final_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"analysis status=completed stages={len(names)} rows={sum(len(rows) for rows in tables.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
