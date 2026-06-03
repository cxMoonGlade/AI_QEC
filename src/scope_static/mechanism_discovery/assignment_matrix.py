from __future__ import annotations

import numpy as np


def normalize_rows(matrix: np.ndarray) -> np.ndarray:
    arr = np.asarray(matrix, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError("assignment matrix must be 2D")
    clipped = np.maximum(arr, 0.0)
    row_sum = np.sum(clipped, axis=1, keepdims=True)
    if np.any(row_sum <= 0.0):
        raise ValueError("assignment matrix contains an empty row")
    return clipped / row_sum


def normalize_rows_with_zeros(matrix: np.ndarray) -> np.ndarray:
    arr = np.asarray(matrix, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError("matrix must be 2D")
    clipped = np.maximum(arr, 0.0)
    row_sum = np.sum(clipped, axis=1, keepdims=True)
    if clipped.shape[1] == 0:
        return clipped
    out = np.divide(clipped, row_sum, out=np.zeros_like(clipped), where=row_sum > 0.0)
    zero_rows = np.where(np.squeeze(row_sum, axis=1) <= 0.0)[0]
    if zero_rows.size:
        out[zero_rows, :] = 1.0 / float(clipped.shape[1])
    return out
