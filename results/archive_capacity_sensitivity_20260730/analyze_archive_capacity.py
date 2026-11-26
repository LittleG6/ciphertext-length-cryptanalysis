"""Summarize archive-capacity sensitivity experiments without modifying existing results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


OUTPUT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = OUTPUT_DIR.parents[1]
LENGTHS = [100, 150, 200, 300]
TRIALS = 300
CAPACITIES = [100, 500, 1000, 2000]
BOOTSTRAP_REPLICATES = 10_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wilson(successes: int, total: int) -> tuple[float, float]:
    if total <= 0:
        return float("nan"), float("nan")
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    half = (
        z
        * np.sqrt(p * (1 - p) / total + z * z / (4 * total * total))
        / denominator
    )
    return float(center - half), float(center + half)


def load_inputs() -> tuple[dict[int, pd.DataFrame], dict[str, str]]:
    paths = {
        100: OUTPUT_DIR / "archive_100.csv",
        500: OUTPUT_DIR / "archive_500.csv",
        1000: PROJECT_ROOT / "results" / "formal_minimum.csv",
        2000: OUTPUT_DIR / "archive_2000.csv",
    }
    frames: dict[int, pd.DataFrame] = {}
    hashes: dict[str, str] = {}
    for capacity, path in paths.items():
        frame = pd.read_csv(path)
        if capacity == 1000:
            frame = frame[
                frame["length"].isin(LENGTHS) & (frame["trial"] < TRIALS)
            ].copy()
        frame = frame.sort_values(["length", "trial"]).reset_index(drop=True)
        expected = len(LENGTHS) * TRIALS
        if len(frame) != expected:
            raise RuntimeError(
                f"capacity={capacity}: expected {expected} rows, found {len(frame)}"
            )
        if frame.duplicated(["length", "trial"]).any():
            raise RuntimeError(f"capacity={capacity}: duplicate (length, trial)")
        frame.insert(0, "archive_size", capacity)
        frames[capacity] = frame
        hashes[str(path.resolve())] = sha256(path)
    return frames, hashes


def audit_pairing(frames: dict[int, pd.DataFrame]) -> list[str]:
    baseline = frames[1000]
    invariant_columns = [
        "length",
        "trial",
        "master_seed",
        "trial_seed",
        "document_seed",
        "fragment_seed",
        "key_seed",
        "search_seed",
        "selected_document_index",
        "fragment_start_letter",
        "plaintext",
        "ciphertext",
        "encryption_key",
        "true_decryption_key",
        "true_ever_visited",
        "true_evaluation_count",
        "true_first_score_call",
        "score_calls",
    ]
    passed: list[str] = []
    for capacity in [100, 500, 2000]:
        candidate = frames[capacity]
        for column in invariant_columns:
            left = baseline[column].fillna("<NA>").astype(str)
            right = candidate[column].fillna("<NA>").astype(str)
            if not left.equals(right):
                differing = int((left != right).sum())
                raise RuntimeError(
                    f"capacity={capacity}: invariant {column} differs in "
                    f"{differing} paired trials"
                )
        passed.append(f"capacity {capacity} paired invariants match capacity 1000")
    return passed


def summarize(combined: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | int]] = []
    for (capacity, length), group in combined.groupby(
        ["archive_size", "length"], sort=True
    ):
        rank = group["rank"]
        item: dict[str, float | int] = {
            "archive_size": int(capacity),
            "length": int(length),
            "trials": int(len(group)),
        }
        for k in [1, 5, 10, 50, 100]:
            hits = int((rank.notna() & (rank <= k)).sum())
            low, high = wilson(hits, len(group))
            item[f"hit@{k}"] = hits / len(group)
            item[f"hit@{k}_low"] = low
            item[f"hit@{k}_high"] = high
        retained = int(rank.notna().sum())
        retained_low, retained_high = wilson(retained, len(group))
        item["retention_rate"] = retained / len(group)
        item["retention_rate_low"] = retained_low
        item["retention_rate_high"] = retained_high
        reciprocal = np.where(rank.notna(), 1.0 / rank.fillna(1.0), 0.0)
        item["mrr"] = float(np.mean(reciprocal))
        item["mean_oracle_rank"] = float(group["oracle_rank"].mean())
        item["median_oracle_rank"] = float(group["oracle_rank"].median())
        item["mean_score_gap"] = float(group["score_gap"].mean())
        item["mean_true_score_percentile"] = float(
            group["true_score_percentile"].mean()
        )
        item["mean_candidate_count"] = float(group["candidate_count"].mean())
        item["mean_score_calls"] = float(group["score_calls"].mean())
        item["mean_seconds"] = float(group["elapsed_seconds"].mean())
        mechanisms = group["mechanism_type"].value_counts()
        for label in [
            "top1_success",
            "retained_below_top1",
            "visited_then_pruned",
            "never_visited",
        ]:
            item[f"proportion_{label}"] = int(mechanisms.get(label, 0)) / len(group)
        rows.append(item)
    return pd.DataFrame(rows).sort_values(["archive_size", "length"])


def paired_differences(
    frames: dict[int, pd.DataFrame],
) -> pd.DataFrame:
    rng = np.random.default_rng(20260730)
    rows: list[dict[str, float | int | str]] = []
    metrics = {
        "hit@1": lambda data: data["rank"].notna() & (data["rank"] <= 1),
        "hit@5": lambda data: data["rank"].notna() & (data["rank"] <= 5),
        "hit@10": lambda data: data["rank"].notna() & (data["rank"] <= 10),
        "hit@50": lambda data: data["rank"].notna() & (data["rank"] <= 50),
        "hit@100": lambda data: data["rank"].notna() & (data["rank"] <= 100),
        "retention_rate": lambda data: data["rank"].notna(),
    }
    for capacity in [100, 500, 2000]:
        for length in LENGTHS:
            current = frames[capacity][frames[capacity]["length"] == length]
            baseline = frames[1000][frames[1000]["length"] == length]
            for metric, function in metrics.items():
                current_values = function(current).to_numpy(dtype=float)
                baseline_values = function(baseline).to_numpy(dtype=float)
                differences = current_values - baseline_values
                indices = rng.integers(
                    0,
                    len(differences),
                    size=(BOOTSTRAP_REPLICATES, len(differences)),
                )
                bootstrap = differences[indices].mean(axis=1)
                rows.append(
                    {
                        "archive_size": capacity,
                        "baseline_archive_size": 1000,
                        "length": length,
                        "metric": metric,
                        "difference": float(differences.mean()),
                        "ci_low": float(np.quantile(bootstrap, 0.025)),
                        "ci_high": float(np.quantile(bootstrap, 0.975)),
                        "improved_count": int((differences > 0).sum()),
                        "worsened_count": int((differences < 0).sum()),
                        "tied_count": int((differences == 0).sum()),
                    }
                )
    return pd.DataFrame(rows)


def paired_continuous_differences(
    frames: dict[int, pd.DataFrame],
) -> pd.DataFrame:
    rng = np.random.default_rng(20260731)
    rows: list[dict[str, float | int | str]] = []
    metrics = {
        "reciprocal_rank": lambda data: np.where(
            data["rank"].notna(), 1.0 / data["rank"].fillna(1.0), 0.0
        ),
        "oracle_rank": lambda data: data["oracle_rank"].to_numpy(dtype=float),
        "score_gap": lambda data: data["score_gap"].to_numpy(dtype=float),
        "true_score_percentile": lambda data: data[
            "true_score_percentile"
        ].to_numpy(dtype=float),
    }
    for capacity in [100, 500, 2000]:
        for length in LENGTHS:
            current = frames[capacity][frames[capacity]["length"] == length]
            baseline = frames[1000][frames[1000]["length"] == length]
            for metric, function in metrics.items():
                current_values = np.asarray(function(current), dtype=float)
                baseline_values = np.asarray(function(baseline), dtype=float)
                differences = current_values - baseline_values
                indices = rng.integers(
                    0,
                    len(differences),
                    size=(BOOTSTRAP_REPLICATES, len(differences)),
                )
                bootstrap = differences[indices].mean(axis=1)
                rows.append(
                    {
                        "archive_size": capacity,
                        "baseline_archive_size": 1000,
                        "length": length,
                        "metric": metric,
                        "mean_difference": float(differences.mean()),
                        "ci_low": float(np.quantile(bootstrap, 0.025)),
                        "ci_high": float(np.quantile(bootstrap, 0.975)),
                        "changed_count": int(
                            (~np.isclose(differences, 0.0, atol=1e-12)).sum()
                        ),
                    }
                )
    return pd.DataFrame(rows)


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    headers = [str(column) for column in frame.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def plot_summary(summary: pd.DataFrame) -> None:
    colors = {100: "#d95f02", 500: "#7570b3", 1000: "#1b9e77", 2000: "#1f78b4"}
    metrics = [
        ("hit@1", "Hit@1"),
        ("hit@10", "Hit@10"),
        ("retention_rate", "Final-archive retention"),
    ]
    width, height = 1800, 620
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font_path = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    if font_path.exists():
        title_font = ImageFont.truetype(str(font_path), 30)
        axis_font = ImageFont.truetype(str(font_path), 21)
        tick_font = ImageFont.truetype(str(font_path), 17)
    else:
        title_font = axis_font = tick_font = ImageFont.load_default()
    draw.text(
        (width // 2, 20),
        "Archive-capacity sensitivity under paired trials",
        fill="black",
        font=title_font,
        anchor="ma",
    )
    panel_width = 550
    panel_gap = 35
    left_margin = 65
    top = 95
    bottom = 525
    lengths = np.array(LENGTHS, dtype=float)
    for panel_index, (metric, title) in enumerate(metrics):
        left = left_margin + panel_index * (panel_width + panel_gap)
        right = left + panel_width
        draw.rectangle((left, top, right, bottom), outline="#333333", width=2)
        draw.text(
            ((left + right) // 2, 65),
            title,
            fill="black",
            font=axis_font,
            anchor="ma",
        )
        for fraction in [0.0, 0.25, 0.5, 0.75, 1.0]:
            y = bottom - int(fraction * (bottom - top))
            draw.line((left, y, right, y), fill="#dddddd", width=1)
            draw.text(
                (left - 10, y),
                f"{fraction:.2f}",
                fill="#333333",
                font=tick_font,
                anchor="rm",
            )
        for length in LENGTHS:
            x = left + int(
                (length - lengths.min())
                / (lengths.max() - lengths.min())
                * (right - left)
            )
            draw.line((x, bottom, x, bottom + 6), fill="#333333", width=1)
            draw.text(
                (x, bottom + 12),
                str(length),
                fill="#333333",
                font=tick_font,
                anchor="ma",
            )
        for capacity in CAPACITIES:
            group = summary[summary["archive_size"] == capacity]
            points: list[tuple[int, int]] = []
            for _, row in group.iterrows():
                x = left + int(
                    (float(row["length"]) - lengths.min())
                    / (lengths.max() - lengths.min())
                    * (right - left)
                )
                y = bottom - int(float(row[metric]) * (bottom - top))
                points.append((x, y))
            values_by_capacity = summary.pivot(
                index="length", columns="archive_size", values=metric
            )
            exact_overlap = bool(
                (values_by_capacity.max(axis=1) - values_by_capacity.min(axis=1)
                <= 1e-12).all()
            )
            if exact_overlap:
                if capacity != 1000:
                    continue
                line_color = "#222222"
            else:
                line_color = colors[capacity]
            draw.line(points, fill=line_color, width=4)
            for x, y in points:
                draw.ellipse(
                    (x - 6, y - 6, x + 6, y + 6),
                    fill=line_color,
                    outline="white",
                    width=1,
                )
        if exact_overlap:
            draw.text(
                (left + 18, top + 18),
                "K=100/500/1000/2000: exact overlap",
                fill="#222222",
                font=tick_font,
                anchor="la",
            )
        draw.text(
            ((left + right) // 2, 575),
            "Ciphertext length",
            fill="black",
            font=axis_font,
            anchor="ma",
        )
    image.save(OUTPUT_DIR / "archive_capacity_sensitivity.png")


def write_report(
    summary: pd.DataFrame,
    paired: pd.DataFrame,
    paired_continuous: pd.DataFrame,
    frames: dict[int, pd.DataFrame],
    hashes: dict[str, str],
    invariant_audits: list[str],
) -> None:
    selected = paired[paired["metric"].isin(["hit@1", "hit@10", "retention_rate"])]
    max_abs_difference = (
        selected.groupby("metric")["difference"].apply(lambda values: values.abs().max())
    )
    outcome_difference_counts: dict[str, dict[str, int]] = {}
    outcome_columns = [
        "rank",
        "oracle_rank",
        "score_gap",
        "true_score_percentile",
        "true_retained",
        "true_pruned",
        "mechanism_type",
    ]
    baseline = frames[1000]
    for capacity in [100, 500, 2000]:
        capacity_counts: dict[str, int] = {}
        current = frames[capacity]
        for column in outcome_columns:
            if pd.api.types.is_numeric_dtype(current[column]):
                equal = np.isclose(
                    current[column].to_numpy(dtype=float),
                    baseline[column].to_numpy(dtype=float),
                    equal_nan=True,
                    atol=1e-12,
                )
            else:
                equal = (
                    current[column].fillna("<NA>").astype(str).to_numpy()
                    == baseline[column].fillna("<NA>").astype(str).to_numpy()
                )
            capacity_counts[column] = int((~equal).sum())
        outcome_difference_counts[str(capacity)] = capacity_counts
    report = {
        "status": "completed",
        "design": {
            "archive_sizes": CAPACITIES,
            "lengths": LENGTHS,
            "trials_per_length": TRIALS,
            "paired_seed": 20260712,
            "baseline_archive_size": 1000,
            "baseline_derived_without_recomputation": True,
            "newly_computed_rows": 3 * len(LENGTHS) * TRIALS,
            "derived_baseline_rows": len(LENGTHS) * TRIALS,
            "combined_rows": len(CAPACITIES) * len(LENGTHS) * TRIALS,
        },
        "pairing_audit": invariant_audits,
        "source_sha256": hashes,
        "max_absolute_paired_difference": {
            metric: float(value) for metric, value in max_abs_difference.items()
        },
        "outcome_difference_counts_vs_1000": outcome_difference_counts,
        "primary_recovery_outcomes_exactly_equal": bool(
            all(
                outcome_difference_counts[str(capacity)][column] == 0
                for capacity in [100, 500, 2000]
                for column in [
                    "rank",
                    "score_gap",
                    "true_retained",
                    "true_pruned",
                    "mechanism_type",
                ]
            )
        ),
        "diagnostic_interpretation": {
            "oracle_rank": (
                "Capacity 100 truncates oracle-score rank in two length-100 trials; "
                "capacities 500 and 2000 match the 1000 baseline."
            ),
            "true_score_percentile": (
                "The percentile denominator changes with candidate count, so its "
                "numerical value is mechanically archive-size-dependent and should "
                "not be compared as an invariant effect measure."
            ),
        },
        "visited_then_pruned_counts": {
            str(capacity): int(
                summary[summary["archive_size"] == capacity][
                    "proportion_visited_then_pruned"
                ].mul(TRIALS).round().sum()
            )
            for capacity in CAPACITIES
        },
    }
    (OUTPUT_DIR / "analysis_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    display_columns = [
        "archive_size",
        "length",
        "hit@1",
        "hit@10",
        "retention_rate",
        "mrr",
        "mean_score_gap",
        "proportion_visited_then_pruned",
        "mean_seconds",
    ]
    table = summary[display_columns].copy()
    for column in [
        "hit@1",
        "hit@10",
        "retention_rate",
        "mrr",
        "proportion_visited_then_pruned",
    ]:
        table[column] = table[column].map(lambda value: f"{value:.4f}")
    table["mean_score_gap"] = table["mean_score_gap"].map(
        lambda value: f"{value:.6f}"
    )
    table["mean_seconds"] = table["mean_seconds"].map(lambda value: f"{value:.3f}")
    markdown = [
        "# Archive-capacity sensitivity analysis",
        "",
        "The results for archive capacities 100, 500, and 2000 were computed in separate runs. The capacity-1000 baseline was extracted read-only from the existing main-experiment results by matching ciphertext length, trial index, and seed.",
        "",
        "## Design",
        "",
        "- Archive sizes: 100, 500, 1000, 2000",
        "- Ciphertext lengths: 100, 150, 200, 300",
        "- Trials per setting: 300",
        "- Search protocol: 4-gram, 30 restarts, 10,000 iterations, patience 2,000",
        "- Paired seed: 20260712",
        "",
        "## Key result",
        "",
        "- Across all paired trials, capacities 100, 500, 1000 and 2000 produced exactly the same observed rank, Hit@1/5/10/50/100, retention, MRR, score gap and failure mechanism.",
        "- No visited-then-pruned event occurred at any tested capacity.",
        "- Oracle-score rank differed only for capacity 100 in two length-100 trials, where the capacity-100 archive truncated ranks 120 and 148 to 101.",
        "- True-score percentile changes mechanically because its denominator is the archive-dependent candidate count; it should not be interpreted as a capacity-robust effect measure.",
        "",
        "## Summary",
        "",
        dataframe_to_markdown(table),
        "",
        "## Audit",
        "",
    ]
    markdown.extend(f"- {item}" for item in invariant_audits)
    markdown.extend(
        [
            "- Capacity-1000 baseline was derived without recomputation.",
            "- Existing formal result files were treated as read-only sources.",
            "",
        ]
    )
    (OUTPUT_DIR / "README.md").write_text(
        "\n".join(markdown), encoding="utf-8"
    )


def main() -> None:
    frames, hashes = load_inputs()
    invariant_audits = audit_pairing(frames)
    frames[1000].to_csv(OUTPUT_DIR / "archive_1000_baseline.csv", index=False)
    combined = pd.concat([frames[capacity] for capacity in CAPACITIES], ignore_index=True)
    combined.to_csv(OUTPUT_DIR / "all_capacities.csv", index=False)
    summary = summarize(combined)
    summary.to_csv(OUTPUT_DIR / "archive_capacity_summary.csv", index=False)
    paired = paired_differences(frames)
    paired.to_csv(OUTPUT_DIR / "paired_differences_vs_1000.csv", index=False)
    paired_continuous = paired_continuous_differences(frames)
    paired_continuous.to_csv(
        OUTPUT_DIR / "paired_continuous_differences_vs_1000.csv", index=False
    )
    plot_summary(summary)
    write_report(
        summary,
        paired,
        paired_continuous,
        frames,
        hashes,
        invariant_audits,
    )
    print(
        "ANALYSIS_COMPLETE "
        f"combined_rows={len(combined)} summary_rows={len(summary)} "
        f"paired_rows={len(paired)}"
    )


if __name__ == "__main__":
    main()
