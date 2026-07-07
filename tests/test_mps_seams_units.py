"""Wave-2.6 ISOLATED per-unit tests for the A3 ``mps_forward.py`` seams (§5).

Binding contract: ``docs/twin_validation/wave2_6_unit_test_contract.md`` §5 (A3),
the K-catalog (§1), the DEVIOUS-TEST STANDARD, and the orchestrator decisions §10
(item 3: ``_leak_sample`` value contract is CPU-only via a STUB ``mps``) + the v2
red-team amendments §11 (AM-1 fallback recipe, AM-2 stub completeness).

These are ADDITIVE to the KEPT integration gates in ``tests/test_shotset_records.py``
(``test_am5_leak_sample_tiebreak_registry`` on a REAL GPU MPS,
``test_a3_attach_layout_pure_addition``, ``test_a3_mps_from_statevector_roundtrip``):
the units here isolate the exception surfaces + branch legs those cannot reach.

Units covered (§5.1/5.2/5.3):
  * ``MpsLeakageForward._leak_sample`` -- the RETURNED branch index (value contract
    ONLY, not the trajectory body). Driven CPU-only via a STUB ``mps`` whose
    ``local_expectation_canonical`` returns a CONSTRUCTED ``pk`` vector; ``gate_`` /
    ``multiply_`` are no-ops (AM-2). Reaches the FALLBACK leg (mps_forward.py 660->665)
    deterministically with ``u`` one ULP above 1.0 (AM-1: ``u=1.0`` breaks INSIDE the
    loop at the last k; the fallback needs ``u`` slightly ABOVE 1.0).
  * ``MpsLeakageForward.attach_layout`` -- the Mapping ``TypeError`` (mps_forward.py:458)
    + non-permutation ``ValueError`` (mps_forward.py:464) + the INVERSE binding.
  * module-level ``mps_from_statevector`` -- non-identity-order round-trip (CPU quimb).

CPU-ONLY. ``attach_layout`` / ``mps_from_statevector`` need ``quimb`` importable (the
``MpsLeakageForward.__init__`` imports ``quimb.tensor``) but NOT cuda (device="cpu");
gate with ``importorskip`` (matching ``test_shotset_records.py``), NOT ``requires_cuda``.
The ``_leak_sample`` value contract uses a STUB mps and needs NO quimb + NO cuda.
"""

from __future__ import annotations

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from qec_twin.forward.scalable import mps_forward as mf
from qec_twin.forward.scalable.mps_forward import PHYS, MpsLeakageForward
from qec_twin.numerics import NUMERICAL_ZERO

from _support.fixtures import assert_control_trips, require_precondition

CDTYPE = torch.complex128
_CPU = torch.device("cpu")


# --------------------------------------------------------------------------- #
# §5.1  _leak_sample -- the RETURNED branch index (value contract, CPU stub).  #
# --------------------------------------------------------------------------- #
class _StubMps:
    """A CPU stub ``mps`` isolating the pure selection/fallback logic of
    ``_leak_sample`` (orchestrator decision §10.3 + AM-2). It returns a CONSTRUCTED
    ``pk`` vector -- one value per ``local_expectation_canonical`` call, in call order
    (the loop reads ``K.conj().T @ K`` for each K but the branch NORM is what the
    selection consumes; the stub supplies those norms directly). ``gate_`` and
    ``multiply_`` are no-ops (the trajectory-application body is out of scope for the
    value contract and covered by the GPU AM-5 gate)."""

    def __init__(self, pk: list[float]) -> None:
        self._pk = [float(p) for p in pk]
        self._i = 0
        self.gate_calls: list = []
        self.multiply_calls: list = []

    class _Scalar:
        def __init__(self, val: float) -> None:
            self.real = float(val)

    def local_expectation_canonical(self, op, site, normalized=False, info=None):
        val = self._pk[self._i]
        self._i += 1
        return _StubMps._Scalar(val)

    def gate_(self, kraus, where=None, contract=True):  # noqa: D401 -- no-op sink
        self.gate_calls.append((where, contract))

    def multiply_(self, inv, spread_over=1):  # noqa: D401 -- no-op sink (via _renormalize)
        self.multiply_calls.append((inv, spread_over))


def _kraus(K: int) -> list[torch.Tensor]:
    """K distinct 3x3 torch tensors so ``kraus[sel]`` indexes for any ``sel`` in
    ``[0, K-1]`` (AM-2: kraus long enough for ``kraus[K-1]``). Content is irrelevant to
    the value contract -- the stub supplies the branch norms -- but they must be real
    tensors so ``gate_`` (a no-op here) receives a valid arg."""
    return [torch.eye(PHYS, dtype=CDTYPE, device=_CPU) * float(k + 1) for k in range(K)]


def _drive_leak(pk: list[float], u: float) -> tuple[int, _StubMps]:
    """Run the REAL ``MpsLeakageForward._leak_sample`` (unbound, on a stub mps) and
    return ``(sel, stub)``. ``MpsLeakageForward.__init__`` imports quimb; the value
    contract must NOT depend on quimb/cuda, so the method is invoked UNBOUND with a
    minimal ``self`` carrying only ``device`` (``_renormalize`` is a staticmethod)."""
    stub = _StubMps(pk)
    kraus = _kraus(len(pk))

    class _SelfShim:
        device = _CPU
        _renormalize = staticmethod(MpsLeakageForward._renormalize)

    sel = MpsLeakageForward._leak_sample(_SelfShim(), stub, kraus, mps_site=1, u=float(u))
    return int(sel), stub


def test_leak_sample_first_branch_u_zero():
    """§5.1 BOUNDARY: ``u=0.0`` -> ``sel=0`` (``target=0 <= cum_0``). Defends K-3
    (the FIRST branch is selected at the lower edge)."""
    sel, _ = _drive_leak([0.2, 0.3, 0.5], 0.0)
    assert sel == 0, f"u=0.0 must select branch 0 (got {sel})"


def test_leak_sample_interior_branch():
    """§5.1 NORMAL: a ``u`` whose ``u*tot`` lands in the SECOND branch's mass -> the
    analytically-expected interior index 1. ASYMMETRIC branch masses (0.2,0.3,0.5) so
    the returned index is uniquely determined by ``u`` (K-6: NOT a permutation-
    symmetric equal-mass set that would hide leg-order bugs)."""
    pk = [0.2, 0.3, 0.5]
    tot = sum(pk)
    # target = 0.35 lands strictly inside branch 1's mass (cum_0=0.2 < 0.35 < cum_1=0.5).
    u = 0.35 / tot
    sel, _ = _drive_leak(pk, u)
    assert sel == 1, f"interior u (target=0.35) must select branch 1 (got {sel})"


def test_leak_sample_last_branch_u_below_one():
    """§5.1 BOUNDARY: ``u`` just below 1.0 -> the LAST branch (K-1), selected INSIDE
    the loop (``target <= final cum`` holds). Distinct from the fallback leg below."""
    sel, _ = _drive_leak([0.2, 0.3, 0.5], 1.0 - 1e-12)
    assert sel == 2, f"u->1^- must select the last branch 2 (got {sel})"


def test_leak_sample_nonstrict_boundary_selects_earlier():
    """§5.1 BOUNDARY (K-3, the NON-STRICT ``<=`` edge): ``u*tot`` landing EXACTLY on
    the branch-0 cumsum boundary selects the EARLIER branch 0 (``<=``, not ``<``). A
    ``<`` drift would select branch 1. The landscape (0.25, 0.35, 0.40) admits an
    exact float boundary at ``u = 0.25/tot`` where ``u*tot == 0.25 == cum_0``."""
    pk = [0.25, 0.35, 0.40]
    tot = sum(pk)
    u_edge = pk[0] / tot
    require_precondition(
        float(u_edge) * tot == pk[0],
        "the crafted landscape has no exact float boundary at cum_0 (the K-3 strict-"
        "vs-nonstrict leg would be ill-defined)", remedy="re-pick the pk landscape")
    sel, _ = _drive_leak(pk, u_edge)
    assert sel == 0, \
        "u*tot == cum_0 exactly must select the BOUNDARY branch 0 (registry '<=' " \
        "semantics); selecting 1 is the strict-'<' drift (K-3)"

    # KILLER (K-3): a strict-'<' selection on the SAME boundary would pick branch 1.
    # Replicate the two rules on the probed floats and demonstrate they DISAGREE here.
    def _select(rule_le: bool) -> int:
        cum = 0.0
        target = float(u_edge) * tot
        sel_local = len(pk) - 1
        for k, p in enumerate(pk):
            cum += p
            hit = (target <= cum) if rule_le else (target < cum)
            if hit:
                return k
        return sel_local
    require_precondition(
        _select(True) != _select(False),
        "the '<=' and '<' rules agree on this boundary (the K-3 drift killer would be "
        "vacuous)", remedy="re-pick a u exactly on cum_0")

    def _tiebreak_check(candidate_rule_le, _tol):
        # candidate is the rule flag; the check asserts the '<=' outcome == the REAL sel.
        assert _select(candidate_rule_le) == sel, "candidate tie-break rule mismatch"
    assert_control_trips(_tiebreak_check, False, 0.0)  # the '<' rule must trip


def test_leak_sample_fallback_last_branch():
    """§5.1 BOUNDARY -- the FALLBACK leg (mps_forward.py 660->665, the measured
    uncovered branch): ``u`` one ULP ABOVE 1.0 makes ``target = u*tot > tot >= cum``
    for EVERY k, so the loop finds no k and ``sel`` retains its initializer
    ``len(pk)-1 = K-1``. AM-1: ``u=1.0`` breaks INSIDE the loop at the last k (``target
    == final cum``); the pure fallback needs ``u`` slightly ABOVE 1.0. Defends K-3
    (the fallback index is K-1, not 0 -- a ``sel=0`` init mutant fails this leg) and
    K-2 (fallback off-by-one)."""
    pk = [0.25, 0.35, 0.40]
    K = len(pk)
    u_over = float(np.nextafter(1.0, 2.0))  # one ULP above 1.0
    require_precondition(
        u_over > 1.0,
        "nextafter(1.0, 2.0) did not exceed 1.0 (the fallback leg would not be "
        "entered)", remedy="use a larger over-1 epsilon")
    sel, stub = _drive_leak(pk, u_over)
    assert sel == K - 1, \
        f"u>1 must reach the FALLBACK leg and return K-1={K - 1} (got {sel}); a " \
        f"sel=0 initializer mutant fails here (K-3)"
    # AM-2 sanity: the application body still ran on the fallback index (gate_ once).
    assert len(stub.gate_calls) == 1, "gate_ must be applied exactly once on the sel branch"

    # KILLER (K-3): u=1.0 (NOT above) breaks inside the loop -> also K-1, but via the
    # loop body, not the fallback. Both return K-1; the discriminator is the RULE. A
    # fallback-init mutant of `sel = 0` would return 0 here at u_over -> demonstrate the
    # init value is load-bearing by replicating the loop with a sabotaged init.
    def _select_with_init(init: int) -> int:
        cum = 0.0
        target = u_over * sum(pk)
        sel_local = init
        for k, p in enumerate(pk):
            cum += p
            if target <= cum:
                return k
        return sel_local
    require_precondition(
        _select_with_init(0) != _select_with_init(K - 1),
        "the fallback init value is not load-bearing on this input (the K-3 init "
        "killer would be vacuous)", remedy="use u strictly above 1.0")

    def _init_check(candidate_init, _tol):
        assert _select_with_init(candidate_init) == sel, "candidate fallback init mismatch"
    assert_control_trips(_init_check, 0, 0.0)  # the sel=0 init mutant must trip


def test_leak_sample_renormalize_skipped_on_zero_norm():
    """§5.1 DEGENERATE (K-7): when the selected branch norm ``pk[sel]`` is <=
    ``NUMERICAL_ZERO``, ``_renormalize`` does NOT call ``multiply_`` (the guard at
    mps_forward.py:580). A zero-mass first branch with ``u=0.0`` selects branch 0 and
    the renorm is skipped -- assert no ``multiply_`` fires (no divide-by-zero)."""
    pk = [0.0, 0.4, 0.6]
    sel, stub = _drive_leak(pk, 0.0)
    assert sel == 0, "u=0.0 selects branch 0 even at zero mass"
    assert len(stub.multiply_calls) == 0, \
        "renormalize must SKIP multiply_ when norm_sq <= NUMERICAL_ZERO (K-7)"


def test_leak_sample_renormalize_fires_on_positive_norm():
    """§5.1 NORMAL (control for the K-7 test above): a POSITIVE selected branch norm
    DOES trigger ``multiply_`` exactly once -- so the skip above is a real branch, not
    an always-skip. Defends the ``norm_sq > NUMERICAL_ZERO`` branch is LIVE."""
    pk = [0.3, 0.3, 0.4]
    sel, stub = _drive_leak(pk, 0.0)
    assert sel == 0
    assert pk[sel] > NUMERICAL_ZERO
    assert len(stub.multiply_calls) == 1, \
        "renormalize must call multiply_ once on a positive branch norm"


# --------------------------------------------------------------------------- #
# §5.2  attach_layout -- Mapping reject, non-permutation reject, INVERSE bind. #
# --------------------------------------------------------------------------- #
qtn = pytest.importorskip("quimb.tensor")  # attach_layout ctor imports quimb.tensor


def _fwd_cpu() -> MpsLeakageForward:
    """A CPU ``MpsLeakageForward`` (device='cpu' -> no cuda). ``__init__`` imports
    quimb (guarded by importorskip above); ``attach_layout`` is pure dict/tuple work."""
    return MpsLeakageForward(device="cpu")


def test_attach_layout_identity_binds_inverse():
    """§5.2 NORMAL: identity ``order=(0,1,2)`` -> ``_eng_to_mps == {0:0,1:1,2:2}``,
    ``_mps_order == (0,1,2)``, ``_log_eng_support`` primed. Defends K-1 (the seam is
    not inert -- the attrs are actually set)."""
    fwd = _fwd_cpu()
    fwd.attach_layout((0, 1, 2), [1, 2])
    assert fwd._mps_order == (0, 1, 2), "identity order not bound"
    assert fwd._eng_to_mps == {0: 0, 1: 1, 2: 2}, "identity inverse map wrong"
    assert fwd._log_eng_support == [1, 2], "logical support not primed"


def test_attach_layout_nonidentity_inverse_direction():
    """§5.2 NORMAL (K-2 INVERSE direction): the docstring worked example
    ``order=(2,0,1)`` -> ``_eng_to_mps == {2:0, 0:1, 1:2}`` (engine->site, the INVERSE
    of site->engine). An implementation that set ``_eng_to_mps = dict(enumerate(order))``
    (i.e. ``{0:2,1:0,2:1}``, the UN-inverted map) is the discriminator and DIFFERS."""
    fwd = _fwd_cpu()
    fwd.attach_layout((2, 0, 1), [])
    inverse = {2: 0, 0: 1, 1: 2}
    uninverted = dict(enumerate((2, 0, 1)))  # {0:2,1:0,2:1} -- the wrong direction
    require_precondition(
        inverse != uninverted,
        "the chosen order is involutory (inverse == un-inverted; the K-2 direction "
        "killer would be vacuous)", remedy="pick a non-involutory permutation")
    assert fwd._eng_to_mps == inverse, \
        "attach_layout did not INVERT the site->engine order (K-2 direction drift)"

    # KILLER (K-2): the UN-inverted map must trip an equality against the real binding.
    def _direction_check(candidate, _tol):
        assert fwd._eng_to_mps == candidate, "layout direction mismatch"
    assert_control_trips(_direction_check, uninverted, 0.0)


def test_attach_layout_single_site_and_empty_support():
    """§5.2 BOUNDARY: single-site ``order=(0,)`` + empty ``logical_support`` -> the
    trivial identity bind with an empty support list."""
    fwd = _fwd_cpu()
    fwd.attach_layout((0,), [])
    assert fwd._mps_order == (0,)
    assert fwd._eng_to_mps == {0: 0}
    assert fwd._log_eng_support == []


def test_attach_layout_mapping_rejected_typeerror():
    """§5.2 EXCEPTION (K-6): a ``Mapping`` (the eng->mps dict) is REJECTED with
    ``TypeError`` (mps_forward.py:458) -- the guard fires BEFORE the permutation check,
    because dict iteration yields KEYS only (silent insertion-order reinterpretation).
    A dict that IS a valid total map would pass the permutation check otherwise."""
    fwd = _fwd_cpu()
    valid_total_map = {0: 0, 1: 1, 2: 2}  # a valid permutation as a Mapping
    with pytest.raises(TypeError, match="Mapping|sequence|order tuple|eng_to_mps"):
        fwd.attach_layout(valid_total_map, [])


def test_attach_layout_non_permutation_duplicate_raises():
    """§5.2 EXCEPTION: ``order=(0,0,1)`` (duplicate, not a permutation) -> ``ValueError``
    (mps_forward.py:464, the measured uncovered raise). Defends K-2 (a non-bijective
    order must not silently bind)."""
    fwd = _fwd_cpu()
    with pytest.raises(ValueError, match="permutation"):
        fwd.attach_layout((0, 0, 1), [])


def test_attach_layout_non_permutation_gap_raises():
    """§5.2 EXCEPTION: ``order=(0,1,3)`` (gap at 2, not a permutation of 0..2) ->
    ``ValueError`` (mps_forward.py:464)."""
    fwd = _fwd_cpu()
    with pytest.raises(ValueError, match="permutation"):
        fwd.attach_layout((0, 1, 3), [])


# --------------------------------------------------------------------------- #
# §5.3  mps_from_statevector -- non-identity-order round-trip (CPU quimb).     #
# --------------------------------------------------------------------------- #
def _dense_of(mps, ref: torch.Tensor) -> torch.Tensor:
    d = mps.to_dense()
    if not isinstance(d, torch.Tensor):
        d = torch.as_tensor(np.asarray(d))
    return d.reshape(-1).to(device=ref.device, dtype=CDTYPE)


def test_mps_from_statevector_identity_order_roundtrip():
    """§5.3 NORMAL: identity ``order`` -> ``to_dense`` recovers ``psi`` directly (n=3
    random normalized qutrit state). ``from_dense`` is EXACT (zero-truncation lift, the
    C8 anchor). CPU device (device-agnostic convention)."""
    n = 3
    rng = np.random.default_rng(7)
    v = rng.standard_normal(PHYS ** n) + 1j * rng.standard_normal(PHYS ** n)
    v = v / np.linalg.norm(v)
    psi = torch.tensor(v, dtype=CDTYPE, device=_CPU)
    mps = mf.mps_from_statevector(psi, tuple(range(n)), _CPU)
    err = float(torch.max(torch.abs(_dense_of(mps, psi) - psi)).item())
    assert err < 1e-13, f"identity-order round-trip max err {err:.3e} >= 1e-13"


def test_mps_from_statevector_nonidentity_order_transpose():
    """§5.3 NORMAL/BOUNDARY (K-8 site-0-MSB convention, K-1 the ``order`` permutation
    must be APPLIED): with a NON-identity ``order`` the raw ``to_dense`` is the
    SNAKE-basis vector (``psi`` with engine axes transposed into site axes); inverting
    the permutation recovers the ORIGINAL engine-basis ``psi`` at 1e-13. An
    order-ignoring implementation fails against the permuted reference."""
    n = 4
    order = (2, 0, 3, 1)  # non-identity site->engine order
    inv = tuple(int(i) for i in np.argsort(order))
    rng = np.random.default_rng(11)
    v = rng.standard_normal(PHYS ** n) + 1j * rng.standard_normal(PHYS ** n)
    v = v / np.linalg.norm(v)
    psi = torch.tensor(v, dtype=CDTYPE, device=_CPU)
    psi_snake = psi.reshape([PHYS] * n).permute(*order).contiguous().reshape(-1)
    require_precondition(
        float(torch.max(torch.abs(psi_snake - psi)).item()) > 1e-6,
        "drawn state is invariant under the chosen permutation (the K-1 dead-order "
        "killer would be vacuous)", remedy="re-seed / re-pick the order")

    dense_nid = _dense_of(mf.mps_from_statevector(psi, order, _CPU), psi)
    # the raw dense form IS the snake-basis vector (order consumed, K-8)...
    err_snake = float(torch.max(torch.abs(dense_nid - psi_snake)).item())
    assert err_snake < 1e-13, f"raw to_dense != psi permuted by order ({err_snake:.3e}, K-8)"
    # ...and inverting the site permutation recovers the ORIGINAL engine-basis psi.
    psi_rec = dense_nid.reshape([PHYS] * n).permute(*inv).contiguous().reshape(-1)
    err = float(torch.max(torch.abs(psi_rec - psi)).item())
    assert err < 1e-13, f"inverse-permuted round-trip max err {err:.3e} >= 1e-13"

    # KILLER (K-1/K-8): the identity-order build's dense form DIFFERS from the
    # non-identity build's raw snake-basis form (an order-ignoring impl coincides).
    dense_id = _dense_of(mf.mps_from_statevector(psi, tuple(range(n)), _CPU), psi)

    def _order_check(candidate, gate_tol):
        e = float(torch.max(torch.abs(dense_id - candidate)).item())
        assert e < gate_tol, f"identity/non-identity dense mismatch {e:.3e}"
    assert_control_trips(_order_check, dense_nid, 1e-13)


def test_mps_from_statevector_single_site():
    """§5.3 BOUNDARY: ``n=1`` (single site, trivial MPS) -> ``to_dense`` == psi."""
    rng = np.random.default_rng(3)
    v = rng.standard_normal(PHYS) + 1j * rng.standard_normal(PHYS)
    v = v / np.linalg.norm(v)
    psi = torch.tensor(v, dtype=CDTYPE, device=_CPU)
    mps = mf.mps_from_statevector(psi, (0,), _CPU)
    err = float(torch.max(torch.abs(_dense_of(mps, psi) - psi)).item())
    assert err < 1e-13, f"n=1 round-trip max err {err:.3e} >= 1e-13"
