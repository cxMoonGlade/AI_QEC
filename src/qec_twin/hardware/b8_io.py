"""Chunked reader for stim ``.b8`` shot files.

Format: little-endian bit packing within bytes; each shot padded to a byte
boundary, so a file is ``num_shots x ceil(bits_per_shot / 8)`` raw bytes.
Readers return PACKED uint8 arrays; a full corpus file is never materialized
unpacked (350 MB packed would become ~2.8 GB of bools).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import numpy as np

DEFAULT_CHUNK_SHOTS = 10_000


def packed_bytes_per_shot(bits_per_shot: int) -> int:
    if int(bits_per_shot) <= 0:
        raise ValueError(f"bits_per_shot must be positive, got {bits_per_shot}")
    return (int(bits_per_shot) + 7) // 8


def num_shots_in_file(path: Path | str, bits_per_shot: int) -> int:
    """Shot count from the exact file size; raises on a non-integer shot count."""

    bps = packed_bytes_per_shot(bits_per_shot)
    size = Path(path).stat().st_size
    if size % bps != 0:
        raise ValueError(
            f"b8 size mismatch: {path} has {size} bytes, not a multiple of "
            f"{bps} bytes/shot ({bits_per_shot} bits/shot)"
        )
    return size // bps


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
        raise ValueError(f"shot slice ({start}, {stop}) out of range for {total_shots} shots")
    return start, stop


def read_b8(path: Path | str, bits_per_shot: int, shot_slice=None) -> np.ndarray:
    """Packed uint8 ``[shots, ceil(bits/8)]`` for the requested shot range."""

    bps = packed_bytes_per_shot(bits_per_shot)
    total = num_shots_in_file(path, bits_per_shot)
    start, stop = _normalize_shot_slice(shot_slice, total)
    count = (stop - start) * bps
    data = np.fromfile(str(path), dtype=np.uint8, count=count, offset=start * bps)
    if data.size != count:
        raise ValueError(f"short read from {path}: got {data.size} bytes, expected {count}")
    return data.reshape(stop - start, bps)


def iter_b8_chunks(
    path: Path | str,
    bits_per_shot: int,
    *,
    chunk_shots: int = DEFAULT_CHUNK_SHOTS,
    shot_slice=None,
) -> Iterator[tuple[int, np.ndarray]]:
    """Yields ``(start_shot, packed_chunk)`` in ~``chunk_shots``-shot pieces."""

    total = num_shots_in_file(path, bits_per_shot)
    start, stop = _normalize_shot_slice(shot_slice, total)
    for chunk_start in range(start, stop, int(chunk_shots)):
        chunk_stop = min(chunk_start + int(chunk_shots), stop)
        yield chunk_start, read_b8(path, bits_per_shot, (chunk_start, chunk_stop))


def unpack_bits(packed: np.ndarray, bits_per_shot: int) -> np.ndarray:
    """Unpack a CHUNK-SIZED packed array to bool ``[shots, bits_per_shot]``.

    Never call this on a whole corpus file — go through ``iter_b8_chunks``.
    """

    packed = np.asarray(packed, dtype=np.uint8)
    if packed.ndim != 2:
        raise ValueError(f"expected [shots, bytes] packed array, got shape {packed.shape}")
    bits = np.unpackbits(packed, axis=1, count=int(bits_per_shot), bitorder="little")
    return bits.view(np.bool_)


def pack_bits(bits: np.ndarray) -> np.ndarray:
    """Pack bool/0-1 ``[shots, bits]`` back to b8 layout (little-endian, padded)."""

    bits = np.asarray(bits)
    if bits.ndim != 2:
        raise ValueError(f"expected [shots, bits] array, got shape {bits.shape}")
    return np.packbits(bits.astype(np.uint8, copy=False), axis=1, bitorder="little")
