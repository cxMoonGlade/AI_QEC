"""Canonical skip probes and constants for the current test suite.

The binding contract is ``docs/SIMULATOR.md``. This module is the single home for:

  * ``_HAS_CUDA`` / ``requires_cuda`` -- the GPU probe. House rule: GPU-only model
    compute is a hard skip without CUDA, never a CPU fallback.
  * ``_HAS_DATA`` / ``requires_data`` -- the strict d3 dataset probe: all four
    shipped ``d3_at_q6_7`` files must be present (r01 circuit+metadata AND r10
    circuit+metadata). A partial dataset is unavailable by definition.
  * the canonical device/dtype constants ``DEVICE`` / ``CDTYPE`` / ``RDTYPE`` / ``PHYS``.

Test-only probe hook (not a user feature): the env var ``ECS_D3_MASK`` falsifies the
``_HAS_DATA`` predicate itself. It holds a comma list of logical names in
``{r01_circ, r01_meta, r10_circ, r10_meta}``; masked names are treated as ABSENT by
``_HAS_DATA``. An UNKNOWN name raises ``ValueError`` loudly -- a typo silently masking
nothing would make the probe vacuous (DEVIOUS-TEST STANDARD). Exercised by
``tests/_support/test_support_selftest.py``.

Torch is imported guarded so collection works on a box without torch (the GPU-gated
tests then skip via ``requires_cuda``).
"""

from __future__ import annotations

import os

import pytest

try:
    import torch
except Exception:  # noqa: BLE001 -- collection must survive a torch-less box
    torch = None

_HAS_CUDA = bool(torch is not None and torch.cuda.is_available())

# --------------------------------------------------------------------------- #
# Canonical constants. Model compute is GPU-only (house rule);                 #
# CDTYPE/RDTYPE are None on a torch-less box (collection-safe -- any test that  #
# uses them is requires_cuda-gated and skips there).                           #
# --------------------------------------------------------------------------- #
DEVICE = "cuda"
CDTYPE = torch.complex128 if torch is not None else None
RDTYPE = torch.float64 if torch is not None else None
PHYS = 3  # qutrit physical dimension

# --------------------------------------------------------------------------- #
# The strict d3 dataset probe (all four files) + its test-only mask hook.      #
# --------------------------------------------------------------------------- #
_D3_MASK_ENV = "ECS_D3_MASK"
_D3_DATA_ENV = "ECS_D3_DATA_ROOT"
_D3_LOGICAL_NAMES = ("r01_circ", "r01_meta", "r10_circ", "r10_meta")


def _d3_paths() -> dict:
    """The four shipped d3_at_q6_7 files keyed by logical name ({} if the parser is
    unimportable -- then the data probe is simply False, never a collection crash)."""
    try:
        from error_coupling_simulator.frontend import xzzx_parser as xp
    except Exception:  # noqa: BLE001
        return {}
    configured = os.environ.get(_D3_DATA_ENV)
    if configured is not None:
        configured = configured.strip()
        if not configured:
            raise ValueError(
                f"env var {_D3_DATA_ENV} is SET but empty/whitespace; unset it "
                "to use the portable default dataset root")
    r01_circ, r01_meta = xp.default_r01_paths(dataset_root=configured)
    r10_circ, r10_meta = xp.default_r10_paths(dataset_root=configured)
    return {"r01_circ": r01_circ, "r01_meta": r01_meta,
            "r10_circ": r10_circ, "r10_meta": r10_meta}


def _parse_d3_mask(mask) -> frozenset:
    """Parse + VALIDATE a mask (comma string or iterable of logical names; None reads
    the ``ECS_D3_MASK`` env var). Unknown names raise ValueError -- fail loud."""
    if mask is None:
        mask = os.environ.get(_D3_MASK_ENV, "")
    if isinstance(mask, str):
        names = tuple(tok.strip() for tok in mask.split(",") if tok.strip())
    else:
        names = tuple(str(tok).strip() for tok in mask if str(tok).strip())
    unknown = sorted(set(names) - set(_D3_LOGICAL_NAMES))
    if unknown:
        raise ValueError(
            f"{_D3_MASK_ENV}: unknown logical name(s) {unknown}; valid names are "
            f"{list(_D3_LOGICAL_NAMES)}. (A typo silently masking nothing would make "
            f"the mask probe vacuous -- fail loud.)")
    return frozenset(names)


def _has_data(mask=None) -> bool:
    """The strict d3 data predicate: True iff ALL FOUR shipped files are present AND
    unmasked. ``mask`` is the TEST-ONLY probe hook (see module docstring); the normal
    suite runs with ``mask=None`` and no env var set. Callable directly (meta-tests
    exercise it without reimporting this module)."""
    masked = _parse_d3_mask(mask)
    paths = _d3_paths()
    if not paths:
        return False
    return all(name not in masked and paths[name].is_file()
               for name in _D3_LOGICAL_NAMES)


_HAS_DATA = _has_data()

# --------------------------------------------------------------------------- #
# Canonical markers. These reason strings are the current shared definitions. #
# --------------------------------------------------------------------------- #
requires_cuda = pytest.mark.skipif(
    not _HAS_CUDA,
    reason="GPU-only model compute (house rule: hard skip, never CPU fallback)")
requires_data = pytest.mark.skipif(
    not _HAS_DATA,
    reason="shipped d3_at_q6_7 r01/r10 patch absent (all four files required)")
