# SPDX-License-Identifier: MIT
"""Deterministically generate the COBS / COBS-R conformance vectors.

Run `python generate.py` to (re)write `vectors/vectors.jsonl`. Output is
deterministic: the same Python produces byte-identical vectors every run.
"""
import json
import os
import random

from reference import cobs_decode, cobs_encode, cobsr_decode, cobsr_encode


def non_zero_bytes(length):
    """Deterministic non-zero byte stream (matches the reference test suites)."""
    out = bytearray()
    while len(out) < length:
        for i in range(1, 50):
            for j in range(1, 256, i):
                if len(out) == length:
                    return bytes(out)
                out.append(j)
    return bytes(out)


def make_vector(data):
    cobs = cobs_encode(data)
    cobsr = cobsr_encode(data)
    assert cobs_decode(cobs) == data
    assert cobsr_decode(cobsr) == data
    assert 0 not in cobs and 0 not in cobsr
    return {"decoded": data.hex(), "cobs": cobs.hex(), "cobsr": cobsr.hex()}


def main():
    seen = set()
    vectors = []

    def add(data):
        data = bytes(data)
        if data in seen:
            return
        seen.add(data)
        vectors.append(make_vector(data))

    # 1. Every single-byte value.
    for b in range(256):
        add([b])

    # 2. Zero runs and non-zero runs around the 254-byte block boundaries.
    lengths = sorted(set(
        list(range(0, 20)) +
        [126, 127, 128, 252, 253, 254, 255, 256, 257,
         507, 508, 509, 510, 762, 763, 764]
    ))
    for n in lengths:
        add(b"\x00" * n)
        nz = non_zero_bytes(n)
        add(nz)
        add(nz + b"\x00")
        add(b"\x00" + nz)

    # 3. The full 0x00..0xFF ramp and a few slices.
    ramp = bytes(range(256))
    for sl in (ramp, ramp[1:], ramp[2:], ramp[1:255], ramp[1:256]):
        add(sl)

    # 4. Deterministic pseudo-random sample, biased toward short lengths, block
    #    boundaries, and zero/0xFF-heavy content.
    rng = random.Random(0xC0B5C0DE)
    for _ in range(2000):
        pick = rng.random()
        if pick < 0.2:
            length = rng.randint(0, 8)
        elif pick < 0.35:
            length = rng.choice([253, 254, 255, 256, 508, 509])
        else:
            length = rng.randint(0, 600)
        if rng.random() < 0.5:
            data = bytes(rng.randint(0, 255) for _ in range(length))
        else:
            data = bytes(rng.choice([0, 0, 1, 254, 255, rng.randint(0, 255)])
                         for _ in range(length))
        add(data)

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vectors")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "vectors.jsonl")
    with open(path, "w", encoding="ascii", newline="\n") as f:
        for v in vectors:
            f.write(json.dumps(v, separators=(",", ":")) + "\n")
    print(f"wrote {len(vectors)} vectors to {path}")


if __name__ == "__main__":
    main()
