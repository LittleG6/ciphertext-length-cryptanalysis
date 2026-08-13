"""文本规范化、单表代换加密和解密。"""

from __future__ import annotations

import random
import re
import string

ALPHABET = string.ascii_lowercase
ALPHABET_SIZE = len(ALPHABET)


def normalize_text(text: str) -> str:
    """转小写，仅保留英文字母和单个空格。"""
    text = text.lower()
    text = re.sub(r"[^a-z]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def letter_count(text: str) -> int:
    return sum("a" <= char <= "z" for char in text)


def letters_only(text: str) -> str:
    """删除所有非英文字母字符，包括会泄露词边界的空格。"""
    return "".join(char for char in normalize_text(text) if "a" <= char <= "z")


def group_blocks(text: str, block_size: int = 5) -> str:
    """把字母流格式化为固定长度分组；分组空格不参与语言模型评分。"""
    if block_size <= 0:
        raise ValueError("block_size must be positive")
    stream = letters_only(text)
    return " ".join(stream[index : index + block_size] for index in range(0, len(stream), block_size))


def random_encryption_key(rng: random.Random) -> tuple[int, ...]:
    """返回 plain_index -> cipher_index 的均匀随机排列。"""
    key = list(range(ALPHABET_SIZE))
    rng.shuffle(key)
    return tuple(key)


def inverse_key(encryption_key: tuple[int, ...]) -> tuple[int, ...]:
    """把加密密钥转换为 cipher_index -> plain_index 的解密密钥。"""
    if sorted(encryption_key) != list(range(ALPHABET_SIZE)):
        raise ValueError("key must be a permutation of 0..25")
    result = [0] * ALPHABET_SIZE
    for plain_index, cipher_index in enumerate(encryption_key):
        result[cipher_index] = plain_index
    return tuple(result)


def encrypt(plaintext: str, encryption_key: tuple[int, ...]) -> str:
    table = str.maketrans(
        ALPHABET,
        "".join(ALPHABET[index] for index in encryption_key),
    )
    return plaintext.translate(table)


def decrypt(ciphertext: str, decryption_key: tuple[int, ...]) -> str:
    """使用 cipher_index -> plain_index 的密钥解密，非字母原样保留。"""
    table = str.maketrans(
        ALPHABET,
        "".join(ALPHABET[index] for index in decryption_key),
    )
    return ciphertext.translate(table)


def sample_by_letter_length_with_start(
    text: str,
    length: int,
    rng: random.Random,
    *,
    include_spaces: bool = True,
) -> tuple[str, int]:
    """随机截取恰含 length 个字母的连续片段并返回字母起点序号。"""
    if length <= 0:
        raise ValueError("length must be positive")
    normalized = normalize_text(text)
    positions = [i for i, char in enumerate(normalized) if "a" <= char <= "z"]
    if len(positions) < length:
        raise ValueError(f"document has {len(positions)} letters, fewer than {length}")
    start_ordinal = rng.randrange(0, len(positions) - length + 1)
    if not include_spaces:
        stream = letters_only(normalized)
        return stream[start_ordinal : start_ordinal + length], start_ordinal
    start = positions[start_ordinal]
    end = positions[start_ordinal + length - 1] + 1
    return normalized[start:end].strip(), start_ordinal


def sample_by_letter_length(
    text: str,
    length: int,
    rng: random.Random,
    *,
    include_spaces: bool = True,
) -> str:
    """兼容接口：随机截取恰含 length 个字母的连续片段。"""
    sample, _ = sample_by_letter_length_with_start(
        text,
        length,
        rng,
        include_spaces=include_spaces,
    )
    return sample
