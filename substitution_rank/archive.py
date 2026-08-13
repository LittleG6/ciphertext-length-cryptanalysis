"""容量受限、按明文去重的候选档案。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    plaintext: str
    score: float
    decryption_key: tuple[int, ...]


class CandidateArchive:
    def __init__(self, capacity: int = 1000):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._items: dict[str, Candidate] = {}

    def add(self, candidate: Candidate) -> None:
        previous = self._items.get(candidate.plaintext)
        if previous is None or candidate.score > previous.score:
            self._items[candidate.plaintext] = candidate
        if len(self._items) > self.capacity * 2:
            self._prune()

    def _prune(self) -> None:
        best = sorted(self._items.values(), key=lambda item: item.score, reverse=True)[: self.capacity]
        self._items = {candidate.plaintext: candidate for candidate in best}

    def ranked(self) -> list[Candidate]:
        self._prune()
        return sorted(self._items.values(), key=lambda item: item.score, reverse=True)

    def __len__(self) -> int:
        return min(len(self._items), self.capacity)

