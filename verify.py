# SPDX-License-Identifier: MIT
"""Verify that a vectors.jsonl file is self-consistent with the reference.

Used by CI to guard against a corrupted or out-of-date vector set. Any COBS
implementation can conform by checking its own encode/decode against the same
`decoded`/`cobs`/`cobsr` fields.
"""
import json
import sys

from reference import cobs_decode, cobs_encode, cobsr_decode, cobsr_encode


def main(path):
    count = 0
    with open(path, encoding="ascii") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            v = json.loads(line)
            data = bytes.fromhex(v["decoded"])
            cobs = bytes.fromhex(v["cobs"])
            cobsr = bytes.fromhex(v["cobsr"])
            assert cobs_encode(data) == cobs, f"line {line_no}: cobs mismatch"
            assert cobsr_encode(data) == cobsr, f"line {line_no}: cobsr mismatch"
            assert cobs_decode(cobs) == data, f"line {line_no}: cobs round-trip"
            assert cobsr_decode(cobsr) == data, f"line {line_no}: cobsr round-trip"
            assert 0 not in cobs and 0 not in cobsr, f"line {line_no}: zero byte"
            count += 1
    print(f"OK: {count} vectors verified against the reference.")
    return count


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "vectors/vectors.jsonl"
    if main(path) == 0:
        print("ERROR: no vectors found", file=sys.stderr)
        sys.exit(1)
