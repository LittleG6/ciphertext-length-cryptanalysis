from substitution_rank.analysis import summarize
from substitution_rank.experiment import ExperimentConfig, run_experiment
from substitution_rank.search import SearchConfig


def test_tiny_experiment_is_reproducible(tmp_path):
    train = ["this is ordinary english training material " * 50]
    test = ["this unseen document contains enough letters for a small trial " * 30]
    config = ExperimentConfig(
        lengths=(25,),
        trials_per_length=1,
        seed=99,
        ngram_order=3,
        search=SearchConfig(restarts=1, iterations=20, patience=10, archive_size=10),
    )
    first = run_experiment(train, test, config, tmp_path / "first.csv")
    second = run_experiment(train, test, config, tmp_path / "second.csv")
    stable_fields = [
        "length",
        "trial",
        "trial_seed",
        "document_seed",
        "fragment_seed",
        "key_seed",
        "search_seed",
        "rank",
        "oracle_rank",
        "top_plaintext",
    ]
    assert {key: first[0][key] for key in stable_fields} == {
        key: second[0][key] for key in stable_fields
    }
    report = summarize(first)
    assert report[0]["length"] == 25
    assert "hit@10" in report[0]
    assert " " not in first[0]["plaintext"]
    assert first[0]["ciphertext_blocks"].replace(" ", "") == first[0]["ciphertext"]
    assert len({first[0][name] for name in ("document_seed", "fragment_seed", "key_seed", "search_seed")}) == 4
    assert "wrong_score_mean" in first[0]
