"""Reviewer-supplement experiment runner with fixed-pool cross-reranking."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
from typing import Any

from .archive import Candidate
from .experiment import (
    ExperimentConfig,
    _run_trial_outcome,
    append_csv,
    read_csv,
    read_documents,
    write_csv,
)
from .language_model import NGramLanguageModel
from .metrics import exact_rank, oracle_rank, score_gap


_TEST_DOCUMENTS: list[str] | None = None
_SEARCH_MODEL: NGramLanguageModel | None = None
_RERANK_MODELS: dict[int, NGramLanguageModel] = {}
_CONFIG: ExperimentConfig | None = None


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: str | Path) -> dict[str, Any]:
    resolved = Path(path).resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _initialize_worker(
    train_documents: list[str],
    test_documents: list[str],
    config_payload: dict[str, Any],
    rerank_orders: tuple[int, ...],
) -> None:
    global _TEST_DOCUMENTS, _SEARCH_MODEL, _RERANK_MODELS, _CONFIG
    search_payload = dict(config_payload["search"])
    payload = {key: value for key, value in config_payload.items() if key != "search"}
    payload["lengths"] = tuple(payload["lengths"])
    _CONFIG = ExperimentConfig.from_json_payload(payload, search_payload)
    _TEST_DOCUMENTS = test_documents
    _SEARCH_MODEL = NGramLanguageModel(
        order=_CONFIG.ngram_order,
        alpha=_CONFIG.alpha,
        include_spaces=_CONFIG.include_spaces,
    ).fit(train_documents)
    _RERANK_MODELS = {}
    for order in rerank_orders:
        if order == _CONFIG.ngram_order:
            _RERANK_MODELS[order] = _SEARCH_MODEL
        else:
            _RERANK_MODELS[order] = NGramLanguageModel(
                order=order,
                alpha=_CONFIG.alpha,
                include_spaces=_CONFIG.include_spaces,
            ).fit(train_documents)


def _candidate_pool_digest(candidates: list[Candidate]) -> str:
    digest = hashlib.sha256()
    for candidate in candidates:
        digest.update(candidate.plaintext.encode("ascii"))
        digest.update(b"\0")
        digest.update(bytes(candidate.decryption_key))
        digest.update(b"\0")
        digest.update(candidate.score.hex().encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _rerank_columns(
    row: dict[str, Any], candidates: list[Candidate]
) -> dict[str, Any]:
    output: dict[str, Any] = {
        "candidate_pool_sha256": _candidate_pool_digest(candidates),
    }
    true_plaintext = str(row["plaintext"])
    for order, model in sorted(_RERANK_MODELS.items()):
        rescored = [
            Candidate(candidate.plaintext, model.score(candidate.plaintext), candidate.decryption_key)
            for candidate in candidates
        ]
        rescored.sort(key=lambda item: item.score, reverse=True)
        true_score = model.score(true_plaintext)
        rank = exact_rank(rescored, true_plaintext)
        prefix = f"rerank_order{order}"
        output.update({
            f"{prefix}_rank": rank if rank is not None else "",
            f"{prefix}_oracle_rank": oracle_rank(rescored, true_plaintext, true_score),
            f"{prefix}_score_gap": score_gap(rescored, true_plaintext, true_score),
            f"{prefix}_top_plaintext": rescored[0].plaintext,
            f"{prefix}_true_score": true_score,
        })
    return output


def _run_task(task: tuple[int, int]) -> dict[str, Any]:
    if _TEST_DOCUMENTS is None or _SEARCH_MODEL is None or _CONFIG is None:
        raise RuntimeError("supplement worker was not initialized")
    length, trial = task
    row, candidates = _run_trial_outcome(
        _TEST_DOCUMENTS,
        _SEARCH_MODEL,
        length,
        trial,
        _CONFIG.seed,
        _CONFIG.search,
        _CONFIG.include_spaces,
    )
    if _RERANK_MODELS:
        row.update(_rerank_columns(row, candidates))
    return row


def _protocol_payload(
    config: ExperimentConfig,
    train_paths: list[Path],
    test_paths: list[Path],
    rerank_orders: tuple[int, ...],
    source_paths: list[Path],
) -> dict[str, Any]:
    payload = {
        "config": asdict(config),
        "rerank_orders": list(rerank_orders),
        "training_documents": [file_record(path) for path in train_paths],
        "test_documents": [file_record(path) for path in test_paths],
        "source_files": [file_record(path) for path in source_paths],
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["protocol_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload


def run_stage(
    *,
    name: str,
    config: ExperimentConfig,
    train_paths: list[Path],
    test_paths: list[Path],
    output_path: Path,
    rerank_orders: tuple[int, ...] = (),
    workers: int = 1,
    batch_size: int = 250,
    resume: bool = True,
) -> list[dict[str, str]]:
    if workers < 1 or batch_size < 1:
        raise ValueError("workers and batch_size must be positive")
    train_resolved = [path.resolve() for path in train_paths]
    test_resolved = [path.resolve() for path in test_paths]
    if set(train_resolved) & set(test_resolved):
        raise ValueError("training and test documents must be disjoint")
    source_paths = sorted((Path(__file__).resolve().parent).glob("*.py"))
    protocol = _protocol_payload(config, train_paths, test_paths, rerank_orders, source_paths)
    metadata_path = output_path.with_suffix(".metadata.json")
    expected = {
        (length, trial)
        for length in config.lengths
        for trial in range(config.trials_per_length)
    }
    rows: list[dict[str, str]] = []
    completed: set[tuple[int, int]] = set()
    started_at = _utc_now()
    if resume and output_path.exists():
        rows = read_csv(output_path)
        for row in rows:
            pair = (int(row["length"]), int(row["trial"]))
            if pair not in expected or pair in completed:
                raise ValueError(f"invalid or duplicate checkpoint task: {pair}")
            completed.add(pair)
        previous = json.loads(metadata_path.read_text(encoding="utf-8"))
        if previous.get("protocol_sha256") != protocol["protocol_sha256"]:
            raise ValueError(f"resume protocol mismatch for stage {name}")
        started_at = previous["run_state"].get("started_at", started_at)
    elif output_path.exists() or metadata_path.exists():
        raise ValueError(f"existing stage output requires resume: {output_path}")

    tasks = sorted(expected - completed)
    metadata = {
        "stage": name,
        **protocol,
        "runtime": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "workers_requested": workers,
        },
        "run_state": {
            "status": "running",
            "expected_trials": len(expected),
            "completed_trials": len(completed),
            "remaining_trials": len(tasks),
            "batch_size": batch_size,
            "started_at": started_at,
            "updated_at": _utc_now(),
            "parallel_fallback": False,
        },
    }
    _write_json_atomic(metadata_path, metadata)
    if tasks:
        train_documents = read_documents(train_paths)
        test_documents = read_documents(test_paths)
        config_payload = asdict(config)
        with ProcessPoolExecutor(
            max_workers=workers,
            initializer=_initialize_worker,
            initargs=(train_documents, test_documents, config_payload, rerank_orders),
        ) as executor:
            for start in range(0, len(tasks), batch_size):
                batch = tasks[start : start + batch_size]
                batch_rows = list(executor.map(_run_task, batch, chunksize=1))
                append_csv(batch_rows, output_path)
                completed.update((int(row["length"]), int(row["trial"])) for row in batch_rows)
                metadata["run_state"].update({
                    "completed_trials": len(completed),
                    "remaining_trials": len(expected) - len(completed),
                    "updated_at": _utc_now(),
                })
                _write_json_atomic(metadata_path, metadata)
                print(f"stage={name} completed={len(completed)}/{len(expected)}", flush=True)

    rows = read_csv(output_path)
    rows.sort(key=lambda row: (int(row["length"]), int(row["trial"])))
    write_csv(rows, output_path)
    metadata["run_state"].update({
        "status": "completed",
        "completed_trials": len(rows),
        "remaining_trials": 0,
        "updated_at": _utc_now(),
        "completed_at": _utc_now(),
    })
    _write_json_atomic(metadata_path, metadata)
    return rows
