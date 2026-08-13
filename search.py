"""随机重启爬山法及搜索统计。"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
import random
import string
import time

from .archive import Candidate, CandidateArchive
from .cipher import ALPHABET_SIZE, decrypt
from .language_model import NGramLanguageModel


ENGLISH_FREQUENCY_ORDER = "etaoinshrdlcumwfgypbvkjxqz"


@dataclass(frozen=True)
class SearchConfig:
    restarts: int = 30
    iterations: int = 10_000
    patience: int = 2_000
    archive_size: int = 1_000
    frequency_initialization: bool = True
    algorithm: str = "hill_climb"
    initial_temperature: float = 0.20
    final_temperature: float = 0.002


@dataclass(frozen=True)
class SearchResult:
    candidates: list[Candidate]
    score_calls: int
    elapsed_seconds: float


def random_decryption_key(rng: random.Random) -> tuple[int, ...]:
    key = list(range(ALPHABET_SIZE))
    rng.shuffle(key)
    return tuple(key)


def frequency_decryption_key(ciphertext: str, rng: random.Random) -> tuple[int, ...]:
    """按密文字母频率匹配英文频率，并随机填充未出现字母。"""
    cipher_order = [char for char, _ in Counter(c for c in ciphertext if c.isalpha()).most_common()]
    unused_cipher = [char for char in string.ascii_lowercase if char not in cipher_order]
    rng.shuffle(unused_cipher)
    cipher_order.extend(unused_cipher)
    plain_order = list(ENGLISH_FREQUENCY_ORDER)
    key = [0] * ALPHABET_SIZE
    for cipher_char, plain_char in zip(cipher_order, plain_order):
        key[ord(cipher_char) - 97] = ord(plain_char) - 97
    return tuple(key)


def hill_climb(
    ciphertext: str,
    model: NGramLanguageModel,
    rng: random.Random,
    config: SearchConfig,
) -> SearchResult:
    if config.restarts <= 0 or config.iterations <= 0 or config.patience <= 0:
        raise ValueError("search budget values must be positive")
    archive = CandidateArchive(config.archive_size)
    score_calls = 0
    started = time.perf_counter()

    for restart in range(config.restarts):
        if config.frequency_initialization and restart == 0:
            current_key = frequency_decryption_key(ciphertext, rng)
        else:
            current_key = random_decryption_key(rng)
        current_plaintext = decrypt(ciphertext, current_key)
        current_score = model.score(current_plaintext)
        score_calls += 1
        archive.add(Candidate(current_plaintext, current_score, current_key))
        without_improvement = 0

        for _ in range(config.iterations):
            left, right = rng.sample(range(ALPHABET_SIZE), 2)
            proposed = list(current_key)
            proposed[left], proposed[right] = proposed[right], proposed[left]
            proposed_key = tuple(proposed)
            proposed_plaintext = decrypt(ciphertext, proposed_key)
            proposed_score = model.score(proposed_plaintext)
            score_calls += 1
            archive.add(Candidate(proposed_plaintext, proposed_score, proposed_key))

            if proposed_score > current_score:
                current_key = proposed_key
                current_plaintext = proposed_plaintext
                current_score = proposed_score
                without_improvement = 0
            else:
                without_improvement += 1
            if without_improvement >= config.patience:
                break

    return SearchResult(
        candidates=archive.ranked(),
        score_calls=score_calls,
        elapsed_seconds=time.perf_counter() - started,
    )


def simulated_annealing(
    ciphertext: str,
    model: NGramLanguageModel,
    rng: random.Random,
    config: SearchConfig,
) -> SearchResult:
    if config.restarts <= 0 or config.iterations <= 0 or config.patience <= 0:
        raise ValueError("search budget values must be positive")
    if config.initial_temperature <= 0 or config.final_temperature <= 0:
        raise ValueError("annealing temperatures must be positive")
    if config.final_temperature > config.initial_temperature:
        raise ValueError("final_temperature cannot exceed initial_temperature")

    archive = CandidateArchive(config.archive_size)
    score_calls = 0
    started = time.perf_counter()
    cooling_ratio = config.final_temperature / config.initial_temperature

    for restart in range(config.restarts):
        if config.frequency_initialization and restart == 0:
            current_key = frequency_decryption_key(ciphertext, rng)
        else:
            current_key = random_decryption_key(rng)
        current_plaintext = decrypt(ciphertext, current_key)
        current_score = model.score(current_plaintext)
        best_score = current_score
        score_calls += 1
        archive.add(Candidate(current_plaintext, current_score, current_key))
        without_best_improvement = 0

        for iteration in range(config.iterations):
            progress = iteration / max(1, config.iterations - 1)
            temperature = config.initial_temperature * cooling_ratio**progress
            left, right = rng.sample(range(ALPHABET_SIZE), 2)
            proposed = list(current_key)
            proposed[left], proposed[right] = proposed[right], proposed[left]
            proposed_key = tuple(proposed)
            proposed_plaintext = decrypt(ciphertext, proposed_key)
            proposed_score = model.score(proposed_plaintext)
            score_calls += 1
            archive.add(Candidate(proposed_plaintext, proposed_score, proposed_key))

            delta = proposed_score - current_score
            if delta >= 0 or rng.random() < math.exp(delta / temperature):
                current_key = proposed_key
                current_plaintext = proposed_plaintext
                current_score = proposed_score
            if proposed_score > best_score:
                best_score = proposed_score
                without_best_improvement = 0
            else:
                without_best_improvement += 1
            if without_best_improvement >= config.patience:
                break

    return SearchResult(
        candidates=archive.ranked(),
        score_calls=score_calls,
        elapsed_seconds=time.perf_counter() - started,
    )


def search_candidates(
    ciphertext: str,
    model: NGramLanguageModel,
    rng: random.Random,
    config: SearchConfig,
) -> SearchResult:
    if config.algorithm == "hill_climb":
        return hill_climb(ciphertext, model, rng, config)
    if config.algorithm == "simulated_annealing":
        return simulated_annealing(ciphertext, model, rng, config)
    raise ValueError(f"unsupported search algorithm: {config.algorithm}")
