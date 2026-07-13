"""Stage-D batch ``seam_teachers`` (D8) -- per-unit L0+L1+L2 coverage of
``error_coupling_simulator.mechanisms.seam_teachers`` (11 public units, all CPU-pure).

Full-coverage program (docs/twin_validation/wave2_6_unit_test_contract.md SS12.3/12.4;
work-list docs/twin_validation/l3_release_package_unit_inventory.md D8). The module is the
ADR-0008 C3 SEAM-TEST controlled-teacher line (EVALUATOR-ONLY): the M3-scale ``BitFlip.RX``
backdrop, the coherent seam edge ``exp(-i phi Z(x)Z)`` on the strip's unchecked seam data
pair, its exact Pauli twirl (correlated dephasing), and the D5 T-B/T-A two-state Markov
member. It imports torch but every unit builds only SMALL, device-agnostic dense Kraus/field
tensors on CPU -- no GPU-required unit exists, so all 11 are CPU-pure and in-scope for full
L0+L1+L2.

  UNIT                            branch surface                 L1 faithfulness / value pin
  ----                            --------------                 ---------------------------
  tb_markov_kraus                 none (straight line; 0/0)      CPTP; NON-UNITAL (p01!=p10);
                                                                 realizes [[1-p01,p10],[p01,1-p10]]
  tb_record_chain_stats           none (straight line; 0/0)      r,R,lambda1,T3 == indep chain
  tb_member_from_rate_and_ratio   ratio>1 sqrt guard (2 arcs)    inversion round-trip; both arcs
  backdrop_kraus                  none (straight line; 0/0)      == indep BitFlip(1e-2).RX(0.2)
  backdrop_teacher                none (straight line; 0/0)      name/channel/edge/params pin
  coherent_seam_teacher           none (straight line; 0/0)      + coherent edge on seam pin
  bias_injected_coherent_teacher  none (straight line; 0/0)      + injected=phi+delta pin
  twirled_seam_teacher            none (straight line; 0/0)      + correlated-dephasing edge pin
  tb_bunching_teacher             none (straight line; 0/0)      T-B member; registered r,R,lam
  pauli_ablation_teacher          none (straight line; 0/0)      T-A member; R==1 unital
  seam_teacher_arms               bias_delta-is-not-None (2)     roster keys; per-arm identity

Value-discrimination is the real bar (the standing lesson: 100% coverage at ~0.75 kill by
asserting shapes/verdicts). EVERY channel/edge/param is pinned against an INDEPENDENT numpy
recompute built here (NOT the module's own builders), so a wrong coefficient / sign / index /
kron-order / arg-swap / constant mutation diverges from the reference and is KILLED. The
load-bearing invariants are shown DISCRIMINATING (assert_discriminates): the T-B member is
genuinely non-unital where the R=1 ablation is unital; the Kraus realizes the DECLARED Markov
transition (a swapped-index sabotage fails); the coherent edge fires on the seam pair only.

CPU-ONLY: every torch tensor stays on CPU; no unit is moved to cuda or requires a GPU.
"""
from __future__ import annotations

import math

import numpy as np
import pytest
import torch
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_cptp, assert_discriminates

from error_coupling_simulator.mechanisms import seam_teachers as st_mod
from error_coupling_simulator.mechanisms.seam_teachers import (
    BACKDROP_FLIP_RATE,
    BACKDROP_ROTATION,
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

PHI_TOP = SEAM_PHI_REGIME[1]  # 0.15, the regime top


# --------------------------------------------------------------------------- #
# A minimal strip stub: the factories touch ONLY strip.seam_pair.             #
# --------------------------------------------------------------------------- #
class _Strip:
    def __init__(self, seam_pair=(2, 3)):
        self.seam_pair = tuple(seam_pair)


TOY = _Strip((2, 3))


# --------------------------------------------------------------------------- #
# INDEPENDENT numpy recomputes (from scratch -- NOT the module's builders).   #
# --------------------------------------------------------------------------- #
_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
_I2 = np.eye(2, dtype=complex)
_I4 = np.eye(4, dtype=complex)
_ZZ = np.diag([1.0, -1.0, -1.0, 1.0]).astype(complex)  # Z(x)Z diagonal


def _rx_np(theta: float) -> np.ndarray:
    c, s = math.cos(theta / 2.0), math.sin(theta / 2.0)
    return np.array([[c, -1j * s], [-1j * s, c]], dtype=complex)


def _backdrop_np(p: float = BACKDROP_FLIP_RATE, theta: float = BACKDROP_ROTATION) -> np.ndarray:
    """BitFlip(p) . RX(theta) = {sqrt(1-p) RX, sqrt(p) X RX} as a (2,2,2) stack."""
    u = _rx_np(theta)
    return np.stack([math.sqrt(1.0 - p) * (_I2 @ u), math.sqrt(p) * (_X @ u)])


def _tb_markov_np(p01: float, p10: float) -> np.ndarray:
    """K0=diag(sqrt(1-p01),sqrt(1-p10)), K1=sqrt(p01)|1><0|, K2=sqrt(p10)|0><1|."""
    k0 = np.array([[math.sqrt(1.0 - p01), 0.0], [0.0, math.sqrt(1.0 - p10)]], dtype=complex)
    k1 = np.array([[0.0, 0.0], [math.sqrt(p01), 0.0]], dtype=complex)
    k2 = np.array([[0.0, math.sqrt(p10)], [0.0, 0.0]], dtype=complex)
    return np.stack([k0, k1, k2])


def _zz_np(phi: float) -> np.ndarray:
    """exp(-i phi Z(x)Z) = diag(e^-iphi, e^iphi, e^iphi, e^-iphi) as a (1,4,4) stack."""
    d = np.array([np.exp(-1j * phi), np.exp(1j * phi), np.exp(1j * phi), np.exp(-1j * phi)])
    return np.diag(d)[None, :, :]


def _corr_deph_np(phi: float) -> np.ndarray:
    """{cos(phi) I4, sin(phi) Z(x)Z} as a (2,4,4) stack (Pauli twirl of exp(-i phi ZZ))."""
    return np.stack([math.cos(phi) * _I4, math.sin(phi) * _ZZ])


def _np(t: torch.Tensor) -> np.ndarray:
    return t.detach().cpu().numpy()


def _transition_from_kraus_np(kraus: np.ndarray) -> np.ndarray:
    """Z-population transition T[i_out, j_in] realized by the Kraus action on |j><j|.
    Columns sum to 1; off-diagonals of the image must vanish on diagonal inputs."""
    T = np.zeros((2, 2))
    for j in (0, 1):
        rho = np.zeros((2, 2), dtype=complex)
        rho[j, j] = 1.0
        out = sum(k @ rho @ k.conj().T for k in kraus)
        assert abs(out[0, 1]) + abs(out[1, 0]) < 1e-12
        T[0, j] = out[0, 0].real
        T[1, j] = out[1, 1].real
    return T


def _chain_stats_indep(T: np.ndarray) -> dict:
    """Stationary flip-process functionals by EXPLICIT chain products (a different
    computation path from tb_record_chain_stats' closed forms)."""
    p01, p10 = T[1, 0], T[0, 1]
    s = p01 + p10
    pi = np.array([p10 / s, p01 / s])            # stationary distribution
    flip = np.array([p01, p10])                  # P(flip | state)
    after = {0: 1, 1: 0}                         # state after a flip
    r = float((pi * flip).sum())
    pff = float(sum(pi[i] * flip[i] * flip[after[i]] for i in (0, 1)))
    pfff = float(sum(pi[i] * flip[i] * flip[after[i]] * flip[after[after[i]]] for i in (0, 1)))
    lam1 = float(np.sort(np.linalg.eigvals(T).real).min())  # eigenvalues {1, 1-p01-p10}
    return {"r": r, "R": pff / r ** 2, "T3": pfff / r ** 3, "lambda1": lam1}


def _is_unital(kraus: np.ndarray, tol: float = 1e-9) -> bool:
    dim = kraus.shape[1]
    s = sum(k @ k.conj().T for k in kraus)
    return float(np.max(np.abs(s - np.eye(dim)))) <= tol


def _assert_params(actual: dict, expected: dict, atol: float = 1e-12) -> None:
    """Recursive value pin over a params dict (floats to atol, ints/tuples exact-ish)."""
    assert isinstance(actual, dict), type(actual)
    assert set(actual) == set(expected), (set(actual), set(expected))
    for k, e in expected.items():
        a = actual[k]
        if isinstance(e, dict):
            _assert_params(a, e, atol)
        elif isinstance(e, (tuple, list)):
            assert len(a) == len(e), (k, a, e)
            for x, y in zip(a, e):
                assert abs(float(x) - float(y)) <= atol, (k, x, y)
        else:
            assert abs(float(a) - float(e)) <= atol, (k, a, e)


def _pin_complex(actual: torch.Tensor, ref: np.ndarray, atol: float = 1e-12) -> None:
    a = _np(actual)
    assert a.shape == ref.shape, (a.shape, ref.shape)
    assert np.allclose(a, ref, atol=atol, rtol=0.0), np.max(np.abs(a - ref))


def _backdrop_params_expected() -> dict:
    return {
        "backdrop_flip_rate": BACKDROP_FLIP_RATE,
        "backdrop_rotation": BACKDROP_ROTATION,
        "backdrop_coherent_rate": math.sin(BACKDROP_ROTATION / 2.0) ** 2,
    }


# =========================================================================== #
# L0 -- per-unit statement + branch coverage (explicit, crafted inputs)       #
# =========================================================================== #
def test_L0_tb_markov_kraus_runs():
    k = tb_markov_kraus(TB_P01, TB_P10)
    assert tuple(k.shape) == (3, 2, 2)


def test_L0_tb_record_chain_stats_runs():
    s = tb_record_chain_stats(TB_P01, TB_P10)
    assert set(s) == {"r", "R", "lambda1", "T3"}


def test_L0_tb_member_from_rate_and_ratio_both_branches():
    # ratio > 1.0 -> the sqrt arc; ratio <= 1.0 -> the root=0.0 arc (both exercised)
    hi = tb_member_from_rate_and_ratio(TB_FLIP_RATE, TB_BUNCHING_RATIO)
    assert hi[0] < hi[1]                                  # split members
    one = tb_member_from_rate_and_ratio(0.02, 1.0)        # else arc: root = 0
    assert one[0] == pytest.approx(one[1])                # degenerate pair
    lo = tb_member_from_rate_and_ratio(0.02, 0.5)         # else arc: ratio < 1
    assert lo[0] == pytest.approx(lo[1])


def test_L0_backdrop_kraus_runs():
    assert tuple(backdrop_kraus().shape) == (2, 2, 2)


def test_L0_backdrop_teacher_runs():
    t = backdrop_teacher(TOY)
    assert isinstance(t, SeamNoiseProcess) and t.edge_field is None


def test_L0_coherent_seam_teacher_runs():
    t = coherent_seam_teacher(TOY)
    assert t.edge_field is not None


def test_L0_bias_injected_coherent_teacher_runs():
    t = bias_injected_coherent_teacher(TOY, delta=0.02)
    assert t.edge_field is not None


def test_L0_twirled_seam_teacher_runs():
    t = twirled_seam_teacher(TOY)
    assert t.edge_field is not None


def test_L0_tb_bunching_teacher_runs():
    t = tb_bunching_teacher(TOY)
    assert t.edge_field is None


def test_L0_pauli_ablation_teacher_runs():
    t = pauli_ablation_teacher(TOY)
    assert t.edge_field is None


def test_L0_seam_teacher_arms_both_branches():
    # bias_delta is None -> the skip arc (5 arms); not-None -> the add arc (6 arms).
    no_bias = seam_teacher_arms(TOY)
    assert set(no_bias) == {"backdrop", "coherent", "twirled", "bunching", "ablation"}
    with_bias = seam_teacher_arms(TOY, bias_delta=0.02)
    assert "bias" in with_bias
    # bias_delta = 0.0 is NOT None -> still adds the arm (kills `if bias_delta:` truthiness)
    zero_bias = seam_teacher_arms(TOY, bias_delta=0.0)
    assert "bias" in zero_bias


# =========================================================================== #
# VALUE PINS -- each channel / edge / param vs an INDEPENDENT numpy recompute  #
# =========================================================================== #
def test_pin_tb_markov_kraus_values():
    _pin_complex(tb_markov_kraus(TB_P01, TB_P10), _tb_markov_np(TB_P01, TB_P10))
    # asymmetric second point so p01<->p10 swap / index swap is load-bearing
    _pin_complex(tb_markov_kraus(0.1, 0.4), _tb_markov_np(0.1, 0.4))


def test_pin_tb_record_chain_stats_values():
    got = tb_record_chain_stats(TB_P01, TB_P10)
    # independent closed forms recomputed here (different arithmetic grouping)
    p01, p10 = float(TB_P01), float(TB_P10)
    s = p01 + p10
    ref = {"r": 2.0 * p01 * p10 / s, "R": (s * s) / (4.0 * p01 * p10),
           "lambda1": 1.0 - s, "T3": (s * s) / (4.0 * p01 * p10)}
    _assert_params(got, ref, atol=1e-15)
    # the registered (a)-class member values (D5 T-B at r=1.27e-2, R=5, lambda1=0.873)
    assert got["r"] == pytest.approx(TB_FLIP_RATE, abs=1e-6)
    assert got["R"] == pytest.approx(TB_BUNCHING_RATIO, abs=1e-4)
    assert got["lambda1"] == pytest.approx(TB_LAMBDA1, abs=1e-6)
    assert got["T3"] == pytest.approx(got["R"], rel=1e-12)


def test_pin_tb_member_inversion_and_values():
    # ratio > 1: {p01,p10} = r R (1 -/+ sqrt(1 - 1/R)), sorted ascending
    for r, ratio in ((TB_FLIP_RATE, TB_BUNCHING_RATIO), (0.02, 3.0), (0.05, 1.5)):
        rr = r * ratio
        root = math.sqrt(1.0 - 1.0 / ratio)
        lo, hi = tb_member_from_rate_and_ratio(r, ratio)
        assert lo == pytest.approx(rr * (1.0 - root), abs=1e-15)
        assert hi == pytest.approx(rr * (1.0 + root), abs=1e-15)
    # ratio <= 1 branch: root = 0 -> both members equal r*ratio
    for r, ratio in ((0.02, 1.0), (0.03, 0.7)):
        lo, hi = tb_member_from_rate_and_ratio(r, ratio)
        assert lo == pytest.approx(r * ratio, abs=1e-15)
        assert hi == pytest.approx(r * ratio, abs=1e-15)
    # round-trip identity: inverting the T-B member's (r,R) recovers (p01,p10) sorted
    lo, hi = tb_member_from_rate_and_ratio(TB_FLIP_RATE, TB_BUNCHING_RATIO)
    assert lo == pytest.approx(min(TB_P01, TB_P10), abs=1e-6)
    assert hi == pytest.approx(max(TB_P01, TB_P10), abs=1e-6)


def test_pin_backdrop_kraus_values():
    _pin_complex(backdrop_kraus(), _backdrop_np())


def test_pin_backdrop_teacher():
    t = backdrop_teacher(TOY)
    assert t.name == "seam-backdrop"
    assert t.edge_field is None
    _pin_complex(t.channel_field(0, 0), _backdrop_np())
    _pin_complex(t.channel_field(3, 1), _backdrop_np())        # location/round-constant
    _assert_params(t.params, {**_backdrop_params_expected(), "seam_pair": (2, 3)})


@pytest.mark.parametrize("seam", [(2, 3), (4, 5)])
def test_pin_coherent_seam_teacher(seam):
    strip = _Strip(seam)
    t = coherent_seam_teacher(strip)                          # default phi = SEAM_PHI_REF
    assert t.name == "seam-coherent(phi=+0.1)"
    _pin_complex(t.channel_field(0, 0), _backdrop_np())
    # coherent edge exp(-i phi ZZ) fires on the seam pair, is None elsewhere
    _pin_complex(t.edge_field(0, seam), _zz_np(SEAM_PHI_REF))
    assert t.edge_field(0, (0, 1)) is None
    _assert_params(t.params, {**_backdrop_params_expected(), "phi": SEAM_PHI_REF,
                              "phi_ref": SEAM_PHI_REF, "phi_regime": SEAM_PHI_REGIME,
                              "seam_pair": tuple(seam)})


def test_pin_coherent_seam_teacher_nondefault_phi():
    t = coherent_seam_teacher(TOY, phi=PHI_TOP)
    assert t.name == "seam-coherent(phi=+0.15)"
    _pin_complex(t.edge_field(0, (2, 3)), _zz_np(PHI_TOP))
    assert t.params["phi"] == pytest.approx(PHI_TOP)


def test_pin_bias_injected_coherent_teacher():
    delta, phi = 0.02, SEAM_PHI_REF
    t = bias_injected_coherent_teacher(TOY, delta=delta, phi=phi)
    injected = phi + delta
    assert t.name == "seam-coherent-bias(phi=+0.1,delta=+0.02)"
    _pin_complex(t.channel_field(0, 0), _backdrop_np())      # same M3 backdrop as the coherent arm
    # the injected edge is exp(-i (phi+delta) ZZ) -- pins the '+' (a '-' diverges)
    _pin_complex(t.edge_field(0, (2, 3)), _zz_np(injected))
    assert t.edge_field(0, (9, 9)) is None
    _assert_params(t.params, {**_backdrop_params_expected(), "phi": phi, "delta": delta,
                              "phi_injected": injected, "seam_pair": (2, 3)})


def test_pin_twirled_seam_teacher():
    phi = SEAM_PHI_REF
    t = twirled_seam_teacher(TOY, phi=phi)
    assert t.name == "seam-twirled(phi=+0.1)"
    _pin_complex(t.channel_field(0, 0), _backdrop_np())
    _pin_complex(t.edge_field(0, (2, 3)), _corr_deph_np(phi))
    assert t.edge_field(0, (0, 1)) is None
    _assert_params(t.params, {**_backdrop_params_expected(), "phi": phi,
                              "twirl_rate": math.sin(phi) ** 2, "seam_pair": (2, 3)})


def test_pin_tb_bunching_teacher():
    t = tb_bunching_teacher(TOY)
    assert t.name == "seam-bunching-TB(R=5)"
    assert t.edge_field is None
    _pin_complex(t.channel_field(0, 0), _tb_markov_np(TB_P01, TB_P10))
    p01, p10 = float(TB_P01), float(TB_P10)
    s = p01 + p10
    ref = {"p01": TB_P01, "p10": TB_P10, "r": 2.0 * p01 * p10 / s,
           "R": (s * s) / (4.0 * p01 * p10), "lambda1": 1.0 - s,
           "T3": (s * s) / (4.0 * p01 * p10),
           "registered": {"r": TB_FLIP_RATE, "R": TB_BUNCHING_RATIO, "lambda1": TB_LAMBDA1}}
    _assert_params(t.params, ref, atol=1e-15)


def test_pin_pauli_ablation_teacher():
    t = pauli_ablation_teacher(TOY)
    assert t.name == "seam-pauli-ablation-TA(R=1)"
    assert t.edge_field is None
    _pin_complex(t.channel_field(0, 0), _tb_markov_np(TB_FLIP_RATE, TB_FLIP_RATE))
    q = float(TB_FLIP_RATE)
    # T-A closed forms: p01=p10=r -> r=q, R=1 exactly, lambda1=1-2q (independent forms)
    _assert_params(t.params, {"p01": q, "p10": q, "r": q, "R": 1.0, "lambda1": 1.0 - 2.0 * q},
                   atol=1e-12)


@pytest.mark.parametrize("phi", [SEAM_PHI_REF, PHI_TOP])
def test_pin_seam_teacher_arms(phi):
    # without bias: exactly the five item-2 arms, each == its own factory
    arms = seam_teacher_arms(TOY, phi=phi)
    assert set(arms) == {"backdrop", "coherent", "twirled", "bunching", "ablation"}
    assert arms["backdrop"].name == backdrop_teacher(TOY).name
    assert arms["coherent"].name == coherent_seam_teacher(TOY, phi=phi).name
    assert arms["twirled"].name == twirled_seam_teacher(TOY, phi=phi).name
    assert arms["bunching"].name == tb_bunching_teacher(TOY).name
    assert arms["ablation"].name == pauli_ablation_teacher(TOY).name
    # the phi threads into the coherent + twirled arms (not hardcoded)
    _pin_complex(arms["coherent"].edge_field(0, (2, 3)), _zz_np(phi))
    _pin_complex(arms["twirled"].edge_field(0, (2, 3)), _corr_deph_np(phi))
    # with a declared bias_delta the sixth arm appears at phi + delta
    delta = 0.03
    arms6 = seam_teacher_arms(TOY, phi=phi, bias_delta=delta)
    assert set(arms6) == {"backdrop", "coherent", "twirled", "bunching", "ablation", "bias"}
    assert arms6["bias"].params["delta"] == pytest.approx(delta)
    assert arms6["bias"].params["phi_injected"] == pytest.approx(phi + delta)
    _pin_complex(arms6["bias"].edge_field(0, (2, 3)), _zz_np(phi + delta))


# =========================================================================== #
# L1 -- Hypothesis faithfulness properties                                    #
# =========================================================================== #
@st.composite
def _rates(draw, lo=1e-4, hi=0.49):
    p01 = draw(st.floats(lo, hi, allow_nan=False, allow_infinity=False))
    p10 = draw(st.floats(lo, hi, allow_nan=False, allow_infinity=False))
    return p01, p10


@settings(max_examples=150, deadline=None)
@given(_rates())
def test_L1_tb_markov_kraus_is_cptp(rates):
    """sum_k K^dag K = I (trace-preserving) for any T-B member -- a faithfulness invariant."""
    p01, p10 = rates
    assert_cptp(list(_np(tb_markov_kraus(p01, p10))), tol=1e-9)


@settings(max_examples=150, deadline=None)
@given(_rates())
def test_L1_tb_markov_realizes_declared_transition(rates):
    """DISCRIMINATING: the Kraus action on Z populations is the DECLARED two-state Markov
    transition [[1-p01, p10], [p01, 1-p10]] -- an index/sign mutation moves an entry."""
    p01, p10 = rates
    T = _transition_from_kraus_np(_np(tb_markov_kraus(p01, p10)))
    ref = np.array([[1.0 - p01, p10], [p01, 1.0 - p10]])
    assert np.allclose(T, ref, atol=1e-12), np.max(np.abs(T - ref))


@settings(max_examples=150, deadline=None)
@given(_rates())
def test_L1_tb_record_chain_stats_match_independent_chain(rates):
    """DISCRIMINATING: the D5 closed forms (r,R,lambda1,T3) equal an INDEPENDENT explicit
    chain-product computation over the realized transition -- pins every coefficient."""
    p01, p10 = rates
    T = _transition_from_kraus_np(_np(tb_markov_kraus(p01, p10)))
    indep = _chain_stats_indep(T)
    got = tb_record_chain_stats(p01, p10)
    for key in ("r", "R", "lambda1", "T3"):
        assert got[key] == pytest.approx(indep[key], rel=1e-9, abs=1e-12), key
    assert got["T3"] == pytest.approx(got["R"], rel=1e-9)  # renewal: T3 == R


@settings(max_examples=150, deadline=None)
@given(st.floats(1e-4, 0.2, allow_nan=False), st.floats(1.05, 40.0, allow_nan=False))
def test_L1_tb_member_inversion_roundtrips_stats(r, ratio):
    """DISCRIMINATING: for ratio>1 the inverted (p01,p10) feed back through the closed forms
    to reproduce (r, ratio) -- the inversion is the exact inverse of the record-chain stats."""
    p01, p10 = tb_member_from_rate_and_ratio(r, ratio)
    assert p01 <= p10                                   # sorted ascending
    back = tb_record_chain_stats(p01, p10)
    assert back["r"] == pytest.approx(r, rel=1e-9, abs=1e-12)
    assert back["R"] == pytest.approx(ratio, rel=1e-9)


def test_L1_backdrop_and_seam_edges_are_cptp():
    """Structural CPTP closure on every built channel/edge (necessary, not sufficient)."""
    assert_cptp(list(_np(backdrop_kraus())), tol=1e-9, label="backdrop")
    assert_cptp(list(_np(coherent_seam_teacher(TOY).edge_field(0, (2, 3)))),
                tol=1e-9, label="coherent-edge")
    assert_cptp(list(_np(twirled_seam_teacher(TOY).edge_field(0, (2, 3)))),
                tol=1e-9, label="twirled-edge")


# =========================================================================== #
# KILLER teeth -- prove the load-bearing invariants DISCRIMINATE               #
# =========================================================================== #
def test_KILLER_tb_member_is_genuinely_non_unital():
    """The T-B member (p01 != p10) is genuinely NON-UNITAL (sum K K^dag != I); the R=1
    ablation (p01 = p10) IS unital. assert_discriminates proves the non-unitality property
    has teeth -- it holds for the real T-B member and FAILS for the unital ablation."""
    def prop_non_unital(kraus):
        assert not _is_unital(kraus), "channel is unital (sum K K^dag == I)"

    real = _np(tb_markov_kraus(TB_P01, TB_P10))            # p01 != p10 -> non-unital
    unital = _np(tb_markov_kraus(TB_FLIP_RATE, TB_FLIP_RATE))  # p01 == p10 -> unital
    assert_discriminates(prop_non_unital, real, unital, label="T-B non-unitality")
    # and the two are exactly the T-B member vs the T-A ablation channels of the module
    _pin_complex(tb_bunching_teacher(TOY).channel_field(0, 0),
                 _tb_markov_np(TB_P01, TB_P10))
    _pin_complex(pauli_ablation_teacher(TOY).channel_field(0, 0),
                 _tb_markov_np(TB_FLIP_RATE, TB_FLIP_RATE))


def test_KILLER_tb_markov_transition_index_discriminates():
    """The 'realizes [[1-p01,p10],[p01,1-p10]]' property FAILS for an index-swapped
    (p01<->p10) sabotage -- so it genuinely constrains K1/K2 placement, not just CPTP."""
    p01, p10 = 0.1, 0.4

    def prop_transition(kraus):
        T = _transition_from_kraus_np(kraus)
        ref = np.array([[1.0 - p01, p10], [p01, 1.0 - p10]])
        assert np.allclose(T, ref, atol=1e-12), "transition != declared"

    real = _np(tb_markov_kraus(p01, p10))
    swapped = _np(tb_markov_kraus(p10, p01))              # swaps the off-diagonal flips
    assert_discriminates(prop_transition, real, swapped, label="Markov transition index")


def test_KILLER_coherent_edge_fires_on_seam_pair_only():
    """The coherent seam edge is placed on the strip's declared seam pair ONLY: it returns
    the exp(-i phi ZZ) Kraus there and None on every other pair (edge PLACEMENT has teeth)."""
    t = coherent_seam_teacher(_Strip((2, 3)), phi=PHI_TOP)

    def prop_on_seam(edge_field):
        val = edge_field(0, (2, 3))
        assert val is not None, "edge is silent on its own seam pair"
        assert np.allclose(_np(val), _zz_np(PHI_TOP), atol=1e-12), "edge != exp(-i phi ZZ)"

    # real fires on the seam; a foil that only fires off-seam does not (property has teeth)
    zz = _zz_np(PHI_TOP)

    def wrong_edge(t_, e):
        return None if tuple(e) == (2, 3) else torch.as_tensor(zz)

    assert_discriminates(prop_on_seam, t.edge_field, wrong_edge, label="edge placement")
    assert t.edge_field(0, (5, 6)) is None
