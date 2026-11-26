"""Minimal validation entry point that does not require pytest."""

from __future__ import annotations

from pathlib import Path
import tempfile

from tests.test_archive_metrics import (
    test_archive_deduplicates_sorts_and_caps,
    test_rank_and_wilson_interval,
    test_wrong_candidate_score_distribution,
)
from tests.test_cipher import (
    test_encrypt_decrypt_round_trip,
    test_normalize_and_sample_exact_letter_count,
    test_remove_spaces_and_group_in_blocks_of_five,
)
from tests.test_experiment import (
    test_controlled_search_uses_exact_effective_budget,
    test_resume_skips_completed_trials,
    test_target_diagnostics_do_not_change_search_trajectory,
    test_tiny_experiment_is_reproducible,
)
from tests.test_language_model import test_score_is_deterministic_and_favors_regular_text


def main() -> int:
    tests = [
        test_encrypt_decrypt_round_trip,
        test_normalize_and_sample_exact_letter_count,
        test_remove_spaces_and_group_in_blocks_of_five,
        test_score_is_deterministic_and_favors_regular_text,
        test_archive_deduplicates_sorts_and_caps,
        test_rank_and_wilson_interval,
        test_wrong_candidate_score_distribution,
        test_target_diagnostics_do_not_change_search_trajectory,
        test_controlled_search_uses_exact_effective_budget,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        test_tiny_experiment_is_reproducible(temporary)
        test_resume_skips_completed_trials(temporary)
    print("PASS test_tiny_experiment_is_reproducible")
    print("PASS test_resume_skips_completed_trials")
    print(f"VALIDATION COMPLETE: {len(tests) + 2} tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
