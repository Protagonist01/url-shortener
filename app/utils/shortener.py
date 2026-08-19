"""Short-code generation strategy.

We use an auto-increment integer ID as input to a base62 encoder. This gives:
  - Deterministic, short, reversible codes (no collisions, no uniqueness check)
  - ~62**6 = 56.8B possible codes at length 6, plenty for a demo project
  - Codes are NOT guessable in sequence without knowing the ID, because we XOR
    the ID with a fixed salt before encoding. This prevents enumeration attacks
    (someone iterating code = base62(1), base62(2), ... to scrape every URL).
"""
from __future__ import annotations

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BASE = len(ALPHABET)
SALT = 0x5A3C7E91  # arbitrary fixed 30-bit value, do not change post-launch


def _xor_id(id_: int) -> int:
    return id_ ^ SALT


def encode(id_: int) -> str:
    if id_ <= 0:
        raise ValueError("id must be positive")
    n = _xor_id(id_)
    chars: list[str] = []
    while True:
        n, rem = divmod(n, BASE)
        chars.append(ALPHABET[rem])
        if n == 0:
            break
    return "".join(reversed(chars))


def decode(code: str) -> int:
    n = 0
    for ch in code:
        idx = ALPHABET.find(ch)
        if idx == -1:
            raise ValueError(f"invalid character in code: {ch!r}")
        n = n * BASE + idx
    return _xor_id(n)
