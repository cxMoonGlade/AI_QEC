"""Stim ``.b8`` record packing and chunked reading.

Bits are packed little-endian within each byte. Every shot is padded to a
byte boundary, so an on-disk array has shape
``[num_shots, ceil(bits_per_shot / 8)]`` in packed bytes.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import numpy as np


DEFAULT_CHUNK_SHOTS = 10_000


def packed_bytes_per_shot(bits_per_shot: int) -> int:
    """Return the byte-aligned packed width of one positive-width shot."""

    if int(bits_per_shot) <= 0:
        raise ValueError(f"bits_per_shot must be positive, got {bits_per_shot}")
    return (int(bits_per_shot) + 7) // 8


def num_shots_in_file(path: Path | str, bits_per_shot: int) -> int:
    """Return the exact shot count, rejecting partial packed shots."""

    bytes_per_shot = packed_bytes_per_shot(bits_per_shot)
    size = Path(path).stat().st_size
    if size % bytes_per_shot != 0:
        raise ValueError(
            f"b8 size mismatch: {path} has {size} bytes, not a multiple of "
            f"{bytes_per_shot} bytes/shot ({bits_per_shot} bits/shot)"
        )
    return size // bytes_per_shot


def _normalize_shot_slice(shot_slice, total_shots: int) -> tuple[int, int]:
    if shot_slice is None:
        return 0, total_shots
    if isinstance(shot_slice, slice):
        start, stop, step = shot_slice.indices(total_shots)
        if step != 1:
            raise ValueError("only contiguous shot slices are supported")
        return start, stop
    start, stop = int(shot_slice[0]), int(shot_slice[1])
    if not (0 <= start <= stop <= total_shots):
        raise ValueError(
            f"shot slice ({start}, {stop}) out of range for {total_shots} shots"
        )
    return start, stop


def read_b8(path: Path | str, bits_per_shot: int, shot_slice=None) -> np.ndarray:
    """Read packed uint8 records with shape ``[shots, ceil(bits / 8)]``."""

    bytes_per_shot = packed_bytes_per_shot(bits_per_shot)
    total = num_shots_in_file(path, bits_per_shot)
    start, stop = _normalize_shot_slice(shot_slice, total)
    count = (stop - start) * bytes_per_shot
    data = np.fromfile(
        str(path),
        dtype=np.uint8,
        count=count,
        offset=start * bytes_per_shot,
    )
    if data.size != count:
        raise ValueError(f"short read from {path}: got {data.size} bytes, expected {count}")
    return data.reshape(stop - start, bytes_per_shot)


def iter_b8_chunks(
    path: Path | str,
    bits_per_shot: int,
    *,
    chunk_shots: int = DEFAULT_CHUNK_SHOTS,
    shot_slice=None,
) -> Iterator[tuple[int, np.ndarray]]:
    """Yield ``(start_shot, packed_chunk)`` over a contiguous shot range."""

    total = num_shots_in_file(path, bits_per_shot)
    start, stop = _normalize_shot_slice(shot_slice, total)
    for chunk_start in range(start, stop, int(chunk_shots)):
        chunk_stop = min(chunk_start + int(chunk_shots), stop)
        yield chunk_start, read_b8(
            path,
            bits_per_shot,
            (chunk_start, chunk_stop),
        )


def unpack_bits(packed: np.ndarray, bits_per_shot: int) -> np.ndarray:
    """Unpack a packed chunk to bool records of the declared bit width."""

    packed_array = np.asarray(packed, dtype=np.uint8)
    if packed_array.ndim != 2:
        raise ValueError(
            f"expected [shots, bytes] packed array, got shape {packed_array.shape}"
        )
    bits = np.unpackbits(
        packed_array,
        axis=1,
        count=int(bits_per_shot),
        bitorder="little",
    )
    return bits.view(np.bool_)


def pack_bits(bits: np.ndarray) -> np.ndarray:
    """Pack bool/0-1 records to byte-aligned, little-endian Stim ``.b8``."""

    bit_array = np.asarray(bits)
    if bit_array.ndim != 2:
        raise ValueError(f"expected [shots, bits] array, got shape {bit_array.shape}")
    return np.packbits(
        bit_array.astype(np.uint8, copy=False),
        axis=1,
        bitorder="little",
    )


__all__ = [
    "DEFAULT_CHUNK_SHOTS",
    "iter_b8_chunks",
    "num_shots_in_file",
    "pack_bits",
    "packed_bytes_per_shot",
    "read_b8",
    "unpack_bits",
]
