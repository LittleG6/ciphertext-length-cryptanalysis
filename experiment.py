"""数据加载、单次试验和批量实验。"""

from __future__ import annotations

import csv
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Any
import warnings

from .cipher import (
    encrypt,
    group_blocks,
    inverse_key,
    letter_count,
    normalize_text,
    random_encryption_key,
    sample_by_letter_length_with_start,
)
from .language_model import NGramLanguageModel
from .metrics import (
    character_accuracy,
    exact_rank,
    observed_key_accuracy,
    oracle_rank,
    score_distribution,
    score_gap,
)
from .search import SearchConfig, search_candidates


@dataclass(frozen=True)
class ExperimentConfig:
    lengths: tuple[int, ...] = (25, 40, 50, 60, 75, 80, 100, 150, 200, 300, 500)
    trials_per_length: int = 100
    seed: int = 20260712
    ngram_order: int = 4
    alpha: float = 0.1
    include_spaces: bool = False
    search: SearchConfig = SearchConfig()

    @classmethod
    def from_json(cls, path: str | Path) -> "ExperimentConfig":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        search = SearchConfig(**payload.pop("search", {}))
        if "lengths" in payload:
            payload["lengths"] = tuple(int(value) for value in payload["lengths"])
        return cls(search=search, **payload)


def read_documents(paths: list[str | Path]) -> list[str]:
    documents = [normalize_text(Path(path).read_text(encoding="utf-8")) for path in paths]
    documents = [document for document in documents if document]
    if not documents:
        raise ValueError("no non-empty documents were loaded")
    return documents


def _trial_seed(master_seed: int, length: int, trial: int) -> int:
    digest = hashlib.sha256(f"{master_seed}:{length}:{trial}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _component_seed(trial_seed: int, component: str) -> int:
    digest = hashlib.sha256(f"{trial_seed}:{component}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _key_text(key: tuple[int, ...]) -> str:
    return "".join(chr(index + 97) for index in key)


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _run_trial_outcome(
    documents: list[str],
    model: NGramLanguageModel,
    length: int,
    trial: int,
    master_seed: int,
    search_config: SearchConfig,
    include_spaces: bool = False,
) -> tuple[dict[str, Any], list[Any]]:
    trial_seed = _trial_seed(master_seed, length, trial)
    document_seed = _component_seed(trial_seed, "document")
    fragment_seed = _component_seed(trial_seed, "fragment")
    key_seed = _component_seed(trial_seed, "key")
    search_seed = _component_seed(trial_seed, "search")

    eligible = [
        (index, document)
        for index, document in enumerate(documents)
        if letter_count(document) >= length
    ]
    if not eligible:
        raise ValueError(f"no test document contains {length} letters")
    document_index, document = random.Random(document_seed).choice(eligible)
    plaintext, fragment_start = sample_by_letter_length_with_start(
        document,
        length,
        random.Random(fragment_seed),
        include_spaces=include_spaces,
    )
    encryption_key = random_encryption_key(random.Random(key_seed))
    true_decryption_key = inverse_key(encryption_key)
    ciphertext = encrypt(plaintext, encryption_key)

    result = search_candidates(
        ciphertext,
        model,
        random.Random(search_seed),
        search_config,
    )
    candidates = result.candidates
    true_score = model.score(plaintext)
    rank = exact_rank(candidates, plaintext)
    inserted_rank = oracle_rank(candidates, plaintext, true_score)
    gap = score_gap(candidates, plaintext, true_score)
    distribution = score_distribution(candidates, plaintext, true_score)
    top = candidates[0]

    if rank == 1:
        failure_type = "top1_success"
    elif rank is not None:
        failure_type = "scoring_failure"
    else:
        failure_type = "search_failure"

    row = {
        "length": length,
        "trial": trial,
        "master_seed": master_seed,
        "trial_seed": trial_seed,
        "document_seed": document_seed,
        "fragment_seed": fragment_seed,
        "key_seed": key_seed,
        "search_seed": search_seed,
        "selected_document_index": document_index,
        "fragment_start_letter": fragment_start,
        "search_algorithm": search_config.algorithm,
        "rank": rank if rank is not None else "",
        "oracle_rank": inserted_rank,
        "true_score": true_score,
        "top_score": top.score,
        "score_gap": gap,
        **distribution,
        "character_accuracy": character_accuracy(top.plaintext, plaintext),
        "observed_key_accuracy": observed_key_accuracy(
            top.decryption_key, true_decryption_key, ciphertext
        ),
        "candidate_count": len(candidates),
        "score_calls": result.score_calls + 1,
        "elapsed_seconds": result.elapsed_seconds,
        "failure_type": failure_type,
        "plaintext": plaintext,
        "plaintext_blocks": group_blocks(plaintext),
        "ciphertext": ciphertext,
        "ciphertext_blocks": group_blocks(ciphertext),
        "top_plaintext": top.plaintext,
        "top_plaintext_blocks": group_blocks(top.plaintext),
        "encryption_key": _key_text(encryption_key),
        "true_decryption_key": _key_text(true_decryption_key),
    }
    return row, candidates


def run_trial(
    documents: list[str],
    model: NGramLanguageModel,
    length: int,
    trial: int,
    master_seed: int,
    search_config: SearchConfig,
    include_spaces: bool = False,
) -> dict[str, Any]:
    row, _ = _run_trial_outcome(
        documents,
        model,
        length,
        trial,
        master_seed,
        search_config,
        include_spaces,
    )
    return row


def run_experiment(
    train_documents: list[str],
    test_documents: list[str],
    config: ExperimentConfig,
    output_csv: str | Path,
    workers: int = 1,
) -> list[dict[str, Any]]:
    model = NGramLanguageModel(
        order=config.ngram_order,
        alpha=config.alpha,
        include_spaces=config.include_spaces,
    ).fit(train_documents)
    tasks = [
        (
            test_documents,
            model,
            length,
            trial,
            config.seed,
            config.search,
            config.include_spaces,
        )
        for length in config.lengths
        for trial in range(config.trials_per_length)
    ]
    if workers > 1:
        try:
            with ProcessPoolExecutor(max_workers=workers) as executor:
                rows = list(executor.map(_run_trial_task, tasks, chunksize=1))
        except (OSError, PermissionError) as error:
            warnings.warn(
                f"parallel workers unavailable ({error}); falling back to sequential execution",
                RuntimeWarning,
                stacklevel=2,
            )
            rows = [_run_trial_task(task) for task in tasks]
    else:
        rows = [_run_trial_task(task) for task in tasks]
    write_csv(rows, output_csv)
    metadata_path = Path(output_csv).with_suffix(".metadata.json")
    metadata_path.write_text(
        json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return rows


def _run_trial_task(args: tuple[Any, ...]) -> dict[str, Any]:
    return run_trial(*args)


def write_csv(rows: list[dict[str, Any]], path: str | Path) -> None:
    if not rows:
        raise ValueError("cannot write an empty result table")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def run_single_pilot(
    train_documents: list[str],
    test_documents: list[str],
    config: ExperimentConfig,
    output_dir: str | Path,
) -> tuple[Path, Path, Path]:
    """运行一个长度为 100 的试验并导出完整 Top-K 候选与分布。"""
    if tuple(config.lengths) != (100,) or config.trials_per_length != 1:
        raise ValueError("single-pilot config must use lengths=[100] and trials_per_length=1")
    model = NGramLanguageModel(
        order=config.ngram_order,
        alpha=config.alpha,
        include_spaces=config.include_spaces,
    ).fit(train_documents)
    row, candidates = _run_trial_outcome(
        test_documents,
        model,
        100,
        0,
        config.seed,
        config.search,
        config.include_spaces,
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    candidate_rows = []
    for rank, candidate in enumerate(candidates, start=1):
        candidate_rows.append({
            "rank": rank,
            "score": candidate.score,
            "score_minus_true": candidate.score - float(row["true_score"]),
            "is_correct_plaintext": candidate.plaintext == row["plaintext"],
            "plaintext": candidate.plaintext,
            "plaintext_blocks": group_blocks(candidate.plaintext),
            "decryption_key": _key_text(candidate.decryption_key),
        })
    candidates_path = output_dir / "pilot_top100_candidates.csv"
    write_csv(candidate_rows, candidates_path)

    wrong_scores = [
        candidate.score for candidate in candidates if candidate.plaintext != row["plaintext"]
    ]
    histogram_rows = []
    if wrong_scores:
        minimum, maximum = min(wrong_scores), max(wrong_scores)
        bin_count = min(10, max(1, len(wrong_scores)))
        width = (maximum - minimum) / bin_count if maximum > minimum else 1.0
        counts = [0] * bin_count
        for score in wrong_scores:
            index = min(bin_count - 1, int((score - minimum) / width)) if width else 0
            counts[index] += 1
        for index, count in enumerate(counts):
            histogram_rows.append({
                "bin": index + 1,
                "lower": minimum + index * width,
                "upper": minimum + (index + 1) * width,
                "count": count,
            })
    histogram_path = output_dir / "pilot_wrong_score_histogram.csv"
    write_csv(histogram_rows, histogram_path)

    summary = {
        "protocol": asdict(config),
        "result": row,
        "correct_plaintext_search_status": (
            f"rank_{row['rank']}" if row["rank"] != "" else "not_retrieved_in_top_k"
        ),
        "candidate_file": candidates_path.name,
        "histogram_file": histogram_path.name,
    }
    summary_path = output_dir / "pilot_summary.json"
    summary_path.write_text(
        json.dumps(_json_safe(summary), ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    return candidates_path, histogram_path, summary_path
