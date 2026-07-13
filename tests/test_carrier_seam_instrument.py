"""ADR 0008 SEAM-TEST -- S1 build checks: the strip instrument + teachers.

FIX ROUND (2026-06-10): rebuilt against SEAM-TEST PRE-RUN AMENDMENT 1
(docs/metric_results.md) -- the instrument is the DISJOINT two-window strip
(ruling 1: seam DATA pair shared across the seam, NO check measured on it;
extraction = per-window checks only), the scored family is the
``StripObservations`` strip joint (ruling 2), production = windows (3, 4),
D = 7 data, 12 instrument qubits under the 2D-2 accounting (ruling 3).

Covers registration items 1 (instrument) and 2 (teachers), and supplies /
validates the contexts items 4-7 score. BUILD-ONLY scope: no carrier fits, no
production runs -- every law here is the forward/exact oracle on toy strips,
CPU per the device policy (the toy-scale enumeration is launch-bound on CUDA).
Law toy: windows (2, 2) -> D = 4 data, 6 instrument qubits (the same window
sizes as the carrier side's structural-pin instrument ``StripSpec(2, 2)``; the
same data count as the pre-fix toy, so the ladder-count pins carry verbatim).
Layout toy: windows (3, 3) -> D = 6, used at rounds = 1 for the record-layout
cross-check against the carrier's OWN splitter (enumeration is 2**K branches,
K = rounds*(D-2) + D, so (3, 3) is out of reach at the R3/R4 contexts).

Epistemic classes (METRICS.md declaration rule):
  (a) the T-B/T-A record-chain identities (D5 closed forms vs an independent
      numerical chain computation), CPTP closures, the phi=0 reduction, the
      ROUNDS=1 repeats=1 phi-blindness (disjoint-geometry theorem: the single
      edge application -- a Z(x)Z-diagonal unitary or its twirl -- is followed
      ONLY by Z-diagonal operations, parity projections and final Z readout,
      with which it commutes term-by-term, so it cancels from the record law
      exactly), the stochastic-backdrop phi-blindness at ANY rounds (a
      Pauli-Z-basis backdrop maps diagonals to diagonals and off-diagonals to
      off-diagonals, so the phi-marked coherences never reach any diagonal
      readout functional), the phi-parity of pre_rotation=0 contexts (T2': the
      (prod Z) o K anti-unitary maps the circuit at phi to -phi; the proof
      never references WHICH parities are measured, so it survives the
      disjoint extraction), the twirl's exact phi-sign blindness (the channel
      is even in phi), the rounds=1 record/data-parity column identities, and
      the zero-seam family equality against the carrier's composed law (S2's
      structural pin replicated from the instrument side). Record-level law
      gaps bound the declared-family gaps (grouping is a data processing).
  (c) the visibility GUARDS: TV > 1e-8 / 1e-9 floors that the registered
      phi-sensitive functionals are non-degenerate at toy size; the
      bunching-vs-ablation record-visibility guard TV > 1e-6 (declared here
      per reviewer build_R_seam_review.md section E); the multi-round
      seam-coherence build-sanity ceiling TV <= 1e-1 (AMENDMENT 2 ruling 13);
      the positive-mass floor
      (probs > NUMERICAL_ZERO) used to select branches in the layout checks.
      Build sanity, not registered thresholds.

FIX ROUND 2 (R2-1, build_R2_seam_postfix_review.md section B): the
memory-bounded grouped oracle evaluator is pinned (a)-class BIT-EXACT against
the monolithic enumeration at toy scale (the StripObservations joint AND the
window-record marginal laws; total mass |sum p - 1| <= 1e-12), and the
oracle_memory_probe dry-run is pinned exactly equal to the instrumented walk's
counters. (c)-class declarations carried by this suite for R2-1:
ORACLE_LIVE_BRANCH_CAP = 512 (the live-branch execution cap -- bounds RESIDENT
branches, never truncates), MONOLITHIC_ORACLE_MAX_BYTES = 64 MiB (the "auto"
routing threshold; every pre-fix toy law stays monolithic, so the 16 pre-fix
tests run unchanged), the transient-memory model factors (5x doubling /
5x noise layer), and the production smoke bounds dm_peak <= 1.1e9 /
est_peak <= 2.5e9. The window-marginal SPLITTER-route cross-check uses a
DERIVED 1e-14 re-association bound (same per-cell multiset summed in a
different order; |delta| <= (n_terms - 1) * 2**-53 * cell_mass <= 7.0e-15 at
the toy sizes) -- the joint law itself carries NO such allowance: the record ->
code-pair GF(2) bijection makes the grid accumulation collision-free, hence
bit-exact.

REGISTRATION DISCREPANCY FLAG (pre-run, derivation BEFORE measurement --
escalated to the registrar; see build_S1_instrument.md FIX ROUND):
amendment ruling 4 declares P-a (oracle law(phi-edge) vs law(no-edge) at
repeats=1, gap <= 1e-10) class (a) in the disjoint geometry. Derivation says
this holds as a THEOREM only at rounds=1 (or for a stochastic backdrop): with
the seam pair UNCHECKED, in-window extraction leaves single-window-flip
coherence pairs alive with UNEQUAL seam-pair parity; U_phi marks them
(e^{-+2i phi}), and the registered COHERENT backdrop component (RX) converts
them to the diagonal in later rounds. Predicted multi-round oracle gap at the
(2, 2) toy, phi = 0.15: TV ~ (1 - cos 2 phi) * beta^2|A| * O(1) ~ 1e-5 for
pre_rotation=0 (even in phi, T2'-consistent), larger (up to ~1e-4..1e-3) for
the ry probes (beta = cos(theta/2) sin(theta/2) (1-2p) ~ 0.0988). This is
exactly registration item 7's EMERGENT "across the seam" H2-T1 slot, now
visible on the ORACLE itself. The tests below pin the true theorems at 1e-10
and MEASURE the multi-round gap (ceiling-only assert); if the run shows all
multi-round gaps <= 1e-10 the derivation is wrong and the registered blanket
P-a assert must be restored.
"""

from __future__ import annotations

import math

import pytest

import torch

from qec_twin.contexts.seam_strip import (
    MAX_ORACLE_QUBITS,
    MONOLITHIC_ORACLE_MAX_BYTES,
    ORACLE_LIVE_BRANCH_CAP,
    PRODUCTION_WINDOW_SIZES,
    TILING_FAMILY,
    TOY_WINDOW_SIZES,
    ObservationTeacher,
    SeamStrip,
    oracle_memory_probe,
    production_strip,
    toy_strip,
)
from qec_twin.forward.exact.circuit_sim import bit_flip
from qec_twin.forward.scalable import (
    StripSpec,
    composed_strip_law,
    split_strip_record,
    strip_observations_from_records,
    window_joint_codes,
    zero_seam_exactness_pin,
)
from qec_twin.mechanisms.seam_teachers import (
    BACKDROP_FLIP_RATE,
    SEAM_PHI_REF,
    SEAM_PHI_REGIME,
    TB_BUNCHING_RATIO,
    TB_FLIP_RATE,
    TB_LAMBDA1,
    TB_P01,
    TB_P10,
    SeamNoiseProcess,
    backdrop_kraus,
    backdrop_teacher,
    bias_injected_coherent_teacher,
    coherent_seam_teacher,
    pauli_ablation_teacher,
    seam_teacher_arms,
    tb_bunching_teacher,
    tb_markov_kraus,
    tb_member_from_rate_and_ratio,
    tb_record_chain_stats,
    twirled_seam_teacher,
)
from qec_twin.mechanisms.teachers import zz_coupling_kraus
from qec_twin.numerics import NUMERICAL_ZERO

# --------------------------------------------------------------------------- #
# Toy instrument + teacher arms (module-level: cheap frozen constructions)     #
# --------------------------------------------------------------------------- #
TOY = toy_strip()  # law toy: windows (2, 2) -> D = 4 data, 6 instrument qubits
PHI_TOP = SEAM_PHI_REGIME[1]  # regime top, the strongest registered edge

BACKDROP = backdrop_teacher(TOY)
COH = {
    p: coherent_seam_teacher(TOY, phi=p)
    for p in (0.0, SEAM_PHI_REF, -SEAM_PHI_REF, PHI_TOP, -PHI_TOP)
}
TWIRL = {p: twirled_seam_teacher(TOY, phi=p) for p in (SEAM_PHI_REF, -SEAM_PHI_REF, PHI_TOP)}
BUNCH = tb_bunching_teacher(TOY)
ABLATE = pauli_ablation_teacher(TOY)

SANDWICH = TOY.sandwich_eval_context()  # eval:R4-k2 (repeats=2, pre_rotation=0)
K2RY = next(
    c for c in TOY.calibration_contexts(4) if c.repeats == 2 and c.pre_rotation > 0.0
)  # r4:R2-L0-k2ry -- the phi-linear signed probe


def _tv(fa, fb) -> float:
    # branch-aligned TV: identical enumeration order is asserted, so the
    # branch-wise L1 is the exact record-law TV (and bounds the family TV).
    assert torch.equal(fa.measurement_record, fb.measurement_record)
    return 0.5 * float((fa.probs - fb.probs).abs().sum())


def _branch_kl(fa, fb) -> float:
    """Exact record-level KL(p||q) over aligned branches (zero-mass branches
    carry no KL; q is clamp-guarded -- for theorem pairs q matches p's support)."""
    assert torch.equal(fa.measurement_record, fb.measurement_record)
    p = fa.probs.to(torch.float64)
    q = fb.probs.to(torch.float64)
    mask = p > 0
    return float((p[mask] * (torch.log(p[mask]) - torch.log(q[mask].clamp_min(1e-300)))).sum())


@pytest.fixture(scope="module")
def law():
    """Memoized toy-strip oracle laws keyed by (teacher name, context key)."""
    cache: dict = {}

    def _law(teacher, ctx):
        key = (teacher.name, ctx.key)
        if key not in cache:
            cache[key] = TOY.oracle_law(ctx, teacher)
        return cache[key]

    return _law


# --------------------------------------------------------------------------- #
# Registration item 1 -- strip geometry, tiling, envelope (amendment 1-3)       #
# --------------------------------------------------------------------------- #
def test_strip_geometry_production_and_toy() -> None:
    prod = production_strip()
    assert PRODUCTION_WINDOW_SIZES == (3, 4)  # amendment ruling 3
    assert (prod.window_a_size, prod.window_b_size) == PRODUCTION_WINDOW_SIZES
    assert prod.distance == 7  # 7 data qubits total
    assert prod.total_qubits == 12  # 2D-2 disjoint-extraction accounting
    assert prod.seam_pair == (2, 3)
    assert prod.window_a == (0, 1, 2)
    assert prod.window_b == (3, 4, 5, 6)
    assert prod.window_a_checks == (0, 1)
    assert prod.window_b_checks == (3, 4, 5)
    assert prod.seam_pair_index == 2  # the UNMEASURED adjacent pair

    assert TOY_WINDOW_SIZES == (2, 2)
    for strip, n_total in ((TOY, 6), (SeamStrip(2, 3), 8), (SeamStrip(3, 3), 10)):
        a, b = set(strip.window_a), set(strip.window_b)
        # disjoint contiguous windows covering the strip (amendment ruling 1) ...
        assert a | b == set(strip.data_qubits)
        assert a & b == set()
        # ... sharing the seam DATA pair across the seam: one qubit each side
        i, j = strip.seam_pair
        assert j == i + 1
        assert i == max(a) and j == min(b)
        # NO check on the seam pair: measured checks = per-window pairs only
        measured = set(strip.window_a_checks) | set(strip.window_b_checks)
        assert set(strip.window_a_checks) & set(strip.window_b_checks) == set()
        assert strip.seam_pair_index not in measured
        assert measured == set(range(strip.distance - 1)) - {strip.seam_pair_index}
        assert strip.num_checks == strip.distance - 2 == len(measured)
        assert strip.total_qubits == n_total

    # the declared tiling is an attribute of the instrument (frozen descriptor)
    # and names the SAME family as the carrier's StripSpec (one shared instrument)
    tiling = prod.tiling
    assert tiling.family == TILING_FAMILY == StripSpec(3, 4).tiling
    assert tiling.window_a == prod.window_a
    assert tiling.window_b == prod.window_b
    assert tiling.seam_pair == prod.seam_pair
    with pytest.raises(Exception):
        tiling.seam_pair = (0, 1)  # frozen: tiling is family design, never a knob


def test_strip_envelope_guards() -> None:
    # degenerate windows rejected (each window needs >= 1 internal check)
    with pytest.raises(ValueError):
        SeamStrip(1, 3)
    with pytest.raises(ValueError):
        SeamStrip(2, 1)
    # the registered DM-oracle envelope under the 2D-2 accounting: the cap 13
    # stays (registered constant); D = 7 -> 12 is the envelope maximum (the
    # even accounting never attains 13), D >= 8 -> >= 14 is out
    assert production_strip().total_qubits == 12 <= MAX_ORACLE_QUBITS
    for sizes in ((4, 4), (3, 5), (4, 5), (5, 5)):
        with pytest.raises(ValueError):
            SeamStrip(*sizes)


def test_context_ladder_counts_and_probes() -> None:
    # cumulative H2 ladder reused verbatim at the strip data count (D = 4: the
    # same distance as the validated pre-fix toy, so the counts pin identically)
    sizes = {r: len(TOY.calibration_contexts(r)) for r in range(5)}
    assert sizes == {0: 1, 1: 6, 2: 8, 3: 10, 4: 12}
    for r in range(1, 5):  # monotone nesting C_cal(r-1) subset C_cal(r)
        keys_lo = {c.key for c in TOY.calibration_contexts(r - 1)}
        keys_hi = {c.key for c in TOY.calibration_contexts(r)}
        assert keys_lo < keys_hi
    full = TOY.calibration_contexts(4)
    assert all(c.distance == TOY.distance for c in full)
    # the ladder includes the repeated-storage (sandwich-type) and k2ry probes
    assert any(c.repeats == 2 and c.pre_rotation == 0.0 for c in full)  # r2 k2 rungs
    assert any(c.repeats == 2 and c.pre_rotation > 0.0 for c in full)  # r4 k2ry
    # ladder is bounded at the registered r <= 4
    with pytest.raises(NotImplementedError):
        TOY.calibration_contexts(5)

    # held-out seam evals: the R4-k2 sandwich + the k2ry exotics
    evals = TOY.seam_eval_contexts()
    assert evals["memory"].repeats == 1 and evals["memory"].rounds == 4
    assert evals["sandwich"].repeats == 2 and evals["sandwich"].pre_rotation == 0.0
    assert any(c.repeats == 2 and c.pre_rotation > 0.0 for c in evals["exotics"])
    cal_keys = {c.key for c in full}
    for ctx in (evals["memory"], evals["sandwich"], *evals["exotics"]):
        assert ctx.distance == TOY.distance
        assert ctx.key not in cal_keys  # held-out: disjoint from every rung


# --------------------------------------------------------------------------- #
# Registration item 2 -- T-B / T-A teacher identities ((a)-class)               #
# --------------------------------------------------------------------------- #
def _chain_from_kraus(kraus: torch.Tensor):
    """Independently rebuild the record chain from the KRAUS ACTION on Z states."""
    outs = []
    for b in (0, 1):
        rho = torch.zeros((2, 2), dtype=kraus.dtype)
        rho[b, b] = 1.0
        out = sum(k @ rho @ k.conj().T for k in kraus)
        # populations only; off-diagonals must vanish on diagonal inputs
        assert float(out[0, 1].abs() + out[1, 0].abs()) <= NUMERICAL_ZERO
        outs.append(torch.stack([out[0, 0].real, out[1, 1].real]))
    transition = torch.stack(outs, dim=1)  # T[i_out, j_in]
    return transition


def _chain_stats(transition: torch.Tensor) -> dict[str, float]:
    """Stationary flip-process functionals computed by explicit chain products."""
    p01 = float(transition[1, 0])
    p10 = float(transition[0, 1])
    s = p01 + p10
    pi = torch.tensor([p10 / s, p01 / s], dtype=torch.float64)
    t64 = transition.to(torch.float64)
    assert float((t64 @ pi - pi).abs().max()) <= NUMERICAL_ZERO  # stationarity
    flip = torch.tensor([p01, p10], dtype=torch.float64)  # P(flip | state)
    after = {0: 1, 1: 0}  # state after a flip
    r = float((pi * flip).sum())
    pff = sum(float(pi[i] * flip[i] * flip[after[i]]) for i in (0, 1))
    pfff = sum(float(pi[i] * flip[i] * flip[after[i]] * flip[after[after[i]]]) for i in (0, 1))
    # lag-2 flip pair: one non-flip step between the two flips
    pf_f2 = 0.0
    for i in (0, 1):
        mid = after[i]
        for j in (0, 1):
            step = float(t64[j, mid])
            pf_f2 += float(pi[i] * flip[i]) * step * float(flip[j])
    lam = torch.linalg.eigvals(t64).real
    lam1 = float(lam.min())  # eigenvalues {1, 1 - p01 - p10}
    return {
        "r": r,
        "R": pff / r**2,
        "R2": pf_f2 / r**2,
        "T3": pfff / r**3,
        "lambda1": lam1,
        "p01": p01,
        "p10": p10,
    }


def test_tb_member_identities() -> None:
    kraus = tb_markov_kraus(TB_P01, TB_P10)
    # CPTP closure (structural): sum K^dag K = I
    closure = sum(k.conj().T @ k for k in kraus)
    assert float((closure - torch.eye(2, dtype=kraus.dtype)).abs().max()) <= NUMERICAL_ZERO

    # the Kraus action realizes the declared two-state Markov transition exactly
    transition = _chain_from_kraus(kraus)
    target = torch.tensor(
        [[1.0 - TB_P01, TB_P10], [TB_P01, 1.0 - TB_P10]], dtype=torch.float64
    )
    assert float((transition.to(torch.float64) - target).abs().max()) <= NUMERICAL_ZERO

    # chain functionals: independent numerical chain vs D5 closed forms
    num = _chain_stats(transition)
    form = tb_record_chain_stats(TB_P01, TB_P10)
    for key in ("r", "R", "lambda1", "T3"):
        assert abs(num[key] - form[key]) <= 1e-12 * max(1.0, abs(form[key])), key

    # registered member values ((a)-class identities of the registration):
    # r = 2 p01 p10 / (p01 + p10) = 1.27e-2; R = (p01+p10)^2/(4 p01 p10) = 5;
    # lambda1 = 1 - p01 - p10 = 0.873
    assert abs(num["r"] - TB_FLIP_RATE) <= 1e-6
    assert abs(num["R"] - TB_BUNCHING_RATIO) <= 1e-4
    assert abs(num["lambda1"] - TB_LAMBDA1) <= 1e-6

    # T3 triple pin: T-B predicts T3 = R exactly (renewal after two flips)
    assert abs(num["T3"] - num["R"]) <= 1e-9 * num["R"]
    # multi-lag law at k = 2: R_k = 1 + (R - 1) lambda1^{k-1}
    predicted_r2 = 1.0 + (num["R"] - 1.0) * num["lambda1"]
    assert abs(num["R2"] - predicted_r2) <= 1e-9 * predicted_r2
    # D5 inversion: {p01, p10} = r R (1 +/- sqrt(1 - 1/R)) reproduces the member
    lo, hi = tb_member_from_rate_and_ratio(num["r"], num["R"])
    assert abs(lo - min(TB_P01, TB_P10)) <= 1e-9 * TB_P10
    assert abs(hi - max(TB_P01, TB_P10)) <= 1e-9 * TB_P10
    # ceiling R <= 1/(2r)
    assert num["R"] <= 1.0 / (2.0 * num["r"]) + 1e-12


def test_pauli_ablation_member_structural_pins() -> None:
    # T-A in-family: p01 = p10 = r pins R_k == 1 at every lag (STRUCTURAL --
    # a violation is a build bug, never a finding)
    kraus = tb_markov_kraus(TB_FLIP_RATE, TB_FLIP_RATE)
    closure = sum(k.conj().T @ k for k in kraus)
    assert float((closure - torch.eye(2, dtype=kraus.dtype)).abs().max()) <= NUMERICAL_ZERO

    num = _chain_stats(_chain_from_kraus(kraus))
    assert abs(num["r"] - TB_FLIP_RATE) <= 1e-12  # matched registered record rate
    assert abs(num["R"] - 1.0) <= 1e-9  # R = 1 exactly (iid record)
    assert abs(num["R2"] - 1.0) <= 1e-9
    assert abs(num["T3"] - 1.0) <= 1e-9
    assert abs(num["lambda1"] - (1.0 - 2.0 * TB_FLIP_RATE)) <= 1e-12
    assert ABLATE.params["R"] == pytest.approx(1.0, abs=1e-12)


# --------------------------------------------------------------------------- #
# D8 equal treatment + oracle sanity (registration items 1/2 + item 7 floors)   #
# --------------------------------------------------------------------------- #
def test_equal_treatment_interface_and_normalization() -> None:
    arms = seam_teacher_arms(TOY, bias_delta=0.02)
    assert set(arms) == {"backdrop", "coherent", "twirled", "bunching", "ablation", "bias"}
    ctx = TOY.calibration_contexts(0)[0]  # r0:R2-L0
    ref_law = None
    ref_obs = None
    for arm in arms.values():
        assert isinstance(arm, ObservationTeacher)  # the D8 observation surface
        assert isinstance(arm.params, dict) and arm.params  # declared constants
        strip_law = TOY.oracle_law(ctx, arm)
        # structural pins (registration item 7): normalization + zero nonpositive
        assert abs(float(strip_law.total_probability()) - 1.0) <= 1e-9
        assert float(strip_law.probs.min()) >= -NUMERICAL_ZERO
        # the declared scored family (amendment ruling 2): grouped via the
        # carrier's OWN splitter; normalization carries through the grouping
        obs = strip_law.observations()
        assert abs(float(obs.probs.sum()) - 1.0) <= 1e-9
        if ref_law is None:
            ref_law, ref_obs = strip_law, obs
        else:
            # identical declared block family: the enumerated record set (and
            # hence the per-window code-pair support) is teacher-independent
            assert torch.equal(strip_law.measurement_record, ref_law.measurement_record)
            assert torch.equal(obs.codes_left, ref_obs.codes_left)
            assert torch.equal(obs.codes_right, ref_obs.codes_right)

    # record layout: K = rounds*(D-2) + D -- NO seam-check column
    d, r = TOY.distance, ctx.rounds
    assert ref_law.measurement_record.shape[1] == r * (d - 2) + d
    out_a, out_b = ref_law.window_records()
    assert out_a.shape[1] == r * (TOY.window_a_size - 1) + TOY.window_a_size
    assert out_b.shape[1] == r * (TOY.window_b_size - 1) + TOY.window_b_size


def test_oracle_phi_zero_reduces_to_backdrop_bit_consistently(law) -> None:
    # phi = 0: U_0 = I4 is still APPLIED through the edge slot (non-vacuous)
    assert COH[0.0].edge_field is not None
    assert COH[0.0].edge_field(0, TOY.seam_pair) is not None
    contexts = [
        TOY.calibration_contexts(0)[0],  # r0:R2-L0
        next(c for c in TOY.calibration_contexts(2) if c.repeats == 2),  # r2:R2-k2
        K2RY,
    ]
    for ctx in contexts:
        fa, fb = law(COH[0.0], ctx), law(BACKDROP, ctx)
        assert torch.equal(fa.measurement_record, fb.measurement_record), ctx.label
        assert torch.equal(fa.probs, fb.probs), ctx.label


def test_oracle_guards() -> None:
    other = SeamStrip(2, 3)  # data count 5 != TOY's 4
    ctx5 = other.calibration_contexts(0)[0]
    with pytest.raises(ValueError):
        TOY.oracle_law(ctx5, BACKDROP)


# --------------------------------------------------------------------------- #
# P-a in the disjoint geometry (amendment ruling 4) -- the theorem part         #
# --------------------------------------------------------------------------- #
def test_rounds1_repeats1_contexts_phi_blind(law) -> None:
    # (a) Disjoint-geometry theorem: at rounds=1, repeats=1 the edge (coherent
    # Z(x)Z unitary or its twirl) applies ONCE and is followed only by
    # Z-diagonal operations (the in-window parity projections and the final
    # all-qubit Z readout), with which it commutes term-by-term -- it cancels
    # from the record law exactly, for ANY prep (incl. ry) and ANY backdrop.
    contexts = [c for c in TOY.calibration_contexts(4) if c.repeats == 1 and c.rounds == 1]
    assert len(contexts) == 3  # r1:R1-L0, r1:R1-L1, r3:R1-L0-ry
    for ctx in contexts:
        base = law(BACKDROP, ctx)
        for arm in (COH[PHI_TOP], TWIRL[PHI_TOP]):
            f = law(arm, ctx)
            tv = _tv(f, base)
            kl = _branch_kl(f, base)
            assert tv <= 1e-10, f"{ctx.label}/{arm.name}: rounds=1 blindness violated (TV={tv:.3e})"
            assert kl <= 1e-10, f"{ctx.label}/{arm.name}: rounds=1 blindness violated (KL={kl:.3e})"


def test_stochastic_backdrop_phi_blind_any_rounds() -> None:
    # (a) Theorem: under a Pauli-Z-basis (bit-flip-only) backdrop the diagonal
    # and off-diagonal sectors never mix, so the phi-marked window-flip
    # coherences can never reach a diagonal readout functional -- every
    # repeats=1 context (any rounds, any prep) is exactly phi-blind. This
    # isolates the multi-round finding below to the COHERENT backdrop
    # component x unchecked-seam interaction.
    flip = bit_flip(BACKDROP_FLIP_RATE)
    edge = zz_coupling_kraus(PHI_TOP)
    seam = TOY.seam_pair
    stoch_base = SeamNoiseProcess(
        name="stoch-backdrop", channel_field=lambda t, i: flip, edge_field=None
    )
    stoch_coh = SeamNoiseProcess(
        name="stoch-coherent",
        channel_field=lambda t, i: flip,
        edge_field=lambda t, e: edge if tuple(e) == seam else None,
    )
    contexts = [
        TOY.calibration_contexts(0)[0],  # r0:R2-L0 (multi-round, memory)
        TOY.memory_eval_context(),  # eval:R4-L0
        TOY.exotic_eval_contexts()[0],  # exotic:R4-ry (repeats=1, ry prep)
    ]
    for ctx in contexts:
        fa = TOY.oracle_law(ctx, stoch_coh)
        fb = TOY.oracle_law(ctx, stoch_base)
        tv = _tv(fa, fb)
        assert tv <= 1e-10, f"{ctx.label}: stochastic-backdrop blindness violated (TV={tv:.3e})"


def test_repeats1_multiround_seam_coherence_measurement(law) -> None:
    """REGISTERED-EXPECTATION MEASUREMENT (registration discrepancy -- see the
    module docstring): amendment ruling 4 expects ALL repeats=1 contexts
    phi-blind at <= 1e-10; the disjoint-geometry derivation predicts a nonzero
    multi-round oracle gap (the EMERGENT across-seam H2-T1 mass of item 7,
    visible on the oracle itself). Measured and reported here; asserted only
    against the (c) build-sanity ceiling, never banded. T2' phi-parity (a
    surviving theorem) is pinned alongside for the pre_rotation=0 contexts.
    If every gap below lands <= 1e-10, the derivation is falsified and the
    registered blanket assert must be restored (registrar decision)."""
    contexts = [c for c in TOY.calibration_contexts(4) if c.repeats == 1 and c.rounds > 1]
    contexts += [TOY.memory_eval_context(), TOY.exotic_eval_contexts()[0]]  # R4-L0, R4-ry
    assert len(contexts) == 7  # + the 3 rounds=1 contexts = the registered 10
    print("\n--- repeats=1 multi-round oracle phi-gap (disjoint geometry) ---")
    for ctx in contexts:
        base = law(BACKDROP, ctx)
        tv_coh = _tv(law(COH[PHI_TOP], ctx), base)
        tv_tw = _tv(law(TWIRL[PHI_TOP], ctx), base)
        kl_coh = _branch_kl(law(COH[PHI_TOP], ctx), base)
        print(
            f"{ctx.label:>16}: TV(coh,base)={tv_coh:.3e} KL(coh,base)={kl_coh:.3e} "
            f"TV(twirl,base)={tv_tw:.3e}"
        )
        # (c) build-sanity ceiling only -- the magnitude is a finding, not a pin
        # (AMENDMENT 2 ruling 13: ceiling 1e-1 = catastrophe tripwire; measured
        # worst case 1.83e-2 at the (2,2) toy regime-top k2ry, recorded in the
        # amendment -- never a band)
        assert 0.0 <= tv_coh <= 1e-1 and 0.0 <= tv_tw <= 1e-1, ctx.label
        if ctx.pre_rotation == 0.0:
            # (a) T2': the law is exactly even in phi for pre_rotation=0, so
            # any nonzero gap above must be even-order in phi
            tv_parity = _tv(law(COH[PHI_TOP], ctx), law(COH[-PHI_TOP], ctx))
            assert tv_parity <= 1e-10, f"{ctx.label}: T2' phi-parity violated ({tv_parity:.3e})"


# --------------------------------------------------------------------------- #
# P-b shape at toy size: twirled control vs the coherent edge                   #
# --------------------------------------------------------------------------- #
def test_twirled_control_vs_coherent(law) -> None:
    phi = SEAM_PHI_REF

    # (a) the twirl is exactly even in phi: identical CHANNEL at +/- phi
    for ctx in (SANDWICH, K2RY):
        tv = _tv(law(TWIRL[phi], ctx), law(TWIRL[-phi], ctx))
        assert tv <= NUMERICAL_ZERO, f"{ctx.label}: twirl phi-sign sensitivity ({tv:.3e})"

    # (a) T2' transfer: every pre_rotation=0 context is exactly even in phi for
    # the COHERENT edge (the (prod Z) o K anti-unitary maps phi -> -phi; the
    # proof is independent of which parity pairs are measured, so it holds
    # verbatim under the disjoint extraction)
    tv_even = _tv(law(COH[phi], SANDWICH), law(COH[-phi], SANDWICH))
    assert tv_even <= 1e-10, f"sandwich phi-parity violated ({tv_even:.3e})"

    # (c) guards: the registered phi-sensitive functionals are non-degenerate.
    # k2ry opens the SIGNED sector for the coherent edge only ...
    tv_sign = _tv(law(COH[phi], K2RY), law(COH[-phi], K2RY))
    assert tv_sign > 1e-8, f"k2ry signed sector degenerate ({tv_sign:.3e})"
    # ... where coherent and twirl differ (the phi-linear vs rate-only fork)
    tv_fork = _tv(law(COH[phi], K2RY), law(TWIRL[phi], K2RY))
    assert tv_fork > 1e-8, f"coherent-vs-twirl fork degenerate at k2ry ({tv_fork:.3e})"
    # the sandwich carries the (even) seam channel for both arms: rate visible
    tv_rate = _tv(law(TWIRL[phi], SANDWICH), law(BACKDROP, SANDWICH))
    assert tv_rate > 1e-9, f"twirl sin^2(phi) rate invisible at sandwich ({tv_rate:.3e})"
    tv_coh = _tv(law(COH[phi], SANDWICH), law(BACKDROP, SANDWICH))
    assert tv_coh > 1e-9, f"coherent phi^2 sandwich channel dead ({tv_coh:.3e})"


def test_bias_injection_variant_construction(law) -> None:
    delta = 0.02
    bias = bias_injected_coherent_teacher(TOY, delta=delta)
    ref = coherent_seam_teacher(TOY, phi=SEAM_PHI_REF + delta)
    # declared injection recorded (evaluator-side ground truth for item 35)
    assert bias.params["delta"] == delta
    assert bias.params["phi"] == SEAM_PHI_REF
    assert bias.params["phi_injected"] == SEAM_PHI_REF + delta
    # construction identity: the bias arm IS the coherent teacher at phi + delta
    for ctx in (TOY.calibration_contexts(0)[0], K2RY):
        assert torch.equal(TOY.oracle_law(ctx, bias).probs, law(ref, ctx).probs)


def test_bunching_vs_ablation_record_visibility(law) -> None:
    # the bunching DOF lives in the record law: at matched stationary flip rate
    # the T-B (R=5) and T-A (R=1) arms must produce different multi-round joints.
    # The TV > 1e-6 floor is a (c)-class visibility guard (declared in the
    # module-docstring (c) list per reviewer section E), not a registered band.
    ctx = next(c for c in TOY.calibration_contexts(1) if c.rounds == 3 and c.logical == 0)
    fa, fb = law(BUNCH, ctx), law(ABLATE, ctx)
    assert abs(float(fa.total_probability()) - 1.0) <= 1e-9
    assert abs(float(fb.total_probability()) - 1.0) <= 1e-9
    assert _tv(fa, fb) > 1e-6


# --------------------------------------------------------------------------- #
# Record-layout contract: the oracle's records feed S2's splitter EXACTLY       #
# --------------------------------------------------------------------------- #
def test_record_layout_matches_carrier_splitter() -> None:
    """The amendment's layout cross-check: a (3, 3) toy strip record must split
    cleanly through the carrier's OWN ``split_strip_record`` with no seam-check
    column, and the grouped family must reconcile with the composed carrier's
    zero-seam law (S2's structural pin, replicated from the instrument side)."""
    strip = SeamStrip(3, 3)  # layout toy: D = 6, 10 instrument qubits
    spec = StripSpec(3, 3)
    ctx = next(c for c in strip.calibration_contexts(1) if c.rounds == 1 and c.logical == 0)

    # edge ON: the layout contract must hold on the coupled-oracle path too
    seam_law = strip.oracle_law(ctx, coherent_seam_teacher(strip))
    rec, probs = seam_law.measurement_record, seam_law.probs
    # K = rounds*(D-2) + D: per round (3-1) + (3-1) = 4 check columns -- there
    # is NO column for the seam pair (2, 3)
    assert rec.shape[1] == 1 * 4 + 6
    out_a, out_b = split_strip_record(rec, spec, 1)
    wa, wb = seam_law.window_records()
    assert torch.equal(out_a, wa) and torch.equal(out_b, wb)
    assert out_a.shape[1] == 1 * 2 + 3 and out_b.shape[1] == 1 * 2 + 3

    # column semantics at rounds=1 (nothing happens between extraction and the
    # final data readout, so each recorded check equals its data parity on
    # every positive-mass branch); column order: window A checks then window B
    mask = probs > NUMERICAL_ZERO  # (c) positive-mass floor
    data0 = 4  # rounds * (D - 2)
    for col, (i, j) in enumerate([(0, 1), (1, 2), (3, 4), (4, 5)]):
        parity = (rec[mask, data0 + i] + rec[mask, data0 + j]) % 2
        assert torch.equal(rec[mask, col], parity), f"column {col} is not check ({i},{j})"
    # the seam parity (data 2 (+) data 3) is pinned by NO column: both values
    # occur with positive mass
    seam_parity = (rec[mask, data0 + 2] + rec[mask, data0 + 3]) % 2
    assert float(seam_parity.min()) == 0.0 and float(seam_parity.max()) == 1.0

    # family grouping: the carrier's own helper consumes the record directly
    obs = strip_observations_from_records(rec, probs, spec, ctx)
    assert abs(float(obs.probs.sum()) - 1.0) <= 1e-9
    obs2 = seam_law.observations()
    assert torch.equal(obs.codes_left, obs2.codes_left)
    assert torch.equal(obs.codes_right, obs2.codes_right)
    assert torch.equal(obs.probs, obs2.probs)
    # per-window codes are valid rep-code (s, m) codes: < 2**(detectors + 1)
    codes_a = window_joint_codes(out_a, 3, 1)
    assert int(codes_a.max()) < 2 ** ((1 + 1) * 2 + 1)

    # zero-seam reconciliation: backdrop-only instrument law == the composed
    # carrier law (product of window-exact forwards, no seam slot) -- S2's
    # zero-seam exactness pin scored on the INSTRUMENT's observations
    base_law = strip.oracle_law(ctx, backdrop_teacher(strip))
    kraus = backdrop_kraus()
    composed = composed_strip_law(
        spec,
        ctx,
        left_field=lambda t, i: kraus,
        right_field=lambda t, i: kraus,
        seam_kraus=None,
    )
    pin = zero_seam_exactness_pin(composed, base_law.observations(), tol=1e-10)
    assert pin["ok"], f"instrument-vs-carrier zero-seam reconciliation failed: {pin}"


# --------------------------------------------------------------------------- #
# Report (run with -s; numbers feed the S1 build report)                        #
# --------------------------------------------------------------------------- #
def test_s1_report(law) -> None:
    prod = production_strip()
    print("\n=== ADR 0008 seam-test S1 build, post-amendment (disjoint geometry) ===")
    print(f"tiling family: {TILING_FAMILY} (== carrier StripSpec.tiling)")
    print(
        f"prod windows {prod.window_a} | {prod.window_b}  seam={prod.seam_pair} "
        f"(unchecked)  D={prod.distance}  qubits={prod.total_qubits} (2D-2)"
    )
    print(
        f"toy  windows {TOY.window_a} | {TOY.window_b}  seam={TOY.seam_pair} "
        f"(unchecked)  D={TOY.distance}  qubits={TOY.total_qubits}"
    )
    stats = tb_record_chain_stats(TB_P01, TB_P10)
    print(
        f"T-B member (p01={TB_P01}, p10={TB_P10}): r={stats['r']:.6e} "
        f"R={stats['R']:.6f} lambda1={stats['lambda1']:.7f} T3={stats['T3']:.6f}"
    )
    phi = SEAM_PHI_REF
    rows = {
        "TV(coh+ , coh-)  @ sandwich": _tv(law(COH[phi], SANDWICH), law(COH[-phi], SANDWICH)),
        "TV(coh+ , coh-)  @ k2ry    ": _tv(law(COH[phi], K2RY), law(COH[-phi], K2RY)),
        "TV(coh  , twirl) @ k2ry    ": _tv(law(COH[phi], K2RY), law(TWIRL[phi], K2RY)),
        "TV(twirl, base)  @ sandwich": _tv(law(TWIRL[phi], SANDWICH), law(BACKDROP, SANDWICH)),
        "TV(coh  , base)  @ sandwich": _tv(law(COH[phi], SANDWICH), law(BACKDROP, SANDWICH)),
        "TV(coh  , base)  @ R4-L0   ": _tv(
            law(COH[PHI_TOP], TOY.memory_eval_context()), law(BACKDROP, TOY.memory_eval_context())
        ),
        "TV(coh  , base)  @ R4-ry   ": _tv(
            law(COH[PHI_TOP], TOY.exotic_eval_contexts()[0]),
            law(BACKDROP, TOY.exotic_eval_contexts()[0]),
        ),
    }
    for name, value in rows.items():
        print(f"{name}: {value:.6e}")
    assert math.isfinite(sum(rows.values()))


# --------------------------------------------------------------------------- #
# FIX ROUND 2 / R2-1 (build_R2_seam_postfix_review.md section B, verdict 1):   #
# the memory-bounded production oracle evaluator -- (a) equivalence pins       #
# --------------------------------------------------------------------------- #
def _assert_grouped_equals_monolithic(strip, ctx, teacher, cap, mono=None):
    """(a)-class equivalence pin: the chunked evaluator computes the IDENTICAL
    law. Bit-exactness is demanded (and achievable) because the record ->
    code-pair map is a GF(2) bijection: every grid cell receives exactly ONE
    enumeration leaf, so no float64 re-association exists anywhere on the
    joint-law path -- torch.equal, not a tolerance."""
    if mono is None:
        mono = strip.oracle_law(ctx, teacher, evaluator="monolithic")
    grp = strip.oracle_law(ctx, teacher, evaluator="grouped", live_branch_cap=cap)
    assert grp.grouped and grp.measurement_record is None
    assert not mono.grouped
    obs_m, obs_g = mono.observations(), grp.observations()
    assert torch.equal(obs_g.codes_left, obs_m.codes_left)
    assert torch.equal(obs_g.codes_right, obs_m.codes_right)
    assert torch.equal(obs_g.probs, obs_m.probs)  # the joint law, BIT-EXACT
    # (a) structural: total mass through the chunked accumulation
    assert abs(float(grp.total_probability()) - 1.0) <= 1e-12
    # window-record marginal laws: the shared lexicographic-grid path is
    # bit-exact across modes (the same op sequence on bit-equal observations)
    gl, gr = grp.window_marginal_laws()
    ml, mr = mono.window_marginal_laws()
    assert torch.equal(gl, ml) and torch.equal(gr, mr)
    return mono, grp


def test_grouped_oracle_bit_exact_toy22(law) -> None:
    ctx_r0 = TOY.calibration_contexts(0)[0]  # r0:R2-L0
    ctx_r3l1 = next(
        c for c in TOY.calibration_contexts(1) if c.rounds == 3 and c.logical == 1
    )
    contexts = [ctx_r0, ctx_r3l1, SANDWICH, K2RY, TOY.memory_eval_context()]
    arms = [BACKDROP, COH[PHI_TOP], TWIRL[PHI_TOP], BUNCH, ABLATE]
    # cap 4 = 2**(D-2) is the minimal admissible cap -> the deepest chunk tree;
    # cap 32 mixes straight-through and split paths
    for cap in (4, 32):
        for arm in arms:  # all six-surface arms x two multi-round contexts
            _assert_grouped_equals_monolithic(
                TOY, ctx_r3l1, arm, cap, mono=law(arm, ctx_r3l1)
            )
            _assert_grouped_equals_monolithic(
                TOY, SANDWICH, arm, cap, mono=law(arm, SANDWICH)
            )
        for ctx in contexts:  # full context sweep on the coherent arm
            _assert_grouped_equals_monolithic(
                TOY, ctx, COH[PHI_TOP], cap, mono=law(COH[PHI_TOP], ctx)
            )

    # Splitter-route cross-check on the WINDOW marginals: grouping the
    # monolithic per-branch records via the carrier's own splitter sums the
    # SAME per-cell multiset in branch order instead of lexicographic cell
    # order -- a pure float64 re-association. Derived bound (the documented
    # R2-1 allowance; the JOINT law above carries no allowance at all):
    # per cell |delta| <= (n_terms - 1) * u * cell_mass, n_terms = 2**bits_other
    # = 2**6 here, u = 2**-53 => <= 63 * 1.11e-16 = 7.0e-15 < 1e-14.
    mono, grp = _assert_grouped_equals_monolithic(
        TOY, SANDWICH, COH[PHI_TOP], 4, mono=law(COH[PHI_TOP], SANDWICH)
    )
    out_a, out_b = mono.window_records()
    bits_l, bits_r = mono.code_bits
    marg = grp.window_marginal_laws()
    for out_w, d_w, bits, lex in (
        (out_a, TOY.window_a_size, bits_l, marg[0]),
        (out_b, TOY.window_b_size, bits_r, marg[1]),
    ):
        codes = window_joint_codes(out_w, d_w, mono.rounds)
        dense = torch.zeros(1 << bits, dtype=mono.probs.dtype)
        dense.scatter_add_(0, codes, mono.probs)
        assert float((dense - lex).abs().max()) <= 1e-14


def test_grouped_oracle_bit_exact_toy33_rounds1_and_asymmetric() -> None:
    # (3, 3) layout toy at rounds=1: bigger windows/register through identity
    # (a1) -- at rounds=1 the WHOLE law is one noise layer + one diagonal
    # readout (no doubling round exists), the strongest use of the identity
    strip33 = SeamStrip(3, 3)
    ctx1 = next(
        c for c in strip33.calibration_contexts(1) if c.rounds == 1 and c.logical == 0
    )
    for arm in (backdrop_teacher(strip33), coherent_seam_teacher(strip33, phi=PHI_TOP)):
        _assert_grouped_equals_monolithic(strip33, ctx1, arm, 16)
    # asymmetric strip (2, 3) at rounds=2: asymmetric splitter columns through
    # the grouped finalize, at the minimal admissible cap 2**c = 8
    strip23 = SeamStrip(2, 3)
    ctx2 = strip23.calibration_contexts(0)[0]  # r0:R2-L0
    _assert_grouped_equals_monolithic(
        strip23, ctx2, coherent_seam_teacher(strip23, phi=PHI_TOP), 8
    )


def test_grouped_oracle_routing_guards_and_production_geometry() -> None:
    prod = production_strip()
    ctx_r1 = next(
        c for c in prod.calibration_contexts(1) if c.rounds == 1 and c.logical == 0
    )
    ctx_r2 = prod.calibration_contexts(0)[0]  # r0:R2-L0

    # "auto" routing ((c) threshold): every toy-suite law stays monolithic
    # (records present -- the 16 pre-fix tests run unchanged); EVERY
    # production-geometry context routes to the memory-bounded evaluator
    assert oracle_memory_probe(TOY_WINDOW_SIZES, 4)["evaluator"] == "monolithic"
    assert oracle_memory_probe((3, 3), 1)["evaluator"] == "monolithic"
    for r in (1, 2, 3, 4):
        assert oracle_memory_probe(PRODUCTION_WINDOW_SIZES, r)["evaluator"] == "grouped"
    toy_law = TOY.oracle_law(TOY.calibration_contexts(0)[0], BACKDROP)
    assert not toy_law.grouped and toy_law.measurement_record is not None

    base = prod.oracle_law(ctx_r1, backdrop_teacher(prod))
    assert base.grouped and base.measurement_record is None
    assert base.probs.numel() == 2 ** 12  # K = 1*(D-2) + D = 12
    assert abs(float(base.total_probability()) - 1.0) <= 1e-12

    # the rounds=1 repeats=1 phi-blindness theorem (AMENDMENT 2 ruling 11(i))
    # re-pinned AT PRODUCTION GEOMETRY through the production evaluator
    # (grouped laws are cell-aligned: the cell space is teacher-independent)
    coh = prod.oracle_law(ctx_r1, coherent_seam_teacher(prod, phi=PHI_TOP))
    tw = prod.oracle_law(ctx_r1, twirled_seam_teacher(prod, phi=PHI_TOP))
    assert 0.5 * float((coh.probs - base.probs).abs().sum()) <= 1e-10
    assert 0.5 * float((tw.probs - base.probs).abs().sum()) <= 1e-10

    # multi-round production-geometry smoke (rounds=2 -- the first context the
    # as-coded oracle OOMed on at 34 GB): bounded memory, exact mass
    multi = prod.oracle_law(ctx_r2, coherent_seam_teacher(prod, phi=PHI_TOP))
    assert multi.grouped and multi.probs.numel() == 2 ** 17
    assert abs(float(multi.total_probability()) - 1.0) <= 1e-12

    # guards: inadmissible cap, unknown evaluator, record access on grouped laws
    with pytest.raises(ValueError):
        prod.oracle_law(
            ctx_r1, backdrop_teacher(prod), evaluator="grouped", live_branch_cap=16
        )  # 16 < 2**5
    with pytest.raises(ValueError):
        TOY.oracle_law(TOY.calibration_contexts(0)[0], BACKDROP, evaluator="bogus")
    with pytest.raises(RuntimeError):
        base.window_records()


def test_oracle_memory_probe_matches_walk_and_production_envelope() -> None:
    # (a) probe <-> implementation consistency: the dry-run plan's integer
    # counters must equal the instrumented walk's measured counters EXACTLY
    # (the probe mirrors the walk's bookkeeping line for line)
    ctx_r3 = next(
        c for c in TOY.calibration_contexts(1) if c.rounds == 3 and c.logical == 0
    )
    strip23 = SeamStrip(2, 3)
    cases = [
        (TOY, ctx_r3, COH[PHI_TOP], 4),
        (TOY, SANDWICH, BUNCH, 32),
        (strip23, strip23.calibration_contexts(0)[0], coherent_seam_teacher(strip23), 8),
    ]
    for strip, ctx, teacher, cap in cases:
        stats: dict = {}
        strip.oracle_law(
            ctx, teacher, evaluator="grouped", live_branch_cap=cap, memory_stats=stats
        )
        probe = oracle_memory_probe(
            (strip.window_a_size, strip.window_b_size), ctx.rounds, live_branch_cap=cap
        )
        for key in (
            "peak_resident_branches",
            "peak_transient_branches",
            "leaf_chunks",
            "leaf_branches",
            "max_leaf_chunk_branches",
        ):
            assert probe[key] == stats[key], key
        # the cap never truncates: every branch entering the last round visited
        assert probe["leaf_branches"] == 2 ** (
            probe["checks_per_round"] * (int(ctx.rounds) - 1)
        )

    # production memory table ((c) envelope gates): the registered item-13
    # oracle live-set letter is one 13q DM = 1.07 GB (re-review E-6 reading);
    # the grouped DM working set sits under it at EVERY production context
    # with the default declared cap
    for r in (1, 2, 3, 4):
        p = oracle_memory_probe(PRODUCTION_WINDOW_SIZES, r)
        assert p["evaluator"] == "grouped"
        assert p["live_branch_cap"] == ORACLE_LIVE_BRANCH_CAP
        assert p["grid_bytes"] == (2 ** (5 * r + 7)) * 8
        assert p["leaf_branches"] == 2 ** (5 * (r - 1))
        assert p["dm_peak_bytes"] <= 1.1e9
    p4 = oracle_memory_probe(PRODUCTION_WINDOW_SIZES, 4)
    assert p4["grid_bytes"] == 2 ** 30  # 1.07 GB: the R4 law object itself
    assert p4["est_peak_bytes"] <= 2.5e9  # grid-dominated total, (c) smoke bound
    # the headline infeasibility the fix removes: monolithic R4 = 35 TB
    assert p4["monolithic_final_bytes"] == 2 ** 45
    assert MONOLITHIC_ORACLE_MAX_BYTES < p4["monolithic_final_bytes"]
    with pytest.raises(ValueError):
        oracle_memory_probe(PRODUCTION_WINDOW_SIZES, 2, live_branch_cap=16)
