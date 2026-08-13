from substitution_rank.archive import Candidate, CandidateArchive
from substitution_rank.metrics import exact_rank, oracle_rank, score_distribution, wilson_interval


def candidate(text, score):
    return Candidate(text, score, tuple(range(26)))


def test_archive_deduplicates_sorts_and_caps():
    archive = CandidateArchive(capacity=2)
    archive.add(candidate("a", -3.0))
    archive.add(candidate("b", -1.0))
    archive.add(candidate("a", -2.0))
    archive.add(candidate("c", -4.0))
    assert [(item.plaintext, item.score) for item in archive.ranked()] == [
        ("b", -1.0),
        ("a", -2.0),
    ]


def test_rank_and_wilson_interval():
    items = [candidate("wrong", -1.0), candidate("truth", -2.0)]
    assert exact_rank(items, "truth") == 2
    assert exact_rank(items, "missing") is None
    assert oracle_rank(items, "new truth", -1.5) == 2
    low, high = wilson_interval(8, 10)
    assert 0 < low < 0.8 < high < 1


def test_wrong_candidate_score_distribution():
    items = [candidate("a", -3.0), candidate("b", -2.0), candidate("truth", -1.0)]
    result = score_distribution(items, "truth", -1.0)
    assert result["wrong_score_count"] == 2
    assert result["wrong_score_mean"] == -2.5
    assert result["true_score_percentile"] == 1.0
