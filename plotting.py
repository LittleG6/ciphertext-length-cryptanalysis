"""论文所需的三类基础图。"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


def plot_summary(
    summary_csv: str | Path,
    output_dir: str | Path,
    trials_csv: str | Path | None = None,
) -> list[Path]:
    try:
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise RuntimeError("绘图需要安装 matplotlib：python -m pip install matplotlib") from error

    with Path(summary_csv).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    lengths = [int(row["length"]) for row in rows]
    created: list[Path] = []

    fig, ax = plt.subplots(figsize=(8, 5))
    for k in (1, 5, 10, 50, 100, 1000):
        key = f"hit@{k}"
        if key in rows[0]:
            values = [float(row[key]) for row in rows]
            low = [float(row[f"{key}_low"]) for row in rows]
            high = [float(row[f"{key}_high"]) for row in rows]
            ax.plot(lengths, values, marker="o", label=f"Hit@{k}")
            ax.fill_between(lengths, low, high, alpha=0.10)
    ax.set(xlabel="Ciphertext length (letters)", ylabel="Recovery probability", ylim=(0, 1.02))
    ax.legend(ncol=2)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    hit_path = output_dir / "hit_at_k.png"
    fig.savefig(hit_path, dpi=200)
    plt.close(fig)
    created.append(hit_path)

    fig, ax = plt.subplots(figsize=(8, 5))
    labels = ["top1_success", "scoring_failure", "search_failure"]
    bottoms = [0.0] * len(rows)
    for label in labels:
        values = [float(row[f"proportion_{label}"]) for row in rows]
        ax.bar(lengths, values, bottom=bottoms, label=label, width=max(4, min(lengths) * 0.35))
        bottoms = [a + b for a, b in zip(bottoms, values)]
    ax.set(xlabel="Ciphertext length (letters)", ylabel="Proportion", ylim=(0, 1.02))
    ax.legend()
    fig.tight_layout()
    failure_path = output_dir / "failure_decomposition.png"
    fig.savefig(failure_path, dpi=200)
    plt.close(fig)
    created.append(failure_path)

    if trials_csv is not None:
        with Path(trials_csv).open(encoding="utf-8", newline="") as handle:
            trial_rows = list(csv.DictReader(handle))
        gaps: dict[int, list[float]] = defaultdict(list)
        for row in trial_rows:
            try:
                gaps[int(row["length"])].append(float(row["score_gap"]))
            except (KeyError, ValueError):
                continue
        ordered_lengths = sorted(gaps)
        if ordered_lengths:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.boxplot(
                [gaps[length] for length in ordered_lengths],
                tick_labels=[str(length) for length in ordered_lengths],
                showfliers=False,
            )
            ax.axhline(0.0, color="black", linewidth=1, linestyle="--")
            ax.set(
                xlabel="Ciphertext length (letters)",
                ylabel="True score - best wrong score",
            )
            ax.grid(axis="y", alpha=0.25)
            fig.tight_layout()
            gap_path = output_dir / "score_gap_boxplot.png"
            fig.savefig(gap_path, dpi=200)
            plt.close(fig)
            created.append(gap_path)
    return created
