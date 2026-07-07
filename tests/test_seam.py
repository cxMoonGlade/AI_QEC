"""The teacher output → decoder-input SEAM (``forward/scalable/seam.py``).

Executable spec for the teacher's output contract (ADR 0010; graduated from
``outputs/teacher_prereg/p7_seam.py``): the ``ShotSet`` packed buffer →
``(detection_events, obs_flips)`` adaptor and its first-round-raw + interior round-to-round
XOR fold, the matched-Pauli-DEM foil (leak ABSENT), and the ledger-(v) positive control.

The load-bearing test (pre-reg §1.5 ledger v) is the RAW-CIRCUIT-DETECTOR control: a planted
single fault must ROUND-TRIP through the pack/unpack + XOR fold to the hand-computed
detectors, and the foil DEM (built from the RAW d3 XZZX ``.stim`` geometry, not from a Pauli
reduction of the leakage channel — anti-circular, ledger invariant ii) must decode the
zero-syndrome shot to observable 0. A wrong endianness / round-order / XOR direction MUST
trip the planted-fault round-trip; the MSB-first teeth prove the LSB convention is
load-bearing.

The fold-only tests run with NO dataset / NO GPU (host-side I/O). The matched-DEM legs read
the shipped d3 ``d3_at_q6_7`` r01/r10 patch and skip if absent (stim/pymatching are the
frozen evaluator tooling). No teacher GPU model-compute happens here.
"""

from __future__ import annotations

import numpy as np

from qec_twin.forward.scalable.seam import (
    assert_leak_absent_from_dem,
    build_matched_pauli_dem,
    g2_positive_control,
    inspect_raw_detectors,
    teacher_shots_to_events,
)
from qec_twin.forward.scalable.sv_sampler import SvSampler

# Skip gate from tests/conftest.py (Wave 1, contract C1). DECLARED strictening (C1 risk
# note): the old local probe checked 3 files (no r10 metadata); the canonical probe
# requires ALL FOUR -- a partial patch now skips the dataset legs.
from conftest import requires_data


# =========================================================================== #
# G2 fold — the planted-fault round-trip (NO dataset / NO GPU; host-side I/O)  #
# =========================================================================== #
def test_g2_planted_fault_roundtrips_through_xor_fold():
    """A KNOWN single-round-flip fault round-trips: pack → unpack → first-round-raw +
    interior round-to-round XOR fold → the hand-computed detectors. Distinct from the raw
    syndrome: a single stab ON at one interior round fires TWO detectors (the on/off edge
    pair). This is the seam's core contract and is fully self-contained (no dataset)."""
    n_stab, R = 8, 3
    rng = np.random.default_rng(11)
    N = 32
    # random background so the test is not trivially all-zero, plus a PLANTED fault in shot 0.
    raw = rng.integers(0, 2, size=(N, R, n_stab)).astype(np.uint8)
    raw[0] = 0
    raw[0, 1, 5] = 1  # stab 5 ON at round 1 only → fires detectors (r1,s5) and (r2,s5)
    syn_flat = raw.reshape(N, R * n_stab)
    flips = rng.integers(0, 2, size=N).astype(np.uint8)
    flips[0] = 1  # an arbitrary known flip label on the planted shot

    packed = SvSampler.pack_shots(syn_flat, flips)
    det, obs = teacher_shots_to_events(packed, n_stab, R)

    # obs_flips passes through verbatim (the trailing-byte label).
    assert obs.dtype == np.uint8 and obs.shape == (N,)
    assert np.array_equal(obs, flips), "obs_flips must equal the injected flip labels"

    # the planted shot's detectors: first round raw (all 0), then the on/off XOR edge pair.
    det0 = det[0].reshape(R, n_stab)
    expected0 = np.zeros((R, n_stab), dtype=np.uint8)
    expected0[1, 5] = 1  # round 1: s[1,5]=1 XOR s[0,5]=0
    expected0[2, 5] = 1  # round 2: s[2,5]=0 XOR s[1,5]=1
    assert np.array_equal(det0, expected0), (
        f"planted-fault detectors mismatch.\n got {det0}\n exp {expected0}")

    # the fold reproduced on the FULL batch (the convention applied to every shot).
    s = syn_flat.reshape(N, R, n_stab)
    ref = np.empty_like(s)
    ref[:, 0, :] = s[:, 0, :]
    ref[:, 1:, :] = s[:, 1:, :] ^ s[:, :-1, :]
    assert np.array_equal(det, ref.reshape(N, R * n_stab)), "full-batch XOR fold mismatch"


def test_g2_msb_first_unpack_scrambles_lsb_is_load_bearing():
    """Positive-control teeth: decoding the kernel buffer MSB-first (the wrong endianness)
    SCRAMBLES the raw syndromes — so the LSB-first convention is genuinely load-bearing and
    the round-trip check is not inert (a wrong bitorder would be caught)."""
    n_stab, R = 8, 3
    rng = np.random.default_rng(3)
    N = 16
    syn_flat = rng.integers(0, 2, size=(N, R * n_stab)).astype(np.uint8)
    flips = rng.integers(0, 2, size=N).astype(np.uint8)
    packed = SvSampler.pack_shots(syn_flat, flips)

    syn_lsb, _ = SvSampler.unpack_shots(packed, n_stab, R)
    assert np.array_equal(syn_lsb, syn_flat), "LSB-first unpack must round-trip"

    sb = (R * n_stab + 7) // 8
    syn_msb = np.unpackbits(packed[:, :sb], axis=1, bitorder="big")[:, :R * n_stab]
    assert not np.array_equal(syn_msb, syn_flat), (
        "MSB-first decode also matched — the bitorder check is inert (LSB not load-bearing)")


# =========================================================================== #
# Ledger (v) — the full deterministic positive control (RAW-CIRCUIT DEM)       #
# =========================================================================== #
@requires_data
def test_g2_positive_control_planted_fault_and_matched_dem():
    """Ledger (v) the raw-circuit-detector control: the deterministic positive control runs
    round-trip + XOR convention + MSB teeth AND builds the matched-Pauli-DEM foil from the RAW
    d3 XZZX ``.stim`` geometry, then decodes the zero-syndrome shot to observable 0. All legs
    MUST pass; a broken XOR/order trips round-trip/convention, a broken DEM/decoder trips the
    decode."""
    ctrl = g2_positive_control()
    assert ctrl["roundtrip_ok"], "pack/unpack round-trip of raw syndromes FAILED"
    assert ctrl["conv_ok"], "detector XOR convention MISMATCH on the known single-flip shot"
    assert ctrl["msb_scrambles"], "MSB-first decode matched — the LSB check is inert"
    assert ctrl["zero_syndrome_obs0"], "zero-syndrome decode returned a nonzero observable"
    assert ctrl["matched_dem_obs"] == 1, "matched DEM must carry exactly one observable"
    assert ctrl["matched_dem_dets"] == 8 * 3, "matched DEM detectors must be R*n_stab = 24"
    assert 0.0 < ctrl["matched_p_depol"] < 0.5


@requires_data
def test_matched_dem_is_over_teacher_emitted_space_and_leak_absent():
    """G1: the foil DEM is built over the teacher's EMITTED detector space (``R*n_stab``
    ancilla-syndrome detectors, one logical observable) and carries NO leak DOF (pure Pauli —
    ledger invariant ii). The detector count tracks R."""
    for R in (1, 3, 5):
        dem, info, _circ = build_matched_pauli_dem(0.07, 0.09, R)
        assert dem.num_detectors == R * info["n_stab"], (
            f"R={R}: DEM detectors {dem.num_detectors} != R*n_stab {R * info['n_stab']}")
        assert dem.num_observables == 1, f"R={R}: DEM must have a single logical observable"
        ev = assert_leak_absent_from_dem(dem)
        assert ev["pure_pauli"], f"R={R}: DEM is not the pure-Pauli foil (leak DOF smuggled?)"
        assert ev["num_detectors"] == R * info["n_stab"]


@requires_data
def test_shipped_detectors_use_terminal_data_so_foil_is_over_emitted_space():
    """The load-bearing design fact (invariant ii), read from the RAW circuit: the shipped d3
    XZZX DEM's detectors ALL reference the TERMINAL per-data-qubit readout (8 at r01, 80 at
    r10) — so they CANNOT be reconstructed from the teacher's ancilla-only emission, which is
    WHY the foil DEM is matched to the teacher's emitted ancilla-syndrome space, not the
    shipped DEM."""
    res = inspect_raw_detectors()
    r01, r10 = res["r01"], res["r10"]
    # every shipped detector folds in terminal data; none is pure-ancilla.
    assert r01["detectors_using_terminal_data"] == r01["num_detectors"] > 0, res
    assert r01["pure_ancilla_detectors"] == 0, res
    assert r10["detectors_using_terminal_data"] == r10["num_detectors"] > 0, res
    assert r10["pure_ancilla_detectors"] == 0, res
