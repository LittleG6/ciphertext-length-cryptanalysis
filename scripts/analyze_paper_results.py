#!/usr/bin/env python3
"""Create paper-facing analyses from the completed formal experiment CSVs.

Only Python's standard library and Pillow are required.  Source CSVs are opened
read-only; all derived outputs are written under results/paper_analysis/.
"""

from __future__ import annotations

import csv
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUT = RESULTS / "paper_analysis"
OUT.mkdir(parents=True, exist_ok=True)

BOOKS = {
    0: "The Time Machine",
    1: "Treasure Island",
    2: "The Picture of Dorian Gray",
    3: "The Wonderful Wizard of Oz",
}


def read_rows(name: str) -> list[dict[str, str]]:
    with (RESULTS / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def as_float(value: str | None) -> float:
    if value is None or value == "":
        return math.nan
    return float(value)


def rank_hit(row: dict[str, str], k: int) -> bool:
    value = as_float(row.get("rank"))
    return not math.isnan(value) and value <= k


def mean(values: Iterable[float]) -> float:
    items = list(values)
    return statistics.fmean(items) if items else math.nan


def write_rows(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def group_rows(
    rows: Iterable[dict[str, str]], keys: tuple[str, ...]
) -> dict[tuple[str, ...], list[dict[str, str]]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in keys)].append(row)
    return grouped


def paired_bootstrap(
    left: list[bool], right: list[bool], seed: int, draws: int = 20_000
) -> tuple[float, float, float]:
    delta = [float(a) - float(b) for a, b in zip(left, right, strict=True)]
    rng = random.Random(seed)
    n = len(delta)
    sampled_means = [
        sum(delta[rng.randrange(n)] for _ in range(n)) / n for _ in range(draws)
    ]
    sampled_means.sort()
    return (
        mean(delta),
        sampled_means[int(0.025 * draws)],
        sampled_means[int(0.975 * draws) - 1],
    )


def paired_comparison(
    left: list[dict[str, str]],
    right: list[dict[str, str]],
    left_label: str,
    right_label: str,
    seed_offset: int,
) -> list[dict[str, object]]:
    right_lookup = {(row["length"], row["trial"]): row for row in right}
    paired = [
        (row, right_lookup[(row["length"], row["trial"])])
        for row in left
        if (row["length"], row["trial"]) in right_lookup
    ]
    grouped: dict[int, list[tuple[dict[str, str], dict[str, str]]]] = defaultdict(list)
    for left_row, right_row in paired:
        grouped[int(left_row["length"])].append((left_row, right_row))

    output: list[dict[str, object]] = []
    for length in sorted(grouped):
        group = grouped[length]
        for label, k in (("Hit@1", 1), ("Hit@10", 10), ("Hit@1000", 1000)):
            left_hit = [rank_hit(pair[0], k) for pair in group]
            right_hit = [rank_hit(pair[1], k) for pair in group]
            difference, low, high = paired_bootstrap(
                left_hit, right_hit, 20260729 + seed_offset + length + k
            )
            output.append(
                {
                    "length": length,
                    "metric": label,
                    "left": left_label,
                    "right": right_label,
                    "left_rate": mean(float(value) for value in left_hit),
                    "right_rate": mean(float(value) for value in right_hit),
                    "difference_left_minus_right": difference,
                    "bootstrap_95_low": low,
                    "bootstrap_95_high": high,
                }
            )
    return output


def make_main_tables() -> dict[str, object]:
    summary = read_rows("formal_minimum_summary.csv")
    main = read_rows("formal_minimum.csv")
    main_fields = [
        "length",
        "trials",
        "hit@1",
        "hit@1_low",
        "hit@1_high",
        "hit@5",
        "hit@10",
        "hit@1000",
        "mrr",
        "mean_character_accuracy",
        "mean_key_accuracy",
        "mean_score_gap",
        "mean_true_score_percentile",
        "proportion_mechanism_retained_below_top1",
        "proportion_mechanism_never_visited",
        "mean_seconds",
    ]
    write_rows(
        OUT / "main_results.csv",
        [{field: row[field] for field in main_fields} for row in summary],
        main_fields,
    )

    per_book: list[dict[str, object]] = []
    grouped = group_rows(main, ("length", "selected_document_index"))
    for (length_text, document_text), rows in sorted(
        grouped.items(), key=lambda item: (int(item[0][0]), int(item[0][1]))
    ):
        ranks = [as_float(row["rank"]) for row in rows]
        per_book.append(
            {
                "length": int(length_text),
                "document_index": int(document_text),
                "document": BOOKS[int(document_text)],
                "trials": len(rows),
                "hit@1": mean(float(rank_hit(row, 1)) for row in rows),
                "hit@10": mean(float(rank_hit(row, 10)) for row in rows),
                "hit@1000": mean(float(rank_hit(row, 1000)) for row in rows),
                "mrr": mean(0.0 if math.isnan(rank) else 1.0 / rank for rank in ranks),
                "mean_character_accuracy": mean(
                    as_float(row["character_accuracy"]) for row in rows
                ),
                "mean_seconds": mean(as_float(row["elapsed_seconds"]) for row in rows),
            }
        )
    per_book_fields = list(per_book[0])
    write_rows(OUT / "per_book_results.csv", per_book, per_book_fields)

    selected_lengths = [100, 150, 200, 300, 500]
    pivot_rows: list[dict[str, object]] = []
    for index, title in BOOKS.items():
        pivot_row: dict[str, object] = {"document": title}
        for length in selected_lengths:
            match = next(
                row
                for row in per_book
                if row["document_index"] == index and row["length"] == length
            )
            pivot_row[str(length)] = match["hit@1"]
        pivot_rows.append(pivot_row)
    write_rows(
        OUT / "per_book_hit1_selected_lengths.csv",
        pivot_rows,
        ["document", *[str(length) for length in selected_lengths]],
    )

    mechanism_counts: list[dict[str, object]] = []
    mechanisms = group_rows(main, ("length", "mechanism_type"))
    totals = {
        length: sum(
            len(rows)
            for (candidate_length, _), rows in mechanisms.items()
            if candidate_length == length
        )
        for length, _ in mechanisms
    }
    for (length, mechanism), rows in sorted(
        mechanisms.items(), key=lambda item: (int(item[0][0]), item[0][1])
    ):
        mechanism_counts.append(
            {
                "length": int(length),
                "mechanism_type": mechanism,
                "count": len(rows),
                "proportion": len(rows) / totals[length],
            }
        )
    write_rows(
        OUT / "mechanism_counts.csv",
        mechanism_counts,
        ["length", "mechanism_type", "count", "proportion"],
    )

    hit1_200 = [row["hit@1"] for row in per_book if row["length"] == 200]
    hit1_300 = [row["hit@1"] for row in per_book if row["length"] == 300]
    return {
        "main_rows": len(main),
        "lengths": sorted({int(row["length"]) for row in main}),
        "sum_trial_cpu_hours": sum(as_float(row["elapsed_seconds"]) for row in main)
        / 3600,
        "per_book_hit1_range_at_200": [min(hit1_200), max(hit1_200)],
        "per_book_hit1_range_at_300": [min(hit1_300), max(hit1_300)],
    }


def experiment_table(
    frames: dict[int, list[dict[str, str]]], factor_name: str
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for factor, rows in frames.items():
        for (length_text,), group in sorted(
            group_rows(rows, ("length",)).items(), key=lambda item: int(item[0][0])
        ):
            ranks = [as_float(row["rank"]) for row in group]
            output.append(
                {
                    factor_name: factor,
                    "length": int(length_text),
                    "trials": len(group),
                    "hit@1": mean(float(rank_hit(row, 1)) for row in group),
                    "hit@10": mean(float(rank_hit(row, 10)) for row in group),
                    "hit@1000": mean(float(rank_hit(row, 1000)) for row in group),
                    "mrr": mean(
                        0.0 if math.isnan(rank) else 1.0 / rank for rank in ranks
                    ),
                    "mean_character_accuracy": mean(
                        as_float(row["character_accuracy"]) for row in group
                    ),
                    "mean_seconds": mean(as_float(row["elapsed_seconds"]) for row in group),
                }
            )
    return output


def make_robustness_tables() -> dict[str, object]:
    budget_frames = {
        10: read_rows("predefined_budget_restarts10.csv"),
        30: read_rows("predefined_budget_restarts30.csv"),
        100: read_rows("predefined_budget_restarts100.csv"),
    }
    order_frames = {
        3: read_rows("predefined_order3.csv"),
        4: read_rows("predefined_order4.csv"),
        5: read_rows("predefined_order5.csv"),
    }

    budget = experiment_table(budget_frames, "restarts")
    order = experiment_table(order_frames, "ngram_order")
    experiment_fields = [
        "length",
        "trials",
        "hit@1",
        "hit@10",
        "hit@1000",
        "mrr",
        "mean_character_accuracy",
        "mean_seconds",
    ]
    write_rows(
        OUT / "budget_robustness.csv",
        budget,
        ["restarts", *experiment_fields],
    )
    write_rows(
        OUT / "order_robustness.csv",
        order,
        ["ngram_order", *experiment_fields],
    )

    budget_differences = [
        *paired_comparison(
            budget_frames[30], budget_frames[10], "30 restarts", "10 restarts", 1000
        ),
        *paired_comparison(
            budget_frames[100], budget_frames[30], "100 restarts", "30 restarts", 2000
        ),
    ]
    difference_fields = list(budget_differences[0])
    write_rows(
        OUT / "budget_paired_differences.csv",
        budget_differences,
        difference_fields,
    )

    order_differences = [
        *paired_comparison(order_frames[4], order_frames[3], "4-gram", "3-gram", 3000),
        *paired_comparison(order_frames[5], order_frames[4], "5-gram", "4-gram", 4000),
    ]
    write_rows(
        OUT / "order_paired_differences.csv", order_differences, difference_fields
    )
    return {
        "budget_rows": sum(len(rows) for rows in budget_frames.values()),
        "order_rows": sum(len(rows) for rows in order_frames.values()),
    }


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_line_chart(
    path: Path,
    title: str,
    x_values: list[int],
    series: list[tuple[str, list[float], str]],
    y_min: float,
    y_max: float,
    y_label: str,
) -> None:
    width, height = 1600, 900
    left, right, top, bottom = 170, 80, 110, 145
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = load_font(30)
    small = load_font(24)
    title_font = load_font(38)
    plot_left, plot_right = left, width - right
    plot_top, plot_bottom = top, height - bottom

    def x_px(value: int) -> float:
        return plot_left + (value - min(x_values)) / (max(x_values) - min(x_values)) * (
            plot_right - plot_left
        )

    def y_px(value: float) -> float:
        return plot_bottom - (value - y_min) / (y_max - y_min) * (
            plot_bottom - plot_top
        )

    for tick in range(0, 11):
        value = y_min + (y_max - y_min) * tick / 10
        y = y_px(value)
        draw.line((plot_left, y, plot_right, y), fill="#D9DEE5", width=2)
        draw.text((55, y - 15), f"{value:.1f}", fill="#222222", font=small)
    for value in x_values:
        x = x_px(value)
        draw.line((x, plot_bottom, x, plot_bottom + 10), fill="#222222", width=2)
        draw.text((x - 25, plot_bottom + 20), str(value), fill="#222222", font=small)

    draw.line((plot_left, plot_top, plot_left, plot_bottom), fill="#222222", width=3)
    draw.line((plot_left, plot_bottom, plot_right, plot_bottom), fill="#222222", width=3)
    draw.text((width // 2 - 270, 28), title, fill="#111111", font=title_font)
    draw.text((width // 2 - 120, height - 65), "Ciphertext length", fill="#222222", font=font)
    draw.text((20, 30), y_label, fill="#222222", font=small)

    legend_x = plot_right - 280
    legend_y = plot_top + 25
    for index, (label, values, color) in enumerate(series):
        points = [(x_px(x), y_px(y)) for x, y in zip(x_values, values, strict=True)]
        draw.line(points, fill=color, width=6, joint="curve")
        for x, y in points:
            draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=color)
        y = legend_y + index * 45
        draw.line((legend_x, y + 14, legend_x + 55, y + 14), fill=color, width=6)
        draw.text((legend_x + 70, y), label, fill="#222222", font=small)
    image.save(path, dpi=(220, 220))


def make_figures() -> None:
    main = read_rows("formal_minimum_summary.csv")
    x_values = [int(row["length"]) for row in main]
    draw_line_chart(
        OUT / "main_hit_curves.png",
        "Top-k recovery as ciphertext length increases",
        x_values,
        [
            ("Hit@1", [as_float(row["hit@1"]) for row in main], "#2166AC"),
            ("Hit@10", [as_float(row["hit@10"]) for row in main], "#D6604D"),
            ("Hit@1000", [as_float(row["hit@1000"]) for row in main], "#1B7837"),
        ],
        0.0,
        1.0,
        "Success probability",
    )


def main() -> None:
    status = json.loads((RESULTS / "all_formal_experiments_status.json").read_text())
    if status.get("status") != "completed" or status.get("total_result_rows") != 17_300:
        raise RuntimeError("Formal results are not in the expected completed 17,300-row state")
    report = {
        "formal_status": {
            "status": status["status"],
            "computed_unique_trials": status["computed_unique_trials"],
            "derived_baseline_rows": status["derived_baseline_rows"],
            "total_result_rows": status["total_result_rows"],
        },
        "main": make_main_tables(),
        "robustness": make_robustness_tables(),
    }
    make_figures()
    (OUT / "analysis_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
