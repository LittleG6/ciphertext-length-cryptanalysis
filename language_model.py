"""带加性平滑的字符 n-gram 语言模型。"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
import math
from pathlib import Path

from .cipher import normalize_text


@dataclass
class NGramLanguageModel:
    order: int = 4
    alpha: float = 0.1
    include_spaces: bool = True
    counts: Counter[str] | None = None
    total: int = 0

    def fit(self, documents: list[str]) -> "NGramLanguageModel":
        if self.order < 1:
            raise ValueError("order must be at least 1")
        if self.alpha <= 0:
            raise ValueError("alpha must be positive")
        counts: Counter[str] = Counter()
        for document in documents:
            text = self._prepare(document)
            counts.update(
                text[index : index + self.order]
                for index in range(max(0, len(text) - self.order + 1))
            )
        if not counts:
            raise ValueError("training corpus contains no usable n-grams")
        self.counts = counts
        self.total = sum(counts.values())
        return self

    @property
    def vocabulary_size(self) -> int:
        alphabet_size = 27 if self.include_spaces else 26
        return alphabet_size**self.order

    def score(self, text: str) -> float:
        """返回每个 n-gram 的平均对数概率；越高越像训练语言。"""
        if self.counts is None or self.total <= 0:
            raise RuntimeError("language model has not been fitted")
        prepared = self._prepare(text)
        n_windows = len(prepared) - self.order + 1
        if n_windows <= 0:
            return float("-inf")
        denominator = self.total + self.alpha * self.vocabulary_size
        return sum(
            math.log((self.counts.get(prepared[i : i + self.order], 0) + self.alpha) / denominator)
            for i in range(n_windows)
        ) / n_windows

    def _prepare(self, text: str) -> str:
        text = normalize_text(text)
        return text if self.include_spaces else text.replace(" ", "")

    def save(self, path: str | Path) -> None:
        if self.counts is None:
            raise RuntimeError("language model has not been fitted")
        payload = {
            "order": self.order,
            "alpha": self.alpha,
            "include_spaces": self.include_spaces,
            "total": self.total,
            "counts": dict(self.counts),
        }
        Path(path).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "NGramLanguageModel":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        model = cls(
            order=int(payload["order"]),
            alpha=float(payload["alpha"]),
            include_spaces=bool(payload["include_spaces"]),
        )
        model.counts = Counter({key: int(value) for key, value in payload["counts"].items()})
        model.total = int(payload["total"])
        return model

