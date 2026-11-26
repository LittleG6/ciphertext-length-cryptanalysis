import random

from substitution_rank.cipher import (
    decrypt,
    encrypt,
    inverse_key,
    group_blocks,
    letter_count,
    letters_only,
    normalize_text,
    random_encryption_key,
    sample_by_letter_length,
)


def test_encrypt_decrypt_round_trip():
    rng = random.Random(7)
    key = random_encryption_key(rng)
    plaintext = "this is a reproducible test"
    assert decrypt(encrypt(plaintext, key), inverse_key(key)) == plaintext


def test_normalize_and_sample_exact_letter_count():
    text = normalize_text("Hello, WORLD! This is sample number 42.")
    sample = sample_by_letter_length(text, 12, random.Random(3))
    assert letter_count(sample) == 12
    assert set(sample) <= set("abcdefghijklmnopqrstuvwxyz ")


def test_remove_spaces_and_group_in_blocks_of_five():
    assert letters_only("Meet me, at 10!") == "meetmeat"
    assert group_blocks("Meet me, at 10!") == "meetm eat"
    sample = sample_by_letter_length(
        "one two three four five",
        8,
        random.Random(3),
        include_spaces=False,
    )
    assert len(sample) == 8
    assert " " not in sample
