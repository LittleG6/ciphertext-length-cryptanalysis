import random

from substitution_rank.language_model import NGramLanguageModel


def test_score_is_deterministic_and_favors_regular_text():
    corpus = ["the quick brown fox jumps over the lazy dog " * 30]
    model = NGramLanguageModel(order=3, alpha=0.1).fit(corpus)
    natural = "the quick brown fox jumps over the lazy dog"
    shuffled = list(natural.replace(" ", ""))
    random.Random(1).shuffle(shuffled)
    shuffled_text = "".join(shuffled)
    assert model.score(natural) == model.score(natural)
    assert model.score(natural) > model.score(shuffled_text)

