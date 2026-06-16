from __future__ import annotations

"""Executable spec for the WindowChannel step-2 build (``docs/cf_wr/window_channel_spec.md`` §6).

This file is implementer **C** of the parallel build (spec §9): it codes strictly against the
FROZEN §10 interface contract so it links cleanly against the concurrently-built siblings —
``forward/mechanisms_torch.py`` (A, the θ-parameterised CPTP dictionary), ``forward/window_diagnostics.py``
(D, the small-support PTM / coherence / Choi / partial-trace lenses), and ``forward/window_channel.py``
(B, the faithful single-round noisy-circuit object) — plus the committed stage-0 enumerator
``outputs/placement_enumerate.py`` and its sidecar.

Discipline (spec §6 + [[feedback-adversarial-self-verification]] + window_covering_RESULTS §4):
**every** self-check carries a POSITIVE CONTROL — a deliberately-broken input the check must flag. A
check that cannot distinguish "broken" from "passed" is worthless. The controls live next to each
assertion (``_assert_flags`` runs the same predicate on a corrupted input and asserts it FAILS).

The six §6 self-checks:
  1. CPTP — every mechanism + the composed window map: ``tp_residual < NUMERICAL_ZERO`` and PSD Choi
     (min eigenvalue ≥ −NUMERICAL_ZERO).  Control: a hand-built non-TP / non-CP map is flagged.
  2. Coherence representable — coherent mechanisms (rzz, …) have PTM off-diagonal mass > 0; a
     Pauli-stochastic mechanism has ~0 off-diagonal (diagonal PTM).  Control: the diagonal/off-diagonal
     roles cannot be swapped without the check noticing.
  3. Placement correctness — (a) ``build_placement`` slot counts == the committed sidecar
     (CZ=168, data-1q=196, spectator=156); (b) an embedded operator acts on exactly the intended
     qubits (permutation check).  Control: a dropped spectator edge / a wrong target index is flagged.
  4. Cross-validation oracle — each torch builder vs the same-named ``channels.py`` NumPy builder at
     the same θ: elementwise (when Kraus order matches) AND gauge-invariant (Choi distance + action on
     IC inputs) < 1e-10.  Control: a θ-perturbed torch channel is flagged as DIFFERENT.
  5. ρ_BC self-consistency — ``WindowChannel.rho_bc`` == an independent brute-force partial trace of
     ``apply(rho)``.  Control: keeping the wrong qubit is flagged.
  6. Gradient — ``WindowChannel.sensitivity`` (the exact ∂apply/∂θ carrier it returns) matches a
     central finite difference of the matching scalar functional.  Control: the analytic value scaled
     by 2 (or another index's value) is flagged.  Any fault-injection teacher check uses a Pauli
     ``*_ERROR(1.0)`` channel, NEVER a Pauli *gate* (the ``compile_detector_sampler`` gate-absorption
     trap, window_covering_RESULTS §4 / ``inject_debug.py``).

GPU-capable: every tensor op carries the resolved ``DEVICE`` (CUDA when available); the model body is
``complex128`` throughout. Window-level checks need the REAL d7 circuit (no toy models —
[[feedback-no-toy-models-real-target]]); they skip without ``QEC_TWIN_HW_DATA``. The mechanism-level,
oracle, PTM, and sidecar checks are data-free and always run.
"""

import functools
import json
import math
import os
from pathlib import Path

import numpy as np
import pytest
import torch

from qec_twin.numerics import NUMERICAL_ZERO

# --- the §10 sibling modules (built concurrently; this file codes against the frozen contract) --- #
from qec_twin.forward.mechanisms_torch import MECH_1Q, MECH_2Q
from qec_twin.forward import window_diagnostics as wd
from qec_twin.forward.window_channel import (
    MAX_WINDOW_QUBITS,
    SLOT_CZ,
    SLOT_ONEQ,
    SLOT_SPECTATOR,
    WindowChannel,
    build_placement,
    full_in_ancilla,
)

# --- reused, already-landed primitives (spec §7 "Reuse") --- #
from qec_twin.forward.cptp_channel import (
    CDTYPE,
    apply_kraus,
    choi_matrix,
    tp_residual,
)
from qec_twin.forward import channels as npch


# --------------------------------------------------------------------------- #
# Device / dtype policy (GPU-ONLY HARD gate; complex128 model body — §3)        #
# --------------------------------------------------------------------------- #
# §3 "GPU-only (HARD gate)": every WindowChannel construction / forward / eigvalsh / gradient in this
# suite runs on cuda. There is NO cuda-if-available-else-cpu fallback — running the window tests on CPU
# to dodge memory is the exact defect this build removes (the register is BOUNDED instead, full-in
# ancilla only; see test_interior_window_register_memory_bound). Require cuda and fail loudly otherwise.
if not torch.cuda.is_available():
    raise RuntimeError(
        "tests/test_window_channel.py is GPU-only (spec §3 'GPU-only (HARD gate)'): CUDA is required "
        "but torch.cuda.is_available() is False. No CPU fallback — run on a CUDA workstation."
    )
DEVICE = torch.device("cuda")

# Tolerances (epistemic tag (c): heuristic gate constants — tripwires only, never a premise).
TP_TOL = NUMERICAL_ZERO          # spec §6.1: tp_residual < 1e-12
CHOI_PSD_TOL = -NUMERICAL_ZERO   # spec §6.1: min Choi eigenvalue >= -1e-12
ORACLE_TOL = 1e-10               # spec §6.4: torch-vs-NumPy elementwise / Choi / action < 1e-10
COH_POS = 1e-6                   # a coherent mechanism's off-diagonal PTM mass is comfortably > this
COH_ZERO = 1e-9                  # a stochastic-Pauli mechanism's off-diagonal PTM mass is ~0
GRAD_TOL = 1e-6                  # finite-difference vs autograd agreement (central diff, h=1e-4)
FD_STEP = 1e-4

# Representative non-trivial θ for the dictionary checks (a generic angle / sigmoid-pre-image; the
# checks must hold for an arbitrary live θ, not just θ=0).
THETA_1Q = 0.37
THETA_2Q = 0.41

# Real-dataset wiring (mirrors outputs/placement_enumerate.py + the existing hardware tests).
_REL = "google_105Q_surface_code_d3_d5_d7/google_105Q_surface_code_d3_d5_d7"
_PATCH, _BASIS, _ROUNDS = "d7_at_q6_7", "X", "r90"
_MEAS_NAMES = {"M", "MX", "MY", "MZ", "MR", "MRX", "MRY", "MRZ"}
_SIDECAR = Path(__file__).resolve().parents[1] / "outputs" / "placement_enumerate_results.json"

# Sidecar ground-truth slot counts for the FULL d7 round (committed; window_covering_RESULTS §2/§5):
EXPECT_CZ_INCIDENCES = 168       # 4 CZ layers x 42 (data,measure) pairs
EXPECT_DATA_1Q_SLOTS = 196       # 49 data x 4 data-1q layers
EXPECT_SPECTATOR_PAIRS = 156     # (data,data) share-a-stabilizer edges
EXPECT_DATA = 49


# --------------------------------------------------------------------------- #
# Positive-control harness — a check is alive iff it FLAGS a broken input      #
# --------------------------------------------------------------------------- #
def _assert_flags(predicate, broken, *, what: str) -> None:
    """Assert that ``predicate(broken)`` is False — i.e. the check detects the deliberate break.

    ``predicate`` returns True for a GOOD input. The positive control passes a deliberately-broken
    input and asserts the predicate REJECTS it; if it does not, the check is worthless (it cannot
    distinguish broken from passed) and we fail loudly here, in the test, not silently in production.
    """
    assert not predicate(broken), f"POSITIVE CONTROL DEAD: check accepted a broken input ({what})"


# --------------------------------------------------------------------------- #
# Builder enumeration over the §10 registries                                  #
# --------------------------------------------------------------------------- #
def _theta(arity: int) -> torch.Tensor:
    """A real-scalar θ for an ``arity``-qubit builder (the §10 builder input), for MEASUREMENT checks.

    Detached (no ``requires_grad``): the CPTP / coherence / oracle / PTM checks only read scalar
    metrics off the Kraus, so a grad-tracked leaf would only spew "converting a tensor with
    requires_grad to a scalar" warnings. The differentiability half of the contract (builders accept a
    grad leaf and pass gradients) is exercised separately and end-to-end by the gradient/sensitivity
    test through ``WindowChannel.parameters()`` and by ``test_builders_accept_grad_leaf``.
    """
    value = THETA_1Q if arity == 1 else THETA_2Q
    return torch.tensor(float(value), dtype=torch.float64, device=DEVICE)


def _all_builders():
    """Yield ``(name, arity, builder, kraus)`` for every §10 dictionary mechanism at a live θ."""
    for name, builder in sorted(MECH_1Q.items()):
        kraus = builder(_theta(1), device=DEVICE)
        yield name, 1, builder, kraus
    for name, builder in sorted(MECH_2Q.items()):
        kraus = builder(_theta(2), device=DEVICE)
        yield name, 2, builder, kraus


# Which §10 keys are coherent (unitary, PTM off-diagonal LIVE) vs stochastic-Pauli (diagonal PTM).
# Per spec §2 + the §10 key list. Coherent = the differentiator (correction 2).
COHERENT_1Q = {"rx", "ry", "rz"}
COHERENT_2Q = {"rzz", "rxx", "ryy", "rxx_ryy", "cphase", "two_pauli_xy", "two_pauli_zx", "two_pauli_zy"}
PAULI_STOCH_1Q = {"pauli_x", "pauli_y", "pauli_z"}   # diagonal PTM (no coherence)


# --------------------------------------------------------------------------- #
# §6.1  CPTP — every mechanism is trace-preserving with a PSD Choi             #
# --------------------------------------------------------------------------- #
def _is_tp(kraus: torch.Tensor) -> bool:
    return float(tp_residual(kraus)) < TP_TOL


def test_cptp_every_mechanism_is_trace_preserving():
    """§6.1 (mechanisms): every §10 builder is TP — ``tp_residual < 1e-12`` at a live θ."""
    checked = 0
    for name, arity, _builder, kraus in _all_builders():
        assert kraus.dtype == CDTYPE, f"{name}: builder must return complex128 Kraus (got {kraus.dtype})"
        assert kraus.dim() == 3 and kraus.shape[-1] == kraus.shape[-2] == 2 ** arity, (
            f"{name}: Kraus stack must be (r, {2 ** arity}, {2 ** arity}); got {tuple(kraus.shape)}"
        )
        res = float(tp_residual(kraus))
        assert res < TP_TOL, f"{name}: not trace-preserving (tp_residual={res:.3e} >= {TP_TOL:.1e})"
        checked += 1
    assert checked == len(MECH_1Q) + len(MECH_2Q), "did not cover the full §10 dictionary"

    # POSITIVE CONTROL: a deliberately non-TP map (a scaled isometry) must be flagged.
    eye = torch.eye(2, dtype=CDTYPE, device=DEVICE)
    not_tp = torch.stack([0.5 * eye])  # sum K^dag K = 0.25 I != I
    assert float(tp_residual(not_tp)) >= TP_TOL, "tp_residual failed to see a non-TP map"
    _assert_flags(_is_tp, not_tp, what="non-TP scaled-identity map")


def test_cptp_every_mechanism_has_psd_choi():
    """§6.1 (mechanisms): every §10 builder is CP — Choi min-eigenvalue ≥ −1e-12 at a live θ.

    Note (made explicit so the control below is honest): ``choi_matrix(kraus)`` is a sum of rank-1
    ``vec(K) vec(K)^†`` outer products, hence **PSD by construction** for ANY operator stack. So this
    leg's real content is a consistency guard on D's eigenvalue computation + the Choi build (it would
    catch a builder returning NaN / wrong-shape / non-Hermitian-Choi operators). The positive control
    therefore validates the *detector*: that ``choi_min_eig``'s minimum-eigenvalue routine genuinely
    reports a negative number on an indefinite Hermitian Choi — i.e. the ≥ −1e-12 gate has teeth.
    """
    for name, _arity, _builder, kraus in _all_builders():
        lo = float(wd.choi_min_eig(kraus))
        assert lo >= CHOI_PSD_TOL, f"{name}: Choi not PSD (min eig={lo:.3e} < {CHOI_PSD_TOL:.1e})"

    # POSITIVE CONTROL (detector liveness): an explicitly INDEFINITE Hermitian matrix (the canonical
    # non-CP "Choi" of the transpose map = SWAP, eigenvalues {+1,+1,+1,-1}) must yield a clearly
    # negative minimum eigenvalue under the SAME primitive D's choi_min_eig uses (eigvalsh). If this
    # did not go negative, the PSD gate could never fire and the CP check would be worthless.
    bad_choi = _indefinite_choi()
    assert float(torch.linalg.eigvalsh(bad_choi).min()) < CHOI_PSD_TOL, (
        "eigenvalue detector failed to flag an indefinite Choi"
    )

    def _choi_psd(j: torch.Tensor) -> bool:
        herm = 0.5 * (j + j.conj().transpose(-1, -2))
        return float(torch.linalg.eigvalsh(herm).min()) >= CHOI_PSD_TOL

    good_choi = choi_matrix(MECH_1Q["amp_damp"](_theta(1), device=DEVICE))
    assert _choi_psd(good_choi), "PSD-Choi predicate wrongly rejected a valid CP map's Choi"
    _assert_flags(_choi_psd, bad_choi, what="indefinite Hermitian Choi (non-CP / transpose map)")


def _indefinite_choi() -> torch.Tensor:
    """The Choi matrix of the (non-CP) transpose map on a qubit: eigenvalues {+1,+1,+1,−1}.

    ``J(T) = Σ_ij |i><j| ⊗ T(|i><j|) = Σ_ij |i><j| ⊗ |j><i| = SWAP`` (4×4), whose spectrum is the
    symmetric (+1, triple) / antisymmetric (−1, single) decomposition — manifestly indefinite. The
    textbook witness that the transpose is positive but NOT completely positive, so it is the correct,
    honest break for a "PSD Choi" check. It cannot be produced by any real Kraus stack — which is
    exactly why the control is built at the Choi level, not via a (always-PSD) Kraus impostor.
    """
    return torch.tensor(
        [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=CDTYPE, device=DEVICE
    )


def test_builders_accept_grad_leaf_and_are_differentiable():
    """§2/§10 contract: every builder accepts a ``requires_grad`` real scalar θ and passes gradients.

    The differentiability half of the dictionary contract (the rest of the suite reads detached
    metrics to stay warning-clean). A representative coherent + non-unitary builder of each arity is
    differentiated through a simple scalar functional; the gradient must be finite and non-None.
    """
    for arity, name in [(1, "rz"), (1, "amp_damp"), (2, "rzz"), (2, "depol2")]:
        reg = MECH_1Q if arity == 1 else MECH_2Q
        leaf = torch.tensor(
            THETA_1Q if arity == 1 else THETA_2Q,
            dtype=torch.float64, device=DEVICE, requires_grad=True,
        )
        kraus = reg[name](leaf, device=DEVICE)
        # a real scalar functional of the Kraus (sum of |entries|^2 — depends on θ for every builder).
        loss = (kraus.abs() ** 2).sum()
        (grad,) = torch.autograd.grad(loss, leaf, allow_unused=True)
        assert grad is not None, f"{name}: builder did not pass a gradient to its θ leaf"
        assert torch.isfinite(grad).all(), f"{name}: builder produced a non-finite θ gradient"

    # POSITIVE CONTROL: differentiate a (genuinely differentiable) loss built from a DIFFERENT,
    # independent leaf w.r.t. an UNUSED leaf ⇒ ``allow_unused`` returns None. This proves the
    # assertion above is meaningful — it distinguishes a builder that passes grad to its θ (non-None)
    # from one whose output does not depend on the queried θ at all (None). A builder that severed the
    # θ→Kraus path would land in this None branch and be caught by the assertion.
    used = torch.tensor(THETA_1Q, dtype=torch.float64, device=DEVICE, requires_grad=True)
    unused = torch.tensor(THETA_2Q, dtype=torch.float64, device=DEVICE, requires_grad=True)
    loss = (MECH_1Q["rz"](used, device=DEVICE).abs() ** 2).sum()
    (none_grad,) = torch.autograd.grad(loss, unused, allow_unused=True, retain_graph=False)
    assert none_grad is None, "control: a θ the output does not depend on should yield a None gradient"


# --------------------------------------------------------------------------- #
# §6.2  Coherence representable — coherent off-diagonal > 0; Pauli diagonal ~0 #
# --------------------------------------------------------------------------- #
def test_coherence_coherent_mechanisms_have_offdiagonal_ptm():
    """§6.2: every coherent §10 mechanism has PTM off-diagonal Frobenius mass > 0 (representable)."""
    for name, builder in sorted(MECH_1Q.items()):
        if name not in COHERENT_1Q:
            continue
        kraus = builder(_theta(1), device=DEVICE)
        mass = float(wd.coherence_budget(kraus, 1))
        assert mass > COH_POS, f"{name}: coherent mechanism has no off-diagonal PTM mass ({mass:.3e})"
    for name, builder in sorted(MECH_2Q.items()):
        if name not in COHERENT_2Q:
            continue
        kraus = builder(_theta(2), device=DEVICE)
        mass = float(wd.coherence_budget(kraus, 2))
        assert mass > COH_POS, f"{name}: coherent 2q mechanism has no off-diagonal PTM mass ({mass:.3e})"

    # POSITIVE CONTROL: a coherent mechanism at θ = 0 is the identity (diagonal PTM, ZERO off-diag);
    # the "coherence > 0" predicate must REJECT it — proving the check actually responds to coherence
    # and is not trivially true for every input.
    rz_identity = MECH_1Q["rz"](
        torch.tensor(0.0, dtype=torch.float64, device=DEVICE), device=DEVICE
    )
    assert float(wd.coherence_budget(rz_identity, 1)) <= COH_ZERO, "θ=0 rz is not coherence-free"
    _assert_flags(lambda k: float(wd.coherence_budget(k, 1)) > COH_POS, rz_identity,
                  what="θ=0 rz (identity) wrongly read as coherent")


def test_coherence_pauli_stochastic_is_diagonal_ptm():
    """§6.2 control side: a Pauli-stochastic mechanism has ~0 off-diagonal PTM mass (diagonal PTM)."""
    for name in sorted(PAULI_STOCH_1Q):
        kraus = MECH_1Q[name](_theta(1), device=DEVICE)
        mass = float(wd.coherence_budget(kraus, 1))
        assert mass <= COH_ZERO, f"{name}: Pauli-stochastic mechanism has off-diagonal PTM mass ({mass:.3e})"
        # the PTM must be (near-)diagonal: its off-diagonal Frobenius mass is ~0 directly.
        r = wd.ptm(kraus, 1, device=DEVICE)
        offdiag = r - torch.diag(torch.diagonal(r))
        assert float(torch.linalg.matrix_norm(offdiag)) <= COH_ZERO, f"{name}: PTM not diagonal"

    # POSITIVE CONTROL: a COHERENT mechanism must NOT pass the "diagonal PTM" predicate — i.e. the
    # diagonality check has teeth (it is not satisfied by every channel).
    coherent = MECH_1Q["ry"](_theta(1), device=DEVICE)
    assert float(wd.coherence_budget(coherent, 1)) > COH_POS, "control coherent mech is not coherent"
    _assert_flags(lambda k: float(wd.coherence_budget(k, 1)) <= COH_ZERO, coherent,
                  what="coherent ry wrongly read as diagonal/Pauli")


# --------------------------------------------------------------------------- #
# §6.4  Cross-validation oracle — torch builder vs channels.py NumPy builder   #
# --------------------------------------------------------------------------- #
def _npkraus_to_torch(np_kraus) -> torch.Tensor:
    """Stack a list of NumPy Kraus operators into a (r, d, d) complex128 torch tensor on DEVICE."""
    arr = np.stack([np.asarray(k, dtype=np.complex128) for k in np_kraus])
    return torch.as_tensor(arr, dtype=CDTYPE, device=DEVICE)


def _ic_inputs(dim: int) -> torch.Tensor:
    """Informationally-complete input density matrices (tensored {|0>,|1>,|+>,|+i>}) for size ``dim``.

    An independent IC set (built here, not imported from cptp_channel) so the oracle check does not
    inherit any bug in the reused helper; spanning Herm(dim) ⇒ equal action on this set ⇔ equal map.
    """
    z = torch.tensor([1.0, 0.0], dtype=CDTYPE, device=DEVICE)
    o = torch.tensor([0.0, 1.0], dtype=CDTYPE, device=DEVICE)
    p = (z + o) / math.sqrt(2.0)
    pi = (z + 1j * o) / math.sqrt(2.0)
    singles = [torch.outer(v, v.conj()) for v in (z, o, p, pi)]
    acc = singles
    n = int(round(math.log2(dim)))
    for _ in range(n - 1):
        acc = [torch.kron(a, b) for a in acc for b in singles]
    return torch.stack(acc)


def _channels_equal(k_torch: torch.Tensor, k_np: torch.Tensor) -> bool:
    """True iff two Kraus stacks represent the same CPTP map to < 1e-10.

    The mathematically-correct channel equality is GAUGE-INVARIANT (a channel's Kraus set is defined
    only up to a unitary mixing / reordering of operators), so the load-bearing comparison is:
      (i)  Choi distance (``choi_matrix`` is Kraus-gauge invariant — its docstring), and
      (ii) equal action on an Herm-spanning IC input set (the action determines the map).
    Elementwise ``< 1e-10`` (spec §6.4) is exact and unambiguous for SINGLE-Kraus unitaries (r == 1,
    the coherent dictionary) and is asserted for those in the caller; for multi-Kraus channels a raw
    elementwise compare would false-fail on a benign operator REORDER, so (i)+(ii) adjudicate there.
    """
    choi_d = float(torch.linalg.matrix_norm(choi_matrix(k_torch) - choi_matrix(k_np)))
    ins = _ic_inputs(k_torch.shape[-1])
    act_d = float((apply_kraus(ins, k_torch) - apply_kraus(ins, k_np)).abs().max())
    ok = choi_d < ORACLE_TOL and act_d < ORACLE_TOL
    if k_torch.shape == k_np.shape and k_torch.shape[0] == 1:
        ok = ok and float((k_torch - k_np).abs().max()) < ORACLE_TOL
    return ok


def _oracle_pairs():
    """Yield ``(name, arity, k_torch, k_np)`` for every torch builder with an UNAMBIGUOUS NumPy twin.

    The single-θ torch builder maps to the same-named ``channels.py`` builder at the matching angle
    (coherent) or ``p = sigmoid(θ)`` strength (non-unitary CPTP), exactly as the §10 contract states.
    Builders whose single θ → multi-angle mapping is not pinned by the contract (e.g. ``rxx_ryy``
    takes two independent angles in NumPy) are still covered for CPTP/coherence above; here we
    cross-validate every builder whose NumPy correspondence is contract-unambiguous.
    """
    t1 = float(THETA_1Q)
    t2 = float(THETA_2Q)
    # p = sigmoid(θ) computed in float64 — MUST match the builders' precision (a float32
    # torch.tensor(t) default would shift p by ~1e-8 and inflate the Choi distance to ~4e-9).
    p1 = float(torch.sigmoid(torch.tensor(t1, dtype=torch.float64)))
    p2 = float(torch.sigmoid(torch.tensor(t2, dtype=torch.float64)))

    # ---- 1q coherent (Kraus = [U], θ = rotation angle) ----
    yield "rx", 1, MECH_1Q["rx"](_theta(1), device=DEVICE), _npkraus_to_torch([npch.rx_unitary(t1)])
    yield "ry", 1, MECH_1Q["ry"](_theta(1), device=DEVICE), _npkraus_to_torch([npch.ry_unitary(t1)])
    yield "rz", 1, MECH_1Q["rz"](_theta(1), device=DEVICE), _npkraus_to_torch([npch.rz_unitary(t1)])
    # ---- 1q non-unitary CPTP (p = sigmoid(θ)) ----
    yield "amp_damp", 1, MECH_1Q["amp_damp"](_theta(1), device=DEVICE), _npkraus_to_torch(npch.amplitude_damping_kraus(p1))
    yield "phase_damp", 1, MECH_1Q["phase_damp"](_theta(1), device=DEVICE), _npkraus_to_torch(npch.phase_damping_kraus(p1))
    yield "pauli_x", 1, MECH_1Q["pauli_x"](_theta(1), device=DEVICE), _npkraus_to_torch(npch.pauli_stochastic_kraus({"X": p1}))
    yield "pauli_y", 1, MECH_1Q["pauli_y"](_theta(1), device=DEVICE), _npkraus_to_torch(npch.pauli_stochastic_kraus({"Y": p1}))
    yield "pauli_z", 1, MECH_1Q["pauli_z"](_theta(1), device=DEVICE), _npkraus_to_torch(npch.pauli_stochastic_kraus({"Z": p1}))
    yield "thermal", 1, MECH_1Q["thermal"](_theta(1), device=DEVICE), _npkraus_to_torch(npch.thermal_excitation_kraus(p1))
    yield "custom_nonpauli", 1, MECH_1Q["custom_nonpauli"](_theta(1), device=DEVICE), _npkraus_to_torch(npch.custom_non_pauli_kraus(p1))
    yield "leakage", 1, MECH_1Q["leakage"](_theta(1), device=DEVICE), _npkraus_to_torch(npch.leakage_relaxation_surrogate_kraus(p1))
    # ---- 2q coherent (Kraus = [U], θ = rotation angle) ----
    yield "rzz", 2, MECH_2Q["rzz"](_theta(2), device=DEVICE), _npkraus_to_torch([npch.rzz_unitary(t2)])
    yield "rxx", 2, MECH_2Q["rxx"](_theta(2), device=DEVICE), _npkraus_to_torch([npch.rxx_unitary(t2)])
    yield "ryy", 2, MECH_2Q["ryy"](_theta(2), device=DEVICE), _npkraus_to_torch([npch.ryy_unitary(t2)])
    yield "cphase", 2, MECH_2Q["cphase"](_theta(2), device=DEVICE), _npkraus_to_torch([npch.controlled_phase_error_unitary(t2)])
    yield "two_pauli_xy", 2, MECH_2Q["two_pauli_xy"](_theta(2), device=DEVICE), _npkraus_to_torch([npch.two_pauli_rotation(t2, "X", "Y")])
    yield "two_pauli_zx", 2, MECH_2Q["two_pauli_zx"](_theta(2), device=DEVICE), _npkraus_to_torch([npch.two_pauli_rotation(t2, "Z", "X")])
    yield "two_pauli_zy", 2, MECH_2Q["two_pauli_zy"](_theta(2), device=DEVICE), _npkraus_to_torch([npch.two_pauli_rotation(t2, "Z", "Y")])
    # ---- 2q non-unitary CPTP (p = sigmoid(θ)) ----
    yield "depol2", 2, MECH_2Q["depol2"](_theta(2), device=DEVICE), _npkraus_to_torch(npch.two_qubit_depolarizing_kraus(p2))
    yield "corr_relax", 2, MECH_2Q["corr_relax"](_theta(2), device=DEVICE), _npkraus_to_torch(npch.correlated_relaxation_kraus(p2))
    # NOTE: ``rxx_ryy`` is intentionally NOT here. Its NumPy twin ``rxx_ryy_unitary`` takes TWO
    # independent angles, while the §10 torch builder takes a SINGLE θ — so the single-θ → two-angle
    # mapping is not pinned by the contract. It is covered for CPTP/coherence in the other checks and
    # given a dedicated, convention-tolerant oracle check below (a hard assert on an undefined mapping
    # would be a false failure). The strength locals are kept for the mapping's readability.
    _ = (p1, p2)


def test_oracle_torch_builders_match_numpy_channels():
    """§6.4: each torch §10 builder == its ``channels.py`` NumPy twin at the same θ (< 1e-10).

    Gauge-invariant equality (Choi distance + action on an IC set) is the contract-faithful comparison
    for every builder; strict ELEMENTWISE ``< 1e-10`` is additionally asserted for the single-Kraus
    unitaries (r == 1 — the coherent dictionary), where Kraus order is unambiguous. Multi-Kraus
    channels (depol2, amplitude/phase damping, …) are equal up to operator reordering, so elementwise
    is intentionally not forced there (it would false-fail on a benign reorder).
    """
    n_ok = 0
    elementwise_checked = []
    for name, _arity, k_torch, k_np in _oracle_pairs():
        choi_d = float(torch.linalg.matrix_norm(choi_matrix(k_torch) - choi_matrix(k_np)))
        ins = _ic_inputs(k_torch.shape[-1])
        act_d = float((apply_kraus(ins, k_torch) - apply_kraus(ins, k_np)).abs().max())
        assert choi_d < ORACLE_TOL, f"{name}: Choi distance to NumPy oracle {choi_d:.3e} >= {ORACLE_TOL:.1e}"
        assert act_d < ORACLE_TOL, f"{name}: IC-action distance to NumPy oracle {act_d:.3e} >= {ORACLE_TOL:.1e}"
        # strict elementwise for single-Kraus unitaries (gauge-unambiguous; spec §6.4 "elementwise").
        if k_torch.shape == k_np.shape and k_torch.shape[0] == 1:
            ew = float((k_torch - k_np).abs().max())
            assert ew < ORACLE_TOL, f"{name}: elementwise unitary mismatch {ew:.3e} >= {ORACLE_TOL:.1e}"
            elementwise_checked.append(name)
        n_ok += 1
    assert n_ok >= 18, f"oracle cross-validated too few builders ({n_ok})"
    assert len(elementwise_checked) >= 7, (
        f"too few single-Kraus unitaries elementwise-checked ({elementwise_checked})"
    )

    # POSITIVE CONTROL: the SAME comparison must REJECT a θ-perturbed torch channel — i.e. the oracle
    # test detects a real numerical disagreement and is not vacuously satisfied.
    good = MECH_2Q["rzz"](_theta(2), device=DEVICE)
    perturbed = MECH_2Q["rzz"](
        torch.tensor(float(THETA_2Q) + 0.1, dtype=torch.float64, device=DEVICE), device=DEVICE
    )
    np_ref = _npkraus_to_torch([npch.rzz_unitary(float(THETA_2Q))])
    assert _channels_equal(good, np_ref), "oracle equality wrongly rejected a matching channel"
    _assert_flags(lambda k: _channels_equal(k, np_ref), perturbed,
                  what="θ-perturbed rzz wrongly accepted as oracle-equal")


def test_oracle_rxx_ryy_unitary_and_coherent():
    """§6.4 (rxx_ryy): the two-axis coherent builder is a unitary CPTP coherent map, and matches the
    NumPy ``rxx_ryy_unitary`` under the canonical equal-angle reading IF B adopted it.

    ``rxx_ryy``'s single θ → two-angle mapping is NOT pinned by §10 (the NumPy twin takes two
    independent angles), so this check HARD-asserts only the contract-guaranteed properties (CPTP +
    coherent + unitary single-Kraus) and REPORTS — does not fail — the equal-angle (θ_x = θ_y = θ)
    correspondence to the NumPy oracle, since asserting an undefined mapping would be a false failure.
    """
    k = MECH_2Q["rxx_ryy"](_theta(2), device=DEVICE)
    # contract-guaranteed: CPTP, coherent (off-diagonal PTM), and (per spec §2 coherent class) unitary.
    assert float(tp_residual(k)) < TP_TOL, "rxx_ryy not trace-preserving"
    assert float(wd.choi_min_eig(k)) >= CHOI_PSD_TOL, "rxx_ryy Choi not PSD"
    assert float(wd.coherence_budget(k, 2)) > COH_POS, "rxx_ryy carries no coherence (off-diagonal PTM)"

    # REPORT the equal-angle oracle correspondence (informational; a mismatch here is a convention
    # difference, NOT a defect — printed for the integrator, never asserted).
    np_equal_angle = _npkraus_to_torch([npch.rxx_ryy_unitary(theta_x=float(THETA_2Q), theta_y=float(THETA_2Q))])
    matches = _channels_equal(k, np_equal_angle)
    print(f"[oracle] rxx_ryy equal-angle (θx=θy=θ) correspondence to NumPy oracle: {matches}", flush=True)


# --------------------------------------------------------------------------- #
# §6.3 (b)  Placement — embedded operator acts on exactly the intended qubits  #
# --------------------------------------------------------------------------- #
def test_placement_embedded_operator_acts_on_intended_qubits():
    """§6.3 (permutation): a 1q operator embedded on a chosen target acts ONLY on that qubit.

    Uses ``window_diagnostics.partial_trace`` (the §10 helper) as the independent witness: apply
    ``X`` on qubit ``target`` of an ``n``-qubit register, reduce to each qubit, and assert only the
    targeted qubit flipped (|0> -> |1>) while every spectator stayed |0>.
    """
    n = 3
    target = 1
    dim = 2 ** n
    rho0 = torch.zeros((dim, dim), dtype=CDTYPE, device=DEVICE)
    rho0[0, 0] = 1.0  # |000><000|
    # apply X on `target` via the reused embedding (the same path WindowChannel uses).
    from qec_twin.forward.exact.circuit_sim import apply_channel_local
    x = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE, device=DEVICE).unsqueeze(0)
    rho1 = apply_channel_local(rho0, x, [target], n)

    def _qubit_is_one(rho, q) -> bool:
        red = wd.partial_trace(rho, [q], n)        # (2,2) reduced state of qubit q
        return float(red[1, 1].real) > 0.5         # population in |1>

    for q in range(n):
        expect_one = (q == target)
        got_one = _qubit_is_one(rho1, q)
        assert got_one == expect_one, (
            f"qubit {q}: expected |1>={expect_one} after X on {target}, got |1>={got_one} "
            f"(operator acted on the wrong qubit)"
        )

    # POSITIVE CONTROL: embedding on the WRONG target flips a different qubit — the permutation check
    # would then see qubit `target` still |0>, so it must reject the wrong-target state.
    wrong_target = 2
    rho_wrong = apply_channel_local(rho0, x, [wrong_target], n)
    predicate = lambda rho: (_qubit_is_one(rho, target) and not _qubit_is_one(rho, wrong_target))
    assert predicate(rho1), "permutation predicate wrongly rejected the correct placement"
    _assert_flags(predicate, rho_wrong, what="X embedded on the wrong qubit")


# --------------------------------------------------------------------------- #
# Real-circuit parse (faithful; reused convention from outputs/placement_enumerate.py)  #
# --------------------------------------------------------------------------- #
def _hw_root() -> Path | None:
    parent = os.environ.get("QEC_TWIN_HW_DATA")
    if not parent:
        return None
    leaf = Path(parent) / _REL / _PATCH / _BASIS / _ROUNDS / "circuit_ideal.stim"
    return leaf if leaf.exists() else None


_needs_hw = pytest.mark.skipif(
    _hw_root() is None,
    reason="real d7 circuit absent (set QEC_TWIN_HW_DATA); window-construction checks need it (no toy models)",
)


@functools.lru_cache(maxsize=1)
def _parse_real_round():
    """Parse the REAL d7 ideal circuit into (round_schedule, data, measure, adjacency, coord_of).

    Cached (the d7 circuit file is fixed): the flatten of a 90-round, 101-qubit circuit is the slow
    step, and the window-construction checks each need it — matches the ``functools.lru_cache`` pattern
    of the existing ``tests/test_hardware_m2_window_closure.py``. Callers only READ the returned
    containers (or copy them, e.g. ``set(adjacency)``), so sharing the cached value is safe.

    Identical convention to ``outputs/placement_enumerate.py`` (correction 1): roles from the circuit
    (measured-every-round => measure/ancilla; measured-once => data), supports from the CZ layers,
    adjacency = share-a-stabilizer (data,data) co-occurrence, and the steady-state round = the second
    interior M-to-M block. ``round_schedule`` is the §3/§10 ``{"name","qubits","pairs"}`` op-list that
    ``build_placement`` consumes.
    """
    import stim

    leaf = _hw_root()
    circ = stim.Circuit.from_file(str(leaf))
    fc = circ.flattened()

    meas_count: dict[int, int] = {}
    for inst in fc:
        if inst.name in _MEAS_NAMES:
            for t in inst.targets_copy():
                if t.is_qubit_target:
                    meas_count[t.qubit_value] = meas_count.get(t.qubit_value, 0) + 1
    measure = {q for q, c in meas_count.items() if c >= 2}
    data = {q for q, c in meas_count.items() if c == 1}

    coord_of: dict[int, tuple[float, float]] = {}
    for inst in fc:
        if inst.name == "QUBIT_COORDS":
            v = inst.gate_args_copy()
            for t in inst.targets_copy():
                if t.is_qubit_target:
                    coord_of[t.qubit_value] = (v[0], v[1])

    # supports: measure -> {data it CZ-couples to}
    supp: dict[int, set[int]] = {m: set() for m in measure}
    for inst in fc:
        if inst.name != "CZ":
            continue
        ts = inst.targets_copy()
        for i in range(0, len(ts), 2):
            a, b = ts[i].qubit_value, ts[i + 1].qubit_value
            if a in measure and b in data:
                supp[a].add(b)
            elif b in measure and a in data:
                supp[b].add(a)
    adjacency: set[tuple[int, int]] = set()
    for s in supp.values():
        sl = sorted(s)
        for i in range(len(sl)):
            for j in range(i + 1, len(sl)):
                adjacency.add((sl[i], sl[j]))

    # steady-state round = second interior M-to-M block (skip the time-boundary init).
    m_idx = [i for i, inst in enumerate(fc) if inst.name in _MEAS_NAMES]
    assert len(m_idx) >= 3, "need >= 3 measure rounds for an interior steady round"
    lo, hi = m_idx[1], m_idx[2]
    skip = {"TICK", "DETECTOR", "OBSERVABLE_INCLUDE", "SHIFT_COORDS", "QUBIT_COORDS"}
    round_schedule = []
    for k, inst in enumerate(fc[lo + 1:hi + 1]):
        if inst.name in skip:
            continue
        qs = [t.qubit_value for t in inst.targets_copy() if t.is_qubit_target]
        pairs = None
        if inst.name == "CZ":
            ts = inst.targets_copy()
            pairs = [(ts[i].qubit_value, ts[i + 1].qubit_value) for i in range(0, len(ts), 2)]
        round_schedule.append({"name": inst.name, "qubits": qs, "pairs": pairs, "layer": k})
    return round_schedule, data, measure, adjacency, coord_of, supp


_WINDOW_QUBIT_BUDGET = 10   # 2**10 density matrix — cheap for autograd / eigvalsh in a unit test.


def _small_real_window(data, measure, adjacency, coord_of, supp):
    """Pick a SMALL REAL window (a corner) + its FULL-IN ancilla (§3 register bound), register ≤ budget.

    REAL window, REAL schedule (no toy models — [[feedback-no-toy-models-real-target]]). The window is
    the share-a-stabilizer radius-1 ball of a corner data qubit (step-1: corner windows have 4 data).
    Ancilla = the §3 FULL-IN set (``full_in_ancilla``): measure qubits whose CZ support is a SUBSET of
    the window data — the stabilizers contained in the window. Seam ancilla (support reaching outside
    the window) are DEFERRED to step-4, so they never enter the register. A corner window is then 4
    data + 2 full-in = 6 qubits (measured; ``outputs/window_register_probe.py``) — comfortably under
    the unit-test budget and well within :data:`MAX_WINDOW_QUBITS`. A full-in ancilla's support ⊆ the
    window data, so its CZ ``(data, measure)`` pairs are in-window by construction (the 2q coherent
    slots are exercised). No arbitrary trimming — the register IS the bounded faithful window.
    """
    nbr: dict[int, set[int]] = {d: set() for d in data}
    for a, b in adjacency:
        nbr[a].add(b)
        nbr[b].add(a)
    # corner data qubit = minimum share-a-stabilizer degree (step-1: corners have degree 3), tie-broken
    # by coordinate for determinism.
    center = min(data, key=lambda d: (len(nbr[d]), coord_of[d]))
    window_data = sorted({center} | nbr[center])

    # §3 register bound: FULL-IN ancilla only (support ⊆ window data); seam ancilla deferred to step-4.
    ancilla = full_in_ancilla(window_data, supp)
    n = len(window_data) + len(ancilla)
    assert n <= _WINDOW_QUBIT_BUDGET, f"corner window register n={n} exceeds budget {_WINDOW_QUBIT_BUDGET}"
    return window_data, ancilla, center


def _interior_real_window(data, measure, adjacency, coord_of, supp):
    """Pick a REAL INTERIOR window (9 data) + its FULL-IN ancilla — the §3 register-bound stress case.

    The radius-1 share-a-stabilizer ball of an INTERIOR data qubit has 9 data (a real 3x3 window). Its
    FULL-IN ancilla (support ⊆ the 9 data) is 4 on the real d7 covering, giving a 13-qubit register
    (``outputs/window_register_probe.py``) — exactly the worst case the §3 bound must keep GPU-feasible
    (4**13 ≈ 0.07 GB bare; autograd/eigvalsh peak measured in the memory-bound test). The FORBIDDEN
    data + ALL-touching-ancilla register for the same window is ~25 qubits (4**25 ≈ 1e6 GB), which
    WindowChannel refuses to instantiate. Deterministic: smallest full-in register, tie-broken by
    coordinate. Returns ``(window_data, ancilla, center, n_forbidden)`` (the forbidden size is reported
    so the test can show what the bound avoids).
    """
    nbr: dict[int, set[int]] = {d: set() for d in data}
    for a, b in adjacency:
        nbr[a].add(b)
        nbr[b].add(a)
    candidates = []
    for d in data:
        w = sorted({d} | nbr[d])
        if len(w) == 9:  # a real interior 3x3 window
            fin = full_in_ancilla(w, supp)
            candidates.append((len(w) + len(fin), coord_of[d], d, w, fin))
    assert candidates, "no interior 9-data window found on the real d7 covering"
    candidates.sort(key=lambda t: (t[0], t[1]))  # smallest register, then coordinate
    n_reg, _coord, center, window_data, ancilla = candidates[0]
    # the forbidden full + ALL-touching-ancilla register size (reported, never built).
    win_set = set(window_data)
    all_touching = sorted(m for m, s in supp.items() if set(s) & win_set)
    n_forbidden = len(window_data) + len(all_touching)
    return window_data, ancilla, center, n_forbidden


# --------------------------------------------------------------------------- #
# §6.3 (a)  Placement counts vs the committed sidecar / placement_enumerate.py #
# --------------------------------------------------------------------------- #
@_needs_hw
def test_placement_counts_match_sidecar():
    """§6.3 (counts): ``build_placement`` over the FULL d7 round reproduces the committed slot counts.

    A pure ENUMERATION (no density matrix is built — only the dataclass program), so it runs over all
    49 data / 48 measure / 156 spectator edges cheaply. Cross-checked against
    ``outputs/placement_enumerate_results.json`` (the stage-0 enumerator's committed sidecar):
    CZ incidences = 168, data-1q over-rotation slots = 196, spectator slots = 156.
    """
    round_schedule, data, measure, adjacency, _coord, _supp = _parse_real_round()
    assert len(data) == EXPECT_DATA, f"parsed {len(data)} data qubits, expected {EXPECT_DATA}"

    # full-patch placement: window_data = all data, ancilla = all measure, adjacency = all edges.
    # A pure enumeration over the dataclass program — no 2**97 density matrix is built.
    placement = build_placement(round_schedule, sorted(data), sorted(measure), adjacency)
    slots = placement.slots()
    # Count by the §3 slot classes (imported SLOT_* constants — follows B if the strings are renamed).
    n_cz = sum(1 for s in slots if s.slot_class == SLOT_CZ)
    n_oneq = sum(1 for s in slots if s.slot_class == SLOT_ONEQ)
    n_spec = sum(1 for s in slots if s.slot_class == SLOT_SPECTATOR)

    # sidecar cross-check (the committed ground truth from outputs/placement_enumerate.py).
    side = json.loads(_SIDECAR.read_text(encoding="utf-8"))
    assert side["class2_cz"]["cz_data_measure_incidences_per_round"] == EXPECT_CZ_INCIDENCES
    assert side["class1_oneq"]["data_1q_slots_per_round"] == EXPECT_DATA_1Q_SLOTS
    assert side["class3_spectator"]["data_data_share_stabilizer_pairs"] == EXPECT_SPECTATOR_PAIRS

    assert n_cz == EXPECT_CZ_INCIDENCES, f"CZ slots {n_cz} != sidecar {EXPECT_CZ_INCIDENCES}"
    assert n_oneq == EXPECT_DATA_1Q_SLOTS, f"data-1q slots {n_oneq} != sidecar {EXPECT_DATA_1Q_SLOTS}"
    assert n_spec == EXPECT_SPECTATOR_PAIRS, f"spectator slots {n_spec} != sidecar {EXPECT_SPECTATOR_PAIRS}"

    # Cross-check the CZ count against the ideal CZ GATE steps too (GateStep.name is semantically
    # forced, independent of the slot-class naming) — a second angle on the 168 figure.
    n_cz_gates = sum(1 for g in placement.gates() if g.name == "CZ")
    assert n_cz_gates == EXPECT_CZ_INCIDENCES, f"CZ gate steps {n_cz_gates} != {EXPECT_CZ_INCIDENCES}"

    # Field DOF (§5), from PUBLIC SlotStep fields (no private state): distinct support-tuples of the
    # coherent classes — one per data qubit (1q) and one per (data,data) edge (spectator). These are
    # the tie-key supports WindowChannel shares across overlapping windows.
    oneq_supports = {s.global_support for s in slots if s.slot_class == SLOT_ONEQ}
    spec_supports = {s.global_support for s in slots if s.slot_class == SLOT_SPECTATOR}
    assert len(oneq_supports) == EXPECT_DATA, f"distinct 1q supports {len(oneq_supports)} != {EXPECT_DATA}"
    assert len(spec_supports) == EXPECT_SPECTATOR_PAIRS, (
        f"distinct spectator supports {len(spec_supports)} != {EXPECT_SPECTATOR_PAIRS}"
    )
    # The de-duplicated learnable θ leaves cover at least the coherent field DOF (1q + spectator).
    # NOTE (register bound, §3): a full-patch WindowChannel (97 qubits) MUST NOT be constructed — that
    # is the forbidden data + ALL-ancilla register (4**97 density matrix); WindowChannel now refuses it
    # at construction (n > MAX_WINDOW_QUBITS), and CPU is no longer an escape (GPU-only HARD gate). The
    # θ-tie count is a pure function of placement.slots() (one leaf per (mech_type, global_support)), so
    # we count the distinct tie keys directly from the PUBLIC placement — exactly WindowChannel's tying
    # rule — without instantiating any register. Per-window construction at the bounded scale is
    # exercised on cuda by the §6.1/6.5/6.6 window tests and the interior-window memory-bound test.
    tie_keys = {(s.mech_type, s.global_support) for s in slots}
    assert len(tie_keys) >= EXPECT_DATA + EXPECT_SPECTATOR_PAIRS, (
        f"too few tied θ leaves ({len(tie_keys)}) for the coherent field DOF "
        f"(>= {EXPECT_DATA + EXPECT_SPECTATOR_PAIRS})"
    )

    # POSITIVE CONTROL: drop ONE spectator edge ⇒ the spectator slot count MUST fall to 155, so the
    # "== 156" check has teeth (it is not satisfied by an arbitrary adjacency).
    broken_adj = set(adjacency)
    broken_adj.discard(next(iter(adjacency)))
    broken_placement = build_placement(round_schedule, sorted(data), sorted(measure), broken_adj)
    broken_spec = sum(1 for s in broken_placement.slots() if s.slot_class == SLOT_SPECTATOR)

    def _spec_ok(n_spec_count: int) -> bool:
        return n_spec_count == EXPECT_SPECTATOR_PAIRS

    assert _spec_ok(n_spec), "spectator-count predicate wrongly rejected the true placement"
    _assert_flags(_spec_ok, broken_spec, what="adjacency with one spectator edge dropped (155 != 156)")


# --------------------------------------------------------------------------- #
# §6.1  CPTP — the COMPOSED window map (real small window)                     #
# --------------------------------------------------------------------------- #
def _window_zero_state(n: int) -> torch.Tensor:
    dim = 2 ** n
    rho = torch.zeros((dim, dim), dtype=CDTYPE, device=DEVICE)
    rho[0, 0] = 1.0
    return rho


def _random_window_rho(n: int, *, seed: int = 0) -> torch.Tensor:
    """A random valid density matrix on ``n`` qubits (PSD, unit trace) — a non-trivial probe state.

    The CPU ``torch.Generator`` below is the §3-ALLOWED exception (an RNG-seed generator); its sampled
    tensor is moved to ``DEVICE`` (the final ``.to(DEVICE)``), so all model compute on this ρ runs on
    cuda. This is NOT a CPU model-compute path.
    """
    gen = torch.Generator(device="cpu").manual_seed(seed)
    dim = 2 ** n
    a = torch.randn(dim, dim, generator=gen, dtype=torch.float64)
    b = torch.randn(dim, dim, generator=gen, dtype=torch.float64)
    m = (a + 1j * b).to(CDTYPE)
    rho = m @ m.conj().transpose(-1, -2)
    rho = rho / torch.trace(rho).real
    return rho.to(DEVICE)


@_needs_hw
def test_cptp_composed_window_map_is_cptp():
    """§6.1 (composed): the full single-round window map is TP and (operationally) CP.

    Built on a small REAL window (a corner + its most window-native ancilla, register ≤ budget) so the
    ``2**n`` density matrix is cheap. TP: trace is preserved on a random ρ (the composed map's own
    completeness). CP: ``apply`` is a composition of CPTP steps (``apply_channel_local`` /
    ``apply_kraus`` of CPTP-by-construction mechanism Kraus + CPTP reset/measure), so the full map is
    CP by construction; we verify the OPERATIONAL witness (every PSD input → PSD output) on an
    Herm-spanning IC set + random PSD probes, which catches a composition bug that broke positivity.
    (The exact Choi-PSD of the n-qubit map needs ``2**(2n)`` — out of budget; per-mechanism Choi-PSD
    is checked separately above, so the structural CP guarantee is covered end to end.)
    """
    round_schedule, data, measure, adjacency, coord_of, supp = _parse_real_round()
    window_data, ancilla, center = _small_real_window(data, measure, adjacency, coord_of, supp)
    placement = build_placement(round_schedule, window_data, ancilla, adjacency)
    n = placement.n_qubits
    assert n <= _WINDOW_QUBIT_BUDGET, f"real window too large for the unit-test budget (n={n})"

    chan = WindowChannel(window_data, ancilla, round_schedule, placement, device=DEVICE)

    # ---- TP: trace preserved on a random valid ρ (within float64 round-off). ----
    rho = _random_window_rho(n, seed=3)
    out = chan.apply(rho)
    tr_in = float(torch.trace(rho).real)
    tr_out = float(torch.trace(out.detach()).real)  # detach: θ leaves require grad (warning-clean read)
    assert abs(tr_out - tr_in) < 1e-9, f"composed map not trace-preserving: {tr_in} -> {tr_out}"

    # ---- CP (operational witness): every PSD input maps to a PSD output. ----
    min_eigs = []
    for probe in list(_ic_inputs(2 ** n)) + [_random_window_rho(n, seed=7), _window_zero_state(n)]:
        o = chan.apply(probe)
        o = 0.5 * (o + o.conj().transpose(-1, -2))
        min_eigs.append(float(torch.linalg.eigvalsh(o).min()))
    worst = min(min_eigs)
    assert worst >= -1e-9, f"composed map produced an indefinite output (min eig {worst:.3e}) — not CP"

    # POSITIVE CONTROL #1 (TP): a map that loses trace must be flagged by the trace-preservation
    # predicate — proving the TP check reacts to a real violation.
    def _tp_ok(pair) -> bool:
        ti, to = pair
        return abs(to - ti) < 1e-9

    broken = (tr_in, tr_out * 1.5)  # a map that lost 1/3 of the trace
    assert _tp_ok((tr_in, tr_out)), "TP predicate wrongly rejected the true composed map"
    _assert_flags(_tp_ok, broken, what="composed map that loses trace (non-TP)")

    # POSITIVE CONTROL #2 (CP witness liveness): the min-eigenvalue positivity test must flag an
    # indefinite output — i.e. if the composition HAD broken positivity, this leg would fire. Feed the
    # same predicate an explicitly indefinite Hermitian matrix (the transpose-map Choi / SWAP).
    def _output_psd(o: torch.Tensor) -> bool:
        herm = 0.5 * (o + o.conj().transpose(-1, -2))
        return float(torch.linalg.eigvalsh(herm).min()) >= -1e-9

    assert _output_psd(chan.apply(rho)), "CP-witness predicate wrongly rejected a valid output"
    _assert_flags(_output_psd, _indefinite_choi(), what="indefinite output state (broken positivity)")


# --------------------------------------------------------------------------- #
# §3 Register bound — a REAL INTERIOR window (9 data) on cuda, peak-memory proof #
# --------------------------------------------------------------------------- #
# §3 register-bound memory ceiling for the interior-window proof (epistemic tag (c): a tripwire — the
# 13-qubit full-in register's autograd/eigvalsh peak must sit comfortably under this). 16 GB is < half
# the 5090's 34 GB; the FORBIDDEN 25-qubit register would need ~1e6 GB, so this gate has real teeth.
_INTERIOR_PEAK_BUDGET_GB = 16.0


@pytest.mark.slow
@pytest.mark.skipif(
    not os.environ.get("QEC_TWIN_HW_SLOW"),
    reason="opt-in heavy run: 13-qubit interior-window autograd/eigvalsh on cuda (enable QEC_TWIN_HW_SLOW)",
)
@_needs_hw
def test_interior_window_register_memory_bound():
    """§3 register bound, REAL interior scale: a 9-data window's FULL-IN register is GPU-feasible.

    This is the proof the register bound holds at REAL interior scale ON GPU — not dodged to CPU and
    not capped to a 4-data corner. It builds the radius-1 ball of an INTERIOR data qubit (9 data) with
    its §3 FULL-IN ancilla (support ⊆ the window data; seam ancilla deferred to step-4), giving a
    13-qubit register on the real d7 covering (``outputs/window_register_probe.py``), then exercises the
    model path on cuda while tracking ``torch.cuda.max_memory_allocated()`` in two parts:
      * the REGISTER-BOUND PROOF — the forward ``apply`` + ``eigvalsh`` density-matrix path (what the §3
        bound governs) must peak under ``_INTERIOR_PEAK_BUDGET_GB``, PROVING the full-in register keeps
        an interior window feasible where the forbidden data + ALL-touching register (~25 q, 4**25 ≈
        1e6 GB) is not;
      * the GRADIENT CAPABILITY — autograd through the full window circuit yields a finite θ gradient
        on cuda (its backward-graph memory is reported under a generous device ceiling, not the tight
        forward budget, since a deep-circuit backward is inherently graph-heavy and is not the
        register-bound metric).
    A closing positive control asserts the forbidden oversized register is REFUSED at construction.
    """
    round_schedule, data, measure, adjacency, coord_of, supp = _parse_real_round()
    window_data, ancilla, center, n_forbidden = _interior_real_window(
        data, measure, adjacency, coord_of, supp
    )
    placement = build_placement(round_schedule, window_data, ancilla, adjacency)
    n = placement.n_qubits
    # the §3 bound: an interior 9-data full-in register is ≤ MAX_WINDOW_QUBITS (measured 13).
    assert len(window_data) == 9, f"interior window must have 9 data; got {len(window_data)}"
    assert n <= MAX_WINDOW_QUBITS, f"interior full-in register n={n} exceeds §3 bound {MAX_WINDOW_QUBITS}"
    # the forbidden alternative is genuinely infeasible (sanity that we are testing the right thing).
    assert n_forbidden >= 20, (
        f"the data + ALL-touching register should be ~25 qubits (infeasible); got {n_forbidden}"
    )

    chan = WindowChannel(window_data, ancilla, round_schedule, placement, device=DEVICE)
    assert chan.device.type == "cuda", "interior WindowChannel must live on cuda (GPU-only HARD gate)"

    # set a non-trivial θ on every leaf so the forward is a genuine noisy circuit (not the θ=0 identity).
    params = chan.parameters()
    assert len(params) > 0, "interior window has no learnable θ leaves"
    with torch.no_grad():
        for j, leaf in enumerate(params):
            leaf.copy_(torch.tensor(0.03 + 0.005 * (j % 11), dtype=leaf.dtype, device=leaf.device))

    rho = _random_window_rho(n, seed=13)
    assert rho.device.type == "cuda", "probe ρ must be on cuda"

    # ---- REGISTER-BOUND PROOF: the forward apply + eigvalsh model-compute path (the path the §3
    # register bound governs) stays under the stated GPU budget at real interior scale. Measured in
    # no_grad so the peak reflects the DENSITY-MATRIX path (no retained autograd graph) — this is what
    # proves n=13 is feasible where the forbidden n=25 register is not. ----
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(DEVICE)
    with torch.no_grad():
        out = chan.apply(rho)
        assert out.device.type == "cuda" and out.shape == (2 ** n, 2 ** n)
        herm = 0.5 * (out + out.conj().transpose(-1, -2))
        min_eig = float(torch.linalg.eigvalsh(herm).min())  # CP witness at interior scale (on cuda)
        tr = float(torch.trace(out).real)
    assert min_eig >= -1e-8, f"interior composed map produced an indefinite output (min eig {min_eig:.3e})"
    assert abs(tr - 1.0) < 1e-7, "interior composed map not trace-preserving"
    fwd_peak_gb = torch.cuda.max_memory_allocated(DEVICE) / 1e9
    assert fwd_peak_gb < _INTERIOR_PEAK_BUDGET_GB, (
        f"interior-window forward+eigvalsh peak GPU memory {fwd_peak_gb:.3f} GB exceeded the §3 budget "
        f"{_INTERIOR_PEAK_BUDGET_GB} GB — the register bound is not holding at real interior scale"
    )

    # ---- GRADIENT CAPABILITY at interior scale (on cuda): autograd through the full window circuit
    # produces a finite θ gradient. Memory here is the BACKWARD GRAPH of a deep circuit (inherently
    # larger than the forward density-matrix path and NOT the register-bound metric), so it is reported
    # with its own generous ceiling (most of the 5090) rather than the tight forward budget. ----
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(DEVICE)
    loss = chan.apply(rho).real.sum()
    (grad,) = torch.autograd.grad(loss, params[0], allow_unused=True)
    assert grad is not None and torch.isfinite(grad).all(), "interior-scale θ gradient is None / non-finite"
    grad_peak_gb = torch.cuda.max_memory_allocated(DEVICE) / 1e9
    _free_now, total_mem = torch.cuda.mem_get_info(DEVICE)
    grad_ceiling_gb = 0.9 * total_mem / 1e9  # capability ceiling: must not exhaust the device
    assert grad_peak_gb < grad_ceiling_gb, (
        f"interior-window backward peak {grad_peak_gb:.3f} GB exceeded the device capability ceiling "
        f"{grad_ceiling_gb:.3f} GB (autograd through the deep circuit did not fit)"
    )

    print(
        f"[interior-bound] center={center} data={len(window_data)} full_in_ancilla={len(ancilla)} "
        f"n={n} (forbidden data+all-ancilla n={n_forbidden}) | "
        f"forward+eigvalsh peak={fwd_peak_gb:.3f} GB (budget {_INTERIOR_PEAK_BUDGET_GB} GB) | "
        f"backward peak={grad_peak_gb:.3f} GB (ceiling {grad_ceiling_gb:.1f} GB)",
        flush=True,
    )

    # POSITIVE CONTROL (bound has teeth): the FORBIDDEN data + ALL-touching-ancilla register must be
    # REFUSED at construction (n_forbidden > MAX_WINDOW_QUBITS), never silently built — proving the
    # §3 guard fires instead of OOMing. We construct the placement for the oversized register and
    # assert WindowChannel raises before any density matrix is allocated.
    all_touching = sorted(m for m, s in supp.items() if set(s) & set(window_data))
    forbidden_placement = build_placement(round_schedule, window_data, all_touching, adjacency)
    assert forbidden_placement.n_qubits == n_forbidden
    with pytest.raises((ValueError, MemoryError)):
        WindowChannel(window_data, all_touching, round_schedule, forbidden_placement, device=DEVICE)


# --------------------------------------------------------------------------- #
# §6.5  ρ_BC self-consistency — WindowChannel.rho_bc vs brute-force trace      #
# --------------------------------------------------------------------------- #
def _brute_partial_trace(rho: torch.Tensor, keep_local: list[int], n: int) -> torch.Tensor:
    """Independent reference partial trace (einsum reshape) — NOT window_diagnostics.partial_trace.

    Reshapes ρ to a 2n-leg tensor (qubit 0 = most significant, the circuit_sim convention) and
    contracts every traced leg's bra/ket pair. The witness for ρ_BC: a from-scratch implementation
    so the test does not inherit a bug in D's helper.
    """
    keep_local = [int(q) for q in keep_local]
    traced = [q for q in range(n) if q not in keep_local]
    t = rho.reshape([2] * (2 * n))
    # contract traced legs pairwise (row leg q at axis q, col leg q at axis n+q).
    # Move to an explicit einsum over labels.
    row_labels = [chr(ord('a') + q) for q in range(n)]
    col_labels = [chr(ord('A') + q) for q in range(n)]
    for q in traced:
        col_labels[q] = row_labels[q]  # tie traced row==col => trace that qubit
    out_row = [row_labels[q] for q in keep_local]
    out_col = [col_labels[q] for q in keep_local]
    subscripts = "".join(row_labels + col_labels) + "->" + "".join(out_row + out_col)
    k = len(keep_local)
    reduced = torch.einsum(subscripts, t).reshape(2 ** k, 2 ** k)
    return reduced


@_needs_hw
def test_rho_bc_matches_bruteforce_partial_trace():
    """§6.5: ``WindowChannel.rho_bc`` equals an independent brute-force partial trace of ``apply(ρ)``."""
    round_schedule, data, measure, adjacency, coord_of, supp = _parse_real_round()
    window_data, ancilla, center = _small_real_window(data, measure, adjacency, coord_of, supp)
    placement = build_placement(round_schedule, window_data, ancilla, adjacency)
    n = placement.n_qubits
    chan = WindowChannel(window_data, ancilla, round_schedule, placement, device=DEVICE)

    rho = _random_window_rho(n, seed=11)
    overlap = window_data[:2]  # keep two real window-data qubits as the seam overlap region

    got = chan.rho_bc(rho, overlap)

    # brute-force reference: evolve then trace to the SAME local indices rho_bc keeps.
    evolved = chan.apply(rho)
    keep_local = [placement.local_of[g] for g in overlap]
    ref = _brute_partial_trace(evolved, keep_local, n)

    diff = float((got - ref).detach().abs().max())  # detach: θ leaves require grad (warning-clean read)
    assert got.shape == (2 ** len(overlap), 2 ** len(overlap)), f"rho_bc shape {tuple(got.shape)} wrong"
    assert diff < 1e-9, f"rho_bc disagrees with brute-force partial trace (max abs diff {diff:.3e})"

    # trace is preserved by the reduction (ρ_BC is a valid reduced state).
    assert abs(float(torch.trace(got).real) - float(torch.trace(evolved.detach()).real)) < 1e-9

    # POSITIVE CONTROL: keeping a DIFFERENT qubit set yields a DIFFERENT reduced state — so the
    # equality check + the partial trace genuinely discriminate which qubits are kept. The control runs
    # on the random INPUT ρ (not the post-round `evolved` state): after a full syndrome-extraction round
    # the data qubits end maximally mixed (reset + measurement dephasing), so every 2-data marginal of
    # `evolved` is I/4 and a wrong-keep would be vacuously equal — the round physics, not the reduction,
    # would defeat the control. On the generic input ρ the marginals differ, so the SAME machinery
    # (_brute_partial_trace + the equality predicate) is exercised with real resolving power.
    keep_a = [placement.local_of[g] for g in window_data[:2]]
    keep_b = [placement.local_of[window_data[2]], placement.local_of[window_data[3]]] \
        if len(window_data) >= 4 else [keep_a[0], next(q for q in range(n) if q not in keep_a)]
    red_a = _brute_partial_trace(rho, keep_a, n)         # the correct reduction of the input
    red_b = _brute_partial_trace(rho, keep_b, n)         # a DIFFERENT kept set on the same input
    assert float((red_a - red_b).abs().max()) > 1e-6, (
        "control precondition: the input ρ's two 2-qubit marginals coincide — pick a seed where they "
        "differ so the wrong-keep control is non-vacuous"
    )

    def _matches_red_a(reference: torch.Tensor) -> bool:
        return reference.shape == red_a.shape and float((red_a - reference).abs().max()) < 1e-9

    # the equality check accepts the matching reduction and REJECTS the wrong-keep one (it has teeth).
    assert _matches_red_a(red_a), "partial-trace equality wrongly rejected the correct reduction"
    _assert_flags(_matches_red_a, red_b, what="partial trace keeping the wrong qubits")


# --------------------------------------------------------------------------- #
# §6.6  Gradient — WindowChannel.sensitivity vs central finite difference      #
# --------------------------------------------------------------------------- #
@_needs_hw
def test_gradient_sensitivity_matches_finite_difference():
    """§6.6: ``sensitivity(ρ, i)`` == central FD of the matching scalar functional of ``apply(ρ)``.

    ``WindowChannel.sensitivity`` returns ``gr + 1j*gi`` where ``gr = Σ_kl ∂Re(out_kl)/∂θ_i`` and
    ``gi = Σ_kl ∂Im(out_kl)/∂θ_i`` (the §10 hook: split real/imag autograd of the output, summed by
    the all-ones grad_outputs). The matching finite-difference target is therefore the central
    difference of ``f_re(θ) = Σ Re(apply)`` and ``f_im(θ) = Σ Im(apply)`` w.r.t. the i-th θ leaf.
    """
    round_schedule, data, measure, adjacency, coord_of, supp = _parse_real_round()
    window_data, ancilla, center = _small_real_window(data, measure, adjacency, coord_of, supp)
    placement = build_placement(round_schedule, window_data, ancilla, adjacency)
    n = placement.n_qubits
    chan = WindowChannel(window_data, ancilla, round_schedule, placement, device=DEVICE)
    params = chan.parameters()
    assert len(params) > 0, "window has no learnable θ leaves to differentiate"

    # Set a realistic NON-TRIVIAL θ on every leaf: B initialises leaves to 0 (= no noise, a degenerate
    # gradient probe). A small distinct angle per leaf makes the map a genuine noisy circuit and the
    # ∂apply/∂θ generically non-zero — the meaningful regime for the sensitivity hook.
    with torch.no_grad():
        for j, leaf in enumerate(params):
            leaf.copy_(torch.tensor(0.05 + 0.01 * (j % 7), dtype=leaf.dtype, device=leaf.device))

    rho = _random_window_rho(n, seed=5)

    def _functionals_at(leaf: torch.Tensor, value: float) -> tuple[float, float]:
        saved = leaf.detach().clone()
        with torch.no_grad():
            leaf.copy_(torch.tensor(value, dtype=leaf.dtype, device=leaf.device))
        with torch.no_grad():
            out = chan.apply(rho)
            f_re = float(out.real.sum())
            f_im = float(out.imag.sum())
        with torch.no_grad():
            leaf.copy_(saved)
        return f_re, f_im

    # Differentiate a couple of representative leaves (first coherent + first non-trivial index).
    idxs = [0]
    if len(params) > 1:
        idxs.append(len(params) // 2)

    for i in idxs:
        leaf = params[i]
        theta0 = float(leaf.detach())
        # sensitivity returns the per-element Jacobian ∂out_kl/∂θ_i SHAPED LIKE THE OUTPUT (§10:
        # (2**n, 2**n)). The FD targets below are derivatives of the SUMMED functionals Σ Re(apply) /
        # Σ Im(apply); by linearity ∂(Σ_kl Re out_kl)/∂θ = Σ_kl ∂Re(out_kl)/∂θ = analytic.real.sum().
        analytic = chan.sensitivity(rho, i)
        assert analytic.shape == (2 ** n, 2 ** n), (
            f"sensitivity must return the output-shaped Jacobian (2**n, 2**n); got {tuple(analytic.shape)}"
        )
        gr_an = float(analytic.real.sum())
        gi_an = float(analytic.imag.sum())

        re_p, im_p = _functionals_at(leaf, theta0 + FD_STEP)
        re_m, im_m = _functionals_at(leaf, theta0 - FD_STEP)
        gr_fd = (re_p - re_m) / (2 * FD_STEP)
        gi_fd = (im_p - im_m) / (2 * FD_STEP)

        assert abs(gr_an - gr_fd) < GRAD_TOL, (
            f"θ[{i}] Re-gradient mismatch: autograd {gr_an:.6e} vs FD {gr_fd:.6e}"
        )
        assert abs(gi_an - gi_fd) < GRAD_TOL, (
            f"θ[{i}] Im-gradient mismatch: autograd {gi_an:.6e} vs FD {gi_fd:.6e}"
        )

    # POSITIVE CONTROL: the FD value must REJECT a deliberately wrong analytic gradient (2x the true
    # one) — proving the gradient check has resolving power and is not vacuously satisfied. (Skip the
    # degenerate case where the true gradient is ~0, where 2x is also ~0.)
    leaf = params[idxs[0]]
    theta0 = float(leaf.detach())
    re_p, im_p = _functionals_at(leaf, theta0 + FD_STEP)
    re_m, im_m = _functionals_at(leaf, theta0 - FD_STEP)
    gr_fd = (re_p - re_m) / (2 * FD_STEP)
    if abs(gr_fd) > 1e-3:
        def _grad_ok(claimed: float) -> bool:
            return abs(claimed - gr_fd) < GRAD_TOL
        assert _grad_ok(gr_fd), "gradient predicate wrongly rejected the matching FD value"
        _assert_flags(_grad_ok, 2.0 * gr_fd, what="analytic gradient inflated 2x (wrong slope)")


# --------------------------------------------------------------------------- #
# §6.6 trap  Fault injection uses a Pauli *_ERROR channel, never a Pauli gate  #
# --------------------------------------------------------------------------- #
@_needs_hw
def test_fault_injection_uses_error_channel_not_gate():
    """§6.6 trap (window_covering_RESULTS §4 / ``inject_debug.py``): a teacher fault MUST be injected
    as a Pauli ``*_ERROR(1.0)`` *channel*, NEVER a deterministic Pauli *gate*.

    ``compile_detector_sampler`` absorbs a deterministic Pauli GATE into the intended-circuit
    reference (the detector footprint is 0 — the fault becomes invisible), whereas an ``X_ERROR(1.0)``
    error CHANNEL flips its stabilizers and is detected. This test demonstrates the trap on the REAL
    d7 noiseless circuit and asserts (a) the gate path is footprint-0 (the trap) and (b) the
    error-channel path is footprint > 0 (the correct injection) — so any fault-injection teacher in
    the step-2/3 self-checks that used a gate would be caught here.
    """
    import stim

    leaf = _hw_root()
    base = stim.Circuit.from_file(str(leaf))
    fc = base.flattened()

    # pick a real DATA qubit (measured once) to inject on.
    meas_count: dict[int, int] = {}
    for inst in fc:
        if inst.name in _MEAS_NAMES:
            for t in inst.targets_copy():
                if t.is_qubit_target:
                    meas_count[t.qubit_value] = meas_count.get(t.qubit_value, 0) + 1
    data_qubits = sorted(q for q, c in meas_count.items() if c == 1)
    victim = data_qubits[len(data_qubits) // 2]

    # insert location: right after the FIRST reset / state-prep block (early in round 1), so a data
    # Pauli propagates through the full circuit and reliably flips its stabilizers' detectors — the
    # faithful injection point of `inject_debug.py` (window_covering_RESULTS §4).
    insert_at = 1
    for i, inst in enumerate(fc):
        if inst.name in {"R", "RX", "RY", "RZ"}:
            insert_at = i + 1
            break

    def _footprint(injected_name: str, *, as_gate: bool) -> int:
        c = stim.Circuit()
        for i, inst in enumerate(fc):
            if i == insert_at:
                if as_gate:
                    c.append("X", [victim])                 # the TRAP: deterministic Pauli GATE
                else:
                    c.append("X_ERROR", [victim], 1.0)      # the CORRECT injection: error CHANNEL
            c.append(inst)
        # detector footprint = number of detectors that fire with the injection present (single shot;
        # the only stochastic element is X_ERROR(1.0), which is deterministic at p=1).
        sampler = c.compile_detector_sampler()
        dets = sampler.sample(shots=1)
        return int(dets.sum())

    gate_footprint = _footprint("X", as_gate=True)
    error_footprint = _footprint("X", as_gate=False)

    # (a) the TRAP: a deterministic Pauli gate is absorbed into the reference => footprint 0.
    assert gate_footprint == 0, (
        f"expected the Pauli-GATE absorption trap (footprint 0); got {gate_footprint} — the trap "
        f"premise (window_covering_RESULTS §4) no longer holds on this circuit"
    )
    # (b) the CORRECT injection: an X_ERROR(1.0) channel flips detectors => footprint > 0.
    assert error_footprint > 0, (
        f"X_ERROR(1.0) channel produced footprint {error_footprint}; a real data fault must flip >=1 "
        f"detector (it is NOT being absorbed)"
    )

    # POSITIVE CONTROL: the discriminator "footprint > 0 distinguishes channel from gate" must REJECT
    # the gate footprint — i.e. the test genuinely separates the correct path from the trap.
    def _is_visible_injection(footprint: int) -> bool:
        return footprint > 0

    assert _is_visible_injection(error_footprint), "discriminator wrongly rejected the error channel"
    _assert_flags(_is_visible_injection, gate_footprint, what="Pauli GATE injection (absorbed, footprint 0)")


# --------------------------------------------------------------------------- #
# §3 GPU-only HARD gate — data-free guard (always runs; no hardware needed)     #
# --------------------------------------------------------------------------- #
def test_window_channel_is_gpu_only():
    """§3 "GPU-only (HARD gate)": WindowChannel defaults to cuda and REFUSES a CPU device.

    A cheap, data-free guard that the GPU-only contract is enforced at the object boundary (so the
    defect this build removes — running the window model on CPU to dodge memory — cannot reappear). A
    minimal real-shaped placement is built from a tiny synthetic single-CZ schedule (this checks the
    DEVICE POLICY, not physics — the faithful-circuit checks use the real d7 round and need the data),
    then: (a) the default device is cuda; (b) an explicit ``device="cpu"`` raises.
    """
    # a minimal 2-qubit (1 data + 1 measure) schedule with one in-window CZ — enough to make a slot.
    round_schedule = [{"name": "CZ", "qubits": [0, 1], "pairs": [(0, 1)], "layer": 0}]
    window_data, ancilla = [0], [1]
    placement = build_placement(round_schedule, window_data, ancilla, adjacency=set())
    assert placement.n_qubits == 2 and len(placement.slots()) >= 1

    # (a) default device is cuda (no cuda-if-available-else-cpu fallback).
    chan = WindowChannel(window_data, ancilla, round_schedule, placement)
    assert chan.device.type == "cuda", f"WindowChannel default device must be cuda; got {chan.device}"
    chan_explicit = WindowChannel(window_data, ancilla, round_schedule, placement, device=DEVICE)
    assert chan_explicit.device.type == "cuda"

    # (b) an explicit CPU device is refused (the GPU-only HARD gate has teeth).
    with pytest.raises(RuntimeError):
        WindowChannel(window_data, ancilla, round_schedule, placement, device="cpu")

    # (c) the register bound is enforced: a register over MAX_WINDOW_QUBITS is refused before any
    # density matrix is built (synthetic oversized schedule; pure dataclass enumeration).
    big = MAX_WINDOW_QUBITS + 1
    big_schedule = [{"name": "CZ", "qubits": list(range(big)),
                     "pairs": [(2 * i, 2 * i + 1) for i in range(big // 2)], "layer": 0}]
    big_data = list(range(big))
    big_placement = build_placement(big_schedule, big_data, [], adjacency=set())
    assert big_placement.n_qubits == big
    with pytest.raises((ValueError, MemoryError)):
        WindowChannel(big_data, [], big_schedule, big_placement, device=DEVICE)

    print(
        f"[gpu-gate] WindowChannel default device=cuda OK; CPU refused; "
        f"register bound MAX_WINDOW_QUBITS={MAX_WINDOW_QUBITS} enforced",
        flush=True,
    )


# --------------------------------------------------------------------------- #
# Smoke summary (printed evidence; scripted-execution discipline)             #
# --------------------------------------------------------------------------- #
def test_smoke_contract_surface_present():
    """Cheap data-free smoke: the §10 contract surface is importable and shaped as specified.

    Confirms this test file links against the concurrently-built siblings (A/B/D) at the frozen §10
    signatures before the heavier checks run.
    """
    # A — dictionary registries with the §10 keys.
    assert set(MECH_1Q) == {
        "rx", "ry", "rz", "amp_damp", "phase_damp", "pauli_x", "pauli_y", "pauli_z",
        "thermal", "custom_nonpauli", "leakage",
    }, f"MECH_1Q keys drifted from §10: {sorted(MECH_1Q)}"
    assert set(MECH_2Q) == {
        "rzz", "rxx", "ryy", "rxx_ryy", "cphase", "two_pauli_xy", "two_pauli_zx", "two_pauli_zy",
        "depol2", "corr_relax",
    }, f"MECH_2Q keys drifted from §10: {sorted(MECH_2Q)}"

    # D — diagnostics callables present.
    for fn in ("pauli_basis", "ptm", "coherence_budget", "choi_min_eig", "partial_trace"):
        assert hasattr(wd, fn), f"window_diagnostics missing §10 callable {fn!r}"

    # B — object + factory present with the §10 methods.
    for meth in ("apply", "rho_bc", "coherence_budget", "parameters", "sensitivity"):
        assert hasattr(WindowChannel, meth), f"WindowChannel missing §10 method {meth!r}"
    assert callable(build_placement), "build_placement missing"

    # a one-shot sanity: a 1q coherent builder yields a CPTP, coherent (2,2)-or-(1,2,2) Kraus.
    k = MECH_1Q["rz"](_theta(1), device=DEVICE)
    assert k.shape[-2:] == (2, 2) and float(tp_residual(k)) < TP_TOL
    print(
        f"[smoke] device={DEVICE} dtype={CDTYPE} | MECH_1Q={len(MECH_1Q)} MECH_2Q={len(MECH_2Q)} "
        f"| diagnostics+WindowChannel surface OK",
        flush=True,
    )


if __name__ == "__main__":
    # Scripted-execution discipline: a runnable smoke entry (the integrator drives the full suite via
    # pytest). Runs only the data-free contract smoke so a bare invocation never needs the dataset.
    test_smoke_contract_surface_present()
    print("OK: contract-surface smoke passed (run `pytest tests/test_window_channel.py` for the full spec).")
