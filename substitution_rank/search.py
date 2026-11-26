"""Random-restart hill-climbing search and search statistics."""

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
    proposal_scope: str = "all_symbols"
    early_stopping: bool = True
    neutral_proposals_count_toward_patience: bool = True


@dataclass(frozen=True)
class SearchResult:
    candidates: list[Candidate]
    score_calls: int
    elapsed_seconds: float
    target_ever_visited: bool
    target_evaluation_count: int
    target_first_score_call: int | None
    total_proposals: int
    neutral_proposals: int
    non_neutral_proposals: int
    accepted_moves: int
    accepted_improvements: int
    early_stopped_restarts: int
    proposals_per_restart: tuple[int, ...]
    distinct_plaintexts_visited: int


def _proposal_indices(ciphertext: str, config: SearchConfig) -> range | tuple[int, ...]:
    if config.proposal_scope == "all_symbols":
        # Keep the historical range object so seeded default runs retain their
        # exact random.sample trajectory.
        return range(ALPHABET_SIZE)
    if config.proposal_scope == "observed_symbols":
        observed = tuple(sorted({ord(char) - 97 for char in ciphertext}))
        if len(observed) < 2:
            raise ValueError("observed-symbol proposals require at least two ciphertext symbols")
        return observed
    if config.proposal_scope == "non_neutral":
        # Pair selection is handled by _sample_proposal_pair; the observed
        # indices are returned here only to validate the ciphertext.
        observed = tuple(sorted({ord(char) - 97 for char in ciphertext}))
        if not observed:
            raise ValueError("non-neutral proposals require a non-empty ciphertext")
        return observed
    raise ValueError(f"unsupported proposal_scope: {config.proposal_scope}")


def _sample_proposal_pair(
    rng: random.Random,
    proposal_indices: range | tuple[int, ...],
    config: SearchConfig,
    non_neutral_pairs: tuple[tuple[int, int], ...],
) -> tuple[int, int]:
    if config.proposal_scope == "non_neutral":
        return rng.choice(non_neutral_pairs)
    return tuple(rng.sample(proposal_indices, 2))  # type: ignore[return-value]


def _state_signature(key: tuple[int, ...], observed_indices: tuple[int, ...]) -> bytes:
    """Compact exact signature for the plaintext induced by the observed symbols."""
    return bytes(key[index] for index in observed_indices)


def random_decryption_key(rng: random.Random) -> tuple[int, ...]:
    key = list(range(ALPHABET_SIZE))
    rng.shuffle(key)
    return tuple(key)


def frequency_decryption_key(ciphertext: str, rng: random.Random) -> tuple[int, ...]:
    """Match ciphertext letter frequencies to English frequencies and randomly assign absent letters."""
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
    diagnostic_plaintext: str | None = None,
) -> SearchResult:
    if config.restarts <= 0 or config.iterations <= 0 or config.patience <= 0:
        raise ValueError("search budget values must be positive")
    archive = CandidateArchive(config.archive_size)
    score_calls = 0
    target_evaluation_count = 0
    target_first_score_call: int | None = None
    total_proposals = 0
    neutral_proposals = 0
    accepted_moves = 0
    accepted_improvements = 0
    early_stopped_restarts = 0
    proposals_per_restart: list[int] = []
    observed_indices = tuple(sorted({ord(char) - 97 for char in ciphertext}))
    proposal_indices = _proposal_indices(ciphertext, config)
    non_neutral_pairs = tuple(
        (left, right)
        for left in range(ALPHABET_SIZE)
        for right in range(left + 1, ALPHABET_SIZE)
        if left in observed_indices or right in observed_indices
    )
    visited_states: set[bytes] = set()
    started = time.perf_counter()

    for restart in range(config.restarts):
        if config.frequency_initialization and restart == 0:
            current_key = frequency_decryption_key(ciphertext, rng)
        else:
            current_key = random_decryption_key(rng)
        current_plaintext = decrypt(ciphertext, current_key)
        current_score = model.score(current_plaintext)
        visited_states.add(_state_signature(current_key, observed_indices))
        score_calls += 1
        if diagnostic_plaintext is not None and current_plaintext == diagnostic_plaintext:
            target_evaluation_count += 1
            target_first_score_call = target_first_score_call or score_calls
        archive.add(Candidate(current_plaintext, current_score, current_key))
        without_improvement = 0

        restart_proposals = 0
        stopped_early = False
        for _ in range(config.iterations):
            left, right = _sample_proposal_pair(
                rng, proposal_indices, config, non_neutral_pairs
            )
            proposed = list(current_key)
            proposed[left], proposed[right] = proposed[right], proposed[left]
            proposed_key = tuple(proposed)
            proposed_plaintext = decrypt(ciphertext, proposed_key)
            visited_states.add(_state_signature(proposed_key, observed_indices))
            proposed_score = model.score(proposed_plaintext)
            score_calls += 1
            total_proposals += 1
            restart_proposals += 1
            neutral = proposed_plaintext == current_plaintext
            if neutral:
                neutral_proposals += 1
            if diagnostic_plaintext is not None and proposed_plaintext == diagnostic_plaintext:
                target_evaluation_count += 1
                target_first_score_call = target_first_score_call or score_calls
            archive.add(Candidate(proposed_plaintext, proposed_score, proposed_key))

            if proposed_score > current_score:
                current_key = proposed_key
                current_plaintext = proposed_plaintext
                current_score = proposed_score
                without_improvement = 0
                accepted_moves += 1
                accepted_improvements += 1
            else:
                if not neutral or config.neutral_proposals_count_toward_patience:
                    without_improvement += 1
            if config.early_stopping and without_improvement >= config.patience:
                stopped_early = True
                break
        proposals_per_restart.append(restart_proposals)
        if stopped_early:
            early_stopped_restarts += 1

    return SearchResult(
        candidates=archive.ranked(),
        score_calls=score_calls,
        elapsed_seconds=time.perf_counter() - started,
        target_ever_visited=target_evaluation_count > 0,
        target_evaluation_count=target_evaluation_count,
        target_first_score_call=target_first_score_call,
        total_proposals=total_proposals,
        neutral_proposals=neutral_proposals,
        non_neutral_proposals=total_proposals - neutral_proposals,
        accepted_moves=accepted_moves,
        accepted_improvements=accepted_improvements,
        early_stopped_restarts=early_stopped_restarts,
        proposals_per_restart=tuple(proposals_per_restart),
        distinct_plaintexts_visited=len(visited_states),
    )


def simulated_annealing(
    ciphertext: str,
    model: NGramLanguageModel,
    rng: random.Random,
    config: SearchConfig,
    diagnostic_plaintext: str | None = None,
) -> SearchResult:
    if config.restarts <= 0 or config.iterations <= 0 or config.patience <= 0:
        raise ValueError("search budget values must be positive")
    if config.initial_temperature <= 0 or config.final_temperature <= 0:
        raise ValueError("annealing temperatures must be positive")
    if config.final_temperature > config.initial_temperature:
        raise ValueError("final_temperature cannot exceed initial_temperature")

    archive = CandidateArchive(config.archive_size)
    score_calls = 0
    target_evaluation_count = 0
    target_first_score_call: int | None = None
    total_proposals = 0
    neutral_proposals = 0
    accepted_moves = 0
    accepted_improvements = 0
    early_stopped_restarts = 0
    proposals_per_restart: list[int] = []
    observed_indices = tuple(sorted({ord(char) - 97 for char in ciphertext}))
    proposal_indices = _proposal_indices(ciphertext, config)
    non_neutral_pairs = tuple(
        (left, right)
        for left in range(ALPHABET_SIZE)
        for right in range(left + 1, ALPHABET_SIZE)
        if left in observed_indices or right in observed_indices
    )
    visited_states: set[bytes] = set()
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
        visited_states.add(_state_signature(current_key, observed_indices))
        score_calls += 1
        if diagnostic_plaintext is not None and current_plaintext == diagnostic_plaintext:
            target_evaluation_count += 1
            target_first_score_call = target_first_score_call or score_calls
        archive.add(Candidate(current_plaintext, current_score, current_key))
        without_best_improvement = 0

        restart_proposals = 0
        stopped_early = False
        for iteration in range(config.iterations):
            progress = iteration / max(1, config.iterations - 1)
            temperature = config.initial_temperature * cooling_ratio**progress
            left, right = _sample_proposal_pair(
                rng, proposal_indices, config, non_neutral_pairs
            )
            proposed = list(current_key)
            proposed[left], proposed[right] = proposed[right], proposed[left]
            proposed_key = tuple(proposed)
            proposed_plaintext = decrypt(ciphertext, proposed_key)
            visited_states.add(_state_signature(proposed_key, observed_indices))
            proposed_score = model.score(proposed_plaintext)
            score_calls += 1
            total_proposals += 1
            restart_proposals += 1
            neutral = proposed_plaintext == current_plaintext
            if neutral:
                neutral_proposals += 1
            if diagnostic_plaintext is not None and proposed_plaintext == diagnostic_plaintext:
                target_evaluation_count += 1
                target_first_score_call = target_first_score_call or score_calls
            archive.add(Candidate(proposed_plaintext, proposed_score, proposed_key))

            delta = proposed_score - current_score
            accepted = delta >= 0 or rng.random() < math.exp(delta / temperature)
            if accepted:
                current_key = proposed_key
                current_plaintext = proposed_plaintext
                current_score = proposed_score
                accepted_moves += 1
                if delta > 0:
                    accepted_improvements += 1
            if proposed_score > best_score:
                best_score = proposed_score
                without_best_improvement = 0
            else:
                if not neutral or config.neutral_proposals_count_toward_patience:
                    without_best_improvement += 1
            if config.early_stopping and without_best_improvement >= config.patience:
                stopped_early = True
                break
        proposals_per_restart.append(restart_proposals)
        if stopped_early:
            early_stopped_restarts += 1

    return SearchResult(
        candidates=archive.ranked(),
        score_calls=score_calls,
        elapsed_seconds=time.perf_counter() - started,
        target_ever_visited=target_evaluation_count > 0,
        target_evaluation_count=target_evaluation_count,
        target_first_score_call=target_first_score_call,
        total_proposals=total_proposals,
        neutral_proposals=neutral_proposals,
        non_neutral_proposals=total_proposals - neutral_proposals,
        accepted_moves=accepted_moves,
        accepted_improvements=accepted_improvements,
        early_stopped_restarts=early_stopped_restarts,
        proposals_per_restart=tuple(proposals_per_restart),
        distinct_plaintexts_visited=len(visited_states),
    )


def search_candidates(
    ciphertext: str,
    model: NGramLanguageModel,
    rng: random.Random,
    config: SearchConfig,
    diagnostic_plaintext: str | None = None,
) -> SearchResult:
    if config.algorithm == "hill_climb":
        return hill_climb(ciphertext, model, rng, config, diagnostic_plaintext)
    if config.algorithm == "simulated_annealing":
        return simulated_annealing(ciphertext, model, rng, config, diagnostic_plaintext)
    raise ValueError(f"unsupported search algorithm: {config.algorithm}")
