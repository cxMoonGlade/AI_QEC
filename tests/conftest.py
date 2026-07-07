"""Canonical skip-gate probes + constants for the test suite (Wave 1, contract row C1).

Binding contract: ``docs/twin_validation/api_hardening_ownership_design.md`` (row C1, the
NAMING STANDARD, and review dispositions AM-2/AM-4). This module is the ONE home for:

  * ``_HAS_CUDA`` / ``requires_cuda`` -- the GPU probe. House rule: GPU-only model
    compute is a HARD SKIP without CUDA, never a CPU fallback (the memlean
    cuda-else-cpu fallback was a divergence eliminated on migration -- a DECLARED
    behavior change, contract AM-2).
  * ``_HAS_DATA`` / ``requires_data`` -- the ONE strict d3 dataset probe: ALL FOUR
    shipped ``d3_at_q6_7`` files must be present (r01 circuit+metadata AND r10
    circuit+metadata -- the strict p2 variant). Files that previously probed only
    3 of the 4 (soft_readout, seam) or r01-only (qutrit_dm_exact) are DELIBERATELY
    strictened by this migration: a partial patch now skips them (correct behavior,
    C1 risk note).
  * the canonical device/dtype constants ``DEVICE`` / ``CDTYPE`` / ``RDTYPE`` / ``PHYS``.

TEST-ONLY probe hook (NOT a user feature): the env var ``QEC_TWIN_D3_MASK`` is the
Rule-II falsifying probe for the ``_HAS_DATA`` predicate itself (contract AM-2 --
"the predicate is SHOWN to trip"). It holds a comma list of logical names in
``{r01_circ, r01_meta, r10_circ, r10_meta}``; masked names are treated as ABSENT by
``_HAS_DATA``. An UNKNOWN name raises ``ValueError`` loudly -- a typo silently masking
nothing would make the probe vacuous (DEVIOUS-TEST STANDARD). Exercised by
``outputs/twin_validation/wave1_skipgate_probe.py`` and
``tests/_support/test_support_selftest.py``.

The separate, documented ``QEC_TWIN_HW_DATA`` hardware-test convention
(``test_hardware_m*``) is deliberately NOT touched here (C1 risk note).

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
# Canonical constants (contract C1). Model compute is GPU-only (house rule);   #
# CDTYPE/RDTYPE are None on a torch-less box (collection-safe -- any test that  #
# uses them is requires_cuda-gated and skips there).                           #
# --------------------------------------------------------------------------- #
DEVICE = "cuda"
CDTYPE = torch.complex128 if torch is not None else None
RDTYPE = torch.float64 if torch is not None else None
PHYS = 3  # qutrit physical dimension

# --------------------------------------------------------------------------- #
# The ONE strict d3 dataset probe (all four files) + the AM-2 mask hook.       #
# --------------------------------------------------------------------------- #
_D3_MASK_ENV = "QEC_TWIN_D3_MASK"
_D3_LOGICAL_NAMES = ("r01_circ", "r01_meta", "r10_circ", "r10_meta")


def _d3_paths() -> dict:
    """The four shipped d3_at_q6_7 files keyed by logical name ({} if the parser is
    unimportable -- then the data probe is simply False, never a collection crash)."""
    try:
        from qec_twin.forward.exact import xzzx_parser as xp
    except Exception:  # noqa: BLE001
        return {}
    r01_circ, r01_meta = xp.default_r01_paths()
    r10_circ, r10_meta = xp.default_r10_paths()
    return {"r01_circ": r01_circ, "r01_meta": r01_meta,
            "r10_circ": r10_circ, "r10_meta": r10_meta}


def _parse_d3_mask(mask) -> frozenset:
    """Parse + VALIDATE a mask (comma string or iterable of logical names; None reads
    the ``QEC_TWIN_D3_MASK`` env var). Unknown names raise ValueError -- fail loud."""
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
            f"the AM-2 probe vacuous -- fail loud.)")
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
# Canonical markers (contract C1: these reason strings ARE the canon; a local  #
# variant in a test file is a migration target, the canonical wins).           #
# --------------------------------------------------------------------------- #
requires_cuda = pytest.mark.skipif(
    not _HAS_CUDA,
    reason="GPU-only model compute (house rule: hard skip, never CPU fallback)")
requires_data = pytest.mark.skipif(
    not _HAS_DATA,
    reason="shipped d3_at_q6_7 r01/r10 patch absent (all four files required)")
