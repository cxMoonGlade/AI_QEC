from __future__ import annotations

"""Temporal detector-record folding shared by simulator carriers.

The record layout is round-major on the final axis. For stabilizer outcome
``s(r, j)``, the detector event is ``det(0, j) = s(0, j)`` and
``det(r, j) = s(r, j) XOR s(r - 1, j)`` for later rounds. The inverse is the
prefix XOR over rounds. Consequently, both directions are the identity when
``R == 1``.
"""

import numpy as np


def s_to_det(s_bits, R: int, n_stab: int) -> np.ndarray:
    """Convert raw syndrome bits to temporal detector bits.

    ``s_bits`` is array-like with a final axis of length ``R * n_stab``, ordered
    round-major then stabilizer-major. The returned ``uint8`` array has the same
    shape.
    """

    R, n_stab = int(R), int(n_stab)
    if R < 1 or n_stab < 1:
        raise ValueError(f"R and n_stab must be positive, got R={R}, n_stab={n_stab}")
    s = np.asarray(s_bits, dtype=np.uint8)
    if s.shape[-1] != R * n_stab:
        raise ValueError(
            f"s_bits last axis {s.shape[-1]} != R*n_stab = {R * n_stab}"
        )
    shp = s.shape
    sr = s.reshape(shp[:-1] + (R, n_stab))
    det = np.empty_like(sr)
    det[..., 0, :] = sr[..., 0, :]
    if R > 1:
        det[..., 1:, :] = sr[..., 1:, :] ^ sr[..., :-1, :]
    return det.reshape(shp)


def det_to_s(det_bits, R: int, n_stab: int) -> np.ndarray:
    """Invert temporal detector bits to raw syndrome bits by prefix XOR."""

    R, n_stab = int(R), int(n_stab)
    if R < 1 or n_stab < 1:
        raise ValueError(f"R and n_stab must be positive, got R={R}, n_stab={n_stab}")
    det = np.asarray(det_bits, dtype=np.uint8)
    if det.shape[-1] != R * n_stab:
        raise ValueError(
            f"det_bits last axis {det.shape[-1]} != R*n_stab = {R * n_stab}"
        )
    shp = det.shape
    dr = det.reshape(shp[:-1] + (R, n_stab))
    s = np.bitwise_xor.accumulate(dr, axis=-2)
    return s.astype(np.uint8).reshape(shp)


__all__ = ["det_to_s", "s_to_det"]
