"""Wave-2 gates for the A2/A3 API extensions (ShotSet records + mps_forward seams).

Binding contract: ``docs/twin_validation/api_hardening_ownership_design.md`` rows A2/A3,
the NAMING STANDARD (N-1..N-5 rename table), the DEVIOUS-TEST STANDARD (KILLER
requirement + K-catalog), and review dispositions AM-3 / AM-5 / AM-8.

Gate -> test map (K-classes each test defends are declared in its docstring):

  AM-3  : test_am3_to_det_obs_matches_hand_roll        (K-2, K-5, K-8)
  A2    : test_a2_packed_and_syndrome_prefix_bytes      (K-1, K-2, K-5)
  A2    : test_a2_syndrome_prefix_midbyte_repack        (K-2, K-5)
  AM-5  : test_am5_leak_sample_tiebreak_registry        (K-2, K-3)
  A3    : test_a3_attach_layout_pure_addition           (K-1, K-5, K-6, K-9)
  A3    : test_a3_mps_from_statevector_roundtrip        (K-1, K-5, K-8)

The A2/A3 src diff LANDED (ratified decision 6). The former ``requires_a2_api`` /
``requires_a3_api`` hasattr skip-probes were REMOVED with it: a future deletion of a
landed API must FAIL these gates (AttributeError/TypeError), never skip them.

API SHAPES (the LANDED signatures, verified against
``src/qec_twin/forward/scalable/{sv_sampler,mps_forward}.py``):
  * ``ShotSet.to_det_obs()`` -> ``{"det": (N, R*n_stab) uint8, "obs": (N,)}``,
    round-major det layout (round outer, then stab), n_stab/R read from the header.
  * ``ShotSet.packed_bytes()`` -> the full packed buffer as ``bytes``
    (== ``np.ascontiguousarray(ss.shots).tobytes()``).
  * ``ShotSet.syndrome_prefix_bytes(n_rounds)`` -> per-shot leading
    ``n_rounds*n_stab`` syndrome bits repacked LSB-first, shot-major concatenated,
    NEVER including the trailing flip byte. Byte-aligned round boundary = raw byte
    slice; MID-BYTE boundary = unpack + truncate + repack (unreachable on the d3
    n_stab=8 geometry -- exercised by the synthetic n_stab=3 gate below).
  * ``MpsLeakageForward.attach_layout(order, logical_support)`` -- ``order`` is the
    SITE->ENGINE order TUPLE (``order[k]`` = engine position carried at MPS site
    ``k``); ``_eng_to_mps`` is primed with its INVERSE (engine position -> MPS site)
    and ``_log_eng_support`` with the engine-position logical support. A ``Mapping``
    is REJECTED with ``TypeError`` (dict iteration yields keys only -- the silent
    insertion-order reinterpretation hazard).
  * module-level ``mps_forward.mps_from_statevector(psi, order, device)`` -- THREE
    required positionals; site-0-MSB ``from_dense(dims=[3]*n)`` convention; the dense
    engine-basis vector is transposed so MPS site ``k`` carries engine axis
    ``order[k]`` BEFORE factorization.
  * ``MpsLeakageForward._leak_sample(...)`` RETURNS the selected branch index (int).

GPU-only model compute (house rule); the sampling tests additionally need the shipped
d3_at_q6_7 r01/r10 patch.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import torch

qtn = pytest.importorskip("quimb.tensor")

from qec_twin.forward.exact import xzzx_parser as xp
from qec_twin.forward.scalable import mps_forward as mf
from qec_twin.forward.scalable.mps_forward import MpsLeakageForward
from qec_twin.forward.scalable.sv_sampler import RunSpec, ShotSet, SvSampler

# Wave-1 canon: markers/constants from tests/conftest.py (contract C1), guard helpers
# from tests/_support/fixtures.py (contract C2).
from conftest import CDTYPE, DEVICE, PHYS, requires_cuda, requires_data
from _support.fixtures import assert_control_trips, require_precondition

# --------------------------------------------------------------------------- #
# Env isolation (review finding: env-honoring facade vs env-blind reference).  #
# --------------------------------------------------------------------------- #
@pytest.fixture(autouse=True)
def _no_d3_env_override(monkeypatch):
    """Every gate here builds DEFAULT-root artifacts and compares them against
    env-blind hand rituals; a legitimately-set ``QEC_TWIN_D3_DATA`` (honored by any
    env-honoring facade component that enters the chain) must never make a correct
    implementation fail. Deleted per-test, restored by monkeypatch teardown."""
    monkeypatch.delenv("QEC_TWIN_D3_DATA", raising=False)


# --------------------------------------------------------------------------- #
# Thin call adapters (byte-normalization only; the APIs themselves LANDED).    #
# --------------------------------------------------------------------------- #
def _to_det_obs(ss) -> dict:
    return ss.to_det_obs()


def _packed_bytes(ss) -> bytes:
    return bytes(ss.packed_bytes())


def _prefix_bytes(ss, n_rounds: int) -> bytes:
    return bytes(ss.syndrome_prefix_bytes(n_rounds=int(n_rounds)))


# --------------------------------------------------------------------------- #
# The p2 cell ritual, copied from tests/test_p2_mps_per_round_leak.py           #
# (_sched_and_spec/_spec_at/_base_leak/_packed -- the registered leak-active    #
# point of the sweep; migrates onto the A1 facade in Wave 7).                   #
# --------------------------------------------------------------------------- #
_R01_CIRC, _R01_META = xp.default_r01_paths()
_R10_CIRC, _R10_META = xp.default_r10_paths()

THETA, G_SEEP, G_HEAT, B_BIAS, ARM = 0.30, 0.09, 0.0, 0.9, "A"
# the GROSSLY different second cell of p2's round-index discriminator (the two tables
# must drive different branch selections under the same u stream).
THETA_HI, G_SEEP_HI = 1.2, 0.5


def _spec_at(theta: float, g_seep: float, R: int, N: int, seed: int = 11) -> RunSpec:
    return RunSpec(circuit_path=_R01_CIRC, metadata_path=_R01_META, m=0, theta=theta,
                   g_seep=g_seep, g_heat=G_HEAT, arm=ARM, b=B_BIAS,
                   readout_conv="biased_b", N=N, base_seed=seed, R=R, dtype="c128")


def _sched_and_spec(R: int, N: int, seed: int = 11):
    sched = xp.parse_xzzx_circuit(_R01_CIRC, _R01_META, verify=True)
    sched = sched.with_within_cycle_streams(
        xp.parse_within_cycle_streams(_R10_CIRC, _R10_META))
    return sched, _spec_at(THETA, G_SEEP, R, N, seed=seed)


def _base_leak(spec: RunSpec) -> torch.Tensor:
    """The spec-built exp(L/4) slice via the SAME builder the static arm uses (CPTP +
    composition asserted inside -- the C1 source of truth, not a re-derivation)."""
    leak, _ = SvSampler(device=DEVICE).build_within_cycle_leak(spec)
    return leak


def _hand_packed(ss) -> bytes:
    return bytes(np.ascontiguousarray(np.asarray(ss.shots)).tobytes())


# =========================================================================== #
# AM-3: one-time equivalence gate for ShotSet.to_det_obs()                     #
# =========================================================================== #
@requires_cuda
@requires_data
def test_am3_to_det_obs_matches_hand_roll():
    """AM-3 one-time equivalence gate (contract: BEFORE any consumer deletes its
    hand-roll). Defends: K-2 (misindexed unpack/reshape), K-8 (round-major layout
    convention drift), K-5 (self-comparison vacuity -- the hand-roll below is an
    INLINE ``np.unpackbits`` transcription of the header's ``syndrome_layout`` text,
    sharing NO ``SvSampler`` unpack code, and stays IN THIS TEST by contract).

    KILLER (K-8): a deliberately TRANSPOSED reshape (stab-major instead of
    round-major) is DEMONSTRATED to trip the equality — on a SYNTHETIC buffer whose
    bit pattern is transpose-ASYMMETRIC BY CONSTRUCTION (first gate run 2026-07-07:
    the cold real cell drew an all-zero — transpose-symmetric — record at N=3 and the
    scan precondition fired; a synthetic pattern is deterministic, no scan, no
    vacuity risk; the REAL record below still carries the AM-3 equivalence gate).
    """
    R, N = 2, 3  # the p2 cell (small seeded MPS sample)
    sched, spec = _sched_and_spec(R=R, N=N, seed=11)
    fwd = MpsLeakageForward(device=DEVICE)
    ss, _ = fwd.sample(spec, sched=sched)
    assert ss.shots is not None
    n_stab = int(ss.header["n_stab"])
    # ---- the HAND-ROLLED independent transcription, straight off the header's
    # ---- pinned layout text (cited verbatim; NO SvSampler unpack code):
    # ----   "shot_major: shot_id outer, then round, then stab (round-major,
    # ----    LSB-first packbits); logical_flip in the trailing byte (value 0/1)"
    layout = str(ss.header["syndrome_layout"])
    assert "LSB-first" in layout and "trailing byte" in layout, \
        f"header syndrome_layout text drifted from the pinned convention: {layout!r}"
    packed = np.asarray(ss.shots)
    syn_nbytes = (R * n_stab + 7) // 8
    bits = np.unpackbits(packed[:, :syn_nbytes], axis=1,
                         bitorder="little")[:, :R * n_stab]
    det_hand = bits.reshape(N, R * n_stab).astype(np.uint8)  # round outer, stab inner
    obs_hand = packed[:, syn_nbytes].astype(np.uint8)        # trailing byte = raw 0/1

    out = _to_det_obs(ss)
    assert set(out.keys()) >= {"det", "obs"}, \
        f"to_det_obs payload keys drifted (registered {{'det','obs'}}): {sorted(out)}"
    det_api = np.asarray(out["det"])
    obs_api = np.asarray(out["obs"])
    assert det_api.dtype == np.uint8, f"det dtype {det_api.dtype} != uint8 (contract A2)"
    assert det_api.shape == (N, R * n_stab), \
        f"det shape {det_api.shape} != (N, R*n_stab)=({N}, {R * n_stab})"
    assert obs_api.shape == (N,), f"obs shape {obs_api.shape} != ({N},)"
    assert np.array_equal(det_api, det_hand), \
        "to_det_obs det != inline header-layout unpackbits transcription (AM-3 " \
        "equivalence gate)"
    assert np.array_equal(obs_api, obs_hand), \
        "to_det_obs obs != hand-rolled logical flips (AM-3 equivalence gate)"

    # KILLER (K-8) on a SYNTHETIC transpose-ASYMMETRIC buffer (deterministic; the
    # real cold-cell record can legitimately be all-zero = transpose-symmetric).
    # Pattern: shot 0 round 0 = e_0, round 1 = e_1 -> the (R, n_stab) matrix is not
    # symmetric under round<->stab transpose (n_stab=2 slice suffices; use R=n_stab=2
    # so the transpose is shape-preserving and the killer is a pure layout probe).
    syn_k = np.zeros((2, 4), dtype=np.uint8)   # N=2 shots, R=2, n_stab=2
    # NOTE the first attempt used [1,0,0,1]/[0,1,1,0] — the identity and swap
    # matrices, both transpose-SYMMETRIC; the BY-CONSTRUCTION assert below caught it
    # (2026-07-07). A hot round-0 / cold round-1 pattern is genuinely asymmetric:
    syn_k[0, :] = [1, 1, 0, 0]                 # rows (rounds): [1,1] / [0,0]
    syn_k[1, :] = [0, 0, 1, 1]                 # rows (rounds): [0,0] / [1,1]
    packed_k = SvSampler.pack_shots(syn_k, np.array([0, 1], dtype=np.uint8))
    ss_k = ShotSet(header={"n_stab": 2, "R": 2}, path=None, header_path=None,
                   n_shots=2, syndrome_bits_per_shot=4, shots=packed_k)
    det_k = np.asarray(_to_det_obs(ss_k)["det"])
    assert np.array_equal(det_k, syn_k), "synthetic round-major payload mismatch"
    det_k_transposed = (syn_k.reshape(2, 2, 2).transpose(0, 2, 1)
                        .reshape(2, 4).astype(np.uint8))
    assert not np.array_equal(det_k_transposed, syn_k), \
        "synthetic pattern must be transpose-asymmetric BY CONSTRUCTION"

    def _det_equality_check(candidate, _gate_tol):
        assert np.array_equal(np.asarray(candidate), det_k), \
            "candidate det layout != to_det_obs det"
    assert_control_trips(_det_equality_check, det_k_transposed, 0.0)


# =========================================================================== #
# A2: packed_bytes() / syndrome_prefix_bytes()                                 #
# =========================================================================== #
@requires_cuda
@requires_data
def test_a2_packed_and_syndrome_prefix_bytes():
    """A2 byte-surface gate. Defends: K-1 (an inert per-round seam is visible through
    the NEW API itself -- the varied-run killer), K-2 (syn-bytes prefix arithmetic /
    round misindex; the round-0 prefix logic mirrors test_p2_mps_per_round_leak.py's
    round-index discriminator), K-5 (non-vacuity controls on every byte equality).

    KILLER (K-1/K-2 on the new API): the n_rounds=1 prefix of the [lo,hi] varied run
    must be EQUAL to the [lo,lo] run's (round 0 consumes the same table + u prefix --
    the EXACT-identity leg) while the FULL packed_bytes DIFFER (round 1's table must
    matter). A constant-index seam breaks the second; a reversed/shifted round index
    breaks the first.
    """
    R, N = 2, 3
    sched, spec = _sched_and_spec(R=R, N=N)
    fwd = MpsLeakageForward(device=DEVICE)
    leak_lo = _base_leak(spec)
    leak_hi = _base_leak(_spec_at(THETA_HI, G_SEEP_HI, R, N))
    require_precondition(leak_hi.shape == leak_lo.shape,
                         "retained Choi rank differs between the two cells",
                         remedy="re-pick the discriminator cell")

    ss_ll, _ = fwd.sample(spec, sched=sched, leak_slices=[leak_lo, leak_lo])
    ss_lh, _ = fwd.sample(spec, sched=sched, leak_slices=[leak_lo, leak_hi])
    n_stab = int(ss_ll.header["n_stab"])
    pb1 = (n_stab * 1 + 7) // 8
    pbR = (n_stab * R + 7) // 8

    # packed_bytes == the raw contiguous buffer (hand transcription of p2's _packed).
    assert _packed_bytes(ss_ll) == _hand_packed(ss_ll), \
        "packed_bytes != contiguous ss.shots buffer"
    # prefix(1 round) == the hand-extracted round-0 block (leading packed-syn bytes
    # per shot; round-major layout: bits [0, n_stab) are round 0).
    hand_round0 = bytes(np.ascontiguousarray(np.asarray(ss_ll.shots)[:, :pb1]).tobytes())
    got_round0 = _prefix_bytes(ss_ll, 1)
    assert len(got_round0) == N * pb1 > 0, \
        f"prefix(1) length {len(got_round0)} != N*ceil(n_stab/8)={N * pb1}"
    assert got_round0 == hand_round0, \
        "syndrome_prefix_bytes(n_rounds=1) != hand-extracted round-0 block (K-2)"
    # prefix(R rounds) == ALL syndrome bytes, and must EXCLUDE the trailing flip byte.
    hand_syn_all = bytes(np.ascontiguousarray(np.asarray(ss_ll.shots)[:, :pbR]).tobytes())
    got_syn_all = _prefix_bytes(ss_ll, R)
    assert got_syn_all == hand_syn_all, "prefix(R) != full packed-syndrome block (K-2)"
    assert len(got_syn_all) == N * pbR < len(_packed_bytes(ss_ll)), \
        "prefix(R) must exclude the trailing logical-flip byte (K-2 boundary)"

    # ---- the KILLER pair on the varied run (K-1 inert seam / K-2 misindex) ----
    assert _prefix_bytes(ss_lh, 1) == _prefix_bytes(ss_ll, 1), \
        "round-0 prefix of [lo,hi] != [lo,lo]: round 0 is NOT consuming leak_slices[0] " \
        "(reversed/shifted round index visible through the new API)"
    assert _packed_bytes(ss_lh) != _packed_bytes(ss_ll), \
        "[lo,hi] packed_bytes == [lo,lo]: round 1 ignores its table (inert seam, K-1)"
    assert _prefix_bytes(ss_lh, R) != _prefix_bytes(ss_ll, R), \
        "[lo,hi] full syndrome block == [lo,lo]: round-1 difference is flip-only " \
        "(re-seed if this ever trips at these grossly different cells)"

    # K-5 non-vacuity control: a corrupted prefix DEMONSTRABLY trips the equality.
    corrupted = bytearray(hand_round0)
    corrupted[0] ^= 0xFF

    def _prefix_equality_check(candidate, _gate_tol):
        assert bytes(candidate) == _prefix_bytes(ss_ll, 1), "candidate prefix mismatch"
    assert_control_trips(_prefix_equality_check, bytes(corrupted), 0.0)


# =========================================================================== #
# A2: syndrome_prefix_bytes mid-byte branch (synthetic n_stab=3 -- CPU-only)   #
# =========================================================================== #
def test_a2_syndrome_prefix_midbyte_repack():
    """A2 mid-byte-branch gate (CPU-only, synthetic buffer -- no GPU, no dataset).

    The shipped d3 geometry has n_stab=8, so every round boundary is byte-aligned and
    the unpack+truncate+repack branch of ``syndrome_prefix_bytes`` is UNREACHABLE
    through the d3-driven gates above; this gate reaches it with a synthetic
    ``n_stab=3, R=3, N=4`` buffer packed by ``SvSampler.pack_shots`` and a
    header-shaped ``ShotSet`` carrying exactly the fields the accessors read
    (``header["n_stab"]``/``header["R"]`` + ``shots``). Defends: K-2 (mid-byte
    boundary arithmetic), K-5 (the reference below is an inline unpackbits/truncate/
    packbits transcription sharing NO SvSampler unpack code).

    KILLER (K-2): the devious raw-byte-slice implementation
    (``packed[:, :ceil(n_rounds*n_stab/8)]``) leaks round-1/round-2 bits into the pad
    bits of the boundary byte; it is DEMONSTRATED to fail the comparison.
    """
    n_stab, R, N = 3, 3, 4
    # hand-chosen bits: round-0 blocks vary per shot; bit positions 3..7 of the first
    # packed byte (rounds 1-2) are nonzero, so a raw byte slice CANNOT match a
    # zero-padded 3-bit repack. Shot 3 is the sharpest discriminator: round 0 is
    # all-zero (correct prefix byte 0x00) while its pad region carries leaked bits.
    syndromes = np.array([
        [1, 0, 1, 1, 1, 0, 0, 1, 1],
        [0, 1, 0, 0, 0, 1, 1, 0, 0],
        [1, 1, 1, 0, 0, 0, 1, 1, 0],
        [0, 0, 0, 1, 0, 1, 0, 1, 1],
    ], dtype=np.uint8)
    flips = np.array([1, 0, 1, 0], dtype=np.uint8)
    packed = SvSampler.pack_shots(syndromes, flips)
    ss = ShotSet(header={"n_stab": n_stab, "R": R}, path=None, header_path=None,
                 n_shots=N, syndrome_bits_per_shot=n_stab * R, shots=packed)

    # ---- the HAND-WRITTEN inline transcription (unpack LSB-first + truncate at the
    # ---- round boundary + repack LSB-first) -- NOT SvSampler.unpack_shots.
    def _hand_prefix(n_rounds: int) -> bytes:
        syn_nbytes = (n_stab * R + 7) // 8
        bits = np.unpackbits(packed[:, :syn_nbytes], axis=1,
                             bitorder="little")[:, :n_rounds * n_stab]
        return np.packbits(bits, axis=1, bitorder="little").tobytes()

    for n_rounds in (1, 2, 3):
        require_precondition(
            (n_rounds * n_stab) % 8 != 0,
            f"n_rounds={n_rounds} lands on a byte-aligned boundary (the mid-byte "
            f"branch would not be exercised)", remedy="re-pick n_stab/R")
        assert bytes(ss.syndrome_prefix_bytes(n_rounds)) == _hand_prefix(n_rounds), \
            f"syndrome_prefix_bytes({n_rounds}) != inline unpack/truncate/repack " \
            f"transcription (mid-byte branch, K-2)"

    # ---- KILLER: the raw-byte-slice transcription must FAIL at n_rounds=1 (3 bits).
    raw_slice = np.ascontiguousarray(packed[:, :(1 * n_stab + 7) // 8]).tobytes()
    require_precondition(
        raw_slice != _hand_prefix(1),
        "the crafted bits do not discriminate the raw byte slice (no round-1/2 bits "
        "share the boundary byte)", remedy="set a bit in positions 3..7 of some shot")

    def _prefix_midbyte_check(candidate, _gate_tol):
        assert bytes(candidate) == bytes(ss.syndrome_prefix_bytes(1)), \
            "candidate mid-byte prefix mismatch"
    assert_control_trips(_prefix_midbyte_check, raw_slice, 0.0)


# =========================================================================== #
# AM-5: tie-break conformance micro-test on _leak_sample's new return value    #
# =========================================================================== #
@requires_cuda
def test_am5_leak_sample_tiebreak_registry():
    """AM-5: the prereg tie-break registry's EXECUTABLE TRANSCRIPTION outside the arm
    (batched_mps_backend_prereg v2/v5: serial rule = first k with ``u*tot <= cumsum_k``,
    fallback K-1). Defends: K-3 (tie-break/comparison drift: ``<=`` vs ``<``,
    first-vs-last, argmax-on-bool), K-2 (fallback index off-by-one).

    Landscape BY CONSTRUCTION: ``K_k = sqrt(q_k) * I`` with q = (0.25, 0.35, 0.40)
    (sum K^H K = I), so ``p_k = q_k * <psi|psi>`` for ANY state -- the cumulative
    boundary after branch 0 is known exactly. The floats _leak_sample will actually
    compute are PROBED first with the same canonical-local-expectation call on MPS
    copies (bitwise determinism asserted as a precondition), then:

      * exact-boundary leg (K-3, strict-vs-nonstrict): search a few ULPs around
        cum_0/tot for a u with ``float(u)*tot == cum_0`` EXACTLY; the serial ``<=``
        semantics MUST select the BOUNDARY branch 0, never branch 1 (a ``<`` drift
        selects 1). A failed search is a LOUD class-(c) PRECONDITION failure (the
        crafted landscape must admit an exact float boundary) -- never a silently
        skipped leg.
      * hair-below / hair-above legs: ``u*tot = cum_0 -/+ 1e-12`` must select 0 / 1
        respectively -- the flip pins the boundary location to within 1e-12 (>> the
        ~1e-16 fp noise of the probed pk, << the 0.35 gap to the next boundary), the
        contract's registered fallback when the exact boundary is unreachable. The
        flip IS the sabotage pair: a first-vs-last or argmax drift fails both legs.
      * fallback leg: ``u = 1.0 - 1e-16`` (one ULP below 1.0) -> index K-1 = 2. Note
        the registry's init-fallback and the last-iteration selection COINCIDE at K-1
        (tot and the cumsum accumulate the same floats in the same order, so the pure
        undershoot branch is unreachable); this leg asserts the u->1 limit VALUE.
    """
    n, site = 3, 1  # tiny chain; mid-site exercises canonicalization
    q_weights = (0.25, 0.35, 0.40)
    eye = torch.eye(PHYS, dtype=CDTYPE, device=DEVICE)
    kraus = [math.sqrt(q) * eye for q in q_weights]

    # tiny quimb MPS loader -- the 3-line pattern of
    # tests/test_batched_mps_ops.py::_qmps_from_dense_row (lines 232-239).
    rng = np.random.default_rng(1234)
    v = rng.standard_normal(PHYS ** n) + 1j * rng.standard_normal(PHYS ** n)
    v = (v / np.linalg.norm(v)).astype(np.complex128)
    mps = qtn.MatrixProductState.from_dense(v, dims=[PHYS] * n)
    mps.apply_to_arrays(lambda x: torch.as_tensor(x, dtype=CDTYPE, device=DEVICE))

    # cheap constructor -- tests/test_batched_mps_ops.py::_fwd (lines 218-222).
    fwd = MpsLeakageForward(device=DEVICE)

    def _probe_pk(m) -> list[float]:
        """The SAME pk floats _leak_sample computes (same call, same order, fresh
        info cache) -- the site_rdm-equivalent probe on a copy."""
        info: dict = {}
        return [float(m.local_expectation_canonical(
                    K.conj().transpose(-1, -2) @ K, site, normalized=False,
                    info=info).real) for K in kraus]

    pk1 = _probe_pk(mps.copy())
    pk2 = _probe_pk(mps.copy())
    require_precondition(pk1 == pk2,
                         "pk probe is not bitwise deterministic across MPS copies "
                         "(the exact-boundary leg would be ill-defined)",
                         remedy="drop to the hair-below/above legs only")
    require_precondition(
        all(abs(p - q) < 1e-10 for p, q in zip(pk1, q_weights)),
        f"probed pk {pk1} drifted from the constructed landscape {q_weights}",
        remedy="re-seed the state")

    # replicate _leak_sample's accumulation arithmetic on the probed floats.
    tot = float(sum(pk1))
    cum0 = 0.0 + pk1[0]

    def _drive(u: float) -> int:
        sel = fwd._leak_sample(mps.copy(), kraus, site, float(u))
        assert sel is not None and isinstance(sel, (int, np.integer)), \
            f"A3 contract: _leak_sample must RETURN the selected branch index (got {sel!r})"
        return int(sel)

    # exact-boundary search (a few ULPs around cum0/tot).
    u_exact = None
    for direction in (0.0, 2.0):
        u = cum0 / tot
        for _ in range(64):
            if u * tot == cum0:
                u_exact = u
                break
            u = float(np.nextafter(u, direction))
        if u_exact is not None:
            break

    require_precondition(
        u_exact is not None,
        "the exact-boundary nextafter search found no u with float(u)*tot == cum_0 "
        "(the K-3 strict-vs-nonstrict leg would be silently skipped)",
        remedy="adjust the crafted pk landscape so an exact float boundary exists")
    assert _drive(u_exact) == 0, \
        "u*tot == cum_0 exactly must select the BOUNDARY branch 0 (registry '<=' " \
        "semantics); selecting 1 is the strict-'<' drift (K-3)"
    # hair-below / hair-above (the registered +/-1e-12 fallback pair; see docstring).
    assert _drive((cum0 - 1e-12) / tot) == 0, \
        "u*tot = cum_0 - 1e-12 must stay on branch 0 (K-3 boundary pin, below)"
    assert _drive((cum0 + 1e-12) / tot) == 1, \
        "u*tot = cum_0 + 1e-12 must flip to branch 1 (K-3 boundary pin, above)"
    # fallback leg: u one ULP below 1.0 -> the last branch index K-1 (K-2 off-by-one).
    assert _drive(1.0 - 1e-16) == len(kraus) - 1, \
        "u -> 1 limit must select index K-1 (registry fallback value)"


# =========================================================================== #
# A3: attach_layout is a pure addition; mps_from_statevector round-trips       #
# =========================================================================== #
@requires_cuda
@requires_data
def test_a3_attach_layout_pure_addition():
    """A3 attach_layout seam. Defends: K-1 (an attach_layout that silently does
    nothing would pass the byte gate trivially -- the layout attrs are probed as the
    anti-inert leg), K-6 (DIRECTION drift: ``order`` is site->engine, ``order[k]`` =
    engine position at MPS site ``k``, and ``_eng_to_mps`` its INVERSE; a NON-identity
    NON-involutory permutation makes the inverted and un-inverted maps distinct, and
    the UN-inverted expectation is DEMONSTRATED to trip), K-9 (state contamination:
    priming must not leak into a subsequent sample()), K-5 (non-vacuity control on
    the byte equality).

    Also pins the landed Mapping REJECTION: passing the eng->mps dict itself instead
    of the order tuple raises ``TypeError`` (dict iteration yields keys only -- the
    silent insertion-order reinterpretation hazard).

    Gate: a sample() run AFTER calling attach_layout on a FRESH instance is
    byte-identical to the baseline (pure addition -- sample() owns/overwrites the
    layout; the seam only replaces the test-side _prime_fwd ritual).
    """
    R, N = 1, 2
    sched, spec = _sched_and_spec(R=R, N=N, seed=23)
    ss_base, _ = MpsLeakageForward(device=DEVICE).sample(spec, sched=sched)
    assert ss_base.shots is not None

    n = int(sched.n_data)
    # NON-identity, NON-involutory site->engine order (cyclic shift): its inverse
    # DIFFERS from its un-inverted reading, so the direction is actually testable
    # (a reversal is an involution -- inverted == un-inverted -- and would be vacuous).
    order = tuple((k + 1) % n for k in range(n))
    eng_to_mps_hand = {order[k]: k for k in range(n)}   # hand-inverted: engine -> site
    wrong_direction = {k: order[k] for k in range(n)}   # UN-inverted: site -> engine
    require_precondition(
        eng_to_mps_hand != wrong_direction,
        "the chosen order is involutory (inverted == un-inverted; the K-6 direction "
        "killer would be vacuous)", remedy="pick a non-involutory permutation")
    log_support = sorted(int(q) for q in sched.logical.keys())

    fwd2 = MpsLeakageForward(device=DEVICE)
    # Mapping REJECTION (landed guard): the eng->mps dict is NOT an order tuple.
    with pytest.raises(TypeError):
        fwd2.attach_layout(eng_to_mps_hand, log_support)
    fwd2.attach_layout(order, log_support)
    # anti-inert leg (K-1) + direction pin (K-6): _eng_to_mps must be the INVERSE of
    # the site->engine order tuple (the _prime_fwd ritual it replaces set exactly
    # these attrs -- tests/test_batched_mps_ops.py::_prime_fwd, lines 225-229).
    assert getattr(fwd2, "_eng_to_mps", None) == eng_to_mps_hand, \
        "attach_layout did not prime _eng_to_mps with the INVERTED (engine->site) " \
        "map (inert seam K-1 / direction drift K-6)"
    assert list(getattr(fwd2, "_log_eng_support", [])) == log_support, \
        "attach_layout did not prime _log_eng_support (inert seam, K-1)"

    # KILLER (K-6): the UN-inverted (wrong-direction) expectation must trip.
    def _layout_direction_check(candidate, _gate_tol):
        assert getattr(fwd2, "_eng_to_mps", None) == candidate, \
            "layout direction mismatch"
    assert_control_trips(_layout_direction_check, wrong_direction, 0.0)

    ss_after, _ = fwd2.sample(spec, sched=sched)
    assert _hand_packed(ss_after) == _hand_packed(ss_base), \
        "sample() after attach_layout != baseline sample() (attach_layout must be a " \
        "PURE ADDITION -- K-9 contamination)"
    tb_a = np.asarray(ss_after.diag["terminal_bits"])
    tb_b = np.asarray(ss_base.diag["terminal_bits"])
    assert np.array_equal(tb_a, tb_b), "terminal bit side-channel differs (K-9)"

    # K-5 non-vacuity control: a corrupted buffer DEMONSTRABLY trips the byte gate.
    corrupted = bytearray(_hand_packed(ss_base))
    corrupted[0] ^= 0xFF

    def _byte_equality_check(candidate, _gate_tol):
        assert bytes(candidate) == _hand_packed(ss_after), "candidate buffer mismatch"
    assert_control_trips(_byte_equality_check, bytes(corrupted), 0.0)


@requires_cuda
def test_a3_mps_from_statevector_roundtrip():
    """A3 module-level loader ``mps_from_statevector(psi, order, device)`` (three
    required positionals). Defends: K-8 (site-order/MSB convention drift -- the
    site-0-MSB ``from_dense(dims=[3]*n)`` convention, with ``order[k]`` = the engine
    axis carried at MPS site ``k``), K-1 (a DEAD ``order`` parameter: the identity-
    and non-identity-order builds must produce DIFFERENT raw dense forms --
    demonstrated), K-5 (the control proves the 1e-13 gate resolves the permutation).

    Gate: with a NON-identity ``order`` the raw ``to_dense()`` is the SNAKE-basis
    vector (psi with engine axes transposed into site axes); inverting the
    permutation recovers the ORIGINAL psi at 1e-13; the identity-order build
    round-trips onto psi directly. KILLER (K-1/K-8): the identity-order build's
    dense form is DEMONSTRATED to differ from the non-identity build's raw
    snake-basis dense form at the same 1e-13 gate (an order-ignoring implementation
    would make the two coincide).
    """
    n = 4
    order = (2, 0, 3, 1)                            # NON-identity site->engine order
    inv = tuple(int(i) for i in np.argsort(order))  # inv[order[k]] = k
    rng = np.random.default_rng(7)
    v = rng.standard_normal(PHYS ** n) + 1j * rng.standard_normal(PHYS ** n)
    v = v / np.linalg.norm(v)
    psi = torch.tensor(v, dtype=CDTYPE, device=DEVICE)
    # the snake-basis form the non-identity build must produce (independent transpose).
    psi_snake = psi.reshape([PHYS] * n).permute(*order).contiguous().reshape(-1)
    require_precondition(
        float(torch.max(torch.abs(psi_snake - psi)).item()) > 1e-6,
        "drawn state is invariant under the chosen permutation (the K-1 dead-order "
        "killer would be vacuous)", remedy="re-seed / re-pick the order")

    def _dense(mps) -> torch.Tensor:
        d = mps.to_dense()
        if not isinstance(d, torch.Tensor):
            d = torch.as_tensor(np.asarray(d))
        return d.reshape(-1).to(device=psi.device, dtype=CDTYPE)

    dense_nid = _dense(mf.mps_from_statevector(psi, order, DEVICE))
    # the raw dense form IS the snake-basis vector (order actually consumed, K-8)...
    err_snake = float(torch.max(torch.abs(dense_nid - psi_snake)).item())
    assert err_snake < 1e-13, \
        f"raw to_dense != psi permuted by order (max err {err_snake:.3e}, K-8)"
    # ...and inverting the site permutation recovers the ORIGINAL engine-basis psi.
    psi_rec = dense_nid.reshape([PHYS] * n).permute(*inv).contiguous().reshape(-1)
    err = float(torch.max(torch.abs(psi_rec - psi)).item())
    assert err < 1e-13, \
        f"inverse-permuted round-trip max|P^-1(to_dense) - psi| = {err:.3e} >= 1e-13"

    # identity-order build round-trips onto psi directly.
    dense_id = _dense(mf.mps_from_statevector(psi, tuple(range(n)), DEVICE))
    err_id = float(torch.max(torch.abs(dense_id - psi)).item())
    assert err_id < 1e-13, \
        f"identity-order round-trip max|to_dense - psi| = {err_id:.3e} >= 1e-13"

    # KILLER (K-1/K-8): identity vs non-identity raw dense forms must DIFFER at the
    # gate (the discriminating comparison is proven to discriminate).
    def _order_discrimination_check(candidate, gate_tol):
        e = float(torch.max(torch.abs(dense_id - candidate)).item())
        assert e < gate_tol, f"identity/non-identity dense mismatch {e:.3e}"
    assert_control_trips(_order_discrimination_check, dense_nid, 1e-13)
