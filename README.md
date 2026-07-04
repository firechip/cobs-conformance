# cobs-conformance

[![CI](https://github.com/firechip/cobs-conformance/actions/workflows/ci.yml/badge.svg)](https://github.com/firechip/cobs-conformance/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Canonical **conformance test vectors** for **Consistent Overhead Byte Stuffing
(COBS)** and **COBS/R (Reduced)**. This is the single source of truth that keeps
the Firechip COBS implementations byte-identical across languages, and it lets
any third-party implementation prove conformance too.

## What is COBS?

COBS encodes an arbitrary byte string into one that contains no zero (`0x00`)
bytes, at a small, predictable cost (at most one extra byte per 254 bytes, plus
one). A single `0x00` can then reliably delimit packets on a byte stream. See
Cheshire & Baker, *"Consistent Overhead Byte Stuffing"*, IEEE/ACM Transactions
on Networking, Vol. 7, No. 2, April 1999. COBS/R is a variant by Craig McQueen
that often removes the trailing overhead byte.

## The vectors

`vectors/vectors.jsonl` is [JSON Lines](https://jsonlines.org): one JSON object
per line, all fields lowercase hex strings:

```json
{"decoded":"","cobs":"01","cobsr":"01"}
{"decoded":"02","cobs":"0202","cobsr":"02"}
{"decoded":"110022","cobs":"02110222","cobsr":"021122"}
{"decoded":"3132333435","cobs":"063132333435","cobsr":"3531323334"}
```

| Field | Meaning |
| ----- | ------- |
| `decoded` | the original bytes (hex) |
| `cobs` | the basic-COBS encoding of `decoded` (hex) |
| `cobsr` | the COBS/R encoding of `decoded` (hex) |

The set covers every single-byte value, zero/non-zero runs around the 254-byte
block boundaries, the full `0x00..0xFF` ramp, and a large deterministic
pseudo-random sample biased toward edge cases.

## Conform your implementation

For every line, decode the hex fields and assert:

1. `your_cobs_encode(decoded) == cobs`
2. `your_cobsr_encode(decoded) == cobsr`
3. `your_cobs_decode(cobs) == decoded` and `your_cobsr_decode(cobsr) == decoded`
4. neither `cobs` nor `cobsr` contains a `0x00` byte

CI in each implementation repo downloads this file and runs exactly these
checks.

## Regenerating / verifying

Pure Python 3, no dependencies:

```console
python generate.py                    # rewrites vectors/vectors.jsonl (deterministic)
python verify.py vectors/vectors.jsonl # checks the file against reference.py
```

`reference.py` is the canonical reference implementation the vectors are
generated from.

## Implementations

| Language | Package |
| -------- | ------- |
| Dart / Flutter | [`cobs_codec`](https://pub.dev/packages/cobs_codec) ([repo](https://github.com/firechip/cobs_codec)) |
| Kotlin / Android | [`cobs_codec_kt`](https://github.com/firechip/cobs_codec_kt) |

## License

MIT (c) 2026 Alexander Salas Bastidas ([Firechip](https://firechip.dev)). See
[LICENSE](LICENSE). COBS/R and the reference implementation follow Craig
McQueen's MIT-licensed work.
