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

### Extended vectors

Two companion files cover the capabilities beyond the plain `0x00` codec (all
fields are still lowercase hex).

`vectors/sentinel.jsonl` — the **configurable-sentinel** codec, where an
arbitrary byte (not `0x00`) is the value the encoding avoids. Encoding is
XOR-over-the-finished-stream, so a `sentinel` of `00` equals the plain codec:

```json
{"decoded":"1100aa","sentinel":"aa","cobs":"a8bba800","cobsr":"a8bb00"}
```

| Field | Meaning |
| ----- | ------- |
| `decoded` | the original bytes (hex) |
| `sentinel` | the delimiter byte the encoding avoids (one hex byte) |
| `cobs` / `cobsr` | the sentinel encoding of `decoded` (hex) |

`vectors/errors.jsonl` — decode **outcomes** for raw, often malformed frames, so
error behaviour is conformance-checked too:

```json
{"encoded":"0511","cobs":null,"cobsr":"1105"}
```

| Field | Meaning |
| ----- | ------- |
| `encoded` | a raw frame to decode (hex) |
| `cobs` | basic-COBS decode result (hex), or `null` if decoding must fail |
| `cobsr` | COBS/R decode result (hex), or `null` if decoding must fail |

The same bytes can be valid COBS/R (a reduced final block) yet invalid basic
COBS (a truncated frame) — the example above is exactly that divergence.

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

The Firechip COBS family, all verified byte-identical against these vectors:

| Language | Package |
| -------- | ------- |
| Rust | [`cobs_codec_rs`](https://crates.io/crates/cobs_codec_rs) ([repo](https://github.com/firechip/cobs_codec_rs)) |
| Dart / Flutter | [`cobs_codec`](https://pub.dev/packages/cobs_codec) ([repo](https://github.com/firechip/cobs_codec)) |
| Kotlin / Android | [`cobs_codec`](https://github.com/firechip/cobs_codec_kt) (Maven `dev.firechip:cobs_codec`) |
| Swift (macOS/iOS/Linux) | [`CobsCodec`](https://github.com/firechip/cobs_codec_swift) (Swift Package Manager) |

### Feature comparison

How the family compares with Craig McQueen's reference implementations and other
ecosystem crates. Legend: ✓ supported · ◐ partial · ○ not supported · · not
applicable.

| Feature | `cobs_codec_rs` | `cobs_codec` · Dart | `cobs_codec` · Kotlin | `CobsCodec` · Swift | cobs-c | cobs · Python | libcobs | cobs · jamesmunns | cobs-codec · alvra | GlassGem · Swift | SerialFiller · C++ | KiTools · Python |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Basic COBS | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| COBS/R (reduced) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ○ | ○ | ○ | ○ | ○ | ○ |
| Configurable sentinel | ✓ | ✓ | ✓ | ✓ | ○ | ○ | ○ | ✓ | ✓ | ○ | ○ | ○ |
| In-place decode | ✓ | ✓ | ✓ | ✓ | ○ | ○ | ○ | ✓ | ○ | ○ | ○ | ○ |
| Incremental / streaming decode | ✓ | ✓ | ✓ | ✓ | ○ | ○ | ○ | ✓ | ✓ (async) | ○ | ○ | ✓ |
| Frame delimiting | ✓ | ✓ | ✓ | ✓ | ○ | ○ | ○ | ◐ | ✓ | ◐ | ○ | ◐ |
| Size helpers (max length) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ○ | ✓ | ○ | ○ | ○ | ○ |
| Typed error reporting | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ◐ | ✓ | ✓ | ○ | ✓ | ◐ |
| `no_std` / freestanding | ✓ | · | · | · | ✓ | ○ | ✓ | ✓ | ○ | · | ○ | · |
| Zero dependencies | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ○ | ○ | ✓ | ✓ | ○ |
| Native framework hooks | ◐ (serde/defmt) | ✓ (`dart:convert`) | ✓ (java.io/Flow) | ○ | ○ | ○ | ○ | ◐ (serde/defmt) | ✓ (tokio-util) | ○ | ○ | ○ |
| Verified against these vectors | ✓ | ✓ | ✓ | ✓ | source | source | ○ | ○ | ○ | ○ | ○ | ○ |

The first four columns are the Firechip family. **cobs-c** and **cobs** (Python)
are McQueen's references and the *source* of these vectors. **libcobs** is a
minimal basic-COBS implementation. **cobs** (jamesmunns) is the de-facto embedded
Rust crate, rich but with no COBS/R and not dependency-free. **cobs-codec**
(alvra) is an async Tokio framing codec. **GlassGem** (armadsen) is a third-party
Swift `Data` extension implementing basic COBS only — Foundation-based, with no
COBS/R and no configurable delimiter (both on its roadmap), which the family's
stdlib-only `CobsCodec` provides. **SerialFiller** (gbmhunter) and **KiTools**
(Kirale) embed basic COBS inside larger tools — a C++ serial-framing library and
a Python Thread / 802.15.4 CLI — rather than shipping it as a reusable package;
KiTools is notable for a byte-for-byte streaming decoder.

## License

MIT (c) 2026 Alexander Salas Bastidas ([Firechip](https://firechip.dev)). See
[LICENSE](LICENSE). COBS/R and the reference implementation follow Craig
McQueen's MIT-licensed work.
