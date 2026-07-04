# SPDX-License-Identifier: MIT
"""Reference pure-Python implementation of COBS and COBS/R.

This is the canonical implementation used to generate the conformance vectors.
The algorithms are those described in:

    Stuart Cheshire and Mary Baker, "Consistent Overhead Byte Stuffing",
    IEEE/ACM Transactions on Networking, Vol. 7, No. 2, April 1999.

COBS/R (Reduced) is a variant devised by Craig McQueen; this reference follows
his MIT-licensed pure-Python implementation.
"""


class DecodeError(Exception):
    """Raised when input is not a valid COBS/COBS-R encoding."""


def cobs_encode(in_bytes):
    """Encode ``in_bytes`` (bytes) with basic COBS. Returns bytes."""
    final_zero = True
    out_bytes = bytearray()
    idx = 0
    search_start_idx = 0
    for in_char in in_bytes:
        if in_char == 0:
            final_zero = True
            out_bytes.append(idx - search_start_idx + 1)
            out_bytes += in_bytes[search_start_idx:idx]
            search_start_idx = idx + 1
        else:
            if idx - search_start_idx == 0xFD:
                final_zero = False
                out_bytes.append(0xFF)
                out_bytes += in_bytes[search_start_idx:idx + 1]
                search_start_idx = idx + 1
        idx += 1
    if idx != search_start_idx or final_zero:
        out_bytes.append(idx - search_start_idx + 1)
        out_bytes += in_bytes[search_start_idx:idx]
    return bytes(out_bytes)


def cobs_decode(in_bytes):
    """Decode basic-COBS ``in_bytes``. Raises DecodeError on invalid input."""
    out_bytes = bytearray()
    idx = 0
    if len(in_bytes) > 0:
        while True:
            length = in_bytes[idx]
            if length == 0:
                raise DecodeError("zero byte found in input")
            idx += 1
            end = idx + length - 1
            copy = in_bytes[idx:end]
            if 0 in copy:
                raise DecodeError("zero byte found in input")
            out_bytes += copy
            idx = end
            if idx > len(in_bytes):
                raise DecodeError("not enough input bytes for length code")
            if idx < len(in_bytes):
                if length < 0xFF:
                    out_bytes.append(0)
            else:
                break
    return bytes(out_bytes)


def cobsr_encode(in_bytes):
    """Encode ``in_bytes`` with COBS/R (Reduced). Returns bytes."""
    out_bytes = bytearray()
    idx = 0
    search_start_idx = 0
    for in_char in in_bytes:
        if idx - search_start_idx == 0xFE:
            out_bytes.append(0xFF)
            out_bytes += in_bytes[search_start_idx:idx]
            search_start_idx = idx
        if in_char == 0:
            out_bytes.append(idx - search_start_idx + 1)
            out_bytes += in_bytes[search_start_idx:idx]
            search_start_idx = idx + 1
        idx += 1
    try:
        final_byte_value = in_bytes[-1]
    except IndexError:
        final_byte_value = 0
    length_value = idx - search_start_idx + 1
    if final_byte_value < length_value:
        out_bytes.append(length_value)
        out_bytes += in_bytes[search_start_idx:idx]
    else:
        out_bytes.append(final_byte_value)
        out_bytes += in_bytes[search_start_idx:idx - 1]
    return bytes(out_bytes)


def cobsr_decode(in_bytes):
    """Decode COBS/R ``in_bytes``. Raises DecodeError on invalid input."""
    out_bytes = bytearray()
    idx = 0
    if len(in_bytes) > 0:
        while True:
            length = in_bytes[idx]
            if length == 0:
                raise DecodeError("zero byte found in input")
            idx += 1
            end = idx + length - 1
            copy = in_bytes[idx:end]
            if 0 in copy:
                raise DecodeError("zero byte found in input")
            out_bytes += copy
            idx = end
            if idx > len(in_bytes):
                out_bytes.append(length)
                break
            elif idx < len(in_bytes):
                if length < 0xFF:
                    out_bytes.append(0)
            else:
                break
    return bytes(out_bytes)


def _xor(data, sentinel):
    """XOR every byte of ``data`` with ``sentinel`` (a no-op when sentinel==0)."""
    if sentinel == 0:
        return bytes(data)
    return bytes(b ^ sentinel for b in data)


# Configurable-sentinel variants. A single, arbitrary "sentinel" byte replaces
# 0x00 as the value the encoding avoids (so it can delimit frames). The scheme is
# XOR-over-the-finished-encoding: encode/decode normally, then XOR the whole byte
# stream with the sentinel. ``sentinel == 0`` is byte-for-byte identical to the
# plain codec. Every Firechip implementation uses this exact method, which is why
# the sentinel encoding stays byte-identical across languages.


def cobs_encode_with_sentinel(in_bytes, sentinel):
    """Encode ``in_bytes`` with basic COBS using an arbitrary ``sentinel`` byte."""
    return _xor(cobs_encode(in_bytes), sentinel)


def cobs_decode_with_sentinel(in_bytes, sentinel):
    """Decode basic-COBS ``in_bytes`` encoded with an arbitrary ``sentinel``."""
    return cobs_decode(_xor(in_bytes, sentinel))


def cobsr_encode_with_sentinel(in_bytes, sentinel):
    """Encode ``in_bytes`` with COBS/R using an arbitrary ``sentinel`` byte."""
    return _xor(cobsr_encode(in_bytes), sentinel)


def cobsr_decode_with_sentinel(in_bytes, sentinel):
    """Decode COBS/R ``in_bytes`` encoded with an arbitrary ``sentinel``."""
    return cobsr_decode(_xor(in_bytes, sentinel))
