"""Spitz Eq. 13 exact two-point estimators for emitted detector records."""

from __future__ import annotations

import numpy as np

from ..numerics import NUMERICAL_ZERO


def spitz_pij_exact(
    mean_i: np.ndarray,
    mean_j: np.ndarray,
    mean_joint: np.ndarray,
) -> np.ndarray:
    """Spitz et al. arXiv:1712.02360 **Eq. 13, EXACT form**.

    ``p_ij = 1/2 - sqrt(1/4 - cov(x_i, x_j) / (1 - 2<x_i XOR x_j>))``

    Here ``cov = <x_i x_j> - <x_i><x_j>`` and
    ``<x_i XOR x_j> = <x_i> + <x_j> - 2<x_i x_j>``. This estimator is
    two-point only and is structurally blind to hyperedges. Negative outputs
    are meaningful sampling noise around null pairs and are not floored.
    """

    mi = np.asarray(mean_i, dtype=np.float64)
    mj = np.asarray(mean_j, dtype=np.float64)
    mij = np.asarray(mean_joint, dtype=np.float64)
    cov = mij - mi * mj
    denom = 1.0 - 2.0 * (mi + mj - 2.0 * mij)
    radicand = 0.25 - cov / denom
    return 0.5 - np.sqrt(np.clip(radicand, 0.0, None))


def _pij_gradients(mi: np.ndarray, mj: np.ndarray, mij: np.ndarray):
    """d p_ij / d(<x_i>, <x_j>, <x_i x_j>) for the exact Eq. 13 form."""

    cov = mij - mi * mj
    denom = 1.0 - 2.0 * (mi + mj - 2.0 * mij)
    g = cov / denom
    root = np.sqrt(np.clip(0.25 - g, NUMERICAL_ZERO, None))
    d2 = denom * denom
    common = 1.0 / (2.0 * root)
    gi = common * (-mj * denom + 2.0 * cov) / d2
    gj = common * (-mi * denom + 2.0 * cov) / d2
    gij = common * (denom - 4.0 * cov) / d2
    return gi, gj, gij


def spitz_pij_delta_se(
    mean_i: np.ndarray,
    mean_j: np.ndarray,
    mean_joint: np.ndarray,
    num_shots: int,
) -> np.ndarray:
    """Per-entry delta-method SE from the exact per-shot moment covariance."""

    mi = np.asarray(mean_i, dtype=np.float64)
    mj = np.asarray(mean_j, dtype=np.float64)
    mij = np.asarray(mean_joint, dtype=np.float64)
    gi, gj, gij = _pij_gradients(mi, mj, mij)
    var_i = mi * (1.0 - mi)
    var_j = mj * (1.0 - mj)
    var_ij = mij * (1.0 - mij)
    cov_i_j = mij - mi * mj
    cov_i_ij = mij * (1.0 - mi)
    cov_j_ij = mij * (1.0 - mj)
    variance = (
        gi * gi * var_i
        + gj * gj * var_j
        + gij * gij * var_ij
        + 2.0 * gi * gj * cov_i_j
        + 2.0 * gi * gij * cov_i_ij
        + 2.0 * gj * gij * cov_j_ij
    )
    return np.sqrt(np.clip(variance, 0.0, None) / float(num_shots))


__all__ = ["spitz_pij_delta_se", "spitz_pij_exact"]
