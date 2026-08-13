"""单次试验指标与汇总统计。"""

from __future__ import annotations

import math
import statistics
from typing import Iterable

from .archive import Candidate


def exact_rank(candidates: list[Candidate], true_plaintext: str) -> int | None:
    for index, candidate in enumerate(candidates, start=1):
        if candidate.plaintext == true_plaintext:
            return index
    return None


def oracle_rank(candidates: list[Candidate], true_plaintext: str, true_score: float) -> int:
    """将真实明文插入候选集后的评分排名（同分按并列最优排名）。"""
    return 1 + sum(
        candidate.score > true_score
        for candidate in candidates
        if candidate.plaintext != true_plaintext
    )


def score_gap(candidates: list[Candidate], true_plaintext: str, true_score: float) -> float:
    wrong_scores = [c.score for c in candidates if c.plaintext != true_plaintext]
    return true_score - max(wrong_scores) if wrong_scores else float("nan")


def score_distribution(
    candidates: list[Candidate],
    true_plaintext: str,
    true_score: float,
) -> dict[str, float | int]:
    """概括高分错误候选的完整分数分布以及真实明文所处位置。"""
    wrong_scores = sorted(
        candidate.score for candidate in candidates if candidate.plaintext != true_plaintext
    )
    if not wrong_scores:
        return {
            "wrong_score_count": 0,
            "wrong_score_mean": float("nan"),
            "wrong_score_median": float("nan"),
            "wrong_score_std": float("nan"),
            "wrong_score_min": float("nan"),
            "wrong_score_max": float("nan"),
            "wrong_score_q95": float("nan"),
            "wrong_score_q99": float("nan"),
            "true_score_percentile": float("nan"),
            "true_score_z": float("nan"),
        }

    def quantile(probability: float) -> float:
        position = (len(wrong_scores) - 1) * probability
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return wrong_scores[lower]
        weight = position - lower
        return wrong_scores[lower] * (1 - weight) + wrong_scores[upper] * weight

    centre = statistics.fmean(wrong_scores)
    spread = statistics.pstdev(wrong_scores)
    return {
        "wrong_score_count": len(wrong_scores),
        "wrong_score_mean": centre,
        "wrong_score_median": statistics.median(wrong_scores),
        "wrong_score_std": spread,
        "wrong_score_min": wrong_scores[0],
        "wrong_score_max": wrong_scores[-1],
        "wrong_score_q95": quantile(0.95),
        "wrong_score_q99": quantile(0.99),
        "true_score_percentile": sum(score <= true_score for score in wrong_scores)
        / len(wrong_scores),
        "true_score_z": (true_score - centre) / spread if spread > 0 else float("nan"),
    }


def character_accuracy(predicted: str, target: str) -> float:
    pairs = [(a, b) for a, b in zip(predicted, target) if "a" <= b <= "z"]
    return sum(a == b for a, b in pairs) / len(pairs) if pairs else float("nan")


def observed_key_accuracy(
    predicted_key: tuple[int, ...],
    true_key: tuple[int, ...],
    ciphertext: str,
) -> float:
    observed = {ord(char) - 97 for char in ciphertext if "a" <= char <= "z"}
    return (
        sum(predicted_key[index] == true_key[index] for index in observed) / len(observed)
        if observed
        else float("nan")
    )


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        return float("nan"), float("nan")
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total**2)) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)


def mean(values: Iterable[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    return sum(finite) / len(finite) if finite else float("nan")
