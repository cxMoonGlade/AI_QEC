from __future__ import annotations

"""D5 (ADR 0004): identifiability gating that predicts the validity curve.

The gating is NOT monolithically pre-D2. It splits:

**D5a -- DEM-layer, genuinely first, cheap.** The stochastic / Pauli "quadratic
variation" layer, computable from the known DEM parity map ``A`` alone:
  * ``anchor_features`` -- the Moran sparse-decoding condition: a fault is
    mechanism-identifiable iff >= 2 detectors fire for it alone. Faults without
    two anchors enter the alias quotient.
  * ``learnable_first_moment_dim`` -- the leading-order learnable-DOF ceiling
    (Bravyi-Haah-Hastings direction): from detector fire-rates the learnable
    fault-rate subspace is the image of ``A``, so its real rank bounds how many
    fault-rate combinations are separable from first-moment syndrome statistics
    (pairwise correlations add more; this is the conservative ceiling).

**D5b -- coherent Girsanov, co-built with D2 (PARTIAL here).** ``girsanov_split``
is a cheap exact decomposition of a channel's Pauli-transfer matrix into the
diagonal Pauli block (the "quadratic variation", second-order identifiable) and
the off-diagonal coherent + non-unital "drift" (invisible to second-order
statistics). ``has_coherent_drift`` is the *qualitative* gate: a necessary
condition for a moment-matched/DEM twin to fail. But the *quantitative
per-direction* prediction -- how much a given coherent drift moves ``B_LER`` and
at which probe richness it becomes observable -- cannot be computed from the
channel alone; it needs the r=2-4 coherent-probe forwards that D2 builds (the
coherent half has a circular dependency on D2). So ``predict_b_ler_by_direction``
is a stub until D2 lands; using the qualitative gate as if it were the
quantitative prediction would give false confidence exactly on the coherent slice
that is the target of B5.
"""

import torch

from qec_twin.decoder.stim_dem import extract_dem_data
from qec_twin.contexts.ladder import calibration_contexts
from qec_twin.knobs.reference import stim_rep_code_circuit
from qec_twin.forward.cptp_channel import pauli_transfer_matrix


# --------------------------------------------------------------------------- #
# D5a -- DEM-layer identifiability (Pauli / quadratic-variation faults)         #
# --------------------------------------------------------------------------- #
def rep_code_parity_map(distance: int, rounds: int, *, nominal_p: float = 0.05):
    """Extract the rep-code DEM parity map ``A`` (faults -> detectors+observable)."""
    circuit = stim_rep_code_circuit(distance, rounds, nominal_p, logical=0)
    return extract_dem_data(circuit, decompose_errors=False)


def anchor_features(parity_map) -> dict[str, object]:
    """Per-fault anchor-detector counts and the >= 2 identifiability flag (Moran)."""
    matrix = parity_map.raw_masks.to(torch.int64)  # (num_detectors+num_obs, num_faults)
    detector_rows = matrix[: parity_map.num_detectors]
    fault_per_detector = detector_rows.sum(dim=1)  # how many faults flip each detector
    num_faults = detector_rows.shape[1]
    counts = [
        int(((detector_rows[:, j] == 1) & (fault_per_detector == 1)).sum())
        for j in range(num_faults)
    ]
    return {
        "anchor_counts": counts,
        "identifiable": [c >= 2 for c in counts],
        "num_faults": num_faults,
        "num_identifiable": sum(c >= 2 for c in counts),
    }


def learnable_first_moment_dim(parity_map) -> dict[str, int]:
    """Real rank of the detector parity map = leading-order learnable-rate DOF."""
    detector_rows = parity_map.raw_masks[: parity_map.num_detectors].to(torch.float64)
    rank = int(torch.linalg.matrix_rank(detector_rows))
    num_faults = detector_rows.shape[1]
    return {"first_moment_rank": rank, "num_faults": num_faults, "aliased": num_faults - rank}


# --------------------------------------------------------------------------- #
# D5b -- channel-layer Girsanov split (PARTIAL: co-built with D2)               #
# --------------------------------------------------------------------------- #
def girsanov_split(kraus: torch.Tensor, *, tol: float = 1e-9) -> dict[str, object]:
    """Split a single-qubit channel into Pauli "quadratic variation" + coherent
    "drift" via its Pauli-transfer matrix.

    ``coherent_offdiag`` is the max off-diagonal of the 3x3 Pauli block (coherent
    rotation -- invisible to second-order syndrome statistics); ``non_unital`` is
    the ``I -> Pauli`` column (relaxation drift). A pure stochastic Pauli channel
    has both ~ 0 and is second-order identifiable. Cheap and exact; this is the
    decomposition D5b builds its quantitative prediction on top of, once D2's
    high-r forwards exist.
    """
    ptm = pauli_transfer_matrix(kraus)
    block = ptm[1:, 1:]
    diagonal = torch.diagonal(block)
    off_diagonal = block - torch.diag(diagonal)
    coherent = float(off_diagonal.abs().max())
    non_unital = float(ptm[1:, 0].abs().max())
    return {
        "pauli_diagonal": [float(d) for d in diagonal],
        "coherent_offdiag": coherent,
        "non_unital": non_unital,
        "drift": max(coherent, non_unital),
        "second_order_identifiable": coherent < tol and non_unital < tol,
    }


def has_coherent_drift(field, n_locations: int, *, tol: float = 1e-9) -> bool:
    """Qualitative D5b gate: does any location carry drift a second-order/DEM twin
    must miss?

    A *necessary* condition for a moment-matched twin's knob to fail -- NOT the
    quantitative prediction (how much, at which `r`). That is
    ``predict_b_ler_by_direction``, which is co-built with D2.
    """
    return any(
        girsanov_split(field(0, i), tol=tol)["drift"] > tol for i in range(int(n_locations))
    )


def predict_exotic_drop_level(
    teacher_field, distance: int, *, levels=(0, 1, 2, 3, 4), tol: float = 1e-9
) -> dict[str, object]:
    """D5b (co-built with D2): structurally PREDICT where the held-out coherent-
    exotic prediction error collapses, before running the expensive D2 curve.

    The prediction combines the Girsanov gate with the ladder structure: if the
    teacher carries coherent drift (off-diagonal PTM), a Z-basis fit Pauli-shadows
    it, so the phase-sensitive exotic stays mispredicted until the calibration set
    ``C_cal(k)`` first contains a phase-sensitive (``pre_rotation != 0``) probe --
    that ``k`` is the predicted drop level. A drift-free (pure Pauli) teacher needs
    no phase-sensitive probe, so the prediction is ``0`` (Z-basis already pins it).
    This is the pre-registered D4 hypothesis the D2 curve then confirms or falsifies.
    """
    if not has_coherent_drift(teacher_field, distance, tol=tol):
        return {
            "predicted_drop_level": 0,
            "reason": "no coherent drift; Z-basis calibration already pins the channel",
        }
    for k in levels:
        if any(c.pre_rotation != 0.0 for c in calibration_contexts(k, distance=distance)):
            return {
                "predicted_drop_level": k,
                "reason": (
                    "coherent drift is invisible to Z-basis; recovered only once a "
                    "phase-sensitive (pre_rotation) probe enters C_cal(k)"
                ),
            }
    return {
        "predicted_drop_level": None,
        "reason": "coherent drift but no phase-sensitive probe in the ladder",
    }
