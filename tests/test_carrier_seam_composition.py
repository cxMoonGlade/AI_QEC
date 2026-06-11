"""ADR 0008 C3 seam test -- the composed-carrier arm's build pins (S2 scope).

Covers the carrier-facing slice of the frozen seam-test pre-registration
(docs/metric_results.md "ADR 0008 SEAM-TEST PRE-REGISTRATION", items 3, 5, 6, 7
carrier side): the declared seam composition rule
(``forward/scalable/composed.py`` docstring -- conditional-product, synchronous
mean-field at the declared per-round extraction boundaries), its structural
pins, the fit-free two-block-marginal bunching functionals, the channel-level
do() pushforward pin, the W2-gate-before-fit hook, and a TOY SMOKE FIT.

Scope discipline: everything here is toy-scale (windows d=2..3, <= 6 strip
qubits) and controlled. The K1 measurement (P-c seam residual scaling), the
swap-gate triplet under the frozen decoder, and every production fit are
REVIEWER-GATED runs wired by S3 -- this file builds and pins the machinery
only. The whole-strip oracle below is the evaluator-side stand-in for the S1
``SeamStrip`` instrument (same declared record layout, ``forward/exact``
primitives only); no S1 module is imported, so this file runs standalone.

Pin classes (registration item 7): every assertion here is STRUCTURAL
(numerical floor; violation = build bug). Emergent quantities (the seam
residual) are only checked for machinery liveness, never banded here.
"""

from __future__ import annotations

import math

import pytest
import torch

from qec_twin.forward.cptp_channel import CDTYPE, RDTYPE, tp_residual
from qec_twin.forward.exact.circuit_sim import (
    amplitude_damping,
    apply_channel_local,
    apply_unitary,
    bit_flip,
    measure_parity_enumerate,
    measure_qubit_enumerate,
    pauli_x,
    ry,
    zero_state,
)
from qec_twin.forward.scalable import (
    CarrierErrorAccounting,
    ComposedCarrier,
    StripContext,
    StripSpec,
    composed_strip_law,
    fit_composed_carrier,
    fixed_point_pin,
    nonpositive_pin,
    normalization_pin,
    pauli_ablation_pin,
    r_det_lag,
    seam_conditional_reduction,
    seam_reduction_tp_pin,
    strip_joint_kl,
    strip_law_total_variation,
    strip_observations_from_records,
    t3_triple,
    unital_diagonal_pin,
    zero_seam_exactness_pin,
)
from qec_twin.knobs.intervention import do_remove
from qec_twin.mechanisms.teachers import (
    coherent_overrotation_kraus,
    correlated_dephasing_kraus,
    zz_coupling_kraus,
)

SPEC = StripSpec(2, 2)  # 4-qubit strip: the fast structural-pin instrument
PHI = 0.12  # inside the registered seam regime [0.05, 0.15] (item 2)
HALF_PI = math.pi / 2


# --------------------------------------------------------------------------- #
# Evaluator-side whole-strip oracle (forward/exact primitives; the S1 stub).    #
# Declared record layout = composed.split_strip_record's (module docstring).    #
# --------------------------------------------------------------------------- #
def _oracle_strip(spec, context, *, left_field, right_field, seam_kraus=None, device="cpu"):
    n_l, n_r = spec.d_left, spec.d_right
    n = n_l + n_r
    rho = zero_state(n, device=device).unsqueeze(0)
    out = torch.zeros((1, 0), dtype=RDTYPE, device=device)
    if int(context.logical):
        for q in range(n):
            rho = apply_unitary(rho, pauli_x(device), [q], n)
    if float(context.pre_rotation):
        gate = ry(context.pre_rotation)
        for q in range(n):
            rho = apply_unitary(rho, gate, [q], n)
    for t in range(int(context.rounds)):
        for _ in range(int(context.repeats)):
            for i in range(n_l):
                kraus = left_field(t, i)
                if kraus is not None:
                    rho = apply_channel_local(rho, kraus, [i], n)
            for i in range(n_r):
                kraus = right_field(t, i)
                if kraus is not None:
                    rho = apply_channel_local(rho, kraus, [n_l + i], n)
            if seam_kraus is not None:
                rho = apply_channel_local(rho, seam_kraus, [n_l - 1, n_l], n)
        for j in range(n_l - 1):
            rho, out = measure_parity_enumerate(rho, out, j, j + 1, n)
        for j in range(n_r - 1):
            rho, out = measure_parity_enumerate(rho, out, n_l + j, n_l + j + 1, n)
    for i in range(n):
        rho, out = measure_qubit_enumerate(rho, out, i, n, reset=False)
    probs = torch.diagonal(rho, dim1=-2, dim2=-1).real.sum(-1)
    return strip_observations_from_records(out, probs, spec, context)


def _backdrop_fields():
    """Heterogeneous local backdrop incl. coherent + non-unital mechanisms."""
    left = [bit_flip(0.03), coherent_overrotation_kraus(0.04, 0.5)]
    right = [amplitude_damping(0.05), coherent_overrotation_kraus(0.02, 0.3)]
    return (lambda t, i: left[i]), (lambda t, i: right[i])


def _carrier_with_stacks(spec, stacks_left, stacks_right, *, seam_phi_init=None, seed=3):
    """Evaluator-side carrier carrying declared Kraus stacks at every location
    (channel-level replacement via the do() path -- machinery tests only)."""
    carrier = ComposedCarrier.random(spec, seed=seed, seam_phi_init=seam_phi_init)
    for i, stack in enumerate(stacks_left):
        carrier = carrier.do_on_location("L", i, lambda _k, _s=stack: _s)
    for i, stack in enumerate(stacks_right):
        carrier = carrier.do_on_location("R", i, lambda _k, _s=stack: _s)
    return carrier


def _tb_kraus(p01: float, p10: float) -> torch.Tensor:
    """D5's explicit T-B member: K0 = diag(sqrt(1-p01), sqrt(1-p10)),
    K1 = sqrt(p01)|1><0|, K2 = sqrt(p10)|0><1|."""
    k0 = torch.diag(torch.tensor([math.sqrt(1 - p01), math.sqrt(1 - p10)], dtype=RDTYPE)).to(CDTYPE)
    k1 = torch.zeros((2, 2), dtype=CDTYPE)
    k1[1, 0] = math.sqrt(p01)
    k2 = torch.zeros((2, 2), dtype=CDTYPE)
    k2[0, 1] = math.sqrt(p10)
    return torch.stack([k0, k1, k2])


# --------------------------------------------------------------------------- #
# 1. THE LOAD-BEARING PIN: zero seam mass => composed law == whole-strip oracle #
# --------------------------------------------------------------------------- #
def test_zero_seam_exactness_pin() -> None:
    """STRUCTURAL <= 1e-10: composition exact when there is nothing to
    approximate (registration items 3/7; P-a's machinery base)."""
    left_field, right_field = _backdrop_fields()
    contexts = [
        StripContext(rounds=2, label="R2-L0"),
        StripContext(rounds=2, repeats=2, pre_rotation=HALF_PI, label="R2-k2ry"),
        StripContext(rounds=3, logical=1, label="R3-L1"),
    ]
    for ctx in contexts:
        law = composed_strip_law(SPEC, ctx, left_field=left_field, right_field=right_field, seam_kraus=None)
        oracle = _oracle_strip(SPEC, ctx, left_field=left_field, right_field=right_field, seam_kraus=None)
        assert abs(float(oracle.probs.sum()) - 1.0) <= 1e-12  # oracle stub sanity
        pin = zero_seam_exactness_pin(law, oracle, tol=1e-10)
        assert pin["ok"], f"{ctx.label}: zero-seam exactness violated (max_abs={pin['max_abs']:.3e}, tv={pin['tv']:.3e})"


# --------------------------------------------------------------------------- #
# 2. Normalization / zero-negative-mass / fixed-point structural pins           #
# --------------------------------------------------------------------------- #
def test_normalization_and_nonpositive_pins() -> None:
    left_field, right_field = _backdrop_fields()
    ctx = StripContext(rounds=2, repeats=2, pre_rotation=HALF_PI, label="R2-k2ry")
    seam = zz_coupling_kraus(PHI)
    law = composed_strip_law(SPEC, ctx, left_field=left_field, right_field=right_field, seam_kraus=seam)
    norm = normalization_pin(law, tol=1e-12)
    assert norm["ok"], f"normalization defect: {norm}"
    neg = nonpositive_pin(law, tol=1e-12)
    assert neg["ok"], f"negative probability mass: {neg}"


def test_fixed_point_pin() -> None:
    field = lambda t, i: bit_flip(0.04)  # noqa: E731
    pin = fixed_point_pin(field, distance=2, tol=1e-9)
    assert pin["ok"], f"fixed-point residual {pin['residual']:.3e} > 1e-9"


# --------------------------------------------------------------------------- #
# 3. The composition rule's CPTP kernel is trace preserving                     #
# --------------------------------------------------------------------------- #
def test_seam_reduction_tp_pin() -> None:
    gen = torch.Generator().manual_seed(7)
    a = torch.randn(2, 2, generator=gen, dtype=RDTYPE) + 1j * torch.randn(2, 2, generator=gen, dtype=RDTYPE)
    sigma_mixed = a @ a.conj().T
    sigma_mixed = sigma_mixed / sigma_mixed.trace().real
    sigma_pure = torch.zeros((2, 2), dtype=CDTYPE)
    sigma_pure[0, 0] = 1.0  # the det=0 boundary case
    for seam in (zz_coupling_kraus(0.3), correlated_dephasing_kraus(0.2)):
        for sigma in (sigma_mixed.to(CDTYPE), sigma_pure):
            pin = seam_reduction_tp_pin(seam, sigma, tol=1e-12)
            assert pin["ok"], f"seam reduction not TP: {pin}"
    # identity seam stack reduces to the exact identity map on any partner state
    eye4 = torch.eye(4, dtype=CDTYPE).unsqueeze(0)
    reduced = seam_conditional_reduction(eye4, sigma_mixed.to(CDTYPE), side="left")
    rho = torch.tensor([[0.7, 0.2 - 0.1j], [0.2 + 0.1j, 0.3]], dtype=CDTYPE)
    out = sum(k @ rho @ k.conj().T for k in reduced)
    assert float((out - rho).abs().max()) <= 1e-12
    assert float(tp_residual(reduced)) <= 1e-12


# --------------------------------------------------------------------------- #
# 4. R_det / T3 from the two-block marginal: exact on a synthetic T-B law       #
# --------------------------------------------------------------------------- #
def test_r_det_matches_tb_analytics() -> None:
    """Registration item 6 machinery: R_k = 1 + (R-1) lambda1^(k-1) and T3 = R,
    both EXACT identities of the T-B member -- no fit anywhere."""
    p01, p10 = 6.7039e-3, 1.20296e-1  # the registered R=5 member at r = 1.27e-2
    tb = _tb_kraus(p01, p10)
    field = lambda t, i: tb if i == 0 else None  # noqa: E731
    r_true = 2 * p01 * p10 / (p01 + p10)
    big_r = (p01 + p10) ** 2 / (4 * p01 * p10)
    lambda1 = 1.0 - p01 - p10
    for lag in (1, 2, 3, 4):
        out = r_det_lag(field, distance=2, check=0, lag=lag)
        expected = 1.0 + (big_r - 1.0) * lambda1 ** (lag - 1)
        assert abs(out["R_k"] - expected) <= 1e-9, f"lag {lag}: {out['R_k']} vs {expected}"
        assert abs(out["flip_rate"] - r_true) <= 1e-12
        assert out["record"] == "data-record-chain"  # the declared convention travels
    triple = t3_triple(field, distance=2, check=0)
    assert abs(triple["T3"] - big_r) <= 1e-9  # T-B: T3 = R exactly


# --------------------------------------------------------------------------- #
# 5. T-A Pauli-ablation and unital-diagonal pins: R_k pinned at 1               #
# --------------------------------------------------------------------------- #
def test_pauli_ablation_pin_r1() -> None:
    p01, p10 = 6.7039e-3, 1.20296e-1
    tb = _tb_kraus(p01, p10)
    field = lambda t, i: tb if i == 0 else None  # noqa: E731
    pin = pauli_ablation_pin(field, distance=2, check=0, lags=(1, 2, 3), tol=1e-9)
    assert pin["ok"], f"Pauli ablation must pin R_k == 1: {pin}"


def test_unital_diagonal_pin_r1() -> None:
    field = lambda t, i: bit_flip(0.04)  # noqa: E731
    pin = unital_diagonal_pin(field, distance=2, check=0, lags=(1, 2, 3), tol=1e-9)
    assert pin["in_scope"] and pin["ok"], f"unital-diagonal field must pin R_k == 1: {pin}"


# --------------------------------------------------------------------------- #
# 6. Channel-level do() with the strip pushforward pinned (registration item 5) #
# --------------------------------------------------------------------------- #
def test_do_pushforward_reproduces_ablated_oracle() -> None:
    left_field, right_field = _backdrop_fields()
    stacks_l = [left_field(0, i) for i in range(SPEC.d_left)]
    stacks_r = [right_field(0, i) for i in range(SPEC.d_right)]
    ctx = StripContext(rounds=2, repeats=2, pre_rotation=HALF_PI, label="R2-k2ry")

    carrier_phi = _carrier_with_stacks(SPEC, stacks_l, stacks_r, seam_phi_init=PHI)
    law_phi = carrier_phi.strip_law(ctx)
    # liveness: the seam slot is observable on the phi-sensitive sandwich probe
    law_none = composed_strip_law(SPEC, ctx, left_field=left_field, right_field=right_field, seam_kraus=None)
    live_gap = strip_law_total_variation(law_phi, strip_observations_from_law(law_none, ctx))

    # do(E_seam -> I4): channel-level, parameterization-independent
    carrier_do = carrier_phi.do_on_seam(do_remove)
    law_do = carrier_do.strip_law(ctx)
    gap_vs_none = strip_law_total_variation(law_do, strip_observations_from_law(law_none, ctx))
    assert gap_vs_none["max_abs"] <= 1e-12, f"do(seam->I) != seam-free carrier: {gap_vs_none}"
    assert live_gap["tv"] > 1e-6, "seam slot dead on the sandwich probe -- do() test vacuous"

    # the pinned pushforward: do(U_phi -> I) reproduces the seam-ABLATED oracle
    oracle_ablated = _oracle_strip(SPEC, ctx, left_field=left_field, right_field=right_field, seam_kraus=None)
    pin = zero_seam_exactness_pin(law_do, oracle_ablated, tol=1e-10)
    assert pin["ok"], f"do() pushforward violated: {pin}"

    # parameterization independence: the SAME transform from a different
    # parameter point yields the identical post-do() law
    carrier_phi2 = _carrier_with_stacks(SPEC, stacks_l, stacks_r, seam_phi_init=0.4)
    law_do2 = carrier_phi2.do_on_seam(do_remove).strip_law(ctx)
    gap = strip_law_total_variation(law_do2, strip_observations_from_law(law_do, ctx))
    assert gap["max_abs"] <= 1e-12, f"do() depends on parameterization: {gap}"

    # location do(): same discipline on a location slot
    carrier_loc = carrier_phi.do_on_location("L", 0, do_remove)
    eye = torch.eye(2, dtype=CDTYPE).unsqueeze(0)
    ref_left = lambda t, i: eye if i == 0 else stacks_l[i]  # noqa: E731
    law_ref = composed_strip_law(
        SPEC, ctx, left_field=ref_left, right_field=right_field, seam_kraus=zz_coupling_kraus(PHI)
    )
    gap_loc = strip_law_total_variation(carrier_loc.strip_law(ctx), strip_observations_from_law(law_ref, ctx))
    assert gap_loc["max_abs"] <= 1e-12, f"location do() pushforward violated: {gap_loc}"


def strip_observations_from_law(law, ctx):
    """Test helper: view a StripLaw's full product grid as a StripObservations
    (for law-vs-law TV via the same exact comparator)."""
    from qec_twin.forward.scalable import StripObservations

    grid = law.full_joint()
    codes_l = law.left.codes.repeat_interleave(law.right.codes.numel())
    codes_r = law.right.codes.repeat(law.left.codes.numel())
    return StripObservations(context=ctx, codes_left=codes_l, codes_right=codes_r, probs=grid.reshape(-1))


# --------------------------------------------------------------------------- #
# 7. W2 gate hook before any fit + the TOY SMOKE FIT (label-free Born-NLL)      #
# --------------------------------------------------------------------------- #
def test_gate_hook_and_smoke_fit() -> None:
    """SMOKE, not production: a few-step LBFGS fit on a tiny matched teacher,
    asserting the gate-before-fit contract and a converging cross-entropy.
    Production seam-test fits are reviewer-gated (GPU, S3's run)."""
    rates_l, rates_r = [0.03, 0.05], [0.04, 0.06]
    left_field = lambda t, i: bit_flip(rates_l[i])  # noqa: E731
    right_field = lambda t, i: bit_flip(rates_r[i])  # noqa: E731
    contexts = [
        StripContext(rounds=1, label="R1-L0"),
        StripContext(rounds=2, label="R2-L0"),
        StripContext(rounds=2, logical=1, label="R2-L1"),
    ]
    observations = [
        _oracle_strip(SPEC, c, left_field=left_field, right_field=right_field, seam_kraus=None)
        for c in contexts
    ]

    carrier = ComposedCarrier.random(SPEC, num_kraus=2, seed=0)
    # the registration's order pin: NO fit before the W2/Fisher gate has run
    with pytest.raises(RuntimeError, match="gate"):
        fit_composed_carrier(observations, SPEC, carrier=carrier, steps=2)

    # stub gate record (S3 wires the real audit W2/Fisher machinery; the hook
    # and the order contract are what this test pins)
    carrier.manifest.apply_gate({"stub": "toy smoke gate -- real W2/Fisher gate wired by S3"})
    assert carrier.manifest.gated and set(carrier.manifest.active_names()) == {
        "L.loc0", "L.loc1", "R.loc0", "R.loc1",
    }

    with torch.no_grad():
        init_kl = sum(float(strip_joint_kl(o, carrier.strip_law(o.context))) for o in observations)
    result = fit_composed_carrier(observations, SPEC, carrier=carrier, steps=120)
    # SMOKE gate (deliberately loose): the matched-class CE converges toward the
    # entropy floor; precision-grade convergence is the production fit's gate.
    assert result["total_kl"] < 1e-3, f"smoke fit did not converge: KL={result['total_kl']:.3e}"
    assert result["total_kl"] < 0.1 * init_kl, f"smoke fit barely moved: {result['total_kl']:.3e} vs init {init_kl:.3e}"


# --------------------------------------------------------------------------- #
# 8. Error accounting: eps_log and B_carrier are separate books                 #
# --------------------------------------------------------------------------- #
def test_seam_residual_ledger_machinery() -> None:
    """B_carrier bookkeeping liveness (registration items 3/8): the measured
    seam residual is recorded functional-indexed, tier-3, in its OWN book;
    eps_log holds float64 round-off only. Magnitude/banding is S3's K1 scoring,
    NOT asserted here."""
    left_field, right_field = _backdrop_fields()
    ctx = StripContext(rounds=2, repeats=2, pre_rotation=HALF_PI, label="R2-k2ry")
    seam = zz_coupling_kraus(PHI)
    law = composed_strip_law(SPEC, ctx, left_field=left_field, right_field=right_field, seam_kraus=seam)
    oracle = _oracle_strip(SPEC, ctx, left_field=left_field, right_field=right_field, seam_kraus=seam)

    residual = strip_law_total_variation(law, oracle)
    acct = CarrierErrorAccounting()
    acct.record_seam_residual(
        "strip_joint_tv", ctx.label, residual["tv"],
        note=f"phi={PHI} sandwich+ry; mean-field composition residual; K1 scored by S3",
    )
    acct.record_law_round_off(law)

    assert residual["tv"] > 1e-8, "no measurable seam residual -- ledger liveness check vacuous"
    report = acct.report()
    assert set(report) == {"eps_log", "B_carrier", "convention"}
    assert report["B_carrier"][0]["functional"] == "strip_joint_tv"
    assert report["B_carrier"][0]["tier"].startswith("B_misspec")
    assert all(rec["value"] <= 1e-10 for rec in report["eps_log"])  # round-off only
    # the two books never merge: B_carrier values are NOT in the eps_log book
    assert all(rec["name"].startswith("normalization_defect") for rec in report["eps_log"])


def test_floor_hit_counters_two_books() -> None:
    """Checklist item 5 (reviewer §E, orchestrator fix round 2026-06-10):
    model-class floor hits and evaluator log-clamp hits are counted in SEPARATE
    books — reported in production scoring, never harvested, never merged."""
    from qec_twin.forward.scalable.composed import (
        StripLaw,
        StripObservations,
        WindowLaw,
        strip_cross_entropy,
    )
    from qec_twin.numerics import NUMERICAL_ZERO

    codes = torch.tensor([0, 2, 5], dtype=torch.int64)
    probs = torch.tensor([0.5, 0.3, 0.2], dtype=torch.float64)
    window = WindowLaw(codes=codes, probs=probs)

    counter: dict = {}
    out = window.lookup(torch.tensor([0, 1, 5, 7], dtype=torch.int64), counter=counter)
    assert counter["floor_hits_model_class"] == 2  # codes 1 and 7 carry no support
    assert float(out[1]) == NUMERICAL_ZERO and float(out[3]) == NUMERICAL_ZERO

    ctx = StripContext(rounds=1, label="counter-toy")
    law = StripLaw(spec=StripSpec(2, 2), context=ctx, left=window, right=window)
    obs = StripObservations(
        context=ctx,
        codes_left=torch.tensor([0, 1], dtype=torch.int64),   # 1 = unsupported left
        codes_right=torch.tensor([2, 7], dtype=torch.int64),  # 7 = unsupported right
        probs=torch.tensor([0.6, 0.4], dtype=torch.float64),
    )
    counter2: dict = {}
    ce = strip_cross_entropy(obs, law, counter=counter2)
    assert torch.isfinite(ce)
    assert counter2["floor_hits_model_class"] == 2  # one per window lookup
    # the (1,7) cell's product = floor**2 < floor => exactly one evaluator clamp
    assert counter2["evaluator_nonpositive"] == 1
    assert set(counter2) == {"floor_hits_model_class", "evaluator_nonpositive"}
