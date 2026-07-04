# SPDX-License-Identifier: MIT
"""Verify that the vector files are self-consistent with the reference.

Used by CI to guard against a corrupted or out-of-date vector set, and a template
any implementation can follow to prove conformance. With no arguments it verifies
all three files in ``vectors/``; a path argument verifies just that file (its
schema is chosen by basename).

  vectors.jsonl   {decoded, cobs, cobsr}            plain COBS / COBS-R
  sentinel.jsonl  {decoded, sentinel, cobs, cobsr}  configurable-sentinel codec
  errors.jsonl    {encoded, cobs, cobsr}            decode outcome (hex or null)
"""
import json
import os
import sys

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


def _rows(path):
    with open(path, encoding="ascii") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if line:
                yield line_no, json.loads(line)


def verify_vectors(path):
    count = 0
    for line_no, v in _rows(path):
        data = bytes.fromhex(v["decoded"])
        cobs = bytes.fromhex(v["cobs"])
        cobsr = bytes.fromhex(v["cobsr"])
        assert cobs_encode(data) == cobs, f"{path}:{line_no}: cobs mismatch"
        assert cobsr_encode(data) == cobsr, f"{path}:{line_no}: cobsr mismatch"
        assert cobs_decode(cobs) == data, f"{path}:{line_no}: cobs round-trip"
        assert cobsr_decode(cobsr) == data, f"{path}:{line_no}: cobsr round-trip"
        assert 0 not in cobs and 0 not in cobsr, f"{path}:{line_no}: zero byte"
        count += 1
    return count


def verify_sentinel(path):
    count = 0
    for line_no, v in _rows(path):
        data = bytes.fromhex(v["decoded"])
        sentinel = int(v["sentinel"], 16)
        cobs = bytes.fromhex(v["cobs"])
        cobsr = bytes.fromhex(v["cobsr"])
        assert cobs_encode_with_sentinel(data, sentinel) == cobs, f"{path}:{line_no}: cobs"
        assert cobsr_encode_with_sentinel(data, sentinel) == cobsr, f"{path}:{line_no}: cobsr"
        assert cobs_decode_with_sentinel(cobs, sentinel) == data, f"{path}:{line_no}: cobs rt"
        assert cobsr_decode_with_sentinel(cobsr, sentinel) == data, f"{path}:{line_no}: cobsr rt"
        assert sentinel not in cobs and sentinel not in cobsr, f"{path}:{line_no}: sentinel byte"
        count += 1
    return count


def _check_decode(fn, encoded, expected_hex, where):
    if expected_hex is None:
        try:
            fn(encoded)
        except DecodeError:
            return
        raise AssertionError(f"{where}: expected a decode failure, got success")
    assert fn(encoded).hex() == expected_hex, f"{where}: decode mismatch"


def verify_errors(path):
    count = 0
    for line_no, v in _rows(path):
        encoded = bytes.fromhex(v["encoded"])
        _check_decode(cobs_decode, encoded, v["cobs"], f"{path}:{line_no} cobs")
        _check_decode(cobsr_decode, encoded, v["cobsr"], f"{path}:{line_no} cobsr")
        count += 1
    return count


VERIFIERS = {
    "vectors.jsonl": verify_vectors,
    "sentinel.jsonl": verify_sentinel,
    "errors.jsonl": verify_errors,
}


def main(paths):
    total = 0
    for path in paths:
        verifier = VERIFIERS.get(os.path.basename(path), verify_vectors)
        n = verifier(path)
        print(f"OK: {n} vectors verified in {path}")
        total += n
    return total


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vectors")
        args = [os.path.join(base, name) for name in VERIFIERS]
    if main(args) == 0:
        print("ERROR: no vectors found", file=sys.stderr)
        sys.exit(1)
