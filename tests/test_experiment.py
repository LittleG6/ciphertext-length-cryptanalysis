import json
import random

from substitution_rank.analysis import summarize
from substitution_rank.cipher import decrypt
from substitution_rank.experiment import (
    ExperimentConfig,
    read_csv,
    run_experiment,
    write_csv,
)
from substitution_rank.search import (
    SearchConfig,
    hill_climb,
    random_decryption_key,
    simulated_annealing,
)


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
    assert first[0]["mechanism_type"] in {
        "top1_success",
        "retained_below_top1",
        "visited_then_pruned",
        "never_visited",
    }
    assert "true_ever_visited" in first[0]
    assert "true_retained" in first[0]
    assert "true_pruned" in first[0]
    assert "proportion_rank_not_retained" in report[0]
    assert "proportion_mechanism_never_visited" in report[0]


def test_target_diagnostics_do_not_change_search_trajectory():
    class ConstantModel:
        @staticmethod
        def score(_text):
            return 0.0

    seed = 71
    ciphertext = "aaaaa"
    expected_initial_key = random_decryption_key(random.Random(seed))
    target = decrypt(ciphertext, expected_initial_key)
    config = SearchConfig(
        restarts=1,
        iterations=3,
        patience=3,
        archive_size=20,
        frequency_initialization=False,
    )
    diagnosed = hill_climb(
        ciphertext,
        ConstantModel(),
        random.Random(seed),
        config,
        diagnostic_plaintext=target,
    )
    plain = hill_climb(
        ciphertext,
        ConstantModel(),
        random.Random(seed),
        config,
    )
    assert diagnosed.target_ever_visited
    assert diagnosed.target_evaluation_count >= 1
    assert diagnosed.target_first_score_call == 1
    assert [
        (item.plaintext, item.score, item.decryption_key)
        for item in diagnosed.candidates
    ] == [
        (item.plaintext, item.score, item.decryption_key)
        for item in plain.candidates
    ]


def test_controlled_search_uses_exact_effective_budget():
    class ConstantModel:
        @staticmethod
        def score(_text):
            return 0.0

    ciphertext = "abcabcabc"
    config = SearchConfig(
        restarts=2,
        iterations=7,
        patience=1,
        archive_size=20,
        frequency_initialization=False,
        proposal_scope="non_neutral",
        early_stopping=False,
        neutral_proposals_count_toward_patience=False,
    )
    result = hill_climb(ciphertext, ConstantModel(), random.Random(7), config)
    assert result.total_proposals == 14
    assert result.non_neutral_proposals == 14
    assert result.neutral_proposals == 0
    assert result.proposals_per_restart == (7, 7)
    assert result.early_stopped_restarts == 0
    assert result.score_calls == 16
    assert 1 <= result.distinct_plaintexts_visited <= result.score_calls

    annealing = simulated_annealing(
        ciphertext,
        ConstantModel(),
        random.Random(7),
        SearchConfig(**{**config.__dict__, "algorithm": "simulated_annealing"}),
    )
    assert annealing.total_proposals == 14
    assert annealing.non_neutral_proposals == 14
    assert annealing.proposals_per_restart == (7, 7)


def test_resume_skips_completed_trials(tmp_path):
    train = ["this is ordinary english training material " * 50]
    test = ["this unseen document contains enough letters for a small trial " * 30]
    config = ExperimentConfig(
        lengths=(25,),
        trials_per_length=2,
        seed=123,
        ngram_order=3,
        search=SearchConfig(restarts=1, iterations=20, patience=10, archive_size=10),
    )
    output = tmp_path / "resume.csv"
    run_experiment(train, test, config, output, batch_size=1)
    complete_rows = read_csv(output)
    first_row = complete_rows[0]
    write_csv([first_row], output)

    metadata_path = output.with_suffix(".metadata.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["run_state"].update({
        "status": "running",
        "completed_trials": 1,
        "remaining_trials": 1,
    })
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    resumed = run_experiment(
        train,
        test,
        config,
        output,
        batch_size=1,
        resume=True,
    )
    assert len(resumed) == 2
    assert {(int(row["length"]), int(row["trial"])) for row in resumed} == {
        (25, 0),
        (25, 1),
    }
    assert resumed[0]["trial_seed"] == first_row["trial_seed"]
    final_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert final_metadata["run_state"]["status"] == "completed"
    assert final_metadata["run_state"]["completed_trials"] == 2
    assert final_metadata["run_state"]["remaining_trials"] == 0
