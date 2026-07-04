# SPDX-License-Identifier: MIT
"""Deterministically generate the COBS / COBS-R conformance vectors.

Run `python generate.py` to (re)write `vectors/vectors.jsonl`. Output is
deterministic: the same Python produces byte-identical vectors every run.
"""
import json
import os
import random

from reference import (
    DecodeError,
    cobs_decode,
    cobs_decode_with_sentinel,
    cobs_encode,
    cobs_encode_with_sentinel,
    cobsr_decode,
    cobsr_decode_with_sentinel,
    cobsr_encode,
    cobsr_encode_with_sentinel,
)


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


# Sentinels exercised by the configurable-sentinel vectors: 0x00 (== plain),
# a low byte, a mid byte, the ASCII boundary, and the two extremes.
SENTINELS = [0x00, 0x01, 0x2A, 0x7F, 0xAA, 0xFF]


def make_sentinel_vector(data, sentinel):
    cobs = cobs_encode_with_sentinel(data, sentinel)
    cobsr = cobsr_encode_with_sentinel(data, sentinel)
    assert cobs_decode_with_sentinel(cobs, sentinel) == data
    assert cobsr_decode_with_sentinel(cobsr, sentinel) == data
    assert sentinel not in cobs and sentinel not in cobsr
    return {
        "decoded": data.hex(),
        "sentinel": f"{sentinel:02x}",
        "cobs": cobs.hex(),
        "cobsr": cobsr.hex(),
    }


def build_sentinel_vectors():
    """A curated input set crossed with every sentinel (deterministic)."""
    inputs = []
    seen = set()

    def add(data):
        data = bytes(data)
        if data not in seen:
            seen.add(data)
            inputs.append(data)

    add(b"")
    for b in (0x00, 0x01, 0x11, 0x7F, 0xAA, 0xFE, 0xFF):
        add([b])
        add([b, b])
        add([b, 0x00, b])
    add(b"\x11\x00\x22")
    add(b"12345")
    add(non_zero_bytes(254))
    add(non_zero_bytes(255))
    add(b"\x00" * 5)
    add(bytes(range(20)))
    rng = random.Random(0x5E17C0DE)
    for _ in range(30):
        length = rng.randint(0, 300)
        add(bytes(rng.randint(0, 255) for _ in range(length)))

    return [make_sentinel_vector(data, s) for s in SENTINELS for data in inputs]


def _decode_or_none(fn, encoded):
    try:
        return fn(encoded).hex()
    except DecodeError:
        return None


def make_error_vector(encoded):
    """Record the reference's decode outcome for a raw (maybe invalid) frame.

    ``cobs`` / ``cobsr`` hold the decoded output (hex) when the frame is valid
    under that scheme, or ``null`` when decoding must fail. The same bytes can be
    valid COBS/R (reduced final block) yet invalid basic COBS (truncated).
    """
    return {
        "encoded": encoded.hex(),
        "cobs": _decode_or_none(cobs_decode, encoded),
        "cobsr": _decode_or_none(cobsr_decode, encoded),
    }


def build_error_vectors():
    """Curated edge frames: valid-both, valid-COBS/R-only, and invalid-both."""
    candidates = [
        b"",                             # empty -> valid, decodes to empty
        b"\x01",                         # empty block -> valid, empty
        b"\x02\x11",                     # valid small frame
        b"\x03\x11\x22",                 # valid two-byte frame
        b"\x02\x11\x02\x22",             # valid multi-block
        b"\x01\x01\x01",                 # valid, decodes to zeros
        b"\x06\x31\x32\x33\x34\x35",     # valid basic-COBS "12345"
        b"\x35\x31\x32\x33\x34",         # valid COBS/R "12345"; invalid basic COBS
        b"\x05\x11",                     # basic COBS truncated; COBS/R reduced
        b"\x04\x11\x22",                 # basic COBS truncated; COBS/R reduced
        b"\xfe",                         # len 254, no data
        b"\xff",                         # len 255, no data
        b"\xff" + bytes(range(1, 254)),  # 0xFF block, one byte short
        b"\xff" + bytes(range(1, 255)),  # 0xFF block, full 254 data
        b"\x00",                         # leading zero -> invalid both
        b"\x01\x00",                     # trailing zero -> invalid both
        b"\x02\x00",                     # zero in block -> invalid both
        b"\x03\x11\x00",                 # zero in block -> invalid both
        b"\x02\x11\x00\x22",             # zero mid-frame -> invalid both
        bytes([0xFF]) + bytes([0x00]),   # 0xFF then zero -> invalid both
    ]
    seen = set()
    out = []
    for enc in candidates:
        enc = bytes(enc)
        if enc not in seen:
            seen.add(enc)
            out.append(make_error_vector(enc))
    return out


def write_jsonl(path, rows):
    with open(path, "w", encoding="ascii", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, separators=(",", ":")) + "\n")


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
    write_jsonl(path, vectors)
    print(f"wrote {len(vectors)} vectors to {path}")

    sentinel_vectors = build_sentinel_vectors()
    s_path = os.path.join(out_dir, "sentinel.jsonl")
    write_jsonl(s_path, sentinel_vectors)
    print(f"wrote {len(sentinel_vectors)} sentinel vectors to {s_path}")

    error_vectors = build_error_vectors()
    e_path = os.path.join(out_dir, "errors.jsonl")
    write_jsonl(e_path, error_vectors)
    print(f"wrote {len(error_vectors)} error vectors to {e_path}")


if __name__ == "__main__":
    main()
